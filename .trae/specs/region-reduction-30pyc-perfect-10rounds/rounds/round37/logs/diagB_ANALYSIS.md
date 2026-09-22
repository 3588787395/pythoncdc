# Round 37 · 诊断线 B（DIAGNOSE-ONLY）：`matcher.pyc :: DefaultMatcher.match` 的 281/259 换位根因

靶：`F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc`
函数 `<module>.DefaultMatcher.match`，落地态 official `16/17`，一手读数 `orig=713 decomp=689 jump=9 true=524`。
本文件全部产品/插桩只写入 `D:/Temp/r37diagB/`；仓库内零写入；核副本只读镜像在 `D:/Temp/r37diagB/mirr_probe/`
（`setup_mirror.py` 断言与 worktree `core/` **BYTES IDENTICAL: True**，`__pycache__` 为空，sha256[:20] `bbfe1a414032436921ab`）。

脚本清单（全部可复跑）：
`drv.py`（臂可选的重生成+测量）· `blocks.py`（块分区/区域树/发射时序）· `align.py`（指令级对齐证明）·
`probe2.py`（IfRegion 组成 + 时序）· `patch37.py`（候选 R37-B 打到镜像核）· `patch37b.py`（收窄变体 R37-B′）·
`sweep.py` + `cmp_sweep.py`（402 文件双臂全量代价）· `mkbattery.py` + `runbat.py` + `showbat.py`（合成电池）·
`expo.py`（语料暴露面）· `offrec.py`（官方标尺按产物测量）。

---

## 1. 块级实测：换位被定位到**唯一一条归属决定**

### 1.1 落地态复现（先证明测量对象就是被跟踪的产物）
`python -X utf8 drv.py landed out/matcher_landed.py <matcher.pyc> match` → 0.985 s，产物 12922 字符，
与仓库跟踪的 `matcherOK.py` **逐字节相同**；strict 缺陷函数恰 1 个（`match`, 715/689）；official `16/17`；
三处 hunk 与归档 `round36/logs/probe1_matcher_match.txt` 完全一致：

| # | 类型 | orig 区间 | orig 偏移 | decomp 区间 | decomp 偏移 | 长度 |
|---|------|-----------|-----------|-------------|-------------|------|
| H1 | delete | `orig[182:463]` | `@1322..3206` | `decomp[182:182]` | — | **281** |
| H2 | delete | `orig[575:579]` | `@3952..3966` | `decomp[294:294]` | — | 4 |
| H3 | insert | `orig[713:713]` | — | `decomp[428:687]` | `@3060..4860` | **259** |

### 1.2 基本块分区（`out/blocks_landed.txt`，78 块；块 → 指令 → 后继 → 异常后继）
关键块（`@偏移` 为该块首指令偏移）：

| 块 | 偏移区间 | 正常后继 | 异常后继 | 内容（opname 前缀） | 角色 |
|----|----------|----------|----------|----------------------|------|
| B6 | loop 头 | … | — | `FOR_ITER` | 循环头（CONTINUE 落点） |
| B22 | `@1320..1322` | `[2464]` | — | `EXTENDED_ARG, JUMP_FORWARD` | **纯转移块（无语句）** |
| B23 | `@1324..1370` | `[1372,1384]` | — | `symbol[:3] == '300'` | B1 区首条件 |
| B53 | `@2460..2462` | `[6]` | — | `… CONTINUE` | 臂尾硬退出 |
| **B54** | `@2464..2466` | `[3210]` | — | `JUMP_FORWARD→3210` | **裸跳转汇合点（祖先区 merge）** |
| B55 | `@2468..2482` | `[2484,3208]` | — | `self._price_limit` | B2 区首条件 |
| B62 | `@3208` | `[3210]` | — | `NOP` | 落点 |
| B63 | `@3210..3224` | `[3226,3954]` | — | `self._volume_limit` | C 区首条件 |
| B76 | `@4960..4962` | `[6]` | — | `CONTINUE` | 循环回边 |
| B77 | `@4964..4966` | `[]` | — | `LOAD_CONST None; RETURN_VALUE` | LOOP_ELSE |

