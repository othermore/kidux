#!/bin/sh
# One-time setup of a CI container: the counterpart of ci/setup-dev-host.sh.
#
#   ci/setup-ci-host.sh <builder>     as root, in a fresh debian:trixie container
#
# GitHub Actions runs the same ci/test-release.sh the development machine runs
# before a release (docs/dev/packaging.md, "Continuous integration"). This
# gives the container what the development machine has: the toolchain of
# docs/dev/dev-environment.md section 5, an unprivileged user to build as,
# an archive root, the name kidux.local, KVM for the test machines, and a
# signing key made for this run alone. The archive's real key is never in CI.
#
# Safe to run again; it converges on the same state.

set -eu

BUILDER="${1:-builder}"
ARCHIVE_ROOT=/srv/kidux-apt
KEY_DIR=/srv/kidux-ci-key

if [ "$(id -u)" -ne 0 ]; then
    echo "$0 must run as root" >&2
    exit 1
fi

echo "==> Toolchain"
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
    build-essential ca-certificates curl debhelper devscripts dh-python gh git gettext \
    gnupg iproute2 librsvg2-bin libyaml-libyaml-perl lintian mmdebstrap openssh-client \
    ovmf pamtester pybuild-plugin-pyproject pyflakes3 python3 python3-all \
    python3-dbusmock python3-gi python3-pytest python3-tomli-w qemu-system-x86 \
    qemu-utils reprepro sbuild uidmap xz-utils

# sbuild's unshare mode brings the network up inside the build with ip, and
# bind-mounts the host's /dev/console, which a container does not have.
[ -e /dev/console ] || mknod -m 600 /dev/console c 5 1 || true

echo "==> $BUILDER, who builds and tests, as on the development machine"
if ! id "$BUILDER" >/dev/null 2>&1; then
    useradd --create-home --shell /bin/bash "$BUILDER"
fi
# sbuild's and mmdebstrap's unshare mode map the build's users through these.
grep -q "^$BUILDER:" /etc/subuid || echo "$BUILDER:100000:65536" >> /etc/subuid
grep -q "^$BUILDER:" /etc/subgid || echo "$BUILDER:100000:65536" >> /etc/subgid
# The test machines run under KVM.
if [ -e /dev/kvm ]; then
    chmod 666 /dev/kvm
fi

echo "==> Archive root $ARCHIVE_ROOT, served as http://kidux.local/apt"
mkdir -p "$ARCHIVE_ROOT" /srv/www
chown "$BUILDER:" "$ARCHIVE_ROOT"
ln -sfn "$ARCHIVE_ROOT" /srv/www/apt
grep -q " kidux.local\$" /etc/hosts || echo "127.0.0.1 kidux.local" >> /etc/hosts

echo "==> A signing key for this run only"
mkdir -p "$KEY_DIR"
chown "$BUILDER:" "$KEY_DIR"
runuser -u "$BUILDER" -- sh -c "
    set -e
    export GNUPGHOME=$KEY_DIR/gnupg
    mkdir -p -m 700 \$GNUPGHOME
    if ! gpg --list-secret-keys --with-colons 2>/dev/null | grep -q '^sec'; then
        gpg --batch --pinentry-mode loopback --passphrase '' \
            --quick-generate-key 'Kidux CI throwaway key (one run only) <ci@kidux.invalid>' \
            ed25519 sign 1d
    fi
    gpg --with-colons --list-secret-keys | awk -F: '/^fpr/ { print \$10; exit }' \
        > $KEY_DIR/fingerprint
    gpg --export > $KEY_DIR/public.pgp
"

echo "==> The build chroot"
runuser -u "$BUILDER" -- sh -c '
    set -e
    mkdir -p "$HOME/.cache/sbuild"
    [ -f "$HOME/.cache/sbuild/trixie-amd64.tar" ] ||
        mmdebstrap --mode=unshare --variant=buildd trixie "$HOME/.cache/sbuild/trixie-amd64.tar"
'

echo "==> Ready. Build and test as $BUILDER with:"
echo "    KIDUX_SIGNING_KEY=\$(cat $KEY_DIR/fingerprint) GNUPGHOME=$KEY_DIR/gnupg \\"
echo "    KIDUX_ARCHIVE_PUBLIC_KEY=$KEY_DIR/public.pgp ci/test-release.sh <label>"
