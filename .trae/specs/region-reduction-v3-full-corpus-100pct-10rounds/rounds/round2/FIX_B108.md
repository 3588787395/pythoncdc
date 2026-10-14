# FIX_B108 — 混合极性 `or` 链被整体取反（`A or not B` → `not (A or B)`）

轮次：Round 2 / 破口 B108（登记见 `REVIEW.md` §4.4）。执行人：round-2 修复 agent。
判定尺：`scripts/pyc_verify.py`（未修改）。所有产物均由 `python -X utf8 pycdc.py -o <base>OK.py <base>.pyc`
先删后生成，未手改任何 `*OK.py`。

## 0. 落地标记（grep 用）

```
[R2-B108 修复·混合极性 or 链逐项还原]
```

落地站点（全部在 `core/cfg/region_ast_generator.py`）：

| 行 | 站点 | 作用 |
|---|---|---|
| 37852 | 新方法 `_boolop_mixed_polarity_or_chain`（含六项算法 docstring） | 混合极性判据本体 |
| 38247 | `_build_boolop_expression_inner` 判定表取用点 | 链级极性表 |
| 38379 | `_build_boolop_expression_inner` implicit-not 分支 | 逐操作数还原 `not Z` |
| 23816 | `_if_extract_condition_from_instructions` 整体取反闩锁 | 抑制 `not (...)` |
| 19162 | `_if_generate_elif_chain` elif 整体取反闩锁 | 抑制 `not (...)` |

`core/cfg/region_analyzer.py` **零改动**（字节校验：31914 行全 CRLF、单个 BOM，与开工前一致）。

## 1. 具体反转谓词：修复前 → 修复后

最小标本 `test_repros/round2/r2v3_c02_or_not_operand_plain.py`（源码 `if username not in uinfo or not uinfo[username]:`）：

```
修复前： if not (username not in uinfo or uinfo[username]):
修复后： if username not in uinfo or not uinfo[username]:
```

语料锚点（`site-packages/fly/common/future_contract_info.pyc`）：

```
info_conbine off462  前： elif username not in self._FutureInfoCache__user_info or uinfo[username] 的 not(...) 形
                    后： elif username not in self._FutureInfoCache__user_info or not self._FutureInfoCache__user_info[username]:   （OK.py:266，单元转 success）
check_user  off66   前： if not (username not in …keys() or …[username]):
                    后： if username not in self._FutureInfoCache__user_info.keys() or not self._FutureInfoCache__user_info[username]:  （OK.py:168，臂入口互换消失，仅剩 §5 的 finally 复制）
```

c01（elif 形）修复前 `elif not (username not in uinfo or uinfo[username]):` → 修复后 `elif username not in uinfo or not uinfo[username]:`。
修复前两条臂（then=raise / end=return）互换：整体取反后「A 真 → 跳 end」，`RAISE` 与 `RETURN` 的入口对调，正是原则 2/原则 4 的违反。

## 2. 被纠正的分类，以及它原先读的是哪条白名单判据

字节码事实（`pycdc` 实测 op_chain，S = 链真入口 = 末成员落空边，F = `merge_block`）：

| 标本 | op_chain | 各成员 IF_TRUE 目标 |
|---|---|---|
| c02 | [(blk@0,'or'), (blk@10,'or')] | blk@0→26(=S)，blk@10→56(=F=merge) |
| c01 | [(blk@40,'or'), (blk@48,'or')] | 40→64(=S)，48→94(=F=merge) |
| c04（对照，必须保持） | [(blk@0,'or'), (blk@10,'or')] | 0→56，10→56（全员同一目标 = R14c 负极性整链） |

识别端 `region_analyzer._detect_boolop_conditional_chain` 的 `[W14-A]/[R14c]` 同目标归一守卫
（`region_analyzer.py:29670-29685`）对「全员 TRUE 跳 + 目标同一块」保持 `'or'` 并交构建层整体取反，
对「目标分裂」的链**显式不做归一**，其注释（29677-29679）把这类链交给「and/逐项 implicit-not 路径」。
即识别端交出的链 `[('or'),('or')]` 运算符归类正确，反转不发生在识别端。

