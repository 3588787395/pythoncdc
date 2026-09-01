# R12 修复工程师报告 — Pattern A2（try-body if/return collapse，异常边切分）

## 1. 修复目标

修复 Pattern A2：try-body 内 `if cond: return x / else: return y` 被 CFG 异常边切分为独立块后，区域分析器误判为三元值分支，导致 return 语句被错误重建为 POP_TOP（表达式语句丢弃返回值）。

- **目标文件**: `core/cfg/region_analyzer.py` + `core/cfg/region_ast_generator.py`
- **最高 count 子模式**: A2a（simple condition + try-body if collapse），7/13 repros
- **根因共通**: A2a/A2b/A2c 共享同一根因 — try-body 内异常边将 `LOAD + RETURN_VALUE` 切开，区域分析误判 LOAD 块为三元值分支

## 2. 缺陷根因分析

### 2a. 区域分析层根因（region_analyzer.py）

`_is_return_statement_body` 方法判定一个块是否为 return 语句体时，检查块末尾是否为 `RETURN_VALUE`/`RETURN_CONST`。但在 try-body 内，`LOAD_FAST a` + `RETURN_VALUE` 被异常边切分为两个块：
- **LOAD_FAST 块**: 有异常边到 handler，末尾为 LOAD_FAST（非 RETURN_VALUE）
- **RETURN_VALUE 块**: 无异常边，末尾为 RETURN_VALUE

原逻辑：LOAD_FAST 块末尾非 RETURN_VALUE → 误判为三元值分支的条件块 → return 语句被重建为 `POP_TOP`（丢弃返回值）。

### 2b. 区域 AST 生成层根因（region_ast_generator.py）

`_generate_ternary_assign` 的 `_non_noise_remaining` 分支处理 merge_block 后续指令。当 merge_block 含 `STORE_FAST a + LOAD_FAST a`（被异常边切开），后继块为 `RETURN_VALUE` 时，原逻辑将 LOAD_FAST a 作为独立 Expr 语句发射，而非与 RETURN_VALUE 合并为 Return 语句。

## 3. 修复方案

### 3a. region_analyzer.py — 异常边切分检测（`_is_return_statement_body`）

在 `_is_return_statement_body` 的 `last.opname not in ('RETURN_VALUE', 'RETURN_CONST')` 分支中，追加结构性判据：

```python
# [R12 fix] Pattern A2: try-body exception edge splitting.
_exc_succs = getattr(blk, 'exception_successors', set())
if _exc_succs:
    _normal_succs = [s for s in blk.successors if s not in _exc_succs]
    if len(_normal_succs) == 1:
        _succ_eff = [i for i in _normal_succs[0].instructions
                     if i.opname not in NOISE_OPS]
        if (_succ_eff and _succ_eff[-1].opname in ('RETURN_VALUE', 'RETURN_CONST')
                and not any(i.opname == 'POP_TOP' for i in _succ_eff[:-1])):
            return True
```

**判据**：块有异常边 + 唯一正常后继块末尾为 RETURN_VALUE/RETURN_CONST + 无 POP_TOP（排除表达式语句）→ 判定为 return 语句体。

### 3b. region_ast_generator.py — try-body ternary assign + return 合并（`_generate_ternary_assign`）

在 `_non_noise_remaining` 分支中，追加 return 合并逻辑：

```python
# [R12 fix] Pattern A2: try-body ternary assign + return.
_r12_exc_succs = getattr(region.merge_block, 'exception_successors', set())
_r12_normal_succs = [s for s in region.merge_block.successors
                     if s not in _r12_exc_succs]
if (len(_r12_normal_succs) == 1
        and not any(i.opname == 'POP_TOP' for i in _non_noise_remaining)):
    _r12_succ_eff = [i for i in _r12_normal_succs[0].instructions
                     if i.opname not in NOISE_OPS]
    if (_r12_succ_eff and _r12_succ_eff[-1].opname == 'RETURN_VALUE'
            and not any(i.opname == 'POP_TOP' for i in _r12_succ_eff[:-1])):
        # 合并 _non_noise_remaining + succ_pre_return 为 Return 语句
        _r12_ret_instrs = list(_non_noise_remaining) + _r12_succ_pre
        _r12_ret_expr = self.expr_reconstructor.reconstruct(_r12_ret_instrs)
        if _r12_ret_expr is not None:
            results.append({'type': 'Return', 'value': _r12_ret_expr})
            self.generated_blocks.add(_r12_normal_succs[0])
            _r12_ret_handled = True
```

