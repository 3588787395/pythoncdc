# Round 5 · FIX_PARENT_EDGE —— 区域树「错父边」实弹复现与试改：语料 0 翻转 ⇒ 字节级回滚

轮次：Round 5 / 破口 = `FIX_PAIRED_ARMJOIN.md` §3.2 与 §7.1① 移交的命名缺陷
（`clock_worker` 的 `IfRegion@6690.parent` 被取成 `LoopRegion@5598`，按成员证据应为 `IfRegion@6548`）。
判定尺：唯一判据 `scripts/pyc_verify.py`（全程未改、未替代；ruler sha `9c7567bd6776b36b`，interp 3.11.7 64 位）。
落地文件：试改只动 **`core/cfg/region_analyzer.py` 单文件**（`region_ast_generator.py` / `code_generator.py` 零改动）；
发射端一行未碰（承「五票都在补发射端」的判词）。产物一律**先删后** `python -X utf8 pycdc.py -o <base>OK.py <pyc>` 重生成，无手改。
插桩：全部临时探针在 `D:/Temp/rrv5/`（probe5/probe6/probe7/probe8/regen_batch/pins/hunks + `bk2/` 入轮备份），生产目录零新增文件。

**结论标记：「仅归档 spec 未落地」**。
**语料翻转：0**（八靶逐位不变）。**合成臂翻转：0**（`r4_probe_index` 37 臂 / 81 单元 逐位 = 71/81、27 success / 10 failure，
零条绿臂转红）⇒ **交付物 4（追加臂）不执行**。
标记 True-hits：父边改判 **9 条边**（`clock_worker` 1 + strategy 7 + r1_42 1）/ flips **0** ⇒ 命中未翻转，整批回滚。

---

## 1. 错父边的实测证据（入轮基线，probe5/probe7 原文）

### 1.1 主靶 `site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`
`<module>.RealtimeEventSource.clock_worker`（12/13）：

```
CFG blk 6690 len=4 pred=[6652, 6678] succ=[6702, 6778, 9218] exc=[9218] last=POP_JUMP_FORWARD_IF_FALSE 6778
CFG blk 6702 len=10 pred=[6690] succ=[6778, 9218]              last=POP_TOP
CFG blk 6778 len=3  pred=[6690, 6702] succ=[6792, 9218]        last=STORE_ATTR 'before_trading_date'
CFG blk 6652 len=1  pred=[6582] succ=[6690, 9218]              last=JUMP_FORWARD 6690
CFG blk 6678 len=2  pred=[6672] succ=[6690, 9218]              last=JUMP_FORWARD 6690   ← try 臂尾桩（6672∈TryExceptRegion@6582）

基线区域树：
 IfRegion@6548  parent=LoopRegion@5598  blocks=[6548,6580,6582,6652,6690]
                then_blocks=[6580,6582,6652,6690]  else_blocks=[]  merge=6792      ← 6702/6778 不在其内
 IfRegion@6690  parent=LoopRegion@5598  blocks=[6690,6702]  then_blocks=[6702]  merge=6778   ← 命名缺陷（应为 @6548）
 IfRegion@6280  parent=LoopRegion@5598  then_blocks=[6322,…,6548,6580,6582,6652,6690,6792]
 LoopRegion@5598 在该单元出现**两个区域对象**（blocks 末 9194 / 末 9214，父子互挂）
```

成员证据结论：6690 的两条前驱（6652 直系、6678 经 `@6582` 嵌套）**全部落在 `@6548` 的 then 臂体内**，
6702 与 6778 的前驱又全部落在同一臂内 ⇒ `@6690` 的唯一父应是 `IfRegion@6548`。

### 1.2 语料靶 `site-packages/IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc`
`<module>.Strategy.tick_worker_thread`（26/27）同因复现：

