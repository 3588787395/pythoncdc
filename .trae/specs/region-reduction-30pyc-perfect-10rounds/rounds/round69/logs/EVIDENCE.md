# Round 69 — EVIDENCE（原始读数，可复核）

所有读数都在本轮门禁日志里，路径前缀 `rounds/round69/`（命令与镜像脚本前缀 `center/`）。
判定臂：`landed` = R68 落地字节（本轮起点），`m69` = 中心镜像 `center/mirr_m69`
（`mkfinal69.py m69` 合并 spec → `mbuild69c.py m69` 重建），落地后 `landproof mirr_m69`
= 33/33 same。候选单臂：`d1d` / `d2a` / `d5i`（三件采纳件各自的独立镜像）。

## A. 起点字节指纹与起点读数（阶 B/C 实测）

| 文件 | R68 HEAD（landed 臂起点） | R69 落地（落地后实测） |
|---|---|---|
| `core/cfg/region_analyzer.py` | 1 753 093 B，sha256 `27089306098c35dc1f3a`，无 BOM，CRLF 28 015，裸 LF 0 | 1 754 683 B，sha256 `c6cf9d568dd317b4c46b…`，无 BOM，CRLF 28 015，裸 LF 0，28 016 行 |
| `core/cfg/region_ast_generator.py` | 3 193 950 B，sha256 `3cd0fcd6cbd7446c3703`，BOM 有，CRLF 51 368，裸 LF 0 | 3 199 517 B，sha256 `240ecbaea36eeb7073be…`，BOM 有，CRLF 51 368，裸 LF 0，51 369 行 |
| `core/cfg/comprehension_generator.py` | 108 192 B，sha256 `be5490c1118c7199fe0a` | **未改**，sha 不变 |

`git diff --numstat core/cfg/`：analyzer `+20 / −2`、generator `+59 / −0`（comprehension 无差异）。
官方尺起点（`dump/index_before69.json`，轮初）：`status {ok:392, partial:10}`、`matched 5709/5746`
= 99.36%。10 支合集起点（`dump/landed10.jsonl`）：缺陷函数 **37**、`Σ|Δ| **256**`、`Σhunk **151**`、
`Σtrue-diff **5911**`、官方匹配 **412/449**。严格尺起点（`dump/strict10_open_r69.txt`）：
**ok 433/488、缺陷函数 55**。金丝雀起点 4 sha：`4d41187e356544e0` / `af77224b34b203c4` /
`e711b8ea86d49a15` / `9d09af09249da177`。45 项电池起点 `182/200`、缺陷 18。

## B. 落地 3 处编辑（行内标签 = 最终落地字节实测）

合并器输出：`specs/m69_region_analyzer.py.json`（1 edit，来自 `cand_r69d1_d`）、
`specs/m69_region_ast_generator.py.json`（2 edits，来自 `cand_r69diag2_a` ×1、
`cand_r69_loop_hdr_import` ×1）；链式锚点断言全过。标签实测
（`grep -o '\[R69[^\]]*\]'` 落地文件）：

- analyzer 2 处：`[R69 fix]`、`[R69-diag1 链尾合并豁免·臂末判据放宽]`（同一编辑块）
- generator 2 处：`[R69-diag2-A while cond-chain prefix: a complete non-Assign statement must
  not be dropped]`、`[R69-diag5 A1]`
- comprehension 0 处（未改）

落地链路：`land69.py --apply` 先 dry-run 断言「spec 重放 == `mirr_m69` 镜像字节」逐文件通过，
再写入仓库；`logs/gate/Land69_replay_r69.txt`（`scripts/replay69.py` 对 R68 HEAD blob 重推演：2 文件 `replay == measured mirror bytes: OK` 与 `repository bytes == replay == mirror: OK`）为 replay 证据，`logs/gate/landproof` 结果
`33 core files, same=33 diff=0`。

## C. 门禁原始读数

