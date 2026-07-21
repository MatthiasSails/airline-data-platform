# Project presentation - infrastructure, DevOps, and operations segment

## Scope, goal, and highlights

**Audience:** the jury for the final DataScientest data-engineering project defense. The audience
has seen the business problem and data pipeline before this segment; this part must prove that the
pipeline is deployable, reviewable, secure by design, and operable by a three-person team.

**Format:** one presenter, exactly **5 minutes**, as one segment of the team's three-presenter
defense. Use **5 slides** at 16:9. This document is a content and visual specification, not the
finished deck.

**Scope:** infrastructure, AWS Lightsail, Terraform, AWS CLI/operator access, managed databases,
containerization, GitHub Flow, GitHub Actions, CI/CD, Portainer, Git-driven operations, Cloudflare
Tunnel and its remote API configuration, security/SecOps, and day-two operations. The data science,
ML, and detailed transformation logic belong to the other presenters except where a database or
deployment boundary needs context.

**Goal:** defend the operating model through project evidence. The section should answer five jury
questions:

1. Where does the system run, and why are the databases managed separately from compute?
2. Which tool owns infrastructure, artifacts, and runtime state?
3. What happens between a pull request and production?
4. Which security controls reduce exposure and credential risk?
5. What operates reliably today, and which gaps are honestly acknowledged?

**Highlights to land:**

- MongoDB Atlas preserves heterogeneous raw snapshots; Supabase Postgres exposes the stable
  relational serving contract.
- Production and Q use separate AWS Lightsail compute. The Q VM, static IP, and firewall are
  reproducible with Terraform; the production VM predates that IaC.
- GitHub Actions builds container images in CI and publishes them to GHCR. Nothing is compiled on
  the VMs.
- Pull requests become running Q previews through the Portainer API; production follows the
  `main` branch through Portainer's Git polling. These are related but distinct delivery paths.
- Cloudflare Tunnel removes inbound HTTP/HTTPS ports and TLS operations from the VMs. Secrets stay
  outside Git and outside Lightsail user data.
- The project applies serious operating principles without adding Kubernetes to a small,
  single-host-per-environment platform.

**One-sentence storyline:**

> We turned a live-data script into an operated data product by separating data, infrastructure,
> artifacts, runtime reconciliation, and public ingress into explicit control boundaries.

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
| 1. Operating model | 0:00-0:45 | Orient the jury: managed data, separate compute, protected ingress |
| 2. Control boundaries | 0:45-1:40 | Explain what Terraform, GitHub Actions, Portainer, and the AWS CLI each do |
| 3. Delivery flow | 1:40-2:55 | Show PR review, CI, Q deployment, merge, and production as one flow |
| 4. Security/SecOps | 2:55-4:00 | Connect network, secrets, identity, and data controls to concrete evidence |
| 5. Operations and limits | 4:00-5:00 | Prove day-two operation, acknowledge gaps, and finish with the takeaway |
| **Total** | **5:00** | |

Five slides are preferable to the previous twelve-slide infrastructure deck. At normal defense
pace, twelve slides force tool enumeration; five slides leave enough time to explain decisions,
trade-offs, and evidence.

## Accuracy rules for the presenter and deck builder

Use consistent status labels wherever a diagram mixes different maturity levels:

- **Running today** - verified in current architecture/deployment documentation.
- **Tracked configuration** - present in the repository, but not proof of a live resource by itself.
- **Manual bootstrap/operator action** - intentionally outside automation.
- **Next hardening step** - not implemented and never shown as current state.

Do not make the following claims:

| Avoid this claim | Accurate wording |
|---|---|
| "All infrastructure is Terraform-managed." | Terraform manages the Q Lightsail VM, static IP, and firewall; production was created manually. |
| "One exact image moves from PR to production." | Images are built in CI and never on a VM, but the current workflow rebuilds after merge instead of promoting the tested PR digest. |
| "Q deployment is pure GitOps." | Q is API-triggered CD through Portainer; production has the pull-based, Git-driven path from `main`. |
| "GitHub Actions runs the full test suite." | Current CI validates and publishes container builds; lint, unit-test, and security-scan gates are the next layer. |
| "Q is fully isolated." | Compute and Postgres are separated; Q deliberately shares the production MongoDB collections. |
| "The VMs have zero open ports." | They have zero inbound **web** ports. SSH remains; Q also exposes the Portainer-agent port only to the production VM. |
| "Cloudflare configuration is infrastructure as code." | Tunnel routing is remotely managed through Cloudflare's API/dashboard and is currently outside Git/Terraform. |
| "AWS CLI deploys the application." | The AWS CLI is operator tooling for authenticated inspection; Terraform calls the AWS API for Q provisioning, and Portainer deploys applications. |
| "MongoDB TTL is created by the ingestion code." | The code stores BSON timestamps suitable for TTL, but the current repository does not create a TTL index. Do not put a TTL duration on a slide. |

