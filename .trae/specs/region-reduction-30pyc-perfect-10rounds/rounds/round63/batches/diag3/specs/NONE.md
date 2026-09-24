# Round 63 batch 3 —— 本批无已证明的 spec

基线复核 = FACTS.md（dump/landed.jsonl，5 支全跑）。全部精力投给最接近全清的
matcher.pyc/match（-26 条过滤后指令），机制已定位，但没有一条候选在自己见证上动过，
按红线一律不提交。

## 已证伪假设
1. `cand_r63_claim.json`（保留此文件仅作记录，**不落地**）：`_process_if_blocks` 子区域
   归约产物为空时不登记 `generated_blocks` / `_generated_regions`，寄望同层 BoolOpRegion
   兄弟节点接管发射。实测 matcher `match` 逐函数元组 `713/689/jd9/td524` **零变化**；
   再在 c1 臂上探针确认 `_generate_boolop` 对该批块从未被调用（BoolOpRegion 不在该
   else 单元的 nested 分派集合内）。⇒ 解除登记不是生效机制。
2. 合成复现 `test_repros/round63_b3/r63b3_chained_value_ctx_prefix.py`：落地臂 2/2 matched，
   未复现丢失。⇒ 形态缺成分，不能当见证。
3. 「缺的是 `_try_build_method_call_chained_compare` 左切片吞前导语句」单独作为修复点：
   切片 `cond_instrs[:left_start]`（1696..1784）确实吃掉了两条已完结赋值，但该区域的
   `_generate_ternary` 整体返回 EMPTY，所以即便收窄切片也不会让语句出现——它只是同一
   错误划界的次要表现，非主因。

## 下一步判据方向（R64）
主因单点 = `_generate_ternary` 对「值语境链式比较」区域（merge_context='store'、
value_target 非空、chained_compare_ops>=2）返回空。CPython 3.11 的
JUMP_IF_FALSE_OR_POP 在此是链式比较的内部短路，不是三元分支，归约目标应是
`Assign(value_target, Compare(a, [<=,<=], [b, c]))`（无三元外壳），同块前导语句用既有
纯栈深判据 `_split_block_condition_prefix`（region_ast_generator.py L336）切出后经
`pre_stmts` 交父序列发射——接线范式即同函数 L34401-34407 的
`_build_ternary_boolop_condition(region, pre_stmts)`。先用 settrace/分段日志定位该区域
在 `_generate_ternary` 里究竟走到哪个 bail 分支（34425 之后窗口内无 return None）。

## 未动靶（本批时间不足，实测数据见 dump/landed.jsonl）
- realtime_event_source/clock_worker (+11，多余发射型，需查重复归属)
- graph/_process_task_queue、graph/_get_influence_task、fileio_utils/acquire、
  fileio_utils/write、fly-logger/logging_process、fly-logger/write_logging_thread
