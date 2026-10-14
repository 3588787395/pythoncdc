# Round 6 · FIX_B120 —— 无条件循环头 NOP 落点块归属（G-A / G-B 同轴裁决）

判定尺：唯一判据 `scripts/pyc_verify.py`（全程未改、未替代；interp 3.11.7 64 位）。
靶文件 `site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc`，
10 失败单元中的 **6 个 B120 形**（G-B：`_process_order` / `_process_cancel_order` / `_trade_status_handle`；
G-A：`_process_tick_order` / `rzrq_credit_order` / `get_ipo_stocks`）。
插桩全部在 `D:/Temp/rrv6/`（`b120_probe.py` 真机管线循环头/区域读数 / `dump_cfg.py` 逐块 CFG /
`probe_units.py` 逐单元 hunk），**生产目录零新增脚本、生产文件零写入**。

**判定标记：「仅归档 spec 未落地」** —— 两个症状组经真机管线读数证实**不在交办站点
（`region_analyzer.py:4881 / :4891 / :5221 / :5234`）构成可翻转的归属判据**：其一（G-A）
区域模型已正确、残留只是 CPython 行锚落点的单跳偏移；其二（G-B）头块被上游 loop 分析器
折叠、交办站点看到的是恒等输入（B121 同型伪证）。True-hits = 0、翻转 = 0，按硬性验收规则
不予落地。`region_analyzer.py` / `region_ast_generator.py` 本轮**从未被编辑**（终态 sha 与入轮
备份逐字节相同，见 §5），「byte-exact revert」平凡成立。

---

## 1. G-A 与 G-B 是否共享一条归属规则？—— 裁决：**不共享可落地的同一条规则**

交办假设「一条 loop-header/back-edge 归属规则同时解释两组」**被真机读数否证**。两组根因不同：

### 1.1 G-B（`_process_order`）：外层 `while True:` 头块 @44 被**上游折叠**，交办站点是恒等输入

真机 `get_all_loops()` 读数（`b120_probe.py _process_order`）：

```
LOOPHEADERS _process_order
  hdr@46  n=9  backsrc=[360, 620, 682, 850, 1362, 1576, 3128]  bodysize=62   ← 唯一被登记的 header
```

⇒ `get_all_loops()` **不含 @44**。CFG 里 `blk@44 n=1 NOP preds=[0,360,620,682,850,1362,1576] succ=[46]`
（外层 while True 的 NOP 行锚认领块，体内 6 条 continue 落它）在 **loop_analyzer 回边归一化阶段**
就被折进 @46：6 条 continue + 尾 sink 3128 全部被登记为「@46 的回边源」。因此 region_analyzer 在
`:4847 back_edges_for_header = [src for src,tgt in back_edges if tgt==header]` 处**根本看不到 @44**，
`:4881 max(...)` 与 `:4891 _detect_break_continue(natural_back_edge=…)`、`:5221/:5234` 的
`back_edge_block` 选择，其候选集恒为 {360,620,682,850,1362,1576,3128}，@44 无从参与。
**在交办站点做任何 tie-break 推广都作用在这份「已折叠」输入上 ⇒ 恒等变换（B121 §3 同型伪证）。**

产物后果（`OK.py:423-495`）：`_process_order` 被拍平成单一 `while len(self.open_orders) > 0:`（对应 @46），
外层 while True 消失，其 `break` 被外提到体内首语句前（`OK.py:429`），CPython 3.11 不可达消除删掉其后
整段（`dis` 实测覆盖行集 `[423,424,425,426,427,428,429,495]`），orig 520 → prod 42（−478）。
`_process_cancel_order`（−304）、`_trade_status_handle`（NOP@44 整块消失、−4）同因。
**真正需要改的是 `core/cfg/loop_analyzer.py` 的回边归一化（不折叠承载 continue 落点的 NOP 行锚头块）**，
而非交办点名的 `region_analyzer.py`；而 header/回边选取「每个循环都走」（交办明示），任何全局回边
重划几乎必然击穿 quotation 之外的其它循环 pin（cgroup / ptradeAccount 137 / fly.logger 64 …）。

