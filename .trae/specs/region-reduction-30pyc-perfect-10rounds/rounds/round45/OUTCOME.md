# Round 45 结果：落地 R45-A（if/elif 链的 merge 块被链内后代区域认领时，链尾无人发射）

落地铁笔：本轮 `core/` 改动为单文件单处插入，与实测镜像臂 `D:/Temp/r43gate/mirr_r45a` 逐字节相同。

- `core/cfg/region_ast_generator.py`：`d4c430303a5d2b63753d` → `e743b6de1d8efc014da8`，len 2 995 945 → 2 997 983，CRLF 48 563 → 48 592、裸 LF 0、UTF-8 BOM 保留
- `core/cfg/region_analyzer.py`：未改动，仍为 `55a9f61b9b0703063d44`（len 1 681 035，CRLF 27 023、裸 LF 0）

## 一、开工靶池（实测 landed `5a46b245`）

`stats`：375 ok / 27 partial / 0 failed，5659/5746。承接 Round 44 移交的线 C 线索
（「兄弟块若起始于前一守卫区域的 merge 块 ⇒ `region_ast_generator` 只发射第一个三元表达式」），
按纯发射侧形状排查后命中。

靶文件 `IQCommon/strategy/wizard_quant_api.pyc` 开工时 `50/53`，三条缺陷函数中
`<module>.region_mean_desicion` 为 `seq_len orig=51 decomp=52`（多 1 条）。

## 二、根因（发射侧：链的 merge 块归属在链内、发射责任在链外）

`region_mean_desicion` 形态：`if len(...) < max(...): log + return` → `elif 链式比较: return True` → 链后 `return False`。
链后那条 `return False` 整条不发射（原始 51 条里缺 1 条收尾 `RETURN_VALUE`）。

归属层的结构事实（`probe45e.py` 的区域转储，合成见证与真实靶文件逐字段同形）：

```
IfRegion IF_ELIF_CHAIN entry=B0 exit=B250 cond=B0 then=[B68] else=[B114,B186,B242,B240,B246] merge=B250
   blocks=[B0,B68,B114,B186,B240,B242,B246]                     <-- merge 块 B250 不在链的 blocks 归属集内
...IfRegion IF entry=B114 then=[B246] else=[B250] merge=B246    <-- 链内某个臂的后代 IfRegion 认领了 B250
ownership: B250 term=RETURN_VALUE preds=[B186,B242] owner=IfRegion(RegionType.IF)
```

真实靶：链 `entry=B0 exit=B268 merge=B268`、blocks `[B0,B68,B112,B194,B258,B260,B264]`，
内层 `IF entry=B112 then=[B264] else=[B268]`。

⇒ 链的 merge 块被链内一个嵌套 `IfRegion` 取得归属（作其 else 臂）后：
① 链的 elif 发射路径只读 `elif_conditions` / `elif_bodies` / `elif_final_else`，不读 `merge_block`；
② 被链吞并的内层区域不独立发射自己的 else 臂（它已在链的展平中被消费）；
③ 于是该块在两条路径之间失去发射责任 —— 违反原则 2（每块唯一归属）所承诺的「归属者必发射」。

R45-A 为发射侧同层判据（`_if_generate_full_elif_chain` 收尾处，插在 `_should_emit_elif` 装配完之后、
`_r57_shared_mb` / `_r91_post_if_blocks` 之前），五条合取全部只读结构事实：
① merge 块不在本链 `region.blocks` 归属集内，且本链某后代 `IfRegion` 认领它；
② 本链中存在块以正常后继指向它（臂汇入 ⇒ 链后代码可达）；
③ 它不是隐式 `return None` 块（隐式返回由编译器补齐，不该由链补写）；
④ 此刻尚未被任何发射登记（`start_offset not in generated_offsets` ⇒ 后代已发射则不重复）；
⑤ 未经 `trailing_return` / `_r57_shared_mb` / `_r91_post_if_blocks` 任一路径承担。
命中时按 `_generate_block_statements(merge)` 追加为链的尾随语句，并登记块与偏移。只加发射责任，不改归属树。

## 三、门禁序列（严格串行）

- **G0 合成见证**（`D:/Temp/r43gate/r45e`，见证 4 个 code object + 对照 8 个 code object）：
  落地核 `RESULT landed: defective=1/4`（`region_mean_repro DEFECT seq_len orig=49 decomp=50`）→
  候选臂 `RESULT r45a: defective=0/4`，产物链尾 `return False` 复位。
  对照电池 `run45e2.py`（链在循环内 / 普通 if+尾块 / 隐式 merge / if-elif-else+尾块 / 臂内嵌套链 /
  链后接 for / 全 return 无尾块，7 支具名函数 + 模块共 8 个 code object）：
  `landed defective=0`、`r45a defective=0`、`BYTE-IDENTICAL products: candidate is inert on all 8 control shapes`。
- **G1 靶 + 已失败文件池**（18 支，清单 `g1r45a.txt`，行 `g1_r45a.jsonl`）：
  `SUM files=18 same=17 gained=1 lost=0`，`UP wizard_quant_api.pyc 50/53 -> 51/53`；
  该文件残余 `calculate_di 75/73 j0 t45`、`params_analysis 133/126 j1 t117`。
