# Sourced by the acceptance VM's runner, which provides check() and $ARCHIVE.
# docs/dev/packaging.md, "Testing before a real machine".
#
# kidux-base installs, with every language Kidux ships in.

# Installing the metapackage is what runs the locale postinst.
check "kidux-base installs" \
    sh -c 'DEBIAN_FRONTEND=noninteractive apt-get install -y kidux-base pamtester'

# A child's language is chosen long after the installer picked one, so
# every language Kidux ships in has to exist on the machine already.
for generated in en_US.utf8 es_ES.utf8; do
    check "locale $generated is generated" \
        sh -c "locale -a | grep -qx $generated"
done

check "unattended-upgrades accepts the Kidux origin" \
    sh -c 'grep -q "origin=Kidux" /etc/apt/apt.conf.d/60kidux-unattended-upgrades'

# A child's session runs labwc (session.md, section 3), and nothing a person
# types comes with it: kidux-session conflicts with the terminal labwc
# suggests and with a launcher's menu, so installing with recommends leaves
# both out.
check "no terminal or menu came with labwc" \
    sh -c '! dpkg-query -W -f "\${Status}\n" foot wmenu 2>/dev/null | grep -q "^install ok installed"'
check "and no terminal emulator of any kind is on the machine" \
    sh -c 'test ! -e /etc/alternatives/x-terminal-emulator && test ! -e /usr/bin/x-terminal-emulator'
check "the child's labwc configurations are root's and read-only to them" \
    sh -c 'test "$(stat -c "%U %a" /usr/share/kidux/labwc/kiosk/rc.xml /usr/share/kidux/labwc/desk/rc.xml | sort -u)" = "root 644"'
# A laptop's keys for its screen, keyboard light and sound run kidux-keys
# in both configurations (D61), and the lid can be read by the launcher.
check "both configurations bind the laptop's keys to kidux-keys" \
    sh -c 'for c in kiosk desk; do for k in XF86MonBrightnessUp XF86MonBrightnessDown XF86KbdBrightnessUp XF86KbdBrightnessDown XF86AudioRaiseVolume XF86AudioLowerVolume XF86AudioMute; do grep -q "key=\"$k\".*kidux-keys" /usr/share/kidux/labwc/$c/rc.xml || exit 1; done; done'
check "kidux-keys is there, and does nothing on a machine without the things" \
    sh -c 'test -x /usr/libexec/kidux-keys && /usr/libexec/kidux-keys brightness up && /usr/libexec/kidux-keys keyboard down && /usr/libexec/kidux-keys volume mute'
check "an input switch may be read by anyone" \
    sh -c 'test -f /usr/lib/udev/rules.d/70-kidux-switches.rules && grep -q ID_INPUT_SWITCH /usr/lib/udev/rules.d/70-kidux-switches.rules'
# The rule applied to the switches there are, right after the install and
# without a restart: every one is 0644 (the test machine has none, and the
# check says so).
# A keyboard's light is video's, as the backlight is, so that a child and
# the trusted screens can set it (step 3.24): the rule, its effect after a
# trigger on every such light there is (the test machine has none, and the
# check says so), and _greetd in video.
check "a keyboard's light belongs to group video, and so does the sign-in screen's user" \
    sh -c 'test -f /usr/lib/udev/rules.d/91-kidux-keyboard-light.rules \
           && udevadm trigger --subsystem-match=leds --action=change && udevadm settle \
           && found=0 && for light in /sys/class/leds/*kbd_backlight*/brightness; do \
                  [ -e "$light" ] || continue; found=$((found + 1)); \
                  [ "$(stat -c %G "$light")" = video ] || { echo "$light is $(stat -c %G "$light")"; exit 1; }; \
              done && echo "$found keyboard lights, every one video'"'"'s" \
           && id -nG _greetd | grep -qw video'
check "every input switch there is is readable by anyone now, without a restart" \
    sh -c 'found=0; for dev in /dev/input/event*; do \
               udevadm info --query=property --name="$dev" | grep -qx ID_INPUT_SWITCH=1 || continue; \
               found=$((found + 1)); \
               [ "$(stat -c %a "$dev")" = 644 ] || { echo "$dev is $(stat -c %a "$dev")"; exit 1; }; \
           done; echo "$found input switches, every one 0644"'
