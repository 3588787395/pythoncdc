# Round 3 — fly/data/quote.pyc 18 个不匹配函数根因分析与复现

日期：2026-09-19
目标文件：`site-packages/fly/data/quote.pyc`（81 函数，63 匹配 / 18 不匹配，77.78%）
分析工具（同 Round 2 方法论）：
- `python _r2_dis.py <pyc> <func> [offset]` — 反汇编
- `python _r2_adiff.py <pyc> <OK.py> <func>` — difflib 对齐原始指令序列 diff（`raw_ratio=1.000` 即纯比较器问题；本轮 **18 个全部 raw_ratio<1.0，均为反编译器真实缺陷**，无新增比较器误报）
- `python _r2_run_repro.py <repro.py> [func]` — 复现流水线
- 对齐 diff 全文存于 `_r3_tmp/adiff/<func>.txt`；`pyc_batch_verify.py single` 只打印前 10 个 mismatch，全量清单用 `_r3_tmp/_r3_mismatch_list.py`（复用其 `bytecode_diff` API，未修改脚本）

**关键结论**：18 个函数共享 9 类根因（R3-A…R3-I/K）。最大的共性是两类：
① **旋转 while 循环体重建时语句丢失/塌缩**（3 个函数，含 `while not redata and count < 3` 重试循环，丢指令最多）；② **try/except 区域块归属错乱**（3 个函数，其中 run_individual_transform 灾难级）。另有 2 个函数丢 continue 导致语义覆盖、2 个函数三元赋值降级为裸表达式、以及多个布局级问题。

---

## 1. 根因分类汇总表（18 个函数）

