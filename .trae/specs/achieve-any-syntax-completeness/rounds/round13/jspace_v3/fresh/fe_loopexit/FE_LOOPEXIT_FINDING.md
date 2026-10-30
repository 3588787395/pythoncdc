# for-else 后首语句被吸进循环体（REAL46-003 `_c3_mro` v[53]，rr-v5r91 登记诊断，rr-v5r92 修复）

状态：**已修复**（rr-v5r92：`region_analyzer.py` break 落点收窄精炼版 +
`region_ast_generator.py` R102 落点查找补 TernaryRegion，两文件只增不破）。
真实案例：G2c REAL46-003（stdlib `functools.py`）`_c3_mro`——for-else 之后
的 `abcs = list(abcs) if abcs else []`（三元赋值）被吸进循环体。修复后
v[53] **字节级 EQUAL**，REAL46-003 R7 差 **3→2**（剩 v[51]/v[55] 独立子族）。
与 Task 11 REAL46-004 `use_args`（BoolOp 重叠 + generator 发射三层）、
v[55] `_find_impl` 同属「循环退出汇合块归属」根因族——本形态（无 BoolOp
重叠）证明识别层+三元发射两点修复即可闭合，为该族后续轮次提供路径。

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

## 修复（rr-v5r92，两文件只增不破）

### ① 识别层（region_analyzer.py，break 落点 region_blocks.add 收窄·精炼版）

装配处 `elif not any(RETURN…): region_blocks.add(break_block)` 分支收窄——
break 落点**前向收尾**（末条指令非 JUMP_BACKWARD/POP_JUMP_BACKWARD_IF_*）
且可从 natural_exit 的正常后继链到达（BFS 不展开向后跳转收尾的块）时不收进
LoopRegion.blocks，由函数级序列在循环后发射；其余形态（向后跳转收尾的
外层回边重检块、需经向后跳转才能到达的落点、RETURN 落点）逐位维持旧行为（C3）。

**精炼原因（第一版全量闸门 14 回归实测）**：首版仅用「可从 natural_exit
到达」判据，把 m06_module_loops 的内层 for break 落点 B154（外层 while 的
回边重检块 `POP_JUMP_BACKWARD_IF_TRUE`，可从 for-else fall-through 直接
到达）误判为循环后顺序代码而收窄 → B154 所有权从 for 翻转到 while →
while 体发射走查把回边重检块当普通块发进循环体（`i < 3` 幻影语句）→
JS-IF/CONTINUE/WHILE/AUGASSIGN/AUGFORM 14 条 J 空间条目 EQUAL→DIFFERENT。
精炼补「落点前向收尾 + BFS 不穿向后跳转」两判据后 m06 逐字节恢复 HEAD，
14 条回归全部消除（v5r93 闸门复核）。

### ② 发射层（region_ast_generator.py，R102 落点查找补 TernaryRegion）

`_loop_generate_for` 的 break 落点 post-loop 处理中，结构化子区域查找元组
`(IfRegion, LoopRegion, TryExceptRegion)` 补 `TernaryRegion`：break 落点是
for-else 后三元赋值的条件块时（本族形态），落点归 TernaryRegion 所有；旧
查找不认 TernaryRegion → 落点落入普通块发射分支，`_generate_block_statements`
对条件块走通用 if/else 重建（值块 JUMP_FORWARD 跳向含 RETURN 的 merge 被判
为 return 臂 → `if abcs: return … else: return []` 幻影），随后函数级走查
再经 TernaryRegion 发射真尾段 → 双发射。补后落点经 `_generate_region` 走
三元路径单次发射并登记 generated/_generated_regions（C3：非三元落点维持
既有路径逐位不变）。

## 验证（实测读数）

| 检查 | 修复前 | 修复后 |
|---|---|---|
| fe1 repro（for-else + 尾随三元赋值，三调用形态对拍原全 DIFF） | 尾段吸进循环体、break 跳过尾段、提前 return | **co_code+异常表逐字节相等；三调用形态返回值逐项 SAME** |
| m3（fe_variants） | 同上 | **BYTE-EQUAL + 运行时 SAME**（4 调用形态） |
| m2/m4/m5（调用赋值/普通赋值/无 else 对照） | 正确 | 逐字节不变 |
| te_shapes s1/s3/s4/s5（rr-v5r90 族） | 正确 | 逐字节不变 |
| te_variants v1-v8 | 正确 | 逐字节不变 |
| w28 w1/w3/w4 | 正确 | 逐字节不变（w2 不可达 continue 既有丢弃不变） |
| m06_module_loops（R58-B 外层回边重检落点） | 正确 | 逐字节恢复 HEAD（精炼判据消除首版 14 回归） |
| REAL46-003 v[10]/v[53] | v[53] co_code 差 | **v[10]+v[53] 双双逐字节相等** |
| REAL46-003 权威 semantic_diff | R7×3 | **R7×2**（v[51] IfRegion 反转、v[55] _find_impl 独立子族登记；R1–R6 干净） |
| REAL46-003 singledispatch 行为 | — | 与 HEAD 逐场景一致（`f(1)` 失败为 v[55] 既有缺陷，非回归；FIXED/HEAD 全场景输出/异常逐项相同） |
| pytest 7 套件 | 2F/282P/2XP（冻结对） | **2F/282P/2XP 零新增失败** |
| el_variants/el_narrow/va/tern/er 前轮探针 | 全绿 | 全绿（MISSING none / 8 OK / 8 rc=0 / 5/5 / er 读数不变） |
| 全量 1556 闸门 | v5r89 基线 EQUAL 1132 | 见下节 |

## 全量 1556 闸门（v5r93 三分片对 v5r89 基线，offset 0/519/1038）

实测读数（`semantic_shard{0,1,2}_v5r93.json` vs `..._v5r89.json`，
`compare_v5r92.py`）：EQUAL **1132=1132**、总变化 **0**、REGRESSION **0**、
IMPROVEMENT 0、OTHER 仅 JS-IF-074 None→ERROR（产物加载抖动，同 v5r86/v5r88/
v5r90 轮已登记情形）。

**首版闸门对照（rr-v5r92 内部迭代，v5r92 三分片）**：EQUAL 1132→1118，
REGRESSION 14（JS-IF-059/082/084、JS-CONTINUE-009/028、JS-WHILE-024/041、
JS-AUGASSIGN-002/006/046/050、JS-AUGFORM-002/006/036，全部 R7 级）——定位为
m06 R58-B 落点所有权翻转（见①精炼原因），精炼后 v5r93 复跑归零。首版分片
产物与读数保留于 `semantic_shard{0,1,2}_v5r92.json` 作迭代证据。

## 诚实边界

- REAL46-003 仍 DIFFERENT（R7×2 在案）：v[51] `_c3_merge` IfRegion 结构反转
  （语义等价）、v[55] `_find_impl` 循环退出 merge 错构（与 Task 11 use_args
  同族，涉及 BoolOp/if 重叠层）——独立登记未修。
- REAL46-004 use_args（Task 11）未在本轮范围（需 BoolOp 重叠层同修）。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 候选修复历史（rr-v5r91 主候选首版，已回退）

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
