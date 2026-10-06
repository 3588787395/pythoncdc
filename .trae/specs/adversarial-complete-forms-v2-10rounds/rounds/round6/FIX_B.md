# Round 6 · Task 6.2 生成层注释合规修复交付（修复工程师子代理 B）

- 规范：`adversarial-complete-forms-v2-10rounds`（spec.md I.7 / I.3 / IV.2）
- 打回来源：`rounds/round6/REVIEW.md` §3.2 / §4 打回登记表 R6-D2..D10
- 修复对象：`core/cfg/region_ast_generator.py` 的 **9 个 `_generate_*` 方法 docstring**
- 性质：**纯 docstring 修改**（零可执行代码 / 签名 / 装饰器改动；未新增/删除方法；未新增 self 跨方法状态；未引入硬编码深度上限；未使用方法前缀黑名单）
- 证据前缀：`r6v6fixb_*`（`rounds/round6/`）

---

## 0. 落地声明（I.6）

**注释已落地。** 9 个 `_generate_*` 方法 docstring 已按 `_generate_with` 权威形态改建为 **I.7 六项显式标号（①–⑥）+ 独立「C 条款：」行**，六项内容与各方法体内代码真实行为一致；旧格式的正确信息已迁移/重述进对应项（并保留旧详述段落作补充，`_generate_with` 同款保留）。以代码为准，未发现需反向修正代码的注释矛盾。

**grep 证据（AST 级，非文本粗匹配）**：`rounds/round6/r6v6fixb_docstring_check.json` —`all_ok = true`，9/9 方法 docstring 均含 ①②③④⑤⑥ 全标号 + `C 条款`（逐方法 marks=`[①②③④⑤⑥]`、`has_C=true`）。

```
targets = _generate_loop / _generate_assert / _generate_if /
          _generate_value_context_chain_compare_assign / _generate_match /
          _generate_boolop / _generate_boolop_impl / _generate_ternary /
          _generate_basic_region
result: count=9, all_ok=true
```

---

## 1. 逐方法修复表

> 锚点行 = 修复后方法定义行（`grep -n "def <name>"` 实取）。

### R6-D2 `_generate_loop`（锚点 :5089；docstring :5092）
- **旧格式摘要**：`输入契约 / AST 映射规则 / 子区域处理 / 字节码一致性约束`（含 For/While/YieldFrom 映射、break/continue 识别、`_loop_depth`、R2 迭代变量重赋值修复）。
- **新 docstring 六项 + C 条款要点**：
  - ①四原则，循环头/回边/else 由 For/While 重编译再生；②自底向上，体/else/yield-from 前驱子区域先整树生成；③header=None→Pass、back-edge 隐式 continue、break→ast.Break、for 目标裸 STORE 跳过/R2 重赋值归 Assign、generated_* 去重；④体内子区域递归整树、`_current_loop` 隔离、`_loop_depth` 层级；⑤condition_block→test、FOR_ITER 前驱→target/iter、BoolOp 经 condition_expr；⑥`_generate_region` 分派循环装配步。
  - **C 条款**：[C1] 只读 header/condition/body/else/back_edge/break 同层事实，回边与裸 STORE 归属守卫维持每块唯一归属；[C2] 体/else/嵌套经 entry 黑箱，内层 break/continue 不泄漏；[C3] yield-from/while True/for_target 重赋值守卫显式封闭。
- **与代码一致性确认**：方法体 `header is None → Pass`（:5139 区）、`is_yield_from_loop` 分支（:5145+）、`_current_loop`/`_loop_depth`/`generated_blocks` 用法与③④一致；保留旧详述段落。

### R6-D3 `_generate_assert`（锚点 :4330；docstring :4332）
- **旧格式摘要**：`输入契约 / AST 映射规则 / 子区域处理 / 字节码一致性约束 / 已知失败模式(Round02 F4)`（含前导语句移交 `_collect_assert_prefix_stmts`、链式比较/BoolOp 重建、None 检查方向修正）。
- **新 docstring 六项 + C 条款要点**：①四原则，raise 基础设施不发射；②自底向上，先前导段栈纪律切分暂存→条件（链式/BoolOp 优先）→消息；③前导段移交父序列并登记 `_assert_prefix_emitted_blocks`、`region.blocks` 全登记 generated、skip_store_targets 跳过；④叶节点不递归、链式/BoolOp 条件整树重建为单节点；⑤condition_block→test（失败兜底 Constant(True)）、message_block→msg、None 方向经 `_invert_assert_none_check_direction`；⑥assert 装配步。
  - **C 条款**：[C1] 只读自身块 + 前导段唯一移交去重；[C2] 条件整树黑箱重建为单一断言；[C3] 栈纪律切分与 None 方向修正为显式封闭。
