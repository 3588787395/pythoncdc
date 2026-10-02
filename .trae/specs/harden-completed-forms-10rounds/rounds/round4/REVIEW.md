# Round 4 评审（对抗性审查：Match + match_case 8 模式族）

- 评审人：评审工程师（Round 4，对抗攻击者）
- 日期：2026-10-02
- 唯一判据：`scripts/pyc_verify.py`（附件 pylingual `compare_pyc`，逐 code object 单元判 Equal，全 Equal 才 success）；验证方式 = `python -c "import py_compile; py_compile.compile(file='test_repros/round4/X.py', cfile='test_repros/round4/X.pyc', doraise=True)"` → `python pycdc.py -o test_repros/round4/XOK.py test_repros/round4/X.pyc` → `python scripts/pyc_verify.py single test_repros/round4/X.pyc`。
- 首分歧定位工具：`test_repros/round3/_r3_firstdiff.py`（只读判据配套；所引三元组为 `(offset, opname, argval)`，o=原 pyc，d=OK.py 重编译；`<module>` 级 LOAD_CONST code-object 同身份噪声已滤除，仅录函数级分歧）。
- 硬约束遵守：未修改任何 `core/`、`scripts/`、`pycdc.py`、`*OK.py`（既有）、`site-packages/`、`.trae/specs/` 既有内容；每条 shell 命令 ≤300 s；全部 `*OK.py` 由 `pycdc.py` 生成。
- 命名注记：`test_repros/round4/` 内 r4_01..r4_09（boolop_merge/continue 族）为 2026-09 历史战役遗留（commit c33af45b），本轮 Match 攻击复现以 **r4_01_match_* 起的全异名文件** 编号避让（`r4_01_match_value.py` 与历史 `r4_01_boolop_merge_*.py` 无同名冲突），历史产物零改动。
- 管线活性探针：`probe_match_min`（最小 value 单 case / 双 case）= **3/3 success** —— Match 管线活性确认，后续按形态覆盖展开。

---

## §1 任务A — Match 攻击总表（14 文件 + 1 活性探针 + 1 负对照，共 96+3+7 单元：48 success / 58 failure）

统计：**MISMATCH 58 单元 / 13 文件（其中 4 文件为 compile_error=输出语法非法，0 单元可比）**；文件级 3/16 success（r4_02、n4_01、probe）；单元级 48/106 = 45.3%（含探针/负对照）。**wiki 将 Match 形态判为「完备」的声明被对抗证伪**：8 攻击面中 6 面出现 MISMATCH，2 面（value 字面量、singleton）在浅层封闭。

### MISMATCH 清单（首分歧 = (offset, opname, argval) 三元组）

