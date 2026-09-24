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
| **b4x = 本候选（窄门控）** | **17/18**，get_kline_by_count 元组消失（854/854 jd0 td0） | **13/13** |
| ts1 = 仅 b4 三元让位判据（生成器侧） | 17/18，get_price 已清、get_kline_by_count 未动 | 11/13（两个形状各缺一截 75/71、59/55） |
| b4c = b4x + ts1 | **18/18，mism 空** | **13/13** |
| f2 = blunt：整体关掉值块扩展 | 17/18 | 13/13 |
| f3 = 按块内容判据（候选值块含 STORE 即拒） | 16/18（854/852，只把 −13 收到 −2） | 11/13 |

（本表首版把 `b4x` 与 `f2` 两个标签写反、并把 `f3` 说成「去掉 store 门控」；已按下方
子代理自述附录更正，读数不变、归属更正。附录同时给出 `mirr_b4x` 的 region_ast_generator
与落地前逐字节相同（`b9778ee0…`/3 059 418），故 b4x 是单变量分析器臂。）

三条结论按证据成立：
1. **b4x 与 ts1 必须成对**——单用任一支都把靶从 16/18 推到 17/18 但各自留下对方的洞，
   且 ts1 单独使用时砸的正是 b4x 负责的形状。与项目记忆
   `analyzer-generator-pair-inertness` 同一形状（两支只在同时落地时共同生效）。
2. **f3 被证伪**：被吞的 128 本就不含 STORE，缺的是结构事实而非内容特征。
3. **f2（blunt）在本语料与 b4x 逐字节等价**（子代理 402 全量 `b4x→f2 : REGRESSION=0
   IMPROVED=0 MOVED=0 SAME=402`）⇒ P5 扩展在值上下文于本语料 inert；
   仍交付窄判据，理由是保留 P5 的本职用途，不是因为它在全量上多修了什么。

## 全量对照（本工作区 402 支）

`h62.py ab --a=fix2/dump/landed_402.jsonl --b=fix2/dump/b4c_402.jsonl`：

```
TALLY SAME=399 IMPROVED=1 REGRESSION=0 MOVED=2 ERR=0   影响面 3/402
IMPROVED history_data_source 16/18 -> 18/18
MOVED    trade_live_broker  fund_transfer [123,88,1,57] -> [123,106,1,57]
MOVED    flyAccount         _do_request  [436,429,2,379] -> [436,443,2,384]
files fully matched 381 -> 382
```

`--a=landed_402 --b=b4x_402`（本候选单臂的影响面）：SAME=401 IMPROVED=1 REGRESSION=0，
5675 → 5676、完全匹配文件停在 381 —— 与子代理自述的 `5676 / clean 381` 一致；
即窄门控单独落地不足以让靶转 ok，必须与 tern_slot 成对（b4c 才到 5677/382）。
blunt 变体 f2 与 b4x 在全量上逐字节等价（见上第 3 条），故本表不再单列。

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


---

# fix2 子代理自述（Round-63 batch-4 IMPLEMENTER，本轮定位与实测原始记录）

（上面主代理表格里的臂名与本工作区 `dump/` 的臂名不一致，先给键：
`b4x`=本候选窄门控；`b4c`=本候选 + `diag4/specs/cand_r63b4_tern_slot.json`；
`ts1`=仅 tern_slot；`f2`=把 `_all_ternary_cond_c` 直接置假（blunt 关扩展）；
`f3`=按块内容判据（候选块含 STORE 即拒）。主代理表把 b4x/f2 的职责写反了：
blunt 关扩展的是 **f2**，本候选是 **b4x**，二者在 402 上逐字节等价，见下。）

## Step 1 —— 实测「缺的是哪些语句」（`align.py`，非猜测）

`logs/align_landed_kline.txt`：`orig=944 decomp=930 deficit=-14`，12 个差异块，前 6 块全在函数头
62 条指令内。还原出的缺失原始语句（pyc 行号 / 指令偏移）：

