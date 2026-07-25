# LOOP 区域 Pass 1 修复报告 (pass_01)

- 修复日期：2026-07-25
- 架构分析报告：`test_findings.md`（同目录）
- 修复文件：`core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`
- 算法原则：严格遵循区域归约 4 原则（自底向上归约、每块唯一归属、嵌套即抽象节点、父引用子入口）
- 修复策略：聚焦消除 3 处反模式（1 处死代码 + 3 个后处理补丁），判据基于区域结构属性
  （`block_to_region` 区域类型归属 + CFG 跳转结构），非指令名计数启发式

## 修复目标

依据架构工程师分析报告（`test_findings.md`），消除 LOOP 区域的 3 处反模式：

1. `_loop_generate_while` 中与上方完全重复的死代码块（region_ast_generator.py）
2. `_cleanup_try_else_in_loop_body` 后处理补丁（事后从 TryRegion.else_blocks 移除已被
   LoopRegion.body_blocks 占用的块）——应前移为识别期 `block_to_region` 守卫
3. `_detect_and_filter_conditional_recheck_fake_loops` +
   `_rebuild_block_roles_after_fake_loop_removal` 两个后处理补丁（事后识别并移除由
   `continue` 形成的条件重检假循环）——应前移为识别期结构判据

## 修复详情

### 修复 1 — 删除 `_loop_generate_while` 死代码

- 文件：`core/cfg/region_ast_generator.py`
- 位置：原 L3431-L3437（`if region.is_while_true and cond_block == region.header_block:`
  条件判据及其 5 行函数体 + 1 行尾随空行）
- 操作：删除该 7 行
- 根因：该条件判据与上方 L3424-L3429 的代码块**逐字重复**（同一 `if` 表达式、同一
  `body_stmts`/`result`/`output`/`return` 序列）。控制流上方命中即 `return output`，
  下方重复块永不可达，为零风险死代码
- 验证：修复前 `grep` 全文件该条件判据出现 2 次，修复后仅 1 次（保留 L3424）
- 原则：消除死代码反模式

### 修复 2 — `_find_loop_else` 加 `block_to_region` 守卫，消除 `_cleanup_try_else_in_loop_body`

- 文件：`core/cfg/region_analyzer.py`
- 新增方法：`_is_owned_by_other_region(block, exclude_loop_header) -> bool`（L3436）
  - 检测块是否已被**非本 LOOP** 的区域占用
  - 判据：`block_to_region[block]` 为 `TryExceptRegion` / `WithRegion` / `MatchRegion` /
    `AssertRegion` 时返回 True；为 `LoopRegion` 时，若其 `header_block` ≠
    `exclude_loop_header`（即嵌套的其他 LoopRegion）返回 True
  - 返回 True 表示该块不应纳入当前 LoopRegion.else_blocks
- 守卫调用点（3 处 else_blocks 收集点）：
  - L3542 — for-else DFS 收集点：`if cur not in body_set and not
    self._is_owned_by_other_region(cur, header)`
  - L3622 — while-else path_blocks 收集点：列表推导加 `and not
    self._is_owned_by_other_region(b, header)`
  - L3658 — while 无 natural_exit 过滤收集点：列表推导加 `and not
    self._is_owned_by_other_region(b, header)`
- 删除：
  - `_cleanup_try_else_in_loop_body` 方法体（原 L3320-L3369，~50 行）
  - `analyze()` 中 `self._cleanup_try_else_in_loop_body(loop_regions, try_regions)` 调用
    （原 L1599 附近）
- 根因：TryExceptRegion 在 LOOP 之前识别（analyze Phase 1），`block_to_region` 中
  TryRegion 已注册。原方案在 `_find_loop_else` 收集 else_blocks 时无差别纳入 TryRegion
  内部块，事后用 `_cleanup_try_else_in_loop_body` 从 TryRegion.else_blocks 移除已被
  LoopRegion.body_blocks 占用的块——这是「先污染后清理」的后处理补丁。守卫将判据前移
  到识别期，使 LoopRegion.else_blocks 一次正确
- 原则：每块唯一归属 + 嵌套即抽象节点——已被其他区域占用的块不纳入 LoopRegion；
  消除后处理补丁

### 修复 3 — 扩展 `_is_fake_loop` 识别 continue 假循环，消除两个后处理补丁

