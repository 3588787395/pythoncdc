# FINDING — rr-v5r128 [v128-NBEUPD]：NONE_CHECK 旋转 while 环底更新语句丢失修复（真实 R1：循环不前进）——v118 E2 残差闭合

## 0. 结论速览

- v118 E2 残余（§53.5 登记首选）**修复并升级闭合**：`while tok is not
  None:` 旋转 while 的环底更新语句 `tok = next(it, None)` 曾整条丢失
  （产物循环永不前进=**真实 R1 死循环语义**，非纯字节差）——缺陷位点 =
  `_loop_find_cond_start_idx` 的 NONE_CHECK 扩展回溯把真实赋值 STORE 吞
  进条件求值段（walrus 形专设），`_nbe_cond_start_idx=0` →
  `_loop_process_natural_back_edge` 前置语句零提取、整块静默抑制。
  [v128-NBEUPD] 单文件 +18/−0（无 COPY 1 前驱的 STORE 停回溯=语句边界）。
- 修复后：repro 重编译**全字段 BYTE-EQUAL**；电池 267 案唯一
  TEXT-DIFF=登记语料案 `E2_andnot_while_gen`（HEAD 丢更新→v128 归位，
  签名 DIFF→**BYTE-EQUAL**，方向=修复）——该案即 v118 E2 家族本尊。
- 全额闸门：电池 267 案 **TEXT-DIFF 1/267（唯一差=功效方向）**；R110
  168/169 一致（mc1 正常归一）；登记差 10 案 **ALL SAME-SIGNATURE**；
  NO-SRC 0；pytest 7 套件 **2 failed/282 passed/2 xpassed（基线一致）**；
  矩阵 6 案 **ALL PASS**；REAL46 sweep A/B 见 §4。

## 1. 根因（三层追踪）

- 复现（e2.pyc，v118 E2 同源）：旋转 while 环底块@128 =
  `[LOAD_GLOBAL next, CALL, STORE_FAST tok, LOAD_FAST tok,
  POP_JUMP_BACKWARD_IF_NOT_NONE 72]`（更新+底部重检，∈body_blocks），
  产物 140 字节 vs 原始 172（while 只剩顶部测试，更新语句丢失）。
- 追踪：region 树 LoopRegion back_edge_block=128；trace-set 实证唯一
  标记点 = `_loop_process_natural_back_edge`（17175）。`_nbe_has_store`
  命中后依赖 `_loop_find_cond_start_idx` 切点提取前置语句。
- 根因：块尾 `POP_JUMP_BACKWARD_IF_NOT_NONE` ∈ NONE_CHECK_OPS → 走
  **walrus 扩展回溯**（`_none_check_extended_ops` 含 STORE_*，为
  `(x := next(it, None))` 形专设）；回溯从跳转位向下把 `STORE_FAST
  tok`(158) 连同整个 `tok = next(it, None)` 求值段一起消费 → 切点=0 →
  `> 0` 不成立 → 零提取 + 整块标记 generated = 静默吞语句。
- 对照辨析：`n -= 1` 形（尾指令 `POP_JUMP_BACKWARD_IF_FALSE`，走
  COMPARE_OP 分支，STORE 不在其扩展集）正常提取——这正是该族只炸
  `is (not) None` 旋转 while 的精确边界。兄弟形态（E2_is_none 简形体/
  多语句更新）实测 HEAD 本已正确（走 R21-66 闩锁通道等其它提取路径），
  缺陷面=该复合形（内含 if/elif/else + yield 臂）独占 natural_back_edge
  提取路径。

## 2. 修复（[v128-NBEUPD]，只增不破，单文件 +18/−0）

`_loop_find_cond_start_idx` NONE_CHECK 扩展回溯循环内新增 STORE 语句
边界判别：遇 STORE_* 且其前驱**不是 COPY arg=1**（非 walrus 对）即停止
回溯——切点保持已消费的 LOAD 位（E2 实测 160 位 `LOAD_FAST tok`），其
前的 STORE 及求值段划回前置体语句（`tok = next(it, None)` 重生）。

- 判别式健全性（栈语义）：walrus 对 `COPY 1; STORE x` 的值经 COPY 留
  栈供 NONE_CHECK 跳转直取；无 COPY 前驱的 STORE 后值已出栈，跳转直取
  必栈下溢不可能成立——故该 STORE 必为语句终结符。
- walrus 对（COPY 1 前驱）维持原消费路径逐位不变（B105 C3）；其余两个
  调用点（R43-D2 纯重检位/with_condition 位）块内无 STORE，不受影响。

## 3. 验证（全实测）

- **repro（e2）**：产物环底更新归位（缩进 8=体末语句），重编译
  **w + module 全字段 BYTE-EQUAL**（172=172）。
- **A/B 电池 267 案**（r128_regress.py，单文件 RAG 交换 HEAD 23c0b6b7
  vs v128）：**TEXT-DIFF 1/267 = `E2_andnot_while_gen`（V118 登记案，
  HEAD 丢更新→v128 归位，签名 DIFF→BYTE-EQUAL 方向=修复）**；R110
  168/169 一致（mc1 正常归一）；登记差 10 案 ALL SAME-SIGNATURE（含
  SUBST-SIG pd8_prod）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与基线逐项
  一致，余 2 失败=冻结对 B01/BOUNDARY_02）。
- **变体矩阵 6 案**（matrix_v5r128.py，A/B 单文件交换）：E1_e2_shape
  HEAD TEXT-DIFF→v128 BYTE-EQUAL **PASS**；E2_is_none 变体/E4 多语句
  更新实测 HEAD 本已正确（归控制零漂移）；E3 walrus 对照（B105 路径
  维持）/C1 `n-=1` 对照/C2 truthy 对照全零漂移 BYTE-EQUAL。
  **MATRIX: ALL PASS**。
- **REAL46 sweep 46 案 A/B**（v128/HEAD 双侧新鲜产物 --source）：§4 读数。

## 4. 验收口径与 sweep 读数

REAL46 sweep A/B：46 案读数**逐字节一致**（双侧结果文件 diff-exit=0
实证；head 侧与 r127 head 侧亦逐字节一致=真包零漂移基线稳定）——
NBEUPD 修复在 46 真实包零触发（该复合形未被真包命中，闭合面=合成域
+电池 V118 登记案）；ElementPath 维持 **39/39 100%**。分布：15 success
+ 27 failure + 4 compile_error（与基线一致，failure=REAL46-011~016
在案族）。不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. E6 相邻 NOP 对；46 sweep 其余 DIFFERENT（REAL46-011~016）/
   4 compile_error；pytest 余 2 失败 = 冻结对（B01/B02，登记态）。

## 6. 证据文件

`fix_patch_v5r128.diff`（+18 单文件）、`repro_e2.py`/
`product_HEAD_e2.py`/`product_v128_e2.py`（最小复现双态产物）、
`matrix_v5r128.py`+result、`r128_regress.py`+result、本文件；中间件
D:/temp/opencode/cl_layout/r128diag、r128matrix、r128regress（sweep 双
侧）不入库。
