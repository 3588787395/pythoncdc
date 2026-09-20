# Round 14-J — 测试工程师根因报告：`if` 臂体含 try 时 then 区被截断

判据唯一：`_r10_strict_check.strict_compare`（严格尺子，逐指令 + 跳转终点，仅 import）。
复现电池：`test_repros/round14_join/run_all.py`（16 个形状）

```
PYTHONIOENCODING=utf-8 python test_repros/round14_join/run_all.py
repros=16  MISMATCH=11  MATCH=5  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=0   （--strict 退出码 0）
```

目标 pyc：`site-packages/IQCommon/profiler_func.pyc` `<module>`（15/16 干净）。
**同源副本实测为 3 份**（见 §7）。

---

## 0. 一句话结论（以及任务书原假设的判决）

**IfRegion 从来没有被创建。** 不是 merge 算错、不是 `then_blocks` 收错、不是 TryRegion 抢块。

上一条语句 `PY35 = PY3 and sys.version_info[1] >= 5` 归约成一个**值上下文 BoolOpRegion**，
它的 `merge_block`（B204）里装着两条语句：`STORE_NAME PY35`（上一条语句的值消费）
＋ `LOAD_NAME PY35 | POP_JUMP_FORWARD_IF_FALSE 280`（下一条语句 `if PY35:` 的完整测试）。
B204 因此**同时**是 BoolOp 的值归并点和 if 的条件头块（双角色块）。
`_identify_conditional_regions` 在处理候选块时，看到「本块被某个 BoolOpRegion 占有且不是它的
entry」，就在 **`core/cfg/region_analyzer.py:15910`** 一刀切 `continue`，跳过了这个 if 的识别。
真实区域树里（§1.1）**没有任何 IfRegion@204**，于是 `import inspect`（B210）与
`TryExceptRegion@220` 都成了 `<module>` 顶层兄弟区域，产物里那条 `if PY35:` 是生成端
通用块语句路径给双角色块「补」出来的（then 体只拿到紧跟其后的第一个块，假出口落在 try 体），
这就是尺子看到的 `#82 POP_JUMP_IF_FALSE 终点 orig=("'PY35'", LOAD_NAME) decomp=('0', LOAD_CONST)`。

| 任务书假设 | 判决 | 依据 |
|---|---|---|
| 嵌套 `TryRegion` 在 `block_to_region` 里抢块 | **否决** | 真实树里 try 只登记了它自己的 7 个块（B220-B274），B210 无人认领；抢块者是 BoolOpRegion 对 B204 的合法认领（原则 2 正常生效），问题在 if 侧被跳过 |
| 父 `IfRegion` 的 `then_blocks`/merge 在 try 入口停下 | **否决** | 没有 IfRegion，`_collect_branch_blocks` 对本 if 一次都没跑；`_compute_merge_from_jump_targets` / `_find_merge_via_forward_reachability` 与本缺陷无关 |
| `if not PY35:` 的**标志位复读** confuse 了 merge | **否决** | `r14j_12`（完全去掉复读）照样 MISMATCH；复读只改变表现形态（有复读 → 指令数相等的 `target_diff`；无复读 → `seq_len` 少 2 条） |
| 原则 3「嵌套区域在父区域中作为单个抽象节点」被违反 | **确认**（表述为：抽象节点根本没建立） | 见 §5 |

真正必要的触发成分（每个都由一对 MISMATCH/MATCH 复现隔离，见 §6）：

1. 上一条语句是**值上下文短路 BoolOp**（`and`/`or`），其结果用 `STORE_*` 消费；
2. `if` **紧邻其后**，使得 if 头块 == 该 BoolOp 的 `merge_block`；
3. if 的某条臂里存在一个**区域**（try/except、try/finally、try/except/else 皆可）。

三者缺一即 MATCH：`r14j_13`（换成 `b = 2`）、`r14j_14`（换成三元）、`r14j_15`（中间插一条赋值）、
`r14j_16`（try 在外）、`r14j_01`（臂里没有 try）全部 MATCH。

---

## 1. 证据链

### 1.1 真实 pyc 的区域树（`site-packages/IQCommon/profiler_func.pyc` → `<module>`）

