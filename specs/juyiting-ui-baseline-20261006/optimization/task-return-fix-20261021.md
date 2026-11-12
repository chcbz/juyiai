# 办事直达事项详情返回漏加载修复（2026-10-21）

## 范围与根因

单Agent Owner：chat-stop-main。仅修 Web 事项详情返回列表，不改 API、Runtime、状态契约、资料或其他业务。

生产1.16.28只读复现：新页面从办事点击待点将卡片的查看进展，详情正常；点击返回后列表0行，状态计数“—”。`openOverviewTask` 用 `restore: true` 避免列表查询影响精准详情，而 `selectTask(null)` 原来只清空选中项，没有查询第一次打开的事项列表。

## 修改

- 唯一原型 `web/prototypes/juyiting/interaction-completion.js`：详情返回事项；规格在同目录 `specs/prototype-spec.md`。PC1440×1000、移动390×844均返回#tasks，展示8条离线示例。
- `web/src/components/world/JuyiHall.vue`：只在实际选中详情关闭、当前为tasks时，清空选择后复用 `loadTasks()`。保留现有关键词/状态/能力条件、加载/错误及计数处理；不增加watch、轮询或状态机。
- `web/tests/juyiting-component-behavior.test.js`：两种布局实际挂载JuyiHall+BountyPanel，验证首次直达详情返回触发一次查询、卡片渲染、筛选保留、重复清空不重复查询。修复前2失败，修改后通过。
- package.json/package-lock.json仅发布版本更新为1.16.29。

## 固定源码与定向证据

- 原HEAD和查询时origin/develop：`3fe5125e3c40eeeadf89e0b15e78e3902389a761`。
- 业务修复commit：`06baa5f99e778901ae4a9da001de79487c2e554b`。
- 最终版本commit：`e69507b8de111847cc6ca481f9196eb83eb4e950`，tree `1e9f9cad6578c7434a6d4358b337350e1eff0fed`，已push组件develop。
- 本地定向：组件/导航/point-and-start 181通过；组件/hall-data 137通过，有重叠不相加，不替代正式Flow。
- 私有证据 `/var/tmp/cyf-task-return-20261021/`：red.log、targeted.log、data-targeted.log、browser/修复前PC和移动截图、离线原型截图。

## 发布记录

- Flow4403172 Run266：3157通过、0失败、2既有pending；构建/扫描成功，部署失败。Owner漏同步包版本，制品1.16.28与显式目标1.16.29不符，被安装前校验拦截。未绕过校验，未将其标为上线；本次失败不是业务测试失败。
- 补齐版本后固定新commit，候选/恢复配置及证据在 `release-r2/`，使用独立备份路径；不覆盖首次失败证据。最终发布/线上结果如下。

## 最终结果（2026-10-21 07:20前核验）

- Flow4403172 **Run267 SUCCESS**；3157通过、0失败、2既有pending。部署单71487624：Success、主机healthy。版本 **1.16.29**，上述最终commit/tree。
- 同Run制品SHA-256 `d347694a5929c112a2d233e84ef7f7b3aab412c467c240b0010c58ce47c10bdf`（106717235字节）；366个安装文件与manifest一致；浏览器实际加载index及JuyiHallEntry JS/CSS与安装内容一致。API未改。
- PC1440×1000、移动390×844且pointer:coarse：新开页面→办事待点将卡片→详情→返回，显示1条待点将事项，状态计数正确；不是隐藏DOM推断，已截图。筛选榜号488后列表→详情→返回仍保留488并展示对应卡片。
- 离线返回：列表/计数读取错误可见；恢复网络点击重查后卡片与计数恢复。最终真实空态：自建测试事项488取消后，返回显示待点将0，无误装载为“—”。
- 原先可读的用户事项480在核验期间由外部操作转为进行中，本次未修改；为重测待点将创建明确标识的测试事项488，未点将、未调用Agent/扣费，验完通过正常界面取消，仅保留取消历史。
- 流水线已恢复本轮开始前非自动部署配置，readback SHA-256 `31883fd59c9a33ef4847979fd99147375fda555d99498f17bc8cc5a6b94c389b`。
- 证据：`/var/tmp/cyf-task-return-20261021/release-r2/` 中status/deploy/web-artifact/artifact-verification/public-assets/browser-verification/restore-result；截图及只读网络日志位于同级browser目录。浏览器为独立Chromium及移动触控模拟，不宣称实体手机全覆盖。本次仅闭环本问题，不扩称其他业务全量验收。