区域树（分析器实得 **49 个区域**）：`IfRegion / BoolOpRegion / TernaryRegion` **全部是 `LoopRegion@6` 的直接子区**
——区域树是**扁平**的，源级嵌套只在 AST 生成期重建。这是本缺陷得以发生的结构前提：任何一条臂的成员表都
可以横向吞掉任意远的兄弟语句而不违反「区域树嵌套」。

IfRegion 组成（`out/probe2_landed.txt`，只读分析器实得字段）：

```
IF@1068  type=IF_THEN_ELSE cond=1110  exit=6     merge=6     then=[1190]
IF@1194  type=IF_THEN      cond=1236  exit=1320  merge=1320  then=[1316]
IF@816   type=IF_THEN_ELSE cond=816   exit=2464  merge=2464  then=[1068,1110,1190,1194,1236,1316,1320]
                                                       else=[1324..2460]        <- 区域 B1
IF@800   type=IF_THEN      cond=800   exit=2464  merge=2464  then=[816..2460]   -> 5 stmts
IF@546   type=IF_THEN_ELSE cond=546   exit=3210  merge=3210  then=[664..2464]   else=[2468..3208] <- 区域 B2
IF@3210  type=IF_THEN_ELSE cond=3210  exit=3968  merge=3968  then=[3226..3952]  else=[3954]       <- 区域 C
IF@3226  type=IF_THEN_ELSE cond=3226  exit=6     merge=6
```

发射时序（挂 `_generate_region` / `PIB`；`out/probe2_landed.txt` 尾部）：

```
PIB @1068 branch=then  blocks=[1190]                                     -> 1 stmt
GEN IfRegion @1194
GEN IfRegion @3210            <-- 整个区域 C 在 @1068 的 ELSE 臂内部被生成
PIB @1068 branch=else  nblocks=19 blocks=[1194,1236,1316,1320,2464,3210,3226,
                                         3294,3432,3574,3626,3760,3764,3828,3952,3954,3968,4678,4960]
PIB @816 branch=then / branch=else nblocks=31 [1324..2460]               -> 1 stmt   (B1 被推迟)
PIB @546 branch=then nblocks=47 [664..2464] / GEN @2468 ...              -> 1 stmt   (B2 被推迟)
PIB @10 branch=else  nblocks=69 [546..4960]                              -> 2 stmts
```

### 1.3 指令级对齐（**不是看文本像不像**；`out/align.txt`）
把被删窗口 `orig[182:463]`（281 toks）与尾部插入 `decomp[428:687]`（259 toks）做归一化 token 对齐
（跳转按 `<JUMP> kind` 归一）：

```
insert sub_d[0:3]   @3060..3072 ['LOAD_FAST','LOAD_ATTR','STORE_FAST']     # 3 toks 前置
equal  sub_o[0:65]   (orig @1322..1698)  <-> sub_d[3:68]   (@3076..3460)   n=65
delete sub_o[65:91]  @1708..1838  26 instr                                 -> [] 完全缺失
equal  sub_o[91:107] (@1848..1906)  <-> sub_d[68:84]      (@3470..3534)    n=16
replace sub_o[107]   @1908 ['LOAD_FAST'] -> sub_d[84] ['LOAD_GLOBAL']
equal  sub_o[108:153](@1910..2206)  <-> sub_d[85:130]     (@3548..3844)    n=45
replace sub_o[153]   @2208 ['LOAD_FAST'] -> sub_d[130] ['LOAD_GLOBAL']
equal  sub_o[154:281](@2210..3206)  <-> sub_d[131:258]    (@3858..4854)    n=127
insert sub_d[258]    @4860 ['JUMP']
对齐 token 253/259 = 尾部拷贝的 97.7%，= 被删窗口的 90.0%；逆序对 0；index delta 只有 {223, 249} 两个值
```

