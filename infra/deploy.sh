#!/usr/bin/env bash
# Manual deploy from any machine — the same steps deploy.yml runs in CI.
# Usage: DEPLOY_HOST=1.2.3.4 DEPLOY_USER=ubuntu [SSH_KEY=~/.ssh/id_ed25519] \
#        [IMAGE_TAG=latest] [DEPLOY_DOMAIN=argus.example.duckdns.org] ./infra/deploy.sh
set -euo pipefail

: "${DEPLOY_HOST:?set DEPLOY_HOST}"
: "${DEPLOY_USER:?set DEPLOY_USER}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/id_ed25519}"
SSH=(ssh -i "$SSH_KEY" "${DEPLOY_USER}@${DEPLOY_HOST}")

repo_root="$(cd "$(dirname "$0")/.." && pwd)"
cd "$repo_root"

echo "==> Syncing compose files and infra/ to ${DEPLOY_HOST}"
"${SSH[@]}" "mkdir -p ~/argus"
scp -i "$SSH_KEY" docker-compose.yml docker-compose.prod.yml "${DEPLOY_USER}@${DEPLOY_HOST}:~/argus/"
scp -i "$SSH_KEY" -r infra "${DEPLOY_USER}@${DEPLOY_HOST}:~/argus/"

echo "==> Pulling ${IMAGE_TAG} images and restarting"
"${SSH[@]}" "cd ~/argus && IMAGE_TAG='${IMAGE_TAG}' docker compose -f docker-compose.yml -f docker-compose.prod.yml pull \
  && IMAGE_TAG='${IMAGE_TAG}' docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --remove-orphans"

url="http://${DEPLOY_HOST}:8000/health"
[ -n "${DEPLOY_DOMAIN:-}" ] && url="https://${DEPLOY_DOMAIN}/health"
echo "==> Health gate: $url"
for i in $(seq 1 24); do
  code=$(curl -ks -o /dev/null -w '%{http_code}' "$url" || true)
  if [ "$code" = "200" ]; then echo "Healthy."; exit 0; fi
  echo "Attempt $i/24: HTTP $code; retrying in 5s"
  sleep 5
done
echo "Deploy failed the health gate." >&2
exit 1
