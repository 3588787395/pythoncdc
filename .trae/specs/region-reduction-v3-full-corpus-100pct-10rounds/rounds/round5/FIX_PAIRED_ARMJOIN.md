# Round 5 · FIX_PAIRED_ARMJOIN —— 配对票（E1 臂语句段交付 + 臂尾汇合身份）实测：语料 0 翻转 ⇒ 字节级回滚

轮次：Round 5 / 破口 = `FIX_LOOP_EXIT.md` §7.1 判定的「必须成对落地的两半」
（E1 站点 `region_ast_generator.py:21080` + 臂尾汇合块身份 = 本层顺序续流块优先于祖先汇合块）。
主靶 `<module>.RealtimeEventSource.clock_worker`（`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` 12/13 → 目标 13/13）。
判定尺：唯一判据 `scripts/pyc_verify.py`（全程未改、未替代）。产物一律**先删后** `python -X utf8 pycdc.py -o <base>OK.py <pyc>` 重生成，无手改。
插桩：全部临时探针在 `D:/Temp/rrv5/`（probe3.py 区域/CFG 窗口探针、probe4.py 闭包求解离线探针、hunks.py 差量探针、prod_v2.py 试改态产物快照、rag.baseline.py / ra.baseline.py 入轮备份），生产目录零新增文件。

**结论标记：「仅归档 spec 未落地」**。
**语料翻转：0**（`realtime_event_source` 12/13 → 12/13、`profiler_func` 17/18 → 17/18、`strategy` 26/27 → 26/27）。
合成臂翻转：0（`r4_probe_index` 试改态 71/81 单元、27 success / 10 failure，与入轮逐位相同，且零条绿臂转红）⇒ **交付物 4（追加臂）不执行**；索引完整性另行复核 = 37 条唯一路径、盘上 `r4v3_*.pyc` 37 个（见 §6）。

---

## 1. 逐步实测差量与 hunk 计数（全部为本票实测原文）

| 步 | 改动 | 该单元 orig/prod 指令数 | 差量 | 真分歧（非位移伪影）hunk | 关键形态 |
|---|---|---|---|---|---|
| S0 | 入轮基线（未改码） | 1280 / 1178 | **−102** | 25 | `persist_flag` 段整 100 条丢失（`delete orig idx[1054:1154]`） |
| S1 | **E1**：站点 21080 由 `blocks=[7668]` 改为 `_or_extension_arm_block_run(...)` 序列（复现 FIX_B117 §2 配方） | 1280 / 1276 | **−4** | 3 | `persist_flag` 0→3 出现、`OK.py:276` 段就位；`delete orig idx[841:857]`（off6690 起 16 条）仍在，该段被外提到 `OK.py:312`（臂外一级） |
| S2 | **E2-v1**：`_process_if_blocks` 入口加「臂块序列的前驱闭包延补」，种子 = 臂块 ∪ **宿主条件块** | 1280 / 893 | **−387** | — | 链@6280 的父臂一次被补进 **36 块**（6702…9144，含兄弟臂入口 6846/7164/7582/7634/8592/8904 与整条后续链），S1 交付的 100 条 `persist_flag` 段再次整段丢失（`delete orig idx[1012:1248]` 236 条） |
| S3 | **E2-v2**：闭包**不**把宿主条件块入种子（条件块的正/负跳边落点＝兄弟臂入口/本层汇合，不能当臂内前驱） | 1280 / 1263 | **−17** | — | @6548 与 @6280 各补 `[6702, 6778]`；臂尾就地就位，但链@7164 的 `elif` 臂@7216 臂体塌成 `pass`（S1 无此形） |
| S4 | **E2-v3**：加「**最内层认领者**才补尾」守卫（存在其他区域 R2 满足 `入口块 ∈ R2.blocks ∧ R2.blocks ⊊ host.blocks` ⇒ 本宿主是父臂，不改序列） | 1280 / 1263 | **−17** | — | 闭包只对 @6548 生效（probe4 实测 ADDED=[6702,6778]）；`OK.py:243-245` = `if holiday_not_do_before == '0': put(BEFORE_TRADING_START)` + `self.before_trading_date = now_date` **在臂内**，off6690 段不再外提 |

