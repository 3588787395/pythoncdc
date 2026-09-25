# Round 67 · diag4 · FACTS (read-only diagnose log)

Workspace `D:/Temp/opencode/r67gate/diag4`. Repo `F:/Downloads/pythoncdc-main` untouched.
Batch: `IQCommon/util/trade_info_utils.pyc` (38/40), `IQCommon/util/fileio_utils.pyc` (12/14),
`IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` (11/12).

## Step 1/2 — CANDIDATE A (landed): realtime_event_source::get_one_event strict seq_len

### 1. Normalized hunk table (`nhunks.py`, jumps→J, code consts→CODEOBJ)
```
python -X utf8 nhunks.py <realtime.pyc> build_landed/..._realtime_event_sourceOK.py get_one_event --ctx=2
# realtime_event_source.pyc :: get_one_event   orig=22 decomp=23  substantive-hunks=2
HUNK replace  orig[17:18]@82(1) decomp[17:18]@82(1)
     80 POP_EXCEPT | orig:  82 JUMP_BACKWARD to 2     | decomp: 82 JUMP_FORWARD to 92
HUNK insert   orig[22:22]@90(0) decomp[22:23]@92(1)
                                        decomp: 92 JUMP_BACKWARD to 4
```
⇒ **NOT missing statements**: one statement class is mis-emitted. Strict ruler sees
`seq_len orig=19 decomp=20` (NOP/CACHE filtered), official ruler already counts it matched
(`pass` and `continue` differ only in jump edges + 1 shared tail block).

### 2. Attribution on LANDED bytes
CFG/region reading of the landed analyzer (`bdisp.py`, `regprobe.py`):
```
B80 role=BlockRole.LOOP_BACK_EDGE lh=False succ=[2] preds=[78]   POP_EXCEPT@80 | JUMP_BACKWARD@82 -> 2
LOOP entry=2 header=2 cond=None back_edge=80 body=[2,6,60,78,80] exit=None ; header instrs=[NOP@2,NOP@4]
TRY  entry=6 try=[6,58] handler_entries=[60]  handler[0]=('Empty',None,blocks=[78,80]) cleanup=[84,86]
```
`core/cfg/region_ast_generator.py` (line numbers re-grepped on landed bytes):
* L25773-25775 handler-body loop: `_hb_role = self.region_analyzer.get_block_role(hb)` /
  `if _hb_role in (BlockRole.CONTINUE, BlockRole.PURE_CONTINUE):` — a **LOOP_BACK_EDGE**
  handler tail is *not* covered, so it drops to `_generate_handler_body_statements(hb)`
  (L25812), which filters POP_EXCEPT+JUMP_BACKWARD to nothing.
* L25861 `'body': handler_body if handler_body else [{'type': 'Pass'}]` — the empty handler
  body is then filled with `pass`. **That `pass` is the defect.**
* The guard that *suppresses* the sibling case is `_handler_backedge_is_natural_loop_iteration`
  (L19857, called from L25787) — it only ever sees CONTINUE/PURE_CONTINUE roles, and it is the
  R32 note "for-loop implicit iteration" case. My predicate is disjoint from it (see 4).
* L26644 `[R66-diag5-B try-tail-unprotected-else]` is a *try-body tail* rule; mine folds in the
  **handler body**, one level deeper, and never rewrites a try tail Expr into a Return.

### 3. CPython-side proof that the shape is decidable (probe `probe/b.py`, `probe/a.py`)
```
while True: try: return g() except E: pass      -> POP_EXCEPT ; JUMP_FORWARD  to <loop-tail>   (+ JUMP_BACKWARD to 4)
while True: try: return g() except E: continue  -> POP_EXCEPT ; JUMP_BACKWARD to 2  (header)
while cond: try: return g() except E: pass      -> POP_EXCEPT ; JUMP_FORWARD  to <retest block>
while cond: try: return g() except E: continue  -> POP_EXCEPT ; JUMP_BACKWARD to 2  (header)
for ...:    try: g()           except E: pass/continue -> identical bytes (both forms)
```
⇒ an *unconditional backward* edge out of a handler tail can only come from an explicit
`continue`; `pass` always leaves the try statement *forward* into the loop's own tail block.

