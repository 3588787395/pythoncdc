# 迭代区域测试修复 Spec

## Why

pythoncdc 反编译器在 10 类区域（IF / LOOP / TRY / WITH / MATCH / TERNARY / BOOLOP / CHAINED_COMPARE / ASSERT / ASYNC）上存在大量反编译缺陷。需要通过"测试工程师→修复工程师"的对抗性迭代，逐区域、逐轮地暴露并修复缺陷，最终达到字节码 100% 等价。

## What Changes

- 按"10 类区域 × 20 轮"的节奏推进对抗性测试修复
- 每轮：测试工程师产 `test_findings.md`（10+ 错误）→ 修复工程师产 `fix_report.md`（修复+回归）
- 修复必须严格依"区域归约算法 4 原则"：自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口
- 禁止：跨区域启发式特例 / 后处理补丁 / 启发式优先级覆盖 / 展平嵌套
- 每轮必须 push 到远程（血泪教训：R4-6 因未 push 全部丢失）

## Impact

- 影响代码：`core/cfg/region_analyzer.py` / `core/cfg/region_ast_generator.py` / `core/cfg/ast_generator_v2.py` / `core/cfg/code_generator.py`
- 影响测试：`tests/exhaustive/<region>/` 每轮新增 10+ 测试
- 基线 100% 不可退化，每步回归验证

## ADDED Requirements

### Requirement: 区域对抗性测试迭代
系统 SHALL 支持按区域、按轮次地暴露并修复反编译缺陷。每轮包含测试发现、修复实施、全量回归、修复报告四个阶段。

#### Scenario: 单轮迭代成功
- **WHEN** 测试工程师产出 N 个新错误（test_findings.md）
- **AND** 修复工程师按算法 4 原则修复 M 个错误（M >= 5）
- **AND** 全量回归无退化（基线失败数不增）
- **THEN** 该轮判定为成功，写 fix_report.md，更新 tasks.md

#### Scenario: 退化回滚
- **WHEN** 修复引入退化（基线失败数增加）
- **THEN** 回滚该修复，换方案重试

### Requirement: 修复依区域归约算法 4 原则
所有修复 SHALL 遵循：
1. 自底向上归约（自内层区域向外层）
2. 每块唯一归属（任一时刻一块只属一区域）
3. 嵌套即抽象节点（子区域在父区域中是单抽象节点）
4. 父引用子入口（父的 then/else 列表引用子区域入口）

#### Scenario: 禁止跨区域启发式
- **WHEN** 修复方案需要为某区域加特例
- **THEN** 判定违反原则，拒绝该方案

### Requirement: Ternary 区域 Round 01 修复
针对 R1 测试工程师发现的 17 个 ternary 缺陷，按 P0/P1/P2 优先级修复，目标至少 5 个 bug。

#### Scenario: P0 R4 修复（ternary 作为外层表达式操作数）
- **WHEN** ternary 作为 compare 左操作数 / 方法调用参数 / starred 表达式
- **THEN** merge_block 的消费指令（COMPARE_OP / CALL / LIST_EXTEND）应归属到 ternary 父区域

#### Scenario: P0 R1 修复（walrus 在 ternary body/orelse）
- **WHEN** ternary 值块含 walrus 副作用（COPY 1 / STORE_*）
- **THEN** walrus 视为值表达式内子节点，不破坏外层单表达式性

## MODIFIED Requirements

### Requirement: _is_single_expression_block
原：拒绝任何含 STORE_* 的块。
改：识别 walrus 的 `COPY N / STORE_*` 模式为子表达式副作用，剥离后判定单表达式性。依据「嵌套即抽象节点」。

### Requirement: _detect_ternary_context
原：仅识别 PUSH_NULL + LOAD_* 调用模式。
改：新增 LOAD_METHOD 调用模式识别；新增 COMPARE_OP 后含 STORE_* 的赋值上下文识别。

### Requirement: CodeGenerator Starred 渲染
原：`*{value_code}` 直接渲染。
改：当 value 是低优先级复合表达式（IfExp/BoolOp/NamedExpr/Lambda/Yield/BinOp/UnaryOp/Compare/Starred）时，渲染为 `*({value_code})`。
