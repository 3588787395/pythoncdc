# FINDING — rr-v5r118 [v118-ANDNOT]：生成器循环体内 `elif A and not B:` 复合条件拆嵌套 IfRegion、else 臂错挂丢失（REAL46-008 叶 1 闭合 3→2）

## 0. 结论速览

- REAL46-008（xml/etree/ElementPath）判官 R7 **3→2**：`/xpath_tokenizer` 闭合
  （co_code 410 vs 410 等长异字节 → 全等），剩余 `/prepare_predicate`（+10
  字节）与 `/iterfind`（−102 字节）两叶均为 **while-1/store-recheck 重构族**
  （pe8 同域，r105 两版窄修复失败在案，本轮不动）。
- 本族是**真实 R1 语义缺陷**：`elif default_namespace and not parsing_attribute:`
  的 else 臂 `yield token` 在 `ns` 真且 `pa` 真的路径上**整臂丢失**（产品反极性
  真边直达 merge、两个 yield 都不执行；原件 else 臂 yield token 照常执行）。
- 家族面：**生成器与非生成器同塌缩**（矩阵 C3/E4 实证）；单层（无外层 if 壳）
  或无 for/while 壳时不塌缩（r1/r2 实证）。

## 1. 根因（区域树对照 r2 绿形/r3 病形 + B1b 门与 IfExp 守卫双插桩 + 行级追踪）

### 1.1 差异面

原件（ElementPath.xpath_tokenizer，elif 形）与产品（嵌套 if 形）字节码**几乎
全同**，唯二差异：①@342 `POP_JUMP_FORWARD_IF_TRUE` 目标 370（else 臂）vs
368（JUMP_FORWARD 跳空）；②@340 `LOAD_FAST parsing_attribute` 行锚 None
（原件）vs line=22（产品）。产品把 `elif ns and not pa:` 渲染为
`if ns: if not pa: <yield1>`（内层无 else）+ 外层 `else: <yield2>`——ns 真且
pa 真时两个 yield 全丢。

### 1.2 机制链（双断点）

- 区域树：r3 病形里 elif 条件 `ns and not pa` 的两个测试块（68: LOAD ns+PJF；
  72: LOAD pa+PJT 反极性）**未形成 BoolOpRegion**，被拆成 IfRegion@68 与
  IfRegion@72，链条 else 臂（90）挂在 @68 的 else；r2 绿形（无循环壳）同形
  块形成 BoolOpRegion(entry, blocks=[测试块×2])、链条 elif_conds=1。
- 断点一（准入）：循环体内候选块被 LoopRegion 认领 → 链 walk 走
  skip_claimed_check=True 路径，候选准入交 `_b1b_loop_body_run_continuation`
  三分类判据（and→or 边界/or-run 续接/and-run 续接 + TRUE/TRUE 同目标分判）。
  本形（current FALSE 族 + candidate TRUE 族共享同一失败出口）不属任何一类 →
  break，链长 1 → DT 返回 None（probe_b1b 实证 (68,72,False)）。无循环路径
  （skip=False、candidate 未认领）同形直接入链——差异只在认领守卫。
- 断点二（IfExp 值块守卫）：准入修复后链 walk 第二迭代仍断——IfExp 真值块
  守卫（fall-through 块以 JUMP_FORWARD 收尾且「无语句指令」时判 IfExp 值块
  → 断链）把臂体块 76（`yield ('n', ns)` + 臂尾 JUMP_FORWARD 越过 else 臂）
  误判为 IfExp 值块：**YIELD_VALUE 不在语句指令清单**（STORE/RETURN/RAISE/
  DELETE 系），块含值指令又不满 B1b fix-r2 纯控制豁免 → 维持 break
  （行级追踪实证 34117 break → 34824 len(chain)<2 return None）。
- 行锚判别器（两源文形字节码同形、唯行锚可分）：elif-and 尾操作数块是同一
  行级测试的编译器续行产物，块首非噪声指令 starts_line=None（原件 block@340
  与 r3 复现 block@72 实测）；嵌套 if 形内层测试块首指令必带内层语句行锚
  （产品编译实测 line=22）。

### 1.3 同域排除

- while 复合条件闩锁吸收域（v117-ELIFTEST）不动；本形是 for/while **体内**
  if 链的 BoolOp 装配，与闩锁重检无关。
- r4 普通循环内 `if a and b:`（候选 FALSE 族）走既有路径不变（C2 零漂移）；
  裸 yield 作 IfExp 值（无 POP_TOP）维持断链不变（C4 零漂移）。

## 2. 修复（region_analyzer.py 只增不破，[v118-ANDNOT] 三 hunk +63/−3）

1. `_b1b_loop_body_run_continuation` case (1) 增设 (1b)：current FALSE 族 +
   candidate TRUE 族 + `_cand_tgt is _cur_tgt`（双边共享失败出口）+ 候选块首
   非噪声指令无行锚 → 放行入链（`A and not B` 标准降级形）；不命中维持原
   break。原 `return (A∧X)∨(A∧Y)` 重构为 `if A: return X∨Y`（语义等价）。
2. IfExp 真值块守卫：块内 YIELD_VALUE 后（隔噪声）跟 POP_TOP ⇒ yield 表达式
   语句 ⇒ 语句块非值块（真 IfExp 值块内 YIELD 后不可能 POP_TOP——值必须
   留栈进 merge；裸 yield 作 IfExp 值时无 POP_TOP）。
3. 新增 `_boolop_cand_head_unanchored` 辅助（行锚判别器，噪声集与本文件既判
   一致 RESUME/NOP/CACHE/EXTENDED_ARG）。

