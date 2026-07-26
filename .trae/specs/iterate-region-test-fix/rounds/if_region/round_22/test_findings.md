# IF Region Round 22 — Test Findings

**日期**: 2026-07-25
**测试工程师**: R22 TEST ENGINEER（仅分析 + 单测验证，未修改任何源码）
**当前分支**: trae/agent-iter-continue
**基线**: commit 56b283f — `tests/exhaustive/if_region/` 34 failed / 783 passed / 10 skipped
**测试范围**: `tests/exhaustive/if_region/` 下全部 34 个失败用例
**分析对象**: `core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`
**分析方法**: 从最内层（最嵌套）区域向外层逐层归约分析，禁止跨区域启发式；通过运行单测 + 内部反编译管线（`CFGBuilder → RegionAnalyzer.analyze → RegionASTGenerator.generate → CodeGenerator`）打印反编译输出与区域结构验证根因。

---

## Summary

- **Total failures analyzed**: 34（全部 `test_decompile` 失败用例，已逐个读取源码与错误信息并复现反编译输出）
- **Root cause clusters**: 10（C1–C10），覆盖全部 34 个失败用例
- **R21 修复回退/不完整统计**:
  - R21-C1（三元+boolop 抢占 if 头）已修复 `(ternary) and b` 单三元场景，但**多三元链 / 嵌套三元 cond** 仍失败 → R22-C1
  - R21-C3（多元组/切片/链式比较含三元）**修复不完整**，3 个测试仍失败 → R22-C6
  - R21-C4（if-elif-else 嵌套 loop-else/try-else else 子句归属）**修复不完整**，7 个测试仍失败 → R22-C7
  - R21-C5（async if 多 await）**已修复**，本轮 0 回归
  - R21-C6 / C7（嵌套 with / lambda IIFE）**未修复** → R22-C8 / R22-C9
- **R22 新增根因簇**:
  - **C2（P0，5 测试）**: walrus 绑定三元后在 if 条件继续运算（`.field`/`[0]`/`.method()`/`+1`/直接比较）时 IfRegion 被丢弃 — R21-C1 redirect 触发但 `IfRegion.entry` 与 `TernaryRegion.entry` 共享，`_generate_if` 入口 `entry in generated_blocks` 检查把整个 IfRegion 丢弃。这是本轮最大的新根因簇。
  - **C3（P0，3 测试）**: AssertRegion 抢占 if-elif-else 头块（含 assert + msg + chained cmp）
  - **C4（P0，3 测试）**: if-elif-else 三分支均以 for 循环开头时头块被 TernaryRegion 抢占，整 if 坍塌为链式三元
  - **C5（P1，3 测试）**: elif 链条件含三元 / 链式比较 / 多重 in 检查时 elif 链断裂
- **Recommended fix priority**:
  - **P0**: C2（5 测试，walrus+三元 if 条件核心坍塌）、C3（3 测试，assert 抢占 if 头）、C4（3 测试，for-分支 if 头坍塌）、C7（7 测试，嵌套 region 不透明子节点）— 共 18 测试
  - **P1**: C1（3 测试，多三元/嵌套三元链）、C5（3 测试，elif 链复杂条件）、C6（3 测试，三元在容器内）— 共 9 测试
  - **P2**: C8（2 测试，嵌套 with）、C9（1 测试，lambda IIFE）、C10（4 测试，复杂表达式多块拆解）— 共 7 测试

---

## 区域归约算法 4 原则违反统计

| 原则 | 违反簇 | 主要场景 |
|------|--------|----------|
| 原则 1（自底向上归约） | C1, C4, C5, C9 | TernaryRegion/BoolOpRegion 应作 IfRegion.test 子节点而非抢占头块；elif 条件子表达式未归约；lambda body 比较未归约 |
| 原则 2（每块唯一归属） | C2, C3, C4, C7 | IfRegion.entry 与 TernaryRegion.entry 共享；AssertRegion 抢占 if 头；嵌套 region else 子句被 IfRegion 与 LoopRegion/TryExcept 争抢 |
| 原则 3（嵌套即抽象节点） | C6, C7, C8, C10 | 共享容器 merge 的兄弟三元应作 Tuple/Slice 子节点；LoopRegion/TryExcept/WithRegion 应作 then_blocks 不透明子节点；raise-from / BUILD_SET+genexp / dictcomp 多 for 应作单一表达式子节点 |
| 原则 4（父引用子入口） | C1, C2, C5, C8 | IfRegion 应通过 condition_block/entry 引用 ternary/boolop 子节点；elif_conditions 应引用 ternary merge；嵌套 with cleanup 块 LOAD_CONST 索引错位 |

---

## 跨测试根因汇总表

