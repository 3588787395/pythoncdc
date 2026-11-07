# FINDING — rr-v5r143 [v143-ORCHAIN]：while or 链条件拆分族闭合（前向 or 闭合判据 + 链首前缀保留，na5 登记差案实质改进）

## 0. 结论速览

- 68.5 首选 while or 链条件拆分族（C2 形 `while i > 3 or b[i] == 1:`
  渲染 `while i > 3: return b[i]==1` 碎片）三层定位：
  1. **or 链前向闭合缺失**：字节码形态=or 真出口→体入口（A 块
      POP_JUMP_FORWARD_IF_TRUE→header）、假出口→循环出口（B 块
      POP_JUMP_FORWARD_IF_FALSE→exit）。前向链走查收齐 [(0,'or'),
      (18,'and')] 后按 **all_same_target** 判据（and 链唯一合法性判
      据）判 False → None；回溯走查只看 predecessors 够不着后继操作
      数（or 次操作数是链首的 fall-through 后继）——or 条件链彻底丢
      失，次操作数块被排除出循环条件成独立 Region（渲染 junk return）
      （**真实 R1**：or 条件丢失=每次迭代不再复查次操作数，语义破坏）。
  2. **链首前缀重置蒸发**：前向闭合修复后 or 条件还原，但链首块与条
      件块同块（`i = 0` init 与 or 条件同块）——cond 走查按 op_chain
      分段器契约把前导 STORE 提取进 pre_stmts 后，boolop 分支的
      `pre_stmts = []` 重置把它们清空；下方逐链块重提取被
      `chain_block != cond_block` 守卫跳过（or 链的 cond_block 恰为链
      首）——`i = 0` 蒸发（探针实证 BSS emit→stmt 但终返回 dict 无前
      缀）。
- [v143-ORCHAIN] 双文件 +75/−1（只增不破）：
  1. region_analyzer `_detect_while_boolop_forward_chain`：all_same_target
     失败后新增 **or 链前向闭合判据**——①链首 op='or' 且跳转目标 ==
     loop.header_block（or 真出口=体）；②末成员 FORWARD FALSE 族收尾、
     目标=循环出口（假出口唯一收敛）且不在体语义集合；③末成员
     fall-through == header（完备性闭合）；④非首成员无 STORE_*（R38
     前置排除）；未命中逐位落回 None（C3）。
  2. region_analyzer B6 所有权校验：纯基类 `Region` 占位认领（块集 ⊆
     链块集）让位给条件链（撤销走既有 _b6_supersede 序列）。
  3. region_ast_generator `_loop_generate_while` boolop 分支：链首块
     恰为条件块时保留 cond 走查前缀（非链首 cond_block 的 and 链维持
     原重置，逐位不变）。
- 真函数复判：C2 全量 **byte_equal=True**；r142/r141/r139/r140 回归防
  护 byte_equal 维持；**na5 登记差案实质改进**（HEAD 版
  `while items[i]:` 丢 `or opt` 重检=opt 假时死循环的语义破损+junk
  碎片；v143 渲染=真源码结构 or 条件完整；余差=字节 43 起的既有 if
  包装族残差，orig 136 vs prod 98）；difflib 判官 56/62 维持。

## 1. 根因（三层追踪）

- 区域树探针（C2）：LoopRegion@0 header=42 condition=0 body=[42,64] +
  **Region@18 独立**——次操作数块被排除出环。
- 链探针：`_detect_while_boolop_forward_chain(0, loop)` → None；
  `_detect_while_condition_boolop_chain(0, loop)` → [(0,'or')] 单成员。
- 前向走查代码走读：all_same_target 判 42≠88 → None（or 结构性不满
  足）；B6 占位 Region@18 认领 18 → 所有权校验拒链。
- 前缀蒸发：BSS 探针 `_build_store_statement([LOAD_CONST 0, STORE i])`
  经 `_loop_generate_while:9809` → stmt；终返回 dict 无前缀 →
  881 行重置清空 + 905 区守卫跳过。

