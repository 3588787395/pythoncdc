# Pass 5 IF 修复报告

## 修复内容

### Fix 1: 标记 `_if_generate_branch_stmts` 死形参 `region=None` 与两个不可达分支

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:11937-11958`（`_if_generate_branch_stmts` 方法）

**问题根因**（Pass 1-4 未触及的死代码，与 Pass3-IF 删除 `_depth=0` 同型）：

全仓 grep `_if_generate_branch_stmts\(` 仅 4 行命中：
- L3211: `self._if_generate_branch_stmts(_filtered_else_blocks)`
- L3949: `self._if_generate_branch_stmts(_filtered_else_blocks)`
- L6607: `self._if_generate_branch_stmts(body_blocks_no_header)`
- L11937: 本函数定义

3 处调用点全部仅传入 `blocks`（位置参数），**从不**传 `region=` 关键字；测试文件中无任何直接调用。
故函数体内：

1. `region=None` 形参在调用点恒为 None（死形参）
2. `if region is not None: return self._generate_if(region)` 分支不可达
3. 末尾 `return []` 仅当 blocks/region 同时为 None 时可达，调用点亦不可达

与 Pass3-IF 删除 `_depth=0` 形参同型——都是「调用点从不传入」的死形参，差别仅在
`_depth=0` 完全未被函数体引用（纯死），而 `region=None` 在函数体内被引用（形成不可达分支）。

**修复策略**：
仅添加 `[Pass5-IF]` 标记注释，登记 3 处调用点行号（3211/3949/6607，与 Pass4-IF 注释中的
3207/3945/6597 同步漂移）与三项死代码清单。**不删除形参/不删除分支**——删除 `region` 形参需评估
`_process_if_blocks(blocks, region, branch='standalone')` 第二位置参数语义（当 region 为 None 时
`_process_if_blocks` 内 `if region and hasattr(region, 'children'):` 短路为 False，跳过子区域处理），
属控制流评估，超出本轮保守范围。

**为什么不直接删除（与 Pass3-IF 删 _depth=0 不同）**：
`_depth=0` 完全未被函数体引用，删除零副作用；`region=None` 形参虽调用点不传，但函数体内
`_process_if_blocks(blocks, region, branch='standalone')` 显式把 `region` 透传给下游
`_process_if_blocks`。删除 `region` 形参需同步把第二位置参数改为 `None` 字面量，并核对
`_process_if_blocks` 在 region=None 时的子区域跳过行为是否与 standalone 分支语义一致——
属控制流评估而非纯文本清理，本轮保守不动。

控制流不变，仅注释文本追加。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py IF
```
**结果**：`79 1 0 80 7.4 IF files=80` —— 与基线一致（79 passed, 1 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 死形参 + 不可达分支 | **已标记**（region=None 形参与 2 个不可达分支登记为已知死代码，待后续 Pass 删除） |

## 未完成项

1. **`region=None` 死形参 + 2 个不可达分支删除**（本轮已标记）：低风险但需评估
   `_process_if_blocks` 第二位置参数语义，超出本轮保守范围。
2. **TODO[pass2-CC] 未完成**：`_detect_boolop_after_chained_compare` 与
   `_if_generate_full_elif_chain` 中的 save/restore 块仍存在。
3. **baseline_failures.txt 中的 1 处预存失败**：非本轮引入，未处理。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：追加 [Pass5-IF] 死形参标记注释）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/IF/pass_05/fix_report.md`（本报告）
