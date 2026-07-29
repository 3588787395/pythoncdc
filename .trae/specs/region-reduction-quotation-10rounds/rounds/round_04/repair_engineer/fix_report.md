# Round 4 修复工程师报告（fix_report.md）

> 区域归约算法驱动的 quotation.pyc 反编译迭代 — 第 4 轮修复工程师阶段
> 工作目录：`/workspace/.trae/specs/region-reduction-quotation-10rounds/rounds/round_04/repair_engineer/`
> 算法约束：区域归约 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）

## 1. 修复目标

主攻 `one_prod_to_dataframe`（+11 指令，最易 +1 候选），力争将一致函数数从 141 提升至 142，不允许退化。

## 2. 根因分析

### 2.1 缺陷函数：`one_prod_to_dataframe`（+11）

**缺陷模式**：`if i == 0 and len(v) == N:` 复合条件 elif 链被拆分为两个独立 if 结构。

**算法根因**：`_identify_conditional_regions` 在处理 `A and B` 复合条件的 elif 链时，将 `A`（`i == 0`）提取为外层 if 条件，破坏 elif 链连续性。具体表现为：
- 块 592（`i == 0` 条件）被识别为独立的 IF_THEN 区域（Region [13]）
- 块 634（`len(v) == 8` 条件）及后续条件块被识别为 IF_ELIF_CHAIN 区域（Region [12]）
- 反编译源码出现冗余的 `if i == 0:` 和独立的 `if len(v) == 11:` 结构

**深入分析**（使用 `debug_quotation_regions.py` 与 `debug_repro13_boolop.py`）：
1. `_detect_boolop_conditional_chain` 未能检测到 `i == 0 and len(v) == N` 模式的 BoolOp 链
2. `_sb_has_body` 检查错误地将 `v = str(v)` 的 STORE_FAST 指令视为 body 语句，阻止了 BoolOp 检测
3. 链条扩展被 `ft_succ in self.block_to_region` 中断，因为 `len(v) == N` 块属于 FOR_LOOP 区域（FOR_LOOP 区域在 BoolOp 之前识别，抢占块归属）

### 2.2 区域归约 4 原则违反项

- **原则 2（每块唯一归属）**：FOR_LOOP 区域在 BoolOp 之前识别，将循环体内条件块抢占为 FOR_LOOP body，阻止 BoolOp 链扩展
- **原则 4（入口引用语义）**：`A and B` 复合条件的 elif 链应共享同一 exit 入口，但被拆分为两个独立 if 结构

## 3. 修复尝试

### 3.1 修复方案

修改 `core/cfg/region_analyzer.py` 的 `_detect_boolop_conditional_chain` 方法：

1. **扩展 `_cond_start_offset` 回溯**：对 IF_FALSE/IF_TRUE，当条件是比较测试（COMPARE_OP / IS_OP / CONTAINS_OP + POP_JUMP_IF_FALSE/TRUE）时，通过栈深度回溯找到条件的起始指令（第一操作数入栈点），仅检查条件起始之后的 body 语句。关键差异：使用 `_depth == 0` 而非 `<= 0`——COMPARE_OP/IS_OP/CONTAINS_OP 的栈效应为 (1, 2)（净 -1），`<= 0` 会在 COMPARE_OP 处（depth=-2）过早停止，而 `== 0` 能继续回溯到第一操作数的 LOAD_* 指令。

2. **增加 `_compare_op_backtrack` 标志**：在 COMPARE_OP 回溯时，CALL+POP_TOP 检查需扫描整个块（含条件之前），以检测前置表达式语句（如 `check_datetime(date); if len(date) != 8 and ...:`）。

### 3.2 修复结果：退化（141 → 140）

修复后 quotation.pyc 一致函数数从 141 降至 140，`get_option_info` 新增退化（-26 指令），且 `one_prod_to_dataframe` 仍未修复（+11 不变）。

### 3.3 退化根因：`get_option_info` 的 if/elif 被误判为 BoolOp

通过 `debug_quotation_regions.py get_option_info` 对比修复前后区域：

**修复前（正确，get_option_info 匹配）：**
- Block 602（`if key == 'price_change_ratio':` → POP_JUMP_IF_TRUE 634）识别为 IF_THEN
- Block 622（`elif key == 'trading_time_desc':` → POP_JUMP_IF_FALSE 636）识别为 IF_ELIF_CHAIN
- 生成正确的 `if/elif` 结构

**修复后（错误，get_option_info -26）：**
- Block 602 + 622 被误识别为 BOOL_OP 区域（Region [4] BOOL_OP entry=602 blocks=[602, 622]）
- 生成错误的 `or` 短路结构

**误判原因**：COMPARE_OP 回溯使 BoolOp 检测在 if/elif 结构上触发。Block 602 跳转 TRUE（continue），block 622 跳转 FALSE（else body）——这是 `if/elif` 模式，不是 `or` 短路模式。真正的 `or` 链中两条件应跳向同一 TRUE 目标。修复缺少区分 `if A: continue; elif B:` 与 `if A or B:` 的守卫，属于跨区域启发式规则，违反算法原则。

### 3.4 `one_prod_to_dataframe` 未修复原因

即使 BoolOp 检测因 COMPARE_OP 回溯而触发，FOR_LOOP 区域仍在 BoolOp 之前识别，将循环体内条件块抢占为 FOR_LOOP body，阻止 BoolOp 链扩展到 `len(v) == N` 块。修复未触及区域识别顺序，无法解决此问题。

## 4. 回退决策

依据 spec 要求"若某轮出现退化，修复工程师必须先回退退化再推进新修复"，执行回退：

