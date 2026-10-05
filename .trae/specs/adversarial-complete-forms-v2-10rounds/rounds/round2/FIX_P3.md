# Round 2 修复报告（Task 2.2 修复工程师位 3 接续位）—— 发射层 B87/B89 收尾 + B84/B85/B86/B91/B92/B95 在途封闭确认

- 位 3 接续范围：接手 HEAD = `3a9db846` 在途存证（+870 行未定稿修复），先实测在途读数，再补齐/确认评审 §5.1 判据草案的破口封闭；涉改文件 = `core/cfg/region_ast_generator.py`（+55 行）+ `core/cfg/region_analyzer.py`（+15 行，副本签名判据一处）。
- 工具链：`D:/Python/python.exe`（3.11.7，magic 匹配）；`pycdc.py x.pyc -o xOK.py`（先 regen 后 verify，RV2 方法学）→ `scripts/pyc_verify.py single x.pyc`。
- 终态读数证据：`p3_probe_final.json`（42 探针）、`p3_regress_final.json`（站桩 45 文件）。

---

## §0 三态读数总览

| 树态 | 探针读数 | 说明 |
|---|---|---|
| 评审基线（87e59c49） | 154/189 + c06/m12 两文件 COMPILE_ERROR（0/0） | REVIEW §3 |
| 在途存证（3a9db846） | 169/196（c06 3/4、m12 2/3 转可编译后计入分母） | 在途会话产出，本批实测复核确认 |
| 本批终态 | **172/196** | +x04.try_in_while、+x04.try_in_with、+m12 全文件 |

新增封闭单元（before → after）：
- `x04.try_in_while`：FAIL（try 体 `R=1` 蒸发 + 幻影 continue）→ **MATCH**
- `x04.try_in_with`：FAIL（handler 臂 `R=2` 蒸发为幻影 pass）→ **MATCH**
- `m12.<module>`：FAIL（`X` 语句 LOAD_CONST 值差）→ **MATCH**（m12 文件 3/3）

---

## §1 根因分析（锚点 + 机制 + 违反条款）

### §1.1 B87 变体一：x04.try_in_while —— 嵌套 try 预生成越过中间循环宿主

- **锚点**：`region_ast_generator.py` `_generate_try_body` 嵌套预循环（span containment 判据，W11 fix 段）。
- **机制（实测确证）**：`while 1: try: while 1: try: R=1 finally: F=1; except ValueError: R=2` 中，内层 TRY_FINALLY（entry=10，try_blocks=[10]）被外层 TRY_EXCEPT（try_blocks=[6,8,34]，块 8 = 内层循环头）的体装配按 `_is_span_contained` 判据**提前预生成**。后果两段：(a) 内层 try 语句被提升到循环之前（装配序错位）；(b) 内层循环体走查经 `_loop_handle_child_region_entry` 二次派发该 try 时，其体块已被标记 generated，体装配退化为 `Pass`（`R=1` 蒸发、内层 `while 1` 消失、回边泄漏为幻影 `continue`）。监视证据：块 10（R=1）共 5 次 `generated_blocks.add`，首次发生在预生成流内、其后循环走查二次生成同一 region（预生成未登记 `_generated_regions`）。
- **违反条款**：C1（try 体块认领后未发射、静默蒸发）+ C2（循环体内 try 装配序与源码不一致）。

### §1.2 B87 变体二：x04.try_in_with —— handler 臂被祖先区域块集吸收而跳过

- **锚点**：`region_ast_generator.py` `_generate_try` handler 臂块走查的 `_in_other_nested` 守卫。
- **机制（实测确证）**：`with _A() as a: try: with _A() as b: ... except ValueError: R=2` 中，handler 臂块 162（`POP_TOP; LOAD_CONST 2; STORE_FAST R`）同时 ∈ 祖先 WithRegion(0).blocks（CPython 异常传播路径上 with 退出清理共享该块）。`_in_other_nested` 守卫按「块 ∈ 某嵌套 Loop/If/With/TernaryRegion.blocks → 该区域拥有、跳过发射」处理；既有的祖先豁免 `region.entry in nr.blocks` 因块 34（try 头）∉ WithRegion(0).blocks（区域块集非完备超集）而失效 → 臂块被静默跳过，发射 `except ValueError: pass`。parent 链实测：try(34).parent = With(0)。
- **违反条款**：C1（handler 臂块认领后未发射）+ C3（块集重叠的祖先语义未被守卫区分）。

### §1.3 B87 变体三：c04.CTryNest —— try-else 臂被误标 finally 内联副本（keep=0）而蒸发

