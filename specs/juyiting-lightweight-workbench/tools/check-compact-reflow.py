#!/usr/bin/env python3
"""Local Vue chat/menu regression at 200%-equivalent CSS viewports.

Run `cd web && npm run dev -- --host 127.0.0.1 --port 61360 --strictPort`
from the worktree, then run this file from the root. These half-sized CSS viewports
at DPR2 are *not* proof of actual Chrome/browser zoom, a real soft keyboard,
a real account, or the fixed CI Chrome 133 gate.
"""
import argparse
import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

SIZES = [(160, 370), (195, 422), (422, 195), (720, 450)]
WEB_SHA = "8f47a1289bf501616ba234638192a5303d3155d7"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='https://127.0.0.1:61360')
    parser.add_argument('--chromium', default=shutil.which('chromium'))
    parser.add_argument('--out', type=Path, help='Optional JSON output without credentials')
    parser.add_argument('--screenshots', type=Path, help='Optional directory for 160×370 and 422×195 screenshots')
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if parsed.scheme not in ('https', 'http') or parsed.hostname not in ('localhost', '127.0.0.1', '::1') or parsed.username or parsed.password:
        parser.error('Only a loopback URL without credentials is allowed')
    if not args.chromium:
        parser.error('Specify --chromium PATH for a locally installed Chromium')
    web_path = Path(__file__).resolve().parents[3] / "web"
    actual_sha = subprocess.check_output(["git", "-C", str(web_path), "rev-parse", "HEAD"], text=True).strip()
    if actual_sha != WEB_SHA:
        parser.error(f"Expected candidate {WEB_SHA}, got {actual_sha}")
    origin = f'{parsed.scheme}://{parsed.netloc}'
    output = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium, headless=True)
        version = browser.version
        try:
            for width, height in SIZES:
                context = browser.new_context(viewport={'width': width, 'height': height}, device_scale_factor=2, ignore_https_errors=True, service_workers='block')
                context.add_init_script("if (location.origin === " + json.dumps(origin) + " && window.top === window) localStorage.setItem('api_token', JSON.stringify({data:'reflow-layout-fixture', expTime:Date.now()+120000}))")

                def route_request(route):
                    url = urlparse(route.request.url)
                    if f'{url.scheme}://{url.netloc}' != origin:
                        route.abort()
                    elif (route.request.resource_type in ('xhr', 'fetch') or url.path.startswith(('/api/', '/chat/', '/agent/', '/user/', '/task/', '/oauth2/'))):
                        route.fulfill(status=200, content_type='application/json', body='{"code":200,"data":[],"items":[]}')
                    elif f'{url.scheme}://{url.netloc}' == origin:
                        route.continue_()
                    else:
                        route.abort()

                context.route('**/*', route_request)
                page = context.new_page()
                try:
                    page.goto(origin + '/juyiting', wait_until='domcontentloaded', timeout=30000)
                    page.locator('.onboarding-dialog .skip-button').click(timeout=25000)
                    page.locator('.onboarding-overlay').wait_for(state='hidden')
                    trigger = page.locator('.workbench-mobile-more')
                    trigger.click()
                    menu = page.locator('.workbench-more-menu')
                    menu.wait_for(state='visible')
                    last_menu_item = menu.locator('button').last
                    last_menu_item.scroll_into_view_if_needed()
                    last_menu_item.focus()
                    assert last_menu_item.evaluate('(e) => document.activeElement === e')
                    initial = page.evaluate('''() => {
                      const box = s => document.querySelector(s).getBoundingClientRect();
                      const header = box('.hall-app-header'), nav = box('.workbench-mobile-nav'), menu = box('.workbench-more-menu');
                      return { headerLeft:header.left, headerRight:header.right, navLeft:nav.left, navRight:nav.right,
                        navTop:nav.top, menuLeft:menu.left, menuRight:menu.right, menuBottom:menu.bottom,
                        pageScrollWidth:document.documentElement.scrollWidth,
                        tabs:[...document.querySelectorAll('.workbench-mobile-nav button')].map(x => { const span=x.querySelector('span'); const rect=x.getBoundingClientRect(); return { label:x.getAttribute('aria-label'), text:x.textContent.trim(), labelDisplay:getComputedStyle(span).display, width:rect.width, height:rect.height }; }) };
                    }''')
                    assert initial['headerLeft'] >= -0.5 and initial['headerRight'] <= width + 0.5, initial
                    assert initial['navLeft'] >= -0.5 and initial['navRight'] <= width + 0.5, initial
                    assert initial['menuLeft'] >= -0.5 and initial['menuRight'] <= width + 0.5 and initial['menuBottom'] <= initial['navTop'] + 0.5, initial
                    assert initial['pageScrollWidth'] <= width, initial
                    assert len(initial['tabs']) == 4 and all(x['label'] == x['text'] for x in initial['tabs']), initial
                    assert initial['tabs'][-1]['label'] == '典籍阁', initial
                    assert all(x['width'] > 0 and x['height'] > 0 for x in initial['tabs']), initial
                    if width <= 240:
                        assert all(x['labelDisplay'] == 'none' for x in initial['tabs'][:3]), initial
                    else:
                        assert all(x['labelDisplay'] != 'none' for x in initial['tabs'][:3]), initial
                    assert initial['tabs'][-1]['labelDisplay'] != 'none', initial
                    menu.get_by_role('button', name='厅内议事').click()
                    dialog = page.get_by_role('dialog', name='厅内议事')
                    assert dialog.count() == 1
                    title_id = dialog.get_attribute('aria-labelledby')
                    assert title_id and page.evaluate('id => document.getElementById(id)?.textContent?.includes("厅内议事")', title_id)
                    page.wait_for_function('''() => { const overlay = document.querySelector('.panel-overlay.is-workbench-panel');
                      const panel = overlay?.querySelector('.floating-panel'); return panel && Math.abs(panel.getBoundingClientRect().top - overlay.getBoundingClientRect().top) <= .5; }''', timeout=8000)
                    measurements = page.evaluate('''() => {
                      const rect = s => { const e=document.querySelector(s); const r=e.getBoundingClientRect(); return {left:r.left, right:r.right, top:r.top, bottom:r.bottom, height:r.height}; };
                      const window = document.querySelector('.panel-overlay.is-workbench-panel > .floating-panel');
                      const toolbar = document.querySelector('.chat-panel .panel-toolbar');
                      return {messages:rect('.hall-messages'), composer:rect('.hall-chat-composer'), nav:rect('.workbench-mobile-nav'),
                        windowClientHeight:window.clientHeight, windowScrollHeight:window.scrollHeight,
                        toolbarClientWidth:toolbar.clientWidth, toolbarScrollWidth:toolbar.scrollWidth,
                        overlay:rect('.panel-overlay.is-workbench-panel'),
                        pageScrollWidth:document.documentElement.scrollWidth};
                    }''')
                    assert measurements['pageScrollWidth'] <= width, measurements
                    if height <= 260:
                        assert measurements['windowScrollHeight'] > measurements['windowClientHeight'], measurements
                        page.locator('.composer-textarea').scroll_into_view_if_needed()
                        page.locator('.composer-send').scroll_into_view_if_needed()
                        button = page.locator('.composer-send').bounding_box()
                        assert button and button['y'] >= measurements['overlay']['top'] - 0.5 and button['y'] + button['height'] <= measurements['nav']['top'] + 0.5, (measurements, button)
                        measurements['windowScrollAfter'] = page.locator('.floating-panel').evaluate('(e) => e.scrollTop')
                        assert measurements['windowScrollAfter'] > 0, measurements
                    else:
                        assert measurements['composer']['bottom'] <= measurements['nav']['top'] + 0.5, measurements
                        assert measurements['messages']['height'] >= 40, measurements
                        if width <= 240:
                            assert measurements['toolbarScrollWidth'] > measurements['toolbarClientWidth'], measurements
                            last_action = page.locator('.chat-panel .toolbar-actions button').last
                            last_action.scroll_into_view_if_needed()
                            toolbar_scroll = page.locator('.chat-panel .panel-toolbar').evaluate('(e) => e.scrollLeft')
                            assert toolbar_scroll > 0, toolbar_scroll
                            last_action.focus()
                            assert last_action.evaluate('(e) => document.activeElement === e')
                            measurements['toolbarScrollAfter'] = toolbar_scroll
                            action_box = last_action.bounding_box()
                            toolbar_box = page.locator('.chat-panel .panel-toolbar').bounding_box()
                            assert action_box and toolbar_box and action_box['x'] >= toolbar_box['x'] - 1 and action_box['x'] + action_box['width'] <= toolbar_box['x'] + toolbar_box['width'] + 1
                    if args.screenshots and (width, height) in ((160, 370), (422, 195)):
                        args.screenshots.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(args.screenshots / f'compact-reflow-{width}x{height}.png'))
                    output.append({'viewportCss': f'{width}x{height}', 'navAndMenu': initial, 'chat': measurements})
                    print(f'PASS {width}x{height}: menu/nav within bounds; composer reachable, no horizontal page overflow')
                finally:
                    context.close()
        finally:
            browser.close()
    if args.out:
        args.out.write_text(json.dumps({'source': 'Local Vue, half CSS viewport at DPR2; not actual browser zoom, real service or pinned CI browser', 'webSha': actual_sha, 'chromiumVersion': version, 'results': output}, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
