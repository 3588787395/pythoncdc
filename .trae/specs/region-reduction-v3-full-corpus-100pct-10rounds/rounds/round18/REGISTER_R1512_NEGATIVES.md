# REGISTER R15-12/11 + R14-05 —— 三条负结果与第 19 轮票面

本轮（会话）已落地并认证的只有 R14-04（门链 label 18：units 6583→6584、files 390、
回退 0、翻正 1，提交 `1577a2b0`/`a9dedc29`/`12378d5e`，checks 已登记）。
以下三条为**实测负结果**，全部未落地，core 保持 `5066b1367b6de3c7`。

## 1. R14-05（镜像修理工，跑了 150 子轮后达上限中止）

交付物：`D:/Temp/r160/deliver/region_analyzer.py`（相对当前 core `+221 −5` 行）。
新增识别端 helper：`_r16_cc_cleanup_hop`、`_r16_boolop_cc_run_operand`、
`_r16_cc_operand_success_edge`，接入点：merge 计算族（cur 19675 / 19717 / 19757）、
臂归属（cur 20680）、`_boolop_resolve_merge`（cur 27998）、链走认领守卫与尾钳
（cur 29792 / 29975 / 29977 / 30010 / 30093）、链末成员（cur 30537）。

自述判决：**验收门第 1 步未过（repro_arm a01/a02/a03 未达 2/2），且该补丁使
api_base 回退**。我方的独立复判（不读子代理叙述，只判它自己产出的产物）：
20:07 与 20:13 两次读取 `a01/a02/a03` 均为 `status=failure units=1/2`
⇒ 与其自述一致。⇒ **不安装**；补丁与结论留档，避免下一轮重复同一实现。

## 2. R15-11（try 体尾已终止 ⇒ 不追加函数隐式 return）

判据：`region_ast_generator.py:28738-28748` 的 `_is_inlined_ret` 分支加
「发射尾部已是 Return/Raise」守卫。A/B（`D:/Temp/r150/retguard_rig.py`）：

| 文件 | 封盘 | 施加 R15-11 |
|---|---|---|
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | 43/45 | **43/45（不变）** |
| `IQEngine/core/strategy/strategy.pyc` | 20/20 | 20/20（未回退） |
| `IQCommon/util/trade_info_utils.pyc` | 38/41 | 38/41（不变） |

⇒ `get_real_minute_kline` 多发射的那对 `LOAD_CONST None; RETURN_VALUE`
**不是**由 `_is_inlined_ret` 分支产生的 ⇒ 发射点另有其处（候选：同段
`_is_cond_jump_target` 分支，或 try 体之外的链尾发射）。本票登记为「分支选错」，
下一步应先用消融确定实际发射分支，而不是再叠守卫。

## 3. R15-12（逐臂 continue：臂末块跳回 continue 落点即补 `continue`）

动机：`klinedata.get_kline_by_count_new` 内容差 1 处 —— orig `@2926 JUMP_BACKWARD`
（`if symbol_four not in dividends_stock: 赋值; continue` 的臂尾），产物为
`@2924 JUMP_FORWARD`（链尾统一一条 `continue`）。放宽 [R3-Continue]
（`region_ast_generator.py:21378-21391`）的 `merge_block is 循环头` 前置后：

| 文件 | 封盘 | 施加 R15-12 | 结果 |
|---|---|---|---|
| `IQCommon/api/klinedata.pyc` | 63/64 | **51/64** | −12 回退 |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | **111/128** | −7 回退 |
| `IQCommon/logger/handlers.pyc` | 29/30 | **28/30** | −1 回退 |
| user_info_utils / fly_basicdata/basic_data_source / local_finance / basic_data_source / IQEngine/core/strategy / api_base / strategy | 9/9、43/43、21/21、8/8、20/20、27/28、26/27 | 同封盘 | 不变 |

⇒ 目标单元未翻正，反而 −20 单元 ⇒ **立即回退**（已强制还原 `5066b1367b6de3c7`，
`py_compile` 通过，`git status -- core/` 空）。
结论：**`merge_block is 循环头` 这条前置是承重的**，与 `[21372-21377]` 早已登记的
「整个 R3-Continue 块不可删（删之净 −3 函数）」互相印证：该补发判据的正确收紧方向
是「更少发射」而非「更多发射」。下一版判据必须给出**臂级**区分事实（例如本臂末块跳回
目标 == 循环头，且**另一臂/merge 路径不再被链尾 continue 覆盖**），
并先在 `repro/` 级别把 klinedata 形与回退形分开复现，再谈改 core。

## 4. 第 19 轮票面（按距整文件翻正的距离排序）