- **锚点**：`region_analyzer.py` `_collect_finally_body_blocks` 内联 finally 副本检测（指令匹配段）。
- **机制（实测确证）**：外层 finally（`LEAF = 6`）异常路径副本块（PUSH_EXC_INFO..RERAISE 之间）的指令签名按**纯 opname 序列** `(LOAD_CONST, STORE_NAME)` 提取；块 68（else 臂 `OUT = 5; JUMP_FORWARD`）剥噪后 opname 序列含该前缀且以 JUMP_FORWARD 终结 → 被误标 `finally_copy_blocks[68] = 0` → `_generate_try_body` 按 `_fc_keep == 0` 整体跳过，`OUT = 5` 蒸发。opname 序列 `(LOAD_CONST, STORE_*)` 对任意「常量赋值 + 跳转」块都成立，判据不封闭。
- **违反条款**：C1（用户语句块被误抑制、静默蒸发）。

### §1.4 B89 残余：m12 `X` 语句 —— 分组 boolop 重建把外层 or 操作数并入内层 and 组

- **锚点**：`region_ast_generator.py` `_build_grouped_boolop_expression` 链内 fall-through 吸收段（Phase 7 fix）。
- **机制（实测确证，修正评审 B89 草案的表述）**：`X = (_F and 1) or (_G and 2) or 3` 的 BoolOpRegion（entry=16）op_chain = [blk16(and), blk22(or), blk26(and), blk30(or)]，分组检测命中（blk16 跳转目标 26 为链块）走 `_build_grouped_boolop_expression`。末链块 blk30 的 fall-through 块 34（`LOAD_CONST 3`）同时是 blk26 的短路跳转目标（`POP_JUMP_FORWARD_IF_FALSE → 34`，or 链下一操作数入口）。Phase 7 链内吸收判据未排除「候选块是链内其他块的跳转目标」→ `3` 被并入内层 and 组（产出 `and([_G, 2, 3])`，终态 and 组同时含外层操作数），且同一 `3` 又经末尾 fall-through 处理作为外层末操作数再发射一次 → 产物 `X = _F and 1 or _G and 2 and 3 or 3`，重编译时 `2 and 3` 常量折叠为 `3`，LOAD_CONST 值与原 pyc 不符。评审登记的裸语句泄漏（`_F`/`_A < _B`）已由在途 `_b89_trim_trailing_at_cond_jump` 封闭，本残余为同单元的另一机理。
- **违反条款**：C1（外层操作数被内层组双重归属）+ C2（混合 and/or 链重建与 CPython 求值序不一致）。

### §1.5 在途修复的封闭确认（本批复核，非本会话改动）

| 破口 | 复核证据 |
|---|---|
| B84（del 蒸发） | m01 5/5、m08 2/2 MATCH；c13 del 段已发射 |
| B85（链式/多目标赋值） | m08 2/2、c01 5/5 MATCH |
| B86（多上下文 with） | m07 1/1 MATCH |
| B92（LOAD_CLASSDEREF） | c11 10/10 MATCH |
| B95（await 语句蒸发） | x09 10/10 MATCH |
| x09 SWAP 尾段（FIX_P2 §6.1 移交） | 已由在途 SWAP 尾段守卫封闭（x09 AHost.a2 单元 MATCH） |
| B90（f-string，位 2） | m12 f-string 段逐指令等价（P2 报告），本批 m12 3/3 终证 |
| B91（类体幻影 return → COMPILE_ERROR） | 主体封闭：c06 COMPILE_ERROR 消除（0/0 → 3/4），`if x:` guard 正确发射 |
| B88（尾随 return 归属） | 主体封闭：c02 `return ITEMS` 拉入已消失（残余为 B78 融合）、c13 `return None` 已发射；x08.return_leaf 尾 `return None` 蒸发残余与 B78 纠缠（见 §5） |

---

## §2 修复方案（封闭语义 + I.4 白名单逐项核对）

### §2.1 [B87] 中间循环宿主守卫（`_generate_try_body`，region_ast_generator.py）

在嵌套预循环 `is_nested` 判据追加豁免项：存在 LoopRegion L（L 非 region 非 r）使得 `r.entry ∈ set(L.blocks)` 且 `L.entry ∈ set(region.try_blocks)` 时不预生成——内层 try 归属循环体，由循环体走查经 `_loop_handle_child_region_entry` 整树生成（语句序正确 + 体块不被预消费）。

**I.4 白名单核对**：判据 = 区域成员关系双向包含（内层 entry ∈ 中间循环 blocks ∧ 循环 entry ∈ 本 region try_blocks）+ 区域类型（LoopRegion 结构事实）。黑名单零命中：无文件/函数名白名单、无 start_offset 魔数（无偏移比较）、无跨层反查（同层区域 blocks 成员，合法判据）、无 self 新增跨方法状态（循环局部）、无少发射/深度上限（仅豁免预生成，发射改由循环走查完成，语句总量不减）。

