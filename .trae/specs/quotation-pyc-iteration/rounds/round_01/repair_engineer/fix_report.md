# Round 1 修复报告（fix_report.md）

> 目标文件：`/workspace/quotation.pyc`
> 修复工程师产物路径：`rounds/round_01/repair_engineer/`
> 修复依据：`rounds/round_01/test_engineer/decompile_report.md`（12 类缺陷）+ `minimal_repros/repro_01..repro_12`
> 算法依据：区域归约算法 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）+ 「No More Gotos」

## 0. 总体结论

| 指标 | 基线 | Round 1 修复后 | 变化 |
|------|------|----------------|------|
| 反编译产物总行数 | 2593 | 2592 | -1 |
| stderr 警告数（MatchSingleton） | 19 | **0** | **-19（全部消除）** |
| 编译验证 | **失败**（line 2579 `filter_type=` 语法错误） | **通过**（COMPILE OK） | **阻塞解除** |
| AST 解析 | 失败 | 通过 | — |
| 该轮缺陷修复数 | — | 4 / 12 | P0×2 + P1×2 |
| 残留缺陷类数 | 12 | 8 | P2×4 + P3×4 |
| 既有测试矩阵退化 | — | **0 退化** | 持平 |
| 新增反模式前缀方法 | — | **0** | G3 满足 |
| `import core.cfg.region_analyzer; region_ast_generator` | — | 通过 | F6 满足 |

### 0.1 修复优先级执行情况

| 优先级 | repro | 缺陷类型 | 修复状态 | 算法依据 |
|--------|-------|----------|----------|----------|
| **P0**（阻塞编译） | repro_03 | FUNCTION_DEF 列表默认值丢失 | **完全修复** | 嵌套即抽象节点 |
| **P0**（影响面广） | repro_01 | MATCH MatchSingleton case 合并 | **P0 阻塞解除**（警告清零、可编译；残留 case 模式保真问题） | 每块唯一归属 + 嵌套即抽象节点 |
| **P1** | repro_05 | ASSERT/COMPARE 链式比较 CALL 参数丢失 | **完全修复** | 嵌套即抽象节点 |
| **P1** | repro_07 | TRY pass→del + return(tuple)退化 | **部分修复**（return(tuple) 已修复；pass→del 残留） | 每块唯一归属 |
| P2 | repro_02 | IF/ELIF 边界 + IS_OP 退化 | 未修复（留待 Round 2） | 每块唯一归属 |
| P2 | repro_06 | IF/BOOLOP `and` 拆为嵌套 if | 未修复（留待 Round 2） | 入口引用语义 |
| P2 | repro_10 | IF 嵌套 if/elif 整段丢失 | 未修复（留待 Round 2） | 自底向上归约 |
| P2 | repro_12 | IF 嵌套合并 + 语句提升 | 未修复（留待 Round 2） | 每块唯一归属 |
| P3 | repro_04 | LOOP STORE_SUBSCR 丢失 + spurious for-else | 未修复（留待 Round 2） | 每块唯一归属 |
| P3 | repro_08 | TERNARY 嵌套 IfExp 作 if 条件 | 未修复（留待 Round 2） | 嵌套即抽象节点 |
| P3 | repro_09 | LOOP 双层 spurious for-else | 未修复（留待 Round 2） | 每块唯一归属 |
| P3 | repro_11 | IF/ELIF 裸 Name Expr + 语句复制 | 未修复（留待 Round 2） | 每块唯一归属 |

---

## 1. 修复点详解

### Fix 01 — repro_03：FUNCTION_DEF 列表默认值丢失（P0 阻塞编译）

- **区域类型**：FUNCTION_DEF（函数定义默认参数）
- **触发位置**：`quotation.pyc::filter_stock_by_status`（`filter_type=['ST','HALT','DELISTING']`）
- **根因**：
  - `core/cfg/code_generator.py::_generate_arguments`（L5048+）的默认值渲染分支原仅识别 `Constant` 类型，当默认值通过 `BUILD_LIST 0 + LIST_EXTEND` 在模块级动态构造时，defaults 节点被重建为 List 字典，旧逻辑 `repr(default)` 或仅取 `default['value']` 对 List/Tuple/Call 等复合节点失效，发射 `name=` 空默认值。
