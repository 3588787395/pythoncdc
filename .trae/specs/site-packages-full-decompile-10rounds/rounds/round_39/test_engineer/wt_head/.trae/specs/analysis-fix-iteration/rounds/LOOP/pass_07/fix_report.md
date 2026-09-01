# Pass 7 LOOP 修复报告

## 修复内容

### Fix 1: 同步 `_loop_generate_pre_stmts` docstring 首行「init_blocks」具误导性表述

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:4197`（`_loop_generate_pre_stmts` docstring 首行）

**问题根因**（docstring 与函数体实际行为不一致）：

`_loop_generate_pre_stmts` docstring 首行为：
```
"""从init_blocks和内层for循环的iter_setup提取前置语句
```

但函数体（L4237-4248）实际行为：
```python
if region.region_type == RegionType.FOR_LOOP:
    for child in (region.children or []):
        if isinstance(child, LoopRegion):
            if child.entry:
                for pred in child.header_block.predecessors:
                    if any(instr.opname in ('GET_ITER', 'GET_AITER') for instr in pred.instructions):
                        if pred in region.body_blocks:
                            _pre_stmts = self._loop_extract_pre_stmts_from_block(pred)
                            if _pre_stmts:
                                body_stmts.extend(_pre_stmts)
                            self.generated_blocks.add(pred)
                        break
```

仅处理 `region.region_type == FOR_LOOP` 时内层 for 循环（`child.header_block.predecessors`）中含 GET_ITER/GET_AITER 的前驱块。**并未处理 `region.init_blocks`**。

`region.init_blocks` 的实际处理在 `_loop_generate_for`（grep `if region.init_blocks:` 在 region_ast_generator.py 共 2 处命中，均位于 `_loop_generate_for` 内：L2977 / L3238）：
```python
if region.init_blocks:
    for ib in region.init_blocks:
        if ib == for_iter_setup:
            continue
        if ib not in self.generated_blocks:
            ib_stmts = self._generate_block_statements(ib)
            pre_stmts.extend(ib_stmts)
            ...
```

docstring 首行的「init_blocks」表述为历史遗留——可能源自早期 init_blocks 处理内联于此的设计，后分离至 `_loop_generate_for`，但 docstring 首行未同步。

**修复策略**（与 Pass5-LOOP / Pass6-LOOP 同型——仅 docstring 文本同步）：

保留原首行不变（保留作历史追溯），追加 `[Pass7-LOOP]` 段落说明：
1. 首行「init_blocks」表述具误导性，函数体实际不处理 `region.init_blocks`
2. `region.init_blocks` 的实际处理位置：`_loop_generate_for`（grep `if region.init_blocks:` 在本文件仅 2 处命中，均位于 `_loop_generate_for` 内 L2977/L3238）
3. 首行「init_blocks」表述为历史遗留
4. 本轮仅追加说明段落，未修改首行，未触碰可执行代码
5. 控制流不变，仅 docstring 文本同步
6. 验证：grep `_loop_generate_pre_stmts\(` 全仓仅 1 处调用点（L4101），调用点不依赖 init_blocks 处理（init_blocks 已由 _loop_generate_for 处理）

**为什么不直接修改首行**：
修改首行虽能消除误导，但首行作为「设计意图描述」可能为后续读者提供历史脉络（曾经包含 init_blocks 处理）。本轮保守追加段落说明而非修改首行，与 Pass5/Pass6-LOOP 同型保守策略一致。

控制流不变，仅 docstring 文本同步。

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
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| docstring 与函数体行为不一致（首行误导性 init_blocks 表述） | **已校正**（追加 [Pass7-LOOP] 段落说明实际处理位置） |

## 未完成项

1. **3 处 Pass 2 已标记的反模式**仍挂账 Pass 3+：
   - `_preceding_if_cond` 跨区域反向抓 IfRegion
   - 跨 LoopRegion 去重后处理
   - `_is_except_handler_block` 指令模式启发式
   本轮未重构这些反模式（需识别阶段统一改造）。

2. **`_loop_generate_pre_stmts` 重命名**（如改为 `_loop_extend_inner_for_iter_pre_stmts`）：
   收益小、改动面大，本轮保守不动。

3. **docstring 首行「init_blocks」表述**：本轮仅追加段落说明，未直接修改首行。
   后续 Pass 若实施「重命名以反映副作用语义」可一并修改首行。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_loop_generate_pre_stmts` docstring 追加 [Pass7-LOOP] 段落同步首行 init_blocks 误导性表述）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/LOOP/pass_07/fix_report.md`（本报告）
