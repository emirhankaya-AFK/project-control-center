import unittest
from unittest.mock import patch

from project_control_center.analyze import analyze
from project_control_center.github import GitHubError, collect, enrich_ci
from project_control_center.report import render_html


class CITests(unittest.TestCase):
    def test_collect_private_for_authenticated_owner(self):
        item = {"name": "private-project", "private": True,
                "owner": {"login": "alice"}}
        with patch("project_control_center.github._api", side_effect=[{"login": "alice"}, [[item]]]) as api:
            repos = collect("alice")
        self.assertTrue(repos[0]["private"])
        self.assertEqual(api.call_args_list[1].args[0].split("?")[0], "user/repos")

    def test_public_fallback_for_other_owner(self):
        with patch("project_control_center.github._api", side_effect=[{"login": "bob"}, [[]]]) as api:
            self.assertEqual(collect("alice"), [])
        self.assertTrue(api.call_args_list[1].args[0].startswith("users/alice/repos?"))

    def test_bounded_ci_and_pending(self):
        repos = [{"name": "older", "pushed_at": "2026-01-01"},
                 {"name": "newer", "pushed_at": "2026-10-01"},
                 {"name": "archived", "archived": True, "pushed_at": "2026-10-19"}]
        with patch("project_control_center.github._api", return_value={"workflow_runs": [{"status": "completed", "conclusion": "failure"}]}) as api:
            result = enrich_ci(repos, "alice", limit=1)
        self.assertEqual(api.call_count, 1)
        self.assertEqual(result[1]["ci_status"], "failure")
        self.assertEqual(result[0]["ci_status"], "not_checked")
        self.assertEqual(result[2]["ci_status"], "not_checked")
        self.assertFalse(api.call_args.kwargs["paginate"])

    def test_unavailable_and_no_runs_are_not_success(self):
        repos = [{"name": "a"}, {"name": "b"}, {"name": "c"}]
        with patch("project_control_center.github._api", side_effect=[GitHubError("403"), {"workflow_runs": []}, {"workflow_runs": [{"status": "in_progress"}]}]):
            enrich_ci(repos, "alice", limit=3)
        self.assertEqual([r["ci_status"] for r in repos], ["unavailable", "no_runs", "in_progress"])

    def test_score_action_and_xss(self):
        row = {"name": "repo", "url": "https://github.com/u/repo", "private": False,
               "archived": False, "language": "Python", "description": "yes", "ci_status": "failure", "open_issues": 0}
        audited = analyze([row])
        self.assertEqual(audited["repositories"][0]["score"], 70)
        self.assertIn("loglarını incele", audited["repositories"][0]["next_action"])
        self.assertIn("Başarısız", render_html(audited))
        row["ci_status"] = "<svg/onload=alert(1)>"
        self.assertNotIn("<svg", render_html(analyze([row])))

    def test_ci_limit_validation(self):
        with self.assertRaises(ValueError):
            enrich_ci([], "alice", limit=0)

class RunnerStartupTests(unittest.TestCase):
    def test_failure_without_runner_or_steps_is_startup_failure(self):
        repos = [{"name": "blocked", "pushed_at": "2026-10-21"}]
        run = {"workflow_runs": [{"id": 123, "status": "completed", "conclusion": "failure"}]}
        jobs = {"jobs": [{"conclusion": "failure", "steps": [], "runner_name": ""}]}
        with patch("project_control_center.github._api", side_effect=[run, jobs]) as api:
            enrich_ci(repos, "alice", limit=1)
        self.assertEqual(api.call_count, 2)
        self.assertEqual(repos[0]["ci_status"], "startup_failure")
        self.assertIn("test adımı çalışmadı", analyze(repos)["repositories"][0]["next_action"])

    def test_real_test_failure_keeps_failure(self):
        repos = [{"name": "failed"}]
        run = {"workflow_runs": [{"id": 123, "status": "completed", "conclusion": "failure"}]}
        jobs = {"jobs": [{"conclusion": "failure", "steps": [{"name": "pytest", "conclusion": "failure"}], "runner_name": "GitHub Actions"}]}
        with patch("project_control_center.github._api", side_effect=[run, jobs]):
            enrich_ci(repos, "alice", limit=1)
        self.assertEqual(repos[0]["ci_status"], "failure")

    def test_no_job_details_cannot_be_claimed_runner_failure(self):
        repos = [{"name": "unknown"}]
        run = {"workflow_runs": [{"id": 123, "status": "completed", "conclusion": "failure"}]}
        with patch("project_control_center.github._api", side_effect=[run, GitHubError("forbidden")]):
            enrich_ci(repos, "alice", limit=1)
        self.assertEqual(repos[0]["ci_status"], "failure")

    def test_invalid_job_data_keeps_failure(self):
        repos = [{"name": "unknown"}]
        run = {"workflow_runs": [{"id": 123, "status": "completed", "conclusion": "failure"}]}
        with patch("project_control_center.github._api", side_effect=[run, {"jobs": []}]):
            enrich_ci(repos, "alice", limit=1)
        self.assertEqual(repos[0]["ci_status"], "failure")


if __name__ == "__main__":
    unittest.main()
