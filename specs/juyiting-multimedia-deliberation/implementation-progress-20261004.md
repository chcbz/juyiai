# 分版本开发：第一批源码进度

2026-10-04。用户已明确恢复开发并要求按版本节奏落实；本记录是源码与验证回执，不是第二套运行台账，不是发布/用户验收证明。

## 分版本节奏

1. **入口与输入增量（T01–T04）**：复用现有创建/点将/资料/语音，先让主入口清楚、点将直接议事、＋输入方便、仅附件可发。
2. **成果与验收增量（T05–T06）**：明确本次成果与替换关联，补纯文字交付，去掉验收多选，复用现有 finalization。
3. **实际闭环与发布收口（T07–T09）**：边做边验证 Agent/媒体/保存/恢复，改动组件走既有正式 Flow，核对上线后业务闭环。

具体发布编号在就绪时读取线上版本、release refs 和在途 Run 后分配，不预留或覆盖历史 1.13.45–1.13.47。不为凑版本发布空增量，不增加审批或第二条流水线。未完成的第一批不抢先上线。

## 本轮已经改源码

Web 独立候选 `codex/mmd-ui-input-v1-20261004`：`58d631da0b0c1cccebf152f2f95b350db4bbe9a9` / tree `b7b81093d8796578c78c871fe443ebd8a005a872`，已推送并独立远端读回。基于任务清单指定 Web 候选 `12edde24`，不是旧根 checkout；未更新 SDD gitlink/pin，未合 develop。

- T01：事项主入口合为“提出需求”，正文必填；既有正式/私人领域编辑路由仍保留。资料选择器不再要求用户挑版本，沿用精确版本冻结、预览与下载。
- T02：点将册新增针对待点将事项的“点将并议事”；按钮传显式 Agent，父级传当前真实 task 并复用原 point-and-start。无待办只留密议；密议不调用点将接口。
- T03：资料、工作空间、历史/重取/另起话头和语音操作收进＋；资料目录与语音位于输入区域，顶部保留状态与取消。菜单支持外侧/ESC关闭、焦点恢复和上下文切换收起；语音停止转写先追加可编辑草稿，不自动发送，不改变其他语音入口的自动发送偏好。

以上为上一批 T01–T03 源码记录，验证仍非真实 API/Agent 产品验收。T04本轮已配套实现，最新候选及验证见下节；第一增量尚未发布。

## 实际验证

- 精确提交上 8 组定向 Web 测试：**229 PASS / 0 FAIL**。包含真实挂载组件与新增菜单、Agent CTA、转写入草稿回归；既有 HTTP/Agent mocks 不冒充真实 Provider。
- 本地 `npm run build` 通过，只作研发验证；有既有 chunk-size warning，未新增大小门禁，未发布本地制品。
- 改动小组件/voice composable和新增测试 scoped ESLint通过；BountyPanel既有11条、JuyiHall既有187条诊断保留，与原候选比较新增0。不宣称全仓 lint 全绿。
- `git diff --check`通过；原主工作区的脏 api、日志及其他分支未覆盖。

原始测试/构建/ lint日志及基线比较用gzip保留原始字节，manifest同时绑定压缩文件与解压原件SHA-256，避免Git换行归一化破坏回执；证据：[一次合并回执](implementation-evidence-20261004/ui-input-v1/manifest.json)。

## 本轮继续：T04附件-only已形成配套源码候选

Web `codex/mmd-ui-input-v1-20261004`：`f927f344ff24c07f92030a8c35140475b35a35b9` / tree `326034da26c72f9b3f37d926349596938abcd815`。
API `codex/mmd-attachment-only-v1-20261004`：`7a9418c3c4dfa5d4850b7eb02b091bdbaa2de88b` / tree `a6e4f83f0d4f17fead130c85e7467ac586e6ef8a`。
两个候选均已推送并独立远端读回；原统一资料候选分别是父基线，不覆盖其分支，不更新SDD集成pin/gitlink。

- Composer仅在typed bounty有选中精确附件时放开空正文发送；公议/密议及交互锁仍按原限制。Wire保留schemaVersion1及数量/长度合同，双空、坏引用仍拒绝。空白正文按实际字节留存，不补造用户文字。
- 后端仅由服务器鉴权解析后的typed目录允许空正文；客户端metadata不能放行普通chat。保留 task/owner/target/generation 校验、精确版本、原正文及附件的幂等摘要、澄清关联。
- 原USER保存解析后的精确资料引用，前端显示对应资料卡和版本，历史空正文不丢ID/hash；资料卡不出现在密议或其他事项。历史metadata只作展示，不能作为读取/执行授权。
- 原USER续办仍核对所属request/turn/snapshot和真实正文hash；INSPECT复用原USER、原请求键，不插入人工正文或把Agent指令当用户许可。网络未知恢复不自动换键重发。

### 本轮实际验证

- Web **311 PASS / 0 FAIL**，12组定向测试，包含挂载附件卡、空白发送限制、原键/原正文/精确版本恢复以及既有入口、点将、语音回归。
- 当前Web源码 `npm run build`通过，仍仅是本地研发验证；保留既有chunk warning，不冒充正式发布制品。
- 本次生产源码和小测试scoped ESLint通过。两个改动的大测试文件既有5/7条诊断仍是5/7，新增0；不宣称全仓lint全绿。
- API通过既有锁定orchestrator、普通Gradle依赖/编译图执行5组定向JUnit：**50 PASS / 0 FAIL / 0 ERROR / 0 SKIP，natural exit0**。涵盖Wire、durable admission、原USER续办、context鉴权及精确引用；这是无数据库单测，不是Flow正式云测、真实Provider或业务验收。
- 原始失败保留：API v1新缓存缺settings plugin，改用源码include-build与已有test-only发布占位；v2新增测试错误引用constructor局部sender，按真实编译错误修复。挂载附件卡发现误用函数名，修复后311项通过。未禁用AP、覆盖旧class、伪造skip或重跑付费动作。

原始日志及JUnit XML合并保存并校验压缩/解压SHA-256：[本轮回执](implementation-evidence-20261004/attachment-only-v1/manifest.json)。

## 本轮继续：T05改稿关联子增量（部分完成）

Web `codex/mmd-ui-input-v1-20261004`：`b1f807c717714f0eebc0b98014ad9b8a2084a6cb` / tree `c90a562e6a78c35429a4e86518397cb06f87a02f`。
API `codex/mmd-attachment-only-v1-20261004`：`0ff0322b08ab5c01208e7bb764be72ce3d4849e3` / tree `434913fd4dd7fefe06cd5ed3060c5805b1aeec5c`。
两个候选已推送并独立远端读回；不更新SDD集成pin/gitlink，不覆盖原脏工作区。

- 现有成果目录补可选 `replaces` 精确来源（request/step/output/hash），仅来自服务端持久v3 EDIT_IMAGE输入清单并核对原摘要；新生成时的参考图、工作空间图片编辑不会冒充替换旧会话成果。读取仍经过owner/task/assignment/grant与真实字节校验，Chat另外检查父成果请求的相同会话generation/task/Agent。
- Web目录验证、冻结上述关系，成果卡显示改稿关联并保留历史稿。新增纯函数仅对**已明确的初始清单**应用精确替换，保留其他项，拒绝失效父稿/歧义分叉；重建后冻结所见引用，不从历史或MIME猜测当前集合。
- **生产验收尚未接入该重建函数；初始交付清单来源仍需明确持久引用。** 当前没有隐藏checkbox后自动选择历史成果，也没有声称T05/T06完成。纯文字完成消息的鉴权/快照正式交付分支仍待实现。

### 实际验证

- Web8组相关定向测试 **208 PASS / 0 FAIL**，包含目录/真实挂载gallery/恢复/inline results/finalization/任务刷新及会话组件；`npm run build`自然exit0。仍为本地研发验证，既有chunk和mock环境警告保留。
- 目录源码与小测试scoped ESLint通过；gallery既有诊断baseline13/current13，rule/message元组一致，新增0。不宣称全仓lint通过。
- API通过既有orchestrator/Gradle锁、普通依赖与AP编译图执行3组定向JUnit：**55 PASS / 0 FAIL / 0 ERROR / 0 SKIP**，Agent与Chat任务均natural exit0。包括真实服务方法的owner/root/source digest路径与原有回归；无数据库/真实Provider，不是Flow或业务验收。
- 原始Web失败保留：v1测试用URL.pathname造成Windows重复盘符，改为fileURLToPath；v2两项静态测试依赖旧self-closing slot和空行，用真实标签定位纠正后208通过。没有改生产逻辑规避断言。

