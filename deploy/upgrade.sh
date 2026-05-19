#!/usr/bin/env bash

set -Eeuo pipefail

APP_DIR="${APP_DIR:-/data/bankai}"
LOCAL_HEALTH_URL="${LOCAL_HEALTH_URL:-http://127.0.0.1:8000/health}"
PUBLIC_HEALTH_URL="${PUBLIC_HEALTH_URL:-}"
TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-360}"
CHECK_ONLY=false
RUN_TESTS=false
SERVICES=(redis backend frontend nginx)

usage() {
  cat <<'EOF'
Usage: deploy/upgrade.sh [options]

Options:
  --app-dir PATH       Deployment directory. Default: /data/bankai
  --health-url URL     Local health URL. Default: http://127.0.0.1:8000/health
  --public-health-url URL
                       Optional public health URL to check from this machine.
  --timeout SECONDS    Health wait timeout per service. Default: 360
  --check-only         Do not rebuild or restart. Only validate current health.
  --run-tests          Run backend pytest suite after services are healthy.
  --service NAME       Upgrade specific service. Can be repeated.
  -h, --help           Show this help.

Examples:
  deploy/upgrade.sh
  deploy/upgrade.sh --check-only
  deploy/upgrade.sh --service backend --service frontend --run-tests
EOF
}

log() {
  printf '[upgrade] %s\n' "$*"
}

fail() {
  printf '[upgrade] ERROR: %s\n' "$*" >&2
  exit 1
}

compose() {
  docker compose "$@"
}

parse_args() {
  local custom_services=false
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --app-dir)
        APP_DIR="${2:-}"
        [ -n "$APP_DIR" ] || fail "--app-dir requires a value"
        shift 2
        ;;
      --health-url)
        LOCAL_HEALTH_URL="${2:-}"
        [ -n "$LOCAL_HEALTH_URL" ] || fail "--health-url requires a value"
        shift 2
        ;;
      --public-health-url)
        PUBLIC_HEALTH_URL="${2:-}"
        [ -n "$PUBLIC_HEALTH_URL" ] || fail "--public-health-url requires a value"
        shift 2
        ;;
      --timeout)
        TIMEOUT_SECONDS="${2:-}"
        [[ "$TIMEOUT_SECONDS" =~ ^[0-9]+$ ]] || fail "--timeout must be seconds"
        shift 2
        ;;
      --check-only)
        CHECK_ONLY=true
        shift
        ;;
      --run-tests)
        RUN_TESTS=true
        shift
        ;;
      --service)
        [ -n "${2:-}" ] || fail "--service requires a value"
        if [ "$custom_services" = false ]; then
          SERVICES=()
          custom_services=true
        fi
        SERVICES+=("$2")
        shift 2
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        fail "Unknown option: $1"
        ;;
    esac
  done
}

service_container_id() {
  compose ps -q "$1"
}

service_status() {
  local service="$1"
  local cid
  cid="$(service_container_id "$service")"
  if [ -z "$cid" ]; then
    printf 'missing'
    return
  fi
  docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$cid"
}

wait_for_service() {
  local service="$1"
  local deadline=$((SECONDS + TIMEOUT_SECONDS))
  local status

  log "Waiting for $service health"
  while [ "$SECONDS" -lt "$deadline" ]; do
    status="$(service_status "$service")"
    log "$service status: $status"
    if [ "$status" = "healthy" ] || [ "$status" = "running" ]; then
      return 0
    fi
    sleep 5
  done

  compose ps "$service" >&2 || true
  compose logs --tail=100 "$service" >&2 || true
  fail "$service did not become healthy within ${TIMEOUT_SECONDS}s"
}

check_health_url() {
  local label="$1"
  local url="$2"
  log "Checking $label health: $url"
  curl --fail --show-error --silent --max-time 20 "$url" >/tmp/bankai-upgrade-health.json
  cat /tmp/bankai-upgrade-health.json
  printf '\n'
}

main() {
  parse_args "$@"

  [ -d "$APP_DIR" ] || fail "App directory not found: $APP_DIR"
  cd "$APP_DIR"

  log "Validating compose file"
  compose config >/tmp/bankai-compose-rendered.yml

  if [ "$CHECK_ONLY" = false ]; then
    log "Upgrading services: ${SERVICES[*]}"
    compose up -d --build "${SERVICES[@]}"
  else
    log "Check-only mode: skipping rebuild/restart"
  fi

  for service in redis backend frontend nginx; do
    wait_for_service "$service"
  done

  compose ps redis backend frontend nginx
  check_health_url local "$LOCAL_HEALTH_URL"

  if [ -n "$PUBLIC_HEALTH_URL" ]; then
    check_health_url public "$PUBLIC_HEALTH_URL"
  fi

  if [ "$RUN_TESTS" = true ]; then
    log "Running backend tests"
    compose exec -T backend python -m pytest tests -q
  fi

  log "Upgrade verification complete"
}

main "$@"
