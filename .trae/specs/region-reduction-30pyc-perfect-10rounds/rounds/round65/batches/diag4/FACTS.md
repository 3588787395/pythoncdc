# Round 65 · diag4 · FACTS.md

工作目录 `D:/Temp/opencode/r65gate/diag4`。所有读数用官方 `bytecode_diff`（`h62.py run`）。
一律 `python -X utf8`，未设 `PYTHONIOENCODING`。**仓库零改动**（见 §0）。

## 0. 仓库完整性自检（开工前 / 收工前各跑一次）

```
python -X utf8 -c "import hashlib,io;\
 p=r'F:\Downloads\pythoncdc-main\core\cfg\region_ast_generator.py';\
 b=io.open(p,'rb').read(); print(len(b), hashlib.sha256(b).hexdigest()[:12], b.count(b'\r\n'), b.count(b'\n'))"
```
| 文件 | 落地基线（BRIEF §4） | 实测（开工） |
|---|---|---|
| `core/cfg/region_ast_generator.py` | 3 103 668 B / sha `c9099bb0fc35` / BOM+CRLF / 裸LF=0 | **3 103 668 / c9099bb0fc35 / CRLF=50149 裸LF=0 / BOM=True** ✔ |
| `core/cfg/region_analyzer.py` | 1 725 369 B / sha `24a88392ee61` / CRLF / 裸LF=0 | **1 725 369 / 24a88392ee61 / CRLF=27635 裸LF=0 / BOM=False** ✔ |

`git status --porcelain` 开工时仅 ` M .trae/specs/.../round64/OUTCOME.md`（主代理文档）+ 既有未跟踪脚本，
core 两文件未出现在改动列表；diag4 全程未写仓库（所有臂只写 `D:/Temp/opencode/r65gate/diag4/mirr_*`、`build_*`）。
`emit_spec.py` 的 anchor 直接从业已落地的 LF 归一字节里切出，`h62.py build` 断言 `anchor occurrences==1` 通过。

## 1. landed 基线（targets 4 支，`dump/landed.jsonl`）

复现：`python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl`

```
landed real_quote.pyc               39/44  [get_cache_l2_data 337/335 jd2 t313,
   get_cache_l2_data_by_one 321/320 jd2 t300, get_real_minute_kline 253/254 jd3 t197,
   get_tick_direction 259/258 jd3 t102, one_prod_to_ndarray 605/607 jd5 t424]
landed klinedata.pyc                42/45  [get_all_real_daily_kline 188/187 jd3 t26,
   get_multiminute_his_data 479/478 jd5 t16, kline_datetime_list 389/389 jd9 t228]
landed __init__.pyc                 32/35  [_on_publish_after_trading_end 486/481 jd3 t33,
   _save_testds_to_csv 71/68 jd7 t19, get_TradeMode_trades 1839/1801 jd4 t1617]
landed trade_info_utils.pyc         38/40  [get_trade_list 339/323 jd14 t148,
   trade_operation 304/302 jd2 t40]
```
与 BRIEF §5 完全一致（sha 级）。

## 2. landed 基线（battery 19 项，`dump/battery_landed.jsonl`）

复现：`python -X utf8 h62.py run --arm=landed --list=battery.txt --out=dump/battery_landed.jsonl`

