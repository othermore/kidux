# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# phase-3-plan.md, step 3.1: which modules are installed and which are
# enabled for whom, through the daemon, with the tests' stand-in module
# copied into place from the seed and removed at the end.

AS="/usr/local/bin/kidux-as"
CANARY=/usr/share/kidux/modules/canary
SEED=http://10.0.2.2:8000/modules/canary

check "the tests' stand-in module is put in place" \
    sh -c "mkdir -p $CANARY && curl -fsS -o $CANARY/module.toml $SEED/module.toml \
           && curl -fsS -o $CANARY/icon.svg $SEED/icon.svg"
check "it is listed for a child, switched off" \
    sh -c "test \"\$(runuser -u debian -- $AS modules marta)\" = 'canary off'"
check "an adult switches it on for the child" \
    sh -c "runuser -u debian -- $AS enable marta canary on \
           && test \"\$(runuser -u debian -- $AS modules marta)\" = 'canary on'"
check "and the audit trail says so" \
    grep -q '"action": "module enabled", "caller": "debian", "child": "marta", "module": "canary"' \
        /home/.kidux/state/audit.log
check "a module that is not installed cannot be switched on" \
    sh -c "test \"\$(runuser -u debian -- $AS enable marta nothing on)\" \
           = org.kidux.Daemon1.Error.InvalidArgument"
check "a child lists their own modules" \
    sh -c "test \"\$(runuser -u marta -- $AS modules marta)\" = 'canary on'"
check "and not a sibling's" \
    sh -c "runuser -u debian -- $AS add zoe Zoe && runuser -u marta -- $AS child-sibling zoe"
check "a module whose files are gone is no longer listed, and keeps its switch" \
    sh -c "rm -rf $CANARY && test -z \"\$(runuser -u debian -- $AS modules marta)\" \
           && grep -q canary /home/.kidux/children/marta/modules.toml"
