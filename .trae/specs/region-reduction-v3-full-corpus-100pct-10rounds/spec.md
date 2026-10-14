# 全量语料逐文件终局 10 轮 Spec（区域归约算法 · 100% 字节码一致）

## Why

v2 规范（`adversarial-complete-forms-v2-10rounds`）Round 2 已终审放行，但其验证读数来自 P3 在途代码的中间态：Round 2 报告记 `trade_info_utils.pyc` 35/41，而当前 HEAD（d5d3899a）实测重生成产物 sha `0bd56da795ed` 为 **36/41**，即该 −1 单元是过期读数而非在途回退。真实缺口是：402 语料仍有 **33 个文件 / 63 个单元**未达字节码一致（61 个 Different control flow + 3 个 Different bytecode），quotation.pyc 仍卡 152/153。用户要求「每个 pyc 反编译成功、字节码完全匹配、100% 成功率」，且必须由测试工程师 + 修复工程师双角色、每轮独立文件夹、迭代 10 轮达成。

## What Changes

- 建立本规范三件套与 **语料普查表**（1721 pyc 逐类拆解 + 排除反向夹钳），把验证面钉死在「真实语料 = 402」这一口径上。
- **Fresh 基线重验**：用当前 HEAD 代码重生成 402 全部产物 + 八分片 `scripts/pyc_verify.py batch`，产出本规范唯一 before 基线（取代 v2 Round 2 的过期读数）。
- 门禁升级：文件级 `REGRESSIONS=0` **且** 单元级逐文件 `units_success` 不得下降（本轮暴露的盲区：文件分类不变但单元 −1）。
- Round 1–10：每轮 = 测试工程师（每次一个 pyc，产出 ≥10 最小复现 + 分类）→ 修复工程师（区域归约算法 + `_identify_*`/生成方法注释六项模板）→ 主代理验证序六步 → 归档 → 提交并 push（前缀 `rr-v3rNN:`）。
- 每轮硬门禁：至少 1 个 pyc 从 failure 转 success（同目录生成同名 `+OK.py` 且全单元 Equal），或全量单元读数净增；两者皆无禁止下一轮。
- **禁止**手改任何 `*OK.py` 产物；产物只能由 `python pycdc.py -o <pyc去扩展名>OK.py <pyc>` 重生成。
- 验证脚本唯一：`F:\Downloads\pythoncdc-main\scripts\pyc_verify.py`（v2 用的 `pyc_batch_verify.py` 一律不再作为判据）。

## Impact

- affected specs：继承 `adversarial-complete-forms-v2-10rounds` 理论基准 I/II/III/IV（四原则、C1/C2/C3、判据白名单、128 台账、13 误解、IV.2 门禁）；`rules.md` 为本规范强制性工程规范。
- affected code：`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`、`core/cfg/dominator_analyzer.py`、`core/cfg/cfg_builder.py`、`core/cfg/patch_detector.py`（只读参考，禁止新增补丁）、`pycdc.py`、`scripts/pyc_verify.py`（只用作判据，不改判定逻辑）。
- affected data：`site-packages/**/*OK.py`（402 产物）、`pyc_index.json`、`.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/`、`test_repros/roundN/`。
- 交付节奏：每轮 1 次本地提交（派发子代理前）+ 1 次归档提交并 push origin main；所有单条命令 ≤300s（分片并行，verify 内部 290s）。

## 语料普查与排除登记（封表时点 2026-10-05，口径唯一）

`site-packages/**/*.pyc` 实测 1721 个，逐类拆解如下（三类合计 = 1721，无第四类）：

| 类别 | 数量 | 判据 | 处置 |
|------|------|------|------|
| A 真实语料（入本规范验证面） | 402 | 在 `pyc_index.json`，第三方包原始 pyc，文件名无 `OK.cpython-311` | batch 全量验证 + 逐轮修复 |
| B 派生畸形 pyc | 1312 | 文件名含 `OK.cpython-311`（含三层嵌套 `__pycache__`），由历史迭代把 `*OK.py` 再编译成 pyc 再当语料造成 | 排除，不入索引；每轮以反向夹钳脚本重算数量，不得凭空增减 |
| C 会话自造 scratch pyc | 7 | `market_time_probe_recompile/_tmp_difffn/ptradeAccountOK_marker_test/klinedataOK/klinedataOK_check/_load_algo_recomp/__init__OK.py.tmp` 命名或含 `OK`/`tmp`/`probe`/`recomp` 痕迹 | 排除并逐个附来源证据；其中 3 个已有 `OK.py` 者一并登记 |

