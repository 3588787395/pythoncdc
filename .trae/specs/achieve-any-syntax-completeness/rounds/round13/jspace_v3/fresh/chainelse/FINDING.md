# FINDING — rr-v5r132 [v132-CHAINESELSE]：elif 链末臂 else 归还（REAL46-011 statistics 全闭合 77/77 = 100%）

## 0. 结论速览

- REAL46-011 最后一差单元 **harmonic_mean**（Different control flow）本轮
  修复：**statistics 判官 76/77 → 77/77 = 100.00%（REAL46-011 全闭合）**。
- 缺陷：`if A: <终态> elif B: <终态> if C: <体> else: <守卫 if>×2+尾>`
  的末 if（非终态臂）被分析端把其 else 侧首块 M 误判为链 merge——
  final_else 收集为空，生成器渲染成 `elif C: <体>` + else 内容压平为链
  后平铺兄弟语句。语义缺陷（**真实 R1**）：C-taken 路径落入压平代码
  （harmonic_mean 的 None 路径落入 `len(None)` TypeError；repro 语义破
  实证）；臂体出口 JUMP 丢失=控制流/字节差 R2。
- [v132-CHAINESELSE] 单文件 +54/−0（只增不破）：`_if_generate_elif_chain`
  渲染前归还——elif_final_else 空 + merge_block M 前驱恰为末臂条件块
  （单前驱=非汇合点）+ 末臂体末块 JUMP_FORWARD/JUMP_ABSOLUTE 目标 T≠M
  且 T 不在链块集 → elif_final_else = [M, T) 偏移序块、merge_block = T
  （真汇合），else 臂交既有 final_else 渲染通道（_process_if_blocks
  按分支派发，区间内独立 IfRegion 整树生成）。

## 1. 根因（三层追踪）

- 复现（repro1 = harmonic_mean 守卫段精确形）：源
  `if n<1: raise / elif (n==1 and weights is None): return / if weights
  is None: w=1;s=n else: if weights: …; if len!=n: raise; s=2`；HEAD
  产物 = `elif weights is None: w=1;s=n` + else 内容平铺（None 路径落
  入 `if len(weights) != n` → len(None) TypeError）。
- 区域树实证：IfRegion@0 = IF_ELIF_CHAIN，elif_conditions=[44,80]、
  elif_bodies=[[60],[84]]、**elif_final_else=[]**、merge_block=**94**；
  前驱图：94 的唯一前驱=80（末臂条件块）——单前驱块非汇合点；真汇合
  T=200（84 的 JUMP_FORWARD 目标，preds=[84,196]）。分析端把 94 当链
  merge → 末臂 else 收集 `_collect_branch_blocks(94, 94)`=空 →
  final_else=[] → 渲染压平。
- 语义/字节双缺陷：压平后 elif-taken 路径继续落入平铺守卫（R1）；
  84 的 JUMP_FORWARD→200 在平铺形中变 fall-through（R2 控制流差）。

## 2. 修复（[v132-CHAINESELSE]，只增不破，单文件 +54/−0）

`_if_generate_elif_chain` final_else 渲染前新增归还分支（识别条件全
I.4 结构事实）：
1. elif_final_else 空 + merge_block M 非空 + elif_conditions 非空；
2. `set(M.predecessors) == {末臂条件块}`（单前驱 ⇒ M 非多臂汇合点）；
3. 末臂体末块 JUMP_FORWARD/JUMP_ABSOLUTE、目标 T≠M、T 不在链块集、
   T.offset > M.offset；
4. 候选 = [M, T) 偏移序块（不在链块集、未生成）非空且首块=M。

命中 → `elif_final_else = 候选`、`merge_block = T`（使 Round8 扩张的
own-merge 排除不再误删 M）→ 既有 final_else 渲染通道发射 else 臂。
未命中任一守卫逐位落回（C3）。

## 3. 验证（全实测）

- **矩阵 6 案**（matrix_v5r132.py，A/B 单文件 RAG 交换 HEAD 1e24ff69
  vs v132）：E1 harmonic_mean 精确形 HEAD TEXT-DIFF→v132 **BYTE-EQUAL
  PASS**（repro 重编译 byte_equal 实证）；E2 单嵌套 if 形实测 HEAD 本
  已等价（归控制）；C1 终态臂链/C2 无 else 链/C3 真汇合双臂 if-else
  （恢复判据不得命中）/C4 末臂终态+else（既有 final_else 通道）全零
  漂移。**MATRIX: ALL PASS**。
- **REAL46 判官**：statistics **76/77→77/77 = 100.00%**（REAL46-011
  全闭合；REAL46 系 46 案中首个 100% 的 failure→success 翻案）。
- **A/B 电池 267 案**（r132_regress.py，单文件 RAG 交换 HEAD 1e24ff69
  vs v132）：**TEXT-DIFF 0/267**（全语料零漂移——恢复判据仅在
  final_else 空+单前驱 merge+体跳转目标异于 merge 的结构事实下触发，
  267 语料零触发=外科性）；R110 168/169 一致（mc1 正常归一）；登记差
  10 案 **ALL SAME-SIGNATURE**（含 SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项一致，
  余 2 失败=冻结对 B01/BOUNDARY_02）。
- **REAL46 全量 sweep 豁免（小修口径）**：statistics 新鲜判官读数直接
  覆盖触达面（77/77）；回归面由电池 267 案零漂移+矩阵 4 控制案兜底。

## 4. 验收口径

实测读数同 §3：**statistics 77/77 = 100.00%（REAL46-011 全闭合）**；
电池 267 案 TEXT-DIFF 0；pytest 冻结对基线一致。不宣称 G1/G2c/G3/G4/
G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. REAL46-012 difflib（53/62）/014 tarfile（142/160）/016 urllib.request
   （185/194）未触达族；REAL46-013 cookiejar 91/105、015 subprocess
   68/78 余差；4 compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r132.diff`（+54 单文件）、`matrix_v5r132.py`+result、
`repro1_src.py`/`product_HEAD_repro1.py`/`product_v132_repro1.py`（最
小复现双态产物）、`r132_regress.py`+result、本文件；中间件
D:/temp/opencode/cl_layout/r132diag、r132matrix、r132regress 不入库。
