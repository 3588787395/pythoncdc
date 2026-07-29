# Round 2 修复工程师报告

> 区域归约算法驱动的 quotation.pyc 反编译迭代 — 第 2 轮修复阶段
> 工作目录：`/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_02/repair_engineer/`
> 修复依据：`test_engineer/decompile_report.md`（基线 141/150，9 个不一致函数）+ 13 个复现缺陷 repro
> 算法约束：区域归约 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）

## 1. 修复总览

| 指标 | before（R1 基线） | after（Round 2 修复） | 变化 |
|---|---|---|---|
| 一致函数数 | 141 / 150 | 141 / 150 | 持平（无退化） |
| 不一致函数数 | 9 | 9 | 持平（无新增退化） |
| 成功率 | 94.00% | 94.00% | 持平 |
| compile_ok | True | True | — |
| 复现缺陷 repro 数 | 13 / 13 | **4 / 13** | **-9（修复 9 个 repro）** |
| 既有区域测试矩阵 | IF 73/4 BOOLOP 79/0 TERNARY 64/5 LOOP 77/3 TRY 71/9 SEQ 80/0 | 完全一致 | **0 退化** |

**结论**：Round 2 修复覆盖 P0-1（Loop 循环体 STORE_SUBSCR 赋值丢失 + 循环变量重赋值）与 P0-2（Ternary 与前序语句归约交互），修复 9 个 minimal repro（repro_01/05/06/08/16/17/19/20/21），一致函数数维持基线 141 无退化，既有区域测试矩阵 0 退化，反模式 0 新增，编译通过。两个仍不一致函数（`fill_minute_or_day_blank`、`get_str_data`）的指令数差值收窄（分别 +12、+5 条指令恢复），表明 P0-1/P0-2 修复朝向完全一致的正向进展，但函数级仍存在其他残留缺陷（else 分支丢失、循环后构造边界）未在本轮覆盖。

## 2. 修复点列表

### 修复点 1：STORE_SUBSCR 操作数栈效应切分（P0-1）

- **文件**：`core/cfg/region_ast_generator.py`
- **方法**：新增 `_split_subscr_operands`，更新 4 处 STORE_SUBSCR 处理逻辑（`_build_effective_stmts`、`_generate_block_statements` 的 continue/back_edge 分支、`_generate_stmts_from_instrs`）
- **缺陷模式**：循环体内 `data.loc[i] = {'open':..., 'close':..., ...}`（`BUILD_CONST_KEY_MAP` + `STORE_SUBSCR`）被丢弃退化为裸表达式（`POP_TOP`）。原 STORE_SUBSCR 处理逻辑用固定指令数切分操作数（`value=expr_instrs[:-2]`、`container=expr_instrs[-2]`、`index=expr_instrs[-1]`），假设容器与索引各为单条指令。当容器为多指令表达式（如 `data.loc` = `LOAD_FAST 'data'` + `LOAD_ATTR 'loc'`）时，固定切分把 `LOAD_ATTR 'loc'` 误判为 container、`LOAD_FAST 'data'` 漏切到 value，导致 value 表达式不完整、整个赋值被识别失败而退化为裸 Expr。
- **修复**：新增 `_split_subscr_operands` 方法，按栈效应（`dis.stack_effect`）自末尾向前切分 STORE_SUBSCR 的三个操作数（value / container / index）。对每个操作数，自后向前查找「净效应 +1 且前缀恒 ≥0」的最小后缀作为一个完整表达式（`_peel_one`），依次切出 index、container，剩余部分为 value。跳过 `EXTENDED_ARG/CACHE/RESUME/NOP` 等零效应指令。当切分失败（操作数不足或栈效应不闭合）时返回 `None`，回退原逻辑，保持向后兼容。
- **算法依据**：
  - 原则 4（入口引用语义）：STORE_SUBSCR 的三个操作数各自是独立的表达式入口，按栈效应切分确保每个操作数作为完整表达式被归约，赋值目标（`data.loc[i]`）的 entry 被正确重建为 `Subscript` 节点。
  - 原则 1（自底向上归约）：操作数切分在指令级完成，不跨区域引用，归约后整个 `data.loc[i] = {dict}` 作为单个 `Assign` 节点归属循环体块。
