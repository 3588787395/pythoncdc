# FIX_R21-49 — clock_worker：拒绝把嵌套 if-D 的测试块 @7248 收集为 @7186 链的 elif

工单：**R21-49**
目标单元：`<module>.RealtimeEventSource.clock_worker`
（`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`，13 单元，当前 12/13）
镜像：`D:/Temp/r78`（仓库全程只读）
基（generator）：`core/cfg/region_ast_generator.py = 30a4d7827122e165`（= r75 [R21-46] A+B on r74d）
analyzer：`core/cfg/region_analyzer.py = f7d849e974904492`（本工单在分析端改 elif 收集）

## 0. 前提复测（规则 6：简报逐条重测，全部在 `D:/Temp/r78` 干净镜像里跑）

镜像认证（sha256[:16]）：
```
core/cfg/region_ast_generator.py  = 30a4d7827122e165   （= 简报 base，MATCH）
core/cfg/region_analyzer.py       = f7d849e974904492   （=  landed，MATCH）
```

基线复测（`work/vmeasure.py base`）：
```
len orig=1424 prod=1426 delta=+2
hunks=2 landings=7 judge_diff=True      （unit_diff --all）
window #1: insert spurious JUMP_FORWARD @7252（orig[1046]，@7248 POP_JUMP_IF_FALSE 之后）
window #2: insert spurious JUMP_FORWARD @7590（orig[1099]，@7582 之后）
judge: status=failure units=12/13  Different control flow
```
简报 base 数字 **全部复现**：`delta=+2 / 2 windows / 7 landings / 12/13`。两窗各是一条伪 `JUMP_FORWARD`。

### 前提 A：`IF_ELIF_CHAIN@7186` 收集 `@7248` 为 elif，但把 `@7248` 的真实 true successor 漏在体之外（实测 census）
```
CHAIN entry=7186  conds=[7248]  bodies=[[7372, 7488]]  final_else=[7492, 7582, ...]
  cond@7248 last=POP_JUMP_FORWARD_IF_FALSE true_succ=7270 false_succ=7492
          assigned_body=[7372, 7488]   true_in_body=False      ← @7270 被链跳过
```
确认：`elif_bodies=[[@7372,@7488]]` 不含 `@7248` 的真实 true successor `@7270`。

### 前提 B：错误发生在「收集」本身 —— inline `and` 布尔链把携带语句的 `@7270` 折进条件（实测探针）
探针（`work/_probe_analyzer.py`，仅加一条 stderr print，行为不变）：
```
[PROBE elif] header=7186 first_else=7248 inline_op=and inline_blocks=[7248, 7270] inner_cond=7270
```
即 `_check_elif_chain` 把 `@7248` 的 true successor `@7270` 当作 `and` 短路链的第二操作数折进条件，
于是 `inner_condition_block` 变成 `@7270`、链为 `@7248` 分配的臂体从 `@7270` 之后（`@7372`）开始。
但 `@7270` **不是纯条件块**：它含一条 `CALL → POP_TOP`（`debug()` 语句，其结果被丢弃）再跟 `if E:` 测试。
POP_TOP 丢弃栈值 = 一条独立语句 ⇒ `@7270` 是臂内顺序内容（`debug(); if E:`），不是 `A and B` 里的操作数。
折进条件 ⇒ `debug()` 语句被吞 ⇒ 这正是简报「@7248 不是 @7186 的 elif，而是 @7216 臂内嵌套 if-D」的根因，
且落在 **elif 收集（inline-and 折叠）** 这一层，不在过滤器/发射层。

