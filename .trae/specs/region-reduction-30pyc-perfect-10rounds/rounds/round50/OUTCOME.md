# Round 50 · 出货结论：core/ 零改动、不发货

## 本轮唯一靶子与落地基线

`site-packages/IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc` —— 落地 strict `33/36`，
三支缺陷逐字为：

```
<module>.base_order    [target_diff] #136 POP_JUMP_IF_TRUE 终点 orig=("'order_obj'", 'LOAD_FAST') decomp=("'生成订单，订单号:{order_id}，可转债代码：{symbol}，数量：{side}{share}'", 'LOAD_CONST')
<module>.future_order  [seq_len] orig=101 decomp=93
<module>.option_order  [seq_len] orig=83 decomp=74
```

## 三条候选判据全部否证（G0：6 个真 pyc ＋ 合成电池，编排方独立复跑）

| 臂 | 站点 | order_api | future/option 逐函数 decomp 条数 | quotation | quote_handler :: get_index_stocks_local |
| --- | --- | --- | --- | --- | --- |
| `head50`（落地） | — | 33/36 | 93 / 74 | 148/150 | 150 |
| `r50a` | 17062 区段（早站点改绑 `merge=else_succ`，五条合取） | 34/36 | **77 / 65** | **134/150** | **60** |
| `r50b` | 19441–19452（链候选剔除 `TernaryRegion` 已认领块） | 33/36 | 93 / 74（逐字节同落地） | 148/150 | 150 |
| `r50e` | 17062 ＋ 第⑥合取（`else_succ` 的后继是某 `TernaryRegion` 入口） | 33/36 | **79 / 65** | 148/150 | 150 |

`klinedata.pyc 53/63`、`wizard_quant_api.pyc 52/56`、`plugin_system_log/__init__.pyc 9/10`
四支臂逐项相同（未受触动）。电池：`r50_controls` 三臂皆 `MATCH`；
`r50_target_shape` 落地 `shape_exit_then_ternary_stmt seq_len orig=28 decomp=31`、
`r50e` 同支 `26`、`r50a` `26` ⇒ 合成见证方向相反，未复原语料形状（诚实覆盖边界：语料那条语句是
**三个三元链＋三个并列值**填满 5–6 个 kwargs 槽，见证只有一个三元）。

命中实测（带打印的镜像核，非推断）：

- `r50e` 在 `option_order H=130` **确实开火**：`then=174`（`RETURN_VALUE`，无正常流后继）、
  `else=178`（`POP_JUMP_FORWARD_IF_TRUE`，前驱仅 `[130]`）、`else_succs=[542, 206]`、`PRED=True`、改绑前 `merge=None`
  ⇒ 「then 臂硬退出 ⇒ `merge=else_succ`」这条判据本身成立，**但成立之后 strict 更差**（74→65）。
- `r50b` 同样开火：落地该链 `cands=[350]`（`conds=[178] bodies=[[344]] fe=[348] exits=[[],[350],[350]]`），
  臂上 `cands=[]`（`owned=[206,344,348,350,418,422,424,504,508,510]`）⇒ 链不再把 `TernaryRegion@206`
  的臂块当 merge；**但产物逐字节与落地相同**（惰）。

⇒ 本轮否证的原命题：「链 merge 选错（或早站点 merge 留空）是 order_api 两支函数丢指令的根因」。
两条独立站点上分别开火后，一支变得更差、一支完全惰，说明丢失发生在**归属/merge 之外**的装配层。

## 真实根因（生成器侧，逐行定位并已用打印取证）

`core/cfg/region_ast_generator.py` `_try_build_ternary_kwarg_call`（定义 41375，唯一调用点 36829）
在第 41500–41505 的槽位装配循环里 `return None`。臂内打印实测两条 bail：

```
R50GEN preload_kwarg i= 1 ('order_id', 'symbol', 'side', 'oper', 'share', 'hedge_type') 1 424     # option_order
R50GEN preload_kwarg i= 1 ('order_id', 'symbol', 'side', 'oper', 'share') 1 558                    # future_order
```