```
B134  preds=[86]      succs=[172,204] :: LOAD_NAME sys|LOAD_ATTR version_info|LOAD_CONST 0|BINARY_SUBSCR|LOAD_CONST 3|COMPARE_OP ==|STORE_NAME 'PY3'|LOAD_NAME 'PY3'|JUMP_IF_FALSE_OR_POP 204
B172  preds=[134]     succs=[204]     :: LOAD_NAME sys|...|COMPARE_OP >=                       ← and 链右操作数
B204  preds=[134,172] succs=[210,280] :: STORE_NAME 'PY35' | LOAD_NAME 'PY35' | POP_JUMP_FORWARD_IF_FALSE 280   ← 双角色块
B210  preds=[204]     succs=[220]     :: LOAD_CONST 0|LOAD_CONST None|IMPORT_NAME 'inspect'|STORE_NAME 'inspect'
B220  preds=[210]     succs=[228]     :: ... IMPORT_NAME 'line_profiler_py35'   （try 体）
B280  preds=[204,228,268]             :: LOAD_NAME 'PY35' | POP_JUMP_FORWARD_IF_TRUE 296        （if not PY35:）

==== REGIONS (11) ====
BoolOpRegion     entry=134  blocks=[134,172,204]  merge_block=204  value_target='PY35'  is_condition_context=False
Region           entry=210  type=BASIC  blocks=[210]                        ← import inspect：游离块，无 IfRegion 认领
TryExceptRegion  entry=220  blocks=[220,228,250,258,268,272,274]            ← 顶层兄弟，本该是 IfRegion@204 的子区域
IfRegion         entry=280  then_blocks=[284] merge_block=296               ← 全模块唯一幸存的 IfRegion（if not PY35:）
top-level order = [TryExceptRegion@220, TryExceptRegion@4, TryExceptRegion@86, BoolOpRegion@134, IfRegion@280, ...]
block_to_region:  B204 -> BoolOpRegion@134      B210 -> Region@210      B220 -> TryExceptRegion@220
```

**没有 IfRegion@204。** 真源码的 `if PY35:`（假出口 280）在区域层不存在，
`is_coroutine`/`wrap_coroutine` 的定义（try 的 else 臂）与 `import inspect`（then 臂）被拍平成顺序语句。

同一判据在 `site-packages/IQData/utils/profiler_func.pyc`（merge=B166，假出口 242）与
`site-packages/IQEngine/utils/profiler_func.pyc`（merge=B202，假出口 326）逐字成立。

### 1.2 最小复现（`D:/Temp/r14join/bad.py` = 电池 r14j_12 去掉 docstring）

```python
a = 1
b = a and 2
if b:
    try:
        c = 1
    except ValueError:
        pass
```

区域树（12 块 / 5 区域）：

```
B12  preds=[0,10] succs=[18,52] :: STORE_NAME 'b' | LOAD_NAME 'b' | POP_JUMP_FORWARD_IF_FALSE 52   ← 双角色块
BoolOpRegion entry=0 blocks=[0,10,12] merge_block=12 value_target='b' is_condition_context=False
Region entry=18 BASIC / TryExceptRegion entry=20 blocks=[18,20,24,28,36,38,44,46] / Region entry=52
IfRegion 集合 = {}                      ← 整个作用域一个 if 区域都没有
产物：a = 1; b = a and 2; if b: pass; try: c = 1; except ValueError: pass
尺子：<module> seq_len 27→25（真实文件里是 136=136 的 target_diff，同一根因两种表现）
```

### 1.3 正对照：**同一双角色块，归并者是三元表达式时一切正常**

`D:/Temp/r14join/tern.py`（电池 r14j_14 的无 docstring 版）：

```python
a = 1
b = (2 if a else 3)
if b:
    try: c = 1
    except ValueError: pass
```

```
B16 :: STORE_NAME 'b' | LOAD_NAME 'b' | POP_JUMP_FORWARD_IF_FALSE 56      ← 与 1.2 的 B12 逐指令同构
TernaryRegion  entry=0  blocks=[0,10,14] merge_block=16 value_target='b'
IfRegion       entry=16 condition_block=16 then_blocks=[22,24,28] else_blocks=[56] merge_block=56
TryExceptRegion entry=24 parent=IfRegion@16                                ← 嵌套即抽象节点，正确
产物 = 原样，MATCH
```

`D:/Temp/r14join/extra.py`（电池 r14j_15：BoolOp 后插一条 `q = 5`）同样正确
——因为 if 头块变成 B14（`STORE q | LOAD b | POP_JUMP`），**不再是** BoolOp 的 merge 块。

⇒ 结论：这不是「双角色块本质上无法处理」，而是 **BoolOp 路径缺了 Ternary 路径已有的那道判据**。

