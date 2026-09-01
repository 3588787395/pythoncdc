# decompiler_test_comprehensive.pyc 区域归约算法完善 Spec

## Why

`decompiler_test_comprehensive.cpython-311.pyc` 是一个覆盖 Python 全语法的综合测试文件，包含 IF / LOOP / TRY / WITH / MATCH / ASSERT / BOOLOP / TERNARY / CHAINED_COMPARE / SEQUENCE 全部 10 类区域。当前反编译器在该文件上基线成功率为 87.50%（24 个函数中 21 个匹配），3 个函数存在字节码不一致。需要通过「测试工程师 + 修复工程师」10 轮对抗性迭代，以区域归约算法为核心，将反编译逻辑显式写入识别方法注释（6 节模板）与生成方法注释（4 节模板），驱动该 pyc 文件达到 100% 成功率与字节码完全匹配。

核心设计原则：
- **区域化分析**（Region-Based Analysis）：基于编译器理论中的区域分析算法，将 CFG 分解为层次化的区域
- **单向数据流**：分析结果从底层向上层传递，不回溯修正
- **一次正确**：每个结构在识别阶段就正确分类，不需要后处理修正
- **算法驱动**：用算法替代模式匹配，用数学性质替代启发式规则

算法基础：采用 "No More Gotos" (Launez et al., 2013) 论文中的结构化算法核心思想，结合 Python 字节码特性：
- 回边检测：基于支配树的标准回边检测算法（DominatorAnalyzer）
- 区域分类：将 CFG 节点集合分类为有限种区域类型
- 归约：将识别出的区域归约为单个节点，迭代直到整个 CFG 归约为一个节点
- AST 映射：每个区域类型对应唯一的 AST 节点类型

禁止跨区域跨层次的启发式规则，禁止破坏算法对嵌套的天然支持。

核心原则：
- 从最内层到最外层识别区域（归约顺序）
- 每个块在任何层级只属于一个区域
- 嵌套区域在其父区域中作为单个抽象节点表示
- 归约后：父区域的 then/else 列表引用子区域的入口，而不是子区域的所有块

## What Changes

### A. 区域注释模板强化

- **11 个 `_identify_*_regions` 方法** MUST 在 docstring 中包含 6 节模板：
  1. 区域类型（Region Type）
  2. 算法描述（Algorithm Description，含「No More Gotos」章节引用 + 区域归约 4 原则对应条款 + 自底向上归约顺序中的位置）
  3. 字节码模式（Bytecode Pattern）
  4. 边界条件（Boundary Conditions）
  5. 归约语义（Reduction Semantics，含归约顺序 / 唯一归属 / 嵌套抽象节点 / 入口引用语义）
  6. AST 映射 + 已知失败模式（AST Mapping & Known Failure Patterns）
- **9+ 个 `_generate_*` 方法** MUST 在 docstring 中包含 4 节模板：
  1. 输入契约（Input Contract）
  2. AST 映射规则（AST Mapping Rules）
  3. 子区域处理（Sub-region Handling）
  4. 字节码一致性约束（Bytecode Consistency Constraints）

### B. decompiler_test_comprehensive.cpython-311.pyc 验证

- 测试工程师反编译 `decompiler_test_comprehensive.cpython-311.pyc`，验证字节码一致性
- 对比反编译产物与原 pyc 字节码，输出不一致函数清单 + 成功率
- 针对每处不一致，构造 10+ 最小复现实例
- 统计反编译前后字节码一致函数数与成功率

### C. 持续双工程师迭代（10 轮）

每轮（round_NN，NN=01,02,...,10）：
1. **测试工程师**：反编译 `decompiler_test_comprehensive.cpython-311.pyc`，验证字节码一致性，列出不一致函数清单 + 成功率，针对不一致点构造 10+ 最小复现实例
2. **修复工程师**：依据测试报告，按区域归约算法完善 `_identify_*_regions` / `_generate_*` 方法，同步更新方法注释（6/4 节模板），运行回归测试
3. **commit + push**：commit message 前缀 `dtc-rNN:`（decompiler-test-comprehensive round NN）
4. **重复** 10 轮，目标是 100% 成功率与字节码完全匹配

