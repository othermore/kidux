"""The words Kidux uses, defined once.

Four programs put words in front of the same family, and the same idea has to
be the same word every time. A child who learns that the button is called
"Lock" on one screen must not find it called "Block" on another; an adult who
is told to "ask an adult" must not later be asked to "ask a parent".

So the shared words live here, marked for translation but not yet translated,
and every screen imports them instead of typing the word again. Translating
them once means they cannot drift apart in Spanish either.

A string belongs here when more than one program shows it, or when it is a
term the family learns. A sentence that only one screen ever says belongs in
that screen.
"""

from .i18n import N_

# --- who people are ----------------------------------------------------------

#: Never "parent". Mothers, fathers, grandparents and teachers all use the same
#: machine, and a six-year-old reads "Adult" without help.
ADULT = N_("Adult")

#: What the adult types. Never "PIN": it is free-form text, because forcing
#: digits stops adults using something they can actually remember.
ADULT_PASSWORD = N_("Adult password")

CHILD = N_("Child")
CHILD_PASSWORD = N_("Your password")

# --- the corner: what a laptop has, on every screen (corner.py) --------------

BATTERY = N_("Battery")
SCREEN_BRIGHTNESS = N_("Screen brightness")
KEYBOARD_LIGHT = N_("Keyboard light")
VOLUME = N_("Volume")
#: The sound's mute toggle, in its two states.
MUTE = N_("Mute")
MUTED = N_("Muted")

# --- the four screens --------------------------------------------------------

SIGN_IN = N_("Sign in")
LOCK = N_("Lock")
LOG_OUT = N_("Log out")
TURN_OFF = N_("Turn off")
CONTINUE = N_("Continue")
CANCEL = N_("Cancel")
BACK = N_("Back")
TRY_AGAIN = N_("Try again")
RESTART = N_("Restart")
TURN_OFF_QUESTION = N_("Turn off the computer?")

# --- time --------------------------------------------------------------------

#: Shown on the launcher all day, so it has to read naturally to a child who is
#: still learning to tell the time.
TIME_LEFT = N_("Time left")
TIME_IS_UP = N_("Time is up")
NO_TIME_LIMIT = N_("No time limit")
#: Said to an adult about a child; `minutes` is `minutes()` below.
TIME_CHILD_HAS_LEFT = N_("Time {name} has left: {minutes}")
GIVE_MORE_TIME = N_("Give more time")
UNLOCK_TO_SAVE = N_("Unlock to save work")
#: What a child taps when their time is spent, to fetch an adult. Written
#: as the action, not in the child's voice: a button is something to do.
ASK_ADULT_FOR_TIME = N_("Ask an adult for more time")
HOW_LONG = N_("How long?")


def minutes(translations, count: int) -> str:
    """ "15 minutes", in the language of `translations`.

    A function rather than a constant because the plural depends on the
    number, and not every language has only two forms.
    """
    return translations.ngettext("{count} minute", "{count} minutes", count).format(count=count)

# --- access modes ------------------------------------------------------------
#
# The name an adult sees in the panel, not the identifier the daemon stores.
# The stored values are "unlimited", "daily" and "manual" and never change with
# the language.

ACCESS_UNLIMITED = N_("Whenever they like")
ACCESS_DAILY = N_("A set time each day")
ACCESS_MANUAL = N_("Only when an adult says so")

# --- things that go wrong ----------------------------------------------------
#
# Written to be read by a child sitting alone in front of the screen. They say
# what happened and what to do, and they never blame the person reading them.

WRONG_PASSWORD = N_("That password is not right. Try again.")
ASK_AN_ADULT = N_("Ask an adult to unlock the computer for you.")
TIME_SPENT_TODAY = N_("You have used all your time for today. You can use it again tomorrow.")
#: On a day of the week an adult has not ticked for this child (D54).
NOT_TODAY = N_("The computer is not for you today. An adult can give you time.")
CANNOT_REACH_DAEMON = N_("The computer is still starting up. Wait a moment and try again.")
UPDATING = N_("The computer is being updated. Wait a moment and try again.")
