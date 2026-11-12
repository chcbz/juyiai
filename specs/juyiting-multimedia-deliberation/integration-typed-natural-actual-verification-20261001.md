# 自然议事闭包：本轮真实验证与修复（2026-10-01）

本记录为源码/验证证据，不是第二任务台账。不改冻结合同、研发 pins 或产品验收状态。运行Owner/gate仍在主工作区 `docs/implementation/TASKS.yaml#runtime_ledger_json`。

## 1. Web实际通过项与未通过项

原Owner候选 `eba12b14bfe74b31272902b619e6f76376efc60f` / tree `34ce0ce7d790913ab4bdf7334a6794186ba661f3`，12条授权路径。Main实际执行原7文件定向测试：**31通过**。但主线程补测真实模板/emit/production composable边界：**7失败**，因此未晋升。

1. Page将嵌套cards/pending/recovery ref本体传给组件，真实Vue接收RefImpl而不是数组/null/布尔值。
2. BountyDiscussionPanel丢弃send-message参数，本轮选定reference没有到达Page/API。
3. 较晚返回的OPEN覆盖已收到的ANSWERED，问题状态倒退。
4. ANSWERED readback未清除已选pending，下一条仍拟答已回答的问题。
5. foreign task outcome被加入当前cards；历史assignment仍应遵循原scope读权限，不能借修复隐藏历史。
6. GENERATE_IMAGE携带合法参考源时被parser丢弃。冻结Client合同允许GEN引用image，并非仅无参考。
7. recoveryAvailable被首次模板读取缓存为false，原键UNKNOWN持久化写入后不响应更新，恢复按钮不会出现。

原始未改probe、stdout、31项日志和SHA见[便携manifest](integration-evidence-20260928/web-typed-eba12b1-main-failures/manifest.json)。Owner按固定矩阵修复新child，并补typed_question_answered的权威GET提示、cold recovery/dispose生命周期；不是提高数字门槛或关闭功能来获得通过。

## 2. API实际编译失败与新源码修复

`b3c02a1646a583d0ceda08dc83922ec90859f003`的正常生产源图编译成功，但测试编译真实失败：旧AgentTaskProviderCostConsentServiceImplTest.MemoryDao未实现新增follow-up DAO接口。实际javac报revokeFollowup一项；另五项由接口/源码逐项比对确认。此次**0测试、0 fresh XML**，不能把62项V3/MySQL3和82项V2当通过。

原Owner已提供最小child `da1710bcbe966209015941debdcee179034a0bb7` / tree `337ebd925036d0faba365249a105d4784d95dc31`，parent为b3c02a，只增加该一个测试文件的62行；六方法实现purpose/scope/operationGrant/版本与合法状态CAS，生产源与selector不变。Main独立核对parent/path/tree/blob/whitespace和Owner证据。该child仍**待实际验证**，不是源码验收或发布结论。

[精确验证授权矩阵](integration-evidence-20260928/api-followup-v3-memorydao-child-verification-matrix-20261001.json)允许原Verifier在自身干净worktree更新该child、保持真实正常源图/AP/依赖/既有测试并经orchestrator串行运行；不得删除V2、缩selector、复制class或用手工javac绕过。原OOM/import/testCompile失败分别保留。

## 3. 完整交付仍须继续

API原子typed final/question CAS/new CHAT续办包仍在独立Owner施工。本轮不合develop、不生产构建/部署、不调用付费Provider、不修改生产数据库。后续必须精确组合、真实隔离MySQL及当前session/身份闭包，再继续真实INSPECT、双接应、全部媒体预览下载保存、正式交付验收/完成与目标版本发布。源码切片通过不代表34项产品/29桥/浏览器全流程通过，未达到条件不通知“可以验收”。


## 4. 第二轮真实边界复核（2026-10-01 17:40，北京时间）

以下是新输入/新测试的实际结果；不改写前文历史失败。证据、固定 probe 与摘要见[本轮便携 manifest](integration-evidence-20260928/typed-natural-second-boundaries-20261001/manifest.json)。

### Web：原七项修复保留，但还有实际遗漏

Owner 两次修复后的 `55a66c8316a8a419f28428c9e7191a3c3135212a` / tree `0bd13c2fed2af84affa97df94dd9637d3988fd64` 已在 Main 干净精确 worktree 复核：原六项 probe 和 recovery probe 均通过。Owner 的37项只代表其自检范围。Main扩大到13个相关旧新测试文件，实际 **189通过、2失败**；两个失败均是实际挂载JuyiHall的语音测试 harness 未接新增 `useHallBountyRequestCatalog`，不是已经证明语音产品故障。原Owner获得仅该一个测试路径的追加授权，保留原语音用例并修补真实依赖。

Main另补两个独立、固定production composable probe，结果：

- **同版本OPEN轮询失败**：选择待澄清问题后再读完全相同OPEN，选中状态被清；实际下一次POST错误地成为DISCUSSION，丢失CLARIFICATION_REPLY及问题CAS。根因比较不存在的 `selected.stateVersion`，而选择记录保存的是 `expectedPendingQuestionStateVersion`。原Owner已产出单composable/测试最小child `38e67579e2efdadc02b0850cfbcc72ff0324247a` / tree `aef03511e118dab01a9cdf8ce38407efdf2fdf8d`；Main在干净精确child实测同版本OPEN保留选择、实际POST保持CLARIFICATION_REPLY及问题CAS，且原六项及recovery固定probe全部继续通过。回执绑定和语音harness仍待修复，不据此提前提升分支。
- **新typed回执绑定负向1通过、6失败**：正确完整回执可采用，但不同userMessageId、turnId、conversationGeneration、目标Agent、turn所属conversation、缺失requestRevision均被真实采用，并继续读取content。需在新typed适配入口严格核对受理回执与权威request/turn后才写状态；不改旧兼容 `applyRequestView` 的全局语义。原Owner继续独立child及回归，不能把不匹配回执当成功或制造第二次POST。

上述都是定向源码边界测试，不是浏览器、真实服务端/Provider或产品验收。

### API：生产和测试已编译，真实MySQL setup尚未通过

`da1710`测试源实际出现4处继承fluent setter返回BaseEntity的编译错误；原Owner单路径child `5f187b5b7be61f590f4592c819f8fb481a8c7768` / tree `cdde506acf9e4644fc8766efe89352a6599db210` 将其拆分调用。正常源图再次实际运行，Agent **37项中34通过、3失败、0跳过，9份新XML**，不是62项通过。三项隔离MySQL测试均在setup被 `legacy.chk_pwex_controlled_consent` CHECK定义比对阻止，业务body未到达；Chat25和完整82项V2 **NOT_RUN**。Verifier已退出并保存真实失败，未盲目重跑；原Owner进行CHECK目录/标准化的最小源码诊断，Verifier仅对自有精确fixture做只读目录核验，不移除约束或改fixture来过测。

### 分支和设计交付与产品状态分开

本轮再次直接读远端：SDD/API/Web/Client四仓feature存在、与对应本地HEAD一致，当前fast HEAD均是feature祖先；不重复建分支或merge。SDD核验点 `4691f89c`，组件已推送基线仍为API `87c0acc` / Web `1993b88` / Client `2f69072`；本次仅追加文档证据，不替换组件pin或gitlink。长期方案、详设v2和开发计划继续有效。原子typed闭包仍在原Owner施工，真实INSPECT、双接应、全部媒体及完整浏览器/正式验收/版本发布未关闭。
