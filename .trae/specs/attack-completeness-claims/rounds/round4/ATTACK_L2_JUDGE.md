# ATTACK_L2_JUDGE —— L2 判定层攻击：判据强度 / 共同原因 / 覆盖缺口

> 规范：`attack-completeness-claims` Task 4（spec.md §攻击分层设计 L2 行、tasks.md 4.1–4.4）。
> 被攻击对象：「判定器够强 ⇒ 单元绿 ⇒ 完备」这条推断链，及其判据本体
> `scripts/pyc_verify.py` → 附件 `pylingual/equivalence_check.py::compare_pyc`。
> 取证方式：**实测为主**。本轮对**记录在案的绿产物**注入已知语义错误，
> 用**判据自身**（同一 `compare_pyc`、同一 patch 链、同一比较语义）复判，
> 并对每一次漏检做**归因**（差异落在哪一层、哪个字段、哪条归一化）。
> 本轮**只测不修判定器**：`core/cfg/**`、`scripts/pyc_verify.py`、`tests/**` 零改动。
>
> **判据本体的落点**：`D:\Desktop\ptrade相关\pylingual\pylingual\equivalence_check.py`
> （仓外；本轮实测 sha256 前 16 位 `9c7567bd6776b36b`，与 `baseline/judge_criteria.md:16` 记的一致）。
> 下文简称 **eq**（附件判据本体）；**pyc_verify** 指 `scripts/pyc_verify.py`；
> **CLI 口径**指 `python -X utf8 scripts/pyc_verify.py single <pyc> --source <产物>`（任务约定形式）。
>
> **本轮测法**：全部读数由 `_scripts/mutate.py` 产生，**只走 CLI 子进程**，
> 不复用 `pyc_verify` 内部 `evaluate()` API ⇒ 读数 = 使用者实际敲命令看到的 `[single] status=…`。
> 同轮另有一次 in-process 全语料读数（`_scripts/mutation_experiment.py`，416 绿产物 / 2046 变异），
> 二者**交叉核对**（§4.5）。

---

## §0 摘要

### 0.1 结论一句话

**「判定器够强」被证伪（击穿）。** 判据在**控制流/结构**维度确实强（删语句、极性反转、
语句换序、实参换序、异常类型改名、装饰器换序、match 绑定/守卫、with 项序、del、assert 消息、
跨函数调用目标、模块级常量、类属性 —— 逐条 100% 抓到），但在**值语义 / 槽位语义 /
元数据（`co_consts`）/ 无条件跳转属性 / 归一化抹平**五个维度上**结构性失明**，
且这些失明**不可由「多跑几个探针」消除**。

### 0.2 本轮实测读数（CLI 口径；207 个绿产物 / 211 个抽样子集）

| 口径 | 变异次数 | 漏检 | 漏检率 |
|---|---|---|---|
| **任务要求的 8 类** | **1031** | **99** | **9.60%** |
| 补测 3 族（形参换序 / 函数 docstring / 保证语义对照） | 280 | 267 | 95.36% |
| **合计** | **1311** | **366** | **27.92%** |

**任务要求的 8 类逐族（CLI 实测，`_out/mutate_summary.json`）**：

| # | 族 | 语义错误 | mutated | missed | miss-rate | 归因（§4.4） |
|---|---|---|---|---|---|---|
| (a) | `a_num_int` | 改数值：整数字面量 n→n+1 | 112 | **0** | **0.00%** | — |
| (b) | `b_cmp_polarity` | 翻转比较：a\<b ↔ a\>b（≤/≥ 同理） | 78 | **0** | **0.00%** | — |
| (c) | `c_del_assign` | 删语句：删除一条赋值语句 | 176 | **0** | **0.00%** | — |
| (d) | `d_int_to_bool` | **x=1 改 x=True（纯类型变，值不变）** | 84 | **83** | **98.81%** | COMPARATOR-BLIND 79 + PIPELINE-DEFECT 4 |
| (e) | `e_str_content` | 改字符串：字符串字面量内容 +X | 166 | 1 | 0.60% | NORMALIZED-AWAY 1 |
| (f) | `f_stmt_swap` | 换语句序：交换两条**相互独立**的赋值语句 | 107 | **0** | **0.00%** | — |
| (g) | `g_rename_local` | 改标识符：函数内形参/局部一致改名 | 167 | 15 | 8.98% | OUT-OF-INSTRUCTION 12 + NORMALIZED-AWAY 3（**均为语义惰性**，见 §4.2 诚实读数） |
| (h) | `h_arg_swap` | 换实参序：交换同一调用的两个实参 | 141 | **0** | **0.00%** | — |
| — | **合计** | — | **1031** | **99** | **9.60%** | — |

**补测 3 族（CLI 实测）**：

| 族 | 语义错误 | mutated | missed | miss-rate | 归因 |
|---|---|---|---|---|---|
| `h_param_order` | **交换两个形参的顺序**（调用约定改变） | 162 | **159** | **98.15%** | SLOT-INDEX-BLIND 149 + PIPELINE-DEFECT 4 + OUT-OF-INSTRUCTION 3 + NORMALIZED-AWAY 3 |
| `j_func_docstring` | **改函数 docstring**（`__doc__` 语义） | 108 | **108** | **100.00%** | OUT-OF-INSTRUCTION 81 + NORMALIZED-AWAY 14 + SLOT-INDEX-BLIND 9 + PIPELINE-DEFECT 4 |
| `g3_kwparam_rename` | **保证语义**的改标识符（改「被以关键字实参调用」的形参名 ⇒ 调用必抛 TypeError） | 10 | **0** | **0.00%** | —（**对照组：判据对语义确定的标识符改写有效**） |

### 0.3 三条独立击穿证据（全部可复现，§4.7 独立复跑 14/14 一致）

| # | 击穿 | 实测读数（CLI） | 根因（附件行号） |
|---|---|---|---|
| E1 | **值类型盲区**：`x=1 → x=True`（**纯类型变，值不变**） | **83/84 = 98.81% 漏检**；补测 `x=1 → x=1.0`（in-process 全语料）**222/222 = 100% 漏检** | `eq:59` `argval_a == argval_b` 用 Python `==`；`bool` 是 `int` 子类、`1 == 1.0` 亦真 ⇒ **值的类型**在判据内不可分辨 |
| E2 | **形参槽位盲区**：交换两个**形参**的顺序（调用约定改变） | **159/162 = 98.15% 漏检**（in-process 全语料 **306/306 = 100%**） | `eq:47` 的属性清单**不含 `arg`（槽位下标）**，只比 `argval`（名字）；形参换位时**名字不变、槽位变** ⇒ 判据看不见 |
| E3 | **归一化抹平盲区**：try 体为空（`try: pass`）时**整个 except handler 块**被 `fix_unreachable` 从**两侧同时删除** | 构造探针 `try_pass_handler_body` / `try_pass_except_type` / `except_tuple_order` **全部 MISS**；对照 `try_assign_handler_body` / `try_raise_handler_body`（try 体有真实语句）**全部 CAUGHT** | `eq:194-195` 的 patch 链含 `fix_unreachable`；`EditableBytecode.py:440-447` `remove_unreachable_instructions` = `set(instructions) - set(cfg.nodes)`；`control_flow_graph.py:133-146` 只对**落在异常表区间内的指令**加 EXCEPTION 边 ⇒ 区间内无存活指令 ⇒ handler 不可达 ⇒ 被删 |

### 0.4 共同原因（判据与产品共享）

产品 `core/cfg/**` 的发射规则**直接以判据的判红为理由**：

- `core/cfg/region_ast_generator.py:7755`：「（重编译跳转目标错位，pyc_verify "Different control flow"）」；
- `core/cfg/region_ast_generator.py:14244`：「IF_FALSE 的落点从 continue 块错位到 break 块，pyc_verify …」；
- `core/cfg/region_ast_generator.py:21750`：「pylingual is_control_flow_equivalent 的按址节点映射出边集合随之不等」；
- `core/cfg/code_generator.py:5001`：「!s (flag=1) 与无转换 (flag=0) 产生不同的 FORMAT_VALUE 字节码，
  **必须显式输出 `!s` 以保证字节码等价**」。

实测计数（`core/cfg/*.py`）：「字节(码)等价」表述 **23** 处；「判据」**1435** 处；直接点名判据工具 **3** 处。

⇒ **判据与产品是同一条优化回路**：产品把「让判据判 Equal」当目标函数，
于是「形状保住但语义变了」这一类缺陷**恰好落在判据的盲区里**。
判据**在结构上不可能**证伪产品在这条回路上的选择。详见 §3。

### 0.5 逐项判定（AT-2N）