- 文件：`core/cfg/region_analyzer.py`
- 新增方法：`_is_continue_recheck_fake_loop(header, body, back_edge_sources) -> bool`
  （L4122，~61 行）
  - 判据（全部满足才返回 True）：
    1. **header 末指令为条件回边自循环**：`header.get_last_instruction().opname ∈
       {POP_JUMP_BACKWARD_IF_TRUE, POP_JUMP_BACKWARD_IF_FALSE}`，且其跳转目标为
       header 自身（条件回边自循环）
    2. **header 已被外层 LoopRegion 占用**：先查 `block_to_region[header]`，若为
       LoopRegion 且 `header_block ≠ header` 且 `header ∈ outer.body_blocks`，则取
       outer_header；否则回退查 `LoopAnalyzer.get_all_loops()` 找包含 header 的外层
       loop header（兼容外层 LOOP 尚未注册到 `block_to_region` 的时序）
    3. **body 中存在 continue 块**：body 中至少一个非 header 块的末指令为
       `JUMP_BACKWARD` / `JUMP_BACKWARD_NO_INTERRUPT`，且跳转目标为外层 LOOP 的
       header（continue 目标）
- 调用点：`_is_fake_loop` 方法开头（L4183）——`if
  self._is_continue_recheck_fake_loop(header, body, back_edge_sources): return True`
- 删除：
  - `_detect_and_filter_conditional_recheck_fake_loops` 方法体（原 L3371-L3449，~79 行）
  - `_rebuild_block_roles_after_fake_loop_removal` 方法体（原 L3255-L3318，~64 行）
  - `analyze()` 中相关调用块（原 L1607-L1614，~8 行）：
    ```python
    fake_loop_region_ids = self._detect_and_filter_conditional_recheck_fake_loops(loop_regions)
    if fake_loop_region_ids:
        self._rebuild_block_roles_after_fake_loop_removal(loop_regions, fake_loop_region_ids)
        loop_regions = [r for r in loop_regions if id(r) not in fake_loop_region_ids]
        all_regions = [r for r in all_regions if id(r) not in fake_loop_region_ids]
        for block, region in list(self.block_to_region.items()):
            if id(region) in fake_loop_region_ids:
                del self.block_to_region[block]
    ```
- 根因：原方案在 LOOP 识别完成后，事后扫描已创建的 LoopRegion，识别「条件重检假循环」
  并重建 `block_to_region`——这是「先创建后拆除」的后处理补丁，且 `_is_fake_loop` 中
  `len(body) != 2` 硬编码无法覆盖 continue 形态。新判据在识别期直接判定，由
  `block_to_region` 外层 LOOP 占用 + body 块 JUMP_BACKWARD 跳外层 header 的 CFG 结构
  驱动，不依赖 opname 计数
- 时序正确性：主循环按 `dominance_depth` 倒序处理，外层 LOOP 先识别先注册到
  `block_to_region`，内层假循环调用 `_is_fake_loop` 时外层已注册；判据 2 同时提供
  `LoopAnalyzer.all_loops` 回退路径以应对边界时序
- 原则：自底向上归约 + 每块唯一归属——continue 假循环的 header 实为外层 LOOP body
  内的条件重检块，不应单独成为 LoopRegion；消除后处理补丁 + 硬编码

## 编译检查

```bash
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```

- 结果：**通过**（exit code 0，输出 `COMPILE_OK`，无异常）

## 回归测试

三区域 bounded subset 回归（`run_region_tests.py`，300s 内完成）：

| 区域 | 基线 (passed/failed/total) | 修复后 (passed/failed/errors/total) | 耗时(s) | 状态 |
|------|----------------------------|-------------------------------------|---------|------|
| LOOP | 79 / 0 / 79 | 79 / 0 / 0 / 79 | 2.0 | 无退化 ✓ |
| TRY  | 80 / 0 / 80 | 80 / 0 / 0 / 80 | 2.5 | 无退化 ✓（验证修复 2 不影响 TRY）|
| IF   | 79 / 1 / 80 | 79 / 1 / 0 / 80 | 7.2 | 无退化 ✓（验证不退化）|

- LOOP 完全匹配基线（修复 1/2/3 未引入回归）
- TRY 完全匹配基线（修复 2 删除 `_cleanup_try_else_in_loop_body` 不影响 TRY 区域
  识别——TryRegion 仍按 Phase 1 顺序正常识别，守卫仅在 LoopRegion.else_blocks 收集
  时跳过 TryRegion 占用块，不修改 TryRegion 自身）
- IF 剩余 1 失败为预存（bounded subset 内，非本次引入）

## 反模式自检

