// The machine: the editor, its buttons and the screen (D84). A program is
// written in the editor and run in a frame of its own, runner.html, where
// wwwBASIC draws; Stop takes the frame away, which ends everything the run
// was doing, and leaves a picture of its screen. The program being written
// is kept in the browser's storage, which is the module's own.

(function () {
  "use strict";

  const words = window.BASIC.words;
  const check = window.KiduxBasic;
  const STORED = "kidux-basic-program";

  const editor = document.getElementById("editor");
  const gutter = document.getElementById("gutter");
  const screen = document.getElementById("screen");
  const still = document.getElementById("still");
  const status = document.getElementById("status");
  const ask = document.getElementById("ask");
  const opener = document.getElementById("opener");

  let frame = null;
  let running = false;
  let fromGuide = null;
  // Tab writes spaces in the editor; Escape, then Tab, leaves it, so that
  // the keyboard alone reaches the buttons and the guide.
  let leaving = false;

  function say(text, kind) {
    status.textContent = text;
    status.className = kind || "";
  }

  function fill(text, values) {
    return text.replace(/\{(\w+)\}/g, (all, name) => (name in values ? values[name] : all));
  }

  // The editor, its numbered margin, and the browser's storage.

  function remember() {
    try { localStorage.setItem(STORED, editor.value); } catch (error) { /* without it, nothing is kept */ }
  }

  function numberLines() {
    const count = editor.value.split("\n").length;
    let text = "";
    for (let i = 1; i <= count; i++) { text += i + "\n"; }
    gutter.textContent = text;
    gutter.scrollTop = editor.scrollTop;
  }

  function setProgram(text) {
    editor.value = text;
    numberLines();
    remember();
  }

  editor.addEventListener("input", () => { fromGuide = null; numberLines(); remember(); });
  editor.addEventListener("scroll", () => { gutter.scrollTop = editor.scrollTop; });
  editor.addEventListener("keydown", (event) => {
    const leave = leaving;
    leaving = event.key === "Escape" && !running;
    if (event.key === "Enter" && event.ctrlKey) { event.preventDefault(); run(); }
    if (event.key === "Escape" && running) { event.preventDefault(); stop(true); }
    if (event.key === "Tab" && !leave && !event.shiftKey && !event.ctrlKey && !event.altKey) {
      event.preventDefault();
      editor.setRangeText("  ", editor.selectionStart, editor.selectionEnd, "end");
      editor.dispatchEvent(new Event("input"));
    }
  });

  function showLine(line) {
    const lines = editor.value.split("\n");
    let start = 0;
    for (let i = 0; i < line - 1; i++) { start += lines[i].length + 1; }
    editor.focus();
    editor.setSelectionRange(start, start + lines[line - 1].length);
    const height = editor.scrollHeight / Math.max(lines.length, 1);
    editor.scrollTop = Math.max(0, (line - 3) * height);
  }

  // A question with two answers, in the page's own words.
  function confirm(question) {
    return new Promise((resolve) => {
      document.getElementById("question").textContent = question;
      const yes = document.getElementById("yes");
      const no = document.getElementById("no");
      function answer(value) {
        yes.onclick = no.onclick = null;
        ask.close();
        resolve(value);
      }
      yes.onclick = () => answer(true);
      no.onclick = () => answer(false);
      ask.onclose = () => answer(false);
      ask.showModal();
      no.focus();
    });
  }

  // Sound: the page plays what SOUND asks for, one tone after another.

  let audio = null;
  let freeAt = 0;
  let tones = [];

  function wake() {
    try {
      audio = audio || new AudioContext();
      audio.resume();
    } catch (error) { audio = null; }
  }

  function tone(frequency, seconds) {
    if (!audio || !(frequency >= 20 && frequency <= 20000) || !(seconds > 0)) { return; }
    const start = Math.max(audio.currentTime, freeAt);
    const end = start + Math.min(seconds, 10);
    const oscillator = audio.createOscillator();
    oscillator.type = "square";
    oscillator.frequency.value = frequency;
    const gain = audio.createGain();
    gain.gain.value = 0.08;
    oscillator.connect(gain).connect(audio.destination);
    oscillator.start(start);
    oscillator.stop(end);
    freeAt = end;
    tones.push(oscillator);
    oscillator.onended = () => { tones = tones.filter((t) => t !== oscillator); };
  }

  function silence() {
    for (const oscillator of tones) { try { oscillator.stop(); } catch (error) { /* already stopped */ } }
    tones = [];
    freeAt = 0;
  }

  // Running and stopping.

  function keepPicture() {
    try {
      const canvas = frame.contentDocument.getElementById("screen");
      still.width = canvas.width;
      still.height = canvas.height;
      still.getContext("2d").drawImage(canvas, 0, 0);
      still.hidden = false;
    } catch (error) { still.hidden = true; }
  }

  function stop(byHand) {
    if (!frame) { return; }
    keepPicture();
    frame.remove();
    frame = null;
    silence();
    if (byHand && running) { say(words.stopped); }
    running = false;
    document.getElementById("stop").disabled = true;
  }

  function run() {
    wake();
    stop(false);
    const program = editor.value;
    const missing = check.missingJumps(program);
    if (missing.length) {
      const first = missing[0];
      say(fill(words.jump, { number: first.number === null ? first.line : first.number,
                             target: first.target }), "wrong");
      showLine(first.line);
      return;
    }
    frame = document.createElement("iframe");
    frame.src = "runner.html";
    frame.title = words.screen;
    screen.appendChild(frame);
    running = true;
    still.hidden = true;
    say(words.running);
    document.getElementById("stop").disabled = false;
  }

  function explainError(data) {
    const found = check.explain(data.error, editor.value, data);
    if (found.kind === "syntax" && found.line !== null) {
      say(fill(found.number === null ? words.syntaxLine : words.syntax,
               { number: found.number, line: found.line }) + "  (" + found.text + ")", "wrong");
      showLine(found.line);
    } else if (found.kind === "syntax") {
      say(words.syntaxEnd + "  (" + found.text + ")", "wrong");
    } else if (found.kind === "data") {
      say(words.noData, "wrong");
    } else if (found.kind === "inside") {
      say(words.inside, "wrong");
    } else {
      say(fill(words.other, { message: found.text }), "wrong");
    }
  }

  window.addEventListener("message", (event) => {
    if (!frame || event.source !== frame.contentWindow || !event.data || !event.data.basic) { return; }
    const data = event.data;
    if (data.ready) {
      frame.contentWindow.postMessage({ program: editor.value }, location.origin);
      frame.focus();
    } else if (data.ended) {
      running = false;
      if (status.className !== "wrong") { say(words.ended); }
      document.getElementById("stop").disabled = true;
    } else if (data.error) {
      running = false;
      explainError(data);
      document.getElementById("stop").disabled = true;
    } else if (data.sound) {
      tone(data.sound[0], data.sound[1]);
    } else if (data.stop) {
      stop(true);
      editor.focus();
    } else if (data.again) {
      run();
    }
  });

  // The buttons.

  document.getElementById("run").addEventListener("click", run);
  document.getElementById("stop").addEventListener("click", () => { stop(true); editor.focus(); });

  document.getElementById("new").addEventListener("click", async () => {
    if (editor.value.trim() && !(await confirm(words.sure))) { editor.focus(); return; }
    stop(false);
    still.hidden = true;
    setProgram("");
    say("");
    editor.focus();
  });

  document.getElementById("save").addEventListener("click", () => {
    const link = document.createElement("a");
    link.href = URL.createObjectURL(new Blob([editor.value.replace(/\n*$/, "\n")], { type: "text/plain" }));
    link.download = words.file + ".bas";
    link.click();
    setTimeout(() => URL.revokeObjectURL(link.href), 10000);
  });

  document.getElementById("open").addEventListener("click", () => opener.click());
  opener.addEventListener("change", async () => {
    const file = opener.files[0];
    opener.value = "";
    if (!file) { return; }
    const text = (await file.text()).replace(/\r\n?/g, "\n").replace(/\n+$/, "");
    if (editor.value.trim() && editor.value !== text && !(await confirm(words.sure))) { return; }
    stop(false);
    fromGuide = null;
    setProgram(text);
    say("");
    editor.focus();
  });

  // What the guide hands over: a listing, put in the editor, after asking
  // when the editor holds the child's own work.
  window.BASIC.typeIn = async function (text) {
    const own = editor.value.trim() && editor.value !== text && editor.value !== fromGuide;
    if (own && !(await confirm(words.sure))) { return; }
    stop(false);
    setProgram(text);
    fromGuide = text;
    say(words.typed);
    document.getElementById("run").focus();
  };

  // The program left last time.
  try { editor.value = localStorage.getItem(STORED) || ""; } catch (error) { editor.value = ""; }
  numberLines();
  editor.focus();
})();