| 原句 | 行 | 缺失指令（orig 偏移） | landed 产物实际写成 |
|---|---|---|---|
| `if len(asset) < 1 or count == 0:` | L624 | —（极性被反） | `if len(asset) < 1 or count == 0 or fields is None:`；@126 由 `POP_JUMP_IF_FALSE` 变 `POP_JUMP_IF_TRUE` |
| `return EMPTY_DAY_BAR_NP_ARRAY if fields is None else EMPTY_DAY_BAR_NP_ARRAY[fields]` | L625 | @144 JUMP_FORWARD、@146 LOAD_GLOBAL、@158 LOAD_FAST、@160 BINARY_SUBSCR（else 臂 4 条） | `return EMPTY_DAY_BAR_NP_ARRAY` + 死码 `return None` |
| `cur_date = convert_int_to_date(query_date)` | L628 | @172 LOAD_GLOBAL、@184 LOAD_FAST、@186 PRECALL、@190 CALL、@200 STORE_FAST（整句 5 条） | 整句消失 ⇒ 后续 `LOAD_FAST cur_date` 退化为 `LOAD_GLOBAL`（decomp @192/@282/@340/@386，即 orig[47]/[61]/[73]/[81] 四个单条替换块） |
| `if asset['type'] == 'FUTURE':` | L630 | @202 LOAD_FAST、@204 LOAD_CONST 'type'、@206 BINARY_SUBSCR、@216 LOAD_CONST 'FUTURE'、@218 COMPARE_OP、@224 POP_JUMP_IF_FALSE（测试 6 条） | 测试消失，then/else 两臂被拍平为顺序语句（landed 产物 L463/L464） |
| then 臂汇合跳转 | L631→L634 | @306 JUMP_FORWARD（1 条） | 消失 |

其余 3 个 `replace n=1` 块（orig[468]/[494]/[778]）是 `<code object at 0x…>` 地址串噪声；
末块 `insert decomp[928:930]` 的多余 `LOAD_CONST None; RETURN_VALUE`（+2）是 landed 既有形状，
官方尺归一化不计（`mirr_b4x` 产物上 align 只剩 3 个地址噪声块 + 这一个 +2）。

## Step 2 —— 吞语句的站点（实测，非推断）

只读诊断臂 `mirr_diag`（`specs/diag_boolop_log.json`，在 `RegionAnalyzer._create_boolop_region_from_chain`
建区域前落日志）打印本文件全部 7 条 BoolOp 区域（`logs/booldiag.txt`），越界吸块**只有一条**：

```
[DIAGBOOL] fn=get_kline_by_count chain=[(0, 'or'), (116, 'or')] cond=True merge=374
           blocks=[0, 116, 128, 172]        ← 128=语句体首块  172=if 之后的语句块
```

`probe2.py`（跑完整 `generate()` 之后才读 `region_analyzer.block_to_region`）：

```
blk 0   n=19 L?    term=POP_JUMP_IF_TRUE       succ=[116,128]
blk 116 n=4        term=POP_JUMP_IF_FALSE      succ=[128,172]
blk 128 n=2  L625  term=POP_JUMP_IF_NOT_NONE   succ=[132,146]
blk 172 n=11 L628  term=POP_JUMP_IF_FALSE      succ=[226,308]   ← 赋值 + FUTURE 测试同块
landed：BoolOpRegion@0 owns=[116,128,172]；IfRegion@0 cond=116 then=[132,146,170] else=[226,…]
        无 TernaryRegion@128、无 IfRegion@172（⇒ 172 的三条语句没有发射者）
```

