# ARMS B127 — `r10g7_` 电池与基线（Round 10 工单 #15，G7 落点成员判据）

Battery builder's report. **No production code was touched**: `core/` is byte-clean
(`git status --porcelain -- core/` empty at every reading) and the two sealed files were
re-hashed before any number below was trusted.

| item | value |
|---|---|
| repo | `D:\admin\.qoder\worktrees\app\f557fd\pythoncdc-main` @ `274b6a2c` |
| `core/cfg/region_ast_generator.py` | 3715383 bytes, sha256 `e9a8f65f6451bcc8…` = ticket's sealed prefix ✔ |
| `core/cfg/region_analyzer.py` | 2058547 bytes, sha256 `38a1d5142d132fd7…` ✔ |
| `git status --porcelain -- core/` | empty (verified before and after the battery) |
| interpreter | 3.11.7 (`python -X utf8` everywhere; PYTHONIOENCODING never set) |
| ruler | `scripts/pyc_verify.py` → `pylingual/equivalence_check.py` sha256 `9c7567bd6776b36b` |
| read date | 2026-10-08 |

Defect mechanism under test (one line): **a shared implicit-return epilogue is not
recognised as ONE landing point**, so each path inlines its own
`LOAD_CONST None; RETURN_VALUE` and the shared tail that should be jumped into is never
emitted. Production site = `core/cfg/region_ast_generator.py:51806-51812`, the `[G7]`
clause whose release condition is the coincidence
`_pli is not None and _pli.opname == 'POP_TOP'` (verified present at current bytes).
The same builder already computes a joint-owner test at `:51813-51821`
(`_p in _rb and _b in _rb` over `self.regions`) — noted so the fix engineer does **not**
duplicate that machinery; only the `POP_TOP` coincidence branch is to be replaced by
region-membership facts.

---

## 1. 仪器（口径与 `D:/Temp/r9main/r10loss.py` 一致）

`D:/Temp/r10g7/r10g7_hunk.py` — per-unit hunk printer:
* pairs orig/product code objects by **FULL walk path** (`/<module>/<qual…>`), refuses to
  judge when a path has more than one copy (the corpus has two different `handlers.pyc`;
  name-tail matching is the known trap);
* prints per unit `len orig/prod`, `net`, `hunks`, and splits `deleted` (orig-only) from
  `inserted` (prod-only) so relocation is never conflated with loss;
* classifies each hunk `real` (opcode multiset differs → true content loss/gain) vs
  `reloc` (same opcodes, only jump targets moved);
* normalises nested code-object constants `<code object X at 0xADDR, file "F", line N>`
  → **`<co X>`** before comparing. The line number is dropped too, otherwise every product
  whose `def` moved manufactures a false diff (ticket §六 `NORMALIZER_BLIND`).

Validation of the instrument against the ticket's own numbers (current bytes, corpus):

| corpus unit (full qualname) | this instrument | ticket §一/§五/§八 |
|---|---|---|
| `IQCommon/logger/handlers.pyc :: <module>.TWHThreadController._target` | `len 199/197 net=+2 hunks=17 real=1 reloc=16`, `delete orig[75:77] = LOAD_CONST None \| RETURN_VALUE` | 199/197, 17 hunks, one content diff ✔ |
| `… :: <module>.TWHThreadRotatingFileHandler._target` | `len 126/126 hunks=0` | 126/126, 0 ✔ (mandated same-named negative control) |
| `IQCommon/util/trade_info_utils.pyc :: <module>.query_strategy_id` | `len 117/116`, `orig[108] JUMP_FORWARD ->@648` → inlined pair, `orig[115:117]` tail pair deleted | ✔ |
| `… :: <module>.query_trade_strategy_info` | `len 122/122 net=0`, two inline sites (`orig[94]`, `orig[113]`) + tail pair `orig[120:122]` deleted | ✔ (net 0 but defect real) |
| `fly/data/quote.pyc :: <module>.Quote.check_frequency` | `len 131/132`, `orig[106:108]` pair → `JUMP_FORWARD ->@558`, surplus pair inserted at `prod[130:132]` | ✔ |
| `IQCommon/api/klinedata.pyc :: <module>.get_multiminute_his_data` | `len 529/530`, `orig[512] JUMP_FORWARD ->@2758` → `LOAD_FAST his_data_dict \| RETURN_VALUE`; `orig[527] LOAD_FAST his_data_dict` → `LOAD_CONST None` | ✔ |
| `IQCommon/strategy/wizard_quant_api.pyc :: <module>.filter_desicion` | `len 195/197`, `POP_JUMP_FORWARD_IF_NONE ->@710` → `->@774`, surplus pair at `prod[195:197]` | ✔ |
| `fly/data/quote.pyc :: <module>.Quote.get_real_from_zeromq` | `len 782/780 hunks=39 real=5 reloc=34`, `insert prod[187:188] JUMP_FORWARD ->@1034` before the shared `return None, flag` | ✔ |

