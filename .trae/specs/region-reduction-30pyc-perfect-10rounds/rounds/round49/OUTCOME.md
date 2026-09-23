# Round 49 · 出货结论

## 落地的单条同层判据：R49-A

站点：`core/cfg/region_analyzer.py` 中两处会把 `merge` 绑成 `else_succ` 的兜底
（落地前行号 17012 `_else_has_external_pred`、17055 短路链兜底），
新增同层谓词 `_r49a_shared_sink_tail_merge` 在两处之前先取「两臂真正汇合的公共 sink 尾块」。

```python
_r49a_tail = self._r49a_shared_sink_tail_merge(
    block, then_succ, else_succ, _if_struct_blocks)
merge = (_r49a_tail if _r49a_tail is not None else else_succ)
```

判据四条合取，全读结构事实（块身份／前驱·后继／终结符操作码类别），
不读名字、常量、绝对偏移、指令数、历史清单（原则 1「块 = 前导语句 + 唯一终止符」
＋原则 2「每块唯一归属，且归属者必须发射该块」）：
① `else_succ ∉ then 臂前向闭包`（闭包不越过条件结构块）；
② 候选 `t ∈ 闭包`、`t ∉ 结构块`，其终结符属 return/raise 族且无正常流后继（纯 sink 尾）；
③ `t` 有前驱 `p` 既不在闭包内也不属结构块，且 `p` 不经闭包即可由 `else_succ` 前向到达
（⇒ 另一臂真的汇入 `t`）；④ 满足 ①..③ 的 `t` 唯一。命中返回 `t`，否则返回 `None`
⇒ 逐字保留原兜底世界。

## 根因（编排方独立实测，非推论）

靶：`site-packages/IQCommon/api/klinedata.pyc :: <module>.get_history_new`
（官方 `322 条 orig / 321 条 decomp`，strict `seq_len orig=322 decomp=323`）。

1. 用带打印的镜像核对阻塞站点：该 if（`H=298 T=312 E=1556`）在 **17012** 绑 `merge=1556`；
   同文件的短路链兜底 **17055** 另有 `H=154 T=312 E=1556` 一支（两站点都会绑 `else_succ` ⇒ 判据必须同时挂在两处）。
2. `NCPD(312,1556)=None`（then 臂内含 `RETURN_VALUE` 出口块 1350）；
   `_compute_merge_from_jump_targets` 亦 `None`——其第 1 步只读 `then_succ` **自身**的 `JUMP_FORWARD`，
   而本形状的臂出口在更深的块 1548/1550。
3. 真实汇合点是函数尾部块 `1678`（`LOAD_FAST kline_data_dict; RETURN_VALUE`，
   前驱 `1548/1550/1674`）。`merge=1556` 使 `_collect_branch_blocks(312, 1556)` 沿 then 臂
   越过 `1678` 把它吸入臂内 ⇒ 尾部 `return` 被重复发射：臂内 2 条（原处只 1 条 `JUMP_FORWARD`）
   ＋函数末尾退化为隐式 `return None`（`LOAD_CONST None`）。
   CPython 3.11.7 不合并相同 return 尾（`dis` 复核），故发射侧复制不可能复原原字节面——
   Round 48 移交的「发射侧按路径重复」假设就此否证，正解是把 merge 归回真实汇合块。

谓词命中普查（离线对同一 CFG 跑判据，`w49eval_preland.txt`）：该函数 15 个 if 区域中
**恰 1 个**命中（`H=298 → 1678`，唯一候选、唯一闭包外前驱 1674），其余 14 个 `cands=[]`。
落地后同址复验：`H=298 merge=1678`（`w49eval_get_history_new.txt`）。

字节面：`region_analyzer.py` `0e1c4ce1417fe38993ab` → `c644a6ccab745ac6be0e`，
len 1 683 289 → 1 687 755，CRLF 27 049 → 27 126（裸 LF 0），无 BOM，单文件 3 hunk（1 定义 + 2 站点）；
`region_ast_generator.py` 逐字节未动 `2a3d522b0ec9e8fe66e4`（BOM 保留）。

## 门禁（编排方独立复跑，非代理数字）

