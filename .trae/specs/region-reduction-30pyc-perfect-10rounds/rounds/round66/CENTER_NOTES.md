# Round 66 · center notes (live, pre-archive)

Landed bytes at round open (= R65, commit `4d2a0039`):
`core/cfg/region_ast_generator.py` 3 123 069 B sha `e0cf887ecb7430d662c2` BOM+CRLF bare-LF 0;
`core/cfg/region_analyzer.py` 1 727 576 B sha `9fd4618b7bd2647f111f` CRLF bare-LF 0.

## 0. Round-open baseline audit (center, `--arm=landed`, 4 shards, dump/l402_all.jsonl)
402 records, matched **5693/5746**, fully-matched files **385**, errors 0.
`audit66.py` vs committed `pyc_index.json`: entries-not-in-dump **0**, dump-paths-not-in-index **0**,
**per-entry mismatches 0** (compares matched_functions / function_count / decompile_status).
battery 24 items: matched 91/104, 17 fully clean files (dump/battery_landed.jsonl).
canary 4: 143/143, 10/10, 26/26, 25/25; shas 4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177.
Strict ruler over the 17 partials: **672/749** (dump/strict_landed17.json).

## 1. Adopted candidates (independently reproduced in center, not taken from the agents)

| spec | batch | marker | site (landed bytes) | target reading |
|---|---|---|---|---|
| `diag6/specs/cand_r66_iterpre_del.json` | diag6 | `[R66-diag6-A for-iter-delete-terminator]` | `_loop_extract_for_iter_pre_stmts` (def L7081) anchor @L7212 | `IQCommon/util/common_func.pyc` **20/21 → 21/21** (full OK), strict 21/22→22/22 |
| `diag4/specs/cand_r66_d1_augsub_continue.json` | diag4 | `[R66-diag4 D1 augsub-continue-role]` | `_generate_block_statements_body` STORE_SUBSCR splitter @L44369-71 | `plugin_system_risk_calculation/__init__.pyc` 32/35 → 33/35 (`get_TradeMode_trades` cleared), strict 33/37→34/37 |
| `diag5/specs/cand_r66_trytail_else.json` | diag5 | `[R66-diag5-B try-tail-unprotected-else]` | `_generate_try` tail @L26554 | `IQEngine/utils/scheduler.pyc` 43/45 → 44/45 (`get_checked_time` cleared), strict 49/52→50/52 |
| `diag1/specs/cand_r66_e1.json` | diag1 | `[R66-diag1 E1 单测试空臂不得吞并 if/else 之后的汇合块]` | `_merge_block_is_then_exclusive` (def L16809) `_noise_ops` filter @L16843-16850, use site `_if_generate_normal` (def L17290) @L17916 | `trade_live_broker.pyc` 106/119 → **107/119** (`get_etf_stock_info` cleared), strict 104/123→105/123 |

Symbol verification done by the center before adopting (memory rule):
- `_build_delete_stmt` def L47882, 8 call sites → diag6 delegates to existing builder; DELETE terminators
  already exist at L2856 / L5706 / L8931 (the patched method was the odd one out).
- `_w11_unprotected_else_candidate` def `region_analyzer.py` L10360, signature `(try_region, block)`;
  `self.region_analyzer` used 345× in the generator → diag5's cross-object call is an existing channel.
- diag4 anchor `count==1` @L44369; `_split_subscr_operands` def L2624, `_build_subscript_assign` def L49198.
- diag1: `IfRegion.chained_compare_blocks` is a real dataclass field (`region_analyzer.py` L372, class `IfRegion`
  at L363 — also present on AssertRegion L996 / TernaryRegion L1152, all `default_factory=list`);
  `_merge_block_is_then_exclusive` L16809 / `_noise_ops` L16843 / `_if_generate_normal` L17290 all confirmed
  on landed bytes. Center rebuilt the arm alone: 17-partial `SAME=16 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`,
  battery `SAME=24`, canary `SAME=4`, synth-repro 2/3→3/3 — matches the agent's numbers.
  The agent's variant-1 rejection is kept as evidence (no `chained_compare_blocks` clause ⇒ `strategy.pyc`
  24/24→23/24 on the 402; the 24-item battery did NOT catch it).

