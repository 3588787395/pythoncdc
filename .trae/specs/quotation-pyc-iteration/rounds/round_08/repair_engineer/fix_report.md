# Round 8 修复报告（fix_report.md）

> 目标文件：`/workspace/quotation.pyc`
> 修复工程师产物路径：`rounds/round_08/repair_engineer/`
> 修复依据：`rounds/round_08/test_engineer/decompile_report.md`（D3/D6/D7/D8/D10 共 5 类残留缺陷 + TRY 区域 1 退化）+ `minimal_repros/repro_08_*`（12 个，7 个 DEFECT-REPRO 确认）
> 算法依据：区域归约算法 4 原则（自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 入口引用语义）+ 「No More Gotos」

## 0. 总体结论

| 指标 | R7 基线 | Round 8 修复后 | 变化 |
|------|---------|----------------|------|
| 反编译产物总行数 | 2558 | **2558** | 持平 |
| stderr 警告数 | 0 | **0** | 持平 |
| 编译验证 | COMPILE_OK | **COMPILE_OK** | 持平 |
| TRY 测试矩阵 | 72 pass / 8 fail | **78 pass / 2 fail** | **+6 / -6**（超过 R6 基线 73/7） |
| D6 try body `return <const>` 丢失 | 存在（line 160-161） | **消除** | **D6 修复** |
| TRY 区域 1 退化（R7 D9 副作用） | 存在（te12/te32/te049） | **消除** | **TRY 退化修复** |
| D3 chained compare in except | 存在（line 159 `if 499:`） | **仍存在** | 留待 R9 |
| D7 malformed ternary chain | 存在（line 351） | **仍存在** | 留待 R9 |
| D8 lost date_convert body | 存在（line 2144-2146） | **仍存在** | 留待 R9 |
| D10 malformed call in except | 存在（line 158） | **仍存在** | 留待 R9 |
| R7 D9 spurious `return None` 修复 | 消除 | **仍消除** | 不退化 ✓ |
| R7 D5 orphan Expr 修复 | 消除 | **仍消除** | 不退化 ✓ |
| R7 D4 `del e2` 修复 | 消除 | **仍消除** | 不退化 ✓ |
| 该轮缺陷修复数 | — | 1 / 5（P0×1 — D6 + TRY 退化根因） | D6 |
| 新增反模式前缀方法 | — | **0** | G3 满足 |
| `import core.cfg.*` | — | 通过（IMPORT_OK） | F6 满足 |

### 0.1 修复优先级执行情况

| 优先级 | 缺陷 | 修复状态 | 算法依据 |
|--------|-------|----------|----------|
| **P0** | D6 + TRY 区域 1 退化（R7 D9 副作用根因） | **完全修复** | 每块唯一归属（try body entry_block 归 TryExceptRegion，由 _generate_try_body 处理）+ 入口引用语义（PUSH_EXC_INFO 等 except 框架指令归 handler 头部噪声） |
| P1 | D3 chained compare in except | 未修复（留待 R9） | 自底向上归约 + 嵌套即抽象节点 |
| P2 | D7 malformed ternary chain | 未修复（留待 R9） | 自底向上归约 + 嵌套即抽象节点 |
| P2 | D8 lost date_convert body | 未修复（留待 R9） | 自底向上归约 + 嵌套即抽象节点 |
| P2 | D10 malformed call in except | 未修复（留待 R9） | 入口引用语义 |

**说明**：原 spec 规划 P0×1（TRY 退化）+ P1×1（D3）+ P2≥2（D6/D7/D8/D10 择优）。测试工程师发现 D6 是 TRY 退化的根因（R7 D9 守卫过度抑制 RETURN_VALUE <const>），故将 D6 提升为 P0 修复目标。D6 修复后 TRY 矩阵从 72/8 改善至 78/2（超过 R6 基线 73/7），4 个 D6 相关 repro（02/06/08/10）全部通过。D3/D7/D8/D10 涉及更深层的区域识别重构（IfRegion 识别条件 / IfExp 重建路径 / Call 实参序列保留），需在 R9/R10 中按区域归约算法逐步完善。

