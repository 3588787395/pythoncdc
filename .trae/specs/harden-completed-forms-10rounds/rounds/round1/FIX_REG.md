# Round 1 修复工程师三报告（单元级回退归零：risk_calculation.get_daily_summary）

- 回退对象：`site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc`
  单元 `PluginRiskCalculation.get_daily_summary`，基线 Equal → 现 `Failure: Different bytecode`
  （文件 41/43 → 40/43）。本批归零：**41/43，回退单元回到 Equal**。
- 唯一判据：`python scripts/pyc_verify.py single`（pylingual compare_pyc 逐单元）。
- 硬约束自检：无函数名/文件名白名单、无 start_offset 数值阈值（偏移仅作块/指令
  身份恒等比较）、无跨层读取、无新增 self 跨方法状态（`_r76_upgr_binds` 为函数
  内局部量）、被丢弃操作数全部接回（让位形态下守卫条件由既有 R59-B 升级端
  承载，剥离形态维持 R76 原通道）；未删任何既有判据（剥离+wrap 通道保留，仅
  加互斥让位守卫）；未执行 git commit（主代理负责）。

---

## 1. 时间窗修正（重要：主代理的窗口假设不成立）

主代理假设回退必为 B1b/B6 两批新判据误触发。**实测否定**：

| 分析器状态 | risk_calculation 读数 |
|---|---|
| a9ac63e3（Round75 fix3 落地态，git worktree 实测） | 41/43，get_daily_summary Equal |
| 57f3e944 / 1a0f2760 / 9725103d（round1 评审产物 + B1b + B6，worktree 实测） | 40/43，get_daily_summary Different bytecode |

a9ac63e3 → 57f3e944 在 core/ 的唯一代码差异是 `region_ast_generator.py`
+419/-2 行（c53df077 随 round1 start 落地的在途变更：[R76-A1/A2] 前导守卫
wrap + [R75 fix1] B1a `_graft_pending_operand` 嫁接）。**回退根因在这段在途
变更**；B1b/B6 两批零责任——它们落库时 `*OK.py` 存量产物未再生成，主代理
全量验证（再生成 402）时回退才显形。

## 2. 首分歧与完整传播链（trace 实证，非臆测）

首分歧与主代理取证一致（orig=真身 pyc / new=再生产物重编译，剔行号）：
- orig：`... CALL(append); POP_TOP;` + 独立测试 `LOAD_FAST self; LOAD_ATTR
  _engine; LOAD_ATTR benchmark_portfolio; POP_JUMP_FORWARD_IF_FALSE to 4066`
- new：`... CALL(append)` 直接被 `POP_JUMP_FORWARD_IF_FALSE to 4042` 消费，
  benchmark 测试整体消失，产物呈 `if self._returns.append(total_return):`

块布局事实（插桩 trace）：块 3388 是 `summary.update({... 'returns': <三元> ...})`
内嵌三元的 TernaryRegion（entry=2716，blocks=[2716,3282,3286,3388]）的
**merge_block**，其尾承载 ①普通语句（today=/date=/STORE_SUBSCR）②纯表达式
语句 `self._returns.append(total_return)` ③独立 if 测试 + PJIF（fall-through
3660=顶层 IfRegion entry，目标 4066=该 if 的 merge）。benchmark if 自身无
region（条件块归属三元）。传播链四步：

1. `[R76-A1/A2] MERGEPATH 剥离`（`_try_build_ternary_merge_consumer_expr` 内
   `_detect_leading_guard(region.merge_block)`）命中：把 ③ 的条件指令段判为
   「外层守卫」，从 R40 W45 切分的 `_rest_clean` 中剔除，并在 3660 登记
   `_leading_guard` wrap 记录（`GUARD_CAND then=3660 REGISTERED extent=[3952,
   3660,3722,3838]`）。
2. `_build_statements_from_instructions(_rest_clean)` 尾条件段已空 → 产出
   `[..., Expr(append)]`（trace：`BSFI out=['Assign','Assign','Assign','Expr']`，
   尾部 PJIF@3658 仍留在流中）。
3. `_emit_post_extra_with_if_upgrade`（既有 R59-B 机制，不在在途变更 diff 内）：
   merge 块尾是条件跳转 + post_extra 尾是可绑定类型 Expr → 合成
   `if <post_extra[-1].value>:` 并把 fall-through 侧区域（IfRegion 3660、
   Region 3952）内联生成、全部标记 generated。**绑定的是 ② 的 append 调用
   表达式，真测试丢失**。
