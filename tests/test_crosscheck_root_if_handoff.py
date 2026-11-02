"""Synthetic source-free checks: no original SWF content or story claims."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from tools.crosscheck_root_if_handoff import crosscheck


def fixtures():
    swf, action = 'b' * 64, 'c' * 64
    rid = hashlib.sha256(f'{swf}:2:{action}:15'.encode('ascii')).hexdigest()[:24]
    handoff = {
        'schema': 'swf-root-if-audit-handoff-v1', 'source_swf_sha256': 'b' * 64,
        'candidate_count': 1, 'verified_story_events': 0, 'ready_for_html5_mapping': 0,
        'entries': [{'review_id': rid, 'source_location': {
            'root_frame': 9, 'action_tag_ordinal': 2, 'if_source_offset': 15,
            'action_sha256': 'c' * 64, 'branch_target_offset': 20, 'fallthrough_offset': 20},
            'checks': {'ffdec_script_sha256': None, 'condition_confirmed': False,
                       'state_effects_confirmed': False, 'map_context_confirmed': False,
                       'runtime_reproduced': False, 'independent_reviewed': False,
                       'adaptation_rights_confirmed': False},
            'review_status': 'unverified', 'html5_event_id': None}],
    }
    windows = {
        'schema': 'swf-root-if-opcode-windows-v1', 'source_swf_sha256': 'b' * 64,
        'selected_if_count': 1, 'window_width': 12, 'verified_story_events': 0,
        'entries': [{'review_id': rid, 'root_frame': 9, 'action_tag_ordinal': 2,
                     'if_source_offset': 15, 'review_status': 'unverified',
                     'preceding_record_count': 2,
                     'preceding_record_offsets': [4, 10],
                     'preceding_opcode_classes': ['push_opaque', 'comparison'],
                     'straight_line_preceding_record_count': 2,
                     'straight_line_preceding_record_offsets': [4, 10],
                     'straight_line_preceding_opcode_classes': ['push_opaque', 'comparison'],
                     'straight_line_boundary_limited': False,
                     'comparison_opcode_count': 1,
                     'has_branch_or_opaque_control': False,
                     'if_incoming_reachable_syntactic_source_count': 1,
                     'if_has_multiple_reachable_syntactic_predecessors': False}],
    }
    return handoff, windows


class CrosscheckTests(unittest.TestCase):
    def test_matching_handoff_reports_only_source_free_hints(self):
        h, w = fixtures()
        result = crosscheck(h, w)
        self.assertEqual(result['matched_candidate_count'], 1)
        self.assertTrue(result['entries'][0]['bounded_comparison_opcode_present'])
        self.assertEqual(result['verified_story_events'], 0)
        self.assertNotIn('condition_confirmed', str(result))

    def test_rejects_cross_swf_and_coordinate_drift(self):
        h, w = fixtures()
        w['source_swf_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            crosscheck(h, w)
        h, w = fixtures()
        w['entries'][0]['if_source_offset'] = 16
        with self.assertRaisesRegex(ValueError, 'coordinate'):
            crosscheck(h, w)

    def test_rejects_missing_or_duplicate_review_identity(self):
        h, w = fixtures()
        w['entries'][0]['review_id'] = 'e' * 24
        with self.assertRaisesRegex(ValueError, 'identity'):
            crosscheck(h, w)
        h, w = fixtures()
        w['entries'].append(copy.deepcopy(w['entries'][0]))
        w['selected_if_count'] = 2
        h['entries'].append(copy.deepcopy(h['entries'][0]))
        h['candidate_count'] = 2
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            crosscheck(h, w)

    def test_rejects_unverified_claims_and_private_checkboxes(self):
        h, w = fixtures()
        w['verified_story_events'] = 1
        with self.assertRaisesRegex(ValueError, 'story events'):
            crosscheck(h, w)
        h, w = fixtures()
        h['entries'][0]['checks']['condition_confirmed'] = True
        with self.assertRaisesRegex(ValueError, 'attestations'):
            crosscheck(h, w)

    def test_rejects_action_fingerprint_or_review_identity_tampering(self):
        h, w = fixtures()
        h['entries'][0]['source_location']['action_sha256'] = 'd' * 64
        with self.assertRaisesRegex(ValueError, 'review identity'):
            crosscheck(h, w)
        h, w = fixtures()
        h['entries'][0]['source_location']['action_sha256'] = 'not-a-sha'
        with self.assertRaisesRegex(ValueError, 'fingerprint'):
            crosscheck(h, w)
        h, w = fixtures()
        changed_id = 'f' * 24
        h['entries'][0]['review_id'] = changed_id
        w['entries'][0]['review_id'] = changed_id
        with self.assertRaisesRegex(ValueError, 'review identity'):
            crosscheck(h, w)

    def test_rejects_incomplete_or_extended_private_checklist(self):
        for mutate in (
            lambda checks: checks.pop('runtime_reproduced'),
            lambda checks: checks.update({'unreviewed_extra': False}),
            lambda checks: checks.update({'condition_confirmed': 0}),
            lambda checks: checks.pop('ffdec_script_sha256'),
        ):
            with self.subTest(mutate=mutate):
                h, w = fixtures()
                mutate(h['entries'][0]['checks'])
                with self.assertRaisesRegex(ValueError, 'attestations'):
                    crosscheck(h, w)

    def test_rejects_tampered_opcode_window_summary(self):
        mutations = (
            lambda row: row.update({'preceding_record_count': 3}),
            lambda row: row.update({'preceding_record_offsets': [10, 4]}),
            lambda row: row.update({'preceding_record_offsets': [4, 15]}),
            lambda row: row.update({'straight_line_preceding_record_offsets': [4]}),
            lambda row: row.update({'straight_line_preceding_opcode_classes': ['comparison', 'push_opaque']}),
            lambda row: row.update({'preceding_opcode_classes': ['push_opaque', 'fake_comparison']}),
            lambda row: row.update({'comparison_opcode_count': 0}),
            lambda row: row.update({'straight_line_boundary_limited': True}),
            lambda row: row.update({'has_branch_or_opaque_control': True}),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                h, w = fixtures()
                mutate(w['entries'][0])
                with self.assertRaisesRegex(ValueError, 'opcode'):
                    crosscheck(h, w)

    def test_accepts_valid_truncated_straight_line_suffix(self):
        h, w = fixtures()
        row = w['entries'][0]
        row['straight_line_preceding_record_count'] = 1
        row['straight_line_preceding_record_offsets'] = [10]
        row['straight_line_preceding_opcode_classes'] = ['comparison']
        row['straight_line_boundary_limited'] = True
        result = crosscheck(h, w)
        self.assertTrue(result['entries'][0]['bounded_comparison_opcode_present'])

    def test_rejects_window_exceeding_declared_width(self):
        h, w = fixtures()
        w['window_width'] = 1
        with self.assertRaisesRegex(ValueError, 'opcode'):
            crosscheck(h, w)

    def test_rejects_inconsistent_opcode_and_predecessor_counts(self):
        h, w = fixtures()
        w['entries'][0]['straight_line_preceding_record_count'] = 3
        with self.assertRaisesRegex(ValueError, 'opcode'):
            crosscheck(h, w)
        h, w = fixtures()
        w['entries'][0]['if_has_multiple_reachable_syntactic_predecessors'] = True
        with self.assertRaisesRegex(ValueError, 'predecessor'):
            crosscheck(h, w)


    def test_cli_rejects_invalid_opcode_summary_like_import(self):
        h, w = fixtures()
        w['entries'][0]['preceding_record_count'] = 3
        with self.assertRaisesRegex(ValueError, 'opcode'):
            crosscheck(h, w)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            handoff, windows, output = root / 'handoff.json', root / 'windows.json', root / 'out.json'
            handoff.write_text(json.dumps(h), encoding='utf-8')
            windows.write_text(json.dumps(w), encoding='utf-8')
            script = Path(__file__).resolve().parents[1] / 'tools' / 'crosscheck_root_if_handoff.py'
            result = subprocess.run(
                [sys.executable, str(script), '--handoff', str(handoff),
                 '--windows', str(windows), '--out', str(output)],
                capture_output=True, text=True, timeout=15)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('opcode', result.stderr)
            self.assertFalse(output.exists())

    def test_cli_and_import_agree_on_valid_window(self):
        h, w = fixtures()
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            handoff, windows, output = root / 'handoff.json', root / 'windows.json', root / 'out.json'
            handoff.write_text(json.dumps(h), encoding='utf-8')
            windows.write_text(json.dumps(w), encoding='utf-8')
            script = Path(__file__).resolve().parents[1] / 'tools' / 'crosscheck_root_if_handoff.py'
            result = subprocess.run(
                [sys.executable, str(script), '--handoff', str(handoff),
                 '--windows', str(windows), '--out', str(output)],
                capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(output.read_text(encoding='utf-8')), crosscheck(h, w))



if __name__ == '__main__':
    unittest.main()