## 2. 修复（[v143-ORCHAIN]，只增不破，双文件 +75/−1）

见 §0 修复清单。闭合判据全部 I.4 白名单（块末 opcode 极性 + 跳转/
落空目标同一性）；and 链路径（all_same_target 通过）逐位不变；B6 让
位仅对 `type(r) is Region` 精确基类占位（任何语义子类不让位）。

## 3. 验证（全实测）

- **矩阵 7 案**（matrix_v5r143.py，A/B 双文件交换 HEAD 13610dcc vs
  v143）：E1 2 首 or 链（C2 精确形）/E2 3 首 or 链/E3 or 次操作数带
  调用 3 功效案 HEAD TEXT-DIFF→v143 **BYTE-EQUAL PASS**；C1 and 链
  （r142 功效域）/C2 非循环 or 链 if（不同域）/C3 r141 自环体/C4
  r139 自环体回归防护零漂移 PASS。**MATRIX: ALL PASS**（3 功效+4 控
  制）。
- **真函数复判**（verify7）：C2 重编译 **byte_equal=True**；r142
  E1/r141 repro2/repro1/r139/r140 chain1 回归防护 byte_equal 维持；
  get_matching_blocks 852=852、find_longest_match 1466=1466 维持；
  difflib units DIFF 6/60 维持。
- **A/B 电池 267 案**（r143_regress.py，双文件电池适配版）：TEXT-DIFF
  **1/267**——唯一差异=**na5 登记差案实质改进**（§0/§5 定性；其余
  266 案零漂移）；R110 169 案 TEXT 状态一致 167/签名一致 168——唯一
  变化=na5（同上）；REG-10 其余 9 案 ALL SAME-SIGNATURE（含 SUBST-SIG
  pd8_prod）；NO-SRC 0。
- **na5 定性**（字节码实证）：真源码=「if i < len(items): while
  items[i] or opt: i += 1; return i」；HEAD 渲染 `while items[i]:` +
  junk `opt` Expr + `if opt: pass/else: return i` 碎片——or 次操作数
  重检丢失=**opt 假时死循环的真实 R1 语义破损**；v143 渲染=真源码结
  构（or 条件完整），余差=字节 43 起既有 if 包装族残差（orig 136 vs
  prod 98，登记态）。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（基线一致，冻结
  对 B01/BOUNDARY_02）。
- **REAL46 判官**：difflib 56/62（90.32%）维持；REAL46 全量 sweep 豁
  免（小修口径）。

## 4. 验收口径

实测读数同 §3：or 链拆分族（真实 R1）闭合、3 功效案重编译 BYTE-EQUAL、
and 链/非循环 or/r139-r142 域零回退；电池 267 案 1 处 TEXT-DIFF=na5
实质改进（定性见 §3/§5）、其余 266 零漂移；pytest 冻结对基线一致；
difflib 56/62 维持。不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍
NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **na5 if 包装族残差**（字节 43 起，orig 136 vs prod 98——`if i <
   len(items):` 外层守卫与 while 入口检查的重复求值布局差，登记态）；
   while or 多首更深层形态（or+and 混合链 `while A or B and C:` 未在本
   轮矩阵覆盖）；difflib 其余 6 差单元（get_grouped_opcodes/
   get_close_matches/_fancy_replace/_mdiff×2/_line_wrapper）；
   REAL46-014 tarfile（142/160）/016 urllib.request（185/194）；
   REAL46-013 cookiejar 91/105、015 subprocess 68/78 余差；4
   compile_error；pytest 余 2 冻结对（登记态）。
2. **REG-10 口径更新**：na5 自本轮起签名=v143 改进形（or 条件完整），
   后续轮电池以本读数为新基线。

## 6. 证据文件

`fix_patch_v5r143.diff`（双文件 +75/−1）、`matrix_v5r143.py`+result、
`r143_regress.py`+result（双文件电池适配版）、`difflib_judge_v143.txt`、
本文件；中间件 D:/temp/opencode/cl_layout/r141diag、r143matrix、
r143regress 不入库。