| 文件 | 焦点形态 | 读数（single） | 失败单元签名（首分歧指令三元组） | 破口归类 |
|---|---|---|---|---|
| r4_01_match_value | value 字面量 case；int/str 混排 | 4/6 | `match_value_int_str_mixed` @15：o(40,'COPY',1) vs d(40,'LOAD_CONST','b')（捕获尾 case `other`→`_` 降级，体 `(other,0)`→`(other,)`）；`match_value_expr_body` @0：o(2,'BUILD_LIST',0) vs d(2,'LOAD_FAST','x')（前导 `acc=[]` 吞失+尾 `return acc` 归入 case 1 体） | B14 / B15 |
| r4_02_match_singleton | None/True/False | **5/5 success** | —（封闭面） | — |
| r4_03_match_sequence | [a,b]/(a,b)/嵌套/星号尾 | 2/7 | `match_seq_tuple3` @17：o(42,'NOP',None) vs d(42,'LOAD_CONST',None)；`match_seq_nested` @3：o(8,'POP_JUMP_FORWARD_IF_FALSE',66) vs d(8,…,72)（模式改写 `[[a,b] as c, _]`）；`match_seq_deep_nested` @61：o(174,'NOP') vs d(174,'LOAD_CONST',None)；`match_seq_mixed_literal` @52：o(132,'NOP') vs d(132,'LOAD_CONST',None)；`match_seq_open_ended` @31：o(96,'NOP') vs d(96,'LOAD_CONST',None) —— 共同签名 = 序列形态后的尾 `case _` 整体丢失 | B13（nested 另涉模式腐蚀） |
| r4_04_match_mapping | {"k": v, **rest}；嵌套 mapping | **compile_error 0/6** | 输出含 `case {'points': {'type': 'MatchSequence', 'patterns': [<core.ast_nodes.ASTName object at 0x…>, …], 'as_name': 'y1'}}:` → SyntaxError: invalid syntax；另 `case {'type': rest}:`（**rest 丢失）与 `case {'user': 2}`/`{'user': 1}`（嵌套 mapping 退化为幻影常量） | **B12**（+识别层 rest/嵌套坍缩） |
| r4_05_match_class | Point(x=1, y=2) 类模式 | 5/9 | `match_class_kwargs` @40：o(128,'POP_JUMP_FORWARD_IF_NONE',158) vs d(…,156)（关键字槽位错排 `Point(x=x, y=0)`→`Point(x=0, y=x)`）；`match_class_positional` @58：o(178,'NOP') vs d(178,'LOAD_CONST',None)（尾 `_` 丢）；`match_class_mixed` @49：o(144,'NOP') vs d(144,'LOAD_CONST',None)；`match_class_nested_value` @23：o(78,'POP_JUMP_FORWARD_IF_NONE',164) vs d(…,94)（guard `if abs(x)+abs(y)<=1` 整体丢失） | B18（+B13 尾丢、C3 guard 丢） |
| r4_06_match_or | case 1\|2\|3；or 序列形状 | **compile_error 0/6** | 输出含 `case {'type': 'MatchSequence', 'patterns': [<core.ast_nodes.ASTConstant object at 0x…>, …], 'as_name': None} \| {'type': 'MatchSequence', …}:` → SyntaxError（or 交替=序列形状时爆炸；or 字面量 `1 \| 2 \| 3`、`'yes'\|'y'` 均正常） | **B12**（生产者=MatchOr→ASTBinary 子节点 dict 壳） |
| r4_07_match_capture_wildcard | case x 捕获与 `_` | 3/6 | `match_capture_after_cases` @8：o(22,'COPY',1) vs d(22,'LOAD_CONST',1)（`case other`→`case _`+体 `(other,0)`→`(other,)`）；`match_wildcard_inside` @30：o(74,'NOP') vs d(74,'LOAD_CONST',None)；`match_capture_in_mapping` @24：o(56,'COPY',1) vs d(56,'MATCH_MAPPING',None)（`("notmap",whatever)`→`(whatever,)`） | B14 / B13 |
| r4_08_match_star | [1, *rest] 星号形态 | 2/7 | `match_star_head` @17：o(64,'NOP') vs d(64,'LOAD_CONST',None)；`match_star_double` @17：o(42,'NOP') vs d(42,'LOAD_CONST',None)；`match_star_tuple` @17：o(42,'NOP') vs d(42,'LOAD_CONST',None)；`match_star_literal_head` @59：o(152,'NOP') vs d(152,'LOAD_CONST',None)（=尾 `case _` 丢×4）；`match_star_body_work` @0：o(2,'BUILD_LIST',0) vs d(2,'LOAD_FAST','seq')（前导 `out=[]` 吞失+`return out` 归入 case 体） | B13 / B15 |
| r4_09_match_guard | case x if x>0；guard×or 混排 | **compile_error 0/7** | 输出含 `case {'type': 'MatchAs', 'pattern': <core.ast_nodes.ASTConstant object at 0x…>, 'name': 'v'} \| {…} \| {…}:` → SyntaxError（`case 3 \| 5 \| 7` 被识别为 MatchAs(Constant) 包裹链后再经 B12 爆炸）；另 `case 0`→`case 0 as v` 幻影捕获注入、guard `if v % 2 == 0` 丢失 | **B12**（生产者=识别层 or×guard 判据） |
| r4_10_match_default_tail | 多 case + 默认尾 | 2/6 | `match_default_no_wildcard` @0：o(2,'LOAD_CONST','unset') vs d(2,'LOAD_FAST','x')（`result="unset"` 吞失+case 3 体整丢）；`match_default_tail_with_work` @0：o(2,'BUILD_LIST',0) vs d(2,'LOAD_FAST','x')；`match_default_capture_tail` @20：o(42,'COPY',1) vs d(42,'LOAD_CONST',0)（`("captured",val)`→`(val,)`）；`match_default_nested_tail` @8：o(22,'LOAD_CONST',2) vs d(22,'COPY',1)（尾体 if/elif 装配漂移） | B15 / B14 / B13 |
| r4_11_match_complex_subject | subject=属性链/元组/调用/下标 | 9/10 | `match_subject_call` @0：o(2,'LOAD_GLOBAL','sorted') vs d(2,'LOAD_GLOBAL','_')（subject=函数调用→`match _:` 主体丢失）。正向：属性链/元组/下标/方法链 subject 全 MATCH | B19 |
| r4_12_match_nested_loop | for/while 内 match（case 体 break/continue）、match 嵌 match | **compile_error 0/7** | 输出：`match_in_for_break` 的 for 循环整体消失+`match _:`；`match_in_while_break` 出现幻影 `case 0 \| 1:` 于 `case _:` 之后 → SyntaxError: wildcard makes remaining patterns unreachable；`nested_match_inner` 内层 match 整体消失（`return '1b'`/`return '1?'` 丢失）；`nested_match_seq` 内层 match 退化为 `if 2:` 常量条件；`match_in_for_guard` match 降级为 if/elif 链且捕获名错绑（`v`→未定义 `n`） | **B16** |
| r4_13_match_try | try/except 包 match、match 包 try | 3/7 | `try_wrap_match` @0：o(2,'NOP',None) vs d(2,'LOAD_FAST','x')（29→16 指令，try/except 整体丢弃）；`try_wrap_match_body_raise` @0：o(2,'NOP',None) vs d(2,'LOAD_FAST','x')（43→18）；`match_wrap_try_finally` @0：o(2,'BUILD_LIST',0) vs d(2,'LOAD_FAST','seq')（`log=[]` 吞失）；`try_wrap_match_in_loop` @5：o(12,'FOR_ITER',112) vs d(12,'FOR_ITER',122)（循环内 match→未定义名 `n` 的 if 链）。正向：match 体含 try/except（match_wrap_try）MATCH | B17 / B15 / B16 |
| r4_14_match_case_body | case 体 return/fall-through/if-else 布尔 | 3/7 | `match_case_shared_body` @0：o(2,'LOAD_CONST','none') vs d(2,'LOAD_FAST','x')（match 后继语句整体归入 `case _` 体）；`match_case_ifelse_body` @0：o(2,'LOAD_FAST','x') vs d(2,'LOAD_GLOBAL','n')（match 结构坍缩为未定义名 if 链+幻影 `case -100`）；`match_case_multi_stmt` @1：o(4,'STORE_FAST','acc') vs d(4,'COPY',1)（subject `x`→常量 `0`、`case 1`→`case 1 as acc`、`acc += 1` 与 `if x > 0` 分支丢失）；`match_case_bool_guard` @0：o(2,'LOAD_FAST','x') vs d(2,'LOAD_GLOBAL','a')（match→未定义名 `a` 的 if/else 链） | B15 / B16（C3） |
| **n4_01_no_match_control（负对照）** | 等价 if/elif 链 + 简单 for/while + 简单 try | **7/7 success** | —（判据有效性成立，无误报基线） | — |

