# R07 反编译验证报告 — IQCommon/backtest/backtest.pyc

## 1. 目标 pyc 信息

| 字段 | 值 |
|---|---|
| pyc 路径 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/backtest/backtest.pyc` |
| 文件大小 | 9047 字节 |
| 函数数 | 2（`<module>` / `handle_backtest_build`） |
| Python 版本 | 3.11 |
| 验证轮次 | R07 (rcm-r07) |
| 反编译产物 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/backtest/backtestOK.py` (6260 chars) |
| 上轮状态 | pending（未验证，按轮询规则本轮选取） |
| 本轮 R07 pre-fix 状态 | **failed**（load_compiled_failed — backtestOK.py 含 2 处语法错误，py_compile 返回 None） |

## 2. 反编译 + 字节码 diff 结果

本轮目标：按轮询规则选取下一个 `decompile_status != ok` 的 pyc。从 `pyc_index.json` 按路径字母序轮询，排除已 ok 的 pyc 后，首个 pending 条目为 `IQCommon/backtest/backtest.pyc`。

执行命令：

```bash
python scripts/pyc_batch_verify.py single "F:/Downloads/pythoncdc-main/site-packages/IQCommon/backtest/backtest.pyc"
```

完整输出：

```
[SINGLE] F:\Downloads\pythoncdc-main\site-packages\IQCommon\backtest\backtest.pyc
  OK.py: F:\Downloads\pythoncdc-main\site-packages\IQCommon\backtest\backtestOK.py
  source: 6260 chars

字节码 diff 报告:
  decompile_status:   failed
  total_functions:   0
  matched_functions: 0
  match_rate:        0.00%
  missing_in_decomp: []
  extra_in_decomp:   []
  error: load_compiled_failed: TypeError: expected str, bytes or os.PathLike object, not NoneType
```

**结论**：反编译产物 `backtestOK.py` 含 2 处语法错误，`py_compile` 返回 `None`（静默失败，非异常），导致 `load_compiled` 拿到 `None` 路径触发 `TypeError`。整个文件无法编译 → 2 个函数全部无法比对 → `match_rate=0.00%`、`total_functions=0`。这不是真实 0% 一致，而是「生成产物语法不合法」级别的失败。

### 2.1 两处语法错误定位（backtestOK.py）

**Pattern G — f-string 字面花括号未转义（L69）**：

```python
user_code = f',\n        "debug_port": {DEFAULT_PORT!s},\n    },\n    "plugin_fly_api": {\n        "enabled": True,\n    },\n},\n}\n\nconfig = parse_config(config)\nrun(config, user_variables={user_variables!s})\n'
```

f-string 的字面常量片段中，`{` 与 `}` 未转义为 `{{`/`}}`。Python 解释器把 `{\n        "enabled": True,\n    }` 当作 FormattedValue 表达式体（含反斜杠 → `SyntaxError: f-string expression part cannot include a backslash`），`{}` 当作空表达式（`SyntaxError: f-string: empty expression not allowed`）。仅 `{DEFAULT_PORT!s}` 与 `{user_variables!s}` 是真实 FormattedValue。

**Pattern T — TRY except handler 被丢弃（L92-94）**：

```python
try:
    shutil.copy(strategy_path, backtest_path)
time = datetime.datetime.now()
```

`try:` 体之后直接跟随 `time = ...`，`except FileExistsError as e: return (...)` 整段被丢弃 → `SyntaxError: expected 'except' or 'finally' block`。

## 3. 当前 pyc 成功率

| 指标 | 修复前（pending） | R07 pre-fix | 变化 |
|---|---|---|---|
| 总函数数 | 2 | 2 | — |
| 一致函数数 | 0（未验证） | 0（load_compiled_failed） | — |
| 当前 pyc 成功率 | 0.00%（pending） | **0.00%**（failed） | 持平（语法错误阻断） |
| decompile_status | pending | **failed** | 降级（验证后发现语法错误） |

**结论**：该 pyc 反编译产物含 2 处语法错误，整个文件无法编译，2 个函数全部阻断。需修复 Pattern G + Pattern T 后才能进入字节码比对阶段。

## 4. 不一致函数清单（2 个全部阻断）

该 pyc 全部 2 个函数因 `backtestOK.py` 语法错误无法编译，全部阻断（无法进入字节码 diff）：

