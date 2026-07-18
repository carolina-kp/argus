#!/usr/bin/env bash
# Nightly backup: pg_dump (custom format) + Qdrant snapshots, gzipped and
# date-stamped locally, then pushed offsite. Provider-agnostic offsite targets:
#   BACKUP_TARGET=github-release  assets on a rolling release in a private repo
#   BACKUP_TARGET=s3              any S3-compatible endpoint (AWS CLI required)
#   BACKUP_TARGET=none            local only
# Reads config from ~/argus/.env (see infra/.env.prod.example).
# Cron (02:30 nightly):
#   30 2 * * * /home/USER/argus/infra/backup/backup.sh >> /home/USER/argus/backup.log 2>&1
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/argus}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
# shellcheck disable=SC1091
[ -f "$APP_DIR/.env" ] && set -a && . "$APP_DIR/.env" && set +a

STAMP="$(date -u +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
compose() { docker compose -f "$APP_DIR/docker-compose.yml" -f "$APP_DIR/docker-compose.prod.yml" "$@"; }

echo "==> [$STAMP] Postgres dump"
PG_FILE="$BACKUP_DIR/postgres-$STAMP.dump.gz"
compose exec -T postgres pg_dump -Fc -U "${POSTGRES_USER:-argus}" "${POSTGRES_DB:-argus}" |
  gzip >"$PG_FILE"

echo "==> Qdrant snapshots (per collection)"
QDRANT_FILE="$BACKUP_DIR/qdrant-$STAMP.tar.gz"
qdrant_api() { compose exec -T api python -c "
import sys, httpx
r = httpx.request(sys.argv[1], 'http://qdrant:6333' + sys.argv[2], timeout=120)
r.raise_for_status()
sys.stdout.write(r.text)
" "$@"; }
tmp="$(mktemp -d)"
collections=$(qdrant_api GET /collections | python3 -c "import sys,json;[print(c['name']) for c in json.load(sys.stdin)['result']['collections']]")
for col in $collections; do
  echo "    snapshot: $col"
  snap=$(qdrant_api POST "/collections/$col/snapshots" | python3 -c "import sys,json;print(json.load(sys.stdin)['result']['name'])")
  # Snapshots land inside the qdrant volume; copy out via the container.
  compose exec -T qdrant cat "/qdrant/snapshots/$col/$snap" >"$tmp/$col-$snap"
  qdrant_api DELETE "/collections/$col/snapshots/$snap" >/dev/null
done
tar -czf "$QDRANT_FILE" -C "$tmp" .
rm -rf "$tmp"

echo "==> Offsite push (target: ${BACKUP_TARGET:-none})"
case "${BACKUP_TARGET:-none}" in
github-release)
  : "${BACKUP_GITHUB_TOKEN:?set BACKUP_GITHUB_TOKEN}"
  : "${BACKUP_GITHUB_REPO:?set BACKUP_GITHUB_REPO}"
  api="https://api.github.com/repos/$BACKUP_GITHUB_REPO"
  auth=(-H "Authorization: Bearer $BACKUP_GITHUB_TOKEN" -H "Accept: application/vnd.github+json")
  # One release per calendar day keeps assets grouped and pruning simple.
  tag="backup-$(date -u +%Y%m%d)"
  release_id=$(curl -fs "${auth[@]}" "$api/releases/tags/$tag" 2>/dev/null |
    python3 -c "import sys,json;print(json.load(sys.stdin)['id'])" 2>/dev/null || true)
  if [ -z "$release_id" ]; then
    release_id=$(curl -fs "${auth[@]}" -X POST "$api/releases" \
      -d "{\"tag_name\":\"$tag\",\"name\":\"$tag\",\"prerelease\":true}" |
      python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
  fi
  for f in "$PG_FILE" "$QDRANT_FILE"; do
    curl -fs "${auth[@]}" -H "Content-Type: application/gzip" \
      --data-binary @"$f" \
      "https://uploads.github.com/repos/$BACKUP_GITHUB_REPO/releases/$release_id/assets?name=$(basename "$f")" >/dev/null
    echo "    uploaded $(basename "$f")"
  done
  ;;
s3)
  : "${BACKUP_S3_ENDPOINT:?set BACKUP_S3_ENDPOINT}"
  : "${BACKUP_S3_BUCKET:?set BACKUP_S3_BUCKET}"
  export AWS_ACCESS_KEY_ID="$BACKUP_S3_ACCESS_KEY" AWS_SECRET_ACCESS_KEY="$BACKUP_S3_SECRET_KEY"
  for f in "$PG_FILE" "$QDRANT_FILE"; do
    aws s3 cp --endpoint-url "$BACKUP_S3_ENDPOINT" "$f" "s3://$BACKUP_S3_BUCKET/$(basename "$f")"
  done
  ;;
none)
  echo "    skipped (local only)"
  ;;
*)
  echo "Unknown BACKUP_TARGET: $BACKUP_TARGET" >&2
  exit 1
  ;;
esac

echo "==> Pruning local copies older than ${BACKUP_RETENTION_DAYS:-7} days"
find "$BACKUP_DIR" -name '*.gz' -mtime "+${BACKUP_RETENTION_DAYS:-7}" -delete

echo "==> Done: $PG_FILE, $QDRANT_FILE"