臂 `D:/Temp/r43gate/mirr_r49a`（spec `spec_r49a.json`，`mkspec49a.py` 生成、`build2.py` 构造，
镜像 == 落地面已断言；落地后工作树产物与臂产物逐字节相同）。

- **G0 靶文件逐函数 strict**：`klinedata.pyc` 缺陷 `11 → 10`，
  `get_history_new seq_len orig=322 decomp=323` → `clean ok`；其余 10 支缺陷消息逐字未变。
  合成电池 `g049.py`（4 个 code object）两臂 `MISMATCH=1 MATCH=3 ERROR=0` 逐项相同（惰）。
- **G1 变化面**：sha 变化产物 **仅 1 支**（`g49_changed.txt` = `IQCommon/api/klinedata.pyc`）。
- **G2′ 电池 143 支**：`SAME=143 IMPROVED=0 REGRESSION=0 MOVED=0`。
- **G3 锚点 109 支**：`SAME=109 IMPROVED=0 REGRESSION=0 MOVED=0`。
- **G4 全量 544 路径（唯一发货判据）**：`TALLY SAME=543 IMPROVED=1 REGRESSION=0 MOVED=0`，
  `files fully matched a=484 b=484`；402 索引子集 `SAME=401 IMPROVED=1 REGRESSION=0`。
  改进项：`klinedata.pyc 40/45 → 41/45`。
- **G4′ 尺上逐支 strict 复验**：`affected=1 fixed=1 broken=0 changed=0`（官方尺可见的真修复，非假 ok）。
- **G5 single**：`klinedata.pyc total_functions 45 / matched 41 / 91.11%`，
  mism 只剩 `_all_bars_of_cache`、`get_all_real_daily_kline`、`get_multiminute_his_data`、
  `kline_datetime_list`；金丝雀 `fly/data/quotation.pyc 143/143 100.00%`；
  `test_repros/round16_sink/run_all.py` `repros=15 MISMATCH=0 MATCH=15 ERROR=0 UNEXPECTED=0`。
- **G6** `batch --index pyc_index.json --all --round 49`：402 verified / 0 failed。
  索引差异：`401` 条仅轮次戳变化；值域差异 `1` 条
  （`IQCommon/api/klinedata.pyc`：`matched_functions 40→41`，`bytecode_match_rate 0.8889→0.9111`）。
- **G7 stats 原样**：

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

## 残余与移交 Round 50

- 同文件同族已不再受本判据影响，但 `get_multiminute_his_data`（strict `481/482`）与
  `kline_datetime_list`（`390/391`）仍各差 1 条，`_all_bars_of_cache`（`230/231`）同形；
  三者均非「臂吞掉尾部公共 sink 块」形状（本判据在其区域内 `cands=[]`），需各自另找同层事实。
- 本判据只在 `merge` 即将退化为 `else_succ` 的两处兜底生效，未覆盖 `merge = else_succ`
  的其余 10 处绑定点（16770/16826/16853/16908/16913/16915/16953/17109/17240/17317）；
  若后续靶子落在那些站点，应按同一谓词逐站点开证，不得一次全铺（合并补全是级联兜底，非单调）。
- 链式汇合候选线（`order_api :: future_order [101,92,2,36]`、`option_order [83,73,3,39]`：
  `_chain_merge_candidates` 的 `len(_non_empty_exits) == 1` 分支里，已被 `TernaryRegion`
  臂认领的候选不得再作链 merge）与 `else` 体内 merge 之后尾随块的 `_elif_struct_blocks` 回填，
  仍是从 Round 45/46 挂着的第一优先线索。
- 台账（未变）：`plugin_system_log/__init__.pyc :: setup`（320/253）、`matcher::match`、`clock_worker`、
  `decrypt_database_url 295/324`、`events 510/508`、`_init_config 86/84`、`OverNightOrder.__init__`、
  `api_base::get_history_df −24`、`write_logging_thread 113/113 j1`、`init_connection 42/41`、
  `params_analysis 133/126`、`quote_handler::get_kline_local 760/682 j12`、`handle_exrights 276/268`、
  `trade_live_broker 105/119`、`real_quote 39/44`、`fly/data/quote.pyc 69/81`、
  Round 48 五条等长 `seq_diff` 函数。
