"""The first start, by keyboard, in Spanish: plan step 9.6b's acceptance."""

from sessionlib import (
    ADULT_PASSWORD,
    Machine,
    NIGHT,
    SPEAKS,
    WIZARD_CHILD,
    WIZARD_CHILD_NAME,
    WIZARD_CHILD_PASSWORD,
    active_terminal,
    colour_share,
    greeter_log,
    report,
    root,
    screens_shown,
    shlex_quote,
    ssh,
    wait,
)



#: Run in every language (tests/lib/session-vm.py): it sets the machine up,
#: or checks what a language can change.
EVERY_LANGUAGE = True

def run(machine: Machine) -> None:
    def showing(name: str) -> bool:
        return wait(lambda: screens_shown(name) > 0, 20)

    report("a machine never set up starts the wizard", showing("wiz_language"), greeter_log())
    welcome = machine.screenshot("wizard-language")
    report("the welcome shows Kidux's logo",
           colour_share(welcome, NIGHT, (0.3, 0.05, 0.7, 0.5)) > 0.01, str(welcome))
    for _ in range(SPEAKS["tabs"]):          # English is first; Español is next
        machine.key("tab")
    machine.key("ret")
    showing("wiz_keyboard")
    machine.screenshot("wizard-keyboard")
    machine.key("ret")                       # the first layout offered: Spain's, the US's
    report("choosing the keyboard restarts the screen in it, at the adult password",
           showing("wiz_password"), greeter_log())
    config = root("cat /home/.kidux/config.toml").stdout
    report("the machine's language and keyboard are saved",
           f'default_language = "{SPEAKS["locale"]}"' in config
           and f'default_keyboard = "{SPEAKS["keyboard"]}"' in config,
           config)
    machine.screenshot("wizard-adult-password")
    machine.type(ADULT_PASSWORD + "\n")
    machine.type(ADULT_PASSWORD + "\n")
    report("then the first child's form, the same as the panel's", showing("wiz_child"),
           greeter_log())
    machine.screenshot("wizard-child")
    # Enter moves from the name to the password, then to the password again,
    # and adds the child: the picture and the access keep what the form shows.
    machine.type(WIZARD_CHILD_NAME + "\n")
    machine.type(WIZARD_CHILD_PASSWORD + "\n")
    machine.type(WIZARD_CHILD_PASSWORD + "\n")
    done = showing("wiz_done")
    machine.screenshot("wizard-done")
    report("the wizard ends with everything ready", done, greeter_log())
    machine.key("ret")
    showing("choose")
    machine.screenshot("wizard-first-child")

    config = root("cat /home/.kidux/config.toml").stdout
    report("the machine is set up", "setup_complete = true" in config, config)
    profile = root(f"cat /home/.kidux/children/{WIZARD_CHILD}/profile.toml").stdout
    report("the first child exists, in the machine's language",
           f'language = "{SPEAKS["locale"]}"' in profile, profile)
    access = root(f"cat /home/.kidux/children/{WIZARD_CHILD}/access.toml").stdout
    report("with the form's hour a day", 'mode = "daily"' in access
           and "daily_minutes = 60" in access, access)

    # The child the wizard made signs in, from the only picture there is.
    machine.key("ret")
    showing("password")
    machine.still()
    machine.type(WIZARD_CHILD_PASSWORD + "\n")
    signed_in = wait(lambda: WIZARD_CHILD in ssh("loginctl list-sessions --no-legend").stdout, 30)
    report("and signs in with the password the wizard gave them", signed_in, greeter_log())
    ssh(f"/usr/local/bin/kidux-as end {WIZARD_CHILD} {shlex_quote(WIZARD_CHILD_PASSWORD)}")
    wait(lambda: active_terminal() == "tty7"
         and "greeter" in ssh("loginctl list-sessions --no-legend").stdout, 30)
    return None
