# COMPLETENESS_METHOD — 从「抽样绿」到「可证伪完备」

> 版本：v3（两轮红队评审未通过后修订；评审见 `METHOD_REVIEW.md`，第三轮复审前不得标记 Task 8 完成）
> 依据：`spec.md` §100–109（四支柱 + 可证伪门槛）、`spec.md` §125–142（v9 双读数、禁止以 128 单独声称完备）；
> 攻击结论：`rounds/round2/ATTACK_L0_THEORY.md` … `rounds/round7/ATTACK_L5_EVIDENCE.md`；
> 破口台账：`rounds/round3/BREACH_REGISTRY.md` B163–B219 + U-01–U-06。
>
> 适用范围：**CPython 3.11.7** 字节码 → 本产品反编译源码的等价性；3.12+ 语法、跨解释器 ABI、运行时外部依赖不在本版范围。
> 结论强度：本方法只能把「完备」降级为**可证伪的工程断言**，不能证明「对所有 Python 程序语义等价」；
> 任何超出声明模型的场景都必须显式标为「未覆盖」或 `N/A`。

---

## §0 术语、口径与禁用词

| 术语 | 定义 | 当前基线 |
|---|---|---|
| 形态基线（v8） | 128 个节点/形态中「登记为完备」的占比 | 128/128 = 100%（**历史口径，只表示形态清单**） |
| 判定空间 J | 四维笛卡尔积下有限、可枚举、可生成探针的条目集合 | v1 = **1556** 条（`rounds/round1/judgment_space.json`） |
| 条目五元组覆盖 | 条目 j 同时具备「源 + pyc + 产物 + 执行级判定 + 哈希链」 | **尚未实现**；旧 976/1556 = 62.72% 只是 probe-only（B170） |
| 语义差分 | 原 pyc 与产物源码在受控沙箱中执行，比较返回/副作用/异常/顺序/元数据 | L2/L4 已证旧判据不执行（B-01） |
| 规则覆盖引理 | 每条归约规则 R 在 J 中有正例/反例、域/守卫/组合覆盖，且不变式机检通过 | **0 条完成**；manifest 未建立；不得用 `0/0` 通过 |
| J 门槛达标 | G1 + G2a + G3 + G4 + G5 + G6 全满足 | **未达成** |
| 语料完备 | 「J 门槛达标」+ G2b（`N/A=0`）+ G2c（真实项目） | **未达成** |
| 完备（不加限定） | 仅指「语料完备」；不得用「J 门槛达标」简称 | **未达成** |
| 形态基线达成 | 128/128 形态清单有登记，但未满足上述门槛 | 当前状态 |

**禁用表述**（与 L5 §4.4 一致）：

- 不得把 `6617/6617`、`128/128` 单独写成「完备」「语义完备」「100% 正确」；
- 不得用「探针全绿」替代「条目五元组覆盖」；
- 不得用「规则看起来对」替代「规则覆盖引理 + 语义差分」；
- 不得把 `INCONCLUSIVE`（超时/不支持/环境缺失）或 `N/A`（无输入模型）计为通过；
- 不得把旧结构判据的 `4/46=8.70%` 写成语义差分绿；它是 `compare_pyc` 读数，同批还有 `7/46=15.22%` 产物不可编译。

---

## §1 设计原则（从 L0–L5 反推）

| 编号 | 原则 | 来自哪条攻击结论 | 可操作要求 |
|---|---|---|---|
| P1 | **可证伪优先** | L0 归纳二元性、L3 0/7 族通用、L5 自证 | 任何「完备」结论必须给出可失败的读数；不能失败的指标不得作为门槛 |
| P2 | **语义优先** | L2 漏检 27.92%、L4 语料外判据绿 8.70% | 执行级差分是主判据；字节码/CFG 判据只做分诊 |
| P3 | **源/产物可追** | L5 原始源 0/402、stamp 3342/197 | 每个判定绑定 pyc sha、产物 sha、源 sha（若有）、判据 sha、解释器版本 |
| P4 | **平面分离** | L5 9 类 bytecode 盲区、伪零 | 不可判定形态输出 `N/A`；bytecode/source 两平面分别报覆盖 |
| P5 | **规则闭合** | L0 三元组合、L3 叠加塌陷 | 每条规则有不变式、守卫闭包、组合义务；不能只测单形态 |
| P6 | **证据去重** | L5 16.96 条/产物、B219 | 以 artifact id 为唯一分母；stamp 数、运行记录数不得冒充独立证据 |
| P7 | **版本绑定** | L1 解释器漂移 96.24%、L5 语料偏差 | J、判据、生成器、语料快照全部带版本；跨版本必须重跑门槛 |
| P8 | **零特判** | v3 纪律 I.4 / G3 / G4 | 规则不得按文件名、路径、语料指纹特判；不得硬编码上限 |

---

## §2 支柱一：判定空间（J）

### 2.1 形式化定义

设：

- `F`：**语法形态族**，v1 取 39 族（25 行既有口径 + NEW 14 族）；族是文法级，不是 128 个词法标签；
- `H`：**宿主上下文**，v1 取 48 种（模块/函数/类/循环/try/with/match/async/lambda/comprehension/装饰器等）；
- `D`：**深度档**，`D0=顶层`、`D1=一层嵌套`、`D2=两层及以上`（v1 至少 3 档）；
- `V`：**变体槽**，由 schema 给出（赋值目标、值类型、break/continue/else、异常别名、装饰器顺序、字符串转义、注解位置等）。

判定空间：

```
J ⊆ F × H × D × V
```

每个条目 `j = (f, h, d, v)` 有唯一 ID `JS-<layer>-<seq>`，并**必须**绑定以下机器字段：

