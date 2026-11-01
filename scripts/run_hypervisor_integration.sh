#!/usr/bin/env bash
# Demarre la cellule gandal-hypervisor, lance tests/integration_hypervisor, puis l'arrete.
#
#   scripts/run_hypervisor_integration.sh ../gandal-hypervisor [python-de-la-cellule]
#
# Par defaut la cellule tourne sur son faux pool (GANDAL_HV_FAKE=1). Pour le pool
# reel, definir avant l'appel :
#
#   GANDAL_HV_FAKE=0 GANDAL_HV_PASSWORD_FILE=... GANDAL_HV_CA_FILE=... \
#   GANDAL_IT_DELAY=5 scripts/run_hypervisor_integration.sh ../gandal-hypervisor
#
# La cellule reste en bac a sable (sdk-it-*, 1 vCPU, 1 Go, 2 VM au plus) : ce
# script refuse de la lancer avec un autre perimetre.
set -euo pipefail

CELL_DIR=$(cd "${1:?chemin du depot gandal-hypervisor}" && pwd)
CELL_PYTHON=${2:-$CELL_DIR/.venv/bin/python}
PORT=${GANDAL_IT_HYPERVISOR_PORT:-8771}
WORK=$(mktemp -d)
LOG="$WORK/cell.log"

if [[ "${GANDAL_HV_POLICY:-sandbox}" != "sandbox" ]]; then
    echo "Les tests d'integration n'acceptent que GANDAL_HV_POLICY=sandbox." >&2
    exit 1
fi

cleanup() {
    if [[ -n "${CELL_PID:-}" ]]; then
        kill "$CELL_PID" 2>/dev/null || true
        wait "$CELL_PID" 2>/dev/null || true
    fi
    rm -rf "$WORK"
}
trap cleanup EXIT

if curl -s -o /dev/null "http://127.0.0.1:$PORT/"; then
    echo "Le port $PORT est deja occupe ; liberez-le ou definissez GANDAL_IT_HYPERVISOR_PORT." >&2
    exit 1
fi

# Jeton ephemere, lisible par le seul utilisateur courant.
(umask 077 && head -c 32 /dev/urandom | base64 > "$WORK/token")

(
    cd "$CELL_DIR"
    GANDAL_HV_FAKE=${GANDAL_HV_FAKE:-1} \
    GANDAL_HV_POLICY=sandbox \
    GANDAL_HV_TOKEN_FILE="$WORK/token" \
    GANDAL_HV_HOST=127.0.0.1 \
    GANDAL_HV_PORT="$PORT" \
        exec "$CELL_PYTHON" -m gandal_hypervisor
) >"$LOG" 2>&1 &
CELL_PID=$!

for _ in $(seq 1 60); do
    if curl -s -o /dev/null "http://127.0.0.1:$PORT/health"; then
        break
    fi
    if ! kill -0 "$CELL_PID" 2>/dev/null; then
        echo "La cellule s'est arretee au demarrage :" >&2
        cat "$LOG" >&2
        exit 1
    fi
    sleep 0.5
done
head -1 "$LOG" >&2  # « FAUX POOL » ou « pool ... » : on sait contre quoi on teste

GANDAL_IT_HYPERVISOR_ENDPOINT="http://127.0.0.1:$PORT" \
GANDAL_IT_HYPERVISOR_TOKEN=$(cat "$WORK/token") \
    python -m pytest -q tests/integration_hypervisor
