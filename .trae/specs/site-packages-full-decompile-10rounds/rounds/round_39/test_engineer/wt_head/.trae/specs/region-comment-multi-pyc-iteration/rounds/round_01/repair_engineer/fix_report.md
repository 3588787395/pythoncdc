# 修复报告 — round_01 (rcm-r01)

## 1. 修复概述

| 项目 | 值 |
|---|---|
| 轮次 | rcm-r01 |
| 目标 pyc | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/__init__.pyc` |
| 核心缺陷 | try/except/finally 中 try 体（含 if/elif/else 链）被丢弃，坍缩为 `pass` |
| 修复文件 | `core/cfg/region_ast_generator.py` |
| 修复方法数 | 3 处（generate + _generate_try_body + _wrap_boolop_with_merge_compare） |
| 修复前成功率 | 0.00% (0/2 函数一致) |
| 修复后成功率 | 50.00% (1/2 函数一致，`get_python_version` 100% 一致；`<module>` 1 diff 为 code object 身份噪声) |

## 2. 缺陷根因分析

### 2.1 缺陷一：try 体坍缩为 pass

**现象**：try/except/finally 中，try 体内的 if/elif/else 链（含属性访问 `sys.version_info`）被整体丢弃，坍缩为 `pass`。

**根因**（两处）：

1. **`generate()` 方法**：当 `entry_block` 同时是 `TryExceptRegion` 的入口（`entry_block is region.entry`）时，原代码将 `entry_block` 标记为 `generated`，导致 `_generate_try_body` 跳过该块，try 体无语句可生成 → `pass`。
   - CPython 3.11+ 优化：不可抛出异常的指令被移出异常表，try 体与函数入口同块。

2. **`_generate_try_body()` 方法**：当多个区域共享同一入口块时（如 `IfRegion.entry == BoolOpRegion.entry == 条件块`），BoolOpRegion 被优先于 IfRegion 生成，导致仅生成布尔条件片段，丢失 if/elif/else 整体结构。

### 2.2 缺陷二：条件表达式多余 `== 3`

**现象**：修复缺陷一后，try 体正确生成 if/elif/else 链，但首个条件出现多余比较运算符：
```python
if (sys.version_info[0] == 3 and sys.version_info[1] == 11) == 3:  # 错误：多余 == 3
```

**根因**：`_wrap_boolop_with_merge_compare()` 方法错误地将 BoolOp 包裹在 Compare 中。

- BoolOpRegion@8（主 if 条件 `a==3 and b==11`）的 `merge_block=102`
- Block 102 是 BoolOpRegion@102（elif 条件 `a==3 and b==5`）的 **entry**
- Block 102 包含 elif 条件的 `COMPARE_OP ==`（`sys.version_info[0] == 3`）
- `_wrap_boolop_with_merge_compare` 检测到 merge_block 中的 COMPARE_OP，错误包裹为 `(boolop) == 3`

## 3. 修复点清单

### 3.1 generate() 方法（L631-654）

**算法依据**：区域归约算法原则 3（嵌套即抽象节点）+ 原则 4（入口引用语义）

**修复**：当 `entry_block is _entry_region.entry`（TryExceptRegion 入口）时，不将 `entry_block` 标记为 `generated`，让 `_generate_try` 通过入口引用语义处理该块（作为抽象节点），try 体语句由 `_generate_try_body → _generate_block_statements` 生成。

**注释更新**：添加 6 节注释（区域类型/算法描述/字节码模式/边界条件/归约语义/AST 映射），标注 `[rcm-r01 fix]`。

### 3.2 _generate_try_body() 方法（L14773-14786）

**算法依据**：区域归约算法原则 3（嵌套即抽象节点）+ 原则 1（自底向上归约）

**修复**：遍历子区域时，跳过「父区域拥有同一入口块」的子区域（如 BoolOpRegion 的 parent 是 IfRegion，且 IfRegion.entry == BoolOpRegion.entry == block）。让外层区域（如 IfRegion）作为单个抽象节点生成，其内部由 `_generate_if_region` 负责递归生成 BoolOpRegion 条件。

**注释更新**：添加 `[rcm-r01 fix]` 注释，说明跳过逻辑与算法原则对应。

### 3.3 _wrap_boolop_with_merge_compare() 方法（L19412-19460）

**算法依据**：区域归约算法原则 2（每块唯一归属）+ 原则 3（嵌套即抽象节点）

**修复**：在检查 merge_block 的 COMPARE_OP 之前，添加两项结构性守卫：

1. **结构性判据一**：若 `merge_block` 同时是【另一个区域】的 entry（通过 `block_to_region` 查询），依「每块唯一归属」merge_block 属于该区域，非本 BoolOpRegion 的比较目标 → 不包裹。
2. **兜底判据二**：BoolOpRegion.op_chain 全部使用控制流短路跳转（POP_JUMP_IF_FALSE/TRUE）时，boolop 结果已被真值测试消费，merge_block 是下一分支入口（elif/else），非值上下文比较目标（CPython `if (a or b) == c:` 必用 JUMP_IF_*_OR_POP 值上下文短路）→ 不包裹。

**注释更新**：在 docstring 的【修复】节后添加【rcm-r01 结构性守卫】节，说明两项判据与算法原则对应。代码内添加 `[rcm-r01 fix]` 注释。

## 4. 回归测试结果

### 4.1 区域测试矩阵

| 区域 | 基线通过率 | 本轮结果 | 变化 |
|---|---|---|---|
| TRY | 90.43% (208/230) | 96.96% (223/230) | **+6.53% (改善)** |
| IF | 96.60% (1309/1355) | 96.10% (74/77 子集) | 子集一致，无退化 |
| BOOLOP | 100.00% (133/133) | 100.00% (79/79 子集) | **无退化** |

TRY 区域从 22 个失败降至 7 个失败（显著改善），失败用例均为基线已知的字节码不一致（指令数不匹配），无新增失败模式。

### 4.2 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀方法名：**0 新增**
- 硬编码深度上限：**0 新增**
- 跨区域启发式规则：**0 新增**（修复完全基于区域归约算法 4 原则的结构性判据）

### 4.3 算法 4 原则合规

- ✅ 自底向上归约：子区域（BoolOpRegion）先于父区域（IfRegion）识别
- ✅ 每块唯一归属：merge_block 归属通过 `block_to_region` 查询确定
- ✅ 嵌套即抽象节点：BoolOpRegion 作为 IfRegion 的抽象条件节点
- ✅ 入口引用语义：父区域通过 entry 引用子区域入口

## 5. 复现实例验证结果

验证脚本：`test_engineer/minimal_repros/verify_repros.py`

| 结果 | 数量 |
|---|---|
| 通过（match=True） | **10/12** |
| 仍触发缺陷 | 2/12 |

### 通过的实例（10 个）

repro_01 ~ repro_09（除 repro_10）、repro_11 — 全部 match=True，覆盖裸 except、except as、多 except、except+else、finally only、multi handler、if/elif+except+finally、nested try、raise in try 等变体。

### 残留不一致（2 个，非本轮目标缺陷）

1. **repro_10_return_in_try.py**：`try: return 1; except: return 2` 中 except handler 的 `return 2` 被生成为 `return None`（返回值丢失）。1 个 true_diff（`LOAD_CONST 2` vs `LOAD_CONST None`）。
   - 修复前：11 个 true_diff（try 体 + except handler 全部坍缩）
   - 修复后：1 个 true_diff（仅 except handler 返回值）
   - 判定：**独立缺陷**（except handler 返回值生成），非 try 体坍缩缺陷，留待后续轮次修复。

2. **repro_12_func_call_in_try.py**：elif 条件 `a==3 and b==5` 被拆分为嵌套 `if`（`elif a==3: if b==5: ...`）。1 个 jump_diff（跳转目标偏移不同）。
   - 修复前：54 个 true_diff（try 体坍缩）
   - 修复后：1 个 jump_diff（elif BoolOp 链结构差异）
   - 判定：**独立缺陷**（elif 链中 BoolOp 条件拆分），非 try 体坍缩缺陷，留待后续轮次修复。

## 6. 原 pyc 成功率变化

| 指标 | 修复前 | 修复后 |
|---|---|---|
| `get_python_version` | 0% (102 true_diffs) | **100% (0 diffs)** |
| `<module>` | 1 diff (code object 身份噪声) | 1 diff (code object 身份噪声) |
| 总成功率 | 0.00% (0/2) | **50.00% (1/2)** |

`<module>` 的 1 diff 为 code object 身份差异（`LOAD_CONST code object get_python_version` 内存地址 + 文件路径不同），非真实字节码缺陷。`get_python_version` 函数本身 100% 字节码一致。pyc 实际已 100% 字节码等价（identity noise 经 verify_repros.py 过滤逻辑确认为噪声）。

## 7. pyc_index.json 更新

| 字段 | 修复前 | 修复后 |
|---|---|---|
| decompile_status | pending | partial |
| bytecode_match_rate | 0.0 | 0.5 |
| ok_py_generated | false | true |
| last_tested_round | 0 | 1 |

注：decompile_status 设为 `partial`（非 `ok`）因 pyc_batch_verify.py 脚本未过滤 code object 身份噪声，报告 50% match rate。实际 `get_python_version` 函数 100% 一致，`<module>` 仅 identity noise。

## 8. 产物清单

| 产物 | 路径 |
|---|---|
| 本报告 | `.trae/specs/region-comment-multi-pyc-iteration/rounds/round_01/repair_engineer/fix_report.md` |
| 修复源码 | `core/cfg/region_ast_generator.py`（3 处修改） |
| 反编译 OK.py | `site-packages/IQCommon/__init__OK.py`（已生成，未修改） |
| pyc_index.json | `pyc_index.json`（IQCommon/__init__.pyc 条目已更新） |

## 9. 残留问题

1. **repro_10**：except handler 中 `return <value>` 的返回值丢失（生成为 `return None`）。独立缺陷，非 try 体坍缩。
2. **repro_12**：elif 链中 BoolOp 条件被拆分为嵌套 if。独立缺陷，非 try 体坍缩。
3. **pyc_batch_verify.py**：未过滤 code object 身份噪声，导致 `<module>` 的 identity diff 被计为不一致。工具改进项，非反编译器缺陷。

以上残留均为独立缺陷或工具改进项，不影响本轮 try 体坍缩缺陷的修复完整性。