| # | 文件 | matched/total | 残余 |
|---|---|---|---|
| 1 | r63_ft.pyc | 2/2 | — |
| 2 | r63_ft2.pyc | 2/2 | — |
| 3 | r63_ft4.pyc | 1/2 | t4 31/22 jd1 t23 |
| 4 | probe_r63b2_cases.pyc | 7/9 | c6_elif_try_then_more 50/50 jd1 t15; c8_elif_chain_only 31/33 jd1 t15 |
| 5 | probe_r63b2_cases2.pyc | 7/9 | d2_elif_notry 44/45 jd1 t28; d8_elif_try_chain_or_plain 51/50 jd1 t6 |
| 6 | repro_r63b2_tail_cmp_return.pyc | 2/2 | — |
| 7 | r63b3_chained_value_ctx_prefix.pyc | 2/2 | — |
| 8 | r63b4_tern_in_elif_chain.pyc | 3/3 | — |
| 9 | r63b5_w1.pyc | 1/2 | init_connection 42/41 jd0 t25 |
| 10 | r63b3_chainstore_prefix.pyc | 2/2 | — |
| 11 | r63b4_cond_boolop_stmt_steal.pyc | 13/13 | — |
| 12 | **r64d1b_closed_exit_prefix.pyc** | **2/2** | — （R64-diag1 chain.pop 的 witness，全绿） |
| 13 | r64d1b_sibdispatch_attempt.pyc | 4/4 | — |
| 14 | r64d2_chain_yield_sibling_entry.pyc | 2/2 | — |
| 15 | r64d2_valuectx_consumer.pyc | 2/2 | — |
| 16 | r64d3_postif_join.pyc | 2/2 | — |
| 17 | r64d4_boolop_poptop_merge.pyc | 3/3 | — |
| 18 | r64d4_deferred_prefix.pyc | 3/3 | — |
| 19 | r64d5_contsink.pyc | 1/2 | probe 122/122 jd1 t9 |

battery 合计 matched=**53** / total=**62**（19 支里 13 支全绿）。

## 3. landed 基线（canary 4 支，`dump/canary_landed.jsonl`）

复现：`python -X utf8 h62.py run --arm=landed --list=canary.txt --out=dump/canary_landed.jsonl`

| 文件 | matched/total | sha 前缀 |
|---|---|---|
| fly/data/quotation.pyc | 143/143 | 见 jsonl |
| fly/common/market_time.pyc | 10/10 |  |
| IQCommon/util/datetime_func.pyc | 26/26 |  |
| IQData/utils/datetime_func.pyc | 25/25 |  |

canary 全部 100% 匹配 —— 验收标准是候选下**逐支 sha 不变**。


---

# 4. 候选 n1 —— analyzer 侧 `[R65-diag4 n1 operand-rejoin exemption]`（**成立**）

## 4.1 缺陷定位（klinedata `get_multiminute_his_data`，code obj 首行 1009）

复现：`python -X utf8 probe_pop.py <pyc> get_multiminute_his_data`
（sys.settrace 挂在落地 analyzer 的 `chain.pop()` 行 25601，**不改任何文件**）

落地全函数只有 **1 次** [R64-diag1] pop：
```
POP line=25601 start_block@824 current@1094 chain=[(824,'or'),(1090,'or'),(1094,'and')]
    T@1314 cj@1144 ft@1136 caller=_detect_boolop_chain_start
```
真实源码（`dis` 偏移 1086..1382）：
```
1086 LOAD_FAST fq            ; POP_JUMP_IF_NONE  -> 1314     # A: fq is None
1090 LOAD_FAST dividends_all ; POP_JUMP_IF_NONE  -> 1314     # B: dividends_all is None
1094 isinstance(fields,str)  ; POP_JUMP_IF_FALSE -> 1144     # C  (op_type 派生成 'and')
1136 fields in tmp_fields    ; POP_JUMP_IF_TRUE  -> 1314     # D: C and D
1314 need_exrights = 0            ; JUMP_FORWARD -> 1382     # T = if-body
1320 fq in DIVIDEND_CALC_TYPE ...                             # else 分支入口 1144 之后
```
即条件为 **`if fq is None or dividends_all is None or (isinstance(fields, str) and fields in tmp_fields):`**
—— 三个 `or` 操作数，第三个是 `and` 子链。pop 撤销第 3 个操作数后，链只剩 `[824,1090]`，
`(C and D)` 被拆成**下一条语句**的条件，BoolOpRegion@824 blocks=[824,1090] 与 IfRegion@824
blocks=[1338,1320,824,1094] 争抢，jumpdiff 3→5。

## 4.2 为什么移交线索的字面判据不可用（实测）

