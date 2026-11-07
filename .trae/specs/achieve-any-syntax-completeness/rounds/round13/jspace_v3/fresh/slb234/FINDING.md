# FINDING — rr-v5r141 [v141-SLB234]：while 自环体走查 B234 反源序多目标赋值整组归约（自环走查第七条缺口 walk 实例=真实 R1 修复；difflib find_longest_match 体段修复）

## 0. 结论速览

- 66.5 首选 difflib 余 7 差单元逐函数诊断首战 **find_longest_match**
  （1272 vs 1466，差 194 字节最大头）：对齐 diff + 产品文本对照实双重
  缺陷——①**while 自环体 `besti, bestj, bestsize = besti - 1, bestj - 1,
  bestsize + 1`（B234 反源序形）渲染 `bestsize = bestsize + 1`**（besti/
  bestj 整条丢失=真实 R1）；②4 首 BoolOp while 条件（含 not isj(...)
  调用首）拆成 `if A and B: while D:` + 重检碎片（条件拆分独立大族）。
- ①位点 = 自环走查 `_loop_extract_self_loop_stmts` STORE 分支（15358
  区）：首 STORE 走 `_build_store_statement` 重建单目标（reconstruct 仅
  返回栈顶）、次级 STORE 缓冲空落尾部污染、末级 STORE 携污染退化调用
  丢失——B234 归约此前已存在主 walk/42743/for 前缀/while 前缀（v134）/
  回边走查（v136）/融合落空块走查（v137），本自环走查为第七条实例。
- [v141-SLB234] 单文件 +61/−0（只增不破）：自环走查 STORE 分支（unpack
  状态机之后）新增 v136 同款整组归约——当前 STORE 起连续简单名 STORE
  段 N>=2（hdr.instructions 前瞻）+值段去噪无 COPY/SWAP/UNPACK_*+重建
  栈深 >=N → `Assign(Tuple(源序目标), Tuple(压栈序值))`、后随 STORE 经
  `_sl_skip_offsets`（主循环顶部既有守卫）跳过；未命中逐位落回（C3）。
  体边界启发式（_body_end_idx=末 STORE）保证归约后重检求值段不泄入
  缓冲。
- 真函数复判：repro2（简单 while+B234 体）**byte_equal=True**（HEAD 产
  品 `bestj = bestj - 1` 丢 besti → v141 完整还原）；r139/r140 功效域
  回归防护 byte_equal 维持；difflib 判官 55/62 维持；find_longest_match
  1272→1312（原 1466；体段闭合，余差=条件拆分族 154 字节登记）。

## 1. 根因（三层追踪）

- 诊断路径：diag7 对齐 diff（ratio 0.814）+ 产品文本/原源码对照——产
  品把 4 首 BoolOp while 拆 if+while 碎片且体丢 besti/bestj；repro1 复
  现后逐层剥离出纯 B234 形 repro2（简单 while 条件）A/B 实证 HEAD
  `bestj = bestj - 1`（besti 丢）→ v141 `besti, bestj = (besti - 1,
  bestj - 1)`。
- 字节码形态：自环单块 [B234 值求值 9 条, STORE bestsize, STORE bestj,
  STORE besti, 重检求值, POP_JUMP_BACKWARD_IF_TRUE→126]——自环跳回块
  首。
- 走查定位：trace/走查实例试探——自环跳回块首的 while 体由
  `_loop_extract_self_loop_stmts` 渲染（v139 已修其体边界启发式），其
  STORE 分支缺 B234 归约（UNPACK 状态机只覆盖 UNPACK 形）。

## 2. 修复（[v141-SLB234]，只增不破，单文件 +61/−0）