站点＝`core/cfg/region_analyzer.py` `_create_boolop_region_from_chain`：
L24363-24364 `if is_condition_context and merge: region_blocks = chain_blocks` 已把块集收回为
纯操作数块，随后 L24396 起（`_BOOLOP_CHAIN_JUMPS` / `_all_ternary_cond_c`，L24415-24416）的
P5「三元值块扩展」又把跳转目标 128 与落空目标 172 加回去，末尾
`for b in region.blocks: self.block_to_region[b] = region`（条件上下文分支还是覆写式认领）
把它们从 IfRegion 的臂里摘走。既有守卫只查「落空块含 STORE」，从不查跳转目标块
（172 明明含 3 条 STORE），也没用「本链是条件上下文 ⇒ 两个出口都是语句级块」这一同层事实。
别名陷阱：收回处写作 `region_blocks = chain_blocks`（同一对象），故第一版探针的
`region_blocks - chain_blocks` 恒空打出 `extra=[]` —— 坏探针，改用 `sorted(start_offset)` 全量打印才拿到证据。

## Step 3 —— 实现（`specs/cand_r63b4_boolop_exit.json`）

`_all_ternary_cond_c = not (is_condition_context and merge is not None)`（原 `= True`）
+ 三要素中文注释（识别条件/归约方式/AST 映射）写在识别它的 `_create_boolop_region_from_chain` 内。
判据与紧邻的收回语句完全同一：不新增形状/偏移/名字谓词、无阈值、无跨层包含。

修复后同层结构（`logs/probe2_b4x.txt`，`CORE=mirr_b4x`）正是设计律形态：

```
BoolOpRegion@0 blocks=[0, 116]                            parent=[IfRegion@0]
TernaryRegion@128 blocks=[128,132,146,170]               parent=[IfRegion@0]
IfRegion@172  cond=172 merge=374 then=[226] else=[308]   parent=[IfRegion@0]
IfRegion@0    then=[128] else=[172,…]                    ← 父层只引用子区域入口
```

## 见证行 before → after

| 臂 | 靶文件 | get_kline_by_count | get_price |
|---|---|---|---|
| landed | 16/18 | 854/841 jd3 td807 | 550/544 jd4 td475 |
| **b4x（本候选）** | **17/18** | **消失（854/854 jd0 td0）** | 未动 |
| ts1（仅 tern_slot） | 17/18 | 未动（854/841） | 消失 |
| **b4c（两支合并）** | **18/18** | **消失** | **消失** |

## 证伪（逐条实测）

1. 前批「本行与三元让位判据正交」= 成立：`ts1` 单跑靶 17/18，本行元组纹丝不动。
2. 「按块内容判值块」= 证伪：`f3`（候选块含 STORE 即拒）把 `-13` 收到 `-2`，函数仍失配
   `854/852`，复现体两形状 `75/71`、`59/55`。被吞的 128 本就不含 STORE，缺的是结构事实。
3. 「blunt 关掉整个扩展」= 与本候选在本语料**逐字节等价**：`f2` 402 全量
   `b4x→f2 : REGRESSION=0 IMPROVED=0 MOVED=0 SAME=402` ⇒ P5 扩展在值上下文于本语料 inert。
   仍交付窄判据 b4x：只在本层已声明出口为语句级时不扩展，保留 P5 本职用途。
4. 复现体阴性对照：`cond_boolop_merge_return_terminated`（if 之后语句块以 RETURN_VALUE 结尾
   ⇒ 扩展判据不成立）与 `value_context_or_with_ternary`（值上下文 `x = A or (B if c else d)`）
   **两臂都匹配** ⇒ 触发者是「链成员出口块以条件跳转结尾」，不是三元形状也不是「if 后有语句」。
5. `_boolop_resolve_merge` 在本例给出的 `merge=374`（真出口应是 172）本候选不改（改它属另一判据，未测，留 R64）。

## 爆炸半径（同一清单由我跑 `--arm=landed` 对照）