### 4. Synth repro (`synth/r67d4_handler_continue.py`, 15 lines → `synth/r67d4_handler_continue.pyc`,
list `synth/r67d4.txt`)
```
python -X utf8 h62.py run  --arm=landed --list=synth/r67d4.txt --out=dump/landed_synth.jsonl
python -X utf8 sstrict.py build_landed synth/r67d4.txt
landed r67d4_handler_continue.pyc 4/4 official ; strict 3/4 -> <module>.s1 [seq_len] orig=15 decomp=16
landed r67d4_controls.pyc         7/8 official ; strict 7/8 -> c3_cont_cond [seq_len] orig=20 decomp=21
```
nhunks on s1 reproduces get_one_event **exactly** (orig `JUMP_BACKWARD to 2` vs
decomp `JUMP_FORWARD to 66` + inserted `JUMP_BACKWARD to 4`).
Controls file `synth/r67d4_controls.py` covers the 5 adjacent shapes (`c1 pass/while-True`,
`c2 pass/while-cond`, `c3 continue/while-cond`, `c4 continue/for`, `c5 continue/while-True
non-returning try`) — all officially matched except c3, which is the R34 `while cond`→
`while True: if not cond: break` family, deliberately left out of scope.

## Step 4 — SPEC: `specs/cand_r67_handler_continue.json`
`[R67-diag4-A try-handler-backedge-explicit-continue]`, file `core/cfg/region_ast_generator.py`,
2 edits, each anchor `count==1` in the LF-normalised landed text (verified by `find_anchor.py`:
chars 1080882/L19899 and 1409446/L25774).
* edit 1 inserts `_handler_backedge_is_explicit_continue` (3-part 识别条件/归约方式/AST 映射 comment).
* edit 2 adds one branch before the CONTINUE/PURE_CONTINUE test at L25774.
Predicate inputs are all same-level block/edge fields: `region_analyzer.get_block_role(hb)`,
`hb.get_last_instruction()` + its `argval` target block, `self._current_loop.header_block`,
`self._current_loop.back_edge_block is hb`, per-block instruction purity
(RESUME/NOP/CACHE/PUSH_NULL/POP_TOP/POP_EXCEPT/COPY before the terminator), and the
already-empty `handler_body`. No function/file/offset/threshold, no cross-region containment,
no new `self` state, nothing suppressed (it *adds* the missing `continue` statement).

### first-build correction (recorded because the first measurement was negative)
Build #1 with `any(i.opname not in noise for i in hb.instructions)` returned False: the block's
own terminator `JUMP_BACKWARD` counted as "dirty" (instrumented reading
`{'hb': 54, 'role': LOOP_BACK_EDGE, 'hdr': 2, 'back_edge': 54, 'tgt': 2, 'dirty': ['JUMP_BACKWARD'], 'res': False}`
via `dbg_hc.py`). Fixed to `hb.instructions[:-1]`. **Do not trust a negative A/B before tracing
the gate** — the shape itself was already confirmed reachable by `dbg_hc.py`.

## Step 5 — measurements of `--arm=hcand` (fresh dumps, products under `build_hcand/`)
```
targets  official: trade_info 38/40 | fileio 12/14 | realtime 11/12  (unchanged - get_one_event
                   was never an official defect)
targets  strict  : trade_info 36/41 | fileio 13/15 | realtime 10/12 -> 11/12   (get_one_event cleared)
battery        : matched 115/127, 7 defect files  == landed baseline
canary         : 143/143, 10/10, 26/26, 25/25
synth  s1      : strict 15/16 -> CLEAN (4/4);  controls: c3 seq_len(20/21) -> c3 seq_diff#3
                 (POP_JUMP_IF_FALSE vs POP_JUMP_IF_TRUE, counts now equal 20/20, still 1 defect)
ab targets : SAME=2 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0   (MOVED = realtime sha changed,
             mismatch list gained=[] lost=[] -> gain is strictly on the strict ruler)
ab battery : SAME=31 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0  (all 31 products byte-identical)
ab canary  : SAME=4  IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0  (4 canary shas byte-identical)
```
Canary shas under hcand: `4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177`
— identical to landed, byte for byte.


