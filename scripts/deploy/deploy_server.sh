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
DEPLOY_USER="$(id -un)"

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

run_with_sudo() {
  if [[ "${EUID}" -eq 0 ]]; then
    "$@"
    return
  fi

  if command_exists sudo && sudo -n true 2>/dev/null; then
    sudo "$@"
    return
  fi

  echo "Missing required command and passwordless sudo is not available: $*" >&2
  echo "Install Podman on the server manually, or deploy with a SERVER_USER that can run sudo without a password." >&2
  exit 1
}

install_podman_if_missing() {
  if command_exists podman; then
    return
  fi

  if [[ -f /etc/debian_version ]] && command_exists apt-get; then
    echo "Podman is not installed. Installing podman with apt-get..."
    run_with_sudo apt-get update
    run_with_sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y \
      podman \
      uidmap \
      dbus-user-session \
      slirp4netns \
      fuse-overlayfs
    return
  fi

  echo "Podman is not installed and this script only auto-installs it on Debian/Ubuntu hosts." >&2
  echo "Install Podman on the server, then rerun the deployment." >&2
  exit 1
}

enable_linger_if_possible() {
  if ! command_exists loginctl; then
    return
  fi

  if loginctl show-user "${DEPLOY_USER}" >/dev/null 2>&1; then
    if loginctl show-user "${DEPLOY_USER}" -p Linger --value 2>/dev/null | grep -qx yes; then
      return
    fi
  fi

  if [[ "${EUID}" -ne 0 ]] && (! command_exists sudo || ! sudo -n true 2>/dev/null); then
    echo "Warning: passwordless sudo is not available; skipping loginctl enable-linger ${DEPLOY_USER}." >&2
    echo "Run it manually if dashboard services stop after SSH exits." >&2
    return
  fi

  echo "Enabling lingering for ${DEPLOY_USER} so user services keep running after SSH exits..."
  run_with_sudo loginctl enable-linger "${DEPLOY_USER}"
}

install_podman_if_missing
enable_linger_if_possible

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
  data2001 run-workflow

systemctl --user enable --now data2001-dashboard.service
systemctl --user restart data2001-dashboard.service

echo "Deployment completed with image ${IMAGE_REF}"
