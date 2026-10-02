# Round 4 修复（批次一：P0 B12 + P2 B13 + P4 B14）

- 修复工程师：Round 4 批次一
- 日期：2026-10-02
- 唯一判据：`scripts/pyc_verify.py`（single）。所有 `*OK.py` 由 `python pycdc.py -o test_repros/round4/XOK.py test_repros/round4/X.pyc` 重新生成，未手改任何 `*OK.py` 既有产物、`site-packages/`、`.trae/specs/` 既有内容。
- 修改源文件（3 支，全部为非 G0 文件，文件头 3 字节核对无变化；`region_ast_generator.py` 未改动，其 G0 BOM `efbbbf` 原样在位）：
  - `core/cfg/ast_converter.py`（B12）
  - `core/cfg/region_analyzer.py`（B13 + B14 体首元素边界 + B12 伴生 or-merge 对齐）
  - `core/cfg/pattern_parser.py`（B14 + B12 伴生 capture+guard 算术守卫）
- 调试插桩：探针全部位于进程外临时脚本（/tmp、D:/Temp），源码树 `git diff` grep `print(/DEBUG/probe/XXX/TODO` 零残留。

---

## §1 B12（P0）— Match 模式发射层混合树 `str()` 回退灾难

**根因**（实证复核与评审一致，另发现第三生产者路径）：发射层 `code_generator.py:3374` 的 `str(pattern)` 回退本身不是病根——病根在中层 `ast_converter._convert_match_pattern` 把「模式」降格为「表达式」：
1. `ast_converter.py:1710`（原）MatchMapping → `ASTDict(keys, values)`：value 侧子模式是纯 dict 壳（无 `to_code`），ASTDict 渲染 `str(dict)` 外泄（r4_04 爆点，`<core.ast_nodes.ASTName object at 0x…>`）；
2. `ast_converter.py:1761`（原）MatchOr → `ASTBinary(BIN_OR)` 链：or 交替为序列形状/MatchAs dict 壳时对 dict 子节点 `str()` 外泄（r4_06、r4_09 爆点）；
3. MatchAs 分支的裸 ASTConstant 子节点经由 1/2 的混合树间接外泄（直接路径本可渲染）。

**修复落点**（走真正的模式渲染路径，不对 `str()` 打补丁）：
- `core/cfg/ast_converter.py:1702-1716`：MatchMapping 保留 `{'type':'MatchMapping','keys':[ASTNode…],'patterns':[子模式…],'rest':…}` dict 壳（键经 `_convert_expression`、值递归 `_convert_match_pattern`），由 `code_generator._generate_match_pattern` 的 MatchMapping 分支按模式语法渲染 `{'k': pat, **rest}`。
- `core/cfg/ast_converter.py:1764-1784`：MatchOr 保留 `{'type':'MatchOr','patterns':[…]}` dict 壳（含 left/right 旧格式归一），由 MatchOr 分支渲染 `pat1 | pat2 | …`。
- 伴生（识别层，`core/cfg/pattern_parser.py`）：
  - `:2076-2092` `_extract_mapping_pattern` 的嵌套值模式判据补入 `MATCH_MAPPING`（此前嵌套 mapping 坍缩为 GET_LEN 常量幻影 `{'user': 2}`）；
  - `:2095-2126` `**rest` 的 STORE 归属：DICT_UPDATE 之后首个 `STORE_*` 是 rest 绑定，值槽位行走跳过它（此前 `case {'type': t, **rest}` 的 STORE rest 被误填 slot 0 → `{'type': rest}` 且 rest 双绑，发射 `case {'type': rest, **rest}:` 语法非法）；
  - `:514-525 + :563-651 + :653-680` capture+guard 算术守卫链回退（`case v if v % 2 == 0:` 的守卫此前整体丢失 → 裸捕获 `case v:` 出现在非末位 → Python 语法不可达错误）；`region_analyzer.py:13591-13610` or 等价体合并时 case_blocks 同步压缩为每组首块，消除 case_blocks/case_patterns/case_guards 三者下标错位（守卫借位丢失）。

**判据形态**（结构事实表述）：mapping/or 模式是模式匹配节点，其子节点必须保持模式类型分派（渲染端按 `type` 分派到各模式分支生成合法 Python 模式语法），禁止折叠为表达式节点——折叠即产生「dict 壳无 to_code」的混合树。嵌套 mapping 判据 = UNPACK 后继的 `MATCH_*` 操作码形态；rest STORE 判据 = DICT_UPDATE→STORE 配对（编译器发射的 rest 协议）；守卫链判据 = 模式头 STORE 之后的 LOAD_VAR 开头表达式链被 fail 极性条件跳转终止（链内仅 LOAD_*/LOAD_CONST/BINARY_OP/COMPARE_OP/IS_OP/CONTAINS_OP，操作数栈求值），链起点以「模式头 STORE 在前」封闭。

