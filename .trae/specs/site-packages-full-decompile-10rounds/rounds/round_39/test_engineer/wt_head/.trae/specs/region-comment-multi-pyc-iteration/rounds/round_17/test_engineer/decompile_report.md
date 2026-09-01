# R17 反编译验证报告 — IQCommon/strategy/zt_api.pyc

## 1. 目标 pyc 信息

| 字段 | 值 |
|---|---|
| pyc 路径 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/strategy/zt_api.pyc` |
| 文件大小 | 9793 字节 |
| 函数数 | 4（含 `<module>` / `read_model_file` / `read_config_file` / `amount_trans`） |
| Python 版本 | 3.11 |
| 验证轮次 | R17 (rcm-r17) |
| 反编译产物 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/strategy/zt_apiOK.py` (6164 chars) |
| 上轮状态 | pending（未验证，按轮询规则本轮选取） |
| 本轮 R17 match_rate | **100.00%** (4/4) — 升级为 ok |

## 2. 反编译 + 字节码 diff 结果

本轮目标：按轮询规则选取下一个 `decompile_status != ok` 的 pyc（新 pyc 轮询，pending 优先）。从 `pyc_index.json` 按路径字母序轮询，排除已 ok / 已验证 pyc 后，首个 pending 条目为 `IQCommon/strategy/zt_api.pyc`（pending, function_count=4, last_tested_round=0, size=9793）。

执行命令：

```bash
python scripts/pyc_batch_verify.py single "F:/Downloads/pythoncdc-main/site-packages/IQCommon/strategy/zt_api.pyc"
```

完整输出：

```
[SINGLE] F:\Downloads\pythoncdc-main\site-packages\IQCommon\strategy\zt_api.pyc
  OK.py: F:\Downloads\pythoncdc-main\site-packages\IQCommon\strategy\zt_apiOK.py
  source: 6164 chars

字节码 diff 报告:
  decompile_status:   ok
  total_functions:   4
  matched_functions: 4
  match_rate:        100.00%
  missing_in_decomp: []
  extra_in_decomp:   []
```

**结论**：该 pyc 反编译后 4/4 函数字节码 100% 一致，无需修复。反编译产物 `zt_apiOK.py` 已自动生成。该 pyc 包含 dict 下标连续赋值链（`cfg['k'] = float(model['x']) * 0.01` / `int(model['x'])` / `float(a / b)`）、`dict.get('k', dict.get('k2', default))` 嵌套默认值、变量跨调用重赋值（`factor_type = 0,1,2,3`）、`if flag:` 简单分支（无 else）、裸 `try/except` + except 内赋值、`if/elif/else` + 字符串切片比较（`stock[:2] == '68'`）+ `in` 元组成员（`stock[:2] in ('11','10','12')`）+ 嵌套 if/else + return 等模式，均被 R01–R16 累积修复后的反编译器正确处理。

## 3. 当前 pyc 成功率

| 指标 | 修复前（pending） | R17 验证后 | 变化 |
|---|---|---|---|
| 总函数数 | 4 | 4 | — |
| 一致函数数 | 0（未验证） | **4** | +4 |
| 当前 pyc 成功率 | 0.00%（pending） | **100.00%** | +100.00 pp |
| decompile_status | pending | **ok** | 升级 |

**结论**：该 pyc 首次验证即达 100% 字节码一致，升级为 ok。无需修复工程师介入。

## 4. 不一致函数清单（0 个）

该 pyc 全部 4 个函数字节码一致，无不一致函数。

涉及的函数模式（全部正确反编译）：
- `<module>`：import + 3 函数定义
- `read_model_file`：`dict()` 构造 + 大量 dict 下标连续赋值（`sys_config['k'] = float(model['x']) * 0.01` / `int(model['x'])` / `float(sys_config['price5'] / sys_config['price'])`）+ return dict
- `read_config_file`：变量重赋值（`factor_type = 0,1,2,3`）跨 4 次 `factor_info_get` 调用 + `dict.get('k', dict.get('k2', default))` 嵌套默认值 + `dict['k']` 下标赋值 + `if is_trade_flag:` 简单分支（无 else，body 内赋值）+ 裸 `try/except`（except body 内赋值 `sys_config['hold_days'] = 10`）+ return dict
- `amount_trans`：`if/elif/else` 链 + 字符串切片比较（`stock[:2] == '68'`）+ 嵌套 `if/else`（`amount < 200` 分支 return）+ `in` 元组成员（`stock[:2] in ('11','10','12')`）+ `int(amount / 10) * 10` 算术 + 尾部 return

