import unittest

from verify_promotion import verify_export_reference, verify_run, verify_test_steps


class PromotionEvidenceTests(unittest.TestCase):
    def test_only_successful_expected_workflow_is_trusted(self):
        run = {
            "status": "completed",
            "conclusion": "success",
            "path": ".github/workflows/export-agent.yml",
            "head_branch": "main",
            "head_repository": {"full_name": "owner/repo"},
            "event": "workflow_dispatch",
        }
        verify_run(run, "owner/repo", "export-agent.yml")
        for field, value in (
            ("conclusion", "failure"),
            ("head_branch", "feature"),
            ("path", ".github/workflows/other.yml"),
            ("head_repository", {"full_name": "fork/repo"}),
            ("event", "pull_request"),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                verify_run({**run, field: value}, "owner/repo", "export-agent.yml")

    def test_preflight_and_wrong_format_are_not_deployment_evidence(self):
        def jobs(conclusion):
            return [{
                "conclusion": "success",
                "steps": [
                    {"name": "Verify selected export", "conclusion": "success"},
                    {"name": "Verify target environment", "conclusion": "success"},
                    {"name": "Import exported solution ZIP", "conclusion": conclusion},
                ],
            }]
        verify_test_steps(jobs("success"), "solution")
        with self.assertRaises(ValueError):
            verify_test_steps(jobs("skipped"), "solution")
        with self.assertRaises(ValueError):
            verify_test_steps(jobs("success"), "template")

    def test_export_run_reference_must_match_exactly(self):
        log = "deploy\tDownload trusted export\t2026-10-21T15:47:07Z   Export run: 12345\n"
        verify_export_reference(log, "12345")
        for other in ("1234", "123456"):
            with self.subTest(other=other), self.assertRaises(ValueError):
                verify_export_reference(log, other)

    def test_export_run_reference_requires_exact_download_step(self):
        for step in (
            "Verify selected export",
            "Other Download trusted export",
            "Download trusted export extra",
        ):
            log = f"deploy\t{step}\t2026-10-21T15:47:07Z   Export run: 12345\n"
            with self.subTest(step=step), self.assertRaises(ValueError):
                verify_export_reference(log, "12345")
            log += (
                "deploy\tDownload trusted export\t"
                "2026-10-21T15:47:08Z   Export run: 67890\n"
            )
            with self.subTest(step=step, wrong_export=True), self.assertRaises(ValueError):
                verify_export_reference(log, "12345")

    def test_prefixed_artifact_run_markers_are_not_evidence(self):
        for marker in ("other Export run", "prefix:Export run", "prefix Export run"):
            log = (
                "deploy\tDownload trusted export\t"
                f"2026-10-21T15:47:07Z   {marker}: 12345\n"
            )
            with self.subTest(marker=marker), self.assertRaises(ValueError):
                verify_export_reference(log, "12345")

    def test_missing_artifact_run_reference_is_not_evidence(self):
        for log in (
            "",
            "deploy\tDownload trusted export\t2026-10-21T15:47:07Z   account: example\n",
            "deploy\tDownload trusted export\t2026-10-21T15:47:07Z   Export run:\n12345\n",
        ):
            with self.subTest(log=log), self.assertRaises(ValueError):
                verify_export_reference(log, "12345")

    def test_ambiguous_artifact_run_references_are_not_evidence(self):
        log = "deploy\tDownload trusted export\t2026-10-21T15:47:07Z   Export run: 12345\n"
        for other in ("12345", "67890"):
            duplicate = (
                "deploy\tDownload trusted export\t"
                f"2026-10-21T15:47:08Z   Export run: {other}\n"
            )
            with self.subTest(other=other), self.assertRaises(ValueError):
                verify_export_reference(log + duplicate, "12345")


if __name__ == "__main__":
    unittest.main()
