# FINDING — rr-v5r139 [v139-SLBODYEXPR]：while 自循环体边界扩展白名单补纯表达式操作码（C4_body_tuple 循环体 UNPACK 族尾语句截断=真实 R1 修复）

## 0. 结论速览

- 64.5 首选 while 体/其余 walk 同族 UNPACK/B234 缺口系统清点：C4_body_tuple
  精确形（r134 轮登记预存在残差）`while items: a, b = items.pop();
  res.append(a + b)` 复现显示 **UNPACK 本身已正确渲染**（`a, b =
  items.pop()` ✓——自循环 walk 既有 UNPACK 状态机），真正丢失的是
  **后随 `res.append(a + b)` 整条语句**（真实 R1）。
- 走查清点（trace 探针+全方法调用普查 549 帧）：while 体块自跳
  （POP_JUMP_BACKWARD→块首）成自环，由 **`_loop_extract_self_loop_stmts`
  （第六条 walk，第六条自环域走查）** 渲染；回边/语句/融合走查全部零
  命中（`_build_store_statement` 仅模块级 def 一击）。
- 根因 = 自循环体边界启发式 `_body_end_idx` 的扩展白名单缺纯表达式
  操作码：`_last_store_idx`（STORE b）之后的 append 实参求值
  [LOAD res, LOAD_METHOD append, LOAD a, LOAD b, **BINARY_OP**, PRECALL,
  CALL, POP_TOP] 在 **BINARY_OP** 处 break → `_body_end_idx` 停在
  STORE b → 主走查 `_sli_idx > _body_end_idx` 截断，append 整条丢失。
  对照实证：无 STORE 体形（`out.append(items.pop())`，
  `_last_store_idx=-1`）走全长路径幸存；多 POP_TOP 体形走既有的栈模拟
  归约路径幸存——仅「末 STORE+单 POP_TOP+表达式实参」形落缺口。
- [v139-SLBODYEXPR] 单文件 +19/−1（只增不破）：扩展白名单补
  LOAD_CONST/BINARY_OP/BINARY_SUBSCR/COMPARE_OP/CONTAINS_OP/IS_OP/
  UNARY_*/BUILD_SLICE/BUILD_STRING/BUILD_SET/LIST_EXTEND/SET_UPDATE/
  DICT_UPDATE/DICT_MERGE——扩展跨过实参求值到 POP_TOP，`_body_end_idx`
  前进，语句经缓冲由循环尾 `_build_statement` flush 发射（与无 STORE
  形同一通道，f3 对照实证该通道健壮）；COPY/SWAP（walrus/换栈签名）
  与循环机制操作码不纳入；重检求值段（无 POP_TOP 可推进）边界不变；
  多 POP_TOP 体仍走栈模拟路径。
- 真函数复判：repro1/2/3 全量 **byte_equal=True**；r136/r137/r138 功效
  域回归防护 byte_equal 维持；get_matching_blocks 852=852 维持；difflib
  判官 55/62 维持。

## 1. 根因（三层追踪）

- 复现（repro1= r134 矩阵 C4_body_tuple 精确形）：`def m(items):
  res = []; while items: a, b = items.pop(); res.append(a + b); return
  res` → 渲染丢 `res.append(a + b)`。
- 走查清点：trace9（块级）零命中后，trace10 全方法调用普查（549 帧
  66 名）锁定 `_loop_extract_self_loop_stmts` 1 次调用=体渲染者；其
  UNPACK 状态机完成 `a, b = items.pop()` 后，`_body_end_idx` 截断。
- 边界启发式：`_last_store_idx` 向后扩展遇白名单外指令 break——
  白名单（PUSH_NULL/LOAD_*/PRECALL/CALL/LOAD_METHOD/LOAD_ATTR/
  BUILD_TUPLE/BUILD_LIST/BUILD_MAP/FORMAT_VALUE）缺 BINARY_OP/
  LOAD_CONST 等；本块扩展在 BINARY_OP 处 break → 体边界=STORE b。

## 2. 修复（[v139-SLBODYEXPR]，只增不破，单文件 +19/−1）

