# Round 52 — 比较链把「两臂汇合块」认领成 else 臂 ⇒ 凭空补一条越臂跳转（R52-B 落地）；退化占位区域不再否决 R51-A（R52-A 落地）

## 靶与真实根因

主靶 `site-packages/IQCommon/api/klinedata.pyc`（严格尺逐函数落地前 `53/63`），本轮清掉其长度缺陷的两条：

- `<module>._all_bars_of_cache [seq_len] orig=230 decomp=231`
- `<module>.kline_datetime_list  [seq_len] orig=390 decomp=391`

同一根因另外两处：`site-packages/fly/data/quote.pyc :: <module>.check_stock [seq_len] orig=88 decomp=89`
（其最小复现体即本轮在册的 `test_repros/round3/r3_12_assert_absorbed_as_else.pyc 1/2 → 2/2`）。
四条缺陷一律是 **len(+1) 的长度缺陷**：产物多出一条跳转，不是少。

逐字取证（`dis` 原函数）：

```
214 LOAD_FAST  start_date
218 LOAD_CONST '20050101'
...
228 POP_JUMP_FORWARD_IF_FALSE to 242     # 比较链第一段落空
238 POP_JUMP_FORWARD_IF_FALSE to 250     # 比较链最后一段落空 → 汇合块
240 JUMP_FORWARD  to 246                  # 链为真 → 臂体
242 POP_TOP / 244 JUMP_FORWARD to 250     # 短路中间出口 → 同一汇合块
246 LOAD_CONST '20050101' / 248 STORE_FAST start_date   # 臂体（唯一语句）
250 LOAD_GLOBAL history_cache             # 汇合块 = 臂后那条兄弟语句 `if history_cache == 1:` 的条件块
```

臂体块 246 **以正常流落入 250**，且 250 同时是链落空边的靶。即 250 是两条臂的汇合点。
`core/cfg/region_analyzer.py :: _build_chained_compare_region`（定义 `19550`）原先把
`real_else = short_circuit_succ` 直接当作 else 臂（`else_blocks = [real_else]`）并认领进 `all_blocks`
（`19605-19610`、`19631` 一带），于是「汇合块」被当成「else 臂首块」。发射侧照 `IF ... ELSE ...` 形状
为 then 臂补一条越过该块的 `JUMP_FORWARD`，而原函数是落进去的 ⇒ 恰多一条指令。

结构性依据（不需任何名字/常量/偏移特判）：CPython 编译 `if A: T else: E` 时必然在 T 臂末尾发射一条
跳过 E 的跳转；因此 **T 臂的任何块都不可能被列为 E 首块的后继之外的方向**——反过来，一旦 T 臂某块把
「被认领的 else 首块」列在其 `successors` 里，那块就不是互斥臂而是汇合点。这与原则 2（同一层每块唯一归属、
且归属者必须发射它）直接矛盾：认领它的那个区域会把它的正常流改写成一个显式跳转。

## 落地判据

### R52-B `core/cfg/region_analyzer.py :: _build_chained_compare_region`，`19683-19704`（+22 行，0 删除；判据体已写入识别方法注释）

在构造 `IfRegion(region_type=RegionType.IF, ... then_blocks=_blocks, else_blocks=else_blocks,
merge_block=merge_block, ...)`（`19706` 起）**之前**插入同层判据：

1. 取 `else_blocks[0]` 为被声称的 else 臂头块；
2. 若 then 臂块集 `_blocks` 中任一块把该头块列为 `successors` 成员 ⇒ 它是两臂真正汇合点；
3. 命中则按「无 else 的比较链 `if`」归约：`else_blocks = []`、`merge_block = ` 该头块，
   并把原 else 臂各块从 `all_blocks` 摘出 ⇒ 该块及其后语句保持未认领，由父层按兄弟节点发射
   （原则 4：父层以子区域 entry 引用之，不复制其内部块）。

未命中时代码路径与落地前逐字节相同（`git diff` 为纯新增 hunk）。判据只读 then/else 块集与
`successors` 关系，不读名字、常量、绝对偏移、指令数、文件清单，也不跨区域跨层次。

### R52-A `core/cfg/region_ast_generator.py :: _if_generate_elif_chain` 的 entry 否决精化，`16135-16150`（+16 行，0 删除）

