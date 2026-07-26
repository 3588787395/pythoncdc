# IF Region Round 21 — Test Findings

**日期**: 2026-07-25
**测试工程师**: R21 TEST ENGINEER（仅分析，未修改任何代码）
**当前分支**: trae/agent-iter-continue
**测试范围**: tests/exhaustive/if_region/ 下 35 个失败用例

---

## Summary

- **Total failures analyzed**: 35（覆盖 Group A/B/C 三大类）
- **Root cause clusters**: 6
  - C1: if 条件中含三元 + BoolOp（and/or）时 IfRegion 被 TernaryRegion/BoolOpRegion 抢占，整 if 体坍塌为表达式（Group A + Group B 主体）
  - C2: AssertRegion 与 IfRegion 边界冲突，if body 内的 assert 把外层 if-elif-else 误判为三元/独立 raise（Group A 部分）
  - C3: 多元组解包 / 链式比较 / 切片中含三元时，ternary merge_block 未被父表达式归约（Group B）
  - C4: if-elif-else 三分支内嵌套 for-else / while-else / try-except-else 时，else 子句归属错位、循环体块被吸入 IfRegion then_blocks（Group C 主体）
  - C5: async 函数 if-elif-else 条件含 await 时 `_collect_await_predecessor_chain` 只吸收单个 setup+poll 对，多 await 链路丢失（Group C 部分）
  - C6: if body 内多 with 上下文 / 嵌套 with 时，子 WithRegion 块被平铺到外层 with 的 context 列表，破坏嵌套层级（Group C 部分）
- **Recommended fix priority**:
  - **P0**: C1（11+ 测试，IF 区域核心坍塌）, C4（15+ 测试，else 子句归属）
  - **P1**: C3（4+ 测试，三元表达式归约）, C5（3+ 测试，async if 条件）
  - **P2**: C2（3 测试，assert 边界）, C6（2 测试，with 嵌套）

---

## Finding R21-01: 三元作 if 条件 and 操作数时整 if 坍塌为表达式

- **Test**: tests/exhaustive/if_region/test_adv02_ternary_in_boolop_and.py
- **Source**: `if (a if c else d) and b:\n    pass`
- **Error**: `反编译结果中未找到预期的区域类型 IF_REGION (期望AST节点: ['If'])`，反编译结果为 `pass`
- **Root cause**: 在 `_identify_conditional_regions`（region_analyzer.py:10278-10337）中，`if (a if c else d) and b` 的 cond 块（`LOAD c, POP_JUMP_IF_FALSE → false_value`）先被 `_identify_ternary_regions`（Phase 2 之前）识别为 TernaryRegion.entry；之后 BoolOpRegion 识别把 `(ternary) and b` 抢占为 BoolOpRegion。当 `_identify_conditional_regions` 扫到末尾为 `POP_JUMP_FORWARD_IF_FALSE` 的块时，line 10315 `if any(tr.entry == block for tr in ternary_regions): continue` 直接跳过——但 cond 块的 jump target 不是 false_value 而是 ternary 的 merge，merge 又是 BoolOpRegion 的 merge_block，最终整个 if 头块被多层抢占，IfRegion 创建被跳过，then/else 体（仅 `pass`）也丢失。
- **Algorithm principle violated**: 原则 1（自底向上归约）——TernaryRegion/BoolOpRegion 应该是 IfRegion.test 的子节点而非抢占 if 头；原则 4（父引用子入口）——父 IfRegion 应通过 entry 引用 ternary/boolop 子节点，子节点不应"吃掉"父节点。
- **Fix direction**: 在 ternary/boolop 抢占 if 头块的判定中加入"if 条件上下文"判据：当候选 ternary 块的 jump target 指向 if body（含 STORE/PASS/非值消费指令）时，应让 IfRegion 优先创建并把 TernaryRegion/BoolOpRegion 作为子节点 add_child，而非跳过 IfRegion 创建。

---

## Finding R21-02: 三元作 or 操作数 + 多元 and 链导致指令数大幅丢失

- **Test**: tests/exhaustive/if_region/test_adv02_ternary_three_and.py
- **Source**: `if (a if c else d) and b and e:\n    pass`
- **Error**: `指令数不匹配: 16 vs 6`
  - 原始（16）: `RESUME, LOAD_NAME c, LOAD_NAME a, LOAD_NAME d, LOAD_NAME b, LOAD_NAME e, LOAD_CONST None, RETURN_VALUE, ...`（4 个 LOAD_NAME + 4 个隐式 return）
  - 重编（6）: `RESUME, LOAD_NAME c, LOAD_CONST None, RETURN_VALUE, LOAD_CONST None, RETURN_VALUE`
- **Root cause**: 与 R21-01 同源（C1）。三元 `(a if c else d)` 的 cond_block 被识别为 TernaryRegion.entry；外层 and 链 `(ternary) and b and e` 中三个操作数各自的 LOAD 块全部被 TernaryRegion.blocks / BoolOpRegion.blocks 吸收。`b` 和 `e` 的 LOAD_NAME 块以 JUMP_IF_FALSE_OR_POP 短路跳转，被识别为 BoolOpRegion 的 op_chain 元组。最终 IfRegion 头块未创建，then body（`pass`）和 `b`/`e` 的 LOAD 全部丢失，只剩 `LOAD_NAME c`（ternary cond）和一个 `return None`。
- **Algorithm principle violated**: 原则 1（自底向上归约）+ 原则 4（父引用子入口）。BoolOp 应被 IfRegion.test 引用，而非吞掉 IfRegion 体。
- **Fix direction**: 同 R21-01。具体地，在 `_identify_conditional_regions` 中，对末尾为 `POP_JUMP_FORWARD_IF_FALSE` 且 `block_to_region[block]` 是 `BoolOpRegion(entry==block, is_condition_context=True)` 的块，应强制创建 IfRegion（已存在 line 10438 分支，但前置 ternary 跳过使此处走不到）。

---

## Finding R21-03: 双三元作 and 操作数时 and 链断裂

- **Test**: tests/exhaustive/if_region/test_adv13_ternary_and_ternary_boolop.py
- **Source**: `if (a if c else b) and (d if e else f):\n    pass`
- **Error**: `指令数不匹配: 17 vs 13`（重编少 4 条，两个三元的 false_value 各自的 LOAD_NAME 与对应 return None 丢失）
- **Root cause**: 两个 TernaryRegion 共享外层 BoolOpRegion 的 op_chain。`_identify_boolop_regions`（推断）在处理两个三元作 and 操作数时，将第一个三元的 false_value_block（`LOAD b; JUMP_FORWARD → merge`）从 op_chain 中"修剪"掉（line 10223-10256 的 trimming 逻辑），导致第二个三元只识别出 true 分支。AST 生成时第二个三元的 IfExp.orelse 丢失。底层是 BoolOpRegion 的 op_chain 收集没有正确处理"操作数本身是 TernaryRegion"的情况——TernaryRegion 的 true/false value 块各自有 JUMP_FORWARD，被 trimming 误判为非 and 链一部分。
- **Algorithm principle violated**: 原则 3（嵌套即抽象节点）——TernaryRegion 作为 BoolOpRegion 的操作数子节点，BoolOp 不应修剪 ternary 的内部 value 块。
- **Fix direction**: 在 BoolOpRegion op_chain trimming（line 10232-10245 的 `_prev_jt` 检测）中，当 prev_cb 的 jump target 块属于某个 TernaryRegion 的 true_value_block/false_value_block 时跳过 trimming（已有的 `_prev_jt_last` SHORT_CIRCUIT 判据只覆盖了直接短路，未覆盖 ternary value 块的 JUMP_FORWARD）。

