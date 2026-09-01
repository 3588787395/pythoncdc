# 区域归约算法深度迭代与全测试集 100% 字节码一致性 Spec

## Why

前置三个 spec（`region-decompile-perfection` / `refine-region-algorithm` /
`region-100pct-bytecode-match`）均标记「100% 2068/2068 完成」，但该 100% **仅覆盖**
`tests/exhaustive/run_test_matrix.py` 所收集的子集。仓库内还存在大量未被该矩阵纳入的
对抗性测试集，实际状态为：

| 测试集 | 失败 / 通过 | 来源文件 |
| --- | --- | --- |
| `tests/exhaustive/if_region/`（c01-c37 + if01-if37 + adv01-adv17，~370 用例） | ~75 失败 | `if_region_failures.txt` |
| `tests/exhaustive/loop/`（含 while/for 全对抗矩阵） | 128 失败 / 181 通过 | `loop_errors.txt` |
| `tests/exhaustive/match_region/` 之外的 match 用例 | 74 失败 / 93 通过 | `match_errors.txt` |
| `tests/nook/`（~130 真实代码模式） | 13 failures + 25 errors（前置 spec 已记录） | `region-decompile-perfection` Phase 5.3 |
| `tests/control_flow_matrix/`（基础+对抗+完备性） | 未纳入 run_test_matrix | `tests/control_flow_matrix/base.py` |

用户原话：「经过大量的测试修复，仍然不断有错误的实例产生，仔细阅读代码，深度思考
怎么才能使程序能反编译所有情况。是否需要更多的区域，或是更好的方法」。

典型失败模式（来自 `if_region_failures.txt`）：
- `指令数不匹配: 24 vs 29` / `15 vs 8` / `14 vs 11` — 识别多/少块
- `反编译结果中未找到预期的区域类型 IF_REGION` — 区域被错误归约为其他类型
- `反编译结果语法错误` — AST 生成产出了非法 Python
- `指令7操作码不匹配: LOAD_ASSERTION_ERROR vs LOAD_CONST` — assert 与 if 混淆
- `嵌套code object不匹配` — 子 code object 内的识别错误

这些失败根因不是「个别 case 修补」可解决的——它们反映出**算法在以下维度的根本性不足**：

1. **区域类型不够**：当前 19 个 RegionType（含 BREAK/CONTINUE/PASS/RETURN 等语句级）
   是否覆盖了 CPython 3.11+ 字节码的所有结构化模式？例如：
   - `with` + `try` 复合清理块（te046 已暴露）
   - `for-else` / `while-else` 中 else 的归约边界
   - `match` 的 guard 块与 OR 模式的复合 case 入口
   - `async with` / `async for` 的异步语义区域
   - 嵌套 comprehension 与 walrus 的 code object 边界

2. **归约顺序不够严格**：当前 `analyze()` 的「固定优先级三阶段流水线」是论文迭代归约的
   工程近似。当多个区域类型在同一个块上竞争归属时（如 if/boolop/ternary/match-guard），
   优先级覆盖破坏「自底向上归约」原则。

3. **子区域抽象泄漏**：尽管 spec 声称「嵌套即抽象节点」，实际代码在 `_generate_*` 阶段
   仍出现「子区域块被父区域重复展开」（te046 的 spurious `if True: pass` 即此症）。

4. **后处理补丁回潮**：`_merge_consecutive_with_regions` 等后处理被前置 spec 标记为
   「工程近似 WARN」，但未真正消除——只是不再新增类似补丁。

本 spec 在前置工作基础上，**以全部测试集（nook + control_flow_matrix + exhaustive
所有子目录 + testqouter/ok）为基线**，对每一区域类型执行深度「测试→字节码 diff→
算法根因修正→注释重写→回归」循环，直到全部测试集 100% 通过且字节码完全匹配。
**禁止跨区域跨层次的启发式规则，禁止破坏算法对嵌套的天然支持**。

## What Changes

### A. 算法根本性反思与重构
- **审计现有 19 个 RegionType**：列出每个类型的归约边界、AST 映射、失败用例集；
  识别「该类型不足以覆盖某些字节码模式」的情况
- **评估是否需要新增区域类型**：候选包括（需逐个论证必要性）：
  - `WITH_EXIT`（with 清理块作为独立区域，而非 WithRegion 的 exception_blocks）
  - `LOOP_ELSE`（for/while-else 的 else 作为独立区域，而非 LoopRegion.else_blocks）
  - `MATCH_GUARD`（match case 的 guard 作为独立区域，而非 MatchCase 的 guard 属性）
  - `IMPLICIT_RETURN`（隐式 module-level return None 作为独立区域）
  - `ASYNC_WITH` / `ASYNC_FOR`（异步语义区域，与同步分离）