`test_repros/round64_diag1/r64d1b_closed_exit_prefix.pyc::kbin_repro`（R64-diag1 的 witness，落地 2/2）
的 pop **形状与 klinedata 完全同构**：
```
POP start_block@0 current@62 chain=[(0,'or'),(48,'or'),(62,'and')] T@124 cj@92 ft@74
```
| | klinedata@1094 | witness@62 |
|---|---|---|
| chain 算子序列 | or,or,and | or,or,and |
| 被 pop 块是否链首 | 否（chain[0]=824） | 否（chain[0]=0） |
| 真值 | **同一条 or-run 的第 3 操作数** | **下一条语句 `if c == 6:`** |

⇒ 「被 pop 的块自身是 or-run 首块」这一条件在两边都**不成立**，写进去等于把判据整体关掉
（klinedata 修好、witness 与 quote_handler 的收益一起丢）。判别量必须在**边的汇入关系**上：
- klinedata：current 的落空边 ft=1136 的末指令 `POP_JUMP_IF_TRUE -> 1314` **就是 T** → run 未闭合；
- witness：current 的两条后继 74 / 92 末指令都是 `JUMP_FORWARD`（落到 merge/next），**无一汇入 T** → run 已闭合。

## 4.3 判据（同层次结构身份）

**识别条件**：`_detect_boolop_conditional_chain` walk 中 `len(chain)>=3`；链前缀 `chain[:-1]` 全部短路到同一块 T
（落地 [R64-diag1] 已判定的 `_r64_closed`）；`current` 的跳转边 `_r64_cj` 与落空边 `ft_succ` 都不是 T
且 `T is not current`（落地原 pop 前置条件全部成立）；**并且** `current` 的某条后继块（`ft_succ` 或 `_r64_cj`）
自身的末指令属于 `BOOLOP_CHAIN_JUMPS` 且其跳转目标 `is T`。
**归约方式**：此时 `current` 不是新语句的入口，而是**本算子 run 的第 (n) 个操作数（一个 `and` 子链的头）**，
其真值边一跳即汇入 run 的共享目标 T；因此**不 pop、不 break**，链继续按 `chain[-1]=(current,op_type)` 扩展，
`current` 仍归属同一个 BoolOpRegion（原则 2：每块唯一归属；原则 3：只有嵌套**区域**才是抽象节点，
一跳汇入 T 的块不是嵌套区域）。
**AST 映射**：`BoolOp(or, [A, B, BoolOp(and, [C, D])])` → `if A or B or (C and D): body`；
pop 的副作用是把 C 当成下一条语句、翻转其极性并把 D 变成孤儿。

De Morgan 形态 `if a is None or b is None or (c and d):` 正是本判据的目标：前两个 `is None`
操作数共享 body T，第三个操作数是 `and` 子链，其头块的两条边都不是 T，但落空边的末指令跳 T。

## 4.4 实测读数

spec `specs/cand_n1.json`（1 edit，`core/cfg/region_analyzer.py`，anchor 唯一，+29 行，CRLF/BOM 校验通过）

```
python -X utf8 h62.py build --spec=specs/cand_n1.json --dst=n1
python -X utf8 h62.py run --arm=n1 --list=targets.txt --out=dump/n1.jsonl
python -X utf8 h62.py run --arm=n1 --list=battery.txt --out=dump/n1_battery.jsonl
python -X utf8 h62.py run --arm=n1 --list=canary.txt  --out=dump/n1_canary.jsonl
printf 'F:/Downloads/pythoncdc-main/site-packages/fly/data/quote_handler.pyc
' > qh.txt
python -X utf8 h62.py run --arm=n1 --list=qh.txt --out=dump/n1_qh.jsonl
python -X utf8 cstrict.py build_n1 targets.txt dump/n1_strict.json
```