**docstring 三要素与 C1/C2/C3 落点**：`ast_converter.py:1702-1712/:1764-1773`（识别/归约/映射 + [C2] 嵌套即抽象节点、嵌套无感声明）；`pattern_parser.py:566-585`（`_extract_arithmetic_guard` 三要素 + [C1]/[C2]/[C3] 全条款）；`region_analyzer.py:13599-13610`（压缩对齐的归属论证）。

**读数**：r4_04 **0/6 → 4/6**（compile 通过；余 2 单元见 §5 未封闭）、r4_06 **0/6 → 5/6**（compile 通过；余 1 单元 = B15）、r4_09 **0/7(compile_error) → 4/7**（compile 通过；`case 0` 幻影捕获、`case 3|5|7` MatchAs 包裹链、guard 丢失三项已封闭，余 3 单元 = B16/B18 族）。最低验收线「compile 通过且单元数不倒退」全部达成。

---

## §2 B13（P2）— 序列/星号/类模式链尾通配 `case _` 整体丢失

**根因**（实证复核修正了评审的锚点归因）：尾 `case _` 块的字节码形态为 `POP_TOP（丢弃被匹配值）; NOP（显式 case 体标记）; <体>`——**POP_TOP 在 NOP 之前**。评审指认的 `region_analyzer.py:13841-13850` 连接块判据只吞食 `[POP_TOP]` 单指令块形态（体独立成块时，该形态经既有 NOP-首块判据自愈）；实际主吞食点在 `jump_instr is None` 分支的前置判断 `_is_pattern_fail_handler`（原 :14909）：尾通配块 POP_TOP+平凡 return 且前驱含 `MATCH_*` → 被误判为 pattern fail handler → `break`，case 永不登记。次吞食点为 `_is_implicit_default_body`（原 :14871）：其 NOP 标记检查要求 NOP 是首条非 NOISE 指令，POP_TOP 前缀使其漏判（`return None` 体时判为隐式 default；`return ()` 等非 None 体时虽登记但 pattern/body 归属仍错）。字面量链不触发的分歧点（评审待查项）：字面量尾 case 块无 POP_TOP 前缀，NOP 即首条指令，既有判据命中。

**修复落点**（同层结构事实，无位置特例）：
- `core/cfg/region_analyzer.py:14959-14994` 新增 `_mr_block_has_explicit_case_marker`：跳过 NOISE 与前导 POP_TOP 后认 NOP 标记（NOP ∈ NOISE_OPS，必须先于 NOISE 跳过检查——首版实现踩过此坑，已修）。
- `:14997-15003` `_is_pattern_fail_handler` 顶部守卫：携带显式 case 标记的块不是 fail handler。
- `:14919-14940` `_is_implicit_default_body` NOP 检查扩展：允许前导 POP_TOP 后认标记。
- 连接块判据（:13850-13860）未改动：`[POP_TOP]` 纯连接形态的体块以 NOP 开头，走既有登记路径自愈。

**判据形态**：NOP 是 CPython 按 case 发射的显式 case 体标记（无 `case _` 的隐式 fail 续块 `POP_TOP; LOAD_CONST None; RETURN_VALUE` 无 NOP——`match x: case [a,b]: …` 与 `case _:` 的对照实测），与「第几个 case」「是否最后一个」无关。

**docstring 三要素与 C1/C2/C3 落点**：`region_analyzer.py:14960-14985`（识别条件=块内 NOP 标记形态/归约方式=纯块内操作码序列判据/AST 映射=MatchAs wildcard case；[C1] 只读 block.instructions、[C2] 不窥视子父区域、[C3] 编译器显式结构标记非位置特例）；`_is_implicit_default_body` 扩展处 `:14919-14940` 同步注记。

**读数**：r4_03 **2/7 → 7/7**（验收达成；含评审注记的 R4-O1 观察点 match_seq_list2 由「判据归一化的假 Equal」转为真 Equal）、r4_08 **2/7 → 6/7**（4 个尾丢单元全封闭，余 match_star_body_work = B15）、r4_05 **5/9 → 7/9**（尾丢单元 match_class_positional/mixed 封闭）、r4_10 **2/6 → 3/6**。

