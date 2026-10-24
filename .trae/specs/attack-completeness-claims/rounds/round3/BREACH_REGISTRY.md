# 破口注册表（canonical，主代理裁决）

> 本表是本规范**唯一**破口编号权威。攻击轮次报告中的临时编号（round2 的 B163–B170、round3 的 B164–B171）**已被本表取代**；各轮报告中的临时号在“来源临时号”列保留以便追溯。
> 开档规则：编号自 **B163** 起连续；同一根因不同表现可归入同一条目并分列「表现」。
> 状态：`开放`（待封闭） / `定性登记`（属口径或表述层，不改实现但须改文档/台账） / `已封闭`。
> 2026-10-23 起止状态登记：`achieve-any-syntax-completeness` 规范于基线 commit `e755d773` 启动（工作轮 `rounds/round11`）；本表 B200 行截断已由该规范 Task 0.6 修复；终态由该规范 Task 8 回填。

## §1 实施层缺陷（需改 `core/cfg/**` 或判定器）

| 编号 | 根因 | 表现（最小复现/证据） | 来源临时号 | 归属层 | 判定空间条目 | 状态 |
|---|---|---|---|---|---|---|
| B172 | 归纳步「二元封闭」不成立 | 三元组合可击穿：① `while True:` 宿主在 try×for×while 中整体丢失（`l0_a4_triple_while_try_for.py`）② 内层 try 体整块消失、两级 finally 错位（`l0_a3_triple_nested_finally_continue.py`）③ for-else 塌陷为顺序语句，带 `break` 时 else 语义破坏（`l0_e8_for_else_break_in_if_in_try.py`）；对照：同族二元投影全绿 | round2 B167 | L0 | JS-*（try/for/while 三元组合） | 开放 |
| B173 | 区域划分**唯一性**破（同优先级由注册顺序裁决） | `FOR_LOOP` 与 `WHILE_LOOP` 同分 50.0/50.0，canonical 取先注册者（`l0_e5_proj_while_for.pyc` e5 @off=4）；机检 22 处平局块 | round2 B166 | L0 | JS-*（判定归属唯一性） | 开放 |
| B174 | 同块双重归属（finally 副本同时计入 try 体 → 副作用重复；for-else 归属塌陷） | 同 B172 ②③ | round2 B167 | L0 | JS-*（finally/loop-else 归属） | 开放 |
| B175 | 守卫触发集未封闭：`continue` 守卫 `_block_is_continue_target`（`region_ast_generator.py:14832`）**无 loop 限定、无 docstring**，12 个调用点全走它；同文件 B106（`:28590`）显式 loop 限定者不对称 | 机检 12 调用点 | round2 B168 | L0 | JS-*（Break/Continue 守卫） | 开放 |
| B176 | 文本—实现不一致（9 处 docstring/注释与代码不符，含 C1 公式引用不存在的字段） | 逐处 file:line 见 ATTACK_L0_THEORY.md §2 AT-06 | round2 B169 | L0 | — | 开放 |
| B166 | 分子为**词法读数**：97 命中中 43 个真实 `ast.X` 代码引用 + 54 个仅字符串类型标签（严格去字面量 22）；「三路径（识别/归约/生成）」**无分路径测点** | `tools/kb/syntax_coverage.py` 命中口径 | round3 B166 | L1/L2 | JS-*（三路径判定） | 开放 |
| B170 | 覆盖检查器 `covered` 语义只验**探针存在**，不验**形态被触发** → covered 轴不承载完备性 | `tools/completeness/coverage_checker.py` 命中逻辑（对照 F1 家族） | round2 B169（AT-09） | L5 | JS-* 全域 | 开放 |

## §2 口径/表述层缺陷（不改实现；须改台账/文档/工具）

