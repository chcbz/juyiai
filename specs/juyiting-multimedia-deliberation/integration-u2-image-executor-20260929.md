# U2 图像生成执行适配器候选（2026-09-29）

Agent Client 独立候选分支 `codex/juyiting-mmd-native-image-executor` 提交 `4e3319614f50c86b269155d112bdc4d3c1b348e3` / tree `da89f5eb2fec0415eb2bdfc6355f5459f5f94b4d`，已推送并回读远端；**尚未合入四仓主融合分支，更未部署或开启生图**。

- 仅在 NativeConversationLane 已从 API 核实当前命令、租约、精确输入清单后，且运行环境显式 `CYF_CONVERSATION_IMAGEGEN_ENABLED=1`、本地校验工具可用时，才为原生通道装配 Codex imagegen 执行适配器。默认未配置不执行；旧 workspace 文件生图路径语义不变。
- 适配器从受控运行目录建立新 Codex session，只将受控 `inputs/input_N.png|jpg|jpeg` 文件传作图片参数，拒绝任意路径/符号链接；要求**唯一**已完成的内置 imagegen 结果及真实栅格、reopen 验证。文本路径、纯文字完成、重复 imagegen 或失败均不能冒充交付；字节由现有原生 fence 输出阶段提交（无独立收费测试）。
- exact 候选提交定向 Node 运行 `conversation-imagegen.test.mjs`、`conversation-native.test.mjs`、`agent-client.test.mjs`：**128/128 通过**，0失败/跳过；原始日志在 `evidence/u2-references/client-executor-4e33196.log`，SHA-256 `254a560704f791d47886c8a99e0fd924b1ba3958a5c34970055e2366c3a16528`。首轮隔离 worktree 缺依赖，复用既有 node_modules 非仓库副本后重测；初版负向测试断言错误 message 而非 code，已修夹具后以 exact 候选树重跑。所有 imagegen 事件均为测试 mock，**未调用付费 Provider**。

**出厂前必修**：参考图片受控下载/物化候选合并、合同/目录格式对齐；服务端当前 assign 明确将 `costAuthorizationRef` 置空，真实费用授权和结算尚未接通，因此真实生图依然不可进入。还须证明模型工具隔离及调用副作用未知时不自动二次生图，媒体 part.ready、用户主动保存、正式交付/验收、真实 DB/浏览器/发布均未通过。不能因本分支存在或本地测试通过而启用开关/通知用户验收。