（活性探针 probe_match_min = 3/3；Task B 的 r4_or4_and2 = 1/2，见 §4。）

---

## §2 机制分析（锚点均 2026-10-02 实际 grep/read 核对；新破口 B12–B19 续接登记）

理论权威：`wiki/concepts/decompile-invariant-completeness.md` §1（C1 局部消费 / C2 黑箱组合 / C3 守卫封闭）。Match 管线锚点实测：`RegionType.MATCH` `region_analyzer.py:182`；`MATCH_SUBJECT/MATCH_CASE/MATCH_GUARD_ROLE` `:149-151`；`_identify_match_regions` 调用点 `:1465`（定义 `:13058`）；生成层 `_generate_match` `region_ast_generator.py:31224`；模式构造 `_mr_collect_case_body` `region_analyzer.py:13675`、`_mr_finalize_match_region` `:13551`；发射层 `_generate_match_pattern` `code_generator.py:3240`；模式解析 `pattern_parser.py:47`（`parse_case_pattern`）/`:1097`（`_extract_sequence_pattern`）/`:1599`（`_extract_or_or_literal_pattern`）。

### B12 — Match 模式发射层混合树 `str()` 回退灾难（**新登记，未修，本轮最高优先级**）

- **破坏条款**：C2（黑箱组合失败 → 输出语法非法，0 单元可比）
- **现象**：4 文件（r4_04/r4_06/r4_09/r4_12）反编译产物无法通过 `py_compile`，pyc_verify 判 `compile_error units=0/0`。发射文本内嵌内部对象 repr（含每次运行变化的内存地址 `<core.ast_nodes.ASTName object at 0x…>`），为非确定性垃圾。
- **机制（发射层汇点，已定位）**：`code_generator.py:3240` `_generate_match_pattern` 末行回退 `return str(pattern)`（**`code_generator.py:3374`**）。凡传入的模式不是「可识别 type 的 dict」也不是「带可用 to_code 的 ASTNode」，即整 dict `str()` 外泄。
- **生产者（中层转换，已定位）**：`ast_converter.py:1701-1710` MatchMapping 分支 **`return ASTDict(keys=keys, values=values)`** —— 把 mapping 模式转为 ASTDict 节点，其 value 侧是 `_convert_match_pattern` 产出的「纯 dict 壳（`{'type':'MatchSequence', 'patterns':[ASTNode…]}`）」；dict 壳无 `to_code`，ASTDict 渲染时 `str(dict)` 外泄 → r4_04 爆点。`ast_converter.py:1747-1761` MatchOr 分支 **`result = ASTBinary(left=…, right=…, op=BIN_OR)`** —— or 交替若是序列形状，转换产物为纯 dict 壳，ASTBinary 渲染对 dict 子节点 `str()` 外泄 → r4_06 爆点（or 交替为纯字面量时子节点为 ASTConstant、可正常渲染，故 `1|2|3` 封闭）。`ast_converter.py:1731-1736` MatchAs 分支 `return {'type':'MatchAs','pattern':value_pattern,'name':name}` 中 `value_pattern` 可为裸 ASTConstant → r4_09 爆点。
- **识别层伴随伤（伴生，需 B12 修复后复归因）**：r4_09 `case 3 | 5 | 7`（前邻 guard case）被解析为 MatchAs(Constant) 包裹链（`pattern_parser.py:1599` `_extract_or_or_literal_pattern` 的 COPY/STORE 归属判据在 guard 混排下漂移）；r4_04 `{"type": t, **rest}` → `case {'type': rest}`（rest 捕获丢失）、`{"user": {"name": n, …}}` → `case {'user': 2}` 幻影常量（`_extract_mapping_pattern` `pattern_parser.py:1700` 嵌套坍缩）。
- **复现组（验收组）**：r4_04 全体 6 单元、r4_06 全体 6 单元、r4_09 全体 7 单元。
- **状态**：已定位（汇点 `code_generator.py:3374` + 生产者 `ast_converter.py:1710/:1761/:1736` 实测确认）。

