# 规则覆盖行（REACHABILITY 第 4 行）读数 — round13

阈值（`REACHABILITY.md` L31）：`open = 0`。本行未达成；以下是当前权威读数与完整链条。

## 权威链条（全部产物已入库）

1. **域扫描**：`tools/completeness/rule_universe.py`（v1.1.1，含 `--opcode-scope {any,interpreter}`
   证据门控过滤，默认 `any` 行为不变）扫描 `core/cfg/**`：
   `fresh/gate_g4/universe_v4.json` — **344 规则 / 5899 occurrences**。
2. **证据门控排除**：`fresh/gate_g4/universe_v5.json`（纯静态过滤，过度排除）→
   `fresh/gate_g4/universe_v6.json`（最终）：**282 保留 / 62 排除，并集 344 守恒**。
   - 排除双门槛：规则符号所属 opcode-set 成员**全部**不在 CPython 3.11 `dis.opmap`
     **且**该符号在 proof_records_v4 全量测量中 `symbol_observed=False`。
   - 7 条被观察证据救回（`rescued_by: symbol_observed_in_traces`，含
     `RULE-9b4f09e19147 CONDITIONAL_JUMP_OPS`、`RULE-bcec04aa5657 IF_ELIF_CHAIN` 等）。
   - **方法学教训（已入 spec）**：排除必须证据门控，纯静态过滤曾错杀 66 条中
     实际 7 条有观察证据的规则。
3. **证明测量**：`tools/completeness/rule_proof_check.py`（v1.1.0，本轮新增两个默认关闭的
   CLI 开关：`--also-legacy` 顺带驱动 v2 生成器入口、`--structural-negative` 同锚异 pyc
   结构性反例；关闭时与旧口径完全一致）：
   `python -X utf8 tools/completeness/rule_proof_check.py --universe universe_v6.json
   --manifest <gate_g4/manifest_v3.json> --jspace <round9/judgment_space.json>
   --traces traces_v4.json --out rows/proof_records_v6.json
   --manifest-out rows/manifest_proved_v6.json`
   — 跑满 1556 J 条目、131 个去重 pyc、447 s，`runs.run_failures` 为空。
4. **G4 门禁彩排**（`rule_manifest.py --check`，输入必须同域配对）：
   `rows/manifest_proved_v6_scoped.json`（从 manifest_proved_v6 过滤到 universe_v6 的
   282 条，否则 62 排除规则成 orphan，open 虚高为 208）→
   `rows/rule_coverage_v6.json`：
   **total 282 / manifest 282 / proved 136 / open 146 / orphan 0 / unmapped 0 /
   empty_cov 100 / G4=FAIL**。

## open=146 构成（proof_records_v6.counts）

| open 原因 | n | 含义 | 已知可行路线 |
|---|---|---|---|
| `no_occurrence_in_J` | 71 | J 运行从未到达锚点（0 次谓词求值） | `--also-legacy` 测量 `ast_generator_v2.py` 遗留管线规则（`unmapped_source_predicates=499` 全在该文件）；或补 J 探针 |
| `predicate_false_at_site` | 29 | 锚点被到达但谓词从未为真 | 构造使谓词为真的 J 正见证案例 |
| `negative_witness_missing` | 46 | 有真见证、缺严格 4.1 反见证（39 条已有 false 求值） | `--structural-negative`（同锚异 pyc 反例，`negative_witness_weak_only=32`，接受后 proved 将到 168）；需先裁决是否采用 |

- `guard_only_proved`（v6=22 / v7=18）：谓词为真但规则自身符号从未成为匹配成员
  （`guard_only=True` 且 `symbol_observed=False`）的 proved 规则。
  **口径更正（2026-11-22 复核）**：`rule_proof_check` 的 status 口径**把这批计入
  proved**（B2 宽松式计数），`G4_REVIEW_PACKET.md` 裁决二**推荐**的 B1 保守口径
  （proved 要求 `symbol_observed=True`，guard_only 仅诊断）**尚未在工具中强制执行**。
  本文件此前的「不计 proved」表述有误，特此更正。两套读数并存：
  工具口径 proved 136（v6）/ 144（v7）；B1 保守口径 proved 114（v6）/ 126（v7），
  对应 open 168 / 156。**终局裁决前，保守读数为准向外部报告**。
  **→ 已按裁决二落定并在工具强制（v8，2026-11-23，见下节）。**

## 裁决二落定：B1 保守口径工具强制（v8，2026-11-23，当前权威）