| # | 函数 | 阻断原因 | 缺陷模式 |
|---|---|---|---|
| 1 | `<module>` | 整文件 py_compile 失败（None） | 间接（被 handle_backtest_build 的语法错误连带） |
| 2 | `handle_backtest_build` | L69 Pattern G + L92-94 Pattern T | Pattern G（f-string 字面花括号未转义）+ Pattern T（except handler 丢弃） |

### 4.1 Pattern G 根因（f-string 字面花括号未转义）

- 反编译器：`core/cfg/code_generator.py`
- 缺陷方法：`_generate_joined_str_from_dict`（L4122-4149）与 `_generate_joined_str`（L4221-4250）
- 缺陷点：处理 f-string 的字面字符串常量片段时（`isinstance(value, str)` / `ASTConstant`-str 分支），仅对 `'`/`\n`/`\r` 转义，**未把字面 `{`→`{{`、`}`→`}}` 转义**。
- FormattedValue 分支（产生真实 `{expr}`）不应转义 — 当前实现正确，无需改动。
- `backtestOK.py` L69 的 BUILD_STRING 25（offset 1454）含 25 个片段，其中字面常量片段（如 const `',\n    },\n    "plugin_fly_api": {\n        "enabled": True,\n    },\n},\n}\n\n...'`）含字面 `{`/`}`，仅 `{DEFAULT_PORT!s}` 与 `{user_variables!s}` 是真实 FormattedValue。

### 4.2 Pattern T 根因（TRY except handler 被丢弃）

- 反编译器：`core/cfg/region_ast_generator.py`
- 缺陷方法：`_generate_with`（L17593，post-body 块循环 L18443-18455）
- 确诊路径（`diag_trace_2438.py` 实测）：try@2394 的 handler_entry block 2438 被 `_generate_with` 在 **L18454** `self.generated_blocks.add(blk)` 标记为 generated（调用栈：`_generate_region:2188 → _generate_if:7686 → _if_generate_normal:11020 → _if_generate_else_branch:10027 → _process_if_blocks:13425 → ... → _generate_region:2192 → _generate_with:18454`）。
- 随后 `_generate_try`（L15654）在 handler 循环 L15896 `if handler_entry in self.generated_blocks: continue` 跳过 handler 2438 → 不输出 `except` → `try:` 未关闭 → 语法错误。
- **根因**：`_generate_with` 在 post-body 循环 L18436-18440 **重新计算** `with_cleanup_blocks = cleanup_blocks ∪ exception_blocks`，但**未重新应用** L17631-17643 的 R20-Bug7 `_nested_try_handler_entries` 排除。block 2438（属 TryExceptRegion 的 handler_entry）在 L18436 重算时回到 `with_cleanup_blocks`，被 L18453-18454 误消费。
- 区域识别本身正确：`block_to_region[2438] = TryExceptRegion`（2438 唯一归属 TryExceptRegion）。bug 在生成层：WithRegion 违反「每块唯一归属」原则消费了不属于自己的块。
- 影响面：Pattern T 同时阻断 `main.pyc`（fc=34）与 `graph.pyc`（fc=40）→ 共 76 函数。

## 5. 累计成功率（跨所有已验证 pyc）

执行命令：`python scripts/pyc_batch_verify.py stats`

```
======================================================================
累计统计:
  total_pyc:             402
  verified_pyc:          30
  ok_pyc:                22
  partial_pyc:           5
  failed_pyc:            3
  total_functions:       434
  matched_functions:     256
  cumulative_match_rate: 58.99%
======================================================================
```

| 指标 | R06 累计 | R07 pre-fix 累计 |
|---|---|---|
| verified_pyc | 18 | **30** |
| ok_pyc | 15 | **22** |
| partial_pyc | 1 | 5 |
| failed_pyc | 2 | **3**（+backtest） |
| total_functions | 249 | **434** |
| matched_functions | 143 | **256** |
| cumulative_match_rate | 57.43% | **58.99%** |

### 与上一轮对比

- **R06 → R07 pre-fix 累计 match_rate**：57.43% → 58.99%（+1.56 pp，单调递增；新增 12 个 pyc 验证，其中 backtest/main/graph 3 个 failed，其余多 ok）。
- **本 pyc 贡献**：backtest.pyc 从 pending → failed（2 函数全部阻断），累计 +3 failed_pyc（含 main/graph）。
- **Pattern T 跨 pyc 影响**：backtest(fc=2) + main(fc=34) + graph(fc=40) = 76 函数被 Pattern T 阻断，修复 Pattern T 可一次性解锁。

