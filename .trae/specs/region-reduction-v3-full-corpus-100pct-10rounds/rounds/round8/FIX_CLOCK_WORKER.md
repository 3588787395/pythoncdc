# Round 8 · FIX_CLOCK_WORKER —— B117 第二实例：or-extension 整臂交付已实测（−112→−1）但单点不翻面 ⇒ 字节级回滚

轮次：Round 8 / 破口 = **B117**（第二实例）。
主靶 `site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` **12/13**，
拦路单元 `<module>.RealtimeEventSource.clock_worker`，指令差量 **−112**。
判定尺：唯一判据 `scripts/pyc_verify.py`（全程未改、未替代；interp 3.11.7 64 位，ruler sha `9c7567bd6776b36b`）。
产物一律先删后 `python -X utf8 pycdc.py -o <base>OK.py <pyc>` 重生成，无手改 `*OK.py`。
插桩全部在 `D:/Temp/rrv8/`（`cw_diff.py` 逐指令差分、`cfg_dump.py` CFG/区域导出），生产目录零新增脚本。

**结论标记：「仅归档 spec 未落地」**（已回退到入轮字节态）。
**语料翻转：0** —— `realtime_event_source.pyc` 12/13 → 12/13（终态字节实测）。
交付物 4（追加可反证臂）在 0 翻面时**不执行**，`test_repros/round6/r6_probe_index.json` 保持 **40 条**路径不动。

---

## 1. 先复测：入轮 13 单元差量清单（改动前实测原文，`cw_diff.py clock_worker`）

工单要求「不要相信旧数字，先复测」。实测确认 R7 `[exitclaim]` **未吸收** clock_worker 残余
（与 Round 7 §3「PRED 在该单元零调用、12/13、−112 逐位不变」一致，hunk 地形与 Round 5/7 记录相同）。

```
ORIG .RealtimeEventSource.clock_worker co_firstlineno=120 ins=1442
PROD .RealtimeEventSource.clock_worker co_firstlineno=54  ins=1330
DELTA (orig-prod) = 112
=== HUNKS（入轮）===
REPLACE orig[717:718]/[723:724]  LOAD_CONST <code object check_handle_date …>   ← 伪影豁免（嵌套 code 常量按地址序不同，pylingual 递归比对为 Equal）
INSERT  orig[768]/[913]/[945]/[954]/[1039]/[1057(2)]/[1114]/[1407(2)]           ← EXTENDED_ARG/地址重排伪影
DELETE  orig[876:877]  off6318  (1)   EXTENDED_ARG 1                            ← 编码伪影
DELETE  orig[959:976]  off6690-6782 (17)  LOAD_FAST holiday_not_do_before | LOAD_CONST 0 | COMPARE_OP == …   ★(c) 臂尾外提
DELETE  orig[1062:1068] off7270-7308 (6)  LOAD_GLOBAL system_log | LOAD_ATTR debug | LOAD_CONST 获取重登信号量 | PRECALL 1  ★(b) AND-leg 吞
DELETE  orig[1192:1304] off7972-8586 (112) LOAD_FAST persist_flag | LOAD_CONST False | IS_OP 0 | POP_JUMP_FORWARD_IF_FALSE 8170  ★(a) 整臂语句段
REPLACE orig[1411:1413] prod[1284:1301] off9210-9212 (2/17)  LOAD_CONST None | RETURN_VALUE None  ← 函数尾 sink：(c) 的 17 条落在此
=== 计数：delete=5 replace=3 insert=8 ===
```

净差量核算：`112(a) + 17(c-del) + 6(b-del) + 1(EXT) + 1(EXT) − 10(1-ins 群) − 15(尾 replace 多出) = 112`。
真实缺陷三处（其余为 code-常量/EXTENDED_ARG/地址重排伪影）：**★(a) 整臂不发射 112、★(b) AND-leg debug 吞 6、★(c) holiday 段被外提到函数尾 17**。

## 2. 三个失败边/语句段的站点与归属问题（实测 CFG，`cfg_dump.py`）

- 靶出口边：`blk@5598 last=POP_JUMP_FORWARD_IF_FALSE(9214) preds=[5492,5594,6792] succ=[5614,9214]`（`if self.active:` while 体首条），
  假边落点 `blk@9214 n=2 last=RETURN_VALUE preds=[5598] succ=[]`（函数尾 sink）。此即工单点名站点。