## Step 0 — baseline replay on `--arm=landed`   (appended first, kept LAST in this file; read it first)


Commands (each < 300 s, wall times ~15/40/60 s):
```
python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed_targets.jsonl
python -X utf8 h62.py run --arm=landed --list=battery.txt --out=dump/landed_battery.jsonl
python -X utf8 h62.py run --arm=landed --list=canary.txt --out=dump/landed_canary.jsonl
python -X utf8 cstrict.py build_landed targets.txt dump/landed_strict.json
python -X utf8 tally.py landed
```

**REPLAY VERDICT: every reading matches the brief byte-for-value. No stop-condition.**

| file | official | mismatches (name, orig, decomp, jump_diffs, true_diffs) |
|---|---|---|
| trade_info_utils.pyc | 38/40 | get_trade_list 339/323 h14 fd148; trade_operation 304/302 h2 fd40 |
| fileio_utils.pyc | 12/14 | acquire 96/93 h3 fd52; write 637/637 h4 fd519 |
| realtime_event_source.pyc | 11/12 | clock_worker 1275/1286 h10 fd481 |

Battery landed: **matched 115/127**, 7 defect files, 31 items — identical list to brief
(probe_r63b2_cases 7/9, probe_r63b2_cases2 7/9, r63b5_w1 1/2, r64d5_contsink 1/2,
r65_trytail 8/9, fs2 6/10, r66d3_pred 2/3; all others full).

Canary landed shas (must stay byte-identical):
```
quotation.pyc        143/143  sha=4d41187e356544e0
market_time.pyc       10/10   sha=af77224b34b203c4
datetime_func.pyc     26/26   sha=e711b8ea86d49a15
datetime_func.pyc     25/25   sha=9d09af09249da177
```

Strict landed: trade_info_utils 36/41 (5 defects), fileio_utils 13/15 (2), realtime 10/12 (2) —
all five strict readings reproduce `targets.md` exactly (get_trade_list 345/329, get_trade_status
target_diff #70 FOR_ITER, get_trade_unit_info 240/241, set_trade_status target_diff #113 JUMP,
trade_operation 304/302; FileIO.write seq_diff #42 ('None','LOAD_CONST') vs ('<JUMP>','JUMP'),
FileLock.acquire 98/93; clock_worker 1276/1287, get_one_event 19/20). missing=0 extra=0 everywhere.

Products for step 1 live in `build_landed/`:
`IQCommon__util__trade_info_utilsOK.py`, `IQCommon__util__fileio_utilsOK.py`,
`IQEngine__plugins__plugin_system_event_source__realtime_event_sourceOK.py`.

### Methodology hazard found while reading nhunks tables (correction for the whole effort)
`nhunks.py` normalises jump **arguments** to `J` but **not** the `EXTENDED_ARG` prefix
instruction, so a 1-instruction `delete` hunk sitting immediately before a `JUMP_*`
is *relocation noise*, not a defect. This accounts for `set_trade_status` (1 delete @598
right before `JUMP_BACKWARD`) and 2 of `get_trade_list`'s 4 hunks (@1326, @1404, both
before `JUMP_BACKWARD to 814`). Do not chase those.

## Step 1/2 — remaining residuals of the batch (all measured, none landable this round)