## 6. 复现实例清单

验证脚本：`minimal_repros/verify_repros.py`（函数级字节码 diff，复用 R06 harness）。

构造 13 个最小复现实例（4 Pattern G + 2 Pattern T full-drop + 3 Pattern T2 body-drop + 4 NO-DEFECT 控制组）：

| # | 实例文件 | 模式 | 期望 | pre-fix 实测 | 说明 |
|---|---|---|---|---|---|
| 01 | repro_01_pattern_g_fstring_literal_braces | Pattern G 字面 `{}` | DEFECT | **ERROR** syntax_error `empty expression not allowed` | `{{}}` 未转义 → `{}` 空表达式 |
| 02 | repro_02_pattern_g_fstring_json_nested | Pattern G JSON 嵌套 | DEFECT | **ERROR** syntax_error `backslash` | 字面 `{` 未转义 → 表达式体含 `\n` |
| 03 | repro_03_pattern_g_fstring_multiline_braces | Pattern G 多行 | DEFECT | **ERROR** syntax_error `backslash` | 同上 |
| 04 | repro_04_pattern_g_fstring_braces_around_fv | Pattern G 紧邻 FV | DEFECT | **DEFECT-REPRO** 17 true_diffs | `{{start}}` → `start` LOAD_NAME |
| 05 | repro_05_pattern_t_with_then_try_except | Pattern T full-drop | DEFECT | **ERROR** syntax_error `expected 'except' or 'finally'` | with 前置 → except 整段丢 |
| 06 | repro_06_pattern_t_try_in_else_with_preceded | Pattern T 镜像 backtest | DEFECT | **ERROR** syntax_error `expected 'except' or 'finally'` | with→if/else→else:try/except |
| 07 | repro_07_pattern_t2_except_return_str | Pattern T2 body-drop | DEFECT | **DEFECT-REPRO** 11 true_diffs | `except X as e: return 'str'` body 丢 |
| 08 | repro_08_pattern_t2_except_return_int | Pattern T2 body-drop | DEFECT | **DEFECT-REPRO** 11 true_diffs | `return 42` body 丢 |
| 09 | repro_09_pattern_t2_except_return_none | Pattern T2 body-drop | DEFECT | **DEFECT-REPRO** 11 true_diffs | `return None` body 丢 |
| 10 | repro_10_ctrl_fstring_no_braces | CTRL f-string 无字面花括号 | NO-DEFECT | **NO-DEFECT** ✓ | 确认无字面花括号时不触发 G |
| 11 | repro_11_ctrl_try_except_no_with | CTRL try/except 无 with | NO-DEFECT | **NO-DEFECT** ✓ | 确认无 with 前置时不触发 T |
| 12 | repro_12_ctrl_except_return_tuple | CTRL return tuple | NO-DEFECT | **NO-DEFECT** ✓ | 确认 return tuple 不触发 T2 |
| 13 | repro_13_ctrl_except_no_as | CTRL 无 as 绑定 | NO-DEFECT | **NO-DEFECT** ✓ | 确认无 `as e` 不触发 T2 |

**pre-fix 汇总**：13 repros，9 DEFECT（4 G + 2 T + 3 T2），4 NO-DEFECT。原始输出归档于 `_verify_repros_out_pre.txt`。

### Pattern T2 说明（独立子缺陷）

Pattern T2（`except X as e: return <简单常量>` → handler body 被丢弃为 `pass`/`return None`）是与 Pattern T **不同**的子缺陷：
- Pattern T：except **整段**丢弃（`try:` 无 `except`）— 由 WithRegion 误消费 handler_entry 触发，需 with 前置。
- Pattern T2：except **行保留**，但 **body 被丢**（`return 'str'` → body 空）— 无需 with 前置，由 handler body return-const 触发。

Pattern T2 的修复不在 R07 scope（除非修复 trivial 且无回归）。R07 优先修复 Pattern T（解锁 76 函数）。Pattern T2 作残留记录。

## 7. 缺陷根因分析

### Pattern G（f-string 字面花括号未转义）

