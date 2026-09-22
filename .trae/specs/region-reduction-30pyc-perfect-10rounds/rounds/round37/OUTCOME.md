# Round 37 OUTCOME —— 落地 R37-A：or-extension 找「可借 elif 臂的链」时，把本区域入口块收在自己块集里的祖先链必须跳过

## 一、结论

* 本轮靶 **`IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc :: Strategy.tick_worker_thread`**
  （strict `268/247`、jump 32、true 113）：**一整段 21 条指令的区域 @718..820 不发射**，
  官方尺该文件 `23/24`。该形状自 Round 31 起两次交回（Round 32 线 B 的因果归因已被否证，只留下块级线索）。
* 根因在 `_if_generate_normal` 的 `[R23-A]` 段（`region_ast_generator.py:16956-16964`）：带 or-extension
  的区域要在**扁平的** `self.region_analyzer.regions` 整表里找一条「本区域 else 臂其实所属」的 elif 链，
  筛选条件只有两条——供体是带 `elif_conditions` 的 `IfRegion`，且其 `then_blocks` 里有与 `_r23_or_then`
  **偏移相等**的块。第一条缺少归属约束：**祖先链同样通过**，于是 `:16973-16977` 把祖先的
  `elif_conditions/elif_bodies/elif_final_else` 挂到子孙区域上发射。按原则 2 每块只有一个主人，
  子孙「替祖先发射」的直接后果是祖先侧与该臂相连的整段区域被跳过。
* **R37-A**（`arm-design.md` §五）：供体区域的块集若含本区域入口块，则它是祖先（或自身），不得借臂。
  判据只消费块同一性与区域块归属。补丁 1 处编辑、+3 行、243 字节。
* 一手因果证据（编排方在落地核的镜像副本上插桩，只读语料靶文件，`logs/g0_stamp_strategy.txt`）：
  `tick_worker_thread` 上该 `continue` 命中两次，两次都带 `would_have_been_accepted=True`，
  其中一行的 `cur_entry=718` 与线 A 独立报出的缺失区域入口相同，供体为 `entry=210 / 56 块` 的祖先链。
* 靶文件 **23/24 → 24/24**（整文件翻转）；`logs/g4prime37_readings.txt`：严格尺
  `25/27 σ-defect=2 Σ|Δ|=21` → `25/27 σ=2 Σ|Δ|=0`（`tick_worker_thread 268/268 delta=+0`，
  残余降为一条在册 `[target_diff]`）。顺带把同族的 `clock_worker` 从 `+16` 推进到 `+6`
  （`realtime_event_source.pyc` `Σ|Δ| 17 → 7`），该文件整文件仍 partial。
* 发货判据 **G4 全 402 逐文件 sha 优先 A/B**：`SAME=400 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0`，
  整文件全匹配 `374 → 375`。

## 二、门禁（严格按序 G0→G1→G2′→G3→G4→G4′→落地→G5→G6→G7，逐条实测见 `arm-design.md` §六）

| 门禁 | 判据 | 实测 |
|---|---|---|
| **G0** 合成见证（不依赖语料，32 片：`wit` 7 + `battery` 7 + `ladder` 10 + `ladder2` 8） | 见证须在改前字节 FAIL、候选下 CLEAN；控制两侧 CLEAN；无一片 Σ\|Δ\| 上升 | `+5→0`（`l2_nested_orarm`、`c4_loop_ancestor_single_arm`）、`+4→0`（`n6_orarm_else_sibling`、`n8_orarm_then_plain_arm`）；7 片控制两侧全 CLEAN；`logs/g0_all_arms.txt` |
| **G1** d1+d2 池 17 文件 | 靶翻转、其余不退 | `TALLY SAME=15 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0`，`files fully matched a=0 b=1` |
| **G2′** 上一轮合成电池 51 片 | 全 SAME | `TALLY SAME=51 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`（`a=40 b=40`） |
| **G3** 承重锚点 106 个 | 全 SAME | `TALLY SAME=106 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`（`a=76 b=76`） |
| **G4** 全 402（发货权威） | 0 REGRESSION、0 ERR | `TALLY SAME=400 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0` |
| **G4′** 变化产物逐文件 strict | Σ\|Δ\| 与缺陷函数数不升 | `strategy 21→0`、`realtime_event_source 17→7`，两者 clean 计数不变 |
| **G5** `single` 靶 + canary | 靶满格且在册产物 == 候选臂产物；canary 字节不变 | `24/24 rate=100.00%`，产物 13159 字节 `68c457315b02353f` 两侧全等；`quotation.pyc 143/143`，183261 字节 `3f2242e73d7fd56a0096` 与 Round 36 收尾值逐字节相同 |
| **G6** `batch --all --round 37` | 402 全复验＋索引回写＋逐字段 diff | 0 failed；实质变化只有 `strategy.pyc` 的三个字段（`23→24`、`partial→ok`、`rate→1.0`），其余 402 条仅 `last_tested_round 36→37` |
| **G7** `stats` | 原样一行 | 见 §四 |

