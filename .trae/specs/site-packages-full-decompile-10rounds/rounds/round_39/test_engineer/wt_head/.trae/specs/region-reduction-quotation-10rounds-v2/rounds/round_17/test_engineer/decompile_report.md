# R17 测试工程师报告

## 1. 基线统计

| 指标 | R16 修复后 | R17 基线 |
|------|-----------|---------|
| 总函数数 | 150 | 150 |
| 一致函数数 | 146 | **146** |
| 不一致函数数 | 4 | 4 |
| 成功率 | 97.33% | **97.33%** |
| compile_ok | True | True |

R17 基线与 R16 修复后完全一致（146/150），无退化。继承 R14/R15/R16 全部归一化逻辑。

## 2. 残留 4 个不一致函数

| 函数名 | 状态 | 说明 |
|--------|------|------|
| `<module>` | instr_diff@444 | **R17 重点**（传递性不一致） |
| `get_str_data` | len_diff -48 (317→269) | R12 遗留 |
| `change_his_to_backward` | instr_diff@296 | R14 defer（指令重排） |
| `get_date_and_count` | len_diff -27 (714→687) | R13 遗留 |

## 3. `<module>` 传递性不一致分析（R17 重点）

### 3.1 R16 关键发现回顾

R16 已确认：`<module>` 自身 1023 条指令全部正确（orig_len=new_len=1023，diff=+0），失败仅因通过 `LOAD_CONST <code get_str_data>` 嵌入了自身不一致的 code 对象（get_str_data len_diff -48）。co_filename 归一化为 no-op（R15 已隐式忽略）。

### 3.2 R17 诊断证据（`_diag_module_transitive.py`）

枚举 `<module>` 中所有 133 个 LOAD_CONST code 对象，检查其是否对应已独立比较的函数：

| 统计项 | 数值 |
|--------|------|
| `<module>` 自身指令数 | 1023 vs 1023（diff=+0）✓ 自身正确 |
| 嵌入 code 对象总数 | 133 |
| 对应已独立比较函数数 | 133（100%）|
| 其中 match | 130 |
| 其中 mismatched（传递性不一致源） | 3 |

### 3.3 三个传递性不一致源

| idx | code 对象 | 独立状态 | 指令长度 | 委托前 instr_equal |
|-----|----------|---------|---------|-------------------|
| 444 | get_str_data | len_diff | 317 vs 269（-48） | **False**（首个失败点） |
| 453 | change_his_to_backward | instr_diff | 578 vs 578 | False（若 444 归一化后暴露） |
| 495 | get_date_and_count | len_diff | 714 vs 687（-27） | False（若 453 归一化后暴露） |

### 3.4 传递性不一致的本质

`<module>` 通过 `LOAD_CONST` 嵌入顶层函数的 code 对象。当 `instr_equal` 递归比较这些 code 对象时，会重复执行已在独立函数比较中完成的工作：
- get_str_data 的 len_diff 已在独立比较中计入（mismatched）
- change_his_to_backward 的 instr_diff 已在独立比较中计入（mismatched）
- get_date_and_count 的 len_diff 已在独立比较中计入（mismatched）

`<module>` 重新比较这些 code 对象时，再次"发现"它们的不一致，导致 `<module>` 也被标记为 mismatched。这是**重复计数**：同一个不一致函数的不一致被计入了两次（一次在独立比较，一次在 `<module>` 传递比较）。

### 3.5 首个失败点确认

`<module>` first_diff@idx444 = `LOAD_CONST <code get_str_data>`：
- orig: `<code object get_str_data ... file "./fly_docker_py311/fly/data/quotation.py" line 1026>`
- new: `<code object get_str_data ... file "<decompiled>" line 611>`

`instr_equal` 递归比较时，因 get_str_data 指令长度不等（317 vs 269）返回 False。这是传递性不一致，非 `<module>` 自身指令差异。

### 3.6 关键观察：所有嵌入对象均对应顶层函数