| # | 函数 | orig→decomp (过滤后) | raw_ratio | 根因（一句话） | 算法阶段 | 严重度 |
|---|---|---|---|---|---|---|
| 1 | build_current_period_df | 117→108 | 0.889 | 尾部 `tempdict['is_open'] = [1 if c else 0]`（下标赋值+列表包裹三元）被降级为裸表达式 `[1 if c else 0]`（STORE_SUBSCR 丢），后续 `tmp = pandas.DataFrame(...)` 与 `return tmp` 整体丢失，函数变隐式 return None | 区域归约/AST生成（伪三元合并 + 语句跨度丢失） | 语义错误 |
| 2 | check_frequency | 122→123 | 0.963 | try 体以全终结（raise/assert）if/elif/else 链结尾：orig 在 RAISE_VARARGS 与 PUSH_EXC_INFO 之间有不可达 `LOAD_CONST None; RETURN_VALUE`（O99-100）；decomp 改为 JUMP_FORWARD 且函数尾复制出双份 return None | 代码生成（隐式 return 块布局） | 等价（布局） |
| 3 | check_limit | 330→315 | 0.859 | (a) `while not redata and count < 3:` 重试循环塌缩为 `if redata or count < 3: pass`（and→or 反演 + 整个循环体丢失，r3_03 同签名）；(b) `self.log.quote.info(f'...{tmp_universe[None:10]!s}等{len(tmp_universe)}只代码')` f-string 日志语句整体丢失（21 条指令） | 区域归约（旋转 while 体丢失）+ AST生成（f-string） | 语义丢失 |
| 4 | check_stock | 87→88 | 0.914 | 与前一 if 同条件的 `assert 11 >= len(s) >= 9, msg` 被吸收为 if 的 else 分支：decomp 在 error 块后多出 `JUMP_FORWARD to 346` 直达 assert 通过点，链式比较重复求值，if+fallthrough 结构变成 if/else | 区域归约（链出口归属） | 等价（布局） |
| 5 | fill_minute_or_day_blank | 220→227 | 0.962 | 三条 POP_JUMP_FORWARD_IF_FALSE（O3/O53/O131）全部汇聚到函数尾 `return klines`；decomp 把该 return 归属为内层 else（`else: return klines`），顶层 return 丢失——back 分支、外层条件为假等路径全部落到隐式 return None | 区域归约（汇聚出口 return 归属） | 语义错误 |
| 6 | filter_stock_by_status | 202→205 | 0.963 | (a) `if not A.get(s) and not B.get(s) and not C.get(s) and not D.get(s): append` 的 and 链（not 操作数）被重写为嵌套 if + 3 条显式 continue：orig 每检查 1 条条件跳转（PJF_TRUE→循环底 1076），decomp 变 2 条（PJF_FALSE→next + JUMP_BACKWARD）；(b) try 体 `return result` 后多出不可达 `return None` | 区域归约（boolop 链重建失败，P1-1 残余形态） | 等价（布局） |
| 7 | get_individual_data | 313→306 | 0.856 | (a) `data_count = int(data_count) if 0 < int(data_count) <= 200 else 200` 被降级为两个裸表达式语句 `int(data_count)` / `200`（赋值丢失，first_diff idx20 JUMP_FORWARD(98) vs POP_TOP）；(b) 块尾 `returnPa = pandas.Panel(data); return returnPa` 被替换为 `return None`（Panel 构造丢失）；(c) flag==1/-1 检查块（2 条 log + return None）从 `if redata:` 的 else 位移到函数尾（except 清理块之后） | 区域归约/AST生成（三元赋值降级 + 块位移） | 语义错误 |
| 8 | get_merger_data | 65→64 | 0.915 | `if newSecuCode and newSecuCode in list(...): { if not return_data.empty: append else: assign }` 被折叠为 `if not (A and B and empty): append` + `assign` 无条件执行——外层条件被吸收进 not(...) 且 else 体提升为顺序语句（永远覆盖 append 结果），O48 的 JUMP_FORWARD to 356 消失 | 区域归约（嵌套 if 折叠 + else 体提升，R2 #7 kill_trade_process 家族残余） | 语义错误 |
| 9 | get_price | 229→187 | 0.764 | 函数首条 `self.log.quote.debug(f'调用函数get_price，参数为：stocks={security[None:10]!s}等{len(security) if isinstance(security, list) else 1}只代码,...')`：f-string 模板错乱（LOAD_FAST/LOAD_CONST 被当文字拼进模板 → `stocks=securityNone{10!s}`，BUILD_SLICE/BINARY_SUBSCR 丢失）+ 调用接收者 self.log.quote.debug + CALL + POP_TOP 丢失 | AST生成（f-string 模板重建 + 调用接收者） | 语义丢失（日志） |
| 10 | get_real_from_zeromq | 702→670 | 0.875 | 同 #3 双根因：`while not redata and count < 3:` 重试循环 + `f'在线获取real数据，参数为{params[None:10]!s}等{len(params) - 1}只代码'` 日志语句整体丢失（O32-52，22 条指令） | 同 #3 | 语义丢失 |
| 11 | initImagedata | 244→227 | 0.866 | 同 #3 双根因：重试循环 + `f'初始化imagedata,在线获取snapshot数据,包括{universe[None:10]!s}等{len(universe)}只代码'` 整体丢失（O34-52，19 条指令） | 同 #3 | 语义丢失 |
| 12 | is_ST_stock_real | 82→82 | 0.988 | for 循环内 if/elif 链首分支 `if 'ST' in name or 'PT' in name: result[i] = True; continue` 的 continue（JUMP_BACKWARD to 92，O35）被丢弃，decomp 改为 JUMP_FORWARD to 192（链尾）→ `result[i] = False` 覆盖 True（唯一 true diff） | 区域归约→AST生成（分支终结边误判为链出口） | 语义错误 |
| 13 | is_delisting_stock_real | 106→105 | 0.976 | 同 #12：`if stock_status == 'DELISTED': result[i] = True; continue`（JUMP_BACKWARD to 278，O98）被丢弃 → 落入 `result[i] = False` | 同 #12 | 语义错误 |
| 14 | load_bars_from_hundsun | 476→445 | 0.877 | 首条 f-string 日志语句（同 #9 形态，模板错乱 + 接收者丢失）**并吞掉其后语句**：`data = collections.OrderedDict()`（O35-38）与 `retpanel = pandas.Panel()`（O39-42）两条赋值整体丢失（后续引用未定义变量，NameError），`if os.path.exists(...) and typet == 6:` 的 and 首操作数也丢失 | AST生成（f-string + 相邻语句吞并） | 语义错误（灾难） |
| 15 | load_get_price | 170→135 | 0.761 | 同 #9（f-string 模板错乱 + 接收者丢失） | 同 #9 | 语义丢失 |
| 16 | one_prod_to_dataframe | 484→483 | 0.949 | 内层循环 `elif len(v)==14: ... if int(...) >= 16 or int(...) < 9: break` / `else: break`：orig 的 break 路径直达循环底汇聚块（1702: POP_TOP; JUMP→1972），decomp 产生额外中转块（JUMP→1820; 1820: POP_TOP; JUMP→1970）且 or 短路块与 else-break 块合并方式不同，15 处 jump 目标级联偏移 | 区域归约（break/continue 汇聚块布局） | 等价（布局） |
| 17 | run_individual_transform | 363→320 | 0.846 | while 内 try/except 区域块归属错乱（灾难级）：try 体被替换为 `pass` + 单条 JUMP_FORWARD；except BaseException 体吞入了原 try 体的大块业务语句（stocks=…、real_data 分发、continue、isSet 检查、socket.close…），业务语句出现在 except 体内 continue 之后（不可达位置）；try 体业务块被复制两份且第二份引用未定义变量 | 区域归约（try/except 块归属 + 语句吞并位移） | 语义错误（灾难） |
| 18 | run_tick_socket | 308→308 | 0.597 | 内层 try/except 的正常出口块被伪造为 try/except/else 的 else 子句（decomp D18 起直接内联 else 体：warning/updateflag=-1/stocks/real_data 分发），外层 `if message:` 的 else 体（return None）错位，elif 链（`elif message[stocks][-1]==1 and ...`）挂接层级改变 | 区域归约（try/except/else 伪造 + if/else 体错位） | 语义错误 |

