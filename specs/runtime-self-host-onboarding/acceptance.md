# 最小方案验收合同

## 状态

2026-11-13定义；**本轮无应用验收通过记录。** 删除上一稿连接世代/批调度/目标五态测试要求，它们不再属于目标设计。已有身份、资金、隔离及幂等测试保留。

| 范围 | 必须观察到的结果 |
|---|---|
| 同一stateRoot重复启动 | 原独占锁拒绝第二writer；失败退出不错误释放仍在执行的所有权；不新增connect/hostGeneration |
| 同机两Agent | 一个Runtime主进程、各自原异步worker/执行身份；一个慢/失败/撤销不停止另一个；不新建整机调度器 |
| 空主机登记 | 一次主机secret；API只存hash；本地确认归属前不执行；不向浏览器输出secret |
| 授权目录 | 只列认证host的当前授权；沿公共cursor/pageSize/hasMore合同，分页无副作用；局部结果不误撤其他worker；新Agent无需人工改配置 |
| 主机/Agent权限 | host token不能领取其他host或非所属Agent命令；预准备不能越过付款准入；付款后同worker不用第二secret |
| 原生目录入口 | GET只放行目录路径及各一个cursor/pageSize，页尾hasMore/nextCursor一致、无body；exchange POST继续拒绝query；非法方法/路径/身份头仍拒绝 |
| 退款授权 | 原退款与旧授权撤销同事务；任一步失败全回滚；重请新授权，不恢复旧UNKNOWN |
| 存量关联结构 | 无setup的真实控制映射可导入并撤权；不伪造历史邀请；重复lease/授权仍由唯一键拒绝 |
| 真实HTTP | 实际MVC字段白名单与生产/消费fixture相同；不靠mock绕过原第二hash缺陷；保留原单项Q/R/M |
| 幂等与断网 | 重发原结果直到ACK；查询完成操作不再次入队；UNKNOWN不变成FAILED_NO_EFFECT；原生命周期journal恢复 |
| 托管正常流程 | 用户不拿JSON/生成token/配主机；原套餐、报价确认和扣费路径不回归 |
| 自部署后续邀请 | 复用已登记主机，不新起Runtime；主机秘密不进入Agent沙箱 |
| 目标库存 | 用实际目标，未知不填零、停用技能仍按原规则计；确认及prepare摘要核对保持原责任 |
| 首费与退款 | reserve/capture各一次；ACK/在线不是ready；精确前安装退款后可重请，有/未知安装不能套捷径 |
| RETAINED混合历史 | 同一用户两条旧RETAINED不阻断正常PAID/TRANSITION到期；无伪造新付款/期限；正常付费零金额仍报错，未知来源不静默跳过 |
| 自动续费启用 | 确认auto-renew开关与实际处理器注册、原到期待办一致；不能仅凭lease/待办存在宣称自动执行 |
| 切换旧日志 | 保留已发现RECOVERY_REQUIRED原operation及journal，不双发/自动重放；李逵CURRENT与UNKNOWN不改写为SERVICE_READY |
| 离线 | 主动/永久离线有余额仍按原30天续费；不依赖host发现/心跳/回执 |
| selfhost解绑 | 不要求远端stop/cleanup，不删本地；平台事项/资金按原规则收尾，旧授权拒绝后续访问 |
| managed资产复用 | 保留原停止/清理事实；实际跨用户沙箱不能互读秘密/目录/会话；原native条件skip不能算通过 |
| 存量 | 李逵不重复登记/延期；扈三娘按固定原身份、plan/cutover登记；不重新预占/enroll/adopt；收费与控制映射分开 |
| 路由迁移 | 明确配置选择；旧未知命令不双发；outbound bean存在不截断既有托管；不新建动态路由平台 |
| 持久化 | scope先于LIMIT/锁；PK/UK/FK及原事务保留；无CHECK/触发器/启动自动DDL |
| 失败恢复 | host密钥撤销/更换沿受控维护；不承诺无中断/双主；失败不清秘密以外的用户资产或财务历史 |

实际测试前须固定代码tree、输入/selector和环境；原95/55项等历史局部通过不迁移到本方案。API尚未执行的SQL及未完成layering不能写成已通过。文档链接/JSON检查只证明文档形状，不证明实现和生产完成。

本次已核实的锁序、wire消费入口和生产事实见[审查](review.md)；已固定的规则不能在实现阶段另选方案。真实运行验证则在实现后按既有测试入口完成，不以本页预写期望冒充结果。


---
## 历史材料（非本次目标合同，不据此重跑或认定通过）



- 本机生成真实manifest和摘要可被Runtime校验；密钥不输出，权限0600，不覆盖旧目录。
- 非默认tenant/client正确贯通，不从owner或旧任务猜租户。
- UI仅明确动作登记；错误scope/含凭据导入被拒；查询不重复创建；状态不伪报在线。
- local文书/技能不再推荐旧API Key/codex-ws-agent或Node版本门槛。
- 本轮不创建新生产installation或执行enroll；已发布源码的正式测试与上线核验见末节，不把它等同新用户登记E2E。
