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

The team uses the same `.pem` key as Matthias. Request the file `airline_vm.pem` from Matthias and save it to your machine.

#### Step 1 — Save the key file and set permissions

**macOS / Linux:**
```bash
chmod 400 ~/path/to/airline_vm.pem
```

**Windows (PowerShell):**
```powershell
icacls $env:USERPROFILE\.ssh\airline_vm.pem /inheritance:r /grant:r "$env:USERNAME:R"
```

#### Step 2 — Connect

```bash
ssh -i ~/path/to/airline_vm.pem ubuntu@63.185.229.117
```

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

- Atlas Network Access: the VM's IPv4 (`63.185.229.117`) must be whitelisted in the MongoDB Atlas project. Symptom when missing: `pymongo.errors.ServerSelectionTimeoutError: SSL handshake failed: TLSV1_ALERT_INTERNAL_ERROR`
- Account hard-stop 2026-11-28: provision replacement in paid account before this date and update DNS + Atlas whitelist
