# Round 14 目标清单（由 Round 13 收口实测基线推导）

基线（commit `f89b85f2`，见 `baseline_strict_after_r13.txt`）：
文件级 **325 / 402** 全一致，**77** 有真缺陷；函数级 **5977 / 6204**。
官方口径 351 ok（两把尺子，数字不得互减）。

「只差 1 个函数」的文件共 **30 个** —— 修对一类即可翻正，性价比最高。

## 按缺陷签名分组（30 个候选）

### A. `target_diff`（指令数已相等，只有一条跳转落点错）——9 个
| 文件 | 缺陷限定名 | 备注 |
|---|---|---|
| `IQCommon/profiler_func.pyc` | `<module>` | `#82 POP_JUMP_IF_FALSE 终点 orig=('PY35', LOAD_NAME) decomp=('0', LOAD_CONST)` |
| `IQData/utils/profiler_func.pyc` | `<module>` | **与上一行同源的同一份源码副本** ⇒ 一处修复翻正 2 个 pyc |
| `IQData/manager/plugin_manager.pyc` | `<module>.PluginManager.set_engine` | 与下行同源副本 |
| `IQEngine/core/plugin_manager.pyc` | `<module>.PluginManager.set_engine` | ⇒ 一处修复翻正 2 个 pyc |
| `IQCommon/data/api_data.pyc` | `<module>.check_limit_common` | |
| `IQCommon/data/local_finance.pyc` | `<module>.get_local_financial_factors` | |
| `IQEngine/core/strategy/strategy_universe.pyc` | `<module>.StrategyUniverse._on_clear_de_listed` | |
| `fly/common/common.pyc` | `<module>.api_get_from_zeromq` | |
| `fly/common/market_time.pyc` | `<module>.MarketTime.is_open` | |

判据：`seq_len` 已相等 ⇒ 不是语句丢失/重复，而是**合流点（merge）落点**判错，
与 Round 13 的 R13-C/R13-N 同族（链 merge 计算退化为 `None` 后按启发式指派）。

#### A-1 已完成的形状级定位：`profiler_func`（dis 实测，非推测）
原始模块码语义指令 #74–#82（噪声已按尺子剔除，`len orig = len decomp = 136`）：
```
#74 LOAD_NAME  sys        #75 LOAD_ATTR version_info   #76 LOAD_CONST 1
#77 BINARY_SUBSCR         #78 LOAD_CONST 5             #79 COMPARE_OP >=
#80 STORE_NAME 'PY35'     #81 LOAD_NAME  'PY35'
#82 POP_JUMP_IF_FALSE 280     <-- orig 落点 280 = LOAD_NAME 'PY35'（即 `if not PY35:`）
#83 LOAD_CONST 0          #85 IMPORT_NAME inspect      #87 IMPORT_NAME line_profiler_py35
```
反编译产物同一条为 `POP_JUMP_IF_FALSE 218`，218 处是 `LOAD_CONST 0`（`try:` 内
`import line_profiler_py35` 的 IMPORT_NAME 前置常量）。对应产物 `profiler_funcOK.py:18-28`：
```python
if PY35:
    import inspect
try:                      # <-- 本应在 if PY35: 体内，被踢到体外
    import line_profiler_py35
```
真实源码形状：
```python
PY35 = sys.version_info[1] >= 5
if PY35:
    import inspect
    try:
        import line_profiler_py35
    except ImportError:
        PY35 = False; line_profiler_py35 = None
    else:
        def is_coroutine(f): return inspect.iscoroutinefunction(f)
        wrap_coroutine = line_profiler_py35.wrap_coroutine
if not PY35:
    ...
```
⇒ 症状：**then 臂体含 try/except/else 时，臂体在第一条语句后被截断**，
链的 merge/出口集判错，`else` 落点提前。`IQData/utils/profiler_func.pyc`
是同一份源码的副本 ⇒ 一处修复同时翻正 2 个 pyc。

#### A-2 静态定位（不依赖反编译，纯 dis + 产物对照）：`PluginManager.set_engine` ×2
`IQEngine/core/plugin_manager.pyc` 与 `IQData/manager/plugin_manager.pyc` 各差 1 个函数，
**语义指令条数完全相等**（194 = 194 / 184 = 184），只有第 #60 条无条件跳转的落点不同：