`_loop_extract_self_loop_stmts` STORE 分支（unpack 状态机之后、
STORE_SUBSCR/STORE_ATTR 之前）新增整组归约：
- 识别：`_sl_unpack_info is None and _self_loop_instrs` 非空+当前 STORE
  起连续简单名 STORE 段 N>=2（hdr.instructions/_sli_idx 前瞻）+值段
  （_self_loop_instrs 去 RESUME/NOP/CACHE/PUSH_NULL）无
  COPY/SWAP/UNPACK_SEQUENCE/UNPACK_EX+重建栈深（expr_reconstructor
  reset+逐指令回放取 stack 滤 PUSH_NULL）>=N；
- 归约：`Assign(targets=[Tuple(reversed stores)], value=Tuple(栈尾 N 项
  压栈序))`；`_self_loop_instrs` 清空、后随 STORE 偏移加入
  `_sl_skip_offsets`（主循环顶部既有 skip 守卫消费，防重复发射与缓冲
  污染）；
- 未命中（N<2/纯度拒/栈深不足）逐位落回既有单 STORE 路径（C3）。

## 3. 验证（全实测）

- **矩阵 8 案**（matrix_v5r141.py，A/B 单文件 RAG 交换 HEAD 1a0d1b58
  vs v141）：E1 简单 while+B234 两目标（repro2 精确形）/E2 三目标下
  标值/E3 B234 体+后随调用（归约不吞后随语句）3 功效案 HEAD
  TEXT-DIFF→v141 **BYTE-EQUAL PASS**；C1 while 单赋值/C2 while 解包
  （UNPACK 状态机既有域）/C3 r139 自环体/C4 r140 chain1 回归防护零
  漂移 PASS；R1_cond_scramble_preexisting（4 首 BoolOp while 条件拆分
  族——本轮新登记独立大族，体段已被本轮修复故 head≠v141，排除判
  定记录实测 text_same=False+byte_equal=False）。**MATRIX: ALL PASS**
  （3 功效+4 控制+1 预存在登记）。
- **真函数复判**：repro2 重编译 **byte_equal=True**；r139/r140 回归防
  护（repro1/chain1/chain2/census）byte_equal 维持；difflib 判官
  **55/62（88.71%）维持**；find_longest_match 1272→1312（原 1466，
  体段闭合、余差=条件拆分族 154 字节）。
- **A/B 电池 267 案**（r141_regress.py）：**TEXT-DIFF 0/267**（全语料
  零漂移）；R110 168/169；登记差 10 案 ALL SAME-SIGNATURE（含
  SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（基线一致，冻结
  对 B01/BOUNDARY_02）。
- **REAL46 全量 sweep 豁免（小修口径）**：difflib 新鲜判官读数直接覆
  盖触达面+电池 267 零漂移兜底。

## 4. 验收口径

实测读数同 §3：while 自环体 B234 丢次级目标（真实 R1）修复、3 功效
案重编译 BYTE-EQUAL、r139/r140 功效域零回退；电池 267 案 TEXT-DIFF
0；pytest 冻结对基线一致；difflib 55/62 维持；find_longest_match 体段
闭合（余差=条件拆分族登记）。不宣称 G1/G2c/G3/G4/G6 通过；
product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **while 多首 BoolOp 条件拆分族**（4 首 BoolOp while cond 含调用首
   拆 if+while+重检碎片——repro1 形，find_longest_match 尾段 3 个同构
   while 全中招；字节码形态=单块 cond 4 退出+自环体重检全 4 首；环分
   析器/合成层缺陷，真实 R1 级，首选下一轮大轮）；difflib 其余 6 差单
   元（get_grouped_opcodes/get_close_matches/_fancy_replace/_mdiff×2/
   _line_wrapper）；REAL46-014 tarfile（142/160）/016
   urllib.request（185/194）；REAL46-013 cookiejar 91/105、015
   subprocess 68/78 余差；4 compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r141.diff`（+61 单文件）、`matrix_v5r141.py`+result、
`r141_regress.py`+result、`difflib_judge_v141.txt`、本文件；中间件
D:/temp/opencode/cl_layout/r141diag、r141matrix、r141regress 不入库。
