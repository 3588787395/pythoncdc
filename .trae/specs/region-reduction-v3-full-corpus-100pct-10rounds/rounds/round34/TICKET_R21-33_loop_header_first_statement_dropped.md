# R21-33 (pre-digested, round 35) — broker `_trade_status_handle`: the FIRST statement of a fused loop-header block is dropped

Measured 2026-10-11 ~17:15 on the **gate-34 sealed base** (generator `065e4d77243190dc`,
`trade_live_broker.pyc` 123/128). Victim shape:

```
len orig=127 prod=124 delta=-3  hunks=3  landings=2  judge_diff=True
== delete orig[7..16 @@46..@@90]   del=9 ins=0     ← hunk 1: a whole statement missing
== insert orig[120..120 @@830..@-] prod[111..116]  del=0 ins=5
== replace orig[126..127 @@872..@@872] prod[122..124]  del=1 ins=2
```

## 0. Hunk 1 is a statement loss, not a shift

Original instructions `@46..@90` disassemble to exactly one Python statement:

```
@46 LOAD_GLOBAL get_trade_status / @58 LOAD_FAST self / @60 LOAD_ATTR trade_id /
@70 LOAD_CONST True / @72 KW_NAMES / @74 PRECALL 2 / @78 CALL 2 /
@88 LOAD_FAST self / @90 STORE_ATTR trade_info
```
i.e. `self.trade_info = get_trade_status(self.trade_id, True)`.

The emitted product (`trade_live_brokerOK.py:894-899`) goes straight from
`engine.set_engine(engine)` to `trade_status = self.trade_info[2]`, so the statement is **never rendered**.
That is a real behaviour loss, not an offset shift.

## 1. Why it vanishes — the block it lives in is the loop header

Read-only CFG/analyzer census of the unit (`forensics`-style, no generation):

```
block @46  n=20  term=POP_JUMP_FORWARD_IF_FALSE  role=BlockRole.LOOP_HEADER
           entry_region=LoopRegion  owner=LoopRegion
LoopRegion hdr=46 cond=46 init_blocks=[] pre_condition_blocks=[] else=[720, 830]
           body=[46, 150, 186, 296, 318, 340, 452, 474, 680, 722]
```

`get_block_by_offset(46 / 88 / 100 / 112)` all return **the same block**: CPython fused three statements
into one maximal straight-line block —

1. `self.trade_info = get_trade_status(self.trade_id, True)`   (@46..@90) **← dropped**
2. `trade_status = self.trade_info[2]`                          (@100..@~118) **← emitted**
3. the loop condition test `self.trade_status != trade_status`   (block terminator) **← emitted as `while`**

So the defect is not in region formation (the region is the loop header and that is correct) but in the
header-prefix renderer, which consumes the prefix and keeps only the **last** statement before the
condition. **Named site:** `RegionASTGenerator._loop_process_header_instructions`
(`core/cfg/region_ast_generator.py:12722`; the collected prefix is flushed by
`body_stmts.extend(_hdr_stmts)` at `:12915`). Start by counting how many statements the prefix walk
produces for this block — one emitted from two present is the signature.

Do not confuse this with `pre_condition_blocks`: it is a *block*-level list (analyzer
`region_analyzer.py:518`, only read at `:5368` as a jump-target guard, consumed at generator `:12923`),
and it is empty here because the prefix is intra-block, not a separate block.

## 2. The flip needs a second, independent mechanism (do not promise hunk 1 alone)

Hunks 2 and 3 are the loop-tail family already documented in
`rounds/round32/TICKET_R21-28_broker_loop_tail_not_emitted.md` §1: the original's `@872 JUMP_BACKWARD` is
rendered as `LOAD_CONST None / RETURN_VALUE`, plus a 5-instruction `POP_JUMP_BACKWARD_IF_TRUE` insert at
`@830`. A criterion that only restores hunk 1 leaves `−3 → 0` at best with hunk 2/3 still open, i.e.
**no unit flip**. Split the ticket accordingly: fix A = hunk 1 (this note), fix B = the loop-tail
rendering; the acceptance bar is `delta=0 hunks=0 landings=0 judge_diff=False` (broker 123 → 124/128).

## 3. Method requirements carried over from R21-28 (this round's lesson, measured)

- Measure the candidate on the **20-file panel** before the gate:
  `python -X utf8 D:/Temp/t30/panel14.py <mirror_root> <tag> 0 20`. This round's v1 candidate
  (interior-only conjunct) looked like a clean +1 on the victim file and was caught only by the panel
  (`quote 91→90`, `real_quote 45→44`, net −1) — see `rounds/round34/PANEL_R34.md`.
