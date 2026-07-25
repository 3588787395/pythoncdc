# Round 24 Fix Report — IF 区域 C8/C10/C1 簇修复

## 概要

| 指标 | R23 基线 | R24 当前 | Δ |
|---|---|---|---|
| if_region 失败数 | 21 | 17 | **-4** |
| if_region 通过数 | 796 | 800 | +4 |
| if_region skipped | 10 | 10 | 0 |
| ternary 失败数 | 0 | 0 | 0 |
| ternary 通过数 | 506 | 506 | 0 |
| ternary skipped | 36 | 36 | 0 |

**结论**: IF 区域 R24 净修复 4 个测试，ternary 区域 0 回归。

## 修复清单

### C8 assert_chained_cmp 系列（2 测试）
- ✅ test_adv19_assert_chained_cmp_in_if_body
- ✅ test_adv20_assert_chained_cmp_in_branches
- 根因: `_can_be_ternary_header` 在判断 assert message_block 是否被多个 AssertRegion 共享时，未区分共享 vs 独立 message_block
- 修复: `core/cfg/region_analyzer.py:12012` 在 `_can_be_ternary_header` 中区分共享 vs 独立 AssertRegion message_block
- 算法合规性: 每块唯一归属 — assert message_block 应归属唯一 AssertRegion

### C10 raise_from_complex（1 测试）
- ✅ test_adv18_raise_from_complex_in_if_body
- 根因: RAISE_VARARGS arg==2 (raise x from y) 重建时未正确分离 exc 和 cause
- 修复: `core/cfg/region_ast_generator.py:21812` 新增 `_split_raise_from_stmts` + `27221` RAISE_VARARGS arg==2 call 重建
- 算法合规性: 父引用子入口 — raise 的 exc 和 cause 分别引用各自表达式入口

### C1 嵌套 ternary 条件（1 测试）
- ✅ test_adv01_nested_ternary_cond
- 根因: 嵌套三元表达式在 if 条件中的归约冲突
- 修复: 通过 R23 已建立的 TernaryRegion/IfRegion 协调机制自动修复
- 算法合规性: 嵌套即抽象节点 — 嵌套 ternary 作为 if 条件的单抽象节点

## 修改的文件
- `core/cfg/region_analyzer.py` (+约 130 行)
- `core/cfg/region_ast_generator.py` (+约 60 行)

## 算法合规性自检（区域归约 4 原则）
- ✅ 自底向上归约
- ✅ 每块唯一归属（assert message_block 归属唯一 AssertRegion）
- ✅ 嵌套即抽象节点（嵌套 ternary 作 if 条件单抽象节点）
- ✅ 父引用子入口（raise exc/cause 引用各自表达式入口）

## 禁止项自检
- ✅ 未引入跨区域启发式特殊 case
- ✅ 未添加后处理补丁
- ✅ 未修改任何测试文件
- ✅ 未在源码添加 print/pdb/breakpoint
- ✅ 未留 _debug_*.py 调试文件

## 剩余未修复（17 个失败，留待 R25+）
- C1 嵌套 ternary 条件（5 测试）: test_adv13_ternary_*, test_adv15_ternary_*
- C4 chained_compare（1 测试）: test_adv18_if_with_chained_compare_cond
- C5 lambda_iife / mixed_complex_branches（2 测试）
- C6 with multi_ctx / for_else_break / nested_with_try（3 测试）
- C8 star_expr / tuple_return（2 测试）
- C9 dictcomp_complex_filter（1 测试）
- C10 for_continue / chained_in_check（2 测试）
- 其他（1 测试）: test_adv18_nested_ternary_in_elif_cond

## commit
待主代理 git commit + push
