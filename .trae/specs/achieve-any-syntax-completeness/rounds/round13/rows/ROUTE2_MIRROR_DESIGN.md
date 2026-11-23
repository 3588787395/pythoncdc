# DESIGN（设计草稿）— Task 122.14「镜像异常等价」裁决

日期：2026-11-23（Asia/Shanghai）。撰写代理：设计子代理（受父代理委派）。
仓库：`F:\Downloads\pythoncdc-main`（main，**只读，零改动**——本文件与全部探针产物均位于 `D:\temp`，仓库内未新增/修改/删除任何文件，未 commit/push）。
本文件性质：**设计草稿，供父代理裁决**。不预设结论；行 2 状态的最终定性（含新 verdict 是否引入、是否计入阈值）**裁决权归父代理**。

---

## 0. 任务与范围

- 任务（tasks.md 122.14，L2230–2234 原文要点）：「原始与产物两侧模块级同异常（类型＋消息一致）⇒ 模块边界内等价证据……判定语义变更＝judge 裁决项：需先出设计（新 verdict 词表、与 `unresolved=0` 阈值的映射、证据强度如实分级——镜像异常只证 import 链重建忠实至墙，不证墙后语义），经 t31 全量数据定范围后实施。」
- 本设计覆盖方案空间 A（新 verdict）/ B（Linux 宿主路线）/ C（维持 unresolved＋边界声明）/ D（混合 C＋A），每项含：规格字面符合性（逐字引用行 2 阈值并正面回答「镜像类条目的 R1–R7 从未测量怎么定性」）、证据强度分级、实施草图（semantic_diff.py 哪一层、verdict 词表扩展、下游 SEMANTIC_J_FULL/checklist 计数）、验证计划（judge_sha256 变更处置、回归守卫）、失败模式。
- 范围占位：t31 全量复测在飞（旧 judge）。本设计的镜面人口规模、签名分布等**均以占位符（【t31 回填】）标注**，不依赖 t31 精确数字；t31 数据落地后由父代理回填再裁决（第 9 节问题清单）。

## 1. 事实基础

### 1.1 观察（直接证据，均可复核）

**墙的收敛史（四层）：**
1. 第 1 层 package_root 布线缺失 → runner v1.1.0 修复（`semantic_runner.py` `resolve_package_root` auto 模式，L222–224 CLI 帮助文本；布线写入 case 双侧 `semantic_diff.py` runner 侧 L174–179）。
2. 第 2 层 logbook/tornado 缺失 → vendor（rr-v5r197）。
3. 第 3 层 zmq 缺失 → vendor pyzmq 27.3.0＋typing_extensions 4.16.0（rr-v5r198，PROVENANCE_v3.md §1）。
4. 第 4 层（现墙）：`ModuleNotFoundError: No module named 'IQCommon.data.TickDataCache'`。`IQCommon.data.TickDataCache` 为公司内部 Cython 扩展，语料内唯一制品 `site-packages/IQCommon/data/TickDataCache.cpython-311-x86_64-linux-gnu.so`（2,753,976 B，ELF，Linux x86_64）。Windows CPython `EXTENSION_SUFFIXES` 不含 `.so` → 结构性不可装载。非 PyPI、无源码、构建被禁 → vendor 路线封闭（PROVENANCE_v3.md §2.4 结论）。

**37 样本 v3 复测（vendor 后，sample_out_v3.json）：** 37 条 = EQUAL 10 / ERROR 27；judge_sha256 `d31948b3a0a4336078d3e031467fa942947c358ecc7584c5194bd389d1a9cc38`；翻转表 v2→v3 全等（EQUAL→EQUAL 10、ERROR→ERROR 27）；守卫四断言 PASS。

**残留 27 条的底层探针（probe_underlying_v3.json）：** 27/27 **全部同一异常签名**：`type: "builtins.ModuleNotFoundError"`、`message: "No module named 'IQCommon.data.TickDataCache'"`、ok=false、timeout=null、returncode 0、stdout/stderr 空、无挂起，elapsed 3.5–21.8 s。条目覆盖 15+ 个语法族（IF/BOOLOP/IFEXP/TRY/RAISE/IMPORT/LISTCOMP/WITH/BREAK/CONTINUE/WHILE/AUGASSIGN）。
- 注意：该探针**只测原始侧**（probe_all_v3.py 只调 `sd._run_side(case2, 'original', ...)`）。产物侧失败证据目前只存在于判定器进程内（见 1.2 推断 3），未单独落盘。

**本轮新增抽样核验（本子代理，只读）：**
- 27 条 ERROR 记录中 **c3.product 与 c1.source 逐条字节一致者仅 4/27**（其余 23 条产物与 round9 eqsrc 快照 sha 不同——反编译器/产物生成路径与快照代次不同）。⇒ 镜像主张**不能**靠「产物＝已记录源码」的字节同一性 shortcut，必须靠行为证据。
- 27/27 条 `input_model.calls` 为空（module-only 人口）；27/27 条带 `package_root` 字段。
- 语料内 Linux `.so` 共 9 个：8× `cpython-311-x86_64-linux-gnu`（TickDataCache/CTPEngine/Exrights/L2DataCache/NetEngine/pycrypto/pyKLine/ReferenceCache，均在 IQCommon/data）＋1× `cpython-35m`（fly/common/pycrypto，**CPython 3.5 ABI 标签，3.11 宿主任何平台都不可装载**）。

