# FINDING — rr-v5r147 [v147-ORANDTAIL]：or+and 尾 while 条件闭合（or 首混合链目标一致性判据豁免，E1/E2/E3 BYTE-EQUAL）

## 0. 结论速览

- 72.5 候选 or+and 尾族定位：F3 真源码 = `while i > 3 or b[i] and
  c[i]:`（= `i > 3 or (b[i] and c[i])`，or 优先级低于 and）。v146 渲染
  `while i > 3:` + 体内嵌套 if 碎片（`if b[i]: if c[i]: pass else:
  return i else: break`）——**and 尾组被逐出循环条件**，每次迭代不再复
  检 `b[i] and c[i]`（i 递增后语义漂移）=**真实 R1**。
- 结构探针：LoopRegion cond=0（i>3 块，or 头 POPJT→50=header）+块
  18=`b[i]`（POPJF→104=出口）+块 34=`c[i]`（POPJF→104，TRUE 落
  空→50）；回边副本=块 50 尾（i+=1 后 i>3 POPJB TRUE→50）→72（b[i]
  POPJF→104）→88（c[i] POPJB TRUE→50）。**FWDCHAIN cond@0 → None**：
  or 链前向走查在块 18 入链后（len=2）触发均匀链目标一致性判据
  （chain[0] 目标 50=header vs 当前块 18 目标 104=出口不等）→ 34 被
  截；截后链 [(0,'or'),(18,'and')] 进 v143 闭合——判据③（末成员落空
  ==header）失败（18 的落空=34≠50）→ 闭合**贯穿失败返回 None**（
  32727 既有贯穿语义）→ 全检测器链放弃 → and 尾落体内碎片。
- 根因本质：均匀链（全 and/全 or）目标一致性判据对 **or 首混合链**（or
  头 + and 尾组）结构性过严——or 头真腿直达 header、and 尾成员假腿出
  循环，成员目标**合法地不同**；判据把 and 尾截断后闭合判据③在截断
  链上必败。
- [v147-ORANDTAIL] analyzer 单文件 +10/−1（只增不破）：前向走查目标一
  致性判据加 `chain[0][1] != 'or'` 守卫——or 首链跳过该判据（截断根
  因），折叠合法性由 v143 闭合判据①-④整体承担（链首真边=header、末
  成员假边=出口+落空=header、非首成员无 STORE——F3 全链 [(0,'or'),
  (18,'and'),(34,'and')] 逐条满足）；and 首链（Round 08 嵌套形态误折
  叠防护域）维持原判据逐位不变。生成侧零改动（or_groups 分组
  [('or',[i>3]),('and',[b[i],c[i]])] → Or([i>3, And([b[i],c[i]])])=源
  级优先级）。
- 真函数复判：**E1/E2/E3 byte_equal=True**（渲染与源码逐字同，含 or 头
  init 前导 STORE 形）；na5/D1/r145 多块嵌套/r146 扁平/r143/r142/r141/
  r139 回归防护 byte_equal 维持；difflib 判官 56/62 维持。

## 1. 根因（三层追踪）

- F3 残差定位：v146 矩阵 P2 案（head==v146 逐字节同预存在）。
- FWDCHAIN=None 实证链：前向走查 [(0,'or')]→18 入链（len 1→2 无校
  验）→len≥2 校验 first_jt(50)≠cur_jt(104)→break→34 截→链
  [(0,'or'),(18,'and')]→all_same_target 失败→v143 闭合进入→①链首
  POPJT→50==header ✓→②末成员 18 POPJF→104 FORWARD FALSE ✓→③18 落
  空=34≠header **败**→贯穿 32727 `return None`。
- 均匀判据的适用域：Round 08 修复针对 **and 首链**（外层 if 测试
  false→else 与 while 预测试 false→出口的嵌套形态误折叠成扁平 and
  链）；or 首混合链的成员目标差异是 or/and 短路语义的结构事实，非嵌
  套信号——判据域应限 and 首链。

## 2. 修复（[v147-ORANDTAIL]，只增不破，单文件 +10/−1）

`region_analyzer.py` `_detect_while_boolop_forward_chain` 走查目标一致
性判据一处：`if len(chain) >= 2 and chain[0][1] != 'or':`（or 首链豁
免）；注释记录判据域转移依据（闭合判据①-④整体承担 or 首链合法性）。
v145/v146 前置通道在 F3 形自然不触发（块 0 无 FALSE 前驱）；D1/na5/
扁平域逐位保持。

## 3. 验证（全实测）

- **矩阵 14 案**（matrix_v5r147.py，A/B 单文件交换 HEAD 1d959c3a vs
  v147）：E1 or+and 尾（下标）/E2 纯名+调用尾/E3 or 头 init 前导
  STORE HEAD TEXT-DIFF→v147 **BYTE-EQUAL PASS**+C1 na5/C2 D1 守卫
  or/C3 r145 多块嵌套/C4 r146 扁平/C5 扁平纯名/C6 r143 or 链/C7 r142
  and 链/C8 r141 自环/C9 r139 自环体回归防护零漂移 PASS+P1 守卫嵌套/
  P2 守卫嵌套2 head 与 v147 逐字节同预存在零触碰=**MATRIX ALL PASS**
  （3 功效+9 控制+2 预存在）。
- **A/B 电池 267 案**（r147_regress.py）：**TEXT-DIFF 0/267** 全语料零
  漂移；R110 169 案 TEXT 一致 168/签名一致 167（唯一变化=na5 改进
  A/B 口径归一，v147==v146 输出）；REG-10 其余 9 案 ALL
  SAME-SIGNATURE（含 SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（基线一致，冻结
  对 B01/BOUNDARY_02）。
- **REAL46 判官**：difflib 56/62（90.32%）维持；REAL46 全量 sweep 豁免
  （小修口径）。不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT
  PASS。

## 4. 验收口径

实测读数同 §3：E1-E3（真实 R1 条件复检丢失）闭合、C1-C9 域零回退、
电池 267 案零漂移、pytest 冻结对基线一致、difflib 56/62 维持。

## 5. 剩余登记（下一轮候选）

1. **守卫嵌套族**（`if a: while b and (c or d):` → `if a and b: while
   c or d:`——三层手术：截断式前置（守卫成员无环副本截去）+越界朴素
   BoolOpRegion [守卫头,循环头] 撤销+IfRegion 条件链重建，本轮探针实
   证结构）；difflib 其余 6 差单元（get_grouped_opcodes/
   get_close_matches/_fancy_replace/_mdiff×2/_line_wrapper）；REAL46-
   014 tarfile（142/160）/016 urllib.request（185/194）；REAL46-013
   cookiejar 91/105、015 subprocess 68/78 余差；4 compile_error；
   pytest 余 2 冻结对（登记态）。
2. **REG-10 口径**：na5 维持 BYTE-EQUAL 改进态（r143 起登记），后续电
   池 REGISTERED 名单可缩减（na5 移出、R110 比对行同步归一）。

## 6. 证据文件

`fix_patch_v5r147.diff`（单文件 +10/−1）、`matrix_v5r147.py`+result、
`r147_regress.py`+result、`difflib_judge_v147.txt`、本文件；中间件
D:/temp/opencode/cl_layout/r147diag、r147matrix、r147regress 不入库。
