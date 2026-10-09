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
