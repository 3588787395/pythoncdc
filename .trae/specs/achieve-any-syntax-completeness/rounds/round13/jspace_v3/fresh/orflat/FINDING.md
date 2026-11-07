# FINDING — rr-v5r146 [v146-ORFLAT]：扁平 and-or while 条件闭合（or 闭合扁平形前置判据，E1/E2 BYTE-EQUAL）

## 0. 结论速览

- 71.5 首选扁平 and-or 族定位：F1 真源码 = `while i < 5 and b[i] or
  c[i]:`（= `(i < 5 and b[i]) or c[i]`，平坦优先级）。v145 渲染
  `if i < 5: while b[i] or c[i]:`——and 组（i<5 块）被外提守卫 if 只查一
  次，循环内 i 递增后 `b[i]` 求值条件丢失每迭代的 `i < 5` 复检=**真实
  R1**；F2 纯名形（`while a and b or c:` → `if a: while b or c:`）同族。
- 结构探针：LoopRegion cond=18（b[i] 块，and 组末成员 TRUE→body=or
  头）+BoolOpRegion blocks=[18,34,72,88] op_chain=[(18,'or'),(34,'and')]
  merge=104+IfRegion blocks=[0,18] cond=0（守卫认领 and 头块 0）；块 0
  （init i=0 + i<5）FALSE→**34（or 尾入口块）**≠出口 104——嵌套形判据
  （v145 FALSE→出口）结构性不命中。
- **嵌套/扁平唯一块级区分**（本轮核心判别）：or 链前向走查两形完全同
  形（and 组末成员 TRUE→body、or 尾 FALSE→exit），区分只在 and 组成员
  的假边目标——嵌套形 FALSE→循环出口（==or 尾假出口）、扁平形 FALSE→
  or 尾入口块（==chain[1][0]，短路跳进条件序列续接 or 右操作数）。二者
  互斥（出口 ∉ 条件块集）。
- [v146-ORFLAT] analyzer 单文件 +54/−0（只增不破）：v145 嵌套回溯未命
  中且链长≥2 时按扁平判据回溯收集 and 组前缀（连续前驱：FORWARD FALSE
  族收尾+假边目标==chain[1][0]+落空续接前驱成员+非体/header，16 上
  限），收集后走 v145 同一回边复核贪心副本匹配门控（扁平真 while 条件
  同样回边重检全条件：F1 体块 50 尾含 i<5 副本、块 72/88 含 or 腿副
  本）；前置后链=and 组('and')+or 组（统一记 'or'）——生成侧既有
  or_groups 分组（and 段闭合于首个 'or'）与 `_detect_boolop_grouping`
  （and 块假边目标 ∈ 链块→INNER 信号→outer='or'）重建
  Or([And([i<5, b[i]]), c[i]])=源级平坦优先级，生成侧零改动。
- 真函数复判：**F1/F2 byte_equal=True**（渲染与源码逐字同）；na5/D1/
  r145 多块嵌套/r143/r142/r141/r139 回归防护 byte_equal 维持；difflib
  判官 56/62 维持。

## 1. 根因（三层追踪）

- F1 残差定位：v145 矩阵 P 案（head==v145 逐字节同预存在）。块布局
  （dis 实证）：块 0=init `i=0` STORE + `i<5`（FALSE→34）→块 18=`b[i]`
  （TRUE→50=header，FALSE 落空→34）→块 34=`c[i]`（FALSE→104=出口）；
  回边副本=块 50 尾（i+=1 后 i<5，FALSE→88）→块 72（b[i] POPJB
  TRUE→50）→块 88（c[i] POPJB TRUE→50，FALSE 落空→104）。
- v145 嵌套回溯在块 0 处不命中（FALSE 目标 34 ≠ _oc_exit 104）→ 链保
  持 [(18,'or'),(34,'and')] → 生成侧 or_groups 以此双成员链渲染
  `b[i] or c[i]`，块 0 留守卫 IfRegion（cond=0 blocks=[0,18] merge=34）
  → `if i < 5: while b[i] or c[i]:`。
