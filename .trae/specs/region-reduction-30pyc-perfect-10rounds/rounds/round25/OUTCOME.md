# Round 25 落地记录：R25-A（elif 链 post-chain 汇合块被误认领为 else 臂 · 前驱侧对偶判据）

落地提交前基线：`8a0c269a`（Round 24 R24-A 之后）。
被改文件：`core/cfg/region_analyzer.py`（唯一），
`6df13cdaf815920c` → `7a88adcedf5249ef`（+49 行 / −0 行，纯插入，无删改既有语句）。
`core/cfg/region_ast_generator.py` 本轮未动（`a365c378e6a40fed`）。

## 一、缺陷与根因（详述见 `fixes.md`、`arm-design.md`）

缺陷族：一条 `if / elif / …` 链的**所有臂都以 `RETURN_VALUE` 终结**时，链之后唯一的直落续块
（post-chain 语句块，通常是函数末尾的 `return X`）被 `_check_elif_chain` 认领为 `final_else`，
即被当成链的 `else` 臂。后果有两层：
1. 该语句被移进 `else` 臂，链尾次序整体后移（官方尺上表现为等长换位）；
2. 外层 `if` 因失去真实末语句，其出口退化为函数级隐式 `return None`，产物多出成对的
   `LOAD_CONST None; RETURN_VALUE`。官方尺的 R97 `_trim_spurious_intermediate_returns`
   在对齐位置静默剪掉这些对，于是 `data_proxy.get_bar` 读成 `86/86` 等长 —— 换位是尺子伪影，
   严格尺同一函数读成 `orig=86 decomp=90`。

既有的降级规则（`_chain_merge_candidates` 的臂末共同后继交集、`_body_succs_to_fe` 计数）
**全部只在「臂末块的 successors」一侧取材**；本形臂末是 `RETURN_VALUE`，没有后继，
交集恒空、计数恒 0，规则永不触发。

## 二、判据 R25-A（同层 · 前驱侧对偶）

位置：`_build_elif_region` 内，紧跟既有 `_body_succs_to_fe >= 1` 降级块之后
（`core/cfg/region_analyzer.py:19122` 起）。

同一结构事实的对偶表述改从 `final_else` 候选 F 的 **predecessors** 一侧取材：
CPython 3.11 把 `if/elif/…/else` 布局为「每个条件的假边指向下一个条件，只有最后一个条件的
假边指向 else 体」⇒ else 体被链内进入的方式唯一；任何位于臂体内（`then_blocks ∪ 各 elif body`）
且**不是本链条件块**的块，以 `FORWARD_CONDITIONAL_JUMP_OPS` 且目标正是 F 入口而进入 F，
只能是该臂中嵌套条件的假分支掉出整条链，而链的掉出口恒在 else 体之后 ⇒ F 是链的汇合块，
不属于任何臂，降级为 merge（`_chain_merge_candidates |= F`，并从 `final_else` / `else_blocks` 摘除）。

同层性：只读链的块集合（`conditions` / `then_blocks` / `bodies`）、F 的前驱及其末指令的跳转目标，
即区域归约算法原则 2（每块唯一归属）与原则 4（入口引用语义）在本层的直接取证；
不读偏移量次序、不读函数名、不读源码形状，不引入跨层启发。

## 三、门禁（严格串行，全部对**落地字节**复跑；原始日志见 `logs/`）

| # | 门禁 | 结果 |
|---|---|---|
| G0 | 落地字节自证 | `mkmirror25.py` 由工作树重建 `mirr/landed25`，44 文件全树逐文件比对：`region_analyzer 7a88adcedf5249ef MATCH`、`region_ast_generator a365c378e6a40fed MATCH`；`diff -rq landed25 patchB25` 无差异 ⇒ 电池测的字节即 402 A/B 测的字节 |
| G1/G2 | 最小复现电池（5 例，`dump/wl25_repro.txt`） | `TALLY {"FIXED":3,"BROKEN":0,"MOVED":0,"SAME":0}`；`d3case_cd/efg/hi` 三个 FAIL 复现 `2/3→3/3`、`3/4→4/4`、`2/3→3/3` 翻转，两个 CONTROL（`d3case_a/b`）保持 `2/2` |
| G3 | D3 语料锚点电池（22 文件 / 62 函数，`dump/wl25_d3all.txt`） | `FIXED=4 BROKEN=0 MOVED=1 SAME=57`；翻转 `api_base 47/48→48/48`、`executor 9/10→10/10`、`data_proxy 8/9→9/9`、`quotation 142/143→143/143` |
| G3′ | 上一轮（R24）锚点电池（9 文件，`anchors24.txt`） | `FIXED=2 BROKEN=0 MOVED=1 SAME=6` —— R24-A 的锚点无一回退 |
| G4 | 全 402 文件 A/B（head25 vs patchB25，同一 runner、独立产物目录） | `REGRESSION: 0`、`ERR: 0`、`IMPROVED: 4`、`SAME: 396`、`MOVED: 2`；爆炸半径 = **6/402 产物**；五个反例逐字节不变：`IQCommon/manager/instance.pyc`、`IQCommon/util/cgroup_utils.pyc`、`IQData/manager/plugin_manager.pyc`、`IQEngine/core/plugin_manager.pyc`、`…/trade_live_broker.pyc`（另 `arg_checker ×3`、`profiler_func ×3` 承重锚点亦不变） |
| G5 | `single` 四靶 | `api_base 48/48 100.00%`、`executor 10/10`、`data_proxy 9/9`、`fly/data/quotation.pyc 143/143 100.00%`（本轮首次全绿） |
| G6 | `batch --index pyc_index.json --round 25 --all` 全量复验 | 索引仅动 4 个字段：`last_tested_round` 402 条 24→25；`matched_functions`/`decompile_status`/`bytecode_match_rate` 各 4 条（上表四文件 `partial→ok`）。其余字段零改动；文件仍纯 CRLF（4553 CRLF / 0 LF-only / 无 BOM） |