## 5. 累计成功率（跨所有已验证 pyc）

执行命令：`python scripts/pyc_batch_verify.py stats`

```
======================================================================
累计统计:
  total_pyc:             402
  verified_pyc:          35
  ok_pyc:                24
  partial_pyc:           10
  failed_pyc:            1
  total_functions:       456
  matched_functions:     306
  cumulative_match_rate: 67.11%
======================================================================
```

| 指标 | R16 累计（基线 commit d490b86） | R17 累计 |
|---|---|---|
| verified_pyc | 34 | **35** |
| ok_pyc | 23 | **24** |
| partial_pyc | 10 | 10 |
| failed_pyc | 1 | 1 |
| total_functions | 452 | **456** |
| matched_functions | 302 | **306** |
| cumulative_match_rate | 66.81% | **67.11%** |

### 与上一轮对比

- **R16 → R17 累计 match_rate**：66.81% → 67.11%（+0.30 pp，单调递增）。
- **本 pyc 贡献**：zt_api.pyc 从 pending → ok（4/4），累计 +4 matched functions、+1 ok_pyc、+1 verified_pyc、+4 total_functions。
- **本 pyc 状态**：首次验证即达 100%，升级为 ok。

## 6. 复现实例清单

验证脚本：`minimal_repros/verify_repros.py`（函数级字节码 diff，含 code-object 身份噪声归一化）。

该 pyc 首次验证即 100% 一致，按规范豁免强制 10+ DEFECT-REPRO 要求。为回归保护，仍构造 10 个控制组复现实例（全部 NO-DEFECT），覆盖该 pyc 涉及的所有模式 + 跨轮交叉验证：

| # | 实例文件 | 模式 | 结果 | 对应函数/交叉引用 |
|---|---|---|---|---|
| 01 | repro_01_dict_subscript_assign_chain | dict 下标连续赋值链（float/int/算术） | NO-DEFECT ✓ | read_model_file |
| 02 | repro_02_float_mul_01_conv | float(x) * 0.01 转换赋值 | NO-DEFECT ✓ | read_model_file change_percent |
| 03 | repro_03_int_conv_assign | int(x) 转换赋值 | NO-DEFECT ✓ | read_model_file stock_avg_poly |
| 04 | repro_04_float_div_in_call | float(a / b) 除法后 float 包装 | NO-DEFECT ✓ | read_model_file close_percent |
| 05 | repro_05_dict_get_nested_default | dict.get('k', dict.get('k2', default)) 嵌套默认值 | NO-DEFECT ✓ | read_config_file pe_times_high |
| 06 | repro_06_simple_if_no_else_assign | if flag: 赋值（无 else） | NO-DEFECT ✓ | read_config_file is_trade_flag |
| 07 | repro_07_var_reassign_across_calls | 变量跨调用重赋值（ft=0,1,2） | NO-DEFECT ✓ | read_config_file factor_type |
| 08 | repro_08_bare_try_except_assign | 裸 try/except + except 内赋值 | NO-DEFECT ✓ | read_config_file hold_days |
| 09 | repro_09_if_elif_else_slice_in_tuple | if/elif/else + 切片比较 + in 元组 + 嵌套 if/else return | NO-DEFECT ✓ | amount_trans |
| 10 | repro_10_ctrl_if_elif_else_no_try | CTRL-if/elif/else 无 try（交叉 A2，无 try） | NO-DEFECT ✓ | 确认 A2 需 try 上下文触发 |

```
Found 10 repros
  repro_01_dict_subscript_assign_chain.py                      NO-DEFECT      2/2 matched
  repro_02_float_mul_01_conv.py                                NO-DEFECT      2/2 matched
  repro_03_int_conv_assign.py                                  NO-DEFECT      2/2 matched
  repro_04_float_div_in_call.py                                NO-DEFECT      2/2 matched
  repro_05_dict_get_nested_default.py                          NO-DEFECT      2/2 matched
  repro_06_simple_if_no_else_assign.py                         NO-DEFECT      2/2 matched
  repro_07_var_reassign_across_calls.py                        NO-DEFECT      2/2 matched
  repro_08_bare_try_except_assign.py                           NO-DEFECT      2/2 matched
  repro_09_if_elif_else_slice_in_tuple.py                      NO-DEFECT      2/2 matched
  repro_10_ctrl_if_elif_else_no_try.py                         NO-DEFECT      2/2 matched

Summary: 0 DEFECT-REPRO, 10 NO-DEFECT, 0 ERROR
```