`_loop_extract_self_loop_stmts` 体边界扩展白名单（14851 区）补 14 个
纯表达式操作码（补丁 fix_patch_v5r139.diff）：
- LOAD_CONST/BINARY_OP/BINARY_SUBSCR/COMPARE_OP/CONTAINS_OP/IS_OP/
  UNARY_NEGATIVE/UNARY_NOT/UNARY_INVERT/BUILD_SLICE/BUILD_STRING/
  BUILD_SET/LIST_EXTEND/SET_UPDATE/DICT_UPDATE/DICT_MERGE；
- 效果：扩展跨过末语句实参求值到 POP_TOP（`_body_end_idx` 前进），
  走查处理该语句入缓冲，循环尾 `_build_statement` flush 发射 Expr；
- 不变式：POP_TOP 才推进边界（重检求值段无 POP_TOP→边界不动）；
  多 POP_TOP 体仍走既有 `_poptop_count_after > 1` 栈模拟归约；
  walrus（COPY）与换栈（SWAP）签名不纳入白名单（各走专用路径）。

## 3. 验证（全实测）

- **矩阵 9 案**（matrix_v5r139.py，A/B 单文件 RAG 交换 HEAD 39a4d2ff
  vs v139）：E1 while 体 unpack+append(a+b)（C4 精确形）/E2 常量实参
  （LOAD_CONST）/E3 下标实参（BINARY_SUBSCR）3 功效案 HEAD
  TEXT-DIFF→v139 **BYTE-EQUAL PASS**；C1 无 STORE 体（全长路径）/
  C2 单 STORE 体/C3 双调用体（多 POP_TOP 栈模拟路径）/C4 算术条件
  重检（重检段边界不变）/C5 r138 E1 形（融合落空域）/C6 r136 E1 形
  （回边域）6 控制零漂移 PASS。**MATRIX: ALL PASS**（3 功效+6 控制）。
- **真函数复判**（verify4）：repro1/2/3 重编译 **byte_equal=True**；
  r136/r137/r138 回归防护（E1 形）byte_equal 维持；**get_matching_blocks
  852=852 维持**；difflib 判官 **55/62（88.71%）维持**（无回退）。
- **A/B 电池 267 案**（r139_regress.py，单文件 RAG 交换 HEAD
  39a4d2ff vs v139）：**TEXT-DIFF 0/267**（全语料零漂移）；R110
  168/169（mc1 正常归一）；登记差 10 案 ALL SAME-SIGNATURE（含
  SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项
  一致，余 2 失败=冻结对 B01/BOUNDARY_02）。
- **REAL46 全量 sweep 豁免（小修口径）**：difflib 新鲜判官读数直接
  覆盖触达面+电池 267 零漂移兜底。

## 4. 验收口径

实测读数同 §3：C4_body_tuple 族尾语句截断（真实 R1）修复、3 功效案
重编译 BYTE-EQUAL、自循环无 STORE/多 POP_TOP/重检段边界零漂移、
r136/r137/r138 功效域零回退；电池 267 案 TEXT-DIFF 0；pytest 冻结对
基线一致；difflib 55/62 维持。不宣称 G1/G2c/G3/G4/G6 通过；
product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **while 体/自环域其余白名单清点**（同族启发式其余缺口：如
   BUILD_MAP 扩展段后的 dict 方法调用形、BUILD_STRING f-string 实参
   形——矩阵未覆盖形按需补；首选下一轮清点）；链式融合域 walrus 形
   （COPY 域）；difflib 余 7 差单元（find_longest_match/
   get_grouped_opcodes/get_close_matches/_fancy_replace/_mdiff×2/
   _line_wrapper——控制流族）；REAL46-014 tarfile（142/160）/016
   urllib.request（185/194）；REAL46-013 cookiejar 91/105、015
   subprocess 68/78 余差；4 compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r139.diff`（+19/−1 单文件）、`matrix_v5r139.py`+result、
`r139_regress.py`+result、`difflib_judge_v139.txt`、本文件；中间件
D:/temp/opencode/cl_layout/r139diag、r139matrix、r139regress 不入库。
