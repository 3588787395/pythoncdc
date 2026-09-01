# Pass 4 CC (Chained Compare) 修复报告

## 修复内容

### Fix 1: 简化 `compute_chained_compare_operands` 中永假的 `not all_blocks` 死判据

**问题位置**：`/workspace/core/cfg/region_analyzer.py` `compute_chained_compare_operands` 方法（L2623-L2625）

**问题根因**（与 ASSERT Pass 3 同型死判据）：
原代码：
```python
all_blocks = [region.condition_block] + list(region.chained_compare_blocks)
if not all_blocks or region.condition_block is None:
    return
```

`all_blocks = [region.condition_block] + list(region.chained_compare_blocks)` 至少含 `region.condition_block` 一个元素——即便 `region.condition_block` 为 `None`，`[None] + list(...)` 仍是至少 1 元素的非空列表，故 `not all_blocks` 永假。真正起作用的是 `region.condition_block is None` 守卫。

**修复策略**：
简化为单一判据 `if region.condition_block is None: return`，新增 `[Pass4-CC]` 注释说明永假判据与简化依据。控制流等价：
- `region.condition_block is None` 时：原 `not all_blocks` 为 False，但 `region.condition_block is None` 为 True → 短路返回；简化后同样 `region.condition_block is None` 为 True → 返回。等价。
- `region.condition_block is not None` 时：原 `not all_blocks` 为 False，`region.condition_block is None` 为 False → 不返回；简化后 `region.condition_block is None` 为 False → 不返回。等价。

**与 ASSERT Pass 3 的同型性**：
ASSERT Pass 3 已对 `_build_assert_chained_compare` 内 `if not all_blocks or cond_block is None:` 执行完全相同的死判据简化（`all_blocks = [cond_block] + list(chain_blocks)` 同型）。本轮对 CC 区域 `compute_chained_compare_operands` 内同型判据做一致处理，保持两处风格统一。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py CC
```
**结果**：`37 3 0 40 3.5 CC files=40` —— 与基线一致（37 passed, 3 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（删除永假判据，控制流等价） |
| 测试文件修改 | 未修改任何测试文件 |

## 未完成项

1. **`_try_build_*` patch chain 统一**（Pass 2 已标记 `TODO[pass2-CC]`）：高风险，需保证 walrus / literal-middle / method-call 三特例的栈模拟语义被统一路径覆盖。
2. **Phase 3 CC extra_blocks 预扫描 / 重检测 / 字段回填删除**（Pass 2 已识别为后处理补丁）：前置依赖（放宽 Phase 2a CC 触发条件）未满足，直接删除会改变控制流并丢识别。
3. **`_detect_boolop_after_chained_compare` 消除**（Pass 1/2 已列）：中风险。
4. **3 例预存失败**：需针对各自模式单独设计，非保守修复范围。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`compute_chained_compare_operands` L2624 死判据简化）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/chained_compare/pass_04/fix_report.md`（本报告）
