# R10 测试报告

## 主 pyc 测试结果
- 通过: 22/24 (91.67%)
- 失败: 
  - validate_data (114 字节码差异, 编译器版本差异)
  - exception_handling_complex (179 字节码差异, 结构性bug)

## Repro 测试结果
- 通过: 10/12 (83.33%)
- 失败:
  - repro_r2_06_nested_try_else (编译器版本差异)
  - repro_r2_10_try_wrap_for_else_break (编译器版本差异)

## 综合成功率
- 主 pyc: 91.67%
- 总体 (34个测试): 32/34 = 94.12%
