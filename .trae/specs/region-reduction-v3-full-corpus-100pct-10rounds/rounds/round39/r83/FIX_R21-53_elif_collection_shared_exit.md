# FIX R21-53 — NARROW elif-collection rule keyed on the shared false-exit block

Ticket **R21-53**. Unit `<module>.RealtimeEventSource.clock_worker`,
`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`,
currently 12/13. Base = `rounds/round39/r75/CANDIDATE_r75a_r2146_AB_on_r74d_30a4d7827122e165.py`.

Written immediately after the premise check (rule 5), appended as I go.

## 0. Mirror certification (measured, this run)

Mirror `D:/Temp/r83` = repo `core/ scripts/ parsers/ utils/ bytecode/ pycdc.py` (repo untouched, read-only).

| file | sha16 | bytes | convention |
|---|---|---|---|
| `core/cfg/region_ast_generator.py` (base installed) | `30a4d7827122e165` | 3884461 | BOM + 61672 CRLF, 0 bare LF, 0 `\r\r\n` |
| `core/cfg/region_analyzer.py` (landed, kept) | `f7d849e974904492` | 2104888 | BOM + 32910 CRLF, 0 `\r\r\n` |

Repo landed bytes are generator `11324f276cce6d5b` / analyzer `f7d849e974904492` (re-measured from
`core/cfg/`), i.e. the base I am handed is the banked r75a candidate, not repo bytes — as briefed.

## 1. Base measurement (re-measured, reproduces the brief exactly)

Regenerated with `python -X utf8 pycdc.py --region -o <out> <abs pyc>` after deleting the old output
(`D:/Temp/r83/out_base/realtime_event_source_base.py`, 21548 bytes):

```
len orig=1424 prod=1426 delta=2
hunks=2 landings=7 judge_diff=True
[single] status=failure units=12/13 success_rate=92.31%
  ***<module>.RealtimeEventSource.clock_worker: Failure: Different control flow
```

The two unfiltered windows (`unit_diff --all`) are both single-instruction inserts:

```
insert orig[1046..1046 @@7248..@-] prod[1046..1047] del=0 ins=1   + @7252 JUMP_FORWARD
insert orig[1099..1099 @@7582..@-] prod[1100..1101] del=0 ins=1   + @7590 JUMP_FORWARD
```

Both new jumps land on prod `@9206` — CONFIRMED by compiling the WHOLE product module on
Python 3.11.7 and resolving jump targets (`work/prodshape.py`):

```
prod @7248 POP_JUMP_FORWARD_IF_FALSE -> to 7254   line=249
prod @7252 JUMP_FORWARD              -> to 9206   line=250   (the `pass` arm tail)
```

`prod co_code len=9342` vs `orig 9330` (delta 2 instructions, the two JUMP_FORWARDs; everything else
is shape, not size).

## 2. Premise check (re-measured from region data + original disassembly, this run)

### 2a. Region data (read-only probe `work/premise.py`, in-process, no product bytes touched)

```
== IfRegion cond=7186 type=IF_ELIF_CHAIN
   then_blocks      [7212]
   elif_conditions  [7248]
   elif_bodies      [[7372, 7488]]
   elif_final_else  [7492, 7582, 7604, 7634, 7620, 7632, 7668, 8592, 7630, 7706, 8666, 8904, 7708,
                     7972, 8688, 8852, 8926, 9144, 7710, 7980, 8170, 8948, 7712, 8166, 8184, 8964,
                     8976, 7814, 8186, 8974, 8256, 8980, 8294, 8306, 8350, 8354, 8588, 8400, 8450,
                     8548, 8504, 8544]                (42 blocks)
   merge_block      7216
   IBC {op='and' blocks=[7248, 7270]}
== IfRegion cond=7216 type=IF_THEN
   then_blocks      [7248, 7270, 7492, 7372, 7488]   (5 blocks)
   else_blocks      []   merge_block  7582
== IfRegion cond=7270 type=IF_THEN_ELSE
   then_blocks [7372, 7488]   else_blocks [7492]   merge_block 7582
```

Discriminator, exactly as the ticket states, and it holds:

```
@7248 in  IfRegion@7186.elif_conditions                = True
@7248.false_exit (CFG successor)                       = 7492
@7492 in IfRegion@7216.then_blocks                     = True
@7492 in IfRegion@7186.elif_final_else                 = True
```

### 2b. CFG successor data for @7248

`successors = [7270, 7492, 9218]`. 9218 is the exception/other edge; the two normal edges are
true->7270, false->7492.