1. `api_base` 27/28：0 内容差 + 2 处落点（`@994→1098`、`@1006→1040` 被并成 `1254`）
2. `strategy`（fly_data）26/27：0 内容差 + 4 处落点（`@522/@534→568`、`@992/@1004→1038`）
3. `klinedata` 63/64：1 处内容差（臂尾 continue）+ 12 处落点
4. `handlers` 29/30：源形状搜索（产物源码编译只得 6 条 stub，原始 7 条）
5. `realtime_event_source` 12/13：需共要件（批量认领抑制）+ 重定位判据两条
6. `real_quote` 43/45：两处 1 指令过发射，发射分支待定（先消融定位）
7. `trade_live_broker` 118/128：臂身份读反族（−465/−293）

## 5. R15-12 窄化版实测（补充）：零回退但零翻正 ⇒ 惰性，站点未命中

`merge_block is 循环头` 前置保留、只加「双臂 if 且臂末块跳回当前循环 header/condition」
一支后，11 文件面板读数与封盘**逐文件相同**（klinedata 仍 63/64、broker 118/128、
handlers 29/30、quote 86/92、user_info_utils 9/9、fly_basicdata 43/43、local_finance 21/21、
IQEngine/core/strategy 20/20、api_base 27/28、strategy 26/27、real_quote 43/45）
⇒ 判据没走到实际装配点。识别端实测（只读 analyze）给出目标区域事实：

```
IfRegion entry=2802 cond=2802 merge=3076
  then=[2894,2898,2902,2916,2924]  else=[2928,3050,3054,3068]  elif_conds=[] elif_bodies=[]
  臂末块 @2924 尾指令 JUMP_BACKWARD -> 1268
外层循环 LoopRegion entry=1268 header=1268 condition_block=None
父链 IfRegion entry=2742 cond=2764 merge=3076 then=[2802,...]   ← 2802 是 2742 的臂
```

三个前件在 2802 上全部成立，但 `region_ast_generator.py:21333/21378` 这个站点是
`_if_generate_normal` 的 then 分支装配处；2802 由父链 2742 经
`_if_generate_full_elif_chain`(:15183)/`_if_generate_elif_chain`(:18867) 装配。
**实测：`_if_generate_elif_chain` 函数体内没有任何 Continue 发射逻辑**
（18867-19100 段内只出现 JUMP_FORWARD/JUMP_BACKWARD 文本判断两处），
⇒ 下一版的施工点是 elif 链臂装配处，而不是再在 `_if_generate_normal` 上叠判据。

## 6. 会话结束时的认证态

- core：`region_ast_generator.py 5066b1367b6de3c7`（含 R14-04）、`region_analyzer.py 640d33a77dcb71c2`（未改）
- 磁盘产物 = 第 18 轮认证产物：`git status --porcelain -- site-packages` 为空；
  抽查实判 `klinedata 63/64`、`api_base 27/28`
- 残差名册 `RESIDUAL_ROUND18.md`：12 文件 / **33 单元**（= 6617 − 6584），UNREGISTERED=0
- 全部提交并推送 `rr-v3r01-f557fd`（远端 = 本地）

## 7. R15-13（生成端取反闩锁守卫）实测：零回退、零翻正 ⇒ 惰性

判据：`region_ast_generator.py:24109-24111` 的整链取反闩锁，当链的「全员同目标 T」
其实是**真值进入点**时不得取反（`_r15_uni_target_is_true_entry`：末成员除跳转边外的
另一条件后继若是测试块且其跳回 T，则 T 为 S 而非 F）。
13 文件面板（`D:/Temp/r150/uniguard.log`，跑完即还原 `5066b1367b6de3c7 byte_exact=True`）：
strategy 26/27、api_base 27/28 均**不变**；quotation 153/153、matcher 17/17、
IQEngine/core/strategy 20/20 全部守住；其余残差文件读数与封盘逐文件相同。

不可翻正的原因（与 DIAG_B137 自述一致）：strategy 的 or 链里，回到 @568 的边来自
链式比较段内的**后一个块**（@562 `JUMP_FORWARD -> @568`），不是末成员 @524 的直接条件后继
⇒ 判据在真实数据上从不命中。而 B137 早已实测：把该闩锁真正抑制掉（negate-guard 臂）
会把 4 处 target-only 变成 **2 target-only + 2 CONTENT**，即生成端单独动只把误差挪位。
⇒ **生成端单独路线关闭**（三次独立实测：本臂惰性、negate-guard 挪位、
`inner-38744` 臂逐字节相同）。strategy/api_base 的翻正必须走识别端
「三成员 or 链（第二成员为链式比较）的成链资格 + 父臂/merge 身份同判」，
即 R14-05 的诊断票；镜像诊断子代理正在追该 trace。

