# for-else 后首语句被吸进循环体（REAL46-003 `_c3_mro` v[53]，rr-v5r91 登记，未修复）

状态：**已诊断，未修复**（与 Task 11 REAL46-004 `use_args`、REAL46-003 v[55]
`_find_impl` 同属「循环退出汇合块归属」根因族；按 spec「一次只开一个根因族/
不发半修复」登记，作为后续独立一轮的实施输入）。真实案例：G2c REAL46-003
（stdlib `functools.py`）`_c3_mro`——for-else 之后的 `abcs = list(abcs) if
abcs else []`（三元赋值）被吸进循环体。

## 缺陷（最小复现 fe1_runtime_divergence.json 全实测）

```python
# 源
def m(bases, abcs=None):
    boundary = -1
    for i, b in enumerate(bases):
        if b == 'A':
            boundary = len(bases) - i
            break
    else:
        boundary = 0
    items = list(abcs) if abcs else []      # ← for-else 之后的首语句（三元赋值）
    extra = boundary + 1
    return boundary, items, extra
# HEAD 产物（fe1_out_prefix.py）：整个尾段（含 return）吸进循环体
for i, b in enumerate(bases):
    if b == 'A':
        boundary = len(bases) - i
        break
    items = list(abcs) if abcs else []       # ← 每迭代执行
    extra = boundary + 1
    return (boundary, items, extra)          # ← 第 0 迭代即 return
else:
    boundary = 0                             # ← break 路径整体跳过尾段
# 函数耗尽路径不再 return → 返回 None
```

运行时逐调用对拍（`fe1_repro.py`，原件 vs 产物）：

| 输入 | 原件 | 产物 |
|---|---|---|
| `(['X','A'], {'k':1})`（break 路径） | `(1, ['k'], 2)` | `(-1, ['k'], 0)` **DIFF** |
| `(['A'], {'k':1})`（首迭代 break） | `(1, ['k'], 2)` | `None` **DIFF** |
| `(['X','Y'], {'k':1})`（for-else 路径） | `(0, ['k'], 1)` | `(-1, ['k'], 0)` **DIFF** |

break 路径跳过 `items=`（`abcs` 保持原值，None 时下游 `for base in abcs`
即 TypeError——`_c3_mro` 递归调用链的真实崩溃面）；非 break 路径第 0 迭代
提前 return。**R1 级真实语义缺陷**（REAL46-003 因 module-only 仅跑 R7）。

## 触发边界（fe_variants.py 四形态隔离）

| 形态 | 结果 |
|---|---|
| m2 for-else + 尾随**调用**赋值 `items = list(bases)` | 正确 ✓ |
| **m3 for-else + 尾随三元赋值 `items = list(bases) if bases else []`** | **尾段整体吸进循环体** ✗ |
| m4 for-else + 尾随普通赋值 `items = boundary` | 正确 ✓ |
| m5 无 else + 尾随语句 | 正确 ✓ |

触发边界 = **for-else 存在 ∧ for-else 之后的首语句是三元赋值**（尾块成为
TernaryRegion 条件块）。三元换成调用/普通赋值即不触发。

## 根因链（fe_region_probe / fe_trace_probe 实证）

1. `_collect_natural_loop_body` 正确：body={B2 头,B3 if,B4 break 源,B5 回边}，
   break 目标 B7 经 [R102 for-else fix] 屏障排除在 body 外 ✓。
2. `_detect_break_continue`（[R102 for-else fix] 判据「源块末尾无条件
   JUMP_FORWARD → s 是 break 目标，与 s 内容无关」）把 break **目标** B7
   计入 `break_blocks_set`（命名实为 break 落点集）。
3. 循环装配的 `verified_break_blocks` 路径：
   `elif not any(RETURN in block): region_blocks.add(break_block)`——B7
   （三元条件块，无 RETURN）被**加入 LoopRegion.blocks**（含
   `block_roles[B7]=BREAK`）。该分支的历史用途是让循环后代码可被发射
   走查消费（create_daily_stats 404 形态）。
