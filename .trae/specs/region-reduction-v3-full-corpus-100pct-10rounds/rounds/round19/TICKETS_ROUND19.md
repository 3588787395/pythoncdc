# 第 19 轮票面（起点：门链 label 18 认证态 390/402 文件、6584/6617 单元、残差 12 文件/33 单元）

## 测试工程师（≥10 个可复现实例；全部只判 pycdc 产物）

- T19-0 现状复测：`rounds/round14/repro_arm`（a01/a02/a03 = 3 例 RED）、
  `rounds/round14/repro_ccneg`（4 例）、`rounds/round14/repro`（9 例）、
  `rounds/round18/repro_retbreak`（4 例：2 红 2 绿，其中 r02 因第二缺陷不能当控制例）
  ⇒ 合计 20 个可复现实例，满足「每轮 ≥10」。
- T19-1 待补电池：为 R15-11（`real_quote` 两条 1 指令过发射）与 R15-10 缺陷 A
  各补「无外层 while True」的配对控制例，使红例可归因单判据。

## 修复工程师（按距整文件翻正的距离）

- T19-2 **R14-05（唯一可能一次翻正两个文件的票）**：`api_base` 27/28（0 内容差 +
  2 落点）与 `strategy` 26/27（0 内容差 + 4 落点）。生成端单独路线已三次实测关闭
  （R15-13 惰性；B137 的 negate-guard 臂把误差挪成 CONTENT；inner-38744 逐字节相同），
  ⇒ 必须走识别端：为「第二成员是链式比较的正极性 or run」建立 BoolOpRegion，
  并同时决定 then=T / merge=J。已排除清单见
  `rounds/round14/DIAG_R1405_ARM_MEMBERSHIP.md` §5/§7/§8 与
  `rounds/round18/REGISTER_R1512_NEGATIVES.md`；上一版 +221 行补丁已存档
  `rounds/round18/banked_r1405/`（电池仍 1/2、api_base 回退 ⇒ 不安装，勿重复实现）。
  施加与复判：`D:/Temp/r150/integ_rig.py <candidate_region_analyzer.py>`
  （已用 no-op 候选验证：还原 `restored analyzer=640d33a77dcb71c2 byte_exact=True`；
  控制读数 battery GREEN=0 RED=3/3、api_base 27/28、strategy 26/27）。
- T19-3 `klinedata` 63/64：`get_kline_by_count_new` = 1 内容差（臂尾 continue）
  **+ 12 落点差** ⇒ 单判据不足，需两条；continue 判据的实际装配点是
  elif 链臂（`_if_generate_elif_chain` 内无 Continue 逻辑），
  宽化版会造成 −20 单元回退（已实测登记）。
- T19-4 `handlers` 29/30：源形状搜索（产物源码编译只得 6 条 return-None stub，
  原始 7 条），三个剥离/汇合守卫均已实测无效。
- T19-5 `realtime_event_source` 12/13：需两条判据（批量认领抑制共要件 + 重定位），
  共要件脚本 `D:/Temp/r150/evt_patch.py`。
- T19-6 `trade_live_broker` 118/128：`_process_order` −465/507、
  `_process_cancel_order` −293/333，臂身份读反（见
  `rounds/18/DIAG_R1508_BROKER_LOSS.md`）。

## 门禁（不得省略）

`gate_round.py 19 18 --stage regen|verify|report|checks`；验收 =
regen `ok=402 bad=0`、`文件级回退=0`、`UNIT_REGRESSIONS=0`、`新增失败单元=0`、
`翻正单元≥1`，checks 四项与封盘同值（quotation 153/153、small34 1535/22、
自证 153/153 Equal、pytest 2 failed/280 passed/2 xpassed），随后提交并推送。
### T19-2 施工点精确到行（由 R15-14/R15-15 实测确定，勿再重新推导）

- **strategy（26/27，唯一失败单元 tick_worker_thread）需两条同时成立**：
  1. 准入侧：`region_analyzer.py:30009-30022`（B1b 循环头守卫）—— a03/strategy 的
     链走在此 break，实测条件 `_b1b_c0 is _ft_reg.header_block`（chain 首成员
     = LoopRegion@2 的 header B@16）；放行判据必须只针对「后继成员是链式比较操作数」
     的情形（候选判据见 DIAG_R1514 §5-2），否则破坏循环自身条件装配。
  2. 修剪侧：`region_analyzer.py:30250-30258`（W14-A 一致性修剪）—— 已实现并实测
     **单独施加零回退零翻正**（惰性，因步骤 1 未同时成立）；helper 与判据文本在
     `D:/Temp/r150/cctrim_rig.py` 的 TRIM_NEW / HELPER 里，可直接复用。
- **api_base（27/28，唯一失败单元 get_history_df）只需一条**：父 IfRegion 的
  then/merge 身份（DIAG_R1405 §5）；其认领守卫断点实测值为
  `_r16_boolop_cc_run_operand` 的第 (2) 合取项：`_T=B@1098` 不等于 `_t=B@1040`
  （prefix 混 and/or 成员）⇒ 候选判据 DIAG_R1514 §5-1「按算子分层的共享出口」。
  注意：banked 补丁的 merge 计算三段（banked 行 19675 / 19717 / 19757）使
  api_base 27/28 → **25/29**（多生成一个 code object）⇒ 施工时必须排除这三段。
- 施加与复判：`python -X utf8 D:/Temp/r150/integ_rig.py <candidate_region_analyzer.py>`
  （控制读数已封：battery GREEN=0 RED=3/3、api_base 27/28、strategy 26/27、
  quotation 153/153、matcher 17/17、klinedata 63/64、trade_info 38/41、
  wizard 55/58、real_quote 43/45）；单点判据另有 `cctrim_rig.py`（修剪侧）以及
  `hold_rig / join2c_rig / retguard_rig / cont3_rig / uniguard_rig / order_abl`
  系列已否清单可查，避免重复尝试已登记为惰性的判据。
