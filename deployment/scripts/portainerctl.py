#!/usr/bin/env python3
"""Operate the Portainer-managed stacks from the command line.

Read-only by default; the only write is `redeploy`, and it needs --apply.

Why this exists: on 2026-11-19 a data outage took several hours to diagnose, and most of
that time went into building these queries from scratch. The answers that mattered —
"is the container actually running the code we merged?", "why is the deploy stuck?" —
were not visible in the Portainer UI, which reported success throughout. See the runbook
in README.md for question -> command.

Hard-won details encoded here, all verified against Portainer 2.42:

  * Cloudflare blocks urllib's default User-Agent with a 403 (error 1010) before the
    request ever reaches Portainer. A browser-ish or curl UA is required.
  * `git/redeploy` is PUT, not POST. POST returns 405.
  * `git/redeploy` REPLACES the stack's entire Env array. Posting a partial list wipes
    the rest — this once crash-looped gold_api on a missing DATABASE_URL. So: GET the
    stack, mutate one entry in the array it returns, PUT the whole array back. That is
    what `redeploy --set` does; never hand-build an env list.
  * HTTP 409 "deployment already in progress" is a lock, not an unreachable endpoint. If
    it persists, a deployment died holding it; restarting the Portainer container clears
    it (running containers are unaffected, verified).
  * A 200 from redeploy does NOT mean a container was recreated, and it does not even
    mean the endpoint was reachable. Confirm with `watch` or `endpoints`, which report
    the container's image id — the only trustworthy signal.

Changed in Portainer 2.45 (upgraded 2026-11-19):

  * `git/redeploy` is asynchronous: HTTP 200 after about a second, the deployment runs
    afterwards with the stack in status 3 ("deploying"). UpdateDate changes at once, so it
    says nothing about completion; `watch` follows the stack's DeploymentStatus instead.
    Because a fast deployment can finish before a separately started `watch` takes its
    first look, prefer `redeploy --apply --watch <container>`, which snapshots first.
  * `git/redeploy` returns 403 when endpointId differs from the stack's environment.
  * The 409 lock still happens on 2.45.4: a deployment sits in "deploying" with no Docker
    activity behind it, and only a Portainer restart clears it.

Token: macOS Keychain item `portainer_api_mk`. Never pass it on the command line.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

# The Portainer base URL is deliberately NOT hardcoded: this repository is public and
# internal hostnames do not belong in tracked files. Export PORTAINER_URL (the same
# value the GitHub Actions secret carries); the local pointer lives in CLAUDE.local.md.
BASE = (os.environ.get("PORTAINER_URL") or "").rstrip("/") + "/api"
DEFAULT_ENDPOINT = 3  # the production VM's Docker environment
KEYCHAIN_ITEM = os.environ.get("PORTAINER_KEYCHAIN_ITEM", "portainer_api_mk")

# Used for both Stack.Status and the entries of Stack.DeploymentStatus (observed values).
STACK_STATUS = {1: "active", 2: "inactive", 3: "deploying", 4: "error"}
DEPLOYING = 3
ENDPOINT_STATUS = {1: "up", 2: "down"}

# Never print a log line that could carry a connection string, password or token.
SECRET = re.compile(
    r"mongodb(\+srv)?://|://[^/\s]*:[^@\s]*@|password|secret|token|api[-_]?key", re.I
)


# ---------------------------------------------------------------------------
# transport
# ---------------------------------------------------------------------------

def keychain(item: str = KEYCHAIN_ITEM) -> str:
    out = subprocess.run(
        ["security", "find-generic-password", "-s", item, "-w"],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def call(path: str, token: str, method: str = "GET", payload=None, raw: bool = False,
         timeout: int = 180):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        method=method,
        headers={
            "X-API-Key": token,
            "User-Agent": "curl/8.0",  # see module docstring: Cloudflare blocks urllib
            **({"Content-Type": "application/json"} if data else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read()
        if raw:
            return resp.status, body
        return resp.status, (json.loads(body) if body else None)


def find_container(token: str, endpoint: int, name: str):
    _, containers = call(f"/endpoints/{endpoint}/docker/containers/json?all=1", token)
    return next(
        (c for c in containers if name in (n.lstrip("/") for n in c["Names"])), None
    )


# ---------------------------------------------------------------------------
# commands
# ---------------------------------------------------------------------------

def cmd_stacks(args, token):
    _, stacks = call("/stacks", token)
    for s in sorted(stacks, key=lambda x: x.get("Id", 0)):
        git = s.get("GitConfig") or {}
        print(
            f"{s.get('Id'):>3}  ep={s.get('EndpointId')}  "
            f"{STACK_STATUS.get(s.get('Status'), s.get('Status')):<9} "
            f"{s.get('Name'):<22} {git.get('ReferenceName', '-'):<22} "
            f"[{','.join(e.get('name', '') for e in (s.get('Env') or []))}]"
        )


def cmd_stack(args, token):
    for sid in args.stack_id:
        _, s = call(f"/stacks/{sid}", token)
        git = s.get("GitConfig") or {}
        auto = git.get("Autoupdate") or s.get("AutoUpdate") or {}
        print(f"=== stack {sid}: {s.get('Name')} ===")
        print(f"  endpoint    : {s.get('EndpointId')}")
        print(f"  composeFile : {git.get('ConfigFilePath')}")
        print(f"  ref         : {git.get('ReferenceName')}")
        print(f"  commit      : {git.get('ConfigHash')}")
        print(f"  autoUpdate  : {json.dumps(auto)}")
        print(f"  updateDate  : {s.get('UpdateDate')}")
        print(f"  env names   : {[e.get('name') for e in (s.get('Env') or [])]}")
        print()


def cmd_endpoints(args, token):
    _, endpoints = call("/endpoints", token)
    print("=== endpoints ===")
    for ep in endpoints:
        print(
            f"  id={ep.get('Id')}  {ep.get('Name'):<16} "
            f"status={ENDPOINT_STATUS.get(ep.get('Status'), ep.get('Status'))}  "
            f"url={ep.get('URL')}"
        )
    for ep_id in args.endpoint or [e.get("Id") for e in endpoints]:
        print(f"\n=== containers on endpoint {ep_id} ===")
        try:
            _, containers = call(
                f"/endpoints/{ep_id}/docker/containers/json?all=1", token, timeout=30
            )
        except Exception as e:  # noqa: BLE001 - an unreachable endpoint is normal here
            print(f"  not queryable: {type(e).__name__}: {e}")
            continue
        for c in containers or []:
            print(
                f"  {(c.get('Names') or ['?'])[0].lstrip('/'):<22} "
                f"{c.get('State'):<9} {c.get('Status'):<26} {c.get('Image')}"
            )


def cmd_logs(args, token):
    c = find_container(token, args.endpoint, args.container)
    if c is None:
        sys.exit(f"{args.container}: not found on endpoint {args.endpoint}")
    _, body = call(
        f"/endpoints/{args.endpoint}/docker/containers/{c['Id']}/logs"
        f"?stdout=1&stderr=1&tail={args.tail}",
        token, raw=True,
    )
    # Docker frames each log line with an 8-byte header; drop the control bytes.
    text = re.sub(r"[\x00-\x08\x0b-\x1f]", "", body.decode("utf-8", errors="replace"))
    shown = withheld = 0
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Filter first, so "withheld" counts only lines that matched --grep. Counting
        # across the whole log read as a hidden match when there was none.
        if args.grep and args.grep.lower() not in line.lower():
            continue
        if SECRET.search(line):
            withheld += 1
            continue
        print(" ", line)
        shown += 1
    print(f"\n({shown} shown, {withheld} withheld as possibly credential-bearing)")


def cmd_redeploy(args, token):
    _, stack = call(f"/stacks/{args.stack_id}", token)
    env = list(stack.get("Env") or [])
    git = stack.get("GitConfig") or {}
    ref = args.ref or git.get("ReferenceName") or "refs/heads/main"

    print(f"stack {args.stack_id}: {stack.get('Name')}  (endpoint {args.endpoint})")
    print(f"  compose : {git.get('ConfigFilePath')}")
    print(f"  ref     : {ref}")
    print(f"  commit  : {git.get('ConfigHash')}")
    print(f"  env read: {[e.get('name') for e in env]}  ({len(env)} entries)")

    for pair in args.set or []:
        if "=" not in pair:
            sys.exit(f"--set needs KEY=VALUE, got {pair!r}")
        key, value = pair.split("=", 1)
        for entry in env:
            if entry.get("name") == key:
                entry["value"] = value
                print(f"  set     : {key} (existing entry updated)")
                break
        else:
            env.append({"name": key, "value": value})
            print(f"  set     : {key} (new entry appended)")

    payload = {
        "env": env,
        "repositoryReferenceName": ref,
        "pullImage": True,
        "prune": False,
    }
    print(f"  sending : PUT /stacks/{args.stack_id}/git/redeploy"
          f"?endpointId={args.endpoint}")
    print(f"            pullImage=True prune=False "
          f"env={[e.get('name') for e in env]}")

    if not args.apply:
        print("\nDRY RUN — nothing sent. Re-run with --apply.")
        return

    # Snapshot before sending: on Portainer 2.45 a quick deployment can be over before a
    # watch started afterwards takes its first look.
    before = snapshot(token, args.stack_id, args.endpoint, args.watch) if args.watch else None

    try:
        status, _ = call(
            f"/stacks/{args.stack_id}/git/redeploy?endpointId={args.endpoint}",
            token, method="PUT", payload=payload,
        )
    except urllib.error.HTTPError as e:
        detail = e.read()[:300].decode(errors="replace")
        print(f"\nHTTP {e.code} — redeploy FAILED: {detail}")
        if e.code == 409:
            print("  409 is a lock, not an unreachable endpoint. If it persists, a "
                  "deployment died holding it — restart the portainer container.")
        sys.exit(1)

    print(f"\nHTTP {status} — redeploy accepted.")
    if before is None:
        print("  This is NOT proof the container was recreated. Verify with:")
        print(f"    portainerctl.py watch {args.stack_id} <container>")
        return
    print()
    wait_for_deploy(token, args.stack_id, args.endpoint, args.watch, before,
                    args.timeout, args.interval)


def _utc(ts) -> str:
    return time.strftime("%H:%M:%SZ", time.gmtime(ts)) if ts else "-"


def snapshot(token, stack_id, endpoint, container) -> dict:
    _, stack = call(f"/stacks/{stack_id}", token)
    c = find_container(token, endpoint, container) or {}
    last = (stack.get("DeploymentStatus") or [{}])[-1]
    return {
        "commit": ((stack.get("GitConfig") or {}).get("ConfigHash") or "")[:8],
        "deploy": last.get("Status"),
        "deployTime": last.get("Time"),
        "deployMsg": last.get("Message") or "",
        "image": c.get("ImageID") or c.get("Image"),
        "created": c.get("Created"),
        "status": c.get("Status"),
    }


def wait_for_deploy(token, stack_id, endpoint, container, first, timeout, interval):
    """Wait until the container changes or a deployment newer than `first` finishes.

    Settling on the stack's UpdateDate is wrong since Portainer 2.45: it changes the
    moment the asynchronous redeploy is accepted, long before anything is pulled.
    """
    print(f"start: commit={first['commit']} "
          f"deploy={STACK_STATUS.get(first['deploy'], first['deploy'])}"
          f"@{_utc(first['deployTime'])} created={_utc(first['created'])}")
    print(f"       image={first['image']}")

    now = first
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(interval)
        now = snapshot(token, stack_id, endpoint, container)
        print(f"  commit={now['commit']} "
              f"deploy={STACK_STATUS.get(now['deploy'], now['deploy'])}"
              f"@{_utc(now['deployTime'])} created={_utc(now['created'])} "
              f"status={now['status']}")

        recreated = now["created"] != first["created"]
        new_deploy_done = (
            (now["deployTime"] or 0) > (first["deployTime"] or 0)
            and now["deploy"] != DEPLOYING
        )
        if not (recreated or new_deploy_done):
            continue

        print("\nSETTLED:")
        print(f"  commit : {first['commit']} -> {now['commit']}")
        print(f"  image  : {first['image']}")
        print(f"        -> {now['image']}")
        if now["deploy"] == 4:
            print(f"  verdict: deployment FAILED — {now['deployMsg']}")
            sys.exit(1)
        if now["image"] != first["image"]:
            print("  verdict: container is on a NEW image")
        elif recreated:
            print("  verdict: container recreated, but on the SAME image id")
        else:
            print("  verdict: deployment finished WITHOUT recreating the container — "
                  "the running code is unchanged (was the image built yet?)")
        return

    if now["deploy"] == DEPLOYING:
        print(f"\nTIMEOUT — stack has been 'deploying' since {_utc(now['deployTime'])} "
              "with the container untouched. That is the stale lock: the next redeploy "
              "gets HTTP 409. Restart the portainer container to clear it.")
    else:
        print("\nTIMEOUT — no new deployment and no new container. If the redeploy was "
              "sent before this watch started, it may already be over: compare the "
              "image id above with what you expect, or use redeploy --watch next time.")
    sys.exit(1)


def cmd_watch(args, token):
    first = snapshot(token, args.stack_id, args.endpoint, args.container)
    wait_for_deploy(token, args.stack_id, args.endpoint, args.container, first,
                    args.timeout, args.interval)


# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--endpoint", type=int, default=DEFAULT_ENDPOINT,
                    help=f"Docker endpoint id (default {DEFAULT_ENDPOINT} = production)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("stacks", help="list every stack with endpoint, status and env names")

    p = sub.add_parser("stack", help="one stack's GitOps and autoUpdate configuration")
    p.add_argument("stack_id", nargs="+")

    p = sub.add_parser("endpoints", help="endpoint reachability and live containers")
    p.add_argument("--only", dest="endpoint", type=int, nargs="*")

    p = sub.add_parser("logs", help="container logs, credential lines filtered out")
    p.add_argument("container")
    p.add_argument("--tail", default="200")
    p.add_argument("--grep")

    p = sub.add_parser("redeploy", help="force a re-pull, preserving the stack's env")
    p.add_argument("stack_id")
    p.add_argument("--set", action="append", metavar="KEY=VALUE")
    p.add_argument("--ref", help="override the git ref, e.g. refs/heads/main")
    p.add_argument("--apply", action="store_true", help="actually send it")
    p.add_argument("--watch", metavar="CONTAINER",
                   help="snapshot CONTAINER before sending, then wait for the result")
    p.add_argument("--timeout", type=int, default=420)
    p.add_argument("--interval", type=int, default=10)

    p = sub.add_parser("watch", help="wait for a redeploy to settle, report the image")
    p.add_argument("stack_id")
    p.add_argument("container")
    p.add_argument("--timeout", type=int, default=420)
    p.add_argument("--interval", type=int, default=20)

    args = ap.parse_args()
    if not os.environ.get("PORTAINER_URL"):
        sys.exit(
            "PORTAINER_URL is not set. Export the Portainer base URL first — it is not\n"
            "hardcoded because this repository is public. The value is noted in\n"
            "CLAUDE.local.md and is the same one the PORTAINER_URL Actions secret holds."
        )
    token = keychain()
    {
        "stacks": cmd_stacks, "stack": cmd_stack, "endpoints": cmd_endpoints,
        "logs": cmd_logs, "redeploy": cmd_redeploy, "watch": cmd_watch,
    }[args.cmd](args, token)


if __name__ == "__main__":
    main()
