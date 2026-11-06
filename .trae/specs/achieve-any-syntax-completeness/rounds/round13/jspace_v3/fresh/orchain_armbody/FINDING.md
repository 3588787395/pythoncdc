# FINDING — rr-v5r121 [诊断登记轮] + rr-v5r122 [v122-ORCHAIN 实施轮]：or 链拆臂丢体（混合 or+and 嵌套链，真实 R1）——诊断闭环、两段式嵌套构造实施与全量验收

## 7. rr-v5r122 [v122-ORCHAIN]：两段式嵌套构造实施（Task 48，§47.3 登记路径）

### 7.1 实现（只增不破，两文件 +176/−4）

1. **吸收使能**（region_analyzer.py，R64 rejoin 扩展 +15）：后继条件块的
   **落空边**汇聚 T 亦算 rejoin——and 尾成员签名（or 链尾操作数的 and 组：
   续测块 PJT 落全链假出口、其落空边才是真出口 T）。R64 守卫对成员 26 不再
   误弹（`(A or B or (C or D) and not E):` 中 C 的真边指向 and 续测 S≠T）。
2. **嵌套重建器**（region_ast_generator.py `_build_orchain_andtail_grouped`
   +147）：准入判据全同层结构事实（块末 opcode 族 + argval 目标 + 链块集合
   成员 + region.merge_block）——外层 or 前缀成员 [0,j) 全员 PJT→同一 T
   （∉链）；内层 or 段 [j,m) 真边（跳转边或落空边）全汇聚 S=op_chain[m]
   （链上续测块）；内层末成员 PJF→merge（段失败=全链假出口）；尾成员
   PJT→merge 且落空边→T（否定 and 尾签名，`not E` 的编译形）。重建
   `or[前缀, and[or[内层段], not(尾)]]`，各成员表达式仍由各自块内指令重建
   （不挪块，唯一归属不变）。调用点：`_build_boolop_expression_inner` 的
   skipedge 重建之后、显式分组检测之前（`_detect_boolop_grouping` 对本形因
   「真跳目标∈链块」信号误判 outer='and' 并把内层段并入前缀组——实测产
   `and[or[A,B,C,D], E]`，故必须先手）。
3. **取反闩锁豁免**（两处）：IfRegion 条件闩锁与 elif 条件闩锁——末成员
   PJT→merge 触发「整体取反」闩锁，但本形极性已由嵌套重建器逐项携带（尾包
   not），整体取反会二次取反（实测 `not (a or b or (c or d) and not re)`）。
   R2-B108 混合极性判定器第 ③ 条明文排除链内目标（归属分组路径独占）且要求
   全员 'or' op（成员 38='and' 不符），不覆盖本形属设计使然，由 v122 谓词
   补位（豁免条件 = B108 命中 **或** v122 形命中）。

### 7.2 验证（全实测）

- **o1 最小复现**：`if sig == 'a' or sig == 'b' or ((sig == 'c' or
  sig == 'd') and not pred.isdigit()):` 完全还原（and 优先级无需括号），
  重编译全字段 **BYTE-EQUAL**（o1_out5.py）。
- **REAL46-008 /prepare_predicate**：1204=1204 **全字段 BYTE-EQUAL**
  （v120 后 +12 残余清零）；混合链臂 `elif signature == ".='" or
  signature == ".!='" or ((signature == "-='" or signature == "-!='") and
  not re.match(...))` 精确还原——`.='` 签名误 raise SyntaxError 病形闭合
  （真实 R1 消除）；`/iterfind` 858 vs 756 不属本族（while-1 体丢失族，
  登记未动）。
- **权威判官**（pyc_verify single，`--source` v122 新鲜产物）：REAL46-008
  **38/39 = 97.44%**（陈旧 OK.py 口径 35/39）——唯一失败单位 iterfind
  （R7 计数 2→1）。
