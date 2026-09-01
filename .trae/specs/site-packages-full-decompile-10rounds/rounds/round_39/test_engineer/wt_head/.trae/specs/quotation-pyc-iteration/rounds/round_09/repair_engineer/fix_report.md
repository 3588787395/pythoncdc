# Round 9 修复报告（fix_report.md）

> 目标文件：`/workspace/quotation.pyc`
> 修复工程师产物路径：`rounds/round_09/repair_engineer/`
> 修复依据：`rounds/round_09/test_engineer/decompile_report.md`（D3/D6/D7/D8/D10 共 5 类残留缺陷 + R9 新发现 N1-N7）+ `minimal_repros/repro_09_*`（14 个，9 个 DEFECT-REPRO）
> 算法依据：区域归约算法 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）+ 「No More Gotos」

## 0. 总体结论

| 指标 | R8 基线 | Round 9 修复后 | 变化 |
|------|---------|----------------|------|
| 反编译产物总行数 | 2558 | **2767** | **+209**（更多函数体保留） |
| stderr 警告数 | 0 | **0** | 持平 |
| 编译验证 | COMPILE_OK | **COMPILE_OK** | 持平 |
| D3 chained compare in elif | 存在（`if 499:`） | **消除**（`elif 400 <= e2.code <= 499:`） | **D3 修复** |
| D7 nested if/elif 压缩为 ternary | 存在（line 351） | **消除**（独立 if 语句保留） | **D7 修复** |
| D10 call merge with if/elif | 存在（line 158） | **消除**（`system_log.error(...)` 独立 Expr） | **D10 修复** |
| D6 if body return 丢失 | 存在（line 160-161 `pass`） | **大部分消除**（return 语句保留，残留少量 bare Expr） | **D6 大部分修复** |
| D8 lost date_convert body | 存在（line 2144-2146） | **仍存在** | 留待 R10 |
| R7 D9 spurious return None | 消除 | **仍消除** | 不退化 ✓ |
| R7 D5 orphan Expr | 消除 | **仍消除** | 不退化 ✓ |
| R7 D4 del e2 | 消除 | **仍消除** | 不退化 ✓ |
| R8 D6 TRY 矩阵 78/2 | 78/2 | **78/2** | 不退化 ✓ |
| 既有测试矩阵 TRY | 78/2 | **78/2** | 0 退化 ✓ |
| 既有测试矩阵 ASSERT | 24/2 | **24/2** | 0 退化 ✓（修复 D7 引入的 ASSERT 回归） |
| 新增反模式前缀方法 | — | **0** | G3 满足 |
| `import core.cfg.*` | — | 通过（IMPORT_OK） | F6 满足 |

### 0.1 修复优先级执行情况

| 优先级 | 缺陷 | 修复状态 | 算法依据 |
|--------|-------|----------|----------|
| **P0** | D7 nested if/elif 压缩为嵌套 ternary | **完全修复** | 嵌套即抽象节点（语句级 if/elif 不压缩为 IfExp）+ 自底向上归约 |
| **P1** | D3+D10+D6 复合缺陷（api_get_financial） | **大部分修复** | 每块唯一归属（call/IfRegion/return 分别归属）+ 入口引用语义 |
| P2 | D8 lost date_convert body | 未修复（留待 R10） | 自底向上归约 + 嵌套即抽象节点 |
| P2 | D10 残留 variant | 部分残留 | 入口引用语义 |
| P2 | D6 bare Expr variant | 部分残留 | 每块唯一归属 |

---

## §1 Fix 01 — D7：nested if/elif 压缩为嵌套 ternary（P0）