| AT | 攻击项 | 判定 | 一句话证据 |
|---|---|---|---|
| AT-21 | 判据实际比较面测绘（盲区表） | **击穿** | §2.2 十八维度表 + §2.3 三十四探针实测 |
| AT-22 | 值语义盲区（1/True/1.0） | **击穿** | `83/84`（CLI）/`222/222`（in-process 全语料）漏检；根因 `eq:59` |
| AT-23 | 常量精度盲区（int/float/complex/大整数） | **击穿** | `i_int_to_float 222/222`；`d_any_int_to_bool` 仅在被改值为 1 时漏检（78/215）⇒ 漏检**只由 `==` 等价类决定**，与「精度」无关 |
| AT-24 | 字符串与转义 | **未击穿**（内容层已比；转义写法不可见但**语义等价**） | `e_str_content` 165/166 被抓；唯一 1 例归因 `NORMALIZED-AWAY`（非字符串维度） |
| AT-25 | f-string 语义 | **未击穿** | 构造探针 `fstring_literal` / `fstring_conversion` 均 CAUGHT |
| AT-26 | 注解 | **部分击穿** | 参数/返回/模块级注解 **CAUGHT**；函数内局部注解被 pycdc 丢弃（语义惰性） |
| AT-27 | docstring | **击穿（不对称）** | **函数** docstring 只在 `co_consts[0]`、从不进指令流 ⇒ **108/108 漏检**；**模块/类** docstring 经 `STORE_NAME __doc__` 进指令流 ⇒ CAUGHT |
| AT-28 | 装饰器序 / 闭包捕获 / global-nonlocal 绑定 | **未击穿**（运行时语义层；**元数据/自省层为 partial 盲区**） | 装饰器换序 `23/23` CAUGHT；闭包改绑 CAUGHT；`global`/`nonlocal` 改绑 CAUGHT（构造探针） |
| AT-29 | 异常别名 / except 元组序 | **击穿** | `except (A,B) → except (B,A)` **MISS**（handler 块被归一化删除，E3）；异常类型**改名** CAUGHT |
| AT-30 | 归一化抹平（NOP/行号/EXTENDED_ARG/间接跳转/不可达） | **击穿** | E3（handler 体被删）+ 死代码族 `n_dead_code 166/308` 漏检 + **12 例**无条件跳转属性差异（`eq:50-51` 早退分支跳过整组 `attr_list`） |
| AT-31 | 副作用序 / 生成器 / async 调度 / 异常消息 | **不可证伪** | 判据**从不执行**（`eq:180-226` 无执行路径）⇒ 这些维度**在现有判据体系内根本无法判定**；须转方法层（Task 9 `semantic_diff.py`） |
| AT-32 | 共同原因失败 | **击穿** | §3：产品 4 处显式引用判据内部语义；「字节(码)等价」23 处、「判据」1435 处 |
| AT-33 | 跨函数/模块级/类级/闭包/装饰器装配覆盖 | **击穿（口径层）** | §5：装配语义**不在任何独立维度被判定**；实测漏检率与作用域**无关**（全部由值/槽位驱动） |
| AT-34 | 变异测试（≥6 类语义错误） | **击穿** | §4：8 类 1031 次变异 99 漏检（**9.60%**）；补测 3 族 280 次变异 267 漏检（95.36%），其中 2 族 ≈100% |
| AT-35 | 「判据自检 ⇒ 判据可用」的覆盖面 | **击穿** | `pyc_verify.py:297,332-346` 的内建自检**只覆盖 2 类变异**（常量、极性）；这两类恰是判据最强的维度 ⇒ 自检结论不可外推 |
| AT-36 | 单元粒度「绿 ⇒ 语义等价」 | **击穿** | 与 round5 B194 同域但不同根因：round5 证「**哪个**单元绿错了」，本轮证「**该绿的单元为何**绿错」（五类机制）；§6 展开 |
| **AT-37** | **「已判绿」清单的时效性**（本轮新增） | **击穿** | 211 个抽样的记录在案绿产物中 **4 个（1.90%）当前已判红**（§5.2）⇒ 「绿产物」不是稳定前提 |

---

## §1 攻击项清单

| AT | 名称 | 目标（file:line） | 可证伪条件 | 实际结果 | 判定 |
|---|---|---|---|---|---|
| AT-21 | 判据比较面测绘 | `pyc_verify.py:93-131`、`eq:14-226` | 列出判据逐项实际比较的字段，并与「语义维度」一一对账 | 十八维度表 + 34 探针实测 | 击穿 |
| AT-22 | 值语义 | `eq:59` | 注入 `1→True`，判据应判红 | 83/84 判绿 | 击穿 |
| AT-23 | 常量精度 | `eq:59` | 注入 `1→1.0`，判据应判红 | 222/222 判绿 | 击穿 |
| AT-24 | 字符串与转义 | `eq:56-66` | 注入字符串内容/转义改动 | 内容被抓（165/166） | 未击穿 |
| AT-25 | f-string | `eq:46-66` | 注入 `!r` 转换 / 字面量段改动 | 全被抓 | 未击穿 |
| AT-26 | 注解 | `eq:80-99`（无注解通道） | 注入参数/返回/局部/模块级注解改动 | 参数/返回/模块级被抓；局部注解被产品丢弃 | 部分击穿 |
| AT-27 | docstring | `eq:80-99`（`co_consts` 不比） | 注入函数/模块/类 docstring 改动 | 函数 108/108 漏；模块/类被抓 | 击穿 |
| AT-28 | 装饰器序/闭包/global-nonlocal | `eq:56-66` | 注入装饰器换序、闭包改绑、global/nonlocal 改绑 | 构造探针全被抓 | 未击穿 |
| AT-29 | 异常别名/元组序 | `eq:83`（异常表整体比） | 注入 `except` 类型改名/元组换序/handler 体改写 | 改名被抓；元组序与 handler 体**漏** | 击穿 |
| AT-30 | 归一化抹平 | `eq:194-195` | 注入不可达代码/空 try 体 handler 改动 | 死代码 166/308 漏；handler 体 100% 漏 | 击穿 |
| AT-31 | 执行级语义（副作用序/生成器/async/异常消息） | `eq:180-226` | 判据体系内不存在可判定路径 | 不可判定 | 不可证伪 |
| AT-32 | 共同原因失败 | `core/cfg/**` 对判据内部的引用 | 列出共享假设并给出可分离的探针 | 4 处显式引用 + 目标函数同构 | 击穿 |
| AT-33 | 装配覆盖缺口 | `eq:199`（逐 code object 独立判） | 量化跨函数/模块级/类级/闭包/装饰器覆盖率 | 装配不在任何独立维度 | 击穿（口径层） |
| AT-34 | 变异测试 | `pyc_verify.py::evaluate` | ≥6 类语义错误，统计漏检率 | 8 类 9.60%；补测 3 族 95.36% | 击穿 |
| AT-35 | 判据自检覆盖面 | `pyc_verify.py:284-320` | 自检覆盖的变异族数 ≥ 实际高风险族数 | 只有 2 类（常量、极性） | 击穿 |
| AT-36 | 单元粒度推断链 | `pyc_verify.py:129`（文件级全或无） | 「单元绿 ⇒ 语义等价」是否成立 | 不成立（round5 o4b + 本轮五类机制） | 击穿 |
| AT-37 | 「已判绿」清单时效性 | `pyc_verify.py:129` + recorded stamps | 记录在案的 success 行当前是否仍 success | 211 抽样中 4 个（1.90%）已判红 | 击穿 |

---

## §2 判据解剖

### 2.1 `pyc_verify.py` 与附件判据**实际**比较什么（逐项 file:line）

**第一层：`scripts/pyc_verify.py`（装载 / 配对 / 报告，判定本体不在此）**

| # | 动作 | 行号 | 事实 |
|---|---|---|---|
| 1 | 判据本体在**仓外**附件 | `:3-8`（模块 docstring 原文）、`:47-68` | 仓内不可审计；附件根 `D:\Desktop\ptrade相关\pylingual`（`:40`），可用 `--pylingual` 换 ⇒ **换尺子**风险在 L2 攻击面内 |
| 2 | 尺子锚定只用 sha256 **前 16 hex** | `:79-83`（`ruler_stamp`）、`:221`（报告头 `ruler`） | 锚定强度弱；附件换版不可察（除非比对前缀） |
| 3 | **产物重编译后再比** | `:101` `py_compile.compile(source, cfile=recompiled, doraise=True, optimize=0)` | 比的不是原始 `.py`，而是产物**重新编译出的字节码**；产物语法错 ⇒ `compile_error`（`:102-109`） |
| 4 | 调用附件判据 | `:112` `results = compare_pyc(pyc, recompiled)` | 逐 code object 出 verdict |
| 5 | 单元计数 | `:122-123` | `units_total` / `units_success` |
| 6 | **文件级判定是「全或无」** | `:129` | `status = success` 当且仅当 `units_success == units_total` |
| 7 | 空结果无效 | `:124-127` | `results` 为空 ⇒ `error` |
| 8 | 内建变异**只有两类** | `:297`、`:332-346` | `_mutate_return`（改 `return None/True/False/数字`）、`_mutate_compare`（翻转 `>`/`<`/`==`/`!=`）⇒ selfcheck 的「判据可用」结论**只覆盖这两族** |
| 9 | 退出码语义 | `:181`（single）、`:230`（batch） | `batch` 仅 `error`/`compile_error` 非空才 rc=1 ⇒ **文件级 failure 不影响 batch 退出码** |
| 10 | 解释器硬门 | `:381-383` | 语料必须是 3.11 字节码（本轮实测解释器 3.11.7） |

**第二层：附件 `equivalence_check.py::compare_pyc`（真正的比较算子；本轮逐行复核）**

| # | 被比较的方面 | eq 行号 | 判定内容 | **不比较什么** |
|---|---|---|---|---|
| 1 | 代码对象数量 | `:80` | `len(pyc_a) != len(pyc_b)` ⇒ 不等即失败 | — |
| 2 | 代码对象**按 name 配对** | `:158` `difflib.SequenceMatcher(a=[x.name for x in bc_a], b=[x.name for x in bc_b])` | 配不上 ⇒ `Missing bytecode` / `Extra bytecode` | **同名 code object 的配对是位置性的**（`co_qualname` 层级不参与） |
| 3 | 异常表**整体相等** | `:83` `pyc_a.named_exception_table != pyc_b.named_exception_table` | handler/depth/区间整体比 | 不做**逐 handler**定位 |
| 4 | CFG 节点数 | `:17` | 基本块节点数必须相等 | — |
| 5 | CFG **出边目标集合** | `:28-40` | 按 offset 排序映射节点后逐节点比出边集合 | 边属性/边类型（EXCEPTION 边与普通边**同权**） |
| 6 | 指令级属性 | `:47` `attr_list` | `opname, opcode, optype, real_size, has_arg, has_extended_arg, offset, is_jump_target` 逐字段相等 | **`arg`（槽位下标）不在清单内** |
| 7 | **无条件跳转只比 argval** | `:50-51` | 双方均为无条件跳转 ⇒ **早退**，只比 `argval`（目标偏移） | **整组 `attr_list` 被跳过**（`opname`/`opcode`/`optype`/`real_size`/`has_arg`/`has_extended_arg`/`offset`/`is_jump_target`）⇒ `JUMP_FORWARD`↔`JUMP_BACKWARD` 互换与 `is_jump_target` 差异均不可见（§4.4，12 例） |
| 8 | 操作数值 | `:59` `if argval_a == argval_b:` | 相等即通过 | **Python `==` 语义** ⇒ `1`/`True`/`1.0` 互判相等 |
| 9 | 嵌套 code object 直接放行 | `:62-64` | `hasattr(argval,'co_code')` ⇒ True | 嵌套体本身（改由递归配对比对） |
| 10 | 归一化补丁链 | `:194-195` | `remove_extended_arg, remove_nop, fix_indirect_jump, fix_unreachable, remove_extended_arg, replace_firstlno` | **`fix_unreachable` 会删块**（见 §2.3 维度 11） |
| 11 | verdict 分类 | `:201-224` | 5 类：Extra/Missing bytecode、Different control flow、Different bytecode、Equal | — |
| 12 | **从不执行** | `:180-226` 全文 | 只比静态结构 | 返回值、副作用、异常消息、副作用顺序 |

