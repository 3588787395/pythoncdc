# BASELINE_ROUND37 — state handed to the next gate (input `rounds/round36/after`, 6612/6617, 399/402)

## Landed and certified (gate 36, commits `a1316bdf` + `70eff476` + `5e54094f`, all pushed)

- analyzer `efd455859b69d8a1` — `_is_while_true`: header test whose landing block jumps back to that
  same header keeps both exits inside the cycle ⇒ the loop is `while True` and the test is nested `if`.
- generator `37997bdac555b2e9` — `_loop_handle_no_exit_successors`: a landing block that is *also*
  entered from inside the then side is the `if`'s merge, so the then side is rendered with the suite
  renderer `_if_generate_branch_stmts(blocks = body_blocks − header − merge)` and the merge follows
  the `If`. `_generate_block_statements` is falsified for that job (`−85/2`).

Chain: regen `ok=402 bad=0`, verify `786/786 469/469 538/538 887/887 855/855 998/999 797/801
1281/1282`, report `翻正单元=1 文件级回退=0 UNIT_REGRESSIONS=0 新增失败单元=0`, checks
`quotation 153/153 · small34 1562→1563 · selfcheck OK · pytest 2 failed 282 passed`.
Panel 20 files: 19 byte-identical, zero decreases, all six canaries held.

## Residual: 3 files / 5 units, with who owns what

| unit | shape on gate-36 bytes | owner | what is still missing |
|---|---|---|---|
| `trade_live_broker._process_cancel_order` | `−1 / 3` | engineer **r60a** (mirror `D:/Temp/r60`) | the then-arm `continue` must be the last statement **inside `Try.body`**; proved by compiling both source shapes (164 vs 163 instrs) |
| `quote.run_individual_transform` | `0 / 2` needs analyzer `c069d359cbfe76b0` | engineer **r62a** (mirror `D:/Temp/r62`) | one 9-instruction block rendered in the wrong position; the original is the negated early-guard `if not message: warning; continue` |
| `trade_live_broker._sync_worker` | `−3 / 5` | r62a's second victim | relocation + flipped polarity + moved `time.sleep(60)` |
| `realtime_event_source.clock_worker` | `−113 / 7`; `−3 / 8` with banked `3d4f27de6d80ab6e` | unowned | placement + the lost 17-instruction guard `@6690` |
| `trade_live_broker._process_order` | `−68 / 14` (my rig: `orig=519 prod=454`) | queued as R21-37 | ternary-as-call-argument with empty arms, plus one dropped `strategy_log.info(f'…')` statement |

## Correction to a claim I already committed

My round-36 note and commit message say the clock_worker residual is one relocation of ~106
instructions that are emitted **late** (`del 109 @7972` vs `ins 106 @9194`). Re-measuring the same
build (`3d4f27de6d80ab6e`, product `D:/Temp/t30/out/r36cw_*`, rig `D:/Temp/r36/align_unit.py`) puts
the extra copy at `prod[1182..1283 @7886..@8488]` while the **later** region is the one that is
short (`replace orig[1347..1411 @8840..@9212]` 65 → 1). So the direction depends on which aligner
is trusted; what both agree on is that the content is present, in the right amount, at the wrong
place — roughly a thousand offsets apart. The ticket text must say "misplaced by ~1k offsets,
direction aligner-dependent", not "late".

Also recorded so nobody re-does it: `align_unit.py`'s per-window output for `clock_worker` is ~55
`replace` windows of exactly 1 instruction, and the first of them is an artifact — it compares
`LOAD_CONST <code object check_handle_date … file "./fly_docker_py311/…" line 380>` against
`… file "<p>" line 204>`. Nested-code-object reprs always differ by construction, so windows whose
only payload is a `LOAD_CONST <code object …>` are NOT defects; the authoritative count stays
`unit_diff`'s `−3 / 8`. Use `unit_diff` for verdicts and the aligner only for the large windows.

## Gate-order rule learned this round

A zero-flip gate does **not** consume the round's gate label: gate 36 first certified hunk A alone
at `翻正单元=0` (reverted byte-exactly, `git status core/+site-packages` = 0), and the same label 36
was then re-run with the analyzer+generator pair, which landed. Keep label 37 reserved for the next
real candidate, and install only candidates that flip at the panel.
