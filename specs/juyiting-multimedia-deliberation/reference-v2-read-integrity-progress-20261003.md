# 参考图固定版本实测与点将查询修复（2026-10-03）

**完整34项仍未完成。语音e586已在Web1.13.64/Run164上线；本轮不重复合入或启动前端Run。** API线上仍1.13.66/9d55，新增查询修复已自检FF到API develop `8359ec5de7e8f0c0772ca381240f2dd64ad61904` / tree `058eb65e1cb2ebe36becdfc1003e476adfdaa3b1`，尚未构建发布。

## 实际旅程

- 用浏览器新建独立参考文件 `pws_9e84e1e8ab25439b86339d1bf7a86018`，v1/v2均为原鸟图的明确测试副本；原418成果、工作空间原v1及正式验收均未改动。
- 从参考图选择器选v2，创建新419；之后用正常版本API追加摘要不同的v3测试截图，再点吴用。固定v2卡、创建回执、实际grant都保留v2及原图摘要2bc30dd5…，未被v3替换。v3上传脚本两项前置诊断错误（SyntaxError及plain-envelope假设）均在POST前停止，整改后只一次版本POST201；不冒充产品失败。
- 实际UI完成本次精确业务consent（未知外部费用明示、单次请求）并点将；没有引用voice33/500作为图像预算，没有伪造grant。原POST201后GET assignment-operation500，停止重放。
- 生产只读SQL确认bootstrap已ADMITTED到会话1760458004762；原execution已经FAILED/AGENT_DELIVERY_FAILED、Provider START两个字段均null。**未自动进入议事是浏览器观察，不能误写为后台尚未创建会话。执行失败根因仍未知，不归因于查询修复。**

## 有据最小修复

MySQL JSON列会调整对象字段顺序和空格；readInputs/readOperations却比较原始字符串与Java序列化字节，空输入通过，非空参考/多操作列表误判INTEGRITY_ERROR。

仅修改 `AgentTaskDeliberationOperationReadServiceImpl.java` 的序列化比较为严格JSON值比较，仍检查字段/类型、数组排序、重复项、摘要、grant/bootstrap绑定及全部owner范围/锁。重复键、额外/缺失字段、类型强转和尾随文档保持拒绝；无DDL、无生产DML、无授权扩张。

- 新增实际MySQL `CAST AS JSON` 与公开read投影红测：29项中2失败，其余27通过。
- 最小修复后29 PASS /0FAIL /0skip，含6项真实隔离MySQL与23项原bootstrap/读边界测试。通过orchestrator串行，`local_user_authorized`，不是Flow验证。
- 仅3个API路径（实现+2测试），干净候选已非force推特性分支及develop，readback exact一致；没有部署、没有声明线上修复。

## 仍需执行

1. 按版本发布查询修复，所有monitor CLI放release锁外；Web无改动，不重复构建。
2. 单独定位419 local输入阶段的FAILED；不能重置旧执行、删paid claim或重放START。若需新执行，使用现有授权内新的明确业务意图。
3. 继续AC02的runtime精确v2字节、AC07新生成实时展示、AC10未归档原稿改图、AC17双模式，以及其余34项。

证据：[固定回执](integration-evidence-20260928/reference-v2-read-integrity-20261003/verdict.json)、同目录浏览器/只读SQL/红绿测试摘要。截图 `/var/tmp/cyf-mmd-bird-delivery-main-20261003/phase2-reference-blocked.png` 已视觉核验。自有网络observer已关闭，无新Provider调用或runtime进程操作。
