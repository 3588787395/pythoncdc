# 算法评估报告（Phase 1）

> 基于 Phase 0.2 的 `failures_root_causes.md`（7 个算法根因聚类），
> 对当前区域归约算法进行根本性反思，论证新区域类型 / 新方法 / WARN 消除方案。
> 遵循规范核心约束：禁止跨区域跨层次启发式 / 禁止后处理补丁 / 必须识别阶段一次正确。

## 1. 现有 19 个 RegionType 覆盖范围审计

当前 `RegionType`（region_analyzer.py L128-147）：
BASIC, SEQUENCE, IF, IF_THEN, IF_THEN_ELSE, IF_ELIF_CHAIN,
WHILE_LOOP, FOR_LOOP, TRY_EXCEPT, TRY_FINALLY, WITH, MATCH, ASSERT,
BREAK, CONTINUE, PASS, RETURN, BOOL_OP, TERNARY。

### 能正确识别的模式（含通过测试）
- IF/IF_THEN_ELSE/IF_ELIF_CHAIN：基础 if/elif/else（if_region 787 passed）
- WHILE_LOOP/FOR_LOOP：基础循环（while_loop 120p, for_loop 192p）
- TRY_EXCEPT/TRY_FINALLY：基础 try（try_except 228p）
- WITH：基础 with（with_region 191p）
- MATCH：基础 match（match_region 193p）
- BOOL_OP：基础 boolop（boolop 132p）
- TERNARY：module-level/function-tail 三元（ternary 485p）

### 不能正确识别的模式（含失败用例，来自根因映射）
- **根因 A**：while 条件位三元（9 failed）— TERNARY 识别晚于 LOOP
- **根因 C**：assert + if 混淆（4 failed）— ASSERT 与 IF 边界不清
- **根因 D**：子表达式三元（BUILD_SLICE/TUPLE/COMPARE 内嵌三元，6 failed）—
  TERNARY 的 value_target 语义未覆盖值消费
- **根因 E**：顺序语句 boolop 边界（已修但补丁违反原则）— BOOLOP 链检测用指令判据

### 候选新类型评估
- **SUBEXPR_TERNARY（子表达式三元）**：不采用。三元本就是 TERNARY 类型，
  问题在生成阶段 value_target 语义，不是识别阶段类型缺失。新增类型会破坏
  「嵌套即抽象节点」（三元在子表达式位置应是值节点，不是独立区域）。
- **WHILE_COND_TERNARY（while 条件三元）**：不采用。同上，问题是识别顺序，
  不是类型缺失。

**结论：不新增 RegionType。** 所有失败根因都可由现有类型覆盖，
问题在识别顺序、生成阶段语义、测试断言标准。

## 2. 新方法论证

### 候选方法 1: 迭代归约替代固定优先级流水线

**现状**（analyze() L1126-1175）：固定优先级三阶段流水线
TRY > LOOP > WITH/MATCH/ASSERT > CHAINED_COMPARE > BOOLOP > TERNARY > IF > SEQUENCE。

**问题**：固定优先级无法表达「三元是 while 条件的子表达式，应先于 while 识别」。
根因 A 正是此问题：LOOP 先于 TERNARY，LOOP 的 header 吞掉三元 cond 块。

**论证**：
- 真正的迭代归约（论文 4.1）是「反复扫描 CFG，每次归约最内层可归约区域，
  直到无可归约」。这天然保证子表达式先于父结构识别。
- 但当前流水线在「满足 4 原则时与迭代归约等价」（analyze() docstring L1067-1071）。
  问题在于**当前优先级不满足「子表达式先于父结构」**：三元是 while/if 的子表达式，
  却排在 LOOP/IF 之后。

**采用结论：不全面改为迭代归约**（风险过大，3000+ 通过测试可能回归），
**但修正优先级**：把 TERNARY 和 BOOL_OP 的「条件位/子表达式」识别提前到
LOOP 和 IF 之前。具体：
- 在 LOOP 识别前，对每个潜在 header_block 做「条件位三元」探测，
  若命中则先归约为 TERNARY，LOOP 引用其入口。
- 在 IF 识别前，对每个潜在 cond 块做「条件位三元/boolop」探测。

这是「固定优先级流水线内的局部子表达式优先」，不是全面迭代归约，
风险可控，且遵守「识别阶段一次正确」。

### 候选方法 2: 异常表驱动识别

**现状**：`_identify_try_except_regions` 已部分使用异常表。
**论证**：根因映射中无 TRY 相关失败（try_except 228p 全通过）。
**采用结论：不采用**，当前足够。

### 候选方法 3: 支配树驱动边界

**现状**：dom_analyzer 已用于 loop 检测和 merge 块定位。
**论证**：根因映射中无「merge 块定位错误」类失败。
**采用结论：不采用**，当前足够。

