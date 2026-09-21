# Round 17-A 修复与验证记录（fixes）

## 一、目标与根因（实测，非推测）

目标真源：`site-packages/IQData/manager/plugin_manager.pyc` 与同源孪生
`site-packages/IQEngine/core/plugin_manager.pyc` 的 `<module>.PluginManager.set_engine`
（补丁前项目工具报 partial 9/10、8/9；逐函数比对给出的签名是 JUMP 终点漂移：
`#60 JUMP 终点 orig=('utils'/'time', LOAD_GLOBAL) decomp=('system_log', LOAD_GLOBAL)`）。

根因（`core/cfg/region_analyzer.py`，方法 `_build_elif_region` `:17831`）：D2 守卫在把
「外层 else 臂开头的嵌套 if」当作 elif 链的一级之前有五条件判断，其中第④条件
`self._find_enclosing_loop(first_else) is None`（外层 else 不在循环内才干预）把**循环归属**
当成了结构差异。真 elif 链的嵌套汇聚点必然等于外层汇聚点，已被③排除；④只对
「else 内嵌套 if + 尾随语句」的循环形状漏检，漏检后尾随语句被 `_elif_struct_blocks` 剔出并
外提，then 臂 `JUMP_FORWARD` 落点随之外移。详见 `arm-design.md` §1。

附带翻正：`site-packages/fly/common/user_error.pyc`（2/4→4/4，两函数各少/多发射 8 条）。

## 二、方案与区域归约算法的对应

- 原则「每块唯一归属」：判据④删除后，循环内的 else 臂与循环外走同一条归约路径——
  要么整体识别为 elif 链（③不成立），要么 IF_THEN_ELSE + 嵌套子区域 + 尾随兄弟节点（③成立），
  每块仍只属于一个区域。
- 原则「嵌套区域即抽象节点」：嵌套 if 作为子 `IfRegion` 出现在外层 else 体，父区域 else 列表
  引用其入口块，未改成引用子区域全部块。
- 单向数据流：本轮只删一条判据，**不新增回溯修正**，生成层 `region_ast_generator.py` 零改动。
- 禁止跨区域跨层次启发式：撤销一条按「是否在循环内」放行的层次豁免，属于**移除**启发式而非
  增加；同层同结构现在得到同一结论。
- 反编译逻辑已写入识别方法注释：D2 注释块 `:18731-18749`（识别条件①②③④ → 归约方式 →
  外提机制 → 真源签名 → 实测代价），docstring 摘要 `:17863-17865`。

## 三、补丁与落地

`D:/Temp/r17/r17a_patch.py`（3 hunk 纯 assert 字节级补丁，锚点唯一性 / 无 BOM / 纯 CRLF /
`ast.parse` / 拒绝二次应用）：

| 项 | 值 |
|---|---|
| 唯一代码改动 | H1：D2 守卫删除 `and self._find_enclosing_loop(first_else) is None`（`:18746-18748` → `:18754-18756`） |
| 文档改动 | H2 判据注释块（+11/−2 行）、H3 docstring 判据摘要（⑤→④ 重编号） |
| `region_analyzer.py` | `110bf739bde62846 → 255d53d3c8707a07`，26643 → 26651 行（+9/−1），26650 CRLF / 0 裸 LF / 无 BOM |
| `region_ast_generator.py` | 未触碰（本轮零改动） |

落地前先在副本上量：`D:/Temp/r17/h.py` 就地方法替换（`inspect.getsource` → 行级改写 →
`exec(compile(src, …), dict(RA.__dict__))` → `setattr`），仓库零写入。
**踩坑记录**：以 `importlib` 模块级替换播种 `core.cfg.region_analyzer` 会使产物整体退化
（限定名塌缩）；改为就地替换后正常；即便喂入逐字节相同的 HEAD 副本，模块级替换也会把
`round16_sink` 的差异数从 8 扰动到 13 —— 类身份/`isinstance` 被打断，故本轮所有 A/B 一律走就地替换。

## 四、落地前验证（副本测量，仓库零写入）

| 试验 | 结果 |
|---|---|
| `round16_sink` 电池（15 项）A/B | 补丁前 8 项不一致 / 补丁后 0 项，5 负对照两臂均一致 |
| 406 pyc 逐函数比对 A/B | 变好 7 文件 / 9 函数，变坏 0，签名变化 1（`strategy.pyc` 缺陷数不变） |
| `quotation.pyc` A/B | 两臂同名同数 3 个缺陷函数，中性 |

