# R64 incident — a diagnose agent flattened the landed core file (line endings only)

At 07:51:04 the worktree `core/cfg/region_ast_generator.py` became **3 036 663 B, CR=0, LF=49937,
sha `5ffe31558df46f7f636d`** while `git hash-object` still matched HEAD — i.e. an agent read the file in
text mode and wrote it back with `\n` endings, losing the CRLF smudge state. Content was untouched
(`current == git show HEAD:<path>` byte-for-byte in LF form, BOM intact). diag4's agent noticed it and
was still investigating when it hit its own 150-turn cap ("Line endings of the landed core file changed
under me").

Effect if left in place: every landing proof (`CRLF 49937 / bare LF 0`), `mbuild.py`'s mixed-line-ending
guard, and `land63.py`'s `nl = '\r\n' if src.count(CR) else '\n'` would silently produce an LF-only core
file — the toolchain would still *work* (Python ignores the difference, and the agents' measurements are
therefore valid), but the repo's byte convention would be broken and the next round's sha comparisons
would be garbage. `region_analyzer.py` was never touched (still CRLF 27590, sha `c694d2514eb2f2b21ccf`).

**Fix applied at ~08:03 by `r64gate/restore_crlf.py`** — it refuses to write unless
`current.replace(b'\n', b'\r\n')` has sha256 `7ec41fa2f9cdd5d62c1aeea25e695d84a3c84b0de537937b2e867676fae95f0d`
and the BOM is present; result 3 086 600 B, CRLF 49937, bare LF 0, `git status` shows no tracked change.
No git write command was used, no other file touched, nothing was reverted that was not machine-damaged.

**How to apply for the rest of the round:** re-check
`python -X utf8 -c "import hashlib,io;print(hashlib.sha256(io.open(r'F:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py','rb').read()).hexdigest()[:20])"`
before every build/land step, and brief every agent that core files must be read with
`io.open(..., newline='')` or in binary — text-mode read + write is what caused this.

# Center verification of diag4 arm a (`cand_r64d4_a_deferred_prefix.json`) — measured in r64gate, not taken on trust

Rule: in `_try_deferred_return_in_loop` (landed L49798), the reverse stack scan chose `_val_start` as the
expression start and *marked* everything before it generated without emitting it. The edit emits those
prefix statements through the existing `_generate_stmts_from_instrs` when the prefix is ≥2 real
instructions and every produced node is a statement (`Assign/AugAssign/Expr/Return/Delete`), otherwise it
falls back to the original `return [_ret]`. Tagged `[R64-D4-A]`, three-element comment present,
1 edit, +25 lines, anchor unique, BOM+CRLF preserved (3 086 600 → 3 088 481 B).

| gate | landed (center) | arm d4a (center) | verdict |
|---|---|---|---|
| 4 targets official | 98/108 (main 29/33, graph 29/31, logger 28/30, fileio 12/14) | **103/108 — main 33/33, graph 30/31** | IMPROVED=2 REGRESSION=0 MOVED=0 |
| 4 targets strict | 135/144, main **missing 3 nested code objects** (`get_same_shard_server_ip_info.<dictcomp>`, `get_server_ip_info.<dictcomp>`, `get_server_ip_info.<lambda>`) | **140/144, missing=0** (main 34/34, graph 33/34) | +5 strict, whole-unit loss repaired |
| pinned battery (11 R63 repros) | 34/48, clean 4/11 | 34/48, clean 4/11 | **SAME=11, inert** |
| canary (quotation / market_time / 2× datetime_func) | 143/143, 10/10, 26/26, 25/25 = 204/204 | 204/204 | **SAME=4, inert** |

`IQCommon/common/main.pyc` goes 29/33 → **33/33 = fully OK** ⇒ this is Round 64's mandatory "at least one
pyc fixed to completely OK", already in hand before the remaining batches report.
Still required before landing: the 402-file A/B (deferred until the merged set is chosen), and a decision
on whether diag4's `b` arm (3 edits, clears `logger :: logging_process`) composes with it.
