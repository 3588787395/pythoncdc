# Round 72 diag1 · 只读诊断 FACTS

- 被测 HEAD：`37dc4a01`（round72 start，基线 `6c0a8f8c` = R71 落地）
- mandated 尺：`F:/Downloads/pythoncdc-main/scripts/pyc_verify.py`（pylingual `compare_pyc`，判据源 `D:\Desktop\ptrade相关\pylingual`）
- 使命：对 47 支 failure / 108 失败单元做族聚类 + A 组 10 支 58 单元根因到行 + ≥10 支最小复现 + 三要素判据提案
- 边界：**未修改 `F:/Downloads/pythoncdc-main` 下任何文件，未 git commit/push，未跑 land72，未做 402 全量扫描**
- 自算读数（`filecat.json` 与 `fam72.json` 双向核对一致）：
  `files_by_status {success:355, failure:47, compile_error:0, error:0}`，
  `units_total 6623 / units_success 6515 = 98.369%`，
  失败单元 **108 = Different control flow 85 + Different bytecode 17 + Extra bytecode 6**

---

## 1. synth 清单 + 读数

仪器：`mksynth72.py` = `py_compile` → `pycdc.py <pyc> -o <OK.py>`（仓库落地字节）→ `scripts/pyc_verify.py single`（mandated 尺）。
逐支读数：`synth/verify_readings.txt`；族复算：`synthfam.py` → `synth/synth_families.json`。

**复现 11 / 24（mandated 全部 `status=failure`）**

| 文件 | 失败单元 | mandated 读数 | 归族 |
|---|---|---|---|
| a01_ternary_return_in_try | `<module>.BarData.limit_up` | failure 2/3 66.67% | **F-TERNARY** `idx10 JUMP_FORWARD→RETURN_VALUE` |
| a02_andchain_shared_else | `<module>.f` | failure 1/2 50.00% | **F-ABSORB** 落点 42→46 落不同指令 |
| a03_try_wrapped_shared_tail | `<module>.get_fields` | failure 1/2 50.00% | **F-ABSORB** `28 JUMP_FORWARD 66→126` |
| a04_sibling_return_none | `<module>.post` | failure 1/2 50.00% | **F-PAD** 落点 72→76，同指令同 len |
| a05_mixed_and_or_chain | `<module>.BarData._history_bars` | failure 2/3 66.67% | **F-ABSORB** 落点 28→24 |
| a09_try_finally_tail_return | `<module>.upd` | failure 1/2 50.00% | **F-ABSORB** `JUMP_FORWARD→LOAD_CONST`，len 73/72 |
| b01_dupe_elif_return_listcomp | `B.get_orders/get_open_orders.<listcomp>` + Extra×5 | failure 7/16 43.75% | **F-EXTRA 5 + F-ABSORB 3** |
| b04_elif_not_orchain_raise | `<module>.Cache.info_conbine` | failure 3/4 75.00% | **F-ABSORB**（极性变体） |
| b05_bareexcept_boolop_orchain | `<module>.rep` | failure 1/2 50.00% | **F-ABSORB** len 84/80 |
| c02_genexpr_and_predicate | `P.*.<genexpr>` ×2 | failure 4/6 66.67% | **F-OTHER** `FORWARD_IF_FALSE→BACKWARD_IF_FALSE`，24/24 |
| c03_guard_polarity_inverted | `<module>` | failure 2/3 66.67% | **F-ABSORB**（默认参数常量被拆，非极性） |

族计数（synthfam）：`F-ABSORB 11 / F-EXTRA 5 / F-OTHER 2 / F-TERNARY 1 / F-PAD 1`，复现源 11。
A 组 6 族中 **5 族有最小复现**；唯一缺口 = A 组 F-OTHER 的 quote 2 支（b07 外层 if 掏空、b08 `not in` 会员判据均 success，最小形状未触发）。

**负对照（不复现 = 触发条件反证）**：`neg01_bare_ternary_return` 4/4 success、`neg02_assert_outside_try` 3/3 success。
**R72 已被 R71 修复而转绿的 R71 老形状（重要负读数）**：a06 try/except/else、a07/a08 if 吸收、a10 循环尾、b06 → 全 success，对应 R71 fix3(exctable) 与 fix2(THENOVER) 已生效，本族不再是 R72 主力。

