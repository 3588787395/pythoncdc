# 已判完备形态对抗评审与算法完善 10 轮 Spec

## Why

wiki 总纲 `wiki/concepts/decompile-invariant-completeness.md` 现行读数为「路径存在 128/128、完备 127、破口 1（BoolOp B1）」，但 127 个"完备"判定从未经过独立对抗验证——判据是锚点存在性 + 守卫族登记，缺少深层嵌套/交叉组合的攻击性复验；且当前工作树存在一段未评审、未过门禁的在途修复（`region_ast_generator.py` +419 行，标记 `[R76-A1/A2]`/`[R75 fix1]`）。

**本规范的主任务不是修复未完成 OK 的 pyc 文件**，而是：对台账已标榜"无感完备"的区域与语法形态进行对抗性评审与完善。评审工程师独立攻击，修复工程师做真正的算法修复，严格认定「算法驱动 / 嵌套无感 / 完备精简」，不得通容。未完全 OK 的 pyc 仅作为小测试集供子代理回归自测；全量验证由主代理执行。

## What Changes

- 建立本新规范：以 wiki 总纲为唯一理论权威，对抗对象 = §5 台账判定"完备"的 127 形态 + 12 个 `_identify_*` 识别方法族 + 已登记守卫族（B2/B3/B4）
- **修复工程师 × 评审工程师**对抗迭代 × 10 轮（round1–round10，各自独立文件夹）：
  - **评审工程师**（子代理）：每轮轮换抽取台账已判完备形态 ≥2 个，构造深层嵌套/交叉组合最小复现探针（每形态 ≥10 复现 + ≥2 MATCH 负对照）；并对当前树做算法合规审计——文件名/函数名白名单、start_offset 魔法阈值、跨层 `entry in blocks` 反查、新增 self 跨方法状态，发现即打回，零容忍
  - **修复工程师**（子代理）：只做区域归约算法内修复；反编译逻辑（识别条件→归约方式→AST 映射 + C1/C2/C3 条款声明）写入识别/生成方法注释；自测 = 本轮全部 MISMATCH 复现转 MATCH 且负对照保持 MATCH + 小测试集无回退
  - **主代理**：不执行修复/评审实现任务；只负责调度、本地提交、全量验证无回退、push 远程
- 破口登记 Bn 续接（B1a/B1b 之后为 B5+），走 wiki §8.3 状态机：未定位→已定位→已落地→已复审；封闭后按 §8.2 复审六步推进台账
- Round 1 特别范围：BoolOp 破口族（B1）+ If 形态（含在途未评审变更的对抗审计）

## Impact

- Affected specs: 无（本规范独立新建；历史规范归档保留，禁止回滚任何既有变更）
- Affected code: `core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`、`core/cfg/comprehension_generator.py`、`core/cfg/cfg_builder.py`
- Affected wiki: `decompile-invariant-completeness.md`（破口状态机推进、台账判定更新、占比重算）
- 验证判据唯一 = `F:\Downloads\pythoncdc-main\scripts\pyc_verify.py`（single/batch/compare，pylingual compare_pyc）
- 小测试集 = 34 个未完全 OK 的 pyc（`baseline/failing_index.json`），仅供子代理回归自测

## ADDED Requirements

### Requirement: 角色分工与主代理纪律

主代理 SHALL 只承担：调度子代理、阶段边界本地提交、全量验证（无回退判定）、归档提交与 push。修复与评审实现任务 SHALL 全部由子代理承担。两工程师对抗关系：评审工程师对树中一切代码（含在途未提交变更）独立攻击；修复工程师对评审结论不得协商通容，只能以更优算法修复回应或举证反驳。

#### Scenario: 一轮完整闭环
- **WHEN** Round N 启动
- **THEN** 顺序 = 主代理本地提交 → 建 `rounds/roundN/` → 评审工程师对抗攻击+合规审计（产出 REVIEW.md + 复现）→ 修复工程师算法修复+注释（产出 FIX.md）→ 评审工程师复核（通过/打回）→ 主代理全量验证无回退 → 归档 → 提交并 push origin main

### Requirement: 评审工程师对抗审查

