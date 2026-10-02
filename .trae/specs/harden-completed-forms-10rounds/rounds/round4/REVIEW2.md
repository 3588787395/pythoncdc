# Round 4 复核（Task 4.3，对抗性独立复核）

- 复核人：复核工程师（Round 4，独立对抗复核）
- 日期：2026-10-02
- 对象：修复两批次（批次一 bb8efb50 = B12/B13/B14；批次二 e0ad6f3b = B16/B15/B17/B18/B19）共 7 个封闭声明
- 唯一判据：`scripts/pyc_verify.py`（single）。全部读数 = 复核工程师本人 2026-10-02 在现树（HEAD = e0ad6f3b，`git status` core/ scripts/ 干净）亲手复跑，未采信任何书面声明。
- 复核纪律：未修改任何 `core/`、`scripts/`、`pycdc.py`、既有 `*OK.py`、`site-packages/`、`.trae/specs/` 既有内容；唯一产出文件为本 REVIEW2.md；新增变体复现 `rv4_*.py/.pyc/OK.py` 落于 `test_repros/round4/`（变体验证后产物按交接单保留）；未执行 git commit。

---

## §1 读数复跑全表（声明 vs 实测，逐支）

### 1.1 Round 4 Match 组（FIX.md §12.1 声明 vs 本复核实测）

| 文件 | FIX.md 声明（批次二后） | 本复核实测 | 判定 |
|---|---|---|---|
| probe_match_min | 3/3 | **3/3** | 一致 |
| n4_01_no_match_control（负对照） | 7/7 | **7/7** | 一致 |
| r4_01_match_value | 6/6 | **6/6** | 一致 |
| r4_02_match_singleton | 5/5 | **5/5** | 一致 |
| r4_03_match_sequence | 7/7 | **7/7** | 一致 |
| r4_04_match_mapping | 4/6（余 2 未落地） | **4/6**（失败单元 = match_map_nested、match_map_mixed_seq，见 §5） | 一致 |
| r4_05_match_class | 9/9 | **9/9** | 一致 |
| r4_06_match_or | 6/6 | **6/6** | 一致 |
| r4_07_match_capture_wildcard | 6/6 | **6/6** | 一致 |
| r4_08_match_star | 7/7 | **7/7** | 一致 |
| r4_09_match_guard | 7/7 | **7/7** | 一致 |
| r4_10_match_default_tail | 6/6 | **6/6** | 一致 |
| r4_11_match_complex_subject | 10/10 | **10/10** | 一致 |
| r4_12_match_nested_loop | 7/7 | **7/7** | 一致 |
| r4_13_match_try | 7/7 | **7/7** | 一致 |
| r4_14_match_case_body | 7/7 | **7/7** | 一致 |
| r4_or4_and2（B11-R2 残留，不在本批范围） | 1/2 | **1/2** | 一致 |

**虚报检查：零。** 17 支逐支核对全部与 FIX.md §12.1 一致（13/14 文件全 success、96 单元 94 MATCH 的总口径成立）。批次一中间态读数（如 r4_03 2→7/7）无法在现树单线复验，终态与声明一致即通过。

---

## §2 逐 hunk 审查结论

两笔 diff（`git show HEAD~1 -- core/`、`git show HEAD -- core/`）共 67 hunk 全部逐个审毕。判定口径：判据是否同层结构事实（操作码形态/栈效应/前驱后继/块角色/认领状态）、有无白名单或跨层启发式、docstring 三要素 + [C1]/[C2]/[C3] 是否齐全且与代码一致、嵌套无感、调试插桩残留。

### 2.1 批次一（bb8efb50，3 文件 28 hunk）

