# Round 10 裁定：工单 #16（B126）判据**成立但零翻转**→ 按 sha256 逐字节回滚，补丁作为 #13 的必带共要件移交

裁定时点：2026-10-08 主代理自有复测封盘。**回滚不是否证**：本档同时登记该判据被正面证实的三件事，
以及它为何不能单独落地。二者分开记，不得合并成一句「失败」。

## 一、回滚凭据（字节级）

| 文件 | 回滚后工作树 sha256 前 12 | 应等于 | 判定 |
|---|---|---|---|
| `core/cfg/region_analyzer.py` | `38a1d5142d13` | Round 8/9 封表值 `38a1d5142d132fd7…` | ✓ |
| `core/cfg/region_ast_generator.py` | `e9a8f65f6451` | Round 9 落地值 `e9a8f65f6451bcc8…` | ✓ |

（`git show HEAD:` 的 blob 哈希另为 `b3ed95868d2b` / `1304bbea3643`——差在 CRLF 归一，非内容差。）
在飞工作树字节已先行保存：`D:/Temp/r9main/WIP_R10_B126_analyzer.py`（`515da6c6e1a21f76…`，与回滚前逐字节相同）
与补丁 `D:/Temp/r9main/RAVED_R10_B126.patch`（288 行，标记三族：
`[r10-b126-else-backedge-refute]`、`[r10-b126-whiletrue-ifjoin]`、`[r10-b126-loopheader-tail-confluence]`）。
回滚后重生成受影响 3 产物并复验：`trade_live_broker 118/128`、`finance 32/32`、`function 71/71` ⇒ 语料回到封表态。

## 二、主代理自有复测（不采信工程师自述；工程师在 150 回合上限截断，§二「判据实现」一节留空）

### 二A 复现臂电池：判据**有效**

`test_repros/round9/r9w16_probe_index.json`（18 臂：11 复现 + 6 对照 + 1 意外对照），
产物一律删除后由 `pycdc.py -o` 重生成（`ok=18 bad=0`）：

| 态 | units | success/failure 文件 |
|---|---|---|
| HEAD 基线（`D:/Temp/r9w16/base.json`） | **26/37** | 7 / 11 |
| WIP（主代理自有 `D:/Temp/r9main/w16_mainverify.json`） | **33/37** | 14 / 4 |

转绿臂 7 条：`01_bare_tail`、`02_break_in_arm`、`03_continue_in_arm`、`04_multi_arm_join`、
`08_while_in_while`、`10_class_method_ctx`、`12_after_join_stmts`。
**BROKE＝0**：6 条对照臂（含真 `while…else`、真 `while…else`+break、`for…else: continue` 桩、
`else` 体是嵌套 while、`else` 桩 continue 跳**外层 for** 头）全部保持绿。
⇒ 判据方向正确、不过度收紧；残余 4 条红臂为更深嵌套（`05/06/07/11`）。
（注：工程师自己的 `after2.json` 读 30/37，主代理复测读 33/37——差 3 单元是它截断前又推进了一版，
不计为读数矛盾。）

### 二B 语料 402 八分片双门禁：**零翻转、零回退**

| 步 | 读数 |
|---|---|
| 402 重生成 | 8 片 `ok=51×7+45=402`、`bad=0` |
| batch verify | units **6577/6617 → 6577/6617**，files success **386 → 386** |
| 逐文件 units 差 | `UNIT_REGRESSIONS=0`、`UNIT_IMPROVEMENTS=0` |
| 逐单元名集差 | 翻正 **0** 条、新增失败 **0** 条 |
| 产物变更面 | `git diff --stat` 显示仅 **1** 个语料产物变化：`trade_live_brokerOK.py`（167 行）；`finance/function` 两条是 Round 9 落地产物未入库之差 |

### 二C 变更内容确为真源形状

`while True:` 计数：HEAD 产物 **2** → WIP 产物 **5**；三条目标行的头部
`while len(self.open_orders) > 0:` / `while len(self.pending_cancel_orders) > 0:` /
`while self.trade_status != trade_status:` 在 WIP 产物中**已不再作为循环头出现**，
即简报 §二（本机 3.11.7 复演的 B2 形状）的改判**在语料字节上确实发生**。

## 三、为何仍判回滚（纪律而非情绪）