**判据**：merge_block 有异常边 + 唯一正常后继块末尾为 RETURN_VALUE + 无 POP_TOP → 将 merge_block 后续指令 + 后继块 return 前指令合并为 Return 语句。

## 4. 算法 4 原则合规

| 原则 | 合规 | 说明 |
|---|---|---|
| 自底向上归约 | ✓ | return 语句体判定在块级归约阶段，先识别异常边切分的块对，再归约为 return 语句 |
| 每块唯一归属 | ✓ | LOAD_FAST 块归 return 语句体（非三元值分支条件块）；RETURN_VALUE 后继块通过 `generated_blocks.add` 标记归属 |
| 嵌套即抽象节点 | ✓ | try-body 内的 `LOAD + RETURN_VALUE` 作为整体判定为 return 语句，不展开为独立表达式 |
| 入口引用语义 | ✓ | 父 Return 节点通过 value 子节点引用 LOAD_FAST 表达式，保持入口引用链 |

**无反模式**：0 新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀。`_r12_` 前缀为轮次标记变量名，非反模式。

## 5. 注释更新清单

| 文件 | 方法 | 更新内容 |
|---|---|---|
| `region_analyzer.py` | `_is_return_statement_body` | 追加 `[R12 fix]` 注释段：说明 Pattern A2 异常边切分判据、触发条件、结构性依据 |
| `region_ast_generator.py` | `_generate_ternary_assign` | 追加 `[R12 fix]` 注释段：说明 try-body ternary assign + return 合并逻辑、每块唯一归属、结构性判据 |

注：两处修改均为辅助方法内的行内注释（`[R12 fix]` 标记），非 `_identify_*_regions`（6 节）或 `_generate_*`（4 节）主方法 docstring 更新。本轮未修改 `_identify_*_regions` 主方法签名/docstring。

## 6. 回归测试结果

| 指标 | R11 基线 | R12 末 | 变化 |
|---|---|---|---|
| pytest testqouter/round1/ | 1 failed, 112 passed, 15 errors | 1 failed, 112 passed, 15 errors | 零回归 |
| `detail_test.py` collection error | 预存在（test_b05_expr_stmt.pyc） | 预存在（不变） | 非新增 |
| 反模式自检 | 0 新增 | 0 新增 | 通过 |
| 模块编译 | OK | OK | 通过 |

## 7. 残留不一致

- **klinedata.pyc**: 21 个不一致函数（match rate 持平 53.33%）。Pattern A2 修复减少了 try-body 内部 true_diffs，但 21 函数的 first_diff 均为非 A2 模式（B:9 / E:7 / R:3 / C:2 / C2:1），无法使任何函数达到 100% 一致。
- **跨轮残留**: backtest.pyc `<module>` Pattern R / main.pyc `run` 独立模式 / graph.pyc 4 mismatch 函数 不变。

## 8. 结论

- Pattern A2 修复正确：13 个最小复现实例全部通过（7 DEFECT-REPRO → 0），零回归。
- 修复基于 CFG 异常边拓扑结构性判据，非实例特征启发式，符合算法 4 原则。
- klinedata.pyc match rate 持平：Pattern A2 缺陷被前置 B/E/R/C/C2 缺陷掩盖。
- 累计成功率持平 67.05%（≥ R11，满足单调递增约束）。
- 后续优先修复 Pattern B（scope，9 函数）或 Pattern E（jump renumber，7 函数）以提升 klinedata.pyc match rate。
