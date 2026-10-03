#!/usr/bin/env node
// What the machine says about a program before and after running it
// (webapp/check.js): the jumps that lead nowhere, and errors explained.

"use strict";

const assert = require("assert");
const check = require("../webapp/check.js");

const program = '10 PRINT "GOTO 900"\n20 GOTO 40\n30 GOSUB 500\n40 IF A = 1 THEN 10 ELSE 70\n' +
                '50 ON X GOTO 10, 20, 800\n60 REM GOTO 999\n70 PRINT "X" \' GOSUB 998\n80 RESTORE 30\n';

assert.deepStrictEqual(check.numbers("10 PRINT\n  20 END\nPRINT\n"), [10, 20, null, null]);
assert.deepStrictEqual(check.missingJumps(program), [
  { line: 3, number: 30, target: 500 },
  { line: 5, number: 50, target: 800 },
]);
assert.deepStrictEqual(check.missingJumps("10 GO TO 30\n20 GOSUB 10\n"), [{ line: 1, number: 10, target: 30 }]);

const text = '10 PRINT "A"\n20 PRIMT "B"\n';
assert.deepStrictEqual(check.explain('Expected "=" found ""B"" at line 2', text, { reading: true }),
  { kind: "syntax", line: 2, number: 20, text: 'Expected "=" found ""B""' });
assert.deepStrictEqual(check.explain("Unmatched for at line 3", text, { reading: true }),
  { kind: "syntax", line: null, number: null, text: "Unmatched for" });
assert.strictEqual(check.explain("Bad value at line 1", 'PRINT 1\n', { reading: true }).number, null);
assert.strictEqual(check.explain("Out of data at line 4", text, {}).kind, "data");
assert.strictEqual(check.explain("TypeError: ops[(ip++)] is not a function", text, { internal: true }).kind, "inside");
assert.deepStrictEqual(check.explain("Illegal function call at line 3", text, {}),
  { kind: "other", line: null, number: null, text: "Illegal function call" });

// Spanish letters at their place in the PC's table, which wwwBASIC draws.
assert.strictEqual(check.forScreen('PRINT "¿Cómo?"'), 'PRINT "' + String.fromCharCode(168) + "C" +
                   String.fromCharCode(162) + 'mo?"');
assert.strictEqual(check.forScreen("Ñ Á €"), String.fromCharCode(165) + " A ?");

console.log("PASS  check.js");
