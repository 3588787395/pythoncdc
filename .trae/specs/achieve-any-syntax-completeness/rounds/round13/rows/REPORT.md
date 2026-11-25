# 122.9 阶段一 · 行 4（G4 规则覆盖）no_occ 65 条定性 REPORT

**基线**：proof_records_v8_b1.json（universe_v6：282 kept / 5400 anchors + 62 excluded / 499 anchors；
131 dedup pyc / 1556 J 条目；total 282 / proved 126 / open 156（guard_only 18 / neg_missing 47 /
no_occ 65 / pred_false 26）/ orphan 0 / unmapped 0 / empty_cov 100 / G4=FAIL）。

**环境完整性**：所有分析在 `v8b1_env` shadow env（`git archive edc1ab08`）执行——v8_b1 的 8 个
锚点文件在 edc1ab08 处与 universe_v6 声明的 text-sha 完全一致（**零漂移**）；输入 4 JSON 中
jspace 曾被 e1be7895（122.20, 11-24）污染、x01/x04 pyc 被重写，均已在 shadow env 中以
`git show edc1ab08` 恢复旧 jspace、并经「compile(HEAD 源码, 现行 co_filename) 的
marshal.dumps == 现行 pyc」校验后重建。core/ 零改动；仓库无提交。

---

## 交付物 1：no_occ 65 条逐锚点定性（全闭合）

分类合计：**(a) 15 + (b) 19 + (c) 31 = 65**（`classification_65.json` / `classification_65.md`；
每条含 rule_id、symbol、anchor、类别、守卫链、真实外层函数及入口计数、行动建议）。

### (a) 纯工具路径 · 15 条
patch_detector.py 4 条（Assign@328；List/Set/Tuple@425）+ objective_patch_detector.py 11 条
（FunctionDef/AsyncFunctionDef@89、ClassDef@93、If@181、Compare@191、BoolOp@195、Attribute@197、
Call@199、Name@207、Subscript@211、Constant@213）。四重证据（静态 import 封闭 / core 引用封闭 /
探针 0 进入 / v8_b1 0 谓词求值）见 **dossier_15.md**。→ 建议排除出 G4 分母（宇宙归类错误）。

### (b) legacy 死码 · 19 条
- **dict 兼容层 17 条**（管道死码）：16 条 `_generate_dict_node`（code_generator.py:255 elif 阶梯，
  AnnAssign/Assert/Assign/AsyncFor/AsyncFunctionDef/AugAssign/ClassDef/Delete/Expr/FunctionDef/
  Global/Import/ImportFrom/Module/Nonlocal/Pass）+ FunctionObject@4085。全部 20 个调用点在
  `isinstance(x, dict)` 之后；实测双管道只经 CFGASTConverter 传 ASTNode——generate 进入
  131/129 次、_generate_node 9055/4369 次、_generate_expression 35449/9051 次，dict 分支
  **0 次为真**；_generate_dict_node 全程 0 进入。
- **零调用点死方法 1 条**：is_conditional（basic_block.py:193）——全 core/ 0 调用点，探针 0 进入。
- **遮蔽死分支 1 条**：PREP_RERAISE_STAR（ast_generator_v2.py:23481）——elif 位于
  L23446 `if opname in ('PUSH_EXC_INFO','WITH_EXCEPT_START','POP_EXCEPT','RERAISE',
  'CHECK_EXC_MATCH')` 体内，PREP_RERAISE_STAR 不在集合中且集合成员被更早分支消耗 →
  **对任意输入结构上不可达**。相邻 CHECK_EG_MATCH@23476 同理为死码（非本轮规则，可顺带标注）。

### (c) J 未覆盖形态 · 31 条
全部为可达代码（外层函数或其调用链在度量中运行过），但 1556 J 条目未产生所需字节码形态。
代表性守卫链证据（`guard_paths.json`，AST 包含式守卫走查 + 探针入口计数）：
- extract_elif_chain 6 条（Break/Continue/For/Match/Try/While，同锚点 agv2:13459）：函数进入
  243 次（legacy），需 else 体出现「`_is_nested_if` 标记 If 且 index 1-2」形态——从未发生。
- PRINT_EXPR@agv2:11556（真实外层 `_generate_if_ast@10211`，793 次 legacy；**经 AST 包含关系
  修正**，原 name 级定位误挂 get_predecessor_instructions@10741）：需「复合条件 if + 回边 +
  CALL 族后继」组合。
- _CHECK_OPS_r08b@rag:41716（真实外层 `_generate_try@40468`，187 次 region；同样修正）：需
  「外层 handler 条目非空」的 try 形态。