结论：
1. **259 条尾部拷贝与 281 条被删窗口是同一段区域**（253 条一一等值、5 段单调等值游程、0 次逆序），
   差值 22 完全由「一条 26 指令语句整体缺失（−26）」加「拷贝头部多出的 3 条 + 尾部 1 条跳转」构成。
   ⇒ 这是**被搬运并截断的区域**，不是重复发射（R35-B 的重复尾声抑制**没有**在这里起作用）。
2. 全序列等值游程 `orig[0:182]↔decomp[0:182]`、`orig[463:575]↔decomp[182:294]`、
   `orig[579:713]↔decomp[294:428]`、`orig[713:715]↔decomp[687:689]` ⇒ 实际发射次序是 **A, C, B**，
   正确次序是 **A, B1, B2, C**。
3. 唯一的归属决定就是 `out/probe2_landed.txt` 里 `IF@1068` 的 **`else_blocks` 成员表**（19 块，跨越
   `@2464` 与 `@3210`）。B22/`@1320` 是纯转移块、B54/`@2464` 是裸跳转汇合点：区域 B 的收尾被认成了
   区域 C 的入口。

---

## 2. 判定点定位（插桩在**镜像副本**，worktree 从未改动）

**判决发生在分析器侧，不在生成器侧。** 逐点：

| 位置 | 代码 | 实测事实 |
|------|------|----------|
| `core/cfg/region_analyzer.py:17290` | `else_blocks = self._collect_branch_blocks(else_succ, merge, else_stop)` | **就是这一行**。`block=@1068`、`else_succ=@1194`、`merge=@6`（外层 FOR 循环头，因两臂都以 `continue` 硬退出）→ 臂成员表 19 块，跨过 `@2464`、`@3210` |
| `:17135-17136` | `then_stop = {else_succ} \| (boundary_stop - {then_succ})` / `else_stop = …` | 停止集只含「兄弟臂入口 + boundary_stop」；`@2464`/`@3210` 是**祖先 IfRegion 的 merge**，从来不在其中 |
| `:16581` + `:16610` | `boundary_stop = block_region.get_if_branch_boundary_stop(block)`；`\| self._get_enclosing_structural_boundary_stop(block)` | `block_region` 是 `LoopRegion@6`，其边界只给循环头/break/continue 目标；祖先 **If** 区收敛点无人提供 |
| `:25876` | `def _collect_branch_blocks(self, entry, merge, stop_set=None)` | `stop = {merge} \| stop_set`，BFS 只沿正常后继；`merge=@6` 在身后 ⇒ 前向无界吸收 |
| `:17137-17176`（R31-B） | `for _r31b_arm … _r31b_stop.discard(_r31b_s)` | 该遍历**只从停止集里取消认领，从不新增** ⇒ 结构上不可能拦住这次越界 |
| `region_ast_generator.py:20144` | `_process_if_blocks`（臂内块按 `start_offset` 升序发射） | 生成器只是**忠实照抄**臂成员表：`@3210`（区域 C 入口）在表里，于是被就地发射 |
| `region_ast_generator.py:11152` | `if region.entry in self.generated_blocks: …` | 已发射者跳过；B1/B2 因不在 `@1068` 臂表内，只能等 `@816 else` / `@546 else` 归约 ⇒ 「推迟」是**副产物** |
| `region_ast_generator.py:3053` | `_generate_degraded_statements` | **从未触发**（0 次） |
| `region_ast_generator.py:1553` | `top_level_regions = sorted(all_regions, key=entry.start_offset)` | 顶层顺序本身是对的，被破坏的是臂内顺序 |

**没有任何 early-return / 守卫在生成器侧「起作用」——这就是答案。** 为排除「探针没打印」的假阴性，
镜像副本里 `_r37_arm_collect` 的入口无条件打印（`out/r37_trace.txt`，需 `R37TRACE=1`）：