原始日志、JUnit XML、来源Git blob/测试工作文件hash及压缩hash见[本轮合并回执](implementation-evidence-20261004/output-lineage-v1/manifest.json)。Windows CRLF工作文件与LF blob只允许换行归一化差异，分别记录原始SHA-256。

## T05/T06：事项详情媒体验收接线子增量（2026-10-04，部分完成）

Web `f0f4d1fced43effbb37a216351e7e145813ff7d0` / tree `84d5b90a894cebab4243ba5656208ecfdda439f9`，仍在 `codex/mmd-ui-input-v1-20261004`，已推送并独立远端读回。API源码未改，沿用上轮 `0ff0322b08ab5c01208e7bb764be72ce3d4849e3` 的有效来源合同/55项测试证据，不宣称本轮重跑API。

- 验收操作移到事项详情，议事卡保留历史稿、预览/下载/可选保存，不再有checkbox。事项页只读本次成果，复用原finalization；点击确认时提交当时实际显示的精确来源，保存不是前置。
- **当前支持边界**：现有持久输出中仅有一个独立committed manifest批次时，将该明确批次及精确改稿关联接入生产页面；按request/step/output/hash替换一项，保留其他图/音频/文件。多轮改稿依父链重建，不依网络到达顺序。多个独立原始批次、分叉改稿或失效父稿一律提示回议事澄清，**尚未实现澄清后追加/重置交付意图的持久读取**；不是通用当前清单完成，不自动并集所有历史或挑同MIME最新版。
- 已开始/完成的验收继续显示冻结原引用，晚到新稿、刷新或remount不替换原内容；未知响应仍查/恢复原operation与key/body，不重跑工具。
- 事项页只读原owner/task作用域下的现有conversation/list和requests。冷读来源不唯一不猜最新；明确原会话在既有分页中查找，身份/任务/会话切换立即清理并隔离晚到响应。非法目录/权限或读取失败不能降级到旧验收路径。没有原生请求记录的既有正式事项仍由原FormalTaskDeliveryPanel领域服务处理；资金榜和明确delivery review路由保持原样，私人事项路由未改变。
- “继续修改”只返回原会话；正在同一会话时不重置对象/草稿，跨分页只选择原history条目，身份切换或正在处理其他会话时停止切换。不点将、不创建/发送、不插入新草稿、原成果不改写。

精确提交上10组相关测试 **235 PASS / 0 FAIL**；本地build自然exit0，仍保留既有chunk及mock环境警告，非Flow/真实Agent/发布验收。小组件/新增hook/catalog与相关测试scoped lint通过；与上一提交比gallery13→12、BountyPanel11→11、JuyiHall187→187、大组件测试7→7，rule/message无新增诊断。最终Git blob与测试工作文件只允许CRLF/LF差异，回执见[合并记录](implementation-evidence-20261004/task-acceptance-v1/manifest.json)。

## 下一实际缺口

第一增量T01–T04的最小源码差异已接齐，**尚未整体联调/发布/用户验收**。第二增量T05/T06已接通上述单批次媒体清单、只读事项验收及返回原会话，但仍需补多独立批次的明确交付意图与纯文字来源分支；不能将该子增量标成T05/T06整体完成。仍复用现有finalization，不自动勾选全部历史成果，不新建交付集合服务。

随后在实际闭环中核对T07/T08，并按T09使用既有正式Flow测试/同Run制品发布及上线验收。Client本轮未改源码，真实空正文到Agent的配对闭环尚待联调；不将静态检查或mocks算成产品通过。未新增付费Provider调用、生产数据/迁移、Flow Run、release ref或部署。

## T05：纯文字可信来源与现有正式交付内部适配（2026-10-04，部分完成）

API `codex/mmd-attachment-only-v1-20261004`：`a847c3d42421ecf61c9828b23744b951cd997fb7` / tree `0b7e10d17d5e898ec091bb50fe8b8d7a654964c3`，已推送并独立远端读回。Web未改，沿用 `f0f4d1fc` 的235项既有证据，不冒称本轮重跑。

- 只读来源直接校验已有v3 CHAT完成消息、typed admission、任务/owner/client/会话generation、实际快照及重建的finalDigest；读取原ASSISTANT字节，中文多行/末尾空白不改写。未完成、CLARIFY/ACTION_REQUEST、消息/快照/正文/摘要/任务或assignment不一致均拒绝。不会扫描/自动选择回答，寒暄不自动成为交付。
- 实际自然议事没有interaction-step行，故文字来源使用真实request/turn/message/snapshot，**不伪造stepId、executionId、runId或outputId**。媒体保留原step/output链；文字不要求先保存空间或生成文件。
- Agent可信内部来源union支持文字和混合来源；复用现有真实lease/artifact/正式提交/owner验收。当前grant/assignment仍由原promotion机制校验，不把文字读取结果当执行授权；原媒体摘要已有独立固定值回归，不更换在途原键/原正文。
- **本轮尚未改公开HTTP媒体-only合同、existing-items持久字段或接上事项页文字验收**。当前仅可信来源及Agent内部适配完成，不能声称用户已能纯文字直接验收，T05/T06整体仍是部分完成。

精确API提交上既有锁定orchestrator、普通依赖/AP编译图的9组定向JUnit：**112 PASS / 0 FAIL / 0 ERROR / 0 SKIP**，Agent/Chat任务均natural exit0。真实final reader与snapshot/finalDigest破坏测试、UTF8原文、混合来源、虚构执行/步骤拒绝及原媒体权限/恢复/严格wire/schema回归均通过；无数据库、真实Agent、Provider或Flow业务验收。保留首轮57项中的2个fixture失败及原日志/XML，按实际发布bytes修fixture；未修改生产逻辑绕过断言。原始日志、JUnit、失败记录、精确Git/远端测试源hash见[合并回执](implementation-evidence-20261004/completed-message-v1/manifest.json)。

下一步仍是将明确文字来源接入**现有**HTTP selectedOutputs及原items持久记录/恢复，再接事项页只读展示；同时补多独立批次追加/重置的明确交付意图，不新增delivery-set服务/表/状态机。未做生产迁移、Flow、发布或付费调用；本轮无新增需用户决定的范围事项。

## T05：文字验收HTTP、原条目持久化及恢复接线（2026-10-04，部分完成）

API `codex/mmd-attachment-only-v1-20261004`：`88243a317bd32f0495f8c9d9041e3e3582f764d4` / tree `3a9087b100b2737c255131a79519ace2376f97a1`，已推送并独立远端读回。生产实现位于父提交 `ba984d2b`；最终子提交只补两份组合测试。Web仍未改，不重跑未变更235项/本地构建。

- 原 `/agent/tasks/{taskId}/finalizations` POST接受原6字段媒体项或文字5字段项（requestId/sha256/title/purpose/messageSource）；文字messageSource严格含turnId/messageId/snapshotId/finalDigest。messageId保持十进制字符串，支持JavaLong最大值、不经JS数字截断；不存在伪造step/output/run或浏览器提供grant权限。支持有序混合来源，混杂字段、未知字段、重复来源、非规范/越界ID均拒绝。
- 原 `chat_selected_output_finalization_item` 补来源kind及真实消息/快照字段，文字step/output为NULL。继续原operation/key与GET按key/operation恢复，只读GET不推进；receipt校验条目重建的原requestDigest，持久引用被改写时拒绝而非偷换内容。已完成/已提交操作先恢复实际Agent记录，不重读过期来源或再跑工具。
- 文字的当前grant仅由服务器在既有owner task-root锁内解析，沿用原active grant、资料/requirement和assignment校验，Agent.prepare仍再次校验；不获得工具/付费授权。继续原lease/artifact/正式提交/owner验收，不新建交付服务、表或状态机。
- 新建表DDL及原条目表的一次升级SQL已写入源码，schema initializer核对来源列/唯一索引/check/nullable。**既有表升级不在启动时自动执行**；正式发布时须按原授权流程与API配套迁移。本轮未对生产执行DDL或数据写入。

