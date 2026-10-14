# Round 5 · FIX_LOOP_EXIT —— `exit=` 交付假设实测：既非充分也未被消费 ⇒ 字节级回滚

轮次：Round 5 / 破口 = 共享根（FIX_A_FAMILY §5.1 臂尾外提 + FIX_B117 §6.1 站点 21080/5186）。
判定尺：唯一判据 `scripts/pyc_verify.py`（全程未改、未替代）。
插桩：全部临时探针在 `D:/Temp/rrv5/`（probe1.py / probe2.py / hunks.py），生产代码终态已回滚。

**结论标记：「仅归档 spec 未落地」**。
**语料翻转：0**（`realtime_event_source` 12/13→12/13、`profiler_func` 17/18→17/18、`strategy` 26/27→26/27）。
合成臂翻转：0（`r4_probe_index` 终态 71/81 单元、27 success / 10 failure，与入轮逐位相同 ⇒ 交付物 4 不执行）。

---

## 1. 假设 (H1)「`exit=` 交付是共享根」——实测否决：未被消费，且改不了任何读数

### 1.1 结构事实（grep 核实，非推断）

```
grep -rn "\.exit\b"  core/cfg/code_generator.py        → 0
grep -rn "\.exit\b"  core/cfg/region_ast_generator.py  → 0 个直接读取点
grep -rn "'exit'"    core/cfg/region_ast_generator.py  → 1 处：24620 getattr(anc,'exit',None)
                     （[R2-B107] `_b107_...` 祖先汇合身份判据，唯一的 exit 消费者）
class Region:  exit: Optional[BasicBlock] = None   （region_analyzer.py:208，字段存在）
LoopRegion(… ) 构造点 = region_analyzer.py:5186，实参不含 exit（工单假设成立的那一半）
```

⇒ 发射器（`region_ast_generator` / `code_generator`）**不读 `region.exit`**；补上 `exit=` 只能被
[R2-B107] 的祖先汇合判据看到，看不到「臂尾该落在哪里」。假设的机制链（「emitter 看不见出口 ⇒ 把循环后的语句
材料化到错误位置」）在第一环就断：**没有 emitter 消费该事实**。

### 1.2 试改与读数（E3：`region_analyzer.py:5186` 加 `exit=natural_exit`）

| 靶 | 基线 | E3（叠加在 E1 之上）实测 | 翻转 |
|---|---|---|---|
| `realtime_event_source` `clock_worker` | 12/13 | 12/13（序列差量仍 −4） | 无 |
| `profiler_func` | 17/18 | 17/18 | 无 |
| `r4_probe_index` 37 臂 | 71/81 · 27/10 | 71/81 · 27/10（逐位） | 无 |

⇒ **H1 判定：不是根。** 既非必要（E1 单改 21080 就能把 −102 收窄到 −4，全程未交付 exit），
也非充分（交付后零读数变化、零消费点）。若将来要走这条路，**必须与「消费 exit 的发射点」同批落地**，
单点交付属 `rules.md` §6.4 与 REVIEW §6.1 点名的 vestigial 形态（算了不用）。

## 2. 实测到的真·臂尾根（两种形态，同一个名字：臂尾归属/位置，不是成员认领）

### 2.1 形态 A（语料 `clock_worker`）：or-ext 臂语句段能被交付，但链汇合块取成了外层汇合

重放 FIX_B117 §2 的配方（E1 = 新增 `_or_extension_arm_block_run`：候选集 = 宿主 elif 链首臂成员，
自臂首块沿正常后继（剔 `exception_successors`）闭包，按 `start_offset` 升序；站点 21080 由
`blocks=[7668]` 改为该序列）。**复现成功**：

```
persist_flag 出现次数 0 → 3        产物 realtime_event_sourceOK.py:276 起 `if persist_flag is False:` 段就位
指令序列差量  −102 → −4            （orig 1280 / prod 1276）
整段 delete orig idx[1054:1154]（100 条）不再出现
```

剩余**真**分歧（其余 replace hunk 为 −128/±2 位移伪影，按 rules §5.2 豁免）：