### B13 — 序列/星号/类模式链尾通配 `case _` 整体丢失（**新登记，未修**）

- **破坏条款**：C1（尾 case 体局部消费丢失）+ C2（case 链收尾归属错）
- **机制（已定位至路径，精确分支待查）**：字面量链后的尾 `case _`（如 r4_01/match_value_single）正常发射；**序列/星号/类模式链后的尾 `case _` 整体丢失**（pattern 与 body 双丢，函数尾部退化为隐式 return）。字节码形态：尾 `case _` 块仅含 `POP_TOP`+`NOP`（原 pyc r4_03.match_seq_list2 @38-40 实测），`_mr_collect_case_body` 尾部行走把该块按「连接块」消费——`region_analyzer.py:13841-13850` `is_connector = (… all(i.opname in ('POP_TOP','JUMP_FORWARD','JUMP_ABSOLUTE') …) …)` → `visited.add(current); current = next(iter(current.successors))`，该 case 永不进入 `case_blocks/case_patterns`；其 body 块（如 `LOAD_CONST None; RETURN_VALUE`）被 all_blocks 占有却不发射。为何字面量链同形不触发（r4_01 尾 `_` 保留）——精确判据分歧点待查（状态：已定位待查）。
- **判据盲区伴生发现（R4-O1 观察点）**：当尾 `case _` 体恰为 `return None` 时（r4_03.match_seq_list2），丢 case 后重编译仅在尾部 RETURN_VALUE/RETURN_CONST/NOP 上有差异，**pyc_verify 判 Equal** —— 即判据对「尾 return 常量差」有归一化，语义破缺（非匹配输入抛 NoMatchError vs 返回 None）不被判据捕获；`case _` 体非平凡时（`return ()`/字符串）才判 MISMATCH。
- **复现组**：r4_03 ×5、r4_05 ×2（positional/mixed 的尾丢）、r4_07.match_wildcard_inside、r4_08 ×4。
- **状态**：已定位（锚点 `region_analyzer.py:13841-13850`），精确分支待查。

