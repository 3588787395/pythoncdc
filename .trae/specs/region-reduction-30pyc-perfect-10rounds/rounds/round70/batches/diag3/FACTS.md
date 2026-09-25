# Round 70 · diag3 · FACTS

臂名前缀 `r70diag3`。工作区 `D:/Temp/opencode/r70gate/diag3`；仓库只读。
仪器：本目录 `h62.py`（ROOT=`D:/Temp/opencode/r70gate/center`）、`sstrict67.py`、
`mybat.py`（diag3 私有电池 runner，避免与并行代理抢 `center/dump/repro65_*.jsonl`）。

## Step 0 · baseline replay

`python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl`

| pyc | 官方 matched | mism（官方尺 orig→decomp / jumpdiff / truediff） |
|---|---|---|
| `IQCommon/api/klinedata.pyc` | **43/45** ✓ | `get_multiminute_his_data` 479→478 (j3,t16)、`kline_datetime_list` 389→389 (j9,t228) |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | **40/44** ✓ | `get_cache_l2_data_by_one` 321→322 (j2,t197)、`get_real_minute_kline` 253→254 (j3,t197)、`get_tick_direction` 259→258 (j3,t102)、`one_prod_to_ndarray` 605→607 (j5,t424) |
| `IQCommon/util/trade_info_utils.pyc` | **39/40** ✓ | `trade_operation` 304→302 (j2,t40) |

`h62.py run --arm=landed --list=canary.txt --out=dump/landed_canary.jsonl`

| canary | matched | sha |
|---|---|---|
| `fly/data/quotation.pyc` | 143/143 ✓ | `4d41187e356544e0` |
| `fly/common/market_time.pyc` | 10/10 ✓ | `af77224b34b203c4` |
| `IQCommon/util/datetime_func.pyc` | 26/26 ✓ | `e711b8ea86d49a15` |
| `IQData/utils/datetime_func.pyc` | 25/25 ✓ | `9d09af09249da177` |

（sha 见 `dump/landed_canary.jsonl`，逐一等于合同给定值。）

45 项电池（`mybat.py landed 45`，round63..67）：**182/200、bad=18、err=0、worse=0** ✓ 与 targets.md 完全一致。
82 项扩展电池（`mybat.py landed`，round63..69）：**318/356、bad=37、err=0、worse=0** ✓ 与 targets.md 完全一致。

严格尺（`sstrict67.py build_landed targets.txt`）：**136/149、缺陷 13、missing=0 extra=0**

| pyc | 严格 matched | 缺陷明细 |
|---|---|---|
| klinedata | **58/63** ✓ | `get_history_common` [target_diff] #41 POP_JUMP_IF_NONE orig=('is_dict',LOAD_FAST) decomp=('fields',LOAD_FAST)；`get_kline_by_count_new` [target_diff] #161 同型 orig=('0',LOAD_CONST) decomp=('symbols',LOAD_FAST)；`get_multiminute_his_data` [seq_len] 481→482；`get_price_common` [target_diff] #114 orig=('frequency',…) decomp=('is_dict',…)；`kline_datetime_list` [seq_diff] #151 POP_JUMP_IF_TRUE→POP_JUMP_IF_FALSE |
| real_quote | **41/45** ✓ | `get_cache_l2_data_by_one` [seq_len] 321→322；`get_real_minute_kline` [seq_len] 253→256；`get_tick_direction` [seq_len] 259→260；`one_prod_to_ndarray` [seq_len] 606→608 |
| trade_info_utils | **37/41** ✓ | `get_trade_status` [target_diff] #70 FOR_ITER orig=('return_trade_info',…) decomp=('count',…)；`get_trade_unit_info` [seq_len] 240→241；`set_trade_status` [target_diff] #113 JUMP orig=('count',…) decomp=('exchange_flag',…)；`trade_operation` [seq_len] 304→302 |

**与 targets.md 逐字段比对：全部相同，无更正。**
唯一观察：官方尺与严格尺对同一函数的条数口径不同（官方 `get_multiminute_his_data` 479→478 / 严格 481→482；
官方 `get_real_minute_kline` 253→254 / 严格 253→256；官方 `one_prod_to_ndarray` 605→607 / 严格 606→608；
官方 `trade_operation` 304→302 = 严格 304→302）。targets.md 的表用的是严格尺，故一致。

## Step 1 · hunk tables（`nested_diff.py`，按 code-object 全路径配对；NOP/EXTENDED_ARG 归为伪影）