```
 IfRegion@512  parent=LoopRegion@50  blocks=25  then_blocks=[536,552,562,564,612,…,820]  merge=568
 IfRegion@536  parent=LoopRegion@50  (应为 @512)  entry 536 的唯一前驱 = 524
 BoolOpRegion@512 parent=IfRegion@512  merge=568
 block_to_region[536] = TryExceptRegion@48（不是 child ⇒ `_entry_owner` 通道 31509 不生效）
```

### 1.3 根因站点（实测，非推断）

`_build_region_hierarchy` 的候选收集里，「entry ∈ IfRegion.then/else」这一**成员认领通道**（入轮 31454-31457）
确实把 `@6548`/`@512` 收进了候选集，但随后 31498-31586 的类型/区间级联把它淘汰：
31534 的 `if len(_loop_cands) >= 2: best_parent = max(_loop_cands, key=(priority, -width))`
在候选含**两个以上 LoopRegion**（本簇两例都含）时**先于任何 IfRegion 成员证据**胜出 ⇒ 臂内嵌套结构被挂成循环兄弟。
其余六靶（`api_base`/`matcher`/`finance`/`bar`/`function`/`load_daily`）未逐例探针，仅按同形（臂内 if 的父取成循环）登记。

## 2. 试改两版与门禁实测（逐位原文）

### 2.1 v1（宽判据）——复现缺陷但**打红一条绿臂**

判据：候选以 `then/else/elif_conditions/elif_bodies/elif_final_else/body/try/with` 任一清单列有 `child.entry` 即认领；
`child.entry` 全部正常前驱 ∈ 认领者成员闭包（`blocks ∪ 入口在其中的后代区域 blocks`）；极小认领者唯一；
改判仅当新父块集 ⊊ 原选者块集。

```
r4_probe_index    71/81 单元  27 success / 10 failure            逐位 STAY
r1_probe_index   107/110 单元  43 success / 3 failure            ← 回退：r1_42_self_product_cgroup
                                                                 <module>.add_process_to_cgroup 8/8 → 7/8
r1_regress        34/34  STAY
strategy 单元差量：4 处 replace → 7 处 replace + 一段 delete（566..610 整段丢），形态恶化
clock_worker 边：@6690 → @6548 ✓ 但读数仍 12/13
```

回退根因（边差分探针原文）：`IfRegion@94 base=TryExceptRegion@4 new=IfRegion@4`、
`@376 base=TryExceptRegion@4 new=IfRegion@94`、`@492 …new=IfRegion@376` —— `IfRegion.else_blocks`
与 `elif_conditions` 在本分析器里是 **elif 链的续流引用**，据其建父子边即把链的兄弟层改判成嵌套层（原则4 的入口引用被重复表达）。

### 2.2 v2（交付形态判据）——缺陷修复 + 零回退 + 零翻转

两条显式守卫（承 §1.3 与 §2.1 实弹，也承 `FIX_PAIRED_ARMJOIN` §3.1「绝不以宿主条件块为臂内前驱」）：
① 认领清单限定为**正向臂**（IfRegion 取 `then_blocks/elif_bodies/elif_final_else`；LoopRegion 取
`body_blocks/else_blocks`；TryExcept 取 `try_blocks`；With 取 `with_blocks`）；
② `child.entry` 除「全部前驱 ∈ 成员闭包」外，还须**至少一条前驱 ∈ 臂体闭包**（臂体块 ∪ 入口在臂体内的后代块）。
另保留：极小认领者唯一 + 新父块集为原选者真子集（否则保留既有结论）。

```
命名缺陷：IfRegion@6690.parent  LoopRegion@5598 → IfRegion@6548 ✓（then_blocks 认领 + 前驱 6652/6678 在臂体内）
          IfRegion@6548.parent  LoopRegion@5598 → IfRegion@6280 ✓（同判据）
strategy：@536 的 @512 认领被**正确拒绝**（前驱 524 是 @512 的 or 链腿块、不在臂体内），改判为外层 @210；
          其余 6 条边（@512/@612/@642/@718/@748/@1006）按成员证据落位 ⇒ 单元差量 4 处 replace **逐位与基线相同**（未恶化）
r1_42：@94/@376 回到既有父级，仅 @492 改判，读数 8/8 复原 ✓
```

