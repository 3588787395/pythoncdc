# R10 测试工程师报告 — Pattern Q（f-string FormattedValue 内 Constant 字符串引号冲突）

## 1. 目标 pyc 与轮次

| 字段 | 值 |
|---|---|
| 轮次 | R10 (rcm-r10) |
| 目标 pyc | `site-packages/IQCommon/backtest/backtest.pyc`（R09 状态 `failed`，Pattern G2 已修复但暴露 latent Pattern Q） |
| 缺陷模式 | Pattern Q（f-string 定界符引号选择与 FormattedValue 内 Constant 字符串引号冲突） |
| 修复层 | 代码生成层 `core/cfg/code_generator.py` |
| 累计成功率（R09 末） | 70.90% |

## 2. 反编译产物实证

### 2a. backtest.pyc `handle_backtest_build` line 69（实际缺陷段）

完整 f-string（25 段，R09 已修复 COMPARE_OP 截断）经 `py_compile.compile(..., quiet=0)` 重编触发：

```
SyntaxError: f-string: expecting '}'
```

缺陷段（f-string 单引号定界，FormattedValue 内 Constant 字符串单引号冲突）：

```python
user_code = f'...{{\n        "enabled": {'1'!s},\n...        "enabled": {frequency != 'tick'!s},\n...        "enabled": {enable_debug == 'true'!s},\n...'
```

三个冲突 FormattedValue：
1. `{'1'!s}` — `ASTFormattedValue(conv=1, inner=ASTConstant('1'))`（索引 13）
2. `{frequency != 'tick'!s}` — `ASTFormattedValue(conv=1, inner=ASTCompare(..., 'tick'))`（索引 15）
3. `{enable_debug == 'true'!s}` — `ASTFormattedValue(conv=1, inner=ASTCompare(..., 'true'))`（索引 19）

### 2b. f-string AST 结构（25 段，trace 实证）

通过 monkey-patch `_generate_joined_str` 确认：
- **AST 版本**（`_generate_joined_str`）被调用（非 dict 版本）
- 25 个 values：13 个 `ASTConstant`（字面片段）+ 12 个 `ASTFormattedValue`
- 字面片段含 `"`（如 `"plugins": {`、`"enabled": `）—— 来自 JSON 模板
- FormattedValue 内表达式经 `_generate_expression` → `repr(node.value)`（L2109）渲染，所有字符串 Constant 一律单引号

## 3. 根因分析

### 缺陷层
`core/cfg/code_generator.py` `_generate_joined_str`（L4227-4261）

### 缺陷机制

1. **Constant 字符串渲染**（L2108-2109）：
   ```python
   elif isinstance(node, ASTConstant):
       return repr(node.value)
   ```
   `repr('1')` → `"'1'"`（单引号）；`repr('tick')` → `"'tick'"`（单引号）。所有字符串 Constant 一律单引号。

2. **f-string 字面片段转义**（L4236-4247）：
   ```python
   escaped = value.replace("'", "\\'").replace('\n', '\\n').replace('\r', '\\r')
   escaped = escaped.replace('{', '{{').replace('}', '}}')
   ```
   字面片段的 `'` 转义为 `\\'`，但 `"` **不转义**（原样保留）。

3. **f-string 定界符选择**（L4256-4261）：
   ```python
   content = ''.join(parts)
   if "'" in content and '"' not in content:
       return f'f"{content}"'
   else:
       return f"f'{content}'"
   ```
   - 当 content 同时含 `'`（来自 FormattedValue 的 `'1'`/`'tick'`）和 `"`（来自字面片段 `"plugins"`）→ 落入 `else` 分支 → 单引号定界 `f'...'`
   - FormattedValue 内未转义的单引号 `'1'` 与外层单引号定界符冲突 → `SyntaxError: f-string: expecting '}'`

### Python 3.11 f-string 语法约束

- f-string 表达式片段（`{...}` 内）**不允许出现定界符引号**（未转义）
- f-string 表达式片段**不允许反斜杠转义**（不能 `\'`）
- 因此定界符选择必须**避开**所有 FormattedValue 表达式片段中出现的引号字符

## 4. 最小复现实例（10 个，7 DEFECT-REPRO / 3 NO-DEFECT）