### IQCommon/util/trade_info_utils.pyc（41 code objects，4 处有差异）
| code object | orig/decomp | 归一化 hunk | 判定 |
|---|---|---|---|
| `<root>` | 396/390 | delete×2 组 `NOP NOP NOP` | **伪影**（NOP），官方尺算 matched |
| `/trade_operation#32` | 339/337 | delete `['LOAD_CONST None','RETURN_VALUE']` @296 | **真缺陷**：官方/严格唯一 mismatch，缺 2 条指令 |
| `/get_trade_unit_info#44` | 273/274 | replace `EXTENDED_ARG+JUMP_BACKWARD`→`JUMP_FORWARD`；insert 同型 @271 | 伪影/位移，官方尺 matched |
| `/set_trade_status#67` | 180/179 | delete `NOP` @109 | **伪影**（NOP） |
（`get_trade_status` 官方 matched，仅严格尺 `target_diff`。）

### IQCommon/api/klinedata.pyc（64 code objects，4 处有差异）
| code object | orig/decomp | 归一化 hunk | 判定 |
|---|---|---|---|
| `<root>` | 545/541 | delete `NOP NOP` ×2 | 伪影 |
| `/get_multiminute_his_data#54` | 535/536 | replace `JUMP_FORWARD`→`LOAD_FAST his_data_dict+RETURN_VALUE` @518；replace `LOAD_FAST his_data_dict`→`LOAD_CONST None` @533 | **真缺陷**：`return his_data_dict` 位置前移 + 尾部变 `return None`，净 +1 |
| `/kline_datetime_list#57` | 413/417 | 7 hunks：3 处 decomp 多 `EXTENDED_ARG`；`POP_JUMP_IF_TRUE`→`POP_JUMP_IF_FALSE` 极性反 + `time_count-=1` 位置移动 | **已知死胡同**（R69 diag3 判 NONE），跳过 |
| `/get_price_common#67` | 594/596 | insert `NOP`；insert `EXTENDED_ARG` | 伪影 |
（`get_history_common`、`get_kline_by_count_new` 严格 `target_diff` 但官方/嵌套尺都算 matched——jump 终点被归一。）

### IQData/plugins/plugin_system_realquote/real_quote.pyc（45 code objects，6 处有差异）
| code object | orig/decomp | 归一化 hunk | 判定 |
|---|---|---|---|
| `/RealQuoteData#23`（类体） | 131/123 | delete `NOP NOP` ×4 | 伪影 |
| `.../one_prod_to_ndarray#11` | 659/665 | 7 hunks：`data_dict['datetime'].append(temp_time)` 与 `int(temp_time[11:13])` 两段整体**前移**；4 处 `JUMP_FORWARD`↔`JUMP_BACKWARD` | **真缺陷**（块顺序位移），净 +6 |
| `.../get_real_minute_kline#21` | 280/287 | `EMPTY_DAY_BAR_NP_ARRAY+return` 块从 orig@65 **后移到** decomp@221；3 处 `EXTENDED_ARG` | **真缺陷**，净 +7 |
| `.../get_bar#24` | 267/266 | delete `NOP` | 伪影 |
| `.../get_cache_l2_data_by_one#34` | 355/356 | insert `JUMP_BACKWARD` @134 | **真缺陷**，净 +1 |
| `.../get_tick_direction#39` | 297/299 | `if flag==1: system_log.debug(...)` 块从 orig@172 **后移到** decomp@268；2 处 `EXTENDED_ARG` | **真缺陷**，净 +2 |

结论：`trade_info_utils` 官方 gap=1 = 仅 `trade_operation`；`klinedata` 官方 gap=2 = `get_multiminute_his_data` + `kline_datetime_list`（后者死胡同 ⇒ 上限 44/45）；`real_quote` 官方 gap=4 全为块顺序/条数差。

## Step 2 · 根因（进行中）· trade_info_utils `trade_operation`（官方 gap=1）

**合成/结构实测**（`synth/layout_probe.py`）：把该 if/with 形状写成四种源码并编译：
- A（`if X: <with…>` 后接 `warning; return False`，**无 else**）→ 字节码**无** `LOAD_CONST None; RETURN_VALUE`；
- B（`if X: <with…> else: warning; return False`）→ `…with清理 4 pops + LOAD_CONST None + RETURN_VALUE + else体`，与 orig **逐条一致**；
- D（`if X: <with…>; return None` 后接 warning）→ 与 B **逐条一致**。
⇒ orig 源必为 B 或 D 形（都编译出 1464-1466 的裸 `return None`），而反编译产物是 A 形（`orelse=[]`，AST 实测 `Try.body=[If(orelse=[]), Expr, Return]`，全树 `return None` 计数=0）。