```
ENTER arm=else entry=1194 merge=6 n=19 exempt=[6, 1110, 1190, 1194]
TRUNC arm=else at=2464 dropped=[2464, 3210, 3226, 3954, 3294, 3432, 3968, 3574, 3764,
                                4678, 4960, 3626, 3760, 3828, 3952]
      outside_preds=[800, 2164, 2208, 2338, 2380]  kept=[1194, 1236, 1320, 1316]
```
`n=19` 与 §1.2 的 `PIB @1068 branch=else nblocks=19` 逐块吻合；截断后 `kept` 正是源级 `else:` 体的 4 块。
同一函数内共 22 次 TRUNC（同一臂因分析器二次归约被收集两次，exempt 集不同：见 §6.4）。

---

## 3. 一条候选同层判据（R37-B）

**判据（≤3 句）**：一条 if 臂收集到的块序列里，若出现某块 J（非臂入口、非本 if 的 merge）带有一个
**不在「本臂成员 ∪ 本 if 自身条件/短路链块 ∪ 两臂入口」之内**的正常前驱，则 J 是**更外层区域的收敛块**：
按原则 1（块 = 前导语句 + 收尾跳转，纯转移块不承载语句）与原则 2（每块唯一归属），J 及其之后的块属于
祖先区域的续行，**本臂必须在 J 之前截断**。被丢下的块不新增任何发射——它们本来就还在外层区域的块表里
（`PIB @10 branch=else` 的 69 块已含 `@3210..@4960`），截断只是取消一次越权认领。
**只读结构事实**：块身份、臂入口/merge 字段、前驱/后继关系、opname 是否为 NOISE；不读名字、常量、
绝对偏移、指令条数、也不读遍历次序。

**最小字节编辑**（两处同形 + 一个新方法；`patch37.py` 已把该编辑逐字节施加到镜像副本并断言锚点唯一）：

锚点 1（`core/cfg/region_analyzer.py:17177`，唯一）
```
            then_blocks = self._collect_branch_blocks(then_succ, merge, then_stop)
```
替换 1
```
            then_blocks = self._r37_arm_collect(
                then_succ, merge, then_stop, 'then',
                exempt={block, then_succ, else_succ, merge} | set(chain_blocks or ()))
```
锚点 2（`:17290`，唯一）
```
            else_blocks = self._collect_branch_blocks(else_succ, merge, else_stop)
```
替换 2：同上，`'then'→'else'`。
新增方法（锚点 `    def _build_elif_region(self, block, then_blocks, else_blocks, merge, all_condition_blocks,` 之前）
```python
    def _r37_arm_collect(self, arm_entry, merge, stop_set, arm_name='', exempt=None):
        collected = self._collect_branch_blocks(arm_entry, merge, stop_set)
        _ex = set(exempt or ())
        _ex.update([b for b in (arm_entry, merge) if b is not None])
        if len(collected) <= 1:
            return collected
        _seen = set(collected)
        for _i, _b in enumerate(collected):
            if _i == 0:
                continue
            if set(_b.predecessors) - _seen - _ex:
                return collected[:_i]
        return collected
```
（镜像副本里另有 `R37TRACE` 门控的两行日志，用于 §2 的探针自证；落地时删去即可。）

**代价（402 文件全量 A/B，`sweep.py` 双臂各跑一遍，产物只在 scratch）**

| 指标 | landed | R37-B | 判定 |
|------|--------|-------|------|
| 我定义的 strict Σ\|Δ\|（长度差 + hunk 数） | **1779** | **2694** | ✗ 升 915 |
| official matched / total | **5649/5746** | 5626/5746 | ✗ −23 |
| official 部分匹配文件数 | **28** | 41 | ✗ +13 |
| official Σdeficit | **97** | 120 | ✗ +23 |
| fatal / 编译失败 / 捕获异常 | 0 / 0 / 0 | 0 / 0 / 0 | ✓ 无崩溃 |
| 变化文件 | — | better 5 / worse 19 | ✗ 净负 |