---

## Finding R21-04: 三元 + 普通变量 + 三元作 and 链，三元间被普通变量隔开

- **Test**: tests/exhaustive/if_region/test_adv13_ternary_plain_ternary_and.py
- **Source**: `if (a if c else b) and d and (e if f else g):\n    pass`
- **Error**: `指令数不匹配: 20 vs 10`（重编少 10 条，整个第二三元 + 第一个三元的 false 分支 + 多个 return 丢失）
- **Root cause**: BoolOpRegion op_chain 检测遇到中间的普通变量 `d`（其 LOAD 块以 JUMP_IF_FALSE_OR_POP 结尾）后，链检测中断，导致第二个三元 `(e if f else g)` 未被纳入 op_chain。后续 IfRegion 检测时第二个三元被独立处理（识别为另一个 IfRegion），与外层 IfRegion 冲突，最终第二个三元及其 false 分支被丢弃。这是 BoolOpRegion 链检测不连续的典型表现——`_is_boolop_ternary_candidate`（line 11678+）在遇到普通变量中断后没有继续扫描后续三元。
- **Algorithm principle violated**: 原则 1（自底向上归约）——BoolOp 应该完整覆盖所有 and 操作数，包括三元之间的普通变量。
- **Fix direction**: BoolOpRegion 链检测在遇到 JUMP_IF_FALSE_OR_POP 的 LOAD 块后，应继续沿 fallthrough 追踪后续候选块（特别是另一段 TernaryRegion.entry），将整个 and 链完整收集后再归约。

---

## Finding R21-05: 三个三元作 or 链导致三元归属冲突

- **Test**: tests/exhaustive/if_region/test_adv13_ternary_three_or_cond.py
- **Source**: `if (a if c else b) or (d if e else f) or (g if h else i):\n    pass`
- **Error**: `指令数不匹配: 16 vs 10`（重编少 6 条，第三段三元完全丢失）
- **Root cause**: 三个 TernaryRegion 的 cond_block 链通过外层 or 短路（JUMP_IF_TRUE_OR_POP）连接。前两个 ternary 被识别，但第三个 ternary 的 cond_block（`LOAD h, POP_JUMP_IF_FALSE`）被前两个 BoolOpRegion/IfRegion 抢占（block_to_region 已映射到前一个 region）。`_identify_ternary_regions` 的 `_can_be_ternary_header`（line 11644+）对已归属块的判断 `existing.can_be_ternary_header` 走到保守分支，跳过第三个 ternary 创建。AST 生成时第三个 or 操作数缺失，整个 `(g if h else i)` 丢失。
- **Algorithm principle violated**: 原则 2（每块唯一归属）+ 原则 4（父引用子入口）。BoolOp 应通过 op_chain 引用所有三个 ternary entry，第三个 ternary 不应被前两个的 region 抢占。
- **Fix direction**: 在 BoolOpRegion op_chain 收集时，对每个候选 cond_block 检测其是否构成 ternary header（含两个单表达式 value 块 + JUMP_FORWARD merge），若是则预先标记为 ternary entry，避免被前序 ternary 的 blocks 集合吸收。

---

## Finding R21-06: if body 内 assert + f-string msg 把 if-elif-else 误判为三元

- **Test**: tests/exhaustive/if_region/test_adv18_assert_in_if_body.py
- **Source**:
  ```python
  if x > 0:
      assert x < 100, f"value too large: {x}"
  elif x < 0:
      assert x > -100, "value too small"
  else:
      assert True, "should not reach"
  ```
- **Error**: `反编译结果中未找到预期的区域类型 IF_REGION`，反编译结果为：
  ```
  (x < 100 if x > 0 else x < 0)
  raise RuntimeError('value too small')
  ```
- **Root cause**: `_identify_assert_regions`（line 9476+）在扫描时，对每个 `POP_JUMP_IF_TRUE` 块都检测是否到达 `LOAD_ASSERTION_ERROR`。`if x > 0` 的 cond 块以 `POP_JUMP_IF_FALSE → elif_cond` 结尾，其 else 分支（`elif x < 0` 的 cond 块）恰好含 `LOAD_ASSERTION_ERROR`（来自 elif body 内的 assert），于是 `if x > 0` 的 cond 块被误识别为 AssertRegion.entry，cond_block 为 `x > 0`，message_block 为 elif 的 assert message。同时 `if x > 0` 的 then body 是 `assert x < 100`（其 cond 块 `x < 100` 也被识别为独立 AssertRegion），在 IfRegion 检测阶段 then body 的 assert cond 块被识别为 ternary header（POP_JUMP_IF_TRUE 跳到 merge），把 `x < 100` 和 `x < 0` 当作三元 true/false value，merge 到 `(x < 100 if x > 0 else x < 0)`。
- **Algorithm principle violated**: 原则 2（每块唯一归属）——if-elif-else 头块被 AssertRegion 错误抢占；原则 4（父引用子入口）——AssertRegion 应作为 IfRegion.then_blocks 内的子节点，而非吃掉外层 IfRegion 头。
- **Fix direction**: 在 `_identify_assert_regions` 中加入 "assert 块的 POP_JUMP_IF_TRUE 目标必须是其 message_block" 的严格判据，避免 elif 条件块（其 jump target 是下一个 elif 而非 assert message）被误识别为 AssertRegion。同时 AssertRegion 识别应跳过 `block_to_region` 中已被 IfRegion 头候选的块。

---

## Finding R21-07: if-elif-else 三分支都含 assert + chained cmp 时结构完全错乱