## 三、落地与产物身份

* 落地前证明：`land37.py` 把同一个 `spec37a.json` 重放到工作区文件，断言内存重放字节与被测量的
  `mirr_r37a` **全等**才写盘——`replay == measured mirror bytes: OK (region_ast_generator.py, 2984567 bytes)`，
  写盘后 `2984324 -> 2984567 bytes, CRLF 48421, BOM=True, equals measured mirror=True`。
* 核身份：`bbfe1a414032436921ab`（改前）→ `6b0759b1a0a566a4eb8f`（改后），2984567 字节、48421 CRLF、BOM 保留。
* 产物侧 `git status` 只有两个 `M`：`strategyOK.py` 与 `realtime_event_sourceOK.py`，
  两者与候选臂产物各自字节全等（`68c457315b02353f` / `b1b282deba63cd16`）——即落地核复现了被测臂。
* 常驻电池增量：`test_repros/round37_ancestor_elif_or_arm/`（4 见证 + 4 控制，`.py` 入仓，
  `.pyc` 现地重编），在落地字节上 `cases=8 CLEAN=8 DEFECT=0`（`logs/g0_pinned_on_landed.txt`）。

## 四、G7 `stats` 原样

```
======================================================================
累计统计:
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                375
  partial_pyc:           27
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5650
  cumulative_match_rate: 98.33%
======================================================================
```

## 五、移交 Round 38

1. `matcher :: match 713/689`：R37-B 由代理自己的代价门否证（`Σ|Δ| 1779→2694`、
   `official matched 5649→5626`、`partial 28→41`、better 5 / worse 19；该表为代理私有目录读数，
   编排方未复测——NO-GO 不需要独立确认，基线 `5649/5746` 已与编排方自己的索引求和交叉核对为真）。
   可用线索：`core/cfg/region_analyzer.py:17290` `_collect_branch_blocks` 的停止集、等长换位见证、
   暴露面 21 函数/13 文件。**先解决排序，再谈判据。**
2. `tick_worker_thread` 的同族另一半：本轮 stamps 显示同一函数里 `cur_entry=612` 也命中过一次，
   而 `w2_outer_three_arms` 那片的「mangled or-arm」产物形状在候选下 14→14 未动——
   or 臂形状还有一次要取，入口块归属之外还差臂内容器的表示。
3. `clock_worker 1275/1281 +6`（本轮从 +16 推进 10 条，仍未收口）；
   `decrypt_database_url 295/324 +29`（过量发射，需放弃发射侧）；`events 510/508`（欠定）；
   `_init_config 86/84`（R16 J1 在册反例，受保护）；`OverNightOrder.__init__ 172/148 −24`（#41）；
   #61 汇合块残余 + `r29x_01 <module> 142/138`；等长换位 5 处（`fileio_utils::write`、`graph`、
   `logger`、`scheduler`×2）；`:2118` 附近读 `orelse` 的同族读者本轮未动。
4. 电池增量：G2′ 用 `reprobat51 + round37 的 8 片 = 59`，G3 的 106 个锚点须先对 Round 37 落地字节
   重读作基线（本轮 `a106_landed.jsonl` 已是该基线，但落地后必须重跑）。
5. **诊断代理耗尽轮次时，候选仍可从它的 scratch 脚本里恢复**：线 A 未交 ANALYSIS.md，
   但 `mkfix.py` 里有完整补丁文本；恢复后必须在**干净镜像臂**上重建并重测——它的 `mirr_fix`
   是插在已插桩镜像之上的，读数不可沿用。
