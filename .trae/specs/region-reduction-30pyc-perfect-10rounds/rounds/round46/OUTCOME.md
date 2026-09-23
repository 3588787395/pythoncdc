# Round 46 结果：落地 R46-B（链尾 merge 块是「链后兄弟区域」入口时，发射责任是整个区域而非裸语句）

落地铁笔：本轮 `core/` 改动为单文件单处插入，与实测镜像臂 `D:/Temp/r43gate/mirr_r46bB` 逐字节相同。

- `core/cfg/region_ast_generator.py`：`e743b6de1d8efc014da8` → `b8bfc794dc6c852e7d9c`，len 2 997 983 → 3 000 351，CRLF 48 592 → 48 620、裸 LF 0、UTF-8 BOM 保留
- `core/cfg/region_analyzer.py`：未改动，仍为 `55a9f61b9b0703063d44`（len 1 681 035，CRLF 27 023、裸 LF 0）

## 一、开工靶池（实测 landed `cc71dd2d`）

`stats`：375 ok / 27 partial / 0 failed，5660/5746。靶池 27 支部分失败文件（清单 `g1pool46.txt`，
去重后 27 行）；电池/锚点基线沿用 Round 45（`bat45.jsonl` 143 支、`anch45.jsonl` 109 支、
`g4_r45a_full544.jsonl` 为其 a 侧，臂 `mirr_r45a` 的 generator 已核验与落地字节等值）。

本轮三条诊断线并行开工：线 B（代理，链后兄弟区域发射侧）、线 C（代理，等长 MOVE 族）、
线 D（编排方一手，`flyAccount :: init_connection` 反转 if + 丢失出口跳）。
**发货判据只认 G4 官方尺增益**：线 B 的 R46-B 命中，线 C、线 D 均官方尺中性 ⇒ 移交 Round 47。

靶文件 `site-packages/fly/data/quote_handler.pyc` 开工时 `51/57`，其中
`<module>.get_index_stocks_local` 官方 mism `[150, 60, 0, 92]`（跳转差已为 0、条数缺 90），
strict `seq_len orig=151 decomp=56`。

## 二、根因（发射侧：merge 块的归属区域以它为入口时，裸语句补发吃不下整段区域）

Round 45 的 R45-A 关掉了「链的 merge 块被链内某个后代 `IfRegion` 当作 **else 臂**认领」这一格；
没关掉的是「链的 merge 块是**其后兄弟区域的入口块**」。此时该块自带一个完整的条件结构：
按 R45-A 的动作写「该块的裸语句」只打印它的前导赋值，**块终止符携带的那个 `if` 连同两臂与整段
嵌套体一起消失**。归属层面仍有人认领（原则 2 名义满足），发射责任仍空一档。

真实靶（`lineB_ANALYSIS.md` §2，落地核只读转储 `probe_qh_gisl.txt` / `probe2_gisl.txt`）：

```
IfRegion IF_ELIF_CHAIN entry=B0 exit=B344 cond=B0 then=[B10] else=[B88,…,B340] merge=B344
   blocks=[B0,B10,B88,B170,B214,B298,B302,B340]        <-- merge B344 不在链的归属集内
IfRegion IF_THEN_ELSE entry=B344 cond=B344 then=[B424] else=[B428,B546,B578,B808,B624,B804]
   parent=IfRegion@B214                                <-- B344 是该区域的 ENTRY，且它是链的后代
   blocks=[B344,B424,B428,B546,B578,B624,B804,B808]
ownership:  B344 term=POP_JUMP_FORWARD_IF_FALSE 428 succ=[B424,B428] preds=[B302,B10] owner=IfRegion(IF_THEN_ELSE)
发射调用（落地核）：IF_THEN_ELSE entry=B344 从未进入 _generate_region / _generate_if
```

合成见证 `r46b_witness.py :: r46b_01_tail_region_at_merge` 与真实靶逐字段同形
（链 `merge=B64` 不在 blocks 内、`IF_THEN_ELSE entry=B64` 为其后代 `IfRegion@B32` 的入口、
外层链 `final_else=[]` 而子链非空）：落地核 strict `seq_len orig=56 decomp=33`。

R46-B 为发射侧同层判据，插在 R45-A 的 `_is_implicit_return_block` 分支内（即只在该分支已经命中、
判定要补发 merge 块之后才细分「补发裸语句」还是「补发整区域」）。六条合取全读结构事实：
① 该块有归属区域 owner；② owner 非本链、亦非本链之父；③ `owner.entry is` 该块
（它是 owner 的入口，而非 owner 臂内的块 —— R45-A 的见证在此为假）；④ 该块在 `owner.blocks` 内；
⑤ `id(owner)` 未在 `_generated_regions`；⑥ `owner.blocks` 与 `generated_blocks` 不相交。
命中时 `self._generate_region(owner)` 整区域发射，接在链 `result` 之后；否则逐字节沿用 R45-A 的
`_generate_block_statements(merge)`。只加发射责任，不改归属树、不改任何块的角色判定。

