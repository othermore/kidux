# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4d-plan.md, step 4.23: Gmail, a door to Gmail's website, installs
# from the archive with kidux-webapps; while it is installed Chromium's
# policy allows Gmail's hosts and the accounts host of every country's
# Google, and nothing else of Google; its Chromium opens Google's sign-in
# with the child's address and language in it; and it is removed without a
# trace of the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
GMAIL=/usr/share/kidux/modules/gmail
POLICY=/etc/chromium/policies/managed/kidux.json

check "kidux-module-gmail installs through the daemon, with kidux-webapps" \
    sh -c "$ADMIN_AS install gmail | grep -q '^installed ' && dpkg -s kidux-webapps >/dev/null"
check "its manifest, icon and Spanish words are in place" \
    sh -c "test -f $GMAIL/module.toml && test -f $GMAIL/icon.svg \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-gmail.mo"
check "while it is installed, the policy allows Gmail and every country's sign-in, not Google whole" \
    sh -c "python3 -c 'import json, sys; a = json.load(open(sys.argv[1]))[\"URLAllowlist\"]; \
sys.exit(not (\"mail.google.com\" in a and \"accounts.google.es\" in a and \"accounts.google.co.uk\" in a \
and \"google.com\" not in a and \"www.google.com\" not in a \
and len([h for h in a if h.startswith(\"accounts.google.\")]) == 187))' $POLICY"
check "its Chromium opens Google's sign-in with the child's address and language, walled in" \
    sh -c "command=\$(runuser -u marta -- env LC_ALL=es_ES.UTF-8 KIDUX_SETTING_EMAIL=marta@example.org \
               /usr/libexec/kidux-webapp --print gmail) \
           && echo \"\$command\" | grep -qF -- 'continue=https%3A%2F%2Fmail.google.com%2Fmail%2F&Email=marta%40example.org&hl=es' \
           && echo \"\$command\" | grep -qF -- ';mail.google.com;*.mail.google.com;' \
           && runuser -u marta -- env LC_ALL=C.UTF-8 /usr/libexec/kidux-webapp --print gmail \
              | grep -qF -- '&Email=&hl=en'"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'gmail off'"
check "removing it leaves nothing of the module behind" \
    sh -c "$ADMIN_AS remove gmail | grep -q '^removed ' && test ! -e $GMAIL \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-gmail.*')\""
check "and the policy went with the server, installed for it alone (D100)" \
    sh -c "test ! -e $POLICY"
