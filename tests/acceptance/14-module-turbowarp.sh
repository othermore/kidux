# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4-plan.md, step 4.5: TurboWarp, Scratch made faster, built at
# development time (D68), installs from the archive with kidux-webapps, is
# served under /turbowarp/ with its editor as the site's index, and is removed
# without a trace of the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
POLICY=/etc/chromium/policies/managed/kidux.json
TURBOWARP=/usr/share/kidux/modules/turbowarp
SITE=/usr/share/kidux/webapps/turbowarp

check "kidux-module-turbowarp installs through the daemon, with kidux-webapps" \
    sh -c "$ADMIN_AS install turbowarp | grep -q '^installed ' && dpkg -s kidux-webapps >/dev/null"
check "its manifest, icon, Spanish words and the editor, as the site's index, are in place" \
    sh -c "test -f $TURBOWARP/module.toml && test -f $TURBOWARP/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-turbowarp.mo \
           && cmp -s $SITE/index.html $SITE/editor.html && test -f $SITE/LICENSE"
check "the server answers for the editor and for the program its page names" \
    sh -c "for _ in \$(seq 20); do curl -fsS http://127.0.0.1:8123/turbowarp/ | grep -q '<title>TurboWarp' && break; sleep 0.5; done \
           && script=\$(curl -fsS http://127.0.0.1:8123/turbowarp/ | grep -o 'src=\"/turbowarp/js/[^\"]*editor[^\"]*\"' | head -1 | cut -d'\"' -f2) \
           && test -n \"\$script\" && curl -fsS -o /dev/null \"http://127.0.0.1:8123\$script\""
check "the policy, written again when it came, allows the hosts its library comes from" \
    sh -c "python3 -c 'import json, sys; sys.exit(json.load(open(sys.argv[1]))[\"URLAllowlist\"] != [\"127.0.0.1:8123\", \"assets.scratch.mit.edu\", \"cdn.assets.scratch.mit.edu\", \"blob:*\"])' $POLICY"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'turbowarp off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove turbowarp | grep -q '^removed ' && test ! -e $TURBOWARP && test ! -e $SITE \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-turbowarp.*')\""
check "and when it went, no longer" \
    sh -c "python3 -c 'import json, sys; sys.exit(json.load(open(sys.argv[1]))[\"URLAllowlist\"] != [\"127.0.0.1:8123\", \"blob:*\"])' $POLICY"