### D. 算法 4 原则强制合规

- 自底向上归约：从最内层到最外层识别区域（归约顺序）
- 每块唯一归属：任意 CFG 块在任何层级仅属于一个区域
- 嵌套即抽象节点：嵌套区域在父区域中作为单个抽象节点表示
- 入口引用语义：归约后父区域 then/else 列表引用子区域入口，而非子区域所有块

### E. 反模式禁止

- 禁止跨区域跨层次的启发式规则
- 禁止破坏算法对嵌套的天然支持
- 禁止后处理补丁（必须识别阶段一次正确）
- 禁止硬编码深度上限
- 禁止 `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀方法名
- 禁止修改反编译生成的文件
- 禁止任何投机取巧（如针对特定 pyc 的硬编码绕过）
- 禁止跳过任何区域类型，所有 10 类区域必须同等完善

### F. 命令预算

- 所有命令执行 ≤ 300 秒
- 每轮 commit + push ≤ 300 秒
- 单轮回归测试 ≤ 280 秒
- 反编译单个 pyc ≤ 60 秒
- 字节码 diff ≤ 60 秒

### G. 成功率快速提升

测试应尽快使成功率增加。每轮修复后必须验证：
- 当前 pyc 的字节码一致函数数 ≥ 上一轮的函数数
- 成功率单调递增，禁止下降

### H. 每轮强制 commit + push

每轮必须 commit + push 到远程仓库，禁止只 commit 不 push：
- GitHub 远程仓库必须与本地同步
- 每轮结束前必须验证 push 成功
- push 失败则重试直到成功
- commit message 前缀 `dtc-rNN:`
- push 凭证：使用提供的 GitHub token

## Impact

- **Affected specs**：
  - `region-comprehensive-pyc-10rounds`（python_syntax_comprehensive_test.pyc 的迭代，本规范聚焦 decompiler_test_comprehensive.cpython-311.pyc）
  - `region-comment-multi-pyc-iteration`（多 pyc 迭代，继承其 4 原则与反模式禁令）
- **Affected code**：
  - `core/cfg/region_analyzer.py`（11 个 `_identify_*_regions` 方法注释 + 逻辑修正）
  - `core/cfg/region_ast_generator.py`（9+ 个 `_generate_*` 方法注释 + 逻辑修正）
  - `core/cfg/code_generator.py`（必要时）
  - `compare_bytecode_v2.py`（字节码比较工具）
- **Affected tests**：每轮新增 10+ 最小复现实例归档到 `rounds/round_NN/test_engineer/minimal_repros/`
- **Algorithm compliance**：持续 FULLY COMPLIANT（0 反模式新增，0 硬编码深度上限）

## ADDED Requirements

### Requirement: 区域识别方法 6 节注释模板

所有 `_identify_*_regions` 方法 SHALL 在 docstring 中包含以下 6 节结构，每节以 `##` 标题分隔：

1. **区域类型**：本方法识别的区域类型名称
2. **算法描述**：本区域识别所依据的「No More Gotos」章节 + 区域归约 4 原则对应条款 + 自底向上归约顺序中的位置
3. **字节码模式**：本区域对应的字节码指令模式
4. **边界条件**：区域入口 / 出口 / 包含块集合的判定条件，以及如何保证每块唯一归属
5. **归约语义**：嵌套子区域如何作为单个抽象节点表示；父区域 then/else 列表如何引用本区域入口
6. **AST 映射 + 已知失败模式**：从字节码模式到 AST 节点的完整映射步骤 + 已知失败场景与待完善点

#### Scenario: 注释模板合规
- **WHEN** 检查任意 `_identify_*_regions` 方法的 docstring
- **THEN** 6 节标题全部存在且内容非空
- **AND** 内容与本方法实际逻辑一致（禁止模板空壳）