| # | orig | prod | 机制 |
|---|---|---|---|
| 1 | idx[667] off5612 `POP_JUMP_FORWARD_IF_FALSE → 9214`（函数尾 sink） | off5614 → 9082 | 短路出口边落点被换成臂内汇合块 |
| 2 | **delete idx[841:857]**（off6690 起 16 条 = `if holiday_not_do_before == '0': put(BEFORE_TRADING_START)`） | 同一段被发射在**臂外**（OK.py:312，dedent 一级） | 链的臂尾跳边 `6652/6680 JUMP_FORWARD 6690` 在 prod 变成 `JUMP_FORWARD 9066`（= orig 9194 外层汇合）⇒ 内层链的汇合块身份被取成**外层**汇合块，尾随语句段被外提为兄弟 |
| 3 | replace idx[935:941]（off7268 起 7 条 = `system_log.debug('获取重登信号量')` 段） | 同段消失/前移 | 同 #2 的第二处臂尾 |

⇒ `clock_worker` 的翻转需要**「链汇合块 = 本层顺序续流块」**这一条（A 族 B100/B110 轴）与 E1 并轨；
E1 只解决「有没有语句段」，不解决「语句段落在哪一层」。FIX_B117 §6.2 的「两票并轨」判定成立。

### 2.2 形态 B（合成臂 a07 族）：`while` 宿主的臂尾被注册成幻影 loop-else

用 probe1.py（build_cfg + RegionASTGenerator，只读）测 `r4v3_a07_no_or_control` 的 `<module>.f`：

```
LoopRegion entry=4 exit=None merge=None
  body_blocks = [4,22,136,148,160,176,186,188,224,240,250,252,288,304,314,320]
  else_blocks = [52,192,256,316,350]      ← 幻影：52=第一臂体、192/256/316=各臂尾跳转桩、350=回边块
  back_edge_block = 350      blocks ⊇ else_blocks
CFG: blk4 'x' in ACCTS 的假边 → 350（350 末条 JUMP_BACKWARD→4，即本循环 continue/回边桩）
     臂尾 52/192/256/316 全部以 JUMP_FORWARD→350 汇入该桩
```

站点实名：`region_analyzer.py:4810-4845`（`_find_loop_else` 返回之后的 `if condition_block == header
and not else_blocks:` 分支）。它把「header 假边落点 = 本循环回边桩」这一形态的**汇入该桩的臂尾块**
整批收为 `else_blocks`，并 `body = body - _else_backedge_set`，同时置 `natural_exit = _hdr_jump_target`
（= 桩自身，一个在循环之内的块）。后果正是 FIX_A_FAMILY §5.1 登记的读数：
`if chained: break … sleep(60); sleep(60)`（臂体尾外提成 `break`，语句段材料化到循环之后）。

试改（E2 = 删除该分支，桩与臂尾块留在 body 内由其所属 IfRegion 发射）实测：

| 靶 | 基线产物 | E2 产物 | 读数 |
|---|---|---|---|
| `r4v3_a07` | `while 'x' in ACCTS: … break …` + 循环后两条 `sleep(60)` | `break` 消失、两条 `sleep(60)` 回到臂内（形态部分复原），但出现 `while not 'x' in ACCTS:` 条件反相、`if not '09:00:00': continue` 伪语句、末臂 `pass` | 1/2 → **1/2（未翻转）** |
| `r4_probe_index` 37 臂（E1+E2） | 71/81 · 27/10 | 71/81 · 27/10（逐位） | 0 翻转 |
| `realtime_event_source`（E1+E2） | −102 | **−4**（与 E1 单改同值 ⇒ E2 在本语料不触发，其宿主非该形） | 12/13 → 12/13 |

⇒ 形态 B 是**真病灶之一**（它确实负责 a07 族的 `break` + 循环后语句），但单独改它 0 翻转，
且改后暴露出同分支的第二层依赖（`natural_exit` 被 `_detect_break_continue`(:4891) 与 R58/R102
break 验证消费；桩留在 body 后 header 假边的角色判定改判为「条件取反」）。
**下一手必须成对处理：else_blocks 不认领 + 回边桩的 continue 语义交付**，否则只是把一种形变换成另一种。

## 3. A 族语料「链 walk 上游截断」的实测更正

FIX_A_FAMILY §5.2 记「`strategy`/`api_base`/… 的 or-run 成员对根本没走到 LoopRegion 认领守卫
（链 walk 在更早分支即 break）」。用 probe2.py（sys.settrace 只跟
`RegionAnalyzer._detect_boolop_conditional_chain` 的 code object，记录每次调用的末行与结果长度）
在**终态回滚前的 E1+E2+E3 代码态**实测 `strategy.pyc::Strategy.tick_worker_thread`（26/27）：