- **Test**: tests/exhaustive/if_region/test_adv19_assert_chained_cmp_in_if_body.py
- **Source**:
  ```python
  def f(x):
      if x > 0:
          assert 0 < x < 100, f'x out of range: {x}'
          return 'pos_valid'
      elif x < 0:
          assert -100 < x < 0, f'x too negative: {x}'
          return 'neg_valid'
      else:
          assert x == 0
          return 'zero'
  ```
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 27 vs 31`（重编多 4 条）
- **Root cause**: `_identify_assert_regions` 对每个 assert 的 chained_compare 检测（line 9537 `cc_info = self._detect_chained_compare_pattern(block)`）把 `0 < x < 100` 的 chain_blocks 收集到 AssertRegion.blocks。但外层 IfRegion 在收集 then_blocks 时，把这些 chain_blocks 当成独立块再次纳入 then_blocks（line 10646 `_collect_branch_blocks`），导致 `0 < x < 100` 的 chain 块被重复生成。同时 elif 链的 `assert -100 < x < 0` 因为 `-100 < x` 是负数常量，chain 块的 COMPARE_OP 顺序被打乱，重编后多出 4 条指令（重复的 COMPARE_OP + POP_TOP）。
- **Algorithm principle violated**: 原则 2（每块唯一归属）——chained_compare chain 块被 AssertRegion 与 IfRegion 同时纳入 blocks。
- **Fix direction**: 在 `_collect_branch_blocks` 中，跳过 `block_to_region[b]` 是 AssertRegion 且 b 在 AssertRegion.chained_compare_blocks 中的块；或在 IfRegion 收集 then_blocks 时，过滤掉 assert 子区域的 chained_compare_blocks。

---

## Finding R21-08: 链式比较中段为三元时父 Assign 表达式归约失败

- **Test**: tests/exhaustive/if_region/test_adv15_ternary_in_chain_compare_body.py
- **Source**: `if c:\n    z = 0 < (a if p else b) < 10`
- **Error**: `指令数不匹配: 19 vs 32`（重编多 13 条）
  - 原始（19）: `RESUME, LOAD_NAME c, LOAD_CONST 0, LOAD_NAME a, LOAD_NAME b, LOAD_NAME p, SWAP, COPY, COMPARE_OP, JUMP_IF_FALSE_OR_POP, LOAD_CONST 10, COMPARE_OP, SWAP, POP_TOP, STORE_NAME z, LOAD_CONST None, RETURN_VALUE, LOAD_CONST None, RETURN_VALUE`
  - 重编（32）: 多出 `POP_TOP, LOAD_CONST, LOAD_NAME a, LOAD_NAME b, LOAD_NAME p, SWAP, ...` 重复段
- **Root cause**: `_generate_value_context_chain_compare_assign`（region_ast_generator.py:6648）的 fallback 分支（line 6723+）试图从 cond_block 是某 TernaryRegion.merge_block 的情形重建 chained compare with ternary middle。但 `_build_chained_compare_with_ternary_middle`（line 6801）与父 IfRegion 的处理重复——父 IfRegion 又把 cond_block 当作普通条件块走 `_if_generate_normal`，把 ternary 的 true/false value 块当作 then/else body 生成 `Expr(POP_TOP)`，导致三元和链式比较被生成两次。
- **Algorithm principle violated**: 原则 4（父引用子入口）——父 Assign 应通过 merge_block 的 STORE_z 引用 chained compare，chained compare 通过 cond_block 引用 ternary 子节点；不应让 IfRegion 重复处理同一组块。
- **Fix direction**: 在 `_if_generate_normal` 入口检测 region 是否已被 `_generate_value_context_chain_compare_assign` 处理（generated_blocks 含 cond_block + chain_blocks + ternary blocks 时直接返回 []）。

---

## Finding R21-09: 元组解包右值为两个三元时 UNPACK 结构破坏

- **Test**: tests/exhaustive/if_region/test_adv15_ternary_in_tuple_unpack.py
- **Source**: `if c:\n    a, b = (1 if x else 2), (3 if y else 4)`
- **Error**: `指令数不匹配: 15 vs 19`（重编多 4 条）
  - 原始（15）: 两个三元各生成 true/false LOAD_CONST，再 `BUILD_TUPLE 2, SWAP, STORE_NAME a, STORE_NAME b`
  - 重编（19）: 第一个三元被独立生成为 `Expr(POP_TOP)`（即 `1 if x else 2` 作为独立语句丢弃），第二个三元才进入 BUILD_TUPLE，且 `STORE_NAME a` 提前到 BUILD_TUPLE 之前，`b` 的赋值丢失，结构完全错乱
- **Root cause**: 两个 TernaryRegion 共享同一个 merge_block（含 BUILD_TUPLE 2 + UNPACK）。`_detect_ternary_context`（line 11839）对第一个 ternary 检测 merge_block 时返回 `container_type='tuple'`，但 `_generate_ternary` 在生成时只考虑了自身 ternary 的 value，没有把同 merge 的另一 ternary 一起组装到 BUILD_TUPLE 的元素列表。第一个 ternary 被独立识别为 `Expr(IfExp)` + POP_TOP，第二个 ternary 才正确生成。父 Assign 通过 STORE_NAME a/b 引用整个 BUILD_TUPLE，但 a/b 的多目标赋值完全破坏。
- **Algorithm principle violated**: 原则 3（嵌套即抽象节点）——两个 ternary 都是父 Assign.value 的 Tuple.elts 子节点，不应被独立生成为语句；原则 4 失败。
- **Fix direction**: 在 `_identify_ternary_regions` 中检测共享同一 merge_block（含 BUILD_TUPLE/BUILD_LIST）的多个 ternary，将其归约为单一 "chained ternary container" 区域；或在 `_generate_ternary` 中扫描同 merge_block 的其他 ternary 子节点，组装为完整 Tuple/List AST。

---

## Finding R21-10: 切片下界/上界均为三元时 BUILD_SLICE 归约失败

- **Test**: tests/exhaustive/if_region/test_adv15_ternary_slice_in_body.py
- **Source**: `if c:\n    x = lst[a if p else q:b if r else s]`
- **Error**: `指令数不匹配: 16 vs 20`（重编多 4 条，两个三元各自变为 `Expr(POP_TOP)` 独立语句，BUILD_SLICE 后跟 STORE_NAME x 但 `x` 仅得到第二个三元结果）
- **Root cause**: 与 R21-09 同源（C3）。两个 TernaryRegion 的 merge_block 含 `BUILD_SLICE 2 + BINARY_SUBSCR + STORE_NAME x`。`_detect_ternary_context` 没有识别 `BUILD_SLICE` 作为容器指令（只识别了 BUILD_LIST/TUPLE/SET/MAP），导致两个 ternary 被独立处理为 `Expr(IfExp)` + POP_TOP，BUILD_SLICE 的栈位被破坏。
- **Algorithm principle violated**: 原则 3（嵌套即抽象节点）——两个 ternary 是父 Assign.value 的 Subscript.slice 的 Slice.lower/upper 子节点。
- **Fix direction**: 在 `_detect_ternary_context` 的 merge_block 扫描中加入 `BUILD_SLICE` 指令识别，返回 `container_type='slice'`；并在 `_generate_ternary` 中处理 slice 上下文，把多个 ternary 组装为 `Slice(lower=ternary1, upper=ternary2)` 节点。

---

## Finding R21-11: async if-elif-else 条件含 await + boolop 时整个 if 体丢失

- **Test**: tests/exhaustive/if_region/test_adv19_await_in_if_cond.py
- **Source**:
  ```python
  async def f(a, b):
      if await a > 0 and await b < 100:
          return 'valid'
      elif await a == 0 or await b == 0:
          return 'zero'
      elif not await a:
          return 'falsy'
      else:
          return 'other'
  ```
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 49 vs 5`
  - 重编（5）: `RETURN_GENERATOR, POP_TOP, RESUME, LOAD_CONST None, RETURN_VALUE` —— 整个 async 函数体退化为 `return None`
- **Root cause**: `_collect_await_predecessor_chain`（line 4425）从 condition_block 反向追踪 await setup+poll 块时，只收集 **一组** setup+poll 对（`poll_block` 与 `setup_block`）。但 `await a > 0 and await b < 100` 含两个 await，每个 await 各有一组 setup+poll；多 elif 链共 5 个 await。第 2-5 个 await 的 setup+poll 块未被吸收进 IfRegion.all_condition_blocks，被作为独立 BASIC 区域处理，其 SEND 指令的 conditional_successors==2 又触发 IfRegion 候选检测但被 line 10291 的 SEND+YIELD+JUMP_BACKWARD_NO_INTERRUPT 三联判据跳过。最终 if 头块未识别，整个 if-elif-else 链丢失，函数体坍塌为隐式 return None。
- **Algorithm principle violated**: 原则 1（自底向上归约）——所有 await setup+poll 块应作为 IfRegion.all_condition_blocks 子节点被归约；原则 4（父引用子入口）——IfRegion 应通过 condition_block 入口引用所有 await 子表达式。
- **Fix direction**: 修改 `_collect_await_predecessor_chain` 沿 condition_block 的所有前驱链反向迭代收集，直到不再遇到 setup+poll 对为止；或在前驱块含 GET_AWAITABLE 但不含 SEND 时，沿前驱链继续向上扫描，收集所有 await setup 块。

---

## Finding R21-12: if body 内 for-else + 嵌套 if-elif-else 时 else 子句归属错位

