# ORANDCHAIN_IF：or 首 + and 尾 + 终止臂短路链尾成员归位修复（rr-v5r111，REAL46-036 闭合）

## 家族选定与真实案面

rr-v5r110 后 46 真实 pyc sweep 读数 13 DIFFERENT / 15 EQUAL / 17 ERROR+skip1。
本轮选 **REAL46-036**（`D:\Python\Lib\site-packages\pandas\core\indexing.py`，
pyc `...\__pycache__\indexing.cpython-311.pyc`）。唯一 R7 =
`$.metadata.code.co_consts.v[71].code_sha`，即函数 **`check_dict_or_set_indexers`**：
`co_code` 338B 中仅 3 个跳转 oparg 不同，其余字段全同（证据
`D:/temp/opencode/cl_layout/r111diag_a/fielddiff_036.txt`、`dis036.txt`、
`semantic_036_v110_recheck.json`）。

源码 `indexing.py:2780-2796` 是**两个独立** `if A or (B and C): raise TypeError`；
产品（`prod_v110_recheck.py` 约 2001-2010 行）渲染成：

```python
if A or B and C:
    raise TypeError(...)          # 第一臂：文本等价（A or B and C == A or (B and C)）
elif A or B:                      # 第二臂：被拆成 (A or B) and C —— 语义错误
    if C:
        raise TypeError(...)
    return None
```

第二臂里 `A` 为真时不再直达 raise，而是继续测 `C`：`key` 为 dict 时原件
`raise TypeError`、产品 `return None`。正确形态是
`If(BoolOp(or,[A, BoolOp(and,[B,C])]), body=[Raise])`；错误 AST 是
`If(BoolOp(or,[A,B]), body=[If(C,[Raise])])`。注意 Python 文本
`A or B and C` 与 `A or (B and C)` 等价，但**嵌套 if 不等价**。

族特征：**or 首 + and 尾 + 终止臂（raise/return）+ 臂后无语句**。与历史已修族
不同——`[v100-ORTAIL]` 是 and 链尾嵌套 or；`[v106-ANDORTAIL]` 是
`A and B and C and (D or E)`；`[v110-MCSUB]` 是 for 迭代前缀链式赋值。本族断链
发生在**假边目标**而非真边目标，且终止臂导致两条等价的平凡出口块。

## 精确缺陷位点（插桩 / 区域树 dump / 反汇编）

诊断证据：`evidence_tree_dump.txt`（`probe_tree.py` 区域树）、
`evidence_discriminator.txt`（`discriminator.py` 字节码并排）、
`D:/temp/opencode/cl_layout/r111diag_a/probe_hook2.py`（生成端消费者插桩）、
`probe_ast.py`（最终 AST dump）。以下偏移均为**最小复现案**的块偏移，仅作
说明；修复判据不依赖任何具体偏移值、变量/函数名、测试名或 B 编号。

### ① 字节码布局与断链机制

CPython 3.11 把 `if A or (B and C): raise` 编译为（`m4_single_if`，
`evidence_tree_dump.txt:57-63`）：

```
@0    A;  POP_JUMP_FORWARD_IF_TRUE  -> 136   # 真边直达 T（raise body）
@44   B;  POP_JUMP_FORWARD_IF_FALSE -> 166   # 假边 F_B
@86   C;  POP_JUMP_FORWARD_IF_FALSE -> 170   # 假边 F_C
@136  T:  RAISE_VARARGS                      # 终止臂
@166  F_B: LOAD_CONST None; RETURN_VALUE     # 平凡隐式出口 1
@170  F_C: LOAD_CONST None; RETURN_VALUE     # 平凡隐式出口 2
```

**关键**：当 if 臂以 raise/return 终止且其后无语句时，`F_B` 与 `F_C` 是
**两个不同偏移、但语义等价的平凡隐式 return-None 块**。分析端
`region_analyzer.py` 的 BoolOp 短路链走查以「相邻腿假边目标同一」把 B、C
串成 and 链；此处 `166 != 170`，判据在 B 处失败 → `op_chain` 截断。

