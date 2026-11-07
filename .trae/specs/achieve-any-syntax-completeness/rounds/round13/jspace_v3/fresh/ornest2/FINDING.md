# FINDING — rr-v5r145 [v145-ORNEST2]：多块 and 头嵌套链闭合（整段回溯前置 + 回边复核判别 + 生成侧后向 or 腿续链，E2 BYTE-EQUAL + D1 v144 误触发回归闭合）

## 0. 结论速览

- 70.5 首选多块 and 头嵌套链定位：E2 真源码 = `while i < 10 and a[i]
  and (b[i] or f(i)):`。v144 渲染 `if i < 10 and a[i]: while b[i] or
  f(i):` + 体内重检碎片——**and 头（两块）被外提守卫 if 只查一次**，循环
  内 i 递增后 `a[i]/b[i]` 越界（IndexError）=**真实 R1**；v144 单块前置
  限定（`_on_ext`）在多块 and 头让位=整链回落守卫族。
- **D1 回归发现**（v144 自身引入，本轮域内闭合）：`if a: while b or c:`
  v144 误渲染 `while a and (b or c):`——守卫 if 头与 and 头在
  predecessors 走查视角块级结构全同（FALSE→同一循环出口、落空续接链
  首），v144 单块前置在守卫头误触发=单次检查变成每次迭代重检。
- [v145-ORNEST2] 双文件（只增不破）：
  1. `region_analyzer.py`（+121/−50，v144 单块逻辑整段一般化）：①or 闭
     合前置改**整段回溯**——自链首前驱起连续收集「FORWARD FALSE 族收尾
     +假边目标==本链假出口+落空续接前驱成员+非体/header」的 and 前缀块
     （E2 的 i<10、a[i] 两块整段），安全上限 16；②**回边复核判别**（守
     卫 if 与 and 头的唯一结构区分）：真 while 条件在回边重检全条件，
     循环环（header 前向可达∩前驱可达）内存在每个成员的逐块复核副本；
     判据=前置后最终链全员在环块集中**贪心匹配独立副本块**（成员去噪
     pre-jump 值段[链首 STORE 前缀剥离]==副本去噪 pre-jump 序列后缀，副
     本互不重复；任一成员无副本/冲突/值段空→整段不前置逐位回落 v143
     闭合行为）。D1 的守卫头在环内无副本→不前置→`if a: while b or c:`
     正确渲染；na5/E2 的 and 头在环内有副本→前置。
  2. `region_ast_generator.py`（+21/−1）：自循环提取器
     `_loop_extract_self_loop_stmts` 的 `_is_compound_loop_cond` 链走查
     补**后向 or 腿续链**——or 链回边 or 腿副本以
     POP_JUMP_BACKWARD_IF_TRUE→header 收尾（or 短路真腿直达体入口），
     原判据只认 FORWARD 中间段在 or 腿副本处 break → header 重检尾渲染
     为体内伪 if-break（E2 实测 `if i < 10: break` 幻影=真实 R1 第二
     层）；补中间段 BACKWARD→header 续链后 `_is_compound_loop_cond` 判
     真、重检尾归条件语义抑制。
- 真函数复判：**E1（E2 形）byte_equal=True**（渲染与源码逐字同）、
  **D1 byte_equal=True**（v144 误触发闭合）；na5/r143 or 链/r142 and
  链/r141/r139 回归防护 byte_equal 维持；difflib 判官 56/62 维持。

## 1. 根因（三层追踪）

- E1 残差定位：v144 矩阵 E2 案 head==v144 逐字节同（预存在排除判定）。
  结构探针：LoopRegion cond=34（b[i] 块）+BoolOpRegion blocks=
  [0,18,34,50,94,110,126] op_chain=[(34,'or'),(50,'and')]（v143 or 闭合
  收尾 run）+IfRegion blocks=[0,18,34]（守卫 if 认领 and 头两块 0/18）。
- 块布局（dis 实证）：块 0=init `i=1` STORE + `i<10`（FALSE→148）→块
  18=`a[i]`（FALSE→148）→块 34=`b[i]`（TRUE→72=header）→块 50=`f(i)`
  （FALSE→148）；回边副本=块 72 尾（i+=1 后 `i<10`）→块 94（`a[i]`）→
  块 110（`b[i]` POPJB TRUE→72）→块 126（`f(i)` POPJB TRUE→72）。
