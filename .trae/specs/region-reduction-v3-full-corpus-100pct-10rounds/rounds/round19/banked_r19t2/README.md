# R19-T2 镜像补丁存档（判决 FALSIFIED，未安装）

- 交付：`region_analyzer.py`（sha256 前 16 位见下）、`FIX_T19-1.md`（阶段读数与消融）。
  实时仓库 core 从未被该工程师写入；其镜像 core 已逐字节还原（640d33a77dcb71c2）。
- 判决：**不安装**。api_base 仍 27/28、strategy 仍 26/27（阶段 3 未达）；
  零回退（5 个电池读数与基线全同，15 个面板文件全部 SAME）。
- 该补丁**买到的关键读数**（下一手必须建立在此之上，勿重复实现同一 32895 行）：
  1. `_r16_boolop_cc_run_operand` 卡在**第 (2) 项**「每个前缀成员的尾跳转落同一块 T」：
     `cand=B@1008, prefix=[B@992,B@996]` 时 `_T` 取自 B@992（`POP_JUMP_IF_TRUE -> @1098`，
     and 链的**假**出口=下一 elif 臂），而 B@996（`-> @1040`，or 链的**真**出口=真臂体）与它不同
     ⇒ 对 `A and (B or cc)` 混合前缀该判据**结构性不可满足**；
     改 `prefix=[B@996]` 单成员即 True ⇒ or run 能建。第 (3) 项本身通过
     （`_r16_cc_operand_success_edge(B@1008)=B@1040`）。
  2. strategy 侧 `cand=B@536, prefix=[B@512,B@524]` 已 True（两条都 `-> @568`，成功边 `@568`），
     其阻塞点是 **W14-A 尾钳**从链式比较成员自身的 fallthrough 取 `_w14_last_ft=@552`，
     而不是取 cc 成功边 `@568`。
  3. 消融隔离出旧补丁的回归臂：**单独施加「强制 `merge = BoolOpRegion.merge_block`」**
     使 api_base 27/28 -> **25/29**（过度收集 `then=[1040,5924,…]`）；去掉它子区反而正确：
     `IfRegion e=996 cond=1008 merge=1782 then=[1040] else=[1098,1142,1200]`。
- 剩余两个卡点（下一票的靶心）：
  A. 父 `IfRegion e=992` 的 `then=[996,1024,1034,1036,1040]` 仍认领 `@1040`
     ⇒ 父子争抢同一块（违「每块唯一归属」），臂体在产物里渲染成 `pass`；
  B. `chain_start B@992 -> []`：走链时 `block_to_region[B@996]` 尚未成为 BoolOpRegion
     （兄弟 run 按偏移顺序发现，B@992 先于 B@996）⇒ 需要与发现顺序无关的 run 归段判据。
- 复核口径：本票的落点差一律用修好的 `unit_diff.py`（qualname + `landings` 列）复量：
  `api_base <module>.get_history_df -> hunks=0 landings=2`（@994 应 ->1098 产物 ->1254；
  @1006 应 ->1040 产物 ->1254）；`strategy <module>.Strategy.tick_worker_thread -> hunks=0 landings=4`
  （@522/@534 应 ->568 产物 ->820；@992/@1004 应 ->1038 产物 ->1286）。