### `trade_info_utils::get_trade_list`  (official 339/323, strict 345/329)
4 normalized hunks, all `delete`: **12 instrs @888, 6 instrs @1056** (real) + 2 EXTENDED_ARG
noise. The two real ones are dropped `and`-chain members of elif conditions:
```
B836 LOAD_FAST item; 'status'; BINARY_SUBSCR; '2'; COMPARE_OP != ; POP_JUMP_FORWARD_IF_FALSE 1010
B860 LOAD_FAST op_station            ; POP_JUMP_FORWARD_IF_FALSE 888      <- nested short-circuit
B864 item['op_station']==op_station  ; POP_JUMP_FORWARD_IF_FALSE 1010     BoolOpRegion@864 blocks=[864,888]
B888 item['strategyType'] in list(CUSTOM_STRATEGY_TYPE_DICT.values()) ; POP_JUMP..._FALSE 1010   <-- DELETED
B968 trades.append(item)
```
The landed product emits `if item['status'] != '2' and (op_station and item['op_station']==op_station):`
and simply **loses member B888** (`grep` of the product for `CUSTOM_STRATEGY_TYPE_DICT.values()`
and `== COMMON_STRATEGY_TYPE` inside `get_trade_list` → 0 hits, both dropped members).
Attribution (landed bytes): the elif-chain fold in `core/cfg/region_analyzer.py`
`_main_inline_boolop_chain` walk L16733-16780 (incl. the `[P1-1a 链成员纯净性]` gate L16756-16770,
which `break`s the walk on STORE_*/POP_TOP members) — a member reached *through* a single-instruction
short-circuit block whose false edge points at the *next member* (B860 → 888) is cut off the chain,
and `_generate_boolop` then rebuilds only the surviving prefix.
**候选：NONE (this round)** — this is statement *loss*, needs a chain-completeness predicate in the
analyzer, and the same elif-chain area still carries the 4 open battery defects
(`probe_r63b2_cases` c6/c8, `probe_r63b2_cases2` d2/d8) ⇒ one-spec-per-agent + 402 sweep is the
centre's, so it cannot be safely attempted beside candidate A. **R68 lead, with the block/region
readings above.**

### `trade_info_utils::trade_operation` (official 304/302, strict 304/302)
Single hunk: orig `1464 LOAD_CONST None; 1466 RETURN_VALUE` missing. Landed CFG:
```
B1442 role=NORMAL      succ=[1448,1450,1456] preds=<28 blocks>   PUSH_EXC_INFO|WITH_EXCEPT_START|POP_JUMP_FORWARD_IF_TRUE 1456
B1456 role=TRY_BODY    succ=[1450,1458]                          POP_TOP           (with __exit__ suppressed the exception)
B1464 role=TRY_BODY    succ=[] preds=[1458]                      LOAD_CONST None | RETURN_VALUE
B1468 role=TRY_BODY    succ=[1522,1526] preds=[350]              app_log.warning('...文件不存在...')
```
⇒ the *exception-suppressed* with-cleanup path resumes at a **duplicated inline tail**
(`return None`) while the normal path (B1416 → `1438 LOAD_CONST False; RETURN_VALUE`) resumes at
`return False`; the decompiler shares one tail and falls the suppressed path into B1468.
This is precisely the try/with-body JUMP_FORWARD family (`fileio_utils::write` HUNK1/2 show the
identical shape: orig inlines `NOP; LOAD_CONST None×3; PRECALL; CALL; POP_TOP; LOAD_CONST True;
RETURN_VALUE` @206, decomp emits `EXTENDED_ARG; JUMP_FORWARD to 778` and re-materialises that copy
@776-804). R66 already returned **候选：NONE** for the twin `write`, and the family's other twin
`wizard_quant_api::params_analysis` [133,126,1,117] is still open in the centre's corpus.
**候选：NONE (this round)** — measured reason: any fix must *duplicate* a cleanup tail per exit
path (a scheduler change in `region_analyzer`), which is orthogonal to and unproven beside the
R66-diag5-B try-tail rule at generator L26644; it also collides with the on-record hazard
"rewrite a try tail → a downstream guard deletes the whole Try".