- **D1 判别案**（probe5 实证 v144 误触发）：`if a: while b or c:` 的守
  卫块 a 与 na5 的 and 头在 FALSE 目标（==or 假出口）与落空后继（==链
  首）上全同——块级结构不可分；v144 `_on_ext` 单块限定恰在 D1（单块守
  卫无延伸）放行误前置。唯一结构区分=回边复核（D1 环内无 a 副本；
  na5/E2 环内有全员副本）。
- **第二层泄漏**（生成侧）：前置修复后 E1 条件正确但 body 出现
  `if i < 10: break` 幻影——自循环提取器 `_is_compound_loop_cond` 链走
  查（header 落空链 72→94→110→126）在块 110（POPJB 后向 or 腿）处
  break（原判据只认 FORWARD 中间段），未达回边块 126 → 重检尾被判
  if-break。NA5 对照实证不触发（回边块 112 是 header 直接后继，走查一
  步即达）。

## 2. 修复（[v145-ORNEST2]，只增不破，双文件 +142/−51）

`region_analyzer.py`（v144 前置逻辑整段一般化）：
1. or 闭合收尾：单块 `_on_head`/`_on_ext` → 整段回溯收集（16 上限）+
   回边复核贪心副本匹配门控；未过门控逐位返回 v143 闭合链。
2. 前置后 or 成员统一记 'or'（B45 链约定，v144 语义保持）。

`region_ast_generator.py`（提取器链走查一处）：
3. `_is_compound_loop_cond` 链走查中间段判据补 BACKWARD→header 续链
   （fall-through 推进对前向/后向同形；visited+limit 32 既有）。

## 3. 验证（全实测）

- **矩阵 10 案**（matrix_v5r145.py，A/B 双文件交换 HEAD 3597cb33 vs
  v145）：E1 多块 and 头嵌套 HEAD TEXT-DIFF→v145 **BYTE-EQUAL PASS**+
  E2 守卫误触发（v144 既有回归）HEAD TEXT-DIFF→v145 **BYTE-EQUAL
  PASS**+C1 na5/C2 r143 or 链/C3 r142 and 链/C4 r141 自环/C5 r139 自环
  体回归防护零漂移 PASS+P1 守卫嵌套/P2 扁平 and-or/P3 守卫多块 or
  head 与 v145 逐字节同预存在零触碰=**MATRIX ALL PASS**（2 功效+5 控
  制+3 预存在）。
- **A/B 电池 267 案**（r145_regress.py 双文件版）：**TEXT-DIFF 0/267**
  全语料零漂移（v145 与 HEAD 产品逐字节同）；R110 169 案 TEXT 一致
  168/签名一致 167（唯一变化=na5 改进，r143/r144 既有改善的 A/B 口径
  归一：v145==v144 输出）；REG-10 其余 9 案 ALL SAME-SIGNATURE（含
  SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（基线一致，冻结
  对 B01/BOUNDARY_02）。
- **REAL46 判官**：difflib 56/62（90.32%）维持（余 6 差单元同清单）；
  REAL46 全量 sweep 豁免（小修口径）。不宣称 G1/G2c/G3/G4/G6 通过；
  product_complete 仍 NOT PASS。

## 4. 验收口径

实测读数同 §3：E1/E2（真实 R1 越界崩溃 + v144 守卫误触发）双闭合、
C1-C5 域零回退、电池 267 案零漂移、pytest 冻结对基线一致、difflib
56/62 维持。

## 5. 剩余登记（下一轮候选）

1. **扁平 and-or 族**（`while i < 5 and b[i] or c[i]:` 守卫 if+or-while
   碎片，假边目标不同，head==v145 逐字节同本轮登记）；**守卫+嵌套族**
   （`if a: while b and (c or d):` → `if a and b: while c or d:` 守卫
   外提，同上登记）；difflib 其余 6 差单元（get_grouped_opcodes/
   get_close_matches/_fancy_replace/_mdiff×2/_line_wrapper）；REAL46-014
   tarfile（142/160）/016 urllib.request（185/194）；REAL46-013 cookiejar
   91/105、015 subprocess 68/78 余差；4 compile_error；pytest 余 2 冻结
   对（登记态）。
2. **REG-10 口径**：na5 维持 BYTE-EQUAL 改进态（r143 起登记），后续电
   池 REGISTERED 名单可缩减（na5 移出、R110 比对行同步归一）。

## 6. 证据文件

`fix_patch_v5r145.diff`（双文件 +142/−51）、`matrix_v5r145.py`+result、
`r145_regress.py`+result、`difflib_judge_v145.txt`、本文件；中间件
D:/temp/opencode/cl_layout/r145diag、r145matrix、r145regress 不入库。
