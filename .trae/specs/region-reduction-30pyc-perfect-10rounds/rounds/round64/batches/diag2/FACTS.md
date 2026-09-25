# FACTS — Round 64 · batch diag2 (measured numbers only; mechanism prose lives in ANALYSIS.md)

Workspace: `D:/Temp/opencode/r64gate/diag2` · targets: 4 partial pyc (168 functions) + 11 pinned R63 repro shapes.
All numbers below are `scripts/pyc_batch_verify.bytecode_diff` readings produced by `h62.py run`
(`matched_functions/total_functions`, `mism = [name, orig_count, decomp_count, jump_diffs, true_diffs]`).
Every command was run with `python -X utf8` from this directory.

## 0. Byte-level provenance (this is what the arms were built against)

| file | stated landed | measured on disk at run time | verdict |
|---|---|---|---|
| `core/cfg/region_ast_generator.py` | sha `7ec41fa2f9cdd5d62c1a`, 3 086 600 B, BOM + pure CRLF (49 937 lines) | worktree = sha `5ffe31558df46f7f636d`, 3 036 663 B, BOM + **bare LF** (49 937 LF, 0 CRLF) | 3 086 600 − 49 937 = 3 036 663 **exactly**; re-converting LF→CRLF hashes to `7ec41fa2f9cdd5d62c1a` ⇒ *same bytes as landed, checkout lost its CRs only* |
| `core/cfg/region_analyzer.py` | sha `c694d2514eb2f2b21ccf`, 1 721 959 B | identical (BOM absent, pure CRLF 27 590) | untouched by this batch |

Update after the mirrors were built (08:12): the worktree file **re-smudged itself back to the landed
form** (3 086 600 B, `7ec41fa2f9cdd5d62c1a`, `git status --porcelain core/` now empty). While the drift
was live, `git status` said `M core/cfg/region_ast_generator.py` but both `git diff` and
`git diff --ignore-cr-at-eol` were **empty** and the HEAD blob equalled the bare-LF bytes
(3 036 663 / `5ffe31558df46f7f636d`) ⇒ the code text never changed, only the checkout's newlines.
The centre's own builder then accepts the merged spec directly —
`python -X utf8 ../mbuild.py c12r specs/cand_r64b2_merged_c12.json` →
`edits=2 lines=+75 bytes 3086600 -> 3092646 BOM=True`, and `../mirr_c12r/…/region_ast_generator.py` is
**byte-identical** to `mirr_c12/…` (sha `af273ca5c79c76dee866`). So the merged arm is reproducible with
the shipped tooling and **the two candidates do not collide**.
A fresh `--arm=landed` re-run after the drift reproduces every landed sha of the pre-drift dump
(see §1 column "landed-fresh"), so **no dump in this batch is stale in content**.

Consequence for the build tooling (recorded, not worked around silently):
`../mbuild.py` and `h62.py build` both derive `nl` from the worktree text and then assert
`out.count(b'\n') == out.count(b'\r\n')`, so **they refuse every spec — single-arm included — while the
checkout is bare LF**. `mbuild.py` additionally refuses two specs for the same file
(`'two specs for core/cfg/… -- merge them first'`), which is a *merge* requirement, not a collision.
`mbuild_diag2.py` (this dir) is mbuild with the CR-restoration step and every other assertion kept
(anchor uniqueness **in the already-patched text**, BOM preserved, uniform endings, claimed inserted-line
count). It restores the landed CRLF base before patching, so the mirrors measure the shipped form.

| arm | generator bytes | sha256/20 | edits | lines |
|---|---|---|---|---|
| landed (restored) | 3 086 600 | `7ec41fa2f9cdd5d62c1a` | 0 | +0 |
| `mirr_c1f` = `mirr_c1` (07:36 build) | 3 089 429 | `c6595d9bc46e28682a52` | 1 | +33 |
| `mirr_c2f` (= `mirr_c2` modulo CR) | 3 089 817 | `5b4bc8bed1ebfc85044` | 1 | +42 |
| `mirr_c12` | 3 092 646 | `af273ca5c79c76dee866` | 2 in one spec | +75 |

