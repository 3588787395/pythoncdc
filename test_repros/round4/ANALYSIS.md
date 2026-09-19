# Round 4 根因分析与修复记录

本轮修的是**区域归约算法**本身的两类缺陷，都属「原则 2：每个块在任何层级只属于一个区域」被破坏。

轮次目标：每轮至少完全解决 1 个 pyc。
**本轮达标项：`IQCommon/util/strategy_info_utils.pyc` → 28/28 = 100.00%（修复前 27/28）。**
另一项附带达标：`fly/dockerspawner/dockerspawner.pyc` → 100.00%（修复前 96.00%）。

---

## R4-G：短路归并块跨越语句边界 → 归并点之后的语句被整段吞掉

### 现象（最小复现 `r4_01_boolop_merge_swallows_following_stmts.py`）

```python
def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
    user = self.get_current_user()
    if user is None:
        return 1
    else:
        return 2
```

修复前反编译输出**只到第一行就截断**（带 `yield` 时则整函数塌成 `pass`）：

```python
def f(self):
    op = self.get_argument('a', False) or self.get_argument('b', '')
```

真实受害函数：`fly/oauthenticator/oauth2.pyc` 的 `OAuthCallbackHandler.post`
（一个 `@gen.coroutine` 生成器，190 条指令）修复前反编译只剩 `pass`，修复后恢复出 179 条指令的完整函数体。

### CFG 事实

```
@0   []          -> [46, 88]         LOAD ...; JUMP_IF_TRUE_OR_POP 88      <- 短路跳转
@46  [0]         -> [88]             LOAD ...                             <- 第二操作数
@88  [0, 46]     -> [134, 138]       STORE_FAST op                       <- boolop 归并点
                                     LOAD_FAST self; ... CALL; STORE_FAST user
                                     LOAD_FAST user; POP_JUMP_FORWARD_IF_NOT_NONE 138
@134 [88]        -> []               LOAD_CONST 1; RETURN_VALUE            <- then
@138 [88]        -> []               LOAD_CONST 2; RETURN_VALUE            <- else
```

区域分析结果（修复前）：

```
BoolOpRegion entry=0  merge=88  blocks=[0, 46, 88]
IfRegion     cond=88  entry=88  blocks=[88, 134, 138]      <- 与 BoolOpRegion 争用 @88
```

`block_to_region[88]` 归 BoolOpRegion；生成器先发射 BoolOpRegion（`op = ... or ...`）并把
**整块 @88** 标记为已生成，随后以 @88 为入口的 IfRegion 被静默跳过——语句整体蒸发。

Python 编译器不会在「boolop 归并点」与「后续语句」之间插块边界，所以归并点所在基本块
天然会跨越语句边界。这是 CFG 归一化缺失，不是生成器 bug。

### 修复（`core/cfg/cfg_builder.py`）

新增前置归一化 pass：`_split_blocks_at_short_circuit_merges()`，在 `_connect_blocks()` 之后、
`_identify_exit_blocks()` 之前调用。对每个短路跳转（`JUMP_IF_TRUE_OR_POP` /
`JUMP_IF_FALSE_OR_POP`）的目标块 T：

1. **定位消费点**：进入 T 时栈顶恰是「短路归并值」这一个逻辑值。沿 T 前向累积栈效应
   （push-pop），首个使累积量转负的指令 C 即消费该值的指令。
2. **值消费判据**：C 必须是 `STORE_*` / `POP_TOP` / `RETURN_*` / `YIELD_VALUE`。
   （若 C 是条件跳转或 `BINARY_OP`，说明归并值还在更大表达式里，不切分。）
3. **语句边界必要性守卫**：消费点之后**必须真的还有新语句**（`STORE_*` / `DELETE_*` /
   `CALL`+`POP_TOP` / `RETURN_*` / `RAISE_VARARGS`）。若余下部分只是外层 if/while 的条件
   （取值 + 条件跳转），说明该块是「赋值 + 条件」形态，由既有 IfRegion 机制正确处理，
   **不切分**。
4. **异常保护区间守卫**：切分点若落在异常表任一保护区间 `[start, end)` 内，禁止切分
   （try 体首块被割裂会破坏 TryExceptRegion 的块跨度）。

在 C 之后切分（T 只保留到 C，新块 S 继承 T 的后继）。切分后 BoolOpRegion 的 merge_block
恰好止于归并值消费点，语句与其后的 IfRegion 各自独占入口块。

**收益与代价（全量 402 pyc 实测对照）**：