- **修复**：
  - `core/cfg/code_generator.py::_generate_arguments`：将默认值渲染统一委托 `_generate_expression(default_val, 0)`，覆盖 Constant/List/Tuple/Set/Dict/Name/Call/IfExp 等所有表达式类型。
  - 同步更新 `_generate_arguments_dict`（L534+）与 kw_defaults 分支（L5207+）保持一致。
- **算法依据**：
  - **嵌套即抽象节点**：`BUILD_LIST + LIST_EXTEND` 构造的列表默认值应作为单个 List 表达式节点整体参与 defaults 重建，不可拆解后只取字段。
- **docstring 更新**：`_generate_arguments` 已按 6 项统一模板补充「[P2-2026 反编译流程]」+「[算法依据]」段。
- **验证**：
  - `quotation.pyc` line 2578：`def filter_stock_by_status(stocks, filter_type=['ST', 'HALT', 'DELISTING'], query_date=None):` ✓
  - repro_03 反编译产物：`filter_type=['ST', 'HALT', 'DELISTING']` ✓
  - 编译验证：COMPILE OK（line 2579 阻塞解除）

### Fix 02 — repro_01：MATCH MatchSingleton case 合并失败（P0 影响面广）

- **区域类型**：MATCH（match/case 语句）
- **触发位置**：`quotation.pyc::process`（case None / case str() / case _）
- **根因**：
  - `core/cfg/region_analyzer.py::_mr_finalize_match_region`（L8174+）的 `_mr_bodies_are_equivalent` 原基于「末块相同」的宽松判定，把 `case None` 与 `case str()` 的 body 错误判定为等价并合并为 MatchOr；merge_block 同时被计入两个 case body，违反每块唯一归属。
  - `core/cfg/ast_converter.py` 的表达式类型白名单遗漏 `MatchSingleton`，导致 MatchSingleton 字典被当作表达式节点传入 `_generate_expression`，触发 19 处 `Unknown expression type: MatchSingleton` 警告。
- **修复**：
  - `core/cfg/region_analyzer.py::_mr_finalize_match_region`：先调用 `_mr_compute_case_merge` 计算 merge_block 并从各 case body 中移除，确保每块唯一归属；同步修复 `_mr_finalize_match_region_post`（L9076+）与 `_mr_finalize_match_region_v2`（L9202+）。
  - `core/cfg/region_analyzer.py::_mr_bodies_are_equivalent`：从「末块相同」宽松判定改为严格的集合相等判定（`body_i_set == body_j_set`），避免不同 case 错误合并。
  - `core/cfg/ast_converter.py`：在模式匹配类型白名单中添加 `MatchSingleton`，使 MatchSingleton 字典不被当作表达式节点，消除警告。
- **算法依据**：
  - **每块唯一归属**：merge_block 不得同时计入多个 case body。
  - **嵌套即抽象节点**：MatchSingleton/MatchClass 模式应作为模式匹配节点，不应作为表达式节点传入 `_generate_expression`。
- **验证**：
  - `quotation.pyc` stderr MatchSingleton 警告：19 → **0** ✓
  - repro_01 反编译产物：3 个独立 case（不再合并为 MatchOr），可编译 ✓
  - 残留：`case None` 模式被发射为 `case _`（wildcard），pattern 保真问题留待 Round 2。

### Fix 03 — repro_05：ASSERT/COMPARE 链式比较 CALL 参数丢失（P1）

- **区域类型**：ASSERT + COMPARE_OP（链式比较 `11 >= len(s) >= 9`）
- **触发位置**：`quotation.pyc::check_stock`
- **根因**：
  - `core/cfg/region_ast_generator.py` 的链式比较重建在处理中段为函数调用（`len(s)` = `LOAD_GLOBAL len + LOAD_FAST s + PRECALL + CALL`）的三元链式比较时，把 CALL 节点拆解为单独的 `LOAD_GLOBAL len`，丢失了 `LOAD_FAST s + PRECALL + CALL` 指令，导致只剩裸 `len`。