---

## §3 B14（P4）— 捕获尾 case 捕获名丢失 + case 体首元素被模式头吞食

**根因**（三处，均实证）：
1. **捕获名丢失**：捕获 case（`case other:`）头块无条件跳转，经 `_mr_collect_case_body` 的 `jump_instr is None` 分支登记时 pattern **硬编码** `{'type': 'MatchAs'}`（从不调用 parse）——`:13699`（原）；pattern_parser 侧 `_extract_case_pattern` 终局 else 分支也无捕获头 STORE 归属。
2. **幻影捕获注入**（r4_09 `case 0` → `case 0 as v`，同 STORE 归属族）：`_find_as_binding` 的策略 2/3 BFS 无差别扩展全部后继，经 fail 边（模式失败条件跳转目标 = 下一 case 头块）把下一 case 的捕获头 STORE v 误识为本 case 的 as 绑定。
3. **体首元素被吞**：`_mr_compute_case_body_start_indices` 在模式绑定 STORE 消耗完后不停止，body 首条 `LOAD_CONST`（如 `return (other, 0)` 的常量 `0`/`("notmap", whatever)` 的 `"notmap"`）被其 LOAD_CONST 跳过分支吞食（r4_07 实测 start_indices 把 `[STORE other, LOAD_CONST 'fallback', LOAD other, BUILD_TUPLE, RETURN]` 切到 index 2，'fallback' 丢失）。

**修复落点**：
- `core/cfg/region_analyzer.py:13708-13727`：`jump_instr is None` 分支登记时调用 `parse_case_pattern`，仅接受「带名 MatchAs」，其余保守回退通配（零行为面扩大）。
- `core/cfg/pattern_parser.py:947-957 + :968-1013`：`_extract_capture_head_store`（终局 else 分支归因）：块不含模式匹配指令且有效指令流为 `POP_TOP* 后紧跟 STORE_*` → 该 STORE 是捕获绑定（栈平衡事实：STORE 直接消费前序 case 失败路径遗留的被匹配值副本；case 体 STORE 前必有加载指令，故该形态唯一对应捕获头）。
- `core/cfg/pattern_parser.py:1136-1166 + :1170-1218 + :1270-1310`：`_fail_jump_target_offsets` + `_find_last_store_on_success_path`/`_find_store_in_successors` 改为全程排除 fail 极性条件跳转目标（IF_FALSE/IF_NONE/IF_NOT_NONE 族；IF_TRUE 是 or-guard 成功边保留）——as 绑定只在成功路径上，fail 边目标是下一 case 头块。
- `core/cfg/region_analyzer.py:13316-13343`：`_mr_compute_case_body_start_indices` 的 STORE 分支在模式绑定名全部消耗（且无未完成 unpack 槽位）后立即 `break`——模式头 STORE 属于模式绑定，其后指令全部属于 case 体（每块唯一归属）。
- 伴生（嵌套序列 `[[a, b], c]` 被腐蚀为 `[[a, b] as c, _]`，r4_03.match_seq_nested）：`core/cfg/pattern_parser.py:1342-1360 + :1394-1399 + :1476-1490 + :1501-1517 + :1563-1611`——`allow_own_as_store` 参数 + `_nested_sequence_slot_consumers_end` 消费计数：内层子模式自身 as 绑定的唯一结构事实是子模式 `MATCH_SEQUENCE` 前紧邻 `COPY 1`（`[[a,b] as c, d]` 与 `[[a,b], c]` 的 STORE 流字节相同，纯 STORE 序列不可区分）；无 COPY 时内层槽位消耗完的 STORE 归外层余下槽位，外层跳过子模式内部指令后继续绑定（不再整体 `break` 丢弃余下槽位）。

**判据形态**：一切判据为操作码形态（POP_TOP*/STORE 前缀、fail 边极性、COPY 前缀、UNPACK argval 槽位数），无函数名/文件名/字面量白名单，无「最后一个 case」位置特例。覆盖一般结构：捕获头判据对首/中/尾 case 同判（实测 r4_01 中间捕获尾、r4_07 POP_TOP 前缀尾、r4_10 默认尾）；fail 边排除对任意链深的 or 交替块同判（r4_09 三交替 or 修复）。