```
calls 30（该函数体内全部条件块）
  entry@512   lastline=-30099 resultlen=2   ← 或链建成（2 名成员），正常返回点
  entry@982   lastline=-30099 resultlen=2   ← 同（#3 的 off992/1004 那一族）
  entry@350/536/552/612/628/642/658/718/734/748/764/822/1006/… lastline=-29747 resultlen=0
                                            ← 29747 = `if len(chain) < 2: return None`（单条件 if，本就无链）
```

⇒ **链 walk 没有上游截断**：`strategy` 的两条 or-run（成员对 @512、@982）**都建成了 2 成员链**
（与 a07 的 `entry@136 resultlen=2` 同一条成功返回路径 30099）。A 族语料与合成臂一样，
失败点都在**建链之后**：区域汇合块身份（本文 §2.1 #2）与发射位置，不在 walk。
a07 的 walk 读数同为成功（`entry@136 → resultlen=2`），两条曲线在此完全重合 ⇒ A 族与臂尾根是**同一根**。

## 4. 标记 · True-hits vs flips

| 试改 | 标记 | True-hits（实测） | flips |
|---|---|---|---|
| E1 `_or_extension_arm_block_run` @21080 | `[R5-B117-armrun]` | 1 次调用 / 1 次多块交付（`clock_worker` 臂序列 23 块，7668→8590 段就位） | **0**（12/13 不变；差量 −102→−4） |
| E2 删除 `region_analyzer.py:4810-4845` 幻影 else 认领 | `[R5-B117-armtail]` | 1 次命中（a07 形态：`break` 与循环后 `sleep(60)` 消失） | **0**（37 臂逐位不变；反相/伪 continue/pass 新形变暴露） |
| E3 `exit=natural_exit` @5186 | — | 0 次读数变化（发射端零消费点） | **0** |

合成臂 True-hits 0 flips；语料 True-hits 2 flips 0 ⇒ 按硬验收线整批回滚。

## 5. 门禁读数（终态字节实测原文；产物一律先删后 `pycdc.py` 重生成，无手改）

```
single realtime_event_source   12/13   （重生成后复判）
single profiler_func           17/18   （重生成后复判）
single strategy                26/27   （重生成后复判）
batch round4/r4_probe_index    71/81 单元  files 27 success / 10 failure / compile_error 0 / error 0   STAY
batch round1/r1_probe_index   108/110 单元  files 44 / 2                                              STAY
batch round1/r1_regress_index  34/34  单元  files 17 / 0                                              STAY
batch round2/r2v3_probe_index 105/126 单元  files 41 / 21                                             STAY
batch round3/r3_probe_index   101/122 单元  files 35 / 21                                             STAY
pytest 6 套件                   2 failed / 277 passed / 2 xpassed（仍 test_B01_simple_if_then_else_merge、
                               test_BOUNDARY_02_large_function）
import core.cfg.{region_analyzer,region_ast_generator,code_generator} OK；compileall -q core OK
未跑：402 语料八分片批（按工单由主代理持有）。
```

pin 复判（代码态 = 入轮逐位字节态，判据直接判在盘产物；与入轮基线逐条相同）：

```
quotation 152/153（失败单元仍 <module>.get_fundflow_day）· handlers 29/30 · trading_dates_mixin 14/14
stock_position 37/37 · cgroup_utils 8/8 · email_utils 4/4 · calexrights_func 8/8 · future_contract 29/29
fly/logger 64/64 · ptradeAccount 137/137 · fly/data/quote 86/92 · trade_info_utils 37/41
trade_live_broker 118/128 · strategy 26/27 · api_base 27/28 · matcher 16/17 · finance 31/32
bar 84/85 · function 70/71          —— 19 条全部 = 基线，无一下跌、无一下涨
```

## 6. 回滚 · 字节完整性 · 插桩残留

