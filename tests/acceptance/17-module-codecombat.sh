# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4b-plan.md, step 4.13: CodeCombat, a door to the CodeCombat website
# (D85, D86), installs from the archive with kidux-webapps; while it is
# installed Chromium's policy allows its site, its Chromium opens on the
# module's own Connecting page and is walled in to the site (phase-4c-plan.md,
# 4.17), and it is removed without a trace of the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
COMBAT=/usr/share/kidux/modules/codecombat
POLICY=/etc/chromium/policies/managed/kidux.json

check "kidux-module-codecombat installs through the daemon, with kidux-webapps" \
    sh -c "$ADMIN_AS install codecombat | grep -q '^installed ' && dpkg -s kidux-webapps >/dev/null"
check "its manifest, icon, sign-in script, Connecting page and Spanish words are in place, and nothing of CodeCombat's" \
    sh -c "test -f $COMBAT/module.toml && test -f $COMBAT/icon.svg && test -f $COMBAT/sign-in.js \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-codecombat.mo \
           && test \"\$(ls /usr/share/kidux/webapps/codecombat)\" = index.html"
check "while it is installed, the policy allows its site" \
    sh -c "python3 -c 'import json, sys; sys.exit(json.load(open(sys.argv[1]))[\"URLAllowlist\"] != [\"127.0.0.1:8123\", \"codecombat.com\", \"blob:*\"])' $POLICY"
check "its Chromium opens on its own page, walled in to the site, without WebGL in software" \
    sh -c "command=\$(runuser -u marta -- /usr/libexec/kidux-webapp --print codecombat) \
           && echo \"\$command\" | grep -qF -- \" '--app=http://127.0.0.1:8123/codecombat/?lang=\" \
           && echo \"\$command\" | grep -qF -- \"--proxy-server=127.0.0.1:1 '--proxy-bypass-list=127.0.0.1;codecombat.com;*.codecombat.com'\" \
           && ! echo \"\$command\" | grep -q -- --enable-unsafe-swiftshader"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'codecombat off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove codecombat | grep -q '^removed ' && test ! -e $COMBAT \
           && test ! -e /usr/share/kidux/webapps/codecombat \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-codecombat.*')\""
check "and the policy no longer allows its site" \
    sh -c "python3 -c 'import json, sys; sys.exit(json.load(open(sys.argv[1]))[\"URLAllowlist\"] != [\"127.0.0.1:8123\", \"blob:*\"])' $POLICY"