| # | 实例 | 源码 | pre-fix |
|---|---|---|---|
| 01 | fstring_const_str_conversion | `x = f'"k": {"1"!s}'` | **DEFECT**（SyntaxError） |
| 02 | fstring_const_str_no_conversion | `x = f'"k": {"1"}'` | **DEFECT**（SyntaxError） |
| 03 | fstring_const_str_double_quotes | `x = f'"k": {"hello"!s}'` | **DEFECT**（SyntaxError） |
| 04 | fstring_const_num_conversion (CTRL) | `x = f'"k": {1!s}'` | OK（int Constant，无引号） |
| 05 | fstring_mixed_const_var | `x = f'"k": {"1"!s}{var}suffix'` | **DEFECT**（SyntaxError） |
| 06 | fstring_const_str_in_double_quotes | `x = f'"k": {"a"!r}'` | **DEFECT**（SyntaxError） |
| 07 | fstring_nested_quotes (Compare) | `x = f'"enabled": {freq != "tick"!s}'` | **DEFECT**（SyntaxError） |
| 08 | fstring_const_str_repr (Call) | `x = f'"k": {repr("hello")!s}'` | **DEFECT**（SyntaxError） |
| 09 | ctrl_fstring_var_conversion (CTRL) | `x = f'"k": {var!s}'` | OK（变量，无引号） |
| 10 | ctrl_fstring_num_literal (CTRL) | `x = f'"k": {42}'` | OK（数字，无引号） |

- **DEFECT-REPRO 计数**：pre-fix 7 / 10
- **CTRL 组（04, 09, 10）全部 OK**：证明缺陷仅在 FormattedValue 内含字符串字面量时触发

## 5. decompile 流程诊断

```
python _r10_trace.py 2>&1
=== _generate_joined_str (AST) CALLED for user_code ===
num values: 25
  [13] ASTFormattedValue conv=1 inner=<ASTConstant>  ← {'1'!s}
  [15] ASTFormattedValue conv=1 inner=<ASTCompare>    ← {frequency != 'tick'!s}
  [19] ASTFormattedValue conv=1 inner=<ASTCompare>    ← {enable_debug == 'true'!s}
RESULT: f'...{"enabled": {'1'!s}...'  ← 单引号冲突
```

`pyc_batch_verify.py single` 因 `py_compile.compile(..., quiet=2)` 在 Python 3.11.7 返回 None（pre-existing 工具 bug，自 R07 起记录），无法自动测量 match_rate。手动 `py_compile.compile(..., quiet=0)` 确认 SyntaxError。

## 6. 当前 pyc 状态与累计成功率

| 指标 | R09 末 | R10 pre-fix |
|---|---|---|
| 累计成功率 | 70.90% | 70.90%（持平，backtest 仍 failed） |
| verified pyc | 31 | 31 |
| backtest.pyc | failed（f-string 完整 25/25 段，但 Pattern Q SyntaxError） | failed（同） |
| backtestOK.py 编译 | SyntaxError line 69 | SyntaxError line 69 |

## 7. 修复方向建议

**修复目标**：`_generate_joined_str`（AST 版本）+ `_generate_joined_str_from_dict`（dict 版本）+ `_generate_expression` FormattedValue 顶层分支（L3187-3191）的定界符选择逻辑。

**算法驱动修复**（非补丁）：
1. **分两遍渲染**：先渲染所有 FormattedValue/表达式片段（含 `{}` 包裹），再渲染字面片段。
2. **扫描表达式片段引号**：检查所有表达式片段中出现的引号字符（`'` / `"`）。
3. **选择定界符**：
   - 表达式片段无 `'` → 用 `'` 定界
   - 表达式片段无 `"` → 用 `"` 定界
   - 两者皆有 → 三引号 `'''` 定界（罕见边界）
4. **按定界符转义字面片段**：仅转义定界符引号（不总是 `'`）+ 换行 + 花括号（R07 fix）；另一引号原样保留。

**算法依据**：区域归约算法原则 2「每块唯一归属」—— 字面片段归字面层（可转义、可重新选择引号），表达式片段归表达式层（不可转义、不可含定界符引号）；定界符选择由表达式片段内容决定，确保表达式片段不变即可放入 f-string。

**预期效果**：
- 7 DEFECT-REPRO → 0 DEFECT-REPRO
- backtest.pyc `handle_backtest_build` f-string 编译通过
- backtest.pyc 状态 failed → partial/ok（解锁累计成功率提升）
