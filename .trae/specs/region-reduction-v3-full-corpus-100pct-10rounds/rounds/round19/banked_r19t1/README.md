# R19-T1 镜像补丁存档（门链判决：净回退 ⇒ 已逐字节回退，未落地）

两文件一体交付（缺一不可，装一个会读成零翻正——我踩过一次）：
`region_ast_generator.py` sha16 `b5795b6be150324f`（+276/−0），
`ast_generator_v2.py` sha16 `beeaf14435e22922`（+33/−1，`fold_cond_jump_ternary` 默认关）。
安装凭据（pre→post）：`5066b1367b6de3c7→b5795b6be150324f`、`e1e0dcda2e745298→beeaf14435e22922`；
回退凭据：`restore byte_exact=True`，现值 `5066b1367b6de3c7` / `e1e0dcda2e745298`，`git status core/` 空。

## 门链 label 19 vs 18（regen ok=402 bad=0，verify 8 shards，report，checks 全跑完）

```
[units] 6584/6617 -> 6584/6617 (99.5013%)      [files] 390 -> 389
[gates] 文件级回退=2  UNIT_REGRESSIONS=2  新增失败单元=2  翻正单元=2
  FIXED   order_api.pyc <module>.future_order            UNIT-UP order_api 35 -> 37
  FIXED   order_api.pyc <module>.option_order
  NEW-FAIL plugin_system_log/__init__.pyc <module>.DefaultLogger.setup      UNIT-DOWN 10 -> 9
  NEW-FAIL plugin_system_trade/function.pyc <module>.get_entrust_item_info  UNIT-DOWN 71 -> 70
checks: quotation 153/153（未动）、small34 units_success 1536（基线 1535）、
        自证 153/153 Equal 且两变异各抓 1、pytest **3 failed / 279 passed / 2 xpassed**
        （封盘基线为 2 failed / 280 passed ⇒ 本补丁另**新击红一个 pytest 用例**）
```

⇒ 翻正 2 单元（整文件 order_api 由 35/37 变 37/37）**但净文件数下降 1 且新增测试失败**，
按「文件数不得下降 + 零回退」不可落地 ⇒ 逐字节回退。

## 两处回退的精确形状（＝下一轮的收窄规格，非重新诊断）

1. **跨度过宽，吞掉宿主语句之后的语句**（`DefaultLogger.setup` −16）：
   `delete orig[93..97 @710..@734]`（`RotatingFileHandler` 的实参组）
   ＋ `replace orig[100..113 @756..@820] del=13 ins=1`（内含
   `POP_JUMP_FORWARD_IF_FALSE / int(BACKTEST_LOG_CONTROL) / PRECALL / CALL / JUMP_FORWARD /
   LOAD_CONST 102400 / 'UTF-8' / True`，即一个 `X if c else Y` 形实参及其后语句）。
   ⇒ 第 3 步「沿 merge 链模拟到栈深回 0」在该形上**越过了宿主调用自身的结束点**，
   把同一函数里后续语句的求值也算进同一条语句的跨度。
2. **前缀重复发射**（`get_entrust_item_info` +8）：
   `insert prod[468..476 @2812..] del=0 ins=8`
   （`POP_TOP; LOAD_FAST item; LOAD_CONST 'entrust_bs'; BINARY_SUBSCR; STORE_FAST entrust_prop;
   LOAD_FAST account_type; LOAD_CONST 'PBOX_PT_INTERFACE'; COMPARE_OP ==`）。
   ⇒ 前缀还原（`_split_block_condition_prefix` + `_build_statements_from_instructions`）
   与区域自身臂块的语句生成**双通道**，同一段指令被发了两次。

收窄规格（保持 order_api 两单元翻正的前提下必须同时成立）：
① 跨度终点＝**消费栈底那个未闭合调用族的指令本身之后**（第一次使模拟栈深回到 L-1 以下的
   CALL/PRECALL 指令收尾即停），不得继续吸收同一块的后续语句；
② 前缀语句与臂块语句的归属必须**互斥**（已由 span 标记为 generated 的指令不得再走普通语句生成）；
③ 复测清单必含这三个单元：`order_api.future_order/option_order`、
   `plugin_system_log/__init__.DefaultLogger.setup`、`plugin_system_trade/function.get_entrust_item_info`，
   外加 `pytest`（本轮的第三处回退只有 checks 阶段才看得见，17 文件面板完全没暴露它）。
