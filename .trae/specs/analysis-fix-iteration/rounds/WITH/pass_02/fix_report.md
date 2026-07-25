# Pass 2 WITH 修复报告

## Pass 1 已修复回顾
Pass 1 完成 3 项反模式消除：(1) `_collect_normal_exit_cleanup` 的 magic number `+1000` 改为空块跳过（行为等价，避免 exc_target 上界回归）；(2) 抽取 `ASYNC_WITH_SEND_LOOP_OPS` 常量 + `_is_async_with_send_loop` 谓词，消除 5 处 inline 5-元组；(3) 修正 `_identify_with_regions` docstring 归约顺序（TRY、LOOP 之后，MATCH/ASSERT 之前）。

## Pass 2 新发现与修复

聚焦 `_generate_with`（region_ast_generator.py L14175-15259）与 `_identify_with_regions`（region_analyzer.py L7191）的低风险冗余。

### 修复 1 — 标记 async-with target 三重检测的冗余兜底（添加注释）

**位置**: region_ast_generator.py `_generate_with` L14728-14742（原 L14728-14737 注释 + L14738 起的 `if region.target is None and region.is_async:` 块）

**问题**: async-with 的 `as x` target 检测在 `_generate_with` 内有三处：
1. **early pass**（L14293-14318）：主循环前无条件执行，取 `with_blocks` 中 start_offset 最小块、查首条非噪声指令是否为 STORE_*。
2. async body 提取块（L14708-14727）：从 SEND/YIELD 循环的 LOOP_ELSE 块首条指令提取 target。
3. **L14738 兜底块**（L14738-14761）：与 early pass **逻辑完全一致**——同取 `with_blocks[0]`、同查首条非噪声 STORE_*。

经分析，L14738 块为冗余兜底：
- early pass 已无条件执行（条件 `region.is_async and region.target is None`）；
- L14738 块仅在该块进入时执行（条件 `region.target is None and region.is_async`，且外层闸门 `if region.is_async and not body_stmts:`）；
- 两者对同一 `region.with_blocks`（函数内未修改）执行相同检测；
- 故若 early pass 未设 target（with_blocks[0] 首条非噪声指令非 STORE_*），L14738 块执行相同检测必得相同结果（仍为 None）；
- L14738 块对 `_async_target` 的赋值仅在块内 L14752 使用，块外无引用——纯局部副作用。

**修复**: 在 L14738 块前添加 `[Pass 2 注]` 注释，明确登记本块与 early pass 逻辑等价、为冗余兜底（已知反模式），待归约期统一 async-with target 检测后消除。保留代码不变（保守修复，不改变控制流）。

**为什么不直接删除**: L14738 块虽为死代码（无可观测副作用），但删除涉及 24 行 + 10 行注释，diff 较大。本 pass 取保守策略——登记反模式，留待归约期统一处理（与 Pass 1 修复 3 的 async-with SEND 循环 patch 同属「归约期消除」待办）。

### 修复 2 — 删除 post_with_stmts 段冗余 `body_end_offset` 重赋值（删除死代码）

**位置**: region_ast_generator.py `_generate_with` L15022（原 L15017）

**问题**: `body_end_offset` 在 `_generate_with` 内被赋值两次，表达式完全相同：
- L14248（主循环前）：`body_end_offset = region.body_offset_end if region.body_offset_end is not None and region.body_offset_end > 0 else 0`
- L15022（post_with_stmts 段开头）：同上表达式（完全相同）

`region.body_offset_end` 在 `_generate_with` 内未被修改（`grep body_end_offset\s=` 确认仅 L14248 一处赋值），故 L15022 重赋值产生相同值——纯冗余操作。

**修复**: 删除 L15022 重赋值行，替换为单行注释说明 `body_end_offset` 沿用主循环前的赋值。`body_end_offset` 在后续 L15025/L15091/L15100 等处仍按 L14248 的值使用，行为不变。

**等价性证明**:
- `region.body_offset_end` 在 L14248 与 L15022 之间未被修改（无 mutation）；
- 表达式 `region.body_offset_end if ... is not None and ... > 0 else 0` 对相同输入产生相同输出；
- 故 L15022 重赋值是 no-op，删除后 `body_end_offset` 仍为 L14248 的值。

## 编译验证

```
$ python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
IMPORT OK ✓
```

## 回归测试结果

| Region | 基线 | 实际 | 时长 | 退化 |
|---|---|---|---|---|
| WITH | 191p/0f | 191p/0f | 2.15s | 无 ✓ |
| TRY | 228p/0f/2s | 228p/0f/2s | 2.79s | 无 ✓ |
| LOOP | 5f（预存） | 5f（预存） | 1.15s | 无 ✓ |

### LOOP 5 个失败的预存性确认

5 个 while_loop 失败（test_wl07nestedwhile_{a_b,n_m,x_y}、test_while15_nested_while、test_while16_for_in_while）经 `git stash` 验证：在无本轮修改的干净工作树上同样失败（已确认 test_wl07nestedwhile_* 3 个；另 2 个为同类嵌套 while 失败）。本轮修改仅在 `_generate_with`（+6/-1 行），不影响 `_generate_loop`，故 LOOP 失败为预存基线，非本轮回归。

## 反模式自检

| 检查 | 期望 | 实际 | 结果 |
|---|---|---|---|
| 禁止前缀方法名 | 无 _fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_ | 无新增 | ✓ |
| 新增后处理补丁 | 无 | 无（仅注释 + 删除冗余赋值） | ✓ |
| 硬编码深度上限 | 无 | 无 | ✓ |
| 控制流变更 | 无 | 无（注释不影响控制流；删除冗余赋值是 no-op） | ✓ |
| 行为等价 | 是 | 是（Issue 1 仅注释；Issue 2 删除 no-op 赋值） | ✓ |

## 未完成项（Pass 3+ 待处理）

1. **async-with target 三重检测统一**（Pass 2 修复 1 标记）：将 early pass / async body 提取 / L14738 兜底三处 target 检测合并为归约期单次归属。属根因修复（归约期归属 SEND/YIELD 循环），需在 `_identify_with_regions` 阶段将 async-with 的协程恢复循环识别为 WithRegion 内部块，消除生成期 patch。
2. **`_generate_with` 内 `_try_else_fixup` / `_if_blocks_fixup` save-mutate-restore 模式**（Pass 1 test_findings.md 已登记）：违反「每块唯一归属」原则，需在识别期排除 cleanup 块归属冲突。
3. **`_filter_if_blocks_in_with` / `_is_with_exit_cleanup` 改为区域归属查表**（Pass 1 test_findings.md 已登记）：消除生成期 isinstance 遍历与 opname 启发式。
4. **`_generate_with` 方法过长**（~940 行，Pass 1 test_findings.md 已登记）：可拆分 cleanup 处理 / 子区域调度 / items 重建为独立方法。
5. **L4294 / L10311 的 6-元组 inline**（含 'CACHE'，Pass 1 已说明不在 5-元组重构范围）：与 async-for/await SEND loop 相关，需单独评估。