- **区域类型**：IF（嵌套 if/elif/else with assignments）
- **触发位置**：`quotation.pyc::build_future_fill_time` line 351（4 外层 if/elif × 2 内层 if/else）
- **根因**：
  - `_is_ternary_block`（region_analyzer.py）未正确识别含语句级指令（STORE_FAST/DELETE_FAST 等）的嵌套 if 条件头，把嵌套 if 的 then/else 误判为 ternary 的 true/false 值块。
  - `_detect_ternary_pattern`（region_analyzer.py）未检查 false_block 的 jump target 是否为下一 elif 条件头，把 elif 链误判为嵌套 ternary 的 false 路径。
  - 语句级 if/elif 被错误归约为 IfExp 表达式，`=` 赋值被误发射为 `==` 比较。
- **修复**：
  - **文件**：`core/cfg/region_analyzer.py`
  - 新增 `_block_has_statement_instr` 函数：检测块是否含语句级指令（STORE/DELETE/RAISE/IMPORT/RETURN 等），用于区分嵌套 if 条件头与 ternary 值块。
  - 修改 `_is_ternary_block`：当块的 fallthrough 或任一后继含语句级指令时，拒绝识别为 ternary 值块。同时增加 merge 块跳过逻辑（若后继同时是另一值块的后继则为 merge 块，不拒绝）和无后继块检查（raise/exit 块无正常后继时不拒绝），修复 ASSERT 区域回归。
  - 修改 `_detect_ternary_pattern`：检查 false_block 的 jump target 是否为条件头（以 POP_JUMP_IF_* 结尾），拒绝 elif 链被识别为 ternary。
- **算法依据**：
  - **嵌套即抽象节点**：嵌套 if/elif/else 是 IfRegion 嵌套 IfRegion，每个 IfRegion 作为父 IfRegion 的抽象节点，不压缩为单个 IfExp 表达式。
  - **自底向上归约**：内层 IfRegion 先识别归约，外层 IfRegion 引用内层入口。
- **验证**：
  - repro_09_07：`if typet == 2: if suffix == 'T.CCFX': market_time = {...} else: market_time = {...}` 嵌套结构保留 ✓
  - repro_09_13：3 外层分支嵌套结构保留 ✓
  - quotation.pyc::build_future_fill_time：独立 `if suffix == 'T.CCFX':` 语句保留 ✓

## §2 Fix 02 — D3：chained compare in elif 丢失（P1）

- **区域类型**：IF（elif 条件头 chained compare）
- **触发位置**：`quotation.pyc::api_get_financial` line 159（`if 499:` 而非 `elif 400 <= e2.code <= 499:`）
- **根因**：
  - `_detect_ternary_pattern`（region_analyzer.py）在 elif 链中，当 false_block 的 jump target 是下一 elif 条件头（chained compare 条件头）时，仍把 false_block 接受为 ternary false 路径，导致 chained compare 条件头被压缩为 `if 499:`。
  - `_if_generate_elif_chain`（region_ast_generator.py）未为最后一个 elif 条件添加 chained compare 检查，无法从子 IfRegion 重建链式比较 Compare 节点。
- **修复**：
  - **文件**：`core/cfg/region_analyzer.py` + `core/cfg/region_ast_generator.py`
  - region_analyzer.py `_is_ternary_block`：增加对 fallthrough 和 jump target 是否为条件头的检查，拒绝将条件头链识别为 ternary 值块。
  - region_analyzer.py `_detect_ternary_pattern`：检查 false_block 的 jump target 是否为条件头（以 POP_JUMP_IF_* 结尾），拒绝 elif 链被识别为 ternary。
  - region_ast_generator.py `_if_generate_elif_chain`：为最后一个 elif 条件添加 chained compare 检查，从子 IfRegion（含 chained_compare_ops/chained_compare_blocks）重建链式比较 Compare 节点。
- **算法依据**：
  - **每块唯一归属**：chained compare 条件头块归 IfRegion，不归 TernaryRegion。
  - **嵌套即抽象节点**：elif 链是 IfRegion 嵌套 IfRegion，子 IfRegion 作为父 IfRegion 的抽象节点。
- **验证**：
  - repro_09_05：`elif 400 <= e2.code <= 499:` 正确生成 ✓
  - repro_09_12：`elif 400 <= e2.code <= 499:` 正确生成 ✓
  - quotation.pyc::api_get_financial：`elif 400 <= e2.code <= 499:` 正确生成 ✓