| 字段 | 用途 | 缺失后果 |
|---|---|---|
| `source` / `P_j` | 可编译的 3.11 源码（生成器产出，不手改） | C1 不成立 |
| `expected_label` | 生成器应命中的 f/h/d/v 标签 | 生成器自检失败 |
| `input_model` / `I_j` | 确定性输入或输入类（含空/边界/异常触发） | 无法进入 G2a |
| `host_prelude` / `host_postlude` | imports、fixture、异常注入点 | 宿主不成立 |
| `entrypoint` | 被测函数/类/模块入口 | 无法执行 |
| `counterexample_hint` | 该条目最容易被什么错误实现破坏 | 反例设计缺失 |
| `excluded` | 不合法组合的语言理由 | 分母静默缩小 |

**v1 规模**：1556 条（`rounds/round1/JUDGMENT_SPACE.md`）。现有 J 文件只装配了 **299/408 个 `(form,variant)` 槽、584 个 `(form,host,depth)` 单元**（评审核验）；稀疏选择本身合法，但必须生成 `excluded[]` 并说明语言理由。J 的**充分性**由独立评审检查，不能由生成器自证。

**`excluded` 的口径**：`excluded[]` 记录**生成器槽级**的非法组合（如 `yield` 在 lambda 内），不是 J 条目状态；被排除的组合不进入 1556 分母。若某条目本身不合法，则它不在 J v1 的 1556 条内。报告单列 `excluded_slots`，并满足：

```
covered_5tuple + probe_only + unexecuted + n/a + inconclusive = J_total = 1556
```

`excluded_slots` 不参与该等式；任何把 excluded 条目计入 `J_total` 又在 G1 要求 covered=1556 的写法都是口径错误。

### 2.2 有限可枚举生成

`tools/completeness/jspace_generator.py` 是 J 的唯一生成源：

- 输入：`J_SCHEMA_VERSION`、`PYTHON_VERSION=3.11.7`、族表、宿主表、深度表、变体 schema；
- 输出：`judgment_space.json`（条目 + 生成器版本 + schema 哈希）、每个条目的 `P_j`/输入模板、`excluded[]`、覆盖清单；
- 约束：
  - 生成是**确定性的**（固定 seed；同一版本重复生成字节级一致）；
  - 每个条目必须通过「生成器自检」：`compile(P_j)` 成功、形态检测器命中预期标签；
  - 不允许生成器读取被审计产品源码或判据结论（避免共同原因）；
  - 不合法组合（例如 `yield` 在 lambda 内）必须显式记录为 `excluded`，并给出语言理由，不得静默丢弃；
  - 每个 `(f,h,d,v)` 的选择/排除都要可复算；`J` 的装配率与 `excluded` 清单随 J 版本冻结。

### 2.3 覆盖检查器（0 未覆盖）

一个条目只有同时满足以下**五元组**才算 `covered`：

| 条件 | 证据 |
|---|---|
| C1 源存在且非空 | `P_j` 的 sha256 + 行数 |
| C2 pyc 存在且可加载 | `compile(P_j)` 的 pyc sha256 + 解释器版本 |
| C3 产物存在 | 反编译产物的 sha256 + 生成命令 |
| C4 执行级判定已运行 | `semantic_diff` 的 verdict + 输入 seed + 退出码 |
| C5 哈希链完整 | C1–C3 三个内容 sha + C4 判定记录（verdict/seed/退出码）+ `judge_sha256` + runner 版本，全部写入同一证据记录并与 J 条目 ID 绑定 |

`tools/completeness/coverage_checker.py` 的输出必须同时给：

```
J_total, covered_5tuple, probe_only, unexecuted, n/a, inconclusive,
excluded, uncovered[], checker_version
```

- `covered_5tuple = J_total` 才满足 G1；
- `probe_only`（只有源/探针、没有 C2–C4）不得计入 covered；
- `n/a`（无输入模型/不可执行）不得计入 covered；
- `inconclusive` 不得计入 covered；
- 任何未覆盖条目必须带 `reason`（未生成/不可执行/环境缺失/语法排除/无输入模型）并进入缺口台账；
- **当前状态**：现有 `coverage_checker.py` 仍是 probe-only（B170），因此 G1 **不可评**，不能把 976 当分子；升级后的检查器必须先用合成正例/反例自测。

**对 B170 的修复**：不再以「探针存在」作为 covered；以 C1–C5 为准。

### 2.4 版本与增长

- J v1 冻结为 1556 条；新增语法（3.12+）进入 J v2，另立版本，不得改写 v1 分母；
- 任何 J 变更必须重跑 G1–G6，并在台账中记录「新增条目数 / 新增覆盖数 / 新增缺口 / 新增 excluded」；
- 双读数必须写 J 版本与生成器哈希，禁止只写百分比；
- `arg`/`arguments`（函数形参面）、签名、docstring 必须进入 J 或独立观测类（B171）；若判定其不影响语义，必须给出可复现的排除论证，不能以「没有枚举」代替。

---

## §3 支柱二：判据升级（语义差分）

### 3.1 主判据：执行级语义差分

对每个 `semantic_case`：

```
原程序：  pyc     --(SourcelessFileLoader / importlib)--> 模块 M_orig
产物：    *OK.py  --(import)--------------------------> 模块 M_prod
输入：    I_j 的确定性样本 x
比较：    run(M_orig, x)  vs  run(M_prod, x)
```

`semantic_case` 的最小字段：

