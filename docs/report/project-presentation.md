# Project presentation - development, infrastructure, DevOps, and operations segment

## Scope, goal, and highlights

**Audience:** the jury for the final DataScientest data-engineering project defense. The audience
has seen the business problem and data pipeline before this segment; this part must prove that the
team can plan, develop, review, deploy, secure, and operate that pipeline as one coherent system.

**Format:** one presenter, exactly **5 minutes**, as one segment of the team's three-presenter
defense. Use **5 slides** at 16:9. This document is a content and visual specification, not the
finished deck.

**Scope:** the **development model** and **operating model** around the data platform: lightweight
project management in the public GitHub Project; issues, branches, pull requests, reviews, and
ADRs; infrastructure, AWS Lightsail, Terraform, AWS CLI/operator access, managed databases,
containerization, GitHub Actions, CI/CD, Portainer, Git-driven operations, Cloudflare Tunnel and
its remote API configuration, security/SecOps, and day-two operations. The data science, ML, and
detailed transformation logic belong to the other presenters except where a database or deployment
boundary needs context.

**Goal:** defend the development and operating model through project evidence. The section should
answer five jury questions:

1. How does a three-person team turn an idea into visible, owned, reviewable work?
2. What is the shared source of truth from planning through production?
3. What happens between a pull request and a running Q or production deployment?
4. Which infrastructure and security boundaries reduce drift, exposure, and credential risk?
5. What operates reliably today, and which gaps are honestly acknowledged?

**Highlights to land:**

- **Everything as Code — One Source of Truth:** GitHub is the shared system of record. The Project
  plans work; issues, pull requests, and ADRs explain decisions; the repository stores versioned
  code and configuration; and `main` defines the deployable production state.
- The public GitHub Project is the team's lightweight development-control surface: Kanban for flow,
  Roadmap for timing, and linked issues/pull requests for traceability from intent to implementation.
- MongoDB Atlas preserves heterogeneous raw snapshots; Supabase Postgres exposes the stable
  relational serving contract.
- Production and Q use separate AWS Lightsail compute. The Q VM, static IP, and firewall are
  reproducible with Terraform; the production VM predates that IaC.
- GitHub Actions builds container images in CI and publishes them to GHCR. Nothing is compiled on
  the VMs.
- Application-code pull requests matching the workflow path filters become running Q previews
  through the Portainer API; production follows `main` through Portainer's Git polling. Compose,
  Portainer, documentation, and infrastructure-only changes are not previewed by that workflow.
- Cloudflare Tunnel removes inbound HTTP/HTTPS ports and TLS operations from the VMs. Secrets stay
  outside Git and outside Lightsail user data.
- The project applies serious operating principles without adding Kubernetes to a small,
  single-host-per-environment platform.

**One-sentence storyline:**

> Everything as Code — One Source of Truth: one visible path connects the idea, the reviewed
> change, the deployable state, and the running data product.

### Curriculum alignment

The locally supplied course plan (`APR26 PP BDE.pdf`, p. 2) makes this segment directly relevant to
the defense:

| Course area | Project evidence used in this segment |
|---|---|
| Sprint 3 - SQL and MongoDB | MongoDB Atlas Bronze plus Supabase Postgres Silver |
| Sprint 5 - ETL and AWS Cloud Practitioner | Managed data services and AWS Lightsail compute |
| Sprint 7 - DevOps / isolation | Docker, FastAPI health endpoints, environment separation, API security |
| Sprint 8 - CI/CD | GitHub Actions, GHCR, PR previews, release flow |
| Sprint 9 - monitoring and Terraform | Health checks, restart/logging policy, Terraform-managed Q infrastructure |

Kubernetes, Prometheus, and Grafana are course topics, but not implemented platform components.
That distinction should be explicit rather than hidden behind a technology logo wall.

## Recommendation: five slides for five minutes