| 清单 | landed | b4x | REGRESSION | IMPROVED | MOVED | 产物文本相同 |
|---|---|---|---|---|---|---|
| `targets.txt` 1 支 | 16 | 17 | 0 | 1 | 0 | 0/1（变的正是靶） |
| `diag4/targets.txt` 5 支 | 151 | 152 | **0** | 1 | **0** | 4/5 |
| `shapes_r62.txt` 6 支 | 10（clean 4） | 10（clean 4） | **0** | 0 | 0 | 6/6 |
| `test_repros/round63_fix2` | 11/13 | 13/13 | 0 | 1 | 0 | 0/1 |
| 全量 402 | 5675 / clean 381 | **5676 / clean 381** | **0** | 1 | **0** | **401/402** |
| 合并臂 b4c 全量 402 | 5675 / clean 381 | **5677 / clean 382** | **0** | 1（靶 16/18→18/18） | 2（与 diag4 批 c3 单跑同一对：`trade_live_broker` fund_transfer 123→106、market_fund_transfer 94→77 收敛；`flyAccount._do_request` 436→443 反向，该函数 landed 即已失配） | 399/402 |

即：本候选在 402 上只改动 1 份产物文本；与 tern_slot 合并不改变对方的 MOVED 集合。

## 交付物体检

* `specs/cand_r63b4_boolop_exit.json`：`{"file","edits":[{anchor,repl}]}`，锚文本 LF 归一，
  在 landed 字节（1 719 972 B / 无 BOM）中 `count==1`（`mk_cand_spec.py` 于 04:05 断言，
  `mbuild.py` 亦断言）。与 `cand_r63b4_tern_slot.json` 的锚在不同文件，合并构建两条锚各自唯一。
* `mirr_b4x`：`region_analyzer.py` 1 721 959 B、sha256 `c694d2514eb2f2b21ccf`、CRLF 27 590（=27 568+22）、
  裸 LF 0、无 BOM（原文件即无 BOM）、py_compile OK、ast.parse OK；该镜像的 `region_ast_generator.py`
  与 landed 逐字节相同（sha `b9778ee0130865d55888` / 3 059 418）。
* `mirr_b4c`：额外带 `region_ast_generator.py` 3 061 465 B / BOM 保留 / CRLF 49 485 / 裸 LF 0 /
  py_compile+ast OK（sha `c54b2d972170084aa55e`）。
* 复现：`F:/Downloads/pythoncdc-main/test_repros/round63_fix2/r63b4_cond_boolop_stmt_steal.py` + 同名
  `.pyc`（magic 3495 / cpython-311，与前批 `round63_b4` 复现同规格）；landed 11/13 → b4x/b4c 13/13。
* 工具/日志：`probe2.py`（`CORE=` 可切臂）、`mk_diag_spec.py`、`mk_cand_spec.py`、`mk_fals_specs.py`、
  `logs/{align_landed_kline,align_b4x_kline,probe2_kline,probe2_b4x,booldiag}.txt`、
  `dump/{landed,b4x,b4c,ts1,f2,f3}{,_diag4,_shapes,_repro,_402}.jsonl`。

## 测量完整性（重要）

仓库工作树的 `core/` 在 **04:20:39** 被外部（集中验证方/兄弟批次）改写：
`region_analyzer.py` 变为 1 721 959 B / `c694d2514eb2f2b21ccf`（与本候选镜像逐字节相同 ⇒ 本候选已被落地），
`region_ast_generator.py` 变为 3 086 600 B / `7ec41fa2f9cdd5d62c1a`（既非 landed 的 3 059 418/`b9778ee0…`，
也非 tern_slot 的 3 061 465/`c54b2d97…`）。本子代理全程未写 `core/`、未跑任何改状态的 git 命令。
我全部 `--arm=landed` 进程（targets/diag4/shapes/repro/402 两轮）都在 04:18:52 之前结束，
导入的是落地前 R62 字节；完整性自检：landed 侧复现出文档基线
`16/18 + [854 841 3 807]/[550 544 4 475]`、diag4 151、shapes 10、402 matched 5675 / clean 381，逐项吻合。
此后 `--arm=landed` 不再代表 R62 落地态，主循环复测请以此为准。
