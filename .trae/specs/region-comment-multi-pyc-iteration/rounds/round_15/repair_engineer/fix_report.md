# R15 修复报告 — get_trading_schedule continue-sink 误并 else 分支

## 1. 修复概述

| 字段 | 值 |
|---|---|
| 轮次 | R15 (rcm-r15) |
| 目标 pyc | `IQCommon/trade_schedule.pyc` |
| 缺陷模式 | Pattern：IF_THEN_ELSE 中 then_succ=continue（JUMP_BACKWARD→循环头）时，NCPD 返回循环头，_collect_branch_blocks 将 post-if 语句误并入 else 分支 |
| 修复文件 | `core/cfg/region_analyzer.py`（`_identify_conditional_regions` 方法） |
| 修复方法 | continue-sink 检测（then_succ 末尾 JUMP_BACKWARD 目标=包围循环 header_block）→ merge=else_succ，创建 IF_THEN，post-if 语句归循环体 |
| 修复前 pyc match_rate | 50.00%（3/6，诊断阶段 partial） |
| 修复后 pyc match_rate | **66.67%** (4/6) — partial |
| 修复前 repro | get_trading_schedule 内层 for 循环被误并入 else 分支（drop 为 continue 后死代码） |
| 修复后 repro | **7 DEFECT-REPRO / 5 NO-DEFECT**（repro_08-10 验证 R15 修复，repro_11-12 回归控制） |
| 回归测试 | import 编译通过；R14 repros 结果不变（7 DEFECT / 5 NO-DEFECT）；tools.pyc 仍 83.33%（5/6） |

## 2. 缺陷定位

**函数**: `get_trading_schedule`（trade_schedule.pyc）

**源码结构**:
```python
def get_trading_schedule(trading_time, is_backtest=True):
    time_set = set()
    start_time_delta = int(is_backtest)
    for s, e in trading_time:        # outer FOR_ITER @64 (loop header)
        if s > 1200:                  # block 66, cond
            continue                  # block 86, JUMP_BACKWARD → 64
        for i in range(s + start_time_delta, e + 1):   # block 88 (post-if)
            time_set.add(divmod(i, 60))
    return time_set
```

**CFG 块拓扑**（diag_regions.py 输出）:
- block@66: if 条件（`POP_JUMP_FORWARD_IF_FALSE 88`），succ=[86, 88]
- block@86: `JUMP_BACKWARD 64`（continue），succ=[64]
- block@88: 内层 for setup（`range(...); GET_ITER`），succ=[132]
- block@132: 内层 `FOR_ITER 208`，succ=[134, 208]
- block@134: 内层循环体，succ=[132]
- block@208: `JUMP_BACKWARD 64`（外层回边），succ=[64]
- block@64: 外层 `FOR_ITER 210`（循环头）

**缺陷**: NCPD(then_succ=86, else_succ=88) = 64（循环头）。因 block 86（continue）的唯一后继是 64，且 else 分支（88→132→134→208）经 208 回边也到达 64，故 NCPD 返回 64。设 merge=64 后：
- then_blocks = _collect_branch_blocks(86, merge=64, stop={88,...}) = [86]（86→64，64 在 stop）
- else_blocks = _collect_branch_blocks(88, merge=64, stop={86,...}) = [88, 132, 134]（误收集内层 for 循环）

区域 dump（修复前）: `IF_THEN_ELSE entry=66 merge=64 then=[86] else=[88, 132, 134]`

内层 for 循环（blocks 88/132/134）被误并入 else 分支。AST 生成时 else 分支的 continue 之后的代码被作为死代码丢弃，`for i in range(...): time_set.add(...)` 完全丢失。decomp 产物仅含 `for s, e: if s>1200: continue`，无内层 for 循环。

**根因**: then_succ（block 86）以 `JUMP_BACKWARD`（continue 语义）终止，退出当前循环迭代、永不与对侧分支在循环内汇聚。NCPD 假设两分支最终汇聚，但 continue 分支经循环头回到循环顶、对侧分支经循环末尾回边也回到循环头，故 NCPD 返回循环头（64）而非真正的 if 合并点（88）。循环头不是 if 的合并点——if 的合并点是非退出分支（else_succ=88）的入口（post-if 语句）。算法 4 原则 2（每块唯一归属）要求 post-if 语句（block 88）归循环体，不由 else 分支生成。

## 3. 修复方案

在 `core/cfg/region_analyzer.py` 的 `_identify_conditional_regions` 方法中，紧随 R24-A 循环内 merge 修正之后、sink 回退之前，新增 continue-sink 检测（`_r15_*` 局部变量）：

1. **检测**: 当 `merge is not None` 且 `block`（if 条件块）位于某 LoopRegion 内时，取该 LoopRegion 的 `header_block`。检查 `then_succ` 末尾指令为 `JUMP_BACKWARD`/`JUMP_BACKWARD_NO_INTERRUPT` 且 `argval == header_block.start_offset`（continue 语义：跳回包围循环头）。
2. **elif 守卫**: 若 `else_succ` 是 elif 条件块（2 个条件后继 + 末尾为 FORWARD_CONDITIONAL_JUMP / SHORT_CIRCUIT_JUMP），不设 merge，交由 elif 链检测处理（如 `if b: continue / elif c: ...`）。
3. **修正**: 设 `merge = else_succ`，使 else_blocks 为空（entry==merge），创建 IF_THEN；block 88（post-if 语句）归循环体由父 LoopRegion 生成。