## 3. 算法根因修正方案（按根因映射优先级）

### 方案 A: while 条件位三元（根因 A，9 failed）

**算法根因**：TERNARY 识别晚于 LOOP，LOOP header 吞掉三元 cond 块。

**修正**（识别阶段，region_analyzer.py）：
在 `_identify_loop_regions` 之前，新增 `_identify_cond_position_ternary_regions`：
扫描每个潜在 loop header（含 POP_JUMP_IF_* 的块），若该块是三元 cond 块
（IF_FALSE 跳转到 false_value，true_value 经 JUMP_FORWARD 到 merge），
先归约为 TERNARY，把 cond 块从后续 LOOP 识别的 header 候选中移除。
LOOP 识别时遇到已被 TERNARY 占用的 header，引用 TERNARY 入口作为条件节点。

**覆盖**：walrus 包裹（COPY/STORE 后 COMPARE_OP）、比较包裹（COMPARE_OP 在 merge 后）、
嵌套三元 —— 全部由「三元结构模式」（IF_FALSE + JUMP_FORWARD + merge）统一识别，
不依赖具体指令（POP_TOP/STORE_*）判据。这是普遍性方案。

**原则合规**：识别阶段一次正确（非后处理）；不跨层启发式（基于三元结构模式）；
每块唯一归属（TERNARY 先占 cond 块，LOOP 引用入口）。

### 方案 C: assert/if 边界（根因 C，4 failed）

**算法根因**：ASSERT 识别未区分 LOAD_ASSERTION_ERROR 与 if-raise。

**修正**（识别阶段）：`_identify_assert_regions` 在 IF 之前运行（当前已是），
但需增强：若 body 块首指令是 LOAD_ASSERTION_ERROR + RAISE，强制归约为 ASSERT，
阻止 IF 吞并。当前 assert_regions 已识别，但 `_identify_conditional_regions`
可能仍把同一块建 IfRegion。需在 IF 识别时跳过已被 ASSERT 占用的块。

**原则合规**：识别阶段一次正确；每块唯一归属。

### 方案 D: 子表达式三元（根因 D，6 failed）

**算法根因**：TernaryRegion 生成时 value_target 未覆盖 BUILD_SLICE/TUPLE/COMPARE 消费。

**修正**（生成阶段，region_ast_generator.py）：`_generate_ternary` 检查
merge_block 后继指令，若是 BUILD_SLICE/BUILD_TUPLE/COMPARE_OP/BINARY_OP 等
「值消费」指令，把三元作为子表达式节点嵌入该指令的操作数位置，
而非生成独立语句。

**原则合规**：生成阶段语义补全（非后处理补丁）；嵌套即抽象节点
（三元作为值节点嵌入）。

### 方案 E: 顺序 boolop 边界重设计（根因 E，已修但需重设计）

**算法根因**：当前修复用 POP_TOP/STORE_* 首指令判据，是实例驱动补丁。

**修正**（识别阶段）：`_detect_boolop_short_circuit_chain` 的 fall-through 扩展，
判据改为「succs[0] 的短路跳转目标是否是当前 chain 的 merge」。
若 succs[0] 是下一语句的 entry（其短路目标指向不同的 merge），
则不扩展。这基于「短路跳转目标语义」，不依赖具体指令。

**原则合规**：识别阶段一次正确；不跨层启发式（基于短路语义）。

## 4. 2 个 WARN 消除方案

（规范 Task 1.4，已在 Phase 2.5 完成，此处仅确认）
- `_merge_consecutive_with_regions` 前移：已完成（Phase 2.5.1）
- try_except `depth` 改异常表判定：已完成（Phase 2.5.2）

## 5. 优先级与依赖关系

1. **方案 A（while 条件位三元）** — 最高优先级，9 个失败，独立无依赖
2. **方案 C（assert/if 边界）** — 4 个失败，独立
3. **方案 D（子表达式三元）** — 6 个失败，依赖 A（三元识别正确后才能修生成）
4. **方案 E（boolop 边界重设计）** — 重设计现有补丁，依赖无
5. **根因 B/G（STRICT_ASSERT ~60 个）** — 评估测试断言，不修反编译器
6. **根因 F（测试框架 41 个）** — 修测试，不修反编译器

## 6. 不变量检查实施计划（C2.11-C2.14）

在上述方案实施后，增加 debug 模式不变量检查：
- `analyze()` 末尾：每块唯一归属检查（每块恰好属于一个区域）
- `_generate_*` 中：子区域抽象节点检查（嵌套区域作为单节点引用）
- `_generate_*` 中：入口引用语义检查（父引用子入口，非子全部块）