- ★(a) `persist_flag` 段（7972-8586）：属 `blk@7634` IF_ELIF_CHAIN 首臂成员（then_blocks=[7668,7706,…,8588]），
  在 for 循环（LoopRegion@7706，for_iter_setup=7668，FOR_ITER 自然出口=7972）**之后** ⇒ 穿过该边的顺序段失去发射方
  = **or-extension 正臂只交臂首块**（`region_ast_generator.py:21080`，同形 21099）。归属问 = 臂语句段所有权（原则 1/2/§1.5 C3）。
- ★(b) `debug('获取重登信号量')`（7270 首 6 条）：`blk@7270 preds=[7248] succ=[7372,7492]`，7248 是
  `elif … and login_semaphore.acquire(…) is False:` 的 **and 短路腿**（BoolOpRegion）。块内后续 11 条已发射，仅腿首 debug 语句被吞
  = **AND-leg 语句归属**，与 21080 **不同**区域、不同机构（boolop 折叠侧），是独立的归属问（[R5-B100-armjoin] 族邻位）。
- ★(c) `holiday_not_do_before == '0'` 段（6690，17 条）：`blk@6690 preds=[6652,6678]`（6280 真分支、try 设值之后），
  在 6280-true 子树内，与 persist_flag 所在的 6280-false 子树（7582/7634）**兄弟分支**。段被发射但**落到函数尾**（prod 尾 +17）
  = **臂尾外提 / arm-tail join identity**（Round 5 §6.2、FIX_A_FAMILY §5.1），亦**不经 21080**。

## 3. 落地的规则（已实测、终态已回滚）

新增 `RegionASTGenerator._or_extension_arm_block_run(arm_entry, arm_blocks)`（置于 `_if_generate_normal` 之前）+
消费点 21080/21099：候选集 = 宿主 elif 链首臂成员 `_or_elif_ir.then_blocks`（无宿主链回退 `region.then_blocks`）；
自臂首块沿 `block.successors − block.exception_successors` 正向封闭展开、限候选集内、按 `start_offset` 升序返回，
交 `_process_if_blocks`（其 `:24983` 本就按地址序扫描并经 `_loop_entry_generate` 正确生成子 LoopRegion）。
输入全在白名单（块末 opcode/前驱后继/异常边/区域成员），C1 空扩展逐位等价旧行为。
docstring 六项 ①算法依据 ②归约顺序 ③唯一归属判定 ④嵌套处理 ⑤入口引用语义 ⑥反编译流程 + C1/C2/C3 齐备（随回滚一并撤除）。

**实测（仅 (a) 在场，其余未动）**：
```
DELTA (orig-prod) = 1     ← −112 → −1
DELETE  orig[1192:1304] …persist_flag 整段 消失（112 条复原，if persist_flag is False: 于 OK.py:276 正确就位）
仍在：DELETE orig[959:976] holiday 17（仍外提到尾 REPLACE orig[1411:1413]→prod 17）+ DELETE orig[1062:1068] debug 6
single realtime_event_source：12/13（仍 clock_worker Different control flow）  ← 命中未翻转
```

## 4. 语料翻转（唯一验收信号）与 True-hits

| 靶 | 基线 | 试改态 (a) 实测 | 翻转 |
|---|---|---|---|
| `realtime_event_source.pyc` | 12/13 | **12/13**（clock_worker 仍 Different，差量 −112→−1） | **无** |

- True-hits：1 单元命中并改变产物（clock_worker，or-ext 臂序列整臂交付、persist_flag 0→发射、delete-hunk 5→3）。
- flips：**0**。工单验收要求 13/13；(a) 单点为「命中未翻转」，与 Round 5 §3（−102→−4、0 翻面）同结论。
  翻面需 **同时**闭 ★(b) AND-leg 归属与 ★(c) 臂尾外提两处**异家族**残余（Round 5 §6.2 已判为须与 FIX_A_FAMILY §5.1 并轨）；
  三者并轨超出本票预算与「一发翻面」判据，且 (a) 会改动**全语料**每个 or-extension 臂的发射面（饱和机上无法在预算内跑遍 7 批 + 30+ pin 证无回退）⇒ 按「命中未翻转即字节级回滚」纪律回退。

