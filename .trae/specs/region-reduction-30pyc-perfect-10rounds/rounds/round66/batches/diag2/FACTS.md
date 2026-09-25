# Round 66 · diag2 · FACTS (read-only diagnosis)

Nothing was written inside `F:\Downloads\pythoncdc-main` (no `core/`, no `*OK.py`,
no `pyc_index.json`, no `.trae/`); every artefact lives in
`D:/Temp/opencode/r66gate/diag2`. All commands `python -X utf8`, no
`PYTHONIOENCODING`.

## Step 0 — baseline re-read (arm=landed), all reproduce brief exactly

`dump/landed.jsonl`, `dump/battery_landed.jsonl`, `dump/canary_landed.jsonl`.

targets `site-packages/fly/data/quote.pyc` = **70/81**, sha `9573f1767596ff7b`, mism =
[["build_current_period_df",115,108,5,12],["check_frequency",121,120,1,21],["check_limit",330,311,2,248],
["get_individual_data",312,311,1,156],["get_price",230,228,0,224],["get_real_from_zeromq",703,678,0,660],
["initImagedata",243,225,0,190],["load_bars_from_hundsun",477,524,3,507],["load_get_price",171,167,2,164],
["run_individual_transform",362,321,2,263],["run_tick_socket",306,307,2,228]] -> identical to brief.

canary 4/4 shas identical to brief:
quotation.pyc 143/143 sha=4d41187e356544e0 ; market_time.pyc 10/10 sha=af77224b34b203c4 ;
datetime_func.pyc 26/26 sha=e711b8ea86d49a15 ; datetime_func.pyc 25/25 sha=9d09af09249da177.

battery 24 items = 91/104, each line identical to the brief table (fs2 5/10 with
v1/v3/v6/v7/v8, fsrepro 6/7 with m_b 39/35). No drift => the round starts on the
bytes the brief describes.

## 1. Normalized substantive-hunk tables (`nhunks.py`, C1 3.11 instruction level)

### 1a. quote.pyc — 11 residual functions, arm=landed (`dump/hunks_quote_landed.txt`)

| function | orig/decomp instr | hunks | hunk addresses (orig[lo:hi]@off / decomp[lo:hi]@off) |
|---|---|---|---|
| build_current_period_df | 124/113 | 2 | replace@…, insert@… (except-path join, R64 family) |
| check_frequency | 132/133 | 2 | 1 extra branch arg pair (relocation-neutralised) |
| check_limit | 356/334 | 1 | delete 22 instr (loop-else loss) |
| get_individual_data | 354/354 | 4 | 4 replaces (f-string prefix shredding + call flattening) |
| get_price | 256/254 | 3 | replace@46 (f-string prefix), delete@54 (BUILD_SLICE/BINARY_SUBSCR), insert (dup group) |
| get_real_from_zeromq | 793/767 | 8 | zeromq try/except per-exit tails (R64 family) |
| initImagedata | 273/251 | 1 | delete 22 instr |
| **load_bars_from_hundsun** | **526/580** | 3 | `replace orig[5:8]@46(3) decomp[5:6]@46(1)`; `delete orig[9:11]@54(2)`; **`insert orig[49:49]@256(0) decomp[45:103]@242(58)`** |
| load_get_price | 185/181 | 3 | same trio as load_bars (prefix shred + slice + dup insert) |
| run_individual_transform | 412/359 | 11 | boolop/stmt-steal family |
| run_tick_socket | 347/348 | 4 | socket loop |

The **headline hunk** of this round is the third one of `load_bars_from_hundsun`:
a *58-instruction pure insertion* at decomp offset 242 with **no orig counterpart**
(`orig[49:49]@256(0)`), i.e. 58 instructions that exist in the product and nowhere
in the original code object. The same shape appears in `load_get_price` and
`get_price` (the three prologue-log functions of this module).

### 1b. quote.pyc — `load_bars_from_hundsun` under candidate p4 (`dump/hunks_quote_p4.txt`)

