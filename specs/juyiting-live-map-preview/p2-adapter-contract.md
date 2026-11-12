# P2 接入合同补充 — 2026-09-06

性质：基于已接受后继源码的接入设计补充，不是实现完成/发布证据；P2 写入仍需主控正式共享路径交接。
原设计：root `4f19923129333bfc50d61ccee797b08fb25d3736` 五件套保持历史来源。

## 已确认后继与可复用修复
- SCREEN accepted：`5fa0685a32363ad9f77e8c1b6ae61197e8ab7d4c` / tree `5be146b7c83d302ba2cb9eaeff1d3fe95a22619f`。
- 累计 Web 后继：`d81b59e2724c45e7af47c60022296b2d20793295` / tree `d712c8b59922e93189df7fcb24b996cc6896d773`，据主控共享交接文档为 SCREEN 与 reader 验收内容的精确集成。最终实施基线由主控交接确认。
- `JuyitingGame.mount` 已只初始化一次全局 renderer，后续复用 canvas；已有 `_rebindEngineContainer`、`_reflowEngineForContainer`、带 generation/容器身份检查的 observer、`_resumeHallRunLoop` 和完整 cleanup。
- 该修复保留的是 renderer/canvas，不是跨卸载的 HallScene/人物运行态。不能把“canvas 复用”误认为已满足本任务人物连续性。
- `HallStage` 仍在离开 landscape-map 时 suspend/destroy；P2 必须在只读预览转换时保留组件与运行态，而不是重新 mount 一个小地图。

## 1. 推荐宿主方案：搬移同一个 HallStage，不搬出内部 canvas

```text
JuyiHall（只存在一个 HallStage 实例）
  HallPortraitHome（稳定保留，按模式显示）
    HallLiveMapPreview
      slot: portraitTarget
  landscapeTarget（稳定保留，按模式显示）
  Teleport -> 当前有效 target
    HallStage（同一组件/内部 map container/Canvas/HallScene）
```

两个 target 必须在首次挂载场景前存在，之后到路由离开前保持 DOM 身份；以组件 ref 定位，不用全局固定 ID。加载/错误/暂停浮层不能替换 target。
Teleport 只改变 HallStage 的祖先位置；它的内部地图容器保持不变，因此无需新增第二个引擎或直接把 canvas 从其已接受父容器拆出。尺寸变化继续走已接受的 observer/稳定 viewport commit，保留 generation fence。
不修改页面方向协调器；不新增 CSS 旋转。既有已接受的方向/virtual viewport 支持不能被预览覆盖或误激活。

## 2. HallStage 的最小职责扩展
- 新增明确 `readOnlyPreview` 展示状态；原 header、交互工具和选中卡片在预览不显示，原横屏样式与操作不改。
- 地图状态和实际地图宽高通过受控展示事件送至竖屏外壳；ready 必须来自真实场景构建成功，不从 Teleport 成功推断。
- 原 experienceMode watcher 在“横屏 ↔ 只读预览”仅转换镜头、布局和 preview 输入锁，不再 suspend/destroy/emit simulation-reset。
- 最终路由卸载、主体退出/变化和真实加载失败仍按原安全 cleanup 处理；不能为了保留地图绕过旧失败清理。
- 单独 preview 输入锁覆盖引擎全局 pointer/wheel/keyboard/agent/hotspot 入口；离开预览只释放自己的锁，不能释放 modal/voice/loading 锁。
- 输入锁先于搬移，镜头/尺寸稳定提交后才允许横屏输入；过期回调不能解锁新的 preview 或覆盖新的入口目标。

## 3. 冷竖屏只读与单一业务驱动
- 地图实例可以初始化既有本地巡逻模拟，以便冷竖屏就有角色运动；不因而强开 simulation/voice 等部署开关。
- 冷竖屏的 scene ready 不触发页面 backend simulation-ready 接入；不拉起第二个命令消费者，不调用派令/状态写入接口。纯表现 phase 不转发成业务执行状态。
- 首次真正进入横屏且场景 ready 时，才沿原事件接入一次页面级命令驱动；快速重复切换不能重复接入。
- 驱动已建立后，回到只读预览不创建另一套连接，也不因 UI 切换销毁/重新执行已接纳业务命令。已有命令继续由同一 Owner 处理；只读禁止新的预览 UI 操作，不假造 terminal 或丢弃既有事件。
- 上述标志必须按页面主体/场景 generation 清理，不能用跨主体全局 boolean。应有冷预览零业务启动、首次横屏一次、三次往返仍一次、卸载与主体切换清理的行为测试。

