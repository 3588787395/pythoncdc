# Round 9 复核报告（复核工程师 · 任务 9.3 / REVIEW2.md）

- 复核人：复核工程师（独立对抗角色，零容忍立场）
- 日期：2026-10-04
- 复核对象：修复批次 `1624ef6d`（含在途算法快照 `be58c97d`，净效果 = `git diff d8246a8e 1624ef6d -- core/`）
- 唯一判据：`python scripts/pyc_verify.py batch --json <输出> <pyc...>`（pylingual compare_pyc，Python 3.11.7）；全部输出落 `rounds/round9/` 下 `rv9_` 前缀新文件，零覆盖修复 JSON
- 归因手段：`git worktree` @ `d8246a8e`（评审批次基线）独立目录 `D:/Temp/r9_rev`，实测后已移除（见 §6 注记 1）

## 终判：**放行**

修复零回归成立（变体攻击 post-fail 集合 ⊂ pre-fail 集合，无任何 MATCH→MISMATCH；四组复验面逐位持平）；B66/B67/B68 三破口封闭经独立复跑证实（r9 攻击面 5 MISMATCH 全转 MATCH 且负对照保持，另在任务书外的 2 个边界变体上额外 +2 补强）；逐 hunk 审计未发现任何判据违规（无名字/文件白名单、无魔法阈值、无跨层回溯、无新增 self 跨方法状态、无以少发射换全绿）；docstring 三要素与 C1/C2/C3 条款与代码逐字一致；红线四项全过。残留 2 个 MISMATCH 单元经 pre-fix worktree 同败证实为既有缺口结构变体（新登记 B69/B70 交后续），不构成打回条款。FIX.md 两处文档偏差为记录层面（见 §5），非 docstring-代码不一致，不构成打回。

---

## §1 逐 hunk 对抗审计表（`git diff d8246a8e 1624ef6d -- core/` 全量 8 hunk）

| # | 文件:行（现行） | 内容 | 判据来源审查 | 结论 |
|---|---|---|---|---|
| H1 | region_analyzer.py:1 | 单 BOM 恢复（be58c97d 双 BOM → 单 BOM） | 提交树字节证实：be58c97d = `efbbbfefbbbf222222`（双 BOM 不可运行），d8246a8e 与 1624ef6d 头 9 字节逐字节一致 = `efbbbf222222` | PASS |
| H2 | region_analyzer.py:8417-8449 | [B68 fix] 种子收窄：finally_blocks 全为异常机制块（门控）时，帧跳落点为条件分支头（末指令 ∈ CONDITIONAL_JUMP_OPS）或含 FOR_ITER 者不入 try-finally 跨度 | 判据全为同层块结构事实（末指令 opcode、块内 FOR_ITER 扫描）；门控引用既有常量 CONDITIONAL_JUMP_OPS（:49 = POP_JUMP_* 全族，无魔法值）；**门控互斥完备**：非空 finally 必发射 machinery 集外 opcode（LOAD_*/CALL/STORE/RETURN_*）→ 门关断走原种子收集（W21 保护面），独立复跑 trade_info_utils 36/41 持平证实 | PASS |
| H3 | region_analyzer.py:9696-9727 | [B68 fix] try_start 回扩收窄：取「start_offset < try_start 且末指令 JUMP_FORWARD 且 argval > handler_start」最大偏移帧跳块；无则不回扩 | 判据对象为区域自身边界（handler_start）而非硬编码常量；内联注释自带识别条件/归约方式/AST 映射三段，与代码逐条核对一致；无跨层回溯（只在同层块序内选择） | PASS |
| H4 | region_analyzer.py:27724-27758 | [B67 fix] for 迭代目标 STORE 豁免：块首非噪声指令为 STORE_* 且某普通前驱以 FOR_ITER/GET_ANEXT/GET_AITER 收尾 → 该 offset 入豁免集 | 判据 = 块首 opcode + 前驱末 opcode（同层事实）；**offset 精确豁免**（仅豁免目标绑定那一条 STORE，同块内真 body 赋值不受豁免）；async for（GET_AITER/GET_ANEXT）覆盖；unpacking 目标（UNPACK_SEQUENCE 打头）不豁免 = 维持原行为无回归；内联注释三要素与代码一致，C1/C2/C3 成立 | PASS |
| H5 | region_ast_generator.py:3106-3264 | 新方法 `_b68_is_tryfin_tail_releasable`（156 行） | 六重门控全部为同层区域字段/块属性：has_finally、finally_copy_blocks 空（Dict 真值判断，:794 字段证实）、start_offset ≥ try_offset_end、结构成员集合排除（try/else/finally/cleanup/handler/except_handlers/finally_copy.keys()）、无异常机制指令、末 meaningful 指令非 BACKWARD_JUMP_OPS（:138 既有导入）、非 loop_header（basic_block.py:79 真实字段）；无 region_analyzer 访问（C2 成立）；docstring 识别条件 3 条/机制/归约方式/AST 映射与代码逐字一致 | PASS |
| H6 | region_ast_generator.py:3191-3282 | 新方法 `_b66_is_with_exit_continue_chain_head`（72 行） | 四重判据：循环帧（self._current_loop）、链头剥噪无语句、唯一非异常后继满足退出回边签名（末指令 JUMP_BACKWARD[_NO_INTERRUPT] 目标=当前循环 header + 清理调用内容签名）+ WithRegion 成员锚定（红线明列允许的「区域成员关系」）；**内容签名与既有 `_is_with_exit_back_edge`（:12496-12502）逐 opcode 同一元组**，docstring「与 _is_with_exit_back_edge 的内容签名一致」核实为真；`region_analyzer.regions` 仅只读成员查询（C2 成立）；非 with 特判——判据是「with 装配后角色形态」的结构外推（链头 NOP + 退出回边后继两点式），排除 `if c: f(None,None,None); continue` 同形状普通调用由第 4 判据完成 | PASS |
| H7 | region_ast_generator.py:8553 / 13488 / 13519 / 29999 | [B68] 4 处装配守卫调用点 | :8553 位于 `_loop_handle_child_region_entry` 的 `isinstance(_target_region, TryExceptRegion)` 显式门控内（:8552）；:13488/:13519 位于 `isinstance(entry_region, TryExceptRegion)` 分支内（:13475 等）；:29999 位于 `_generate_try(self, region: TryExceptRegion)` 类型签名内；**反向修复合规**——守卫是「跳过毯式标记、交还宿主派发」，字节级比对证明释放块被宿主正常再发射，非少发射 | PASS |
| H8 | region_ast_generator.py:30325 / 52125 | [B66] 2 处装配守卫调用点 | 均位于孤立边界 NOP 分支内、先于幻影 `while False` 判定（:30315/:52115 附近），两站点逻辑逐字相同；命中即发射 Continue 并登记链头+退出块，与 docstring「归约方式」一致 | PASS |

