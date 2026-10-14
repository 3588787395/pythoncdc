# FIX_R21-52 — inline_boolop_chains 成员块资格：被 POP_TOP 消费的推送值不是布尔操作数

工单：**R21-52**
目标单元：`<module>.RealtimeEventSource.clock_worker`
（`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`，13 单元，基 12/13）
镜像：`D:/Temp/r82`（仓库全程只读）
基（generator）：`core/cfg/region_ast_generator.py = 30a4d7827122e165`（r75 [R21-46] A+B on r74d）
analyzer：`core/cfg/region_analyzer.py = f7d849e974904492`（landed，本工单默认不改；若改另出 builder）

## 0. 镜像认证与基线复测（规则 6）

```
core/cfg/region_ast_generator.py  sha256[:16] = 30a4d7827122e165   （= 简报 base，MATCH）
core/cfg/region_analyzer.py       sha256[:16] = f7d849e974904492   （= landed，MATCH）
```
重新生成（`python -X utf8 pycdc.py --region -o work/base_evt.py <abs pyc>`，2.7 s）：
产物与仓库已存的 `rounds/round39/r75/PRODUCT_r75a_AB_on_r74d_realtime_event_sourceOK.py`
**逐字节相同**（`cmp` 无输出）。

`unit_diff.py --all`：
```
len orig=1424 prod=1426 delta=+2
== insert orig[1046..1046] prod[1046..1047] del=0 ins=1   + @7252 JUMP_FORWARD
== insert orig[1099..1099] prod[1100..1101] del=0 ins=1   + @7590 JUMP_FORWARD
hunks=2 landings=7 judge_diff=True
```
judge（`pyc_verify.py single --source`，fresh 产物）：
```
[single] status=failure units=12/13 success_rate=92.31%
  ***<module>.RealtimeEventSource.clock_worker: Failure: Different control flow
```
简报的 base 数字 **全部复现**：`delta=+2 / 2 windows / 7 landings / 12/13`。

## 1. 前提逐条复测（三条成立、一条因果链被实测否证）

用 `co_lines()` 把 **原始 pyc 自带的行号表** 打出来（`work/linemap.py`，原始源码行号是地面真值，
比任何反推都硬）：

```
@7164 L469 LOAD_FAST now_date / … / COMPARE_OP >        A = now_date > self.pre_before_trading_date
@7184 L469 POP_JUMP_FORWARD_IF_FALSE to 7216            ← A 的假出口 = C 的测试，不是链尾
@7186 L469 pre_before_trading<=now_time … pm_close<     B（链式比较）
@7210 L469 POP_JUMP_FORWARD_IF_TRUE  to 7248            ← B 的真出口 = 臂体入口 @7248
@7216 L470 self.pre_before_trading_date == self.initial_trading_date   C
@7246 L470 POP_JUMP_FORWARD_IF_FALSE to 7582            ← C 的假出口 = L482 的 elif
@7248 L472 now_date != self.first_run_date              D（**臂体内嵌套 if 的测试**）
@7268 L472 POP_JUMP_FORWARD_IF_FALSE to 7492            ← D 的假出口 = 臂尾 @7492，不是下一个 elif
@7270 L473 system_log.debug('获取重登信号量')  CALL @7298 **POP_TOP @7308**
@7310 L474 login_semaphore.acquire(...) is False        E
@7370 L474 POP_JUMP_FORWARD_IF_FALSE to 7492
@7372 L475..@7490 L477  error / put / return
@7492 L478 put(PRE_BEFORE_TRADING_START)  @7568 L479 pre_before_trading_date = now_date
@7582 L482 elif now_date > self.before_trading_date:    F
```
⇒ 原源码形状：`if (A and B) or C:` → 臂内 `if D: debug(); if E: …` → 臂尾 `put/store` → `elif F:`。

产物侧（`--prod work/base_evt.py`）：
```
@7164 L248 A ; POP_JUMP_IF_FALSE to 9206                 ← A 假出口落 loop 重测（landing #1）
@7188 L249 B or C ; POP_JUMP_IF_FALSE to 7254            ← C 假出口落 D 的测试（landing #3）
@7250 L250 EXTENDED_ARG / @7252 L250 JUMP_FORWARD to 9206   = 伪跳 #1（空 then 臂）
@7254 L251 D ; POP_JUMP_IF_FALSE to 7592                    = elif now_date != first_run_date
@7276 L252 system_log.debug('获取重登信号量')               ← **语句在产物里，未被吞**
@7588 L259 EXTENDED_ARG / @7590 L259 JUMP_FORWARD to 9206   = 伪跳 #2（臂尾）
@7592 L260 elif F
```

