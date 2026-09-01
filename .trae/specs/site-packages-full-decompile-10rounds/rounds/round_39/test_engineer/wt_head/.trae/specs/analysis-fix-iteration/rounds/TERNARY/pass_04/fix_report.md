# Pass 4 TERNARY 修复报告

## 修复内容

### Fix 1: 为 `_is_ternary_block` 内 `('RETURN_VALUE', 'RETURN_CONST')` 字面量添加已知反模式标记

**问题位置**：`/workspace/core/cfg/region_analyzer.py` `_is_ternary_block` 嵌套函数（L11720-L11730，位于 `_identify_ternary_regions` 内）

**问题根因**（Pass 1-3 已识别但未处理）：
`_is_ternary_block` 内有两处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量（原 L11722 / L11730），与模块级常量 `RETURN_TERMINATOR_OPS`（L54 定义，`frozenset({'RETURN_VALUE', 'RETURN_CONST'})`）重复。

- Pass 1 test_findings §反模式检查 已识别：「实例驱动判据散布 10+ 处: ... RETURN_VALUE/RETURN_CONST 6处」
- Pass 1 修复 2 已将 5 处 RETURN 字面量替换为 `RETURN_TERMINATOR_OPS` 常量，但 `_is_ternary_block` 内 2 处同模式字面量未在 Pass 1 范围内
- Pass 2/3 评估后 deferred，理由：「字面量→常量替换属纯重构（frozenset 等价），不在删除死代码/同步 docstring/标记反模式三类仅做清单内」

**修复策略**：
本轮以「添加注释标记已知反模式」名义处理——在首处字面量前添加 `[Pass4-TERNARY]` 注释，明确登记：
1. 两处字面量为实例驱动判据（DRY 违背）
2. 应替换为模块级常量 `RETURN_TERMINATOR_OPS`（L54）
3. Pass 1-3 的 deferred 历史
4. 后续替换需评估 frozenset 与 tuple 的 `in` 语义等价性（`x in frozenset` 与 `x in tuple` 均为成员检测，语义等价）

不触及任何可执行代码，控制流不变。

**为什么不直接替换**：
Pass 2/3 已明确字面量→常量替换属纯重构，不在「仅做」清单内。本轮严格遵循保守策略——仅添加注释标记，把替换留给后续 Pass 以「重复代码消除」名义统一处理（避免本轮单独打破 Pass 2/3 的约束先例）。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py TERNARY
```
**结果**：`69 7 0 76 5.2 TERNARY files=80` —— 与基线一致（69 passed, 7 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 实例驱动判据（DRY 违背） | **已标记**（`_is_ternary_block` 两处 RETURN 字面量登记为已知反模式，待后续替换为 RETURN_TERMINATOR_OPS） |

## 未完成项

1. **`_is_ternary_block` 内 2 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量→`RETURN_TERMINATOR_OPS` 替换**（本轮已标记，待后续 Pass 以「重复代码消除」名义实施）
2. **7 例预存失败**（ternary 值被外层表达式消费的模式：assert method call / listcomp body / await call arg / for-iter subscript / compare in both / tuple-unpack / starred-list scalar）：需针对各自消费模式单独设计，非保守修复范围
3. **BOOLOP→TERNARY 识别顺序调换**（Pass 1 已明确为高风险）：影响全流水线
4. **`_detect_ternary_pattern` / `_generate_ternary` 函数过长**（~1600 / ~3000 行，Pass 1 已登记）：可维护性改进

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_is_ternary_block` L11720 添加 `[Pass4-TERNARY]` 反模式标记注释）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/TERNARY/pass_04/fix_report.md`（本报告）