| 文件 | hunk（新行号） | 内容 | 判定 |
|---|---|---|---|
| ast_converter.py | :1702-1716 | MatchMapping 保留模式 dict 壳（不再折叠 ASTDict），rest 透传 | **通过**（判据=模式类型分派，[C2] 注记与代码一致） |
| ast_converter.py | :1764-1784 | MatchOr 保留模式 dict 壳（含 left/right 旧格式归一） | **通过**（同上） |
| pattern_parser.py | :514-525 | capture+guard 算术守卫链回退入口（search_start>0 排除通配形态） | **通过** |
| pattern_parser.py | :566-651/:653-680 | `_extract_arithmetic_guard` + `_BINARY_OP_ARG_MAP` + `_eval_guard_expr_stack`（NB 表整数 arg 映射=Cython 操作码语义表，非字面量白名单） | **通过**（三要素+C1/C2/C3 齐全，fail 极性判据封闭） |
| pattern_parser.py | :947-957 | `_extract_case_pattern` 终局 else 归因捕获头 STORE | **通过** |
| pattern_parser.py | :968-1013 | `_extract_capture_head_store`（无模式指令 ∧ 首条有效 STORE；POP_TOP 前缀跳过） | **通过**（栈平衡结构事实，首/中/尾 case 同判） |
| pattern_parser.py | :1136-1166 | `_fail_jump_target_offsets`（IF_FALSE/IF_NONE/IF_NOT_NONE 族=fail 边；IF_TRUE=or 成功边保留） | **通过** |
| pattern_parser.py | :1170-1218/:1270-1310 | `_find_last_store_on_success_path`/`_find_store_in_successors` 全程排除 fail 边目标 | **通过**（修复幻影捕获注入，判据极性驱动） |
| pattern_parser.py | :1338-1354/:1354-1373/:1391-1399 | `allow_own_as_store` 参数 + 嵌套 COPY 1 判据 + skip_until 机制 | **通过**（COPY 前缀=内层 as 唯一结构事实，docstring 如实声明「纯 STORE 序列不可区分」的极限） |
| pattern_parser.py | :1473/:1481-1490 | seen_pattern_instr ∧ allow_own_as_store 双门 as_name 归属 | **通过** |
| pattern_parser.py | :1498-1517 | 嵌套子模式类型分派递归 + `_nested_sequence_slot_consumers_end` 消费计数 | **通过**（UNPACK argval 驱动，无位置特例） |
| pattern_parser.py | :1560-1611 | `_nested_sequence_slot_consumers_end` 本体 | **通过** |
| pattern_parser.py | :2075-2092/:2117-2126 | 嵌套值模式补 MATCH_MAPPING 递归 + **rest 的 DICT_UPDATE→STORE 配对跳过 | **通过** |
| region_analyzer.py | :13317-13323/:13332-13342 | 模式绑定 STORE 消耗完即 break（体首元素边界） | **通过**（每块唯一归属，C1 论证成立） |
| region_analyzer.py | :13578/:13596-13610 | or 等价体合并时 case_blocks 同步压缩（三数组下标对齐） | **通过**（修复守卫借位，归属论证清晰） |
| region_analyzer.py | :13708-13727 | jump_instr is None 分支改 parse 且仅接受带名 MatchAs | **通过**（保守回退，零行为面扩大） |
| region_analyzer.py | :14916-14940 | `_is_implicit_default_body` 前导 POP_TOP 扩展（NOP 先于 NOISE 检查的次序坑已注明「勿改」） | **通过** |
| region_analyzer.py | :14959-14994/:14997-15003 | `_mr_block_has_explicit_case_marker` + `_is_pattern_fail_handler` 顶部守卫 | **通过**（NOP=编译器显式 case 标记，非位置特例；三要素+C1/C2/C3 齐全） |

### 2.2 批次二（e0ad6f3b，3 文件 39 hunk）

