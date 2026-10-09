# Round 14 票单（诊断轮：三个新缺陷族定位到最小例，0 落地）

门侧：本轮 `gate_round.py 17 … --stage checks` 全绿读数（quotation 153/153、small34 1534/22、
判据自证 153/153 且变异「常量」1/153、「极性」1/153、pytest 2 failed/280 passed/2 xpassed
＝第 9 轮封表的两个基线红，零新增失败）。`core/` 与 `site-packages/` 工作树 0 行差异，
两个生产文件仍是基线字节 `region_analyzer 640d33a77dcb71c2`、`region_ast_generator 851b0723732a2402`。
语料仍是 **390/402 文件、6583/6617 单元（99.4862 %）**，残余 12 文件 / 34 单元（门 label 16 出表）。

## 一、本轮结论（按需求 → 状态 → 证据）

| 票 | 需求面 | 状态 | 证据 |
|---|---|---|---|
| R14-01 | `or` 链末操作数是链式比较 | 缺陷族成立，未落地；四处识别端阻塞点已逐个打开并定位到最后一处（父区域条件装配） | `DIAG_R1401_OR_CHAIN_CC_TAIL.md` §3-§9；电池 `repro/`（RED=9/9，只判 pycdc 产物） |
| R14-03 | `api_base.get_history_df`（27/28，该文件唯一失败单元） | 触发条件收到 5 行最小例；折叠支路实测无关，根指向识别端相序 | `DIAG_R1403_API_BASE_MERGE_AS_BODY.md` §1-§8；电池 `repro_ccneg/`（GREEN=1 对照 / RED=3） |
| R14 面板 | 分析端四臂对语料的影响 | **13/13 文件读数与基线逐文件相同 ⇒ 0 翻正 0 回归**，按「fires without flips」不落地 | R14-03 §4 表格（quotation/strategy/quote/trade_live_broker/api_base…） |

## 二、排除清单（下一票不要再走的路）

* 分析端 blocks 组装 `region_analyzer.py:28577`、`:28666`（两处都实测：blocks 变干净但父区域仍被打脏）。
* Phase 3 链式比较标志继承 `:20682`（实测：不再泄漏 cc 标志，但产物丢更多臂）。
* 生成端折叠三径 `region_ast_generator.py:21591-21717`（含单层 and 支路取反臂，实测逐字节无效果）。
* `sys.settrace` 行追踪（0 读数且改变产物）；进程内 harness 判决（产物与 CLI 差 ~350 B，只能读区域表）。
* 手写源当 `--source` 的判据（必然绿，见 R14-01 §1）。

## 三、下一票定向（同一条结构事实，两个方向）

负极性布尔 run 的判据必须比较：**「成员真值边 == 本区域 merge_block？」** 与
**「then 体 == 该成员的落空边？」**，且链式比较操作数的极性要按 **末段** 的跳转判定（头段末指令
只是 IF_FALSE->清理块）。

* R14-02：`or` 链 cc 尾 —— 从 `_identify_conditional_regions` 给父区域选定 `condition_block` 的支路入手
  （Phase 2 的链式比较区域抢走了布尔算子链成员，是本族共同根）。
* R14-04：`api_base.get_history_df` / `strategy.tick_worker_thread` 都等这条判据；
  两侧方向相反（api_base 需要取反，strategy 需要取消取反），单点实现、两处复用。
* 验收顺序不变：`repro/` 与 `repro_ccneg/` 两电池先绿 ⇒ 12 残余文件 + quotation 的 13 文件面板 A/B
  ⇒ 完整门链（下一 label 17 regen/verify/report 对 16）⇒ 提交并推送。
