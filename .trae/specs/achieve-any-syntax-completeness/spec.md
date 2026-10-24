# 任意语法完备反编译 Spec

## Why

`attack-completeness-claims` 已证明：v8 的 **128/128 形态基线**不是语义完备；更根本的问题是，它把“完备”定义成**问题集通过率**，因此只能说明“已知问题已处理”，不能说明“任何语法都能处理”。

本规范不再使用抽象定理或形式证明，而是把“产品完备”拆成**五个可达组成部分**。每个组成部分都必须给出：

1. **有限的输入来源**；
2. **已存在的生成器或执行器**；
3. **明确的验收命令**；
4. **明确的阈值**。

任何一格只能写“待定”或“未知”，规范状态即为 `NOT READY`，不得进入实现。

## 术语对照：三个“五”

本规范同时出现三个“五”，它们指不同的东西：

| 术语 | 指什么 | 内容 |
|---|---|---|
| **J 的五个维度** | 判定空间的坐标轴 | 形态、宿主、深度、变体、可调用性 |
| **J 记录的五个字段** | 每条 J 的最低存储字段 | `p_j`、`pyc`、`expected_label`、`input_model`、`excluded` |
| **产品完备的五个组成部分** | 验收支柱 | J 空间（五个维度）、语义差分、变异测试、规则覆盖、G5 回归 |

三者关系：

- **五个维度**回答“判定什么”：一条 J 是这五个维度上的一个点。
- **五个字段**回答“怎么存”：`expected_label` 承载前四个维度，`input_model.calls` 承载第五个维度。
- 其余哈希、行数、`entrypoint` 等字段是审计辅助，不参与“五字段”定义。
- **五个组成部分**回答“怎么验收”：每一支都必须给出有限输入、已有工具、明确命令和阈值。

## J 的五个维度

“J 的五个维度”指判定空间的**五个坐标轴**，不是 J 记录的字段数，也不是产品完备的组成部分数。

| 维度 | 含义 | 示例 |
|---|---|---|
| **形态** | 语法/节点/扩展形态 | `if`、`for`、`try`、`with`、`match`、`async`、推导式 |
| **宿主** | 该语法出现的位置/上下文 | module、function、class、loop、try、with、match、async |
| **深度** | 嵌套档位 | 1、2、3、≥3 |
| **变体** | 同一形态的语义变体槽 | 值类型、作用域、异常路径、装饰器、docstring |
| **可调用性** | 是否有函数/类入口调用 | `input_model.calls` 非空；module-only 不算覆盖 |

一条具体的 J 例如：

> `形态=try/finally`，`宿主=for`，`深度=2`，`变体=continue`，`可调用性=有函数入口调用`

这五个维度都来自**有限集合**，因此 J 空间可枚举，不涉及无限程序空间。

一条 J 记录的目标形态示例（摘自 `JS-IF-017`，`calls` 为需补齐项）：

```json
{
  "p_j": ".trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.py",
  "pyc": ".trae/specs/adversarial-complete-forms-v2-10rounds/rounds/round1/probes_rv2/v_b71_face.pyc",
  "expected_label": {
    "form": "If",
    "variant": "if-no-else",
    "host": "try-body",
    "depth": "d3plus 三层及以上"
  },
  "input_model": {
    "kind": "module",
    "calls": ["v_nest_fin_continue([[0, 1]])"],
    "seed": 0
  },
  "excluded": []
}
```

现状提醒：J v2 里多数 `input_model.calls` 为空；这正是 module-only 假绿的来源，Task 5 必须补齐。

## What Changes