| 名单 | landed | n1 | 结论 |
|---|---|---|---|
| targets A/B | — | `SAME=3 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0` | 无回归 |
| klinedata | 42/45，`get_multiminute_his_data [479,478, jd5, t16]` | 42/45，同函数 **jd 5→3** | R64 唯一实测代价被收回 |
| klinedata 严格尺 | **54/63** | **56/63** | 修好 `get_kline_by_date_new`、`get_multiminute_his_data_by_date`（都是 `POP_JUMP_IF_NONE` target_diff） |
| battery 19 项 | matched 53/62 | **SAME=19**（逐支 sha 不变），matched 53/62 | 不退，含 `r64d1b_closed_exit_prefix` 2/2、`r64d1b_sibdispatch_attempt` 4/4、`r64d4_*` 6/6 |
| canary 4 支 | 143/143,10/10,26/26,25/25 | **SAME=4**（sha 全不变） | 通过 |
| **quote_handler（硬验收）** | **57/57** | **57/57，SAME=1，sha 不变** | **R64 收益未丢** |

其余三支 targets 读数逐函数与 landed 全等（real_quote 39/44、risk_calculation 32/35、trade_info_utils 38/40 的
五个/三个/两个残余项元组不变）。

## 4.5 尚未覆盖的风险

n1 只在我名下 4 支 + battery 19 + canary 4 + quote_handler 上测过。判据是全局的（所有 or-run 都走这条路），
落地前必须由主代理跑 402 支全量。diag4 的分片复放见 §7。


## 4.6 全量爆炸半径（analyze-only，不生成 AST；402 支 + battery + canary 全覆盖）

`blast.py` 用 `sys.settrace` 挂在落地 analyzer 行 25601，对每个 code object 只跑
`build_cfg + RegionAnalyzer.analyze()`，统计 ① [R64-diag1] pop 次数 ② 其中 n1 的
operand-rejoin 豁免会抑制的次数。仓库只读。

```
python -X utf8 blast.py D:/Temp/opencode/r65gate/all402.txt --out=dump/blast_sK.jsonl --nshard=8 --shard=K   # K=0..7, 每片 50/51 支 ~70s
python -X utf8 blast.py D:/Temp/opencode/r65gate/diag4/rest.txt --out=dump/blast_rest.jsonl                   # 补齐 11 支
python -X utf8 blast.py D:/Temp/opencode/r65gate/diag4/battery.txt --out=dump/blast_batt.jsonl
python -X utf8 blast.py D:/Temp/opencode/r65gate/diag4/canary.txt  --out=dump/blast_canary.jsonl
```

全 402 支里 **只有 3 支文件会走到 [R64-diag1] 的 pop**：

| 文件 | pop 次数 | 被 n1 抑制（rejoin） | 影响 |
|---|---|---|---|
| `fly/data/quote_handler.pyc` | 1 | **0** | n1 完全不改变它 → 57/57 保持（实测 sha SAME） |
| `IQCommon/util/crypto_utils.pyc` | 2 | **0** | 不变 |
| `IQCommon/api/klinedata.pyc` | 4 | **4** | 全部是 `A or B or (C and D)` |

klinedata 的 4 个 rejoin 站点（函数名@首行 / chain / T / current）：
```
get_kline_by_count_new@321                 chain=[862,976,980]      T=1200 current=980
get_kline_by_date_new@673                  chain=[136,162,166]      T=386  current=166
get_multiminute_his_data@1009              chain=[824,1090,1094]    T=1314 current=1094
get_multiminute_his_data_by_date@1098      chain=[1472,1498,1502]   T=1722 current=1502
```
battery 19 支：`r64d1b_closed_exit_prefix.pyc` 1 次 pop、**rejoin=0**（witness 保持弹出），
其余 18 支 0 次 pop。canary 4 支：0 次 pop。
⇒ **n1 的作用域在数学上被限定为 klinedata 的这 4 个站点**；官方 A/B 的 `SAME=19 / SAME=4 / SAME=1(quote_handler)`
与之一致，这是「不丢别人收益」的直接证据，不需要靠全量重跑赌概率。

严格尺增量也解释了：n1 让 klinedata 严格 54/63→56/63，修好的两支正是上表里的
`get_kline_by_date_new`、`get_multiminute_his_data_by_date`。