## 8. 会话累计（截至本条）

已落地并认证：R14-04（门链 18：units 6583→6584、files 390、回退 0、翻正 1）。
本会话新增实测负结果：T12-11 共要件（label 17，0 翻正）、R15-11、R15-12 宽/窄两版、
R15-13，以及 R14-05 子代理补丁（不安装）。所有负结果均已登记并逐字节还原，
core 现为 `region_ast_generator.py 5066b1367b6de3c7` / `region_analyzer.py 640d33a77dcb71c2`，
`site-packages` 零漂移，残差 12 文件 / 33 单元。

## 9. T12-22（order_api 两条单元同失一段调用）首两枪实测

目标：`IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` 35/37，两个失败单元
`future_order` / `option_order` 丢的是同一形：整条
`strategy_log.info('生成订单…{side}{oper}…'.format(o.order_id, o.symbol, side=('开仓' if o.futures_direction.value.upper()=='OPEN' else '平仓'), …))`
日志调用丢失，产物该臂只剩一行裸三元 ⇒ 一条判据即可整文件翻正。

- 猜测一「臂走 `_EXPR_REGION_TYPES`（含 TernaryRegion）的表达式区域路由」：把
  `region_ast_generator.py:314` 改成 `(BoolOpRegion,)` ⇒ order_api 仍 35/37，
  needle 计数（`strategy_log.info('生成订单`=1、`.format(`=13、`'买入' if`=3、`hedge_type`=5）
  与基线逐字节相同，quotation 153/153、matcher 17/17 不变 ⇒ 惰性，猜测被否。
- 猜测二「`:25422` 的 `child_expr_regions` 分派把臂入口交给三元区域」：加环境变量门旁路
  （`ABL_T` 未设时逻辑上必然等价于原路径）。结果 control 侧与 withABL 侧读数完全相同，
  但与**未打补丁的基线**不同：order_api 35/37 → **34/37**，`.format(` 13→12、`'买入' if` 3→0。
  ⇒ (1) 旁路没有找回丢失的 `strategy_log.info(...format(...))` 调用，丢失点在更上游；
  (2) 证实本管线输出对**源码文本布局本身**敏感（id() keyed 缓存与集合迭代次序随分配改变）——
  「逻辑死支路」的编辑不是惰性对照，唯一有效控制是逐字节相同的树。
  该条已并入用户级记忆 `in-analyzer-probes-perturb-cfg` 第 4 点。

## 10. 存档：R14-05 上一版补丁在镜像里的独立复判（诊断子代理测得）

镜像施加 banked `region_analyzer.py` 后：a01/a02/a03 仍 1/2；
`api_base` 由 27/28 退到 **25/29**（单元总数 28→29 ⇒ 该补丁额外生成了一个 code object）；
`strategy` 26/27 不变 ⇒ 除「不成链」外还多造对象，进一步坐实不安装。

## 11. R15-15（W14-A 修剪读 cc success edge）实测：零回退、零翻正 ⇒ 惰性，且暴露 strategy 的真正断点更靠前

`cctrim_rig.py ccedge`（把 `_cc_operand_success_edge` 接进 `region_analyzer.py:30250-30258`
的一致性修剪 keep 循环）8 文件面板：strategy 26/27、api_base 27/28 不变，
quotation 153/153、matcher 17/17、klinedata 63/64、trade_info_utils 38/41、
real_quote 43/45、evt 12/13 全部与封盘同值 ⇒ **零回退但零翻正**，跑完
`restored=640d33a77dcb71c2 byte_exact=True`。

原因即镜像 trace 自述的对称事实：修剪只会在成员**已被准入**之后才轮到剥；
而在未打补丁的 live 构建里 strategy/a03 的链走断在更前面一处 ——
**`region_analyzer` 的循环头判据**（banked 30018 对应 live ≈30005-30018，
`_b1b_c0 = (B@16 is LoopRegion@2.header_block)` 时 break），
不是认领守卫（api_base 才是断在认领守卫：`claimed` n=55 含 `B@1008`，
且 `_r16_boolop_cc_run_operand` 第 (2) 合取项 `_T=B@1098` ≠ `_t=B@1040`）。
⇒ 修 strategy 需要「准入侧」改动（放行 cc 成员越过循环头判据）+ 本修剪接线两条一起；
⇒ 修 api_base 需要「父臂 then/merge 身份」判据（DIAG_R1405 §5），与本修剪无关。
两条各自都是独立一票，单点判据不会翻正任何单元 —— 本票由此**关闭单点尝试**，
第 19 轮按这两张票分头施工（票面见 `rounds/round19/TICKETS_ROUND19.md` T19-2 拆分说明）。
