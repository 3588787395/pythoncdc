# Baseline Report: python_syntax_comprehensive_test.pyc

## Summary
- Total functions: 79
- Matched: 74
- Success rate: 93.67%
- Mismatches: 5

## Mismatch Details

### <module>
- true_diffs: 1
- jump_diffs: 0
  - {'index': 364, 'orig_op': 'LOAD_CONST', 'decomp_op': 'LOAD_CONST', 'orig_arg': '\n这是一个多行字符串，\n用于测试反编译器的字符串处理能力。\n包含特殊字符: \t\n\r\'"\\\n以及Unicode字符: 中文测试 ✅ 🎉\n', 'decomp_arg': '\n这是一个多行字符串，\n用于测试反编译器的字符串处理能力。\n包含特殊字符: \t\n\n\'"以及Unicode字符: 中文测试 ✅ 🎉\n'}

### <module>.control_flow_examples
- true_diffs: 47
- jump_diffs: 28
  - {'index': 56, 'orig_op': 'LOAD_CONST', 'decomp_op': 'LOAD_GLOBAL', 'orig_arg': '没有找到3', 'decomp_arg': 'print'}
  - {'index': 57, 'orig_op': 'CALL', 'decomp_op': 'LOAD_CONST', 'orig_arg': 1, 'decomp_arg': '没有找到3'}
  - {'index': 58, 'orig_op': 'POP_TOP', 'decomp_op': 'CALL', 'orig_arg': None, 'decomp_arg': 1}
  - {'index': 59, 'orig_op': 'LOAD_CONST', 'decomp_op': 'POP_TOP', 'orig_arg': 0, 'decomp_arg': None}
  - {'index': 60, 'orig_op': 'STORE_FAST', 'decomp_op': 'LOAD_CONST', 'orig_arg': 'counter', 'decomp_arg': 0}

### <module>.exception_handling_examples
- true_diffs: 60
- jump_diffs: 16
  - {'index': 69, 'orig_op': 'LOAD_GLOBAL', 'decomp_op': 'LOAD_GLOBAL', 'orig_arg': 'risky_operation', 'decomp_arg': 'risky_call'}
  - {'index': 74, 'orig_op': 'LOAD_GLOBAL', 'decomp_op': 'LOAD_GLOBAL', 'orig_arg': 'Exception', 'decomp_arg': 'ValueError'}
  - {'index': 77, 'orig_op': 'STORE_FAST', 'decomp_op': 'POP_TOP', 'orig_arg': 'e', 'decomp_arg': None}
  - {'index': 79, 'orig_op': 'LOAD_CONST', 'decomp_op': 'LOAD_CONST', 'orig_arg': '错误: ', 'decomp_arg': '内部错误处理'}
  - {'index': 80, 'orig_op': 'LOAD_FAST', 'decomp_op': 'CALL', 'orig_arg': 'e', 'decomp_arg': 1}

### <module>.multiple_coroutines
- true_diffs: 18
- jump_diffs: 0
  - {'index': 3, 'orig_op': 'LOAD_GLOBAL', 'decomp_op': 'LOAD_GLOBAL', 'orig_arg': 'asyncio', 'decomp_arg': 'results'}
  - {'index': 4, 'orig_op': 'LOAD_ATTR', 'decomp_op': 'RETURN_VALUE', 'orig_arg': 'gather', 'decomp_arg': None}
  - {'index': 5, 'type': 'missing_in_decomp', 'orig_op': 'LOAD_GLOBAL', 'orig_arg': 'simple_coroutine'}
  - {'index': 6, 'type': 'missing_in_decomp', 'orig_op': 'CALL', 'orig_arg': 0}
  - {'index': 7, 'type': 'missing_in_decomp', 'orig_op': 'LOAD_GLOBAL', 'orig_arg': 'simple_coroutine'}

### <module>.complex_expressions
- true_diffs: 0
- jump_diffs: 1