### 1.2 G-A（`_process_tick_order`）：区域模型**已正确**，残留是 CPython 行锚落点单跳偏移

真机读数（`b120_probe.py _process_tick_order`）：`get_all_loops()` **含** hdr@114 与 hdr@130（嵌套），
且最终区域表**已生成独立内层 LoopRegion**：

```
FINAL REGION HEADERS _process_tick_order
  LoopReg entry@114 hdr@130 is_while_true=False back_edge=724   ← 内层循环独立成区，header/back_edge 正确
  LoopReg entry@46  hdr@46  is_while_true=True  back_edge=1132  ← 外层 while True
  LoopReg entry@46  hdr@60  ...
```

CFG：`blk@130 n=8 preds=[114,178,724] succ=[178,180] last=POP_JUMP_FORWARD_IF_FALSE 180`，
`blk@178 preds=[130] succ=[130]` ⇒ `@130↔@178` 自环 = 内层 while；@178 是体内 `continue` 块。
唯一真分歧：orig `@178 JUMP_BACKWARD → @130`（体内首语句/行锚块），prod `→ @114`（测式块），
指令多重集与顺序逐位相同（delta=0、bare-token hunk=0，仅 1 个跳目标异）。
⇒ **这不是 原则2 归属失败**（@130 已唯一归属到内层 LoopRegion、header/back_edge 无误）：
重建出的 Python `while self.before_trading_start:` 里 `continue`（`OK.py:503`）由 **CPython 编译器**
决定回边落到测式 @114 还是体内行锚 @130。要把这一跳对齐到 @130，需复刻 CPython 的行锚放置，
等价于**逐 offset/发射形**凑数（instant rejection：offset 特例 / 文本后处理 / 抑制发射），
不是任何「块终端 opcode + 前驱/后继 + 区域归属」白名单判据能表达的唯一归属守卫。
`rzrq_credit_order`（`@2368 JUMP_FORWARD` orig@2534 vs prod@2506）、`get_ipo_stocks`
（`@1108 POP_JUMP_FORWARD_IF_TRUE` orig 汇合@1154 vs prod 回边@1130）同为 delta=0、恰一条落点跳，
同属此行锚/汇合落点极性，而非认领归属缺失。

**合并裁决**：G-B = 认领归属真缺陷，但根在 loop_analyzer（交办点恒等）；G-A = 归属已正确，
残留不可用白名单归属判据消除。两组**非同一可落地规则**。按交办「若为两规则，只落能证明的那一条」——
两条均不能在 `region_analyzer.py` 交办站点落地，故本票不落地。

---

## 2. 6 个 B120 单元的 before→after（未编辑 ⇒ 逐单元恒等）

| 单元 | 组 | 首分歧 | orig/prod（before） | after（=before，无改动） |
|---|---|---|---|---|
| `_process_order` | G-B | 删 o@44 NOP（+@92 EXTENDED_ARG+体蒸发） | 520 / 42（−478） | 520 / 42（**仍失败**） |
| `_process_cancel_order` | G-B | 删 o@44 NOP | 344 / 40（−304） | 344 / 40（**仍失败**） |
| `_trade_status_handle` | G-B | 删 o@44 NOP+首语句 | 130 / 126（−4） | 130 / 126（**仍失败**） |
| `_process_tick_order` | G-A | `@178 JUMP_BACKWARD` 130↔114 | 188 / 188（1 跳） | 188 / 188（**仍失败**） |
| `rzrq_credit_order` | G-A | `@2368 JUMP_FORWARD` 2534↔2506 | 786 / 786（1 跳） | 786 / 786（**仍失败**） |
| `get_ipo_stocks` | G-A | `@1108 POP_JUMP_IF_TRUE` 1154↔1130 | 497 / 497（1 跳） | 497 / 497（**仍失败**） |

**无任一单元改善、无整文件翻转。** 未归 B120 的 4 单元（`_sync_worker` G-E、`etf_basket_order` G-D、
`etf_purchase_redemption` G-F 常量面、`ipo_stocks_order` G-C）本轮**未触碰**。

