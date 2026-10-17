import io

TEXT = u"""9. rv7_02 三元操作数链式比较（r2fix9 4/4；回归 42/42、负对照 60/60）：本批根因 =
   链式比较的可比较操作数由**三元表达式**经外栈供给时，既有链式比较重建器全部不接手——
   a) chain_two_ternary（(a if c1 else b) < (x if c2 else y) < c）：链头 @22 [SWAP 2,
      COPY 2, COMPARE_OP 0(<), JUMP_IF_FALSE_OR_POP→cleanup]，cleanup @44 [SWAP 2,
      POP_TOP]，merge @48 RETURN_VALUE；两个操作数分别由 TernaryRegion T1@0
      （merge=@12）与 T2@12（merge=@22、merge_context='compare'、
      vt='__compare_target__'）以外栈值供给（头块无任何 LOAD 前导），
      _build_chained_compare_from_region_data 依赖的 region.chained_left_instr 为空
      → None；IfRegion@22 被降级为 `if (x if c2 else y): pass`，T1 裸 Expr 外漏。
   b) chain_three_ternary（(a if c1 else b) <= (x if c2 else y) < (m if c3 else n)）：
      宿主是 BoolOpRegion@22（op_chain=[(22,'and')] 单成员，非 IfRegion）；链段比较块
      @44 前无操作数指令——第三操作数 (m if c3 else n) 以**值钻石**（@34 LOAD c3 条件
      跳 → @38 LOAD m 跳 join / @42 LOAD n 直落）到达 @44 COMPARE_OP；
      _detect_chained_compare_pattern 在 @34 无 COMPARE_OP 处断链 → None。
   修复（标签 [B98-V3R2]，判据均为同层结构事实）：
   ① 新方法 _try_build_ternary_operand_chained_compare(cc_block, ops, chain_blocks,
      merge_hint)：头块非噪声首三指令 == [SWAP(2), COPY(2), 比较指令族] 且末 ∈
      SHORT_CIRCUIT_JUMP_OPS；cleanup=跳转目标块 [SWAP,POP_TOP]；merge 值上下文为
      RETURN_*/STORE_*；沿 merge 链反查提供者——T2=TernaryRegion(merge is cc_block)、
      T1=TernaryRegion(merge is T2.condition_block)，均要求
      _compute_ternary_cond_preload_exprs 为空；left/mid 由 _build_nested_ternary_expr
      重建；comparators=[mid]+逐链段块（三元=merge 命中的嵌套三元 / 前缀 LOAD 重建 /
      值钻石内联）；新增 _extract_inline_ternary_operand_at 重建值钻石（真路径块
      JFL→join、假路径直落、共同前驱 p 的条件跳正常后继集恰 {t,f}）；命中后标记全部
      被消费块（T1/T2/T3.blocks、钻石块、cleanup、链段块），merge 归调用方。
   ② 两处消费者接入：W1=_build_chained_compare_from_region_data 内（IfRegion 宿主：
      _generate_if → _generate_value_context_chain_compare_assign R82 return 分支）；
      W2=_try_build_chained_compare_in_boolop 的 [R106] 回落内（BoolOpRegion 宿主）。
   ③ 发射端抑制守卫 _ternary_chain_compare_host（+静态判定
      _is_ternary_chain_compare_host_block）：TernaryRegion 的 merge 链上溯命中链式比较
      宿主块且恰两个提供者时，该三元不得独立发射（区域迭代序 entry@0/@12 先于宿主
      @22，否则裸 Expr 先出）；_generate_region TernaryRegion 分支改为**代持交权**——
      与 [R59-B Fix2] 同构把宿主结构区域（IfRegion/BoolOpRegion，entry is merge_block）
      就地生成并返回其 AST，比较消费者在宿主生成中以 T1/T2 区域图引用重建完整
      Compare。非命中形状（如 `if (x if c else y):` 普通条件三元、中段单独三元
      `0 < T < 10`）守卫不触发，行为逐位不变（C3）。
   验证：AST chain_two = Return(Compare(IfExp, ['<','<'], [IfExp, c]))、chain_three =
   Return(Compare(IfExp, ['<=','<'], [IfExp, IfExp]))，无裸 Expr 前导；stamp
   r2fix9_rv702 4/4；回归 r2fix9_reg 42/42（e01 15 + e02 18 + b98_resid 5 + 最小重现
   _rv7m 4）；负对照 r2fix9_negctl 60/60；r2fix9_rest 红集合与 r2fix7_rest 逐项一致
   （无回归）。

rv7_02 进度：r2fix7_rest 2/4 → r2fix9 4/4（本批全绿）。

"""

with io.open(r'.trae\specs\attain-true-completeness\rounds\round2\FIX.md', 'a', encoding='utf-8', newline='\n') as f:
    f.write(TEXT)
print('APPENDED')