```json
{
  "case_id": "JS-... | ART-... | REAL-...",
  "artifact_id": "...",
  "entrypoint": "module:function | module | class",
  "signature_binding": {
    "source": "inspect.signature(orig)", "product": "inspect.signature(prod)",
    "args_ok": true, "bound_argcount": 2, "bound_kwonly": 0
  },
  "arg_model": {"strategy": "typed|defaults|boundary|fixed", "values": []},
  "setup": "module import | fixture | constructor",
  "inputs": [{"seed": 0, "class": "boundary", "payload_sha256": "..."}],
  "timeout_s": 5,
  "observation_set": ["R1", "R2", "R3", "R4", "R5", "R7"],
  "body_reached": {"required": true, "witness": "line:42", "hits": 1},
  "model_status": "modeled | n/a | inconclusive"
}
```

**有效性前置条件（防假绿）**：

- `signature_binding.args_ok = true` 且参数个数/类型能绑定到目标签名；绑定失败记 `ERROR` 或 `N/A`，**不得**因双方都抛 `TypeError` 而判 `EQUAL`；
- 函数级 case 必须 `body_reached.hits >= 1`（至少执行到目标函数体/目标块）。R6 覆盖率可作诊断，但 `body_reached` 是 case 有效性的前置条件；
- `model_status=modeled` 必须同时满足签名绑定成功 + 至少一个输入到达目标体 + 无 harness 自身异常；
- 没有 `entrypoint` + `input_model` + `body_reached` 的 code object 不得生成 import 级「假绿」：只能记 `N/A`，并保留在缺口清单中。

**必须比较的观测类**：

| 类别 | 比较内容 | 容差 |
|---|---|---|
| R1 返回值 | 类型、`repr`、深度相等、NaN/±0/浮点误差 | 浮点：`abs/rel <= 1e-9` 或条目显式声明；其他类型默认精确 |
| R2 异常 | 异常类型、args、规范化 message、traceback 末帧函数名 | message 仅允许去除路径/行号/对象地址；不得忽略类型 |
| R3 副作用 | 输入对象前后深拷贝 diff、stdout/stderr、临时目录文件清单+sha、模块级白名单变量 | 文件顺序无关；时间/随机/环境变量必须显式 seed 或排除 |
| R4 顺序 | 事件日志（调用序列、写入序列、异常抛出点） | 仅比较声明为语义顺序的事件；墙钟时间不计 |
| R5 终止 | 正常返回 / 异常 / 超时 / 崩溃（信号/非零退出） | 超时 = `INCONCLUSIVE`，不是 EQUAL |
| R6 覆盖 | 产物执行到的行/分支（`trace`/`coverage`）；`body_reached` 为 case 有效性前置 | 覆盖率本身不作为语义通过条件；未到达目标体记 `N/A/ERROR` |
| R7 元数据/ABI/身份 | `__doc__`、`__annotations__`、`inspect.signature`、`__defaults__`、`co_*`、闭包单元、类/函数身份、装饰器顺序、别名拓扑（身份图同构，不比较裸 `id`） | 默认精确；`co_*` 仅比较语义白名单，规范化规则见 §3.5 |

R7 是 L2 实测盲区的直接补丁：docstring 漏检 108/108、形参换序漏检 159/162、`x=1→x=True` 漏检 83/84；这些都必须判 `DIFF`，不能以「源码可读」视为等价。

**verdict 四类**：

- `EQUAL`：R1–R5、R7 全部在容差内一致；
- `DIFF`：任一观测类不一致；产物编译/导入失败记 `DIFF/PRODUCT_ERROR`；
- `INCONCLUSIVE`：超时、环境缺失、依赖不可用；
- `ERROR`：harness 自身错误。

只有 `EQUAL` 计入通过；`DIFF`、`INCONCLUSIVE`、`ERROR` 都不得混入绿。

### 3.2 沙箱与输入

- 每个 case 独立子进程；`cwd` 为临时目录；`PYTHONHASHSEED=0`；固定 `TZ`/`LC_ALL`；网络默认关闭（除非条目声明）；
- 资源限制：CPU 时间、内存、文件大小、进程数；超时按条目声明（默认 5 s，规模条目单独声明）；
- 输入生成：确定性 seed + 输入类（空/单元素/边界/异常触发/大输入）；输入对象深拷贝后再分别喂给两个模块；
- 禁止共享可变全局状态：每个 case 重新 import；或用子进程隔离；
- 原 pyc 直接加载（`SourcelessFileLoader`），**不要求原始 `.py` 存在**；这修复 L5 B214 对执行级判定的阻塞。源级形态审计仍要求 `.py`，二者分开报告；
- 产物 `*OK.py` 若不能编译/导入，直接记 `DIFF/PRODUCT_ERROR`，不得跳过为 `N/A`。

### 3.3 判定集的分层（G2a / G2b / G2c）

| 层 | 对象 | 要求 | 不得混入 |
|---|---|---|---|
| **G2a** | J v1 全 1556 条 | 每条有 `modeled` 输入；`DIFF=0`、`INCONCLUSIVE=0`、`N/A=0` | 402 语料、旧判据绿 |
| **G2b** | 402 认证产物（6617 code object） | 每个 artifact 至少一个 `artifact_import` case；每个可建模 code object 一个函数级 case；`N/A` 逐条列出 | J 条目、small34 |
| **G2c** | 46 个语料外真实 pyc | 每个可加载产物一个 import case + 可建模函数 case；至少覆盖注解/f-string/dataclass/生成器/async/装饰器链/PEP604/`except*` 各 1 个真实样本 | 合成探针、J 条目 |

- G2b 的 `N/A` 不是通过；只有 `N/A=0` 才可称「语料完备」，否则只能报「语料语义覆盖 X%」。
- G2b 的 **`modeled` 机检规则**：签名可绑定 + 至少一个输入到达目标函数体 + 无 harness 异常；`artifact_import` 只覆盖模块级，不能替代函数级 case；无法满足者记 `N/A` 并附 `reason`，由 C 角色抽查签字。
- G2c 中 `7/46=15.22%` 产物不可编译必须计入 `DIFF/PRODUCT_ERROR`；`except*` 真实样本当前为 0（B213），因此 G2c **不能通过**，必须保留缺口。
- G2b/G2c 的读数只证明「语料/真实项目」层，不能替代 G2a 的 J 覆盖。

