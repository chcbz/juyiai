# 本地 Gradle 定向验证根因矩阵（2026-09-26）

任务：`BUG-USERNAME-ENCODING-INTEGRITY-20260926`

| 尝试 | 输入 | 终止点 | 根因 | 产品代码/测试是否执行 |
| --- | --- | --- | --- | --- |
| 1 | 普通 orchestrator `./gradlew` | 根 `build.gradle:109` 配置期 | 本地未定义只用于 publishing DSL 的 `repoUsername/repoPassword` | 否，0 tests |
| 2 | 增加 Flow `cold-init.gradle` | init script line 14 | 该脚本明确只允许 `flow_remote`，需要 `CYF_FLOW_GRADLE_ACTIVE`、外部构建目录及受管 Maven consumer 凭据；本地验证不能伪造 Flow 环境 | 否，0 tests |

## 已验证的最小修复

不伪造 Flow 环境、不读取或传递 Maven 凭据、不修改产品源代码。第三次输入只通过 Gradle project properties 为根工程 publishing DSL 提供非发布占位值：

```text
-PrepoUsername=
-PrepoPassword=
-PreleasesRepoUrl=https://maven.aliyun.com/repository/public
-PsnapshotsRepoUrl=https://maven.aliyun.com/repository/public
```

定向任务不包含 publish；这些属性只阻止配置期读取不存在的 extra property。依赖解析仍使用仓库现有配置和本机缓存。若第三次仍在配置、编译或测试失败，停止本地重试，保留真实失败并转云端/后续根因处理。

## 运行期资源归因

第三次 OAuth 定向选择器已成功：41 tasks，BUILD SUCCESSFUL，证据键 `ea121ff41e07f5f68f1b27b8976f6fe89cb85ba0b8cd67d0e837429068903f2e`。

随后 User 两类测试在 `testClasses` 完成后、测试 JVM 启动阶段遭遇全局 OOM。内核明确记录：

```text
Out of memory: Killed process 3888526 (java), anon-rss: 618568kB
```

同一时段另有不属于本任务的 Chromium 进程被 OOM killer 处理。本任务不操作、不取消该 foreign 进程。修复输入改为：一次只运行一个测试类，Gradle daemon `-Xmx384m/-XX:MaxMetaspaceSize=256m`，Test worker `maxHeapSize=256m`、`maxParallelForks=1`；不以资源阈值拒绝执行，但若同一低内存输入再次 OOM 则停止该本地选择器并保留失败。