```
core/cfg/region_analyzer.py      2045409 bytes / \n 32167（行数 32168）/ 前导 BOM 1 / CRLF 32167 / bare LF 0 /
                                 sha256[:16] = 2a7517c61b083449
                                 与入轮备份（D:/Temp/rrv5/bk/region_analyzer.baseline.py）**逐字节相同**（比较 = True）
core/cfg/region_ast_generator.py 3684310 bytes / \n 58668（行数 58669）/ BOM 1 / CRLF 58668 / bare LF 0 /
                                 sha256[:16] = ab05c4c6bb9da904   （= 工单事实，两处试改逐字符撤回）
core/cfg/code_generator.py       未触碰
ast.parse 两文件 OK
标记复验（core/cfg/ 三文件合计，与入轮逐条相同）：
  [R2-B106] 4 · [R2-B107] 7 · [R2-B108] 5 · [R3-B115] 1 · [R3-B109] 3 ·
  [R4-B116 sinkexit] 4 · [R5-B100-armjoin-trueentry] 4
插桩残留 grep（python 计数，core/ + scripts/ + test_repros/ 全量 .py）：
  R5-B117 → 0 · _or_extension_arm_block_run → 0 · armrun/armtail → 0 · exit=natural_exit → 0   合计命中 0
临时脚本 probe1.py / probe2.py / hunks.py / bk/ 全部在 D:/Temp/rrv5/，生产目录零新增文件。
禁止前缀命名新增方法 0；硬编码深度/数量上限 0；文件名·函数名·偏移特判 0；文本后处理 0；抑制式发射 0。
```

**附带修复（非生产代码）**：本轮执行既有标本生成器 `test_repros/round4/_r4v3gen.py`（31 臂规格）时，
它把 `r4_probe_index.json` **重写为 31 条**（丢 FIX_A_FAMILY 追加的 a15/a16/a17 等 6 条）。已按盘上
`r4v3_*.pyc` 实存 37 个复原索引为 37 条 `{"path": …}`（与既往同 schema、同排序），复跑读数
`units_total=81 / 71 success / 27 files / 10 files` **与入轮记录逐位相同** ⇒ 索引等价复原，无单元增减。

## 7. 收窄后的残余（下一票最窄表述）

1. **翻转所需最小并集已实测成对**：E1（21080 臂语句段交付，−102→−4，`persist_flag` 就位）
   \+「链汇合块 = 本层顺序续流块」（§2.1 #2/#3 三处真分歧：off5612→9214/9082、
   off6652·6680 `JUMP_FORWARD 6690` 被取成 9066、off7268 段）。任一半单独落地都只得「命中未翻转」。
   下一手 = 在 `_check_elif_chain` / `_if_generate_elif_chain` 的 merge 求解侧补「本层顺序续流块优先于
   祖先汇合块」的结构判据（只读块末 opcode、后继/前驱、成员关系），与 E1 并票交付。
2. **`exit=` 路线判死（本轮实测）**：发射端不消费 `Region.exit`（唯一读者 = [R2-B107] 祖先汇合判据），
   补字段 0 读数变化。若要走 C2「子区域只经 entry/exit 接口被消费」的正解，必须**先在发射端建立
   exit 消费点**（例如循环区域作为抽象节点交付给宿主臂时，宿主臂据 exit 决定「出口之后的同臂顺序段」
   归属），再谈交付；两者必须同票，否则复现 §6.1 的 vestigial 形态。
3. **a07 族的幻影 loop-else（§2.2）是第二个独立可翻面**：`region_analyzer.py:4810-4845` 把汇入本循环
   回边桩的臂尾块收为 `else_blocks` 并摘出 body。删除后 a07 的 `break`/循环后 `sleep(60)` 消失但
   暴露 header 假边角色反相（`while not 'x' in ACCTS`）⇒ 必须与「回边桩 = continue 语义交付」同修。
   6 条臂 + （很可能）`api_base`/`matcher`/`finance`/`bar`/`function`/`load_daily` 的
   `while` 宿主形都卡在这对上；这是 A 族语料**唯一**已被实测改动过产物形态的站点。
4. **`profiler_func` 不属本族**：E1 站点 calls=0（FIX_B117 §3 同判），E2 对它无影响，读数 17/18 逐位不变
   ⇒ 按工单要求不强行并轨，留在册。
5. **walk 侧无需再动**（§3 实测更正）：A 族语料的 or 链建成正常，成员对未被 LoopRegion 认领守卫命中
   并不等于 walk 截断；FIX_A_FAMILY §5.2 的「下一站点在 walk 侧」应撤销，改判为「建链之后的汇合身份侧」。
