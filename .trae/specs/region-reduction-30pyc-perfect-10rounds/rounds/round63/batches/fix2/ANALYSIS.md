# Round 63 fix2 — 条件语境 BoolOp 停止吸块（R63-B4 boolop_exit）

本文件由集中验证方（主代理）撰写：fix2 子代理未留下 ANALYSIS.md。数字全部来自
`fix2/dump/` 自产记录与集中重测，逐条可回溯。

## 交付物（已落地）

`specs/cand_r63b4_boolop_exit.json` —— `core/cfg/region_analyzer.py` 单 edit，+22 行
（含三要素注释），落地后 sha256 `c694d2514eb2f2b21ccf` / 1 721 959 B / 纯 CRLF 27 590 /
无 BOM，与测量镜像 `mirr_final` 逐字节相同。

改动本体：`_all_ternary_cond_c = not (is_condition_context and merge is not None)`
（原为 `= True`），并把 `_BOOLOP_CHAIN_JUMPS` 提为局部量。判据与上方既有的
「条件上下文收回块集」语句完全同一，不新增形状判据。

## 靶形态

`site-packages/IQData/plugins/plugin_system_fly_historyquote/history_data_source.pyc
:: HistoryDataSource.get_kline_by_count`（L623-630）。BoolOpRegion@0 是 if 的测试，
块集收回后又把语句体首块 128 与 if 之后的 172 吸为三元 true/false 值块，
导致 128 的条件被并成第三析取支、172 无人发射，实测缺 13 条指令（854/841）。

## 单变量见证（本工作区自测，同一靶 + 自有最小复现）

最小复现 `test_repros/round63_fix2/r63b4_cond_boolop_stmt_steal.pyc`（13 个函数，
两个受害形状 `cond_boolop_steals_stmt_block` / `cond_boolop_merge_test_terminated`）。

| 臂 | 靶 history_data_source | 自有复现 |
|---|---|---|
| landed（落地前基线） | 16/18，get_kline_by_count 854/841、get_price 550/544 | — |
| f2 = 仅本 fix | 17/18，get_kline_by_count 已清 | **13/13** |
| ts1 = 仅 b4 三元让位判据（生成器侧） | 17/18，get_price 已清 | 11/13（本 fix 的两个形状各缺一截） |
| b4c = f2 + ts1 | **18/18，mism 空** | **13/13** |
| f3 = 去掉 store 门控的放宽版 | 16/18（854/852 反而新引入偏差） | 11/13 |
| b4x = 直接关掉整个值块扩展 | 17/18（只修一半） | 13/13 |

两条结论按证据成立：
1. **f2 与 ts1 必须成对**——单用任一支都把靶从 16/18 推到 17/18 但各自砸开另一处，
   且 ts1 单独使用时砸的正是 f2 负责的形状。与项目记忆
   `analyzer-generator-pair-inertness` 同一形状（两支只在同时落地时共同生效）。
2. **f3、b4x 两个更宽/更 blunt 的变体被自有复现与靶同时证伪**，不落地。

## 全量对照（本工作区 402 支）

`h62.py ab --a=fix2/dump/landed_402.jsonl --b=fix2/dump/b4c_402.jsonl`：

```
TALLY SAME=399 IMPROVED=1 REGRESSION=0 MOVED=2 ERR=0   影响面 3/402
IMPROVED history_data_source 16/18 -> 18/18
MOVED    trade_live_broker  fund_transfer [123,88,1,57] -> [123,106,1,57]
MOVED    flyAccount         _do_request  [436,429,2,379] -> [436,443,2,384]
files fully matched 381 -> 382
```

`--a=landed_402 --b=b4x_402`（blunt 变体的影响面）：SAME=401 IMPROVED=1 REGRESSION=0，
完全匹配文件停在 381 —— 更宽的做法在全量上没有额外收益，只在靶上少修一支。

## 落地后集中门禁（与本工作区无关的复核，记录于此供交叉对照）

- 官方 `single` 靶：18/18 100.00%，`*OK.py` 由工具链重写（源 31 915 字符）。
- 金丝雀 quotation：官方 143/143、严格 148/150，缺陷集逐字未变；market_time 官方 10/10、严格 10/10。
- 全量 `batch --index pyc_index.json --all --round 63`：402 verified / 0 failed / ok 382 / partial 20，
  `stats` 5746 / 5677 / 98.80%。
- 索引逐条目比对 HEAD：401 支仅 `last_tested_round` 变化，唯一实质变化即靶条目
  （partial→ok、16→18、88.89%→100%）。
- 工作树里被改动的生成产物恰 4 支 `*OK.py`（靶 + matcher + trade_live_broker + flyAccount），
  与合并臂 402 对照的 MOVED/IMPROVED 集合一致。

## 残余（不粉饰）

- `get_kline_by_count` 严格尺 orig 857 → decomp 859（+2 过冲）；`get_price` 553 → 555（+2）。
  落地前是 844 / 549（缺 13 / 缺 4）。缺失变过冲，严格计数仍 22/24。
- `_do_request` 严格尺 431（缺 5）→ 445（多 9），官方 21/23 未动。
