import unittest
from datetime import datetime, timezone

from project_control_center.analyze import analyze
from project_control_center.report import render_html


class AnalysisTests(unittest.TestCase):
    def test_missing_metadata_and_stale_repository(self):
        data = [{"name": "demo", "description": "", "language": "", "pushed_at": "2020-01-01T00:00:00Z", "open_issues": 11, "archived": False, "private": False, "url": "https://github.com/x/demo"}]
        result = analyze(data, datetime(2026, 10, 16, tzinfo=timezone.utc))
        self.assertEqual(result["repositories"][0]["score"], 30)
        self.assertEqual(len(result["repositories"][0]["findings"]), 4)

    def test_html_escapes_untrusted_github_metadata(self):
        data = [{"name": "<script>alert(1)</script>", "description": "ok", "language": "Python", "pushed_at": "", "open_issues": 0, "archived": False, "private": False, "url": "javascript:alert(1)"}]
        html = render_html(analyze(data))
        self.assertNotIn("<script>alert", html)
        self.assertNotIn('href="javascript:', html)

    def test_name_overlap_is_only_suggestion(self):
        data = [{"name": x, "description": "ok", "language": "Python", "private": False, "archived": False} for x in ("docrag", "docrag-")]
        result = analyze(data)
        self.assertEqual(len(result["possible_name_overlaps"]), 1)


if __name__ == "__main__":
    unittest.main()

