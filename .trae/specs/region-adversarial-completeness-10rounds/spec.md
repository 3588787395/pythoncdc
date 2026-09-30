# 区域对抗完善：嵌套无感与语法完备 10 轮迭代 Spec

## Why

wiki 总纲 `wiki/concepts/decompile-invariant-completeness.md` 已确立「嵌套无感 × 语法完备」唯一权威理论：128 形态中路径存在 100%、完备 127、破口 1（BoolOp B1a 已验证未落地 + B1b 未定位）、sstrict 残留缺陷单元、8 个官方 partial pyc（最差 `fly/data/quote.pyc` 88.89%）、严格尺 34 失败文件 / 71 失败单元。理论读数与工程落地之间存在缺口，且历轮修复缺少独立对抗评审。需要以「修复工程师 × 评审工程师」对抗迭代将理论落地为 **402/402 pyc 全部 success（字节码逐单元完全一致）**。

## What Changes

- 建立本新规范文档：以 wiki 总纲为唯一理论权威，目标「嵌套无感 + 语法完备」双达标
- **BREAKING**：验证判据唯一化为 `F:\Downloads\pythoncdc-main\scripts\pyc_verify.py`（pylingual compare_pyc；废弃 `pyc_batch_verify.py` 作为判据）；唯一通过标准 = 单元全 Equal（success）
- 三工程师对抗工作流 × 10 轮（round76–round85）：
  - **测试工程师**（子代理）：每轮取 1 个 pyc → 验证字节码一致性 → ≥10 最小复现 + 负对照 → 根因归类（区域类型 × C1/C2/C3 条款）
  - **修复工程师**（子代理）：按区域归约算法完成真正的算法修复，将反编译逻辑（识别条件→归约方式→AST 映射 + 不变式声明）写入识别方法注释
  - **评审工程师**（子代理）：独立对抗审核，对不符合「算法驱动 / 嵌套无感 / 完备精简」者严格认定、打回重修，不得通容；**优先对台账已判完备的 127 形态进行对抗完善**
- B1a 落地（落地标记 `_graft_pending_operand` grep 命中）+ B1b 定位封闭 → 台账 B1 升完备、占比重算
- 全部 402 pyc 达 success，同目录 `*OK.py` 全部由程序生成
- 每轮独立文件夹归档；调用子代理前必须本地提交；每轮结束提交并 push 远程（origin main）
- 全程所有命令执行 ≤300 秒（批量验证按分片索引执行）

## Impact

- Affected specs: `region-reduction-30pyc-perfect-10rounds`（rounds 1–75 历史，归档保留不回滚）、`define-cfg-completeness-standard`（理论前身）
- Affected code: `core/cfg/region_analyzer.py`（12 个 `_identify_*` 识别方法）、`core/cfg/region_ast_generator.py`、`core/cfg/comprehension_generator.py`、`core/cfg/cfg_builder.py` 等核心管线
- Affected wiki: `decompile-invariant-completeness.md` 台账（破口状态机推进、占比重算、log 记录，按 §8 复审六步）
- 产物: `site-packages/**` 402 个 `*OK.py`（只允许程序生成，禁止手改）

## ADDED Requirements

### Requirement: 对抗迭代工作流（四角色分工）

每轮 SHALL 按固定角色分工执行：主代理只负责调度、门禁验证与无回退确认，**不执行修复/测试/评审的实现任务**；测试/修复/评审三个实现角色一律由子代理承担。角色对抗关系：评审工程师对修复工程师的产出独立对抗验证，双方不得协商通容。

#### Scenario: 一轮完整闭环
- **WHEN** Round N 启动
- **THEN** 顺序为：主代理本地提交 → 建 `rounds/roundN/` 文件夹 → 测试工程师产出复现与根因 → 修复工程师算法修复+注释 → 评审工程师对抗审查通过 → 主代理验证（靶 pyc 100% → quotation.pyc → 批量回归无回退）→ 归档 → 提交并 push

### Requirement: 嵌套无感对抗完善

评审工程师每轮 SHALL 执行两类对抗审查：

1. **本轮触及路径**：修复涉及的识别/归约/生成路径逐条检验 C1（局部消费：只读 `L(A) = A.blocks ∪ A.out_edges ∪ A.exception_table`）、C2（黑箱组合：子区域只经 entry/exit 被父级消费）、C3（守卫封闭：非局部信息读取必须有显式守卫）
2. **台账已判完备形态**：每轮从 127 个完备形态中轮换抽取 ≥2 个，构造深层嵌套/交叉组合探针，验证「深层与浅层行为一致」；发现违反即登记新破口（编号 Bn 续接，走 wiki §8 破口状态机）

评审结论只有「通过 / 打回」两态；打回必须给出锚点（file:line）与违反条款编号。**不得通容**。

#### Scenario: 对抗发现伪完备
- **WHEN** 台账判完备的 If 形态在 32 层嵌套探针下与浅层产物结构不一致
- **THEN** 登记 Bn 破口，该轮修复被打回，修复工程师按封闭守卫恢复无感（禁止给语料个案打补丁）

### Requirement: 识别方法注释（区域反编译逻辑）

每个区域识别方法（`_identify_*` 族 12 个及生成器对应方法）SHALL 在 docstring 中维护三要素反编译逻辑：

1. **识别条件**：仅依赖 L(A) 内 CFG 结构事实（回边/支配关系/异常表/操作码模式），标注对应区域类型
2. **归约方式**：块归属集合的计算、守卫条件（何时排除/认领）、子区域入口引用语义
3. **AST 映射**：区域类型 → AST 节点构造点（file:line 或方法名）

