# 悬赏议事目标绑定修复（2026-10-03）

## 已证实的问题

Run161真实线上原417议事显示`@公孙胜`，输入新画鸟意图后点击“生成图片”无预览HTTP、无Provider调用。实际组件props显示`selectedAgent=null`；`enterBountyDiscussion`本来就将私人会话subject Agent置空，而F1、typed与成果catalog错误读取`conversationAgent`。同一会话的权威context GET200返回原task/唯一Agent，故不是缺少账号、图像服务器或Provider费用额度。

## 最小修复

Web `3024a832144cc01f2d34cb239bfd7e4474b4cc76` / tree `501a1de08f2735223401d3fc28c1d5fa0ef9c66f`：从既有任务会话scope及已通过roster权限筛选的唯一target选择目标；不是从当前浏览选中Agent或map数据推导。多目标不自动取首位；仅允许已属于participant的明确唯一target。撤权/解绑立即清空目标，target切换仍使旧上下文失效。服务器继续权威校验assignment、grant和consent，修复不授予Provider或其他用户资料权限。

没有改动voice实现、Composer、API、Client、账户或Flow配置。两处Hall测试mock-import映射仅新增真实helper导出，不用假helper绕过逻辑。

## 源码证据

旧Hall绑定3条新真实上下文回归失败；修正后6个定向文件58通过，含34 voice与真实ChatContext→Hall getter→F1 composable→预览HTTP adapter链。adapter是测试fixture，不是Provider。helper/路由测试ESLint通过；Hall188与component fixture7既有诊断不增加，voice0。

本地完整component-behavior导入缺生成的`public/juyiting/hall.tmx`，如实记录未执行，不伪造本地全suite通过；正式全套交Flow。没有本地生产构建。证据见`integration-evidence-20260928/bounty-interaction-target-source-20261003/`。

## 发布与产品边界

已非force推develop，先分页确认无自动/活动Run，再单次启动4403172/162，实际checkout3024a832已从正式日志核对。测试/制品/部署终态另附同Run证据，不凭目标SHA或本地绿灯声明上线。

历史“33/500”是voice预算证据，不作为本次图片预算。用户既有真实画鸟与gpt-image-cli统一授权仅用于所需平台新明确意图；不充值、换账户或运行独立付费探针，原417已放弃START绝不重放。当前仍无鸟图；完整AC01–AC22与FD01–FD12未完成。


## 14:40 发布补录（保留上述历史）

Run162最终2953通过/2pending/4失败：4个旧compiled-Hall测试loader缺少新增helper映射，并非voice或Provider问题。`14c2abbee6ca25dc7c0c4a2009de4a00de5deb71` / tree `a27bb8e5d0cd6211c75fc2d21435d395d5772ee1`仅补4处真实helper导入，受影响105条定向通过。

正式Run163实际checkout为14c2：2957通过/2pending/0失败、扫描与部署成功，部署单70601174的一台主机healthy。同Run制品SHA-256 `0fae6a42ab0a5a9c87bbf4c4baa380c603d4f95b842be862300c7fd3dff73919`，364个已安装文件和真实浏览器4个入口/HallJS/CSS/SW资源逐字节匹配。冻结远端`release/1.13.61`。voice e58644ae是祖先且未修改。证据见`integration-evidence-20260928/release-1.13.61/`。

新的完整需求418已通过浏览器创建、点公孙胜并自动进入议事。14:14真实生成了翠鸟PNG，已进入平台STAGED；结果commit404，尚不能在会话预览/下载。详见`task418-result-delivery-diagnosis-20261003.md`。这条事实取代“当前仍无鸟图”，但不意味着交付成功或34项已完成。
