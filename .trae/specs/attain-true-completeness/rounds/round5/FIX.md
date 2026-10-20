# Round 5 FIX.md（match-with 幻影族封闭）——终稿

规范：`.trae/specs/attain-true-completeness/`；基线 HEAD=71fda309（rr-v3r04）。
证据目录：本目录（stamps/日志/dump），探针 stage=`.trae/specs/attain-true-completeness/test_repros/round5/`。
范围（tasks.md Task 5）：B122（match 深层/守卫未命中挂死）、B93（x05::with_in_match）、B61（r8_09::r8_dh_match_multi + r8_11::r8_dh2_match_guard）、x01::if_in_match、B70（rv9_02::while_with_whole_body）；B74 深层变体保持绿；须过全部门禁（邻域/负对照/合成/E 全量）。
域外不追：c04/m02 park 归 R8；B57、x01::if_in_while（R6）、r8_10 for_iter_ternary、rv9_01 等非本族勿动。
只改 `core/cfg/**`；禁 git 写操作；判据 I.4 白名单；G3=0；G4=0；标记 `[Bn-V3R5]`。

## §0 范围与基线读数（r5pre1…，HEAD=71fda309）

| 探针 | 基线 | 红单元（failures） |
|---|---|---|
| b122a（test_repros/round8/r8v8rev_bmatch_nestnoguard.pyc, #T60） | **HANG**（regen_rc=-9，60s 硬杀） | 无读数 |
| b122b（test_repros/round8/r8v8rev_bmatch_guards_battery.pyc, #T60） | **HANG**（regen_rc=-9，60s 硬杀） | 无读数 |
| x05（test_repros/round2/x05_with_deep_hosts.pyc） | 6/7 | with_in_match（B93） |
| x01（test_repros/round2/x01_if_deep_hosts.pyc） | 5/7 | if_in_while（R6 域外）、if_in_match（R5） |
| r809（test_repros/round8/r8_09_deep_host_combo.pyc） | 7/10 | r8_dh_match_multi（B61/R5）；r8_dh_for_else_del（B59/R7）、r8_dh_with_assert（B60/R7）域外 |
| r811（test_repros/round8/r8_11_deep_host_combo2.pyc） | 5/6 | r8_dh2_match_guard（B61） |
| rv902（test_repros/round9/rv9_02_b66_with_nest.pyc） | 4/5 | while_with_whole_body（B70） |
| vb74（…/probes_rv2/v_b74_face.pyc） | 4/4 | —（保持） |
| 负对照九件 | **60/60** | — |
| 邻域 16 探针 | **79/86** | x02 for_in_match、x01 if_in_while/if_in_match、c04 CTryNest、m02、r8_10 r8_x_for_iter_ternary、rv9_02 while_with_whole_body（与 R4 基线逐位一致） |
| R4 保护组 5 件 | **71/71** | —（c4_20 24/24、e12d 11/11、r7_06 10/10、r5_10 13/13、e09b 13/13） |

stamps：`rec1_probes_r5pre1.json`（B122 双 HANG）、`rec1_probes_r5pre2.json`（红单元+vb74）、`rec1_probes_r5pre3_neg9.json`、`rec1_probes_r5pre4_neigh.json`、`rec1_probes_r5pre5_r4prot.json`。零漂移确认；零 pass→fail。

## §1 修复日志（增量，随做随写）

### B122-V3R5（b122a/b122b 挂死 + 幻影 guard + 嵌套守卫装配；stamp=rec1_probes_r5_b122_fix.json）

- 根因（挂死）：`analyze()` 收敛循环（region_analyzer L1643 区）中 `_identify_nested_match_regions` 对 MatchRegion 父区域扫描 case 体块，候选=内层链首 case 头（块 18，无 COPY 字面量头）；策略 3 `_find_nested_match_subject(18)` 前驱回溯越过内层链首命中外层 subject=0（外层同形），`_collect_nested_literal_match(0)` 复制外层 match 区域；新区域成为下一轮 parent 再命中同一候选——每轮新增同型区域不收敛（faulthandler 命中 L18147 `existing_match_blocks.update`）。b122b 首函数 v1 同型（cand=18）。
- 根因（幻影 guard）：外层 case 体首块=内层 match 链首（块 18 非 pattern 块，pb=[0]），函数序言赋值 `r=0` 的 STORE 使「最后 STORE」锚前移；主提取路径按 [B16] 捕获名重读例外拒收 `x==1` 段，但 `_extract_arithmetic_guard` 回退缺失该纪律，产出幻影 `case 1 if x == 1:`。
- 根因（嵌套守卫）：`_collect_nested_literal_match` 缺两处（与顶层 `_scan_literal_match_subjects` 同判据双实现未同步）：(1) [B81] and-guard 链解析——真值守卫臂块被并入 case 体（无 COMPARE_OP 不被发射层 guard_pattern_blocks 覆盖）→ 幻影 if/else 吞默认臂（v2 形态）；(2) case 守卫提取——`case_guards=[None]*n` 硬置。
- 修复（4 处，均 I.4 白名单：块内 opcode 形态/跳转目标/块归属）：
  1. `pattern_parser._extract_arithmetic_guard`：回退段为纯 `LOAD x; LOAD_CONST c; COMPARE_OP ==` 且 x 非先前 STORE 捕获名重读时撤销（镜像 [B16]）。
  2. `region_analyzer._find_nested_match_subject`：候选块自身满足「无 COPY + 含 LOAD_VAR + 含 COMPARE/IS_OP + 条件跳转终结」时直接认领为 subject（链首自 subject，不回溯）。
  3. `region_analyzer._identify_nested_match_regions`：嵌套区域入口同块去重（镜像 L18573 条款）——同入口已存在 MatchRegion 即拒绝（收敛保障）。
  4. `region_analyzer._collect_nested_literal_match`：移植 and-guard 链解析（同 `_scan_literal_match_subjects` B81 代码）；补齐逐 case 守卫提取（collect_pattern_blocks+parse_case_guard，allow 门槛与 [B74] 后校验同源）；or 组合并携带守卫（组取首个非 None）。
