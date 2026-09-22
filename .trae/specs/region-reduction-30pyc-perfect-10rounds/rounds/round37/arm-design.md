# Round 37 · arm-design

改前基线：HEAD `d1052a6c`，`core/cfg/region_ast_generator.py` sha256[:20] `bbfe1a414032436921ab`
（2984324 字节、统一 CRLF 48418 行、UTF-8 BOM）。本轮全部「改前」读数对该字节成立；镜像臂
`mirr_head` 由 `r37c.py build` 断言与工作区文件**字节全等**后才使用（`logs/r37c.py`）。

## 一、目标池（实测，`logs/pool37.txt`）

`pool37.py` 对 landed 重读全索引：**files 402 partial 28 sum_deficit 97 deficit1 6 deficit2 11**。
partial 由 Round 36 开池的 29 降为 28，只因 R36-A 使 `fly_api/base.pyc` 翻转为 ok（该条目已不在
`pool37.txt` 的 partial 名单里）；`logs/summ37.py` 打印的 d2 表里仍出现的 `base.pyc 39/41` 是
Round 36 的**改前**在册记录，不是本轮读数。

六个 deficit-1 文件的唯一 unmatched 函数（`logs/g1_d17_table.txt`，官方尺 `orig/decomp j t`）：

| 文件 | 唯一 unmatched 函数 | orig/decomp | jump | true | 在册归因 |
|---|---|---|---|---|---|
| `IQCommon/manager/instance.pyc` | `_init_config` | 86/84 | 1 | 37 | 共享 `return None` 尾声内联，R16 J1 在册反例（受保护勿再取） |
| `IQCommon/util/replace_utils.pyc` | `decrypt_database_url` | 295/324 | 1 | 250 | 已生成区域体二次走查（过量发射，需放弃发射侧） |
| `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | `tick_worker_thread` | 268/247 | 32 | 113 | **本轮靶子**（Round 31/32 两次交回，见 §四线 A） |
| `.../default_event_source.pyc` | `events` | 510/508 | 2 | 157 | R30 残余：15 条错位＋两跳转槽 |
| `.../realtime_event_source.pyc` | `clock_worker` | 1275/1291 | 15 | 480 | R22/R23 在册残余 D2＋D3 |
| `IQEngine/plugins/plugin_system_matcher/matcher.pyc` | `match` | 713/689 | 9 | 524 | 281 指令区域被推迟到函数尾并旋转（线 B） |

电池本轮扩到 **合成 51 片 / 锚点 106 个**（`logs/lists37.py`）：合成侧 = Round 36 的 44 片 +
R36-A 的 7 片（`test_repros/round36_for_loop_dropped/`）；锚点侧 = Round 36 的 105 个 +
`strategy.pyc` 所在批次的 `plugin_fly_data/fly_api/base.pyc`（R36-A 靶子，本轮已全匹配，转为承重锚）。
两条改前基线：`logs/b51_landed.jsonl`（51 行）、`logs/a106_landed.jsonl`（106 行）均 0 error。

## 二、Round 36 移交项 ④ 的答案：机械故障假设对全部 28 个残缺点已排除

移交项要求把「区域生成期被吞掉的异常」探针制度化。`logs/crashscan37.py` 钩住
`RegionASTGenerator._generate_region`（异常被 per-region 回退吞掉）与 `_generate_degraded_statements`
（区域降级入口），按 3 分片跑完 **全 402 个语料文件**（`logs/scan37_all402.txt` + 三个分片日志）：

- landed 字节：**0 fatal、0 swallowed、0 degradation**。
- 正对照（`--core=mirr_pre36`，即 R36-A 之前的字节）在同一探针下报出
  `2x TypeError @ region_ast_generator.py:4824` + `2x degradation-arm-entered`（`logs/ctl_head.txt`）。
  对照跑在**镜像**上，不碰工作区（`logs/crash37_ctl.py`）。

探针报不出东西不等于没有东西，所以对照是这一节成立的前提。结论：剩余 28 个 partial 文件的缺陷
全部在**判断侧**（归属/发射决策），不存在「异常吞掉一整块」的机械因；R36 那一族是首例也是孤例。
本轮靶子 `tick_worker_thread` 在探针下同样 0 异常，因此它的 −21 只能靠结构判据取回。

## 三、目标选择

| 候选 | 池内形状 | 一次判据的成本 | 结论 |
| --- | --- | --- | --- |
| `strategy :: tick_worker_thread` 268/247 | 缺失一段 21 条指令的区域 @718..820，同时首合取支被「借走」 | 可合成最小重现（无池外依赖） | **选为本轮靶，发货 R37-A** |
| `matcher :: match` 713/689 | 281 删 + 259 插的等长换位，另丢一条 `STORE_FAST` | 需先拆排序，暴露面 21 函数/13 文件 | 线 B 诊断，代价门 NO-GO |
| 其余四个 deficit-1 | 三条在册受保护残余 + 一条过量发射 | — | 不动 |

## 四、两条诊断线（代理在各自私有目录做只诊断，编排方在自己的镜像根独立复测）

* **线 A（发货）**：`strategy.pyc :: tick_worker_thread`。代理 `D:/Temp/r37diagA` 在 150 轮上限处
  终止且**未交 ANALYSIS.md**；它的候选补丁文本保存在 `logs/diagA_mkfix.py` 里。它的读数不可直接沿用：
  其 `mirr_fix` 臂是在**已插桩的** `mirr_probe` 之上再打补丁（`mkfix.py` 的输入不是 landed 字节），
  所以 `logs/diagA_landed_strategy.json` 与 `logs/diagA_fix_strategy.json` 只用作**方向**证据
  （后者 `official_gen "24/24"`、`mismatches: []`）。编排方从 `mkfix.py` 取出补丁文本，
  用 `r37c.py build --spec=spec37a.json --dst=r37a` 从 landed 字节重建干净臂，§六 的每一个读数都是
  编排方在干净臂上重跑的。代理的块级证据（`logs/diagA_dump_orig.txt`：66 块/20 区域，缺失区域
  `@718..820` = B23..B32，B23 的前驱集 {19,21}，它是 B18 @642 的兄弟）被本轮 §五 的 stamps 独立证实。
* **线 B（NO-GO）**：`matcher.pyc :: match`。代理 `D:/Temp/r37diagB/ANALYSIS.md`（已归档）给出机制
  （`core/cfg/region_analyzer.py:17290` `_collect_branch_blocks` 遇停止集即停）与候选 R37-B，
  并**由它自己的代价门否证**：`Σ|Δ| 1779 → 2694`、`official matched 5649/5746 → 5626/5746`、
  `partial 28 → 41`、变化文件 better 5 / worse 19。**该表是代理私有目录的读数，编排方未复测**——
  理由是 NO-GO 不需要独立确认，只有发货需要；但它的**基线**经编排方交叉核对为真：它用的
  `5649/5746` 与编排方从 `git show HEAD:pyc_index.json` 求得的 Σmatched/Σfc 完全相同。
  机制线索与等长换位见证留在账上（§八），候选不取。

## 五、根因链与本轮落地的那一条同层判据（R37-A）

`_if_generate_normal` 处理带 or-extension 的区域时（`[R23-A]` 段，`:16947-16964`），要先为
「本区域的 else 臂其实属于某条 elif 链」找到那条链：它在**扁平的** `self.region_analyzer.regions`
整表里找第一个满足两条性质供体——① `isinstance(r, IfRegion)` 且有 `elif_conditions` 与 `then_blocks`；
② 其 `then_blocks` 里存在与 `_r23_or_then` **偏移相等**的块。找到后 `:16965-16977` 直接把供体的
`elif_conditions/elif_bodies/elif_final_else` 挂到**本区域**上并 `_if_generate_elif_chain(region)`。

缺陷就在性质 ① 缺少归属约束：`regions` 表里同时装着**祖先区域**。若本区域的入口块本身是某个祖先
elif 链区域的成员块，祖先照样通过筛选，于是祖先的 elif 臂被挂到子孙区域上发射——那些臂块在归约里
只有一个主人（原则 2），子孙区域「替祖先发射」的结果是祖先侧与该臂相连的整段区域被跳过，
`tick_worker_thread` 丢的就是 @718..820 那 21 条指令。

**R37-A（同层，只读结构事实）**：一个 `IfRegion` 若把**本区域的入口块**收在自己的块集里，
它就不是可借臂的旁系链，而是本区域的祖先（或自身），必须跳过。

```python
             for r in self.region_analyzer.regions:
                 if isinstance(r, IfRegion) and r.elif_conditions and r.then_blocks:
