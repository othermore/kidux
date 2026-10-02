# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-3-plan.md, step 3.6: GCompris, the first real module, installs from
# the archive with the Qt platform plugin a Wayland session needs, and is
# removed without a trace of the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
GCOMPRIS=/usr/share/kidux/modules/gcompris

check "kidux-module-gcompris installs through the daemon" \
    sh -c "$ADMIN_AS install gcompris | grep -q '^installed '"
check "it brings GCompris and qt6-wayland, without which it opens no window" \
    sh -c "dpkg -s gcompris-qt gcompris-qt-data qt6-wayland >/dev/null"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'gcompris off'"
check "its manifest, icon and Spanish words are in place" \
    sh -c "test -f $GCOMPRIS/module.toml && test -f $GCOMPRIS/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-gcompris.mo"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove gcompris | grep -q '^removed ' && test ! -e $GCOMPRIS \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-gcompris.*')\""
