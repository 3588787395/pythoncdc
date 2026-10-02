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

---

# Round 4 修复（批次二：P1 B16 + P3 B15 + P5 B17 + P6 B18 + P7 B19）

- 修复工程师：Round 4 批次二
- 日期：2026-10-02
- 唯一判据：`scripts/pyc_verify.py`（single）。所有 `*OK.py` 由 `python pycdc.py -o test_repros/round4/XOK.py test_repros/round4/X.pyc` 重新生成，未手改任何 `*OK.py` 既有产物、`site-packages/`、`.trae/specs/` 既有内容（仅本文件追加本章节）。
- 修改源文件（3 支）：`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`（G0 BOM `efbbbf` 在位）、`core/cfg/pattern_parser.py`；`ast_converter.py`、`code_generator.py` 未改动。
- 批次一判据零回退：`_mr_block_has_explicit_case_marker`（region_analyzer 8 处引用 + region_ast_generator 2 处引用原样在位）、ast_converter 模式壳保真（MatchMapping/MatchOr 壳 :1777/:1782 原样）、B14 的捕获头/fail 边/COPY 前缀判据原样。树中既有批次二在途改动（会话中断遗留），本批次在其基础上续作并收尾，未回退其在途判据。
- 调试插桩：探针全部位于进程外临时脚本（已删除 `_r4b2_dump.py`/`_r4b2_probe.py`），源码 diff grep print/DEBUG/probe/XXX/TODO 零残留（唯一 "probe" 命中为注释中对复现名 probe_match_min 的引用）。

---

## §7 B16（P1）— 循环×match 装配灾难

**根因**（三项，均实证）：循环体块被 LoopRegion 先占后，match 二次扫描失败/重复建区（同一入口块重复 MatchRegion、外层 match 占住内层体块）；case 链行走把循环结构块（旋转 while 迭代再检测块、FOR_ITER 块）拆成幻影 case；`case _:` 头块融合体首 if 条件时（NOP + 体条件同块），体内容被当作下一 case 检查块继续跟进拆成幻影 case 链。

**修复落点**（region_analyzer.py，含会话在途判据的收尾）：
- `:1632-1652` 嵌套 match 二次扫描收敛循环（match×match 多层：每轮只扫新区域，无新区域即收敛）+ `:1774-1826` `_mr_dissolve_match_subsumed` 溶解被 match 链误认领的同构条件/布尔区域（判据 = 候选 blocks ⊆ MatchRegion.blocks 且 entry == subject_block 或 entry ∈ case_blocks）；
- `:1827-1836`/`:3358` match×match 内层优先：同类型 MatchRegion 块集真子集者在 block_to_region 竞争中获胜；
- `:13221-13235` 子链去重（同一 case 头块只归属一条 case 链）+ `:15130-15138` 入口同块去重（同一 subject 块只建一个 MatchRegion）；
- `:13608-13632`/`:13943-13983` `_mr_body_walk_predicates_closed`：merge 汇合闭合判据（支配松弛版）——未闭合前驱全部受体入口支配（循环回边形态）→ 体内部块；否则链外汇合块（真 merge）；
- `:13633-13723` `_mr_collect_case_body_blocks`/`_mr_collect_simple_body_blocks`：case 体行走统一接入支配边界 + 回边再检测排除 + 汇合闭合守卫；
- `:14146-14160`/`:14363-14375` 链行走「下一 case 必须受当前 case 支配」（循环再检测块不是下一 case）；`:14075-14098`/`:14146-14155` 显式 case 体标记（NOP）→ 默认 case 头短路（体可含 if 等条件结构，不再拆幻影 case）。

**判据形态**：支配关系、跳转方向（回边目标支配 subject）、块集包含、NOP 显式标记——全部同层结构事实；无位置/名字特例。嵌套无感：for/while×match（r4_12 全组）、match×match（收敛扫描 + 内层优先）、try×match（r4_13）三向同判。

## §8 B15（P3）— match 前导初始化吞失 + 尾 return 物化进 case 体

**根因**（两项，实证）：① 默认 case（无跳转头块）的体行走沿后继无界前进，把 match 之后的顺序语句（尾 `return acc`、后继 if/else）物化进最后一个 case 体——且 merge 退化为误判的循环头（r4_01/r4_06/r4_08 形态：merge=B52/B76/B104 循环头）；② subject 块融合 match 之前的顺序语句时，subject 行走的 PATTERN_INSTRS 跳过分支把前导赋值指令丢弃，前缀提取无法还原。

