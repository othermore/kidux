# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# docs/dev/packaging.md, "Testing before a real machine".
#
# The archive: the bootstrap packages by hand, then apt trusting it.

# The two bootstrap packages are fetched by hand over plain HTTP, from the
# fixed address the instructions give. Nothing is trusted yet.
check "bootstrap packages download from the archive" \
    sh -c "cd /var/tmp && \
           curl -fsSLO $ARCHIVE/bootstrap/testing/kidux-archive-keyring.deb && \
           curl -fsSLO $ARCHIVE/bootstrap/testing/kidux-apt-source.deb"

check "keyring and apt source install by hand" \
    sh -c "apt-get install -y --no-install-recommends \
           /var/tmp/kidux-archive-keyring.deb /var/tmp/kidux-apt-source.deb"

# In CI the archive is signed with a key made for that run, published beside
# it; the machine trusts it too. Nowhere else is there such a key, and the
# keyring is still the one file kidux.sources names, so removing the package
# still leaves apt trusting nothing (11-no-key-no-archive.sh).
if curl -fsS -o /var/tmp/extra-key.pgp "$ARCHIVE/extra-key.pgp" 2>/dev/null; then
    cat /var/tmp/extra-key.pgp >> /usr/share/keyrings/kidux-archive-keyring.pgp
fi

# The shipped file follows stable, which is right for a family's machine
# and wrong here: this run is what qualifies a package for stable in the
# first place. Following testing is the documented way to help develop
# Kidux, and it exercises the same shipped file rather than a copy.
check "the apt source can be pointed at testing" \
    sed -i 's/^Suites: stable$/Suites: testing/' \
        /etc/apt/sources.list.d/kidux.sources

# apt refuses a repository it cannot verify, so this passing is the
# signature check.
check "apt update accepts the signed archive" apt-get update

check "kidux-base comes from the Kidux archive, not Debian" \
    sh -c 'apt-cache policy kidux-base | grep -q kidux.local'
