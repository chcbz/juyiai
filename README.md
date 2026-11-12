# 聚义 JuyiAI

以事项为中心的开源多 Agent 协作项目：让 AI 各展所长，把事情办成。

本仓管理跨组件文档、开发工具和固定版本引用。前端、后端、Runtime 分别独立维护。

| 仓库 | 职责 |
| --- | --- |
| [juyiai](https://github.com/chcbz/juyiai) | 集成入口、规格与开发工具 |
| [juyiai-api](https://github.com/chcbz/juyiai-api) | 业务、权限、事项、钱包与调度 |
| [juyiai-web](https://github.com/chcbz/juyiai-web) | Vue 前端与聚义厅交互 |
| [juyiai-runtime](https://github.com/chcbz/juyiai-runtime) | Agent Runtime、codex-bridge 与技能 |

## 获取源码

```sh
git clone --recurse-submodules https://github.com/chcbz/juyiai.git
cd juyiai
# 已克隆但没有组件时：
git submodule update --init --recursive
```

根仓 gitlink 是集成版本；不要用 `submodule update --remote` 代替固定版本验收。
`main` 是对外入口，`develop` 是开发集成分支，首次迁移两者指向同一候选。

## 配置和运行

- [API 配置说明](api/OPEN_SOURCE.md)：数据库、中间件、身份和模型配置由部署者提供。
- [Web 配置说明](web/OPEN_SOURCE.md)：本地默认 HTTP，HTTPS 使用自行提供的证书。
- [Runtime 说明](runtime/README.md)：接入、隔离、执行与打包。
- [文档入口](docs/README.md) · [架构和组件地图](docs/codex-project-map.md)。

**当前是源码迁移基线，不是已经完成干净环境一键安装验收的发布版。**
API 仍使用现有 Gradle 插件与依赖仓配置，全部外部依赖的公开可用性需要单独验证。
模型调用需要部署者自行配置凭证，并可能产生第三方费用。
历史规格中的验收结果不代表这个公开候选已完成全量回归。

## 安全与历史

本次导入仅包含脱敏后的当前源码，不携带原仓提交历史、生产证书、私有会话、内部运行证据或真实服务密钥。
原项目技术标识 `cyf`、`cn.jia` 与固定安装路径按兼容契约保留，不因品牌变更批量替换。
部分技术文档仍引用未公开的历史证据；这些引用不作为公开仓的操作步骤或验收证明。
请勿提交 `.env`、密钥、证书、用户数据或生产日志；配置示例不包含可用服务凭证。

## 许可证

MIT，保留原作者版权声明；第三方依赖与素材遵循各自许可证。
