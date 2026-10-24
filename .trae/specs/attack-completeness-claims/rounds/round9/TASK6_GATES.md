# Task 6 门禁执行记录（rr-v5r06）

输入与产物（均在 `rounds/round9/`）：

| 门 | 输入 | 产物 | 读数 | 判定 |
|---|---|---|---|---|
| G2b | `g2b_402/space_402.json`（402 语料 manifest，p_j=反编译等价源） | `g2b_402/semantic_402.json`（逐样本 C1–C5+verdict，8 分片合并） | EQUAL 57 / DIFFERENT 3（interface.pyc、convert.pyc、user_error.pyc）/ ERROR 342（全部 `original artifact did not load/execute`＝pyc-only 发行缺第三方依赖，环境不可判定） | **FAIL**（可判定 60 条中 3 DIFF） |
| G2c | `g2c_46/space_46.json`（46 真实 pyc，43 现存 + 3 由 stdlib 源重编） | `g2c_46/semantic_46.json` | EQUAL 5 / DIFFERENT 24（19 仅 R7 结构差，5 含行为差：REAL46-004/022/023/031/046）/ ERROR 17（环境） | **FAIL** |
| G3 | 30 条 covered_equal J 样本 × ≤25 mutants（seed 0） | `g3_mutation/`（30 逐案报告 + `g3_sample_summary.json`） | KILLED 32 / MISSED 602 / ERROR 1；mutation_score≈5%；missed 主因＝变异落在 call_exprs 未覆盖的函数（幸存者无等价证明时按口径记 MISSED）——完整变异总体未跑 | **FAIL**（样本级如实；全量总体为剩余工作） |
| G4 | `rule_traces.json`（131 唯一 pyc × coverage.py 行覆盖 → 1556 条 entry 级 rule 命中） | `rule_coverage.json`、`g4_never_hit_rules.json`、manifest witnesses（187 条已填） | 339 规则：187 条被 J 空间执行命中（witness=pos/neg entry），**152 条全程未执行**（opcode_eq 137 + isinstance_ast 15；分布：region_ast_generator 46、code_generator 35、ast_generator_v2 34、死管线 detector 22 等）；proved=0（proof 按框架须评审员供给，未伪造） | **FAIL**（reason=mapping_or_proof_gap；从 INCONCLUSIVE/no_rule_traces 升级为实测覆盖） |
| G5 | 本树复跑：8 分片 6617/6617、small34 1568/1568、quotation 153/153、全量 pytest 406 失败清单与基线逐字节一致、IV.2 全绿 | `g5_regression_current.json` | 全部实质绿；gate 字符串期望「2 failed, 282 passed」为 round8 旧口径（当前同 6 文件套件 277 passed＝套件组合漂移，文件自 889a0417 未改；2 failures 均为 406 基线内既有对：B01_simple_if_then_else_merge、BOUNDARY_02_large_function） | **FAIL（仅陈旧字符串口径）**——实质回归绿，差异原因在案 |
| G6 | 无独立 custody | — | 沿用 round9 旧 canary 20/24；无独立托管 ⇒ 按 Task 7.2 口径应记 `ASSURANCE_BLOCKED`，不以本地 bootstrap 冒充 PASS | **BLOCKED** |

聚合：`GATE_REPORT_V5R06.md` / `gate_report_v5r06.json`（overall=BLOCKED；G1 395/1556、189 diffs 沿 Task 5.4 读数）。

诚实声明：本轮未宣称任何门禁 PASS；G2b/G2c/G4 从 UNESTABLISHED 升级为实测 FAIL 读数（逐条证据在案），G3 建立样本级读数；152 条 never-hit 规则与 G2c 24 条 DIFFERENT（19 条 R7 结构差）登记为后续修复输入。
