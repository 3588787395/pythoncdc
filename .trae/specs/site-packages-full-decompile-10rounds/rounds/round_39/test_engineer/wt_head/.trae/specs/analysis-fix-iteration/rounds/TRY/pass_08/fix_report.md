# Pass 8 TRY 修复报告

## 修复内容

### Fix 1: 同步 [Pass5-TRY] 段落中 te046 修复段行号上界 L886-L910 → L886-L911（off-by-one）

**问题位置**：
- `/workspace/core/cfg/region_ast_generator.py:12763-12769`（`_generate_try` docstring [Pass5-TRY] 段落）
- `/workspace/core/cfg/region_analyzer.py:4770-4776`（`_identify_try_except_regions` docstring [Pass5-TRY] 段落，与上者同型）

**问题根因**（与 Pass7-IF 同型——注释行号引用与实际位置不一致）：

[Pass5-TRY] 段落原文：
```
- [Pass5-TRY] 同步：原 te046 修复注释引用的行号 `L599-634` 已过时——
  实际「顶级祖先」检查（orphan block 释放逻辑中的 te046 修复段）
  已下移至 L886-L910（te046 注释起始 L886，沿 parent 链查找顶级祖先
  L898-L905，无顶级祖先释放分支 L909-L911）。...
```

段落内部行号引用不一致：
- 上界「已下移至 L886-L910」
- 下界「无顶级祖先释放分支 L909-L911」

实际 te046 修复段（grep `修复 te046 spurious` 定位）：
- L886: `# 修复 te046 spurious `if True: pass`：...`（注释起始）
- L898-L905: 沿 parent 链查找顶级祖先
- L909: `# 无顶级祖先 → 真正的孤儿块，释放`
- L910: `del self.region_analyzer.block_to_region[_block]`
- L911: `_orphaned_blocks.append(_block)`（释放分支末行）

故 te046 修复段实际跨 L886-L911（含释放分支末行 L911），上界引用 L886-L910
少 1 行，与同段「L909-L911」下界不一致。

**对称缺失**：原 [Pass5-TRY] 段落同时存在于 `_generate_try` 与
`_identify_try_except_regions` 两处 docstring（Pass6-TRY 已补齐对称同步），
故本轮 off-by-one 校正也需同步两处。

**修复策略**（与 Pass7-IF 同型——仅注释文本同步，不改控制流）：

在两处 docstring 的 [Pass5-TRY] 段落后追加 `[Pass8-TRY]` 段落，校正上界引用
L886-L910 → L886-L911，与同段 L909-L911 口径一致。保留原 [Pass5-TRY] 段落
作历史追溯（与 Pass7-IF 改用 grep 验证方式描述同型保守策略一致）。

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
| 控制流改变 | 未改变（仅注释文本同步） |
| 测试文件修改 | 未修改任何测试文件 |
| 注释行号引用 off-by-one（与 Pass7-IF 同型） | **已校正**（两处 docstring 同步 L886-L910 → L886-L911） |

## 未完成项

1. **TODO[pass2-CC] _try_build_* 三连 patch chain**（`_try_build_walrus_chained_compare`
   / `_try_build_literal_middle_chained_compare` / `_try_build_method_call_chained_compare`）
   仍挂账 Pass 3+，需统一操作数提取路径后删除。
2. **`_generate_try_body` 4 并列启发式**（is_child / is_in_try_blocks / is_before_try_start
   / handler_in_range）仍挂账 Pass 3+，待统一为区间包含判据。
3. **「100% 通过率」表述**：Pass7-TRY 已在 _identify_try_except_regions docstring
   追加 [Pass7-TRY] 校正段落，与 _generate_try docstring [Pass4-TRY] 段落口径一致。
   后续若实施「彻底删除原表述」需同步两处。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_generate_try` docstring [Pass5-TRY] 段落后追加 [Pass8-TRY] 校正段落）
- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_identify_try_except_regions` docstring [Pass5-TRY] 段落后追加 [Pass8-TRY] 校正段落，与 _generate_try 同步）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/TRY/pass_08/fix_report.md`（本报告）
