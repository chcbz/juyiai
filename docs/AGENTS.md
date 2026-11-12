# docs 文档维护与发现

适用于本目录，继承[根规则](../AGENTS.md)。先读[统一入口](README.md)，只加载任务相关的一个责任专题和必要源码/工具。

- 需求/现行合同归[specs索引](../specs/INDEX.md)，术语与冲突仲裁见[规格维护规则](../specs/AGENTS.md)，实现摘要归知识库，操作方法归既有runbook；不要再新建“最新/完整/最终版”同义副本。
- 历史handoff、evidence、receipt、原冻结合同与基线保持原字节/来源，不批量重标日期/通过；引用历史时写清候选和范围。
- 发现旧规则冲突，应修正当前正文并指向唯一责任合同；无法核实的支持资料保持未核实，不凭文件日期推断有效或删除。
- 新当前文档须从根AGENTS→本README/专题导航可达，并在既有`sdd-document-map.json`的discovery支持选择中登记（不是新任务台账）。
- 复用`./sddw check-docs --all-docs`检查路径和可达性，`--catalog`看全量角色；默认搜索复用`./docs/knowledge-base/kb-search.sh --project '<关键词>'`，追溯才用`--project-all`。
- 导航检查不等于内容与源码全部同步/线上验收。源代码、当前合同、精确测试、安装与业务验收分别记录，默认不构建、不部署、不调用收费Provider。

- 已退役专题按sdd-document-map中的继任入口维护，不因新增五件套/细则或显式选择而恢复为当前合同；恢复须有新的明确业务依据。旧BASELINE_REFERENCE仅定向/全历史检索，不进入默认当前项目搜索。