**审计结论**：8/8 PASS。零白名单、零魔法阈值、零跨层跨区域回溯修正、零新增 self 跨方法状态（两新方法均为纯判定函数）、零以少发射换全绿。

## §2 docstring 三要素与 C1/C2/C3 条款核验

| 项 | 识别条件 | 归约方式 | AST 映射 | C1 | C2 | C3 | 判定 |
|---|---|---|---|---|---|---|---|
| `_b68_is_tryfin_tail_releasable`（:3111-3140 docstring） | 3 条编号，与代码六重门控逐条对应 | 「仅判定（毯式标记跳过），释放块由归属区域派发」= 与 4 调用点 `continue` 语义一致 | 「无（归属修正）」= 一致 | 声明「只来自同层块对象结构事实」= 代码只触 region 自身字段/块属性 ✓ | 声明「无跨层/跨区域回溯」= 方法体零 region_analyzer 访问 ✓ | 声明「无名字/文件名特判」= 无字符串比较 ✓ | **一致** |
| `_b66_is_with_exit_continue_chain_head`（:3196-3219 docstring） | 4 条编号，与代码四重判据逐条对应 | 「then 臂发射 Continue 并登记链头+退出块已生成」= 与 H8 两站点逐字一致 | ast.Continue = 一致 | 同层事实（含 WithRegion 成员关系）✓ | 声明「regions 仅作成员关系查询、不改写归属」= 代码只读遍历 ✓ | 无名字特判 ✓ | **一致** |
| B67 内联注释（region_analyzer.py:27724-27734） | 识别条件（块首 STORE_* + FOR_ITER/GET_ANEXT/GET_AITER 前驱）与代码一致 | 「豁免后交既有 B1b 边汇聚判据」= 与豁免集合注入 `_sb_has_body` 一致 | 「单个 BoolOpRegion→BoolOp 条件」路径声明完整 | opcode+前驱集合 ✓ | 无跨层回溯 ✓ | 无名字特判 ✓ | **一致**（非独立方法无 docstring 载体，条款在 FIX.md §4 存档，合规） |

## §3 读数独立复跑表（不信任修复自报，唯一判据全量重跑）

