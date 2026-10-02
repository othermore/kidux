# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# docs/dev/packaging.md, "Testing before a real machine".
#
# The audit trail holds everything above, and never a password.

check "the audit trail recorded all of it and no password" \
    sh -c 'grep -q "\"child created\"" /home/.kidux/state/audit.log \
           && grep -q "\"child deleted\"" /home/.kidux/state/audit.log \
           && grep -q "\"first boot\"" /home/.kidux/state/audit.log \
           && ! grep -q "\"password\":" /home/.kidux/state/audit.log \
           && ! grep -q "marta password" /home/.kidux/state/audit.log'

# The state is the administrators' to read and closed to every child: the
# files root writes are given to kidux-admin (layout.md, "The family's state").
check "an administrator reads the audit trail and the settings without root" \
    sh -c 'runuser -u debian -- cat /home/.kidux/state/audit.log >/dev/null \
           && runuser -u debian -- cat /home/.kidux/adults.toml >/dev/null \
           && runuser -u debian -- cat /home/.kidux/children/marta/access.toml >/dev/null'

check "a child reads none of it" \
    sh -c '! runuser -u marta -- cat /home/.kidux/adults.toml 2>/dev/null \
           && ! runuser -u marta -- ls /home/.kidux/children 2>/dev/null'