**附件内部两处与判据相关的实现事实**

- `Instruction.py:116-122`：`is_uncond_jump` = `opcode in bytecode.opcode.JUMP_UNCONDITIONAL`（**一组**无条件跳转 opcode）⇒ `eq:50-51` 对整组只比目标偏移。
- `EditableBytecode.py:440-447` `remove_unreachable_instructions` = `set(self.instructions) - set(cfg.nodes)`；
  `bytecode_patches/fix_unreachable.py:4-7` = `remove_unreachable_instructions() + remove_useless_jumps() + _bake_jumps()`。
- `control_flow_graph.py:132-148`（`inst_to_edges_311`）：`:137` 只在**指令偏移落在异常表区间内**时取到 handler，
  `:145-146` 才加 EXCEPTION 边 ⇒ 区间内无存活指令 ⇒ handler 块不在 CFG 节点集 ⇒ 被 `fix_unreachable` 删除。
- `bytecode_patches/remove_docstrings.py` **存在但 `compare_pyc` 未使用** ⇒ docstring 的可见性完全取决于它是否落在指令流里。

### 2.2 判据盲区表（任务要求的 15 个维度 + 补充）

判据：`compared` = 该维度的差异进入被比较的字段；`partial` = 仅**部分**形态进入；
`not compared` = 该维度的差异**不进入任何被比较字段**。

| # | 维度 | 判定 | 依据（file:line / 实测） | 说明 |
|---|---|---|---|---|
| 1 | **值语义**（1 / True / 1.0） | **not compared** | `eq:59`；CLI 实测 `d_int_to_bool 83/84` 漏检；in-process `i_int_to_float 222/222` | `==` 把三者判为相等；**值的类型**不可分辨 |
| 2 | **常量精度**（大整数/float/complex） | **not compared** | `eq:59`；`d_any_int_to_bool` 仅在被改值为 1 时漏检（78/215） | 漏检**只由 `==` 等价类决定**，与精度无关 |
| 3 | **字符串**（内容层） | **compared** | CLI 实测 `e_str_content` 165/166 被抓（唯一 1 例为 `NORMALIZED-AWAY`） | 字符串常量进指令流（`LOAD_CONST`） |
| 3b | **字符串**（转义写法层） | **not compared**（但语义等价） | `'\x41'` vs `'A'` 在常量层是同一对象 | 不可见但**语义等价**，非破口 |
| 4 | **注解**（参数/返回/模块级） | **compared** | `annot_param` / `annot_return` / `annot_module` 均 CAUGHT | 注解在 def 时求值 ⇒ 进外层指令流 |
| 4b | **注解**（函数内局部） | **not compared** | 构造探针 `annot_local` NOT_APPLICABLE：pycdc 丢弃局部注解（`cp_annot_localOK.py` 为 `v = 1`） | 局部注解运行时**不求值**（PEP 526）⇒ 语义惰性 |
| 5 | **docstring**（函数） | **not compared** | CLI 实测 `j_func_docstring 108/108` 漏检；构造探针 `docstring_func` MISS | 只在 `co_consts[0]`，**无任何指令**（实测：`def f(): """DOC"""` 的指令流为 `RESUME/LOAD_CONST None/RETURN_VALUE`） |
| 5b | **docstring**（模块/类） | **compared** | `doc_dunder` CAUGHT | CPython 3.11 对模块/类 docstring 发 `LOAD_CONST 'DOC'; STORE_NAME '__doc__'` ⇒ 进指令流（**与函数 docstring 不对称**） |
| 6 | **装饰器序** | **compared** | 构造探针 `decorator_order` CAUGHT；补测 `s_decorator_swap 23/23` | 装饰器应用顺序改 ⇒ 指令序列改 |
| 7 | **闭包捕获** | **partial** | 构造探针 `closure_capture` CAUGHT（改绑到**异名**变量） | 比的是 `LOAD_DEREF <名字>` 的 argval；**同名改绑**不可分辨；`co_freevars`/`co_cellvars` **从不比较**（`eq:80-99` 只比数量+异常表+指令） |
| 8 | **异常别名**（类型身份） | **partial** | `except_alias` CAUGHT（改名）；`p_except_type 171/171` CAUGHT | 比的是 `LOAD_GLOBAL <名字>` 的 argval ⇒ **类的身份**不比（同名不同类、运行期改绑不可见） |
| 8b | **except 元组序** | **not compared** | 构造探针 `except_tuple_order` **MISS** | 元组常量在 handler 块内 ⇒ 被 `fix_unreachable` 删除（E3） |
| 9 | **副作用序**（语句级静态序） | **compared** | CLI 实测 `f_stmt_swap 107/107`、`h_arg_swap 141/141`、构造探针 `side_effect_order` CAUGHT | 静态指令序被比 ⇒ 语句换序被抓；**运行时**可见的副作用顺序（跨函数/跨模块）不可判定（见 17） |
| 10 | **lambda** | **compared**（默认值层） | `lambda_default` CAUGHT | 默认值在 `MAKE_FUNCTION` 前压栈 ⇒ 进外层指令流；lambda 体本身的语义随体指令流被比 |
| 11 | **生成器语义**（惰性/send/throw/StopIteration 值） | **not compared**（协议层） | `yield_value` CAUGHT（只到 yield 的**值**） | 生成器的**协议行为**须执行才可见 |
| 12 | **async 语义**（await 参数值 / 调度 / 取消） | **partial** | `async_await` CAUGHT（参数值） | 调度与取消语义须执行才可见 |
| 13 | **match 绑定/守卫** | **compared** | `match_guard` CAUGHT、`match_binding_order` CAUGHT | 守卫是比较指令；捕获顺序改 ⇒ `STORE_FAST` 序改 |
| 14 | **with `__exit__` 序** | **partial** | `with_item_order` CAUGHT（进入序） | `__exit__` 的**逆序调用**与**抑制语义**须执行才可见 |
| 15 | **del** | **compared** | `del_target` CAUGHT | `DELETE_FAST` opname 进指令流 |
| 16 | **global/nonlocal 绑定** | **partial** | `nonlocal_target` CAUGHT、`global_target` CAUGHT（改绑到**异名**）；补测 `w_global_stmt 28/294` 漏检 | `global`/`nonlocal` 声明**本身不产生指令**，只改名字的解析方式 ⇒ **同名**改绑不可分辨；补测的 28 例归因见 §4.4 |
| 17 | **assert** | **compared** | `assert_message` CAUGHT；`z_assert_msg 6/6` CAUGHT | 消息是 `LOAD_CONST` ⇒ 进指令流；「测试先于消息求值」的次序也进指令流 |
| 18 | **形参槽位次序** | **not compared** | `eq:47` 属性清单无 `arg`；CLI 实测 `h_param_order 159/162` 漏检 | 名字不变、槽位变 ⇒ 判据不可见（E2） |
| 19 | **无条件跳转指令的属性**（方向 / `is_jump_target` / `real_size`） | **not compared** | `eq:50-51` 早退分支只比 `argval`；CLI 归因中 **12 例** PIPELINE-DEFECT | 前后跳互换、无条件跳转上的**跳板标记**差异 ⇒ 全部不可见（§4.4） |
| 20 | **死代码** | **not compared** | `n_dead_code 166/308` 漏检（in-process 全语料） | `fix_unreachable` 删除不可达指令（两侧同时删） |
| 21 | **行号信息** | **not compared** | `eq:194-195` `replace_firstlno` | traceback 行号语义差异不可见 |
| 22 | **co_varnames / co_freevars / co_cellvars / co_flags / co_names / co_consts** | **not compared** | `eq:80-99`（只比数量 + 异常表 + 指令）；实测 `g_rename_local` OUT-OF-INSTRUCTION 12、`j_func_docstring` OUT-OF-INSTRUCTION 81 | 槽位集合与常量池变化不改指令流 ⇒ 不可见 |
| 23 | **返回值 / 副作用 / 异常消息 / 运行时顺序** | **not compared** | `eq:180-226` 无执行路径 | 判据**从不执行** ⇒ 这一整族在现有判据体系内**不可判定**（转方法层） |

### 2.3 构造级探针实测（34 个语义维度各一个最小探针）

流程与 `attain-true-completeness/rounds/round1/rec1_run.py` 同源：
写探针 `.py` → `py_compile`(3.11) → `pycdc.py -o <base>OK.py` → `pyc_verify.py single`（基线）
→ 注入语义错误 → `pyc_verify.py single`（判定）→ `CAUGHT` / `MISS` / `NOT_APPLICABLE`。
产物：`rounds/round4/_probes/`（34 组 `.py`/`.pyc`/`OK.py`）、`_out/construct_probe.json`。

| 结果 | 计数 | 探针 |
|---|---|---|
| CAUGHT | 27 | annot_param、annot_return、annot_module、decorator_order、decorator_arg、closure_capture、nonlocal_target、global_target、except_alias、lambda_default、yield_value、async_await、match_guard、match_binding_order、with_item_order、del_target、assert_message、fstring_literal、fstring_conversion、kwarg_name、cross_function_call、module_const_used、class_attr、side_effect_order、doc_dunder、**try_assign_handler_body**、**try_raise_handler_body** |
| **MISS** | **4** | **docstring_func**（函数 docstring）、**except_tuple_order**（元组序）、**try_pass_except_type**（except 类型）、**try_pass_handler_body**（handler 体） |
| NOT_APPLICABLE | 3 | annot_local（pycdc 丢弃局部注解）、docstring_module / docstring_class（pycdc 改写成 `__doc__ = '...'`，由 `doc_dunder` 覆盖） |

> **探针目录的两点披露**：`_probes/` 下另有 **2 个**探针产物（`cp_fstring_field`、`cp_future_annotations`）
> 的 `.py`/`.pyc`/`OK.py` 存在，但它们的源**不在最终 PROBES 清单**（`construct_probe.py:519-575`）内，
> 因此**没有记录 verdict**，**不计入**上面 34 条读数；`construct_probe.json` 的 34 条是**唯一**读数来源。

