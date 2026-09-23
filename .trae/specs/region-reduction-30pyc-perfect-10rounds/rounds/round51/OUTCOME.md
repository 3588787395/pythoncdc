# Round 51 — 空 `else: pass` 臂被分析侧擦除后，链尾出口跳转随兄弟摊平折叠丢失（R51-A + R51-B 落地）

## 靶与真实根因

靶 `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`（严格尺逐函数
`98/123`，官方尺 `105/119`）。四条缺陷改前逐字：

- `<module>.TradeLiveBroker.get_crdt_stock_info [seq_len] orig=251 decomp=250`
- `... get_crdt_target_stockinfo [seq_len] orig=285 decomp=284`
- `... get_crdt_enslosecu_stock_info [seq_len] orig=350 decomp=349`
- `... etf_basket_order [seq_len] orig=696 decomp=695`

落地前产物里链尾的形状（`trade_live_brokerOK.py` 改前 2024/2071/2123 三处，
见 `r51_product.diff`）：

```
                        elif code[0] == '3' or code[:3] == '002' or ...:
                            code += '.SZ'
                        while False:          # ← 孤立边界 NOP 摊平出的兄弟语句
                            pass
                        stock_out_info = dict()
```

源码实为 `if … elif … else: pass`（空 else 子句）。根因三段，逐段取证：

1. `core/cfg/region_analyzer.py :: <RegionAnalyzer>._build_elif_region`
   （`19138-19139`）`if inner_else_blocks and all(self._is_trivial_block(b) for b in
   inner_else_blocks): inner_else_blocks = []` —— 平凡 else 臂被整体擦除，
   那个只含 `NOP`（外加一条无条件跳转，R51-A 形）的垫块因此**既不属于本链也不属于任何子区域**。
2. `core/cfg/region_ast_generator.py :: _generate_block_statements_body`
   的孤立边界 NOP 分支（`44730-44749`）把它作为**兄弟语句**摊平成 `while False: pass`。
3. 摊平出的块紧跟前一臂体 ⇒ 前一臂末不再需要「越过空臂」的跳转 ⇒ re-compile 恰少一条
   `JUMP_FORWARD`，长度缺陷而非内容缺陷（strict 全为 `seq_len`，差值恒为 −1）。

结构性依据（决定该块确实来自源码 `else`）：无 `else` 子句时 CPython 3.11 把最后一个测试的
落空边直接指向汇合点，不会留下需要被跳过的中间块；留下这样一块本身就是「源码有一个空 else」
的图面证据。本轮**未改分析侧**（`_build_elif_region` 的擦除是 merge/region 归属的上游依赖，
按 [[merge-completion-cascade]] 逐站点开证原则不在本轮动），改为在链的发射点按归属收回该块。

## 落地判据（R51-A + R51-B，`_if_generate_elif_chain` 单站点，`16099-16205`，判据体已写入注释）

R51-A（`16099-16140`）—— 链**有** `elif_final_else` 臂、且此刻既无 `nested_elif_stmts`
也无 `final_else_stmts` 时：该臂全部块只含噪声指令（`RESUME/NOP/CACHE/EXTENDED_ARG/
PUSH_NULL` + 一条 `JUMP_FORWARD|JUMP_ABSOLUTE`）、块本身不是汇合块、臂首块是链最后一个测试
（`elif_conditions[-1]`，退化时用 `condition_block`）的后继、臂末块以跳转或顺序后继到达
`merge_block`、且没有区域的 entry 落在臂内 ⇒ `final_else_stmts = [Pass]` 并把臂块标为已生成。