### B14 — 捕获尾 case 捕获名丢失 + case 体首元素腐蚀（**新登记，未修**）

- **破坏条款**：C1（局部消费），伴生 C2
- **签名（4 实例，首分歧一致为 COPY 1 位丢失）**：`case other: return (other, 0)` → `case _: return (other,)`；`case val: return ("captured", val)` → `case _: return (val,)`。捕获名降为通配（捕获名 STORE 未被 `_extract_or_or_literal_pattern` `pattern_parser.py:1599` 的 STORE_OPS 分支归属为 as_name），且 case 体元组丢一个元素（r4_01 丢 `0`、r4_07.match_capture_in_mapping 丢 `"notmap"`——体首指令被模式头吞食）。首分歧：r4_01 @15 o(40,'COPY',1) vs d(40,'LOAD_CONST','b')；r4_07 @8 o(22,'COPY',1) vs d(22,'LOAD_CONST',1)、@24 o(56,'COPY',1) vs d(56,'MATCH_MAPPING',None)；r4_10 @20 o(42,'COPY',1) vs d(42,'LOAD_CONST',0)。
- **正向**：裸捕获单 case `match x: case val: return (…)` → `val = x; return (…)` 为字节等价降级（r4_07.match_capture_bare、r4_13.match_case_try_loop 均 MATCH）——降级本身合法，**捕获名在多 case 上下文丢失 + 体腐蚀**才是破口。
- **复现组**：r4_01.match_value_int_str_mixed、r4_07.match_capture_after_cases / match_capture_in_mapping、r4_10.match_default_capture_tail = 4 单元。
- **状态**：已定位（签名+归因方向），精确分支待查。

### B15 — match 前导初始化语句吞失 + 尾部 return 归入 case 体（**新登记，未修**）

- **破坏条款**：C2（归约错归属——match 区域把前导顺序语句与后继语句吞入 case 体）
- **签名（6 实例，首分歧一致 @0：o 开头为前导语句指令，d 开头为 LOAD_FAST subject）**：`acc = []`/`log = []`/`result = "unset"`/`out = []` 等前导赋值消失；match 之后的 `return acc/log/result` 被物化进首个/默认 case 体末尾。实例：r4_01.match_value_expr_body（41→41 指令重排）、r4_08.match_star_body_work、r4_10.match_default_no_wildcard（26→19，case 3 体整丢）、r4_10.match_default_tail_with_work、r4_13.match_wrap_try_finally、r4_14.match_case_shared_body（`result="none"` 吞失 + match 后 if/else 整体归入 `case _` 体）。
- **归因方向**：`_generate_match`（`region_ast_generator.py:31224`）case 体收集对 merge_block/前驱块的所有权判据（`_mr_compute_case_merge` `region_analyzer.py:13616` post-dominator 出口计算把前导/后继块卷入 case body 集合）；精确分支待查。
- **复现组**：6 单元（上列）。
- **状态**：已定位（签名），机制待查。