### 前提 C：同形例 @6846 是**合法** elif，必须不被拒（over-fire 面）
```
CHAIN entry=6280  conds=[6846]  bodies=[[6890, 7048]]  final_else=[]
[PROBE elif] header=6280 first_else=6846 inline_op=None inner_cond=6868
```
`@6846` 的 `true_succ=@6868` 同样不在体 `[6890,7048]` 里（`true_in_body=False`，与 @7248 同形），
但 @6868 是 **纯测试块**（LOAD/COMPARE/POP_JUMP，无 CALL/POP_TOP/STORE），且 @6846 走的是
**预建 BoolOpRegion 路径**（`block_to_region[@6846]` 是 BoolOpRegion，`inline_op=None`），
不是 inline-and walk。⇒ 只真 `A and B`。判据必须只命中 walk 折进「带语句的臂入口」的情形。

### 前提 D：@6868 与 @7270 的判别（结构事实）
- `@6868`（@6846 的操作数）：5 条指令，无 POP_TOP、无 STORE、无独立 CALL-语句 ⇒ 纯条件操作数，折叠合法。
- `@7270`（@7248 的臂入口）：17 条指令，含 `CALL; POP_TOP`（debug() 语句）⇒ 臂内容，折叠非法。
判据取材：`_ft_next.instructions` 是否含 POP_TOP（丢弃值的语句闭合）——与 landed walk 的 STORE 判据同域同层。

## 1. 真实源码形状（r76 §5 compile() 反证，直接引用）
`SHAPE_topology_site7164.txt`：site `@7164` = `if A and B or C:` → then 臂内 `if D: debug(); if E: … ; <@7492 顺序语句>`。
`@7492` 是 D/E 共享续体（`self.pre_before_trading_date=…`），不是 E 的 else。

## 2. 机制（单件，correct-at-identification）
`[R21-49]`：在 `_check_elif_chain` 的 inline `and` walk（region_analyzer.py:22094 STORE 判据同处）追加一条
「纯条件块」核验：`_ft_next`（候选 elif 条件的 true successor / 臂入口）若携带 **POP_TOP**（丢弃返回值的语句），
它就是臂内顺序语句而非短路链操作数 ⇒ 本 `first_else` 的平坦 elif 解释不成立 ⇒ **弃权整条 elif 展平（return None）**。
调用方 `_build_elif_region` 见 `elif_info is None` 即 return None，`_identify_conditional_regions` 回退
`_build_basic_if_region` 按 IF_THEN_ELSE 建 `@7186`，`@7248` 不再落在任何链的 `elif_conditions`，
过滤器（1672-1691）不再删除 `IfRegion@7248` ⇒ `@7248/@7270(debug(); if E)` 作为 @7216 臂内嵌套 if 正确发射。

## 3. 判据依据（结构事实 / 保守性 / 可证明性，非偏好）
- 结构事实：`A and B` 短路链的每个成员求值结果都被后续 POP_JUMP 消费，绝不出现 POP_TOP（丢弃值）。
  折叠成员一旦出现 POP_TOP，即证明它是「先执行一条语句、再做下一测试」的臂内序列，不是布尔操作数。
- 保守性：命中即 `return None` 走既有 IF_THEN_ELSE 回退，不新增区域类型、不新增 AST 节点、无跨级回补；
  其余链（@6280 走 BoolOpRegion 路径、@8592/@8294/@7634/@1742 inline_op=None）逐字节不变。
- 取材面：仅 `first_else` 自身 walk 中选出的 `_ft_next.instructions`（opname 集合含 POP_TOP）；
  不读名字/常量/绝对偏移、不读计数阈值、不读兄弟区域、无历史清单。无函数名、无绝对偏移。

## 4. 人口普查（规则 2，编辑前，实测）

