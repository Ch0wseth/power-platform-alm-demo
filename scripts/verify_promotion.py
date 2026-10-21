"""Require a trusted export and proof that its selected format deployed in test."""

import json
import os
import re
import subprocess


def gh(*args):
    return subprocess.check_output(["gh", *args], text=True)


def verify_run(run, repo, workflow):
    if not (
        run["status"] == "completed"
        and run["conclusion"] == "success"
        and run["path"] == f".github/workflows/{workflow}"
        and run["head_branch"] == "main"
        and run["head_repository"]["full_name"] == repo
        and run["event"] == "workflow_dispatch"
    ):
        raise ValueError(f"Untrusted or unsuccessful run: {workflow}")


def verify_test_steps(jobs, deployment_format):
    expected = {
        "solution": "Import exported solution ZIP",
        "template": "Create a separate agent from the YAML template",
    }[deployment_format]
    for job in jobs:
        steps = {step["name"]: step["conclusion"] for step in job.get("steps", [])}
        if (
            job["conclusion"] == "success"
            and steps.get("Verify selected export") == "success"
            and steps.get("Verify target environment") == "success"
            and steps.get(expected) == "success"
        ):
            return
    raise ValueError("No successful test deployment for the selected format")


def verify_export_reference(log, export_run_id):
    # The pinned artifact-download action logs its evaluated run-id input.
    if not re.search(rf"\brun-id:\s*{re.escape(export_run_id)}\s*$", log, re.MULTILINE):
        raise ValueError("Test deployment did not download the specified export")


def main():
    if os.environ["TEST_VALIDATED"] != "true":
        raise ValueError("Explicit functional test confirmation is required")
    repo = os.environ["GITHUB_REPOSITORY"]
    export_id = os.environ["EXPORT_RUN_ID"]
    test_id = os.environ["TEST_RUN_ID"]
    for run_id in (export_id, test_id):
        if not re.fullmatch(r"[1-9][0-9]*", run_id):
            raise ValueError("Run IDs must be positive integers")
    deployment_format = os.environ["FORMAT"]
    if deployment_format not in ("solution", "template"):
        raise ValueError("Unsupported format")
    for run_id, workflow in (
        (export_id, "export-agent.yml"),
        (test_id, "deploy-export.yml"),
    ):
        run = json.loads(gh("api", f"repos/{repo}/actions/runs/{run_id}"))
        verify_run(run, repo, workflow)
    jobs = json.loads(
        gh("api", f"repos/{repo}/actions/runs/{test_id}/jobs?per_page=100")
    )
    verify_test_steps(jobs["jobs"], deployment_format)
    log = gh("run", "view", test_id, "--repo", repo, "--log")
    verify_export_reference(log, export_id)
    print("Trusted export and matching successful test deployment confirmed.")


if __name__ == "__main__":
    main()