**前提复测结论**：
1. `inline_blocks=[7248,7270]` — **成立**。只读探针 `work/probe_regions.py`（跑完整 `gen.generate()`
   后读 `gen.regions`，不写文件、不改控制流）：
   ```
   IfRegion cond=7186 IF_ELIF_CHAIN elif_conditions=[7248]
       IBC op=and blocks=[7248, 7270]
       elif_final_else=[7492,7582,7604,7634,…]（44 块 = 函数尾，r78a 的承重量级一致）
   IfRegion cond=7216 IF_THEN then=[7248,7270,7492,7372,7488] else=[] merge=7582
   IfRegion cond=7270 IF_THEN_ELSE then=[7372,7488] else=[7492] merge=7582
   ```
   即 @7270 既是 ibc 成员，又是已声明区域 IfRegion@7270 的 condition_block。
2. 「line 249 的 then 臂是 `pass`」 — **成立**（产物 L250 = `pass`，编译出伪跳 #1 的
   `JUMP_FORWARD to 9206`）。
3. 「`debug()` 重现在下一个臂里」 — **成立**（L251 elif + L252 语句；简报写的行号 248/249
   与实际 251/252 差 3 行，方向与内容一致）。
4. **「折叠吞掉 @7270 ⇒ 语句消失」的因果链 — 在本字节上不成立**。基线已含 `[R21-46]`
   （`_r2146_ibc_member_has_stmt_prefix`，generator `:505`；消费点 `:20576-20580`），它对
   `op='and'` 且成员块带「未发射的完结语句前导」的记录 **既否决抬升又把成员块交还臂体**，
   这正是 `debug()` 出现在 L252 的原因。于是本工单要实现的规则（成员块被 POP_TOP 消费 ⇒
   不得吸收）与基线既有守卫命中**同一条记录、同一个结论**。
   ⇒ 必须先做的实测问题变成：**新判据相对 [R21-46] 是否有独立的可动面**（其他消费点 /
   其他语料记录），以及在此站点是否逐字节惰性。§3 census 回答它。

## 2. 规则（本工单唯一机制）

`[R21-52]`：ibc 折叠的**成员块**只有在其推送值被本链自己的后继条件跳转消费时才是布尔操作数。
成员块内在终结条件跳转之前出现 `POP_TOP`（丢弃返回值 = 一条完结语句的闭合）⇒ 该块是臂内顺序
内容（`语句; 下一个测试`），**从该成员起截断链成员资格**（连同其后成员），并把被截下的成员块
交还臂体（复用既有 `[R21-13]` 通道）。整条链的 `elif_conditions` / `elif_final_else` **不动**
—— 这是与已否证的 `[R21-49]`（break/return None 都在分析端动收集，−269）唯一的区别。
纯 opcode/栈形状判据，不读名字、偏移、计数器、阈值。

## 3. 人口普查（规则 2，编辑前；`work/census_r2152.py` 外部只读探针，20 面板文件全量）

探针 = 在 `RegionASTGenerator.generate()` 返回后枚举每个生成器实例的
`region.inline_boolop_chains`，对**每个成员块**算新判据，并**原样**调用既有
`_r2146_ibc_member_has_stmt_prefix` 记录其返回值（不改任何判据结果、不改控制流）。
惰性证明：20/20 探针产物与不挂探针的 `work/panel_base/` 逐字节相同（见
`DELIVER/CENSUS_20file_inert_probe.txt` 的 INERT 列）。

```
文件                        records members fire_new fire_only_new  r2146_eval r2146_fire
quotation                     48      57      0        0                1        0
quote                         14      16      0        0                1        0
klinedata                     27      31      0        0                0        0
handlers                       1       1      0        0                0        0
wizard_quant_api              13      13      0        0                0        0
trade_info_utils              14      16      0        0                0        0
api_base                      28      31      0        0                0        0
real_quote                    11      14      0        0                0        0
strategy                       0       0      0        0                0        0
order_api                      2       2      0        0                0        0
trade_live_broker             50      75      0        0                0        0
matcher                       14      15      0        0                3        0
realtime_event_source          4       5      1        0                1        1
__init__(risk)                 4       4      0        0                0        0
arg_checker x3                 2+2+2   2+2+2  0        0                0        0
profiler_func x3               4+2+4   4+2+4  0        0                0        0
------------------------------------------------------------------------
合计                          246     296     1        0                7        1
```
唯一 fire 就是本工单点名的记录：
```
FIRE unit=<module>.RealtimeEventSource.clock_worker head=7248 op=and
     blocks=[7248, 7270] refused=[7270] r2146_pred=True
```
⇒ **新判据的命中集合是既有 `[R21-46]` 命中集合的子集且等势（1=1，同一条记录、同一个成员块）；
`fire_only_new=0`：面板上不存在「新判据命中而 [R21-46] 不命中」的记录。**
既有站点级读数（`R2146CALL`）确认该记录在产物生成期被 `region_ast_generator.py:20577`
消费一次并返回 True —— 即折叠**今天已经被否决**，成员块 @7270 已交还臂体（产物 L252 的
`system_log.debug(...)` 就是它）。

