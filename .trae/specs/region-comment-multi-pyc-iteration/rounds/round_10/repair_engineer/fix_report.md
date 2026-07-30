# R10 修复报告 — Pattern Q（f-string FormattedValue 内 Constant 字符串引号冲突）

## 1. 修复目标

| 字段 | 值 |
|---|---|
| 轮次 | R10 (rcm-r10) |
| 目标 pyc | `site-packages/IQCommon/backtest/backtest.pyc`（R09 状态 `failed`，Pattern G2 已修复但暴露 latent Pattern Q） |
| 缺陷模式 | Pattern Q（f-string 定界符引号选择与 FormattedValue 内 Constant 字符串引号冲突） |
| 修复文件 | `core/cfg/code_generator.py` |
| 修复方法 | `_generate_joined_str`（AST 版本，L4227-4295）+ `_generate_joined_str_from_dict`（dict 版本，L4122-4190）+ FormattedValue 顶层分支（L3187-3195） |
| 修复前 repro | 7 DEFECT-REPRO（repro 01-03, 05-08） |
| 修复后 repro | 0 DEFECT-REPRO（10/10 OK） |
| 回归测试 | 1 failed, 154 passed, 19 errors（与 R09 基线**完全一致**，零回归） |

## 2. 根因分析

- **缺陷层**：代码生成层 `core/cfg/code_generator.py`
- **缺陷方法**：`_generate_joined_str`（AST 版本）+ `_generate_joined_str_from_dict`（dict 版本）
- **根因**：定界符选择逻辑扫描**整个 content**（字面片段 + 表达式片段混合），当 content 同时含 `'`（来自 FormattedValue 的 `'1'`/`'tick'`）和 `"`（来自字面片段 `"plugins"`）时落入 else 分支选**单引号定界** `f'...'`。但 FormattedValue 内的 Constant 字符串经 `repr()` 渲染为单引号（`'1'`），与外层单引号定界符冲突 → `SyntaxError: f-string: expecting '}'`。

### Python 3.11 f-string 语法约束（关键事实）

- f-string 表达式片段（`{...}` 内）**不允许出现定界符引号**（未转义）
- f-string 表达式片段**不允许反斜杠转义**（不能 `\'`）
- 因此定界符选择必须**避开**所有 FormattedValue 表达式片段中出现的引号字符

### backtest.pyc 实证

`handle_backtest_build` 的 `user_code` f-string（25 段）含三个冲突 FormattedValue：
1. `{'1'!s}` — `ASTFormattedValue(conv=1, inner=ASTConstant('1'))`（索引 13）
2. `{frequency != 'tick'!s}` — `ASTFormattedValue(conv=1, inner=ASTCompare)`（索引 15）
3. `{enable_debug == 'true'!s}` — `ASTFormattedValue(conv=1, inner=ASTCompare)`（索引 19）

字面片段含 `"`（JSON 模板 `"plugins": {` 等）。旧逻辑：content 同时含 `'` 和 `"` → 单引号定界 → `'1'`/`'tick'`/`'true'` 冲突 → SyntaxError line 69。

## 3. 修复方案

分两遍渲染（算法驱动，非补丁），覆盖三处定界符选择：

### 修改点 1：`_generate_joined_str`（AST 版本，L4227-4295）

```python
# 第一遍：分类渲染。literal 项存原始字面文本（未转义），expr 项存已渲染
# 的表达式源码（含 {} 包裹）。
rendered = []  # list of (is_literal, text)
for value in node._values:
    if isinstance(value, str):
        rendered.append((True, value))
    elif isinstance(value, ASTConstant) and isinstance(value.value, str):
        rendered.append((True, value.value))
    elif isinstance(value, ASTFormattedValue):
        rendered.append((False, self._generate_formatted_value(value)))
    else:
        rendered.append((False, self._generate_expression(value, 0)))

# 第二遍：确定定界符。扫描表达式片段中出现的引号字符。
fv_has_single = any("'" in text for is_lit, text in rendered if not is_lit)
fv_has_double = any('"' in text for is_lit, text in rendered if not is_lit)
if not fv_has_single:
    delim = "'"
elif not fv_has_double:
    delim = '"'
else:
    delim = "'''"  # 三引号回退（罕见边界）

# 第三遍：按定界符转义字面片段。仅转义定界符引号 + 换行 + 花括号。
parts = []
for is_lit, text in rendered:
    if is_lit:
        esc = text.replace(delim, '\\' + delim).replace('\n', '\\n').replace('\r', '\\r')
        esc = esc.replace('{', '{{').replace('}', '}}')
        parts.append(esc)
    else:
        parts.append(text)
return 'f' + delim + ''.join(parts) + delim
```