| 文件 | hunk（新行号） | 内容 | 判定 |
|---|---|---|---|
| pattern_parser.py | :63-84/:310-313 | parse_case_guard 增加 allow_in_header_block/fail_case_offset 形参 | **通过**（默认 False 保持旧行为） |
| pattern_parser.py | :381-429 | guard_start 检测新增真值臂/算术调用混合臂/捕获名重读例外 | **通过**（「捕获重读 vs 模式材料比较」以 LOAD 同名重读区分，判据同层） |
| pattern_parser.py | :452-600 | guard 臂链提取重构：`_mr_guard_arm` 形态 a/a'/b/c + fail_case_offset 极性判定（倒臂=dir_true==to_fail，复核推导等价正确）+ 链 op=首臂目标是否 fail 边 | **通过**（三要素+C1/C2/C3 齐全；fail_case_offset 未知时回退旧启发式，行为兼容） |
| pattern_parser.py | :719-723/:771-796/:815-818 | 算术守卫段纳入 PRECALL/CALL；`_eval_guard_expr_stack` 支持 CALL（弹 argval 实参→Call 节点）+ 段结果类型放宽 | **通过** |
| pattern_parser.py | :838-870/:880-890 | `_find_real_match_header` 前驱 BFS 限定 fall-through 连续边（false 边候选=别的 case 头） | **通过**（r4_12 nested_match_seq 形态的封闭判据） |
| pattern_parser.py | :1016-1050/:1050-1072 | 捕获头预检先于跨块收集（回边防误拼）+ 捕获+守卫头分派（COPY;STORE;LOAD 同名三连 ∧ 块尾条件跳转） | **通过**（walrus 分界=不重读绑定名，论证成立） |
| pattern_parser.py | :1438-1453 | has_body 判据补 BINARY_OP/CONTAINS_OP/UNARY_*（体首增广赋值形态） | **通过** |
| pattern_parser.py | :2090-2163 | **B18 核心**：`_extract_class_pattern` SWAP 栈模拟（栈元素=槽位号，SWAP k 交换 [-1]/[-k]——复核核对 CPython SWAP k 语义 TOS↔TOS(k-1) 一致；未消费尾槽通配补位防串位） | **通过**（窗口起点=UNPACK 压满 count 槽，类模式窗口起点假设成立；mapping 值槽位窗口起点假设不成立正是 r4_04 余项，FIX.md §14 如实登记，一致） |
| region_analyzer.py | :1632-1652 | 嵌套 match 二次扫描收敛循环（每轮只扫新区域） | **通过** |
| region_analyzer.py | :1774-1836 | `_mr_dissolve_match_subsumed`（候选 blocks ⊆ MatchRegion.blocks ∧ entry∈{subject}∪case_blocks；NOP 标记豁免防误杀体首 if） | **通过**（判据=块集包含+入口同一性；NOP 豁免为 B13 判据复用，嵌套无感） |
| region_analyzer.py | :1890-1901/:3373-3385 | block_to_region 双落点：同类型 MatchRegion 块集真子集者优先（match×match 内层优先） | **通过** |
| region_analyzer.py | :13236-13255/:13290-13310 | capture-guard 块纳入候选 + 子链去重（同一 case 头块只归一条链）+ 头块守卫提取放行 + fail_case_offset 供参 | **通过** |
| region_analyzer.py | :13371-13390 | 纯通配 case 头短路（pattern=MatchAs 无名无子模式 ∧ 头协议 POP_TOP/NOP 前缀跳过） | **通过** |
| region_analyzer.py | :13623-13645 | 逆臂守卫链判定（IF_TRUE 目标==行走收敛块 ⇒ 体=fall-through 终点）+ 终点非条件跳转时从链块集排除 | **通过** |
| region_analyzer.py | :13685-13723 | `_mr_collect_simple_body_blocks`：start 前移与 worklist 扩展双点接入 `_mr_body_walk_predicates_closed`（B15 汇合守卫） | **通过** |
| region_analyzer.py | :13723-13745 | `_mr_finalize_match_region` subject_block 透传 | **通过** |
| region_analyzer.py | :13816-14070 | **B16/B15/B17 核心**：`_mr_compute_case_merge`（支配边界 (a)+循环再检测排除 (b)+异常表边排除 [B17]）+ `_mr_is_loop_recheck_block` + `_mr_apply_case_body_boundary` + `_mr_body_walk_predicates_closed` + `_mr_collect_case_body_blocks` + `_mr_is_case_check_shaped_block`（6 个新函数，三要素+C1/C2/C3 全齐） | **通过**（支配/回边/前驱闭合/块集包含全部同层；无位置/名字特例；JUMP_BACKWARD 终结保留=continue 语义，判据明确） |
| region_analyzer.py | :14095-14160/:14363-14455 | `_mr_skip_case_connectors` + `_mr_collect_case_body`：try 体边界 [B17] + 异常分派块前驱闭合排除 [B17] + NOP 默认 case 头短路 [B16-F3] + 下一 case 受当前 case 支配 [B16]（`_last_case_no_dom` 终止前登记=末 case 不丢 [B15]）+ 嵌套 match 头收口 [B16-F4] + 守卫续块判定收窄 [B16-C3] | **通过**（B18 类模式 fail 边经连接桩解析覆盖，与 `_mr_skip_case_connectors` 同源判据） |
| region_analyzer.py | :14881-15055/:15121-15560 | `_collect_nested_literal_match`/`_scan_literal_match_subjects` 镜像同步（NOP 短路/支配终止/体行走/merge 候选过滤/入口同块去重） | **通过**（与主路径同判据，无双标） |
| region_analyzer.py | :15564-15643 | `_mr_head_has_capture_binding` + `_is_capture_guard_case_block` | **通过**（COPY;STORE;LOAD 同名三连，walrus 分界沿用） |
| region_ast_generator.py | :31219-31230/:7870/:11849 | `_mr_mark_match_blocks_generated`（merge 块一并标记）替换两处裸标记 | **通过** |
| region_ast_generator.py | :31265-31436 | **B15/B16/B19 核心**：subject 行走 8 处 break 点记录 `_subject_break_idx`；for-target 消费偏移集；内层 POP_TOP 跳过；捕获绑定 STORE 与前导赋值 STORE 以「块内后续有无 COPY」区分；捕获 subject 以 COPY 终止；**B19**：LOAD_GLOBAL/LOAD_NAME 仅在后继 LOAD_CONST(tuple)+MATCH_* 三元组时按类协议跳过 | **通过**（后继指令形态判据，无名字/位置特例；类模式 Point 加载仍走协议分支——rv4_19 11/11 实证） |
| region_ast_generator.py | :31404-31480 | B15 前导语句按原始块前缀 [0:_subject_break_idx] 以语句终结指令切分、经 `_build_statement` 发射在 Match 之前 | **通过**（rv4_15 三前导语句形态实证通过） |
| region_ast_generator.py | :31658-31682/:32007-32025 | case 体终块 break 判定（纯跳转/POP_TOP 前缀 + 目标∉region.blocks ∧ 存在 Loop 父区域） | **通过**（r3_27 9/9 哨兵实证未误伤平直 match） |
| region_ast_generator.py | :32042-32060 | has_only_pattern 判据加 NOP 显式 case 体标记守卫 | **通过** |
| region_ast_generator.py | :32184-32262 | **B15 核心**：merge 块尾链行走发射（先发射后标记；子区域入口走 `_generate_region`；`_tail_cursor` 限 match 自有块）+ 前缀/merge 存在时返回语句列表 | **通过**（块归属与 block_to_region 所有权判据） |
| region_ast_generator.py | :35777-35790 | boolop else 路径 merge 块解除标记→生成→复标（R02/R78 同模式） | **通过** |