## 4. 全景镜头不是主厅 reset
- 实际地图边界使用解析后的 coordinateWidth/coordinateHeight 等已验证运行时字段；1664×928 仅作为未知尺寸时的占位比例。
- contain 策略输出 `screen = world * scale + offset`，而 HallScene 当前矩阵以 viewport 中心为基点。适配到 camera offset 时必须换算：`cameraOffset = containOffset - viewportCenter * (1 - scale)`。
- 当前 camera controller 的正常最小 zoom 受主厅 preset 限制；不能直接调用 restore/reset 并假定能得到全景。应提供显式 preview presentation/contain 支持，不能降低正常横屏最小 zoom 作为旁路。
- 预览镜头与横屏 snapshot 分离；进入预览取消正在运行的 reset 动画并保存横屏视图，预览 resize 只重算 contain；返回横屏按原入口目标优先级恢复。
- 如需修改 `src/game/camera/cameraController.ts` 或新增纯 camera adapter/tests，先纳入主控明确 owned paths，不能以原 HallStage 权限扩大范围。

## 5. 绘制预算与运动更新必须分离
已只读核对安装的 melonJS `src/application/application.js`：TICK 调用 update 和 draw；timer.maxfps 会影响 updateFrameRate，不是无副作用的“仅绘制限帧”开关。
- P2 不通过更改全局 timer.maxfps/world.fps 达到预览 20fps，否则可能改变既有模拟时间步。
- 不通过暂停整个 engine 实现预览离屏省电而暂停已接纳业务驱动。
- 可在唯一 JuyitingGame Owner 内增加有身份/生命周期保护的绘制 adapter，针对当前场景跳过无意义 draw，不增加第二个 RAF；横屏恢复原 draw 路径，卸载仅撤销本 Owner 自己安装的 wrapper。
- 若采用 draw wrapper，必须保存原 receiver/参数，准确回收，且跳过整个 draw（保留末帧），不能先清空 renderer 再跳过 HallScene.draw 造成白屏。
- 此方案只承诺减少绘制，不宣称所有模拟 CPU 工作已暂停；实际节能和20fps以真实帧计数验证。后台浏览器调度不属于业务实时 SLA。

## 6. 接入验收重点与交接记录
新增状态式测试：同 HallStage/Canvas/Scene 身份跨模式保留；移动中位置连续；冷热缓存；独立镜头；preview 与其他锁叠加；冷预览零业务、首次横屏单驱动；draw 节流不改变 update/命令计数；卸载/重进恢复旧 SCREEN 回归。
最终需真实浏览器 Canvas 至少10次往返及非空帧/角色位置证据；production build + fresh integrated Reviewer。微信真机未验证仍明确标未验收。
P1 基础包 ACCEPT 仅说明新组件/策略可用于接入，不能把整个 JY-LIVE-PREVIEW 标记完成、发布或解锁绕过上述门禁。

## 7. 提请主控交接的最小新增 owned paths
以下是在 P1 原四路径之外申请的 P2 白名单；未获回执前仅可读，非自行授权。

```text
src/components/world/JuyiHall.vue
src/components/juyiting/HallPortraitHome.vue
src/components/juyiting/HallStage.vue
src/game/JuyitingGame.js
src/game/scenes/HallScene.js
src/game/camera/cameraController.ts
tests/juyiting-live-map-preview-integration.test.js
tests/juyiting-live-map-preview-runtime.test.js
tests/juyiting-portrait-home.test.js
tests/juyiting-experience-mode.test.js
tests/game/camera/camera-controller.test.ts
```

前六项为共享实现路径；两项 live-map-preview 测试为新增；末三项仅更新与新需求直接冲突的旧契约或扩展 contain 回归，不删除原横屏交互验收。其余 SCREEN 回归先只运行、不修改；如确需更改其他路径须另报原因和清单。
已知原 SCREEN 源码 Owner 为 `01a0741c-b852-7d00-9d2c-0d89808251ba`；当前共享交接文件没有明确登记其源主控 thread ID，协调者不据此编造身份或声称已获路径释放。
