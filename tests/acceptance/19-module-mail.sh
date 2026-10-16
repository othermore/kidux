# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-4d-plan.md, step 4.22: Mail, Thunderbird as a child's mailbox,
# installs from the archive with Thunderbird and its languages; its policies
# bind Thunderbird while it is installed; its program, as a child with the
# settings an adult gave, writes the account into Thunderbird's user.js; and
# it is removed without a trace of the module's own.

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
MAIL=/usr/share/kidux/modules/mail
POLICIES=/etc/thunderbird/policies/policies.json

check "kidux-module-mail installs through the daemon, with Thunderbird in Spanish" \
    sh -c "$ADMIN_AS install mail | grep -q '^installed ' \
           && dpkg -s thunderbird thunderbird-l10n-es-es >/dev/null"
check "its manifest, icon, program and Spanish words are in place" \
    sh -c "test -f $MAIL/module.toml && test -f $MAIL/icon.svg \
           && test -x /usr/libexec/kidux-module-mail \
           && test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-mail.mo"
check "Thunderbird's policies are in place, whole, and the package's conffile" \
    sh -c "python3 -c 'import json, sys; p = json.load(open(sys.argv[1]))[\"policies\"]; \
sys.exit(not (p[\"DisableAppUpdate\"] and p[\"BlockAboutConfig\"] and \"Handlers\" in p \
and p[\"Preferences\"][\"browser.download.forbid_open_with\"][\"Status\"] == \"locked\"))' $POLICIES \
           && dpkg-query -W -f='\${Conffiles}' kidux-module-mail | grep -q $POLICIES"
check "as a child, with the settings an adult gave, it writes the account for Thunderbird" \
    sh -c "runuser -u marta -- env HOME=/home/marta XDG_CONFIG_HOME=/home/marta/.config/kidux/mail \
               LC_ALL=es_ES.UTF-8 KIDUX_SETTING_EMAIL=marta@example.org KIDUX_SETTING_NAME=Marta \
               KIDUX_SETTING_IMAP_HOST=imap.example.org KIDUX_SETTING_SMTP_HOST=smtp.example.org \
               /usr/libexec/kidux-module-mail --print > /var/tmp/mail-user.js \
           && grep -qF 'user_pref(\"mail.server.server1.hostname\", \"imap.example.org\");' /var/tmp/mail-user.js \
           && grep -qF 'user_pref(\"mail.identity.id1.useremail\", \"marta@example.org\");' /var/tmp/mail-user.js \
           && grep -qF 'user_pref(\"mail.server.server2.name\", \"Carpetas locales\");' /var/tmp/mail-user.js \
           && test \"\$(stat -c %a /home/marta/.config/kidux/mail/thunderbird)\" = 700"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'mail off'"
check "removing it leaves nothing of the module behind, its policies with it" \
    sh -c "$ADMIN_AS remove mail | grep -q '^removed ' && test ! -e $MAIL \
           && test ! -e $POLICIES && test ! -e /usr/libexec/kidux-module-mail \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-mail.*')\""
