# ADR 019 — Cloudflare Tunnel as the Only Ingress; No Reverse Proxy, No Inbound Web Ports

**Status:** Accepted (in production since 2026-07-01, nginx removed; written down 2026-07-05)
**Date:** 2026-07-05

---

## Context

The platform's web-facing services (dashboards, landing page, Portainer UI) run as containers
on a cloud VM and need to be reachable under public hostnames with TLS. The conventional
pattern is a reverse proxy (nginx/Traefik/Caddy) on the VM: open inbound ports 80/443, obtain
and renew TLS certificates (e.g. Let's Encrypt), and route by hostname to local services.
This project ran exactly that — an nginx reverse proxy — until 2026-07-01.

## Decision

**All public ingress goes through Cloudflare Tunnel.** A `cloudflared` connector container on
each VM opens an **outbound-only** connection to the Cloudflare edge; ingress rules (public
hostname → `http://localhost:<port>`) are managed in Cloudflare's remote tunnel configuration.
The VMs expose **no inbound web ports at all** — the firewall allows only SSH (and, on the Q
VM, the Portainer agent port restricted to the production VM's address). nginx was removed.

Each VM runs its own connector, because a connector can only route to `localhost` on the host
it runs on — the Q environment therefore has a separate tunnel and hostname rather than sharing
production's.

## Rationale

- **Attack surface:** no listening web ports on the public interface. Port scans see SSH only;
  HTTP(S) exposure, TLS termination, and DDoS absorption happen at Cloudflare's edge.
- **No certificate operations on the VM:** TLS is handled by the edge; nothing to renew, no
  certbot timers to monitor.
- **Less moving machinery than a reverse proxy:** hostname→port mapping is one remote config
  instead of nginx server blocks + cert config + reload discipline.
- The connector runs with `network_mode: host` so it can reach services bound to `127.0.0.1`
  (e.g. the Gold dashboard) — services stay loopback-only and are still publishable.

**Alternatives rejected:**

- *Keep nginx + Let's Encrypt:* works, but is a second routing layer doing the same job as the
  tunnel's ingress rules, plus certificate lifecycle on the VM. It was removed precisely
  because it had become redundant.
- *Publish container ports directly (host:443 etc.):* no hostname routing, certificates in
  every service, maximal attack surface.

## Consequences

- Zero inbound web ports; hostname routing and TLS live at the Cloudflare edge.
- **Vendor dependency:** if Cloudflare is down or the account is lost, all web ingress is down
  (SSH access is independent and unaffected).
- **The ingress config is not in git.** Tunnel ingress rules are remote configuration edited
  via API/dashboard — a drift risk and the natural next IaC candidate (Terraform has a
  Cloudflare provider) if this ever changes more often than it does today.
- Each environment needs its own connector container and tunnel token (a secret, injected via
  the deployment platform, never committed).
- Anyone reproducing this setup needs a Cloudflare-managed domain — the design is portable to
  any tunnel-style ingress (e.g. Tailscale Funnel, ngrok), but not provider-neutral as
  configured.

## References

- Current-state network exposure diagram: [docs/architecture/README.md](../architecture/README.md)
- Q environment tunnel connector: `deployment/q-cloudflared.yml`
- Containerization / GitOps deployment foundation: PR #26