### B16 — 循环 × match 装配灾难（**新登记，未修**）

- **破坏条款**：C1+C2（区域认领冲突），C3（case 体 break/continue 守卫丢失）
- **签名**（r4_12 全军覆没 0/7 + r4_13.try_wrap_match_in_loop + r4_14 两单元）：
  - for 循环整体消失（`match_in_for_break` 输出以 `match _:` 开头，subject/循环双丢，`return total` 丢失）；
  - 幻影 case 追加（`match_in_while_break` 输出 `case 0: case 1: case _: case 0 | 1:` → 语法非法）；
  - 嵌套 match 整体消失（`nested_match_inner` 内层 match 被剥壳，`return '1b'`/`return '1?'` 丢失）；
  - 嵌套 match 退化为常量条件 `if 2:`（`nested_match_seq`）；
  - match 降级为 if/elif 链且捕获名错绑为**未定义名**（`match_in_for_guard` 的 `v`→`n`、r4_13.try_wrap_match_in_loop 的 `item` 捕获→`n`、r4_14.match_case_ifelse_body 的 subject `x`→未定义 `n`、r4_14.match_case_bool_guard →未定义 `a`）；
  - 幻影捕获注入（`case 1` → `case 1 as acc`，r4_14.match_case_multi_stmt，同时 subject→常量 `0`、case 体部分丢失）。
- **归因方向**：LOOP 识别（Phase 1 `region_analyzer.py:1463`）先于 MATCH（`:1465`）认领，循环体块被 LoopRegion 占有后 `_identify_nested_match_regions`（`:14192` 注释自承嵌套 match 只能二次扫描）重扫失败；case 体 break/continue 与循环回边的 Terminator 归属争抢。精确判据待查。
- **复现组**：r4_12 ×7、r4_13.try_wrap_match_in_loop、r4_14.match_case_ifelse_body / match_case_multi_stmt / match_case_bool_guard = 10 单元。
- **状态**：已定位（签名），机制待查。

### B17 — try/except 包 match：try 壳整体丢弃（**新登记，未修**）

- **破坏条款**：C2（结构组合）
- **签名**：`try: match x: … except TypeError: return 'bad-type'` → try/except 壳完全消失（try_wrap_match 29→16 指令；try_wrap_match_body_raise 43→18，`except ValueError as e` 分支丢失）。首分歧 @0：o(2,'NOP',None) vs d(2,'LOAD_FAST','x')（原 try 体以 NOP 前导）。正向：match 体**内**含 try/except（match_wrap_try）与 try/finally 体外层（match_wrap_try 的 finally 变体除 B15 外结构保留）MATCH —— 单向破口（外层 try→match）。
- **复现组**：r4_13.try_wrap_match、try_wrap_match_body_raise = 2 单元。
- **状态**：已定位（签名），机制待查。

### B18 — 类模式关键字/位置槽位错排 + guard 丢失（**新登记，未修**）

- **破坏条款**：C1，guard 丢失涉 C3
- **签名**：`case Point(x=x, y=0): return ('x', x)` → `case Point(x=0, y=x): return ('x', x)`（关键字槽字面量/捕获错排，`_extract_class_pattern` `pattern_parser.py:1457` 槽位归属漂移；首分歧 r4_05.match_class_kwargs @40 o(128,'POP_JUMP_FORWARD_IF_NONE',158) vs d(…,156)）；`case Point(x=x, y=y) if abs(x)+abs(y) <= 1` → guard 整体丢失（match_class_nested_value @23 o(78,…,164) vs d(…,94)，跳转目标漂移 70 字节）。位置模式 `Color(0,0,0)`/`Color(r,g,b)` 本身发射正确（尾 `_` 丢归 B13）。
- **复现组**：r4_05.match_class_kwargs、match_class_nested_value = 2 单元。
- **状态**：已定位（签名），机制待查。

### B19 — match subject 为函数调用表达式时主体丢失（**新登记，未修**）