- **变体矩阵 13 案**（matrix_v5r122.py，A/B 两文件交换 HEAD 02a529d3 vs
  v122）：3 功效案（E1 臂体带 return / E2 臂体不退出 / C11 while 域
  prepare_predicate 同构）HEAD TEXT-DIFF → v122 重编译 **BYTE-EQUAL**；
  10 控制案零漂移（C1 R65 直连 and 尾 / C2 显式分组 / C3 and-inner-or /
  C4 or-and-or / C5 纯链 / C6 keeppop / C7 skipedge / C8 R14c not(or) /
  C9 B108 混合极性 / C10 B98 边界）——其中 C6/C7 为 HEAD 前已存在字节残余
  （实测 HEAD 产物 byte_equal=False，A/B TEXT-SAME 零漂移，归 OBSERVE-PASS
  如实登记）。**MATRIX: ALL PASS**（10 hard + 3 OBSERVE）。
- **A/B 回归电池 267 案**（r122_regress.py：r110 169 + v111 15 + v112 15 +
  v113 15 + v115 9 + v116 4 + v117 6 + v118 7 + v119 8 + v120 6 + 本轮 13；
  独立 TMP r122regress；两文件交换 + fix_patch 自愈）：**TEXT-DIFF 3/267
  恰为本轮三功效案且全部 BYTE-EQUAL**；R110 案 168/169 一致（唯一差 mc1 =
  r110 轮功效案两侧同持修复正常归一，TEXT-SAME+BYTE-EQUAL）；既有登记差
  10 案 **ALL SAME-SIGNATURE**；NO-SRC 0。
- **pytest 7 套件**（test_algorithm_correctness / deep_nesting_pressure /
  control_flow_completeness_matrix / complete_syntax_coverage /
  boundary_cases / core_functional / repo_tool_hygiene）：**3 failed /
  281 passed / 2 xpassed**——HEAD 同命令对照 **3 failed / 281 passed /
  2 xpassed 逐项一致（同名 3 失败），v122 零漂移**；3 失败 = 2 冻结对 +
  卫生红数闩（15>14）前已存在；+4 passed 与 r118~r120 台账读数（277）之差
  亦为前已存在收集差异（HEAD 实测同读数）。
- **卫生验证器 A/B**（validate_region_generator_signatures.py）：v122 与
  HEAD 同为 **15 错 6 警**（新方法零触发——非 `_generate_*` 前缀、无禁止
  模式命中），红数闩失败为更早轮基线闩值漂移，非本轮回归。
- **REAL46 sweep 46 案全量复核**（新鲜产物 `--source`，sweep46_v122.py）：
  见 §7.4 实测读数。

### 7.3 过程登记

- 电池 phase2 首跑被用户收敛指令中止，工作树两文件曾停 HEAD 版（v122 标记
  归零）——由 fix_patch_v5r122.diff 自愈恢复（补丁含两文件 +176/−4 已核，
  o1 功效复核通过）后干净重跑 phase1/2/3，本节数字为修正后实测。
- 矩阵脚本首跑两处小缺陷（输出目录缺位、dict 迭代解包）修正后干净重跑；
  C6/C7 判据按实情改归 OBSERVE（HEAD 前残余 + 零漂移）。

### 7.4 验收口径与 sweep 读数

大改动级全量验收按指令执行（267 案电池 + pytest 7 套件 + REAL46 sweep 复核）。
REAL46 sweep 46 案全量重判（v122 新鲜产物 `--source`）+ **HEAD 侧同 sweep
A/B 对照**：46 案读数**仅 1 差**——stdlib_xml_ElementPath HEAD 37/39 94.87%
→ v122 **38/39 97.44%**（+1 = prepare_predicate 过判官，唯一残余单位 =
iterfind，R7 2→1），其余 45 案逐字节一致（sweep46_v122_result.txt vs
sweep46_head_result.txt diff 实证），**零新增回归**。不宣称 G1/G2c/G3/G4/G6
通过；product_complete 仍 NOT PASS。

