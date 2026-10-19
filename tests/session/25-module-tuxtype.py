"""Tux Typing, the typing course (phase-4-plan.md, step 4.3).

Installed through the daemon, as the panel installs it, and switched on for
Leo from the command line. Leo opens it by keyboard: it comes up in a
window of its own, through XWayland, its pictures scaled to fill the room
above the bar, Kidux's build of Tux Typing (kidux-tuxtype, D113) with
Kidux's theme of Leo's language (`--theme kidux-es`, or `kidux-en`), and
its home the module's own directory, not Leo's. Its Lessons list Kidux's
lessons in Leo's language, and the first one opens and starts its practice
when P is pressed. Leo types a whole lesson, as a child does, and the
practice takes every key and lights every finger: in Spanish, the ñ of the
second lesson all the way through, and the accented vowels of the
thirteenth, typed with the dead key, without an error. Alt+F4 closes it,
the launcher comes back, and the daemon removes it.
"""

import time
import tomllib

from sessionlib import (
    CHILD,
    CHILD_PASSWORD,
    CREAM,
    REPO,
    SPEAKS,
    Machine,
    active_terminal,
    child_session,
    colour_share,
    greeter_log,
    journal_count,
    launcher_log,
    launcher_shown,
    on_screen,
    pointer,
    report,
    root,
    wait,
    windows,
)
from sessionlib import _png  # the PNG reader colour_share uses

HOME = f"/home/{CHILD}"
DATA = f"{HOME}/.local/share/kidux/tuxtype"
#: Tux Typing's main menu's Lessons, and the first lesson of its list, where
#: they are on the screen; and a place over nothing, for the pointer to rest.
LESSONS = "0.477,0.48"
FIRST_LESSON = "0.5,0.084"
ASIDE = "0.97,0.5"
#: A lesson's place on the list, eight to a page, and the arrow to the next.
LESSON_ROWS = (0.084, 0.18, 0.276, 0.374, 0.471, 0.567, 0.664, 0.761)
NEXT_PAGE = "0.597,0.87"
#: Where the practice writes how many errors it counted, its first figure.
ERRORS = (0.115, 0.675, 0.15, 0.725)
#: What Tux Typing writes when a key of a practice has no finger.
NO_FINGER = "has no valid finger"
#: The lessons as the module builds them, for what each practice asks.
COURSE = tomllib.loads((REPO / "packages" / "kidux-module-tuxtype" / "lessons"
                        / f"{SPEAKS['lang']}.toml").read_text(encoding="utf-8"))["lesson"]
#: The first lesson's file, as the list shows it and Tux Typing logs it.
FIRST = {"es": "Lección 01 - a s d f.xml", "en": "Lesson 01 - a s d f.xml"}
#: The lesson's pages, green; the practice has none of it. Its first page
#: is a darker green, and the list of lessons is blue.
LESSON_GREEN = (0x3F, 0x7F, 0x3F)
FIRST_PAGE = (0x3F, 0x4F, 0x1F)

#: The room above the launcher's bar, and the bar.
ABOVE_THE_BAR = (0.0, 0.0, 1.0, 0.92)
BAR = (0xF2, 0xE2, 0xCC)
BAR_BOX = (0.0, 0.94, 1.0, 1.0)


def daemon(command: str) -> bool:
    """`kidux-as install|remove tuxtype`: the daemon's job, start to end."""
    return root(f"runuser -u debian -- /usr/local/bin/kidux-as {command} tuxtype",
                timeout=1200).stdout.startswith(command + ("ed " if command == "install" else "d "))


def tuxtype_pid() -> str:
    return root(f"pgrep -u {CHILD} -x kidux-tuxtype | head -1").stdout.strip()


def region(picture, box) -> bytes:
    """A picture's pixels inside `box`, as fractions of it, to compare
    exactly: the figure 0 is the same pixels each time it is drawn."""
    width, height, rows = _png().read_png(picture)
    left, top, right, bottom = box
    return b"".join(bytes(rows[y][int(left * width) * 3:int(right * width) * 3])
                    for y in range(int(top * height), int(bottom * height)))


def tuxtype_window() -> dict:
    return next((w for w in windows() if w.get("module") == "tuxtype"), {})