结论（编辑前即可判定，仍按规则 3 实测坐实）：本工单的规则在此基线上**已经生效**，
它的实现面 = 「换一种说法重做同一个否决」。仍要跑实测的两问：
① 独立实现（置于 [R21-13]/[R21-46] 之前，直接作用于分析端原始记录）是否逐字节惰性；
② 同一判据搬到分析端（`_basic_inline_chains` 成员资格本身）会怎样 —— 这一条由 r78a 的
`-269` 占位，我在自己镜像里复测它（§5）。

## 4. 实现（`build_cand_r82a_r2152.py`，只改 generator，analyzer 保持 landed）

`[R21-52]` = 两处以字节级补丁插在基 `30a4d7827122e165` 上：

1. **新方法 `_r2152_ibc_member_is_operand(blk)`** —— 紧跟既有否证器
   `_inline_and_chain_exits_agree`（`region_ast_generator.py:19602`，[R21-13] 落地件）之后，
   同层同形：只读块内指令 + CPython 自己的 stack effect（`_instruction_stack_effect`，
   与既有切分器 `_split_block_condition_prefix` 同源）。
   判据：块末是指定条件跳转族（`FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS |
   NONE_CHECK_OPS`）时，前向模拟值栈深度；**若在终结跳转之前出现一条把栈带回入口深度 0 的
   `POP_TOP`，返回 False = 该成员不得吸收**。空块 / 块末非条件跳转 / 取不到栈效应 / 栈下溢
   ⇒ 一律 True（维持既有折叠），与 `_inline_and_chain_exits_agree` 的「只在测得矛盾时否决」同规。
2. **消费点**：`_if_generate_elif_chain` 的 elif 条件 ibc 查找处（基 `:20556`），插在
   [R21-13]/[R21-46] **之前**，作用于分析端原始记录：从第一个不合格成员起截断成员资格；
   余下 `kept>=2` 时用截短的副本继续折叠（不改分析端字典本体），`kept==1` 时置
   `_inline_chain_info=None`；被截下的成员块一律前接进既有 `[R21-13]` 通道 `_r2113_legs_back`
   交还臂体。`elif_conditions` / `elif_final_else` 一字不动。

`--probe` 变体（`e4fe94d918160cb4`）在真正改动前写 FIRE/EVAL 行；实测其产物与不挂探针逐字节
相同（下表现场读数），探针不参与判定。

## 5. 实测（规则 3：两处「家」各自单独测；A 惰性 ⇒ 无需配对）

| 变体 | 文件字节 | sha16 | delta | windows | landings | judge | 面板 changed files |
|---|---|---|---|---|---|---|---|
| 基 `30a4d782`（generator）+ landed analyzer `f7d849e9` | 3884461 | `30a4d7827122e165` | **+2** | 2 | 7 | `status=failure units=12/13` Different control flow | — |
| **A：generator 侧（本工单交付件）** | 3890265 (+86 行) | `32595f2b7e21f8b9` | **+2** | 2 | 7 | `status=failure units=12/13` Different control flow | **0 / 20** |
| A 的探针版 | 3890975 (+102 行) | `e4fe94d918160cb4` | 同 A | 同 A | 同 A | 产物与基**逐字节相同** | 0 / 20 |
| B：analyzer 侧（同一判据搬到成员资格本体，r78a 交付件 `8d9993219d2f7418` 在我镜像复测） | — | analyzer `8d9993219d2f7418` | **−269** | 4 | 2 | `status=failure units=12/13` | 1（目标，恶化） |