严重度统计：语义错误/丢失 11 个（#1,3,5,7,8,9,10,11,12,13,14,17,18 中 13 个，其中 #17/#14 灾难级），纯布局/等价 5 个（#2,4,6,16）。无比较器误报。

---

## 2. 共性根因分类（算法级）

| 编号 | 名称 | 影响函数 | 一句话描述 |
|---|---|---|---|
| R3-A | f-string 调用参数区域重建失败 | #9 #14 #15（模板错乱）、#3 #10 #11（整语句丢失） | `recv(f'...{x[None:10]!s}...')` 形态的日志调用：模板按指令逐条拼接而非栈模拟 → 文字垃圾化、切片/调用操作数丢失、接收者链丢失，甚至吞并相邻语句 |
| R3-B | 不可达隐式 return None 位移/复制 | #2、#6(b) | try 体全终结链尾的隐式 return 被搬到函数尾并复制 |
| R3-C | assert 被吸收为前一 if 的 else | #4 | 同条件 assert 与 if 合并成 if/else，链式比较重复求值 |
| R3-D | 循环内 if/elif 首分支 continue 丢失 | #12 #13 | 分支终结边（目标=循环回边）误判为链出口 → 链尾语句覆盖分支结果 |
| R3-E | 汇聚 return 块归属错误 | #5 | 多分支汇聚的函数尾 return 被归属给单个内层 else 并制造提前 return |
| R3-F | 三元赋值降级 + 尾语句丢失 | #1 #7(a)(b) | `x = a if c else b`（含 `[1 if c else 0]` 列表包裹形态）降级为裸表达式，后续语句被吞 |
| R3-G | break/continue 汇聚块布局重排 | #16 #6(a) | 循环内 break/continue 经额外中转块，条件跳转方向取反 |
| R3-H | and 链（not 操作数）→ 嵌套 if + continue | #6(a) | boolop 链重建失败退化为结构化嵌套（P1-1 残余） |
| R3-I | try/except 区域块归属错乱 | #17 #18 #7(c) | try 体↔except 体语句互换/吞并、伪造 else 子句、业务块位移到函数尾 |
| R3-K | 嵌套 if 条件吸收 + else 体提升 | #8 | `if A: if B: X else: Y` → `if not (A and B): X; Y`（语义反转） |
| R3-L | 旋转 while 体语句丢失/塌缩 | #3 #10 #11（r3_03/r3_03d 复现） | `while not X and Y:` 体中 if/elif 链前后的普通语句丢失，甚至整个循环塌缩为 if + or 反演 |

注：R3-J（#14 的赋值吞并）并入 R3-A 记录；R3-M（r3_03d 的 sleep 丢失）并入 R3-L 记录。

---

## 3. 复现实例（test_repros/round3/）

验证：`python _r2_run_repro.py <repro.py>`（py_compile → pycdc --region → 重编译 → compare_bytecode）。
**13 个复现成功（MISMATCH REPRODUCED），3 个探针未复现（负对照，记录触发边界）**。每个 ≤60 行、独立编译。

