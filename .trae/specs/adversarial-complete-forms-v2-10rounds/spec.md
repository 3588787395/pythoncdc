# 对抗完备形态 v2：嵌套无感与语法完备终局 10 轮 Spec

## Why

前序规范 `harden-completed-forms-10rounds` 已完成 9 轮（402 全量 6554/6617 = 99.05%、文件 369/402、quotation 152/153、小测试集 34 = 1505/1568，全部零回退），但存在三项未竟：① wiki 总纲 §5 台账 127 个"完备"判定的对抗覆盖仍是逐轮抽样，未做全台账终局复验；② 残余破口 B42×3/B43/B44/B46–B51/B56–B65/B69/B70 未清零，旧规范 Round 10 终审未执行；③ `_identify_*` 十族识别方法的注释三要素（识别条件/归约方式/AST 映射 + C1/C2/C3 条款）与代码行为一致性未经逐方法独立审计。

**本规范主任务不是修复未完成 OK 的 pyc 文件**，而是对文档标榜"无感完备"的区域与语法形态进行对抗性评审与完善：评审工程师独立攻击，修复工程师（可多位协同）做真正的算法修复；凡不符合「算法驱动 / 嵌套无感 / 完备精简」的，严格认定、对抗进行、不得通容。未完全 OK 的 pyc 仅作为小测试集供子代理回归自测；全量验证由主代理执行。

## What Changes

- 新建本规范承接旧规范 Round 10 未竟终审（本规范 Round 1 = 承接轮），历史归档全部保留、禁止回滚
- 优化迭代流程（相对旧规范的四点变化）：
  - **修复工程师多位协同**：单轮评审登记 ≥2 个互不相交破口族（破口族不相交 ∧ 涉改文件不相交）时并行派发，合并后统一验证
  - **站桩回归常设化**：每轮强制重放已封闭破口登记探针面（round6 115/115、round7 r7 面、round8 r8 面、round9 50/50 及本规范已完结各轮），读数不得变差，不再单设回归轮
  - **注释三要素入对抗面**：识别/生成方法 docstring（识别条件/归约方式/AST 映射）与代码行为不一致 = 打回项，设专轮全量审计
  - **主代理零实现**：主代理只做调度、阶段边界提交、全量验证、归档 push
- 对抗优先级：台账 §5 判"完备"形态（表A 语句结构 / 表B 表达式 / 表C 31 扩展形态）→ 已封闭守卫族（B2/B3/B4）深度外推 → 残余破口族（B42+）
- 破口登记 Bn 续接（当前累计 B1a–B70，新登记自 B71 起），走 wiki §8.3 状态机（未定位→已定位→已落地→已复审）；每轮封闭的破口随轮推进台账，Round 10 终审统一执行 wiki §8.2 复审六步全量（grep 落地标记→台账更新→syntax_coverage 重跑→占比重算→log 记录）

## Impact

- Affected specs: `harden-completed-forms-10rounds`（其 Round 10 未竟项由本规范 Round 1 承接、终审定稿由本规范 Round 10 完成；归档保留，禁止回滚）
- Affected code: `core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`、`core/cfg/comprehension_generator.py`、`core/cfg/code_generator.py`、`core/cfg/exception_handler.py`、`core/cfg/pattern_parser.py`
- Affected wiki: `wiki/concepts/decompile-invariant-completeness.md`（台账判定、破口登记、占比重算、§8.2 六步、log）
- 验证判据唯一 = `F:\Downloads\pythoncdc-main\scripts\pyc_verify.py`（single / batch --index --json / compare --before --after）
- 小测试集 = 34 个未完全 OK 的 pyc（`harden-completed-forms-10rounds/baseline/failing_index.json`），仅供子代理回归自测；全量验证（402）由主代理执行
- 承接基线读数（round9 终态 7453e670）：402 全量 6554/6617（99.05%）文件 369/402；小测试集 34 = 1505/1568；quotation 152/153；tests 六套件 277 passed / 2 failed（基线名单 test_B01 + test_BOUNDARY_02）/ 2 xpassed

## ADDED Requirements

### Requirement: 三方角色与主代理纪律

主代理 SHALL 只承担：调度子代理、阶段边界本地提交、全量验证（无回退判定）、归档提交与 push；禁止执行任何修复/评审实现任务，子代理故障时重试派发或如实上报，不得代笔。修复工程师 SHALL 只做区域归约算法内修复，可多位协同：并行派发判据 = 破口族不相交 ∧ 涉改文件不相交，合并后统一过验证序。评审工程师 SHALL 独立于修复工程师，对树中一切代码（含在途未提交变更）攻击；修复工程师对评审结论不得协商通容，只能以更优算法修复回应或举证反驳。

#### Scenario: 一轮完整闭环
- **WHEN** Round N 启动
- **THEN** 顺序 = 主代理本地提交 → 建 `rounds/roundN/` → 评审工程师对抗攻击 + 合规审计（REVIEW.md）→ 修复工程师 1..m 位算法修复 + 注释三要素（FIX.md，可多份）→ 评审工程师复核（通过/打回，REVIEW2.md）→ 主代理全量验证无回退（VERIFICATION.md）→ 归档 → 提交并 push origin main

### Requirement: 评审工程师独立对抗审查

评审工程师每轮 SHALL 执行两类审查，结论只有「通过 / 打回」两态，打回必须给出锚点（file:line）+ 违反条款编号 + 机制说明：