Round 51 的 R51-A 在链发射点收回「空 `else: pass`」垫块，但带一条「该块是某区域 entry ⇒ 竞争归属 ⇒ 否决」的
守卫。分析器会为尚未归约的块留下**退化容器区域**（`Region`、`region_type is RegionType.BASIC`、
`blocks` 只含 entry 自己一块），它不是原则 3 意义上的抽象节点，只是占位记录。R52-A 精化为：
仅当该退化区域的 `block_to_region` 归属**不是本链**时才算真竞争者。

- 作用面实测：`wit52/` 电池 13/14 → **14/14**（`r51a_04` / `r51b_06` 的垫块正是此形状）。
- 真实语料：R52-A 单独跑 G4 为 `IMPROVED=0 REGRESSION=0 MOVED=3`，与 R52-B 合并后
  `MOVED` 仍是那 3 支（`klinedata` / `order_api_trade` / `trade_live_broker`）、`IMPROVED` 仍是 R52-B 的 3 支
  ⇒ 两条判据零相互作用（`ab --a=g4_c52b.jsonl --b=g4_c52ab.jsonl`：`SAME=541 IMPROVED=0 REGRESSION=0 MOVED=3`）。
- 它移动的 3 支产物恢复 4 处 `else: pass`，两把尺子都记为「不变」——`pass` 臂编译成噪声 NOP，
  官方尺与严格尺都滤噪声。落地理由只有两个：源码保真（少一条语句就是错的）与电池闭合；
  不计入成功率收益，也不据它以宣称任何率值提升。

## 门禁（候选臂 + 落地核双跑，全部串行）

- **G0**（15 靶 + `wit52/` 电池，缺陷消息逐字）：靶文件逐函数 `15/15` 与落地前对比只有
  `fly/data/quote.pyc 71/89 → 72/89`，靶面严格缺陷行数 `95 → 94`，其余 14 支逐字未变；
  电池 `MISMATCH=0 MATCH=14`。（`mirr_c52b` 单臂同结果 ⇒ R52-A 对靶面惰，与 G4 一致。）
- **G1**（17 支 deficit≤2 文件）：`SAME=16 IMPROVED=0 REGRESSION=0 MOVED=1`，
  唯一 `MOVED` 为 `IQData/api/api_base.pyc`（`get_history_df` 缺陷计数 `1718 → 1719`，严格靠近）。
- **G2′**（143 路径含复现体）：`SAME=142 IMPROVED=1 REGRESSION=0 MOVED=0`，`files fully matched 111 → 112`。
- **G3**（109 锚点）：`SAME=108 IMPROVED=1 REGRESSION=0 MOVED=0`，`files fully matched 79 → 80`。
- **G4**（全量 544 路径，唯一发货权威）：`SAME=538 IMPROVED=3 REGRESSION=0 MOVED=3 ERR=0`，
  `files fully matched 484 → 485`；
  `IMPROVED klinedata 41/45 → 42/45`、`IMPROVED fly/data/quote 69/81 → 70/81`、
  `IMPROVED test_repros/round3/r3_12_assert_absorbed_as_else 1/2 → 2/2`。
- **G4′**（受影响文件逐 code object 严格尺复核）：`fixed=2 broken=0 changed=3`，且三处 `changed` 逐项严格靠近：
  `quote::check_stock`、`r3_12::check_stock` 由 `seq_len 88/89` 转 `ok`；
  `klinedata::_all_bars_of_cache` 由 `seq_len 230/231` 转 `target_diff #24`、
  `kline_datetime_list` 由 `seq_len 390/391` 转 `seq_diff #151`（长度缺陷清除后**露出**内容缺陷，见下）；
  `api_base::get_history_df` `|1742−1718|=24 → |1742−1719|=23`。
- **R52-B 复现电池 `wit52b/`（12 例，新增）**：落地前 `MISMATCH=7 MATCH=5`，候选臂 `MISMATCH=1 MATCH=11`
  （6/7 复现体被修，5 例阴性对照两臂均 MATCH ⇒ 判据未过火）。逐例见 `wit52b_tally.md`。
