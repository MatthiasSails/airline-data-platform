#!/bin/bash
# Lightsail user_data — runs once as root on first boot.
# Installs Docker only. Deliberately NO secrets in here: user_data is readable
# via the instance metadata service, so the Portainer agent (which needs
# AGENT_SECRET) is started afterwards via a single ssh command instead.
set -euo pipefail

# 1 GiB swapfile — OOM safety net on the 1 GB micro_3_0 bundle (steady-state
# footprint is ~800 MiB; spikes e.g. during docker pull would otherwise risk
# OOM kills). Lightsail Ubuntu images ship without swap.
fallocate -l 1G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab

# Docker's official convenience installer (adds apt repo, installs engine + compose plugin)
curl -fsSL https://get.docker.com | sh

# Let the default user run docker without sudo
usermod -aG docker ubuntu

systemctl enable --now docker