- **新增 `REACHABILITY.md`**：用一张表列出 J 空间（五个维度）、语义差分、变异测试、规则覆盖、G5 回归的输入来源、执行方式、验收命令和阈值。
- **冻结基本比较器**：`scripts/pyc_verify.py` 及其装载的 `pylingual/equivalence_check.py::compare_pyc` 的字节、行为、容差和 verdict 语义全部保持不变；只允许在其外层新增报告/汇总，不得改变判定。
- **J 空间（五个维度）**：判定空间按 形态 / 宿主 / 深度 / 变体 / 可调用性 五个维度组织；每条 J 记录至少包含 `p_j`、`pyc`、`expected_label`、`input_model`、`excluded` 五个字段，其中 `expected_label` 存前四个维度，`input_model.calls` 存第五个维度。
- **R7 阻断**：`co_code` / `co_consts` / `co_exceptiontable` 的 code object 差异默认判 `DIFFERENT`；未经书面 tolerance 不得忽略。
- 修复 **B142**：嵌套 `try/finally` 中的 `continue` 必须按 finally 副本谱系正确装配，不得双发/丢失/错层。
- 修复 `JS-IF-076` 暴露的 x01 结构差、B199 函数 docstring 保真、module docstring 还原，以及四个已最小化 fuzz 发现（含 B197/B202 的 positional-only 签名问题）。
- 补齐 J 空间：388 条缺 source、12 条缺 pyc 必须显式恢复/生成或登记为不可判定；全量 1556 条跑 C1–C5。
- 完成 G1–G5 与 E 门禁：语义差分、变异、规则 witness、402 语料、small34、quotation、pytest 基线、IV.2；G6 独立 canary 作为**独立保证**单列，不以本地 bootstrap 冒充 PASS。
- **BREAKING**：完备性不再由问题集通过率定义，而由**可达性表**定义；上表任一格缺失即 `NOT READY`。

## Impact

- 受影响规范：`attack-completeness-claims`（攻击结论转为实现验收）、`attain-true-completeness`（v8 口径仅作历史基线）、`adversarial-complete-forms-v2-10rounds`（旧探针作为回归面）。
- 受影响代码：`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`、`core/cfg/code_generator.py`、`core/cfg/ast_generator_v2.py`、`core/cfg/pattern_parser.py`；`tools/completeness/` 的 runner/coverage/mutation/rule/fuzz/canary；`rules.md` 与 `wiki/` 台账。
- **不修改**：`scripts/pyc_verify.py`、外部 `pylingual/equivalence_check.py`、`tests/` 基线、402 认证产物、用户既有变更。
- 目标范围：CPython **3.11** 字节码（`py_compile` 产物），覆盖完整语法族及其 ≥3 级宿主组合。
- 非目标：3.12/3.13 新字节码、C 扩展、动态 `eval`/`exec` 生成代码、混淆字节码、依赖运行时环境的不可判定行为；“任何语法”不等于“任意程序在任意输入下的所有运行时行为”。

## 产品完备的可达组成

“产品完备”由下表五个组成部分共同决定。每一行都必须满足“**有限输入 + 已有工具 + 明确命令 + 明确阈值**”。

| 组成部分 | 有限输入来源 | 生成/执行方式 | 验收读数 |
|---|---|---|---|
| **J 空间（五个维度）** | CPython 3.11 语法产生式 | `tools/completeness/jspace_generator.py` 按 形态 / 宿主 / 深度 / 变体 / 可调用性 生成 `p_j / pyc / expected_label / input_model / excluded` | 1556 条全量；`source_missing = 0`、`pyc_missing = 0`、`calls_missing = 0` |
| **语义差分** | J 空间（五个维度） + 402 语料 + 46 真实 pyc | `tools/completeness/semantic_runner.py` + `tools/completeness/semantic_diff.py` | `unresolved = 0`；C1–C5 齐全；R1–R7 无未裁决失败 |
| **变异测试** | J 空间（五个维度） + 402 语料 | `tools/completeness/mutation_test.py` | `missed = 0` |
| **规则覆盖** | 339 条规则 | `tools/completeness/rule_manifest.json` + witness/trace 映射 | `open = 0` |
| **G5 回归** | 402 八分片 / small34 / quotation / IV.2 | 既有回归脚本 | 全绿 |

