# Round 41 诊断 —— 开轮台账

落地基线：commit `11af6751`（Round 40 / R40-A2），
`core/cfg/region_ast_generator.py` 工作区字节 sha256[:20] `f1cde2536f9fa2c9033b`（2 991 175 B，CRLF 48 506，BOM 在位）。

## 一、目标池（对落地字节实测，非结转）

* 索引 `pyc_index.json`（G6 刚以 `--round 40` 回写）实测：**27 partial / Σdeficit 91 / 6 个 deficit-1**，
  `failed 0`，`decompile_status=ok` 375 支。
  列表：`D:/Temp/r41gate/pool27.txt`、`g1_d1.txt`（6）、`g1_d2.txt`（11）。
  deficit-1 六支：`IQCommon/manager/instance.pyc`、`IQCommon/util/replace_utils.pyc`、
  `IQData/utils/common_func.pyc`、`IQEngine/plugins/plugin_system_event_source/default_event_source.pyc`、
  `…/realtime_event_source.pyc`、`IQEngine/plugins/plugin_system_matcher/matcher.pyc`
  —— 其中后两支分别撞上已否证的循环 `else` 归属线（R34-E/F）与 `matcher::match`（R37-B NO-GO），
  本轮线 A 需绕开。
* **索引可复现性证明（同时充当本轮 G4 的 head 臂）**：
  `python -X utf8 r41g.py run --arm=landed --list=all402.txt`（3 分片并行，私有 ROOT 副本
  `D:/Temp/r41gate/r41g.py`，产物只写 `build_landed/`，仓库零写入）⇒
  `rows=402 unique=402 errors=0 empty=0`，逐文件与 `pyc_index.json` 比对 **402/402 一致、0 处不符**
  （`D:/Temp/r41gate/landed41.jsonl`、`verify_landed41.py`）。
  ⇒ 已发布索引是实测支撑而非自报，且本轮候选臂有了同源基线。

## 二、承重资产重基（对落地字节重测）

| 资产 | 实测 |
| --- | --- |
| G2′ `reprobat61.txt`（63 条目，Round 40 移交） | `errors=0 empty=0`，52 支全匹配，`landed.jsonl` 已存 `D:/Temp/r41gate/reprobat61_landed.jsonl` |
| G3 `anchors109.txt`（109 条目） | `errors=0 empty=0`，79 支全匹配，`anchors109_landed.jsonl` |
| G5 金丝雀基线 | 重新导出 `D:/Temp/r40gate/canary_shas_landed40.txt`（9 条目，比值逐个对 `pyc_index.json` 核过）。**判据已于 Round 40 更正**：承重文件不得掉官方函数；产物文本移动数只作观测量上报 |
| Round 40 新电池 `test_repros/round40_merge_not_a_merge/{r40w_witness,r40c_controls}.py` | 对落地字节复跑（`D:/Temp/r41gate/g0_landed41.txt`）：`CLEAN=2 DEFECT=0` ⇒ 见证已转为阳性、负对照仍绿；本族天然阳性对照改由 `ctl_two_cont` 承担（见 Round 40 §五·3） |

## 三、本族余量实测（决定候选优先级的编排方独立读数）

对 `landed41.jsonl` 的 per-function 明细聚合：官方尺下 **差一条指令（`orig − decomp == 1`）的函数有 15 支，分布在 7 支文件**：

| `.pyc` | 函数 | orig/decomp |
| --- | --- | --- |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | `get_cache_l2_data_by_one`、`get_tick_direction`、`one_prod_to_dataframe` | 321/320、259/258、432/431 |
| `fly/data/quote.pyc` | `check_frequency`、`one_prod_to_dataframe` | 121/120、484/483 |
| `fly/data/quote_handler.pyc` | `get_kline_binary`、`is_delisting_stock_local` | 129/128、95/94 |
| `fly/simtradding/flyAccount.pyc` | `init_connection`（`jump=0`，非跳转并族） | 42/41 |
| `IQCommon/api/klinedata.pyc` | `get_all_real_daily_kline`、`get_history_new`、`get_multiminute_his_data` | 188/187、322/321、479/478 |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | `_process_cancel_order`、`etf_basket_order`、`get_all_orders`、`ipo_stocks_order` | 293/292、693/692、79/78、1075/1074 |