`stats --index pyc_index.json` 的输出原样归档在 `logs/stats25.txt`，本记录只逐条交代
上面 4 个索引条目的变化，不与任何旁路计量互推。

## 四、6 个产物变化的逐项交代（每个都是「删掉一条虚构 else / 把误挪进臂的语句退回链后」）

* `IQEngine/api/api_baseOK.py` `cancel_order`：`elif engine.can_cancel_order(...)` → `if …`，
  `return order_obj` 退回链后直落。⇒ 48/48。
* `IQEngine/core/executorOK.py` `check_before_trading`：删掉虚构的
  `else: if …: pass elif …: pass` 5 行。⇒ 10/10。
* `IQEngine/data/data_proxyOK.py` `get_bar`：链的 `else: return self.BarData(…, dt)` 退回链后。⇒ 9/9。
* `fly/data/quotationOK.py` `change_his_to_forward`：同形。⇒ 143/143。
* `fly/common/custom_toolsOK.py` `memory_handler`：`else: return False` 退回链后（该函数仍有
  独立缺陷：严格尺 `decomp 71→69`，官方尺仍 `mismatch`）。
* `fly/simtradding/pboxAccount_jupyterhubOK.py`：`else: return (account, '登录成功')` 退回链后，
  该文件官方读数不变（`4/4`），函数级错位仍存。⇒ 记为残余，不算翻转。

## 五、本轮发现的**计量仪器**缺陷两条（非 core 缺陷，但足以伪造判决）

1. **臂隔离失效**：`batt25.py` 的 `sys.modules` 清理按 `'core.'` 前缀匹配，漏掉 `core` 包对象本身，
   残留的 `core.__path__` 让第 2 个 arm 重新解析到第 1 个 arm 的目录 —— 于是 arm 2 测的是 arm 1
   的字节，TALLY 读成 `SAME=45 / FIXED=0`（真实情况是候选改了 `data_proxy` 产物）。
   已改为「凡 `__file__` 落在任一私有镜像下的模块全部清除」+ 逐 arm 断言
   `core.cfg.region_analyzer.__file__` 必须 startswith 本 arm 根目录。
   **同样的缺陷在 `D:/Temp/r24land/probes/batt24.py:50-51`，因此 Round 24 及更早各轮「电池」证据
   须视为未证**（`single` / `batch --all` / `stats` 每进程只加载一个核，不受影响）。
2. **产物命名碰撞**：`pool25.py` 用 `<basename>OK.py` 落盘，语料里约 30 个不同的 `__init__.pyc`
   在同一个扁平产物目录里互相覆盖，4 个并发 shard 还争用同一 `__pycache__` 条目 ——
   制造出一条假的 `plugin_system_debug/__init__ 6/6 → 0/6`「回退」和一条 `PermissionError`。
   已改为按**整条相对路径**改名（`/`→`__`，并为镜像外的复现文件把 `:`→`_`，
   否则 `py_compile` 报 `WinError 87` 而电池只打印 `0/0`）；同时给电池加了**空读数即硬失败**
   断言：任一记录 `error` 非空或 `total_functions` 为 0 立刻中止，`0/0 -> 0/0` 是仪器坏了，
   不是没有缺陷。
   本轮所有引用数字都在修好这两条之后重测得出。

## 六、残余与移交

* `custom_tools.memory_handler`：`else` 误认领已消，仍差 4 条（`65` vs `69`，jump 1 / true 21），
  属另一族（链内语句次序），列为 Round 26 候选锚点。
* `pboxAccount_jupyterhub`：产物次序改善但未翻转，与 `wizard_quant_api`（`48/53`）同列 D2 过量发射族，
  仍是任务 #42。
* 异常布局族 #39、整块丢失族 #41、`decrypt_database_url +29 / log.setup −67 / fly_api.base −21×2` #43、
  `+1` 翻转对 #44 未收口，Round 26 继续单线推进。
* `quotation.pyc` 自本轮起 `ok`，后续轮次它不再是「零副作用」金丝雀，而是**必须保持 143/143**
  的承重锚点；任何让它跌出 143 的候选直接否决。
