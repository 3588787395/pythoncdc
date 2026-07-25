# Pass 6 TERNARY 修复报告

## 修复内容

### Fix 1: 同步 Pass4-TERNARY 标记中过时的「下方 L11722 与 L11730 两处」行号引用

**问题位置**：`/workspace/core/cfg/region_analyzer.py:11779-11793`（`_is_ternary_block`
内 Pass4-TERNARY / Pass5-TERNARY 标记注释段后追加 [Pass6-TERNARY] 段落）

**问题根因**（与 Pass6-BOOLOP / Pass6-MATCH / Pass6-ASSERT / Pass6-WITH / Pass6-TRY
同型行号漂移）：
Pass4-TERNARY 在 `_is_ternary_block` 内标记两处 `('RETURN_VALUE', 'RETURN_CONST')`
字面量 DRY 违背时，写入：
```
# [Pass4-TERNARY] 已知反模式标记：下方 L11722 与 L11730 两处
# `('RETURN_VALUE', 'RETURN_CONST')` 字面量为实例驱动判据（DRY
# 违背），应替换为模块级常量 RETURN_TERMINATOR_OPS（L54 定义，...
```

Pass5-TERNARY 完成替换（字面量 → `RETURN_TERMINATOR_OPS`）并追加 [Pass5-TERNARY]
段落约 7 行后，原两处字面量（现 `RETURN_TERMINATOR_OPS` 用法）行号下移至 L11796 /
L11804（grep 验证）。Pass4-TERNARY marker 中的 L11722/L11730 引用与实际严重不符。

经 `git show dd2d4bb:core/cfg/region_analyzer.py | grep -n "in ('RETURN_VALUE', 'RETURN_CONST')"`
确认 Pass5-TERNARY 写入前 `_is_ternary_block` 内两处字面量实际位于 L11752 / L11760
（与 Pass5-TERNARY fix_report 描述「L11744（原）/L11752（现）」、「L11752（原）/L11760
（现）」一致）。Pass4-TERNARY marker 中「L11722/L11730」与 Pass5 fix_report 描述
「L11744/L11752（原）」均有偏差，存疑。

**修复策略**（与 Pass6-BOOLOP/MATCH/ASSERT 同型——仅注释文本同步 + 改用 grep 验证
+ 相对位置描述）：
保留原 Pass4-TERNARY / Pass5-TERNARY 注释文本不变（历史追溯用），追加
`[Pass6-TERNARY]` 段落，说明：
1. Pass4-TERNARY 引用「下方 L11722 与 L11730 两处」经 Pass5 替换 + 追加 [Pass5-TERNARY]
   段落后已下移
2. **不再引用具体行号**——改为 grep 验证 + 相对位置描述（避免递归漂移）：
   - 首处：本函数 `_is_ternary_block` 内 `if fallthrough is not None:` 之后
     `ft_last.opname in RETURN_TERMINATOR_OPS`
     （grep `ft_last and ft_last.opname in RETURN_TERMINATOR_OPS` 在本文件仅 1 处命中）
   - 次处：本函数内 `all(... for cs in s.conditional_successors)` 中
     `cs.get_last_instruction().opname in RETURN_TERMINATOR_OPS`
     （grep 该串在本文件仅 1 处命中）
3. 原 Pass 4 引用 L11722/L11730 与 Pass5 fix_report 描述 L11744/L11752（原）/L11752/L11760
   （现）均有偏差，本轮不再追究

**为什么不引用具体行号**（与 Pass5-TERNARY 不同）：
与 Pass6-BOOLOP/MATCH/ASSERT 同型思路——每轮上游修改都会使行号继续漂移。本轮
Pass6-TERNARY 改用 grep 验证 + 相对位置描述方式，从根因上消除漂移源。

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py TERNARY
```
**结果**：`69 7 0 76 5.4 TERNARY files=80` —— 与基线一致（69 passed, 7 预存失败,
0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用（Pass4-TERNARY 同型） | **已同步**（追加 [Pass6-TERNARY] 段落，改用 grep 验证 + 相对位置描述避免递归漂移） |

## 未完成项

1. **文件其他位置 50+ 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量**未替换（Pass5-TERNARY
   已替换 `_is_ternary_block` 内 2 处，本轮同步行号引用；余 44+ 处待统一替换）：
   全量替换需逐处评估语义等价性，留待后续 Pass 统一处理。
2. **7 例预存失败**（ternary 值被外层表达式消费的模式：assert method call / listcomp body
   / await call arg / for-iter subscript / compare in both / tuple-unpack / starred-list scalar）：
   需针对各自消费模式单独设计，非保守修复范围。
3. **BOOLOP→TERNARY 识别顺序调换**（Pass 1 已明确为高风险）：影响全流水线。
4. **`_detect_ternary_pattern` / `_generate_ternary` 函数过长**（~1600 / ~3000 行，Pass 1
   已登记）：可维护性改进。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_is_ternary_block` 内 Pass4-TERNARY
  标记追加 [Pass6-TERNARY] 同步段落，改用 grep 验证 + 相对位置描述避免递归漂移）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/TERNARY/pass_06/fix_report.md`（本报告）
