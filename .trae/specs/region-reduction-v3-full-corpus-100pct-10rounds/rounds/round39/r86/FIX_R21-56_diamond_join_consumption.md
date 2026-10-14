# FIX_R21-56 — the diamond-join pair's collateral: attribution corrected, consumption conjunct added

Ticket **R21-56** (spec `region-reduction-v3-full-corpus-100pct-10rounds`, round 39 follow-up).
Target: keep the `_process_order` flip of the banked r85a+r85c pair and remove the collateral on
`IQCommon/util/replace_utils.pyc`.
Working mirror `D:/Temp/r86` (gate-38 landed bytes copied from the read-only repo; repo never written).

## §0 Mirror certification (measured, not copied)

```
core/cfg/region_ast_generator.py  sha16=11324f276cce6d5b  bytes=3846610   (brief: 11324f276cce6d5b OK)
core/cfg/region_analyzer.py       sha16=f7d849e974904492  bytes=2104888   (brief: f7d849e974904492 OK)
python 3.11.7 ; repo `git status --porcelain -- core/ scripts/ parsers/ utils/ bytecode/ pycdc.py site-packages/` = 0 lines
```

Products regenerated with `python -X utf8 pycdc.py --region -o <out> <abs pyc>` after deleting the old output.

## §1 PREMISE RE-MEASUREMENT — the brief's attribution is INVERTED (measured 4-way, not reasoned)

Brief claimed: "A alone causes it: with only A installed in my mirror, `replace_utils` judges 8/9.
The generator half C is exonerated."

I measured all four combinations, byte-hashing both products:

| variant | ana sha16 | gen sha16 | broker product | broker judge | replace_utils product | replace_utils judge |
|---|---|---|---|---|---|---|
| base (landed) | `f7d849e974904492` | `11324f276cce6d5b` | `a6d6deb78a5a5eac` 179259 B | `units=126/128` (`_process_order`, `_sync_worker` Different control flow) | `6863a9f709e6ccef` 13501 B | **`units=9/9` status=success** |
| A alone | `842e2748bcdfeb66` | `11324f276cce6d5b` | `9221e0d00361b40d` 178383 B | `units=126/128` | `6863a9f709e6ccef` = **byte-identical to base** | **`units=9/9`** |
| C alone | `f7d849e974904492` | `45796ca24b371a8c` | `a6d6deb78a5a5eac` = **byte-identical to base** | `units=126/128` | `dc0c24c2ba5003dc` 13521 B | **`units=8/9`** `<module>.decrypt_database_url` Different control flow |
| A+C (pair) | `842e2748bcdfeb66` | `45796ca24b371a8c` | `f25d834a6b0d763e` 179288 B | **`units=127/128`**, only `_sync_worker` failing | `dc0c24c2ba5003dc` (== C alone) | `units=8/9` |

Conclusions, all measured:

1. The broker flip of the pair **is** confirmed (`127/128`, `_process_order` no longer in the failure list).
2. **A does NOT cause the collateral.** With only A installed the `replace_utils` product is
   byte-identical to base and still judges 9/9. The brief's A-alone-8/9 reading must have been taken
   in a mirror that still had C installed.
3. **C alone causes the collateral**, identically to the pair (`dc0c24c2ba5003dc`, `8/9`), and C alone
   leaves the broker byte-identical to base. So the two halves are independent on `replace_utils`
   (A contributes nothing there) and the culprit is the generator half.
4. Consequence for the ticket: the consumption conjunct cannot be placed on A — A has no fire in
   `replace_utils` to refuse. It belongs on the permission C grants, i.e. on the generator half.
   The acceptance bar is unchanged (broker 127/128 **and** `replace_utils` 9/9); the mechanism moves.

## §2 Diagnosis of both collateral sites — opcode class + stack shape, `co_lines()` mapped

