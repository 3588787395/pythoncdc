# NOTBOOLOP_ORAND：`not (or+and)` 值链双重取反 与 or 真出口极性反 修复（rr-v5r112，REAL46-001 闭合）

## 家族选定与真实案面

rr-v5r111 后选 **REAL46-001**（`D:\Python\Lib\dataclasses.py`，pyc
`D:\Python\Lib\__pycache__\dataclasses.cpython-311.pyc`）。HEAD `9139e4c3`
下整案 `semantic_diff.compare_case` = **DIFFERENT，2 个 R7**
（`semantic_REAL46-001.json`）：

- `$.metadata.code.co_consts.v[47].code_sha` = `_get_field`
- `$.metadata.code.co_consts.v[69].code_sha` = `_process_class`

前置只读诊断（`D:/temp/opencode/cl_layout/r112diag_b/`：
`diswin.txt`、`sem_probe.txt`、`minrepro.txt`、`fd001.txt`、
`m1..m8_*.py/.pyc`）已确认两处都是**可观察的真实功能错误**：

1. `_process_class`（源码 `dataclasses.py:1006`）
   原件 `has_explicit_hash = not (class_hash is MISSING or (class_hash is None and '__eq__' in cls.__dict__))`
   产品 `has_explicit_hash = not not (...)` —— 多渲染一个 `not`，极性反
   （`sem_probe.txt` 四组输入 ORIG/PROD 全反）。
2. `_get_field`（源码 `dataclasses.py:945-954` 同族形态）
   原件 `if _is_initvar(a_type, dataclasses) or (isinstance(f.type, str) and _is_type(...)): f._field_type = _FIELD_INITVAR`
   产品 `if not _is_initvar(...): if isinstance(...) and _is_type(...): ...`
   —— or 真出口极性反 + and 链被拆成嵌套 if（`sem_probe.txt` 实测
   ORIG `_FIELD_INITVAR` / PROD `_FIELD`，InitVar 识别失败）。

**本轮关键新发现**：`_process_class` 里除 `not not` 外，**还有第二处同族
or 真出口缺陷**——`if (_is_kw_only(type, dataclasses) or (isinstance(type, str) and _is_type(...))):`
同样被渲染成 `if not _is_kw_only(...): if ...`（产品 316-318 行）。故两个 R7
叶各含两处缺陷，须同一族判据一次闭合。

与 rr-v5r111 `[v111-ORAND]`（or 首 + and 尾 + **终止臂** + 两条等价平凡
return-None 假边目标不同）**不冲突**：v111 判据要求 `T` 以
RAISE/RETURN 收尾、C 沦为内层 `IfRegion.condition_block` 且假边为
平凡 return-None；本族 T 是**普通赋值/取反 body**，且 or 首成员根本
未入 op_chain（BoolOpRegion 缺首成员，或整链未形成 BoolOpRegion）。
两族判据互不相交，A/B 实证见回归电池。

## 精确缺陷位点（插桩 / 区域树 dump / 反汇编）

插桩脚本 `probe_v112.py`（各 BoolOp hook 返回值 + 最终 AST 里所有
`UnaryOp(not)` 节点路径）、`probe_tree_v112.py`（CFG 块 + 全区域平铺
dump，产物 `probe_*.txt` / `tree_*.txt`）；反汇编 `diswin.py`、
字段级比对 `fielddiff_diag.py`。偏移仅为说明，判据不依赖任何具体
偏移值/名字/测试名/B 编号。

### ① `not not`：merge 块 UNARY_NOT 被消费两次

`m4_not`（`r = not (a or b)`）区域树：

```
BoolOpRegion entry=@0 merge=@8 value_target=r cond_ctx=False
  op_chain=[(0,'or',('JUMP_IF_TRUE_OR_POP',8))]
  merge_instrs=['UNARY_NOT','STORE_FAST']
```

