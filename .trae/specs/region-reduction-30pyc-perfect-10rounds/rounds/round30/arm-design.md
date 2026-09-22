# Round 30 arm design — R30-C1：终止指令是「跳向别处头部的向后跳转」的候选 break 块，是外层 loop 的回边，不得作本区域的 break 认领

## 靶子与目标池（实测，基线 = 落地字节 `06f0ba50`）

索引口径下 partial 32 个、Σdeficit 104、deficit==1 的文件 8 个（`logs/pool30.txt`，逐条
`path / matched/function_count` 已存档）。本轮锚点取其中缺口最大的一个：

`site-packages/IQEngine/plugins/plugin_system_event_source/default_event_source.pyc`
`:: <module>.DefaultEventSource.events` —— 官方尺 `['events', 510, 491, 2, 157]`（缺 19 条），
严格尺 `seq_len 512/493`、**4 个非相等对齐块**（`logs/g4prime_head.txt`、一手差分
`logs/g4prime_hunks_events.txt`）：

```
H1 delete   orig[352:367] @2380..2472 -> decomp[352:352]        n=15/0
H2 replace  orig[481:483] @3208..3212 -> decomp[466:474]        n=2/8
H3 replace  orig[485:486] @3238       -> decomp[476:477]        n=1/1   (LOAD_CONST 15 vs 8)
H4 replace  orig[489:500] @3258..3318 -> decomp[480:481]        n=11/1
```

H1 那 15 条（`LOAD_FAST 'day' … STORE_FAST 'dt_before_day_trading'`）**在两臂下都逐字出现一次**，
位置固定在产物 idx 466 / @3116（本轮一手串计数，见 §四），即它不是丢失而是被排到了循环之后；
H3/H4 才是真正少发射的部分。这个「同一段既少排、又错排」的复合形状，正是本轮判据的作用点。

## 三条诊断线的取舍（全部实测，代理日志 `logs/diag{A,B,C}_ANALYSIS.md`）

| 线 | 靶子 | 一手读数 | 结论 |
|---|---|---|---|
| A（异常尾声发射侧） | `risk_calculation/function.pyc :: save_testds_to_json 314/310`、`fly/common/flytools.pyc :: FileLock.acquire 88/85` | R30-A（拒绝消费 bare-return-None 尾声）**改进 0**：靶子只是把副本移到函数尾（仍 310），并在合成锚 `r2_09_bool_cond_invert_dec*` 上造成**真回归 102/102 → 96/80**；对 flytools 的产物**字节零改动** | **REJECTED**。同时修正 Round 28 的同族归并：两个靶子不是同一种缺陷 —— function.pyc 是缺一份内联 `return None` 尾声副本，flytools 是「裸 raise 迁移 ＋ `except-as e` 清理尾声 ＋ 环尾回边丢失」的混形，尾声载荷是 `STORE/DELETE e`。发射侧重设计（按跳转前驱把副本挂回 except 退出口）**只推断、未落地** |
| B（汇合块的源级嵌套归属） | `fly/dumpload/load_daily.pyc :: <module>` 严格尺 `target_diff #596` | R30-B3 完整门禁：98 文件窗 sha 级 `SAME=97 MOVED=1`、REGRESSION=0，严格尺 `target_diff → CLEAN`、文件 clean `22/25 → 23/25`，全 402 官方尺 **SAME=402 / IMPROVED=0** | **不占本轮槽位**：官方尺完全中性且 G0 不可得（该族缺陷在分析器对原始布局的读取，任何源级合成都不落进那个状态，Round 29 已实测过一次）。判据与证据原样移交（任务 #61） |
| C（内层 loop 的 break 角色核验） | `default_event_source.pyc :: events −19` | 见 §二、§三 | **本轮采纳** |

线 C 胜出的理由是三条硬指标同时成立：① 有**语料外可复现**的见证电池与 CONTROL 电池（线 B 恰恰没有）；
② 只删不增；③ 在真实语料靶子上找回 17 条被吞掉的指令，且在 402 份产物上**足迹只有 1 份**。

## 二、根因链（代理一手打戳，编排方独立复现）

内层 loop 区域构造时（`core/cfg/region_analyzer.py` 的 LoopRegion 路径 `_r102` 块，约 4060–4130），
候选 break 块经 `verified_break_blocks` → `region_blocks` 进入本区域，随后
`region_ast_generator.py:4216` 的批量入账把它的指令登记为「已生成」。靶子里被吞掉的块 @3214
同时被三处认领（`[Q] L4216 / L6469 / L20469`），所以**发射侧收窄任何一处认领都无效**
（实测 `candc` 臂 `SAME=2 IMPROVED=0`）—— 这是本轮最有价值的负结果：修必须落在分析器侧的
那一次认领上。

## 三、判据 R30-C1

锚点 `core/cfg/region_analyzer.py:4098`（`if break_blocks:` / `for break_block in break_blocks:`
与紧随其后的 `_r102_reachable` 前驱测试之间），落地形为该处插入 **5 行判据注释 ＋ 6 行代码**
（`git diff --numstat` = `11 0`，纯 CRLF 保持，该文件本就无 BOM）：