实际验证：10组定向JUnit合计 **124 PASS / 0 FAIL / 0 ERROR / 0 SKIP**，由父提交Agent59 + 最终提交Chat65组成，三次Gradle任务natural exit0。Agent生产/测试及SQL字节在最终test-only子提交未变更，故不冒称新树上重跑Agent。新增组合用例使用真实HTTP parser、Chat store、完成来源及原final reader，确认中文多行原文/实际快照、正式进度与原键只读/重放不重复读源；JDBC、身份与Agent/grant边界仍为fixtures，不冒充部署JWT/Spring/真实Agent验收。

另在**独占新建datadir、关闭网络、独有socket**的MySQL **8.0.21**执行24项SQL检查：fresh与旧schema升级、旧operation/key/digest/媒体条目不变、文本/媒体共存、NULL/零/前导零/溢出ID/错误digest/虚构step/output/未知kind/重复消息拒绝；24项通过。两个自有测试数据库已删除，自有mysqld正常退出，不复用或操作生产及其他任务实例。原始DDL/catalog、日志/JUnit和复用字节hash见[本轮合并回执](implementation-evidence-20261004/text-wire-v1/manifest.json)。

**仍缺**：事项页纯文字的只读展示/验收接线，以及多独立批次明确追加/重置交付意图。不能据本批后端通过把任意ANSWER、最新消息或寒暄自动变成交付，T05/T06整体尚未完成。未调用Provider、Flow、生产迁移、release ref或部署；本轮暂无需用户决定的范围事项。


## T05/T06：前端文字验收请求与原键恢复合同（2026-10-04，部分完成）

Web `codex/mmd-ui-input-v1-20261004`：`846460606c415246bba557a07b8b0c76bfe12136` / tree `8215652635722514e6cdd24641593aa80bb2ac9f`，已推送并独立远端读回。API未改，沿用 `88243a31` 的后端合同与既有124项源码/24项隔离SQL证据，不声称本批重跑。

- 原finalization composable识别严格5字段文字项及4字段messageSource，媒体继续原6字段；支持有序图文混合，不增加接口、集合服务或状态机。messageId始终为正规范十进制字符串，可保留JavaLong最大值；数字/前导零/溢出及虚构step/output/execution/run/grant均在请求前拒绝。
- 请求、持久恢复及receipt按原消息turn/message/snapshot/finalDigest逐字段核对；相同实际消息不能靠改snapshot/digest/title重复验收。来源类型或顺序变化不能偷换原成果。
- 新增嵌套messageSource深复制/冻结：调用方后续修改原对象不改变在途正文；未知响应、remount、只读状态查询及显式续办保持原key/body，不换键、不自动写入或执行工具。账号切换隔离晚到文字receipt及恢复记录。旧媒体恢复仍有效。
- **仅前端请求/恢复合同接齐**；事项页尚未读取/渲染明确的纯文字交付来源，多独立批次追加/重置意图仍缺。没有把任意ANSWER、问候或最新回复自动列入待验收成果，不能标T05/T06整体完成。

本批4组相关Web测试 **68 PASS / 0 FAIL**，含32项finalization合同/恢复测试（新增9项）、既有挂载gallery、事项页和任务刷新回归。改动composable及测试定向ESLint exit0；本地Vite build自然exit0，保留既有chunk warning。真实请求/Agent/正式Flow/发布闭环未测。测试与源码字节、构建及lint原日志hash见[本批回执](implementation-evidence-20261004/text-wire-web-v1/manifest.json)。未覆盖原脏工作区、修改集成pin/gitlink、调用Provider或执行生产迁移/部署；暂无需用户决定的新范围事项。


## T05/T06：明确文字交付标记与事项页读取/验收（2026-10-04，部分完成）

API `732f7b7f35765c47c7d12fdded4ae257905a26b1` / tree `2d609a8d2f176c55a988ce4358ef0c2deb841197`；Client新独立候选 `codex/mmd-text-deliverable-client-v1-20261004`：`f7d6d3956f8fcdc7c373ce968f1b7389753bfb58` / tree `d177772b45825f874c3f606df3d275adeeb92686`；Web `31154e0393d5509288ae92b7d5762c00458f7de8` / tree `c85a2da355303125e7c1f83c9eb7fef404a8b4fd`。均已推送并独立远端读回；Web末提交只清理新增尾空白，最终验证覆盖该工作字节。

- 既有v3 interactionOutcome补可选Boolean `deliverable`，只有CHAT ANSWER允许true。缺字段历史摘要前像不变，不从ANSWER猜交付；标记进入原持久JSON/finalDigest，读取拒绝篡改，无新表/接口/服务。Client新生成合同显式给Boolean：问候、进度、澄清、文件生成说明为false，文字本身为请求完成成果才true，不当授权或验收。
- 原typed-outcome对true返回真实turn/message/snapshot/finalDigest。事项页核对原request/task/generation/完成CHAT turn，按原UTF8文字计算hash、冻结来源并转义展示；下载仅原文Blob，不伪造step/output/run、不先保存空间。验收继续原五字段文字来源和原key/body恢复，刷新/remount不偷换新稿；文字卡不显示假asset保存按钮，原选区归档保持独立。
- **支持边界仍为一个明确文字项且无媒体，或原单一媒体manifest及改稿链**。多文字/图文独立批次拒绝歧义，不按最新消息或历史并集。混合来源wire已支持，明确追加/重置/文字替换关系仍待补，T05/T06整体未完成。

实际验证：API9组 **87 PASS /0 FAIL /0 ERROR /0 SKIP**，普通Gradle/AP图经既有orchestrator共享锁、natural exit0；未重跑不变Agent。Client3组 **34 PASS /0 FAIL /0 SKIP**，最终LF源码Node natural exit0。Web9组 **123 PASS /0 FAIL**，scoped lint与本地Vite build exit0，gallery12→12无新增诊断。Client缺依赖软链接、测试边界与CRLF上传失败日志保留，仅修自有文件/软链接，未安装或重启生产运行时。

Fixture由实际API服务/read导出，hash与Web原件一致；身份/JDBC/engine仍mock，非部署Agent或发布验收。原日志/JUnit/失败回执/精确blob与fixture hash见[合并回执](implementation-evidence-20261004/text-deliverable-v1/manifest.json)。既有items升级SQL仍需授权正式发布配套执行，本轮未做生产DDL/Provider/Flow/部署/集成pin变更。用户要求无确认事项直接继续，不逐次等待。


## T05/T06续推：服务端文字标记收口与跨轮文字关联（20261004工作包，部分完成）

API候选 `6b794b0a2663a18d306ee8515d89e7fe59a09c60` / tree `ab733d02fbb49998e9ca2256340f777256d4c584`；Client候选 `213f461f404af275c8b33ca524921f0ffeabc45d` / tree `6d7a8917073d12967ca8d3f32f40a85ee6169c99`；Web候选 `0a4abbbe67fc29914d84c9aa79c0736aaa9999ec` / tree `2381bd90180cdeb49542240cb37ceaf1b0617f24`。沿用上述三个自有分支，均已推送并独立远端读回，原脏工作区及集成pin不变。

- 先补齐服务端可信文字source的标记校验：即使提交精确消息引用，未标记或明确false的ANSWER仍不可进入新正式交付；不扫描回复、不把普通文字自动变成果。独立提交 `72797d13` 的9组88项回归通过，原回执见[文字标记收口](implementation-evidence-20261004/text-marker-promotion-v1/manifest.json)，最终增量的109项也覆盖此行为。
- 复用现有DISCUSSION parentOutcomeId及真实完成消息读回，在原snapshot admissionFacts补只读 `deliveryParent`（实际outcomeId/finalDigest）。只有read-verified的已完成、同任务/指派版本、明确marked CHAT文字才广告为父来源；父链接本身不表示替换、许可或验收。
- 原interactionOutcome JSON补可选 `deliveryRelation`，严格APPEND/REPLACE/RESET + 精确父outcomeId/finalDigest，只用于明确文字ANSWER。来源必须匹配原admission和server snapshot中的父事实，且父仍在相同scope/task/assignment，不能凭模型或浏览器捏造；关系进入原finalDigest，读取重建。旧缺字段/新null不会改变原缺字段摘要前像。无新表、接口、集合服务或状态机。
- Client native CHAT有nullable关系schema及明确选择指令；仅复制server广告的父ID/摘要，无父或篡改父即拒绝发布final，不执行工具。原INSPECT不能成为任务交付。Web从持久关系重建一条文字因果链：APPEND保留原项，REPLACE只换其精确父文字并保留其他项，RESET弃原清单。顺序来自关系而非到达时间，不取最新回复；缺父、坏摘要、重复、分叉和断开的环拒绝猜测。
- 普通文字续聊只在已读清、唯一明确文字链时带原父CAS，新的问候不抢父位置；多独立根、未完成/未读请求或媒体目录不推断父。未知响应保留原父/key/body。事项页实际挂载测试覆盖3种关系的展示、所见原refs/hash提交和remount冻结恢复，不先保存/生成文件、不重跑工具。

