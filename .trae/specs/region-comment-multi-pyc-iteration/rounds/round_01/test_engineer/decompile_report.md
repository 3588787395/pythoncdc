# 反编译报告 — round_01 (rcm-r01)

## 1. 目标 pyc 基本信息

| 项目 | 值 |
|---|---|
| pyc 路径 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/__init__.pyc` |
| pyc 大小 | 1630 字节 |
| 函数数 | 2（`<module>` + `get_python_version`） |
| Python 版本 | 3.11 |
| 原始源文件 | `./fly_docker_py311/IQCommon/__init__.py` (line 17) |
| 反编译产物 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/__init__OK.py` (499 chars) |
| decompile_status（本轮） | pending（未达 100% 一致，不更新 pyc_index.json） |

## 2. 不一致函数清单

反编译命令：`python scripts/pyc_batch_verify.py single "F:/Downloads/pythoncdc-main/site-packages/IQCommon/__init__.pyc"`

| 函数名 | 原指令数 | 反编译指令数 | jump_diffs | true_diffs | 首个差异 |
|---|---|---|---|---|---|
| `<module>` | 28 | 28 | 0 | 1 | index 23：`LOAD_CONST`(code object `get_python_version`) vs `LOAD_CONST`(code object `get_python_version`)。**注**：此为 code object 身份差异（内存地址不同），非真实缺陷——子函数 `get_python_version` 自身反编译错误导致其 code object 引用不一致。 |
| `get_python_version` | 122 | 45 | 8 | 102 | **index 13**：原 `LOAD_ATTR version_info` vs 反编译 `PUSH_EXC_INFO`。**真实缺陷**。 |

### 首个差异详情（get_python_version，index 13）
```
orig_op:   LOAD_ATTR
orig_arg:  version_info        # try 体内 if 条件 sys.version_info[0] 的起始指令
decomp_op: PUSH_EXC_INFO       # except handler 入口指令
decomp_arg: None
```
含义：原 pyc 在该位置是 try 体内 `sys.version_info` 属性访问（if/elif/else 链的起始），反编译产物在该位置已是 except handler 入口 `PUSH_EXC_INFO`——**即整个 try 体内容被丢弃，坍缩为 `pass`**。

### 反编译产物（__init__OK.py 中 get_python_version）
```python
def get_python_version():
    import traceback
    import sys
    flag = '0'
    try:
        pass                  # ← 错误：原 try 体含完整 if/elif/else 链被丢弃
    except:
        traceback.print_exc()
    finally:
        globals()['python_version'] = flag
    return flag
```

### 原 pyc 实际语义（由字节码反推）
```python
def get_python_version():
    import traceback
    import sys
    flag = '0'
    try:
        if sys.version_info[0]==3 and sys.version_info[1]==5 and sys.version_info[2]==1:
            flag = '3.5'
        elif sys.version_info[0]==3 and sys.version_info[1]==5 and sys.version_info[2]==2:
            flag = '3.5'
        elif sys.version_info[0]==3 and sys.version_info[1]==11:
            flag = '3.11'
        else:
            print('不支持该版本: Python {:s} on {:s}'.format(sys.version, sys.platform))
    except:
        traceback.print_exc()
    finally:
        globals()['python_version'] = flag
    return flag
```

## 3. 当前 pyc 成功率

| 指标 | 值 |
|---|---|
| 总函数数 | 2 |
| 一致函数数 | 0 |
| 成功率 | **0.00%** |

## 4. 累计成功率（跨所有已验证 pyc）

| 指标 | 值 |
|---|---|
| 已验证 pyc 数 | 1（本 pyc，round_01 首个） |
| 总函数数 | 2 |
| 一致函数数 | 0 |
| 累计成功率 | **0.00%** |

