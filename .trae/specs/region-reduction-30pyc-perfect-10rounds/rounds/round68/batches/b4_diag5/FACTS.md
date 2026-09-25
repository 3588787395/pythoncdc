# FACTS · Round 68 · diag5（只读诊断代理）

工作区 `D:/Temp/opencode/r68gate/diag5`；仓库 `F:/Downloads/pythoncdc-main` 只读。
边跑边写。

## Step 0 · baseline replay   （landed 复放 vs brief 预读数）

实测（`h62.py run --arm=landed`，dump/landed.jsonl）：

| 靶支 | matched/total | 缺陷函数 (name, orig, decomp, jumpdiffs, truediffs) |
|---|---|---|
| real_quote.pyc | **40/44** | get_cache_l2_data_by_one 321/322 jd=2 td=197 ；get_real_minute_kline 253/254 jd=3 td=197 ；get_tick_direction 259/258 jd=3 td=102 ；one_prod_to_ndarray 605/607 jd=5 td=424 |
| wizard_quant_api.pyc | **52/53** | params_analysis 133/126 jd=1 td=117 |
| api_base.pyc | **24/25** | get_history_df 1742/1740 jd=14 td=1263 |

=> 与 targets.md / BRIEF §8 预读数**逐字段相同**，无更正。

金丝雀（dump/landed_canary.jsonl）sha：`4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177`
—— 与 BRIEF §3-1 逐字节相同，143/143、10/10、26/26、25/25 全 matched。

45 项电池 landed（closeout67.py battery landed，dump/repro65_landed.jsonl）：
**174/200 matched、缺陷函数 26、Σ|Δ| 101、worse-than-landed=0、ERR=0** —— 与 BRIEF §4 基线**逐字段相同**。

Step 0 结论：环境/落地字节与 brief 一致，可作为 A/B 对照列。

## Step 1 · hunk tables（nested_diff，按 code-object 全路径配对；未归一 NOP/EXTENDED_ARG ⇒ 自行分类）

### real_quote.pyc（`/RealQuoteData#23` 命名空间下）
| code object | orig/decomp | 归一化 hunk | 真缺陷 or 伪影 |
|---|---|---|---|
| /RealQuoteData#23 | 131/123 | 4× delete NOP | **伪影**（NOP 计数，official/strict 均不计） |
| /RealQuoteData#23/get_bar#24 | 267/266 | 1× delete NOP | **伪影** |
| …/get_cache_l2_data_by_one#34 | 355/356 | 1× insert `JUMP_BACKWARD` | 真：多 1 条跳转（official 321/322） |
| …/get_real_minute_kline#21 | 280/287 | 4× insert EXTENDED_ARG + `orig[65:100]` 整段 35 指令 delete → `decomp[221:259]` insert | 真：**整段位移**（EXTENDED_ARG 为伪影） |
| …/get_tick_direction#39 | 297/299 | 1× insert EXTENDED_ARG + `orig[172:202]` 30 指令 → `decomp[268:299]` | 真：**整段位移** |
| …/one_prod_to_ndarray#11 | 659/665 | 7 hunk：`orig[389:423]` 34 指令 → `decomp[201:237]`；4× `JUMP_FORWARD`→`EXTENDED_ARG+JUMP_BACKWARD` | 真：**整段位移**（含回边化） |

⇒ 复核 R67-diag5 结论成立：real_quote 三支是**纯位移/线性化顺序**族，无语句增删（除 get_cache_l2 多 1 条 JUMP_BACKWARD）。

### wizard_quant_api.pyc
| code object | orig/decomp | hunk | 分类 |
|---|---|---|---|
| `<root>` | 222/217 | 5× delete NOP | 伪影 |
| /filter_desicion#10 | 195/197 | 尾部 insert `LOAD_CONST None;RETURN_VALUE` | **真**（strict 179/181）：产物多一条末尾 return None |
| /params_analysis#11 | 144/137 | 2× `JUMP_FORWARD`→`LOAD_CONST None;RETURN_VALUE`；`orig[20:29]` 9 指令 delete | **真**：try-except 之后的 `return {…float(value_params)}` 整条语句丢失 |
| /get_DMI#31/calculate_di#1/`<genexpr>`#3、#4 | 64/50 ×2 | 各 delete 14 指令 | 真缺陷但**两把尺都看不见**（`_load_map` 用 `setdefault` 以 `parent.name.<genexpr>` 为键，同名嵌套只留第一个）⇒ 修它不得分 |
| /init_stock_pool_filter#33 | 175/175 | delete NOP + insert EXTENDED_ARG | 伪影（strict 报 target_diff #33 JUMP 终点） |
| /ST_stock_filter#34 /HALT_stock_filter#35 /read_config_file#51 | — | delete NOP | 伪影 |