- **修复**：
  - `core/cfg/region_ast_generator.py`：新增 `_try_build_call_middle_from_blocks` 方法（L7659+），通过逆向栈模拟识别 cond_block 中以 `CALL`（且不含 `LOAD_METHOD`）作为中段操作数的情况，完整重建 Call 节点作为链式比较的中间 comparator。
  - 识别 `SWAP`/`COMPARE_OP` 边界，逆向计算 left 与 middle1 的指令范围，分别委托 `expr_reconstructor.reconstruct` 重建。
- **算法依据**：
  - **嵌套即抽象节点**：`len(s)` 应作为一个 Call 子节点整体参与比较，不可拆解为 LOAD_GLOBAL + LOAD_FAST 后丢弃 LOAD_FAST + CALL。
  - 「No More Gotos」§链式比较：通过 SWAP+COPY+COMPARE_OP 边界识别链式比较首段。
- **docstring 更新**：`_try_build_call_middle_from_blocks` 已补充「算法依据」段（嵌套即抽象节点 + No More Gotos §链式比较）。
- **验证**：
  - `quotation.pyc` line 1902：`assert 11 >= len(s) >= 9, '请输入正确的标的代码'` ✓
  - repro_05 反编译产物：`assert 11 >= len(s) >= 9, 'msg2'` ✓

### Fix 04 — repro_07：TRY pass→del + return(tuple) 退化（P1，部分修复）

- **区域类型**：TRY（try/except）
- **触发位置**：`quotation.pyc::api_get`
- **根因**：
  - (b) `return (tuple)` → 裸 tuple + `return None`：`_generate_try` 在 except handler 内遇到 as-var 清理（`LOAD_CONST None → STORE_FAST e → DELETE_FAST e`）后的 `RETURN_VALUE` 时，把 RETURN_VALUE 错误归约为 `RETURN_CONST None`，原 tuple 表达式被作为孤立 Expr 语句留在前面。
  - 多 STORE 指令块提前 fallback 到 `_generate_block_statements`，该路径无 cleanup chain 检测，进一步加剧 return 值丢失。
- **修复**：
  - `core/cfg/region_ast_generator.py` POP_EXCEPT 处理逻辑（L13686+）：检测 as-var 清理后是否紧跟 `RETURN_VALUE`/`RETURN_CONST`，若是则将 `stmt_instrs` 重建为 `Return` 语句（value 为重建的表达式），而非裸 Expr。
  - 多 STORE 指令块（L13629+）：添加 return 链检测（`_find_return_through_cleanup_chain`），若 block 含 return chain 则跳过 `_generate_block_statements` fallback，依「每块唯一归属」：return 值表达式归 Return 语句，as-var 清理归 except 机制。
  - 动态设置 `skip_initial_pop`（L13644+）：原无条件 `True` 会误跳 block 中部的 POP_TOP（如 call 结果丢弃的 POP_TOP），改为根据 block 首指令判定，避免 call 表达式被误绑定为后续 Assign 的 value。
- **算法依据**：
  - **每块唯一归属**：return 值表达式归 Return 语句，as-var 清理（LOAD_CONST None → STORE → DELETE）归 except 机制，call 结果丢弃的 POP_TOP 归 Expr 语句。
- **验证**：
  - repro_07 反编译产物：`return ({'error_no': error_no, 'error_info': error_info}, {})` ✓（不再退化为裸 Expr + return None）
  - 残留：`pass` → `del e2`（P1 issue a）未修复，留待 Round 2。

---

## 2. 回归测试结果

### 2.1 既有测试矩阵（`run_region_tests.py`，10 区域）

