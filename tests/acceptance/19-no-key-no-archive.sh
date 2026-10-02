# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# docs/dev/packaging.md, "Testing before a real machine".
#
# Without the key, the same archive is refused. Last: it breaks the machine's
# configuration on purpose.

# The negative half, and the one that gives the others their meaning:
# without the key, the same archive must be rejected. Run last, because it
# deliberately breaks the machine's configuration.
check "removing the key leaves the source in place" \
    dpkg --remove --force-depends kidux-archive-keyring

# The exit status is no use here: apt treats an unverifiable repository as
# a warning, keeps the indexes it already had and still exits 0. What has
# to be true is that verification failed, and failed on our archive rather
# than on something else that happened to go wrong.
apt-get update >/tmp/check.out 2>&1 || true
if grep -qi 'signature verification' /tmp/check.out \
   && grep -q 'kidux.local' /tmp/check.out; then
    echo "PASS  apt refuses the archive once the key is gone"
else
    echo "FAIL  apt still accepted the archive with no key installed"
    sed 's/^/      /' /tmp/check.out
    failures=$((failures + 1))
fi

# Worth knowing, and worth saying in the install guide: because apt only
# warns, a machine that lost the keyring does not break. It quietly stops
# receiving updates, which on a child's computer is the kind of failure
# nobody notices for months.
