# Pass 3 ASSERT 修复报告

## 修复内容

### Fix 1: 简化 `_build_assert_chained_compare` 中永假的 `not all_blocks` 死判据

**问题位置**：`/workspace/core/cfg/region_ast_generator.py` `_build_assert_chained_compare` 方法（L2365-L2367）

**问题根因**（Pass 2 已识别但未实施，Pass 3 执行）：
原代码：
```python
all_blocks = [cond_block] + list(chain_blocks)
if not all_blocks or cond_block is None:
    return None
```

`all_blocks = [cond_block] + list(chain_blocks)` 至少含 `cond_block` 一个元素——
即便 `cond_block` 为 `None`，`[None] + list(chain_blocks)` 仍是至少 1 元素的非空列表，
故 `not all_blocks` 永假。真正起作用的是 `cond_block is None` 守卫。

**修复策略**：
简化为单一判据 `if cond_block is None: return None`，新增 `[Pass3-ASSERT]` 注释
说明永假判据与简化依据。控制流等价：
- `cond_block is None` 时：原 `not all_blocks` 为 False，但 `cond_block is None` 为 True
  → 短路返回 None；简化后同样 `cond_block is None` 为 True → 返回 None。等价。
- `cond_block is not None` 时：原 `not all_blocks` 为 False，`cond_block is None` 为 False
  → 不返回；简化后 `cond_block is None` 为 False → 不返回。等价。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py ASSERT
```
**结果**：`21 6 0 27 2.5 ASSERT files=27` —— 与基线一致（21 passed, 6 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（删除永假判据，控制流等价） |
| 测试文件修改 | 未修改任何测试文件 |

## 未完成项

1. **`_build_assert_message` 非 build_string 分支未同步主路径 [Round8-12] walrus 反向
   RAISE_VARARGS 扫描**（Pass 2 已标记）：属控制流变更，超出本轮约束。
2. **6 例预存失败**（3 ternary-in-assert-test + 3 assert-in-if-body 链式比较变体）：
   需识别顺序调整，非本轮范围。
3. **四条 fall-through 遍历器逻辑近似可统一**（Pass 2 已评估）：终止条件有细微差别，
   统一会改变边界行为，超出保守修复范围。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/ASSERT/pass_03/fix_report.md`（本报告）
