# 点将首轮动作与授权集合合同 v1

日期：2026-09-30。冻结施工合同，未实现/验收。

1. `AgentTaskAssignDTO` 增加可选 `initialOperation`；v2 assign_and_start 的 `requestedOperations` 仍是整个授权集合，初始动作必须是同一既有操作枚举并属于该集合。严格原样校验，不trim/按顺序挑选/依文本重分类。允许例如集合 `GENERATE_IMAGE,EDIT_IMAGE,INSPECT_INPUTS`，首轮明确 `GENERATE_IMAGE`。只形成一个bootstrap outbox、一个首轮request/step/execution intent，不同时执行集合。
2. 缺失initialOperation只允许旧v2兼容路径：沿用当前单个非INSPECT动作（或INSPECT唯一动作）的确定推导；歧义仍400。旧legacy未声明v2不变。不得把旧歧义请求暗自选成新动作；能力声明不因增加字段而冒充EDIT_IMAGE已可执行。
3. 初始动作持久于已有outbox.permitted_operation；grant保留完整集合。生成/重放校验使用固定初始动作与集合成员关系，不重新从集合推导覆盖已有outbox。明确selector改变属于幂等异正文409；同原键同正文只复用原outbox，撤回/重派历史规则不放宽。缺grant/half outbox/integrity漂移失败，root锁/事务不变。
4. 哈希兼容冻结：缺失selector请求的requestHash保留原 `ASSIGN_AND_START` 输入字节；显式selector使用新domain `ASSIGN_AND_START_INITIAL_OPERATION_V1` + 与原hash相同的task/canonicalAgent/expectedTaskVersion/requirementRevision/operationsJSON/inputsJSON +末尾\n+initialOperation；两域不能混合或自动重写旧record。原key增加/删除selector属于正文变化，409。既有bootstrap.payloadHash算法不改，只绑定已选动作。
5. 原操作只读投影同样接受完整授权集合，仅校验outbox持久动作在集合中；不对整个集合调用旧implicit推导。对grant.requestHash分别按原hash/新域固定动作核验（现有assignmentVersion与version-1两个合法写入来源保持）；旧域只接受旧可确定集合，新域必须核验所记录动作。GET不得写/claim/Provider，不自动补初始动作。
6. 最小测试：显式生成+编辑+INSPECT单首轮；显式INSPECT；selector缺失旧单操作原hash字节/replay；歧义缺selector400；不属于集合/unknown/blank/大小写/padding400；同键改单初动作/selector有无409；同集合不同顺序规范一致；persisted动作漂移/缺失失败；原读取投影新旧域及零副作用；身份/版本/引用ACL、撤权/START和收费边界不变。
7. 不增加表/列、费用开关、Provider、Chat schema及工具。实现不使新grant允许OwnDerivedAssets自动true；后续会话资产引用/EDIT_INPUT另包按真实ACL实现。
