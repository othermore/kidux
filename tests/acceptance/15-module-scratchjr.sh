# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4-plan.md, step 4.6: ScratchJr, from its community desktop port with
# the Electron it runs in (D68, D69), installs from the archive with every
# library its binaries need, and is removed without a trace of the module's
# own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
SCRATCHJR=/usr/share/kidux/modules/scratchjr
APP=/usr/lib/kidux-module-scratchjr

check "kidux-module-scratchjr installs through the daemon" \
    sh -c "$ADMIN_AS install scratchjr | grep -q '^installed '"
check "its manifest, icon, Spanish words, starter and app are in place" \
    sh -c "test -f $SCRATCHJR/module.toml && test -f $SCRATCHJR/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-scratchjr.mo \
           && test -x /usr/libexec/kidux-module-scratchjr && test -x $APP/ScratchJr \
           && test -f $APP/resources/app.asar"
check "every library its binaries link to is on the machine" \
    sh -c "test \"\$(for f in $APP/ScratchJr $APP/*.so*; do ldd \$f; done | grep -c 'not found')\" = 0"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'scratchjr off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove scratchjr | grep -q '^removed ' && test ! -e $SCRATCHJR && test ! -e $APP \
           && test ! -e /usr/libexec/kidux-module-scratchjr \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-scratchjr.*')\""
