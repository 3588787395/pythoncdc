# Pass 2 第 13 轮修复报告（TRY 区域）

## 修复范围

文件：`/workspace/core/cfg/region_ast_generator.py`

### Fix 1: 删除 3 处死代码（零行为变更）

| # | 原行号 | 内容 | 处理 |
|---|--------|------|------|
| 1 | L12906-L12907 | `self._generating_regions.discard(id(_nested_ternary_for_handler))` 紧接 `self._generating_regions.add(...)`，discard 为 NO-OP | 删除 discard 行 |
| 2 | L12124-L12125 | `else: pass` 空分支 | 删除 else 分支，保留 if 分支 |
| 3 | L12152-L12153 | `if not is_nested_region_entry: pass` 空 if 体 | 删除整个 if 块 |

### Fix 2: 标记 4 启发式为已知技术债

位置：`_generate_try_body` 方法体内 `nested_try_regions = []` 上方

注释内容：
```python
# [Pass 2 标记] 4 并列启发式（is_child / is_in_try_blocks / is_before_try_start /
# handler_in_range）待统一为区间包含判据，符合原则 3「嵌套即区间包含」。
```

## 验证

- 编译验证：`python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` → `COMPILE_OK`
- 退出码：0
- 严格约束：未修改测试文件，未引入反模式，Fix 1 仅删除冗余、未改变任何控制流

## 行号偏移说明

由于三处删除顺序执行，删除后行号会前移；按读取时的原始行号定位，编辑工具按上下文锚定，全部成功命中。
