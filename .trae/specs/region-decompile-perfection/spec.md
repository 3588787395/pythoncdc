# 区域反编译逻辑完善与字节码一致性 Spec

## Why

当前区域归约反编译器存在两层测试基线：

1. **测试矩阵**（`run_test_matrix.py` 覆盖 L1/L2/L3/P1 共 1870 个用例）：**5 失败**
   （99.7% 通过率），分别为 L1 类别 1 个、L2 类别 3 个、P1 类别 1 个。
2. **match_region 独立测试集**（`tests/exhaustive/match_region/`，~200 个用例，**未纳入**
   `run_test_matrix.py`）：**44 失败**，覆盖 m013/m026-029/m036/m038-043/m047-048/
   m05matchmapping×3/m06matchguard×3/m080/m083/m084/m093/m094/m096/m098/m100/m101/m104/
   m106matchguardboolop/m107matchinfuncreturn/m13matchclassargs×3/m15matchmappingkey×3/
   m16matchguardcomplex×3/m30matchclassmultiattr×3。

**合计 49 失败**，距离用户要求的 **100% 成功率与字节码完全匹配** 仍有差距。

各识别方法（`_identify_*_regions`）的反编译逻辑注释不统一、不完整，部分逻辑停留在
「模式匹配 + 后处理补丁」层面，违反区域归约算法的核心原则（自底向上归约、每块唯一归属、
嵌套即抽象节点、父引用子入口）。

需要系统性地：
1. 为每一种区域类型的识别方法补充**算法级**的反编译逻辑注释（统一模板）。
2. **将 match_region 纳入测试矩阵**（修复 `run_test_matrix.py` 的 LEVEL_CATEGORIES），
   量化每一区域的失败率。
3. 根据**字节码不一致**的具体错误，修正识别逻辑（不是后处理补丁），重新写入注释。
4. 迭代到 100% 成功率 + 字节码完全匹配。

## What Changes

- **统一识别方法注释模板**：所有 `_identify_*_regions` 方法采用统一结构
  （算法描述 / 字节码模式 / 边界条件 / 归约语义 / AST 映射 / 已知失败模式）。
- **统一生成方法注释模板**：所有 `_generate_*` 方法在 `region_ast_generator.py`
  中明确「区域→AST 节点」的一一映射规则。
- **修复 73 个失败用例**：按区域类型分批修复，每批修复后回归测试，避免引入回归。
- **建立字节码一致性验证闭环**：每次逻辑修改后必须运行 `tests/exhaustive/run_test_matrix.py`
  + 失败用例的字节码 diff，确保**字节码完全匹配**而非「语义等价」。
- **消除跨区域启发式规则**：识别阶段出现的「跨区域特例判断」「后处理 patch」一律
  回归到区域归约算法本身修正（参考 `analyze()` 方法已确立的 4 条核心原则）。
- **强化归约顺序**：自底向上识别 → 嵌套区域作为父区域的抽象入口节点 →
  父区域 `then/else/body` 列表只引用子区域入口块（不是子区域所有块）。

**BREAKING**: 无（不改变对外 API，仅完善识别逻辑与注释）。

## Impact

- **Affected specs**: 无（首份 spec）。
- **Affected code**:
  - `core/cfg/region_analyzer.py` — 10 个 `_identify_*_regions` 方法 + `analyze()` 编排
  - `core/cfg/region_ast_generator.py` — 18 个 `_generate_*` 方法
  - `core/cfg/dominator_analyzer.py` — 回边检测、支配树（被大量补丁覆盖，需澄清边界）
  - `core/cfg/structured_analyzer.py` — 旧补丁式分析器（参考对比，不修改）
  - `tests/exhaustive/` — 现有测试矩阵（运行验证，不修改测试）
  - `tests/nook/` — 真实代码模式测试（运行验证）
- **Affected regions (10 类)**:
  1. `WHILE_LOOP` / `FOR_LOOP` — `_identify_loop_regions` / `_generate_loop`
  2. `IF` / `IF_THEN_ELSE` / `IF_ELIF_CHAIN` — `_identify_conditional_regions` / `_generate_if`
  3. `TRY_EXCEPT` / `TRY_FINALLY` — `_identify_try_except_regions` / `_generate_try`
  4. `WITH` — `_identify_with_regions` / `_generate_with`
  5. `MATCH` — `_identify_match_regions` / `_generate_match`
  6. `ASSERT` — `_identify_assert_regions` / `_generate_assert`
  7. `BOOL_OP` — `_identify_boolop_regions` / `_generate_boolop`
  8. `TERNARY` — `_identify_ternary_regions` / `_generate_ternary`
  9. `CHAINED_COMPARE` — `_identify_chained_compare_regions`（无独立 generate，复用 If）
  10. `SEQUENCE` — `_identify_sequence_regions` / `_generate_basic_region`

## ADDED Requirements

### Requirement: 统一识别方法注释模板

每一个 `_identify_<type>_regions` 方法的 docstring **SHALL** 包含以下 6 个固定小节，
顺序与命名严格统一：

