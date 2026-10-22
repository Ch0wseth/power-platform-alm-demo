"""Validate the managed harness demo export and source-test attestation."""

import argparse
import hashlib
import json
import os
import re
import uuid
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from verify_promotion import gh, verify_run


SOLUTION = "ppdemo_HarnessReleaseAdvisor"
FILENAME = f"{SOLUTION}_managed.zip"
WORKFLOW = "harness-release.yml"


def positive_id(value):
    if not re.fullmatch(r"[1-9][0-9]*", value):
        raise ValueError("Run IDs and attempts must be positive integers")
    return value


def environment_fingerprint(value):
    return hashlib.sha256(str(uuid.UUID(value)).encode()).hexdigest()


def check_configuration():
    for name in (
        "PP_TENANT_ID",
        "PP_APPLICATION_ID",
        "PP_ENVIRONMENT_ID",
        "PP_ENVIRONMENT_URL",
    ):
        if not os.environ.get(name):
            raise ValueError(f"Missing environment secret {name}")
    for name in ("PP_TENANT_ID", "PP_APPLICATION_ID", "PP_ENVIRONMENT_ID"):
        uuid.UUID(os.environ[name])
    if not re.fullmatch(
        r"https://[a-zA-Z0-9.-]+\.crm[0-9]*\.dynamics\.com/?",
        os.environ["PP_ENVIRONMENT_URL"],
    ):
        raise ValueError("Expected a public-cloud Dataverse URL")


def check_source_configuration():
    check_configuration()
    if os.environ.get("SOURCE_HARNESS_VERIFIED") != "true":
        raise ValueError("Confirm the harness, source acceptance tests and settings in TEST first")
    validate_agent_schema(os.environ.get("HARNESS_AGENT_SCHEMA", ""))


def validate_agent_schema(schema):
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+", schema):
        raise ValueError("Set HARNESS_AGENT_SCHEMA to the actual agent schema name from Studio")


def validate_solution(folder, schema):
    validate_agent_schema(schema)
    payload = folder / FILENAME
    with zipfile.ZipFile(payload) as archive:
        if archive.testzip() is not None:
            raise ValueError("Corrupt solution ZIP")
        root = ET.fromstring(archive.read("solution.xml"))
        for path, expected in {
            "./SolutionManifest/UniqueName": SOLUTION,
            "./SolutionManifest/Managed": "1",
            "./SolutionManifest/Publisher/CustomizationPrefix": "ppdemo",
        }.items():
            if root.findtext(path) != expected:
                raise ValueError(f"Unexpected managed solution metadata: {path}")
        if f"bots/{schema}/bot.xml" not in archive.namelist():
            raise ValueError("Configured agent is missing from the solution")
        version = root.findtext("./SolutionManifest/Version")
        if not version or not re.fullmatch(r"\d+\.\d+\.\d+\.\d+", version):
            raise ValueError("Missing or invalid solution version")
    return hashlib.sha256(payload.read_bytes()).hexdigest(), version


def seal_export(folder):
    check_source_configuration()
    schema = os.environ["HARNESS_AGENT_SCHEMA"]
    digest, version = validate_solution(folder, schema)
    evidence = {
        "solution": SOLUTION,
        "filename": FILENAME,
        "agent_schema": schema,
        "version": version,
        "sha256": digest,
        "release_run_id": positive_id(os.environ["GITHUB_RUN_ID"]),
        "release_run_attempt": positive_id(os.environ["GITHUB_RUN_ATTEMPT"]),
        "source_environment": environment_fingerprint(os.environ["PP_ENVIRONMENT_ID"]),
        "source_harness_attested": True,
        "source_acceptance_attested": True,
        "validation_scope": "source-agent-only",
    }
    (folder / "release.json").write_text(json.dumps(evidence, indent=2) + "\n")
    return evidence


def verify_payload(folder, run_id, attempt, target=None):
    evidence = json.loads((folder / "release.json").read_text())
    if (
        evidence["solution"] != SOLUTION
        or evidence["filename"] != FILENAME
        or evidence["release_run_id"] != positive_id(run_id)
        or evidence["release_run_attempt"] != positive_id(attempt)
        or evidence["source_harness_attested"] is not True
        or evidence["source_acceptance_attested"] is not True
        or evidence["validation_scope"] != "source-agent-only"
    ):
        raise ValueError("Release identity or source attestation mismatch")
    digest, version = validate_solution(folder, evidence["agent_schema"])
    if digest != evidence["sha256"] or version != evidence["version"]:
        raise ValueError("Payload differs from the exported release")
    if target and environment_fingerprint(target) == evidence["source_environment"]:
        raise ValueError("PROD must differ from the TEST source environment")
    return evidence


def verify_export_run(repo, run_id):
    run_id = positive_id(run_id)
    run = json.loads(gh("api", f"repos/{repo}/actions/runs/{run_id}"))
    verify_run(run, repo, WORKFLOW)
    attempt = positive_id(str(run["run_attempt"]))
    result = json.loads(
        gh("api", f"repos/{repo}/actions/runs/{run_id}/attempts/{attempt}/jobs?per_page=100")
    )
    required = {
        "Check source configuration and attestation",
        "Export managed harness solution",
        "Seal managed payload",
        "Upload managed export",
    }
    for job in result["jobs"]:
        passed = {
            step["name"]
            for step in job.get("steps", [])
            if step["conclusion"] == "success"
        }
        if job["conclusion"] == "success" and required <= passed:
            return attempt
    raise ValueError("No completed managed harness export in the latest attempt")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        choices=("config", "source-config", "seal", "verify", "provenance"),
    )
    parser.add_argument("--folder", type=Path, default=Path("release"))
    parser.add_argument("--target", action="store_true")
    args = parser.parse_args()
    if args.operation == "config":
        check_configuration()
        return
    if args.operation == "source-config":
        check_source_configuration()
        return
    if args.operation == "provenance":
        if os.environ.get("TEST_VALIDATED") != "true":
            raise ValueError("Explicit functional and harness validation is required")
        attempt = verify_export_run(
            os.environ["GITHUB_REPOSITORY"], os.environ["RELEASE_RUN_ID"]
        )
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(f"attempt={attempt}\n")
        return
    if args.operation == "seal":
        evidence = seal_export(args.folder)
    else:
        run_id = os.environ["RELEASE_RUN_ID"]
        attempt = os.environ["RELEASE_RUN_ATTEMPT"]
        evidence = verify_payload(
            args.folder,
            run_id,
            attempt,
            target=os.environ["PP_ENVIRONMENT_ID"] if args.target else None,
        )
    print(f"Managed solution {evidence['solution']} {evidence['version']}")
    print(f"SHA-256: {evidence['sha256']}")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as summary:
            summary.write(
                f"Managed solution `{evidence['solution']}` {evidence['version']}\n\n"
                f"SHA-256: `{evidence['sha256']}`\n\n"
                "TEST source-agent checks are human-attested. The managed ZIP has "
                "not been imported or tested before PROD in this two-environment demo. "
                "No explicit publish command is run; inspect publication and channels.\n"
            )


if __name__ == "__main__":
    main()