⇒ 若线 B 的「臂中段逃逸回边」判据成立，其收益上界不止 `one_prod_to_dataframe` 两支；反之若只修两支，
说明该形状另有归属约束。此表仅作候选排序依据，不构成任何发货判据。

### 三之补：形状侧的编排方独立扫描（analyzer-only，`family_scan.py` → `family_scan2.txt`）

对同一批函数只读跑分析器，统计「`IfRegion(else 空, merge 非空)` 臂内的**非尾块**以无条件跳转指向某个
**包围循环的 `header_block`**」这一结构出现次数（并区分 `merge == / != loop.back_edge_block`）：

| 函数 | 该形状出现 | `merge != back_edge` | 官方尺读数 |
| --- | --- | --- | --- |
| `real_quote.pyc :: one_prod_to_dataframe` | 1 | 1 | 432/431（移交形状，线 B） |
| `quote.pyc :: one_prod_to_dataframe` | 1 | 1 | 484/483（同上孪生） |
| `trade_live_broker.pyc :: ipo_stocks_order` | **24** | 24 | 1075/1074 |
| `klinedata.pyc :: get_multiminute_his_data` | 2 | 1 | 479/478 |
| `klinedata.pyc :: get_history_new` | 1 | 0 | 322/321 |
| `real_quote.pyc :: get_cache_l2_data_by_one` | 2 | 0 | 321/320 |
| `check_frequency`、`get_kline_binary`、`is_delisting_stock_local`、`init_connection`、`get_tick_direction`、`_process_cancel_order`、`etf_basket_order`、`get_all_orders`、`get_all_real_daily_kline` | 0 | — | 同为 +1，但**不是本族** |

两条结论直接约束本轮取舍：

1. 移交形状（`merge != back_edge` 的臂中段逃逸）在两支 `one_prod_to_dataframe` 上各自**恰好一处**，
   编排方仪器独立复现，线 B 前提成立；
2. 同一形状在 `ipo_stocks_order` 里出现 **24 处却只丢 1 条指令** ⇒ 「臂中段逃逸」远不是充分条件，
   任何只以此为由的判据都会过度暴露（over-fire）。候选必须带第二重判别项，评估线 B 交付时
   以 `ipo_stocks_order` 与 `get_multiminute_his_data` 为首要反例。
   （第一版扫描把「最内层包围循环」排序写反，导致两支靶函数误报 no such shape——
   已修；负读数在修正前不可信，此处数字全部为修正后重跑。）

## 四、两条诊断线（均为 diagnosis-only，禁改 `core/`）

* **线 A**（`D:/Temp/r41diagA`，私有 harness 副本，禁用共享 `mirr_head`）：deficit-1 六支聚类后取最便宜的一族。
* **线 B**（`D:/Temp/r41diagB`）：`one_prod_to_dataframe` ×2 的臂中段 `continue` 归属；
  已交结构性事实（`B@1818 succs=[742]` 位于 `IfRegion(cond=746, then=[18 块], merge=1972)` 臂内中段，
  `back_edge_block=1864`），并显式划出不得复用的已落地判据与两支受保护的 `SHAPE` 反例。

编排方对两线交付一律做独立复核：锚点唯一性、见证在落地字节上确败、A/B 真身重跑，才进入 G0–G7。

## 五、线 B 前提的编排方独立复测（严格尺，直接读提交产物）

`D:/Temp/r41gate/premise_b.py`（difflib 对齐两条指令流）：

* `fly/data/quote.pyc :: <module>.Quote.one_prod_to_dataframe` ⇒ 严格尺 `orig=485 decomp=484`，`defect=True`；
* `IQData/plugins/plugin_system_realquote/real_quote.pyc :: <module>.RealQuoteData.one_prod_to_dataframe`
  ⇒ 严格尺 `orig=433 decomp=432`，`defect=True`（官方尺同一行读作 484/483 与 432/431，两尺计数法不同，不可互减）。
* 两条流的**首个差异块之前逐指令全等**，差异形如
  `700 POP_JUMP_FORWARD_IF_FALSE 1976` ↔ `700 … 1972`（目标恒差 4 字节），
  ⇒ 缺失点之后所有跳转目标整体平移 4 字节，与「仅缺一条指令、且缺的是 `@1862` 处 `JUMP_BACKWARD`」完全自洽。
  故线 B 的结构前提在落地字节上仍成立，不是 Round 40 落地后失效的结转读数。
