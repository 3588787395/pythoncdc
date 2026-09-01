# Baseline Report: decompiler_test_comprehensive.cpython-311.pyc

## Summary
- Total functions: 24
- Matched: 21
- Success rate: 87.50%
- Mismatches: 3

## Mismatch Details

### 1. DataProcessor.validate_data (115 diffs, orig=170 instrs, decomp=142 instrs)
- **根因**: try-except 内嵌 for-else 结构中，`return False` 重复生成（第44行和45行），`for...else` 中的 `return True` 之后又有多余的 `return False`
- **表现**: 反编译产物比原始少了28条指令，说明有代码块被错误合并/跳过

### 2. DataProcessor.exception_handling_complex (179 diffs, orig=197 instrs, decomp=172 instrs)
- **根因**: 嵌套 try-except-finally + for-continue 结构中，`continue` 后面的代码被错误保留（应不可达），`if isinstance(item, str): pass else: converted = item` 结构位置错误
- **表现**: 反编译产物比原始少了25条指令，指令序列大幅偏移

### 3. DataProcessor.final_integration_test (46 diffs, orig=176 instrs, decomp=180 instrs)
- **根因**: try-except-else-finally 结构中 `else` 块的 `return results` 被错误放置，`finally` 块位置不对
- **表现**: 反编译产物比原始多了4条指令

## Common Root Causes
1. **try-except 内嵌 for-else**: 反编译器在处理 try 块内 for-else 结构时，错误处理了循环退出路径
2. **嵌套 try-except-finally**: 多层嵌套异常处理中的 finally 块位置识别错误
3. **continue 后不可达代码**: continue 后面的代码应被跳过但被错误保留
4. **try-else 块识别**: try-except-else 结构中 else 块的入口/出口识别不准确