| 编号 | 根因 | 表现 | 来源临时号 | 归属层 | 状态 |
|---|---|---|---|---|---|
| B163 | **行级完备判据不校验探针内容**（形态级证据缺失） | ① `global_nonlocal` 行登记探针 `x04_try_deep_hosts.py` 既不含 `nonlocal` 也不含 `global`；真 nonlocal 探针 r10_13/r10_14 未进入任何 stamp（见 `round1/FINDING_F1_GLOBAL_NONLOCAL.md`）② **同构第二例**：`slice` 行登记探针 `r8v8rev3_b104_exprtail_battery.py` 的 `ast.Slice` 实例数 = **0** | round1 F1 / round3 B167 | L1/L5 | 定性登记（同时是实施层取证缺口：需补形态级探针） |
| B164 | **分母构成错误**：97 节点集因 `n[0].isupper()` 大小写过滤漏 7 个真实节点类型（`alias/arg/arguments/comprehension/keyword/match_case/withitem`）→ 分母 ≠ 语言面 | 工具 `tools/kb/syntax_coverage.py` 节点选取规则 | round3 B164 | L1 | 定性登记 |
| B165 | **解释器漂移 + deny-list 失效**：skip 集合中 `'typevar'/'type_param'` 大小写错误 → 对 3.12 永久失效；模拟 3.12：分母 97→102、总项 128→133、同工具读数 **96.24%** | 同上 | round3 B165 | L1 | 定性登记 |
| B167 | **128 非互斥分区**：31 扩展形态中 28 项与 97 节点集重复、3 项为缺项补偿、新增语言面 0；`arg/arguments`（函数形参面）在两侧均无条目 | `docs/refactor/syntax-coverage.json` + 工具清单 | round3 B170 / L1-§2 | L1 | 定性登记 |
| B168 | **行级变体缺口**：25 行声明变体 279，登记探针实际触发 **118（42.3%）**，24/25 行有缺口（仅 AugAssign 20/20 全覆盖） | 逐行 AST 触发统计（round3 §3/§5） | round3 B168 | L1 | 定性登记 |
| B169 | **「证据空集即完备」**默认入完备；三态（完备/破口/零能力）**机器测点 0 处**，无互斥可机检性 | round3 §4/§5 | round3 B169 | L1/L5 | 定性登记 |
| B171 | **C1 的 L(A) 表述与实现无对应字段**：`Region` 无 `out_edges`/`exception_table`（异常表为全局 `cfg.exception_table`）；14 类 L(A) 外通道实测存在（`analyzer.regions` 113×、`get_block_role` 104×、`block_to_region` 38×、`Region.metadata`、区域树导航、块级 `loop_header`…）无一登记 | `core/cfg/**` 机检 | round2 B163/B164 | L0 | 定性登记（须重定义 L(A) 为可机检字段集 + 通道静态审计器） |
| B177 | **双读数缺失导致表述冲突**：v8 的「100%」与判定空间的 62.72%（976/1556）并存而无口径区分，易被读作互相矛盾 | round1 覆盖基线 vs wiki §0 | — | L5 | 定性登记（Task 10 v9 双读数处置） |
| B178 | **「标记 174 处」不可复现**：精确式 `[Bn-V3Rn]` 实测 123（R2:25/R3:22/R4:13/R5:9/R6:12/R7:20/R8:22）/ 宽式 174 / 另一口径 191 —— 取决于正则；wiki/log/rules 旧表述未标口径 | `core/cfg/*.py` 三口径实测 | — | L5 | 定性登记（Task 10 订正表述 + 固定计数规则） |

## §3 不可证伪项（需新判据；非破口）

| 编号 | 项 | 所需判据 | 来源 |
|---|---|---|---|
| U-01 | 归纳基「任意一层正确」 | 形态级不变式 + 覆盖引理 + 机检覆盖器（Task 8/9） | round2 AT-07 |
| U-02 | 守卫是否死代码 | 可参数化 phase 序 + 一致性测试 | round2 AT-08（当前实测未击穿） |
| U-03 | 「100%」与 62.72% 是否矛盾 | 取决于 v9 双读数口径是否成立 | round3 AT-18 |
| U-04 | 零能力 vs 破口的形式区分 | 需实现级可判定的「识别路径缺失」探针 | round3 AT-17 |
| U-05 | `for×match` 组合的语义归属 | 执行级语义差分（Task 9 `semantic_diff.py`） | round2 §2 |
| U-06 | **检测器完备性无独立 oracle**：`l5_selftest.py` 31/31 由同作者构造，xdis 交叉校验只对齐“我们的解析 = 判据的解析” | 独立标注语料 + 第二实现/执行级差分交叉复核 | round7 AT-58 |

## §4 既有残余（承前规范，非本轮新开）