本轮每张工单简报都写死了同一条：**零翻转即按 sha256 逐字节回滚**（B122 否证、B123 零翻转已立此例）。
B126 与 B123 的差别要说清：B123 是「判据命中而产物不动」，B126 是「产物动了而单元不翻正」——
后者动的 167 行只是**结构改判**，这三单元各自还压着 **#13 的巨额省略**
（`_process_order` 少 465 条、`_process_cancel_order` 少 293 条、`_trade_status_handle` 少 3 条），
所以相等性判定必然仍红。**单列落地即成为「有行为、无单元收益」的挂账改动**，
而语料门禁是唯一的封表凭据。按同一条尺子处理，尺子才不会因为下次改动看起来顺眼就被弯一弯。

## 四、移交：#13 的必带共要件（不得重复推导）

`FIX_OMISSION_R10_BRIEF.md` 的 LOSS_COLLAPSE 名单里有三条正是被 #16 挡住的单元。
故 **#13 派发时须先应用 `D:/Temp/r9main/RAVED_R10_B126.patch`**，再在其自有判据面上作业，验收要求写死：

1. 共要件应用后先复跑 `r9w16_*` 索引，读数须不低于 **33/37 且 BROKE=0**（防 #13 的改动把 #16 的判据挤掉）；
2. `trade_live_broker` 的三条单元须**逐名**翻正才记 #13 的成绩；
   若 #13 只补回省略而 `while True:` 改判未应用，这三条依旧不翻正——**两票共担，禁止任一票单独记功**；
3. #13 落地后 402 门禁仍由主代理自有跑，`REGRESSIONS=0 ∧ UNIT_REGRESSIONS=0` + 逐单元名单为准。

## 五、流程缺陷登记（同 Round 9 那条同源，本轮再现）

工程师在 150 回合上限截断，`FIX_B126_WHILE_TRUE_IFJOIN.md` 的「二、判据实现」与结果一节**空白**，
本轮已按「先建回报、边做边写」派发（其 §〇/§一/§一B 确实在早期落盘，比 Round 9 的 0 字节回报好），
但仍未写完 ⇒ **回合预算不足是排产问题，不是工程师问题**：
下一票派发改为**更窄的靶面**（#13 先只做 P0 一条：`matcher.DefaultMatcher.match` 的单条被吞测试语句），
并把共要件应用与复测并入同票，以免再次在门禁前耗尽回合。

## 附：#13-P0（B128）工程师同型截断的裁定（2026-10-08 19:16）

**结论：本票零落地、零取证记录，树仍为封表字节。**

| 检查项 | 实测 |
|---|---|
| `git status -- core/` | **空**（`region_analyzer.py = 38a1d5142d13…`、`region_ast_generator.py = e9a8f65f6451…` 均等于封表值） |
| 落地标记 `[r10-b128…]` | grep 命中 **0** |
| 回报「§一 进度日志」六个复选项 | **全部未勾**（既未写丢弃点，也未写「 ruling out」） |
| 电池臂 | 磁盘上 7 枚 `.pyc` 臂可用（`r10ls_01/02/04/05` 复现 ＋ `c1…c6` 对照），索引 `r10ls_probe_index.json` 14 条**不含**产物文件 |
| 其基线读数 `D:/Temp/r10ls/final_base.json` | **不可信**：`files=28` 而索引只 14 条，行内同时出现 `X.pyc` 与 `XOK.pyc`（把产物当输入跑了），表头 `units=33/16` 自相矛盾 |
| 其末句自述 | 「Anchor sentinel 454/454. Running the remaining sentinels.」——报的是 HEAD 态哨兵，非改后读数 |

⇒ **不需要回滚**（无生产改动），但也**没有任何一单元翻正**：本轮至今仍 386/402，`≥1 pyc 转 success` 未达成。

**流程诊断（三轮连续截断的共同因）**：我给工程师的票面把「定位缺陷 ∧ 建 ≥10 臂电池 ∧ 实现 ∧ 复测 ∧ 哨兵 ∧ 写回报」
压在同一个 150 回合预算里，违背 spec 自己的「测试工程师→修复工程师→主代理验证」串行分工，
也违背我自己的既有教训（一个代理不得同时诊断与修复）。B126 靠截断前边写回报留下了可裁定的判据，
B128 连这个都没有。

**对策（已生效）**：把 #13-P0 拆成两票——
① **纯诊断票**（现已派出，禁改 `core/`、禁 git 写、最多 4 个小复现、边写 `DIAG_B128_MATCHER_DROPSITE.md`），
   交付物＝丢弃点的 `文件:函数:行` ＋ 误发条件（白名单事实表述）＋ 是否静默豁免；
② **实现票**：拿到①的结论后只写判据与跑门禁，不再自己找宿主。
后续票（#14/#15/#21/#22/#23/#24）一律按此两段式派。
