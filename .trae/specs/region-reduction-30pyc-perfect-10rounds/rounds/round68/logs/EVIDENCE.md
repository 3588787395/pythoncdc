# Round 68 — EVIDENCE（原始读数，可复核）

所有读数都在本轮门禁日志里，路径前缀 `rounds/round68/`（命令与镜像脚本前缀 `center/`）。
判定臂：`prev` = `center/mirr_prev`（R67 HEAD 字节，`mkmirr_prev68.py` 复原），`landed` = 落地字节
（落地前测量臂 `center/mirr_m68`，落地后 `landproof mirr_m68` = 33/33 same）。

## A. 起点字节指纹（阶段 B/C 实测，同一批镜像）

| 文件 | R67 HEAD（prev 臂） | R68 落地（landed 臂） |
|---|---|---|
| `core/cfg/region_analyzer.py` | 1 742 308 B，sha256 `af8cc88b9f89779b3ef0`，无 BOM，CRLF 27 873，裸 LF 0 | 1 753 093 B，sha256 `27089306098c35dc1f3a`，无 BOM，CRLF、裸 LF 0，27 998 行 |
| `core/cfg/region_ast_generator.py` | 3 153 249 B，sha256 `f712bc20d7ad44542e18`，BOM 有，CRLF 50 782，裸 LF 0 | 3 193 950 B，sha256 `3cd0fcd6cbd7446c3703`，BOM 有，CRLF、裸 LF 0，51 310 行 |
| `core/cfg/comprehension_generator.py` | 108 192 B，sha256 `be5490c1118c7199fe0a` | **未改**，sha 不变 |

`git diff --numstat core/cfg/`：analyzer `+126 −2`、generator `+591 −64`（comprehension 无差异）。
官方尺起点（`pyc_index.json`，轮初）：`status {ok:387, partial:15}`、`matched 5701/5746`、99.22%。
严格尺起点（15 支，`dump/landed15_strict.json`）：**ok 632/700、缺陷函数 68**。

## B. 落地集 17 处编辑（标记为最终落地字节上的标记）

合并器输出：`m68_region_analyzer.py.json`（6 edits，来源 `cand_r68_wizapib` ×2、`cand_r68b2_andchain`、
`cand_r68_b1` ×3）+ `m68_region_ast_generator.py.json`（11 edits，来源 `cand_r68b3_combo` ×3、
`cand_r68b5_initc` ×5、`cand_r68b2_final_gen` ×2、`cand_r68b3_thenfold` 归并 1）。链式锚点断言全过。
标签实测（`grep -o '\[R68[^\]]*\]'` 落地文件）：

- analyzer 6 处：`[R68-diag5]`×2、`[R68-b2 and-chain]`×1、`[R68-B]`×1、`[R68-E·有 merge 收集的剪枝守卫]`×1、
  `[R68-C·循环豁免收紧]`×1。
- generator 13 处标签命中 / 11 处编辑：`[R68-b3 修复]`×2、`[R68-b2 cell-swap]`×2、`[R68-diag3 C3]`×2、
  `[R68-diag6]`×2、`[R68-diag6/b5 init-if]`、`[R68-diag6/b5 init-if fold]`、`[R68-D4-ORCHAIN-TAIL]`、
  `[R68-diag6/b5]`、`[R68]`（该条为 R67 既有，`git show HEAD:` 命中同文）。
  **1 处编辑（then-fold 调用点）无行内标签**，三要素在 helper `_fold_header_then_continuation`
  docstring（L10509 `[R68-b3 修复]`）；已记入 OUTCOME §8 技术债。

`logs/dump/merged_comments_r68.txt` 逐 edit 打印 anchor + 抽取到的注释行，是本节的机器凭据。

## C. 门禁原始读数

### G0 语法与形态（`logs/gate/G0_syntax_form_r68.txt`）

```
G0 OK region_analyzer.py     bytes=1753093 sha256=27089306098c35dc1f3a nl=CRLF bareLF=0 BOM=False lines=27998
     cross-level pattern HEAD=2 WORK=2 (all pre-existing: True)
G0 OK region_ast_generator.py bytes=3193950 sha256=3cd0fcd6cbd7446c3703 nl=CRLF bareLF=0 BOM=True lines=51310
     cross-level pattern HEAD=3 WORK=3 (all pre-existing: True)
G0 OK comprehension_generator.py bytes=108192 sha256=be5490c1118c7199fe0a nl=CRLF bareLF=0 BOM=False lines=2017
     cross-level pattern HEAD=0 WORK=0 (all pre-existing: True)
G0 FORM: no new region.entry-in-r.blocks patterns, py_compile+ast.parse all OK
```