## 2. Merged sets (one file, `core/cfg/region_ast_generator.py`)
- `m66`  = 3 edits (diag6+diag4+diag5), +100 lines
- `m66b` = 4 edits (m66 + diag1 E1), +143 lines, mirror 3 134 898 B sha `716422d4e10ec0f8245e`,
  BOM kept, CRLF 50 552, bare LF 0; markers at L7219 / L16876 / L26625 / L44490.
  `h62.py build` for both reported `head pristine == worktree bytes` (repo untouched).

| gate | landed | m66 | m66b | verdict |
|---|---|---|---|---|
| 17 partials (official) | 0 full-OK | `SAME=14 IMPROVED=3 REG=0 MOV=0 ERR=0` | `SAME=13 IMPROVED=4 REG=0 MOV=0 ERR=0` | additive, 4 files up, 1 newly fully OK |
| battery 24 | 91/104, 17 clean | `SAME=24` | `SAME=24` IMP=0 REG=0 MOV=0 ERR=0 | identical shas |
| canary 4 | 4 shas | `SAME=4` | `SAME=4` | identical shas |
| **402 A/B** | matched 5693, clean 385 | matched 5696, clean 386 | matched **5697/5746**, clean **386** | `SAME=398 IMPROVED=4 REGRESSION=0 MOVED=0 ERR=0`, 4 shards ×(101/101/100/100) each < 24 s |
| product blast (402) | — | 3 changed | **identical=398 changed=4 unresolved=0** | changed set == the 4 IMPROVED files |
| Σ\|orig−decomp\| | 418 | 377 | **375** | −43 |
| Σ jumpdiff / Σ truediff | 196 / 11977 | 192 / 10272 | **191 / 10133** | −5 / −1844 |
| defect functions (402) | 53 | 50 | **49** | −4 |
| strict ruler (17 partials) | 672/749, 77 defects (51 seq_len/18 target_diff/8 seq_diff) | 675/749, 74 | **676/749, 73 defects (48/18/7)** | +4, **0 NEW defect on any of the 17 files**, per-file diff = 4 removals only |

## 3. Per-edit witness: the four new minimal repros, run in center on one list (`r66repro.txt`)
| repro | landed | m66b |
|---|---|---|
| `diag1/synth/r66_empty_then_join.pyc` | 2/3 (`j1` 17/16 jd1 t12) | **3/3** |
| `diag4/synth/r66d4_augsub.pyc` | 1/2 (`probe` 94/78 jd2 t62) | **2/2** |
| `diag5/synth/r66_else.pyc` | 2/3 (`wrapped` 43/43 t17) | **3/3** |
| `diag6/synth/r66_delrepro.pyc` | 1/3 (`p_a` 36/33, `p_b` 16/14) | **3/3** |

A/B: `IMPROVED=4 SAME=0 REGRESSION=0 MOVED=0 ERR=0`, matched 6/11 → **11/11**, fully-matched files 0 → 4.
So the merged set is not just additive on the corpus — each edit still clears its own witness after all four
are applied together (no within-set interference).

## 4. Product-level specimen check of the 4 changed `*OK.py` (logs/prod_diff_landed_m66b.txt)
- `IQCommon/util/common_func`: `+ del freq_k_minute[0]` (statement restored, diag6)
- `risk_calculation/__init__`: 3×3 mangled `'win_time'[1] = self.TradeMode_trade_statistic` →
  `self.TradeMode_trade_statistic['win_time'] += 1` etc. (diag4)
- `trade_live_broker`: duplicated `in_stock = []` inside the empty then arm → `pass` (diag1)
- `scheduler`: unconditional `hour, minute = divmod(minute_time, 100)` → moved under restored `else:` (diag5)

## 5. Batch 2 (diag2) and batch 3 (diag3) — both died on the 150-turn cap, deliverables salvaged
`r66diag2` and `r66diag3` were cut off at 150 turns (turn cap, see memory `project-subagent-turn-cap`);
both had written FACTS.md before dying, and every claim was re-measured in center on my own arms.

