# Round 14 修复台账

基线（Round 13 收口，commit `f89b85f2`）：严格尺子 **325 / 402** 文件全一致，
函数 **5977 / 6204**；官方口径 351 ok。

---

## R14-D（已落地 + 主agent 复验）—— 同级推导式被焊接进容器字面量

**症状**：`{'k1': [..a], 'k2': [..b]}` 生成 `[x for x in [y for y in a]]` ——
键元组 `LOAD_CONST` 与 `BUILD_CONST_KEY_MAP` 整段消失，第二个推导式的 iterable 被
第一个推导式的 AST 顶替。真实目标 2 个：
`plugin_system_simulation/broker.pyc <module>.SimulationBroker.save`（22→15）、
`live.pyc <module>.DefaultLiveBroker.save`（16→12）。

**根因（两处，均为判据缺失而非风格问题）**
`core/cfg/comprehension_generator.py`：

1. `:114-144` 相邻 `MAKE_FUNCTION` 对的「是否焊接」判据失效。旧判据先找第一个
   `GET_ITER` 之后的 `_first_call_end`，再对 `instrs[_first_call_end:_ci2]` 做
   「是否只有闭包装载」弱检验 —— 该检验**双向恒真**：真嵌套时切片为空（`all([])=True`），
   兄弟时切片恰为兄弟自己的 `LOAD_CONST <code>`，被 `LOAD_CONST + co_name` 分支放过。
   **正解 = 装载次序判据**：推导式的可调用对象先装载、可迭代对象随后装载，故
   真嵌套时第二个 code 对象的索引 `_ci2 < _first_get_iter`（内层是在外层 iterable
   构造期间装载的）；兄弟时 `_ci2` 出现在第一个推导式调用链之后。判据一条即覆盖
   旧的两个方向，旧「闭包装载」检验通过它之后必然恒真 ⇒ 直接删除，不改变可焊接集合宽度。
2. `:196` `_expr_build` 消费者白名单缺 `BUILD_CONST_KEY_MAP` 与全部 `CALL*` /
   推导式累加 / 容器合并 op ⇒「推导式结果被更大表达式消费 ⇒ 放弃焊接、交回通用路径」
   这道保险从未触发，`:207/:215` 于是用 `prev_end = len(instrs)` 把整块声明为已生成。
   补齐后白名单即「焊接只能认领推导式自身的指令」这条不变式的机器可读形式。

**归约方式 / AST 映射**：容器字面量区域的**每个 value 子区域各自归约为一个表达式节点**；
`BUILD_CONST_KEY_MAP` 的宿主节点类型是 `Dict`，不是其任一子推导式的 `ListComp` 类型，
因此禁止在推导式焊接路径里认领宿主 op 的指令。通用路径
（`core/cfg/ast_generator_v2.py:948` 弹键元组 + count 个值；`:1274/:1288-1313` CALL）
本来就能正确合成父节点。

**主agent 复验（实测，非转述）**
```
round14      repros=17  MISMATCH=0  MATCH=17  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round13      repros=25  MISMATCH=14 MATCH=11 ERROR=0 UNEXPECTED=0  NOT-REPRODUCED=2
round14_join repros=16  MISMATCH=11 MATCH=5  ERROR=0 UNEXPECTED=0  NOT-REPRODUCED=0
strict       OK 29/29 broker.pyc   OK 29/29 live.pyc   函数级 58/58
```
⇒ **2 个 pyc 翻正到 100%**（broker 28/29→29/29，live 28/29→29/29）。
`test_repros/round14/run_all.py` 的 10 个 `MISMATCH` 期望已翻成 `SENTINEL`
（回归哨兵：一旦回到 MISMATCH 即记 REGRESSED）；`round13` 的 `r13_05` 同。
差集核对：修复只让 `r13_05` 由 MISMATCH→MATCH，无其它形状变动。

**影响面**（修复工程师只读 A/B）：全语料含 `comp` 的 96 个 `ok` 文件中 94 个产物字节不变，
差异恰为 broker/live；33 个 `partial`+comp 文件全部字节不变（含 quotation/klinedata/function）。

---

## A-1（修复工程师进行中）—— 值上下文 BoolOp 的 merge 块承载下一条 if 时被整体跳过

`region_analyzer.py:15910` 无条件 `continue`，正确判据 `_ternary_merge_hosts_next_if`
（`:25398`）已在同文件、只被 Ternary 路径（`:15770`）调用。目标：
`profiler_func.pyc ×3`（IQCommon + IQData/utils 各翻正 1 个文件到 100%）。
证据与判据见 `test_repros/round14_join/ANALYSIS.md`（11 MISMATCH + 5 MATCH，全部实测）。

