# Pass 2 第 12 轮修复报告（LOOP 区域）

## 修复性质

本轮**仅做注释标记与 docstring 文案同步**，**零代码逻辑变更**。所有改动均为 Python 注释（`#`）或 docstring 文本，不改变任何控制流、表达式或数据结构。

## 修复清单

### Fix 1：标记 `_preceding_if_cond` 跨区域反向抓 IfRegion

- 文件：`/workspace/core/cfg/region_ast_generator.py`
- 位置：L3974 上方（`_preceding_if_cond = None` 之前）
- 操作：插入 3 行注释，标注跨区域反向抓前驱 IfRegion 拼装 BoolOp 违反原则 4（入口引用语义），待 Pass 3 重构为识别期 BoolOpRegion 归属。

### Fix 2：标记跨 LoopRegion 去重后处理

- 文件：`/workspace/core/cfg/region_analyzer.py`
- 位置：L3222 上方（`if len(loop_regions) >= 2:` 之前）
- 操作：插入 3 行注释，标注跨 LoopRegion 去重后处理与 Pass 1 已删除的 `_detect_and_filter_conditional_recheck_fake_loops` 同型，待 Pass 3 迁移到识别期主循环判据。

### Fix 3：标记 `_is_except_handler_block` 指令模式启发式

- 文件：`/workspace/core/cfg/region_analyzer.py`
- 位置：`_is_except_handler_block` docstring 末尾（L3754-L3758 之前结束引号上方）
- 操作：在 docstring 末尾追加 4 行 `[Pass 2 标记]` 段落，说明本方法基于 PUSH_EXC_INFO/CHECK_EXC_MATCH 指令模式判据，与 Pass 1 强调的「非 opname 计数启发式」原则相悖，待 Pass 3 调研 `TryExceptRegion.handler_blocks` 注册情况后改为查 `block_to_region` 归属判据。

### Fix 4：同步 docstring 与 Pass 1 fix_report 一致

- 文件 1：`/workspace/core/cfg/region_analyzer.py`
  - 位置：`_identify_loop_regions` docstring 第 6 节「已知失败模式」段落
  - 操作：在测试通过率条目下方追加「已知反模式：跨区域反向抓 IfRegion（`_preceding_if_cond`）+ 跨 LoopRegion 去重 + while/for-else 三联过滤，待 Pass 3 重构」附注。
- 文件 2：`/workspace/core/cfg/region_ast_generator.py`
  - 位置：`_generate_loop` docstring「字节码一致性约束」段落（`_loop_generate_while` 由其派发，本段为本轮 Fix 4 在 ast 侧的对应位置）
  - 操作：在「100% 完全匹配」条目下方追加同样的「已知反模式」附注。

> 说明：`_loop_generate_while` 本身在 L3210 处无 docstring（直接进入函数体）；用户指定的「`_loop_generate_while` docstring 中字节码一致性约束段落」实际位于其调用者 `_generate_loop` 的 docstring（L2763-L2777）。已在最贴近的位置完成附注。

## 严格约束符合性

| 约束 | 符合情况 |
| --- | --- |
| 不修改任何代码逻辑 | ✅ 仅插入 `#` 注释与 docstring 文本，无语句变更 |
| 不修改测试文件 | ✅ 未触碰任何 `tests/` 文件 |
| 不引入反模式 | ✅ 仅标记已有反模式，未新增 |
| 编译通过验证 | ✅ `python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` 退出码 0 |

## 验证结果

```
$ python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
OK: imports succeeded
（exit code 0）
```

## 后续建议

本轮标记的 3 个反模式均挂账到 Pass 3：

1. `_preceding_if_cond` 反向抓 IfRegion → Pass 3 重构为识别期 BoolOpRegion 归属
2. 跨 LoopRegion 去重 → Pass 3 迁移到识别期主循环判据
3. `_is_except_handler_block` 指令模式启发式 → Pass 3 调研 `TryExceptRegion.handler_blocks` 注册到 `block_to_region` 后改用归属判据
