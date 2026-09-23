# Round 54 结果（OUTCOME）

**本轮发货判据：R54-COMP**（`core/cfg/comprehension_generator.py :: _detect_comp_ternary`，单 hunk
`1733-1746 → 1733-1749`，+13 行 −4 行、文件 `102 871 → 104 143 B`，CRLF 1960、裸 LF 0、无 BOM，
sha256[:20] `fa43dbc9e878eeacbfe0 → 00903b60ef2411cb6b37`）。
`region_analyzer.py`（`b10ee76b55754f09e945`）与 `region_ast_generator.py`（`c36cf1fe7dad68377c80`）
本轮逐字节未动。

## 靶与真实根因

靶：`site-packages/fly/data/quote_handler.pyc :: <module>.is_delisting_stock_local`
（落地前严格 `seq_len orig=97 decomp=95`，官方 `52/57`）。

`dis` 地面真值（父函数 `<module>.is_delisting_stock_local` 的 `<dictcomp>` 码对象，源码行 299-302）：
元素值是一个**嵌套三元链**——

```
100 POP_JUMP_FORWARD_IF_FALSE -> 106      # 外层条件 False → 进 false 区
102 LOAD_CONST True ; 104 JUMP_FORWARD -> 200
106 ... CONTAINS_OP(not in) ; 192 POP_JUMP_FORWARD_IF_FALSE -> 198   # 内层条件（false 区内还有一条前向条件跳转）
194 LOAD_CONST None ; 196 JUMP_FORWARD -> 200
198 LOAD_CONST False
200 LIST_APPEND / MAP_ADD
```

落地核只取**第一条**条件跳转作为三元，然后把 false 区整段指令切片交给通用重建器
（`false_expr = self.expr_reconstructor.reconstruct(false_instrs)`），通用重建器不认识区域内的
第二条前向条件跳转，于是丢掉内层的条件与内层 true 臂，只留下最后一个常量：
产物发成 `... else False for stock in stocks_bk`（`quote_handlerOK.py:203`），
即 `{stock: True if ... in delisting_set else False ...}`，而源码是
`... else (None if ... not in ashares_list_local else False)`。少发 6×2 条指令。

## 判据（符合区域归约算法）

false 区域内若还存在前向条件跳转（`BACKWARD` 条件是推导式 filter 回边，排除），说明该区域本身
又是一个三元区域 ⇒ **递归调用 `_detect_comp_ternary`，把内层先归约为一个 `IfExp` 抽象节点**，
外层把它当作 `orelse` 持有（嵌套区域在父层就是一个抽象节点、块唯一归属、内层→外层归约）。
递归未命中（内层并非三元）时 `false_expr is None` 逐字回落到原重建调用，因此该判据是**严格附加**的。
判别式只用运算码类别与区域切片边界，不读名字/常量/绝对偏移/指令数。

## 可达性证明（本轮的发货面为什么只有 1 支文件）

`D:/Temp/r54gate/reach54.py` 静态枚举 `site-packages` 下**全部 1719 个 pyc**（不只索引的 402 支）：
推导式码对象 1642 个，其中「≥2 条前向条件跳转」——即本判据唯一可能开火的形状——只有 **3 个**，
分属 2 支文件：`IQCommon/strategy/wizard_quant_api.pyc` ×2、`fly/data/quote_handler.pyc` ×1。
实测与之一致：`wizard_quant_apiOK.py` 产物 **逐字节不变**（其推导式已由既有路径正确重建），
`quote_handlerOK.py` 只有 **1 行**变化（推导式那一行），984 行不变。

## 门禁

- **电池**（`D:/Temp/r54mine55/`，12 例，`run55b.py`）：落地核 **12/12 MATCH**；落地前 **8 MISMATCH / 4 MATCH**。
  复现族：dict 值（`w55_01` 与真实缺陷同数 `orig=39 decomp=25`）、list 元素、set 元素、genexp 元素、
  dict 键、三级嵌套、臂为调用；阴性对照 4 例两臂均 MATCH（单三元推导式、赋值式嵌套三元、
  调用实参式嵌套三元、循环体内嵌套三元）⇒ 推导式元素上下文是必需的，判据不过火。
- **G0** 16 靶逐函数严格值：仅 `quote_handler 65/72 → 67/72`，其余 15 靶逐字未变
  （含金丝雀 `quotation 148/150`、`klinedata 56/63`），合计 `760/851 → 762/851`。
- **G4** 全量 544 路径 A/B（臂对 Round 53 落地核产物 `g453_c53a.jsonl`）：
  `TALLY SAME=543 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`，`files fully matched 485 → 485`
  （quote_handler `52/57 → 54/57`）。
- **G4′** 受影响文件逐码对象严格 A/B：`strict defects 7 → 5`，
  `FIXED is_delisting_stock_local`、`FIXED is_delisting_stock_local.<dictcomp>`，`BROKEN=0`。
- **G5** 落地核重跑 ⇒ 电池 12/12；`quotation.pyc` 官方 `143/143`、严格 `148/150`
  （缺陷集合与落地前逐字相同：`change_his_to_forward`、`get_trend`）；
  `test_repros/round16_sink` 15/15 MATCH（第 16 项 `run_all.py` 是驱动脚本）；
  落地核产物与通过门禁的臂产物**逐字节相同**（`quote_handler landed==arm: True`）。
- **G6** `batch --index pyc_index.json --all --round 54`：**402 verified / 0 failed**，
  `ok_pyc 375 / partial_pyc 27 / failed_pyc 0`；全量重跑只有 1 支 `*OK.py` 变化
  （`site-packages/fly/data/quote_handlerOK.py`，工具生成，无手改产物）。
  另先跑一轮不含 `--all` 的 partial 批回归（27 支，0 failed）。
