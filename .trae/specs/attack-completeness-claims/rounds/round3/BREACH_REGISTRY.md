# 破口注册表（canonical，主代理裁决）

> 本表是本规范**唯一**破口编号权威。攻击轮次报告中的临时编号（round2 的 B163–B170、round3 的 B164–B171）**已被本表取代**；各轮报告中的临时号在“来源临时号”列保留以便追溯。
> 开档规则：编号自 **B163** 起连续；同一根因不同表现可归入同一条目并分列「表现」。
> 状态：`开放`（待封闭） / `定性登记`（属口径或表述层，不改实现但须改文档/台账） / `已封闭`。

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

## §4 既有残余（承前规范，非本轮新开）

| 编号 | 内容 | 状态 |
|---|---|---|
| B142 | 嵌套 finally 副本归属（`v_b71_face::v_nest_fin_continue`，本轮 `l0_d4_repl_v_b71_face.py` 复现原样红） | 开放（前规范即稀窝登记） |
| B143 | finally 体内 break 的 finalbody 子区域派发 | 开放（前规范稀窝登记） |
| B132 | c04/m02（Try 配对 / 模块级） | 前规范已封闭（B155/B156） |