- **Test**: tests/exhaustive/if_region/test_adv18_for_else_nested_in_if_body.py
- **Source**:
  ```python
  def f(items):
      if flag:
          for x in items:
              if x > 0:
                  continue
              elif x < 0:
                  break
          else:
              return -1
          return x
      return 0
  ```
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 18 vs 15`（重编少 3 条，`POP_TOP, LOAD_FAST x, RETURN_VALUE` 丢失，即 `return x` 丢失）
- **Root cause**: `_identify_conditional_regions` 在收集 IfRegion.then_blocks 时（line 10668-10714 的 LoopRegion 分支），把 `for-else` 的 `else: return -1` 块从 else_blocks 中过滤掉（被 `_conditional_back_edge_blocks` / `_loop_back_edge_blocks` 误判为 loop back-edge）。同时 `return x` 块（在 for-else 之后、if body 末尾）被 `_collect_branch_blocks` 误归入 for-else 的 else 分支，导致外层 IfRegion.then_blocks 丢失 `return x`。底层是 LoopRegion 的 `else_blocks` 与 IfRegion 的 then_blocks 边界未正确切割——`_collect_branch_blocks` 沿 fallthrough 走到 for-else 之后的 `return x`，但 boundary_stop 未包含该块。
- **Algorithm principle violated**: 原则 2（每块唯一归属）——`return x` 块被 LoopRegion.else_blocks 与 IfRegion.then_blocks 同时争抢；原则 4 失败。
- **Fix direction**: 在 `_collect_branch_blocks` 收集 IfRegion.then_blocks 时，把 LoopRegion.else_blocks 加入 boundary_stop；或在 LoopRegion 识别时把 for-else 之后的"if body 内 but loop 外"的块从 LoopRegion.blocks 中剥离，归 IfRegion.then_blocks。

---

## Finding R21-13: if body 内 try-finally + 后续 if-elif 时第二个 if 被错挂到 finally

- **Test**: tests/exhaustive/if_region/test_adv18_try_finally_in_if_body.py
- **Source**:
  ```python
  def f(x):
      if x > 0:
          try:
              r = compute(x)
          finally:
              cleanup()
          if r > 100:
              return 'big'
          elif r > 10:
              return 'mid'
      return 'small'
  ```
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 34 vs 36`（重编多 2 条，`RERAISE, COPY` 之后重复了一段 cleanup 调用）
- **Root cause**: TryExceptRegion（含 finally）的 `finally_blocks` 与外层 IfRegion.then_blocks 边界冲突。`_identify_conditional_regions` line 10653-10655 在 `block not in try_handler_blocks` 时过滤 then/else 中的 handler 块，但当 if 条件块本身在 try_blocks 中时不过滤。第二个 `if r > 100` 的 cond 块位于 try-finally 之后，被误纳入 TryExceptRegion.finally_blocks（finally 块的 fallthrough 被错误延伸到第二个 if），导致 IfRegion 创建时第二个 if 被作为 finally 的子节点而非 IfRegion.then_blocks 的兄弟节点。AST 生成时 finally body 后多出一段 cleanup 调用（重复 2 条指令）。
- **Algorithm principle violated**: 原则 2（每块唯一归属）——第二个 if 头块被 TryExceptRegion.finally_blocks 与 IfRegion.then_blocks 同时争抢；原则 4（父引用子入口）失败。
- **Fix direction**: 在 TryExceptRegion 识别 finally_blocks 时，严格以 `RERAISE`/`PUSH_EXC_INFO` 之后的 cleanup 块为边界，不应沿 fallthrough 吸收 try 体之外的代码；或在 IfRegion 收集 then_blocks 时，把已识别的 TryExceptRegion.exit 加入 boundary_stop。

---

## Finding R21-14: if-elif-else 三分支各自含 for + continue/break 时分支顺序错乱

- **Test**: tests/exhaustive/if_region/test_adv19_for_continue_in_each_branch.py
- **Source**: 三分支分别为 `for x in items: if x < 0: continue; process_a(x); return 'a_done'` / `for x in items: if x > 100: break; process_b(x); return 'b_done'` / `for x in items: process_c(x); return 'c_done'`
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 44 vs 24`（重编少 20 条）
  - 原始前 7 条: `RESUME, LOAD_FAST mode, LOAD_CONST 'a', COMPARE_OP, LOAD_FAST items, GET_ITER, STORE_FAST x`（if cond + for setup）
  - 重编前 7 条: `RESUME, LOAD_FAST mode, LOAD_CONST 'a', COMPARE_OP, LOAD_FAST items, LOAD_FAST x, LOAD_CONST 0`（if cond + 内层 if cond，**for setup 被推迟**）
- **Root cause**: IfRegion.then_blocks 收集时，把内层嵌套 IfRegion（`if x < 0: continue`）的 cond 块放到外层 ForLoop.body 之前。`_collect_branch_blocks` 从 then_succ 开始 BFS，遇到 ForLoop.entry 时未把 ForLoop 视为整体子节点，而是继续遍历 ForLoop.body_blocks，把内层 IfRegion 头块错位到 For setup 之前。For setup（GET_ITER + STORE_FAST）被推迟到内层 if 之后。整个分支结构顺序错乱，最终三分支中只有第一个被部分生成，其他丢失。
- **Algorithm principle violated**: 原则 1（自底向上归约）——ForLoop 应作为 IfRegion.then_blocks 的单一抽象节点，不应被遍历拆解；原则 3（嵌套即抽象节点）失败。
- **Fix direction**: 在 `_collect_branch_blocks` 中，遇到 `block_to_region[b]` 是 ForLoop/WhileLoop/TryExcept 等"已归约区域 entry"时，把该区域作为整体加入 branch_blocks 并停止 BFS 进入其内部 blocks；仅沿 region.exit 后继继续收集。

---

## Finding R21-15: if-elif-else 三分支都含 for-else + break 时 else 子句丢失

- **Test**: tests/exhaustive/if_region/test_adv20_for_else_break_in_each_branch.py
- **Source**: 三分支各自为 `for x in items: if x > 0: break; else: return 'no_pos'; return x` 等
- **Error**: `嵌套code object不匹配 (指令1): 指令5操作码不匹配: GET_ITER vs LOAD_FAST`
  - 原始指令 5: `GET_ITER`（for setup 紧跟 if cond）
  - 重编指令 5: `LOAD_FAST`（for setup 被推迟，内层 if cond 提前）
- **Root cause**: 与 R21-14 同源（C4），且更严重——`_collect_branch_blocks` 在收集 ForLoop.body 时把 for-else 的 `else: return 'no_pos'` 块当作 IfRegion.then_blocks 的 fallthrough 块收集，导致 for-else 的 else 子句被剥离 ForLoop。同时 `return x`（for-else 之后的 if body 内代码）被错挂到 IfRegion.else_blocks。最终 for setup 与内层 if cond 顺序被打乱，指令 5 处出现 LOAD_FAST 而非 GET_ITER。
- **Algorithm principle violated**: 原则 2（每块唯一归属）+ 原则 3（嵌套即抽象节点）。ForLoop 应作为整体子节点，else 子句归 ForLoop 所有。
- **Fix direction**: 同 R21-14，加上 ForLoop.else_blocks 必须从 IfRegion.then_blocks/else_blocks 中排除。

---

## Finding R21-16: elif body 内 while-else + break 时 else 子句被错挂到 if

- **Test**: tests/exhaustive/if_region/test_adv19_while_else_break_in_elif_body.py
- **Source**:
  ```python
  def f(items, mode):
      if mode == 'a':
          return 'a_mode'
      elif mode == 'b':
          i = 0
          while i < len(items):
              if items[i] == 'stop':
                  break
              i += 1
          else:
              return 'no_stop'
          return items[i]
      else:
          return 'unknown'
  ```
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 40 vs 36`（重编少 4 条，`return 'no_stop'` 与 `return items[i]` 的部分指令丢失）
- **Root cause**: WhileLoop.else_blocks（含 `return 'no_stop'`）被 IfRegion.elif_bodies 收集时误纳入。`_collect_branch_blocks` 从 elif body 入口 `i = 0` 开始 BFS，遇到 WhileLoop 时未把 WhileLoop 视为整体子节点，继续遍历其 body 与 else_blocks。while-else 的 `else: return 'no_stop'` 块被错挂到 IfRegion.elif_bodies 末尾，而 `return items[i]`（while 之后的 elif body 代码）被剥离。整体重编少 4 条指令（`LOAD_CONST 'no_stop', RETURN_VALUE` + `LOAD_FAST items, LOAD_FAST i, BINARY_SUBSCR, RETURN_VALUE` 中的部分）。
- **Algorithm principle violated**: 原则 2 + 原则 3——WhileLoop 应作为 elif body 的单一抽象节点，else 子句归 WhileLoop 所有。
- **Fix direction**: 同 R21-14，WhileLoop.entry/exit 加入 IfRegion.branch boundary_stop，else_blocks 不被 IfRegion 收集。

