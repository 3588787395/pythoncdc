# FINDING — rr-v5r136 [v136-LOOPB234B]：for 回边走查 B234 反源序多目标赋值整组归约（get_matching_blocks for 体残差闭合=真实 R1 修复，difflib 54→55/62）

## 0. 结论速览

- 61.5 首选 get_matching_blocks for 体残差（登记 prod 844 vs 852）逐字节
  定位：塌缩循环 else 臂尾 `i1, j1, k1 = i2, j2, k2`（B234 反源序形：
  LOAD i2, LOAD j2, LOAD k2, STORE k1, STORE j1, STORE i1）渲染为
  `k1 = k2`——**i1/j1 赋值整条丢失**，塌缩算法结果错误（**真实 R1**；
  61.5 登记的「跳转目标差 6 字节」实为 8 字节=else 臂缺 LOAD i2/j2+
  STORE i1/j2 共 4 指令，FOR_ITER 目标差随之 8 字节，本轮实测修正）。
- 位点 = `_generate_stmts_from_instrs`（回边走查，73320 区 STORE 分支，
  调用链 `_loop_generate_for→_loop_generate_body→_loop_dispatch_block→
  _loop_handle_back_edge→_loop_process_back_edge_with_condition:17731`）：
  首 STORE 触发 `_build_store_statement` 重建单目标（reconstruct 仅返回
  栈顶）、次级 STORE 缓冲已空分支不触发（`and _buf`）落入底部
  `_buf.append` 污染缓冲、末级 STORE 携污染缓冲触发退化调用返回 None
  （探针实证两次 BSS 调用：[LOAD i2,LOAD j2,LOAD k2,STORE k1] 与
  [STORE j1,STORE i1]）。B234 归约此前已存在主 walk/42743/for 前缀
  11672/while 前缀（v134），本回边走查为第四条缺口 walk。
- [v136-LOOPB234B] 单文件 +60/−0（只增不破）：回边走查 STORE 分支镜像
  v134 整组归约——连续简单名 STORE 段 N>=2（instrs 前瞻）+值段去噪无
  COPY/SWAP/UNPACK_*+重建栈深 >=N → `Assign(Tuple(源序目标=反源序
  STORE), Tuple(压栈序值=栈尾 N 项))`、整段消费（_gi 推进过 STORE 段，
  后随 STORE 不再落缓冲污染）；未命中逐位落回（C3）。
- 真函数复判：**get_matching_blocks co_code 852=852 字节全等（单元闭
  合）**；difflib 判官 **54/62→55/62（87.10%→88.71%）**。

## 1. 根因（三层追踪）

- 复现（repro1）：`for i2, j2, k2 in blocks: if ...: k1 += k2; else:
  if k1: out.append(...); i1, j1, k1 = i2, j2, k2` → HEAD 产物 else 臂尾
  渲染 `k1 = k2`（i1/j1 丢失）。
- 探针实证（trace2 全量 BSS 打点）：仅两次命中——
  `_build_store_statement([LOAD i2,LOAD j2,LOAD k2,STORE k1])`（渲染
  `k1 = k2`）与 `_build_store_statement([STORE j1,STORE i1])`（污染缓
  冲退化调用，返回 None）——均自 `_generate_stmts_from_instrs:73320`。
- 字节码形态：`i1, j1, k1 = i2, j2, k2`（FAST 目标）=[LOAD i2, LOAD j2,
  LOAD k2, STORE k1, STORE j1, STORE i1]（值压栈源序、STORE 反源序、
  无 SWAP）；产品 844=852−8（4 条指令整缺）。

## 2. 修复（[v136-LOOPB234B]，只增不破，单文件 +60/−0）

`_generate_stmts_from_instrs` STORE 分支（73319 前）新增整组归约（
v134-LOOPB234 同源镜像）：
- 识别：当前 STORE 起连续简单名 STORE 段 N>=2（`instrs`/`_gi`/`_gn`
  前瞻）+ 值段（`_buf` 去 RESUME/NOP/CACHE/PUSH_NULL）无
  COPY/SWAP/UNPACK_SEQUENCE/UNPACK_EX + 重建栈深（expr_reconstructor
  reset+逐指令回放取 stack，滤 PUSH_NULL）>= N；