- **评估是否需要更好的方法**：候选包括：
  - **真正的迭代归约**（替代固定优先级流水线）：每轮只识别「最内层」区域并归约，
    直到无可归约；用 `visited` 集合终止，无优先级覆盖
  - **基于异常表的结构化识别**：异常表（start/end/target）天然定义了 try 区域的
    嵌套层级，可作为 try/with 识别的算法基础（替代当前的指令模式匹配）
  - **支配树驱动的区域边界**：用支配关系（dom/frontier）定义 if/loop 区域的边界，
    而非启发式的「跳转目标距离」
- **消除 2 个 WARN**：`_merge_consecutive_with_regions` 后处理补丁前移至识别阶段；
  try_except 的 `depth` 字段特例改为异常表结构包含关系判定

### B. 测试基线扩展
- **建立全测试集基线**：将 `tests/exhaustive/if_region/`、`tests/exhaustive/loop/`、
  `tests/exhaustive/with_region/`、`tests/exhaustive/try_except/`、
  `tests/exhaustive/match_region/`、`tests/control_flow_matrix/`、`tests/nook/`、
  `ok/`、`testqouter/` 全部纳入基线统计（**不修改测试本身**）
- **按区域类型分类失败用例**：每一失败用例标注「失败类型」（指令数/操作码/语法错误/
  区域未识别/嵌套 code object 不匹配）+ 「所属区域类型」+ 「字节码 diff 摘要」
- **建立失败用例 → 区域类型 → 算法根因的映射表**：用于驱动算法修正（非补丁）

### C. 每区域的深度迭代循环
对 10 类区域（IF / LOOP / TRY / WITH / MATCH / ASSERT / BOOLOP / TERNARY /
CHAINED_COMPARE / SEQUENCE）的每一个，执行以下循环直到 100% + 字节码完全匹配：

1. **测试**：运行该区域所有测试集（含 nook/control_flow_matrix/exhaustive）
2. **字节码 diff**：对每个失败用例执行 `_compare_code_objects(original, recompiled)`，
   记录差异摘要（指令数/操作码/参数/嵌套 code object）
3. **算法根因修正**：根据 diff 定位算法缺陷（不是后处理补丁），修正识别逻辑；
   若现有区域类型不足，新增区域类型并重写归约顺序
4. **注释重写**：将该区域的反编译逻辑（识别策略 + 归约顺序 + AST 映射 + 已知失败模式）
   重新写入 `_identify_*_regions` 与 `_generate_*` 方法的 docstring，符合统一模板
5. **回归测试**：全测试集回归，确保不引入新失败

### D. 算法 4 原则强化
- **自底向上归约**：`analyze()` 改造为迭代归约（若评估可行），或保留流水线但
  明确文档化等价性条件
- **每块唯一归属**：在 `block_to_region` 中增加 invariant 检查（每个块仅归属一个区域）
- **嵌套即抽象节点**：在 `_generate_*` 中增加 invariant 检查（子区域块不出现在
  父区域展开中）
- **入口引用语义**：父区域的 then/else/body 列表仅引用子区域入口块（不是所有块）
- **禁止反模式**：跨区域特例 / 后处理补丁 / 启发式优先级覆盖 / 破坏嵌套的扁平化

### E. 注释模板（继承自前置 spec，强化「算法根因」节）
- **6 节识别方法模板**：1.算法描述 / 2.字节码模式 / 3.边界条件 / 4.归约语义 /
  5.AST映射 / 6.已知失败模式（**新增**：每条失败用例的「算法根因」与「修复策略」）
- **4 节生成方法模板**：输入契约 / AST映射规则 / 子区域处理 / 字节码一致性约束
  （**新增**：子区域抽象节点的不变量检查）

**BREAKING**: 无对外 API 变更。但 `RegionType` 枚举可能新增成员（内部）；
`analyze()` 内部实现可能从「固定优先级流水线」改为「迭代归约」（内部）。

## Impact

- **Affected specs**:
  - `region-decompile-perfection`（已完成，作为基线参考）
  - `refine-region-algorithm`（已完成，2 个 WARN 待本 spec 消除）
  - `region-100pct-bytecode-match`（已完成，但 100% 仅覆盖 run_test_matrix 子集）
  - `iterate-region-test-fix`（仅完成 IF 区域 R1-16，本 spec 接管剩余工作）
