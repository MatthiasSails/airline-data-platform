# ADR 012 — GitHub Flow: Branching & Merge Strategy

**Status:** Accepted — team-confirmed 2026-06-23 (Slack)
**Date:** 2026-06-23
**Deciders:** Matthias, Pavel, Chaithra

---

## Context

With three developers working in parallel, we need one shared, simple rule for how a change moves
from a developer's machine into `main`. There was no written workflow before — changes reached `main`
ad hoc. The team wanted a reviewable, low-overhead process, not a heavyweight branching model.

---

## Decision

### Feature-branch workflow

We adopt a **feature-branch** workflow (GitHub Flow), as agreed by the team:

1. `main` is always deployable.
2. Each change is developed on a **short-lived branch** — `feature/<topic>` for a feature
   (e.g. `feature/new-dash-dashboard`), `fix/<topic>`, `chore/<topic>`.
3. Open a **Pull Request** for every change — **no direct pushes to `main`.** A second team member
   reviews; revisions happen on the branch until approved.
4. Once approved, the branch is **merged into `main` and deleted** — it is no longer needed.

This is the pull-request life cycle from *GitOps and Kubernetes* (Fig. 1.6): create branch → open PR
and request review → review and revise → maintainer merges → branch deleted.

### Merge strategy: Squash and merge

GitHub offers three merge strategies:

- **Create a merge commit** — every branch commit is kept individually, plus an extra "merge" commit
  tying the branches together. Full history is preserved, but `main`'s log gets noisier with small
  intermediate commits ("fix typo", "oops").
- **Squash and merge** — all branch commits collapse into a **single** commit added to `main`. Clean,
  linear history — one PR = one commit. Individual commit details are lost from `main`'s log (but stay
  visible in the PR).
- **Rebase and merge** — branch commits are replayed individually onto `main` without a merge commit,
  as if created there directly. Linear like squash, but each original commit stays separate.

**We use Squash and merge as the default:** one clean commit per PR on `main` instead of many small
intermediate steps. Rebase-and-merge is the alternative when preserving each individual commit
matters.

### Why not full Gitflow

Gitflow's author, Vincent Driessen, noted in 2020 that for teams doing continuous delivery of web
applications it adds unnecessary complexity. The feature-branch flow above is the right fit at our
scale.

---

## Out of scope — future, not yet adopted

A fuller CI/CD pipeline — automated test gates, a Q / staging environment, OIDC-based deploys, an
image registry, Terraform IaC, tag-based production releases (build-once / promote-artifact) — is a
plausible later direction but is **not** part of this decision. Deployment today is still manual via
Portainer GitOps on the deployment VM. Revisit when the team actually needs automated promotion; it
would warrant its own ADR.

---

## Consequences

- Every change to `main` is reviewed by a second person and lands as one squashed commit — clean,
  reviewable history.
- Low overhead, appropriate for a three-person learning project; no heavyweight Gitflow.
- Once configured, GitHub Branch Protection on `main` (require a PR + one approval) can enforce this.

---

## References

- *GitOps and Kubernetes* — Billy Yuen et al., Fig. 1.6 (pull-request life cycle), p. 119–127 (branching)
- [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow)
- [A successful Git branching model — Vincent Driessen](https://nvie.com/posts/a-successful-git-branching-model/) (why we do *not* adopt full Gitflow)
- ADR 007 — Decouple from Liora VM (current compute context)