- `git checkout core/cfg/region_analyzer.py` 恢复 R3 状态
- 回退后重新验证：141/150 = 94.00%，9 个不一致函数（与 R3 基线完全一致）
- 区域测试矩阵无退化（详见第 6 节）

**回退理由**：
1. 修复导致退化（141→140），违反"不允许退化"硬性要求
2. 修复未达成目标（one_prod_to_dataframe 仍 +11）
3. 修复方案存在算法原则违反（跨区域启发式守卫缺失），无法通过简单补充守卫解决——区分 `if/elif` 与 `or` 短路需要分析跳转目标语义，超出单区域识别范围

## 5. 残留不一致数

| 指标 | R3 基线 | R4 修复尝试 | R4 回退后 |
|---|---|---|---|
| 一致函数数 | 141 | 140（退化） | 141（无退化） |
| 不一致函数数 | 9 | 10（+get_option_info） | 9 |
| 成功率 | 94.00% | 93.33% | 94.00% |
| compile_ok | True | True | True |

R4 回退后 9 个不一致函数与 R3 完全一致：`<module>`, `one_prod_to_dataframe`, `fill_minute_or_day_blank`, `build_future_fill_time`, `load_bars_from_hundsun`, `load_get_price`, `get_str_data`, `change_his_to_backward`, `get_date_and_count`。

## 6. 回归测试结果

### 6.1 quotation.pyc 一致性

- total=150, matched=141, mismatched=9, missing=0, success_rate=94.00%, compile_ok=True
- 与 R3 基线完全一致，无退化

### 6.2 既有区域测试矩阵

| 区域 | passed | failed | errors | total | 与 R3 对比 |
|---|---|---|---|---|---|
| IF | 73 | 4 | 0 | 77 | 一致，无退化 |
| LOOP | 77 | 3 | 0 | 80 | 一致，无退化 |
| TRY | 71 | 9 | 0 | 80 | 一致，无退化 |
| BOOLOP | 79 | 0 | 0 | 79 | 一致，无退化 |
| TERNARY | 64 | 5 | 0 | 69 | 一致，无退化 |
| SEQ | 80 | 0 | 0 | 80 | 一致，无退化 |

### 6.3 minimal_repros 验证

R4 测试工程师阶段提取 15 个 minimal_repros（10 个复现缺陷），覆盖 one_prod_to_dataframe / build_future_fill_time / load_get_price / load_bars_from_hundsun / get_str_data 等不一致函数。回退后区域状态与 R3 一致，repro 行为不变。

## 7. 算法 4 原则合规性

R4 回退后 `core/cfg/region_analyzer.py` 与 R3 完全一致，4 原则合规性与 R3 相同：

1. **自底向上归约**：`_build_region_hierarchy` 统一构建层级，识别阶段不跨层引用 ✓
2. **每块唯一归属**：`block_to_region` 为 canonical owner ✓
3. **嵌套即抽象节点**：嵌套区域作为单个抽象节点 ✓
4. **入口引用语义**：父区域 then/else 列表引用子区域 entry ✓

**R4 修复尝试的违规项（已回退）**：COMPARE_OP 回溯缺少区分 `if/elif` 与 `or` 短路的守卫，属于跨区域启发式规则，违反原则 1（自底向上归约——不应在单区域识别中分析跨块跳转目标语义）。

## 8. 反模式自检

- `core/cfg/` 下无新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法 ✓
- 无新增硬编码深度上限 ✓
- 无跨区域跨层次启发式规则（修复尝试已回退） ✓

## 9. 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator" → COMPILE OK
```

## 10. R5 修复建议

1. **one_prod_to_dataframe（+11）**：需解决 FOR_LOOP 区域抢占 BoolOp 块的问题。建议方向：在 `_identify_boolop_regions` 中允许链扩展到同一循环体内的块（验证 `ft_succ` 是否与起始块属于同一循环体）。需配套 `if/elif` vs `or` 短路守卫，避免 get_option_info 退化。
2. **build_future_fill_time（instr_diff）**：frozenset 版本差异，不可修，接受。
3. **get_date_and_count（-27）**：尾部 elif 体丢失，可探索 _generate_conditional 的 tail body 发射。
4. **load_get_price（-25）/ load_bars_from_hundsun（-174）**：长 or 链 + 嵌套 if 包裹，R3 修复未触达原始 CFG 路径，需更深区域嵌套分析。

## 11. 产物清单

| 产物 | 路径 |
|---|---|
| 调试脚本（CFG dump） | `repair_engineer/debug_quotation_regions.py` |
| 调试脚本（BoolOp 检测） | `repair_engineer/debug_repro13_boolop.py` |
| 修复报告 | `repair_engineer/fix_report.md`（本文件） |
| 测试工程师反编译报告 | `test_engineer/decompile_report.md` |
| 测试工程师一致性统计 | `test_engineer/bc_results.json` |
| 测试工程师 diff 详情 | `test_engineer/diff_detail.txt` |
| 测试工程师最接近目标分析 | `test_engineer/closest_targets.md` |
| minimal_repros 目录 | `test_engineer/minimal_repros/`（15 个 repro） |

## 12. 结论

R4 修复工程师阶段对 `one_prod_to_dataframe` elif 链分裂缺陷进行了根因分析与修复尝试。修复方案（COMPARE_OP 回溯扩展 BoolOp 检测）因导致 `get_option_info` 退化（-26 指令，141→140）且未修复目标函数，依据 spec 要求回退。R4 最终一致函数数 141/150 = 94.00%，与 R3 基线一致，无退化。退化根因与未修复原因已完整记录，为 R5 提供明确的修复方向（FOR_LOOP 区域抢占 + if/elif vs or 守卫）。
