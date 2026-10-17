"""What only the launcher says. Shared words are in `kidux.vocabulary`."""

from kidux.i18n import N_

NOTHING_YET = N_("There is nothing here yet. An adult can add things to do.")
SAVED_YOUR_WORK = N_("Have you saved your work?")
DID_NOT_OPEN = N_("That did not open. An adult can look at it.")
#: The bar's first button, and the key that does the same: the launcher.
HOME = N_("Home")
#: The bar's button that closes the module on screen, and what a screen
#: reader says of it.
CLOSE = N_("Close")
CLOSE_MODULE = N_("Close {name}")
#: What the bar asks when a module asked to close is still open.
NOT_CLOSED = N_("{name} has not closed. It may have something to save.")
CLOSE_ANYWAY = N_("Close it anyway")

#: The bar's bell, which keeps the last notices (bubbles.py, D98).
NOTICES = N_("Notices")
NO_NOTICES = N_("Nothing to show yet.")
CLEAR_NOTICES = N_("Clear")

#: A module's guide beside it (guide.py, D103): the bar's button and the
#: folded pane, the pane's own buttons, and its boxes.
GUIDE = N_("Guide")
FOLD = N_("Fold")
PIN = N_("Pin")
PIN_HINT = N_("The guide stays while other windows are in use")
LESSONS = N_("Lessons")
BACK = N_("Back")
NEXT = N_("Next")
TRY_THIS = N_("Try this")
MISSION = N_("Mission")
#: How to open a lesson's mission from the module: {name} the module's,
#: {folder} the folder its missions are in, {file} the mission's file.
OPEN_MISSION_FROM = N_("Open it from {name}: File, Open, Documents, {folder}, {file}.")
#: The folder in the child's Documents a module's missions are copied to.
MISSIONS_OF = N_("Missions of {name}")