## Slide 1 - A production-minded operating model for a small data platform

**Time:** 45 seconds

**Purpose:** bridge from the data pipeline section into infrastructure. The jury should understand
the entire deployment topology before hearing tool details.

### Exact on-slide text

**Eyebrow:** `INFRASTRUCTURE · DEVOPS · OPERATIONS`

**Title:** `A production-minded operating model for a small data platform`

**Architecture labels:**

- `MongoDB Atlas` / `Bronze · raw snapshots`
- `Supabase Postgres` / `Silver · map1 serving contract`
- `AWS Lightsail` / `Production VM · Q VM`
- `Docker + Portainer` / `Application runtime`
- `Cloudflare Tunnel` / `Outbound-only public ingress`

**Bottom proof points:**

- `2 managed databases`
- `2 separate compute stages`
- `0 inbound web ports`

Do not add prose paragraphs. The labels and three proof points are the complete on-slide copy.

### Visual specification

Create one left-to-right topology with three zones:

```text
MANAGED DATA                    COMPUTE                         EDGE
MongoDB Atlas -> Postgres      Production VM | Q VM           Cloudflare
Bronze raw     -> Silver       Docker + Portainer             Tunnel -> users
```

- Make the two Lightsail instances visually separate, not two labels inside one server.
- Show data connections from both VMs to the managed databases, but do not draw every container.
- Use a tunnel arrow from each VM to Cloudflare pointing outward; no inbound 80/443 arrow.
- The sanitized project screenshot
  [`lightsail-instances.png`](images/lightsail-instances.png) may be used as a small evidence inset.
  It is stronger evidence than the legacy superhero artwork.
- Use `mongodb.svg` with the word `Atlas`; `mongodb-atlas.svg` has excessive whitespace in its
  current view box and will reproduce too small unless cropped.

**Recommended assets:** `mongodb.svg`, `postgresql.svg` plus `supabase.svg`, `aws.svg`,
`cloudflare.png`. Use at most four visible vendor marks; text labels carry the rest.

### Speaker beats

1. The databases are managed services because data durability and database operations are not the
   team's differentiator.
2. MongoDB accepts source-shaped raw data; Postgres gives consumers a predictable relational
   contract.
3. Compute is deliberately visible and reproducible: separate production and Q Lightsail VMs run
   the containers, while Cloudflare provides public ingress without VM web ports.

### Evidence and references

- Project: [`docs/architecture/README.md`](../architecture/README.md),
  [`deployment/README.md`](../../deployment/README.md),
  [`infra/q-vm/main.tf`](../../infra/q-vm/main.tf).
- Book grounding: *Designing Data-Intensive Applications*, 2nd ed. (Martin Kleppmann), ch. 3
  "Data Models and Query Languages," pp. 81-83 (PDF 105-107): schema-on-read fits heterogeneous
  externally controlled records; schemas are valuable for a stable, uniform contract.

## Slide 2 - Three control planes keep responsibilities explicit

**Time:** 55 seconds

**Purpose:** explain infrastructure, CI, containerization, Git-driven operations, and operator
tooling without presenting them as interchangeable buzzwords.

### Exact on-slide text

**Title:** `Three control planes keep responsibilities explicit`

| `1 · PROVISION` | `2 · PACKAGE` | `3 · RUN` |
|---|---|---|
| `Terraform` | `GitHub Actions` | `Portainer + Compose` |
| `Q VM · static IP · firewall` | `Build images · publish to GHCR` | `Pull · configure · restart · observe` |
| `AWS provider API` | `pr-N · sha-* · latest` | `One stack = one lifecycle boundary` |

**Footer:** `Provision → bootstrap trust → reconcile applications`

**Small operator callout:** `AWS CLI: authenticated inspection, not the deployment engine`

### Visual specification

Use three equal vertical cards connected by a thin arrow. Each card gets one dominant noun and one
simple icon. Under the Terraform card, draw a narrow dotted side path labelled `manual bootstrap`
to the Portainer card.

- Terraform card: show only **Q**. Do not put the production VM inside the Terraform boundary.
- Bootstrap callout: `Docker from user data; Portainer agent after boot over SSH`.
- Package card: show a container image moving into GHCR, not source code moving to a VM.
- Runtime card: show separate Bronze and Silver stack tiles to demonstrate independent cadence and
  failure boundaries; do not draw all services.
- Use a small lock beside the bootstrap path: `AGENT_SECRET never enters user data`.

**Recommended assets:** `aws.svg`, `github.svg`, `docker.svg`, `portainer.png`. A Terraform logo is
not currently present in `logos/`; use a restrained text tile for this draft or add the official
HashiCorp asset before producing the final deck. Do not substitute `ec2.svg` for Lightsail.

