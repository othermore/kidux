# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4h-plan.md, step 4.41: Kydux, a door to the Kidux family's game
# (D85, D120), installs from the archive with kidux-webapps; while it is
# installed Chromium's policy allows the game's host and its counting's,
# and never kidux.org; its Chromium opens the game, walled in to them; and
# it is removed without a trace of the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
KYDUX=/usr/share/kidux/modules/kydux
POLICY=/etc/chromium/policies/managed/kidux.json
HOSTS='"analytics.google.com", "google-analytics.com", "googletagmanager.com", "kidux.goatcounter.com", "kydux.kidux.org"'

check "kidux-module-kydux installs through the daemon, with kidux-webapps" \
    sh -c "$ADMIN_AS install kydux | grep -q '^installed ' && dpkg -s kidux-webapps >/dev/null"
check "its manifest, icon and Spanish words are in place, and nothing of the game's" \
    sh -c "test -f $KYDUX/module.toml && test -f $KYDUX/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-kydux.mo \
           && test ! -e /usr/share/kidux/webapps/kydux"
check "while it is installed, the policy allows the game and its counting, and not kidux.org" \
    sh -c "python3 -c 'import json, sys; sys.exit(json.load(open(sys.argv[1]))[\"URLAllowlist\"] != [\"127.0.0.1:8123\", $HOSTS, \"blob:*\"])' $POLICY"
check "its Chromium opens the game, walled in to it, without WebGL in software" \
    sh -c "command=\$(runuser -u marta -- /usr/libexec/kidux-webapp --print kydux) \
           && echo \"\$command\" | grep -qF -- \"'--app=https://kydux.kidux.org/?from=kidux'\" \
           && echo \"\$command\" | grep -qF -- ';kydux.kidux.org;*.kydux.kidux.org' \
           && ! echo \"\$command\" | grep -qE -- \"[;']\\*?\\.?kidux\\.org[;']\" \
           && ! echo \"\$command\" | grep -q -- --enable-unsafe-swiftshader"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'kydux off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove kydux | grep -q '^removed ' && test ! -e $KYDUX \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-kydux.*')\""
check "and the policy went with the server, installed for it alone (D100)" \
    sh -c "test ! -e $POLICY"