> **对照实验（E3 的直接证据）**：同一形态、同一变异、只改 try 体：
> `try: pass` ⇒ **MISS**；`try: x = 1` ⇒ **CAUGHT**；`try: raise E()` ⇒ **CAUGHT**。
> ⇒ 漏检的触发条件是「**异常表区间内没有存活指令**」，与 handler 体内容无关。

### 2.4 归因器（判据失明的五种机制）

`_scripts/miss_attribution.py` 对每一次漏检做**四级归因**（对原始 pyc 与变异产物分别计算指纹）：

| 归因 | 含义 | 可改进性 |
|---|---|---|
| `OUT-OF-INSTRUCTION` | 归一化前后指令流都相同 ⇒ 差异**根本不在指令流**（落在 `co_consts`/`co_varnames`/`co_flags` 等从不比较的维度） | **须新增判据维度**（不是改算子） |
| `COMPARATOR-BLIND` | 指令流相同，但**类型敏感**比较下不同 ⇒ 差异被 `==` 抹平 | **改比较算子即可**（类型敏感标签） |
| `SLOT-INDEX-BLIND` | 指令流仅在 `arg`（槽位下标）上不同 | **改比较算子即可**（补 `arg` 字段） |
| `NORMALIZED-AWAY` | 归一化前不同、归一化后相同 ⇒ 被 patch 链抹平 | **须改归一化策略**（不可删块） |
| `PIPELINE-DEFECT` | 判据自身语义下归一化后仍不同，却仍判绿 | **比较算子缺陷**：命中 `eq:50-51` 的早退分支（无条件跳转只比 `argval`）⇒ 该指令的整组 `attr_list` 被跳过；同时 CFG 只比**出边目标集合**（同目标 ⇒ 同边集）⇒ **判据的两道防线同时失效** |

---

## §3 共同原因失败：判定器与产品共享的假设

### 3.1 共享假设清单

| # | 共享假设 | 证据 | 后果 |
|---|---|---|---|
| **A1** | **「重编译后字节码形状相同 ⇒ 语义等价」**，且该形状就是产品的**目标函数** | `core/cfg/region_ast_generator.py:7755`、`:14244`、`:21750` 直接引用 `pyc_verify` / `pylingual is_control_flow_equivalent`；`core/cfg/code_generator.py:5001`「必须显式输出 `!s` 以保证字节码等价」；实测 `core/cfg/*.py`：「字节(码)等价」23 处、「判据」1435 处、点名判据工具 3 处 | 任何「形状保持但语义变了」的缺陷**必然落在判据盲区**；判据**不能**证伪产品在这条回路上的选择 |
| **A2** | **「常量相等用 Python `==` 判」** | `eq:59`；`core/cfg` 的常量折叠同用 `==` | `1`/`True`/`1.0` 不可分辨；产品若也把二者当同一值，其错误**不可被判据发现** |
| **A3** | **「归一化链（remove_nop / fix_unreachable / replace_firstlno / remove_extended_arg / fix_indirect_jump）是语义中性的」** | `eq:194-195`；`EditableBytecode.py:440-447` | 已证伪：`fix_unreachable` 会删 handler 块（E3） |
| **A4** | **「code object 可逐个独立判定」** | `eq:199`（逐 code object）；`pyc_verify.py:129`（文件级全或无） | 装配语义（跨函数/模块级/类级/闭包/装饰器）**不在任何独立维度被判定**；单元粒度的「绿」不可外推 |
| **A5** | **「不执行即可判定」** | `eq:180-226` 无执行路径 | 副作用顺序、生成器协议、async 调度、异常消息、运行期绑定**不可判定** |
| **A6** | **「code object 按 name 配对即等价于语义配对」** | `eq:158`（`difflib` on name 序列） | 同名 code object（如多处 `<listcomp>`）配对是位置性的；`co_qualname` 层级不参与 |

### 3.2 每项的探针设计（每项 ≥3 个：换 oracle / 不可伪造属性）

**A1（形状即目标函数）**
1. **换 oracle**：把判据换成**执行级差分**（同输入序列分别执行源与产物，比对返回值 / 全局与属性写入 / 副作用序列 / 异常类型与消息）。round5 的 `tools/l3_semdiff.py` 已是原型（`rounds/round5/ATTACK_L3_MECHANISM.md:58`），应提升为 Task 9 的 `tools/completeness/semantic_diff.py` 并进 E 门禁。
2. **不可伪造属性**：`co_exceptiontable` 的 **depth 字段**（嵌套 handler 的层级）。判据只比 `named_exception_table` 的整体相等（`eq:83`），而产品的区域归属判据依赖 depth；「depth 相同但 handler 归属不同」的 pyc 只能由**异常表字节改写**伪造（源码不可伪造）。
3. **不可伪造属性**：**指令偏移布局**（每条指令的 offset 实值）。判据比 `offset` 字段，但 `remove_nop`/`fix_unreachable` 会重排 ⇒ 应引入「语义级对齐」oracle（把两侧按语义位置对齐后比较），而非按 offset 顺序比。

**A2（`==` 语义）**
1. **换 oracle**：类型敏感比较：`argval` 换 `(type(v), repr(v))` 标签。实测可把 `d_int_to_bool` 的 **79 次 `COMPARATOR-BLIND`** 漏检转成判红；**余 4 例属 `PIPELINE-DEFECT`**（无条件跳转属性，须另修 `eq:50-51`）⇒ **两类盲区须同时修**，否则该族 83 次漏检只能消 79 次。
2. **不可伪造属性**：`co_consts` 的**常量池身份**（下标 + 对象 `is` 身份）。`1` 与 `True` 即使 `==`，也是**不同对象**；常量池比较能分辨「同值不同对象」。
3. **不可伪造属性**：`type(argval)` 本身。`bool` 是 `int` 的子类是 Python 的类型系统事实；`repr` 不足以区分 `1` 与 `1.0`，**只有 `type` 能区分**。

**A3（归一化中性）**
1. **换 oracle**：把 `fix_unreachable` 换成「**只标记不可达、不删除**」，再比对 ⇒ handler 体差异立刻暴露（对照探针 `try_assign_handler_body` 已证明该差异在判据视野内）。
2. **不可伪造属性**：异常表的**区间**（start/end/target 原始三元组）。handler 是否可比由区间内是否有存活指令决定 ⇒ 区间本身是不伪造的语义事实。
3. **不可伪造属性**：`co_exceptiontable` 的**原始字节**（而非解析后的表）。判据应记录「归一化前后的异常表字节哈希」作为不可伪造指纹。

**A4（逐 code object 独立判定）**
1. **换 oracle**：**模块级装配差分**——把产物与源拼装为同一模块整体执行，比对模块级副作用序列（导入期副作用、类注册、装饰器应用顺序）。
2. **不可伪造属性**：`co_qualname`（层级路径，如 `outer.<locals>.inner`）。判据按 `name` 序列配对，**同名 code object 的配对是位置性的**；`co_qualname` 是唯一的层级锚。
3. **不可伪造属性**：`co_freevars` / `co_cellvars`（单元变量集合与顺序）。判据从不比较（`eq:80-99`）；它们是闭包/作用域语义的事实载体。

**A5（不执行）**
1. **换 oracle**：执行级差分（同 A1-1），并扩展到**副作用序列哈希**与**异常配对**（类型 + 消息 + `__exit__` 抑制语义）。
2. **不可伪造属性**：**运行轨迹**（副作用写入序列的哈希）——静态字节码**不可**推出。
3. **不可伪造属性**：异常**类型—消息—顺序**三元组；`with` 的 `__enter__`/`__exit__` 配对次数。

**A6（按 name 配对）**
1. **换 oracle**：按 `co_qualname`（而非 `name`）配对，再做配对一致性检查（同名多体时报告歧义而不是按序硬配）。
2. **不可伪造属性**：**嵌套深度**（`co_qualname` 的 `<locals>` 层数）与**兄弟顺序**（同名体在源中的出现序）。
3. **不可伪造属性**：`co_firstlineno` 的**相对序**（在同名体之间给出稳定的次序锚），比纯 `name` 序列更抗歧义。

### 3.3 共同原因的可观测后果（本轮读数）

| 共享假设 | 本轮可观测后果 |
|---|---|
| A1 | 判据最强的维度恰是产品最容易「凑形状」的维度（`code_generator.py:5001` 的 `!s` 发射即为一例）；产品在形状上做的每一处「保险」，都在降低判据的证伪能力 |
| A2 | `d_int_to_bool` 在**每一个作用域**（模块级 / 类级 / 闭包 / 装饰器）都是 ≈100% 漏检（§5.2）⇒ 盲区与作用域无关，是**比较算子**的性质 |
| A3 | 死代码族 53.90% 漏检、空 try 体 handler 族 100% 漏检 ⇒ 「判据的绿」对**产品自选的形态**（哪些块被发射）尤其不可靠 |
| A4 | 文件级「全或无」（`pyc_verify.py:129`）掩盖了单元级误绿 ⇒ 台账里「单元绿」这一读数**不可用于任何推断**（round5 B194 同域） |
| A5 | 六类执行级语义维度在现有判据体系内**不可证伪** ⇒ 转方法层（Task 9） |
| A6 | 34 个构造级探针里 `except_alias` / `closure_capture` 都靠**异名**改绑被抓 ⇒ 若产品把闭包改绑到**同名**变量，判据**结构性不可见**（探针缺口，非本轮变异族覆盖） |

---

## §4 变异测试实测（CLI 口径）

### 4.1 方法

- **判据调用**：`_scripts/mutate.py` 逐次拉起
  `python -X utf8 scripts/pyc_verify.py single <pyc> --source <变异产物>`（**只走 CLI**，不调内部 API）。
  「漏检」的定义严格是 CLI 打印的 `[single] status=success`；`status=failure` = 捕获；
  `status=compile_error` = 变异产物不可编译（INVALID，单列）；变异不适用 = NA（不计入分母）。
- **语料**：**记录在案**的绿产物 —— `.trae/specs/attain-true-completeness/rounds/round8/*report*.json`
  （402 语料八分片 + small34 + quotation 的 success 行）与 `rounds/round1/rec1_probes_*.json`
  （登记探针的 success 行）去重后 **422** 个。
  **本轮 CLI 口径取确定性子采样**（`--sample-mod 2`，即索引偶数项）**211** 个 ⇒ **207** 个当前仍为绿
  （4 个已漂移，见 §5.2）；分母只计**适用**的产物。
  （子采样的唯一原因是本机 2 核、CLI 单次判定 ≈1.35 s CPU，全语料 2468 次调用 ≈ 55 min；
  抽样口径为确定性，与 §4.5 的全语料 in-process 读数交叉核对。）
