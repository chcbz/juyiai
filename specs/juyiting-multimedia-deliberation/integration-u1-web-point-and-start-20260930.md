# 原点将意图与只读恢复：源码整合证据

日期：2026-09-30。Web `7ac3bbc3fd21bfb1b053a8fbe249cc2b17d42a1d` / tree `665b0ace4abbcdc5c5fa1c0d91c3436d9c8c77a1` 已正常快进到融合feature并push/readback。这是ENTRY-W的独立恢复组件，**尚未接实际页面或协商服务端能力，不是产品验收**。

## 实现

- 新 `useHallPointAndStart` 读取真实current requirement与canonical TaskDTO，检查同一版本和open状态，固定显式点击目标、操作集合、初始动作、可空引用；拒绝无法安全表示的写入数字。读取期间修改引用草稿不改变原正文，改变显式目标不能悄悄替换Agent。
- 首次POST前owner/task-scoped持久并readback原key/body；存储损坏、失败、已有原操作不创建另一意图。不传私有目录、工具或费用授权字段。GET404不证明未受理。
- `start`是首次明确动作；`checkOriginal`是纯读核对（mount/刷新用它）；`resumeOriginal`只允许用户明确恢复时、原操作确切404且从未确认后复用原key/body。401/403/500/503、已确认或已有投影都不重写。读取PENDING/RETRY仅显示准备中，不補发首轮。
- POST grant核对独立于TaskDTO；不 `Object.assign(task, grant)`。读取原键projection，区分root/grant/outbox版本，拒绝独立版本回退、同fence事实漂移、已确认ADMITTED退回或已撤权grant复活。保存确认facts先于可能失败的榜文/历史读取。
- ADMITTED且当前assignment真实匹配后只读canonical task，root已前进时再读原操作检查实际assignment，不拿taskVersion当assignmentRevision。向页面集成回调交接canonical task和精确bootstrap引用，不查会话列表第一条、不新建会话、不重发需求。
- scope变化/dispose隔离迟到响应；保留原scope恢复记录，不覆盖新身份界面。回调必须在实际异步状态更新前检查所交付的`isCurrent()`，并复用已实现的`adoptBountyBootstrap`自身task/target/request fence。

`start/checkOriginal/resumeOriginal`返回true仅表示匹配的原操作事实成功读取；应以status及权威回执决定页面呈现，不能把返回值当生成/任务完成。历史原操作可查看但不自动作为当前办理。

## 验证与证据

7文件定向回归 **182 passing，0 failing**，本组件 **45项新增**。包含既有fast、会话、首轮采用、multimedia与legacy/funded/多选TaskActions回归；仍是受控API/存储的实际composable测试，不是浏览器/Provider。

新增三文件ESLint、Node语法与diff-check通过。测试源字节与已提交树逐文件相同，无需对同树重复完整测试。缓存key `68870c05220cb33467b5df766df5f9b49acfcf776396e8f84d668b312b67b03e`。保留首轮测试fixture规范化差异失败并精确修正；控制面首次证据登记因ledger仍指父树被拒绝，更新确切已提交树后才登记成功。

[便携证据](integration-evidence-20260928/u1-web-point-and-start-20260930.json)含manifest、fixture、selector与日志SHA-256。

## 不足与下一包

1. 实际`JuyiHall`/`useHallTaskActions`仍旧点将；新组件未接页面，`isSupported`默认false。UI flag不是授权；服务端明确能力协商合同/源码还须补齐，不得凭测试注入true广告上线能力。
2. 参考文件必须实际入榜并具有ACTIVE scoped task-file link；本组件只固定引用，不伪造关联。跨标签页真实浏览器恢复及互斥未验证。
3. current requirement/projection/finalization/initialOperation候选未正式整合与测试。API pin仍`194ec91a`。Owner新候选`05ace019`与`c75ff0af`仅静态；发现Controller selector-only路由缺口另交独立修正包。
4. schema readiness v2实际执行5项、3失败已保留；归因为fixture未启用条件archive initializer。纠正候选`399cb3c3`仅补条件，未削弱断言，v3在验证；不能称正常构建/真实MySQL已通过。
5. 真实上一稿resolver/修改/澄清、费用授权服务桥、双接应、Provider、浏览器、版本化发布与34项产品验收仍未完成。**不通知可验收。**