**CFG 实测**（`cfgprobe.py`）：`@350 POP_JUMP_FORWARD_IF_FALSE → 1468`（false 臂）、`@414`（true 臂）；
`@1456→@1458→@1464(LOAD_CONST None+RETURN_VALUE, succ=[])`，`@1464` 的唯一前驱链回溯到 `@1442`（with 异常处理器），
而 `@1442` 的 **全部 28 个前驱都在 then 臂内**；`@1468` 的唯一前驱是条件块 `@350`（**与 then 臂完全不相交**）。
⇒ then 臂与 false 臂**不汇合**；`return None@1464` 是编译器为 then 臂真实出口排出的函数级隐式 return。

**区域实测**（`reginfo.py`）：`IfRegion@350 cond=350 then=[414…1438]`（31 块，**不含** 1442/1456/1458/1464）、
`merge_block=1468`、`exit=1468`、**`else_blocks=[]`**。`NCPD(414,1468)=None`、`_find_merge_via_forward_reachability=None`、
`_compute_merge_from_jump_targets=None`——三个正统 merge 算法全空。

**定位实测**（`sys.settrace` 监 `merge` 局部变量）：`merge=1468` 是在
`region_analyzer.py::_identify_conditional_regions` **L17679 `merge = else_succ`**（`[25b]` 规则，L17655-17680）赋的值；
`_build_basic_if_region` 被调用时已是 `merge=1468, else=[]`。

**根因**：`[25b]` 规则「then 臂是汇点 ⇒ else_succ 即 if 之后的顺序语句 ⇒ `merge := else_succ`（AST 映射：`If(test, then_body, [])` 无 orelse）」
在本形态下判错：then 臂的"汇点性"来自 `with` 的异常处理器**被压制路径**（`@1442→@1456→@1458→@1464`）掉出臂外、落在
**只从 then 臂可达、else_succ 不可达**的裸 `return None` 块上。编译器把该落点排在 else 臂之前，证明 `@1468` 是 **else 体**而非
if 之后的语句；`merge := else_succ` 把 `else_blocks` 收空 ⇒ 生成器输出 A 形 ⇒ 少 2 条指令（官方/严格 `trade_operation` seq_len 304→302）。

## Step 3 · 合成见证（同层次结构，非复制靶源）

产出 `synth/r70_variants_25b.py` → `synth/r70_variants_25b.pyc`（11 个形状 + 2 个辅助），
用 `armcmp.py <arm> <pyc>` / `nested_diff.py` / `tracefire.py` 三读。

**咬合形状 `v9`**（全部三层条件同时满足才成立）：
```
try:
    if os.path.exists(...):            # 条件块 → false 臂 = else 入口
        with open(...):                # then 臂 = 单个 with
            <body 一律硬 return>        # with 正常出口不可达 ⇒ 清理链只走异常边
            return trades
        return None                    # 【关键】then 臂内、with 之后的裸 return
    else:                              # else 体在该 return 之后另起
        log_warning(...); return False
except BaseException: ...
```
- `head`：`v9 orig=80 decomp=78 DELTA=-2`，`nested_diff` = `delete ['LOAD_CONST None','RETURN_VALUE']`
  —— **与官方靶 `trade_operation` 304→302 同签名（少且仅少这 2 条）**。
- `r70diag3_a2`：`v9 orig=88... → positional-diffs=0`，`nested_diff` 零 hunk；官方
  `pyc_batch_verify` 从 head `['v9',80,78,1,26]` 变为**不再入 mism**。
- 文件级官方口径：head `6/14` → a2 **`7/14`，IMPROVED，REGRESSION=0**。

**对照（守卫不得误伤）**：
- `v5`（同 then 臂、**无 else**、trailing 调用在 if 之后）：head 与 a2 均 `positional-diffs=0`，
  官方两臂均不在 mism —— 守卫在该形状不改变产物。
- `v7`（else 不返回）head/a2 均 0；`v10`（then 臂内 return None 但 with 正常出口可达）head/a2 均 0。
- `tracefire.py r70diag3_a2` 全文件 6 次 FIRE，官方 `REGRESSION=0`。

**锚点**：`h62.py build` 断言 `anchor occurrences == 1`、`patch applied`、`head mirror == worktree bytes`
——两处锚点均通过（build 输出 `mirrors built: head pristine == worktree bytes, cand patched (2 edits,
core/cfg/region_analyzer.py, BOM=False, nl=CRLF)`）。

## Step 4 · A/B（臂 `r70diag3_a2`，镜像 `center/mirr_r70diag3_a2`）

