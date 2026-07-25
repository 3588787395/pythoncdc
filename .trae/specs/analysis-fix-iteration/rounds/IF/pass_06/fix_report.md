# Pass 6 IF 修复报告

## 修复内容

### Fix 1: 完成 Pass5-IF deferred 的 `_if_generate_branch_stmts` 死形参与不可达分支删除

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:11952`（`_if_generate_branch_stmts` 方法）

**问题根因**（Pass5-IF fix_report §未完成项 1 已识别为低风险但 deferred 至后续 Pass）：

Pass5-IF fix_report.md §未完成项 1 已登记：
> 1. **`region=None` 死形参 + 2 个不可达分支删除**（本轮已标记）：低风险但需评估
>    `_process_if_blocks` 第二位置参数语义，超出本轮保守范围。

本轮 Pass 6 在 Pass 5 标记的基础上完成评估并实施删除：

1. **死形参 `region=None`**：3 处调用点（line 3211/3949/6607，Pass5-IF 已 grep 确认）
   均仅传入 `blocks` 位置参数，从不传 `region=` 关键字。`region` 在函数体内恒为 None。
2. **不可达分支 `if region is not None: return self._generate_if(region)`**：region 恒为
   None，该分支永不触发。
3. **末尾 `return []` 仅当 blocks 为 None 时可达**：调用点均传入非空 blocks（外层
   `if _filtered_else_blocks else []` / `if branch_stmts and body_stmts` 已 guard），
   但保留以维持函数纯防御性兜底契约，不视为死代码。
4. **`_process_if_blocks(blocks, region, branch='standalone')` → `_process_if_blocks(blocks, None, branch='standalone')`**：
   经核对 `_process_if_blocks`（L10471 定义）首句 `if region and hasattr(region, 'children'):`
   短路为 False（`None and ...`），与原 region=None 调用行为完全等价。子区域跳过逻辑
   （child_region_blocks/child_entries/child_expr_regions 全部为空集）与原版一致。

**修复策略**（与 Pass3-IF 删 `_depth=0` 同型——纯死代码删除）：

1. 删除 `region=None` 形参（签名 `def _if_generate_branch_stmts(self, blocks=None, region=None)`
   → `def _if_generate_branch_stmts(self, blocks=None)`）
2. 删除 `if region is not None: return self._generate_if(region)` 不可达分支（2 行）
3. 把 `_process_if_blocks(blocks, region, branch='standalone')` 中的 `region` 改为 `None` 字面量
4. 追加 `[Pass6-IF]` 段落说明完成情况、语义等价性证明、与 Pass5-IF 标记的对应关系

**为什么不直接重命名 / 改返回类型**（与 Pass5-LOOP 改 `-> None` 不同）：
本函数实际行为：通过副作用修改 `body_stmts` 参数（在 `_process_if_blocks` 内部 extend）
并返回 `self._coalesce_compares(stmts)` 列表。返回值被 3 处调用点使用
（`else_stmts = self._if_generate_branch_stmts(...) if ... else []` /
`branch_stmts = self._if_generate_branch_stmts(...)`）。返回类型与函数语义匹配，无需重命名。
本轮仅做 Pass5-IF deferred 的死形参/不可达分支删除，不改函数签名语义。

**与 Pass3-IF 删 `_depth=0` 的对比**：

| 维度 | Pass3-IF (`_depth=0`) | Pass6-IF (`region=None`) |
|---|---|---|
| 形参被函数体引用 | 否（纯死） | 是（被 _process_if_blocks 透传） |
| 删除影响范围 | 仅签名（无调用点透传） | 签名 + 函数体 1 处调用（region→None 字面量） |
| 调用点变更 | 无 | 无（3 处调用点均不传 region=） |
| 控制流变更 | 无 | 无（region 恒为 None，_process_if_blocks 短路） |
| 风险等级 | 零风险 | 低风险（已核对 _process_if_blocks None 兼容性） |

控制流不变，仅删除死形参与不可达分支。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py IF
```
**结果**：`79 1 0 80 7.2 IF files=80` —— 与基线一致（79 passed, 1 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（region 恒为 None，行为完全等价） |
| 测试文件修改 | 未修改任何测试文件 |
| 死形参 + 不可达分支 | **已删除**（Pass5-IF deferred 项完成：删除 `region=None` 形参 + 1 个不可达分支 + 1 处变量→字面量替换） |

## 未完成项

1. **TODO[pass2-CC] 未完成**：`_detect_boolop_after_chained_compare` 与
   `_if_generate_full_elif_chain` 中的 save/restore 块仍存在，等待后续 Pass
   将「CC + and/or 短路块」识别阶段统一为 `BoolOpRegion` 后一并删除。
2. **baseline_failures.txt 中的 1 处预存失败**：非本轮引入，未处理。
3. **`_if_generate_branch_stmts` 末尾 `return []` 防御性兜底**：调用点已 guard
   （`if _filtered_else_blocks else []`），但保留以维持函数纯防御性契约，
   不视为可删死代码，本轮不动。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：删除 `_if_generate_branch_stmts` `region=None` 死形参与不可达分支 + 追加 [Pass6-IF] 段落）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/IF/pass_06/fix_report.md`（本报告）
