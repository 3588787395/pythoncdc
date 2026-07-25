# Pass 8 LOOP 修复报告

## 修复内容

### Fix 1: 删除 `_loop_generate_for` 中 `for_iter_setup` 的冗余重赋值

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:2988`（`_loop_generate_for` 内「Build iterator expression」段落起始处）

**问题根因**（与 Pass3-IF 删 `_depth=0` 同型——纯死代码/冗余赋值）：

`_loop_generate_for` 中 `for_iter_setup` 被同一表达式赋值两次：

```python
L2975:  for_iter_setup = region.metadata.get('for_iter_setup')

L2977-2987:
        if region.init_blocks:
            for ib in region.init_blocks:
                if ib == for_iter_setup:    # 使用第一次赋值
                    continue
                if ib not in self.generated_blocks:
                    ib_stmts = self._generate_block_statements(ib)
                    pre_stmts.extend(ib_stmts)
                    self.generated_blocks.add(ib)
                    self.generated_offsets.add(ib.start_offset)

L2987:  # Build iterator expression
L2988:  for_iter_setup = region.metadata.get('for_iter_setup')   # 冗余重赋值
L2989:  iter_expr = None
```

L2975-2988 之间仅访问 `region.init_blocks` / `self.generated_blocks` /
`self.generated_offsets` / `pre_stmts` / `ib` / `ib_stmts`，**从未修改
`region.metadata`**。`dict.get(key)` 是纯查询无副作用，相同入参恒返回相同值。
故 L2988 重赋值恒为 no-op，`for_iter_setup` 值不变。

**修复策略**（与 Pass3-IF 删 `_depth=0` 同型——纯冗余赋值删除）：

1. 删除 L2988 `for_iter_setup = region.metadata.get('for_iter_setup')` 一行
2. 追加 `[Pass8-LOOP]` 注释段说明：
   - `for_iter_setup` 已在 L2975 由同一表达式赋值
   - L2975-2987 之间无 `region.metadata` 修改，本行重赋值恒为 no-op
   - 删除后行为完全等价
   - 保留 `# Build iterator expression` 注释作段落起始锚点

**为什么不合并 L2975 与 L2988 中间代码**：中间 `if region.init_blocks:` 块
依赖 `for_iter_setup`（`if ib == for_iter_setup: continue`），不能下移。
本轮仅删除冗余重赋值，不重排代码块。

**与 Pass3-IF 删 `_depth=0` 的对比**：

| 维度 | Pass3-IF (`_depth=0`) | Pass8-LOOP (`for_iter_setup` 重赋值) |
|---|---|---|
| 死代码类型 | 死形参（函数体从不引用） | 冗余重赋值（同表达式无中间修改） |
| 删除影响范围 | 仅签名 | 函数体内 1 行 |
| 调用点变更 | 无 | 无 |
| 控制流变更 | 无 | 无 |
| 风险等级 | 零风险 | 零风险（同表达式 + 无中间修改） |

控制流不变，仅删除冗余重赋值。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py LOOP
```
**结果**：`79 0 0 79 2.0 LOOP files=80` —— 与基线一致（79 passed, 0 failed, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅删除冗余重赋值） |
| 测试文件修改 | 未修改任何测试文件 |
| 冗余重赋值（同表达式无中间修改） | **已删除** |

## 未完成项

1. **3 处 Pass 2 已标记的反模式**仍挂账 Pass 3+：
   - `_preceding_if_cond` 跨区域反向抓 IfRegion
   - 跨 LoopRegion 去重后处理
   - `_is_except_handler_block` 指令模式启发式
   本轮未重构这些反模式（需识别阶段统一改造）。

2. **`_loop_generate_pre_stmts` 重命名**（如改为 `_loop_extend_inner_for_iter_pre_stmts`）：
   收益小、改动面大，本轮保守不动。

3. **docstring 首行「init_blocks」表述**：Pass7-LOOP 仅追加段落说明，未直接修改首行。
   本轮不动。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：删除 `_loop_generate_for` 中 `for_iter_setup` 冗余重赋值 + 追加 [Pass8-LOOP] 注释段）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/LOOP/pass_08/fix_report.md`（本报告）