---

## 2. 每族根因到行（R72 HEAD 实测行号；R71 引用的 `ra-gen :22445-22450` 已漂移到 `:22512`）

### A 组 58 单元族分布（最终读数）

`F-ABSORB 42 / F-PAD 6 / F-EXTRA 5 / F-OTHER 2 / F-TERNARY 2 / F-POLARITY 1`（10 文件，58 单元）

### 全量 108 单元族分布

`F-ABSORB 70 / F-PAD 14 / F-OTHER 12 / F-EXTRA 6 / F-POLARITY 3 / F-TERNARY 2 / F-EXCTABLE 1 / F-META 0 / F-ASSERT 0`

族×判据：`F-ABSORB` cf 65 + bc 5；`F-PAD` cf 14；`F-OTHER` bc 10(genexpr) + cf 2(quote)；`F-EXTRA` 6；`F-POLARITY` cf 2 + bc 1；`F-TERNARY` cf 2；`F-EXCTABLE` bc 1。

### 判据行

| 族 | 判据行 | 机制（首分歧实测） |
|---|---|---|
| **F-TERNARY** (2：`bar.limit_up` / `limit_down`) | `core/cfg/region_analyzer.py:20432` `_identify_ternary_regions`；`core/cfg/region_ast_generator.py:3199-3223`（IF_ELIF_CHAIN 对嵌套三元的让位判据，不让位 ⇒ `ast.Return(ast.IfExp)`）；`:11711 _generate_if`；`:17753 _if_generate_normal` | try 内 `return v if c else n` 未归约成 `Return(IfExp)`，降级为 if+两个内联 return：`20 JUMP_FORWARD to 26` → `20 RETURN_VALUE`（orig line 180/191，产物 line 144/157） |
| **F-ABSORB** (42 A组 / 70 全量) | ① and 链共享 else：`region_analyzer.py:23303 _identify_boolop_regions`、`:26646 _try_unify_mixed_boolop_chain`、`:15929 _identify_conditional_regions`；② if/elif 链尾被吞进 else 臂：`region_ast_generator.py:22512 [R71-thenover]` 影子认领守卫（**R72 仍不充分**）、`:17753 _if_generate_normal`、`:15503 _if_generate_else_branch`（R71 fix1 落点） | 落点指令不同 或 指令条数改变。细分：27 支「落点同但 len 变」、40 支「落点落在不同指令」、3 支 opname 变化 |
| **F-PAD** (6 A组 / 14 全量) | `region_ast_generator.py:185 _is_duplicated_cleanup_exit_return`、`:26482 [R35-B] 重复清理尾声非终末副本不得物化为 return None`、`:14865 _if_generate_then_branch`（R71 known-unfixed 行） | 指令流全同、仅跳转落点偏移**一律 +4**：614→618、644→648、310→314、638→642、726→730、138→142、332→336、434→438、198→236、158→364、380→404、148→174、506→934（后三个为大位移变体）。相邻 return-None/清理尾声块重排一个 4 字节槽 |
| **F-EXTRA** (5 A组 / 6 全量) | **`core/cfg/comprehension_generator.py:520-521`** —— `elif last_instr.opname in ('RETURN_VALUE','RETURN_CONST')` 分支 append `{'type':'Return'}` 后**未推进 `prev_end`**，`:573 remaining_instrs = instrs[prev_end:]` 再次生成同一 Return；对照 `:519/:565/:568/:571` 均有推进。佐证 `region_ast_generator.py:22505-22506` 注释「elif 分支内 listcomp 的 ast.Return 被重复发射一次」 | 产物源码每条 elif 臂 `return [...]` 连写两次（brokerOK.py 47/48、50/51、67/68、70/71、73/74、76/77）→ 多出 6 个无原对应的 `<listcomp>`：`TradeLiveBroker.get_orders`×1、`SimulationBroker.get_orders`×1、`SimulationBroker.get_open_orders`×3、`DefaultLiveBroker.get_orders`×1 |
| **F-OTHER** (2 A组 quote) | ① `check_industry_code` `in→not in`：**`region_ast_generator.py:88-100 _flip_contains_compare`**（`{'In':'NotIn','NotIn':'In','in':'not in','not in':'in'}`）+ 调用点 `:12743`、`:16032`、`:16386`、`:16823`；② `load_get_price` 外层 if 被掏空：`region_ast_generator.py:21530 _process_if_blocks`、`:17753 _if_generate_normal` | ① `idx158 CONTAINS_OP in → not in`（len 168 相等）；② `idx52 POP_JUMP_FORWARD_IF_FALSE → POP_TOP`（len 168 相等），产物把外层条件降级为裸表达式语句 `len(panel.major_axis) != 0`，内层 if/elif 链上提到同级 |
| **F-POLARITY** (1 A组 `_sync_worker`) | `region_ast_generator.py:46 _negate_expr`、`:57-59`、`:12032`、`:12108`（`UnaryOp('not')` 折叠）；`region_analyzer.py:15929 _identify_conditional_regions`（then/else 臂归属） | `94 POP_JUMP_FORWARD_IF_TRUE to 156` → `94 POP_JUMP_FORWARD_IF_FALSE to 134`（极性与落点同时移动）。另 2 支：`api_base.get_history` `60 IF_FALSE→IF_TRUE to 66`（同落点纯极性翻转）、`asset_mixin.get_assets.<listcomp>` `10 BACKWARD_IF_NONE→BACKWARD_IF_FALSE` |
| **F-EXCTABLE** (1，A 组外 `commission.set_commission`) | `region_ast_generator.py:24342`（注释：compiles try-else as two adjacent exception table entries）及 `:26152/:26587/:26615/:27010`（R71 F-EXCTABLE 落点，行号需按 R72 重定位） | 指令流全同，异常表 18/18 字节但范围不同 |

