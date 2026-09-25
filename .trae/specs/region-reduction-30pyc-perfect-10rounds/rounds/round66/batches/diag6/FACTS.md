# Round 66 · diag6 · FACTS（只读诊断；仓库零改动）

纪律：`python -X utf8`，不设 PYTHONIOENCODING；每命令 <300s；不写 `F:/Downloads/pythoncdc-main`。

## Step 0 — landed 基线复放（必须与 BRIEF 逐支相同）

命令：
- `python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl`
- `python -X utf8 h62.py run --arm=landed --list=battery.txt --out=dump/battery_landed.jsonl`
- `python -X utf8 h62.py run --arm=landed --list=canary.txt --out=dump/canary_landed.jsonl`

实测（landed，全部与 BRIEF 基线逐支一致）：
- targets 6 支：logger 29/30 jd1、matcher 16/17 jd10、realtime_event_source 11/12 jd10、
  IQData/utils/common_func 23/24、api_base 24/25（get_history_df 1742/1719 jd14 td1277）、
  IQCommon/util/common_func 20/21。**一致，继续。**
- battery 24 支：合计 91/104，逐支 mism 与基线相同（含 r64d5_contsink 1/2、r65d5_probe 2/2）。**一致。**
- canary 4 支 sha 逐支相同：4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177。**一致。**

## Step 1 — 残余函数 hunk 表（`nhunks.py ... --ctx=3`，全量存 `logs/nh_*.txt`）

| 函数 | orig/decomp | 归一 hunk | 判定 |
|---|---|---|---|
| `IQCommon/util/common_func::get_kline_time_by_frequency_array` | 254/251 | 1 个：`delete orig[203:206]@1070(3)` | **真缺语句**：`del freq_k_minute[0]`（LOAD_FAST/LOAD_CONST/DELETE_SUBSCR）整条不在产物里 |
| `IQData/utils/common_func::handle_exrights` | 304/297 | `delete orig[16:24]@64(8)` + `insert decomp[289:297]@1474(8)`（同一 8 条） | **纯换位**：`return real_data if fields else real_data[fields]` 被挪到函数末尾 |
| `fly/logger::write_logging_thread` | 127/128 | `delete orig[78:87]@368(9)` + 尾部 insert | **换位**：`if msgs:` 块（orig 368..424）排到 if/else 之后 |
| `matcher::match` | 800/809 | 4 个（大块尾部重排） | 换位家族（R65：orig[207:519] 与 B[483:807] 相似度 0.9748） |
| `realtime_event_source::clock_worker` | 1442/1458 | 14 个 | 换位 + **重复发射**（第 4 臂） |
| `api_base::get_history_df` | 1900/1873 | `delete orig[1039:1063]@4982(24)` | **真缺语句**（见下，与 R65 描述不同：缺的是 guard 体内的赋值 + 其 if 链） |

## Step 2 — 归因（全部用 `grep -n` 在当前落地字节上取行号 + 运行时探针，仓库零改动）

### 2a. `get_kline_time_by_frequency_array`（已定性、已修）
* 原源码：`del freq_k_minute[0]` 位于 if/else 汇合块 `block@1070`（1070..1292），
  该块同时是 `LoopRegion@1294` 的 **for_iter_setup 块**（`…GET_ITER@1292 | FOR_ITER@1294`）。
  `regdump`：`LoopRegion@1294 blocks=[1070,1294,1296,1334]`，1070 既非 body 亦非 else。
* 运行时栈（`logs/probe_where_kline.txt`，`probe_where.py` 打印调用链）：
  `_generate_block_statements` → `_generate_block_statements_body(blk=1070)` →
  `_generate_loop` → `_loop_generate_for`(4580) → **`_loop_extract_for_iter_pre_stmts`(7158)** →
  `_build_store_statement(instrs=1070..1154)` 只返回 1 个 `Assign`。
  `probe_blk.py` 实测该块返回 `[Assign,Expr,Assign,Assign,For,Return]`（6 条，缺 Delete），
  全函数轨迹中 `Delete` 出现 0 次。
* 根因（落地字节 `core/cfg/region_ast_generator.py` 行号）：
  `_loop_extract_for_iter_pre_stmts`（定义 **7081**）是「直线块语句流 → 前置语句」的
  终止符状态机，已认 `STORE_*`(7146)、`UNPACK_SEQUENCE`(7181)、`STORE_SUBSCR`(7205)、
  `STORE_ATTR`(7212)、`POP_TOP`(7226)、`GET_ITER`(7234)，**唯独不认 `DELETE_SUBSCR/DELETE_ATTR`**
  ⇒ `del` 的 LOAD 段留在 `_buf`，被下一条 `STORE_FAST kline_ndarray` 归并吞掉。
