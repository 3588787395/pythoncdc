# IF Region Round 12 — 测试发现报告

## 轮次范围
- **批次 0**：修复 R11 batch 2 引入的 2 个退化（test_adv03_ternary_call_arg, test_adv03_ternary_in_subscr）
- **批次 1**：新增 15 个三元包裹表达式测试，覆盖 CALL_FUNCTION_EX / DICT_MERGE / 嵌套三元 / 链式比较等模式

## 批次 0 — 退化修复

### 退化 1: test_adv03_ternary_call_arg
- **源码**：`if f(a if c else b) > 0: ...`
- **现象**：三元表达式完全丢失（14 → 3 指令）
- **根因**：ternary 作 call arg 在 if 条件中时，merge_block 后的 CALL wrapping 未被识别
- **修复**：batch 0 (commit f5049fd)

### 退化 2: test_adv03_ternary_in_subscr
- **源码**：`if d[a if c else b] > 0: ...`
- **现象**：三元表达式完全丢失（12 → 3 指令）
- **根因**：同上 — ternary 作 BINARY_SUBSCR 操作数在 if 条件中
- **修复**：batch 0 (commit f5049fd)

## 批次 1 — 新错误清单（15 个）

### 错误 1: ternary 作为方法调用 receiver
- **测试**：test_adv12_ternary_method_call.py
- **源码**：`if (x if c else y).method(arg) > 0: ...`
- **现象**：方法调用被丢弃，仅保留 cond
- **根因**：LOAD_ATTR + PRECALL/CALL 在 ternary merge_block 后未归约到三元表达式

### 错误 2: ternary 作为 call arg 配合 BINARY_OP
- **测试**：test_adv12_ternary_call_arg_binary_op.py
- **源码**：`if f(x if c else y) + 1 > 0: ...`

### 错误 3: ternary 作为 call kwarg 配合 COMPARE_OP
- **测试**：test_adv12_ternary_call_kwarg_compare.py
- **源码**：`if f(k=v if c else w) == 0: ...`

### 错误 4: ternary 作为 call arg 配合 UNARY_OP
- **测试**：test_adv12_ternary_call_arg_unary_op.py
- **源码**：`if -f(x if c else y) > 0: ...`

### 错误 5: ternary 方法 receiver 配合 *args
- **测试**：test_adv12_ternary_method_starred_arg.py
- **源码**：`if (x if c else y).method(*args) > 0: ...`
- **根因**：CALL_FUNCTION_EX 处理器未处理 *args (Tuple/Starred 展开)

### 错误 6: ternary 方法 receiver 配合 **kwargs
- **测试**：test_adv12_ternary_method_dict_kwarg.py
- **源码**：`if (x if c else y).method(**kwargs) > 0: ...`
- **根因**：CALL_FUNCTION_EX 处理器未处理 **kwargs (DICT_MERGE 展开)

### 错误 7: ternary attr 在链式比较中
- **测试**：test_adv12_ternary_attr_in_chained.py
- **源码**：`if 0 < (x if c else y).z < 10: ...`
- **根因**：链式比较操作数含 ternary+attr 时未合并

### 错误 8: ternary 方法在链式比较中
- **测试**：test_adv12_ternary_method_in_chained.py
- **源码**：`if 0 < (x if c else y).m() < 10: ...`

### 错误 9: 嵌套三元 attr
- **测试**：test_adv12_nested_ternary_attr.py
- **源码**：`if (a if c1 else (b if c2 else d)).x > 0: ...`
- **根因**：嵌套三元共享 merge_block，内层三元被选中导致外层丢失 → 选最外层

### 错误 10: ternary subscr 配合链式比较
- **测试**：test_adv12_ternary_subscr_compare_chain.py
- **源码**：`if 0 < d[a if c else b] < 10: ...`

### 错误 11: ternary subscr + attr
- **测试**：test_adv12_ternary_subscr_attr.py
- **源码**：`if (d[a if c else b]).x > 0: ...`

### 错误 12: ternary subscr + subscr
- **测试**：test_adv12_ternary_subscr_subscr.py
- **源码**：`if d[a if c else b][e] > 0: ...`

### 错误 13: ternary attr + attr
- **测试**：test_adv12_ternary_attr_attr.py
- **源码**：`if (x if c else y).a.b > 0: ...`

### 错误 14: ternary 方法链
- **测试**：test_adv12_ternary_method_chain.py
- **源码**：`if (x if c else y).m().n() > 0: ...`

### 错误 15: 嵌套三元在 true 分支
- **测试**：test_adv12_nested_ternary_in_true.py
- **源码**：`if a if (b if c else d) else e: ...` (作为条件)

## 共性根因
1. **CALL_FUNCTION_EX 未实现**：`*args`/`**kwargs` 调用模式完全缺失
2. **DICT_MERGE 未实现**：`**a, **b` 字典合并在 if 条件中无法表达
3. **嵌套三元选择错误**：共享 merge_block 时选错 TernaryRegion 层级
4. **链式比较支持不足**：FORWARD_CONDITIONAL_JUMP 后续段未合并

## 已知限制（保留，不修复）
- test_adv03_nested_ternary_chain.py：`if 0 < (a if (b if c else d) else e) < 10:` — 三元条件本身也是三元时的重叠菱形检测，修复风险高