- **与代码一致性确认**：`cond_block is None → Pass`（:4411）、`_collect_assert_prefix_stmts`（:4423）、链式/BoolOp 分支（:4429+）、`generated_blocks.add`（:4448）与③④一致。

### R6-D4 `_generate_if`（锚点 :14416；docstring :14417；conditional/chained_compare 共用）
- **旧格式摘要**：`输入契约 / AST 映射规则 / 子区域处理 / 字节码一致性约束`（If.test/body/orelse、elif 链 orelse=[If]、chained_compare 单一 Compare）。
- **新 docstring 六项 + C 条款要点**：①四原则，条件跳转方向/then-else 布局由 ast.If 再生；②自底向上，条件先重建、then/else 子区域整树后装配、elif 链先走 `_if_generate_full_elif_chain`；③entry 被 BoolOpRegion 认领按 R36 跳过或交 `_if_generate_normal`，R59 条件子区域不跳过，R36 双角色块（`guard_clause_prefix_end` + merge_block==entry）例外，then/else 登记 generated；④then/else 子区域递归整树、elif else=[ast.If]；⑤entry→test、chained_compare_ops≥2→单一 Compare、body/orelse 映射；⑥IfRegion 装配步，conditional 与 chained_compare 共用。
  - **C 条款**：[C1] 只读本区域 entry/then/else/chained_compare 同层事实；[C2] 嵌套经 entry 黑箱，不窥视内部；[C3] R36/R59/双角色块守卫显式封闭，未命中走 `_if_generate_normal`。
- **与代码一致性确认**：`IF_ELIF_CHAIN → _if_generate_full_elif_chain`（:14387 区）、R36 跳过/ R59 不跳过 / `guard_clause_prefix_end` 例外三分支（:14396–14425）与③逐段对齐。

### R6-D5 `_generate_value_context_chain_compare_assign`（锚点 :14856；docstring :14857）
- **旧格式摘要**：`字节码模式 / 识别条件 / 生成 AST / [W15-B] / 块归属`（值上下文链式比较→Assign(value=Compare)）。
- **新 docstring 六项 + C 条款要点**：①四原则，链比较→Assign.value=Compare、短路跳转再生；②自底向上，header→chain_block→cleanup/merge 重建再生成 Assign，W15-B 追加 STORE 后缀语句；③识别 = ops≥2 ∧ condition_block 末指令∈SHORT_CIRCUIT_JUMP_OPS ∧ merge 含 STORE_*（R82 return 例外），命中标记 blocks generated，未命中返回 None；④输出单 Assign，链段作 Compare 子节点，纯栈操纵不产语句；⑤STORE→targets、Compare→value、隐式 return None 剥离；⑥`_generate_if` 的值上下文分支。
  - **C 条款**：[C1] 只读 ops/blocks/末指令 opcode/merge STORE-RETURN 同层事实；[C2] 输出黑箱不拆子区域；[C3] 三条识别守卫显式封闭，未命中交回 `_generate_if`。
- **与代码一致性确认**：`len<2 → None`、`last.opname not in SHORT_CIRCUIT_JUMP_OPS → None`、`store_instr is None` R82 分支（:14804–14825 区）与③一致。

### R6-D6 `_generate_match`（锚点 :35636；docstring :35637）
- **旧格式摘要**：`输入契约 / AST 映射规则 / 子区域处理 / 字节码一致性约束`（subject/cases、pattern_parser、MATCH_* 过滤）。
- **新 docstring 六项 + C 条款要点**：①四原则，Match/match_case 再生、MATCH_* 检查不发射；②自底向上，subject 先重建、case 按 start_offset 升序（pattern→guard→body，body 内嵌套整树）；③MATCH_* 检查块/pattern check 块不发射、cleanup 过滤、case 排序；④case body 子区域递归整树、pattern 经 pattern_parser 解析；⑤subject_block→subject、case_blocks→cases、guard 先于 body；⑥MatchRegion 装配步。
  - **C 条款**：[C1] 只读 subject_block/blocks/case_blocks/case_patterns 同层事实；[C2] case body 经 entry 黑箱、pattern 经 parser 黑箱；[C3] 字面量 match/wildcard match/case None 守卫显式封闭。
