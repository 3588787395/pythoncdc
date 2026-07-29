# 区域归约算法驱动的 quotation.pyc 反编译 10 轮迭代 V2 Spec

## Why

V1 10 轮迭代已完成，一致函数数从 141/150 (94.00%) 提升至 143/150 (95.33%)，但仍残留 7 个不一致函数，未达 100% 字节码一致目标。其中 3 个为真正的算法缺陷（Loop 区域语句丢失），3 个为跳转目标归一化差异（语义等价），1 个为元数据差异（非算法缺陷）。

本次目标：以区域归约算法（No More Gotos）继续驱动 10 轮双工程师迭代（R11-R20），重点攻克 3 个 Loop 区域缺陷 + 3 个跳转目标归一化 + 1 个元数据差异，最终达到 100% 字节码一致。

## What Changes

- 继承 V1 的双工程师迭代流程（测试工程师 → 修复工程师 → 回归 → commit + push）
- 重点分析 Loop 区域（`_identify_loop_regions` / `_generate_loop`）在嵌套 for/while 循环体语句丢失的根因
- 解决跳转目标归一化差异：在 `exact_match_stats.py` 进一步归一化语义等价的跳转目标，或在 `code_generator.py` 对齐跳转目标布局
- 解决 `<module>` 嵌套 code 对象 co_filename 元数据差异
- 每轮独立目录 `rounds/round_NN/{test_engineer,repair_engineer}/`（NN=11..20），每轮 commit + push（commit 前缀 `rr-rNN:`）
- 持续 10 轮，每轮后统计一致函数数 / 成功率，要求成功率单调递增，直至 100% 字节码完全匹配
- **禁止修改反编译生成的产物文件**（`quotation_decompiled.py`、`/tmp/r*_decompiled.py` 等只读）
- **所有命令执行不得超过 300 秒**

## Impact

- Affected specs:
  - `region-reduction-quotation-10rounds`（V1，沿用其 baseline、测试基础设施、`final_residual.md` 残留清单）
  - `quotation-pyc-iteration`（沿用 baseline 与测试基础设施）
  - `analysis-fix-iteration`（区域测试矩阵作为回归基线）
- Affected code:
  - `core/cfg/region_analyzer.py` — `_identify_loop_regions` / `_identify_conditional_regions` 识别逻辑
  - `core/cfg/region_ast_generator.py` — `_generate_loop` / `_if_generate_then_branch` / `_if_generate_normal` 生成逻辑
  - `core/cfg/code_generator.py` — 跳转目标布局对齐 / 表达式优先级
  - `core/cfg/cfg_builder.py` — CFG 构建 / 跳转目标识别
  - `.trae/specs/region-reduction-quotation-10rounds/rounds/round_NN/test_engineer/exact_match_stats.py` — 跳转目标归一化增强
- 受约束的核心算法原则（贯穿所有方法，继承 V1）：
  1. **自底向上归约**：从最内层到最外层识别区域，归约后才在父区域出现
  2. **每块唯一归属**：每个块在任何层级只属于一个区域（`block_to_region` canonical owner）
  3. **嵌套即抽象节点**：嵌套区域在其父区域中作为单个抽象节点表示
  4. **入口引用语义**：归约后父区域的 then/else 列表引用子区域的 entry，而不是子区域的所有块

## 残留不一致函数清单（V1 输出，V2 输入）

### Loop 区域语句丢失（3 个，真算法缺陷，优先级 P0）

| 函数 | 状态 | 根因 |
|------|------|------|
| `load_get_price` | len_diff -2 | Conditional+BoolOp 嵌套分支残留 2 指令（R10 部分修复 -26→-2）|
| `get_str_data` | len_diff -48 | Loop 嵌套 for/while 循环体语句丢失 |
| `get_date_and_count` | len_diff -27 | Loop+Conditional while 循环 if/elif 链语句丢失 |

### 跳转目标归一化差异（3 个，语义等价，优先级 P1）

| 函数 | 状态 | 根因 |
|------|------|------|
| `one_prod_to_dataframe` | instr_diff@131 | 首个 `i==0` 提取为外层 if，原始跳到下一 elif，跳转目标偏移 |
| `build_future_fill_time` | instr_diff@226 | listcomp 内部 code 对象布局 + 后续跳转目标偏移 |
| `change_his_to_backward` | instr_diff@296 | for 循环内嵌套 if 的 else 体已恢复，残留跳转目标偏移 |

### 元数据差异（1 个，非算法缺陷，优先级 P2）

| 函数 | 状态 | 根因 |
|------|------|------|
| `<module>` | instr_diff@394 | 嵌套 code 对象的 co_filename 在原始为 `./fly_docker_py311/fly/data/quotation.py`，反编译产物为 `<decompiled>` |

## ADDED Requirements

### Requirement: Loop 区域缺陷修复（P0）

系统 SHALL 修复 3 个 Loop 区域语句丢失缺陷。

#### Scenario: load_get_price 完全一致
- **WHEN** R11-R20 任一轮修复完成
- **THEN** `load_get_price` 字节码 diff = 0（一致）
- **AND** 修复依据区域归约算法 4 原则，禁止跨层启发式规则

