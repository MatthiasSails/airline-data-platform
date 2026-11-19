# Deployment scripts

## Runbook — question → command

Export `PORTAINER_URL` once per shell first (see `CLAUDE.local.md`; it is not in this
repository because the repository is public). The API token is read from the macOS
Keychain item `portainer_api_mk`, never passed on the command line.

```bash
export PORTAINER_URL=https://<portainer-host>
```

| Question | Command |
|---|---|
| Is the container actually running the code we merged? | `portainerctl.py endpoints --only 3` — compare the image id, **not** the Portainer status |
| Which stacks exist, on which endpoint, with which env keys? | `portainerctl.py stacks` |
| Which commit and compose file does one stack track? | `portainerctl.py stack 14` |
| Is an environment reachable at all? | `portainerctl.py endpoints` — `status=down` means the agent is unreachable |
| Why is bronze not writing? | `portainerctl.py logs etl_bronze --tail 60` — look for `Quota: N of 500 requests left` |
| Did a deploy actually land? | `portainerctl.py watch 14 etl_bronze` — reports whether the image id changed |
| Force a stack onto the current image | `portainerctl.py redeploy 14 --apply` (dry run without `--apply`) |
| Change one env var and redeploy | `portainerctl.py redeploy 14 --set OPENSKY_ENABLED=false --apply` |
| Is the GitOps poller healthy? | `portainerctl.py logs portainer --tail 200 --grep "failed to"` |

Stack ids referenced above: `14` = `airline-etl-bronze`, `15` = `airline-etl-silver`.
`portainerctl.py stacks` prints the current list.

---

## Why these exist

A data outage on 2026-11-19 took several hours to diagnose, and most of that time went
into building these queries from scratch. The Portainer UI reported success throughout.
The scripts exist so the next investigation starts from an answer instead of a shell
one-liner.

### What the outage taught, in short

**A 200 from Portainer does not mean the code is deployed.** On one merge Portainer's
5-minute git poll fired 98 seconds *before* the image build finished, pulled the
then-current `:latest` — four months old — reported "Stack deployment successful", and
left the stale container running. Both `main` and Portainer then showed the new commit.
The only honest signal is the container's image id, which is why `watch` and `endpoints`
print it and `redeploy` refuses to claim success.

**HTTP 409 is a lock, not an unreachable endpoint.** "Deployment is already in progress"
means a deployment holds the stack. If a deployment dies mid-flight the lock is never
released and every later redeploy fails. Restarting the `portainer` container clears it;
the managed containers keep running (verified — Portainer is the management plane, not
their supervisor).

**One broken stack can freeze all of them.** A single stack whose git clone directory was
left in a broken state failed its fresh clone every 5 minutes for four days
(`repository already exists`), which stopped the autoUpdate job before it reached the
deploy phase for *any* stack. The error sat in the log 1153 times and nobody looked. A
partially-finished clone re-creates the same condition, so clearing it means moving the
directory aside under
`/var/lib/docker/volumes/portainer_data/_data/compose/<stack-id>/`, not just retrying.

**`git/redeploy` replaces the whole env array.** Sending a partial list silently wipes
every other variable. `redeploy --set` reads the stack first and mutates one entry, which
is the only safe shape; never hand-build an env list.

---

## set-q-image-tag.sh

Points the Q stacks at a PR image tag and is called from `.github/workflows/`. It loops
over `PORTAINER_Q_STACK_IDS` and skips stacks that carry no `IMAGE_TAG`. Note it fails
whenever the Q environment is down, which makes `deploy-q` red on every PR that touches
`etl/` or `deployment/`.