`tools/completeness/rule_proof_check.py` v1.1.0 → **v1.2.0**：新增
`--counting {b1,b2}`（**默认 b1**）。b1 下 proved 额外要求 `symbol_observed=True`；
仅靠 guard 为真证明的规则降级为 open，reason code 为新码
`guard_only_symbol_not_observed`，附 `b1_downgrade` 诊断（`b2_status="proved"`），
proof/witnesses 全部保留；b2 显式给出时逐位复现 1.1.0 计数。三组回归 guard 全 PASS
（guard a：b2 全量复测 vs v7 逐规则 diff 空、282/282、manifest 344/344、inputs
SHA 一致；guard b：默认 b1 全量 **proved=126 / open=156** 与事后推算逐位一致；
guard c：18 条 guard_only-proved 全部降级、12 条 guard_only-open 逐条不变、
status 变化集恰为 18 条降级集）。新 reason code 下游影响清单已核查：无封闭枚举
校验消费者（`rule_manifest.py` 不读 reason codes；g4decide/g4queue 按 code 聚合无
校验；build_scoped_universe 只读 symbol_observed，v8 与 v7 逐规则相同）。

**v8 权威读数**（`--counting b1 --also-legacy`，131 pyc/1556 entries，runtime 725 s，
`runs.run_failures` 空，`partial_run_failures` 恰为 v7 同款 2 条 legacy_v2 已知缺陷）：
`rows/proof_records_v8_b1.json` ＋ `rows/manifest_proved_v8_b1{,_scoped}.json` →
`rows/rule_coverage_v8_b1.json`：**total 282 / manifest 282 / proved 126 /
open 156 / orphan 0 / unmapped 0 / empty_cov 100 / G4=FAIL
（mapping_or_proof_gap）**。open=156 构成：guard_only_symbol_not_observed **18** /
neg_missing **47** / no_occ **65** / false_at_site **26**。FAIL 主因仍是
empty_cov=100（J 覆盖缺口），与计数口径无关。

- **region-only 交叉核对**（`rows/proof_records_v8_region_b1.json`）：proved **114** /
  open **168**，与 v6 链事后 B1 推算逐位一致（22 条 guard_only-proved 全部降级、
  12 条 guard_only-open 不变）。v8_b1 vs v7 差异恰为 18 条降级集。
- 记录内 `g4_check_rehearsal` 是 unscoped 344 候选彩排口径（orphan 62、open 218），
  权威门禁读数以 scoped `rule_coverage_v8_b1.json` 为准（同 v7 惯例）。
