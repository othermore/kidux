# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4e-plan.md, step 4.27: Kig installs from the archive with the Qt
# platform plugin a Wayland session needs, and is removed without a trace
# of the module's own, Kig with it (D100).

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
KIG=/usr/share/kidux/modules/kig

check "kidux-module-kig installs through the daemon" \
    sh -c "$ADMIN_AS install kig | grep -q '^installed '"
check "it brings Kig and qtwayland5, without which it opens no window" \
    sh -c "dpkg -s kig qtwayland5 >/dev/null"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'kig off'"
check "its manifest, icon, starter, restrictions and Spanish words are in place" \
    sh -c "test -f $KIG/module.toml && test -f $KIG/icon.svg \
           && test -x /usr/libexec/kidux-module-kig \
           && grep -qx 'ghns=false' $KIG/kde/kdeglobals \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-kig.mo"
check "removing it leaves nothing of the module behind, and takes Kig with it" \
    sh -c "$ADMIN_AS remove kig | grep -q '^removed ' && test ! -e $KIG \
           && test ! -e /usr/libexec/kidux-module-kig \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-kig.*')\" \
           && [ \"\$(dpkg-query -W -f '\${db:Status-Status}' kig 2>/dev/null)\" != installed ]"