## 五、门禁（mandate 顺序：单点 → quotation → 批量）

基线 = 落地前磁盘产物（R16 已验证终态）的逐函数比对全量输出 `D:/Temp/r17/r17_base_strict_all.txt`。

1. **单点** `_r13_gate.py --targets rounds/round17/targets_1fix.txt` →
   `IQData/manager/plugin_manager 9/10→10/10`、`IQEngine/core/plugin_manager 8/9→9/9`、
   `fly/common/user_error 2/4→4/4`，**FLIPPED-CLEAN=3**，无回滚。
2. **quotation.pyc 单验** → `WORSENED(rolled back)`（148/150 → 再生成 147/150，闸门自动回滚，
   磁盘产物保持 148/150）。与 Round 16 同判：磁盘产物来自 Round 9 的核（`git log --
   site-packages/fly/data/quotationOK.py` ⇒ `393d9ff0`），当前核再生成更差 ⇒ SubTask 13.3
   的产物/核漂移，不由本轮引入（§四 A/B 已证本轮改动对 quotation 缺陷集合中性）。
   另记：项目工具 `single` 对 quotation 报 `FAILED: timeout after 60s`（其内部反编译超时），
   该文件只能靠逐函数比对与 `batch` 复验。
3. **406 全量批量回归**（`gate_all_1.json`，单趟 147s）：

   | verdict | R17 | R16（同一 406 列表） |
   |---|---|---|
   | CLEAN | 333 | 330 |
   | UNCHANGED | 57 | 64 |
   | IMPROVED | 4 | 0 |
   | WORSENED(rolled back) | 9 | 9 |
   | REGRESSION(rolled back) | 2 | 2 |
   | NO-OKPY | 1 | 1 |

   异常集合**逐个文件与 Round 16 完全一致**（9 WORSENED + 2 REGRESSION，另 1 NO-OKPY 是
   `ptradeAccountOK_marker_test.pyc` 标记文件）；R17 只多出 4 个 IMPROVED（本轮收益），
   无任何文件由正常转异常。另有 5 个产物随核重写但比对结果不变（闸门不回滚）：
   `plugin_fly_data/strategy`、`plugin_system_event_source/realtime_event_source`、
   `plugin_system_matcher/matcher`、`plugin_system_trade/function`、`fly/data/quote`。

## 六、成功率复验（只用项目自带工具的数字对外汇报）

对外口径唯一：`scripts/pyc_batch_verify.py`。

| 命令 | 结果 |
|---|---|
| `single site-packages/IQData/manager/plugin_manager.pyc` | `decompile_status: ok`，`10/10`，`match_rate 100.00%` |
| `single site-packages/IQEngine/core/plugin_manager.pyc` | `ok`，`9/9`，`100.00%` |
| `single site-packages/fly/common/user_error.pyc` | `ok`，`4/4`，`100.00%` |
| `single site-packages/fly/data/quotation.pyc` | `FAILED: timeout after 60s`（工具内部反编译超时） |
| `stats --index pyc_index.json`（索引累计值） | total 402 / verified 402 / **ok 356** / partial 46 / failed 0 / 累计匹配率 **97.88%** |
| 对 R16 同一份产物清单重跑工具内的 `bytecode_diff`（`D:/Temp/r16_arm/official_all.py`，不改判定） | 本轮末行 `SUMMARY ok=357 partial=48 noart=1 funcs=5705/5838`（`D:/Temp/r17/r17_after_official.txt`）；R16 末行 `SUMMARY ok=356 partial=49 noart=1 funcs=5700/5838`（`D:/Temp/r16_arm/official_all_R16.txt`） |

口径固定两句：记账主口径 = `pyc_index.json` 的 402 个 pyc，本轮条目数与每条 `function_count`
零变化（`git diff --numstat` = 30/30，全落在本轮重测的 7 个条目）；`stats` 的 97.88% 与
上一行的 5838 分别是索引历史值、R16 脚本自带清单（406 = 402 + 4 个 `*OK.py` 二次编译的
非语料 pyc）的产物内函数数，均不写作本轮成果。净收益 = 3 个 pyc 转 100% + 4 个 pyc
匹配函数上升（16→17、100→103，孪生两条 8→8 仅减缺陷）+ 0 个退步。

