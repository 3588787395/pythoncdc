# round70_diag1 — c1 [R70-diag1 循环分支会合·异常边后继豁免] 见证

消费者：`IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`
`on_order_response`（官方 445/444 → 445/445）、`on_trade_response`（392/391 → 392/392）。

- 复现：`python -m py_compile r70_exc_r57e.py`（或直接用同目录编译产物 `r70_exc_r57e.pyc`），
  再用 `pycdc.decompile_pyc` 反编译并对 `repro` 函数跑 `pyc_batch_verify.bytecode_diff`。
- landed（R69）读数：`1/2`（`repro` 93/92，hunk 4、true 55）。
- m70（R70）读数：`2/2`（`repro` 全对齐）。
- 判据三要素在 `core/cfg/region_analyzer.py` 的 `_r57e_in_loop_branch_convergence`
  落地段注释（[R70-diag1] 标记）。