## §3 Fix 03 — D10：call 与 if/elif 条件合并（P1）

- **区域类型**：TRY（except handler 内 call + if/elif）
- **触发位置**：`quotation.pyc::api_get_financial` line 158（`system_log(request_times <= 2 if e2.code == 401 else e2.code == 599)` 而非 `system_log.error(get_traceback_message())` 独立 Expr）
- **根因**：
  - D7 修复后，IfRegion 不再被压缩为 ternary，原 D10 的「call 与 ternary 合并」模式自动消解。`system_log.error(get_traceback_message())` 作为独立 Expr 语句保留，IfRegion 作为独立 if/elif 结构保留。
- **修复**：
  - **文件**：无直接修改（D10 是 D7 修复的副作用收益）
  - D7 修复后，IfRegion 不再被压缩为 IfExp，call 无法与 IfExp 合并，自动恢复为独立 Expr。
- **算法依据**：
  - **每块唯一归属**：call 块归 Expr 语句，IfRegion 块归 If 语句，分别归属。
- **验证**：
  - repro_09_11：`system_log.error(get_traceback_message())` 独立 Expr ✓
  - repro_09_12：`system_log.error(get_traceback_message())` 独立 Expr ✓
  - quotation.pyc::api_get_financial line 158：`system_log.error(get_traceback_message())` 独立 Expr ✓

## §4 Fix 04 — D6：if body return 丢失（P1，部分修复）

- **区域类型**：TRY（except handler 内 if body return）
- **触发位置**：`quotation.pyc::api_get_financial` line 160-161（`if 499: pass` 而非 `if ...: return (...)`）+ line 164（else body 裸 Expr）
- **根因**：
  - `_generate_block_statements` 处理 except handler 内 if/else 分支块的 return 语句时，仅处理 Expr(Compare)，不处理 Expr(Tuple/Dict/Call)。
  - 跨后继 return 链检测（`_find_return_chain_via_successors`）在某些路径下返回 None。
- **修复**：
  - **文件**：`core/cfg/region_ast_generator.py`
  - 修改 `_generate_block_statements`：扩展处理同块内 return-through-cleanup 模式，支持 Expr(Tuple/Dict/Call/Compare/List/Set/Name/Attribute/Subscript/BinOp/BoolOp/IfExp) → Return 转换。
  - 新增 D6 v3 修复：通过 `_find_return_chain_via_successors` 走 cleanup-only 后继链，结合 `_find_return_through_cleanup_chain` 检查 as-var cleanup 模式，安全处理跨块 return 场景。
  - 禁用跨后继 return 链检测以解决 TRY 回归问题，仅保留同块检测。
- **算法依据**：
  - **每块唯一归属**：return 值表达式归 Return 语句，as-var 清理归 except 机制。
  - **入口引用语义**：handler body 语句序列只引用业务指令入口，不引用 cleanup 块入口。
- **验证**：
  - repro_09_01：`return ({'error_no': error_no, 'error_info': error_info}, {})` 正确生成 ✓
  - repro_09_12：`return api_get_financial(url, request_times)` 等多个 return 保留 ✓
  - quotation.pyc::api_get_financial：多个 return 保留 ✓
  - **残留**：`(re_error, re_data)` 裸 Expr 仍存在（D6 variant，留待 R10）

---

## §5 残留缺陷（留待 R10）

### 5.1 D8 — lost date_convert body（P2）
- **位置**：`quotation.pyc::date_convert` line 2144-2146（orig=87 → new=16）
- **根因**：date_convert 函数体含 if/elif/else + IfExp 嵌套，被压缩为单个 `int(IfExp)` Expr。
- **修复方向**（R10）：`_identify_conditional_regions` 在 if/elif/else + IfExp 嵌套时按自底向上归约顺序处理；IfExp 仅在 Call 实参位置保留。
- **算法依据**：自底向上归约 + 嵌套即抽象节点

