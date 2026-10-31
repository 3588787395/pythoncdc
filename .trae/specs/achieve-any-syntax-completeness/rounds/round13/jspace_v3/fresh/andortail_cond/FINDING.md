# ANDORTAIL：正极性 if 条件嵌套 or 尾重建修复（rr-v5r106，Task 32，nb2 平铺形闭合）

## 家族选定与根因

rr-v5r105 剩余登记选 nb2 平铺形（or 链检测域；pe8 while-1 重构族按其诊断
注记需派发表先行、维持登记；46 sweep 14 DIFFERENT 留作后备）。

根因（区域树转储 + 逐消费者插桩 + 产品 A/B）：`return`/`if` 语境的
`A and B and C and (D or E)`——嵌套 or 尾的平坦 op_chain 为
[(A,'and'),(B,'and'),(C,'and'),(D,'or'),(E,'and')]：嵌套 or 首位成员 D 以
TRUE 极性收尾（D 真 ⇒ `(D or E)` 真 ⇒ 整链真，PJT 直达 then 块 270/真出
口）、末位成员 E 以 FALSE 极性收尾（E 假 ⇒ 整链假，PJF 直达 merge 274/假
出口，其 fall-through 后继即真出口）。`_build_boolop_expression_inner` 的
既有 `_try_build_and_inner_or_pattern`（`a and (b or c)` 检测器）条件 3
要求「边界后全为 'or'」——本形态在边界检查即被拒（E 标注 'and'）→ 落入
or_groups 平坦化 → 产品 `A and B and C and D or E`（优先级破坏，
`(A and B and C and D) or E` 语义错误）。

判别器密闭性：真平坦混链 `A and B or E` 的 and 前缀假边指向 E 块（or 的
右操作数求值起点）≠ merge——本变体要求 and 前缀全员 IF_FALSE → merge，
二者互斥（na7/na8 控制实证）。na2/na3/na6/na9 同族形态由更早的既有路径
（[B98] 尾值边界 / V3R2 / skipedge / 显式分组）接住而绿——本修复不触及
（C3 实证）。

## 修复（region_ast_generator 只增不破，[v106-ANDORTAIL]，+125 行）

`_try_build_and_inner_or_pattern` 首段（条件 3 之前）插入新检测器
`_try_build_and_inner_or_positive_tail`，七重守卫全同层结构事实：①链形状
= and×p (p≥1) + or×q (q≥1) + 末 and×1；②末成员（嵌套 or 的末位操作数）
FALSE 极性 → merge 且后继恰为 {merge, T} 两条非异常边（T = fall-through
≠ merge）；③and 前缀全员 IF_FALSE → merge；④嵌套 or 组全员 TRUE 极性 →
同一真出口 T；⑤LoopRegion 父守卫（循环条件嵌套 or 尾涉及 while 重构域
——na5 实测其 collapse 属 loop 重构域，留既有/后续路径）；⑥操作数由
`_reconstruct_boolop_operand` 逐块重建（任一 None 即退回）；⑦重建
and([...and 操作数..., Or([...or 操作数...])])。修复过程实证：首版
or_blocks 只收 'or' 标注段、末位成员 E 被丢成 and 第 4 操作数（产品
`A and B and C and D`，E 蒸发）——修正为 or 组 = 'or' 标注段 + 末位成员
（其 FALSE→merge + fall-through==T 已由②③校验承载）。

## 验证（全实测）

- 复现矩阵：功效案 **nb2**（v105 DIFF→v106 重编译全 code object 逐字段
  BYTE-EQUAL，产品 `A and B and C and (D or E)` 括号正确恢复）；控制案
  **14** 零变化——C3：na2/na3/na6/na9（同族但由更早既有路径接住的绿形）、
  na7/na8（真平坦混链 `A and B or E`，or_groups 既有正确路径）、nb1/nb3
  （值语境/4 成员形）、no1/no2/no4/no5/no8/no9/no10（r100 ORTAIL 族）。
  既有登记 na5（while 条件嵌套 or 尾——loop 重构域）产品 v105/v106 逐字
  节相同（LoopRegion 父守卫）。
- 回归电池 **120 案**（r106_regress.py 双文件交换 A/B：v5r105 HEAD=dc9fd5d5
  vs v106 同输入 pyc 反编译产物逐字节比对 + 逐顶层函数重编译比对）：
  **1 功效案（nb2）TEXT-DIFF/BYTE-EQUAL + 119 TEXT-SAME**（23 原案含 w28
  w2/w3 v97 既有同态 + 全部控制案）；既有登记差维持与 v104 逐字节同签名
  （w28 w2/w3、na5、pe8、pe8_target）。
- pytest 7 套件 **冻结对一致 2 failed**（TestDominanceFrontierIf::test_B01
  _simple_if_then_else_merge、TestBoundaryConditions::test_BOUNDARY_02
  _large_function）/ 277 passed / 2 xpassed；第 3 failed = product_freshness
  在位产物预存在陈旧（A/B 实证 INPLACE≠v104 且 v106==v104 逐字节，非本轮
  引入）；比较器 pyc_verify.py SHA256 FE1902A9 冻结一致、tests/ 零改动。
- REAL46-004（enum.cpython-311.pyc sha 60e3ca30）单案权威 semantic_diff
  复跑 **EQUAL**（verdicts={'EQUAL': 1}）；产品与 v104 逐字节相同（行尾
  规范化后）。
- 全量 1556 闸门（v5r106 三分片对 v5r89 基线）**0 回归**：EQUAL 1180=1180、
  ERROR 376=376；对 v105 逐案 c4 verdict 唯一变化 JS-WHILE-045 None→ERROR
  （上轮 NO_C4 并发抖动案本轮恢复基线值 ERROR——已登记超时抖动族
  （r96 轮 7 案、r100 轮 JS-LISTCOMP-004 同族），连续第六轮零实质抖动）；
  分片汇总 shard0 367/152、shard1 406/113、shard2 407/111（与 v104/v105
  基线逐分片一致）。
- REAL46 sweep（v5r106 对 v5r105）**45 案 c4 逐案零变化 0 回归**：14
  DIFFERENT/14 EQUAL/17 ERROR+skip1（c2_pyc_missing=已登记 REAL46-045）；
  REAL46-004 维持 EQUAL。

## 诚实边界

- nb2 平铺形闭合；na5（while 条件嵌套 or 尾 → loop 重构 collapse）为同域
  观察、本轮不修（LoopRegion 父守卫排除），维持登记。
- pe8（while-1 重构族，需派发表先行）、46 sweep 14 DIFFERENT/17 ERROR 在案。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r106.diff` | [v106-ANDORTAIL] 完整 diff（+125 行） |
| `nb2.py`/`nb2_out.py`/`nb2.pbpyc` | 复现 + v106 产品（括号正确恢复）+ 原件字节码 |
| `na2/na3/na6/na9.py` | 同族控制（更早路径接住的绿形，C3） |
| `na7/na8.py` | 真平坦混链控制（or_groups 既有路径，判别器互斥实证） |
| `nb1/nb3.py` | 值语境/4 成员控制 |
| `na5.py` | 同域观察（loop 重构域，登记不变） |
| `matrix_v106_baseline.txt` | v105 基线 + 修复后矩阵读数 |
| `r106_regress.py`/`r106_regress_result.txt` | 120 案回归电池驱动与结果 |