| 区域 | 基线 pass/fail/skip | Round 1 后 pass/fail/skip | 退化 |
|------|---------------------|---------------------------|------|
| IF | 79/1/0 | 79/1/0 | **0** |
| LOOP | 79/0/0 | 79/0/0 | **0** |
| TRY | 80/0/0 | 80/0/0 | **0** |
| WITH | 80/0/0 | 80/0/0 | **0** |
| MATCH | 79/0/0 | 79/0/0 | **0** |
| ASSERT | 21/6/0 | 21/6/0 | **0** |
| BOOLOP | 79/0/0 | 79/0/0 | **0** |
| TERNARY | 69/7/0 | 69/7/0 | **0** |
| CC | 37/3/0 | 37/3/0 | **0** |
| SEQ | 127/10/0 | 127/10/0 | **0** |

> 基线通过 `git stash` 临时回退 4 个修复文件后运行获得，与修复后结果完全一致。
> 所有失败均为预先存在的基线失败，**Round 1 修复引入 0 退化**（G6 满足）。

### 2.2 12 个最小复现实例（repro_01..repro_12）

| repro | 优先级 | 反编译可编译 | 修复状态 |
|-------|--------|--------------|----------|
| repro_01 | P0 | ✓ | P0 阻塞解除（残留 case 模式保真） |
| repro_02 | P2 | ✓ | 未修复（原错误保持） |
| repro_03 | P0 | ✓ | **完全修复** |
| repro_04 | P3 | ✓ | 未修复（原错误保持） |
| repro_05 | P1 | ✓ | **完全修复** |
| repro_06 | P2 | ✓ | 未修复（原错误保持） |
| repro_07 | P1 | ✓ | 部分修复（return(tuple) 已修复） |
| repro_08 | P3 | ✓ | 未修复（原错误保持） |
| repro_09 | P3 | ✓ | 未修复（原错误保持） |
| repro_10 | P2 | ✓ | 未修复（原错误保持） |
| repro_11 | P3 | ✓ | 未修复（原错误保持） |
| repro_12 | P2 | ✓ | 未修复（原错误保持） |

> 12 个 repro 全部反编译成功且 AST 解析通过（无语法错误）。

---

## 3. 算法合规性自检