| Slide | Time | Narrative job |
|---|---:|---|
| 1. Development + operating model | 0:00-0:35 | Establish the slogan and the single path from idea to running system |
| 2. Lightweight project management | 0:35-1:30 | Show how the public GitHub Project makes work, ownership, timing, and evidence visible |
| 3. Delivery flow | 1:30-2:40 | Show application-code PR, CI, Q deployment, review, merge, and production as one flow |
| 4. Control boundaries + SecOps | 2:40-3:45 | Connect Terraform, AWS, containers, Portainer, Cloudflare, and security controls |
| 5. Operations and limits | 3:45-4:45 | Prove day-two operation, acknowledge gaps, and finish with the takeaway |
| Transitions and contingency | 0:15 | Absorb slide changes, one breath, and the handoff to the next presenter |
| **Total** | **5:00** | |

Five slides are preferable to the previous twelve-slide infrastructure deck. At normal defense
pace, twelve slides force tool enumeration; five slides leave enough time to explain decisions,
trade-offs, and evidence. Rehearse **4:45 of spoken content**, not five minutes of uninterrupted
copy; the remaining 15 seconds are an intentional delivery buffer.

## Accuracy rules for the presenter and deck builder

Use consistent status labels wherever a diagram mixes different maturity levels:

- **Running today** - verified in current architecture/deployment documentation.
- **Tracked configuration** - present in the repository, but not proof of a live resource by itself.
- **Manual bootstrap/operator action** - intentionally outside automation.
- **Next hardening step** - not implemented and never shown as current state.

Do not make the following claims:

| Avoid this claim | Accurate wording |
|---|---|
| "Everything is code." | **Everything as Code** is the operating principle: work, decisions, code, and deployable configuration are versioned or linked in GitHub. Secrets, live telemetry, manual trust bootstrap, and some remote configuration remain outside Git. |
| "One Source of Truth means one file contains everything." | GitHub is the shared system of record: the Project tracks work, issues/PRs/ADRs preserve context, and `main` defines deployable state. Each concern still has an explicit owner. |
| "The Project board proves formal Scrum." | It is deliberately lightweight project management: Kanban flow, a roadmap, ownership fields, and links between work items and implementation. Do not invent ceremonies or metrics that are not evidenced. |
| "Every historical merge has a submitted approval." | ADR 012 defines second-person review as team policy, and PR #9 demonstrates requested changes followed by approval. Do not generalize that evidence to every historical PR. |
| "All infrastructure is Terraform-managed." | Terraform manages the Q Lightsail VM, static IP, and firewall; production was created manually. |
| "One exact image moves from PR to production." | Images are built in CI and never on a VM, but the current workflow rebuilds after merge instead of promoting the tested PR digest. |
| "Q deployment is pure GitOps." | Q is API-triggered CD through Portainer; production has the pull-based, Git-driven configuration path from `main`. |
| "GitHub Actions runs the full test suite." | Current CI validates and publishes container builds; lint, unit-test, and security-scan gates are the next layer. |
| "Q is fully isolated." | Compute and Postgres are separated; Q deliberately shares the production MongoDB collections. |
| "The VMs have zero open ports." | They have zero inbound **web** ports. SSH remains; Q also exposes the Portainer-agent port only to the production VM. |
| "Cloudflare configuration is infrastructure as code." | Tunnel routing is remotely managed through Cloudflare's API/dashboard and is currently outside Git/Terraform. |
| "AWS CLI deploys the application." | The AWS CLI can provide authenticated operator inspection; Terraform calls the AWS API for Q provisioning, and Portainer deploys applications. |
| "MongoDB TTL is created by the ingestion code." | The code stores BSON timestamps suitable for TTL, but the current repository does not create a TTL index. Do not put a TTL duration on a slide. |

## Slide 1 - Everything as Code — One Source of Truth

**Time:** 35 seconds

**Purpose:** frame this segment as one combined development and operating model. The jury should
understand the organizing principle before seeing any individual tool.

### Exact on-slide text

**Eyebrow:** `OUR WORKING PRINCIPLE · DEVELOPMENT MODEL + OPERATING MODEL`

**Title:** `Everything as Code — One Source of Truth`

**Subtitle:** `From idea to running data product`

**Development band:**

```text
GitHub Project → issue → branch → application-code PR → Q preview → review → main
```

**Operations band:**

```text
selected PR → Actions/GHCR → Q via Portainer API
main → Actions → GHCR:latest
production ← main config via Portainer · GHCR:latest via Docker
```

