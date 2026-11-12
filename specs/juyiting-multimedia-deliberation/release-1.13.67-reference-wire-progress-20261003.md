# API1.13.67：参考图查询与来源序列化修复（2026-10-03 20:30）

**已发布后端修复；完整多媒体34项仍未完成。** Web保持1.13.64/Flow4403172 Run164（含e586语音SVG），Client保持1.13.62；不重复前端合入、构建或Provider调用。

## 发布与实际验证

- API `b8053da6cea338d6ee0d35d99ed4da531cae9bf2` / tree `9a456f4106e675f61d3766940ea72887af0c6103`，已非force推develop并冻结release/1.13.67。既有API本地授权 `local_user_authorized`，正常生产图bootJar；**不是Flow成功证据**。
- 本次真实Spring HTTP converter、V3执行/START与runtime路由10 PASS/0fail/0skip；查询修复复用8359源码的29项通过证据，不宣称同次跑了39项。离线用线上JAR中的原DTO/真实Jackson、候选DTO，以及实际已部署Client严格解析器，确认GENERATE/EDIT两类旧格式拒绝、修复格式通过；10项负向仍拒绝。
- JAR SHA256 `1d454902c6b27ac3149e4626ed79e20d7806f596a61872dc5175d0e6c375adfc`，PID19026，scope `cyf-api-release-1-13-67-20261003-main.scope`，实际HTTP200/UP。配置及launcher不变，无迁移/生产DML。
- 全部monitor CLI在release锁外：pause/status→锁内marker哈希、PID/JAR CAS、安装/健康→解锁→status/resume/status。正常单次成功，maintenance=false/in_flight=null，无解环或foreign进程控制。
- API重启后浏览器实际跳登录，正常UI重新登录；原419相同意图键只读GET由500恢复200，bootstrap ADMITTED、同会话及v2/原摘要不变。原419仍FAILED且Provider START均null，未重放、未复位。旧418验收成果不变。

## 有据缺陷与归因边界

后端RuntimeSource是两种source的联合record。HTTP默认序列化输出13字段（不适用的字段也为null），Client则按workspace4字段/asset10字段精确校验；非空参考或改图在Provider START前会拒收。最小修复仅在该record加NON_NULL，并声明已有catalog的Jackson annotations依赖；不改全局mapper、字段类型、摘要、授权、grant、租约或Client严格校验。

新增两个实际HTTP序列化case红测均失败（10项中2失败），修复后10绿。中间编译失败已归因为API模块缺annotation依赖，明确补已有依赖后重测；离线helper首次猜错缓存core版本也如实记录，改用线上JAR内精确库后通过。**未捕获419当时inputs-v3 HTTP响应，故这证明独立可复现的线上二进制合同缺陷，不声称已证明419历史失败的唯一原因。** 新正常业务意图的runtime字节/生成仍待实测。

## 下一步与边界

通过新的正常任务/明确业务意图继续参考图与local接应，验证实际v2字节、生成后无刷新显示、同会话改图/旧新稿共存，再补音频/文件、权限和恢复。不能重放419/418 START，不能用旧FAILED任务伪报恢复。仅本地spool、服务端无stage的上传恢复仍未实现。

语音协作Main指定ID的send_input返回agent_not_found，本轮不声称跨线程通知已送达；本线程保留已上线证据，无需对方再推或开Run。

证据：[发布回执](integration-evidence-20260928/release-1.13.67/release-result.json)、同目录浏览器GET200、只读SQL、红绿摘要、跨语言检查、制品及监控回执。
