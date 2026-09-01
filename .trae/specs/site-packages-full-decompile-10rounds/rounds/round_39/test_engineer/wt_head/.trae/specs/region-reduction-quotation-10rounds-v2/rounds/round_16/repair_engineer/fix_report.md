# R16 修复工程师报告

## 1. 修复目标

- **目标函数**: `<module>`（instr_diff@444；任务假设 @394 为 co_filename 差异）
- **R15/R16 基线**: 146/150 (97.33%)
- **修复方向**: 低风险方案 — 在 `exact_match_stats.py` 中归一化 code 对象的 co_filename 元数据差异，不修改反编译器代码（core/cfg/）

## 2. 根因分析

### 2.1 任务假设验证：co_filename 非真实阻塞点

任务假设：`<module>` 失败因嵌套 code 对象的 co_filename 差异（原始 `./fly_docker_py311/fly/data/quotation.py` vs 反编译 `<decompiled>`）。

**验证结果：co_filename 差异真实存在，但并非 `<module>` 失败的根因。**

诊断证据（`_diag_module.py`）：

| idx | code 对象 | co_filename 差异 | 指令长度 | instr_equal | 结论 |
|-----|----------|-----------------|---------|-------------|------|
| 441 | obtain_date | 是（不同） | 58 vs 58（相同） | **True** | co_filename 不同但通过 → 证明 co_filename 已不被比较 |
| 444 | get_str_data | 是（不同） | 317 vs 269（**不同，-48**） | **False** | 失败根因为 **len_diff**，非 co_filename |

**关键证据**：idx 441 (obtain_date) 的 co_filename 同样不同，但 `instr_equal=True`，因为其指令列表相同（58 vs 58）。这证明 R15 的 `instr_equal` 在 code 对象比较分支**已隐式忽略 co_filename**（只递归比较 `get_instr_list` 指令列表，从不直接比较 co_filename）。

### 2.2 真实根因：get_str_data 的 len_diff 传递性不一致

`<module>` @idx444 为 `LOAD_CONST <code get_str_data>`。`<module>` 通过此指令嵌入 get_str_data 的 code 对象，递归比较时因 **get_str_data 指令长度不等（317 vs 269，-48）** 而失败。

这是**传递性不一致**（transitive mismatch）：`<module>` 自身的 1023 条指令全部正确（orig_len=new_len=1023），失败仅因嵌入了一个自身不一致的 code 对象（get_str_data，R12 deferred）。

### 2.3 diff_detail 显示假象

diff_detail.txt 中所有 code 对象均标记 `!!`，这是因为 diff_detail 的 `_eq_av` 函数对所有 code 对象返回 False（简化显示，不做递归比较）。任务假设的"co_filename 差异"系被此显示假象误导。实际 `instr_equal` 做递归比较，只有指令列表不等的 code 对象（get_str_data）才真正失败。

### 2.4 `<module>` 后续潜在失败点

即使归一化 get_str_data 的比较，`<module>` 还会在后续 code 对象处失败：
- idx 453: change_his_to_backward（instr_diff@296，R14 deferred）
- get_date_and_count（len_diff -27，R13 deferred）

即 `<module>` 的失败是多个 deferred 函数传递性不一致的叠加，非单一 co_filename 元数据问题。

## 3. 修复方案

### 3.1 co_filename 元数据归一化（`_code_instr_equiv`，显式化）

新增 `_code_instr_equiv(av_a, av_b)` 函数，将 R15 隐式忽略 co_filename 的行为**显式化**并文档化：

**归一化规则（文档化到注释）**：
- 忽略 co_filename 差异：原始 pyc 为源文件路径，反编译产物为 `<decompiled>`，仅影响 traceback，不影响字节码语义
- 忽略 co_firstlineno 等纯位置元数据
- 保留 co_name 比较（语义标识，防止误比较不同函数的 code 对象）
- 递归比较字节码指令序列（含跳转目标归一化、常量归一化、嵌套 code 对象归一化）

**安全保证（防止过度归一化）**：
- 指令长度不等返回 False（不掩盖 len_diff）
- 指令内容不等返回 False（不掩盖 instr_diff）
- 仅忽略 co_filename/co_firstlineno 等纯元数据，不忽略任何语义字段

### 3.2 行为变化：no-op（0 退化风险）

R15 的 `instr_equal` 在 code 对象分支已只比较指令列表（隐式忽略 co_filename）。R16 将此行为提取为 `_code_instr_equiv` 并增加 co_name 检查，**不改变任何比较结果**：

- co_name 检查：所有 code 对象在 `<module>` 中均同名配对（obtain_date vs obtain_date 等），不影响结果
- 指令比较逻辑：与 R15 完全一致

### 3.3 修改范围

仅修改测试统计工具 `exact_match_stats.py`（repair_engineer 目录），**不修改反编译器代码（core/cfg/、pycdc.py）**，0 退化风险。

## 4. 回归结果

### 4.1 一致性统计