### 3.4 结构判据的定位

`scripts/pyc_verify.py` / `compare_pyc` 保留为**分诊器**：

- 用于快速定位可疑 code object、缩小差分范围、生成最小复现；
- 不作为最终 oracle；其盲区 B195–B201 必须在报告中标注；
- 当结构判据与语义差分冲突时，**语义差分优先**；结构判据的 `Equal` 不得覆盖 `DIFF`；
- `4/46=8.70%`、`12/21=57.1%` 等旧判据读数只能放在「旧结构判据（历史）」行，不能放进 G2。

### 3.5 R7 的 `co_*` 规范化白名单

`co_*` 不能裸比：`co_code`、`co_filename`、`co_firstlineno`、`co_linetable`、`co_exceptiontable` 的差异可能是合法的布局/重编译差异。R7 采用版本化白名单：

| `co_*` | 处理 |
|---|---|
| `co_name`、`co_qualname` | 精确比较；生成器临时名若被声明为规范化项，必须逐条列出 |
| `co_argcount`、`co_posonlyargcount`、`co_kwonlyargcount` | 精确比较 |
| `co_flags` | 只比语义位掩码（版本化定义）；布局/优化标志不参与 |
| `co_varnames` | 参数前缀精确；局部临时名按声明的规范化映射比较 |
| `co_freevars`、`co_cellvars` | 精确比较（顺序敏感，闭包语义相关） |
| `co_names` | 精确比较（属性/全局名影响语义） |
| `co_consts` | 递归规范化后比较；`code` 常量递归进入本白名单 |
| `co_code`、`co_filename`、`co_firstlineno`、`co_linetable`、`co_exceptiontable` | **不裸比**；由 R1–R5 + 结构分诊覆盖 |

白名单与规范化函数必须带版本哈希；白名单外的差异一律 `DIFF`，不得以「实现细节」为由忽略。

### 3.6 判定记录 schema（最小字段）

```json
{
  "case_id": "JS-...",
  "artifacts": {
    "source_sha256": "...", "pyc_sha256": "...",
    "product_sha256": "...", "judge_sha256": "...",
    "python": "3.11.7", "j_schema": "v1"
  },
  "entrypoint": "module:function",
  "signature_binding": {"args_ok": true, "bound_argcount": 2},
  "body_reached": {"required": true, "witness": "line:42", "hits": 1},
  "input": {"seed": 0, "class": "boundary", "payload_sha256": "..."},
  "observations": {
    "return": {}, "exception": {}, "side_effects": {},
    "order": [], "termination": "normal", "metadata": {}
  },
  "tolerance": {"float_abs": 1e-09, "ignore_paths": true},
  "verdict": "EQUAL",
  "runner": {"tool": "semantic_diff.py", "version": "...", "elapsed_s": 0.12}
}
```

没有上述字段的记录不进入证据链；禁止只保留 `status=success` 的汇总。

### 3.7 变异总体与 G3 公式

G3 的总体不是「随便造几个变异」，而是**可复算的有限集**：

```
M_total = { m | m = mutate(c, op, site), c ∈ C_cases, op ∈ Ops, site ∈ Sites(c) }
```

- `C_cases`：已通过 G2 有效性前置的 J/语料 case；
- `Ops`：≥12 类变异算子（值/分支/删除/换序/别名/转义/注解/docstring/装饰器顺序/异常别名/循环控制/局部-属性/类属性/边界）；
- `Sites(c)`：case 内可变异位置；生成器独立于产品实现，不得 import 产品规则；
- 每个变异体必须可编译/可导入；不可编译者记 `invalid`，不进入 accepted。

状态定义（集合必须互斥）：

```
accepted  = M_total - invalid
E         = { m ∈ accepted | 有机器可检等价证明 }
N         = accepted - E                  # 非等价变异体
killed    = { m ∈ N | semantic_diff(m) = DIFF }
survived  = { m ∈ N | semantic_diff(m) ∈ {EQUAL, INCONCLUSIVE, ERROR} }
false_kill= { m ∈ E | semantic_diff(m) = DIFF }
true_neg  = { m ∈ E | semantic_diff(m) ≠ DIFF }
```

由此：

```
N = killed + survived
accepted = killed + survived + E
E = false_kill + true_neg
miss_rate = survived / N              # 非等价变异体漏检率
false_kill_rate = false_kill / E
```

- `killed` 与 `false_kill` **互斥**：前者是「非等价且判 DIFF」，后者是「等价却判 DIFF」；
- `survived` 不含等价变异体；等价变异体只能进 `E`，且必须有证明；
- `accepted > 0` 且 `N > 0` 才可计算；否则记 `INCONCLUSIVE`；
- `equivalent` 必须附证明：`{mutant_id, case_id, method: symbolic|exhaustive|theorem, input_domain, checker_version, result}`；无证明或不可复算 → 计入 `survived`；
- `false_kill > 0` 说明 oracle/规范化有误，G3 不通过；
- 报告必须单列 `invalid`、`survived`、`equivalent(proved)`、`false_kill`；
- 旧 `366/1311=27.92%` 是结构判据历史读数，公式不同，不得代入 G3。

---

## §4 支柱三：证明义务

### 4.1 规则清单（rule manifest）

每条归约规则 `R_i` 必须在 `rule_manifest.json` 中登记：