| 根因簇 | 涉及测试 | 测试数 | 优先级 | 关键源码位置 | 违反原则 |
|--------|----------|--------|--------|--------------|----------|
| **C1**: 多三元/嵌套三元 boolop 链抢占 if 头 | adv01_nested_ternary_cond, adv13_ternary_and_ternary_boolop, adv13_ternary_three_or_cond | 3 | P1 | region_analyzer.py:10404-10433（_ternary_if_cond_redirect 仅覆盖单三元）、10223-10256（BoolOp op_chain trimming） | 1, 4 |
| **C2**: walrus+三元 if 条件 IfRegion 被丢弃 | adv14_walrus_ternary_attr, adv14_walrus_ternary_binary_op, adv14_walrus_ternary_method, adv14_walrus_ternary_subscr, adv15_walrus_ternary_cond | 5 | P0 | region_ast_generator.py:6629-6641（_generate_if entry-generated 检查丢弃 IfRegion）；region_analyzer.py:12952-12984（merge_context='compare' walrus wrapping 检测）、10566-10571（condition_block redirect） | 2, 4 |
| **C3**: AssertRegion 抢占 if-elif-else 头块 | adv18_assert_in_if_body, adv19_assert_chained_cmp_in_if_body, adv20_assert_chained_cmp_in_branches | 3 | P0 | region_analyzer.py:9458-9657（_identify_assert_regions POP_JUMP_IF_TRUE 误判 if 头为 assert cond） | 2, 4 |
| **C4**: if-elif-else 三分支均以 for 开头时头块被 TernaryRegion 抢占 | adv19_for_continue_in_each_branch, adv19_mixed_complex_branches, adv20_for_else_break_in_each_branch | 3 | P0 | region_analyzer.py:_identify_ternary_regions（if 头→ternary.cond, for-iter setup→true_value, elif cond→false_value）、10404-10436（_ternary_owner_for_skip continue） | 1, 2, 3 |
| **C5**: elif 链条件含三元/链式比较/多重 in 时 elif 链断裂 | adv18_nested_ternary_in_elif_cond, adv18_if_with_chained_compare_cond, adv19_chained_in_check_in_if_cond | 3 | P1 | region_analyzer.py:11006+（_check_elif_chain 未对每个 elif cond 调 _detect_chained_compare_pattern / 未传递 ternary merge）；region_ast_generator.py:_if_generate_full_elif_chain | 1, 4 |
| **C6**: 多元组/切片/链式比较含三元父表达式归约失败（R21-C3 不完整） | adv15_ternary_in_tuple_unpack, adv15_ternary_slice_in_body, adv15_ternary_in_chain_compare_body | 3 | P1 | region_ast_generator.py:6648-6880（_generate_value_context_chain_compare_assign 丢失 STORE 目标）、_generate_ternary（未组装共享容器 merge 的兄弟三元为 Tuple/Slice） | 3, 4 |
| **C7**: if body 内嵌套 loop-else/try-else/nested-if 未作不透明子节点（R21-C4 不完整） | adv18_try_finally_in_if_body, adv19_try_except_else_in_if_body, adv19_while_else_break_in_elif_body, adv19_tuple_unpack_in_if_body, adv19_multiline_return_in_if_body, adv20_walrus_in_while_cond_nested_if, adv20_yield_in_while_in_if_body | 7 | P0 | region_analyzer.py:10646-10714（_collect_branch_blocks BFS 进入 LoopRegion/TryExceptRegion 内部块）、LoopRegion.get_if_branch_boundary_stop、TryExceptRegion.else_blocks 边界 | 2, 3 |
| **C8**: 多 with 上下文 + 嵌套 with 子 WithRegion 被平铺（R21-C6 未修复） | adv19_with_multi_ctx_in_if_body, adv20_nested_with_try_in_elif_body | 2 | P2 | region_analyzer.py:7237-7265（_identify_with_regions 把内层 BEFORE_WITH 吸收进外层 context 列表） | 3, 4 |
| **C9**: lambda IIFE 递归反编译 body 退化（R21-C7 未修复） | adv19_lambda_iife_in_if_cond | 1 | P2 | 递归 code object 反编译路径（elif 条件 lambda code object 退化为 `lambda *args, **kwargs: None`） | 1 |
| **C10**: if body 内复杂表达式多块结构被拆解 | adv18_raise_from_complex_in_if_body, adv20_tuple_return_in_branches, adv20_dictcomp_complex_filter_in_branches, adv20_star_expr_in_call_in_if_body | 4 | P2 | region_ast_generator.py:_collect_branch_blocks（raise-from 多块、BUILD_SET+genexp、dictcomp 多 for、闭包 MAKE_CELL/LOAD_CLOSURE prologue 被拆解） | 3 |

---

## C1 — 多三元 / 嵌套三元 boolop 链抢占 if 头（P1，3 测试）

### 涉及测试
- `test_adv01_nested_ternary_cond` — `if (a if (b if c else d) else e): pass`
- `test_adv13_ternary_and_ternary_boolop` — `if (a if c else b) and (d if e else f): pass`
- `test_adv13_ternary_three_or_cond` — `if (a if c else b) or (d if e else f) or (g if h else i): pass`

### 反编译输出（实测）
- adv01_nested_ternary_cond → `if ((b if c else d) and a):\n    pass`（嵌套外层三元 `a if (inner) else e` 被误并为 BoolOp(And)，`e` 分支丢失）
- adv13_ternary_and_ternary_boolop → `if (a if c else b):\n    pass\nif (d if e else f):\n    pass`（and 链断裂为两个独立 if，第二个 if 实为 else 分支）
- adv13_ternary_three_or_cond → `if (g if c else i):\n    pass`（三段 or 只剩一段，且 cond `c`/value `g`/`i` 来自不同三元被错配）

### 根因（从内层到外层）
1. **内层**：每个三元 `(a if c else b)` 的 cond_block（`LOAD c, POP_JUMP_IF_FALSE`）+ true_value（`LOAD a, JUMP_FORWARD`）+ false_value（`LOAD b`）+ merge_block（`LOAD b` fallthrough）被 `_identify_ternary_regions` 识别为独立 TernaryRegion。
2. **中层**：外层 BoolOpRegion（`and`/`or`）的 op_chain 收集（`_identify_boolop_regions`，region_analyzer.py:10223-10256 的 trimming 逻辑）遇到"操作数本身是 TernaryRegion"时，把 TernaryRegion 的 true/false value 块（各自以 JUMP_FORWARD 结尾）误判为非 and 链一部分而修剪掉；多三元链在第 2、3 个三元处 op_chain 中断。
3. **外层**：`_identify_conditional_regions` 的 R21-C1 `_ternary_if_cond_redirect`（region_analyzer.py:10404-10433）只覆盖"单个三元 merge_block 以 FORWARD_CONDITIONAL_JUMP 结尾"场景。多三元链中每个三元 merge 仅产生值（无 cond jump），redirect 不触发；嵌套三元 `a if (inner) else e` 中内层三元 merge 是外层三元 cond_block，redirect 误把外层三元 cond 当 boolop 处理。

### 违反原则
- 原则 1（自底向上归约）：TernaryRegion 应作 BoolOpRegion op_chain 子节点，BoolOpRegion 应作 IfRegion.test 子节点，不应抢占 IfRegion 头。
- 原则 4（父引用子入口）：IfRegion 应通过 condition_block 引用 BoolOpRegion，BoolOpRegion 通过 op_chain 引用所有三元 entry。

### 修复方向
- BoolOpRegion op_chain trimming（line 10232-10245 `_prev_jt` 检测）：当 prev_cb 的 jump target 块属于某 TernaryRegion 的 true_value_block/false_value_block 时跳过 trimming。
- `_ternary_if_cond_redirect`：扩展判据，当多个 TernaryRegion 的 merge_block 链式汇聚到同一 BoolOpRegion.merge_block 且后者以 FORWARD_CONDITIONAL_JUMP 结尾时，把 BoolOpRegion.merge 作为 IfRegion.condition_block，所有三元作为 BoolOpRegion op_chain 子节点。

---

## C2 — walrus 绑定三元后在 if 条件继续运算时 IfRegion 被丢弃（P0，5 测试）

### 涉及测试
- `test_adv14_walrus_ternary_attr` — `if (x := a if c else b).field > 0: pass`
- `test_adv14_walrus_ternary_binary_op` — `if (x := a if c else b) + 1 > 0: pass`
- `test_adv14_walrus_ternary_method` — `if (x := a if c else b).method() > 0: pass`
- `test_adv14_walrus_ternary_subscr` — `if (x := a if c else b)[0] > 0: pass`
- `test_adv15_walrus_ternary_cond` — `if (n := (a if c else b)) > 0: pass`

### 反编译输出（实测）
5 个用例反编译输出全部为 `pass`（IfRegion 整体丢失，三元 + walrus + 比较 + if body 全部消失）。