**判定器结构（semantic_diff.py，行号以当前 HEAD 为准）：**
- L44：verdict 常量 `EQUAL, DIFFERENT, INCONCLUSIVE, ERROR`；TOOL_VERSION "1.0.0"。
- L944–947：原始侧超时 → INCONCLUSIVE（优先于一切失败分类）。
- L948–955：原始侧装载/执行失败 → **无条件 ERROR**（`errors.append("original artifact did not load/execute")` 或 harness_error 分支后早退）。**这是镜像规则的唯一插入点。**
- L957–965：产物侧失败 → LOAD diff（→ DIFFERENT）；判定器对两侧失败**天生不对称**（原始失败＝环境问题→ERROR；产物失败＝产物问题→DIFFERENT）。
- L795–800（worker）：装载失败捕获 `result["error"] = exception_info(exc)`＋traceback；`harness_error=True` 仅当异常类型**不在**白名单 `(ImportError, AttributeError, NameError, TypeError, ValueError, RuntimeError, SyntaxError, OSError)`。ModuleNotFoundError ⊂ ImportError → 白名单内 → harness_error=False。
- L812–815（worker）：`_scrub` 只替换 workdir→`<cwd>`、harness 目录→`<harness>`。⇒ **traceback 文本两侧必然不同**（原始侧含 pyc 路径，产物侧含产物 .py 路径，且 co_filename 分别为 `./fly_docker_py311/...` 与产物落盘路径）——镜像谓词只能基于 `exception_info`（type/args/message/cause/context），不能含 traceback。
- L1110：`_summary` 计数按四词表零初始化（新词表需增行，否则不进汇总头）。
- L1116–1123：CLI `_exit_code`：ERROR→3、INCONCLUSIVE→2、DIFFERENT→1、否则 0。
- `_load_target` L582–583：`sys.path.insert(0, package_root)`——判定器内唯一语料特化布线机制，已存在，镜像规则**不得**新增任何 site-packages 特判。

**runner 结构（semantic_runner.py）：**
- L25–30：`EXIT_FOR_STATUS`（EQUAL:0/DIFFERENT:1/INCONCLUSIVE:2/ERROR:3）。
- L185：`verdict = result.get("status") if result.get("status") in EXIT_FOR_STATUS else sd.ERROR` —— **静默强制门：判定器返回未知 verdict 会被无声改写为 ERROR**。不改此行则整个新词表不可见。这是实施草图中最重要的单点。
- L186–191：c4 装配（verdict/seed/exit_code/diffs/errors/inconclusive——c4 只拷贝判定器结果的选定键）。
- L192–194：c5（含 judge_sha256、runner_version）。
- L195–203：status 映射：INCONCLUSIVE/ERROR → `unexecuted`；无 calls → `probe_only`＋reason `module_only`；有 calls → `covered_5tuple`。
- L263–268：verdict 计数（`.get` 模式，新词表不炸）；module_only/covered 计数按 reason/status。
- L286：exit 3 iff 有 ERROR；镜像 verdict 不触发 3。

**下游消费方：**
- `coverage_checker.py` L42 `VERDICTS`（闭元组）、L44 `NON_COVERED`。
- `mutation_test.py` L411–415：基线 `!= sd.EQUAL` → `ABORTED_BASELINE`（镜像基线同样 abort → 沿 G3 unjudgeable 惯例，不产生语义漂移）。
- `SEMANTIC_J_FULL.md`（行读数文档）、`checklist.md` L158（行 2 状态）、`REACHABILITY.md` L29（行文本，冻结于规格）。

**冻结基线（REACHABILITY.md L101 原文要点）：** 冻结对象＝`scripts/pyc_verify.py` 及其装载的 `pylingual/equivalence_check.py::compare_pyc`（字节、行为、容差、verdict 语义全部不变）；「执行级语义差分只能以新增工具 `tools/completeness/semantic_diff.py` 作为附加判据」。⇒ **semantic_diff.py 不在冻结表内**；其治理工具是 c5.judge_sha256 的逐记录留痕＋回归守卫，不是字节冻结。

**t31 时序：** t31 在飞，使用旧 judge（sha `d31948b3…`）。runner 在启动时计算 judge_sha256 一次（L232），进程内不重读——**但若在 t31 运行期间编辑 semantic_diff.py，后续记录携带新 sha，会把一次运行劈成两代**。⇒ 实施必须排在 t31 结束之后（第 8 节时序）。

### 1.2 推断（由观察支撑的结论，标注强度）

1. **（强）镜像类人口的真实根因是「语料制品平台缺口」，与反编译器质量无关。** 依据：27/27 同签名、同根因链、原始侧证据独立于产物侧存在。
2. **（强）产物侧必然以同异常失败。** 依据：产物（产物 .py 经 SourceFileLoader）与原始 pyc 在同一 `package_root` 布线下执行**同一模块级 import 链**（IQCommon.common → zmq/logbook/tornado → TickDataCache）；墙位于两者共同的传递依赖上，且 4/27 字节同一性＋全部 27 条经判定器双侧跑过（产物 worker 结果被算出后丢弃，见推断 3）。但注意「必然」是结构性推断；**设计要求把产物侧失败从推断升格为实测落盘证据**（第 5.1 节）。
3. **（强）产物侧失败证据目前是易失的。** judge_case 在 L948–955 早退时，`product` dict（含产物 worker 的 ok/phase/error/exception_info）在进程内已知但既不写入 c4（L186–191 只拷选定键）也不写入探针文件。runner 记录只有 `c4.errors` 文案。⇒ **离线重分类不可能**：旧记录（t30/t31）无法事后改判镜像——必须用新 judge 重新双侧测量。
4. **（中）镜像类人口全部为 module-only/无 calls。** 样本 27/27 无 calls；t30 的 374 条 site-packages ERROR 属 excluded＋无 calls 人口（J 空间 excluded 条目无 calls；`calls_missing_non_excluded=0`）。全量确认留待 t31 回填（第 9 节问题 7）。若成立 ⇒ 镜像 verdict **对 covered_5tuple 覆盖率零影响**（该人口即使无墙也只是 module-import 证据，永远进不了覆盖分子）。
5. **（中）Linux 宿主路线（方案 B）不保证消灭墙。** 8 个 cp311 `.so` 在 Linux 可被 import 系统识别，但 init 期行为未知（系统库依赖、网络/资源访问、更深内部依赖均未验证）；cp35m pycrypto 在 3.11 上任何平台都不可装载；且 pyc 的 co_filename（`./fly_docker_py311/...`）证明**语料原生环境是 Linux**——这是 B 的正面论据，与 B 的成本/可比性问题并存（第 5.2 节如实并列）。

