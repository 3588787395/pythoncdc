# Round 38 设计稿 —— 目标池、形状聚类、两条诊断线的否证，以及本轮为何 `core/` 零改动

靶轮字节：commit `7b8af974`（Round 37 落地 R37-A），核
`core/cfg/region_ast_generator.py` sha256[:20] `6b0759b1a0a566a4eb8f`、2 984 567 字节、
CRLF 48 421、UTF-8 BOM 在位、HEAD blob 与工作区逐字节相同、`git status --porcelain -- core` 空。
所有测量都在该字节的**私有镜像**（`logs/r38m.py mirror` 建的 `mirr_head`，建后立即断言与
工作区字节全等）上做，工作区核自始至终未写一个字节。

## 一、目标池（实测，非沿用）

`logs/pool38.py` 读 Round 37 G6 回写的 `pyc_index.json`，先断言索引确由 37 轮盖章
（402 条全为 `last_tested_round == 37`）、核 sha 未移动、`core/` 干净，再出池：

```
baseline(landed round37 index, HEAD 7b8af974, core sha 6b0759b1a0a566a4eb8f): files 402 partial 27 sum_deficit 96 deficit1 5 deficit2 11
```

deficit-1 池（`logs/g1_d1_5.txt`）：`IQCommon/manager/instance.pyc 31/32`、
`IQCommon/util/replace_utils.pyc 8/9`、`default_event_source.pyc 13/14`、
`realtime_event_source.pyc 11/12`、`matcher.pyc 16/17`。
逐文件在 `head` 臂上复测（`logs/g1head_d1_5.jsonl`、`logs/g1head_d2_11.jsonl`）与索引一致。

## 二、先排除机械故障：全 402 崩溃探针（带阳性对照）

Round 36 证明过一次「整块缺失」其实是 per-region 兜底吞掉的 `TypeError`。本轮把那条探针
（`logs/crashscan38.py`，钩 `_generate_region` 的被吞异常与 `_generate_degraded_statements`
的降级入口）推到**全 402**，3 片各自 134 文件、0 error、33/32/54 秒：
每一行的崩溃列都是 `-`。

探针本身先被阳性对照校验过（反向 R36-A 镜像 `mirr_rev36a`，spec 见 `logs/spec_rev36a.json`）：
`fly_api/base.pyc` 复现 `2x TypeError @ region_ast_generator.py:4824 in _fold_break_to_return`
——「什么都不报的探针是坏探针，不是空探针」。

结论：语料里已无机械故障，96 个 deficit 函数全部是**判据级**形状。

## 三、形状聚类：按对齐后的指令签名分桶

`logs/sigscan38.py` 对 27 个 partial 文件的 94 个不匹配函数（`logs/pooltab38.py` 出全表）
做过滤后指令序列的 difflib 对齐，签名 =（操作码序列、删除的操作码、插入的操作码）：
**81 个签名组覆盖 94 个函数，0 个因同名多义而未决**。最大的一簇是 8 个函数各差**一条**
`JUMP_BACKWARD`：

```
[8] hunks=(('delete', 1, 0),)  deleted=['JUMP']  inserted=[]
  klinedata::get_all_real_daily_kline 188/187   wizard_quant_api::wizard_quant_check_limit 91/90
  IQCommon/util/common_func::fill_kline_data 60/59   …::fill_kline_data_by_pre 82/81
  real_quote::one_prod_to_dataframe 432/431   IQData/utils/common_func::fill_kline_data_by_pre 82/81
  quote::is_delisting_stock_real 107/106   quote::one_prod_to_dataframe 484/483
```

## 四、窗口探针否证「一簇一形状」：8 行其实是两种形状

`logs/dupjump38.py` 把 8 行各自的 ±4 指令窗口打出来，按「前一条指令是否同 token」和
「被删跳转与保留跳转是否同落点」分解：

* **子形状 A（2 行）**：前一条指令同、两条 `JUMP_BACKWARD` 同落点 ⇒ 原本连着发两条
  相同的回边，产物只发一条，第二条被并掉。
  `wizard_quant_check_limit` `@336 STORE_SUBSCR / @340 JUMP_BACKWARD→92（保留）/
  @342 JUMP_BACKWARD→92（<<删除）/ @344 PUSH_EXC_INFO`；`get_all_real_daily_kline` 同形。
  产物侧形状是 `if …: 赋值; continue / elif …: 赋值` 之后**在链外**再补一个 `continue`。
* **子形状 B（6 行）**：前一条指令不同、落点也不同 ⇒ 臂尾回边被并掉后，**else 臂被摊平成
  顺序语句**。产物因此语义错：`logs/build_landed 摘录`（`IQCommon/util/common_funcOK.py:200-207`）
  里 `if name == 'amount' or name == 'balance': nan_data[…]=0` 之后无条件执行
  `nan_data[…] = result_data[…][name]`，把 0 又覆盖掉；原码应是 `else` 臂。

因此这一簇**不能**按一条判据处理，本轮拆成两条诊断线。

## 五、两条诊断线：均 NOT-READY，且编排方复核否证了线 B 的可实施性

* **线 A（子形状 B，6 行，`logs/diagA_subshapeB_analysis.md`）**：交付结论是自己那步
  「把臂尾跳转从块名袋里剥出来」的判据**够不到** —— 区域构造期没有「臂尾 vs 其他出口」的概念，
  需要一个发射器/区域树的新 API，且它点名的检查站点在实测中未到达。
  它给出的下一步实验（打印该函数 `if` 区域的 `then_blocks/else_blocks/merge`）未做。