**10/10 NO-DEFECT**。控制组确认：
- 该 pyc 的所有模式（dict 下标赋值链 / float×0.01 / int 转换 / float(a/b) / dict.get 嵌套默认值 / 简单 if 无 else / 变量跨调用重赋值 / 裸 try/except / if/elif/else + 切片 + in 元组 + 嵌套 return）被正确反编译
- Pattern A2（R04 残留）需 try 上下文触发，无 try 时不触发（repro_10 确认 if/elif/else 无 try 正常）
- 裸 try/except + except 内赋值（repro_08）被 R01 TRY 修复正确处理，不触发 Pattern T/T2/T3

## 7. 缺陷根因分析（本轮无新增缺陷）

本轮 pyc 首次验证即 100% 一致，无新增缺陷。该 pyc 的模式被 R01–R16 累积修复后的反编译器正确处理。

### 跨轮残留模式交叉验证

- **Pattern A2**（R04 残留，9 函数 in klinedata.pyc）：需「简单条件 + try-body if + 多分支 + return 坍缩（无 BoolOp）」组合触发。zt_api.pyc 的 try 是裸 except + except 内赋值（非 try-body if 坍缩），不触发 A2（repro_10 确认 if/elif/else 无 try 正常）。
- **Pattern B**（R03 残留）：变量作用域/名称解析问题。zt_api.pyc 的变量作用域简单（函数内局部变量 + dict 下标赋值），不触发。
- **Pattern C/C2**（R03/R11 残留）：值/赋值/tuple unpack 丢失。zt_api.pyc 的赋值均正确保留（含 dict.get 嵌套默认值），不触发 C2（无 SWAP unpack，repro_05 确认）。
- **Pattern F**（R01 残留）：elif BoolOp 链拆分。zt_api.pyc 使用 if/elif/else（非 elif BoolOp 链），不触发。
- **Pattern T3/T4**（R08/R14 修复）：try post-try / 共享 merge_block。zt_api.pyc 的 try 是函数末尾裸 except + except 内赋值 + return dict（try 后无 post-try 语句），不触发 T3/T4（repro_08 确认）。
- **continue-sink**（R15 修复）：then_succ=continue 误并 else。zt_api.pyc 无 continue，不触发。
- **BOOLOP-in-return**（R15 残留）：chained-compare + BoolOp OR 短路在 return 上下文。zt_api.pyc 的 return 为简单 dict / int 表达式，无短路跳转，不触发。

## 8. 产物清单

| 产物 | 路径 |
|---|---|
| 本报告 | `.trae/specs/region-comment-multi-pyc-iteration/rounds/round_17/test_engineer/decompile_report.md` |
| 验证脚本 | `.trae/specs/.../round_17/test_engineer/minimal_repros/verify_repros.py` |
| 复现实例 01-10 | `.trae/specs/.../round_17/test_engineer/minimal_repros/repro_01_*.py` … `repro_10_*.py` |
| 反编译 OK.py | `site-packages/IQCommon/strategy/zt_apiOK.py` |

## 9. pyc_index.json 更新

`scripts/pyc_batch_verify.py single` 已自动回写 zt_api.pyc 条目：
`decompile_status=ok` / `bytecode_match_rate=1.0` / `ok_py_generated=true`。
`last_tested_round` 手动补写为 17。
本 pyc 达到 100%，升级为 ok。

## 10. 约束遵守

- 未修改 `core/cfg/*` 任何代码（pyc 100%，无需修复）。
- 未修改任何 `+OK.py` 文件（zt_apiOK.py 由 single 命令生成，未手工编辑）。
- 未修改 pyc_index.json 超出 single 命令自动回写范围 + last_tested_round 补写。
- 所有命令均在预算内（single ≤60s 实测 <8s，stats ≤60s 实测 <5s，repro 验证 ≤60s 实测 <15s）。
- 10 个 repro 均 ≤15 行、自包含、无业务逻辑/领域知识。
- 算法约束（bottom-up / 唯一块归属 / nested=abstract / parent ref child entry）未违反。
- 无反模式前缀新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）。