- 读数：b122a HANG→**2/2 success**（regen_rc 0）；b122b HANG→**5/5 success**；产物与源逐行一致（v1 `case 1 if g:`、v2 内层 `case 2 if g:`、v3 or+guard、v4 return 体）。
- 回归：邻域 16=**79/86**（失败集/失败名与基线逐位一致，stamp=rec1_probes_r5post1_neigh.json）；负对照九件=**60/60**（r5post2_neg9）；R4 保护组=**71/71**（r5post3_r4prot）。
- 候选先行验证：CPython 3.11.7 compile+dis 对照（`_r5_dis_ground.txt`）确证题面字节码形态；结构 dump（`_r5_v2_dis.txt`、`_r5_b122b_regions.txt`、`_r5_b122a_guard_trace.txt`）定位三处根因。

### B93-V3R5（x05::with_in_match with×match 深嵌套幻影 with；stamp=rec1_probes_r5_b93_fix.json，当前树复跑 stamp=rec1_probes_r5b93re.json）

- 根因：`match 1: case 1: with … as a: match 1: case 1: with … as b: R=(a,b)` 位形。生成内层 WithRegion@56 扫体时，块归属解析（get_entry_region_for_block/get_region_for_block）对双区域共享体块（@84/@94）命中祖先 WithRegion@14，两道既有祖先排除均失效：① W11-A「候选 blocks 含本区域 entry」不成立（@56 已被内层 with 先行认领、不在外层 blocks）；② B29 parent 链上溯断链（IfRegion@42.parent=None——层级装配归属门未采纳，@42 入口块被外层 WithRegion 先行归属）→ 祖先被当嵌套子结构递归 `_generate_region` 反向再生成（wtrace 实测 `re-enter WithRegion@14 call#2`），内层 with 体内幻影重复外层 `with … as a:`（bc_b 77 vs bc_a 56 条指令，_r5_x05_cmp_detail.txt）。
- 判据（I.4 白名单：异常表结构事实 + 区域字段，零启发式）：候选 nested_region 为 WithRegion 且其异常表体范围 `[body_offset_start, body_offset_end)` 含本区域 entry 的 start_offset ⇒ 候选是祖先 with——with 体内嵌套结构的入口必落在父体保护范围内；子区域的体范围由自身异常表刻画，不可能覆盖父区域入口。仅 WithRegion 候选适用（body_offset_* 为 WithRegion 异常表字段，region_analyzer L15457 构造）。
- 修复：`region_ast_generator._generate_with` 祖先排除（_w11a 块，L40411 区）增第三判据（+18 行，标 `[B93-V3R5]`，含注释）——两道既有判据未命中且候选为 WithRegion 时按体范围补足祖先排除，命中置空 nested_region（行为：不反向生成祖先，块走后续常规归属路径）。
- 读数：x05 6/7→**7/7 success**（with_in_match 翻绿，产物与源语义一致 `if…with…if…with`）；stamp=rec1_probes_r5_b93_fix.json；**接手复跑 7/7**（stamp=rec1_probes_r5b93re.json，2026-10-19）。
- 回归（前任已跑，stamps 在本目录）：邻域 16=**79/86**（失败集/失败名与基线逐位一致，rec1_probes_r5post4_neigh.json）；负对照九件=**60/60**（rec1_probes_r5post5_neg9.json）；R4 保护组=**71/71**（rec1_probes_r5post6_r4prot.json）。
- 候选先行验证：CPython 3.11.7 dis 对照（`_r5_x05_dis.txt`，异常表体范围 42-116/84-92）；区域 dump（`_r5_x05_regions.txt`、`_r5_x05_owners.txt` 父链断链实证）；重入 trace（`_r5_x05_wtrace.txt` re-enter call#2 全栈）；修复前后产物对照（`_r5_x05_gen.txt` 幻影 with → `_r5_x05_fix1_ok.py` 复原；`_r5_x05_fix1_verify.txt` 7/7）。

### B122-V3R5b（x01::if_in_match 无默认 match 尾汇合块被吞为幻影 `case _`；stamp=rec1_probes_r5fix1b122.json）

- 根因：`match (1,2): case (a,b): if a: … R=b; return 5`（无默认 case）。末 case 失败链 = COPY 清理桩 B56[POP_TOP] → 链外汇合块 B58[LOAD 5, RETURN]；`_mr_collect_case_body` 连接桩行走跳过纯清理桩后游标落 B58，其无条件跳转经 `_mr_find_case_jump_instruction` 返回 None 走 L17401 无跳转 default 分支，B58 被登记为幻影 `case _`（裸通配回退，`_is_pattern_fail_handler`=False、`_is_implicit_default_body`=False 因 return 5 非 None）——`return 5` 被吞入 match 体，case 体出口（原跳 B58）改道 implicit return None（`_r5_x01_dis.txt`：原始全部路径汇 B58 return 5；`_r5_x01_regions.txt`：case_blocks=[0,58] 幻影）。同族形态测试 f5/f7/f10（`_r5_shapetestOK.py`/`_r5_shapetest2fix1OK.py`）均复现。
- 判据（I.4 白名单：前驱/后继边 + 本链 case 体成员，编译器协议）：已匹配 case 体恒向前跳过剩余 case 链直达汇合块，真实 case 头绝无体块前驱（fail 链是头唯一入口；`case _` 走 NOP 标记分支；`case other` 捕获头由清理桩链到达，桩不在体集内）。故无跳转 default 候选的前驱 ∈ 本链已收集 case 体块集 ⇒ 候选是体出口共同续块（merge），不是 case 头——不登记，块留给父层后继发射。捕获尾/真默认/域外形态无体块前驱，行为逐位不变。
- 修复：`region_analyzer._mr_collect_case_body` L17401 无跳转 default 分支登记前置汇合收敛排除（+31 行注释+2 行判据，标 `[B122-V3R5]`）。域外域内无损：f8（捕获尾幻影路径）/g2（`case other`）逐位保留。
- 读数：x01 5/7→**6/7**（if_in_match 翻绿 `if a and b == 2: … else: pass` + match 后 `return 5`，语义/字节码等价；if_in_while R6 域外不变）；**同函数其余 5 单元产物逐位一致**（`_r5_x01_fix1_cmp.py`：only if_in_match changed）。
- 回归：负对照九件=**60/60**（rec1_probes_r5fix1neg.json）；R4 保护组=**71/71**（rec1_probes_r5fix1r4prot.json）；B122 双探针=**7/7**（b122a 2/2 + b122b 5/5，rec1_probes_r5fix1b122.json）；x05=**7/7**（B93 稳定）；邻域 17 探针=86/95（失败集/失败名与基线逐位一致，rec1_probes_r5fix1neigh.json）。
- 候选先行验证：CPython 3.11.7 ground truth（`_r5_g45_dis.txt`、`_r5_g610_dis.txt`——真 `case _` 必 NOP 标记、真 `case other` 以 STORE 捕获开头、无默认链以 POP_TOP 清理终止）；形态矩阵 f1-f10（`_r5_shapetest*.py/.txt`）；L17401 裸通配回退无绿色语料依赖论证（若依赖，产物重编译多 NOP 必红，402 语料全绿 ⇒ 无依赖）。