反转发生在消费端的两条**白名单闩锁**，它们只读「全员跳转目标是否同一块」与「末成员末指令 opcode 族」，
完全没有考虑成员真边的分裂（部分成员真边指向链真入口 S、部分指向 F）：

1. `region_ast_generator.py:23783-23803` `_w14_uniform_and` → 23804-23808 `_boolop_negate = True`
   → 23837 `_negate_expr(boolop_expr)`（整链取反）。
2. `region_ast_generator.py:19162` `_elif_negate = (_elif_last.argval in _elif_then_offsets) != _elif_if_true`
   （elif 链同族闩锁）。

实测证据（临时插桩，已随脚本留在 `D:/Temp/rrv3/`，仓库内零残留）：`_negate_expr(BoolOp 'or')` 的调用栈
c02/c06/c09/c10 命中 `region_ast_generator.py:23837`，c01 命中 `19191`，c11 命中 `21431`（嵌套 if 折叠路径，见 §5）。

纠正后的分类：新增判据 `_boolop_mixed_polarity_or_chain(region)` —— 只读
「成员末指令 opcode 族 + 成员跳转目标块 + 末成员非跳转后继 + 区域自身 `merge_block`」四类同层事实，
命中「全员 IF_TRUE 族 + 目标分裂为 S 与 F」时返回逐成员极性表，
由 `_build_boolop_expression_inner` 的 implicit-not 分支把真边离开 S 的成员逐个包成
`UnaryOp(not, 操作数)`，并让两条整体取反闩锁对该链失效（避免二次取反）。
AST 映射：`BoolOp(op='or', values=[X, …, UnaryOp(not, Z)])` = `X or … or not Z`。
判据不命中（全员同目标 S、全员同目标 F、含 `FALSE`/`NONE` 族成员、离开目标落在链内块、
离开目标非本区域 merge）一律返回 `None`，输出与编辑前逐位一致 —— c04/c03/c05/c07/c13 五条对照即此路径。

无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 新方法；无深度/数量硬上限；
无操作数计数特判（判据对 2..n 成员一视同仁）；无文件名/函数名白名单；无文本级改写；
单向数据流：极性在链归约（`_build_boolop_expression_inner`）一次成型，未做发射后回溯修正。

## 3. 落地文件

* `core/cfg/region_ast_generator.py`：新增 `_boolop_mixed_polarity_or_chain`（六项 docstring ①-⑥齐全）
  + 4 处接线（38247 取用、38379 逐项还原、23816 闩锁抑制、19162 闩锁抑制）。
* `core/cfg/region_analyzer.py`：**未改动**。理由见 §2 的实测调用栈与识别端注释；
  若把该链在识别端改标 `'and'`（唯一可用的既有负极性载体），`_boolop_negate` 仍按末成员 IF_TRUE 触发
  双重取反（`not (A or not B)`），改标全员 `'and'` 亦得 `A or B`（丢 `not Z`）——
  识别端任何既有编码都无法同时携带「或链 + 末位负极性」，反转确由消费端闩锁引入，故按 ticket 授权
  改这**单个**文件（`region_ast_generator.py`）并在此说明。

## 4. before → after 全量数字

