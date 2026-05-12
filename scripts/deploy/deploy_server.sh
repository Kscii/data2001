#!/usr/bin/env bash
set -euo pipefail

IMAGE_REF="${IMAGE_REF:-}"
if [[ -z "${IMAGE_REF}" ]]; then
  echo "IMAGE_REF is required, for example ghcr.io/owner/repo/data2001-app:latest" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SYSTEMD_DIR="${HOME}/.config/containers/systemd"
DATA2001_CONFIG_DIR="${HOME}/.config/data2001"
APP_ENV_FILE="${DATA2001_CONFIG_DIR}/app.env"
POSTGRES_ENV_FILE="${DATA2001_CONFIG_DIR}/postgres.env"

mkdir -p "${SYSTEMD_DIR}" "${DATA2001_CONFIG_DIR}"

if [[ ! -f "${APP_ENV_FILE}" ]]; then
  cp "${REPO_ROOT}/containers/env/app.env.example" "${APP_ENV_FILE}"
  echo "Created ${APP_ENV_FILE} from example. Review it before exposing the service publicly."
fi

if [[ ! -f "${POSTGRES_ENV_FILE}" ]]; then
  cp "${REPO_ROOT}/containers/env/postgres.env.example" "${POSTGRES_ENV_FILE}"
  echo "Created ${POSTGRES_ENV_FILE} from example. Review the password before exposing the service publicly."
fi

cp "${REPO_ROOT}/containers/quadlet/data2001.network" "${SYSTEMD_DIR}/data2001.network"
cp "${REPO_ROOT}/containers/quadlet/data2001-postgis.container" "${SYSTEMD_DIR}/data2001-postgis.container"
sed "s#ghcr.io/OWNER/REPO/data2001-app:latest#${IMAGE_REF}#g" \
  "${REPO_ROOT}/containers/quadlet/data2001-dashboard.container" \
  > "${SYSTEMD_DIR}/data2001-dashboard.container"

systemctl --user daemon-reload

if [[ -n "${GHCR_USERNAME:-}" && -n "${GHCR_TOKEN:-}" ]]; then
  echo "${GHCR_TOKEN}" | podman login ghcr.io -u "${GHCR_USERNAME}" --password-stdin
fi

podman pull "${IMAGE_REF}"

systemctl --user enable --now data2001-postgis.service

set -a
# shellcheck disable=SC1090
source "${POSTGRES_ENV_FILE}"
set +a

echo "Waiting for PostGIS to become ready..."
for _ in $(seq 1 60); do
  if podman exec data2001-postgis pg_isready -U "${POSTGRES_USER:-data2001}" -d "${POSTGRES_DB:-data2001}" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

podman exec data2001-postgis pg_isready -U "${POSTGRES_USER:-data2001}" -d "${POSTGRES_DB:-data2001}"

podman run --rm \
  --network data2001 \
  --env-file "${APP_ENV_FILE}" \
  "${IMAGE_REF}" \
  data2001 reset-db --yes

podman run --rm \
  --network data2001 \
  --env-file "${APP_ENV_FILE}" \
  "${IMAGE_REF}" \
  data2001 pipeline

systemctl --user enable --now data2001-dashboard.service
systemctl --user restart data2001-dashboard.service

echo "Deployment completed with image ${IMAGE_REF}"
