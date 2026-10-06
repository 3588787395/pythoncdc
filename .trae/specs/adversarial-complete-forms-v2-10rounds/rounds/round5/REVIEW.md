# Round 5 评审报告（Task 5.1）—— 深层嵌套交叉矩阵对抗

- 规范：`.trae/specs/adversarial-complete-forms-v2-10rounds`
- 评审角色：独立对抗评审工程师子代理（只读审计 + 探针构建 + 报告 + 破口登记；**零实现 / 零 core 修改 / 零 git 提交**）
- 工作目录：`f:\Downloads\pythoncdc-main`（Windows / PowerShell）
- 启动快照 HEAD：`58c2099e12f03bf29e98f2a92721a22d81867d27`（`rr-v2r05: round5 启动快照`）
- 判据唯一：`scripts/pyc_verify.py`（ruler sha256 `9c7567bd6776b36b`，pylingual `equivalence_check.py::compare_pyc`）
- 方法学：RV2 —— 一切读数先 `python pycdc.py <pyc> -o <同目录>OK.py` regen，再 verify，禁信磁盘陈旧产物
- 本轮主题：**形态 × 宿主区域组合（深度 ≥3）交叉矩阵对抗**，重点攻击 Round 3/4 宣告完备的 7 族交叉宿主空白格

---

## §0 三态终判预备结论

| 维度 | 读数 | 判定 |
|---|---|---|
| 探针总读数 | **187 / 208**（attack 165/186，负对照 22/22 全 MATCH） | — |
| 站桩 6 面 WORSE | **0**（全 6 面同 round4 基线逐位一致） | PASS |
| 合规审计 | 新增违反 **0**；I.4 五项 / I.5 七前缀 / BOM 单头 / 插桩 / 在途 / `*OK.py` 手改 全 PASS | PASS |
| 新破口登记 | **3 项：B114 / B115 / B116** | — |
| 同机理存量 | 4 项（starargs→B106、walrus→B105、decorator→B111、except*→B102 残余；lambda→round3 F5/B106 族） | — |

**预备终判：三态 = 破口（非完备、非零能力）。**
- 已宣告完备的 7 族中，`elif 链 / augmented_assign / keyword_args / slice(宿主形态) / global-nonlocal / f-string 转换符 / for-else 单侧` 的**形态本体**在交叉宿主下仍逐位完备（对应探针全 MATCH）；但**交叉宿主空白格**暴露 3 个此前从未被交叉攻击覆盖的新破口（B114/B115/B116），故"完备"声明的**交叉封闭性被证伪**。
- 7 族声明中 `slice`（B6/C7）交叉宿主格命中 B115（if+while 条件融合，与 slice 无关），`AnnAssign`（A12）格命中 B116 —— 二者属"形态本体完备、宿主组合破口"，机制独立于原形态族。
- 未发现核心算法整体回退（站桩 6 面 WORSE=0），破口局限于上述 3 个交叉机制。

---

## §1 合规审计表（基准 HEAD `58c2099e`；本轮纯评审 → 新增应 0）

审计前提：`git status --porcelain` 与 `git status --porcelain core/` **均为空**，core/ 零在途变更（见 §2 命令证据），故核心源码新增违规恒为 0。下表并存"全树存量扫描"结果供移交。

