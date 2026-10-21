# Travel Concierge

A small, importable Copilot Studio travel demo for a Power Platform ALM workshop. It demonstrates a customer-facing agent rather than explaining ALM inside the conversation.

**Choose a city -> Set a budget -> Explore a sample itinerary -> Compare costs**

Plan a fictional three-day / two-night city break for one adult in Lisbon, Rome or Barcelona. A structured topic collects the destination, budget and preferences, displays a fixed example itinerary, calculates the sample cost using Power Fx, and reports whether the included categories fit the budget.

This is an original, simplified demo of the [public Microsoft travel-concierge scenario](https://learn.microsoft.com/power-platform/architecture/solution-ideas/agent-travel-customer), not an official Zava asset or a copy of an internal demo.

## Safety and scope

- The agent has **no booking, payment, inventory, weather or customer-data connections**.
- Prices are fictional EUR amounts. No availability, opening hours, tickets or accessibility have been checked.
- The estimate covers two single-occupancy room nights, three days of meals and local transport, and one activities allowance. It excludes flights, intercity travel, taxes, insurance and extras.
- Preferences are collected in the conversation, but the guided itinerary is a fixed example, not a personalized live search.
- No reservation or request is saved. The agent cannot book, pay, refund or generate booking references.
- Use synthetic examples only. Never enter credentials, card details, passport data, customer records or real booking IDs.
- The repository is public. Keep tenant identifiers and environment-specific configuration out of committed files.
- GitHub Actions packages the source into an **unmanaged Dataverse solution**. A separate, manually triggered workflow can import it into the configured test environment. Publishing the agent remains manual.

## Try the demo

In the Copilot Studio test chat, try:

1. `Plan a city break`
2. Choose **Lisbon**, enter **400** EUR, then **food and a relaxed pace**.
3. Expected sample estimate: **366 EUR**, **34 EUR** below budget for the included categories.
4. Restart with **Rome** and **400** EUR: **450 EUR**, **50 EUR** over budget.
5. `Can you book it?` Expected: a clear explanation that no reservation or payment is possible.

The guided topics use English prompts; the agent instructions request the user's language for generative responses. French trigger phrases are included, but this is not a fully localized French solution.

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

The final importable ZIP is written to `out/` and ignored by Git. PAC CLI currently generates a different publisher option-value prefix on each `copilot pack`; the normalization step fixes this demo publisher at `11411`. The historical `ppdemo_ReleaseRadar` schema, solution name, artifact name and deployment identity are deliberately retained so importing this revision updates the existing agent instead of creating a second one. Only the displayed name and scenario change.

## Package with GitHub Actions

Run **Actions -> Package Travel Concierge -> Run workflow**. The job has read-only repository permissions, uses no environment credentials, and publishes the ZIP as the `release-radar-solution` workflow artifact for 14 days.

## Import into the intended test environment

### GitHub Actions deployment

Use **Actions -> Deploy Travel Concierge -> Run workflow** on `main`:

1. Supply the run ID of a successful **Package Travel Concierge** build from `main`.
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
  topics/                 # Guided trip planner, booking boundaries, system topics
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