| 编号 | 内容 | 状态 |
|---|---|---|
| B142 | 嵌套 finally 副本归属（`v_b71_face::v_nest_fin_continue`，本轮 `l0_d4_repl_v_b71_face.py` 复现原样红） | **已修复（rr-v5r02，achieve-any-syntax-completeness Task 2）**：副本谱系签名 + 透明链搜索 + 属地继承守卫 + 台账优先重建 + fc 出口物化。验证：冻结比较器 4/4（修复前 3/4）；R1 `v_nest_fin_continue([[0,1]])/([[1,2]])` 返回序列逐项相等；族级判据与探针见 `.trae/specs/achieve-any-syntax-completeness/rounds/round12/probes_b142/README.md`。I.4 判据：全部为副本签名（opname+argval 连续子序列）/台账成员/出口可达/回边目标等区域与 CFG 结构事实，无 B 编号/测试名/输入值专用分支 |
| B143 | finally 体内 break 的 finalbody 子区域派发 | 开放（前规范稀窝登记） |
| B132 | c04/m02（Try 配对 / 模块级） | 前规范已封闭（B155/B156） |

## §5 L3 机制层轮（round5）新增（B179–B194，接 B178）

| 编号 | 根因 | 表现 | 状态 |
|---|---|---|---|
| B179 | 机制族通用性为 0：7 族中 **0 族达形态通用** | R2 形态特化（BoolOp keep-or-pop + merge_ctx 枚举）、R3 部分特化、R4 形态特化、R5 部分特化、R6 形态特化（R7/R8 同） | 开放 |
| B180 | 块级抢归属（非优先级裁决）：同块被两区域争抢 | 新构型探针 R2/R4/R8 多例（while→if 丢语句、finally 移出+append 丢、嵌套 handler 体丢） | 开放 |
| B181 | **B142 重新定性为形态级缺口**（前规范「稀窝」定性被证伪）：Continue 形态整条未产出 + finally 体互换重复；单层亦复现 | _b71_face::v_nest_fin_continue；执行级证实 finally 副本 3 次 | **已随 B142 修复（rr-v5r02）**：continue 形态产出且字节级 4/4；break/三层/finally-return 变体挂账（见 probes_b142/README 影响面） |
| B182 | B143 定性为归约级缺口（Try/If/Break/While 形态齐全，仅 finalbody 派发顺序错） | finalbody 派发序错 | 开放（不计入形态级分子扣减） |
| B183 | 标记计数口径不唯一（口径 A/B/C = 191/123/44+24…；174 全部差异落在 R5） | 三口径复算 | 定性登记 |
| B184 | 守卫触发集未封闭 | R6 B140 五合取、12 调用点 continue 守卫无 loop 限定 | 开放 |
| B185 | **「判绿 ⇒ 对」在单元粒度被实测击穿**（首次） | round5 o4b：函数级 code object 判 Equal，失败仅落嵌套 <listcomp>；另 8 单元「判红但执行级 EQUAL」 | 开放 |
| B186 | R2 族形态特化致 while→if 化丢语句 | 新构型探针 | 开放 |
| B187 | R4 族形态特化致 finally 移出后 append 丢失 | 新构型探针 | 开放 |
| B188 | R6 handler-continue 触发集不对称 | 4 格中 1 格红 | 开放 |
| B189 | R7 slice step 丢失（BUILD_SLICE 三元 vs 二元白名单） | 新构型探针 | 开放 |
| B190 | R5×with 同体语句丢弃（新增） | 叠加探针 d′ | 开放 |
| B191 | 口径层：6 族深度≥3 叠加塌成 pass | 叠加探针 a | 定性登记（与 B172 同族证据） |
| B192 | 口径层：三元真值臂降级 + 极性反转；B151 丢合取项；augassign/del/slice 抢前缀 | 叠加探针 b/d/e | 定性登记 |
| B193 | 守卫相互作用危险 H1–H11（含 H2: B152 与 B150 争同一 merge_block、B150 不查 generated_blocks；H11: with×match 同体语句丢） | 交互分析 | 开放 |
| B194 | 判据层：判绿/判红与执行级语义不对应（8 单元判红但执行级 EQUAL；1 单元判绿但语义错） | round5 执行级差分 | 开放 |

## §6 L2 判定层轮（round4）新增（B195–B201，接 B194）