## 三、门禁序列（严格串行，全部在最终发货字节上复跑）

- **G0 合成见证**（`g0_r46.py`，三支电池共 17 个 code object：线 B 见证 5 个 +
  R45-A 自己的见证 `r45e_witnesses.py` 4 个 + R45-A 对照 `r45e2_controls.py` 8 个）：
  落地核 `defective=1/5`（`<module>.r46b_01_tail_region_at_merge`）→ 候选臂 `defective=0/5`；
  逐 code object 指令签名比对 **16 个 IDENTICAL、唯一 DIFFERS 就是见证本身**
  ⇒ R45-A 的两支电池在本判据下完全惰性。
- **G1 靶 + 已失败文件池**（27 支，`g1_r46bB.jsonl`）：`SUM files=27 same=26 gained=1 lost=0`，
  `UP quote_handler.pyc 51/57 -> 52/57`；该文件残余
  `<dictcomp> 38/24`、`get_Ashares_local 75/77`、`get_kline_binary 129/128`、`get_kline_local 760/682`、
  `is_delisting_stock_local 95/94`。
- **G2′ 电池**：`test_repros` 143 支 `SUM files=143 same=143 gained=0 lost=0`。
  （首轮有一支 `r2_02_guard_early_return_dec_dec.pyc` 记为 `AssertionError('empty reading for …')`
  ＝读盘瞬时失败的行，非判据行为：单独重跑两臂同为 `1/2`、mism 逐字段相同，已并回 `g2_r46bB_fixed.jsonl`。）
- **G3 锚点**：109 支 `SUM files=109 same=109 gained=0 lost=0`（本轮无缺行）。
- **G4 全量 A/B（唯一发货判据）**：`r45full.txt`（402 索引 + 电池/锚点补充 + G0 见证，共 544 路径）
  对 Round 45 落地态行比对：`SUM files=544 same=543 gained=1 lost=0`；
  sha 变化面 **仅 1 支产物**（`fly/data/quote_handler.pyc`，见 `changed46bB.txt`）。
- **G4′ 变更产物 strict 尺**（a=落地前 repo core / b=`mirr_r46bB`，原文见 `g4prime46_prelanding.log`）：

```
== fly/data/quote_handler.pyc  strict-defective a=7 b=7
   CHANGED <module>.get_index_stocks_local  a=[seq_len orig=151 decomp=56] b=[seq_len orig=151 decomp=150]
G4-prime affected=1 fixed=0 broken=0 changed=1
```

  唯一 CHANGED 是一支**原本已失败**的函数换了成色：strict 发射条数 56 → 150（原始 151），
  官方 mism 行 `[150, 60, 0, 92]` 整行消失 ⇒ `51/57 → 52/57`。两把尺同向变好、无新增缺陷函数。
  残余 1 条是同文件 `get_industry_stocks_local 89/88`、`get_kline_binary 129/128` 所属的
  with 出口跳转桩族，与本形状无关。

判定：G4 `REGRESSION=0` ∧ G4′ `broken=0` ∧ sha 变化面 1 支 ⇒ 发货。

## 四、落地方式与落地后复验

落地＝按 `spec_r46b2.json`（由落地前字节 + 唯一锚点派生，`mkspec46b2.py` 断言锚点出现 1 次、净插入 28 行
＝16 行文档块 + 12 行新代码，另把原本那行 `_tail45 = self._generate_block_statements(_mb45)` 降入 `else` 分支）
经 `land46.py` 写入 `core/`；落地前另以臂 `mirr_r46bA2`（与发货臂**仅注释行不同、
非注释行逐行相等**，39 630 行）实测得同一组门禁数字（G1 `gained=1 lost=0`、G4 `same=543 gained=1 lost=0`、
G4′ `broken=0`、strict 同为 `56 → 150`），故文档块扩充不改变任何行为。

- **G5 `single`**：`site-packages/fly/data/quote_handler.pyc` → `matched_functions: 52`；
  惰性与锚定金丝雀 `site-packages/fly/data/quotation.pyc` → `143 / 143 100.00%`。
- **G6** `batch --index pyc_index.json --all --round 46`：`verified_pyc: 402`，`failed_pyc: 0`（日志 `g6_batch46.log`）。
  索引差异＝402 条 `last_tested_round: 45 → 46` ＋ 1 条 `matched_functions: 51 → 52`（`quote_handler.pyc`），无其它漂移。