> 说明：本轮为 region-comment-multi-pyc-iteration 首轮，本 pyc 为首个验证目标。pyc_index.json 中其余条目 `last_tested_round=0`（未验证）。本 pyc 成功率 0.0%（未达 100%），按约束不更新 pyc_index.json 的 decompile_status，故累计成功率 = 本 pyc 成功率 = 0.00%。

## 5. 与上一轮对比

**首轮基线**（无上一轮）。

| 指标 | 基线（round_01） |
|---|---|
| 成功率 | 0.00% |
| 一致函数数 | 0 / 2 |
| 主要缺陷 | try/except/finally 中 try 体内容坍缩为 pass |

## 6. 最小复现实例验证结果

验证脚本：`minimal_repros/verify_repros.py`（函数级字节码 diff，已过滤模块级 code object 身份噪声）。

共构造 12 个最小复现实例，**12/12 全部触发缺陷**：

| 实例 | 覆盖变体 | match | 不一致函数 | orig | decomp | true_diffs | jump_diffs | 首个差异 |
|---|---|---|---|---|---|---|---|---|
| repro_01_bare_except_finally_attr | 裸 except + finally + 属性访问 | False | get_ver | 71 | 32 | 60 | 7 | LOAD_ATTR version_info vs PUSH_EXC_INFO |
| repro_02_except_as_bind | except Exception as e + finally | False | f | 89 | 50 | 73 | 12 | LOAD_ATTR version_info vs PUSH_EXC_INFO |
| repro_03_multi_exc_tuple | except (元组) + finally | False | f | 80 | 41 | 67 | 9 | LOAD_ATTR version_info vs PUSH_EXC_INFO |
| repro_04_bare_except_only | 裸 except（无 finally） | False | f | 55 | 16 | 49 | 2 | LOAD_ATTR version_info vs PUSH_EXC_INFO |
| repro_05_except_else | except + else + finally | False | f | 81 | 43 | 67 | 10 | LOAD_GLOBAL sys vs NOP |
| repro_06_finally_only | 仅 try/finally | False | f | 63 | 25 | 55 | 4 | LOAD_GLOBAL sys vs NOP |
| repro_07_multi_handler | except A + except B + finally | False | f | 85 | 46 | 67 | 13 | LOAD_ATTR version_info vs PUSH_EXC_INFO |
| repro_08_except_finally_ifelif | if/elif/else + except + finally（最接近原 pyc） | False | get_python_version | 84 | 45 | 67 | 9 | LOAD_ATTR version_info vs PUSH_EXC_INFO |
| repro_09_nested_try | 嵌套 try/except | False | f | 70 | 40 | 56 | 9 | LOAD_GLOBAL sys vs LOAD_CONST '3.11' |
| repro_10_return_in_try | try 中含 return | False | f | 12 | 3 | 11 | 0 | NOP vs LOAD_CONST |
| repro_11_raise_in_try | try 中含 raise + except + finally | False | f | 79 | 38 | 66 | 9 | LOAD_ATTR version_info vs PUSH_EXC_INFO |
| repro_12_func_call_in_try | try 中含函数调用 + except + finally | False | f | 83 | 66 | 54 | 12 | LOAD_CONST 11 vs LOAD_CONST 5 |

**核心缺陷签名**：7 个实例（repro_01/02/03/04/07/08/11）首个差异完全一致——`LOAD_ATTR version_info` vs `PUSH_EXC_INFO`，与原 pyc 的 get_python_version 缺陷签名（index 13）一一对应，确认复现成功。

## 7. 缺陷根因初步分析

### 缺陷现象
try/except/finally 结构中，**try 体内的 if/elif/else 链（含属性访问 `sys.version_info` + 下标）被整体丢弃，坍缩为 `pass`**，而 except/finally 结构本身被正确识别。反编译产物指令数从 122 降至 45，丢失的正是 try 体内的全部业务逻辑。