### 可达性判定

- **不要求形式证明**。
- 每个组成部分必须写出：输入集合大小、生成器或执行器、验收命令、阈值。
- 输入集合必须**有限**；任意嵌套由递归处理，不通过枚举无限样例。
- 若某组成部分无法给出命令或阈值，该行记 `NOT READY`，不得进入实现。
- 已知缺陷（B142、x01、fuzz）只是反例，不是完备性的定义。

## 命令面

五个组成部分的既有命令如下；`REACHABILITY.md` 必须逐行复述，不允许只写工具名：

| 组成部分 | 既有命令 |
|---|---|
| **J 空间（五个维度）** | `python -X utf8 tools/completeness/jspace_generator.py --evidence-root .trae/specs/attain-true-completeness/rounds --out .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json --md .trae/specs/attack-completeness-claims/rounds/round9/JUDGMENT_SPACE.md`；覆盖检查：`python -X utf8 tools/completeness/coverage_checker.py --space .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json --evidence .trae/specs/attack-completeness-claims/rounds/round9/semantic_j_sample.json --judge scripts/pyc_verify.py --out .trae/specs/attack-completeness-claims/rounds/round9/COVERAGE.md --json .trae/specs/attack-completeness-claims/rounds/round9/coverage_c1c5.json` |
| **语义差分** | `python -X utf8 tools/completeness/semantic_runner.py --space .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json --out .trae/specs/attack-completeness-claims/rounds/round9/semantic_j_sample.json`；单案：`python -X utf8 tools/completeness/semantic_diff.py --case <case.json> --out <result.json>` |
| **变异测试** | `python -X utf8 tools/completeness/mutation_test.py --case <case.json> --source <subject.py> --out <mutations.json>` |
| **规则覆盖** | `python -X utf8 tools/completeness/rule_manifest.py --check --universe .trae/specs/attack-completeness-claims/rounds/round9/rule_universe.json --manifest tools/completeness/rule_manifest.json --jspace .trae/specs/attack-completeness-claims/rounds/round9/judgment_space.json --traces <rule_traces.json> --json .trae/specs/attack-completeness-claims/rounds/round9/rule_coverage.json` |
| **G5 回归** | `python -X utf8 scripts/pyc_verify.py batch --index .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/baseline/shards/shard0.json`（同法跑 shard1–shard7）；`python -X utf8 scripts/pyc_verify.py batch --index .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/baseline/small34_index.json`；`python -X utf8 scripts/pyc_verify.py single site-packages/fly/data/quotation.pyc`；`python -X utf8 -m pytest -q tests/test_algorithm_correctness.py test_deep_nesting_pressure.py test_control_flow_completeness_matrix.py test_complete_syntax_coverage.py test_boundary_cases.py test_core_functional.py`；IV.2 自检见 `.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round9/VERIFICATION.md` §三 |

## ADDED Requirements

### Requirement: 基本比较器冻结

系统 SHALL 保持 `scripts/pyc_verify.py` 与 `pylingual/equivalence_check.py::compare_pyc` 的字节、行为、容差和 verdict 语义不变。任何改动、替换、包装降级或 tolerance 放宽 SHALL 使本规范验收失败。

当前冻结基线（SHA256，基线 commit `e755d773`）：

| 文件 | SHA256 |
|---|---|
| `scripts/pyc_verify.py` | `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4` |
| 外部 `pylingual/equivalence_check.py`（`D:\Desktop\ptrade相关\pylingual\pylingual\equivalence_check.py`） | `9C7567BD6776B36B6AF1991AF222CF79E48412335CA01CBB07146F9ED50045A6` |

#### Scenario: 比较器被修改
- **WHEN** `git diff` 显示 `scripts/pyc_verify.py` 或外部比较器 SHA256 变化
- **THEN** 验收立即失败，并记录为“比较器污染”，不得用新读数宣称完备