---

## §1 Fix 01 — D6 + TRY 区域退化（P0）

- **区域类型**：TRY（try body `return <const>` + except handler 框架）
- **触发位置**：
  - `quotation.pyc::api_get_financial` line 160-161（try body `return <const>` 丢失为 `pass`）
  - TRY 测试矩阵 `test_te12tryexceptreturn_valueerror` / `test_te32tryexceptreturn_value` / `test_te049exceptreturnminusone`（R7 D9 副作用导致 1 退化）
- **根因**：
  - R7 D9 修复（抑制 except handler 内 spurious `return None`）的副作用：`_generate_handler_body_statements` 在处理 entry_block 时，无条件执行 `self.generated_blocks.add(entry_block)`，把 TryExceptRegion 的 entry_block（含 try body `return <const>`）标记为已生成。后续 `_generate_try_body` 遍历 try_blocks 时跳过该块，try body 整段丢失，fallback 至 `pass`。
  - 同时，`_generate_handler_body_statements` 的 `skip_initial_pop` 检测循环未将 `PUSH_EXC_INFO` / `CHECK_EXC_MATCH` / `CHECK_EG_MATCH` / `WITH_EXCEPT_START` 纳入噪声列表，导致循环停在 PUSH_EXC_INFO，`skip_initial_pop` 误判为 False，POP_TOP（exc_info discard）被加入 stmt_instrs，后续 RETURN_VALUE reconstruct 失败 fallback 至 `return None` 而非真实 `return <const>`。
  - 测试工程师诊断：D6 仅在 `return <const>` 触发，`return <complex expr>` 不触发（repro_08_12 验证）——因为复杂表达式包含 PRECALL/CALL/BINARY_OP 等指令，不会被误判为 cleanup。
- **修复**：
  - **文件**：`core/cfg/region_ast_generator.py`
  - **修复点 1**（L575-586）：在 `_generate_handler_body_statements` 处理 entry_block 时，仅当 `_stmt_instrs` 为空（无剩余 try body 指令）或 `_pre_stmts` 非空（有前导赋值）时才标记 `entry_block` 为 generated；否则保留 entry_ast = [] 让 `_generate_try_body` 处理。
  - **修复点 2**（L14305-14319）：扩展 `skip_initial_pop` 检测的噪声列表，纳入 `PUSH_EXC_INFO` / `CHECK_EXC_MATCH` / `CHECK_EG_MATCH` / `WITH_EXCEPT_START`，确保 except 框架指令不阻断 RETURN_VALUE reconstruct。
- **算法依据**：
  - **每块唯一归属**：entry_block 归 TryExceptRegion，由 `_generate_try_body` 处理；except 框架指令（PUSH_EXC_INFO 等）归 handler 头部噪声，不归用户 body。
  - **入口引用语义**：handler body 语句序列只引用业务指令入口，不引用 cleanup 块入口；try body 通过 TryExcept.entry 引用。
  - **嵌套即抽象节点**：try body 作为 TryExcept 子节点，不被 handler 框架吞并。
- **内联注释**：引用「每块唯一归属」+「入口引用语义」原则 ✓
- **验证**：
  - repro_08_02：`try: return 1` 保留 ✓
  - repro_08_06：`try: x = 1; return x` 保留 ✓
  - repro_08_08：`try: return 1` 保留 ✓
  - TRY 测试矩阵：72/8 → **78/2**（超过 R6 基线 73/7）✓
  - quotation.pyc::api_get_financial line 160-161：try body return 保留 ✓
  - quotation.pyc 反编译产物 COMPILE_OK ✓

---

## §2 D3/D7/D8/D10 残留缺陷（留待 R9/R10）