* 同层次镜像证据（同一契约已有两份实现，本方法缺第三份）：
  `_loop_extract_self_loop_stmts` **8933**、`_generate_stmts_from_instrs` **48368**
  均已有 `if _instr.opname in ('DELETE_SUBSCR','DELETE_ATTR')` 终止符；
  `_generate_block_statements_body` 的 CONTINUE 路径 **44419** 同样有。
  （`_loop_extract_pre_stmts_from_block`(7244) 是零调用死码，不属本修点。）
* 复现：`synth/r66_delrepro.py`（14 行，p_a 用 DELETE_SUBSCR、p_b 用 DELETE_ATTR，
  均为「汇合块内含 del + 赋值 + GET_ITER」）→ landed **1/3**
  （`p_a 36/33`、`p_b 16/14`，两条 del 全丢），名单 `del.txt`。

### 2b. `api_base::get_history_df`（真缺语句，**非** R65 所述形状）
* 缺失段实测是 **guard 体首条赋值**：`tmp_dividends = engine_obj.basic_data_handler.get_dividend(symbol, None)`
  （@4986..5038），R65 记成 `if not tmp_dividends: …`。原源码：
  `if fq == DIVIDEND_CALC_TYPE[1] and len_real_data > 0:` → 体第一句即该赋值，
  紧接 `if tmp_dividends and symbol not in tmp_dividends and len(tmp_dividends[symbol]) == 0:`。
* `regdump`：`IfRegion@4986 inline_boolop_chains={blocks:[Block138 4986-5042, Block139 5044-5050],op:'and'}`
  ⇒ 短路链**首块 138 头部装着一条完整赋值**（4986..5038 STORE_FAST），
  链重建把整块当左操作数，赋值被吞。产物 377-379 行因此变成
  `if fq == … and len_real_data > 0:` / `return real_data if fields is None else real_data[fields]`
  （那是 else 臂/尾块），体丢失 24 条。
* 探针 `probe_where.py … 4986`：**零命中**——`_build_store_statement/_build_statement/
  _generate_stmts_from_instrs/_build_effective_stmts` 从未收到以 4986 开头的指令段，
  即该段根本没进入任何语句归约器，被表达式重建直接吃掉。
* 现成同层次契约是 `_split_block_condition_prefix`（336）+ `_collect/_take_assert_prefix_stmts`
  （443/463，Assert 通道）与 5855 的 `_r23_cond_prefix`（BoolOp 通道）；
  `inline_boolop_chains` 的 If 通道（12426/17455 两处 `_main_ibc`）**没有**前导语句切分。
  要补的是「链首块前导完整语句」的抽取+父序列回吐，跨 2 个发射点、需新增暂存契约，
  且 R65 已警告该形状与 `[R65-D5-A/B]` 近邻相互作用 ⇒ 本轮按 **候选：NONE（本支）**处理，
  证据即上述零命中读数（不交多锚点 spec）。

## Step 3/4 — 复现 + 唯一 spec

`specs/cand_r66_iterpre_del.json`（单文件 `core/cfg/region_ast_generator.py`、单锚点：
`STORE_ATTR` 终止符块，LF 归一文本 `count==1`（实测打印 `anchor count = 1`））。
补丁 = 在 `_loop_extract_for_iter_pre_stmts` 追加 `DELETE_SUBSCR/DELETE_ATTR` 终止符，
复用 `_build_delete_stmt`；三要素写在注释里（识别条件=同块直线流的语句终止指令；
归约方式=`_buf+[DELETE_*]`→一条语句，归约失败则逐字保留改前行为；
AST 映射=`Delete(targets=[Subscript|Attribute(ctx='Del')])`）。
无名字/偏移/阈值判据、无跨区域包含、无抑制发射。

## Step 5 — 实测（`--arm=cand`）

* repro `del.txt`：landed **1/3** → cand **3/3**（两条 del 均回来）。
* targets：`IMPROVED IQCommon/util/common_func.pyc 20/21 -> 21/21`，
  `TALLY SAME=5 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`。
* battery：`TALLY SAME=24 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`，fully matched 17→17；
  `r65d5_probe` 仍 **2/2**、`r64d5_contsink` 仍 1/2（未回退）。
* canary：`SAME=4`，sha 逐支不变：
  4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177。
* dumps：`dump/del_landed.jsonl`、`dump/del_cand.jsonl`、`dump/cand_targets.jsonl`、
  `dump/cand_battery.jsonl`、`dump/cand_canary.jsonl`。

## Step 1 — 残余函数 hunk 表

## Step 1b/2b — 换位家族与「缺语句」家族其余支的实测归因

### 换位家族（matcher / clock_worker / logger）——**候选：NONE（本轮）**
R65 移交的前提（「兄弟槽被追加到父序列末尾 ⇒ 父序列按来源块 entry 偏移稳定排序」）
本轮逐支实测后**只对 matcher 成立**，且排序无法修它：

