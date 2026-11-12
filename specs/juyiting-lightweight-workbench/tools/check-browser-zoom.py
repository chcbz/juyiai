#!/usr/bin/env python3
"""Check actual Chromium tab zoom (100%/200%) on local Vue without live API or credentials.

A temporary MV3 extension calls chrome.tabs.setZoom(factor) and getZoom(); no CSS zoom,
page-scale emulation, or viewport-halving shortcut is used. Requires a fresh Vite
server for this worktree and the system Chromium/Playwright (not CI Chrome 133).
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

WEB_SHA = '8f47a1289bf501616ba234638192a5303d3155d7'
SIZES = [(320, 740), (390, 844), (844, 390), (1440, 900)]
# These are navigation surfaces, not assertions that the backend actions succeed.
PRIMARY_SURFACES = [
    ('tasks', '我的事项', '悬赏榜', '.bounty-panel'),
    ('agents', '点将册', '点将册', '.agent-panel'),
    ('treasure', '百宝箱', '百宝箱', '.personal-workspace'),
    ('library', '典籍阁', '典籍阁', '.library-panel'),
    ('messages', '消息通知', '消息', '.hall-overview.is-messages'),
    ('chat', '厅内议事', '厅内议事', '.chat-panel'),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='https://127.0.0.1:61360')
    parser.add_argument('--chromium', default=shutil.which('chromium'))
    parser.add_argument('--out', type=Path, help='Save safe, local-only geometry JSON')
    parser.add_argument('--screenshots', type=Path, help='Save local-only screenshots')
    parser.add_argument('--rendered-history', action='store_true', help='Feed 28 synthetic messages through the real Vue chat API path')
    parser.add_argument('--zoom-factor', type=int, choices=(1, 2), default=2, help='Actual Chromium tab zoom; native size only probes mobile widths')
    args = parser.parse_args()
    url = urlparse(args.url)
    if url.scheme not in ('https', 'http') or url.hostname not in ('localhost', '127.0.0.1', '::1') or url.username or url.password:
        parser.error('Only a loopback origin without credentials is allowed')
    if not args.chromium:
        parser.error('Specify --chromium PATH')
    web_dir = Path(__file__).resolve().parents[3] / 'web'
    actual_sha = subprocess.check_output(['git', '-C', str(web_dir), 'rev-parse', 'HEAD'], text=True).strip()
    if actual_sha != WEB_SHA:
        parser.error(f'Expected local web HEAD {WEB_SHA}; got {actual_sha}')
    origin = f'{url.scheme}://{url.netloc}'
    results = []
    with TemporaryDirectory(prefix='cyf-actual-zoom-') as temp, sync_playwright() as playwright:
        extension = Path(temp) / 'extension'
        extension.mkdir()
        (extension / 'manifest.json').write_text(json.dumps({
            'manifest_version': 3, 'name': 'CYF offline zoom measurement', 'version': '1.0',
            'permissions': ['tabs'], 'background': {'service_worker': 'worker.js'},
        }))
        (extension / 'worker.js').write_text('chrome.runtime.onInstalled.addListener(() => {});')
        for width, height in (SIZES if args.zoom_factor == 2 else SIZES[:2]):
            context = playwright.chromium.launch_persistent_context(
                str(Path(temp) / f'profile-{width}'), executable_path=args.chromium,
                headless=True, viewport={'width': width, 'height': height},
                device_scale_factor=1, ignore_https_errors=True,
                args=[f'--disable-extensions-except={extension}', f'--load-extension={extension}'],
            )
            try:
                context.add_init_script("if (location.origin === " + json.dumps(origin) +
                    " && window.top === window) { localStorage.setItem('api_token', JSON.stringify({data:'local-layout-only',expTime:Date.now()+120000})); " +
                    "if ('serviceWorker' in navigator) navigator.serviceWorker.register = () => Promise.reject(new Error('Local probe blocks app service workers')); }")

                intercepted = {'GET': 0, 'POST': 0, 'other': 0}
                web_sockets = {'localVite': 0, 'blocked': 0}
                fixture_requests = {'list': 0, 'content': 0, 'events': 0}

                def route_request(route):
                    target = route.request.url
                    parsed = urlparse(target)
                    path = parsed.path
                    if f'{parsed.scheme}://{parsed.netloc}' != origin:
                        route.abort()
                    elif route.request.resource_type == 'eventsource':
                        route.abort()  # No SSE simulation: the offline fixture measures only UI.
                    elif (route.request.resource_type in ('xhr', 'fetch') or
                            path.startswith(('/api/', '/chat/', '/agent/', '/user/', '/task/', '/oauth2/'))):
                        method = route.request.method
                        intercepted[method if method in intercepted else 'other'] += 1
                        if args.rendered_history and method == 'POST' and path == '/api/chat/conversation/list':
                            fixture_requests['list'] += 1
                            conversation = {'id': '19001', 'title': '本地虚构公议', 'conversationType': 'juyiting',
                                            'conversationScopeType': 'public', 'conversationScopeKey': 'public',
                                            'updateTime': 1700000000000}
                            route.fulfill(status=200, content_type='application/json', body=json.dumps({'data': [conversation]}))
                        elif args.rendered_history and method == 'GET' and path == '/api/chat/conversation/content':
                            assert parsed.query == 'id=19001', 'Unexpected fixture conversation ID'
                            fixture_requests['content'] += 1
                            mock_messages = [
                                {'id': str(i + 1), 'senderType': 'agent' if i % 2 else 'user',
                                 'messageType': 'USER' if i % 2 == 0 else 'AGENT',
                                 'senderName': '虚构好汉' if i % 2 else '你',
                                 'createTime': 1700000000000 + i * 1000,
                                 'content': (f'**本地样例 {i + 1}**：仅用于测试真正 Vue 消息渲染和布局，非真实账号会话。\n\n'
                                             '- 一段较长的 Markdown 文本用于测试换行和气泡宽度。\n'
                                             '- 另一段列表内容。' +
                                             ('\n\n[示例锚点](#local-fixture)' if i == 0 else '') +
                                             ('\n\n```text\n' + '0123456789abcdef ' * 12 + '\n```' if i == 1 else ''))}
                                for i in range(28)
                            ]
                            route.fulfill(status=200, content_type='application/json', body=json.dumps({'data': mock_messages}))
                        elif args.rendered_history and method == 'GET' and path == '/api/chat/conversation/events':
                            fixture_requests['events'] += 1
                            route.fulfill(status=403, content_type='text/plain', body='Local fixture does not simulate SSE')
                        else:
                            route.fulfill(status=200, content_type='application/json', body='{"code":200,"data":[],"items":[]}')
                    elif target.startswith(origin + '/'):
                        route.continue_()
                    else:
                        route.abort()

                context.route('**/*', route_request)
                # HTTP routing does not isolate WebSocket handshakes. Let only this dev
                # server's HMR root connect; prevent an app socket reaching any service.
                def route_web_socket(ws):
                    target = urlparse(ws.url)
                    if (target.scheme == ('wss' if url.scheme == 'https' else 'ws') and
                            target.hostname == url.hostname and target.port == url.port and
                            target.path == '/'):
                        web_sockets['localVite'] += 1
                        ws.connect_to_server()
                    else:
                        web_sockets['blocked'] += 1
                        ws.close()

                context.route_web_socket('**/*', route_web_socket)
                page = context.new_page()
                page.goto(origin + '/juyiting', wait_until='domcontentloaded', timeout=30000)
                assert page.evaluate('''() => !!document.querySelector('script[src*="/@vite/client"]') &&
                  (!('serviceWorker' in navigator) || navigator.serviceWorker.controller === null)'''), 'Only fresh Vite dev pages are permitted'
                page.locator('.onboarding-dialog .skip-button').click(timeout=25000)
                page.locator('.onboarding-overlay').wait_for(state='hidden')
                worker = context.service_workers[0] if context.service_workers else context.wait_for_event('serviceworker', timeout=10000)
                tab_zoom = worker.evaluate('''async ([origin, factor]) => {
                  const tabs = await chrome.tabs.query({});
                  const tab = tabs.find(t => t.url?.startsWith(origin + '/juyiting'));
                  if (!tab) throw new Error('Local workbench tab not found');
                  await chrome.tabs.setZoom(tab.id, factor);
                  return chrome.tabs.getZoom(tab.id);
                }''', [origin, args.zoom_factor])
                page.wait_for_function('''([w,h,factor]) => devicePixelRatio === factor &&
                    Math.abs(innerWidth * factor - w) <= 1 &&
                    Math.abs(innerHeight * factor - h) <= 1''', arg=[width, height, args.zoom_factor], timeout=12000)
                viewport = page.evaluate('''() => ({ devicePixelRatio, innerWidth, innerHeight, outerWidth, outerHeight,
                    visualViewportScale: visualViewport.scale, pageScrollWidth:document.documentElement.scrollWidth,
                    userAgent:navigator.userAgent })''')
                assert tab_zoom == args.zoom_factor and viewport['visualViewportScale'] == 1, viewport
                assert viewport['pageScrollWidth'] <= viewport['innerWidth'], viewport
                trigger = page.locator('.workbench-mobile-more')
                trigger.click()
                menu = page.locator('.workbench-more-menu')
                menu.wait_for(state='visible')
                last = menu.locator('button').last
                last.scroll_into_view_if_needed()
                last.focus()
                assert last.evaluate('(e) => document.activeElement === e')
                nav_menu = page.evaluate('''() => {
                  const box = s => {const r=document.querySelector(s).getBoundingClientRect();return {left:r.left,right:r.right,top:r.top,bottom:r.bottom,height:r.height}};
                  const tabs=[...document.querySelectorAll('.workbench-mobile-nav button')].map(e=>({
                    label:e.getAttribute('aria-label'), display:getComputedStyle(e.querySelector('span')).display,
                    width:e.getBoundingClientRect().width }));
                  return {header:box('.hall-app-header'),menu:box('.workbench-more-menu'),nav:box('.workbench-mobile-nav'),tabs};
                }''')
                assert nav_menu['header']['left'] >= -.5 and nav_menu['header']['right'] <= viewport['innerWidth'] + .5, nav_menu
                assert nav_menu['menu']['left'] >= -.5 and nav_menu['menu']['right'] <= viewport['innerWidth'] + .5, nav_menu
                assert nav_menu['menu']['bottom'] <= nav_menu['nav']['top'] + .5, nav_menu
                assert [t['label'] for t in nav_menu['tabs']] == ['办事概览', '我的事项', '厅内议事', '典籍阁'], nav_menu
                assert all(t['width'] > 0 for t in nav_menu['tabs']), nav_menu
                if viewport['innerWidth'] <= 240:
                    assert [t['display'] for t in nav_menu['tabs'][:3]] == ['none'] * 3, nav_menu
                assert nav_menu['tabs'][-1]['display'] != 'none', nav_menu
                menu.get_by_role('button', name='厅内议事').click()
                dialog = page.get_by_role('dialog', name='厅内议事')
                assert dialog.count() == 1
                title_id = dialog.get_attribute('aria-labelledby')
                assert title_id and page.evaluate('id => document.getElementById(id)?.textContent?.includes("厅内议事")', title_id)
                # The panel enters with translateY(10px); wait for animation before checking overlap.
                page.wait_for_function('''() => {const a=document.querySelector('.panel-overlay.is-workbench-panel');
                   const b=a?.querySelector('.floating-panel');return b && Math.abs(a.getBoundingClientRect().top-b.getBoundingClientRect().top)<.5}''')
                chat = page.evaluate('''() => {
                  const box=s=>{const r=document.querySelector(s).getBoundingClientRect();return {top:r.top,bottom:r.bottom,height:r.height}};
                  const p=document.querySelector('.panel-overlay.is-workbench-panel > .floating-panel');
                  return {messages:box('.hall-messages'),composer:box('.hall-chat-composer'),overlay:box('.panel-overlay.is-workbench-panel'),
                    windowClientHeight:p.clientHeight,windowScrollHeight:p.scrollHeight,nav:box('.workbench-mobile-nav'),
                    pageScrollWidth:document.documentElement.scrollWidth};
                }''')
                assert chat['pageScrollWidth'] <= viewport['innerWidth'], chat
                if viewport['innerHeight'] <= 260:
                    assert chat['windowScrollHeight'] > chat['windowClientHeight'], chat
                    page.locator('.composer-send').scroll_into_view_if_needed()
                    send_box = page.locator('.composer-send').bounding_box()
                    assert send_box and chat['overlay']['top'] - .5 <= send_box['y'] and send_box['y'] + send_box['height'] <= chat['nav']['top'] + .5, chat
                    chat['windowScrollAfter'] = page.locator('.floating-panel').evaluate('(e) => e.scrollTop')
                    assert chat['windowScrollAfter'] > 0, chat
                else:
                    assert chat['composer']['bottom'] <= chat['nav']['top'] + .5, chat
                    assert chat['messages']['height'] >= 40, chat
                    if viewport['innerWidth'] <= 240:
                        action = page.locator('.chat-panel .toolbar-actions button').last
                        action.scroll_into_view_if_needed()
                        action.focus()
                        assert action.evaluate('(e) => document.activeElement === e')
                        chat['toolbarScrollAfter'] = page.locator('.chat-panel .panel-toolbar').evaluate('(e) => e.scrollLeft')
                        assert chat['toolbarScrollAfter'] > 0, chat
                if args.rendered_history:
                    page.wait_for_function('''() => document.querySelectorAll('.hall-messages .hall-message').length === 28''', timeout=12000)
                if args.screenshots and width in ((320, 390, 844) if args.rendered_history else (320, 844)):
                    args.screenshots.mkdir(parents=True, exist_ok=True)
                    filename = (f'rendered-chat-zoom{args.zoom_factor}' if args.rendered_history else 'actual-zoom')
                    page.screenshot(path=str(args.screenshots / f'{filename}-{width}x{height}.png'))
                long_chat = page.evaluate('''rendered => {
                    const messages=document.querySelector('.hall-messages');
                    if (!rendered) {
                      for (let i=0;i<28;i++) { const item=document.createElement('p');
                        item.textContent='本地合成消息 '+(i+1)+'：仅用于浏览器缩放时测试长对话滚动，不来自任何用户或服务。';
                        messages.appendChild(item); }
                    }
                    messages.scrollTop=messages.scrollHeight;
                    return {clientHeight:messages.clientHeight,scrollHeight:messages.scrollHeight,scrollTop:messages.scrollTop,
                      renderedMessages:messages.querySelectorAll('.hall-message').length,
                      markdownStrong:messages.querySelectorAll('.message-content strong').length,
                      markdownLists:messages.querySelectorAll('.message-content ul').length,
                      markdownCodeBlocks:messages.querySelectorAll('.message-content pre').length,
                      maxPreScrollExcess:Math.max(0,...[...messages.querySelectorAll('.message-content pre')].map(pre=>pre.scrollWidth-pre.clientWidth)),
                      sampleLink:messages.querySelector('.message-content a')?.getAttribute('href') || null,
                      renderedStyle:rendered ? (() => {
                        const bubble=messages.querySelector('.hall-message');
                        const content=bubble.querySelector('.message-content');
                        const link=messages.querySelector('.message-content a');
                        const pre=messages.querySelector('.message-content pre');
                        const fields=e=>{const c=getComputedStyle(e),r=e.getBoundingClientRect();return {
                          width:r.width,height:r.height,fontFamily:c.fontFamily,fontSize:c.fontSize,fontWeight:c.fontWeight,
                          lineHeight:c.lineHeight,color:c.color,backgroundColor:c.backgroundColor,padding:c.padding,
                          textDecorationLine:c.textDecorationLine,textUnderlineOffset:c.textUnderlineOffset,
                          borderRadius:c.borderRadius,overflowX:c.overflowX};};
                        return {bubble:fields(bubble),content:fields(content),link:{...fields(link),
                          href:link.getAttribute('href'),target:link.getAttribute('target'),rel:link.getAttribute('rel')},
                          pre:fields(pre)};
                      })() : null,
                      renderedBounds:rendered ? (() => {
                        const box=messages.getBoundingClientRect();
                        const padding=getComputedStyle(messages);
                        const left=box.left+parseFloat(padding.paddingLeft), right=box.right-parseFloat(padding.paddingRight);
                        const bubbles=[...messages.querySelectorAll('.hall-message')].map(e=>e.getBoundingClientRect());
                        return {areaLeft:box.left,areaRight:box.right,contentLeft:left,contentRight:right,
                          scrollWidth:messages.scrollWidth,clientWidth:messages.clientWidth,scrollLeft:messages.scrollLeft,
                          minBubbleLeft:Math.min(...bubbles.map(r=>r.left)),maxBubbleRight:Math.max(...bubbles.map(r=>r.right)),
                          clippedLeft:bubbles.filter(r=>r.left<left-.5).length,
                          clippedRight:bubbles.filter(r=>r.right>right+.5).length};
                      })() : null,
                      pageScrollWidth:document.documentElement.scrollWidth};
                }''', args.rendered_history)
                if args.rendered_history:
                    assert long_chat['renderedMessages'] == 28 and long_chat['markdownStrong'] >= 28, long_chat
                    assert long_chat['markdownLists'] >= 28 and long_chat['markdownCodeBlocks'] >= 1, long_chat
                    assert long_chat['sampleLink'] == '#local-fixture' and long_chat['maxPreScrollExcess'] > 0, long_chat
                    style = long_chat['renderedStyle']
                    assert style['content']['fontSize'] == '15px' and style['content']['lineHeight'] == '23.25px', style
                    assert style['link']['color'] == 'rgb(127, 74, 34)' and style['link']['textDecorationLine'] == 'underline', style
                    assert style['link']['textUnderlineOffset'] == '2px' and style['link']['target'] is None and style['link']['rel'] is None, style
                    assert style['pre']['overflowX'] == 'auto', style
                    assert fixture_requests['list'] >= 1 and fixture_requests['content'] >= 1 and fixture_requests['events'] >= 1, fixture_requests
                assert long_chat['scrollHeight'] > long_chat['clientHeight'] and long_chat['scrollTop'] > 0, long_chat
                assert long_chat['pageScrollWidth'] <= viewport['innerWidth'], long_chat
                if args.rendered_history:
                    bounds = long_chat['renderedBounds']
                    assert bounds['clippedLeft'] == 0 and bounds['clippedRight'] == 0, bounds
                    assert bounds['scrollWidth'] == bounds['clientWidth'] and bounds['scrollLeft'] == 0, bounds
                if viewport['innerHeight'] > 260:
                    composer_bottom = page.locator('.hall-chat-composer').bounding_box()
                    assert composer_bottom and composer_bottom['y'] + composer_bottom['height'] <= chat['nav']['top'] + .5, long_chat
                surfaces = []
                for panel, label, title, content_selector in PRIMARY_SURFACES:
                    trigger.click()
                    menu.wait_for(state='visible')
                    menu.get_by_role('button', name=label, exact=True).click()
                    dialog = page.get_by_role('dialog', name=title, exact=True)
                    dialog.wait_for(state='visible')
                    dialog.locator(content_selector).wait_for(state='visible')
                    page.wait_for_function('''() => {
                        const panel=document.querySelector('.panel-overlay.is-workbench-panel > .floating-panel');
                        const overlay=panel?.parentElement;
                        return panel && Math.abs(overlay.getBoundingClientRect().top-panel.getBoundingClientRect().top)<.5;
                    }''')
                    surface = page.evaluate('''([panel, label, selector]) => {
                        const dialog=document.querySelector('.panel-overlay.is-workbench-panel .floating-panel');
                        const content=dialog.querySelector(selector);
                        const rect=dialog.getBoundingClientRect();
                        const body=content.getBoundingClientRect();
                        const nav=document.querySelector('.workbench-mobile-nav').getBoundingClientRect();
                        return {panel, label, title:dialog.querySelector('.panel-title > span')?.textContent,
                            ariaModal:dialog.getAttribute('aria-modal'),
                            ariaLabelledby:dialog.getAttribute('aria-labelledby'),
                            contentVisible:getComputedStyle(content).display!=='none' && body.width>0 && body.height>0,
                            dialog:{left:rect.left,right:rect.right,top:rect.top,bottom:rect.bottom},
                            navTop:nav.top, pageScrollWidth:document.documentElement.scrollWidth,
                            menuExpanded:document.querySelector('.workbench-mobile-more').getAttribute('aria-expanded')};
                    }''', [panel, label, content_selector])
                    assert surface['title'] == title and surface['ariaModal'] == 'false' and surface['ariaLabelledby'], surface
                    assert surface['contentVisible'] and surface['menuExpanded'] == 'false', surface
                    assert surface['dialog']['left'] >= -.5 and surface['dialog']['right'] <= viewport['innerWidth']+.5, surface
                    assert surface['dialog']['bottom'] <= surface['navTop']+.5, surface
                    assert surface['pageScrollWidth'] <= viewport['innerWidth'], surface
                    if panel == 'library':
                        dialog.get_by_role('tab', name='案卷检索').click()
                        assert dialog.get_by_role('tab', name='案卷检索').get_attribute('aria-selected') == 'true'
                        assert dialog.get_by_role('tab', name='典籍阅读').get_attribute('aria-selected') == 'false'
                        surface['archiveSearchTabReachable'] = True
                    surfaces.append(surface)
                trigger.click()
                menu.wait_for(state='visible')
                menu.get_by_role('button', name='办事概览', exact=True).click()
                page.locator('.panel-overlay.is-workbench-panel').wait_for(state='hidden')
                overview = page.evaluate('''() => ({pageScrollWidth:document.documentElement.scrollWidth,
                    visible:!document.querySelector('.panel-overlay.is-workbench-panel') &&
                        !!document.querySelector('.hall-overview') &&
                        getComputedStyle(document.querySelector('.hall-overview')).display!=='none',
                    navCurrent:[...document.querySelectorAll('.workbench-mobile-nav button[aria-current="page"]')]
                        .map(button=>button.getAttribute('aria-label'))})''')
                assert overview['visible'] and overview['pageScrollWidth'] <= viewport['innerWidth'], overview
                assert overview['navCurrent'] == ['办事概览'], overview
                results.append({'baseViewportPixels': f'{width}x{height}', 'tabZoom': tab_zoom,
                                'viewport': viewport, 'navigation': nav_menu, 'chat': chat, 'syntheticLongChat': long_chat,
                                'primarySurfaces': surfaces, 'returnToOverview': overview,
                                'interceptedApiRequestsByMethod': intercepted, 'webSockets': web_sockets,
                                **({'renderedHistoryFixtureRequests': fixture_requests} if args.rendered_history else {})})
                print(f'PASS tab zoom {args.zoom_factor * 100}% {width}x{height} -> {viewport["innerWidth"]}x{viewport["innerHeight"]}')
            finally:
                context.close()
    if args.out:
        args.out.write_text(json.dumps({'webSha': actual_sha, 'browser': 'system Chromium (not project Chrome 133); see results[*].viewport.userAgent for runtime version',
                                        'method': f'chrome.tabs.setZoom({args.zoom_factor}) and getZoom() using isolated temporary extension',
                                        'limitations': ('local fake token, synthetic Vue-rendered history, no real keyboard/safe area or service'
                                                        if args.rendered_history else 'local fake token, empty intercepted API, no real keyboard/safe area or service'),
                                        **({'renderedHistory': True} if args.rendered_history else {}),
                                        'results': results}, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