| 指标 | R15/R16 基线 | R16 归一化后 | 变化 |
|------|-------------|-------------|------|
| 总函数数 | 150 | 150 | — |
| 一致函数数 | 146 | **146** | 0（no-op） |
| 不一致函数数 | 4 | 4 | 0 |
| 成功率 | 97.33% | **97.33%** | 0 |
| compile_ok | True | True | — |

### 4.2 `<module>` 状态

| 函数名 | 基线状态 | 归一化后状态 | 说明 |
|--------|---------|-------------|------|
| `<module>` | instr_diff@444 | instr_diff@444 | **未变 match**（真实阻塞点为 get_str_data len_diff，非 co_filename） |

**说明**：co_filename 归一化为 no-op（R15 已隐式忽略 co_filename），`<module>` 未变为 match。`<module>` 的真实修复需先解决 get_str_data（R12）、change_his_to_backward（R14）、get_date_and_count（R13）的 deferred 不一致，超出了 R16 低风险方案范围。

### 4.3 已修复函数无退化

| 函数名 | R15 状态 | R16 状态 |
|--------|---------|----------|
| `build_future_fill_time` (R15) | match | match ✓ |
| `one_prod_to_dataframe` (R14) | match | match ✓ |
| 其他 145 个函数 | match | match ✓ |

### 4.4 残留不一致函数（4 个，与基线一致）

| 函数名 | 状态 | 说明 |
|--------|------|------|
| `<module>` | instr_diff@444 | get_str_data len_diff 传递性不一致（R16 已归一化 co_filename，但真实阻塞为 len_diff）|
| `get_str_data` | len_diff -48 | R12 遗留 |
| `change_his_to_backward` | instr_diff@296 | R14 defer（指令重排）|
| `get_date_and_count` | len_diff -27 | R13 遗留 |

### 4.5 反编译器代码完整性

| 检查项 | 结果 |
|--------|------|
| core/cfg/ 修改 | 无 ✓ |
| pycdc.py 修改 | 无 ✓ |
| git diff --stat -- core/ pycdc.py | 空 ✓ |

## 5. 算法 4 原则符合度

本修复仅修改测试统计工具，不涉及区域归约算法。归一化规则遵循语义等价原则：

| 原则 | 状态 | 说明 |
|------|------|------|
| 1. 自底向上归约 | N/A | 不涉及区域归约 |
| 2. 每块唯一归属 | N/A | 不涉及区域归约 |
| 3. 嵌套即抽象节点 | ✓ | code 对象作为嵌套节点递归比较，co_filename 为节点元数据非语义 |
| 4. 入口引用语义 | ✓ | code 对象比较只看字节码指令序列（入口语义），忽略 co_filename 元数据 |

## 6. 反模式自检

| 检查项 | 结果 |
|--------|------|
| `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法 | 0 新增 ✓ |
| 新增私有方法 | `_code_instr_equiv`（语义化命名，非反模式前缀）✓ |
| 硬编码深度上限 | 0 新增（_chase_elif_chain 复用 R14 的 200 步上限）✓ |
| 跨区域跨层次启发式规则 | 0 新增 ✓ |
| 后处理修正 | 0 新增（仅测试工具归一化）✓ |

## 7. 编译与导入

| 检查项 | 结果 |
|--------|------|
| compile /tmp/r16_decompiled.py | COMPILE_OK ✓ |
| 反编译产物 src_len | 175488 (3641 lines) ✓ |

## 8. 总结

R16 采用低风险方案，在 `exact_match_stats.py` 中将 code 对象的 co_filename 元数据归一化**显式化**为 `_code_instr_equiv` 函数并文档化归一化规则。

**关键发现**：任务假设的"co_filename 元数据差异"非 `<module>` 失败的真实根因。诊断证据表明：
1. co_filename 差异真实存在（orig 源文件路径 vs new `<decompiled>`），但 R15 的 `instr_equal` **已隐式忽略** co_filename（code 对象分支只比较指令列表）
2. `<module>` @idx444 失败的真实原因是 **get_str_data 的 len_diff（317 vs 269，-48）** 的传递性不一致——`<module>` 嵌入了 get_str_data 的 code 对象，递归比较时因长度不等而失败
3. 即使修复 get_str_data，`<module>` 还会在 change_his_to_backward、get_date_and_count 处失败（均为 deferred 函数）

**结果**：co_filename 归一化为 no-op，一致函数数维持 146/150（0 退化），0 新增反模式，反编译器代码未修改。`<module>` 未变为 match，因其真实阻塞点为多个 deferred 函数的传递性不一致，超出 R16 低风险方案范围。

**对后续轮次的建议**：要使 `<module>` 变为 match，需先修复 get_str_data（R12）、change_his_to_backward（R14）、get_date_and_count（R13）的 len_diff/instr_diff；或在 code 对象比较中引入"传递性不一致委托"机制（code 对象若已作为顶层函数单独比较，则 `<module>` 中不再重复比较其内部），但后者属于跨函数启发式，需谨慎评估。