**docstring 三要素与 C1/C2/C3 落点**：`pattern_parser.py:969-1002`（捕获头 STORE）、`:1137-1165`（fail 边集合）、`:1355-1373`（allow_own_as_store）、`:1564-1584`（消费计数）；`region_analyzer.py:13708-13727`、`:13318-13343`。全部含识别条件/归约方式/AST 映射 + [C1]（只读 L(A)）/ [C2]（子模式抽象节点、不窥视内部）/ [C3]（显式守卫排除通配形态与 fail 边泄漏）条款。

**读数（4/4 验收单元全转 MATCH）**：
| 单元 | 修复前 | 修复后 |
|---|---|---|
| r4_01.match_value_int_str_mixed | MISMATCH（`case _` + `(other,0)`→`(other,)`） | **MATCH** |
| r4_07.match_capture_after_cases | MISMATCH | **MATCH** |
| r4_07.match_capture_in_mapping | MISMATCH | **MATCH** |
| r4_10.match_default_capture_tail | MISMATCH | **MATCH** |
哨兵：r4_07.match_capture_bare（字节等价降级面）保持 MATCH（r4_07 全文件 6/6）。

---

## §4 自测读数全表

### 4.1 Round 4 Match 组（single，现树）

| 文件 | 登记基线 | 修复后 | 判定 |
|---|---|---|---|
| probe_match_min | 3/3 | **3/3** | 持平（绿面） |
| r4_01_match_value | 4/6 | **5/6** | 改善（match_value_int_str_mixed 转 MATCH；match_value_expr_body = B15 留批次二） |
| r4_02_match_singleton | 5/5 | **5/5** | 持平（绿面） |
| r4_03_match_sequence | 2/7 | **7/7** | **验收达成**（B13；含嵌套序列腐蚀修复） |
| r4_04_match_mapping | 0/6（compile_error） | **4/6（compile 通过）** | B12 最低线达成（余 2 单元见 §5） |
| r4_05_match_class | 5/9 | **7/9** | 改善（尾丢单元封闭；余 2 = B18） |
| r4_06_match_or | 0/6（compile_error） | **5/6（compile 通过）** | B12 最低线达成（match_or_capture_body = B15） |
| r4_07_match_capture_wildcard | 3/6 | **6/6** | **验收达成**（B14） |
| r4_08_match_star | 2/7 | **6/7** | 改善（4 尾丢封闭；match_star_body_work = B15） |
| r4_09_match_guard | 0/7（compile_error） | **4/7（compile 通过）** | B12 最低线达成（幻影捕获/or 包裹链/guard 丢失封闭；余 3 = B16/B18 族） |
| r4_10_match_default_tail | 2/6 | **3/6** | 改善（match_default_capture_tail 转 MATCH；余 = B15×2 + 尾体装配漂移） |
| r4_11_match_complex_subject | 9/10 | **9/10** | 持平（OK.py 逐字节不变；match_subject_call = B19） |
| r4_12_match_nested_loop | 0/7（compile_error） | 0/7（compile_error） | 持平（B16，批次二；产物仅 4 行级差） |
| r4_13_match_try | 3/7 | **3/7** | 持平（OK.py 逐字节不变；B17/B15/B16 批次二） |
| r4_14_match_case_body | 3/7 | **3/7** | 持平（OK.py 逐字节不变；B15/B16 批次二） |
| n4_01_no_match_control（负对照） | 7/7 | **7/7** | 持平（无误报基线） |

### 4.2 site-packages 哨兵

| 哨兵 | 登记基线 | 修复后 | 判定 |
|---|---|---|---|
| fly/data/quotation.pyc | 152/153 | **152/153** | 持平 |
| IQCommon/strategy/jq_trans_module.pyc | 65/65 | **65/65** | 持平 |
| fly/data/quote.pyc | 84/92 | **84/92** | 持平 |
| IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | 118/128 | **118/128** | 持平 |
| IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 41/43 | **41/43** | 持平 |

### 4.3 round1–3 抽验与附加回归

