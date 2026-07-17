# ADR 018 — Mono-Repo: Application Code, Deployment Config, and Infrastructure in One Repository

**Status:** Accepted (documents a decision made incrementally since project start, written down 2026-07-05)
**Date:** 2026-07-05

---

## Context

This repository contains three kinds of artifacts that GitOps literature often separates:

- **Application code** (`etl/`, `03-gold/`, `03-gold-dash/`)
- **Deployment configuration** (`deployment/*.yml` — the Compose files Portainer pulls)
- **Infrastructure as code** (`infra/q-vm/` — Terraform for the Q VM)

Yuen et al. explicitly recommend the opposite: a **separate Git repository for deployment
config**, kept apart from application source (*GitOps and Kubernetes*, §3.2, pp. 68–69). Their
reasons: config-only changes shouldn't trigger CI builds; a config-only repo has a cleaner audit
history; apps composed from multiple source repos deploy as one unit; **access separation**
(who may commit code ≠ who may change production config); and avoiding CI/CD trigger loops.

Salecha demonstrates the opposite model: one repository with application code and an `infra/`
folder for Terraform side by side (*Practical GitOps*, ch. 5, pp. 181–182). Richards/Ford note
that keeping architecture records and code in the same repository is common practice, with the
caveats aimed at **larger organizations** (*Fundamentals of Software Architecture*, 2nd ed.,
ch. 21, pp. 400–401).

## Decision

**One repository holds everything: application code, deployment config, infrastructure code,
and documentation.** No separate config or infra repository.

## Rationale

Each of Yuen's five reasons for splitting was checked against this project — none applies at
the current size:

1. *Config changes triggering unwanted builds* — prevented by `paths:` filters in
   `.github/workflows/build-push.yml`; a Compose-only change builds nothing.
2. *Cleaner audit history* — at this commit volume, `git log -- deployment/` answers the same
   question a dedicated repo would.
3. *Multi-repo applications* — does not apply; all services live here already.
4. *Access separation* — there is no separate operations group; the people who write code are
   the people who deploy.
5. *CI/CD trigger loops* — Portainer **polls** this repo; it never commits back, so no loop is
   possible.

Against that, the mono-repo has one decisive advantage for a small team: **a change to a service
and the change to how it is deployed land in the same PR**, reviewed together, atomically
revertable together (e.g. a new env var in code plus the corresponding `environment:` entry in
the Compose file).

## Consequences

- One PR can change code, deployment config, and infra consistently; one audit trail.
- Portainer stacks and CI workflows reference paths inside this repo — no cross-repo
  coordination.
- Deployment-config commits share history with feature commits; filtering is done with paths,
  not repo boundaries.
- **Revisit trigger:** if the team grows to the point where production-config access must be
  restricted to a subset of committers, the config split from *GitOps and Kubernetes* §3.2
  becomes relevant — that boundary, not repo size, is the signal.

## References

- *GitOps and Kubernetes* — Yuen et al., §3.2 "Git strategies", pp. 68–69
- *Practical GitOps* — Salecha, ch. 5 (mono-repo with `infra/` working directory), pp. 181–182
- *Fundamentals of Software Architecture* — Richards/Ford, 2nd ed., ch. 21 "Architectural
  Decisions", pp. 400–401
- Repo-internal layout: [ADR 010](010-repo-layout-knowledge-vs-pipeline.md),
  [ADR 011](011-layer-named-folders-connector-abstraction-ml.md)
