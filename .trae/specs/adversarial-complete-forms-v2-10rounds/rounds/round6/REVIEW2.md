# Round 6 · Task 6.3 复核（REVIEW2）
## 修复批次（HEAD `76765985`）注释合规整改复核

- 复核对象：`rr-v2r06: round6 修复批次（任务 6.2）` = HEAD `76765985`（父 `ce19bf05` = 评审批次）
- 对照基准：`rounds/round6/REVIEW.md`（R6-D1..D10，19 个方法打回）
- 复核角色：评审工程师子代理（只读审计 + 独立复跑；零 core 修改 / 零 git add / 零 commit）
- 证据前缀：`r6v6r_*`（`rounds/round6/`）
- 结论域：**仅两态「通过 / 打回」**

---

## §1 逐方法复核结论表（19 行）

判据：I.7 六项模板（①–⑥ / 六项标题）齐全且标号清晰 + 独立可 grep 的 `C 条款：C1——…；C2——…；C3——…` 声明 + **对抗性核对声明真实性**（注释断言 vs 方法体内真实代码）。

### 识别层 `core/cfg/region_analyzer.py`（10）

| 方法 | def 行 | C 条款行 | 六项 | C1/C2/C3 | 真实性核对（对抗性） | 结论 |
|------|-------|---------|------|----------|--------------------|------|
| `_identify_loop_regions` | 4171 | 4275 | ✓ | ✓✓✓ | C3「回边合法性依赖 `dom_analyzer.is_dominator(header, src)`」→ 代码 :4294 实证；C3「`_is_post_merge_sibling_head` 跨区域 entry 反查」→ :2917 定义、:6021/:6427 使用 ✓ | **通过** |
| `_identify_try_except_regions` | 8178 | 8263 | ✓ | ✓✓✓ | C1「`excluded_offsets` 区间包含判定」→ :8423 构造、:8454 `block.start_offset in excluded_offsets` 实证 ✓ | **通过** |
| `_identify_with_regions` | 13275 | 13405 | ✓ | ✓✓✓ | C3「仅以 `exit_block`/`exit_via_jump` 引用而不改归属」→ :13241 赋值、:13308 引用不改所有权 ✓（本方法体 is_dominator/back_edge 计数 = 0） | **通过** |
| `_identify_match_regions` | 13977 | 14067 | ✓ | ✓✓✓ | C1/C3 声明的 subject 前驱回溯 / claimed / B74 撤销均实证（:16448 `_has_match_op`、:1866 `match_case_body_blocks`）；方法本体（13977–14180）内 is_dominator = 0，支配判据仅出现在 `_mr_*` 子方法（各自带 C1/C3 内联声明）✓ | **通过** |
| `_identify_assert_regions` | 16690 | 16838 | ✓ | ✓✓✓ | C1「本方法不依赖支配树/回边」→ 方法体 + 其 8 个 `_*assert*` 助手全区间（16690–17500）is_dominator/back_edge/dom_analyzer 计数 **均 = 0**，断言为真 ✓；`LOAD_ASSERTION_ERROR` :16699 实证 | **通过** |
| `_identify_chained_compare_regions` | 17501 | 17602 | ✓ | ✓✓✓ | C3「claimed 集合（取自 block_to_region）」→ :17563/:17612 `claimed.update(region.blocks)` 实证；`_detect_chained_compare_pattern` :22491 定义、:4441:23668 使用 ✓ | **通过** |
| `_identify_conditional_regions` | 17976 | 18122 | ✓ | ✓✓✓ | C3「`_should_skip_block_for_if_region` 以 LoopRegion 身份排除」→ :17644 定义、:18313 使用；「`_get_enclosing_structural_boundary_stop` 回溯外层边界」→ :30890 定义、:19312 使用 ✓ | **通过** |
| `_identify_ternary_regions` | 22572 | 22706 | ✓ | ✓✓✓ | C3「`existing.can_be_ternary_header` 多态守卫」→ 各 Region 类覆写 :332/:485/:670/:1007/:1038/:1102/:1193；`_ternary_block_sets`/`_region_overlaps_with_ternary` :1506–1569 实证 ✓ | **通过** |
| `_identify_boolop_regions` | 25714 | 25881 | ✓ | ✓✓✓ | C3「`loop_condition_blocks`/`match_case_body_blocks` 允许重叠为显式认领例外」→ :25903 构造、:25984 成员判定、:1866 match 集合；「Step5 残链超越替换」:25759 实证 ✓ | **通过** |
| `_identify_sequence_regions` | 30943 | 31035 | ✓ | ✓✓✓ | C1「不构造跨块 Sequence」→ 每块 entry=block、:31043 `block in self.block_to_region` 跳过；C3「仅读 block_to_region，无跨层窥视」→ 方法体无非局部读写（唯一 `back_edge` 命中 :31701 属其后独立的 `_annotate_*` 助手）✓ | **通过** |

