#!/usr/bin/env python3
"""Exercise the original HTML5 demo in a real Chromium browser.

This is NOT an original-SWF plot, map, or battle-fidelity test.
"""
import json
import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


def walk_to_objective(page):
    button = page.locator('#step-route')
    for _ in range(400):
        if button.is_disabled():
            hint = page.locator('#quest-desc').inner_text()
            assert '已靠近' in hint, f'route stopped before reaching target: {hint}'
            return
        button.click()
    raise AssertionError('objective route did not finish within 400 steps')


def main():
    server = ThreadingHTTPServer(
        ('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}/index.html'
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                executable_path=os.environ.get('BROWSER_EXECUTABLE') or None,
            )
            context = browser.new_context(accept_downloads=True, viewport={'width': 1440, 'height': 960})
            page = context.new_page()
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(url, wait_until='networkidle')
            page.wait_for_function("document.querySelector('#quest-desc').textContent.includes('下一步：')")
            page.wait_for_function("document.querySelector('.portrait img').naturalWidth > 0")
            assert page.locator('#silver').inner_text() == '10'
            assert page.locator('#attack-num').inner_text() == '12'
            assert page.evaluate("document.querySelector('#game').getContext('2d').getImageData(10, 10, 1, 1).data[3] > 0")

            walk_to_objective(page)
            page.locator('#interact').click()
            assert '清心草' in page.locator('#quest-progress').inner_text()
            page.locator('#interact').click()  # dismiss dialogue
            walk_to_objective(page)
            page.locator('#interact').click()
            assert '清心草' in page.locator('#inventory').inner_text()
            page.locator('#interact').click()
            walk_to_objective(page)
            page.locator('#interact').click()
            assert page.locator('#combat').is_visible()
            for _ in range(3):
                page.locator('#attack').click()
            assert not page.locator('#combat').is_visible()
            walk_to_objective(page)
            page.locator('#interact').click()
            assert page.locator('#silver').inner_text() == '40'
            assert '竹纹短剑' in page.locator('#inventory').inner_text()
            page.locator('#interact').click()
            page.locator('#equip-weapon').click()
            assert page.locator('#attack-num').inner_text() == '16'

            page.locator('#save').click()
            page.reload(wait_until='networkidle')
            assert page.locator('#silver').inner_text() == '10'
            page.locator('#load').click()
            assert page.locator('#silver').inner_text() == '40'
            assert page.locator('#attack-num').inner_text() == '16'
            with page.expect_download() as download_info:
                page.locator('#export-save').click()
            download = download_info.value
            exported = json.loads(Path(download.path()).read_text(encoding='utf-8'))
            assert exported['version'] == 2 and exported['quest'] == 'completed'

            fresh = browser.new_context(accept_downloads=True)
            imported_page = fresh.new_page()
            imported_page.on('pageerror', lambda error: errors.append(str(error)))
            imported_page.goto(url, wait_until='networkidle')
            # Import preview must not replace unsaved progress without consent.
            preview_messages = []
            imported_page.once('dialog', lambda dialog: (preview_messages.append(dialog.message), dialog.dismiss()))
            imported_page.locator('#import-save-file').set_input_files(download.path())
            imported_page.wait_for_function("document.querySelector('#toast').textContent.includes('已取消导入')")
            assert imported_page.locator('#silver').inner_text() == '10'
            assert imported_page.evaluate("localStorage.getItem('jianghu-q-save-v1')") is None
            imported_page.once('dialog', lambda dialog: (preview_messages.append(dialog.message), dialog.accept()))
            imported_page.locator('#import-save-file').set_input_files(download.path())
            imported_page.wait_for_function("document.querySelector('#silver').textContent === '40'")
            assert len(preview_messages) == 2
            assert all('银两 40' in message and '不会自动覆盖本机存档' in message for message in preview_messages)
            assert imported_page.locator('#attack-num').inner_text() == '16'
            imported_page.reload(wait_until='networkidle')
            assert imported_page.locator('#silver').inner_text() == '10', 'import must not silently overwrite local save'
            # Independent touch-enabled Chromium context at a narrow mobile viewport.
            # Only original-demo controls are tested; this is not source-SWF fidelity.
            mobile = browser.new_context(
                viewport={'width': 390, 'height': 844},
                device_scale_factor=1,
                is_mobile=True,
                has_touch=True,
                accept_downloads=True,
            )
            mobile_page = mobile.new_page()
            mobile_page.on('pageerror', lambda error: errors.append(str(error)))
            mobile_page.goto(url, wait_until='networkidle')
            mobile_page.wait_for_function("document.querySelector('#quest-desc').textContent.includes('下一步：')")
            assert mobile_page.locator('.mobile-pad').is_visible(), 'touch direction pad is hidden'
            assert mobile_page.locator('[data-direction="right"]').is_visible()
            assert mobile_page.evaluate(
                "document.querySelector('#game').getBoundingClientRect().width <= window.innerWidth"
            ), 'mobile game canvas extends beyond the viewport'
            mobile_page.locator('[data-direction="right"]').tap()
            mobile_page.locator('#save').tap()
            saved = mobile_page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1'))"
            )
            assert (saved['player']['x'], saved['player']['y']) == (6, 8), (
                'touch direction must move exactly one walkable tile'
            )
            mobile_page.reload(wait_until='networkidle')
            assert mobile_page.locator('#silver').inner_text() == '10'
            mobile_page.locator('#load').tap()
            with mobile_page.expect_download() as mobile_download:
                mobile_page.locator('#export-save').tap()
            restored = json.loads(Path(mobile_download.value.path()).read_text(encoding='utf-8'))
            assert (restored['player']['x'], restored['player']['y']) == (6, 8)
            route_button = mobile_page.locator('#step-route')
            for _ in range(400):
                if route_button.is_disabled():
                    assert '已靠近' in mobile_page.locator('#quest-desc').inner_text()
                    break
                route_button.tap()
            else:
                raise AssertionError('touch route did not reach the first NPC')
            mobile_page.locator('#interact').tap()
            assert '清心草' in mobile_page.locator('#quest-progress').inner_text()
            mobile_page.locator('#interact').tap()
            mobile_output = ROOT / 'reports' / 'browser_smoke_mobile.png'
            mobile_page.screenshot(path=str(mobile_output), full_page=True)
            mobile.close()
            assert not errors, f'browser JavaScript errors: {errors}'
            output = ROOT / 'reports' / 'browser_smoke.png'
            output.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(output), full_page=True)
            # Restart must not erase a completed run or local checkpoint when cancelled.
            page.once('dialog', lambda dialog: dialog.dismiss())
            page.locator('#new-game').click()
            assert page.locator('#silver').inner_text() == '40'
            assert page.evaluate("JSON.parse(localStorage.getItem('jianghu-q-save-v1')).quest") == 'completed'
            # Confirmed restart clears both current run and this browser's checkpoint.
            page.once('dialog', lambda dialog: dialog.accept())
            page.locator('#new-game').click()
            assert page.locator('#silver').inner_text() == '10'
            assert page.locator('#attack-num').inner_text() == '12'
            assert page.evaluate("localStorage.getItem('jianghu-q-save-v1')") is None
            page.reload(wait_until='networkidle')
            page.locator('#load').click()
            assert '没有有效的存档' in page.locator('#toast').inner_text()
            print('PASS: Chromium canvas, complete original-demo playthrough, equipment, local save, JSON export/import, and import persistence boundary')
            fresh.close()
            context.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


if __name__ == '__main__':
    main()