- **G2′ 电池**：`test_repros` 143 支 `SUM files=143 same=143 gained=0 lost=0`。
- **G3 锚点**：109 支 `SUM files=109 same=109 gained=0 lost=0`（本轮无缺行）。
- **G4 全量 A/B（唯一发货判据）**：`r45full.txt`（402 索引 + 142 支电池/锚点补充 + 4 支 G0 见证，共 544 路径）
  对 Round 44 落地态行比对：`SUM files=544 same=539 gained=1 lost=0`；sha 变化面 **仅 2 支**
  （`wizard_quant_api.pyc`、`quote_handler.pyc`，见 `changed45.txt`）。
- **G4′ 变更产物 strict 尺**（a=落地前产物 / b=`build_r45a`）：

```
== IQCommon/strategy/wizard_quant_api.pyc  strict-defective a=5 b=4
   FIXED   <module>.region_mean_desicion   [seq_len orig=51 decomp=52]
== fly/data/quote_handler.pyc  strict-defective a=7 b=7
   CHANGED <module>.get_index_stocks_local  a=[seq_len orig=151 decomp=56] b=[seq_len orig=151 decomp=60]
G4-prime affected=2 fixed=1 broken=0 changed=1
```

  唯一 CHANGED 是一支**原本已失败**的函数换了成色：`get_index_stocks_local` 发射条数 56 → 60（原始 151），
  官方 mism 行的跳转差由 `j=5` 归零（`[149,54,5,97] → [150,60,0,92]`）。即严格尺与官方尺同向变好、
  未新增缺陷函数，属 Round 44 移交线索 3（`quote_handler` 臂内续块）的部分命中，不是回归。

判定：G4 `REGRESSION=0` ∧ G4′ `broken=0`，且增益函数 `region_mean_desicion` 有 strict `FIXED` 行佐证
（非「只比跳转操作码」造成的假 ok）⇒ 发货。

## 四、落地方式与落地后复验

落地＝按 `spec45a.json`（由落地前字节 + 唯一锚点派生，`mkspec45.py` 断言锚点出现 1 次、插入 29 行）
经 `land45.py` 写入 `core/`，落地后 sha 与 `mirr_r45a` 一致，`region_analyzer.py` 逐字节未动。

- **G5 `single`**：`site-packages/IQCommon/strategy/wizard_quant_api.pyc` → `matched_functions: 51 / 53`，
  残余缺陷函数与 G1/G4 行一致（`region_mean_desicion` 已从 mism 消失）。
  惰性与锚定金丝雀 `site-packages/fly/data/quotation.pyc` → `143 / 143 100.00%`。
- **G6** `batch --index pyc_index.json --all --round 45`：`verified_pyc: 402`，无 failed（日志 `g6_batch45.log`）。
- **G7 `stats`（本轮唯一发布数字，逐字）**：

```
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                375
  partial_pyc:           27
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5660
  cumulative_match_rate: 98.50%
```

- **索引审计**（`idxaudit45b.py`，G6 之后）：402 条、`function_count` 合计与冻结值相等、
  `last_tested_round` 全为 45、对 Round 44 落地基线仅 1 条漂移
  （`IQCommon/strategy/wizard_quant_api.pyc` `50/53` → `51/53`）。
- 本轮一并提交 `site-packages/**/*OK.py` 的 7 支已改动产物：其中 5 支（`klinedata`、`execution_context`、
  `history_api`、`plugin_system_trade/function`、`trade_live_broker`）是 Round 44 的 sha 变化面当时未随提交入库、
  本轮 G6 由落地核重出的产物，另 2 支为本轮变化面。全部由当前落地核生成，语料与核一致。

## 五、Round 46 移交

1. **R45-A 的邻域残余（同一条判据可继续细化的方向）**：判据第①合取目前只接受后代 `IfRegion` 认领
   （`find_descendant_region_for_block(_mb, (IfRegion,))`）。若链的 merge 块被后代 **LoopRegion / TryRegion**
   认领，或认领链为多层（后代区域的兄弟而非直接子），仍会落入「归属者不发射」的空档。
   见证形状沿用 `r45e_witnesses.py` 的 `region_mean_repro`，把 merge 块的归属换成 loop/try 即可判定是否需要扩展。
2. **`quote_handler.pyc :: <module>.get_index_stocks_local`（本轮换好成色但未收口）**：
   strict `seq_len orig=151 decomp=60`，官方 mism `[150,60,0,92]`。跳转差已归零、条数仍缺 91，
   属 Round 44 移交线索 3 的「兄弟块起于守卫 merge 块」大形状剩余部分——本轮判据只吃到了链尾一支。
3. **`wizard_quant_api.pyc` 残余 2 函数**：`calculate_di`（`75 vs 73`，`j=0` ⇒ 纯条数缺 2）、
   `params_analysis`（`133 vs 126`，`j=1`）。前者是「等长/近等长无跳转差」族，与布局换位族同源。
4. **台账继续有效**：`get_ipo_stocks`（官方已算 matched，strict 为 `target_diff` 的假 ok）与 `ipo_stocks_order`；
   等长块换位（`fly/logger.pyc :: write_logging_thread 113/113 j=1`、`_process_task_queue 378/378`）；
   反转 if + 丢失出口跳（`fly/simtradding/flyAccount.pyc :: init_connection 42/41`）；
   `matcher::match`、`realtime_event_source::clock_worker`、`api_base::get_history_df`、`decrypt_database_url`、
   `events 510/508`、`_init_config 86/84`、`OverNightOrder.__init__ 172/148` 等。
5. **Round 45 四条代理诊断线（A/B/C/D）均耗尽轮次未交结论**，其私有 scratch 目录
   （`D:/Temp/r45diagA…D`，含 `battery_pyc/`、`spec_p1.json` 等）仍在盘上，Round 46 可直接接管证据而不是重跑。
