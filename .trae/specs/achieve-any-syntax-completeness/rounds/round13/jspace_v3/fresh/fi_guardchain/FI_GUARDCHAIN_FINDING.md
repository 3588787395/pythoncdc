# 循环内 BoolOp 守卫链 + 双终止臂的 IfRegion 错构（REAL46-003 `_find_impl` v[55]，rr-v5r93 登记诊断，rr-v5r94 修复）

状态：**已修复**（rr-v5r94：`region_analyzer.py` `_identify_conditional_regions`
break-角色 merge 分支补「then_succ 无实质语句」守卫，一行判据只增不破）。
真实案例：G2c REAL46-003（stdlib `functools.py`）`_find_impl`（module
co_consts v[55]）——`singledispatch` 的实现查找函数，运行时必经路径。修复后
v[55] **字节级 EQUAL**，REAL46-003 R7 差 **2→1**（仅剩 v[51] `_c3_merge`
IfRegion 反转——语义等价独立子族）。

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

## 修复（rr-v5r94，一行判据只增不破）

### 根因精确定位（rr-v5r93 候选修复方向的收敛）

`sys.settrace` 行级追踪 `_identify_conditional_regions` 的全部 `merge =`
赋值点（`fi_trace5.py`），merge=74 的唯一来源：

```
L23707  elif _else_role in (BlockRole.BREAK, BlockRole.PURE_BREAK):
              ...
              if not _elif:
                  merge = then_succ        # ← else 臂是 break ⇒ merge=then_succ
```

该分支位于 sink 计算之前（注释：break 角色判据「前移至 sink 回退之前」），
对 else 臂是 break 的形态无条件取 `merge=then_succ`（仅挡 elif 条件块）——
**未检查 then_succ 是否为无实质语句的裸 fall-through 块**。本族 then_succ
是 raise 块（终止）→ merge=74 为捏造汇合点，连锁：①then 臂收集
`entry==merge` 退化为 `then=[]`（raise 臂丢失）；②else 臂以 merge=74 有界
收集越过 break 边把循环后 B162 收进 else；③生成端按错构区域渲染出嵌套
if 级联+极性翻转+break 移位+return 内移。同函数 wl32 修复（both-sink 场景）
早已有同口径 `_then_meaningful` 守卫——但 merge 已被本分支提前污染，
wl32 守卫永不触达。

### 修复

`elif _else_role in (BREAK, PURE_BREAK):` 分支补 wl32 同口径
`_then_meaningful` 守卫——then_succ 含实质指令（RAISE/RETURN/调用/赋值等，
去除 NOISE 与纯跳转后非空）时**不设** merge=then_succ（merge 维持 NCPD 的
None，双臂无汇合点）。裸跳转/空块维持旧 merge=then_succ（C3：既有
`if c: break` 形态逐位不变）。

修复后流向：merge=None → 双 sink（then=RAISE / else 经 ipdom 链至 RETURN）
→ wl32 两分支均不设 merge → 臂收集 then=[74 raise]、else=[144 break 桩]
（B162 由循环边界挡住，归还函数级序列）→ 生成端渲染
`if <BoolOp>: raise` + `break` + 循环后 `return registry.get(match)`。

### 与候选修复原案的偏差

原案（rr-v5r93）预设需三处改动（merge 置 None + else 臂边界 + 生成端渲染）；
实测只需 merge 守卫一处——merge=None 后既有的双 sink 走查（wl32 不设
merge）、循环边界（B162 已在 boundary_stop）、then=[raise]/else=[break 桩]
收集、生成端 `if <BoolOp>: raise`+break 渲染全部按既有路径自然正确，
无需新增生成端逻辑。

## 验证（实测读数）

| 检查 | 修复前 | 修复后 |
|---|---|---|
| fi1 repro（守卫链+双终止臂，三场景原全 DIFF） | 嵌套 if 级联+极性翻转+return 内移+尾 return 丢失 | **co_code+异常表逐字节相等**；四调用场景（含无守卫命中路径）返回值逐项 SAME |
| REAL46-003 v[55] `_find_impl` | co_code 差 | **逐字节相等**（`elif` 渲染与源 `if` 分支字节恒等——外层 if 真臂恒 break 使二进制同构） |
| REAL46-003 权威 semantic_diff | R7×2 | **R7×1**（仅剩 v[51] `_c3_merge` IfRegion 反转——语义等价独立子族） |
| fe 家族 m2-m5/fe1（rr-v5r92） | 正确 | 逐字节不变 |
| te_shapes s1-s5、te_variants v1-v8、w28 w1/w3/w4 | 正确 | 逐字节不变（w2 不可达 continue 既有丢弃不变） |
| 前轮探针 el/el_narrow/va/tern/er/r31 | 全绿 | 全绿 |
| pytest 7 套件 | 2F/282P/2XP（冻结对） | **2F/282P/2XP 零新增失败** |
| 全量 1556 闸门 | v5r89 基线 EQUAL 1132 | 见下节 |

## 全量 1556 闸门（v5r94 三分片对 v5r89 基线，offset 0/519/1038）

实测读数（`semantic_shard{0,1,2}_v5r94.json` vs `..._v5r89.json`，
`compare_v5r94.py`）：EQUAL **1132=1132**、REGRESSION **0**、IMPROVEMENT 0、
OTHER 仅 JS-IF-074 None→ERROR（产物加载抖动，同 v5r86/v5r88/v5r90/v5r93
轮已登记情形）。

## 诚实边界

- REAL46-003 仍 DIFFERENT（**R7×1** 在案）：v[51] `_c3_merge` IfRegion 结构
  反转（`if not sequences: return result` ⇔ `if sequences: … else: return`
  语义等价、字节码翻转）——独立子族登记未修。
- REAL46-004 use_args（Task 11）未在本轮范围（BoolOp 重叠层：条件块被前序
  BoolOpRegion 吸收，与本轮 break-角色 merge 守卫不同层）。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

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