```
#53 POP_JUMP_FORWARD_IF_FALSE 360      （两条产物一致）
#54..#59  plugin_module = {} ; plugin = user_plugin_config.load_plugin()
#60 JUMP_FORWARD  orig -> off832 = LOAD_GLOBAL 'time'   （IQData: off790 = LOAD_GLOBAL 'utils'）
          decomp -> off622 = LOAD_GLOBAL 'system_log'   （IQData: off580）
```
产物 `plugin_managerOK.py:33-51` 形状：
```python
if hasattr(user_plugin_config, 'load_plugin') and callable(user_plugin_config.load_plugin):
    plugin_module = {}
    plugin = user_plugin_config.load_plugin()
elif hasattr(user_plugin_config, 'setup') and callable(user_plugin_config.setup):
    ...
else:
    lib_name = plugin_name
system_log.debug(...)          # <-- 真源码里这些属于 else 臂
plugin_module = utils.import_plugin(lib_name)
if plugin_module is None:
    del (self._plugin_list[idx]); return None
plugin = plugin_module.load_plugin()
time.sleep(0.01)               # <-- orig 臂尾 JUMP 的真正落点（链后共享尾）
```
⇒ 真实形状是 **if/elif 链带 `else` 臂**，`else` 臂尾无条件跳到链后共享尾；
产物把 `else` 臂**降级成链后的顺序语句**（指令一条不少，所以 `seq_len` 相等），
于是前两条臂的出口跳转落在 `system_log.debug` 上而不是 `time.sleep` 上。
判据仍然落在 merge/出口集：臂尾 `JUMP_FORWARD` 的目标（off832/off790）就是链的 merge，
它是**链后共享尾的入口**，而 `else` 臂入口（off622/off580）只是臂的落空后继。
把 merge 判成 else 臂入口 ⇒ else 臂被当成链外顺序代码。
与 `test_repros/round13/ANALYSIS.md` 的 **R13-N** 是同一症状（当年只留了真实文件证据、
未做成复现），且**与 A-1 是两个独立判据**（A-1 是 BoolOp merge 块被整体跳过）。
一处修复 ⇒ `IQEngine/core/plugin_manager.pyc` 9/10→10/10、
`IQData/manager/plugin_manager.pyc` 8/9→9/9，**再翻正 2 个 pyc**。
最小复现待写（须在 A-1 落地后实测，避免基线漂移）：
`if A: p=1 / elif B: p=2 / elif C: q=3 / else: log(); p=4` 后接共享尾 `after()`，
要求前两臂尾部的 `JUMP` 落点必须是 `after()`。

### B. `seq_len` 负差（语句被吞）——11 个
`can_resume_strategy`(-32)、`DefaultMatcher.match`(-26)、`events`(-24)、
`SimulationBroker.save`(-7)、`live.DefaultLiveBroker.save`(-4)、
`FileLock.acquire`(-5)、`_on_before_trading_start_trading_thread`(-4)、
`StockPosition.make_trade`(-4)、`save_testds_to_json`(-4)、
`trading_dates_reload`(-2)、`perform_rollover`(-2)。

### C. `seq_len` 正差（语句被多发射）——8 个
`DataProxy.get_bar`(+16)、`getVaildAccount`(+16)、`check_before_trading`(+11)、
`memory_handler`(+8)、`send_email`(+2)、`get_price`(+2)、`tls_client`(+2)、
`remove_lock_files`(+1)、`PtradeBroker.create_portfolio`(+1)。
正差 = 同一区域被发射两次，属 Round 13 已回退的 A2 判据同族（原则 2 归属层缺信息）。

### D. `seq_diff`（长度相等、内容错位）——1 个
`IQEngine/data/asset_mixin.pyc <module>.AssetMixin.get_assets.<listcomp>`。

## 本轮已排定的修法（顺序即门禁顺序）
1. **R14-D**（B 类中的 dict 双推导式塌陷）：`broker` / `live` 各 -7 / -4，
   一处修复翻正 **2 个 pyc**，复现已在 `test_repros/round13/r13_05` 钉住。
2. **A2 正解**（C 类归属层判据）：见 tasks.md SubTask 13.1 / 13.2。
3. **R13-C/G 合流点**（A + B 大头）：`_collect_branch_blocks` 目前在
   `merge=None` 时做「无界收集 + 事后反向剪枝」（`region_analyzer.py:25516-25600`，
   内含 `if False and ...` 的死代码与三层豁免），这正是被禁止的跨区域启发式；
   正解是把 merge 算出来（出口集 / 结构合流），让无界收集不再发生。