```
# quote.pyc :: load_bars_from_hundsun   orig=526 decomp=529  substantive-hunks=3
HUNK replace  orig[5:8]@46(3) decomp[5:6]@46(1)
        46 LOAD_CONST    '调用函数load_bars_from_hundsun，参数为：stocks='
        48 LOAD_FAST     stocks            <-- 48 LOAD_CONST None 50 LOAD_CONST 10
        50 LOAD_CONST    None              <-- 46 LOAD_CONST '…stocks=stocksNone'
HUNK delete   orig[9:11]@54(2) decomp[7:7]@48(0)
        54 BUILD_SLICE   / 56 BINARY_SUBSCR      (deleted: `stocks[:10]`)
HUNK insert   orig[49:49]@256(0) decomp[45:52]@242(7)   <-- was 58 instructions
```
p4 collapses the pure insertion 58 -> 7 instructions (the residual 7 are
`os.path.exists(DumploadDailyFile)` emitted as a bare `Expr`, a different,
pre-existing defect) and the two interpolation hunks stay — they are candidate p3's
territory (§3).

### 1c. fs2.pyc / fsrepro.pyc, arm=landed (`dump/hunks_fs2_landed.txt`)

| fn | orig/decomp | hunks | shape |
|---|---|---|---|
| v1 | 13/11 | 1 | `delete orig[10:12]@20(2)` — FORMAT_VALUE/POP_TOP tail lost |
| v3 | 16/11 | 2 | `replace orig[1:3]@2(2)` + `delete orig[11:15]@32(4)` — callee `print` leaked as a literal part (bare `Name`, not `Attribute`) |
| v6 | 15/11 | 1 | `delete orig[10:14]@20(4)` |
| v7 | 25/25 | 1 | `replace orig[8:9]@44(1) decomp[8:9]@44(1)` — one wrong part |
| v8 | 34/24 | 3 | `replace orig[5:8]@46(3)` + `delete orig[9:11]@54(2)` + `replace orig[19:26]@82(7) decomp[15:16]@66(1)` — prefix shredding of `a[:1]`-style interpolation operands |
| fsrepro m_b | 43/39 | 2 | `replace orig[5:8]@46(3)` + `delete orig[9:11]@54(2)` — identical to the first two hunks of v8 / load_bars |

**Measured correction to the brief's premise**: the *duplication* is **not** present
in fs2. `probe_disc.py` recorded **0 calls** to
`_generate_chain_head_prefix_assign` for fs2, fsrepro, **all 24 battery files** and
the 3 synthetic files — the only file in the whole measured set that calls it is
`quote.pyc` (exactly 1 call, and its result is the duplicated group). So
"fix the duplication ⇒ fs2 10/10" cannot hold: fs2's five residuals are the
prefix-scan families of §3, whose fix is p3 (and, for v3, p1).

## 2. Attribution on current landed bytes (`grep -n` on `F:/Downloads/pythoncdc-main/core/cfg/region_ast_generator.py`, 50409 lines, CRLF+BOM)

| site | bytes now | role |
|---|---|---|
| `34646 def _generate_ternary` | — | f-string/ternary statement generator |
| `36060 elif merge_ctx == 'fstring':` | — | the flattened-f-string statement branch |
| `36121-36143 [R65-d3 C1a]` | callee skip, gated on `self._ternary_pending_callee(cond_block)` | v3 (bare-Name callee) leaks `print` as a part |
| `36144-36179` prefix scan | `for pi in _prefix_instrs: if pi.opname.startswith('LOAD_'): reconstruct([pi]) … elif FORMAT_VALUE … elif LOAD_CONST` then `36180? fstring_parts = _stack` | **pushes one part per single LOAD_***: `stocks`/`None`/`{10}` from `stocks[:10]` → the two hunks of §1b/§1c |
| `36193-36249 [R65-d3 C1b]` | merge-tail segment reduction via `_fstring_parts_from_segment` (def `41294`) | the *same-level* reduction the prefix scan never got |
| `36250-36253` | `joined_str = {'type':'JoinedStr','values':fstring_parts}` | |
| `36254-36267 [R65-d3 C1c]` | `_r65_stmt = self._try_wrap_fstring_pending_call(...)` (def `41458`), `results.append`, `results.extend(_r65_post)`, mark `region.blocks` generated, **`return results`** | marks blocks + returns **without** registering the region itself |
| `16949 def _generate_chain_head_prefix_assign` | owner loop `16979-16990`: skips `not isinstance(_r,(BoolOpRegion,TernaryRegion))`, `merge_block is not head_block`, `id(_r) in self._generated_regions`, `id(_r) in self._generating_regions`, `BoolOpRegion and not _r.value_target`; `_res = self._generate_ternary(_owner)` at `16998`; keeps every leading non-`If` statement | **the duplication source** |
| `17577` (inside `_if_generate_normal`, def `17290`) | `_disc_pre = self._generate_chain_head_prefix_assign(_d_cb)` / `pre_stmts.extend(_disc_pre)`, sole call site, reached from `_generate_region:3184 <- _generate_if:11630` | splices the group a second time |