### G0 语法与形态（`logs/gate/G0_syntax_form_r69.txt`）
```
core/cfg/region_ast_generator.py   bytes=3199517 sha=240ecbaea36eeb70 BOM=True  CRLF=51368 bareLF=0 ast/py_compile OK cross-pattern=2
core/cfg/region_analyzer.py        bytes=1754683 sha=c6cf9d568dd317b4 BOM=False CRLF=28015 bareLF=0 ast/py_compile OK cross-pattern=1
core/cfg/comprehension_generator.py bytes=108192  sha=be5490c1118c7199 BOM=False CRLF=2016  bareLF=0 ast/py_compile OK cross-pattern=0
cross-layer pattern set (landed=2/1/0, merged=2/1/0, new=0): zero-new OK
```

### G1 10 支合集（`logs/gate/G1_targets_r69.txt`）
```
IMPROVED=2 SAME=7 MOVED=1 REGRESSION=0 ERR=0 ; file fully cleared: none
trade_live_broker 108/119 d=11 -> 109/119 d=10 IMPROVED ; quote 70/81 d=11 -> 72/81 d=9 IMPROVED
risk_calculation/__init__ 33/35 d=2 -> 33/35 d=2 MOVED（集合 [71,68] -> [71,70]）
其余 7 支 SAME；官方 412/449 -> 415/449（gap 37 -> 34）、Σ|Δ| 256 -> 195、Σhunk 151 -> 147、Σtrue-diff 5911 -> 5234
```

### G2 金丝雀（`logs/gate/G2_canary_r69.txt`、`G2_strict_canary_r69.txt`、`dump/{landed,m69}_canary.jsonl`）
```
landed quotation.pyc 143/143 sha 4d41187e356544e0 -> m69 SAME
landed market_time.pyc 10/10 sha af77224b34b203c4 -> m69 SAME
landed datetime_func.pyc (IQCommon) 26/26 sha e711b8ea86d49a15 -> m69 SAME
landed datetime_func.pyc (IQData) 25/25 sha 9d09af09249da177 -> m69 SAME
strict: 两臂均 STRICT TOTAL ok=209 / functions=211 / defects=2（余 2 = change_his_to_forward #250、get_trend #10）
```

### G3 批量（`logs/gate/G3_batch_r69.txt` = 同名 `.log` 的入库副本；仓库 `.gitignore` 忽略 `*.log`，故 `run402_*` 亦以 `logs/dump/run402_{landed,m69}_r69.txt` 入库）
```
verified_pyc 402 | ok_pyc 392 | partial_pyc 10 | failed_pyc 0
total_functions 5746 | matched_functions 5712 | cumulative_match_rate 99.41%
Traceback 0 | FAIL-line 0（g8_artifacts69.py 复核）
```

### G4 `stats`（`logs/gate/G4_stats_r69.txt`）
与 G3 同读数（5746 / 5712 / 99.41%，ok 392、partial 10）。

### G4′ 严格尺·发布产物（`logs/gate/G4p_strict_after_r69.txt`）
```
trade_live_broker ok 106/123 bad 17 -> ok 107/123 bad 16
quote              ok 74/89  bad 15 -> ok 76/89  bad 13
risk_calc/__init__ ok 34/37  bad 3  -> ok 34/37  bad 3（函数内 seq_len 68 -> 72）
其余 7 支逐字不变；STRICT TOTAL ok 433/488 -> 436/488 ; defects 55 -> 52（NEW=0）
```

### G5 索引审计（`logs/gate/G5_index_audit_r69.txt`）
```
entries HEAD=402 worktree=402 ; added=0 removed=0 ; key-shape diffs=0
round-stamp-only=400  substantive=2
  trade_live_broker: bytecode_match_rate 0.907563025210084 -> 0.9159663865546218 ; matched 108 -> 109
  quote:             bytecode_match_rate 0.8641975308641975 -> 0.8888888888888888 ; matched 70 -> 72
matched HEAD=5709/5746  NEW=5712/5746  delta=+3
```