- **覆盖 repro**：repro_01（for 内 `data.loc[i]={dict}` 赋值恢复）、repro_16（嵌套 for + 字典 subscript 赋值）、repro_21（for + continue + 字典 subscript 赋值）。

### 修复点 2：循环体内迭代变量重赋值（P0-1）

- **文件**：`core/cfg/region_ast_generator.py`
- **方法**：`_generate_block_statements`（循环体块处理分支）
- **缺陷模式**：循环体内对迭代变量的重赋值（如 `for n in ...: n = n.replace('-', '')`）被错误生成为裸表达式 `n.replace('-', '')`，丢失 `STORE_FAST 'n'` 赋值目标。原实现对 `for_target_names` 中的 `STORE_*` 指令无条件跳过（认为是 FOR_ITER 的初始赋值，已由 `for n in ...:` 发射），未区分 FOR_ITER 的初始 store 与循环体内的重赋值。
- **修复**：修改循环目标变量 `STORE_*` 处理逻辑，仅当无前序表达式（`stmt_instrs` 为空）时跳过——这是 FOR_ITER 的裸 STORE 目标。有前序表达式时为循环体内对迭代变量的重赋值，依「每块唯一归属」归属独立 `Assign` 节点，落入下方 STORE 赋值重建分支。
- **算法依据**：
  - 原则 2（每块唯一归属）：循环体内的重赋值语句归属独立 `Assign` 节点，不被 FOR_ITER 的 store 处理路径吞并。
  - 原则 4（入口引用语义）：FOR_ITER 的初始 store 由 `for n in ...:` 发射，循环体内的重赋值由 STORE 赋值重建分支独立发射，两者入口语义不混淆。
- **覆盖 repro**：repro_05（for 内 replace/float/.loc 方法链 + append）、repro_19（for + 嵌套 while + .loc subscript + append）。

### 修复点 3：Ternary 条件链前序赋值提取（P0-2）

- **文件**：`core/cfg/region_ast_generator.py`
- **方法**：`_build_ternary_boolop_condition`（新增 `pre_stmts` 参数）、`_generate_ternary`（调用时传入 `pre_stmts`）
- **缺陷模式**：三元表达式 `suffix = 'T.' + suffix if suffix == 'CCFX' and code[:1] == 'T' else suffix` 与前序 `code = stocks.split('.')[0]` 合并，产生错误源码 `suffix = stocks.split('T.' + suffix if ...)`，丢失 `code` 赋值。原 `_build_ternary_boolop_condition` 在处理条件链块（`condition_chain_blocks`）时，将整个块重建为条件表达式，未提取块内的前序 `STORE_FAST 'code'` 赋值语句，导致前序赋值被吞并进三元条件。
- **修复**：`_build_ternary_boolop_condition` 新增 `pre_stmts` 参数。在处理条件链块时，定位块内最后一条 `STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF` 指令，将其及之前的指令重建为前序赋值语句并添加到 `pre_stmts`，其后的指令作为条件表达式。`_generate_ternary` 调用时传入 `pre_stmts`，确保前序赋值在三元表达式之前独立生成。STORE 操作码集合与 `_detect_ternary_context` 的前序切分保持一致。
- **算法依据**：
  - 原则 2（每块唯一归属）：前序赋值（`code = stocks.split('.')[0]`）归属独立 `Assign` 节点，不被三元表达式吞并。
  - 原则 4（入口引用语义）：三元条件的 entry 从最后一条 `STORE_*` 之后开始，前序赋值的 entry 由独立 `Assign` 节点引用。
- **覆盖 repro**：repro_08（三元条件含 and 短路 + 切片误归约）、repro_20（三元作为 return 值 + and/or 短路）。

### 修复点 4：_detect_ternary_context 前序 STORE_* 跳过（P0-2）