## 2. 规格文本与术语操作化现状

### 2.1 REACHABILITY.md 行 2 阈值（逐字引用，不改写）

> `unresolved = 0`；C1–C5 齐全；R1–R7 无未裁决失败

行 2 输入来源（逐字引用）：「J 空间（五个维度，1556 条）+ 402 语料 + 46 真实 pyc」。
行 2 生成/执行方式（逐字引用）：「`tools/completeness/semantic_runner.py` + `tools/completeness/semantic_diff.py`（R1–R7：返回值/stdout/stderr/事件序/副作用/异常/元数据）」。

### 2.2 关键观察：REACHABILITY 原文内无这三个术语的定义

对 REACHABILITY.md 全文检索：`unresolved`、`未解决`、`未裁决`、`C1–C5` 的解释均**只出现在行 2 阈值单元格里**，表内/表外无定义区。三个子句的操作化全部由下游行读数文档确立：

| 术语 | 操作化出处 | 操作化定义 |
|---|---|---|
| unresolved（未解决） | SEMANTIC_J_FULL.md L72 | 「未解决（ERROR+INCONCLUSIVE+NO_C4）= 442（374 包根缺失 + 48 探针 ERROR + 18 超时 + 2 反编译失败）」 |
| 「R1–R7 无未裁决失败」 | SEMANTIC_J_FULL.md L75–76 | 「30 条已裁决 DIFFERENT（已决失败，如实保留，不混入未裁决）；未裁决 442 条」——即已裁决失败（DIFFERENT）允许存在且不计入「未裁决」 |
| 「C1–C5 齐全」 | SEMANTIC_J_FULL.md L74 | 「`covered_5tuple=395/1556`；module_only 719 条按定义不计覆盖」——行读数以 covered_5tuple 口径读该子句 |

推论（中等强度）：**「unresolved = 0」的度量延展（哪些 verdict 计入）是行读数层面的操作化选择，不是 REACHABILITY 字面文本的改动**。引入新 verdict 不改行文本一个字，但会改变操作化定义的外延——因此**旧/新两种读数必须同时公布**（第 7 节纪律 2）。

## 3. 核心定性问题：镜像类条目的 R1–R7 从未测量，怎么定性？

这是四个方案都必须正面回答的问题。答案分三层：

**第一层（观察）：测量面在墙处截断。** judge_case 对该类条目在 L948–955 早退——早退发生在任何 R1–R7 比较之前。R1（返回值）未测：人口无 calls（27/27，见 1.2 推断 4）；R2/R3（stdout/stderr）模块装载期已测（27/27 为空）；R4（事件序）装载期已测（空）；R5（副作用/命名空间值）未测（模块未装载完成）；R6（异常）模块级顶层异常已测（27/27 同签名）；R7（元数据）未测（无可比 code object）。

**第二层（定性）：该类是「测量面截断」，不是「R1–R7 失败」。** 在已测面内：无可判不同的维度，且唯一可观测结果（模块级异常）两侧一致。在未测面内：既无失败证据，也无「无失败」的证据——**「未测量」≠「无失败」，也不得写成「已裁决无失败」**。诚实的定性语句只有：**「已测面（装载结果＋模块级异常签名）全部测量且裁决等价；未测面（墙后语义/R1/R5/R7）因语料平台缺口在本宿主不可测」**。

**第三层（对阈值子句的两种读法，裁决点）：**
- **严格读法**：「R1–R7 无未裁决失败」要求 R1–R7 七维全部有裁决记录。镜像类 R1/R5/R7 无裁决记录 ⇒ 子句不满足 ⇒ 行 2 不满足。此读法下任何 verdict 词表扩展都不救行 2；只有消灭墙（方案 B 成功）才行。
- **边界读法**：子句约束的是「未裁决的失败」——已测面内无未裁决失败（异常已裁决等价），未测面内无已知失败且其不可测性作为环境边界**显式声明**（墙的四层证据＋EXTENSION_SUFFIXES 结构性论证）。此读法下镜像类不构成对子句的违反，但必须以边界声明＋单列为前提，不得默认。
- 两读法不冲突地并存的方式：行读数文档**同时公布两套口径**（第 7 节），行状态以严格口径为标题口径，边界口径下的达成判定留给父代理显式裁决——与 G4_REVIEW_PACKET「裁决之前 G4 保持 FAIL」的惯例同构。

## 4. 方案空间总览

| 方案 | 一句话 | 改判定器 | 改行文本 | 新证据 | 行 2 严格读法下 | 行 2 边界读法下 |
|---|---|---|---|---|---|---|
| A | 判定器新增 verdict `MIRRORED_EXCEPTION` | 是 | 否 | 产物侧镜像行为实测落盘 | 仍未达成（镜像仍算未解决） | 可达成（镜像单列为边界裁决类） |
| B | WSL2/Linux Py3.11 全链复测消灭墙 | 否（换宿主） | 否 | 墙后真实语义（若墙真消灭） | 可达成（若全解） | 可达成 |
| C | 维持 unresolved，墙写成规格化边界声明 | 否 | 否 | 无新增 | 永不达成（本宿主） | 不达成（只声明不裁决） |
| D | C＋A 混合：边界声明＋镜像 verdict＋双口径 | 是 | 否 | 同 A | 仍未达成 | 可达成（裁决后） |

四方案都**不改 REACHABILITY.md 行 2 文本**；差别在 judge 行为、读数口径与声明形式。

## 5. 方案详述

### 5.1 方案 A：判定器扩展新 verdict（「镜像异常等价」）

**语义**：原始与产物两侧均在 `phase="load"` 失败、均非 harness_error、均非超时、且 `exception_info` 规范化全等（type/args/message/cause/context 链）⇒ verdict `MIRRORED_EXCEPTION`。与四词表并列、单独计数、**不计入 EQUAL、不进覆盖分子**。

