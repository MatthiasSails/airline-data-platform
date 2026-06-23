# Requirements & Scope

What the project delivers, for whom, and under which constraints. For the project description and
architecture overview, start at the root [README](../../README.md).

---

## Team & Context

**Team:** Matthias Köhler, Pavel, Chaithra (3 people)
**Mentor:** Nicolas ("NicoTheDataSherpa")
**Program:** DataScientest Data Engineer Bootcamp, cohort `apr26_bde_airlines`

**Constraints worth knowing as a reader:**
- OpenSky API blocked on external VMs (outbound HTTPS) — local-only collector (see [ADR 005](../adr/005-opensky-mongo-migration.md))
- ML is explicitly de-prioritized (mentor approved)
- Strategic pivot: MongoDB positioned as multi-source hub, not single-feed buffer ([ADR 004](../adr/004-mongo-as-multisource-hub.md))

For the full original assignment see [source/](source/).

---

## How to navigate this folder

| Path | What's inside |
|---|---|
| **[scope.md](scope.md)** | What we deliver per phase, what's out of scope, non-goals |
| **[timeline.md](timeline.md)** | Mermaid Gantt chart of milestones |
| **[source/](source/)** | Original Liora assignment + mentor messages (immutable) |

**New to the repo?** Read in this order: root [README](../../README.md) → [scope.md](scope.md) →
[architecture/README.md](../architecture/README.md) → [adr/](../adr/).