区域树直证（`evidence_tree_dump.txt:76-98`）：
- `m4_single_if`：`BoolOpRegion@0 op_chain=[(0,'or'),(44,'or')]`（**截断**：
  尾成员 C 未入链、B 被误标为 'or'），`merge=@166`；`IfRegion@86
  condition_block=@86` —— **C 沦为 then 体里的内层 IfRegion.condition_block**。
- 正确控制 `m5_two_if_diff_tail`（`:125-128`）：`op_chain=[(0,'or'),
  (44,'and'),(86,'and')]` 完整 3 成员；因为 B/C 假边都指向**同一个** @166
  （后续第二个 if 的条件块，非平凡出口），假边目标同一判据成立。
- `m1_exact`（`:28-52`）：主条件 `BoolOpRegion@0 op_chain=[(0,'or'),
  (44,'and'),(86,'and')]` 同样正确；缺陷出现在第二个 if/elif 臂——其
  `@250` 成为内层 `IfRegion@250 condition_block=@250`，产品渲染成
  `elif A' or B': if C': raise; return None`。

### ② 生成端消费者（probe_hook2.py 插桩定位）

- 单 If / 内层 If 主路径：`RegionASTGenerator._if_generate_normal`，出口
  `return if_result`（`m4_single_if` 的错误 If 节点由此产出）。
- if/elif 链路径：`RegionASTGenerator._if_generate_full_elif_chain`，构造
  `result = {'type':'If', 'test':..., 'body':..., 'orelse':...}` 后返回
  （`m1_exact` 的 elif 臂截断由此产出）；`_extract_condition_for_elif_block`
  负责 elif 条件单块重建。

即：分析端已把 C 错放成内层 IfRegion 的 condition_block，生成端两个出口都
只是**忠实**把这个错误区域树渲染成嵌套 If，没有二次判错。故修复落在生成端
出口做结构事实判据 + AST 归位，不动分析端、不动既有渲染逻辑。

### ③ 判别器密闭性（真嵌套 vs 复合条件互不混淆）

`evidence_discriminator.txt` 同长度（174B / 128B）并排反汇编：

| | 真嵌套 `if A or B: if C: raise` | 复合 `if A or (B and C): raise` |
|---|---|---|
| A 的 PJT 目标 | **C 块本身** @86（POP_JUMP_IF_FALSE 收尾） | **raise body** @136（RAISE_VARARGS 收尾） |
| C 的 fall-through | body @136（不等于 A 的 PJT 目标） | **恰为 T** @136（等于 A 的 PJT 目标） |
| B / C 假边 | 两个平凡 return-None 块 | 两个平凡 return-None 块 |

密闭判据靠「**A 的真边目标 T 是不是终止臂、且 C 的 fall-through 是不是 T**」
把两者互斥分开：真嵌套的 `T` 是条件块（非 RAISE/RETURN）、`C is T`，
复合条件的 `T` 是终止块、`C is not T` 且 `C_ft is T`。控制案
`v111_nested` / `v111_nested_bool` 在修复后 A/B **TEXT-SAME** 实证未被误伤。

## 修复（region_ast_generator 只增不破，`[v111-ORAND]`，单文件 +209 行 diff）

仅改 `core/cfg/region_ast_generator.py`；`region_analyzer.py` 零改动。补丁
`fix_patch_v5r111.diff`。新增 4 个方法与 2 处出口调用，**不删/不改任何既有
逻辑，不认领块、不登记 generated**：

- `_v111_is_implicit_return_none(blk)`：只读块内 opcode/常量，识别
  `LOAD_CONST None; RETURN_VALUE` 或 `RETURN_CONST None` 平凡出口。
