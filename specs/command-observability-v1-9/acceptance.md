# 验收矩阵（1.9.2已发布，范围内线上回归通过，待用户验收）

<!-- CYF-CURRENT-CONTRACT-20261107 -->
## 当前验收合同（2026-11-07）

**本专题：只读协作运行看板与异常定位。**

### 必须验证的业务结果
权限隔离、空态/未知/过期/失败区分、读接口无副作用、指标与原业务事实一致。

### 不回归边界
投递完成不等于任务完成；不从看板自动重试/重放/扣费/迁移，不为观测每片输出写库。

### 证据如何判定
- 绑定实际commit/tree、测试selector/fixture和输入；真实返回/数据库事实/页面行为只证明各自层，mock不冒充跨层验收。
- 必要身份/ACL、幂等、事务、锁及完整性保护按责任层覆盖；不在每个消费者复制同一防御矩阵。
- 性能使用真实同一请求/场景：请求数、查询数、读取字节、首字与完成时间分别记录；超标记录待优化，不用快速失败计成功。
- 以当前规则本地执行必要测试/构建并保存日志/制品摘要；本页历史Flow记录只证明当时输入，不要求重新付费Run。
- 源码接受、测试、安装、健康、业务验收分别写结果；不把历史PASS迁移到新tree，不补填未实测指标。

责任与DFX：[统一开发约束](../architecture-convergence/development-principles.md)。

**入口与阅读边界：** 文档状态、入口及阅读边界以[需求](spec.md)现行规格为准。

<!-- /CYF-CURRENT-CONTRACT-20261107 -->


1. capability允许/无权/关闭与JWT异常精确响应，不依赖DB/Rabbit，原D09授权不放宽。
2. 指标真实字段、只读说明、未知值处理、正确更新时间；不能以投递完成代替任务完成。
3. 非空DLQ/audit，字符串ID与游标完整、下一页去重、刷新重置；不出现敏感字段或mutation按钮。
4. 局部网络错可重试；旧数据标过期；401/403撤权清空。
5. 身份/generation变更、离开页面、请求乱序、分页在途刷新，旧数据不回写。
6. 个人中心入口发现、禁用/无权不可进入数据读取；直达/刷新/返回准确。
7. 桌面/手机横竖屏可读可滚动；1.8个人中心/经济预览/聚义厅往返仍可用。
8. 所有HTTP均只读GET；无Provider、生产写入、运维重放或服务操作。
9. exact tree相关测试、实际bundle、制品摘要与远端develop/release一致；release/1.9保留1.8祖先，不覆盖1.8冻结分支。

生产原read-enabled=false及用户ops-read权限不由开发任务放开；实际启用需有原授权依据或用户指定，不能将缺权限说成已验收。生产/真机/双真实账号尚未执行。

## 统一候选验证回执

API/Web exact SHA及树见 integration.yaml，所有证据在 `deliverables/releases/v1.9.0-local-ready-20260917/`：

- 条目1：新capabilities6项、旧D09只读ACL/DTO4项通过；JAR公共制品验证64项通过，未重复/声称API全量套件通过。
- 条目2–6：Web相关308项及经济只读策略7项通过；包含实际Vue mounted click、身份切换、卸载、分页在途刷新、403清空。修复真实点击MouseEvent捕获、ACK小数、游标严格前进、不可用原因、16列表头、未授权重试。
- 条目6–8：最终生产bundle真实Chromium99项通过：桌面/横竖屏导航、非空精确大ID、分页/刷新、网络错重试/过期标记、禁用/无权/404不读数据、403撤权清空、command-operations只发GET/OPTIONS。所有外网被mock，不是线上真机/真实双账号验收。
- 条目9：两个远端develop及release/1.9.0已readback，1.8祖先及原冻结分支不变；420个Web文件与制品逐项摘要匹配，API/Web制品SHA见readiness.json。
- 未把前两轮浏览器夹具失败改为PASS；错误桌面溢出断言、OPTIONS403导致CORS网络错均保留归因，修正夹具后得到最终99项通过。
- 未部署生产；不启用read-enabled、不发放ops-read权限，不操作业务数据/Provider/进程。等待用户安排统一发布。


## 统一发布1.9.2最终回执（覆盖上述待部署状态）

- 实际API/Web exact见当前integration.yaml；原1.9.0/1.9.1冻结分支保留。补齐线上hotfix后，修复真实回归发现的OAuth Controller同名遮蔽，未放宽身份/ACL。
- 新OAuth身份7+安全7+组合classpath1=15PASS；其余1.9功能源代码未变，保留上述隔离测试证据，不声称重新执行全套或全API。
- 真实OAuth/HTTPS API46PASS，完整本轮Chromium113PASS，无响应mock，无业务写或付费/语音调用。个人中心↔经济预览↔聚义厅、刷新/横竖屏、典籍内容/进度GET和看板无权提示均实际验证。
- 当前账号仅实际观察FORBIDDEN；未授予ops-read/开启read-enabled。DISABLED、特权非空看板、第二真实身份/client、真机、非空商品/成果正例仍未测；不能把之前99项隔离mock浏览器写成这些线上场景的验收。
- 首次API404、浏览器DOM存在性误判与构建工具失败证据保留；修正后新线上报告单独封存，不覆盖旧FAIL。
- 证据：`/home/isp/wsps/cyf/deliverables/releases/v1.9.2-regression-20260918/`；发布/用户步骤：`/home/isp/wsps/cyf/docs/implementation/V1_9_2_RELEASE_RESULT_20260918.md`。
- 技术发布与本轮回归完成，用户最终验收待回执；语音、交易、完整server-hosting及整体M5/G07不因此宣称完成。