| I.4/I.5 条款 | 检查方法 | 命中 | 判定 |
|---|---|---|---|
| I.4-① 文件名/函数名白名单特判 | grep `test_repros\|round\d\|co_filename\|_OK\.py\|\.pyc` in `core/` | 命中均为**注释性引用**（`region_ast_generator.py` 注释 7 处引用 round67_diag4/quote.pyc/live.pyc 等）+ `pyc_loader_v2.py:231` `__main__` 缺省路径 1 处；**无判据型语料名特判**；与 round1 §4 口径一致 | 新增 0 **PASS**（存量注释观察） |
| I.4-② start_offset 魔法阈值 | grep `start_offset == 62\|== 74\|start_offset\s*==\s*\d+` | round1 §4 登记的 `ast_generator_v2.py:9050==62` / `:14990==74` **已不存在**；`structured_analyzer.py` 仅余 `== 0`（结构序键，白名单）与两处**注释掉的** `== 76`；`region_ast_generator.py:24487` 存在 `b.start_offset in (192, 584)`（见下"存量观察"） | 新增 0 **PASS** |
| I.4-③ 跨层 `entry in blocks` 反查 | grep `entry in blocks` | 0 命中（round4 §1 注①的存量实例以 `X.entry in Y.blocks` 变体存在，属 HEAD 基线前历史守卫，非本轮新增） | 新增 0 **PASS** |
| I.4-④ 新增 `self.` 跨方法状态 | git diff core/（在途为空） | 在途 0 → 新增 0 | 新增 0 **PASS** |
| I.4-⑤ 少发射换绿 / 硬编码深度上限 | grep `depth > \d+\|MAX_DEPTH\|max_depth\s*=\s*\d+` | round1 §4 的 `structured_analyzer.py:14330 depth>3` **已不存在**；现存 `bytecode_matcher.py:89/91/93 max_depth>5/3/2`、`patch_detector_enhanced.py:358 depth>3`、`region_analyzer.py:2663/2822/2827 max_depth=15/3`、`region_ast_generator.py:30875 max_depth=6` —— 均为**历史存量**（非归约终止判据的单文件内搜索上限）；站桩 6 面 WORSE=0 亦否证"少发射换绿" | 新增 0 **PASS**（存量观察移交） |
| I.5 七前缀方法（新增） | grep `def (_fix_\|_merge_\|_patch_\|_fallback_\|_hack_\|_workaround_\|_temp_)\w+` in `core/` | 3 命中：`control_flow.py:720 _merge_redundant_blocks`、`region_ast_generator.py:19986 _merge_block_is_then_exclusive`、`:41068 _merge_block_is_loop_back_edge`（**与 round4 §1 "树内存量 3 处历史名" 逐位一致**） | 新增 0 **PASS** |
| BOM（IV.2 单头） | 字节级 `region_analyzer.py` / `region_ast_generator.py` | 头 3 字节均 `efbbbf`，全文 BOM 计数各 = 1 → **双核心恰一单头**，无双 BOM | **PASS** |
| 插桩残留（G0） | grep `DBG_\|DEBUG_\|environ.get(` | round1 §4 的 `region_analyzer.py:18324-18625 DBG_OR×18` **已不存在**（commit `a411d9d5` round1 位 A 清理）；现存 `region_ast_generator.py` 15 处、`ast_generator_v2.py` 2 处 **env-gated 调试守卫**（`R7_DEBUG_IFGEN`/`R23N6_DEBUG*`/`R16_DEBUG`/`EBM_DEBUG`/`R30_13_DEBUG`/`PYCDC_DEBUG`），全部 `os.environ.get(...)` 条件包裹、缺省关闭 | 新增 0 **PASS**（存量观察移交，非本轮引入） |
| 在途代码变更 | `git status --porcelain core/` | 空 | **PASS** |
| `*OK.py` 手改 | `git status --porcelain`（无 `M` 项） | 本轮新增 `*OK.py` 全为工具链 regen 产物（untracked），**零手改** | **PASS** |

**存量观察（非新增，移交 §5）**
1. `region_ast_generator.py:24486-24487`、`:24524-24525` —— `R7_DEBUG_IFGEN` 调试守卫 + 其中 `start_offset in (192, 584)` 属**偏移魔数成员判定**（I.4-② 边界面，env 关闭时惰性）。
2. `region_ast_generator.py` + `ast_generator_v2.py` 共 17 处 env-gated 调试块（G0 插桩残留类）。
3. round1 §4 原 4 族（`ast_generator_v2:9050/:14990`、`structured_analyzer:14330`、`region_analyzer DBG_OR×18`）**经复核均已被 round1 修复批次（`a411d9d5`/`33d6e87e`）清理**，本轮零命中 —— 存量清单更新，不再列为遗留。

---

## §2 站桩回归读数表（RV2：逐面先 regen 再 verify）

执行：`python .trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round5/r5v5_station.py <face>`（round2face 面因并发争用曾误读 7→0，**已单进程串行重跑复现 234/251**），对照：`r5v5_compare_regress.py`。

| 面 | round4 基线 | 本轮新读数 | common | same | improved | **WORSE** | 判定 |
|---|---|---|---|---|---|---|---|
| round2 45 文件面 | 234/251 | **234/251** | 45 | 45 | 0 | **0** | 持平 |
| round2 42 探针面 | 172/196 | **172/196** | 42 | 32 | 10 | **0** | 持平/累计改善 |
| round1 哨兵面 | 417/423 | **417/423** | 24 | 24 | 0 | **0** | 持平 |
| v1 残余面 | 417/446 | **417/446** | 72 | 62 | 10 | **0** | 持平/累计改善 |
| 旧规范 round6–10 面 | 664/692 | **664/692** | 59 | 55 | 4 | **0** | 持平/累计改善 |
| quotation.pyc 单验 | 152/153 | **152/153** | 1 | 1 | 0 | **0** | 持平 |

