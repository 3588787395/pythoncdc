# Round 35 修复报告：datetime_func.change_2str_of_time_2_datetime 双角色块 STORE_FAST 变体

- 日期：2026-08-30
- 目标：`IQCommon/util/datetime_func.pyc::change_2str_of_time_2_datetime`（round_34 遗留，25/26）
- 改动文件：`core/cfg/region_ast_generator.py`（+34/−12 净）

## 症状

```
原始:
  source_start = datetime.datetime.strptime(startttime[:8] + (len(startttime[8:]) == 4 and startttime[8:] or '0000'), '%Y%m%d%H%M')
  source_end   = datetime.datetime.strptime(endtime[:8]   + (len(endtime[8:])   == 4 and endtime[8:]   or '1530'), '%Y%m%d%H%M')
  return source_start, source_end

反编译（修复前）:
  source_start = datetime.datetime.strptime(...)   # OK
  source_end = endtime[8:]                          # 退化
  return '1530'                                     # 退化
```

指令数：原始 67 vs 反编译 38 → 修复后 **67/67 逐条零差异**。

## 根因（两层叠加）

### 层 1：双角色块的 value_target（STORE_FAST）变体

连续两条 `x = f(a and b or c)` 赋值时，第 1 条的 merge_block（blk@140：
`BINARY_OP + CALL + STORE source_start + 第 2 条的条件求值`）**同时是第 2 条
BoolOp 的 entry**。`block_to_region` 是单值映射（先到先得），下游 BoolOpRegion
对 `get_region_for_block` 不可见，永不被 `generate()` 顶层派发 → 其语句退化为
通用块语句（source_end 的 strptime 调用丢失、return 变 `return '1530'`）。

这与 Round 02 F3 / R78 修复的 STORE_ATTR 变体**同构**，但 F3/R78 只修了
STORE_ATTR 分支；本函数的赋值是 STORE_FAST（value_target 分支），漏掉。
修复：与 R78 一致，用 `_downstream_region_entry` 依原则 4（父引用子入口）
派发下游结构化区域。

### 层 2：双角色块 + 下游为「退化容器区域」时 post-store 被整体跳过

修复层 1 后，blk@300（第 2 条 BoolOp 的 merge_block）同时被 analyzer 的
孤儿释放机制（generate() 顶部为 orphaned blocks 建 BASIC Region）认领为
普通 `Region(300)` 的 entry，但该普通 Region **只含 300 一个块、不向外延伸**
（退化容器）。`_downstream_region_entry` 依结构判据（`set(r.blocks) - {block}`
非空）正确地返回 None，然而旧分支 `if not _merge_is_other_entry_r10f3:`
此时为 False，R61 post-store 处理被**整体跳过** → 尾部
`return source_start, source_end`
（`LOAD source_start / LOAD source_end / BUILD_TUPLE / RETURN_VALUE`）
静默丢失，函数以隐式 `return None` 结束。

## 修复

```python
_downstream_r35 = None
if _merge_is_other_entry_r10f3:
    # 层 1：双角色块 → 派发下游结构化区域（BoolOp→BoolOp，与 R78 一致）
    _downstream_r35 = self._downstream_region_entry(region.merge_block, region)
    if _downstream_r35 is not None:
        ...dispatch + return results...
    # 层 2：下游是退化容器（返回 None）→ 不跳过，fall through 到 R61 post-store
if not _merge_is_other_entry_r10f3 or _downstream_r35 is None:
    # [R61 fix] 原有 post-store 提取逻辑（保持不变）
```

语义：双角色块但下游退化时，merge 块 STORE 之后的指令仍属**父 BoolOp 的尾部
语句**（本函数的 return 元组），必须走 R61 post-store 路径发射，不得跳过。

## 实测结果（全部实测值，PYTHONHASHSEED=0）

- 目标函数 `change_2str_of_time_2_datetime`：**orig=67 / decomp=67，逐条指令零差异**
- 产物恢复完整：
  `source_end = datetime.datetime.strptime(endtime[:8] + (len(endtime[8:]) == 4 and endtime[8:] or '1530'), '%Y%m%d%H%M')` +
  `return (source_start, source_end)`
