# DIAG B140 — `IQData/api/api_base.pyc :: <module>.get_history_df` (Round 11, DIAGNOSTIC ONLY)

Status: **in progress**. Instruments: `D:/Temp/r10g7/r10g7_hunk.py` (hunk census),
`D:/Temp/r140/dump_region.py` (orig-vs-recompiled-prod instruction+line dump),
`D:/Temp/r139m/probe_handlers.py` pattern (role census via `RegionASTGenerator(cfg).region_analyzer`).
Scratch: `D:/Temp/r140/`. `core/` untouched (`git status --porcelain -- core/` = 0 at start).
NOTE: Git Bash mangles argv starting with `/` (MSYS path conversion) — pass unit paths with
`export MSYS_NO_PATHCONV=1`, otherwise `find()` returns nothing and you get a false `StopIteration`.

## 0. Re-verification of the main agent's measurements (what is right, what is wrong)

| main agent claim | verdict |
|---|---|
| 20 hunks, 15 target-only + 5 content, pairing by full qualname `copies 1/1` | **confirmed** (`r10g7_hunk.py --corpus` prints `hunks=20 real=5 reloc=15 deleted=36 inserted=36`) |
| "orig 1900 / prod 1900 instructions" | **口径 difference, not a disagreement**: raw `dis.get_instructions` = 1900; with `NOISE = NOP/CACHE/EXTENDED_ARG` dropped (r10g7 口径) both sides are **1881/1881**. Net delta is 0 either way. |
| hunk indices `orig[457:462]`, `orig[522:523]`, `orig[528:533]` | off by 8/3/… because of the NOP-drop; the same hunks are `orig[449:454]=5→prod[449:450]=1`, `orig[514:515]=1→prod[510:519]=9`, `orig[520:525]=5→prod[524:529]=5`, plus **two the brief did not list**: `orig[527:536]=9→prod[531:532]=1` and `insert prod[540:544]=4` |
| hunk 1 = "compound assignment and a following loop-test arithmetic squashed into the jump" | **wrong description, right location.** Nothing is "squashed". `time_count -= 1` (orig line **419**) is *moved*, not deleted: it is re-emitted at the very end of the product's `if`-body (prod `insert orig[544:544]→prod[540:544]`, product source line **311**). The `POP_JUMP_FORWARD_IF_TRUE ->@2254` became `POP_JUMP_FORWARD_IF_FALSE ->@2570` = the *polarity flip of the enclosing test*, see §1 |
| hunk 2 = "polarity inverted AND a test materialised inline" | half right: the polarity *is* inverted (`IF_TRUE ->@2518` → `IF_FALSE ->@2518`), but nothing is "materialised inline" — the 9 inserted instructions are `max_len_real_data = count if max_len_real_data > count else max_len_real_data` **which the original already contains at @2518–@2536**. It is the *same statement*, relocated into the then-arm. |
| hunk 3 = "different statements aligned by mistake after a reordering" | **correct, and the main agent's own §4.1 correction stands.** I confirm no "operand reversal" defect exists. |
| "the real difference is that the product puts 434 before `-=`" | **true but incomplete — this is the whole story only for the inner `if`.** There is a *second, larger* instance of the same defect 200 bytes earlier (`time_count -= 1` / the `if frequency==MINUTE : elif : else :` chain), see §1. |
| "I tested swapping product lines 304/305 as an oracle and it did not flip the unit ⇒ defect is structural" | **confirmed and explained**: swapping 304/305 does not change which *block* owns them. The required edit is a **dedent** (see §2 oracle). |

## 1. ROLE CENSUS — the two branch structures (measured, not inferred)

### 1.1 ORIGINAL bytecode (`api_base.pyc`, `get_history_df` co_firstlineno=329)

Statements are identified by the line number the instruction starts.