### Requirement: 区域生成方法 4 节注释模板

所有 `_generate_*` 方法 SHALL 在 docstring 中包含以下 4 节结构：

1. **输入契约**：region 参数的预期类型 / 必填字段 / 前置不变量
2. **AST 映射规则**：region 字段 → AST 节点字段的完整映射
3. **子区域处理**：嵌套子区域如何递归生成；抽象节点如何展开
4. **字节码一致性约束**：生成的 AST 重编译后必须满足的字节码不变量

#### Scenario: 注释模板合规
- **WHEN** 检查任意 `_generate_*` 方法的 docstring
- **THEN** 4 节标题全部存在且内容非空

### Requirement: decompiler_test_comprehensive.cpython-311.pyc 字节码一致性验证

系统 SHALL 反编译 `decompiler_test_comprehensive.cpython-311.pyc`，对比反编译产物重编译后的字节码与原 pyc 字节码，输出：
- 不一致函数清单（函数名 / 指令偏移 / 差异类型）
- 当前成功率（一致函数数 / 总函数数）
- 与上一轮对比（成功率变化）

#### Scenario: 字节码验证成功
- **WHEN** 执行反编译 + 字节码 diff
- **THEN** 输出不一致函数清单与成功率
- **AND** 成功率 ≥ 上一轮

### Requirement: 持续双工程师迭代（10 轮）

系统 SHALL 执行 10 轮「测试工程师 + 修复工程师」迭代，每轮：
1. 测试工程师反编译 `decompiler_test_comprehensive.cpython-311.pyc`，输出字节码 diff 报告 + 10+ 最小复现实例
2. 修复工程师按区域归约算法修复，同步更新方法注释（6/4 节模板）
3. 运行回归测试（既有测试矩阵不退化）
4. commit + push（前缀 `dtc-rNN:`）

#### Scenario: 单轮闭环
- **WHEN** 第 NN 轮迭代完成
- **THEN** `rounds/round_NN/test_engineer/decompile_report.md` 已生成
- **AND** `rounds/round_NN/test_engineer/minimal_repros/` 含 ≥ 10 个可独立复现实例（若该 pyc 已 100% 一致则可豁免）
- **AND** `rounds/round_NN/repair_engineer/fix_report.md` 已生成
- **AND** 该轮 10+ 复现实例全部通过
- **AND** 既有测试矩阵无退化
- **AND** 已 commit + push `dtc-rNN:`

#### Scenario: 成功率单调递增
- **WHEN** 比较第 NN 轮与第 NN-1 轮的成功率
- **THEN** 第 NN 轮 ≥ 第 NN-1 轮（允许持平，禁止下降）

### Requirement: 算法 4 原则持续合规

每轮修复后 SHALL 保持算法 4 原则 FULLY COMPLIANT：
1. 自底向上归约：子区域先于父区域识别
2. 每块唯一归属：`block_to_region[block_id]` 每个块仅归属一个区域
3. 嵌套即抽象节点：子区域块不出现在父区域展开中
4. 入口引用语义：父区域仅引用子区域入口块

#### Scenario: 原则合规
- **WHEN** 检查任意一轮的代码变更
- **THEN** 无 `_fix_` / `_merge_` / `_patch_` 等禁止前缀
- **AND** 无 `depth > N` 硬编码
- **AND** 该轮测试矩阵通过数不下降

## MODIFIED Requirements

### Requirement: 区域归约算法实现（持续强化）

继承 `region-comment-multi-pyc-iteration` 的算法 4 原则，本规范过程中：
- 消除该区域剩余的特殊 case 处理
- 统一判据（基于结构模式而非指令模式）
- 强化子区域抽象节点不变量
- 完善方法 docstring（6 节 / 4 节模板）
- 所有修复必须符合区域归约算法，禁止跨区域启发式 / 后处理补丁

## REMOVED Requirements

无