### Duplication mechanism — proven, three independent measurements

1. **Emission ledger** (`probe_ledger.py --mark=调用函数load_bars_from_hundsun`,
   `logs/ledger_quote.txt`): 4 records, **2 duplicate AST dicts**
   (`***SAME-DICT-AS-#0***`). #0/#1 come from the prologue walk
   (`… <- _generate_region:3305 <- _generate_ternary:36258`); #2/#3 come from
   `_generate_region:3184 <- _generate_if:11630 <- _if_generate_normal:17577 <-
   _generate_chain_head_prefix_assign:16998 <- _generate_ternary:36258`. The very
   same 4 statements (`Expr(self.log.quote.debug(…))`, `data=`, `retpanel=`,
   `Expr(os.path.exists(…))`) are spliced into the `If`'s `pre_stmts`.
2. **Owner state snapshot** (`probe_disc.py`, pure pass-through wrapper, `logs/disc_quote2.txt`):
   `PRE  TernaryRegion ctx=fstring mask=GGGG allblk_gen=True gen_id=False`
   `POST … mask=GGGG allblk_gen=True gen_id=True`.
   So at the moment the chain-head loop considers the region, **all four of its
   blocks are already in `self.generated_blocks`** (they were marked by the first
   emission, `[R65-d3 C1c]` at `36254-36267`), while the loop's only
   "already claimed" guards look at `id(region)` in `_generated_regions`
   (`gen_id=False` — the C1c early `return results` never registers the region).
   That asymmetry is the whole defect: block-level claim vs region-id-level guard.
3. **Ablation**: a wrapper that raises before returning (so
   `except Exception: _res = None` at `16999-17000` swallows it and `out` stays
   empty) makes the second copy vanish: product marker count 2 -> 1. A *pure*
   pass-through wrapper leaves 2, so it is the chain-head result that duplicates,
   not the wrapper's presence.

**Synthetic repro: attempted twice, does not reproduce** (`synth/r66p4.py`, 7 and 8
lines: f-string-with-ternary prologue statement, two stores, `if d and …:` /
`if d.exists() and …:`). Both variants stay 1/2 (defects elsewhere: callee leak +
`if …: pass`) and byte-identical under p4 — the fallback chain discovery at
`17543` only reaches the sharing pattern when the merge block also carries the
module-level names/call shape of quote's prologue. Evidence above (hunk 58->7,
ledger SAME-DICT pair, PRE mask=GGGG) is therefore reported instead of a synthetic;
`build_landed` vs `build_p4` diff on quote is exactly the 4 duplicate lines
(`@@ -384,10 +384,6 @@`), nothing else.

## 3. Candidate p3 — prefix scan reduced with the existing same-level helper

`quarantine/hold_r66_p3_prefixparts.json` (fully measured, **not submitted** this
round because p4 attacks the brief's named #1 cost; single anchor, 1 edit, build
`mirrors built: … cand patched (1 edits, … BOM=True, nl=CRLF)`).
Anchor: the unique line `                    fstring_parts = _stack\n`
(count==1 in LF-normalised bytes). Patch only *appends*: re-slice
`cond_block_instrs[_r65_callee_skip:cond_val_start]`, cut at every `FORMAT_VALUE`,
reduce each complete group with the existing
`self._fstring_parts_from_segment(seg, fv_instr)` (def `41294`, the same helper
`[R65-d3 C1b]` already uses for merge-tail segments); a single `None` (unexplainable
group)退回改前结果, so no new escape hatch; the unchanged per-`LOAD_*` scan still
owns the trailing incomplete group. Three-part comment (识别条件/归约方式/AST 映射)
in the patch; no names, offsets, thresholds or cross-region containment.