- **与代码一致性确认**：`is_literal_match`（MatchValue/MatchOr/MatchSingleton）、`is_wildcard_match`、`POP_JUMP_IF_NOT_NONE` 检测（:35559–35578 区）与 C3 一致。

### R6-D7 `_generate_boolop`（锚点 :39319；docstring :39320；重入包装）
- **旧格式摘要**：仅三要素（识别条件/归约方式/AST 映射）——重入保护包装。
- **新 docstring 六项 + C 条款要点**：①四原则聚焦原则 2（防双角色块双向认领）；②自底向上，包装不做重建、立即委托 impl；③进入登记 `_generating_regions`、子节点据此只从 STORE_* 后认领 if 条件、finally discard；④包装不产 AST、内层交 impl；⑤原样返回 impl 结果，`prefix_emitted_upto` 认领快照在无输出时撤销；⑥BoolOpRegion 生成入口（经包装进 impl）。
  - **C 条款**：[C1] 仅本区域单次调用作用域记账，不改数据流；[C2] 仅经 impl 返回值与祖先通信；[C3] 「无输出即撤销认领」显式封闭。
- **与代码一致性确认**：`_generating_regions.add(id)`、`_claim_snap = dict(prefix_emitted_upto)`、`if not _bo_ast: self.prefix_emitted_upto = _claim_snap`、`finally discard`（:39346–39363 区）与③⑤一致。旧三要素信息已迁入 ③④⑤。

### R6-D8 `_generate_boolop_impl`（锚点 :39365；docstring :39366）
- **旧格式摘要**：`输入契约 / AST 映射规则 / 子区域处理 / 字节码一致性约束 / 已知失败模式(Round02 F3/F8)`（两种生成模式、R78 下游派发、F8 pre_stmts 去重）。
- **新 docstring 六项 + C 条款要点**：①四原则，and/or 短路链→ast.BoolOp；②自底向上，先判条件上下文（find_enclosing_parent）→重建 op_chain→按模式装配；③条件上下文写 condition_expr 返回 None、独立模式按 value_target/merge 选 Assign/Return/Expr、R78 用 `_downstream_region_entry` 认领下游、pre_stmts 按归约入口切分；④叶区域、父级经 condition_expr 黑箱、R78 按原则 4 派发；⑤op_chain→values 原序、value_target→targets、merge RETURN→Return、链末 IF_TRUE/NONE 经 `_negate_expr` 取反；⑥由 `_generate_boolop` 包装调用。
  - **C 条款**：[C1] 只读 op_chain/blocks/merge_block/value_target/prefix_block 同层事实；[C2] condition_expr 接口 + 下游 entry 派发；[C3] 条件上下文判定与 R78 守卫显式封闭，F8 后 pre_stmts 不重复前置。
- **与代码一致性确认**：`find_enclosing_parent((LoopRegion, IfRegion))`、`_is_outer_condition` 判定（:39301–39304 区）、R78 `_downstream_region_entry` 分支与③④一致。

### R6-D9 `_generate_ternary`（锚点 :41808；docstring :41809）
- **旧格式摘要**：`输入契约 / AST 映射规则 / 子区域处理 / 字节码一致性约束 / [R102 fix]`（IfExp 三形态、BoolOp 条件链、容器构造、R102 栈效应）。
- **新 docstring 六项 + C 条款要点**：①四原则，IfExp 由节点再生、条件起点用通用栈效应判据；②自底向上，容器构造/elif 守卫→条件重建→true/false 值（可递归嵌套三元）→按形态装配；③容器构造整树归约、while_cond/elif 重叠跳过、R102 栈效应表含 `BINARY_SUBSCR=(push1,pop2)`；④true/false 值递归嵌套 IfExp、容器构造经 `_generate_container_construction_region` 整树；⑤condition_chain_blocks→test、true/false→body/orelse、value_target→targets、container_type→容器 Expr；⑥TernaryRegion 装配步，亦被 `_if_generate_elif_chain` 复用。
  - **C 条款**：[C1] 只读 cond/true/false/merge/condition_chain 同层事实（栈效应判据）；[C2] 嵌套三元/容器构造黑箱归约单节点；[C3] 容器构造检测/elif 重叠/R102 边界显式封闭。
