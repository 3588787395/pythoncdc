# G4 前五簇探针回合报告（round13 / jspace_v3 / fresh/gate_gap）

> 只读分析：未改 `core/`、`scripts/`、`tests/`，未改 `tools/completeness/rule_manifest.py` 等工具，
> 未改 `judgment_space.json` / `rule_universe_current.json` / `rule_traces_current.json`。
> 本轮只写「命中」这一步，**没有**写任何 `status`/`witness`/`domain`/`proof`。

## 1. 结论（一句话）

新增 11 条探针、覆盖 5 簇全部结构，但**前 5 簇 41 条规则在本追踪器下 0 条可命中**：
`empty_cov` 由 99（2026-10-27 读数）变为 **157**（今天在同一 `core/` 树上重跑），
**探针自身贡献的下降为 0**；下降量为负的原因是旧 traces/universe 与今天的 `core/` 已经漂移（见 §4）。

## 2. 实测读数

| 运行 | jspace | traces | entries | failed | rules_hit | empty_cov | G4 |
|---|---|---|---|---|---|---|---|
| 基线（g4_empty_cov.json 所用，2026-10-27） | round9/judgment_space.json (1556) | `fresh/g4_audit/rule_traces_current.json` | 1556 | 0 | 243 | **99** | FAIL |
| 今天重跑基线（同一 1556 条） | 同上 | `D:\temp\...\rule_traces_base_today.json` | 1556 | 0 | 185 | **157** | FAIL |
| 今天 + 11 条探针 | 合并后 1567 条 | `D:\temp\...\rule_traces_plus.json` | 1567 | 0 | 185 | **157** | FAIL |

命令（cwd = `F:\Downloads\pythoncdc-main`）：

```powershell
# 合并（judgment_space.entries + g4_probe_entries.entries）
D:/Python/python.exe -I -X utf8 .trae\specs\achieve-any-syntax-completeness\rounds\round13\jspace_v3\fresh\gate_gap\_build_artifacts.py --merge

# 追踪（现成追踪器，未改）
D:/Python/python.exe -I -X utf8 .trae\...\fresh\g4_audit\trace_g4_current.py `
  --universe .trae\...\fresh\g4_audit\rule_universe_current.json `
  --jspace   D:\temp\opencode\cl_layout\gap\jspace_plus.json `
  --out      D:\temp\opencode\cl_layout\gap\rule_traces_plus.json

# 读数（check）
D:/Python/python.exe -I -X utf8 tools\completeness\rule_manifest.py --check `
  --universe .trae\...\g4_audit\rule_universe_current.json `
  --manifest .trae\...\g4_audit\rule_manifest_current.json `
  --jspace D:\temp\opencode\cl_layout\gap\jspace_plus.json `
  --traces D:\temp\opencode\cl_layout\gap\rule_traces_plus.json `
  --json   D:\temp\opencode\cl_layout\gap\rule_coverage_plus.json
```

关键输出行：

```
[trace] entries=1567 failed=0 rules_hit=185/342 never_hit=157        (plus)
[trace] entries=1556 failed=0 rules_hit=185/342 never_hit=157        (today baseline)
[rule_manifest] total_rules=342 manifest=342 unmapped=0 orphan=0 proved=0 tested_only=0 open=342 empty_cov=157 G4=FAIL reason=mapping_or_proof_gap
[rule_manifest] ... empty_cov=157 G4=FAIL ...                        (today baseline: 同一读数)
[observed] empty_cov oct27=99 today=157 plus=157 target_hits=0/41
```

**41 条目标规则**：在今天基线里 41/41 为空，加探针后仍 41/41 为空（`g4_probe_observed.json`）。

## 3. 五簇逐簇判定

| 簇 | 规则数 | 命中 | 一句话原因 |
|---|---|---|---|
| 1 `CodeGenerator._generate_dict_node` | 16 | **0** | `_generate_dict_node` 只在 `CodeGenerator.generate()/_generate_node()` 收到 **dict** AST 时进入；本追踪器固定传 `CFGASTConverter().convert(ast_dict)`，其返回类型是 `ASTNode|None`（`convert_body` 丢弃转换失败的 dict），dict 永远到不了该函数。实测：11 条探针 + 131 个真实 pyc 中 `code_generator.py:255-467` 执行 0 行。 |
| 2 `ASTGeneratorV2._generate_if_ast` | 10 | **0** | 该函数只由 legacy `ASTGeneratorV2` 调用；区域流水线对 `ast_generator_v2` 只用到 `ExpressionReconstructor`（`_process_instruction` 等）。唯一桥 `_decompile_nested_code` 需要 `ASTConstant` 里放 `types.CodeType`，11 条探针（嵌套 def/lambda/推导式/类体）中该分支一次都没走到。 |
| 3 `extract_elif_chain` | 6 | **0** | 同上（`_generate_if_ast` 的嵌套函数）；且这 6 条的第二个锚点集落在 `code_generator.py:266/270/315/317/366/405`，同样在 `_generate_dict_node` 体内，与簇 1 同一死路。 |
| 4 `StructuredAnalyzer._identify_with_structures` | 5 | **0** | `StructuredAnalyzer` 只由 `ASTGeneratorV2.__init__`(`ast_generator_v2.py:3508`)、`exception_handler`（区域路径从不调用）、以及模块级 demo(`structured_analyzer.py:16082`) 构造；区域流水线从不构造它，整个 `structured_analyzer.py` 在语料 + 探针中执行 0 行。锚点位于「≥2 个 BEFORE_WITH 且其间无 STORE/POP_TOP」的多上下文 with 合并分支，但函数本身从未进入。 |
| 5 `ObjectivePatchDetector._extract_test_pattern` | 4 | **0** | 该模块是独立 CLI 探测器（文件自身 `__main__` 里 `detector = ObjectivePatchDetector()`），`core/` 里没有任何 importer；兄弟锚点所在的 `core/cfg/patch_detector.py` 同样不在区域路径上（执行 0 行）。 |

