# 循环内 BoolOp 守卫链 + 双终止臂的 IfRegion 错构（REAL46-003 `_find_impl` v[55]，rr-v5r93 登记，未修复）

状态：**已诊断，未修复**（循环退出汇合块族第三形态：BoolOp 守卫链 + 双终止
臂——then 臂 RAISE、else 臂 break 跳出循环。比 v[53]/use_args 更深一层：
`_build_basic_if_region` 的臂计算/merge 语义对双终止臂失效）。真实案例：G2c
REAL46-003（stdlib `functools.py`）`_find_impl`（module co_consts v[55]）——
`singledispatch` 的实现查找函数，运行时必经路径。

## 缺陷（最小复现 fi1 + 运行时对拍 fi1_runtime_divergence.json 全实测）

```python
# 源（_find_impl 形态）
def find(mro, registry, cls_mro):
    match = None
    for t in mro:
        if match is not None:
            if (t in registry and t not in cls_mro
                    and match not in cls_mro
                    and not issubclass(match, t)):
                raise RuntimeError("Ambiguous: {} or {}".format(match, t))
            break
        if t in registry:
            match = t
    return registry.get(match)
# HEAD 产物（fi1_out_prefix.py）：
for t in mro:
    if match is not None:
        if t not in cls_mro:
            if match not in cls_mro:
                if issubclass(match, t):          # ← 极性翻转（应 not issubclass 才 raise）
                    raise RuntimeError(...)
        else:
            break                                  # ← break 只在 else 臂
        if t in registry and ...:                  # ← 幻影重列条件
            continue
        return registry.get(match)                 # ← 循环后 return 吸进循环内
    elif t in registry:
        match = t
# ← 函数尾 return registry.get(match) 整体丢失（多数路径返回 None）
```

运行时逐场景对拍（`fi1_repro.py`，原件 vs 产物）：

| mro | 原件 | 产物 |
|---|---|---|
| `[int, object]`（match 命中后 break） | `'INT'` | `None` **DIFF** |
| `[str, int]` | `'STR'` | `None` **DIFF** |
| `[float, int]` | `'INT'` | `None` **DIFF** |

三场景全 DIFF——`return registry.get(match)` 在循环内被守卫链拦截、函数尾
return 缺失 → 所有正常路径返回 None。**R1 级真实语义缺陷**（REAL46-003
module-only 仅跑 R7；REAL46-003 exec 的 singledispatch `f(1)` 报
`TypeError: 'NoneType' object is not callable` 即此缺陷 @wrapper:L659，
rr-v5r92 轮已实证 FIXED/HEAD 逐场景一致）。

## 根因（fi_region_probe / fi_trace_probe 实证）

块图（find 函数）：

```
B1 [0]    match=None; GET_ITER          → B2
B2 [10]   FOR_ITER                      → B3 / B13(耗尽)
B3 [12]   STORE t; if match is not None → B4 / B10
B4 [18]   t in registry（conj1）        → B5 / B9(假)
B5 [26]   t not in cls_mro（conj2）     → B6 / B9(假)
B6 [34]   match not in cls_mro（conj3） → B7 / B9(假)
B7 [42]   issubclass(match,t)           → B8(假=not→raise) / B9(真=跳过 raise)
B8 [74]   raise RuntimeError            → (exit)
B9 [144]  POP_TOP; JUMP_FORWARD         → B13（break 跳出循环）
B10[148]  t in registry                 → B11 / B12
B11[156]  match = t                     → B12
B12[160]  JUMP_BACKWARD                 → B2
B13[162]  return registry.get(match)    ← 循环后代码
```

区域树（当前）：

- `LoopRegion@10 blocks=[0,10,12,144,148,156,160] else=[] break_blocks=[144]`
  （B13 循环后 return 块不在循环内 ✓）
- `IfRegion@12 blocks=[12,18,26,34,42,74,144,148,156] then=[18,…,144] merge=None`
  （外层 `if match is not None`，正常）
