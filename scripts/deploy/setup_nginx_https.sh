#!/usr/bin/env bash
set -euo pipefail

DOMAIN="kscii.tech"
CERTBOT_EMAIL="xuejian-fang@outlook.com"
DASHBOARD_UPSTREAM="http://127.0.0.1:8050"
NGINX_CONF="/etc/nginx/conf.d/data2001.conf"

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

  echo "This script must run as root or as a user with passwordless sudo." >&2
  exit 1
}

require_command() {
  local name="$1"
  if command_exists "${name}"; then
    return
  fi

  echo "Missing required command: ${name}" >&2
  exit 1
}

enable_epel_10() {
  require_command dnf

  echo "Enabling CentOS Stream 10 CRB and EPEL repositories..."
  run_with_sudo dnf config-manager --set-enabled crb
  run_with_sudo dnf install -y \
    https://dl.fedoraproject.org/pub/epel/epel-release-latest-10.noarch.rpm
}

install_packages() {
  echo "Installing Nginx and Certbot packages..."
  run_with_sudo dnf install -y nginx certbot python3-certbot-nginx
}

write_nginx_config() {
  echo "Writing ${NGINX_CONF}..."
  run_with_sudo tee "${NGINX_CONF}" >/dev/null << EOF
server {
    listen 80;
    server_name ${DOMAIN};

    location / {
        proxy_pass ${DASHBOARD_UPSTREAM};
        proxy_http_version 1.1;

        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";

        proxy_read_timeout 300;
        proxy_redirect off;
    }
}
EOF
}

open_firewalld_ports_if_active() {
  if ! command_exists firewall-cmd; then
    return
  fi

  if ! firewall-cmd --state >/dev/null 2>&1; then
    return
  fi

  echo "Opening http/https services in firewalld..."
  run_with_sudo firewall-cmd --permanent --add-service=http
  run_with_sudo firewall-cmd --permanent --add-service=https
  run_with_sudo firewall-cmd --reload
}

configure_nginx() {
  echo "Validating and starting Nginx..."
  run_with_sudo nginx -t
  run_with_sudo systemctl enable --now nginx
}

issue_certificate() {
  echo "Requesting Let's Encrypt certificate for ${DOMAIN}..."
  run_with_sudo certbot --nginx \
    -d "${DOMAIN}" \
    --agree-tos \
    -m "${CERTBOT_EMAIL}" \
    --redirect \
    --non-interactive
}

print_checks() {
  cat << EOF
Nginx HTTPS setup completed.

Recommended checks:
  systemctl --user status data2001-dashboard.service
  curl -I ${DASHBOARD_UPSTREAM}
  nginx -t
  systemctl status nginx
  curl -I http://${DOMAIN}
  curl -I https://${DOMAIN}
  systemctl list-timers | grep certbot
EOF
}

enable_epel_10
install_packages
write_nginx_config
open_firewalld_ports_if_active
configure_nginx
issue_certificate
print_checks
