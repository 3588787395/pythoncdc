# G3 判据修复：嵌套 code object 逐字段比较（G3_RULER_FIX）

日期：2026-11-17
范围：只改 `tools/completeness/semantic_diff.py` 与 `tools/completeness/mutation_test.py`。
未改 `core/`、`scripts/pyc_verify.py`、外部 `pylingual/equivalence_check.py`、`tests/`、`TOLERANCE_REGISTRY.md`。

## 0. 结论摘要

- **A（修尺子）**：`co_consts` 里的嵌套 code object 不再塌缩成 `code_sha`，改为递归逐字段比较（`co_code` / `co_consts` / `co_exceptiontable` 及其它既有字段）。198 条“唯一差异是嵌套 `code_sha`”的样本 **198/198 从 MISSED 变 KILLED**；302 条 `semantic_EQUAL` 中 **300 条变 KILLED**、2 条是真恒等变异；102 条 other 中 **98 条变 KILLED**、4 条顶层 `co_code` 等价改写仍为 MISSED。
- **B（J 空间）**：`coverage_checker` 的 `covered_5tuple` **仍为 1180**（C1–C5 口径不变）；真正表示“判对”的 `green`（EQUAL）从 **1180 降到 1151**，`semantic_failures` 从 **0 升到 29**。按 J 空间“EQUAL 读数”说，**下降 29 条（−2.46%）**。
- **C（分类）**：302 条抽样 **10/10 是“未调用函数/不可达分支内变异”**，修复后 10/10 变 DIFFERENT；它们此前 EQUAL 的根因是**第二层嵌套 code 塌缩（判据盲）**，不是语义等价。102 条 other = 98 条嵌套 code + `consts_len` + 4 条顶层 `co_code`；前 5 类路径计数见 §C.2。
- **必须提请注意**：对新判据下“嵌套 code 真实差异 + 未调用/不可达”的变异写 `equivalents` proof，当前 `mutation_test` 会记 **FALSE_KILL**，不是 EQUIVALENT（已实测 M0010）。见 §D.2，需你决定是否扩展 proof 分支。

---

## A. 修改点

### A.1 `semantic_diff.py`

1. `code_metadata()` 改为 `_code_metadata()` 递归：
   - 顶层 code object 的 `co_consts` 走 `_const_meta()`；
   - `co_consts` 中是 code object 时递归 `_code_metadata()`；
   - tuple/frozenset/list 常量继续逐项展开；
   - 结果路径形如：
     - `$.metadata.code.co_consts.v[i].co_code`
     - `$.metadata.code.co_consts.v[i].co_consts.v[j]`
     - `$.metadata.code.co_consts.v[i].co_exceptiontable`
   - `dimension` 仍为 `R7`，受保护字段仍是 `co_code` / `co_consts` / `co_exceptiontable`，判定强度未放宽。
2. 字节字段 `co_code` / `co_exceptiontable` 表示为 `{"t":"bytes","len":…,"sha256":…}`；`compare_canon` 对 `t=="bytes"` 在**字段路径本身**报差异（不再只报 `.sha256`/`.len` 两个子路径）。
3. 环/深度保护：`ancestors` 是当前递归路径上的 `id()` 集合（`frozenset`）。命中已访问对象时返回 `{"t":"code","cycle":true,...}` / `{"t":"ref","v":"<cycle>"}`。**没有数字深度上限**。
4. `_is_ignored()` 让 `co_filename` / `co_firstlineno` / `co_linetable` 在**任意 code 深度**都按 `TOLERANCE_REGISTRY.md §1` 忽略；自定义 `ignore_metadata_fields` 仍按精确路径生效，受保护字段的未登记忽略仍判 ERROR。

### A.2 `mutation_test.py`

`_code_metadata_only()` 更新为：

- 非 R7 差异 → 不是 metadata-only；
- 路径不以 `$.metadata.code.` 开头 → 不是；
- 叶子字段是 `co_filename` / `co_firstlineno` / `co_linetable` → 继续忽略（任意深度）；
- 路径落在 `co_consts.v[...]` 下（嵌套 code 的真实字段）→ **不再是 metadata-only**；
- 顶层 code object 自己的 `co_code` / 签名 / names 等仍按原 metadata-only 处理（R1–R6 已经量过该 body；保留既有 EQUIVALENT-with-proof 流程）。
- 顶层 `co_consts` 的常量值差异会因路径落在 `co_consts.v[...]` 下而被算作真实差异（这是“函数体常量表变了”的直接证据）；本次 30 案中没有因此新增残余 MISSED，残余的 4 条顶层差异全部是 `co_code` 字节码，不是 `co_consts`。