- 归约：`Assign(targets=[Tuple(反源序 STORE 目标)], value=Tuple(栈尾
  N 项 压栈序))`；`_buf` 清空、`_gi` 推进过整段（后随 STORE 不再落入
  缓冲污染——同时消除预存污染路径）；
- 未命中（N<2/纯度拒/栈深不足）逐位落回既有单 STORE 路径（C3）。

## 3. 验证（全实测）

- **矩阵 7 案**（matrix_v5r136.py，A/B 单文件 RAG 交换 HEAD 76af0778
  vs v136）：E1 else 臂三目标（get_matching_blocks 精确形，continue
  渲染域）HEAD TEXT-DIFF→v136 **BYTE-EQUAL PASS**；C1 回边单赋值/
  C4 兄弟独立赋值（LOAD 交错 STORE 不连续）零漂移 PASS；E2 两目标/
  E3 属性值形实测 head 与 v136 输出逐字节同（本轮零触碰——其丢目标
  经 `_loop_extract_self_loop_stmts` 融合落空路径渲染，探针实证该域
  零 BSS 调用，非回边走查，登记下轮）；C2 链式回边 walrus 形/C3 循环
  体 UNPACK 元组族（C4_body_tuple 同族）预存在不等。**MATRIX: ALL
  PASS**（1 功效+2 控制过判+4 预存在排除判定）。
- **真函数复判**：repro1 重编译 **byte_equal=True**；
  **get_matching_blocks 852=852 co_code 全等**；difflib 全单元差
  7/60（判官口径 55/62）。
- **A/B 电池 267 案**（r136_regress.py，单文件 RAG 交换 HEAD
  76af0778 vs v136）：**TEXT-DIFF 0/267**（全语料零漂移——整组归约
  仅在连续 STORE 段 N>=2+值段纯净+栈深足的结构事实下触发，267 语料
  零触发=外科性）；R110 168/169（mc1 正常归一）；登记差 10 案 ALL
  SAME-SIGNATURE（含 SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项
  一致，余 2 失败=冻结对 B01/BOUNDARY_02）。
- **REAL46 判官**：difflib **54/62→55/62（87.10%→88.71%）**，
  get_matching_blocks 全闭合；REAL46 全量 sweep 豁免（小修口径）——
  触达面由 difflib 新鲜判官读数直接覆盖+电池 267 零漂移兜底。

## 4. 验收口径

实测读数同 §3：get_matching_blocks for 体残差（真实 R1 丢 i1/j1）闭
合、repro1/矩阵 E1 重编译 BYTE-EQUAL；电池 267 案 TEXT-DIFF 0；pytest
冻结对基线一致；difflib 55/62。不宣称 G1/G2c/G3/G4/G6 通过；
product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **self-loop 融合路径 fall-through 多目标赋值丢次级目标**（E2/E3 形
   实测：`x, y = b, a`/`i1, j1 = self.p, self.q` 渲染单目标——位点
   `_loop_extract_self_loop_stmts`（14546）融合落空块走查，探针实证
   零 BSS 调用；真实 R1 级，首选下一轮）；循环体 UNPACK 元组族
   （C4_body_tuple/C3_unpack 同族，预存在登记）；difflib 余 7 差单元
   （find_longest_match/get_grouped_opcodes/get_close_matches/
   _fancy_replace/_mdiff×2/_line_wrapper——控制流族）；
   REAL46-014 tarfile（142/160）/016 urllib.request（185/194）；
   REAL46-013 cookiejar 91/105、015 subprocess 68/78 余差；4
   compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r136.diff`（+60 单文件）、`matrix_v5r136.py`+result、
`r136_regress.py`+result、`difflib_judge_v136.txt`、本文件；中间件
D:/temp/opencode/cl_layout/r136diag、r136matrix、r136regress 不入库。
