# 前端 1.0.6 版本化发布

状态：**RELEASED_ONLINE_VERIFIED**。范围：已确认原型对应的厅内议事 UI 优化；不改业务逻辑、不发布 API、不把完整业务闭环标为完成。

## 固定版本与证据

| 项目 | 结果 |
| --- | --- |
| 正式版本 / tag | `1.0.6` / `v1.0.6` |
| 源码 commit | `ee6ca1b6beba562e0c7fa13d422857f554644471` |
| tree | `02afcc5b6f36f834745cc96520528084b8495ab1` |
| UI 来源 | `7264539`；发布提交只修改 package.json / package-lock.json 的版本号 |
| Flow | `4403172 / Run180 SUCCESS`；扫描、测试/构建/制品、部署三作业均 SUCCESS |
| 正式测试 | `3181 passing / 2 pending / 0 failures`，3183注册测试，无额外跳过 |
| 同 Run 完整归档 | `106711601` bytes；SHA256 `72c44215bc060a8d41c06e99bab76481070502cc999c1a9c7cd32a0a928e4e36` |
| 部署单 | `70689069`，hostGroup28833，一批一台 `Success / healthy` |
| 安装记录 | `/var/lib/cyf-web-flow/record.json`，版本1.0.6 / Run180 / 同一commit和归档摘要，`online_verified` |
| 线上完整性 | 原始Flow制品与主机下载一致；manifest全364文件及入口、主JS/CSS、JuyiHall懒加载JS/CSS，安装与公网HTTPS字节全部一致 |
| 正式页面 | 独立真实Chromium、正常登录；1440/390/320，无页面横向溢出，七动作20px SVG / 1.8px描边 / 38px点击区一致；工具栏同排、资料在＋后直接打开，语音在发送前、＋保留语音设置 |
| 配置恢复 | 前端恢复发布前的 develop CI-only 配置，readback相同；没有部署阶段，develop不自动部署 |
| 在线核验时间 | `2026-10-07T16:33:38.599022Z`（UTC；证据目录日期采用主机Asia/Shanghai日期） |

[机器可读发布记录](evidence/release-1.0.6-20261008/release.json)；[制品验真](evidence/release-1.0.6-20261008/artifact-verification.json)；[全文件线上核验](evidence/release-1.0.6-20261008/online-verification.json)；[浏览器检查](evidence/release-1.0.6-20261008/browser-verification.json)；[配置恢复](evidence/release-1.0.6-20261008/configuration-restored.json)。

## 发布顺序与控制面

1. 实时核对原正式版本1.0.5/Run177、远端develop7264539、前端与运维入口无活动Run。保存当前配置、正式manifest与前值。
2. 创建只增加版本号的发布提交，冻结完整SHA。固定候选Flow配置使用手动触发，构建和部署均验证精确SHA/1.0.6；更新并readback后推送develop和版本tag，单次启动Run180，没有重复CI构建。
3. 在云端执行原完整测试/构建与扫描，上传同Run制品。内嵌helper同步当前已安装适配器摘要 `fba8d49564946f381a02b7aee0bdfaeab48091be7ca5eb871f7dc4ac2eeeff6b`，内嵌upgrade调用采用五参数版本契约。发布不修改或降级主机helper。
4. 同Run VMDeploy下载归档，校验版本、源码及既有helper，先备份旧manifest全364文件与记录，再按五参数 `PIPELINE RUN COMMIT VERSION ARCHIVE_SHA256` 调用安装器。保留互斥等待、完整性核验、资产优先/入口最后发布与实际在线检查；无本机生产build或源码发布。
5. 用Flow原始下载再独立对账制品、主机归档、全部安装字节、公网364响应、部署单和正式页面。终态后确认无其它活动Run、当前仍是本候选配置，再恢复原CI-only配置并readback。
6. 写回本SDD与版本记录；仅独立SDD工作树更新Web gitlink，API gitlink不变。关闭自己的浏览器及删除临时登录profile，不操作其它进程、浏览器或原型服务。

## 可恢复措施

- 发布前完整备份：`/home/isp/baks/cyf-web-flow-before-180`，含1.0.5/Run177旧record与全部364文件；独立逐文件摘要和前值记录核验通过。没有执行回滚，也没有清理历史资产/备份。
- 若需恢复，先核对正式record仍是本Run并等待既有发布锁，通过既有Flow运维入口执行备份校验及资产优先/入口最后恢复，随后还原旧record并复验线上；不得直接调用旧Run安装器（其防倒序部署保护仍保留），不得本机重新构建或抢占其它发布。
- 候选/原始完整Flow YAML保存在受限控制目录 `/tmp/cyf-ui-release-1.0.6-20261008`，配置摘要和readback已落盘；后续发布仍需重新查当前配置并冻结新的版本/源码。

## 验收边界与剩余任务

- UI及版本发布已完成；`product_acceptance`仍为`NOT_COMPLETE`。
- R01独立图文root长期关联恢复、重复正文及完成态恢复不在本次UI范围，仍按多媒体SDD和现有业务待办推进。本次正式截图中既有重复正文没有被界面简化伪装为已修复。
- 页面检查只打开既有事项426与资料/设置菜单；没有发送、录音、调用Provider、创建事项、导入资料、扣费、验收或归档。本次不重新验证全部真实业务状态。
- 终态VM作业日志接口未返回正文；以部署单单机结果、实际主机记录、原始制品与全部线上字节独立证明部署，不伪称已读取日志。云端测试/构建日志可截断，测试总数以同Run报告验真。

Owner / ledger：`WEB-UI-RELEASE-1.0.6-20261008`；单Owner，无独立Reviewer或重复人工门禁。