`work/dissite.py` (dis + `co_lines()` on the pyc code object), `work/probe_run.py` (+ `work/build_probe_gen.py`,
a probe-patched copy of C that only appends to a module-level list; **probe inertness proven**: with the
probe installed the broker product is still `a6d6deb78a5a5eac` and the `replace_utils` product still
`dc0c24c2ba5003dc`, both byte-identical to C without the probe).

The 3-line text diff (base → C) reproduces the brief exactly:

```
             app_log.info('SM4解密执行完成，解密结果长度: {}'.format(len(decrypted_url) if decrypted_url else 0))
+            decrypted_url
             if not decrypted_url or '://' not in decrypted_url:
-                return url
+                url
```

What the probe says about how those two lines are produced. Both come from
`_generate_host_prefix_ternary_statement`'s **`tail_instrs`** path (`region_ast_generator.py:43389-43391`,
43450-43457): the span registers *every* instruction of the blocks it covers as generated, so the part of
the closing block that lies after the statement's own close must be re-emitted by
`_build_statements_from_instructions(tail_instrs, ...)`.

| site | region | span close | tail (closing block after close) | tail last instr | emitted node types | verdict |
|---|---|---|---|---|---|---|
| 1 | `decrypt_database_url` cond@292 | `POP_TOP` @428 | `LOAD_FAST decrypted_url @430`, `POP_JUMP_FORWARD_IF_FALSE @432` | **conditional jump** | `['Assign','Expr','Expr']` — the last `Expr` is the bare `decrypted_url` | junk |
| 2 | `decrypt_database_url` cond@442 | `POP_TOP` @534 | 27 instrs, `… CALL @670`, `POP_TOP @680`, `LOAD_FAST url @682` | **value producer, its consumer `RETURN_VALUE` is in the next block** | `['Expr','Expr','Expr','Expr']` — the last `Expr` is `url` where the original has `return url` | junk |

Controls from the flip itself (same probe, analyzer A + generator C):

| site | span close | tail | tail last instr | emitted types | verdict |
|---|---|---|---|---|---|
| `_process_order` cond@2092 (fires, one of the six) | `POP_TOP` @2426 | 1 instr `JUMP_FORWARD @2428` | unconditional jump | `['Expr']` | correct |
| `_process_order` cond@2430 (fires) | `POP_TOP` @2690 | 31 instrs ending `PRECALL @2896, CALL @2900, POP_TOP @2910` | `POP_TOP` | `['Expr','Expr','Assign','Expr','Expr']` | correct |
| `etf_purchase_redemption` cond@1856 (canary, no relaxation used) | `POP_TOP` @1960 | `LOAD_CONST @1962, RETURN_VALUE @1964` | `RETURN_VALUE` | `['Expr','Return']` | correct |

So the discriminator is not "is the value consumed" at the merge — both collateral spans do reach a
`POP_TOP` close — it is **whether the leftover the recovery forces itself into the tail is a complete
statement**. When the closing block's tail ends on

  * a conditional jump (site 1) — the tail is the *test of the following region*, not a statement, or
  * a value producer (site 2) — the tail's last value has no consumer inside the tail (its
    `RETURN_VALUE` sits in the next block),

