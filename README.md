# Release Radar

A small, importable Copilot Studio demo for a Power Platform ALM workshop. The agent turns a release into four gates:

**Capture → Review → Release → Prove**

It guides a maker through a simulated readiness check, asks about owners, dependencies, tests, artifact identity, target configuration, approval, and recovery, then returns `BLOCKED`, `NEEDS OWNER`, or `READY TO TEST`.

## Safety and scope

- This is a fictional demo agent with **no GitHub, Dataverse, or Sanofi connections**.
- It does not run CI, inspect an environment, deploy a solution, or publish the agent.
- Use synthetic examples only. Never add credentials, customer or patient data, or regulated records.
- The repository is public. Keep tenant identifiers and environment-specific configuration out of committed files.
- GitHub Actions packages the source into an **unmanaged Dataverse solution**. Importing and publishing are separate, manual steps.

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
```

## References

- [PAC CLI: `pac copilot init` and `pac copilot pack`](https://learn.microsoft.com/power-platform/developer/cli/reference/copilot)
- [Copilot Studio extension for Visual Studio Code](https://learn.microsoft.com/microsoft-copilot-studio/visual-studio-code-extension-overview)
- [Export and import agents using solutions](https://learn.microsoft.com/microsoft-copilot-studio/authoring-solutions-import-export)