另加 `sys.path.insert(0, dirname(__file__))`，使指定的
`D:/Python/python.exe -I -X utf8 tools/completeness/mutation_test.py …`
在 `-I` 隔离模式（会移除脚本目录）下仍能 `import semantic_diff`。

### A.3 自测/回归

- `semantic_diff_selftest.py`：**26/26 通过**（日志 `selftest_semantic_diff_after.txt`）。
- `mutation_test_selftest.py`：9 项检查全 True（`selftest_mutation_after.txt`）。
- `semantic_runner_selftest.py`：11/11（`selftest_semantic_runner_after.txt`）。
- `coverage_checker_selftest.py`：通过（`selftest_coverage_after.txt`）。
- 递归行为探针 `probe_recursion_result.json`：
  - 嵌套函数体 `return 1 → 2`：DIFFERENT，路径 `$.metadata.code.co_consts.v[0].co_consts.v[1].co_consts.v[1].v`；
  - 仅嵌套 `co_filename`/行号不同：EQUAL；
  - 嵌套推导式常量 `1 → 2`：DIFFERENT，路径 `$.metadata.code.co_consts.v[1].co_consts.v[0].v`；
  - 无变化的 lambda：EQUAL；
  - `_code_metadata_only` 契约 6/6（顶层 `co_code` 为 metadata-only；嵌套 `co_code`、深层 `co_code` 为真实差异；嵌套 `co_filename` 仍忽略）。

### A.4 round9 三案复跑（`mutation_test.py --case … --source … --max-mutants 25`）

| case | before KILLED/MISSED | after KILLED/MISSED | 结论 |
|---|---:|---:|---|
| JS-ASYNCFOR-021 | 0 / 25 | **25 / 0** | 25 条全部 MISSED→KILLED |
| JS-AUGFORM-017 | 0 / 25 | **25 / 0** | 25 条全部 MISSED→KILLED |
| JS-NAMEDEXPR-001 | 0 / 25 | **25 / 0** | 25 条全部 MISSED→KILLED |

日志：`mut_after_JS-ASYNCFOR-021.json`、`mut_after_JS-AUGFORM-017.json`、`mut_after_JS-NAMEDEXPR-001.json`（及对应 `.log`）。

### A.5 30 案全量复跑（同一判据，`--max-mutants 25`）

| 读数 | before | after |
|---|---:|---:|
| KILLED | 32 | **628** |
| MISSED | 602 | **6** |
| ERROR | 1 | 1 |
| 选中总数 | 635 | 635 |

按旧重分类（`g3_reclass.json`）拆开：

| 旧类别 | 条数 | after KILLED | after MISSED | 说明 |
|---|---:|---:|---:|---|
| `nested_code_sha_only`（198 类） | 198 | **198** | 0 | 全部 MISSED→KILLED |
| `semantic_EQUAL`（302 类） | 302 | **300** | 2 | 300 条其实有更深的嵌套 code 变化；2 条是恒等变异 |
| `other`（102 类） | 102 | **98** | 4 | 98 条是嵌套 code + `consts_len`；4 条是顶层 `co_code` 等价改写 |

剩余 6 条 MISSED：

1. `JS-BREAK-001 M0014`：`return None → return None`，AST 重写前后源码相同（零 diff；恒等变异）。
2. `JS-WHILE-040 M0014`：同上（恒等变异）。
3. `JS-RETURN-033 M0006/M0008`：模块级 `M1/M2` 的 boolop 交换；常量取值为 1/2/3，交换后值不变（`(1 or 2) and 3 == (1 and 2) and 3 == 3`；`1 or (2 and 3) == 1 or (2 or 3) == 1`），唯一差异是顶层 `co_code`。
4. `JS-RETURN-070 M0006/M0008`：同上。

1 条 ERROR 是 `JS-AUGFORM-031 M0005` 的既有生成/加载错误，修复前后不变。

---

## B. 对 J 空间的影响（如实报）

### B.1 方法