### `fileio_utils::FileLock.acquire` (official 96/93, strict 98/93)
3 hunks: decomp **inserts** `JUMP_FORWARD to 354` + `time.sleep(self.delay)` @302-352 and
**deletes** the 12-instr orig block @532-590 (`time.sleep` + `POP_EXCEPT; LOAD_CONST None;
STORE_FAST e; DELETE_FAST e; JUMP_FORWARD to 608`) + deletes `EXTENDED_ARG; JUMP_BACKWARD to 42`
@608. So one `sleep` copy is *relocated* to the wrong exit path and the `except Exception as e:`
re-raise tail is folded: same cleanup-tail family as `write`, plus a real missing `del e` scope
cleanup. Not attemptable beside candidate A under the one-spec rule. **候选：NONE (this round).**

### `realtime_event_source::clock_worker` (official 1275/1286, strict 1276/1287)
14 hunk table: dominated by `delete orig[1192:1304]@7972 (112 instrs)` paired with
`insert decomp[1274:1409]@8404 (135 instrs)` and `replace orig[1097:1110]@7492(13) → (2)`: one
large handler/loop block is emitted ~400 bytes later than the original schedules it, plus the
`replace` shows the shared `for…else`/loop-then ambiguity of this R34 family. Per the brief this
file may not be re-attacked from else-ownership edges without a different-level predicate +
repro; candidate A is that different level (handler tail), and it cleared only `get_one_event`.
**clock_worker: 候选：NONE (this round).**

### Strict-only target_diffs `get_trade_status` (#70 FOR_ITER) / `set_trade_status` (#113 JUMP)
`nhunks` after jump-arg normalisation: **0 substantive hunks** (get_trade_status) and 1 EXTENDED_ARG
artifact (set_trade_status) — i.e. identical streams whose *loop/branch target instruction* differs
(`'return_trade_info'` vs `'count'`, `'count'` vs `'exchange_flag'`): the payload blocks are the
same, only the resolved jump target block is off by one test. `get_trade_unit_info` 273/274 is the
same-shape tail-scheduling pair (replace @1340 + insert @1402). **候选：NONE (this round)** — a
target-resolution predicate needs the 402-corpus reading of `chained-compare`/`value-context`
gates (analyzer L20949), which only the centre can measure.

## Verdicts
| target | verdict |
|---|---|
| realtime_event_source::get_one_event | **CANDIDATE A landed-spec** `specs/cand_r67_handler_continue.json`, strict 10/12→11/12, zero regressions |
| realtime_event_source::clock_worker | 候选：NONE (R34 loop-else family, readings above) |
| trade_info_utils::get_trade_list | 候选：NONE (dropped `and`-chain members; R68 lead with region readings) |
| trade_info_utils::trade_operation | 候选：NONE (with-cleanup duplicated-tail family, twin of `write`) |
| trade_info_utils::{get_trade_status,set_trade_status,get_trade_unit_info} | 候选：NONE (jump-target / tail-schedule, 0 real hunks) |
| fileio_utils::write, acquire | 候选：NONE (same cleanup-tail family; `write` already NONE in R66, no new entry found) |

## Brief corrections
* `targets.md`, `battery.txt` (31 items = 115/127) and the 4 canary shas all replayed exactly —
  no stop-condition triggered.
* `cstrict.py` cannot pair *scratch* pyc paths (it only resolves names after `site-packages/`, so
  `test_repros/...` works and `D:/.../synth/...` yields NO-PRODUCT). Added `sstrict.py` (same ruler,
  h62-compatible product naming) to strict-measure the synth repro; it is the only way to score
  synth files on the strict ruler.
* `nhunks.py` leaves `EXTENDED_ARG` un-normalised → 1-instr delete hunks before jumps are noise
  (see the hazard note above). `regdump.py`'s FIELDS lack `handler_entry_blocks` /
  `except_handlers`, so a try region prints as if it had no handlers; added `regprobe.py`.
* The strict ruler is the ruler that sees the `get_one_event` class of defect: the **official**
  ruler counts `get_one_event` as *matched* (11/12 with only `clock_worker` open), so an
  official-only A/B shows `MOVED` (sha changed, mismatch list unchanged) for candidate A. Any
  future brief line that lists a function under STRICT only should still be treated as in scope.


