# Tasks

目标：402 真实语料逐文件达到字节码完全一致（units 6617/6617 = 100%，files 402/402 success），quotation 153/153；`_identify_*` 与对应生成方法注释六项模板与代码一致；单元级 + 文件级双不回退门禁全程成立。
理论依据：`rules.md` §1（四原则 + C1/C2/C3 + 判据白名单 + 禁止事项 + 修复语义 + 注释口径）+ 继承 v2 spec 理论基准 I/II/III/IV。角色：主代理 = 调度 + 阶段提交 + 全量验证 + push（零实现）；测试工程师（子代理）= 逐 pyc 复现与登记破口；修复工程师（子代理）= 区域归约算法完善 + 注释合规。
纪律：每轮独立文件夹；派发子代理前必须本地提交；每轮 ≥1 个 pyc 转完全 OK（或读数净增）否则禁止下一轮；每轮提交并 push（前缀 `rr-v3rNN:`）；单条命令 ≤300s；禁止手改 `*OK.py`；判据唯一 `scripts/pyc_verify.py`。

- [ ] Task 0: 三件套与语料普查就位（主代理）
  - [ ] 0.1 本规范 `spec.md`/`tasks.md`/`checklist.md` 落盘
  - [ ] 0.2 落盘 `tools/corpus_census.py`：输出 `total=1721 A=402 B=1312 C=7` + A/B/C 名单 + `A_delta`（A 与 `pyc_index.json` 对称差），非 0 则退出码 1
  - [ ] 0.3 普查读数与名单快照写入 `baseline/corpus_census.json`（封表时点 2026-10-05）
  - [ ] 0.4 本地提交（派发前置）

- [ ] Task 1: Fresh 全量基线重验（主代理，作废 v2 Round2 过期读数）
  - [ ] 1.1 八分片 regen：`verify_driver.py` 同构驱动（`pycdc.py -o <pyc>OK.py <pyc>`，每文件 90s 上限），产物写回 site-packages 同目录
  - [ ] 1.2 八分片 `pyc_verify batch` → `baseline/shard{0..7}_report.json`（每片 ≤290s）
  - [ ] 1.3 聚合 → `baseline_snapshot.md`：预期 units ≈ 6554/6617、files 369/402、quotation 152/153、34 小测试集 1505/1568
  - [ ] 1.4 交叉核对：`trade_info_utils.pyc` batch 读数 = `single` 实测 36/41（证明基线与当前 HEAD 一致）
  - [ ] 1.5 tests 六套件基线失败名单落盘 + 本地提交

- [ ] Task 2: Round 1 — 单单元损失族（22 个文件各失 1 单元，含 quotation 除外）
  - [ ] 2.1 测试工程师：按索引每次只取 1 个 pyc（顺序 `IQCommon/util/cgroup_utils` → `IQCommon/util/email_utils` → `IQData/utils/calexrights_func` → `IQData/plugins/plugin_system_fly_basicdata/calexrights_func` → `IQCommon/data/finance` → `IQCommon/logger/handlers`），逐单元定位不一致点，每个缺陷建 ≥10 最小复现（深度 ≥3 变体 + ≥2 MATCH 负对照），登记破口（B98+ 续接：锚点 + 机制 + 违反条款）→ `rounds/round1/REVIEW.md` + `test_repros/round1/`
  - [ ] 2.2 修复工程师：依区域归约算法封闭（判据只取白名单：块末 opcode / 后继前驱 / 异常边 / 区域成员关系；修复语义 = 封闭守卫恢复 C1/C2/C3，禁个案补丁 / 按深度特判 / 窄门控）；触及方法 docstring 六项模板 + C 条款；自测 = 复现转 MATCH ∧ 负对照不变差 ∧ 34 小测试集 ∧ 单元级不回退 ∧ IV.2 门禁自检 → `rounds/round1/FIX.md`（含「代码已落地」声明）
  - [ ] 2.3 派发前本地提交；本轮结束按验证序六步验证并 push

- [ ] Task 3: Round 2 — 双单元损失族（real_quote 43/45、risk_calculation/__init__ 41/43、future_contract_info 27/29、ptradeAccount 135/137）
  - [ ] 3.1 测试工程师：同 2.1 攻击协议，逐 pyc 一个，≥10 复现/缺陷
  - [ ] 3.2 修复工程师：同 2.2 约束
  - [ ] 3.3 复核 + 验证序六步 + push

