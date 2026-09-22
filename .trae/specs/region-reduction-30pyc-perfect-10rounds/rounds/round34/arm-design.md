# Round 34 arm design — 目标池（实测 landed 762e8213）与三条线的取舍

## 一、目标池（一手实测）

池由 `D:/Temp/r34gate/pool34.py` 直读 Round 33 G6 回写的索引（该索引已被 Round 33 的 `head` 臂逐文件
复测过，`logs/index_vs_head_arm.txt` 0 冲突），再经两条 `--arm=landed` 复测拉回实测：

```
baseline(landed round33 index, HEAD 762e8213, core sha 2d3a5d51d114da77d3d4): files 402 partial 30 sum_deficit 100 deficit1 7 deficit2 12
```

`pool34.py` 内的断言：索引 `len==402`、`Σfunction_count==5746`、`Σmatched_functions==5646`、
`all(last_tested_round==33)`、落地核 `sha256[:20]==2d3a5d51d114da77d3d4` 且正规化后 ==
`git cat-file blob HEAD:core/cfg/region_ast_generator.py`、`git status --porcelain -- core` 为空。

deficit-1 池 7 个文件，逐个在落地字节上复测（`logs/landed_d1.jsonl`，官方尺），**每个文件恰有一个缺陷
函数**：

| 文件 | 读数 | 唯一缺陷函数 `orig/decomp j t` |
|---|---|---|
| `IQCommon/manager/instance.pyc` | 31/32 | `_init_config 86/84 j1 t37`（R16 J1 在册反例，受保护勿再取） |
| `IQCommon/util/replace_utils.pyc` | 8/9 | `decrypt_database_url 295/324 j1 t250`（#43 老账，+29 过量发射） |
| `IQEngine/plugins/plugin_fly_data/strategy.pyc` | 23/24 | `tick_worker_thread 268/247 j32 t113`（R32 线 B 只留线索） |
| `IQEngine/plugins/plugin_system_event_source/default_event_source.pyc` | 13/14 | `events 510/508 j2 t157` |
| `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | 11/12 | `clock_worker 1275/1291 j15 t480`（R22/R23 移交 D2/D3） |
| `IQEngine/plugins/plugin_system_matcher/matcher.pyc` | 16/17 | `match 713/689 j9 t524` |
| `IQEngine/plugins/plugin_system_risk_calculation/function.pyc` | 14/15 | `save_testds_to_json 314/310 j19 t8`（= Round 33 线 B 移交） |

deficit-2 池 12 个文件同尺读一遍存档（`logs/landed_d2.jsonl`，12 条、0 error），因为「一条语句/一个尾声
整条消失」这类形状历史上更多出现在 deficit-2 一侧。Round 33 §七 里被标为「残余 deficit-1 六个」的名单
已在该轮记录内订正：那六个只是上表七行的六个，`wizard_quant_api.pyc 49/53` 的 deficit 是 4，不在此池。

## 二、基线电池（G2′ / G3 的「改前」侧，本轮先建）

* 承重锚点扩为 **104** = Round 33 的 102（由 `anchors98` + Round 31/32 四件合成件重建并与
  `round33/logs/list_anchors102.txt` 逐条比对全等）＋ `test_repros/round33_return_through_statement/r33a_witness.pyc`
  ＋ 靶子 `site-packages/IQCommon/utils.pyc`。落地臂读数 `logs/a104_landed.jsonl`：104 条、0 error，
  两个新锚分别读 `17/17`、`22/22`（与 Round 33 §七 预告一致）。其余 30 条「非全匹配」是锚点的固有
  性质（钉住已知残余形状），G3 的判据是「候选 vs 落地逐条 SAME=104」，不是「104 全匹配」。
* 上一轮合成复现电池扩为 **39** = `reprobat38` ＋ `r33a_witness.pyc`，落地臂读数
  `logs/b39_landed.jsonl`：39 条、0 error、28 条全匹配。G2′ 判据同上是 `SAME=39`。
* 全量 `head` 臂基线（G4 的「改前」侧，同时充当索引时效性证明）：`logs/g4_head.s{0..3}.jsonl` 四片
  合并 `g4_head.all.jsonl` = 402 条、402 个唯一路径、0 error、0 个 `total_functions==0`，
  `Σmatched 5646 / Σtotal 5746`。与 `pyc_index.json` 逐文件比对（matched、count、由匹配推得的
  `ok`／`partial` 三项）→ `logs/index_vs_head_arm34.txt` 记 **0 冲突**，即 Round 33 回写的索引在
  Round 34 的落地字节上仍逐文件成立，候选臂的 A/B 起点无需重推。

## 三、三条线的取舍

* **线 A（代理 `A1`，只诊断）**：Round 33 线 B 交下来的 `function.pyc :: save_testds_to_json
  314/310 j19 t8`。Round 33 归档的严格尺 hunk 已把它压到一处：
  `H1 delete orig[302:306] @1976..1982 → decomp 空`，缺的四条是
  `POP_EXCEPT, POP_EXCEPT, LOAD_CONST(None), RETURN_VALUE` —— 即嵌套异常尾声的**正常退出**那份拷贝
  整条没发射（同函数兄弟路径 `@1944/1948`、`@1952/1954`、`@1964/1966`、`@1968/1970` 的 POP_EXCEPT＋
  RERAISE 对都在）。这是发射侧形状，与 R31-C 的纯 `discard` 判据同教义反侧；Round 28 已用全量 A/B
  否证过「抑制型」候选（破 12 文件），故本轮只接受「补回结构上已存在之物」。
* **线 B（代理 `A2`，只诊断）**：`default_event_source.pyc :: events 510/508 j2 t157`（−2、只有 2 个
  跳转槽错位），本轮池里最便宜且从未被一手刻画过的形状；须先 grep 历史轮次记录确认这不是已否证过的
  老候选。
* **线 C（编排方）**：不动 `core/`；把两条代理线交上来的判据按「先证伪、再上电池、再全量 A/B」的顺序
  自己重量一遍才决定发货哪一条 —— 每轮只发一条同层判据。

（§四起待代理交付与编排方复量后填写。）

## 四、线 B 候选 R34-E 的门禁裁决：G2′ 否证，不发货

代理 A2 交来的判据（`D:/Temp/r34gate/A2/spec_r34e.json`，目标文件 `core/cfg/region_analyzer.py`，
`spurious = [eb for eb in lr.else_blocks …]` 一行加一条豁免）由编排方从**落地字节重新派生**并逐符号
复核：anchor 在该文件唯一（第 4494 行），它引用的 `lr.else_blocks / lr.header_block /
Block.predecessors / start_offset / get_last_instruction / cfg.get_block_by_offset`
全部在同一作用域内已被既有代码使用，候选文本 `compile()` 通过，且重派生结果与 A2 提案
**逐字节相同**（`logs/tool_mk_spec34e.py` 的 `byte-for-byte identical to A2 proposal: True`）。
`region_analyzer.py` 无 BOM、纯 CRLF（26995 行）、正规化 sha256[:20] `2f7c18c2e7b7e3851a2b` ==
HEAD blob，`git status --porcelain -- core` 空 ⇒ 判定前提成立（未被代理改过工作树）。

门禁读数（`r34c.py` 臂 `cand`，`mirr_cand` 比 `mirr_head` 多 1215 字节）：

* **G1（deficit-1 池 7 文件）**：`SAME(sha 全等)=6 IMPROVED=0 REGRESSED=0`，第 7 行即唯一被触及的靶子
  `default_event_source.pyc`（产物字节变了、文件级仍 `13/14`），其 `events` 由 `510/508 j2 t157` →
  `510/509 j2 t155`（取回 1 条指令，文件级不翻转）⇒ 与 Round 31 §六「该靶子需两条判据」一致，
  本判据只是其中一条。读数 `logs/r34e_cand_d1.txt`（＋ `logs/r34e_cand_d1.jsonl`）。
* **G2′（上一轮 39 合成复现电池）**：`SAME=37 IMPROVED=0 REGRESSION=2 MOVED=0 ERR=0`，
  `files fully matched: a=28 b=26`。两条回退是
  `test_repros/round4/r4_06_continue_after_nested_for_dropped.pyc 2/2 → 1/2`
  （`f 56/55 j3 t19`）与 `r4_07_continue_after_two_nested_fors.pyc 2/2 → 1/2`（`f 84/83 j3 t25`）；
  单独重跑 `r4_06` 复现同一读数 ⇒ 不是分片/顺序伪影。⇒ **电池尺 FAIL，不进入 G3/G4，不发货。**
  读数 `logs/r34e_g2prime_cand_ab.txt` ＋ `logs/r34e_b39_cand.jsonl` ＋ 单件复跑
  `logs/r34e_one06.txt`／`logs/r34e_one06_cand.jsonl`。

一手根因（读受跟踪的复现源文件即得，无需推测）：`r4_06` 的形状是

```
for node in tree:                 # 父环
    if …:
        for ca in BLACK:          # 子环，源码里没有 else
            …
        continue                  # ← 子环耗尽后落到父环的下一轮/回边块
