# Pass 8 TERNARY 修复报告

## 修复内容

### Fix 1: 同步 `_generate_ternary` docstring 中「字节码一致性状态：截至 Pass 01」表述

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:18561-18581`
（`_generate_ternary` 方法 docstring「字节码一致性约束」节末段追加 [Pass8-TERNARY] 校正段落）

**问题根因**（与 Pass3-BOOLOP 在 `_generate_boolop` docstring 同步测试状态同型「过时时点表述」）：

`_generate_ternary` docstring「字节码一致性约束」节末段原文：
```
- 字节码一致性状态：存在已知失败（截至 Pass 01: TERNARY 69p/7f/76）。
  7 个失败用例为 ternary 值被外层表达式消费的模式，详见 TERNARY
  Pass 01 报告。历史问题 test_tn20/tn21（`a if a and b else 0`）已
  解决：根因在 _identify_ternary_regions 的 BoolOpRegion 抢占 +
  skip_ternary=True 守卫，Phase 5 修复了 IfRegion 对简单三元的过度
  抢占，BoolOp 条件链由 _build_ternary_boolop_condition 精确重建，
  短路语义完整保留。
```

其中「截至 Pass 01: TERNARY 69p/7f/76」表述仅引用 Pass 01 时点状态、
未说明 Pass 2-7 期间无回归变化，可能误读为「Pass 01 后状态已变」。

**对称缺失**（Pass3-BOOLOP 已在 `_generate_boolop` docstring 同步同型问题）：

`_generate_boolop` docstring（region_ast_generator.py L17672-L17680）中 Pass3-BOOLOP
已对同型「字节码一致性状态」表述追加了 `[Pass3-BOOLOP]` 校正段落：
```
- 字节码一致性状态：[Pass3-BOOLOP] 同步与实际测试状态一致——bool_op +
  boolop 共 153 用例（151 passed / 1 failed / 1 skipped）...
```

但 `_generate_ternary` docstring 中的同型「截至 Pass 01」表述**未校正**——
对称缺失。截至 Pass 7，应同步 Pass 2-7 期间的状态变化（实际为无变化）。

**修复策略**（与 Pass3-BOOLOP 同型——保留原表述作历史追溯，追加校正段落）：

保留原「截至 Pass 01: TERNARY 69p/7f/76」表述作历史追溯，追加 `[Pass8-TERNARY]`
段落校正口径：
- TERNARY bounded subset 80 文件实测自 Pass 01 起持续为 69 passed / 7 failed /
  0 errors / 76 总计（Pass7-TERNARY fix_report 回归记录 `69 7 0 76 5.4 TERNARY
  files=80`，与本 docstring 原「Pass 01: 69p/7f/76」口径一致）
- Pass 1-7 期间持续 69p/7f/76，无新增失败亦无失败消除
- 7 例预存失败为 ternary 值被外层表达式消费的模式（assert method call /
  listcomp body / await call arg / for-iter subscript / compare in both /
  tuple-unpack / starred-list scalar），非保守修复范围（与 Pass7-TERNARY
  §未完成项 2 同源）
- 与 Pass3-BOOLOP 在 `_generate_boolop` docstring 中追加 [Pass3-BOOLOP] 段落
  同步测试状态同型

控制流不变，仅 docstring 文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py TERNARY
```
**结果**：`69 7 0 76 5.6 TERNARY files=80` —— 与基线一致（69 passed, 7 预存失败,
0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 过时时点表述（与 Pass3-BOOLOP 在 _generate_boolop docstring 同步测试状态同型） | **已校正**（追加 [Pass8-TERNARY] 段落，说明 Pass 1-7 期间状态持续 69p/7f/76 无变化） |

## 未完成项

1. **文件其他位置 50+ 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量**未替换（Pass5-TERNARY/SEQ
   已替换 3 处，Pass7-TERNARY 已同步行号引用；余 40+ 处待统一替换）：全量替换需逐处评估语义
   等价性，留待后续 Pass 统一处理。
2. **7 例预存失败**（ternary 值被外层表达式消费的模式：assert method call / listcomp body
   / await call arg / for-iter subscript / compare in both / tuple-unpack / starred-list scalar）：
   需针对各自消费模式单独设计，非保守修复范围。
3. **BOOLOP→TERNARY 识别顺序调换**（Pass 1 已明确为高风险）：影响全流水线。
4. **`_detect_ternary_pattern` / `_generate_ternary` 函数过长**（~1600 / ~3000 行，Pass 1
   已登记）：可维护性改进。
5. **`_sim_wrapping_instr` 内 `'NOT_NONE' in op` 子串匹配判据未标记**（ternary 栈模拟路径，
   本轮 grep 发现 1 处命中）：与 Pass5/Pass6-BOOLOP / Pass7-ASSERT / Pass8-BOOLOP 同型 DRY
   违背，待后续 Pass 统一标记或替换。
6. **「截至 Pass 01」表述对称缺失已补齐**：本轮在 `_generate_ternary` docstring 中追加
   [Pass8-TERNARY] 校正段落，与 `_generate_boolop` docstring [Pass3-BOOLOP] 段落口径一致。
   后续若实施「彻底删除原表述」需同步两处。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_generate_ternary` docstring
  「字节码一致性约束」节末段追加 [Pass8-TERNARY] 校正段落，与 `_generate_boolop`
  [Pass3-BOOLOP] 段落口径一致）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/TERNARY/pass_08/fix_report.md`（本报告）
