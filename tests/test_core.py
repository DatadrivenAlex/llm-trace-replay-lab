import unittest

from trace_replay import compare_traces, diff_values, normalize


class ReplayTests(unittest.TestCase):
    def test_volatile_fields_are_ignored_recursively(self):
        self.assertEqual(
            normalize({"timestamp": 1, "call": {"request_id": "a", "x": 2}}),
            {"call": {"x": 2}},
        )

    def test_trace_order_is_irrelevant_but_call_order_is_not(self):
        report = compare_traces(
            [{"trace_id": "a", "calls": [1, 2]}, {"trace_id": "b", "output": "ok"}],
            [{"trace_id": "b", "output": "ok"}, {"trace_id": "a", "calls": [2, 1]}],
        )
        self.assertFalse(report.passed)
        self.assertTrue(any("calls[0]" in item for item in report.differences))

    def test_reports_missing_and_extra_ids(self):
        report = compare_traces([{"trace_id": "old"}], [{"trace_id": "new"}])
        self.assertEqual(report.missing_ids, ("old",))
        self.assertEqual(report.unexpected_ids, ("new",))

    def test_nested_diff_paths_are_actionable(self):
        self.assertEqual(
            diff_values({"answer": {"text": "a"}}, {"answer": {"text": "b"}}),
            ["$.answer.text: expected 'a', got 'b'"],
        )

    def test_duplicate_id_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate expected"):
            compare_traces([{"trace_id": "x"}, {"trace_id": "x"}], [])

    def test_clean_replay_passes(self):
        traces = [{"trace_id": "x", "output": {"answer": "42"}}]
        self.assertTrue(compare_traces(traces, traces).passed)


if __name__ == "__main__":
    unittest.main()
