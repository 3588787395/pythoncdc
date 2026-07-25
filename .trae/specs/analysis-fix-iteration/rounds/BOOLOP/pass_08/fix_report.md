# Pass 8 BOOLOP 修复报告

## 修复内容

### Fix 1: 标记 `_generate_boolop` 内 `'TRUE' in _last_ci.opname or 'NONE' in _last_ci.opname` 子串匹配 DRY 违背

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:17719-17741`
（`_generate_boolop` 方法内 `_is_outer_condition` 分支末段取反判定前的 [Pass8-BOOLOP] 标记段落）

**问题根因**（与 Pass5-BOOLOP / Pass6-BOOLOP / Pass7-ASSERT 同型「子串匹配 DRY 违背」反模式）：

`_generate_boolop` 在 `_is_outer_condition` 分支末段取反判定时使用子串匹配判据：
```python
_last_cb = region.op_chain[-1][0] if region.op_chain else None
if _last_cb:
    _last_ci = _last_cb.get_last_instruction()
    if _last_ci and _last_ci.argval is not None and _last_ci.opname in FORWARD_CONDITIONAL_JUMP_OPS:
        if 'TRUE' in _last_ci.opname or 'NONE' in _last_ci.opname:
            _boolop_negate = True
```

其中 `'TRUE' in _last_ci.opname` / `'NONE' in _last_ci.opname` 子串匹配判据与以下 Pass 标记的同型反模式一致：

- Pass5-BOOLOP 已标记：`_detect_while_condition_boolop_chain` 内 `'FALSE' in last.opname` / `'TRUE' in last.opname` 子串匹配判据散布 17+ 处
- Pass6-BOOLOP 已同步行号引用，改用 grep 验证方式描述避免递归漂移
- Pass7-ASSERT 已标记：`_detect_assert_boolop_chain` 内 `'TRUE' in cond_last.opname` / `'NOT_NONE' in cond_last.opname` 子串匹配同型
- Pass7-ASSERT 已标记：`_build_assert_boolop_condition` 内 `'NOT_NONE' in last_instr.opname` 同型

但 `_generate_boolop` 内的同型子串匹配判据**未标记**——属散布 17+ 处之一但此前未被识别（且位于 region_ast_generator.py 而非 region_analyzer.py，跨文件）。

**全量统计**（grep 验证）：
- 本文件 `_generate_boolop` 内 `'TRUE' in _last*.opname` / `'FALSE' in _last*.opname` 共 3 处命中
  - 1 处为本行紧邻下方（`_is_outer_condition` 分支末段取反）
  - 2 处位于本函数 if-like 复杂短路结构 then/else 取反分支内

**修复策略**（与 Pass5-BOOLOP / Pass7-ASSERT 同型——仅添加内联标记）：

在 `if 'TRUE' in _last_ci.opname or 'NONE' in _last_ci.opname:` 行前追加 `[Pass8-BOOLOP]` 标记段落：
1. 说明此处子串匹配判据与 Pass5-BOOLOP / Pass6-BOOLOP / Pass7-ASSERT 同型 DRY 违背一致
2. **不再引用具体行号**——改用 grep 验证 + 相对位置描述（与 Pass6-SEQ / Pass7-TERNARY 同型思路一致，避免递归漂移）
3. 本轮仅添加内联标记，未触碰可执行代码，控制流不变
4. 验证方法：grep `'TRUE' in _last.opname` / `'FALSE' in _last.opname` 在 `_generate_boolop` 内共 3 处命中

**为什么不直接替换为 frozenset 常量**：
Pass5-BOOLOP / Pass6-BOOLOP fix_report §未完成项 1 已说明全量替换需先按
FALSE/TRUE/IF_NONE/IF_NOT_NONE/NONE 多类归类，再分别定义 frozenset 常量，
属高风险重构（涉及 17+ 处调用点）。本轮保守仅标记，待后续 Pass 统一替换。

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py BOOLOP
```
**结果**：`79 0 0 79 1.6 BOOLOP files=80` —— 与基线一致（79 passed, 0 failed, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 子串匹配 DRY 违背（与 Pass5/Pass6-BOOLOP / Pass7-ASSERT 同型，跨文件 region_ast_generator.py 首处） | **已标记**（追加 [Pass8-BOOLOP] 内联标记段落，改用 grep 验证 + 相对位置描述避免递归漂移） |

## 未完成项

1. **`'FALSE' in opname` / `'TRUE' in opname` 子串匹配统一替换为结构判据**（Pass 5 已标记首处，
   Pass6-BOOLOP 同步行号引用；Pass7-ASSERT 已标记 `_detect_assert_boolop_chain` /
   `_build_assert_boolop_condition` 同型；本轮在 region_ast_generator.py 的
   `_generate_boolop` 内标记首处；余 16+ 处待统一替换）：需先按
   FALSE/TRUE/IF_NONE/IF_NOT_NONE/NONE 多类归类，再分别定义 frozenset 常量，
   高风险重构。
2. **`_generate_boolop` 内 if-like 复杂短路结构分支两处同型子串匹配判据未单独标记**
   （本处仅标记 `_is_outer_condition` 分支首处）：本轮 grep 验证 3 处命中，
   仅首处添加 [Pass8-BOOLOP] 标记，余 2 处与本处同型，待后续 Pass 统一标记或替换。
3. **`_identify_boolop_regions` 两段重复 docstring 合并**（Pass 2/3 已评估）：长版 +
   短版「保留供快速参考」，删除任一段都会损失独有信息，需谨慎合并。
4. **BOOLOP→TERNARY 识别顺序调换**（Pass 1 已明确为高风险）：影响全流水线。
5. **`_detect_boolop_after_chained_compare` 生成期后处理**（Pass 1 已列为后续建议）：
   与 IF 区域 TODO[pass2-CC] 同源，需识别阶段统一为 BoolOpRegion 后删除。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_generate_boolop` 内 `_is_outer_condition`
  分支末段取反判定前追加 [Pass8-BOOLOP] 同型反模式标记段落，改用 grep 验证 + 相对位置描述避免递归漂移）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/BOOLOP/pass_08/fix_report.md`（本报告）