the generic tail builder emits that value as a **bare expression statement**, i.e. exactly the symptom
the brief describes ("a bare expression statement appears where the original emits nothing"; "a RETURN
statement destroyed: value emitted, `return` not"). When the tail ends on a statement-boundary opcode
(`POP_TOP` / `STORE_*` / `RETURN_VALUE` / `RAISE_VARARGS` / unconditional `JUMP_*`) every tail statement
is complete and the render is faithful — which is the case for all six `_process_order` fires.

## §3 The conjunct R21-56 installs (generator half, opcode class / stack shape only)

Candidate `CANDIDATE_r86a_r2156_generator_relax_tail_boundary.py`, sha16 **`b4363f5858e58074`**, built
from the landed bytes by `build_cand_r86a_r2156.py`. The builder applies the [R21-55c] relaxation
verbatim and **self-checks**: the intermediate produced by (1) alone is byte-identical to the banked
`45796ca24b371a8c` (asserted in the builder, printed: `(1) only, sha16 = 45796ca24b371a8c == banked r85c`).
So the delta of my candidate over the banked half is exactly the conjunct.

Inside `_ternary_host_call_prefix_span` (`region_ast_generator.py:43235` in landed bytes):

1. `_r2156_relaxed_used = []` next to `visited = {cond_block}`;
2. `_adopt_arm` records the marker when — and only when — the arm passed the successor test thanks to
   the [R21-55c] exception-entry permission;
3. at the span's exit, before `return span_instrs, all_blocks, prefix_instrs, tail_instrs`:

```python
        if _r2156_relaxed_used and tail_instrs:
            if not self._r2156_tail_is_bounded_statements(tail_instrs):
                return None
```

4. `_r2156_tail_is_bounded_statements(tail_instrs)` — three opcode-class facts, no names, no constants,
   no offsets, no counters, no thresholds:
   * ① no `POP_JUMP_*` / `JUMP_IF_*` anywhere in the tail: a conditional jump whose arms are not in the
     tail means the tail is the **test of the following region**, not a statement (site 1);
   * ② the tail's last instruction must be a statement boundary — `POP_TOP`, `RETURN_VALUE`/`RETURN_CONST`,
     `RAISE_VARARGS`, `STORE_*`, or an unconditional `JUMP_*`: it takes the value off the stack or
     transfers control, so every tail statement is self-contained;
   * ③ anything else (`LOAD_*`, `BUILD_*`, `CALL`, `BINARY_OP`, …) means the value the tail last pushed
     is consumed **in a later block** — and those blocks are already registered as generated, so the
     value is emitted as a bare expression statement and the real statement (`return url`) disappears
     (site 2).

The conjunct narrows **only the new permission**: spans that do not use the relaxation are untouched, so
landed behaviour is byte-preserved by construction. Refusal happens before any block/offset is registered,
so a refused span falls back to the gate-38 render exactly (the same convention as the other guards in
that function).

§11 consistency (the inline-boolop fold rule the brief asked me to cross-check): §11 says a
condition-context fold must refuse to absorb a member block whose value is discarded by `POP_TOP` rather
than consumed by a following `POP_JUMP_*`. Mine is the statement-side dual and they do not contradict:
in a boolean-test chain a `POP_TOP` proves the block ends a statement and therefore does **not** belong
to the condition; in a statement fold a `POP_TOP` **is** the legitimate close of the host call, and the
thing that must be refused is a *leftover* whose value outlives the tail. Both are "value-consumption
class" tests; neither reads names.

**Where the ticket's wording is falsified by the measurement** (rule 6, stated with numbers, not as a
failure): the conjunct as prescribed — "refuse when the value is discarded by `POP_TOP`" — cannot be
installed on this pair. The two host statements that the relaxation takes over in the target unit close
on `POP_TOP` (`cond@2092` close `POP_TOP` @2426, `cond@2430` close `POP_TOP` @2690 — these two spans are
what carries all six analyzer-side join sites `@1634/@2092/@2310/@2236/@2430/@2574`, and `cond@1634`
itself returns no span), and the two collateral statements close on `POP_TOP` too (@428, @534). A
`POP_TOP` veto therefore refuses the flip and the collateral alike; it does not separate them. What does
separate them, with zero overlap, is the tail shape (§2 table): broker's two relaxed spans have
well-formed tails (`JUMP_FORWARD` / `POP_TOP`), `risk_calculation`'s has no tail at all, and both
collateral spans have malformed ones.

## §4 Fire census BEFORE editing (probe, both tiers; probe proven inert)

Probe = `work/build_probe_gen.py` → `work/PROBE_gen_region_ast_generator.py` (sha16 `b1c913613fad84de`),
which only appends to a module-level list. **Inertness measured**: with the probe installed,
broker product `a6d6deb78a5a5eac` and `replace_utils` product `dc0c24c2ba5003dc` — byte-identical to the
same variants without the probe. The conjunct itself was then evaluated read-only in `work/census_tier2.py`.