**Infrastructure/edge rail:** `Terraform → Q infrastructure · Cloudflare Tunnel → edge`

**Data rail:** `MongoDB Atlas · Bronze → ETL → Supabase Postgres · Silver`

**Footer:** `Plan · review · provision · package · deploy · operate`

Do not add a vendor-logo row or a definition paragraph. The slogan, the two linked bands, and the
data rail are the complete argument.

### Visual specification

Create one continuous lifecycle with `main` as the visual hinge:

```text
DEVELOPMENT MODEL                                  OPERATING MODEL
Project -> Issue -> app PR -> CI/Q -> Review -> MAIN -> CI artifact + polled config
              GitHub system of record               \-> production pulls latest -> Operate

RUNNING PRODUCT: Atlas Bronze -> Postgres Silver -> API/Dashboard -> Cloudflare edge
```

- Put a bracket labelled `GitHub system of record` around Project, issue, PR, ADRs, repository, and
  `main`. This means connected authority, not one giant file or database.
- Give `main` a stronger shape or color: it is the bridge from reviewed development work to the
  deployable production state.
- Keep the runtime rail compact: managed databases, two Lightsail environments, containers, and
  outbound Cloudflare Tunnel. Detailed topology belongs on slide 4.
- Add one tiny boundary note below the bracket: `Secrets and live telemetry stay outside Git`.
- Use arrows for information flow; do not imply that Terraform deploys the containers or that
  GitHub stores the live database state.

**Recommended assets:** `github.svg` as the only dominant mark. Use small `mongodb.svg`,
`postgresql.svg`, `aws.svg`, and `cloudflare.png` marks only if the lifecycle remains readable.

### Speaker beats

1. "Everything as Code" is the team's working principle: plans, decisions, code, infrastructure,
   container definitions, and delivery workflows should be visible, reviewable, and reproducible.
2. "One Source of Truth" means one connected GitHub system of record: the Project shows intended
   work, issues and PRs preserve context, the repository stores the implementation, and `main`
   represents deployable production state.
3. This connects development and operations without a handoff gap: a matching application-code PR is
   built and previewed on Q before approval; after merge, `main` defines the production path.

### Evidence and references