### 2c. Original bytecode ground truth (`dis.get_instructions`, line map via `co_lines()`)

```
orig @7184 POP_JUMP_FORWARD_IF_FALSE -> 7216   line=469   (A false -> 7216 = C's test)
orig @7200 POP_JUMP_FORWARD_IF_FALSE -> 7214   line=469   (chained-compare cleanup)
orig @7210 POP_JUMP_FORWARD_IF_TRUE  -> 7248   line=469   (condition true -> body @7248)
orig @7212 JUMP_FORWARD              -> 7216   line=469   (condition false -> merge @7216)
orig @7216..@7240 COMPARE_OP ==                  line=470
orig @7246 POP_JUMP_FORWARD_IF_FALSE -> 7582   line=470
orig @7248 LOAD_FAST now_date ... @7262 COMPARE_OP !=  line=472   <-- the "elif condition"
orig @7268 POP_JUMP_FORWARD_IF_FALSE -> 7492   line=472   <-- ITS FALSE EXIT
orig @7270 LOAD_GLOBAL system_log.debug(...)   line=473   <-- ITS TRUE SUCCESSOR (a statement)
orig @7488 LOAD_CONST None / @7490 RETURN_VALUE line=477
orig @7492 LOAD_DEREF self.event_queue          line=478   (sequential tail, the shared block)
orig @7582 LOAD_FAST now_date (next if)         line=482   (the @7216 arm's merge)
```

### 2d. Corrections to the brief (rule 6)

1. **`elif_final_else` is 42 blocks, not 44** (r78a said 44, my §12 restated it). Measured here: 42.
   Immaterial to the argument (it is still "the whole function tail"), but the number is corrected.
2. Everything else in the brief's premise statement held on my bytes: `@7248` IS collected as
   `@7186`'s elif condition; `elif_bodies` omits `@7270`; `@7492` is simultaneously in
   `IfRegion@7216.then_blocks` and in `@7186.elif_final_else`.
3. The `debug()` statement is NOT swallowed (r82a, §12 of the adjudication): confirmed — prod emits
   `system_log.debug(...)` and the `[R21-46]` veto is live in this base (`region_ast_generator.py`,
   consumed at 20577 area). The residual really is the two `JUMP_FORWARD -> @9206`.

## 3. Why this must be narrower than [R21-49] (the trap, quoted from the adjudication §8)

r78a's `[R21-49]` refused the **whole chain** at both granularities and got `+2 -> -269` (4 windows,
2 landings, judge 12/13, changed files = 1 = the target *regressing*), because
`@7186.elif_final_else` is the entire function tail and the downstream merge guard then abandoned
the fold and orphaned it. So this rule is constrained to:

* **(a) fire only on the shared-block signature** (`cond.false_exit ∈ parent-arm.then_blocks AND
  cond.false_exit ∈ chain.elif_final_else`), and
* **(b) preserve the chain's tail ownership** — `elif_final_else` population must be re-measured
  before/after; a shrink means I reproduced `-269` and I stop and bank, not install.

The second axis the ticket names (`@7184`'s false exit lands on `@7216`, i.e. `(A and B) or C`) is
CONFIRMED in 2c but is handled only if axis (a)/(b) is in place (see §6).

## 4. Where the collection happens (code read)

`_build_elif_region` (region_analyzer.py:21416) calls `_check_elif_chain(block, else_blocks, merge)`
at `:22746`, gets `elif_info` with keys `conditions/bodies/final_else/inline_boolop_chains`, and the
chain is built at `:23095` (`elif_conditions=elif_info["conditions"]`). The candidate set that
contains `@7248` is therefore produced inside `_check_elif_chain`.

## 5. Plan

1. Read `_check_elif_chain` and find the loop that appends `@7248` to `conditions`.
2. Implement `[R21-53]`: drop that single condition (and its paired body) when the shared-exit
   signature holds, keeping `final_else` byte-for-byte identical. Use only region data / CFG
   successor structure; no offsets, no names, no counters.
3. Census BEFORE editing: evaluations + fires over the 20 panel files, corpus-wide counts, inert
   probe, byte-change census per fire.
4. Measure halves; re-measure `elif_final_else` population base-vs-candidate; membership census
   with the counting rule STATED.
5. Acceptance bar or bank.

## 6. Status log (appended as I go)

* 20:20 mirror certified, base re-measured `+2 / 2 windows / 7 landings`, judge `12/13`.
* 20:25 premises confirmed (2a/2b/2c); `elif_final_else` count corrected to 42.