Tier 1 (`work/census_t1/shard{0..7}.json`, log `work/CENSUS_tier1.log`) — analyzer-only over **406 .pyc**,
8 shards ≤ 60 s each, counting rule stated in the log:
`TernaryRegion` records **349**, relaxation-eligible arm sites **217**, in **20 files**. All other 386 .pyc
have zero eligible sites, i.e. the whole action surface of [R21-55c] — and therefore of my conjunct —
lives in those 20 files.

Tier 2 (`work/census_t2_panel.json`, `work/census_t2_extra.json`, log `work/CENSUS_tier2.log`) — full
pipeline with the probe, over panel-20 **plus** every tier-1 flagged file outside the panel (union 40
runs, 17 unique extra files, `replace_utils` included):

| population | CALLS | FIRED | RELAXED+FIRED | PERMIT | REFUSE |
|---|---|---|---|---|---|
| panel 20 files | 239 | 30 | 9 | 9 | **0** |
| tier-1 flagged outside panel | 428 | 32 | 13 | 9 | **4** |

CALLS/FIRED/… are counted once per code-object pass, and this campaign's copies make three passes see
the same nested code (`<module>`, the class body, the function), so unique relaxed spans are:

* **permitted, 3 unique**: `_process_order` cond@2092 (tail last = `JUMP_FORWARD` @2428) and cond@2430
  (tail last = `POP_TOP` @2910) — reported 6× because the three passes each repeat them; plus
  `risk_calculation._on_collect_handle_data` cond@548 with `tail_n = 0` (the conjunct is vacuous there).
* **refused, 2 unique**: `IQCommon/util/replace_utils.pyc` `<module>.decrypt_database_url` cond@292
  (tail ends `POP_JUMP_FORWARD_IF_FALSE`) and cond@442 (tail ends `LOAD_FAST`) — reported 4× (two passes
  × two sites).

Nothing else in the corpus can be affected: the other 386 .pyc have zero tier-1 eligible arm sites, so
no span can reach the relaxation, and the conjunct guards only the relaxation path. Byte-change census
per fire is §6: the pair changes **1 of 402** products.

The panel's REFUSE=0 row is the point of the new protocol: the 20-file panel is provably blind to this
collateral, exactly as the brief says — it is not a sample of the corpus for this criterion.

## §5 Halves alone + the pair (`work/HALVES.log`, `work/JUDGE_halves.log`)

| variant | ana / gen sha16 | `_process_order` delta / hunks / landings | broker judge | `decrypt_database_url` delta / hunks | replace_utils judge |
|---|---|---|---|---|---|
| base (landed) | `f7d849e974904492` / `11324f276cce6d5b` | `-68 / 14 / 12` | `units=126/128` | `0 / 0` | `units=9/9` success |
| A alone | `842e2748bcdfeb66` / landed | `-97 / 4 / 4` | `units=126/128` | `0 / 0` | `units=9/9` success |
| C alone (r85c) | landed / `45796ca24b371a8c` | `-68 / 14 / 12` (product `a6d6deb7` == base) | `units=126/128` | **+2 / 2** | **`units=8/9`** `_decrypt…` Different control flow |
| **C′ alone (r86a)** | landed / **`b4363f5858e58074`** | `-68 / 14 / 12` (product `a6d6deb7` == base) | `units=126/128` | `0 / 0` (product `6863a9f7` == base) | `units=9/9` success |
| A+C (brief pair) | `842e2748bcdfeb66` / `45796ca24b371a8c` | `0 / 0 / 0` | **`units=127/128`** | **+2 / 2** | `units=8/9` |
| **A+C′ (R21-56 pair)** | `842e2748bcdfeb66` / `b4363f5858e58074` | **`0 / 0 / 0`** `judge_diff=False` | **`units=127/128`**, only `_sync_worker` failing | **`0 / 0`** | **`units=9/9` status=success** |