```bash
# 1. 三个补丁方法应已删除（0 结果）
grep -n "_cleanup_try_else_in_loop_body\|_detect_and_filter_conditional_recheck_fake_loops\|_rebuild_block_roles_after_fake_loop_removal" core/cfg/region_analyzer.py
```
- 结果：**0 结果** ✓（三个补丁方法及调用均已删除）

```bash
# 2. 禁止前缀方法名（_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_）
grep -nE "^\s*def _(fix|patch|fallback|hack|workaround|temp|merge)_" core/cfg/region_analyzer.py core/cfg/region_ast_generator.py
```
- 结果：
  - `core/cfg/region_analyzer.py`：**0 结果** ✓
  - `core/cfg/region_ast_generator.py`：1 处预存——`_merge_block_is_loop_back_edge`
    （L18304）。经 `git diff` 验证，本次修复对 region_ast_generator.py **仅删除 7 行**
    （修复 1 死代码），未新增任何方法，该预存项非本次引入

```bash
# 3. 硬编码深度上限
grep -nE "depth > [0-9]" core/cfg/region_analyzer.py
```
- 结果：**0 结果** ✓

## 4 原则合规性自检

| 原则 | 合规性 | 说明 |
|------|--------|------|
| 1. 自底向上归约 | ✓ 合规 | 修复 3 依赖外层 LOOP 先于内层假循环识别注册到 `block_to_region`（主循环按 `dominance_depth` 倒序），并保留 `LoopAnalyzer.all_loops` 回退路径应对边界时序；不依赖事后重扫 |
| 2. 每块唯一归属 | ✓ 合规 | 修复 2 守卫确保已被 TryExceptRegion/WithRegion/MatchRegion/AssertRegion/嵌套 LoopRegion 占用的块不纳入 LoopRegion.else_blocks；修复 3 确保 continue 假循环 header 不被错误创建为独立 LoopRegion（其归属外层 LOOP）|
| 3. 嵌套即抽象节点 | ✓ 合规 | 修复 2 守卫使父 LoopRegion 通过 entry 引用子区域而非吞并子区域内部块；修复 3 消除假循环独立区域化，保持外层 LOOP 对该块的单一抽象 |
| 4. 入口引用语义 | ✓ 合规 | 守卫与假循环判据均基于区域结构属性（`block_to_region` 区域类型 + CFG 跳转目标），非 opname 计数启发式；不引入跨区域特例 |

## 修改文件清单

| 文件 | 修改内容 | diff 行数 |
|------|----------|-----------|
| `core/cfg/region_ast_generator.py` | 修复 1：删除 `_loop_generate_while` 中 L3431-L3437 重复死代码块 | -7 |
| `core/cfg/region_analyzer.py` | 修复 2：新增 `_is_owned_by_other_region`（L3436）+ 3 处收集点调用守卫（L3542/L3622/L3658）+ 删除 `_cleanup_try_else_in_loop_body` 方法及 `analyze()` 调用；修复 3：新增 `_is_continue_recheck_fake_loop`（L4122）+ `_is_fake_loop` 调用（L4183）+ 删除 `_detect_and_filter_conditional_recheck_fake_loops` / `_rebuild_block_roles_after_fake_loop_removal` 方法及 `analyze()` 调用 | +86 / -211（净 -125）|

## 复现命令

```bash
# 编译检查
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"

# 三区域 bounded subset 回归
python .trae/specs/analysis-fix-iteration/run_region_tests.py LOOP
python .trae/specs/analysis-fix-iteration/run_region_tests.py TRY
python .trae/specs/analysis-fix-iteration/run_region_tests.py IF

# 反模式自检
grep -n "_cleanup_try_else_in_loop_body\|_detect_and_filter_conditional_recheck_fake_loops\|_rebuild_block_roles_after_fake_loop_removal" core/cfg/region_analyzer.py
grep -nE "^\s*def _(fix|patch|fallback|hack|workaround|temp|merge)_" core/cfg/region_analyzer.py core/cfg/region_ast_generator.py
grep -nE "depth > [0-9]" core/cfg/region_analyzer.py
```

## 后续迭代遗留（非本轮范围）

依据 `test_findings.md`，以下问题留待后续迭代处理：

- 复合 and 条件链计数配额启发式（`_identify_loop_regions` 中 ~95 行）
- `_loop_generate_while` 中 `_preceding_if_cond` 拼装 BoolOp（反向抓前驱 IfRegion）
- `is_yield_from_loop` 与 TernaryRegion 块重叠事后移除
- 跨 LoopRegion 去重（`_identify_loop_regions` 末尾）
