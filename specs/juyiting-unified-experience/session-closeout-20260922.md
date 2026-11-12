# 聚义厅当前上下文与收尾（2026-09-22）

## 结论与用户确认范围

已发布 **1.13.10-uxfix4**。用户在本轮交付后回复“好了，把当前上下文更新到sdd文档，然后删除worktree，做一次磁盘清理。”，记录为本轮UI调整已确认、允许收尾；**不推导真机逐项通过、付费业务闭环或推广效果已验收**。本文件是交接快照，唯一执行台账仍为 `docs/implementation/TASKS.yaml#runtime_ledger_json`。

## 当前已落地的体验

- 百宝箱是聚义厅内的统一功能入口，不恢复个人中心的工作空间；列表→预览→管理／上传逐层进入，一个活动窗口，不堆功能卡片，无独立“回聚义厅”。
- 地图／概览通向同一办理事项；需求→选材及固定版本预览→草稿→独立交办确认→回执。取消不改原引用，状态未知只核对原意图，不暗中重提。
- **横屏地图沉浸显示**：隐藏常驻业务header/toolbar/footer，使用真实melonJS地图和紧凑悬浮入口。办事概览仍有业务导航。
- **竖屏只有地图上的“横屏看全景”方向入口**；工具栏、弹窗不再出现横向按钮，不显示缩放／全景复位控制。横竖切换不重建打开的草稿／阅读面板。
- `experienceMode==='landscape-map' && homeMode==='map'`决定沉浸模式；不以键盘压缩后的高度猜物理方向。地图canvas采用cover，允许超出裁切区域，测试四边覆盖而非与页面等宽。HUD图标必须在实际安装的Varlet图标集中存在。

## 可复现基线

| 对象 | 精确记录 |
|---|---|
| Web | `10fc7207335485e09bf423f08b957a238996d018`；tree `80bc81c359b9d4cc758a6b1a9afa34ac1973a6a4` |
| Web冻结分支 | `release/1.13.10-uxfix4`，已合入develop，旧release未移动 |
| API | `787ae631264d0ae323fcce48957cb71c1cae52c8`；tree `d99e39b1d7518ad6a548d97e1bc3979c9f7a33ae`；本轮不重建／重启 |
| API冻结分支 | `release/1.13.10-fix1`；develop的20ae5fb合并含另一WX改动，不应误当已部署API |
| root发布基线 | `311d195212a7215ab9649425516e8ceabd276d3b`，本收尾文档在其后追加 |
| Web制品SHA-256 | `d183d174b589b948836a6e7091c9c5a6d8813f3e8c1996ae20455c13be42ac20` |
| 安装树SHA-256 | `8a456014424cc54a4bd0c2c8f293b2c2ebe97c894c87ee60e1cd8140ae9714db` |

安装记录：`/opt/cyf/service/api/release-records/jyt-ux-1.13.10/JYT-UXFIX4-20260922/installed.json`。
制品／可恢复发布工具：`deliverables/releases/v1.13.10-uxfix4-local-20260922/`。
便携测试摘要：`verification-immersive-20260922.json`；完整证据：`deliverables/verification/juyiting-immersive-20260922/final-result.json`。

## 已有证据，不重复推测

- 同一最终Web树：302项单元／组件、39项真实Vue＋隔离API夹具浏览器流程，全通过。
- 线上授权账号：6项只读HTTP、37项UI检查，全通过；1440×900、844×390、390×844、320×700，16张截图，横竖首页已实际查看。
- 包括弹窗及草稿连续性、五轮阅读旋转、地图/概览往返、百宝箱分层、选材取消、固定版本、独立确认、刷新恢复。
- `build_origin=local_user_authorized`、Flow Run=null。只在本机执行，没有用Eva，没有恢复自动Flow，没有重启API/Nginx/Agent或执行付费Provider。
- 测试初始失败及诊断均保留，不回写PASS；具体生成／提交写流程在fixture，不将只读线上检查包装成付费端到端成功。

## 尚未取得的证据／继续工作的边界

1. 手机／微信宿主真实方向、系统键盘、原生下载的设备级记录，不能由Chromium仿真替代。
2. 真实授权的付费生成、实际下载可用文件、修改后两版成果关联和回访闭环；不得自动重跑原QUEUED或回填生产数据。
3. Runtime `e0fb44c...`源码测试与线上激活分开；本轮无Agent重启，不能称可靠回传新版本已激活。
4. 目标用户试点P01与业务价值指标尚未完成，不从UI认可或测试数量推导推广成功。整套SDD不因本轮收尾全部归档为完成。

## 工作树和磁盘清理约定

先推送本收尾文档，再移除已完成的本任务9个worktree；保留远端源码及冻结分支。删除前核验干净状态、远端可恢复和无活动进程占用。工作树内`.tmp-w04/w05-evidence`及API测试报告先独立归档并校验。只清理本任务浏览器临时profile、Vite缓存等可再生目录。

**保留**主root/api/web未提交修改、其他任务工作树及进程、共享node_modules、线上与回退站点、全部发布包／哈希／日志／报告／截图。清理实录：`deliverables/cleanup/juyiting-closeout-20260922/`，清理摘要见 `cleanup-closeout-20260922.md`，最终9树完成记录位于上述目录的`final-result.json`（本提交推送后移除最后文档树）。

## 下次接手

1. 先读本文件与 `integration.yaml`，再只读核对实际安装记录；主目录checkout较旧且有无关修改，不把它当线上源码。
2. 从组件当前远端develop或精确冻结基线创建**新**worktree，并明确是否保留develop未上线变化。不要依赖已删除worktree路径，不覆盖旧release，不重复执行旧apply。
3. 文档在root远端master；本机保留本文件便于直接续接。旧长会话摘要仅是历史，不覆盖本文件的最新约束。
4. 后续普通代码由Owner自检；不创建独立Reviewer；Gradle仍经orchestrator串行，当前本地发布授权保留，资源/请求慢只观测。需要真实收费／生产DML／Agent激活时先明确授权。
