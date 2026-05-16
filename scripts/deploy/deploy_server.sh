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
APP_CONFIG_FILE="${DATA2001_CONFIG_DIR}/local.yaml"
DEPLOY_USER="$(id -un)"
PODMAN_PACKAGES=(
  podman
  uidmap
  dbus-user-session
  dbus-x11
  slirp4netns
  fuse-overlayfs
)

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

require_file() {
  local path="$1"
  local example="$2"

  if [[ -f "${path}" ]]; then
    return
  fi

  echo "Missing required deployment config: ${path}" >&2
  echo "Create it manually on the server before deploying. Template: ${example}" >&2
  exit 1
}

quadlet_available() {
  podman quadlet --help >/dev/null 2>&1 && return 0

  [[ -x /usr/lib/systemd/user-generators/podman-user-generator ]] && return 0
  [[ -x /lib/systemd/user-generators/podman-user-generator ]] && return 0
  [[ -x /usr/lib/systemd/system-generators/podman-system-generator ]] && return 0
  [[ -x /lib/systemd/system-generators/podman-system-generator ]] && return 0

  return 1
}

install_podman_packages() {
  if [[ ! -f /etc/debian_version ]] || ! command_exists apt-get; then
    return 1
  fi

  run_with_sudo apt-get update

  if command_exists apt-cache && apt-cache policy podman | grep -q bookworm-backports; then
    echo "Installing Podman packages from bookworm-backports for Quadlet support..."
    run_with_sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y -t bookworm-backports "${PODMAN_PACKAGES[@]}"
    return
  fi

  echo "Installing Podman packages with apt-get..."
  run_with_sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y "${PODMAN_PACKAGES[@]}"
}

ensure_podman_with_quadlet() {
  if command_exists podman && quadlet_available; then
    return
  fi

  if command_exists podman; then
    echo "Podman is installed, but Quadlet support was not found. Updating Podman packages..."
  else
    echo "Podman is not installed. Installing Podman packages..."
  fi

  if ! install_podman_packages; then
    echo "This script only auto-installs Podman on Debian/Ubuntu hosts." >&2
    echo "Install Podman with Quadlet support on the server, then rerun the deployment." >&2
    exit 1
  fi

  if ! command_exists podman; then
    echo "Podman is still unavailable after installation." >&2
    exit 1
  fi

  if ! quadlet_available; then
    podman --version >&2 || true
    echo "Podman is installed, but Quadlet support is still unavailable." >&2
    echo "Install Podman 4.4+ from backports or another supported repository, then rerun the deployment." >&2
    exit 1
  fi
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

ensure_podman_with_quadlet
enable_linger_if_possible

mkdir -p "${SYSTEMD_DIR}" "${DATA2001_CONFIG_DIR}"

require_file "${APP_ENV_FILE}" "${REPO_ROOT}/containers/env/app.env.example"
require_file "${POSTGRES_ENV_FILE}" "${REPO_ROOT}/containers/env/postgres.env.example"
require_file "${APP_CONFIG_FILE}" "${REPO_ROOT}/configs/example.yaml"

if ! grep -qx "DATA2001_CONFIG=/app/configs/local.yaml" "${APP_ENV_FILE}"; then
  echo "${APP_ENV_FILE} must include exactly: DATA2001_CONFIG=/app/configs/local.yaml" >&2
  echo "The server file ${APP_CONFIG_FILE} is mounted there inside the app container." >&2
  exit 1
fi

cp "${REPO_ROOT}/containers/quadlet/data2001.network" "${SYSTEMD_DIR}/data2001.network"
cp "${REPO_ROOT}/containers/quadlet/data2001-postgis.container" "${SYSTEMD_DIR}/data2001-postgis.container"
sed "s#ghcr.io/OWNER/REPO/data2001-app:latest#${IMAGE_REF}#g" \
  "${REPO_ROOT}/containers/quadlet/data2001-dashboard.container" \
  > "${SYSTEMD_DIR}/data2001-dashboard.container"

systemctl --user daemon-reload

if ! systemctl --user cat data2001-postgis.service >/dev/null 2>&1; then
  echo "Quadlet did not generate data2001-postgis.service." >&2
  echo "Podman version: $(podman --version)" >&2
  echo "Quadlet files in ${SYSTEMD_DIR}:" >&2
  ls -la "${SYSTEMD_DIR}" >&2
  exit 1
fi

if [[ -n "${GHCR_USERNAME:-}" && -n "${GHCR_TOKEN:-}" ]]; then
  echo "${GHCR_TOKEN}" | podman login ghcr.io -u "${GHCR_USERNAME}" --password-stdin
fi

podman pull "${IMAGE_REF}"

systemctl --user start data2001-postgis.service

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
  --volume "${APP_CONFIG_FILE}:/app/configs/local.yaml:ro,z" \
  "${IMAGE_REF}" \
  data2001 reset-db --yes

podman run --rm \
  --network data2001 \
  --env-file "${APP_ENV_FILE}" \
  --volume "${APP_CONFIG_FILE}:/app/configs/local.yaml:ro,z" \
  "${IMAGE_REF}" \
  data2001 run-workflow

systemctl --user restart data2001-dashboard.service

echo "Deployment completed with image ${IMAGE_REF}"
