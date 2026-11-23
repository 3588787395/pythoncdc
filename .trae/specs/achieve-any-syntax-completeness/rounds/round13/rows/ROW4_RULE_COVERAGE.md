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

## 与 REACHABILITY 行 4 字面命令的对齐（未完成）

表内命令的 universe 是 `round9/rule_universe.json`（339 规则）+ `tools/completeness/
rule_manifest.json`。当前链条是 code_root 域扫描口径（344）。终局对齐需在 open 收敛后
按字面命令重跑一遍；两个口径的规则集合差异（339 vs 344）需要在那时逐一裁决。

## 状态

**未达成**：v7（`--also-legacy`）权威读数 open=138 ≠ 0。收敛顺序：
1. 65 条 no_occurrence 逐锚点定性（legacy 死码 / J 未覆盖形态 / patch_detector
   工具路径），可证实的走证据排除，可构造的补 J 探针；
2. 47 条 negative_witness_missing：先裁决 `--structural-negative`
   （v6 敏感性 proved 136→168；v7 重算后需更新该数），再补严格反见证；
3. 26 条 predicate_false_at_site：构造使谓词为真的 J 正见证；
4. open 收敛后按 REACHABILITY 行 4 字面命令（round9 universe 339）终局对齐——
   339 vs 344 差异：338 条共享，round9 独有 1 条（`RULE-95f93fd49770
   _b115_frame_noise`，当前树已不存在该谓词，需裁决刷新 universe 还是字面证死），
   v4 独有 6 条（comprehension_generator 4、region_analyzer 1、region_ast_generator 1）。
