# Round 17 结果（OUTCOME）

一条根因线（R17-A），按门禁顺序完成：单点修到完全 OK → quotation.pyc 单验 → 全量批量回归 →
标注回填 → 索引纠正 → 提交 push。设计稿 `arm-design.md`，验证记录 `fixes.md`。

## 一、解决了什么

`IQData/manager/plugin_manager.pyc` 与同源孪生 `IQEngine/core/plugin_manager.pyc` 的
`PluginManager.set_engine`，以及 `fly/common/user_error.pyc` 的两个函数 ——
**循环内「else 臂嵌套 if + 尾随语句」不再被展平成 elif 链**，尾随语句回到 else 体内，
then 臂 `JUMP_FORWARD` 落点回到外层合并点。

单点门禁 **FLIPPED-CLEAN=3** —— 三个 pyc 由 partial 转为项目工具
`pyc_batch_verify.py single` 报 `decompile_status: ok` / `match_rate 100.00%`：
`IQData/manager/plugin_manager.pyc`、`IQEngine/core/plugin_manager.pyc`、`fly/common/user_error.pyc`。

另有 4 个文件的缺陷函数减少、无一文件增加：`IQCommon/logger/handlers`、
`IQData/utils/calexrights_func` 与 `IQData/plugins/plugin_system_fly_basicdata/calexrights_func`
（同源孪生）、`IQEngine/plugins/plugin_system_trade/trade_live_broker`。

修法是最小删除：`core/cfg/region_analyzer.py` `_build_elif_region` 的 D2 守卫去掉第④判据
（`self._find_enclosing_loop(first_else) is None`），+9/−1 行（代码只删这一行条件，其余是判据
注释与 docstring 的同步改写）。生成层 `region_ast_generator.py` 本轮零改动。
该判据是按「外层是否在循环内」放行的跨层次豁免——真 elif 链已被判据③
（`inner_merge is not merge_`）排除，⑤继续排除终态共享退出汇聚，删掉它不新增任何规则。

## 二、门禁与归因

1. 单点 → 3 项 FLIPPED-CLEAN，零回滚。
2. quotation.pyc → `WORSENED(rolled back)`（当前核再生成 147/150 < 磁盘产物 148/150，自动回滚，
   产物未变差）。与 Round 16 同判；A/B 显示本轮改动对 quotation 缺陷集合逐名相同。
   磁盘产物停在 Round 9（`393d9ff0`），即当前核比产物旧的那次改动才是病根（SubTask 13.3）。
   另记：`single` 跑 quotation 会 `FAILED: timeout after 60s`（工具内部反编译超时）。
3. 全量产物门 → CLEAN 333 / UNCHANGED 57 / IMPROVED 4 / WORSENED 9 / REGRESSION 2 / NO-OKPY 1；
   异常集合与 Round 16 **逐个文件相同**（11+1），本轮只多出 4 个 IMPROVED ⇒ 零新增回退。
4. 七套复现电池 `--strict` 全部退出码 0，UNEXPECTED=0、ERROR=0；本轮新增 `round17_arm`
   26 项（18 SENTINEL / 6 负对照 / 1 两臂皆不一致的判据⑤残留 / 1 UNCONFIRMED）。
5. 产物清单级 A/B（就地方法替换）：变好 7 个文件，变坏 0，签名变化 1。

## 三、代价与残留

1. SubTask 13.3 产物/核漂移 11 项（含 quotation）：需按轮次二分定位「当前核比 Round 9 差」的
   提交；在此之前闸门每轮都会 WORSENED 回滚一次。
2. `strategy.pyc` 缺陷数 2→2，`tick_worker_thread` 签名由序列错位变长度不等（268 vs 247）。
3. `r17a_25_terminal_inner_merge`：判据⑤（终态汇聚）造成的循环内 `return` 形状残留。
4. `calexrights_func` 孪生对各残留 1 个 JUMP 终点漂移；`handlers` 残留 2；`trade_live_broker` 残留 26。
5. `r16a_05`、`r15a_08`、`r15a_09`、`round13` 14 项 anchor、`round14_join` 1 项、T1/T2 then 臂
   收集顺序；SubTask 13.4、Task 5 遗留（`decrypt_database_url` +29、`cgroup` +2/+1、
   `replace_utils` 差 2）。
6. 工具链事实（已写进 `fixes.md` §三）：`core.cfg.region_analyzer` 不可用 importlib 模块级替换
   播种（类身份断裂使产物塌缩，连逐字节相同副本都会扰动测量），只能就地 `exec + setattr` 换方法。

## 五、提交物

核：`core/cfg/region_analyzer.py`（`region_ast_generator.py` 未改）。
产物：`site-packages/{IQData/manager,IQEngine/core}/plugin_managerOK.py`、
`site-packages/fly/common/user_errorOK.py`、`site-packages/IQCommon/logger/handlersOK.py`、
`site-packages/IQData/utils/calexrights_funcOK.py`、
`site-packages/IQData/plugins/plugin_system_fly_basicdata/calexrights_funcOK.py`、
`site-packages/IQEngine/plugins/plugin_system_trade/trade_live_brokerOK.py`，
以及 5 个「比对结果不变、随核重写」的产物（`plugin_fly_data/strategy`、
`plugin_system_event_source/realtime_event_source`、`plugin_system_matcher/matcher`、
`plugin_system_trade/function`、`fly/data/quote`）。
记录：`pyc_index.json`、`rounds/round17/{arm-design.md,fixes.md,OUTCOME.md,targets_1fix.txt,targets_all.txt}`、
`test_repros/round17_arm/`（26 复现 + `run_all.py` + `ANALYSIS.md`）、
`test_repros/round16_sink/run_all.py`（SENTINEL 回填）、`tasks.md`（Task 17）。