Broker products: A+C and A+C′ are the **same bytes** `f25d834a6b0d763e` (179288 B) — the conjunct does not
move the flip by one instruction. `replace_utils` under A+C′ is the base bytes `6863a9f709e6ccef`
(13501 B): both emitted bare-expression sites are gone, proven by judging the file, not by reasoning.
Nothing here is the "`|delta| ≤ 3` but judge still Different" shape: the flipped unit is `delta=0 hunks=0
landings=0 judge_diff=False` and the file reads 127/128.

## §6 Corpus-wide collateral sweep (the new pre-gate protocol, 402 products)

`work/sweep.py 250 D:/Temp/r9main/all402_rel.txt out_sweep 0` → `SWEEP done ok=402 bad=0 elapsed=184s`
(one command, under the 300 s cap; every product deleted before regeneration, mirror bytes = the pair
`842e2748bcdfeb66` + `b4363f5858e58074`). Re-run into a second directory (`logs/SWEEP_run.log`):
`ok=402 bad=0 elapsed=183s`, and **0 of 402 products differ between the two runs** — the sweep is
deterministic, so the changed-file list below is not a sampling artifact.

`work/sweep_cmp.py out_sweep work/head all402_rel.txt` (`work/SWEEP_cmp.log`) — HEAD products extracted
with `git archive HEAD site-packages` (equivalent to `git show HEAD:<path>`, stored LF), compared after
stripping CR from both sides:

```
compared=402 identical=401 CHANGED=1 missing=0
  CHANGED site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc head=176180B swept=176226B
```

**One changed file corpus-wide, and it is the target.** `replace_utils` is now inside the 401 identical.
Judge of the changed file plus every canary (`work/JUDGE_changed_and_panel.log`, run on the swept
products): broker `units=127/128` (only `_sync_worker`), quotation `153/153`, quote `92/92`,
order_api `37/37`, klinedata `64/64`, handlers `30/30`, matcher `17/17`, wizard_quant_api `58/58`,
trade_info_utils `41/41`, api_base `28/28`, real_quote `45/45`, strategy `27/27`,
risk_calculation `43/43`, realtime_event_source `12/13` (clock_worker unchanged, not this ticket),
arg_checker `49/49 / 39/39 / 43/43`, profiler_func `17/17 / 15/15 / 18/18`, replace_utils `9/9`.

No changed file loses a unit: the only changed file gained one (126 → 127). The 401 unchanged files
cannot lose a unit by definition, which is the evidence the 20-file panel was never going to give.
I did not run pytest/small34/selfcheck here — the byte-identity sweep subsumes them for this candidate,
and the 402-file gate is the owner's step.

## §7 Membership, principles, and correctness at identification

Counting rule (stated because r82a's 148 and r78a's 186 are different definitions — `work/membership.py`
header carries the same text): `blocks` = `BasicBlock` objects in `build_cfg(co).blocks`;
`regions` = `len(RegionAnalyzer.regions)` after `analyze()`; `two_owner` = CFG blocks listed in the
`blocks` of ≥ 2 regions; `zero_owner` = blocks listed by 0 regions; `not_held` = regions whose `entry`
is not in their own `blocks`.