插桩 `probe_m4_not.txt`：
- `_build_boolop_expression_inner` → `UnaryOp(not, BoolOp(or,[a,b]))`
  （**已正确**；各 hook 的 merge-not 整链包裹按「merge 含
  UNARY_NOT」包一层 not，见 `region_ast_generator.py:48528`
  `_wrap_merge_unary_not` 与 `:49182-49189`、`:50133-50150` 三处镜像）；
- 最终 AST `/body/0/value` → `UnaryOp(not, UnaryOp(not, BoolOp(or,[a,b])))`
  （**双层**）。

第二个 `not` 的消费者定位在 `_generate_boolop_impl` 的
`value_target` 分支（`region_ast_generator.py:51870-51962`）：merge 块
`[UNARY_NOT, STORE_FAST]` 在 STORE 之前有 expression-continuation
`_pre_store=[UNARY_NOT]`，代码以 `initial_stack=[boolop_expr]` 调
`expr_reconstructor.reconstruct(_pre_store, ...)`，把同一条
`UNARY_NOT` 指令又作用到**已经包过 not** 的 `boolop_expr` 上
→ `not not (a or b)`。`m5_hash` 走 `_try_build_keeppop_target_grouped`
的 `_wrap_merge_unary_not`（`probe_m5_hash.txt:3`），同样单层 not 正确、
最终 AST 双层，证实是**统一消费者**重复消费，与哪个 hook 产出无关。

### ② `if not A: if B and C`：or 真出口被误当跳过出口

`m8_getfield` 区域树（`tree_m8_getfield.txt`）：

```
@514  PJT→712   succs=[592,712]   # A=_is_initvar(...) 真出口 = body
@592  PJF→736   succs=[736,644]   # B
@644  PJF→736   succs=[736,712]   # C 真 fall-through = 712 = T
@712  STORE_ATTR _field_type      # body T
@736  ...                        # F（后续）
BoolOpRegion entry=@592 merge=@736 op_chain=[(592,'and'),(644,'and')]
IfRegion entry=@514 merge=@712 parent=@486 then=[592,644] cond_lastj=PJT→712
IfRegion entry=@592 merge=@736 parent=@514 then=[712] cond_lastj=PJF→736
```

即：A 所在块 @514 同时承载前导语句 `dataclasses = sys.modules[...]`
（STORE_FAST），分析端 BoolOp 链走查不把它并入 op_chain，or 首成员
退化成 IfRegion 的条件（IF_TRUE 跳转极性被取反 ⇒ `not A`），余下 B/C
形成全 and 的 BoolOpRegion + 内层 IfRegion，产品遂渲染成
`if not A: if B and C: <body>`，A 为真时不再直达 body。

`_process_class` 是**同一族的另一子形态**（`tree_...` 由
`probe` 直证，CFG `@556 PJT→696 / @596 PJF→746 / @638 PJF→746 /
@696 body / @746 F`），但位于 for 循环体内，B/C **没有**形成
BoolOpRegion，而是直接并入 `IfRegion.then_blocks`：

```
IfRegion entry=@556 merge=@696 parent=@554 then=[596,638,746] cond_lastj=PJT→696
IfRegion entry=@596 merge=@746 parent=@554 then=[696,700,736] cond_lastj=PJF→746
```

其断裂 AST（`probe` 关闭 fixup 后 dump）为
`If(UnaryOp(not,A), body=[If(and(B,C), X), S1, S2])`，其中 X 以
`Continue` 终结，S1=`cls_fields.append(...)`、S2=`Continue` 是原
`if ...: ... else: ...` 的 else 臂被误塞进 then 臂内层 if 之后。

### ③ 判别器密闭性（真嵌套 vs 断裂 or 链）

| | 真嵌套 `if not A: if B and C` | 断裂 `if A or (B and C)` |
|---|---|---|
| A 的 IF_TRUE 目标 T | = B/C 假边 F（跳过出口） | = body（短路真出口），T is not F |
| C 真 fall-through | body | 恰为 T |
| A 的归属 | 3 成员 and BoolOpRegion 首成员 | **IfRegion.condition_block**（IF_TRUE） |
| R.then_blocks | 不含 B/C 链块 | 覆盖 B/C 链块 |