| 字段 | 内容 |
|---|---|
| `rule_id` | 稳定 ID（与代码中的规则位置/注释锚点一致） |
| `anchor` | 代码锚点 `file:line` + canonical 正则命中串 |
| `pattern` | 触发的 opcode/AST 形状（最小模式） |
| `preconditions` | 入栈/块/作用域/异常表状态 |
| `effect` | 生成节点/区域、边、异常表、变量绑定 |
| `guards` | 守卫条件与全部调用点（必须列全） |
| `invariants` | O1–O7 中适用的不变式 |
| `semantic_domain` | 该规则声明覆盖的输入域；超出即 `UNKNOWN` |
| `witnesses` | 至少一个正例 J 条目 ID、一个反例 ID |
| `composition` | 与宿主/相邻规则的组合证据（D2 + 三元组） |
| `proof` | `proof_id`、检查器版本、反例搜索界、评审记录 |
| `status` | `proved` / `tested-only` / `open` |

**只有 `proved` 计入规则完备**；`tested-only` 是证据，不是证明。

**manifest 完整性**：

- **独立规则全集**：`total_rules` 必须来自**独立枚举器**（从 `core/cfg/**` 的规则分派分支/区域类型/生成器入口静态枚举），不得由 manifest 自己的 canonical 正则定义；manifest 只做映射，不能自定分母；
- `total_rules = |rule_universe| > 0`；`0/0` 记 `INCONCLUSIVE`，不得通过 G4；`1/1` 也不自动通过，仍需域/守卫/组合见证；
- `rule_manifest` 必须与独立全集**双向对账**：`unmapped_anchors=0`（独立全集中的规则未映射）且 `orphan_rules=0`（manifest 有、全集无）；
- 独立枚举器无法枚举时记 `INCONCLUSIVE`，不得退回 manifest 自证；
- 对账正则、锚点提取器、独立枚举器和 manifest 版本必须写入证据；B178/B183 的 191/174/123 口径歧义以独立枚举结果为准，并在台账注明；
- 负例的「相似但不该触发」必须由 `pattern` 的最小编辑（同 opcode/AST 形状、改一个前置条件）生成，不能手写一个无关程序充数。

### 4.2 七类证明义务

| 编号 | 义务 | 机检方式 | 失败示例 |
|---|---|---|---|
| O1 | **全域性**：每个输入块恰好归入一个规则/区域 | 对 J 全量 + fuzz 样本 + 402 语料跑 `unowned_blocks=0` | L0 三元组合内层 try 体消失 |
| O2 | **唯一性**：同一块不得双归属 | `block_to_region` 多值检测；同优先级平局必须报错而非按注册顺序裁决 | L0 B173/B174、finally 双归属 |
| O3 | **守卫闭包**：守卫的触发集覆盖所有宿主/深度 | 守卫调用点静态清单 + 每个调用点至少一个负例 + `continue` 的 loop 限定检查 | continue 守卫无 loop 限定（B175） |
| O4 | **结构保持**：块/边/异常表/作用域不变式 | CFG 校验器 + 异常表逐项 compare | finally 副本重复、handler 体丢失 |
| O5 | **语义保持**：规则声明域内 `EQUAL` | `semantic_diff` 对规则关联的 J 条目全量执行 | try-else 并主路径（B204）、continue 消失（B208） |
| O6 | **组合保持**：与宿主/相邻规则的组合不破坏 O1–O5 | 3 元组合样本 + 深度 D2 + 叠加 fuzz | L0 三元击穿、L3 深度≥3 塌成 pass |
| O7 | **非干扰**：不依赖全局缓存/注册顺序/文件名 | 乱序运行、重命名、清缓存后结果一致 | 同优先级按注册顺序裁决（B173） |

### 4.3 覆盖引理（可机检）

对每条规则 `R_i` 定义：

```
Cov(R_i) = { j ∈ J | P_j 触发 R_i 且五元组覆盖 }
```

要求：

1. `Cov(R_i) ≠ ∅`（规则至少被一个 J 条目触发）；
2. `Cov(R_i)` 中至少 1 个正例（预期规则应触发，且有 `rule_fired` 轨迹）与 1 个反例（同 `pattern` 最小编辑、改一个前置条件后不触发）；
3. 规则的 `semantic_domain` 在 `H × D` 的每个声明单元至少有一个见证；不能只用单宿主/单深度；
4. 规则的每个 `guard` 调用点至少有一个负例；`continue`/`break`/`finally` 守卫必须显式覆盖 loop/handler 限定；
5. 每个 `j ∈ J` 至少映射到 1 条规则；映射为空 ⇒ 生成器或规则清单缺口；
6. 每个规则至少有一个 O6 组合见证（D2 + 相邻规则），不能只测单形态；
7. 映射由 `coverage_checker` 从形态标签/CFG 轨迹自动产生，禁止手工填表。

**规则覆盖率** = `proved_rules / total_rules`；**条目覆盖率** = `covered_5tuple / J_total`。
两者都必须在报告中出现；`total_rules=0` 时 G4 记 `INCONCLUSIVE`，不得把 `0/0` 当 100%。

### 4.4 「证明」的诚实边界

本方法不要求 Coq/Isabelle 级别的机器证明。`proved` 的含义是：

> 在声明的 CPython 3.11.7 语义模型、J 输入模型与规则声明域内，不变式机检通过、边界搜索未发现反例、组合见证齐全、且人工评审记录可追。

因此：

- 「proved」仍可能被新反例推翻；台账必须保留 `counterexample` 字段；
- 任何规则若只能在「小样本」成立，必须标记 `tested-only`，不得升级为 `proved`；
- 证明义务不能由「判据绿」替代；L2 已证判据绿可语义错；
- `proof` 字段必须可由独立评审复算；不能只写「已评审」。

---

## §5 支柱四：持续证据