#### Scenario: get_str_data 完全一致
- **WHEN** R11-R20 任一轮修复完成
- **THEN** `get_str_data` 字节码 diff = 0（一致）
- **AND** 重点分析 `_generate_loop` 嵌套 for/while 循环体块遍历是否漏掉 merge/follow 块

#### Scenario: get_date_and_count 完全一致
- **WHEN** R11-R20 任一轮修复完成
- **THEN** `get_date_and_count` 字节码 diff = 0（一致）
- **AND** 重点分析 Loop+Conditional while 循环 if/elif 链的完整生成

### Requirement: 跳转目标归一化（P1）

系统 SHALL 通过以下任一方式消除 3 个跳转目标归一化差异：
1. 在 `exact_match_stats.py` 进一步归一化语义等价的跳转目标
2. 在 `code_generator.py` 对齐跳转目标布局

#### Scenario: 跳转目标语义等价归一化
- **WHEN** exact_match_stats.py 检测到跳转目标差异
- **THEN** 若跳转目标指向语义等价的指令（如同一 elif 链的下一分支入口），SHOULD 视为一致
- **AND** 归一化规则需文档化到 `exact_match_stats.py` 注释

### Requirement: 元数据差异修复（P2）

系统 SHALL 修复 `<module>` 嵌套 code 对象 co_filename 差异。

#### Scenario: co_filename 对齐
- **WHEN** 反编译产物生成 `<module>` 顶层 code 对象
- **THEN** 嵌套 code 对象的 co_filename SHALL 设置为原始 pyc 文件中的对应文件名
- **OR** exact_match_stats.py 在比较 code 对象时归一化 co_filename

### Requirement: 双工程师迭代流程（继承 V1）

系统 SHALL 每轮由两位工程师协作完成：

#### Scenario: 测试工程师职责
- **WHEN** 进入轮 N（N=11..20）
- **THEN** 测试工程师反编译 `/workspace/quotation.pyc`
- **AND** 与原始字节码做精确 diff，统计一致函数数 / 总函数数 / 成功率
- **AND** 从不一致函数中提取 ≥10 个最小复现实例到 `rounds/round_NN/test_engineer/minimal_repros/`（若残留 < 10 个不一致函数，记录为已达成退出条件 E2）
- **AND** 输出 `decompile_report.md`（含一致函数数、成功率、缺陷分类、repro 清单）

#### Scenario: 修复工程师职责
- **WHEN** 测试工程师完成 decompile_report.md
- **THEN** 修复工程师依据 repro 与 `decompile_report.md`
- **AND** 定位根因到 `_identify_*_regions` 或 `_generate_*` 方法
- **AND** 按区域归约算法 4 原则修复，禁止跨区域跨层次启发式规则
- **AND** 同步更新相关方法 docstring（6 节模板）
- **AND** 输出 `fix_report.md`（含修复点、算法依据、4 原则对应条款、回归结果、残留不一致数）

### Requirement: 成功率单调递增（继承 V1）

系统 SHALL 保证每轮反编译一致函数数不退化。

#### Scenario: 成功率提升
- **WHEN** 轮 N 修复完成并回归后
- **THEN** 轮 N 的 quotation.pyc 一致函数数 ≥ 轮 N-1 的一致函数数
- **AND** 若某轮出现退化，修复工程师必须先回退退化再推进新修复

### Requirement: 每轮 commit + push（继承 V1）

系统 SHALL 每轮独立 commit 并 push 到远程。

#### Scenario: 提交并推送
- **WHEN** 轮 N 的 fix_report.md 与回归测试完成
- **THEN** 使用 commit 前缀 `rr-rNN:` 提交（NN 为 11..20）
- **AND** push 到 `origin/main`（远程 `https://github.com/3588787395/pythoncdc`）
- **AND** 使用提供的 GitHub token 完成鉴权
- **AND** 单次命令执行 ≤ 300 秒

### Requirement: 反模式零新增（继承 V1）

系统 SHALL 禁止在修复中引入反模式。

#### Scenario: 反模式自检
- **WHEN** 修复工程师提交代码
- **THEN** `core/cfg/` 下无新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法
- **AND** 无新增硬编码深度上限
- **AND** 禁止跨区域跨层次启发式规则（违反 4 原则）

## MODIFIED Requirements

### Requirement: 区域归约算法合规性（继承 V1）

修复工程师所有改动 MUST 符合区域归约算法 4 原则：

1. **自底向上归约**：`_build_region_hierarchy` 在所有区域识别完成后统一构建层级，识别阶段不跨层引用
2. **每块唯一归属**：`block_to_region` 为 canonical owner，`_ni_is_peer` 守卫不把共享 entry 的子区域误判为祖先
3. **嵌套即抽象节点**：嵌套区域（如 TryExcept 在 IfRegion else 分支）作为单个抽象节点
4. **入口引用语义**：父区域 then/else 列表引用子区域 entry，不展开子区域所有块

**禁止**：
- 跨区域跨层次的启发式规则
- 破坏算法对嵌套的天然支持
- 用模式匹配替代算法
- 后处理修正（一次正确原则）

## REMOVED Requirements

无移除项。沿用 V1 (`region-reduction-quotation-10rounds`) 的 baseline、测试基础设施、`final_residual.md` 残留清单，以及已补全的 11 类 `_identify_*_regions` 识别方法 docstring（6 节模板，11/11）。
