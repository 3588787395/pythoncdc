# R02 反编译验证报告 — IQCommon/api/__init__.pyc

## 1. 目标 pyc 信息

| 字段 | 值 |
|---|---|
| pyc 路径 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/__init__.pyc` |
| 文件大小 | 152 字节 |
| 函数数 | 1（仅 `<module>`） |
| Python 版本 | 3.11 |
| 验证轮次 | R02 (rcm-r02) |

## 2. 反编译 + 字节码 diff 结果

执行命令：

```bash
python scripts\pyc_batch_verify.py single "F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/__init__.pyc"
```

完整输出：

```
[SINGLE] F:\Downloads\pythoncdc-main\site-packages\IQCommon\api\__init__.pyc
  OK.py: F:\Downloads\pythoncdc-main\site-packages\IQCommon\api\__init__OK.py
  source: 94 chars

字节码 diff 报告:
  total_functions:   1
  matched_functions: 1
  match_rate:        100.00%
  missing_in_decomp: []
  extra_in_decomp:   []
```

原 pyc 字节码（dis 验证）：

```
co_name: <module>
co_consts: (None,)
  0           0 RESUME                   0
              2 LOAD_CONST               0 (None)
              4 RETURN_VALUE
```

生成的 `__init__OK.py` 内容：

```python
# Source Generated with Decompyle++ (Python version)
# File: __init__.pyc (Python 3.11)

pass
```

`py_compile` 验证：✅ 通过。

## 3. 当前 pyc 成功率

| 指标 | 值 |
|---|---|
| 总函数数 | 1 |
| 一致函数数 | 1 |
| 当前 pyc 成功率 | **100.00%** |

## 4. 不一致函数清单

**无**。本 pyc 100% 一致，无不一致函数。

## 5. 累计成功率（跨所有已验证 pyc）

| 指标 | R01 累计 | R02 累计 |
|---|---|---|
| verified_pyc | 1 | 2 |
| ok_pyc | 0 | 1 |
| total_functions | 2 | 3 |
| matched_functions | 1 | 2 |
| cumulative_match_rate | 50.00% | **66.67%** |

### 与上一轮对比

- **R01 → R02 累计 match rate**：50.00% → 66.67%（+16.67 pp）
- **新增已验证 pyc**：1 个（`IQCommon/api/__init__.pyc`）
- **新增 ok_pyc**：1 个（本 pyc 100% 一致，状态升级为 `ok`）
- **新增 matched_functions**：+1（`<module>` 完全一致）

### 已验证 pyc 明细

| # | pyc 路径 | 函数数 | match_rate | status | 轮次 |
|---|---|---|---|---|---|
| 1 | `IQCommon/__init__.pyc` | 2 | 0.50 | partial | R01 |
| 2 | `IQCommon/api/__init__.pyc` | 1 | 1.00 | **ok** | **R02** |

## 6. 复现实例豁免说明

**本 pyc 100% 一致，豁免复现实例。**

依据任务约束："若本 pyc 100% 一致（无缺陷），则：
- 在 decompile_report.md 注明 '本 pyc 100% 一致，豁免复现实例'
- 生成 `__init__OK.py`（若 single 命令已生成则跳过）
- 更新 pyc_index.json（decompile_status=ok / bytecode_match_rate=1.0 / ok_py_generated=true / last_tested_round=2）
- 跳过步骤 4-5"

本 pyc 已满足全部豁免条件：
- ✅ `__init__OK.py` 已由 single 命令生成，位于 `F:/Downloads/pythoncdc-main/site-packages/IQCommon/api/__init__OK.py`
- ✅ `py_compile` 验证通过
- ✅ `pyc_index.json` 已更新：`decompile_status=ok` / `bytecode_match_rate=1.0` / `ok_py_generated=true` / `last_tested_round=2`
- ✅ 未修改 `__init__OK.py` 文件内容
- ✅ R01 的 `IQCommon/__init__.pyc` 条目保持不变

## 7. 缺陷根因分析

**无**。本 pyc 100% 一致，无需根因分析。

### 备注

本 pyc 是一个极简的空 `__init__.py` 模块（仅 `pass`），字节码仅含 `RESUME` + `LOAD_CONST None` + `RETURN_VALUE` 三条指令，不涉及 R01 残留的两个缺陷场景（except handler 返回值丢失 / elif 链 BoolOp 拆分）。因此本 pyc 无法用于验证 R01 残留缺陷的修复情况，仅作为批量进度推进的一个 ok 节点。

R01 残留缺陷需在后续含有 try/except 与 elif 链的 pyc（如 `IQCommon/api/base_api.pyc`、`IQCommon/api/check_strategy.pyc` 等）中进一步复现与定位。
