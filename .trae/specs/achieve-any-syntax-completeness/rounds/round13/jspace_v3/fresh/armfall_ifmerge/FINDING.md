# FINDING — rr-v5r120 [v120-ARMFALL]：直落臂后随语句被折进假边专属 else（if-merge 折叠族，真实 R1）——prepare_predicate 病形二闭合

## 0. 结论速览

- rr-v5r119 闭合 `/prepare_predicate` 病形一（循环顶 try 错挂）后，字节残余
  1204 vs 1218 深挖出**第二层病形**：循环体内 quote 调整臂（`if token[0]
  and token[0][:1] in '\'': token = ...`）**直落**到无条件随后的
  `signature/predicate.append(...)`，产品把这对独立 if 语句折叠成
  `elif quote: 调整 / else: appends`——appends 变成 quote-if 的**假边专属
  else**：quote 臂成立时调整后的 token **不再追加**（真实 R1），且臂尾多出
  JUMP_FORWARD 越过 else（+2 字节源）。
- 本轮 [v120-ARMFALL] 三点修复后：最小复现 p2 **重编译全字段
  BYTE-EQUAL**；`/prepare_predicate` 1218→**1216**（形状语义正确；剩余
  +12 为第三层病形——or 链拆臂丢体，§5 登记，判官 R7 维持 2）。

## 1. 根因（字节级比对 + AST/转换器/代码生成三层追踪）

### 1.1 差异面（p2 = 精确最小复现）

原件（prepare_predicate 循环体尾）：`if ']' break` / `if ('','') continue` /
`if quote 调整`（无 else）三条**独立 if**，appends 无条件随其后。
产品（HEAD）：`if ']' break / elif ('','') continue / elif quote: 调整 /
else: appends`。

### 1.2 机制链（三层）

- 渲染层：quote-if 的 IfRegion（IF_THEN，无 else 臂，merge=206=appends 块）
  在 else 走查（`_process_if_blocks`）内联派发，其 AST 与后随兄弟语句
  （appends）成为同层列表 `[If(quote), Expr, Expr]`——此层**正确**。
- 转换层（`CFGASTConverter._convert_if`）：dict 无 elif 链字段，
  orelse 原样转换 `[ASTIf(quote), Expr, Expr]`——此层也**正确**。
- 代码生成层（`CFGCodeGenerator._generate_elif_or_else`）：orelse.nodes =
  [If, 兄弟…] 且首 If 未标 `_is_elif` 时打印 `elif`，随后「剩余非 If 节点 →
  `else:`」把兄弟语句塞进该 elif 的**假边专属 else**（code_generator.py
  ~1940-1952）——折叠发生于此。Round-31 既有否证只覆盖「首 If 自身 orelse
  有内容」形，直落臂（orelse 空）漏网。

### 1.3 语义危害（repro 实测口径）

原件：quote 臂成立 → token 调整 → **appends 照常执行**。
产品：quote 臂成立 → 调整 → 跳过 else → **appends 丢失**（signature/
predicate 少一条目）。

## 2. 修复（只增不破，[v120-ARMFALL] 三文件 +114/−6 + 分析层同族守卫 +62）

1. **渲染层打标**（region_ast_generator.py）：`_process_if_blocks` 嵌套
   IfRegion 派发后，若该区域无 else_blocks 且无 elif_conditions 且其
   merge_block 恰为走查序列中其自身块之后的第一个块（臂直落到后随语句）→
   给该 If 的 AST 打 `_v120_arm_falls` 标（同构守卫同步加在
   `_if_generate_else_branch` 的 C3 emit-units 'region' 分支）。
2. **转换层传递**（ast_converter.py）：dict 标转入模块级标记集
   `_V120_ARM_FALLS`（ASTIf `__slots__` 不可挂属性；持引用防 id 复用）。
3. **代码生成否证**（code_generator.py）：`_generate_elif_or_else` 中首 If
   带标时整块走 else 体渲染（该 If 作嵌套 if、兄弟语句保序跟其后）——
   Round-31 既有形状的直落臂扩展；无标路径逐位不变。
4. **分析层同族守卫**（region_analyzer.py，本轮开头实施）：`_check_elif_chain`
   准入点增设臂直落否证——候选条件块真臂有限步直落/显式跳入其假边目标且
   假边目标 ≠ 本层 merge（排除无 else 链的等价形，W52 行为不变）→ 拒绝吸收。
   本轮病形链在渲染层拼装、此守卫未触发（probe 实证 `_build_elif_region`
   对 62/104/118 全 None），但它封住同族的分析层路径；不命中逐位不变。

## 3. 验证（全实测）

### 3.1 变体矩阵（`matrix_v5r120.py` 6 案，A/B 四文件交换 HEAD `4baf2261` vs v120）