不重跑反编译器（产品文本未变），只把 `semantic_v3m_b275_merged.json` 中 **1180 条旧 EQUAL** 的 C1/C2/C3 原样取出，用修改后的 `semantic_diff` 重判 C4；然后用 `coverage_checker.py`（`--judge` 指向新判据）重算。这样只改变“尺子”一个变量，不混入反编译非确定性。376 条旧 ERROR 原样跳过。

- 旧证据：`fresh/semantic_v3m_b275_merged.json`（1180 EQUAL + 376 ERROR）
- 新证据：`g3fix/semantic_v3m_b275_g3fix_merged.json`（C5 judge_sha 已更新）
- 新判据 sha256：`d31948b3a0a4336078d3e031467fa942947c358ecc7584c5194bd389d1a9cc38`
- 复算命令（日志 `coverage_g3fix.log`）：

```text
D:/Python/python.exe -I -X utf8 tools/completeness/coverage_checker.py \
  --space .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/judgment_space_v3m_b275.json \
  --evidence D:/temp/opencode/cl_layout/gap/g3fix/semantic_v3m_b275_g3fix_merged.json \
  --judge tools/completeness/semantic_diff.py \
  --out D:/temp/opencode/cl_layout/gap/g3fix/COVERAGE_G3FIX.md \
  --json D:/temp/opencode/cl_layout/gap/g3fix/coverage_g3fix.json
```

### B.2 读数

```text
[coverage] J_total=1556 covered_5tuple=1180 probe_only=0 unexecuted=0 n/a=0
           inconclusive=0 excluded=376 uncovered=376 coverage=75.84%
totals: semantic_failures=29 green=1151
```

| 读数 | before | after | 变化 |
|---|---:|---:|---:|
| J_total | 1556 | 1556 | 0 |
| **covered_5tuple** | 1180 | **1180** | 0（C1–C5 口径；DIFFERENT 仍计 C4 有效） |
| **green（EQUAL）** | 1180 | **1151** | **−29** |
| semantic_failures | 0 | **29** | +29 |
| excluded / uncovered | 376 / 376 | 376 / 376 | 0 |
| coverage_pct | 75.84% | 75.84% | 0 |

**口径说明**：`coverage_checker` 的 `covered_5tuple` 只要求 C1–C5 证据链完整，`DIFFERENT` 也计入 `covered_5tuple`；`green` 要求 `covered_5tuple + EQUAL`。因此“修尺子”让 **green/EQUAL 读数下降 29**，而 `covered_5tuple` 数值不变。若你所说的 `covered_5tuple=1180` 实际指“EQUAL 覆盖读数”，则答案是 **1151**；按 checker 字段名则是 **1180**。两种口径都在这里列出，不混报。

### B.3 29 条 EQUAL→DIFFERENT（全部为 DIFFERENT，无 ERROR/INCONCLUSIVE）

前 10 条 id（J 顺序）：

| # | id | 主要差异路径 |
|---:|---|---|
| 1 | JS-IFEXP-001 | `$.metadata.code.co_consts.v[6].co_consts.v[2].co_consts.v[0]` |
| 2 | JS-IFEXP-002 | 同上 |
| 3 | JS-IFEXP-003 | 同上 |
| 4 | JS-IFEXP-007 | 同上 |
| 5 | JS-IFEXP-008 | 同上 |
| 6 | JS-IFEXP-009 | 同上 |
| 7 | JS-IFEXP-010 | 同上 |
| 8 | JS-IFEXP-011 | 同上 |
| 9 | JS-IFEXP-012 | 同上 |
| 10 | JS-IFEXP-013 | 同上 |

其余 19 条：`JS-IFEXP-014/015/024/025`、`JS-LISTCOMP-012/028/029`、`JS-SETCOMP-017`、`JS-DICTCOMP-019/020`、`JS-GENEXP-005/017/018`、`JS-BREAK-001/011/023/027/030`、`JS-WHILE-040`。

按形态族：IFEXP 14、BREAK 5、LISTCOMP 3、GENEXP 3、DICTCOMP 2、WHILE 1、SETCOMP 1。
按差异形状：**17 条**含嵌套 `co_code`/`co_consts.len`；**12 条**只有嵌套 `co_consts` 值（IFEXP 001–015 族）。
29 条**全部是 R7-only**（共 92 个差异路径），R1–R6 没有任何差异。

