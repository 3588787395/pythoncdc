# Round 6 修复终稿（循环控制族：Break / Continue / While）

基线 = rr-v3r05a = 774cd9cb（冻结树）。域内目标：B94（while NOP 残段）、B79/B71（break 分支族）、B97（handler break）、B103 宿主 match 归属连带。

## §0 范围与基线读数

- 轮次定位：Task 6（`tasks.md` L30-34）——循环控制族封闭，四个登记破口 B79 / B94 / B97 / B71 残余。
- 基线探针（stamp `rec1_probes_r6pre1.json`，本轮首次读数 17/22）：
  - `x01=test_repros/round2/x01_if_deep_hosts.pyc` → 6/7，失败单元 `if_in_while`（B94）
  - `b71=.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc` → 3/4，失败单元 `v_nest_fin_continue`（B79/B71 续接）
  - `x10=test_repros/round2/x10_handler_hosts.pyc` → 2/3，失败单元 `h_basic`（B97）
  - `g2ctl/g2spec=@r6_g2_hdrbreak_*.pyc`（round6 源探针，py_compile 3.11 同版本产物）→ 2/2、1/2（header break）
  - `q2ctl/q2spec=@r6_q2_whilehost_*.pyc` → 2/2、1/2（while 宿主；line 6/offset 6 字节码差）
- 终态读数（stamp `rec1_probes_r6state3.json`，13 探针 43/45）：x01 **7/7**、g2spec 2/2、q2spec 2/2、x10 **3/3**、b71 3/4（`v_nest_fin_continue` 未闭合，见 §6 残余）、6 合成探针 22/23（`s_b140_break_in_finally_loop` 未闭合，见 §6 残余）。

## §1 修复日志（增量）

### B137-V3R6（x01::if_in_while，while True 体首 NOP 占位；B94）

- 症状：`while True:` 体的入口块首指令为 NOP（编译器为循环行再生的占位 NOP），体首语句被幻影占位吞掉，单元 `if_in_while` 控制流失配。
- 机制三处（`region_ast_generator.py` L13870 / L64381 / L64414）：
  1. `_loop_handle_header_no_condition`：当区域回边目标即体首块、块首为 NOP、且代码对象中其前一指令同为 NOP 时，发射 `while False: pass` 占位（重编译恰为单个 NOP）——判据只用区域回边块末跳转 argval、块后继数与相邻指令 opname（I.4 白名单）。
  2. 短路表达式块的后继数守卫：`SHORT_CIRCUIT_JUMP_OPCODES` 误纳 `JUMP_BACKWARD`（循环回边）时，块只有 0~1 条条件后继，不再是短路表达式——`_has_boolop=False`，避免整块被重构结果无差别包成 `Expr`（原 `Expr(Assign)` 退化）。
  3. 短路重构结果已是语句节点（Assign / AugAssign / AnnAssign）时直接发射，不得再包 `Expr`。
- 门禁：不命中时既有发射逐位不变（C3）；新机制不涉语料/文件名/行号特判。

### B139-V3R6（header break 与 while-else 归属；g2spec / q2spec）

- 症状：`while`/`for` 的 header 断点（header 分支上的 break）与 while-else 体归属错位：else 体被并入子 IfRegion 的 `elif_final_else`/`blocks`，生成阶段被误判为已生成 → else 体语句丢失；或 loop-else 因「尾随 return None」被折叠。
- 机制两处（`region_analyzer.py` L6671 / L6794）：
  1. loop-else 出口目标（condition 假边目标）识别：仅在 `lr.has_break` 且该目标含实际语句（非纯 pass / return None）时保留为真实 loop-else；**首版放宽为「无 has_break 也认」时 E 门禁首跑即暴露误杀**（live.pyc `DefaultLiveBroker._sync_worker` 与 trade_live_broker.pyc `TradeLiveBroker._process_tick_order` 各退化一单元，6615/6617）→ 按 I.4 收窄回 `lr.has_break` 守卫后两文件复原 32/32、128/128 且 g2spec/q2spec 仍绿。
  2. 循环 else 块若同时是子 IfRegion 的 `merge_block`，该块属循环 else 顺延代码：自子 IfRegion 的 `elif_final_else`/`else_blocks`/`blocks` 移除，并把 `block_to_region` 交还循环区域（每块唯一归属）。
- 门禁：首跑回归自捕获 → 收窄 → 二跑 6617/6617（§5）。

### B140-V3R6（except handler 体内的 break；B97）

