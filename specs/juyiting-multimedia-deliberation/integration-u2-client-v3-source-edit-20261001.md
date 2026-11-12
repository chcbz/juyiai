# Client v3精确来源与上一稿EDIT：源码整合证据

日期：2026-10-01。只读状态补充，不改变冻结合同或运行台账，不是产品验收。

## 精确源码

Client feature已精确FF/push/readback至`71b26ce69d25a59f223499854b692e597b57d911`，tree`9675a2d85bf08a8e1af45d7c8e76106352db55a3`，父`5548052`。Main核对原矩阵允许11路径中的实际10路径、完整fixture/hash与工作树clean；旧executor文件完全未改。SDD更新Client研发pin，不提升未验证API候选。

已实现独立v3 command/snapshot/START严格parser、source-aware私有物化、operation-aware HTTP adapter、durable claim、独立inbox和真实factory组合。EDIT输入精确当前会话asset/revision/完整producer lineage，不要求先归档，不伪装workspace；生成输入仍限定任务关联版本。新long为decimal字符串，实际字节长度用BigInt比较。原v1/v2边界保留。

**声明强制disabled、operations=[]，controlledImageV3Ready=false**。production profile poller未调度本lane；只有后端每意图authority/source/START与真实组合完成才另行启用。API/费用/澄清未闭合不能由Client factory或mock广告READY。

## 实际验证及历史失败

Owner实际离线7selector：4个v3测试、v2 bridge、旧HTTP executor/runtime，43项全部通过，无失败/跳过。3个合法golden样例canonical字节/摘要解析一致，另有严格字段/来源/数值/操作变更与ACK丢失、receipt drift、claim并发/重启、无重复外发等覆盖。不是所有13个共同负向或29桥/34产品用例的验收；fixture内NOT_RUN状态保持原始合同。

第一次无loader：36项/34通过/2模块加载失败，根因是独占工作树没有yauzl依赖，两个runtime测试文件尚未执行；失败日志保留。验证修复只以只读loader解析真实`yauzl@3.4.0`，不伪造stub或源码通过。Main核对loader、真实index.js与package.json摘要，以及通过stdout的43/0结果。此验证不代表技能包运行路径验证；完整依赖安装及版本构建仍在后续发布范围。

[便携manifest](integration-evidence-20260928/client-v3-source-edit-71b26ce/manifest.json)保存两个原stdout、loader、依赖package元数据、owner矩阵和Main精确源码证明；gzip解压摘要与原件一致。唯一runtime ledger中该slice为source_accepted，不据此修改整产品验收状态。

## 下一步

API先融合当前develop语音差异，继而闭合每新EXECUTE独立授权/consent、实际asset来源resolver、v3 native wire及owner澄清/续办合同；Web composer与成果卡统一Hall follow-up，再验证双接应及完整图音文文件、保存/正式交付/验收/任务完成。真实Provider、账号选择、浏览器及版本发布均未执行，不通知可验收。