```python
                    _r30c1_last = (break_block.get_last_instruction()
                                   if break_block.instructions else None)
                    if (_r30c1_last is not None
                            and _r30c1_last.opname in BACKWARD_JUMP_OPS
                            and _r30c1_last.argval != header.start_offset):
                        continue
```

判据（结构表述）：**候选 break 块是「离开本区域」的块；若它的终止指令属于向后跳转类，而落点
又不是本区域的头部，那条终止边就是某个外层 loop 的回边，本区域不得把它当作 break 出口 ——
不核验、不并入 `region_blocks`，也就不会经批量入账变成无人发射的块。**

同层性：三个合取项只读**块自身**的属性（终止指令的 opname 类、跳转落点与本区域头部的同一性
关系），不读绝对偏移常量、不读名字／常量、不读指令条数、不读函数名、不读源码形状。

同源形状：同一个 `_r102` 块上方 9 行处（`:4089-4091`）已经有一条**后继侧的镜像**判据
`_rl = _rb.get_last_instruction(); if _rl and _rl.opname in BACKWARD_JUMP_OPS and _rs.start_offset == _rl.argval: continue`
——「终止指令跳向自己」的后继是本 loop 的回边，不是出口。本轮用的是同一个 helper
（`get_last_instruction`）、同一个 op 类常量（`BACKWARD_JUMP_OPS`，`:30` 处导入）、同一个关系
形状，只是把它搬到 **break 角色侧**。因此补丁不引入任何新词汇，只补一条对称缺失。

不命中时行为逐字节不变；命中时只**取消一次成员资格**（`verified_break_blocks.add` 与其后的
`region_blocks.add`），不新增任何发射、语句或块。

## 四、本轮一手实测（编排方自己的镜像根 `D:/Temp/r30gate/c1`，非转述）

* **G0/G1（语料外复现）**：`test_repros/round30_enclosing_loop_backedge_break/r30c_w2.pyc`
  落地核 `3/6`（`w_a_true_break_epilogue 27/21`、`w_b_true_break_yield_epilogue 23/19`、
  `w_e_deep 30/26`）→ R30-C1 `6/6`、`mism=[]`；CONTROL 电池 `r30c_witness.pyc` 两核均 `6/6`
  且产物 **sha 逐字节相同**（`ef52a76276145780`）。见证产物 sha `d17b0ae28839af5e → 82e204835d56eeed`。
* **靶子一手严格尺**：`512/493 (−19) 4 hunk → 512/510 (−2) 2 hunk`，文件级 clean 13/14 不变、
  sigma-defect 1 不变。余下两处 = H1 的 15 条错排（产物 @3116）＋ orig@3208..3212 的
  `JUMP→JUMP` 两连。
* **两臂产物间差分**（一手）：c1 相对 head 在 `events` 里**只有一段 17 条插入**
  （@3210..3314：`date.replace(15,30)` → `dt`、`Event(EventEnum.AFTER_TRADING_END, dt, dt)` 的
  yield、以及循环尾的 `POP_TOP`），**零删除、零其他改动** —— 与「只删不增、找回被吞块」的判据
  表述完全一致。
* **落地形等价**：带注释的落地镜像 `mirr_c1c` 去掉那 5 行注释后与测量臂 `mirr_c1` **逐字节相同**
  （`provec.py`：唯一 insert opcode、5 行全为注释），且 38／96／402 三档对测量臂
  `ab` 判据 `SAME=38 / SAME=96 / SAME=402 MOVED=0`。
* **落地核复现**：`batch --all` 重写的靶子产物与测量臂 `build_c1` 的产物 **sha 相同**
  （`e80b5b38f0146f2b`），落地核文件与 `mirr_c1c` **sha 相同**（`7ee4151d31faf41b8202…`）。

## 五、被排除的候选（勿再取）

1. **发射侧收窄认领**（把 `:6468` 的 Round-08 移交标记限定为可渲染角色集）：实测死路，@3214
   被三处认领，任一一处收窄都被其余两处抵消（`candc` 臂 `SAME=2 IMPROVED=0`）。
2. **R30-C2（父 loop 直接移交子 loop 区域时，先就地渲染 fall-through 序中排在子区域之前的裸体块）**：
   单独用计数中性（`491→491`），必须与 C1 同轮才有意义；加上 C1 可把严格尺压到只剩 1 个非相等
   块，但官方尺 `true_diffs 157→31` 而 `jump_diffs 2→4`，且多 22 行源码。本轮按「一轮一条判据」
   只落 C1，C2 随残余移交。
3. **给最后 −2 补跳转发射**：未尝试，且明确警示 —— `JUMP_FORWARD exit / JUMP_BACKWARD header`
   两连是 CPython 在「body 末条语句即 break 的 `while True:`」尾部留下的边；若原始的那条回边无法
   从任何忠实源码重新生成，`events` 就有 −2 下限，追它是死路（需自己的轮次，不是门禁槽位）。
4. **把 `events` 归入 Round 24 的「整块丢失族 D」**：它是两条机制（17 条少排 ＋ 15 条错排）再加
   第三个 2 指令形状，没有任何单条 block-loss 判据能覆盖。
