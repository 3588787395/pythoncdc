# R58 修复工程师报告

## 修复概述
在 _build_store_statement 方法中添加 STORE_ATTR 和 STORE_SUBSCR 支持，使属性赋值和下标赋值能被正确识别为赋值语句。

## 修复点

### 1. _store_ops 集合扩展 (L34851)
- 原：`('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')`
- 新：`('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR')`

### 2. STORE_ATTR 目标构造 (L34867+)
- 检测 store_instr.opname == 'STORE_ATTR'
- 从 value_instrs 中找到最后一个 LOAD_* 指令作为对象
- 构造 `{'type': 'Attribute', 'value': obj_node, 'attr': attr_name, 'ctx': 'Store'}`
- 从 value_instrs 中移除对象 LOAD，避免表达式重建错误

### 3. STORE_SUBSCR 目标构造
- 检测 store_instr.opname == 'STORE_SUBSCR'
- 从 value_instrs 中找到最后两个 LOAD_* 指令作为 key 和 object
- 构造 `{'type': 'Subscript', 'value': obj, 'slice': key, 'ctx': 'Store'}`

### 4. Assign 节点使用 STORE_ATTR 目标
- 在最终 Assign 节点构造前检查 _store_attr_target
- 若不为 None，使用 Attribute/Subscript 目标代替 Name 目标

## 算法依据
- 原则 2（每块唯一归属）：STORE_ATTR 指令的对象 LOAD 和值 LOAD 由不同语义角色区分
- 非补丁：扩展已有的 _store_ops 集合，无硬编码 offset / 无跨区域启发式

## 验证结果
- 代码编译通过
- trade.pyc: 22/23 (不变，JUMP_IF_TRUE_OR_POP 由不同代码路径处理)
- klinedata.pyc: 28/45 (不变，无回归)
- STORE_ATTR 支持是防御性修复，为后续修复 JUMP_IF_TRUE_OR_POP 模式奠定基础

## 残留
- JUMP_IF_TRUE_OR_POP 表达式赋值坍缩：由 _generate_block_statements 的表达式重建路径处理，不走 _build_store_statement。需要在该路径中添加 STORE_ATTR 识别逻辑