- **G5**：落地核对 6 支受影响 pyc 重新反编译，产物与门禁臂产物 **6/6 逐字节相同**；
  金丝雀 `fly/data/quotation.pyc` 官方 `143/143`、严格 `148/150`（与落地前同）；
  `test_repros/round16_sink` 15/15 MATCH（第 16 项 `run_all.py` 是电池驱动脚本）。
- **G6**：`batch --index pyc_index.json --all --round 52` → `402 verified / 0 failed`，
  `ok_pyc 375 / partial 27 / failed 0`。
- **G7**（`stats` 原样）：`total_functions 5746`、`matched_functions 5665 → 5667`、
  `cumulative_match_rate 98.59% → 98.63%`（函数总量 Σfc 仍为 5746，未动分母）。

## 否证与遗留（交 Round 53）

1. **同形残支**：`wit52b/r52b_09_chain_inside_or`（`if a < b < c or d: x = 2`）两臂均 `+2`。
   链被 `or` 包成一段时，落空边指向的是 boolop 自身的塌缩块而非本区域的 `short_circuit_succ`，
   故 R52-B 的「then 臂块的后继」判据不触发。开证点是 `_build_chained_compare_region` 里
   `chain_blocks` / `all_compare_blocks` 与外层布尔区域的汇合块如何互相引用，不是本轮站点。
2. **`_all_bars_of_cache` 的 `target_diff #24`**（`POP_JUMP_FORWARD_IF_TRUE` 终点 `160` vs `148`）与
   `kline_datetime_list` 的 `seq_diff #151` 是长度缺陷掩盖下的**另一处**内容缺陷；
   `check_datetime_common 39/45`、`get_multiminute_his_data`（R49/R50 旁支）也仍未消。
3. **伪造尾随 `continue`（T1/T2）未触碰**：`trade_live_broker::_on_set_positions 297/298`、
   `finance::func_get_fundamentals_daily_data 192/193`。本轮已把地面真凶取证完毕
   （`gt52_try.py`：T1 = try 体末 `JUMP_BACKWARD`、处理器末 `POP_EXCEPT; JUMP_BACKWARD`；
   T2 = try 体末 `JUMP_FORWARD` 到一个独立回边块），发射站点已由带打印镜像核定位到
   `region_ast_generator.py` 的 `stmts.append({'type': 'Continue'})`（`blk=964`），
   且该块前驱数 `≥2` 已被 `_is_loop_tail_convergence_block` 吞掉 ⇒ 该族需要发射侧判据，另轮开证。
4. Round 51 移交的 R50 线 A（`_try_build_ternary_kwarg_call` 的 kwarg 逐槽装配 + 入口 region 取最外层三元）
   本轮未动；`order_api.pyc 33/36` 三条靶逐字未变。

## 字节面

- `core/cfg/region_analyzer.py`：`c644a6ccab745ac6be0e → 66553c66939e9e9242f4`，
  `1 687 755 → 1 689 673 B`，CRLF `27 126 → 27 148`，裸 LF `0`，无 BOM，`git diff --numstat` = `+22 −0`（单 hunk）。
- `core/cfg/region_ast_generator.py`：`944c18b3e0807f7139c0 → c36cf1fe7dad68377c80`，
  `3 010 264 → 3 011 895 B`，CRLF `48 761 → 48 777`，裸 LF `0`，BOM 保留，`+16 −0`（单 hunk）。
- 落地方式：`land52.py` 先在内存里对两份 spec 应用锚点（各 `count == 1` 断言），
  与通过门禁的合并臂 `mirr_c52ab/core/cfg/*` **逐字节相同才写盘**；写盘后回读断言 BOM/CRLF/裸 LF 不变。
- `pyc_index.json`：`--all` 回写 402 条 `last_tested_round → 52`；值域变化仅 2 条
  （`klinedata matched_functions 41 → 42`，rate `0.9111 → 0.9333`；`quote 69 → 70`，rate `0.8519 → 0.8642`）。
  文件仍为纯 CRLF 4553 行、裸 LF 0。
- 5 支 `*OK.py` 随 `batch --all` 重生成（`klinedata` / `api_base` / `quote` / `order_api_trade` /
  `trade_live_broker`），未手工改动任何产物；全量 402 支重跑后只有这 5 支内容变化 ⇒
  本轮改动面与 G4 的 `MOVED/IMPROVED` 集合完全一致。