### api_base.pyc
| code object | orig/decomp | hunk | 分类 |
|---|---|---|---|
| /get_history_df#26 | 1900/1898 | ①②`POP_JUMP_IF_TRUE`+4 指令组 ↔ `POP_JUMP_IF_FALSE`（极性翻转+位移）③④两处 insert（各 4）⑤**delete `orig[584:586]=[LOAD_FAST include, POP_JUMP_FORWARD_IF_TRUE]`** | ①-④ 是同内容**位移**；⑤ 是**真缺陷**＝净 -2 的唯一来源 |
| 其余 27 个 code object | 全等 | — | — |

### 判定：本批唯一「一处修多得」的高价值真缺陷
`wizard::params_analysis` 丢语句（official gap 1 + strict 1）＝**唯一**能让某支文件官方口径直接满匹配（52/53→53/53）的缺陷。

## Step 2 · 根因（实测，全部为我自己进程内探针读数，未改仓库）

### 2.1 wizard::params_analysis —— 已定位到解析器单行，实测证据链完整

探针：`aprobe.py`（包装 `RegionAnalyzer._collect_branch_blocks`，打印 arm/merge/stop/返回）
```
CBB arm=10 args=[None, {blk@86}]                 -> [10, 12, 28, 48]     # 第一次收集（merge=None）
CBB arm=10 args=[12, ]  kwargs={'stop_set':[86]} -> [10]                 # 第二次：merge 被算成 12 ⇒ 臂被截断
区域终态：IfRegion@0 then=[10] merge=12 exit=12   # merge=12 就是 try 体入口块自己
```
`trace_r68.py` 证据（发射侧）：
```
TRACE _if_generate_then_branch(IfRegion@0)
  TRACE _process_if_blocks(blocks=[blk@10], IfRegion@0)   # ⇒ 臂里根本没有 blk@48
  RETN -> []
RETN -> [Try]                                             # try 由子区域循环补发，blk@48 的 return 永久丢失
```
（对照：branch 2 走 `_if_generate_elif_chain`→`_process_if_blocks([98,100,116,136])`，臂块表完整，
`_generate_block_statements(blk@136) -> [Assign, Return]` 正常发射。⇒ 同一 merge=100 误算对 elif 臂无伤，
只有 then 臂（用 `region.then_blocks`）受害。）

**根因行**：`core/cfg/region_analyzer.py` **L19688**
```python
_then_exit_succs = set(then_blocks[0].successors)      # ← 取臂【首块】的后继
...
for _body in elif_info["bodies"]:
    _all_branch_exits.append(set(_body[-1].successors))  # ← elif 臂取【末块】的后继
```
两侧不对称。当 then 臂含嵌套区域（本例 try/except）时 `then_blocks` 有 4 个块
[10,12,28,48]，`then_blocks[0].successors={12}` 是**臂的内部边**，不是臂出口；
而所有 elif 臂与 final_else 都以 RETURN_VALUE 终结 ⇒ 后继为空 ⇒
`_non_empty_exits=[{12}]` ⇒ 命中 L19702-19703 `elif len(_non_empty_exits)==1:
_chain_merge_candidates = set(_non_empty_exits[0])` ⇒ `merge := 12`（臂自身内部块！）
⇒ L19830 `then_blocks = _collect_branch_blocks(then_blocks[0], 12, {86})` 返回 `[10]`
⇒ 臂体只剩一个 NOP 块，`return {...float(value_params)}`（blk@48，9 条指令）从 AST 消失。