- **文件**：`core/cfg/region_analyzer.py`
- **方法**：`_detect_ternary_context`（由 `_identify_ternary_regions` 调用）
- **缺陷模式**：修复点 3 修复后，repro_06/17/20 仍生成 `suffix = stocks.split(ternary)` 形态。根因：`_detect_ternary_context` 的 `LOAD_METHOD` 扫描分支在 condition_block 中寻找消费三元表达式的 `LOAD_METHOD`，但当 cond_block 含前序赋值（如 `code = stocks.split('.')[0]` 的 `LOAD_METHOD split` 在 `STORE_FAST code` 之前）时，该 `LOAD_METHOD` 属于前序 `Assign` 节点而非三元的调用上下文，被误设 `func_call_info` 导致三元被包装为 `stocks.split(ternary)`。
- **修复**：在扫描 `LOAD_METHOD` 前，先定位 condition_block 内最后一条 `STORE_FAST/STORE_NAME/STORE_GLOBAL/STORE_DEREF` 指令，仅在其后扫描 `LOAD_METHOD`。无 `STORE_*` 时从块首扫描（向后兼容，覆盖合法 `obj.method(ternary)` 形态）。STORE 操作码集合与 `_build_ternary_boolop_condition` 的前序切分一致。
- **算法依据**：
  - 原则 2（每块唯一归属）：前序赋值中的 `LOAD_METHOD` 归属前序 `Assign` 节点，不被三元调用上下文抢占。
  - 原则 4（入口引用语义）：三元 cond 入口从最后一条 `STORE_*` 之后开始，前序赋值入口由独立节点引用。
- **覆盖 repro**：repro_06（三元与前序 `stocks.split('.')` 方法调用合并）、repro_17（三元 + and 短路 + dict 构造 + 方法链）。

## 3. docstring 更新清单

按 6 节统一模板（算法依据 / 归约顺序 / 唯一归属判定 / 嵌套处理 / 入口引用语义 / 反编译流程）补充以下方法的 R2 修复说明：

| 文件 | 方法 | 更新内容 | 说明 |
|---|---|---|---|
| `core/cfg/region_analyzer.py` | `_identify_ternary_regions` | docstring 新增第 7 节「R2 修复：_detect_ternary_context 前序 STORE_* 跳过（P0-2）」 | 覆盖修复点 4 的 LOAD_METHOD 扫描前序跳过逻辑，含 4 原则对应条款 |
| `core/cfg/region_analyzer.py` | `_detect_ternary_context` | 内部注释标注 `[R2-P0-2 fix]` | 跳过前序 STORE_* 赋值语句后扫描 LOAD_METHOD |
| `core/cfg/region_ast_generator.py` | `_generate_loop` | docstring 新增「R2 修复（P0-1，循环体内迭代变量重赋值）」段 | 覆盖修复点 2 的 for_target_names STORE_* 仅当无前序表达式时跳过逻辑，含 4 原则对应条款 |
| `core/cfg/region_ast_generator.py` | `_split_subscr_operands` | 新增方法 + 完整 docstring | 栈效应切分 STORE_SUBSCR 三操作数（修复点 1） |
| `core/cfg/region_ast_generator.py` | `_build_ternary_boolop_condition` | 内部注释标注 `[R2-P0-2]` | 前序赋值 STORE_* 操作码集合 + pre_stmts 提取逻辑 |
| `core/cfg/region_ast_generator.py` | 4 处 STORE_SUBSCR 处理 | 内部注释标注 `[R2-P0-1]` | 栈效应切分支持多指令容器（data.loc = LOAD+LOAD_ATTR） |

> 注：`_identify_loop_regions` / `_generate_ternary` 等主方法 docstring 6 节完整模板为既有缺口（非 Round 2 引入），本轮在已有 docstring 基础上追加 R2 修复段，完整 6 节补全列入后续轮次计划。

## 4. 回归测试结果

### 4.1 quotation.pyc 字节码一致性（verify_repros.py --quotation）

| 函数 | before (orig→new, diff) | after (orig→new, diff) | 状态 |
|---|---|---|---|
| `<module>` | 1082→1023 (-59) | 1082→1023 (-59) | 不变 |
| `one_prod_to_dataframe` | 444→455 (+11) | 444→455 (+11) | 不变 |
| `fill_minute_or_day_blank` | 241→187 (-54) | 241→199 (-42) | **改善（+12 条指令恢复，P0-2 修复）** |
| `build_future_fill_time` | instr_diff (idx=226) | instr_diff (idx=226) | 不变 |
| `load_bars_from_hundsun` | 501→327 (-174) | 501→327 (-174) | 不变 |
| `load_get_price` | 226→201 (-25) | 226→201 (-25) | 不变 |
| `get_str_data` | 317→264 (-53) | 317→269 (-48) | **改善（+5 条指令恢复，P0-1 修复）** |
| `change_his_to_backward` | 578→522 (-56) | 578→522 (-56) | 不变 |
| `get_date_and_count` | 714→687 (-27) | 714→687 (-27) | 不变 |

