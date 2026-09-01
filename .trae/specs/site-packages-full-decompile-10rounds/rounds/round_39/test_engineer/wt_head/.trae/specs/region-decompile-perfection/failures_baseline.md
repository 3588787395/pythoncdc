# 失败用例基线清单

**生成时间**: 2026-07-11

## 总体统计

- 总测试数: 1842
- 通过: 1828
- 失败: 14
- 通过率: 99.24%

## 按类别分布

| 类别 | 通过 | 总数 | 通过率 | 失败数 |
|------|------|------|--------|--------|
| L1_basic | 22 | 22 | 100.0% | 0 |
| basic | 122 | 122 | 100.0% | 0 |
| boolop | 132 | 132 | 100.0% | 0 |
| for_loop | 193 | 193 | 100.0% | 0 |
| if_region | 311 | 311 | 100.0% | 0 |
| nested | 282 | 285 | 98.9% | 3 |
| ternary | 114 | 116 | 98.3% | 2 |
| triple_nested | 112 | 120 | 93.3% | 8 |
| try_except | 229 | 230 | 99.6% | 1 |
| while_loop | 120 | 120 | 100.0% | 0 |
| with_region | 191 | 191 | 100.0% | 0 |

## 失败用例详情

### [L1] try_except/test_te046.py

- **路径**: `tests\exhaustive\try_except\test_te046.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\try_except\test_te046.py", line 9, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 指令数不匹配: 71 vs 67
原始: ['RESUME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'BEFORE_WITH', 'STORE_NAME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'BEFORE_WITH', 'STORE_NAME', 'LOAD_NAME', 'LOAD_METHOD', 'PRECALL', 'CALL', 'LOAD_NAME']
重编: ['RESUME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CON
```

### [L2] nested/test_n13try_for_if_break_a_indexerror.py

- **路径**: `tests\exhaustive\nested\test_n13try_for_if_break_a_indexerror.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\nested\test_n13try_for_if_break_a_indexerror.py", line 19, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 29 vs 32
原始: ['RESUME', 'LOAD_FAST', 'GET_ITER', 'STORE_FAST', 'LOAD_FAST', 'POP_JUMP_FORWARD_IF_NONE', 'LOAD_FAST', 'LOAD_CONST', 'COMPARE_OP', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_FAST', 'STORE_FAST', 'LOAD_CONST', 'RETURN_VALUE', 'PUSH_EXC_INFO', 'L
```

### [L2] nested/test_n13try_for_if_break_n_valueerror.py

- **路径**: `tests\exhaustive\nested\test_n13try_for_if_break_n_valueerror.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\nested\test_n13try_for_if_break_n_valueerror.py", line 19, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 33 vs 36
原始: ['RESUME', 'LOAD_FAST', 'GET_ITER', 'STORE_FAST', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_GLOBAL', 'PRECALL', 'CALL', 'LOAD_FAST', 'LOAD_METHOD', 'PRECALL', 'CALL', 'POP_TOP', 'LOAD_CONST', 'RETURN_VALUE', 'LOAD_FAST', 'STORE_FAST', 'LOAD_CONST', 'RETURN_
```

### [L2] nested/test_n15while_if_try_except_a_b_indexerror.py

- **路径**: `tests\exhaustive\nested\test_n15while_if_try_except_a_b_indexerror.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\nested\test_n15while_if_try_except_a_b_indexerror.py", line 20, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 54 vs 52
原始: ['RESUME', 'LOAD_CONST', 'STORE_FAST', 'LOAD_FAST', 'LOAD_GLOBAL', 'LOAD_FAST', 'PRECALL', 'CALL', 'COMPARE_OP', 'LOAD_FAST', 'LOAD_FAST', 'COMPARE_OP', 'LOAD_FAST', 'LOAD_FAST', 'BINARY_SUBSCR', 'POP_JUMP_FORWARD_IF_NONE', 'LOAD_FAST', 'LOAD_F
```

### [L3] triple_nested/test_tn_if_try_for_v0.py

- **路径**: `tests\exhaustive\triple_nested\test_tn_if_try_for_v0.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\triple_nested\test_tn_if_try_for_v0.py", line 17, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 指令数不匹配: 26 vs 15
原始: ['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'GET_ITER', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'PUSH_EXC_INFO', 'LOAD_NAME', 'CHECK_EXC_MATCH', 'POP_TOP', 'POP_EXCEPT', 'LOAD_CONST', 'RETURN_VALUE']
重编: ['RESUM
```

### [L3] triple_nested/test_tn_if_try_for_v1.py

- **路径**: `tests\exhaustive\triple_nested\test_tn_if_try_for_v1.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\triple_nested\test_tn_if_try_for_v1.py", line 17, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 指令数不匹配: 26 vs 15
原始: ['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'GET_ITER', 'STORE_NAME', 'LOAD_CONST', 'RETURN_VALUE', 'PUSH_EXC_INFO', 'LOAD_NAME', 'CHECK_EXC_MATCH', 'POP_TOP', 'POP_EXCEPT', 'LOAD_CONST', 'RETURN_VALUE']
重编: ['RESUM
```