### Speaker beats

1. Terraform owns three AWS resources for Q: the Lightsail instance, its stable address, and the
   least-privilege firewall. The AWS provider calls the service API; the named AWS profile also
   supports operator checks through the CLI without credentials in Git.
2. First boot installs Docker only. A secret-bearing Portainer agent is bootstrapped afterward
   because Lightsail user data is readable from instance metadata.
3. Portainer then owns the application lifecycle from versioned Compose files. Bronze and Silver
   remain separate because they have different rates, health domains, and restart behavior.

### Evidence and references

- Project: [`infra/q-vm/README.md`](../../infra/q-vm/README.md),
  [`infra/q-vm/versions.tf`](../../infra/q-vm/versions.tf),
  [`infra/q-vm/user_data.sh`](../../infra/q-vm/user_data.sh),
  [`deployment/bronze.yml`](../../deployment/bronze.yml),
  [`deployment/silver.yml`](../../deployment/silver.yml).
- Book grounding: *Terraform: Up & Running*, 3rd ed. (Yevgeniy Brikman), ch. 1 "Why
  Terraform," PDF 51-54 (the library has no reliable printed-page map): declarative configuration
  belongs in version control and providers communicate with cloud APIs.
- Official verification: [HashiCorp - What is Infrastructure as Code with Terraform?](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/infrastructure-as-code),
  [AWS - Lightsail instance metadata and user data](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-instance-metadata.html).

## Slide 3 - Pull requests become running Q previews

**Time:** 75 seconds

**Purpose:** this is the hero slide. Explain GitHub Flow, GitHub Actions, CI, CD, GHCR, Q, and the
production pull path as one sequence, while using the terms precisely.

### Exact on-slide text

**Title:** `Pull requests become running Q previews`

**Flow labels:**

```text
feature branch
  → pull request + review
  → GitHub Actions build
  → GHCR: pr-N + sha-*
  → Portainer API deploys Q
  → review the running system
  → squash merge
  → main build: latest + sha-*
  → production pulls from main
```

**Three legend labels:**

- `CI · build and publish container images`
- `CD · API-triggered Q deployment`
- `GIT-DRIVEN OPS · production pulls main configuration`

**Bottom callout:** `The VMs pull images; they never build application code.`

### Visual specification

Use one horizontal pipeline with three colored bands behind the relevant stages: CI, CD to Q, and
the production pull path. Split the flow after GHCR into two environment lanes:

- **Q lane:** `pr-N` image tag → Portainer API → Q Compose stacks → `q_map1`.
- **Production lane after merge:** `latest`/`sha-*` → Portainer Git polling → production stacks →
  `map1`.

Add two small honesty annotations, not a large limitations box:

- `Q MongoDB is shared with production` beside the Q data lane.
- `Current pipeline rebuilds after merge` beside the production image.

The GitHub Flow image in `docs/images/` is not suitable as the primary visual: it only explains
branch review and omits artifacts, Q, and deployment. Build a project-specific flow instead.

**Recommended assets:** `github.svg`, `docker.svg`, `portainer.png`, `gitops.svg`. Treat the GitOps
icon as a legend marker for the pull path, not as a blanket label over the whole slide.

### Speaker beats

1. A pull request triggers the same container build definitions used on `main`; GHCR receives a PR
   tag for convenience and a commit-derived tag for traceability.
2. Only after every Q image has built does the workflow call the Portainer API to change Q's
   `IMAGE_TAG`. Q reuses production Compose definitions and selects `q_map1` by configuration.
3. Review therefore includes a running integration environment before merge. After merge,
   production follows `main` through Portainer's pull path.
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

## Slide 4 - Security comes from reducing trust and exposure

**Time:** 65 seconds

**Purpose:** turn the architecture into a SecOps story. Show implemented controls first, then two
material gaps. Avoid generic cybersecurity claims.

### Exact on-slide text

**Title:** `Security comes from reducing trust and exposure`

**Implemented controls:**

- `NETWORK` / `Cloudflare Tunnel · no inbound 80/443`
- `SECRETS` / `GitHub + Portainer secrets · never in Git or user data`
- `IDENTITY` / `Scoped workflow permissions · key-based SSH · DB roles`
- `DATA` / `map1/q_map1 allowlist · read-only serving API`

**Known exposure:**

- `Atlas network access currently permits all source IPs`
- `Cloudflare hostname rules live outside Git/Terraform`

**Next hardening:** `Narrow Atlas access · manage Cloudflare as code · scan and attest images`

### Visual specification

Use a shield-shaped or four-layer defense-in-depth visual on the left and a narrow amber
`Known exposure` panel on the right. The slide must show cause and effect:

