# Round 4 · FIX_ELIF_HOST —— or-run 完整性（Step A）＋ 条件区域层的 elif 链宿主选择（Step B）

结论标记：**「仅归档 spec 未落地」**。生产代码已按入站字节逐字节复位（§6），五套电池、
12 个 pin、pytest、import/compileall 与基线逐位相同。

**flips 计数 = 0**（语料文件读数无一改善；r4 臂无一 MISMATCH→MATCH；未向索引追加永久臂）。

判定尺唯一 = `scripts/pyc_verify.py`（全程未改、未替代）。

---

## 1. Step A 检查点（配方复用，实测命中）

配方来自 `FIX_ORRUN.md` §2 的 5 个 hunk，按 patch1→patch2→patch3→patch6→patch7 顺序重放
（跳过 patch4/patch5，即 §4.1 已排除的「op_chain 保留 4 名 + 阻止修剪」形）。

`IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc <module>.Strategy.tick_worker_thread`
（探针 `D:/Temp/rrv4/probe_ccg.py`，monkeypatch 只读，不改生产码）：

| 检查点项 | 基线（入站实测） | Step A 态 | 配方预测 |
|---|---|---|---|
| `_detect_boolop_conditional_chain(off512)` | `[(512,'or'), (524,'or')]` | `[(512,'or'), (524,'or'), (536,'and'), (552,'and')]` | ✔ 一致 |
| BoolOpRegion(entry off512).blocks | `[512, 524]` | `[512, 524, 536, 552]` | ✔ 第二 leg 不再是无主块 |
| BoolOpRegion(entry off512).merge_block | off568（两名成员的公共真边） | **off612** | ✔ 解析到 run 的假出口 |
| R14c 整链取反 `elif not (A or B):` | 发射 | 消失，发射 `elif A or B or '11:30:00' < dt_strf < '12:30:00':` | ✔ |
| 该单元 first_diff（`_r4v3_diag diff`） | idx 73：off522 `IF_TRUE→568` vs prod `→820` | idx 40：`(348, POP_JUMP_FORWARD_IF_FALSE, 822)` vs `826`，且 target-content 签名两侧相同（位移伪影）；orig 270 / prod 254（−16） | 前进但仍不闭合 |
| `strategy` 读数 | 26/27 | **26/27** | 与配方 §2 表一致（0 flips） |

**Step-A 检查点命中**（run 成员齐、merge=612、链式比较腿不再自成 IfRegion）。

## 2. Step B：宿主选择的实测根（不是配方 §4.4 的猜测形）

Step A 之后区域事实（probe 原文）：

```
基线   IfRegion(entry off350) elif_conditions=[]      elif_bodies=[[552..820 共22块]]
StepA  IfRegion(entry off350) elif_conditions=[off512] elif_bodies=[[552,562,564,568,612,628,…,820 共22块]]
```

即 run 完整后，**512 这一臂仍把紧随其后的 elif 串（612/642/…）整段吞进臂体**。
临时插桩（`[R4-DBG*]`，只读打印后已撤除）给出确切失配点：

```
[R4-DBG] hdr=350 else0=512 cond=536 then=536 elseS=564 merge=1286 nThen=21   ← StepA 基线态
[R4-DBG] hdr=350 else0=512 cond=552 then=562 elseS=612 merge=1286 nThen=2     ← 本票 B1 后
[R4-DBG2] recurse cond=512 elseBlocks=[612, 628, 640, 638, 674, 642, …, 820]
[R4-DBG] hdr=512 else0=612 cond=612 then=628 elseS=640 merge=1286 nThen=17
[R4-DBG3] recurse cond=612 res=None
```

根因两层，都在 `region_analyzer._build_elif_region` 的内嵌 `_check_elif_chain`：

1. **臂头 run 的「尾名」被取错**（可修，本票已修并实测生效）：
   `inner_condition_block = inner_br.op_chain[-1][0]` 取的是 op_chain 末位，而链式比较
   按「每名操作数一条」修剪后末位 = 第一条 leg（536），它的两条边都不触及 run 出口；
   于是臂体从第二 leg（552）起算、run 出口 612 被当臂体收集。
   修形 = 新增 `_boolop_run_terminal_member(bor)`，在本区域自身的 `blocks` 内沿
   `conditional_successors` 前进到「短路边即 merge_block」的真正末名（536→552）。
   实测：`cond=552 then=562 elseS=612 nThen=2`、`elif_conditions=[off512, off612]`、
   512 臂 body = `[562, 568..610]` ✔ 512 这一臂的宿主正确。
2. **链式比较臂自身的尾名/极性无解**（本票未能修好，见 §3）：612 处不是 BoolOpRegion
   （`_detect_boolop_conditional_chain(612) = None`，两 leg 假边经清理桩传递、真边 IF_TRUE），
   走的是 `_check_elif_chain` 的内联 `and` 链扩展，该扩展在 21683 `if 'IF_TRUE' in
   _ft_last.opname: break` 处收手 ⇒ `inner_condition_block` 停在 612，`sorted()` 取
   `then=628 / else=640`，臂体从条件腿 628 起算并越过假出口吞掉 642 之后的整条链。