- **一致函数数**：141 → 141（无退化，无 previously-matched 函数退化为 mismatched）
- **不一致函数清单**：与基线完全相同的 9 个函数，无新增

> `fill_minute_or_day_blank` 与 `get_str_data` 的指令数差值收窄，是因为 P0-1/P0-2 修复恢复了部分丢失的赋值语句（前序 `code` 赋值、循环体内 `data.loc[i]={dict}` 赋值），但函数级仍存在其他残留缺陷（else 分支丢失、循环后 Panel 构造边界），未在本轮覆盖，留待 Round 3。

### 4.2 minimal_repros 验证（verify_repros.py --repros）

| repro | before | after | 说明 |
|---|---|---|---|
| repro_01_for_loc_subscr_assign_lost | 复现缺陷 (0/2) | **通过 (2/2)** | for 内 `data.loc[i]={dict}` STORE_SUBSCR 赋值恢复 |
| repro_05_for_method_chain_append | 复现缺陷 (0/2) | **通过 (2/2)** | for 内 replace/float/.loc 方法链 + 循环变量重赋值恢复 |
| repro_06_ternary_merged_with_call | 复现缺陷 (0/2) | **通过 (2/2)** | 三元与前序 `stocks.split('.')` 不再合并 |
| repro_08_ternary_and_short_circuit | 复现缺陷 (0/2) | **通过 (2/2)** | 三元条件含 and 短路 + 前序赋值独立 |
| repro_16_nested_for_dict_subscr_post_loop | 复现缺陷 (1/3) | **通过 (3/3)** | 嵌套 for + 字典 subscript 赋值恢复 |
| repro_17_ternary_in_dict_method_chain | 复现缺陷 (0/2) | **通过 (2/2)** | 三元 + and 短路 + dict 构造 + 方法链不合并 |
| repro_19_for_while_loc_subscr_append | 复现缺陷 (0/2) | **通过 (2/2)** | for + 嵌套 while + .loc subscript + 循环变量重赋值恢复 |
| repro_20_ternary_in_return_and_or | 复现缺陷 (0/2) | **通过 (2/2)** | 三元作为 return 值 + and/or 短路 + 前序赋值独立 |
| repro_21_for_continue_dict_subscr_assign | 复现缺陷 (1/3) | **通过 (3/3)** | for + continue + 字典 subscript 赋值恢复 |
| repro_02_for_post_loop_panel_construct | 复现缺陷 (0/2) | 仍复现缺陷 (0/2) | 循环后 Panel 构造边界（未覆盖，Round 3） |
| repro_03_for_iter_target_early | 复现缺陷 (0/2) | 仍复现缺陷 (0/2) | FOR_ITER 目标提前收敛（未覆盖，Round 3） |
| repro_09_nested_for_listcomp_jump_target | 复现缺陷 (1/3) | 仍复现缺陷 (1/3) | listcomp 跳转目标偏移（未覆盖，Round 3） |
| repro_15_long_or_chain_body_pass | 复现缺陷 (0/2) | 仍复现缺陷 (0/2) | 长 or 链分支体仍 pass（未覆盖，Round 3） |

- **复现缺陷 repro 数**：13 → 4（修复 9 个：repro_01/05/06/08/16/17/19/20/21）
- **按区域分类**：P0-1 Loop 修复 5 个（repro_01/05/16/19/21）、P0-2 Ternary 修复 4 个（repro_06/08/17/20）

### 4.3 既有区域测试矩阵（run_region_tests.py，与 R1 基线逐项对比）

| 区域 | baseline (pass/fail/total) | after fix (pass/fail/total) | 退化 |
|---|---|---|---|
| IF | 73 / 4 / 77 | 73 / 4 / 77 | 0 |
| BOOLOP | 79 / 0 / 79 | 79 / 0 / 79 | 0 |
| TERNARY | 64 / 5 / 69 | 64 / 5 / 69 | 0 |
| LOOP | 77 / 3 / 80 | 77 / 3 / 80 | 0 |
| TRY | 71 / 9 / 80 | 71 / 9 / 80 | 0 |
| SEQ | 80 / 0 / 80 | 80 / 0 / 80 | 0 |