| 命令 | before | after | 结论 |
|---|---|---|---|
| `batch --index test_repros/round2/r2v3_probe_index.json` | 85/114 units，56 文件 = 27 success / 29 failure | **90/114 units，56 文件 = 32 success / 24 failure** | +5 文件 / +5 单元，零回退 |
| c 族 8 标本 | 全 failure | **c01, c02, c08, c09, c10 = success（5/8）**；c06 1/2、c11 1/2、c12 1/2 仍 failure | 未全绿，见 §5 |
| c 族 5 对照 c03/c04/c05/c07/c13 | success | **success（5/5 保持）** | 过伸展检查通过 |
| `single site-packages/fly/common/future_contract_info.pyc` | 27/29 | **28/29**（`info_conbine` 翻转；`check_user` 条件已正确、仅剩 finally 复制） | 未达 29/29 |
| `batch --index test_repros/round1/r1_probe_index.json` | 108/110，44 success / 2 failure | **108/110，44 success / 2 failure** | 保持 |
| `batch --index test_repros/round1/r1_regress_index.json` | 34/34，17 success / 0 failure | **34/34，17 success / 0 failure** | 保持 |
| `single …/plugin_system_realquote/real_quote.pyc` | 43/45 | **43/45** | 未跌 |
| `single …/plugin_system_risk_calculation/__init__.pyc` | 41/43 | **41/43** | 未跌 |
| `single site-packages/IQCommon/data/finance.pyc` | 31/32 | **31/32** | 未跌 |
| `single site-packages/fly/data/quotation.pyc` | 152/153，失败单元 `get_fundflow_day` | **152/153，失败单元仍是 `<module>.get_fundflow_day`** | 未跌、单元未换 |
| `single site-packages/IQCommon/util/cgroup_utils.pyc` | 8/8 | **8/8** | 保持 |
| `single …/plugin_system_trade/trade_live_broker.pyc` | 118/128 | **118/128** | 未跌 |
| `single site-packages/fly/data/quote.pyc` | 85/92 | **85/92** | 未跌 |
| `pytest -q tests/{test_algorithm_correctness,test_deep_nesting_pressure,test_control_flow_completeness_matrix,test_complete_syntax_coverage,test_boundary_cases,test_core_functional}.py` | 2 failed / 277 passed / 2 xpassed | **2 failed / 277 passed / 2 xpassed**（同一两条：`TestDominanceFrontierIf::test_B01_simple_if_then_else_merge`、`TestBoundaryConditions::test_BOUNDARY_02_large_function`） | 保持 |
| `python -X utf8 -c "import core.cfg.region_analyzer, core.cfg.region_ast_generator, core.cfg.code_generator"` | ok | **ok** | — |
| `python -X utf8 -m compileall -q core` | ok | **ok** | — |

字节完整性：`region_ast_generator.py` 58279 行全 CRLF、恰 1 个前导 BOM；`region_analyzer.py` 31914 行全 CRLF、
恰 1 个前导 BOM（未触碰）。补丁区未做任何整文件换行归一。

## 5. 仍未转绿的三条臂（B108 未闭环，如实登记）

* **c06 / `check_user`**：条件与两臂入口已正确（`_r2diag diff` 只剩 off818 区 6 条插入 =
  `finally` 的 `self.lock.release()` 被复制进 handler 的 `POP_EXCEPT` 之前）。
  REVIEW §4.2 预判该复制是臂归属的下游后果，实测**臂归属修复后它独立存在** ⇒ 应另立破口，
  不在本票判据面上做特判（本轮不修）。
* **c11**：链在 while 体内未被识别为 `BoolOpRegion`（`analyze()` 区域表无该项），反转由
  嵌套 if 折叠路径 `region_ast_generator.py:21431` 的 `_all_negated` 分支引入 ——
  该分支读「两条待合并条件是否都带 `not`」，不读成员真边归属，属另一处白名单；
  且其宿主链识别本身失败，混入本票需改链识别的循环体认领判据（越界）。
* **c12**（三操作数 `A or not B or C`）：识别端把非末位负极性 or 成员按
  `op_type = 'and' if 'FALSE' in last.opname else 'or'`（`region_analyzer.py:29105`）错标为 `'and'`，
  链变成 `[or, and, and]` → 产物 `a not in b or b[a] and c is None`。
  这是**识别端**的运算符归类缺陷（同函数 29094-29103 的 None-check 分支已有「按跳转目标定 op_type」的先例），
  修它需在识别端引入「成员跳转目标 == 链真入口 ⇒ or 链接」的目标基判据，改动面覆盖全部 and/or 混合链，
  超出本票剩余预算，本轮不动。

## 6. 声明

**「代码已落地」**：判据与接线已在 `core/cfg/region_ast_generator.py`（5 个 `[R2-B108 修复·混合极性 or 链逐项还原]`
标记站点），round-2 电池 +5 文件 / +5 单元、c 族 5 对照全保持、Round-1 两批复跑不变、9 个哨兵文件与 pytest 零回退。
**B108 尚未闭环**：8 标本中 5 转绿，c06/c11/c12 仍红（机制见 §5，分别为独立的 finally 复制、折叠路径白名单、
识别端运算符归类），`future_contract_info.pyc` 为 28/29 而非 29/29。未使用任何即时否决形换绿。