| 文件 | 根因 | 对照函数 | 验证结果（关键签名） |
|---|---|---|---|
| r3_01_fstring_log_mangled.py | R3-A | get_price | **复现**：orig=83 decomp=54，dec 输出 `if self.log.quote.debug(len(security) if isinstance(security, list) else 1):`（模板丢、调用变 if 条件） |
| r3_01b_fstring_log_mangled_cls.py | R3-A | get_price/load_bars（类上下文） | **复现**：orig=84 decomp=30；dec 丢失中间 isinstance 块（data 未定义） |
| r3_02_fstring_log_dropped.py | R3-L+R3-A | check_limit | **复现**：orig=130 decomp=88；while 塌缩 + `{x[None:10]!s}` 渲染为 `{x[:10]!s}`（None 起始丢） |
| r3_02b_fstring_conv_probe.py | R3-A 触发边界探针 | — | **未复现（负对照）**：带/不带 `!s` 的 f-string 在孤立上下文均正确——证明 `!s` 转换标志不是触发条件 |
| r3_03_while_retry_loop.py | R3-L | check_limit / initImagedata / get_real_from_zeromq | **复现**：orig=90 decomp=47；`while not redata and count < 3:` + 体 → `if redata or count < 3: pass`（整循环体丢失） |
| r3_03b_while_cond_probe.py | R3-L 触发边界探针 | — | **复现（p_isnone）**：`while redata is None and count < 3:` 条件跳转 NONE/NOT_NONE 反演（P1-2 残余形态）；p_not/p_eq 匹配 |
| r3_03c_while_body_probe.py | R3-L 触发边界探针 | — | **未复现（负对照）**：体含元组解包或 if/elif 单独存在时不塌缩 |
| r3_03d_while_sleep_probe.py | R3-L/M | 重试循环（time.sleep 位于 if/elif 之后） | **复现（p_sleep_mid）**：orig=54 decomp=49，`self.sleep(3)`（位于 if/elif 链与尾部元组解包之间）被丢弃；p_sleep_first 匹配 |
| r3_04_loop_branch_continue_lost.py | R3-D | is_ST_stock_real / is_delisting_stock_real | **复现（is_st）**：idx36 JUMP_BACKWARD(90) vs JUMP_FORWARD(190)——与目标 first_diff（idx35 JUMP_BACKWARD(92) vs JUMP_FORWARD(192)）同型；true_diffs=1 同目标 |
| r3_05_converge_return_misattrib.py | R3-E | fill_minute_or_day_blank | **复现**：orig=210 decomp=212（目标 220→222 同型）；dec 确认 `else: return klines` + 顶层 return 丢失 |
| r3_06_pseudo_ternary_subscript.py | R3-F | build_current_period_df | **复现（与目标完全同数值）**：orig=115 decomp=108 true=12 jump=5 raw=0.889，first_diff idx103 LOAD_FAST(tempdict) vs POP_TOP；dec 尾部为裸 `[1 if ... else 0]` |
| r3_07_ternary_assign_degraded.py | R3-F | get_individual_data | **复现**：orig=152 decomp=151；dec 确认 `int(data_count)` / `200` 裸表达式（同目标形状） |
| r3_08_and_chain_nested_continue.py | R3-H | filter_stock_by_status | **复现（同目标数值）**：true_diffs=41（目标 41）；first_diff POP_JUMP_FORWARD_IF_TRUE vs POP_JUMP_FORWARD_IF_FALSE（目标 idx165 同型）；需 4 操作数完整形态（3 操作数不触发） |
| r3_09_nested_if_else_flatten.py | R3-K | get_merger_data | **复现（与目标完全同数值）**：orig=66 decomp=65 true=16 jump=3 raw=0.915 |
| r3_10_try_except_block_scramble.py | R3-I | run_tick_socket | **复现**：raw=0.593（目标 0.597）；dec 确认伪造 try/except/**else** 子句 + `if message:` 的 else 体错位 |
| r3_11_implicit_return_shift.py | R3-B | check_frequency | **复现**：orig=84 decomp=83 true=64；try 体全终结链 + 不可达 return None 位移 |
| r3_12_assert_absorbed_as_else.py | R3-C | check_stock | **复现（与目标完全同数值）**：orig=86 decomp=87 true=46 raw=0.914 |
| r3_13_break_gather_layout.py | R3-G | one_prod_to_dataframe | **复现**：orig=65 decomp=65 true=8；break 汇聚块中转重排 |

未复现记录与触发边界：
- **r3_02b / r3_03c**：孤立上下文中 f-string（含/不含 `!s`）与含元组解包/if-elif 的 while 体均反编译正确 → R3-A 与 R3-L 的触发依赖更大的上下文（调用接收者链长度、体首尾语句组合、循环外结构组合），非单一语法特征。
- **r3_04 的 is_delisting 变体**（无 or 条件、单 if + continue + 链尾赋值）在孤立上下文中反编译正确；目标的同形态不匹配可能依赖其在 try 块内的位置或前驱 `if stock not in all_stocks_list: continue` 的存在。is_st 变体（or 条件 + elif + 外层 if）已完整复现该根因。
- **r3_06 初版用 `[1] if c else [0]`**（两个 BUILD_LIST）未复现且反编译正确；改为 `[1 if c else 0]`（单个共享 BUILD_LIST，与目标原始字节码 O99-102 一致）后逐字节复现。说明 R3-F 的触发形状是"列表包裹三元 + 下标赋值 + 块尾 return"三要素。
- #17 run_individual_transform 的完整灾难形态（try 体 pass + except 体吞业务块）由 r3_10 的简化形态（伪造 else 子句）代表，同属 R3-I；更完整的复现需要 while + 双 except + continue 组合，限于篇幅未单独成文件。

---

## 4. 修复建议（按优先级，均为算法级，禁止特判补丁）

**P0-1（R3-L/R3-M，覆盖 #3/#10/#11 三个大函数，一次修复收益最大）：旋转 while 体语句归因完整性校验**
`while not redata and count < 3:` 重试循环重建时，体语句被丢弃（r3_03d 的 sleep、r3_03 的全部体），头部条件被 and→or 反演，整个循环塌缩为 if。三个受损函数累计丢失 140+ 条指令。修复点（`core/cfg/region_analyzer.py` 循环区域识别 + `region_ast_generator.py` `_loop_generate_while`）：
1. 循环体区域认领的指令跨度必须连续覆盖 [循环头, 回边] 间所有块；存在未被认领的块时禁止发射该 while（降级为保守渲染），当前实现显然允许体内块逃逸；
2. 体语句重建后做数量校验（体区域块数 vs 生成语句数），不一致回退；
3. while 条件重建禁止 and→or 反演（与 R2 P1-1 的收敛性校验同源：or 链短路目标必须收敛到同一后继）。
触发组合（探针结论）：体首或 if/elif 链之后的普通调用语句 + 尾部元组解包赋值 + `not X and Y` 头部条件。

**P0-2（R3-I，覆盖 #17/#18/#7c）：异常表驱动的 try/except 块归属不变量**
run_individual_transform（灾难级：try 体 pass、except 体吞入业务块、业务块复制两份）、run_tick_socket（伪造 try/except/else）、get_individual_data（flag 块位移到函数尾）同属一类。CPython 3.11 code object 自带 exceptiontable，归约时应以其条目界定 try 体/handler 的块归属。修复点（`core/cfg/region_analyzer.py` 异常区域分类）：
1. Try 节点认领的指令跨度必须与异常表条目一致；handler 内语句不得吸收 handler 范围外的块；
2. try 体正常出口块只有在原 CFG 中确为 else 目标（条件跳转 False 边指向）时才可渲染为 else 子句——伪造 else 是 r3_10 的直接来源；
3. 除 handler 之外的任何块位移到函数尾（不可达位置）应视为归约失败并回退。

**P0-3（R3-D，覆盖 #12/#13）：循环内 if/elif 分支终结边分类**
分支体末尾的边目标 == 循环回边目标、且该 if/elif 链之后还有同层后续语句时，必须发射 `continue`（is_halt_stock_real 同形态反编译正确，说明该分类在特定上下文失效——r3_04 复现表明 or boolop 条件 + 外层 if 包裹是失效组合）。修复点：`region_ast_generator.py` 的 if/elif 链生成器，为每个分支末尾选边时按"边目标 vs 回边目标"分类，不得把 continue 边当作链出口。此为语义级修复（当前输出会把 True 覆盖成 False）。

**P1-1（R3-F，覆盖 #1/#7）：三元赋值与块尾语句跨度校验**
`x = a if c else b` 与 `d['k'] = [1 if c else 0]` 被降级为裸表达式语句，且同组后续语句（DataFrame 构造、return）被吞。修复点（`region_ast_generator.py` 语句发射 + 伪三元构建 `_try_build_andor_boolop_from_ternary` 家族）：
1. 表达式语句（无赋值目标）的指令跨度若包含 STORE_SUBSCR/STORE_FAST/RETURN_VALUE，或组内存在未被任何语句认领的指令，必须回退保守渲染；
2. 伪三元合并需校验 BUILD_LIST 位置（目标形态是单个共享 BUILD_LIST 在跳转汇合点之后）——r3_06 证明 `[1 if c else 0]` 与 `[1] if c else [0]` 编译形态不同，混用即错。
与 R2 P2-1（下标接收者链完整性）共用"语句指令跨度对齐校验"机制即可。

**P1-2（R3-K，覆盖 #8）：嵌套 if 折叠的 else 体守卫**
`if A: if B: X else: Y` 被折叠为 `if not (A and B): X` + Y 无条件提升，语义反转。R2 P1-1 已修 boolop 纯净性/elif 成形，此为折叠器未校验 else 体的残余形态。修复点：`region_analyzer.py` 条件吸收变换仅当"被吸收的内层 if 无 else 体"时允许；有 else 体时保留嵌套结构。r3_09 与目标逐字节同签名，可直接作为该修复的回归用例。

**P1-3（R3-E，覆盖 #5）：汇聚 return 块归属规则**
≥2 个条件跳转的 False/True 边指向同一 return 块时，该块是公共出口，必须渲染为函数尾（或链尾）公共 return，不得归属给某个内层 else 并为其制造提前 return——否则其余路径落到隐式 return None（fill_minute_or_day_blank 语义破坏）。修复点：出口块被多源共享时禁止单分支认领。

**P2-1（R3-A，覆盖 #9/#14/#15）：f-string 调用参数区域的模板重建**
模板重建必须基于表达式栈模拟（FORMAT_VALUE 消费其真实栈上子表达式：切片 BINARY_SUBSCR、条件表达式、调用），而不是把 LOAD_FAST/LOAD_CONST 的 argrepr 当文字拼接（产生 `stocks=stocksNone{10!s}` 垃圾）；重建失败时回退为 `"...".format(...)` 或保留指令组原样。同时禁止该区域吞并相邻语句（#14 的 `data = collections.OrderedDict()` / `retpanel = pandas.Panel()` 丢失会直接 NameError）。

**P2-2（R3-C/R3-G/R3-B，覆盖 #4/#16/#2/#6 布局级）：链出口与汇聚块保持**
- assert 不得被吸收为前一 if 的 else（#4；r3_12 逐字节复现可直接回归）；
- break/continue 汇聚块应直达循环底公共块，不得引入额外中转块（#16、#6a）；
- 全终结分支链后的不可达隐式 return None 保持原位或省略，不得搬到函数尾并复制（#2、#6b）。
均为等价输出，但消除后可提升 match_rate 约 5 个函数。

**比较器侧**：本轮 18 个函数 raw_ratio 全部 <1.0，无 Round 2 式 R104b 误报；R34（LOAD_ATTR/LOAD_METHOD 归一）在本文件小版本差异场景仍工作正常（首条 diff 中出现的 LOAD_ATTR vs LOAD_METHOD 均为语句丢失后的对齐错位，非版本差异本身）。

---

## 附：本文引用的关键产物

- 全量 mismatch 清单：`python _r3_tmp/_r3_mismatch_list.py site-packages/fly/data/quote.pyc`
- 逐函数对齐 diff：`_r3_tmp/adiff/<func>.txt`（18 份）
- 复现验证日志：`_r3_tmp/final_results.txt`
- 复现流水线：`python _r2_run_repro.py test_repros/round3/r3_XX_*.py [func]`
- 关键反汇编锚点：check_stock O158-268（assert 吸收）、is_ST_stock_real O92-204（continue 丢失）、fill_minute_or_day_blank O3/O53/O131→1176（汇聚 return）、build_current_period_df O92-114（伪三元）、filter_stock_by_status O976-1076（and 链）、get_merger_data O24-64（else 提升）、run_tick_socket O18-144（else 伪造）、get_price O0-11（f-string）