- 症状：`except` 臂里的 `break` 被编译为 `POP_EXCEPT` + 无条件 `JUMP_FORWARD(所属循环出口)`；该 handler 体块被 TryExceptRegion 吸收（不在 LoopRegion.body_blocks 内），循环结构角色标注看不到它 → break 退化为空 handler 体（`pass`），控制流失配（x10::h_basic）。
- 机制两处：
  1. 分析器 `_detect_handler_break_blocks`（`region_analyzer.py` L36099）：判据（I.4 白名单）= ①try 保护区落在循环体内（`try_blocks ∩ 循环体 ≠ ∅`）；②handler 入口块由循环体块经**异常边**（`cfg.exception_successors`）进入；③handler 体块不在该循环体集合内；④该块以无条件前向跳转结束且目标为该循环出口块；⑤块内无 RETURN_VALUE/RETURN_CONST。
  2. 出口目标集合 `_r6_loop_exit_targets`（L36169）：condition 假边目标 + **for 循环 FOR_ITER 耗尽目标**（for 无 condition_block）+ `exit_block`。
  3. 发射端 `_generate_handler_body_statements`（`region_ast_generator.py` L37314）：命中登记块时按 break 语义发射 `ast.Break`。
- 覆盖：x10::h_basic 3/3；合成 `s_b140_handler_break` 4/4（含 for 循环内 handler break、handler continue）。

### B141-V3R6（宿主链 try→handler→with→match 的 case 体归属；B103 连带）

- 症状：match 嵌在 with 内、with 又嵌在 except handler 内时，case 体块先被祖先 TryExceptRegion 认领（`block_to_region` 指向祖先，祖先优先），`nested_region` 既非 WithRegion 也非 MatchRegion → 既有 With 分支不命中 → case 体块被无语句标记 generated → case 体退化为 `pass`（`R='t'/'R='o'` 丢失）。
- 机制（`region_ast_generator.py` L43292）：case 体块的**语义归属**判据 = 块 ∈ 某 WithRegion 的 `with_blocks` 且该 WithRegion 与本 match 区块集相交（宿主关系）→ 按普通块生成语句归本 case 体发射（与 B103 with 宿主同构：语义归属优先于首 Claim 登记，「每块唯一归属」由正在生成的 MatchRegion 承担）。
- 覆盖：x10::h_basic 3/3；合成 `s_b141_match_with_handler` 7/7（handler/顶层/嵌套三形态）。

## §2 变更清单（增量）

- `core/cfg/region_analyzer.py` +139/−4；`core/cfg/region_ast_generator.py` +88/−1；合计 2 文件 **+227/−5**。
- 标记 `[Bn-V3R6]` 11 处（B137×3、B139×2、B140×4、B141×1，另 2 处为 B140 docstring 段落）；新增方法 4 个（`_detect_handler_break_blocks` / `_r6_loop_exit_targets` / `is_handler_break_block` + 既有 `_is_pass_or_return_none_block` 复用），均六项 docstring。
- 新破口编号自 **B142** 起（B142/B143 见 §6 残余登记）；G3=0（无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀新 def）、G4=0、I.4 白名单判据齐备；只改 `core/cfg/**`。
- 新增合成探针 6 个（源 `test_repros/round6/r6_synth_*.py`，pyc 入 stage）：`r6_synth_b137_while_nop`、`r6_synth_b139_hdr_break`、`r6_synth_b139_while_else_break`、`r6_synth_b140_handler_break`、`r6_synth_b140_nested_break`、`r6_synth_b141_match_with_handler`。

## §3 前后读数

| 组 | 基线 | 终态 | 备注 |
|---|---|---|---|
| R6 主探针 7 件 | 17/22 | **21/22** | x01 6/7→7/7、x10 2/3→3/3、g2spec 1/2→2/2、q2spec 1/2→2/2；b71 3/4（`v_nest_fin_continue` 残余） |
| R6 合成 6 件 | — | **22/23** | s140n 残余；其余 5 件全绿 |
| 邻域 16 探针 | 82/86 | **83/86** | 仅 +x01；失败集 = r810 11/12、c04 5/6、m02 2/3（域外/park） |
| 命名 8 探针 | 43/46 | **44/46** | 仅 +x01；余 r809 两单元（B59/B60→R7） |
| 负对照九件 | 60/60 | **60/60** | 逐位一致 |
| R4 保护 5 组 | 71/71 | **71/71** | 逐位一致 |
| R5 合成 20 探针 | 65/65 | **65/65** | 逐位一致 |
| R5 三真实文件 | 41/41、52/52、79/79 | **同** | 172/172 |