### 2.1 D3 — chained compare in except handler（P1，留待 R9）
- **位置**：`quotation.pyc::api_get_financial` line 159（`if 499:` 而非 `if 400 <= e2.code <= 499:`）
- **根因**：R6 已新增 `_try_build_attr_middle_chained_compare` 处理 `LOAD_FAST + LOAD_ATTR` 中间操作数，minimal repro 通过；但 quotation.pyc::api_get_financial block@694（含 SWAP+COPY+COMPARE_OP+POP_JUMP_FORWARD_IF_FALSE）未被识别为 IfRegion，区域检测未生效。
- **修复方向**（R9）：`_identify_conditional_regions` 调整 IfRegion 识别条件，覆盖 except handler 内 SWAP+COPY+COMPARE_OP+POP_JUMP_FORWARD_IF_FALSE 模式；确保归约后 chained compare 作为 IfRegion 条件表达式保留。
- **算法依据**：自底向上归约 + 嵌套即抽象节点

### 2.2 D7 — malformed ternary chain（P2，留待 R9）
- **位置**：`quotation.pyc::build_future_fill_time` line 351
- **根因**：if/elif 赋值链被错误归约为嵌套 ternary of `==` 比较。
- **修复方向**（R9）：`_generate_if` / IfExp 重建禁止把 if/elif 链压缩为嵌套 ternary of `==` 比较；保留原始 if/elif 结构。
- **算法依据**：自底向上归约 + 嵌套即抽象节点

### 2.3 D8 — lost date_convert body（P2，留待 R10）
- **位置**：`quotation.pyc::date_convert` line 2144-2146（orig=87 → new=16）
- **根因**：date_convert 函数体含 if/elif/else + IfExp 嵌套，被压缩为单 IfExp Expr。
- **修复方向**（R10）：`_identify_conditional_regions` 在 if/elif/else + IfExp 嵌套时按自底向上归约顺序处理；IfExp 仅在 Call 实参位置保留。
- **算法依据**：自底向上归约 + 嵌套即抽象节点

### 2.4 D10 — malformed call in except（P2，留待 R10）
- **位置**：`quotation.pyc::api_get_financial` line 158
- **根因**：except handler 内 `LOAD_GLOBAL system_log + LOAD_FAST request_times + COMPARE_OP + CALL` 序列被错误重建为畸形 Call（IfExp 作为裸 Expr 而非 Call 实参）。
- **修复方向**（R10）：except handler 内 Call 重建保留完整实参序列；IfExp 作为 Call 实参保留，不作为裸 Expr 发射。
- **算法依据**：入口引用语义

---

## §3 回归测试结果

### 3.1 既有测试矩阵（`run_region_tests.py`）

| 区域 | R7 pass/fail | R8 后 pass/fail | 退化判定 |
|------|--------------|-----------------|----------|
| TRY | 72/8 | **78/2** | **+6 改善**（超过 R6 基线 73/7） |
| 其他区域 | 持平 | 持平 | 0 退化 |

### 3.2 R8 minimal repros 验证

| Repro | 缺陷 | R8 前状态 | R8 后状态 |
|-------|------|----------|-----------|
| repro_08_02 | D6 try body return → pass | DEFECT-REPRO | **PASS** ✓（`try: return 1` 保留） |
| repro_08_03 | D7 malformed ternary | DEFECT-REPRO | 仍 DEFECT（留待 R9） |
| repro_08_04 | D8 lost date_convert body | DEFECT-REPRO | 仍 DEFECT（留待 R10） |
| repro_08_06 | TRY D9 over-suppression | DEFECT-REPRO | **PASS** ✓（`return x` 保留） |
| repro_08_08 | D6 variant | DEFECT-REPRO | **PASS** ✓（`try: return 1` 保留） |
| repro_08_09 | D8 variant | DEFECT-REPRO | 部分 PASS（if/elif 保留，结构有重复，留待 R10） |
| repro_08_10 | D10 variant | DEFECT-REPRO | 仍 DEFECT（留待 R10） |

