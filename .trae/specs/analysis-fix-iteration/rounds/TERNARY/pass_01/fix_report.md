# 修复实施报告 — TERNARY Pass 01

## 概览

| 修复 | 状态 | 风险 | 说明 |
|------|------|------|------|
| Fix 1 — 抽取 `_is_value_block_nested_if_header` 局部 helper | ✅ 已实施（适配） | 极低 | 消除 3 处重复；helper 判据适配为指令特征（非 IfRegion 归属），见下文 |
| Fix 2 — 抽取 `RETURN_TERMINATOR_OPS` / `TERMINAL_JUMP_OPS` 模块级常量 | ✅ 已实施 | 极低 | 纯重构，行为不变；常量名 `TERMINAL_JUMP_OPS` 替代 `PURE_JUMP_OPS`（名称冲突） |
| Fix 3 — `_is_call_without_value_used` 增加 IfRegion 抢占判据 | ❌ 已回退 | 中 | 实施后验证：1 处回归 + 0 处改进，依规回退 |

## 最终回归结果（Fix 1+2，Fix 3 已回退）

| 套件 | 基线 | 修复后 | 状态 |
|------|------|--------|------|
| TERNARY | 69p/7f/76 | 69p/7f/76 | ✅ 不退化 |
| BOOLOP | 79p/0f/79 | 79p/0f/79 | ✅ 不退化 |
| IF（有界 80） | 79p/1f/80 | 79p/1f/80 | ✅ 不退化 |
| IF（全量 826） | 31f/787p | 31f/787p | ✅ 不退化 |

**TERNARY 失败用例修复情况：未从 69/76 提升。** 7 个失败用例均为 ternary 值被外层表达式消费的模式（assert/listcomp/await/for-iter/compare/tuple-unpack/starred-list），无一是 `print(ternary)` 类 CALL+POP_TOP 模式，Fix 3 对它们无效。

## 编译检查
`python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` → OK，无异常。

## 反模式自检
- 无 `def _fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法名（grep 空）
- 无硬编码深度上限
- 无新增后处理补丁
- RETURN 字面量在 TERNARY 区域内已全部替换为 `RETURN_TERMINATOR_OPS`（区域外 5 处属其他 region 识别代码，不在本轮范围）
- 4 元素纯跳转列表在 TERNARY 区域内已全部替换为 `TERMINAL_JUMP_OPS`（区域外 3 处 `L1819/L1914/L4480` 属 loop region 代码，不在本轮范围）

---

## Fix 1 — 抽取 `_is_value_block_nested_if_header` 局部 helper

### 文件 / 位置
`/workspace/core/cfg/region_analyzer.py`
- helper 定义：L12197-L12216（`_detect_ternary_pattern` 内嵌套）
- 3 处替换：L12347 / L12353 / L12361

### 关键决策：判据适配（偏离任务 spec 的 helper 代码）

任务 spec 的 helper 代码基于 **IfRegion 归属判据**（`block_to_region[vb] is IfRegion and entry==vb`）。但经分析 `analyze()` 主流程（L1240-L1404）的 Phase 顺序：

```
Phase 1: try/loop/with/match/assert regions
Phase 2: chained_compare → boolop → ternary → conditional(=IfRegion)
                                                ↑ IfRegion 在此创建
```

`_identify_ternary_regions`（L1287）**早于** `_identify_conditional_regions`（L1396，创建 IfRegion）。故 TERNARY Pass 调用时 `block_to_region` 中**尚无 IfRegion**。若按 spec helper 实施：
- `_is_value_block_nested_if_header` 恒返回 False
- R19 Bug 22-24 修复（防止 if-elif-else 条件头被误归约为 ternary）完全失效
- 9 分支 if-elif-else 退化为 6 裸 return（回归）

任务 spec 的**约束优先级**明确：「语义必须等价」+「不引入回归」+「极低风险」高于 helper 代码示例。故**保留原指令特征判据**以维持语义等价，仅消除 3 处重复实现：

```python
def _is_value_block_nested_if_header(vb):
    if vb is None:
        return False
    _vb_last = vb.get_last_instruction()
    if not (_vb_last and _vb_last.opname in (
            FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS)):
        return False
    for _succ in vb.conditional_successors:
        _succ_last = _succ.get_last_instruction()
        if _succ_last and _succ_last.opname in RETURN_TERMINATOR_OPS:
            return True
    return False