## §4 复核

- 合成演进：`r6acc_synth1` 21/23 → 补 for 出口目标后 `r6acc_synth2` 22/23（s140h 3/4→4/4）。
- 独立验收（主代理复跑，非继承子代理读数）：`r6fin_synth1` 65/65、`r6fin_neigh1` 83/86、`r6fin_named1` 44/46、`r6fin_neg9_1` 60/60、`r6fin_r4prot1` 71/71、`r6fin_real3` 172/172、`r6state3` 43/45（13 探针）。
- E 门禁自捕获回归：首跑 6615/6617（shard6 两真实文件退化）→ 定位 B139 首版过宽 → 收窄 → 单文件复验 32/32 + 128/128 → 二跑 6617/6617 files_failure=0。
- 诊断证据：`_r6_excprobe.py`（异常边/try 区域/循环出口字段）、`_r6_matchprobe.py`（MatchRegion case 体）、`_r6_matchtrace.py`（match 生成时块占用追踪）、`_r6_regions.py`（x10/b71 区域快照）、`_r6_fin_regions.txt`、`_r6_b71_regions_now.txt`、`_r6_x10_regions_now.txt`、`_r6_rerun.py`（从既有 stamp JSON 重建批跑命令）。

## §5 门禁读数

- 脚本 `rounds/round6/final_verify_run_r6.py`（`verify_driver.py`/`verify7_split.py` 复制自 R5；BASE_COMMIT=774cd9cb；G3 判据 `git diff 774cd9cb -- core/`），产 `final_verify_summary.json` / `final_verify_log.txt`。
- **二跑（最终树，530s）**：402 八分片 **6617/6617**、files_failure=0（shard0 786、shard1 469、shard2 538、shard3 887、shard4 855、shard5 999、shard6 801、shard7 1282）。
- small34：**1568/1568**（files success 34）。
- quotation：**success**（`site-packages/fly/data/quotation.pyc`）。
- pytest 七套件：**2 failed / 282 passed / 2 xpassed**（失败名单与基线逐位一致：`test_B01_simple_if_then_else_merge` + `test_BOUNDARY_02_large_function`）。
- IV.2：IMPORT_OK / COMPILE_OK、BOM 单头（region_ast_generator / region_analyzer）、instrumentation code 命中 0、`G3_forbidden_prefix_new_defs=0`。
- 首跑（记录）：6615/6617、files_failure=2（live.pyc `_sync_worker`、trade_live_broker.pyc `_process_tick_order`）——已按 §1/B139 收窄修复，二跑归零。

## §6 落地声明

- Task 6 域内封闭：x01::if_in_while（B94，7/7）、x10::h_basic（B97 + B103 连带，3/3）、g2spec/q2spec（header break / while 宿主，2/2 各）；b71 3/4。
- 通用性实证：6 个非语料合成探针 22/23 覆盖 while-NOP 占位、header break、while-else、handler break/continue（while + for）、handler 内 with+match 三形态。
- **残余登记（park，不追）**：
  - **B142-V3R6**：`v_b71_face::v_nest_fin_continue`（嵌套 try/finally 内的 continue，B71/B79 续接）。根因：analyzer 的 try 区域构造按异常表深度分层时把「正常路径 finally 副本」误纳为外层 try 的 try_blocks（副本签名检测未命中，finally_copy_blocks 为空），内层 try 体与外层 try 体错位，continue 路径的两级副本被重排成伪嵌套 try/finally。需重构 try 区域/副本归属（异常表 depth 序 + 副本签名），非本轮循环控制检测域可闭合。
  - **B143-V3R6**：`s_b140_break_in_finally_loop`（finally 体内的 break）。根因：finally 体（副本序列）中的嵌套 IfRegion 条件块与 break 臂块在 finalbody 装配时线性发射，break 未落在 if 臂内（`if i == 1: pass` + 臂外 break/continue）。需 finalbody 装配按子区域派发（entry 身份）而非线性发射；判据与 B141 同族。
- 本轮无新增拖延破口；E 门禁首跑自捕获的 B139 放宽误杀已在提交前收窄并双门禁复验（单文件复验 + E 二跑 + 6 组回归）。
- 变更面：2 文件 **+227/−5**，标记 11 处，只改 `core/cfg/**`。