### 修改点 2：`_generate_joined_str_from_dict`（dict 版本，L4122-4190）

同上算法（dict 节点路径）。

### 修改点 3：FormattedValue 顶层分支（L3187-3195）

```python
_fv_inner = self._generate_formatted_value_from_dict(node)
if "'" not in _fv_inner:
    return f"f'{_fv_inner}'"
elif '"' not in _fv_inner:
    return f'f"{_fv_inner}"'
else:
    return f"f'''{_fv_inner}'''"
```

### 算法依据

区域归约算法原则 2「每块唯一归属」：
- **字面片段**归字面层 — 可转义（按定界符引号转义）、可重新选择引号
- **表达式片段**归表达式层 — 不可转义、不可含定界符引号（Python 3.11 约束）
- **定界符选择由表达式片段内容决定**：选择未出现在任何表达式片段中的引号，确保表达式片段不变即可放入 f-string

### 非补丁声明

- 守卫基于 Python 3.11 f-string 语法约束（表达式片段不允许定界符引号、不允许反斜杠），非硬编码 offset / 非跨区域启发式 / 非后处理
- 字面片段转义随定界符动态调整（不总是 `'`），修正了旧逻辑在双引号定界时字面 `'` 误转义为 `\'` 的 latent bug
- 无表达式片段引号时保留原行为（用 `'` 定界）

## 4. 算法依据（定界符选择如何对齐区域归约算法）

4 原则合规：

- **自底向上归约**：✓ 未改变（修复在生成层最终渲染阶段，不影响归约顺序）
- **每块唯一归属**：✓ **强化** — 字面片段与表达式片段分别归属不同层（字面层可转义、表达式层不可转义）。定界符选择由表达式片段内容决定，字面片段按定界符动态转义。旧逻辑把两层混合扫描，导致字面引号干扰定界符选择。
- **嵌套即抽象节点**：✓ 未改变
- **入口引用语义**：✓ 未改变

## 5. 注释更新清单

| 方法 | 文件:行 | 更新内容 |
|---|---|---|
| `_generate_joined_str` | `code_generator.py:4227-4249` | docstring 重写，追加 `[R10 fix]` Pattern Q 段：说明 Python 3.11 f-string 表达式片段引号约束、旧逻辑缺陷（扫描整个 content 选定界符）、修复算法（分两遍渲染 + 表达式片段引号扫描 + 定界符动态选择 + 字面片段按定界符转义）、算法依据（原则 2）、非补丁声明。保留 [R07 fix] 花括号转义。 |
| `_generate_joined_str_from_dict` | `code_generator.py:4130-4141` | docstring 追加 `[R10 fix]` Pattern Q 段（同上，dict 版本）。保留 [R07 fix] 段。 |
| FormattedValue 顶层分支 | `code_generator.py:3188-3190` | 行内注释追加 `[R10 fix]` — 说明定界符选择基于表达式片段引号扫描。 |

## 6. 回归结果

### 最小复现实例（10 个）

| # | 实例 | pre-fix | post-fix | 变化 |
|---|---|---|---|---|
| 01 | fstring_const_str_conversion | DEFECT (SyntaxError) | OK | **修复** |
| 02 | fstring_const_str_no_conversion | DEFECT (SyntaxError) | OK | **修复** |
| 03 | fstring_const_str_double_quotes | DEFECT (SyntaxError) | OK | **修复** |
| 04 | fstring_const_num_conversion (CTRL) | OK | OK | 不变 |
| 05 | fstring_mixed_const_var | DEFECT (SyntaxError) | OK | **修复** |
| 06 | fstring_const_str_in_double_quotes | DEFECT (SyntaxError) | OK | **修复** |
| 07 | fstring_nested_quotes (Compare) | DEFECT (SyntaxError) | OK | **修复** |
| 08 | fstring_const_str_repr (Call) | DEFECT (SyntaxError) | OK | **修复** |
| 09 | ctrl_fstring_var_conversion (CTRL) | OK | OK | 不变 |
| 10 | ctrl_fstring_num_literal (CTRL) | OK | OK | 不变 |

