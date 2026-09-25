# Round 64 — OUTCOME

## 1. 本轮形态

20 支 partial 按缺陷函数数排序后分 5 批（diag1-diag5）由 5 个只读诊断代理并行诊断，各自在
私有工作区 `D:/Temp/opencode/r64gate/diag{1..5}` 建臂实测，再由主代理集中验证与回退。
本轮与 R63 的差别是：五个批次里只有 diag1/diag2/diag4 交出了可落地的机制性判据，diag3 的两个
候选在全量 A/B 上被证伪，diag5 的四个臂全部实测无增益。

批次起点排序（`logs/rank20.txt`）：只差 1 个函数即可全绿的有两支——
`realtime_event_source` 11/12（`clock_worker` [1275,1286,10,481] 过冲）与
`matcher` 16/17（`match` [715,715,10,517] 纯顺序问题）。

## 2. 修到完全 OK 的 pyc（本轮 mandate：至少一支，实测两支）

| pyc | 轮初 | 轮末 | 依据 |
|---|---|---|---|
| `site-packages/IQCommon/common/main.pyc` | partial 29/33 87.88% | **ok 33/33 100.00%** | 官方 `single`（G1）+ 严格尺 **34/34**，且轮初缺失的 3 个嵌套 code object（`get_same_shard_server_ip_info.<dictcomp>`、`get_server_ip_info.<dictcomp>`、`get_server_ip_info.<lambda>`）全部回来 |
| `site-packages/fly/data/quote_handler.pyc` | partial 55/57 96.49% | **ok 57/57 100.00%** | 官方 `batch` 条目 55→57、`decompile_status` partial→ok；严格尺 68/72→69/72（残余 3 项在 `get_index_stocks_local`/`get_industry_stocks_local`/`get_kline_local`） |

两支都由工具链重写 `*OK.py`，未手改任何生成文件。

## 3. 落地集（13 处编辑，全部先对 R63 落地字节单变量实测）

```
core/cfg/region_ast_generator.py  3 086 600 -> 3 103 160 B  12 edits +208 行
                                  BOM 保留，CRLF 50 145，裸 LF 0，sha c6c6a7dd69ab3ff64b8b
core/cfg/region_analyzer.py       1 721 959 -> 1 724 219 B  1 edit  +35 行
                                  无 BOM，CRLF 27 625，裸 LF 0，sha 9b5cae3ce5a96bc39eec
```

`land63.py land --spec … --mirror … --apply` 逐条重放：replay == 实测镜像字节；
`closeout64.py landproof mirr_full2` ⇒ 33 个 core 文件 same=33 diff=0。

**收尾追加（三要素注释补全，纯注释、已实测字节中性）**：

```
core/cfg/region_ast_generator.py  3 103 160 -> 3 103 668 B  1 edit +4 行注释
                                  BOM 保留，CRLF 50 149，裸 LF 0，sha c9099bb0fc3527e5b552bdc590066cab2d103343f6edca3d6a1c97a74a79bc4a
core/cfg/region_analyzer.py       1 724 219 -> 1 725 369 B  1 edit +10 行注释
                                  无 BOM，CRLF 27 635，裸 LF 0，sha 24a88392ee61f31f5882a4dedb7f1b62cc16533ebc4909152e67b9c3ea77d107
```

逐行 diff 证明这两处只插入注释（insert_blocks=1 / delete=0 / replace=0，非注释插入行 0），
落地后 15 支改动产物与金丝雀 (sha, mism) 与 `full2` 逐支相同、电池读数不变（细节见 EVIDENCE §H）。
下表行号一列是**实现代理 spec 中锚点相对落地前文本的位置**；引用代码时请用最终字节上的标记行：
generator `[R64-b2]` L14360、`[R64-B2]` L21189/L41570/L41624/L41669、`[R64-D4-B]` L32990、
`[R64-B1 sibling merge-entry dispatch]` L33174、`[R64-D4-A]` L49989；analyzer
`[R64-diag1 closed-shared-exit-prefix]` L25558。

| 落地行号 | 标记 | 来源 | 识别条件 / 归约方式 / AST 映射（摘要，全文在代码注释里） |
|---|---|---|---|
| L14370 (+42) | `[R64-b2]` 值栈消费者判据 | diag2 c2 | 条件语境里被链式比较消费的块不再作为三元值块吸收 |
| L21221 (+33) | `[R64-B2]` 让位契约兑现侧 | diag2 c1 | 放弃发射的嵌套区域不得继续认领成员块 |
| L32979 (+1)、L32995 (+24)、L33074 (+4) | `[R64-D4-B]` | diag4 b | 汇合块首条有效指令是 `POP_TOP` ⇒ 短路链的值在语句边界被丢弃，`Expr(BoolOp)` 与下一条 `Assign` 分两条平级语句发射 |
| L33192 (+31) | `[R64-B1 sibling merge-entry dispatch]` | diag1 c1 | 同层次结构身份（`r.entry is region.entry or region.parent is r`）下的兄弟汇合入口分派 |
| L41002 (+29)、L41075、L41566 (+5)、L41617 (+7)、L41672 (+7) | `[R64-B2]` FORMAT_VALUE 回填 | diag1 c2 | f-string 层三元结果的 `FormattedValue` 槽位表与消费点回填 |
| L49990 (+25) | `[R64-D4-A]` | diag4 a | `_try_deferred_return_in_loop` 丢弃的块前缀在 `len(_r64d4_pre) >= 2` 且产物全为 `Assign\|AugAssign\|Expr\|Return\|Delete` 时经 `_generate_stmts_from_instrs` 复原，否则退回 `return [_ret]` |
| analyzer L25594 (+35) | `[R64-diag1 closed-shared-exit-prefix]` | diag1 kbin | `_detect_boolop_conditional_chain`：算子 run 已在唯一汇出块 T 闭合，而 current 两条边都不到 T 且 current≠T ⇒ `chain.pop()`，current 自成新 IfRegion 入口 |

