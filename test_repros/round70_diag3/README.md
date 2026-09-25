# round70_diag3 — c3 [R70-diag3 裸 return None 孤儿块归并豁免] 见证

消费者：`IQCommon/util/trade_info_utils.pyc::trade_operation`
官方 39/40 → **40/40**（严格尺同函数 seq_len 304→302 消失、既有 target_diff #94 露出，
缺陷总数不变）。

- 复现：编译 `r70_witness_25b.py` 为 pyc 后反编译，对 `trade_operation_witness` 跑
  `bytecode_diff`。该见证为**部分咬合**：landed（R69）105/103 → m70（R70）104/102
  （方向性改善，未全清；全清证据在真实 pyc 上：官方尺 40/40）。
- 非靶支核查：klinedata 43/45、real_quote 40/44 守卫 0 命中、读数逐项不变。
- 判据三要素在 `core/cfg/region_analyzer.py` 的 `_25b_then_arm_orphan_return_none`
  方法 docstring（[R70-diag3] 标记）。