**5.1.1 规格字面符合性**
- `unresolved = 0`：新 verdict 不改行文本；在 L72 操作化定义下，镜像类离开「ERROR+INCONCLUSIVE+NO_C4」集合 ⇒ 未解决数下降。**必须同时公布旧口径（镜像计入未解决）与新口径（镜像单列）两个读数**（第 7 节纪律 2）。A 单独不使阈值达成——只把「无证据」转化为「边界内已裁决证据」；达成与否取决于父代理对边界读法的裁决（即 A 是 D 的构件）。
- C1–C5 齐全：镜像记录保留 c1–c5 全部五字段（装载失败≠证据缺失：c1/c2/c3/c5 照常，c4.verdict 有值）。covered_5tuple **零变化**（镜像人口 module-only，见 1.2 推断 4）——覆盖计数零通胀。
- R1–R7 无未裁决失败：按第 3 节三层定性执行——已测面裁决（R6 模块级异常等价；R2/R3/R4 装载期已测如实记录），未测面显式声明。**不得写「R1–R7 已裁决」**，只能写「R6（模块级）＋装载期 R2/R3/R4 已测已裁；R1/R5/R7 未测（墙）」。
- 与「R1–R7 无未裁决失败」「C1–C5 齐全」的冲突判定：严格读法下 A 不解决 R1/R5/R7 无裁决记录的问题（冲突仍在）；边界读法下以单列＋声明化解（无冲突但需显式裁决）。设计不隐藏这一分歧。

**5.1.2 证据强度分级（如实）**
- **证明（强，直接行为证据）**：产物的模块级 import 链至少重建忠实至失败点——产物（重编译源码，非原字节码）走过同一依赖链（zmq→logbook/tornado→TickDataCache）并以相同异常签名死在同一缺失模块上。这是模块语义的非平凡子集（丢失/错序/改写 import 的反编译产物会失败得不同或成功），构成**墙前 import 链忠实性**的正证据。
- **证明（中）**：条目的失败归因稳定为「环境×语料」而非「反编译变换」——两侧同墙说明失败是环境属性。
- **不证明**：① 墙后模块体语义（本宿主从未执行）；② R1 calls 行为（人口无 calls——是 J 条目属性，非镜像规则局限；但即使有 calls 的墙类条目，镜像也不覆盖 call 面）；③ R7 code object 保真（无可比对象）；④ 无墙宿主上的行为一致性（在 Linux 上 TickDataCache 会 import **成功**，墙后行为两侧均未测）。镜像证据是**环境相对的**：它证明的是「本环境下等价失败」，这恰是其诚实边界。
- **反向证据价值（设计增益）**：产物**不**镜像（异常不同/产物装载成功而原始失败）时，规则记为非镜像 ⇒ 那是 import 链不忠实的真实信号（如反编译丢 import）。规则因此是双向出证据的，不是单向豁免通道。

**5.1.3 实施草图（t31 结束后才动手，见 5.1.5 时序）**

semantic_diff.py（judge 层）：
1. L44 词表：新增常量 `MIRRORED_EXCEPTION`（候选名，裁决点 1；备选 `MIRROR_EXCEPTION`/`IMPORT_MIRROR`；**禁止含 "EQUAL" 字样**）。TOOL_VERSION "1.0.0"→"1.1.0"。
2. judge_case L948–955 改造（唯一插入点，严格增量）：
   - 前置不变：原始侧超时→INCONCLUSIVE（L944–947）优先；原始侧 harness_error→ERROR 不受镜像规则影响。
   - 镜像谓词（全部满足才授级）：`not original.ok and not original.harness_error and original.phase=="load"`；`product` 同侧三条件（产物超时优先于镜像判定——产物超时＋原始失败维持现行 ERROR 早退顺序，不改）；两侧 `exception_info` 经既有 canon 机制规范化全等；**v1 限定异常族＝ImportError 子类**（ModuleNotFoundError 含于内；现墙类。允许任意白名单异常会把「两侧同 ValueError」也授级——主张超出 import 链忠实性，v1 不做，裁决点 2）。
   - 谓词成立 ⇒ `_result(case, MIRRORED_EXCEPTION, ...)`，附镜像证据块：`mirror = {phase: "load", original_exception, product_exception, boundary: "module_load"}`；**errors 列表保持空**（非 ERROR verdict 不得携带 errors——维护 `_summary`/下游不变式）；旧文案 `"original artifact did not load/execute"` 移入镜像块作 `original_error_label`（审计连续性）。
   - 谓词不成立 ⇒ 原 ERROR 路径逐字节不变（errors 文案、diffs、返回结构）——**ERROR 记录零字节漂移**，使守卫 5.1.5-1 干净。
   - R2/R3/R4/R5 装载期可观察量（装载期 stdout/stderr、import 事件、files_final）**如实比较并记入镜像块**（equal/diverged 标记），**不作为谓词必要条件**（裁决点 3；理由：流文本可能含仅 workdir/harness 被洗、路径相关的环境噪声，若作为硬条件会因无关噪声错拒镜像；验证词表的主张只有「装载结果＋顶层异常签名等价」，不主张全边界等价）。
   - traceback 不进谓词（1.1 节：两侧 co_filename 结构性不同）。
3. `_summary` L1110 零初始化元组加入新词表；`_exit_code` L1116–1123 新增映射（推荐 exit 4，备选 2，裁决点 4；理由：4 与四遗留码零重叠，c4.exit_code 使跨代翻转在两字段可见）。

