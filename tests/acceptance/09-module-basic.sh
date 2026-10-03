# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4b-plan.md, step 4.10: BASIC, wwwBASIC in an editor of Kidux's own
# with its guide beside it (D84), installs from the archive with
# kidux-webapps, is served under /basic/ with every language's guide in its
# page, and is removed without a trace of the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
BASIC=/usr/share/kidux/modules/basic
SITE=/usr/share/kidux/webapps/basic

check "kidux-module-basic installs through the daemon, with kidux-webapps" \
    sh -c "$ADMIN_AS install basic | grep -q '^installed ' && dpkg -s kidux-webapps >/dev/null"
check "its manifest, icon, Spanish words, page and wwwBASIC's licence are in place" \
    sh -c "test -f $BASIC/module.toml && test -f $BASIC/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-basic.mo \
           && test -f $SITE/index.html && test -f $SITE/wwwbasic/LICENSE"
check "the server answers for the page, with its title and the Spanish guide" \
    sh -c "for _ in \$(seq 20); do curl -fsS 'http://127.0.0.1:8123/basic/?lang=es' > /tmp/basic.html && break; sleep 0.5; done \
           && grep -q '<title>BASIC</title>' /tmp/basic.html && grep -q 'Ejecutar' /tmp/basic.html \
           && grep -q 'PING' /tmp/basic.html; status=\$?; rm -f /tmp/basic.html; exit \$status"
check "the server answers for wwwBASIC, as JavaScript, and the machine's and the guide's scripts" \
    sh -c "curl -fsS -o /dev/null -w '%{content_type}' http://127.0.0.1:8123/basic/wwwbasic/wwwbasic.mjs | grep -q '^text/javascript' \
           && curl -fsS -o /dev/null http://127.0.0.1:8123/basic/machine.js \
           && curl -fsS -o /dev/null http://127.0.0.1:8123/basic/guide.js \
           && curl -fsS -o /dev/null http://127.0.0.1:8123/basic/runner.html"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'basic off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove basic | grep -q '^removed ' && test ! -e $BASIC && test ! -e $SITE \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-basic.*')\""
