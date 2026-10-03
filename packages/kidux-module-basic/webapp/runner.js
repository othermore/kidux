// The screen of one run: wwwBASIC, with the bindings Kidux gives it, in a
// frame of its own, so that ending a run is taking the frame away (D84).
// It tells the page what happens through messages: ready, ended, an
// error, a sound to play, and the keys that stop or run again.

import basic from "./wwwbasic/wwwbasic.mjs";

const page = window.parent;
const say = (message) => page.postMessage(Object.assign({ basic: true }, message), location.origin);

const bindings = basic.GraphicsBindings(document.getElementById("screen"));
// Forty columns, the home computers' letters, large enough for a child.
bindings.statement_width_iI(40, 25);

// SOUND frequency, duration: the page plays it, since the page has the
// child's click that browsers ask for before a sound. The duration is in
// the PC's clock ticks, 18.2 a second.
bindings.statement_sound_ii = (frequency, ticks) => say({ sound: [frequency, ticks / 18.2] });

const halt = bindings.Halt;
bindings.Halt = () => { halt(); say({ ended: true }); };

// wwwBASIC writes what it cannot read to the console, and throws what goes
// wrong while it runs.
let reading = false;
console.error = (text) => say({ error: String(text), reading: reading, internal: /^[A-Z][a-z]+Error\b/.test(String(text)) });
console.info = () => {};
console.log = () => {};
window.addEventListener("error", (event) => {
  const thrown = event.error;
  say({ error: String(thrown === undefined ? event.message : thrown), reading: false,
        internal: typeof thrown !== "string" });
});

window.addEventListener("keydown", (event) => {
  if (event.key === "Escape") { say({ stop: true }); }
  if (event.key === "Enter" && event.ctrlKey) { say({ again: true }); }
});

window.addEventListener("message", (event) => {
  if (event.source !== page || typeof event.data.program !== "string") { return; }
  reading = true;
  try {
    // Reads the program, then runs it, its first part before returning.
    basic.Basic(window.KiduxBasic.forScreen(event.data.program), { bindings: bindings });
  } catch (thrown) {
    say({ error: String(thrown), reading: false, internal: typeof thrown !== "string" });
  } finally {
    reading = false;
  }
});

say({ ready: true });