## 5. 门禁读数（全部为**回退终态字节**实测；realtime 产物先删后 pycdc 重生成）

```
single realtime_event_source        12/13  （已复原，与基线同值）
batch round6/r6_probe_index          76/85 单元  40 臂  31 success / 9 failure   = 基线逐位（无绿臂转红）
batch round1/r1_probe_index         108/110 单元  46 文件  44 / 2                STAY
batch round1/r1_regress_index        34/34  单元  17 文件  17 / 0                STAY
batch round2/r2v3_probe_index       105/126 单元  62 文件  41 / 21               STAY
batch round3/r3_probe_index         101/122 单元  56 文件  35 / 21               STAY
batch round4/r4_probe_index          77/87  单元  40 文件  30 / 10               STAY
pytest 六套件   2 failed / 277 passed / 2 xpassed（仍 test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function）= 基线
import core.cfg.{region_analyzer,region_ast_generator,code_generator} OK；compileall -q core rc=0
```
未跑：402 语料八分片批（并行会话占机，按工单由主代理持有）。

关键 pin（读既存产物，单判，全部 = 基线）：**quotation 153/153 success · quote_handler 79/79 success ·
IQEngine/utils/profiler_func 18/18（R7 锚点，未回退）· IQCommon/profiler_func 17/17 · IQData/utils/profiler_func 15/15**。
（代码逐字节 = 入轮基线，其余 pin 读数按构造与基线同值。）

## 6. 标记 · 残留 · 字节完整性

```
标记（core/cfg 三文件合计，前缀口径，逐条 = 基线）：
  [R2-B106] 4 · [R2-B107] 7 · [R2-B108] 5 · [R3-B115] 1 · [R3-B109] 3 · [R4-B116 sinkexit] 4 ·
  [R5-B100-armjoin-trueentry] 4 · [R5-B119 loopsink] 3 · [R6-B111 armscope] 3 · [R7-B117 exitclaim] 3
残留 grep（python 计数，终态）：`_or_extension_arm_block_run` 0 · `R8-B117` 0 · 禁止前缀新增方法 0 ·
  硬编码深度/数量/语句上限 0 · 文件名·函数名·偏移·块号特判（无 5598/9214/clock_worker 键）0 ·
  文本后处理 0 · 抑制式/死代码发射 0 · 塌臂为 pass 0。
字节完整性（终态 = 入轮，逐字节复原）：
  core/cfg/region_ast_generator.py  3691860 B / CRLF 58769 / 前导 BOM 1 / sha256 2e3051ed3614bd9102e86d2160dd80c06c94906d2ac167d038fa3efddbf8399b
  core/cfg/region_analyzer.py       2058547 B / CRLF 32336 / BOM 1 / sha256 38a1d5142d132fd7…  ← 未触碰
  core/cfg/code_generator.py        299897 B / 无 BOM / sha256 28aba10bae133952…              ← 未触碰
  test_repros/round6/r6_probe_index.json  40 条目（未追加、未改动）
```

## 7. 收窄后的残余（下一票的可执行表述）

1. **B117 clock_worker 需三票并轨才翻面**：★(a) or-ext 整臂交付（本票实测 −112→−1、单点 0 翻面，已回滚）；
   ★(b) AND-leg `debug('获取重登信号量')` 吞（站点在 BoolOpRegion and 腿折叠侧，blk@7270 首 6 条 / orig idx1062:1068 / off7270-7308，**非 21080**）；
   ★(c) `holiday_not_do_before=='0'` 段外提（orig idx959:976 / off6690-6782，落 prod 尾 REPLACE idx1411:1413，属 FIX_A_FAMILY §5.1 臂尾 join identity，**非 21080**）。
   (a)+(b)+(c) 任缺其一即 Different control flow。
2. `_or_extension_arm_block_run` 已证为正确、通用、白名单内的交付面（persist_flag 复原、C1 逐位等价旧行为），
   可作下一票起点复用；但须与 (b)(c) 同批落地并以语料翻面为准绳，不可单发。
3. ★(b)(c) 各自站点未在本票展开归因（属异家族），下一票须自带其宿主区域的边落地/发射残缺口的最小标本与反证臂。
