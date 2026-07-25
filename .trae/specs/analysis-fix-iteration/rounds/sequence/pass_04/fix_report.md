# Pass 4 SEQ (Sequence) 修复报告

## 修复内容

### Fix 1: 为 `_generate_block_statements` 内 `_loop_depth > 0` 跨层启发式添加已知反模式标记

**问题位置**：`/workspace/core/cfg/region_ast_generator.py` `_generate_block_statements` 方法（L24959，`if self._loop_depth > 0:` break 检测段）

**问题根因**（Pass 2 已识别为 TODO[pass3-SEQ]-F 但未添加内联标记）：
`_generate_block_statements` 开头的 `if self._loop_depth > 0:` break 检测为跨层启发式：
- `_loop_depth` 是生成阶段的状态变量（"当前是否在循环体内"）
- 使用生成阶段状态做 break 模式判别（POP_TOP + LOAD_CONST None + RETURN_VALUE → Break），而 break 归属理想上应在识别阶段通过 `block_role` / `BlockRole.BREAK` 统一判定
- 本启发式作为 `block_role` 之外的后处理补丁存在——当识别阶段未标记 BlockRole.BREAK 时，生成阶段用 `_loop_depth > 0` 兜底检测 break 模式

Pass 2 报告 §5 已列为 TODO[pass3-SEQ]-F「消除 `_loop_depth > 0` 跨层启发式（中风险）」，但仅在报告记录，未在代码内联添加标记注释。

**修复策略**：
在 `if self._loop_depth > 0:` 前添加 `[Pass4-SEQ]` 注释标记，明确登记：
1. 该判据为跨层启发式（生成阶段状态变量做识别阶段应做的 break 归属判别）
2. 对应 Pass 2 报告 TODO[pass3-SEQ]-F
3. 待识别阶段完善 break 块标记后消除
4. 本轮仅添加标记，不改变控制流

不触及任何可执行代码，控制流不变。

**为什么不直接消除**：
Pass 2 已明确消除该启发式为中风险——需先在识别阶段完善 break 块标记（保证 for 循环 try 块中的 if-break 结构被正确识别为 BlockRole.BREAK），否则直接删除会导致 break 检测漏识别。本轮严格遵循保守策略——仅添加注释标记，把消除留给后续 Pass。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py SEQ
```
**结果**：`127 10 0 137 1.6 SEQ files=80` —— 与基线一致（127 passed, 10 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 跨层启发式（后处理补丁） | **已标记**（`_loop_depth > 0` break 检测登记为已知反模式 TODO[pass3-SEQ]-F，待识别阶段完善后消除） |

## 未完成项

1. **`_loop_depth > 0` 跨层启发式消除**（本轮已标记，对应 TODO[pass3-SEQ]-F）：中风险，需先在识别阶段完善 break 块标记。
2. **`_cond_jump_bs` 兜底分支删除**（Pass 1 TODO[pass2-SEQ]-C，已标记）：中风险，需先在 `_identify_conditional_regions` 末尾扫描未认领条件跳转块。
3. **`_generate_block_statements` god-method 瘦身**（Pass 2 TODO[pass3-SEQ]-E）：高风险，需把语句边界判定移到识别阶段。
4. **`_is_trivial_return_block` Pattern 1 收紧为 `argval is None`**（Pass 2 TODO[pass2-SEQ]-B）：低风险但属控制流变更，需评估影响。
5. **10 例预存失败**：L1_basic NameError 类（测试基础设施问题）+ basic/test_b23yieldfrom_complex（字节码重建差异），非保守修复范围。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_generate_block_statements` L24959 添加 `[Pass4-SEQ]` 跨层启发式反模式标记）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/sequence/pass_04/fix_report.md`（本报告）
