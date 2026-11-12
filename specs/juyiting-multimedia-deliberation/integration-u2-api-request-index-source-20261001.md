# 同会话请求目录：API 源码接受（2026-10-01）

API `97989512351b6a409ac629e4546ce9fe698670e0` / tree `407555079ec0c17d5508cabdc01902c24cd7465a` 已精确 FF/push/readback 到 feature，SDD gitlink/pin同步。新增 owner/client/tenant/conversation/generation 精确隔离、固定through分页、完整既有 RequestView 投影与纯只读目录，不要求ACTIVE grant才可读历史。

首轮正常源图在Chat编译前发生daemon heap失败，0tests/0XML，证据保留。验证改为两个独立 invocation，保留正常依赖/AP/源码/init/heap与全部原测试，不复制class、不手工跳任务：production **compileJava真实执行，exit0**；test **9份新XML、62/62通过、0fail/error/skip**，含13新例与49回归，新例中隔离真实MySQL2验证102条分页、owner精确分区、低ordinal晚commit从0重扫及SQL只读。Main独立核对XML/log/source哈希、6路径授权、exactclean树、PID终态与ownedMySQL Unix/TCP身份和prefix空。

[便携实际证据](integration-evidence-20260928/api-request-index-9798-source-accepted/portable-manifest.json)。test原manifest复制的“All counts static NOT_RUN”计划句保留原件；实际XML覆盖该计划句，其他范围限制不消除：MVC为mock/manualJWT、service为直接实例/反射mock、MySQL为storeSQL，没有证明完整Springbean/事务代理/真实JWT过滤链/整套启动，需后续跨仓验证。成功不证明宿主OOM长期风险已解决。

Web `1993b88`目录已源码接受，但两仓真实联调和浏览器恢复未执行，不以来源通过代替34产品/29桥、双接应、自然澄清/真实INSPECT/媒体/发布。下一步收口typed原子final+pending CAS/resume及75路径每意图授权包，再做完整纵切。
