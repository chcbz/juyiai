# U2 受控参考图快照与议事执行关联（2026-09-29）

开发基线：API `codex/juyiting-multimedia-deliberation` 提交 `ca005e8b4453f14ae74b8c08f81e471e528920bd` / tree `03105bcae9d8d2227d125ddbad6ebb122f1a08b2`；远端同 SHA，未合 `develop`、未发布。

- API 子树 `b24355c1a531da732b08a314e91202351d4fffa3` 新增租约约束的 runtime 图片输入清单和二进制读取：赋权输入版本与执行记录逐项比较；读取时复核当下授权、执行 fence、数据摘要；参考资料不回退旧 `/inputs`。原子树经 orchestrator 定向 Agent `mmdU2ConversationOutput` **47/47** 与 grant `mmdU1Grant` **18/18**，0失败/错误/跳过；原始日志在工作树 `evidence/u2-references/gradle-b24355c1.log` 和 `gradle-grant-b24355c1.log`。这些不是最终跨模块树的完整回归。
- 集成 `ca005e8b` 在服务端议事协调器验证持久首轮参考清单与**当前 grant** 的 fileId、version、purpose、MIME、bytes、SHA-256、顺序全部一致，才将不可变引用传给 conversation execution；旧请求若 grant 存在不可见参考资料拒绝绕过，暂不支持的素材格式保持 `WAITING_INPUT_RESOLVER`，不会被忽略后盲生图。后端创建/领取分别复核授权和租约，不信任聊天 metadata、模型话术或浏览器自填路径。
- 集成 exact tree 经 orchestrator 串行 `:chat:jia-chat-service:chatDeliberation` **24 类/121 项，0失败/错误/跳过**，其中 coordinator 7项；证据 key `ad67f3b1741482ac3bb453499beb39ba72ab0da49cd8f43720a731e3f1abaaf8`、日志 `evidence/u2-references/gradle-chat-ca005e8b-local.log`（SHA-256 `108ff85eb58e5be41f481a8fb7c4b7eb6b519722e254a419f3989129b32bb75a`）。首轮使用 Flow-only init 在本地被拒于编译前；已归因并改用非发布本地 init，未伪称 Flow Run。

**仍非可验收版本**：Agent Client 参考字节安全落地、真实已有付费授权/生图执行器、媒体 ready/实时会话关联、用户主动保存/正式成果晋升/验收、真实 MySQL/浏览器与分版本构建发布均未证明。后续必须以整合后的最终组件树重跑必要范围、核对费用授权，再决定 `develop` 合并与版本发布；不得因该定向结果通知用户可以画鸟验收。
