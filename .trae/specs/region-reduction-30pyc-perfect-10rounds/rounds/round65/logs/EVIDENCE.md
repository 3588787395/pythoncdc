# Round 65 — 集中验证记录（EVIDENCE）

主代理 = 集中验证方。所有读数在 `D:/Temp/opencode/r65gate`（中心工作区）用该目录自己的
`h62.py`（`ROOT` 指向中心目录，与六个诊断代理的私有 `ROOT` 隔离）跑出；一律 `python -X utf8`，
未设 `PYTHONIOENCODING`。中心侧脚本：`vfy65spec.py`（spec 落地前体检）、`mkfinal65.py`（合并）、
`mbuild65.py`（建镜像）、`land65.py`（重放并落盘）、`closeout65.py`（landproof + 电池）、
`blast65.py`（产物逐字节爆炸半径）、`cstrict65.py`（严格尺·镜像产物）、`strict_repo65.py`
（严格尺·仓库产物 + 与镜像产物 sha 对齐）、`archive65.py`（归档）。

## A. 轮初基线是可复放的，不是自报的

`dump/a402_landed.jsonl`（`--arm=landed`，6 分片，402/402，0 `error`，0 空读数）逐条比对
**HEAD（R64 落地后）的 `pyc_index.json`**：402 条目 `function_count`/`matched_functions`
**逐条相同（agree 402 / disagree 0）**，合计 5746 / 5689 / 全清文件 384。
⇒ 本轮所有候选的对照臂建立在被索引背书的字节上。

同一份 dump 也是 G5 的 A 侧（落地前）；B 侧是 `dump/a402_m65.jsonl`（合并臂，落地前测）。

## B. 候选体检：12 份 spec 全部对 R64 落地字节干净应用

`python -X utf8 vfy65spec.py <12 specs>` ⇒ `ALL APPLY CLEAN = True`。逐条断言：anchor 在**当前
（已打过前一处编辑的）文本**里 `count==1`、BOM 形态保持、行尾统一（裸 LF 0）、`py_compile` +
`ast.parse` OK，并打印每个 `[R64-*]` 标记的位移。臂 sha 前 12 位（主代理独立复算）：

| spec | 文件 | 编辑 | 净行 | 结果 sha |
|---|---|---|---|---|
| diag0 `cand_r65b0_stripdbg` | generator | 13 | −78 | `de510d95b12f` |
| diag1 `cand_r65_trytail` | generator | 1 | +74 | `af02aa61797a` |
| diag2 `c1_fstring_consumer_dispatch` | generator | 1 | +168 | `abe20270e39e` |
| diag3 `cand_r65d3_c1` / `c2` / `c3` | generator | 1/1/1 | +98/+99/+124 | `7227a67c25c5` / `b28934bfa952` / `0881ca09edc9` |
| diag4 `cand_n1` / `n2` / `n3` | analyzer | 1/1/1 | +29/+5/+50 | `9fd4618b7bd2` / `dd0b323706a2` / `59906ca74482` |
| diag5 `r65d5_a` / `b` / `ab` | generator | 1/1/2 | +38/+50/+88 | `ef1389880220` / `0032e8e04c5a` / `84a136fb707d` |

## C. 逐批判定（代理自述 + 主代理复测；被推翻的写在最右列）

### C.1 diag1（graph / logger / matcher / realtime / api_base）——采纳 A

主代理用中心 `h62.py` 复放：`ab --a=diag1/dump/landed.jsonl --b=diag1/dump/trytail.jsonl` ⇒
`IMPROVED graph.pyc 30/31 -> 31/31`、`TALLY SAME=4 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`、
`files fully matched a=0 b=1`。电池 `SAME=19`、金丝雀 `SAME=4`（其 `dump/battery_*`、`dump/canary_*`）。
**推翻其「全语料 398 支 sha 全等」这条爆炸半径证据**：`diag1/dump/wide_*.jsonl` 的名单是
`site-packages` 递归减靶/金丝雀/电池，实测 **缺 9 支语料文件**（含它自己改善的 `graph.pyc`，以及
`api_base`、`matcher`、`realtime_event_source`、`logger`、两支 `datetime_func`、`quotation`、
`market_time`），且**多 5 支非语料 pyc**（`klinedataOK.pyc`、`klinedataOK_check.pyc`、
`_tmp_difffn.pyc`、`_load_algo_recomp.pyc`、`ptradeAccountOK_marker_test.pyc`）。因此
`SAME=398 / REGRESSION=0` 只覆盖 393 支语料，不能证明「只在两个站点命中」——该结论改由
§D 的真实 402 A/B（`MOVED` 集合恰为 6 支）支撑。候选本身成立，证据链不成立。
另：其 §1.6 的异常表论证（`[560,566)->570`、`[1108,1114)->1118` 不覆盖 `@566`/`@1114` 的
`LOAD_CONST None; RETURN_VALUE`）主代理未在产物上复算，但 `single` 的 31/31 + 严格尺 34/34
（`missing=0 extra=0`）与之一致。