### G1 完全 OK 靶（`G1_single_scheduler.txt` / `G1_single_flyAccount.txt`）

```
scheduler:    decompile_status ok  45/45  match_rate 100.00%  missing_in_decomp []  extra_in_decomp []
              strict: functions 52, ok 52, bad []
flyAccount:   decompile_status ok  23/23  match_rate 100.00%  missing_in_decomp []  extra_in_decomp []
              strict: functions 23, ok 23, bad []
```

### G2 金丝雀（`G2_canary_post68.txt` = 同名 `.log` 的入库副本、`G2_strict_canary_r68.txt`、`dump/landed_canary_post68.jsonl`）

```
landed quotation.pyc     143/143  sha 4d41187e356544e0   （与 rounds/round67/logs/dump/canary_landed.jsonl 同值）
landed market_time.pyc    10/10   sha af77224b34b203c4   同值
landed datetime_func.pyc  26/26   sha e711b8ea86d49a15   同值
landed datetime_func.pyc  25/25   sha 9d09af09249da177   同值
strict: quotation 148/150（bad = change_his_to_forward #250、get_trend #10）、market_time 10/10、
        datetime_func 26/26、25/25  ⇒ 合计 209/211，缺陷集逐字同 R67
```

### G3 批量（`G3_batch_r68.txt` = 同名 `.log` 的入库副本，background，exit 0；仓库 `.gitignore` 忽略 `*.log`）

```
verified_pyc 402 | ok_pyc 392 | partial_pyc 10 | failed_pyc 0
total_functions 5746 | matched_functions 5709 | cumulative_match_rate 99.36%
```

### G4 `stats`（`G4_stats_r68.txt`）= G3 同读数（5746 / 5709 / 99.36%，ok 392、partial 10）。

### G4′ 严格尺·发布产物（`G4p_strict_after_r68.txt`，15 支）

```
trade_live_broker 106/123 bad 17 | quote 74/89 bad 15 | real_quote 41/45 bad 4 | klinedata 58/63 bad 5
trade_info_utils 37/41 bad 4 | order_api 33/36 bad 3 | risk_calc/__init__ 34/37 bad 3 | fileio_utils 13/15 bad 2
flyAccount 23/23 bad 0 | wizard_quant_api 54/56 bad 2 | scheduler 52/52 bad 0 | logger 63/64 bad 1
api_base 26/27 bad 1 | realtime_event_source 11/12 bad 1 | matcher 16/17 bad 1
TOTAL ok=641/700 defects=59   （轮初 632/700 defects=68；FIXED 13、NEW 4 全为既有函数换 kind）
```

NEW=4 明细：`api_base seq_len→seq_diff`、`fileio write seq_diff→seq_len`、
`matcher seq_diff→target_diff`、`ipo_stocks_order seq_len→seq_diff`（第 4 支不在本 15 支窗口内，
见 `dump/m68_strict.json` 与 `dump/landed15_strict.json` 对比）。

### G5 索引审计（`G5_index_audit_r68.txt`）

```
entries HEAD=402 worktree=402 | added=0 removed=0 | key-shape diffs=0
round-stamp-only=395  substantive=7
substantive: klinedata 42→43 | wizard_quant_api 52→53 partial→ok | trade_info_utils 38→39 |
             matcher 16→17 partial→ok | scheduler 44→45 partial→ok | logger 29→30 partial→ok |
             flyAccount 21→23 partial→ok
status HEAD {ok:387, partial:15} → NEW {ok:392, partial:10};  matched 5701 → 5709 (delta +8)
```

### G5′ 产物 blast（`G5p_blast_r68.txt`）