### 5.1 差分 fuzz

| 组件 | 要求 |
|---|---|
| 生成器 | 从 3.11 AST/字节码文法生成，不使用产品代码作为模板；覆盖 F/H/D/V 的边缘组合 |
| 属性测试 | `decompile(compile(P))` 与 `compile(P)` 语义等价；重复反编译幂等；异常/副作用保持 |
| 变异 fuzz | 对产物注入已知错误（值/分支/删除/换序/别名/转义/注解/装饰器顺序/异常别名），统计判据/差分捕获率 |
| 崩溃最小化 | 对每个 `DIFF`/`ERROR` 做 ddmin（源码或 AST 级），保留失败并输出最小复现 |
| 金丝雀 | v1 至少 **24 条**（3 类 × 8：稀有语法、深层宿主、语义陷阱）；不进公开语料；独立评审者保管；季度轮换；泄漏扫描 |
| 语料回归 | 402 认证语料 + small34 + quotation + tests 基线；任何失败阻断发布 |

**金丝雀的独立性**：

- 生成者与产品实现者分离；探针 seed 与期望输出密封保存；
- 每次运行记录 `canary_id`、`seed_hash`、`verdict`，不记录明文探针到公开日志；
- 泄漏检测：在公开语料/仓库中搜索 canary 特征串；命中即本轮证据作废；
- 轮换后旧 canary 退役但保留历史 verdict，不能删除失败记录。

### 5.2 分层节奏

| 层 | 频率 | 内容 | 阻断条件 |
|---|---|---|---|
| L-A 提交级 | 每次 commit | 编译、单测、J 抽样（≥100）、E 门禁 | 任一失败 |
| L-B 夜间 | 每日 | 402 全量 import + J 全量语义差分（分片）+ 变异抽样 | `DIFF > 0` 或 `INCONCLUSIVE > 0` |
| L-C 周级 | 每周 | 全量 fuzz（≥4 CPU 小时）+ 规则覆盖引理 + 24 金丝雀 | 新反例/规则缺口/金丝雀失败 |
| L-D 发布级 | 每次发布 | G1–G6 全量 + 独立审计 + 双读数台账 | 任一门槛不满足 |

预算参数（4 CPU 小时、24 金丝雀、≥100 抽样）写入 `roadmap.md` 并由变更控制；降低预算必须记录理由，不能静默缩水。

### 5.3 证据保留

- 证据以 **JSONL + 内容寻址**保存：每条记录含五元组 sha、输入 seed、命令、退出码、耗时、工具版本；
- 只保留「绿」的汇总视为无效证据；必须保留失败、跳过、超时、`N/A`、最小复现；
- 证据目录按 `rounds/roundN/evidence/` 或 CI artifact 归档，保留期 ≥1 年；
- 任何读数必须可由「命令 + seed + 版本」重放；不可重放的读数降级为「观察」。

### 5.4 停止条件

fuzz 不是无限跑：

- 达到声明预算（≥4 CPU 小时/周）且连续 4 小时无新 `DIFF`；
- 覆盖率连续 2 轮无增长；
- 新失败率低于阈值但**不为 0** ⇒ 仍不得称完备，只能报「未发现新反例」；
- 任何 `DIFF` 必须最小化、登记、修复或明确挂账后才可结束本轮。

---

## §6 可证伪门槛（G1–G6）

任何「完备」结论必须**同时**满足：

| 门槛 | 条件 | 读数来源 | 当前 |
|---|---|---|---|
| **G1 判定空间覆盖** | `covered_5tuple = 1556`，`probe_only=0`、`n/a=0`、`unexecuted=0`、`inconclusive=0`；且 `covered+probe_only+unexecuted+n/a+inconclusive = J_total`；`excluded_slots` 已审计且不入分母 | 升级后的 `coverage_checker` | **不可评**：旧 976 仅 probe-only；五元组检查器未实现 |
| **G2a 语义差分 J** | J v1 全 1556 条 `modeled`；`DIFF=0`、`INCONCLUSIVE=0`、`N/A=0`；签名绑定/`body_reached` 全通过 | `semantic_diff` | 未建立 |
| **G2b 语义差分 402** | 402 个 `artifact_import` case + 每个可建模 code object 函数级 case；`DIFF=0`、`INCONCLUSIVE=0`、`N/A=0`；`N/A` 不为 0 则本门槛不通过 | `semantic_diff` | 未建立；旧 `4/46` 不是本门槛读数 |
| **G2c 语义差分 真实项目** | 46 个语料外 pyc；`DIFF=0`、`PRODUCT_ERROR=0`、`INCONCLUSIVE=0`；8 类特性各 ≥1 真实样本；`except*` 缺口显式保留 | `semantic_diff` + offcorpus 台账 | 未建立；7/46 不可编译、0 个真实 `except*` |
| **G3 变异测试** | `accepted>0`；`survived=0`；`equivalent` 仅有机器可检证明；`false_kill=0`；`invalid`/分母公开 | `mutation_test` + `semantic_diff` | 未建立；旧 366/1311=27.92% 是结构判据读数，不是 G3 |
| **G4 规则覆盖** | `total_rules = |rule_universe| > 0`（独立枚举，不由 manifest 自定）；`unmapped_anchors=0`、`orphan_rules=0`；每条规则正/反例、域/守卫/组合覆盖；`proved=total` | 独立规则枚举器 + `rule_manifest` + checker | 未建立；0 条完成；`0/0` 记 `INCONCLUSIVE` |
| **G5 回归门禁** | 402 八分片 6617/6617、small34 1568/1568、quotation 153/153、tests 基线、IV.2 全绿 | E 门禁 | 当前基线绿，但只证明回归 |
| **G6 金丝雀** | 24 条隐藏探针全 `EQUAL`；泄漏扫描 0；独立保管与轮换记录完整 | canary runner | 未建立 |