**A-1 落地（主 agent 实测，非转述）**

区域归属层新增**例外 3**（与既有 `loop_condition_blocks` 同源，是原则 2 的明确例外，
不是跨区域启发式补丁）：
- `region_analyzer._value_merge_hosts_next_if(block, expr_region)`：值上下文表达式区域
  （BoolOp / 三元）的 merge_block 在**语句边界**之后承载下一条语句的 if 测试。判据全部
  是语言级的：值已被 `POP_TOP`/`STORE_*` 消费、消费点严格在块尾之前、块尾条件跳转的两个
  后继完全落在该表达式区域之外。
- 接入点 `:15915` 的 `_is_merge_next_stmt_if`，与例外 1（`_is_merge_if_condition`）、
  例外 2（`_is_merge_with_guard_clause`）并列；`:15948` 的前缀/后缀切分对三种例外共用
  `region.guard_clause_prefix_end`。
- `_ternary_merge_hosts_next_if` 逐条比对后统一委托给新函数：唯一新增判据是
  `is_condition_context`，而 `TernaryRegion` 没有该属性 ⇒ 行为不变（下方 A/B 实测印证）。
- `region_ast_generator`：抽出 `_boolop_merge_owner_for`，使「生成期丢弃 IfRegion」路径与
  `_if_generate_normal` 双角色发射路径共用同一个归属判据；另加 `prefix_stmts_pending`
  一次性延迟记录。

**窄化：`_conditional_value_producing_arms`（修掉唯一创伤）**

例外 3 初版在 `IQCommon/utils.pyc <module>.parse_db_url` 上把整个
`if driver is None: ... else: ...` 吞掉（23/26，HEAD 为 24/26）。根因：
`driver = config.pop('driver', None) or DB_DEFAULT_DRIVER.get(dialect)` 的 merge 块
同样是「同块 store + 同块 if 测试」形状。区分它的不是实例而是**后继形状**：若两条后继
各自以「对同一目标的一次 `STORE_*`」结案（较短分支再补一条 `JUMP_FORWARD` 跳过另一分支），
则该测试的值就在其自身分支内产生并落库 ⇒ 它是**赋值表达式（三元）的测试**，不是下一条
语句的 if；例外 3 必须拒绝，让 merge_block 回到原有的单一归属路径。正例 `if PY35:`
（then 臂是 `import` + `try` 的多语句体、无对称 store）保持翻正。

**归因 A/B（文件级换件，只读、不写产物；`D:/Temp/r14_ab2.py`、`r14_ab3.py`）**

14 文件集（11 个劣化候选 + arg_checker + profiler_func ×3）：
```
all_HEAD（三个 core 文件全退回提交态）  530 / 589
A-1 首版                               533 / 589   +_is_valid_interval  +3×<module>  -parse_db_url
A-1 + 窄化判据                          534 / 589   优势 4 个函数，劣势 0 个
```
`klinedata / common_func / real_quote / plugin_fly_data__init__ / history_api / flytools /
market_time / quotation / quote_handler / json_persistance / base_validator` 这十一处劣化，
在 `all_HEAD` 与本轮之间**数字与缺陷集合完全相同**（含 `klinedataOK.pyc` 的「数值相等但
缺陷集不同」：`get_history_common,get_price_common` ↔ `np_tp_pd,to_pd_result`）
⇒ 属 Round 13 提交遗留的「已提交产物优于已提交核心」债，归 SubTask 13.3，非本轮 hunks 造成。

**门禁顺序验收（实测）**
```
quotation.pyc 单验：148/150 -> 147/150 WORSENED（产物门自动回滚；all_HEAD 同为 147 ⇒ 遗留债）
全量产物门 406 targets：CLEAN=327 UNCHANGED=67 WORSENED(回滚)=9 REGRESSION(回滚)=2 NO-OKPY=1
                        elapsed=117s
翻正到 100%：IQCommon/profiler_func 16/16、IQData/utils/profiler_func 14/14
其余改善：arg_checker 48/49、38/39、42/43（各 +1）；IQEngine/utils/profiler_func 16/17（+1，未翻正）
round14_join  repros=16 MISMATCH=11 MATCH=5  UNEXPECTED=0（前缀重复 +13 仍在 → 13.1/13.2）
round14       repros=17 MISMATCH=0  MATCH=17（10 个 SENTINEL 全部保持）
```
被本轮产物门改写的两个重复源产物（`klinedataOKOK.py` / `klinedataOK_checkOK.py`）已按 HEAD
字节复原（`git show` 取 blob + CRLF 归一，非工作区回退命令），不随本轮提交。