+                    _r37_rb = set(getattr(r, 'blocks', None) or [])
+                    if region.entry is not None and region.entry in _r37_rb:
+                        continue        # [R37-A] an ancestor chain may not lend its elif arms
                     if any(b.start_offset == _r23_or_then.start_offset for b in r.then_blocks):
```

判据只消费块同一性与区域块归属，不读名字、常量、绝对偏移、指令计数，也不读遍历次序。补丁共 1 处
编辑、+3 行；锚点在文件中唯一（`r37c.py build` 断言）。

**编排方一手因果证据**（`logs/stamp37.py` → `logs/g0_stamp_strategy.txt`）：在 `mirr_r37a` 的副本
`mirr_stamp37` 的**新 `continue` 站点**插桩，只跑语料靶文件。落地核在 `tick_worker_thread` 上打出
两行，且两行都带 `would_have_been_accepted=True`（即改前的偏移测试会接受该供体）：

```
[STAMP37] REJECT donor entry=210 donor_blocks=56 cur_entry=612 would_have_been_accepted=True
[STAMP37] REJECT donor entry=210 donor_blocks=56 cur_entry=718 would_have_been_accepted=True
```

`cur_entry=718` 正是线 A 独立报出的缺失区域入口；`entry=210 / 56 块` 是那条被借臂的祖先链。
两处拒绝的**联合**效果才是本轮 268/247 → 268/268 的读数，不单独归因给其中一处。

## 六、门禁（严格串行，读数逐条归档）

| 门 | 判据 | 实测 |
|---|---|---|
| **G0** 合成见证（不依赖语料） | 见证在改前字节 FAIL、在候选臂下 CLEAN；控制两侧都 CLEAN；任一片 Σ\|Δ\| 不升 | `logs/g0_all_arms.txt` 32 片：`ladder/l2_nested_orarm` +5→0、`ladder2/n6_orarm_else_sibling` +4→0、`ladder2/n8_orarm_then_plain_arm` +4→0、`wit/c4_loop_ancestor_single_arm` +5→0；7 片控制（`l0b`、`l1`、`m1`、`m2`、`m3`、`m3_two_or_arms_simple`、`n7`）两侧都 CLEAN；**没有一片 Σ\|Δ\| 上升**；异常探针逐片 0 swallowed/0 degraded。`wit` 批在清掉一次驱动脚本的陈旧片名后重跑（`logs/g0_wit2_landed.txt` / `g0_wit2_r37a.txt`：7 片，改前 CLEAN=0 DEFECT=7 → 候选 CLEAN=1 DEFECT=6） |
| **G1** deficit-1 + deficit-2 池（17 文件） | 靶子翻转，其余不退 | `TALLY SAME=15 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0`，`files fully matched: a=0 b=1`；IMPROVED = `strategy.pyc 23/24 → 24/24`；MOVED = `clock_worker [1275,1291,15,480] → [1275,1281,10,478]`（`logs/g1_landed_d17.jsonl` / `g1_r37a_d17.jsonl` / `g1_d17_table.txt`） |
| **G2′** 上一轮合成电池（51 片） | 全 SAME | `TALLY SAME=51 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`，`files fully matched: a=40 b=40`（`logs/tally_b51.txt`） |
| **G3** 承重锚点电池（106 个） | 全 SAME | `TALLY SAME=106 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`，`a=76 b=76`（`logs/tally_a106.txt`） |
| **G4** 全 402 逐文件 sha 优先 A/B（**唯一发货判据**） | 0 REGRESSION、0 ERR | `TALLY SAME=400 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0`；整文件全匹配 `374 → 375`（`logs/g4_landed.all.jsonl` / `g4_r37a.all.jsonl`） |
| **G4′** 对每个产物变化的文件跑 strict 尺 | Σ\|Δ\| 不升、缺陷函数数不升 | `logs/g4prime37_readings.txt`：`strategy.pyc 25/27 σ=2 Σ\|Δ\|=21 → 25/27 σ=2 Σ\|Δ\|=0`；`realtime_event_source.pyc 10/12 σ=2 Σ\|Δ\|=17 → 10/12 σ=2 Σ\|Δ\|=7`（`clock_worker +16 → +6`） |
| **落地** | 与工作区字节全等 | `land37.py land --spec=spec37a.json --mirror=mirr_r37a --apply` 先打印 `edits 1 inserted lines 3 nl=CRLF BOM=True` 与 `replay == measured mirror bytes: OK (2984567 bytes)`，再写盘：`2984324 -> 2984567 bytes, CRLF 48421, BOM=True, equals measured mirror=True`（`logs/land37.py`、`logs/core_identity37.txt`） |
| **G5** `single` 靶子 + canary | 靶子官方尺满格且在册产物 == 候选臂产物；canary 产物字节不变 | 靶子 `total_functions 24 matched 24 rate=100.00%`；`strategyOK.py` 重生成 13159 字节 `68c457315b02353f`，与 `build_r37a` 产物**字节全等**（`logs/g5_strategy.txt`）。canary `fly/data/quotation.pyc total_functions 143 matched 143`，产物仍 183261 字节 `3f2242e73d7fd56a0096`（与 Round 36 收尾值逐字节相同，`logs/g5_canary.txt`） |
| **G6** `batch --index pyc_index.json --all --round 37` | 402 全复验、索引回写、逐字段 diff | `logs/g6_batch_all37.txt` 402/402 跑完 0 failed。索引 diff：`last_tested_round 36→37` 共 402 条（例行），**实质变化只有 3 个字段、全部落在 `strategy.pyc`**：`matched_functions 23→24`、`decompile_status partial→ok`、`bytecode_match_rate 0.9583…→1.0`；Σfc 5746→5746、Σmatched 5649→5650、全匹配文件 374→375、partial 28→27。产物侧 `git status` 只有 `strategyOK.py` 与 `realtime_event_sourceOK.py` 两个 `M`，且两者与 `build_r37a` 产物各自字节全等（`68c457315b02353f` / `b1b282deba63cd16`） |
| **G7** `stats` 原样 | — | 见 `OUTCOME.md` 引用的 `logs/g7_stats.txt` |

G4′ 的两条 residual 定性：`tick_publish_thread` 的 `#44 POP_JUMP_IF_TRUE` 终点差与翻转后的
`tick_worker_thread #62` 同为 `[target_diff]`，属在册「操作数同一性」族，不是本轮判据的产物；
`clock_worker +6` 与 `get_one_event +1` 为 R22/R23 在册残余，本轮只把它从 +16 推进到 +6，未收口。