```
products identical=388 changed=14 unresolved=0
official instruction-gap sum prev=296 landed=256
matched functions prev=5701 landed=5709
fully matched files prev=387 landed=392
CHANGED: klinedata | api_data | wizard_quant_api | fileio_utils | resource_utils | trade_info_utils |
         api_base | matcher | function | trade_live_broker | scheduler | quote | logger | flyAccount
（improved=7：klinedata/wizard/trade_info_utils/matcher/scheduler/logger/flyAccount；
  regressed=0；moved=7：其中 api_data/resource_utils/function/quote 缺陷集合逐字相同、
  fileio/api_base/trade_live_broker 为改善量级移动）
逐支读数样例：
  fileio write   [637,637,4,519] → [637,636,0,38]
  api_base get_history_df [1742,1740,14,1263] → [1742,1742,11,89]
  trade_info_utils get_trade_list [339,323,14,148] 消失、trade_operation [304,302,2,40] 保留
  wizard params_analysis [133,126,1,117] 消失
  klinedata get_all_real_daily_kline [188,187,3,26] 消失
```

### G6 电池（`G6_battery_{prev,landed,table}_r68.txt`，`closeout67.py battery` + `battable67.py`）

```
repro pycs discovered: 45（round63 批次 + 11 枚钉住的 R62 见证）
items=45  matched prev=174/200  landed=182/200
defect-functions prev=26 landed=18 | fewer=6 equal=39 WORSE=0
errors=0 []
改善 6 项：r63b5_w1 | r64d5_contsink | r67d3_lostreturn | r67d3_return_sink | r67d3_return_tern |
          r67d6_whiletrue_headif（1/2 → 2/2）
```

### G7 本轮见证 28 支（`G7_witness_repro68.txt`，`dump/repro68_{prev,landed}.jsonl`）

```
TALLY SAME=16 IMPROVED=10 REGRESSION=0 MOVED=2 ERR=0  (unpaired lists=0)
files fully matched: a=10 b=20
IMPROVED: r68b2_cell_tuple 2/3→3/3 | r68b2_cell_tuple_body 2/3→3/3 | r68d4_s3 3/5→5/5 |
          r68b4_apib_inc7 1/2→2/2 | r68d5_trymerge 1/2→2/2 | r68d6_handler_return2 1/3→3/3 |
          r68d6_tuple_ternary 3/4→4/4 | r68d6_tuple_ternary2 1/3→3/3 | …
MOVED:   r68b3_headif（w1 [59,59,2,19]→[59,59,3,8]、w2 同形、w3 [54,54,2,24]→[53,52,1,16]，缺陷数不变）
```

## D. 402 A/B 与索引（阶段 A/A 后跑）

- 双臂 sweep：`h62 run --arm=prev/landed --list=all402.txt` → `dump/prev402.jsonl`、`dump/landed402.jsonl`
  （各 402 条），`blast67.py` 得 G5′ 读数（上表）。
- 五批单臂 15 支矩阵（`dump/b{1..5}_all15.jsonl`、`m68_all15.jsonl`，逐支 `matched/total`）：

| pyc | b1 | b2 | b3 | b4 | b5 | m68 |
|---|---|---|---|---|---|---|
| matcher | **17/17** | 16/17 | 16/17 | 16/17 | 16/17 | 17/17 |
| klinedata | 42/45 | **43/45** | 42/45 | 42/45 | 42/45 | 43/45 |
| scheduler | 44/45 | **45/45** | 44/45 | 44/45 | 44/45 | 45/45 |
| trade_info_utils | 38/40 | 38/40 | **39/40** | 38/40 | 38/40 | 39/40 |
| logger | 29/30 | 29/30 | **30/30** | 29/30 | 29/30 | 30/30 |
| wizard_quant_api | 52/53 | 52/53 | 52/53 | **53/53** | 52/53 | 53/53 |
| flyAccount | 21/23 | 21/23 | 21/23 | 21/23 | **23/23** | 23/23 |
| 其余 8 支 | 各臂均 = 轮初值（不变） | | | | | |
| **15 支合计 matched/617** | 573 | 574 | 574 | 573 | 574 | **580**（轮初 prev=572） |

（合计口径：`dump/b{1..5}_all15.jsonl`、`dump/m68_all15.jsonl` 逐条 `matched_functions` 求和，
分母 617 = 15 支 `total_functions` 之和；轮初 prev = 572。）

  合并集 15 支 h62 `ab`（`dump/m68_all15.jsonl` vs `dump/landed15*.jsonl` 对比输出）：
  **SAME=4 IMPROVED=7 REGRESSION=0 MOVED=4 ERR=0**，完全匹配文件 0→5。

## E. 五批判定（全部实测，机器锚点在 `batches/`）

