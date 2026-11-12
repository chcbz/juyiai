# 1.13.10 本机发布状态（2026-09-22）

> 最新：原型纠偏 `1.13.10-uxfix3` 已发布，Web6726cc0；300项回归、31项fixture浏览器、真实账号HTTP6/UI27通过。详见 `prototype-correction-20260922.md`。下文保留初次发布历史，不能作为最新原型一致性结论。

## 当前结论（14:57）

**1.13.10 技术发布已完成，可请用户验收；不等于全部业务验收通过。**

- 当前 API `787ae631264d0ae323fcce48957cb71c1cae52c8` / tree `d99e39b1d7518ad6a548d97e1bc3979c9f7a33ae`，冻结 `release/1.13.10-fix1`；Web仍 `b8bd0de760e1532ac168bc6a45e741c94a41e571` / `release/1.13.10`。
- 14:51:20 API-only安装实际exit0且健康UP；原API恢复件、锁/进程身份、Web字节不变已核验。无WX ALTER、无Eva/Flow、无Nginx或Runtime重启。
- 14:56真实账号只读HTTP **6/6通过**，此前草稿列表503已变200；地图/概览/能力接口正常，匿名访问被拒绝。
- 真实线上浏览器 **6/6通过**：默认地图已到ready且canvas可见；844×390百宝箱为820×374单窗，无“回聚义厅”；概览隐藏但保留地图；恢复草稿GET200；方向入口存在，切换390×844视口后编辑器仍保持。只证明浏览器仿真，不冒充真机或手动宿主方向完整验收。
- 浏览器19个API请求均<400，无被拦截请求；未保存草稿/上传/执行Provider或修改生产数据；临时浏览器与私有profile已关闭/清除。
- 初次浏览器检查将canvas的`aria-hidden`误当物理不可见，属于测试谓词错误；保留失败与归因，修正后重测通过，没有改产品来迁就测试。
- 初次重启后的概览请求11.049s，后续同接口0.066s，仅记录冷启动观测，不据此宣称性能达标或因耗时拒绝业务。
- 准确来源、摘要与边界：`verification-20260922.json`。用户操作清单：`acceptance-guide-1.13.10.md`。真机、真实收费文件闭环、R01 Runtime激活、目标用户试点仍未验收。

## 首次安装来源与验证（历史基线，fix1见当前结论）

- API：`6cc769ad71d403d8a2be7ecf3b15948f40d9fd91`；tree `bfb3b523c78286d7d85a99d8e1fcf4244b4ccdb2`。
- Web：`b8bd0de760e1532ac168bc6a45e741c94a41e571`；tree `73cf89d63e1183860ab2702a83c486f53d8e73fe`。
- 两组件已 fast-forward 合入远端 develop，并 create-only 冻结 `release/1.13.10`。未覆盖既有分支、未修改 dirty 根 checkout。
- `build_origin=local_user_authorized`；Flow Run=null，没有恢复 Flow 自动触发，也没有使用 Eva。
- API 定向回归117通过、零跳过；bootJar真实exit0，mandatory公共制品64项及POI2项通过。
- Web最终14 selectors共294通过；生产构建真实exit0。构建生成的声明文件只恢复本次生成差额，最终源树clean。
- 实际浏览器复验关闭两项横屏问题：百宝箱374px高度、首屏文件与操作可达；办事概览优先办理信息、保留而隐藏地图实例。固定v1资料草稿保存/恢复由本机API夹具验证，不等于真实Provider闭环。

## 安装进度（12:41观察，尚未宣布完成）

- 发布预检PASS；12:38开始持久journal与锁保护的实际安装。
- API原件已保留；canonical launcher停止原进程并于12:40启动新制品，等待真实健康。
- 只有新API健康后才切换Web；本节不会把启动进程或健康等待写成上线成功。
- 制品与完整证据：`deliverables/releases/v1.13.10-local-20260922/`。

## 验收边界

- Runtime只分发固定源码包，现有Agent未更新或重启；未进行新的付费Provider生成。
- 原生Android/iOS/微信、完整方向/下载和全部A01–A22业务验收未全部完成；不以截图或单测替代。
- 本机预览分片夹具的MIME错误单独保留，不能作为产品失败或预览通过证据。
- 发布后主控将核实际制品、服务健康及已授权账号只读Hall接口，再通知用户验收；真实业务价值仍须按验收表确认。

