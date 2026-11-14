# task统一调度

核对日期：2026-11-12。API/Web、统一调度与四个存量实例过渡租约已上线；李逵Runtime1.3.102已安装，本机仍为恢复后的1.3.99。租费/调度最终定向回归、真实事项扣款和真实知识Provider→隔离中心账本已通过各自范围验证；完整交接组合及最终安装余项以[当前验收](acceptance.md)为准，整体尚未交付。Owner：task-scheduling-owner。
用户决定：升级既有task模块，后台业务任务统一注册，优先接入Agent周期收费；后台任务发现按分区条件+游标执行，不进行无条件的全库空扫。多容器支持由当前实际部署要求决定，不作为预留目标。

## 目标与边界
- 复用task的JobHandler/JobRegistry入口，统一定时、事件唤醒、恢复、执行状态及集群协调。
- 保留TaskPlan/Item/Detail及TaskService原业务语义，它们仍服务事项创建和提醒。新增调度持久模型不借旧表字段换含义。
- 业务负责授权、事务、幂等、队列和资金事实；task不决定价格、退款、Agent关系或事项完成。
- 不新增流程编排平台、独立管理UI或付费中间件。已有Redis可用于协调/通知，数据库保存可靠事实。
- 首批费用消费者：到期续费、余额增加后的欠费恢复、锁定超过15天移除。主动离线或永久失联不暂停租期，余额充足且未停止续费仍按每30天续期；Runtime在线/清理状态不参与收费判断。收费完整口径见[费用与交接合同](../agent-economy-marketplace/beta-wen-billing.md)，调度注册不等于生产启用收费。
- 全部系统后台业务调度纳入清单并分批接入；连接心跳、执行中租约和节点本地文件处理须保留节点/执行归属，不能改成任意容器唯一执行。本期不擅改外部Runtime/主机cron。

## 实施前基线（历史调查，不代表当前线上）
API 49f6b4d20abecd87dfceb8db3c7bbf7600e1eb6b。旧cron仅日志；内存互斥非原子；运行状态不持久；Memory自带另一个定时入口。现有AgentTaskEventBroker为进程内有损通知，不是集群可靠消息总线。

## 导航
- [设计](design.md)
- [实施任务](tasks.md)
- [验收](acceptance.md)
- [源码调查与已确认费用规则](../../docs/implementation/handoffs/TASK-SCHEDULING-UNIFICATION-20261109.md)