- `_v111_reconstruct_operand(blk)`：剔除跳转/噪声后重建短路链块操作数。
- `_v111_truncated_or_tail_exprs()`：遍历区域树找截断链，返回尾成员 C 的
  重建表达式。**全部为块图/指令序/区域树结构事实**，无名字/偏移/计数/测试名：
  1. `BoolOpRegion.op_chain >= 2`，首块以 `IF_TRUE` 族收尾（or 首），跳转目标
     `T` 以 `RAISE_VARARGS/RETURN_VALUE/RETURN_CONST` 收尾（终止臂）；
  2. 链末块 B 以 `IF_FALSE` 族收尾，假边 `F_B`；
  3. B 的非跳转后继 C 为纯条件块、`IF_FALSE` 族收尾、假边 `F_C`，且
     **C 的 fall-through 恰为 T**；
  4. **`C is not T`**（排除真嵌套：其 A 的 PJT 就是 C 块）；
  5. `F_B` 与 `F_C` 均为平凡隐式 return-None 出口（本族的等价出口特征）；
  6. C 是某内层 `IfRegion` 的 `condition_block`，且块内不含
     `STORE_*`/`POP_TOP`（纯条件操作数块）。
  任一校验失败即不产出候选（C2 逐位回落）。
- `_v111_fixup_if_node(node)`：把
  `If(BoolOp(or,[A,B]), body=[If(C,[终止臂])])` 重写为
  `If(BoolOp(or,[A, BoolOp(and,[B,C])]), body=[终止臂])`，内层 if 的 body
  提升为外层 if 的 body。密闭校验：区域树存在**唯一**截断链、且其重建表达式
  与内层 if 的 `test` 结构一致（JSON 规范化比对）；否则逐位回落既有 AST。
  递归覆盖 `body`/`orelse`/`finalbody` 中的 elif 链与嵌套容器。

出口挂载（均带 `[v111-ORAND]` 注释）：
- `_if_generate_full_elif_chain`：`result = self._v111_fixup_if_node(result)`
- `_if_generate_normal`：`if_result = self._v111_fixup_if_node(if_result)`

`[C1]` 只读区域标注与块关系；`[C2]` 不命中逐位回落；`[C3]` 纯函数、无状态、
不认领块——所有非目标形态产品文本逐字节不变（A/B 实证见下）。

## 验证（全实测，权威判官 `semantic_diff.compare_case`）

- **正式复现矩阵 12 案全 BYTE-EQUAL**（`matrix_v5r111.py` /
  `matrix_v5r111_result.json`）：逐案 compile→pyc→pycdc→recompile，逐 code
  object 比对 `co_code/co_exceptiontable/co_consts/co_names/co_varnames/
  co_freevars/co_cellvars/co_flags`。功效案 4（`m1_exact` / `m2_no_genexpr` /
  `m4_single_if` / `two_if_diffmsg`）A/B **TEXT-DIFF 且 BYTE-EQUAL**；控制案
  8（真嵌套 / 真嵌套 bool / plain_or / plain_and / m3_plain_if /
  m5_diff_tail / or_and_else / return_arm）A/B **TEXT-SAME 8/8 且 BYTE-EQUAL**。
  A/B 用 `git show HEAD:` 交换 `region_ast_generator.py` 与 `region_analyzer.py`
  逐案实证，脚本 `finally` 断言恢复。
- **REAL46-036 整案 semantic_diff**（`sd_r111.py`）：`status: EQUAL, diffs: 0 []`，
  完成 **DIFFERENT → EQUAL**；**REAL46-004**（`enum.cpython-311.pyc`）复跑
  `status: EQUAL, diffs: 0 []`，维持闭合。
- **未领形态 3 案如实登记**（`unclaimed_v5r111.py` / `unclaimed_v5r111_result.json`）：
  `or_and3`（and 尾 3 成员，`a or not b or c and d` 取反）、`or3_and2`（or 链
  3 成员丢尾 `a or b or c`）、`prefix_stmts`（终止臂后仍有语句、`if not A:`
  翻转）。三者 v111 产品与 HEAD 产品**逐字节相同**（A/B TEXT-SAME 3/3），
  **HEAD 基线即 recompile DIFF**（`chg=['f']`），属分析端 BoolOp 链**另一缺陷族**
  （非「C 沦为内层 IfRegion.condition_block」），本轮窄修复未触碰、不计入
  正式矩阵，按纪律绝不发半修复。
