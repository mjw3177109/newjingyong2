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
            assert '拳脚' in page.locator('#attack').inner_text()
            assert '12 伤害' in page.locator('#attack').inner_text()
            assert page.locator('#rematch').is_disabled()
            assert page.evaluate("document.querySelector('#game').getContext('2d').getImageData(10, 10, 1, 1).data[3] > 0")
            # A mouse click focuses the Save button; movement keys must still work
            # without requiring an undocumented click on the canvas/background.
            page.locator('#save').click()
            assert page.evaluate("document.activeElement.id") == 'save'
            page.keyboard.press('ArrowRight')
            page.locator('#save').click()
            assert page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1')).game.player.x"
            ) == 6, 'focused game button swallowed the movement shortcut'
            # A legacy strict-v2 checkpoint must still load through the real UI.
            # This tests browser integration, not just the standalone adapter.
            legacy_game = page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1')).game"
            )
            page.evaluate(
                """game => localStorage.setItem(
                    'jianghu-q-save-v1', JSON.stringify(game)
                )""",
                legacy_game,
            )
            page.reload(wait_until='networkidle')
            page.once('dialog', lambda dialog: dialog.accept())
            page.locator('#load').click()
            assert page.locator('#silver').inner_text() == '10'
            page.locator('#save').click()
            upgraded = page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1'))"
            )
            assert upgraded['format'] == 'demo-event-envelope'
            assert upgraded['game']['player']['x'] == 6
            assert upgraded['eventHistory'] == {}
            # Exercise the independent bamboo scene in real Chromium, not merely
            # its source-level wiring. This is original demo content, not SWF fidelity.
            bamboo_context = browser.new_context()
            bamboo_page = bamboo_context.new_page()
            bamboo_page.on('pageerror', lambda error: errors.append(str(error)))
            bamboo_page.goto(url, wait_until='networkidle')
            gate_save = json.loads(json.dumps(upgraded))
            gate_save['game']['player']['x'] = 24
            gate_save['game']['player']['y'] = 7
            bamboo_page.evaluate(
                "(raw) => localStorage.setItem('jianghu-q-save-v1', raw)",
                json.dumps(gate_save),
            )
            bamboo_page.once('dialog', lambda dialog: dialog.accept())
            bamboo_page.locator('#load').click()
            bamboo_page.locator('#interact').click()
            assert '竹风山径' in bamboo_page.locator('#quest-desc').inner_text()
            assert bamboo_page.locator('#save').is_disabled()
            assert bamboo_page.locator('#export-save').is_disabled()
            for _ in range(2):
                bamboo_page.keyboard.press('ArrowRight')
            stored_region = bamboo_page.evaluate(
                "JSON.parse(localStorage.getItem('newjingyong2:bamboo-session:v1'))"
            )
            assert stored_region['position'] == {'x': 3, 'y': 4}
            bamboo_page.reload(wait_until='networkidle')
            assert bamboo_page.locator('#save').is_disabled(), 'region did not restore after refresh'
            assert '竹风山径' in bamboo_page.locator('#quest-desc').inner_text()
            for _ in range(7):
                bamboo_page.keyboard.press('ArrowRight')
            bamboo_page.keyboard.press('e')
            assert bamboo_page.evaluate(
                "localStorage.getItem('newjingyong2:bamboo-session:v1')"
            ) is None, 'exiting region must clear the independent checkpoint'
            assert '竹风山径' not in bamboo_page.locator('#quest-desc').inner_text()
            assert bamboo_page.locator('#save').is_enabled()
            assert bamboo_page.locator('#export-save').is_enabled()
            bamboo_page.locator('#save').click()
            returned = bamboo_page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1'))"
            )
            assert (returned['game']['player']['x'], returned['game']['player']['y']) == (23, 7)
            # Corrupted independent region data must never block boot or be
            # treated as a valid player position after a browser refresh.
            bamboo_page.evaluate(
                "() => localStorage.setItem('newjingyong2:bamboo-session:v1', '{broken-json')"
            )
            bamboo_page.reload(wait_until='networkidle')
            assert '竹风山径' not in bamboo_page.locator('#quest-desc').inner_text()
            assert bamboo_page.locator('#save').is_enabled()
            assert bamboo_page.locator('#export-save').is_enabled()
            # Starting over must remove a valid region checkpoint as well as
            # the V2 game save; a subsequent refresh must not revive the region.
            bamboo_page.once('dialog', lambda dialog: dialog.accept())
            bamboo_page.locator('#load').click()  # restore village x=23 from saved V2
            bamboo_page.keyboard.press('ArrowRight')  # approach gate x=24
            bamboo_page.locator('#interact').click()
            assert '竹风山径' in bamboo_page.locator('#quest-desc').inner_text()
            # Cancelling a reset must preserve the live region and its checkpoint.
            before_cancel = bamboo_page.evaluate(
                "localStorage.getItem('newjingyong2:bamboo-session:v1')"
            )
            assert before_cancel is not None
            bamboo_page.once('dialog', lambda dialog: dialog.dismiss())
            bamboo_page.locator('#new-game').click()
            assert '竹风山径' in bamboo_page.locator('#quest-desc').inner_text()
            assert bamboo_page.evaluate(
                "localStorage.getItem('newjingyong2:bamboo-session:v1')"
            ) == before_cancel, 'cancelled reset must preserve the region checkpoint'
            bamboo_page.reload(wait_until='networkidle')
            assert '竹风山径' in bamboo_page.locator('#quest-desc').inner_text()
            bamboo_page.once('dialog', lambda dialog: dialog.accept())
            bamboo_page.locator('#new-game').click()
            assert bamboo_page.evaluate(
                "localStorage.getItem('newjingyong2:bamboo-session:v1')"
            ) is None
            bamboo_page.reload(wait_until='networkidle')
            assert '竹风山径' not in bamboo_page.locator('#quest-desc').inner_text()
            bamboo_context.close()
            # Non-empty replay metadata must survive the actual browser load/save path.
            # This is adapter persistence coverage, not an original-SWF event mapping.
            with_history = {**upgraded, 'eventHistory': {'demo_event_1': True}}
            page.evaluate(
                "(raw) => localStorage.setItem('jianghu-q-save-v1', raw)",
                json.dumps(with_history),
            )
            page.once('dialog', lambda dialog: dialog.accept())
            page.locator('#load').click()
            page.locator('#save').click()
            persisted = page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1'))"
            )
            assert persisted['eventHistory'] == {'demo_event_1': True}
            page.reload(wait_until='networkidle')
            page.once('dialog', lambda dialog: dialog.accept())
            page.locator('#load').click()
            page.locator('#save').click()
            assert page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1')).eventHistory"
            ) == {'demo_event_1': True}
            # Reset metadata to keep the remaining original-demo assertions isolated.
            page.evaluate(
                "(raw) => localStorage.setItem('jianghu-q-save-v1', raw)",
                json.dumps(upgraded),
            )
            page.once('dialog', lambda dialog: dialog.accept())
            page.locator('#load').click()
            # Canvas pointer coordinates must respect CSS scaling; each click moves one tile.
            canvas_box = page.locator('#game').bounding_box()
            assert canvas_box
            def click_tile(x, y):
                page.mouse.click(
                    canvas_box['x'] + canvas_box['width'] * (x + 0.5) / 25,
                    canvas_box['y'] + canvas_box['height'] * (y + 0.5) / 15,
                )
            click_tile(7, 8)
            page.locator('#save').click()
            assert page.evaluate("JSON.parse(localStorage.getItem('jianghu-q-save-v1')).game.player.x") == 7
            click_tile(6, 8)
            page.locator('#save').click()
            assert page.evaluate("JSON.parse(localStorage.getItem('jianghu-q-save-v1')).game.player.x") == 6
            page.keyboard.press('b')
            assert '背包：' in page.locator('#toast').inner_text()
            page.keyboard.press('j')
            assert '未接受' in page.locator('#toast').inner_text()

            walk_to_objective(page)
            page.locator('#interact').focus()
            assert page.evaluate("document.activeElement.id") == 'interact'
            page.keyboard.press('e')
            assert '清心草' in page.locator('#quest-progress').inner_text()
            # Real UI acceptance must produce exactly one replay marker in the envelope.
            page.locator('#save').click()
            accepted = page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1'))"
            )
            assert accepted['eventHistory'] == {'demo_quest_accepted': True}
            assert accepted['game']['quest'] == 'active'
            # Acceptance metadata must survive a real reload and explicit UI load.
            # This is a demo marker, not a recovered jin.swf event.
            page.reload(wait_until='networkidle')
            assert page.locator('#silver').inner_text() == '10'
            page.once('dialog', lambda dialog: dialog.accept())
            page.locator('#load').click()
            page.locator('#save').click()
            reloaded_acceptance = page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1'))"
            )
            assert reloaded_acceptance['game']['quest'] == 'active'
            assert reloaded_acceptance['eventHistory'] == {'demo_quest_accepted': True}
            page.keyboard.press('Escape')  # dismiss dialogue without activating focused button
            assert not page.locator('#dialog').is_visible()
            walk_to_objective(page)
            page.locator('#interact').click()
            assert '清心草' in page.locator('#inventory').inner_text()
            page.locator('#interact').click()
            walk_to_objective(page)
            page.locator('#interact').click()
            assert page.locator('#combat').is_visible()
            assert page.locator('#drink').is_disabled(), 'empty combat potion button must be disabled'
            assert '0 包' in page.locator('#drink').inner_text()
            before_invalid_potion = page.locator('#journal').inner_text()
            page.keyboard.press('3')
            assert page.locator('#journal').inner_text() == before_invalid_potion, 'disabled potion shortcut must not create a fake turn'
            page.keyboard.press('Escape')
            assert page.locator('#combat').is_visible(), 'Escape must not silently abandon a battle'
            page.locator('#attack').click()
            assert '拳脚，造成 12 点伤害' in page.locator('#journal').inner_text()
            for _ in range(2):
                page.locator('#attack').click()
            assert not page.locator('#combat').is_visible()
            page.locator('#save').click()
            first_victory = page.evaluate("JSON.parse(localStorage.getItem('jianghu-q-save-v1')).eventHistory")
            assert first_victory == {'demo_quest_accepted': True, 'demo_first_bandit_victory': True}
            walk_to_objective(page)
            page.locator('#interact').click()
            assert page.locator('#silver').inner_text() == '40'
            assert '竹纹短剑' in page.locator('#inventory').inner_text()
            page.locator('#save').click()
            completed_history = page.evaluate("JSON.parse(localStorage.getItem('jianghu-q-save-v1')).eventHistory")
            assert completed_history == {**first_victory, 'demo_quest_completed': True}
            assert page.locator('#rest-village').is_disabled(), 'reward dialogue must block village rest'
            page.locator('#interact').click()
            # Two enemy counterattacks cost 12 HP; R restores exactly the missing 12.
            assert page.locator('#hp-num').inner_text() == '88 / 100'
            assert page.locator('#rest-village').is_enabled()
            assert '恢复 12 气血' in page.locator('#rest-village').inner_text()
            page.locator('#rest-village').focus()
            page.keyboard.press('r')
            assert page.locator('#hp-num').inner_text() == '100 / 100'
            assert page.locator('#rest-village').is_disabled()
            assert '恢复 12 点气血' in page.locator('#journal').inner_text()
            rested_journal = page.locator('#journal').inner_text()
            page.keyboard.press('r')
            assert page.locator('#journal').inner_text() == rested_journal, 'full-HP R must be a no-op'
            page.locator('#equip-weapon').click()
            assert page.locator('#attack-num').inner_text() == '16'
            assert '青竹剑' in page.locator('#attack').inner_text()
            assert '16 伤害' in page.locator('#attack').inner_text()
            assert page.locator('#rematch').is_enabled()
            page.locator('#rematch').click()
            assert page.locator('#combat').is_visible()
            assert page.locator('#rematch').is_disabled()
            page.locator('#attack').click()
            page.locator('#attack').click()
            assert not page.locator('#combat').is_visible()
            assert '再试胜利！不重复发放任务奖励' in page.locator('#journal').inner_text()
            assert page.locator('#silver').inner_text() == '40'
            assert page.locator('#inventory').inner_text().count('竹纹短剑') == 1
            page.locator('#save').click()
            after_rematch = page.evaluate("JSON.parse(localStorage.getItem('jianghu-q-save-v1')).eventHistory")
            assert after_rematch == completed_history, 'rematch must not duplicate milestone events'
            # The button path must use the same capped heal rule as the R shortcut.
            assert page.locator('#hp-num').inner_text() == '94 / 100'
            assert '恢复 6 气血' in page.locator('#rest-village').inner_text()
            page.locator('#rest-village').click()
            assert page.locator('#hp-num').inner_text() == '100 / 100'
            assert page.locator('#rest-village').is_disabled()
            assert '恢复 6 点气血' in page.locator('#journal').inner_text()

            # Rejecting an older local checkpoint must preserve unsaved completed
            # progress AND its in-memory event replay history (not only UI silver).
            page.evaluate(
                "(raw) => localStorage.setItem('jianghu-q-save-v1', raw)",
                json.dumps(accepted),
            )
            page.once('dialog', lambda dialog: dialog.dismiss())
            page.locator('#load').click()
            # Dismissing a stale checkpoint must not overwrite either the current
            # run or the original stored bytes before the player explicitly saves.
            assert page.evaluate("JSON.parse(localStorage.getItem('jianghu-q-save-v1'))") == accepted
            assert page.locator('#silver').inner_text() == '40'
            assert page.locator('#hp-num').inner_text() == '100 / 100'
            assert page.locator('#inventory').inner_text().count('竹纹短剑') == 1
            assert page.locator('#rematch').is_enabled()
            page.locator('#save').click()
            after_cancelled_load = page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1'))"
            )
            assert after_cancelled_load['game']['quest'] == 'completed'
            assert after_cancelled_load['eventHistory'] == completed_history, (
                'cancelled load must preserve in-memory completion markers'
            )
            page.reload(wait_until='networkidle')
            assert page.locator('#silver').inner_text() == '10'
            # Cancel local checkpoint preview: current run and stored checkpoint stay intact.
            load_previews = []
            page.once('dialog', lambda dialog: (load_previews.append(dialog.message), dialog.dismiss()))
            page.locator('#load').click()
            assert page.locator('#silver').inner_text() == '10'
            assert page.evaluate("JSON.parse(localStorage.getItem('jianghu-q-save-v1')).game.quest") == 'completed'
            page.once('dialog', lambda dialog: (load_previews.append(dialog.message), dialog.accept()))
            page.locator('#load').click()
            assert page.locator('#silver').inner_text() == '40'
            assert page.locator('#attack-num').inner_text() == '16'
            assert len(load_previews) == 2
            assert all('银两 40' in message and '不会删除或修改本机存档' in message for message in load_previews)
            # Completed quest milestones must survive a second real UI reload/load.
            # This is original-demo persistence coverage, not SWF plot fidelity.
            page.locator('#save').click()
            page.reload(wait_until='networkidle')
            page.once('dialog', lambda dialog: dialog.accept())
            page.locator('#load').click()
            assert page.locator('#silver').inner_text() == '40'
            assert page.locator('#rematch').is_enabled()
            page.locator('#save').click()
            restored_completion = page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1'))"
            )
            assert restored_completion['game']['quest'] == 'completed'
            assert restored_completion['eventHistory'] == completed_history
            assert restored_completion['game']['player']['silver'] == 40
            # A rematch after loading a completed checkpoint must not replay rewards
            # or append milestone events; exercise the real UI, not the adapter alone.
            page.locator('#rematch').click()
            assert page.locator('#combat').is_visible()
            page.locator('#attack').click()
            page.locator('#attack').click()
            assert not page.locator('#combat').is_visible()
            assert page.locator('#silver').inner_text() == '40'
            assert page.locator('#inventory').inner_text().count('竹纹短剑') == 1
            page.locator('#save').click()
            after_restored_rematch = page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1'))"
            )
            assert after_restored_rematch['game']['quest'] == 'completed'
            assert after_restored_rematch['eventHistory'] == completed_history
            assert after_restored_rematch['game']['player']['silver'] == 40

            with page.expect_download() as download_info:
                page.locator('#export-save').click()
            download = download_info.value
            exported = json.loads(Path(download.path()).read_text(encoding='utf-8'))
            assert exported['format'] == 'demo-event-envelope' and exported['version'] == 1
            assert exported['game']['version'] == 2 and exported['game']['quest'] == 'completed'
            assert exported['eventHistory'] == {'demo_quest_accepted': True, 'demo_first_bandit_victory': True, 'demo_quest_completed': True}, 'quest milestones must survive save/export'

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
            # Imported completion milestones must be retained in memory, even
            # though importing does not silently write a local checkpoint.
            with imported_page.expect_download() as imported_download_info:
                imported_page.locator('#export-save').click()
            imported_export = json.loads(
                Path(imported_download_info.value.path()).read_text(encoding='utf-8')
            )
            assert imported_export['game']['quest'] == 'completed'
            assert imported_export['eventHistory'] == completed_history, (
                'accepted portable import must restore all completion milestones'
            )
            assert imported_page.evaluate("localStorage.getItem('jianghu-q-save-v1')") is None
            # Explicit save after portable import must persist the imported event
            # milestones; import alone must never write a local checkpoint.
            imported_page.locator('#save').click()
            imported_checkpoint = imported_page.evaluate(
                "JSON.parse(localStorage.getItem('jianghu-q-save-v1'))"
            )
            assert imported_checkpoint['game']['quest'] == 'completed'
            assert imported_checkpoint['eventHistory'] == completed_history
            imported_page.reload(wait_until='networkidle')
            assert imported_page.locator('#silver').inner_text() == '10', 'checkpoint must require explicit load after refresh'
            imported_page.once('dialog', lambda dialog: dialog.accept())
            imported_page.locator('#load').click()
            assert imported_page.locator('#silver').inner_text() == '40'
            with imported_page.expect_download() as persisted_import_download:
                imported_page.locator('#export-save').click()
            persisted_import = json.loads(
                Path(persisted_import_download.value.path()).read_text(encoding='utf-8')
            )
            assert persisted_import['eventHistory'] == completed_history, (
                'explicitly saved imported milestones must survive refresh and load'
            )
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
            assert saved['format'] == 'demo-event-envelope' and saved['version'] == 1
            assert (saved['game']['player']['x'], saved['game']['player']['y']) == (6, 8), (
                'touch direction must move exactly one walkable tile'
            )
            mobile_box = mobile_page.locator('#game').bounding_box()
            assert mobile_box
            def tap_tile(x, y):
                mobile_page.touchscreen.tap(
                    mobile_box['x'] + mobile_box['width'] * (x + 0.5) / 25,
                    mobile_box['y'] + mobile_box['height'] * (y + 0.5) / 15,
                )
            tap_tile(7, 8)
            mobile_page.locator('#save').tap()
            assert mobile_page.evaluate("JSON.parse(localStorage.getItem('jianghu-q-save-v1')).game.player.x") == 7
            tap_tile(6, 8)
            mobile_page.locator('#save').tap()
            assert mobile_page.evaluate("JSON.parse(localStorage.getItem('jianghu-q-save-v1')).game.player.x") == 6
            mobile_page.reload(wait_until='networkidle')
            assert mobile_page.locator('#silver').inner_text() == '10'
            mobile_page.once('dialog', lambda dialog: dialog.accept())
            mobile_page.locator('#load').tap()
            with mobile_page.expect_download() as mobile_download:
                mobile_page.locator('#export-save').tap()
            restored = json.loads(Path(mobile_download.value.path()).read_text(encoding='utf-8'))
            assert restored['format'] == 'demo-event-envelope' and restored['version'] == 1
            assert (restored['game']['player']['x'], restored['game']['player']['y']) == (6, 8)
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
            mobile_output.parent.mkdir(parents=True, exist_ok=True)
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
            assert page.evaluate("JSON.parse(localStorage.getItem('jianghu-q-save-v1')).game.quest") == 'completed'
            # Confirmed restart clears both current run and this browser's checkpoint.
            page.once('dialog', lambda dialog: dialog.accept())
            page.locator('#new-game').click()
            assert page.locator('#silver').inner_text() == '10'
            assert page.locator('#attack-num').inner_text() == '12'
            assert page.evaluate("localStorage.getItem('jianghu-q-save-v1')") is None
            page.reload(wait_until='networkidle')
            page.locator('#load').click()
            assert '没有有效的存档' in page.locator('#toast').inner_text()
            # A malformed event envelope must never be interpreted as a legacy save.
            # Reject it without a confirmation prompt, mutating progress, or deleting data.
            malformed = json.dumps({
                'format': 'demo-event-envelope',
                'version': 1,
                'game': {'version': 2},
                'eventHistory': {},
            })
            page.evaluate(
                "(raw) => localStorage.setItem('jianghu-q-save-v1', raw)",
                malformed,
            )
            page.locator('#load').click()
            assert '没有有效的存档' in page.locator('#toast').inner_text()
            assert page.locator('#silver').inner_text() == '10'
            assert page.evaluate(
                "localStorage.getItem('jianghu-q-save-v1')"
            ) == malformed, 'invalid checkpoint must remain available for manual recovery'
            # Local checkpoints obey the same UTF-8 64 KiB limit as portable imports.
            # This payload is short in JS code units but oversized in UTF-8 bytes.
            page.evaluate("localStorage.setItem('jianghu-q-save-v1', '汉'.repeat(22000))")
            assert page.evaluate("localStorage.getItem('jianghu-q-save-v1').length") == 22000
            page.locator('#load').click()
            assert '本机存档超过 64 KB' in page.locator('#toast').inner_text()
            assert page.locator('#silver').inner_text() == '10'
            assert page.evaluate("localStorage.getItem('jianghu-q-save-v1').length") == 22000
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
