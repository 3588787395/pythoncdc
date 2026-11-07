# FINDING — rr-v5r138 [v138-FTUNPACK]：融合落空块走查 UNPACK 多目标解包赋值整组归约（C4_ft_unpack 形丢目标=真实 R1 修复）

## 0. 结论速览

- 63.5 首选 `_build_effective_stmts` UNPACK 分支缺失（C4_ft_unpack 形）
  实证：`x, y = p`（LOAD p, UNPACK_SEQUENCE 2, STORE x, STORE y）渲染
  为 `x = p`——**y 目标整条丢失**=**真实 R1**。位点 = 第五 walk
  `_build_effective_stmts`（v137 已修同函数 B234 归约）无 UNPACK 分支：
  UNPACK 落入 expr_instrs 缓冲，首个 STORE_* 触发 `_build_statement`
  重建单目标（v137 纯度判据正确拒绝含 UNPACK 的 B234 归约）、次级
  STORE 缓冲已空落尾部 `expr_instrs.append` 污染——目标丢失。
- [v138-FTUNPACK] 单文件 +63/−0（只增不破）：STORE 分支前新增
  UNPACK_EX/UNPACK_SEQUENCE 整组归约（镜像回边走查既有分支）——
  值缓冲非空+**本块非 for_iter_fall_through**（for 目标解包属循环机制，
  由既有 for_target 吸收路径处理，绝不可吞）→ 前向收集后继连续
  STORE_*（SEQUENCE 取 arg 个；EX 按 before/Starred/after），值=
  reconstruct(值缓冲)，发射 `Assign(targets=[Tuple(elts)], value)`、
  整段消费（`_bes_skip_offsets` 跳过后随 STORE）；收集不全逐位落回
  （C3）。
- 真函数复判：C4_ft_unpack 全量 **byte_equal=True**；r136/r137 功效域
  回归防护（repro1/r136 E1/r137 E1-E3）byte_equal 维持；
  get_matching_blocks 852=852 维持；difflib 判官 55/62 维持。

## 1. 根因（三层追踪）

- 复现（r137 矩阵 C4 遗留）：`for p in pairs: if x: x -= 1; else:
  x, y = p` → 渲染 `x = p`（y 丢失）。
- 字节码形态：else 臂尾块 = [LOAD p, UNPACK_SEQUENCE 2, STORE x,
  STORE y, JUMP_BACKWARD]。
- 走查机制：融合落空块委托 `_build_effective_stmts`（trace 实证 v137
  轮）；该 walk 分支覆盖 POP_TOP/STORE_SUBSCR/STORE_*/DELETE_*——
  唯无 UNPACK_*：UNPACK 落 expr_instrs；STORE x → v137 B234 归约纯度
  判据（UNPACK 在值段→拒绝，判据工作正常）→ `_build_statement`
  重建单目标 `x = p`；STORE y → 缓冲空落尾部污染丢失。

## 2. 修复（[v138-FTUNPACK]，只增不破，单文件 +63/−0）

`_build_effective_stmts` STORE 分支前新增 UNPACK 分支（补丁
fix_patch_v5r138.diff）：
- 触发：`instr.opname in ('UNPACK_EX', 'UNPACK_SEQUENCE') and
  expr_instrs and not _is_for_target_store_block`（for 目标解包绝不吞）；
- 收集：`effective.index` 前瞻连续 STORE_*（v134/v137 同款）；期望数
  SEQUENCE=arg、EX=before+1+after（Starred 居 before 位）；
- 归约：收集完整（`len(_fu_stores)==_fu_expected`）且值非 None →
  `Assign(targets=[Tuple(Name*/Starred*)], value=reconstruct(expr_instrs))`、
  `expr_instrs` 清空、`_bes_skip_offsets` 登记消费段；
- 收集不全/值 None 逐位落回既有路径（C3）。

## 3. 验证（全实测）

- **矩阵 8 案**（matrix_v5r138.py，A/B 单文件 RAG 交换 HEAD 4865223a
  vs v138）：E1 固定解包（C4 形）/E2 星号解包（UNPACK_EX
  before/after 形）/E3 调用值解包 3 功效案 HEAD TEXT-DIFF→v138
  **BYTE-EQUAL PASS**；**C1 for 目标解包（for_iter_fall_through 循环
  机制域——守卫判据直接验证，绝不可吞）零漂移 PASS**；C2 融合落空
  单赋值/C3 r137 E1 形（HEAD 已含 v137）/C4 r136 E1 形（回边域）零
  漂移 PASS；C5 链式融合域 walrus 形（COPY 域，r136/r137 矩阵同形）
  实测 head 与 v138 输出逐字节同=预存在排除判定。**MATRIX: ALL
  PASS**（3 功效+4 控制+1 预存在）。
- **真函数复判**（verify3）：C4_ft_unpack 重编译 **byte_equal=True**；
  r136 回归防护 repro1/r136 E1 + r137 回归防护 E1/E2/E3 byte_equal
  维持；**get_matching_blocks 852=852 维持**；difflib 判官 **55/62
  （88.71%）维持**（无回退）。
- **A/B 电池 267 案**（r138_regress.py，单文件 RAG 交换 HEAD
  4865223a vs v138）：**TEXT-DIFF 0/267**（全语料零漂移）；R110
  168/169（mc1 正常归一）；登记差 10 案 ALL SAME-SIGNATURE（含
  SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项
  一致，余 2 失败=冻结对 B01/BOUNDARY_02）。
- **REAL46 全量 sweep 豁免（小修口径）**：difflib 新鲜判官读数直接
  覆盖触达面+电池 267 零漂移兜底。

## 4. 验收口径

实测读数同 §3：C4_ft_unpack 形丢目标（真实 R1）修复、3 功效案重编译
BYTE-EQUAL、for 目标机制零触碰、r136/r137 功效域零回退；电池 267 案
TEXT-DIFF 0；pytest 冻结对基线一致；difflib 55/62 维持。不宣称
G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **while 体/其余 walk 的同族 UNPACK/B234 缺口清点**（五条 walk 修复
   后系统清点剩余走查是否还有缺口——循环体 UNPACK 元组族
   C4_body_tuple 若走独立 walk 则同法补齐，首选下一轮）；链式融合域
   walrus 形（COPY 域）；difflib 余 7 差单元（find_longest_match/
   get_grouped_opcodes/get_close_matches/_fancy_replace/_mdiff×2/
   _line_wrapper——控制流族）；REAL46-014 tarfile（142/160）/016
   urllib.request（185/194）；REAL46-013 cookiejar 91/105、015
   subprocess 68/78 余差；4 compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r138.diff`（+63 单文件）、`matrix_v5r138.py`+result、
`r138_regress.py`+result、`difflib_judge_v138.txt`、本文件；中间件
D:/temp/opencode/cl_layout/r136diag、r138matrix、r138regress 不入库。