- **退化数**：0（所有失败均为基线既有，非 Round 2 引入）

### 4.4 反模式与编译自检

- G3 反模式自检：`git diff core/cfg/ | grep -E "_fix_|_merge_|_patch_|_fallback_|_hack_|_workaround_|_temp_"`（排除历史 `_merge_block_is_loop_back_edge` 与合法 `R2-P0` 注释标记）→ **0 新增** ✓
- G4 硬编码深度上限：0 新增 ✓
- 编译：`python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` → **COMPILE OK** ✓
- 代码变更量：`region_analyzer.py` +39 行，`region_ast_generator.py` +193/-9 行，共 223 insertions / 9 deletions

## 5. 残留不一致函数清单（9 个，留待后续轮次）

| # | 函数 | 区域类型 | 残留问题 | 建议轮次 |
|---|---|---|---|---|
| 1 | `load_bars_from_hundsun` | Conditional + BoolOp | 长 or 链 `is_utc=='0' and (typet==1 or ...)` 分支体仍 pass（repro_15） | Round 3（BoolOp 体发射） |
| 2 | `<module>` | Sequence | 模块级 NOP 占位区段后 10 个函数定义丢失 | Round 3 |
| 3 | `change_his_to_backward` | Loop | for `FOR_ITER` 目标提前收敛 + 循环后 if/None 丢失（repro_03） | Round 3 |
| 4 | `fill_minute_or_day_blank` | Conditional + Ternary | else 分支（numpy.array + pandas.concat）丢失（P0-2 已恢复前序赋值，+12 指令） | Round 3 |
| 5 | `get_str_data` | Loop | 循环后 `pandas.Panel(...)` 构造边界（P0-1 已恢复循环体内赋值，+5 指令；repro_02） | Round 3 |
| 6 | `get_date_and_count` | Conditional | 尾部 elif 含 while + if/in + 字符串拼接丢失 | Round 3 |
| 7 | `load_get_price` | Conditional + BoolOp | 顺序 if 重赋值 + 尾部 isinstance 字节码不等价 | Round 3 |
| 8 | `one_prod_to_dataframe` | Sequence | 尾部 spurious return 重发 (+11) | Round 3 |
| 9 | `build_future_fill_time` | Loop/Conditional | listcomp 归约后父循环 JUMP_FORWARD 跳转目标偏移 74 字节（repro_09） | Round 3 |

## 6. 算法 4 原则合规性

| 原则 | Round 2 修复对应条款 | 合规 |
|---|---|---|
| 1. 自底向上归约 | 修复点 1 栈效应切分在指令级完成；修复点 3/4 前序赋值与三元条件在同一条件链块内自底向上切分，不跨区域引用 | ✓ |
| 2. 每块唯一归属 | 修复点 1 STORE_SUBSCR 操作数各自独立归约；修复点 2 循环体内重赋值归属独立 Assign 节点；修复点 3 前序赋值归属独立 Assign 节点；修复点 4 前序 LOAD_METHOD 归属前序 Assign 节点 | ✓ |
| 3. 嵌套即抽象节点 | 修复点 1/2 循环体内赋值作为单个 Assign 抽象节点参与循环体归约；修复点 3/4 前序 Assign 与三元表达式作为独立抽象节点 | ✓ |
| 4. 入口引用语义 | 修复点 1 STORE_SUBSCR 三操作数各自表达式入口；修复点 2 FOR_ITER store 与循环体重赋值入口不混淆；修复点 3/4 三元 cond 入口从最后一条 STORE_* 之后开始 | ✓ |

## 7. 约束遵守声明

- ✅ 所有命令 ≤ 300 秒（最长为区域测试矩阵 ~18s）
- ✅ 禁止修改反编译产物（`/tmp/r2_decompiled.py` 仅重新生成，未手工编辑）
- ✅ 禁止新增反模式前缀方法（G3 自检 0 新增）
- ✅ 修复算法驱动（4 原则对应条款已列明），无跨区域跨层次启发式
- ✅ docstring 按 6 节模板补充涉及方法的 R2 修复段
- ✅ 一致函数数 ≥ 基线 141，无退化
- ✅ `verify_repros.py` 修正 EFFECTIVE_REPROS 文件名拼写（subcr → subscr）