`n8_true_nested` / `n8_or_and` / `n8_or_and_term` 三个控制案修复后
A/B TEXT-SAME 实证未被误伤（`tree_n8_*.txt` 显示真嵌套被归约为
单条 `if not a and b and c`，正确 or 链归约为单条 `if a or b and c`，
均不产生 `If(UnaryOp(not,.)., body=[If(and,.)])` 嵌套形态）。

## 修复（region_ast_generator 只增不破，`[v112-NOTBOOL]`，单文件）

仅改 `core/cfg/region_ast_generator.py`；`region_analyzer.py` 零改动。
补丁 `fix_patch_v5r112.diff`。新增 2 个方法 + 1 处消费者判据 + 2 处出口
挂载，**不删/不改任何既有逻辑，不认领块、不登记 generated**：

- **值链双重取反归位**（`_generate_boolop_impl` 的 `value_target`
  expression-continuation 拼接处）：判据 = ① `_pre_store` 全部由
  `UNARY_NOT` 组成（k_cont ≥ 1，排除 `not f(a or b)` 等非目标形态）；
  ② `initial_stack` 栈顶顶层连续 `UnaryOp(not)` 层数 k_expr ≥ 1
  （重建器已消费标志）。归约 = 从栈顶剥掉 `min(k_expr,k_cont)` 层 not，
  使 merge 块的 k_cont 个 `UNARY_NOT` 全权决定源码 not 层数
  （k_cont=1 → 单层 not；k_cont=2 → `not not X` 保真）。
  **[C1]** 只读 opcode 族与 AST 节点类型；**[C2]** 未命中逐位回落既有
  拼接；**[C3]** 不认领/不改写区域。
- `_v112_broken_or_true_exit_exprs()`：**纯块图 + IfRegion 判据**（不依赖
  BoolOpRegion 是否存在，统一覆盖上述两种子形态）：
  a. `IfRegion R` 的 `condition_block = A` 以 IF_TRUE 族跳转收尾，目标 T；
  b. A 的非跳转后继 B 以 IF_FALSE 族收尾，假边 F 且 `F is not T`；
  c. B 的非跳转后继 C 亦以 IF_FALSE 族收尾，假边同为 F；
  d. C 的真 fall-through 恰为 T；
  e. `R.then_blocks` 覆盖 B/C；
  f. 存在内层 `IfRegion IR`，`condition_block is C` 且 T 在其 `then_blocks`。
  返回按 B/C 块重建的 and 表达式结构（供密闭比对）。
- `_v112_fixup_if_node(node)`：把
  `If(UnaryOp(not,A), body=[If(and([B,C]), X)])` 重写为
  `If(BoolOp(or,[A, and([B,C])]), body=X)`；外层 body 的尾随语句
  （原 else 臂）归位为 `orelse`，避免其滞留 then 臂内成为 `continue`
  之后的死代码。密闭校验：区域树存在**唯一**命中链、且其重建 and
  表达式与内层 if 的 `test` 结构相等（`_r76_expr_equal` 剥位置元数据），
  否则逐位回落既有 AST。递归覆盖 `body`/`orelse`/`finalbody`。
- 出口挂载（均带 `[v112-NOTBOOL]` 注释，紧随 v111 同款出口之后）：
  - `_if_generate_full_elif_chain`：`result = self._v112_fixup_if_node(result)`
  - `_if_generate_normal`：`if_result = self._v112_fixup_if_node(if_result)`

## 验证（全实测，权威判官 `semantic_diff.compare_case`）

- **REAL46-001 整案**（`semantic_REAL46-001_v112.json`）：
  `status: EQUAL, diffs: 0 []`，完成 **DIFFERENT → EQUAL，两个 R7 全消**
  （v[47] `_get_field`、v[69] `_process_class` 两叶各含的两处缺陷均闭合）。
