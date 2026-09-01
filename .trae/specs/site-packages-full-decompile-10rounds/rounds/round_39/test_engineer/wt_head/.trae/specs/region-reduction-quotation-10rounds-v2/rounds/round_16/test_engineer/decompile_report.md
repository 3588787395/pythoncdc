# R16 测试工程师报告

## 1. 基线统计

| 指标 | R15 修复后 | R16 基线 |
|------|-----------|---------|
| 总函数数 | 150 | 150 |
| 一致函数数 | 146 | **146** |
| 不一致函数数 | 4 | 4 |
| 成功率 | 97.33% | **97.33%** |
| compile_ok | True | True |

R16 基线与 R15 修复后完全一致（146/150），无退化。`build_future_fill_time` 在 R15 已修复，保持 match。

## 2. 残留 4 个不一致函数

| 函数名 | 状态 | 说明 |
|--------|------|------|
| `<module>` | instr_diff@444 | **R16 重点**（任务假设 co_filename，实测为 get_str_data len_diff 传递） |
| `get_str_data` | len_diff -48 (317→269) | R12 遗留 |
| `change_his_to_backward` | instr_diff@296 | R14 defer（指令重排） |
| `get_date_and_count` | len_diff -27 (714→687) | R13 遗留 |

## 3. `<module>` 差异分析

### 3.1 任务假设 vs 实测根因

任务假设：`<module>` @idx394 为嵌套 code 对象的 co_filename 元数据差异。

**实测结果：任务假设不准确。**

- 实际 first_diff 为 **@idx444**（非 394；394 为早期估计值）
- idx 444 为 `LOAD_CONST <code get_str_data>`，两边的 code 对象 co_filename 确实不同：
  - orig: `./fly_docker_py311/fly/data/quotation.py`
  - new: `<decompiled>`
- **但 co_filename 并非 `<module>` 失败的根因**：当前 `instr_equal` 的 code 对象比较分支**只递归比较字节码指令列表，从不比较 co_filename**。

### 3.2 诊断证据（_diag_module.py）

| idx | code 对象 | co_filename 差异 | 指令长度 | instr_equal | 结论 |
|-----|----------|-----------------|---------|-------------|------|
| 441 | obtain_date | 是（不同） | 58 vs 58（相同） | **True** | co_filename 不同但通过 → 证明 co_filename 不被比较 |
| 444 | get_str_data | 是（不同） | 317 vs 269（**不同，-48**） | **False** | 失败根因为 **len_diff**，非 co_filename |

**关键证据**：idx 441 (obtain_date) 的 co_filename 同样不同（`./fly_docker_py311/...` vs `<decompiled>`），但 `instr_equal=True`，因为其指令列表相同（58 vs 58）。这证明 co_filename 差异**已被忽略**，不是 `<module>` 失败的原因。

idx 444 (get_str_data) 失败的真实原因是 **get_str_data 自身的 len_diff（317 vs 269，-48）**——即反编译产物丢失了 48 条指令。`<module>` 通过 `LOAD_CONST <code get_str_data>` 嵌入了 get_str_data 的 code 对象，递归比较时因长度不等而失败。这是**传递性不一致**（transitive mismatch），非 `<module>` 自身的指令差异。

### 3.3 diff_detail 显示假象说明

diff_detail.txt 中所有 code 对象均标记 `!!`，这是因为 diff_detail 的 `_eq_av` 函数对所有 code 对象返回 False（简化显示，不做递归比较）。实际 `instr_equal` 做递归比较，只有指令列表不等的 code 对象（get_str_data）才真正失败。任务假设的"co_filename 差异"系被此显示假象误导。

### 3.4 `<module>` 后续潜在失败点

即使归一化 get_str_data 的比较，`<module>` 还会在后续 code 对象处失败：
- idx 453: change_his_to_backward（instr_diff@296，指令内容不同）
- get_date_and_count（len_diff -27）

即 `<module>` 的失败是多个 deferred 函数（get_str_data/change_his_to_backward/get_date_and_count）传递性不一致的叠加，非单一 co_filename 元数据问题。

## 4. 最小复现实例（10 个）

10 个复现实例演示嵌套 code 对象的 co_filename 元数据差异（编译时 filename 不同导致 co_filename 不同，但字节码指令 100% 相同）：

| 复现实例 | code 对象数 | co_filename 差异数 | 指令相同率 |
|---------|-----------|-------------------|-----------|
| repro_01_module_nested_func | 2 | 2 | 2/2 (100%) |
| repro_02_lambda | 2 | 2 | 2/2 (100%) |
| repro_03_listcomp | 2 | 2 | 2/2 (100%) |
| repro_04_dictcomp | 2 | 2 | 2/2 (100%) |
| repro_05_setcomp | 2 | 2 | 2/2 (100%) |
| repro_06_genexpr | 2 | 2 | 2/2 (100%) |
| repro_07_nested_func_in_func | 3 | 3 | 3/3 (100%) |
| repro_08_multi_top_level_funcs | 4 | 4 | 4/4 (100%) |
| repro_09_closure | 3 | 3 | 3/3 (100%) |
| repro_10_mix_func_comp | 4 | 4 | 4/4 (100%) |

**结论**：co_filename 差异是真实的元数据差异（orig 用源文件路径，new 用 `<decompiled>`），但**不影响字节码指令**。当前 `instr_equal` 已正确忽略此差异（只比较指令列表）。

## 5. 反编译产物

| 检查项 | 结果 |
|--------|------|
| /tmp/r16_decompiled.py | 生成成功（src_len=175488, src_lines=3641） |
| compile(src, '<decompiled>', 'exec') | OK |
| 反编译耗时 | 1.62s |

## 6. 对修复工程师的建议

1. **co_filename 归一化**：可在 `instr_equal` 的 code 对象比较分支中显式文档化"忽略 co_filename"（当前已是隐式行为，可作为防御性归一化显式化）。此归一化**本身是正确的**（co_filename 不影响字节码语义），但**不会使 `<module>` 变为 match**，因为真实阻塞点是 get_str_data 的 len_diff。

2. **`<module>` 真实修复路径**：要使 `<module>` 变为 match，需先修复 get_str_data（R12 deferred）、change_his_to_backward（R14 deferred）、get_date_and_count（R13 deferred）的 len_diff/instr_diff。这些超出 R16 低风险方案范围。

3. **零退化保证**：co_filename 归一化为 no-op（当前已隐式忽略），实施后不会改变任何函数的比较结果，0 退化风险。