A 的现场读数（`--probe`，`R2152_CENSUS`）：
```
FIRE head=7248 op=and blocks=[7248, 7270] kept=[7248] dropped=[7270]
EVAL_TOTAL                 ← 该站点读到非空记录 1 次，fire 1 次
```
**A 的产物与基逐字节相同**（`cmp work/cand_evt.py work/base_evt.py` 无差异；面板
`changed files = 0 (of 20 panel files, missing=0)`）。机理：本规则的截断结果
`kept=[7248]`（<2 ⇒ 记录作废 + 成员交还臂体）与基上已生效的 `[R21-46]` 对同一条记录的
结论**完全一致**，所以新判据被前向折叠在同一处、同一结论上取代 —— 它不是「无效」，是「冗余」。

块归属唯一性（规则 1，`work/membership.py` 同一脚本，基 vs A）：
```
clock_worker : units=1 regions=67 blocks_in_block_to_region=191 two_owner=148 zero_owner=14
               held-distribution [(0,14),(1,29),(2,57),(3,31),(4,12),(5,8),(6,6),(7,12),(8,15),(9,2),(10,1),(11,3),(12,1)]
               候选 A：逐字段相同（regions/blocks/two_owner/zero_owner/分布 全等）
整文件 13 单元: regions=88 blocks=226 two_owner=159 zero_owner=30 —— 基与 A 相同
```
（我的 two_owner 定义 = 块出现在 ≥2 个区域的体列表中；r78a 报的 186 用的是它自己的计数口径，
两者不可混用。关键读数不变：**候选不新增任何 two_owner/zero_owner 违例，原则 2/4 保持**。）

接受栏（A 的产物，fresh judge）：
```
realtime_event_source  status=failure units=12/13   ← 未翻正
trade_live_broker      status=failure units=126/128 ← 未下降
quote.pyc              status=success units=92/92
quotation.pyc          status=success units=153/153
order_api.pyc          status=success units=37/37
面板 20 文件产物 changed files = 0
```

## 6. 判据该住在哪一侧（工单要我定，且要用普查而不是图省事）

**结论：generator 侧（`_inline_and_chain_exits_agree` 旁边），且只有那一侧是安全的；
但两侧都到不了 13/13。** 依据：
- 普查（§3）：20 面板文件 246 条 ibc 记录 / 296 个成员块求值，新判据 **fire 1 条**，且
  `fire_only_new=0` —— 唯一命中正是 `[R21-46]` 已在 `:20577` 否决并交还臂体的那条记录。
  即：**这条规则在语料可观测面上没有独立作用点**，它描述的是基线已经做对的事。
- generator 侧实现（A）逐字节惰性，风险为零；analyzer 侧实现（成员资格本体，即
  `_check_elif_chain` 的 and-walk `region_analyzer.py:22072-22123`，`_basic_inline_chains`
  在 `:21399-21406` 只是把该 walk 的结果存入区域）在我镜像里实测 **delta −269 / 4 窗 / 2 landing /
  12/13**：截断 walk 使 `len(_inline_chain)<2` ⇒ `inline_boolop_chain=None` ⇒
  `inner_condition_block` 落回 `@7248` 自身，下游 `inner_merge`/d2 守卫随之放弃整条 `@7186`
  展平，而该链的 `elif_final_else` 是 **44 块 = 整个函数尾**（探针读数见 §1 前提 1），尾部
  失去发射。与 r78a 的 −269 一致（口径：同一 analyzer 字节 `8d9993219d2f7418`，我用基
  generator `30a4d782` 复跑）。⇒ 分析端是**已证的回归家**，不是省事与否的问题。

## 7. 判定：FALSIFIED（惰性/冗余），不安装

- 工单的三条前提：`inline_blocks=[7248,7270]` **成立**；line 249 的 `then` 臂是 `pass`
  **成立**；`debug()` 重现在下一个臂 **成立**（实际行号 251/252，简报写 248/249）。
- 工单的**因果**前提不成立：语句没有被吞。基线的 `[R21-46]`（`_r2146_ibc_member_has_stmt_prefix`
  + `_r2113_legs_back`）今天已经在同一处、以同一结论否决了这条记录的折叠；因此
  「拒绝吸收 POP_TOP 消费的成员块」= 把已生效的否决换个说法再写一遍，产物 0 字节变化。
- 「语句恢复但两个跳转仍在」的准确表述：**语句本来就是恢复的**（产物 L252），
  两个 `JUMP_FORWARD → @9206`（产物 @7252 / @7590）**原样存活**，7 条 landing 一条不少，
  judge 仍 12/13。

## 8. 仍开放的机理（按我的实测重排，非简报原序）