- **`IfRegion@18 blocks=[18,144,162] then=[] merge=74`** ← 守卫 if 错构核心：
  ①`then=[]`——raise 臂 B74 未收入 then；②`merge=74`——**双终止臂**（then 臂
  RAISE 终止、else 臂 break 跳出循环）本无汇合点，merge 应为 None，实测却取
  了 raise 块 74；③`else=[144,162]`——else 臂走查越过 break 边把循环后
  return 块 B162 收进 else（trace 实证创建点
  `_build_basic_if_region:24953 ← _identify_conditional_regions:24327`）。
- `BoolOpRegion@18 blocks=[18,26,34,42]`（条件链区域存在，但 IfRegion@18 的
  then/else/merge 结构错构驱动生成端把链拆成嵌套 if 级联 + 极性翻转）。
- `block_to_region[162] → IfRegion@18`——循环后 return 块被守卫 if 认领，
  函数级序列失去发射责任 → 函数尾 return 丢失。

## 层次分析（与 Task 11 / v[53] 的关系）

循环退出汇合块族第三形态，比前两形态多一层：

| 形态 | BoolOp 重叠 | 双终止臂 | 修复状态 |
|---|---|---|---|
| v[53]/fe1（for-else 尾随三元） | 无 | 无（break 边后无 if 结构） | **rr-v5r92 已修复** |
| Task 11 use_args | **有**（`save_new = A and B` 吞 if 条件） | 无 | 未修（需 BoolOp 层） |
| **v[55]/fi1（守卫链 + raise/break 双终止）** | **有**（BoolOp 链作 if 条件） | **有**（then=RAISE / else=break） | **本轮登记** |

三处缺陷定位（`_build_basic_if_region` / 调用点 `_identify_conditional_regions`）：
①merge 计算对「双终止臂」（两臂各以 RAISE / break-跳出循环 终止）必须返回
None——现取 raise 块 74 为 merge，驱动生成端把 merge 块当汇合续流渲染；
②then 臂收集漏掉 raise 块 74（then=[]）；③else 臂走查越过 break 边收进
循环后 B162——与 v[53] 同机制（loop 边界未被该臂走查消费；且
`_block_exits_loop(B162)` 过滤项反而把「跳出循环」的 B162 保留在 else 内）。

## 候选修复（未实施）

1. **merge 语义**：`_build_basic_if_region`（或其调用点）在「then 臂尾为
   RAISE_VARARGS/RERAISE ∧ else 臂经 `_block_exits_loop` 跳出宿主循环」时
   merge 置 None、then=[raise 块]、else=[break 桩]（B162 归还函数级序列）。
2. **else 臂边界**：else 走查在 break 边（落点为 `_block_exits_loop` 的
   循环外块）处停止——把 v[53] 轮验证过的「循环边界含 break 落点」判据
   应用到该臂走查（B162 收进边界停止集）。
3. 生成端：双终止臂 if 渲染为 `if <BoolOp>: raise` + 臂外 `break`——BoolOp
   链条件已由 BoolOpRegion 承载，IfRegion 消费端按 then=[raise] 渲染。

风险：`_build_basic_if_region` 为全部 if 归约的公共路径（同 Task 11.2
评估），改动须以全量 1556 闸门验证；单臂终止（仅 raise 或仅 break）的
既有形态（如 `if c: raise` 无 break——现有正确形态）不得回退。

## 诚实边界

- 本族**未修复**。REAL46-003 仍 DIFFERENT（R7×2：v[51]/v[55]）。
- 不宣称 G1/G2b/G2c/G3/G4/G6 通过；`product_complete` 仍 **NOT PASS**。
- 候选修复仅为归因产物，未经全量语义回归验证，**不作为已证修复**。

## 证据探针（归档于本目录）

| 文件 | 作用 |
|---|---|
| `fi1_repro.py` / `fi1.pyc` | 最小复现（守卫链 + raise/break 双终止臂） |
| `fi1_out_prefix.py` | 当前树产物（嵌套 if 级联 + 极性翻转 + return 内移 + 尾 return 丢失） |
| `fi1_runtime_divergence.json` | 三场景逐调用对拍（原件/产物返回值全 DIFF） |
| `fi_region_probe.py` | 区域树/块图/归属 dump（IfRegion@18 错构、B162 被收实证） |
| `fi_trace_probe.py` | IfRegion@18 创建点 trace（`_build_basic_if_region:24953`，then=[] else=[144,162] merge=74） |