```

代码内已加详细注释说明此决策。3 处调用：
- L12347: `false_is_ternary = not _is_value_block_nested_if_header(true_block)`
- L12353: `if _is_value_block_nested_if_header(true_block): false_is_ternary = False`
- L12361: `if any(_is_value_block_nested_if_header(s) for s in false_succs): false_is_ternary = False`

IfRegion 类在文件顶部 L321 定义，同文件内可直接访问。

---

## Fix 2 — 抽取模块级常量

### 文件 / 位置
`/workspace/core/cfg/region_analyzer.py` L53-L61（在 `SHORT_CIRCUIT_JUMP_OPS` 后新增）

### 关键决策：常量名 `TERMINAL_JUMP_OPS`（非 `PURE_JUMP_OPS`）

任务 spec 指定常量名 `PURE_JUMP_OPS`，但该名称**已存在**于 L68：
```python
PURE_JUMP_OPS = NOISE_OPS | frozenset({'POP_TOP', 'JUMP_FORWARD', 'JUMP_ABSOLUTE', 'LOAD_CONST'})
```
语义为「可忽略指令集」（含 NOISE/POP_TOP/LOAD_CONST），被 7 处其他代码引用（L3648/L3682/L3789/L3819/L3931/L10906/L10953）。若重定义会破坏这些引用。

故采用新名 `TERMINAL_JUMP_OPS`（仅 4 个纯跳转指令，无栈效果），并在常量定义处加注释说明与 `PURE_JUMP_OPS` 的语义区别。

### 新增常量
```python
RETURN_TERMINATOR_OPS = frozenset({'RETURN_VALUE', 'RETURN_CONST'})

