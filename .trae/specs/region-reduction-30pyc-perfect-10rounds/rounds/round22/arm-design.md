# Round 22 设计（arm-design）：漂移族三条判据收进区域归约框架（J1′ 塌缩细化 / J2′ or-汇合点 / J3′ 删 V-M）

落地前 HEAD = `46e752ab`（Round 21 收尾）。诊断出处：任务 #25「漂移族 J1/J2 非破坏性中和」
与 Round 21 收尾后的产物/核漂移二分（任务 #22）；本轮实测见 `fixes.md`，收尾见 `OUTCOME.md`。

---

## 一、靶子：`pyc_index.json` 的条目与当前核产物背离

**索引自证**（读 `pyc_index.json` 的 `last_tested_round`）：402 条里 **392 条 = r10**、
2 条 = r12、1 条 = r16、7 条 = r17 —— Round 18/19/20/21 **一条都没回写过**（这四周期的
`rounds/roundNN/OUTCOME.md` 只记 `single` 与 `stats`，没有 batch 步骤）。⇒ 索引里绝大多数
数字是 Round 10 那版核产出的，之后 R11–R21 十次核改动基本没有回写通道。

回不去的原因写在 `scripts/pyc_batch_verify.py:358-361`：

```
include_ok=True 时**连已标记 ok 的条目一起重跑**（全量复验）。
这是必要的：默认模式跳过 ok 条目，一旦某文件被标成 ok 就永不复验，
后续改动使其退化也不会被发现，索引会长期虚高（本项目曾因此把
334 ok 的真实状态记成 370 ok）。每轮收尾应用 include_ok=True 复核。
```

用官方尺（`scripts/pyc_batch_verify.py` 里的 `bytecode_diff`，与批量写索引同一实现）在当前
HEAD 上逐文件重测语料，与索引条目逐条对照，**11 个文件不一致**（其余条目一致）：

| 文件 | 索引条目写的 | 当前核官方尺实测 | 差 | 该条 `last_tested_round` |
| --- | --- | --- | --- | --- |
| `IQCommon/api/klinedata.pyc` | 40/45 | 38/45 | −2 | r10 |
| `IQCommon/manager/instance.pyc` | 29/32 | 31/32 | **+2** | r10 |
| `IQCommon/util/common_func.pyc` | 17/21 | 16/21 | −1 | r10 |
| `IQCommon/util/trade_info_utils.pyc` | 40/40（ok） | 38/40 | −2 | r10 |
| `IQEngine/plugins/plugin_fly_data/__init__.pyc` | 19/20 | 18/20 | −1 | r10 |
| `IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc` | 18/18（ok） | 17/18 | −1 | r10 |
| `IQEngine/plugins/plugin_system_persist/json_persistance.pyc` | 7/7（ok） | 6/7 | −1 | r10 |
| `fly/common/custom_tools.pyc` | 6/6（ok） | 5/6 | −1 | r10 |
| `fly/common/flytools.pyc` | 64/65 | 63/65 | −1 | r10 |
| `fly/common/market_time.pyc` | 10/10（ok） | 9/10 | −1 | r10 |
| `fly/data/quote_handler.pyc` | 50/57 | 47/57 | −3 | r10 |

其中 5 条索引标着 `ok`（`trade_info_utils`、`history_api`、`json_persistance`、
`custom_tools`、`market_time`）而实测有函数不匹配 —— 即索引把不匹配的记成匹配。

**逐提交二分**（`git archive <rev> core bytecode pycdc.py _r10_strict_check.py | tar -x` 建镜像，
官方尺只测这两条）：`trade_info_utils` + `custom_tools` 在 `675ca714`（Round 10）与
`8a1b1def`（Round 11-12）为 46/46，自 `f89b85f2`（Round 13「修 return 被降级为 break，
回退 A2 前缀判据」）起为 43/46。⇒ 这两条不是新缺陷，是 R13 的改动使既有产物退化、
而索引再没被复验。

`instance.pyc` 是**反向**背离：当前核比 r10 条目多匹配 2 个函数 ⇒ 索引低估。本轮不单独
"订正"它，交给 `batch --all` 复测自动回到实测值。

## 二、三条判据（都在区域归约框架内，只删不增）

**逐补丁归属**（严格尺子，镜像 `D:/Temp/r23prep/mirror/{base,j1g,j2p,j3}`，每条只打一个补丁，
11 个漂移文件；记录 `D:/Temp/r23prep/ab/attr2_*.jsonl`，汇总 `probes/attr_sum.py`）：