- 验证脚本与完整 provenance：`D:\temp\opencode\cl_layout\g4d\b1_enforce\`
  （REPORT.md/NOTES.md：全部输入 SHA256、冒烟记录、逐 guard 证据、交叉核对总表）。
- **此后对外报告行 4 一律用 v8_b1（工具 B1，proved 126 / open 156）**；v7 B2
  144/138 仅作历史对照保留。

## `--also-legacy` 全量重测（v7，2026-11-22 已执行）

同链条、唯一变量加 `--also-legacy`（region + legacy_v2 双管线测量，
`pipelines: ["region","legacy_v2"]`，runtime 338 s）：
`rows/proof_records_v7_legacy.json` ＋ `rows/manifest_proved_v7_legacy{,_scoped}.json` →
`rows/rule_coverage_v7_legacy.json`：
**total 282 / manifest 282 / proved 144 / open 138 / orphan 0 / unmapped 0 /
empty_cov 100 / G4=FAIL**。

- **翻转明细（v6→v7，逐条核对）**：9 条 open→proved（6 条 ast_generator_v2.py 的
  no_occurrence：Raise/If/AsyncWith/With/SET_ADD/UNARY_NOT 锚点 ＋ exception_handler.py:88
  `_UNCOND_JUMP_TARGET_OPS` ＋ 2 条 predicate_false_at_site 转 proved：
  code_generator.py:2116、ast_converter.py:340）；**1 条 proved→open 回退**：
  `RULE-87685c80e83d`（ast_generator_v2.py:2666）——legacy 管线扩大了该规则的观测
  出现集，v6 的严格反见证不再覆盖并集域 → `negative_witness_missing`。净 +8。
- **legacy_v2 管线实测缺陷（`runs.partial_run_failures`，非本轮引入）**：
  `m06_module_loops.pyc` → `UnboundLocalError: chain_assign_state`；
  `m08_module_stmts.pyc` → `AttributeError: 'ASTGeneratorV2' object has no
  attribute '_get_compare_op'`。即遗留管线对这两个模块是**坏的**（另一证据：
  测量 stderr 出现 `Unknown expression type: Pass`）。这 2 个 pyc 的 region 管线
  读数不受影响。
- v7 open=138 构成：no_occurrence_in_J **65** / predicate_false_at_site **26** /
  negative_witness_missing **47**。剩余 no_occ 中 `ast_generator_v2.py:13459`
  （6 条）等锚点在双管线下仍未到达——遗留死码或 J 未覆盖形态，需逐锚点定性。

## v7 open=138 按文件聚类（收敛用）

| 文件 | no_occ | false_at_site | neg_missing | 合计 | 备注 |
|---|---|---|---|---|---|
| region_ast_generator.py | 16 | 9 | 14 | 39 | 最大簇 |
| code_generator.py | 17（L262–4085 分散） | 10（L2396/3790–3969/4115 等） | 6（L2148–4055） | 33 | |
| ast_generator_v2.py | 9（含 L13459 ×6） | 3 | 18（L1103 ×6、L920 ×4） | 30 | legacy 管线；neg_missing 两锚点占 10 |
| objective_patch_detector.py | 11 | 0 | 0 | 11 | 工具路径，J 测量从不触发 |
| region_analyzer.py | 3 | 0 | 6 | 9 | |
| comprehension_generator.py | 4 | 4 | 1 | 9 | |
| patch_detector.py | 4 | 0 | 0 | 4 | 工具路径，同上 |
| dominator_analyzer.py / basic_block.py / cfg_builder.py | 0/1/0 | 0 | 1/0/1 | 3 | |

聚类启示：patch_detector/objective_patch_detector 的 15 条是**纯工具路径**
（J 测量口径下从不触发），可走证据排除裁决；ast_generator_v2 的 neg_missing
高度集中（L1103/L920 两锚点占 10 条），适合同锚结构性反例一次收敛。

## 输入陷阱（本轮实测，已留档）

- `rule_manifest.py --check` 必须给 `--traces`，否则 `proved=0 open=339
  reason=no_rule_traces`（`rows/rule_coverage_now.json`）。
- universe 与 manifest 必须同域：344 全量 manifest 配 282 scoped universe 会把
  62 条排除规则算成 orphan、open 虚高 208。
- `rule_universe.py --opcode-scope interpreter` 单用会把 7 条有观察证据的规则错杀，
  必须叠加 `symbol_observed` 证据门（本仓库的最终裁决在 universe_v6）。

## 122.9 阶段一：no_occ 65 逐锚点定性＋四项裁定落定（2026-11-26，子代理 b414e496，父代理验收）

全部在 v8_b1 复现环境（edc1ab08 shadow env，8 锚点文件与 universe_v6 声明 text-sha 零漂移；
e1be7895 污染的 jspace/x01/x04 输入以 git show 恢复＋marshal.dumps 相等校验重建）执行。
产出（已入库 rows/）：`REPORT.md`、`classification_65.{json,md}`、`dossier_15.md`、
`sn_flips_enriched.md`、`proof_records_v8_b1_sn.json`、`manifest_v8_b1_sn.json`、
`unmapped_499_report.json`、`sn_compare.json`、`probe_results.json`、`guard_paths.json`。

**no_occ 65 全闭合**：(a) 纯工具路径 **15**（patch_detector 4＋objective_patch_detector 11，
四重证据 E1 静态 import 封闭/E2 core 零引用方/E3 探针 0 进入/E4 v8_b1 0 谓词求值）
＋ (b) 死码 **19**（dict 兼容层 17：`_generate_dict_node` elif 阶梯 16＋FunctionObject@4085，
20 调用点全在 `isinstance(x,dict)` 后、双管道只传 ASTNode、dict 分支 0 次、
`_generate_dict_node` 0 进入；`is_conditional`@basic_block.py:174 全 core 零调用点；
PREP_RERAISE_STAR@agv2 集合守卫遮蔽死分支，相邻 CHECK_EG_MATCH 同理）
＋ (c) J 未覆盖形态 **31**（全部可达：extract_elif_chain 6 条、PRINT_EXPR、
_CHECK_OPS_r08b、_APPEND_OPS dis 回退块、attr/subscr augassign-boolop 等，
每条 evidence 已给出所需形态）＝ 65。

**unmapped_source_predicates=499 定性（解决）**：499 恰为 universe_v6 排除组
（62 组 no_member_in_interpreter_opmap）的 499 锚点，精确镜像：守恒 5400+499=5899、
10/10 示例命中排除组三元组、kept/excluded (kind,symbol) 交集 0。非新增未映射谓词，无需动作。

**裁决三敏感性 v8 重算**（`--structural-negative`，156.4 s，shadow env）：
**proved 126→144（+18）**；47 neg_missing＝18 翻 proved（selection=
same_anchor_diff_pyc，structural_negative=True）＋3 翻 guard_only
（GET_LEN/LOAD_DEREF/LOAD_CLASSDEREF，b1 降级）＋26 余留，闭合。
内部一致性（sn_compare）：282/282 的 (predicate_evaluations,
pyc_runs_reaching_site, anchors_located, anchors_declared) 完全一致、正向见证
126/126 稳定、candidates 5413/unmapped 499 一致 → **SN 仅作用于裁决阶段，度量零扰动**。
v8_b1+SN 读数：total 282 / proved 144 / open 138（guard_only 21 / neg 26 /
no_occ 65 / false 26）/ empty_cov 100 / G4=FAIL。

**父代理验收记录**：classification_65 独立重数 (a)15+(b)19+(c)31=65 逐位一致；
SN 记录独立重数 proved 144/open 138、guard 21=18+3、neg 26=47−18−3 逐位一致；
499 镜像报告守恒核对通过；dossier E1–E4 抽查通过；两条 (b) 断言在 HEAD 亲证：
agv2 L23464 五成员集合守卫遮蔽 CHECK_EG_MATCH/PREP_RERAISE_STAR 两 elif（结构上不可达）、
`is_conditional` 全 core 零调用点。行号偏移系 edc1ab08 vs HEAD 的 agv2 漂移，结构同源。

**四项裁定（父代理，2026-11-26）**：
1. **裁决三落定：采纳 `--structural-negative`**（同锚异 pyc 结构性负见证）为规则证明
   负见证口径。依据：负见证的方法学作用是证明谓词在同一源码锚点具判别力（可为假），
   same_anchor_diff_pyc 保留该性质；SN 度量阶段零扰动（实证）；v6 时代评审包已推荐。
   **行 4 工作基线自本裁定起为 v8_b1+SN：proved 144 / open 138。**
2. **(a) 15 条工具路径**：定性成立，随 universe 刷新按证据排除出 G4 分母
   （排除理由＝宇宙域错误：补丁检测器自有扫描谓词，非反编译度量路径；dossier 归档）。
3. **(b) 19 条死码**：处置「修死优先、删除次之、排除兜底」——
   PREP_RERAISE_STAR/CHECK_EG_MATCH 两遮蔽分支先修复遮蔽（两 opcode 纳入 agv2
   集合守卫），以 J 空间现有 EXCEPTSTAR 96 条复测 legacy_v2：分支被到达且产物保持
   EQUAL 则转可证路径，否则降级管道死码走删除/排除；dict 兼容层 17＋is_conditional 1
   优先删除死码（repo 全域调用点清查＝0 后删，2507 census 0-变化门控＋五案回归），
   发现仓外调用方或 census 噪音则回退证据排除（死码豁免材料已在案）。
4. **(c) 31 条**：保留分母内，扩 judgment_space 补形态推进（J 空间现有 EXCEPTSTAR
   家族 96 条可直接用于遮蔽复测）。
   裁定后收敛目标（分母 282→248 假设 (a)(b) 全数出局）：proved 144 / open 104
   （guard 21 / neg 26 / no_occ 31 / false 26）。

## 122.9 阶段二：A1 解遮蔽＋A2 死码删除＋A3 恒等重锚回归＋B1 设计（2026-11-26，子代理 b414e496，父代理验收通过）

**改动面（r216 提交）**：17 文件，+30/−1174。
- **A1 解遮蔽（1 行）**：agv2 L23464 五成员守卫扩为七成员（+CHECK_EG_MATCH、
  +PREP_RERAISE_STAR），内层 elif 梯 L23467-23503 全成员可达。分支被取到实证
  （sys.settrace 行级＋opname 级对账）：修复前两遮蔽 elif 行 0 次执行（结构性遮蔽
  实证），修复后 CHECK_EG_MATCH 分支体 ×2、PREP_RERAISE_STAR ×6，守卫行入集
  opcode 逐一对账（pyc 级 14/12 未入集部分由更早 except* 结构处理消费，与阶段一
  probe「3113 次进入、区域路径先行消费」定性一致；region 路径五目标行 0 次执行
  before/after 相同——_process_instruction_sequence 仅 legacy_v2 调用）。legacy_v2
  产品 sha16 `C40A243F574405A4` 改动前后逐字节一致（region 文本 `7F318B44E905C9AE`
  同；ast_dict 序列化唯一差异＝code object repr 内存地址，掩码后全同）。
- **A2 删除**：code_generator.py −1125（19 个 dict 兼容方法＋`generate()`/
  `_generate_node()` 两入口 isinstance 守卫＋`_generate_expression` FunctionObject
  elif L4085-4101）；basic_block.py `is_conditional` −24。保留集显式
  （`_generate_annotation_from_dict`/`_generate_arguments_dict`/`_generate_gen_expr_from_dict`
  等活调用方存活，见 row4_stage2/A2_INVENTORY.md §3）；`_generate_slice_as_function_call`
  唯一调用方随删除集消失、一并删。编码保持 cg BOM+CRLF、bb LF，cg 行数 7603→6478。
- **14 个测试文件 convert-first 补丁**：l1-l4/control_flow_matrix/control_flow_
  completeness/iteration/ternary/run_all/nook 等 17 处裸传 dict 调用改走
  `CFGASTConverter` 正典管线——dict 梯子定性为「生产死、测试活」（生产链路
  pycdc.py/unified_generator.py 等全部先转换，删除前基线 l1＝52 项 29 过/5 败/
  18 错经梯子）；`is_conditional` 两处测试（test_cfg.py test_is_conditional 方法、
  test_regression_cfg.py 断言行）随方法删除。

**门闸（全绿，父代理亲证）**：三树普查 changed=0（2510×3 树，a2_corpus 实数
2510，父口径 2507 为旧数）；五案产物与冻结锚点全 16 位 sha16 一致
（`E5B02D5EF81EBF46`/`010AD393…`/`9F4B826E…`/`BB86DF78…`/`C1F2DF54…`，
HEAD==工作树==锚点；代理脚本曾以 8 位前缀对 16 位全值误报 CHANGED，父代理
全值复比对证为假警报）；J 快照 204/204 head==wt 逐字节（59 条 TRY 相对旧快照
漂移在 HEAD 同在，非本次引入）；**隔离 8 套件 HEAD vs HEAD+A1+A2 逐项一致**
（l1 52/l2 40/l3 18/l4 5/region_decoupling 40/cfg 18/regression_cfg 12/
regression 9；ran/fail/err/skip＋失败测试 ID 全同，父代理双树亲跑）；py_compile
三核心文件 0 错；活动残留引用 0（仅陈旧注释，卫生项另列）。

**A3 四读数**（`--counting b1 --also-legacy --structural-negative`）：

| # | 引擎/锚点 | 规则 | proved | open | not_located |
|---|---|---|---|---|---|
| 1 | 阶段一 edc1ab08（原锚） | 282 | 144 | 138 | 0 |
| 2 | HEAD r215 未重锚 | 282 | 98 | 184 | 64（round13 漂移，HEAD 既有） |
| 3 | A1+A2 未重锚 | 282 | 92 | 190 | 123 |
| 4 | **A1+A2 恒等重锚** | **264** | **144** | **120** | **0（264/264 全定位）** |

读数 4 为定论：恒等重锚（universe_v6_rebased.json：1148 直接＋4484 近邻匹配，
11 个已删层锚点丢弃、涉及规则均有活锚，6 文件 5182/5630 锚点全定位）；逐规则
迁移仅 1 条变动＝RULE-a310f7ea600b（no_occurrence→neg_missing，true_evals
0→6，正见证 JS-EXCEPTSTAR-001——A1 修复的可测签名，(a)15 组内判定不变）；18 条
(b) 删除规则出集；144 proved 逐条持平。未重锚读数（#2/#3）下降全部为测量侵蚀
（a3_marginal.json：59 条 predicate_not_located 伪影），非证明回归——未重锚
读数不得用于纵向比较。

**裁决四（结构负证豁免，父代理，2026-11-26）**：分母口径 A 采纳——修活留分母，
**分母 249**（264−(a)15）。RULE-a310f7ea600b（PREP_RERAISE_STAR）elif 为七成员
守卫梯链尾独占成员，到达即必真，严格负见证结构上不可能；其判别力由支配结构证明
（七成员守卫集合＋六前驱 elif 全枚举＋链尾位置三证）。采纳**结构负证豁免**计入
proved。豁免三要件（同类必须齐备，缺一不得豁免）：
①正见证在案（JS-EXCEPTSTAR-001，true_evals 6）；
②支配守卫证据链留痕（守卫集合、elif 全枚举、链尾位置）；
③逐规则显式登记（rule_proof_check 豁免表：规则 id＋证据引用），禁止类别性豁免。
**G4 工作基线更新：249 / proved 145（含 1 条结构豁免）/ open 104**
（guard 21 / neg 26 / no_occ 31 / false 26）。
复用扫描失败的 CACHE/RESUME/RETURN_VALUE/LOAD_CONST 等结构性覆盖指令：逐条按
同三要件申请豁免或造窄窗口条目（N02b 型），不得类别性豁免。

**B1 设计批准（阶段三实施）**：18 条目族 N01-N18（约 20-24 条新 jspace 条目）
覆盖 104 条 open 规则；6 条 neg_missing 无族规则（CACHE/LOAD_CONST/RESUME/
RETURN_VALUE/Name/_B54_LOADISH_OPS）走复用扫描（从现有 1556 条目挖「锚点可达、
谓词假、条目内规则从未真」纯负条目，零成本先落袋）。前置：①jspace re-baseline
（11/204 抽查项 p_j 快照后重写，快照陈旧，B1 实施前须以当前仓内 pyc 重建基线，
否则新旧条目见证不可比）；②裁决四豁免表实现。流程：复用扫描 → 新条目批量落地
（**每批全量 264 规则回归对比，防 p_j 过拟合改变其他规则测量**）→ 验证闭环
（rule_proof_counting 迭代 p_j 1-3 轮/族）→ G4 复测（249 口径，豁免计数单独
披露：145＝144 严格＋1 豁免）。产出目录 `row4_stage3\`。

**卫生项（阶段三后批量处理）**：cg L1435/1568/2963、rag L45429/45720 陈旧注释
（提及已删 dict 层）；`Dict[str, Any]` 闲置注解（generate()/_generate_expression
签名）；`_generate_dict_comp_from_dict` 零调用死码（先在死码，非本次引入，报告
不动）；tests/nook/test_regression.py L15 旧路径（休眠态）。

**downgraded_from_b2_proved＝21（重锚读数）**：未重锚读数因 not_located 污染
不可比，b2 簿记以重锚读数为准。

## 与 REACHABILITY 行 4 字面命令的对齐（未完成）

表内命令的 universe 是 `round9/rule_universe.json`（339 规则）+ `tools/completeness/
rule_manifest.json`。当前链条是 code_root 域扫描口径（344）。终局对齐需在 open 收敛后
按字面命令重跑一遍；两个口径的规则集合差异（339 vs 344）需要在那时逐一裁决。

## 状态

**未达成**。2026-11-26 阶段二落定（r216：A1 解遮蔽＋A2 死码删除＋A3 恒等重锚）
后行 4 工作基线＝**分母 249 / proved 145（含 1 条裁决四结构豁免）/ open 104**
（guard 21 / neg 26 / no_occ 31 / false 26；264 重锚读数 144/120，
(a)15 排除后 249 基数）。收敛顺序：
1. **阶段三（B1 实施）**：jspace re-baseline → 裁决四豁免表（rule_proof_check
   显式实现）→ 复用扫描（6 条 neg_missing 无族规则，现有 1556 条目先挖纯负条目）→
   新条目 N01-N18 批量落地（每批全量 264 规则回归防过拟合）→ G4 复测（249 口径，
   豁免计数单独披露）；
2. 卫生批（cg/rag 陈旧注释、闲置注解、`_generate_dict_comp_from_dict` 死码、
   test_regression 旧路径）；
3. open 收敛后按 REACHABILITY 行 4 字面命令（round9 universe 339）终局对齐——
   339 vs 344 差异：338 条共享，round9 独有 1 条（`RULE-95f93fd49770
   _b115_frame_noise`，当前树已不存在该谓词，需裁决刷新 universe 还是字面证死），
   v4 独有 6 条（comprehension_generator 4、region_analyzer 1、region_ast_generator 1）；
   恒等重锚工件已建立（universe_v6_rebased.json，1148 直接＋4484 近邻），终局
   重扫以届时 HEAD 为准，v8_b1+SN 及重锚读数转为历史基线。
