# FINDING — rr-v5r144 [v144-ORNEST]：while and+(or) 嵌套链闭合（or 闭合前置 and 头 + 守卫 IfRegion 让位，na5 登记差案自 R110 起首次 BYTE-EQUAL）

## 0. 结论速览

- 69.5 首选 na5 if 包装族残差定位：na5 真源码 = `while i < len(items)
  and (items[i] or opt):`（R7-B45 嵌套链 and 头 + 括号 or 尾）。v143 渲
  染 `if i < len(items): while items[i] or opt:`——**and 头被外提为守卫
  if 只查一次**，循环内 i 递增后 `items[i]` 越界（IndexError）=**真实
  R1**；且 or 尾独立成链（v143 or 闭合判据抢跑）短路了嵌套检测器
  `_detect_while_condition_nested_and_or_chain`（探针实证 NESTED 零调
  用、BOOLOP 返回 [(44,'or'),(60,'and')] 尾 run）。
- [v144-ORNEST] 单文件 +84/−0（只增不破）：
  1. or 闭合判据前置 and 头——链首 fall-through 前驱以 FORWARD FALSE
     族收尾、假边目标==本链假出口（越过整个 or run=R7-B45 结构特征）、
     落空续接链首、非体语义成员 ⇒ 前置 (and 头,'and') 成完整嵌套链
     （与嵌套检测器装配同形）；**单块限定**：and 头自身前驱还有同假出
     口 FALSE 成员（多块 and 链）时不前置（E2 实测三操作数 and 头单块
     前置后链畸形循环体蒸发，多块族另行登记）；or 成员统一记 'or'
     （B45 链约定，按极性记 'and' 会被扁平重结合为 `A and B or C`——
     首跑实证）。
  2. B6 让位扩展：守卫 IfRegion（块集 ⊆ 链块集，type is IfRegion 精
     确判定）让位——and 头此前被外提守卫 if 认领（blocks=[and 头 ∪
     链首]，then=循环入口）；子区域（循环）不属其 blocks，撤销不触及
     循环本体。
- 真函数复判：**na5 byte_equal=True（R110 起登记差案首次全闭合）**；
  渲染与源码逐字同（嵌套括号保留）；r143/r142/r141/r139/r140 回归防
  护 byte_equal 维持；difflib 判官 56/62 维持。

## 1. 根因（三层追踪）

- 残差定位：na5 orig 136 vs v143 prod 98、首差字节 43——对齐 diff+
  源码读取（`fresh/andortail_cond/na5.py`）实证 and 头外提。
- 结构探针：区域树 LoopRegion@44 condition=44 + BoolOpRegion@44
  blocks=[44,60,112,128] + **IfRegion@0 condition=0 blocks=[0,44]
  then=[44]**（守卫 if 认领 and 头块 0）。
- 链探针：BOOLOP cond@44 → [(44,'or'),(60,'and')]（v143 闭合抢跑），
  NESTED 零调用。

## 2. 修复（[v144-ORNEST]，只增不破，单文件 +84/−0）

`region_analyzer.py` 两处：
1. `_detect_while_boolop_forward_chain` or 闭合内：and 头前置（检测+
   单块限定+or 成员重标签 'or'）；
2. B6 所有权校验：守卫 IfRegion 让位（块集 ⊆ 链块集）。

## 3. 验证（全实测）

- **矩阵 7 案**（matrix_v5r144.py，A/B 单文件交换 HEAD d0ab6e94 vs
  v144）：E1 na5 精确形 HEAD TEXT-DIFF→v144 **BYTE-EQUAL PASS**；
  C1 r143 or 链/C2 r142 and 链/C4 r141 自环 B234/C5 r139 自环体回归
  防护零漂移 PASS；E2 多块 and 头嵌套链/C3 扁平 and-or 实测 head 与
  v144 输出逐字节同=预存在排除判定（单块前置限定后 E2 回到 head 行
  为；两族登记下轮）。**MATRIX: ALL PASS**（1 功效+4 控制+2 预存在）。
- **真函数复判**：na5 重编译 **byte_equal=True**；r143 C2/r142
  repro1/r141 repro2/r139/r140 chain1 回归防护 byte_equal 维持；
  difflib units DIFF 6/60 维持。
- **A/B 电池 267 案**（r144_regress.py 双文件版）：TEXT-DIFF 1/267=
  **na5（TEXT-DIFF + BYTE-EQUAL——登记差案闭合形态）**，其余 266 零
  漂移；R110 169 案 TEXT 一致 167/签名一致 167（唯一变化=na5 改进）；
  REG-10 其余 9 案 ALL SAME-SIGNATURE（含 SUBST-SIG pd8_prod）；
  NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（基线一致，冻结
  对 B01/BOUNDARY_02）。
- **REAL46 判官**：difflib 56/62（90.32%）维持；REAL46 全量 sweep 豁
  免（小修口径）。

## 4. 验收口径

实测读数同 §3：na5（真实 R1 越界崩溃）闭合、E1 重编译 BYTE-EQUAL、
r143-r139 域零回退；电池 267 案 1 处=na5 闭合（其余 266 零漂移）；
pytest 冻结对基线一致；difflib 56/62 维持。不宣称 G1/G2c/G3/G4/G6
通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **多块 and 头嵌套链**（E2 形 `while i < 10 and a[i] and (b[i] or
   f(i)):`——and 头两操作数，单块前置限定后回退 head 行为，通用混合链
   装配待独立轮）；**扁平 and-or 族**（C3 形 `while i < 5 and b[i] or
   c[i]:` 守卫 if+or-while 碎片，假边目标不同的另一族）；difflib 其余
   6 差单元（get_grouped_opcodes/get_close_matches/_fancy_replace/
   _mdiff×2/_line_wrapper）；REAL46-014 tarfile（142/160）/016
   urllib.request（185/194）；REAL46-013 cookiejar 91/105、015
   subprocess 68/78 余差；4 compile_error；pytest 余 2 冻结对（登记态）。
2. **REG-10 口径更新**：na5 自本轮起=BYTE-EQUAL（自 R110 登记以来首
   次全闭合），后续轮电池 REGISTERED 名单可缩减（na5 移出）。

## 6. 证据文件

`fix_patch_v5r144.diff`（+60 单文件）、`matrix_v5r144.py`+result、
`r144_regress.py`+result、`difflib_judge_v144.txt`、本文件；中间件
D:/temp/opencode/cl_layout/r141diag、r144matrix、r144regress 不入库。