S4 后仍存的**四类真分歧**（多重集实测，扣除 ±位移重编号伪影后）：

| # | orig | 现状 | 归属根 |
|---|---|---|---|
| 1 | off5612 `POP_JUMP_FORWARD_IF_FALSE 9214`（函数尾 sink） | prod → 9082（臂内汇合），S1–S4 同值未变 | 短路出口边落点（B 族，非本票） |
| 2 | 6652/6678 臂尾 `JUMP_FORWARD 6690` | prod 发 `break`（EXTRA 侧 `JUMP_FORWARD 9064` ×8、MISSING 侧 `JUMP_FORWARD 9194` ×6） | try 臂之后的臂尾跳转桩仍被取成**外层**汇合 ⇒ 3 条伪 `break` |
| 3 | off7270–7308 `system_log.debug('获取重登信号量')` 7 条（块 7270 内含「语句 + 第二条 and 腿的测试」） | prod 折叠成 `elif now_date != self.first_run_date and login_semaphore.acquire(...) is False:`，语句被吞 | **AND 腿内嵌语句**（独立族，S0/S1 同缺，与本票两半不同因） |
| 4 | 臂@7216 首 elif 臂体（put + 赋值） | S4 新增：塌成 `pass`（S3 同，S1 无） | 父臂补尾与链发射次序竞争 ⇒ 本票引入的**回退面** |

⇒ **S1+S4 合并后差量 −17 劣于 S1 单改的 −4**：臂尾身份这一半确实把 off6690 段交付回了臂内（结构上正确），但同时使同一函数内**兄弟链**的臂体塌成 `pass`，且 #2/#3 两道分歧独立存在 ⇒ 该单元无法翻到 13/13。

## 2. 语料翻转与 True-hits（唯一验收信号）

| 靶 | 基线 | S1（E1） | S4（E1+臂尾闭包 v3） | 翻转 |
|---|---|---|---|---|
| `realtime_event_source` `clock_worker` | 12/13 | 12/13（−4） | 12/13（−17） | **无** |
| `profiler_func` | 17/18 | 17/18 | 17/18（站点 calls=0，按工单不强行并轨） | **无** |
| `strategy`（`IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc`） | 26/27 | 26/27 | 26/27 | **无** |
| `r4_probe_index` 37 臂 / 81 单元 | 71/81 · 27/10 | 71/81 · 27/10 | 71/81 · 27/10（逐位） | **无**（且零绿臂转红；`r4v3_a02/a06/a07/a08/a09/a13` 仍各 1/2，未达 2/2） |

标记 True-hits vs flips：

| 标记 | 站点 | True-hits（实测） | flips |
|---|---|---|---|
| `[R5-B117-armrun]` `_or_extension_arm_block_run` @21080 | `clock_worker` | 1 次调用 / 1 次多块交付（臂序列 23 块，7668→8590 段就位，`persist_flag` 0→3，差量 −102→−4） | **0** |
| `[R5-B117-armjoin]` `_arm_block_run_by_predecessor_closure` @`_process_if_blocks` 入口 | `clock_worker` | 1 次命中（@6548/then 补 `[6702,6778]`；`OK.py:243-245` 臂尾就地、off6690 段不再外提）＋ 1 次回退命中（@7216 臂体塌 `pass`） | **0** |
| 合成臂 | — | 0 次新增命中（37 臂逐位） | **0** |

⇒ 语料 True-hits 2 / flips 0，合成臂 0/0。按硬验收线（配对票前两半已实测成对、仍不得翻转）**整批回滚**；
本票不复现「命中未翻转即落地」的先前被拒形态。

## 3. 本轮实测新增的两条结构结论（供下一票直接用）

1. **前驱闭包绝不能把宿主条件块入种子**（S2 实弹：链首臂多吞 36 块、差量 −4→−387、S1 的交付被反向抹掉）。
   条件块的正/负跳边落点在结构上**正是**「兄弟臂入口」与「本层汇合块」，把它们当臂内前驱等于把兄弟臂吸进本臂。