- **Affected code**:
  - `core/cfg/region_analyzer.py`（~13000 行）— 主要修改：识别逻辑算法化、
    可能新增 RegionType、可能改造 analyze() 为迭代归约、消除 2 个 WARN
  - `core/cfg/region_ast_generator.py`（~15500 行）— 配合识别阶段调整、
    子区域抽象节点不变量检查
  - `core/cfg/dominator_analyzer.py` — 若采用支配树驱动边界，需扩展 API
  - `core/cfg/exception_handler.py` — 若采用异常表驱动识别，需扩展 API
  - 测试文件**不修改**（仅运行验证）
- **Affected regions**: 10 类区域全部纳入深度迭代循环
- **Algorithm compliance**: 目标 FULLY COMPLIANT（0 WARN，0 反模式）
- **Risk**:
  - 改造 `analyze()` 为迭代归约可能导致大规模回归，需小步快跑 + 每步回归
  - 新增 RegionType 可能与现有 19 个类型冲突，需论证必要性
  - 全测试集基线扩展可能暴露 200+ 失败，需按区域类型分批修复

## ADDED Requirements

### Requirement: 全测试集基线建立

系统 **SHALL** 建立覆盖仓库内所有区域反编译测试的基线，包括：
- `tests/exhaustive/if_region/`（全部 c01-c37 + if01-if37 + adv01-adv17）
- `tests/exhaustive/loop/`（全部 while/for 对抗矩阵）
- `tests/exhaustive/with_region/`
- `tests/exhaustive/try_except/`
- `tests/exhaustive/match_region/`
- `tests/control_flow_matrix/`（全部 L1/L2/L3/L4 + completeness_matrix）
- `tests/nook/`（全部真实代码模式测试）
- `ok/`（区域测试集合）
- `testqouter/round1/round2/round3/`（轮次对抗测试）

基线 **SHALL** 记录每个测试集的：总用例数 / 通过数 / 失败数 / 跳过数 / 失败用例清单
（含失败类型与字节码 diff 摘要）。

#### Scenario: 基线统计完整
- **WHEN** 执行基线建立脚本
- **THEN** 输出每个测试集的通过率（如 `if_region: 295/370 = 79.7%`）
- **AND** 每个失败用例标注「失败类型」「所属区域类型」「字节码 diff 摘要」
- **AND** 失败用例 → 区域类型 → 算法根因的映射表生成

### Requirement: 算法根本性反思

系统 **SHALL** 完成对区域归约算法的根本性反思，输出「算法评估报告」包含：

1. **现有 19 个 RegionType 的覆盖范围审计**：每个类型能正确识别的字节码模式 +
   不能识别的字节码模式（列出具体失败用例）
2. **是否需要新增区域类型的论证**：对每个候选新类型（WITH_EXIT / LOOP_ELSE /
   MATCH_GUARD / IMPLICIT_RETURN / ASYNC_WITH / ASYNC_FOR），论证：
   - 不新增的代价（多少失败用例无法修复）
   - 新增的收益（覆盖多少失败用例）
   - 新增的风险（对现有区域的归约顺序影响）
   - 新增是否符合 4 原则（不破坏嵌套、不引入跨区域特例）
3. **是否需要更好的方法的论证**：对每个候选新方法（迭代归约 / 异常表驱动 /
   支配树驱动），论证：
   - 当前方法的根本性不足（哪些失败用例反映）
   - 新方法的算法正确性证明（满足 4 原则）
   - 新方法的工程可行性（实现复杂度、回归风险）
4. **2 个 WARN 的消除方案**：
   - `_merge_consecutive_with_regions` 后处理 → 识别阶段合并
   - try_except `depth` 字段特例 → 异常表结构包含关系判定

#### Scenario: 反思报告完整
- **WHEN** 检查算法评估报告
- **THEN** 必须包含上述 4 节，每节有实质内容（非 TODO、非空）
- **AND** 每个候选新类型/新方法有明确的「采用 / 不采用 + 理由」结论

### Requirement: 区域类型扩展（条件性）

**若**算法评估报告论证需要新增区域类型，**THEN** 系统 **SHALL**：
1. 在 `RegionType` 枚举中新增成员（含 docstring 说明归约边界）
2. 新增 `_identify_<new>_regions` 方法（符合 6 节模板）
3. 新增 `_generate_<new>` 方法（符合 4 节模板）
4. 在 `analyze()` 中正确编排新类型的归约顺序（不破坏现有顺序）
5. 在 `block_to_region` 中确保新类型的块归属不变量

#### Scenario: 新区域类型合规
- **WHEN** 新增区域类型 `NEW_TYPE`
- **THEN** `_identify_new_type_regions` docstring 符合 6 节模板
- **AND** `_generate_new_type` docstring 符合 4 节模板
- **AND** 新类型不引入跨区域特例（不依赖其他区域类型的状态）
- **AND** 全测试集回归无退化