最终实际验证：API11组 **109 PASS /0 FAIL /0 ERROR /0 SKIP**，普通Gradle/AP图经原orchestrator共享锁，natural exit0（含既有Spring事务fixtures）；Client3组 **37 PASS /0 FAIL /0 SKIP**，最终LF源码Node自然退出；Web9组 **130 PASS /0 FAIL**，scoped lint及本地Vite build自然exit0，gallery12→12/测试0→0无新增诊断。API真实服务/read导出的APPEND/REPLACE/RESET projection原字节在Client/Web共享，fixture hash一致；DB/身份/native engine仍mock，不冒充真实Agent或上线验收。

失败回执保留：API新增测试缺import、Mockito thenReturn参数中嵌套真实reader导致unfinished stubbing，按真实日志只修fixtures、完成原root-cause matrix后重跑，不删断言/skip/AP；Web新增parser校验误插入旧v1分支导致7项失败，移回v3局部分支后全部回归通过，格式lint修正日志也保留。合并原始日志/JUnit/精确blob与fixture证据见[关联增量回执](implementation-evidence-20261004/text-relations-v1/manifest.json)。

**仍是部分完成**：目前支持单一明确媒体manifest/精确改稿链，或单一根的明确跨轮文字链；图文混合/多独立manifest追加重置、修改较早非广告父文字、经澄清回覆传播文字父来源，以及自然修改媒体时原源可用性仍待接齐。不能把这一增量称作通用T05/T06完成。随后还须实际Agent/保存/刷新闭环及原正式Flow/同Run发布（配套既有items升级SQL）；未执行生产DDL、Provider、部署、release ref或集成pin变更。普通开发步骤继续，无新增需用户确认的范围事项。


## T05/T06续推：文字成果经多轮澄清传播及原CAS恢复（20261004工作包，部分完成）

API候选 `d0a3f80a45c707bb12de12cf2b0cd3558417b2c0` / tree `c2a7d724313bae6162e31b85b2eaa443bb211691`；Client候选 `79bad1e3e01640b5c126d206cf2fab2cae4065c6` / tree `bd51728debc825a63452680da30c7dd10b4130ec`；Web候选 `1fb1fa4c6b6fc7de66408efdab4c05bdc2794531` / tree `5bea0c95a5410f95434f35977c35ad7756fbaafb`。沿用原三个自有候选分支，均已推送并独立远端读回；原脏工作区、生成声明及集成pin未纳入提交。

- `CLARIFICATION_REPLY` 的即时父仍为原OPEN问题及其CAS，不把问题冒充文字成果。服务端另沿真实原admission/snapshot追溯文字 `deliveryParent`，可连续跨多轮澄清，始终广告原成果outcomeId/finalDigest；每轮问题通过实际v3 final reader重校验，并核对scope、任务、assignment、完成CHAT状态及上一轮ANSWERED CAS所指实际回复。
- final在prepare和只读恢复中分别校验即时问题父/回复CAS与原文字父。坏摘要、错快照/账号/任务/assignment、错问题/回复/版本、缺来源及循环均拒绝。最初未绑定文字父的澄清不回溯推断最新ANSWER；旧合同和未绑定来源仍无文字关系。APPEND/REPLACE/RESET继续要求最终明确选择，澄清链接不自动成为替换意图。
- Client/Web本批仅增源码回归与共享实际API projection，不新增runtime合同或入口。验证native CHAT保留原文字父、拒绝以即时问题/问题摘要替换；事项页忽略问题卡，展示并验收真实原文/新稿；未知答复受理及未知验收在remount后保持原CAS/key/body和原refs/hash，不换稿、不重跑工具。
- 复用原outcome/admission/snapshot/pending/finalization；无新表、服务、API、状态机或审核门禁。支持范围是既有单根明确文字链经澄清继续，**并非**图文混合或多个独立manifest通用交付。

实际验证：API12组 **116 PASS /0 FAIL /0 ERROR /0 SKIP**，普通Gradle/AP图经既有orchestrator共享锁，natural exit0；Client4个相关文件 **44 PASS /0 FAIL /0 SKIP**（其中既有3文件加新用例38，另6项旧文字合同回归），Node自然退出；Web9组 **133 PASS /0 FAIL**，scoped lint与本地Vite build自然exit0，gallery12→12/测试0→0无新增诊断。API真实final writer/read导出两轮澄清后的三种关系，共享fixture SHA256 `a8f5515332f6781399323edf4b11b54cf8e11bd9e80dc4004c27711e648f49d6`，Web/Client保持同字节。DB/身份/CAS持久记录与native engine仍fixtures，不冒充真实Agent、浏览器线上或Flow业务验收。

保留API首次116项中的4个fixture失败及XML：Mockito Map默认空集合与新turn stub覆盖原来源turn；显式建模nullable无来源合同、分离原来源turn后，test-only子提交全量定向重跑通过，未放宽生产断言。Web首次133通过后的两个多余空行lint失败保留，仅修格式并重跑。精确提交/tree/source字节、原始日志/JUnit/共享fixture见[本批合并回执](implementation-evidence-20261004/clarified-text-v1/manifest.json)。

**仍待继续**：图文混合、多独立manifest明确追加/重置、修改较早非广告父文字、自然改媒体的原源可用性；随后实际Agent/材料/保存/刷新及既有正式Flow/同Run发布，并按正式发布授权配套已有items升级SQL。T05/T06仍部分完成，T07–T09未完成。本批未调用Provider、执行生产DDL/数据写入、部署或更改release ref/集成pin，无新增需用户确认的范围事项。


## T05续推：自然媒体改稿接入精确原源（2026-10-05验证，20261004工作包，部分完成）

API候选 `01039abb3763d0c0e873bdd93de710260eb37328` / tree `16c64cccaec44120a2436a9f2fb20002bcc9fb4e`；Client候选 `e41246c3fb743adea4d25b0f8fe499505bb12a18` / tree `bda39b4953a72dbebc406dd888f7c0422cdad3ed`；Web候选 `5b13014821cc498c481bc98c1793d1b28c2e2ffc` / tree `0ee5f15d46ff507c3201418be707c5678fb20647`。沿用原三个自有候选分支，均推送并独立远端读回；原脏工作区、Web生成声明及集成pin未纳入提交。

- 普通非空CHAT、未显式选资料且未选澄清问题时，议事适配器读取现有已完成EXECUTE产物清单，复用单一明确manifest与精确replaces链解析，只把当前保留产物的持久assetId/revision加入原sourceSelectors。它们是可用上下文，不是验收交付选择、改稿意图或执行授权；无需先保存到个人空间，也不添加专用参考图选择入口。
- 不按最新文件/MIME/到达顺序猜来源，不合并独立历史批次。晚到未投影assetRef、坏/空/重复manifest、读失败、独立根、分叉/缺父、待完成typed read、文字标记成果与媒体混合均不自动广告来源。当前上下文必须匹配任务、target、assignment、conversation generation及已提交producer；来源不明确时仍交给原议事处理，不捏造媒体绑定。
- API原context查询增加真实产物EXECUTE step与会话的精确task/target/owner/client/generation及OUTPUT_COMMITTED关联，保留原sha256/bytes/requestId/stepId与sourceRef推导；不写入、不投影、不保存、不执行工具。已有动作执行/asset resolver继续重检真实权限和字节，Client生产逻辑不变，仅补既有native CHAT action sidecar回归。
- 显式输入、INSPECT、已选澄清CAS不被重新绑定；空正文仍必须有显式合法附件。查询中busy防重复发送，身份/上下文/catalog漂移后不POST。未知受理跨remount/恢复仍冻结原asset refs、原body与原key，不改成新清单，也不重跑工具。