### G5′ 产物 blast（`logs/gate/G5p_blast_r69.txt`）
```
products identical=397 changed=5 unresolved=0
  CHANGED history_data_source / risk_calculation/__init__ / trade_live_broker / quote / pboxAccount_jupyterhub
official instruction-gap sum landed=256  m69=195 ; matched 5709 -> 5712 ; fully matched 392 -> 392
history_data_source: landed [] / m69 []（官方空；严格 26/28 -> 28/28，d1d 归因）
pboxAccount_jupyterhub: 官方/严格读数逐字不变，仅产物文本 elif -> else: if
risk_calculation/__init__: [71,68,7,19] -> [71,70,7,11]
trade_live_broker: after_trading_cancel_order [155,155,3,122] 消失（缺陷 11 -> 10）
quote: check_limit [330,311,2,248] 与 initImagedata [243,225,0,190] 消失、get_real_from_zeromq [703,678,0,660] -> [703,700,1,551]
REGRESSED=0
```

### G6 电池（`logs/gate/G6_battery_{prev,post,ext}_r69.txt`、`G6_battery_cands_r69.txt`）
```
45 项（落地前，4 候选列）: candidate columns worse-than-landed on 0 repro(s)
45 项（落地后）:           landed 182/200、缺陷 18、candidate columns worse-than-landed on 0 repro(s)
82 项（扩展，含 round68/69 见证）: matched 318/356、缺陷函数 37、worse 0  ← R70 基线
```

### G7 见证（28 支，`logs/gate/G7_witness_repro69.txt`）
```
test_repros/round68_diag1/e1.pyc 3/4 bad=1 -> 4/4 bad=0 IMPROVED
其余 27 支 SAME；TALLY SAME=27 IMPROVED=1 REGRESSED=0 ERR=0 PASS
```

### G8 产物体检（`logs/gate/G8_artifacts_r69.txt`）
```
index entries 402 | OK.py present 402 (missing 0) | py_compile bad 0
batch G3 Traceback 0 | FAIL-line hits 0（SyntaxWarning-only 文件按惯例容忍）
```

## D. 402 A/B（阶段 D 全部实测，锚点在 `logs/gate/`）

- 落地前 402 臂（`dump/landed402_r69.jsonl`）与落地后 402 臂（`dump/m69_402.jsonl`）由
  `run402_*.log` 重建；`blast67.py` 逐文件比对 → §C G5′。
- `audit5_g5_67.py` 对 `pyc_index.json` 逐条审计 → §C G5（substantive=2 全改善、
  round-stamp-only=400）。
- 本轮回写索引后 `site-packages` 侧恰有 5 支 `*OK.py` 随工具链重写（= blast changed 集合），
  **未手改任何生成文件**。

## E. 五批判定原始读数（全部留档 `batches/`）

- 逐件五连：`dump/{d1d,d2a,d5i}_all10.jsonl`、`{d1d,d2a,d5i}_canary.jsonl`、
  `repro65_{d1d,d2a,d5i}.jsonl`、`strict10_{d1d,d2a,d5i}.json`、`syn_{d1d,d2a,d5i}.jsonl`；
  汇总 `scripts/cadelta69.py` 输出（第三列 `Sigmajumpdiff` = Σ m[3] = **hunk 计数之和**）：
  ```
  landed: defects=37 Sigma|d|=256 Sigmajumpdiff=151
  d1d:   defects=36 Sigma|d|=256 Sigmajumpdiff=148   （after_trading_cancel_order 155/155 转绿：hunk 3、true-diff 122 消失；该支 |Δ| 本为 0 ⇒ Σ|Δ| 不变）
  d2a:   defects=35 Sigma|d|=197 Sigmajumpdiff=150   （quote check_limit/initImagedata 转绿 + get_real_from_zeromq 703/678 → 703/700）
  d5i:   defects=37 Sigma|d|=254 Sigmajumpdiff=151   （risk_calc [71,68] → [71,70]，hunk 7 不变、true-diff 19 → 11）
  ```

  ADR-1 归档说明：d1d 为「真缺陷函数转绿」且 Σ|Δ| 不升（256→256）、Σhunk 151→148、严格 106/123 → 107/123、合成 `r69d1_atco` 2/2 咬合、金丝雀 SAME=4 ⇒ 采纳；d2a/d5i 按缺失/过冲族判据直接满足（Σ|Δ| 净减 256→197 / 256→254）。