### 区域结构（以 adv14_walrus_ternary_attr 为例，经 `_r22_debug2.py` 实测）
```
Block@0:  LOAD c, POP_JUMP_FORWARD_IF_FALSE → 10   (ternary cond)
Block@6:  LOAD a, JUMP_FORWARD → 12                (ternary true_value)
Block@10: LOAD b                                   (ternary false_value, fallthrough→12)
Block@12: COPY, STORE_NAME x, LOAD_ATTR field, LOAD_CONST 0, COMPARE_OP >, POP_JUMP_FORWARD_IF_FALSE → 40  (ternary merge + walrus + attr + compare + if test)
Block@36: LOAD_CONST None, RETURN_VALUE            (then body: pass)
Block@40: LOAD_CONST None, RETURN_VALUE            (after if)

TernaryRegion entry=0 blocks=[0,6,10,12]  merge_block=12  merge_context='compare'  true_value=6 false_value=10
IfRegion      entry=0 blocks=[0,6,10,12,36]  then=[36]
block_to_region[0]  -> TernaryRegion
block_to_region[12] -> TernaryRegion
```

### 根因（从内层到外层）
1. **内层**：`_identify_ternary_regions` 识别 TernaryRegion(entry=0, merge_block=12)。merge_block@12 含 `COPY 1, STORE_NAME x, LOAD_ATTR field, LOAD_CONST 0, COMPARE_OP >, POP_JUMP_FORWARD_IF_FALSE`，即 walrus 绑定 + 属性访问 + 比较 + if 测试共处一块。`_is_walrus_wrapping` 检测（region_analyzer.py:12952-12984）发现 COPY 1 紧邻 STORE_NAME x，后续有 LOAD_ATTR（wrapping op）+ COMPARE_OP + 条件跳转，遂设 `merge_context='compare'`。
2. **中层**：`_identify_conditional_regions` 扫到 block@0（ternary entry），R21-C1 redirect（region_analyzer.py:10404-10433）检测到 ternary.merge_block@12 以 `POP_JUMP_FORWARD_IF_FALSE`（FORWARD_CONDITIONAL_JUMP_OPS）结尾，且非 chained-compare middle，遂设 `_ternary_if_cond_redirect = block@12`，并把 condition_block 重定向到 block@12（line 10566-10571），把 TernaryRegion.blocks 加入 chain_blocks。IfRegion 创建：entry=0（仍为 ternary entry），condition_block=12，then=[36]。
3. **外层**：`RegionASTGenerator._generate_if`（region_ast_generator.py:6629-6641）入口检查 `if region.entry and region.entry in self.generated_blocks:`。由于 TernaryRegion.entry==IfRegion.entry==block@0，且 TernaryRegion 先于 IfRegion 生成（作为兄弟顶层区域或被父级先处理）已把 block@0 标记为 generated，此检查为真。随后查找 BoolOpRegion 子节点（line 6630-6640）——本场景无 BoolOpRegion（walrus+三元无 and/or），`boolop_child is None`，遂 `return []`。**整个 IfRegion 被丢弃**，只剩 block@40 的隐式 `return None`，输出坍塌为 `pass`。

### 关键代码位置
- region_analyzer.py:12952-12984（`_is_walrus_wrapping` 设 merge_context='compare'）
- region_analyzer.py:10404-10433（R21-C1 `_ternary_if_cond_redirect` 触发）
- region_analyzer.py:10566-10571（condition_block 重定向到 ternary merge，但 entry 仍为 ternary entry）
- **region_ast_generator.py:6629-6641（`_generate_if` entry-generated 检查丢弃 IfRegion — C2 核心缺陷）**

### 违反原则
- 原则 2（每块唯一归属）：IfRegion.entry 与 TernaryRegion.entry 共享 block@0，生成顺序导致 IfRegion 被丢弃。
- 原则 4（父引用子入口）：IfRegion 应通过 condition_block（merge_block@12）引用 TernaryRegion 子节点，但 entry-based generated 检查阻断了这一路径。

### 修复方向
在 `_generate_if`（region_ast_generator.py:6629）的 entry-generated 检查中，当 IfRegion.condition_block 被 R21-C1 redirect 到 TernaryRegion.merge_block 时（即 IfRegion.entry 是某 TernaryRegion.entry 且 condition_block 是该 TernaryRegion.merge_block），不应 `return []`，而应：把 TernaryRegion 作为 IfRegion.test 子节点，调用 `_build_ternary_wrapped_expr` 重建完整条件表达式（`NamedExpr(walrus, Compare(Call/Attr/Subscr/BinOp(IfExp), op, const))`），再生成 then/else body。或者：在 R21-C1 redirect 时同步把 IfRegion.entry 改为 merge_block@12（但这会破坏 ternary 块归属），需在 `_generate_if` 改用 condition_block 而非 entry 做 generated 检查。

---

## C3 — AssertRegion 抢占 if-elif-else 头块（P0，3 测试）

### 涉及测试
- `test_adv18_assert_in_if_body` — `if x > 0: assert x < 100, f"..."\nelif x < 0: assert x > -100, "..."\nelse: assert True, "..."`
- `test_adv19_assert_chained_cmp_in_if_body` — `if x > 0: assert 0 < x < 100, f'...'; return 'pos_valid'\nelif...`
- `test_adv20_assert_chained_cmp_in_branches` — 三分支各自 `assert 0 < x < 10, f'...'; return x * 2` 等

### 反编译输出（实测）
- adv18_assert_in_if_body → `(x < 100 if x > 0 else x < 0)`（if-elif-else 坍塌为三元表达式，assert 消息、elif/else body 全失）
- adv19_assert_chained_cmp_in_if_body → `def f(x):\n    (0 < x if x > 0 else -100 < x if x < 0 else x == 0)`（坍塌为链式三元，return 全失）
- adv20_assert_chained_cmp_in_branches → `def f(flag, x):\n    (0 < x if flag == 'a' else 10 < x if flag == 'b' else -100 < x)\n    raise RuntimeError('must be neg')\n    return (-x)`（坍塌为链式三元 + raise/return 散落）

### 根因（从内层到外层）
1. **内层**：每个分支 body 内的 `assert cond, msg` 生成 `LOAD_ASSERTION_ERROR, <cond>, <msg>, RAISE_VARARGS 2` 或 `POP_JUMP_IF_TRUE → end, LOAD_ASSERTION_ERROR, ...`。`_identify_assert_regions`（region_analyzer.py:9458-9657）扫描每个 `POP_JUMP_IF_TRUE` 块判定是否到达 `LOAD_ASSERTION_ERROR`。
2. **中层**：`if x > 0` 的 cond 块以 `POP_JUMP_IF_FALSE → elif_cond` 结尾。其 else 分支（elif 条件 `x < 0` 块）恰好通向 elif body 内的 assert（含 LOAD_ASSERTION_ERROR）。`_identify_assert_regions` 把 `if x > 0` 的 cond 块误识别为 AssertRegion.entry，cond_block=`x > 0`，message_block=elif assert message。同时 then body 的 `assert x < 100` cond 块也被识别为独立 AssertRegion。
3. **外层**：if-elif-else 头块被 AssertRegion 抢占后，IfRegion 创建被跳过；then body 的 assert cond 块（`x < 100`）与 elif cond 块（`x < 0`）被当作三元 true/false value，merge 到 `(x < 100 if x > 0 else x < 0)`。