其余四支本轮**不交候选**，理由带排除证据：logger 是 `IfRegion@368` 换位（归属未被破坏，修点在
现场合成 `if q:` 的 then 收口，需改两处）；matcher 与 realtime 是**纯位移**
（312 条 vs 尾部 324 条 similarity 0.9748；112 条 vs 135 条 0.8907，两处 `JUMP_FORWARD↔JUMP_BACKWARD`
翻转）；realtime 那条重复 `elif` 是**空臂**，`drop 312-313` 行只把 1458→1440，5 个大 hunk 一个不消；
api_base 是真缺 24 条（`get_dividend` 在该函数产物内命中 0 次）。

### C.2 diag5（两支 twins + fly/logger 等 7 支）——采纳 ab（a+b 成对）

`ab --a=diag5/dump/w_landed.jsonl --b=diag5/dump/w_ab.jsonl`（18 支）⇒
`IMPROVED IQCommon/util/common_func 19/21 -> 20/21`、`IMPROVED IQData/utils/common_func 22/24 -> 23/24`、
`MOVED trade_live_broker get_etf_stock_info [144,117,1,139] -> [144,146,1,139]`、
`REGRESSION=0`。两支 twins 的 `get_kline_time_by_section` 是同名同形（近重复源），
`A`/`B` 单独都不齐（该代理的 `dump/a.jsonl`、`dump/b.jsonl` 显示单臂只回到一侧），故合并集取 `ab`。

### C.3 diag3（trade_live_broker 14 支缺陷）——采纳 c1；该代理无报告

`FACTS.md` 不存在（150 轮中断）。主代理直接读它的 dump：
`ab --a=diag3/dump/wide_landed.jsonl --b=diag3/dump/wide_c1.jsonl`（18 支）⇒
`IMPROVED trade_live_broker 105/119 -> 106/119`、`MOVED quote.pyc`、`REGRESSION=0 ERR=0`；
电池 `IMPROVED r63_ft4 1/2 -> 2/2`、`SAME=18`；金丝雀 `SAME=4`。
`quote_c1` 与 `quote_c3` 读数**逐元组相同**（`get_price [230,228,0,224]` 等）⇒ `c3` 多出的 26 行
在 quote 上无差别，未采纳。`c2` 只有 spec、无任何 dump，未采纳（不作「无效」结论）。

### C.4 diag4（real_quote / klinedata / risk_calculation / trade_info_utils）——采纳 n1

`FACTS.md` 只写到 §4.6（n1 + 爆炸半径），n2/n3 无文字结论。n1 的判据是**边上的汇入关系**而非
R64 移交线索的字面「被 pop 块是 or-run 首块」——该代理给出关键反例：`r64d1b_closed_exit_prefix.pyc::kbin_repro`
的 pop 形状 `chain=[(0,'or'),(48,'or'),(62,'and')]` 与 klinedata 的 `[(824,'or'),(1090,'or'),(1094,'and')]`
**同构**，字面判据会同时关掉两边（klinedata 修好、witness 与 quote_handler 收益一起丢）。
`sys.settrace` 挂在落地 analyzer 的 `chain.pop()` 行做 analyze-only 爆炸半径：402 支里只有
3 支走到该 pop（`quote_handler` 1 次 / `crypto_utils` 2 次 / `klinedata` 4 次），n1 只抑制
klinedata 的 4 个站点 ⇒ 与主代理的官方 A/B（该函数 `MOVED`、其余 `SAME`）一致。
n2/n3 未集中实测，移交（OUTCOME §6.5）。

