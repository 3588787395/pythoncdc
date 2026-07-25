# 修复实施报告 — Pass 1 / TRY 区域

基于架构工程师分析报告 `test_findings.md`，本轮实施 3 项零/低风险修复，聚焦反模式消除，不触碰失败用例。

## 1. 实施的修复清单

### 修复 A — 统一 L4688 docstring 与实现顺序
- **文件**: `core/cfg/region_analyzer.py`
- **位置**: L4688（`_identify_try_except_regions` docstring）
- **改动**: 优先级顺序由 `TRY > WITH > LOOP > IF > ASSERT` 改为 `TRY > LOOP > WITH > MATCH > ASSERT`
- **理由**: 与 L1226 注释及 L1231-L1236 实际调用顺序（TRY→LOOP→WITH→MATCH→ASSERT）一致，消除文档-代码矛盾
- **行为影响**: 零（仅文档）

### 修复 B — 移除 `_find_return_through_cleanup_chain` 的 max_depth=6 硬编码
- **文件**: `core/cfg/region_ast_generator.py`
- **位置 1**: L13190 方法签名
  - 改动: `def _find_return_through_cleanup_chain(self, start_block, max_depth=6):` → `def _find_return_through_cleanup_chain(self, start_block):`
- **位置 2**: 原 L13245-L13246 深度检查（已删除）
  - 改动: 删除 `if len(path) > max_depth:` 与 `continue` 两行
- **调用点核查**: Grep `_find_return_through_cleanup_chain` 仅 2 处出现（定义 + L13719 调用），调用方 `self._find_return_through_cleanup_chain(block)` 未传 max_depth，无需同步更新
- **终止性保证**: 保留 `visited = {id(start_block)}` 集合（L13238）防环，`if id(current) in visited: continue`（L13242）+ `visited.add(id(current))`（L13244）保证每个 block 至多处理一次；CFG 规模有限，纯依赖 visited 即可终止
- **行为影响**: 解锁长 cleanup 链场景（原 max_depth=6 会误截断 >6 跳的合法 cleanup 路径）

### 修复 C — 提取 pre_handler_blocks 应用逻辑为单一共享块
- **文件**: `core/cfg/region_analyzer.py`
- **改动 1**: L4893 新增 `pre_handler_blocks = []` 外层初始化（紧邻 `pre_handler_entry_candidate = None`），确保两分支内层条件不命中时变量仍有定义
- **改动 2**: 删除 except 分支（原 L4922-L4929）的 `if pre_handler_blocks:` 应用块
- **改动 3**: 删除 finally 分支（原 L4955-L4962）的 `if pre_handler_blocks:` 应用块
- **改动 4**: 在 if/else 之后（L4949-L4956）新增共享应用块（12 空格缩进，与外层 `if handler_type` 同级）：
  ```python
  if pre_handler_blocks:
      for phb in pre_handler_blocks:
          if phb not in try_blocks:
              try_blocks.insert(0, phb)
      try_start_for_blocks = min(try_start_for_blocks,
                                 min(b.start_offset for b in pre_handler_blocks))
      pre_handler_entry_candidate = max(pre_handler_blocks,
                                         key=lambda b: b.start_offset)
  ```
- **等价性论证**:
  - except/except_star 与 finally 两个 `if handler_type` 分支互斥（handler_type 单值），至多一个分支收集 pre_handler_blocks
  - 各分支保留独立的 `pre_handler_blocks = []` 收集逻辑与边界判定（handler_in_try_range / _need_pre_expand），仅移除应用块
  - 收集后 fall-through 到共享应用块；若内层条件不命中，pre_handler_blocks 保持外层 `[]`，共享块空操作
  - 边界判定逻辑未改动，行为等价

## 2. 编译检查结果

```
$ python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; print('IMPORT OK')"
IMPORT OK
```
退出码 0，无异常。

## 3. 回归测试结果（passed/failed/total）

| 区域 | 基线 | 实测 | 结果 |
|------|------|------|------|
| TRY  | 80p/0f/80 | 80p/0f/0e/80 (2.6s) | ✓ 一致 |
| LOOP | 79p/0f/79 | 79p/0f/0e/79 (2.2s) | ✓ 一致 |
| IF   | 79p/1f/80 | 79p/1f/0e/80 (7.3s) | ✓ 一致 |

三区域均与基线一致，无退化。IF 区域既有 1 个失败用例为基线既有状态，本轮未触碰。

## 4. 反模式自检结果

```
$ grep -n "max_depth=6\|max_depth = 6" core/cfg/region_ast_generator.py
(无输出)

$ grep -n "len(path) > max_depth" core/cfg/region_ast_generator.py
(无输出)
```
两项 grep 均返回 0 匹配，硬编码深度上限已消除。

禁止前缀方法名自检：
```
$ grep -n "def _fix_\|def _merge_\|def _patch_\|def _fallback_\|def _hack_\|def _workaround_\|def _temp_" core/cfg/region_ast_generator.py
18302:    def _merge_block_is_loop_back_edge(self, region: TernaryRegion) -> bool:
```
仅 L18302 一处 `_merge_block_is_loop_back_edge`，为 TernaryRegion 上下文预存方法（分析报告已标注"非TRY专属"），非本轮引入，不在本次修复范围。本轮未新增任何禁止前缀方法。

## 5. 4 原则合规性自检

| 原则 | 修复前状态 | 本轮改善 |
|------|-----------|---------|
| 原则 1（自底向上归约） | TRY 优先级最高 + try_try 嵌套补偿 | 文档矛盾消除（修复 A），优先级声明与实现一致；嵌套补偿未触碰（高风险，后续迭代） |
| 原则 2（每块唯一归属） | generated_blocks 反复 add/discard | 未触碰（本轮范围外） |
| 原则 3（嵌套即抽象节点） | _generate_try_body 4 并列启发式 | 未触碰（中风险，后续迭代） |
| 原则 4（入口引用语义） | entry_block 二次改写 | 未触碰；pre_handler_blocks 应用逻辑提取为单一机制（修复 C），更易扩展 |

反模式消除汇总：
- ✅ 文档-代码矛盾（修复 A）：消除
- ✅ 硬编码深度上限 max_depth=6（修复 B）：消除
- ✅ 复制粘贴后处理（修复 C）：消除
- ⏳ try_try 嵌套补偿 / _skipped_outer_try 包装 / R4-09 系列 / Pattern A/B/C/E fix：后续迭代
- ⏳ _generate_try_body 嵌套检测统一为区间包含：后续迭代

## 6. 实施约束合规

- ✅ 未引入 _fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_ 前缀方法名
- ✅ 未引入硬编码深度上限（移除 max_depth=6，纯依赖 visited 防环）
- ✅ 未新增后处理补丁
- ✅ 最小修改原则（3 处精确编辑，仅触碰报告指明位置）
- ✅ 未修改测试文件
- ✅ 未 commit / push（由主调度器统一）