### 违反原则
- 原则 2（每块唯一归属）：if-elif-else 头块被 AssertRegion 错误抢占。
- 原则 4（父引用子入口）：AssertRegion 应作为 IfRegion.then_blocks 内的子节点，而非吃掉外层 IfRegion 头。

### 修复方向
在 `_identify_assert_regions` 中加入严格判据：assert 块的 `POP_JUMP_IF_TRUE` 跳转目标必须是 assert 自身的 message_block（紧邻 LOAD_ASSERTION_ERROR），而 elif 条件块的跳转目标是下一个 elif 条件块（非 assert message）。同时 AssertRegion 识别应跳过 `block_to_region` 中已是 IfRegion 头候选的块。

---

## C4 — if-elif-else 三分支均以 for 开头时头块被 TernaryRegion 抢占（P0，3 测试）

### 涉及测试
- `test_adv19_for_continue_in_each_branch` — 三分支各自 `for x in items: if x < 0: continue; process_a(x); return 'a_done'`
- `test_adv19_mixed_complex_branches` — `if x > 0: for item in items: if item == x: break; return 'found_pos'\nelif x < 0: try: raise...except: return...else: with open('log') as f: if f.read(): return 'has_log'; return 'no_log'`
- `test_adv20_for_else_break_in_each_branch` — 三分支各自 `for x in items: if x > 0: break; else: return 'no_pos'; return x`

### 反编译输出（实测）
- adv19_for_continue_in_each_branch → `def f(items, mode):\n    (items if mode == 'a' else items if mode == 'b' else items)\n    for x in items: if (x < 0): continue; process_a(x)\n    else: return 'a_done'\n    for x in items: ...`（if-elif-else 坍塌为链式三元，三个 for 循环被提升到顶层）
- adv19_mixed_complex_branches → `def f(x, items):\n    (items if x > 0 else x < 0)\n    for item in items: if (item == x): break\n    try: raise ValueError('neg')\n    except ValueError as e: return str(e)\n    with open('log') as f: if f.read(): return 'has_log'`（if 坍塌为三元，try/with 提升到顶层）
- adv20_for_else_break_in_each_branch → `def f(flag, items):\n    (items if flag == 'a' else items if flag == 'b' else items)\n    for x in items: if (x > 0): break\n    else: return 'no_pos'\n    ...`（if 坍塌为三元，for-else 提升到顶层）

### 根因（从内层到外层）
1. **内层**：if-elif-else 头块（`mode == 'a'`，以 `POP_JUMP_IF_FALSE → elif_cond` 结尾）的 then 分支直接进入 `LOAD items, GET_ITER, STORE_FAST x, FOR_ITER ...`（for setup）。elif_cond 块（`mode == 'b'`）同样进入第二个 for setup。
2. **中层**：`_identify_ternary_regions` 把 if 头块识别为 TernaryRegion.entry/cond：if 头块（`mode == 'a'`）→ ternary.cond；then 分支的 `LOAD items`（for setup 第一条）→ ternary.true_value（单表达式）；elif_cond 块（`mode == 'b'`）→ ternary.false_value；elif 的 for setup → 下一层三元。三个分支的 for setup 各为单表达式 value，构成链式三元 `(items if mode=='a' else items if mode=='b' else items)`。
3. **外层**：`_identify_conditional_regions` 扫到 if 头块时，line 10434-10436 `_ternary_owner_for_skip is not None and _ternary_if_cond_redirect is None → continue` 跳过 IfRegion 创建（因 if 头块已在 TernaryRegion.blocks 中，且 ternary merge 不以 FORWARD_CONDITIONAL_JUMP 结尾，redirect 不触发）。IfRegion 未创建，for 循环失去父级，被提升为顶层语句。

### 违反原则
- 原则 1（自底向上归约）：for 循环应作 IfRegion.then_blocks 子节点，不应被拆出。
- 原则 2（每块唯一归属）：if-elif-else 头块被 TernaryRegion 抢占。
- 原则 3（嵌套即抽象节点）：for 循环被提升出 if body，破坏嵌套层级。

### 修复方向
在 `_identify_ternary_regions` 的 ternary 候选判据中，要求 true_value/false_value 块必须是"纯值产生块"（LOAD/CONST + JUMP_FORWARD，无 GET_ITER/STORE_FAST 指令）。当 then 分支紧接 GET_ITER + FOR_ITER（for 循环 setup）时，不应识别为三元 true_value，而应让 IfRegion 优先创建，for 循环作 then_blocks 子节点。或在 `_identify_conditional_regions` 中，对"if 头块的 then 分支首块含 GET_ITER/FOR_ITER"的候选强制创建 IfRegion，跳过 ternary 抢占。

---

## C5 — elif 链条件含三元 / 链式比较 / 多重 in 时 elif 链断裂（P1，3 测试）

### 涉及测试
- `test_adv18_nested_ternary_in_elif_cond` — `if (1 if x else 2) > 0: r='a'\nelif (3 if x else 4) < 5: r='b'\nelse: r='c'`
- `test_adv18_if_with_chained_compare_cond` — `if 0 < x < 10: ...elif 10 <= x <= 50: ...elif 50 < x < 100: ...else: ...`
- `test_adv19_chained_in_check_in_if_cond` — `if x in a and x in b and x in c: ...elif x in a or x in b: ...elif x not in c: ...else: ...`

### 反编译输出（实测）
- adv18_nested_ternary_in_elif_cond → `def f(x):\n    if ((1 if x else 2) > 0): r = 'a'\n    else: (3 if x else 4)\n    return r`（elif 链断裂，第 2 个 elif 条件 `(3 if x else 4) < 5` 退化为裸三元表达式，`< 5` 比较与 `r='b'`/`r='c'` 全失）
- adv18_if_with_chained_compare_cond → `def f(x):\n    if (0 < x < 10): r = 'low'\n    elif (10 <= x <= 50): r = 'mid'\n        if 100: pass\n        else: r = 'out'\n        r = 'high'\n    elif (50 >= x): pass\n    return r`（第 2、3 elif 的 chained compare 链块丢失，结构错乱）
- adv19_chained_in_check_in_if_cond → `def f(x, a, b, c):\n    if ((x in a and x in b and x in c) in a): return 'in_all'\n    elif (x in a or x in b): return 'in_ab'\n    elif (x not in c): return 'not_in_c'\n    else: return 'none'`（第 1 个 if 条件被多包一层 `in a`，`and` 链误识别为 chained compare）

