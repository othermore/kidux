# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4-plan.md, step 4.4: Scratch's editor, built at development time
# (D68), installs from the archive with kidux-webapps, is served under
# /scratch/, and is removed without a trace of the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
POLICY=/etc/chromium/policies/managed/kidux.json
SCRATCH=/usr/share/kidux/modules/scratch
SITE=/usr/share/kidux/webapps/scratch

check "kidux-module-scratch installs through the daemon, with kidux-webapps" \
    sh -c "$ADMIN_AS install scratch | grep -q '^installed ' && dpkg -s kidux-webapps >/dev/null"
check "its manifest, icon, Spanish words and the editor are in place" \
    sh -c "test -f $SCRATCH/module.toml && test -f $SCRATCH/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-scratch.mo \
           && test -f $SITE/index.html && test -f $SITE/gui.js && test -f $SITE/LICENSE"
check "the server answers for the editor, its page and its program" \
    sh -c "for _ in \$(seq 20); do curl -fsS http://127.0.0.1:8123/scratch/ | grep -qi '<title>' && break; sleep 0.5; done \
           && curl -fsS -o /dev/null http://127.0.0.1:8123/scratch/gui.js"
check "the policy, written again when it came, allows the hosts its library comes from" \
    sh -c "python3 -c 'import json, sys; sys.exit(json.load(open(sys.argv[1]))[\"URLAllowlist\"] != [\"127.0.0.1:8123\", \"assets.scratch.mit.edu\", \"cdn.assets.scratch.mit.edu\", \"blob:*\"])' $POLICY"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'scratch off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove scratch | grep -q '^removed ' && test ! -e $SCRATCH && test ! -e $SITE \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-scratch.*')\""
check "and when it went, no longer" \
    sh -c "python3 -c 'import json, sys; sys.exit(json.load(open(sys.argv[1]))[\"URLAllowlist\"] != [\"127.0.0.1:8123\", \"blob:*\"])' $POLICY"