### B.4 这 29 条是不是 29 个真实语义回归？

**不是。** 至少 12 条是嵌套常量写法差异，行为等价。例：

- `JS-IFEXP-001` 源码 `if (x if b else 0)`，产品 `if (x if b else False)`（或 `not flag or x % 2` vs `(x % 2 if flag else True)`）：R1–R6 全 EQUAL，差异只在嵌套 code object 的 `co_consts`（`0` vs `False`）。按 R7 受保护字段仍必须 DIFFERENT，但这不是语义回归。
- `JS-BREAK-001` 产品把 `for … while True …` 重构为 `while 1: for … continue; break`；这是嵌套 `co_code` 结构差异，位于未被 `CMisc()` 调用的方法里，属于“判据现在能看见、但行为未被观测”的一类，需人工判等价/缺陷。

因此：**读数下降 29 是更严格尺子的结果，不等于 29 个已证实缺陷；其中 12 条是等价常量拼写，17 条是嵌套 code 结构差异，需逐条定性。**

### B.5 一句话结论

**这次“修尺子”让 EQUAL/green 读数下降：1180 → 1151（−29，−2.46%）；`covered_5tuple` 按 C1–C5 口径保持 1180，coverage_pct 不变 75.84%。**

---

## C. 302 条 semantic_EQUAL 与 102 条 other 的分类

### C.1 302 条抽样 10 条

抽样方式：按 `(case, mutant)` 排序后等步长取 10。全部位于**未被 `call_exprs` 调用**的函数/方法/分支内；修复后 10/10 变 DIFFERENT（KILLED）。

| # | case / mutant | 位置 | 源码行 | 为何行为不可见 | after |
|---:|---|---|---|---|---|
| 1 | JS-ASYNCFOR-001 M0010 | `a_four` 的 genexp | `return sum(1 for x in xs if await g2(x))` | `call_exprs` 只有 `acm()`，`a_four` 从未调用 | KILLED（嵌套 `co_consts.v[1].v`） |
| 2 | JS-ASYNCFUNC-012 M0009 | `e04_await_deep.go` | `return r` | `CAA()` 只构造类，内部 `go` 从未调用 | KILLED（嵌套 `co_code`） |
| 3 | JS-AUGFORM-017 M0006 | `e01_root` | `y *= 3` | `CAU()` 只构造类，`e01_root` 从未调用 | KILLED（嵌套 `co_consts.v[3].v`） |
| 4 | JS-AWAITEXPR-014 M0006 | `e04_await_deep.go` | `r = 0` | 同上，`go` 未调用 | KILLED（嵌套 `co_consts.v[1].v`） |
| 5 | JS-LISTCOMP-026 M0010 | `a_four` 的 genexp | 同 #1 | `acm()` 只构造，`a_four` 未调用 | KILLED（嵌套 `co_consts.v[1].v`） |
| 6 | JS-NONLOCAL-002 M0014 | `nl_level4` | `return s4()` | `nl_multi_names()` 只返回 `worker`，`nl_level4` 未调用 | KILLED（嵌套 `co_code`） |
| 7 | JS-NONLOCAL-013 M0022 | `worker` | `if i % 2:` | `worker` 被返回但从未调用 | KILLED（嵌套 `co_code` + `consts.len`） |
| 8 | JS-RETURN-025 M0014 | `acm.__aexit__` | `return False` | `acm()` 只构造，`__aexit__` 未触发 | KILLED（嵌套 `co_code`） |
| 9 | JS-RETURN-070 M0016 | `CB98.m_handler` | `return (a or b) and c` | `CB98()` 只构造，方法未调用 | KILLED（嵌套 `co_code`） |
| 10 | JS-STARRED-005 M0018 | `e07_match_host` | `r = f(*xs, 1)` | `CSA()` 只构造，`e07_match_host` 未调用 | KILLED（嵌套 `co_consts.v[2].v`） |

分类计数（抽样 10）：

- **未调用函数/不可达分支内变异：10/10**（应登记 EQUIVALENT + proof，见 §D.2 的当前工具限制）。
- **语义等价改写：0/10**。
- **修复后判据仍盲：0/10**（10/10 已被嵌套字段差异捕获）。

全量 302 条的 after 状态：

