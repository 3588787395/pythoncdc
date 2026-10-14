# MEASURED R19-2 —— 落点列失明已修复 + 残余单元按「距离」重排（本轮施工名册）

## 1. 测量工具缺陷（实测证明，已修 `unit_diff.py`）

判据本体不在仓库里：`scripts/pyc_verify.py` 只是装载/配对/报告，逐条判定由
`D:/Desktop/ptrade相关/pylingual/pylingual/equivalence_check.py::compare_pyc` 执行，其顺序是
**先 `is_control_flow_equivalent(CFG_a, CFG_b)`，再 `compare_bytecode`**，并先套
`remove_extended_arg / remove_nop / fix_indirect_jump / fix_unreachable / replace_firstlno`
（该函数 docstring 自述 "will always patch out unreachable code"）。

⇒ 判据是**控制流图等价**，不是指令文本比较。而 `unit_diff.py` 的 `dump()` 把跳转操作数清空
（内容列本意如此），主函数**从未实现过它 docstring 承诺的落点列**：纯落点残差被读成
`hunks=0 / delta=0`，与判据的 failure 直接矛盾。

实测对照（同一 landed 字节、同一就地产物）：

| 单元 | 修复前读数 | 修复后读数 | 判据 |
|---|---|---|---|
| `api_base.<module>.get_history_df` | `len 1881/1881 delta=0 hunks=0` | `hunks=0 landings=2` | failure |
| `strategy.<module>.Strategy.tick_worker_thread` | `hunks=0 delta=0` | `hunks=0 landings=4` | failure |
| `trade_live_broker…._process_tick_order` | `hunks=0 delta=0` | `hunks=0 landings=1` | failure |

修复两处（均为工具侧，未碰 core）：
1. 新增 `dump_raw()`：按 `dump()` 同一 DROP 过滤给出 `(offset, opname, 目标)`，在 `equal` 段上逐槽比较，
   产出真正的落点列，汇总行改为 `hunks=H landings=L judge_diff=bool(H or L)`。
2. 目标先按「本码对象过滤后指令流的**索引**」表达，再**经 SequenceMatcher 匹配块把 orig 目标映射到
   prod 侧**后才判等：只按偏移或只按索引比较都会被「前部一处内容差 ⇒ 后续全部 2 字节位移」造假
   （实测造假量级：`handlers._target` 127 条、`klinedata` 76 条、`quote.check_frequency` 24 条，
   而真差各为 1~3 处）。映射后上表数字落回真实尺度。
3. `pick()` 另接判据的**点号 qualname**（`<module>.TradeLiveBroker._process_order`），
   裸名匹配到多个码对象时打印 `AMBIG_NAMES=…` 而不是默默取最长者。
   （未给 qualname 时 `strategy.tick_worker_thread` 这类**类方法**根本取不到，先前若干读数因此失真。）

绿控验证（同工具必须读 0/0，否则该列不可信）：
`base_api.pyc::<module>` ⇒ `hunks=0 landings=0 judge_diff=False`；
`matcher.pyc::<module>` ⇒ `hunks=0 landings=0 judge_diff=False`。

## 2. 残余 31 个可测单元按距离排序（完整表 `D:/Temp/r150/residual_ranked_fixed.txt`）

封盘名册 33 个失败单元中，`wizard_quant_api.get_DMI.calculate_di.<genexpr>` ×2 为
`COPY_AMBIG`（同路径副本不唯一，判据拒判）不入本表 ⇒ 31 个可测。
`sum_hunks=71 sum_landings=69`；**纯落点单元 6 个**。

| hunks | landings | \|d\| | 文件 | 单元 | 备注 |
|---|---|---|---|---|---|
| 0 | 1 | 0 | trade_live_broker | `_process_tick_order` / `rzrq_credit_order` / `get_ipo_stocks` | 三条各只差 1 处落点；同文件内还有 7 个其它失败单元 ⇒ 不产生整文件翻绿 |
| 0 | 2 | 0 | trade_info_utils | `kill_trade_process` | 纯落点 |
| 0 | 2 | 0 | api_base | `get_history_df` | 该文件唯一失败单元 ⇒ **翻绿即整文件**；T19-1 轴（r19t2 已给精确卡点，见 §3） |
| 0 | 4 | 0 | strategy | `tick_worker_thread` | 同上，与 api_base 同判据 |
| 1 | 0 | 10 | quote | `build_current_period_df` | 单 hunk 缺 10 条（函数尾被吞） |
| 2 | 0 | 1 | trade_info_utils | `query_strategy_id` | 已逐读：内联 `LOAD_CONST None/RETURN_VALUE` 顶掉 `JUMP_FORWARD→共用尾` |
| 1 | 1~3 | 1~2 | real_quote / quote / wizard / klinedata / handlers | `get_tick_direction`、`get_individual_data`、`filter_desicion`、`get_kline_by_count_new`、`_target` | 小形，1 hunk 级 |
| 1 | 2 | 0 | klinedata | `get_kline_by_count_new` | 与 §3 T20-1 同一单元（1 内容 hunk + 2 处位移影子） |
| 3 | 1 | 0 | trade_info_utils | `query_trade_strategy_info` | 净 0 但 3 hunk |
| 3~10 | 0~18 | 3~465 | trade_live_broker ×5、`__init__`(risk) ×2、quote ×3、realtime_event_source ×1 | `_process_order`(−465) / `_process_cancel_order`(−293) / `clock_worker`(−113) 等 | 大缺失族 |

## 3. 结论与优先级（写给下一手，不改判据口径）

1. **翻绿性价比**：`api_base`（0/2）与 `strategy`（0/4）只差落点、且各自是所在文件的唯一失败单元
   ⇒ 一条判据两整文件；`klinedata`（1 hunk + 2 落点，同为唯一失败单元）是第三档 ⇒ 本表前三档合计
   **3 个整文件 / 7 个单元**。
2. 本轮 r19t2 工程师已把 api_base/strategy 的**精确卡点**测出（其 `FIX_T19-1.md`）：
   子区域在去掉「强制 `merge = BoolOpRegion.merge_block`」这一回归臂后已正确
   （`IfRegion e=996 cond=1008 merge=1782 then=[1040] else=[1098,1142,1200]`），
   仍红的两个原因是 ①父 `IfRegion e=992` 的 `then=[996,1024,1034,1036,1040]` 与子区争抢 `@1040`，
   ②`chain_start B@992 -> []`——走链时 `block_to_region[B@996]` 尚未成为 BoolOpRegion
   （兄弟 run 按偏移顺序发现，B@992 先于 B@996）。下一条票必须针对这两点，而非再动 `@994/@1006` 的取反。
3. 残余表里的 `TARGET_ONLY` 类读数（此前用 `hunk_meas.py`）与本表口径不冲突，但**任何后续读数一律用
   修好的 `unit_diff.py` 并写 qualname**；`hunks`/`landings` 两列分开报，不得合并成「差 N 条」。
