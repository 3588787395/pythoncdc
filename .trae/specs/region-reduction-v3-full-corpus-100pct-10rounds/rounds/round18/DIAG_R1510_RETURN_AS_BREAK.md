# DIAG R15-10 — 循环内「只有 return 的臂」被发射成 break，并吞掉臂后语句

## 目标单元

`site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc` ::
`<module>.PluginRiskCalculation._save_testds_to_csv`（orig 80 指令 / 产物 73，
内容差 3 hunk，落点差 10）。同文件另一失败单元
`_on_publish_after_trading_end`（528/524，内容差 3）——本票只解释前者。

## 实测证据（orig `dis` 行号 + 产物源码并读）

orig 关键段（`dis` 口径，忽略 NOP/CACHE/EXTENDED_ARG）：

```
@276..@286  from ...function import THREAD_STATUS       line=870
@288 LOAD_FAST THREAD_STATUS                             line=871
@290 POP_JUMP_FORWARD_IF_FALSE  to 296
@292 LOAD_CONST None ; @294 RETURN_VALUE                 line=872   ← 源语句 return
@296 LOAD_GLOBAL NULL+time; LOAD_ATTR sleep; LOAD_CONST 0.01; CALL; POP_TOP   line=874
@336 LOAD_FAST self; LOAD_ATTR _stop_save_csv_thread …   line=869   ← 循环回边
```

产物（`site-packages/.../__init__OK.py:536` 起）同一段：

```
while not self._stop_save_csv_thread:
    from IQEngine...function import THREAD_STATUS
    if THREAD_STATUS:
        break            # ← 应为 `return None`
break                     # ← 臂后的 time.sleep(0.01) 与回边尾部整体丢失
```

字节差分对应：产物在 @264/@266 **插入**一对 `LOAD_CONST None; RETURN_VALUE`
（那是 `while…else: return None`，正确），在 orig @292..@334 处**删除** 8 条
（return 对 + `time.sleep(0.01)`）只留一条 `JUMP_FORWARD`，并在 @354/@356 再删一对 stub。

## 形状判据（本票要立的规则，尚未实现）

臂块的**末条指令是 RETURN_VALUE**（且本块无后继）⇒ 该臂在源码里是 `return`，
不可能是 `break`：`break` 编译为跳向循环出口汇合块的前向跳转，而
`RETURN_VALUE` 是直接结束整个 code object。当前发射路径把这条臂认成 break，
并同时丢掉臂后的循环体尾部语句（`time.sleep(0.01)` 与回边续体）。
⇒ 判据应读：臂尾 opcode 类别（RETURN_VALUE / RETURN_CONST）与该块后继集合，
不读名字、常量、偏移、条数（rules.md §1.5 G4/C1/C2）。

## 风险评估（为何本轮不贸然动手）

Break 语句在生成端有 **至少 12 处**相关判定点（`:6161/:6308/:6314/:6904/:6906/:6909/
:6921/:6939/:6958/:7909/:8176` 等，多为「臂体恰为 Break」的形状改写/收敛条件），
把 return→break 的混淆点混在这些收敛条件里；单点改判据 = 局部修，
且极易在循环家族上大面积回归。⇒ 先做**最小复现电池**（`while…else: return` +
`if cc: return` + 臂后语句的 6–10 行形），确认唯一发射点后，再按
「一处判据、多点复用」改造；复现电池与本案同批交付。

## 与 handlers 票的关系

`handlers.TWHThreadController._target` 的残差是「同一循环的两条出口边各落一条
纯 None-return stub，产物只落一条」；本案是「return 臂被认成 break」。
两者都指向**循环出口汇合身份**，但机制不同：handlers 的产物源码里
`return None` 已在（三个剥离守卫消融后读数逐字节不变），本案的产物源码里
根本没有 return（写成 break）。handlers 票面已登记三个被否守卫。

## 最小复现电池首跑（D:/Temp/r150/run_retbreak.py，只判 pycdc 产物）

| 例 | 源形 | 判决 | 产物实际形状 |
|---|---|---|---|
| r01_return_arm_then_tail | `while True: while not stop: if flag: return; sleep; if stop: return  else: return` | **RED 1/2** | 外层 while 被吃掉，两条 `return` 变 `break`，尾部 `return None` |
| r02_break_arm_control | 同骨架但臂体本就是 `break` | **RED 1/2（控制例也红 ⇒ 该控制无效）** | `while…else:` 的 else 子句整体丢失 |
| r03_return_in_else_suite | try/except/continue + else 内 return + 臂后 sleep | GREEN 2/2 | — |
| r04_two_return_arms | 单层 while，两条 return 臂 + 臂后语句 | GREEN 2/2 | — |

⇒ 两个互异缺陷纠缠：
- **缺陷 A**（r01）：外层 `while True:` 被消除后，内层臂的真 `return` 被发射成 `break`；
- **缺陷 B**（r02）：`while…else:` 的 else 子句在「外层 while True + 内层 while + else」骨架下丢失。
r02 之所以不能当控制例，正是因为骨架里同时触发 B；下一版电池必须把
「臂体=break 且无外层 while True」与「臂体=return 且无外层 while True」配对，
才能把 A 单独钉死（r04 已证明无外层 while True 时 return 臂是对的 ⇒ A 只在 B 的
外层循环消除路径上出现）。

## 发射路径已定位（读码）

`region_ast_generator.py:6296-6330` 存在 **break→return 折回**机制
（`_break_to_return_map` + `_fold_break_to_return`，把臂体恰为 `Break` 的 If 改写成
Return），其反向说明「先发射 break、事后按汇合块身份折回 return」是本项目的既有做法；
角色判决点在 `:13280`（「RETURN/RETURN_NONE → Return；既非 BREAK 也非 RETURN 角色 → 裸 Break」）
与 `:12178`（「CPython 把…生成 Break 而非 Return」）。
⇒ A 的正解应在**角色判定的识别端**：臂块末指令为 RETURN_VALUE/RETURN_CONST 时不得记 BREAK 角色；
在生成端再补一次折回属回溯修正（违反原则 5），且与既有 12 处 Break 判定点纠缠。
