# FIX_R21-47 — clock_worker：臂内语句的「归属套件」= 最后一条伪 JUMP_FORWARD 的成因

工单：**R21-47**（R21-44 今天用了两次、R21-45=r74、R21-46=r75，故取 47）。
目标单元：`<module>.RealtimeEventSource.clock_worker`
（`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`，13 单元，面板 12/13）
镜像：`D:/Temp/r76`（仓库 `D:/admin/.../pythoncdc-main` 全程只读）
基：`core/cfg/region_ast_generator.py = f51f9de14d216cda`（= r74c，门禁 38 landed `11324f276cce6d5b` + [R21-45] A+B），
`core/cfg/region_analyzer.py = f7d849e974904492`（不动）。

## 0. 前提复测（规则 6：简报逐条重测，全部在 `D:/Temp/r76` 干净镜像里跑）

镜像认证：
```
core/cfg/region_ast_generator.py  sha256[:16] = f51f9de14d216cda   （= 简报给的 starting base，MATCH）
core/cfg/region_analyzer.py       sha256[:16] = f7d849e974904492   （MATCH）
```

| 字节 | 来源 | orig/prod | delta | hunks | landings | 判定 |
|---|---|---|---|---|---|---|
| `f51f9de14d216cda` | r74c（本工单基） | 1424/1420 | **−4** | **3** | 9 | `status=failure units=12/13` |
| `0a2f4a81c593b1c6` | r75 [R21-46] A+B 走 r75 的构建器在 r74c 上重建（逐字节 `cmp` = r75 DELIVER 件） | 1424/1427 | **+3** | **3** | 10 | 12/13 |
| `05abc061c9fb10ed` | r75 半件 A 独走 | 1424/1426 | +2 | 4 | — | 12/13 |
| `30a4d7827122e165` | r74d（= r74c + [R21-44]）+ r75 A+B | 1424/1426 | **+2** | **2** | **7** | 12/13 |

简报的数字**全部复现**（−4/3、A 独走 +2、AB +3、AB_on_r74d +2）。**两处更正**：

1. **r75 的 A+B 已经把 17 指令块发在臂里了**，缺陷 1 不是「还落在函数尾」。
   A 独走（`05abc061`）才是 relocation：`delete orig[1050..1067 @@7268..@@7368] del=17` +
   `insert ... @@9194 ins=17`。加上 B（`_r2113_legs_back = blocks[1:]`，把成员块交还臂体，
   复用已落地 [R21-13] 通道）后，r75ab 的 3 个窗**全部是单条伪 `JUMP_FORWARD`**
   （prod @6496 / @7254 / @7592），`debug` 缺失窗消失。⇒ 缺陷 1 的「内容」已由 r75 A+B 关闭，
   剩下的位置问题是**臂尾跳转 + landing**（见 §1）。
2. **基（r74c）上伪跳转是 2 条，AB 上是 3 条**，因为 @6496 那条属于 [R21-44] 站点（@6342/@6496），
   只有把 [R21-44] 一起上（r74d）才关掉。可交付候选的底座因此是 **r74d + r75 A+B**
   （`30a4d7827122e165`，2 窗 + 7 landing），不是 r74c。

## 1. 真实源码形状（3.11.7 实测 dis + `compile()` 反证，非散文）