```

子环头块的 `FOR_ITER` 耗尽边的目标块（`continue` 的落点）与源码 `else` 子句的落点，在
「前驱集合恰为子环头块 ＋ 入边即头块尾部的迭代跳转」这一组结构事实上**完全同形**。因此
「只在正常耗尽时进入 ⇒ 它就是 else」只是必要条件而非充分条件：父环体内一条结尾 `continue`
会造出同一个签名。候选把 `parent_body` 成员资格一律判为「DFS 传递产物、不构成归属证据」，
在 `r4_06` 这类形状上就把真正的父环归属也一并抹掉了 —— 少发射 1 条、多 3 个跳转槽错位，
与它在靶子上「取回 1 条」的收益是同一机制的正反两面。

回炉方向由只读探针实测后**改为否定结论**（`logs/tool_probe_else34.py` → `logs/probe_else34_landed.txt`，
它原样重算被包裹方法自己的 `parent_loops`／`parent_body`／`spurious` 判据，再并排打印
「A2 的入边独占性 `r34e_excl`」与两条出路事实 `E1`（eb 恰为某外层环的 `back_edge_block`）／
`E2`（eb 尾指令是跳向**别的**环头的回边））。六条相关行：

| cfg | 子环头 | eb | preds | succs | eb 尾指令 | 落地判 spurious | r34e_excl | E1 | E2 |
|---|---|---|---|---|---|---|---|---|---|
| `r4_06 :: f` | 118 | 160 | [118] | [6] | `JUMP_BACKWARD->6` | 是 | 真 | 假 | **真** |
| `r4_07 :: f` | 210 | 252 | [210] | [6] | `JUMP_BACKWARD->6` | 是 | 真 | 假 | **真** |
| `r4_07 :: f` | 118 | 196 | [118] | [210] | `GET_ITER` | 是 | 真 | 假 | 假 |
| `events` | 2708 | **3208** | [2708] | [3214] | `JUMP_FORWARD->3214` | 是 | 真 | 假 | 假 |
| `events` | 1236 | 1606 | [1236] | [828] | `JUMP_BACKWARD->828` | 是 | 真 | 假 | **真** |
| `events` | 2116 | 2182 | [2116] | [828] | `JUMP_BACKWARD->828` | 是 | 真 | 真 | **真** |

⇒ 只加 `E2`（回边出路）确实一次排除 `r4_06`、`r4_07` 的两条 continue 落点与 `events` 自己
被误豁免的两条，并保留第 4 行那条真实收益（`events` 的 `else` 落点 3208）。但**第 3 行否证了
这条路线的可靠性**：`r4_07` 里子环 `for b …` 之后紧跟兄弟环 `for c …` 的 `GET_ITER` 块，
它的入边集合恰为子环头块、尾指令非回边，与第 4 行想要的真实 `else` 落点在全部可读结构事实上
**同形**。原因不是判据写得不够细，而是这一族的语义在字节码层不可判：

> 源码 `for …: pass; else: S` 与 `for …: pass` 后紧跟同一条语句 `S`，在 `S` 本就紧随其后的
> 场合编译出的 CFG 完全相同 —— `FOR_ITER` 的耗尽边目标就是 `S` 的块。于是「只在耗尽时进入」
> 既不能证明也不能否证 else 的存在；落地代码把 `eb ∈ parent_body` 一律判为 spurious 是一条
> **有意的启发式取舍**（Round 30 R30-C1 同族），任何只读入边/出边的同层判据去推翻它，
> 都必然在 `r4_06`／`r4_07` 这类已固定形状上把「没有 else」的落点也补成 else。

⇒ 本轮裁决：线 B 靶子 `events` 的那 1 条收益**不可作为发货判据**取得；R34-E 及其 E2 细化
（暂名 R34-F）都不进入 G3/G4。该靶子的残余（1 条指令＋2 个跳转槽）改判为「字节码层欠定，
需源码级消歧信息（非纯同层结构事实）」，与 Round 31 §六「需两条判据」的说法合并订正：
第二条判据不在归属侧，也不在发射侧，而在**是否有资格宣称 else**这一不可判前提上。
留档：`logs/tool_probe_else34.py`＋`logs/probe_else34_landed.txt`、`logs/r34e_*`（G1／G2′ 读数）。

## 五、线 A（A1）：根因链已一手闭合，但判据本轮不落地 —— 发货位留给 Round 35

代理 A1（scratch `D:/Temp/r34gate/A1`）在 157 次工具调用后撞上 150 轮次上限终止，未交
`ANALYSIS.md`。编排方不引用其未交付的结论，改用**自己重跑的一手测量**把该形状钉死：

1. 靶子自己的字节码（直读 `site-packages/…/function.pyc` 的 code object，`dis` 解出 361 条指令，
   末指令 `@1998 RERAISE`）：
   `@1976 POP_EXCEPT`、`@1978 POP_EXCEPT`、`@1980 LOAD_CONST(None)`、`@1982 RETURN_VALUE`。
   这四条正是严格尺 hunk 报的唯一缺失段（`H1 delete orig[302:306] @1976..1982 → decomp 空`），
   也与原始异常表比反编译异常表多出的那一行 `start=1976 end=1978 target=1994 depth=1 lasti=yes`
   同一段（`A1/exc_table.txt`）。
2. 落地产物 `save_testds_to_json` 全文 48 行（`A1/landed_functionOK.py:320..367`）里只有**两条**
   `return None`：一条在最内层 `try` 体尾（`:353`，缩进 8），一条在最外层可见 handler 体尾
   （`:367`，缩进 12）；**函数级缩进 4 的终止 `return None` 一条都没有** —— 缺失不是「少一条语句」，
   而是「某条退出路径的隐式返回整条没有落点」。
3. 发射侧站点（编排方自己读码，行号取自落地核 `2d3a5d51d114da77d3d4`）：
   `core/cfg/region_ast_generator.py:24687-24694` 已会为一个 `BlockRole.RETURN` 的 handler 块
   就地发 `Return(None)` —— 这就是 `:367` 那条（其块 `@1970` 本身在 `handler_blocks` 里）。
   紧随其后的 R13 后继扫描 `:24707-24734` 是**唯一**越过 handler 块边界向外看一眼的机制，
   而它只有两条臂：`CONTINUE/PURE_CONTINUE` 与 `BREAK/PURE_BREAK`，且都**再要求**该后继块属于某个
   `TryExceptRegion.has_finally` 的 `finally_copy_blocks` 才补发。靶子的后继 `@1956 → @1976`
   是 `role=PURE_JUMP` 的纯清理块（单条 `POP_EXCEPT`），两条臂都不进 ⇒ `@1976` 与其后继
   `@1978`（`POP_EXCEPT LOAD_CONST RETURN_VALUE`，`role=RETURN`）从未被任何区域认领，
   在区域树上留下两个孤儿 BASIC 区域（`A1/regions.txt` 的 `R19 [1976]`、`R20 [1978]`，
   父区域 R2/R4 的 members 均不含它们），整条退出路径无落点。

⇒ 形状定性：**已认领 handler 块的「清理链 → 裸 `return None` 终止块」不在 R13 后继扫描的
识别范围内**；补它属于「补回结构上已存在之物」（与 R32-C 同教义），不是新增语义。

候选（暂名 R35-A，本轮**未写、未测、未发货**）：在 `:24707-24734` 的后继扫描里加第三条臂，
从 `_succ` 起沿**既有** `_cleanup_only_ops` 白名单（`_is_cleanup_only_no_return`，
`:25496`）穿过纯清理块，直到一个过滤后恰为 `LOAD_CONST(None) + RETURN_VALUE` 的块，
则 `handler_body.append({'type':'Return','value':Constant(None)})` 并把链上各块记入
`generated_blocks`；任何一步不满足即原样回落。

必须先解决的前置（否则不得发货）：A1 的语料级**产物侧**剥离实验（`A1/corpus_drop.py`，
语料 46 个文件里 79 个「文本以 `return None` 收尾」的函数，8 片
`logs/corpus_drop.f{0..7}.jsonl`，汇总 `logs/corpus_drop_summary.txt`）给出实测附带损伤 ——
去掉靶子那条终止 `return None` 使其 `delta −4 → 0`，但同尺下另有三个函数反向变差：
`IQCommon/manager/instance.pyc :: Instance._get_manage_info delta 0 → +1`、
`IQCommon/util/trade_info_utils.pyc :: query_trade_strategy_info`（长度不变但转为有缺陷）、
`query_strategy_id delta 0 → −1`。⇒ 判据还需一条**同层的「该清理链是否就是函数唯一收尾出口」**
守卫来把这三例挡在外面；本轮没有把它读出来，因此宁可不发货，也不带着已知附带损伤去跑 G4。

## 六、本轮发货裁决：`core/` 零改动，索引无需回写

* 两条线均无可发货判据 ⇒ 本轮 `core/` 未写入。落地核仍是 `2d3a5d51d114da77d3d4`／
  `git status --porcelain -- core` 为空（`logs/harness_smoke34.txt` 亦以同一 sha 前后各断言一次）。
* 索引**不需要** G6 回写：本轮的全量 `head` 臂 A/B（G4 的「改前」侧，字节即落地字节）与
  `pyc_index.json` 逐文件比对 **0 冲突**（`logs/index_vs_head_arm34.txt`），
  所以 Round 33 回写的 `5646/5746 / 372 ok / 30 partial` 在本轮落地字节上仍然成立；
  本轮既未改核也未改产物，不存在「索引滞后」。收口时的完整性探针
  `logs/core_pristine34.txt`：`git status --porcelain` 对 `core`／`site-packages`／
  `test_repros`／`pyc_index.json` 四项**全为空**。
* 留档（`logs/`，共 83 件，归档脚本 `D:/Temp/r34gate/archive34.py` 逐件断言非空并复核
  本文件引用的每个数；分片 stdout 日志以 `*.log.txt` 入册，因为 `.gitignore:13` 忽略 `*.log`）：`pool34.txt`＋`tool_pool34.py`＋`tool_setup34.py`、
  `list_{d1,d2,all402,anchors104,reprobat39}.txt`、`landed_d1.txt`／`landed_d2.txt`（＋两份
  `.jsonl`）、`a104_landed.jsonl`、`b39_landed.jsonl`、`g4_head.s{0..3}.jsonl`＋`g4_head.all.jsonl`、
  `index_vs_head_arm34.txt`、`harness_smoke34.txt`、`core_pristine34.txt`、
  `tool_{r34c,land34,g4prime34,hunks34,dump34,probe_chain,pycache_probe34,mkmirror_head}.py`、
  `tool_mk_spec34e.py`＋`r34e_spec_r34e.json`、`tool_probe_else34.py`＋`probe_else34_landed.txt`、
  `r34e_*`（R34-E 的 G1／G2′ 全部读数 ＋ A2 自己的 `r34e_agent_*` 锚点 A/B 与发射转储）、
  `R34E_REJECTED.txt`、`tool_corpus_drop.py`＋`corpus_drop.f{0..7}.jsonl`＋
  `corpus_drop_summary.txt`＋`a1_{exc_table,regions,hunks_landed}.txt`＋`a1_landed_functionOK.py`。
