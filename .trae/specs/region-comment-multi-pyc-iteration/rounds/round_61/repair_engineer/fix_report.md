# R61 修复工程师报告

## 修复目标
按区域归约算法修复 `live_future_position.pyc` 的 `load_from_kwargs` 函数中：
1. `COPY + STORE_FAST + STORE_FAST` 链式赋值模式未被识别
2. TernaryRegion 条件块中 `STORE_SUBSCR` 前缀语句未被提取

## 修复内容

### Fix 1: 链式赋值检测 (`_generate_boolop`)
**文件**: `core/cfg/region_ast_generator.py`
**位置**: `_generate_boolop` 方法，`_full_rhs = boolop_expr` 之前

**变更**:
在 BoolOpRegion 的 merge_block 中检测 `COPY + 多个 STORE_*` 模式。
当检测到时：
1. 收集所有 STORE 目标作为链式赋值目标
2. 生成 `Assign(targets=[t1, t2, ...], value=boolop_expr, is_chain_assign=True)`
3. 跳过表达式续接拼接（COPY 不是表达式操作）
4. 后续指令处理使用最后一个 STORE 的位置作为起点

**算法依据**: 区域归约算法原则 4（父引用子入口）——COPY 指令表示
链式赋值 `a = b = expr`，属于单一赋值语句，不应拆分为独立赋值。

### Fix 2: `is_chain_assign` 标志
**文件**: `core/cfg/region_ast_generator.py`
**位置**: 链式赋值 Assign 节点创建处

**变更**:
添加 `is_chain_assign: True` 标志到 Assign AST 节点，
确保代码生成器生成 `a = b = expr` 而非 `a, b = expr`（元组解包）。

### Fix 3: TernaryRegion 条件块 STORE_SUBSCR/STORE_ATTR 处理
**文件**: `core/cfg/region_ast_generator.py`
**位置**: `_generate_ternary` 方法，条件块指令扫描循环

**变更**:
1. 将 `STORE_SUBSCR` 和 `STORE_ATTR` 添加到条件块指令检查列表
2. 当检测到这些指令时，使用 `_build_statements_from_instructions`
   将前驱指令重建为独立前缀语句（pre_stmts）
3. 推进 `cond_start_idx` 跳过已处理的 STORE 指令

**算法依据**: 区域归约算法原则 2（每块唯一归属）——
条件块中的 `STORE_SUBSCR` 前驱赋值（如 `new_kwargs[key] = [price, amount]`）
归属独立 Assign 节点，不归属 TernaryRegion 条件表达式。

### Fix 4: 链式赋值后后续指令处理
**文件**: `core/cfg/region_ast_generator.py`
**位置**: `_generate_boolop` 方法，merge_block 后续处理

**变更**:
当检测到链式赋值时，后续指令处理使用最后一个 STORE 的位置
（而非第一个 STORE）作为起点，确保链式赋值后的指令
（如 `new_kwargs[...] = [price, amount]`）被正确处理。

## 字节码一致性验证
- `live_future_position.pyc`: 64/64 (100%) ✓
- `option_position.pyc`: 60/60 (100%) ✓
- `live_option_position.pyc`: 51/51 (100%) ✓
- 回归测试: 无破坏

## 算法合规性
- 原则 1（自底向上归约）: 链式赋值作为单一 AST 节点归约 ✓
- 原则 2（每块唯一归属）: STORE_SUBSCR 前驱归属独立 Assign ✓
- 原则 4（父引用子入口）: COPY 指令标志父赋值引用子表达式 ✓