### 生成层 `core/cfg/region_ast_generator.py`（9）

| 方法 | def 行 | C 条款行 | ①–⑥ | C1/C2/C3 | 真实性核对（对抗性） | 结论 |
|------|-------|---------|------|----------|--------------------|------|
| `_generate_assert` | 4330 | 4357 | ✓ | ✓✓✓ | C1「前导段唯一移交去重」→ `_collect_assert_prefix_stmts` :535 定义/:4452 调用、`_assert_prefix_emitted_blocks` :423/:553 实证；C1「None 方向经 `_invert_assert_none_check_direction`」→ :4636 定义/:4466 调用 ✓ | **通过** |
| `_generate_loop` | 5089 | 5119 | ✓ | ✓✓✓ | ③④「`_current_loop`/`_loop_depth`/`generated_*`」→ :379 `_current_loop` 定义、:3443+ 使用；`is_yield_from_loop` 分支实证 ✓ | **通过** |
| `_generate_if` | 14416 | 14442 | ✓ | ✓✓✓ | ②③「elif 链先走 `_if_generate_full_elif_chain`」→ :15245 定义/:14477 调用；「R36 跳过 / R59 不跳过 / `guard_clause_prefix_end` 例外」→ :14494–14508 三分支实证；未命中走 `_if_generate_normal` :20774 ✓ | **通过** |
| `_generate_value_context_chain_compare_assign` | 14856 | 14880 | ✓ | ✓✓✓ | ③「ops≥2 ∧ `SHORT_CIRCUIT_JUMP_OPS` ∧ merge STORE」→ 方法体内三守卫实证；未命中交回 ✓ | **通过** |
| `_generate_match` | 35636 | 35659 | ✓ | ✓✓✓ | C3「字面量/通配/case None 守卫」→ `_has_match_op`、`is_wildcard_match`/`is_literal_match`、`POP_JUMP_IF_NOT_NONE`（:35559–35578 区）实证 ✓ | **通过** |
| `_generate_boolop`（重入包装） | 39319 | 39341 | ✓ | ✓✓✓ | ③⑤「`_generating_regions` 登记 / `prefix_emitted_upto` 快照撤销 / finally discard」→ :375、:413 定义、:4962–5006 区实证 ✓ | **通过** |
| `_generate_boolop_impl` | 39365 | 39391 | ✓ | ✓✓✓ | C2/C3「R78 用 `_downstream_region_entry` 认领下游」→ :51419 定义、:39885/:39993/:40103 调用；`find_enclosing_parent` 条件上下文判定实证 ✓ | **通过** |
| `_generate_ternary` | 41808 | 41836 | ✓ | ✓✓✓ | ③④「容器构造 / while_cond / elif 重叠」→ `_ternary_nested_in_container_construction` :41416、`_generate_container_construction_region` :41468、:41926 调用实证 ✓ | **通过** |
| `_generate_basic_region` | 51085 | 51110 | ✓ | ✓✓✓ | C1「只读 blocks 同层事实（start_offset/block_role）」；C3「`WITH_EXIT_CLEANUP`/`LOOP_EXIT` 短路」→ :4063 等 BlockRole 实证；逐块交 `_generate_block_statements` ✓ | **通过** |