`improved` 系相对 round2/round1/round3 旧基线的**累计**改善（round4 已完成），本轮读数与 `rounds/round4/VERIFICATION.md` 六面**逐位一致**。**WORSE = 0，无回退。**

> 并发纪律登记：首轮 5 面并跑时，`test_repros/round7/r7_08_ternary_deep_host.pyc` 因多进程争用同一 `r7_08_ternary_deep_hostOK.py` 产物，被 round2face 面误读为 0/8 产生**伪 WORSE=1**；单进程串行复跑得 7/8 与基线一致，伪差消除。已据此以单进程串行重采 round2face 面，证据 `r5v5_regress_round2face.json` 为串行终值。**RV2 结论：站桩面读取须串行或隔离 OK 产物，禁并发。**

---

## §3 交叉矩阵攻击结果表（形态 × 宿主区域，深度 ≥3）

探针：`test_repros/round5/r5v5_01..15`（攻击，前缀 `r5v5_`）+ `n5v5_01..04`（负对照）。
**前缀口径偏差登记**：任务书指定 `r5_*`/`n5_*`，但 `test_repros/round5/` 已存在旧规范 round5（推导式主题）26 个已跟踪 `r5_*` 文件；为守"零覆盖既有文件 / 无 `M` 项"更强制纪律，本轮改用 `r5v5_*`/`n5v5_*`（与证据 JSON 前缀一致）。此为**如实登记的偏差**，非违规。

| 探针 | 目标空白格（§3.4 优先级） | 读数 | 失败单元要点 | 三态 |
|---|---|---|---|---|
| `r5v5_01_module_root` | ① Module 根宿主(A1) | 2/3 | `<module>`：`import os.path` 被误发为幻影 `import os.path as os`（多 IMPORT_FROM+POP_TOP） | **破口 B114** |
| `r5v5_02_class_body` | ② ClassDef 体宿主(A15) | 9/9 | — | 完备维持 |
| `r5v5_03_annassign` | ③ AnnAssign 宿主(A12) | 10/11 | `ann_root`：函数内**裸注解** `b: str` 声明局部名被丢弃 → 后续 `b` 退化 LOAD_GLOBAL | **破口 B116** |
| `r5v5_04_elif_cross` | elif 链 × 交叉宿主 | 5/5 | — | 完备维持 |
| `r5v5_05_augassign_cross` | augmented_assign × 交叉宿主 | 10/10 | — | 完备维持 |
| `r5v5_06_keywordargs_callsite` | ⑤ keyword_args 调用点(B6) | 14/14 | — | 完备维持 |
| `r5v5_07_starargs_callsite` | ⑤ star_args 调用点(B9) | 4/13 | `st_nontail/st_mixed/st_multistar/st_deep/CSt.m/st_close.inner/st_match/st_comp(+listcomp)` 9 单元 Different bytecode | **同 B106 存量** |
| `r5v5_08_slice_callsite` | ⑤ slice 调用点(B6/C7) | 10/11 | `sl_deep`：外层 `if i:` + 内层 `while i>0:` → 融合为 `while i and i > 0`（Different control flow） | **破口 B115** |
| `r5v5_09_walrus_callsite` | ⑤ walrus 调用点(C7) | 6/12 | `w_root/w_call/w_nested_call/w_deep/CW.m/w_with` 6 单元 | **同 B105 存量** |
| `r5v5_10_fstring_cross` | ④ f-string 转换符(B7/C9) | 13/13 | — | 完备维持 |
| `r5v5_11_global_nonlocal_cross` | global/nonlocal × 交叉宿主 | 15/15 | — | 完备维持 |
| `r5v5_12_decorator_cross` | ⑥ decorator_with_args(C11) | 21/22 | `d_deep.Local`：产物 `@((x,))`（装饰器表达式形态错） | **同 B111 存量** |
| `r5v5_13_for_else_cross` | for-else 单侧 × 交叉宿主 | 11/11 | — | 完备维持 |
| `r5v5_14_except_star_deep` | 次级 TryStar/except* | 9/10 | `es_with`：Different control flow | **同 B102 残余存量** |
| `r5v5_15_lambda_combo` | 次级 Lambda | 26/27 | `lam_star.<lambda>`：Different bytecode | **同 round3 F5 / B106 族存量** |
| `n5v5_01..04` | 负对照（浅层同形） | 22/22 | 全 MATCH | PASS |