## 4. Candidates measured and rejected / not submitted

* **p2a `storeepi`** (`merge_ctx=='fstring'` store-epilogue): **produced zero change**.
  Premise wrong — `region.value_target` is the sentinel `'__fstring_target__'` for
  *every* f-string ternary (printed from the instrumented mirror `mirr_head`); the
  store name exists only in the merge block's `STORE_*` `argval`. Rejected; the JSON
  was deleted, the builder kept as `mk_spec_p2.py`.
* **p1 `namecallee`** (`_ternary_pending_callee`, tail `41438-41456`, only returns a
  callee when `_expr['type'] == 'Attribute'`): widening to bare `Name` gives
  fs2 5/10 -> **6/10** (v3 matched), battery 91 -> **92/104**, canary shas identical,
  quote sha unchanged (`9573f1767596ff7b`, i.e. provably inert on the batch file).
  Kept in `quarantine/` — it does not touch the duplication, and one round submits one spec.
* **p3** numbers are in §5; kept in `quarantine/` because p4 attacks the brief's
  named #1 cost. p3 and p4 use disjoint anchors and are additive; next round should
  land p3 on top of p4 (`load_bars_from_hundsun` would then lose the remaining
  `replace@46` + `delete@54` hunks too).

## 5. Submitted candidate: `specs/cand_r66_p4_chainhead_owner.json` (arm `p4`)

One file, one anchor, anchor
`            if isinstance(_r, BoolOpRegion) and not _r.value_target:\n                continue\n`
count==1 in LF-normalised text; build verified:
`mirrors built: head pristine == worktree bytes, cand patched (1 edits, core/cfg/region_ast_generator.py, BOM=True, nl=CRLF)`.
Edit = 19 appended lines (16 comment + 3 code) inside the owner loop of
`_generate_chain_head_prefix_assign`: skip a candidate expression region when **its
own `blocks` are all already registered in `self.generated_blocks`** — the same
"already claimed ⇒ do not re-own" invariant the loop already applies to
`_generated_regions` / `_generating_regions`, read only from the region itself. Not
a name/offset/threshold rule, not cross-region containment, and not a suppression
rule: the region's first emission (prologue walk) is untouched, only the second
claim is refused.

### A/B readings (vs step-0 baselines, `h62.py ab`)

targets (`dump/landed.jsonl` vs `dump/targets_p4.jsonl`):
```
MOVED quote.pyc  lost=[['load_bars_from_hundsun',477,524,3,507]]
                 gained=[['load_bars_from_hundsun',477,479,0,471]]
TALLY SAME=0 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0   (70/81 -> 70/81, sha 9573f1767596ff7b -> 24a…)
```
R65's only measured cost is reversed: the log statement occurs **once**
(`grep -c 调用函数load_bars_from_hundsun，参数为：stocks=` -> 2 landed / **1 p4**),
instruction length 580 -> 529 against orig 526, the `missing` counter 3 -> **0**,
and the other 10 residual functions byte-identical to baseline.

battery (`dump/battery_landed.jsonl` vs `dump/battery_p4.jsonl`):
```
TALLY SAME=24 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0   91/104 -> 91/104 (fully matched 17 -> 17)
```
canary (`dump/canary_landed.jsonl` vs `dump/canary_p4.jsonl`):
```
TALLY SAME=4 REGRESSION=0   shas p4 = 4d41187e356544e0 af77224b34b203c4 e711b8ea86d49a15 9d09af09249da177
```
all four **byte-identical** to the brief. synth list unchanged (`fs2 5/10`,
`fsrepro 6/7`, `r66p1 2/5`, `r66p4 1/2`) — consistent with 0 chain-head calls there.

### Forthcoming: 402-file corpus A/B (`--nshard=4 --shard=0..3`)
`dump/c402_landed.jsonl` / `dump/c402_p4.jsonl`, logs `logs/c402_*.log`; the guard
can only matter where the sole call site fires, so the run is a false-positive
sweep. Result appended below when the shards finish.