---

## Finding R21-17: if body 内 try-except-else + 后续 if-elif 时 else 子句与后续 if 顺序错乱

- **Test**: tests/exhaustive/if_region/test_adv19_try_except_else_in_if_body.py
- **Source**:
  ```python
  def f(x):
      if x > 0:
          result = None
          try:
              r = process(x)
          except ValueError:
              r = -1
          else:
              r = r + 1
          if r > 100:
              return 'big'
          elif r > 0:
              return 'small'
      return 'none'
  ```
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 38 vs 40`（重编多 2 条，`else: r = r + 1` 的 `BINARY_OP + STORE_FAST` 被重复生成一次）
- **Root cause**: TryExceptRegion.else_blocks（`r = r + 1`）被 IfRegion.then_blocks 重复收集。TryExcept 识别时 else_blocks 正确纳入，但 IfRegion 收集 then_blocks 时沿 fallthrough 走过 try-except-else 后又把 else 块作为独立 BASIC 块纳入 then_blocks（未识别到 else 块已归属 TryExceptRegion）。AST 生成时 else 块的 `r = r + 1` 被生成两次（一次作为 TryExcept.else 子句，一次作为 IfRegion.then 末尾语句）。
- **Algorithm principle violated**: 原则 2（每块唯一归属）——TryExcept.else_blocks 块被两个区域同时纳入。
- **Fix direction**: 在 `_collect_branch_blocks` 中，过滤 `block_to_region[b]` 是 TryExceptRegion 且 b 在该 region.else_blocks 中的块（除非 b 是 branch 入口）。

---

## Finding R21-18: if body 内多 with 上下文 + 嵌套 with 时嵌套 with 被平铺

- **Test**: tests/exhaustive/if_region/test_adv19_with_multi_ctx_in_if_body.py
- **Source**:
  ```python
  def f(flag):
      if flag:
          with open('a') as fa, open('b') as fb:
              data = fa.read()
              with open('c') as fc:
                  data += fc.read()
              return data + fb.read()
      return None
  ```
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 97 vs 113`（重编多 16 条，第三个 BEFORE_WITH + STORE_FAST + 配套 cleanup 被重复生成）
  - 原始: 2 个外层 BEFORE_WITH + 1 个内层 BEFORE_WITH（嵌套）
  - 重编: 3 个 BEFORE_WITH 全部平铺在外层 with 的 context 列表
- **Root cause**: WithRegion 识别时，外层 `with open('a') as fa, open('b') as fb:` 的多 context 与内层 `with open('c') as fc:` 的嵌套 with 共享同一段 cleanup 块（WITH_EXCEPT_START 链）。`_identify_with_regions` 把内层 with 的 BEFORE_WITH + STORE_FAST 也吸收到外层 WithRegion 的 context 列表（line 7237 附近），未把内层 with 作为独立子区域处理。AST 生成时三个 BEFORE_WITH 全部作为外层 with 的 items，多出 16 条指令（重复的 cleanup 块）。
- **Algorithm principle violated**: 原则 3（嵌套即抽象节点）——内层 with 应作为外层 with body 的子节点，不应被平铺到外层 with 的 context 列表。
- **Fix direction**: 在 WithRegion 识别时，对每个 BEFORE_WITH + SETUP_WITH 对检测其是否位于另一个 WithRegion 的 body 内，若是则作为嵌套 WithRegion 单独识别，父 WithRegion 通过 body 引用子 WithRegion.entry。

---

## Finding R21-19: if body 内 while + yield + 嵌套 if-elif-else 时多生成隐式 return None

- **Test**: tests/exhaustive/if_region/test_adv20_yield_in_while_in_if_body.py
- **Source**: 生成器函数，if body 内 while + yield + 嵌套 if-elif-else
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 51 vs 53`（重编多 2 条，`LOAD_CONST None, RETURN_VALUE` 被多生成一次）
  - 前 19 条完全匹配
- **Root cause**: 生成器函数（含 YIELD_VALUE）的隐式 `return None` 在 IfRegion.then_blocks 末尾被重复生成。`_if_generate_full_elif_chain`（line 7057-7068）的 `trailing_return` 处理逻辑试图把 elif 链末尾的隐式 return None 剥离，但当 IfRegion 位于生成器函数内时，函数体末尾的隐式 return None 已经被外层 FunctionDef 包装生成，IfRegion 又在自己末尾生成一次。底层是 IfRegion 的 `mark_trailing_return_none` 与生成器函数的隐式 return 处理未协调。
- **Algorithm principle violated**: 原则 2（每块唯一归属）——隐式 return None 块被 IfRegion 与 FunctionDef 同时生成。
- **Fix direction**: 在 `_if_generate_full_elif_chain` 中检测当前函数是否为生成器（含 YIELD_VALUE），若是且 elif_part 末尾是隐式 return None，则剥离；同时检测 IfRegion.then_blocks 末尾的隐式 return 是否已被父 FunctionDef 标记为 generated。

---

## Finding R21-20: if body 内 while + walrus 条件 + 嵌套 if-elif-else 时多生成 return None

- **Test**: tests/exhaustive/if_region/test_adv20_walrus_in_while_cond_nested_if.py
- **Source**: if body 内 while `(x := next(it, None)) is not None` + 嵌套 if-elif-else
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 53 vs 55`（重编多 2 条，`LOAD_CONST None, RETURN_VALUE` 被多生成一次）
- **Root cause**: 与 R21-19 同源（C4）。WhileLoop 条件含 walrus + is not None，嵌套 if-elif-else 在 while body 内。IfRegion 末尾的隐式 return None 与外层 IfRegion（if items:）末尾的 return None 重复生成。
- **Algorithm principle violated**: 原则 2（每块唯一归属）。
- **Fix direction**: 同 R21-19。

---

## Finding R21-21: if-elif-else 三分支返回多元素 tuple 时 else 分支嵌套结构丢失

