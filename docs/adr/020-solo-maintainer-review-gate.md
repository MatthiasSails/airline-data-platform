# ADR 020 — Solo maintainer: CI replaces the second reviewer

**Status:** Accepted — 2026-11-19
**Deciders:** Matthias
**Supersedes:** the review clause of [ADR 012](012-github-flow-branch-merge.md). Everything else
in ADR 012 — feature branches, short-lived branches, squash-and-merge, no direct pushes to `main` —
stays in force.

---

## Context

ADR 012 was agreed by three people in June 2026 and requires that "a second team member reviews"
every pull request. That team no longer works on this repository. The rule did not lapse quietly;
it had already stopped being practised long before anyone wrote this down:

- Of the last 15 merged pull requests, **11 had zero reviews**.
- The last review by someone other than the author was **PR #9, merged 2026-06-24** — almost five
  months before this decision.
- Branch protection on `main` was never configured, so nothing enforced the rule anyway.

Meanwhile the rule had a cost. Because a pull request could not be merged without an approval that
would never come, pull requests accumulated: five were open on 2026-11-19, the oldest since
2026-07-15. Two of them (#42, #43) contained changes that would have taken the MongoDB Atlas
cluster down within hours, and they sat unexamined for four months — the review requirement
produced neither review nor safety, only delay.

A review requirement nobody can satisfy is worse than no requirement: it is ignored in practice
while still being cited in documentation, which makes the written process untrustworthy as a
whole.

---

## Decision

### The gate moves from a person to the pipeline

A change may merge when **CI is green**, not when a second person approves. Concretely:

1. **Pull requests stay.** They remain the unit of change, the CI trigger, the Q-preview trigger
   and the text of the squash commit. Only the human approval gate is removed.
2. **Self-review replaces peer review.** The author reads the complete diff before merging, as a
   deliberate step rather than as a side effect of writing it.
3. **Red is red.** A failing check blocks the merge and is investigated, not waved through. Where
   a check fails for reasons unrelated to the change — `deploy-q` while the Q environment is off —
   that is stated explicitly in the pull request before merging, and the check is fixed or made
   tolerant rather than habitually ignored.
4. **A pull request does not outlive the session that opened it.** It is merged or closed in the
   same working session, except when deliberately parked as a draft.

### What this does not change

`main` still receives changes only through a pull request and a squash merge. Direct pushes to
`main` remain out of bounds. The point of this ADR is that the pull request is a process and a
record, not a request for someone else's permission.

---

## Consequences

- **CI is now load-bearing, and it is thin.** The pipeline builds seven container images and runs
  no lint and no tests, although `ml/tests/` exists. "Checks passing" currently means "the images
  built". This was acceptable while a human reviewed; it is not sufficient as the only gate, and
  closing that gap is the natural follow-up to this decision (it is candidate (2) in
  `013-cicd-pipeline.draft.md`).
- **A green pipeline would not have caught PR #42.** That change was five lines, all checks green,
  and would have exhausted the Atlas quota in roughly 1.6 hours. Judgement about *consequences* is
  the part no build job performs, which is why self-review is listed as a step and not as an
  attitude.
- The merge history stays linear and one commit per pull request, unchanged from ADR 012.
- If the project gains collaborators again, requiring approvals is a branch-protection setting
  away; this ADR is then superseded rather than worked around.

---

## References

- [ADR 012](012-github-flow-branch-merge.md) — the superseded review clause and the still-current
  branching and merge strategy
- `013-cicd-pipeline.draft.md` — the CI/CD gaps this decision makes more pressing
- PR #42 and #43, closed 2026-11-19 — what four months without review actually cost