### §2.2 [B87] handler 臂祖先区域豁免（`_generate_try` handler 块走查，region_ast_generator.py）

`_in_other_nested` 判定中，nr 经 parent 链是 region 的祖先时跳过该 nr（继续检查其余区域）：祖先 blocks 含 handler 臂块是异常传播路径的共享块集事实，非生成认领；臂语句归属本 region 的 except_handlers body。

**I.4 白名单核对**：判据 = 区域父子关系（parent 链，区域结构事实）+ 块集成员。黑名单零命中（同 §2.1 口径；无偏移、无宿主/个案分支——对所有「handler 臂块 ∈ 祖先区域块集」形态一致生效）。

### §2.3 [B87] finally 副本签名 argval 化（`_collect_finally_body_blocks`，region_analyzer.py）

内联副本的指令匹配签名由 `tuple(opname)` 改为 `tuple((opname, argval))`，签名端与匹配端同口径；终结 opname 判定相应取对首元素。真副本是同一 finally 体指令序列的复制，opname 与 argval（常量值/名字）逐项相同；`OUT = 5`（5≠6、OUT≠LEAF）不再误匹配。

**I.4 白名单核对**：判据 = 指令 oparg（白名单明列项）。黑名单零命中（同上口径）。非「以少发射换全绿」：匹配收紧只把误标为副本的用户语句块交还唯一归属发射，真副本判定不变（rvC_v1/v2/v3/v4、v_b71 复测逐位一致）。

### §2.4 [B89] 外层操作数边界守卫（`_build_grouped_boolop_expression`，region_ast_generator.py）

Phase 7 链内 fall-through 吸收的候选选择追加排除：候选块起始偏移 ∈ 链块短路跳转目标集合（`op_chain` 各块末跳转 argval）时不吸收——该块是外层链的下一操作数入口，归属外层操作数列表。

**I.4 白名单核对**：判据 = 指令 oparg（跳转目标）+ 链结构。黑名单零命中（同上口径）。非少发射：外层操作数仍由末尾 fall-through 处理发射（发射位从内层组移到外层链，总量不变、归属唯一）。

---

## §3 自测读数表（门禁 1–5 逐项 before/after）

### 门禁 1：破口探针（42 探针，评审基线 → 在途 → 本批终态）

| 探针 | 评审基线 | 在途 | 本批终态 | 失败单元与归属 |
|---|---|---|---|---|
| c01 | 4/5 | 5/5 | 5/5 | —（B85 在途封闭） |
| c02 | 6/7 | 6/7 | 6/7 | CIf.items = B78 存量融合 |
| c03 | 3/4 | 3/4 | 3/4 | CFor = B78 存量 |
| c04 | 5/6 | 5/6 | 5/6 | CTryNest = else 臂 OUT=5 发射位错位（B87 残余，形态由蒸发推进为错位，见 §5） |
| c05/c08/c09/c10/c12/c14/c15 | 全 MATCH | 全 MATCH | 全 MATCH | — |
| c06 | COMPILE_ERROR | 3/4 | 3/4 | CMatchDeep = B81/B74 存量（guard 重构 + 幻影 continue） |
| c07 | 5/6 | 5/6 | 5/6 | third = B78 存量 |
| c11 | 8/10 | 10/10 | 10/10 | —（B92 在途封闭） |
| c13 | 1/3 | 2/3 | 2/3 | boom = B78 存量（return None 已发射） |
| m01 | 4/5 | 5/5 | 5/5 | —（B84 在途封闭） |
| m02 | 2/3 | 2/3 | 2/3 | module = 存量族（体蒸发残余与融合纠缠） |
| m03/m04/m05/m06/m09 | 0/1 | 0/1 | 0/1 | module = B49/B61/B78/B81/B59-61 存量 |
| m07 | 0/1 | 1/1 | 1/1 | —（B86 在途封闭） |
| m08 | 1/2 | 2/2 | 2/2 | —（B84/B85 在途封闭） |
| m10/m11 | 全 MATCH | 全 MATCH | 全 MATCH | — |
| m12 | COMPILE_ERROR | 2/3 | **3/3** | —（B89 残余本批封闭） |
| x01 | 4/7 | 4/7 | 4/7 | if_in_while = B94（移交）；if_in_try = 伪差；if_in_match = B81 存量融合（尾 return 已在产物） |
| x02 | 5/7 | 5/7 | 5/7 | for_in_try = B83 存量；for_in_match = B81 存量融合 |
| x03 | 6/7 | 6/7 | 6/7 | while_in_try = 伪差 |
| x04 | 4/7 | 4/7 | **6/7** | try_in_if = 伪差（try_in_while/try_in_with 本批封闭） |
| x05 | 6/7 | 6/7 | 6/7 | with_in_match = B93（移交） |
| x06/x07 | 全 MATCH | 全 MATCH | 全 MATCH | — |
| x08 | 5/8 | 5/8 | 5/8 | assert_leaf = B56 存量；raise_leaf = B87 变体（搬出 for 体）；return_leaf = B88 残余与 B78 纠缠 |
| x09 | 7/10 | 10/10 | 10/10 | —（B96 位 2 + B95/SWAP 在途封闭） |
| x10 | 2/3 | 2/3 | 2/3 | h_basic = B97（移交）+ B78 + B59-61 纠缠 |
| **合计** | 154/189 | 169/196 | **172/196** | 失败单元逐一可归因（24 真实失败 + 3 伪差 + c06/m12 已转可编译计入） |

