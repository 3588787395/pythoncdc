# 判定器判据清单与已知盲区（`scripts/pyc_verify.py` 及其委托判据）

> 目的：为 L2 判定层攻击提供**可证伪的判据面**——先说清「绿」到底比了什么、没比什么，后面的变异测试与差分才有靶子。
> 取证方式：只读读码 + 本机实测附件存在性/哈希；不执行任何判定（避免污染基线）。

---

## 0. 判据链拓扑（先决事实：`pyc_verify.py` 不是判据本体）

| 事实 | 源 | 影响 |
|---|---|---|
| `scripts/pyc_verify.py` 只做「装载、配对、报告」，判定本体在**附件仓库** `pylingual/equivalence_check.py::compare_pyc` | `scripts/pyc_verify.py:3-8`（模块 docstring 原文：「判据本身不在这里实现……逐条判定由附件 pylingual 的 `pylingual/equivalence_check.py::compare_pyc` 执行」）、`:47-68` | 判据**不在本仓** ⇒ 仓内不可审计 |
| 附件默认根 = `D:\Desktop\ptrade相关\pylingual`（可用 `--pylingual` 改） | `scripts/pyc_verify.py:40`、`:354` | 换一份附件即换一把尺子 |
| 附件通过 `sys.path.insert(0, root)` 注入 | `scripts/pyc_verify.py:53` | 判据与产品共用同一 Python 环境与同一 `networkx` 依赖 |
| 仓内只以 sha256 前 16 位锚定尺子 | `scripts/pyc_verify.py:79-83`（`ruler_stamp`）、`:221`（报告头写入 `ruler`） | 锚定强度弱（16 hex），且文件在仓外 ⇒ **共同原因失败与「换尺子」风险均在 L2 攻击面内** |
| **本机实测**：附件存在，`pylingual/equivalence_check.py` sha256 = `9c7567bd6776b36b6af1991af222cf79e48412335ca01cbb07146f9ed50045a6`（前 16 = `9c7567bd6776b36b`），与 v2 规范基线记的同一前缀一致 | 本次 sha256 实测；对照 `.trae/specs/adversarial-complete-forms-v2-10rounds/baseline/baseline_snapshot.md:5` | 尺子版本至少在两次基线间未漂移 |
| 语料必须是 Python 3.11 字节码，解释器版本硬门 | `scripts/pyc_verify.py:381-383` | 判据只在 3.11 语料上成立 |

---

## 1. `scripts/pyc_verify.py` 自身的判定动作（逐条 + 行号）

| # | 动作 | 行号 | 说明 |
|---|---|---|---|
| 1 | **产物重编译后再比** | `:101` `py_compile.compile(source, cfile=recompiled, doraise=True, optimize=0)` | 比的不是原始 `.py`，而是产物**重新编译出的字节码**；产物语法错 ⇒ `compile_error`（`:102-109`） |
| 2 | 调用附件判据 | `:112` `results = compare_pyc(pyc, recompiled)` | 逐 code object 出 verdict |
| 3 | 单元计数 | `:122-128` | `units_total = len(results)`；`units_success = sum(r.success)`；`success_rate` |
| 4 | 文件级判定 | `:129` | `status = success` 当且仅当 `units_success == units_total`（**全或无**） |
| 5 | 空结果无效 | `:124-127` | `results` 为空 ⇒ `error`（读数无效） |
| 6 | 失败文本留存 | `:130` | `failures = [str(r) for r in results if not r.success]` |
| 7 | 异常归桶 | `:102-117` | `PyCompileError`/`SyntaxError`/`ValueError`/`OSError` → `compile_error`；`compare_pyc` 抛异常 → `error` |
| 8 | Movement Matrix（前后对比） | `:233-281` | 按文件路径做 4×4 桶迁移矩阵；`:272-280` 输出 `units` 前后比与 `REGRESSIONS=` / `IMPROVED=` |
| 9 | **尺子自检** | `:284-320` | 自比必须全等（`:292-296`）；两种变异必须被抓（`:297-311`），否则判「判据失灵」 |
| 10 | 内建变异只有两类 | `:297`、`:332-346` | `_mutate_return`（改 `return None/True/False/数字`）、`_mutate_compare`（翻转 `>`/`<`/`==`/`!=` 极性） |
| 11 | 退出码语义 | `:181`（single）、`:230`（batch） | `single`：status≠success ⇒ rc=1；**`batch`：仅 `error`/`compile_error` 非空才 rc=1，文件级 `failure` 不影响退出码** |