### 触发条件（由 12 个复现实例验证得出）
1. try 体内含 **if/elif/else 链**（单纯 `if` 不触发，需 elif 分支）；
2. try 体含**属性访问 + 下标**（如 `sys.version_info[0]`）；
3. 配合 **except**（裸 except 或具体类型）和/或 **finally**。

仅当 try 体为简单单 `if` 时不触发（首轮初始 repro_01/04/06/12 单 `if` 版本均 match=True），加入 elif 链后立即触发——说明 elif 分支处理是该缺陷的关键诱因。

### 可疑根因方法（指向 _identify_/_generate_）
反编译器 CFG 管线中 try/except/finally 的识别与生成均在 `core/cfg/` 下，可疑方法集中在两处：

1. **`core/cfg/exception_handler.py` — `identify_try_except_simplified` + `_collect_try_body_complete`**
   - `identify_try_except_simplified` 负责从异常表识别 try 块边界、收集 try_body / except_handlers / finally_body，构造 `TryExceptStructure`。
   - `_collect_try_body_complete` 内的 `is_finally_normal_path_block` 启发式（exception_handler.py L1110-1207）用于排除 finally 正常路径块。该启发式在判断"块是否含业务逻辑"时，对 if/elif/else 链中跨越 try 边界的块可能误判；同时 `analyzed_blocks` 机制（L1035-1040）会将 try_body 块标记为已分析。
   - 当 try 体内含 elif 链时，try_body 块集合可能被先前 if-region 识别pass提前消费，导致 `_collect_try_body_complete` 收集到的 try_body 仅剩 NOP 入口块，生成阶段无内容可输出 → `pass`。

2. **`core/cfg/region_ast_generator.py` — try 体 AST 生成方法**
   - region-based AST 生成器在遍历 `TryExceptStructure.try_body` 生成 try 体语句时，若 try_body 块已被标记为 analyzed（被 if-region pass 占用），会跳过这些块，最终 try 体无语句 → 生成 `pass`。
   - 这解释了为何 except/finally 结构正确而 try 体为空：结构边界识别正确，但块归属在多 pass 间冲突。

### 佐证
- first_diff `LOAD_ATTR version_info`（try 体首条业务指令）vs `PUSH_EXC_INFO`（except handler 入口）——try 体在反编译产物中**完全为空**，紧跟 try 入口即进入 except handler，与"try_body 收集仅剩入口块"假设吻合。
- repro_10（try 中 return）同样触发（orig=12 decomp=3），进一步印证 try 体生成阶段整体失效，而非仅 elif 链问题。

### 建议修复方向（供后续修复轮参考，本轮不修改）
- 在 `identify_try_except_simplified` 中确保 try_body 块优先归属 try 结构，避免被 if-region pass 提前消费；
- 复核 `is_finally_normal_path_block` 对含 `COMPARE_OP`/条件跳转的 try 体块的判定，确保含业务逻辑的块不被误排除；
- 在 region_ast_generator 的 try 体生成阶段，对 try_body 块强制重新生成（忽略 analyzed 标记），或调整 pass 顺序使 try/except 识别先于 if-region 识别。

## 8. 产物清单

| 产物 | 路径 |
|---|---|
| 本报告 | `.trae/specs/region-comment-multi-pyc-iteration/rounds/round_01/test_engineer/decompile_report.md` |
| 验证脚本 | `.trae/specs/region-comment-multi-pyc-iteration/rounds/round_01/test_engineer/minimal_repros/verify_repros.py` |
| 复现实例 01-12 | `.trae/specs/region-comment-multi-pyc-iteration/rounds/round_01/test_engineer/minimal_repros/repro_01_*.py` … `repro_12_*.py` |
| 反编译 OK.py（已存在，未修改） | `site-packages/IQCommon/__init__OK.py` |

## 9. pyc_index.json 更新

本 pyc 成功率 0.00%（未达 100%），按约束**不更新** pyc_index.json（decompile_status 保持 pending，ok_py_generated 保持 false，last_tested_round 保持 0）。
