# 控制流反编译快速参考

## 当前状态
- **通过率**: 25.25% (25/99)
- **基础案例**: 17/20 (85%)
- **两层嵌套**: 6/40 (15%)
- **三层嵌套**: 2/29 (6.9%)
- **复杂案例**: 0/10 (0%)

---

## 核心函数速查

| 函数 | 用途 | 关键参量 | 常见错误 |
|------|------|----------|----------|
| `_emit` | 节点分发 | current_offset, node_type | 节点添加到错误块 |
| `_pop_jump_forward_if_false` | if-elif-else | body_start, body_end, else_start, else_end | else范围计算错误 |
| `_pop_jump_backward_if_true` | while循环 | while_body_start, while_body_end | body_end未减2 |
| `_for_iter` | for循环 | for_body_start, for_body_end, for_else_start, for_else_end | else范围检测失败 |
| `_push_exc_info` | try-except | try_body_start, try_body_end | 预try节点查找失败 |
| `_store_fast` | 变量赋值 | current_offset, _chain_assign_offset | 偏移量传递错误 |
| `_find_else_end` | 查找else结束 | body_end | NOP处理不当 |

---

## 关键参量速查

### 范围检查公式
```python
# if/for/while/try body范围
body_start <= current_offset < body_end

# else分支范围
else_start <= current_offset < else_end

# 嵌套结构（外层包含内层）
outer_body_start <= inner_body_start < inner_body_end <= outer_body_end
```

### 栈操作
```python
# if栈
_if_stack.append({'node': if_node, 'body_start': bs, 'body_end': be, 'else_end': ee})

# for栈
_for_stack.append({'node': for_node, 'body_start': bs, 'body_end': be, 
                   'else_start': es, 'else_end': ee})
```

---

## 修复速查表

| 问题现象 | 可能原因 | 修复方法 | 修复ID |
|----------|----------|----------|--------|
| 预try节点找不到 | end被更新 | 只比较start | FIX-001 |
| 空except未创建 | 无CHECK_EXC_MATCH | 检测POP_TOP | FIX-002 |
| while范围错误 | body_end未减2 | 减去指令长度 | FIX-003 |
| 节点添加到while后 | current_block未恢复 | 恢复main_block | FIX-004 |
| 节点添加到for后 | current_block未恢复 | 恢复main_block | FIX-011 |
| RETURN在else中 | 未排除RETURN | 检测RETURN_VALUE | FIX-005 |
| 条件表达式识别错 | 未检测运算 | 检测BINARY_OP | FIX-006 |
| 空else未生成 | NOP未处理 | 处理NOP指令 | FIX-007, FIX-008 |
| 空except类型错 | 使用Exception | 使用None | FIX-009 |
| 赋值偏移错误 | 使用当前offset | 传递实际offset | FIX-010 |

---

## 调试技巧

### 1. 启用调试输出
```python
from parsers import ast_builder
ast_builder.DEBUG = True
ast_builder.DEBUG_FILTER = ["_emit", "_for_iter"]  # 或 [] 表示全部
```

### 2. 查看字节码
```bash
python -m dis tests/control_flow_cases/basic/__pycache__/case_name.cpython-311.pyc
```

### 3. 创建调试脚本
```python
# debug_case.py
from core.pyc_loader_v2 import load_pyc_file_v2
from parsers.ast_builder import ASTBuilder

module = load_pyc_file_v2('path/to/case.pyc')
builder = ASTBuilder(module, module.code.get())
ast = builder.build_from_code(module.code.get())
print(ast.to_code())
```

### 4. 分析失败报告
```bash
python scripts/analyze_failures.py test_reports/test_report_*.json
```

---

## 常见错误模式

### 错误1: 指令数量不匹配
**症状**: 原始19条指令 vs 反编译21条指令
**原因**: 节点被重复添加或添加到错误块
**解决**: 检查 `_emit` 方法中的范围检测逻辑

### 错误2: 跳转目标不匹配
**症状**: JUMP_FORWARD目标 52 vs 反编译 48
**原因**: else_end计算错误
**解决**: 检查 `_find_else_end` 方法

### 错误3: 语法错误
**症状**: 编译反编译输出失败
**原因**: 生成的代码语法不正确
**解决**: 检查AST节点的 `to_code` 方法

### 错误4: 节点缺失
**症状**: 反编译结果缺少某些语句
**原因**: 节点未被添加到AST
**解决**: 检查 `_emit` 方法中的节点添加逻辑

---

## 测试-修复-记录流程

```
1. 运行测试
   python scripts/run_full_test_suite.py

2. 分析失败
   python scripts/analyze_failures.py <report.json>

3. 定位问题
   - 查看原始代码
   - 对比字节码
   - 创建调试脚本

4. 实施修复
   - 添加调试信息
   - 修改代码
   - 验证修复

5. 更新文档
   - 更新修复记录
   - 更新参量表格
   - 记录新模式

6. 循环测试
   - 重新运行测试
   - 验证通过率提升
```

---

## 文档索引

| 文档 | 内容 | 路径 |
|------|------|------|
| 控制流模式 | 详细模式说明 | `docs/patterns/control_flow_patterns.md` |
| 参量对照表 | 参量表格 | `docs/patterns/control_flow_params_table.md` |
| 快速参考 | 速查卡片 | `docs/patterns/quick_reference.md` |
| 修复注册表 | 修复记录 | `docs/fixes/fix_registry.md` |

---

## 待修复问题（按优先级）

### 🔴 高优先级
1. instruction_count不匹配 (74个案例)
2. for-else结构问题
3. 跳转目标计算错误

### 🟡 中优先级
4. FOR_ITER参数错误
5. 复杂嵌套结构

### 🟢 低优先级
6. 语法错误优化
7. 代码格式化

---

*最后更新: 2026-03-01*
