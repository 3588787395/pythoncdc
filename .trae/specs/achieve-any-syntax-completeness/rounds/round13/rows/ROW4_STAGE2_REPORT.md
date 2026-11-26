# ROW4 阶段二汇总报告（A1+A2+A3+B1）

- 产出者：fix subagent（r215=52128723 基础上工作，未提交；父代理裁决后提交 r216）
- 日期：2026-11-26；输出目录：`D:\temp\opencode\cl_layout\g4d\row4_stage2\`
- 仓库：`F:\Downloads\pythoncdc-main`；工作树 = HEAD + A1（1 行）+ A2（−1174 行）+ 14 个测试文件补丁（`git diff --stat`：17 files, +30/−1174）

## 1. A1 — agv2 守卫解遮蔽（裁决③ PREP_RERAISE_STAR「修死」路线）

**改动（1 行，ast_generator_v2.py L23464）**：守卫由五成员扩为七成员
`if opname in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START', 'POP_EXCEPT', 'RERAISE', 'CHECK_EXC_MATCH', 'CHECK_EG_MATCH', 'PREP_RERAISE_STAR'):` + 尾注 `# [R215-STAGE2-A1] 解遮蔽：原两 elif 在五成员守卫外不可达`。

**验证**：内层 if 梯（L23467-23503）逐成员 elif，含 L23494 CHECK_EG_MATCH、L23499 PREP_RERAISE_STAR，全部可达且分支被取到；legacy_v2 产品 sha16 **C40A243F574405A4 改动前后一致**（逐字节）。RULE-a310f7ea600b 的可证路径恢复（见 §4 G4 实测：true_evals 0→6）。

## 2. A2 — 死码删除（裁决③ 其余 (b)18 条「删除」路线）

**删除清单**：code_generator.py −1125 行（19 个 dict 兼容层方法 + FunctionObject elif L4085-4101 + generate() L132-135 / _generate_node() L182-187 两个入口守卫）；basic_block.py is_conditional −24 行（L174-197）。编码保持：cg BOM+CRLF（5590 行）、bb LF（351 行）。

**全部门闸通过**：三树普查 changed=0（2510 项）；五用例 5/5；A2 隔离 9 套件与基线逐项一致；py_compile 0 错；活动引用 0；14 个测试文件 convert-first 补丁（`data_gen`→`gen` 型适配），全部套件绿。

## 3. 过程披露

1. **tree_head agv2 UTF-16 损坏事故**：早期用 PowerShell `git show > file` 提取 blob，重定向产生 UTF-16 编码损坏文件；已用 `git cat-file blob` 重提修复，a3_head_env 重建并字节校验。后续一律用 git cat-file / Python 提取。
2. **J 快照（a2_jsnap_threeway.json）**：204/204 条目 head 与 worktree 的 legacy_v2 **逐字节一致** → A1+A2 对 J 产品零影响。59 条 TRY 条目相对旧快照漂移，**在 HEAD 上已同样存在**（非 A1/A2 引入）；另发现 11/204 的 p_j 输入在快照后被重写 → **快照已陈旧，B1 实施前需以当前仓内 pyc 重新基线**。

## 4. A3 — G4 回归四读数（`--counting b1 --also-legacy --structural-negative`）

| # | 引擎/锚点 | 规则数 | proved | open | not_located |
|---|---|---|---|---|---|
| 1 | 阶段一 edc1ab08（原锚） | 282 | **144** | 138 | 0 |
| 2 | HEAD r215（原锚，未重锚） | 282 | 98 | 184 | 64（rag55+agv29，round13 漂移，HEAD 既有） |
| 3 | A1+A2（原锚，未重锚） | 282 | 92 | 190 | 123（cg48+rag55+agv219+bb1） |
| 4 | **A1+A2 重锚（恒等对齐）** | **264** | **144** | **120** | **0（264/264 全定位）** |

**读数 4 即 A3 定论**（a3_rebased_proof_records.json，175.1s）：
- open_reasons：guard_only 21 / neg_missing 27 / no_occurrence 46 / pred_false 26；witness_pos 192 / witness_neg 165；REHEARSAL proved=144 ready=144 empty_cov=82 G4=FAIL（mapping_or_proof_gap，B1 工作面，符合预期）。
- **逐规则迁移（a3_rebased_transition.json，stage-1 → rebased）**：144 proved→proved 全同；46 no_occ / 26 pred_false / 26 neg_missing / 21 guard_only 原因不变；18 条 (b) 删除规则出集；**仅 1 条变动 = RULE-a310f7ea600b：no_occurrence → neg_missing**（true_evals 0→6、symbol_observed=True、正见证 JS-EXCEPTSTAR-001）——A1 修复的可测签名。CHECK_EG_MATCH proved（26/26 锚，43 真/8734 假）、RERAISE proved（49/49 锚）。
- **行漂移日志（父代理要求的独立记录）= a3_marginal.json**：HEAD→A1+A2 仅 59 条规则状态变化，全部 → predicate_not_located（纯行移/删除测量伪影，28 no_occ+10 pred_false+9 guard_only+6 proved+6 neg_missing 来源），其余 223 条逐位一致。未重锚读数（#2/#3）的下降全部由该测量侵蚀解释，非行为回归。
- **重锚工件**：universe_v6_rebased.json（282→264；1148 直接命中 + 4484 近邻回退；11 个 cg L271-410 已删字典层锚点丢弃，涉及规则均保留其他活锚点）+ rebase_report.json + a3_rebase_universe.py（difflib 行映射 + 复刻 _scan_file 发射枚举验证）。注：rebased 读数 drift_rules=228 是重锚工件未刷新 source_sha256 的簿记现象，定位仅依赖 file/line/kind/symbol，无判读影响。

