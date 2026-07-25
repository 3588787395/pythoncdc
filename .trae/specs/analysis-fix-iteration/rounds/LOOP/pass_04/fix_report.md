# Pass 4 LOOP 修复报告

## 修复内容

### Fix 1: 删除 `_generate_loop` 调用点的 `if pre_stmts: body_stmts.extend(pre_stmts)` 死代码块

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:4089-4091`（`_generate_loop` 内调用 `_loop_generate_pre_stmts` 后）

**问题根因**：
`_loop_generate_pre_stmts(region, body_stmts)` 函数内部：
- L4189（函数内）：`pre_stmts: List[Dict[str, Any]] = []` 初始化为空列表
- L4198：`_pre_stmts = self._loop_extract_pre_stmts_from_block(pred)` —— 注意是
  `_pre_stmts`（带下划线前缀），与 `pre_stmts` 是**不同标识符**
- L4200：`body_stmts.extend(_pre_stmts)` —— extend 的是 `body_stmts`（参数），
  **不是** `pre_stmts`（局部变量）
- L4204：`return pre_stmts` —— 始终返回 `[]`

故函数**始终返回 `[]`**，调用点 L4089-4091 的：
```python
pre_stmts = self._loop_generate_pre_stmts(region, body_stmts)
if pre_stmts:               # 永假（pre_stmts 始终为 []）
    body_stmts.extend(pre_stmts)   # 永不执行
```
属典型「无副作用死代码」——`if pre_stmts:` 永假，`body_stmts.extend(pre_stmts)`
永不执行。函数调用的副作用（修改 `body_stmts`）通过参数传递保留不变。

**修复策略**：
- 移除 `pre_stmts = self._loop_generate_pre_stmts(...)` 赋值（已无引用）
- 移除 `if pre_stmts: body_stmts.extend(pre_stmts)` 死代码块
- 保留 `self._loop_generate_pre_stmts(region, body_stmts)` 函数调用（副作用仍需）
- 新增 `[Pass4-LOOP]` 注释说明删除依据与 `pre_stmts` / `_pre_stmts` 标识符区别

**控制流影响**：无。删除的是永假条件分支，函数调用的副作用（extend body_stmts）
通过参数引用保留。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py LOOP
```
**结果**：`79 0 0 79 2.1 LOOP files=80` —— 与基线一致（79 passed, 0 failed, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（删除永假条件分支） |
| 测试文件修改 | 未修改任何测试文件 |
| 死代码（永假条件 + 永不执行 extend） | **已消除** |

## 未完成项

1. **3 处 Pass 2 已标记的反模式**仍挂账 Pass 3+：
   - `_preceding_if_cond` 跨区域反向抓 IfRegion
   - 跨 LoopRegion 去重后处理
   - `_is_except_handler_block` 指令模式启发式
   本轮未重构这些反模式（需要识别阶段统一改造），仅清理死代码。

2. **`_loop_generate_pre_stmts` 函数自身仍可重构**：函数名声称「generate pre_stmts
   并返回」，实际是通过副作用修改 `body_stmts` 参数且始终返回 `[]`。函数签名
   `-> List[Dict[str, Any]]` 与实际行为不符。本轮仅清理调用点死代码，
   未重构函数本身（重构涉及调用方语义变更，超出保守范围）。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：删除死代码块 + 添加 [Pass4-LOOP] 注释）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/LOOP/pass_04/fix_report.md`（本报告）
