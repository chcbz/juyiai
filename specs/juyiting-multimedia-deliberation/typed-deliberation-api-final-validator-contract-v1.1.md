# typed final 校验合同 v1.1：空白语义分域澄清

冻结日期：2026-10-01。增量于[原合同 v1](typed-deliberation-api-final-validator-contract-v1.md)，**不改写原合同、黄金 fixture 或原30项 NOT_RUN 状态**。继承原3叶子写集/纯函数/授权边界，仅精确定义各字段的 nonblank；后续正常图编译/JUnit另冻结。本澄清不修改普通 CHAT 或任何 HTTP/wire/摘要结构。

## 1. 实际依据与需要澄清的差异

[语言运行时与基线源证据](integration-evidence-20260928/typed-final-v1.1-whitespace-domain-evidence.json)：实际 Node20 `String.trim()` 把 NBSP(U+00A0)、BOM(U+FEFF)判作空白，JDK21 `String.isBlank()` 对它们为 false；U+001C 正相反。基线 API `9798951` 的 `ChatDeliberationService.requireContent`、`requireIdentity` 使用 Java `isBlank()`，身份同时校验 `strip()` 和 ISOControl。

候选 `7f6e54b8` 将三类字段统一使用 ECMAScript 空白判定，源码显示会接受仅 U+001C 的 content，而既有 persistFinal 内容域拒绝；也会额外拒绝既有身份域允许的 NBSP/BOM。应用测试尚未运行，不把语言运行时证据冒充产品缺陷已复现。为保证后续接线使用一致的既有域，应分域而不是全部替换成同一个 blank helper。

## 2. 精确字段规则

| 字段域 | 非空规则 | 其余规则 |
| --- | --- | --- |
| typed outcome 的 text / clarification.question | 与已接受 Client 的 ECMAScript `String.trim().length > 0` 等价 | scalar有效；保留原文/LF；不套 instruction 的 ISOControl 禁止 |
| instruction / sourceRefId | 与 Client 相同的 ECMAScript 非空 | 原4000 codepoint / 512 UTF-16界限；ISOControl禁止；source权限来自可信目录 |
| API content | 非 null、`!String.isBlank()`、≤200000 UTF-16、scalar有效 | 不 trim/normalize；随后完整 outcome 校验且与 text exact相等，因此还须满足 text 的 Client 域 |
| API binding 的 opaque identity字段 | 非 null、`!String.isBlank()`、`equals(strip())`、scalar有效、无ISOControl、原长度上限 | 沿已有 API 域；不把 NBSP/BOM按JS规则额外禁掉；数值ID、route、tenant、contextDigest仍沿v1专门规则 |

接受 binding 字段值只表示纯函数结构校验通过，绝不证明该身份在数据库存在、属于当前用户或拥有执行权限；完整 callback/turn/snapshot 仍由服务端可信源与事务验证。

约束交集示例：仅 U+001C 的 content 先报 INVALID_CONTENT；作为问题的 U+001C 可在正常正文下通过 Client prose 域。仅 NBSP/BOM 的 content 在 API 单域非空，但其相同 typed text 不满足 Client 非空，因此报 INVALID_OUTCOME。instruction/source 中控制字符仍拒绝。U+200B 不因视觉不可见就擅自新增拒绝规则。

## 3. 规范化与摘要

这里只做验证，不改字符串，不去首尾空白，不替换控制字符；valid输入的 canonical digest/完整14字段/五键union/数学版本1规范化保持v1。中文CLARIFY黄金摘要不变。异常仍沿固定6类Reason，不向外输出正文/凭据。

## 4. 施工与验证

Owner在原3叶子范围修正 API content/binding与Client union的分域 helper及测试，保留原fixture字节、所有原30语义用例；新增[8项域边界预期](fixtures/typed-deliberation-api-final-validator-v1.1-whitespace.json)。原fixture expectation不可因为测试声明就改PASS，运行后另记 exact SHA/tree 与 fresh JUnit XML。

主控另冻结正常生产编译→独立测试阶段，严格保留正常依赖/AP/源码图、无需DB；不手工javac或class copy。纯校验通过仍不关闭 typed final原子落库、pending CAS/resume、自然多轮、INSPECT、双接应、浏览器或发布。