- **DEFECT-REPRO 计数**：pre-fix 7 → post-fix 0
- **CTRL 组（04, 09, 10）全部 OK**：证明修复不影响无字符串字面量的 FormattedValue

### 目标 pyc 验证（backtest.pyc）

| 指标 | pre-fix (R09) | post-fix (R10) | 变化 |
|---|---|---|---|
| decompile_status | failed | **partial** | **解锁** |
| backtestOK.py 编译 | SyntaxError line 69 | **COMPILE OK** | **修复** |
| handle_backtest_build 字节码 | 不可比（SyntaxError） | **100% 一致** | **修复** |
| <module> 字节码 | 不可比 | 8 true_diffs（NOP/LOAD_CONST 顺序） | 残留（独立模式） |
| bytecode_match_rate | 0.0 | **0.50** (1/2) | **+50%** |

- Pattern Q（f-string 引号冲突）**已修复**：backtestOK.py 编译通过，`handle_backtest_build` 函数字节码 100% 一致。
- `<module>` 残留 8 true_diffs（NOP padding / LOAD_CONST 顺序差异），独立模式，非本轮 scope。

### 回归 pytest（与 R09 同 scope: testqouter/）

```
python -m pytest testqouter/ --timeout=90 --tb=no -q --continue-on-collection-errors
1 failed, 154 passed, 147 warnings, 19 errors in 41.15s
```

| 指标 | R09 基线 | R10 post-fix | 变化 |
|---|---|---|---|
| failed | 1 | 1 | 持平（test_r2q_10_with_open_read.py FileNotFoundError，预存在） |
| passed | 154 | **154** | **持平（零回归）** |
| errors | 19 | 19 | 持平（均为预存在测试基建问题） |

**R10 定界符选择重构零增量回归**：修复前后 pytest 计数完全一致（1 failed, 154 passed, 19 errors），证明新逻辑不破坏既有行为。

### 模块编译检查

```
python -c "import core.cfg.code_generator; import core.cfg.region_ast_generator"
IMPORT OK
```

## 7. 残留不一致数

### 本轮残留

1. **backtest.pyc `<module>` 8 true_diffs**：`<module>` code object 的 NOP padding / LOAD_CONST 顺序差异（orig 83 instrs vs dec 81 instrs）。原 pyc 在函数定义前有 2 条 NOP（对齐填充），反编译产物缺失。独立模式（Pattern R：模块级 NOP padding），非本轮 scope。

### 跨轮残留（不变）

- Pattern T3 残留（graph.pyc 4 mismatch 函数）
- Pattern T2（R07，except body drop on return-const）
- repro_05 trailing-return（R07）
- repro_12 Pattern G3（R09，链式比较跨块误判）
- Pattern A2 / B / C / E / F / M2（跨轮）

## 8. 累计成功率变化（R09 → R10）

| 指标 | R09（committed pyc_index.json） | R10 post-fix | 变化 |
|---|---|---|---|
| 累计成功率 | 67.05% | **67.28%** | **+0.23%**（单调递增） |
| verified pyc | 30 | 30 | 持平 |
| ok pyc | 22 | 22 | 持平 |
| partial pyc | 6 | **7** | +1（backtest failed→partial） |
| failed pyc | 2 | **1** | -1（backtest 解锁） |
| backtest.pyc | failed (0%, Pattern Q SyntaxError) | **partial (50%, handle_backtest_build 100% 一致)** | **解锁** |

> 注：R09 fix_report 记录的 "70.90%" 与 R09 committed pyc_index.json 实际计算结果（67.05%）不一致（R09 报告使用不同 index 快照或计算口径）。本轮以 committed pyc_index.json 实测为准：R09 实际 67.05% → R10 67.28%，单调递增，满足 G13。

- **成功率提升原因**：backtest.pyc 的 Pattern Q（f-string 引号冲突）已修复，backtestOK.py 编译通过，`handle_backtest_build` 函数字节码 100% 一致。backtest.pyc 状态 failed→partial（0%→50%），累计成功率 +0.23%。
- **结构进展**：R10 修复了 Pattern Q（code_generator.py f-string 定界符选择），7/7 DEFECT-REPRO 修复，零回归。backtest.pyc 从 failed 解锁为 partial，为后续修复 `<module>` NOP padding 残留铺路。
- **下一轮建议**：修复 `<module>` NOP padding 残留可使 backtest.pyc 升级为 ok；继续处理跨轮残留 Pattern T3/T2/A2/B/C/E/F/M2/G3。