`mirr_c1f` is **byte-identical** to the previous agent's `mirr_c1`, and `mirr_c2f` equals `mirr_c2`
after LF-normalisation (`True`, both 3 039 838 B) ⇒ the single-arm dumps are reproducible from the
restored landed base.

## 1. Per-target baseline: landed vs c1 vs c2 vs c12 (168 functions over 4 files)

Official (index) readings, round 63: wizard 51/53, klinedata 42/45, scheduler 42/45, api_base 23/25.

| file | landed | landed-fresh (re-run after CR drift) | c1 | c2 | **c12** |
|---|---|---|---|---|---|
| `IQCommon/strategy/wizard_quant_api.pyc` | 51/53 `6f08c711b8339c5a` | 51/53 same sha | 51/53 same sha | 51/53 same sha | **51/53 same sha** |
| `IQCommon/api/klinedata.pyc` | 42/45 `f5cf4dc545b0ff05` | 42/45 same sha | 42/45 same sha | 42/45 same sha | **42/45 same sha** |
| `IQEngine/utils/scheduler.pyc` | 42/45 `dc2fb6ca37fb711d` | 42/45 same sha | 43/45 `d809b238385b5bd4` | 42/45 `dc2fb6ca37fb711d` | **43/45 `d809b238385b5bd4`** |
| `IQData/api/api_base.pyc` | 23/25 `0e2f6ed8d7ba4047` | 23/25 same sha | 23/25 `0e2f6ed8d7ba4047` | 24/25 `bb400ce80d918a3c` | **24/25 `bb400ce80d918a3c`** |
| **Σ matched / 168** | **158** | 158 | 159 | 159 | **160** |

c12's scheduler product sha equals c1's and its api_base product sha equals c2's **exactly** ⇒ the two
rules are mutually non-interfering, each file's product is the corresponding single-arm product.

### open defect tuples `[orig, decomp, jumpdiff, truediff]`

| arm | file | open functions |
|---|---|---|
| landed | wizard | `calculate_di` [75,73,0,45] · `params_analysis` [133,126,1,117] |
| landed | klinedata | `get_all_real_daily_kline` [188,187,3,26] · `get_multiminute_his_data` [479,478,3,16] · `kline_datetime_list` [389,389,9,228] |
| landed | scheduler | `get_checked_time` [106,106,0,43] · `is_run_interval_time_now` [225,201,2,173] · `run_daily` [77,71,0,56] |
| landed | api_base | `get_future_history_df` [973,957,3,229] · `get_history_df` [1742,1719,14,1277] |
| c1 | scheduler | `get_checked_time` [106,106,0,43] · `run_daily` [77,71,0,56] — `is_run_interval_time_now` **cleared** |
| c1 | other 3 | unchanged tuples, unchanged product shas (wizard/kline/api_base identical to landed) |
| c2 | api_base | `get_history_df` [1742,1719,14,1277] — `get_future_history_df` **cleared**; `get_history_df` tuple byte-identical to landed |
| c2 | other 3 | unchanged (scheduler sha == landed sha ⇒ c2 is inert on scheduler) |
| c12 | wizard 2 · klinedata 3 · scheduler 2 · api_base 1 | `calculate_di` [75,73,0,45] · `params_analysis` [133,126,1,117] · `get_all_real_daily_kline` [188,187,3,26] · `get_multiminute_his_data` [479,478,3,16] · `kline_datetime_list` [389,389,9,228] · `get_checked_time` [106,106,0,43] · `run_daily` [77,71,0,56] · `get_history_df` [1742,1719,14,1277] |

## 2. Pinned-shape battery (`dump/my4_shapes.txt`: 4 targets + 11 R63 repros; battery = the 11)