## 七、本轮把 G0 见证钉成常驻电池

`test_repros/round37_ancestor_elif_or_arm/`（`logs/pinbat37.py`）：4 片见证 + 4 片控制，`.py` 入仓，
`.pyc` 由 `py_compile` 现地重编（`.gitignore:2` 忽略 `*.pyc`，与 round36 目录同一做法）。
在落地字节上重跑：`logs/g0_pinned_on_landed.txt` → `cases=8 CLEAN=8 DEFECT=0`。
Round 38 的 G2′ 应为 51 + 这 8 片 = 59。

## 八、残余账（移交 Round 38）

1. `matcher :: match 713/689`：R37-B 已否证，但机制线索可用——`region_analyzer.py:17290`
   `_collect_branch_blocks` 的停止集、等长换位见证、暴露面 21 函数/13 文件。取它之前先解决排序。
2. `OverNightOrder.__init__ 172/148 −24`（#41，`base.pyc` 唯一残余，本轮 `base.pyc` 已是 41/41）。
3. `decrypt_database_url 295/324 +29`（过量发射，需放弃发射侧）。
4. `clock_worker 1275/1281 +6`（本轮推进 10 条，仍未收口）；`events 510/508`（欠定）；
   `_init_config 86/84`（R16 J1 在册反例，受保护）。
5. 汇合块残余 + 合成见证 `r29x_01 <module> 142/138`（#61）。
6. 等长换位 5 处：`fileio_utils::write`、`graph`、`logger`、`scheduler`×2。
7. or 臂形状的另一半仍未探：线 A 的 `w2_outer_three_arms` 产物里出现「mangled or-arm」，
   本轮判据没有覆盖它（该片在候选下 14→14）。
8. `:2118` 附近读 `orelse` 的那处同族读者本轮未动。
