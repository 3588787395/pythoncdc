# R05 修复报告 — Pattern M 装饰器调用坍缩

## 1. 修复概述

| 字段 | 值 |
|---|---|
| 轮次 | R05 (rcm-r05) |
| 目标 pyc | `IQCommon/data/base_storage.pyc` |
| 缺陷模式 | Pattern M — 装饰器调用坍缩（`@deco()` → `@deco`） |
| 修复文件 | `core/cfg/code_generator.py`（主修复）、`core/cfg/region_ast_generator.py`（防御性增强） |
| 修复方法 | `_generate_decorator`（主）、`_reconstruct_decorator_chain`（防御） |
| 修复前 pyc match_rate | 80.00% (4/5) — BaseStorage 类体不一致 |
| 修复后 pyc match_rate | **100.00%** (5/5) — 升级为 ok |
| 修复前 repro | 7 DEFECT-REPRO / 5 NO-DEFECT |
| 修复后 repro | **11 NO-DEFECT** / 1 DEFECT-REPRO（repro_11 Pattern M2 残留） |
| 回归测试 | 1 failed, 112 passed, 14 errors（== R04 基线，无退化） |

## 2. 缺陷定位

### 2.1 现象

`base_storage.pyc` 的 `BaseStorage` 类使用 `@lru_cache()` 装饰 `__new__`。反编译产物错误输出 `@lru_cache`（无括号），丢失 `PUSH_NULL/PRECALL/CALL` 三指令，导致类体字节码不一致（true_diffs=27）。

### 2.2 双路径分析

装饰器处理存在两条路径：

1. **AST 节点路径**（`_generate_function_def` → `_generate_decorator`）：dict FunctionDef 先转换为 ASTFunctionDef（ASTNode），再由 `_generate_decorator` 渲染 `@expr` 行。
2. **dict 路径**（`_generate_function_def_dict` → `_generate_expression`）：直接处理 dict 节点。

调试（`_r05_debug_codegen.py` monkeypatch 追踪）确认 **AST 节点路径被实际使用**：

```
[TRACE _generate_decorator] in=<ASTName object> -> out='deco'
[TRACE _generate_decorator] in=<ASTCall object> -> out='deco'   ← BUG: ASTCall(deco()) 渲染为 'deco'
```

dict 路径 `_generate_function_def_dict` 未被调用。

### 2.3 AST 正确性验证

`_r05_debug_trace.py` 追踪 `region_ast_generator._build_function_def` 确认 AST 层产出正确：

```
[TRACE _build_function_def] result.decorator_list=[{'type': 'Call', 'func': {'type': 'Name', 'id': 'deco'}, 'args': []}]
```

即 AST 层已正确产出 `Call(func=Name('deco'), args=[])` 节点（表示 `@deco()`）。缺陷在代码生成层，不在 AST 重建层。

### 2.4 根因

`core/cfg/code_generator.py` 第 2143-2146 行（修复前）：

```python
if args_code:
    return f'{func_code}({", ".join(args_code)})'
else:
    return func_code    # ← BUG: ASTCall 零参时丢弃调用括号
```

该逻辑源自历史「F08 修复：无参装饰器不加括号」。F08 错误地将两种语义不同的形式混为一谈：
- `@deco` → ASTName 节点（无调用，1 个 CALL：`deco(func)` 应用）
- `@deco()` → ASTCall 节点（零参调用，2 个 CALL：先 `deco()` 再应用）

两者字节码不同（`@deco()` 含 `PUSH_NULL/PRECALL/CALL`，`@deco` 不含）。ASTCall 节点语义即「调用」，无论是否有参数都必须发射括号 `()`。F08 在 `args_code` 为空时 `return func_code` 将 `@deco()` 坍缩为 `@deco`。

## 3. 修复方案

### 3.1 主修复：`core/cfg/code_generator.py` `_generate_decorator`