### 2.2 real_quote —— R67-diag5 的「纯位移族」结论复核成立，未找到同层判据
`get_real_minute_kline`/`get_tick_direction`/`one_prod_to_ndarray`：整段 30-35 指令被搬到函数尾，
零语句增删；`get_cache_l2_data_by_one` 多 1 条 JUMP_BACKWARD。**不是**三元/BoolOp/链式比较家族
（`_build_ternary_boolop_condition`/`_r67_split_cc_ternary_stmt_prefix`/`_r67_boolop_chain_end`
三支 R67 站点与本批形状无交集，实测 nested_diff hunk 里没有任何 boolop/cc 形状）。

### 2.3 api_base::get_history_df —— 净 -2 的唯一来源是 `orig[584:586]=[LOAD_FAST include, POP_JUMP_FORWARD_IF_TRUE]`
（若 `include:` 的测试被整体吞掉），另 4 个 hunk 是同内容位移 + 极性翻转。尚未做发射侧实测。

## Step 3 · 合成复现（`synth/r68d5_trymerge.py` → `.pyc`，名单 `synth/r68d5_trymerge.txt`）

landed 读数：`1/2`，`[['params_analysis', 89, 82, 2, 72]]` —— 与真靶支 `params_analysis 133/126`
**同一签名（净缺 7 条、两处 JUMP_FORWARD 退化成 LOAD_CONST None/RETURN_VALUE）**。
产物文本失败签名（`build_landed/D___Temp__opencode__r68gate__diag5__synth__r68d5_trymergeOK.py`）：
第一臂只剩 try/except，其后的 `return {…'ob_value': float(value_params)}` 整条语句消失；
第二臂（elif，走 `_if_generate_elif_chain`）完整 ⇒ 复现的正是「只有 then 臂受害」这一不对称。

## Step 4 · 候选与 A/B

### 4.1 被证伪的第一版（阴性证据）
`specs/cand_r68_thenarmexit.json`（臂 `r68diag5a`）：把 then 臂出口改成「臂内**末块**（后继全部
离开本臂的块）的后继并」。它确实修好 wizard（52/53→53/53）与合成（1/2→2/2），canary 不变、
电池 worse=0，**但在 all15 上打出一个真回归**：
`trade_live_broker::option_covered_trans` landed 匹配 → 臂 297/297 jd=3 td=25（`REGRESSION 108/119→107/119`）。
`aprobe2.py` diff 出机理：该臂 `then_blocks=[1170,1182,1298,1412]` 是**过度收集**的臂，
旧式 `then_blocks[0].successors={1182,1298}` 参与交集后把候选清空 ⇒ merge=None（正确）；
新式给出 ∅ ⇒ `_non_empty_exits` 从 2 降到 1 ⇒ 命中 `len(_non_empty_exits)==1` 捷径
⇒ `merge:=1582`（别臂的出口被认成链汇合块）⇒ 臂被错误截断。**⇒ 该路线作废。**

### 4.2 交出的候选 `specs/cand_r68_thenfallthrough.json`（臂 `r68diag5b`）
锚点 `core/cfg/region_analyzer.py` L19688 `            _then_exit_succs = set(then_blocks[0].successors)`
（在当前落地字节 `count==1`，实测 `h62.py build` 通过：1 edit，CRLF，无 BOM）。
判据（三要素已写进注释文本）：
- **识别条件**：只读本臂入口块自身的末条指令与它的后继集——末条指令显式转移控制
  （`JUMP* / POP_JUMP* / BRANCH* / RETURN_VALUE / RETURN_CONST / RAISE_VARARGS / RERAISE`）
  时其后继才是臂出口；否则臂出口集为 ∅（控制流仍在本臂内直落）。
- **归约方式**：以该臂出口集参与 `_chain_merge_candidates` 的交集/唯一后继判定；候选为空则
  merge 保持 None，**不再**以「merge=臂内部块」重收 then 臂，臂体保留首次
  `_collect_branch_blocks` 的完整块表。
- **AST 映射**：`If.body = [Try, …, Return]` 完整语句序列，与 elif 臂经 `_process_if_blocks`
  的发射形态一致；不引入新节点类型。
