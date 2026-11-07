# FINDING — rr-v5r130 [v130-EXCASSERT/ASSERTNOT]：except 处理器内 assert 还原（REAL46-011 statistics 首战 +5 单元）

## 0. 结论速览

- REAL46-011~016 DIFFERENT 族（§55.5 登记首选）本轮首战 REAL46-011
  statistics：判官 6 差函数中 3 个（`_exact_ratio`/`_sum`/`_ss`）同属
  **except 处理器内 assert 族**——两个缺陷位点：
  1. **[v130-EXCASSERT]** handler 臂区域派发白名单
     `(LoopRegion, IfRegion, WithRegion, TernaryRegion, BoolOpRegion)`
     **漏 AssertRegion**——条件块落入指令级重建被物化为
     `if COND: raise AssertionError else: <后续>`+幻影 `return None`；
  2. **[v130-ASSERTNOT]** `_generate_assert` 主路径无极性处理——`assert
     not X`（not 不可折叠进比较：调用/属性形实测）编译为
     `POP_JUMP_FORWARD_IF_FALSE→L_ok`，旧主路径只按 IF_TRUE 极性重建，
     not 被静默丢弃 → `assert not _isfinite(x)` 渲染为
     `assert _isfinite(x)`（**语义反转 R1 级**）。
- 修复后：statistics 判官 **71/77→74/77（92.21%→96.10%）**；REAL46-013
  cookiejar 90→91、REAL46-015 subprocess 67→68（**合计 +5 单元**）；
  difflib/tarfile/urllib.request 不变（他族另登记）。
- 判别器健全性：`LOAD_ASSERTION_ERROR` 仅 assert 语句编译产出（用户手写
  `raise AssertionError` 必为 `LOAD_GLOBAL`）——AssertRegion 识别不含
  手写形，矩阵 C1 实证零漂移。

## 1. 根因（三层追踪）

- 复现（repro2 = statistics._exact_ratio 精确形）：try/except 臂内
  `assert not _isfinite(x)` + 后续 `return (x, None)`。HEAD 产物：
  `if _isfinite(x): raise AssertionError else: return (x, None)` +
  幻影 `return None`；重编译 `LOAD_GLOBAL AssertionError` vs 原始
  `LOAD_ASSERTION_ERROR`（字节不等）。
- 区域树实证：分析层**已正确识别 AssertRegion**（entry=76
  blocks=[76,100]）；trace 插桩显示 handler 臂生成调用
  `_generate_block_statements(100)/(104)` 而非 `_generate_assert`——
  `_generate_try` 处理器体走查的区域派发白名单（39161 位点）不含
  AssertRegion，条件块经 CJB 物化为 if/else。
- 极性层：白名单补位后产物 `assert _isfinite(x)`（not 丢失）——
  `_generate_assert` 主路径重建条件时不读块尾跳转极性；BoolOp or 链
  分支另有 not 检测（jump TRUE→message_block）、NONE_CHECK 由
  `_invert_assert_none_check_direction` 按块内跳转语义互换，唯独主路径
  直落形的 IF_FALSE 极性无处理。
- 幻影 `return None`：重编译器死代码消除（if/else 双臂均出口后不可达），
  非字节差异源；assert 归位后自然消失。

## 2. 修复（[v130-EXCASSERT]+[v130-ASSERTNOT]，只增不破，单文件 +40/−1）

1. **[v130-EXCASSERT]**（`_generate_try` 处理器体走查派发白名单）：
   `isinstance(_hb_region, (...BoolOpRegion))` → 补 `AssertRegion`——
   `_generate_region→_generate_assert` 发射 ast.Assert（LAE/RAISE 基础
   设施由重编译自然再生），失败块由其 generated 登记消化，assert 跳转
   目标块（后续语句）照常由走查发射。
2. **[v130-ASSERTNOT]**（`_generate_assert` 主路径）：重建后读
   condition_block 尾条件跳转极性——opname 含 `FALSE`（FORWARD 条件跳
   转；NONE_CHECK 名不含 FALSE 不受扰）→ 条件包 `UnaryOp not`。可达
   性：主路径此处必为单表达式直落形（链式比较/BoolOp 链分支已先行返回）。
3. `while True: break` 特例、B135 无 else 形、BoolOp or 链检测全部不变
   （矩阵 C2-C4 零漂移实证）。

## 3. 验证（全实测）

- **矩阵 8 案**（matrix_v5r130.py，A/B 单文件 RAG 交换 HEAD 473ac054
  vs v130）：E1 assert not X+后续 return（statistics._exact_ratio 精确
  形）/E2 assert X 极性/E3 assert 末语句/E4 assert 带消息——4 功效案
  HEAD TEXT-DIFF→v130 **BYTE-EQUAL PASS**；C1 手写 if+raise（判别器健
  全性，绝不可变 assert）+C2 非 handler 域+C3 普通体+C4 try 体全零漂
  移。**MATRIX: ALL PASS**。
- **REAL46 判官触达**：statistics 71/77→**74/77**（+3）；cookiejar
  90/105→**91/105**（+1）；subprocess 67/78→**68/78**（+1）；difflib/
  tarfile/urllib.request 不变（他族）。
- **A/B 电池 267 案**（r130_regress.py，单文件 RAG 交换 HEAD 473ac054
  vs v130）：**TEXT-DIFF 0/267**（全语料零漂移——白名单补位仅在分析层
  已识别 AssertRegion 的 handler 臂生效+极性规则仅 IF_FALSE 形触发，
  267 语料零触发=外科性）；R110 168/169 一致（mc1 正常归一）；登记差
  10 案 **ALL SAME-SIGNATURE**（含 SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项一致，
  余 2 失败=冻结对 B01/BOUNDARY_02）。
- **REAL46 全量 sweep 豁免（小修口径）**：本轮触达面已由 6 个目标案
  （REAL46-011~016）新鲜判官读数直接覆盖（§0/§3 的 +5 单元=权威
  semantic_diff 判定）；其余 40 案回归面由电池 267 案零漂移+矩阵 4 控
  制案兜底。

## 4. 验收口径

实测读数同 §3：statistics 71/77→74/77（92.21%→96.10%）、cookiejar
90→91、subprocess 67→68（REAL46-011/013/015 三案 +5 单元，方向=修
复）；电池 267 案 TEXT-DIFF 0；pytest 冻结对基线一致。不宣称
G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. REAL46-011 余 3 差单元（harmonic_mean 控制流/NormalDist.samples×2）
   他族未定；REAL46-012 difflib（53/62）/014 tarfile（142/160）/016
   urllib.request（185/194）未触达族；4 compile_error；pytest 余 2 冻
   结对（登记态）。

## 6. 证据文件

`fix_patch_v5r130.diff`（+40/−1 单文件）、`matrix_v5r130.py`+result、
`product_HEAD_repro2.py`/`product_v130_repro2.py`（最小复现双态产物）、
`r130_regress.py`+result、本文件；中间件
D:/temp/opencode/cl_layout/r130diag、r130matrix、r130regress 不入库。
