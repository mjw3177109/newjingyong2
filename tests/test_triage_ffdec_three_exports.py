"""Synthetic, source-free tests for conditional three-export FFDec triage."""
import hashlib
import json
import unittest

from tools.triage_ffdec_three_exports import triage

SWF = 'a' * 64


def index(files, swf=SWF):
    entries = [
        {'path_sha256': hashlib.sha256(name.encode('utf-8')).hexdigest(),
         'content_sha256': hashlib.sha256(value.encode('utf-8')).hexdigest()}
        for name, value in files.items()
    ]
    return {'schema_version': 1, 'source_swf_sha256': swf,
            'script_file_count': len(entries), 'entries': entries}


class ThreeExportTriageTests(unittest.TestCase):
    def setUp(self):
        self.a = index({'secret/hero.as': 'version A'})
        self.b = index({'secret/hero.as': 'version B'})

    def test_b_is_observed_outlier_when_a_equals_c(self):
        report = triage(self.a, self.b, self.a)
        self.assertEqual(report['whole_export_pattern'], 'a_c_equal')
        self.assertEqual(report['observed_outlier'], 'b')
        self.assertEqual(report['common_paths_with_content_difference'], 1)
        self.assertEqual(report['verified_story_event_count'], 0)
        self.assertNotIn('secret', json.dumps(report))
        self.assertNotIn('hero.as', json.dumps(report))

    def test_a_is_observed_outlier_when_b_equals_c(self):
        report = triage(self.a, self.b, self.b)
        self.assertEqual(report['whole_export_pattern'], 'b_c_equal')
        self.assertEqual(report['observed_outlier'], 'a')

    def test_three_distinct_exports_do_not_claim_outlier(self):
        c = index({'secret/hero.as': 'version C'})
        report = triage(self.a, self.b, c)
        self.assertEqual(report['whole_export_pattern'], 'all_distinct')
        self.assertIsNone(report['observed_outlier'])

    def test_third_export_outlier_and_all_equal(self):
        self.assertEqual(triage(self.a, self.a, self.b)['observed_outlier'], 'c')
        same = triage(self.a, self.a, self.a)
        self.assertEqual(same['whole_export_pattern'], 'all_equal')
        self.assertEqual(same['paths_with_any_difference'], 0)

    def test_membership_change_is_separate_from_content_change(self):
        b = index({'secret/hero.as': 'version A', 'private/extra.as': 'another'})
        report = triage(self.a, b, self.a)
        self.assertEqual(report['paths_with_membership_difference'], 1)
        self.assertEqual(report['common_paths_with_content_difference'], 0)
        self.assertEqual(report['paths_with_any_difference'], 1)

    def test_limit_only_truncates_examples_not_counts(self):
        a = index({f'private/{i}.as': 'a' for i in range(3)})
        b = index({f'private/{i}.as': 'b' for i in range(3)})
        report = triage(a, b, a, limit=1)
        self.assertEqual(report['paths_with_any_difference'], 3)
        self.assertEqual(len(report['changed_path_sha256_examples']), 1)
        self.assertTrue(report['examples_truncated'])
        self.assertEqual(len(report['changed_path_variation_examples']), 1)
        self.assertEqual(sum(report['path_variation_patterns'].values()), 3)

    def test_whole_exports_all_distinct_can_have_per_path_repeated_pairs(self):
        a = index({'private/one.as': 'v1', 'private/two.as': 'v1'})
        b = index({'private/one.as': 'v2', 'private/two.as': 'v1'})
        c = index({'private/one.as': 'v1', 'private/two.as': 'v2'})
        report = triage(a, b, c)
        self.assertEqual(report['whole_export_pattern'], 'all_distinct')
        self.assertEqual(report['path_variation_patterns']['a_c_equal'], 1)
        self.assertEqual(report['path_variation_patterns']['a_b_equal'], 1)
        self.assertEqual(report['content_path_variation_patterns'],
                         report['path_variation_patterns'])
        self.assertEqual(sum(report['membership_path_variation_patterns'].values()), 0)
        self.assertEqual(report['paths_with_any_difference'],
                         sum(report['path_variation_patterns'].values()))
        self.assertNotIn('private/', json.dumps(report))

    def test_membership_and_content_patterns_are_separated(self):
        a = index({'private/stable.as': 'A'})
        b = index({'private/stable.as': 'B', 'private/only-b.as': 'B'})
        c = index({'private/stable.as': 'A'})
        report = triage(a, b, c)
        self.assertEqual(report['path_variation_patterns']['a_c_equal'], 2)
        self.assertEqual(report['content_path_variation_patterns']['a_c_equal'], 1)
        self.assertEqual(report['membership_path_variation_patterns']['a_c_equal'], 1)
        self.assertEqual({e['difference_kind'] for e in report['changed_path_variation_examples']},
                         {'content', 'membership'})
        self.assertTrue(all(len(e['path_sha256']) == 64 for e in
                            report['changed_path_variation_examples']))

    def test_reject_mixed_swf_and_tampered_index(self):
        with self.assertRaisesRegex(ValueError, 'different source SWF'):
            triage(self.a, self.b, index({'x': 'z'}, swf='c' * 64))
        bad = json.loads(json.dumps(self.a))
        bad['entries'][0]['content_sha256'] = 'not-a-sha'
        with self.assertRaisesRegex(ValueError, 'SHA-256'):
            triage(self.a, self.b, bad)

    def test_reject_bool_or_out_of_range_limit(self):
        for invalid in (True, 0, 101, -1, '2'):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    triage(self.a, self.b, self.a, limit=invalid)


if __name__ == '__main__':
    unittest.main()