| | ok_pyc | partial_pyc | failed |
|---|---|---|---|
| 修复前（HEAD cfg_builder） | 332 | 70 | 0 |
| 修复后（R4-G） | **333** | 69 | 0 |

新增达标：`fly/dockerspawner/dockerspawner.pyc` 0.9600 → **1.0000**。
第 3 条守卫消除了最初引入的唯一退化（`IQCommon/arg_checker.pyc` 97.87% → 95.74%，现恢复 97.87%）。

---

## R4-H：嵌套 for 之后的 `continue`（循环回边）被丢弃

### 现象（最小复现 `r4_06_continue_after_nested_for_dropped.py`）

```python
def f(self, tree):
    for node in tree:
        if isinstance(node, int) and isinstance(node.value, str):   # and 链条件
            for ca in BLACK:                                       # 嵌套 for
                if ca in node.value:
                    return {'e': -1, 'i': ca}
            continue                                               # <- 被整条丢弃
        if isinstance(node, str):
            return {'e': -1, 'i': 2}
    return {'e': 0, 'i': ''}
```

四个要素同时具备才触发（去掉任一即正常）：外层 `for`、`and` 链条件、`if` 体内嵌套 `for`、
嵌套 for 之后紧跟 `continue`。

CFG 关键块：

```
@118 [104,158] -> [120,160]    内层 FOR_ITER
@160 [118]     -> [6]          外层循环头 @6 = JUMP_BACKWARD 6，即该 continue
```

`@160` 同时是「内层 for 耗尽出口」与「外层 continue 回边」——CPython 把两者编译进同一块。
`_process_if_blocks` 原有的 `_block_is_structural_for_iter_exit` 判据把「for 耗尽出口」
一律当作结构性迭代收尾而抑制 `Continue`，于是整条 `JUMP_BACKWARD` 丢失。

真实受害函数：`IQCommon/util/strategy_info_utils.pyc` 的 `check_python_code`，
原字节码 @400 的 `JUMP_BACKWARD to 84` 缺失（orig=140 / decomp=139 条指令）。

### 修复（`core/cfg/region_ast_generator.py` 的 `_process_if_blocks`）

补充结构判据：该块是嵌套 LoopRegion 的 for_iter_exit **且**其 `JUMP_BACKWARD` 目标恰是
当前外层循环 header **且** 所属 `IfRegion.merge_block` 不是该 header（即 if 之后循环体内
仍有后继代码需要本回边跳过）→ 判为**显式 continue**，正常发射 `ast.Continue`。
自然收尾形态（`merge_block` 即循环 header）仍走原抑制。

同时调整 R100 冗余抑制优先级：已确认为显式 continue 时不再被 R100 抑制，并保留
`_is_loop_tail_convergence_block`（≥2 前驱汇合）作二次判据——真显式 continue 块只有
FOR_ITER 单前驱。

---

## 本轮验证命令（全部用 3.11：`D:\Python\python.exe`）

```
"D:/Python/python.exe" scripts/pyc_batch_verify.py single site-packages/IQCommon/util/strategy_info_utils.pyc
    -> 28/28 = 100.00%
"D:/Python/python.exe" scripts/pyc_batch_verify.py single site-packages/fly/dockerspawner/dockerspawner.pyc
    -> 25/25 = 100.00%
"D:/Python/python.exe" _r2_run_repro.py test_repros/round4/r4_01_boolop_merge_swallows_following_stmts.py
"D:/Python/python.exe" _r2_run_repro.py test_repros/round4/r4_06_continue_after_nested_for_dropped.py
"D:/Python/python.exe" test_repros/round4/_probe_continue.py        # 5/5 ok
"D:/Python/python.exe" test_repros/round4/_probe_boolop_merge.py    # 13/13 ok
```

无回归护栏（必须保持 matched）：
```
r3_02_fstring_log_dropped / r3_03_while_retry_loop / r3_04_loop_branch_continue_lost /
r3_05_converge_return_misattrib / r3_09_nested_if_else_flatten / r3_10_try_except_block_scramble
```

---

## 必须记录的一个方法论问题：pyc_index.json 的 ok 计数会「陈旧」

`scripts/pyc_batch_verify.py batch` 只处理 `decompile_status != 'ok'` 的条目（本次 `pending=29`），
**从不重验已标 ok 的文件**。因此后续任何改动若弄坏了某个已 ok 的文件，索引不会发现，
`ok_pyc` 计数会虚高。本轮首次做全量复验（构造全量 pending 索引）才发现：
committed 索引标称 373 ok，真值是 332 ok。

后续每轮收尾都应做一次全量复验（把索引全部置 pending 再跑），或给 batch 增加 `--recheck-all`。
