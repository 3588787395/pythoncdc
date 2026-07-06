# 修复7个嵌套区域测试失败 - 验证清单

## 根因分析验证
- [ ] n07 根因分析完成：`if v is None: break` 条件反转 + `n = v` 错位 + 多余 `else: return None`
- [ ] n09 根因分析完成：try-except 后多余 `len(data)` 语句
- [ ] n10a/n10n 根因分析完成：内层 for 不在 if 内 + for-else 混淆 + 重复 if 条件
- [ ] n13a/n13n 根因分析完成：BoolOp 拆分 + 循环后语句错位 + 多余 return None
- [ ] n15 根因分析完成：`i = 0` 丢失 + 多余 if-else break

## 修复验证
- [ ] n07 try_for_break_n_stopiteration 字节码指令数匹配（26 vs 26）
- [ ] n09 while_try_except_a_indexerror 字节码指令数匹配（35 vs 35）
- [ ] n10a for_if_for_break_a_b 字节码操作码匹配（无 LOAD_GLOBAL vs LOAD_FAST 差异）
- [ ] n10n for_if_for_break_n_m 字节码匹配
- [ ] n13a try_for_if_break_a_indexerror 字节码指令数匹配（29 vs 29）
- [ ] n13n try_for_if_break_n_valueerror 字节码匹配
- [ ] n15 while_if_try_except_a_b_indexerror 字节码指令数匹配（54 vs 54）

## 回归验证
- [ ] nested 测试套件通过率 ≥97.5%（不低于当前基线）
- [ ] for_loop 测试套件通过率 ≥98.4%（3f，不增加失败数）
- [ ] 全量10区域测试无回归