## 首次安装与真实账号核验（12:54更新）

- 12:45:28 安装进程真实 exit 0，持久 journal 为 `DEPLOYED_HEALTHY`；API 实际健康后切换 Web，未重启 Nginx 或现有 Runtime Agent。
- 原始记录：`/opt/cyf/service/api/release-records/jyt-ux-1.13.10/JYT-L01-20260922/journal.json`；新 API PID 1440287/startTicks 3162454874。
- API SHA-256：`af82eb5495df4d1d1f6fc55b1e65ef37a806e6362b9b9f8d699425c6978f1dc2`；Web 包 SHA-256：`036df46668e52c3b782cf367841d5dc94c190b623bdc5b8810455d3b4b745bee`。
- 用户授权账号经过真实 OAuth PKCE 登录后的只读核验：用户身份、办事概览（六个分区 complete）、能力入口、地图均 HTTP 200；匿名概览 HTTP 401。
- **未通过：正确请求 `GET /agent/hall/drafts` 返回 HTTP 503。** 服务健康不代表业务验收成功；目前不得标为完整发布验收通过。
- 完整只读证据：`deliverables/verification/juyiting-unified-experience-20260921/local-20260922/controller-online/installed-attempt2.json`。首轮探针错误另行保留归因，不当作产品缺陷或成功证据。
- API Owner 正在定位草稿列表真实 SQL，确认根因后补隔离 MySQL 回归与最小修复。原 `release/1.13.10` 不移动；修复使用独立冻结 ref/制品，Web 无变更复用原包，不重复构建。

### 12:58 根因已确认、修复中

从已部署同摘要 JAR 的 mapper class 常量池读到 `<script>\nSELECTdraft_id,...`：Java 文本块移除尾空白，导致 SELECT 与列名之间无分隔。原数据库提交夹具未调用真实列表 SQL，原 mapper 测试仅检查 ACL 字符串，未检测 token 拼接。证据 `deliverables/releases/v1.13.10-local-20260922-preparation/draft-list-production-diagnosis.json`。修复 Owner 已在独立分支修改 mapper 并补 BoundSql 与真实 MySQL 列表回归；此处不预报测试通过。

### 14:29 修复回归通过并冻结

- API修复 `787ae631264d0ae323fcce48957cb71c1cae52c8` / tree `d99e39b1d7518ad6a548d97e1bc3979c9f7a33ae`：真实 BoundSql + 隔离 MySQL 空列表/首页/跨页同时间排序/owner、client、大小写身份隔离共10项通过，零失败、零跳过。原117项属于此前6cc树，单列复用，不冒充新树重跑117项。
- 新回归首轮因离线环境缺发布属性而未启动测试，已归因；补齐测试环境后第二轮真实exit0。详见 `deliverables/verification/juyiting-unified-experience-20260921/local-20260922/fix1-owner/tests-attempt2-summary.json`。
- 并行任务已向 develop 提交独立 WX 变更fd47。主控非覆盖合并为 `20ae5fb3b14dcce8dfa17b483dbf19fb5e240441`，核对双方路径不重叠且文件blob逐个与原件相同；没有覆盖对方提交。
- create-only `release/1.13.10-fix1` 固定787；该提交已作为merge parent合入develop。本次只发布787最小修复，**不发布WX代码或执行其ALTER**。原 `release/1.13.10` 仍6cc。版本仍1.13.10，build修订fix1独立留证。
- 发布Owner接续暖树生产构建和API-only安装，未将测试成功当作修复已上线。

### 14:48 构建完成，API-only安装执行中

- fix1暖树生产构建真实exit0，11分48秒；制品SHA-256 `bad06e5a5b8b7421119e32cad8669610c6d4249b940b86f342f2975a706a4d6c`。
- 发布目录：`deliverables/releases/v1.13.10-fix1-local-20260922/`，独立authorization `JYT-L01-FIX1-20260922`。保持最小修复源码787，不含WX ALTER。
- 14:45通过canonical launcher停止原API，14:45:59启动新PID1518439，等待实际健康；Web未切换，原API af82已作为本次恢复原件保存。
- 此时仍未再次执行真实账号/浏览器探针，不能将“Java已启动”写成接口问题已解决。