修复触及的方法 SHALL 同步更新注释；新增守卫 SHALL 注明对应的 C1/C2/C3 条款。注释与代码不一致视为评审不通过。

#### Scenario: 修复后注释同步
- **WHEN** 修复工程师在某识别方法新增共享尾守卫
- **THEN** 该方法 docstring 的「归约方式」同步登记守卫判据与 C3 条款引用，评审工程师核对一致才放行

### Requirement: 测试工程师工作流（单 pyc → 最小复现）

每轮 SHALL 取恰好 1 个 pyc（选靶优先级：已知破口关联文件 > 字节码一致率最低者）：

1. `python scripts/pyc_verify.py single <target.pyc>` 验证（≤300s），记录单元级/文件级成功率
2. 对每个失败单元做 dis 对照，根因定位到「区域类型 × 不变式条款」
3. 产出 ≥10 个最小复现（≥10 MISMATCH + ≥2 MATCH 负对照），存 `test_repros/round<N>/`
4. 产出 `ANALYSIS.md`（根因分类 RN-A…，含锚点）
5. 以「现有规范中未完全 OK 的 pyc 清单」为小测试集验证（子代理口径）；主代理另行全量验证

#### Scenario: 复现质量门
- **WHEN** 复现不足 10 个或负对照缺失
- **THEN** 本轮不得进入修复阶段，测试工程师补齐

### Requirement: 修复工程师工作流（算法驱动）

修复 SHALL 只允许区域归约算法内修复：禁止跨区域/跨层次启发式规则、禁止文件名/函数名白名单、禁止 start_offset 魔法阈值、禁止以少发射换全绿、禁止新增 self 跨方法状态。修复后自测：本轮全部 MISMATCH 复现转 MATCH 且负对照保持 MATCH。

#### Scenario: 算法合规
- **WHEN** 修复方案依赖「目标函数名 == 'xxx'」类判据
- **THEN** 评审工程师直接打回（违反算法驱动），改用同层块对象的结构事实判据

### Requirement: 主代理无回退验证

主代理每轮 SHALL 亲自执行验证序（判据唯一 = `scripts/pyc_verify.py`）：

1. 靶 pyc 达 success（`*OK.py` 由程序生成于同目录，禁止手改）
2. `quotation.pyc` 验证通过（无新增失败）
3. 批量回归：402 全量分片执行（每片 ≤300s），`pyc_verify.py compare` Movement Matrix **REGRESSIONS=0**
4. 运行现有区域相关测试套件（tests/ 下相关测试）确认通过
5. 汇报成功率读数（反编译前后字节码一致函数数、单元级成功率、文件级 success 数），成功率须逐轮尽快增加

#### Scenario: 回退拦截
- **WHEN** 批量回归出现任一 success → failure 位移
- **THEN** 本轮修复不得合入，打回修复工程师定位回退根因

### Requirement: 每轮门禁与推进纪律

- 每轮使用独立文件夹 `.trae/specs/region-adversarial-completeness-10rounds/rounds/round<N>/`（分析、修复说明、评审意见、验证读数归档于内）
- 调用子代理前必须先提交到本地（保证子代理改动可归因）
- **每轮至少解决 1 个 pyc（达到 success），未解决禁止进入下一轮**
- 每轮结束必须提交并 push 到远程（origin main）
- 所有命令执行不得超过 300 秒；超时命令必须分片或拆分
- 逐步进行，禁止任何投机取巧（禁手改 `*OK.py`、禁跳过验证、禁虚报读数）

#### Scenario: 轮门禁未过
- **WHEN** Round N 结束时无任何 pyc 新达 success
- **THEN** 禁止开启 Round N+1；本轮必须继续迭代（可另开同轮批次）直到至少 1 个 pyc 达标

### Requirement: 语法完备落地（B1 封闭与台账复审）

- B1a：按归档方案（`.trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round75/batches/fix1/specs/jqop1.json`）落地嫁接，落地标记 `_graft_pending_operand` + `_contains_identity` 在当前树 grep 命中
- B1b：定位语句上下文 or 臂第二丢弃入口（复现 `synth/neg75_jqcond2.py/.pyc`）并封闭
- 封闭后按 wiki §8.2 复审六步执行：grep 落地标记 → 台账更新 → `tools/kb/syntax_coverage.py` 重跑 → 占比重算 → wiki log 记录
- 目标终态：128/128 完备、破口清零

#### Scenario: B1 复审升完备
- **WHEN** B1a/B1b 双入口接回且 neg75_jqcond2 3/3 success 且 jq_trans_module 保持 65/65
- **THEN** 台账 BoolOp 判定升「完备」，完备占比重算为 128/128

### Requirement: 全量收敛（402/402）

全部 402 pyc SHALL 达 `pyc_verify.py` 判 success（单元全 Equal），每个在同目录生成同名 `*OK.py`。10 轮为最小迭代数；若 round85 结束仍未全量收敛，按同一规范续轮（round86+）直到 402/402。

#### Scenario: 终态验收
- **WHEN** 最后一轮批量验证
- **THEN** `pyc_verify.py batch --index pyc_index.json` 全量报告 files_by_status.success == 402、其余桶全 0

## MODIFIED Requirements

### Requirement: 验证判据（承接 region-reduction-30pyc-perfect-10rounds）

验证脚本由 `scripts/pyc_batch_verify.py` 改为 `F:\Downloads\pythoncdc-main\scripts\pyc_verify.py`（唯一判据；batch/single/compare 三模式）。历史 rounds 归档不动，后续所有验证读数一律出自新脚本。

## REMOVED Requirements

无移除需求（历史规范与归档全部保留，禁止回滚用户已有变更）。