| 批 | 交付 | 单臂读数 | 判定 |
|---|---|---|---|
| B1 `diag1` | `cand_r68_b1.json`（analyzer 3） | `matcher` 16→17、其余 14 支不变、金丝雀 SAME=4、电池无 worse | **采纳** |
| B2 `diag3` | `cand_r68b2_andchain.json` + `cand_r68b2_final_gen.json` | `klinedata` 42→43、`scheduler` 44→45、REG=0 | **采纳** |
| B3 `diag4` | `cand_r68b3_combo.json`（generator 4） | `trade_info_utils` 38→39、`logger` 29→30、REG=0 | **采纳** |
| B4 `diag5` | `cand_r68_wizapib.json`（analyzer 2） | `wizard` 52→53、`api_base` hunk 14→11、REG=0 | **采纳** |
| B5 `diag6` | `cand_r68b5_initc.json`（generator 4） | `flyAccount` 21→23、REG=0 | **采纳** |
| `diag2` | `cand_r68_else_join_cut.json` | ADR-1 实测 `matcher 715/715→713/466`、`quote 70/81→64/81` | **撤回**（不进合并集） |

五批各自的 `dump/b{1..5}_{canary,bat}.jsonl` 与 `batches/*/FACTS.md` 是本表的原始凭据；
合并后 `m68` 一次过 G0–G7（无二次修正）。

## F. 见证与电池登记

- `test_repros/round68_diag{1,3,4,5,6}/`：28 支 `.py` + 本机编译 `.pyc` + 每目录 `README.md`
  （来源工作区、采纳 spec、消费者、prev→landed 读数表）。`.pyc` 不入库（`.gitignore`）。
- 批次凭据归档 `batches/{b0_diag2,b1_diag1,b2_diag3,b3_diag4,b4_diag5,b5_diag6}/`：每批
  `FACTS.md` + `specs/*.json` + `synth/*.py`（`b0_diag2` = 撤回件 `cand_r68_else_join_cut.json` 留档；
  含未采纳的中间候选，如 `cand_r68b1_a..j`、`cand_r68_sinkcont*`、`cand_r68_orchain_tail*`、
  `cand_r68b5_a2as/initif` 等，便于下轮复用或否证）。
- 门禁 G8（`logs/gate/G8_artifacts_r68.txt`，脚本 `logs/g8_artifacts68.py`）：402/402 `*OK.py` 在位、
  `py_compile` bad=0（仅 SyntaxWarning）。
- 仪器与镜像脚本 `logs/*.py`：`mkfinal68.py`、`mbuild68c.py`、`land68.py`、`mkmirr_prev68.py`、
  `mkreadme68.py`、`archive68.py`；基线 dump 在 `logs/dump/`（`index_before68.json`、
  `prev402.jsonl`、`landed402.jsonl`、`repro68_{prev,landed}.jsonl`、`m68_*`、`b1..b5_*`）。

## G. 残余缺陷登记（本轮落地后仍红，逐支来自 `G4p_strict_after_r68.txt` + 索引）

| pyc | 官方 | 严格 | 主要残余 |
|---|---|---|---|
| `trade_live_broker` | 108/119 | 106/123（17） | `_process_order` 396/454、`_process_cancel_order` seq_len、16 hunk |
| `quote` | 70/81 | 74/89（15） | 位移族（`initImagedata`、`get_real_from_zeromq` 等） |
| `real_quote` | 40/44 | 41/45（4） | `one_prod_to_ndarray`、`get_tick_direction` seq_len |
| `klinedata` | 43/45 | 58/63（5） | `kline_datetime_list` hunks 9、`get_multiminute_his_data` |
| `trade_info_utils` | 39/40 | 37/41（4） | `get_trade_status`/`set_trade_status` target_diff |
| `order_api` | 32/34 | 33/36（3） | `future_order`/`option_order` seq_len、`base_order target_diff #136` |
| `risk_calculation/__init__` | 33/35 | 34/37（3） | try/loop-exit JUMP_FORWARD 族 |
| `fileio_utils` | 12/14 | 13/15（2） | `acquire` hunks 3；`write` 本轮改善后仍红（见 OUTCOME §6） |
| `api_base` | 24/25 | 26/27（1） | `get_history_df` 11 条 true-diff |
| `realtime_event_source` | 11/12 | 11/12（1） | handler 回边 continue 族残留 |
| 双尺全清（本轮达成） | `scheduler` 45/45、`flyAccount` 23/23 | 52/52、23/23 | — |
