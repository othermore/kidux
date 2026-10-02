# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-3-plan.md, steps 3.4 and 3.5: the reference module is offered by the
# archive, installs through the daemon as the panel asks for it, puts
# everything where the launcher looks, and is removed without a trace; never
# while a child has a session, and never for anything but a module's id.

AS="/usr/local/bin/kidux-as"
ADMIN_AS="runuser -u debian -- $AS"
HELLO=/usr/share/kidux/modules/hello

# A child's session, made as 05-time-and-lock.py makes one, for as long as
# the command given takes; the daemon has to have seen it first.
with_a_child_signed_in() {
    systemctl start kidux-test-child@marta.service
    for _ in $(seq 40); do
        loginctl list-sessions --no-legend | grep -q ' marta ' && break
        sleep 0.5
    done
    sleep 2
    "$@"
    status=$?
    systemctl stop kidux-test-child@marta.service
    for _ in $(seq 40); do
        loginctl list-sessions --no-legend | grep -q ' marta ' || break
        sleep 0.5
    done
    sleep 2
    return "$status"
}

# What the archive offers, in English and then in Spanish (D47): a module
# not installed is named from its package's own fields, and says its ages
# (D55). The machine's language is put back as it was.
offered_in() {
    $ADMIN_AS set-config default_language "\"$1\"" >/dev/null \
        && $ADMIN_AS modules-available | grep -qxF "hello available - 4-8 - $2"
}
named_in_both() {
    was="$($ADMIN_AS get-config default_language)"
    offered_in en_US.UTF-8 "[Test] Hello" && offered_in es_ES.UTF-8 "[Prueba] Hola"
    status=$?
    $ADMIN_AS set-config default_language "$was" >/dev/null
    return "$status"
}

check "the archive offers kidux-module-hello, not installed, for ages 4 to 8, named in the machine's language" \
    named_in_both
check "and kidux-module-hello-web, with hello to do first" \
    sh -c "$ADMIN_AS modules-available | grep -q '^hello-web available - 4-8 hello '"
check "a name that is not a module's id is refused" \
    sh -c "$ADMIN_AS install ../hello | grep -qx org.kidux.Daemon1.Error.InvalidArgument \
           && $ADMIN_AS install kidux-module-hello | grep -qx org.kidux.Daemon1.Error.InvalidArgument"
check "nothing is installed while a child has a session" \
    with_a_child_signed_in sh -c "$ADMIN_AS install hello | grep -qx org.kidux.Daemon1.Error.SessionActive"
check "kidux-module-hello installs through the daemon, as the panel asks" \
    sh -c "$ADMIN_AS install hello | grep -q '^installed '"
check "the archive says it is installed" \
    sh -c "$ADMIN_AS modules-available | grep -q '^hello installed '"
check "it is listed for a child, switched off" \
    sh -c "$ADMIN_AS modules marta | grep -qx 'hello off'"
check "its manifest, icon, program and both pages are in place" \
    sh -c "test -f $HELLO/module.toml && test -f $HELLO/icon.svg \
           && test -x /usr/libexec/kidux-module-hello \
           && test -f $HELLO/content/en/hello.md && test -f $HELLO/content/es/hello.md"
check "and its Spanish words" \
    test -f /usr/share/locale/es/LC_MESSAGES/kidux-module-hello.mo
check "the install is in the audit log" \
    sh -c "grep '\"action\": \"module installed\"' /home/.kidux/state/audit.log | grep -q '\"module\": \"hello\"'"
check "nothing is removed while a child has a session" \
    with_a_child_signed_in sh -c "$ADMIN_AS remove hello | grep -qx org.kidux.Daemon1.Error.SessionActive"
check "removing it through the daemon leaves nothing of it behind" \
    sh -c "$ADMIN_AS remove hello | grep -q '^removed ' \
           && test ! -e $HELLO && test ! -e /usr/libexec/kidux-module-hello \
           && test -z \"\$(find /usr/share/locale -name 'kidux-module-hello.*')\""
check "and it is no longer listed" \
    sh -c "! $ADMIN_AS modules marta | grep -q '^hello '"
check "and the archive offers it again" \
    sh -c "$ADMIN_AS modules-available | grep -q '^hello available - '"
