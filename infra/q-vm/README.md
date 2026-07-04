# infra/q-vm

Terraform for the Q (stage) VM (`aws-airline-q-1`) — the first Infrastructure-as-Code in this
project. Scope is deliberately narrow: **VM provisioning only** (instance, static IP, firewall).
Everything that runs *on* the VM is provisioned by other means — see "Three layers" below before
adding anything here.

## What's here

| File | Purpose |
|---|---|
| `main.tf` | the three resources: Lightsail instance, static IP, firewall rules |
| `variables.tf` | inputs (sizes, names, AZ — all with safe defaults except `prod_vm_ip`) |
| `outputs.tf` | the VM's public IP and SSH username, for `~/.ssh/config` and the Portainer endpoint |
| `versions.tf` | provider pin + AWS region |
| `user_data.sh` | first-boot script (Docker install only — see "Three layers") |
| `terraform.tfvars` (gitignored) | real values, incl. the prod VM's IP |
| `terraform.tfstate*` (gitignored) | state — contains resource IDs, never commit |

Run with `AWS_PROFILE=terraform` (see `CLAUDE.local.md` for the credential chain).

## Three layers — why cloudflared and the Portainer agent aren't Terraform resources

Getting a service running on the Q VM involves three distinct layers. Mixing them up is the
usual reason someone goes looking for "the container config" in the wrong place:

1. **VM provisioning (this directory, Terraform).** Only the instance, its static IP, and the
   firewall. Nothing container-related — Terraform's job ends once the VM boots and Docker is
   installed.
2. **Portainer agent bootstrap (manual, not in git).** The agent (`portainer/agent`) is what
   registers this VM as a Portainer endpoint — but it can't be started by `user_data.sh`, because
   `user_data` is readable via Lightsail's instance metadata service, and the agent needs a secret
   (`AGENT_SECRET`) that must never be exposed that way. So it's started once, by hand, over SSH,
   after boot. This is a real chicken-and-egg constraint (you need Portainer reachable before
   Portainer can manage anything here), not an oversight — see `CLAUDE.local.md` for the exact
   command.
3. **Application & tunnel deploys (Portainer GitOps stacks, not here).** Everything that actually
   serves traffic — the `q-gold-dash` stack and the `q-cloudflared` tunnel connector — is a
   Portainer stack defined in [`../../deployment/`](../../deployment/) (`gold-dash.yml`,
   `q-cloudflared.yml`), pulled from git by Portainer itself. `cloudflared` belongs here, not in
   Terraform: it's an application-layer container like any other stack, not part of standing up
   the VM.

So: **VM exists → agent bootstraps it manually → everything else is a normal Portainer stack.**
Only layer 1 is Terraform's job; layers 2 and 3 are deliberately kept out of this directory.