**判定规则**：

- **J 门槛达标** = G1 + G2a + G3 + G4 + G5 + G6 全满足；此时只能写「J 门槛达标（J v1 / CPython 3.11.7 / 日期 / commit）」，不得简称「完备」；
- **语料完备** = J 门槛达标 + G2b（`N/A=0`）+ G2c 全绿；此时才可写「语料完备」；
- **完备（不加限定）** = 仅指「语料完备」；不得用「J 门槛达标」或「形态基线达成」冒充；
- 任一不满足 ⇒ 只能写「形态基线达成」或「未发现反例」；
- `G5` 单独绿不代表任何语义完备；L4 已证 100% 语料绿可伴随 8.70% 语料外绿；
- `G2` 的 `INCONCLUSIVE` 必须为 0；把超时/环境缺失算绿是本方法明确禁止的；
- `G3` 的 `accepted=0`、`G4` 的 `total_rules=0`、`G2b` 的 `N/A>0` 都只能记 `INCONCLUSIVE`/未通过，不能记绿。

---

## §7 双读数与台账

### 7.1 两套读数

```
形态基线占比 = 完备形态数 / 128
判定空间占比 = covered_5tuple / J_total
```

同时附：

```
语义差分 J：EQUAL / DIFF / INCONCLUSIVE / N/A / ERROR
语义差分 402：artifact_import EQUAL / DIFF / INCONCLUSIVE / N/A / ERROR
语义差分 真实项目：46 总数 / 7 不可编译 / 14 差异（24/46 子集、56 探针）/ INCONCLUSIVE / ERROR
变异：killed / survived / equivalent(proved) / invalid / false_kill；accepted 分母
规则：proved_rules / total_rules；unmapped_anchors；orphan_rules
证据：405 stamp 文件 / 404 stamp 名 / 3342 记录 / 197 产物；源 0/402
```

### 7.2 报告模板（任何页面/文档必须同时出现）

```
[形态基线] 128/128 = 100%（v8 口径，仅形态清单；不等于语义完备）
[判定空间] covered_5tuple/1556 = ?；probe_only=976；unexecuted=?；N/A=?；inconclusive=?；excluded_slots=?
[空间不变式] covered+probe_only+unexecuted+N/A+inconclusive = 1556；excluded_slots 不入分母
[语义差分 J] EQUAL=?/1556；DIFF=?；INCONCLUSIVE=?；N/A=?；ERROR=?
[语义差分 402] import EQUAL=?/402；code-object modeled=?/6617；DIFF=?；INCONCLUSIVE=?；N/A=?；ERROR=?
[语义差分 真实项目] 46 个；不可编译 7/46=15.22%；执行差异 14/56（24/46 子集）；except* 真实样本 0；INCONCLUSIVE=?；ERROR=?
[变异测试] killed=?/accepted；survived=?；equivalent(proved)=?；invalid=?；false_kill=?
[规则覆盖] proved=?/total；total>0；unmapped_anchors=?；orphan_rules=?
[证据链] 405 stamps/404 名/3342 记录/197 产物；源可用 0/402；执行抽样假阳性 12/21=57.1%
[旧结构判据] 4/46=8.70% 判据绿；7/46=15.22% 不可编译（历史，不进入 G2；12/21 不属此行）
[回归门禁] 6617/6617；1568/1568；153/153；tests 基线；IV.2
[结论] 形态基线达成；J 门槛达标/语料完备未达成
```

- 两读数**分列不互替**；禁止用 `128/128` 推导「J 门槛达标」，也禁止用 `J` 百分比反推 128；
- v8 的 `128/128` 保留为历史口径，台账中标注「历史 / 非完备证据」；
- 任何「完备」结论必须附 G1–G6 的原始证据路径，而不是只写一句 100%。

---

## §8 攻击式评审（第三轮有条件通过；2 项已修）

首轮独立红队评审结论为 **不通过（revise & re-review）**；第二轮复审仍为 **不通过**，指出 Task 9 未承接 S4–S6、G4 对账可自证、G2 输入无效可假绿、G3 分母不可计算、术语/R7/模板残余；第三轮复审为 **有条件通过**，要求统一术语并修正 G3 集合划分。全文与逐条意见见 `METHOD_REVIEW.md`。v3 已补：Task 9 扩为 9.1–9.7、独立 `rule_universe`、`signature_binding`/`body_reached`、G3 公式/等价证明、R7 白名单、术语与模板；第三轮 2 项已修。

首轮 5 项阻断的 v2 处置：

| 首轮反对意见 | v2/v3 处置 |
|---|---|
| G2 没有输入模型，402/tests 可能空真 | 新增 G2a/G2b/G2c 与 `semantic_case`（入口/输入/超时/观测集）；`N/A` 单列，不得冒充绿 |
| 把旧判据 `4/46` 当语义绿 | `4/46`、`7/46` 移入「旧结构判据（历史）」；`12/21` 单列「执行抽样假阳性」；G2 只认 `EQUAL/DIFF/INCONCLUSIVE` |
| G3 用旧结构变异、等价变异体可缩分母 | G3 改用 `semantic_diff` oracle；`equivalent` 必须机器可检证明，否则归入非等价集 `N`，按 oracle 结果进 `killed`/`survived` |
| G4 `0/0` 空真、覆盖引理过弱 | `total_rules>0`；manifest 双向对账；正/反例 + 域/守卫/组合见证；`0/0` 记 `INCONCLUSIVE` |
| G1 检查器仍是 probe-only、J 缺字段 | 五元组 C1–C5 输出；J 补 `source/expected_label/input_model/entrypoint/excluded`；976 不计入 covered |
| 缺元数据/ABI、真实项目维度 | 新增 R7（docstring/annotations/signature/defaults/`co_*`/身份/装饰器顺序/别名图）与 G2c（46 个真实 pyc） |
| 报告模板只列绿读数 | 模板加入 `0/402`、`4/46`、`7/46`、`14/56`、`12/21`、`405/3342/197`、`N/A`、`INCONCLUSIVE` |
| 预写「有条件通过」 | 删除预写结论；第一/二轮不通过、第三轮有条件通过全部留档；第三轮 2 项修正后 Task 8.1–8.3 可签收 |