**修复落点**：
- region_analyzer.py `:13695-13700`（`_mr_collect_simple_body_blocks` 纯连接头块 start 前移受汇合闭合守卫——r4_14.match_case_shared_body 的 `case _: pass` 后继 if 条件块不再被物化）；
- region_ast_generator.py `:31268`（`_subject_break_idx` 在 subject 行走全部 8 处 break 点记录边界）+ `:31391-31418`（前导语句提取改读原始块前缀 `[0:_subject_break_idx]`，按 STORE_*/POP_TOP 语句终结指令切分，经 `_build_statement` 发射在 Match 之前——非字面量 match 的 PATTERN_INSTRS 跳过不再吞前缀）；
- region_ast_generator.py `:32197-32240` merge 块由 `_generate_match` 在 match 节点之后按块归属发射（顺序约束：先发射后标记，`_generate_block_statements` 对已标记块短路返回空）；merge 是子区域入口（match 之后的顺序语句是 if/while 等结构，被外层包含性过滤排除在顶级发射序列之外）时以 `_generate_region` 生成子区域并随后继尾链行走（`_tail_cursor`，限 match 自有块）——r4_14.match_case_shared_body 的 `if x == 1 or x == 2: …` + `return result` 全链还原。

**判据形态**：语句终结操作码（栈平衡事实）、链级出口的块归属、`block_to_region` 所有权——同层结构事实，无位置/名字特例。

## §9 B17（P5）— try 包 match：try 壳整体丢失

**根因**（两项，实证）：① `_mr_compute_case_merge` 出口枚举走 `successors` 含异常表隐式边——try 包 match 时各 case 体的异常边共同指向 try 的异常分派块（PUSH_EXC_INFO 头块），被误判为 match 的 merge；② 支配种子把「前驱全部经异常边可达」的 handler 机制块卷入 match 区域，TryExceptRegion 反被装成 match 子区域（层级倒置）。

**修复落点**（region_analyzer.py）：
- `:13848-13857` 出口枚举排除 `exception_successors`（merge 不再误判为异常分派块）；
- `:14125-14152` 支配种子排除「无任何正常控制流前驱」的异常机制块（前驱闭合性判据）+ `_try_body_bound`：subject 落在某 TryExceptRegion 的 try 体内时 match 块集以该 try 体为界（C3 显式守卫：外层区域暴露的接口事实）。

**判据形态**：异常表边（编译器显式结构边）、前驱闭合性、try 体边界归属——同层结构事实。`match_wrap_try`（match 内 try 面）保持 MATCH；`match_wrap_try_finally` 同批转 MATCH。

## §10 B18（P6）— 类模式关键字槽位错排 + guard 丢失

**根因**（两项，实证）：① 类模式子模式指令的**出现顺序 ≠ 槽位顺序**（编译器把字面量测试提前、捕获绑定延后，SWAP 链轮转取值）——线性归属把字面量填进错误的槽（`Point(x=x, y=0)` → `Point(x=0, y=x)`）；② 守卫臂含函数调用/算术（`abs(x) + abs(y) <= 1`）时臂链提取器形态不覆盖，守卫整体丢失。

**修复落点**（pattern_parser.py）：
- `:2085-2163` `_extract_class_pattern` 属性槽位归属升级为含 SWAP 的栈模拟：栈元素 = 槽位号（0..count-1），SWAP k 交换 TOS 与 TOSk，LOAD_CONST+COMPARE（字面量）/STORE（捕获）/POP_TOP（通配）各消费 TOS 槽位，产出按槽位号排序的 patterns（与 keyword_keys 下标对齐；未消费尾槽以通配补位防串位）；
- `:365-421` guard_start 检测新增算术/调用混合臂形态（LOAD_VAR 开头的表达式段含 BINARY_OP/COMPARE/CALL/UNARY_*，被极性条件跳转终止，段内含 COMPARE 或 CALL）；
- `:524-560` `_mr_guard_arm` 形态 c 扩展（扫描集纳入 PRECALL/CALL，计算判据 `_COMPUTE_OPS` 纳入 CALL）；
- `:755-796` `_eval_guard_expr_stack` 支持 PRECALL（无栈效果）+ CALL（弹 argval 个实参与可调用对象 → Call 节点），段结果节点类型放宽为单一纯表达式节点。

