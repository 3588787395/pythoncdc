# round70_diag4 — c4 [R70-diag4 while-true 循环出口候选剔除] 见证（本轮旗舰）

消费者：`IQCommon/util/fileio_utils.pyc`
官方 12/14 → **14/14 100.00%**，mandated ruler（`scripts/pyc_verify.py`）15/15 = 100%，
严格尺 `FileIO.write` / `FileLock.acquire` 两条 seq_len 全消 —— **双尺全清旗舰**。

- 复现：编译 `r70diag4_witness.py` 为 pyc 后反编译，对 `wret` 跑 `bytecode_diff`。
  landed（R69）读数：`1/2`（wret 62/61）；m70（R70）读数：`2/2`。
- `r70diag4_wret.py` 为对照（两侧均 2/2，防假阳）。
- 判据三要素在 `core/cfg/region_analyzer.py` 的 `_find_loop_else` 出口候选剔除、
  R102 有界 DFS `block_to_region[_cur_jt].entry ∈ body_set` 守卫、`for_iter_exit`
  截断豁免三处落地段注释（[R70-diag4] 标记）。