---

## 2. 真正的比较项（附件 `compare_pyc` 内，逐项 + 行号）

> 路径：`D:\Desktop\ptrade相关\pylingual\pylingual\equivalence_check.py`（仓外；下文简称 `eq`）。

| # | 被比较的方面 | `eq` 行号 | 判定内容 |
|---|---|---|---|
| 1 | **代码对象数量** | `:80` | `len(pyc_a) != len(pyc_b)` ⇒ 不等即失败 |
| 2 | **代码对象配对（按名字）** | `:152-177`（`:158`） | `difflib.SequenceMatcher` 以 code object **name** 序列配对；配不上 ⇒ `Missing bytecode`(`:205`) / `Extra bytecode`(`:201`) |
| 3 | **异常表结构** | `:83` | `pyc_a.named_exception_table != pyc_b.named_exception_table` ⇒ 失败（handler/depth/区间整体比对） |
| 4 | **CFG 节点数** | `:17` | 基本块节点数必须相等 |
| 5 | **CFG 边集合（控制流形状）** | `:28-40` | 按 offset 排序映射节点后，逐节点比较**出边目标集合**；不等 ⇒ `Different control flow`(`:213`) |
| 6 | **指令级属性** | `:46-53` | `opname, opcode, optype, real_size, has_arg, has_extended_arg, offset, is_jump_target` 逐字段相等（`attr_list`） |
| 7 | **无条件跳转目标** | `:50-51` | 双方均为无条件跳转时**只比 `argval`**（目标偏移） |
| 8 | **操作数值** | `:56-66` | `argval_a == argval_b` ⇒ 相等；`:62-64` 嵌套 code object 的 `co_code` 在父层跳过（改由递归配对比对） |
| 9 | **归一化补丁（比较前）** | `:194-195` | `remove_extended_arg, remove_nop, fix_indirect_jump, fix_unreachable, replace_firstlno` 各施加一次 |
| 10 | **verdict 分类** | `:201-224` | 5 类：`Extra bytecode` / `Missing bytecode` / `Different control flow` / `Different bytecode`(`:219`) / `Equal`(`:223`) |

**据此可判定的「绿」= 每个 code object 都 Equal**，即：代码对象集合一致 + 每对象的异常表一致 + CFG 形状一致 + 指令序列（含操作数值）一致（在被归一化抹平的范围内）。

---

## 3. 已知盲区（**从代码直接可见**，非推测）

| # | 盲区 | 依据行 | 后果 |
|---|---|---|---|
| B-01 | **从不执行程序**：全流程只比字节码/CFG，不执行 | `eq:180-226` | 返回值、副作用（文件/全局/属性写入）、异常**消息**、副作用**顺序**完全不参与判定 |
| B-02 | **值语义按 `==` 判** | `eq:59` | `1` / `True` / `1.0` / `0` / `False` 互相**不可分辨**（Python `==` 语义）；即 spec 所述「1 vs True vs 1.0」在此判据内**结构性不可见** |
| B-03 | **指令实参下标（`arg`）不比** | `eq:47`（`attr_list` 无 `arg`）、`eq:53` | 只比 `has_arg` 与 `argval`；`LOAD_FAST 0` 与 `LOAD_FAST 1` 若 `argval` 同名则等价 ⇒ **形参顺序错位可能漏检**（`argval` 是名字，`arg` 是下标） |
| B-04 | **行号信息被抹平** | `eq:194-195`（`replace_firstlno`） | 全部行号归一到首个 lno ⇒ traceback 行号语义差异不可见 |
| B-05 | **NOP 与不可达代码不可见** | `eq:194-195`（`remove_nop`, `fix_unreachable`） | 死代码差异、冗余 NOP 差异不判失败 |
| B-06 | **EXTENDED_ARG / 间接跳转被归一** | `eq:194-195` | 该两类字节码差异不判失败 |
| B-07 | **CFG 只比形状，不比边属性** | `eq:28-40` | 只比出边目标集合；边上的类型/权重信息不参与 |
| B-08 | **code object 属性只经指令间接体现** | `eq:80-99`（仅数量 + 异常表 + 指令） | `co_names`/`co_varnames`/`co_freevars`/`co_flags` 等无独立比较通道；捕获变量的**集合**变化若不改变指令序列则不可见 |
| B-09 | **无 AST / 源码级判据** | `eq` 全文无 `ast` 比较 | 注解、docstring、装饰器顺序、字符串与转义写法**没有专门判据**；只有当它们改变字节码时才可能被抓（故本条表述为「无专门判据」，不断言必漏） |
| B-10 | **batch 退出码不反映文件级 failure** | `scripts/pyc_verify.py:230` | 有 failure 文件时 `batch` 仍可 rc=0；只看 rc 会误判「全绿」 |
| B-11 | **内建变异只有两类** | `scripts/pyc_verify.py:297,332-346` | 「删语句 / 换操作数顺序 / 改参数顺序 / 改注解 / 改字符串转义」等**无内建夹钳**；selfcheck 的「判据可用」结论只覆盖常量与极性两种变异 |
| B-12 | **尺子在仓外、锚定只有 16 hex** | `scripts/pyc_verify.py:40,79-83` | 仓内无法独立复算判据；附件换版不可察（除非比对 sha 前缀） |
| B-13 | **判据与产品共享 3.11 字节码 / 异常表 / CFG 假设** | `eq:14-99` + `core/cfg/region_analyzer.py` 的 CFG 建模 | 「共同原因失败」不可排除（spec.md:78 要求以变异测试证伪） |
| B-14 | **单元级判定不覆盖跨函数 / 模块级装配** | `eq:199`（逐 code object 独立判定） | 模块级副作用顺序、跨函数闭包绑定、类级装饰器链等装配语义不在任一单元内比较 |