- **注入**：对**产物**（`OK.py`）注入已知语义错误（`_scripts/mutation_lib.py`，按 CPython `ast` 定位、
  按 UTF-8 字节偏移做**文本切片替换**，变异之外的字节原样保留）。
- **归因**：对每次漏检用 `_scripts/miss_attribution.py` 做四级归因（§2.4）。
- **原始记录**：`_out/mutate_results.jsonl`（作用域内逐次判定记录，2508 行）、
  `_out/mutate_parts/part_*.jsonl`（分片原始记录）、`_out/mutate_summary.json`（汇总）。

### 4.2 任务要求的 8 类（主表，CLI 实测）

见 §0.2 主表。要点与诚实读数：

- **(g) `g_rename_local` 的 15 次漏检不是判据盲区**：归因为 `OUT-OF-INSTRUCTION` 12（名字根本不在指令流里 ⇒
  改名**不改变任何可观察行为**）+ `NORMALIZED-AWAY` 3；对照族 **`g3_kwparam_rename`（保证语义：
  改「被以关键字实参调用」的形参名 ⇒ 调用必抛 TypeError）** 实测 **10/10 全部被抓（0 漏检）**
  （in-process 全语料 19/19 同样 0 漏检）⇒ **判据对语义确定的标识符改写有效**。
- **(d) `d_int_to_bool` 的 1 次「捕获」不是判据的有效性**：该例归因 `PIPELINE-DEFECT`（无条件跳转属性差异
  恰好使 CFG 出边集合不同）⇒ **判绿不是因为判据更严，而是因为差异恰好落在了另一条被比字段上**；
  换一批语料就会回到 100%（in-process 全语料 163/163 = 100%）。
- **(e) `e_str_content` 的唯一漏检**：`NORMALIZED-AWAY`（被 `fix_unreachable` 抹平），**不是字符串维度**的问题。
- **(h) `h_arg_swap` CLI 口径 0/141**：in-process 全语料口径为 1/283（同族唯一一例 `NORMALIZED-AWAY`），
  该例未落在本轮子采样内 ⇒ 两口径差异**只来自抽样**，不来自判据。

### 4.3 补测 3 族（CLI 实测）

见 §0.2 补测表。要点：

- `h_param_order`（**形参换序 = 调用约定改变**）：**159/162 漏检（98.15%）**，
  归因 **SLOT-INDEX-BLIND 149**（名字不变、槽位变 ⇒ `eq:47` 无 `arg` 字段）+
  `PIPELINE-DEFECT` 4 + `OUT-OF-INSTRUCTION` 3 + `NORMALIZED-AWAY` 3
  ⇒ **「槽位盲区是主因、不是唯一因」**。
- `j_func_docstring`（**函数 `__doc__` 语义**）：**108/108 漏检（100%）**，
  归因 `OUT-OF-INSTRUCTION` 81（函数 docstring 只在 `co_consts[0]`）+ `NORMALIZED-AWAY` 14
  + `SLOT-INDEX-BLIND` 9 + `PIPELINE-DEFECT` 4 ⇒ **函数 docstring 与模块/类 docstring 不对称**。
- `g3_kwparam_rename`（**保证语义对照**）：**10/10 全部被抓（0 漏检）**。

### 4.4 漏检归因（机制级，CLI 口径 366 次漏检逐条计算）

| 归因 | 次数 | 占比 | 机制 | 可改进性 |
|---|---|---|---|---|
| `COMPARATOR-BLIND` | **79** | 21.6% | `eq:59` 的 `==` 抹平值类型 | 改比较算子（类型敏感标签） |
| `SLOT-INDEX-BLIND` | **158** | 43.2% | `eq:47` 属性清单无 `arg` | 改比较算子（补 `arg`） |
| `OUT-OF-INSTRUCTION` | **96** | 26.2% | 差异不在指令流（`co_consts` / `co_varnames` / `co_flags` 等从不比较的维度） | 新增判据维度 |
| `NORMALIZED-AWAY` | **21** | 5.7% | `fix_unreachable` / `remove_nop` 删块 | 改归一化策略 |
| `PIPELINE-DEFECT` | **12** | 3.3% | `eq:50-51` 的早退分支跳过整组 `attr_list` + CFG 只比出边集合 ⇒ 两道防线同时失效 | 改比较算子（无条件跳转也须比整组 `attr_list`） |

逐族归因分布（**实测逐条**，原始记录见 `_out/mutate_miss_attribution.json`，366 条）：

> - `d_int_to_bool` 83 = **COMPARATOR-BLIND 79** + PIPELINE-DEFECT 4；
> - `h_param_order` 159 = **SLOT-INDEX-BLIND 149** + PIPELINE-DEFECT 4 + OUT-OF-INSTRUCTION 3 + NORMALIZED-AWAY 3；
> - `j_func_docstring` 108 = **OUT-OF-INSTRUCTION 81** + NORMALIZED-AWAY 14 + SLOT-INDEX-BLIND 9 + PIPELINE-DEFECT 4；
> - `g_rename_local` 15 = OUT-OF-INSTRUCTION 12 + NORMALIZED-AWAY 3（**均为语义惰性**）；
> - `e_str_content` 1 = NORMALIZED-AWAY 1。

> **`PIPELINE-DEFECT` 的精确定位**：`eq:50-51` 的早退分支对**无条件跳转**只比较 `argval`（目标偏移），
> **跳过整组 `attr_list`**（`opname`/`opcode`/`optype`/`real_size`/`has_arg`/
> `has_extended_arg`/`offset`/`is_jump_target`）；同时 CFG 比较只看**出边目标集合**（同目标 ⇒ 同边集）
> ⇒ **指令比较与 CFG 比较双向失守**。三档复核（抹平 opname/opcode → 抹平整组 attr_list → 仍不同）
> 在本轮 CLI 口径下仍为「仍不同 **0** 例」⇒ **不存在独立的「管线缺陷」，全部归 `eq:50-51`**。

### 4.5 与同轮 in-process 全语料读数的交叉核对

| 族 | **CLI 口径（本轮，207 绿产物）** | in-process 全语料（同轮，416 绿产物） | 一致性 |
|---|---|---|---|
| `a_num_int` | 0/112（0.00%） | 0/222（0.00%） | ✔ |
| `b_cmp_polarity` | 0/78（0.00%） | 0/148（0.00%） | ✔ |
| `c_del_assign` | 0/176（0.00%） | 0/347（0.00%） | ✔ |
| `d_int_to_bool` | **83/84（98.81%）** | **163/163（100%）** | ✔（差异 = 1 例被 `PIPELINE-DEFECT` 偶然抓住） |
| `e_str_content` | 1/166（0.60%） | 1/334（0.30%） | ✔（**同一例** `IQEngine/utils/profiler_func.pyc`） |
| `f_stmt_swap` | 0/107（0.00%） | 0/213（0.00%） | ✔ |
| `g_rename_local` | 15/167（8.98%） | 34/336（10.12%） | ✔（比例一致） |
| `h_arg_swap` | 0/141（0.00%） | 1/283（0.35%） | ✔（唯一漏检未落在子采样内） |
| **8 类合计** | **99/1031（9.60%）** | **199/2046（9.73%）** | ✔ |
| `h_param_order` | 159/162（98.15%） | 306/306（100%） | ✔ |
| `j_func_docstring` | 108/108（100%） | 216/216（100%） | ✔ |
| `g3_kwparam_rename` | 0/10（0%） | 0/19（0%） | ✔ |

⇒ **两条独立路径（CLI 子进程 vs 内部 API、抽样 vs 全语料）给出同一结论**：
判据对**值类型 / 槽位次序 / 函数 docstring** 三族结构性失明，对**语法形态**族几乎不失明。

### 4.6 可复现命令

```powershell
# 0) 单族重跑（例：值类型族；只走 CLI 判定）
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round4/_scripts/mutate.py `
  --shard 0 --nshards 48 --sample-mod 2 --families d_int_to_bool --keep-misses
# 1) 汇总（mutated / missed / miss-rate + 落盘作用域内原始记录）
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round4/_scripts/mutate.py --summary --scope-mod 2
# 2) 漏检归因（COMPARATOR-BLIND / SLOT-INDEX-BLIND / OUT-OF-INSTRUCTION / NORMALIZED-AWAY / PIPELINE-DEFECT）
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round4/_scripts/miss_attribution.py `
  --jsonl .trae/specs/attack-completeness-claims/rounds/round4/_out/mutate_results.jsonl `
  --json   .trae/specs/attack-completeness-claims/rounds/round4/_out/mutate_miss_attribution.json
