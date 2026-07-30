# 区域注释驱动多 pyc 反编译迭代 Spec

## Why

`f:\Downloads\pythoncdc-main\site-packages` 下存在 130+ 个真实业务 pyc 文件（IQEngine/* 与 fly/data/quotation.pyc）。当前反编译器尚未达到字节码 100% 等价。根本性完善方案要求：以区域归约算法为核心，将反编译逻辑显式写入识别方法注释（6 节模板）/ 生成方法注释（4 节模板），通过「测试工程师 + 修复工程师」持续对抗性迭代（每轮取索引中一个 pyc 文件），驱动所有区域识别方法达到 100% 成功率与字节码完全匹配，最终使每个 pyc 文件都能反编译生成同名 `+OK` py 文件。

核心设计原则：
- **区域化分析**（Region-Based Analysis）：基于编译器理论中的区域分析算法，将 CFG 分解为层次化的区域
- **单向数据流**：分析结果从底层向上层传递，不回溯修正
- **一次正确**：每个结构在识别阶段就正确分类，不需要后处理修正
- **算法驱动**：用算法替代模式匹配，用数学性质替代启发式规则

算法基础：采用 "No More Gotos" (Launez et al., 2013) 论文中的结构化算法核心思想，结合 Python 字节码特性：
- 回边检测：基于支配树的标准回边检测算法
- 区域分类：将 CFG 节点集合分类为有限种区域类型
- 归约：将识别出的区域归约为单个节点，迭代直到整个 CFG 归约为一个节点
- AST 映射：每个区域类型对应唯一的 AST 节点类型

与既有规范的区别：
- `analysis-fix-iteration`：按区域类型 × 10 遍，架构工程师 + 修复工程师；本规范以注释驱动 + 多 pyc 闭环验证
- `quotation-pyc-iteration`：仅 quotation.pyc × 10 轮；本规范扩展到全部 pyc 文件 + 强制注释模板
- `iterate-region-test-fix`：单区域深度迭代；本规范覆盖全部 10 类区域 + 全部 pyc 文件

## What Changes

### A. 区域注释模板强制化

- **10 个 `_identify_*_regions` 方法** MUST 在 docstring 中包含 6 节模板：
  1. 区域类型（Region Type）
  2. 算法描述（Algorithm Description，含「No More Gotos」章节引用 + 区域归约 4 原则对应条款 + 自底向上归约顺序中的位置）
  3. 字节码模式（Bytecode Pattern）
  4. 边界条件（Boundary Conditions）
  5. 归约语义（Reduction Semantics，含归约顺序 / 唯一归属 / 嵌套抽象节点 / 入口引用语义）
  6. AST 映射 + 已知失败模式（AST Mapping & Known Failure Patterns）
- **9 个 `_generate_*` 方法** MUST 在 docstring 中包含 4 节模板：
  1. 输入契约（Input Contract）
  2. AST 映射规则（AST Mapping Rules）
  3. 子区域处理（Sub-region Handling）
  4. 字节码一致性约束（Bytecode Consistency Constraints）

### B. pyc 文件索引与逐个验证

- 扫描 `f:\Downloads\pythoncdc-main\site-packages\**\*.pyc`，生成 `pyc_index.json`（路径 / 大小 / 函数数 / 反编译状态 / 成功率）
- 每轮测试工程师从索引中取**下一个** pyc 文件（轮询，确保全部覆盖），反编译 + 字节码 diff
- 每个反编译成功的 pyc 文件 MUST 在同目录下生成 `<name>OK.py`（如 `quotation.pyc` → `quotationOK.py`）
- 累计成功率 = 所有已验证 pyc 的字节码一致函数总数 / 所有已验证 pyc 的函数总数

### C. 持续双工程师迭代（直到 100% 成功）

每轮（round_NN，NN=01,02,03,...）：
1. **测试工程师**（subagent）：从 pyc_index.json 取下一个 pyc 文件，反编译，验证字节码一致性，列出不一致函数清单 + 成功率，针对不一致点构造 10+ 最小复现实例
2. **修复工程师**（subagent）：依据测试报告，按区域归约算法完善 `_identify_*_regions` / `_generate_*` 方法，同步更新方法注释（6/4 节模板），运行回归测试
3. **commit + push**：commit message 前缀 `rcm-rNN:`（region-comment-multi-pyc round NN）
4. **重复**直到所有 pyc 文件所有函数 100% 字节码一致

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
- 禁止修改反编译生成的 `+OK.py` 文件
- 禁止任何投机取巧（如针对特定 pyc 的硬编码绕过）

### F. 命令预算

- 所有命令执行 ≤ 300 秒
- 每轮 commit + push ≤ 300 秒
- 单轮回归测试 ≤ 280 秒
- 反编译单个 pyc ≤ 60 秒
- 字节码 diff ≤ 60 秒

### G. 成功率快速提升

测试应尽快使成功率增加。每轮修复后必须验证：
- 当前 pyc 的字节码一致函数数 ≥ 上一轮该 pyc 的函数数
- 累计成功率（跨所有已验证 pyc）单调递增，禁止下降

## Impact

- **Affected specs**：
  - `analysis-fix-iteration`（区域 × 遍数迭代，本规范继承其 4 原则与反模式禁令）
  - `quotation-pyc-iteration`（quotation.pyc 单文件迭代，本规范扩展到全部 pyc）
  - `iterate-region-test-fix`（单区域深度迭代，本规范覆盖全部区域）
- **Affected code**：
  - `core/cfg/region_analyzer.py`（11 个 `_identify_*_regions` 方法注释 + 逻辑修正）
  - `core/cfg/region_ast_generator.py`（9+ 个 `_generate_*` 方法注释 + 逻辑修正）
  - `core/cfg/cfg_builder.py` / `ast_converter.py` / `pattern_parser.py` / `code_generator.py`（必要时）
  - 新增 `scripts/pyc_index_builder.py`（pyc 索引构建）
  - 新增 `scripts/pyc_batch_verify.py`（批量反编译 + 字节码 diff + +OK 生成）
- **Affected tests**：每轮新增 10+ 最小复现实例归档到 `rounds/round_NN/test_engineer/minimal_repros/`
- **Algorithm compliance**：持续 FULLY COMPLIANT（0 反模式新增，0 硬编码深度上限）
- **Risk**：持续迭代可能引入回归；多 pyc 验证可能暴露既有未发现缺陷

## ADDED Requirements

### Requirement: 区域识别方法 6 节注释模板

所有 `_identify_*_regions` 方法 SHALL 在 docstring 中包含以下 6 节结构，每节以 `##` 标题分隔：

1. **区域类型**：本方法识别的区域类型名称（IF / LOOP / TRY / WITH / MATCH / ASSERT / BOOLOP / TERNARY / CHAINED_COMPARE / SEQUENCE）
2. **算法描述**：本区域识别所依据的「No More Gotos」（Launez et al., 2013）章节 + 区域归约 4 原则对应条款 + 自底向上归约顺序中的位置
3. **字节码模式**：本区域对应的字节码指令模式（含跳转方向 / 回边 / 异常表 / 上下文管理器等）
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

### Requirement: pyc 文件索引构建

系统 SHALL 扫描 `f:\Downloads\pythoncdc-main\site-packages\**\*.pyc`，生成 `pyc_index.json`，每个条目包含：
- `path`：pyc 文件绝对路径
- `size`：文件大小（字节）
- `function_count`：code object 数量
- `decompile_status`：`pending` / `partial` / `ok` / `failed`
- `bytecode_match_rate`：字节码一致函数比例（0.0-1.0）
- `ok_py_generated`：是否已生成 `<name>OK.py`
- `last_tested_round`：最近验证轮次（初始 0）

#### Scenario: 索引构建成功
- **WHEN** 执行 `python scripts/pyc_index_builder.py`
- **THEN** 生成 `pyc_index.json`，覆盖 site-packages 下全部 pyc 文件
- **AND** 每个条目字段完整

### Requirement: 持续双工程师迭代（轮询 pyc）

系统 SHALL 持续执行「测试工程师 + 修复工程师」迭代，每轮：
1. 测试工程师从 pyc_index.json 取下一个 `decompile_status != ok` 的 pyc 文件（轮询顺序：按 path 字母序）
2. 反编译该 pyc，输出字节码 diff 报告 + 10+ 最小复现实例
3. 修复工程师按区域归约算法修复，同步更新方法注释（6/4 节模板）
4. 运行回归测试（既有测试矩阵不退化）
5. 在该 pyc 同目录生成 `<name>OK.py`（若反编译成功）
6. 更新 pyc_index.json（decompile_status / bytecode_match_rate / ok_py_generated / last_tested_round）
7. commit + push（前缀 `rcm-rNN:`）

#### Scenario: 单轮闭环
- **WHEN** 第 NN 轮迭代完成
- **THEN** `rounds/round_NN/test_engineer/decompile_report.md` 已生成
- **AND** `rounds/round_NN/test_engineer/minimal_repros/` 含 ≥ 10 个可独立复现实例（若该 pyc 已 100% 一致则可豁免）
- **AND** `rounds/round_NN/repair_engineer/fix_report.md` 已生成
- **AND** 该轮 10+ 复现实例全部通过
- **AND** 既有测试矩阵无退化
- **AND** 已 commit + push `rcm-rNN:`

#### Scenario: 成功率单调递增
- **WHEN** 比较第 NN 轮与第 NN-1 轮的累计字节码一致函数数
- **THEN** 第 NN 轮 ≥ 第 NN-1 轮（允许持平，禁止下降）

### Requirement: +OK py 文件生成

每个 pyc 文件 MUST 在同目录下生成同名 `+OK.py` 文件（如 `quotation.pyc` → `quotationOK.py`），且该文件：
- 可被 `py_compile` 成功编译
- 编译后字节码与原 pyc 字节码 100% 一致
- 禁止修改生成后的 `+OK.py` 文件（如需修复，必须修复反编译器本身）

#### Scenario: 单个 pyc 反编译成功
- **WHEN** 执行 `python pycdc.py <path>\foo.pyc`
- **THEN** 同目录下生成 `fooOK.py`
- **AND** `python -m py_compile fooOK.py` 成功
- **AND** 重编译字节码与 foo.pyc 逐条指令匹配

#### Scenario: 全部 pyc 反编译成功
- **WHEN** 迭代退出条件满足
- **THEN** `pyc_index.json` 中所有条目 `decompile_status = ok`
- **AND** 所有 `+OK.py` 文件已生成
- **AND** 所有 `+OK.py` 字节码与原 pyc 100% 一致

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

继承 `analysis-fix-iteration` 与 `quotation-pyc-iteration` 的算法 4 原则，本规范过程中：
- 消除该区域剩余的特殊 case 处理
- 统一判据（基于结构模式而非指令模式）
- 强化子区域抽象节点不变量
- 完善方法 docstring（6 节 / 4 节模板）
- 所有修复必须符合区域归约算法，禁止跨区域启发式 / 后处理补丁

## REMOVED Requirements

### Requirement: 仅 quotation.pyc 单文件验证
**Reason**：用户要求扩展到 site-packages 下全部 pyc 文件，轮询取下一个，且每个生成 +OK.py
**Migration**：测试工程师每轮从 pyc_index.json 取下一个 `decompile_status != ok` 的 pyc 文件（轮询顺序按 path 字母序）

### Requirement: 固定 10 轮迭代上限
**Reason**：用户要求「循环迭代直到所有函数 100% 成功」，不设固定轮数上限
**Migration**：持续迭代直到退出条件满足（所有 pyc 所有函数 100% 一致）

### Requirement: 跨区域启发式与后处理补丁
**Reason**：违反区域归约算法 4 原则，导致算法通用性下降
**Migration**：通过完善识别逻辑本身（扩充入口条件 / 补充嵌套判定）替代补丁；已有补丁逐轮消除

## 双工程师工作流

### 测试工程师职责（每轮）
1. 从 `pyc_index.json` 取下一个 `decompile_status != ok` 的 pyc 文件（轮询顺序按 path 字母序）
2. 反编译该 pyc（≤ 60s）
3. 对比反编译产物与原 pyc 字节码，输出 `decompile_report.md`：
   - 不一致函数清单（函数名 / 指令偏移 / 差异类型）
   - 当前 pyc 成功率（一致函数数 / 总函数数）
   - 累计成功率（跨所有已验证 pyc）
   - 与上一轮对比（成功率变化）
4. 针对每处不一致，构造最小复现实例（最小 .py 源码 → 编译 → 反编译 → 字节码 diff）
5. 归档 ≥ 10 个最小复现实例至 `rounds/round_NN/test_engineer/minimal_repros/repro_NN_*.py`
6. 若该 pyc 100% 一致：在同目录生成 `<name>OK.py`，更新 pyc_index.json

### 修复工程师职责（每轮）
1. 阅读测试工程师的 `decompile_report.md` 与 `minimal_repros/`
2. 对每个不一致，定位到 `_identify_*_regions` 或 `_generate_*` 方法
3. 按「No More Gotos」+ 区域归约算法完善逻辑（不得引入补丁）
4. 同步更新方法 docstring（6 节 / 4 节模板）
5. 运行回归测试（既有测试矩阵不退化，≤ 280s）
6. 验证该轮 10+ 复现实例全部通过
7. 输出 `fix_report.md`：修复点 + 算法依据 + 注释更新清单 + 回归结果 + 残留不一致数
8. 若该 pyc 修复后 100% 一致：生成 `<name>OK.py`，更新 pyc_index.json
9. commit + push（前缀 `rcm-rNN:`，≤ 300s）

### 退出条件
- `pyc_index.json` 中所有条目 `decompile_status = ok`
- 所有 pyc 文件 `+OK.py` 已生成且字节码 100% 一致
- 最近 1 轮测试工程师无可新增最小复现实例（< 10 个，因所有 pyc 已 100% 一致）

## 区域顺序提示

各 pyc 文件可能涉及的区域类型（非强制顺序，由测试工程师按不一致热点选取）：
IF / LOOP / TRY / WITH / MATCH / ASSERT / BOOLOP / TERNARY / CHAINED_COMPARE / SEQUENCE

所有 10 类区域必须同等完善，禁止厚此薄彼。

## pyc 轮询策略

- 测试工程师按 pyc_index.json 中 path 字母序轮询
- 每轮取下一个 `decompile_status != ok` 的 pyc 文件
- 若所有 pyc 已 `ok`，则重新轮询验证（回归检查）
- 累计成功率 = Σ(各 pyc 一致函数数) / Σ(各 pyc 总函数数)