### [L3] triple_nested/test_tn_while_if_for_v0.py

- **路径**: `tests\exhaustive\triple_nested\test_tn_while_if_for_v0.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\triple_nested\test_tn_while_if_for_v0.py", line 16, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 指令数不匹配: 25 vs 31
原始: ['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'GET_ITER', 'STORE_NAME', 'LOAD_NAME', 'LOAD_CONST', 'BINARY_OP', 'STORE_NAME', 'LOAD_NAME', 'LOAD_CONST']
重编: ['RESUME', 'LOAD_
```

### [L3] triple_nested/test_tn_while_if_for_v1.py

- **路径**: `tests\exhaustive\triple_nested\test_tn_while_if_for_v1.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\triple_nested\test_tn_while_if_for_v1.py", line 16, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 指令数不匹配: 25 vs 31
原始: ['RESUME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'GET_ITER', 'STORE_NAME', 'LOAD_NAME', 'LOAD_CONST', 'BINARY_OP', 'STORE_NAME', 'LOAD_NAME', 'LOAD_CONST']
重编: ['RESUME', 'LOAD_
```

### [L3] triple_nested/test_tn_with_if_for_v0.py

- **路径**: `tests\exhaustive\triple_nested\test_tn_with_if_for_v0.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\triple_nested\test_tn_with_if_for_v0.py", line 15, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 指令数不匹配: 38 vs 44
原始: ['RESUME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'BEFORE_WITH', 'STORE_NAME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'GET_ITER', 'STORE_NAME', 'LOAD_CONST', 'LOAD_CONST']
重编: ['RESUME', 'PUSH_NULL', 
```

### [L3] triple_nested/test_tn_with_if_for_v1.py

- **路径**: `tests\exhaustive\triple_nested\test_tn_with_if_for_v1.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\triple_nested\test_tn_with_if_for_v1.py", line 15, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 指令数不匹配: 38 vs 44
原始: ['RESUME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'BEFORE_WITH', 'STORE_NAME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'GET_ITER', 'STORE_NAME', 'LOAD_CONST', 'LOAD_CONST']
重编: ['RESUME', 'PUSH_NULL', 
```

### [L3] triple_nested/test_tn_with_if_while_v0.py

- **路径**: `tests\exhaustive\triple_nested\test_tn_with_if_while_v0.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\triple_nested\test_tn_with_if_while_v0.py", line 15, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 指令数不匹配: 41 vs 38
原始: ['RESUME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'BEFORE_WITH', 'STORE_NAME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_NAME', 'LOAD_CONST', 'BINARY_OP', 'STORE_NAME', 'LOAD_NAME', 'LOAD_CONST']
重编: ['RESUME', 'P
```

### [L3] triple_nested/test_tn_with_if_while_v1.py

- **路径**: `tests\exhaustive\triple_nested\test_tn_with_if_while_v1.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\triple_nested\test_tn_with_if_while_v1.py", line 15, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 指令数不匹配: 41 vs 38
原始: ['RESUME', 'PUSH_NULL', 'LOAD_NAME', 'LOAD_CONST', 'PRECALL', 'CALL', 'BEFORE_WITH', 'STORE_NAME', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_NAME', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_NAME', 'LOAD_CONST', 'BINARY_OP', 'STORE_NAME', 'LOAD_NAME', 'LOAD_CONST']
重编: ['RESUME', 'P
```

### [P1] ternary/test_ternary12_in_while.py

- **路径**: `tests\exhaustive\ternary\test_ternary12_in_while.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\ternary\test_ternary12_in_while.py", line 13, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 128, in verify_decompilation
    self.verify_region_type(self.REGION_TYPE)
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 93, in verify_region_type
    self.fail(
AssertionError: 反编译结果中未找到预期的区域类型 TERNARY (期望AST节点: ['IfExp'])
反编译结果:
if (has_more() and next_item()):
    while next_item():
        if has_more():
            pass
        else:
            break


```

### [P1] ternary/test_ternary20_complex_practical.py

- **路径**: `tests\exhaustive\ternary\test_ternary20_complex_practical.py`
- **错误**:
```
Traceback (most recent call last):
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\ternary\test_ternary20_complex_practical.py", line 18, in test_decompile
    self.verify_decompilation()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\base.py", line 132, in verify_decompilation
    self.verify_bytecode_equivalence()
  File "F:\Downloads\pythoncdc-main\tests\exhaustive\..\..\tests\control_flow_matrix\base.py", line 187, in verify_bytecode_equivalence
    self.fail(error)
AssertionError: 嵌套code object不匹配 (指令1): 指令数不匹配: 50 vs 58
原始: ['RESUME', 'LOAD_FAST', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_FAST', 'FORMAT_VALUE', 'LOAD_CONST', 'BUILD_STRING', 'RETURN_VALUE', 'LOAD_FAST', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_FAST', 'LOAD_CONST', 'BINARY_OP', 'LOAD_CONST', 'COMPARE_OP', 'LOAD_FAST', 'LOA
```