#### Scenario: 新增语义判据
- **WHEN** 需要执行级语义差分
- **THEN** 只能以新增工具 `tools/completeness/semantic_diff.py` 作为附加判据，基本比较器仍按原样独立运行

### Requirement: 可达性表

实现前 SHALL 产出并评审 `REACHABILITY.md`，表中每一行必须填写：

1. 有限输入来源；
2. 生成器或执行器；
3. 验收命令；
4. 阈值。

#### Scenario: 任一格为空
- **WHEN** 表中任意单元格为空、`TBD` 或“待定”
- **THEN** 规范状态记 `NOT READY`，不得进入实现

#### Scenario: 输入来源无限
- **WHEN** 某行只能写成“所有可能程序”或“所有可能输入”
- **THEN** 该行不合格；必须改为有限的语法产生式、规则或语料集合

### Requirement: J 空间五个维度与 J 记录最低五字段

J 空间 SHALL 按 **形态 / 宿主 / 深度 / 变体 / 可调用性** 五个维度组织。每条 J 记录 SHALL 至少包含 `p_j`、`pyc`、`expected_label`、`input_model`、`excluded` 五个字段。其中 `expected_label` SHALL 承载形态、宿主、深度、变体四个维度；`input_model.calls` SHALL 承载可调用性维度。每条 J SHALL 至少有一个可调用入口；module-only 只能算导入证据，不能算语义覆盖。

#### Scenario: 维度与字段的对应
- **WHEN** 生成或审计一条 J
- **THEN** `expected_label` 必须包含 `form`、`host`、`depth`、`variant`，`input_model` 必须包含非空 `calls`

#### Scenario: 缺 source
- **WHEN** J 条目缺 `p_j`
- **THEN** 覆盖检查器输出 `source_missing`，该条目不得进入覆盖分子

#### Scenario: 缺 pyc
- **WHEN** J 条目缺 `pyc`
- **THEN** 覆盖检查器输出 `pyc_missing`，该条目不得进入覆盖分子

#### Scenario: 缺 calls
- **WHEN** `input_model` 缺 `calls`
- **THEN** 覆盖检查器输出 `calls_missing`，该条目不得进入覆盖分子

### Requirement: R7 code object 阻断

任何 `co_code`、`co_consts`、`co_exceptiontable` 的 code object 差异 SHALL 默认判 `DIFFERENT`。只有经过书面 tolerance 且不改变行为语义的字段可以忽略。

#### Scenario: R7 与 R1 同时出现
- **WHEN** 产物 code object 与原件不同，且真实调用出现返回值差异
- **THEN** 记录 `R7 + R1`，按 `DIFFERENT` 计入失败，不得只写“metadata only”

#### Scenario: 仅 R7 差异
- **WHEN** R1–R6 相等但 R7 code object 不同
- **THEN** 仍判 `DIFFERENT` 或 `INCONCLUSIVE`，不得计入覆盖

### Requirement: B142 嵌套 finally/continue 修复

系统 SHALL 修复嵌套 `try/finally` 中 `continue` 的 finally 副本归属：内层正常路径副本必须归内层 finally，外层不得重复认领；`continue` 回边必须保留。

#### Scenario: `v_nest_fin_continue([[0, 1]])`
- **WHEN** 反编译 `v_b71_face.pyc` 并调用 `v_nest_fin_continue`
- **THEN** 原件与产物返回序列逐项相等，且 `semantic_diff` 无 R1/R7 失败

#### Scenario: 嵌套 finally 异常路径
- **WHEN** 内层 finally 体抛异常
- **THEN** 先执行内层 finally，再执行外层 finally，最后传播异常，产物顺序与原件一致

### Requirement: 任意语法覆盖证据

系统 SHALL 对完整 CPython 3.11 语法族建立可枚举证据：J 空间（五个维度）、25 行深层矩阵、402 语料、46 个真实 pyc、fuzz 模板、≥3 级宿主组合。每个语法族 SHALL 至少有一个可调用条目和一个语义差分记录。

