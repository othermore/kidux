# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4h-plan.md, step 4.42: Expedition Code, a door to the Expedition
# Code website (D85, D121), installs from the archive with kidux-webapps
# and a font of emoji, which its avatars are drawn with; while it is
# installed Chromium's policy allows the site's pages, its backend and its
# fonts, and nothing of YouTube's or of its counting's; its Chromium opens
# the site, walled in to them; and it is removed without a trace of the
# module's own, its font going with it.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
EXPEDITION=/usr/share/kidux/modules/expedition-code
POLICY=/etc/chromium/policies/managed/kidux.json
HOSTS='"expeditioncode.com", "fonts.googleapis.com", "fonts.gstatic.com", "spotted-shepherd-639.convex.cloud"'

check "kidux-module-expedition-code installs through the daemon, with kidux-webapps and a font of emoji" \
    sh -c "$ADMIN_AS install expedition-code | grep -q '^installed ' && dpkg -s kidux-webapps >/dev/null \
           && fc-list | grep -q 'Noto Color Emoji'"
check "its manifest, icon and Spanish words are in place, and nothing of the site's" \
    sh -c "test -f $EXPEDITION/module.toml && test -f $EXPEDITION/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-expedition-code.mo \
           && test ! -e /usr/share/kidux/webapps/expedition-code"
check "while it is installed, the policy allows its pages, its backend and its fonts, and nothing else" \
    sh -c "python3 -c 'import json, sys; sys.exit(json.load(open(sys.argv[1]))[\"URLAllowlist\"] != [\"127.0.0.1:8123\", $HOSTS, \"blob:*\"])' $POLICY"
check "its Chromium opens the site, walled in to it, without WebGL in software" \
    sh -c "command=\$(runuser -u marta -- /usr/libexec/kidux-webapp --print expedition-code) \
           && echo \"\$command\" | grep -qF -- ' --app=https://www.expeditioncode.com/' \
           && echo \"\$command\" | grep -qF -- ';expeditioncode.com;*.expeditioncode.com' \
           && ! echo \"\$command\" | grep -qE -- 'youtube|posthog' \
           && ! echo \"\$command\" | grep -q -- --enable-unsafe-swiftshader"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'expedition-code off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove expedition-code | grep -q '^removed ' && test ! -e $EXPEDITION \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-expedition-code.*')\""
check "and the font of emoji went with it, installed for it alone (D100)" \
    sh -c "! fc-list | grep -q 'Noto Color Emoji'"
check "and the policy went with the server, installed for it alone (D100)" \
    sh -c "test ! -e $POLICY"