惰性探针 `work/_census_probe.py`（仅加 stderr print，无控制流改变）跑 20 面板文件
（`DELIVER/CENSUS_20file_inert_probe.txt`）：
```
TOTAL_EVAL=230  TOTAL_FIRE=1  changed_files(vs base)=0     ← 探针惰性证明：20/20 产物逐字节 = base
```
命中逐文件分布（仅 realtime_event_source 触发）：
```
realtime_event_source   EVAL=3   FIRE=1   SAME
quotation 57/0  quote 18/0  klinedata 24/0  wizard 55/0  ...  其余 18 文件 FIRE=0
```
fire 明细（`DELIVER/CENSUS_fire_detail_realtime.txt`）：
```
[R2149-EVAL] header=7634 fe=8592 ft=9218        (无 fire)
[R2149-EVAL] header=7186 fe=7248 ft=7270
[R2149-FIRE] header=7186 fe=7248 ft=7270        ← 唯一 fire：@7248 的臂入口 @7270 含 POP_TOP
[R2149-EVAL] header=7186 fe=7248 ft=9218        (无 fire，@9218 无 POP_TOP)
```
@6280 链 @6846（同形 over-fire 面）**不触发**：它走预建 BoolOpRegion 路径（inline_op=None），
不经 walk，故 @6868（纯操作数）不被本判据波及——正是要保住的合法 elif。
⇒ 判据 230 评估 / 1 fire / corpus-唯一 / 探针惰性；字节变更面（见 §5）：fire 只改 realtime_event_source 一个文件。

块归属唯一性（规则 1，`work/membership.py`，DELIVER/MEMBERSHIP_{base,break}.txt）：
```
base  : regions=67 blocks=191 two_owner_blocks=186 zero_owner_blocks=0  IfRegions@entry=7248 = 0
break : regions=67 blocks=191 two_owner_blocks=186 zero_owner_blocks=0  IfRegions@entry=7248 = 0
```
两_owner 计数 base 与候选**完全相同（186）**：拒绝收集不新增任何「一个块两 owner」违例
（`block_to_region` 是 dict，唯一归属恒成立；186 是区域 `.blocks` 嵌套重叠的既有计数，非原则 2 违例）；
zero_owner=0；@7248 的 IfRegion base 亦为 0（证实 r77a/简报前提 A：@7248 若Region 被过滤器删除，
@7248 ∈ CHAIN@7186.elif_conditions，`@7248 final owner=TryExceptRegion`）。原则 2/4 保持。

## 5. 构建器与 2×2 实测（规则 3）

`build_cand_r78a_r2149.py` 从 landed analyzer `f7d849e974904492` 逐字节重建两半（generator 基 `30a4d782` 不动），
打印 sha16 前后，并断言重建字节 == 实测字节（**两半均 True**）：
```
CANDIDATE_r78a_r2149a_breakFold  sha16=8d9993219d2f7418   (= 实测 _break.py  True)
CANDIDATE_r78a_r2149b_refuseChain sha16=5897b1e594bbffa6   (= 实测 _refusal.py True)
```

| 变体 | delta | windows(allwin) | landings | judge | vs base 产物 |
|---|---|---|---|---|---|
| base `30a4d782`（generator）+ landed analyzer | **+2** | **2** | **7** | `status=failure units=12/13` Different control flow | — |
| 半件 A（break：臂入口含 POP_TOP ⇒ 中断 and-fold） | **−269** | 4 | 2 | `units=12/13` Different control flow | **DIFF**（仅 realtime_event_source） |
| 半件 B（return None：拒绝整条 @7186 elif 展平） | **−269** | 4 | 2 | `units=12/13` Different control flow | **DIFF** |
| 配对 A+B | == B（A 被 B 蕴含，无独立产物） | 4 | 2 | `units=12/13` | — |

**两半产物逐字节相同**（A 的 `break` 让臂入口 @7270 不再被折，触发下游 inner_merge/d2 守卫同样放弃整条
@7186 展平；故与 B 收敛到同一 product）。20 面板字节变更（`DELIVER/CENSUS_20file_break_bytediff.txt`）：
`changed_files=1`，且那唯一变化文件是**目标本身、方向是恶化**（+2→−269，12/13→12/13）。
接受栏 5 文件在候选产物下（实测 `DELIVER/MEASURE_*` + 下方 §6）：broker 126/128、quote 92/92、
quotation 153/153、order_api 37/37 全部**未变**（其余 19 面板文件逐字节 = base），realtime_event_source **仍 12/13**。

