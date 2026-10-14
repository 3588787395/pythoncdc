# Round 9：`[R9-B122 fwdonly]` 否证交付（零翻转，已按 sha256 逐字节回滚）

## 处置

工单在 22:46 后无工具活动、亦无回报（TaskStop 返回「no task found」，运行已自行结束）。
主代理接管裁决：先存补丁再回滚。

    补丁：D:/Temp/r9main/WIP_R9B122_fwdonly.patch（70 行，含 [R9-B122 fwdonly] 六项模板与收集器改动）
    WIP 态 sha256：241a0a770b3aaaf2b89a06d08596a3aa591bc74cca136a9ac33f916b60d4c64b  core/cfg/region_analyzer.py
    回滚后 sha256：38a1d5142d132fd7288229851a33a02df71ccb3cf98ee40f84d4042bb8d1135e
                 ＝ HEAD blob 1d17f7bfa48e…，且与 Round 8 入库时同一读数（38a1d5142d132fd7）
    `git diff -- core` 为空 ⇒ 工作树已回到**已认证的 Round 8 态**。
    注：仓库里另有两条**他人**旧 stash（rcm-r49 / R26），本次未取用也未清理（共享工作树禁裸 stash）。

## 一、目标文件：零翻转

`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` 在 WIP 下
`single` 读 **118/128**，失败单元名单与 Round 8 封表**逐条相同**（10 个：`_process_order`、
`_process_cancel_order`、`_process_tick_order`、`_sync_worker`、`_trade_status_handle`、
`etf_basket_order`、`etf_purchase_redemption`、`rzrq_credit_order`、`ipo_stocks_order`、`get_ipo_stocks`）。
⇒ 按「修复只认单元翻转」的口径，**flips = 0**。

## 二、改动确实做到了它说的那件事，但那不是翻转

剔噪指令数：`_process_order` 产物 **42 → 448**（原 507）、`_process_cancel_order` **40 → 334**（原 333）。
被无条件 `break` 吞掉的方法体回来了，`del≫ins` 的整段缺失形状消失。
同时差块数由 3–5 **升至 28–32**（其中仅落点 18–23 块）——这是**遮蔽消失**而非退步：
截断产物因为内容根本不存在，比不出差。⇒ 体回来后剩下的障碍是落点/排位族，
一条边界判据修不完（`REVIEW_RESIDUAL_CENSUS.md` §XI 已预言此事）。

## 三、A/B：WIP 未造成回退，也未带来增益（关键取证）

电池 `test_repros/round9/r9a1_probe_index.json`（10 臂，主代理本次登记入册）：

| 臂 | WIP 态盘上产物读数 | 用 **HEAD 代码**在 `$TEMP` 重生成后读数 |
|---|---|---|
| r9a1_01_backentry_looparm | 1/2 红 | **1/2 红** |
| r9a1_02_backentry_deeparm | 1/2 红 | **1/2 红** |
| r9a1_06_neg_plain_ifelse | 1/2 红 | **1/2 红** |
| r9a1_07_neg_continue_then_only | 1/2 红 | **1/2 红** |
| r9a1_10_backentry_deep3 | 1/2 红 | **1/2 红** |
| 其余 5 臂 | 2/2 绿 | — |

⇒ 五条红臂在 HEAD 下同样红：**B122 既没修好任何一臂，也没打坏任何一臂**。
电池总读数 15/20 与 WIP 态一致，零变化。

**复核（主代理把 10 臂产物用回滚后的 HEAD 字节先删后重生成，ok=10 bad=0，再判）**：
读数仍 **15/20**，红臂还是 01/02/10/06/07——即本票**没有关掉自己三条 A1 复现臂中的任何一条**
（01/02/10 在 WIP 与 HEAD 下都 1/2）。这比语料零翻转更硬：它没过自己的复现门。
（03/08 两条 backentry 命名臂在 HEAD 下即绿，说明它们根本没复现出该形，属臂设计缺陷，
下一票须重做这两臂的形状。）

## 四、必须纠正的两处（含我自己的一处）

1. **`neg_*` 不是负对照**。`r9a1_06/07` 名字写「neg」，但两条在 HEAD 下都红，
   即它们其实是**另一条缺陷的复现臂**：源码 `while True: if C: <body>` + 循环内尾语句，
   产物把它折成 `while C:` 并把尾语句移到循环外（06）或塞进 `while … else:`（07）。
   主代理一度据「负对照变红」判定 WIP 造成回退——A/B 否证了这个推断；
   教训：**臂的角色由实测决定，不由命名决定**（先跑 HEAD 基线再谈回退）。
2. 该折叠形目前**只在合成臂上成立**，尚未在语料 42 个残差单元里定位到同形实例。
   按「电池先于语料」的对称要求，**不得**据此开新票；下一步是在语料里找同形证据
   （`while True:` 头 + 体内 `if` 测试 + 尾语句）再定归属。

## 五、下一票（#14 重开）必须带的约束

- 前向边闭包这一刀方向被证实**不足以**翻转任何单元：必须把**落点/排位**一并解决，
  或以语料逐单元名单证明有翻转才可落地；零翻转仍按本文件同法回滚。
- 补丁在 `D:/Temp/r9main/WIP_R9B122_fwdonly.patch`，可直接续用，不必重新设计。
- 验收面按 §X：以「只差 1 单元的 10 个落点族文件」为主要翻转候选，而非 A1 的两个单元。