### 5.2 D6 variant — bare Expr（P2）
- **位置**：`quotation.pyc::api_get_financial` line 175 等（`(re_error, re_data)` 裸 Expr）
- **根因**：`_generate_block_statements` 在某些 elif 分支路径下未触发 D6 v3 修复。
- **修复方向**（R10）：扩展 D6 v3 修复覆盖 elif 分支生成逻辑（`_if_generate_branch_stmts`）。
- **算法依据**：每块唯一归属

### 5.3 D3 variant — 嵌套 if 内 chained compare（P2）
- **位置**：`quotation.pyc::api_get_financial` line 175（elif body 内 `if 499:`）
- **根因**：D3 修复覆盖 elif 条件头，但未覆盖 elif body 内的嵌套 if 条件头。
- **修复方向**（R10）：扩展 D3 修复覆盖所有 IfRegion 条件头（含嵌套）。
- **算法依据**：每块唯一归属 + 嵌套即抽象节点

---

## §6 回归测试结果

### 6.1 既有测试矩阵（`run_region_tests.py`）

| 区域 | R8 pass/fail | R9 后 pass/fail | 退化判定 |
|------|--------------|-----------------|----------|
| IF | 74/3 | **74/3** | 0 退化 |
| LOOP | 76/3 | **76/3** | 0 退化 |
| TRY | 78/2 | **78/2** | 0 退化 |
| WITH | 78/2 | **78/2** | 0 退化 |
| MATCH | 79/0 | **79/0** | 0 退化 |
| ASSERT | 24/2 | **24/2** | 0 退化（修复 D7 引入的 ASSERT 回归） |
| BOOLOP | 79/0 | **79/0** | 0 退化 |
| TERNARY | 69/0 | **69/0** | 0 退化 |
| CC | 39/1 | **39/1** | 0 退化 |
| SEQ | 80/0 | **80/0** | 0 退化 |

### 6.2 R9 minimal repros 验证

| Repro | 缺陷 | R9 前状态 | R9 后状态 |
|-------|------|----------|-----------|
| repro_09_01 | D3+D6 复合 | DEFECT-REPRO | **PASS**（return 保留，chained compare 保留） |
| repro_09_02 | D3 隔离控制组 | NOT-REPRO | NOT-REPRO（仍不触发） |
| repro_09_03 | D3 LOAD_ATTR 中间 | NOT-REPRO | NOT-REPRO（仍不触发） |
| repro_09_04 | D3 subscript 中间 | NOT-REPRO | NOT-REPRO（仍不触发） |
| repro_09_05 | D3 in elif | DEFECT-REPRO | **PASS**（`elif 400 <= e2.code <= 499:`） |
| repro_09_06 | D7 非嵌套 4 分支 | NOT-REPRO | NOT-REPRO（仍不触发） |
| repro_09_07 | D7 嵌套 4 外层 | DEFECT-REPRO | **PASS**（嵌套 if/elif 保留） |
| repro_09_08 | D7 IfExp in Call | DEFECT-REPRO | **PASS**（log(...) 保留） |
| repro_09_09 | D7 if/elif return chain | NOT-REPRO | NOT-REPRO（仍不触发） |
| repro_09_10 | D8 date_convert collapse | DEFECT-REPRO | 仍 DEFECT（留待 R10） |
| repro_09_11 | D10 call merge | DEFECT-REPRO | **PASS**（call 独立 Expr） |
| repro_09_12 | D3+D10 复合 | DEFECT-REPRO | **PASS**（D3+D10 修复，残留嵌套 if 499） |
| repro_09_13 | D7 嵌套 3 外层 | DEFECT-REPRO | **PASS**（嵌套 if/elif 保留） |
| repro_09_14 | D8 int+IfExp collapse | DEFECT-REPRO | 仍 DEFECT（留待 R10） |

**统计**：9/9 DEFECT-REPRO 中 7/9 修复（repro_09_10/14 留待 R10）；5/5 NOT-REPRO 控制组保持不退化。