4. **边界反噬**：`LoopRegion.get_if_branch_boundary_stop` 以
   `succ not in loop_body_set` 判定循环外——B7 已在 self.blocks 内 →
   break 边 B4→B7 不入 boundary → `_collect_branch_blocks` 越过 break 边
   把 B7 收进 `IfRegion@B3.then_blocks`（实测 then_blocks=[B4,B7]，
   blocks={B3,B4,B7}）——与 Task 11 use_args「B15 已在 loop blocks 内 →
   `_compute_in_loop_if_merge` 守卫不触发」同一机制。
5. 生成端：循环体发射按 body/then 走查，B7（TernaryRegion 条件块）与
   B10（return）落进循环体；IfRegion@B3 与 LoopRegion 双重认领 B7 +
   TernaryRegion@B7 第三重认领（区域树重复挂载实测），违反每块唯一归属。

## 与 Task 11 / v[55] 的关系

同根因族（循环退出汇合块归属）：B7/use_args B15/_find_impl 的循环后
return 块，都是「仅经 break/else 路径可达的循环后代码」被 LoopRegion 或
嵌套 IfRegion 收编。差异：use_args 需 BoolOp/if 重叠 + generator 发射三层
同修；本形态（m3）无 BoolOp 重叠、无 generator 独立缺陷迹象——**若 B7 不
进 LoopRegion.blocks，boundary 即恢复，then 收集止于 B7，结构自然正确**。
故本形态是该族最薄的切入口。

## 候选修复（主候选已实测，已回退；本族需 generator 层同修）

- 主候选实测（rr-v5r91 当轮）：装配处 `elif not any(RETURN…):
  region_blocks.add(break_block)` 收窄——落点可从 natural_exit 正常后继链
  可达时不加。**实测结果**：区域树变正确（B7 出 LoopRegion.blocks、
  IfRegion@B3 blocks=[3,4]、TernaryRegion@B7 顶级无重复认领），**但产品
  仍错**——m3/fe1 尾段变成 `if abcs: return list(abcs) else: return []`
  （B8 值块 JUMP_FORWARD 跳向含 RETURN 的 merge B10，被发射层判为
  return 臂）+ 原语句序列重复发射（B10 双算）；且
  `verified_break_blocks`/`has_break`/`block_roles` 依赖目标块注册
  （`_detect_break_continue` 返回的是 break **落点**而非 break 源块），
  直接摘除会丢 `break` 语句。按 spec「不发半修复」回退（树 clean，
  m3 产物与修复前逐字一致复测；实测产物存档
  `m3_out_attempt_narrowed.py`/`fe1_out_attempt_narrowed.py`）。
- 结论：识别层窄改足以矫正区域树，但发射层（三元 vs if 判定、落点
  发射走查）与 break 源/落点注册语义需同步重构——与 Task 11「三层
  缺陷」评估一致。本族完整修复 = 识别层收窄 + generator 层，作为后续
  独立一轮的实施输入。
- 若 NCPD 对「真臂 break 的 in-loop if」仍算出循环后 merge，还需叠加
  v5r82 尝试 2 的支配守卫（该守卫当时 pytest+全量 1556 双零回归）。
- 按 spec 纪律：本轮不携带未验证的中心改动。

## 诚实边界

- 本族**未修复**。REAL46-003 仍 DIFFERENT（R7×3：v[51]/v[53]/v[55]）。
- 不宣称 G1/G2b/G2c/G3/G4/G6 通过；`product_complete` 仍 **NOT PASS**。
- 候选修复仅为归因产物，未经全量语义回归验证，**不作为已证修复**。

## 证据探针（归档于本目录）

| 脚本 | 作用 |
|---|---|
| `fe1_repro.py` | 最小复现（for-else + 尾随三元赋值） |
| `fe1_runtime_divergence.json` | 三调用形态逐调用对拍（原件/产物返回值） |
| `fe_variants.py` + `m{2,3,4,5}_out.py` / `fe1_out_prefix.py` | 四形态隔离 + 反编译产物 |
| `fe_region_probe.py` | m3 区域树 dump（LoopRegion blocks=[1..7]、IfRegion@B3 blocks={3,4,7}） |
| `fe_trace_probe.py` | 装配后即时快照（B7 已在 loop blocks、block_to_region=B7→LoopRegion、break_blocks=[B7]） |