### B 组（只聚类不动手，fix1/fix2 领地）

- **F-OTHER genexpr 10 支**（`future_position` 4 / `live_future_position` 4 / `option_position` 2）：全部 `20 POP_JUMP_FORWARD_IF_FALSE to 42` → `20 POP_JUMP_BACKWARD_IF_FALSE to 8`，24/24 指令同；orig line 316/325/351/357… 产物 line 215/221/236/239…。判据行 `comprehension_generator.py:1339 _extract_comp_ifs`、`:1443-1459`（R10 OR-pattern 判据）、`:1461-1471`（逐段取反）、`:1479-1492`（AND/OR 合并）、`:1846 _detect_comp_ternary_as_filter`。实测字节码：orig 用 `FORWARD_IF_FALSE → 114(JUMP_BACKWARD)` 跳「跳过本元素」块，product 直接 `BACKWARD_IF_FALSE → 8(FOR_ITER)`，即 `if A and B` 被拆成两个独立 `if` 过滤器。
- **F-POLARITY `asset_mixin.get_assets.<listcomp>`** 同属推导式谓词（`BACKWARD_IF_NONE→BACKWARD_IF_FALSE`）。

---

## 3. 三要素判据提案摘要

（同层次结构身份判据：只读本帧/本区域自身参数与字段；无函数名/文件名/字面偏移/计数阈值；无跨层 `region.entry in r.blocks` 型模式；不新增 self 状态。）

