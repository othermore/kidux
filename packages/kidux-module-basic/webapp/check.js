// What the machine says about a program, apart from running it: the
// BASIC number of each line, the jumps that lead nowhere, and what an
// error from wwwBASIC means for a child. Plain functions, read by the
// page and by the module's tests under node.

(function (root) {
  "use strict";

  // The BASIC number at the start of each line of the editor, or null.
  function numbers(text) {
    return text.split("\n").map((line) => {
      const found = /^\s*(\d+)/.exec(line);
      return found ? Number(found[1]) : null;
    });
  }

  // A line without its strings and its remark: what BASIC reads as words.
  function words(line) {
    let out = "";
    let quoted = false;
    for (let i = 0; i < line.length; i++) {
      const ch = line[i];
      if (ch === '"') { quoted = !quoted; out += " "; continue; }
      if (quoted) { out += " "; continue; }
      if (ch === "'") { break; }
      out += ch;
    }
    const remark = /(^|[\s:\d])REM\b/i.exec(out);
    return remark ? out.slice(0, remark.index + remark[1].length) : out;
  }

  // Every jump to a BASIC number that no line has, in the editor's order:
  // [{line, number, target}], line counted from 1 in the editor, number
  // the BASIC number of that line or null.
  function missingJumps(text) {
    const lines = text.split("\n");
    const known = new Set(numbers(text).filter((n) => n !== null));
    const missing = [];
    const jump = /\b(GO\s*TO|GO\s*SUB|THEN|ELSE|RESTORE)\s*((?:\d+\s*,\s*)*\d+)/gi;
    lines.forEach((line, index) => {
      const own = numbers(line)[0];
      const read = words(line.replace(/^\s*\d+/, ""));
      let found;
      while ((found = jump.exec(read)) !== null) {
        for (const target of found[2].split(",").map((n) => Number(n.trim()))) {
          if (!known.has(target)) {
            missing.push({ line: index + 1, number: own, target: target });
          }
        }
      }
    });
    return missing;
  }

  // What an error from wwwBASIC means: {kind, line, number, text}. kind is
  // "syntax" (the program could not be read; line is the editor's, number
  // its BASIC number or null, and line past the last line means something
  // is missing at the end), "data" (READ found no DATA left), "inside" (a
  // mistake wwwBASIC cannot name: a RETURN without GOSUB, a NEXT without
  // FOR) or "other". how.reading says the error came while wwwBASIC read
  // the program, how.internal that it was JavaScript's and not BASIC's.
  // wwwBASIC counts lines right only while it reads the program: an error
  // while it runs names the last line, so its line is left out.
  function explain(message, text, how) {
    how = how || {};
    const at = / at line (\d+)$/.exec(message);
    const bare = at ? message.slice(0, at.index) : message;
    if (how.internal || /^(TypeError|ReferenceError|RangeError)\b/.test(message)) {
      return { kind: "inside", line: null, number: null, text: bare };
    }
    if (/^Out of data/i.test(bare)) {
      return { kind: "data", line: null, number: null, text: bare };
    }
    if (how.reading && at) {
      const line = Number(at[1]);
      const lines = text.replace(/\n+$/, "").split("\n");
      if (line > lines.length) {
        return { kind: "syntax", line: null, number: null, text: bare };
      }
      return { kind: "syntax", line: line, number: numbers(text)[line - 1], text: bare };
    }
    return { kind: "other", line: null, number: null, text: bare };
  }

  // wwwBASIC draws a character by its number in the PC's own table of
  // letters (code page 437), where Spanish letters sit elsewhere than in
  // the web's: á is 160 there, not 225. So the program is handed over with
  // each such letter at its place in that table, and the screen shows it;
  // the capitals the table has not, Á Í Ó Ú, go without their accent.
  const PC = {
    "á": 160, "é": 130, "í": 161, "ó": 162, "ú": 163, "ñ": 164, "Ñ": 165, "ü": 129,
    "Ü": 154, "É": 144, "¿": 168, "¡": 173, "ç": 135, "Ç": 128, "à": 133, "è": 138,
    "ì": 141, "ò": 149, "ù": 151, "â": 131, "ê": 136, "î": 140, "ô": 147, "û": 150,
    "ä": 132, "ë": 137, "ï": 139, "ö": 148, "Ä": 142, "Ö": 153, "º": 167, "ª": 166,
    "Á": 65, "Í": 73, "Ó": 79, "Ú": 85, "À": 65, "È": 69, "Ò": 79,
  };

  function forScreen(text) {
    return text.replace(/[^\x00-\x7f]/g, (ch) => (ch in PC ? String.fromCharCode(PC[ch]) : "?"));
  }

  const api = { numbers: numbers, missingJumps: missingJumps, explain: explain, forScreen: forScreen };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    root.KiduxBasic = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
