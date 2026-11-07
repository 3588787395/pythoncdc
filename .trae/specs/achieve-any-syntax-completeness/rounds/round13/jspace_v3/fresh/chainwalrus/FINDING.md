# FINDING — rr-v5r140 [v140-SLCENSUS/CHAINFT/CHAINSTORE]：自环域白名单清点收尾 + 链式赋值 walrus 误渲染双域修复（真实 R1）

## 0. 结论速览

- 65.5 首选**自环域其余白名单清点**完成：m1 形（`res.append({'k': a,
  'j': b})`）实测仍丢 append——常量键字典优化 **BUILD_CONST_KEY_MAP**
  不在 65 轮扩展白名单（LOAD a, LOAD b, LOAD_CONST ('k','j'),
  BUILD_CONST_KEY_MAP 处 break）；m2 f-string（FORMAT_VALUE 既有）/
  m3 方法+下标（BINARY_SUBSCR v139 已补）幸存。清点结论：白名单补
  BUILD_CONST_KEY_MAP 一项即闭合（[v140-SLCENSUS]）。
- 65.5 次选**链式融合域 walrus 形**实测双域破：
  1. **融合落空域**（chain1）：`for v in vs: if v: a += v; else: a = b = v`
     渲染 `(a := v)`——**b 赋值整条丢失**（真实 R1）。位点 =
     `_build_effective_stmts` STORE 分支：expr_instrs=[LOAD v, COPY 1]，
     v137 B234 纯度判据正确拒绝 COPY → `_build_statement` 重建
     NamedExpr（walrus）+ 次级 STORE 缓冲空落尾部污染丢失。
  2. **全链输入域**（chain2）：函数顶 `a = b = 0` 渲染 `b = (a := 0)`——
     调用方把整条链 [LOAD_CONST 0, COPY 1, STORE a, STORE b] 一次传入
     `_build_store_statement`，既有 walrus 保留路径把中间 STORE 并入
     value 段、末 STORE 作目标 → NamedExpr（语义侥幸同、文本/字节差）。
     trace 实证 79 行包装器虽有 B85 委托，但 `_scan_prefix_chain_assign`
     判据 (a) 要求累积段以 COPY 收尾——包装器传 instrs[:-1]（以 STORE
     收尾）判据必败。
- [v140-CHAINFT]：`_build_effective_stmts` STORE 分支新增链归约——值
  缓冲尾 COPY(arg==1) + 后随 ≥1 连续简单名 STORE → 链式源序 targets、
  剥 COPY 值、is_chain_assign=True；与独立 walrus（COPY+单 STORE+
  POP_TOP）由后随 STORE 判据区分，不命中逐位落回。
- [v140-CHAINSTORE]：真 `_build_store_statement`（74550 区）头部新增
  全链识别——≥2 连续简单名 STORE 收尾 + 其前恰为 COPY 1 + 非空值段
  （followers 就在 instrs 内，无需块上下文）；79 行包装器同步补全链
  分支（经 _scan_prefix_chain_assign 以链首 STORE 为归约点）。
  COPY 1 + ≥2 连续 STORE 恒为链式赋值，独立 walrus（_cs_n=1）不命中。
- 真函数复判：census/chain1/chain2 全量 **byte_equal=True**；r136-r139
  功效域回归防护 byte_equal 维持；get_matching_blocks 852=852 维持；
  difflib 判官 55/62 维持。

## 1. 根因（三层追踪）

- 清点（census.py 三形）：BUILD_CONST_KEY_MAP break → m1 append 截断
  （65 轮同族缺口收尾）。
- chain1：trace12 实证 `(a := v)` 自 `_build_effective_stmts:5686`
  `_build_statement([LOAD v, COPY 1, STORE a])`（经 _process_if_blocks
  34280 落空块路径）；STORE b 缓冲空丢失。
- chain2 init：trace11 实证 `_build_store_statement([LOAD_CONST 0,
  COPY 1, STORE a, STORE b])` 全链输入；79 行包装器委托
  _scan_prefix_chain_assign 判据 (a)（累积段 COPY 收尾）对全链剥尾
  输入必败 → gen 重建 NamedExpr。

## 2. 修复（[v140-SLCENSUS/CHAINFT/CHAINSTORE]，只增不破，单文件 +106/−1）

1. 自环体边界扩展白名单补 `BUILD_CONST_KEY_MAP`（14863 区）；
2. `_build_effective_stmts` STORE 分支前置链归约（v137 B234 之前，
   COPY 尾判据 + effective 前瞻 follower，_bes_skip_offsets 消费）；
3. 真 `_build_store_statement` 头部全链识别（_cs_n≥2 + COPY 1 + 非空
   值段 → 链 Assign 自包含归约）；79 行包装器补全链分支（链首 STORE
   为 _scan_prefix_chain_assign 归约点 + _chain_consumed 登记）。

## 3. 验证（全实测）

- **矩阵 8 案**（matrix_v5r140.py，A/B 单文件 RAG 交换 HEAD 623ef8e4
  vs v140）：E1 常量键字典/E2 落空域链/E3 init 链/E4 调用值链 4 功效
  案 HEAD TEXT-DIFF→v140 **BYTE-EQUAL PASS**；**C1 独立 walrus
  （COPY+单 STORE+POP_TOP，判别案 _cs_n=1 不命中）零漂移 PASS**；
  C2 融合域 B234（链检查不抢 B234 归约）/C3 r139 自环体/C4 r136 回边
  回归防护零漂移 PASS。**MATRIX: ALL PASS**（4 功效+4 控制）。
- **真函数复判**（verify5）：census/chain1/chain2 重编译 **byte_equal
  =True**；r139/r138/r137/r136 回归防护 byte_equal 维持；
  **get_matching_blocks 852=852 维持**；difflib 判官 **55/62（88.71%）
  维持**（无回退）。
- **A/B 电池 267 案**（r140_regress.py）：**TEXT-DIFF 0/267**（全语料
  零漂移）；R110 168/169；登记差 10 案 ALL SAME-SIGNATURE（含
  SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（基线一致，冻结
  对 B01/BOUNDARY_02）。
- **REAL46 全量 sweep 豁免（小修口径）**：difflib 新鲜判官读数直接覆
  盖触达面+电池 267 零漂移兜底。

## 4. 验收口径

实测读数同 §3：BUILD_CONST_KEY_MAP 清点缺口闭合、chain1 真实 R1（b
丢失）修复、chain2 init walrus 误渲染修复；4 功效案重编译 BYTE-EQUAL；
独立 walrus 判别案零漂移；r136-r139 功效域零回退；电池 267 案
TEXT-DIFF 0；pytest 冻结对基线一致；difflib 55/62 维持。不宣称
G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **difflib 余 7 差单元**（find_longest_match 1272 vs 1466 差 194 字
   节最大头/get_grouped_opcodes/get_close_matches/_fancy_replace/
   _mdiff×2/_line_wrapper——控制流族，首选下一轮）；REAL46-014
   tarfile（142/160）/016 urllib.request（185/194）；REAL46-013
   cookiejar 91/105、015 subprocess 68/78 余差；4 compile_error；
   pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r140.diff`（+106/−1 单文件）、`matrix_v5r140.py`+result、
`r140_regress.py`+result、`difflib_judge_v140.txt`、本文件；中间件
D:/temp/opencode/cl_layout/r140diag、r140matrix、r140regress 不入库。