**独立 AST 复核**（`r6v6r_docstring_check.py` → `r6v6r_docstring_check.json`）：19/19 `items_ok=True`、`has_C_clause=True`、`C1/C2/C3=True`，`ALL_OK=True`。
**§1 结论：通过 19 / 打回 0。**

> 非打回说明：识别方法 docstring 六项标题后保留 I.1 四原则收尾句，**其后**新增独立 `C 条款：` 行——二者并存不冲突（四原则陈述归约不变量，C 条款陈述嵌套无感不变式）。C1「只来自本层块对象结构事实」的**非局部例外**（如 loop 的全函数支配 `is_dominator`）均在 **C3** 显式声明，未出现「空声明 / 照抄模板 / 与代码不符」。

---

## §2 独立零行为变更验证

### 2.1 AST 等价比对（剥离 docstring）
工具：`rounds/round6/r6v6r_ast_equal.py`（`git show HEAD~1:<file>` 解码后 `lstrip('\ufeff')`，剥 Module/FunctionDef/AsyncFunctionDef/ClassDef 首条 docstring 后 `ast.dump` 比对）。

| 文件 | 结果 |
|------|------|
| `core/cfg/region_analyzer.py` | **AST_EQUAL** |
| `core/cfg/region_ast_generator.py` | **AST_EQUAL** |

`ALL_EQUAL=True`。⇒ 修复批次对两文件 **零可执行代码变更**（签名/装饰器/语句全同；+255/-9 与 +70 全部落在 docstring 文本）。原语 `r6v6r_ast_equal.json`。

### 2.2 RV2 抽样（regen + verify）
| pyc | 读数 | 唯一失败单元 | 与基线 |
|-----|------|-------------|--------|
| `site-packages/fly/data/quotation.pyc` | **152/153**（99.35%） | `change_his_to_forward` | 逐位一致 ✓ |
| `site-packages/fly/data/quote_handler.pyc` | **78/79**（98.73%） | `get_kline_local` | 逐位一致 ✓ |

---

## §3 站桩 6 面读数表（vs REVIEW 基线）

驱动 `rounds/round6/r6v6r_station.py`；对照 `rounds/round6/r6v6r_compare_regress.py` → `r6v6r_station_regress_compare.json`（基线 = REVIEW 轮 `r6v6_*` 证据）。

| 面 | REVIEW 基线 | 本轮读数 | same | improved | **WORSE** |
|----|-----------|---------|------|----------|-----------|
| round2face | 234/251 | **234/251** | 45 | 0 | **0** |
| probe42 | 176/196 | **176/196** | 42 | 0 | **0** |
| round1face | 417/423 | **417/423** | 24 | 0 | **0** |
| residual | 417/446 | **417/446** | 72 | 0 | **0** |
| oldface | 664/692 | **664/692** | 59 | 0 | **0** |
| quotation | 152/153 | **152/153** | — | 0 | **0** |

**六面 WORSE 合计 = 0**；逐文件（含失败单元集合）与 REVIEW **完全 same**（improved=0，无漂移）。

---

## §4 合规审计复跑表（基准 HEAD `76765985`）

| # | 项 | 结果 |
|---|----|------|
| 1 | `core/` 变更范围 | 仅 `region_analyzer.py`（+70）/`region_ast_generator.py`（+255/-9），均 **docstring**（由 §2.1 AST_EQUAL 佐证）；`git diff --stat HEAD -- core/` 工作树 = 空 |
| 2 | I.4 黑名单五项 | **无新增**（AST_EQUAL ⇒ 无新增 start_offset 魔法阈值 / 跨层 `entry in blocks` / self 跨方法状态 / 硬编码深度上限） |
| 3 | I.5 七前缀方法 | **无新增**；存量 3：`region_ast_generator.py:20231 _merge_block_is_then_exclusive`、`:41403 _merge_block_is_loop_back_edge`（谓词）、`core/control_flow.py:720 _merge_redundant_blocks`（本轮未触碰） |
| 4 | BOM 单头 | `region_analyzer.py` head3=`efbbbf` count=1；`region_ast_generator.py` head3=`efbbbf` count=1 ✓ |
| 5 | 插桩残留新增 | **无**（AST_EQUAL） |
| 6 | 既有 `rounds/round5/`、`test_repros/round6/` tracked `M` | **无** |
| 7 | 手改 `*OK.py` | **无**；站桩 regen 触发 `test_repros/round2/` 7 个 `*OK.py` 为 `M`，复核结束已按纪律 `git checkout -- test_repros/round2/` 还原（现 `git status` 无 `M`） |