4. wrap 记录孤儿化：generate() 顶层循环到 IfRegion(3660) 时
   `allgen=True` → continue 在 `_r76g_rec` 读取之前（trace 无 CONSUME 行）。
   wrap 的「顶层循环消费」契约被三元自身发射路径抢先破坏。

## 3. 修复（唯一改动文件：core/cfg/region_ast_generator.py，+63 行含注释）

### 3.1 判据与 C 条款

在 MERGEPATH 剥离点加 **[R1-REG 守卫·R59-B 升级消费端让位]**（file:line：
`core/cfg/region_ast_generator.py` `_try_build_ternary_merge_consumer_expr` 内
R40 W45 `_rest_clean` 段，锚点 :42542-42586 一带；docstring 三要素同步于
同方法 :42434-42453）。让位判据（同层发射后结构事实）：

1. `_probe_keep = _build_statements_from_instructions(_rest_clean)`（**未剥离**
   探针）末语句恰为 `Expr` 且值类型 ∈ 升级端可绑定集合
   `Attribute/Subscript/Call/Name/BinOp/UnaryOp/Compare`（与
   `_emit_post_extra_with_if_upgrade` 的判定集合逐字一致）；
2. `_probe_strip = _build_statements_from_instructions(_rest_stripped)`（剥离
   探针）== `_probe_keep[:-1]`（守卫条件段恰好物化为这**单条**尾 Expr，无多
   语句碎片）。

两条件同时成立 ⇒ R59-B 升级端必然把守卫条件（裸物化的尾 Expr）绑定为 merge
尾跳转的测试并单次发射 `if <守卫条件>: <extent 区域单元>` ⇒ **不剥离、撤销
登记**（`delattr(_grd_then, '_leading_guard')`，delattr 幂等约定与消费端一致）；
任一不成立 ⇒ 维持 R76 剥离+wrap 原通道（升级端不触达或多语句碎片形态，wrap
是唯一救援，quote.pyc 三合法单元所走 FSTRINGPATH 通道不受影响）。

- [C1] 只读本块指令流的两次构建产物与 `_detect_leading_guard` 返回的三元组；
- [C2] 两消费端（升级端 / 顶层 wrap）对同一尾跳转互斥——升级端发射后 extent
  内区域标记 generated，顶层循环 allgen continue，双发射被结构性排除；extent
  内子区域仍经各自 entry 被父单元消费；
- [C3] 登记三重校验在 `_leading_guard_candidate`；撤销记录 delattr 恢复块属
  性原状。

语义等价性：让位与 wrap 对同一尾跳转产出等价 `if <守卫条件>: <extent 单元>`
（trace 实证 extent=[3952,3660,3722,3838] 与升级端 `_if_body_regions` 同块
集）；守卫仅使「升级端能正确承载」的形态回到其承载，wrap-needed 形态逐位
保持。

### 3.2 排除的备选（如实记录）

- 「整体禁用 MERGEPATH 剥离」（实验 A，禁用后 risk 41/43）：被否——剥离在
  升级端不触达的形态仍是必要救援，删判据会让 B6 目标（quote.pyc
  load_get_price/get_price/load_bars_from_hundsun 同族形态）暴露回归风险；
- 「在升级端加 provenance 校验」：`_build_statements_from_instructions` 不返
  回指令溯源，需改既有 R59-B 消费端签名，影响面大于让位守卫，弃用。

## 4. 最小复现（真身码对象移植，已注明）

`test_repros/round1/r1_reg_get_daily_summary.py` + `r1_reg_get_daily_summary.pyc`。

- **合成切片不可用**（实测两版合成源码触发的都是无关既有缺陷：早退 return
  else 化 / merge 尾语句双发射，均非本回退），按任务预案移植真身码对象：
  从真身 pyc 提取 `PluginRiskCalculation.get_daily_summary` 方法码对象
  （marshal 原样搬运，`co_code`/`co_consts` 逐位相同，脚本内断言校验），
  以 compile 模板合成「module + class + 单方法」三单元 pyc。
- 模板带模块级绑定 `import six` / `RunType = None`：实测 3.11.7 编译器对
  `six.iteritems(...)` 的形态依赖该名字的模块级在场——在场发
  `LOAD_GLOBAL NULL+six; LOAD_ATTR`，缺席发 `LOAD_GLOBAL six; LOAD_METHOD`，
  缺绑定会让移植复现与真身重编译产物错位。
- 双向实测：守卫禁用（pre-fix 行为）→ get_daily_summary
  `Failure: Different bytecode`，产物 `if self._returns.append(total_return):`
  症状重现；守卫启用（现树）→ `success 3/3 100.00%`。全流程 = 生成脚本重编
  pyc → pycdc 反编译 → pyc_verify single --source。