- **破坏条款**：C1
- **签名**：`match sorted(x):` → `match _:`（subject 发射为 `_`）。首分歧 r4_11.match_subject_call @0：o(2,'LOAD_GLOBAL','sorted') vs d(2,'LOAD_GLOBAL','_')。正向：属性链 `obj.inner().mode`、元组 `(a+1, b*2, c-3)`、下标 `d["key"]`、方法链 `obj.inner().inner().level` subject 全 MATCH（9/10）——仅「裸函数调用」形态中招；subject 块生成 `_generate_match` subject 分支（`region_ast_generator.py:31254-31360`）对 CALL 结尾块的提取判据待查。
- **复现组**：r4_11.match_subject_call = 1 单元。
- **状态**：已定位（签名），机制待查。

### 封闭面正向记录（对抗未破）

- **value 字面量浅层**（probe 3/3 + r4_01 3 单元）、**singleton 全形态**（r4_02 5/5：None/True/False 混排、值/单例混排）、**裸捕获降级**（字节等价）、**or 字面量**（`1|2|3`、`'yes'|'y'|'ok'`、int×str 混型）、**非调用型复杂 subject**、**match 体内 try/except**、**元组 subject + [0,0] 序列**（r4_01.match_value_subject_tuple，tuple→list 模式改写为 MATCH_SEQUENCE 字节等价）——`_identify_match_regions` docstring 宣称的 198/198 矩阵在上述浅层子面成立；**「Match 形态完备」的 wiki 声明按本轮证据应降格为「value/singleton/or-字面量浅层封闭」**（与 Round3 对 B6/B7 的降格同构：深层与组合面即破）。

---

## §3 负对照结果

| 负对照 | 形态 | 读数 | 判定 |
|---|---|---|---|
| n4_01_no_match_control | 无 match 的等价 if/elif 链 ×3 + 简单 for/while（break/continue）+ 简单 try | **7/7 success** | 判据无误报；r4 组 MISMATCH 非误归因，且同形 if/elif 改写（r4_14 崩塌产物即 if 链）在真 if/elif 源上 MATCH，证明 B16 的「match→if 链降级」是装配错误而非 if 链本身不可表达 |

---

## §4 Round 3 残留复验读数

| 登记项 | 探针 | 登记读数 | 本轮读数 | 判定 |
|---|---|---|---|---|
| B10-R | `test_repros/round3/r3_34_b10r_innerforelse_break.pyc`（归档 OK.py 直接 single） | 1/2 MISMATCH（已定位待下轮） | **1/2（failure）**：`outer_break_rise` Different control flow；首分歧 @6 o(36,'FOR_ITER',158) vs d(36,'FOR_ITER',162) | **持平，未变差未变好**（维持「已定位待下轮」） |
| B11-R2 | 新构 `test_repros/round4/r4_or4_and2.pyc`（`while (a or b or c or d) and k < m and b:`） | Round3 登记 MISMATCH（未定位） | **1/2（failure）**：`or4_and2` Different control flow；首分歧 @9 o(20,'POP_JUMP_FORWARD_IF_FALSE',90) vs d(20,…,74)。产物 `if a or b or c or d: while k < m and b:` —— **or 组被提升出循环条件成为入口 if（语义改变：or 组只判一次）** | 维持 MISMATCH；**本轮新增定位**：装配层把 or 前缀提升为循环外包裹 if（B11 家族 or4_and2 形态的机制签名，状态 未定位→已定位） |

---

## §5 基线哨兵读数表

| 哨兵 | 登记基线 | 本轮读数（single，现树） | 判定 |
|---|---|---|---|
| site-packages/fly/data/quotation.pyc | 152/153 | **152/153** | 持平 |
| site-packages/IQCommon/strategy/jq_trans_module.pyc | 65/65 | **65/65** | 持平 |
| site-packages/fly/data/quote.pyc | 84/92 | **84/92** | 持平 |
| site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | 118/128 | **118/128** | 持平 |
| site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 29/29 | **41/43（95.35%）** | **非回退**：round3 FIX.md §5.5/FIX2.md 已注记「验证器单元口径（29 units）与历史记录（41/43）不同源」，41/43 = 历史记录值，零新增失败；round3 FIX.md 建议的「下轮以同一验证器版本固化基线读数」本轮执行——**建议以 41/43 固化为该哨兵的现行登记值** |