- **Test**: tests/exhaustive/if_region/test_adv20_tuple_return_in_branches.py
- **Source**: 三分支分别 return `(x, x+1, x*2, [x,x+1], {'k':x})` / `((x,x+1),(x+2,x+3),[x,x+4])` / `((), [], {}, {x,x+1}, (x for x in range(3)))`
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 62 vs 53`（重编少 9 条）
  - 前 6 条完全匹配
  - else 分支的 `(), [], {}, {x, x+1}, (x for x in range(3))` 中 set 与 genexp 部分丢失
- **Root cause**: else 分支 return 的 tuple 中含 BUILD_SET（`{x, x+1}`）和 genexp（`(x for x in range(3))`，含独立 code object）。IfRegion.else_blocks 收集时把 genexp 的 code object setup 块（LOAD_CONST code + MAKE_FUNCTION + GET_ITER）作为独立 BASIC 块处理，但 BUILD_SET 的元素 LOAD 块被错挂到 IfRegion.then_blocks。AST 生成时 set 字面量与 genexp 表达式丢失，return 值坍塌为更短的 tuple。
- **Algorithm principle violated**: 原则 3（嵌套即抽象节点）——genexp 应作为 return value 的子节点，set 字面量应作为 tuple 元素子节点，不应被 IfRegion 块收集拆解。
- **Fix direction**: 在 `_collect_branch_blocks` 中，遇到 BUILD_SET/BUILD_MAP/BUILD_TUPLE 后跟 GET_ITER + MAKE_FUNCTION 的 genexp pattern 时，把整段作为单一表达式块停止 BFS 拆解。

---

## Finding R21-22: if-elif-else body 内含 *args/**kwargs 混合调用时闭包 cell 处理错误

- **Test**: tests/exhaustive/if_region/test_adv20_star_expr_in_call_in_if_body.py
- **Source**:
  ```python
  def f(flag, items, extra):
      if flag == 'a':
          return sorted(*items, key=lambda x: -x, **extra)
      elif flag == 'b':
          return [f(*x, **{k: v + 1}) for x in items for k, v in extra.items()]
      else:
          return {**extra, 'sum': sum(items), 'count': len(items)}
  ```
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 42 vs 39`（重编少 3 条）
  - 原始开头: `MAKE_CELL, RESUME, LOAD_FAST flag, LOAD_CONST 'a', COMPARE_OP, ...`
  - 重编开头: `RESUME, LOAD_FAST flag, LOAD_CONST 'a', COMPARE_OP, ...` —— **MAKE_CELL 丢失**
  - 原始: `LOAD_DEREF, DICT_MERGE`（闭包引用 extra）
  - 重编: `LOAD_FAST, DICT_MERGE`（extra 被当作普通局部变量）
- **Root cause**: `f` 函数内含 lambda（`key=lambda x: -x`）和 listcomp（`[f(*x, **{k: v + 1}) for x in items for k, v in extra.items()]`），两者都是闭包，捕获外层 `extra`。CPython 编译器为 `extra` 生成 MAKE_CELL + LOAD_DEREF。但 IfRegion 收集 then_blocks 时把 MAKE_CELL 块（位于函数入口、if 之前的 prologue）误纳入 IfRegion.all_condition_blocks 或忽略，导致 MAKE_CELL 指令丢失。同时 listcomp 的 lambda 闭包 `LOAD_CLOSURE + BUILD_TUPLE` 被简化为 `LOAD_CONST + MAKE_FUNCTION + LOAD_FAST`，闭包变量变回普通局部。
- **Algorithm principle violated**: 原则 2（每块唯一归属）——MAKE_CELL prologue 块不应被 IfRegion 收集；原则 3（嵌套即抽象节点）——listcomp/lambda 闭包应作为独立 code object 子节点。
- **Fix direction**: 在 `_collect_branch_blocks` 中，跳过函数 prologue 块（含 MAKE_CELL/LOAD_CLOSURE + COPY_FREE_VARS，位于 if 之前）；listcomp 的闭包 cell 处理应识别 LOAD_CLOSURE + BUILD_TUPLE pattern 并保留为闭包语义。

---

## Finding R21-23: if body 内 async with + async for + 嵌套 if 时部分嵌套结构丢失

- **Test**: tests/exhaustive/if_region/test_adv19_async_with_async_for_in_if_body.py
- **Source**: async 函数，if body 内 `async with ... as session: async for item in session.iter(): if item.is_valid(): await process(item); return 'done'`
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 84 vs 73`（重编少 11 条）
  - 前 20 条完全匹配（async with setup + async for setup）
  - 后续 async for body 内的 `if item.is_valid(): await process(item); return 'done'` 部分指令丢失
- **Root cause**: async for 的 body 内含嵌套 IfRegion（`if item.is_valid()`），其 then body 含 `await process(item)`（自带 setup+poll 块）+ `return 'done'`。`_collect_branch_blocks` 在收集 async for body 时把 await 的 setup+poll 块拆解，部分块被 IfRegion.then_blocks 收集（重复），部分丢失。同时 async for 的 END_ASYNC_FOR cleanup 块与嵌套 IfRegion 边界未正确切割。
- **Algorithm principle violated**: 原则 1 + 原则 3——async for 应作为整体子节点，await setup+poll 应作为 IfRegion.then_blocks 内的子表达式。
- **Fix direction**: 在 async for 识别时把 body 内的嵌套 IfRegion 作为子节点 add_child，不在 `_collect_branch_blocks` 中拆解 IfRegion.then_blocks 内的 await setup+poll 块。

---

## Finding R21-24: elif body 内嵌套 with + try + if-else 时 LOAD_CONST 常量被篡改

- **Test**: tests/exhaustive/if_region/test_adv20_nested_with_try_in_elif_body.py
- **Source**: elif body 内含 `with open(...) as f: try: ... except: ...` + 嵌套 if-else
- **Error**: `嵌套code object不匹配 (指令1): 指令108参数不匹配: none vs None (op=LOAD_CONST)`
  - 原始 LOAD_CONST argval: `"none"`（字符串字面量）
  - 重编 LOAD_CONST argval: `None`（Python None 对象）
- **Root cause**: 源码中某处含字符串 `"none"`（小写），反编译时被错误转换为 Python `None`。可能是 WithRegion 或 TryExceptRegion 识别时把字符串常量池索引与 None 常量索引混淆（co_consts 索引错位）。具体地，with/try 嵌套结构在生成 cleanup 块时，把某个 LOAD_CONST 的 arg（co_consts 索引）指向了 None 而非字符串 "none"。这通常是因为嵌套 with/try 的 cleanup 块顺序被打乱，co_consts 表的索引在重编时与原始不一致。
- **Algorithm principle violated**: 原则 4（父引用子入口）——父区域通过 LOAD_CONST 索引引用子区域常量，索引错位导致语义改变。
- **Fix direction**: 在 WithRegion/TryExceptRegion 生成 cleanup 块时，严格保留原始 LOAD_CONST 的 argval（字符串 vs None），不应根据 cleanup 模板硬编码 None。

---

## Finding R21-25: if 条件含 lambda IIFE + boolop + elif 链时 lambda body 退化为 return None

- **Test**: tests/exhaustive/if_region/test_adv19_lambda_iife_in_if_cond.py
- **Source**:
  ```python
  def f(y):
      if (lambda x: x > 0)(y) and (lambda x: x < 100)(y):
          return 'valid'
      elif (lambda x: x == 0)(y):
          return 'zero'
      else:
          return 'invalid'
  ```
- **Error**: `嵌套code object不匹配 (指令1): 嵌套code object不匹配 (指令16): 指令数不匹配: 5 vs 3`
  - 原始 lambda body（5 条）: `RESUME, LOAD_FAST x, LOAD_CONST 0, COMPARE_OP, RETURN_VALUE`（`return x > 0`）
  - 重编 lambda body（3 条）: `RESUME, LOAD_CONST None, RETURN_VALUE`（`return None`）
- **Root cause**: if 条件中的 lambda IIFE `(lambda x: x > 0)(y)` 的 code object 在重编时 body 完全退化为 `return None`。lambda 的 code object 含 `LOAD_FAST x, LOAD_CONST 0, COMPARE_OP, RETURN_VALUE`，但反编译器未识别 lambda body 内的 `x > 0` 表达式，把整个 body 作为空体处理。底层是 lambda code object 的反编译未走完整的 region_analyzer 流程（lambda body 是独立 code object，需要递归反编译），递归反编译时 IfRegion/BoolOpRegion 识别未正确处理 lambda body 的简单比较表达式。
- **Algorithm principle violated**: 原则 1（自底向上归约）——lambda body 内的比较表达式应被识别为 Return.value 子节点。
- **Fix direction**: 在 lambda code object 递归反编译时，确保简单 `return expr` 模式（含 COMPARE_OP + RETURN_VALUE）被正确识别为 Return 节点，而非退化为隐式 return None。

---

## Finding R21-26: if 条件含链式 in 检查时被误识别为 chained compare

- **Test**: tests/exhaustive/if_region/test_adv19_chained_in_check_in_if_cond.py
- **Source**: if 条件含 `a in b in c in d` 形态（多重 in 检查）
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 27 vs 31`（重编多 4 条）
  - 原始: `LOAD_FAST, LOAD_FAST, CONTAINS_OP, LOAD_FAST, LOAD_FAST, CONTAINS_OP, LOAD_FAST, LOAD_FAST, CONTAINS_OP, LOAD_CONST None, RETURN_VALUE`（无短路，纯表达式求值后 POP_TOP）
  - 重编: `LOAD_FAST, LOAD_FAST, CONTAINS_OP, JUMP_IF_FALSE_OR_POP, LOAD_FAST, LOAD_FAST, CONTAINS_OP, JUMP_IF_FALSE_OR_POP, ...`（误识别为 chained compare，多出 JUMP_IF_FALSE_OR_POP 短路跳转）
