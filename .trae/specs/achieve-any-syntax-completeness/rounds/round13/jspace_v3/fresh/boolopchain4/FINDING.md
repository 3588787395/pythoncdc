# FINDING — rr-v5r142 [v142-BOOLOPCHAIN4]：while 多首 BoolOp 条件链回溯体语义集合补回溯游标（条件拆分族闭合，difflib 55→56/62，find_longest_match 全等）

## 0. 结论速览

- 67.5 首选 while 多首 BoolOp 条件拆分族：repro1（4 首 `while A and B and
  not C and D:`）区域树探针实证——分析器把环条件块定为 78（仅 D 首），
  链走查 `_detect_while_condition_boolop_chain` 探针返回 **[(38,'and'),
  (78,'and')] 仅 2 成员**——回溯在中间操作数 B26 处中断，链头 A/B 被
  外层 IfRegion 抢占为守卫（`if A and B: while D:` 碎片化+重检残片）。
- 断链点 = 回溯的 `cond_in_loop` 检查：前一操作数的 fall-through ==
  current（链内续接），但 current 不在体语义集合（body_blocks ∪
  {header, entry, condition_block}）中——cond_in_loop 误 False → break。
  3+ 操作数链必中招（2 首链首步 pred_ft==condition_block 恰好通过，
  与 C1 控制案实测一致）。
- [v142-BOOLOPCHAIN4] 单文件 +13/−0（只增不破）：回溯游标 current 并
  入体语义集合——current 是上一步刚通过合法性校验（跳转目标=循环出
  口、fall-through 续接链）的链成员，其 fall-through 续接属链内结构事
  实。修复后链探针返回 **[(0,'and'),(26,'and'),(38,'and'),(78,'and')]**
  全 4 成员，repro1 渲染与源码逐字同。
- 真函数复判：repro1 **byte_equal=True**；**find_longest_match 1466=
  1466 co_code 全等（单元闭合，v141 的 1312→全等）**；difflib 判官
  **55/62→56/62（88.71%→90.32%）**；get_matching_blocks 852=852 维持。

## 1. 根因（三层追踪）

- 区域树探针（post-generate regions dump）：LoopRegion@78
  condition=78 back_edge=220 body=[126,168,180,220] + BoolOpRegion@26
  blocks=[26,38] + IfRegion@0 condition=26 then=[78]——守卫 if 碎片。
- 链探针（trace14）：`_detect_while_condition_boolop_chain(78, loop)`
  → [(38,'and'),(78,'and')]——2 成员即断。
- 断链定位：回溯第二步 current=B38、pred=B26 时，pred_ft（B26 的
  fall-through）=B38=current，但 `_loop_body_semantic` 只含
  body_blocks+[header,entry,condition]——cond_in_loop=False → break。

## 2. 修复（[v142-BOOLOPCHAIN4]，只增不破，单文件 +13/−0）

`region_analyzer.py` `_detect_while_condition_boolop_chain` 回溯体语义
集合构造（31377 区）补 `if current is not None:
_loop_body_semantic.add(current)`：
- 识别/合法性不变（跳转目标=循环出口 else_outside、fall-through 续接
  链 cond_in_loop、极性反转守卫、walrus STORE 豁免等既有判据全部保
  持）；
- 仅把上一步已认领的链成员 current 视为「链内」事实（I.4 白名单：
  同一性判定），使中间操作数的 fall-through 续接通过 cond_in_loop。

## 3. 验证（全实测）

- **矩阵 8 案**（matrix_v5r142.py，A/B 单文件交换 HEAD 91e7b412 vs
  v142，本轮文件=region_analyzer.py）：E1 4 首 BoolOp while（repro1
  精确形）/E2 3 首（中间操作数断链精确形）/E3 双同构 4 首 while
  （find_longest_match 尾段形态）3 功效案 HEAD TEXT-DIFF→v142
  **BYTE-EQUAL PASS**；C1 2 首 BoolOp while（既有工作域——首步
  pred_ft==condition_block 恰好通过，零漂移实证）/C3 简单 while/C4
  r141 自环体/C5 r139 自环体回归防护零漂移 PASS；C2 while or 链实测
  head 与 v142 输出逐字节同=预存在排除判定（or 极性拆分族，另一走查
  位点，本轮登记下轮）。**MATRIX: ALL PASS**（3 功效+4 控制+1 预存在）。
- **真函数复判**（verify6）：repro1 重编译 **byte_equal=True**；
  r141/r139/r140 回归防护（repro2/repro1/chain1/chain2/census）
  byte_equal 维持；**find_longest_match 1466=1466 全等**；
  get_matching_blocks 852=852 维持；difflib units DIFF 7→6/60。
- **A/B 电池 267 案**（r142_regress.py，本轮修正目标文件为
  region_analyzer.py——首跑 self-heal 实证继承脚本的 RAG 路径错配并
  修正，证据目录存修正版）：**TEXT-DIFF 0/267**（全语料零漂移）；
  R110 168/169；登记差 10 案 ALL SAME-SIGNATURE（含 SUBST-SIG
  pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（基线一致，冻结
  对 B01/BOUNDARY_02）。
- **REAL46 判官**：difflib **55/62→56/62（88.71%→90.32%）**——
  find_longest_match 全闭合；REAL46 全量 sweep 豁免（小修口径）。

## 4. 验收口径

实测读数同 §3：条件拆分族（真实 R1）闭合、repro1/3 功效案重编译
BYTE-EQUAL、find_longest_match 全等、2 首/or 链域零触碰（C1 实证）；
电池 267 案 TEXT-DIFF 0；pytest 冻结对基线一致；difflib 56/62。不宣
称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **while or 链条件拆分族**（C2 形 `while i > 3 or b[i] == 1:` 渲染
   `while i > 3: return b[i]==1` 碎片——or 极性 sibling 族，另一走查
   位点，本轮实测登记）；difflib 其余 6 差单元（get_grouped_opcodes/
   get_close_matches/_fancy_replace/_mdiff×2/_line_wrapper）；
   REAL46-014 tarfile（142/160）/016 urllib.request（185/194）；
   REAL46-013 cookiejar 91/105、015 subprocess 68/78 余差；4
   compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据文件

`fix_patch_v5r142.diff`（+13 单文件）、`matrix_v5r142.py`+result、
`r142_regress.py`+result（修正版：目标文件 region_analyzer.py）、
`difflib_judge_v142.txt`、本文件；中间件
D:/temp/opencode/cl_layout/r141diag、r142matrix、r142regress 不入库。