### 2.3 v2 全套门禁读数（代码态实测原文）

```
single strategy                 26/27   single api_base             27/28
single matcher                  16/17   single realtime_event_source 12/13
single bar                      84/85   single function             70/71
single load_daily               26/27   single finance              31/32
batch round4/r4_probe_index     71/81 单元  27 success / 10 failure / compile_error 0 / error 0   STAY
batch round1/r1_probe_index    108/110 单元  44 success / 2 failure                               STAY
batch round1/r1_regress_index   34/34  单元  17 success / 0 failure                                STAY
batch round2/r2v3_probe_index  105/126 单元  41 / 21                                               STAY
batch round3/r3_probe_index    101/122 单元  35 / 21                                               STAY
pins（20，先删后重生成再判，全部 = 基线）quotation 152/153（失败单元仍 <module>.get_fundflow_day）·
  handlers 29/30（仍 TWHThreadController._target）· trading_dates_mixin 14/14 · stock_position 37/37 ·
  cgroup_utils 8/8 · email_utils 4/4 · calexrights_func 8/8 · future_contract_info 29/29 · fly/logger 64/64 ·
  ptradeAccount 137/137 · quote 86/92 · trade_info_utils 37/41 · trade_live_broker 118/128 ·
  profiler_func(IQEngine/utils) 17/18 · strategy 26/27 · api_base 27/28 · matcher 16/17 ·
  realtime_event_source 12/13 · finance 31/32 · bar 84/85 · function 70/71 · load_daily 26/27
pytest 6 套件   2 failed / 277 passed / 2 xpassed（仍 test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function）
import core.cfg.{region_analyzer,region_ast_generator,code_generator} OK；python -X utf8 -m compileall -q core OK
未跑：402 语料八分片批（按工单由主代理持有）。
```

## 3. 标记 · True-hits vs flips

| 标记 | 站点 | True-hits（实测） | flips |
|---|---|---|---|
| `[R5-B118-parentedge]`（v2 版共 6 处：新方法 ×5 + `_build_region_hierarchy` 覆盖点注释） | `region_analyzer.py` `_build_region_hierarchy` 的 best_parent 之后、建边之前，配 `_membership_enclosing_region` / `_region_membership_closure` / `_region_arm_body_blocks` / `_region_arm_body_closure` / `_closure_from_blocks` / `_index_regions_by_entry` / `_block_claimed_by_region_arm` | 父边改判 **9 条**：`clock_worker` @6690（命名缺陷本体）+ @6548、strategy 7 条、`r1_42` 1 条；v1 另在 cgroup 链上改判 3 条（即回退来源） | **0**（八靶 + 37 臂 + 五电池 + 20 pin 逐位不变） |

合成臂：0 命中新增、**0 翻转**；六哨兵 `r4v3_a02/a06/a07/a08/a09/a13` 仍各 1/2。

## 4. 收窄后的残余（下一票最窄表述）

1. **「修父边是其余一切的前置条件」这一移交假设被实测否决**：v2 把命名缺陷真修掉了（@6690 现挂 @6548），
   但 `clock_worker` 仍 12/13、strategy 的差量四条（522/534→568 被发成 820、992/1004→1038 被发成 1286）
   **逐位不变** ⇒ 这些单元的发射路径不消费新父边；父边只改层级，不改臂尾/链极性。
2. **命名缺陷只交付了一半**：父边 ✓；另一半「6702 / 6778 ∈ `@6548.blocks ∪ then_blocks`」属
   **IfRegion then/else 边界求解**（`rules.md` §3.2.1），不在层级装配处。本票判据按 C1 刻意**不向任何区域追加块**
   （只校验归属），故不可能由本票顺带完成；下一票应在 then/else 边界处以「全部前驱在臂闭包 ∧ 块末 opcode ∧
   显式 merge 排除」补成员，并沿用本票两条守卫。