## 七、复现电池与标注回填（落地后全部 `--strict` 退出码 0）

| 电池 | 落地后实测 | UNEXPECTED / ERROR |
|---|---|---|
| `round17_arm`（本轮新增 26 项） | 不一致=1 一致=25 | 0 / 0 |
| `round16_sink`（回填后） | 不一致=0 一致=15 | 0 / 0 |
| `round16_arm` | 不一致=1 一致=15 | 0 / 0 |
| `round15_arm` | 不一致=2 一致=10 | 0 / 0 |
| `round14_join` | 不一致=1 一致=15 | 0 / 0 |
| `round14` | 不一致=0 一致=17 | 0 / 0 |
| `round13` | 不一致=14 一致=11 | 0 / 0 |

`round17_arm` 的 26 项里 18 项是 SENTINEL（补丁前必不一致、补丁后必须一致），6 项负对照
两臂皆一致，`r17a_25_terminal_inner_merge` **两臂都不一致**（判据⑤命中的终态汇聚残留，
与④无关，已记入 §九），`r17a_27_merge_signature_equal` 为 UNCONFIRMED（展平确实发生，但两个
落点块首指令逐字相同，比对脚本看不见）。

回填：`test_repros/round16_sink/run_all.py` 的 8 个 anchor `MISMATCH → SENTINEL`，并在 docstring
记录落地核指纹（脚本 `D:/Temp/r17/sink_relabel.py`，纯 LF 字节级，`6174e655eecdfd91 → 2b32157f595a93ac`）。

## 八、`pyc_index.json` 纠正

`e7c3724b7b007f01 → bf67f1cba34d3a86`，4553 CRLF 行不变，30 行改动全部落在 7 个条目内
（脚本 `D:/Temp/r17/r17_index_fix.py`，先 `--dry` 校验；字段值全部取自项目工具 `bytecode_diff`
的实测，不手工填数）：

| 条目 | 变更 |
|---|---|
| `IQData/manager/plugin_manager.pyc` | `partial 0.9 / mismatch 1 / matched 9` → `ok 1.0 matched 10`，round 17 |
| `IQEngine/core/plugin_manager.pyc` | `partial 0.8889 / mismatch 1 / matched 8` → `ok 1.0 matched 9`，round 17 |
| `fly/common/user_error.pyc` | `partial 0.5 / mismatch 1 / matched 2` → `ok 1.0 matched 4`，round 17 |
| `IQCommon/logger/handlers.pyc` | `matched 16 → 17`，rate 0.8889→0.9444，round 17（旧值 rate 与 mismatch_count 自相矛盾，一并纠正） |
| `IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc` | `matched 100 → 103`，mismatch_count 27→16（按 schema `total-matched` 重算），round 17 |
| `IQData/{plugins/plugin_system_fly_basicdata,utils}/calexrights_func.pyc` | 工具实测本就 8/8，保持 `ok`，仅记 round 17 + note（逐函数复核显示 6/8→7/8，即松判据看不见的那 1 个 JUMP 终点漂移仍在） |

## 九、残留

1. quotation 等 11 项产物/核漂移（SubTask 13.3）：磁盘产物来自 Round 9，当前核再生成更差，
   闸门每轮 WORSENED 回滚；根因在生成层，需按轮次二分定位退化提交（线索见 `arm-design.md` §5）。
2. `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc`：缺陷数 2→2，`tick_worker_thread`
   由「序列错位」变「长度不等」（268 vs 247）。
3. `r17a_25_terminal_inner_merge`：判据⑤（终态汇聚）导致的循环内 `return` 形状残留，两臂皆不一致。
4. `calexrights_func`（孪生对）各残留 1 个 JUMP 终点漂移；`handlers` 残留 2；`trade_live_broker` 残留 26。
5. `r16a_05`（循环入口过发射 31→39）、`r15a_08`（`guard_clause_prefix_end`）、`r15a_09`
   （语句序列过发射 +9）、`round13` 14 项 anchor、`round14_join` 1 项、T1/T2 then 臂收集顺序。
6. SubTask 13.4、Task 5 遗留（`decrypt_database_url` +29、`cgroup` +2/+1、`replace_utils` 差 2）。