2. **生成端补序列不能根治臂尾归属**：`6690` 同时是 `IfRegion@6690` 的 entry、`IfRegion@6548/then_blocks` 的成员**和**
   `IfRegion@6280/then_blocks`（父链臂）的成员（实测成员表），三处认领并存时，父臂补尾会改变链发射次序并压掉兄弟
   `elif` 臂体（#4 回退）。加「最内层认领者」守卫（S4）只把回退面收窄、未消除。
   ⇒ 正解在**分析端唯一归属**：`IfRegion@6690` 的 parent 应为 `IfRegion@6548`（现测 = `LoopRegion@5598`），
   且 `6702`（体内块）与 `6778`（该 if 的汇合块、全部前驱 = {6690,6702} 在臂内）应进 `@6548.blocks/then_blocks`。
3. **`Region.exit` / `exit=` 路线**已由 FIX_LOOP_EXIT §1 判死（发射端零消费点），本票未再触碰；
   `_trailing_rn_exit_count`（`region_ast_generator.py:2357/2363`）未动、未据其立规则；E2（幻影 loop-else，
   `region_analyzer.py:4810-4845`）本票未做（它管的是 `while` 宿主的合成臂族，与本票主靶的 `if` 宿主臂尾是两个独立站点）。

## 4. 门禁读数（**回滚后终态字节**实测原文；4 套电池与两语料靶的产物均先删后重生成再判）

```
single realtime_event_source   12/13   （重生成后复判）
single profiler_func           17/18   （重生成后复判）
batch round4/r4_probe_index    71/81 单元  files 27 success / 10 failure / compile_error 0 / error 0   STAY
batch round1/r1_probe_index   108/110 单元  files 44 success / 2 failure                               STAY
batch round1/r1_regress_index  34/34  单元  files 17 / 0                                               STAY
batch round2/r2v3_probe_index 105/126 单元  files 41 / 21                                              STAY
batch round3/r3_probe_index   101/122 单元  files 35 / 21                                              STAY
pytest 6 套件                   2 failed / 277 passed / 2 xpassed（仍 test_B01_simple_if_then_else_merge、
                               test_BOUNDARY_02_large_function）
import core.cfg.{region_analyzer,region_ast_generator,code_generator} OK；python -X utf8 -m compileall -q core OK
未跑：402 语料八分片批（按工单由主代理持有）。
```

pin 复判（20 条，全部 = 基线，无一下跌、无一下涨）：

```
fly/data/quotation 152/153（失败单元仍 <module>.get_fundflow_day）· IQCommon/logger/handlers 29/30
IQEngine/data/trading_dates_mixin 14/14 · …/position_model/stock_position 37/37 · IQCommon/util/cgroup_utils 8/8
IQCommon/util/email_utils 4/4 · IQData/…/calexrights_func 8/8 · fly/common/future_contract_info 29/29
fly/logger 64/64 · fly/simtradding/ptradeAccount 137/137 · fly/data/quote 86/92
IQCommon/util/trade_info_utils 37/41 · IQEngine/plugins/plugin_system_trade/trade_live_broker 118/128
IQEngine/plugins/plugin_fly_data/strategy/strategy 26/27 · IQData/api/api_base 27/28
IQEngine/plugins/plugin_system_matcher/matcher 16/17 · IQCommon/data/finance 31/32 · IQEngine/core/bar 84/85
fly/common/function 70/71 · fly/dumpload/load_daily 26/27
说明：这 20 条按判据直接判在盘产物（未在本票重生成）；代码态与 FIX_A_FAMILY 落地后逐字节相同
（两文件 sha256[:16] 见 §5），故读数为基线本身。
```

## 5. 回滚 · 字节完整性 · 插桩残留