| shape (11 files) | landed | c1 | c2 | c12 |
|---|---|---|---|---|
| `round63_b1/r63_ft` | 1/2 | 1/2 | 1/2 | 1/2 |
| `round63_b1/r63_ft2` | 1/2 | 1/2 | 1/2 | 1/2 |
| `round63_b1/r63_ft4` | 1/2 | 1/2 | 1/2 | 1/2 |
| `round63_b2/probe_r63b2_cases` | 6/9 | **7/9** | 6/9 | **7/9** |
| `round63_b2/probe_r63b2_cases2` | 3/9 | **7/9** | 3/9 | **7/9** |
| `round63_b2/repro_r63b2_tail_cmp_return` | 1/2 | **2/2** | 1/2 | **2/2** |
| `round63_b3/r63b3_chained_value_ctx_prefix` | 2/2 | 2/2 | 2/2 | 2/2 |
| `round63_b4/r63b4_tern_in_elif_chain` | 3/3 | 3/3 | 3/3 | 3/3 |
| `round63_b5/r63b5_w1` | 1/2 | 1/2 | 1/2 | 1/2 |
| `round63_fix1/r63b3_chainstore_prefix` | 2/2 | 2/2 | 2/2 | 2/2 |
| `round63_fix2/r63b4_cond_boolop_stmt_steal` | 13/13 | 13/13 | 13/13 | 13/13 |
| **Σ / 48 · fully-clean files** | **34 · 4** | **40 · 5** | **34 · 4** | **40 · 5** |

The +6 battery functions belong to **c1 alone**; c2 is battery-neutral (34/48, every sha equal to landed —
`dump/c2f_shapes.jsonl`), and c12 == c1 on the battery (`ab --a=dump/c1_shapes.jsonl --b=dump/c12_shapes.jsonl`
⇒ `SAME=11 IMPROVED=0 REGRESSION=0 MOVED=0`).
Battery gain is **not** a stale-dump artifact: `landed-fresh` (§1) reproduced 34/48 with identical shas, and
`mirr_c1f` reproduces `mirr_c1` byte-for-byte.

Functions cleared on the battery by c1: `c5_elif_nochain_try` [57,37,2,28], `d1_elif_try` [57,37,2,28],
`d3_if_try` [57,37,2,28], `d6_elif_try_two_chain_and` [57,37,2,28], `d7_elif_try_assign` [61,39,1,26],
and `case_elif_try_tail_return` [210,186,2,158] → 2/2; `d8_elif_try_chain_or_plain` improves
[50,37,2,21] → [51,50,1,6] without clearing.

## 3. A/B tallies (raw output kept in `logs/`)

| comparison | result |
|---|---|
| `ab --a=dump/landed.jsonl --b=dump/c12_targets.jsonl` | `SAME=2 IMPROVED=2 REGRESSION=0 MOVED=0 ERR=0` (api_base 23→24, scheduler 42→43) — `logs/ab_r64_landed_vs_c12_targets.txt` |
| `ab --a=dump/landed2_targets.jsonl --b=dump/c12_targets.jsonl` (post-drift landed) | identical tally — `logs/ab_r64_landed2_vs_c12_targets.txt` |
| `ab --a=dump/landed2_shapes.jsonl --b=dump/c12_shapes.jsonl` (15-file list) | `SAME=10 IMPROVED=5 REGRESSION=0 MOVED=0`, fully-clean files 4→5 |
| `ab --a=dump/c1_targets.jsonl --b=dump/c12_targets.jsonl` | `SAME=3 IMPROVED=1 REGRESSION=0 MOVED=0` (only api_base moves) |
| `ab --a=dump/c2_targets.jsonl --b=dump/c12_targets.jsonl` | `SAME=3 IMPROVED=1 REGRESSION=0 MOVED=0` (only scheduler moves) |
| `ab --a=dump/c1_shapes.jsonl --b=dump/c12_shapes.jsonl` | `SAME=11 IMPROVED=0 REGRESSION=0 MOVED=0` |

**c12 is strictly additive; nothing regresses on any of the 19 files measured on both sides.**

## 4. New minimal repros (Job 4) — same 4-arm measurement

`F:/Downloads/pythoncdc-main/test_repros/round64_diag2/` (raw: `logs/r64repro_arms.txt`,
`logs/r64repro_t2_arms.txt`; machine-readable `dump/r64repro_{landed,c1f,c2f,c12}.jsonl`,
`dump/t2_{landed,c1f,c2f,c12}.jsonl`)

| repro | landed | c1 | c2 | c12 | owner |
|---|---|---|---|---|---|
| `r64d2_chain_yield_sibling_entry.pyc` (15 lines) | 1/2, `r64d2_chain_yield` [51,27,2,32] | **2/2** | 1/2 [51,27,2,32] | **2/2** | c1 |
| `r64d2_valuectx_consumer.pyc` (12 lines) | 1/2, `r64d2_valuectx` [39,23,0,30] | 1/2 [39,23,0,30] | **2/2** | **2/2** | c2 |