R51-B（`16141-16205`）—— 链此刻没有任何 orelse 内容时，按**归属**找回垫块：候选块非汇合块、
有前驱、全部指令皆噪声（连跳转都没有 ⇒ 与 R51-A 的「臂体自带出口跳转」互斥）、后继集恰为
`{merge}`、未被发射、不是任何区域入口；其每个前驱要么属本链块集，要么其终结子是指向该块的
条件跳转，且至少一个前驱属后者（这条边即源码 if/elif 的落空边）；满足者唯一才生效。
容器选择：`nested_elif_stmts` 恰一条且其 `orelse` 为空 ⇒ 写它的 `orelse`；
否则（皆空）⇒ 写 `final_else_stmts`。两条判据都只读块同一性、终结子类别、前驱/后继关系，
不读名字、常量、绝对偏移与指令数。

## 否证与归档

- **R51-C（放宽 R51-A 的 `not nested_elif_stmts` 合取，使其与 R51-B 共用容器）**：
  12 个真文件靶 + 14 支复现电池逐行逐字与 A+B 臂相同（`diff g051_c51b2.log g051_c51c.log`
  仅差 core 路径一行）⇒ 无任何可测收益，只增加命中面，**不落地**
  （`mk_cand51c_falsified.py` / `g051_c51c_falsified.log`）。
- 上一轮（Round 50）移交的三元链 kwarg 槽位线仍挂在生成器侧
  （`_try_build_ternary_kwarg_call` 在 kwarg 槽位 `return None`），本轮未动。

## 门禁（严格串行；G4 为唯一发货判据）

- **G0** 12 靶文件逐函数严格尺：`trade_live_broker 98/123 → 101/123`，三支 `get_crdt_*`
  转 clean，`etf_basket_order` 由 `seq_len 696/695` 转为同长 `seq_diff #254`；
  其余 11 个靶文件逐支缺陷消息逐字未变（含 `quotation 148/150`、`order_api 33/36`、
  `klinedata 53/63`、`quote_handler 65/72`）。
  复现电池（14 支）：head `MISMATCH=3` → landed `MISMATCH=2`，`r51b_05`（try 包裹的
  嵌套链 + 空 else）`seq_len orig=46 decomp=45` → MATCH，`r51a_04`/`r51b_06` 两支逐字未变，
  无一支转坏。落地工作树与门禁臂产物逐字节相同。
- **G1 变化面（17 支 deficit≤2 文件）**：`SAME=17 IMPROVED=0 REGRESSION=0 MOVED=0`。
- **G2′ 电池 143 支**：`SAME=143 IMPROVED=0 REGRESSION=0 MOVED=0`。
- **G3 承重锚点 109 支**：`SAME=109 IMPROVED=0 REGRESSION=0 MOVED=0`。
- **G4 全量 544 路径**：`TALLY SAME=543 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0`，
  `files fully matched a=484 b=484`；唯一 MOVED 即靶文件，其产物 diff `+5/-3`
  （三处 `while False: pass → else: pass`，一处新增 `else: pass`）。
- **G4′ 逐支严格尺复验**：`affected=4 fixed=3 broken=0 changed=1`
  （官方尺可见的改进：`etf_basket_order` 官方 mism 明细 `[693, 692, 12, 431] →
  [693, 693, 11, 216]`，长度缺陷消除、内容缺陷减半）。
- **G5 落地态**：`build --all` 前 12 靶产物 sha/mism 与臂逐项相同；
  `fly/data/quotation.pyc 143/143`（官方）与 `148/150`（严格）逐字不变；
  `test_repros/round16_sink/run_all.py` `repros=15 MISMATCH=0 MATCH=15 ERROR=0 UNEXPECTED=0`。
- **G6** `batch --index pyc_index.json --all --round 51`：402 verified / 0 failed。
  `pyc_index.json` 仅 402 条 `last_tested_round 49 → 51`，无任何值域变化（脚本断言
  「非轮次戳行数 = 0」），文件仍纯 CRLF `4553/4553`、无 BOM、`json.dumps` 往返逐字节成立。
- **G7 stats 原样**（本轮官方计数不动，见下）：

```
======================================================================
累计统计:
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                375
  partial_pyc:           27
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5665
  cumulative_match_rate: 98.59%
======================================================================
```

