# Travel Concierge

A small, importable Copilot Studio travel demo for a Power Platform ALM workshop. It demonstrates a customer-facing agent rather than explaining ALM inside the conversation.

**Choose a city -> Set a budget -> Explore a sample itinerary -> Compare costs**

Plan a fictional three-day / two-night city break for one adult in Lisbon, Rome or Barcelona. A structured topic collects the destination, budget and preferences, displays a fixed example itinerary, calculates the sample cost using Power Fx, and reports whether the included categories fit the budget.

This is an original, simplified demo of the [public Microsoft travel-concierge scenario](https://learn.microsoft.com/power-platform/architecture/solution-ideas/agent-travel-customer), not an official Zava asset or a copy of an internal demo.

## Separate GitHub Copilot Harness ALM scenario

The [GitHub Copilot Harness workshop](docs/github-harness-alm.md) adds a second,
independent scenario: create **ALM Release Advisor** in the GitHub Copilot Harness
experience in Studio, then export its **managed** solution from DEV, import the
same ZIP into TEST, and promote that tested artifact to PROD after human
validation and environment approval.

Use `harness-release.yml` followed by `harness-promote.yml`. The initial agent
creation is manual; `harness-agent/instructions.md` supplies the authoring content,
not a deployable YAML definition. The scenario requires three new configured
environments and live tenant verification. It does not convert Travel Concierge,
reuse its unmanaged solution, or claim that local tests validate the harness.
The remainder of this README describes the original Travel Concierge scenario.

## Safety and scope

- The agent has **no booking, payment, inventory, weather or customer-data connections**.
- Prices are fictional EUR amounts. No availability, opening hours, tickets or accessibility have been checked.
- The estimate covers two single-occupancy room nights, three days of meals and local transport, and one activities allowance. It excludes flights, intercity travel, taxes, insurance and extras.
- Preferences are collected in the conversation, but the guided itinerary is a fixed example, not a personalized live search.
- No reservation or request is saved. The agent cannot book, pay, refund or generate booking references.
- Use synthetic examples only. Never enter credentials, card details, passport data, customer records or real booking IDs.
- The repository is public. Keep tenant identifiers and environment-specific configuration out of committed files.
- GitHub Actions can package local source or export the live agent as an **unmanaged Dataverse solution ZIP** and an **agent template YAML**. Deployment is manually triggered. No workflow explicitly publishes an agent, but import/create can trigger service-side provisioning and publication; inspect the resulting state in Studio.

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

Deployments are serialized, restricted to `main`, and use the GitHub Environment `copilot-studio-test`. The workflow only consumes successful packaging runs from this repository and records the source commit and ZIP SHA-256. It does not rebuild during deployment or invoke an explicit agent publish command.

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

Select the target at import time. Environment-specific connections and dependencies might require configuration. Import can trigger service-side provisioning and publication even without an explicit publish command, as observed in this workshop. Review publication, authentication and channel state after import. The environment URL and ID are intentionally not stored in this public repository.

## Two export-to-deployment demonstrations

These paths start with the **live agent in Dataverse**, unlike `package-agent.yml`, which builds repository source.

| Path | Export from Studio's environment | Deploy with GitHub Actions |
| --- | --- | --- |
| Classic solution | `pac solution export` produces the unmanaged solution ZIP | `pac solution import` imports the solution and its included components |
| Agent template YAML | `pac copilot extract-template` produces one agent template | `pac copilot create --templateFileName ...` creates a separate agent |

Run **Export Travel Concierge from Studio** (`export-agent.yml`) on `main`, selecting `both`. It exports solution `ppdemo_ReleaseRadar` and extracts that agent's template. The files are available in the `travel-studio-export` artifact for three days. Live exports can contain environment content: review before sharing or committing them. This public workshop repository must contain synthetic demo content only.

Then run **Deploy Studio export (ZIP or YAML)** (`deploy-export.yml`):

1. Enter the successful export run ID.
2. Choose `solution` or `template`.
3. Leave `deploy` unchecked for artifact/provenance and connection checks, or check it to perform the deployment.
4. Open the resulting agent in Studio and test it. A green workflow means the PAC operation completed, not that the conversation passed.

Both workflows currently use the existing `copilot-studio-test` GitHub Environment and OIDC identity. **This is a same-environment workshop round trip, not a configured dev-to-production promotion.** ZIP import updates the existing solution/agent; YAML creates **Travel Concierge YAML** with schema `ppdemo_TravelTemplateDemo` inside the existing `ppdemo_ReleaseRadar` solution. That solution must already exist in the target.

Template creation is not an update operation: rerunning it after that schema exists should fail rather than delete or overwrite the agent. For repeated updates use the solution route or a separately configured clone/pull/push workspace. A template is not an entire Power Platform solution: do not assume external flows, connectors, connection references, environment variables or other dependencies are migrated. Validate those separately.

**Observed template limitation with PAC 2.13.1:** the live ZIP round trip retained all 16 agent components, including `GptComponentMetadata` with the authored instructions. The extracted YAML/create round trip produced 15 components and did **not** retain that GPT metadata component. The guided trip-planning topics worked in the template-created agent, but this is not a lossless generative-agent migration. Use the solution route when preserving that configuration is required; do not assume instructions or model settings survived template creation.

All these workflows share the same concurrency group to prevent overlapping export/import operations. Neither new workflow calls `pac copilot publish` or enables channels, but service-side provisioning/publication can occur; inspect Studio before using a created/imported agent.

## Source layout

### Promote a tested export to production

Run **Promote validated Studio export to production** (`promote-prod.yml`) on
`main` only after testing the selected artifact in the test environment:

1. Enter the export run ID and the successful `deploy-export.yml` test run ID.
2. Select the same format that deployed successfully in that test run.
3. Check `test_validated` to attest that functional testing passed.
4. The validation job checks workflow provenance, the successful format-specific
   PAC step and the test run's artifact-download reference. It then freezes the
   exported files and their SHA-256 in a promotion artifact; nothing is rebuilt.
5. Approve the **copilot-studio-prod** deployment in GitHub's **Review deployments**
   dialog. Only then does the production job receive its OIDC credentials and
   deploy the payload whose hash was verified.

Manual dispatch and a required GitHub Environment review are two separate gates.
Functional testing is a human attestation, not an automated conversation test.
The evidence check currently reads the pinned download action's `run-id` log line;
if logs are expired or that format changes, it fails closed. Rerun test deployment
to supply new evidence instead of skipping validation.

Configure `copilot-studio-prod` with the same four `PP_*` secret names as test,
but production-specific values and a separate Entra deployment application.
Its federated credential must trust only this repository's production environment
subject. Add a Dataverse application user in production with **System Customizer**.
Restrict deployment branches to `main`, require reviewer **Ch0wseth** and disable
administrator bypass. Self-review must remain allowed for this single-user workshop;
in a team, prevent self-review and require an independent reviewer. These GitHub
settings and secret values live outside Git; review them in repository settings.

ZIP promotion uses the exact **unmanaged** workshop ZIP that passed test, supporting
repeat imports. This is not a managed-solution production ALM design. For real
production, build a managed release and test that same managed artifact before
promotion, with connection/environment-variable settings and rollback planning.
YAML promotion creates `ppdemo_TravelTemplateDemo` once; the containing
`ppdemo_ReleaseRadar` solution must exist (promote ZIP first for this demo). A second
YAML creation with that schema is expected to fail, not overwrite production.
The template's documented loss of GPT metadata still applies in production.
No workflow explicitly publishes agents or enables channels; service-side
provisioning can change publication state, which must be reviewed in Studio.

```text
agent/
  agent.mcs.yml
  settings.mcs.yml
  topics/                 # Guided trip planner, booking boundaries, system topics
scripts/
  stabilize_solution_prefix.py
.github/workflows/
  package-agent.yml       # Stable PAC CLI solution package; no deployment
  deploy-agent.yml        # Manual OIDC import; no explicit publish command
  export-agent.yml        # Export live solution ZIP and/or agent template YAML
  deploy-export.yml       # Import ZIP or create another agent from template YAML
  promote-prod.yml        # Manual dispatch + test evidence + production approval
```

## References

- [PAC CLI: `pac copilot init` and `pac copilot pack`](https://learn.microsoft.com/power-platform/developer/cli/reference/copilot)
- [Copilot Studio extension for Visual Studio Code](https://learn.microsoft.com/microsoft-copilot-studio/visual-studio-code-extension-overview)
- [Export and import agents using solutions](https://learn.microsoft.com/microsoft-copilot-studio/authoring-solutions-import-export)
- [PAC CLI authentication and GitHub federation](https://learn.microsoft.com/power-platform/developer/cli/reference/auth)
- [OIDC/FIC for Power Platform GitHub Actions](https://learn.microsoft.com/power-platform/alm/tutorials/github-actions-oidc-fic)