- **300 条 KILLED**：旧 `semantic_EQUAL` 的根因是**更深一层的嵌套 code 塌缩**（父 code 的 `code_sha` 未变、`consts_len` 未变，grandchild 的 `co_consts`/`co_code` 变了）；旧判据零 diff。这不是“语义等价”，是**判据盲**。
- **2 条 MISSED**：`JS-BREAK-001 M0014`、`JS-WHILE-040 M0014`，都是 `return None → return None` 的恒等变异，源码逐字相同（零 diff；属于语义等价/无效变异）。
- **0 条 ERROR/INCONCLUSIVE**。

结论：302 条中 **300 条是嵌套 code 塌缩造成的伪 EQUAL**；抽样 10 条全部是未调用/不可达路径，说明“行为不可见”是这些变异的共同特征，但不是“语义等价”的证明。真正恒等的只有 2 条 no-op。

### C.2 102 条 other 的路径分类

按 diff 路径前缀（路径行计 / 变异条计）：

| 类别 | 变异条数 | 路径行数 | after |
|---|---:|---:|---|
| `$.metadata.code.co_consts.v[i]`（嵌套 code object；`code_sha` + `consts_len`） | **98** | 196 | 98 KILLED |
| `$.metadata.code.co_code`（顶层 code object 字节码） | **4** | 4 | 4 MISSED（metadata-only；见下） |

前 5 个具体路径前缀（按变异条计，均同时带同索引的 `.consts_len`）：

| # | 路径前缀 | 条数 |
|---:|---|---:|
| 1 | `$.metadata.code.co_consts.v[1].code_sha` | 19 |
| 2 | `$.metadata.code.co_consts.v[3].code_sha` | 18 |
| 3 | `$.metadata.code.co_consts.v[2].code_sha` | 16 |
| 4 | `$.metadata.code.co_consts.v[0].code_sha` | 12 |
| 5 | `$.metadata.code.co_consts.v[5].code_sha` | 9 |

其余：`v[4]` 8、`v[10]` 6、`v[7]` 3、`v[8]` 3、`v[9]` 3、`v[6]` 1；总计 98 条嵌套 + 4 条顶层。

4 条顶层 `co_code` 全部是 `JS-RETURN-033` / `JS-RETURN-070` 的 `M0006`/`M0008`（模块级 `M1/M2` boolop 交换）。常量取值使交换前后结果相同，因此是**真正的语义等价改写**；保留为 metadata-only 后，可通过现有 `equivalents` proof 记为 EQUIVALENT（实测 `JS-RETURN-033 M0006 + proof → EQUIVALENT`，日志 `mut_equiv_top_probe.json`；当前默认未提供 proof，所以仍 MISSED）。

---

## D. 残余问题与待你审的设计点

### D.1 6 条残余 MISSED

- 2 条恒等变异（`return None → None`）：`JS-BREAK-001 M0014`、`JS-WHILE-040 M0014`。建议在等价台账登记或从变异生成器中跳过“same-value”变异（本次未改生成器）。
- 4 条顶层 `co_code` 语义等价改写（`JS-RETURN-033/070 M0006/M0008`）。保留 metadata-only 是刻意选择：顶层 body 已被 R1–R6 量过，proof 分支仍可把它们记为 EQUIVALENT；若把它们也改成“真实差异”，这 4 条会变成 KILLED，反而高估 mutation score。

### D.2 `equivalents` proof 与嵌套 code 真实差异的冲突（必须你定）

`mutation_test` 现有分支：

```text
semantic == DIFFERENT:
    if _code_metadata_only(diffs):
        EQUIVALENT if proof else MISSED
    else:
        FALSE_KILL if proof else KILLED
```

按 A 的要求，嵌套 `co_consts.v[i].co_code` 已不再是 metadata-only。因此给“未调用函数内的嵌套 code 变异”写 proof 时，工具会走 `FALSE_KILL`，而不是 EQUIVALENT。实测：

```text
JS-ASYNCFOR-001 M0010 + proof
  -> status=FALSE_KILL, semantic_status=DIFFERENT
  summary: KILLED=9, FALSE_KILL=1
```

这与 Task C “应经 equivalents 文件登记为 EQUIVALENT 并给 proof”冲突。可选方案（未擅自实施，等你审）：