- **复现矩阵 15 案**（`matrix_v5r112.py` / `matrix_v5r112_result.json`）：
  compile→pyc→pycdc→recompile 逐 code object 比对
  `co_code/co_exceptiontable/co_consts/co_names/co_varnames/
  co_freevars/co_cellvars/co_flags`。**15/15 BYTE-EQUAL**；5 功效案
  （m4_not/m5_hash/m8_getfield/n8_not_or_and/n8_notnot）A/B TEXT-DIFF，
  10 控制案 A/B TEXT-SAME。
- **A/B 回归电池 199 案**（`r112_regress.py` /
  `r112_regress_result.txt` / `.json`）：169 r110 + 15 v111 + 15 v112-NEW；
  中间产物写 `D:/temp/opencode/cl_layout/r112regress/`（不落证据目录）。
  以 `git show 9139e4c3:core/cfg/region_ast_generator.py` 文件交换，
  R110 169 案 TEXT 状态一致 168 / 签名一致 168（唯一差异为
  `pd8_prod` 语料替代案，r98 清理后缺失源、以等价源替代，A/B
  TEXT-SAME 实证产品逐字节未变，如实单列）；10 个用户点名登记差
  全部 **SAME-SIGNATURE**；NO-SRC 0。
- **TEXT-DIFF 6 案**：5 个本轮功效案 + 1 个 v111 语料旧案
  `v111_prefix_stmts`。后者源码为
  `if isinstance(key,set) or (isinstance(key,tuple) and key): raise ...; return`，
  HEAD 产品错渲为 `if not A: if B and C`（对源码签名 **DIFF**），
  v112 归位为 `if A or (B and C): raise ...; else: return`
  （对源码 **BYTE-EQUAL**）——系本轮目标形态在 v111 语料中的同族
  实例被一并修复，非 C3 非目标形态漂移；6 案重编译全 BYTE-EQUAL。
- **权威判官 5 案**（`sd_v112_all.py` / `semantic_v112_all.json`）：
  REAL46-001 / 004 / 036 均 **EQUAL, diffs=[]**；REAL46-019
  （DIFFERENT, 1 diff `v[19].code_sha`）、REAL46-031
  （DIFFERENT, 2 diff `co_code.len` / `co_code.sha256`）与修复前
  基线 `status + diffs 全签名` 逐项一致 = **BASELINE-UNCHANGED**。
- **pytest 7 套件**（`pytest_v5r112.log`）：`3 failed / 277 passed /
  2 xpassed`，3 个 failed 与基线逐名一致（2 冻结对
  `TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、
  `TestBoundaryConditions::test_BOUNDARY_02_large_function` +
  `TestProductFreshness::test_products_match_current_code` 预存在陈旧），
  **零新增失败**。
- **完整性**：`scripts/pyc_verify.py` SHA256 =
  `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4`；
  `tests/`、`tools/completeness/semantic_diff.py` 零改动；`core/` 仅
  `M core/cfg/region_ast_generator.py`（`202 insertions / 0 deletions`
  纯新增，`fix_patch_v5r112.diff` 与实时 `git diff` 完全一致）。
  **未提交 git**（提交由后续代理做）。

## 历史族对照

| 族 | 形态 | 断链位置 |
|---|---|---|
| `[v100-ORTAIL]` | and 链尾嵌套 or | 真边目标 |
| `[v106-ANDORTAIL]` | `A and B and C and (D or E)` | and/or 交界 |
| `[v110-MCSUB]` | for 迭代前缀链式赋值 | for 提取器消费者 |
| `[v111-ORAND]` | or 首 + and 尾 + 终止臂 + 臂后无语句 | 两条等价平凡 return-None 假边目标不同 |
| **`[v112-NOTBOOL]`** | **`not (or+and)` 值链（merge UNARY_NOT 双消费）+ or 首成员未入链（真出口极性反）** | **生成端赋值拼接消费者 / IfRegion 条件误取反** |