| 口径 | head（=landed 基线） | r70diag3_a2 | 判定 |
|---|---|---|---|
| 官方 `klinedata.pyc` | 43/45 | 43/45（mism 逐项相同） | SAME |
| 官方 `real_quote.pyc` | 40/44 | 40/44（mism 逐项相同） | SAME |
| 官方 `trade_info_utils.pyc` | **39/40** | **40/40** | **IMPROVED（全清）** |
| 金丝雀 4 文件 | 143/143、10/10、26/26、25/25 | 同 | SAME=4，sha 逐一等于 `4d41187e356544e0` / `af77224b34b203c4` / `e711b8ea86d49a15` / `9d09af09249da177` |
| 45 项电池 | 182/200 bad=18 err=0 | 182/200 bad=18 err=0，**worse=0** | SAME |
| 82 项扩展电池 | 318/356 bad=37 err=0 | 318/356 bad=37 err=0，**worse=0** | SAME |
| 严格尺（3 支 149 函数） | 136/149 缺陷 13 | 136/149 缺陷 13 | SAME（缺陷数不增） |
| 合成见证 `r70_variants_25b.pyc` | 6/14 | **7/14，REGRESSION=0** | IMPROVED |

严格尺缺陷位移（**非新增**，同函数旧缺陷被顶掉后露出既有缺陷）：
`trade_operation` 由 `[seq_len] orig=304 decomp=302` 变为 `[target_diff] #94 POP_JUMP_IF_FALSE
orig=('write_info','LOAD_FAST') decomp=(None,'FOR_ITER')`。
**该 target_diff 在 head 产品里同样存在**（实测 head `trade_operation` 指令108 `POP_JUMP_FORWARD_IF_FALSE to 1042`，
orig 为 `to 1000`；a2 也是 `to 1042`）——即它不是本轮引入，只是被旧的 seq_len 缺陷遮蔽（严格尺每函数只报首条）。
`nested_diff` 口径：head `orig=339 decomp=337 delete LOAD_CONST None+RETURN_VALUE`；
a2 `orig=339 decomp=339`，opname 全等，**仅 1 处 arg 差（该既有 jump target）**。

守卫命中面（`tracefire.py`）：
- 三支靶 pyc 合计 **1 次**：`trade_operation` 的 `cond_then_entry=414 else_succ=1468 n_then=32`；
  `klinedata`、`real_quote` **0 次**（故两支读数逐项不变）。
- 合成见证全文件 6 次，官方口径 REGRESSION=0。

## Step 5 · VERDICTS

| 靶支 | 官方 | 严格 | verdict | 说明 |
|---|---|---|---|---|
| `IQCommon/util/trade_info_utils.pyc` | 39/40 → **40/40** | 37/41 → 37/41（缺陷数 4→4） | **FIXED（官方全清）** | gap 1 → 0；`trade_operation` 官方不再是 mismatch |
| `IQCommon/api/klinedata.pyc` | 43/45 | 58/63 | **UNCHANGED** | 守卫 0 命中，读数逐项相同 |
| `IQData/.../real_quote.pyc` | 40/44 | 41/45 | **UNCHANGED** | 守卫 0 命中，读数逐项相同 |

**候选**：`specs/cand_r70_tradeinfo_25b.json`（`core/cfg/region_analyzer.py`，2 edits）
1. L17677 条件串插入 `and not self._25b_then_arm_orphan_return_none(then_blocks, else_succ)`；
2. 在 `def _if_arm_is_sink` 之前插入新方法 `_25b_then_arm_orphan_return_none`（含三要素注释：
   识别条件 / 归约方式 / AST 映射）。

判据三要素（已写进方法 docstring）：
- **识别条件**：merge is None 候选点上，存在裸 `return None` 块 B 满足 ① 可由本臂沿 CFG 后继
  （含异常表隐式边）到达；② 不在已收集本臂块集内、且从 `else_succ` 前向不可达；
  ③ 不属于任何以本臂块为入口的子区域（with/loop/try/内层 if 的 blocks），即与条件块同层。
- **归约方式**：跳过 `merge := else_succ`，merge 保持 None、对侧臂仍按 `else_blocks` 收集；
  只改归属，不新增块/语句/发射。
- **AST 映射**：`If(test, then_body, else_body)` 保留 orelse，后继语句挂父 SEQ。

**对 BRIEF / targets 的更正**：
1. `BRIEF.md` 是 **Round 69** 模板（正文要求引用 `closeout67.py`，而工作区只有 `closeout69.py`）；
   其 Step 4 的产物命名/脚本引用需按 R70 改为 `closeout69.py` / `mybat.py`。
2. 除此之外 Step 0 基线与 `targets.md` 逐字段一致，**无需更正**。
3. `targets.md`「严格缺陷明细」中 `trade_operation [seq_len] 304→302` 修掉后会露出同函数既有的
   `[target_diff] #94`（见 Step 4），严格缺陷**总数**不变——评估该支时应按「总数不增」而非「逐条位移」。