### B61-V3R5（r8_09::r8_dh_match_multi + r8_11::r8_dh2_match_guard 深宿主 match 组合；stamp=rec1_probes_r5_b61_fix.json / rec1_probes_r5fix2*.json）

- 根因（四点，均 I.4 白名单：块内 opcode 形态/跳转极性/前驱后继/异常表外区域成员）：
  1. [B61a] `_mr_collect_case_body` or 守卫链解析只识别 IF_FALSE 族失败边：case 守卫 `case X if a or b or c` 的中间臂是 POP_JUMP_*_IF_TRUE（真值边 fall-through 续走、失败边才跳下一 case 头）；case 体首断言检查块（`assert v < 1000` 的 POP_TOP 前导+条件 POP_JUMP_*_IF_TRUE 跳过失败块）同极性同不指向下一 case 头，极性目标判据无法区分二者 ⇒ 断言检查块被误并入守卫链（r8_11 case 体漏收 assert 条件块 46 与 return 块 80，产物缺 `assert v < 1000` 条件与 `return v * 2`，见 `_r5_b61_r811_gen.txt`）。
  2. [B61b] `_is_implicit_default_body`/`_is_pattern_fail_handler` 前导 POP_TOP 仅容一条（[B13]）：类模式失败链（MATCH_CLASS 可 COPY 协议）落入尾通配 `case _` 头块时清理两条 subject 副本（`POP_TOP; POP_TOP; NOP; <体>`），显式 case 标记（NOP）判据误判 ⇒ 真 `case _` 被归隐式 default。
  3. [B61c] `_generate_match` case 体首融合块：体首块同时是模式捕获材料（MATCH_MAPPING **rest 的 UNPACK/SWAP/BUILD_MAP/DICT_UPDATE/STORE rest/op 族）与体首条件（`if 'tmp' in rest` 的 CONTAINS_OP+跳转）——IfRegion FirstClaim 该块为 condition_block 后，`_if_generate_normal` 的 entry 前缀提取（entry is not cond_block 分支）从整块重读捕获材料，产出幻影 `(rest,) = {}`（`_r5_b61_r809_gen.txt`/`_r5_b61_dis.txt` 实证；fixc probe `_r5_b61_fixc_probe.py` 证实 cond 已切@60 而幻影仍在）。
  4. [B61d] case 体子区域分发 isinstance 元组缺 AssertRegion：case `_` 体的 `assert x is not None` 检查块落入 body_start 切片路径按「条件跳转+后继」重建为 if/else，断言语义丢失。