### C.5 diag2（`fly/data/quote.pyc` 70/81，11 支缺陷函数）——**不采纳**

它的 `FACTS.md` §2 停在「### 实测（进行中）」，即候选 `c1` 从未被它自己测过。主代理复测其
**六个臂** `c1 c1b c1c c1d c1e c1f`（quote.pyc）⇒ 六臂全部
`TALLY SAME=0 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0`，官方计数钉在 70/81：`get_price` 188→214/212/210
（仍不足 230）、`load_bars_from_hundsun` 470→505（`c1d`/`c1e` 甚至塌到 306）。其合成集
`synth/fs2.pyc` 4/10→5/10、`fsrepro.pyc::m_b` 19→33/39（都不到全绿），电池 1 支 `MOVED`、金丝雀 `SAME=4`。
诊断部分（机制归因、`_fstring_parts_from_segment` L41034 / `_try_wrap_fstring_pending_call` L41198 /
`_ternary_pending_callee` L41084 三个 R63 helper 只接在 `len(ternary_chain) >= 2` 路径 L41331 上、
单三元路径 L35898 一个都没接）经主代理 `grep -n` 逐条核对**行号全部为真**，是本轮最有价值的
机制说明；其 `synth/fs2.py`（v1…v8 + 无三元对照 v5）入库为复现矩阵。候选本身被 diag3 的 C1
取代（同一分支、+98 行却做到 `IMPROVED`）。

### C.6 diag0（技术债：13 处 `_os_dbg_*` 调试导入）——本轮不落地

纯删除 −78 行、`_os_dbg` 行 26→0，该代理自测 402 `SAME=402/MOVED=0/ERR=0`、电池 `SAME=19`、
金丝雀 `SAME=4`。主代理**未复测**，也不把「行为中性的清理」与「会改产物字节的行为补丁」混进
同一次落地（否则 G5 的 `MOVED` 集合同时混有两类原因）。作为 R66 独立清理轮移交，门禁写死为
「产物 402 支逐字节相同」。

## D. 合并集的单变量实测（落地前）

`mkfinal65.py m65 <trytail> <r65d5_ab> <d3_c1> <n1>` ⇒ generator 4 edits +260 行、analyzer 1 edit
+29 行，**链式 anchor 唯一性全通过**（四批互不重叠）；`mbuild65.py m65 …` 建 `mirr_m65`
（generator `e0cf887ecb74` / 3 123 069 B，analyzer `9fd4618b7bd2` / 1 727 576 B）。

| 名单 | 读数 |
|---|---|
| 18 支 partial | `SAME=12 IMPROVED=4 REGRESSION=0 MOVED=2 ERR=0`，`files fully matched a=0 b=1` |
| 402 支 A/B | `SAME=396 IMPROVED=4 REGRESSION=0 MOVED=2 ERR=0`；`files fully matched a=384 b=385` |
| 产物逐字节 | `identical=396 changed=6 unresolved=0`；变化集 = klinedata、graph、两支 common_func、trade_live_broker、quote（= `IMPROVED`∪`MOVED`） |
| 指令缺口 | `Σ|orig-decomp| 545 -> 418`；`matched functions 5689 -> 5693` |
| 电池 19 项 | `IMPROVED r63_ft4 1/2 -> 2/2`、`SAME=18`、`REGRESSION=0` |
| 金丝雀 4 支 | `SAME=4`（sha 逐支不变） |
| 严格尺 18 支 | 合计 `700 -> 706`，逐文件缺陷集取差：FIXED 6 项、**NEW 0 项**（klinedata `get_kline_by_date_new`+`get_multiminute_his_data_by_date`、graph `_process_task_queue`、两支 `get_kline_time_by_section`、trade_live_broker `market_fund_transfer`） |

代价（唯一，逐字节核对过）：`quote.pyc::load_bars_from_hundsun` 缺 7 条变过冲 47 条。原始 code
object 的日志常量只出现 **1 次**，落地产物里那条压平的 f-string 已经出现 **两次** ⇒ 重复发射是
R64 遗留，C1 只是把重复项从裸 f-string 放大为完整 `debug(...)` + 其后 3 条语句。同支
`get_price`/`load_get_price` 分别收窄 40/31 条，`quote` 严格尺两臂同为 74/89。