- 其余 23 条（_APPEND_OPS、_BIND_STORE_OPS/_BIND_UNPACK_OPS、_jump_ops、_ctx_value_ops、
  _hb_noise_ops、_frame_bookkeeping、_NOISE、_STORE_CHK_R02、_STORE_OPS_R2P02、_v105_sub_attr、
  _b107_store_ops、_b33_noise、_bounce_names、_cmp_ops_set、_cso、_mt_store_ops、_skip_ops、
  skip_ops、attr、subscr、_yf_store_ops、_DELETE_NAME_OPS）：逐条守卫链与所需形态见
  `classification_65.json` 的 evidence 字段。例如 `_APPEND_OPS` 的调用方
  _parse_comprehension_from_code 进入 65 次，但主路径 L3251-3252 总是提前返回，dis 回退
  try 块（L3257）从未进入；`attr/subscr` 需 `x.y += <boolop>` / `x[i] += <boolop>` 形态
  （augassign_target_kind 由 region_analyzer 仅在 attr/subscr augassign 区域设置，
  5 次 BoolOp 调用均被 L53321 前置 return 拦截）。

**行动**：(b) 判死并排除出分母；(c) 保留分母内，阶段二扩充 judgment_space 补齐对应形态
（每条 evidence 已给出所需形态）。

---

## 交付物 2：unmapped_source_predicates=499 定性（已解决）

**结论：499 = universe_v6 排除组（62 组，reason=`no_member_in_interpreter_opmap`）的 499 个
锚点，一一精确镜像。** 证据（`unmapped_499_verify.py` / `unmapped_499_report.json`）：
1. 守恒精确：kept 5400 + excluded 499 = 5899（= universe_v4 全量 344 规则的 5899 occ）。
2. v8_b1 的 `unmapped_source_predicates` 明细 10 个示例全部命中排除组的 (file,line,symbol) 三元组。
3. kept 与 excluded 的 (kind,symbol) 交集为 0——排除组不会与 kept 组共享谓词符号。

即 499 不是「源码中存在但未映射的谓词」，而是「因操作码不在 CPython interpreter opmap 中而
**预先排除**的规则锚点在 candidates 扫描中的自然回显」。无需新增映射；G4 分母自始不含它们。

---

## 交付物 3：裁决三敏感性 v8 重算（--structural-negative）

**复算**：`proof_records_v8_b1_sn.json`（shadow env，`--counting b1 --also-legacy
--structural-negative`，156.4s）。**读数**：total=282 / **proved=144**（126→144，+18）/
**open=138**；open_reasons：guard_only 21 / neg_missing 26 / no_occ 65 / pred_false 26；
witness_pos=191、witness_neg=165、no_occurrence=65、drift_rules=0、weak_negative_only=14、
downgraded_from_b2_proved=21、singleton_composition=0。REHEARSAL：proved=144 / ready=144 /
empty_cov=100 / G4=FAIL。stderr 仅良性警告（ImportFromPending/Pass）。

**内部一致性（sn_compare.py）**：282/282 规则在 (predicate_evaluations, pyc_runs_reaching_site,
anchors_located, anchors_declared) 完全一致；正向见证 126/126 稳定；no_occ 65 完全一致；
candidates 5413 / unmapped 499 完全一致 → **SN 仅作用于裁决阶段**，度量阶段零扰动。

**翻转明细（sn_flips_enriched.md，含每条 witness 与首个负见证）**：
- **18 条 open→proved**（全部 neg_missing，selection=same_anchor_diff_pyc，
  structural_negative=True，witness 均为 1/1）：RULE-105526e5cb57（FOR_ITER_OPS,
  dominator_analyzer.py:468）、RULE-196b1a690257/RULE-440f9734bda7/RULE-5f8a4ca1dd8a/
  RULE-6b8f5b50d608（LOAD_NAME/LOAD_FAST/LOAD_GLOBAL/LOAD_CLOSURE, agv2:1103）、
  RULE-37407d3cc94a（base_skip, rag:7109）、RULE-4970d5d079cd（context_expr_ops, ra:9777）、
  RULE-75ad9c36dc4f（check_ops, ra:13382）、RULE-82b8a73502b4（_b112_noise, rag:14557）、
  RULE-85dd5276273c（_stmt_terminators, rag:34022）、RULE-8f02f7727b77（_CHECK_OPS, ra:13649）、
  RULE-aa4f7207f477（_pp.COND_JUMP_OPS, ra:2305）、RULE-b8c8ba46b225（stmt_boundary_ops,
  rag:77619）、RULE-baa4d7477cbf（EFFECTIVE_NOISE_OPS, ra:4258）、RULE-cc3bd8d61747
  （_CMP_SKIP_OPS, rag:20481）、RULE-d5f661567cc1（<module>, rag:74278）、RULE-e2b9a18ee598
  （STATEMENT_TERMINATORS, ra:4261）、RULE-ee56c630c4f5（self.RETURN_INSTRUCTIONS, cfg_builder:266）。
- **3 条 neg_missing→guard_only**（开放内部降级）：RULE-00f0d5ffaaff（GET_LEN, agv2:21495）、
  RULE-1e003061d4c8（LOAD_DEREF, agv2:1103）、RULE-b620fe7fb512（LOAD_CLASSDEREF, agv2:1103）。
