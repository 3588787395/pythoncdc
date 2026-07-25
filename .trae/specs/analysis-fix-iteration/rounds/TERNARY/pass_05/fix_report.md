# Pass 5 TERNARY 修复报告

## 修复内容

### Fix 1: 替换 `_is_ternary_block` 内 2 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量为 `RETURN_TERMINATOR_OPS` 常量（Pass 4 deferred 的「重复代码消除」）

**问题位置**：`/workspace/core/cfg/region_analyzer.py:11752, 11760`（`_is_ternary_block` 内的两处成员检测，原 L11744/L11752）

**问题根因**（Pass 4 TERNARY fix_report.md §未完成项 1 明确 deferred）：
Pass 4 在 `_is_ternary_block` 添加 `[Pass4-TERNARY]` 标记注释，识别出 2 处
`('RETURN_VALUE', 'RETURN_CONST')` 字面量为实例驱动判据（DRY 违背），并明确 deferred：

> 1. **`_is_ternary_block` 内 2 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量→`RETURN_TERMINATOR_OPS` 替换**
>    （本轮已标记，待后续 Pass 以「重复代码消除」名义实施）

模块级常量 `RETURN_TERMINATOR_OPS = frozenset({'RETURN_VALUE', 'RETURN_CONST'})`（L54 定义）
已存在并已在文件其他位置使用（L12204/L12216/L12259 `_block_is_return_body` 等嵌套函数内），
但 `_is_ternary_block` 仍用字面量重复定义。

**修复策略**：
按 Pass 4 deferred 计划，实施「重复代码消除」替换：
1. L11744（现 L11752）`if ft_last and ft_last.opname in ('RETURN_VALUE', 'RETURN_CONST'):`
   → `if ft_last and ft_last.opname in RETURN_TERMINATOR_OPS:`
2. L11752（现 L11760）`cs.get_last_instruction().opname in ('RETURN_VALUE', 'RETURN_CONST')`
   → `cs.get_last_instruction().opname in RETURN_TERMINATOR_OPS`

同时追加 `[Pass5-TERNARY]` 段落说明完成情况与语义等价性验证。

**语义等价性证明**：
- `x in tuple` 与 `x in frozenset` 均为成员检测，当 x 为 hashable 字符串时两者语义
  完全等价（frozenset 略快 O(1)，但 2 元素差异可忽略）
- `RETURN_TERMINATOR_OPS` 已在 L12204/L12216/L12259 等同文件位置使用，本替换使
  `_is_ternary_block` 与之一致
- 编译期与运行期行为完全不变（True/False 结果在替换前后完全一致）

控制流不变，仅把字面量替换为已存在的模块级常量。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py TERNARY
```
**结果**：`69 7 0 76 5.5 TERNARY files=80` —— 与基线一致（69 passed, 7 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（字面量→常量替换，`in` 语义等价） |
| 测试文件修改 | 未修改任何测试文件 |
| 实例驱动判据（DRY 违背） | **已消除 2 处**（`_is_ternary_block` 内 2 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量替换为 `RETURN_TERMINATOR_OPS` 模块级常量，与 L12204/L12216/L12259 等位置一致） |

## 未完成项

1. **文件其他位置 50+ 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量**未替换（本轮仅替换
   Pass 4 标记的 `_is_ternary_block` 内 2 处）。全量替换需逐处评估语义等价性（部分位置
   可能在条件链中与其他 op 联合判定，需谨慎），留待后续 Pass 统一处理。
2. **7 例预存失败**（ternary 值被外层表达式消费的模式：assert method call / listcomp body
   / await call arg / for-iter subscript / compare in both / tuple-unpack / starred-list scalar）：
   需针对各自消费模式单独设计，非保守修复范围
3. **BOOLOP→TERNARY 识别顺序调换**（Pass 1 已明确为高风险）：影响全流水线
4. **`_detect_ternary_pattern` / `_generate_ternary` 函数过长**（~1600 / ~3000 行，Pass 1 已登记）：
   可维护性改进

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_is_ternary_block` L11752/L11760 字面量→`RETURN_TERMINATOR_OPS` 替换 + 追加 [Pass5-TERNARY] 段落）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/TERNARY/pass_05/fix_report.md`（本报告）