- 生成侧实证零缺口：链补全为 [(0,'and'),(18,'or'),(34,'or')] 后既有
  `_detect_boolop_grouping`（块 0 假边 34 ∈ 链块集→INNER 信号→
  outer='or'）+or_groups 分组直接重建正确平坦形——缺口纯在 analyzer
  前置判据少扁平形。

## 2. 修复（[v146-ORFLAT]，只增不破，单文件 +54/−0）

`region_analyzer.py` or 闭合收尾一处：嵌套回溯（FALSE→出口）未命中且
len(chain)≥2 时追加扁平回溯（FALSE→chain[1][0]，其余判据逐字同构），
收集结果并入既有 `_on_heads` 通道→同一回边复核门控→同一前置+or 组重
标签。守卫头（FALSE→出口）与 walrus 剥离殆尽（值段空）均不命中；D1/
na5/r145 域逐位保持。

## 3. 验证（全实测）

- **矩阵 12 案**（matrix_v5r146.py，A/B 单文件交换 HEAD 7c92b061 vs
  v146）：E1 扁平 and-or/E2 纯名形 HEAD TEXT-DIFF→v146 **BYTE-EQUAL
  PASS**+C1 na5/C2 D1 守卫 or/C3 r145 多块嵌套/C4 r143 or 链/C5 r142
  and 链/C6 r141 自环/C7 r139 自环体回归防护零漂移 PASS+P1 守卫嵌套/
  P2 or+and 尾/P3 守卫嵌套2 head 与 v146 逐字节同预存在零触碰=**MATRIX
  ALL PASS**（2 功效+7 控制+3 预存在）。
- **A/B 电池 267 案**（r146_regress.py）：**TEXT-DIFF 0/267** 全语料零
  漂移；R110 169 案 TEXT 一致 168/签名一致 167（唯一变化=na5 改进
  A/B 口径归一，v146==v145 输出）；REG-10 其余 9 案 ALL
  SAME-SIGNATURE（含 SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（基线一致，冻结
  对 B01/BOUNDARY_02）。
- **REAL46 判官**：difflib 56/62（90.32%）维持；REAL46 全量 sweep 豁免
  （小修口径）。不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT
  PASS。

## 4. 验收口径

实测读数同 §3：E1/E2（真实 R1 条件复检丢失）闭合、C1-C7 域零回退、
电池 267 案零漂移、pytest 冻结对基线一致、difflib 56/62 维持。

## 5. 剩余登记（下一轮候选）

1. **守卫嵌套族**（`if a: while b and (c or d):` → `if a and b: while
   c or d:`——守卫 if 与循环 and 头构成同假出口连续链被合并为守卫条
   件，需守卫条件链与循环条件块的边界分离）；**or+and 尾族**（F3
   `while i > 3 or b[i] and c[i]:` → while i>3+体内嵌套 if 碎片——or
   头+and 尾链 [(or),(and),(and)] 的分组重建缺口）；difflib 其余 6 差
   单元（get_grouped_opcodes/get_close_matches/_fancy_replace/
   _mdiff×2/_line_wrapper）；REAL46-014 tarfile（142/160）/016
   urllib.request（185/194）；REAL46-013 cookiejar 91/105、015
   subprocess 68/78 余差；4 compile_error；pytest 余 2 冻结对（登记
   态）。
2. **REG-10 口径**：na5 维持 BYTE-EQUAL 改进态（r143 起登记），后续电
   池 REGISTERED 名单可缩减（na5 移出、R110 比对行同步归一）。

## 6. 证据文件

`fix_patch_v5r146.diff`（单文件 +54/−0）、`matrix_v5r146.py`+result、
`r146_regress.py`+result、`difflib_judge_v146.txt`、本文件；中间件
D:/temp/opencode/cl_layout/r146diag、r146matrix、r146regress 不入库。
