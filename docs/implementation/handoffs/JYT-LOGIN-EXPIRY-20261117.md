# 登录失效后首页未进入重新认证

- 2026-11-17；Owner：jyt-login-expiry；授权：修复与测试，未授权本轮生产安装。
- 工作区：现有 web/develop；base/已安装 Web d2aa3610fb69d0d1894a7457e7e4e3e15f5f8652，tree 1324a16d6e7bdcddd0311a95ae8b46fd3d645530。远端同步状态未确认，不声称最新远端。
- 责任层：Web公共认证请求；getUserInfo复用useHttp现有401处理、single-flight和不重放策略。首页401停止初始化。API/Runtime/接口合同不变；403/网络故障不发起重新认证。
- 原型先行：既有 prototypes/juyiting/login-preview.js 增加 session-expired 状态，描述进入原登录流程；PC/移动共用，不新增生产页面。规格追加到既有 prototype-spec.md。
- 验收：有效身份正常初始化；本地token存在但/user/my为401（含空响应体）清token并发起一次认证；并发401不重放；403/网络失败不跳转；退出/身份切换后迟到响应不重新认证；首页401不启动业务加载。
- 不包含：公开首页强制登录、微信原生登录重构、诊断框架、其他BUG。微信真机验证尚未执行。

## 实现与验证结果

- 固定修复：web/develop `1b72c91f8625dfe0853c265bdfa9bc011fec3fae`，tree `4d17c9ec366750c22858f4387a262c896eb92d28`。生产文件仅api store与JuyiHall；无API/Runtime修改、无新增依赖。保留身份代际/取消和写回保护，不重放请求。
- 原型预览实际HTTP/Chromium通过：`index.html?loginState=session-expired#login`，390/1440宽均显示预期状态且无水平溢出；截图在证据目录。非生产登录端到端验收。
- 控制机轻量诊断30项认证+3项首页组件通过；首次命令cwd错误未执行测试，日志保留。
- 指定worker 203.32.84.239固定源码定向单元/组件回归：**202 PASS /0 FAIL /0 PENDING**，Node24.22.1，9个selector见worker-result-02.json，源归档/fixture归档SHA及依赖manifest/lock摘要匹配。非全量回归、非生产构建。
- 首轮失败保留：归档准备错误引用不存在tsconfig；改为实际jsconfig。正式01因导出缺少组件导入依赖public/juyiting/hall.tmx，在用例执行前失败（3.605秒），补充同一commit原字节fixture后02重新计时，没有改变产品或测试、没有删selector。
- ESLint：api.js无问题；JuyiHall既有94 error/131 warning，与基线逐条rule/message比较无新增；不声明全量lint通过，不顺手整理旧样式。
- 原始证据：`/home/isp/state/jyt-login-expiry-20261117/`；用例逐项结果test-results.json，源码/依赖worker-result-02.json与dependency-receipt.json，日志worker-tests-02.json.log。
- 远端develop查询20秒超时（exit124），尚未push，不声称远端已集成。未改根gitlink、未构建生产包、未安装；线上仍d2aa361。微信真机及部署后回归NOT_RUN。

## 部署授权与固定候选

用户随后明确“部署”：仅发布本修复Web，API/Runtime不构建、不重启。沿原local_web_build.py、RemoteBuild传输和cyf-web-flow-deploy受控安装；公共VITE配置固定原生产输入。为现有builder的*.test.js selector新增一个测试导入入口profile-session-release.test.js，生产源码仍与1b72c91相同，固定新提交后重新执行必要测试/构建。版本字段沿1.16.151，完整commit/tree与制品SHA区分，不以版本标签代替身份。

磁盘较紧：只删除本任务已结束单测的冗余源归档（原commit完整保留在Git，SHA/日志保留）。远端复用已结束03的Git对象只读作为新快照来源，独立干净sparse checkout，补传固定候选增量bundle；不更改旧checkout、不删缓存/其他任务目录。源码与工具准备单独计时；必要测试/构建/打包/等待/回传600秒同批。

## 2026-11-17 部署完成与线上定向回归

- 部署候选 `67bb9367c110e5faceb3a2a2d1c0db2ddaea7c19` / tree `9633a1924ca56c1772bf4cf966834ef2ba8492ee`；相对1b72c91仅增加release测试导入入口，生产代码不变。Web版本字段1.16.151，buildId `jyt-login-release-20261117-02-web`。
- release01：245 PASS/2既有pending；构建因稀疏快照漏带`miniprogram/juyiting/utils/app-config.json`失败，88.966秒（含回传），未安装。源准备最初Git bundle全SHA表达式被Git拒绝（尚无构建），改为固定HEAD排除已核对base；均保留原日志。
- release02：补齐同一提交miniprogram目录；生成的components.d.ts改动先保留patch后仅恢复本任务生成文件，产品/测试不变。克隆浅仓时--shared实际产生了独立pack，核对SHA/大小后将本任务重复pack替换为与原pack的硬链接（不依赖可被删除的alternates，不删除原目录/缓存），释放重复字节；详见git-pack-dedup.json。
- 同批必要测试/构建/打包/回传 **217.469秒**；245 PASS /0 FAIL /2既有pending（小程序冷启动/原生方向恢复合同用例）。原builder完整依赖核验、fresh测试、生产构建、包完整性与公开VITE配置核对均完成。包SHA `a7644c8139e52d8e1d5dc715941b556197805fd5c73a637a7aeac1916769b8d5`。
- 原Web受控安装 **32.868秒**，online_verified，265文件线上摘要核验；锁/前代CAS/备份恢复不变。前代备份 `/var/lib/cyf-web-flow/backups/55d16cd85279abd717a19aa81d37513276efdda36341688d7d44230863181352`。API记录和JAR前后摘要一致，API/Runtime未构建、未重启。健康200、JWKS200、未认证/user/my401通过。
- 线上浏览器发布前复现：390宽，/user/my实际401后仍在/juyiting、无登录表单、无授权导航；证据ui/before-results.json与截图。
- 发布后**6项定向UI PASS**：390宽/juyiting和1440宽/首页，两者保留但服务器无效token均实际收到/user/my401，进入登录页；既有SW初始化完成后的单文档各一次授权。匿名公开首页不强制登录、本地过期token直接进入登录、真实测试账号登录返回聚义厅、有效token刷新后身份接口200且不重新授权均通过。无新业务事项、无扣费操作；测试浏览器已关闭。
- 测试工具失败不覆写：第一次冷启动已成功进入登录页，但现有PWA controllerchange会reload，跨文档观察到两次授权导航，原“整个上下文只一次”断言失败；保留after-cold-start-assertion.log。随后先完成SW首装生命周期再测单文档single-flight，未改生产PWA。登录UI脚本最初选中了EasyUI转换前的输入框超时，保留login-locator-failure-01.log，改选真实可见textbox后真实登录成功。上述是工具断言/定位修正，不把首轮FAIL改成PASS。
- 小程序真机NOT_RUN，不把手机尺寸Chromium当真机；不是全局119项通过。Git远端同步仍未确认，本地develop干净。
- 回执：`/home/isp/state/jyt-login-expiry-20261117/release-02/attempt.json`、`install.json`；UI `ui/after-results.json`、`after-login-results.json`。冗余transport副本核验SHA后移除，正式包、测试、日志、manifest及原失败保留。