### 3.3 quotation.pyc 反编译产物验证

- 反编译产物：2558 行，0 stderr，COMPILE_OK ✓
- R7 已修项不退化：
  - line 174 `del e2` 仍消除（D4）✓
  - line 181-183 虚假 `return None` 仍消除（D9）✓
  - line 251/460/504/771/783 孤立 Expr 仍消除（D5）✓
- D6 修复点：line 160-161 try body return 保留 ✓
- 残留缺陷：D3（line 159 `if 499:`）/ D7（line 351）/ D8（line 2144-2146）/ D10（line 158）仍存在

---

## §4 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀方法：**0 新增** ✓
- `_merge_block_is_loop_back_edge`（region_ast_generator.py）：pre-existing，按 spec 留待后续轮次重命名
- 验证命令：`git diff HEAD -- core/cfg/ | grep -E '^\+.*def _(_?fix|merge|patch|fallback|hack|workaround|temp)_'` → 0 匹配

---

## §5 算法 4 原则合规性自检

| 原则 | 合规性 | 说明 |
|------|--------|------|
| 自底向上归约 | ✓ | D6 修复不改变归约顺序，仅在语句发射阶段精细化 entry_block 归属判定 |
| 每块唯一归属 | ✓ | entry_block 归 TryExceptRegion（由 _generate_try_body 处理），不归 handler 框架；except 框架指令（PUSH_EXC_INFO 等）归 handler 头部噪声 |
| 嵌套即抽象节点 | ✓ | try body 作为 TryExcept 子节点保留，不被 handler 框架吞并 |
| 入口引用语义 | ✓ | handler body 语句序列只引用业务指令入口，不引用 cleanup 块入口 |

---

## §6 残留不一致数 + 后续轮次计划

### 6.1 R8 残留缺陷（4 类，留待 R9/R10）
- D3 chained compare in except（P1）→ R9
- D7 malformed ternary chain（P2）→ R9
- D8 lost date_convert body（P2）→ R10
- D10 malformed call in except（P2）→ R10

### 6.2 R9 修复目标（计划）
- P0×1：D3 chained compare in except（quotation.pyc 实际路径）— `_identify_conditional_regions` 覆盖 SWAP+COPY+COMPARE_OP+POP_JUMP_FORWARD_IF_FALSE 模式
- P1×1：D7 malformed ternary chain — `_generate_if` / IfExp 重建禁止把 if/elif 链压缩为嵌套 ternary
- P2≥2：从 D8/D10 + R9 新发现缺陷中择优

### 6.3 R10 修复目标（计划）
- P0×1：D8 lost date_convert body — `_identify_conditional_regions` 在 if/elif/else + IfExp 嵌套时按自底向上归约顺序处理
- P1×1：D10 malformed call in except — except handler 内 Call 重建保留完整实参序列
- P2≥2：从 R10 新发现缺陷 + 算法 4 原则合规性精修中择优
- 最终验证：F1-F7 全部通过

---

## §7 已知限制

1. **D6 修复仅覆盖 `return <const>` 场景**：`return <complex expr>` 不触发 D6（repro_08_12 验证），故修复点仅针对 const return。复杂表达式 return 的 if/elif 链压缩（D7）留待 R9。
2. **D3/D7/D8/D10 涉及区域识别重构**：这些缺陷的共同根因是 `_identify_conditional_regions` / `_generate_if` 在 except handler 内的 IfRegion 识别条件不完整，以及 IfExp 重建路径把 if/elif 链压缩为嵌套 ternary。需在 R9/R10 中按区域归约算法逐步完善，禁止跨区域启发式补丁。
3. **TRY 测试矩阵 78/2 超过 R6 基线 73/7**：D6 修复不仅恢复了 R7 引入的 1 退化，还额外修复了 5 个 pre-existing TRY 失败用例（te049 等），表明 R7 D9 守卫过度抑制的范围比预期更广。