---

## 2. 决策点逐行（`core/cfg/region_analyzer.py`，`_identify_conditional_regions`）

候选块遍历（15616 `for block in blocks_in_reverse:`）走到 B204/B12 时：

| 行 | 代码 | 对 B204（真实）/ B12（最小）的求值 |
|---|---|---|
| 15862-15864 | `_owning_boolop = block_region`（`block_region` 是 BoolOpRegion 且 `entry != block`） | 命中 → `_owning_boolop = BoolOpRegion@134 / @0` |
| 15883-15888 | 豁免 1 `_is_merge_if_condition`：要求 `not is_condition_context` **且块内含 `COMPARE_OP`** | **False** —— B204 = `STORE|LOAD|POP_JUMP_IF_FALSE`，没有 COMPARE_OP |
| 15892-15905 | 豁免 2 `_is_merge_with_guard_clause`：要求 value_target 的 STORE **之后还有第二个 STORE**（`_other_store_after_vt`） | **False** —— B204 只有一个 STORE（idx=0），后面是 LOAD+POP_JUMP |
| **15910-15911** | `elif any(block in br.blocks and br.entry != block for br in boolop_regions): continue` | **True → `continue`，IfRegion 不创建** ★ 缺陷点 |
| 15912-15925 | 只有走到 `else:` 分支才会有「then_cand 是否属于结构区域」的补救判定 | 永远走不到 |

谓词求值实测（`D:/Temp/r14join/pred_eval.py`，只读复算，未改 core）：

```
IQCommon/profiler_func.pyc  B204: 豁免1=False 豁免2=False 一刀切=True -> IfRegion NOT created   （IfRegion entries=[280]）
IQData/utils/…             B166: 同上
IQEngine/utils/…           B202: 同上
bad.py                      B12 : 同上                                                          （IfRegion entries=[]）
```

★ **单点结论：`core/cfg/region_analyzer.py:15910`（配合其上游 15892-15905 的过窄判据）。**

补充反例（务必不要照此"修"）：把条件写成 `if b > 0:` 时豁免 1 会命中、IfRegion 会被创建，
但产物从 29 条塌成 **9 条**（整个 if 连同臂体一起消失）——
`a=1; b=a and 2; if b > 0: try: c=1; except ValueError: pass` 实测 `seq_len 29→9`。
⇒ **只放宽 15883 的 `COMPARE_OP` 判据是错误的修法**：IfRegion 建立之后，
还必须把「块内前缀（值消费 STORE）」从条件里切出来（既有机制 `_merge_boolop_guard_prefix_end`，
15932-15949，当前仅在豁免 2 命中时才计算），否则条件表达式会把 `STORE` 当成条件的一部分。

---

## 3. 为什么症状是「截断 + try 逃逸」而不是「整块丢失」

区域层没有 IfRegion，但 B204 尾部的 `POP_JUMP_IF_FALSE 280` 仍在，
生成端按「通用块语句」路径消费这个双角色块：先发射 `PY35 = PY3 and ...`，
再为块尾条件跳转补一个合成 `if`，其 then 臂 = 下一个被派发的区域（B210 的 `import inspect`），
假出口自然落到 B220（`LOAD_CONST 0` = `IMPORT_NAME`）。所以：

* 语义指令数不变（136=136），只有落点错 → 尺子报 `target_diff`（`#82`）；
* 最小复现里没有 B210 这条独立语句（try 是臂体唯一语句），合成 `if` 的 then 退化为 `pass`，
  少掉 2 条 → 尺子报 `seq_len`。

生成端已具备承接能力：`_downstream_region_entry`
（`core/cfg/region_ast_generator.py:41177-41219`，R35 双角色派发）就是为
「块前缀归上游区域、块后缀归另一个区域」设计的，其判据 (a) 是
`R.entry is block` 且 `R is not block_to_region[block]`。
**只要分析端把 IfRegion 建出来（entry == BoolOp.merge_block），生成端就有现成派发口**；
同时必须确认合成 `if` 的兜底路径不再触发（否则双份 if）。

---

## 4. 现成的正确判据（就在同一个文件里，只差没被调用）

`_ternary_merge_hosts_next_if`（**`core/cfg/region_analyzer.py:25398-25446`**）——
Ternary 路径在 15770 调用它，BoolOp 路径从未调用。把它直接喂给 BoolOp 的 merge 块，实测：

