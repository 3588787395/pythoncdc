# DIAG/FIX B139c — BoolOp 链头「条件段起点回溯」的判别式：J-判据实测不足，本轴不落地

票号 **B139c**（接替在每日用量上限中断死的 B139b；B139b 只留下 `FIX_B139B_*.md` §0 的基线表，无补丁）。
**全程镜像施工**：镜像 `D:/Temp/r139m/wt`（`core bytecode parsers utils scripts pycdc.py`），
仓库 `core/` 未改动。判据 = `scripts/pyc_verify.py single`（同一把尺）。读数一律 `python -X utf8`，未设 PYTHONIOENCODING。

## 0. 镜像封表校验

| 文件 | sha256[:16] | 说明 |
|---|---|---|
| `core/cfg/region_analyzer.py`（仓库） | `e926a54f17753b33` | 含已落地的 B133；测量前后各读一次 |
| `core/cfg/region_ast_generator.py`（仓库） | `e9a8f65f6451bcc8` | 本票未触碰 |
| 镜像与仓库 `diff -rq`（排除 `__pycache__`） | 仅 `region_analyzer.py` 不同 + 镜像自有 `scr/`、两份实验产物 | 无夹带第三处改动 |

镜像可信度：把**仓库字节**装入镜像跑 `trade_info_utils` → `38/41`、产物 `61281` 字节，与仓库封存产物**逐字节相同** ⇒ 镜像读数可与封表数直接对照。

## 1. 两个标本的结构读数（决定判别式的事实）

头块 `H`，`J` = H 尾跳转的目标块，`F` = H 的另一后继，`K` = F 的非 J 后继。

| 标本 | H | H 尾 | `cond_start` | J | F | K |
|---|---|---|---|---|---|---|
| **需要放宽**：`IQEngine/core/bar :: BarData._history_bars` | @34（块内前两条为已完成语句 `engine=Engine.instance()`、`dt=engine.calendar_dt`） | `POP_JUMP_FORWARD_IF_FALSE→@140` | 120 | @140 **尾=POP_JUMP_FORWARD_IF_FALSE(304)** ⇒ J 自己做判断 | @128 尾=POP_JUMP_FORWARD_IF_TRUE(206) | @206 尾=STORE_FAST(`dt`) ⇒ then 体是语句 |
| **必须排除**：`fly/data/quotation :: <module>._is_same_type_date` | @14（块内前两条为 `a=day1.isocalendar()`、`b=day2.isocalendar()`） | `POP_JUMP_FORWARD_IF_FALSE→@170` | 122（若放宽） | @170 = `[LOAD_CONST, RETURN_VALUE]` ⇒ **J 不判断** | @130 尾=POP_JUMP_IF_FALSE(170) | @166 = `[LOAD_CONST True, RETURN_VALUE]` |

⇒ 「`return A and B`」这类**值上下文**的假边落在常量返回块上；`if` 条件链的假边落在**另一个测试块**上。

## 2. 三臂实测

### 2.1 无判据全量回溯（blanket，我上一轮已登记：commit `47f4b21b`）
`bar 84/85→85/85`、`quotation 153/153→152/153`（新红 `_is_same_type_date`：orig 99 指令 / prod **71** 指令，
产物把 `return False` 发在该块自身两条语句**之前**并丢掉尾部 `return False`）。方向对、判据过宽。

### 2.2 加入 §1 判据（J 的尾指令属条件跳转族才回溯）——候选字节 `360fae76ce699366`（无探针）

| 文件 | HEAD 读数 | 候选读数 | 产物字节 |
|---|---|---|---|
| `IQEngine/core/bar.pyc` | 84/85 | **85/85** | DIFF（整文件翻正） |
| `fly/data/quotation.pyc` | 153/153 | 153/153 | **SAME_as_HEAD** |
| `IQCommon/util/trade_info_utils.pyc` | 38/41 | 38/41 | SAME_as_HEAD |
| `IQEngine/core/strategy/strategy_universe.pyc` | 10/11 | 10/11 | SAME_as_HEAD |
| `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc` | 26/27 | 26/27 | SAME_as_HEAD |
| `IQCommon/api/klinedata.pyc` | 62/64 | 62/64 | SAME_as_HEAD |
| `IQCommon/strategy/wizard_quant_api.pyc` | 55/58 | 55/58 | SAME_as_HEAD |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | 118/128 | 118/128 | SAME_as_HEAD |
| `fly/data/quote.pyc` | 86/92 | **85/92** | DIFF ⇒ 新红 `<module>.Quote.load_bars_from_hundsun` |

新红逐条读回（HEAD 61 行 → 候选 48 行）：候选把 `if os.path.exists(DumploadDailyFile) and typet == 6:` 的**整个嵌套体压成 `pass`**，
并把体内 `source_start/source_end/diffset/len(diffset)==0` 一串语句搬到该 if **之外**，同时 `if retpanel.empty:` 体也变 `pass`。
该头块的 J 同样「自己做判断」（`typet == 6` 测试块），所以 **J-判据对它成立 ⇒ 被放宽 ⇒ 误吸收**。

**结论（写死）**：`J 是否判断` 是 §1 反向排除的必要条件，但**不是**「本头块可启动链」的充分条件；
两标本的差别必须再补一条结构事实——候选缺口是：bar 的 `K`（then 臂）是**同一区域内的语句块**、
而 `load_bars_from_hundsun` 的 then 臂是**含函数内 import 与嵌套 if 的多语句复合体**，
即「放宽后 BoolOpRegion 的 then 臂必须是一条语句」。本票**不落地**（净 +1 单元 / −1 单元，整文件数为 0），
候选字节留在 `D:/Temp/r141/cand_gated.py` 供下一票继续贴条件；三条已证伪臂（blanket / J-gate / J-gate+K）中前两条形成本票读数。

## 3. 方法学发现（对本仓所有探针生效）

**在分析器内部读 `start_block.successors` / `get_block_by_offset` 的探针本身会改变产物**。
隔离臂：把判据改成 `and False`（回溯永不发生）、**保留探针**跑 `trade_info_utils` →
产物 `60591` 字节、`37/41`（新红 `get_trade_status`），而仓库字节臂是 `61281` 字节、`38/41`。
`[P3]` 回溯计数 = 0，日志无 Traceback ⇒ 不是异常回退，是 CFG 属性读取的状态副作用。
我一度把这读成「J-gate 造成 tiu 回归」，是错的；拆臂后才是真因。
要求：此后分析器内探针只读**已在作用域内的对象**（指令列表、offset、已算出的 `_r54_*`），
或改在独立进程用新建 CFG 读结构；任何用探针得到的单元读数，必须再做一次「判据置死、探针保留」臂与「纯净候选」臂双向隔离。