- `datetime_func.pyc` 文件级：**25/26 → 26/26（ok）**
- 合规：
  - `check_patch_patterns.py`：PASS
  - `check_hardcoded_opcodes.py`：region_analyzer=694、region_ast_generator=1370，
    **与 R33/R34 基线持平，本轮零新增硬编码 opcode**
- 全量 402 回归（R35c 串行 3 片，PYTHONHASHSEED=0）：**ok=314 / partial=88 / failed=0，
  函数级 5448/5746**；对比 round_34 基线（312 ok / 90 partial，5446/5746）：
  **回归 0、改进 2**（IQCommon/util/datetime_func 25→26、IQData/utils/datetime_func 24→25）；
  quotation.pyc 恢复基线 143/143（R34 即 ok，回归修复到位）

## R35b/c 回归修复（quotation 143→142→141→143）

### 症状（第一轮修复引入的回归）

`site-packages/fly/data/quotation.pyc`：HEAD 基线 **143/143 ok** → R35 第一轮修复后
**142/143**（`load_bars_from_hundsun` 与 `fill_minute_or_day_blank` 的 elif 条件丢失）
→ R35b 尝试后更差 **141/143**。stash 对照（当前代码用 HEAD 重测）实锤为修复所致。

### 根因（两层）

1. **R35 第一轮把「有父区域的 BoolOpRegion」也提前派发了**：quotation 中
   merge=424/400/1862 的认领者是 BoolOpRegion(286/424)，`_downstream_region_entry`
   返回非 None → 提前派发。但这些 BoolOpRegion 的 `parent=IfRegion(214)`，HEAD 中
   本就由父 IfRegion 的 `boolop_children` 机制正常派发。提前派发把下游 blocks
   （含 IfRegion 的 entry blk@584/560）标记为 `generated_blocks`，破坏后续
   IfRegion(584) 的派发 → elif 条件（`POP_JUMP_FORWARD_IF_FALSE`）丢失。
2. **R35b 的「结构化 owner 由顶层 containment 派发」判断不充分**：若派发失败
   （如 blk@584 的 block_to_region owner 是 IfRegion(584)，`_downstream_region_entry`
   依「r is owner」跳过返回 None），此时跳过 post-store 仍无法补救——因为先前
   提前派发已污染 `generated_blocks`，顶层层层过滤失效，elif 仍丢。

### 关键区分（R35c 最终方案）

用**下游区域的 parent 是否为空**区分两种场景：

- **`parent is None`（顶层 BoolOpRegion）**：如 datetime_func 的 BoolOpRegion(0/140)。
  无父区域负责派发，HEAD 永不被 generate() 派发 → source_end 与尾部 return 丢失。
  **必须**提前派发（R35 第一轮的有效部分）。
- **`parent = IfRegion`（有父区域）**：如 quotation 的 BoolOpRegion(286/424)，
  由父 IfRegion 的 `boolop_children` 机制正常派发。**完全跳过**：不派发、不标记
  blocks、不提取 post-store，保持 HEAD 行为。

```python
# [R35c] 仅顶层（parent is None）BoolOpRegion 提前派发；有父区域者交由父派发
if (_downstream_r35 is not None
        and getattr(_downstream_r35, 'parent', None) is None):
    ...dispatch + return results...
# parent 非 None 或派发失败：跳过 post-store，交由父区域/顶层 containment 处理
```

### 实测结果（R35c，PYTHONHASHSEED=0）

- `quotation.pyc`：**141/143 → 143/143（ok，完全恢复 HEAD 基线）**
- `datetime_func.pyc`：**26/26（ok，保持 R35 主修复成果）**
- 全量 402 回归（合并结果 scan_after_fix_r35.json）：**回归 0、改进 2**（详见上文实测结果）

## 遗留（Round 36 候选）

- `IQEngine/plugins/plugin_fly_data/fly_api/order_api_trade` 23/24（order_market）
- `IQEngine/account/trade` 22/23（create_trade）