---

## 4. 产出「绿」读数的工具清单（攻击面锚点）

| 工具 | 路径 | 产出读数 | 关键行 |
|---|---|---|---|
| **唯一判据入口** | `scripts/pyc_verify.py` | `single`（units/total + status）、`batch`（units/total + 文件四桶 + `ruler` sha）、`compare`（Movement Matrix + `REGRESSIONS`/`IMPROVED`）、`selfcheck`（尺子自检） | `:162-181`、`:184-230`、`:233-281`、`:284-320` |
| **探针驱动** | `.trae/specs/attain-true-completeness/rounds/round1/rec1_run.py` | 每探针：`regen_rc`（`pycdc.py -o` 重生成产物）→ `pyc_verify.py single` → `status`/`units`；落 `rec1_probes_<stamp>.json`，末行汇总 `units=%d/%d (%d probes)` | `:70-120`（单探针）、`:161-166`（落盘 + 汇总）、`:47-67`（`parse_status` 解析 `[single] status=` 与 `***` 失败行） |
| **E 门禁编排** | `.trae/specs/attain-true-completeness/rounds/round8/final_verify_run_r8.py` | 8 分片 regen→verify→compare×8；small34 拆两半；quotation 单验；pytest 七套件；IV.2 自检；`final_verify_summary.json` | `:49-57`、`:58-90`、`:91-94`、`:95-99`、`:100-153`、`:157-177`（被其调用的分片驱动：`rounds/round8/verify_driver.py`、`rounds/round8/verify7_split.py`） |
| **形态覆盖口径工具** | `tools/kb/syntax_coverage.py` | `docs/refactor/syntax-coverage.json`：分母 128（97 ast 节点 + 31 扩展形态）、分子 128、`uncovered` 空 ⇒ 「路径存在 128/128 = 100%」 | `:32-64`（31 扩展形态定义）、`:92-107`（分母）、`:113-142`（分子）、`:144-184`（扩展形态覆盖判定）、`:196-221`（输出） |

> 口径提醒：这四个「绿」**互不等价**——
> `syntax_coverage.py` 的 100% 是**词汇存在性**读数（不涉及任何行为）；
> `pyc_verify.py` 的绿是**字节码 + CFG 形状等价**读数（不涉及执行语义，见 §3 B-01）；
> `rec1_run.py` 的绿是**在指定探针集上**的上述读数（探针集有限且由人挑选）；
> `final_verify_run_r8.py` 的绿是**上述读数在 402+34+1 语料与 7 套 pytest 上的汇总**（语料固定、偏小函数）。
> 「三态 v8 = 128/0/0 = 100%」是这三类读数**加上人工判读**后的合成结论（`rounds/round8/REVIEW2.md:36-42`）——其推断链的断点位置即 L1/L2 的攻击目标。