五支哨兵零新增回退。

---

## §6 修复工程师交接单（按优先级排序）

| 优先级 | 破口 | 机制一句话 | 最小验收组（转 MATCH 判据 = pyc_verify single success） | 回归哨兵清单 |
|---|---|---|---|---|
| P0 | **B12** | 发射层 `_generate_match_pattern` 回退 `str(pattern)`（`code_generator.py:3374`）+ 中层 `ast_converter.py:1710`（MatchMapping→ASTDict 混合树）/:1761（MatchOr→ASTBinary 子节点 dict 壳）/:1736（MatchAs 裸 ASTNode）产出不可渲染混合树 | r4_04（0→6/6）、r4_06（0→6/6）、r4_09（0→7/7）——三文件至少 compile 通过且单元数不倒退 | 现有 match 全绿面：probe_match_min 3/3、r4_02 5/5、r4_01 4/6 不变差、quotation 152/153 |
| P1 | **B16** | 循环体块被 LoopRegion 先占 + `_identify_nested_match_regions` 二次扫描失败 → 循环消失/幻影 case/`if 2:`/未定义名 if 链 | r4_12（0→7/7）、r4_13.try_wrap_match_in_loop、r4_14.match_case_bool_guard | r3_27.loop_try_with_match 9/9、r3_32 11/11、r4_13 3/7 不变差 |
| P2 | **B13** | 尾通配 `case _`（POP_TOP+NOP 桩块）被 `region_analyzer.py:13841-13850` 连接块判据吞食，case 整体不登记 | r4_03（2→7/7）、r4_08（2→7/7） | r4_01/r4_02 value 链尾 `_` 保持 MATCH；r4_05 尾丢单元 |
| P3 | **B15** | match 前导初始化吞失 + 尾 `return` 物化进 case 体（`_mr_compute_case_merge` 出口归属） | r4_10（2→6/6）、r4_01.match_value_expr_body、r4_14.match_case_shared_body | r4_08.match_star_body_work、r4_13.match_wrap_try_finally |
| P4 | **B14** | 捕获尾 case 捕获名丢失（`pattern_parser.py:1599` STORE 归属）+ case 体首元素被模式头吞食 | r4_01.match_value_int_str_mixed、r4_07.match_capture_after_cases / match_capture_in_mapping、r4_10.match_default_capture_tail | r4_07.match_capture_bare（字节等价降级面不得变差） |
| P5 | **B17** | 外层 try/except 包 match 时 try 壳整体丢弃 | r4_13.try_wrap_match、try_wrap_match_body_raise | match_wrap_try（match 内 try 面）保持 MATCH |
| P6 | **B18** | 类模式关键字槽位错排（`pattern_parser.py:1457`）+ 类模式 guard 丢失 | r4_05.match_class_kwargs、match_class_nested_value | r4_05.match_class_positional（位置模式发射正确面） |
| P7 | **B19** | subject 为裸函数调用时主体丢失（`region_ast_generator.py:31254-31360` subject 提取） | r4_11.match_subject_call | r4_11 其余 9 单元（属性链/元组/下标 subject） |
| P7 | **B10-R**（Round3 残留） | for-else×break 内外层归属（Round3 已定位待修） | r3_34 1/2 → 2/2 | 本轮读数已登记 |
| P7 | **B11-R2**（Round3 残留，本轮已定位签名） | or 前缀被提升出 while 条件成为包裹 if | r4_or4_and2 1/2 → 2/2 | r3_33 4/4（FIX-B11c-3 已封闭面）不得回退 |

**修复边界提醒（算法合规）**：所有修复限于区域归约算法同层结构事实判据（识别/归约/生成/发射），禁止白名单式按函数名/文件名打补丁；docstring 三要素 + C1/C2/C3 条款同步；判据形态必须「嵌套无感」（B16 修复须同时覆盖 for/while×match、match×match、try×match 三向嵌套，不得只堵 r4_12 单形）。