**合计：attack 165/186 + neg 22/22 = 187/208。**

### §3.1 新破口机制与最小复现（`_scratch_r5v5/`）

**B114 —— 模块根点号 import × 序列目标赋值 → 幻影别名**
- 最小复现：`y1_dotted_tuple.py` = `import os.path` + `XX, YY = 1, 2`（depth=1 即触发）
- 首分歧：`<module>` orig=108 / ok=110，@11 `orig=STORE_NAME 'os'` vs `ok=IMPORT_FROM 'path'` → 产物 `import os.path as os`（多 IMPORT_FROM+POP_TOP）
- 触发边界（对照实验）：`y2` 链式 `XX = YY = 1` PASS；`y3` 无点号 import PASS；`y5` 普通 `import os` + tuple PASS；`y6` 别名 `import os.path as p` + tuple PASS；`x5` 无 docstring 亦 FAIL（docstring 非必要）；`x6` 无 `import os as _os` 亦 FAIL（前缀别名非必要）。
- 机制：**未别名的点号 import（需 `STORE_NAME a` 绑定顶层名 a）+ 模块级序列目标赋值（UNPACK_SEQUENCE）** 二者共现时，反编译器名称绑定/存储分析把 `import a.b` 的 `STORE_NAME a` 误关联为别名形态，凭空发射 `IMPORT_FROM`。深度 1 即现，属**宿主组合机制**（A1 模块根 × import × 序列赋值），非 A1 本体。
- 违反条款：C1 局部消费（import 区域名绑定泄漏）/ C3 守卫封闭（区域边界被名称分析跨界改写）。

**B115 —— 外层 if 体首语句为 while → 条件融合**
- 最小复现：`k1_ifwhile.py` = `def f(i):` / `if i:` / `while i > 0:` / `i -= 1` / `return i`（nesting depth=2）
- 产物：`while i and i > 0:`（if 条件被并进 while 条件，凭空 BoolOp，Different control flow）
- 触发边界：`k3` 内外互换（`while i>0:` 体首为 `if i:`）PASS → 触发方向单向（**外层 if 体首语句 = while**）。
- 机制：外层 `if` 守卫块与其首个子块（while 头）在区域归约时被合并，if 条件求值块被当作 while 条件的一部分 → **守卫封闭（C3）破坏**。与 B98（or-in-and 分组丢失）不同：此处非 BoolOp 分组，而是区域/控制流融合，BoolOp 为次生。
- 违反条款：C3 守卫封闭 / C2 黑箱组合（子区域未只经 entry/exit 消费，被上层吸收）。

**B116 —— 函数内裸注解丢弃 → 局部名退化**
- 最小复现：`k4_bare_ann.py` = `def f():` / `b: str` / `return b`（bare annotation，无值）
- 首分歧：`f` orig `LOAD_FAST 'b'` vs ok `LOAD_GLOBAL 'b'` → 裸注解 `b: str` 使 `b` 进入 `co_varnames`（局部名声明），反编译器丢弃该注解且未登记局部名 → 引用退化为全局名。
- 触发边界：`k5` 赋值型 `b: str = x` PASS；`k6` 纯赋值型 `b: int = 3` PASS；模块级裸注解 `w2/w5` PASS → 触发限定**函数局部裸注解**。
- 机制：**code object 元数据（co_varnames）** 中由裸注解声明的名字未被反编译器消费，名称解析正确性受损。
- 违反条款：C1 局部消费（code object 元数据未完整读取）/ I.4 白名单允许的"区域成员关系/code object 元数据"未落实。

---

## §3.x II.7 十三条误解自查