**判据形态**：UNPACK/SWAP 栈协议（编译器子模式取值的显式事实）、表达式段操作码集合与跳转极性——同层结构事实，无名字/位置特例。**B16-C3 收窄**：region_analyzer `:14356-14375` 守卫续块判定收窄（fail 极性续块只有跳转目标 == next_case_offset 或其连接桩解析头 `_mr_skip_case_connectors` :14098 时才是守卫材料）——`case 2: acc += 2; if acc and x:` 的体首融合块不再误判为守卫（r4_14.match_case_multi_stmt）；类模式 fail 边经 POP_TOP 连接桩指向下一 case 头的形态由连接桩解析覆盖（r4_05.match_class_nested_value）。

## §11 B19（P7）— subject 为裸函数调用时主体丢失

**根因**（实证）：subject 行走的 PATTERN_INSTRS 跳过分支把 `LOAD_GLOBAL sorted`（subject 调用表达式的可调用对象加载）当作类模式协议材料跳过，subject_instrs 截断为 `[LOAD_FAST x, PRECALL, CALL]`，reconstruct 失败退化为 `_`。

**修复落点**（region_ast_generator.py `:31405-31436`）：LOAD_GLOBAL/LOAD_NAME 只有在后继为 `LOAD_CONST(tuple) + MATCH_*` 三元组时才是类模式协议材料（类引用 + keyword 名单）才跳过；否则（后跟实参加载/PRECALL/CALL）作为 subject 表达式材料保留。

**判据形态**：后继指令形态（同层结构事实），无名字/位置特例。属性链/元组/下标/方法链 subject 全保持 MATCH（r4_11 10/10）。

## §12 自测读数全表（pyc_verify.py single 实际输出）

### 12.1 Round 4 Match 组

| 文件 | 批次一后 | 批次二后 | 判定 |
|---|---|---|---|
| probe_match_min | 3/3 | **3/3** | 持平（绿面） |
| r4_01_match_value | 5/6 | **6/6** | **验收达成**（match_value_expr_body = B15） |
| r4_02_match_singleton | 5/5 | **5/5** | 持平（绿面） |
| r4_03_match_sequence | 7/7 | **7/7** | 持平 |
| r4_04_match_mapping | 4/6 | **4/6** | 持平（余 2 单元未落地，见 §14） |
| r4_05_match_class | 7/9 | **9/9** | **验收达成**（B18：match_class_kwargs 槽位栈模拟、match_class_nested_value guard CALL 链） |
| r4_06_match_or | 5/6 | **6/6** | **验收达成**（match_or_capture_body = B15） |
| r4_07_match_capture_wildcard | 6/6 | **6/6** | 持平 |
| r4_08_match_star | 6/7 | **7/7** | **验收达成**（match_star_body_work = B15） |
| r4_09_match_guard | 6/7 | **7/7** | **验收达成**（match_guard_class = B18 守卫链族） |
| r4_10_match_default_tail | 3/6 | **6/6** | **验收达成**（B15 三单元全封闭） |
| r4_11_match_complex_subject | 9/10 | **10/10** | **验收达成**（match_subject_call = B19） |
| r4_12_match_nested_loop | 0/7(批次一) | **7/7** | **验收达成**（B16） |
| r4_13_match_try | 3/7(批次一) | **7/7** | **验收达成**（B17 两单元 + B15 finally + B16 in_loop；r4_14.match_case_bool_guard 同批 MATCH） |
| r4_14_match_case_body | 3/7(批次一) | **7/7** | **验收达成**（B15 shared_body + B16 ifelse_body/multi_stmt） |
| n4_01_no_match_control（负对照） | 7/7 | **7/7** | 持平（无误报基线） |

14 攻击文件 + 探针 + 负对照：**13/14 文件全 success**（r4_04 4/6 余 2），96 单元中 94 MATCH。

### 12.2 site-packages 哨兵

| 哨兵 | 登记基线 | 批次二后 | 判定 |
|---|---|---|---|
| fly/data/quotation.pyc | 152/153 | **152/153** | 持平 |
| IQCommon/strategy/jq_trans_module.pyc | 65/65 | **65/65** | 持平 |
| fly/data/quote.pyc | 84/92 | **84/92** | 持平 |
| IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | 118/128 | **118/128** | 持平 |
| IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 41/43 | **41/43** | 持平 |

