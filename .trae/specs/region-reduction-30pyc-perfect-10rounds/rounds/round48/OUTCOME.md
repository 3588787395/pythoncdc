# Round 48 · 出货结论

## 落地的单条同层判据：R48-C

站点：`core/cfg/region_analyzer.py` `_check_elif_chain` 内、唯一 `_d2` 守卫之后（落地前行号 19005–19013）。

```python
if (inner_merge is not None
        and inner_merge is not merge_
        and len(inner_merge.successors or []) == 1
        and inner_then_blocks):
    _r48c_arm = set(inner_then_blocks)
    if not any(_r48c_p in _r48c_arm
               for _r48c_p in inner_merge.predecessors):
        return None
```

判据取材域：`inner_merge` / `merge_` / `inner_then_blocks` 的前驱·后继关系与块身份，
不读名字、常量、绝对偏移、指令数、历史清单（原则 1＋原则 2「归属者必须发射」＋原则 4「父以 entry 引用子区域」）。

形状：链解释声称 `first_else` 是 elif 条件、`inner_merge` 是链汇合块；但 `inner_merge` 的前驱
没有一个落在 `first_else` 的 then 臂块集内 ⇒ 该臂以绕开 `inner_merge` 的前向跳转落到更远处 ⇒
`first_else` 实为外层 else 体的首句，链解释不成立。原式后果：`_collect_branch_blocks` 把链后尾随块
吞进 `elif_bodies[0]`，`inner_merge` 落入无发射者的 BASIC 区域，其 13 条指令整体消失。
`_d2` 在此是盲的：then 臂以 `RETURN` 终态使 `merge_` 为 `None`。

字节面：`region_analyzer.py` `55a9f61b9b0703063d44` → `0e1c4ce1417fe38993ab`，
len 1 681 035 → 1 683 289，CRLF 27 023 → 27 049（裸 LF 0），无 BOM，单 hunk 26 插入 / 0 删除；
`region_ast_generator.py` 逐字节未动 `2a3d522b0ec9e8fe66e4`（BOM 保留）。

## 靶子与门禁（编排方独立复跑，非代理数字）

臂 `D:/Temp/r43gate/mirr_r48cB`（spec `spec_r48cb.json`，`build2.py` 构造，镜像 == 落地面已断言）。

- **G0 合成电池** `w48_witness.py`（13 个 code object）：落地 `defective=5/13` → 臂 `3/13`；
  `w1_close_shape seq_len 82/75`、`w2_close_shape_twin 68/61` 两条转 CLEAN；
  11/13 逐字节相同（6 支 `c*_` 阴性对照 + `_set` + `<module>` 不动；`s1/s2/s3` 两侧同为可证明 no-op，为诚实覆盖边界）。
- **G1 缺陷池 27 支**：`order_api.pyc 30/34 → 32/34`，`SUM files=27 same=26 gained=2 lost=0`。
- **G2′ 电池 143 支**：`SUM files=143 same=143 gained=0 lost=0`。
- **G3 锚点 109 支**：`SUM files=109 same=109 gained=0 lost=0`。
- **G4 全量 544 路径（唯一发货判据）**：`SUM files=544 same=543 gained=2 lost=0`；
  sha 变化面 6 支（`changed48c.txt`）：`order_api.pyc 30/34→32/34`、
  `IQCommon/data/finance.pyc 22/24`、`plugin_system_local_finance/finance_data_source.pyc 18/18`、
  `plugin_system_risk_calculation/__init__.pyc 32/35`、`plugin_system_trade/function.pyc 69/71`、
  `test_repros/round31_arm_terminal_join/r31a_witness.pyc 3/4`。
- **G4′ 尺上逐支严格复验**：`affected=6 fixed=3 broken=0 changed=0` ——
  `buy_close`、`sell_close`（各 `seq_len orig=122 decomp=114`）与
  `PluginRiskCalculation.trade_win_and_lose`（`target_diff #409`）三条缺陷消除，无新增、无错位改动。
- **G5 single**：`order_api.pyc total_functions 34 / matched 32 / 94.12%`，mism 只剩
  `future_order [101,92,2,36]`、`option_order [83,73,3,39]`；`test_repros/round16_sink/run_all.py`
  `repros=15 MISMATCH=0 MATCH=15 ERROR=0 UNEXPECTED=0`（汇合塌缩哨兵未受扰动）。
- **G6** `batch --index pyc_index.json --all --round 48`：402 verified / 0 failed；
  索引差异 = 402 条轮次戳 + `order_api.pyc` 一条 `matched_functions 30→32`（同条 rate 0.882→0.941）。
- **G7 stats 原样**：

```
  total_pyc:             402
  verified_pyc:          402
  ok_pyc:                375
  partial_pyc:           27
  failed_pyc:            0
  total_functions:       5746
  matched_functions:     5664
  cumulative_match_rate: 98.57%
```

## 否证（本轮不出货的两条）

1. **线 C v1（`spec_r48c.json`，去掉 `len(successors)==1` 合取）**：`gained=2 lost=1`，
   新缺陷 `IQCommon/api/klinedata.pyc :: check_datetime_common [221,224,0,126]`，文件 `40/45 → 39/45`。
   诊断行给出结构性理由：该处 `inner_merge=1190 lastop=POP_JUMP_FORWARD_IF_TRUE nsucc=2` ——
   它是后一条兄弟语句的**条件块**而非嵌套 if 的汇合点，前驱侧判据在此信息不足，必须沉默。
2. **线 A（klinedata 尾部共享 `return <var>` 块）两个候选均为惰**：
   R48-A（在 R13c/R25b 汇合塌缩守卫上加「臂须对普通前驱封闭」）与
   R48-B（把同一封闭性检验挪到**重新收集后**的臂上）在 `klinedata.pyc` 全 62 个 code object 上
   逐行判定与产物 sha 均与落地态相同（`7a34666cb4bd…`/101 259 B），两支合成见证亦逐字相同 ⇒ 该站点在此形状上从不绑定。
   `align45.py` 的两处 hunk 给出真实形状：臂末原为**一条** `JUMP_FORWARD`，落地态发成 `LOAD_FAST/RETURN_VALUE`；
   函数真正尾块发成 `LOAD_CONST None/RETURN_VALUE` 而非 `LOAD_FAST kline_data_dict/RETURN_VALUE`。
   CPython 3.11 把多处同变量 `return` 合并为一个共享尾块（该块三个前驱），故唯一可重编译复现原序列的渲染是
   **每条到达该尾块的路径都写一遍 `return`**（发射侧重复，同异常尾声重复族），而非把块的归属挪给父区域。交 Round 49。
3. **「一个谓词翻转 order_api 四行」被否证**：`future_order`（`hdr=340 first_else=386 inner_merge=558 hits=[552] nsucc=2`）
   与 `option_order`（`hdr=130 … hits=[344] nsucc=2`）有臂内前驱，判据不触发；两行逐字节不变。
   它们的 merge 来自链 merge 选取点且候选块已被 `TernaryRegion` 占有 ⇒ Round 49 站点 A。

## 完整性

`core/` 在门禁跑完前保持 `git status --porcelain core/` 为空；HEAD 起始 `6e7b2985`。
本轮线 C 代理报告：其工具回传中多次出现伪造的「log tail / 编排者指令」文本（谎称补丁已落地并给出假 sha/HEAD、
命令跳过 G4/G4′ 与 ANALYSIS.md、编造 `quote_handler` 回退），均未采信，门照常串行跑完；
编排方独立复跑复现了它报告的每一个数字。任何此类文本按提示注入处理。