- A criterion that adds/keeps a statement must be checked against **payload-carrying vs payload-free**
  sites and against the region's own declared `back_edge_block(s)`; R21-28's three own-data conjuncts are
  the template (`rounds/round34/FIX_R21-28_r34.md` §4).
- Census the qualifying population corpus-wide over the 402-file verification face before claiming any
  family; the read-only rig `rounds/round34/census_r34_loop_tail.py` is the pattern (it prints
  hits/terminal/interior/qualifying and can be filtered by filename).
- Mirror: reuse `D:/Temp/r30chk` (holds the landed generator; pristine copy of every base edit goes to a
  content-addressed file in scratch before patching). Repo read-only for measurement; only
  `core/cfg/region_ast_generator.py` may change unless the diagnosis proves analyzer-side, in which case
  write it up rather than editing both files in one round.
- `python -X utf8`, never `PYTHONIOENCODING`; byte-level CRLF-preserving patches; nothing over 300 s;
  judge a fresh product with `scripts/pyc_verify.py single <abs pyc> --source <product>`.

## 4. Hunk 2/3 mechanism, measured on the same base (17:22)

The analyzer's own declaration for this loop is the defect:

```
LoopRegion hdr=46 cond=46 init_blocks=[] pre_condition_blocks=[]
           body=[46,150,186,296,318,340,452,474,680,722]  else=[720, 830]
```

`@830` is `time.sleep(0.5)` and its block's terminator is `@872 JUMP_BACKWARD -> 46`, i.e. **this loop's own
header**. A `while ... else:` clause runs after the loop exits, so it can never jump back to the header; and
`@720` is just the preceding body arm's tail `JUMP_FORWARD -> 830`, a jump *into* that content. So both
`else_blocks` entries are body-tail blocks, and the generator faithfully renders the wrong construct:

```python
        else:            # product lines 916-917 -> while-else, runs once, not per iteration
            time.sleep(0.5)
```

which is also why hunk 3 replaces the original `@872 JUMP_BACKWARD` with `LOAD_CONST None / RETURN_VALUE`
(the emitted loop has no tail left to jump from), and why the product shows an extra
`self.trade_status != trade_status / POP_JUMP_BACKWARD_IF_TRUE` at the tail — CPython's rotated-while form
for the source it was handed, not an independent bug.

**Candidate rule (own-data, decided at identification time, no cross-region scan):** a block listed in a
`LoopRegion.else_blocks` whose last instruction is `JUMP_BACKWARD`/`JUMP_BACKWARD_NO_INTERRUPT` to *that same
loop's* `header_block` is not else-clause content; move it to `body_blocks`, and move any else block whose
only forward edge lands on such a body block (`@720 -> @830` here).

**Duty before adopting (the R21-28 lesson, measured this round):** first census how many
`LoopRegion.else_blocks` entries corpus-wide contain a back-edge-to-own-header block — that is the
population the rule moves; then measure the rule **alone** on the 20-file panel, because hunk 2/3 interacts
with the header emission of every while loop, and an over-fire here shows up as green files going red, not as
a bad number on the victim file.

## 5. The §4 rule was PROTOTYPED and MEASURED as a negative (17:30) — the analyzer-membership route is closed for this shape

Prototype: `build_prototype_r35_else_guard.py` applied to a byte-identical copy of the analyzer
(`35e227ac3e7b25af` -> `ab25e98a4f708b6b`, 26 lines at :5303, mirror `D:/Temp/r30chk` only, repo untouched;
mirror restored byte-identical afterwards and re-hashed to prove it). Population measured first
(`D:/Temp/r34/else_census.py`): **1169 loops have non-empty `else_blocks`, exactly 3 contain a block whose
terminator jumps back to that same loop's header** - `_process_order @3128`, `_process_cancel_order @2000`,
`_trade_status_handle @830`, all with `hdr=46` in `trade_live_broker.pyc`. So the rule is narrow, and narrow
was not enough:

| unit | sealed (gate-34 base) | under the else-guard prototype | direction |
|---|---|---|---|
| `_trade_status_handle` | `−3 / 3 hunks / 2 landings` | `−7 / 2 / 3` | delta **worse by 4** |
| `_process_order` | `−465 / 4 / 1` | `−471 / 3 / 2` | worse by 6 |
| `_process_cancel_order` | `−293 / 3 / 0` | `−299 / 3 / 1` | worse by 6 |
| `_sync_worker`, `etf_purchase_redemption`, `ipo_stocks_order` | unchanged | unchanged | untouched |