**算法 4 原则合规**:
- **自底向上归约**: ✓ 未改变归约顺序（仅在 merge 计算阶段修正合并点）
- **每块唯一归属**: ✓ post-if 语句（block 88）由父 LoopRegion 循环体唯一生成，不被 else 分支重复收集
- **嵌套即抽象节点**: ✓ 内层 FOR_LOOP（entry=132, blocks=[88,132,134]）作为抽象节点，其入口 88 作为外层 if 的 post-if 引用
- **入口引用语义**: ✓ 父 LoopRegion 通过循环体序列引用 IfRegion(66) + 内层 FOR_LOOP(132)

**安全性**: `LoopRegion.get_if_branch_boundary_stop`（region_analyzer.py:544）将 `header_block` 加入 `boundary_stop`。故 continue 目标（循环头 64）在 stop 集中，`_collect_branch_blocks` 不会沿 `JUMP_BACKWARD` 回边过度收集循环体（86→64 终止）。

**与既有 R2-C（BREAK 处理）的关系**: R2-C（L12498-12520）处理 then_succ 是循环 break 块（`BlockRole.BREAK/PURE_BREAK`）的场景——break 经 `JUMP_FORWARD` 退出循环，对侧分支是 post-if 语句。R15 是 R2-C 的对偶：处理 then_succ 是 continue 块（`JUMP_BACKWARD`→循环头）的场景——continue 经回边回到循环顶，对侧分支同样是 post-if 语句。两处判据互补，分别覆盖 break（前向跳转出循环）与 continue（后向跳转回循环头）。R2-C 依赖 `get_block_role`（此阶段 BREAK 角色已标注），R15 直接检查指令（CONTINUE 角色此阶段未标注，见 L12631-12632 注释）。

## 4. 回归测试结果

### 模块编译检查

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"
imports OK
```

### 区域 dump（修复后）

```
RegionType.FOR_LOOP entry=132 merge=None then=[] else=[] blocks=[88, 132, 134]
RegionType.FOR_LOOP entry=64 merge=None then=[] else=[210] blocks=[0, 64, 66, 86, 88, 132, 134, 208, 210]
RegionType.IF_THEN entry=66 merge=88 then=[86] else=[] blocks=[66, 86]
```

IF_THEN_ELSE → IF_THEN，else=[] 空，merge=88（post-if 内层 for 入口）。

### 最小复现实例验证

```
12 repros: 7 DEFECT-REPRO, 5 NO-DEFECT, 0 ERROR
  - DEFECT-REPRO (repro_01-07): is_stock/future BOOLOP-in-return 残留模式
  - CTRL NO-DEFECT (repro_08-12): R15 修复验证（continue-sink）+ R2-C 回归 + 纯控制
```

### 目标 pyc 验证

```
trade_schedule.pyc: 66.67% (4/6), decompile_status=partial
  fixed: get_trading_schedule (内层 for 循环恢复)
  residual: is_stock_trade_time_now, is_future_trade_time_now (BOOLOP-in-return)
```

### 跨轮回归验证

- R14 minimal_repros: 7 DEFECT-REPRO / 5 NO-DEFECT（与 R14 一致，无回归）
- R14 目标 pyc tools.pyc: 83.33% (5/6)（与 R14 一致，无回归）

## 5. 算法 4 原则合规

- **自底向上归约**: ✓ 未改变
- **每块唯一归属**: ✓ 强化（post-if 语句由父循环体唯一生成，避免 else 分支重复收集）
- **嵌套即抽象节点**: ✓ 未改变
- **入口引用语义**: ✓ 未改变

## 6. 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀: **0 新增**（`_r15_` 为轮次标记局部变量名）
- 硬编码深度上限: **0 新增**
- 跨区域启发式: **0 新增**（检测基于 `_find_enclosing_loop` + `header_block` 拓扑 + 指令检查，非实例特征）
- 后处理补丁: **0 新增**
- 针对特定 pyc 的硬编码绕过: **0 新增**

## 7. docstring 更新

`_identify_conditional_regions` 方法内新增 `[R15 fix]` 行内注释段落（region_analyzer.py:12452-12479），说明 continue-sink 检测的背景、触发条件、修复方式、与 R2-C 的对偶关系、安全性（boundary_stop 含循环头）、elif 守卫、算法 4 原则合规性。未修改 6 节 / 4 节模板主 docstring（修复为方法内靶向 merge 计算逻辑，非主方法签名变更），与 R14 惯例一致。

## 8. 残留问题

### 本轮新增残留

- **is_stock_trade_time_now / is_future_trade_time_now**: 2 mismatch（BOOLOP-in-return 模式：chained-compare + BoolOp OR 短路在 return 上下文被误分解为 if+pass）。根因较深（值上下文短路跳转被误作控制流分支），R15 continue-sink 修复未触及该路径，留待后续轮次。

### 累计残留（跨轮，未变）

- Pattern T3/T2/A2/B/C/E/F/M2/G3/R 等模式见各轮报告

### 下一轮建议

继续轮询下一个 pending pyc（按 path 字母序）。BOOLOP-in-return 残留根因较深，可作为后续独立轮次的修复目标（涉及 BoolOpRegion / ChainedCompareRegion 与 return-expression 上下文的交互）。
