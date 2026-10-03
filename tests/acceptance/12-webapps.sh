# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-3-plan.md, step 3.7: a web-application module installs with its
# server and Chromium; the server answers for the application and for
# nothing else, on the loopback address only, as a user of its own;
# Chromium's policy, written from the installed modules, is root's; and
# every module's Chromium is walled in by a proxy that answers nothing
# (D85).

ADMIN_AS="runuser -u debian -- /usr/local/bin/kidux-as"
SERVER=http://127.0.0.1:8123
POLICY=/etc/chromium/policies/managed/kidux.json

check "kidux-module-hello-web installs through the daemon, with kidux-webapps and Chromium" \
    sh -c "$ADMIN_AS install hello-web | grep -q '^installed ' \
           && dpkg -s kidux-webapps chromium >/dev/null"
# Chromium's own words, its pages and dialogs, in the child's language:
# its translations are a package of their own, which kidux-webapps brings,
# and kidux-webapp names the session's language.
check "Chromium's translations came with it, and kidux-webapp names the session's language" \
    sh -c "dpkg -s chromium-l10n >/dev/null && test -f /usr/lib/chromium/locales/es.pak \
           && runuser -u marta -- env LC_ALL=es_ES.UTF-8 /usr/libexec/kidux-webapp --print hello-web \
              | grep -q -- '--lang=es '"
check "the server answers for the application" \
    sh -c "for _ in \$(seq 20); do curl -fsS -o /dev/null $SERVER/hello-web/ && exit 0; sleep 0.5; done; exit 1"
check "and for nothing else: no listing, no way out of its directory" \
    sh -c "for path in / /nothing/ /hello-web/../../etc/passwd /../etc/passwd \
                       /hello-web/%2e%2e/%2e%2e/etc/passwd /%2e%2e/etc/passwd; do \
               code=\$(curl -s -o /dev/null -w '%{http_code}' --path-as-is $SERVER\$path); \
               case \$code in 403|404) ;; *) echo \"\$path answered \$code\"; exit 1 ;; esac; \
           done"
check "it listens on the loopback address and nowhere else" \
    sh -c "ss -ltnH 'sport = :8123' | awk '{ print \$4 }' | sort -u | grep -qx '127.0.0.1:8123' \
           && [ \"\$(ss -ltnH 'sport = :8123' | wc -l)\" -eq 1 ]"
check "it runs as a user made for it, without capabilities" \
    sh -c "systemctl show kidux-webapps -p DynamicUser -p CapabilityBoundingSet \
           | grep -qx 'DynamicUser=yes' && ! ps -o user= -C kidux-webapps | grep -qx root"
# D85: the policy is written from the installed modules, not shipped: with
# no module naming a host, it allows the server's address and blob:, the
# address of a file a page makes itself, which Scratch saves through (D75),
# and nothing else.
# A child saves and opens their projects as files: the file dialogs are
# open, a download asks in one where to keep it (D76), and is refused only
# when its type is dangerous.
check "Chromium's policy is root's and no package's conffile, blocks every address but the server's, and lets a child save and open files" \
    sh -c "stat -c '%U %a' $POLICY | grep -qx 'root 644' \
           && ! dpkg-query -W -f='\${Conffiles}' kidux-webapps | grep -q $POLICY \
           && python3 -c 'import json, sys; p = json.load(open(sys.argv[1])); \
                          sys.exit(not (p[\"URLBlocklist\"] == [\"*\"] and p[\"URLAllowlist\"] == [\"127.0.0.1:8123\", \"blob:*\"] \
                                        and p[\"DownloadRestrictions\"] == 1 and p[\"AllowFileSelectionDialogs\"] is True \
                                        and p[\"PromptForDownloadLocation\"] is True))' $POLICY"
check "a module's Chromium is walled in by a proxy that answers nothing, with only the server past it" \
    sh -c "runuser -u marta -- /usr/libexec/kidux-webapp --print hello-web \
           | grep -q -- \"--proxy-server=127.0.0.1:1 --proxy-bypass-list=127.0.0.1 .*'--app=\""
# The machine's own flags for Chromium, from the panel's Advanced settings
# (D51, D52): written by the daemon where kidux-webapp reads them, after
# Kidux's own; none is no file; a flag that would take the module out of
# Kidux's hold is refused.
FLAGS=/etc/kidux/chromium-flags
check "Chromium's flags for this machine reach kidux-webapp's command line, after Kidux's own" \
    sh -c "$ADMIN_AS set-config chromium_flags '[\"--disable-gpu-compositing\"]' \
           && [ \"\$(cat $FLAGS)\" = --disable-gpu-compositing ] \
           && [ \"\$(stat -c '%U %a' $FLAGS)\" = 'root 644' ] \
           && runuser -u marta -- /usr/libexec/kidux-webapp --print hello-web \
              | grep -q -- \"--app=http://127.0.0.1:8123/hello-web/?lang=[a-z]*' --disable-gpu-compositing\$\""
check "none is no file, and a flag that would open another page or take the wall down is refused" \
    sh -c "$ADMIN_AS set-config chromium_flags '[]' && test ! -e $FLAGS \
           && $ADMIN_AS set-config chromium_flags '[\"--app=http://example.org\"]' \
              | grep -qx org.kidux.Daemon1.Error.InvalidArgument && test ! -e $FLAGS \
           && $ADMIN_AS set-config chromium_flags '[\"--no-proxy-server\"]' \
              | grep -qx org.kidux.Daemon1.Error.InvalidArgument && test ! -e $FLAGS"
check "removing the module leaves nothing of it; the server stays for the next" \
    sh -c "$ADMIN_AS remove hello-web | grep -q '^removed ' \
           && test ! -e /usr/share/kidux/modules/hello-web && test ! -e /usr/share/kidux/webapps/hello-web \
           && systemctl is-active --quiet kidux-webapps"