TERMINAL_JUMP_OPS = frozenset({
    'JUMP_FORWARD', 'JUMP_ABSOLUTE',
    'JUMP_BACKWARD', 'JUMP_BACKWARD_NO_INTERRUPT',
})
```

### 替换明细（共 11 处，含 1 处任务 spec 未列出但同模式的）
**RETURN 字面量（5 处）：**
- L12159 `_block_is_return_body`: `last.opname not in RETURN_TERMINATOR_OPS`
- L12171 `_block_ends_with_return`: `last.opname in RETURN_TERMINATOR_OPS`
- L12214 `_is_value_block_nested_if_header`（Fix 1 helper 内）: `_succ_last.opname in RETURN_TERMINATOR_OPS`
- 原 L12316/L12330/L12347 三处 R19 Bug 重复 → 已由 Fix 1 helper 消除

**纯跳转列表（6 处，spec 列 5 处 + 1 处 `_is_call_without_value_used` 内同模式）：**
- L12179 `_is_call_without_value_used`: `effective[-1].opname in TERMINAL_JUMP_OPS`（spec 未列出，但属同模式重复，随 Fix 1 helper 编辑一并替换）
- L12308 `_ft_is_pure_jump`: `i.opname in TERMINAL_JUMP_OPS`
- L12501 `_ft_pure_jump`: `i.opname in TERMINAL_JUMP_OPS`
- L12591 `_ft_pure_jump_nest`: `i.opname in TERMINAL_JUMP_OPS`
- L12625 `_follow_pure_jumps`: `eff[0].opname in TERMINAL_JUMP_OPS`
- L14399 `_is_fused_ternary_false_value_block` 的 `ft_is_pure_jump`: `i.opname in TERMINAL_JUMP_OPS`

行为不变（frozenset 等价），纯重构。

---

## Fix 3 — `_is_call_without_value_used` 增加 IfRegion 抢占判据（已回退）

### 实施与验证过程
1. 按 spec 实施：在 CALL+POP_TOP 命中时，检查 `block_to_region[blk]` 是否为 IfRegion 且 entry==blk；若是则 `return True`（拒绝 ternary），否则 `return False`（允许 ternary）。
2. 编译检查通过。
3. 有界回归：TERNARY 69p/7f/76（无变化）、IF 79p/1f/80（无变化）。
4. 全量 IF 套件对比（826 文件）：
   - 基线（无 Fix 3）：31 failed / 787 passed
   - 含 Fix 3：32 failed / 786 passed
   - **回归 1 处**：`test_adv20_nonlocal_multi_in_elif_branches`（基线通过 → Fix 3 失败）
   - **改进 0 处**：7 个 TERNARY 失败用例无变化

### 回归根因
若 Region 在 `_identify_conditional_regions`（L1396）中创建，**晚于** `_identify_ternary_regions`（L1287）。Fix 3 的 IfRegion 归属检查在 TERNARY Pass 调用时**恒为 False**，使原 CALL+POP_TOP 拒绝逻辑（`return True`）被禁用（改为 `return False`）。`if c: f() else: g()` 类含 CALL+POP_TOP 语句体的 if-else 不再被拒绝，被误归约为 TernaryRegion。

### 无效根因
7 个 TERNARY 失败用例均为 ternary 值被外层表达式消费模式，无一为 `print(ternary)` / CALL+POP_TOP 模式：
- `test_r17_ternary_assert_test_method`: `assert (a if c else b).method()`
- `test_r17_ternary_listcomp_body_and_if`: `[(a if c else b) for x in y if (d if e else f)]`
- `test_r18_ternary_await_call_ternary_arg`: `await g(a if c else b)`
- `test_r18_ternary_for_iter_subscr`: `for x in y[(a if c else b)]:`
- `test_r19_ternary_compare_in_both_ternary`: `x = (a if c else b) in (d if e else f)`
- `test_r19_ternary_tuple_unpack_one_ternary`: `x, y = c, (a if d else b)`
- `test_r20_ternary_starred_list_scalar`: `x = [*[a if c else b]]`

Fix 3 对它们无影响。

### 回退操作
依任务 spec「若验证后发现回归或无效，回退此修复（仅保留修复 1+2）」，已将 `_is_call_without_value_used` 恢复为原始逻辑（CALL+POP_TOP 命中即 `return True`）。

回退后再次验证：TERNARY 69p/7f/76、BOOLOP 79p/0f/79、IF 79p/1f/80，全量 IF 31f/787p，均匹配基线。

---

## 实施约束合规性
- ✅ 禁止反模式：无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法名
- ✅ 禁止硬编码深度上限
- ✅ 禁止新增后处理补丁
- ✅ 最小修改原则：仅修改 `region_analyzer.py` 一个文件
- ✅ 不修改测试文件
- ✅ 不调换 BOOLOP/TERNARY 识别顺序
- ✅ 不 commit / push

## 后续建议（不在本轮范围）
- Fix 3 若要真正修复 `print(ternary)` 类用例，需先调整 Phase 顺序使 IfRegion 先于 TERNARY 识别（高风险，涉及多 Pass 协调），或改用其他不依赖 IfRegion 归属的判据
- 7 个 TERNARY 失败用例的修复需针对各自的表达式消费模式（assert method call / listcomp / await / subscript / compare / unpack / starred）单独设计，非本轮 3 项修复所能覆盖
- `PURE_JUMP_OPS`（L68）与 `TERMINAL_JUMP_OPS`（L58）名称易混淆，后续可考虑重命名 `PURE_JUMP_OPS` 为 `IGNORABLE_OPS` 以消除歧义