semantic_runner.py（runner 层）：
4. `EXIT_FOR_STATUS`（L25–30）加入 `MIRRORED_EXCEPTION: 4`——**不改此行则 L185 静默强制门把新词表吞成 ERROR，整个改动不可见**（本草图最重要单点）。TOOL_VERSION "1.1.0"→"1.2.0"。
5. L186–191 c4 装配：镜像 verdict 时把判定器镜像块拷入 `c4.mirror`（其余键照旧）。
6. L195–203 status 映射：镜像＋无 calls ⇒ `status="unexecuted"`、`reason="mirror_exception"`（**不进 module_only、不进 covered_5tuple、不进 probe_only**——status 词表稳定，扩展 reason 码；裁决点 5）。镜像＋有 calls（若 t31 出现此人口）⇒ 同样 `unexecuted`＋`mirror_exception_calls`（calls 维度丢弃须单列声明，回填后定，第 9 节问题 7）。
7. L263–268 计数：verdict 计数自动含新键；module_only/covered 计数不触碰；L286 exit 规则不变（有 ERROR 才 3）。

下游：
8. `coverage_checker.py` L42 `VERDICTS` 增加新词表并按 non-covered 处理（否则含镜像 verdict 的证据文件过不了校验）。
9. `mutation_test.py` 零改动（L411–415 基线 abort 语义天然兼容：镜像基线照旧 ABORTED_BASELINE→unjudgeable，沿 G3 惯例）。
10. 文档：SEMANTIC_J_FULL.md 新增人口学行（「镜像异常等价 | N | reason=mirror_exception」）＋双口径未解决数＋边界声明；checklist.md L158 单元格同步双口径；行 2 状态在父代理裁决前保持「未达成（严格口径）」。
11. 冻结零触碰：`scripts/pyc_verify.py`、`pylingual/equivalence_check.py`、`REACHABILITY.md` 行文本、`spec.md` 均不动。

**5.1.4 每条目计数方法（与 G3 先例对齐，见第 6 节）**：镜像条目**单列**（reason 码＋verdict 计数），不进 EQUAL 分子、不进覆盖分子、不伪造成 EQUAL；严格口径 unresolved 含之、边界口径不含之——两口径都公布。

**5.1.5 验证计划**
- **judge_sha256 处置**：semantic_diff.py 字节变更 ⇒ judge_sha256 必变。冻结表不含它（2.2 节），治理＝逐记录留痕＋双代公示：镜像测量记录携带新 sha，行读数文档同时公示 t30/t31 代（`d31948b3…`）与镜像代 sha 及其交叉表。**实施不得在 t31 运行期间进行**（1.1 节时序：会把在飞运行劈成两代）。
- **冻结比较器复核**：改动后重验 `pyc_verify.py`（`FE1902A9…`）与 `pylingual/equivalence_check.py`（`9C7567BD…`）sha 不变。
- **回归守卫（按序）**：
  1. 非镜像路径零漂移：形式不变式——新代码路径仅在 `not original.ok` 分支内可达；该分支旧判恒 ERROR。故对旧判 EQUAL/DIFFERENT/INCONCLUSIVE 的任何 case，新判恒同值；对旧判 ERROR 的 case，新判 ∈ {MIRRORED_EXCEPTION, ERROR} 且非镜像时 c4 逐字段相同。以 37 样本实测断言：10 条 EQUAL 的 c4（verdict/diffs/errors/inconclusive/exit_code）改动前后相同。
  2. 37 样本重跑：允许的唯一翻转＝27 条 ERROR→MIRRORED_EXCEPTION（若谓词全覆盖）；DIFFERENT=0；EQUAL→ERROR 回归=0；c3 产物 sha 不变（去编译确定性）；package_root 字段计数 32 不变。
  3. 守卫重规约（重要）：`--package-root off` 旧守卫（「off 复现旧 ERROR」）在新词表下语义改变——off 模式两侧同死于第 1 层墙（IQEngine 级 ModuleNotFoundError）⇒ 镜像谓词同样成立 ⇒ 返回 MIRRORED_EXCEPTION。新守卫改为：**off 模式镜像块异常消息为第 1 层签名（IQEngine…），auto 模式为第 4 层签名（TickDataCache…）**——布线正确性由异常消息层级差证明，比旧守卫（靠 ERROR verdict）证据更强。此为守卫语义变更，须显式写入守卫文档，不得静默继承。
  4. 突变健全性：一条镜像基线 case 跑 mutation_test → 仍 ABORTED_BASELINE（G3 读数零漂移）。
  5. t30→t31→镜像测量三代交叉表：DIFFERENT 30 / INCONCLUSIVE 18 / NO_C4 2 人口的稳定性逐代对照（不属镜像类，但同表必报）。
- **失败模式**：① 假镜像（两侧因与 import 链忠实性无关的原因同败）——缓解：phase=load＋harness_error=False＋ImportError 族限定＋canon 全等（裁决点 2 收紧面）；② 消费方漏改（L185 静默门）——缓解：第 5.1.3 节消费方清单＋守卫 1；③ 双重计数（镜像被某下游计入 EQUAL/覆盖）——缓解：独立 reason 码＋不触 module_only/covered 计数＋双口径公布；④ 过度声明（行读数把镜像类写成「阈值达成」而无边界声明）——缓解：第 7 节纪律＋行状态裁决前置；⑤ t31 中途改 judge 劈代——缓解：时序约束（先 t31 后实施）。

### 5.2 方案 B：Linux 宿主路线（WSL2/Linux Py3.11 全链复测）

**5.2.1 规格字面符合性**：不改任何规格文本、不改判定器语义、不引入新 verdict——从环境成因上攻击墙。若墙消灭，374 类人口得到**真实** EQUAL/DIFFERENT/ERROR 读数，`unresolved=0` 可以诚实达成，无任何裁决债务。这是 B 的决定性优点。B 与 A 不互斥：B 成功后镜像人口归零，词表自然闲置；B 部分成功（如 cp35m pycrypto 仍不可载）时残留墙仍需 A/C 处置。

