# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4-plan.md, step 4.7: Blockly Games, built at development time for
# use without the internet (D68), installs from the archive with
# kidux-webapps, is served under /blockly-games/ in every language it has,
# and is removed without a trace of the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
GAMES=/usr/share/kidux/modules/blockly-games
SITE=/usr/share/kidux/webapps/blockly-games

check "kidux-module-blockly-games installs through the daemon, with kidux-webapps" \
    sh -c "$ADMIN_AS install blockly-games | grep -q '^installed ' && dpkg -s kidux-webapps >/dev/null"
check "its manifest, icon, Spanish words and the games are in place" \
    sh -c "test -f $GAMES/module.toml && test -f $GAMES/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-blockly-games.mo \
           && test -f $SITE/index.html && test -f $SITE/maze.html && test -f $SITE/LICENSE"
check "the server answers for the games' page, their start, and a game's Spanish words" \
    sh -c "for _ in \$(seq 20); do curl -fsS 'http://127.0.0.1:8123/blockly-games/?lang=es' | grep -q '<title>Blockly Games' && break; sleep 0.5; done \
           && curl -fsS -o /dev/null http://127.0.0.1:8123/blockly-games/common/boot.js \
           && curl -fsS -o /dev/null http://127.0.0.1:8123/blockly-games/maze/generated/msg/es.js"
check "a game opens by the address the games' page links to, its name without .html" \
    sh -c "curl -fsS 'http://127.0.0.1:8123/blockly-games/maze?lang=es' | grep -qi '<html' \
           && curl -fsS 'http://127.0.0.1:8123/blockly-games/index?lang=es' | grep -qi '<html'"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'blockly-games off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove blockly-games | grep -q '^removed ' && test ! -e $GAMES && test ! -e $SITE \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-blockly-games.*')\""