区域数据（`work/probe_ibc.py`，本镜像实测）：
```
IfRegion cond=@7164..@7184(5)  then=[…大…] else=[] merge=@7216..@7246(6)      ← A 测试
IfRegion cond=@7186..@7200(6)  merge=@7216                                    ← B 链式比较
     ibc key-block=@7248 op='and' blocks=[7248, 7270]                          ← 把 D/E 误读成 D and E
IfRegion cond=@7216..@7246(6)  then=[7248,7270,7492,7372,7488] else=[] merge=@7582   ← C 测试
IfRegion cond=@7270..@7370(17) then=[7372,7488] else=[7492] merge=@7582        ← E 测试（else=[7492] 是误判）
块：@7248 last=POP_JUMP_IF_FALSE->7492 preds=[7216, 7202]
    @7270 last=POP_JUMP_IF_FALSE->7492 preds=[7248]
    @7492 preds=[7248, 7270] last=STORE_ATTR pre_before_trading_date succ=[7582]
```
原始 dis（`work/dis_unit.py orig … 7160 7600`）唯一自洽的形状：
```
if now_date > self.pre_before_trading_date and pre_before_trading <= now_time < pm_close \
        or self.pre_before_trading_date == self.initial_trading_date:      # (A and B) or C，假出口 -> @7582
    if now_date != self.first_run_date:                                     # D，假出口 -> @7492
        system_log.debug('获取重登信号量')                                    # @7270 前 6 条 = 一条语句
        if login_semaphore.acquire(timeout=LOGIN_TIMEOUT * 60) is False:    # E，假出口 -> @7492
            system_log.error(...); self.event_queue.put((dt, SYSTEM_EXIT)); return None
    self.event_queue.put((dt, EventEnum.PRE_BEFORE_TRADING_START))           # @7492：if-D 之后的**顺序语句**
    self.pre_before_trading_date = now_date
                                                                            # 臂尾无 JUMP，直接落进 @7582
```
两条判据性事实（不是猜测）：
* **D-false == E-false == @7492 且 @7492 有两条前驱（来自 D、来自 E）** ⇒ @7492 是**顺序续体**而不是 E 的
  else 臂：若 @7492 真是 `if E: … else: @7492` 的 else 体，则 D 的假出口必须跳过整个 else 体落到 @7582。
  现产品把它当 else 发（on_r74d_v2 第 257-259 行 `else: put; store`）⇒ landing #4
  （`orig[1050] @7268 IF_FALSE ->idx1086` vs `prod ->idx1101`）与窗 @7590 的伪跳转都是它的后果。
* **@7270 块 = 完结语句前缀 ++ E 测试**（CPython 不在语句结束与紧随的条件求值之间分裂基本块）
  ⇒ `inline_boolop_chains[id(@7248)] = {'op': 'and', 'blocks': [@7248, @7270]}` 是**误读**：
  BoolOp 的操作数块里不可能有一条 POP_TOP 收尾的语句。r75 的 [R21-46] 谓词
  `_r2146_ibc_member_has_stmt_prefix` 正是这条事实的判据（它复用既有切分器
  `_split_block_condition_prefix` + 台账 `prefix_emitted_upto`）。

## 2. 还开着的机制（在最优底座 r74d + r75AB 上，2 窗 + 7 landing 的全清单）

```
窗 #1 insert prod @7252 JUMP_FORWARD    ← (A and B) or C 在 @7164 未平折（被 ⑧ 拒动）
窗 #2 insert prod @7590 JUMP_FORWARD    ← 同一站点臂尾：@7492 被当 else  ⇒ 臂尾必须跳转
landing #1 orig@7184 A 假出口 -> @7216(C) vs prod -> 1392(尾)      ← 平折缺位
landing #2 orig@7210 B 真出口 -> @7248(D) vs prod -> (插入伪跳转的影) ← 窗 #1 的影子
landing #3 orig@7246 C 假出口 -> @7582 vs prod -> @7256           ← 平折缺位
landing #4 orig@7268 D 假出口 -> @7492 vs prod -> @7594           ← else 误判
landing #5 orig@7602 A' 假出口（@7582 站点）-> @7634 vs prod -> 1392 ← @7582 站点同样未平折
landing #6/7 orig@8972/@8978 -> idx1384 vs prod -> 1385/1392      ← 尾跳落点被窗 #1/#2 推移的影子
```
⇒ 单靠「删掉两条跳转」不够：**必须让 @7164 站点走平折形状，且把 @7492 发成顺序续体**。
已证伪（本会话不再重试）：无条件放行 ⑧（`rounds/round39/r74/DIAG_r74d_relax_conjunct8.py`、
`round39/r75/DIAG_r75_relax_conjunct8_on_r74d_plus_r2146.py`）⇒ `delta=−274`，
54/55/160 指令整臂被删；`_orphaned_blocks` 释放路径（本文件 0 事件）；本单元 `merge_block is None`
的 IfRegion 为 0，故 back_edge/merge-declaration 轴无关。