### 根因（从内层到外层）
1. **内层**：elif 条件含三元 `(1 if x else 2) > 0` 时，三元的 merge_block 含 `LOAD_CONST, COMPARE_OP >, POP_JUMP_IF_FALSE`；含链式比较 `10 <= x <= 50` 时，elif cond 块后跟 chain_blocks（`SWAP, COPY, COMPARE_OP, LOAD_CONST, COMPARE_OP`）；含多重 `x in a and x in b and x in c` 时，多个 CONTAINS_OP 经 and 短路连接。
2. **中层**：`_build_elif_region` 的 `_check_elif_chain`（region_analyzer.py:11006+）对每个 elif 条件块**未调用** `_detect_chained_compare_pattern`，elif 的 chain_blocks 未纳入 `IfRegion.all_condition_blocks`/`elif_conditions` 关联条件块集合。对 elif 条件含三元的情况，elif cond 块的 ternary merge_block 未传递给 elif 条件提取，AST 生成时三元退化为独立语句。
3. **外层**：`_if_generate_full_elif_chain`（region_ast_generator.py:6882-7068）对第 2+ 个 elif 条件重建时，因 chain_blocks/ternary merge 未在 elif_conditions 上下文中，要么退化为裸三元表达式（adv18_nested_ternary），要么 chained compare 链块丢失（adv18_if_with_chained_compare），要么 and 链被 `_detect_chained_compare_pattern` 误判为 chained compare 并多包一层 `in a`（adv19_chained_in_check）。

### 违反原则
- 原则 1（自底向上归约）：elif 条件子表达式（三元/链式比较/and 链）应归约进 elif_conditions。
- 原则 4（父引用子入口）：IfRegion.elif_conditions 应通过 ternary merge_block / chain_blocks 引用子表达式。

### 修复方向
- `_check_elif_chain`：对每个 elif 条件块调用 `_detect_chained_compare_pattern`，把 chain_blocks 加入对应 elif 的 all_condition_blocks；对 elif 条件含三元的情况，把三元 merge_block 作为 elif condition_block 上下文传递给 `_if_generate_full_elif_chain`。
- `_detect_chained_compare_pattern`：严格要求 `COPY(arg=2)` 紧邻 `COMPARE_OP` 且后续块以同模式延续；对多个独立 CONTAINS_OP 无 COPY 串联的情况（`x in a and x in b`）识别为 BoolOp(And) 而非 chained compare。

---

## C6 — 多元组 / 切片 / 链式比较含三元父表达式归约失败（R21-C3 不完整，P1，3 测试）

### 涉及测试
- `test_adv15_ternary_in_tuple_unpack` — `if c: a, b = (1 if x else 2), (3 if y else 4)`
- `test_adv15_ternary_slice_in_body` — `if c: x = lst[a if p else q:b if r else s]`
- `test_adv15_ternary_in_chain_compare_body` — `if c: z = 0 < (a if p else b) < 10`

### 反编译输出（实测）
- adv15_ternary_in_tuple_unpack → `if c:\n    a = (3 if y else 4)\n    (a, b) = (1 if x else 2, 3 if y else 4)`（第 1 个三元 `(1 if x else 2)` 被作为独立赋值 `a = (3 if y else 4)` 错位，元组解包 `a, b = ...` 结构破坏，`b` 赋值丢失）
- adv15_ternary_slice_in_body → `if c:\n    x = (b if r else s)\n    x = lst[a if p else q:b if r else s]`（第 1 个三元作为独立 `x = (b if r else s)` 错位，切片被二次生成）
- adv15_ternary_in_chain_compare_body → `if c:\n    (0 < (a if p else b) < 10)`（链式比较作为裸表达式语句，`z =` 赋值目标丢失）

### 根因（从内层到外层）
1. **内层**：两个三元 `(1 if x else 2)`、`(3 if y else 4)` 共享同一 merge_block（含 `BUILD_TUPLE 2, SWAP, STORE_NAME a, STORE_NAME b`）；切片两三元共享 `BUILD_SLICE 2, BINARY_SUBSCR, STORE_NAME x` merge；链式比较中段三元 merge 含 `SWAP, COPY, COMPARE_OP, JUMP_IF_FALSE_OR_POP, LOAD_CONST 10, COMPARE_OP, SWAP, POP_TOP, STORE_NAME z`。
2. **中层**：R21-C3 修复（`_generate_value_context_chain_compare_assign` 检测 ternary merge_block 作为父表达式操作数，递归调 `_generate_ternary`）**仅处理了单个三元**。对两个三元共享同一容器 merge（BUILD_TUPLE/BUILD_SLICE）的情况，`_detect_ternary_context` / `_generate_ternary` 未把兄弟三元组装为单一 Tuple/Slice AST。第 1 个三元被独立生成为 `Expr(IfExp)` 或错位赋值，第 2 个三元才进入容器重建。
3. **外层**：链式比较中段三元场景，`_generate_value_context_chain_compare_assign` 重建了 `Compare(0, [<, (IfExp)], <, 10])` 但**丢失了 `STORE_z` 赋值目标**，把 Compare 作为裸 `Expr` 语句输出。

### 违反原则
- 原则 3（嵌套即抽象节点）：兄弟三元应作 Tuple.elts / Slice.lower/upper 子节点，不应独立为语句。
- 原则 4（父引用子入口）：父 Assign 应通过容器 merge_block（BUILD_TUPLE/BUILD_SLICE/STORE_z）引用所有三元子节点。

### 修复方向
- `_identify_ternary_regions`：检测共享同一 merge_block（含 BUILD_TUPLE/BUILD_LIST/BUILD_SLICE）的多个三元，将其归约为单一"chained ternary container"区域；或在 `_generate_ternary` 中扫描同 merge_block 的其他三元子节点，组装为完整 Tuple/Slice AST。
- `_generate_value_context_chain_compare_assign`：在生成 Compare 后，保留 merge_block 的 `STORE_*` 指令作为 Assign.targets，不应丢弃为 Expr。
- `_detect_ternary_context`：在 merge_block 扫描中加入 `BUILD_SLICE` 指令识别（当前只识别 BUILD_LIST/TUPLE/SET/MAP），返回 `container_type='slice'`。

---

## C7 — if body 内嵌套 loop-else / try-else / nested-if 未作不透明子节点（R21-C4 不完整，P0，7 测试）

### 涉及测试
- `test_adv18_try_finally_in_if_body` — try-finally + 后续 if-elif 在 if body（重编多 2 条，cleanup 重复）
- `test_adv19_try_except_else_in_if_body` — try-except-else + 后续 if-elif（重编多 2 条，else 子句 `r = r + 1` 重复，`return 'none'` 错挂）
- `test_adv19_while_else_break_in_elif_body` — elif body 内 while-else + break（重编少 4 条，while-else 的 `return 'no_stop'` 丢失）
- `test_adv19_tuple_unpack_in_if_body` — 三分支 tuple unpack + 嵌套 if（重编少 2 条，else 分支 `return a, b` 丢失）
- `test_adv19_multiline_return_in_if_body` — if body 内 dict 字面量 + 嵌套 ternary + 嵌套 if（重编少 7 条，嵌套 if 条件退化为裸表达式 `(result['doubled'] > 100)`，`return {**result, 'overflow': True}` 与 `return result` 丢失）
- `test_adv20_walrus_in_while_cond_nested_if` — if body 内 while + walrus 条件 + 嵌套 if-elif-else（重编多 2 条，while body 末尾多出裸 `next` 表达式语句）
- `test_adv20_yield_in_while_in_if_body` — 生成器函数，if body 内 while + yield + 嵌套 if-elif-else（重编多 2 条，隐式 `return None` 多生成一次）

