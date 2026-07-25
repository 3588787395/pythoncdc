# 修复实施报告 — TERNARY Pass 03

## 概览

本轮为 Pass 3 第 21 轮（TERNARY 区域）保守修复。架构工程师分析聚焦于
`_generate_ternary` 内 `func_call_skip` 计算段的死代码识别，发现 1 个明确的
无副作用死代码块。已删除，未改变任何控制流。

| 修复 | 状态 | 风险 | 说明 |
|------|------|------|------|
| Fix 1 — 删除 `_generate_ternary` 内 LOAD_ATTR 内层重赋值死代码块 | ✅ 已实施 | 极低 | 内层 `if obj_i.opname.startswith('LOAD_'): func_call_skip = push_null_idx + 2` 与外层已设置的值完全相同，`obj_i` 仅在该死块内引用，纯死代码删除 |

## 编译验证

`python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` → OK，
退出码 0，无异常。

## 反模式自检

- ✅ 无 `def _fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法名（未新增任何函数）
- ✅ 无硬编码深度上限
- ✅ 无新增后处理补丁
- ✅ 未改变控制流（仅删除 4 行死代码 + 添加 5 行说明注释）
- ✅ 未修改测试文件
- ✅ 未引入反模式注释标记（本轮无符合「已知反模式」的可标记位置）

---

## Fix 1 — 删除 `_generate_ternary` 内 LOAD_ATTR 内层重赋值死代码块

### 文件 / 位置
`/workspace/core/cfg/region_ast_generator.py` `_generate_ternary` 方法内
`func_call_skip` 计算段（原 L18546-L18551）

### 问题
原代码结构：
```python
if next_i.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF', 'LOAD_ATTR'):
    func_call_skip = push_null_idx + 2                          # 外层赋值
    if next_i.opname == 'LOAD_ATTR' and push_null_idx > 0:     # 内层特例
        obj_i = cond_instrs_raw[push_null_idx - 1]
        if obj_i.opname.startswith('LOAD_'):
            func_call_skip = push_null_idx + 2                  # 与外层完全相同
```

判据分析：
1. **外层赋值（L18547）**：对任何 `LOAD_*` 操作码（含 LOAD_ATTR）无条件设置
   `func_call_skip = push_null_idx + 2`。
2. **内层赋值（L18551）**：仅在 `LOAD_ATTR` 且 `push_null_idx > 0` 且前一条指令
   是 `LOAD_*` 时，将 `func_call_skip` 重设为 `push_null_idx + 2` —— **与外层
   完全相同的值**。
3. **`obj_i` 变量**：grep 全文确认 `obj_i`（注意：区别于 `obj_instrs` /
   `obj_expr` / `_obj_i` / `func_obj_info` 等不同标识符）仅在 L18549-L18550
   该死块内被引用，删除后无悬挂引用。
4. **副作用**：内层块仅执行 `cond_instrs_raw[push_null_idx - 1]` 读取与
   `func_call_skip` 重赋值（同值），无其他状态修改、无 break/continue/return。

### 修复
删除内层 4 行死代码块（L18548-L18551），保留外层赋值。在删除位置添加 5 行
注释说明删除原因与安全性依据，便于后续审计追溯。

修复后：
```python
if next_i.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_FAST', 'LOAD_DEREF', 'LOAD_ATTR'):
    # [Pass3-TERNARY] 移除原 LOAD_ATTR 内层重赋值死代码块：
    # 内层 `if obj_i.opname.startswith('LOAD_'): func_call_skip =
    # push_null_idx + 2` 与外层上一行已设置的值完全相同，无副作用。
    # `obj_i` 局部变量仅在该死块内引用（grep 确认无其他使用点），
    # 一并删除。属纯死代码删除，控制流与 func_call_skip 取值不变。
    func_call_skip = push_null_idx + 2
```

### 风险评估
- **行为等价性**：`func_call_skip` 在所有路径下取值与原代码一致
  （LOAD_ATTR 路径下，内层重赋值不改变外层已设的值）。
- **控制流**：未删除任何 break/continue/return，仅删除一个永真同值赋值。
- **变量作用域**：`obj_i` 为方法内局部变量，仅在该块引用，无悬挂引用。

## 回归测试

`timeout 290 python /workspace/.trae/specs/analysis-fix-iteration/run_region_tests.py TERNARY`

| 套件 | 基线 | 修复后 | 状态 |
|------|------|--------|------|
| TERNARY | 69p/7f/76 | 69p/7f/76 | ✅ 不退化 |

7 个失败用例（ternary 值被外层表达式消费的模式）与 Pass 01/02 一致，本轮
死代码删除未改变任何识别/生成逻辑，符合预期。

## 分析过程说明（架构工程师视角）

### 已排查但未采纳的方向

1. **`_is_ternary_block` 内 `('RETURN_VALUE', 'RETURN_CONST')` 字面量未替换为
   `RETURN_TERMINATOR_OPS`**（region_analyzer.py L11718 / L11726）：
   Pass 02 报告已识别但未采纳，理由是「字面量→常量替换属纯重构，不在
   Pass 2「仅做」清单内」。本轮 Pass 3 仍维持同一保守策略——该替换虽
   frozenset 等价、行为不变，但严格不属于「删除死代码 / 同步 docstring /
   标记已知反模式」三类之一，故未采纳，留待后续 Pass 以「重复代码消除」
   名义处理。

2. **`_generate_ternary` 内 `_nested_cond_expr` / `_nested_true_expr` /
   `_nested_false_expr` 三变量初始化**：均有后续消费点（L18500-L18507），
   非死代码。

3. **已知反模式标记**：未在 TERNARY 区域代码中发现需标记的已知反模式
   （无 `_fix_`/`_patch_` 前缀、硬编码深度、后处理补丁等）。

### 为何本轮仅 1 项死代码修复

TERNARY 区域经多轮迭代（R2-R20 + Pass 01 + Pass 02），核心识别与生成逻辑
高度稳定。Pass 01 已完成 helper 抽取与模块级常量化，Pass 02 已同步 2 处
docstring。本轮在 `_generate_ternary` 的 PUSH_NULL/LOAD_ATTR 前缀检测段
发现 1 个明确的死代码块，属典型「重构遗留」（疑似早期版本 LOAD_ATTR 路径
曾有不同 `func_call_skip` 取值，后统一为 `push_null_idx + 2` 后内层块未
同步清理）。删除后行为完全等价。

## 实施约束合规性

- ✅ 禁止反模式：无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法名
- ✅ 禁止硬编码深度上限
- ✅ 禁止新增后处理补丁
- ✅ 最小修改原则：仅删除 4 行死代码 + 添加 5 行说明注释
- ✅ 不修改测试文件
- ✅ 不改变控制流
- ✅ 编译验证通过
- ✅ 回归测试不退化（69p/7f/76 与基线一致）

## 修改文件

- `core/cfg/region_ast_generator.py`（Fix 1：删除 4 行死代码 + 添加 5 行注释）

## 后续迭代建议（本轮未做）

- `_is_ternary_block` 内 2 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量→
  `RETURN_TERMINATOR_OPS` 常量替换（纯重构，待后续 Pass 以「重复代码消除」
  名义处理）
- 7 个 TERNARY 失败用例的修复需针对各自的表达式消费模式（assert method call /
  listcomp body / await call arg / for-iter subscript / compare in both /
  tuple-unpack / starred-list scalar）单独设计，非本轮保守修复范围