- 修复（4 处 + 收尾，只改 core/cfg/**）：
  1. [B61a] `_mr_collect_case_body` 增 AND_TRUE_OPS 与 or 守卫结构签名甄别（+52 行）：IF_TRUE 族跳转不指向下一 case 头时，沿真值边后继链有界行走（_ft_seen 去重、不越 jt）找「AND_FALSE 族跳转、目标==本链下一 case 头」的 or 守卫签名；断言检查块真值边后继是断言失败死端（LOAD_ASSERTION_ERROR+RAISE，无跳转）或体块 ⇒ 非守卫链，break（体首归 case 体收集，AssertRegion 由二次扫描独立归约）。
  2. [B61b] 两判据前导 POP_TOP 允许多条（各 ±6 行）：条数由模式协议（类模式双 subject 副本）决定，非位置特判；NOP 显式 case 标记判据本体不变。
  3. [B61c] `_generate_match` case 体分发：新方法 `_collect_case_capture_names`（含 as_name/rest/顶层 name，与 `_collect_pattern_store_names` 差异=后者不读 MatchClass as_name/顶层 name 键，既有调用方行为不变 C2）；体首块为嵌套区域条件块时按捕获名集走 `_compute_body_block_start` 切出条件段虚拟条件块（样式同 body_start 路径），**entry 同步换绑到同一虚拟块**（与通配 match 体路径 L42274 区双虚拟换绑同构；entry is cond ⇒ `_if_generate_normal` 前缀提取分支不进入），生成后 try/finally 还原 cond 与 entry（+34 行）。
  4. [B61d] case 体分发 isinstance 元组补入 AssertRegion（+7 行）——`_generate_region`→`_generate_assert` 重建 ast.Assert，与既有 IfRegion/Loop/Try/With 分发同构。
- 读数：r809 7/10→**8/10**（r8_dh_match_multi 翻绿：`case {'op': op, **rest}` 体=if+del+return 无幻影、`case [a, b]`、`case _:` 体=`assert x is not None`+raise TypeError）；r811 5/6→**6/6**（r8_dh2_match_guard：guard `v > 10` + 体 `assert v < 1000, 'too large'` + `return v * 2` + 隐式 `case _: pass`，与 ground truth 字节码一致）；stamps=rec1_probes_r5_b61_tgt.json（修复前中态）、rec1_probes_r5_b61_fix.json（终态）。
- 回归（stamps 在本目录）：负对照九件=**60/60**（rec1_probes_r5fix2neg.json）；R4 保护组=**71/71**（rec1_probes_r5fix2r4prot.json）；B122 双探针=**7/7** + x01=**6/7**（仅 if_in_while R6 域外）+ x05=**7/7**（rec1_probes_r5fix2b122.json）；邻域 15 探针=**74/79**（失败集/失败名与基线逐位一致：x02 for_in_match 哨兵、c04、m02、r810、rv902 while_with_whole_body 待 B70；rec1_probes_r5fix2neigh.json）。
- 候选先行验证：CPython 3.11.7 dis ground truth（`_r5_b61_dis.txt`：r8_11 守卫链 POP_JUMP_IF_TRUE@58 真值边→80、assert 条件块 46+失败块 60+续块 80；r8_09 case _ 头块 128=POP_TOP;NOP+assert 形）；区域/块 dump（`_r5_b61_r809_gen.txt`、`_r5_b61_r811_gen.txt`、`_r5_b61_curdump.txt` 当前树 CFG+区域全量）；fixc probe（`_r5_b61_fixc_probe.py`：cond 切片@60 生效、entry 重读为幻影二源）；幻影溯源 probe（`_r5_b61_phantom_probe.py`：排除 `_generate_block_statements` 发射路径）；形态测试（`_r5_shapetest3.py/.pyc/OK.py`）。

### B70-V3R5（rv9_02::while_with_whole_body while True+with 整体循环体；stamp=rec1_probes_r5_b70_tgt.json / rec1_probes_r5fix3*.json）

- 根因（`_check_jump_backward_for_break` 双误触发，均 I.4 白名单：块内 opcode 形态/跳转极性/前驱后继/异常表外区域成员）：
  1. [B70a] while True 整体循环体为 with 时，循环回边目标（循环入口 4）同时是 LoopRegion 与 WithRegion 的 entry；`get_entry_region_for_block` 的类型优先级（WithRegion 6 > LoopRegion 0）返回 WithRegion ⇒ 旧判定径直 `return True`（「非循环入口 ⇒ break」）。
  2. [B70b] CPython 3.11 常真测试不发射测试块：`while True` 的 LoopRegion.condition_block 为 None，循环自然回边直接指向循环入口（entry）；旧判定 `target_block != condition_block` 在 None 时恒真。
  - 合成路径：`_generate_with` 体走查（with_blocks=[34] STORE）后继扫描 → succ=36（cleanup_blocks 含 pass+__exit__ 调用块）→ `_is_with_exit_leading_to_break(36)` → 回边块 84 JUMP_BACKWARD→4 → 误触发 #1/#2 → True ⇒ `stmts=[{'type':'Break'}]`（region_ast_generator L40876）→ 产物 `while True: with open(p) as f: break`，重编译产生原字节码不存在的循环出口跳转 → Different control flow（`_r5_b70_dis.txt`/`_r5_b70_gen.txt`：ground truth 无出口边、return 15 不可达已删；`_r5_b70_regions.txt`：LoopRegion@4 break_blocks 空；`_r5_b70_withfields_probe.py` 输出：红单元 vs 绿 for 单元 WithRegion 字段对比）。
- 修复（1 处，只改 core/cfg/**）：`_check_jump_backward_for_break`（region_analyzer，L9689 起）：
  1. [B70a] 同入口循环归属回退：`get_entry_region_for_block` 返回非 LoopRegion 时，在 self.regions 中查找以该块为 entry 的 LoopRegion——块至多是一个循环的头；回边入循环头=自然回边/continue，非 break（break 出循环是前向跳转，永不回跳循环头）。仅无循环归属时维持原 return True。
  2. [B70b] while True 自然回边：LoopRegion.condition_block 为 None 时自然回边目标=entry，`target_block is not entry` 才是 break；有测试块时维持原 `!= condition_block` 判定。
  - 真 break 语义不受影响：break 编译为 with 清理+前向跳出跳转（FOR 分支 `!= header_block` 与 while 有测试分支逐位保持；`_filter_if_blocks_in_with` L39616 调用点另有 `BlockRole.BREAK` 角色双判据）。
- 读数：rv902 **4/5→5/5**（`while_with_whole_body` 翻绿：`while True: with open(p) as f: pass` 与 ground truth 一致；stamp=rec1_probes_r5_b70_tgt.json）。
- 回归（stamps 在本目录）：负对照九件=**60/60**（rec1_probes_r5fix3neg.json）；R4 保护组=**71/71**（rec1_probes_r5fix3r4prot.json）；B122 双探针=**7/7** + x01=**6/7**（仅 if_in_while R6 域外）+ x05=**7/7**（rec1_probes_r5fix3b122.json）；邻域 16 探针=**81/86**（失败集与基线逐位一致：x02 for_in_match 哨兵、x01 if_in_while、c04 CTryNest、m02、r810 for_iter_ternary；rv902 计入绿；rec1_probes_r5fix3neigh.json）。
- 候选先行验证：误触发探针（`_r5_b70_misfire_probe.py`：修复前 `_is_with_exit_leading_to_break(36,loop)=True`、修复后=False；`_check_jump_backward_for_break(84)` 修复后双情形均 False）；AST dict 探针（`_r5_b70_ast_probe.py`：With.body=[Break] 幻影定位在 `_generate_with` 返回值）；WithRegion 字段对比（`_r5_b70_withfields_probe.py`：绿 for 单元回边→FOR header 走 `!= header_block` 分支恒 False，不受影响）。

### B70-V3R5c/d（合成 g4a 族 while True+with 位形：NOP 前导 continue 回跳 + 占位臂 break/continue 替换；stamp=rec1_probes_r5synthg4a.json）

- 根因（合成 g4a 5 单元首跑 4/5，唯一红 = `<module>.g4a_wt_with_break: Different control flow`；判据均 I.4 白名单：块内 opcode 形态/跳转极性/前驱后继/循环区域成员）：
  1. [B70d] continue 回跳目标是循环头之前的**平凡 NOP 前导块**（编译器为 while True 起点发射的对齐 NOP，随后坠入循环头）——旧判据只接受 `target == header_block`，`with 体内 if a: continue` 的 JUMP_BACKWARD→NOP 前导链漏检，continue 丢失。
  2. [B70c] then 臂只剩异常表边界 NOP 块时，孤立 NOP 保留逻辑把臂渲染为 `while False: pass`（重编译对齐占位）；旧空体判定（空列表或全 Pass）不认该占位 ⇒ break/continue 臂替换不生效，臂体残留幻影 while False。
- 修复（region_ast_generator，2 新方法 + 6 调用/判定点，标 `[B70-V3R5c]`/`[B70-V3R5d]`）：
  1. [B70d] 新方法 `_backjump_reaches_loop_header`（六项 docstring）：沿平凡块（仅 RESUME/NOP/CACHE/PUSH_NULL）唯一非异常垫后继至多 4 步，判达 header_block 即自然回边；`_filter_if_blocks_in_with` then/else 臂 LOOP_BACK_EDGE 甄别两处调用（continue 判定放宽为「回跳目标经平凡前导链达循环头」）。
  2. [B70c] 新方法 `_break_continue_arm_is_placeholder`（六项 docstring）：占位体 = 空列表/全 Pass/全 `While(Constant False, body 全 Pass)`；`_if_blocks_fixup` 恢复处 Break/Continue 臂替换判定扩为占位体判定（L40691/L40695）；then 臂平凡 NOP 块 + 唯一非异常垫后继是 with 清理块且角色 BREAK ⇒ break（L39676-39695）。
- 读数：合成 g4a 族 **4/5→5/5**（g4a_wt_with_break 翻绿：`while True: with open(p) as f: if a: break` + `return 3` 与 ground truth 一致；stamp=rec1_probes_r5synthg4a.json）。
- 回归（stamps 在本目录）：负对照九件=**60/60**（rec1_probes_r5fix4neg.json 52/52 + r708 8/8 rec1_probes_r5fix4neg3.json；fix4neg2=0/0 空跑为拼写重试）；R4 保护组=**71/71**（rec1_probes_r5fix4r4prot.json）；B122 组=b122a 2/2 + b122b 5/5、x01=6/7（仅 if_in_while R6 域外）、x05=**7/7**（rec1_probes_r5fix4b122.json 20/21）；邻域 16 探针=**81/86**（失败集与基线逐位一致：x02 哨兵、x01、c04、m02、r810；rec1_probes_r5fix4neigh.json）。

### B70-V3R5e/f（合成 g4b 族 while True+with continue/双 with break 位形：同 handler 保护区延伸否决 + 空 then 臂真路径出口分类；stamp=rec1_probes_r5synthg4d.json）

- 根因（合成 g4b 5 单元基线 3/5，双红 = g4b_wt_with_continue / g4b_wt_nested_with `Different control flow`；判据均 I.4 白名单：异常表条目结构/opcode 形态/后继布局/区域成员）：
  1. [B70e] `while True: with open(p) as f: if a: continue; return 4`：continue 清理块 42（None×3+CALL+POP_TOP+JUMP_BACKWARD→2）使 `_extend_with_body_end` 收缩循环把 with 体右界从同 handler 保护区真实末端（94）误缩到 42——`_is_with_exit_cleanup` 命中且 R70/B29 判据均不豁免（后继 2∉[34,94)、末指令 JUMP_BACKWARD）；with 体漏收 else 臂汇合块 66/融合 return 块 68，二者泄漏到循环外渲染为 `while False: pass` + `return 4`（源码中均在 with 体内）。
  2. [B70f] `while True: with open(p) as f, open(p) as g: if a: break` + 循环后 `return 6`（多 with 合并形）：IfRegion@66 then_blocks=[]（真路径 72 NOP→74 g.__exit__→96 f.__exit__+JUMP_FORWARD→216 全为 with 清理链，被 IfRegion 构建排除在臂外），`_if_generate_then_branch` 空 then 臂判定空转——`_all_pure_continue` 循环零迭代恒真——误发 Continue；重编译 break 位变 JUMP_BACKWARD→2，块 216（return 6）随 while True 无 break 被 CPython 删除，双向异构。
- 修复（标 `[B70-V3R5e]`/`[B70-V3R5f]`）：
  1. [B70e] region_analyzer `_extend_with_body_end` 收缩循环：候选块之后仍存在 target==本 with 处理器（exc_target）的异常表条目（同 handler 保护区在候选后延伸，with 自身退出调用块不受自身保护、条目必标记体内真实语句位置）⇒ 跳过收缩；真终止位形（g4b_while_cond_with 收缩点 38 等）之后无同 handler 条目，收缩逐位维持。
  2. [B70f] region_ast_generator 新方法 `_classify_empty_then_exit_path`（六项 docstring）：沿条件块真后继（非 POP_JUMP 假目标、非 PUSH_EXC_INFO 异常垫）行进至多 8 步——当前块∈break_blocks 或末端 JUMP_FORWARD/JUMP_ABSOLUTE 目标∈break_blocks ⇒ 'break'；末端 JUMP_BACKWARD* 目标经平凡前导链达循环头（复用 [B70-V3R5d] 判据）⇒ 'continue'；后继不唯一/步数耗尽返回 None。`_if_generate_then_branch` 空 then 臂先走该分类（出循环→Break/回环头→Continue），未命中回退旧空体判定逐位保持。
- 读数：合成 g4b 族 **3/5→5/5**（stamp=rec1_probes_r5synthg4d.json）：g4b_wt_with_continue 翻绿（with 体 = `if a: continue` + `while False: pass`（NOP@66 重编译对齐占位）+ `return 4`，与 ground truth 逐指令一致）；g4b_wt_nested_with 翻绿（`if a: break` + 循环后 `return 6`）；全量合成电池 **28/35**（g4a 5/5 + g4b 5/5 + g5a 3/3 + g5b 4/4 全绿无回归；余红 7 = g1a×2/g1b/g2a/g2b/g3a/g3b；stamp=rec1_probes_r5synth3.json）。
- 回归（stamps 在本目录）：负对照九件=**60/60**（rec1_probes_r5fix5neg.json）；R4 保护组=**71/71**（rec1_probes_r5fix5r4prot.json）；B122 组=**20/21**（x01=6/7 仅 if_in_while R6 域外，rec1_probes_r5fix5b122.json）；邻域 16 探针=**81/86**（失败集与基线逐位一致：x02 哨兵、x01、c04、m02、r810；rec1_probes_r5fix5neigh.json）。

### B61-V3R5i/j（宿主内 match 合成补强：merge 越出 with 延迟归属 + with 出口 return 尾重复抑制；stamp=rec1_probes_r5fix9synth2.json）

- 根因（i，g2a/g2b：match 嵌套在 with 宿主内、case 体含 if+提前 return）：case 体出口 merge 块位于宿主 with 之外，`_generate_match` 直接发射并登记归属，with 清理/后置语句顺序错乱（phantom else、return 错位）。修复：merge 越界 with 时延迟归属，待 with 生成后由外层发射（`_generate_match` L41821/L43475/L43491，标 `[B61i-V3R5]`；判据=merge 块不属任何 with 体块且被 with 出口后继可达）。
- 根因（j）：嵌套 with 出口清理链上同一 return 值被两条路径重读，二次发射出现重复 return 尾。修复：新方法 `_b61j_return_value_already_emitted`（六项 docstring）按 generated 登记判定值已发射，调用点 L12234/L41205，标 `[B61j-V3R5]`。
- 读数：g2a 2/3→3/3、g2b 2/3→3/3（`with_hosts_match` / `with_match_with` 翻绿，产物与 ground truth 逐指令一致）。

### B61-V3R5k（for/with/try 宿主内 match case 体内部 if 未建 IfRegion；stamp=rec1_probes_r5fix9synth2.json）

- 根因（g3a/g3b：mapping-rest 捕获 + case 体 if，match 宿主为 for/with/try）：case 体成员 if 的入口块被 match 认领后，IfRegion 构建门整体拒绝——if 条件/臂并入 case 体，`case _` 体被并成 break 或 if/else 合流。
- 判据（I.4：区域成员关系 + 跳转目标）：块为某 case 体成员且条件跳转目标非 case 头/失败链块 ⇒ 允许 IfRegion 独立构建（region_analyzer L21547 区，标 `[B61k-V3R5]`）。
- 读数：g3a 2/3→3/3、g3b 2/3→3/3；**连带 x02::for_in_match 6/7→7/7**（内层 if 识别缺口同源消除）。

### B70-V3R5g/h/i/j（with 体内 elif 链 continue、NOP 前导循环头、出口分类途经块、无回边 while True break 重建；stamp=rec1_probes_r5fix9synth2.json）

- [B70g] with 体内 `_generate_if` 递归生成 elif 链后继 IfRegion 时绕过 `_filter_if_blocks_in_with`：`if b: continue` 的 with 清理块被物化为 `while False: pass`、continue 丢失（b70a wbc）。修复：`_generate_if` 对 entry 属 WithRegion 成员者复用过滤/占位体替换契约（L16450 区，`_b70a_in_filter` 防二次过滤，标 `[B70-V3R5g]`）。
- [B70h] while True 循环头前 NOP 平面前导块被当孤立块物化：识别为循环控制前导并登记 generated（L39804 区）。
- [B70i] 空 then 臂出口分类途经的连接/清理块未登记，区域体走查二次物化：分类成功即随合成 Break/Continue 一并登记（L21260 区）。
- [B70j] `while True: with …: if a: break` 全出口皆 break（无回边）→ 无 LoopRegion：以 with 出口链 + 前向跳转 merge 识别 break 臂，重建 `While(True,[With,Break])`（新方法 `_r5_b70j_loopless_while_break`，六项 docstring；L40418/L42214 区）。
- 读数：b70a 1/3→3/3（wbc/wbc_nested），g4a/g4b 保持 5/5。
- **E 门禁自捕获修正（B70g 宿主收窄）**：宽守卫（任意 with 内 if）在真实代码误触发三文件——`trade_info_utils::trade_operation`（with 后幻影 return None）、`scheduler::Scheduler×5`（if 臂内 with 被移出体、尾部 `with ModifyExceptionFromType(…): pass` 幻影）、`quote_handler::get_holiday_local`（continue 臂吞 `flg=False`、year 假支 append 丢失）。鉴定（ground truth dis：`_r5_dis_holiday.txt`/`_r5_dis_sched1.txt`）后按 I.4 收窄：仅当宿主 with 的 entry 属某 LoopRegion 体成员（break/continue 必须穿越其清理链）才触发；with 包裹循环、if 臂内嵌 with 两类位形回落原路径。收窄后三文件单验 41/41、52/52、79/79 全绿，b70a 仍 3/3。

### x02::for_in_match 哨兵裁决（历史记录；最终已由 B61k 连带翻绿）

- 现象：产物文本 `if not b == 2: continue` 替代源码内层 `match b: case 2:`（`Different control flow`）。
- 裁决依据：
  1. 机制不属于本族：区域 dump（`_r5_x02_regions_probe.py`）显示外层 MatchRegion@0 正确识别、无捕获材料双发、无守卫极性/切片问题；内层 `match b: case 2:`（单字面量 case、无捕获、无默认）字节码仅 COMPARE_OP+POP_JUMP，与 `if b == 2:` 在孤立视角不可区分，分析器未识别为 MatchRegion（区域层面无幻影）。
  2. 生成器把 if false 边指向回边块 116 解读为 continue → 产出负向 if+continue 形；重编译后 continue 直跳 FOR_ITER、缺原专属回跳块 → CFG 异构。
  3. 对照实验：忠实 `if b == 2:` 形重编译仍异构（原 match 形 fail 边有专属回跳块 116→58；if 形 false 边并入内层 for 耗尽块 114——match 编译在 case 体尾保独立 fail 路径块）。翻绿须以「fail 路径专属块」为结构特征重建内层 match——属 match/if 结构消歧+if-continue 降级域（R6/R8 if-continue 同族），非 R5 捕获材料幻影族。
- 结论（历史）：修复前维持基线红（x02 6/7 在 §0 基线失败集内，邻域门禁逐位一致不破），登记归后续轮（R6/R8 if-continue/match 消歧）。**终态更新**：B61k（宿主内 case 体内部 if 的 IfRegion 构建门）同源消除该缺口后 x02 6/7→7/7（stamp=rec1_probes_r5fix9neigh2.json / r5fin_neigh1.json），原 R6 裁决项提前关闭；本段保留历史裁决与对照证据。

## §2 变更清单（增量）

- `core/cfg/region_analyzer.py`：`_find_nested_match_subject`（+12 行 B122 自 subject 认领）、`_identify_nested_match_regions`（+12 行入口去重）、`_collect_nested_literal_match`（+30 行 and-guard 链解析；+35 行逐 case 守卫提取与 or 组守卫合并）。
- `core/cfg/pattern_parser.py`：`_extract_arithmetic_guard`（+18 行模式比较材料隔离）。
- `core/cfg/region_ast_generator.py`：`_generate_with` 祖先排除（_w11a 块）增 B93 with 跨体祖先判定（+18 行，标 `[B93-V3R5]`）。
- `core/cfg/region_analyzer.py`：`_mr_collect_case_body` L17401 无跳转 default 分支增 [B122-V3R5] 汇合收敛排除（+31 行，无跳转 default 候选前驱 ∈ 本链已收集 case 体块集 ⇒ merge 不登记）。
- `core/cfg/region_analyzer.py`：`_mr_collect_case_body` [B61a-V3R5]（+3 行 AND_TRUE_OPS 定义；+52 行 or 守卫结构签名甄别收窄）。
- `core/cfg/region_analyzer.py`：`_is_implicit_default_body`/`_is_pattern_fail_handler` [B61b-V3R5]（各 ±6 行，前导 POP_TOP 允许多条）。
- `core/cfg/region_ast_generator.py`：`_generate_match` case 体分发 [B61d-V3R5]（+7 行 AssertRegion 入 isinstance 元组）；[B61c-V3R5]（+8 行注释扩写 +34 行体首融合块捕获切片与 entry 同步换绑 + try/finally 还原；新方法 `_collect_case_capture_names` +33 行，六项 docstring）。
- `core/cfg/region_analyzer.py`：`_check_jump_backward_for_break` [B70a/B70b-V3R5]（+21 行：同入口循环归属回退 + while True 自然回边判定）。
- `core/cfg/region_ast_generator.py`：[B70d-V3R5] 新方法 `_backjump_reaches_loop_header`（+36 行，六项 docstring）+ `_filter_if_blocks_in_with` then/else 臂两处调用（回跳目标经平凡 NOP 前导链达循环头）；[B70c-V3R5] 新方法 `_break_continue_arm_is_placeholder`（+31 行，六项 docstring）+ `_if_blocks_fixup` 恢复处 Break/Continue 占位臂替换两处 + then 臂平凡 NOP 块后继 BREAK 角色甄别（合计 +103/-6）。
- `core/cfg/region_analyzer.py`：`_extend_with_body_end` [B70-V3R5e]（+14 行：收缩候选块之后仍有同 handler（target==exc_target）异常表条目 ⇒ with 体在候选后继续，跳过收缩）。
- `core/cfg/region_ast_generator.py`：[B70-V3R5f] 新方法 `_classify_empty_then_exit_path`（+70 行，六项 docstring）+ `_if_generate_then_branch` 空 then 臂分类挂接（+12 行）。
- `core/cfg/region_ast_generator.py`：[B61i-V3R5] `_generate_match` merge 越界 with 延迟归属 + 后置发射（3 处，+60 行区）；[B61j-V3R5] 新方法 `_b61j_return_value_already_emitted`（六项 docstring）+ 双 with 出口 return 值重复抑制调用点（2 处）。
- `core/cfg/region_analyzer.py`：[B61k-V3R5] 宿主内 case 体成员 if 的 IfRegion 构建门放宽（L21547 区）；新方法 `_b74_guard_arm_targets_case_body`（六项 docstring，配合守卫臂/shape 甄别）。
- `core/cfg/region_ast_generator.py`：[B70-V3R5g] `_generate_if` 入口复用 with 过滤/占位体替换契约（L16450 区，含 B70g 宿主收窄判据）；[B70-V3R5h] NOP 前导循环头块识别（L39804 区）；[B70-V3R5i] 出口分类途经块登记（L21260 区）；[B70-V3R5j] 新方法 `_r5_b70j_loopless_while_break`（六项 docstring）+ 无回边 while True+with break 重建挂接（L40418/L42214 区）。
- 累计 numstat（vs HEAD=71fda309）：pattern_parser 147/16、region_analyzer 380/52、region_ast_generator 651/17；共 **1178 insertions / 85 deletions**；标记 `[Bn-V3R5]` **27 处**；新增方法 7 个（`_b74_guard_arm_targets_case_body`、`_b61j_return_value_already_emitted`、`_backjump_reaches_loop_header`、`_break_continue_arm_is_placeholder`、`_classify_empty_then_exit_path`、`_r5_b70j_loopless_while_break`、`_collect_case_capture_names`，均六项 docstring）；G3=0（HEAD 既有两处 `_merge_*` 方法不计）。

## §3 前后读数

| 探针 | 基线（§0，HEAD=71fda309） | 终态（最终树） | 说明 |
|---|---|---|---|
| b122a | **HANG**（60s 硬杀） | **2/2 success** | B122 挂死收敛 |
| b122b | **HANG**（60s 硬杀） | **5/5 success** | B122 幻影 guard + 嵌套守卫 |
| x05 | 6/7 | **7/7** | B93 with 跨体祖先排除 |
| x01 | 5/7 | **6/7** | B122b::if_in_match 翻绿；if_in_while=R6 域外 |
| r809 | 7/10 | **8/10** | B61 四点；r8_dh_for_else_del=B59/R7、r8_dh_with_assert=B60/R7 域外 |
| r811 | 5/6 | **6/6** | B61 守卫/断言/返回 |
| rv902 | 4/5 | **5/5** | B70a/b 双误触发 |
| vb74 | 4/4 | **4/4** | 保持 |
| 合成非语料 20 探针 | 首攻 54/65（r5synthall1） | **65/65** | 5 机制全清：g1a/g1b（or/通配守卫）、g2a/g2b（宿主内装配 B61i/j）、g3a/g3b（B61k + 星形序列）、b74d/b74e、b70a（B70g-j）；g4a/g4b 5/5 |
| 邻域 16 探针 | 79/86 | **82/86** | +x01::if_in_match、+rv902、+x02（B61k）；余 4=x01 if_in_while、c04、m02、r810，均域外/park |
| 负对照九件 | 60/60 | **60/60** | 逐位一致 |
| R4 保护组 5 件 | 71/71 | **71/71** | 逐位一致 |

- 邻域残红单元（4）与基线逐位一致（x01 for if_in_while=R6/B94、c04 CTryNest 与 m02=B132 park 归 R8、r810 for_iter_ternary=R7）；x02 原基线红已转绿（见 §1 x02 段终态更新）。

## §4 复核

- 合成门禁演进 stamps（本目录）：`rec1_probes_r5synth.json` → `r5synth3`（28/35）→ `r5synthg4a/b/c/d`（B70 迭代）→ `r5synthall1`（54/65，5 机制暴露）→ `r5fix9synth2`（65/65）→ 主代理独立复跑 `r5acc_synth1`、`r5acc_synth2`（均 65/65）。
- 主代理独立验收（本目录 stamps）：`r5acc_synth1`（20 探针 65/65）、`r5acc_neigh1`（82/86）、`r5acc_neg9_1`（60/60）、`r5acc_r4prot1`（71/71）、`r5acc_named1`（43/46，3 项域外）；E 门禁修正后终树复跑 `r5fin_neigh1`（82/86）、`r5fin_neg9_1`（60/60）、`r5fin_r4prot1`（71/71）、`r5fin_named1`（43/46）。
- **E 门禁首跑自捕获回归与二分**：首跑 6610/6617（files_failure=3：trade_info_utils 40/41、scheduler 47/52、quote_handler 78/79；small34 1566/1568）→ 停用 B70g 后三文件单验全绿（41/41、52/52、79/79）→ 定位宽守卫 → ground truth dis 对照（`_r5_dis_holiday.txt`：真值 `if flg: flg=False; continue` 与 year 假支无条件 append；`_r5_dis_sched1.txt`：ModifyException with 在 if 臂内包裹 func；`_r5_regr_dump.txt` 产物幻影形态）→ 收窄为「宿主 with entry ∈ LoopRegion 体成员」→ 三文件复原 + b70a 3/3（`r5acc_b70a2`）→ E 二跑 6617/6617。
- 候选先行验证证据：B122=`_r5_dis_ground.txt`/`_r5_v2_dis.txt`/`_r5_b122b_regions.txt`/`_r5_b122a_guard_trace.txt`；B93=`_r5_x05_dis.txt`/`_r5_x05_regions.txt`/`_r5_x05_owners.txt`/`_r5_x05_wtrace.txt`；B61=`_r5_b61_dis.txt`/`_r5_b61_r809_gen.txt`/`_r5_b61_r811_gen.txt`/`_r5_b61_curdump.txt`/`_r5_b61_fixc_probe.py`；B70=`_r5_b70_dis.txt`/`_r5_b70_gen.txt`/`_r5_b70_regions.txt`/`_r5_b70_misfire_probe.py`；合成 5 机制=`_r5_mA_trace.txt`…`_r5_mF_trace.txt`/`_r5_mC_regions.txt`/`_r5_mD_regions.txt`/`_r5min1.py`（最小矩阵隔离 or 守卫链/宿主装配/星形/通配守卫）。
- 零漂移核验：邻域失败集/失败名逐位 = 基线 4 项（x01/c04/m02/r810）+ x02 转绿；负对照逐位；R4 保护逐位；E 二跑 8×REGRESSIONS=0。

## §5 门禁读数

- 脚本 `rounds/round5/final_verify_run_r5.py`（`verify_driver.py`/`verify7_split.py` 复制自 R4；BASE=71fda309；G3 判据 `git diff 71fda309 -- core/`），产 `final_verify_summary.json`/`final_verify_log.txt`。
- **二跑（最终树，578s）**：402 八分片 **6617/6617**、files_failure=0；8×`REGRESSIONS=0`（shard0 786、shard1 469、shard2 538、shard3 887、shard4 855、shard5 999、shard6 801、shard7 1282）。
- small34：units **1505/1568→1568/1568**、files success 1→34、`REGRESSIONS=0 IMPROVED=33`。
- quotation：**153/153 success**（`site-packages/fly/data/quotation.pyc`）。
- pytest 七套件：**2 failed / 282 passed / 2 xpassed**（失败名单= `test_B01_simple_if_then_else_merge` + `test_BOUNDARY_02_large_function`，与基线逐位一致）。
- IV.2：IMPORT_OK/COMPILE_OK、BOM 单头（region_ast_generator/region_analyzer）、`G3_forbidden_prefix_new_defs=0`、instrumentation code 命中 0（in_string 仅既有字符串文本）、site-packages 无新增零字节文件。
- 首跑（B70g 宽守卫树）记录：6610/6617、files_failure=3、small34 1566/1568 —— 回归已按 §4 收窄修复，二跑归零。
- **站点包快照刷新（提交后复核发现）**：E 门禁后对两个真实模块重生成 `site-packages/IQEngine/utils/__init__OK.py`（33/33）与 `site-packages/IQData/plugins/plugin_system_client_db/client_dbOK.py`（9/9）——当前树相对 BASE 71fda309 各减少 1/2 处死代码 `return None`（with 出口 return 后的不可达尾行；无新增行；pyc_verify 双 100%），属 R5 with 出口分类收窄的连带净改善；快照按新输出刷新（`rr-v3r05a`），证据 `_r5_snapref_base_init.txt`/`_r5_snapref_cur_init.txt`/`_r5_snapref_base_clientdb.txt`/`_r5_snapref_cur_clientdb.txt` + `_r5_cmp_base.py`（BASE worktree 对照：base≠cur、cur==工作树）。该两文件不在 402 集，首跑/二跑 6617/6617 读数不受影响。

## §6 落地声明

- Task 5 域内封闭：B122（挂死收敛 + 幻影 guard + 嵌套守卫装配）、B93（with×match 幻影镜像）、B61（a-d 深宿主 guard/断言/融合块 + i-k 合成补强）、B70（a/b 双误触发 + c-j 合成/真实位形）、x01::if_in_match 全部翻绿；B74 保持绿。
- 合成通用性实证：20 个非语料交叉变体 **54/65→65/65**（合成文件在 `test_repros/round5/`，stage 在 `.trae/specs/attain-true-completeness/test_repros/round5/`）。
- 域外/残余（不追，与前轮一致）：x01::if_in_while（R6/B94）、r809::r8_dh_for_else_del（B59/R7）、r809::r8_dh_with_assert（B60/R7）、r810 for_iter_ternary（R7）、c04/m02 park（R8/B132）。
- x02::for_in_match：原裁决归 R6；B61k 同源修复后 6/7→7/7，裁决项提前关闭（邻域 79/86→82/86 的 +2 中占 1）。
- 本轮无新增拖延破口；E 门禁首跑自捕获的 B70g 宽守卫误触发已在提交前收窄并双门禁复验（三文件单验 + E 二跑 + 合成 65/65）。
- 变更面：3 文件 **+1178/−85**，标记 `[Bn-V3R5]` 27 处，新增方法 7 个（六项 docstring），G3=0 / G4=0 / I.4 白名单判据；只改 `core/cfg/**`。
- 提交后快照刷新（2 个 site-packages 真实模块 3 处死代码 `return None` 移除，pyc_verify 双 100%）见 §5，随 `rr-v3r05a` 入库。
