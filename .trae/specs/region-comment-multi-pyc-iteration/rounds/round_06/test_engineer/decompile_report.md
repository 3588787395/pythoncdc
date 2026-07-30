# R06 反编译验证报告 — IQCommon/data/basic_data_source.pyc

## 1. 目标 pyc 信息

| 字段 | 值 |
|---|---|
| pyc 路径 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/data/basic_data_source.pyc` |
| 文件大小 | 5407 字节 |
| 函数数 | 8（含 `<module>` / `BasicDataSource.__init__` / `get_dividend` / `get_dict_assets` / `assets_to_dict` / `get_security_info` / `get_security_info_lru`） |
| Python 版本 | 3.11 |
| 验证轮次 | R06 (rcm-r06) |
| 反编译产物 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/data/basic_data_sourceOK.py` (2927 chars) |
| 上轮状态 | pending（未验证，按轮询规则本轮选取） |
| 本轮 R06 match_rate | **100.00%** (8/8) — 升级为 ok |

## 2. 反编译 + 字节码 diff 结果

本轮目标：按轮询规则选取下一个 `decompile_status != ok` 的 pyc（非 klinedata.pyc / base_storage.pyc / IQCommon/__init__.pyc / IQCommon/api/__init__.pyc）。从 `pyc_index.json` 按路径字母序轮询，排除已 ok / 已排除 pyc 后，首个 pending 条目为 `IQCommon/data/basic_data_source.pyc`（pending, function_count=8, last_tested_round=0）。

执行命令：

```bash
python scripts/pyc_batch_verify.py single "F:/Downloads/pythoncdc-main/site-packages/IQCommon/data/basic_data_source.pyc"
```

完整输出：

```
[SINGLE] F:\Downloads\pythoncdc-main\site-packages\IQCommon\data\basic_data_source.pyc
  OK.py: F:\Downloads\pythoncdc-main\site-packages\IQCommon\data\basic_data_sourceOK.py
  source: 2927 chars

字节码 diff 报告:
  decompile_status:   ok
  total_functions:   8
  matched_functions: 8
  match_rate:        100.00%
  missing_in_decomp: []
  extra_in_decomp:   []
```

**结论**：该 pyc 反编译后 8/8 函数字节码 100% 一致，无需修复。反编译产物 `basic_data_sourceOK.py` 已自动生成。该 pyc 包含 isinstance 条件赋值、嵌套 for 循环 + dict 赋值、if/else + for + continue、if/elif/else + 嵌套 for 等模式，均被 R01–R05 累积修复后的反编译器正确处理。

## 3. 当前 pyc 成功率

| 指标 | 修复前（pending） | R06 验证后 | 变化 |
|---|---|---|---|
| 总函数数 | 8 | 8 | — |
| 一致函数数 | 0（未验证） | **8** | +8 |
| 当前 pyc 成功率 | 0.00%（pending） | **100.00%** | +100.00 pp |
| decompile_status | pending | **ok** | 升级 |

**结论**：该 pyc 首次验证即达 100% 字节码一致，升级为 ok。无需修复工程师介入。

## 4. 不一致函数清单（0 个）

该 pyc 全部 8 个函数字节码一致，无不一致函数。

涉及的函数模式（全部正确反编译）：
- `<module>`：import + class 定义
- `__init__`：实例属性赋值 + os.path.join + 对象构造
- `get_dividend`：isinstance 条件 + 条件重赋值 + return
- `get_dict_assets`：简单 return method call
- `assets_to_dict`：OrderedDict + 嵌套 for + dict 赋值
- `get_security_info`：if isinstance + for + .get(default) + if/continue + 嵌套 for+getattr + else dispatch
- `get_security_info_lru`：if/elif/else + 嵌套 for + getattr + .items()

## 5. 累计成功率（跨所有已验证 pyc）

执行命令：`python scripts/pyc_batch_verify.py stats`

```
======================================================================
累计统计:
  total_pyc:             402
  verified_pyc:          18
  ok_pyc:                15
  partial_pyc:           1
  failed_pyc:            2
  total_functions:       249
  matched_functions:     143
  cumulative_match_rate: 57.43%
======================================================================
```

| 指标 | R04 累计 | R05 累计 | R06 累计 |
|---|---|---|---|
| verified_pyc | 16 | 17 | **18** |
| ok_pyc | 13 | 14 | **15** |
| partial_pyc | 1 | 1 | 1 |
| failed_pyc | 2 | 2 | 2 |
| total_functions | 236 | 241 | **249** |
| matched_functions | 130 | 135 | **143** |
| cumulative_match_rate | 55.08% | 56.02% | **57.43%** |

### 与上一轮对比

- **R05 → R06 累计 match_rate**：56.02% → 57.43%（+1.41 pp，单调递增）。
- **本 pyc 贡献**：basic_data_source.pyc 从 pending → ok（8/8），累计 +8 matched functions、+1 ok_pyc、+1 verified_pyc。
- **本 pyc 状态**：首次验证即达 100%，升级为 ok。

## 6. 复现实例清单

验证脚本：`minimal_repros/verify_repros.py`（函数级字节码 diff）。