wizard 的臂入口块 10 末条是 NOP（它单独成块只因 try 体异常表边界在此切块）⇒ 直落 ⇒ 出口集 ∅
⇒ merge 不再被误设为 12 ⇒ 臂不被截断 ⇒ 9 指令的 `return` 回来了。
`trade_live_broker` 的臂入口块 1170 末条是条件跳转 ⇒ 判据不改变其取值 ⇒ 交集仍为空 ⇒ merge 仍 None。

### 4.3 五列读数（landed → r68diag5b）
| 门 | landed | r68diag5b | 判定 |
|---|---|---|---|
| targets 官方 | 116/122 matched，缺陷函数 6，Σ\|Δ\|=14 | **117/122，缺陷 5，Σ\|Δ\|=7** | 严格变好，Σ\|Δ\| 净 -7 |
| targets 严格尺 | 120/128 ok，defects 8 | **121/128 ok，defects 7**（params_analysis 从缺陷表消失） | 变好 |
| battery 45 项 | 174/200，defects 26，Σ\|Δ\|=101，worse=0 | **逐行完全相同**，worse-than-landed=0 | 不劣于（完全 inert） |
| canary 4 支 | `4d41187e356544e0/af77224b34b203c4/e711b8ea86d49a15/9d09af09249da177` | **逐字节相同** | 通过 |
| synth 见证 | 1/2，Σ\|Δ\|=7 | **2/2，Σ\|Δ\|=0** | 咬合 |
| ERR / 不可反编译 | 0 | 0 | 通过 |

附加外溢证据（不是 402 全量，是抽样）：
- `all15.txt`（15 支 partial，= BRIEF §4 基线 572/617、缺陷 45、Σ\|Δ\|=296）→
  **573/617、缺陷 44、Σ\|Δ\|=290、REGRESSION=0、MOVED=3、ERR=0**；`h62.py ab` TALLY 实证。
  MOVED 明细：`fileio_utils::write` 由 `637/637 jd=4 td=519` 变 `637/636 jd=0 td=38`
  （形状大幅靠近正确、true_diffs 519→38，代价是长度多缺 1 条）；`trade_info_utils`、`quote` 仅产物文本变动、缺陷集不变。
- `sample60.txt`（从 387 支 ok 文件随机抽 60 支，seed=6805）→ **SAME=60 / IMPROVED=0 / REGRESSION=0 / ERR=0**，
  即 60 支已通过文件的产物 sha 逐字节不变。

## Step 4-复测 · R68-batch4 会话在【当前落地字节】上重放 specs/cand_r68_thenfallthrough.json

复测时间 2026-09-25（本轮会话）。前提核对：
- core/ 三支白名单文件 mtime 均为 13:59:23（Round 67 落地字节），晚于它的只有本工作区产物
  ⇒ Step 0 的 landed 基线 dump（14:41/15:08）仍然代表当前落地字节，A/B 有效。