| 单补丁 | 修好的函数（`orig=… decomp=…` 为基线读数） |
| --- | --- |
| J1′ | `klinedata.np_tp_pd` 169→167、`klinedata.to_pd_result` 185→183、`common_func.to_pd_result` 185→183、`history_api.to_pd_result` 185→183、`real_quote.get_real_daily_kline` 210→212、`real_quote.get_real_minute_kline_bk` 169→171、`plugin_fly_data/__init__.ApiMethodPlugin.resist_api` 107→105、`json_persistance.JsonPersistance.persist` 78→76、`flytools.get_mem_under_oom_status` 47→18、`quote_handler.get_all_fundamentals_daily` 73→71、`quote_handler.get_all_valuation` 73→71、`quote_handler.get_all_valuation_new` 73→71 （12 条） |
| J2′ | `trade_live_broker.cancel_order` 89→71、`market_time.trade_is_open` 97→89 （2 条） |
| J3′ | `flytools.whitelist_filter` 116→114 （1 条） |

合计 15 条，与任务 #25 的「非破坏性中和 15 个函数」一致。两条例外如实登记：
`quote_handler.get_kline_local`（基线 760→676，**丢 84**）单补丁都不动它，只有三补丁同时在场
才回到 760→682（J1′ 恢复了臂结构，J2′ 的链判据才用得上）；`api_base.get_history_df`
（基线 1742→1722）在 J2′ 下退化为 1742→1718（严格尺多丢 4 条；官方尺不受影响，仍 23/25）——
这条退化是买 J2′ 那 2 条战果的代价，下面 J2′ 一节末尾登记了试图消掉它的两条细化以及它们
为什么被否决。

### J1′ — 分析层 `_identify_conditional_regions` 的汇点臂塌缩守卫细化

（`core/cfg/region_analyzer.py` 17129 段）。既有判据 `self._if_arm_is_sink(...)` 为真就把
`merge` 定为 `else_succ`，随后 `_collect_branch_blocks` 按这个 merge 重新收臂。实测它在两类
形状上过火（作用域分裂、共享隐式出口，见下 (a)/(b)）：merge 认定错 ⇒ 臂块集跟着错 ⇒
产物要么少语句要么多语句 —— 被 J1′ 中和的 12 个函数（`47→18`、`78→76`、`210→212` 等）
就是两种方向都有。补两条同层判据：

```python
_25b_arm_loop = self._find_enclosing_loop(then_blocks[0])
_25b_else_loop = self._find_enclosing_loop(else_succ)
_25b_same_loop = _25b_arm_loop is _25b_else_loop
_25b_shared_rn = (any(self._is_return_none_block(b) for b in then_blocks)
                  and any(self._is_return_none_block(s) for s in else_succ.successors))
if (not _25b_else_is_cond and _25b_same_loop and not _25b_shared_rn
        and self._if_arm_is_sink(then_blocks, then_stop)):
    merge = else_succ
```

* `(a)` 作用域分裂：臂入口与候选汇合点的最内层 enclosing loop 不同 ⇒ `else_succ` 不可能是
  本 if 的汇合点（两臂在不同作用域里掉出）。复用的是既有 `_find_enclosing_loop`，比的是
  **同一个 IfRegion 自己的两个成员**，不跨层。
* `(b)` 共享隐式出口：臂内已有裸 `return None` 块且 `else_succ` 的直接后继也是 ⇒ 臂的
  "汇点"性其实是函数级隐式 `return None`，不是一次性掉出到 merge。复用的是既有
  `_is_return_none_block`，只看臂内块与候选块的**直接**后继。

### J2′ — 生成端 `_discover_predicate_and_chain` 的 or-短路汇合点识别（只删不增）
（`core/cfg/region_ast_generator.py` 16368-16383，方法末尾 `return {'blocks': chain, 'op': 'and'}` 之前）。
反向收集到的 and 链，其**链首块**可能同时是「上一条语句的表达式汇合跳转落点」或
「某个 `or` 的右操作数入口」。以链首重建整条 test 时，若是后者，左析取支 X 整体丢弃
（`MarketTime.trade_is_open` 实测丢 `>= '0915' and <= '1130'` 一半，`orig=97 decomp=89`）。
落地版只问一件同层的事：发行那条前向跳转的前驱块，自身是不是**另一个纯操作数求值块**
（复用既有 `_chain_block_is_pure`）。

```python
_head = chain[0]
for _pj in _head.predecessors:
    if _pj in chain or _pj.start_offset >= _head.start_offset:
        continue
    _pl = _pj.get_last_instruction()
    if (_pl is not None and _pl.argval is not None
            and _pl.argval == _head.start_offset
            and _pl.opname in FORWARD_CONDITIONAL_JUMP_OPS
            and self._chain_block_is_pure(_pj)):
        return None
```

不命中就原样交给既有的单条件/嵌套生成路径 —— 与该方法既有的两条放弃守卫（`inline_boolop_chains`
缺失时的区域归属守卫、elif 条件块唯一归属守卫）同构：**只放弃一次重建，不新增任何块归属**。
三种实测形状，落地判据各自看到什么：