**249 基数（排除 (a)15 工具路径规则）**：proved=144 / open=105 / total=249（(a)15 全部 open）。与父代理预期 248/104 差 **+1 = RULE-a310f7ea600b**：A1 将其修活（裁决③「修死」），留在分母。两种收口口径由父代理裁决：
- 口径 A（修活留分母）：249 / 144 / 105；
- 口径 B（修毕出分母）：248 / 144 / 104。

**PREP_RERAISE_STAR 结构性特例**：该 elif 为七成员守卫内梯最后一支，到达即必真——严格负见证结构上不可能，b1+SN 下只能停在 neg_missing。三个处置选项：① 结构负证豁免（链尾独占成员真评估即完备）；② 宇宙重锚到 L23464 七成员守卫（in-set 谓词，负证易得）；③ 如实保持 open。裁决归父代理。

## 5. B1 — J 空间扩充设计（仅设计，未实现）

`B1_J_EXPANSION_DESIGN.md`（310 行）+ 机读版 b1_design_data.json：
- 范围：104 条 open 规则（(c)31 + false_at_site 26 + neg_missing 26 + guard_only 21）+ PREP_RERAISE_STAR 特例。
- 方案：**18 个新条目族 N01-N18**（表达式全家桶/elif 链六成员旗舰/推导式电池/三元布尔链/存储形态/with 解包/异常 handler 组/single 模式 PRINT_EXPR/大函数 EXTENDED_ARG 等）覆盖 104 条中的 96 条；其余 6 条 neg_missing 规则走**复用扫描**（从现有 1556 条目挖「锚点可达、谓词假、条目内从未真」纯负条目）。预计新增 jspace 条目 20-24 个。
- 关键设计点：N15 elif 链条目一条覆盖六成员规则（嵌套 If 标记 index≤2 约束）；负证优先复用、缺口再造；每批新 pyc 全量 264 规则回归（防 p_j 过拟合改变他规则测量）。
- 风险清单：快照陈旧须先 re-baseline；CACHE/RESUME/RETURN_VALUE/LOAD_CONST 结构性覆盖指令可能无纯负条目（豁免名单）；G4 终读分母口径待裁决。

## 6. 建议（供父代理裁决/收口）

1. **r216 提交就绪**：A1+A2+14 测试补丁全门闸绿，可整体提交；建议 commit message 披露 convert-first 测试补丁与 A1 七成员守卫语义。
2. **B1 前置**：先做 jspace re-baseline（11/204 p_j 已重写），再按设计文档四步实施（复用扫描 → 新条目 → 验证闭环 → G4 复测）。
3. 残留卫生项（非本阶段改动，待父代理安排）：cg L1435/1568/2963 与 rag L45429/45720 注释仍提及已删 dict 兼容层；`Dict[str, Any]` 注解 A2 后闲置；`_generate_dict_comp_from_dict` 零调用死码（阶段一已录，非本次引入）；tests/nook/test_regression.py L15 旧路径。
4. downgraded_from_b2_proved：rebased 读数 21（未重锚读数因 not_located 污染不可比）；b2 簿记口径以重锚读数为准。

## 7. 工件清单（row4_stage2\）

- **A3 定论**：a3_rebased_proof_records.json / a3_rebased_manifest.json / a3_rebased_transition.json / universe_v6_rebased.json / rebase_report.json / a3_rebase_universe.py / a3_rebased_analyze.py
- 行漂移与对照：a3_marginal.json + a3_marginal.py / a3_proof_records.json / a3_head_proof_records.json / a3_transition.json / a3_analyze.py
- **B1**：B1_J_EXPANSION_DESIGN.md / b1_design_data.json / b1_rules_104.json / b1_rules_detail.txt / b1_patterns.txt / b1_list_all.txt
- A2 证据：a2_jsnap_threeway.json（204/204）
- 临时物已清理（a2_jsnap_tmp）；a3_env / a3_head_env 保留供复核。

**结论：A1+A2 对存活规则零证明状态回归（proved 144 持平，逐规则迁移仅 PREP_RERAISE_STAR 一条且为修复签名）；A3 通过恒等重锚读数定论为 264: 144/120，249 基数 144/105；B1 设计就绪待批。**
