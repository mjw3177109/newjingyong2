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
            # Walk to the village's east gate (24,7) before interacting.
            for _ in range(80):
                click_tile(page, 24, 7, 25, 15)
            page.keyboard.press('e')
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
            # Complete the actual browser journey: route to the exit, return, and
            # verify the independent region checkpoint was cleared.
            for _ in range(108):
                current = session(page)
                if current['position'] == {'x': 10, 'y': 4}:
                    break
                page.locator('#step-route').click()
                next_session = session(page)
                assert next_session, 'region checkpoint vanished before exit'
                distance = abs(next_session['position']['x'] - current['position']['x']) + abs(next_session['position']['y'] - current['position']['y'])
                assert distance == 1, 'exit routing did not make exactly one legal step'
            else:
                raise AssertionError('could not reach bamboo exit through browser controls')
            page.keyboard.press('e')
            assert session(page) is None, 'region checkpoint remained after returning to village'
            assert '青竹村' in page.locator('#quest-desc').inner_text() or '已返回青竹村' in page.locator('#toast').inner_text(), 'village return not visible'
            page.reload(wait_until='networkidle')
            assert session(page) is None, 'refresh unexpectedly restored departed region'
            # Re-enter after leaving: the old NPC-adjacent checkpoint must not leak
            # into a new region session, including after a browser refresh.
            for _ in range(80):
                click_tile(page, 24, 7, 25, 15)
            page.keyboard.press('e')
            reentered = session(page)
            assert reentered and reentered['regionId'] == 'bamboo-pass', 'could not re-enter bamboo region'
            assert reentered['position'] == {'x': 1, 'y': 4}, 'fresh region entry did not reset to the declared spawn tile'
            assert reentered['position'] != current['position'], 'old region position leaked into fresh entry'
            page.reload(wait_until='networkidle')
            assert session(page) == reentered, 'fresh region checkpoint not restored after reload'
            assert not errors, f'page errors: {errors}'
            browser.close()
            print('PASS: Chromium NPC clicks, persistence, E dialogue, exit routing and village return')
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

if __name__ == '__main__':
    main()