## E. 落地与串行门禁

1. `land65.py land --spec=m65_region_ast_generator.py.json --mirror=mirr_m65 --apply`
   与 analyzer 同法 ⇒ `replay == measured mirror bytes: OK`，工作树
   `3103668 -> 3123069`（CRLF 50409、BOM=True、裸 LF 0）与 `1725369 -> 1727576`（CRLF 27664、无 BOM）。
2. `closeout65.py landproof mirr_m65` ⇒ **33 个 core 文件 same=33 diff=0**（门禁跑在被落地的字节上）。
3. G1 `single site-packages/IQCommon/graph.pyc` ⇒ `ok 31/31 100.00%`，`missing_in_decomp=[]`、`extra_in_decomp=[]`。
4. G2 `single quotation.pyc` ⇒ `ok 143/143`；`single market_time.pyc` ⇒ `ok 10/10`。
5. G3 `batch --index pyc_index.json --all --round 65` 复跑 ⇒ 402 verified / ok 385 / partial 17 / failed 0。
   **首跑** 有 3 支 `RuntimeError: Failed to decompile`（`IQCommon/common/__init__.pyc`、
   `IQData/enumerate.pyc`、`IQData/fly_enum.pyc`），同字节下 `h62.py run` 读出 1/1、14/14、1/1 且
   产物 `compile()` 通过、`single fly_enum.pyc` 亦 `ok 1/1`、复跑 `failed=0` ⇒ 判为 `batch` 路径的
   一次性失败（未定位，移交 R66）。发布数字取复跑。
6. G4 `stats` ⇒ `total_functions 5746`、`matched_functions 5693`、`99.08%`。
7. G4′ `strict_repo65.py g4prime.txt`（18+4 支，读仓库产物）⇒ 合计 **915/994**，22 份产物
   `mirror-sha … =measured`（无一 `!=measured`）；`graph` 34/34、`quotation` 148/150 且缺陷集
   逐字未变、`market_time` 10/10、`quote` 74/89。
8. G5 = §D 的 402 A/B 与产物逐字节比对。
9. G6 `closeout65.py battery landed`（落地字节）⇒ 19 项 matched **62/68**、全清 **15**、
   worse-than-landed **0**（`r63_ft4` 由 1/2 变 2/2；`probe_r63b2_cases` 7/9、`r63b5_w1` 1/2、
   `r64d5_contsink` 1/2 为已知同族残余）。
10. 索引核对：`git diff --numstat pyc_index.json` = 411/411 行（逐条目字段更新，无结构性重写）；
    402 条目无增删；改动产物恰 §D 的 6 支 `*OK.py`，`git status --porcelain -- site-packages`
    非 `*OK.py` 行为空（未手改任何生成文件）。

## F. 本轮暴露的仪器问题

1. **子代理 150 轮上限**：6 批里 3 批（diag2/3/4）中断，其中 2 批零报告。集中验证方必须能只靠
   dump 重建结论——`h62.py ab` 的 jsonl 记录（`arm|path` 续跑键）足以复现全部判定，这是本轮没有
   丢批次的原因。下轮简报须继续把「边测边写 FACTS」列为硬任务，并把可用预算压到
   「靶 + 电池 + 金丝雀」三件事上。
2. **名单完整性断言缺失**：`diag1/dump/wide_*`（C.1）与 `diag0` 开工时 `targets.txt`（前一轮已记）
   都是 `find` 出来的名单，均未经存在性/语料成员校验。中心侧 `all402.txt` 402 行、与索引逐条
   对齐，是唯一的语料真值；任何「爆炸半径」结论必须先证明名单 = 语料。
3. **`batch` 的一次性 `Failed to decompile`**（E.5）：`stats` 在复跑前不可信。建议 R66 给
   `scripts/pyc_batch_verify.py` 的失败分支加上异常类型/traceback 落盘（当前只留一行
   `RuntimeError: Failed to decompile <path>`，无法区分「返回假」与「超时」）。
4. **`arm=landed` 语义在落地后即改变**：落地后任何 `--arm=landed` 读数代表 R65 而不是 R64，
   §A 的 402/402 逐条一致是**落地前**取的，两列已分别存档为 `a402_landed.jsonl` / `a402_m65.jsonl`。
