# 任务参考图输入：源码融合与当前缺口

日期：2026-09-30。本补充只记录研发源交付，不改冻结合同，不新增运行台账。长期目标仍以[融合详设v2](fusion-detailed-design-v2.md)、[媒体/存储详设](design.md)与[任务关联参考图合同](task-linked-reference-point-and-start-contract-v1.md)为准。

## 1. 分支与长期方案交付

四仓均已建立并推送 `codex/juyiting-multimedia-deliberation`，本次再次核验包含各自当前远端 fast HEAD，见[分支快照](integration-evidence-20260928/branch-verified-progress-20260930.json)。该快照采集在下述两次源码提升之前，保留当时精确HEAD；提升后的API/Web远端readback见[整合manifest](integration-evidence-20260928/task-linked-reference-source-20260930/manifest.json)。

最新develop独有提交：SDD 1、API 4、Web 4、Client 0。API新增 `b2986836` Redis4语音Lua修复，另有语音Provider及测试；Web有PCM/WAV及确认发送改动。**已合入fast不等于已收敛最新develop**，上线前须保留这些真实修复并补交叉验证，本次不合develop、不发布。

长期方案不是两套聊天系统的短期兼容：统一conversation/request/turn/event/asset，fast只是CHAT策略；INSPECT/EXECUTE按本轮受权精确内容和实际能力加载。明确且已授权的生成可直达执行，不强制先CHAT。唯一过渡层是旧协议适配，退出须有客户端迁移及在途恢复证据。

## 2. 本次精确源码提升

| 组件 | feature commit / tree | Owner最小相关自检 | Main整合范围 |
| --- | --- | --- | --- |
| API | `74b4b44e65dac2e705c4ff7e83f83d7ba0d314e0` / `4b39f2521e7bc1c6363aeeac650475bae4abfe27` | capability/controller/coordinator 18、纠正包名后的native declaration 2、grant 24、conversation native inputs 22；66通过，无失败/错误/跳过 | 从5668精确fast-forward，tree及远端readback一致；不声称Main重跑 |
| Web | `7821209c874995621d139da9047983f3b586d0b0` / `d829db4ca8084cd10f1d68b0ae553ecf1d9e666a` | 108通过，无失败/跳过；7个JS/test路径scoped ESLint通过；实际Hall script/template编译及真实resolver→point/start组合 | 从84b14精确fast-forward，Owner8个改动路径和日志摘要核对，远端readback一致 |
| Client | `1812e5b5d090013338265d16ca34b0b9c257da49` / `430296285683b3597f7401c21e7368c5fd078107` | 复用此前Owner172证据，未重跑 | 本包无Client改动；不推断两种接应已经安装 |

便携证据与四个API accepted cache记录见[manifest](integration-evidence-20260928/task-linked-reference-source-20260930/manifest.json)。API计数来源是Owner终态回执及串行orchestrator记录，不把缺少原始stdout的记录伪写为完整日志。初次全局OOM、首次native测试包名错误及随后正确selector保留原意义。Web全量Hall模板仍有既有108 errors/80 warnings，base/current诊断完全相同、候选script诊断为0；不将全文件lint标PASS，不修无关模板。

旧Web84的213证据仍属于其原精确树，不累计成当前782树的完整测试数。源码自检、组合HTTP夹具、整套启动、浏览器产品验收和发布是不同事实。

## 3. 参考图处理与权限不变量

API新增默认关闭 `agent.task-reference-inputs.enabled`；真实storage/native链路就绪才宣告 `TASK_LINKED_REFERENCE`，否则保持 `EMPTY_ONLY`。费用仍真实为UNAVAILABLE、paid=false、newStart=false。fast-v1 EXECUTE=false不变。

Web新点将先读取完整owner-scoped任务关联分页，再核对精确文件版本，JPEG/PNG、ACTIVE及重复/32上限均检查；latest不能替换关联旧版本。读取失败不是空目录，EMPTY_ONLY不能静默丢图；身份/选择/授权代际/迟到结果受栅栏保护。原key/body/refs优先恢复，不重新读目录改写原操作，不降级legacy。传统-only/funded动作不附加全局workspace门禁。

浏览器检查不是授权或锁。真正assign、执行准入、START和提交继续复用服务端task/grant/assignment/run以及实际资料ACL与摘要校验；资料目录不是Agent已读图片。提示词只说明run路径，不授予权限或提交成果。

## 4. 原子需求创建：实际MySQL失败仍未关闭

API intake `59ed4c32`此前Owner源码12通过、2个可选MySQL跳过，实际AgentService独立事务组合9通过。Main随后实际隔离MySQL8.0.21运行2项，**2项均失败**：新表创建后的初始化器在 `chk_atco_scope` 校验阶段拒绝实际CHECK_CLAUSE。

已捕获实际catalog及HEX解码原始字节：MySQL catalog对引号有一层转义，CLI batch另有展示转义，不能将二者混用。原检查只找关键词也不足以识别弱约束。原Owner正在限定initializer及对应测试修复，要求精确约束集合/ENFORCED、保留运算符/括号/字面值并拒绝歧义转义；不得删检查绕过失败。**候选尚未进入当前API研发pin，也不表示schema可晋升。**

本次失败证据保留于 `/var/tmp/cyf-mmd-main-api-reference-intake-20261001/`：`gradle-mysql-v1.log`、`mysql-v1-failed-xml/`、`mysql-v1-actual-check-raw-hex.json`。此前Owner12/9证据已先保存；诊断只创建/删除本线程前缀隔离数据库，无生产DML/迁移，无MySQL服务或外线程进程控制。目录名/日志时间保留采集原值，不据此推断发布日期。

## 5. 下一步与发布边界

1. 修复并验证原子创建schema，整合exact候选，实际MySQL及组合源码通过后提升API pin。
2. 建立合法且绑定真实Provider账户/用户/任务/目标/操作的费用授权来源；不伪造costRef，不挪用悬赏/钱包其他用途凭据。真实可能计费测试仍需明确授权。
3. 补同会话澄清续办、上一稿/EDIT/派生输入、全部文本/图片/音频/文件与混排、原意图确定拒绝后的权威无副作用退出。
4. 完成保存、正式交付/验收/领域完成与双接应真实联调，收敛最新develop；按exact版本制品部署并做全部产品浏览器用例。

完整34项产品用例保持 **NOT_RUN**。本包未合develop、未生产构建/部署、未生产迁移、未调用付费Provider、未做真实画鸟浏览器验收，**不通知“可验收”**。版本号依[分版本计划](versioned-delivery-plan-20260928.md)重新核对占用，不能沿用已被语音占用的1.13.45。运行推进仍只使用主工作区runtime ledger。