```
IQCommon/profiler_func.pyc  B204  value_target=PY35  判据=True   IfRegion_created=False
IQData/utils/…              B166                    判据=True   IfRegion_created=False
IQEngine/utils/…            B202                    判据=True   IfRegion_created=False
bad.py                      B12   value_target=b     判据=True   IfRegion_created=False
```

该判据全是结构不变量（POP_JUMP_*、两个条件后继都在表达式区域块集之外、
块内最后一个 `POP_TOP/STORE_*` 之前是语句边界、其后只有操作数构造指令），
没有任何 opcode 序列特例或偏移特例 ⇒ **修法 = 让 BoolOp 路径复用同一判据**，
而不是再写第三个豁免。

---

## 5. 算法上正确的行为（区域归约四项原则表述）

1. **原则 1（自底向上归约）**：BoolOp/Ternary 等**表达式区域**先归约（Phase 2a/2b），
   这是它们占有 merge 块前缀的原因，本身正确，不得回退。
2. **原则 2（每块唯一归属）**在块粒度上是**指令可分区**的：一个基本块 =
   「[语句 k 的求值/值消费前缀] ++ [语句 k+1 的前导]」。前缀归上游表达式区域，
   后缀归下游结构区域；`block_to_region` 是单值映射，只能记录一个归属者，
   **不得因为"这已被记录"就宣布下游结构不存在**（这正是 15910 犯的错）。
3. **原则 3（嵌套即抽象节点）**：`TryExceptRegion@220` 必须成为 `IfRegion@204` 的
   `children`，在父区域的 then 区里作为单个抽象节点参与归约；
   BoolOpRegion 则保持为 `<module>` 序列里位于该 IfRegion **之前**的一条表达式语句区域
   （不是 IfRegion 的子节点，它的块已经被值消费完毕）。
4. **原则 4（父引用子入口）**：`IfRegion.entry = IfRegion.condition_block = B204`
   （= BoolOpRegion.merge_block），`then_blocks` 从 B210 起收集、
   以 `POP_JUMP_IF_FALSE` 的目标 280 为 `merge_block`；
   BoolOp 的内部块 `{134,172}`（以及 entry 块自身的前缀）必须登记进 `chain_blocks`
   （Ternary 路径就是这么做的：15962 `chain_blocks.update(_tr_c1b.blocks)` /
   15964-15968 `_ternary_merge_protect_blocks`），否则 `_collect_branch_blocks`
   会顺着 BoolOp 内部块回溯，把 `PY3 = ...` 吸进 then 体。
5. 若同时判定「块内条件测试前存在值消费 STORE/POP_TOP」，则必须把该前缀的**发射权**
   交回表达式区域（既有机制：`_merge_boolop_guard_prefix_end`，15932-15949；
   生成端：`_downstream_region_entry`）。**merge 计算本身不需要任何改动** ——
   假出口 280 就是 `POP_JUMP_IF_FALSE` 的直接目标，正常 IfRegion 建立后
   `find_nearest_common_post_dominator_two(B210, B280)` 无需介入即可给出正确 merge。

---

## 6. 触发成分二分表（16 个复现，实测快照）