- **26 条仍为 neg_missing**：清单见 sn_flips_enriched.md（如 _store_ops@rag:12365、
  STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF@agv2:920、RETURN_VALUE@agv2:1877、
  Dict/Name/Attribute/Tuple/List/Set@code_generator 等）。
- 处置闭合：47 neg_missing = 18 proved + 3 guard_only + 26 余留。

**精确读法**：--structural-negative（rule_proof_check.py L1123-1150）在 verdict 阶段引入
「negative=None 时，取 pos_ev 非 None 且 anchor 相同的异 pyc 负见证（same_anchor_diff_pyc）」。
采用它 ⇒ 裁决三从「必须显式负见证」放宽为「同锚异 pyc 结构性负见证」，proved 126→144。
**是否采纳属裁决决策**（父会话）：采纳则 G4 ready 基线升至 144，26 条余留仍开放。

---

## 交付物 4：工具路径 15 条证据排除 Dossier

见 **dossier_15.md**：15 条规则清单（含源码谓词位置）+ 四重证据链
（E1 静态 import 封闭 / E2 core 引用封闭 / E3 探针 0 进入 / E4 v8_b1 0 谓词求值）+ 处置建议。

---

## 方法附注（精度修正与陷阱）

1. **anchor_contexts 的 name 级外层函数定位有缺陷**：同名嵌套 def 会误挂。本轮以 AST 包含关系
   重算全部 50 条，修正 2 条：PRINT_EXPR@11556 → `_generate_if_ast@10211`（原挂
   get_predecessor_instructions@10741，该嵌套 def 在 11556 前已结束）；_CHECK_OPS_r08b@41716 →
   `_generate_try@40468`（原挂 _v126_in_subtree@41489）。
2. **探针键从 (file, co_name) 改为 (file, co_firstlineno, co_name)**：消除同名 def 聚合
   （如 get_predecessor_instructions 在 agv2 有 3 处定义）。修正后 25 条外层函数 0 进入 /
   25 条至少运行一次；65 条锚点 0 命中；失败集与 v8_b1 完全一致（m06/m08 legacy_v2）。
3. **包含式守卫走查的盲区**：前置 early-return 不在包含链上（如 _parse_comprehension_from_code
   的 L3251-3252 主路径提前返回），对 NEVER 类函数需读源码 def→调用点段补证（已补）。
4. **当前树漂移与 v8_b1 无关**：v8_b1 零漂移；当前 HEAD 相对 universe_v6 有 197/282 规则文本漂移
   （agv2/rag/region_analyzer 三文件），阶段二重扫时才相关。
5. **输入污染已隔离**：e1be7895 改过 jspace 并重写 x01/x04 pyc——本轮全部在 shadow env 用
   edc1ab08 输入复算，不受影响；但若父会话在当前树上直接重跑，必须同样隔离。

## 产出物清单（row4_noocc\）

| 文件 | 内容 |
|---|---|
| classification_65.json / .md | 65 条逐锚点分类（a/b/c + 守卫链 + 行动） |
| dossier_15.md | 工具路径 15 条证据排除 dossier |
| sn_flips_enriched.md | 裁决三 SN 翻转明细（18/3/26） |
| proof_records_v8_b1_sn.json / manifest_v8_b1_sn.json | SN 复算原始输出 |
| probe_results.json | 131 pyc × 双管道运行时探针（def 行消歧） |
| guard_paths.json / .txt | 50 条守卫链与调用点清单 |
| unmapped_499_report.json | 499 镜像验证 |
| sn_compare.py / sn_compare.json | SN 内部一致性比对 |
| v8b1_env\ | edc1ab08 shadow env（含恢复的 jspace 与重建 pyc） |
| 其余 *.py | 诊断脚本（anchor_context/callgraph_live/extract_noocc/rebuild_old_pycs 等） |

## 阶段二建议（供父会话裁决）

1. **分母裁决**：排除 (a) 15（宇宙归类错误）+ (b) 19（死码/管道死码）后，G4 分母 282→248；
   (c) 31 条以「扩充 judgment_space 补形态」推进。
2. **裁决三采纳决策**：采纳 SN ⇒ proved 126→144；26 条余留 neg_missing 需补异 pyc 负见证或
   采纳结构性负见证语义。
3. **499 处置**：无需动作——精确镜像 universe_v6 排除组，非新增未映射谓词。
4. **死分支顺带修复项**：PREP_RERAISE_STAR@23481 与相邻 CHECK_EG_MATCH@23476 遮蔽死分支
   （若欲支持 except*，需将两 opcode 纳入 L23446 集合）。
5. **重扫前提**：当前树 197/282 漂移 + jspace/x01/x04 污染 ⇒ 阶段二任何重扫必须先固化
   输入（建议沿用 shadow env 方法）。