### 反编译输出（实测节选）
- adv19_try_except_else_in_if_body → `... try: r = process(x)\n        except ValueError: r = -1\n        else: r = (r + 1)\n        if (r > 100): return 'big'\n        elif (r > 0): return 'small'\n        return 'none'`（`return 'none'` 本应在外层 if 之外，被错挂到内层 if then 末尾）
- adv19_while_else_break_in_elif_body → `... elif (mode == 'b'): i = 0\n        while i < len(items): if (items[i] == 'stop'): break; i += 1\n        return 'no_stop'`（while-else 的 `else: return 'no_stop'` 退化为 while 之后的顺序 `return 'no_stop'`，`return items[i]` 丢失）
- adv19_multiline_return_in_if_body → `... if (x > 0): result = {...}\n        (result['doubled'] > 100)`（嵌套 `if result['doubled'] > 100: return {...}` 退化为裸表达式，return 丢失）
- adv20_walrus_in_while_cond_nested_if → `... while (x := next(it, None)) is not None: if...elif...else: result.append(...)\n            next`（while body 末尾多出裸 `next`，应为 walrus `next(it, None)` 调用的副作用残留）
- adv20_yield_in_while_in_if_body → `... while i < len(items): x = items[i]; if...: yield ...; i += 1`（生成器隐式 `return None` 多生成一次）

### 根因（从内层到外层）
1. **内层**：if body 内嵌套 LoopRegion（for/while，含 else 子句）、TryExceptRegion（含 else/finally 子句）、嵌套 IfRegion。这些子区域已由各自识别逻辑创建。
2. **中层**：`_collect_branch_blocks`（region_analyzer.py:10646-10714）从 then_succ 开始 BFS 收集 IfRegion.then_blocks/elif_bodies 时，**未把 LoopRegion/TryExceptRegion/嵌套 IfRegion 视为不透明子节点**，而是继续遍历其 body_blocks/else_blocks/finally_blocks。导致：
   - LoopRegion.else_blocks（for-else/while-else 的 else 子句）被 IfRegion.then_blocks 争抢；
   - TryExceptRegion.else_blocks（try-except-else 的 else 子句）被 IfRegion.then_blocks 重复收集（else 块生成两次）；
   - TryExceptRegion.finally_blocks 沿 fallthrough 吸收 try 体之外的后续 if；
   - 嵌套 IfRegion 的 cond 块被作为独立 BASIC 块纳入 then_blocks，其 then/else body 丢失，cond 退化为裸表达式。
3. **外层**：R21-C4 修复（`_collect_branch_blocks` `stop.discard(entry)` + `LoopRegion.get_if_branch_boundary_stop` 用 `self.blocks` + `_build_elif_region` break 目标检测）**只覆盖了 entry 被错误过滤和 break 目标块吸入两个子场景**，未解决"BFS 进入已归约 region 内部块"这一根本问题。生成器隐式 return / walrus 副作用残留 / 嵌套 if cond 退化等子场景均未覆盖。

### 关键代码位置
- region_analyzer.py:10646-10714（`_collect_branch_blocks` BFS 进入子 region 内部块）
- region_analyzer.py:10992-11190（`_build_elif_region` elif body 收集）
- region_ast_generator.py:6882-7068（`_if_generate_full_elif_chain` trailing_return 处理）

### 违反原则
- 原则 2（每块唯一归属）：else 子句被 LoopRegion/TryExcept 与 IfRegion 同时争抢；隐式 return None 被重复生成。
- 原则 3（嵌套即抽象节点）：LoopRegion/TryExceptRegion/嵌套 IfRegion 应作 then_blocks/elif_bodies 的不透明子节点，不应被 BFS 拆解。

### 修复方向
在 `_collect_branch_blocks` 中，遇到 `block_to_region[b]` 是 LoopRegion/WhileLoop/ForLoop/TryExceptRegion/WithRegion/嵌套 IfRegion 等"已归约区域 entry"时，把该区域作为整体加入 branch_blocks 并**停止 BFS 进入其内部 blocks**（body_blocks/else_blocks/finally_blocks），仅沿 region.exit 后继继续收集。同时把 LoopRegion.else_blocks、TryExceptRegion.else_blocks/finally_blocks 加入 IfRegion.branch boundary_stop。对生成器函数，`_if_generate_full_elif_chain` 检测当前函数含 YIELD_VALUE 时剥离 elif 末尾隐式 return None。

---

## C8 — 多 with 上下文 + 嵌套 with 子 WithRegion 被平铺（R21-C6 未修复，P2，2 测试）

### 涉及测试
- `test_adv19_with_multi_ctx_in_if_body` — `with open('a') as fa, open('b') as fb: data = fa.read(); with open('c') as fc: data += fc.read(); return data + fb.read()`
- `test_adv20_nested_with_try_in_elif_body` — elif body 内 `with open(path) as f1: try: data = f1.read(); if data: with open(path+'.bak') as f2: f2.write(data); return 'written'; else: return 'empty'; except IOError as e: return str(e)`

### 反编译输出（实测）
- adv19_with_multi_ctx_in_if_body → `def f(flag):\n    if flag:\n        with open('a') as fa, open('b') as fb, open('c') as fc:\n            data += fc.read()\n            with open('c') as fc: pass\n        (data + fb.read())\n        return None(None, None)`（内层 `with open('c') as fc` 被平铺到外层 with context 列表，外层 with body 只剩 `data += fc.read()`，`return data + fb.read()` 退化为裸表达式 + `return None(None, None)`）
- adv20_nested_with_try_in_elif_body → `指令108参数不匹配: none vs None (op=LOAD_CONST)`（嵌套 with + try cleanup 块顺序被打乱，co_consts 索引错位，字符串 `"none"` 被替换为 Python `None`）

### 根因（从内层到外层）
1. **内层**：外层 `with open('a') as fa, open('b') as fb:` 多 context 与内层 `with open('c') as fc:` 嵌套 with 共享同一段 cleanup 块（WITH_EXCEPT_START 链）。
2. **中层**：`_identify_with_regions`（region_analyzer.py:7237-7265）把内层 with 的 BEFORE_WITH + STORE_FAST 也吸收到外层 WithRegion 的 context 列表，未把内层 with 作为独立子区域处理。
3. **外层**：AST 生成时三个 BEFORE_WITH 全部作为外层 with 的 items，外层 with body 只剩内层 with body 的部分语句；`return data + fb.read()` 被剥离为裸表达式。嵌套 with + try 场景，cleanup 块顺序被打乱导致 co_consts 索引错位（字符串常量与 None 索引互换）。

