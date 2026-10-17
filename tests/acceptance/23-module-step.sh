# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4e-plan.md, step 4.29: Step installs from the archive with the Qt
# platform plugin a Wayland session needs, and is removed without a trace
# of the module's own, Step with it (D100).

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
STEP=/usr/share/kidux/modules/step

check "kidux-module-step installs through the daemon" \
    sh -c "$ADMIN_AS install step | grep -q '^installed '"
check "it brings Step and qt6-wayland, without which it opens no window" \
    sh -c "dpkg -s step qt6-wayland >/dev/null"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'step off'"
check "its manifest, icon, starter, restrictions and Spanish words are in place" \
    sh -c "test -f $STEP/module.toml && test -f $STEP/icon.svg \
           && test -x /usr/libexec/kidux-module-step \
           && grep -qx 'ghns=false' $STEP/kde/kdeglobals \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-step.mo"
check "removing it leaves nothing of the module behind, and takes Step with it" \
    sh -c "$ADMIN_AS remove step | grep -q '^removed ' && test ! -e $STEP \
           && test ! -e /usr/libexec/kidux-module-step \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-step.*')\" \
           && [ \"\$(dpkg-query -W -f '\${db:Status-Status}' step 2>/dev/null)\" != installed ]"
