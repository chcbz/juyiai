#!/usr/bin/env python3
"""Check the real Vue mobile menu geometry, not a static mock or service E2E.

Start the candidate Vite server, then run:
  python specs/juyiting-lightweight-workbench/tools/check-mobile-menu.py \
    --url https://127.0.0.1:61360 --out /tmp/cyf-menu-candidate.json \
    --screenshots specs/juyiting-lightweight-workbench/evidence

Requires Python playwright and a locally installed Chromium. Never sends credentials,
API traffic, or requests to any origin other than the supplied loopback Vite server.
"""
import argparse
import json
import shutil
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

VIEWPORTS = [(320, 320), (320, 740), (390, 844), (640, 390), (720, 450), (760, 390)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='https://127.0.0.1:61360')
    parser.add_argument('--out', type=Path, help='Optional fixture JSON output (no token or credentials)')
    parser.add_argument('--screenshots', type=Path, help='Optional directory for 320×320 and 640×390 current-SHA screenshots')
    parser.add_argument('--chromium', default=shutil.which('chromium'), help='Local Chromium executable; not a pinned CI browser')
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if parsed.scheme not in ('http', 'https') or parsed.hostname not in ('localhost', '127.0.0.1', '::1') or parsed.username or parsed.password:
        parser.error('Only a loopback URL without credentials is allowed')
    if not args.chromium:
        parser.error('No local Chromium found; pass --chromium PATH')
    origin = f'{parsed.scheme}://{parsed.netloc}'
    results = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium, headless=True)
        chromium_version = browser.version
        try:
            for width, height in VIEWPORTS:
                context = browser.new_context(viewport={'width': width, 'height': height}, ignore_https_errors=True)
                # Deliberately not a real session; API requests are intercepted before network.
                context.add_init_script("if (location.origin === " + json.dumps(origin) + " && window.top === window) localStorage.setItem('api_token', JSON.stringify({data:'menu-layout-fixture', expTime: Date.now() + 120000}))")
                external = []

                def route_request(route):
                    url = urlparse(route.request.url)
                    if route.request.url.startswith(origin + '/api/') or route.request.url == origin + '/api':
                        route.fulfill(status=200, content_type='application/json', body=json.dumps({'code': 200, 'data': [], 'items': []}))
                    elif f'{url.scheme}://{url.netloc}' == origin:
                        route.continue_()
                    else:
                        external.append(url.hostname or 'unknown')
                        route.abort()

                context.route('**/*', route_request)
                page = context.new_page()
                try:
                    page.goto(origin + '/juyiting', wait_until='domcontentloaded', timeout=30000)
                    # The guided overlay can appear asynchronously after the header.
                    onboarding = page.locator('.onboarding-dialog .skip-button')
                    onboarding.wait_for(state='visible', timeout=12000)
                    onboarding.click()
                    page.locator('.onboarding-overlay').wait_for(state='hidden')
                    trigger = page.locator('.workbench-mobile-more')
                    trigger.wait_for(state='visible', timeout=25000)
                    trigger.click()
                    menu = page.locator('.workbench-more-menu')
                    menu.wait_for(state='visible')
                    last = menu.locator('button').last
                    last.scroll_into_view_if_needed()
                    last.focus()
                    result = page.evaluate('''() => {
                      const menu = document.querySelector('.workbench-more-menu');
                      const header = document.querySelector('.hall-app-header');
                      const nav = document.querySelector('.workbench-mobile-nav');
                      const rect = menu.getBoundingClientRect();
                      const containingBlock = menu.closest('.juyi-page');
                      const parentRect = containingBlock.getBoundingClientRect();
                      return {
                        viewport: `${innerWidth}x${innerHeight}`,
                        left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom,
                        width: rect.width, height: rect.height,
                        headerBottom: header.getBoundingClientRect().bottom,
                        navTop: nav.getBoundingClientRect().top,
                        scrollHeight: menu.scrollHeight, clientHeight: menu.clientHeight,
                        overflowY: getComputedStyle(menu).overflowY,
                        scrollWidth: document.documentElement.scrollWidth,
                        buttons: menu.querySelectorAll('button').length,
                        lastItemFocusableAfterScroll: document.activeElement === menu.querySelector('button:last-child'),
                        ancestorPosition: getComputedStyle(containingBlock).position,
                        offsetParentIsHall: menu.offsetParent === containingBlock,
                        hallWidth: parentRect.width,
                        menuBoxSizing: getComputedStyle(menu).boxSizing
                      };
                    }''')
                    assert result['buttons'] == 10, result
                    assert result['lastItemFocusableAfterScroll'], result
                    assert result['ancestorPosition'] == 'relative' and result['offsetParentIsHall'], result
                    assert result['menuBoxSizing'] == 'border-box', result
                    assert abs(result['width'] - min(330, result['hallWidth'] - 30)) <= 0.5, result
                    assert result['overflowY'] == 'auto', result
                    assert result['left'] >= -0.5 and result['right'] <= width + 0.5, result
                    assert result['top'] >= result['headerBottom'] - 0.5, result
                    assert result['bottom'] <= result['navTop'] + 0.5, result
                    assert result['scrollWidth'] <= width, result
                    if width == height == 320:
                        assert result['scrollHeight'] > result['clientHeight'], result
                    results.append(result)
                    if args.screenshots and (width, height) in ((320, 320), (640, 390)):
                        args.screenshots.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(args.screenshots / f'menu-candidate-{width}x{height}.png'))
                    print(f"PASS {width}x{height}: menu {result['left']:.0f}..{result['right']:.0f}, "
                          f"{result['top']:.0f}..{result['bottom']:.0f}, focused last item")
                finally:
                    context.close()
        finally:
            browser.close()
    if args.out:
        args.out.write_text(json.dumps({'source': 'Local Vite Vue; synthetic token/empty API; system Chromium, not fixed CI Chrome or service acceptance', 'chromiumVersion': chromium_version, 'results': results}, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