被打破的 **11 个原本 strict cost = 0** 的文件（样例）：`klinedata 16→402`、`trade_info_utils 29→225`、
`scheduler 49→177`、`gtn_request 0→99`、`ptradeFutureAccount 0→33`、`strategy_info_utils 0→25`、
`plugin_system_persist/__init__ 0→21`、`flytools 0→8`。改进仅 5 个：
`profiler_func 64→0`、`email_utils 3→0`、`api_base 51→39`、`real_quote 21→17`、`realtime_event_source 26→22`。
**⇒ 作为发货判据：R37-B 本形 NO-GO**（代价门直接失败）。
原始数据：landed 臂 `out/sweep/landed/shard{0..3}.jsonl`，R37-B 臂 `out/sweep/mirrorB/shard{0..3}.jsonl`
（402 文件全覆盖，逐文件 official matched/total + strict cost + 每缺陷函数 `(len_o,len_d,hunk 数)`）；
汇总打印 = `python -X utf8 cmp_sweep.py`，暴露面 = `python -X utf8 expo.py`。R37-B′ 只做了 `match` + 电池，
**未跑全量**（见证已不过，无须测代价）。镜像核当前状态 = R37-B（`python -X utf8 patch37.py --revert &&
python -X utf8 patch37.py` 可复现；`python -X utf8 patch37b.py` 切到 B′）。

**对 `match` 的实际效果（预测 = 实测）**
预测：换位消失、残余缩为一条语句缺失；`orig_count` 不变、`decomp_count` 不变、`jump_diffs` 略升、
`true_diffs` 明显下降；**不可能到 0 diff**（16/17 → 16/17）。
实测：`orig=713 decomp=689 jump=13 true=457`（landed 为 9/524），`first_diff index` 由 182 → **247**；
hunk 由 `281 删除 + 4 删除 + 259 插入`（搬运 token 544）塌缩为 **`26 删除 + 1 替换 + 1 替换`**（28）。
即：**只收窄，不过门**——门 17/17 还需要第二条独立判据补回缺失的 26 指令语句
`is_first_five_trading_days = …`（@1708..1838，含 `get_next_trading_date` 调用与 `SWAP/COPY/
JUMP_IF_FALSE_OR_POP` 布尔结构；两处 `LOAD_FAST→LOAD_GLOBAL` 正是该 `STORE_FAST` 缺失的派生后果）。

**收窄变体 R37-B′ 已被实测否证**（`patch37b.py`）：把触发条件收紧为「臂内第一个**纯转移块** T，
且 T 的唯一跳转目标有臂外前驱」时，`match` 的换位同样消失（`jump=12 true=458`），但 §4 的源码级见证
`w2_witness` **不再被修复**（landed 与 mirror 产物逐字节相同，cost 仍 2）。⇒ 真正的判据必须允许
「臂在**承载语句**的末块处即被祖先收敛点截断」，但一旦允许就会连带吃掉合法臂内容——
这正是 19 个回退文件的失效模式。**下一步的判别子（本诊断未解决，交Round 38）**：被截断处必须是
*祖先区域的收尾转移*，而不是*本臂自身的末条语句*——前者可由「T 已被某个以 `block` 为 merge 的臂
持有」判定，需要祖先 IfRegion 的 merge 信息（在 `:17290` 时刻尚未建出，见 §6.4）。

---

## 4. 合成见证电池（`D:/Temp/r37diagB/battery/`，全部 ≤60 行、仅 stdlib、`py_compile` 显式 `cfile`）

`python -X utf8 runbat.py`：每个用例在 **landed** 与 **mirrored patched core**（R37-B）两臂各起一个子进程
反编译、`py_compile` 回炉、按 strict 标尺测量，并在臂进程内挂 `_generate_region` / `_generate_degraded_statements`
做 R36 型异常探针。