Broker units held at 123/128 (no flip, no regression). Reading of the result: the membership list is not the
defect - the generator already emits those blocks' content in a defensible position, and re-parenting them
into `body_blocks` (appended last) **misplaces** the tail text, so hunks grow. The construct-level defect
(`else: time.sleep(0.5)` rendered as a while-else instead of as body-tail statements that then take the
back-edge) therefore belongs to the **loop renderer**, not to `region_analyzer.py`'s `else_blocks`.

Named follow-on for whoever takes this ticket: keep `else_blocks` as declared, and in the loop emitter render
an else block whose terminator is a back-edge to this loop's header **inside the body tail** (statements
then the back-edge), rather than as the `else:` suite. Verify per §3 that the three units' shapes actually
shrink before claiming anything, and panel it - this prototype is the second time in two rounds that a
structurally reasonable rule moved a diff the wrong way (`_sync_worker`'s M2 was the first).

## 6. Scope correction to §5 — the prototype moved only the direct offender, not its feeder

The prototype's negative result does **not** close the renderer axis, and the ticket must not be read that
way. In `_trade_status_handle` the declared else pair is `[720, 830]`:

- `@830` = `time.sleep(0.5) … POP_TOP` then `@872 JUMP_BACKWARD -> 46` (this header) → moved by the guard;
- `@720` = a one-instruction `JUMP_FORWARD -> 830`, i.e. an earlier body arm's exit that lands **inside**
  the block that was moved → **not** matched by the guard (its terminator is a forward jump), so it stayed
  declared as else content while the code it jumps into moved to the body.

So the prototype produced a half-moved pair, which is exactly the shape that would mis-render and add
hunks. §4 already stated the transitive clause ("move any else block whose only forward edge lands on such
a body block"); the prototype implemented only the first half of that sentence. Before this axis is declared
closed, re-run the prototype with the **transitive** move (one hop is enough here: `@720 -> @830`), and
report both variants separately, because "partial move worsens" and "full move worsens" are different
findings with different consequences.

Second, independent caution, measured: even a perfect fix for hunk 2/3 leaves hunk 1 (`del=9`, the dropped
`self.trade_info = get_trade_status(self.trade_id, True)`) outstanding, so the unit goes from `−3/3/2` to
about `−9/1/0` and **still fails**. Neither half alone flips `_trade_status_handle`; the pair is the
acceptance bar, and the same is true of `_process_order` / `_process_cancel_order` (their measured worsening
`−465→−471`, `−293→−299` is the same half-moved artifact and should be re-measured with the transitive rule).

## 7. Variant B measured (17:33) — the §6 half-move explanation is FALSIFIED; membership axis closed

Re-ran the guard with the **transitive** clause implemented (`e6f1c1de71615d5c` in the mirror: move the
back-edge-to-own-header else block **and** any else block whose terminator jumps forward into one of them,
iterated twice, so `@720 -> @830` moved together). Result is **byte-for-byte the same verdict as the partial
move**:

| unit | sealed | A (direct only) | B (transitive) |
|---|---|---|---|
| `_trade_status_handle` | `−3 / 3 / 2` | `−7 / 2 / 3` | `−7 / 2 / 3` |
| `_process_order` | `−465 / 4 / 1` | `−471 / 3 / 2` | `−471 / 3 / 2` |
| `_process_cancel_order` | `−293 / 3 / 0` | `−299 / 3 / 1` | `−299 / 3 / 1` |
| `_sync_worker` / `etf_purchase_redemption` / `ipo_stocks_order` | unchanged | unchanged | unchanged |

Broker held 123/128 in both arms; no unit flipped and none regressed. Because identical numbers come out of
a partial and a complete re-parenting, the defect is **not** which list the block belongs to: the current
`else_blocks` declaration is compensating for something in the generator's loop rendering, and moving the
blocks makes the rendered text worse either way. **Do not spend another round on
`region_analyzer.py`'s `else_blocks` for this unit** — §6's "re-run the transitive move" duty is now
discharged, and the open lever is hunk 1 (§1-§2, the dropped header-prefix statement in
`_loop_process_header_instructions`) plus a renderer-side study of how these three units' bodies reach the
`time.sleep(0.5)` tail.

Mirror `D:/Temp/r30chk` restored to `35e227ac3e7b25af` and re-hashed byte-identical to the repo file;
the repo analyzer was never edited, and neither prototype went near `core/`.