| # | 文件 | 形状（相对最小形状的唯一差异） | 实测 | EXPECT | 隔离掉的成分 |
|---|---|---|---|---|---|
| 01 | `r14j_01_neg_if_import_only` | `if c: import x`，无 try | MATCH 20=20 | MATCH | 负对照：单语句 then 区无害 |
| 02 | `r14j_02_real_shape_module` | 真实源码还原（BoolOp 标志 + if 内 try/except/else + `if not PY35:` 复读） | **MISMATCH** `target_diff #24`（67=67，与真实 #82 逐字同构） | MISMATCH | 真实缺陷本体 |
| 03 | `r14j_03_one_stmt_prefix_try_except` | 一条 import + try/except（无 else、无复读） | **MISMATCH** 51→49 | MISMATCH | try/except 的 `else` 臂非必要 |
| 04 | `r14j_04_assign_prefix_try_except` | then 首条语句换成普通赋值 | **MISMATCH** 49→47 | MISMATCH | 与 import/IMPORT_NAME 无关 |
| 05 | `r14j_05_two_assign_prefix_try_except` | then 前缀两条赋值 | **MISMATCH** 51→49（两条都保留） | MISMATCH | 截断点 = 第一个非本区域块，与前缀长度无关 |
| 06 | `r14j_06_try_first_and_only_stmt` | try 是 then 唯一语句 | **MISMATCH** 47→45（产物 `if PY35: pass`） | MISMATCH | 前缀语句非必要 |
| 07 | `r14j_07_try_except_else_in_then` | then 以 try/except/**else** 结束 | **MISMATCH** 56→54（else 内容被并进 try 体） | MISMATCH | try 形态 1/3 |
| 08 | `r14j_08_try_finally_in_then` | then 以 try/**finally** 结束 | **MISMATCH** 46→44 | MISMATCH | try 形态 2/3（无 handler 块也触发） |
| — | （02/03 即 try/except/else 与 try/except 两形态） | | | | try 形态 3/3 |
| 09 | `r14j_09_try_in_else_arm` | try 挪进 **else** 臂 | **MISMATCH** 49→47（else 关键字消失） | MISMATCH | 与臂极性无关 |
| 10 | `r14j_10_try_in_elif_arm` | try 挪进 **elif** 臂 | **MISMATCH** 54→52（elif 链塌成顺序语句） | MISMATCH | 链式臂同等受害 |
| 11 | `r14j_11_function_scope_boolop_try` | 同形状放进**函数**里（LOAD_FAST/STORE_FAST） | **MISMATCH** `<module>.f` 29→27 | MISMATCH | scope 无关 |
| 12 | `r14j_12_no_flag_retest_module` | 去掉 `if not PY35:` 复读的最小模块级形状 | **MISMATCH** 29→27 | MISMATCH | **否决「复读混淆 merge」假设** |
| 13 | `r14j_13_neg_plain_flag_no_boolop` | `b = a and 2` → `b = 2` | MATCH | MATCH | 必要条件 1：值上下文短路 BoolOp |
| 14 | `r14j_14_neg_ternary_flag` | BoolOp → **三元表达式**（同构双角色块） | MATCH | MATCH | 必要条件 1 的精细边界：Ternary 有豁免、BoolOp 没有 |
| 15 | `r14j_15_neg_non_adjacent_boolop` | BoolOp 与 if 之间插 `q = 5` | MATCH | MATCH | 必要条件 2：头块必须是 merge 块本身（也是既有豁免 2 的边界） |
| 16 | `r14j_16_neg_if_inside_try` | **反向嵌套** `try: if b: …` | MATCH | MATCH | 必要条件 3：区域方向；否决「try 抢块」假设 |

11 MISMATCH + 5 MATCH，全部 AS-EXPECTED；无 SENTINEL / UNCONFIRMED。

---

## 7. 杠杆与回归范围

`site-packages` 全量 406 个 pyc（排除 `__pycache__` 重复）跑本类**结构签名**
（存在值上下文 BoolOpRegion，其 merge_block 以 `POP_JUMP_IF_*` 结尾，且无 IfRegion 以该块为
entry/condition_block；脚本 `D:/Temp/r14join/scan_signature.py`，2.6 秒）：

```
with-signature = 3 / 406
   IQCommon/profiler_func.pyc        B204 -> 280   （15/16，唯一缺陷 <module>）
   IQData/utils/profiler_func.pyc    B166 -> 242   （13/14，唯一缺陷 <module>）
   IQEngine/utils/profiler_func.pyc  B202 -> 326   （15/17：<module> 本类 + show_func 300→242 另一类）
```

⇒ 修好本类：**2 个文件直接 100%**（IQCommon、IQData/utils），第 3 个文件少 1 个缺陷
（`IQEngine/utils/profiler_func.pyc` 的 `ProfilerTool.show_func` 58 条指令差属另一类，
不在本类范围）。全库仅此 3 处该签名 ⇒ 修复的影响面天然收敛，
但**必须以 §6 的 5 个 MATCH 负对照作为不回归门槛**（它们正是可能被"放宽"误伤的形态）。

修复验证命令（不得跑 402 文件批）：

```bash
PYTHONIOENCODING=utf-8 python test_repros/round14_join/run_all.py --strict   # 期望 UNEXPECTED=0
PYTHONIOENCODING=utf-8 python _r10_strict_check.py \
  site-packages/IQCommon/profiler_func.pyc site-packages/IQData/utils/profiler_func.pyc \
  site-packages/IQEngine/utils/profiler_func.pyc                              # 期望 函数级 46/47
```

当前基线（实测，修复前）：函数级严格一致 **43 / 47**，缺陷 4 条 =
本类 3 条 `<module>` target_diff（IQCommon #82、IQData/utils #64、IQEngine #82）
+ 另一类 1 条（`IQEngine <module>.ProfilerTool.show_func` seq_len 300→242）。
本类修好 ⇒ 3 条 target_diff 消失 ⇒ **46/47**，文件级 2/3（IQCommon、IQData/utils 变 100%）。

---

## 8. 一旦 merge/归属算对，会变成死代码或需复审的既有启发式

| 位置 | 现状 | 判定 |
|---|---|---|
| `region_analyzer.py:15910-15911` | 「块被 boolop 占有且非 entry」→ 无条件 `continue` | **必须收窄**为「块不是任何语句的完整条件测试头」（即 `_ternary_merge_hosts_next_if` 的否命题），否则本类不可能修好 |
| `region_analyzer.py:15892-15905` `_is_merge_with_guard_clause`（要求第二个 STORE） | 只覆盖「merge 块里值 STORE 之后还有别的赋值」 | **被通用判据完全包含 ⇒ 死代码**（`_other_store_after_vt` 变成多余条件） |
| `region_analyzer.py:15883-15888` `_is_merge_if_condition`（要求 COMPARE_OP） | 只覆盖「值 STORE 后跟 `(a and b) == (c and d)` 型比较」 | **被通用判据包含 ⇒ 死代码**；且实测单独放宽它会产出 29→9 的更糟结果（§2 末） |
| `region_analyzer.py:15912-15925` `then_cand in 结构区域` 补救分支 | 本类永远走不到 | 保留，但需复核它在 BoolOp 双角色块放行后的语义（它正是「then 头是 try 区域入口」的现成识别器） |
| `region_analyzer.py:15932-15949` `_merge_boolop_guard_prefix_end` | 仅豁免 2 命中时计算 | **不应删除，应提升为通用**（任何"块内前缀已被消费"的双角色块都要算前缀切点） |
| `region_analyzer.py:378-411` `IfRegion.get_offset_range`（"按需扩展到后继 try 体" + `_has_closer_loop` 三重回退） | 为「try 紧跟 then 块」的错位打分兜底 | 本类修复后对本类形态**不再触发 ⇒ 需回归审计**（很可能整体退化为死代码） |
| `region_analyzer.py:25546-25600` `[W14-C]` 反向剪枝（含 R14b none-tail 豁免 25554-25587、`_w14_pred_is_child_structural_exit` 25594）与 `25609-25623` R37 可达性收敛 | 全部 `and not merge` 门控，即「merge 没算出来」时的收口 | 本类产生正确 IfRegion 后 merge 非 None ⇒ 这三段对本类**不再进入**；不得反过来依赖它们修本类 |
| `region_analyzer.py:25523-25536` `if False and len(collected) > 1:` | 字面死代码（`False and`） | 建议随手删除（与本类无关，纯卫生） |
| `region_analyzer.py:2014-2016` `_find_merge_via_forward_reachability` 的 `[R13-A3 扩展]` | 被 `if True: return None`（TEMP-DISABLED）短路，2017-2050 不可达 | 字面死代码（与本类无关，纯卫生） |
| `region_ast_generator.py:20220-20248` `[R61]` BoolOp fallback、`31109-31168` 「standalone if from BoolOp merge」 | 只在 `is_condition_context=True` 或 `entry is block` 时触发 | 与本类不冲突，但**修复后必须确认这些兜底不再对本类形态发射合成 `if`**（否则双份 if） |

## 9. 禁止条款（按本轮实测得出的形式约束）

* 禁止按 **scope** 特判：`r14j_11`（函数作用域）与 `r14j_02`（模块作用域）同等 MISMATCH；
  不得写 `co_names`/`LOAD_NAME` vs `LOAD_FAST` 分支。
* 禁止按 **try 形态** 特判：`try/except`、`try/except/else`、`try/finally` 三种
  （02/03/07/08）同等 MISMATCH，`else`/`PUSH_EXC_INFO`/handler 块都不是因。
* 禁止按 **臂体语句类型或条数** 特判：`import`/赋值、0/1/2 条前缀（04/05/06）同等 MISMATCH。
* 禁止按 **臂极性** 特判：then/else/elif（03/09/10）同等 MISMATCH。
* 禁止用偏移、指令计数或 `if b > 0` 这类源码字面形态做豁免（§2 反例）。
* 修复不得依赖 `block_to_region` 的登记顺序调整（原则 2 的语义不变，双角色是**指令级分区**
  而不是块抢占）。
