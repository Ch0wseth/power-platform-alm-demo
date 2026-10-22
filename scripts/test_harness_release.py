import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from harness_release import (
    FILENAME,
    SOLUTION,
    check_configuration,
    check_source_configuration,
    main,
    seal_export,
    verify_payload,
    verify_export_run,
)


TENANT = "11111111-1111-4111-8111-111111111111"
TEST = "22222222-2222-4222-8222-222222222222"
PROD = "33333333-3333-4333-8333-333333333333"
SCHEMA = "ppdemo_HarnessAdvisor"


class HarnessReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        env = patch.dict(
            os.environ,
            {
                "PP_TENANT_ID": TENANT,
                "PP_APPLICATION_ID": TEST,
                "PP_ENVIRONMENT_ID": TEST,
                "PP_ENVIRONMENT_URL": "https://demo.crm.dynamics.com",
                "HARNESS_AGENT_SCHEMA": SCHEMA,
                "SOURCE_HARNESS_VERIFIED": "true",
                "GITHUB_RUN_ID": "123",
                "GITHUB_RUN_ATTEMPT": "2",
            },
        )
        env.start()
        self.addCleanup(env.stop)
        self.make_zip()

    def make_zip(self, managed="1", solution=SOLUTION, schema=SCHEMA):
        with zipfile.ZipFile(self.folder / FILENAME, "w") as archive:
            archive.writestr(
                "solution.xml",
                f"<ImportExportXml><SolutionManifest><UniqueName>{solution}</UniqueName>"
                f"<Managed>{managed}</Managed><Version>1.0.0.0</Version><Publisher>"
                "<CustomizationPrefix>ppdemo</CustomizationPrefix></Publisher>"
                "</SolutionManifest></ImportExportXml>",
            )
            archive.writestr(f"bots/{schema}/bot.xml", "<bot />")

    def test_exact_managed_payload_can_move_test_prod_without_claiming_an_import_test(self):
        check_configuration()
        evidence = seal_export(self.folder)
        result = verify_payload(self.folder, "123", "2", target=PROD)
        self.assertEqual(result, evidence)
        self.assertNotIn(TEST, (self.folder / "release.json").read_text())
        self.assertEqual(result["validation_scope"], "source-agent-only")
        self.assertFalse((self.folder / "test.json").exists())

    def test_rejects_unmanaged_wrong_solution_or_missing_agent(self):
        for kwargs in (
            {"managed": "0"},
            {"solution": "ppdemo_ReleaseRadar"},
            {"schema": "ppdemo_other"},
        ):
            with self.subTest(kwargs=kwargs):
                self.make_zip(**kwargs)
                with self.assertRaises(ValueError):
                    seal_export(self.folder)

    def test_requires_explicit_harness_attestation(self):
        with patch.dict(os.environ, {"SOURCE_HARNESS_VERIFIED": "false"}):
            with self.assertRaises(ValueError):
                seal_export(self.folder)
        with patch.dict(os.environ, {"HARNESS_AGENT_SCHEMA": ""}):
            with self.assertRaises(ValueError):
                check_source_configuration()

    def test_promotion_cli_rejects_missing_functional_attestation_before_api_access(self):
        with (
            patch("sys.argv", ["harness_release.py", "provenance"]),
            patch.dict(os.environ, {"TEST_VALIDATED": "false"}),
            patch("harness_release.gh") as gh,
        ):
            with self.assertRaises(ValueError):
                main()
            gh.assert_not_called()

    def test_promotion_cli_records_the_verified_attempt(self):
        output = self.folder / "outputs.txt"
        with (
            patch("sys.argv", ["harness_release.py", "provenance"]),
            patch.dict(os.environ, {
                "TEST_VALIDATED": "true",
                "RELEASE_RUN_ID": "123",
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_OUTPUT": str(output),
            }),
            patch("harness_release.verify_export_run", return_value="2") as verify,
        ):
            main()
            verify.assert_called_once_with("owner/repo", "123")
        self.assertEqual(output.read_text(), "attempt=2\n")

    def test_detects_changed_zip_and_wrong_run_attempt(self):
        seal_export(self.folder)
        for run_id, attempt in (("124", "2"), ("123", "1")):
            with self.subTest(run_id=run_id, attempt=attempt):
                with self.assertRaises(ValueError):
                    verify_payload(self.folder, run_id, attempt)
        with zipfile.ZipFile(self.folder / FILENAME, "a") as archive:
            archive.writestr("changed.txt", "changed")
        with self.assertRaises(ValueError):
            verify_payload(self.folder, "123", "2")

    def test_prevents_same_environment_imports(self):
        seal_export(self.folder)
        with self.assertRaises(ValueError):
            verify_payload(self.folder, "123", "2", target=TEST)

    def test_promotion_rejects_a_different_validation_scope_or_missing_attestation(self):
        seal_export(self.folder)
        path = self.folder / "release.json"
        evidence = json.loads(path.read_text())
        for changes in (
            {"validation_scope": "import-tested"},
            {"source_acceptance_attested": False},
            {"source_harness_attested": False},
        ):
            with self.subTest(changes=changes):
                path.write_text(json.dumps({**evidence, **changes}))
                with self.assertRaises(ValueError):
                    verify_payload(self.folder, "123", "2")

    def test_configuration_rejects_missing_secret_and_portal_url(self):
        for changes in (
            {"PP_ENVIRONMENT_ID": ""},
            {"PP_ENVIRONMENT_ID": "not-a-uuid"},
            {"PP_ENVIRONMENT_URL": "https://copilotstudio.microsoft.com"},
        ):
            with self.subTest(changes=changes), patch.dict(os.environ, changes):
                with self.assertRaises(ValueError):
                    check_configuration()

    def test_only_completed_export_in_latest_attempt_is_trusted(self):
        run = {
            "status": "completed",
            "conclusion": "success",
            "path": ".github/workflows/harness-release.yml",
            "head_branch": "main",
            "head_repository": {"full_name": "owner/repo"},
            "event": "workflow_dispatch",
            "run_attempt": 2,
        }
        names = (
            "Check source configuration and attestation",
            "Export managed harness solution",
            "Seal managed payload",
            "Upload managed export",
        )
        jobs = {"jobs": [{
            "conclusion": "success",
            "steps": [{"name": name, "conclusion": "success"} for name in names],
        }]}
        with patch("harness_release.gh", side_effect=[json.dumps(run), json.dumps(jobs)]) as gh:
            self.assertEqual(verify_export_run("owner/repo", "123"), "2")
            self.assertIn("/attempts/2/jobs", gh.call_args.args[1])
        jobs["jobs"][0]["steps"][1]["conclusion"] = "skipped"
        with patch("harness_release.gh", side_effect=[json.dumps(run), json.dumps(jobs)]):
            with self.assertRaises(ValueError):
                verify_export_run("owner/repo", "123")
        with patch("harness_release.gh", return_value=json.dumps({**run, "head_branch": "feature"})):
            with self.assertRaises(ValueError):
                verify_export_run("owner/repo", "123")


if __name__ == "__main__":
    unittest.main()