**5.2.2 证据强度分级**：B 产出的是全维（墙后 R1–R7）真实读数——强度上限远高于 A 的边界内等价。但注意其为**平台相对**证据：在 Linux 上证明等价 ≠ 在 Windows 上等价（语料 pyc 的 co_filename 为 `./fly_docker_py311/...`，语料原生环境实为 Linux——这是「Linux 读数更忠实于语料」的正面论据，如实记录；反论据：全部既有读数基线均为 Windows 平台，见 5.2.3-3）。

**5.2.3 诚实成本评估**
1. 环境：WSL2/Linux CPython 3.11（.so 的 cp311 ABI 标签要求 3.11.x）；vendor 需 Linux 并行树（logbook/tornado/pyzmq manylinux wheels，PyPI 有；现有 vendor 树全部 win_amd64 制品无效）；VENDOR_DEPS.md 需 Linux 并行节；r197/r198 Windows vendor 树保留服务 Windows 读数。
2. 冻结与判定器：semantic_diff.py 纯 Python 可移植，**同一字节文件在 Linux 运行 judge_sha256 相同**（sha 是文件属性非平台属性）——这是 B 的一个技术优点。但冻结比较器 pyc_verify.py＋pylingual 的冻结要求是「字节、行为……全部保持不变」：字节可逐字复制，**Linux 行为未验证**（冻结表钉的是 Windows 行为基线），需重新验证＝其服务的每个门槛读数都要 Linux 重建。
3. **证据基线劈叉（B 最大成本）**：既有全部读数（t5/t30/t31、G1、G3 912、G4、coverage）均为 Windows 读数。Linux t32 是新基线，与旧基线不可比（平台是隐藏变量）；每个门槛要么双平台公布、要么重定基线——为行 2 的 ERROR 人口付整个证据体系重构的代价。
4. 成功不保证：8 个 cp311 `.so` 可被识别但 init 期行为未知（系统库/网络/更深依赖未验证）；cp35m pycrypto 在 3.11 任何平台不可载——若它成为次墙，B 换墙不拆墙。
5. 规模：WSL2＋3.11＋Linux vendor＋冻结重验证＋37 样本试点＋全量 t32＋守卫重设计＋双基线簿记——以天计；与在飞 t31、122.15 计划竞争资源。

**5.2.4 实施草图（若父代理选 B）**：WSL2 安装 → Py3.11 → 冻结比较器 Linux 行为验证（先行风险闸门：不过则 B 中止止损）→ Linux vendor（manylinux 三包＋typing_extensions 通用轮）→ 37 样本试点（墙是否真消灭：`import IQCommon.data.TickDataCache` 成功性一票定生死）→ 试点通过才全量 t32 → 双基线公布。
**5.2.5 验证计划**：试点闸门（37 样本 ERROR 消灭率）＋冻结 sha 复核＋t30/t31（Windows 代）与 t32（Linux 代）分列公布，不混算。
**5.2.6 失败模式**：`.so` init 期崩/缺系统库 → 换墙或加层；cp35m 不可载 → 残留墙需 A/C 兜底；冻结比较器 Linux 行为漂移 → 冻结验收失败风险；双基线簿记遗漏 → 跨平台读数误比。

### 5.3 方案 C：维持 unresolved，墙写成规格化边界声明

**5.3.1 规格字面符合性**：严格口径下最诚实——`unresolved = 0` 保持未达成（墙人口仍计入未解决），行状态与阈值一致，无任何口径操作。C 的产出是**声明**而非读数变更。
**5.3.2 证据强度**：零新增证据；把既有探针证据（27/27 同签名墙、四层收敛史、EXTENSION_SUFFIXES 结构性论证）组织为规格化边界声明。声明落点：行读数文档（SEMANTIC_J_FULL.md）＋checklist 行 2 单元格；REACHABILITY.md 行文本不动（改行文本＝规格变更，重程序，非本任务权）。
**5.3.3 实施草图**：纯文档——边界声明（墙定义、四层证据、EXTENSION_SUFFIXES 论证、人口计数【t31 回填】、本宿主不可测声明、后续路线指向）＋行读数双节（严格口径未解决数＝…含墙人口）。
**5.3.4 验证计划**：无代码改动 ⇒ 无回归面；验证＝声明内数字与 t31 交叉核对＋引用文件 sha 留痕。
**5.3.5 失败模式**：① 行 2（及五格可达性产品完备性主张）在本宿主**永久未达成**——后续每轮都要重新诉讼同一堵墙；② 判定器已算出的产物侧镜像信息被继续丢弃（可计算的证据源浪费）；③ 声明被误读为「豁免」——需在声明内自明「本声明不改变 unresolved 计数」。

### 5.4 方案 D：混合（C＋A）

**构成**：C 的规格化边界声明（5.3）＋ A 的镜像 verdict（5.1）＋ 双口径公布（第 7 节）。镜像类在严格口径下仍计入未解决（标题口径、行状态保持未达成），在边界口径下单列为「边界内已裁决」类；行 2 边界口径下的达成判定**显式留给父代理裁决**（沿 G4_REVIEW_PACKET「裁决之前保持 FAIL」惯例）。
**对第 3 节定性问题的回答**：以 C 的声明承接「未测面」的定性，以 A 的实测承接「已测面」的裁决——三层定性各得其所，无一层被默写。
**验证计划**：＝5.1.5 全部＋5.3.4；另加双口径一致性断言（严格未解决数＝边界未解决数＋镜像数，逐代核对）。
**失败模式**：A/C 的失败模式并集；特有：两口径被下游混用（缓解：每份文档两口径并列成对出现，禁止只引其一）。

## 6. 与既有惯例的一致性：G3「174 unjudgeable」先例

**先例原文（G3_FULL_RESULTS.md）**：「基线不可评估的 174 个 case……两类均记 case-level `unjudgeable`，**不计入分子也不伪造成 KILLED**」；「按 `spec.md` G3 阈值 `missed = 0`：**在可评估范围内达成**；但 G3 整体仍需全量 case 可评估，故**不宣称 G3 PASS**」。checklist.md L159：`| 变异测试 | `missed=0` | G3 全量 912 案 **17 284 KILLED / 0 MISSED** | **达成** |`。