1. **F-TERNARY** — `TernaryRegion.merge_block` 是本区域**唯一多路汇聚点**，且它是本区域 entry 后继的**唯一公共后继**、出边集合恰为 {then 出口, else 出口} ⇒ 归约 `Return(IfExp)`。读量：本区域 blocks + merge_block 自身出边数。
2. **F-ABSORB（链尾被吞进 else 臂）** — 在现有 `:22512` 六条之上再加一条同层约束：待影子认领的 `merge_block` 的**全部入边前驱必须都属于本帧 blocks**（不引用兄弟区域内部块名、不比较 offset 大小关系之外的任何阈值）。满足则预标记 generated、生成后撤销。
3. **F-ABSORB（and 链共享 else 不抬升）** — else 臂归属判定改为：`else` 块的**唯一入边前驱**是链的**条件链尾块**而非最内层条件块 ⇒ else 挂到最外层。读量：链上各条件块的出边集合。
4. **F-PAD** — 指令流全同（opname+argval 逐位相等）且仅跳转落点偏移不同的两个候选发射次序，按**原 CFG 中该跳转目标的首次拓扑出现位置**定序，禁止按 offset 升序重排 ⇒ 落点回到 +0。
5. **F-EXTRA** — 记账不变式（非判据）：`comprehension_generator.py` 内任何 append `Return` 的分支必须同步推进 `prev_end`（`RETURN_VALUE/RETURN_CONST` 分支 → `prev_end = len(instrs)` 或 `wrapper_end`），保证 `remaining_instrs` 不再含该 return。**直接采纳 fix2。**
6. **F-OTHER（`in`→`not in`）** — 只有当该 `Compare` 的**消费跳转 opname 含 `IF_TRUE` 且其落点块是本区域 then 臂入口**时才允许 `_flip_contains_compare`；否则保持原 `in` 并翻转跳转极性。读量：跳转 opname + 落点块的臂角色。
7. **F-OTHER（外层 if 掏空）** — 外层 `if` 的 then 臂若**恰为单个嵌套 if/elif 链**且该链的 merge 与外层 merge 是同一块，则禁止上提：外层条件必须保留为 `if`（不得物化为裸 `Expr`）。读量：外层 then 臂首块/末块与 merge 块身份。
8. **F-POLARITY** — 守卫取反只在「then/else 臂语句序列**整体互换**且互换后两臂首条指令的 opname 分别与原臂首条指令相同」时允许；否则回退为原极性 + 臂交换。读量：两臂首指令 opname 与臂语句序列。

---

## 4. fix1 / fix2 覆盖核对与分歧点

fix1/fix2 两支修复**均只改 `core/cfg/comprehension_generator.py`**：
- **fix1 = genexpr 跳转方向分叉**
- **fix2 = RETURN 分支漏推进 `prev_end` 导致重复 Return**

| 项 | 结论 |
|---|---|
| fix2 与本诊断的同源性 | **完全同源**。我定位的 `comprehension_generator.py:520-521`（`RETURN_VALUE/RETURN_CONST` 分支 append `Return` 后未推进 `prev_end`，`:573` 复用旧 `prev_end` 重发）即 fix2 所指的「RETURN 分支漏推进 prev_end」。 |
| fix2 应覆盖 | **F-EXTRA 6 支**（broker 4 + trade_live_broker 1 + live 1）以及 F-ABSORB 中「产物重复 `return [...]`」的子集（b01 最小复现即此形状）。 |
| fix1 应覆盖 | **F-OTHER genexpr 10 支**（position_model 三类）与 `asset_mixin.get_assets.<listcomp>` 的 F-POLARITY 1 支；synth `c02_genexpr_and_predicate` 是同形状最小复现（4/6 failure）。 |
| **分歧点（两支修复不覆盖）** | F-ABSORB 主体（A 组 and 链共享 else 42 支中的非重复-return 部分、链尾吸收）、**F-PAD 14**、**F-OTHER quote 2**、**F-POLARITY `_sync_worker` + `get_history` 2**、**F-TERNARY 2**、**F-EXCTABLE 1**。 |
| 估算剩余面 | 108 − 6(Extra) − 11(genexpr/listcomp 谓词) ≈ **91 单元**为 fix1/fix2 之后需下轮接手的量；A 组 58 − 5(Extra) − 0(genexpr) ≈ **53 单元**仍在 A 组。 |

---

## 5. 产物路径

已落盘（全部在 `D:/Temp/opencode/r72gate/diag1/`，未触碰 repo）：

- `FACTS.md`（本文件）
- `fam72.py` / `fam72.json` — 用真实判据（`matching_iter` + `is_control_flow_equivalent` + `compare_bytecode`）重算的 108 单元族聚类（权威）
- `cluster72.py` / `cluster72.json` — 首轮 raw-dis 分类（配对有偏，保留为对照，**不作为读数来源**）
- `cfdiv.py` — 逐支首分歧指令 + 块差异仪器
- `mksynth72.py` — 编译 → `pycdc.py` 反编译 → `pyc_verify single` harness
- `synthfam.py` — synth 失败单元族复算
- `synth/*.py`（24 支候选）、`synth/out/*`（.pyc / .src / *OK.py）、`synth/verify_readings.txt`、`synth/synth_families.json`
- 既有仪器：`align.py`、`disf.py`、`regdump.py`、`nested_diff.py`、`probe_chain.py`、`h62.py`、`land72.py`、`canary.txt`

**`specs/` 保持空。**
