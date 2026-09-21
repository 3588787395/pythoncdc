# Round 17-A 设计：`_build_elif_region` D2 守卫的第④判据（循环豁免）是漏检源

## 0. 目标与受害真源

本轮主目标 `site-packages/IQData/manager/plugin_manager.pyc`（项目工具 `pyc_batch_verify.py
single` 复验前为 partial 9/10）与其同源孪生 `site-packages/IQEngine/core/plugin_manager.pyc`
（partial 8/9），缺陷函数都是 `<module>.PluginManager.set_engine`。逐函数比对脚本
（仓库既有 `_r10_strict_check.py`，闸门内部判据）给出的签名：

```
IQData/manager    #60 JUMP 终点 orig=('utils', LOAD_GLOBAL)      decomp=('system_log', LOAD_GLOBAL)
IQEngine/core     #60 JUMP 终点 orig=('time',  LOAD_GLOBAL)      decomp=('system_log', LOAD_GLOBAL)
```

即 then 臂末尾的 `JUMP_FORWARD` 落点从**外层合并点**（`plugin_config = utils.DictObject(...)`
首指令）漂移到**被外提的尾随语句入口**（`system_log.debug(...)`）。

真源结构（`set_engine`，位于 `for` 循环体内）：

```python
for idx, (plugin_name, user_plugin_config) in enumerate(self._plugin_list):
    if hasattr(..., 'load') and callable(...):      # then 臂：plugin_module = {}; plugin = ...load()
        ...
    elif hasattr(..., 'install') and callable(...):
        ...
    else:                                           # ← 外层 else，在循环内
        if hasattr(user_plugin_config, 'lib'):      # ← else 臂开头的嵌套 if/elif/else
            lib_name = user_plugin_config.lib
        elif plugin_name.startswith('plugin_system'):
            lib_name = 'IQData.plugins.{}'.format(plugin_name)
        else:
            lib_name = plugin_name
        system_log.debug(...)                       # ← 尾随语句（属于外层 else 体）
        plugin_module = utils.import_plugin(lib_name)
        if plugin_module is None: ...
        plugin = plugin_module.load_plugin()
    plugin_config = utils.DictObject(...)           # ← 外层 if/elif/else 的合并点
```

## 1. 归因：D2 守卫判据④把「循环内」当成了结构差异

识别链在 `core/cfg/region_analyzer.py`：`_identify_conditional_regions → _build_elif_region`
（`:17831`）。该方法在把「外层 else 臂开头的嵌套 if」当作 **elif 链的一级** 之前，有一道 D2
守卫（补丁前 `:18746-18748`），命中即 `return None`——含义是「不要建 elif 链，改建
IF_THEN_ELSE，让嵌套 if 作为 else 体的子区域、尾随语句作为 else 体内的兄弟子节点」。
判据五条（补丁前）：

① `inner_merge is not None`（NCPD 求得的内层汇聚点）；② `merge_ is not None`（外层汇聚点）；
③ `inner_merge is not merge_`（嵌套分支汇聚于外层合并点之前 ⇒ 存在尾随语句）；
④ **`self._find_enclosing_loop(first_else) is None`（外层 else 不在循环内才干预）**；
⑤ `inner_merge` 非终态块（RETURN/RAISE/RERAISE，终态汇聚属共享退出而非尾随）。

缺陷出在④：`first_else` 落在循环内时守卫被跳过，于是「else 内嵌套 if + 尾随语句」被当作
elif 链构建。链式构建后，尾随语句被 `_elif_struct_blocks` 过滤剔出 else 体并外提为整条
if/elif/else 之后的兄弟语句——语义被改写（then 臂也会执行尾随），同时 then 臂末尾
`JUMP_FORWARD` 的落点从外层合并点改为尾随语句入口，即 §0 的 JUMP 终点漂移。

④在区域归约的意义上不是**结构**判据：`if/elif/else` 链与「else 内嵌套 if + 尾随」的差别只在于
嵌套块的汇聚点是否等于外层汇聚点（判据③）。真正的 elif 链（外层 else 本身就是一个新的
`POP_JUMP_IF_*` 条件块）其两路必然汇聚于外层 merge，`inner_merge == merge_`，已被③排除；
把它「因为外面有循环」再豁免一次，等于对同一结构给出两套互斥归约结论，违反
**算法驱动 / 一次正确**（同层次同结构必须同结论）。原注释给出的豁免理由是「循环内
break/continue 经 R24-A 修正后 `inner_merge` 可能合法地不等于 `merge_`」——该风险由⑤
（终态汇聚）与 §3 的负对照实测共同覆盖，不需要按「是否在循环内」整体放行。