## 5. 四项自测全量读数表

### 5.1 自测 1：risk_calculation 回退归零

| 项 | 读数 |
|---|---|
| `__init__.pyc`（--source 法，修复后新反编译产物） | **41/43 95.35%** |
| get_daily_summary | **Equal**（回退单元消除） |
| 剩余 2 失败 | `_on_publish_after_trading_end` / `_save_testds_to_csv`，均 Different control flow，= baseline failing_index 既有 |
| 工作树产物 `__init__OK.py` | 已用修复后分析器再生成并复核 41/43，514 行还原 `self._returns.append(total_return)` 独立语句 + `if self._engine.benchmark_portfolio:` |

### 5.2 自测 2：Round1 全组 25 复现 --source 法（临时产物写系统临时目录）

| 组 | 读数 |
|---|---|
| B1b 14 目标（r1_01/03/04/07/08/09/10/11/14/15/17/18/21/22） | **14/14 全 MATCH**（r1_21 3/3 含 MAKE_CELL） |
| 负对照（n1_01/02/03） | **3/3 全 2/2 100%** |
| MATCH 组（r1_02/05/06/12/13/16/19/20） | **8/8 全 2/2 100%** |
| 本批新复现 r1_reg_get_daily_summary | **3/3 100%** |
| 附加对抗组 rv_01…rv_10 | rv_03/05/09 1/2（守卫开关双向同读数=基线既有 MISMATCH，与本修复无关），余 7 个全 MATCH |

### 5.3 自测 3：真身哨兵

| 目标 | 本批读数 | 基线对照 |
|---|---|---|
| IQCommon/strategy/jq_trans_module.pyc | **65/65 100%** | 达标（65/65） |
| fly/data/quotation.pyc | **152/153 99.35%** | 持平（唯一失败 change_his_to_forward 为基线既有），零新增 |
| IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc | **118/128 92.19%** | 不低于基线 118/128 |
| fly/data/quote.pyc | **84/92 91.30%** | = B6 落地 84/92（含其 +3 增益），零新增 |
| round76 r76_01_guard_leak / r76_02_andchain_leading / r76_03_double_eval | **各 2/2 100%** | [R76] 基线保持（与本修复同族，重点复核） |
| round76 r76_b1a_jqcond / r76_b1b_orarm | **5/5、3/3 100%** | B1a/B1b 保持（round75 neg75_jqcond/jqcond2/repro75_jqcond 的 .pyc 不在树内，按批惯例不入库，无法重跑，以同族 r76 复现代偿） |

### 5.4 自测 4：failing_index 抽验（7 个 ≥ 6 个要求）

| 文件 | 基线 | 本批（--source 法） | 回退 |
|---|---|---|---|
| IQCommon/util/trade_info_utils.pyc | 36/41 | 36/41 | 0 |
| IQCommon/util/email_utils.pyc | 3/4 | 3/4 | 0 |
| IQEngine/core/executor.pyc | 9/10 | 9/10 | 0 |
| fly/common/future_contract_info.pyc | 27/29 | 27/29 | 0 |
| IQEngine/data/trading_dates_mixin.pyc | 13/14 | 13/14 | 0 |
| IQCommon/api/klinedata.pyc | 61/64 | 61/64 | 0 |
| IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc | 26/27 | 26/27 | 0 |

## 6. 遗留与交接

1. **时间窗修正入档**：本回退源于 c53df077 落地的在途变更（R76-A1/A2 wrap +
   R75 fix1 B1a 嫁接），非 B1b/B6；主代理 round1 验证结论中的「回退必为两批
   修复之一」假设应以此为准。
2. **rv_03/05/09 三个对抗目标 1/2**：基线既有 MISMATCH（守卫开关双向同读
   数），未在本批范围（属 B6 后续轮 while/ternary/assert 残留形态，见
   FIX_B6.md §5）。
3. **FSTRINGPATH 站点未加同款让位守卫**：quote 三合法单元全走 FSTRINGPATH
   且 CONSUME 正常、无升级端竞争（trace 零 UPGR 行）；若后续轮在 f-string
   路径发现同族孤儿化，可镜像本守卫。
4. **round75 归档复现不可重跑**：neg75_jqcond/jqcond2/repro75_jqcond 的 .pyc
   按批惯例不入库；本批以同族 r76_b1a_jqcond（5/5）/r76_b1b_orarm（3/3）代
   偿验证。
5. 本批零调试残留：全部 env 门控钩子（R1REG_DEBUG/NEUTER 开关）验后即除，
   `grep -c "NEUTER|_r1reg_dbg|R1REG_DEBUG"` = 0；三个临时 worktree 已移除。