- **反向夹钳**：`python -X utf8 tools/corpus_census.py`（本规范 Task 0 落盘）输出 1721 = 402 + 1312 + 7 与名单；A 类集合与 `pyc_index.json` 必须 1:1 相等（`A \ index = ∅` 且 `index \ A = ∅`）。
- 用户「所有 pyc 都要过」的口径落在 A 类 402 上：B/C 不是待反编译的原始字节码，而是历史工具产物，反编译它们只会重复 A 已覆盖的形状。此结论以脚本 + 名单落盘可复核。

## ADDED Requirements

### Requirement: 语料普查与验证面钉死
系统 SHALL 落盘可重跑的语料普查脚本，输出 A/B/C 三类数量与名单，并断言 A 与索引 1:1。

#### Scenario: 普查闭合
- **WHEN** 运行 `tools/corpus_census.py`
- **THEN** stdout 含 `total=1721 A=402 B=1312 C=7`，且 `A_delta=0`（对称差为空），退出码 0

#### Scenario: 排除类不可扩张
- **WHEN** 任一轮新增 pyc 出现在 B/C 名单之外
- **THEN** 普查脚本失败并要求先登记类别，禁止静默进入 batch

### Requirement: Fresh 基线（本规范唯一 before）
主代理 SHALL 用当前 HEAD 代码重生成 402 全部产物并跑八分片 batch，产出 `baseline/shard{0..7}_report.json` 与 `baseline_snapshot.md`，作为全部 10 轮 compare 的 before。

#### Scenario: 基线与单文件实测一致
- **WHEN** 基线报告读到 `trade_info_utils.pyc` 单元数
- **THEN** 该读数与 `pyc_verify single`（同一重生产物）逐位相等（预期 36/41，非 v2 Round2 的 35/41）

### Requirement: 单元级不回退门禁
每轮 compare SHALL 同时判定文件级 Movement Matrix（`REGRESSIONS=0`）与单元级逐文件差值（`UNIT_REGRESSIONS=0`：任一文件 `units_success` 下降即为回退，即使其 status 分类未变）。

#### Scenario: 分类未变但单元下降
- **WHEN** 某文件 before/after 均为 failure，而 `units_success` 由 36 变 35
- **THEN** 本轮门禁判 FAIL，必须定位并在同轮封闭或如实回滚该次代码改动

### Requirement: 双工程师轮次编排
每轮 SHALL 由测试工程师先行（每次只取索引中一个 pyc，验证字节码一致性，按不一致点建 ≥10 个最小复现），再由修复工程师依区域归约算法完善程序与注释，主代理只做调度、提交、全量验证与 push。

#### Scenario: 测试工程师产出
- **WHEN** 测试工程师完成本轮
- **THEN** `test_repros/roundN/` 落 ≥10 个可复现单元（每个带 MISMATCH 证据 + 期望 MATCH），REVIEW.md 逐条给锚点 + 机制 + 违反条款（C1/C2/C3 或 I 条款）

#### Scenario: 修复工程师产出
- **WHEN** 修复工程师完成本轮
- **THEN** 复现转 MATCH ∧ 负对照保持 MATCH ∧ 触及方法 docstring 六项模板（①算法依据②归约顺序③唯一归属④嵌套处理⑤入口引用语义⑥反编译流程）+ C 条款齐全，FIX.md 含「代码已落地」声明

#### Scenario: 每轮至少一个 pyc 完全 OK
- **WHEN** 一轮结束时
- **THEN** 该 pyc 同目录存在 `+OK.py` 且 `pyc_verify single` 输出 `status=success`，全量读数净不降；否则禁止开启下一轮

### Requirement: quotation 锚点与批量回归次序
修到某文件完全 OK 后，主代理 SHALL 先单验 `site-packages/fly/data/quotation.pyc`（基线 152/153，零新增失败），再跑八分片批量回归，最后跑 tests 六套件。

#### Scenario: 次序不可交换
- **WHEN** 跳过 quotation 单验直接批量回归
- **THEN** 该轮验证序视为未完成，不得提交 push

## MODIFIED Requirements

### Requirement: 每轮纪律（继承 v2 并加强）
调用子代理前必须本地提交；每轮独立文件夹；每轮提交并 push；命令 ≤300s；产物只由 pycdc 重生成；判据唯一 `scripts/pyc_verify.py`。新增：单元级不回退门禁 + 每次派发前把上一轮过期读数作废并如实登记（不得沿用 v2 Round2 报告作为 before）。

## REMOVED Requirements

### Requirement: 以 v2 Round 2 分片报告作为本规范 before 基线
**Reason**: 其 shard1 读数（461/469）对应 P3 在途代码中间态，与当前 HEAD 实测（462/469）不一致，沿用会掩盖真实缺口。
**Migration**: Task 1 用当前 HEAD 重生成 + 重验，产出本规范 fresh 基线；v2 报告仅作为历史证据保留在 v2 目录。