1. 扩展 proof 分支：当 `proof` 存在且**所有差异都是 R7 且路径在 `$.metadata.code.` 下**时，记 EQUIVALENT（不改 verdict，仍 DIFFERENT；只是 mutation 分类）。这样未调用/不可达的嵌套 code 变异可以凭 proof 记为 EQUIVALENT。
2. 维持现状：这类变异一律 KILLED；在报告中单独维护“行为等价但被静态判据杀死”的台账，不进入 mutation score。
3. 只允许 proof 覆盖顶层 metadata-only（现状），嵌套 code 差异不接受 proof；则 302 类里的未调用变异无法登记 EQUIVALENT。

本次未改 proof 分支，避免在“修尺子”任务里顺带改变 mutation 分类语义。

### D.3 R7 强度

- `semantic_diff` 对 `co_code` / `co_consts` / `co_exceptiontable` 仍是硬阻断；未新增任何 tolerance；未放宽 `_unregistered_r7_ignores`。
- `co_filename` / `co_firstlineno` / `co_linetable` 仍按 `TOLERANCE_REGISTRY.md` 默认忽略，并扩展到嵌套 code 深度（否则每个嵌套函数都会因产品文件路径不同而假 DIFFERENT）。
- 没有数字深度上限；递归用 `ancestors` 访问集，环返回 cycle/ref 标记。

---

## E. 产物与复现

### E.1 工具改动

- `tools/completeness/semantic_diff.py`
- `tools/completeness/mutation_test.py`
- 补丁：`D:/temp/opencode/cl_layout/gap/g3fix/g3fix_tools.patch`

### E.2 日志目录 `D:/temp/opencode/cl_layout/gap/g3fix/`

| 文件 | 内容 |
|---|---|
| `selftest_semantic_diff_after.txt` | 26/26 |
| `selftest_mutation_after.txt` | 9 项检查全 True |
| `selftest_semantic_runner_after.txt` | 11/11 |
| `selftest_coverage_after.txt` | coverage checker selftest |
| `probe_recursion.py` / `probe_recursion_result.json` | 递归路径/忽略/`_code_metadata_only` 契约探针 |
| `mut_after_JS-ASYNCFOR-021.json` 等 3 个 | 三案复跑 |
| `mut_all_after_*.json` / `.log` | 30 案全量复跑 |
| `before_class.json` / `compare_classes.txt` | 198/302/102 → after 状态对照 |
| `sample10_equal.json` / `sample10_after.txt` | 302 抽样 10 条 |
| `rejudge_all.json` / `rejudge_all.log` | 1180 条 J 空间重判 |
| `semantic_v3m_b275_g3fix_merged.json` | 更新 C4/C5 的 J 证据 |
| `coverage_g3fix.json` / `COVERAGE_G3FIX.md` / `coverage_g3fix.log` | 新覆盖读数 |
| `show_flips.txt` / `flip_stats.txt` | 29 条翻转与形态 |
| `mut_equiv_probe.json` | proof→FALSE_KILL 实测 |

### E.3 关键复现命令

```text
D:/Python/python.exe -I -X utf8 tools/completeness/mutation_test.py \
  --case .trae/specs/attack-completeness-claims/rounds/round9/g3_mutation/case_JS-ASYNCFOR-021.json \
  --source F:/Downloads/pythoncdc-main/test_repros/round3/e12b_g9_yield_split.py \
  --max-mutants 25 \
  --out D:/temp/opencode/cl_layout/gap/g3fix/mut_after_JS-ASYNCFOR-021.json
```

```text
D:/Python/python.exe -I -X utf8 tools/completeness/coverage_checker.py \
  --space .trae/specs/achieve-any-syntax-completeness/rounds/round13/jspace_v3/fresh/judgment_space_v3m_b275.json \
  --evidence D:/temp/opencode/cl_layout/gap/g3fix/semantic_v3m_b275_g3fix_merged.json \
  --judge tools/completeness/semantic_diff.py \
  --out D:/temp/opencode/cl_layout/gap/g3fix/COVERAGE_G3FIX.md \
  --json D:/temp/opencode/cl_layout/gap/g3fix/coverage_g3fix.json
```

### E.4 边界声明

- 本次只修“尺子”，没有修反编译器；J 空间产品文本与 B275 基线一致。
- `covered_5tuple` 保持 1180 不等于“29 条翻转不存在”；`green`/`semantic_failures` 才是判对读数。
- 不宣称 G1/G3/G4/G6 通过；`product_complete` 仍 NOT PASS。