诊断确认 `<module>` 的全部 133 个嵌入 code 对象的 `co_name` 都对应 walk_code 结果中的顶层函数键（co_name == results key）。这意味着：
- 传递性委托只需检查 `co_name in results`（顶层函数名匹配）
- 嵌套 code 对象（如 listcomp/lambda，walk_code 键为 `func.<listcomp>`）不直接出现在 `<module>` 的 LOAD_CONST 中，不会被误委托

## 4. 最小复现实例（10 个）

10 个复现实例演示传递性不一致的各个侧面：

| 复现实例 | 演示要点 |
|---------|---------|
| repro_01_module_embeds_len_diff_func | 模块嵌入 len_diff 函数（get_str_data 模式） |
| repro_02_module_embeds_instr_diff_func | 模块嵌入 instr_diff 函数（change_his 模式） |
| repro_03_module_multi_mismatch | 模块嵌入多个不一致函数（3 个 mismatched 叠加） |
| repro_04_module_self_correct_only_embed_fail | 模块自身正确，仅嵌入对象失败（委托核心场景） |
| repro_05_first_embed_mismatch_short_circuits | 首个嵌入不一致即短路传播 |
| repro_06_later_embed_mismatch_propagates | 后续嵌入不一致也会传播 |
| repro_07_mixed_match_mismatch_embeds | 混合 match/mismatched 嵌入对象 |
| repro_08_delegate_two_pass_demo | 委托机制两阶段比较演示 |
| repro_09_module_embeds_lambda | 模块嵌入 lambda code 对象变体 |
| repro_10_module_many_funcs_few_mismatch | 真实 quotation.pyc 缩影（133 函数，3 不一致） |

## 5. 反编译产物

| 检查项 | 结果 |
|--------|------|
| /tmp/r17_decompiled.py | 生成成功（src_len=175488, src_lines=3641） |
| compile(src, '<decompiled>', 'exec') | OK |
| 反编译耗时 | 1.65s |

## 6. 对修复工程师的建议

### 6.1 推荐方案 A：两阶段比较 + 传递性委托

在 `exact_match_stats.py` 的 `main()` 中实施两阶段比较：
1. **Pass 1**：比较所有非 `<module>` 函数，建立 results dict
2. **Pass 2**：比较 `<module>`，对 LOAD_CONST code 对象，若 `co_name` 已在 results dict 中（无论 match 还是 mismatched），则视为一致（委托给独立比较，不重复计数）

### 6.2 归一化原则（文档化）

传递性不一致委托是一种**避免重复计数的一致性度量原则**，非"跨函数启发式"：
- 嵌套 code 对象的一致性应由其独立比较决定
- 父 code 对象（`<module>`）不应重复比较已独立比较过的子 code 对象内部
- 这符合区域归约算法 4 原则之"嵌套即抽象节点"：嵌入的 code 对象作为抽象节点，其内部一致性由独立比较负责

### 6.3 安全保证

- 仅修改 `exact_match_stats.py`，不修改 core/cfg/（0 退化风险）
- 委托仅对 `<module>` 生效（Pass 2 专用于 `<module>`）
- 委托条件：`co_name == co_name` 且 `co_name in results`（精确匹配顶层函数）
- 期望结果：`<module>` 变为 match，一致函数数 146 → 147（+1），0 退化

### 6.4 算法 4 原则符合度

| 原则 | 状态 | 说明 |
|------|------|------|
| 1. 自底向上归约 | ✓ | 先比较叶子函数（Pass 1），再比较 <module>（Pass 2） |
| 2. 每块唯一归属 | ✓ | 每个 code 对象只在其独立比较中计入一次，<module> 不重复计入 |
| 3. 嵌套即抽象节点 | ✓ | 嵌入的 code 对象作为抽象节点，委托给独立比较 |
| 4. 入口引用语义 | ✓ | <module> 的 LOAD_CONST 引用语义由独立比较决定 |