负对照 nm01/nm02/nc01/nc02/nx01：全 MATCH（基线保持）✓

### 门禁 2：不越界面保持

- 代码涉改仅 `core/cfg/region_ast_generator.py`、`core/cfg/region_analyzer.py`。
- regen 后 OK.py 变化 vs HEAD：`m12OK`（本批目标封闭）、`x04OK`（本批目标封闭）、`c04OK`（失败形态变化、读数持平）、`m09OK`/`x10OK`/`v_b71_faceOK`（既有失败文件 regen 漂移，读数逐位不变）；其余全部 OK.py 逐字节不变（含全部 MATCH 面与 34 集 6 文件）。
- 过程性回归一次并已修复：§2.3 初版遗漏终结名单元素口径适配导致 rvC_v1/v4 回退，补 `_op = _ops_succ[-1][0]` 后 rvC_v1/v3/v4 恢复 MATCH、rvC_v2 保持基线 FAIL（B83 存量），如实记录。

### 门禁 3：站桩回归面（45 文件，对照 r2_regress_replay.json 基线）

| 面 | 基线 | 本批 | 判定 |
|---|---|---|---|
| r10_04/06/14/15/16/21、rv10_31/32/33、r7_03/07、rv8_01、r8_06 | 全 MATCH | 全 MATCH | 持平 ✓ |
| r7_08 | 7/8（t_host_match_case，B77） | 7/8 同单元 | 持平 ✓ |
| rv8_02 | 6/7（tryfin_then_more，B63） | 6/7 同单元 | 持平 ✓ |
| n6_01/n7_01/n7_02/n8_01/n8_02/n9_01/n9_02/n10_01..04/rv9_03 | 全 MATCH | 全 MATCH | 持平 ✓ |
| v_b46/v_b71/v_b73/v_b74/v_b75 | 1/4、3/4、2/3、3/4、1/3 | 同读数，失败单元逐一相同 | 持平 ✓ |
| v_b50/v_b65/v_b76 | 4/4、3/3、4/4 | 全 MATCH | 持平 ✓ |
| probes_rvC rvC_v1/v3/v4 | MATCH | MATCH | 持平 ✓ |
| probes_rvC rvC_v2 | 1/2 FAIL（drain，B83） | 1/2 FAIL 同单元 | 持平 ✓ |
| quotation.pyc（附加加验） | 152/153（change_his_to_forward） | 152/153 同单元 | 持平 ✓ |

### 门禁 4：34 小测试集抽验 6 文件

| 文件 | 基线 | 本批 | 失败单元 |
|---|---|---|---|
| email_utils | 3/4 | 3/4 | send_email ✓ |
| cgroup_utils | 7/8 | 7/8 | set_cgroup_config ✓ |
| executor | 9/10 | 9/10 | Executor.check_before_trading ✓ |
| strategy_universe | 10/11 | 10/11 | StrategyUniverse._on_clear_de_listed ✓ |
| trading_dates_mixin | 13/14 | 13/14 | TradingDatesMixin.trading_dates_reload ✓ |
| realtime_event_source | 12/13 | 12/13 | RealtimeEventSource.clock_worker ✓ |

### 门禁 5：IV.2 自检

- BOM：region_ast_generator.py / region_analyzer.py 首 3 字节 = `efbbbf`，全文 BOM 计数 = 1（单头保持）✓
- IMPORT_OK：`import core.cfg.region_ast_generator` / `core.cfg.region_analyzer` ✓
- COMPILE_OK：m12 3/3、x04 6/7、c04 5/6 产物 compile 通过（pyc_verify 内含重编译比对）✓
- 插桩：新增行 grep `print(|breakpoint(|import pdb|pdb.set_trace` = 0 ✓
- 禁止前缀：新增行 grep `_fix_|_patch_|_fallback_|_hack_|_workaround_|_temp_` = 0；新增方法 0（全部为既有方法内守卫/判据收窄）✓
- 影响面：见门禁 2（字节级证据，MATCH 面 OK.py 零漂移）✓
- 判据合规：全部判据落在区域成员关系 / 区域父子关系 / 指令 oparg / 跳转目标集合，无名字白名单、无 start_offset 魔数、无深度/计数上限、无 self 新增跨方法状态 ✓