### 12.3 round1–3 抽验与附加回归

| 项 | 登记读数 | 批次二后 | 判定 |
|---|---|---|---|
| round1/r1_01、r1_03、r1_18 | 各 2/2 | 各 **2/2** | 持平 |
| round2/r2_02、r2_03 | 各 3/3 | 各 **3/3** | 持平 |
| round2/r2_05 | 2/2 | **2/2** | 持平 |
| round3/r3_33 | 4/4 | **4/4** | 持平 |
| round3/r3_34（B10-R 残留，不在本批范围） | 1/2 | **1/2** | 持平（不变差） |
| round3/r3_27（B16 哨兵） | 9/9 | **9/9** | 持平 |
| round3/r3_32（B16 哨兵） | 11/11 | **11/11** | 持平 |
| round4/r4_or4_and2（B11-R2 残留，不在本批范围） | 1/2 | **1/2** | 持平（不变差） |
| 历史 round4 boolop/continue 4 支（r4_01b/r4_03b/r4_05b/r4_06c，临时产物验证后即删） | 各 2/2 | 各 **2/2** | 持平 |

零回归。

---

## §13 合规自检

- 判据全部为区域归约同层结构事实：支配关系/跳转极性/回边目标/块集包含、NOP 显式标记、语句终结操作码、UNPACK/SWAP/COPY 栈协议、异常表边、UNPACK argval——无函数名/文件名/字面量白名单，无跨层启发式；
- 无「最后一个 case」类位置特例（merge 归属用前驱闭合 + 支配、前缀归属用语句终结切分、break 判定用跳转目标与区域 blocks 的包含关系 + 父区域类型）；
- 嵌套无感：B16 的支配边界/回边再检测/汇合闭合对任意循环形态与嵌套深度同判（r4_12 三向嵌套全 MATCH）；B15 前缀/merge 归属以语句终结与链级出口显式判据封闭；B18 槽位栈模拟对任意 kwd 数与嵌套深度同判；每处修改 docstring 均含识别条件/归约方式/AST 映射三要素与 [C1]/[C2]/[C3] 条款注记；
- G0 BOM 自检：`region_ast_generator.py` 头 3 字节 `efbbbf` 在位；`region_analyzer.py`/`pattern_parser.py`/`ast_converter.py` 头 3 字节 `222222`（无 BOM——pattern_parser 曾在编辑中误加 BOM，已复原并复验 r4_05/r4_09/r4_14 全 success）；
- 调试探针零残留（源码 diff 无 print/DEBUG/探针标记；临时 dump/probe 脚本已删除）。

---

## §14 未落地项及原因（如实登记）

| 项 | 读数 | 机制（本轮实证） | 未落地原因 |
|---|---|---|---|
| r4_04.match_map_nested / match_map_mixed_seq | 4/6 中余 2 | 嵌套 mapping **值槽位** + 嵌套序列**元素槽位**提取需含 SWAP 的完整栈模拟：编译器把子模式按逆序取值（SWAP 链轮转）、捕获延后绑定（`{"user": {"name": n, "roles": [r, *others]}}` 编译为 UNPACK 2; SWAP×5; MATCH_SEQUENCE; UNPACK_EX; STORE r; STORE others; POP_TOP×4; STORE n），且元素级协议与兄弟协议交错（`[(x1,y1),(x2,y2)]` 的 SWAP 4,2 / 5,3 链）、POP_TOP 同时承担「通配槽消费」与「协议中间项清理」双语义，线性归属无法还原 | 本批已实现标记项栈模拟原型（槽位项/副本/values 元组/opaque 四类标记项 + dis 栈语义演进）并经探针验证 map_nested 形态大体正确，但模拟种子深度 = 窗口起点**绝对栈深**：dis.stack_effect 实测窗口起点真深 ≠ 窗口相对推演深（SWAP 链交换位置随之错位，槽位归属漂移），绝对基深需把 dis 全函数栈深追踪贯通到 pattern_parser（pattern_parser 现无 code object/CFG 通路），改动面大、回归风险高（r4_04 现 4 绿单元全在 mapping 提取路径）。原型已自树移除（不留未接线的死代码）。交后续批次：以「dis.stack_effect 全函数线性追踪 → 按偏移查表提供窗口基深」为前置依赖接入本批已验证的槽位模拟框架 |
| r4_04 之外 | — | — | 其余全部验收单元已落地（见 §12.1） |
