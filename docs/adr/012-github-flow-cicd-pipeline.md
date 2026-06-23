# ADR 012 — Branching Strategy and CI/CD Pipeline

**Status:** Accepted  
**Date:** 2026-06-23  
**Deciders:** Matthias, Pavel, Chaithra

---

## Context

The project currently runs deployments manually via Portainer GitOps on `aws-airline-1`.
There is no automated test gate, no formal code review process, and no staging environment
between development and production. As the team grows and the pipeline matures, this
creates risk: untested code can reach production with no friction, and there is no shared
understanding of how changes move from a developer's machine to the live system.

Three concerns drive this decision:

1. **Code quality and review** — with three developers, changes should require a second
   pair of eyes before reaching main.
2. **Deployment safety** — deployments should go through a quality/staging environment
   before production.
3. **Infrastructure as code** — Terraform (or equivalent) configuration should flow
   through the same pipeline as application code.

---

## Decision

### Branching model: GitHub Flow + hotfix pattern

We adopt **GitHub Flow** as described in the GitHub documentation. This is a Feature Branch
Workflow with four concrete rules added:

1. `main` is always deployable — it mirrors what is in production.
2. All work happens on short-lived branches (`feature/*`, `fix/*`, `chore/*`).
3. The Pull Request is the central collaboration mechanism — no direct pushes to `main`.
4. Branches are deleted after merge.

For production emergencies, we borrow the **hotfix pattern** from Gitflow: a `hotfix/*`
branch is cut directly from `main`, gets an expedited review, merges back to `main`,
and is deployed immediately.

**We explicitly do not adopt full Gitflow.** Vincent Driessen, the author of Gitflow,
stated in 2020 that for teams doing continuous delivery of web applications, Gitflow
introduces unnecessary complexity — GitHub Flow is the appropriate choice.

### Pull Request process

Every merge to `main` requires:
- At least **one approval** from a second team member
- **CI checks passing** (lint, tests — once implemented)
- No unresolved review comments

These rules are enforced via GitHub Branch Protection Rules on `main`.

### Deployment pipeline

We adopt the Cloud Native **build-once, promote-artifact** model:

```
[1] Push to feature/*
        │
        ↓
    CI: build Docker image, tag with commit SHA (sha-<commit>)
    Run automated tests against this image
        │
[2] PR approved + merged → main
        │
        ↓
    CI: retag same image → deploy automatically to Q-environment (AWS)
    No rebuild from source — same image that passed tests
        │
[3] Q environment passes (automated + manual verification)
        │
        ↓
    git tag v<MAJOR>.<MINOR>.<PATCH> on main
        │
        ↓
    CI: tag image as v<MAJOR>.<MINOR>.<PATCH> → deploy to Production
```

The image SHA is the stable identity. Tags are promotion gates, not rebuild triggers.

This satisfies the "Only Build Your Binaries Once" principle from *Continuous Delivery*
(Humble/Farley, p. 113–114): the binary that reaches production is exactly the binary
that was tested.

### Environments

| Environment | Trigger | Purpose |
|---|---|---|
| **Development** | Local / any branch | Each developer runs locally against the shared Supabase project (`dev` schema) |
| **Q (Quality)** | Auto on merge to `main` | First environment with external dependencies; functional + integration tests |
| **Production** | Manual `git tag vX.Y.Z` | Live system; requires Q sign-off |

### Infrastructure changes

Terraform (or equivalent IaC) changes follow the same pipeline. A `git tag v1.2.3`
fires both the application deploy and `terraform apply` for that environment.

### Moving from Portainer to GitHub Actions

The current Portainer GitOps pull model is replaced by GitHub Actions push-based
deploys via OIDC authentication (no stored AWS credentials; the OIDC trust pattern
is kept in the team's internal infra notes). Each GitHub Actions workflow:

1. Authenticates to AWS via OIDC (no stored credentials)
2. Builds and pushes the Docker image to ECR (or GHCR)
3. SSHes into the target EC2 instance and runs `docker compose pull && docker compose up -d`

Portainer remains installed during the migration but is no longer the deployment
authority once GitHub Actions workflows are active.

---

## Consequences

**Positive:**
- Every change to `main` has been reviewed by at least two people.
- The same artifact that was tested is what runs in production (no rebuild risk).
- Full audit trail: every production deploy maps to a specific image SHA and git tag.
- Rollback is deterministic: redeploy the previous image tag, no rebuild needed.
- Aligns with Cloud Native / CNCF GitOps principles (versioned, immutable, automated).

**Negative / risks:**
- Adds process overhead that slows down solo experimentation — acceptable for a
  team of three, but worth revisiting if the team shrinks.
- Q environment requires a second AWS instance (cost: ~$12/month if Lightsail).
- GitHub Actions OIDC setup and IAM role scoping is a one-time upfront investment.

**Resolved decisions:**
- **Supabase:** one shared Supabase project with separate `dev` / `q` / `prod` schemas — basic
  environment isolation without the cost and overhead of separate instances at this team size.
  Revisit if production data sensitivity or load grows.
- **Q deploy trigger:** automatic on every merge to `main` — consistent with the build-once /
  promote-artifact model; no manual gate between merge and Q.
- **Production tags:** restricted to the project lead (Matthias) via GitHub tag protection on `v*`.
- **Merge strategy:** Squash and merge — one commit per PR for a clean, linear history on `main`.

---

## References

- *GitOps and Kubernetes* — Billy Yuen et al., p. 119–127 (branching), p. 101–105 (environment promotion)
- *Continuous Delivery* — Humble/Farley, p. 113–114 (build-once principle)
- *The DevOps Handbook* — Gene Kim et al., p. 342–346 (GitHub Flow and peer review)
- [A successful Git branching model — Vincent Driessen](https://nvie.com/posts/a-successful-git-branching-model/) (Gitflow original + 2020 note)
- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
- Branching and Deployment Strategy — internal team reference (local, not in this repo) with full book citations
- ADR 007 — Decouple from Liora VM (context for current compute setup)
