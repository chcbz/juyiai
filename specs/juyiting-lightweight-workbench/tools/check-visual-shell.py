#!/usr/bin/env python3
"""Offline, read-only workbench shell parity probe (not a service acceptance test).

Start the candidate Vite server on a loopback address, then pass --url. All /api
requests receive empty fixtures and all non-loopback requests are blocked. The
fixture token is deliberately invalid outside this isolated browser context.
"""
import argparse
import json
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

SURFACES = ('overview', 'tasks', 'chat', 'agents', 'treasure', 'library', 'messages')
VIEWPORTS = ((320, 740), (390, 844), (844, 390), (1440, 900))
ORIGIN_DEFAULT = 'https://127.0.0.1:61360'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default=ORIGIN_DEFAULT)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--screenshots', type=Path)
    args = parser.parse_args()
    parsed = urlparse(args.url)
    if parsed.scheme not in ('http', 'https') or parsed.hostname not in ('localhost', '127.0.0.1', '::1') or parsed.username or parsed.password or parsed.path not in ('', '/'):
        parser.error('Only a credential-free loopback origin is allowed')
    origin = f'{parsed.scheme}://{parsed.netloc}'
    report = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path='/usr/bin/chromium', headless=True)
        try:
            for width, height in VIEWPORTS:
                context = browser.new_context(viewport={'width': width, 'height': height}, ignore_https_errors=True)
                context.add_init_script('if (location.origin === ' + json.dumps(origin) + " && window.top === window) localStorage.setItem('api_token', JSON.stringify({data:'visual-shell-fixture',expTime:Date.now()+120000}))")
                def route_request(route):
                    url = urlparse(route.request.url)
                    if route.request.url.startswith(origin + '/api/'):
                        route.fulfill(status=200, content_type='application/json', body=json.dumps({'code': 200, 'data': [], 'items': []}))
                    elif f'{url.scheme}://{url.netloc}' == origin:
                        route.continue_()
                    else:
                        route.abort()
                context.route('**/*', route_request)
                page = context.new_page()
                page.goto(origin + '/juyiting', wait_until='domcontentloaded', timeout=30000)
                page.locator('.onboarding-dialog .skip-button').wait_for(state='visible', timeout=30000)
                page.locator('.onboarding-dialog .skip-button').click()
                page.locator('.onboarding-overlay').wait_for(state='hidden')
                for surface in SURFACES:
                    button = page.locator(f'[data-workbench-tab="{surface}"]:visible').first
                    if button.count():
                        button.click()
                    else:
                        page.locator('.workbench-mobile-more:visible').click()
                        name = {'agents': '点将册', 'treasure': '百宝箱', 'messages': '消息通知'}[surface]
                        page.locator('.workbench-more-menu').get_by_role('button', name=name).click()
                    page.wait_for_timeout(100)
                    row = page.evaluate('''() => {
                      const panel = document.querySelector('.panel-overlay.is-workbench-panel');
                      const nav = document.querySelector('.workbench-mobile-nav');
                      const heading = document.querySelector('.workbench-breadcrumb strong');
                      const rect = el => el?.getBoundingClientRect().toJSON();
                      return {scrollWidth: document.documentElement.scrollWidth, viewportWidth: innerWidth,
                        title: heading?.textContent?.trim(), panel: rect(panel), dock: nav && getComputedStyle(nav).display !== 'none' ? rect(nav) : null,
                        startCard: rect(document.querySelector('.overview-start-card')),
                        stepsVisible: document.querySelector('.overview-start-steps') && getComputedStyle(document.querySelector('.overview-start-steps')).display !== 'none'};
                    }''')
                    assert row['scrollWidth'] <= width + 1, (width, height, surface, row)
                    assert row['title'] == {'overview': '办事概览', 'tasks': '我的事项', 'chat': '厅内议事', 'agents': '点将册', 'treasure': '百宝箱', 'library': '典籍阁', 'messages': '消息通知'}[surface], row
                    assert (row['panel'] is None) == (surface == 'overview'), row
                    if row['dock'] and row['panel']:
                        assert row['panel']['bottom'] <= row['dock']['top'] + 1, row
                    if surface == 'overview':
                        assert row['startCard'] and row['startCard']['width'] > 0, row
                        assert row['stepsVisible'] == (width > 1000), row
                    if surface == 'treasure':
                        search = page.locator('.treasure-search button[type="submit"]')
                        search_rect = search.bounding_box()
                        assert search_rect and search_rect['width'] >= 68 and search_rect['height'] <= 52, (width, height, search_rect)
                        assert search.evaluate('el => getComputedStyle(el).whiteSpace') == 'nowrap'
                    report.append({'viewport': f'{width}x{height}', 'surface': surface, **row})
                    if args.screenshots and (width, surface) in ((390, 'overview'), (390, 'tasks'), (390, 'chat'), (1440, 'overview')):
                        args.screenshots.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(args.screenshots / f'visual-shell-{width}-{surface}.png'))
                context.close()
        finally:
            browser.close()
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps({'browser': 'system Chromium, not fixed CI', 'scope': 'isolated empty-API Vue shell', 'results': report}, ensure_ascii=False, indent=2) + '\n')
    print(f'PASS: {len(report)} Vue surface/viewport checks; no page overflow, dock collision or mislabeled root page')


if __name__ == '__main__':
    main()