### 违反原则
- 原则 3（嵌套即抽象节点）：内层 with 应作外层 with body 的子节点，不应平铺到 context 列表。
- 原则 4（父引用子入口）：父区域通过 LOAD_CONST 索引引用子区域常量，索引错位导致语义改变。

### 修复方向
在 `_identify_with_regions` 中，对每个 BEFORE_WITH + SETUP_WITH 对检测其是否位于另一个 WithRegion 的 body 内，若是则作为嵌套 WithRegion 单独识别，父 WithRegion 通过 body 引用子 WithRegion.entry。生成 cleanup 块时严格保留原始 LOAD_CONST 的 argval（字符串 vs None），不根据 cleanup 模板硬编码 None。

---

## C9 — lambda IIFE 递归反编译 body 退化（R21-C7 未修复，P2，1 测试）

### 涉及测试
- `test_adv19_lambda_iife_in_if_cond` — `if (lambda x: x > 0)(y) and (lambda x: x < 100)(y): return 'valid'\nelif (lambda x: x == 0)(y): return 'zero'\nelse: return 'invalid'`

### 反编译输出（实测）
`def f(y):\n    if ((lambda x: x > 0)(y) and (lambda x: x < 100)(y)): return 'valid'\n    elif (lambda *args, **kwargs: None)(y): return 'zero'\n    return 'invalid'`（if 条件中两个 lambda IIFE 正确，但 elif 条件的 lambda `(lambda x: x == 0)(y)` 退化为 `(lambda *args, **kwargs: None)(y)`，body `x == 0` 比较丢失）

错误信息：`嵌套code object不匹配 (指令16): 指令数不匹配: 5 vs 3`（嵌套 lambda code object 原始 5 条 `RESUME, LOAD_FAST x, LOAD_CONST 0, COMPARE_OP, RETURN_VALUE`，重编 3 条 `RESUME, LOAD_CONST None, RETURN_VALUE`）。

### 根因（从内层到外层）
1. **内层**：elif 条件的 lambda code object 含 `LOAD_FAST x, LOAD_CONST 0, COMPARE_OP ==, RETURN_VALUE`（`return x == 0`）。
2. **中层**：lambda code object 递归反编译时，简单 `return expr` 模式（含 COMPARE_OP + RETURN_VALUE）未被正确识别为 Return.value 子节点，body 退化为隐式 `return None`。if 条件中的两个 lambda（经 BoolOpRegion 处理）正确反编译，elif 条件的 lambda（经 elif 链处理）退化——递归反编译路径对 elif 上下文的 lambda code object 处理不一致。
3. **外层**：elif lambda body 退化导致整个 `return 'zero'` 分支条件失真，但 if-elif-else 结构骨架保留。

### 违反原则
- 原则 1（自底向上归约）：lambda body 内的比较表达式应识别为 Return.value 子节点，而非退化为隐式 return None。

### 修复方向
在 lambda code object 递归反编译路径中，确保简单 `return expr` 模式（含 COMPARE_OP + RETURN_VALUE）被正确识别为 Return 节点；统一 if-cond 上下文与 elif-cond 上下文的 lambda code object 递归反编译处理，避免 elif 路径走简化分支。

---

## C10 — if body 内复杂表达式多块结构被拆解（P2，4 测试）

### 涉及测试
- `test_adv18_raise_from_complex_in_if_body` — 三分支各自 `raise ValueError(...) from RuntimeError(...)`
- `test_adv20_tuple_return_in_branches` — 三分支各自 return 多类型嵌套 tuple（含 BUILD_SET + genexp）
- `test_adv20_dictcomp_complex_filter_in_branches` — 三分支各自 return dictcomp/setcomp（多 for + if 过滤）
- `test_adv20_star_expr_in_call_in_if_body` — 三分支各自含 `*args`/`**kwargs`/lambda 闭包/listcomp

### 反编译输出（实测）
- adv18_raise_from_complex_in_if_body → `def f(x):\n    if (x > 0): raise 'orig_pos'\n    elif (x < 0): raise 'orig_neg'\n    else: raise 'orig_zero'`（`raise ValueError('positive') from RuntimeError('orig_pos')` 退化为 `raise 'orig_pos'`——from 子句 cause 丢失，主异常 ValueError('positive') 也丢失，重编少 21 条）
- adv20_tuple_return_in_branches → `... else: return (x for x in range(3))`（else 分支 `return ((), [], {}, {x, x+1}, (x for x in range(3)))` 坍塌为 `return (x for x in range(3))`，BUILD_SET 与 `(), [], {}` 丢失，重编少 9 条）
- adv20_dictcomp_complex_filter_in_branches → `... if (flag == 'dict'): return {k: v * 2 for k, v, x in data.items() if k != 'skip' and x > 0}`（dict 分支 `for x in [v]` 子句丢失，dictcomp 变成 `{k: v * 2 for k, v, x in data.items() if ...}` 多出 target `x`，嵌套 code object 不匹配）
- adv20_star_expr_in_call_in_if_body → `... if (flag == 'a'): return sorted(*items, key=(lambda *args, **kwargs: None), **extra)`（`key=lambda x: -x` 退化为 `lambda *args, **kwargs: None`，listcomp `for k, v in extra.items()` 子句丢失，MAKE_CELL/LOAD_CLOSURE 闭包 cell 丢失，重编少 3 条）

### 根因（从内层到外层）
1. **内层**：raise-from 的 `LOAD_GLOBAL ValueError, LOAD_CONST 'positive', CALL, LOAD_GLOBAL RuntimeError, LOAD_CONST 'orig_pos', CALL, RAISE_VARARGS 3` 跨多块；tuple return 的 `BUILD_SET + GET_ITER + MAKE_FUNCTION`（genexp）跨多块；dictcomp 多 for + if 过滤是独立 code object；lambda 闭包含 `MAKE_CELL + LOAD_CLOSURE + BUILD_TUPLE` prologue。
2. **中层**：`_collect_branch_blocks` BFS 拆解这些多块表达式结构：raise-from 的 `from Y` 块（`LOAD_GLOBAL RuntimeError + CALL`）与 RAISE_VARARGS 块分离，只保留 cause 字符串；BUILD_SET/genexp 元素块与 BUILD_TUPLE 块分离，set 与 genexp 丢失；dictcomp 内层 `for x in [v]` 子句块被剥离；lambda 闭包 MAKE_CELL/LOAD_CLOSURE prologue 被当作独立 BASIC 块收集或丢失。
3. **外层**：AST 生成时这些表达式各自残缺：raise 退化为 `raise <cause_str>`；tuple 退化为只剩 genexp；dictcomp 多出/丢失 for target；lambda 闭包退化为 `lambda *args, **kwargs: None`。

