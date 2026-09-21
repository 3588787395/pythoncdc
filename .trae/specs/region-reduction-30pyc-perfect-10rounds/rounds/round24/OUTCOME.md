# Round 24 — OUTCOME

起点 HEAD `3b6143c4`（Round 23 已落地并 push）。本轮落地 **R24-A**：
链式比较 `IfRegion` 的入口块可作三元表达式的条件头（分析端单文件判据）。

## 1. 对外序列（本轮 `stats` 实测，唯一发布口径）

```
total_pyc 402 | verified 402 | ok 362 | partial 40 | failed 0
functions 5746 | matched 5634 | cumulative_match_rate 98.05%
```

上一轮序列 `5633 / 98.03%` ⇒ **本轮 +1 函数、+0.02pp**，来源是索引里唯一一条实质变更：
`IQData/plugins/plugin_system_realquote/real_quote.pyc  matched_functions 37 → 38`
（`bytecode_match_rate 84.09% → 86.36%`）。`batch --index pyc_index.json --all --round 24`
402/402、`failed_pyc 0`；其余 401 条只有 `last_tested_round 23 → 24` 推进。

两把内部尺（不外发、不参与相减）同向：严格 sweep 402/402
`Σn_ok 6004 → 6005`、`Σsad 1590 → 1588`、**0 文件变差、0 文件 n_ok 变少**。

## 2. 修的是什么（语义层，不只是指令层）

`can_be_ternary_header` 原本只要区域带 `chained_compare_blocks` 就一律拒绝作三元头，
而生成端 Phase-7-D 恰好支持「区域入口块 = 三元头」。被拒后三元赋值降级为 if/else 语句，
两条纯值臂的栈顶值被丢弃，**赋值语句整体消失**：HEAD 产物里

```
if symbols:
    if 0 < int(data_count) <= 200:
        int(data_count)
    else:
        200
```

`data_count` 从未被重绑（正确产物：`data_count = int(data_count) if … else 200`）。
所以这不是"字节对不齐"，是丢语句。

## 3. 门禁读数（全部在落地字节 `6df13cdaf815920c` 上复跑）

| 门禁 | 读数 |
|---|---|
| Round 24 电池 `test_repros/round24_cc_ternary/` | `G0/G1/G2/G3/G4 全 True → GATE: PASS`；`a01 1/3→3/3`、`a02 1/2→2/2`、锚点 `real_quote 37→38`、`.py` 形状 `13/24 → 16/24`、**fixed=2 broken=0** |
| Round 23 电池（pre-R24 核 vs landed） | `broken=0`、`fixed=0`、`Σ\|orig−decomp\| 12→12`、锚点 `realtime_event_source` 两核同为 `\|d\|=17 / textlen=21823`，残余两条逐字相同（`clock_worker orig=1276 decomp=1292`、`get_one_event 19→20`）（其 `GATE: FAIL` 只因 G0 要求"改善"，本轮语义是**不得改变**）|
| 靶子 `single real_quote.pyc` | `partial 38/44 86.36%`；`get_real_L2_data` 由 `359/359 + true_diffs 337` 变为完全匹配（已不在 mismatches 里）|
| `quotation.pyc` 零副作用 | `partial 142/143 99.30%`，唯一缺陷 `change_his_to_forward orig=547 decomp=548 jump=1 true=377` 与 Round 21/22/23 逐字相同；`quotationOK.py` **未被改写**（不在 `git status` 里）|
| 全量 402 官方臂 | `Σmatched 5633 → 5634`；**产物 sha256 变化 2/402**；**0 个当时已 ok 文件被改动**；0 错误 |
| 语料级严格 sweep | 402/402；按 `textlen` 判定产物变化同为 2/402（`real_quote` sad 10→9 且 n_ok 37→38、`quote` sad 224→223）|

变化的 2 个产物：`real_quote.pyc`（+1 函数匹配）、`fly/data/quote.pyc`
（`get_individual_data` 长度差 8→6，官方计数不变 67/81 —— 收窄但仍未匹配）。

## 4. 否证与反面结果（本轮不做的、做不成的）

* **线 A（多余跳转/块次序）候选否证**：全量触发面 better=2 / equal=8 / **worse=14**，
  且打坏 11 个当时已 ok 的文件 ⇒ 不落地。
* **patchA 否证**：判据放宽到 `chained_compare_blocks[-1]` 会过量发射；
  patchA3 与 patchA4 在 58 文件触发面上逐字节相同 ⇒ 取最小判据。
* **复现构造负结果**：从产物源码回推的 6 个 `.py` 形状在 HEAD 镜核下全部官方 2/2 matched
  （回推源码重编译后块布局不同）。换位族最小复现必须从**字节码布局**构造。
* **尺盲实例**：`t1/t3` 产物含明显死代码（`return self.BarData(...)` 后紧跟 `return None`）
  仍被判 2/2 matched ⇒ 「官方 ok」≠ 产物良构，`.py` 电池不可被官方臂替代。
* **本轮未收口的诊断线**：B（异常布局）、D（整块丢失 −21..−32）、E（clock_worker D2/D3）、
  F（`decrypt_database_url +29` / `log.setup −67` / `fly_api.base` 孪生 −21×2）、
  G（两个最接近翻转的 +1 对）—— 五路诊断代理都在 150 轮上限终止且未交 `ANALYSIS.md`，
  只有线 A/C 的结论被编排方从 on-disk 工件恢复。任务 #39/#41/#42/#43/#44 保留为 Round 25 入口。
* **环境事故（已记入用户记忆）**：本机 `PYTHONIOENCODING` 一旦被设置（任何值）就会让
  `python.exe` 以 exit 0、两条流零字节退出 —— 本轮有 4 个后台作业因此静默空跑。
  现改用 `python -X utf8`，并从子进程 `env` 里剔除该变量。

## 5. 移交 Round 25 的直接入口

1. **R24-A 的两半缺半**：三元头位于**函数首块**（`self.entry is cfg.entry_block`）时仍不放开，
   见证即本轮残余 `get_cache_l2_data` / `get_cache_l2_data_by_one`
   （`orig 337/321 → decomp 335/319`，`first_diff index 18 JUMP_FORWARD vs POP_TOP`）
   与电池 `b03_cc_ternary_at_head`（两核产物逐字节相同、都 FAIL）。
   这一半需要生成端配合，不是同一判据能单独完成的。
2. `for` 体内嵌套三元（电池 `c04`，两核相同）。
3. `quote.get_individual_data`：长度 312/306，还差 6 条 —— 与 1 同一形状家族。
4. `data_proxy.get_bar` 的纯换位（等长 86/86、true=8、jump=3）：本轮已给出块级对齐差，
   但线 A 的第一版候选被否证 ⇒ 需要更严的同层判据（同形尾块的唯一归属），不是跳转修补。
5. Round 23 移交项其余部分照旧（`check_before_trading 243/254`、`decrypt_database_url 295/324`、
   `quotation.change_his_to_forward 547/548`、`api_base.get_history_df 1742/1718`、
   `trade_info_utils` deficit 2、Round 22 电池残留 `r22_23…r22_27`）。

距「100% 成功率」还差 **112 个函数 / 40 个 partial 文件**（5746 − 5634）。