```
@2144 line 415  if not include and frequency == Frequency.MINUTE.value and cur_datetime not in (min_datetime, pm_open):
@2146   POP_JUMP_FORWARD_IF_TRUE  ->@2254     (include truthy  -> skip whole body)
@2188   POP_JUMP_FORWARD_IF_FALSE ->@2254     (freq != MINUTE  -> skip)
@2200   POP_JUMP_FORWARD_IF_FALSE ->@2254     (cur in tuple    -> skip)
@2202 line 417    if not (pm_open > cur_datetime > am_close or cur_datetime > pm_close):   [line 418 = or-continuation]
@2226     POP_JUMP_FORWARD_IF_TRUE ->@2254     (chain A true  -> skip body)
@2242     POP_JUMP_FORWARD_IF_TRUE ->@2254     (or-operand B true -> skip body)
@2244 line 419      LOAD_FAST time_count / LOAD_CONST 1 / BINARY_OP -= / STORE_FAST time_count
@2254 line 422  if frequency == Frequency.MINUTE.value:        <-- MERGE of BOTH ifs above
@2294   POP_JUMP_FORWARD_IF_FALSE ->@2318
@2296 line 423    max_len_real_data = time_count
@2300 line 426    if max_len_real_data > count:   @2310 POP_JUMP_IF_FALSE ->@2316
@2312 line 427      min_count = count
@2316 JUMP_FORWARD ->@2580                       (elif-chain arm exit -> chain join)
@2318 line 428  elif int(frequency[:-1]) >= 5:
@2370   POP_JUMP_FORWARD_IF_FALSE ->@2560        (elif test false -> else-arm)
@2372 line 429    max_len_real_data = ceil(time_count / int(frequency[:-1]))
@2450 line 430    if not include and _query_date != pm_open:
@2452     POP_JUMP_FORWARD_IF_TRUE  ->@2518
@2464     POP_JUMP_FORWARD_IF_FALSE ->@2518
@2466 line 431      if not (pm_open > _query_date > am_close or _query_date > pm_close):  [432 = or-cont]
@2490       POP_JUMP_FORWARD_IF_TRUE ->@2518      (chain A true -> skip body)
@2506       POP_JUMP_FORWARD_IF_TRUE ->@2518      (or-operand B true -> skip body)
@2508 line 433        LOAD max_len_real_data / LOAD 1 / BINARY_OP -= / STORE   <-- only the -= is in the body
@2518 line 434  max_len_real_data = count if max_len_real_data > count else max_len_real_data
                    <-- 5 preds: @2452,@2464,@2490,@2506 + fallthrough from @2516
@2538 line 435  max_len_real_data = 0 if max_len_real_data < 0 else max_len_real_data
@2558 JUMP_FORWARD ->@2580                       (elif-chain arm exit -> chain join)
@2560 line 438  else: max_len_real_data = time_count
@2564 line 439  if max_len_real_data > count:   @2574 POP_JUMP_IF_FALSE ->@2580
@2576 line 440    min_count = count
@2580 line 443  <continuation of the function>
```

Census facts (original), stated only in whitelisted terms:

* `blk@2244` (`time_count -= 1`) — **predecessors**: only the fall-through of the block ending `@2242 POP_JUMP_FORWARD_IF_TRUE`.
  **successor**: `blk@2254`. Its block-tail is `STORE_FAST`, i.e. a sequential edge, no jump.
* `blk@2254` — is the **true successor** of `@2226`, `@2242`, `@2146`, the **false successor** of `@2188`, `@2200`,
  **and** the sequential successor of `blk@2244`. So it is simultaneously the merge of the inner `if`
  (line 417) and of the outer `if` (line 415). Both `if`s have an **empty then-arm** and their *only* body
  statement hangs off the **other** edge of the test.
* The `if frequency==MINUTE / elif / else` chain occupies `@2254..@2578` and joins at `blk@2580`.
  `blk@2580` is **not** the true successor of `@2146` — only of `@2316`/`@2558`/`@2574`/fall-through.
* `blk@2518` (line 434 ternary) — same dual role for the if@430 / if@431 pair: 5 conditional preds + 1
  fall-through pred from `blk@2508`; `blk@2538` (line 435) is its sequential successor; the arm-exit
  `@2558 JUMP_FORWARD ->@2580` is what makes `blk@2580` the *chain* join.

⇒ Required shape: **two nested "if with empty then-arm / body on the fall-through edge" regions whose merge
is the immediately following statement block (`@2254`, `@2518`), and that merge must NOT be pulled out to
the `elif`-chain join (`@2580`/`@2570`).**