- Project: [public GitHub Project](https://github.com/users/MatthiasSails/projects/1),
  [ADR 012](../adr/012-github-flow-branch-merge.md),
  [`docs/architecture/README.md`](../architecture/README.md),
  [`deployment/README.md`](../../deployment/README.md).
- Book grounding: *The DevOps Handbook* (Gene Kim et al.), ch. 8, PDF 163-164 (printed-page
  mapping unavailable in the local index):
  relevant development and operations work should share a visible board so the whole path to
  production can be seen.

## Slide 2 - From idea to reviewed change

**Time:** 55 seconds

**Purpose:** defend the team's deliberately small development model. This is project management as
an engineering control: visible priorities, explicit ownership, and evidence that work reached the
repository through review.

### Exact on-slide text

**Title:** `From idea to reviewed change`

**Proof ribbon:** `Public GitHub Project · Kanban + Roadmap`

**Evidence chips:**

- `TRACE · Issue #15 → linked PR #20 → Done`
- `REVIEW · PR #9 → changes requested → approved → merged`

**Footer:** `Visible work → linked change → reviewed merge`

Do not add a second process diagram. Explain `issue → owner → branch → PR → review → merge`
verbally while the evidence is visible.

### Visual specification

Use a real, sanitized capture of the public
[Airline Project](https://github.com/users/MatthiasSails/projects/1) as the central evidence visual,
not a generic Kanban illustration. Keep the composition to two zones: the board and a compact
trace/review evidence stack.

- Show the four board columns `Ideas`, `Todo`, `In Progress`, and `Done` on the left. Keep
  `Roadmap` as a small view tab or label; do not add a second full screenshot.
- On the right, stack two small evidence crops. First, use the public history of
  [issue #15](https://github.com/MatthiasSails/airline-data-platform/issues/15): assignment and
  `Todo → In Progress → Done`, linked to merged
  [PR #20](https://github.com/MatthiasSails/airline-data-platform/pull/20). A thin arrow should end
  at `main`. Summarize the item as `fallback source`; do not reproduce its typo-bearing title.
- The second crop should show only the review events from
  [PR #9](https://github.com/MatthiasSails/airline-data-platform/pull/9): `changes requested`, then
  `approved`, then `merged`. Crop out the PR body and infrastructure/access details.
- The Project and example issue were accessible while signed out on **2026-07-21**. Recapture the
  board immediately before export, but omit volatile item counts from the argument.
- Crop browser chrome and omit account controls. Do not expose issue text containing infrastructure
  identifiers, secrets, or other private operational details even if an item is publicly visible.

**Recommended asset:** `github.svg` as a small platform identifier. The board itself is the visual.

### Speaker beats

1. This is intentionally not a heavyweight project-management framework. One public Project gives
   the three-person team a shared Kanban view for flow and a Roadmap view for timing.
2. An idea becomes a draft or issue, gains a status and owner, and then moves into a short-lived
   feature branch. That makes work visible before code exists.
3. Two public histories make the controls concrete: issue #15 shows assignment, board movement,
   and a linked merged PR; PR #9 shows review feedback, a correction cycle, approval, and merge.
   ADR 012 turns that second-person review into team policy.
4. Development and operations work live on the same board. Infrastructure, CI, security, database,
   and deployment items are therefore part of product delivery rather than hidden side work.

### Evidence and references

- Project: [public GitHub Project](https://github.com/users/MatthiasSails/projects/1),
  [issue #15](https://github.com/MatthiasSails/airline-data-platform/issues/15), and
  [merged PR #20](https://github.com/MatthiasSails/airline-data-platform/pull/20) for traceability;
  [PR #9](https://github.com/MatthiasSails/airline-data-platform/pull/9) for submitted review
  evidence. Inspected signed out on 2026-07-21; [ADR 012](../adr/012-github-flow-branch-merge.md).
- Official verification: [GitHub - About Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects),
  [GitHub - Linking a pull request to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
- Book grounding: *The DevOps Handbook* (Gene Kim et al.), ch. 2, PDF 55-56, and ch. 8,
  PDF 163-164 (printed-page mapping unavailable in the local index): visual boards make queues and
  blocked work visible; shared boards also prevent operations work from disappearing outside the
  product value stream.

## Slide 3 - Application-code PRs become running Q previews

**Time:** 70 seconds

**Purpose:** this is the hero slide. Explain GitHub Flow, GitHub Actions, CI, CD, GHCR, Q, and the
production pull path as one sequence, while making the workflow path-filter boundary explicit.

### Exact on-slide text

**Title:** `Application-code PRs become running Q previews`

**Flow labels:**

```text
feature branch
  → pull request matching application paths
  → GitHub Actions build
  → GHCR: pr-N + sha-*
  → Portainer API deploys Q
  → review the running system + approve
  → squash merge
  → main build: latest + sha-*
  → Portainer polls main; production pulls GHCR:latest
```

**Three legend labels:**

- `CI · build and publish container images`
- `CD · API-triggered Q deployment`
- `GIT-DRIVEN OPS · Portainer polls main configuration`

**Bottom callout:** `The VMs pull images; they never build application code.`

### Visual specification

Use one horizontal pipeline with three colored bands behind the relevant stages: CI, CD to Q, and
the production pull path. Split the flow after GHCR into two environment lanes:

- **Q lane:** `pr-N` image tag → Portainer API → Q Compose stacks → `q_map1`.
- **Production lane after merge:** `latest` → Portainer Git polling → production stacks → `map1`.
  Keep `sha-*` beside GHCR as a traceability tag, not as the current production deployment input.

Add three small honesty annotations, not a large limitations box:

- `Q MongoDB is shared with production` beside the Q data lane.
- `Rebuild after merge; no sequenced production deploy job` beside the production image.
- `Workflow filters: selected application/Dockerfile/build-workflow paths` beside the PR trigger.
  Compose, Portainer, documentation, and Terraform-only changes do not receive a pre-merge Q
  preview.

The GitHub Flow image in `docs/images/` is not suitable as the primary visual: it only explains
branch review and omits artifacts, Q, and deployment. Build a project-specific flow instead.

**Recommended assets:** `github.svg`, `docker.svg`, `portainer.png`, `gitops.svg`. Treat the GitOps
icon as a legend marker for the pull path, not as a blanket label over the whole slide.

### Speaker beats

1. An application-code pull request matching the workflow paths triggers the same container build
   definitions used on `main`; GHCR receives a PR tag for convenience and a commit-derived tag for
   traceability.
2. Only after every Q image has built does the workflow call the Portainer API to change Q's
   `IMAGE_TAG`. Q reuses almost all production Compose definitions and selects `q_map1` by
   configuration; its landing page is the deliberate exception.
3. The running integration environment is available before approval, so human review can include
   Q. After merge, Actions publishes GHCR `latest`, while Portainer independently polls Compose
   configuration from `main`; production pulls `latest`. `sha-*` remains available for
   traceability.
4. Be exact about maturity: the workflow currently proves container builds, not the complete unit,
   lint, and security-test pyramid; and it rebuilds on `main` instead of promoting the exact tested
   PR digest.

### Evidence and references

- Project: [`.github/workflows/build-push.yml`](../../.github/workflows/build-push.yml),
  [`.github/workflows/q-reset.yml`](../../.github/workflows/q-reset.yml),
  [`deployment/scripts/set-q-image-tag.sh`](../../deployment/scripts/set-q-image-tag.sh),
  [ADR 012](../adr/012-github-flow-branch-merge.md), [ADR 018](../adr/018-mono-repo.md).
- Book grounding: *Continuous Delivery* (Jez Humble and David Farley), ch. 5 "Anatomy of the
  Deployment Pipeline," pp. 113-115 (PDF 147-149): build an artifact once, trace it to its commit,
  and deploy that same artifact in every environment.
- Book grounding: *GitOps and Kubernetes* (Billy Yuen et al.), ch. 1, pp. 5-12 (PDF 27-34): GitOps
  stores desired state in Git and uses an operator to synchronize actual state; section 3.4,
  pp. 82-84 (PDF 104-106), distinguishes durable environments from short-lived previews.
- Official verification: [OpenGitOps principles](https://opengitops.dev/blog/1.0-announcement/),
  [GitHub - Publishing Docker images](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images).

## Slide 4 - Code-defined boundaries reduce operational risk

**Time:** 65 seconds

**Purpose:** make infrastructure ownership and SecOps one causal story. Each tool controls a
specific boundary; the boundaries make drift, exposure, and secret movement easier to reason about.

### Exact on-slide text

**Title:** `Code-defined boundaries reduce operational risk`

| `PROVISION` | `RUN` | `EDGE` |
|---|---|---|
| `Terraform + AWS API` | `Portainer + Compose` | `Cloudflare Tunnel` |
| `Q VM · static IP · firewall` | `Pull GHCR images · configure · restart · observe` | `Outbound-only ingress · API/dashboard rules` |

**Security strip:** `No secrets in Git/user data · zero inbound web ports · scoped image-build permissions`

**Operator note:** `AWS CLI = authenticated inspection capability, not deployment engine`

**Known gaps:** `Production VM + Cloudflare routing outside IaC · Atlas permits all source IPs`

### Visual specification

Use three connected control-boundary cards across the upper two-thirds and a narrow security strip
below them. The arrows must reflect the actual ownership sequence:

```text
Terraform --AWS API--> Q Lightsail --manual trust bootstrap--> Portainer/Compose
GHCR --image handoff from slide 3--> Q + production containers
Q + production cloudflared --outbound tunnel--> Cloudflare edge --> users
```

- Draw Terraform around **Q only**: instance, static IP, and firewall. Put the pre-existing
  production VM beside, not inside, that boundary.
- Show `host bootstrap: swap + Docker; no secrets` in Lightsail user data and a dotted `post-boot
  SSH` path for the secret-bearing Portainer agent. This is a deliberate security boundary, not
  missing automation.
- Place the AWS CLI outside the delivery arrows as an operator lens into the AWS API.
- Show Cloudflare's hostname routes as `remote API/dashboard state`. Do not label current
  Cloudflare configuration as IaC.
- Use one amber exception panel for `Atlas 0.0.0.0/0` and the configuration outside IaC, but never
  show real IPs, hostnames, account IDs, project references, or secrets.

**Recommended assets:** `aws.svg`, `docker.svg`, `portainer.png`, `cloudflare.png`; use small
`mongodb.svg` and `postgresql.svg` marks only if there is room. A Terraform text tile is preferable
until the official logo asset is added. Do not substitute `ec2.svg` for Lightsail.

### Speaker beats

1. Terraform owns the reproducible Q infrastructure through the AWS provider API. The same
   credential profile gives the AWS CLI an authenticated operator-inspection path, but the CLI is
   not the deployment engine. Production predates this IaC boundary.
2. Slide 3 established packaging: GitHub Actions owns builds and GHCR owns artifacts. At this
   boundary, Portainer and versioned Compose files own the runtime lifecycle; a VM only pulls.
3. Secrets remain outside Git and Lightsail user data. The Portainer agent is installed after boot
   because user data is readable through instance metadata.
4. Cloudflare Tunnel removes inbound HTTP/HTTPS rules and VM-side TLS operations. The material
   exceptions remain visible: Cloudflare routing is remote state, and Atlas network access is still
   broad.

### Evidence and references

- Project: [`infra/q-vm/README.md`](../../infra/q-vm/README.md),
  [`infra/q-vm/main.tf`](../../infra/q-vm/main.tf),
  [`infra/q-vm/versions.tf`](../../infra/q-vm/versions.tf),
  [`infra/q-vm/user_data.sh`](../../infra/q-vm/user_data.sh),
  [`deployment/bronze.yml`](../../deployment/bronze.yml),
  [`deployment/silver.yml`](../../deployment/silver.yml), [ADR 019](../adr/019-cloudflare-tunnel-ingress.md),
  [`docs/mongodb-access.md`](../mongodb-access.md).
- Book grounding: *Terraform: Up & Running*, 3rd ed. (Yevgeniy Brikman), ch. 1 "Why Terraform,"
  PDF 51-54 (printed-page mapping unavailable): declarative configuration belongs in version
  control and providers communicate with cloud APIs.
- Book grounding: *Building Secure and Reliable Systems* (Heather Adkins et al.), ch. 5 "Design
  for Least Privilege," pp. 62-65 (PDF 98-101): network location alone is not trust, and access
  should be limited to the smallest functional interface.
- Official verification: [HashiCorp - Infrastructure as Code with Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/infrastructure-as-code),
  [AWS - Lightsail instance metadata and user data](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-instance-metadata.html),
  [AWS - Lightsail firewalls and ports](https://docs.aws.amazon.com/lightsail/latest/userguide/understanding-firewall-and-port-mappings-in-amazon-lightsail.html),
  [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/).

## Slide 5 - Operational proof today, hardening path tomorrow

**Time:** 60 seconds

**Purpose:** close with evidence of day-two operation, then show a short, prioritized improvement
path. The last spoken sentence must resolve the section's storyline.

### Exact on-slide text

**Title:** `Operational proof today, hardening path tomorrow`

| `OPERATES TODAY` | `NEXT HARDENING STEPS` |
|---|---|
| `ETL heartbeat + API health checks` | `Unit, lint, image-scan and SBOM gates in CI` |
| `Restart policies + local container logs` | `Promote the tested image digest after merge` |
| `Independent Bronze/Silver lifecycles` | `Central metrics, alerts, and log aggregation` |
| `Separate production/Q compute` | `Isolate Q MongoDB; bring Cloudflare and prod under IaC` |

**Small decision note:** `Docker Compose is sufficient at this scale; Kubernetes would add an
operations platform before the project needs one.`

**Final takeaway:**

> Everything as Code — One Source of Truth.

### Visual specification

Use a clean two-column maturity board. The left column is dark blue/green and concrete; the right
column is light/amber and clearly future work. Add a small heartbeat line behind the left heading.
A subtle feedback arrow returns the right-hand gaps to a `GitHub Project` card labelled
`visible work`, closing the loop from operations back into development. Do not use vendor logos on
this slide.

Prioritize the four right-column items in the order shown. Do not add a generic backlog, cost
estimates, or technologies that have no direct relationship to an identified gap.

### Speaker beats

1. Operation is encoded: the ETL containers expose file-heartbeat health checks, APIs expose HTTP
   health endpoints, and Compose defines restart and logging behavior.
2. Lifecycle boundaries matter: Bronze can respect source limits while Silver refreshes faster;
   one failure does not terminate both loops.
3. Health checks and local logs are not centralized observability. The next course-aligned step is
   metrics, alerting, and log aggregation, preceded by automated quality and supply-chain gates.
4. Operational gaps return to the same visible Project instead of becoming hidden work. Close with
   the architectural judgment: a three-person project can adopt reproducibility, review, least
   privilege, and feedback without pretending that it needs Kubernetes.

### Evidence and references

- Project: [`deployment/bronze.yml`](../../deployment/bronze.yml),
  [`deployment/silver.yml`](../../deployment/silver.yml),
  [`deployment/gold-dash.yml`](../../deployment/gold-dash.yml),
  [ADR 015](../adr/015-etl-scheduling-docker-loop.md),
  [project scope](../requirements/scope.md).
- Book grounding: *Microservices Patterns* (Chris Richardson), section 11.3 "Designing observable
  services," pp. 365-369 (PDF 395-399): health endpoints and useful logging make services
  operable, while monitoring and log aggregation remain separate operational capabilities.
- Official verification: [Docker - Use Compose in production](https://docs.docker.com/compose/how-tos/production/).

## Visual system and asset plan

### General composition

- Use a consistent 16:9 grid, one dominant visual per slide, and no more than 30-35 words of body
  copy outside diagrams/callouts.
- Titles should be assertions, not topic labels: `Code-defined boundaries reduce operational risk`,
  not `DevOps tools`.
- Use project evidence in visuals: repository paths, image tags, environment labels, and the
  public Project board or sanitized Lightsail screenshot. Never use real infrastructure
  identifiers.
- Color-code concepts consistently:
  - project planning and reviewed change: purple;
  - managed data: green;
  - AWS compute/IaC: orange;
  - CI/artifacts: navy;
  - Q: amber;
  - production: blue;
  - Cloudflare/security boundary: orange/yellow;
  - future work: light amber with a `NEXT` label.
- Logos identify technology; they are not the visual. Use at most four vendor marks on a slide.

### Existing logo review

| Asset | Use in this segment | Notes |
|---|---|---|
| `aws.svg` | Yes | Strong, clean wordmark for the compute/IaC context |
| `lightsail.jpg` | Optional | Recognizable but legacy artwork; prefer the sanitized console screenshot as evidence |
| `ec2.svg` | No | The deployed compute is Lightsail, not EC2 |
| `docker.svg` | Yes | Clear wordmark; use on the control-boundary slide |
| `github.svg` | Yes | Use for the Project, GitHub Flow, Actions, and GHCR as one platform mark |
| `gitops.svg` | Limited | Use only beside the pull-based production path |
| `cloudflare.png` | Yes | Suitable for the edge/security slide |
| `portainer.png` | Yes | Suitable resolution for a small control-plane mark |
| `mongodb.svg` | Yes | Pair with an `Atlas` text label |
| `mongodb-atlas.svg` | Crop first | Current view box makes the mark reproduce too small |
| `postgresql.svg` + `supabase.svg` | Yes | Pair the database engine and managed service; do not show both at full logo size |
| `redshift.svg` | No | Redshift is not part of the running platform |
| `kaggle.svg`, `opensky.png`, `adsb-lol.png`, `ads-b.svg` | No in this segment | They belong to data-source or ML sections |

**Missing asset:** an official Terraform/HashiCorp mark. Add it only from the official brand source
when the final visuals are produced; until then, a text tile is preferable to an unofficial mark.

## Source index and research basis

### Primary project sources

- [`README.md`](../../README.md)
- [Public GitHub Project - Airline Project](https://github.com/users/MatthiasSails/projects/1)
- [Issue #15](https://github.com/MatthiasSails/airline-data-platform/issues/15) and
  [merged PR #20](https://github.com/MatthiasSails/airline-data-platform/pull/20) for board-to-change
  traceability; [PR #9](https://github.com/MatthiasSails/airline-data-platform/pull/9) for review evidence
- [`docs/architecture/README.md`](../architecture/README.md)
- [`deployment/README.md`](../../deployment/README.md)
- [`.github/workflows/build-push.yml`](../../.github/workflows/build-push.yml)
- [`.github/workflows/q-reset.yml`](../../.github/workflows/q-reset.yml)
- [`deployment/scripts/set-q-image-tag.sh`](../../deployment/scripts/set-q-image-tag.sh)
- [`infra/q-vm/`](../../infra/q-vm/)
- [ADR 012 - GitHub Flow](../adr/012-github-flow-branch-merge.md)
- [ADR 015 - ETL scheduling](../adr/015-etl-scheduling-docker-loop.md)
- [ADR 018 - mono-repo](../adr/018-mono-repo.md)
- [ADR 019 - Cloudflare Tunnel ingress](../adr/019-cloudflare-tunnel-ingress.md)
- [`docs/mongodb-access.md`](../mongodb-access.md)
- [`logos/readme.md`](logos/readme.md)

### Books consulted through the local engineering library

- Kim, Gene, et al. *The DevOps Handbook*, ch. 2, PDF 55-56, and ch. 8, PDF 163-164
  (printed-page mapping unavailable in the local index).
- Kleppmann, Martin. *Designing Data-Intensive Applications*, 2nd ed., ch. 3 "Data Models and
  Query Languages," pp. 81-83 (PDF 105-107).
- Brikman, Yevgeniy. *Terraform: Up & Running*, 3rd ed., ch. 1 "Why Terraform," PDF 51-54
  (printed-page mapping unavailable in the local index).
- Yuen, Billy, et al. *GitOps and Kubernetes*, ch. 1, pp. 5-12 (PDF 27-34), and section 3.4
  "Durable vs. ephemeral environments," pp. 82-84 (PDF 104-106).
- Humble, Jez, and David Farley. *Continuous Delivery*, ch. 5 "Anatomy of the Deployment
  Pipeline," pp. 113-115 (PDF 147-149).
- Adkins, Heather, et al. *Building Secure and Reliable Systems*, ch. 5 "Design for Least
  Privilege," pp. 62-65 (PDF 98-101).
- Richardson, Chris. *Microservices Patterns*, section 11.3 "Designing observable services,"
  pp. 365-369 (PDF 395-399).

### Official external references checked

- [OpenGitOps principles](https://opengitops.dev/blog/1.0-announcement/)
- [GitHub - About Projects](https://docs.github.com/en/issues/planning-and-tracking-with-projects/learning-about-projects/about-projects)
- [GitHub - Linking a pull request to an issue](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue)
- [GitHub Actions - Publishing Docker images](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images)
- [HashiCorp - Infrastructure as Code with Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/infrastructure-as-code)
- [AWS Lightsail - Instance metadata and user data](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-instance-metadata.html)
- [AWS Lightsail - Firewalls and ports](https://docs.aws.amazon.com/lightsail/latest/userguide/understanding-firewall-and-port-mappings-in-amazon-lightsail.html)
- [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/)
- [Docker - Use Compose in production](https://docs.docker.com/compose/how-tos/production/)

## Final rehearsal checks

- Speak the section in **4:45-5:00**; target roughly 600-650 spoken words.
- The first 30 seconds must establish the shared development/operations lifecycle, not list tools.
- Capture the public Project while signed out immediately before export, omit volatile item counts,
  and crop out browser/account controls.
- Spend the most time on slide 3; it contains the end-to-end engineering proof.
- Say `zero inbound web ports`, never `zero open ports`.
- Say `API-triggered Q CD` and `pull-based production path`; do not flatten both into one GitOps
  label.
- State one implemented security control and one known risk without defensiveness.
- Do not expose private infrastructure details in diagrams, screenshots, speaker notes, or links.
- Finish exactly on the takeaway: `Everything as Code — One Source of Truth.`