## 3. 两个被实测否决的 Step-B 候选形（勿重复）

* **形 β（清理桩按正常后继判定）**：`_fe_is_cleanup` 的 `len(first_else.successors) == 1`
  改为排除 `exception_successors`。判据本身成立——640 是 `[POP_TOP]` 纯值桩、在 try 区内，
  第二条后继是 handler off1290，故桩没被跳过、递归 `return None`。
  **实测后果**：递归虽推进到 642，但 612 臂 body 仍含 642 的块（同一批块被双重认领），
  产物退化——`tick_worker_thread` 的 `try: while True: …` 整段消失（只剩
  `accounts = …`），单元读数仍 26/27 但结构剧退。**否决并撤除**。
* **形 γ（内联链接纳链式比较第二 leg ＋ 极性换边）**：在 21683 处按「本名跳转目标为纯值
  清理桩」放行 IF_TRUE 腿入链（`inline_boolop_chain=[612,628]`），并在
  `inner_then_succ, inner_else_succ = sorted(...)` 之后按尾名极性交换两条边。
  **实测后果**：链边界修对了（612 臂 body 与 642 的下一 elif 分离），但 elif 内联条件发射
  把链式比较拆成两个独立操作数，产物出现
  `elif '08:30:00' <= dt_strf and not '08:59:00':` / `if '09:00:00': pass`
  一类**操作数错接**（与 `FIX_ORRUN.md` §4.1 被排除的「generator 重复计入 `'12:30:00' and
  '12:30:00'`」同一失效族）。`inline_boolop_chain` 的消费端无链式比较还原能力
  （链式比较只在 `IfRegion.chained_compare_ops` / BoolOpRegion 路径上还原）。**否决并撤除**。

结论：本簇的第二个根**不在认领侧单点**，而在「链式比较臂的条件发射」侧——
`elif` 的内联条件重建与 BoolOpRegion 的 `chained_compare_ops` 重建是两套代码，
前者不认第二 leg。这需要在生成端 `_if_generate_full_elif_chain`
（`region_ast_generator.py:18757 _if_generate_elif_chain` / :19110 / :19620 三处
 `op_chain[-1][0]` 与 `inline_boolop_chain` 消费点）为内联链补链式比较还原，
 属新票范围；本票未落地。

## 4. True-hit vs flips（本票标记）

| 标记 / hunk | 命中实测 | flips |
|---|---|---|
| `[R4-ORRUN-CCG]`（Step A 5 hunk，配方复用） | strategy：hunk1×2、hunk2×2、hunk4×1、hunk5×2（与 `FIX_ORRUN.md` §3 同）；api_base / matcher / bar / function / strategy_universe / load_daily：0 | **0** |
| `[R4-ELIF-HOST]` 形 α `_boolop_run_terminal_member` | 1 处判真（strategy off512 臂），区域事实实测改变（`elif_conditions` `[off512]`→`[off512, off612]`，body 22 块→2 块） | **0**（该单元仍 26/27，首分歧仍在链式比较臂 612） |
| `[R4-ELIF-HOST]` 形 β 清理桩后继判定 | 判真≥1（递归推进到 642） | **0**，且结构退化 ⇒ 撤除 |
| `[R4-ELIF-HOST]` 形 γ 内联 leg ＋ 极性换边 | 判真≥1（612 臂边界修对） | **0**，条件文本错接 ⇒ 撤除 |

api_base / matcher 的前驱证据（`_r4v3_diag blocks`，形 α 态实测原文）：

| 块 | ORIG preds | PROD（入站基线，`FIX_JOIN_IDENTITY.md` §3） | PROD（形 α 态，本票实测） |
|---|---|---|---|
| `off1040` | `[18, 21]` | `[21]` | **`[21]`（未复原）** |
| `off1098` | `[17, 20, 22]` | `[20, 22]` | **`[20, 22]`（未复原）** |

即 A+B 对本票四主靶的前驱塌缩**均无修复**：Step A 的 CCG 判别式在 api_base/matcher 上
本就不命中（`FIX_ORRUN.md` §3 实测 hunk1 命中 0），形 α 只在 strategy 的 512 臂判真。
臂跳转目标 `568→820`（strategy off522）与 `1038→1286`（off1004）在形 α 态：512 臂的
成员真边已落回 568 侧（首分歧从 idx 73 移到 idx 40 的位移伪影），但 612 臂起
后续链的边差未闭，单元仍红；api_base/matcher 两处目标逐字不变。

## 5. 全部读数（复位后实测原文）