### 7.5 剩余登记（下一轮候选）

- `/iterfind`（−102 字节）while-1 体丢失大族（pe8 同域，r105 诊断在案需
  派发表先行）——REAL46-008 判官唯一残余单位（R7=1）。
- v118 E2 残余（while 底部 store-recheck）同域；E6 相邻 NOP 对；
  46 sweep 其余 DIFFERENT（REAL46-011~016）/17 ERROR。
- 卫生红数闩：基线 14 与实测 15 的闩值漂移为前已存在（r113~r120 间引入），
  修复需独立轮（合规范式重命名或闩值重估），不在本轮范围。


## 0. 结论速览

- Task 47 目标族实证闭环：最小复现 o1 在 HEAD（96d4113b）精确复现否定卫臂
  拆臂丢体——`if sig == 'a' or sig == 'b' or ((sig == 'c' or sig == 'd')
  and not pred.isdigit()): <臂体>` 渲染成 `if not (sig == 'a' or sig == 'b'):
  <余部整体嵌套>`，a/b 两真路径整体丢失（sig='a' 原应 return tag，产品返回
  None；对应 prepare_predicate 的 `.='` 签名误入 raise SyntaxError，真实 R1）。
- 本轮实施 [v121-ORCHAIN] R64 rejoin 直落边扩展实验：链吸收成功（26/38/50
  全部入链），但消费端 or_groups 对平坦 op 序列做**平坦重建**，产出
  `not ((a or b or c or d) and pred.isdigit())`——内层分组丢失 + `not` 极性
  反转（o1_out2.py 存档）。**证明单点守卫扩展不足，且暴露第二层缺口**。
- 架构定性：臂体已被内层区域认领（每块唯一归属），外层 IfRegion 真臂为空
  才回退否定卫臂；「复制臂体重渲染」违反唯一归属原则（No More Gotos），
  架构性禁止。**唯一正确修复 = 两段式嵌套 BoolOpRegion 构造**（研究级），
  本轮按纪律「新失败先登记，不并行打补丁」回退实验、登记收口，不修。

## 1. 复现（o1，`repro_o1.py`/`repro_o1.pyc`）

```python
def f(sig, pred):
    if sig == 'a' or sig == 'b' or ((sig == 'c' or sig == 'd') and not pred.isdigit()):
        tag = pred[0]
        return tag
    if sig == 'e':
        return 'E'
    else:
        raise ValueError('bad')
```

块边（pycdump 实测）：@0 PJT→90 ft→14；@14 PJT→90 ft→26；@26 PJT→50
ft→38；@38 PJF→110 ft→50；@50 PJT→110 **ft→90**；@90=臂体 [STORE tag,
RETURN]；@110=e 测试 PJF→126；@126=raise。正确结构：
`or[a(@0), b(@14), and[or[c(@26), d(@38)], ¬re(@50)]]`，真出口 90，假出口 110。

语义实测（HEAD 产物）：
- sig='a'：原→臂体→return tag；产品→`not(a or b)`=False→跳过→隐式 None
  （**真实 R1**，prepare_predicate 对应 `.='` 签名误 raise）。
- sig='c'、pred 非数字：原/产品一致（臂体执行）——内层 and 形未被破坏。
- sig='e'：两侧一致 'E'（否定卫臂真臂内的 e 测试恰好保序）。

## 2. 机制链（三层实证）

1. **走查层**（region_analyzer `_detect_boolop_conditional_chain`）：成员 26
   的 rejoin 判定失败——其链上后继 50 的 PJT 目标=110≠T=90，而 50 的
   **直落边**才是 90；R64 守卫（closed-shared-exit-prefix）`chain.pop() +
   break` 弹出成员 26（line-trace 实证，probe_o1.py）。守卫行为**正确**：
   平坦链表达不了嵌套 and 组，强吞必错。
