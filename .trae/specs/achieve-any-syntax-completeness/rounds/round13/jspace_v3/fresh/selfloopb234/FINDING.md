# FINDING — rr-v5r137 [v137-SELFLOOPB234]：self-loop 融合落空块走查 B234 反源序多目标赋值整组归约（E2/E3 形丢次级目标=真实 R1 修复）

## 0. 结论速览

- 62.5 首选 self-loop 融合路径 fall-through 多目标赋值丢次级目标（E2/E3
  形）逐层定位：真位点 = **`_build_effective_stmts` STORE 分支（5552 区，
  第五条缺口 walk）**——62.5 登记的 `_loop_extract_self_loop_stmts`（融合
  发射域）只是上层调用方，trace 探针（y-块指令序列打点）实证 else 臂尾
  块 `[LOAD hit, LOAD_METHOD append, LOAD y, PRECALL, CALL, POP_TOP,
  LOAD b, LOAD a, STORE y, STORE x]` 委托本方法渲染。
- 失败模式：`x, y = b, a`（B234 反源序形 LOAD b, LOAD a, STORE y,
  STORE x）→ 首 STORE 走 `_build_statement` 重建单目标（reconstruct 仅
  返回栈顶 `y = a`）、次级 STORE 缓冲已空分支不触发（`and expr_instrs`）
  落到尾部 `expr_instrs.append` 污染——**x 目标整条丢失**（E3 形
  `i1, j1 = self.p, self.q` → `j1 = self.q`，i1 丢失）=**真实 R1**。
- [v137-SELFLOOPB234] 单文件 +66/−0（只增不破）：STORE 分支镜像
  v134/v136 整组归约——连续简单名 STORE 段 N>=2（effective 前瞻）+
  值段无 COPY/SWAP/UNPACK_*+重建栈深 >=N → `Assign(Tuple(源序目标),
  Tuple(压栈序值))`、整段消费（`_bes_skip_offsets` 登记后随 STORE 跳过，
  同时消除预存污染路径）；未命中逐位落回（C3）。
- 真函数复判：E2/E3 全量 **byte_equal=True**；r136 功效域回归防护
  （repro1/E1）byte_equal 维持；get_matching_blocks 852=852 维持；
  difflib 判官 55/62 维持。

## 1. 根因（三层追踪）

- 复现（E2 精确形，r136 矩阵遗留）：`for a, b in pairs: if a > y:
  y = a; else: hit.append(y); x, y = b, a` → 渲染
  `hit.append(y); y = a; continue`（x 丢失）。
- trace 探针（trace5：y-块指令序列打点）实证：该块仅被
  `_build_effective_stmts` 接收（两次命中，带/不带 JUMP_BACKWARD 两变
  体）；`_build_store_statement` 零调用（=非回边走查域，修正 62.5 的
  位点定性）；`_generate_block_statements` 域调用不含该块。
- 走查机制：self-loop continue 融合路径（`_loop_extract_self_loop_stmts`
  14546 区发射 `If(body=[Continue])` 后）把落空块语句渲染委托
  `_build_effective_stmts`——B234 归约此前已存在主 walk/42743/for 前缀
  11672/while 前缀（v134）/回边走查（v136），本融合落空块走查为第五条
  缺口 walk。

## 2. 修复（[v137-SELFLOOPB234]，只增不破，单文件 +66/−0）

`_build_effective_stmts` 三处（补丁 fix_patch_v5r137.diff）：
- 循环前新增 `_bes_skip_offsets = set()`（整段消费登记）；
- 循环顶新增 `if instr.offset in _bes_skip_offsets: continue` 守卫；
- STORE 分支（STORE_ATTR 判定前）新增整组归约：当前简单名 STORE 起
  连续 STORE 段 N>=2（`effective.index` 前瞻，v134 同款）+值段
  （expr_instrs）无 COPY/SWAP/UNPACK_SEQUENCE/UNPACK_EX+重建栈深
  （expr_reconstructor reset+逐指令回放取 stack 滤 PUSH_NULL）>=N →
  `Assign(targets=[Tuple(reversed stores)], value=Tuple(栈尾 N 项))`、
  `expr_instrs` 清空、后随 STORE 经 skip 集跳过；未命中逐位落回既有
  单 STORE 路径（C3）。

## 3. 验证（全实测）

- **矩阵 7 案**（matrix_v5r137.py，A/B 单文件 RAG 交换 HEAD 6e730bf7
  vs v137）：E1 两目标/E2 属性值/E3 三目标 3 功效案 HEAD
  TEXT-DIFF→v137 **BYTE-EQUAL PASS**；C1 融合落空单赋值/C2 兄弟独立
  赋值（LOAD 交错 STORE 不连续）/C5 r136 回边域（HEAD 已含 v136）
  零漂移 PASS；C3 链式融合域 walrus 形（r136 矩阵 C2 同形）/C4 循环
  体 UNPACK 元组族（C4_body_tuple 同族）实测 head 与 v137 输出逐字节
  同=预存在排除判定。**MATRIX: ALL PASS**（3 功效+3 控制+2 预存在）。
- **真函数复判**：E2/E3 全量重编译 **byte_equal=True**；r136 回归防护
  repro1/E1 byte_equal 维持；**get_matching_blocks 852=852 维持**；
  difflib 判官 **55/62（88.71%）维持**（无回退）。
- **A/B 电池 267 案**（r137_regress.py，单文件 RAG 交换 HEAD
  6e730bf7 vs v137）：**TEXT-DIFF 0/267**（全语料零漂移——整组归约
  仅在连续 STORE 段 N>=2+值段纯净+栈深足的结构事实下触发，267 语料
  零触发=外科性）；R110 168/169（mc1 正常归一）；登记差 10 案 ALL
  SAME-SIGNATURE（含 SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项
  一致，余 2 失败=冻结对 B01/BOUNDARY_02）。
- **REAL46 全量 sweep 豁免（小修口径）**：difflib 新鲜判官读数直接
  覆盖触达面+电池 267 零漂移兜底。

## 4. 验收口径

实测读数同 §3：E2/E3 形丢次级目标（真实 R1）修复、3 功效案重编译
BYTE-EQUAL、r136 功效域零回退；电池 267 案 TEXT-DIFF 0；pytest 冻结
对基线一致；difflib 55/62 维持。不宣称 G1/G2c/G3/G4/G6 通过；
product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **`_build_effective_stmts` UNPACK 分支缺失**（C4_ft_unpack 实测：
   `x, y = p`（UNPACK_SEQUENCE 2+STORE x+STORE y）渲染 `x = p`——
   UNPACK 落入 expr_instrs 缓冲被首 STORE 吞并，同域第五 walk 的
   UNPACK 缺口，首选下一轮）；循环体 UNPACK 元组族（C4_body_tuple
   同族预存在登记）；链式融合域 walrus 形（C3_ft_chain，COPY 域）；
   difflib 余 7 差单元（find_longest_match/get_grouped_opcodes/
   get_close_matches/_fancy_replace/_mdiff×2/_line_wrapper——控制流
   族）；REAL46-014 tarfile（142/160）/016 urllib.request（185/194）；
   REAL46-013 cookiejar 91/105、015 subprocess 68/78 余差；4
   compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r137.diff`（+66 单文件）、`matrix_v5r137.py`+result、
`r137_regress.py`+result、`difflib_judge_v137.txt`、本文件；中间件
D:/temp/opencode/cl_layout/r136diag、r137matrix、r137regress 不入库。