#### Scenario: 新增/遗漏语法
- **WHEN** 语法族没有 J 条目或没有可调用证据
- **THEN** 覆盖检查器输出未覆盖，G1 失败，不得宣称“任何语法”

#### Scenario: 组合深度
- **WHEN** `if×for×try×match×with×async` 在同一函数叠加
- **THEN** 至少一个 ≥3 级组合条目通过语义差分；否则登记新破口

### Requirement: 全量语义与变异证据

系统 SHALL 在全量 J（1556 条，或经审计扩展后的 J v3）上跑 C1–C5；SHALL 对 402 语料与 46 个真实 pyc 跑语义差分；SHALL 跑完整变异总体，漏检率目标为 0。

#### Scenario: 缺源/缺 pyc
- **WHEN** J 条目缺 source 或缺 pyc
- **THEN** 必须先恢复/生成或登记为不可判定；不得用样本读数代替全量

#### Scenario: 变异漏检
- **WHEN** 任一已知错误产物未被判据捕获
- **THEN** 登记判据盲区，G3 失败，并补判据后重跑

### Requirement: 规则覆盖义务

339 条规则 SHALL 每条绑定 witness/trace；`open = 0` 之前 G4 不得判 PASS。

#### Scenario: 规则无 trace
- **WHEN** 某规则只有 manifest 记录、没有触发证据
- **THEN** 该规则保持 open，G4 仍为 INCONCLUSIVE

### Requirement: 独立 canary 与诚实读数

G6 SHALL 使用独立 custody/轮换；单代理本地 bootstrap 只能标 `local canary`。任何页面 SHALL 同时给出形态基线与判定空间双读数。

#### Scenario: 无独立 custody
- **WHEN** 无法提供独立保管
- **THEN** G6 记为 FAIL/不可满足，不得用 24/24 EQUAL 冒充 PASS

#### Scenario: 报告完备
- **WHEN** 任一 G1–G5 未达标或独立 G6 未满足
- **THEN** 产品完备与独立保证分别标注；不得用一项掩盖另一项，也不得写“形态基线达成（v8）= 完备”

## MODIFIED Requirements

### Requirement: 完备性定义

原“完备占比 = 完备形态数 ÷ 128”修改为：产品完备 = **可达性表五行全部达标**。形态基线保留为历史口径；独立 canary 全绿另列为独立保证，不混入产品完备分子。

### Requirement: 验证序

原六步增加：`REACHABILITY.md`、基本比较器独立回归、可调用语义差分、R7 阻断、变异校准、规则 witness。基本比较器仍是回归门禁，但不是完备性的充分证据；独立 canary custody 在产品验收后单独执行。

## REMOVED Requirements

### Requirement: module-only EQUAL 等于覆盖

**Reason**：`JS-IF-076` 已证明 module import 成功时函数体仍可错误，R1–R6 全相等；module-only 会产生假绿。
**Migration**：所有旧 module-only 记录降级为 `probe_only`，补 calls 后重跑。

### Requirement: R7 可当 metadata 忽略

**Reason**：六条 J R7 中 5 条是 B142 code object 差异，1 条是 x01 结构差；R7 是当前唯一能发现部分函数体缺陷的信号。
**Migration**：R7 code object 差异默认阻断；tolerance 必须书面登记。

### Requirement: v8 128/128 即完备

**Reason**：128 是形态计数，折叠了宿主、变体、深度与可调用性；攻击已证明其不能推出语义完备。
**Migration**：128 保留为历史形态基线；产品完备改由可达性表五行决定，独立保证另列。

### Requirement: 逐例打补丁也算推进

**Reason**：按 B 编号/探针名逐例加分支会把未知缺陷面变成无限打地鼠，无法覆盖“任何语法”。
**Migration**：每个修复必须归入根因族并落在最早共同机制；单点补丁不计关闭，族级谓词 + 邻域回归才算。