- [ ] Task 4: Round 3 — 三单元损失族（klinedata 61/64、wizard_quant_api 55/58、order_api 34/37）
  - [ ] 4.1/4.2/4.3 同 Round 2 结构

- [ ] Task 5: Round 4 — quotation 终局单元（`<module>.change_his_to_forward` Different control flow，152→153）
  - [ ] 5.1 测试工程师：change_his_to_forward 逐指令 diff + ≥10 复现 + 负对照；quotation 其余 152 单元作站桩回归面
  - [ ] 5.2 修复工程师：封闭并使 quotation.pyc `single` 达 `status=success`（本规范首个全量锚点文件级 100%）
  - [ ] 5.3 验证序六步 + push

- [ ] Task 6: Round 5 — Different bytecode 残余（quote 84/92 的 8 单元 + trade_live_broker 的 3 个 bytecode 单元）
  - [ ] 6.1/6.2/6.3 同构；bytecode 差异必须回到发射层归约正确性，禁止字面拼装

- [ ] Task 7: Round 6 — 大损失文件（trade_live_broker 118/128 剩余 control-flow 单元）
  - [ ] 7.1/7.2/7.3 同构

- [ ] Task 8: Round 7 — 已封闭守卫族外推重放（外推/收缩双向攻击，验证守卫恢复嵌套无感而非窄门控）
  - [ ] 8.1 测试工程师：前六轮封闭面做外推/收缩双向攻击 + 站桩回归重放，读数不得变差；新破口登记 Bn 续接（锚点 + 机制 + 违反条款）
  - [ ] 8.2 修复工程师：封闭暴露缺口（I.3 推论 = 封闭守卫恢复无感；窄门控 = 以少发射换全绿的黑名单变体，打回）
  - [ ] 8.3 验证序六步 + push

- [ ] Task 9: Round 8 — 残余清零冲刺（任何仍未转 success 的文件逐 pyc 处理）
  - [ ] 9.1 测试工程师：按残余名单每次取 1 个 pyc，≥10 复现 + 逐项判据形态评估（可封闭 / 需证伪 + C1/C2/C3 归属）
  - [ ] 9.2 修复工程师：封闭；不具备判据形态者按 wiki §8.3 证伪降级并记录机制
  - [ ] 9.3 验证序六步 + push

- [ ] Task 10: Round 9 — 402 全量终局复验（目标 units 6617/6617、files 402/402）
  - [ ] 10.1 八分片 regen + batch + compare（before = Task 1 基线），双门禁 REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0
  - [ ] 10.2 逐文件 `+OK.py` 存在性与 `single` status 抽验（≥30 文件覆盖各区域族）
  - [ ] 10.3 残余非 success 文件（若有）逐 pyc 登记 → 同轮封闭 → 重跑
  - [ ] 10.4 验证序六步 + push

- [ ] Task 11: Round 10 — 注释合规终审与台账定稿
  - [ ] 11.1 `_identify_*` 十族 + 对应生成方法 docstring 六项模板逐方法一致性审计（不一致即修：以代码真实算法为准修注释，或以注释声明的正确算法为准修代码，禁含糊）
  - [ ] 11.2 `tools/kb/syntax_coverage.py` 重跑 + wiki 台账数字同步（禁手改矛盾数字）
  - [ ] 11.3 终验（全量 + quotation + tests 六套件 + 普查反向夹钳）+ 汇报终态读数（单元级/文件级/破口状态/注释合规面）+ push

注：10 轮用尽仍未达 100% 时，如实上报残余清单（文件 × 单元 × 违反条款），不得为凑读数改判据或手改产物。

# Task Dependencies

- Task 0 → Task 1 → Task 2 … Task 11 严格顺序（前一轮门禁未过禁止开启下一轮）
- 每轮内：测试工程师 → 修复工程师 → 主代理验证 → 提交 push 串行；多位修复工程师仅在破口族 ∧ 涉改文件不相交时可并行
- Task 10 的终局复验依赖 Task 2–9 全部封闭标记落盘（grep 落地标记为凭）
- 每次派发子代理前必须先有本地提交（用户硬约束）