| 编号 | 根因 | 表现 | 状态 |
|---|---|---|---|
| B195 | 归一化删 handler 块 | 判据 equivalence_check.py patch 链含 fix_unreachable，handler 块被删后比较 | 开放 |
| B196 | 无条件跳转只比 rgval | 属性不可见 | 开放 |
| B197 | attr_list **无 arg 槽位** | 形参槽位不可见（形参换序漏检 159/162） | 开放 |
| B198 | 常量用 == 比较 | 值语义不可见（x=1→x=True 漏检 **83/84 = 98.81%**） | 开放 |
| B199 | 函数 docstring 不在指令流 | 函数 docstring 漏检 **108/108** → **已修复**（rr-v5r03，Task 3.3）：函数/类体按 const[0] str 纯 docstring 判定（`_detect_docstring_statement`）还原 Expr 首语句；模块体按 `LOAD_CONST(0)+STORE_NAME(__doc__)` 指令形态前置字符串字面量并剥去块走查同值 Assign（两形态重编译逐字节相同，字面量形式保源码形态）。判据只读常量表与指令形态（I.4 白名单），无文件/测试名特判。验证：p5_docstring 4/4、x01 模块 docstring 字面量、402 八分片 6617/6617、small34 1568/1568 | 已修复 |
| B200 | 判据与产品共目标函数（region_ast_generator.py:7755/:14244/:21750、code_generator.py:5001 直接以判红为规则理由） | 共同原因 A1–A6 | 开放 |
| B201 | 「已判绿」清单时效性漂移（4/211 = 1.90% 现已判红） | 清单陈旧 | 定性登记 |


## §7 L4 运行轮（round6）新增（B202–B213，接 B201）

> 归属层除 B213 注明外均为 **L4 实现层**；状态除 B213 注明外均为 **开放**。全部可用 rounds/round6/ 下产物复现（ATTACK_L4_RUNTIME.md §6、tools/、repro/、boundary/、offcorpus/、logs/l4_failure_digest.md）。

| 编号 | 根因 | 表现 | 状态 |
|---|---|---|---|
| B202 | 产物不可编译（L4 实现层） | docstring→`__doc__=` 丢值、`**dict`→`{*d: ...}`、三引号 f-string 未闭合；offcorpus 46 样例中 7 个（15.22%）不可编译；JS-DOC-*、JS-IMPORT-* | 开放 |
| B203 | 局部写被改写为属性赋值或整条丢失 ⇒ NameError（L4 实现层） | difflib `_Machinery.__chain_b`（b2j = {}→self.b2j = {}）、get_matching_blocks/get_opcodes/find_longest_match（difflib.py 2064→779 行）；repro/min_difflib2.py；JS-LOCAL-*、JS-ARG-* | 开放 |
| B204 | try/except/else 的 else 体并入主路径（L4 实现层） | csv.Sniffer.has_header 表头判定语义反转（源减/产物减）；repro/min_csv.py；JS-TRY-*、JS-EXCEPT-* | 开放 |
| B205 | 前置校验/raise 删除 ⇒ 非法入参静默接受（L4 实现层） | dataclasses._process_class eq/order 校验消失：源 ValueError / 产物 no error；core/cfg/cfg_builder.py::_parse_instructions isinstance tuple 校验消失：新建异常类参数坍缩为 TypeError: alpha() takes 1 positional argument but 2 were given；JS-RAISE-*、JS-CHECK-*、JS-CLASS-ARGS-* | 开放 |
| B206 | 逻辑分支极性反转（JUMP_IF_TRUE_OR_POP ↔ JUMP_IF_FALSE_OR_POP）（L4 实现层） | core/cfg/cfg_builder.py::_build_basic_blocks 2 处；JS-BOOLOP-*、JS-JUMP-* | 开放 |
| B207 | finally 副本重复发射且脱离原保护路径（L4 实现层） | asyncio/base_events.py::create_server finalbody 1→3，部分副本在 if/else 外 ⇒ 常规路径也执行清理；B142 语料外同族；JS-FINALLY-*、JS-B142-* | 开放 |
| B208 | continue 整条消失（L4 实现层） | socket.py::_sendfile_use_sendfile L394 continue 消失 ⇒ 落入 if 体引发 UnboundLocalError: local variable 'sent' referenced before assignment；同函数 raise TimeoutError('timed out')→pass；B142 语料外同族；JS-CONTINUE-*、JS-B142-* | 开放 |
| B209 | 结构塌陷且当前判据不可证伪（L4 实现层） | 90 层嵌套 if → 单 and 长链（993 字符、两侧行长）字节码+语义均等价 ⇒ 深度 95→7、语句 94→5；boundary/nest_if_90OK.py；JS-IF-*、JS-BRANCH-*、JS-DEPTH-* | 开放 |
| B210 | yield 常量整条丢失（json/encoder.py）（L4 实现层） | `yield '{'`/`yield '}'`/`yield ','` 丢失 ⇒ JSONEncoder(indent=2).encode 输出非法 JSON（'\n  "a"2,\n  "b"1\n'）；typing.get_args 返回 list 而非 tuple；JS-CONST-*、JS-STR-* | 开放 |
| B211 | 类属性初始化丢失 ⇒ AttributeError（L4 实现层） | httpcore/_models.py::URL port 赋值丢失 ⇒ AttributeError: 'URL' object has no attribute 'port'（repr/dict 序列化）；JS-CLASS-* | 开放 |
| B212 | 规模-耗时超线性（L4 实现层） | 4000 条语句 pycdc 89.84 s（1000 条 ≈11 s）≈ O(n^2)，大递归函数进不了 300 s 门禁；JS-SCALE-*、JS-BIGFNC-* | 开放 |
| B213 | 口径/覆盖缺口（PEP 654 except*）（L4 口径层） | 真实语料（stdlib 795 文件+site-packages 14237 文件）ast.TryStar 命中 0；合成样 offcorpus/synth_except_star.py verify 4/4 通过——合成样可判但真实分布缺失无法证明 | 定性登记 |