该 pyc 首次验证即 100% 一致，按规范豁免强制 10+ DEFECT-REPRO 要求。为回归保护，仍构造 10 个控制组复现实例（全部 NO-DEFECT），覆盖该 pyc 涉及的所有模式 + 跨轮交叉验证：

| # | 实例文件 | 模式 | 结果 | 对应函数/交叉引用 |
|---|---|---|---|---|
| 01 | repro_01_isinstance_conditional_reassign | isinstance 条件重赋值 | NO-DEFECT ✓ | get_dividend |
| 02 | repro_02_nested_for_dict_assign | 嵌套 for + dict 赋值 | NO-DEFECT ✓ | assets_to_dict |
| 03 | repro_03_if_else_for_continue | if/else + for + continue | NO-DEFECT ✓ | get_security_info |
| 04 | repro_04_if_elif_else_nested_for | if/elif/else + 嵌套 for | NO-DEFECT ✓ | get_security_info_lru |
| 05 | repro_05_class_init_attr_assign | class __init__ 属性赋值 | NO-DEFECT ✓ | __init__ |
| 06 | repro_06_method_call_dispatch | 方法分发到另一方法 | NO-DEFECT ✓ | get_security_info else |
| 07 | repro_07_for_get_default | for + dict.get(key, None) | NO-DEFECT ✓ | get_security_info inner |
| 08 | repro_08_for_key_getattr | for key + getattr(obj, key, None) | NO-DEFECT ✓ | get_security_info inner loop |
| 09 | repro_09_ctrl_simple_if_no_boolop | CTRL-简单 if/else（交叉 A2） | NO-DEFECT ✓ | 确认 A2 需 try 上下文触发 |
| 10 | repro_10_ctrl_elif_chain_no_boolop | CTRL-elif 链（交叉 F） | NO-DEFECT ✓ | 确认 elif 无 BoolOp 正常 |

**10/10 NO-DEFECT**。控制组确认：
- 该 pyc 的所有模式（isinstance/嵌套 for/if-continue/elif/getattr）被正确反编译
- Pattern A2（R04 残留）需 try 上下文触发，无 try 时不触发（repro_09 确认）
- Pattern F（R01 残留）需 BoolOp elif 链触发，无 BoolOp 的 elif 正常（repro_10 确认）

## 7. 缺陷根因分析（本轮无新增缺陷）

本轮 pyc 首次验证即 100% 一致，无新增缺陷。该 pyc 的模式被 R01–R05 累积修复后的反编译器正确处理。

### 跨轮残留模式交叉验证

- **Pattern A2**（R04 残留，9 函数 in klinedata.pyc）：需「简单条件 + try-body if + 多分支 + return 坍缩（无 BoolOp）」组合触发。basic_data_source.pyc 无 try 块，故不触发（repro_09 确认）。
- **Pattern B**（R03 残留，6 函数）：变量作用域/名称解析问题。basic_data_source.pyc 的变量作用域简单（方法内局部变量），不触发。
- **Pattern C**（R03 残留，5 函数）：值/赋值丢失。basic_data_source.pyc 的赋值均正确保留。
- **Pattern F**（R01 残留）：elif BoolOp 链拆分。basic_data_source.pyc 使用 if/else（非 elif 链），不触发（repro_10 确认 elif 无 BoolOp 正常）。
- **Pattern M2**（R05 残留）：堆叠装饰器嵌套。basic_data_source.pyc 无装饰器，不触发。

## 8. 产物清单

| 产物 | 路径 |
|---|---|
| 本报告 | `.trae/specs/region-comment-multi-pyc-iteration/rounds/round_06/test_engineer/decompile_report.md` |
| 验证脚本 | `.trae/specs/.../round_06/test_engineer/minimal_repros/verify_repros.py` |
| 复现实例 01-10 | `.trae/specs/.../round_06/test_engineer/minimal_repros/repro_01_*.py` … `repro_10_*.py` |
| 验证原始输出 | `.trae/specs/.../round_06/test_engineer/_verify_repros_out.txt` |
| 反编译 OK.py | `site-packages/IQCommon/data/basic_data_sourceOK.py` |

## 9. pyc_index.json 更新

`scripts/pyc_batch_verify.py single` 已自动回写 basic_data_source.pyc 条目：
`decompile_status=ok` / `bytecode_match_rate=1.0` / `ok_py_generated=true`。
`last_tested_round` 手动补写为 6。
本 pyc 达到 100%，升级为 ok。

## 10. 约束遵守

- 未修改 `core/cfg/*` 任何代码（pyc 100%，无需修复）。
- 未修改任何 `+OK.py` 文件（basic_data_sourceOK.py 由 single 命令生成，未手工编辑）。
- 未修改 pyc_index.json 超出 single 命令自动回写范围 + last_tested_round 补写。
- 未执行 git commit。
- 所有命令均在预算内（single ≤60s 实测 <5s，stats ≤60s 实测 <5s，repro 验证 ≤60s 实测 <10s）。
- 10 个 repro 均 ≤30 行、自包含、无业务逻辑/领域知识。
- 算法约束（bottom-up / 唯一块归属 / nested=abstract / parent ref child entry）未违反。
- 无反模式前缀新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）。