**可迁移的计数纪律**：① 不可裁决人口**单列**（带原因码），不进分子、不伪造成成功类——镜像类同法（reason=`mirror_exception` 单列）；② 阈值按可评估范围陈述、详细文档保留 caveat；③ checklist 简表与详细文档口径可以分层（简表写达成、详档写不宣称 PASS）。

**先例的内在张力（如实呈现，不回避）**：checklist 行 3 标「达成」而 G3_FULL_RESULTS.md 写「不宣称 G3 PASS」——简表口径宽于详档口径。**本设计建议行 2 不沿用简表宽松做法**：G3 的 174 case 是「分母外」（不可评估 case 的变异体从未生成，不进 912 案的 missed 分母）；而行 2 的镜像类**在入口分母内**（`unresolved=0` 是入口人口属性，镜像条目本身就是入口条目）。两者形状不同：行 2 的镜像类若计入，未解决数≠0；若不计入，是一次显式的口径裁决。故本设计把「镜像类是否离开未解决集合」明示为**父代理裁决点**，并要求行 2 状态在裁决前保持「未达成（严格口径）」——不自动继承 G3 简表的「达成」实践。

**G4_REVIEW_PACKET 惯例对齐**：裁决项编号、每项附实测证据与选项、保守口径优先推荐、裁决之前门槛保持 FAIL、不得以「预演 PASS」替代——本设计的行状态处理（严格口径标题＋裁决前置）与之同构。

## 7. 保守性纪律（任何方案都必须遵守）

1. **不计入 EQUAL**：新 verdict 名禁含 "EQUAL"；`_summary` 单列；module_only/covered 计数不触碰；镜像人口不进任何成功分子。
2. **旧/新双读数同时公布**：未解决数旧口径（ERROR+INCONCLUSIVE+NO_C4+镜像，若引入）与新口径（ERROR+INCONCLUSIVE+NO_C4）**成对出现于同一文档**，禁止只引其一；行读数、checklist、行状态三处同步双口径。
3. **上界与保守值分离**：严格口径值为标题（保守）值；边界口径值为括注（宽）值；任何「达成」表述必须显式标注所引口径。
4. **覆盖零通胀**：covered_5tuple 不因新 verdict 变化（镜像人口 module-only；见 1.2 推断 4，全量确认留 t31）。
5. **谓词收窄**：v1 限 ImportError 族＋phase=load＋非 harness_error＋非超时＋canon 全等；判定器不新增任何 site-packages 特判（语料无关谓词；package_root 是既有唯一布线特例）。
6. **冻结纪律**：pyc_verify.py/pylingual sha 零变化；REACHABILITY.md/spec.md 行文本零变化；semantic_diff.py 变更以 judge_sha256 双代公示＋回归守卫治理。
7. **推断与实测分离**：产物侧镜像失败在方案 A 实施前是推断（1.2 推断 2）；实施后必须以落盘实测（镜像块）升格——文档中不得把「必然同败」写成「已测同败」。

## 8. 推荐

**推荐方案 D（C＋A 混合），按序实施；裁决权归父代理。**

理由：
1. **C 单独不够**：行 2 在本宿主永久未达成，且丢弃判定器已在计算的产物侧证据（1.2 推断 3）。
2. **A 单独有过度声明风险**：没有 C 的边界声明，新词表可能被读成「词表改一改阈值就达成」——恰是攻击完备性主张要防的模式。A 是 D 的构件，不是独立方案。
3. **B 成本高、成功概率未知、证据基线劈叉**：以天计的环境工程＋冻结重验证＋双基线簿记，换来「可能」消灭一面墙（cp35m 必不可载；`.so` init 期未验证）；其价值判断依赖 t31 之后的墙人口规模——**应等 t31 数据再评估 B**，不宜现在启动。
4. **D 把可算的证据现在就拿到**（镜像实测落盘＋非镜像即真分歧信号），双口径保诚实，MET 判定显式前置给父代理；与 G3 先例、G4_REVIEW_PACKET 惯例同构。

**实施时序**：t31 落地（旧 judge，勿中途改 judge）→ 本设计第 9 节问题清单回填 → 父代理裁决（含 D 内部各裁决点 1–5＋行 2 边界口径达成判定）→ （若批准）t31 后实施 A 的 judge/runner 改动 → 37 样本守卫（5.1.5）→ 范围化镜像测量（对 t31 的 ERROR 人口双侧复测，双代 sha 公布；无需全量 t32，除非父代理要求单一 judge 代的完整读数）→ 行读数/checklist 双口径更新。若裁决为 B：先走 5.2.4 冻结验证闸门再投入。

## 9. t31 数据回填问题清单（父代理裁决前需回答）

1. **镜像人口规模**：vendor 后全量 ERROR 总数及其构成（site-packages 墙类 / kept / excluded 探针 / harness_error 类）——镜像谓词适用面的分母。【t31 回填】
2. **双侧镜像率**：ERROR 人口的产物侧逐条对照（一次范围化双侧 probe；旧 probe 只测原始侧）——多少条两侧同签名（镜像成立）、多少条产物侧异签名（**真分歧信号，可能是新发现**）、多少条产物侧装载成功而原始失败（import 链发散信号）。【需新 probe，t31 记录不含产物侧异常】
3. **异常签名分布**：镜像成立人口中签名种类（预期 TickDataCache 单一签名；若出现多签名/多墙，镜像块须按签名分层计数）。【t31＋probe 回填】
4. **探针 ERROR 定性**：36 kept＋12 excluded 探针 ERROR 的相分布（load 相可镜像 / call 相、探针模块级自身异常不属镜像类）。【t31 回填】
5. **INCONCLUSIVE 18 分布**：原始侧超时 vs 产物侧超时；有无 load 相长链超时（未来可能转镜像候选）。【t31 回填】
6. **NO_C4 人口**：vendor 后反编译失败条目数（无产物 ⇒ 永不镜像候选）。【t31 回填】
7. **镜像人口的 calls 非空条目数**：样本 27/27 为零；全量若出现非零，status 处置（5.1.3-6 的 `mirror_exception_calls`）需追加裁决。【t31 回填】
8. **t31 judge_sha256**：预期仍 `d31948b3…`（确认 t30/t31 同代判定器，交叉表可比）。【t31 回填】
9. **行阈值范围问题（父代理裁定）**：行 2 输入含「402 语料＋46 真实 pyc」；镜像裁决是否延及 G2b（342 环境不可执行同墙类）与 G2c 的读数？判定器谓词语料无关（何处用 semantic_diff 何处生效），但行读数的范围声明需父代理定。
10. **（若考虑 B）墙人口规模**：t31 后墙类 ERROR 占比决定 B 的边际价值——墙类极小则 D 足矣；墙类巨大且包含 Linux 可载 `.so` 的多样性则 B 价值上升。