1. `matcher::match 715/715 jd10`：自算归一化相似度与 R65 逐字一致
   （`orig[207:519]` 312 条 vs `B[483:807]` 324 条 **ratio=0.9748**，
   `logs/nh_matcher.txt`：`delete orig[207:519]@1320(312)` + `insert decomp[483:807]@3060(324)`）
   ⇒ 整块连续、内部顺序未变，确实只是「被挪到末尾」。
2. `clock_worker 1275/1286 jd10`：`orig[1192:1304]` vs `B[1274:1409]` **ratio=0.8907**（自算一致），
   且 `check_trading_time` 引用数 **orig=4 / decomp=5**（自算），
   产物 `realtime_event_sourceOK.py:312-313` 是重复发射的空臂 `elif check_trading_time(...): pass`。
   ⇒ 该支同时含**重复发射**，纯排序不可能修好（135 vs 112 条）。
3. `logger::write_logging_thread 113/113 jd1`：不是「顺序错」而是**归属层级错**——
   `disf` 实测 orig 368..422 = `if msgs: self.logger_bt.info(msgs)`，位于 `if q:` 的 **then 臂内**
   （424 `JUMP_FORWARD to 666` 跳过 else 臂）；产物 `fly__loggerOK.py:100-101` 把它发到
   `if q:/else:` **之后**（循环体末尾）。父序列排序无法把一条语句从兄弟臂里「搬出来」，
   因为它在产物里根本不在同一个父列表。
4. 电池 witness `r64d5_contsink.pyc::probe 122/122 jd1`（与 logger 同指纹）实测是**反方向的同一形状**：
   `logs/nh_*.txt`+产物显示 loop-tail 兄弟 `total = total + 1`（orig@420..430）被
   **吸收进** `if volume_limit:` 臂内（`r64d5_contsinkOK.py` 中位于 `log.info(...)` 之后）。
   ⇒ 两支合起来证明本家族的可修点在 **区域臂的块集合边界（analyzer `_collect_branch_blocks`
   / `then_blocks`/`else_blocks` 收口）**，不在 gen 的发射顺序层。
   `regdump.py matcher.pyc::match`（`logs/rd_match.txt`）直接可见失控的块表：
   `IfRegion@546 then_blocks=[664..2464]`、`IfRegion@664 else_blocks=[732..4960]`（跨越整个函数）。
5. 「origin map 排序」方案的可行性实测（`probe_ast.py` 跑 landed `RegionASTGenerator.generate()`
   后递归收集节点键）：`If` 节点键 = **['body','orelse','test','type']**、
   `For` = ['body','iter','target','type']、`Expr`/`Continue`/`BoolOp` 亦无任何来源字段
   （只有部分叶表达式带 `lineno`）。⇒ 复合语句节点上**连 lineno 都没有**，
   排序键必须靠 `id(node)` 侧表在**所有** append 点登记；gen 是 50409 行、
   `_pre_stmts.append/_stmts.append/ast_nodes.extend` 类写入点分散在数十个函数，
   单锚点做不到；且按第 3、4 点，做完也修不动 logger/probe 两支 ⇒ 本轮判 **NONE**，
   移交建议：把判据从「排序」改到「IfRegion 臂块集合的上界收口」
   （同层次身份 = 臂的块必须止于同层下一兄弟区域的 entry / 本区域 merge_block，
   而非现在的「无界吞并」），以 `r64d5_contsink::probe`（122/122 jd1，15 行内）为单点见证。

### `IQData/utils/common_func::handle_exrights 276/268`——**候选：NONE（本轮）**，且**不是**换位支
* 定性更正：`delete orig[16:24]@64(8)`+`insert decomp[289:297]@1474(8)` 是**无害换位**
  （`return real_data if fields is None else real_data[fields]` 从 guard 体挪到函数末尾，
  产物 337-375 行整体是「反转 guard」的合法重排）；**真正少掉的 8 条在 guard 条件里**：
  `replace orig[6:15]@12(9) → decomp[7:8]@14(1)`。
* 原源码 guard（`disf --start=0 --end=90` 实测）是三段短路
  `if not tmp_dividends or symbol not in tmp_dividends or len(tmp_dividends[symbol]) == 0:`
  （块1=0..4、块2=6..12、块3=14..62），产物 guard 只剩
  `if tmp_dividends and symbol in tmp_dividends:`（`common_funcOK.py:338`）⇒ **第三个操作数整条丢失**。