```
core/cfg/region_ast_generator.py  3684310 bytes / \n 58668（行数口径 58669）/ 前导 BOM 1 / CRLF 58668 /
                                  bare LF 0 / sha256[:16] = ab05c4c6bb9da904
                                  与入轮备份 D:/Temp/rrv5/rag.baseline.py 逐字节相同（cp 复原 + 哈希核实）
core/cfg/region_analyzer.py       2045409 bytes / \n 32167（行数口径 32168）/ 1 BOM / CRLF 32167 / bare LF 0 /
                                  sha256[:16] = 2a7517c61b083449   —— 本票全程未改（备份比对相同）
core/cfg/code_generator.py        299897 bytes / 6022 行 / 无 BOM —— 未触碰
ast.parse 两文件 OK；编辑期间 CRLF 全程保持（三次实测 lf 计数 == crlf 计数，bare LF 0）
标记复验（core/cfg/ 三文件合计，与入轮逐条相同）：
  [R2-B106] 4 · [R2-B107] 7 · [R2-B108] 5 · [R3-B115] 1 · [R3-B109] 3 ·
  [R4-B116 sinkexit] 4 · [R5-B100-armjoin-trueentry] 4
插桩残留 grep（python 计数，core/**/*.py + scripts/**/*.py + test_repros/**/*.py 全量）：
  R5-B117-armrun → 0 · R5-B117-armjoin → 0 · _or_extension_arm_block_run → 0 ·
  _arm_block_run_by_predecessor_closure → 0 · armrun → 0 · _r5_b117 → 0 · probe[0-9] → 0
  （「armjoin-trueentry」命中 4 = 存活的 [R5-B100-armjoin-trueentry] 原标记，非本票残留）
禁止前缀命名新增方法 0；硬编码深度/数量/语句数上限 0；文件名·函数名·偏移特判 0；
文本后处理 0；抑制式发射（删 continue/pass 掩盖归属）0；发射死代码粉饰 hunk 计数 0。
临时脚本 probe3.py / probe4.py / hunks.py / prod_v2.py / r4_trial*.json / bk 备份全在 D:/Temp/rrv5/，
生产目录零新增文件。
```

## 6. 交付物 4 不执行的核验 + 索引完整性

无翻转 ⇒ 不追加臂。按工单警示复校索引（既往有 helper 脚本覆盖该文件的事故）：

```
test_repros/round4/r4_probe_index.json 条目 = 37，unique = 37，全部 r4v3_*.pyc
盘上 test_repros/round4/r4v3_*.pyc = 37 个 ⇒ 条目与实存一一对应，本票未改动该索引与前四轮任何索引/REVIEW/FIX 文档。
```

## 7. 收窄后的残余（下一票最窄表述）

1. **`clock_worker` 13/13 的最小并集 = 4 手，而非本票的 2 手**（工单假设的「E1 + 臂尾汇合身份」只覆盖 #2 的一半）：
   ①臂尾**分析端**唯一归属（§3.2：`IfRegion@6690` 的 parent 由 `LoopRegion@5598` 改判为 `IfRegion@6548`，
     并把 `6702`/`6778` 收进 `@6548.blocks ∪ then_blocks`；判据 = 前驱全在臂内 + 宿主 merge 显式排除 + 最内层认领者优先，
     全部在白名单内）；
   ②try 臂尾跳转桩不再取外层汇合（#2 的 3 条伪 `break`，EXTRA `JUMP_FORWARD 9064` ×8 / MISSING `JUMP_FORWARD 9194` ×6）；
   ③`system_log.debug('获取重登信号量')` 的 **AND 腿内嵌语句**吞并（#3，7 条，独立族，S0–S4 同缺，
     不修它本票前两手再对也不翻转）；
   ④短路出口边落点 5612→9214（函数尾 sink）vs 9082（#1）。
   本票实测：①+②在生成端做 ⇒ ⑤新增回退（兄弟 `elif` 臂@7216 塌 `pass`），故①必须走分析端。
2. **`profiler_func` 17/18 仍不属本族**（E1 站点 calls=0 实测复述、E2 闭包对其无影响、读数逐位不变），留在册。
3. **E2（幻影 loop-else）与合成臂哨兵集未动**：`r4v3_a02/a06/a07/a08/a09/a13` 仍各 1/2，其闸门是
   `region_analyzer.py:4810-4845` + 「回边桩 = continue 语义交付」那一对，与本票的 `if` 宿主臂尾是两个独立站点，
   不得凭空并票。
4. **walk 侧、`exit=` 侧、`_trailing_rn_exit_count`** 三条已判死路线本票均未再投资（§3.3）。
