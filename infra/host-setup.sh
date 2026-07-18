#!/usr/bin/env bash
# One-time bootstrap for a fresh Ubuntu host (22.04/24.04, amd64 or arm64).
# Idempotent: safe to re-run. Works on Oracle ARM, EC2, Hetzner, anything.
# Run as a sudo-capable user:  bash host-setup.sh
set -euo pipefail

echo "==> Installing Docker Engine + compose plugin (official repo)"
if ! command -v docker >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  # shellcheck disable=SC1091
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" |
    sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

echo "==> Adding $USER to the docker group (re-login to take effect)"
sudo usermod -aG docker "$USER"

echo "==> Firewall: allow SSH, HTTP, HTTPS"
if command -v ufw >/dev/null 2>&1; then
  sudo ufw allow OpenSSH
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw --force enable
else
  echo "    ufw not present; configure the provider firewall for 22/80/443."
fi

echo "==> App directory"
mkdir -p "$HOME/argus"

cat <<'EOF'

Done. Next steps:
  1. Log out and back in (docker group).
  2. Copy infra/.env.prod.example to ~/argus/.env and fill it in.
  3. Deploy: run the GitHub "Deploy" workflow, or infra/deploy.sh from your machine.
  4. Nightly backups: see infra/backup/README section in DECISIONS.md.
Note (Oracle Cloud): also open 80/443 in the VCN security list; ufw alone is not enough there.
EOF