`pass` 臂和两条伪跳的**直接成因不是 @7270 的成员资格，而是 @7248 本身被收成 `@7186` 链的
elif 条件**（探针：`IfRegion cond=7186 IF_ELIF_CHAIN elif_conditions=[7248]
elif_bodies=[None] elif_final_else=[7492,7582,…]`，而 `@7248` 的真实身份是
`IfRegion cond=7216 IF_THEN then=[7248,7270,7492,7372,7488] merge=7582` 的臂内嵌套 if）。
于是父臂体为空 ⇒ `pass` ⇒ 臂尾必须跳链尾（伪跳 #1）；D 臂的尾巴同理（伪跳 #2）。
两条可检验的结构事实（都不需要名字/偏移）：
① `@7248` 的**假出口 `@7492` 落在父臂体内部**（`@7492 ∈ IfRegion@7216.then_blocks`），
   不是链的下一个臂 —— 这是「嵌套 if」而非「elif」的判据；
② `A` 的假出口 `@7216` 是 `C` 的测试（`(A and B) or C` 的一元 or 提升），基产物把它落到
   链尾 `@9206`（landing #1/#3），这一条独立于 ①。
①属 [R21-49] 已证的「链是函数尾承重结构」家族，②属 [R21-44] 的 or-tail 家族（−274），
两条都已在本单元被否证；本工单没给它俩新读数，只排除了「成员块 POP_TOP 资格」这一条轴。

## 3bis. 语料级判据面普查（比 20 面板更强；`work/census_corpus.py`，只跑分析端不生成 AST）

对 site-packages 全部 406 个真实输入 .pyc（排除 `__pycache__`）的**每个 code object**：
`RegionAnalyzer.analyze()` → 枚举全部 `IfRegion.inline_boolop_chains` → 对每个成员块算
新判据 + [R21-46] 的切分器半边。基字节：generator `30a4d782` / analyzer `f7d849e9`。

```
files=406  UNREADABLE=1（一个 pyc marshal 失败，不计入）
CORPUS records=570  members=664  fire_records=1  fire_without_r2146_prefix=0
HIT realtime_event_source.pyc :: <module>.RealtimeEventSource.clock_worker
    head=7248 op=and blocks=[7248, 7270] refused=[7270] r2146prefix=[7270]
```
⇒ **整个语料只有 1 条记录命中本规则，而它同时是 `[R21-46]` 前导判据命中的同一条。**
「新判据相对既有守卫没有独立作用面」不再是 20 面板的外推，而是 402 文件的实测。

## 9. 下一张工单可用的判据（我这次实测顺手拿到的，不在本工单范围内跑）

`DELIVER/REGION_probe_base_clock_worker_7100_7700.txt` 的两行同时成立：
```
IfRegion cond=7216 IF_THEN then=[7248,7270,7492,7372,7488] else=[] merge=7582
IfRegion cond=7186 IF_ELIF_CHAIN elif_conditions=[7248] elif_bodies=[None]
             elif_final_else=[7492, 7582, 7604, …]（44 块）
```
即 `@7248`（被收作 elif 条件）的**假出口 `@7492` 同时是父臂 `IfRegion@7216` 的 then 块**，
又被列进链的 `elif_final_else`。结构判据（不读名字/偏移/阈值）：
**elif 条件的假出口落在本臂体内 ⇒ 它是臂内嵌套 if，不是 elif**；父臂因此不该被判空。
本工单没跑它（属 [R21-49]/[R21-44] 的承重链家族，需先解决「摘出 @7248 后 44 块函数尾失去
归属」这一条，那才是 −269/−274 的真实原因）。

## 10. 交付与仓库状态

交付见 `D:/Temp/r82/DELIVER/`：FIX 文档、`build_cand_r82a_r2152.py`（基 `30a4d7827122e165`
字节级重建，`DELIVER/BUILD_rebuild_proof.txt` 证明重建与实测候选**逐字节相同**）、
候选（`32595f2b7e21f8b9`）+ 探针候选（`e4fe94d918160cb4`）、实测产物（base/candA/candB）、
20 面板与语料 census、site-level FIRE 读数、membership base/candA、allwin 两窗证据、
region 探针转储。未写 analyzer 候选 ⇒ 无第二 builder（B 用 r78a 交付字节 `8d9993219d2f7418`
在我镜像复测，非我改写）。
仓库全程只读：`git status --porcelain -- core/ scripts/ site-packages/ parsers/ utils/
bytecode/ pycdc.py` = 空。镜像已还原 base（generator `30a4d7827122e165` /
analyzer `f7d849e974904492`）。**建议：BANK，勿安装**（惰性候选，安装只增加 86 行而没有
任何可观测效果；语料 570 条记录里唯一命中的那条已被既有守卫处理）。
