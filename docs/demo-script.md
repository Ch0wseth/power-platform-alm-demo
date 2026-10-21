# Release Radar demo script

Use the Copilot Studio test chat with synthetic data. This is a scripted conversation with the demo agent, not a live deployment.

1. **Open:** `Walk me through a release`. Expected: Capture → Review → Release → Prove, with GitHub Actions and Power Platform Pipelines described as delivery choices.
2. **Start:** `Start a release readiness check`. Expected: the agent asks about the solution owner, then one readiness question at a time.
3. **Show a gap:** say that there is no named owner and no recovery plan. Expected: the final status is not `READY TO TEST`; the agent identifies ownership/recovery as gaps.
4. **Show a control:** `Why does the pull request workflow have no deployment identity?` Expected: untrusted PR code is kept separate from a trusted deployment identity.
5. **Close:** `What evidence proves the same artifact reached test?` Expected: the agent asks for or explains the commit, solution version, artifact digest, test record, approval, and run record.

## Acceptance checks

- Answers stay within the fictional ALM walkthrough and don't claim live tenant access.
- Missing owner, tests, target configuration, approval, or recovery are surfaced as readiness gaps.
- The agent never requests or echoes real credentials or sensitive data.
- No deployment, publishing, or external action is performed by this sample.
