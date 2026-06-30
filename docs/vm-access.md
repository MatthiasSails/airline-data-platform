# Airline VM — Team Access

The project's deployed instance: AWS Lightsail, `eu-central-1` (Frankfurt), Ubuntu (user `ubuntu`).
The real host, DNS name, and AWS account ID are **not** in this repo — they live in Proton Pass
(vault "Airlines"). Ask the project owner for access.

---

## SSH

The team uses a shared key `airline_team` (Ed25519, OpenSSH format — not a `.pem`), authorized
alongside the owner key and revocable independently (remove its line from the VM's
`authorized_keys`). Request the private key file from the project owner **as a file** — copy-paste
corrupts Ed25519 keys.

```bash
chmod 400 ~/.ssh/airline_team          # macOS / Linux
# Windows (PowerShell): icacls $env:USERPROFILE\.ssh\airline_team /inheritance:r /grant:r "$env:USERNAME:R"

ssh -i ~/.ssh/airline_team ubuntu@<VM_HOST>   # <VM_HOST> from Proton Pass
```

---

## What runs there

Docker containers via Portainer GitOps (`deployment/`): the Streamlit dashboard, the landing page,
and the ETL pipeline — all exposed through a Cloudflare Tunnel (service URLs in Proton Pass).

---

## Notes

- The VM's IP must be whitelisted in MongoDB Atlas (Network Access). Symptom when missing:
  `ServerSelectionTimeoutError: SSL handshake failed`.
- The study AWS account **expires 2026-11-28** — migrate to a paid account before then and update
  DNS + the Atlas whitelist.