**修改位置**：`_generate_decorator` 方法的 ASTCall 分支（原第 2143-2146 行）。

**修改内容**：移除 `if args_code / else` 分支，ASTCall 始终返回 `f'{func_code}({", ".join(args_code)})'`（args 为空时为 `func_code()`）。

**修改前**：
```python
if args_code:
    return f'{func_code}({", ".join(args_code)})'
else:
    return func_code
```

**修改后**：
```python
# [R05 fix] Pattern M: ASTCall 节点语义即「调用」，无论是否有参数都
# 必须发射调用括号 ()。@deco()（零参调用）与 @deco（无调用）字节码
# 不同：前者含 PUSH_NULL/PRECALL/CALL，后者不含。ASTCall → @deco()，
# ASTName → @deco。旧版在此分支 args 为空时 return func_code（丢括号）
# 导致 @deco() 坍缩为 @deco。
return f'{func_code}({", ".join(args_code)})'
```

**docstring 更新**：扩展为 7 节模板（算法依据/归约顺序/唯一归属判定/嵌套处理/入口引用语义/反编译流程/R05 fix），明确 ASTCall 与 ASTName 的语义区分。

### 3.2 防御性增强：`core/cfg/region_ast_generator.py` `_reconstruct_decorator_chain`

**修改位置**：`_reconstruct_decorator_chain` 方法的 CALL 检测逻辑。

**修改内容**（本轮已应用，作为 AST 层防御性增强）：
- 新增 `has_decorator_call` 列表，独立跟踪每个装饰器条目是否被调用（检测 LOAD 与 MAKE_FUNCTION 之间的 CALL）。
- CALL 检测从 PRECALL/PUSH_NULL 跳过列表中分离，避免零参 CALL 被当作噪声跳过。
- 参数检测循环从 `range(num_decorators - 1)` 扩展为 `range(num_decorators)`，覆盖最内层装饰器。
- CALL 存在即发射 Call 节点（args 可为空）。

**说明**：此增强确保 AST 层在 bytecode 路径（`_reconstruct_decorator_chain`）也能正确识别零参调用。实际 base_storage.pyc 的修复主要由代码生成层（3.1）完成，但此增强保证了 AST 层的健壮性。

### 3.3 不修改的部分

- ASTName 分支：`return node.name`（`@deco` 无括号，正确，不变）
- ASTAttribute 分支：`return f'{value_code}.{node.attr}'`（`@x.y` 无括号，正确，不变）
- dict 路径 `_generate_function_def_dict`：已通过 `_generate_expression` 正确发射 `deco()`，不变

## 4. 回归测试结果

### testqouter/round1/ 测试矩阵

```
Post-R05 (with fix):  1 failed, 112 passed, 105 warnings, 14 errors in 33.12s
R04 基线:             1 failed, 112 passed, 105 warnings, 14 errors in 49.70s
```

- **1 failed**: `test_r2q_10_with_open_read.py` — FileNotFoundError: 'nonexistent.txt'（运行时文件缺失，非反编译缺陷，pre-existing）
- **14 errors**: `test_r2q_03/04/05/06/07/08/17/18/21/25/27/28/30/34` — 反编译产物含语法错误（pre-existing，与 R03/R04 一致）
- **112 passed**: 与 R04 一致

**结论**：无回归（post-R05 == R04 基线），R05 修复未引入新失败。

> 注：`detail_test.py` 在 pytest 收集时因模块级代码重新编译 pyc 触发 "Failed to decompile" RuntimeError（独立运行该脚本正常）。此为测试框架收集期 artifact，非反编译缺陷，通过 `--ignore=testqouter/round1/detail_test.py` 排除后获得真实回归结果。