- **A/B 回归电池**（`r111_regress.py` / `r111_regress_result.txt` / `.json`）：
  r110 的临时语料目录 r98 已被清理，故从 `r110_regress_result.txt` 提取 169
  案名、在 `fresh/` 各子目录按裸名/去后缀规则重建等价源（已核实
  `chainfor_foriter/ca6.py` 的函数 `g6` 与 r110 登记的 `chg=['g6']` 吻合），
  并加入本轮 15 案，共 **184 案**；逐案 A/B（v111 vs HEAD 55b36b1a）比产品
  文本 + 重编译签名。实测 **TEXT-DIFF 4 / 184，且 4 案恰为本轮功效案**
  （`m1_exact`/`m2_no_genexpr`/`m4_single_if`/`two_if_diffmsg`），其余 180 案
  A/B 全 **TEXT-SAME** —— C3 的 169+ 案强实证。10 个既有登记差中 9 个
  **严格 SAME-SIG**（`w28_shapes` w2/w3、`na5`、`pe8`、`pe8_target`、`nb2`、
  `ca6/ca13/ca15`、`cb5`）；`pd8_prod` 因 r98 产品语料不可恢复、以
  `pd8_registered.py` 等价源替代，签名由 `DIFF chg=['f']` 变 `BYTE-EQUAL`，
  但其 A/B **TEXT-SAME** 实证产品逐字节未变，如实单列为「语料替代案」，
  非本轮回归。`mc1` 的 r110 TEXT-DIFF→r111 TEXT-SAME 是 HEAD 已推进到含
  v110 修复所致（r111 仍 BYTE-EQUAL），亦非本轮回归。
  注：r110 对除 `mc1` 外各案均 TEXT-SAME（v110 产品 == 当时 HEAD 产品），
  故 r111 的「v111 产品 == HEAD 55b36b1a 产品」等价于「v111 产品与 r110
  产品逐字节相同」。构建脚本已排除证据目录自身的产品 .py 混入源候选
  （曾导致假 TEXT-DIFF，已修正并全量重生成）。
- **pytest 7 套件**（`pytest_v5r111.log`）：`tests/test_algorithm_correctness.py`
  / `test_boundary_cases.py` / `test_complete_syntax_coverage.py` /
  `test_control_flow_completeness_matrix.py` / `test_core_functional.py` /
  `test_deep_nesting_pressure.py` / `test_product_freshness.py`；实测
  **`3 failed / 277 passed / 2 xpassed`**：2 个冻结对
  （`TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、
  `TestBoundaryConditions::test_BOUNDARY_02_large_function`）+ 第 3 failed
  `TestProductFreshness::test_products_match_current_code`（在位 site-packages
  产物预存在陈旧，日志明示 "stale products ... not produced by the current
  code"，历史轮次已 A/B 实证非本轮引入）。**零新增失败**。
- **完整性**：`scripts/pyc_verify.py` SHA256 =
  `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4`；
  `tests/`、`tools/completeness/semantic_diff.py` 零改动；`core/` 仅
  `M core/cfg/region_ast_generator.py`；**未 git commit/push**。

## 历史族对照

| 族 | 形态 | 断链位置 |
|---|---|---|
| `[v100-ORTAIL]` | and 链尾嵌套 or | 真边目标 |
| `[v106-ANDORTAIL]` | `A and B and C and (D or E)` | and/or 交界 |
| `[v110-MCSUB]` | for 迭代前缀链式赋值 | for 提取器消费者 |
| **`[v111-ORAND]`** | **or 首 + and 尾 + 终止臂 + 臂后无语句** | **两条等价平凡 return-None 假边目标不同** |