禁止形态核查：13 处编辑全部为同层次结构身份判据，无 `region.entry in r.blocks` 型跨区域跨层次
包含、无按函数名/文件名/偏移/阈值的启发、无把 `self` 当帧内临时变量的新增状态。
diag1 特别标注其 c1 中最宽的一支是 `region.parent is None` 析取，保留理由是实测零回归（402 与电池）。

## 4. 门禁（严格串行，全部实测；每条命令 <300 秒）

| 门禁 | 读数 |
|---|---|
| G0 语法 | 两文件 `py_compile` + `ast.parse` OK；BOM/CRLF 形态保持（裸 LF 0） |
| G1 `single` 靶 | `IQCommon/common/main.pyc` → decompile_status ok，33/33，100.00%，missing/extra 皆空，`mainOK.py` 由工具链重写（22 110 字符） |
| G2 金丝雀 | `fly/data/quotation.pyc` 官方 **143/143 100.00%**；严格 **148/150**，缺陷集逐字未变（`change_his_to_forward` #250、`get_trend` #10）；`market_time` 10/10；两支 `datetime_func` 26/26、25/25；三支严格 **61/61** |
| G3 `batch --index pyc_index.json --all --round 64` | 402 verified、**ok 384、partial 18、failed 0**、5689/5746、99.01% |
| G4 `stats` | 与 G3 同读数（轮初 5677 / 98.80%、ok 382、partial 20） |
| G4′ 严格尺（本轮 11 支改动产物） | 函数级 **480 → 492 / 537**；文件级全清 2/11（`main` 34/34、`crypto_utils` 9/9） |
| G5 全量 A/B（落地前镜像 vs 轮初） | IMPROVED=8 REGRESSION=0 MOVED=3 SAME=391，产物改动脉络 11/402 |
| G6 电池（落地字节，19 项） | matched 49 → **61**，全清文件 7 → **14**，worse-than-landed **0** |

## 5. 附带改善与残余（如实记录）

附带改善（官方尺，逐支）：`graph` 29→30/31、`common_func` 18→19/21、`api_base` 23→24/25、
`scheduler` 42→43/45、`logger` 28→29/30、`trade_live_broker` 104→105/119。
严格尺另见 `crypto_utils` 7/9→9/9（官方两臂都 9/9，属官方尺看不见的修复）。

MOVED 三支（计数不变、产物变化）已逐支归属：

* `crypto_utils.pyc` 与 `klinedata.pyc` 同源于 analyzer 那一条 `chain.pop()` 判据；前者严格尺
  由 7/9 变 9/9（真修复），后者 `get_multiminute_his_data` [479,478,3,16]→[479,478,5,16]、
  严格 56/63→54/63，**是本轮唯一实测代价**，采纳理由是该判据同时带来 `quote_handler` 55/57→57/57
  与严格 +1；`att_sib`/`att_fv` 两臂独立复核确认 diag1 的生成器编辑没有触碰这两支。
* `risk_calculation/__init__.pyc` 的 `get_TradeMode_trades` [1839,1753,4,1620]→[1839,1801,4,1617]
  （缺口 86→38，来自 diag2 c2），官方计数与严格函数数都不变。

残余 18 支 partial 清单见 `logs/partial18_after_r64.txt`。

## 6. 移交下一轮的线索

1. `realtime_event_source :: clock_worker` [1275,1286,10,481]：diag1 Job 3 实测产物把
   `elif check_trading_time(...)` **发射两次**（`OK.py` 第 275 与 312 行），原字节码只有一个调用点
   （@8594）。约 +110 指令的重复臂插入与约 −100 指令的 @6690 丢失互相抵消，所以「+11 过冲」这个
   净数没有意义——真正要找的是 elif 链分派（`_if_generate_normal` / R61 通道）的**重复发射**。
2. `matcher :: match` 仍是 16/17，第二处缺陷是 orig[180:462] 共 282 条指令整体投到产物尾部
   （decomp 428..713）而 `if self._volume_limit:` 占了前槽——顺序问题，不是归属问题
   （见 memory `project-r64-matcher-displacement-lead`）。
3. `flyAccount :: _do_request` [436,443,2,384] 过冲 +7 未动，站点仍在
   `_loop_build_if_with_exit_branches`。
4. `get_kline_binary` 的 closed-shared-exit 判据本轮只收窄到「前缀闭合于同一 T 且 current 两边
   都不到 T」；`klinedata` 的 De Morgan 形态（`if fq is None or dividends_all is None or …`）
   被它改写后 jumpdiff 3→5，R65 应加一条「被 pop 的块自身就是 or-run 首块时不 pop」的同层判据再测。
5. 技术债：`region_ast_generator.py` 里残留 **10 处 `import os as _os_dbg_*`** 调试导入
   （L32916、L44320、L46899、L47059、L47107 等），行为中性但是垃圾代码；须用「产物 402 支逐字节
   相同」作门禁单独清理。

## 7. 归档

`rounds/round64/`：`OUTCOME.md`（本文件）、`batches/diag1-5/`（每批 FACTS/ANALYSIS + specs +
dump + 选录 logs，含被拒臂与实测理由）、`logs/EVIDENCE.md`（集中验证全记录）、
`logs/gate/`（G0-G6 原始输出）、`logs/`（四份中心记录 + 列表文件）、`specs/`（合并后的
落地 spec 与中间集）。最小复现入库 `test_repros/round64_diag{1,2,3,4,5}/`（仓库惯例只入库 `.py`，
`.pyc` 被 .gitignore 排除；电池实跑前用 `py_compile` 现编）。
