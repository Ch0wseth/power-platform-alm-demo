# Release Radar

A small, importable Copilot Studio demo for a Power Platform ALM workshop. The agent turns a release into four gates:

**Capture → Review → Release → Prove**

It guides a maker through a simulated readiness check, asks about owners, dependencies, tests, artifact identity, target configuration, approval, and recovery, then returns `BLOCKED`, `NEEDS OWNER`, or `READY TO TEST`.

## Safety and scope

- This is a fictional demo agent with **no GitHub, Dataverse, or Sanofi connections**.
- It does not run CI, inspect an environment, deploy a solution, or publish the agent.
- Use synthetic examples only. Never add credentials, customer or patient data, or regulated records.
- The repository is public. Keep tenant identifiers and environment-specific configuration out of committed files.
- GitHub Actions packages the source into an **unmanaged Dataverse solution**. A separate, manually triggered workflow can import it into the configured test environment. Publishing the agent remains manual.

## Try the demo

In the Copilot Studio test chat, try:

1. `Walk me through a release`
2. `Start a release readiness check`
3. Answer the questions one at a time; intentionally leave out an owner or recovery plan and observe the status.
4. `Why should a pull request workflow have no deployment credentials?`
5. `When would you use Power Platform Pipelines instead of GitHub Actions?`

The readiness check should never claim that it has inspected a real environment or pipeline.

## Package locally

Requires .NET 10 or later and network access to NuGet:

```powershell
dnx Microsoft.PowerApps.CLI.Tool@2.13.1 --yes copilot pack `
  --publisher-prefix ppdemo `
  --project-dir agent `
  --output-path out/raw `
  --solution-name ppdemo_ReleaseRadar

dnx Microsoft.PowerApps.CLI.Tool@2.13.1 --yes solution unpack `
  --zipfile out/raw/ppdemo_ReleaseRadar.zip `
  --folder out/unpacked `
  --packagetype Unmanaged

python scripts/stabilize_solution_prefix.py out/unpacked/Other/Solution.xml

dnx Microsoft.PowerApps.CLI.Tool@2.13.1 --yes solution pack `
  --zipfile out/ppdemo_ReleaseRadar.zip `
  --folder out/unpacked `
  --packagetype Unmanaged
```

The final importable ZIP is written to `out/` and ignored by Git. PAC CLI currently generates a different publisher option-value prefix on each `copilot pack`; the normalization step fixes this demo publisher at `11411` so repeated packages remain compatible with its first import. Keep the publisher name and prefixes unchanged after importing this solution into an environment.

## Package with GitHub Actions

Run **Actions → Package Release Radar → Run workflow**. The job has read-only repository permissions, uses no environment credentials, and publishes the ZIP as the `release-radar-solution` workflow artifact for 14 days.

## Import into the intended test environment

### GitHub Actions deployment

Use **Actions -> Deploy Release Radar -> Run workflow** on `main`:

1. Supply the run ID of a successful **Package Release Radar** build from `main`.
2. Leave `import_solution` unchecked to validate the artifact, OIDC identity, and target access without importing.
3. Run again with `import_solution` checked to import the same solution artifact.
4. Open the imported agent in Copilot Studio and test it before manually publishing.

Deployments are serialized, restricted to `main`, and use the GitHub Environment `copilot-studio-test`. The workflow only consumes successful packaging runs from this repository and records the source commit and ZIP SHA-256. It does not rebuild during deployment and never publishes the agent.

The GitHub Environment must contain these **environment secrets** (identifiers are kept out of public source and masked in logs):

| Secret | Value |
| --- | --- |
| `PP_TENANT_ID` | Entra tenant containing the target environment |
| `PP_APPLICATION_ID` | Deployment application's client ID |
| `PP_ENVIRONMENT_ID` | Target Power Platform environment ID |
| `PP_ENVIRONMENT_URL` | Actual Dataverse URL such as `https://example.crm.dynamics.com`, not the Copilot Studio portal URL |

The Entra application must have a GitHub federated credential for audience `api://AzureADTokenExchange`, issuer `https://token.actions.githubusercontent.com`, and the exact OIDC subject for this repository's `copilot-studio-test` environment. This repository uses immutable subjects, so the owner/repository IDs must be included; inspect its OIDC configuration rather than copying an older name-only example. Restrict the GitHub Environment deployment branches to `main`. Add required reviewers if approval is needed.

Add the application's service principal as an application user in the target Dataverse environment with a role permitting solution import and Copilot Studio component authoring. No Azure subscription role or Graph application permission is needed by the runtime deployment identity.

### Manual import

1. Download the workflow artifact or build it locally.
2. Open the intended environment in Copilot Studio and use **Solutions → Import solution** to select the ZIP.
3. Open the imported agent, test the conversation, review authentication and channel settings, and publish only after the environment owner approves.

The solution package is environment-independent; select the target at import time. Import does **not** publish or share the agent. The environment URL and ID are intentionally not stored in this public repository.

## Source layout

```text
agent/
  agent.mcs.yml
  settings.mcs.yml
  topics/                 # Standard Copilot Studio agent topics
scripts/
  stabilize_solution_prefix.py
.github/workflows/
  package-agent.yml       # Stable PAC CLI solution package; no deployment
  deploy-agent.yml        # Manual OIDC import; no agent publication
```

## References

- [PAC CLI: `pac copilot init` and `pac copilot pack`](https://learn.microsoft.com/power-platform/developer/cli/reference/copilot)
- [Copilot Studio extension for Visual Studio Code](https://learn.microsoft.com/microsoft-copilot-studio/visual-studio-code-extension-overview)
- [Export and import agents using solutions](https://learn.microsoft.com/microsoft-copilot-studio/authoring-solutions-import-export)
- [PAC CLI authentication and GitHub federation](https://learn.microsoft.com/power-platform/developer/cli/reference/auth)
- [OIDC/FIC for Power Platform GitHub Actions](https://learn.microsoft.com/power-platform/alm/tutorials/github-actions-oidc-fic)