- Cloudflare edge → outbound tunnel → loopback/local service.
- Q firewall: `22/tcp SSH`; `9001/tcp only from production VM`; no 80/443.
- Secret sources point into runtime configuration, never into repository or Lightsail metadata.
- Cloudflare routing is labelled `remote API/dashboard config`, followed by a dotted arrow to
  `future Terraform Cloudflare provider`.

Do not show real hostnames, IP addresses, account IDs, project references, token names with values,
or screenshots of secret/configuration pages.

**Recommended assets:** `cloudflare.png`, `aws.svg`, `github.svg`. Use icons for locks, keys, and
firewalls rather than additional vendor logos.

### Speaker beats

1. The largest network control is architectural: `cloudflared` dials out, so the public services do
   not require inbound HTTP/HTTPS firewall rules or certificates on the VM.
2. Infrastructure variables, Terraform state, application credentials, tunnel tokens, and
   Portainer API keys remain outside Git. User data deliberately contains no secret.
3. Least privilege appears in multiple layers: restricted Portainer-agent access, scoped GitHub
   package permissions, read-only serving access, and allowlisted SQL table identifiers.
4. The honest gaps are equally important: Atlas currently permits every source IP at the network
   layer, and Cloudflare routing is remote configuration that can drift from Git.

### Evidence and references

- Project: [ADR 019](../adr/019-cloudflare-tunnel-ingress.md),
  [`infra/q-vm/main.tf`](../../infra/q-vm/main.tf),
  [`docs/mongodb-access.md`](../mongodb-access.md),
  [`03-gold-dash/api/db.py`](../../03-gold-dash/api/db.py),
  [`deployment/q-cloudflared.yml`](../../deployment/q-cloudflared.yml).
- Book grounding: *Building Secure and Reliable Systems* (Heather Adkins et al.), ch. 5 "Design
  for Least Privilege," pp. 62-65 (PDF 98-101): network location alone is not trust, and access
  should be limited to the smallest functional interface.
- Official verification: [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/),
  [AWS - Control instance traffic with Lightsail firewalls](https://docs.aws.amazon.com/lightsail/latest/userguide/understanding-firewall-and-port-mappings-in-amazon-lightsail.html).

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

> Serious operating principles, intentionally small platform.

### Visual specification

Use a clean two-column maturity board. The left column is dark blue/green and concrete; the right
column is light/amber and clearly future work. Add a small heartbeat line behind the left heading.
Do not use vendor logos on this slide.

Prioritize the four right-column items in the order shown. Do not add a generic backlog, cost
estimates, or technologies that have no direct relationship to an identified gap.

### Speaker beats

1. Operation is encoded: the ETL containers expose file-heartbeat health checks, APIs expose HTTP
   health endpoints, and Compose defines restart and logging behavior.
2. Lifecycle boundaries matter: Bronze can respect source limits while Silver refreshes faster;
   one failure does not terminate both loops.
3. Health checks and local logs are not centralized observability. The next course-aligned step is
   metrics, alerting, and log aggregation, preceded by automated quality and supply-chain gates.
4. Close with the architectural judgment: a three-person project can adopt reproducibility,
   review, least privilege, and operational feedback without pretending that it needs Kubernetes.

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
- Titles should be assertions, not topic labels: `Three control planes keep responsibilities
  explicit`, not `DevOps tools`.
- Use project evidence in visuals: repository paths, image tags, environment labels, and the
  sanitized Lightsail screenshot. Never use real infrastructure identifiers.
- Color-code concepts consistently:
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
| `github.svg` | Yes | Use for GitHub Flow/Actions/GHCR as one platform mark |
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
- [GitHub Actions - Publishing Docker images](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images)
- [HashiCorp - Infrastructure as Code with Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/infrastructure-as-code)
- [AWS Lightsail - Instance metadata and user data](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-instance-metadata.html)
- [AWS Lightsail - Firewalls and ports](https://docs.aws.amazon.com/lightsail/latest/userguide/understanding-firewall-and-port-mappings-in-amazon-lightsail.html)
- [Cloudflare Tunnel](https://developers.cloudflare.com/tunnel/)
- [Docker - Use Compose in production](https://docs.docker.com/compose/how-tos/production/)

## Final rehearsal checks

- Speak the section in **4:45-5:00**; target roughly 600-650 spoken words.
- The first 30 seconds must contain the platform topology, not a list of tools.
- Spend the most time on slide 3; it contains the end-to-end engineering proof.
- Say `zero inbound web ports`, never `zero open ports`.
- Say `API-triggered Q CD` and `pull-based production path`; do not flatten both into one GitOps
  label.
- State one implemented security control and one known risk without defensiveness.
- Do not expose private infrastructure details in diagrams, screenshots, speaker notes, or links.
- Finish exactly on the takeaway: `Serious operating principles, intentionally small platform.`