**本轮收益口径（如实说明）**：三支 `get_crdt_*` 在官方尺上本就判为匹配（其长度差被官方尺的
跳转容忍规则吸收），故官方 `matched_functions` 与 `stats` 逐字不动，G4 `IMPROVED=0`；
真实收益是严格尺 3 支转干净 + `etf_basket_order` 的官方明细数值减半。
本轮不是 Round 48/49 那种官方 +1 的落地。

## 字节面

`core/cfg/region_ast_generator.py`：`2a3d522b0ec9e8fe66e4` → `944c18b3e0807f7139c0`，
`3 003 323 → 3 010 264 B`（+107 行），UTF-8 BOM 保留，`CRLF 48 654 → 48 761` 且裸 LF 恒 0。
`core/cfg/region_analyzer.py` 逐字节未动（`c644a6ccab745ac6be0e` / 1 687 755 B）。
落地用 `spec_r51ab.json`（`mkspec51b.py` 从 `mk_cand51b.py` 以 `ast` 抽取，无文本二次复制）
重放，臂与测量镜像 `mirr_c51b` 逐字节相同后才写 `core/`。
工作树改动仅 `core/cfg/region_ast_generator.py`、`site-packages/.../trade_live_brokerOK.py`、
`pyc_index.json` 与本记录目录。

## 残余与移交 Round 52

- `r51a_04`（`32/31`）与 `r51b_06`（`33/32`）两支仍各差 1 条且改前后逐字相同：
  前者是 R51-A 命中后仍差的另一条（同文件另有独立缺陷，见 Round 50 记录），后者是
  **外层与内层各有一个空 else** 的双空 else 形状 —— 内层链收回垫块后外层链的
  `nested_elif_stmts[0]['orelse']` 已非空，R51-B 的「此刻没有任何 orelse 内容」前置因此闭嘴。
  Round 52 线 A：把「本链无 orelse」从全局前置改为**逐臂**判据（对每一层的空 else 分别找垫块），
  并先用 `r51b_06` 单支开证再铺真文件。
- 靶文件严格尺仍余 22 支，官方 `105/119`：`_process_order 454/399`、`_sync_worker 350/323`、
  `fund_transfer 123/88`、`market_fund_transfer 94/67`、`get_etf_stock_info 144/117` 等
  整段丢失族，与 `ipo_stocks_order 1075/1076`、`get_max_amount 201/213` 多出族。
- Round 50 移交的三元链 kwarg 线不变：`order_api :: future_order 101/93`、
  `option_order 83/74`（`_try_build_ternary_kwarg_call` 41500-41505 kwarg 槽位 `return None`
  ＋链行走只沿 `merge_block==inner.entry` 前向延伸），与同文件 `base_order [target_diff] #136`
  是不同形状，不得并入。
- R51-A/R51-B 只挂在 `_if_generate_elif_chain` 的一处发射点；`_build_elif_region:19138` 的
  平凡臂擦除仍是上游病因，若后续靶子落在「链未被建成 ELIF_CHAIN」的形状上，须按同一谓词
  在分析侧逐站点开证，不得一次全铺。
- 台账（未变）：`plugin_system_log/__init__.pyc :: setup`（320/253）、`matcher::match`、
  `clock_worker`、`decrypt_database_url 295/324`、`events 510/508`、`_init_config 86/84`、
  `OverNightOrder.__init__`、`api_base::get_history_df −24`、`write_logging_thread 113/113 j1`、
  `init_connection 42/41`、`params_analysis 133/126`、`quote_handler::get_kline_local 760/682 j12`、
  `handle_exrights 276/268`、`trade_live_broker 105/119`、`real_quote 39/44`、
  `fly/data/quote.pyc 69/81`、`klinedata` 同族 4 支（`_all_bars_of_cache 230/231`、
  `kline_datetime_list 390/391`、`get_multiminute_his_data 481/482`、
  `get_all_real_daily_kline 188/187`）、Round 48 五条等长 `seq_diff` 函数。