实际验证：API6组 **45 PASS /0 FAIL /0 ERROR /0 SKIP**，普通Gradle/AP图经既有orchestrator共享锁，natural exit0；Client4个相关文件 **45 PASS /0 FAIL /0 SKIP**；Web9组 **142 PASS /0 FAIL**，scoped lint（含本次生产composable）及Vite build均exit0。API真实context代码导出共享fixture SHA256 `ffd8c0c4229ef3352deab03c55f66253b39579c7b0b83db6d7da80f32bc33f9b`，Client/Web保持同字节。但SQL行、session/capability与native engine/浏览器调用仍fixtures，**不是实际数据库持久数据、真实Agent改图、保存或线上业务验收**。

保留失败回执：API定向首次通过；Web首次140项通过后的一个多余空行lint失败仅格式修复，扩展实际context fixture与pending/mixed回归后最终142/lint/build通过。Client两次45项运行各一个新测试fixture错误，分别是adapter input JSON字符串误当native input数组、未知source错误码猜测；保留根因矩阵和原始日志，按现有接口/精确ACTION_SELECTION_INVALID合同修正测试后45通过，未放宽生产检查。精确提交/tree/源码字节、JUnit与原始日志见[本批合并回执](implementation-evidence-20261004/media-context-v1/manifest.json)。

**仍待继续**：图文混合、多独立manifest明确交付追加/重置、修改较早非广告父文字；随后实际Agent/资料/保存/刷新及既有正式Flow/同Run发布，并按正式发布授权配套已有items升级SQL。自然媒体原源的上述单明确链源码缺口已补，不代表所有歧义场景或真实联调完成。T05/T06仍部分完成，T07–T09未完成。本批未调用Provider、执行生产DDL/数据写入、部署或更改release ref/集成pin，无新增需用户确认的范围事项。


## T05/T06续推：修改较早文字，保留后来追加内容（2026-10-05验证，20261004工作包，部分完成）

API候选 `905adcf6b988a33de57e46e753528d16dd8c0136` / tree `6a9b07c83d60a0344dc61af8b0726fef3241fb4a`；Client候选 `b5fa7359ac372a6f36425b2b8213671a20d11b3d` / tree `486452edee23f72ec6b86322303e372561518ad9`；Web候选 `f60cfbfd294c121e3fe499ae1a900c9262df57c4` / tree `ddcfee858bf4ff95982f1daa58b5c95e22c3a48b`。沿用原三个自有候选分支，均已推送并独立远端读回；原脏工作区、Web生成声明及集成pin未纳入提交。

- 补齐具体场景：第一段成果→追加第二段→澄清要改哪段→只替换第一段，第二段仍保留；随后继续追加时因果父仍为最后一次真实交付结果，而不是显示顺序最后一张卡片。原文字引用/快照/hash可直接验收，不需先存个人空间或伪造execution。
- 原admission/snapshot增加 `deliveryTargets`，只广告沿既有明确文字关系重建后仍保留的精确outcomeId/finalDigest及原text。逐个验证实际完成CHAT、scope/task/assignment、消息/快照与真实final摘要；不按最新ANSWER猜父、不读取/合并无关批次。正文是供辨别目标的非可信DATA，不作为指令。
- 既有 `deliveryRelation` 的 `REPLACE` 可选携带成对 `targetOutcomeId/targetFinalDigest`，明确改哪一个仍保留的项；原 `parentOutcomeId/parentFinalDigest` 始终表示当前因果basis，原澄清pending CAS另行保持。缺字段、坏摘要/越界目标、已RESET或REPLACE丢弃的目标、非REPLACE携带target、错/缺广告及原快照/消息/scope变化均拒绝；无目标扩展的旧三字段关系和final摘要前像不变。
- 服务端在原final prepare与只读恢复中检查冻结广告和实际保留来源，迭代重放原关系，不新增表、API、服务、集合ID、版本框架或状态机。Client native CHAT schema/sidecar传同一精确关系并拒绝把即时问题或任意历史文字当目标，不执行工具。前端仅扩展原reader/清单纯投影；事项页验收只提交显示的改稿和未修改第二段，原request/messageSource/sha256保持一致，未知验收remount不重新POST或换稿，后续议事仍冻结正确父/原键/body。

实际验证：API12组 **120 PASS /0 FAIL /0 ERROR /0 SKIP**，普通Gradle/AP图经既有orchestrator共享锁，natural exit0；Client4个相关文件 **47 PASS /0 FAIL /0 SKIP**，首次定向通过；Web9组 **148 PASS /0 FAIL**，scoped lint及Vite build均exit0，gallery历史诊断12→12/测试0→0无新增。共享实际API writer/read fixture SHA256 `2076463b50bcba70da910ab28381ace38642f83b19e573a47a9b548d016f4da4`，Client/Web保持首次导出的同字节；最终生产代码与首次导出相同，最终projection语义/原来源/文字字节/摘要一致，但JVM Map遍历导致JSON键顺序与首次不同，保留两份raw及独立摘要，不虚报最终envelope逐字节相同。DB/身份/CAS与native engine/浏览器调用仍fixtures，**不是实际Agent、线上验收或正式Flow证明**。

保留失败回执：首次119通过；补齐admission/旧record round-trip回归后，v2新测试漏声明已有fixture的checked Exception，v3新扩展fixture漏stub精确outcome查找（120项1失败），均按原orchestrator归因、保留原日志/JUnit及根因矩阵，限于新fixture修复后v4全部120通过，未放宽生产断言。Web首次147通过后的一个多余空行lint失败仅格式修复，最终补议事因果父/原键回归后148/lint/build通过。精确源码/tree/日志/JUnit见[本批合并回执](implementation-evidence-20261004/retained-text-v1/manifest.json)。

**仍待继续**：图文混合与多独立manifest明确交付追加/重置；随后实际Agent/资料/保存/刷新及既有正式Flow/同Run发布，并按正式发布授权配套已有items升级SQL。较早但仍保留的明确文字目标源码缺口已补，不代表可以恢复已丢弃历史稿或拼接不明确批次。T05/T06仍部分完成，T07–T09未完成。本批未调用Provider、执行生产DDL/数据写入、部署或更改release ref/集成pin，无新增需用户确认范围。


## T05/T06续推：文字→明确新执行批次，追加或重置（2026-10-05验证，20261004工作包，部分完成）

API `ccdf2ce8423f9e435a3bef0915788aed71ccea01` / tree `1f1130fd4ec44a2f3b54960af855385649501562`；Client `b6ca429f9ba74a09e54c32003ab295f7c4bb6764` / tree `2c7821afddd510dfd5f18b8059fe9c0650a4a043`；Web `fd5f7e87f7ef4ad17a4688b0d6b07b05ab79afe4` / tree `4f3fbe8ae7a1410f622f088bc9eb869c9257dc1c`。沿用原自有三个候选分支，均已推送并独立远端读回；原脏工作区、生成声明、集成pin与release ref未纳入。

- **本次真正接通的子场景**：已明确文字成果→用户自然要求另加一批媒体→原Agent规划final明确APPEND→实际输出就绪后显示“原文字＋新manifest”；明确RESET则仅显示该新manifest。ACTION_REQUEST正文始终不是交付文字，不能在规划成功时提前当媒体完成。
- 复用原 `deliveryRelation` 三字段、冻结 `deliveryParent`、admission/snapshot、动作outbox及child-admission/progress。仅已广告的EXECUTE可关联未来批次的APPEND/RESET，不扩大工具或权限；CLARIFY、INSPECT_INPUTS、非广告动作、动作REPLACE/target及错父/摘要拒绝。文字关系旧摘要与真实资料读取行为保持，不新增接口、表、服务、集合ID/版本或状态机。
- 事项页从现有typed-outcome读取明确动作关系，只把其真实COMPLETED EXECUTE child与同任务/指派/target/会话generation、OUTPUT_COMMITTED step关联，再读取原鉴权outputs。未完成/失败/取消、晚到child、缺manifest、错来源、独立/分支/不完整批次不推断可验收集合；不能把ACTION_REQUEST prose、按类型最新结果或历史合并当交付。
- APPEND保留原文字和该新完整manifest；RESET只保留该新批次。事项页仍用原selectedOutputs/finalization，按真实显示的messageSource或request/step/output/hash提交；未知ACK、remount与晚到无关批次不换原稿/key/body，显式继续先查原键，再仅重发原POST；不要求保存或重新调用工具。旧单manifest/媒体精确改稿路径不变。