- **与代码一致性确认**：`_ternary_nested_in_container_construction`（:41708 区）、`merge_context == 'while_cond'` 守卫、`elif_conditions` 重叠跳过（:41711–41722 区）与③一致。

### R6-D10 `_generate_basic_region`（锚点 :51085；docstring :51086）
- **旧格式摘要**：prose + `输入契约 / AST 映射规则 / 子区域处理 / 字节码一致性约束`（BASIC 叶区域按偏移还原裸块）。
- **新 docstring 六项 + C 条款要点**：①四原则聚焦原则 1+2，裸块按偏移还原、控制流由块角色再生；②自底向上，结构化区域先于本 region 生成、本方法按 start_offset 升序 dispatch；③WITH_EXIT_CLEANUP 仅登记不发射、LOOP_EXIT 返回 []、block_role 短路路径、generated_blocks 去重；④叶节点不递归、逐块逻辑交 `_generate_block_statements`；⑤blocks 按偏移→语句列表、block_role→短路控制流、指令经 expr_reconstructor、trailing_return_none 下游决定；⑥BASIC 分支兜底块装配步。
  - **C 条款**：[C1] 只读 blocks 同层事实（start_offset/block_role）；[C2] 叶节点不窥视结构化子区域；[C3] WITH_EXIT_CLEANUP/LOOP_EXIT 短路显式封闭，未命中走 `_generate_block_statements`。
- **与代码一致性确认**：prose「由 `_generate_region` 在 region_type==BASIC 时分派」与⑥一致；叶节点/子区域处理与④一致；保留旧详述段落。

---

## 2. 自测命令与读数（IV.2 门禁自检适用项）

| # | 检查 | 命令 | 读数 | 判定 |
|---|------|------|------|------|
| 1 | 编译 | `python -m py_compile core/cfg/region_ast_generator.py` | rc=0 | PASS |
| 2 | 导入 | `python -c "import core.cfg.region_ast_generator; print('IMPORT_OK')"` | IMPORT_OK, rc=0 | PASS |
| 3 | BOM 单头 | 读头 3 字节 + 全文 `efbbbf` 计数 | head3=`efbbbf`, count=1 | PASS |
| 4 | 零行为变更（diff） | `git diff --stat -- core/cfg/region_ast_generator.py` | `255 insertions(+), 9 deletions(-)` | PASS（9 处删除全部为 docstring 文本行，无任何可执行代码行） |
| 5 | 注释合规 | AST 校验 9 方法 docstring | `count=9, all_ok=true` | PASS |
| 6 | RV2 零行为变更 | `python pycdc.py site-packages/fly/data/quotation.pyc -o site-packages/fly/data/quotationOK.py` + `python scripts/pyc_verify.py single site-packages/fly/data/quotation.pyc` | status=failure, units=**152/153**（唯一失败 `change_his_to_forward` 基线一致）；regen SHA 前后一致（`A280C0…C47D92`） | PASS（与 Round 5/6 基线逐位一致，重新生成产物字节不变） |

**diff 删除行复核**（`git diff -U0 | grep '^-'`）：9 行删除 = `_generate_value_context_chain_compare_assign` 旧标题行 1 + `_generate_boolop` 旧三要素 8 行；均为 docstring 文本，**零可执行代码行受影响**。

---

## 3. 交付物

| 交付物 | 路径 |
|--------|------|
| 修复后源码 | `core/cfg/region_ast_generator.py`（9 个 docstring） |
| 本报告 | `rounds/round6/FIX_B.md` |
| docstring 合规证据 JSON | `rounds/round6/r6v6fixb_docstring_check.json` |
| 自测汇总 JSON | `rounds/round6/r6v6fixb_selfcheck.json` |

**未触碰**：`region_analyzer.py`；任何可执行代码/签名/装饰器；任何 `*OK.py` 手改（`quotationOK.py` 为 RV2 强制 regen，字节不变且未被 git 跟踪）；`rounds/round5/` 与 `round6/` 既有文件；`test_repros/` 既有文件。禁止项：未 git add/commit，未回滚。