---

## §4 触及方法 docstring 更新说明（I.7 六项模板 + C1/C2/C3）

| 方法 | 文件 | 变更 | 说明 |
|---|---|---|---|
| `_generate_try_body` | region_ast_generator.py | docstring 追加 [B87] 中间循环宿主守卫条目 | 输入契约段补充豁免判据、误发射机制（x04.try_in_while 实测）、C1/C2/C3 条款 |
| `_generate_try` | region_ast_generator.py | docstring 输入契约段追加 [B87] handler 臂祖先区域豁免条目 | 共享块集事实 vs 生成认领的区分、C1/C3 条款 |
| `_build_grouped_boolop_expression` | region_ast_generator.py | docstring 追加【B89 外层操作数边界守卫】段 | m12 实测机理、判据口径（oparg 事实）、C1/C2/C3 条款 |
| `_collect_finally_body_blocks` | region_analyzer.py | **新增完整 docstring**（原缺失） | 按 I.7 六项（算法依据/识别条件/归约方式/嵌套处理/入口引用语义/流程位置）+ [B87] argval 签名条目 + C1/C2/C3 |

代码注释与 docstring 声明一致：每处守卫的代码注释标明 [B87]/[B89]、实测复现单元与判据白名单口径。

## §5 落地声明（I.6）

**代码已落地**。落地标记：`core/cfg/region_ast_generator.py` 内 `_generate_try_body` 的 `_is_inside_intermediate_loop` 守卫、`_generate_try` handler 块走查的 `_nr_is_ancestor` 豁免、`_build_grouped_boolop_expression` 的 `_bo_chain_jump_targets` 排除项（grep 可复核）；`core/cfg/region_analyzer.py` 内 `_collect_finally_body_blocks` 的 `_ops`/`_ops_succ` argval 化签名与 `_op` 取首元素适配。m12 3/3、x04 6/7（try_in_while/try_in_with 转 MATCH）为落地实证。

## §6 遗留观察项（如实说明，含移交清单）

1. **B87 残余（c04.CTryNest，读数持平）**：副本签名 argval 化后 `OUT = 5` 已恢复发射，但发射位落入内层 try 体（异常表随之改变：OUT=5 被内层 handler 覆盖）。机制：外层 TRY_EXCEPT(46) 的区域分解本身与源码结构错位（try_blocks=[66,68,92,94] 含 else 臂、has_else=False），发射序修复需上溯 region_analyzer 的 try/else/finally 嵌套区域构造（位 1 域）。已试方案：R19N2 post-try 收集 owner 检查（块 68 归属外层 46，该路径未触发）；后续应从区域分解入手。锚点：region_analyzer `_identify_try_except_regions`（try-else-finally 三件套嵌套形态）。
2. **B88 残余（x08.return_leaf）**：尾随 `return None`（函数级，for 宿主后）蒸发，单元同时含 B78 融合（`if i: while i:` → `while i and i:`），单修 return 发射无法转 MATCH，移交至 B78 封闭批次一并验证。锚点：region_ast_generator 尾声内联区 + 循环装配序。
3. **B97（x10.h_basic，移交）**：handler 臂内 `break` 蒸发。评审 §5.1 判据（BlockSemantics.is_break 事实 + B71 边类型守卫域从 finally 扩展到 handler 臂）方向确认有效，但该单元同时含 B78 融合、B59-61 match 装配错位与 else 臂 `E = 0` 蒸发（B87 族），单独封闭 B97 无法使单元转 MATCH；且 break 块在现有走查中未到达 BREAK 角色分支（先被块集重叠守卫拦截）。移交至 B78/B59-61 族封闭批次，届时按 `BlockRole.BREAK/PURE_BREAK` 角色判据在 handler 块走查前置位补发 Break。
4. **B93（x05.with_in_match，位 1 移交）**：match 叶被幻影 `with _A() as a` 镜像替换（外层兄弟区域副本）。锚点 region_analyzer `_identify_match_regions`（:12920）+ 区域父子认领；封闭方向 = 子区域入口同一性 + 区域成员关系唯一守卫（禁止兄弟区域副本替换）。本批未动（超批体量：需识别层区域认领结构调整）。
5. **B94（x01.if_in_while，位 1 移交）**：NOP 残段假循环。实测：原 pyc 循环体块 `LOAD_CONST 1; STORE R; JUMP_BACKWARD→8`（跳转目标为 NOP 残段）在产物中重建为 `while False: pass` 幻影 + 体蒸发（仅剩裸回边）。锚点 region_analyzer 假循环过滤/role 修正区（:5011-5054）；封闭方向 = 回边目标 + POP_JUMP_BACKWARD 块末 opcode 双事实，跳转目标 NOP 块不得作为循环头证据。本批未动（同上）。
6. **在途预生成未登记 `_generated_regions`**：`_generate_try_body` 嵌套预循环 `_generate_try(ntr)` 后未 `add(id(ntr))`，依赖块级 generated 标记兜底（本批监视实测二次生成路径存在）。当前无读数影响（块标记已防双份发射），登记为观察项：后续若块标记被回滚语义（`generated_blocks -= ...`）清除，可能复现双份生成。
7. **存量族**：c02/c03/c07/c13/m02/m03/m04/m05/m06/m09/x01/x02/x08/x10 的其余失败单元全部归 B78/B81/B83/B56/B49/B59-61/B61 存量（评审 §4.2 已登记宿主外推证据），非本批新增破口；3 伪差单元（x01.if_in_try、x03.while_in_try、x04.try_in_if）为探针退化（评审 §4.3 口径）。
8. **临时脚本清理**：round2 目录内 tmp_p3_*.py、tmp_*_b94.py、tmp_dump/tmp_trace/tmp_split 及全部 tmp_p3_*.json 中间读数已删除（git 历史 3a9db846 已存证）；终态证据保留为 `p3_probe_final.json`（42 探针）与 `p3_regress_final.json`（站桩 45 文件）。