## 2. 电池名册（`test_repros/round9/`，前缀 `r10g7_`，19 臂 = 12 复现 + 4 名单探针 + 3 负对照）

`units` column is the judge reading of that arm's `.pyc` (module unit + function unit);
every failing unit is named by FULL qualname path.

| arm | role | depth | the face it prints (hunk evidence) | units | failing unit (full qualname) |
|---|---|---|---|---|---|
| `r10g7_01_loopexit_pair_elsestmt` | repro A | 2 | §八#1 `_target`: `delete orig[19:21] LOAD_CONST None\|RETURN_VALUE` @66 + 3 target-propagation hunks (`->@70`→`->@66`, `->@66`→`->@62`) | 1/2 | `<module>.r10g7_01_loopexit_pair_elsestmt` |
| `r10g7_02_loopexit_pair_deep3` | repro A | 3 | same, nested one level deeper (`if outer:` → `if A and B:` → `while`): 1 pair missing @66 + 4 reloc | 1/2 | `<module>.r10g7_02_loopexit_pair_deep3` |
| `r10g7_03_loopexit_pair_handler_in_loop` | repro A | 4 | the literal `_target` twin (`if sys.version_info… and …:` → `while` → `try/except` → post-try statements → `else:` real stmt): pair @328 never emitted, 3 reloc | 1/2 | `<module>.r10g7_03_loopexit_pair_handler_in_loop` |
| `r10g7_04_loopexit_pair_for_twin` | repro A | 2 | `for` instead of `while` — same merge, pair @66 missing, 2 reloc | 1/2 | `<module>.r10g7_04_loopexit_pair_for_twin` |
| `r10g7_05_loopexit_pair_two_loops` | repro A | 3 | two sequential loops in the then-arm (the second one owns the shared tail): pair @104 missing, 3 reloc | 1/2 | `<module>.r10g7_05_loopexit_pair_two_loops` |
| `r10g7_06_loopexit_pair_handler_then_loop` | repro A | 3 | handler epilogue + loop tail in the same then-arm, `else` arm real statement: pair @234 missing, 2 reloc | 1/2 | `<module>.r10g7_06_loopexit_pair_handler_then_loop` |
| `r10g7_07_querytail_inline_single` | repro B | 3 | §八#2 `query_strategy_id`: `orig[57] JUMP_FORWARD ->@248` written in place as `LOAD_CONST None\|RETURN_VALUE` | 1/2 | `<module>.r10g7_07_querytail_inline_single` |
| `r10g7_08_querytail_inline_two_sites` | repro B | 3 | §八#3 `query_trade_strategy_info`: **two** such sites in one function (`orig[63]`, `orig[118]`) — both must clear | 1/2 | `<module>.r10g7_08_querytail_inline_two_sites` |
| `r10g7_09_querytail_inline_deep3` | repro B | 4 | inline site @242 **plus** a surplus `LOAD_CONST None\|RETURN_VALUE` appended at `prod[67:69]` @258 | 1/2 | `<module>.r10g7_09_querytail_inline_deep3` |
| `r10g7_10_querytail_inline_double_pair` | repro B | 3 | one `JUMP_FORWARD ->@240` replaced by **two** inlined pairs (both landing points inlined, shared tail never emitted) | 1/2 | `<module>.r10g7_10_querytail_inline_double_pair` |
| `r10g7_11_querytail_inline_handler_stmt` | repro B | 3 | inline @290 with a real statement after the handler (`time.sleep(1)`), i.e. epilogue is not the handler's last instruction | 1/2 | `<module>.r10g7_11_querytail_inline_handler_stmt` |
| `r10g7_12_querytail_inline_else_arm` | repro B | 3 | same inline with an `else:` arm present (then/else membership on both sides of the tail) | 1/2 | `<module>.r10g7_12_querytail_inline_else_arm` |
| `r10g7_13_probe_valuetail_multiminute` | probe (§八#5) | 3 | **DOES NOT REPRODUCE** — 0 hunks; the value tail's attribution error needs corpus scale | 2/2 | — |
| `r10g7_14_probe_isnone_late_landing` | probe (§八#6) | 3 | **DOES NOT REPRODUCE** — 0 hunks | 2/2 | — |
| `r10g7_15_probe_tuple_tail_handler` | probe (§八#7) | 3 | **DOES NOT REPRODUCE** — 0 hunks | 2/2 | — |
| `r10g7_16_probe_checkfreq_assert_tail` | probe (§八#4) | 3 | **DOES NOT REPRODUCE** — 0 hunks (see §4: the *direction* of #4 is not reachable from a small twin) | 2/2 | — |
| `r10g7_17_ctl_rotatingfilehandler_twin` | **control** | 3 | clean twin of `TWHThreadRotatingFileHandler._target` (shape copied off that passing unit's disassembly) — 0 hunks, must stay 0 | 2/2 | — |
| `r10g7_18_ctl_plain_try_except_trailing` | **control** | 2 | plain `try/except` + trailing statement + `return b` — 0 hunks | 2/2 | — |
| `r10g7_19_ctl_while_return_no_tail` | **control** | 3 | simple `while` + `return`, no shared tail — 0 hunks | 2/2 | — |

Family A = the §一/§八#1 face (shared pair merged → **one pair never emitted**, everything
else is target-offset propagation). Family B = the §五/§八#2-#3 face (path that should
`JUMP_FORWARD` into the shared tail is **inlined**, tail then dropped or duplicated).

## 3. Baseline（current bytes, `core` = sealed above）

`python -X utf8 scripts/pyc_verify.py batch --index test_repros/round9/r10g7_probe_index.json --json D:/Temp/r10g7/base.json`

```
files_total   = 19      (= number of arms built; no arm missing from the index)
units         = 26/38 (68.42%)
files_by_status: success 7 / failure 12 / compile_error 0 / error 0
elapsed_sec   = 1.8
```

* **12 red** = exactly the 12 repro arms `r10g7_01 … r10g7_12`, each `1/2`, failing unit is
  always the arm's own function (`<module>.r10g7_NN_…`), verdict `Different control flow`;
  the module unit of every arm is Equal.
* **7 green** = 4 roster probes (`r10g7_13…16`) + 3 controls (`r10g7_17…19`).
* Pre-existing arms, read at the same bytes for continuity (not in this index):
  `r9g7_01_else_arm_twin`, `r9g7_02_with_handler_tail_twin`, `r9g7_03_single_landing_negative`,
  `r9g7_04_mixed_elsearm_and_tail` → 8/8 units, 4/4 files success. Ticket §二/§五 clamp: they
  must stay 2/2 after the G7 rewrite (`D:/Temp/r10g7/r9g7_base.json`).

## 4. FINDINGS（the fix engineer must read this before coding）

1. **Only two of the seven roster faces are reachable from small hand-written twins at
   current bytes.** Faces §八#1 (missing shared pair) and §八#2/#3 (jump-into-tail written
   in place) reproduce reliably — 12 arms, 2 independent structural families, depths 2-4.
   Faces §八#4 (`check_frequency` in-place-return→jump), #5 (`get_multiminute_his_data`
   value attributed to the wrong return site), #6 (`filter_desicion` late `IF_NONE` landing
   + surplus tail pair), #7 (`get_real_from_zeromq` inserted jump skipping both in-edges)
   were each attempted in 6-10 shape variants (`m1-m6`, `e1-e5`, `v1-v6`, `n01-n10`, `p01-p06`,
   `c1-c5`, scratch `D:/Temp/r10g7/cand_src/*`) and **every one recompiled to a byte-Equal
   product**. They are registered above as probes 13-16, not as repros. Consequence: a G7
   rewrite cannot be accepted on this battery alone for #4-#7 — those four units must be
   re-measured on the corpus files themselves (`klinedata`, `wizard_quant_api`, `quote`,
   and the §八#4-#7 unit lists in `UNITMAP_R10.md`).
2. **Two arms were caught mislabelled during construction and re-authored/moved** (recorded
   as instructed):
   * `r10g7_06` first landed as `r10g7_06_loopexit_pair_then_returnnone` (a `while` with a
     `try/except` body plus a trailing `return None`) — it printed **0 hunks**, so it did not
     reproduce family A; it was replaced by the handler-then-loop shape above, which prints
     the missing pair.
   * Candidate `k10` (two version-gated `while` loops, the closest small twin of the real
     `_target` body) reads red but prints the **loop-test duplication/relocation face**
     (`POP_JUMP_FORWARD_IF_FALSE` re-targeted + a moved `LOAD_FAST running`), not a missing
     pair; it was dropped from the roster rather than passed off as face A.
   * `c1/c2/c5/n01/n02/n03` (`assert`-feeding-a-tail attempts aimed at §八#4) read red but
     print a **different ticket's face** — the `int(n)` / `assert` statement-omission hunk
     (`LOAD_GLOBAL NULL + int | LOAD_FAST n | … | STORE_FAST tmp` collapsed to
     `LOAD_GLOBAL tmp`). That is the #13/#16 omission mechanism; those arms were NOT
     registered here so this battery cannot be accused of claiming another ticket's red.
3. **The `POP_TOP` coincidence is provably not the discriminator.** In every family-A arm
   the two merged pure-none blocks have the *same* predecessor opcode and differ only in
   region membership (one is the loop's bottom-test fall-through continuation, the other is
   entered by the loop's prelude-test conditional jump). Arms `r10g7_01/04/05` show that a
   `POP_TOP`-based release test cannot separate them; arms `r10g7_07…12` show the mirror
   case where the landing point is inlined instead of suppressed.
4. **Net figures lie.** `r10g7_09/10` have `net=-3` yet lose a pair and gain two, and
   `r10g7_08` has `net=-6` with only 2 `real` hunks. The clamp for the fix must be
   **`real` (content) hunks → 0 AND `reloc` → 0** per unit — the ticket §二.1 rule
   ("hunks 17→0, 补发一对却仍有 16 处目标差 = FAIL") generalises to this battery.
5. Nothing under `site-packages/` was written; no `*OK.py` outside `test_repros/round9/`
   was created or modified; `test_repros/round3/` and `round9/r10ls_*` untouched; no git
   write command was run.

## 5. 怎么复跑（exact commands, from the repo root）

```bat
:: 0. bytes of the ruler subject must match the sealed prefixes
python -X utf8 -c "import hashlib;[print(f,hashlib.sha256(open(f,'rb').read()).hexdigest()[:16]) for f in ['core/cfg/region_ast_generator.py','core/cfg/region_analyzer.py']]"
git status --porcelain -- core/

:: 1. rebuild the battery (writes sources, compiles each .pyc with the local 3.11,
::    deletes any existing product, then regenerates every *OK.py ONLY through pycdc.py)
python -X utf8 D:/Temp/r10g7/mkarms.py

:: 2. baseline through the sole judge (19 files, ~2 s; shard with --limit only if needed)
python -X utf8 scripts/pyc_verify.py batch --index test_repros/round9/r10g7_probe_index.json --json D:/Temp/r10g7/base.json

:: 3. per-arm face proof (content hunks; deleted vs inserted separated, <co> normalised)
python -X utf8 D:/Temp/r10g7/r10g7_hunk.py r10g7_01_loopexit_pair_elsestmt r10g7_03_loopexit_pair_handler_in_loop r10g7_08_querytail_inline_two_sites

:: 4. corpus face check (the ticket's own evidence units)
python -X utf8 D:/Temp/r10g7/r10g7_hunk.py --corpus "IQCommon/logger/handlers.pyc" "<module>.TWHThreadController._target"
python -X utf8 D:/Temp/r10g7/r10g7_hunk.py --corpus "IQCommon/logger/handlers.pyc" "<module>.TWHThreadRotatingFileHandler._target"
python -X utf8 D:/Temp/r10g7/r10g7_hunk.py --corpus "IQCommon/util/trade_info_utils.pyc" "<module>.query_strategy_id"

:: 5. the four pre-existing r9g7 arms must stay 2/2 (§二 clamp)
python -X utf8 scripts/pyc_verify.py batch test_repros/round9/r9g7_01_else_arm_twin.pyc test_repros/round9/r9g7_02_with_handler_tail_twin.pyc test_repros/round9/r9g7_03_single_landing_negative.pyc test_repros/round9/r9g7_04_mixed_elsearm_and_tail.pyc --json D:/Temp/r10g7/r9g7_base.json
```

Notes for whoever re-runs this: use `python -X utf8` and **never** set `PYTHONIOENCODING`;
Git-Bash rewrites arguments that begin with `/`, so unit names are passed in the brief's
`<module>.A.b` qualname form (the instruments translate them to walk paths themselves).
Index format follows `r10ls_probe_index.json`: a JSON **list** of
`{"path": "test_repros/round9/<arm>.pyc"}` with forward slashes, indent 2, LF, no BOM.

Artifacts: `D:/Temp/r10g7/base.json` (baseline report), `D:/Temp/r10g7/r9g7_base.json`,
`D:/Temp/r10g7/arms_hunks.txt` (full face prints of all 19 arms),
`D:/Temp/r10g7/{dump_unit,pairs,search,cycle,r10g7_hunk,mkarms}.py` (instruments).

## 6. 读数可复现性 + 现场观察（registered）

* Rerun of the exact batch command produced a **byte-identical row set** (per-row `pyc_sha`,
  `source_sha`, `status`, unit counts all equal; `D:/Temp/r10g7/base_rerun.json` vs
  `D:/Temp/r10g7/base.json`): 19 files, 26/38 units, success 7 / failure 12. The battery is
  deterministic at these bytes; no arm flips between runs.
* While this battery was being built, a **concurrent corpus regeneration was observed writing
  `site-packages/**/*OK.py`** (about one file per second starting 11:10, which is why
  `git status --porcelain -- site-packages` lists
  `M site-packages/IQEngine/plugins/plugin_system_accounts/__init__OK.py` while `git diff`
  for it is empty — stat-only churn from the other run). Nothing in this ticket wrote there:
  the instruments read `site-packages/` only, and every product they produce lands next to its
  own arm `.pyc` inside `test_repros/round9/`. Registered so no later reader attributes that
  churn to this battery, and so the fix engineer knows the 402-file gate is live in this
  worktree while these arms are used as the ruler.
* File census of this deliverable (disk vs index, no orphan, nothing unregistered):
  19 arms x 3 files = 57 — `r10g7_*.py`, `r10g7_*.pyc`, `r10g7_*OK.py` (product naming follows
  the `r9g7_*` convention so `pyc_verify.product_of()` finds it) — plus
  `r10g7_probe_index.json` with exactly 19 entries. The first arm-06 draft
  (`r10g7_06_loopexit_pair_then_returnnone`, which failed to reproduce its face) was deleted
  with all three of its files; no trace remains.