即 `num_ternaries=1` 而 `len(kw_names)=6/5`：41464 的
`num_positional_from_ternary = max(0, num_ternaries - kwarg_count)` 与 41501 的
`if (kwarg_ternary_start + i) < num_ternaries` 合起来只支持「**三元链结果连续占据 kwargs 的前若干槽**」，
任何需要非三元值（preload kwarg 值，注释自认 `# Would need preload kwarg value — not in R9 cases.`）的槽位一律早退。
另有一处独立缺口：链行走（41400–41412）只沿 `region.merge_block == inner.entry` **前向**延伸，
故传入的 `region` 是链尾（`entry=424` / `558`），链头（`206`、`350`）与其间的并列值无从进入装配。

真源（按 `dis` 复原，`option_order` 尾段）是一条语句，产物却只留下碎片：

```python
strategy_log.info('生成订单，订单号：{order_id}，合约代码：{symbol}，方向：{side}{oper}，数量：{share}手, {hedge_type}'.format(
    order_id=order_.order_id, symbol=order_.symbol,
    side='买入' if order_.entrust_direction.value.upper() == 'BUY' else '卖出',
    oper='开仓' if order_.futures_direction.value.upper() == 'OPEN' else '平仓',
    share=order_.amount,
    hedge_type='非备兑类型委托' if order_.hedge_type.value.upper() == 'SPECULATION' else '备兑类型委托'))
```

落地产物实际写成 `'买入' if ... else '卖出'`（漏成兄弟语句）＋ `order_.hedge_type.value.upper('非备兑类型委托' if ... else '备兑类型委托')`
（把 `LOAD_METHOD`＋`CALL` 错绑成 `upper(<三元>)`）⇒ 缺的正是这条 `Expr(Call)` 的装配。

## 否证的旁支（一并记录，避免下一轮重走）

- **R49-A 扩展线**：把 `_r49a_shared_sink_tail_merge` 挂到其余 `merge = else_succ` 绑定点，对
  `klinedata :: _all_bars_of_cache`、`kline_datetime_list` 的所有 if 区域实测 `cands=[]`；
  `get_multiminute_his_data` 唯一命中点（`H=718 → 2758`）改绑前后 merge 相同 ⇒ 该三支残余**非**此形状。
- **早站点单向改绑（R50-A 原式）**：绕过 `IF_ELIF_CHAIN` 创建与 R33/R35 兜底，全局外溢
  （`quotation.pyc 148/150→134/150`、`quote_handler :: get_index_stocks_local` 发射 150→60），
  与 Round 35 的 `else_succ 是 elif 条件块` 告诫一致。

## 移交 Round 51 线 A（唯一优先，两点须分别开证）

1. **链头**：`_try_build_ternary_kwarg_call` 的入口 region 需取语句最外层三元（靶子 `entry=206`）而非链尾；
   现签名从调用点 36829 传入的 region 已是链尾 ⇒ 先证明 206/350 两个区域为何未被当作链头送入。
2. **槽位装配**：把每个 kwarg 槽位映射到「三元链结果」或「该步 merge/preload 块上算出的值」，
   取消 41501 的早退；`num_positional_from_ternary`（41464）的「三元结果 contiguous 且在栈顶」假设必须换成按字节码顺序逐槽判定。
3. 同文件第三支 `base_order [target_diff] #136` 是**不同形状**（跳转终点常量错位，非丢语句），
   不得并入上述判据；`order_api.pyc` 即便 1+2 全修也仍需单独开证它才能到 CLEAN。

## 字节面证明（零改动）

- `core/cfg/region_analyzer.py` = `c644a6ccab745ac6be0e`，len 1 687 755，CRLF 27 126，裸 LF 0，无 BOM
  —— 与 Round 49 落地态逐字节相同；
- `core/cfg/region_ast_generator.py` 逐字节未动，BOM 保留；
- `git status --porcelain core/ pycdc.py` 输出为空；
- 本轮不发货：未跑 G1–G7，未改 `pyc_index.json`，官方尺数字仍为 Round 49 收口时那一份。

三条候选臂（`D:/Temp/r43gate/mirr_r50a`、`mirr_r50b`、`mirr_r50e`）与带打印镜像
（`D:/Temp/r50mine/dbgland`、`dbgr50b`、`dbgr50e`、`dbgr50gen`）连同 spec 留在原处，供 Round 51 直接复跑。