| # | 面 | 期望 | 独立实测（rv9_ JSON） | 判定 |
|---|---|---|---|---|
| a | r9 攻击面 12 pyc（r9_01..10 + n9_01/02） | 50/50 | **50/50**（12/12 文件 success，`rv9_r9face.json`） | ✓ |
| b | round6 全量 16 pyc（r6_01..15 + n6_01） | 115/115 | **115/115**（16/16 success，`rv9_r6.json`） | ✓ |
| c | rv8 3 pyc | 18/20 | **18/20**（rv8_01 6/7、rv8_02 6/7、rv8_03 6/6，`rv9_rv8.json`；失败 = chain_value_boolop / tryfin_then_more，与 B65/B63 登记面一致；with_body_tryfin_chain 经 B68 修复转 MATCH） | ✓ |
| d | quotation 基线（site-packages/fly/data/quotation.pyc） | 152/153（唯一失败 change_his_to_forward） | **152/153**，唯一失败 = change_his_to_forward（`rv9_quote.json`） | ✓ |

交叉验证：修复工程师落盘 `rv8_check.json` 实测 18/20（failure = rv8_01 6/7 + rv8_02 6/7），与交接词「17/20」不符、与 FIX.md §5e「笔误更正」声明一致——更正属实。

## §4 变体攻击（新守卫边界外推，rv9_ 前缀 3 探针 14 单元）

探针：`test_repros/round9/rv9_01_b68_nonfin_tail.py|.pyc|OK.py`、`rv9_02_b66_with_nest.*`、`rv9_03_b67_mixed_chain.*`（py_compile 3.11.7 编译 + `pycdc.py -o` 生成 OK，零手改）；报告 = `rounds/round9/rv9_probes.json`。

### 4.1 攻击读数（post-fix 主树 @ 1624ef6d）

| 探针 | 攻击点 | 单元读数 | 明细 |
|---|---|---|---|
| rv9_01_b68_nonfin_tail | B68 边界：非空 finally + 尾随 break/continue（守卫应收窄拒绝）；空 finally + 尾随 if-else 双臂 return；空 finally 嵌套 if 宿主 | **4/5** | nonfin_tail_break MATCH、nonfin_tail_cont MATCH（非空 finally 内容零泄漏/零蒸发）、emptyfin_ifelse_ret MATCH（**+1 补强**）；emptyfin_in_if MISMATCH（§4.2） |
| rv9_02_b66_with_nest | B66 边界：with 内嵌套循环 continue（跨层归属）；with 内 continue 无 else 臂；with 作整个循环体（误触发边界 ×2） | **4/5** | cont_in_with_nested_loop MATCH（跨层归属正确）、cont_in_with_no_else MATCH（**+1 补强**）、with_whole_body_pass MATCH（B66 守卫未误触发）；while_with_whole_body MISMATCH（§4.2） |
| rv9_03_b67_mixed_chain | B67 边界：`a or b and c` 混合链、3 成员纯 and 链、双重否定守卫 | **4/4** | 全 MATCH，链不拆裂、无多余 continue、极性正确 |
| **合计** | 3 探针 | **12/14** | post-fail = {emptyfin_in_if, while_with_whole_body} |

### 4.2 pre-fix 归因（worktree @ d8246a8e，`D:/Temp/r9_rev/rv9_pre_d8246.json`）

**归因点说明（诚实记录）**：任务书建议归因点 `1624ef6d^` = `be58c97d`，但其**提交树本身为双 BOM**（`git cat-file blob be58c97d:core/cfg/region_analyzer.py` 首 6 字节 = `efbbbfefbbbf`，import 必然 SyntaxError），不可运行；改用 `d8246a8e`（评审批次基线，其 core 与合规基线 `201234ab` 零差异，见 REVIEW.md §1 A1）作为 pre-fix 对照点，归因面纯净。

| 单元 | pre-fix @ d8246a8e | post-fix @ 1624ef6d | 归因 |
|---|---|---|---|
| emptyfin_ifelse_ret | MISMATCH（Different control flow；if/else 双臂 return 整段塌缩进 try 体） | **MATCH** | **本轮修复收益** |
| cont_in_with_no_else | MISMATCH（Different control flow） | **MATCH** | **本轮修复收益** |
| emptyfin_in_if | MISMATCH（Different control flow；try/finally 与 if 宿主倒置 + 臂内 return 6 蒸发） | MISMATCH（Different bytecode；臂内 return 6 仍蒸发） | **pre-fix 同败既有缺口**（B63/B64 族 if 宿主变体，非本轮引入） |
| while_with_whole_body | MISMATCH（Different control flow；`while True: with: pass` → 幻影 `break`，函数体逐字节与 post-fix 相同） | MISMATCH（同签名同产物） | **pre-fix 逐字节同败既有缺口**（与 B66 无关——B66 只发射 Continue，幻影 break 出自既有 while+with 装配面） |

**结论**：post-fail 集合 ⊂ pre-fail 集合（10/14 → 12/14，**+2 补强、零回归**），无任何 MATCH→MISMATCH 漂移。两残留 MISMATCH 依纪律登记新破口（§5 B69/B70），不构成打回。

### 4.3 形态注记