第三轮有条件通过后仍保留的风险：

- J 的 299/408 槽、584 单元是否足以支撑「判定空间」仍需独立充分性审查；
- G2b 的 `N/A=0` 可能难以达成；若最终不可达，只能永久保留「J 门槛达标」，不得改口径；
- `proved` 仍是工程证明，不是定理证明；任何对外文本必须保留这一限定。

---

## §9 实施路线图（详见 `roadmap.md`）

| 阶段 | 交付 | 验收读数 | 预算（工程日） | 回退条件 |
|---|---|---|---|---|
| S1 | J v1 生成器固化 + 五元组检查器 + `excluded[]` | `covered_5tuple` 可复算；检查器正/反例自测通过 | 4 | 生成器不能复现 → 回退手工清单并冻结 |
| S2 | `semantic_diff.py` MVP（pyc 直接加载 + R1–R5/R7） | 100 条 J 用例 `DIFF=0`、`INCONCLUSIVE=0`、`N/A=0` | 6 | 沙箱不稳定 → 缩小输入类并显式降级，不缩 J |
| S3 | `mutation_test.py` + ≥12 类变异 + 等价证明 | 漏检/误杀读数；每个漏检登记盲区 | 5 | 误报率高 → 先修 harness，不修判据 |
| S4 | `rule_manifest.json` + 独立 `rule_universe` + 锚点对账 + 覆盖引理 | `total_rules=|rule_universe|>0`；`unmapped=0`；正/反例/组合见证 | 7 | 独立枚举失败 → G4 记 `INCONCLUSIVE`，不改 J 分母 |
| S5 | fuzz + 最小化 + 24 金丝雀 | 新反例 0 或已最小化登记；canary 全绿 | 6 | 崩溃不可复现 → 保留原始输入与 seed |
| S6 | CI/E 门禁 + 双读数 + v9 台账 + 独立审计 | G1–G6 + 原有 E 门禁 | 4 | 任一失败 → 发布阻断 |

预算为初始估算，由变更控制调整；不能以预算不足为由降低 G1–G6 口径。

---

## §10 不变量、破口映射与迁移

### 10.1 不变量

- `tests/` 零改动；402 认证产物零回退（`compare REGRESSIONS=0`）；
- I.4 白名单、G3=0 新增前缀、G4=0 硬编码上限沿用；
- 128 形态基线保留，不删除、不改写历史；v9 双读数并列；
- 任何超出 3.11.7 / J v1 的结论，必须另立版本并重跑 G1–G6。

### 10.2 破口 → 门槛映射（方法级）

| 破口组 | 关键项 | 归属支柱/门槛 |
|---|---|---|
| L0 归纳/区域 | B163、B172 三元组合、B173/B174 双归属、B175 守卫闭包、B176 文本不一致 | O1/O2/O3/O6；G4；B172 三元组强制进入 J |
| L1 度量 | B164–B171（128 非互斥、`arg/arguments` 漏项、B170 probe-only） | G1；J schema；P7；B171 形参/签名进入 J 或 R7 |
| L0 字段 | B171（L(A) 字段与 14 类通道） | O4/O7；rule manifest 的 anchor/invariant |
| L2 判据 | B195–B201（handler 删除、arg 槽缺失、值语义、docstring、漂移） | R7；G2/G3；P2 |
| L3 机制 | B179–B194（族特化、抢归属、深度塌陷、守卫交互） | O1–O7；G4；三元组/深度 D2 |
| L4 运行 | B202–B213（编译失败、局部/分支/try/finally/continue、元数据、规模、`except*` 缺口） | G2b/G2c；O5/O6；B213 显式缺口 |
| L5 证据 | B214 源 0/402、B215 自证、B216 语料偏差、B217 平面盲区、B218 单元指标、B219 分母膨胀 | P3/P4/P6；G1/G2/G6；报告模板 |
| 未决项 | U-01 归纳基、U-02 守卫死代码、U-03 双读数、U-04 零能力、U-05 for×match、U-06 独立 oracle | G4；O3；§7；G2；O6；G6 |

> 本表是方法级映射；B163–B219 的逐条封闭状态仍在 v9 台账中维护，Task 10 完成逐条签收。不得以本表替代逐条登记。

---

## §11 结论

本方法把「完备」从一句不可证伪的口号，改为**分层门槛 + 两套分列读数 + 四类证据**：

1. 判定空间必须**有限、可枚举、五元组覆盖**，且 `excluded` 可审计；
2. 判据必须以**执行级语义差分**为主，结构判据只做分诊；
3. 每条规则必须承担**不变式 + 覆盖引理 + 组合义务**；
4. 证据必须**分层、可重放、去重、保留失败**；
5. 任何一项不满足，结论只能写成**形态基线达成**；满足 J 层但未满足语料层，只能写「J 门槛达标」；
6. 当前状态：**形态基线达成；J 门槛达标/语料完备均未达成**。前两轮评审不通过，第三轮有条件通过且 2 项条件已修；Task 8.1–8.4 完成（`98e77821` + `3f43c965` 已 push）；下一步按 `roadmap.md` 落地工具并以 G1–G6 复验。