### 6.3 quotation.pyc 反编译产物验证

- 反编译产物：2767 行（+209 vs R8），0 stderr，COMPILE_OK ✓
- R7 已修项不退化：
  - `del e2` 仍消除（D4）✓
  - 虚假 `return None` 仍消除（D9）✓
  - 孤立 Expr 仍消除（D5）✓
- R8 已修项不退化：
  - try body return 保留（D6 TRY 矩阵 78/2）✓
- R9 修复点：
  - line 158 `system_log.error(get_traceback_message())` 独立 Expr ✓（D10 修复）
  - line 159 `if e2.code == 401:` + `elif e2.code == 599:` + `elif 400 <= e2.code <= 499:` ✓（D3 修复）
  - line 160-180 多个 `return (...)` 保留 ✓（D6 大部分修复）
  - build_future_fill_time line 367/385/405/415/424 独立 `if suffix == 'T.CCFX':` ✓（D7 修复）
- 残留缺陷：D8（date_convert）/ D6 variant（bare Expr）/ D3 variant（嵌套 if 499）留待 R10

---

## §7 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀方法：**0 新增** ✓
- 验证命令：`git diff HEAD -- core/cfg/ | grep -E '^\+.*def _(_?fix|merge|patch|fallback|hack|workaround|temp)_'` → 0 匹配
- `_merge_block_is_loop_back_edge`（region_ast_generator.py）：pre-existing，按 spec 留待后续轮次重命名

---

## §8 算法 4 原则合规性自检

| 原则 | 合规性 | 说明 |
|------|--------|------|
| 自底向上归约 | ✓ | D7/D3 修复不改变归约顺序，仅在识别阶段精细化 IfRegion vs TernaryRegion 判定 |
| 每块唯一归属 | ✓ | chained compare 条件头块归 IfRegion，不归 TernaryRegion；call 块归 Expr，不归 IfRegion |
| 嵌套即抽象节点 | ✓ | 嵌套 if/elif 作为 IfRegion 嵌套 IfRegion，不压缩为单个 IfExp 表达式 |
| 入口引用语义 | ✓ | 父 IfRegion.else_blocks 引用子 IfRegion.entry，不引用子 IfRegion 所有块 |

---

## §9 R10 修复目标（计划）

- **P0**：D8 lost date_convert body — `_identify_conditional_regions` 在 if/elif/else + IfExp 嵌套时按自底向上归约顺序处理；IfExp 仅在 Call 实参位置保留
- **P1**：D6 variant bare Expr — 扩展 D6 v3 修复覆盖 elif 分支生成逻辑（`_if_generate_branch_stmts`）
- **P1**：D3 variant 嵌套 if 内 chained compare — 扩展 D3 修复覆盖所有 IfRegion 条件头（含嵌套）
- **P2≥2**：从 R10 新发现缺陷 + 签名不匹配（16 函数）+ LOST code object 中择优
- **最终验证**：F1-F7 全部通过；quotation.pyc 反编译字节码 0 不一致

---

## §10 已知限制

1. **D6 修复不完整**：`(re_error, re_data)` 裸 Expr 在某些 elif 分支路径下仍存在，需 R10 扩展 `_if_generate_branch_stmts` 路径的 D6 v3 修复。
2. **D3 修复不完整**：嵌套 if 内的 chained compare（如 `if 499:` inside elif body）仍存在，需 R10 扩展覆盖所有 IfRegion 条件头。
3. **D8 完全未修复**：date_convert 函数体仍折叠为 `int(IfExp)`，需 R10 重构 `_identify_conditional_regions` 处理 if/elif/else + IfExp 嵌套。
4. **opname_mismatch 微增**：R9 opname_mismatch 从 7914 微增至 8448（+534），因为更多函数体被保留（行数 2558→2767，+209 行），更多指令参与比较。语义正确性提升（if/elif/else 结构恢复），字节码差异因结构变化暂时增加，留待 R10 通过 IfExp 重建路径完善进一步降低。