| 案 | 形 | HEAD | v120 | 判定 |
|---|---|---|---|---|
| E1_armfall_quote | while1 + try + if-break/if-continue/独立 quote-if + 无条件 appends（p2 精确形） | TEXT-DIFF（appends 被折进假边 else） | 重编译 BYTE-EQUAL | PASS |
| C5/E2_armfall_assign | 同构（SUBSCR 臂形） | — | 逐字节同 + BYTE-EQUAL | PASS（HEAD 本已正确——SUBSCR 臂形不触发折叠，实测归控制） |
| C1_trytop_while1 | v119 功效案（TRYTOP 域） | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C2_shared_entry_peer | 共享入口 peer（get_opt_objects 族） | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C3_genuine_else_chain | 真 else 链（return 臂 + else 体） | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |
| C4_armfall_noloop | 无循环直落臂同构 | — | 逐字节同 + BYTE-EQUAL | PASS（C3） |

### 3.2 REAL46-008（ElementPath）

- p2 重编译 4 code objects 全字段 BYTE-EQUAL（功效直证）。
- `/prepare_predicate`：1218→**1216**（else 折叠 +2 字节源消除；剩余 +12 =
  第三层病形，§5）；`/iterfind` 零漂移未动。
- 权威判官维持 DIFFERENT 2 R7（本轮闭合第二层病形语义，R7 按 code_sha 计
  未变——余两层未修）。

### 3.3 回归

- A/B 回归电池（r120_regress.py：r110 169 + v111 15 + v112 15 + v113 15 +
  v115 9 + v116 4 + v117 6 + v118 7 + v119 8 + 本轮 6 = **254 案**，独立
  TMP `r120regress/`，**四文件交换**）：**TEXT-DIFF 1 / 254 恰为本轮唯一
  功效案（E1，重编译 BYTE-EQUAL）**；其余 253 案 TEXT-SAME；R110 案
  168/169 一致（唯一差 mc1 = r110 轮功效案两侧同持修复正常归一，
  TEXT-SAME+BYTE-EQUAL）；既有登记差 10 案 **ALL SAME-SIGNATURE**；
  NO-SRC 0。
  （过程登记：电池漏挂 trytop_loop 路径致 v119 案源导入失败、生成期
  ensure 函数名替换未命中致 `cur_files` 未定义且 phase2 finally 恢复中断
  ——工作树四文件曾停在 HEAD 版，已由补丁自愈恢复（补丁导出亦曾漏
  region_analyzer.py，已补全 4 文件 +166/−6）后干净重跑，本节数字为修正后
  实测。）
- pytest 7 套件：**3 failed / 277 passed / 2 xpassed**——与基线逐项一致
  （2 冻结对 + product_freshness 预存在陈旧），零新增失败；4 个 stale
  条目（strategy_universe 40 行 3787/3712、load_daily 26229/26134、
  matcher 167 行 13299/13375、trade_info_utils 1010 行 61506/61753）与
  r119 读数逐字相同——**v120 零漂移**。
- 比较器 pyc_verify.py FE1902A9 / semantic_diff.py DBCB1E24 冻结一致、
  tests/ 零改动；已跟踪改动 = 4 文件
  `M core/cfg/region_analyzer.py（+58）M core/cfg/region_ast_generator.py
  （+47/−1）M core/cfg/ast_converter.py（+37/−4）
  M core/cfg/code_generator.py（+30）`（标记 `[v120-ARMFALL]`）。

## 4. 验收口径

小测试收口（全量闸门按用户政策只留给大改动）。不宣称 G1/G2c/G3/G4/G6 通过；
product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选，未修）

- **or 链拆臂丢体（新族，真实 R1）**：prepare_predicate 的
  `if signature == ".='" or ".!='" or ((-='" or "-!='") and not re.match(...))`
  共享臂 or+and 混合链被拆成 `elif not (".='" or ".!='"): if (-=… and …): <体>`
  ——`.='"`/`.!='` 真路径丢失（`.='` 签名误 raise SyntaxError，原函数正常
  构建选择器）；成员真跳目标=共享臂体（@606/618 PJT→698）即判别锚点。
  v119 起预存在（本轮 A/B 零漂移），+12 字节残余的主体。
- `/iterfind`（−102 字节）= while-1 体丢失大族（pe8 同域，r105 诊断在案
  需派发表先行）；v118 E2 残余（while 底部 store-recheck）同域。
- E6 相邻 NOP 对；46 sweep 其余 DIFFERENT（REAL46-011/012/013/014/015/016，
  022/046 已定性观察层 R5）/17 ERROR。

## 6. 证据文件

`fix_patch_v5r120.diff`、`matrix_v5r120.py`、`r120_regress.py+result`、
`ElementPath_product_v120.py`、`repro_p2.py`、本文件；探针与复现：
`D:/temp/opencode/cl_layout/r120diag/`（p1/p2 复现、probe_regs120、
probe_emit、转换期 dict 转储）、`D:/temp/opencode/cl_layout/r120matrix/`。
不入库。