### 模块编译检查

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"
imports OK
```

### 最小复现实例验证

```
12 repros: 11 NO-DEFECT, 1 DEFECT-REPRO
  - Pattern M (single @deco() collapse): 6/6 NO-DEFECT (repro_01/02/05/08/09/10 fixed)
  - Pattern M2 (stacked @deco() nesting): 0/1 NO-DEFECT (repro_11 残留)
  - Controls: 5/5 NO-DEFECT (repro_03/04/06/07/12)
```

### 目标 pyc 验证

```
base_storage.pyc: 100.00% (5/5), decompile_status=ok
```

## 5. 算法 4 原则合规

- **自底向上归约**: ✓ 未改变区域归约顺序；修复在 AST → 源码生成阶段（最末期），不影响区域识别
- **每块唯一归属**: ✓ ASTCall 节点唯一归属「被调用的装饰器」`@deco(...)`，ASTName/ASTAttribute 唯一归属「未被调用的装饰器」；渲染由 AST 节点类型唯一决定
- **嵌套即抽象节点**: ✓ 装饰器 Call 节点的 func 槽位引用被调用装饰器子节点（Name/Attribute/嵌套 Call）；Attribute 链递归渲染
- **入口引用语义**: ✓ 父 FunctionDef.decorator_list 通过 `@expr` 行引用装饰器子节点；Call 的 func 槽位引用被调用装饰器子节点

## 6. 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀: **0 新增**
  - 修改的方法名 `_generate_decorator` / `_reconstruct_decorator_chain` 不含禁止前缀
- 硬编码深度上限: **0 新增**
- 跨区域启发式: **0 新增**（渲染由 AST 节点类型决定，非实例特征；ASTCall → 括号 是语法必需，非启发式）
- 后处理补丁: **0 新增**（在代码生成阶段修复，非后处理）
- 针对特定 pyc 的硬编码绕过: **0 新增**

## 7. docstring 更新

### `_generate_decorator`（`core/cfg/code_generator.py`）

扩展为 7 节模板：
1. 算法依据：AST 类型唯一决定语法形式（ASTName → `@name`，ASTCall → `@name(...)`），附 CPython 字节码差异说明
2. 归约顺序：AST → 源码生成阶段（最末期）
3. 唯一归属判定：ASTCall → 被调用装饰器（必发射括号），ASTName/ASTAttribute → 未被调用装饰器
4. 嵌套处理：Attribute 链递归
5. 入口引用语义：父 FunctionDef 通过 `@expr` 行引用装饰器子节点
6. 反编译流程：decorator AST 节点 → 按 AST 类型渲染
7. [R05 fix] Pattern M：详细记录根因（F08 conflation）、修复（ASTCall 始终发射括号）、ASTName 不受影响

### `_reconstruct_decorator_chain`（`core/cfg/region_ast_generator.py`）

新增第 7 节 [R05 fix] Pattern M：记录 has_decorator_call 跟踪、CALL 检测分离、循环扩展、零参 Call 发射。

## 8. 残留问题

### Pattern M2 — 堆叠装饰器嵌套错误（repro_11，本轮未修复）

**现象**：`@deco1() @deco2() def m` 被错误反编译为 `@deco2(deco1()) def m`（deco1() 被当作 deco2 的参数）。

**根因（初步）**：缺陷在表达式重建阶段（`ExpressionReconstructor` 或区域 AST 生成），传给 `_build_function_def` 的 `decorator` 参数已被错误嵌套为 `deco2(deco1())(m)` 而非 `deco1()(deco2()(m))`。`_extract_decorators` 忠实处理了错误的 Call 树。

**影响范围**：base_storage.pyc 无此模式（仅单个 `@lru_cache()`），不影响本轮 100% 结果。

**后续计划**：下一轮深入表达式重建的 Call 树构建逻辑，定位堆叠装饰器应用的嵌套错误。

### 累计残留（跨轮）

- klinedata.pyc 仍为 partial（53.33%，21 mismatches，Pattern A2/B/C/E，R04 残留）
- Pattern M2（repro_11，本轮新增残留）
