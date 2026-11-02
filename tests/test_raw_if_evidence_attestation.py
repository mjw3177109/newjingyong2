"""Synthetic raw-SWF attestation tests; no protected game content."""
import copy
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.build_root_if_audit_handoff import build_handoff
from tools.crosscheck_root_if_handoff import crosscheck, verify_raw_evidence
from tools.index_root_if_opcode_windows import build_windows


def fixture(root):
    action = bytes.fromhex('960100020e9d0200000000')
    def tag(code, payload=b''):
        return struct.pack('<H', (code << 6) | len(payload)) + payload
    body = bytes.fromhex('0800000c0100') + tag(12, action) + tag(1) + tag(0)
    raw = b'FWS\x08' + struct.pack('<I', 8 + len(body)) + body
    swf = root / 'mini.swf'
    swf.write_bytes(raw)
    swf_sha, action_sha = hashlib.sha256(raw).hexdigest(), hashlib.sha256(action).hexdigest()
    rid = hashlib.sha256(f'{swf_sha}:1:{action_sha}:5'.encode('ascii')).hexdigest()[:24]
    packet = {
        'review_id': rid, 'root_frame': 1, 'action_tag_ordinal': 1,
        'action_sha256': action_sha, 'if_source_offset': 5,
        'branch_target_offset': 10, 'fallthrough_offset': 10,
        'if_record_reachable': True, 'same_frame_sprite_transition': False,
        'structural_priority': 8, 'nearby_access_hints': [],
        'review_status': 'unverified',
    }
    packets = {
        'schema': 'swf-root-if-review-packets-v1',
        'source_swf_sha256': swf_sha, 'verified_story_events': 0,
        'manual_review_limit': 12, 'total_if_review_packets': 1,
        'selected_action_tags': 1, 'manual_review_queue': [packet],
    }
    return swf, packets, build_handoff(packets), build_windows(swf, packets)


class RawAttestationTests(unittest.TestCase):
    def test_exact_raw_reports_pass(self):
        with tempfile.TemporaryDirectory() as d:
            swf, packets, handoff, windows = fixture(Path(d))
            verify_raw_evidence(swf, packets, handoff, windows)
            self.assertEqual(crosscheck(handoff, windows)['matched_candidate_count'], 1)

    def test_internally_consistent_opcode_relabel_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            swf, packets, handoff, windows = fixture(Path(d))
            forged = copy.deepcopy(windows)
            row = forged['entries'][0]
            # These four changes preserve the old internal crosscheck invariants.
            row['preceding_opcode_classes'] = ['push_opaque', 'boolean_logic']
            row['straight_line_preceding_opcode_classes'] = ['push_opaque', 'boolean_logic']
            row['comparison_opcode_count'] = 0
            self.assertEqual(crosscheck(handoff, forged)['matched_candidate_count'], 1)
            with self.assertRaisesRegex(ValueError, 'raw SWF opcode windows'):
                verify_raw_evidence(swf, packets, handoff, forged)

    def test_internally_consistent_handoff_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            swf, packets, handoff, windows = fixture(Path(d))
            forged = copy.deepcopy(handoff)
            forged['warning'] = 'altered source-free report'
            self.assertEqual(crosscheck(forged, windows)['matched_candidate_count'], 1)
            with self.assertRaisesRegex(ValueError, 'raw SWF handoff'):
                verify_raw_evidence(swf, packets, forged, windows)

    def test_cli_attestation_accepts_original_and_fails_closed_on_tamper(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            swf, packets, handoff, windows = fixture(root)
            for name, report in (('packets', packets), ('handoff', handoff), ('windows', windows)):
                (root / (name + '.json')).write_text(json.dumps(report), encoding='utf-8')
            output = root / 'result.json'
            script = Path(__file__).resolve().parents[1] / 'tools' / 'crosscheck_root_if_handoff.py'
            cmd = [sys.executable, str(script), '--swf', str(swf),
                   '--packets', str(root / 'packets.json'),
                   '--handoff', str(root / 'handoff.json'),
                   '--windows', str(root / 'windows.json'), '--out', str(output)]
            ok = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertTrue(output.exists())
            output.unlink()
            forged = copy.deepcopy(windows)
            forged['entries'][0]['successor_arm_windows']['branch']['stop_reason'] = 'window_limit'
            (root / 'windows.json').write_text(json.dumps(forged), encoding='utf-8')
            bad = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            self.assertNotEqual(bad.returncode, 0)
            self.assertIn('raw SWF opcode windows', bad.stderr)
            self.assertFalse(output.exists())

    def test_cli_rejects_half_supplied_raw_inputs(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            _, _, handoff, windows = fixture(root)
            for name, report in (('handoff', handoff), ('windows', windows)):
                (root / (name + '.json')).write_text(json.dumps(report), encoding='utf-8')
            script = Path(__file__).resolve().parents[1] / 'tools' / 'crosscheck_root_if_handoff.py'
            cmd = [sys.executable, str(script), '--swf', str(root / 'mini.swf'),
                   '--handoff', str(root / 'handoff.json'),
                   '--windows', str(root / 'windows.json'), '--out', str(root / 'out.json')]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('must be provided together', result.stderr)
            self.assertFalse((root / 'out.json').exists())


if __name__ == '__main__':
    unittest.main()