- git status 无 core/* 修改（只读核对，未执行任何 git 写命令）。

### 4.4 自测步骤（臂名 
68b4_thenfall，新 out 文件名避开 resume）
1. python -X utf8 h62.py build --spec=specs/cand_r68_thenfallthrough.json --dst=r68b4_thenfall
   ⇒ **通过**：mirrors built: head pristine == worktree bytes, cand patched (1 edits, core/cfg/region_analyzer.py, BOM=False, nl=CRLF)
   内部断言 nchor count==1 成立、head 镜像与落地字节逐字节相同；候选 AST 解析 OK（27902 行）。
2. targets（dump/b4_targets.jsonl）/ canary（dump/b4_canary.jsonl）/ 合成（dump/b4_syn.jsonl）/
   电池（dump/repro65_r68b4_thenfall.jsonl）/ 严格尺（dump/strict_b4_land.json vs strict_b4_arm.json）。

### 4.5 五列实测读数（landed → r68b4_thenfall，本轮实跑）
| 门 | landed | r68b4_thenfall | 判定 |
|---|---|---|---|
| targets 官方 | 116/122 matched，缺陷 6，Σ\|Δ\|=14 | **117/122，缺陷 5，Σ\|Δ\|=7**（h62.py ab：SAME=2 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0） | 严格变好，Σ\|Δ\| 净 -7 |
| wizard_quant_api | 52/53（params_analysis 133/126 jd=1 td=117） | **53/53，mism=[]（头号目标达成）** | 变好 |
| targets 严格尺 | 120/128 ok，defects 8 | **121/128 ok，defects 7**（params_analysis 从缺陷表消失：wizard 53/56→54/56） | 变好 |
| real_quote / api_base | 40/44 ；24/25 | **40/44 ；24/25（逐字节 sha 相同，未被触碰）** | 中性 |
| battery 45 项 | 174/200，defects 26，Σ\|Δ\|=101，worse=0 | **174/200，Σ\|Δ\|=101，b SAME=45 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0**，worse-than-landed on 0 repro(s) | 不劣于（完全 inert） |
| canary 4 支 sha | 4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177 | **四支逐字节相同**（143/143、10/10、26/26、25/25） | 通过 |
| synth 见证 | r68d5_trymerge 1/2（Σ\|Δ\|=7） | **2/2，mism=[]**（b：IMPROVED） | 咬合 |
| ERR / 不可反编译 | 0 | 0 | 通过 |

⇒ **上一会话的全部读数在当前字节上原样复现，候选 cand_r68_thenfallthrough 仍成立。**

## Step 5 · api_base 根因定案 + 第二条候选（IfRegion.contains_block）

### 5.1 根因（用 sys.settrace 实测，不是读码推断）
工具：`logs/trace2686.py <pyc> <func> <offsets> "<fnfilter>"`（只 trace `core/cfg/region_analyzer.py`
的帧，按局部变量 `block.start_offset` 过滤，打印 co_name/lineno/block_region 与该行源码）。

`IQData/api/api_base.pyc :: get_history_df` 块 2686（`LOAD_FAST am_close / STORE_FAST tmp /
LOAD_FAST include / POP_JUMP_FORWARD_IF_TRUE`，即 `if not include:` 守卫）的实测路径：

```
_identify_conditional_regions L16038  block_region = self.block_to_region.get(block)
_identify_conditional_regions L16048  br=IfRegion@2654      -> _should_skip_block_for_if_region
_should_skip...               L15412  if not loop_regions:   (假，函数里有循环)
_should_skip...               L15633  elif block_region is not None:
_should_skip...               L15634  if not block_region.contains_block(block):   <- 真
_should_skip...               L15650  if (isinstance(block_region, BoolOpRegion) ..) <- 假
_should_skip...               L15702  return True
_identify_conditional_regions L16049  continue                <- 内层 IfRegion 不建
```

对照组：`synth/r68b4_apib_inc4.py` 的同形块 50 在 `_should_skip...` **L15413 `return False`** 直接放行，
因为它的函数里没有任何循环 => `if not loop_regions: return False` 提前返回，深分支走不到。

**根因**：`IfRegion` 从未覆写 `contains_block`，继承 `Region` 基类的恒 `False` 实现
（全仓 `def contains_block` 只有 4 处：Region:292 恒 False / TryExcept:790 / With:923 恒 True /
BoolOp:1055 仅 entry）。于是「块已登记到某个 IfRegion」被读成「块不属于它的区域」=>
`_should_skip_block_for_if_region` 无条件 `return True`。这条分支只在 `loop_regions` 非空时可达
=> **同一结构在无循环函数里放行、在含任意循环的函数里被否**，判据不在结构同一层。
比较链 IfRegion 的 then 臂入口块在 `_build_chained_compare_region` 里被一并登记进 `block_to_region`，
它自己同时又是一个嵌套 if 的条件块，于是内层 `if not include:` 被整体跳过、`IfRegion@2686` 不建，
守卫的 2 条指令（`LOAD_FAST include / POP_JUMP_FORWARD_IF_TRUE`）从 AST 消失、`min_count -= 1` 被提到外层。

旁证：全仓 `.contains_block(` 只有 1 个调用点（`region_analyzer.py:15634`）=> 覆写只影响这一处。

### 5.2 合成见证（没咬合不许交 spec）
- `synth/r68b4_apib_inc7.py` = inc4 **加一个与结构无关的 for 循环**（只为让 `loop_regions` 非空）。
  landed：`1/2  [55/53 jd=3 td=25]`；候选臂：`2/2 []`。
- 同族对照 inc1/inc2/inc3/inc4/inc5：landed 与候选臂均 `2/2`；inc6 landed `1/2 (41/41 jd=5 td=10)`、
  候选臂 `1/2 (41/41 jd=5 td=10)`（不修也不劣化）。
- inc7 区域树 landed：`IfRegion@58 blocks=[58,74,86,90] then=[90] children=['Region@84']`（缺 IfRegion@90）；
  候选臂出现 `IfRegion@90`。inc4（无循环）landed 即有 `IfRegion@50`。

### 5.3 候选 spec
- `D:/Temp/opencode/r68gate/diag5/specs/cand_r68_ifregion_contains.json`
  （file `core/cfg/region_analyzer.py`，anchor 为 `IfRegion.is_block_entry` 两行，落地字节 count==1，
  新增 28 行：为 IfRegion 补 `contains_block`，实现 `return block in (self.blocks or set())`，
  注释含识别条件 / 归约方式 / AST 映射三要素）
- 合并 spec（两条候选一起交）：`D:/Temp/opencode/r68gate/diag5/specs/cand_r68_wizapib.json`
  （`edits` = [cand_r68_thenfallthrough, cand_r68_ifregion_contains]）

### 5.4 五列读数（landed -> r68b4_both 本轮实跑；臂 r68b4_ifcont 也单独跑过，结论一致）

| 门 | landed | r68b4_ifcont（仅第二条） | r68b4_both（两条合并） | 判定 |
|---|---|---|---|---|
| targets 官方 | 116/122 matched，缺陷 6，SUM_DELTA=14 | 116/122，缺陷 6，SUM_DELTA=12 | **117/122，缺陷 5，SUM_DELTA=5** | 变好 |
| h62.py ab（对 landed targets） | — | SAME=2 REG=0 MOVED=1 ERR=0 | **SAME=1 IMPROVED=1 REG=0 MOVED=1 ERR=0**，files fully matched 0->**1** | 通过 |
| wizard_quant_api | 52/53（params_analysis 133/126） | 52/53（未触碰） | **53/53 mism=[]** | **头号指标达成** |
| api_base get_history_df（官方） | 1742/1740，jd=14，**td=1263** | **1742/1742，jd=11，td=89** | 同左 | COUNT 转正、td 净 -1174 |
| api_base（nested_diff） | orig=1900 **decomp=1898**，hunks=**5**（含 `delete orig[584:586]=LOAD_FAST include / POP_JUMP_FORWARD_IF_TRUE`） | — | orig=1900 **decomp=1900**，hunks=**4**（守卫 hunk 消失，净差 0） | 变好 |
| real_quote | 40/44（6 个 code object 差异） | 40/44 | **40/44，逐字节同 landed** | 中性 |
| targets 严格尺 | 120/128 ok，defects 8 | 120/128，defects 8（api_base 由 seq_len 转 seq_diff #419） | **121/128 ok，defects 7**（wizard 53/56->54/56） | 变好 |
| battery 45 项 | 174/200，SUM_DELTA=101 | ab SAME=45 REG=0 ERR=0，worse-than-landed on 0 | **SAME=45 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0**，files fully matched 30->30，worse=0 | 不劣于 |
| canary 4 支 sha | 4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177 | 四支逐字节相同 | **四支逐字节相同**（143/143、10/10、26/26、25/25） | 通过 |
| synth 8 件 | 5/7 全匹配（trymerge 1/2、inc6 1/2、inc7 1/2） | inc7 -> 2/2 | **7/7 全匹配**（SAME=6 IMPROVED=2 REG=0 ERR=0，IMPROVED = trymerge + inc7） | 咬合 |
| ERR / 不可反编译 | 0 | 0 | 0 | 通过 |

产物与读数文件：`dump/b4t_land2.jsonl`、`dump/b4t_ifcont.jsonl`、`dump/b4t_both.jsonl`、
`dump/b4c_ifcont.jsonl`、`dump/b4c_both.jsonl`、`dump/strict_b4c_land.json`、`dump/strict_b4c_both.json`、
`dump/repro65_r68b4_ifcont.jsonl`、`dump/repro65_r68b4_both.jsonl`、`dump/syn8_land2.jsonl`、
`dump/syn8_both2.jsonl`。`closeout67.py landproof mirr_head` => 33 core files, same=33 diff=0。
`git status --porcelain` 无任何 `M`（core/、pyc_index.json、已跟踪文件均未改动）。

### 5.5 未竟（api_base 仍 24/25 的剩余根因，留给下一轮）
`nested_diff` 剩 4 个 hunk，全是同一件事的两处（`time_count -= 1` 与 `max_len_real_data -= 1`）：
`orig[457] = POP_JUMP_FORWARD_IF_TRUE + 5 条 -=`，`decomp[457] = POP_JUMP_FORWARD_IF_FALSE`，
`-=` 被搬到 decomp[548]/decomp[526]（晚 95 条）。区域侧 `IfRegion@2144 then=[2202,…,2244] merge=2254`
把 2244（`-=`）当作外层 then 臂里的兄弟语句，而原字节码语义是 `if outer and not (A or B): -=`
（外层各跳转与链尾 IF_TRUE 全部 -> 2254，只在链为假时才落到 2244）。
即 **or 链的否定没有被认成「外层条件的一部分」**，属另一族（否定/BoolOp 条件归并），与 5.1 不同源。

### 5.6 real_quote VERDICT 依据
`nested_diff` 6 个差异 code object 全是位移/噪声族：`RealQuoteData` 4x`delete NOP x2`、`get_bar` 1x`delete NOP`、
`get_cache_l2_data_by_one` 1x`insert JUMP_BACKWARD`、`get_real_minute_kline` 6x`EXTENDED_ARG` +
一段 `EMPTY_DAY_BAR_NP_ARRAY` 块整体后移、`one_prod_to_ndarray`/`get_tick_direction` 同形整块位移。
ADR-1 要求位移族成对落地且归一 hunk 数严格下降 + first_diff 回移 + SUM_DELTA 不上升 + 无新增 target_diff；
本轮没有为它做出任何判据候选 => **候选：NONE**。

## Step 6 · 三靶 VERDICT 汇总（R68-batch4 / diag5）

| 靶 | VERDICT | spec 绝对路径 | landed -> 候选 |
|---|---|---|---|
| IQCommon/strategy/wizard_quant_api.pyc :: params_analysis | **候选：成立，100% 完全 OK** | `D:/Temp/opencode/r68gate/diag5/specs/cand_r68_thenfallthrough.json` | 官方 52/53 -> **53/53 mism=[]**；严格尺 wizard 53/56 -> **54/56**（params_analysis seq_len 134/128 从缺陷表消失） |
| IQData/api/api_base.pyc :: get_history_df | **候选：成立（缺失型，Σ\|Δ\| 净减少），未到 100%** | `D:/Temp/opencode/r68gate/diag5/specs/cand_r68_ifregion_contains.json` | 1742/1740 jd=14 td=1263 -> **1742/1742 jd=11 td=89**；nested_diff 1898/1900 hunks=5 -> **1900/1900 hunks=4**；剩余 4 hunk 根因见 5.5 |
| IQData/plugins/plugin_system_realquote/real_quote.pyc | **候选：NONE** | 无 | 40/44 未变；6 处差异全为位移/噪声族，ADR-1 位移族要求成对落地，本轮未产出判据 |

**合并交出的 spec（推荐）**：`D:/Temp/opencode/r68gate/diag5/specs/cand_r68_wizapib.json`
（两条 edit 合并，一次 build 通过全部门：targets 117/122、wizard 53/53、api_base 1742/1742、
strict 121/128 defects=7、battery SAME=45 worse=0、canary 4/4 sha 相同、synth 7/7 全匹配、ERR=0）。

**中心最该先验的一条**：`IfRegion` 缺 `contains_block` 覆写是「含循环的函数才会触发」的条件性缺陷，
建议中心先在自己的样本池里统计「`loop_regions` 非空且 `block_to_region` 值为 IfRegion 的条件块」有多少，
再决定是否连带把 `LoopRegion`/`TernaryRegion`/`MatchRegion` 等同样未覆写 `contains_block` 的子类一并补齐
（本轮只按证据补了 IfRegion，因为只有它有合成见证）。
