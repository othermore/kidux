#!/bin/sh
# One-time privileged setup of the development host.
#
# Run as root:  sudo ci/setup-dev-host.sh
# Safe to run again; it converges on the same state.
#
# Everything the project builds afterwards runs unprivileged: sbuild works in
# unshare mode, reprepro writes to an archive root owned by the developer, and
# nginx only serves static files. This touches the build host only, never a
# machine that Kidux is installed on.

set -eu

DEV_USER="${SUDO_USER:-${1:-}}"
ARCHIVE_ROOT=/srv/kidux-apt
NGINX_SITE=/etc/nginx/sites-available/kidux-apt

if [ -z "$DEV_USER" ]; then
    echo "usage: sudo $0 [developer-username]" >&2
    exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
    echo "$0 must run as root" >&2
    exit 1
fi

DEV_GROUP="$(id -gn "$DEV_USER")"

# Tools the build chroot installs for itself, but that are also wanted outside a
# build: for running the tests and the linters while writing code, and for
# looking at an avatar without booting anything.
echo "==> Development tools"
apt-get install -y --no-install-recommends \
    gettext \
    librsvg2-bin \
    pyflakes3 \
    python3-gi \
    python3-pytest \
    python3-tomli-w

echo "==> Archive root $ARCHIVE_ROOT, owned by $DEV_USER:$DEV_GROUP"
mkdir -p "$ARCHIVE_ROOT"
chown "$DEV_USER:$DEV_GROUP" "$ARCHIVE_ROOT"
chmod 755 "$ARCHIVE_ROOT"

echo "==> nginx site serving $ARCHIVE_ROOT at /apt"
cat > "$NGINX_SITE" <<NGINX
# Kidux development apt archive, served on the LAN.
#
# The archive is signed, so it is served over plain HTTP like any Debian mirror:
# apt verifies the Release signature, not the transport.
#
# This is the default server: the archive has to answer whatever the client asks
# for, because a test VM reaches the host by IP (10.0.2.2 under QEMU user
# networking) while a real LAN machine asks for kidux.local over mDNS.
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name kidux.local kidux _;

    root /var/www/html;

    location /apt/ {
        alias $ARCHIVE_ROOT/;
        autoindex on;
    }

    # reprepro's own bookkeeping must never be served.
    location ~ ^/apt/(db|conf)/ {
        deny all;
    }
}
NGINX
ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/kidux-apt

# Debian's placeholder site claims default_server on port 80 and would take every
# request whose Host header we do not name. This host exists to serve the archive,
# so the placeholder goes. It stays in sites-available and is restored with:
#   ln -s ../sites-available/default /etc/nginx/sites-enabled/default
if [ -e /etc/nginx/sites-enabled/default ]; then
    echo "==> Disabling nginx's placeholder default site"
    rm -f /etc/nginx/sites-enabled/default
fi

nginx -t
systemctl reload nginx

if id -nG "$DEV_USER" | tr ' ' '\n' | grep -qx kvm; then
    echo "==> $DEV_USER is already in the kvm group"
else
    echo "==> Adding $DEV_USER to the kvm group, for accelerated test VMs"
    adduser "$DEV_USER" kvm >/dev/null
    echo "    $DEV_USER must log out and back in before it takes effect."
fi

echo
echo "Done. The archive is empty until ci/publish-local.sh runs."
