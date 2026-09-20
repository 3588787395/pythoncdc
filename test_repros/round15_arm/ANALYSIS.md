# Round 15-B 现场分析：父臂吸入嵌套区域的内部块

配套电池：`run_all.py` + `r15a_NN_*.py`（12 形状，首轮实测 9 MISMATCH / 2 负对照 MATCH /
1 UNCONFIRMED）。判定尺子＝`_r10_strict_check.strict_compare`（唯一真值）。

## 触发形状（一句话）
一个 if 的臂体里先出现**值上下文 BoolOp 赋值**（`flag = a and b`），紧随其后又是一条
`if` —— 后一条 if 的**入口块就是前一条 BoolOp 区域的 merge 块**（双角色块），
于是它的整批内部块被挂到**祖父**的臂上，它自己一条也没发。

## 判据成分（由负对照隔离，全部实测）
| 形状 | 结果 | 结论 |
| --- | --- | --- |
| 07 去掉 BoolOp 前缀（普通赋值 + `if flag:` + try） | **MATCH** | 触发必需「子 if 入口块 == BoolOp merge 块」 |
| 12 去掉中间 if（BoolOp 前缀 + try 直接在臂里） | **MATCH** | 触发必需存在被越过的**中间** if |
| 04 臂体 try/finally、05 臂体 for、06 臂体又是 BoolOp 赋值 | MISMATCH | 与臂体区域**类型**无关 |
| 08 子 if 条件是比较式（不是裸名复读） | MISMATCH | 与条件形态无关 ⇒ **禁止**写「裸名条件」式判据 |
| 09 子 if 在 elif 臂 | MISMATCH（39→48，多 9 条） | 同族既有「丢」也有「重复发射」两种症状 |
| 02 同一形状搬到模块级 | MISMATCH（73→71） | 与作用域无关 |

## 真实靶子（一处修复翻多个 pyc）
| 靶函数 | pyc | 严格尺子 |
| --- | --- | --- |
| `ArgumentChecker._is_valid_quarter` | `IQCommon/arg_checker.pyc`、`IQData/utils/arg_checker.pyc`、`IQEngine/utils/arg_checker.pyc`（**×3**，48/49） | `seq_len orig=90 decomp=88`，少的正是 `LOAD_FAST valid; POP_JUMP_FORWARD_IF_FALSE` |
| `PluginManager.set_engine` | `IQEngine/core/plugin_manager.pyc`、`IQData/manager/plugin_manager.pyc`（×2，8/9） | `target_diff #60 JUMP 终点 orig='time' decomp='system_log'` |
| — | `test_repros/round14_join/r14j_09_try_in_else_arm.py`（本轮唯一残留 MISMATCH） | `seq_len orig=49 decomp=47` |

## 结构证据（`_is_valid_quarter`，`D:/Temp/r15_dump_regions.py`）
```
BoolOpRegion@12 blocks=[12,64,86] merge_block=86:
      86: STORE_FAST valid | 88: LOAD_FAST valid | 90: POP_JUMP_FORWARD_IF_FALSE 99
IfRegion@86     blocks=[86,92,94,152,162,166,168,222,232,236,238]
                condition_block=86（同一块） then_blocks=[92,94,…] merge_block=290
                guard_clause_prefix_end=88 parent=IfRegion@0
TryExceptRegion@94 … parent=IfRegion@86        ← 父子登记是**正确**的
```
`D:/Temp/r15_tr_pib.py` 打印臂块表：
```
[PIB] region@0 branch=else blocks=[92, 94, 152, 162, 166, 168, 222, 232, 236, 238]
      blk 94 entry_region=TryExceptRegion@94 owner=TryExceptRegion@94
      <- 1 stmts: ['Try']
```
⇒ 祖父 IfRegion@0 的 else 臂拿到了 IfRegion@86 的**全部内部块但不含入口块 86**，
臂内按 `_try_entry_generate`（`region_ast_generator.py:20197`）直接派发孙辈 Try；
IfRegion@86 之后在 `generate()` 主循环 `:1570-1577`
（`all(b in self.generated_blocks for b in region.blocks) → continue`）被跳过。
wrap 验证：本函数内 `_generate_if` 只对 entry=0 / entry=290 调用过，**从未对 86 调用**。

## 原则层面缺的那一条
原则 4：「归约后父区域的 then/else 列表引用**子区域的入口**，而不是子区域的所有块」。
`region_analyzer._collect_branch_blocks`（`:25523`）自陈「纯拓扑收集，不使用
block_to_region 排除，区域归属冲突由上层调用者处理」⇒ 臂收集必须在
「另一个尚未发射的结构区域入口」处**止步**；`generate()` 主循环的
`all(blocks 已生成)` 也必须换成「本区域自身是否已发射」的权威判据
（与 A2 在前缀发射权上处理的是同一类量纲错配）。

r14j_09 是同一边界判据的**反向**症状（IfRegion@84 的 else 臂早止步，
`TryExceptRegion@100` 以兄弟身份抢走 [98,100,…] 且 `parent` 为空）——
「过晚止步（吸入孙辈块）」与「过早止步（臂被兄弟抢走）」必须用同一条判据解决。