### §9 回填（2026-11-23 t31 落地，父代理）

1. **镜像人口规模（回填）**：t31 全量 ERROR 412＝site-packages 364（ImportError 族，
   全部撞 TickDataCache 墙，镜像谓词适用面）＋test_repros 48（TypeError/NameError，
   **非** ImportError 族，v1 谓词不覆盖）＋harness_error 类 0。v1 镜像分母＝364
   （外加 NO_C4→ERROR 时序翻转 2 条，同属墙类，合计按逐条实测为准）。
2. **双侧镜像率（待测）**：t31 记录不含产物侧异常，无法离线回填。由 37 样本验证
   （新 judge 双侧落盘）实测样本镜像率；全量率由 t32 落地。产物侧异签名/装载成功
   发散＝真分歧信号，如实单列，不并入镜像。
3. **异常签名分布（回填，原始侧）**：364 条原始侧 6 distinct pyc 布线态探针 6/6
   统一 `No module named 'IQCommon.data.TickDataCache'`（ModuleNotFoundError＝
   ImportError 族）——单一签名预期成立；产物侧签名待 t32 逐条分层计数。
4. **探针 ERROR 定性（回填）**：48 条（kept 36＋excluded 12）全部 load 相模块级
   崩溃、全部**探针源码自身确定性异常**（4 族：TypeError `with (CFG if 0 else
   json) as j`、NameError path/_CM/B）——非镜像类（源码 bug 而非环境墙），v1 维持
   ERROR 属实。
5. **INCONCLUSIVE 18 分布（回填）**：t31 逐条复现，全部 kept 探针执行超时
   （JS-IF-076/114、JS-MATCHSTMT-002、JS-TRY-008/009/025/050/062/078/086/087/
   095/096/097、JS-WHILE-007/032/038、JS-WITH-065），零新增；
   非 load 相长链，不构成镜像候选。
6. **NO_C4 人口（回填）**：t31 NO_C4＝0（trade_live_broker 42 条本轮全部反编译
   成功；2 条时序翻转 NO_C4→ERROR 已入墙类）。
7. **镜像人口 calls 非空条目数（回填）**：364 条墙类**全部** excluded（无 calls；
   kept 449 中 ERROR 36 全为探针族）。5.1.3-6 `mirror_exception_calls` 追加裁决
   **不需要**；covered_5tuple 395 零影响（全量尺度确认样本观察）。
8. **t31 judge_sha256（回填）**：`d31948b3…a9cc38` 与 t30 逐位一致（两块＋逐记录
   c5 失配 0）——t30/t31 同代判定器，交叉表可比 ✅。
9. **行阈值范围问题（父代理裁定，2026-11-23）**：**暂缓**——v1 镜像裁决实施与
   37 样本验证先行；G2b 342/G2c 是否按镜像口径重读，待 t32 落地、镜像读数稳定后
   单独裁决。判定器改动对 G2b 复跑自然生效（共用 semantic_diff），但本轮不重跑
   G2b、不改其已落库读数。
10. **墙人口规模（回填）**：墙类＝364/1556（23.4%）＋时序翻转 2 条。墙类单一
    （TickDataCache 一个签名、6 个 pyc 同根因、9 个 Linux `.so` 均不可载）——
    **B 的边际价值低**，维持「B 留档不启动」裁决。

## 10. 附录：改动点清单速查（仅方案 A/D 时适用）

| 文件 | 位置 | 改动 | 风险级 |
|---|---|---|---|
| tools/completeness/semantic_diff.py | L44 | 新 verdict 常量＋TOOL_VERSION | 低 |
| 同上 | L948–955 | 镜像谓词分支（唯一插入点） | 高（守卫 1–3 覆盖） |
| 同上 | L1110 / L1116–1123 | `_summary` 词表＋`_exit_code` 映射 | 低 |
| tools/completeness/semantic_runner.py | L25–30 | `EXIT_FOR_STATUS` 新增（**否则 L185 静默吞词表**） | 高 |
| 同上 | L186–191 / L195–203 | c4.mirror 拷入＋status/reason 映射 | 中 |
| tools/completeness/coverage_checker.py | L42 | VERDICTS 增词（non-covered 处理） | 中 |
| tools/completeness/mutation_test.py | — | 零改动（L411–415 天然兼容） | 无 |
| docs（SEMANTIC_J_FULL.md / checklist.md） | 行 2 相关节 | 双口径＋边界声明＋人口学行 | 中（口径纪律） |
| REACHABILITY.md / spec.md / pyc_verify.py / pylingual | — | **零改动（冻结）** | — |

—— 设计草稿完。裁决点汇总：① verdict 命名（推荐 MIRRORED_EXCEPTION）；② 谓词异常族（推荐 v1 限 ImportError 族）；③ 装载期可观察量是否为必要条件（推荐否，如实记录）；④ exit code（推荐 4）；⑤ status/reason 映射（推荐 unexecuted＋mirror_exception）。全部裁决权归父代理。