- **G7 `stats`（本轮唯一发布数字，逐字）**：

```
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                375
  partial_pyc:           27
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5661
  cumulative_match_rate: 98.52%
```

- 工作树改动面：`core/cfg/region_ast_generator.py`、`pyc_index.json`、
  `site-packages/fly/data/quote_handlerOK.py`（由 G6 从落地核重出，未手工保留任何产物）。

## 五、本轮否证与移交 Round 47

1. **线 D（编排方一手，`fly/simtradding/flyAccount.pyc :: <module>.TradeAccount.init_connection 42/41`）
   拆成两层，两条候选本轮都不发货**：
   - **R46-D v2（归属层）**：`region_analyzer._collect_branch_blocks` 在 `merge` 非空时对 then 臂无界
     前向吸收，把「本 if 之后的父序列块」吸进臂内 ⇒ 臂尾 else-跳过跳转消失。
     合成见证电池 v2（`r46d2_witness.py`，9 个 code object）落地核 `defective=2/9` → 候选臂 `1/9`
     （`w2_break_arm_and_tail_if` 复位），真实靶 `init_connection` 结构上命中但不充分。
   - **R46-E（发射层）**：`_loop_postprocess` 把回边语句折进「最后一个 `If` 的 body」，条件是其全部
     前驱都在同一 then 臂内 ⇒ 折叠吃下了本属 if 之后的语句。v1 电池（`r46d_witness.py`，6 个对象）
     落地核 `defective=2/6` → 候选臂 `0/6`，v2 电池 `w3` 复位、`w2` 仍在；
     **G1 池 27 支 `same=27 gained=0 lost=0` ⇒ 官方尺完全中性**（合成的三种形状在语料里
     未被官方尺计入），本轮不发货。两支互补：`init_connection` 需两层同时命中，Round 47 可成对驱动。
     注意 `D:/Temp/r43gate/mirr_r46dA`、`mirr_r46d2A` 内留有调试 print，复用前必须从
     `spec_r46d.json` / `spec_r46e.json` 重建。
2. **线 C（代理，等长 MOVE 族）交付候选 R46-C1**（`lineC_ANALYSIS.md`）：
   `_loop_handle_no_exit_successors` 两臂都在环内时只发射各臂的 entry 区域，then 臂私有落块被体走
   最后发射 ⇒ 纯等长 MOVE。自报数字：成员 strict `3/64 → 2/64`（`fly/logger.pyc ::
   Backtest.write_logging_thread` 复位），27 支池 `SAME=26 MOVED=1 IMPROVED=0 REGRESSION=0`、
   matched 合计两侧同为 875/961，全 402 支字节扫描 `changed=1`。**官方尺增益 0 ⇒ 本轮不发货**，
   与线 D 的两层一并交 Round 47（其锚点行号在 R46-B 之后整体下移 28 行，spec 按文本锚点派生仍可用，
   但必须对 Round 46 落地字节重跑 G0/G2′/G3/G4/G4′）。
3. **线 B 自报否证（照录）**：Round 44 提到的 `get_open_orders` 尾部 ~41 条丢失在落地核上是
   **假线索**（strict `(None,'ok')`、两臂产物逐字节相同），它只是 c3 臂的副作用，本轮充当阴性对照 #5。
4. **R45-A 邻域残余继续有效**：判据①目前只接受后代 `IfRegion` 认领；merge 块被后代
   **LoopRegion / TryRegion** 认领、或认领链为多层时仍是空档。
   `get_index_stocks_local` 残余 1 条（with 出口跳转桩族）与 `get_industry_stocks_local 89/88`、
   `get_kline_binary 129/128` 同源。
5. **台账继续有效**：`matcher::match 713/689`、`clock_worker`、`decrypt_database_url 295/324`、
   `events 510/508`、`_init_config 86/84`、`OverNightOrder.__init__ 172/148`、
   `api_base::get_history_df`、`_trade_status_handle 114/112`、`after_trading_cancel_order 155/155 j3`、
   等长行 `write_logging_thread 113/113 j1`、`_process_task_queue 378/378`、`_all_bars_of_cache 230/231`、
   `check_stock 88/89`、`get_history_new 322/323`、`get_multiminute_his_data 481/482`、
   `wizard_quant_api` 的 `calculate_di 75/73`、`params_analysis 133/126`。
6. **接管点**：线 B/线 C 的私有 scratch 目录 `D:/Temp/r46diagB`、`D:/Temp/r46diagC` 在盘
   （见证源、探针、spec、臂 `mirr_r46b1` / `mirr_r46c1`、`full_r46b1_*.jsonl`），
   线 D 在 `D:/Temp/r46orch`；Round 47 直接复跑即可，不必重建证据。