补充：`pj_patchpat_*` 与 `pj_with_*` 在**输入语法**上是到位的（`with a() as x, b() as y:`、`async with`、`isinstance/Attribute/Call/BoolOp` 测试形态都编译并进了追踪），失败点不在探针形状，而在追踪器的固定流水线。

## 4. 关键发现：universe/traces 与今天的 `core/` 已漂移（必须先解决）

`g4_empty_cov.json` 的 99 是 2026-10-27 的读数，`rule_universe_current.json` 与
`rule_traces_current.json` 都是那一版 `core/` 的产物；今天 `core/cfg` 已前进 81 个提交。
按「旧行号 × 新文件」做行覆盖，锚点会落到别的语句上：

| 文件 | 旧版(2026-10-27) 行数 | 现在行数 | 旧行号 N 处的旧内容 | 现在行号 N 处的内容 |
|---|---|---|---|---|
| `core/cfg/code_generator.py` | 6294 (`aebb67ff`) | 6715 | 257 `if node_type == 'Module':`（正是 RULE-1f2bf6bdcd1e 的模式） | 257 `if not isinstance(node, dict) ...`（模式已跑到 262） |
| `core/cfg/ast_generator_v2.py` | 27676 (`8b250a4c`) | 27691 | 10638 `elif instr.opname in ('GET_ATTR', 'GET_ITER')`（正是 RULE-05f8183d28bc） | 10638 另一个 opname 成员测试 |
| `core/cfg/structured_analyzer.py` | 16096 (`33d6e87e`) | 16096 | 13926 与今天一致 | 13926 与规则模式一致（该文件未漂移） |

漂移量：旧 243 命中中有 **67 条今天打不中**（region_ast_generator 38 / code_generator 17 /
ast_generator_v2 7 / region_analyzer 4 / ast_converter 1），另有 9 条变成命中。也就是说
**99 与 157 都是"真"读数，只是对应的 `core/` 版本不同**；在解决 universe 重新生成之前，
「empty_cov 下降多少」没有可比口径。本回合能给出的唯一可比口径是**同一天同一棵树**的
基线 vs 加探针：**157 → 157（Δ=0）**。

## 5. 要让这 41 条真正可命中，需要什么（本轮不做）

1. **重新生成 universe/manifest**（`rule_universe.py --generate` + `rule_manifest.py --generate`）到当前 `core/`，
   并重跑基线 traces —— 否则 99/157 的口径不成立。
2. 二选一，且都需要评审：
   - 把追踪器流水线扩到 `CodeGenerator(dict)` / legacy `generate_ast_v2` 路径（覆盖簇 1/2/3），
     以及让 `patch_detector` / `StructuredAnalyzer` 进入区域路径（覆盖簇 4/5）；或
   - 对这 41 条按 reviewed 做**宇宙排除**（附引用面证据，见 `g4_probe_reachability.json`）。
3. 在此之前，簇 1-5 的 41 条既不能给出 positive witness，也不应被填 witness/domain/proof。

## 6. 文件清单

新增（全部在 `fresh/gate_gap/`）：

- `probes/pj_dictnode_01.py` … `pj_with_02.py`（11 个源文件）+ 同名 `.pyc`（`py_compile` 产物）
- `probes_manifest.json` —— 每条探针的 `p_j` / `pyc` / sha256 / `input_model.calls` / `expected_label{form,host,depth,variant}` / `excluded` / 目标 rule_id
- `g4_probe_entries.json` —— 11 条增量 J 条目（judgment_space entry schema，`status="uncovered"`，`excluded=[]`）
- `g4_probe_observed.json` —— 三次追踪 + check 的读数、逐簇命中数、逐探针 `rule_ids` 摘要
- `g4_probe_reachability.json` —— 五个入口点的静态调用面证据（含每个引用的宿主函数）
- `_build_probes.py` / `_build_artifacts.py` / `_build_observed.py` —— 可复跑构建器
- `_work/`（scratch，只读实验用）：`probe_trace.py`、`anchor_hit.py`、`who_ran.py`、`reachability.py`、`dump_anchors.py`、`anchors.txt`、`cand/`

临时（`D:\temp\opencode\cl_layout\gap\`）：

- `jspace_plus.json`（1567 条 = 1556 + 11）、`jspace_base_only.json`、`jspace_mini.json`
- `rule_traces_plus.json`、`rule_traces_base_today.json`、`traces_mini.json`
- `rule_coverage_plus.json`、`rule_coverage_base_today.json`
