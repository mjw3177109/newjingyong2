#!/usr/bin/env python3
"""Real Chromium NPC click-to-approach regression for original bamboo demo."""
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

def click_tile(page, x, y, width, height):
    box = page.locator('#game').bounding_box()
    assert box
    page.mouse.click(box['x'] + box['width'] * (x + .5) / width,
                     box['y'] + box['height'] * (y + .5) / height)

def session(page):
    return page.evaluate("JSON.parse(localStorage.getItem('newjingyong2:bamboo-session:v1'))")

def main():
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, executable_path=os.environ.get('BROWSER_EXECUTABLE') or None)
            page = browser.new_page(viewport={'width': 1440, 'height': 960})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(f'http://127.0.0.1:{server.server_port}/index.html', wait_until='networkidle')
            # Walk to the village's east gate through actual canvas clicks.
            for _ in range(80):
                click_tile(page, 24, 7, 25, 15)
                if '竹风山径' in page.locator('#quest-desc').inner_text():
                    break
                if '山径入口' in page.locator('#toast').inner_text():
                    break
                # Interact when the player reaches the gate vicinity.
                page.keyboard.press('e')
                if '竹风山径' in page.locator('#quest-desc').inner_text():
                    break
            assert '竹风山径' in page.locator('#quest-desc').inner_text(), 'could not enter bamboo region'
            before = session(page)
            assert before and before['regionId'] == 'bamboo-pass'
            # Click the keeper's occupied tile; each click must commit at most one legal step.
            for _ in range(108):
                previous = session(page)
                click_tile(page, 6, 3, 12, 9)
                current = session(page)
                assert current, 'session vanished'
                distance = abs(current['position']['x'] - previous['position']['x']) + abs(current['position']['y'] - previous['position']['y'])
                assert distance in (0, 1), 'canvas click skipped a tile'
                assert (current['position']['x'], current['position']['y']) != (6, 3), 'player occupied NPC tile'
                if abs(current['position']['x'] - 6) + abs(current['position']['y'] - 3) == 1:
                    break
            else:
                raise AssertionError('NPC was not reachable by repeated real clicks')
            assert '按 E 交谈' in page.locator('#toast').inner_text()
            page.reload(wait_until='networkidle')
            assert session(page) == current, 'refresh lost the persisted NPC approach'
            page.keyboard.press('e')
            assert '山路曲折' in page.locator('#toast').inner_text() or '山路曲折' in page.locator('#quest-desc').inner_text(), 'NPC dialogue not visible'
            assert not errors, f'page errors: {errors}'
            browser.close()
            print('PASS: real Chromium NPC clicks, legal persisted steps, refresh, and E dialogue')
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

if __name__ == '__main__':
    main()