**合规审计新增违反数 = 0。**

---

## §5 变体攻击记录（声明 vs 代码边界核对）

| # | 攻击假定 | 证伪动作 | 结果 |
|---|---------|---------|------|
| A1 | loop C1「判据只来自本层块」是否假 | 搜索 loop 方法体是否读全函数支配：:4294 `is_dominator(header, src)` | 命中——但 **C3 已显式声明**该非局部依赖；C1/C3 分工诚实，**无矛盾** |
| A2 | assert C1「不依赖支配树/回边」是否空声明 | 统计 16690–17500 区间 is_dominator/back_edge/dom_analyzer 计数 | 全 = 0，断言为真，**非空声明** |
| A3 | try_except C1「excluded_offsets 区间包含」是否虚构 | 查 :8423 构造 + :8454 成员判定 | 实证存在，**真** |
| A4 | ternary C3「`can_be_ternary_header` 多态守卫」是否单点硬编码 | 查该名是否有多个类覆写 | :332/:485/:670/:1007/:1038/:1102/:1193 多态覆写，**真** |
| A5 | boolop C3「重叠认领例外」是否泛泛而谈 | 查 `loop_condition_blocks`/`match_case_body_blocks` 与成员判定 | :25903/:25984/:1866 实证，**真** |
| A6 | sequence C1「不构造跨块 Sequence」是否被违背 | 查方法体是否跨块聚合 | entry=单块、:31043 仅 block_to_region 跳过，**真** |

6/6 攻击点均**未产生反例**。

---

## §6 终审结论

**放行（通过）。**

- 19/19 方法：I.7 六项齐全、C 条款独立可 grep（C1/C2/C3 全在），**通过 19 / 打回 0**。
- 对抗性核对：6 个跨族攻击点全过；所有 C 条款引用机制均在代码中实证存在且用于所述位置，**未发现空话/照抄/与代码不符**。
- 零行为变更：两文件 **AST_EQUAL**；RV2 quotation 152/153、quote_handler 78/79 逐位一致。
- 站桩 6 面 **WORSE=0**（全 same）。
- 合规审计**新增违反 = 0**；round2 regen 副作用已还原。
- **无破口、无回退、无需整改。**

### 交付物
| 交付物 | 路径 |
|--------|------|
| 本报告 | `rounds/round6/REVIEW2.md` |
| 站桩驱动（`r6v6r_`） | `rounds/round6/r6v6r_station.py` |
| 回归对照脚本 | `rounds/round6/r6v6r_compare_regress.py` |
| 对照结果 | `rounds/round6/r6v6r_station_regress_compare.json` |
| AST 等价脚本/结果 | `rounds/round6/r6v6r_ast_equal.py` / `.json` |
| docstring 合规脚本/结果 | `rounds/round6/r6v6r_docstring_check.py` / `.json` |
| 站桩证据 JSON | `r6v6r_regress_round2face.json`、`r6v6r_regress_probe42.json`、`r6v6r_full_round1face.json`、`r6v6r_full_residual_a/b.json`、`r6v6r_full_oldface_a/b.json`、`r6v6r_quotation.json` |

**未触碰**：`rounds/round5/` 与 `round6/` 既有文件、REVIEW 证据 `r6v6_*`、FIX 证据 `r6v6fixa_*`/`r6v6fixb_*`、任何 `*OK.py`、`core/`。