### 2.3 专项重点复核

- **B16 支配边界/回边再检测/汇合闭合守卫**：三守卫（`_mr_apply_case_body_boundary`/`_mr_is_loop_recheck_block`/`_mr_body_walk_predicates_closed`）均为支配关系+跳转方向+前驱闭合的同层判据；回边判据=「条件跳转目标支配 subject 或即 subject」，复核推导旋转 while 再检测块（POP_JUMP_BACKWARD→体首）与平直 match merge（前向）两类形态不混判。**判定：嵌套无感成立**（变体攻击 §3 的 B16-R 新边界是识别覆盖面问题，非守卫本身嵌套敏感）。
- **B18 SWAP 栈模拟窗口起点假设**：类模式窗口自 UNPACK_SEQUENCE 起、压满恰好 count 个槽位，窗口相对推演=绝对栈深，假设成立；mapping 值槽位（r4_04 余项）窗口起点夹在兄弟协议之间、绝对栈深≠窗口相对深——FIX.md §14 与实况一致，未被掩盖。
- **调试插桩残留**：两笔 diff 中 `grep print(/DEBUG/probe_/XXX/TODO` = **零命中**（唯一 "probe" 为 probe_match_min 注释引用）。core/ 现树存量 34 处运行期 print 均为历史轮遗留且全部被 `_R23N20_DEBUG`/`DBG_OR` 等环境变量门控（commit a6666b92 引入，非本轮产物）——不计入本轮违规，登记为主代理后续卫生清理观察项。

