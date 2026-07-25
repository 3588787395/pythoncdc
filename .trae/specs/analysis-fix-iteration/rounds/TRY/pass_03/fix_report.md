# Pass 3 TRY 修复报告

## 修复内容

### Fix 1: 同步 `_generate_handler_body_statements` 中 except* 框架指令注释

**问题位置**：`/workspace/core/cfg/region_ast_generator.py` `_generate_handler_body_statements` 方法（L13277-L13281 原注释）

**问题根因**：
原注释列出 6 个 except* 框架指令：
```
# except* 框架指令：BUILD_LIST, SWAP, LIST_APPEND, PREP_RERAISE_STAR,
# COPY（在 CHECK_EG_MATCH/PREP_RERAISE_STAR 上下文中）,
# POP_JUMP_FORWARD_IF_NONE/POP_JUMP_FORWARD_IF_NOT_NONE（分派跳转）
```
但实际 `_EXC_STAR_FRAMEWORK_OPS` 元组只含 4 个 op：
```python
_EXC_STAR_FRAMEWORK_OPS = ('BUILD_LIST', 'LIST_APPEND', 'PREP_RERAISE_STAR', 'SWAP')
```
COPY 与 POP_JUMP_*_IF_NONE/IF_NOT_NONE 不在元组内——COPY 在下方 `_is_except_star_block` 分支单独过滤（`handler_instrs = [i for i in handler_instrs if i.opname != 'COPY']`），POP_JUMP_*_IF_NONE/IF_NOT_NONE 由 `exc_dispatch_jump_offset` 路径（基于 offset 截断 handler_instrs）统一处理。

原注释误导读者以为 6 个 op 都在同一元组内过滤，与代码不符。

**修复策略**：
替换为 `[Pass3-TRY]` 注释，明确说明：
1. 元组仅含 4 个 op（BUILD_LIST / LIST_APPEND / PREP_RERAISE_STAR / SWAP）。
2. COPY 与 POP_JUMP_*_IF_NONE/IF_NOT_NONE 同属 except* 框架指令，但不在本元组内。
3. COPY 由下方 `_is_except_star_block` 分支单独过滤。
4. POP_JUMP_*_IF_NONE/IF_NOT_NONE 由 `exc_dispatch_jump_offset` 路径（基于 offset 截断 handler_instrs）统一处理。

控制流不变，仅注释文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py TRY
```
**结果**：`80 0 0 80 2.7 TRY files=80` —— 与基线一致（80 passed, 0 failed, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变 |
| 测试文件修改 | 未修改任何测试文件 |

## 未完成项

1. **TODO[pass2-CC] _try_build_* 三连 patch chain**（`_try_build_walrus_chained_compare` / `_try_build_literal_middle_chained_compare` / `_try_build_method_call_chained_compare`）仍挂账 Pass 3+，需统一操作数提取路径后删除。
2. **`_generate_try_body` 4 并列启发式**（is_child / is_in_try_blocks / is_before_try_start / handler_in_range）仍挂账 Pass 3+，待统一为区间包含判据。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/TRY/pass_03/fix_report.md`（本报告）