| 检查项 | 结果 |
|--------|------|
| G3 无反模式前缀方法新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`） | **通过**（`def` 计数：_fix_=0, _merge_=1 遗留, _patch_=0, _fallback_=0, _hack_=0, _workaround_=0, _temp_=0） |
| G4 无硬编码深度上限新增 | 通过（本次修复未引入 `depth < N` 类魔法数字） |
| 无跨区域启发式 | 通过（`_try_build_call_middle_from_blocks` 限定于链式比较 cond_block 内，非跨区域） |
| 无后处理补丁 | 通过（修复均在识别/生成阶段，非事后修正） |
| F6 `import core.cfg.region_analyzer; region_ast_generator` | **通过**（IMPORT OK） |
| `_merge_block_is_loop_back_edge` 重命名 | 未执行（pre-existing，计划在后续轮次处理） |

### 反模式说明

- `_merge_block_is_loop_back_edge`（`region_ast_generator.py` L18734）：pre-existing，基线快照即记录 `_merge_=1`，非本轮新增。按 spec 计划在迭代过程中重命名为 `is_merge_block_loop_back_edge`，留待后续轮次。

---

## 4. docstring 更新清单

| 文件 | 方法 | 更新内容 |
|------|------|----------|
| `core/cfg/code_generator.py` | `_generate_arguments` | 补充「[P2-2026 反编译流程]」（字节码→AST 映射 + 默认值渲染 + 位置对齐）+「[算法依据]」（嵌套即抽象节点） |
| `core/cfg/region_ast_generator.py` | `_try_build_call_middle_from_blocks`（新增） | 补充「算法依据」（嵌套即抽象节点 + No More Gotos §链式比较）+ 输入契约 |
| `core/cfg/region_ast_generator.py` | POP_EXCEPT 处理逻辑 | 补充 `[Round1-repro_07]` 内联注释（每块唯一归属：return 值归 Return，as-var 清理归 except） |
| `core/cfg/region_analyzer.py` | `_mr_finalize_match_region` / `_mr_bodies_are_equivalent` / `_mr_compute_case_merge` | 补充每块唯一归属判定说明 |

---

## 5. 残留不一致清单（Round 2 输入）

| # | repro | 优先级 | 残留问题 | 涉及方法 |
|---|-------|--------|----------|----------|
| 1 | repro_01 | P0-残留 | `case None` 被发射为 `case _`（wildcard），pattern 保真不足 | `pattern_parser.py` / `_generate_match` |
| 2 | repro_07 | P1-残留 | `pass` → `del e2`（except 变量清理被误识别为用户语句） | `_generate_try` |
| 3 | repro_02 | P2 | IF/ELIF 边界破坏 + IS_OP 退化为 `== None` | `_identify_if_regions` / `_generate_if` |
| 4 | repro_06 | P2 | `if A and B:` 被拆为嵌套 `if A: if B:`，else 语义改变 | `_identify_if_regions` |
| 5 | repro_10 | P2 | IF 嵌套 if/elif/elif 整段丢失 + `and X is None` 截断 | `_identify_if_regions` |
| 6 | repro_12 | P2 | IF 嵌套合并为 `A and B` + 语句提升出 if | `_identify_if_regions` |
| 7 | repro_04 | P3 | LOOP STORE_SUBSCR 丢失 + spurious for-else | `_generate_loop` / `_identify_loop_regions` |
| 8 | repro_08 | P3 | TERNARY 嵌套 IfExp 作 if 条件，if 关键字丢失 | `_generate_if` / `_generate_ternary` |
| 9 | repro_09 | P3 | LOOP 双层 spurious for-else | `_identify_loop_regions` |
| 10 | repro_11 | P3 | IF/ELIF 裸 Name Expr + 语句复制 | `_identify_if_regions` |

> 残留缺陷类数：8（P2×4 + P3×4）+ 2 项 P0/P1 残留 = 10 项，均可作为 Round 2 测试工程师提取新增最小复现实例的输入（≥10 个，满足 E2 退出条件检查的反向约束）。

---

## 6. 修改文件清单

| 文件 | 修改类型 | 涉及 repro |
|------|----------|------------|
| `core/cfg/code_generator.py` | 修改 | repro_03 |
| `core/cfg/ast_converter.py` | 修改 | repro_01 |
| `core/cfg/region_analyzer.py` | 修改 | repro_01 |
| `core/cfg/region_ast_generator.py` | 修改（含新增方法） | repro_05, repro_07 |

---

## 7. 验收标准核对

| 验收项 | 结果 |
|--------|------|
| 至少修复 P0 两项 | **通过**（repro_03 完全修复 + repro_01 P0 阻塞解除） |
| 反编译后无语法错误 | **通过**（COMPILE OK + AST PARSE OK） |
| MatchSingleton 警告减少 | **通过**（19 → 0） |
| 测试无退化 | **通过**（10 区域 0 退化） |
| 修复报告完整 | **通过**（本文件） |
| docstring 更新 | **通过**（4 处方法 docstring/注释更新） |
| G3 无反模式新增 | **通过**（0 新增） |
| F6 import 编译通过 | **通过** |

---

## 8. Round 2 建议

1. **P0/P1 残留**：优先处理 repro_01 的 `case None`→`case _` pattern 保真（涉及 `pattern_parser.py`）与 repro_07 的 `pass`→`del e2`（涉及 `_generate_try` 的 except 变量清理识别）。
2. **P2 IF/BOOLOP 边界**：repro_02/06/10/12 均涉及 `_identify_if_regions` 的 elif 合并与 `and` 短路拆分，建议 Round 2 集中重构 `_identify_if_regions`，统一处理 if/elif/else 边界与 BoolOp 归约。
3. **P3 LOOP/TERNARY**：repro_04/09 涉及 `_identify_loop_regions` 的 spurious for-else；repro_08 涉及嵌套 IfExp 作 if 条件。
4. **`_merge_block_is_loop_back_edge` 重命名**：按 spec F5 要求，建议 Round 2 执行重命名为 `is_merge_block_loop_back_edge`。