### 违反原则
- 原则 3（嵌套即抽象节点）：`raise X from Y` 应作单一 Raise 节点（X、Y 为子表达式）；BUILD_SET + genexp 应作 tuple 元素子节点；dictcomp 多 for + if 应作单一 comprehension 子节点；lambda 闭包 cell 应作独立 code object 子节点。

### 修复方向
- `_collect_branch_blocks`：遇到 RAISE_VARARGS 前驱块链含 `LOAD_GLOBAL + CALL`（from 子句）时，把整段作为单一 Raise 节点停止 BFS 拆解；遇到 BUILD_SET/BUILD_MAP/BUILD_TUPLE 后跟 GET_ITER + MAKE_FUNCTION 的 genexp pattern 时，把整段作为单一表达式块停止拆解。
- lambda 闭包：识别 `MAKE_CELL/LOAD_CLOSURE + BUILD_TUPLE` prologue 并保留为闭包语义，不当作独立语句；listcomp/dictcomp 的多 for + if 子句应完整保留为 comprehension 的 generators 列表。

---

## 测试覆盖与验证方法

### 已分析测试（34 个，覆盖 10 个根因簇）

| 簇 | 测试数 | 测试列表 |
|----|--------|----------|
| C1 | 3 | adv01_nested_ternary_cond, adv13_ternary_and_ternary_boolop, adv13_ternary_three_or_cond |
| C2 | 5 | adv14_walrus_ternary_attr, adv14_walrus_ternary_binary_op, adv14_walrus_ternary_method, adv14_walrus_ternary_subscr, adv15_walrus_ternary_cond |
| C3 | 3 | adv18_assert_in_if_body, adv19_assert_chained_cmp_in_if_body, adv20_assert_chained_cmp_in_branches |
| C4 | 3 | adv19_for_continue_in_each_branch, adv19_mixed_complex_branches, adv20_for_else_break_in_each_branch |
| C5 | 3 | adv18_nested_ternary_in_elif_cond, adv18_if_with_chained_compare_cond, adv19_chained_in_check_in_if_cond |
| C6 | 3 | adv15_ternary_in_tuple_unpack, adv15_ternary_slice_in_body, adv15_ternary_in_chain_compare_body |
| C7 | 7 | adv18_try_finally_in_if_body, adv19_try_except_else_in_if_body, adv19_while_else_break_in_elif_body, adv19_tuple_unpack_in_if_body, adv19_multiline_return_in_if_body, adv20_walrus_in_while_cond_nested_if, adv20_yield_in_while_in_if_body |
| C8 | 2 | adv19_with_multi_ctx_in_if_body, adv20_nested_with_try_in_elif_body |
| C9 | 1 | adv19_lambda_iife_in_if_cond |
| C10 | 4 | adv18_raise_from_complex_in_if_body, adv20_tuple_return_in_branches, adv20_dictcomp_complex_filter_in_branches, adv20_star_expr_in_call_in_if_body |
| **合计** | **34** | |

### 验证方法

1. 全量失败列表：`cd /workspace && timeout 290 python -m pytest tests/exhaustive/if_region/ --tb=no -q --no-header 2>&1 | grep -E "^FAILED" | sort`（确认 34 failed / 783 passed / 10 skipped）
2. 反编译输出验证：`cd /workspace && timeout 120 python _r22_debug3.py`（打印 21 个代表性失败用例的反编译输出，已在分析中引用）
3. 区域结构验证：`cd /workspace && timeout 60 python _r22_debug2.py`（打印 walrus+三元 if 条件的块/区域/block_to_region 映射，确认 C2 根因）

### 修复优先级建议

1. **P0 - 先修 C2 + C3 + C4 + C7**（共 18 测试）：
   - C2（5 测试）：`_generate_if` entry-generated 检查丢弃 IfRegion — 修一处覆盖 5 测试
   - C3（3 测试）：AssertRegion 抢占 if 头 — 修 assert 严格判据
   - C4（3 测试）：for-分支 if 头被 ternary 抢占 — 修 ternary 候选排除 GET_ITER/FOR_ITER
   - C7（7 测试）：嵌套 region 不透明子节点 — 修 `_collect_branch_blocks` BFS 不进入子 region 内部块
2. **P1 - 再修 C1 + C5 + C6**（共 9 测试）：
   - C1（3 测试）：多三元/嵌套三元 boolop 链 — 修 BoolOp op_chain trimming + redirect 多元覆盖
   - C5（3 测试）：elif 链复杂条件 — 修 `_check_elif_chain` 调 `_detect_chained_compare_pattern` + ternary merge 传递
   - C6（3 测试）：三元在容器内 — 修兄弟三元组装为 Tuple/Slice + 保留 STORE 目标
3. **P2 - 最后修 C8 + C9 + C10**（共 7 测试）：嵌套 with / lambda IIFE / 复杂表达式多块拆解

### 修复后验证命令
```bash
cd /workspace && timeout 280 python -m pytest tests/exhaustive/if_region/ -q --tb=short
```
目标：34 failed → 0 failed，且 ternary region（`tests/exhaustive/ternary_region/`）0 回归。

---

## 关键发现总结（一段话）

本轮 34 个 IF 区域失败用例可归因为 10 个独立根因簇（C1–C10），其中最关键的新发现是 **C2（5 测试，P0）**：当 if 条件为 `walrus 绑定三元后再做属性/下标/方法/二元运算/比较`（如 `if (x := a if c else b).field > 0: pass`）时，R21-C1 的 `_ternary_if_cond_redirect` 正确把 IfRegion.condition_block 重定向到三元 merge_block，但因 IfRegion.entry 与 TernaryRegion.entry 共享同一块，`_generate_if`（region_ast_generator.py:6629-6641）的 `entry in generated_blocks` 检查在 TernaryRegion 先生成后把整个 IfRegion 丢弃，输出坍塌为 `pass`——这是 R21 修复的盲区（R21-C1 只覆盖 `(ternary) and b` 这类有 BoolOpRegion 的场景，未覆盖 walrus+三元无 boolop 的场景）。其次，R21 的 C3/C4 修复均不完整：C6（3 测试）显示多元组/切片/链式比较含三元的父表达式归约仍失败（兄弟三元未组装为 Tuple/Slice、chain compare 丢失 STORE 目标），C7（7 测试）显示 if body 内嵌套 loop-else/try-else/nested-if 的 `_collect_branch_blocks` 仍 BFS 进入子 region 内部块导致 else 子句争抢、隐式 return 重复、嵌套 if cond 退化为裸表达式。新增的 C3（AssertRegion 抢占 if-elif-else 头块，3 测试）与 C4（三分支均以 for 开头时 if 头被 TernaryRegion 抢占，3 测试）是 IF 区域整体坍塌为三元表达式的两类 P0 根因。违反原则集中在原则 2（每块唯一归属，8 簇）与原则 3（嵌套即抽象节点，6 簇），建议按 P0（C2/C3/C4/C7，18 测试）→ P1（C1/C5/C6，9 测试）→ P2（C8/C9/C10，7 测试）顺序修复。