## 3. 形状判定用 `compile()` 反证（规则 5，3.11.7，`work/shape_topology.py`）

把 @7164..@7582 的三条候选源码形状各自编译，**在指令索引空间**比较跳转拓扑
（索引空间对沙箱里 `LOAD_DEREF/LOAD_GLOBAL` 与 `LOAD_FAST` 的宽度差免疫；
`SHAPE_S1_target_shape.txt` 里的 44 个 `**` 全是这类取指宽度差，不是结构差）：

```
orig 窗口 75 条，跳转 7 条，拓扑 = [IF_FALSE+12, IF_FALSE+5, IF_TRUE+9, JUMP+2,
                                    IF_FALSE->窗口尾, IF_FALSE+36, IF_FALSE+19]
S1 平折 + @7492 顺序续体   ：6 条全部逐条相同，第 7 条只差窗口边界（C 的假出口正是尾外第一条）
S2 现产品形状（嵌套+elif+else 尾）：A 假出口 / C 假出口 / D 假出口 三条全错
S3 平折但 @7492 仍作 E 的 else    ：D 假出口 +49（跳到臂尾之后）≠ orig +36（跳到 @7492）
```
⇒ 目标形状唯一确定为 S1；且 **S3 的失败方式与实测 landing #4 完全一致**
（`orig[1050] @7268 IF_FALSE ->idx1086` vs `prod ->idx1101`），
所以 (c)「@7492 是顺序续体不是 else」是独立于平折的第二条判据，不是平折的附属品。
`work/shape_site1.py` 可复现三段对照输出。

## 4. [R21-47] 半件 A 的第一次落地与它的死因（本工单的实测增量）

构建器 `build_cand_r76a_r2147.py`（基 = `30a4d7827122e165`，打印 sha16 before/after，
BOM+全 CRLF、锚点唯一断言、`py_compile`）：
`--halves a` ⇒ `CANDIDATE_r76a_r2147A_gated_relax8_e38c0348a48a35e6.py`（`e38c0348a48a35e6`）。

判据 `_r2147_seq_if_head(blk, arm_lo, arm_hi)`（纯区域身份 / opcode 类别 / 前驱后继）：
① blk 是某区域 `inline_boolop_chains` 的**链首**且 `op=='and'`；
② 非链首成员带「栈已归零的完结语句前导且未登记发射」（复用 r75 既有谓词
   `_r2146_ibc_member_has_stmt_prefix`，不新建切分器）；
③ blk 与每个成员块都以 IF_FALSE 收尾且**目标同一个块 F**，F 的前驱恰为这些块（顺序 if 的
   共享续体签名）；④ blk 与 F 都落在本臂跨内。
⑧ 只在 ①-④ 全成立处放行。

| 字节 | orig/prod | delta | hunks | landings | 判定 |
|---|---|---|---|---|---|
| 基 `30a4d7827122e165` | 1424/1426 | +2 | 2 | 7 | 12/13 |
| + [R21-47A]（⑧ 受条件放行） | 1424/1150 | **−274** | 5 | 3 | 12/13 |

