# JuyiAI 工作区与 Git

根仓 `chcbz/juyiai` 通过 `api/`、`web/`、`runtime/` 三个子模块固定组件版本。
组件 `origin` 分别为 GitHub 的 `juyiai-api`、`juyiai-web`、`juyiai-runtime`。
`develop` 用于开发集成；`main` 为对外入口。不要自动部署分支最新提交。

先在组件提交并推送，再在根仓提交对应 gitlink；使用 `git submodule update --init --recursive` 获取固定候选。
`./gitw api|web|runtime ...` 可定向执行 Git 命令；`./gitw all ...` 遍历三个组件。
旧仓历史保留在原本地仓与私有归档中，不合并到公开分支，不使用 `push --mirror`、`--all` 或 `--tags` 批量上传旧引用。

迁移没有发布应用、运行数据库迁移或更改生产安装目录。
