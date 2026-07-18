#!/usr/bin/env bash
# Restore a backup produced by backup.sh. A backup without a tested restore is
# not a backup. Usage:
#   ./restore.sh postgres path/to/postgres-STAMP.dump.gz
#   ./restore.sh qdrant   path/to/qdrant-STAMP.tar.gz
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/argus}"
# shellcheck disable=SC1091
[ -f "$APP_DIR/.env" ] && set -a && . "$APP_DIR/.env" && set +a
compose() { docker compose -f "$APP_DIR/docker-compose.yml" -f "$APP_DIR/docker-compose.prod.yml" "$@"; }

kind="${1:?usage: restore.sh <postgres|qdrant> <file>}"
file="${2:?usage: restore.sh <postgres|qdrant> <file>}"
[ -f "$file" ] || { echo "No such file: $file" >&2; exit 1; }

case "$kind" in
postgres)
  echo "==> Restoring Postgres from $file (drops and recreates objects)"
  gunzip -c "$file" | compose exec -T postgres pg_restore \
    -U "${POSTGRES_USER:-argus}" -d "${POSTGRES_DB:-argus}" --clean --if-exists --no-owner
  echo "Done."
  ;;
qdrant)
  echo "==> Restoring Qdrant snapshots from $file"
  tmp="$(mktemp -d)"
  tar -xzf "$file" -C "$tmp"
  for snap in "$tmp"/*; do
    base="$(basename "$snap")"
    col="${base%%-*}"
    echo "    collection: $col"
    compose exec -T qdrant sh -c "mkdir -p /qdrant/snapshots/$col && cat > /qdrant/snapshots/$col/$base" <"$snap"
    compose exec -T api python -c "
import httpx
r = httpx.put('http://qdrant:6333/collections/$col/snapshots/recover',
              json={'location': 'file:///qdrant/snapshots/$col/$base'}, timeout=300)
r.raise_for_status()
print(r.text)
"
  done
  rm -rf "$tmp"
  echo "Done."
  ;;
*)
  echo "Unknown kind: $kind (postgres|qdrant)" >&2
  exit 1
  ;;
esac
