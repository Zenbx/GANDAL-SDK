#!/usr/bin/env bash
# Demarre iaas-api sur une base SQLite neuve, lance tests/integration, puis l'arrete.
#
#   scripts/run_integration.sh ../iaas-api [python-d-iaas-api]
#
# Le second argument designe un interpreteur ou les dependances d'iaas-api sont
# installees (par defaut : python3). Les tests utilisent le pytest courant.
set -euo pipefail

API_DIR=$(cd "${1:?chemin du depot iaas-api}" && pwd)
API_PYTHON=${2:-python3}
PORT=${GANDAL_IT_PORT:-8765}
WORK=$(mktemp -d)
LOG="$WORK/iaas-api.log"

cleanup() {
    if [[ -n "${API_PID:-}" ]]; then
        kill "$API_PID" 2>/dev/null || true
        wait "$API_PID" 2>/dev/null || true  # uvicorn s'arrete proprement, pas instantanement
    fi
    rm -rf "$WORK"
}
trap cleanup EXIT

# Un serveur deja present sur le port fausserait tout : les tests le prendraient pour le notre.
if curl -s -o /dev/null "http://127.0.0.1:$PORT/"; then
    echo "Le port $PORT est deja occupe ; liberez-le ou definissez GANDAL_IT_PORT." >&2
    exit 1
fi

(
    cd "$API_DIR"
    IAM_JWT_SECRET="integration-$(date +%s)-$RANDOM-$RANDOM" \
    IAM_SEED_DEMO_USERS=true \
    DATABASE_URL="sqlite:///$WORK/iaas.db" \
        exec "$API_PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port "$PORT"
) >"$LOG" 2>&1 &
API_PID=$!

for _ in $(seq 1 60); do
    if curl -sf "http://127.0.0.1:$PORT/openapi.json" >/dev/null; then
        break
    fi
    if ! kill -0 "$API_PID" 2>/dev/null; then
        echo "iaas-api s'est arretee au demarrage :" >&2
        cat "$LOG" >&2
        exit 1
    fi
    sleep 0.5
done
curl -sf "http://127.0.0.1:$PORT/openapi.json" >/dev/null || {
    echo "iaas-api ne repond pas apres 30 s :" >&2
    cat "$LOG" >&2
    exit 1
}

GANDAL_IT_ENDPOINT="http://127.0.0.1:$PORT" python -m pytest -q tests/integration
