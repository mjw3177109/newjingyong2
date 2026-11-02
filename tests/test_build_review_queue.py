"""Synthetic-only tests: no original SWF source content or filenames."""
import json
import unittest

from tools.build_review_queue import build_review_queue

SWF = 'a' * 64


def entry(path, content, **hints):
    return {'path_sha256': path * 64, 'content_sha256': content * 64,
            'hint_counts': hints, 'private_filename': 'secret_plot_name.as',
            'private_source': 'hiddenCharacter hiddenQuest secretDialogue'}


def index(entries):
    return {'schema_version': 1, 'source_swf_sha256': SWF,
            'script_file_count': len(entries), 'entries': entries,
            'private_metadata': 'do-not-export'}


class ReviewQueueTests(unittest.TestCase):
    def test_ranked_deterministic_and_source_free(self):
        records = [entry('1', 'b', conditional_if=2),
                   entry('2', 'c', timeline_goto=1, event_handler=2),
                   entry('3', 'd', function_decl=8)]
        a = build_review_queue(index(records), limit=2)
        b = build_review_queue(index(list(reversed(records))), limit=2)
        self.assertEqual(a, b)
        self.assertEqual(a['indexed_script_count'], 3)
        self.assertEqual(a['control_signal_candidate_count'], 2)
        self.assertEqual(a['selected_count'], 2)
        self.assertEqual(a['candidates'][0]['path_sha256'], '2' * 64)
        self.assertEqual(a['candidates'][0]['semantic_status'], 'unverified')
        output = json.dumps(a)
        for secret in ('secret_plot_name', 'hiddenCharacter', 'hiddenQuest',
                       'secretDialogue', 'do-not-export', 'private_filename'):
            self.assertNotIn(secret, output)

    def test_empty_queue_and_limit(self):
        i = index([entry('1', 'b', function_decl=7)])
        self.assertEqual(build_review_queue(i)['candidates'], [])
        self.assertEqual(build_review_queue(i)['control_signal_candidate_count'], 0)
        for value in (0, 501, -1, True, 2.5):
            with self.assertRaises(ValueError):
                build_review_queue(i, limit=value)

    def test_rejects_bad_index_and_counts(self):
        good = index([entry('1', 'b', conditional_if=1)])
        cases = [
            dict(good, schema_version=2),
            dict(good, script_file_count=2),
            index([entry('1', 'b'), entry('1', 'c')]),
            index([entry('1', 'b', conditional_if=-1)]),
            index([entry('1', 'b', timeline_goto='2')]),
            index([entry('1', 'b', conditional_if=True)]),
            index([dict(entry('1', 'b'), path_sha256='not-a-hash')]),
        ]
        for bad in cases:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    build_review_queue(bad)


if __name__ == '__main__':
    unittest.main()