实际验证：API13组 **131 PASS /0 FAIL /0 ERROR /0 SKIP**，正常Gradle/AP依赖图经既有orchestrator共享锁，首次natural exit0；Client4文件 **49 PASS /0 FAIL /0 SKIP**（首次48通过，再补原API fixture/native副本49通过）；Web10组 **156 PASS /0 FAIL**，scoped lint及Vite build exit0，gallery基线12/当前12、测试0/0无新增诊断。共享实际final writer/read/progress导出SHA256 `8f1fadefb5418ab2d16cf61b9d1fcf9a55bdd32484b996dad3a17a6934784bf1`，Client/Web同字节。**outbox/admission/child记录、native engine及事项页HTTP/PNG仍fixtures，不是实际Agent生成、线上浏览器或Flow验收**。合并源码/日志/JUnit回执见[execution-batch-v1](implementation-evidence-20261004/execution-batch-v1/manifest.json)。

保留Web失败：v1误将新v3 guard插入legacy v1 reader，140通过/8失败，移除该误插入而非删原断言；v2新未知ACK测试误把状态GET计入POST，154通过/2失败，只修新fixture以分开请求并模拟原键404显式重发。最终156及lint/build通过；未放宽生产来源/权限校验。API与Client未发生本批测试失败。

**明确未完成**：这是“文字为父→新媒体批次”的子增量，不代表所有图文/多独立媒体场景完成。后续需让已完成媒体/动作成为原因果basis并广告精确保留目标，接通混合清单单项改稿；还需处理原legacy EXECUTE独立媒体起点及多独立manifest明确APPEND/RESET。当前这些未接线情况仍拒绝猜父/历史合并，不提前标记T05/T06完成。之后继续实际Agent/材料/可选保存/刷新/隔离及既有正式Flow同Run发布，按正式发布授权配套原items迁移。T07–T09未完成；本批未调用Provider、生产DDL/数据、部署或修改release/integration pin，未增加需要用户确认的范围。


## T05/T06续推：已完成媒体成为因果父，混合保留目标及较早文字改稿（2026-10-05验证，部分完成）

API `0e70e2f0d859cf1eb77817b2bf6ce257ef4d9a3d` / tree `947fa2c258d78055f80d04c2bc1426ecabe77cde`；Client `b42176c51b7213ce0a7b16e5b83228960210d106` / tree `70b01245422dffac195022f8e2f88976143e850d`；Web `c0753037f56e5d6b4690a2bb7b4a6eb2879c569d` / tree `ca14b756816775e0357f35eb67dbf0afa56c68a8`。原自有候选分支均已推送并独立读回，未纳入原脏工作区/生成声明，也未修改集成pin/release ref。

- 已完成EXECUTE的原ACTION_REQUEST final现在可作为后续议事因果basis；它的规划正文仍不是交付。沿用原admission/snapshot/CAS、outbox/child progress、原Step/ExecutionLink和owner鉴权execution/outputs读取，重建精确混合保留目标。文字仍为outcomeId/finalDigest/text；媒体为对应原outcomeId/finalDigest/outputSource(requestId/stepId/outputId/sha256)，一批多文件共享原outcomeId，不伪造新成果ID、不增加集合服务/接口/表/状态机。
- 已接通“原文字→两批明确APPEND媒体→修改较早文字”：只替换仍保留的文字，四个媒体原来源完全保留；随后文字APPEND、媒体APPEND/RESET仍依明确关系重放。文字不能替换媒体组、未完成动作不能广告交付basis、变更/缺失/foreign执行拒绝冻结来源。普通讨论pending动作仍可受理但不广告媒体basis，原键重放先于重绑定。
- 自然CHAT按原清单发送精确保留媒体asset selectors及终端因果父，不按显示顺序/最新MIME选父；显式选附件及仅附件发送保留用户所选selectors，同时绑定同一已验证媒体basis，不偷换资料。晚到asset可暂不自动选媒体但保留已验证因果父，保存不是前置。
- 事项页实际mounted fixture覆盖较早文字改稿后显示“新文字＋四个媒体原源”，selectedOutputs与所见一致；未知ACK、remount与无关晚到outputs保持原key/body/hash，不重生成。原typed ACTION_REQUEST无关系时可作为单一明确媒体root（仅合成单元fixture）；这不代表legacy EXECUTE起点已接齐。

验证：API14组 **137 PASS /0 FAIL /0 ERROR /0 SKIP**；Client4文件 **51 PASS /0 FAIL /0 SKIP**；Web10组 **164 PASS /0 FAIL**，scoped lint（包含useHallTypedDeliberation）及build exit0，gallery基线12/当前12、测试0/0无新增诊断。实际writer/read导出共享fixture SHA256 `6b4846a3caf82a45724b7a048dba6ec5f21beb0d0e7ab24b18ec685d19bce42e`，Client/Web同字节；API v2重新导出因Map序列化顺序不同hash为 `3c91404fa0f9b1c59124336918a513bfd38f555f0f578b0d39d3fdc9c569174f`，已独立核对JSON语义完全相同。**durable记录与execution reader、native引擎及媒体HTTP仍fixture，不是实际Agent/媒体生成、线上浏览器、正式Flow或用户验收**。回执见[media-basis-v1](implementation-evidence-20261004/media-basis-v1/manifest.json)。

失败与修复：API首轮137项中135通过/2个新admission fixture未完成Mockito stubbing（thenReturn里调用真实read触碰mock）；保留失败XML并归因一次，只将真实read预计算，v2全通过。新Web synthetic root fixture把应缺省字段写成null被严格parser拒绝，仅改fixture缺省；新mounted测试缩进75条及duplicate blank lint均只修新测试排版，未删断言/放宽生产校验。最终164及lint/build通过。

**剩余**：混合清单里的单项媒体改稿仍需复用原replaces精确关联，目前拒绝猜测；legacy EXECUTE原始媒体起点与更多独立root明确意图仍需补齐。T05/T06不标完成；T07–T09实际Agent/材料/可选保存/刷新/隔离及既有正式Flow同Run发布未完成。本批未调用Provider、生产DDL/数据、部署或修改release/integration pin，没有新增需要用户确认的范围。


## T05/T06续推：混合清单单项媒体改稿与未修改项保留（2026-10-05验证，部分完成）

API `329d44fd7f8d0b2402853f5eac4cf47c99fcbed9` / tree `69d2cb5448aa165b35ead9794bac0971736f1a7d`；Client `b8d74b14739f0f7868a4d11e8ddfc40ff5ec78cb` / tree `f61a54c50f8e9d83f59f9c790380de4020841a88`；Web `bb64c8149266eb9ae91aaf4e78b6742fc8fa73c9` / tree `4f3eb69889ec2a077c366872ab50b729ebce0e76`。均沿原自有候选分支推送并远端独立读回；原脏工作区/生成声明保留，未改release或集成pin。

- 不新建关系类型/集合版本：沿用原动作APPEND/RESET因果元数据及已存在的outputs `replaces(requestId/stepId/outputId/sha256)`。APPEND清单里有replaces时只替换该确切仍保留媒体，文字、同批兄弟及其他批次保留；无replaces的新输出正常追加。RESET仍先验证改稿原源，再仅保留明确新manifest。
- 先验证整个批次相对上一份仍保留清单的原源，再应用修改：错hash/foreign/已丢弃/重复改同一原源/同批依赖拒绝；不偷选历史稿、不按最新MIME推断。API重放过程中的临时replaces不进入冻结deliveryTargets，广告仍只含原文字或实际新producer outcome＋精确outputSource。
- 共享实际writer/read fixture接通“文字＋两批图片→只改第一批小鸟→只改较早文字→再改该小鸟并追加poster”：文字及未修改图片保持，已被替换的旧bird/blue不进入当前交付。后续自然议事只选五个仍保留媒体的真实asset refs及终端因果父；Client保持原目标和parent、不接受已经替换的历史文字。
- mounted事项页按“修改后的文字＋五个确切媒体原源”展示及selectedOutputs验收；原key/body/hash在未知ACK、remount及无关晚到媒体中不变，不要求保存、不重启工具。

验证：API15组 **140 PASS /0 FAIL /0 ERROR /0 SKIP**，Client4文件 **52 PASS /0 FAIL /0 SKIP**，Web10组 **169 PASS /0 FAIL**，scoped lint及build exit0；gallery基线12/当前12、测试0/0，无新增诊断。API/Client/Web共享fixture同字节SHA256 `bbaec5b50427035f56e49fc58b3795e5af47ce0bc17829d88863a9a4c27a71fd`。**原持久记录与execution reader、native engine及媒体HTTP仍fixture；不是实际Agent生成、部署浏览器、正式Flow或用户验收**。回执见[mixed-media-edit-v1](implementation-evidence-20261004/mixed-media-edit-v1/manifest.json)。