1. **【区域类型】** — 区域名称（中英对照）+ RegionType 枚举值
2. **1. 算法描述（基于"No More Gotos"论文）** — 归约阶段（Phase N）、识别策略、归约过程（Step 1..N）
3. **2. 字节码模式（CPython 编译器行为）** — 模式 A/B/C... 含源码示例 + 字节码结构 + 特征指令
4. **3. 边界条件（数学性质）** — 基于支配树/回边的性质、边界确定规则、嵌套处理规则
5. **4. 归约语义（与父区域的契约）** — 入口块定义、父区域引用规则、子区域块不出现在父区域展开中
6. **5. AST 映射** — 对应的 `_generate_<type>` 方法名 + AST 节点类型 + 关键字段映射
7. **6. 已知失败模式** — 当前测试矩阵中失败的用例编号 + 失败原因（字节码 diff 摘要）+ 修复状态

#### Scenario: 注释模板合规
- **WHEN** 检查任意 `_identify_*_regions` 方法的 docstring
- **THEN** 必须包含上述 6 个小节标题，且每节有实质内容（非空、非 TODO）

#### Scenario: 失败模式可追溯
- **WHEN** 某区域类型在测试矩阵中有失败用例
- **THEN** 该区域的「6. 已知失败模式」小节**SHALL**列出每个失败用例的文件名、字节码差异摘要、修复状态

### Requirement: 统一生成方法注释模板

每一个 `_generate_<type>` 方法的 docstring **SHALL** 包含以下 4 个固定小节：

1. **输入契约** — 接收的 Region 子类、关键字段（entry/blocks/children）
2. **AST 映射规则** — 输出的 AST 节点类型 + 字段对应关系（一一映射表）
3. **子区域处理** — 如何递归调用子区域的 `_generate_region`、如何处理嵌套
4. **字节码一致性约束** — 生成的 AST 重编译后**必须**与原始字节码一致（列出关键约束）

#### Scenario: 生成方法注释合规
- **WHEN** 检查任意 `_generate_*` 方法的 docstring
- **THEN** 必须包含上述 4 个小节标题

### Requirement: 字节码完全一致性验证

每一次反编译逻辑修改后，**SHALL**运行以下验证并记录结果：

1. `python tests/exhaustive/run_test_matrix.py` （L1/L2/L3/P1 全量）
2. 失败用例的 `dis.get_instructions()` 字节码 diff（原始 vs 重编译）
3. 通过率必须达到 **100%**，且字节码 diff 为空

#### Scenario: 修改后回归测试
- **WHEN** 修改任意 `_identify_*` 或 `_generate_*` 方法
- **THEN** **MUST**运行全量测试矩阵并报告通过率
- **AND** 若通过率下降，**MUST**回滚或修正至不下降

#### Scenario: 字节码 diff 为空
- **WHEN** 对任一失败用例执行 `_compare_code_objects(original, recompiled)`
- **THEN** 返回值**MUST**为 `None`（无差异）

### Requirement: 区域归约算法符合度验证

所有识别方法**SHALL**遵守以下 4 条核心原则（已在 `analyze()` 注释中确立）：

1. **自底向上归约**：从最内层区域向最外层识别（归约顺序），不回溯修正
2. **每块唯一归属**：任一基本块在任何层级只属于一个区域
3. **嵌套即抽象节点**：嵌套区域在其父区域中表示为单个抽象节点
4. **入口引用语义**：归约后父区域的 then/else/body 列表引用**子区域入口块**，
   而非子区域的所有块

#### Scenario: 无跨区域启发式规则
- **WHEN** 审查识别方法代码
- **THEN** **MUST NOT**出现以下反模式：
  - 跨区域特例判断（如「如果是 try 内的 if 则...」）
  - 后处理补丁（如「识别完后修正 then/else 列表」）
  - 启发式优先级覆盖（如「match 优先于 if，除非...」）
  - 破坏嵌套天然支持的扁平化逻辑

## MODIFIED Requirements

### Requirement: analyze() 编排方法

`RegionAnalyzer.analyze()` 方法**SHALL**维持当前「固定优先级三阶段流水线」
（TRY > LOOP > WITH/MATCH/ASSERT > CHAINED_COMPARE > BOOLOP > TERNARY > IF > SEQUENCE），
但在 docstring 中**必须**明确：

1. 该流水线是论文 4.1 迭代归约循环的工程近似
2. 等价性条件：满足 4 条核心原则时与真·迭代归约等价
3. 任何识别方法都不得以跨层/跨区域的特例判断破坏这些原则
4. 如遇特例，**MUST**回归到区域归约本身修正（而非添加补丁）

#### Scenario: 编排方法注释完整
- **WHEN** 检查 `analyze()` 方法 docstring
- **THEN** 必须包含「核心原则」「各区域类型反编译逻辑对照表」「当前实现说明」三段

## REMOVED Requirements

### Requirement: 后处理补丁机制

**Reason**: 违反区域归约算法的「一次正确」原则，导致逻辑分散、难以维护、
字节码不一致。
**Migration**: 所有后处理补丁（如 `structured_analyzer.py` 中的 patch_detector
调用、`ast_generator_v2.py` 中的二次修正）**MUST**迁移到识别阶段的算法修正。
本 spec 不删除旧代码（保留作为参考对比），但**禁止**在新的识别逻辑中引用。

### Requirement: 启发式优先级覆盖

**Reason**: 「match 优先于 if，除非...」「try 优先于 loop，除非...」等启发式规则
破坏了算法对嵌套的天然支持，导致边界用例失败。
**Migration**: 优先级**MUST**由归约顺序（自底向上）+ 块的归属关系（每块唯一归属）
天然决定，而非显式的优先级覆盖。