| 用例 | 角色 | landed cost | R37-B cost | 产物比较 | 异常探针（两臂） |
|------|------|-------------|------------|----------|------------------|
| `w1_witness.py`（20 行） | 见证尝试 | 0 | 0 | IDENTICAL | exc=0 deg=0 |
| **`w2_witness.py`（22 行）** | **见证（成立）** | **2**（`<module>.w2` 58/58，h=2 等长换位） | **0** | **DIFFERENT** | exc=0 deg=0 |
| `c1_control.py`（16 行，最内层 if 两臂不硬退出） | 对照 | 0 | 0 | IDENTICAL | exc=0 deg=0 |
| `c2_control.py`（17 行，臂内含循环/完整 if-else 后续语句） | 对照 | 0 | 0 | IDENTICAL | exc=0 deg=0 |
| `c3_control.py`（14 行，elif 链 + 单臂 continue） | 对照 | 0 | 0 | IDENTICAL | exc=0 deg=0 |
| `r29a_01_shape_mimic_and_controls.py`（R29-A 既有电池，导入编译） | 对照 | 0 | 0 | IDENTICAL | exc=0 deg=0 |
| `r29x_01_module_if_deficit_witness.py`（任务 #61 语料外见证） | 对照（不得被破） | 9（144/138，h=3） | 9（同值） | IDENTICAL | exc=0 deg=0 |

`w2_witness` 在 `match` 上的同构性与产物差异（landed → mirror）：

```
@@ -14,10 +14,10 @@
                 continue
             total += 1
-            if total > 100:          <- 区域 C 被搬进 @1068 型臂内
-                total = 100
         else:
             total += 2
     else:
         total = 0
+        if total > 100:              <- 正确位置：与 C 区域同一父序列
+            total = 100
         total = total + n
```

要点：**等长换位**（58/58，两条 hunk），与 `match` 的搬运完全同类；landed 失败、patched 归零；
7 个用例中 6 个逐字节相同，唯一变化者就是见证；`r29x_01`（#61 的语料外见证）在两臂下 cost 均为 9 且产物
逐字节相同 ⇒ 本判据**没有**让它更坏，也没有掩盖它。
诚实附注：发射次序钩子（`self.statements is not st` 判定）在这些用例里恒不触发，故 `top_emission_order`
为空——该子探针**无信息量**，次序证据取自 §1.2/§2 的 `PIB`/`GEN` 打印。

---

## 5. 语料暴露面（`expo.py`，取自 landed 臂全量 sweep 的每函数 `(len_o, len_d, hunk 数)`）

测量方法 = strict 标尺下「一次大段 delete + 一段近似等长 insert」的形状筛（按 hunk 数与长度差分类）：

* **BIG-DEL+INS（≥20 指令缺口且 ≥2 处 hunk）：21 个函数 / 13 个文件** —— 与 `match` 同族的搬运面：
  `risk_calculation/__init__::get_TradeMode_trade(1843/1753,h28)`、`api_base::get_history_df(1742/1718,h9)`、
  `quote_handler::get_kline_local(760/682,h6)`、**`matcher::match(715/689,h3)`**、`quote::get_real_from_zero(703/669,h8)`、
  `trade_live_broker` 4 个、`replace_utils::decrypt_database_url(295/324,h3，+29 型)`、`log/__init__::setup(320/255,h4)`、
  `profiler_func::show_func(300/242,h6)`、`strategy::tick_worker_thread(268/247,h2)`、`main` 2 个、`scheduler` 等。
* 其中被 R37-B **彻底清零**的只有 2 个文件 / 1 个函数：`profiler_func::show_func`（300/242, h6 → 完全等值，
  文件 Σ 64→0）与 `email_utils`（3→0）。其余同族文件在该臂下形状不变（例：`tick_worker_thread 247/h2` 原样）。
* **EQ-TRANSPOSE（严格等长 ≥2 hunk）：5 个函数 / 4 个文件**：`fileio_utils::write 637/637 h4`、
  `graph::_process_task_queue 378/378 h3`、`logger::write_logging_thread 113/113 h2`、
  `scheduler::get_checked_time 106/106 h2`、`scheduler::on_next_day 57/57 h2`。
  这批是 R25 已诊断的 D3 同形块换位族，R37-B **没有**修好它们（`fileio_utils 12→44`、`scheduler 49→177` 反而更坏）
  ⇒ 「等长换位」与「臂越过祖先收敛点」是两条不同的判据线，不可混为一批。