保留失败：API/Client本批首次全部通过。Web新测试首轮66通过/2失败：网络顺序单元测试把manifest内部顺序也反转，却按有序列表比较，改为精确ref tuples排序比较（mounted所见顺序与API仍逐项相等）；mounted无关晚到request错误复用第二批step而非第四批，remount被严格URL校验拒绝，仅修该fixture来源。最终169及lint/build全通过，未放宽生产来源或权限校验。

**剩余**：原legacy EXECUTE媒体起点（无typed ACTION_REQUEST basis）及更多独立root明确意图尚未接齐，仍不制造outcomeId或历史合并。T05/T06整体不标完成；T07–T09真实Agent/材料/可选保存/刷新/隔离、唯一集成候选与既有正式Flow同Run发布未完成；本批未调用Provider、生产DDL/数据、部署或修改release/integration pin，没有新增确认事项。


## 用户范围收口：旧议事和媒体测试数据直接清理，不做适配（2026-10-05）

用户明确“旧的议事和媒体信息直接删除，那都是测试数据，不需要做适配”。已取消 legacy EXECUTE 原媒体起点适配、旧记录补写/迁移，不继续为旧测试数据开发兼容链路；之前回执中的旧起点待办由此次决定覆盖，历史源码/测试事实不改写。

- 已同步 tasks / implementation-design，后续转当前新流程真实Agent和三端联调、既有正式Flow发布与上线验收；仅补实测缺口。
- 删除范围只针对指定环境的旧议事及关联媒体测试数据，不包含代码fixtures、源码、测试回执，也不隐含全库/全账号/全媒体目录清空。
- **尚未删除任何运行数据或媒体文件**：需要明确环境及清理范围，之后核对依赖与共享引用，再执行限定清理并回读结果。新联调数据和非目标记录保留。
- 本次仅文档范围更新，未运行构建/Provider/流水线、未写生产数据库、未修改release/integration pin。T05/T06新流程真实业务验收及T07–T09仍未完成，取消旧兼容任务不等于整体交付完成。


## chcbz 历史聚义厅议事与关联媒体限定清理（2026-10-05）

用户随后明确删除对象为 `chcbz` 账号的历史议事和关联媒体。已核对账号实际归属并冻结当前线上 `jia` 库 109 个聚义厅 conversation IDs（77 个原可见、32 个已墓碑）；不是全账号聊天/全库/全媒体目录清空。未纳入此次冻结范围的新记录不随脚本重新搜索删除。

- 已清除 **370 条消息、10 条请求、5 个 turn、5 个 snapshot、5 个 step、5 个 execution link、5 个 outbox、8 个事件、2 个媒体 asset、2 个保存操作、3 个会话资料引用及3个引用操作、5个旧悬赏会话绑定、1个会话验收操作及其1个 item**。删除7个非TASK终态执行及其2个input/3个output；没有删除或改动TASK执行/任务/资金。依赖按顺序删除，未关闭外键检查。
- 109 个原会话保留**无正文/标题的删除墓碑**，增加 lifecycle generation，阻止旧请求或晚到回调写回；不是物理删除会话ID。删除旧绑定后，新点将可走已有会话bootstrap，不做旧数据适配。
- 删除3个仅归属上述议事的工作区文件及版本、2个相关文件操作，实际删除 **3个专属内容对象，共2,081,107字节**。对象删除前验证规范路径、无符号链接、SHA256与剩余引用；提交后再核对引用并逐个删除，没有递归清空存储目录。
- 保留**13条普通/NULL类型聊天、21个TASK执行、1个Agent正式验收证据及独立正式交付/原始上传**；相关保护记录在提交后以新连接独立读取，逐字节摘要一致。另1个候选媒体对象仍被独立正式成果引用，实际文件及SHA256再次验证保留。
- 私有恢复目录只在服务器维护区（0700；数据/SQL/媒体备份0600），包含冻结范围、原记录、恢复SQL、对象副本及独立回读回执；媒体恢复副本SHA256已核验。数据库内容、owner标识、私有文件、恢复SQL不入Git，仓库仅存脱敏计数摘要。
- **尚未核验Elasticsearch索引残留**：实际配置的localhost:9200拒绝连接，同网络命名空间复核亦失败。未启动/重启搜索服务、未操作全局索引/Redis；主数据与专属文件清理完成不代表搜索索引或外部Agent副本已彻底擦除。

回执：[限定清理摘要](implementation-evidence-20261004/chcbz-history-cleanup-20261005/manifest.json)。本次没有Provider调用、构建、Flow发布、release/integration pin变更；没有新兼容层或清理产品。旧适配继续取消；后续仍为当前新流程真实Agent/三端联调及既有正常发布。T05/T06真实业务验收和T07–T09仍未完成，不能因清理完成标记整个功能交付。


## 三端候选收敛、Web云测实际失败修复与正式云测（2026-10-05，进行中）

只读查询确认旧Web `4403172/165` 已FAIL（旧候选12edde24，3036通过/7失败/2pending），API `5260799/108` 的SUCCESS仅对应旧候选75357f，不可冒充本轮结果。两条当前配置均只有cloud_ci，无部署阶段；保留暂停配置，不恢复、不新增流水线。

- 对7项实质失败修复测试接线：4个实际JuyiHall挂载夹具现在注入真实 `useHallDrafts`（保持原会话/阅读器/工作空间五轮状态和密议检查）；共享资料样式按真正承载的HallMaterialPicker核对；实际表单按当前“提出需求/添加”及默认固定最新版本验证，禁止版本选择控件；既有独立正式任务资料控件保留，嵌入事项只走议事，并新增mounted双场景无POST断言。Windows `.pathname` 造成的额外文件读失败改为 `fileURLToPath`，未改生产来源/授权校验或跳过测试。
- 当前源码诊断：6文件先34通过/7失败，修复后 **42通过/0失败**；原阅读器实际Hall挂载用例 **1通过/0失败**；两文件scoped lint exit0。保留失败日志；这是低成本定向诊断，不替代正式Flow，也没有本地生产构建。
- Web新提交 `10ff97b52b710564e9918010a437ed35621ff235` / tree `19b299885d27daf35edf146b1f3dec5afd46ccb6`，仅7个测试文件，已沿原特性分支推送；原生成声明/脏工作区未提交。
- 现有API `329d44fd`、Client `b8d74b1`、Web `10ff97b` 对各自当前develop均为快进；已合入三个远端develop并独立读回。根api/web gitlink固定此配套源码，当前仅candidate，不标accepted/released，不改历史冻结合同/回执。
- develop push后只读复核没有对应新Run，随后每条单次明确Start。**API `5260799/109`、Web `4403172/166` 已RUNNING**；当前Run来源显示develop但commit字段尚未报告，不提前声称checkout SHA、云测、制品成功。未重发未知请求、未取消他人Run。

回执：[三端与原云测进度](implementation-evidence-20261004/integration-cloud-ci-20261005/manifest.json)。三端源码已收敛，正式云测/同Run制品仍等待；未更新API/Web/Agent实际运行版本，未调用Provider，未新增生产数据。T05–T09真实新流程联调、可选保存/恢复/隔离和上线验收仍待实测；旧数据适配不恢复。


### 本轮正式云测与制品增量（2026-10-05 19:54 CST）

API `5260799/109` 已 **SUCCESS**，实际checkout与制品receipt/metadata均为 `329d44fd7f8d0b2402853f5eac4cf47c99fcbed9`，tree与候选一致；同Run下载制品、不解压部署，已核对receipt SHA与sidecar JAR SHA。归档312份suite报告、2667个测试条目，失败/错误0，**skipped 101**（100项XML未给原因，1项缺精确Redis4.0.6测试二进制）；多个Gradle selector可能重复覆盖测试，不称2667个独立用例全部PASS。制品 SHA256 `d0fa282ac520379b69f8f302a3debd90604dc8145d4ec4120e6bc306421d6570`；JAR SHA256 `3170b50d19b9c28bcd734e1a6a474023be3a2e6a7a4196a12993e9fddf98caa8`。详见同目录 `api109-artifact-verification.json`。

