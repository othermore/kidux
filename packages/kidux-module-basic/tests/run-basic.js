#!/usr/bin/env node
// Runs BASIC programs under node, through wwwBASIC and bindings of the
// tests' own (docs/dev/basic.md): what a program prints is kept as text,
// what it draws and sounds as lines, and the keys it reads come from a
// list, "Enter" for the Enter key.
//
//   node tests/run-basic.js <wwwbasic.js> <directory>
//       every NN-name.bas there, with NN-name.in (its keys, one a line) when
//       it reads, against NN-name.out: the screen's text, then a line ---,
//       then what it drew and sounded; a difference fails
//   node tests/run-basic.js <wwwbasic.js> --one <file.bas> [key ...]
//       one program, its result as JSON: {text, calls, ended, error}
//
// Each program runs in a process of its own, so that one that never ends
// is simply ended after a while, and leaves nothing behind for the next.

"use strict";

const fs = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

const ENOUGH = 1500;   // ms a program may run before it is taken as going on for ever
const KEPT = 20000;    // characters of its text, and lines of its calls, kept

function one(wwwbasic, file, keys) {
  const basic = require(path.resolve(wwwbasic));
  const code = fs.readFileSync(file, "utf8");
  const queue = keys.map((key) => (key === "Enter" ? "\r" : key)).join("").split("");
  let text = "";
  let line = "";
  let input = "";
  const calls = [];
  let done = false;

  function finish(ended, error) {
    if (done) { return; }
    done = true;
    if (line) { text += line + "\n"; }
    // A program that never ends writes a lot: the last of it is enough.
    if (text.length > KEPT) { text = text.slice(-KEPT); }
    process.stdout.write(JSON.stringify({ text: text, calls: calls.slice(-KEPT), ended: ended, error: error }) + "\n",
                         () => process.exit(0));
  }

  const bindings = {
    PutCh(ch) {
      if (ch === undefined) { text += line + "\n"; line = ""; }
      else if (ch !== String.fromCharCode(219)) { line += ch; }
    },
    Halt() { finish(true, null); },
    Pace() { return 100000; },
    Inkey() { bindings.Yield(); return queue.length ? queue.shift() : ""; },
    LineClear() { input = ""; },
    LineValue() { return input; },
    LineInput() {
      while (queue.length) {
        const key = queue.shift();
        if (key === "\r") { bindings.PutCh(); return 0; }
        input += key;
        line += key;
      }
      bindings.Yield();
      return -1;
    },
  };
  const recorded = {
    statement_screen_iIII: "SCREEN", statement_cls_I: "CLS", statement_color_iII: "COLOR",
    statement_locate_iiI: "LOCATE", statement_width_iI: "WIDTH", statement_pset_pI: "PSET",
    statement_preset_pI: "PRESET", statement_circle_piIIIIS: "CIRCLE", Line: "LINE",
    statement_paint_pII: "PAINT", statement_sound_ii: "SOUND",
  };
  for (const [name, word] of Object.entries(recorded)) {
    bindings[name] = (...args) => {
      calls.push(word + " " + args.filter((a) => a !== undefined).join(","));
      if (word === "CLS") { text += line ? line + "\n" : ""; line = ""; }
    };
  }

  console.error = (message) => finish(false, String(message));
  console.info = () => {};
  process.on("uncaughtException", (error) => finish(false, String(error)));
  setTimeout(() => finish(false, null), ENOUGH);
  try {
    basic.Basic(code, { bindings: bindings });
  } catch (error) {
    finish(false, String(error));
  }
}

function every(wwwbasic, directory) {
  let failed = 0;
  const programs = fs.readdirSync(directory).filter((name) => name.endsWith(".bas")).sort();
  for (const name of programs) {
    const base = path.join(directory, name.slice(0, -4));
    const keys = fs.existsSync(base + ".in")
      ? fs.readFileSync(base + ".in", "utf8").split("\n").filter((key) => key !== "")
      : [];
    const ran = spawnSync(process.execPath, [__filename, wwwbasic, "--one", base + ".bas", ...keys],
                          { encoding: "utf8" });
    let got;
    try {
      const result = JSON.parse(ran.stdout);
      got = result.text + "---\n" + result.calls.map((call) => call + "\n").join("") +
            (result.error ? "error: " + result.error + "\n" : "");
    } catch (error) {
      got = "(no result: " + ran.stdout + ran.stderr + ")\n";
    }
    const wanted = fs.existsSync(base + ".out") ? fs.readFileSync(base + ".out", "utf8") : "(no .out)\n";
    if (got === wanted) {
      console.log("PASS  " + name);
    } else {
      failed += 1;
      console.log("FAIL  " + name + "\n--- wanted\n" + wanted + "--- got\n" + got);
    }
  }
  console.log(programs.length + " programs, " + failed + " failed");
  process.exit(failed ? 1 : 0);
}

const args = process.argv.slice(2);
if (args[1] === "--one") {
  one(args[0], args[2], args.slice(3));
} else if (args.length === 2) {
  every(args[0], args[1]);
} else {
  console.error("usage: run-basic.js <wwwbasic.js> <directory> | <wwwbasic.js> --one <file.bas> [key ...]");
  process.exit(2);
}
