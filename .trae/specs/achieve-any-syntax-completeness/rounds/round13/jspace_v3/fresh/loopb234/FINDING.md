# FINDING — rr-v5r134 [v134-LOOPB234]：while 前缀提取器 B234 反源序多目标赋值整组归约（get_matching_blocks 首目标丢失=真实 R1 修复）

## 0. 结论速览

- difflib 余 8 差单元首选 **get_matching_blocks**：`la, lb = len(self.a),
  len(self.b)`（while 前缀 B234 反源序形）渲染为 `lb = len(...)`——**la 赋
  值整条丢失**，后随 `queue = [(la, ...)]` 与 `la + lb` 引用 la → 全局
  查找 NameError（**真实 R1**）。位点 = `_loop_generate_while` 的 while
  前缀语句提取器（_eps walk，9529 区）——B234/SIG2 归约只存在于主 walk
  与 `_build_statements_from_instructions`，本前缀提取器缺对应分支。
- [v134-LOOPB234] 单文件 +68/−0（只增不破）：前缀 STORE 分支新增整组归
  约——连续简单名 STORE 段 N>=2（块内前瞻）+ 累积值段去噪无
  COPY/SWAP/UNPACK_* + 重建栈深 >= N + 段内无 skip_store_targets 成员 →
  `Assign(Tuple(反源序目标), Tuple(压栈序值))`。
- 真函数复判：元组赋值段修复（首差从 byte 68 推进到 byte 130，赋值段
  逐字节同）；get_matching_blocks 单元仍差 2 字节=**循环体深处他族残
  差**（while 体跳转目标差 6 字节——循环体 UNPACK 族，登记下轮）。
  E2 方法形/E3 三目标形矩阵全 BYTE-EQUAL。

## 1. 根因（三层追踪）

- 复现（repro1）：`def g(a, b): la, lb = len(a), len(b); queue = [...];
  while queue: ...` → HEAD 产物 `lb = len(b)`（la 丢失）。
- traceback 实证：lb 的 store 自
  `generate→_generate_loop→_loop_generate_while:9539
  _build_store_statement(_eps_instrs)`——前缀提取器逐 STORE 调
  `_build_store_statement`：首 STORE 把整段值指令当单一 RHS（reconstruct
  仅返回栈顶=len(b)）、次级 STORE（la）缓冲已空返回 None → 静默丢失。
- 字节码形态：`la, lb = len(a), len(b)` = [len(a) eval, len(b) eval,
  STORE lb, STORE la]（FAST/NAME 目标反源序、无 SWAP——B234 同一编译
  事实）；B234/SIG2 归约已存在于主 walk（71392）与
  `_build_statements_from_instructions`（42743），本前缀提取器为第三条
  缺口 walk。

## 2. 修复（[v134-LOOPB234]，只增不破，单文件 +68/−0）

`_loop_generate_while` 前缀 STORE 分支（9538 前）新增整组归约：
- 识别：当前 STORE 起连续简单名 STORE 段 N>=2（`cond_block.instructions
  .index` 前瞻）+ 累积值段去噪无 COPY/SWAP/UNPACK_SEQUENCE/UNPACK_EX +
  重建栈深 >= N + 段内无 skip_store_targets 成员（外层赋值目标不吞）；
- 归约：`Assign(Tuple(反源序目标), Tuple(压栈序值))`（首 STORE 弹
  TOS=最后一个源序目标）、值段消费、缓冲清空；后随 STORE 空缓冲自然落
  None 不重复发射；
- 未命中逐位落回既有单 STORE 路径（C3）。

## 3. 验证（全实测）

- **矩阵 6 案**（matrix_v5r134.py，A/B 单文件 RAG 交换 HEAD f190d0ef
  vs v134）：E1 while 前缀元组赋值（get_matching_blocks 精确形）/E2
  方法调用值形/**C3 三目标形**（实测同为功效）——3 功效案 HEAD
  TEXT-DIFF→v134 **BYTE-EQUAL PASS**（repro 重编译 byte_equal 实证）；
  C1 前缀单赋值/C2 非循环元组（B234 主 walk 域）零漂移；C4 循环体
  UNPACK 元组**预存在残差**（text_same=True⇒HEAD 同产品同不等——循环
  体 UNPACK 族本轮未触碰，登记下轮，排除判定）。**MATRIX: ALL PASS**。
- **真函数复判**：get_matching_blocks 赋值段修复（首差 byte 68→130），
  单元仍差 2 字节=循环体他族（见 §5）。
- **A/B 电池 267 案**（r134_regress.py，单文件 RAG 交换 HEAD f190d0ef
  vs v134）：**TEXT-DIFF 0/267**（全语料零漂移——整组归约仅在连续 STORE
  段 N>=2+值段纯净+栈深足+无 skip 目标的结构事实下触发，267 语料零触
  发=外科性）；R110 168/169 一致（mc1 正常归一）；登记差 10 案 **ALL
  SAME-SIGNATURE**（含 SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项一致，
  余 2 失败=冻结对 B01/BOUNDARY_02）。
- **REAL46 全量 sweep 豁免（小修口径）**：difflib 新鲜判官读数直接覆盖
  触达面；回归面由电池 267 案零漂移+矩阵 3 控制案兜底。

## 4. 验收口径

实测读数同 §3：get_matching_blocks 赋值段（真实 R1 丢失目标）修复、
repro/矩阵 3 功效案重编译 BYTE-EQUAL；电池 267 案 TEXT-DIFF 0；pytest
冻结对基线一致；difflib 单元读数维持 54/62（余差=循环体他族）。不宣
称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **get_matching_blocks 循环体残差**（跳转目标差 6 字节；C4_body_tuple
   循环体 UNPACK 元组族预存在不等同域）；difflib 其余 7 差单元；
   REAL46-014 tarfile（142/160）/016 urllib.request（185/194）；
   REAL46-013 cookiejar 91/105、015 subprocess 68/78 余差；4
   compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r134.diff`（+68 单文件）、`matrix_v5r134.py`+result、
`r134_regress.py`+result、本文件；中间件
D:/temp/opencode/cl_layout/r134diag、r134matrix、r134regress 不入库。