Web `4403172/166` 实际checkout确认 `10ff97b52b710564e9918010a437ed35621ff235`，代码扫描SUCCESS，完整测试/构建仍RUNNING。日志API more=true并提示Too many logs，不能以早期日志推断终态。未重复Start、未改部署配置。上述更新覆盖前节“SHA pending”的阶段记录，**仍未发布、未真实业务验收**。


### Web166失败的最小修复及Web167（2026-10-05 20:15 CST）

正式Flow166已FAIL：**3136 passing /2 pending /10 failing**，扫描SUCCESS，未进入完整Vite构建，无同Run制品。失败摘录已按环境/URL过滤落盘，非完整日志审计。10个失败对应5个旧测试文件：榜文创建仍期待旧createTask接线、聊天工作空间仍期待已移至＋菜单的按钮class、Overview仍期待用户已取消的版本选择器、原表单4个场景仍找“张榜”。

仅调整上述5个测试文件，生产源码未改变：准确核对创建成功后点将包装器、真实Composer→ChatPanel工作空间事件链；资料默认固定最新版本且无版本控件，取消改用另一个文件验证未确认选择不污染已确认资料，保留混合预览/下载GET-only、移除、scope切换和旧ack隔离。补Windows fileURLToPath及CRLF精确闭包解析。定向 **86 passing /0 failing**；scoped lint基线7错误、候选仍7、rule/message无新增（不能写lint通过）。本地初次诊断在CRLF closure导入处中止，不能虚报本地10FAIL，正式红证据来自Flow166。

Web新exact源码 `f6b81b40ee4a579c579af4cb7ab1e0e76e362173` / tree `3f70c8a345ef09359b0169785ec66d5f8cdf5102` 已推原特性分支及develop并读回；生成声明及work未提交。API/Client保持原精确候选。两次只读检查develop push未创建新Run，限定新SHA和原cloud_ci配置、确认无活动Run后仅Start一次，**4403172/167 RUNNING**（build/test529162804、scan529162805）；actual checkout尚未报告，不把expected当actual。不重复API109、不跳过测试、不改暂停部署。

真实新流程仍需API/Web/Agent运行版本更新及现有模型/工具调用；已向用户提出具体发布/预算授权问题，尚未执行这些动作。当前源码/云测修复继续，不将发布授权待定误标为已验收或目标完成。

20:17 CST只读回执：Web167实际checkout已报告f6b81b40ee4a579c579af4cb7ab1e0e76e362173，与目标一致，scan SUCCESS，完整测试/构建仍RUNNING；覆盖上段checkout pending的阶段状态。


### Web167正式云测/构建/同Run制品完成，仍未发布（2026-10-05 21:36 CST复核）

Web `4403172/167` 已 **SUCCESS**，build/test529162804与scan529162805均SUCCESS。云端报告与同Run包内mochawesome统计一致：449 suites /3148注册条目，**3146 passing /2 pending /0 failing /0 skipped**；正式Vite于20:35:51完成。此前166的10项失败现均通过，未跳过测试或修改生产源码。实际checkout、包内source-commit与source-tree分别匹配 `f6b81b40ee4a579c579af4cb7ab1e0e76e362173` / `3f70c8a345ef09359b0169785ec66d5f8cdf5102`。

同Run归档106693406 bytes，SHA256 `2e9b1b4167b76c8931aac843abbad8faf323a1590f75e457f1914222ca0f7a12`；只读逐成员校验，未解压安装，364个dist文件集合覆盖精确相等、逐项size/SHA256均匹配release.json。包内真实package_version仍1.0.1，不把它改称新产品发布版本。详见 `web167-artifact-verification.json`。API109已完成的正式测试/冻结JAR证据沿用（101 skipped如实保留）。三端develop再次读回为API329d44fd /Clientb8d74b1 /Webf6b81b4，与配套候选一致。

21:35只读配置复核两条pipeline SHA256均与启动前相同，仍仅cloud_ci、无部署阶段；本轮没有恢复暂停配置、更新运行版本或调用Provider。现有CI-only Run不能追加不存在的部署job，不能以直接手工安装或本地包绕过既有Flow；获得发布授权后按原路径完成必要最终发布Run，由该Run使用自己的测试/构建/制品/部署身份，既有历史CI证据保留，不伪装成已部署。

**仍未完成的真实结果**：实际API/Web/Agent运行版本配对，新流程无资料提需求→点将→真实成果→同会话改稿→不保存直接验收；混合资料/仅附件、文字与单项改稿保留其他成果、可选保存与刷新不重生成、跨账号/任务和密议隔离、上线精确制品核验。源码/云测已收敛，但这些T05–T09真实业务要求不能由fixture或制品通过替代。已提出具体发布及现有预算内真实调用授权问题，待用户答复；不新增旧数据兼容或独立验收工程。


### 2026-10-05 23:30 CST 三端发布接续

Agent已实装Client4e70c4f，两实例payload/config已核验；主机发布脚本forward-only及现有备份别名问题已修复，26回归PASS；零点调度分页18回归PASS。API5260799现有deploy已恢复，明确新版失败向前修复、不自动降级；等待2026-10-06 00:00既有调度，未创建最终Run。Web仍CI-only且仅API健康后发布。真实业务验收NOT_RUN，T05–T09不标完成。详见 [接续说明](runtime-release-20261005.md) 与 [实际回执](implementation-evidence-20261004/runtime-release-20261005/manifest.json)。用户已授权发布及既有预算内真实调用；IAB已打开chcbz登录页待用户登录，无需传递密码。


### 2026-10-05 23:47 CST 立即发布覆盖

用户明确取消零点等待。API既有Flow Run110已创建，实际检出329d44fd已只读核对并绑定发布intent，无重复Start；正在云测，尚未上线。两个timer临时暂停防重复，本次三端发布完结后恢复。API完整健康后立即发布Web。详见 [接续说明](runtime-release-20261005.md)，T05–T09及业务验收状态不变。


### 2026-10-06 00:40 CST 立即发布实际进展

Agent已完成。API110新JAR现健康运行，finalization确切一次性迁移已验证，但Flow最终FAIL：发布后schema runner仍拒绝报告目录，两表not_attempted。保留失败状态，不重放110schema。修复F06/E05 catalog及E05 hash pin，60离线回归通过并CAS安装。新API5260799/111正式测试部署正在运行，Start UNKNOWN已只读核对唯一Run/真实检出并绑定intent，未重发。Web仍API-first待111最终核验后立即发布，T05–T09 NOT_RUN。监控已恢复，两个防重timer暂未恢复。详见 [当前接续](runtime-release-20261005.md)。


### 主机北京时间2026-10-06 01:04 最新接续

API111 CI成功/JAR健康，但F06旧SQL pin不匹配新版owner-fenced资源，Flow FAIL；保留110/111报告，不重放schema。按当前JAR资源及已有mandatory-owner schema更新严格门禁，62回归通过；真实JAR/MySQL catalog只读equivalent及负控制拒绝已验证，未执行DDL，01:00 CAS安装。最新正式API112运行（CI529282011/deploy529282012），唯一Run/checkout/time/config只读reconcile已完成并绑定intent。Web仍API-first，T05–T09 NOT_RUN；监控健康，timer最后恢复。详见 [权威接续](runtime-release-20261005.md)。


### 主机北京时间2026-10-06 01:17 / UTC2026-10-05 17:17 正式API完成

API5260799/112最终SUCCESS，CI/唯一主机/同Run制品/JAR/record/approval/真实健康均核验，F06 PASS existing_equivalent，E05 not_admitted未调用。Web原deploy已一次恢复，Web4403172/168正式CI发布链运行，Start UNKNOWN只读核对唯一168/checkout marker/CI_SHA/time/config并写intent，没有重发。新同Run Web制品和线上dist字节待核验，T05–T09 NOT_RUN。Agent已完成；监控恢复，Web正式完成后恢复两个timer。见 [权威接续](runtime-release-20261005.md)。

## 2026-10-06 01:30 三端正式上线与业务登录阻塞

API112、Agent双实例4e70c4f、Web168正式发布均已完成。Web168同Run源码/tree/归档及364个dist文件安装与公开HTTPS完整字节一致；3146pass/2pending/0失败/0skipped。核对远端develop及安装record后已恢复两个既有nightly timer。刷新真实IAB出现新版统一资料入口，但随后跳转登录页，chcbz需重新登录；业务T05–T09仍NOT_RUN，不标全部完成。详细状态及证据见runtime-release-20261005.md最新权威段。