不新立编号、但须并入既有台账的两项：

| 项 | 处置 |
|---|---|
| 「判据红 ≠ 语义错」：21 个判红样例里 **12 个（57.1%）** 在探针面语义相同 | 并入 **B201**（判据读数分层标注）的口径扩展：本轮补「**红也有假阳性**」的一侧读数 |
| 「通用最小样例复现不了语料外缺陷」（9/10 不复现） | 并入 **B163/B168**（证据-形态错配）的口径扩展：**通用样例绿 ⇒ 该形态在真实上下文里对**，该推断**不成立** |

## §8 L5 证据层轮（round7）新增（B214–B219，接 B213）

> 归属层除 B219 注明外均为 **L5 证据层**；判定空间条目为 **JS-\* 全域（证据层横切）**；状态除 B219 注明外均为 **开放**。
> 全部读数可用 `rounds/round7/logs/l5_evidence_stats.json` 与 `ATTACK_L5_EVIDENCE.md` §6 命令复算。

| 编号 | 根因 | 表现 | 状态 |
|---|---|---|---|
| B214 | **原始源不可恢复**（源级 oracle 缺失） | 402 语料：397 个 `.py` 缺失、5 个存在但全为 0 字节 ⇒ 有效 **0/402**；探针：197 stamped 中 55 个无源、133 个 source-only 无 stamp；1/275 源记录为 0 字节；扫描器初版把 0 字节占位计为可用（已修，前/后读数留档） | 开放 |
| B215 | **证据链自证循环/共同原因** | 探针源→`py_compile`→pycdc→同一 `compare_pyc`；drift **402/402、6617/6617** 精确复现；self-test **31/31**；无独立 oracle；L2 变异漏检 **27.92%**、L4 语料外判据绿 **8.70%** ⇒ 100% 是判据自洽，不是语义验证 | 开放 |
| B216 | **语料/探针形态与规模偏差** | 语料 bytecode **10/32 形态为零**（dataclass/except*/match/nonlocal/PEP604/async_for/chain_compare/ifexp/deep_nest_d3/d5）；**70/402 无函数 code object**、**68/402 单单元**、**61.44% ≤3 形态**；探针 bytecode **8/32 为零**、**84.26% ≤3 形态**；402/14237 = **2.82%** | 开放 |
| B217 | **测量平面/检测器盲区**（0 ≠ 不存在） | `PLANE_LIMITS` 列 9 类 bytecode 不可判定；语料 bytecode `chain_compare=0 / ifexp=0 / deep_nest=0` 与产物源面 **33/59/254/144** 个文件并存；原源 0/402 使“产物下界”假设无法验证 | 开放 |
| B218 | **指标性质**（单元数/绿率 ≠ 正确性） | 6617 单元 = code object，不加权、不执行；68 个单单元文件、top10 占 **19.25%** 单元；L2 漏检 27.92%、L4 语料外绿 8.70%、执行差分 14/56、判红语义相同 12/21 | 开放 |
| B219 | **证据分母/重复计数**（口径层） | 405 stamp 文件 / 404 个不同 stamp 名 / **3342 条记录**（解析到产物 **3275** 条）/ **197 个唯一产物**（16.96 条/产物，解析后 16.62）；单 stamp 最多 29 产物、单产物最多 98 stamp；174 标记 / 197 产物 / 3342 记录三套分母并存；133 source-only 未判定 | 定性登记 |

> 口径扩展：B219 是 **B178**（174 标记口径不唯一）在探针/产物层的扩展；U-06 是 **B170**（covered 只验探针存在）在检测器层的扩展。均不重复计数，但须在 v9 台账中并列登记。