## 3. 验证（全实测）

### 3.1 变体矩阵（`matrix_v5r118.py` 7 案，A/B HEAD `85982510` vs v118）

| 案 | 形 | HEAD | v118 | 判定 |
|---|---|---|---|---|
| E1_andnot_for_gen | for + 嵌套链 + elif-and + 链尾语句（r3 形） | TEXT-DIFF（elif→嵌套 if 塌缩） | 重编译 BYTE-EQUAL | PASS |
| E3_andnot_nochainstmt | for + 链无尾语句变体 | TEXT-DIFF | BYTE-EQUAL | PASS |
| C3_andnot_nongen | 非生成器同构（赋值臂） | TEXT-DIFF（**同塌缩**） | BYTE-EQUAL | PASS（实测同为功效案） |
| E2_andnot_while_gen | while 变体 | TEXT-DIFF | elif 臂恢复；重编译仍非等价 | PASS-PARTIAL（预存在残余，见 §5） |
| C1_andnot_noloop | 无循环 elif-and（r2 绿形） | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C2_plain_and_loop | 循环内普通 `if a and b:`（r4 绿形） | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C4_yield_ifexp_value | 裸 yield 作 IfExp 值（守卫须维持断链） | — | 逐字节同 | PASS（C3；重编译非等价为预存在 IfExp+yield 值族，HEAD 同非等价） |

### 3.2 REAL46-008（ElementPath）

- 字段级递归比对：差异 code objects **3→2**（`/xpath_tokenizer` 闭合；
  剩 `/prepare_predicate`、`/iterfind` 均 while-1/store-recheck 族）。
- 权威判官 `semantic_diff.compare_case`：R7 **3→2**
  （`semantic_REAL46-008_v118.json`，status 仍 DIFFERENT——余两叶未修）。
- r3 复现重编译 4 code objects 全字段 BYTE-EQUAL。

### 3.3 回归

- A/B 回归电池（r118_regress.py：r110 169 + v111 15 + v112 15 + v113 15 +
  v115 9 + v116 4 + v117 6 + 本轮 7 = **240 案**，独立 TMP `r118regress/`
  干净重跑；本轮交换文件 = `core/cfg/region_analyzer.py`）：**TEXT-DIFF 4 /
  240 恰为本轮 4 功效案**（E1/E3/C3-nongen 重编译 BYTE-EQUAL；E2 elif 臂
  恢复、残余为预存在 while 底部 store-recheck 族且 HEAD 同非等价）；其余
  236 案 TEXT-SAME；R110 案 168/169 一致（唯一差 mc1 = r110 轮功效案两侧
  同持修复正常归一，TEXT-SAME+BYTE-EQUAL）；既有登记差 10 案 **ALL
  SAME-SIGNATURE**；NO-SRC 0。
- pytest 7 套件：**3 failed / 277 passed / 2 xpassed**——与基线逐项一致
  （2 冻结对 + product_freshness 预存在陈旧），零新增失败。诚实登记：
  stale 条目中 `matcher.pyc` 的 current-code 侧变化 13462→13375（168→167
  行）——A/B 实证为**同族正确化**：原件该测试对 `PJF@800→2464` 与
  `PJT@2208→2464` 尾操作数块**无行锚**（原文即 `A and not B` 复合形），
  HEAD 渲染嵌套 `if A: if not B:`（错误形状），v118 恢复合合形；带行锚对
  （`PJT@1908` line=233，原文嵌套形）未被合并（判别器正确排除）；
  `match` 函数字段差异计数 HEAD=1 / V118=1 不变（单 code object 预存在
  差异，形状改正后字节距离 1642→1709、长度 4992→4988 更近 4968）；
  `trade_info_utils.pyc`（61506/61753）、`load_daily`（26229/26134）、
  `strategy_universe.pyc`（40 行 3787/3712，A/B 实证 3712=3712）零漂移。
- 比较器 pyc_verify.py FE1902A9 / semantic_diff.py DBCB1E24 冻结一致、
  tests/ 零改动；唯一已跟踪改动 `M core/cfg/region_analyzer.py`
  （+63/−3，标记 `[v118-ANDNOT]`）。

## 4. 验收口径

小测试收口（全量闸门按用户政策只留给大改动）。不宣称 G1/G2c/G3/G4/G6 通过；
product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选，未修）

- REAL46-008 余两叶 `/prepare_predicate`（+10 字节）/`/iterfind`（−102 字节）：
  **while-1/store-recheck 重构族**（pe8 同域，r105 两版窄修复失败在案「自然
  出口块前向吸收 → _is_while_true 判 True → site9k while-1 发射；需派发表
  先行」）；E2 残余同域（while 底部 `tok = next(it, None)` 重检链丢失）。
- E6 相邻 NOP 对；46 sweep 其余 DIFFERENT（REAL46-011/012/013/014/015/016，
  022/046 已定性观察层 R5）/17 ERROR。

## 6. 证据文件

`fix_patch_v5r118.diff`、`matrix_v5r118.py`、`r118_regress.py+result`、
`semantic_REAL46-008_v118.json`、`ElementPath_product_v118.py`、本文件；
探针与复现：`D:/temp/opencode/cl_layout/r118diag/`（r1-r5 复现系、
probe_r3.py/probe_r2.py 区域树对照、probe_chain.py DT/CR 追踪、
probe_b1b.py B1b 门插桩）、`D:/temp/opencode/cl_layout/r118matrix/`（矩阵
A/B 产物）。不入库。