2. **区域层**：BoolOpRegion 仅 [0,14]（merge=90 共享臂体）；臂体 @90 被内层
   BoolOpRegion（`(c or d) and not re`，真出口 90）认领。外层 IfRegion 真臂
   空 → 回退**否定卫臂**渲染（条件取反、余部整体入真臂）——即 HEAD 产物形。
3. **消费端**（or_groups 平坦重建）：[v121-ORCHAIN] 实验把 rejoin 判定扩到
   「后继条件块的直落边汇聚 T」（@50 ft→90 命中）后，链吸收为
   [(0,or),(14,or),(26,or),(38,?),(50,?)]，但 op 序列是**平坦的**——
   内层 or 段 [26,38]（共享真出口 50=and 组续测）的边界与否定 and 尾成员
   [50]（PJT→假出口 110、ft→真出口 90、极性反转）无法从平坦序列恢复；
   重建产出 `not ((a or b or c or d) and pred.isdigit())`（分组丢 + 极性
   反，o1_out2.py）。**第二层缺口实证。**

### 2.1 为什么不能小修

- 否定卫臂回退的成因是臂体唯一归属：真臂空 ≠ 可复制。把臂体复制进
  `if a or b:` 与 `elif (c or d)…:` 两处，重编译字节形不同（CPython 不去重
  语句块）且违反每块唯一归属——架构性禁止。
- R64 扩展已证：吸收成功 ≠ 重建正确；修 op 分配/分组需同时让消费端理解
  「or 段真跳目标=and 组续测」的内层边界 + 否定成员极性——即完整嵌套构造。

## 3. 修复路径（登记，独立轮次实施）

两段式嵌套 BoolOpRegion 构造（先内后外）：

1. **内层段**：识别 or-run [26,38]——判别锚点：成员 PJT 目标 = 链上后继
   测试块（50）而非臂体（与外层 or 成员 PJT=臂体 90 相区分；即指令判别锚
   「成员真跳目标=共享臂体」的反向应用）；尾随 and 尾成员 [50]——PJT=
   全链假出口（110）且 ft=真出口（90）且极性反转（`not` 操作数，W14-A/R3-K
   同域极性机制）。先构成嵌套 BoolOpRegion：`and[or[c,d], ¬re]`，真出口
   90、假出口 110。
2. **外层链**：嵌套区域作为**单一成员**并入外层 or 链 [0,14]（成员可为
   区域，链真出口 90、假出口 110），消费端按既有 or_groups 重建
   `or[a, b, <嵌套区>]`。
3. 验收：o1 重编译 BYTE-EQUAL 为目标；prepare_predicate /prepare_predicate
   字节收敛（+12 残余的主体）；因动核心走查+消费端，需全额 254 案电池 +
   pytest 7 套件 + REAL46 sweep 复核（按用户政策，此为「大改动」级别）。

## 4. 验收口径

本轮诊断登记收口，**零源码改动**（[v121-ORCHAIN] 实验已完整回退，工作树
core/* 与 HEAD 96d4113b 逐字节一致；grep 复核否定卫臂形=1 确认基线还原）。
不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。实验产物
（o1_out2.py）与探针存档于本目录，供下轮实施比对。

## 5. 剩余登记（未变）

- `/iterfind`（−102 字节）while-1 体丢失大族（pe8 同域，r105 诊断在案需
  派发表先行）；v118 E2 残余（while 底部 store-recheck）同域。
- E6 相邻 NOP 对（Round-33 守卫同形不可分，语义等价低价值）；
  46 sweep 其余 DIFFERENT（REAL46-011/012/013/014/015/016）、17 ERROR。

## 6. 证据文件

`repro_o1.py`/`repro_o1.pyc`（最小复现）、`product_HEAD_o1.py`（HEAD 否定
卫臂产物）、`product_v121experiment_o1.py`（实验错误形存档）、`probe_o1.py`
（区域树+走查 line-trace 探针）、本文件；过程中间件（pycdump、对照产物）
在 `D:/temp/opencode/cl_layout/r121diag/`，不入库。