# 3) 独立复跑（14 例，只用约定 CLI 命令）
python -X utf8 .trae/specs/attack-completeness-claims/rounds/round4/_scripts/mutate_recheck.py
# 4) 单例判定（约定形式）
python -X utf8 scripts/pyc_verify.py single <pyc> --source <product>
```

> 判定用**单条命令**复核任一漏检样例（产物 = `_probes/miss_cli/miss_<md5>_<family>.py`）：
> ```powershell
> python -X utf8 scripts/pyc_verify.py single site-packages\IQCommon\api\check_strategy.pyc `
>   --source .trae\specs\attack-completeness-claims\rounds\round4\_probes\miss_cli\miss_<md5>_d_int_to_bool.py
> ```
> 变异点可用
> `python -X utf8 .trae/specs/attack-completeness-claims/rounds/round4/_scripts/mutation_lib.py <product.py> <family>`
> 直接打印。
>
> **留存规则（如实披露）**：`_probes/miss_cli/` 留存 **13 个**漏检变异产物
> （`d_int_to_bool` 3、`h_param_order` 3、`j_func_docstring` 3、`g_rename_local` 3、`e_str_content` 1；
> 由 `_scripts/mutate_keep_samples.py` 从 `_out/mutate_results.jsonl` 逐族确定性选出并**重建**）；
> 其余 353 条漏检的原始判定记录（pyc / 族 / status / units / 变异点）完整保留在
> `_out/mutate_results.jsonl` 与 `_out/mutate_parts/part_*.jsonl`；
> 样本文件名 = `md5(pyc|family)[:16]` + 族名 ⇒ **任一漏检可由 `(pyc, family)` 确定性重建**。
>
> **留存样本的当场复核**（约定 CLI 命令，实测）：
> ```powershell
> python -X utf8 scripts/pyc_verify.py single site-packages\IQCommon\api\check_strategy.pyc `
>   --source .trae\specs\attack-completeness-claims\rounds\round4\_probes\miss_cli\miss_1f2df9cc817c219f_h_param_order.py
> # => [single] status=success units=2/2        （h_param_order 漏检，复现）
> python -X utf8 scripts/pyc_verify.py single site-packages\IQCommon\api\klinedata.pyc `
>   --source .trae\specs\attack-completeness-claims\rounds\round4\_probes\miss_cli\miss_2495581cdd020277_j_func_docstring.py
> # => [single] status=success units=64/64      （j_func_docstring 漏检，复现）
> python -X utf8 scripts/pyc_verify.py single site-packages\IQEngine\utils\profiler_func.pyc `
>   --source .trae\specs\attack-completeness-claims\rounds\round4\_probes\miss_cli\miss_b3f71f6064f467a8_e_str_content.py
> # => [single] status=success units=18/18      （e_str_content 漏检，复现）
> ```

### 4.7 独立复跑（`_scripts/mutate_recheck.py`；**不复用已落盘汇总读数**）

对每族各取一例（MISS 期望与 CAUGHT 对照），**从产物重新注入**同一语义错误后执行约定 CLI 命令：

| 族 | 期望 | 实测 | CLI 输出 | 一致 |
|---|---|---|---|---|
| `d_int_to_bool` | MISS | MISS | `status=success units=2/2` | ✔ |
| `d_int_to_bool` | MISS | MISS | `status=success units=2/2` | ✔ |
| `d_int_to_bool` | CAUGHT | CAUGHT | `status=failure units=8/9` | ✔ |
| `j_func_docstring` | MISS | MISS | `status=success units=2/2` | ✔ |
| `h_param_order` | MISS | MISS | `status=success units=4/4` | ✔ |
| `h_param_order` | CAUGHT | CAUGHT | `status=failure units=8/9` | ✔ |
| `e_str_content` | MISS | MISS | `status=success units=18/18` | ✔ |
| `g_rename_local` | MISS | MISS | `status=success units=4/4` | ✔ |
| `g3_kwparam_rename` | CAUGHT | CAUGHT | `status=failure units=62/64` | ✔ |
| `a_num_int` | CAUGHT | CAUGHT | `status=failure units=1/2` | ✔ |
| `b_cmp_polarity` | CAUGHT | CAUGHT | `status=failure units=3/4` | ✔ |
| `c_del_assign` | CAUGHT | CAUGHT | `status=failure units=3/4` | ✔ |
| `f_stmt_swap` | CAUGHT | CAUGHT | `status=failure units=1/2` | ✔ |
| `h_arg_swap` | CAUGHT | CAUGHT | `status=failure units=1/2` | ✔ |

⇒ **14 例：14/14 期望一致（6 MISS + 8 CAUGHT）**；E1/E2/E3 在独立复跑下同样成立。

### 4.8 运行事故与覆盖完整性（如实披露）

1. **判据读数零事故**：CLI 口径 1311 次变异判定全部返回 `status`（无 `TIMEOUT` / `NO_STATUS` /
   `JUDGE_ERROR`）；`invalid=0`、`judge_error=0`（见 `_out/mutate_summary.json` 逐族列）。
2. **子采样范围**：CLI 口径语料 = 记录在案的 422 个绿产物中**索引偶数的 211 个**（确定性）。
   理由：本机 2 核、CLI 单次判定 ≈1.35 s CPU（并发 6–8 路实测 ≈0.9–1.0 次/秒），
   全语料 2468 次调用 ≈55 min；抽样口径与 §4.5 的全语料 in-process 读数交叉核对一致。
3. **子采样内覆盖完整性**：211 个产物的 8 个族**全部有记录**（适用 ⇒ 判定；不适用 ⇒ NA），
   **0 个缺口**；4 个产物因**当前非绿**被剔除（§5.2）。
4. **归因作业耗时**：366 条漏检的归因超过单命令 300 s 门限，改用后台作业完成
   （`_out/mutate_attrib.txt` / `_out/mutate_attrib_warnings.txt` 保留告警原文；
   归因结果为**全量 366 条**，无抽样）。

---

## §5 覆盖缺口：跨函数 / 模块级 / 类级 / 闭包 / 装饰器装配，以及「绿」清单的时效性

### 5.1 判据在装配层的**结构事实**

- 判据**逐 code object 独立判定**（`eq:199`），文件级状态是「全或无」（`pyc_verify.py:129`）。
  ⇒ **装配语义（谁调用谁、模块级副作用次序、类级装饰器链、闭包单元绑定）不在任何独立维度被判定**；
  它只是**偶然**被「每个 code object 各自的指令流」覆盖。
- 判据**不比较** `co_qualname` / `co_freevars` / `co_cellvars` / `co_flags` / `co_names` / `co_consts`
  （`eq:80-99`）⇒ 这些**装配事实**在判据内**没有载体**。
- 判据按 **name 序列**配对 code object（`eq:158`）⇒ 同名 code object 的配对是位置性的。

### 5.2 量化（`_out/coverage_scope.json` / 本轮 CLI 读数）

语料装配特征分布（in-process 全语料口径）：`multi_func 317`、`module_stmt 214`、`class_level 231`、
`closure 18`、`decorator 159`、**多 code object（>1）348 / 416**。

| 作用域 | 产物数 | 8 族 mutated | missed | miss-rate |
|---|---|---|---|---|
| 全体 | 416 | 2046 | 199 | **9.73%** |
| 含多函数 | 317 | 1837 | 184 | 10.02% |
| 含模块级语句 | 214 | 1154 | 121 | 10.49% |
| 含类定义 | 231 | 1283 | 127 | 9.90% |
| 含闭包捕获 | 18 | 140 | 18 | 12.86% |
| 含装饰器 | 159 | 994 | 97 | 9.76% |

逐族 × 作用域（8 族主表，in-process 口径）：

| 族 | 全体 | 多函数 | 模块级 | 类级 | 闭包 | 装饰器 |
|---|---|---|---|---|---|---|
| `a_num_int` | 0/222 | 0/200 | 0/138 | 0/132 | 0/17 | 0/113 |
| `b_cmp_polarity` | 0/148 | 0/145 | 0/87 | 0/91 | 0/17 | 0/85 |
| `c_del_assign` | 0/347 | 0/298 | 0/189 | 0/217 | 0/18 | 0/154 |
| **`d_int_to_bool`** | **163/163** | **149/149** | **111/111** | **96/96** | **17/17** | **86/86** |
| `e_str_content` | 1/334 | 1/284 | 1/187 | 1/207 | 1/18 | 1/149 |
| `f_stmt_swap` | 0/213 | 0/184 | 0/133 | 0/134 | 0/17 | 0/103 |
| `g_rename_local` | 34/336 | 33/315 | 9/163 | 30/226 | 0/18 | 10/159 |
| `h_arg_swap` | 1/283 | 1/262 | 0/146 | 0/180 | 0/18 | 0/145 |

### 5.3 「已判绿」清单的时效性（本轮新发现，AT-37）

记录在案的绿产物**不是稳定前提**。本轮对抽样的 211 个「记录在案 success」产物复核基线，
其中 **4 个当前已判红**（用约定 CLI 命令逐个复核）：

| 产物 | 当前 CLI 读数 |
|---|---|
| `test_repros/round7/r7_01_ternary_args_index.pyc` | `status=failure units=8/9` |
| `test_repros/round8/rv8_02_with_tryfin_constret.pyc` | `status=failure units=6/7` |
| `test_repros/round2/c02_class_if.pyc` | `status=failure units=6/7` |
| `test_repros/round9/n9v9_stmt_sweep.pyc` | `status=failure units=5/6` |

⇒ **漂移率 4/211 = 1.90%**（in-process 全语料口径同口径为 6/422 = 1.42%）。
后果：任何「在绿产物上做的回归」**若不复核基线**，其分母是**过期的**；
「绿产物数量」本身是**随时间变化**的量，不能当作稳定基线引用。

### 5.4 结论（覆盖缺口的性质）

1. **漏检率与作用域基本无关**（9.73% ~ 12.86%）：`d_int_to_bool` 在**每个**作用域都是 ≈100%。
   ⇒ 覆盖缺口**不是**「某个作用域忘了覆盖」，而是「**装配只被指令流偶然覆盖**」：
   判据对装配层**没有独立维度**，其覆盖度完全等于「指令流恰好编码了该语义」的比例。
2. **装配层的真实缺口清单**（判据内**无载体**的装配事实）：
   - `co_qualname` 层级（嵌套函数的归属路径）——同名 code object 配对歧义；
   - `co_freevars` / `co_cellvars`（闭包单元绑定）——**同名**改绑不可分辨；
   - `co_flags`（生成器 / 协程 / 位置限定符等）——从不比较；
   - 模块级**求值次序**与类级**装饰器链的应用次序**——只在指令流层面偶然覆盖，
     **运行期**次序（跨模块、跨类）不可判定；
   - `__doc__`（函数级）、`__annotations__`（`from __future__ import annotations` 下）等**元数据**。
3. **装配层的探针读数**（构造级）：`cross_function_call`（改调用目标）CAUGHT、
   `module_const_used` CAUGHT、`class_attr` CAUGHT、`closure_capture` CAUGHT、`decorator_order` CAUGHT
   ⇒ **在「指令流可编码」的装配语义上，判据是有效的**；缺口集中在**指令流编码不到**的装配事实。

---

## §6 与 F1 / B163、round5 `o4b` / B194 的关系

### 6.1 与 round1 F1 / 破口 B163（行级证据—形态错配）

| 维度 | F1 / B163（round1，L1/L5） | 本轮（L2） | 关系 |
|---|---|---|---|
| 断言对象 | 「25 行终表中 `global_nonlocal` 行判**完备**」 | 「判定器对 `global`/`nonlocal` 形态的**判别力**」 | **互补且相乘** |
| 缺陷 | 行登记的探针 `x04_try_deep_hosts.py` **不含** `nonlocal`；真 nonlocal 探针未进任何 stamp ⇒ **该行的完备结论无形态级证据** | 即便注入 `global` 声明（`w_global_stmt` 族，294 次变异），仍有 **28 次漏检（9.52%）**；`global`/`nonlocal` **声明本身不产生指令**，只改名字的解析方式 ⇒ **同名**改绑不可分辨 | **乘性**：B163 说「没被验证过」，本轮说「验证了也未必抓得住」。**只修 B163（补证据）不足以让该行变绿**；必须同时修判据 |
| 修法 | 补形态级探针并进覆盖检查器（Task 10） | 补「作用域绑定」判据维度（§8 R4） | 两者都要做 |

### 6.2 与 round5 `o4b` / 破口 B194（单元粒度误绿）

round5 的结论（`rounds/round5/ATTACK_L3_MECHANISM.md:42,136`）：
「判定器在**函数 code object** 上判 **Equal**（失败只落在嵌套 `<listcomp>` code object 上），
而执行级差分为 **DIFFERENT**」⇒ **单元粒度**上「绿 ⇒ 语义等价」不成立 ⇒ **B194**。

| 方面 | round5 `o4b` / B194 | 本轮（L2） |
|---|---|---|
| 证的是什么 | **哪个单元**绿错了（函数级绿、嵌套级红） | **该绿的单元为何**绿错：五类可分离的失明机制（值类型 `eq:59` / 槽位下标 `eq:47` / 元数据 `co_consts` / 归一化删块 `eq:194-195` / 无条件跳转早退 `eq:50-51`） |
| 层次 | L3 机制层（机制族 × 叠加） | L2 判定层（判据本体） |
| 是否同根因 | **否**。B194 = 「单元粒度的读数被误用」；本轮 = 「判据在单元内部对某些语义维度结构性失明」 | 两者可**同时成立**：一个单元可以既绿错（因为失明）又绿错（因为粒度） |
| 量化 | 48 单元中 23 单元执行级 DIFFERENT | CLI：207 绿产物 / 8 族 1031 变异 / **99 漏检（9.60%）**；补测 3 族 280 变异 / 267 漏检（95.36%）；2 族 ≈100%。in-process 全语料：416 产物 / 2046 变异 / 199 漏检（9.73%）、补测 20 族 2632 变异 / 1020 漏检（38.75%） |
| 可否互相解释 | `o4b` 的 `<listcomp>` 差异是**产品**的机制缺陷（round5 H7 / B151） | 本轮给出**判据侧**的平行说明：若产品丢的是**比较项的常量**（1 → True）或**形参次序**，判据同样看不见 ⇒ **判据与产品两类缺陷在判据内不可区分** |
| 对「完备」结论的影响 | 单元级「绿」不可外推 | **文件级「全或无」（`pyc_verify.py:129`）也不可外推**：文件级绿只说明「每个 code object 的指令流（含被归一化后的）相同」，**不说明语义相同** |

⇒ **共同结论（应写入 v9 台账）**：**「绿」的读数强度必须按判据面分层标注**：
「控制流/结构绿」≠「值语义绿」≠「可执行语义绿」。本规范 v9 的双读数（形态基线 / 判定空间）
**还须补第三列：判据强度分层**（§8 R7）。

---

## §7 新破口登记（自 **B195** 起；不复用 B163–B194）

> 归属层除注明外均为 **L2 判定层**；状态：开放。全部可在 §4 的脚本上复现。

| 编号 | 根因 | 表现（最小复现 / 读数） | 归属层 | 判定空间条目 | 状态 |
|---|---|---|---|---|---|
| **B195** | **归一化抹平：`fix_unreachable` 删除「异常表区间内无存活指令」的 except handler 块** ⇒ handler 语义结构性不可见 | `try: pass except ValueError: return 1` → `return 2` **判绿**；`except (A,B)` → `except (B,A)` **判绿**；`except ValueError` → `except ValueError_MUT` **判绿**。对照：`try: x = 1` / `try: raise E()` 同一变异**判红** | L2（判据） | JS-TRY-*/JS-EXCEPT-* | 开放 |
| **B196** | **无条件跳转只比 argval（目标偏移），即跳过整组 `attr_list`** ⇒ 该指令的 `opname`/`opcode`/`is_jump_target`/`real_size` 等**全部不可见**；且 CFG 只比**出边目标集合**，边类型同权 ⇒ 两道防线同时失效 | **12 例**（本轮 CLI 归因）落在 `PIPELINE-DEFECT`：`d_int_to_bool` 4 + `h_param_order` 4 + `j_func_docstring` 4；三档复核（抹平 opname/opcode → 抹平整组 attr_list → 仍不同）仍不同 **0** 例 ⇒ **无独立「管线缺陷」，全部归 `eq:50-51`** | L2（判据） | JS-JUMP-* | 开放 |
| **B197** | **指令属性清单缺 `arg`（槽位下标）** ⇒ 形参换序（名字不变、槽位变）不可见 ⇒ **调用约定改变近乎 100% 漏检** | CLI `h_param_order`：**159/162 漏检**（SLOT-INDEX-BLIND 149）；in-process 全语料：**306/306 漏检** | L2（判据） | JS-FUNC-*（形参面） | 开放 |
| **B198** | **常量比较用 Python `==`** ⇒ `1`/`True`/`1.0` 互判相等 ⇒ **值的类型**结构性不可分辨 | CLI `d_int_to_bool`：**83/84 漏检**（COMPARATOR-BLIND 79 + PIPELINE-DEFECT 4）；in-process 全语料 `i_int_to_float`：**222/222 漏检** | L2（判据） | JS-CONST-* | 开放 |
| **B199** | **函数 docstring 只在 `co_consts[0]`，从不进指令流** ⇒ 函数 `__doc__` 语义不可见（**与模块/类 docstring 不对称**：后两者经 `STORE_NAME __doc__` 进指令流） | CLI `j_func_docstring`：**108/108 漏检**（OUT-OF-INSTRUCTION 81 + NORMALIZED-AWAY 14 + SLOT-INDEX-BLIND 9 + PIPELINE-DEFECT 4）；in-process 全语料：**216/216 漏检** | L2（判据） | JS-DOC-* | 开放 |
| **B200** | **判据与产品共享目标函数（「形状相同 ⇒ 语义等价」）** ⇒ 共同原因失败不可排除；判据**不能**证伪产品在这条回路上的形态选择 | `core/cfg/region_ast_generator.py:7755`、`:14244`、`:21750` 直接以 `pyc_verify` / `pylingual is_control_flow_equivalent` 的判红为规则理由；`core/cfg/code_generator.py:5001`「必须显式输出 `!s` 以保证字节码等价」；实测 `core/cfg/*.py`：「字节(码)等价」**23** 处、「判据」**1435** 处、点名判据工具 **3** 处 | L2 + L5 | JS-全局（判据独立性） | 开放 |
| **B201** | **「已判绿」清单不是稳定前提**：记录在案的 success 行**会随时间失效**（产物被重生成 / 尺子换版 / 判据变更），而台账与回归直接把它当稳定基线 | 211 个抽样「记录在案绿」产物中 **4 个（1.90%）当前已判红**（`r7_01_ternary_args_index` 8/9、`rv8_02_with_tryfin_constret` 6/7、`c02_class_if` 6/7、`n9v9_stmt_sweep` 5/6；in-process 全语料同口径 6/422 = 1.42%） | L2 + L5（证据层） | JS-全局（基线时效性） | 开放 |

**不新立编号、但须并入既有台账口径的两项**（避免与既有 B 号重复）：

| 项 | 处置 |
|---|---|
| 「判据自检（`pyc_verify.py selfcheck`）只覆盖常量与极性两类变异 ⇒『判据可用』的覆盖面被高估」 | 并入 **B200** 的表现列（自检独立性不足是共同原因的另一个侧面） |
| 「文件级『全或无』（`pyc_verify.py:129`）掩盖单元级误绿 ⇒ 单元/文件两级『绿』都不可外推」 | 并入 **B194** 的口径扩展（round5 已立 B194；本轮补「文件级亦不可外推」的读数与量化） |

---

## §8 判据增强需求

| R | 检查项 | 层次 | oracle | 成本 |
|---|---|---|---|---|
| **R1** | **类型敏感常量比较**：`LOAD_CONST` 的 argval 改用 `(type(v), repr(v))` 标签；并补比 `co_consts` 常量池身份 | 判据本体（`eq:56-66`） | 静态、无需执行 | 低（改一处比较函数 + 一处常量池比较）；可把 `d_int_to_bool` 79 次 `COMPARATOR-BLIND` 漏检转成判红（归因器已验证） |
| **R2** | **补比 `arg`（槽位下标）** 与 `co_flags` / `co_freevars` / `co_cellvars` | 判据本体（`eq:47`、`:80-99`） | 静态 | 低；可把 `h_param_order` 149 次 `SLOT-INDEX-BLIND` 漏检转成判红 |
| **R3** | **归一化策略改为「不删块」**：`fix_unreachable` 改为只标记不可达；或至少**保留 handler 块**（异常表区间内的 handler 必须保留，即使 try 体为空） | 判据本体（`eq:194-195` + `EditableBytecode.py:440-447`） | 静态 | 中（需改附件 patch 链；本仓 `scripts/pyc_verify.py` 只做装载，改动落在**仓外附件** ⇒ 须先解决「尺子在仓外」问题，见 R8） |
| **R4** | **无条件跳转也须比整组 `attr_list`**（不只 opname/opcode，还要含 `is_jump_target`/`real_size`），且 CFG 比较须区分**边类型**（EXCEPTION 边 vs 普通边） | 判据本体（`eq:50-51`、`:28-40`） | 静态 | 低-中；可把 B196 的 **12 例**转成判红（§4.4 三档复核已定位机制） |
| **R5** | **新增「作用域/元数据」判据维度**：函数 docstring（`co_consts[0]`）、局部注解、`__annotations__`、`__qualname__` | 判据本体 | 静态 | 中；新增一组「code object 元数据」比较（docstring 取 `co_consts[0]` 的 str） |
| **R6** | **新增「装配级」判据**：按 `co_qualname` 配对 code object（替代纯 name 序列），并对同名多体报告歧义；跨 code object 的引用关系（`LOAD_GLOBAL`/`LOAD_METHOD` 的目标是否在本文件定义）单独成维度 | 判据本体 | 静态 | 中；直接对应 §5 的装配缺口 |
| **R7** | **执行级语义差分**（返回值 / 全局与属性写入 / 副作用**序列** / 异常类型与消息 / `__enter__`·`__exit__` 配对次数 / 生成器 `send`·`throw` / async 调度） | **新增层次**（在静态判据之上） | 执行（沙箱，同输入序列） | 高（需沙箱 + 受控输入集 + 容差声明）；round5 的 `tools/l3_semdiff.py` 已是可运行原型，应提升为 `tools/completeness/semantic_diff.py`（Task 9）并进 E 门禁 |
| **R8** | **把判据本体纳入仓内**（或至少纳入仓内可审计副本 + 固定 sha256 全长），并把「换尺子」纳入门禁项 | 工具链 | 静态 | 中；否则 R1–R6 的修复无法在本仓落地与回归 |
| **R9** | **判据自检扩容**：内建变异从 2 类扩到 **≥8 类**（值类型、形参换序、handler 体、docstring、异常元组序、注解、死代码、global 绑定），并要求 **漏检 = 0** 才判「判据可用」 | 门禁（`pyc_verify.py:284-320`） | 静态 | 低-中（复用 `_scripts/mutation_lib.py` 与 `_scripts/mutate.py`）；这是把「尺子可信」变成**可机检**命题的最小改动 |
| **R10** | **「绿」的读数分层标注**：任何引用「绿」的台账条目须同时标注**判据面**（控制流/结构 / 值语义 / 槽位与元数据 / 可执行语义）与**归一化状态**（是否经过 `fix_unreachable` 等删块归一化） | 台账/口径（`wiki` §6、`rules.md` §8） | 口径 | 低；本轮 §2.2 的盲区表可直接作为标注词表 |
| **R11** | **变异测试常驻门禁**：把 §4 的 8 族（+ 补测族）作为门禁项，**漏检率读数**与**归因分布**同时上报（不只看漏检数，还要看漏检落在哪一类机制） | 门禁 | 静态 | 中（脚本已就位：`_scripts/mutate.py` / `mutate_recheck.py` / `miss_attribution.py`）；**CI 建议用 in-process 后端**跑全语料，CLI 后端作抽样复核 |
| **R12** | **基线时效性门禁**：任何「在绿产物上做」的回归，**必须先复核基线**（本轮漂移率 1.90%），并在报告里记录「基线复核时刻 + 判据 sha256」；漂移产物单列，不静默纳入/剔除 | 门禁/口径 | 静态 | 低；`_scripts/mutate.py` 的 BASELINE 记录已带 `provenance`，可直接扩展为门禁项 |

**最小可用落地顺序建议**：R1 → R2 → R4（纯比较算子改动，成本最低、收益最大，
可一次性消掉 `d_int_to_bool` / `h_param_order` / B196 三类漏检）→
R3（归一化，消掉 B195 与死代码族）→ R9 + R12（自检扩容 + 基线时效性，把上述变成常驻门禁）→
R7（执行级差分，唯一能覆盖 AT-31「不可证伪」项的路径）→ R5/R6/R8/R10/R11（维度与口径）。

---

## 附录 A：本轮产物清单（`rounds/round4/`）

| 路径 | 内容 |
|---|---|
| `ATTACK_L2_JUDGE.md` | 本报告 |
| `_scripts/mutate.py` | **任务要求的变异脚本**：取已判绿产物 → 注入 8 类语义错误 → 逐次跑 `python -X utf8 scripts/pyc_verify.py single <pyc> --source <产物>` → 统计每类漏检数与漏检率（支持分片/续跑/子采样/汇总） |
| `_scripts/mutate_recheck.py` | **独立复跑**（14 例，只用约定 CLI 命令；`_out/mutate_recheck.json`） |
| `_scripts/mutate_keep_samples.py` | **漏检样本重建**（按留存规则从逐次记录确定性选出并重建变异体；`_probes/miss_cli/`） |
| `_scripts/mutation_lib.py` | 28 个语义变异族（含 8 类任务要求族 + 保证语义族） |
| `_scripts/mutation_experiment.py` / `mutation_experiment2.py` | in-process 全语料变异驱动器（语料 = 记录在案的绿产物；可分片续跑） |
| `_scripts/mutation_summary.py` | in-process 口径按族汇总 mutated / missed / miss-rate |
| `_scripts/miss_attribution.py` / `miss_inspect.py` | 漏检五级归因器（判据看得见的部分 vs 看不见的部分） |
| `_scripts/normalization_evidence.py` | 归一化/比较算子归因（单对 A/B 打印 RAW / NORM / VIS 三层） |
| `_scripts/pipeline_defect_recheck.py` / `pipeline_defect_detail.py` | `PIPELINE-DEFECT` 二档/三档复核 + 残留差异的逐指令坐标定位 |
| `_scripts/coverage_scope.py` | 跨函数/模块级/类级/闭包/装饰器交叉量化 |
| `_scripts/construct_probe.py` | 34 个构造级语义维度探针（写探针 → pycdc → 判定 → 注入 → 判定） |
| `_scripts/judge_sig.py` / `judge_diff_probe.py` / `judge_micro_probe.py` | 判据可见性指纹（类型敏感 argval）与微探针 |
| `_scripts/green_form_scan.py` | 「绿产物」形态扫描（判绿语料的基本形态构成） |
| `_scripts/verify_l2_readings.py` | 关键读数独立复跑（CLI `single` 子进程；12 例） |
| `_scripts/prune_artifacts.py` | 证据目录整理（漏检样本抽样留存 + 中间分片清理） |
| `_out/mutate_results.jsonl` | **CLI 口径**作用域内逐次判定原始记录（2508 行；207 绿产物 × 8 必需族 + 3 补测族 + 基线） |
| `_out/mutate_parts/part_*.jsonl` / `meta_*.json` | CLI 口径分片原始记录与分片参数（含 `sample_mod`） |
| `_out/mutate_summary.json` | CLI 口径汇总读数（逐族 mutated/missed/miss-rate + 判据 sha256 + 作用域参数） |
| `_out/mutate_miss_attribution.json` | CLI 口径逐次漏检归因（**366 条全量**，五类机制） |
| `_out/mutate_recheck.json` | 独立复跑读数（14 例：14/14 一致） |
| `_out/mutate_attrib.txt` / `mutate_attrib_warnings.txt` | CLI 口径归因作业日志与告警原文 |
| `_out/mutation_results.jsonl` / `mutation_summary.json` | in-process 全语料口径逐次记录与汇总（416 绿产物 / 8 族 2046 变异） |
| `_out/mutation_results_extra.jsonl` / `mutation_summary_extra.json` | in-process 补测 20 族记录与汇总（2632 变异 / 1020 漏检） |
| `_out/miss_attribution.json` / `miss_attribution_extra.json` | in-process 逐次漏检归因（199 / 1020 条） |
| `_out/coverage_scope.json` / `construct_probe.json` / `verify_l2_readings.json` | 作用域交叉 / 34 探针 / 12 例复跑读数 |
| `_out/miss_samples.json` / `run_notes.json` | 漏检样本留存规则 / 运行注记 |
| `_out/pipeline_defect_recheck.txt` / `pipeline_defect_detail.json` / `pipeline_defect_detail.txt` | `PIPELINE-DEFECT` 复核读数与逐指令残留差异坐标 |
| `_probes/cp_*` | 34 个构造级探针的 `.py` / `.pyc` / `OK.py`（`.pyc` 被 `.gitignore` 排除） |
| `_probes/mut/cp_*_mut.py` | 34 个探针的**变异产物**（漏检样例可逐条复现） |
| `_probes/miss/miss_*` | 抽样留存的漏检变异产物（in-process 口径，29 个；规则见 `_out/miss_samples.json`） |
| `_probes/miss_cli/miss_*` | **CLI 口径**留存的漏检变异产物（13 个：d_int_to_bool 3、h_param_order 3、j_func_docstring 3、g_rename_local 3、e_str_content 1） |

## 附录 B：口径与纪律声明

1. **本轮只测不修**：`core/cfg/**`、`scripts/pyc_verify.py`、`tests/**`、`wiki/**`、`rules.md`、
   其它规范目录**零改动**；产出全部落在 `rounds/round4/**`。
2. **不 push**；提交前缀 `rr-v4r04:`。
3. **判据调用形式**：本轮 CLI 口径读数**全部**由
   `python -X utf8 scripts/pyc_verify.py single <pyc> --source <变异产物>` 产生；
   「漏检」的定义严格是 CLI 打印的 `[single] status=success`。
4. **所有数字均可复算**：`_out/mutate_results.jsonl`（CLI 口径作用域内）与
   `_out/mutation_results*.jsonl`（in-process 全语料）是逐次判定的原始记录，汇总脚本只做计数。
5. **判据本体在仓外**（`D:\Desktop\ptrade相关\pylingual`，sha256 前 16 位 `9c7567bd6776b36b`）：
   本报告对该附件的 file:line 引用**逐条复核过**（§2.1、§2.4），
   但**仓内无法独立复算判据** ⇒ R8 记录了这一结构性缺口。
6. **诚实性**：本轮同时给出判据的**强项读数**（删语句/极性/语句序/实参序/异常类型/装饰器序/
   match/with/del/assert/跨函数调用/模块级常量/类属性 全部 100% 抓到）、
   **语义惰性变异**的排除论证（(g) 族的 15 次漏检经归因全部非判据盲区，
   且保证语义对照组 `g3_kwparam_rename` 10/10 被抓），
   以及**子采样与全语料两条口径的交叉核对**（§4.5）。
   击穿结论只建立在**保证语义**的变异族与**归因器**的机制分类上。
7. **未核实项**：附件 `pylingual` 的其余模块（`control_flow_reconstruction/cfg.py` 等）本轮只读到
   与判据路径直接相关的部分；`EditableBytecode.remove_instructions` 的偏移修正细节未逐行复核。
8. **独立复跑**：§4.7 的 14 例已用 `_scripts/mutate_recheck.py` 以**约定命令形式**独立重做一次
   ⇒ **14/14 期望一致**（6 MISS / 8 CAUGHT），**不复用已落盘的汇总读数**。
9. **子采样与运行事故（如实披露）**：CLI 口径语料为 422 个记录在案绿产物中**确定性子采样的 211 个**
   （索引偶数项），原因与代价见 §4.8；抽样内 8 个族**0 缺口**；
   归因作业因超 300 s 门限改为后台完成（结果为 366 条全量）。
   4 个「记录在案绿」产物当前已判红（漂移 1.90%）⇒ 单列为 B201，不静默剔除。