---

## §3 变体攻击结果表（对抗性独立验证，8/8 破口各 1 变体）

变体全部为复核工程师新构（`test_repros/round4/rv4_*.py`，py_compile 编译 → pycdc 反编译 → pyc_verify single）。MISMATCH = 新边界，按破口状态机登记为 Bxx-R，不否定原登记面封闭，禁止宣称全族封闭。

| 变体 | 针对破口 | 形态 | 实测读数 | 判定 |
|---|---|---|---|---|
| rv4_12_b12_or_mapping | B12 | mapping/序列形状 or 交替 + or+as 捕获 + 深嵌套 or（3 单元） | **1/4**（or_map_nested / or_as_capture / or_mixed_deep 全 MISMATCH） | **新边界 B12-R** |
| rv4_13_b13_mid_wildcard | B13 | 尾通配非 None 体 + 同函数第二支 match(mapping 头+尾通配) + case 体内嵌套 match 尾通配（3 单元） | **2/4**（two_wildcards_one_fn / nested_wildcard_tail MISMATCH） | **新边界 B13-R** |
| rv4_14_b14_cap_rest | B14 | 序列多捕获乱序取用体 + mapping 具名捕获+**rest 混布 + 捕获尾 case（3 单元） | **4/4 success** | **通过**（登记面无新边界） |
| rv4_15_b15_leading_dual_exit | B15 | match 前 3 条前导语句 + case 体早 return/其余 fall-through 双出口 + 共享尾（3 单元） | **4/4 success** | **通过** |
| rv4_16_b16_loop_nest | B16 | while>match>match 三层 + for>match>while + while>match 尾通配 break/continue（3 单元） | **2/4**（while_match_match / while_match_continue MISMATCH；for_match_while PASS） | **新边界 B16-R** |
| rv4_17_b17_try_match | B17 | try/except/**else** 包 match + case 体 raise 进 try + try/**finally** 包 match（3 单元） | **2/4**（try_else_match 控制流 MISMATCH；try_finally_match 字节 MISMATCH） | **新边界 B17-R** |
| rv4_18_b18_class_slots | B18 | 多关键字乱序槽位 + 位置/关键字混用 + guard 含函数调用/算术混合链（3 单元+类定义） | **6/6 success** | **通过** |
| rv4_19_b19_subject_call | B19 | 方法链尾调用 subject + 调用后下标 subject + 裸调用 subject + await subject（async def 包裹）（4 单元） | **11/11 success** | **通过** |

### 新登记破口（B12-R / B13-R / B16-R / B17-R，Round 4 输出 → 交主代理裁决是否入下轮）

- **B12-R**（结构形状 or 交替族）：`case {'a': 1} | {'a': 2}:` → 拆成两个独立 case 且**体变 pass（体丢失）**；`case 1 | 2 as v:` → as 捕获名丢失（体仍引用 `v` → 潜在 NameError）；`case {'k': w1} | {'k': w1, 'j': _} as w:` → 跨交替同名捕获退化为幻影字面量 `case {'k': 2}:`、as 绑定丢失、体被搬出 match。输出语法合法（compile 通过）但语义破缺——与已封闭的 B12 登记面（混合树 str() 外泄 → compile_error）不同层。机制方向：or-merge 等价体合并（region_analyzer `_mr_finalize_match_region` 族）仅对字面量交替生效；形状交替不合并且拆 case 时 pattern 归属/体归属双错。
- **B13-R**（尾通配封闭面的两处溢出）：① 同函数**第二支** match（mapping 头 + 尾通配）整体坍缩为 `if True: if 1: if ('k',) is not None:` 幻影 if 链（体 `r2 = kk` 引用未绑定名）；② case 体内嵌套 match（序列模式 + 尾通配）的内层 match 整体消失（内层 case pattern/体丢失，外层体直接引用内层捕获名）。已封闭面 = 顶层单 match 链尾通配（r4_03/r4_08 7/7 实证）。
- **B16-R**（循环×match 的两处溢出）：① while>match>**match** 三层中内层 match 降级为 if/else 链（外层 while+match 结构保持）；② while>match 的**尾通配 case 体 = break** 时整个 case 丢失（`case _: break` 消失，while 退化为无 break 版本）。for>match>while 形态 PASS（变体实证）。机制方向：内层 match 头位于外层 case 体内时 B16-F4 收口后二次扫描未接管（或接管后判据不足）；尾通配+break 的体行走与循环出口跳转的归属争抢。
- **B17-R**（try 包 match 的两处溢出）：① try/except/**else** 包 match 时 **else 子句整体丢失**（try/except 壳保留）；② try/**finally** 包 match 时首 case 体退化为 pass（finally 壳保留，case 体指令丢失，Different bytecode）。已封闭面 = try/except 包 match 基本形态（r4_13 7/7 实证）。

变体产物：`rv4_12_b12_or_mapping / rv4_13_b13_mid_wildcard / rv4_14_b14_cap_rest / rv4_15_b15_leading_dual_exit / rv4_16_b16_loop_nest / rv4_17_b17_try_match / rv4_18_b18_class_slots / rv4_19_b19_subject_call`（.py/.pyc/OK.py 留存于 test_repros/round4/，全部由 py_compile/pycdc 生成）。

---

## §4 哨兵与批次一判据保持

### 4.1 哨兵复跑（FIX.md §12.2/§12.3 声明 vs 实测）

| 哨兵 | 声明 | 实测 | 判定 |
|---|---|---|---|
| site-packages/fly/data/quotation.pyc | 152/153 | **152/153** | 持平 |
| site-packages/IQCommon/strategy/jq_trans_module.pyc | 65/65 | **65/65** | 持平 |
| site-packages/fly/data/quote.pyc | 84/92 | **84/92** | 持平 |
| site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | 118/128 | **118/128** | 持平 |
| site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 41/43 | **41/43** | 持平 |
| round3/r3_27_loop_try_with_match（B16 哨兵） | 9/9 | **9/9** | 持平 |
| round3/r3_32_comp_loop_interleave（B16 哨兵） | 11/11 | **11/11** | 持平 |
| round3/r3_33_b11r_or3prefix | 4/4 | **4/4** | 持平 |
| round3/r3_34_b10r_innerforelse_break（B10-R 残留） | 1/2 | **1/2** | 持平 |
| round1/r1_01_stmt_andor3 | 2/2 | **2/2** | 持平 |
| round1/r1_03_chain3 | 2/2 | **2/2** | 持平 |
| round1/r1_18_ortail_return | 2/2 | **2/2** | 持平 |
| round2/r2_02_try_finally_only | 3/3 | **3/3** | 持平 |
| round2/r2_03_try_four_part | 3/3 | **3/3** | 持平 |
| round2/r2_05_try_loop_try | 2/2 | **2/2** | 持平 |

哨兵零回退成立。B11-R2（r4_or4_and2 1/2）与 B10-R（r3_34 1/2）残留如实持平，未混入本轮封闭声明。

### 4.2 批次一判据保持（批次二 diff 语义 grep）

| 判据 | 声明 | 实测 | 判定 |
|---|---|---|---|
| `_mr_block_has_explicit_case_marker` | region_analyzer 8 处引用 + region_ast_generator 2 处引用原样 | region_analyzer 8 处、region_ast_generator :32053 实调 + :32051 注释引用 | **一致** |
| ast_converter 模式壳保真 | MatchMapping/MatchOr 壳原样 | ast_converter.py:1723/:1777/:1782 三壳在位，批次二未触碰该文件 | **一致** |
| B14 判据族 | 捕获头/fail 边/COPY 前缀原样 | `_extract_capture_head_store`(:1167)/`_fail_jump_target_offsets`(:1335)/`allow_own_as_store`(:1551) 全在位且批次二仅扩展调用点 | **一致** |

---

## §5 未落地项与 G0/BOM 核对

| 项 | 声明 | 实测 | 判定 |
|---|---|---|---|
| r4_04 余 2 单元 | match_map_nested / match_map_mixed_seq（嵌套 mapping 值槽位需绝对栈深种子，未落地交后续批次） | single 实测失败单元恰为 **match_map_nested、match_map_mixed_seq**（Different control flow） | **一致** |
| 原型死代码清除 | 「原型已自树移除（不留未接线的死代码）」 | grep pattern_parser 全文 stack_effect/绝对栈深/槽位标记项/opaque/seed 等原型标记 = **零命中**；`git status` core/ scripts/ 干净 | **一致** |
| G0 BOM | region_ast_generator.py 头 3 字节 efbbbf | **efbb bf** 在位 | **一致** |
| pattern_parser BOM 复原 | 无误加 BOM（222222） | 头 3 字节 **22 22 22**；region_analyzer.py/ast_converter.py 同为 222222 | **一致** |
| 调试插桩 | 零残留 | 两笔 diff 零命中（存量 env 门控 print 为历史遗留，见 §2.3） | **一致** |

---

## §6 终判

### 6.1 逐破口终判

| 破口 | 封闭声明 | 复核终判 | 依据 |
|---|---|---|---|
| **B12** | 批次一封闭（r4_04 4/6、r4_06 6/6、r4_09 7/7，compile 全通过） | **放行（登记面封闭）**，附新边界 **B12-R** | 读数一致；壳保真判据同层；变体暴露形状 or 交替拆 case/体丢/as 丢/幻影字面量新边界（输出合法但语义破缺，另层） |
| **B13** | 批次一封闭（r4_03 7/7、r4_08 7/7） | **放行（登记面封闭）**，附新边界 **B13-R** | 读数一致；NOP 显式标记判据非位置特例；变体暴露同函数第二支 mapping+尾通配坍缩、嵌套 match 尾通配丢失 |
| **B14** | 批次一封闭（4/4 验收单元全 MATCH、r4_07 6/6） | **放行**（变体亦通过） | 读数一致；捕获头/fail 边/COPY 前缀判据结构成立；rv4_14 4/4 |
| **B15** | 批次二封闭（r4_01/06/08/10/13/14 收尾全 MATCH） | **放行**（变体亦通过） | 读数一致；前缀切分/merge 块归属判据同层；rv4_15 4/4 |
| **B16** | 批次二封闭（r4_12 7/7） | **放行（登记面封闭）**，附新边界 **B16-R** | 读数一致；支配边界/回边再检测/汇合闭合三守卫嵌套无感成立；变体暴露 while>match>match 内层降级、尾通配+break 丢失 |
| **B17** | 批次二封闭（r4_13 7/7） | **放行（登记面封闭）**，附新边界 **B17-R** | 读数一致；异常表边排除/前驱闭合/try 体边界判据同层；变体暴露 else 子句丢失、try/finally case 体 pass 退化 |
| **B18** | 批次二封闭（r4_05 9/9、r4_09 7/7） | **放行**（变体亦通过） | 读数一致；SWAP 栈模拟与 CPython SWAP k 语义逐条核对一致；rv4_18 6/6 |
| **B19** | 批次二封闭（r4_11 10/10） | **放行**（变体亦通过） | 读数一致；类协议三元组判据同层；rv4_19 11/11（含 await subject） |
| r4_04 余 2 单元 | 未落地如实登记 | **通过登记核对**（非打回项） | 失败单元与 FIX.md §14 逐一对应；原型死代码确已清除 |

**打回项：零。** 两批次全部 7 个封闭声明通过复核（读数零虚报、判据零白名单、注记零缺失失真、哨兵零回归）。

### 6.2 Round 4 轮门禁预判

- **≥1 破口封闭：达成**（实际 7/7 封闭声明复核通过；96 单元 48/106 → 94 MATCH）。
- **建议门禁结论**：Round 4 轮门禁达成，可进入主代理全量验证（402 全量）。
- **禁止宣称**：Match 8 模式族「全族封闭」——B12-R/B13-R/B16-R/B17-R 四个新边界在案，wiki 表述应维持「value/singleton/or-字面量/类模式槽位/调用 subject 浅层封闭 + 循环×match/try×match 登记面封闭」级别。

### 6.3 402 全量回归风险点清单（供主代理验证关注，按风险降序）

1. **`_extract_case_guard_from_blocks` 臂链重构**（pattern_parser）：guard 提取面全量重写（真值臂/算术臂/捕获重读例外/fail_case_offset 极性），match 守卫面与非 match 调用点的幻影守卫风险。关注：site-packages 含 match+guard 的单元（quotation/quote/tlb 已抽验持平，其余 397 文件未抽验）。
2. **`_extract_case_pattern` 捕获头前置短路**（跨块收集之前返回 MatchAs）：所有 case 解析共用入口，误判捕获头则 pattern 整体丢失。关注：头块首 STORE 但非捕获的融合形态。
3. **`_mr_collect_case_body_blocks` 三处替换 `_collect_blocks_on_path`**：case 体收集语义全局变更（支配边界+汇合闭合）。关注：多 case 共享出口、case 体含循环的单元。
4. **merge 块标记归属变更**（`_mr_mark_match_blocks_generated` + 尾链行走 + :35777 解除-复标）：merge 块生成责任移交 `_generate_match`，存在双发/漏发两个方向的回归面。关注：match 后紧跟顺序语句（if/while/return）的单元。
5. **`_mr_dissolve_match_subsumed`**：溶解 entry∈case 头的 If/BoolOpRegion，NOP 豁免之外的误杀残余风险。关注：case 头与体首条件同块且无 NOP 的畸形形态。
6. **B19 subject 行走 LOAD_GLOBAL/LOAD_NAME 保留**：类模式协议三元组判定失配时 subject 材料混入。关注：类模式 + 复杂 subject 组合单元。
7. **match×match 内层优先（双落点）与嵌套扫描收敛循环**：同入口重复建区去重、真子集竞争。关注：r3_32 类 comprehension 内嵌结构、深层 match 嵌套。
8. **B16 break 判定（目标∉region.blocks ∧ 有 Loop 父）**：函数级 return 经纯跳转块中转 + match 在循环内时可能误发 Break。关注：r3_27/r3_34 族。

### 6.4 交主代理派打回/后续批次的处置要求（Bxx-R 验收组）

| 新边界 | 机制一句话 | 最小验收组（pyc_verify single success） | 回归哨兵 |
|---|---|---|---|
| B12-R | 形状 or 交替不合并：拆 case 时体归属丢失 + as 绑定丢失 + 跨交替同名捕获幻影化 | rv4_12_b12_or_mapping 1/4 → 4/4（or_map_nested、or_as_capture、or_mixed_deep） | r4_06 6/6、r4_09 7/7、probe_match_min 3/3、quotation 152/153 |
| B13-R | 同函数第二支 match(mapping+尾通配) 坍缩幻影 if 链；case 体内嵌套 match+尾通配内层整体丢失 | rv4_13_b13_mid_wildcard 2/4 → 4/4 | r4_03 7/7、r4_08 7/7、r4_13 7/7 |
| B16-R | while>match>match 内层 match 降级 if 链；while>match 尾通配+break case 整体丢失 | rv4_16_b16_loop_nest 2/4 → 4/4 | r4_12 7/7、r3_27 9/9、r3_32 11/11 |
| B17-R | try/except/**else** 包 match 丢 else 子句；try/**finally** 包 match 首 case 体 pass 退化 | rv4_17_b17_try_match 2/4 → 4/4 | r4_13 7/7 |
| r4_04 余 2 单元 | mapping 值槽位需 dis.stack_effect 全函数线性追踪提供窗口绝对基深（FIX.md §14 前置依赖声明） | r4_04 4/6 → 6/6（match_map_nested、match_map_mixed_seq） | r4_04 现 4 绿单元、quotation 152/153 |

（B10-R r3_34 1/2、B11-R2 r4_or4_and2 1/2 维持 Round 3 登记，继续挂账。）

---

*本报告全部读数由复核工程师 2026-10-02 亲手跑出：round4 组 17 支 + 哨兵 15 支 + 变体 8 支（8 次编译 + 8 次反编译 + 8 次 single）+ 两笔 commit 67 hunk 逐行审读。*