- `cont_in_with_nested_loop` 产物含一条显式尾随 `continue`（内层 for 末），但单元 MATCH——该显式 continue 与 for 隐式回边编译为同一 JUMP_BACKWARD，字节级等价，compare_pyc 判等通过，属形态噪声非缺陷，不登记破口。
- B66 守卫在 with 作整个循环体的两个边界形态上未误触发（with_whole_body_pass MATCH；while_with_whole_body 的失败产物是幻影 break 而非 B66 的 Continue 发射）。

## §5 新登记破口（既有缺口沿袭，交后续批次）与残留观察

| 编号 | 内容 | 证据 | 优先级 |
|---|---|---|---|
| **B69** | if 宿主臂内空 try/finally 吞臂内尾随 return + 结构倒置（B63/B64/B68 族的 if 宿主变体）：`if a: try: pass / finally: pass / return 6 / return 7` → 臂内 return 6 蒸发。rv9_01 emptyfin_in_if；pre-fix（d8246a8e）control-flow 倒置同败、post-fix bytecode 蒸发同败，失败形态同根，非本轮引入 | rv9_probes.json + rv9_pre_d8246.json | P2 |
| **B70** | `while True:` + with 整体宿主幻影 `break`：`while True: with open(p) as f: pass`（尾随不可达 return）→ 产物 with 体内多出 `break`，控制流改变。rv9_02 while_with_whole_body；pre-fix 产物逐字节相同同败，与 B66/B68 判据无关 | rv9_probes.json + rv9_pre_d8246.json | P2 |
| R-1 | B68 门控 opcode 集的理论重叠面：`finally: continue/break`（体仅 POP_TOP + JUMP_*，全落 machinery 集）会被判为「空 finally」而进入收窄/释放判据；无测试面覆盖、未证实实际产损，登记为边界观察项供后续轮探测（探针建议：含 `finally: continue` 的循环宿主形态） | 本复核 §1 H2 机制分析 | 观察 |
| D-1 | FIX.md 文档偏差（非阻塞）：①§2 称 B68「3 处装配守卫（:13476/:13507/:29985）」，实际为 **4 处**（漏列 region_ast_generator.py:8553 站点——该站点活跃且有 isinstance 门控，功能无缺口）；②行号漂移 ±4~16 行（_b66 实为 :3191、B66 站点实为 :30325/:52125 等，系 1624ef6d 追加 9 行 C 条款 docstring 后未回改） | git diff d8246a8e 1624ef6d 逐 hunk 比对 | 记录 |

沿袭残留（本批复核逐位持平，未认领）：round7 24 单元、round8 11 单元、rv8 2 单元（B65/B63）、r4_or4_and2 1 单元（B11-R2）——按原交接单交后续。

## §6 红线核验

| # | 项 | 判据 | 实测 | 判定 |
|---|---|---|---|---|
| 1 | BOM | 两核心文件头 9 字节 | region_analyzer.py 与 region_ast_generator.py 均 = `efbbbf 222222 0a/0d`（单 BOM + `"""`） | **通过** |
| 2 | 插桩 | `R9DBG|_probe_r|_patch_dbg|_dbg_r9` 于 core/ 与 parsers/ | 两目录均 0 命中 | **通过** |
| 3 | site-packages 零手改 | `git status` 已跟踪文件零改动 | porcelain 输出仅含本轮 rv9_ 新增未跟踪文件（3 探针组 9 文件 + 5 复跑 JSON + 本报告），core/parsers/scripts/site-packages 零修改 | **通过** |
| 4 | worktree 清零 | `git worktree list` | 本复核 `D:/Temp/r9_rev` 已移除；遗留 `D:/temp/pcdc_r0`、`D:/temp/pcdc_wt/3cf6dce2`（locked）、`F:/Downloads/pcdc_r8wt`（@18f4c30d，round8 遗留）系**前轮产物非本轮创建**，如实登记建议后续轮清理 | **通过**（本轮零残留） |

零改码声明：本复核全程未修改任何 core/parsers/scripts 代码；仅新增 §4 探针产物、§3 复跑 JSON 与本报告。

## 附：本轮过程产物清单

- 探针：`test_repros/round9/rv9_01_b68_nonfin_tail.py|.pyc|*OK.py`、`rv9_02_b66_with_nest.*`、`rv9_03_b67_mixed_chain.*`（py_compile 3.11.7 + pycdc.py -o 生成，零手改）
- 复跑报告：`rounds/round9/{rv9_r9face,rv9_r6,rv9_rv8,rv9_quote,rv9_probes}.json`（全部 rv9_ 前缀，零覆盖修复 JSON）
- 归因产物：worktree `D:/Temp/r9_rev` @ d8246a8e（内含 rv9_pre_d8246.json 与 pre-fix 重生成 OK.py，worktree 连同暂存产物已整体移除；归因读数已摘录至 §4.2 存档）