- **G7**（`stats` 原样）：`total_functions 5746`（分母未动）、`matched_functions 5667 → 5669`、
  `cumulative_match_rate 98.63% → 98.66%`。`pyc_index.json` 值域变化仅 2 条
  （`quote_handler matched_functions 52 → 54`、其 `bytecode_match_rate 0.9123 → 0.9474`），
  纯 CRLF 4553 行、裸 LF 0。

## 否证、旁支与移交（Round 55）

1. **线 A（`fly/common/market_time.pyc :: MarketTime.is_open`，`seq_len orig=67 decomp=69`）本轮不发货**。
   诊断给出的两枚臂中 `spec_s2.json` 能把该文件推到严格 `10/10`（条件正确发成
   `A and B or C and D`、`return False` 回到兄弟位），但实测否决两条：
   `fly/data/quotation.pyc 148/150 → 147/150`（`get_quote`、`fetch_quote_and_text`/`_merge_quotation_datas`
   整支塌成 `orig=82 decomp=1`）与 `IQCommon/api/klinedata.pyc 56/63 → 55/63`（新增
   `_is_same_type_date seq_len orig=97 decomp=71`）；另一枚 `spec_s1.json` 对 `is_open` 产物逐字节惰。
   诊断报告引用的 `_try_build_if_region` / `_build_if_region_from_block` /
   `_try_build_ternary_conditional` 三个符号在仓库中**不存在**（已 grep 证伪），机制叙述不得沿用。
   可开证的形状仍在：被判为「else 臂头」的块其正常流并不落到声称的 merge（`210` 的假边去 `316`，
   而 merge 是 `258`）⇒ 同层「臂必须终结于 merge」前置判据，须以 `quotation`/`klinedata`
   两处反例为硬否决跑电池。
2. **线 C（`order_api :: future_order 101/93`、`option_order 83/74`）三枚草图全部否证**，但根因改判清楚：
   程序顺序上最先失败的是 `_try_build_ternary_merge_consumer_expr`（`region_ast_generator.py:39591`，
   调用点 34805/34967/36743）向 `expr_reconstructor` 要重建值时拿到 `None`——**通用表达式重建器
   不支持 `KW_NAMES`**；且绑定到的 `CALL` 是外层调用（`total_args=1`）而非拥有 kwargs 的 `.format` 调用。
   最小复现体 `wit54c/s14_unguarded_fmt_2tern_kwonly.py`（`orig=21 decomp=9`，**两个**三元 kwarg 才触发；
   单三元 kwarg 正确）、精确实形复刻 `wit54c/w16_guarded_real_shape.py`（`orig=33 decomp=25`）；
   33 例电池落地态 `MISMATCH=21 MATCH=12`。语料普查（27 支 partial / 1078 码对象）命中 6 个形状、
   其中 4 个真丢语句：`future_order`、`option_order`，加
   `plugin_system_log/__init__.pyc :: DefaultLogger.setup`（2→0）与
   `trade_live_broker.pyc :: _process_order`（2→1）⇒ **`KW_NAMES` 重建支持是 Round 55 首选靶**，
   一判据可同时触及 giants `-65` 与 `-55`。`base_order [target_diff] #136` 不属此族
   （对齐显示 0 丢 0 增，仅 `POP_JUMP_IF_TRUE` 目标 1124→926 偏差）。
3. **Round 55 靶已量化**：`D:/Temp/r54gate/loss54.py`（操作数用量差）给出三大损失归属——
   `DefaultLogger.setup -65` 丢整段语句组（`os.path.join`×3、`config.backtest`×4、
   `RotatingFileHandler`、`10485760`、`'UTF-8'`）并**多出 5 条跳转** ⇒ 若级联被吸收，属
   Round 48/49 的 merge 归属线；`get_kline_local -78` 丢 10× `BUILD_SLICE`/`end` 与 5×
   `STORE_FAST end_time`+`'1530'`+`int` ⇒ 循环体丢语句；`get_TradeMode_trades -90` 损失以
   `COPY`/`SWAP`（各 14）为主 ⇒ 每出口路径 except 尾声族（F2）。
   另：全语料 117 条严格缺陷中**只有 1 条**是推导式形状（`D:/Temp/r54gate/comp54.py`），
   故本轮族的语料收益已到顶，Round 55 不得再走推导式路线。
4. **线 B（伪造尾随 `continue`，`_on_set_positions 297/298`、`finance :: func_get_fundamentals_daily_data
   192/193`）与线 D（4 胞胎 `api_get_from_zeromq target_diff`）诊断随本轮结束仍在进行**，
   其产物在 `D:/Temp/r54bdiag/`、`D:/Temp/r54ddiag/`；线 B 的三枚草图 spec
   （`spec_sk1/2/3.json`）已入库归档，结论未出，Round 55 先复核再定靶。
5. 本轮起 `subagent` 池触发每日配额上限（Round 55 预备诊断代理被拒），
   上述 1-4 项取证改由主线自查完成，脚本与日志全部留档可重跑。

## 归档

`rounds/round54/`：本文件 + `wit54comp/` 12 支复现体 + `spec_c54comp.json`
+ `land54.py`/`mkc.py`/`run55b.py`/`reach54.py`/`loss54.py`/`comp54.py`/`g054base.py`
+ G0（`g054base.log`、`g054_cmp_a/b.log`）+ G4（`cmp_g4_all.jsonl` 与分片日志）
+ G4′/G5/G6/G7 日志 + `order_api` 线（`FINDINGS54c.txt`、`wit54c/`、三枚 sk spec）
+ 线 A 的 `spec_s1/s2.json` 与 `prod_{landed,s1,s2}_market_time.py` 三件产物对照。
