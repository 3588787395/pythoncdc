# R58 测试工程师报告

## 分析目标
分析 JUMP_IF_TRUE_OR_POP 表达式赋值坍缩模式，并添加 STORE_ATTR 支持到 _build_store_statement。

## 分析结果

### JUMP_IF_TRUE_OR_POP 模式
- trade.pyc `create_trade` 函数：`x or y` 后跟 `LOAD_FAST(obj) + STORE_ATTR(attr)` 被误处理为独立表达式
- 原始字节码：`LOAD_FAST(x) → JUMP_IF_TRUE_OR_POP → LOAD_FAST(y) → LOAD_ATTR(z) → LOAD_FAST(obj) → STORE_ATTR(attr)`
- 应为：`obj.attr = x or y.z`
- 实际：`x or y.z`（表达式语句）+ 后续语句丢失
- 根因：该模式由 _generate_block_statements 的表达式重建路径处理，不走 _build_store_statement

### STORE_ATTR 支持修复
- 在 _build_store_statement 中添加 STORE_ATTR 和 STORE_SUBSCR 支持
- 修改 _store_ops 集合包含 STORE_ATTR 和 STORE_SUBSCR
- 添加 _store_attr_target 变量构造 Attribute/Subscript 目标节点
- 从 value_instrs 中移除对象 LOAD 指令，避免表达式重建错误

## 验证结果
- trade.pyc: 22/23 (不变，JUMP_IF_TRUE_OR_POP 由不同代码路径处理)
- klinedata.pyc: 28/45 (不变，无回归)
- 代码编译通过

## 累计成功率
- 保持 89.24%（无回归，无改善）
- STORE_ATTR 支持是防御性修复，可能对其他文件有帮助
