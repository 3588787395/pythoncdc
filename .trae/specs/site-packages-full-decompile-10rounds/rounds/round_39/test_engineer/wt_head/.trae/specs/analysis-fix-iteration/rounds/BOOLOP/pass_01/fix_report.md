# 修复实施报告 — Pass 1 / BOOLOP 区域

修复工程师依据架构工程师分析报告（`test_findings.md`）实施 3 项反模式消除修复。
全部聚焦于反模式消除，未调换 BOOLOP/TERNARY 识别顺序。

## 修复清单

### 修复 1 — 消除硬编码深度上限 `_walk_count < 5`（极低风险）

- 文件: `core/cfg/region_analyzer.py`
- 位置: `_is_scenario_b_ternary` 检测（原 L15500-L15537 区域）
- 操作:
  - 删除 `while _ft_walk and _walk_count < 5 and ...` 中的 `_walk_count < 5` 条件
  - 删除 `_walk_count = 0` 初始化与 `_walk_count += 1` 计数
  - 保留 `_visited_ft` 集合防环逻辑
- 终止保证: 循环体内已存在结构性终止条件（找到 JUMP_FORWARD 目标是 loop header
  即 `break`；无更多 fall-through 后继时 `_ft_walk = None` 退出）；`_visited_ft`
  集合保证有限 CFG 内必收敛。移除 `< 5` 上限可识别深度更大的合法 Scenario B
  ternary 模式，不再漏检。

### 修复 2 — 统一 guard_idx 修剪逻辑，移至区域创建期（中低风险）

- 文件: `core/cfg/region_analyzer.py`
- 抽取辅助方法: `_trim_boolop_guard_prefix(self, op_chain, loop_region) -> list`
  （位于 `_create_boolop_region_from_chain` 之前，L14800）
  - 纯函数，无副作用：接收 op_chain 与 loop_region，返回修剪后 chain 或原 chain
  - 内含循环体变量收集（BFS from header，跳过 back_edge_block）+ guard 前缀定位
    （首个加载变量与循环体变量无交集的前导块）
- 创建期调用: `_create_boolop_region_from_chain` 起始处（normalize 之后）
  - 先通过条件链匹配定位 op_chain 隶属的 LoopRegion（移植自原主循环事后修剪的
    匹配逻辑，使用 `self._filter_regions(self.regions, LoopRegion)`，等价于原
    `existing_regions` 过滤——Phase 2 不新增 LoopRegion）
  - 调用 `_trim_boolop_guard_prefix(chain, _loop_for_chain)` 一次性应用修剪
  - 仅当修剪实际发生且修剪后 chain < 2 时返回 None（对应原事后修剪中
    `_guard_idx is not None and len(_new_chain) < 2` 的丢弃分支）
- 删除的事后修剪代码:
  - 原主循环修剪（约 78 行）：`for br in boolop_regions: ... trimmed.append(...)`
    + `boolop_regions[:] = trimmed`
  - 原 while 条件重识别后修剪（约 51 行）：`_rv2`/`_guard_idx2`/`_new_chain2`
    重创建逻辑
- 关键正确性细节:
  - 1-元素短路链（JUMP_IF_FALSE_OR_POP）合法——第二操作数位于 merge 块中，
    原 `_create_boolop_region_from_chain` 无 len 检查。故 `len(chain) < 2`
    拒绝条件加上 `_loop_for_chain is not None` 前提（匹配逻辑要求 chain[:-1]
    非空才会设定 `_loop_for_chain`，1-元素链恒为 None），避免误拒合法短路链。
  - 初版误用无条件 `if len(chain) < 2: return None`，导致 60 个 BOOLOP 用例
    退化为 IfRegion；修正后回归基线。
- 行为等价性: 修剪判据（循环体变量集 + 前导块变量无交集）与原两处事后修剪
  完全一致，仅时机前移至创建期。变量名启发式收敛到单一调用点。

### 修复 3 — `_is_not_ternary_boolop_pattern` 委托 `_is_equivalent_exit_block`（低风险）

- 文件: `core/cfg/region_analyzer.py`
- 位置: `_is_not_ternary_boolop_pattern` 嵌套函数内（原 L11619-L11624）
- 操作: 将原「非噪音指令序列 (opname, argval) 元组精确比较」替换为
  `return self._is_equivalent_exit_block(fv_exit_bo, tv_exit_bo)`
  - 保留 L11617 `if fv_exit_bo is tv_exit_bo: return True` 显式短路（减少递归
    开销，helper 内部亦含此短路）
- 判据分析:
  - 原: 通用指令序列精确匹配（任意指令）
  - helper: trivial-return 块 + only-jumps 链等价（更受限）
  - 在 `not(ternary)` 上下文中，exit 块为 return body（如 `LOAD_CONST None;
    RETURN_VALUE`），属 trivial-return，helper 判据覆盖该场景
- 测试验证: TERNARY 基线 69p/7f/76 未退化，确认 helper 判据在该上下文中等价。

## 验证结果

### 编译检查
```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
→ COMPILE OK（无异常）
```

### 回归测试（300s 内）
| 区域 | 基线 | 修复后 | 结果 |
|------|------|--------|------|
| BOOLOP | 79p/0f/79 | 79p/0f/79 | ✅ 持平 |
| TERNARY | 69p/7f/76 | 69p/7f/76 | ✅ 持平 |
| IF | 79p/1f/80 | 79p/1f/80 | ✅ 持平 |

三个测试集均与基线完全一致，无退化、无改进（聚焦反模式消除，不调换识别顺序）。

### 反模式自检
- `grep -n "_walk_count < 5" core/cfg/region_analyzer.py` → 0 匹配 ✅
- `grep -n "_walk_count" core/cfg/region_analyzer.py` → 0 匹配（计数器完全移除）✅
- `grep -n "guard_idx" core/cfg/region_analyzer.py` → 仅 1 处注释（解释与原逻辑
  对应关系），无散布变量 ✅
- 禁止前缀方法名（`_fix_`/`_merge_`/`_patch_`/`_fallback_`/`_hack_`/`_workaround_`/
  `_temp_`）→ 本次未新增；新方法 `_trim_boolop_guard_prefix` 合规 ✅
- 未新增后处理补丁 ✅
- 未修改测试文件 ✅
- 未调换 BOOLOP/TERNARY 识别顺序 ✅

## 修改文件
- `core/cfg/region_analyzer.py`（唯一修改文件）

## 未 commit / 未 push（由主调度器统一）

## 后续迭代建议（本轮未做，见 test_findings.md）
- BOOLOP→TERNARY 识别顺序调换（高风险，影响全流水线）
- `_detect_boolop_after_chained_compare` 生成期后处理移除
- 子串匹配 `'FALSE' in opname` 统一替换为结构判据