* **线 B（子形状 A，2 行，`logs/diagB_subshapeA_analysis.md`）**：报告把根因归到
  `ast_from_stmt` 的硬编码 elif 脱糖，并给出一个「`orelse_if` 非空即忠实体」的开关判据，
  点名 5 个构造站点。编排方复核：`grep -n "def ast_from_stmt\|orelse_if" core/cfg/region_ast_generator.py`
  ⇒ **0 命中**，该函数与该形参名在核内都不存在；核内的 elif 结构体在
  `:15901 / :16012 / :12427 / :32627` 一带以 `_is_elif` 标记拼装，与报告的行号/符号体系不对应。
  ⇒ 判据**无法按报告实施**，本轮不采纳。

两条线各留下了一件有用的东西：线 B 的合成控制
`logs/r38_elif_continue_controls.py`（`ctl_plain_elif` / `ctl_single_cont` / `ctl_two_cont` /
`ctl_elif_more_body`）里 **`ctl_two_cont` 在落地字节上确证 FAIL**——编排方用
`logs/g0_38.py` 在 `mirr_head` 上实跑：`synctl DEFECT 1 1 ctl_two_cont:seq_-1`，
其余三支 CLEAN。也就是说「链外补的 `continue` 少发一条回边」这一形状**有不依赖语料的见证**，
下一轮的 G0 可以直接从这里开工（G0 驱动器本身也顺手做了冒烟校验，确认镜像断言、
显式 `cfile`、异常钩子三条都工作）。

## 六、编排方独立第三条线：8 行「发射器多付一条跳转」的布局等价行

`logs/fallback38.py` → `logs/fallback38.txt`，逐 hunk 打对齐窗口，分三组：

1. **extra-jump（3 行）**：`_all_bars_of_cache 230/231`、`trade_logs_control 193/194`、
   `check_stock 88/89` —— 产物在原码直落的位置多插一条 `JUMP_FORWARD`（落点 498/420/346）。
2. **klinedata-return（2 行）**：`get_history_new 322/323`、`get_multiminute_his_data 481/482`
   —— 原码是「返回值语句 + 跳到共享清理尾巴」，产物把 `return` 就地发射、尾巴另处再发射一份。
3. **等长换位（5 行）**：`_process_task_queue`、`fileio_utils::write`、`get_checked_time`、
   `write_logging_thread`、`after_trading_cancel_order` —— 长度相同而 `finally` 尾声被搬到
   链尾之后（严格尺记 `seq_diff`，落在 `<JUMP>` 槽上）。

注意分组名里的「等价」只指**控制流语义**：这 8 行在官方尺上仍以 `seq_len`/`seq_diff`
记为不匹配，是本轮真实缺口的一部分，不是尺子噪声。它们不是本轮的靶，因为修它们的判据
会直接踩到 Round 33/Round 35 刚落地的两条规则（被持有的 return 值穿副作用块、重复清理尾声
的非终末副本），需要单独设计见证。

## 七、为何本轮零改动、门禁跑到哪

按「一条同层判据」的规矩，本轮没有一条候选判据能同时满足：
（i）站点被实测到达；（ii）判据只消费结构事实；（iii）有不依赖语料的见证在改前字节 FAIL。
线 B 连符号体系都对不上，线 A 自证判据够不到，第三条线要动已落地规则。
⇒ 本轮 `core/` 零改动、不发货，G1–G7 无对象可跑（G1 的池读数与镜像一致性已作为
字节不变性证据提前完成）。

不发货的证明**不是自报**：`logs/index_vs_head38.py` 把 `head` 臂上全 402 的复测
（`logs/g4_head.all.jsonl`，402 行、0 harness error）与 `pyc_index.json` 逐文件逐字段比对，
**冲突 0**，两侧同为 `Σtotal 5746 / Σmatched 5650 / 整文件全匹配 375`。
即：索引在落地字节上仍然是实测值，本轮没有让任何东西悄悄漂走。

## 八、Round 39 台账（按「便宜且已定位」排序）

1. **子形状 A / `ctl_two_cont` 见证已就绪**：先用线 A 未做的那步实验（打 `if` 区域的
   `then_blocks/else_blocks/merge` 与臂尾跳转），在**核内真实符号体系**里找站点；
   线 B 的 elif 假说需要重新验证而不是照抄。
2. **子形状 B（6 行，产物语义错）**：`fill_kline_data` 一族，臂尾回边被并掉 ⇒ else 臂摊平。
   线 A 认为需要发射侧新 API，先量「发射器是否本来就有臂尾表示」再定层。
3. 8 行布局等价行（本稿 §六 三组）。
4. 未动过的同簇兄弟：`matcher :: match 713/689`（机制 `region_analyzer.py:17290`，
   暴露面 21 函数/13 文件，R37-B 已 NO-GO）。
5. `clock_worker +6`、`decrypt_database_url 295/324 +29`、`events 510/508`
   （字节码欠定，勿再从 else 归属进攻）、`_init_config 86/84`（受 R16 J1 反例保护）、
   `OverNightOrder.__init__ 172/148 −24`、#61 ＋ `r29x_01 <module> 142/138`。
6. `:2118` 一带未读的 `orelse` 消费方（Round 36 记为在册残余）。
7. 门禁基线：G2′ 用 `logs/reprobat59.txt`（落地臂 `logs/g2p_head59.jsonl`：59 条 / 48 全匹配 /
   Σ|Δ| 176）；G3 用 `logs/anchors107.txt`（`logs/g3_head107.jsonl`：107 条 / 77 / Σ|Δ| 446）；
   G4 的「改前」侧直接就是 `logs/g4_head.all.jsonl`。
