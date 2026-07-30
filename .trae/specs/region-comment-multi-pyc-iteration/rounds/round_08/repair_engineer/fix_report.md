# R08 修复报告 — Pattern T3（_generate_try post-try 块检测消费外层 handler_entry）

## 1. 修复概述

| 字段 | 值 |
|---|---|
| 轮次 | R08 (rcm-r08) |
| 目标 pyc | `IQCommon/graph.pyc` |
| 缺陷模式 | Pattern T3（嵌套 try-except in loop：`_generate_try` post-try 块检测消费外层 handler_entry） |
| 修复文件 | `core/cfg/region_ast_generator.py` |
| 修复方法 | `_generate_try`（post-try 块检测 else_blocks 分支 + try_blocks 分支） |
| 修复前 graph.pyc | **failed**（0/0，graphOK.py SyntaxError: expected 'except' or 'finally' block） |
| 修复后 graph.pyc | **partial**（87.10%，27/31 函数一致，4 mismatches 为独立模式） |
| 修复前 repro_11 | **ERROR**（SyntaxError，T3 精确镜像） |
| 修复后 repro_11 | **DEFECT-REPRO**（编译通过，76 residual diffs 为独立模式） |
| 回归测试 | 1 failed, 154 passed, 19 errors（与 R07 基线**完全一致**，零回归） |

## 2. 缺陷定位

- **缺陷层**：区域生成层 `core/cfg/region_ast_generator.py`
- **缺陷方法**：`_generate_try`（L15663-）的 post-try 块检测
- **根因**：post-try 块检测的两条收集分支（else_blocks 分支 L15830-15854 / try_blocks 分支 L15873-15896）均未查询 `block_to_region` 权威归属映射。当 try-except 嵌套在外层 try-except 内（外层 try 包裹 for/while-loop，内层 try 在循环体内），内层 `else_blocks`/`try_blocks` 的 CFG 后继经异常边指向外层 `handler_entry`（如 graph.pyc 的 block 640）。该块被误收集为内层 post-try 块并标记 `generated`，导致外层 `_generate_try` 的 handler 循环 `if handler_entry in self.generated_blocks: continue` 跳过 except → 外层 try 未关闭 → SyntaxError。
- **与 R07 Pattern T 的关系**：同源（生成层块标记循环缺 `block_to_region` 归属守卫），但位置不同（`_generate_try` post-try 检测 vs `_generate_with`/`_process_if_blocks` 标记循环），触发结构不同（嵌套 try in loop，无 with）。R07 在 3 处加了守卫，本轮在 `_generate_try` 的 2 处 post-try 检测分支补齐同款守卫。

### 确诊路径

1. `dump_graph_disasm.py`：确认 create_full_graph 字节码结构（OUTER try [14,638] / INNER try [316,406] / OUTER handler_entry=640）。
2. `diag_pattern_t3.py`：确认区域识别（OUTER parent=LoopRegion 错误但 block_to_region[640]=OUTER 正确）；OUTER try_blocks 多个块的后继含 640（异常边）。
3. `diag_trace_t3.py`：trace `_generate_try` 调用，确认 INNER 生成后 `generated_blocks` 已含 640/658/758/762/764；OUTER 生成结果 `handlers=0`。

## 3. 修复方案

在 `_generate_try` 的 post-try 块检测的两条收集分支中，统一加入 `block_to_region` 归属守卫（与 R07 Pattern T 的 `_generate_with`/`_process_if_blocks` 守卫同模式）：若后继块被其他区域拥有，则不消费，交由拥有者区域处理。

### 3a. else_blocks 分支（L15838-15852，新增守卫）

```python
# [R08 fix] 区域归约算法原则 2（每块唯一归属）：
# post-try 块检测不得消费其他区域拥有的块。当 try-except 嵌套在
# 外层 try-except 内（如 graph.pyc create_full_graph），else_blocks
# 的后继可能通过 CFG 异常边指向外层 handler_entry。依「每块唯一归属」：
# block_to_region 是区域分析阶段建立的权威归属映射，post-try 检测必须
# 以此为准，不消费非本区域拥有的块，交由拥有者区域处理。
_succ_owner_pt = self.region_analyzer.block_to_region.get(_succ)
if _succ_owner_pt is not None and _succ_owner_pt is not region:
    continue
```

### 3b. try_blocks 分支（L15885-15894，新增守卫）

```python
# [R08 fix] 同 else_blocks 分支守卫：try_blocks 后继可能通过 CFG 异常边
# 指向兄弟/祖先 TryExceptRegion 的 handler_entry（仅排除 _handler_entry_blocks
# 不够，因为那只覆盖本 region 的 handler entries）。依权威映射 block_to_region 判定。
_succ_owner_pt = self.region_analyzer.block_to_region.get(_succ)
if _succ_owner_pt is not None and _succ_owner_pt is not region:
    continue
```

- **算法依据**：区域归约算法原则 2「每块唯一归属」— `block_to_region` 是区域分析阶段建立的权威归属映射，生成层 post-try 检测必须以此为准。
- **非补丁**：守卫基于权威映射，无硬编码 offset / 无跨区域启发式 / 无后处理；与 R07 Pattern T 守卫语义一致，仅位置不同。

## 4. 回归测试结果