---

## 3. 全部门禁读数（生产文件未编辑 ⇒ 恒等基线；已真机锚定 3 项）

- `pyc_verify single trade_live_broker.pyc` → **118/128**（真机复跑，锚定）。
- `pyc_verify batch r6_probe_index` → 34 文件 / 73 单元，**25 MATCH / 9 MISMATCH**（真机复跑，锚定）。
- `pyc_verify single fly/data/quotation.pyc` → **153/153**（真机复跑，锚定，未回退）。
- r1_probe / r1_regress / r2v3 / r3 / r4 五个 batch：因 `region_analyzer.py`+`region_ast_generator.py`
  **sha 逐字节等于基线**（§5），所有代码路径未变，读数**按恒等等于交办所列基线**：
  108/110(44/2)、34/34、105/126(41/21)、101/122(35/21)、77/87(30/10)。
- pin 抽查前提（loop-header 选取触及每个循环）：quotation **153/153**（真机锚定）；其余 pin
  （cgroup 8/8、email 4/4、ptradeAccount 137/137、fly.logger 64/64、stock_position 37/37 等）
  因源码未编辑，逐字节恒等基线，无过冲风险（未编辑 ⇒ 不存在 over-reach）。
- pytest / compileall / import：源码未改 ⇒ 基线 277 passed / 2 failed（同两例）/ 2 xpassed；import+compileall 无新增。

---

## 4. 标记与残根

- 8 条 marker 真机复核（`grep -c`，生产文件未改，恒等）：
  `[R2-B106]`=4、`[R2-B107]`=7、`[R2-B108]`=5、`[R3-B115]`=1、`[R3-B109]`=3、
  `[R4-B116 sinkexit]`=4、`[R5-B100-armjoin-trueentry]`=4、`[R5-B119 loopsink]`=3。全部符合基线。
- **True-hits = 0 / flips = 0**（未在交办站点落地任何可命中守卫；命中数为 0 因根本未写守卫）。
- 残根 grep 0：未新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 命名、
  无硬编码深度/计数/语句上限、无函数/文件名/offset 特例、无文本后处理、未复活 `Region.exit`、
  未读 `_trailing_rn_exit_count`、未重议 B121 推广。

---

## 5. 字节 / sha 事实（before = after，未编辑证明）

```
core/cfg/region_analyzer.py       2052197 B / 32266 lines(splitlines) / 1 BOM / 全CRLF / sha256=0212c54e4d0c790e…
core/cfg/region_ast_generator.py  3685863 B / 58685 lines(splitlines) / 1 BOM / 全CRLF / sha256=9c36c741bd972593…
```
入轮备份 `D:/Temp/rrv6/region_analyzer.py.bak` sha=`0212c54e4d0c790e5cb68b4bdd09b6d66b167e315d0b0d4de630bfda6e1774a9`；
终态实测 sha=`0212c54e4d0c790e…`（同前缀，逐字节相同）。**「byte-exact revert」平凡成立——不存在需回滚的改动。**
（`trade_live_brokerOK.py` 按交办用 delete+`pycdc.py` 重生成，未手改；重生成后 single 复验 118/128 与基线一致。）

---

## 6. 收窄后的残差（下一手方向，非本票落地）

1. **G-B 唯一真根在 `core/cfg/loop_analyzer.py` 的回边归一化**：不折叠「承载 body continue 落点的
   纯 NOP 行锚头块」（@44 类），使其作为独立自然循环 header 进入 `get_all_loops()`，再交回
   `region_analyzer.py` 认领。风险：header 选取全语料共用 ⇒ 必做 wide pin sweep。本票因交办站点
   （`region_analyzer.py`）对此恒等、且越界改动 blast radius 巨大而未尝试，登记为候选轴。
2. **G-A 行锚落点单跳（@114 测式 ↔ @130 体内首语句）**：属 CPython 行号锚放置语义，非 原则2 归属；
   若要消除需表达式/语句级发射形对齐，禁以 offset/文本凑数。登记为发射形轴，不属认领归属轴。
