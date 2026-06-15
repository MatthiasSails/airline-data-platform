# Airline VM — Access & Connection Details

Deployed instance for the `airline-data-platform` project.  
Connection details and SSH access for the team.

---

## Instance

| Parameter | Value |
| --- | --- |
| Service | AWS Lightsail |
| Name | `aws-airline-1` |
| Region | eu-central-1a (Frankfurt) |
| Plan | $10/Mon — 2 GB RAM, 2 vCPU, 60 GB SSD, x86_64 |
| OS | Ubuntu, user `ubuntu` |
| Static IPv4 | `63.185.229.117` |
| DNS | `airline.matthiaskoehler.com` |
| Account | Study "Consulting" (`503726126644`) — **expires 2026-11-28** → migrate to paid account before that |

---

## SSH Access

### Matthias (owner key)

```bash
ssh -i ~/.ssh/airline_vm ubuntu@63.185.229.117
```

Key file: `~/.ssh/airline_vm` (`.pem`, `chmod 400`)

### Team (Pavel, Chaitra)

```bash
ssh -i ~/.ssh/airline_team ubuntu@63.185.229.117
```

Key file: `~/.ssh/airline_team` (Ed25519, `chmod 600`)  
Private key stored in **Proton Pass** → item "AWS VM ubuntu user" → Vault "Airlines".  
After saving the key file: `ssh-add --apple-use-keychain ~/.ssh/airline_team` (macOS) or `ssh-add ~/.ssh/airline_team` (Linux).

---

## Software

| Package | Version |
| --- | --- |
| Docker | 29.1 |
| Docker Compose | 2.40 |

---

## Running Services

| Service | URL |
| --- | --- |
| Streamlit Dashboard | http://airline.matthiaskoehler.com:8501 |

Entry point: `04-deployment/docker-compose.yml` in `airline-data-platform` repo.

---

## Cross-references

- `airline-compute-prototype-arch.md` — VPC/EC2 architecture planning (longer-term target)
- `aws-free-tier-2026.md` — account limits and monthly cost estimates
- Memory: `project_airlines_status.md`, `reference_aws_accounts.md`

---

## Notes

- Lightsail has a **fixed monthly cost** regardless of usage — stop instance if unused for extended periods
- Atlas Network Access: the VM's IPv4 (`63.185.229.117`) must be whitelisted in the MongoDB Atlas project. Symptom when missing: `pymongo.errors.ServerSelectionTimeoutError: SSL handshake failed: TLSV1_ALERT_INTERNAL_ERROR`
- Account hard-stop 2026-11-28: provision replacement in paid account before this date and update DNS + Atlas whitelist
