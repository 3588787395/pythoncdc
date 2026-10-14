# Round 10 工单 #13-P0（B128）：`matcher.DefaultMatcher.match` 整条切片成员测试被吞

标记族：`[r10-b128-...]`
工单：`.trae/specs/region-reduction-v3-full-corpus-100pct-10rounds/rounds/round10/FIX_OMISSION_R10_BRIEF.md` §一 P0 + §二.1 开放问题。
**只做 P0**；P1（`clock_worker` 三形）/P2（`get_history_df`、`kline_datetime_list`）为另票，禁止并案。

## 〇、靶面事实（主代理实测，本档不重推）

- 单元 `site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc :: <module>.DefaultMatcher.match`
- 该文件读数 16/17，唯一失败单元；本单元只有 **1 个多指令 hunk**：`orig[347:357]` 10 条整体消失
  `LOAD_FAST order | LOAD_ATTR asset | LOAD_ATTR symbol | LOAD_CONST None | LOAD_CONST 3 | BUILD_SLICE |
   BINARY_SUBSCR | LOAD_CONST ('688','689') | CONTAINS_OP | POP_JUMP_FORWARD_IF_FALSE`
  ⇒ 源级形态 `order.asset.symbol[None:3] in ('688', '689')`
- 其余差异为 20 字节缺失导致的跳转目标小平移。

## 〇B、已被否证的锚点（不得重复）

简报首版「宿主＝`MIN_INSTRS_FOR_SUBSCR_ASSIGN` 计数门控」**已被主代理否证**：该常量两处使用
（`_split_subscr_operands`、`_build_effective_stmts`）皆以 `STORE_SUBSCR` 为前提，而被吞串是
`CONTAINS_OP` 测试、全串无 `STORE_SUBSCR`。本票任务＝自证**真实丢弃点**，非照抄该候选。

## 〇C、纪律（`ADJUDICATION_R10_B126_REVERTED.md`）

- 零翻转 ⇒ 按 sha256 逐字节回滚。封表字节：
  `core/cfg/region_analyzer.py` = `38a1d5142d13…`（开工前已复核一致）
  `core/cfg/region_ast_generator.py` = `e9a8f65f6451…`（开工前已复核一致）
- 常驻电池是牙口：`r10ls_*` 复现臂必须先红后绿，对照臂必须持续绿。
- 禁「少发射换全绿」；禁名特判；禁 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`；
  禁硬编码条数/深度/偏移门控。
- 本票靶 `matcher` **无共要件**（§八），故 **不** 应用 `RAVED_R10_B126.patch`；该共要件只属于
  `trade_live_broker` 三条单元，与本票不同轴。

## 一、进度日志（边做边写）

- [ ] §二 丢弃点取证（探针 → 函数名 + 行 + 返回 None 的条件）
- [ ] §三 电池基线（HEAD 字节，r10ls_* 臂 RED/控制 GREEN 实测）
- [ ] §四 实现 + 电池复测
- [ ] §五 靶文件 17/17
- [ ] §六 哨兵复读
- [ ] §七 结论（代码已落地 / 仅归档 spec 未落地）