| 项 | 登记读数 | 修复后 | 判定 |
|---|---|---|---|
| round3/r3_33_b11r_or3prefix.pyc | 4/4（FIX-B11c-3 封闭面） | **4/4** | 持平 |
| round3/r3_34_b10r_innerforelse_break.pyc | 1/2（不变差即可） | **1/2** | 持平 |
| round1/r1_01_stmt_andor3.pyc | 2/2 | **2/2** | 与登记一致 |
| round1/r1_03_chain3.pyc | 2/2 | **2/2** | 与登记一致 |
| round1/r1_18_ortail_return.pyc | 2/2 | **2/2** | 与登记一致 |
| round2/r2_02_try_finally_only.pyc | 3/3 | **3/3** | 与登记一致 |
| round2/r2_03_try_four_part.pyc | 3/3 | **3/3** | 与登记一致 |
| round2/r2_05_try_loop_try.pyc | 2/2 | **2/2** | 与登记一致 |
| round3/r3_27_loop_try_with_match.pyc | 9/9 | **9/9** | 持平（批次二 B16 哨兵预检） |
| round3/r3_32_comp_loop_interleave.pyc | 11/11 | **11/11** | 持平（批次二 B16 哨兵预检） |
| 历史 round4 boolop/continue 4 支（r4_01b/r4_03b/r4_05b/r4_06c） | 各 2/2 | 各 **2/2** | 持平（临时产物验证后即删，未留 OK.py） |

零回归。

---

## §5 未封闭项及原因（如实登记）

| 项 | 读数 | 机制（本轮实证） | 未落地原因 |
|---|---|---|---|
| r4_04.match_map_nested / match_map_mixed_seq | 4/6 中余 2 | 嵌套 mapping **值槽位**提取：`{"user": {"name": n, "roles": [r, *others]}}` 编译为 `UNPACK 2; SWAP×5; <内层序列机制>; STORE r; STORE others; POP_TOP×4; STORE n`——值槽位 STORE 顺序非槽位序（SWAP 栈重排 + 内层机制内联），现行走按 attr_idx 顺序填槽，把内层序列的 GET_LEN 常量误判为 slot 0 字面量（`'name': 1`）、'roles' 槽吞 `r` | 正确修复需把 mapping 值行走升级为含 SWAP 的完整栈模拟（sequence 提取器已有 unpack_stack，mapping 没有）；改动面大、回归风险高（现绿 4 单元全在 mapping 提取路径），交批次二随 B18（类模式槽位）同栈模拟一并处理。嵌套 mapping **首层**递归（`MATCH_MAPPING` 补入判据）本轮已落地 |
| r4_06.match_or_capture_body | 5/6 中余 1 | B15（前导 `total=[]` 吞失 + `return total` 物化进 case 体），`_mr_compute_case_merge` 出口归属 | 批次二（B15） |
| r4_01.match_value_expr_body、r4_08.match_star_body_work、r4_10.match_default_no_wildcard / match_default_tail_with_work | — | B15 同族 | 批次二（B15） |
| r4_10.match_default_nested_tail | — | 尾 case 体 if/elif 的条件块被 case 链行走当作后续 case 认领（`case 100:`/`case 10:` 幻影 case），尾体归属判据 | 批次二（B15/尾体归属族）；本轮 B13 的 NOP 标记判据是其前置依赖（尾 case 现已登记，仅体装配漂移） |
| r4_09.match_guard_capture / match_guard_bool / match_guard_class | 4/7 中余 3 | match→if 链降级（subject 块与 case 头同块形态、or/and 守卫区域降级）与类模式 guard（B18） | 批次二（B16/B18） |
| r4_05.match_class_kwargs / match_class_nested_value | 7/9 中余 2 | B18（类模式关键字槽位错排 + guard 丢失） | 批次二（B18） |
| r4_12 / r4_13 / r4_14 / r4_11 全部余项 | 持平 | B16/B17/B19 | 批次二 |

## §6 合规自检

- 判据全部为区域归约同层结构事实（操作码形态/跳转极性/栈平衡/UNPACK argval），无函数名/文件名/字面量白名单，无跨层启发式；
- 无「最后一个 case」类位置特例（B13 用编译器 NOP 标记、B14 用栈平衡与 fail 边极性）；
- 嵌套无感：B13 的 NOP 标记由编译器按 case 发射（与深度无关）；B14 的捕获头/fail 边/COPY 前缀判据对任意链位置与嵌套深度同判（嵌套序列修复同时覆盖 `[[a,b],c]`、`[[a,b] as c,d]`、`[[a,b],c] as whole` 三种编译同构）；每处修改 docstring 均含识别条件/归约方式/AST 映射三要素与 [C1]/[C2]/[C3] 条款注记；
- `region_ast_generator.py` 未改动；G0 BOM 自检：`region_ast_generator.py` 头 3 字节 `efbbbf` 在位，`region_analyzer.py`/`pattern_parser.py`/`ast_converter.py` 头 3 字节 `222222`（无 BOM，与改前一致）；
- 调试探针零残留（探针均在进程外临时脚本，源码 diff 无 print/DEBUG/探针标记）。