---

## §7 复核整改记录（Round 2 复核打回窄口径整改，依据 REVIEW2.md）

整改范围：仅 REVIEW2.md §0 打回的两项（I.5 命名前缀违反 + I.7 docstring 部分缺口），无任何算法改动。

### 7.1 I.5 整改：方法重命名

- `_merge_annassign_statements` → **`_combine_annassign_statements`**（避开全部禁止前缀 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`），位置 `core/cfg/region_ast_generator.py`，共 3 处：def（:32776）+ 2 调用点（:32671、:50754）；docstring 内自引用同步更新。
- 本文件未出现旧名（grep 复核 0 命中）；落地标记名随本节同步更新为 `_combine_annassign_statements`。
- 自检口径缺口同步：门禁 5 的禁止前缀 grep 现覆盖 `_fix_|_merge_|_patch_|_fallback_|_hack_|_workaround_|_temp_` 七项（补 `_merge_` 项）；既有豁免仍仅覆盖存量 `_merge_block_is_*`（:19937/:40760），本批无新增禁止前缀方法。

### 7.2 I.7 整改：4 个 `_generate_*` 方法 docstring 补齐六项模板 + C1/C2/C3

| 方法 | 位置 | 变更 |
|---|---|---|
| `_generate_region` | region_ast_generator.py | **新增完整 docstring**（原缺失，仅代码内注释承载）：六项模板 + [B87] 早退守卫唯一归属判定 + [R2-With]/[R59-B] merge_block 双角色入口 + C1/C2/C3 |
| `_generate_try_body` | region_ast_generator.py | docstring 标题后插入六项模板块 + C 条款（既有嵌套派发判据与 [B87] 条目保留不动） |
| `_generate_with` | region_ast_generator.py | docstring 标题后插入六项模板块 + C 条款（既有输入契约/AST 映射/R08b/R10-W10 段保留不动） |
| `_generate_block_statements` | region_ast_generator.py | docstring 插入六项模板块 + C 条款（[B86-phantom] 单一漏斗 / AnnAssign 归并 / 伪影剔除 / B32 / R55 收口口径） |
| `_generate_block_statements_body` | region_ast_generator.py | docstring 插入六项模板块 + C 条款（跨块守卫分流 / GET_ITER 抽象节点 / R11 / C1/C2/C3） |

全部六项内容以方法体真实算法为准撰写（与代码行为一致），对照 `_generate_try`/`_generate_assert` 的既有合规 docstring 风格。

### 7.3 整改后自测（smoked 级）

| # | 自测项 | 读数 | 判定 |
|---|---|---|---|
| 1 | `import core.cfg.region_ast_generator` | IMPORT_OK | ✓ |
| 2 | BOM：region_ast_generator.py 首 3 字节 | `efbbbf` 保持 | ✓ |
| 3a | 探针 m08（B85 AnnAssign 面）regen+verify | **2/2 MATCH（保持）** | ✓ |
| 3b | 探针 m12 regen+verify | **3/3 MATCH（持平）** | ✓ |
| 3c | 探针 c01 regen+verify | **5/5 MATCH（持平）** | ✓ |
| 3d | 负对照 nc01 regen+verify | **4/4 MATCH（保持 MATCH）** | ✓ |
| 4 | grep `_merge_annassign_statements` 全树（*.py/*.md，排除评审文档本身） | **0 命中** | ✓ |
| 4b | grep `def (_fix_\|_merge_\|...)\` 七前缀 | 仅存量豁免 `_merge_block_is_*` 2 处，0 新增 | ✓ |
| 5 | `git status --porcelain` 跟踪文件 | 仅 `core/cfg/region_ast_generator.py` + 本文件（FIX_P3.md）变化；regen 产物字节级可复现（4 探针 OK.py 零漂移） | ✓ |

smoked 结论：重命名与 docstring 整改零读数回归，工作树变化面收窄于两文件，落地声明同步完成。

---

## §8 回退拦截整改（create_user_code_iqe 跨文件状态污染）

> Round 2 修复工程师（Round 2 追加批次）：主代理发现 shard1 batch 读数 461/469（基线 462/469），
> `IQCommon/util/trade_info_utils.pyc` 的 `<module>.create_user_code_iqe` 在 batch 方法学下
> Different bytecode（文件 36/41→35/41）。本节记录二分定位、根因证伪与修复。

### 8.1 现象复核与「batch 上下文专属」假象证伪

主代理登记的现象描述为「batch 同进程顺序状态污染」（嫌疑：`_generated_regions` 预生成登记的
跨文件泄漏）。实测复核**证伪跨文件状态污染**：

1. **隔离读数实测 = 35/41 而非登记的 36/41**：`pyc_verify.py single`（compare 现存 OK.py）与
   `pycdc.py` 独立进程重新反编译 + single，读数一致均为 35/41（create_user_code_iqe
   Different bytecode）。隔离与 batch 无读数差异。
2. **regen 逐文件独立进程**：`verify_driver.py regen` 对每个 pyc 单独 `subprocess.run`
   （verify_driver.py:35-47），反编译器不存在跨文件进程内状态；`pyc_verify.py batch` 仅做
   compare（py_compile + 判据），不执行反编译。
3. **真因 = 验证时序的产物版本错位**：隔离验证跑在 HEAD 提交内的 OK.py（round1 终态产物，
   36/41）上；batch 验证序先 regen（用 round2 代码重写全部 OK.py）再 verify，读的是 round2
   产物（35/41）。看似「batch 专属」，实为 round2 代码的确定性反编译行为回退，与进程状态、
   文件顺序无关（`_generated_regions` 为实例属性 per-file 新建，上一轮评审观察项排除）。

### 8.2 二分证据链

| 步骤 | 方法 | 结果 |
|---|---|---|
| 1 | shard1 batch（HEAD，51 文件） | 461/469，trade_info_utils 35/41（create_user_code_iqe Different bytecode） |
| 2 | 基线 shard1_report.json 同文件 | 36/41，失败 5 单元（无 create_user_code_iqe） |
| 3 | 独立进程反编译 + single（HEAD） | 35/41 —— 排除 batch/顺序因素 |
| 4 | git worktree @87e59c49（de039b80 前）反编译 | `user_code = f'...'` 整体 f-string 字面量（基线形态） |
| 5 | git worktree @de039b80（P2）反编译 | `user_code = ''.join([...])` join 列表形态 —— **P2 单独即引入** |
| 6 | round2 输出 diff round1 输出 | 仅 create_user_code_iqe 的 user_code 一处（f-string → ''.join） |

提交区间收窄到 de039b80（P2：ast_converter.py / comprehension_generator.py）；
P3（3a9db846/fd04c276）不涉及。

### 8.3 根因（锚点 + 机制 + 违反条款）

**锚点**：
- `core/cfg/ast_converter.py`（de039b80 引入，修复前行号 1481-1507）：`_convert_formatted_value_expr`
  ——B90 分发项把 `'FormattedValue'` 分发从 `_convert_formatted_value_full`（裸 FV）改为
  单字段 `ASTJoinedStr` 包裹（`ASTJoinedStr(values=[fv])`，无形态标记）。
- `core/cfg/code_generator.py:4295-4307`（修复前）：`_generate_call` 的
  `''.join([Constant, FormattedValue, ...]) → f-string` 拼接归一恢复判据
  `has_fv = any(isinstance(e, ASTFormattedValue))`。

**机制**：reconstructor 对 BUILD_STRING 的表达层重建形态是 `''.join([...])` Call dict，
列表元素为裸 `FormattedValue` dict；发射端据「元素含裸 FV = 拼接片段事实」归一为整体
f-string（重编译恢复原 FORMAT_VALUE+BUILD_STRING 指令流）。B90 包裹改动使所有经
`_convert_expression` 分发的 FV（含 join 列表元素位）变成单字段 `ASTJoinedStr`，裸 FV
事实被遮蔽 → has_fv 判 False → 恢复失效 → 整体发射 `''.join([...])` 源码 → 重编译
BUILD_LIST+CALL 指令流 ≠ 原文 → Different bytecode。AST 层实测（探针）：join 列表 65 元素
全为 `ASTConstant / JS[ASTFormattedValue]` 交替，0 个裸 FV。真实用户码
`''.join([f'{x}', ...])`（元素为 JoinedStr dict）在 round1/round2 均不归一，行为未变。

**违反条款**：
- **C2**（转换层产出与发射端消费判据一致）：B90 包裹改变了拼接列表元素的 AST 形态，
  发射端 join 归一判据（has_fv）未同步，两端口径脱节，恢复通路静默失效。
- **C1**（用户语句形态保真）：既有 success 单元（create_user_code_iqe）的发射形态被
  转换层内部表示变化静默改变（整体 f-string → join 源码），用户级形态蒸发。
- I.4-④（方法/节点状态口径）：包裹产物无区分信号，接收方（发射端）无法按原语义消费——
  修复补齐节点元数据口径（见 8.4）。

### 8.4 修复语义（封闭，非个案补丁）

修复方向 = 恢复「转换层包裹」与「发射端拼接归一」两端的口径一致（C2 闭合），
B90 守卫本身不删：

1. `core/cfg/ast_converter.py::_convert_formatted_value_expr`：包裹产物携带内部元数据
   `_b90_wrapped = True`（AST 节点属性，I.4 白名单「节点元数据」判据；ASTJoinedStr 无
   `__slots__` 约束，属性写入合法）。docstring 六项同步（[Round2-RG1] 注记）。
2. `core/cfg/code_generator.py::_generate_call`：join 拼接归一前，对携带 `_b90_wrapped`
   且 `_values` 恰一个 ASTFormattedValue 的元素还原为裸 FV，再做 has_fv 判定与
   ASTJoinedStr 归一；无标记的 JoinedStr（用户码 f-string 字面量元素）不解包，维持
   round1 的「拼接片段 vs 用户 f-string 字面量」区分语义（真实 join 调用不误归一）；
   判据不命中维持既有发射路径（C3）。docstring 六项模板补齐（本方法此前为单行 docstring）。
3. 禁忌核对：无函数名/文件名白名单（`attr == 'join'` 为既有恢复判据，未新增）、无
   start_offset 魔数、无个案补丁（判据 = 节点元数据 + 结构事实，对全部 BUILD_STRING
   重建形态生效）、无深度特判；`_b90_wrapped` 为 AST 节点属性非 self 方法状态（G0）。

### 8.5 修复后输出一致性

`pycdc.py`（修复后 HEAD）反编译 trade_info_utils 与 worktree@87e59c49（round1 终态）
输出 **diff 逐字节一致**（仅 user_code 处恢复整体 f-string；文件内另一处真实
`''.join([Constant, Call, Subscript])` 用户调用保持不归一）。

### 8.6 自测读数（门禁 1–6 before/after）

| # | 门禁 | before（HEAD 修复前） | after（修复后） | 判定 |
|---|---|---|---|---|
| 1 | shard1 batch（regen 51 文件后 verify） | 461/469 | **462/469**；trade_info_utils 36/41，失败单元回到基线（trade_operation/kill_trade_process/get_trade_status/query_trade_strategy_info/query_strategy_id + email_utils 1 + api_base 1） | ✓ |
| 2 | trade_info_utils 隔离 single | 35/41 | **36/41**（基线 5 失败单元，无 create_user_code_iqe） | ✓ |
| 3 | 42 探针 regen+verify | 172/196 | **172/196 逐位一致**（m01 5/5、m07 1/1、m08 2/2、m12 3/3、c01 5/5、c06 3/4、c11 10/10、x04 6/7、x09 10/10；负对照 nm01 3/3、nc01 4/4、nx01 7/7 全 MATCH） | ✓ |
| 4 | 34 集抽验 3 文件（regen 后 single） | — | email_utils **3/4**、cgroup_utils **7/8**、executor **9/10**（基线同读数） | ✓ |
| 5 | IV.2 | — | BOM 单头：region_analyzer/region_ast_generator 首 3 字节 `efbbbf` 保持；IMPORT_OK：42 探针 regen+verify 全过（`import` 通路零异常）；COMPILE_OK：shard1 batch compile_error=0、修复产物 compile 通过（compare 通路）；插桩残留：git diff core/ 中 `print(/breakpoint(/pdb` 新增 **0**；新增 def **0**（无禁止前缀方法）；ast.parse 两改动文件通过 | ✓ |
| 6 | shard4 抽验 batch | 基线 848/855 | **848/855**（regen 51 文件后 batch，与基线一致） | ✓ |

### 8.7 落地声明（I.6）

**代码已落地**：`core/cfg/ast_converter.py`（+16/-2）、`core/cfg/code_generator.py`
（+42/-3，含 `_generate_call` docstring 六项补齐）。工作树无调试脚本/临时文件残留
（探针脚本全部位于 D:/Temp，工作区外）。未 git commit（移交主代理）。