## 6. 结论：FALSIFIED（回归），机制仍开放

- **前提 A/B/C 全部复现**（chain @7186 误把 @7248 收成 elif、把臂入口 @7270（含 debug() 的 POP_TOP 语句）
  折进短路 `and` 条件、体 `[7372,7488]` 漏 true successor @7270），判据 **230 evals / 1 fire / corpus-唯一 /
  惰性 / 归属唯一性无新增违例** —— 这一侧的全部硬指标都干净。
- **但拒绝该收集不翻正**：@7186 是单 elif 链（conds=[7248]），其 `elif_final_else` = 44 块 =
  **整个函数尾**（@7492/@7582/@7634…/@8592…/@9144）。一旦 @7248 的 and-fold 被拆（break 或 refuse），
  @7186 展平被放弃 → 尾部整段失去发射 → **delta 从 +2 崩到 −269**（销毁 ~269 条指令），judge 仍 12/13。
  与简报点名的已否证轴（⑧ 放宽 −274/−269 级灾难）同量级，机理不同但结局一致。
- **根因不是过滤器/发射，也不是纯收集**：@7248 与 @7216 的 `if D` 属 @7164 的 **then 臂**，
  却因 jump-threading 被 @7164 的 **false 臂链 @7186** 认领；@7186 这条链「错拿 @7248」与「独占函数尾」
  是同一份 final_else 的两面。识别期把 @7248 摘出去，就同时摘走了它身后 44 块的归属。
  ⇒ **简报的 reframe（唯一最后阻塞 = elif 收集）在本字节上不成立**；残差仍是 **jump threading**
  （base 的两条伪 JUMP_FORWARD @7252/@7590），即 r77a 抵达的、需 20 面板 + judge 定夺的那一类。

**已否证（勿再跑）本工单新增**：`_check_elif_chain` inline-`and` walk 层面对臂入口 POP_TOP 的
（a）`break`（不折 @7270）与（b）`return None`（拒整条 @7186 展平）——二者字节相同产物，
均 delta −269 / 12/13 / changed_files=1（目标回归）。@7186 链是尾发射的承重结构，不可从收集侧解耦。

**仍开放的机制（据实测）**：base 的 2 窗是 @7164/@7186 站点 [R21-44] 平折后的**两条伪前向跳转**
（@7252、@7590）；这属 generator/发射的 jump-threading 落点，不在 elif 收集层。若继续 clock_worker，
需在不触碰 @7186 承重链的前提下、就这两条臂尾伪 JUMP_FORWARD 定发射判据——但简报已点明
「generator 无 landing 通道」，故此路可能仍不可动。

## 7. 交付物（D:/Temp/r78/DELIVER/）
- FIX_R21-49_elif_misCollection_clock_worker.md（本文件）
- build_cand_r78a_r2149.py + BASE_generator_30a4d7827122e165.py（基见证）
- CANDIDATE_r78a_r2149a_breakFold_analyzer_on_base.py（半 A，8d9993219d2f7418）
- CANDIDATE_r78a_r2149b_refuseChain_analyzer_on_base.py（半 B，5897b1e594bbffa6）
- PRODUCT_base_30a4d782 / PRODUCT_r78a_break / PRODUCT_r78a_refuse …realtime_event_sourceOK.py
- CENSUS_20file_inert_probe.txt（230 evals/1 fire/0 changed）、CENSUS_20file_break_bytediff.txt（1 changed）
- CENSUS_fire_detail_realtime.txt、MEMBERSHIP_{base,break}.txt（186/0 两_owner/零_owner）
- MEASURE_base.txt / MEASURE_halfA_break.txt / MEASURE_halfB_refuse.txt

## 8. 仓库状态
仓库全程只读：未写 `core/`、`scripts/`、`site-packages/`、`.trae/`。镜像已还原到 base
（generator `30a4d7827122e165`、analyzer `f7d849e974904492`）。**建议：BANK，勿安装**（目标回归 −269）。