- **Root cause**: `_detect_chained_compare_pattern`（line 11502）的判据是 `COPY(arg=2) + COMPARE_OP/IS_OP/CONTAINS_OP` 对。但 `a in b in c in d` 在 CPython 中实际编译为 BoolOp(And) 链（每个 `in` 是独立比较，通过 and 短路连接），而非 chained compare（COPY+COMPARE_OP 共享中间操作数）。反编译器把多个 CONTAINS_OP 误识别为 chained compare，生成了 JUMP_IF_FALSE_OR_POP 短路跳转，但原始字节码是直接连续 CONTAINS_OP（无短路）——说明源码可能是 `a in b and c in d and e in f`，原始字节码经过 CPython peephole 优化去掉了短路跳转。反编译器误识别导致重编多出短路跳转指令。
- **Algorithm principle violated**: 原则 1（自底向上归约）——应识别为 BoolOp(And) 而非 chained compare。
- **Fix direction**: 在 `_detect_chained_compare_pattern` 中，要求 COPY(arg=2) 紧邻 COMPARE_OP/IS_OP/CONTAINS_OP（已存在），但需额外检查后续块是否也以 COPY+COMPARE_OP 模式继续；若仅多个独立 CONTAINS_OP 无 COPY 串联，应识别为 BoolOp 而非 chained compare。

---

## Finding R21-27: if-elif-else 条件含 chained compare 时 elif 链中后续 chained compare 丢失

- **Test**: tests/exhaustive/if_region/test_adv18_if_with_chained_compare_cond.py
- **Source**: `if 0 < x < 10: ... elif 10 < x < 100: ... elif 100 < x < 1000: ...`（三个 elif 分支都含 chained compare）
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 35 vs 28`（重编少 7 条，第二、第三个 elif 的 chained compare chain 块丢失）
  - 前 19 条完全匹配（第一个 if 的 chained compare 正确）
  - 之后重编丢失第二、第三 elif 的 `LOAD_CONST, LOAD_FAST, SWAP, COPY, COMPARE_OP, LOAD_CONST, COMPARE_OP, POP_TOP` 段
- **Root cause**: `_build_elif_region` 的 `_check_elif_chain`（line 11006+）在检测 elif 链时，对每个 elif 条件块调用 `_detect_chained_compare_pattern`，但 elif 条件块的 chain_blocks（COPY+COMPARE_OP 的延续块）未被纳入 IfRegion.all_condition_blocks。第一个 if 的 chained_compare_info 在 `_identify_conditional_regions` 主循环中被正确处理（line 10532-10558），但 elif 链的后续条件块在 `_check_elif_chain` 递归中没有传递 chained_compare_info，导致第二、第三 elif 的 chain 块被作为独立 BASIC 块处理，AST 生成时丢失。
- **Algorithm principle violated**: 原则 2（每块唯一归属）——elif 链中 chained compare chain 块应归 IfRegion.all_condition_blocks；原则 4 失败。
- **Fix direction**: 在 `_check_elif_chain` 中，对每个 elif 条件块调用 `_detect_chained_compare_pattern`，把 chain_blocks 纳入 IfRegion.elif_conditions 对应的 all_condition_blocks；AST 生成时 `_if_generate_full_elif_chain` 对每个 elif 条件重建 chained compare。

---

## Finding R21-28: elif 条件含嵌套三元时 COMPARE_OP 被替换为 POP_TOP

- **Test**: tests/exhaustive/if_region/test_adv18_nested_ternary_in_elif_cond.py
- **Source**: elif 条件含嵌套三元 `(b if c else d)`，三元 true/false value 是常量
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 19 vs 18`（重编少 1 条）
  - 原始: `LOAD_CONST, LOAD_CONST, COMPARE_OP, LOAD_CONST, STORE_FAST`
  - 重编: `LOAD_CONST, LOAD_CONST, POP_TOP, LOAD_CONST, STORE_FAST` —— **COMPARE_OP 被替换为 POP_TOP**
- **Root cause**: elif 条件中嵌套三元的 merge_block 含 `LOAD_CONST, LOAD_CONST, COMPARE_OP, STORE_FAST`（三元 true/false value 各为常量，merge 后做比较并赋值）。`_identify_ternary_regions` 把三元识别后，`_generate_ternary` 在生成 IfExp 时没有正确处理 true/false value 块含 COMPARE_OP 的情况，把 COMPARE_OP 的结果丢弃（生成 POP_TOP 而非 COMPARE_OP）。底层是 `_build_ternary_value_expr`（region_ast_generator.py:17937）对 value 块含 COMPARE_OP 的处理不完整，把比较表达式简化为表达式语句（POP_TOP）。
- **Algorithm principle violated**: 原则 4（父引用子入口）——父 IfRegion.test 通过 merge_block 的 COMPARE_OP 引用三元子节点；COMPARE_OP 不应被替换为 POP_TOP。
- **Fix direction**: 在 `_build_ternary_value_expr` 中，对 value 块含 COMPARE_OP 的情况，把整个 COMPARE_OP 表达式作为 IfExp.body/orelse，而非仅取第一个操作数 + POP_TOP。

---

## Finding R21-29: if body 内含 raise from 复杂形式时 from 子句丢失