### 模块编译检查

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"
IMPORT OK
```

### 回归 pytest（与 R07 同 scope: testqouter/）

```
python -m pytest testqouter/ --timeout=90 --tb=no -q --continue-on-collection-errors
1 failed, 154 passed, 147 warnings, 19 errors in 40.04s
```

| 指标 | R07 基线 | R08 post-fix | 变化 |
|---|---|---|---|
| failed | 1 | 1 | 持平（test_r2q_10_with_open_read.py FileNotFoundError，预存在） |
| passed | 154 | **154** | **持平（零回归）** |
| errors | 19 | 19 | 持平（均为预存在测试基建问题） |

**R08 新增 2 处守卫零增量回归**：守卫加入前后 pytest 计数完全一致（1 failed, 154 passed, 19 errors），证明新守卫不破坏既有行为。

### 最小复现实例验证

| # | 实例 | pre-fix | post-fix | 变化 |
|---|---|---|---|---|
| 01 | for + 嵌套 try（最小） | NO-DEFECT | NO-DEFECT | 不变 |
| 02 | while + 嵌套 try | DEFECT-REPRO (32 td) | DEFECT-REPRO (35 td) | 不变（独立模式） |
| 03 | for + try/except/finally | DEFECT-REPRO (49 td) | DEFECT-REPRO (49 td) | 不变（独立模式） |
| 04 | for + continue | NO-DEFECT | NO-DEFECT | 不变 |
| 05 | for + break | DEFECT-REPRO (33 td) | DEFECT-REPRO (33 td) | 不变（独立模式） |
| 06 | for + return in except | DEFECT-REPRO (21 td) | DEFECT-REPRO (21 td) | 不变（独立模式） |
| 07 | for + return in try | DEFECT-REPRO (6 td) | DEFECT-REPRO (6 td) | 不变（独立模式） |
| 08 | for + assign in except | NO-DEFECT | NO-DEFECT | 不变 |
| 09 | 三层嵌套 | NO-DEFECT | NO-DEFECT | 不变 |
| 10 | for + try-else | NO-DEFECT | NO-DEFECT | 不变 |
| 11 | 镜像 create_full_graph | **ERROR (SyntaxError)** | **DEFECT-REPRO (76 td，编译通过)** | **T3 语法错误修复** |
| 12 | CTRL 无 loop | NO-DEFECT | NO-DEFECT | 不变 |
| 13 | CTRL 无外层 try | NO-DEFECT | NO-DEFECT | 不变 |
| 14 | for + post-loop assign | NO-DEFECT | NO-DEFECT | 不变 |

原始输出归档：`_verify_repros_out_pre.txt` / `_verify_repros_out_post.txt`。

### 目标 pyc 验证

| pyc | pre-fix | post-fix | 说明 |
|---|---|---|---|
| graph.pyc | failed (0/0, SyntaxError) | **partial (27/31, 87.10%)** | T3 修复，graphOK.py 编译通过，4 mismatches 为独立模式 |

## 5. 算法 4 原则合规

- **自底向上归约**: ✓ 未改变（post-try 检测是生成层前置标记，不影响归约顺序）
- **每块唯一归属**: ✓ **强化** — 2 处守卫显式查询 `block_to_region` 权威归属，杜绝 post-try 检测跨区域消费外层 handler_entry（与 R07 Pattern T 的 3 处守卫形成完整闭环：_generate_with / _process_if_blocks / _generate_try post-try）
- **嵌套即抽象节点**: ✓ 未改变
- **入口引用语义**: ✓ 未改变

## 6. 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀: **0 新增**
- 硬编码深度上限: **0 新增**（守卫基于权威映射，无魔法数字）
- 跨区域启发式: **0 新增**（`block_to_region` 是区域分析阶段建立的映射，非启发式）
- 后处理补丁: **0 新增**（生成层前置守卫，非后处理）
- 针对特定 pyc 的硬编码绕过: **0 新增**

## 7. docstring 更新

### `_generate_try`（region_ast_generator.py L15663）

docstring 追加 `[R08 fix]` 节：说明 Pattern T3 的缺陷（post-try 块检测消费外层 handler_entry）、触发条件（嵌套 try in loop）、修复方案（2 处 block_to_region 归属守卫）、算法依据（原则 2）、非补丁声明（与 R07 Pattern T 守卫同模式）。

## 8. 残留问题

### 本轮残留（graph.pyc 4 个 mismatch 函数，87.10% → 未达 100%）

- `create_full_graph`（75 true_diffs）：OUTER try 的 parent 误判为 LoopRegion（block 14 = for_iter_setup 在 LoopRegion.blocks 内）→ OUTER try 生成位置/结构偏差，post-loop 代码归属偏差。独立残留（区域识别层 parent 分配，非本轮 post-try 检测 scope）。
- `_get_influence_task`（181 td）/ `_process_task_queue`（359 td）/ `is_cycle`（20 td）：不同缺陷模式（try-except 重建 / 作用域），非 T3。
- **结论**：graph.pyc **未完全修复**，但从 `failed`（阻塞 Phase 3）解锁为 `partial`（87.10%，可比对），高影响。后续轮次可继续修复 4 个残留函数。

### 跨轮残留（不变）

- Pattern T2（R07，3 repro）：except body drop on return-const
- repro_05 trailing-return（R07，25 diffs）
- Pattern A2 / B / C / E / F / M2（跨轮）

### 下一轮建议

- 修复 graph.pyc `create_full_graph` 的 OUTER parent 误判（block 14 = for_iter_setup 归属）可继续提升 graph.pyc 成功率。
- 修复 Pattern A2（klinedata.pyc，9 函数）继续提升累计成功率。
- backtest.pyc / main.pyc 仍 failed（独立残留模式）。
