# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# docs/dev/packaging.md, "Testing before a real machine".
#
# The daemon, first boot, the adult password, children, and who may do what.

# The cloud image's default user, debian, is in sudo: the administrator
# an installer would have made. First boot has to have made them an
# adult of the family's state, without being told their name (D18).

check "the daemon is running" systemctl is-active --quiet kidux-daemon
check "first boot ran" test -f /home/.kidux/config.toml
check "the state directory is closed to everyone but adults" \
    sh -c 'test "$(stat -c %U:%G:%a /home/.kidux)" = root:kidux-admin:750'
check "the recovery password was made for GRUB" \
    grep -q '^grub_password_hash = "grub.pbkdf2' /home/.kidux/adults.toml
check "the administrator became an adult of the family" \
    sh -c 'id -nG debian | tr " " "\\n" | grep -qx kidux-admin'
check "the administrator sets the adult password and creates two children" \
    runuser -u debian -- /usr/local/bin/kidux-as setup
check "the children are real accounts in the right groups" \
    sh -c 'id -nG marta | grep -qw kidux-children && id -nG leo | grep -qw kidux-children'
check "a child has no shell" \
    sh -c 'test "$(getent passwd marta | cut -d: -f7)" = /usr/sbin/nologin'
check "a child can sign in with the password that was set" \
    sh -c 'printf "marta password\\n" | pamtester login marta authenticate'
check "a wrong password does not sign a child in" \
    sh -c '! printf "a guess\\n" | pamtester login marta authenticate'
check "the sign-in screen's list shows both children" \
    sh -c 'test "$(runuser -u debian -- /usr/local/bin/kidux-as list)" = "leo marta"'
check "a token is useless on another connection" \
    runuser -u debian -- /usr/local/bin/kidux-as reuse-token
check "the administrator's own account can never be deleted" \
    runuser -u debian -- /usr/local/bin/kidux-as delete-admin debian
check "a child may not see the list of children" \
    runuser -u marta -- /usr/local/bin/kidux-as child-list
check "a child may ask about themselves" \
    runuser -u marta -- /usr/local/bin/kidux-as child-self marta
check "a child may not ask about a sibling" \
    runuser -u marta -- /usr/local/bin/kidux-as child-sibling leo
check "a child may not unlock the adult panel, even with the password" \
    runuser -u marta -- /usr/local/bin/kidux-as child-unlock
check "deleting a child removes the account" \
    sh -c 'runuser -u debian -- /usr/local/bin/kidux-as delete leo && ! getent passwd leo'