- **Test**: tests/exhaustive/if_region/test_adv18_raise_from_complex_in_if_body.py
- **Source**: if-elif-else 三分支各自 `raise ValueError(...) from RuntimeError(...)`
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 34 vs 13`（重编少 21 条，三个分支的 `from RuntimeError(...)` 子句 + 部分分支结构丢失）
- **Root cause**: `raise X from Y` 的字节码是 `LOAD_GLOBAL ValueError, LOAD_CONST 'positive', CALL, LOAD_GLOBAL RuntimeError, LOAD_CONST 'orig_pos', CALL, RAISE_VARARGS 3`。IfRegion.then_blocks 收集时，`from Y` 部分的 `LOAD_GLOBAL RuntimeError + CALL` 块被作为独立 BASIC 块处理，与 raise 主块的 RAISE_VARARGS 块分离。AST 生成时只生成了 `raise ValueError(...)`，`from RuntimeError(...)` 部分丢失。三个分支中只有第一个部分保留，后两个完全丢失。底层是 raise from 的多块结构未被识别为单一 Raise 节点。
- **Algorithm principle violated**: 原则 3（嵌套即抽象节点）——`raise X from Y` 应作为单一 Raise 节点，X 和 Y 是其子表达式。
- **Fix direction**: 在 Raise 节点识别时，检测 RAISE_VARARGS 之前的块链是否含 `LOAD_GLOBAL + CALL` 模式（from 子句），若是则把整个块链作为单一 Raise 节点，cause 字段引用 from 子句表达式。

---

## Finding R21-30: if body 内含 multiline return + BUILD_CONST_KEY_MAP 时指令数错乱

- **Test**: tests/exhaustive/if_region/test_adv19_multiline_return_in_if_body.py
- **Source**: if body 内含 `return {'a': 1, 'b': 2 + x, 'c': data['key']}`（多行 return + BUILD_CONST_KEY_MAP）
- **Error**: `嵌套code object不匹配 (指令1): 指令数不匹配: 33 vs 32`（重编少 1 条）
  - 前 20 条完全匹配
  - 之后某处重编少 1 条指令（BUILD_CONST_KEY_MAP 的某个 LOAD_CONST 元素丢失）
- **Root cause**: BUILD_CONST_KEY_MAP 模式（keys 作为单个 LOAD_CONST tuple 打包）在 IfRegion.then_blocks 中被收集时，const tuple 的 LOAD_CONST 块被作为独立 BASIC 块处理。AST 生成时 const tuple 的某个元素丢失，导致重编后 BUILD_CONST_KEY_MAP 的 keys 数量与原始不一致。底层是 `_collect_branch_blocks` 把 BUILD_CONST_KEY_MAP 之前的 LOAD_CONST tuple 块与后续 value 块分离处理。
- **Algorithm principle violated**: 原则 3（嵌套即抽象节点）——BUILD_CONST_KEY_MAP 应作为单一 Dict 字面量子节点，keys tuple 与 values 不应被拆解。
- **Fix direction**: 在 `_collect_branch_blocks` 中，遇到 BUILD_CONST_KEY_MAP 时把前驱 LOAD_CONST tuple 块与后续 value 块作为单一表达式块停止 BFS 拆解。

---

## 跨测试根因汇总表

| 根因簇 | 涉及 Finding | 涉及测试数 | 优先级 | 关键源码位置 |
|--------|--------------|------------|--------|--------------|
| C1: TernaryRegion/BoolOpRegion 抢占 IfRegion 头块 | R21-01, 02, 03, 04, 05 | 11+ | P0 | region_analyzer.py:10315-10337, 10223-10256 |
| C2: AssertRegion 与 IfRegion 头块边界冲突 | R21-06, 07 | 3 | P2 | region_analyzer.py:9476-9587 |
| C3: 多元组/链式比较/切片含三元时父表达式归约失败 | R21-08, 09, 10 | 4+ | P1 | region_ast_generator.py:6648-6880, 11839-12144 |
| C4: if-elif-else 内嵌套 for-else/while-else/try-else 时 else 子句与循环体归属错位 | R21-12, 13, 14, 15, 16, 17, 19, 20, 21, 30 | 15+ | P0 | region_analyzer.py:10646-10714, 10992-11190 |
| C5: async if 条件含 await 时多 await 链路只收集单个 setup+poll | R21-11, 23 | 3+ | P1 | region_analyzer.py:4425-4477 |
| C6: 多 with 上下文 + 嵌套 with 时子 WithRegion 被平铺 | R21-18, 24 | 2 | P2 | region_analyzer.py:7237-7265 |
| C7: lambda IIFE 递归反编译时 body 退化 | R21-25 | 1 | P2 | 递归 code object 反编译路径 |
| C8: chained in 误识别为 chained compare | R21-26 | 1 | P2 | region_analyzer.py:11502-11550 |
| C9: elif 链中 chained compare chain 块未纳入 all_condition_blocks | R21-27 | 1 | P1 | region_analyzer.py:11006-11190 |
| C10: 嵌套三元 value 块含 COMPARE_OP 时被替换为 POP_TOP | R21-28 | 1 | P2 | region_ast_generator.py:17937 |
| C11: raise from 多块结构未识别为单一 Raise 节点 | R21-29 | 1 | P2 | raise 节点识别路径 |
| C12: 闭包 MAKE_CELL/LOAD_CLOSURE prologue 块被 IfRegion 收集 | R21-22 | 1 | P2 | region_analyzer.py: _collect_branch_blocks |

---

## 关键算法原则违反统计

| 原则 | 违反次数 | 主要场景 |
|------|----------|----------|
| 原则 1（自底向上归约） | 12 | TernaryRegion/BoolOpRegion 抢占 IfRegion 头；async await 链未完整收集；lambda body 退化 |
| 原则 2（每块唯一归属） | 18 | for-else/while-else/try-else 的 else 块被 IfRegion 与 LoopRegion/TryExcept 同时争抢；隐式 return None 重复生成；MAKE_CELL prologue 被错误收集 |
| 原则 3（嵌套即抽象节点） | 11 | ForLoop/WhileLoop/TryExcept 在 then_blocks 中被 BFS 拆解；BUILD_TUPLE/BUILD_SLICE 含三元时被拆解；raise from 多块未归约为单一节点 |
| 原则 4（父引用子入口） | 9 | IfRegion 未通过 entry 引用 ternary/boolop 子节点；LOAD_CONST 索引错位；COMPARE_OP 被替换为 POP_TOP |

---

## 测试覆盖与建议

### 已分析测试（30 个具体 Finding，覆盖 35 个失败测试）

Group A（IF 区域未检测，6 测试）: R21-01, 02, 06, 07（含 adv19/adv20 assert 系列）
Group B（指令数不匹配，三元+boolop，7 测试）: R21-02, 03, 04, 05, 08, 09, 10
Group C（嵌套 code object 不匹配，22 测试）: R21-11 至 R21-30

### 未单独列 Finding 但同源的其他失败测试

- `test_adv02_ternary_in_boolop_or.py` → 同 R21-01（or 替换 and）
- `test_adv19_assert_chained_cmp_in_if_body.py` → 已在 R21-07 覆盖
- `test_adv20_assert_chained_cmp_in_branches.py` → 同 R21-07
- `test_adv20_dictcomp_complex_filter_in_branches.py` → dictcomp 内 walrus 丢失，同 R21-22 闭包 cell 处理路径
- `test_adv19_tuple_unpack_in_if_body.py` → 同 R21-17（else 子句归属）

### 修复优先级建议

1. **P0 - 先修 C1 + C4**（覆盖 26+ 测试）：核心 IfRegion 创建被抢占 + 嵌套循环/try 的 else 子句归属错位。这两个根因覆盖 35 个失败中的 26+ 个。
2. **P1 - 再修 C3 + C5 + C9**（覆盖 8+ 测试）：三元在多元组/切片/链式比较中的归约 + async if 条件多 await + elif 链 chained compare。
3. **P2 - 最后修 C2 + C6 + C7 + C8 + C10 + C11 + C12**（覆盖 8+ 测试）：边界 case，每个仅 1-2 个测试。

### 验证方法

修复后运行：
```bash
cd /workspace && timeout 280 python -m pytest tests/exhaustive/if_region/ -q --tb=short
```
目标：35 failed → 0 failed。