| # | 误解 | 本轮自查结论 |
|---|---|---|
| 1 | 循环论证分母 | 分母 208 = 探针实测单元（非按形态族声明反推）；attack/neg 分列。✔ |
| 2 | 有过就算 | 失败单元逐条登记（非"文件有过即算"）；`r5v5_07` 4/13 明确 9 单元破口，未以"有成功即算完备"。✔ |
| 3 | 语料证据口径 | 攻击结论均附最小复现（`_scratch_r5v5/` 第四轮隔离），非仅引语料。✔ |
| 4 | 无限分母 | 分母封闭为 208，未随发现扩分母。✔ |
| 5 | 节点词汇当完备 | 三态判定以判据 `pyc_verify` 输出为准，非以"节点存在"判完备。✔ |
| 6 | 浅层测试当无感证明 | 每探针含 depth≥3 单元（如 `ann_nested3` 三层闭包、`sl_nested` 三重切片）；B114 虽深度 1 触发但已并入深宿主矩阵。⚠ 部分交叉格仅深 2–3，未达极深，登记为残余风险。 |
| 7 | 门禁读数当完备性 | 站桩 6 面仅作回归门禁（WORSE=0），**未**据以判"完备"；完备性由交叉攻击独立判定。✔ |
| 8 | 顶层构造粗清单 | 探针按"形态 × 宿主"组合细分（非按顶层构造罗列）。✔ |
| 9 | 识别率当完备性 | 187/208 仅作读数，破口以机制归因为准。✔ |
| 10 | 维度互替 | 形态维度与宿主维度分列于 §3 表（未以一维度替代另一维）。✔ |
| 11 | 改工具不改方法 | 本轮**未改任何工具/源码**（纯评审），判据与 ruler sha 未变。✔ |
| 12 | 错误检测标准 | 3.11 判据记号 `CHECK_EG_MATCH`/`PREP_RERAISE_STAR`/`is_except_star`（`r5v5_14` except* 用）；未误用 3.12 `PRELOAD_RERAISE`。✔ |
| 13 | 语料上限当能力上限 | B114/B115/B116 由最小复现证机制，非以语料规模判能力上限。✔ |

---

## §4 新破口登记

登记规则：与既有 Bn 同机理者标"同 Bn 存量"不重复编号；新机理自 **B114** 续接（round4 用尽至 B113）。全部附锚点 file:line + 最小复现 + 机制 + 违反条款。

| 编号 | 名称 | 锚点 file:line | 最小复现 | 机制 | 违反条款 | 攻击矩阵格 |
|---|---|---|---|---|---|---|
| **B114** | 模块根 `import a.b`（未别名）× 序列目标赋值 → 幻影 `import a.b as a` | `<module>` @STORE_NAME(点号 import 绑定名) 处；探针 `test_repros/round5/r5v5_01_module_root.pyc` | `test_repros/round5/_scratch_r5v5/y1_dotted_tuple.py` | 未别名点号 import 的顶层 `STORE_NAME a` 与结合 `UNPACK_SEQUENCE` 的序列目标赋值共现时，名称绑定分析误发射 `IMPORT_FROM 'path'`(+POP_TOP) | C1 局部消费 / C3 守卫封闭 | ①Module 根(A1) × import × 赋值 |
| **B115** | 外层 `if` 体首语句为 `while` → if 条件并入 while 条件 | 函数体内 if/while 区域归约处；探针 `r5v5_08_slice_callsite.pyc::sl_deep` | `test_repros/round5/_scratch_r5v5/k1_ifwhile.py` | 外层 if 守卫块与其首子块（while 头）在归约中被合并，if 条件求值块被当作 while 条件 → `while i and i > 0` 凭空 BoolOp | C3 守卫封闭 / C2 黑箱组合 | ⑤slice 调用点(B6/C7) × if/while 宿主 |
| **B116** | 函数内裸注解 `b: str` 丢弃 → 局部名退化 LOAD_GLOBAL | 函数 code object 名称消费处；探针 `r5v5_03_annassign.pyc::ann_root` | `test_repros/round5/_scratch_r5v5/k4_bare_ann.py` | 裸注解使名字进入 `co_varnames`，反编译器丢弃注解且未登记该局部名 → 引用退化为 LOAD_GLOBAL | C1 局部消费（co_varnames 未完整读取） | ③AnnAssign 宿主(A12) × 函数局部 |

**同 Bn 存量（不重复编号，机理外推证据）**

| 探针 | 读数 | 归类 | 机理 |
|---|---|---|---|
| `r5v5_07_starargs_callsite` | 4/13 | 同 B106 存量 | star_args 调用点跨宿主（含 listcomp/match/class 方法）未变 |
| `r5v5_09_walrus_callsite` | 6/12 | 同 B105 存量 | walrus 调用点跨宿主未变 |
| `r5v5_12_decorator_cross` | 21/22 | 同 B111 存量 | `d_deep.Local` 局部类装饰器表达式 `@((x,))` 未变 |
| `r5v5_14_except_star_deep` | 9/10 | 同 B102 残余存量 | `except*` 多 handler × with 宿主 `es_with` 未闭合 |
| `r5v5_15_lambda_combo` | 26/27 | 同 round3 F5 / B106 族存量 | `lam_star.<lambda>` star-arg lambda 未变 |

