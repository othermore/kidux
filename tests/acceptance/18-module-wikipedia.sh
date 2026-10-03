# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4b-plan.md, step 4.14: Wikipedia, a door to the encyclopedia in the
# child's language (D85, D87), installs from the archive with kidux-webapps;
# while it is installed Chromium's policy allows Wikipedia and its sister
# projects, its Chromium opens the child's language's edition walled in to
# them, and it is removed without a trace of the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
WIKI=/usr/share/kidux/modules/wikipedia
POLICY=/etc/chromium/policies/managed/kidux.json
HOSTS='"mediawiki.org", "wikibooks.org", "wikidata.org", "wikifunctions.org", "wikimedia.org", "wikinews.org", "wikipedia.org", "wikiquote.org", "wikisource.org", "wikiversity.org", "wikivoyage.org", "wiktionary.org"'

check "kidux-module-wikipedia installs through the daemon, with kidux-webapps" \
    sh -c "$ADMIN_AS install wikipedia | grep -q '^installed ' && dpkg -s kidux-webapps >/dev/null"
check "its manifest, icon and Spanish words are in place" \
    sh -c "test -f $WIKI/module.toml && test -f $WIKI/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-wikipedia.mo"
check "while it is installed, the policy allows Wikipedia and its sister projects" \
    sh -c "python3 -c 'import json, sys; sys.exit(json.load(open(sys.argv[1]))[\"URLAllowlist\"] != [\"127.0.0.1:8123\", $HOSTS, \"blob:*\"])' $POLICY"
check "its Chromium opens the child's language's edition, walled in to them" \
    sh -c "command=\$(runuser -u marta -- env LC_ALL=es_ES.UTF-8 /usr/libexec/kidux-webapp --print wikipedia) \
           && echo \"\$command\" | grep -q -- ' --app=https://es.wikipedia.org/\$' \
           && echo \"\$command\" | grep -qF -- ';wikipedia.org;*.wikipedia.org;' \
           && ! echo \"\$command\" | grep -q -- --enable-unsafe-swiftshader \
           && runuser -u marta -- env LC_ALL=C.UTF-8 /usr/libexec/kidux-webapp --print wikipedia \
              | grep -q -- ' --app=https://en.wikipedia.org/\$'"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'wikipedia off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove wikipedia | grep -q '^removed ' && test ! -e $WIKI \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-wikipedia.*')\""
check "and the policy no longer allows its hosts" \
    sh -c "python3 -c 'import json, sys; sys.exit(json.load(open(sys.argv[1]))[\"URLAllowlist\"] != [\"127.0.0.1:8123\", \"blob:*\"])' $POLICY"
