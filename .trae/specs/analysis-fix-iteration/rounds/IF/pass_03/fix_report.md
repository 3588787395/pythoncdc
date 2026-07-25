# Pass 3 IF 修复报告

## 修复内容

### Fix 1: 删除 `_if_generate_branch_stmts` 的死形参 `_depth=0`

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:11930`（原签名 `def _if_generate_branch_stmts(self, blocks=None, _depth=0, region=None)`）

**问题根因**：
`_depth=0` 形参在函数体内从未被引用，3 处调用点（line 3203/3941/6600）也均未传入该参数。属无副作用死代码。

**修复策略**：
移除 `_depth=0` 形参，签名简化为 `def _if_generate_branch_stmts(self, blocks=None, region=None)`。
保留 `blocks` / `region` 形参及函数体不变（控制流不变）。

**新增注释**：
```python
# [Pass3-IF] 移除原 `_depth=0` 形参：函数体从未引用，3 处调用点
# (line 3203/3941/6600) 也均未传入。属无副作用死代码删除。
```

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `OK: imports succeeded`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py IF
```
**结果**：`79 1 0 80 7.1 IF files=80` —— 与基线一致（79 passed, 1 预存失败，0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入（且删除了一个 `_depth` 形参占位，更彻底消除深度上限倾向） |
| 控制流改变 | 未改变 |
| 测试文件修改 | 未修改任何测试文件 |

## 未完成项

1. **TODO[pass2-CC] 未完成**：`_detect_boolop_after_chained_compare` 与
   `_if_generate_full_elif_chain` 中的 save/restore 块仍存在，等待后续 Pass
   将「CC + and/or 短路块」识别阶段统一为 `BoolOpRegion` 后一并删除。
2. **baseline_failures.txt 中的 1 处预存失败**：非本轮引入，未处理。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/IF/pass_03/fix_report.md`（本报告）