1. **完备形态攻击**：按本轮主题从台账 §5 已判"完备"形态中抽取（优先文档标榜完备者、前序规范未覆盖或仅抽样覆盖者），每形态构造 ≥10 个最小复现（深层嵌套/交叉组合，深度 ≥3）+ ≥2 个 MATCH 负对照，实测「深层与浅层产物结构一致」；复现存 `test_repros/roundN/`，结果入 `rounds/roundN/REVIEW.md`
2. **算法合规审计**：对当前树逐守卫审查——文件名/函数名白名单、start_offset 魔法阈值、跨层 `entry in blocks` 反查、新增 self 跨方法状态、以少发射换全绿、注释三要素与代码不一致，发现即打回，零容忍

站桩回归（常设）：每轮 SHALL 重放前序已封闭破口的登记探针面（round6 115/115、round7 r7 面、round8 r8 面、round9 50/50 及本规范已完结各轮攻击面），读数不得变差。

#### Scenario: 对抗发现伪完备
- **WHEN** 台账判完备的形态在深层嵌套探针下与浅层产物结构不一致
- **THEN** 登记 Bn 破口（锚点+机制+条款），修复工程师按封闭守卫恢复无感（禁止给个案打补丁）

#### Scenario: 注释与代码不一致
- **WHEN** 识别/生成方法 docstring 声明的识别条件、归约方式或 AST 映射与实际代码行为不符，或缺失 C1/C2/C3 条款声明
- **THEN** 评审工程师打回，修复工程师同步修正注释或代码使两者一致

### Requirement: 修复工程师算法修复

修复 SHALL 只在区域归约算法内进行：禁止跨区域/跨层次启发式、禁止文件名/函数名白名单、禁止 start_offset 魔法阈值、禁止新增 self 跨方法状态、禁止少发射换绿、禁止硬编码深度/计数上限。判据只允许同层块对象的结构事实（块末指令 opcode、后继前驱集合、异常边、区域成员关系）。修复触及的方法 SHALL 同步维护 docstring 三要素（识别条件/归约方式/AST 映射）并注明 C1/C2/C3 条款；注释与代码不一致 = 评审不通过。自测 = 本轮全部 MISMATCH 复现转 MATCH ∧ 负对照保持 MATCH ∧ 小测试集（34 pyc）无回退 ∧ 站桩回归面不变差 ∧ BOM 完整性（utf-8-sig 单头）∧ 无遗留插桩。

#### Scenario: 算法合规
- **WHEN** 修复方案依赖「目标函数名 == 'xxx'」类判据
- **THEN** 评审工程师直接打回，改用同层结构事实判据

### Requirement: 主代理无回退验证

主代理每轮 SHALL 亲自执行验证序（判据唯一 = `scripts/pyc_verify.py`，所有命令 ≤300s，超时分片）：

1. 小测试集（34 pyc）batch 验证：无 success→failure 位移
2. 全量 402 分片 batch（每片 ≤300s）+ `pyc_verify.py compare --before <基线报告> --after <本轮报告>`：**REGRESSIONS=0**
3. `quotation.pyc` 单验通过（无新增失败，承接基线 152/153）
4. 现有区域相关测试（tests/ 下六套件）通过：零新增失败（基线名单 test_B01 + test_BOUNDARY_02）
5. 汇报读数：单元级成功率、文件级 success 数、本轮封闭破口数、站桩回归读数

#### Scenario: 回退拦截
- **WHEN** 批量回归出现任一 success→failure 位移或单元数下降
- **THEN** 本轮修复不得合入，打回修复工程师定位根因

### Requirement: 每轮门禁与推进纪律

- 每轮独立文件夹 `.trae/specs/adversarial-complete-forms-v2-10rounds/rounds/roundN/`（REVIEW.md、FIX.md（可多份）、REVIEW2.md、VERIFICATION.md）；复现在 `test_repros/roundN/`
- 调用子代理前必须先本地提交（含阶段边界：评审后、修复后各一次）
- 每轮必须产出 ≥1 个被登记并封闭的破口，或 ≥1 个 pyc 读数改善；两者皆无 = 本轮未过门禁，禁止开启下一轮
- 每轮结束必须提交并 push 到 origin main
- 所有命令 ≤300 秒，超时必须分片
- 禁止手改 `*OK.py`、禁止修改反编译生成文件、禁止跳过验证、禁止虚报读数、禁止投机取巧；必须逐步进行

### Requirement: 台账推进与终态

- 每个确认破口按 wiki §8.3 状态机推进（未定位→已定位→已落地→已复审），只有走到已复审才允许计入完备分子；每轮封闭的破口随轮更新台账判定
- Round 10 终审 SHALL 统一执行 wiki §8.2 复审六步全量：grep 落地标记 → 台账更新 → `tools/kb/syntax_coverage.py` 重跑 → 占比重算 → wiki 页面数字同步（禁手改、禁矛盾数字）→ log 记录
- 终态目标：残余破口（B42×3/B43/B44/B46–B51/B56–B65/B69/B70 及后续新登记）全部封闭或经对抗证伪降级；台账 128 形态全部经对抗验证仍成立 = 完备占比 128/128；`_identify_*` 十族方法注释三要素全量过审

## MODIFIED Requirements

无。

## REMOVED Requirements

无（历史规范与归档全部保留；对旧规范目录的既有状态不回滚）。