---

## §5 移交清单

### 5.1 新破口移交（Task 5.2 修复优先级）

| 优先级 | 破口 | 判据草案（I.4 白名单内） | 涉改文件 |
|---|---|---|---|
| **P0** | B116（裸注解 → LOAD_GLOBAL） | 函数 `co_varnames` 中无语义绑定的名字（来自裸注解 STORE 缺失）须在名称解析阶段登记为局部名；判据 = code object 元数据 `co_varnames` 与区域成员关系 | `core/cfg/ast_generator_v2.py`（名称解析）/ `region_ast_generator.py` |
| **P0** | B114（点号 import 幻影别名） | 点号 import 归约入口仅按同名 `IMPORT_NAME`+`STORE_NAME a` 发射，**禁**在未别名路径产出 `IMPORT_FROM`；判据 = 后继/前驱指令集合（IMPORT_NAME 后继是否为 IMPORT_FROM） | `core/cfg/ast_generator_v2.py`（import 归约入口） |
| **P1** | B115（if 体首 while 条件融合） | 区域归约时外层 if 守卫块须与其体独立成区域；判据 = 块末 opcode / 后继-前驱集合（if 条件假后继 vs while 头块边界），禁跨 guard 合并 | `core/cfg/region_analyzer.py` / `region_ast_generator.py` |

> 三破口位置互不重叠（B114 import 入口 / B116 名称解析 / B115 区域归约 if-while），可并行派发。

### 5.2 存量移交（沿袭 + 本轮复核）

1. **同 Bn 存量维持**：B105（walrus）、B106（star_args）、B111（decorator）、B102 残余（except* × with）、round3 F5/B106 族（star-lambda）—— 交叉宿主已扩面验证，仍破，移交 Task 5.2 认领。
2. **合规存量观察**（非破口）：`region_ast_generator.py:24486-24487` R7_DEBUG_IFGEN + `start_offset in (192,584)` 偏移魔数；全树 17 处 env-gated 调试守卫；`bytecode_matcher.py`/`region_analyzer.py`/`region_ast_generator.py` 内 `max_depth` 硬编码搜索上限。建议专用清理位一次性删除（删除性变更不触算法）。
3. **未封闭移交清单复核**：B103 残余、B104–B112、B113，B98/B99 残余、B44、B1b 五单元、B87/B88 残余、B93/B94/B96/B97 —— 本轮**未逐一复跑**（超出 Round 5 交叉矩阵主题范围），沿 round4 REVIEW2 维持破口口径，保留至后续轮。
4. **方法学移交**：站桩回归面读取**必须单进程串行或隔离 OK 产物**（本轮并发致 `r7_08` 伪 WORSE），建议写入轮门禁脚本约束。
5. **口径移交**：请主代理在 tasks/checklist 中登记本轮前缀偏差（`r5v5_*`/`n5v5_*` 替代任务书 `r5_*`/`n5_*`）。

### 5.3 交付物清单

- 本报告：`.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round5/REVIEW.md`
- 探针：`test_repros/round5/r5v5_01..15.py(+.pyc/+OK.py)`、`n5v5_01..04.py(+.pyc/+OK.py)`（共 133 项，前缀见 §3 偏差登记）
- 最小复现：`test_repros/round5/_scratch_r5v5/`（y1/k1/k4 为 B114/B115/B116 最小复现；gen_variants*.py 为隔离驱动；`_r5v5_firstdiff.py` 首分歧定位器）
- 证据 JSON（`rounds/round5/`）：`r5v5_probe_index.json`、`r5v5_probe_results.json`、`r5v5_probe_full.json`、`r5v5_regress_round2face.json`、`r5v5_regress_probe42.json`、`r5v5_full_round1face.json`、`r5v5_full_residual_a/b.json`、`r5v5_full_oldface_a/b.json`、`r5v5_quotation.json`、`r5v5_station_regress_compare.json`
- 驱动脚本：`rounds/round5/r5v5_attack.py`、`r5v5_station.py`、`r5v5_compare_regress.py`

---

*评审纪律：零实现、零 core/ 修改、零 git 提交（提交由主代理执行）。所有读数经 RV2（先 regen 再 verify）。判据唯一 = `scripts/pyc_verify.py`。*