- **缺陷层**：表达式重建层 `core/cfg/code_generator.py`
- **缺陷方法**：`_generate_joined_str_from_dict`（L4122-4149）、`_generate_joined_str`（L4221-4250）
- **根因**：f-string 由 `JoinedStr.values` 拼接而成，其中字面字符串常量片段（`str` / `ASTConstant`-str）的 `{`/`}` 是字面字符，重编时必须转义为 `{{`/`}}`。当前实现仅转义 `'`/`\n`/`\r`，漏转义花括号。
- **影响**：仅 backtest.pyc 的 `handle_backtest_build`（1 函数，BUILD_STRING 25 片段）。
- **修复方向**：在两个方法的字面字符串分支，转义后追加 `.replace('{', '{{').replace('}', '}}')`。FormattedValue 分支不动。`_generate_format_spec_inner_from_dict` 不动（格式说明符上下文字面花括号语义不同，且 backtest 无 format_spec）。

### Pattern T（TRY except handler 被丢弃）

- **缺陷层**：区域生成层 `core/cfg/region_ast_generator.py`
- **缺陷方法**：`_generate_with`（L18443-18455 post-body 块循环）
- **根因**：`_generate_with` 在 post-body 循环 L18436-18440 重算 `with_cleanup_blocks` 时，未重新应用 L17631-17643 的 R20-Bug7 `_nested_try_handler_entries` 排除，导致属 TryExceptRegion 的 handler_entry block（如 2438）被 WithRegion 在 L18454 误标记为 generated。随后 `_generate_try` L15896 因 handler_entry 已 generated 而跳过 → 不输出 except。
- **算法原则违反**：违反「每块唯一归属」— `block_to_region[2438]=TryExceptRegion`，WithRegion 不应消费。
- **修复方向**：在 L18453 `if blk in with_cleanup_blocks:` 之前，加 `block_to_region` 归属守卫：若块被其他区域（非本 WithRegion）拥有，则 `continue`（不消费），交由拥有者区域处理。
- **影响**：backtest(fc=2) + main(fc=34) + graph(fc=40) = 76 函数。

### 跨轮残留模式交叉验证

- Pattern A2/B/C/E/F/M2：跨轮残留不变（见 R06 报告）。backtest.pyc 不触发这些（无 BoolOp-in-try / 无 dictcomp / 无装饰器堆叠）。
- Pattern T2：本轮新发现残留（3 函数级 repro），独立于 Pattern T，后续轮次修复。

## 8. 产物清单

| 产物 | 路径 |
|---|---|
| 本报告 | `.trae/specs/region-comment-multi-pyc-iteration/rounds/round_07/test_engineer/decompile_report.md` |
| 验证脚本 | `.trae/specs/.../round_07/test_engineer/minimal_repros/verify_repros.py` |
| 复现实例 01-13 | `.trae/specs/.../round_07/test_engineer/minimal_repros/repro_01_*.py` … `repro_13_*.py` |
| 验证原始输出（pre-fix） | `.trae/specs/.../round_07/test_engineer/_verify_repros_out_pre.txt` |
| 诊断脚本 | `.trae/specs/.../round_07/test_engineer/diag_trace_2438.py`（确诊 2438 消费路径） |
| 反编译 OK.py（含 bug） | `site-packages/IQCommon/backtest/backtestOK.py`（由 single 生成，未手工编辑） |

## 9. pyc_index.json 更新

`scripts/pyc_batch_verify.py single` 已自动回写 backtest.pyc 条目：`decompile_status=failed` / `bytecode_match_rate=0.0` / `ok_py_generated=false`。`last_tested_round` 待修复后补写为 7。

## 10. 约束遵守

- 未修改 `core/cfg/*` 任何代码（测试工程师阶段只诊断 + 复现）。
- 未修改任何 `+OK.py` 文件（backtestOK.py 由 single 命令生成，未手工编辑）。
- 未修改 pyc_index.json 超出 single 命令自动回写范围。
- 未执行 git commit。
- 所有命令均在预算内（single ≤60s 实测 <5s，stats ≤60s 实测 <5s，repro 验证 ≤60s 实测 <15s，diag_trace ≤60s 实测 <5s）。
- 13 个 repro 均 ≤30 行、自包含、无业务逻辑/领域知识。
- 算法约束（bottom-up / 唯一块归属 / nested=abstract / parent ref child entry）未违反（诊断阶段未改算法）。
- 无反模式前缀新增。
