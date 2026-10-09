# repro_tail —— 共用尾/隐式 return None 机器的**碰撞护栏**（不是复现电池）

跑法：`python -X utf8 .trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round19/repro_tail/make_tail.py --run`
（先不带 `--run` 只落 13 个源形到 `repro_tail/src`；判决只喂 `pycdc.py --region` 产物 + `scripts/pyc_verify.py single`。）

## 基准读数（landed 字节，2026-10-09）

```
t01_else_bare_return_tail_value … t10_two_returns_same_value   全部 GREEN
g01_plain_if_return_value / g02_plain_elif_else_assign / g03_while_no_break_tail   GREEN
GREEN=13 RED=0 / 13
```

## 结论（负面证据，勿重复施工）

1. **本族在 6~15 行的合形体上不复现**。round-18 残余表里判给「共用尾」的 5 个单元
   （`trade_info_utils.query_strategy_id`、`trade_info_utils.query_trade_strategy_info`、
   `handlers.TWHThreadController._target`、`real_quote.get_real_minute_kline`、
   `quote.get_real_from_zeromq`）在小合形体上全部走通用发射路径且字节相等
   ——即 `if/elif/else + 裸 return + 尾部 return 值`、`两个裸 return`、`while…else`、
   `and/or 条件两出口`、链式比较、try 体内 return、循环体内 return、两处同值 `return None`
   这些**孤立**形状都不是缺陷触发点。⇒ 本轴只能走**整文件门**（corpus-only gate），
   不可再用「先造最小复现」的路线开票（依 [[battery-before-corpus]] 的反面：
   电池必须先证明它能复现受害者，未证明 ⇒ 不得作为判据来源）。
2. 残余表对 `query_strategy_id` 的读数在 landed 字节上**逐条复核成立**（`unit_diff.py`，绝对路径调用）：

   ```
   len orig=117 prod=116 delta=-1
   == replace orig[108..109 @634] prod[108..110] del=1 ins=2
   ```

   即 `@634` 处原本 1 条 `JUMP_FORWARD -> 共用尾` 被写成 2 条内联 `LOAD_CONST None; RETURN_VALUE`，
   净 −1 与表记一致。缺陷只在**真字节码里共用尾被多条入边共享**时才显现，合形体给不出该结构。
3. **保留价值**：这 13 例构成「隐式 return / 汇合尾发射」机器（`_is_return_none_join_block`、
   `_nested_merge_return_skip`、while 臂尾部剥离、try 体终结尾、`[R3-Continue]`）的
   **常驻回归护栏**。任何改动这条机器的票，都必须先让本电池保持 `GREEN=13 RED=0`
   再去跑整文件门；若改动把任何一例改红，就是撞坏了已经正确的路径，直接回退。