评审工程师每轮 SHALL 执行两类审查，结论只有「通过 / 打回」两态，打回必须给出锚点（file:line）+ 违反条款编号 + 机制说明：

1. **完备形态攻击**：从台账 §5 已判"完备"形态中轮换抽取 ≥2 个，每个构造 ≥10 个最小复现（深层嵌套/交叉组合，深度 ≥3）+ ≥2 个 MATCH 负对照，实测「深层与浅层产物结构一致」；复现存 `test_repros/roundN/`，结果入 `rounds/roundN/REVIEW.md`
2. **算法合规审计**：对当前树（含在途未提交变更）逐守卫审查——出现函数名/文件名白名单、start_offset 魔法阈值、跨层读取（C1/C2 破坏）、新增 self 跨方法状态、以少发射换全绿，直接打回

#### Scenario: 对抗发现伪完备
- **WHEN** 台账判完备的形态在深层嵌套探针下与浅层产物结构不一致
- **THEN** 登记 Bn 破口（锚点+机制），修复工程师按封闭守卫恢复无感（禁止给个案打补丁）

### Requirement: 修复工程师算法修复

修复 SHALL 只在区域归约算法内进行：禁止跨区域/跨层次启发式、禁止文件名/函数名白名单、禁止 start_offset 魔法阈值、禁止新增 self 跨方法状态。判据只允许同层块对象的结构事实（块末指令 opcode、后继前驱集合、异常边、区域成员关系）。修复触及的方法 SHALL 同步维护 docstring 三要素（识别条件/归约方式/AST 映射）并注明 C1/C2/C3 条款；注释与代码不一致 = 评审不通过。修复后自测 = 本轮全部 MISMATCH 复现转 MATCH ∧ 负对照保持 MATCH ∧ 小测试集（34 pyc）无回退。

#### Scenario: 算法合规
- **WHEN** 修复方案依赖「目标函数名 == 'xxx'」类判据
- **THEN** 评审工程师直接打回，改用同层结构事实判据

### Requirement: 主代理无回退验证

主代理每轮 SHALL 亲自执行验证序（判据唯一 = `scripts/pyc_verify.py`，所有命令 ≤300s）：

1. 小测试集（`baseline/failing_index.json` 34 pyc）batch 验证：无 success→failure 位移
2. 全量 402 分片 batch（每片 ≤300s）+ `pyc_verify.py compare` 对基线：**REGRESSIONS=0**
3. `quotation.pyc` 单验通过（无新增失败）
4. 现有区域相关测试（tests/ 下）通过
5. 汇报读数：单元级成功率、文件级 success 数、本轮封闭破口数

#### Scenario: 回退拦截
- **WHEN** 批量回归出现任一 success→failure 位移或单元数下降
- **THEN** 本轮修复不得合入，打回修复工程师定位根因

### Requirement: 每轮门禁与推进纪律

- 每轮独立文件夹 `.trae/specs/harden-completed-forms-10rounds/rounds/roundN/`（REVIEW.md、FIX.md、验证读数归档于内；复现在 `test_repros/roundN/`）
- 调用子代理前必须先本地提交（含阶段边界：评审后、修复后各一次）
- 每轮必须产出 ≥1 个被登记并封闭的破口，或 ≥1 个 pyc 读数改善；两者皆无 = 本轮未过门禁，禁止开启下一轮
- 每轮结束必须提交并 push 到 origin main
- 所有命令 ≤300 秒，超时必须分片
- 禁止手改 `*OK.py`、禁止跳过验证、禁止虚报读数、禁止投机取巧

### Requirement: 台账推进与终态

- 每个确认破口按 wiki §8.3 状态机推进，封闭后按 §8.2 复审六步（grep 落地标记→台账更新→`tools/kb/syntax_coverage.py` 重跑→占比重算→log 记录）
- 终态目标：台账 127 形态全部经对抗验证仍成立，破口清零 = 完备占比 128/128；在途在树变更全部过审

## MODIFIED Requirements

无。

## REMOVED Requirements

无（历史规范与归档全部保留；对旧规范目录的删除为工作区既有状态，不在本规范内回滚）。