3. **本票新得的两条结构结论**（务必带进下一票）：
   ①候选含 ≥2 个 LoopRegion 时，31534 的循环 tie-break 会**先于**臂成员证据胜出 —— 这是本簇错父边的唯一触发点；
   ②`IfRegion.else_blocks` / `elif_conditions` 是链续流引用，不得作为父子认领证据（v1 实弹：一条绿臂转红 +
   strategy 差量翻倍）。
4. **A 族语料翻面闸口不在层级**：strategy 等六靶的差量在 or 链第三腿（链式比较续腿）认领 + R14c 取反极性；
   六哨兵在 `region_analyzer.py:4810-4845` 幻影 loop-else + 回边桩 continue 语义成对；
   `clock_worker` 13/13 仍需 `FIX_PAIRED_ARMJOIN` §7.1 的 ②③④ 三手。三条路线本票均未并票、未触碰。
5. `Region.exit` / `exit=`、`_trailing_rn_exit_count`、walk 侧三条已判死路线本票零投资；
   `profiler_func` 仍不属本族（E1 站点 calls=0 复述，读数 17/18 逐位不变）。

## 5. 回滚 · 字节完整性 · 插桩残留（终态 = 入轮字节）

```
core/cfg/region_analyzer.py      2045409 bytes / \n 32167（行数口径 32168）/ 前导 BOM 1 / CRLF 32167 / bare LF 0 /
                                 sha256[:16] = 2a7517c61b083449  ✓ 与入轮备份 D:/Temp/rrv5/bk2/region_analyzer.py 逐字节相同
core/cfg/region_ast_generator.py 3684310 bytes / \n 58668（行数口径 58669）/ BOM 1 / CRLF 58668 / bare LF 0 /
                                 sha256[:16] = ab05c4c6bb9da904  ✓ 全程未改
core/cfg/code_generator.py       299897 bytes / 6022 行 / 无 BOM —— 未触碰
编辑期间 CRLF 全程保持（v2 态实测 lf 32451 == crlf 32451、bare LF 0、BOM 1）；ast.parse 两文件 OK
标记复验（core/cfg/ 三文件合计，与入轮逐条相同）：
  [R2-B106] 4 · [R2-B107] 7 · [R2-B108] 5 · [R3-B115] 1 · [R3-B109] 3 ·
  [R4-B116 sinkexit] 4 · [R5-B100-armjoin-trueentry] 4
插桩残留 grep（python 计数，core/ + scripts/ + test_repros/ 全量 .py）：
  _membership_enclosing_region 0 · _region_membership_closure 0 · _region_arm_body_blocks 0 ·
  _region_arm_body_closure 0 · _closure_from_blocks 0 · _index_regions_by_entry 0 ·
  _block_claimed_by_region_arm 0 · R5-B118 0 · parentedge 0 · _regions_by_entry 0 · _closure_memo 0 · probe[0-9] 0
禁止前缀命名新增方法 0（`def _fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 全部 0）；
硬编码深度/数量/语句数上限 0；文件名·函数名·偏移特判 0；文本后处理 0；抑制式发射 0。
`Region.exit` 未读未写；`_trailing_rn_exit_count` 未动。
临时脚本 probe5/6/7/8.py、regen_batch.py、pins.py、hunks.py、p5_clock.txt、pins_*.txt、bk2/ 全在 D:/Temp/rrv5/，
生产目录零新增文件。
```

## 6. 索引完整性（交付物 4 不执行的核验）

```
test_repros/round4/r4_probe_index.json 条目 37、unique 37、缺 pyc 0、缺同名 *OK.py 0；
盘上 test_repros/round4/r4v3_*.pyc = 37 个 ⇒ 与条目一一对应。
本票未改动 r4/r1/r2/r3 任何索引、REVIEW/FIX 文档；终态产物全部在回滚字节上重生成后复判（§2.3/§5 读数）。
```
