# Pass 5 LOOP 修复报告

## 修复内容

### Fix 1: 同步 `_loop_generate_pre_stmts` docstring 与实际行为（Pass4-LOOP 后续）

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:4197-4214`（`_loop_generate_pre_stmts` 方法 docstring）

**问题根因**（Pass 4 LOOP 报告 §未完成项 2 已识别但未处理）：
Pass 4 LOOP 在调用点删除了 `if pre_stmts: body_stmts.extend(pre_stmts)` 死代码块后，
报告 §未完成项 2 已指出「`_loop_generate_pre_stmts` 函数自身仍可重构：函数名声称
『generate pre_stmts 并返回』，实际是通过副作用修改 `body_stmts` 参数且始终返回 `[]`。
函数签名 `-> List[Dict[str, Any]]` 与实际行为不符」。

具体漂移点：
1. **返回值漂移**：函数末尾 `return pre_stmts` 中 `pre_stmts` 局部变量初始化为 `[]` 后
   从未被 append/extend（实际副作用是 `body_stmts.extend(_pre_stmts)`，注意 `_pre_stmts`
   与 `pre_stmts` 是不同标识符），故函数**始终返回 `[]`**。
2. **签名漂移**：`-> List[Dict[str, Any]]` 暗示「生成并返回 pre_stmts 列表」，实际返回值
   恒为 `[]`，真实数据通过副作用传递给入参 `body_stmts`。
3. **调用点已无返回值引用**：唯一调用点 L4101（`_loop_generate_body` 内）已不使用返回值
   （Pass4-LOOP 已删除调用点的 `if pre_stmts:` 死分支）。

**修复策略**：
仅同步 docstring 文本——保留原单行 docstring「从init_blocks和内层for循环的iter_setup提取
前置语句」作历史追溯，追加 `[Pass5-LOOP]` 段落校正口径：
- 实际行为：副作用通过 `body_stmts.extend(_pre_stmts)` 修改入参，返回值恒为 `[]`
- 签名/语义漂移：`-> List[Dict[str, Any]]` 与实际不符
- 唯一调用点已不使用返回值（Pass4-LOOP 已清理）
- 后续 Pass 可把签名改为 `-> None` 并重命名以反映副作用语义

不触及任何可执行代码，控制流不变。

**为什么不直接改签名（与 Pass4-LOOP 删调用点死代码不同）**：
改 `-> List[Dict[str, Any]]` 为 `-> None` 涉及函数语义重定义，且需评估是否有外部模块
依赖返回值（虽 grep 确认仅 1 处调用点，但签名变更属接口修改，超出保守范围）。本轮保守
仅同步 docstring，把签名重构留给后续 Pass。

控制流不变，仅 docstring 文本追加。

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
| 控制流改变 | 未改变（仅 docstring 文本同步） |
| 测试文件修改 | 未修改任何测试文件 |
| 签名/语义漂移（虚假返回类型声明） | **已校正**（docstring 同步实际副作用语义） |

## 未完成项

1. **`_loop_generate_pre_stmts` 签名 `-> List[Dict[str, Any]]` 改为 `-> None`**（本轮已 docstring 同步）：
   涉及函数语义重定义，超出保守范围。
2. **3 处 Pass 2 已标记的反模式**仍挂账 Pass 3+：
   - `_preceding_if_cond` 跨区域反向抓 IfRegion
   - 跨 LoopRegion 去重后处理
   - `_is_except_handler_block` 指令模式启发式

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_loop_generate_pre_stmts` docstring 同步实际副作用语义）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/LOOP/pass_05/fix_report.md`（本报告）
