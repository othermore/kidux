# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4e-plan.md, step 4.28: Kalzium installs from the archive with the Qt
# platform plugin a Wayland session needs, and is removed without a trace
# of the module's own, Kalzium with it (D100).

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
KALZIUM=/usr/share/kidux/modules/kalzium

check "kidux-module-kalzium installs through the daemon" \
    sh -c "$ADMIN_AS install kalzium | grep -q '^installed '"
check "it brings Kalzium, its data and qt6-wayland, without which it opens no window" \
    sh -c "dpkg -s kalzium kalzium-data qt6-wayland >/dev/null"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'kalzium off'"
check "its manifest, icon, starter, restrictions and Spanish words are in place" \
    sh -c "test -f $KALZIUM/module.toml && test -f $KALZIUM/icon.svg \
           && test -x /usr/libexec/kidux-module-kalzium \
           && grep -qx 'ghns=false' $KALZIUM/kde/kdeglobals \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-kalzium.mo"
check "removing it leaves nothing of the module behind, and takes Kalzium with it" \
    sh -c "$ADMIN_AS remove kalzium | grep -q '^removed ' && test ! -e $KALZIUM \
           && test ! -e /usr/libexec/kidux-module-kalzium \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-kalzium.*')\" \
           && [ \"\$(dpkg-query -W -f '\${db:Status-Status}' kalzium 2>/dev/null)\" != installed ]"