| spec | batch | site (landed bytes) | center re-measurement |
|---|---|---|---|
| `cand_r66_p4_chainhead_owner.json` | diag2 | generator, `_generate_chain_head_prefix_assign` owner loop, anchor L16985 (count==1) | quote MOVED `load_bars_from_hundsun` 524→479 (orig 477), dup log statement 2→1, battery `SAME=24`, canary `SAME=4` |
| `hold_r66_p3_prefixparts.json` (agent quarantined) | diag2 | generator, f-string prefix scan, anchor L36179 | fsrepro **6/7→7/7**, fs2 `v8` 23→27 instrs (truediff 28→14), quote Σtruediff −246 |
| `cand_r66_p1_namecallee.json` (agent quarantined) | diag2 | generator, `_ternary_pending_callee` tail, anchor L41454 | fs2 **5/10→6/10** (`v3` cleared), corpus 17 `SAME=17` (inert), canary `SAME=4` |
| `cand_r66_diag3.json` | diag3 | **`core/cfg/region_analyzer.py`** L20948 inside `_detect_ternary_pattern` (nested in `_identify_ternary_regions`, so `conditional_regions` is its parameter, L20122) | real_quote **39/44→40/44** (`get_cache_l2_data` fully matched on both rulers), battery `SAME=24`, canary `SAME=4`, its 3 repros 6/12→11/12 |

Symbol verification for diag3 (all on landed bytes): `FORWARD_CONDITIONAL_JUMP_OPS` L37, `NOISE_OPS` L60,
`IfRegion` L363, `can_be_ternary_header` L457, `_can_be_ternary_header` L20253, `_detect_ternary_pattern`
L20932 (indent 8 = nested), `_is_single_expression_block` L2781 (16 `self.` uses),
`get_last_instruction` = `core/cfg/basic_block.py` L132, anchor `count==1`.
Rejected/out-of-spec recorded: diag2 `p2 storeepi` (premise falsified — `value_target` is the
`'__fstring_target__'` sentinel, produced zero change), diag3 arm `drop` (drops `[R24-A]` alone ⇒ keeps a
stray `if …: pass`, synth 33/31→33/46) and arm `pair` (2 anchors, 2 levels — out of spec, but its readings
equal the single-anchor `cand`, which is what makes L20948 the load-bearing collapse).

## 6. Final merged set `m66e` = 2 files, 8 edits, +316 lines
`m66e_region_ast_generator.py.json` (7 edits, +217) + `m66e_region_analyzer.py.json` (1 edit, +99),
built by `mbuild66` into `center/mirr_m66e`: every anchor unique under chained replay, head mirror ==
worktree bytes for both files, generator BOM kept / analyzer no BOM, uniform CRLF, inserted-line counts
exactly as claimed.

| gate | landed (R65) | m66e | verdict |
|---|---|---|---|
| 17 partials (official) | 0 fully OK | 5 files up, 1 fully OK | `SAME=11 IMPROVED=5 REGRESSION=0 MOVED=1 ERR=0` |
| battery 24 | 91/104, 17 clean | fs2 5/10→6/10, fsrepro 6/7→7/7, 18 clean | `IMPROVED=2 SAME=22 REGRESSION=0 MOVED=0` |
| canary 4 | 4 shas | identical | `SAME=4 REGRESSION=0` |
| R66 repro battery 7 | 12/23, 0 clean | **22/23, 6 clean** | `IMPROVED=7 REGRESSION=0 MOVED=0` (residual = `r66d3_pred::v6`, kept by design) |
| **402 A/B** | 5693/5746, clean 385 | **5698/5746, clean 386** | `SAME=396 IMPROVED=5 REGRESSION=0 MOVED=1 ERR=0`, 4 shards, every command < 24 s |
| product blast | — | 6 products changed | `identical=396 changed=6 unresolved=0`, changed set == the 6 touched files |
| Σ\|orig−decomp\| | 418 | **328** | −90 |
| Σ jumpdiff / Σ truediff | 196 / 11977 | **184 / 9405** | −12 / −2572 |
| defect functions (402) | 53 | **48** | −5 |
| strict ruler (17) | 672/749, 77 defects | **677/749, 72 (47/18/7)** | +5; **5 defective function NAMES cleared, 0 newly defective** (the 4 `+NEW` rows are reclassified defects of already-defective functions with smaller gaps) |

Intermediate arms kept for audit: `m66b` (4 edits, `IMPROVED=4`), `m66d` (+diag2 = 7 edits), `d3`, `p1`, `p3`, `p4`.
Decision: land `m66e` — it is the union of all six batches' adoptable candidates, additive on every ruler.

diag2 (quote, 11 fn + R65's `load_bars_from_hundsun` cost; arms p1 namecallee / p2 storeepi / p3 prefixparts),
diag3 (real_quote + klinedata; hunk tables done, attribution in progress). Any adopted spec must be merged on
top of `m66b` and re-swept (17 + battery + canary + strict + 402 + blast) before landing.
