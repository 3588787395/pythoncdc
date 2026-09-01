# Round 34 修复报告：推导式赋值目标支持下标/属性 + 推导式块尾语句边界修复

日期：2026-08-30　修复人：修复工程师　基线：ok=311 / partial=91 / failed=0，funcs=5439/5746（Round 33）

## 1. 主攻目标与根因（已亲自实测验证）

主攻：`IQCommon/graph.pyc`（Round 33 候选清单成功率最高 partial，30/31），
失败函数 `_process_task_queue`（原始 378 指令 vs 反编译 354 指令，true_diffs=304）。
经 CFG 诊断（diag_graph_try.py + sys.settrace 追踪 `_generate_block_statements_body`），
定位到两处独立根因，均在 `core/cfg/comprehension_generator.py`。

### 1.1 推导式赋值劫持块后，尾部语句边界被吞（354 vs 378，根因 1）

- 现象：`_process_task_queue` 的 try 块内
  `value_list.append(nodes)`、`tmp_node_dict[node] = value_list`、
  `queue[task_id] = tmp_node_dict`、`return None` 编译为单基本块
  blk@242 的多语句序列（含 `<listcomp>` 的 MAKE_FUNCTION）。
- 根因：`try_generate_comprehension_assign`（comprehension_generator.py）
  在 `_generate_block_statements_body` 中先于通用语句路径运行，检测到
  块内含 `<listcomp>` 的 MAKE_FUNCTION 即整体接管该块；其
  `_generate_remaining_stmts` 处理剩余指令时：
  - **POP_TOP 被直接 continue 丢弃**——而 POP_TOP 是表达式语句终结符
    （`value_list.append(nodes)` 编译为 `<expr_instrs> + POP_TOP`），
    丢弃后累积指令与后续语句指令混合；
  - **STORE_SUBSCR / STORE_ATTR 不匹配 STORE_FAST 系列被堆积**进
    current_instrs；
  - 尾部语句被整体 reconstruct，退化为裸 `task_id` 表达式。
- 修复：`_generate_remaining_stmts` 中 POP_TOP 改为「先 flush
  current_instrs 重建为 Expr 语句再 continue」；新增
  STORE_SUBSCR / STORE_ATTR 分支，分别委托
  `region_ast_gen._build_subscript_assign` / `_build_attr_assign`
  重建 Assign 语句（镜像 `_build_statements_from_instructions` 的
  L23180/L23186 处理）。修复后 354 → 376 指令。

### 1.2 推导式赋值目标只认 STORE_FAST 系列，下标/属性赋值退化为裸 listcomp（376 vs 378，根因 2）

- 现象：`node_dict[node] = [_n[1] for _n in nx.edges(graph, node)]`
  （else 子句内下标赋值）反编译退化为裸 `Expr(listcomp)`，
  STORE_SUBSCR 丢失，重编译 co_code 差 2 字节（376 vs 378）。
- 根因：`try_generate_comprehension_assign` 的 store_instr 搜索
  （`instrs[wrapper_end:]` 窗口）只匹配 STORE_FAST/STORE_NAME/
  STORE_GLOBAL/STORE_DEREF，STORE_SUBSCR / STORE_ATTR 目标被跳过。
- 修复：store_instr 搜索扩展 STORE_SUBSCR / STORE_ATTR；
  - STORE_SUBSCR：从 `wrapper_end..store_idx` 窗口取最后 2 条
    LOAD 指令（容器 + 键）重建 Subscript 目标；
  - STORE_ATTR：取对象 LOAD 重建 Attribute 目标。
  修复后 **graph.pyc 31/31 全量通过（rate 1.0）**。

## 2. 改动

- `core/cfg/comprehension_generator.py`
  - `try_generate_comprehension_assign`：store_instr 搜索扩展
    STORE_SUBSCR / STORE_ATTR；两分支分别重建 Subscript / Attribute
    赋值目标（`wrapper_end..store_idx` 窗口取容器/键/对象 LOAD）；
  - `_generate_remaining_stmts`：POP_TOP 先 flush current_instrs 重建
    Expr 语句；新增 STORE_SUBSCR / STORE_ATTR 分支委托
    `_build_subscript_assign` / `_build_attr_assign` 重建 Assign。

## 3. 验证结果（全部实测，PYTHONHASHSEED=0）

| 步骤 | 命令/方式 | 结果 |
|---|---|---|
| a. 目标函数单测 | diff_instr.py（原始 vs 反编译 `_process_task_queue`） | 354 → 376 → 378，全部指令对齐 |
| b. 目标文件全函数 | pyc_batch_verify graph.pyc | **31/31（rate 1.0）** |
| c. 全量回归 | full_scan_r34.py 分片（402 pyc，串行重跑消除资源误报） | **ok=312 / partial=90 / failed=0；函数级 5446/5746**；与 round_33 基线（scan_after_fix2.json，全路径对比）**回归 0、改进 6**（graph partial→ok、api_base/setting_api/risk_calculation __init__/scheduler/quote_handler rate 上升） |
| c1. 并行误报说明 | 首轮 3 进程并行扫描出现 17 个 failed（a 片 10 个 IQCommon/util、b 片 7 个 IQEngine/core）+ c 片段错误，全部为**资源紧张**偶发；串行重跑（refill_failed_r34.py + 单进程 c 片）全部恢复，与基线 rate 逐文件一致，**无真实回归** |
| d. 补丁合规 | `scripts/check_patch_patterns.py` | **PASS** |
| d2. opcode 引用 | comprehension_generator.py 相对 r33 版本 +6 处（70→76） | 全部为修复所需指令名（STORE_SUBSCR/STORE_ATTR/POP_TOP 等），无危险模式；该文件不在 check_hardcoded_opcodes 默认扫描范围（同 r33 口径） |

## 4. 已知遗留（Round 35 候选）

按成功率升序 partial 列表（本轮验证为独立问题，非本轮修复辐射范围）：
- `IQCommon/util/datetime_func`（25/26）：`change_2str_of_time_2_datetime` 63 vs 38
- `IQCommon/api/order_api_trade`（23/24）：`order_market` 215 vs 215（指令数相同，需查差异点）
- `IQCommon/trade`（22/23）：`create_trade` 68 vs 44

## 5. 附件

- `test_engineer/diag_graph_try.py`：CFG 诊断脚本（dump 块/异常表/region 树）
- `test_engineer/diff_instr.py`：指令级对比脚本
- `repair_engineer/full_scan_r34.py` / `scan_after_fix2_r34.json`：全量回归明细