def run(machine: Machine) -> None:
    report("kidux-module-tuxtype installs from the archive through the daemon, as the panel "
           "asks", daemon("install"), root("tail -5 /var/log/apt/term.log").stdout)
    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} tuxtype on")

    before = journal_count("kidux-launcher", "tiles: tuxtype")
    password = machine.mark()
    machine.key("ret")                           # Leo, the first picture
    machine.shown("password", password)
    machine.submit(CHILD_PASSWORD)
    report("Leo signs in to its tile", wait(lambda: child_session() is not None, 30)
           and wait(lambda: journal_count("kidux-launcher", "tiles: tuxtype") > before, 30)
           and launcher_shown(machine), greeter_log() + launcher_log())

    # From Lock, which has the focus, back to the tile, and Enter.
    machine.key("shift-tab")
    machine.key("ret")
    opened = wait(lambda: tuxtype_window() != {}, 60, 2)
    wait(lambda: on_screen() == "tuxtype", 10)
    # Past Tux4Kids' splash, to its menu.
    time.sleep(8)
    machine.still(5)
    picture = machine.screenshot("module-tuxtype")
    window = tuxtype_window()
    report("Leo opens it by keyboard, a window filling the room above the bar",
           opened and on_screen() == "tuxtype" and window.get("maximized")
           and not window.get("fullscreen")
           and colour_share(picture, CREAM, ABOVE_THE_BAR) < 0.2
           and colour_share(picture, BAR, BAR_BOX) > 0.4,
           f"{window}; {picture}\n" + launcher_log())

    pid = tuxtype_pid()
    arguments = root(f"tr '\\0' ' ' < /proc/{pid}/cmdline").stdout
    environment = root(f"tr '\\0' '\\n' < /proc/{pid}/environ").stdout
    theme = "--theme kidux-es" if SPEAKS["lang"] == "es" else "--theme kidux-en"
    report("in a window, with Kidux's theme of Leo's language, at home in its own directory",
           "--window" in arguments and "SDL_VIDEODRIVER=" not in environment
           and theme in arguments
           and f"HOME={DATA}" in environment
           and root(f"test -d {DATA}/.tuxtype").returncode == 0,
           arguments + "\n" + root(f"ls -la {DATA}").stdout)

    # Its Lessons, by the pointer: a fresh Tux Typing's menu does not always
    # start on the same entry, so keys cannot be counted.
    before = journal_count("kidux-module-tuxtype", FIRST[SPEAKS["lang"]])
    pointer(LESSONS, "click", ASIDE)
    listed = wait(lambda: journal_count("kidux-module-tuxtype", FIRST[SPEAKS["lang"]]) > before, 15)
    machine.still(3)
    machine.screenshot("module-tuxtype-lessons")
    report("its Lessons list Kidux's lessons in Leo's language", listed,
           root("journalctl -b --no-pager -t kidux-module-tuxtype | tail -5").stdout)
    pointer(FIRST_LESSON, "click", ASIDE)
    time.sleep(3)
    machine.key("ret")                           # past the first page
    time.sleep(3)
    page = machine.screenshot("module-tuxtype-lesson-fingers")
    machine.key("p")                             # P practises
    time.sleep(4)
    practice = machine.screenshot("module-tuxtype-lesson")
    report("the first lesson opens, says where the fingers go, and P starts its practice",
           colour_share(page, LESSON_GREEN, ABOVE_THE_BAR) > 0.3
           and colour_share(practice, LESSON_GREEN, ABOVE_THE_BAR) < 0.05,
           f"{page}; {practice}")
    # Leo types the whole lesson. Its practice waits for a key once the
    # line is typed, and the lesson goes on to its words' page, green.
    no_finger = journal_count("kidux-module-tuxtype", NO_FINGER)

    def practise(line: str) -> bool:
        """Type a practice's line, as a child does: the lesson goes on, past
        Tux's cheer, to a green page, the words' or well done."""
        machine.type(line)
        time.sleep(2)
        machine.key("ret")                       # past Tux's cheer
        return (machine.showing(LESSON_GREEN, ABOVE_THE_BAR, 0.3, 10)
                or machine.showing(FIRST_PAGE, ABOVE_THE_BAR, 0.3, 5))

    def whole(number: int) -> bool:
        """The rest of a lesson, from its first practice to its end, where
        Tux Typing goes back to its main menu."""
        lesson = COURSE[number - 1]
        went_on = practise(lesson["drill"])
        machine.key("p")
        time.sleep(3)
        went_on = practise(lesson["words"]) and went_on
        machine.key("ret")                       # past well done, to the main menu
        time.sleep(4)
        return went_on

    report("Leo types the first lesson whole, each practice going on to the next page",
           whole(1), root("journalctl -b --no-pager -t kidux-module-tuxtype | tail -5").stdout)

    def open_lesson(number: int) -> None:
        """From the main menu, a lesson's first practice."""
        pointer(LESSONS, "click", ASIDE)
        time.sleep(4)
        if number > len(LESSON_ROWS):
            pointer(NEXT_PAGE, "click", ASIDE)
            time.sleep(3)
        pointer(f"0.5,{LESSON_ROWS[(number - 1) % len(LESSON_ROWS)]}", "click", ASIDE)
        machine.showing(FIRST_PAGE, ABOVE_THE_BAR, 0.3, 10)
        machine.key("ret")                       # past the first page
        machine.showing(LESSON_GREEN, ABOVE_THE_BAR, 0.3, 10)
        machine.key("p")
        time.sleep(4)

    if SPEAKS["lang"] == "es":
        open_lesson(2)
        report("Leo types the second lesson whole, the ñ with its finger every time",
               whole(2) and journal_count("kidux-module-tuxtype", NO_FINGER) == no_finger,
               root(f"journalctl -b --no-pager -t kidux-module-tuxtype | grep -c '{NO_FINGER}'").stdout)

        # The thirteenth's practice, of the accented vowels: the errors are
        # 0 after its first key, a plain a, and still 0 once its line, with
        # the dead key before each accented vowel, is typed.
        open_lesson(13)
        machine.screenshot("module-tuxtype-lesson-accents")
        drill = COURSE[12]["drill"]
        machine.type(drill[0])
        time.sleep(2)
        begun = machine.screenshot("module-tuxtype-accents-begun")
        machine.type(drill[1:])
        time.sleep(2)
        typed = machine.screenshot("module-tuxtype-accents-typed")
        report("Leo types the accents' practice with the dead key, and no error is counted",
               len(set(region(begun, ERRORS))) > 1 and region(typed, ERRORS) == region(begun, ERRORS)
               and journal_count("kidux-module-tuxtype", NO_FINGER) == no_finger,
               f"{begun}; {typed}")
        machine.key("ret")                       # past Tux's cheer, to the words' page
        time.sleep(3)

    # Alt+F4 asks it to close; a Tux Typing that asks something first is
    # ended by Alt+F4 again, as the bar's question says (D45).
    ended = journal_count("kidux-launcher", "module tuxtype ended")
    machine.key("alt-f4")
    if not wait(lambda: journal_count("kidux-launcher", "module tuxtype ended") > ended, 20):
        machine.key("alt-f4")
    report("Alt+F4 closes it, and the launcher comes back",
           wait(lambda: journal_count("kidux-launcher", "module tuxtype ended") > ended, 20)
           and wait(lambda: on_screen() == "home", 10),
           launcher_log())

    # Log out from the lock screen, past Continue and Adult.
    locked = machine.mark()
    machine.monitor("system_powerdown")
    wait(lambda: active_terminal() == "tty8", 20)
    machine.shown("locked", locked)
    machine.key("tab")
    machine.key("tab")
    asked = machine.mark()
    machine.key("ret")
    machine.shown("child_password", asked)
    choose = machine.submit(CHILD_PASSWORD)
    report("Leo logs out from the lock screen", wait(lambda: child_session() is None, 30),
           greeter_log())
    machine.shown("choose", choose, 30)

    root(f"runuser -u debian -- /usr/local/bin/kidux-as enable {CHILD} tuxtype off")
    report("and the daemon removes it", daemon("remove"), root("tail -5 /var/log/apt/term.log").stdout)