* 结论：真正的「臂越过祖先 merge」暴露面 = `match` + `profiler_func::show_func` + `email_utils`
  （+ 部分改善 `api_base −12`、`real_quote −4`、`realtime_event_source −4`），
  **量级远小于**同判据带来的 19 文件回退。

---

## 6. 诚实的否证段（没有复现 / 被推翻的东西）

1. **机械侧假设再次死透**：`match` 与全部 7 个电池用例在两臂下 `_generate_degraded_statements` 命中 **0 次**、
   `_generate_region` 抛出异常 **0 次**、402 文件全量 0 fatal / 0 编译失败 / 0 `err`。
   「异常被吞 → 区域降级」在本残余上不成立（与编排方全量池结论一致）。
2. **R35-B（重复清理尾声抑制）不是这里的机制**：§1.3 证明尾部拷贝是被搬运并截断的同一段
   （253/259 对齐、0 逆序），而非「同一区域发射两遍后被抑制」。
3. **Round 29 §六「本族源码级 G0 见证原则上不可能」被推翻**：`battery/w2_witness.py`（22 行，仅 stdlib）
   在落地字节上复现等长换位（cost 2），在镜像 patched 核下归零。该断言的成因是当时只试了
   `r29x_01` 那种「分析器读原始布局」的形状；正确形状需要
   「循环内嵌套 if + 最内层 if 两臂都 `continue` + 祖先 if 的 else 体 + 祖先收敛点之后的兄弟语句」，
   而 `continue` 在 3.11 里把 merge 拉回循环头正是无界吸收的入口。
   但同族的 `w1_witness`（少一层嵌套）**未能**复现（landed 即 0）——复现阈值比想象的更窄，单个见证成立
   不代表该族有稳定的最小形状。
4. **候选自身的纯度瑕疵（违反本轮纪律的自供）**：
   (a) `exempt` 集用 `chain_blocks`/`then_succ`/`else_succ`，而**不含兄弟臂已认领的块**：`then_blocks`
   在 `:17177` 先算、`else_blocks` 在 `:17290` 后算，两臂的截断结果因此**不对称**，即带有一点
   「认领历史/遍历次序」味道——镜像 trace 里同一臂被收集两次而 exempt 不同（`[6,1110,1190,1194]`
   vs `[6,1068,1110,1190,1194]`）就是同一问题的表现；
   (b) 判据要真正变窄（只砍祖先收尾、不砍臂自身末句）需要在 `:17290` 时刻拿到**祖先 IfRegion 的 merge**，
   而祖先区域在 `:17957` 之后才建出（自底向上），只能靠 CFG 反推或改归约次序——本轮没有做出来。
5. **未测/未证**：
   * `match` 残余的 26 指令语句缺失（`is_first_five_trading_days = …`）根因**未查**，它独立存在于两臂；
     因此「R37-B 能把 match 推到 17/17」这一更强的期望**未被支持**。
   * 我定义的 Σ|Δ| 把「hunk 数」计入而把「hunk 尺寸」当 1，故它对 `match`（544→28 搬运 token 的塌缩）
     **不敏感**；全量语料的「搬运 token 总量」两臂对比**未测**（sweep 未存每 hunk 尺寸）。
     代价门之所以仍判 NO-GO，靠的是 official 池（partial 28→41、matched −23、Σdeficit 97→120）
     与 Σ|Δ| 1779→2694 两个独立指标。
   * `plugin_fly_data/strategy/strategy.pyc :: tick_worker_thread` 由并行代理负责，本文件未触碰其目标；
     `instance.pyc _init_config`（PROTECTED）在两臂下产物逐字节相同，未被扰动。