## 2. 修法（唯一改动点，符合「禁止跨区域跨层次的启发式规则」）

删④，保留①②③⑤：

```python
if (inner_merge is not None and merge_ is not None
        and inner_merge is not merge_):
```

改后 else 臂的归属仍由既有收集器完成（`_collect_branch_blocks` + `_elif_struct_blocks` +
原则 2「每块唯一归属」/ 原则 3「嵌套即抽象节点」），不新增跨层回溯修正、不改生成层。
同步改写两处文档：D2 判据注释块（`:18731-18749`，含识别条件、外提机制、真源签名、实测代价）
与 `_build_elif_region` docstring 的判据摘要（`:17863-17865`，⑤→④ 重编号）；补丁后守卫本体
落在 `:18754-18756`。

补丁：`D:/Temp/r17/r17a_patch.py`（3 hunk 纯 assert 字节级，锚点唯一性 / 无 BOM / 纯 CRLF /
`ast.parse` / 拒绝二次应用）。`region_analyzer.py`
`110bf739bde62846 → 255d53d3c8707a07`，26643 → 26651 行（**+9/−1**，其中 −1/+1 为代码，
其余为注释）。

## 3. 复现与 A/B（`test_repros/round16_sink`，15 项）

首轮（补丁前核）8 个 anchor 全部以 JUMP 终点漂移复现，5 个负对照一致；关键分界对照：
`r16s_08_neg_no_enclosing_loop` 与 `r16s_04_anchor_minimal_two_arm_loop` 只差「是否在循环内」，
前者走 VETO(d2)、后者走 FLATTEN-BY-LOOP-EXEMPTION(④)。把④就地移除后重跑：**MISMATCH=0 /
MATCH=15**，8 个 anchor 全部翻正，5 个负对照无一被误伤。
A/B 手段：`D:/Temp/r17/h.py`（就地方法替换：`inspect.getsource` → 行级改写 →
`exec(compile(...), dict(RA.__dict__))` → `setattr`）。注意：**模块级替换 `core.cfg.region_analyzer`
在本项目不可用**——即使喂入逐字节相同的副本，逐函数比对也会改变结果
（实测同一副本控制组 MISMATCH 8→13），因为 `isinstance`/类身份被打断；本轮所有 A/B 均走就地替换。

## 4. 全量产物 A/B（`D:/Temp/r17/out/{base_1,D2all_1,D2all_2}.jsonl`）

| 结果 | 明细 |
|---|---|
| 变好 | 7 个文件的缺陷函数消失，变坏 0 |
| 完全转 100% | `IQData/manager/plugin_manager`、`IQEngine/core/plugin_manager`、`fly/common/user_error` |
| 部分改善（缺陷函数减少，无一增加） | `IQCommon/logger/handlers`、`IQData/utils/calexrights_func`、`.../plugin_system_fly_basicdata/calexrights_func`（同源孪生）、`IQEngine/plugins/plugin_system_trade/trade_live_broker` |
| 缺陷数不变、签名变化 | `IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc`：`tick_worker_thread` 由「序列错位」变「长度不等」（原本即缺陷，仍是缺陷） |

`fly/data/quotation.pyc` 两臂的缺陷函数**同名同数**（3 个）——本轮改动对该文件中性。

## 5. Round 18 线索（记在本文件，不再另开文件）

1. **产物比核新**：`git log -- site-packages/fly/data/quotationOK.py` 显示该产物最后一次被提交
   修改是 Round 9（`393d9ff0`），即磁盘产物来自 7 轮之前的核；Round 10~17 之间某次核改动使
   quotation 再生成变差，而闸门每轮回滚把退化永久隐藏。下一步按轮次取 `core/cfg/*.py` 指纹
   对 quotation 及其余 10 个「再生成劣于磁盘产物」的文件做二分，定位退化提交。
2. 只剩 1 个缺陷函数的文件 28 个（本轮实测），优先取同源孪生对
   `IQData/{utils,plugins/plugin_system_fly_basicdata}/calexrights_func.pyc`——一次修复可翻正 2 个 pyc。