* `regdump.py`（`logs/rd_exrights.txt`）：`IfRegion@0 inline_boolop_chains={blocks:[Block1 0-4,
  Block2 6-12], op:'and'}` —— 链只登记了 **2/3** 个操作数，块3（14..62）被降级成
  `then_blocks[0]=14` 的普通 Region，于是它的条件指令段既没进 guard 也没成为语句 ⇒ 8 条蒸发。
  即缺的是「短路链续块归属判定」，与 api_base::get_history_df 的
  `inline_boolop_chains` 少链首块前导语句是**同一通道的两个方向**（一个少算块、一个吞掉块头语句）。
* 未做 spec 的理由（代价证据，非猜测）：判据要落在 analyzer 的链扫描（`region_analyzer.py:19816-19831`
  主条件链装配、17435、15796 一带）与 gen 的 `_main_ibc` 两处消费点（12426 / 17455），
  属多锚点；且该通道正是 R65 `[R65-D5-A]/[R65-D5-B]` 的落点，电池 witness
  `r65d5_probe` 与 `r63b4_cond_boolop_stmt_steal`(13/13) 全在此链路上，单轮内无法给出安全单锚点。

## Step 6 — 402 全量分片 A/B（`D:/Temp/opencode/r65gate/all402.txt`，`--nshard=4`）
`dump/a402_landed.jsonl`(402) vs `dump/a402_cand.jsonl`(402)，日志 `logs/a402_run.log`：

```
IMPROVED F:/.../IQCommon/util/common_func.pyc  20/21 -> 21/21
TALLY SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0
files fully matched: a=385 b=386
```
⇒ 402 支逐支有读数、无 ERR、无回退、无 MOVED；净 +1 文件全匹配。

## 结论
* **landed-ready 唯一 spec**：`specs/cand_r66_iterpre_del.json`
  （gen `_loop_extract_for_iter_pre_stmts` 的 DELETE 终止符）。
  repro 1/3→3/3；targets +1（get_kline_time_by_frequency_array 231/228→231/231 全匹配）；
  battery SAME=24（r65d5_probe 保持 2/2）；canary 4 sha 逐支不变；402 SAME=401/IMPROVED=1/REGRESSION=0。
* 其余 5 支残余：**候选：NONE**，排除证据见上（logger/probe = 臂块集合无界吞并，非顺序；
  matcher = 仅顺序但排序需多锚点侧表且对同族无效；clock_worker = 排序之外还有重复发射；
  api_base / handle_exrights = `inline_boolop_chains` 通道，多锚点且与 R65-D5 落点重叠）。
* 本轮仓库零改动：所有写入均在 `D:/Temp/opencode/r66gate/diag6`
  （`h62.py build` 的 head 镜像 == 工作树断言每轮均通过，见 `mirrors built` 行）。

## 附：strict 尺（`cstrict.py`，独立于计数尺）+ 仓库零改动核验
`logs/strict_landed.txt` vs `logs/strict_cand.txt`（逐文件 strict ok/functions，missing=extra=0 两侧全部）：

| 文件 | landed | cand |
|---|---|---|
| fly/logger.pyc | 62/64 | 62/64 |
| matcher.pyc | 16/17 | 16/17 |
| realtime_event_source.pyc | 10/12 | 10/12 |
| IQData/utils/common_func.pyc | 26/27 | 26/27 |
| IQData/api/api_base.pyc | 26/27 | 26/27 |
| IQCommon/util/common_func.pyc | **21/22** | **22/22** |

⇒ 严格尺同向：只有靶支变好，其它逐支不变（`get_kline_time_by_frequency_array` 的
`[seq_len] orig=232 decomp=229` 缺陷在 cand 上消失）。
`git -C F:/Downloads/pythoncdc-main status --porcelain` 仅剩上一轮遗留的未跟踪文件
（`.trae/.../round65/batches/diag0/logs/env*.err`、`_r10_difflen.py`），本轮未新增任何仓库写入。

## 交付物清单
* `FACTS.md`（本文件）
* `specs/cand_r66_iterpre_del.json`（唯一 landed-ready spec；单文件单锚点，anchor count 实测 = 1）
* `synth/r66_delrepro.py`（14 行复现）+ `synth/r66_delrepro.pyc` + `del.txt`
* `dump/`：landed.jsonl、battery_landed.jsonl、canary_landed.jsonl、
  del_landed.jsonl、del_cand.jsonl、cand_targets.jsonl、cand_battery.jsonl、cand_canary.jsonl、
  a402_landed.jsonl、a402_cand.jsonl
* `logs/`：nh_{logger,matcher,clock,api,exrights,kline}.txt、rd_{kline,api,exrights,match}.txt、
  probe_{del,blk,where}_{kline,api,api2,match}.txt、dis_kline_orig.txt、a402_run.log、
  strict_{landed,cand}.{txt,json}、probe_*.py（探针产物）
* 探针脚本（只读、进程内 monkey-patch，不落仓库）：`probe_ast.py`、`probe_del.py`、
  `probe_blk.py`、`probe_where.py`