Both reproduce the *shape* of their real target (c1 repro: 24-instruction loss with `jumpdiff=2`,
matching the real [225,201,2,173] deficit; c2 repro: a silently dropped `len(df[mask])` assignment,
matching the real 17-instruction loss at @4274..@4360) and each is broken on the *other* candidate's
arm ⇒ ownership is proven, not assumed.

## 6. Distance to "fully OK" per file (round 64 closing requirement)

| file | landed | c12 | open defect functions on c12 | closest tuple |
|---|---|---|---|---|
| `IQData/api/api_base.pyc` | 23/25 | **24/25** | 1 — `get_history_df` [1742,1719,14,1277] | 25-instruction net deficit spread over 10 hunks (D3) |
| `IQEngine/utils/scheduler.pyc` | 42/45 | 43/45 | 2 — `get_checked_time` [106,106,0,43], `run_daily` [77,71,0,56] | 8-instruction misplacement + an undiagnosed name-collision case (D4/D5) |
| `IQCommon/strategy/wizard_quant_api.pyc` | 51/53 | 51/53 | 2 — `calculate_di`, `params_analysis` (D6/D7) | 2-instruction closure arity |
| `IQCommon/api/klinedata.pyc` | 42/45 | 42/45 | 3 (D8) | 1-instruction delete + polarity replaces |

**No file in this batch reaches full OK on c12.** api_base is the only 1-function-away candidate, and the
lone open function is *not* in c2's family (c2's arm leaves its tuple byte-identical), so it cannot
realistically close this round from diag2. The round requirement has to be met by whichever other batch
holds a file that is one *small-tuple* defect away.

## 7. Replayable commands

```bash
cd /d/Temp/opencode/r64gate/diag2
# 0. (env) worktree generator is bare LF; mbuild refuses ANY spec. Restore + merge:
python -X utf8 -c "import io,json; a=json.load(io.open('specs/cand_r64b2_chaincompare_yield.json',encoding='utf-8'));\
 b=json.load(io.open('specs/cand_r64b2_condcomp_consumer.json',encoding='utf-8')); e=a['edits']+b['edits'];\
 io.open('specs/cand_r64b2_merged_c12.json','w',encoding='utf-8',newline='\n').write(json.dumps({'file':a['file'],'edits':e},ensure_ascii=False,indent=1))"
python -X utf8 mbuild_diag2.py c12 specs/cand_r64b2_merged_c12.json       # -> mirr_c12, 2 edits, +75 lines
python -X utf8 mbuild_diag2.py c1f specs/cand_r64b2_chaincompare_yield.json
python -X utf8 mbuild_diag2.py c2f specs/cand_r64b2_condcomp_consumer.json
# 1. measure
python -X utf8 h62.py run --arm=c12    --list=dump/my4.txt       --out=dump/c12_targets.jsonl
python -X utf8 h62.py run --arm=c12    --list=dump/my4_shapes.txt --out=dump/c12_shapes.jsonl
python -X utf8 h62.py run --arm=landed --list=dump/my4.txt       --out=dump/landed2_targets.jsonl
python -X utf8 h62.py run --arm=landed --list=dump/my4_shapes.txt --out=dump/landed2_shapes.jsonl
python -X utf8 h62.py run --arm=c2f    --list=../shapes_r63.txt  --out=dump/c2f_shapes.jsonl
# 2. compare
python -X utf8 h62.py ab --a=dump/landed.jsonl        --b=dump/c12_targets.jsonl | tee logs/ab_r64_landed_vs_c12_targets.txt
python -X utf8 h62.py ab --a=dump/landed2_shapes.jsonl --b=dump/c12_shapes.jsonl | tee logs/ab_r64_all_comparisons.txt
# 3. repros (compiled with the project interpreter 3.11.7, py_compile -> <name>.pyc next to <name>.py)
python -X utf8 h62.py run --arm=landed --list=dump/r64repro.txt --out=dump/r64repro_landed.jsonl
```
`h62.py run` appends and skips `arm|path` already present in `--out`; delete the file to force a re-read.