| 出现处 | 链首 `_head` 的更早前驱 `_pj` | `_pj` 是纯操作数块？ | 结果 |
| --- | --- | --- | --- |
| `fly/common/market_time.trade_is_open` | 172（`>= '0915'`，链 `[196,208]`） | 是 | 放弃重建，保 `X or (A and B)` ⇒ 严格尺 97→89 |
| `IQData/api/api_base.get_history_df` | 2670（链 `[2704,2818]`） | 是（上一条语句表达式内部汇合恰落在本语句求值块起点＝语句边界） | 同样放弃重建 ⇒ 该函数 −20→−24（官方尺不变 23/25）＝代价 |
| `fly/data/quote_handler.get_kline_local` | 344（链 `[420,458]`） | 是 | 放弃重建（与 J1′ 同场时才有意义） |

**两条被否决的细化**（登记，免得下一轮重走）：想消掉 `api_base.get_history_df` 那 4 条，就得给
上面的判据再加一条"这条跳转其实归属某个区域"的限定。试过的两种写法与判决：

| 变体 | 追加限定 | 全量语料 A/B（402 pyc，严格尺） | 最小复现电池（37 复现） |
| --- | --- | --- | --- |
| J2r | `get_entry_region_for_block(_pj) is not None` | 改善 10 / 破坏 0 / 加重 0，且 `api_base` 不再退化 —— 语料级看严格优于 J2′ | **FAIL**：`r22_16_j2_andor_three_disjuncts` NOT-FIXED（`orig=17 decomp=9`），日志 `D:/Temp/r23prep/batt_j2r.txt` |
| J2r∨块归属 | `_pj in region.blocks or get_entry_region_for_block(_pj) is not None` | 同上 | **FAIL**：同一条锚点同一读数，日志 `D:/Temp/r23prep/batt_r3.txt` |

被它们丢掉的形状（电池锚点，语料 402 个 pyc 里**没有**）：

```python
def f(a, b, c, d, e, g):
    if a and b or c and d or e and g:
        return 1
    return 0
```

中间那条 and 链的链首，其发跳转前驱是纯操作数块、但**没有自己的区域归属**（`or` 的短路汇合点
不要求成区域），于是追加限定使判据不触发 ⇒ 链被重建 ⇒ 左半 `a and b or c and d` 整体丢掉。
⇒ 追加限定在 `trade_is_open` 一类形状上与 J2′ 等价（`r22_12` 两版都 FIXED），却在电池形状上
更弱；它的语料级"零破坏"是覆盖盲区造成的，不是判据本身正确。**语料全量测不能替代最小复现集**
是本轮的收口结论。

### J3′ — 删生成端 `_is_orphan_boundary_nop` 的 V-M 判据
（`core/cfg/region_ast_generator.py` 41230-41237，同时删其 docstring 里 `V-M (条件汇合锚点)` 那条）。
V-M 的写法是 `for blk in self.cfg.get_blocks_in_order()` 全 CFG 扫描「存在任何条件跳转以本 NOP
为汇合目标」⇒ 这是**跨区域的全局条件**，正是禁区；它把合法的语句边界折叠残留也否决掉，
使 `while False: pass` 该还原时不还原。删除后余下 V-T/V-S/V-B/V-L 四条，与该 docstring
「以下四类结构性 NOP」的原话重新自洽（原先是五类却写"四类"，这句话本身就是 V-M 越权的痕迹）。

## 三、原则核对

* **归约顺序（最内层→最外层）**：三条都不改变归约顺序；J1′ 只否定一次 merge 认定，J2′
  只放弃一次 test 重建，J3′ 只删一条否决分支。
* **每块唯一归属**：J1′ 的 `(a)` 正是为「兄弟结构头块不得被循环节/臂双重认领」；J2′ 的
  放弃路径把链交回既有单条件/嵌套生成，不新增归属。
* **嵌套区域作为单个抽象节点**：三条都不引入"跨层查找"，全部只读本区域/本链/本块的直接成员。
  正因如此，被否决的 J2r 细化（要求前驱块承载区域归属）虽然语料级零破坏，实质是把判据
  从"本链的同层事实"改成了"跨层的区域登记表查询"，与这条原则相悖。
* **禁止 pyc 特判、禁止匹配名字与常量与原始偏移**：判据只用 `_find_enclosing_loop`、
  `_is_return_none_block`、`_chain_block_is_pure`、`FORWARD_CONDITIONAL_JUMP_OPS`
  这些既有同层构件；注释里的 pyc 名只是证据出处，不进判据。

## 四、门禁顺序（实际执行序）

最小复现电池（`test_repros/round22_drift/run_all.py`，37 复现，before/after 双镜像核）必须先过 ——
本轮正是它把语料级"零破坏"的 J2r 判回炉；随后 单 pyc 修到完全 OK（`json_persistance`、
`market_time`）→ `quotation.pyc` → 全量 `batch --all --round 22` 复验（把索引拉回实测）→ `stats`。