- **回退件（B4）**：`specs/cand_r69d4_orchain_legit.json` 中心复测 `order_api` 官方
  `Σ|Δ| 19 -> 57`（`future_order 101/92 -> 101/79`、`option_order 83/73 -> 83/48`）、
  合成 `r69d4_orchain` **2/6 -> 2/6** 不咬合 ⇒ 否决，留档 `batches/b4_diag4/specs/`。
- **NONE 批（B3）**：探针实测 and 链游走在 guard 尾 or 子链必断（`kline_datetime_list #151`
  与 `api_base::get_history_df #419` 同签名极性反），修复需 6 读点结构改造 ⇒ 过重，
  `batches/b3_diag3/FACTS.md` + `synth/s_polarity.py` 留档。
- **代理自否决（B1）**：`cand_r69d1_{a,b,c}.json`（a 金丝雀 143→139、c 产物
  `UnboundLocalError`）留档 `batches/b1_diag1/specs/`。

## F. 见证与复现登记

- `test_repros/round69_diag1/`：`r69d1_atco.pyc` 1/2→**2/2**、`r69d1_gma.pyc` 1/2→1/2（族乙未修）
- `test_repros/round69_diag2/`：`r69diag2_whilepre.pyc` 1/2→**2/2**、`r69diag2_whilepre2.pyc` 2/2→2/2（对照）
- `test_repros/round69_diag3/`：`s_polarity.pyc` 1/2→1/2（**未修**，诚实见证）
- `test_repros/round69_diag4/`：`r69d4_orchain.pyc` 2/6→2/6（**回退件不咬合**，留档）
- `test_repros/round69_diag5/`：`t_n2.pyc`、`t_n3.pyc` 各 1/2→**2/2**、`try_A.pyc` 1/2→1/2（形状陷阱对照）
- 合成量测原始件：`dump/syn_landed{1..5}.jsonl`、`dump/syn_m69_{1..5}.jsonl`；
  每目录 README 记 landed → m69 读数；`.pyc` 本机编译、仓库只入库 `.py`。

## G. 残余缺陷登记（落地后，逐支与 OUTCOME §7 映射）

`logs/gate/G4p_strict_after_r69.txt` + `logs/dump/strict10_m69.json`：

| 支 | 官方（缺陷 / `\|Δ\|` / hunk） | 严格（ok/总、缺陷） | 家族 |
|---|---|---|---|
| `trade_live_broker` | 10 / 85 / — | 107/123、16 | 多 hunk 大文件（`get_max_amount`、`_process_order`） |
| `quote` | 9 / 62 / — | 76/89、13 | 位移族残余 |
| `real_quote` | 4 / 5 / — | 41/45、4 | 位移/线性化通道 |
| `klinedata` | 2 / 1 / — | 58/63、5 | 位移族（`kline_datetime_list` 极性反） |
| `fileio_utils` | 2 / 4 / — | 13/15、2 | 改善后仍红 |
| `trade_info_utils` | 1 / 2 / — | 37/41、4 | 改善后仍红 |
| `api_base` | 1 / 0 / — | 26/27、1 | 极性反（`get_history_df`） |
| `order_api` | 2 / 19 / — | 33/36、3 | R50 kwarg 槽位 bail |
| `realtime_event_source` | 1 / 11 / — | 11/12、1 | 重复发射（[R23-A]） |
| `risk_calculation/__init__` | 2 / 6 / — | 34/37、3 | try/IMPORT-from-value（B5 后残 2） |
| **合计** | **34 / 195 / 147** | **436/488、52** | gap 34 |
