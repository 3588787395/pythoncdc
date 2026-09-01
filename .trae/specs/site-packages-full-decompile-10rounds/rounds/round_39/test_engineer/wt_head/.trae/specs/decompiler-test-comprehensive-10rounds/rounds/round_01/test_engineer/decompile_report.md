# 第1轮测试工程师报告

## 测试结果摘要
- 测试时间: 2026-08-19
- 总函数数: 22
- 匹配函数数: 8
- 成功率: 36.36%
- 基准成功率: 87.50%
- 成功率变化: -51.14%

## 不匹配函数详情

### 不匹配函数 1: DataProcessor
- 差异总数: 11
- 原始指令数: 132
- 反编译指令数: 132

前5个差异:
  1. 偏移 20: 原始='LOAD_CONST <code object __init__ at 0x000001D483435110, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 12>' 反编译='LOAD_CONST <code object __init__ at 0x000001D483884F30, file "decompiler_test_comprehensive_decompiled_round01.py", line 9>'
  2. 偏移 48: 原始='LOAD_CONST <code object validate_data at 0x000001D482FC4670, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 17>' 反编译='LOAD_CONST <code object validate_data at 0x000001D483685910, file "decompiler_test_comprehensive_decompiled_round01.py", line 13>'
  3. 偏移 88: 原始='LOAD_CONST <code object process_with_loops at 0x000001D482FDB490, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 52>' 反编译='LOAD_CONST <code object process_with_loops at 0x000001D483687E50, file "decompiler_test_comprehensive_decompiled_round01.py", line 45>'
  4. 偏移 108: 原始='LOAD_CONST <code object nested_function_example at 0x000001D483830C30, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 85>' 反编译='LOAD_CONST <code object nested_function_example at 0x000001D483830E30, file "decompiler_test_comprehensive_decompiled_round01.py", line 72>'
  5. 偏移 168: 原始='LOAD_CONST <code object exception_handling_complex at 0x000001D48364D9D0, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 123>' 反编译='LOAD_CONST <code object exception_handling_complex at 0x000001D4836644D0, file "decompiler_test_comprehensive_decompiled_round01.py", line 105>'

### 不匹配函数 2: validate_data
- 差异总数: 155
- 原始指令数: 173
- 反编译指令数: 145

前5个差异:
  1. 偏移 72: 原始='EXTENDED_ARG 1' 反编译='FOR_ITER 484'
  2. 偏移 74: 原始='FOR_ITER 606' 反编译='UNPACK_SEQUENCE 2'
  3. 偏移 76: 原始='UNPACK_SEQUENCE 2' 反编译='STORE_FAST i'
  4. 偏移 80: 原始='STORE_FAST i' 反编译='STORE_FAST item'
  5. 偏移 82: 原始='STORE_FAST item' 反编译='LOAD_GLOBAL isinstance'

### 不匹配函数 3: nested_function_example
- 差异总数: 1
- 原始指令数: 82
- 反编译指令数: 82

前5个差异:
  1. 偏移 46: 原始='LOAD_CONST <code object inner_calc at 0x000001D483868ED0, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 88>' 反编译='LOAD_CONST <code object inner_calc at 0x000001D483869070, file "decompiler_test_comprehensive_decompiled_round01.py", line 73>'

### 不匹配函数 4: exception_handling_complex
- 差异总数: 183
- 原始指令数: 203
- 反编译指令数: 181

前5个差异:
  1. 偏移 20: 原始='FOR_ITER 852' 反编译='FOR_ITER 756'
  2. 偏移 26: 原始='LOAD_GLOBAL isinstance' 反编译='NOP'
  3. 偏移 38: 原始='LOAD_FAST item' 反编译='LOAD_GLOBAL int'
  4. 偏移 40: 原始='LOAD_GLOBAL str' 反编译='LOAD_FAST item'
  5. 偏移 52: 原始='PRECALL 2' 反编译='PRECALL 1'

