# Pass 6 TRY 修复报告

## 修复内容

### Fix 1: 补齐 `_identify_try_except_regions` docstring 中 te046 修复注释的过时行号引用同步

**问题位置**：`/workspace/core/cfg/region_analyzer.py:4767-4769`（`_identify_try_except_regions` docstring 内 te046 修复段）

**问题根因**（Pass 5 TRY 同型行号漂移遗漏）：
Pass 5 TRY 已在 `_generate_try` docstring（region_ast_generator.py L12727-L12733）同步了
te046 修复段中过时的行号引用 `L599-634` → `L886-L910`，并说明行号漂移源于多轮 Pass
修改使 region_ast_generator.py 顶部插入若干行。

但同一 te046 修复段在 `_identify_try_except_regions` docstring
（region_analyzer.py L4767-L4769）中也存在，原引用 `L599-634` 同样过时，但 Pass 5 TRY
未同步此处的同型引用。本轮 Pass 6 补齐：

1. **原过时引用**：`region_ast_generator.py L599-634 增加「顶级祖先」检查修复`（与 Pass5-TRY
   在 _generate_try 中已校正的引用同型）
2. **实际位置**（与 Pass5-TRY 同步口径一致）：
   - L886: te046 修复注释起始 `# 修复 te046 spurious`
   - L898-L905: 沿 parent 链查找顶级祖先逻辑（`_ancestor = getattr(_region, 'parent', None)` 循环）
   - L909-L911: 无顶级祖先释放分支（`del self.region_analyzer.block_to_region[_block]`）
3. **行号漂移原因**：多轮 Pass 修改使 region_ast_generator.py 顶部插入若干行

**修复策略**（与 Pass5-TRY 同型——仅注释文本同步）：

保留原 te046 修复段文本不变（历史追溯用），追加 `[Pass5-TRY]` + `[Pass6-TRY]` 段落：
1. `[Pass5-TRY]` 段落复用 Pass5-TRY 在 _generate_try 中的同步说明（口径完全一致）
2. `[Pass6-TRY]` 段落说明本轮补齐：Pass5-TRY 仅同步 _generate_try docstring，
   未同步 _identify_try_except_regions docstring 中的同型引用，本轮补齐
3. 验证方法：grep `修复 te046 spurious` 可重新定位

**与 Pass5-TRY 的对比**：

| 维度 | Pass5-TRY | Pass6-TRY |
|---|---|---|
| 同步位置 | `_generate_try` docstring（region_ast_generator.py L12727-L12733） | `_identify_try_except_regions` docstring（region_analyzer.py L4770-L4781） |
| 原引用 | L599-634（过时） | L599-634（过时） |
| 新引用 | L886-L910 | L886-L910 |
| 控制流变更 | 无 | 无 |

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py TRY
```
**结果**：`80 0 0 80 2.6 TRY files=80` —— 与基线一致（80 passed, 0 failed, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变 |
| 测试文件修改 | 未修改任何测试文件 |
| 过时注释行号引用（Pass5-TRY 同型遗漏） | **已同步**（补齐 `_identify_try_except_regions` docstring 中 L599-634 → L886-L910） |

## 未完成项

1. **TODO[pass2-CC] _try_build_* 三连 patch chain**（`_try_build_walrus_chained_compare`
   / `_try_build_literal_middle_chained_compare` / `_try_build_method_call_chained_compare`）
   仍挂账 Pass 3+，需统一操作数提取路径后删除。
2. **`_generate_try_body` 4 并列启发式**（is_child / is_in_try_blocks / is_before_try_start
   / handler_in_range）仍挂账 Pass 3+，待统一为区间包含判据。
3. **`_generate_try` docstring 中 te046 修复段口径**（原 L599-634 引用 + [Pass5-TRY] 校正段落）：
   本轮已在 _identify_try_except_regions docstring 中追加同型段落，两处口径一致。
   后续 Pass 若要彻底删除原 L599-634 引用，需同步删除两处。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_identify_try_except_regions` docstring 追加 [Pass5-TRY]/[Pass6-TRY] 段落同步 te046 行号）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/TRY/pass_06/fix_report.md`（本报告）