### Requirement: 每区域深度迭代循环

对 10 类区域（IF / LOOP / TRY / WITH / MATCH / ASSERT / BOOLOP / TERNARY /
CHAINED_COMPARE / SEQUENCE）的每一个，**SHALL** 执行以下循环直到 100% + 字节码完全匹配：

1. **测试**：运行该区域所有测试集（含 nook/control_flow_matrix/exhaustive）
2. **字节码 diff**：对每个失败用例执行 `_compare_code_objects(original, recompiled)`
3. **算法根因修正**：根据 diff 定位算法缺陷，修正识别逻辑（不是后处理补丁）
4. **注释重写**：将反编译逻辑写入 `_identify_*` / `_generate_*` docstring
5. **回归测试**：全测试集回归，确保不引入新失败

#### Scenario: 区域迭代完成
- **WHEN** 区域 X 的迭代循环完成
- **THEN** 该区域所有测试集通过率 = 100%
- **AND** 该区域所有失败用例的 `_compare_code_objects()` 返回 `None`
- **AND** 该区域的 `_identify_*` / `_generate_*` docstring 反映最终算法状态
- **AND** 全测试集回归无退化

### Requirement: 算法 4 原则不变量检查

系统 **SHALL** 在 `analyze()` 与 `_generate_*` 中增加 4 原则的不变量检查
（debug 模式下断言，release 模式下跳过）：

1. **每块唯一归属**：`block_to_region[block_id]` 在归约完成后每个块仅归属一个区域
2. **嵌套即抽象节点**：`_generate_*` 展开父区域时，子区域的块不出现在父区域展开中
3. **入口引用语义**：父区域的 then/else/body 列表仅引用子区域入口块
4. **自底向上归约**：归约顺序中，子区域先于父区域识别

#### Scenario: 不变量检查通过
- **WHEN** 在 debug 模式下运行任意测试用例
- **THEN** 4 个不变量检查全部通过（无 AssertionError）
- **AND** release 模式下不引入性能开销

## MODIFIED Requirements

### Requirement: 区域识别算法（强化）

区域识别遵循自底向上归约顺序，每个块在任意层级只属于一个区域，嵌套区域在父区域中
作为单个抽象节点表示，父区域引用子区域入口块。识别阶段一次正确，不依赖后处理修正。
所有方法不包含硬编码深度上限。**强化**：
- 优先级覆盖**MUST**由归约顺序（自底向上）天然决定，而非显式优先级
- 后处理补丁**MUST NOT**存在（`_merge_consecutive_with_regions` 等迁移至识别阶段）
- 跨区域特例**MUST NOT**存在（try_except depth 字段等改为结构判定）
- 子区域抽象节点不变量在 debug 模式下检查

### Requirement: 注释模板（强化「算法根因」节）

10 个 `_identify_*_regions` 方法的 docstring 保持 6 节模板，但「6. 已知失败模式」
小节**MUST**为每条失败用例补充：
- **失败类型**（指令数 / 操作码 / 语法错误 / 区域未识别 / 嵌套 code object）
- **算法根因**（哪个算法步骤导致错误分类）
- **修复策略**（识别逻辑的具体修正，不是后处理补丁）
- **修复状态**（已修复 / 进行中 / 已知限制）

9 个 `_generate_*` 方法保持 4 节模板，**强化**「子区域处理」节：
- 子区域作为抽象节点的不变量检查
- 子区域入口块的引用规则
- 子区域块不出现在父区域展开中的保证

## REMOVED Requirements

### Requirement: 仅以 run_test_matrix.py 为基线

**Reason**: `run_test_matrix.py` 仅覆盖 2068 用例（L1/L2/L3/P1 子集），
遗漏 `tests/exhaustive/if_region/`、`tests/exhaustive/loop/`、
`tests/control_flow_matrix/`、`tests/nook/` 等共 500+ 对抗性用例。
前置 spec 的「100% 完成」是基于该不完整基线的虚假完成。

**Migration**: 改用全测试集基线（见 ADDED Requirement: 全测试集基线建立）。

### Requirement: 2 个 WARN 工程折中

**Reason**: `_merge_consecutive_with_regions` 后处理补丁与 try_except `depth`
字段特例被前置 spec 标记为「WARN 工程折中」，但用户明确要求「禁止跨区域跨层次
启发式规则」。这 2 个 WARN **MUST**在本 spec 中消除。

**Migration**:
- `_merge_consecutive_with_regions` → 前移至 `_identify_with_regions` 识别阶段
- try_except `depth` 字段特例 → 改为异常表 `(start, end, target)` 区间包含关系判定
