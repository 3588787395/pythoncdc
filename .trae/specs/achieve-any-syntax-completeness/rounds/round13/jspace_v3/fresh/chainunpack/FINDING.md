# FINDING — rr-v5r135 [v135-CHAINUNPACK]：条件块前导段提取器链式元组解包链尾目标归还（get_matching_blocks 链尾 x 丢失=真实 R1 修复）

## 0. 结论速览

- Task 60 修复 get_matching_blocks 赋值段（v134）后真函数复判：首差推进到
  byte 130 后仍差——循环节 `i, j, k = x = items.pop()`（链式元组解包）渲染
  为 `(i, j, k) = items.pop()`——**链尾目标 x 赋值整条丢失**，后随
  `out.append(x)` 引用 x → 全局查找 NameError（**真实 R1**）。
- 字节码形态：链式解包 = [值求值, COPY 1, UNPACK_SEQUENCE 3, STORE i,
  STORE j, STORE k, **STORE x**]——值栈顶留一份给链尾 STORE x（B85 链式
  赋值与 B234 解包的复合形）。UNPACK 状态机把 COPY 1 当值段噪声、UNPACK
  完成点只发单目标 Assign，链尾 STORE x 落入无主缓冲 → 静默丢失。
- [v135-CHAINUNPACK] 单文件 +51/−3（只增不破）：UNPACK 两个分支记录
  `tail_copy`（值段尾 COPY 1）；解包完成点（简单名目标）前瞻跳过
  RESUME/NOP/CACHE/PUSH_NULL 后遇 STORE_* → 链尾目标并入 targets +
  `is_chain_assign=True`（B85 链式渲染通道 `i, j, k = x = ...`）+ 跳过
  span 覆盖链尾 STORE；未命中逐位落回（C3）。
- 真函数复判：repro2（while 体链式解包精确形）**g byte_equal=True**；
  difflib 判官 54/62 维持，**首差 byte 130→524**（赋值段+链尾全闭合，
  余差=for 体残差 prod 844 vs 852——FOR_ITER 目标差 6 字节，循环体他族，
  登记下轮）。矩阵 E2（if 体形）实测 HEAD 本已等价——归控制（if 体走
  其他路径），功效案仅 E1（while 体形，get_matching_blocks 精确域）。

## 1. 根因（三层追踪）

- 复现（repro2）：`def g(items, out): while items: i, j, k = x =
  items.pop(); if k: out.append(x); return out` → HEAD 产物
  `(i, j, k) = items.pop()`（x 丢失）→ `append(x)` 为 LOAD_GLOBAL。
- traceback/走查实证：位点 = `_if_extract_cond_instructions`（条件块
  前导段提取器）的 UNPACK 状态机——`pre_unpack_info['value']` 完成点
  （22525 区）只把解包目标组包成单 Assign；链尾 STORE x 在
  `_instr_idx+1` 处，不属于解包目标组，也无人消费 → 静默丢失。
- 字节码形态：`i, j, k = x = items.pop()` = [CALL, COPY 1, UNPACK 3,
  STORE i, STORE j, STORE k, STORE x]——COPY 1 复制栈顶给链尾；
  既有 B85 链式赋值（COPY 1+多 STORE）与 B234 解包归约各自独立存在，
  复合形在第三条 walk（前导段提取器）无覆盖。

## 2. 修复（[v135-CHAINUNPACK]，只增不破，单文件 +51/−3）

`_if_extract_cond_instructions` 两处（补丁 fix_patch_v5r135.diff）：
- UNPACK_SEQUENCE/UNPACK_EX 两分支记录 `pre_unpack_info['tail_copy']`
  （值段非空且尾指令为 COPY arg==1）；
- 解包完成点（简单名目标）：tail_copy 时前瞻 `_instr_idx+1` 跳过
  RESUME/NOP/CACHE/PUSH_NULL 噪声后遇 STORE_FAST/NAME/GLOBAL/DEREF →
  链尾目标追加进 targets、Assign 打 `is_chain_assign=True`
  （code_generator._generate_assign 2910 既有链式渲染通道 →
  `i, j, k = x = ...`）、`_c2_skip_until` 覆盖至链尾 STORE（防重复
  发射）；非 tail_copy 形逐位落回既有单 Assign（C3）。
- 首跑教训：只并目标不打 is_chain_assign → 渲染 `(i, j, k) = x = ...`
  变 tuple-join 形（UNPACK 2+嵌套）重编译不等 → 补 flag 走链式渲染。

## 3. 验证（全实测）

- **矩阵 5 案**（matrix_v5r135.py，A/B 单文件 RAG 交换 HEAD 400540a8
  vs v135）：E1 while 体链式元组解包（get_matching_blocks 精确形）
  HEAD TEXT-DIFF→v135 **BYTE-EQUAL PASS**；E2 if 体形实测 HEAD 本已
  等价（if 体走其他路径）→ 归控制（text_same=True+byte_equal=True）；
  C1 普通解包/C2 简单链（B85 域）/C3 函数顶链式解包（非条件块前导段）
  零漂移。**MATRIX: ALL PASS**。
- **真函数复判**：repro2 重编译 **g byte_equal=True**（首跑后修 flag
  实证）；difflib 判官 54/62 维持、首差 byte 130→524（赋值段与链尾
  全闭合；余差=for 体残差 prod 844 vs 852，§5 登记）。
- **A/B 电池 267 案**（r135_regress.py，单文件 RAG 交换 HEAD
  400540a8 vs v135）：TEXT-DIFF 0/267（全语料零漂移——链尾归还原在
  tail_copy+链尾 STORE 结构事实下触发，267 语料零触发=外科性）；
  登记差 10 案 ALL SAME-SIGNATURE；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项
  一致，余 2 失败=冻结对 B01/BOUNDARY_02）。
- **REAL46 全量 sweep 豁免（小修口径）**：difflib 新鲜判官读数直接
  覆盖触达面；回归面由电池 267 案零漂移+矩阵 3 控制案兜底。

## 4. 验收口径

实测读数同 §3：get_matching_blocks 链尾目标（真实 R1 丢失 x）修复、
repro2/矩阵 E1 重编译 BYTE-EQUAL；电池 267 案 TEXT-DIFF 0；pytest
冻结对基线一致；difflib 单元读数维持 54/62（首差 130→524，余差=for
体残差他族）。不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **get_matching_blocks for 体残差**（prod 844 vs 852，FOR_ITER 目标
   差 6 字节；C4_body_tuple 循环体 UNPACK 元组族预存在不等同域）；
   difflib 其余 7 差单元（find_longest_match/get_grouped_opcodes/
   get_close_matches/_fancy_replace/_mdiff×2/_line_wrapper——控制流
   族）；REAL46-014 tarfile（142/160）/016 urllib.request（185/194）；
   REAL46-013 cookiejar 91/105、015 subprocess 68/78 余差；4
   compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r135.diff`（+51/−3 单文件）、`matrix_v5r135.py`+result、
`r135_regress.py`+result、本文件；中间件
D:/temp/opencode/cl_layout/r135diag、r135matrix、r135regress 不入库。