**读数与解释（这是给下一位的关键事实）**：条件放行后 @7164 站点拿到了平折
（5 窗 = `delete @7248..@7268 (5)` + `@7582..@7836 (54)` + replace + `@7960..@8276 (55)` +
`@8282..@9192 (160)`），**与 r73/r75 的无条件放行 `-274` 逐窗相同** ⇒
⑧ 的保守性不是障碍，**障碍是臂入口 @7248 的派发**：平折把区域重声明为
`then=_fr_m.then_blocks ∩ [T,E) = [@7248, @7270, @7492, @7372, @7488]`，
`_process_if_blocks` 里 @7248 既不是任何 IfRegion 的 entry/condition_block
（`_nested_if_entry_generate` 走不到），又被 `_generate_block_statements` 当普通块吞掉，
于是整条臂（含 D/E/尾语句和后续 269 条）失去发射者。
⇒ **[R21-47] 真正缺的半件是「臂内无主测试块的合成派发」**，形如
`IfRegion(entry=condition_block=@7248, then=[@7270], else=[], merge=@7492)` 的声明级对象
（r74 §8 给分析端开的那条路；分析端本工单被钉在 `f7d849e974904492` 不能动，只能在发射端合成），
并且它必须与「@7492 不是 E 的 else」的判据同乘 —— S3 证明只做其一都留下 landing 差。
爆炸半径已数过：20 面板文件里 `changed files = 1`（只有受害文件），
其余 19 个产物与基逐字节相同 ⇒ broker `126/128`、quote `92/92`、quotation `153/153`、
order_api `37/37` 在候选上保持（表见 `PANEL_base_vs_e1.txt`）。

## 5. 半件 B（顺序续体判据）设计，未落地

`IfRegion` 的 `else_blocks=[F]` 是**伪 else** 的充分签名（S1/S3 对照已证）：
存在测试块 P，`P` 的 IF_FALSE 目标 = F，`P` 的另一条件后继 = 本区域 condition_block，
且 F 的全部前驱都在 `{P} ∪ 本区域条件块` 之内 ⇒ F 在 P 的臂**之外**，
因此不可能是 P 臂内那条 if 的 else 体 ⇒ 本区域发单腿 if，F 交回 P 所在套件按顺序发射。
它必须与半件 A 的合成派发同时成立（否则 F 无人接手 ⇒ 新的缺失窗），
故本工单不把 B 单独做成候选去测一个注定不翻正的读数。

## 6. 交付物（`D:/Temp/r76/DELIVER/`）

`FIX_R21-47_clock_worker_arm_statement_placement.md`（本文，§0 复测 / §3 形状判定 / §4 死因）
`build_cand_r76a_r2147.py`（`--halves a`、`--base`、`--out`、`--probe` 预留；基 sha16 断言）
`CANDIDATE_r76a_r2147A_gated_relax8_e38c0348a48a35e6.py`（半件 A，实测 −274，不安装）
`CANDIDATE_r75AB_on_r74c_rebuilt_0a2f4a81c593b1c6.py`（用 r75 构建器在本基上重建，
  与 r75 DELIVER 件 `cmp` 逐字节相同 ⇒ 我的重建链无夹带）
`ALLWIN_e1_relax8gated.txt`、`ALLWIN_on_r74d_v2.txt`（无小窗过滤 + judge 行）
`PRODUCT_base_r74c_ / PRODUCT_r75ab_on_r74c_ / PRODUCT_base_on_r74d_v2_ / PRODUCT_r76a_e1_realtime_event_sourceOK.py`
`SHAPE_topology_site7164.txt`（索引空间跳转拓扑对照 = 形状判决）、
`SHAPE_S1_*.txt`、`SHAPE_S2_*.txt`、`SHAPE_S3_*.txt`、`shape_site1.py`、`shape_topology.py`
`PANEL_base_vs_e1.txt`（20 文件 base/候选 sha16 + `changed files = 1`）
`vmeasure.py`、`allwin.py`、`unit_diff.py`、`regen_only.py`、`probe_ibc.py`、`census_regions.py`（本会话读数工具）

## 7. 仓库状态

仓库全程只读：未写 `core/`、`scripts/`、`site-packages/`、`.trae/`。
镜像 `D:/Temp/r76` 收尾恢复简报给的基：
`core/cfg/region_ast_generator.py = f51f9de14d216cda`、`core/cfg/region_analyzer.py = f7d849e974904492`（安装后 `cmp` 两次）。

