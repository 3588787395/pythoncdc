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

- `guard_only_proved=22`：谓词为真但规则自身符号从未成为匹配成员，如实标注，
  不计入 proved（保守口径：`proved ⇒ symbol_observed=True`）。
- `proved_if_weak_negative_accepted=168`：仅记录敏感性，不作为读数。

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

**未达成**：open=146 ≠ 0。下一步按上表三类 open 分别收敛（先 `--also-legacy` 全量重测
拿新读数，再裁决 structural-negative，最后补正见证案例）。