### 不匹配函数 5: generator_function
- 差异总数: 1
- 原始指令数: 73
- 反编译指令数: 73

前5个差异:
  1. 偏移 12: 原始='LOAD_CONST <code object number_generator at 0x000001D48383C2B0, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 199>' 反编译='LOAD_CONST <code object number_generator at 0x000001D48320F370, file "decompiler_test_comprehensive_decompiled_round01.py", line 159>'

### 不匹配函数 6: class_method_complex
- 差异总数: 1
- 原始指令数: 95
- 反编译指令数: 95

前5个差异:
  1. 偏移 6: 原始='LOAD_CONST <code object InternalCalculator at 0x000001D483884300, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 229>' 反编译='LOAD_CONST <code object InternalCalculator at 0x000001D483885020, file "decompiler_test_comprehensive_decompiled_round01.py", line 185>'

### 不匹配函数 7: InternalCalculator
- 差异总数: 2
- 原始指令数: 23
- 反编译指令数: 23

前5个差异:
  1. 偏移 20: 原始='LOAD_CONST <code object __init__ at 0x000001D4838142D0, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 231>' 反编译='LOAD_CONST <code object __init__ at 0x000001D483814B90, file "decompiler_test_comprehensive_decompiled_round01.py", line 187>'
  2. 偏移 36: 原始='LOAD_CONST <code object calculate at 0x000001D4838A81C0, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 235>' 反编译='LOAD_CONST <code object calculate at 0x000001D4838A8E40, file "decompiler_test_comprehensive_decompiled_round01.py", line 190>'

### 不匹配函数 8: lambda_and_comprehension
- 差异总数: 5
- 原始指令数: 45
- 反编译指令数: 45

前5个差异:
  1. 偏移 6: 原始='LOAD_CONST <code object <lambda> at 0x000001D483814570, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 277>' 反编译='LOAD_CONST <code object <lambda> at 0x000001D483816CD0, file "decompiler_test_comprehensive_decompiled_round01.py", line 222>'
  2. 偏移 12: 原始='LOAD_CONST <code object <lambda> at 0x000001D483884D50, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 278>' 反编译='LOAD_CONST <code object <lambda> at 0x000001D483885110, file "decompiler_test_comprehensive_decompiled_round01.py", line 223>'
  3. 偏移 24: 原始='LOAD_CONST <code object <listcomp> at 0x000001D483870430, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 281>' 反编译='LOAD_CONST <code object <listcomp> at 0x000001D48347EA30, file "decompiler_test_comprehensive_decompiled_round01.py", line 224>'
  4. 偏移 48: 原始='LOAD_CONST <code object <dictcomp> at 0x000001D483884E40, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 284>' 反编译='LOAD_CONST <code object <dictcomp> at 0x000001D483885200, file "decompiler_test_comprehensive_decompiled_round01.py", line 225>'
  5. 偏移 98: 原始='LOAD_CONST <code object <setcomp> at 0x000001D483472C10, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 291>' 反编译='LOAD_CONST <code object <setcomp> at 0x000001D4838D4920, file "decompiler_test_comprehensive_decompiled_round01.py", line 226>'

### 不匹配函数 9: main
- 差异总数: 2
- 原始指令数: 187
- 反编译指令数: 187

前5个差异:
  1. 偏移 234: 原始='LOAD_CONST <code object <listcomp> at 0x000001D483870830, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 395>' 反编译='LOAD_CONST <code object <listcomp> at 0x000001D483423230, file "decompiler_test_comprehensive_decompiled_round01.py", line 283>'
  2. 偏移 614: 原始='LOAD_CONST <code object <listcomp> at 0x000001D483870C30, file "d:\Desktop\ptrade相关\control_flow_tests\decompiler_test_comprehensive.py", line 410>' 反编译='LOAD_CONST <code object <listcomp> at 0x000001D483870D30, file "decompiler_test_comprehensive_decompiled_round01.py", line 292>'