```
batch round4/r4_probe_index     51/67   files 15 success / 16 failure        （= 基线）
batch round1/r1_probe_index    108/110   files 44 / 2                          （STAY）
batch round1/r1_regress_index   34/34   files 17 / 0                            （STAY）
batch round2/r2v3_probe_index  105/126   files 41 / 21                           （STAY）
batch round3/r3_probe_index    101/122   files 35 / 21                           （STAY）
single strategy.pyc   26/27 · api_base.pyc 27/28 · matcher.pyc 16/17
       bar.pyc 84/85 · strategy_universe.pyc 10/11 · load_daily.pyc 26/27
       fly/common/function.pyc 4/4（本票次靶读数与入站逐位相同）
pin：quotation 152/153（失败单元仍 <module>.get_fundflow_day）· cgroup_utils 8/8 ·
      email_utils 4/4 · calexrights_func 8/8 · future_contract_info 29/29 ·
      fly/logger 64/64 · ptradeAccount 137/137 · fly/data/quote 86/92 ·
      trade_info_utils 37/41 · trade_live_broker 118/128 · handlers 29/30 ·
      trading_dates_mixin 13/14      （全部 = 基线，无一跌）
pytest 6 文件：2 failed / 277 passed / 2 xpassed（仍
      test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function）
import 三模块 OK；python -X utf8 -m compileall -q core OK
```

7 个被重生成过的语料产物（strategy / api_base / matcher / bar / function(fly/common) /
strategy_universe / load_daily）均以「删除 + `python -X utf8 pycdc.py -o <base>OK.py <pyc>`」
用**复位后的代码**重新生成，无任何手工编辑，读数回到上表基线值。
r4 索引 31 条臂的 `*OK.py` 全程未重生成（未追加永久臂，理由同 §4：0 flips）。

## 6. 字节核验（复位后）

| 文件 | 字节 | 行数 | BOM | 行尾 |
|---|---|---|---|---|
| `core/cfg/region_analyzer.py` | **2030385**（= 入站，逐字节相同） | **31979** | 恰好 1 | 全 CRLF（CRLF=31978=LF 计数，bare LF=0），`ast.parse` OK |
| `core/cfg/region_ast_generator.py` | **3684310**（未触碰） | **58669** | 恰好 1 | 全 CRLF（58668），`ast.parse` OK |
| `core/cfg/code_generator.py` | 未触碰 | — | — | — |

标记核验：`[R4-ORRUN-CCG]` = **0**、`[R4-ELIF-HOST]` = **0**、`[R4-DBG` = **0**、
`_boolop_run_terminal_member` = **0**（形 α/β/γ 全部撤除，不留零命中守卫）；
必须存活的原标记实测：`[R2-B106` 4、`[R2-B107` 7、`[R2-B108` 5、`[R3-B115` 1、
`[R3-B109` 3、`r3-b100-armjoin` 8。

## 7. 归档件（下一票可直接取用）

1. **形 α 是可落地的半件**，其判据与新方法 docstring（六项 ①算法依据 ②归约顺序
   ③唯一归属判定 ④嵌套处理 ⑤入口引用语义 ⑥反编译流程 ＋ C1/C2/C3）见本节末「判据文」；
   它单独 0 flips，但与「内联链链式比较还原」成对时是本簇的必要条件——保留判据、勿重新发现。
2. **下一手（生成端，非认领端）**：`elif` 的内联 `and` 链消费点
   （`region_ast_generator.py:19110` / `:19620` / `:23854` 三处
   `op_chain[-1][0]` 与 `inline_boolop_chain`）不具备链式比较还原能力；
   形 γ 实测发射 `'08:30:00' <= dt_strf and not '08:59:00'`。
   最小 repro（须同时钉两件事）：
   ```python
   if A: body0
   elif B or C or ('11:30:00' < x < '12:30:00'): body1   # Step A：or-run 完整
   elif '08:30:00' <= x < '08:59:00': body2              # Step B：链式比较臂，
   elif '12:30:00' <= x < '12:59:00': body3              #   其后继 elif 必须挂同层而非臂内
   ```
   必须钉住的区域事实：`off612` 两 leg（612 IF_FALSE→清理桩 640、628 IF_TRUE→臂体 674）、
   清理桩在 try 区内带异常后继 off1290（`successors`=2 而 `exception_successors` 占其一）。
3. **形 β 的教训**（认领侧单独收紧边界必然退化）：只推进 elif 递归、不修臂 body 边界，
   会双重认领同一批块并使产物丢整段 try；两者必须在同一票内成对落地。
4. api_base / matcher 两靶的 `[18,21]→[21]` / `[17,20,22]→[20,22]` 前驱塌缩与本票判据
   **无交集**（Step A 的 CCG 判别式在它们上 0 命中），应另立「非链式比较形的 or-run
   臂认领」子根，勿并入本簇。

### 判据文（形 α，归档未落地）

`_boolop_run_terminal_member(bor)`——沿本区域自身 `blocks` 取 run 末名：
①当前名短路边不是 `bor.merge_block`；②其另一条 `conditional_successors` 仍是
`bor.blocks` 成员；③未在 seen 内。三条任一不成立即停机返回当前名；
`op_chain` 空时退回 `bor.entry`。只读终结子 opcode、后继/异常边归属、本区域 blocks 与
merge_block 身份（[C1] 同层结构事实；C2 纯查询不写字段；C3 保守弃权）。
唯一归属证据只用**本区域自身**的 blocks，不向祖先链取证（承 `[r1-b98-elsescope]` 教训）；
终态判定用 merge_block 身份而非后穷尽（承 `[r3-b103-armjoin-termexit]` 教训）。