| code object | analyzer | blocks | regions | two_owner | zero_owner | not_held |
|---|---|---|---|---|---|---|
| `_process_order` | landed `f7d849e9…` | 63 | 19 | 60 | 0 | 0 |
| `_process_order` | A `842e2748…` (= the pair's analyzer) | 63 | 20 | 60 | 0 | 0 || `decrypt_database_url` | landed | 46 | 11 | 35 | 0 | 0 |
| `decrypt_database_url` | A | 46 | 11 | 35 | 0 | 0 |

(`two_owner` under this rule counts blocks listed by ≥2 region objects, and nested/parent regions in
this codebase legitimately re-list child blocks, so a large `two_owner` is the norm here and is NOT the
metric the earlier 148-vs-186 arguments were about; the claim that matters is the **delta**: +1 region,
`two_owner` and `zero_owner` unchanged, `not_held=0`.)

* Principle 2 (unique membership): A's recovered join adds exactly one region in `_process_order` and
  **does not add a double owner** (60 → 60) and no orphan (`zero_owner 0 → 0`); in `replace_utils` A
  changes nothing at all, and my candidate does not touch the analyzer, so the pair's analyzer-side
  numbers are these. The conjunct is emission-side and registers no block: it only ever *declines* to
  take ownership, so it cannot create a second owner.
* Principle 4 (parent references child entry): `not_held = 0` in both variants; the span's refusal path
  returns before `generated_blocks` / `generated_offsets` are written.
* Correct-at-identification: the conjunct is evaluated inside the identifier (`_ternary_host_call_prefix_span`)
  before any claim is recorded, from the span's own instruction tail — no look-ahead, no cross-region
  information, no counters.

## §8 Verdict, install recommendation, manifest

**Both arms of the acceptance bar are green: broker `_process_order` Equal (`127/128`, `delta=0 hunks=0`)
AND `replace_utils` `9/9`, with a zero-loss 402-file collateral list (1 changed file, +1 unit).**
I would install the pair: analyzer half **unchanged** `842e2748bcdfeb66` + generator half
**`b4363f5858e58074`** (the r86a rebuild of r85c + the conjunct).

Two corrections to the brief for the record:
1. the collateral is caused by the **generator** half, not the analyzer half (§1);
2. the prescribed `POP_TOP` veto is not implementable here (§3), the tail-boundary test is.

`D:/Temp/r86/DELIVER/`

| file | sha16 | role |
|---|---|---|
| `FIX_R21-56_diamond_join_consumption.md` | — | this document |
| `build_cand_r86a_r2156.py` | — | rebuild the generator half from landed bytes (self-checks the r85c reproduction `45796ca24b371a8c`; re-run twice, both produce `b4363f5858e58074` byte-for-byte). No second builder is needed: the analyzer half is the banked r85a file **unchanged**, and no analyzer byte of mine differs from landed `f7d849e974904492` except through that file. |
| `CANDIDATE_r86a_r2156_generator_relax_tail_boundary.py` | `b4363f5858e58074` | candidate (pair half 2), BOM + all-CRLF, no `\r\r\n`, `compile()` + `py_compile` OK |
| `MEASURED_r86_base_broker_product.py` / `…base_replace_utils…` | `a6d6deb7…` / `6863a9f7…` | landed-byte products |
| `products/MEASURED_r86_{A,C,Cp,AC,ACP}_{broker,replace_utils}_product.py` | see §5 | one per variant per file |
| `products/SWEPT_trade_live_broker.py` | `f25d834a…` | the target file as produced by the 402-file sweep |
| `logs/SWEEP_cmp.log`, `logs/SWEEP_run.log` | — | CR-stripped byte compare of all 402 swept products vs HEAD |
| `logs/JUDGE_changed_and_panel.log`, `logs/JUDGE_halves.log` | — | judge lines for the changed file + canaries + halves |
| `logs/CENSUS_tier1.log`, `logs/CENSUS_tier2.log`, `logs/census_tier1/*.json`, `logs/census_tier2_*.json` | — | fire censuses with counting rules |
| `logs/HALVES.log`, `logs/MEMBERSHIP.log`, `logs/PROBE_INERT.log`, `logs/DIFF_replace_utils_base_vs_C.log` | — | measurements |
| `rigs/` | — | `gen.py judge.py judge_sweep.py install.py sweep.py sweep_cmp.py membership.py dissite.py probe_run.py build_probe_gen.py census_tier1.py census_tier2.py unit_diff.py allwin_r63.py PANEL_20files.txt` |

Repo untouched: `git status --porcelain -- core/ site-packages/ scripts/ parsers/ utils/ bytecode/
pycdc.py` = 0 lines; mirror restored to `11324f276cce6d5b` / `f7d849e974904492`.
