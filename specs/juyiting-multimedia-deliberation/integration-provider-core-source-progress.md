# 受控图像与外部请求同意 core：精确源码整合补充

本文件记录本次融合研发进展，**不是产品验收或发布证明，也不是第二份执行台账**。采集主机时钟单列在[便携 manifest](integration-evidence-20260928/provider-core-source-progress/manifest.json)，不当作当前对话日期或发布日期。历史切片及失败证据保留原含义。

## 1. 已提升的研发 pin

| 组件 | feature commit / tree | 证据及实际范围 |
| --- | --- | --- |
| API | `083f9846ee26835e6db79892e4f7186accff467a` / `fbc21df09279e7924d997b11b56ed59039bfa475` | 保持此前已验证参考图入口基线；consent候选尚未整合 |
| Web | `1ceb48d45648e0c6ebaaa7283ce72a724acf9b70` / `2a1b4d47237f9cc779a7ce7e9f5a8a5add9cc2d6` | Owner 69/69定向通过（23 consent、46原point/start）、scoped ESLint/diff检查通过；Main字节精确FF并推送/readback，不重复未变树测试 |
| Client | `69765549f4cf2e157e8c076998eb98243198599e` / `37e8bc55e4da43d8615277a61583cd4feddd7f7c` | Owner193通过，失败/取消/跳过/todo均0；Main核对真实日志hash、cache、树及远端，精确FF/push，无真实Provider |

三组件 feature 均经远端 readback，包含最后fetch的fast HEAD；本次不冒充重新fetch了fast。四仓分支与长期详设交付的前次最新fast核验仍见[交接](fusion-delivery-handoff-20260930.md)。包含fast不代表包含最新develop：发布前须收敛语音等真实修复。

## 2. Client core 的实际能力

- 仅显式operator设置endpoint、model、API key环境变量名、binding/epoch及本profile私有持久ledger时可用，不提取CODEX登录凭据、不默认选账户/模型。
- 最多16参考资料；无参考使用generation，有参考使用JSON edits。仅在实际native START成功后调用。
- 持久排他claim/fsync与稳定command身份限制同一意图并发/重启外发；一次fetch，无重试、fallback、重定向或模型URL下载。
- 一次HTTP尝试不等于一笔已知金额、不承诺网络exactly-once。失败/未知仍保留claim，不自动删除重试。
- 不放宽旧native-v1的32输入广告或fast-v1无工具边界；尚无合法服务端费用桥，生产默认关闭。

原始日志压缩归档在[Client日志](integration-evidence-20260928/provider-core-source-progress/client-final-exact-tree-node.log.gz)，解压后SHA-256为`25fe22ffdb581fdfdf95a9c1bcd92722b83503a129636143ae512dfc3b39cbee`。对应exact tree/selector/fixture的cache记录在manifest。Main不把此前或未改变源码的测试再次算成新执行。

## 3. Web v1.1 修正

依据[冻结Web core合同](web-provider-consent-core-contract-v1.md)接issue/query/revoke：共享原点将持久slot，原assignment与consent的key/body先整体持久/readback，再发POST；普通flow不能绕过该扩展调用legacy assign。

v1.1允许真实API的同版本active→EXPIRED只读投影，保留immutable/终态/版本规则；过期可原version显式revoke。缺少显式ack零存储/零POST；同身份task/target切换使迟到响应失效，不删原意图、不取消服务端办理。

[Owner最终自检回执](integration-evidence-20260928/provider-core-source-progress/web-owner-self-check-v1.1.txt)与[原65项自检](integration-evidence-20260928/provider-core-source-progress/web-prior-owner-self-check-aec7686.txt)分别保留。未提供完整Mocha原始stdout，不合成日志；最终69项来自Owner终态回执及accepted cache。修正中曾有高version EXPIRED处理错误，改变源码后已通过，不把首轮失败改写成成功。

## 4. API候选与验证限制

API `acab34116c3eba9a92d431b8863df47219c6b544` / tree `18348bbfeea78d936087ff59943197f04ce168bc` 已修正final类无法CGLIB代理及同名弱CHECK可通过的问题，增加真实Spring read-only事务、13CHECK完整谓词和MySQL规范化测试，但**本次记录时未获得执行通过，不提升API研发pin**。

此前正常全依赖图两次被kernel global OOM终止，0测试/0XML，不能按测试失败归因源码，也不能宣称已验证。原mini验证Agent另因model_not_found退出，未执行测试；已换可用验证通道，采用不同低足迹tiny源码验证器。首次resolver缺少CI publication extra，在编译前失败并已归因；私有init修正输入后继续，不重复原全图OOM候选。tiny结果即使通过也不证明正常全模块编译、整套启动或生产构建。

## 5. 仍未完成的完整范围

1. 合法operator delegation与owner exact consent接入Grant、唯一execution预留、同事务consume+START；非空costRef不能代替授权。
2. 受控16输入版本化协商及页面显式同意、原键点将、同一悬赏议事自动采用。
3. 同会话澄清、续办、上一稿EDIT及精确会话资产输入解析；全部文本/图片/音频/文件展示、保存与正式交付验收。
4. 双接应真实浏览器及34项产品用例、最新develop融合、精确版本制品与部署/线上验证。

本次未合develop、未生产构建/部署或生产DML/迁移，未选择/启用真实收费账户，未调用付费Provider；34项产品用例保持**NOT_RUN**，不通知“可验收”。下一执行包优先封闭合法费用Grant/START桥，不停留在默认关闭core。
