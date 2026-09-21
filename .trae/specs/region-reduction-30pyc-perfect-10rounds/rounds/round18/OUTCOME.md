# Round 18 结果（OUTCOME）

一条根因线（R18-A），按门禁顺序完成：单点修到完全 OK → quotation.pyc 单验 → 全量批量回归 →
索引回填 → 提交 push。设计稿 `arm-design.md`，验证记录 `fixes.md`。

## 一、解决了什么

`core/cfg/region_ast_generator.py` `_discover_predicate_and_chain`（Round 13 的回退式 and 短路链
重建）把**外层 `elif` 的测试块**当前驱候选收下：候选块与本区域条件块末指令跳同一汇合点、真路径
fallthrough 进入本区域条件块时即入链，而既有守卫只排除「某个区域的 entry 且该区域 condition_block
就是它」的块。`elif X:` 的测试块不是任何区域的 entry（它只是父 if 链区域的 `elif_conditions` 成员），
于是被吸收成内层条件的第一合取支，产物把外层测试重复发射一遍：

```
- if delivery_date and delivery_date < end[:8]:
+ if delivery_date < end[:8]:
```

修法是最小删除：新增原则 2（每块唯一归属）守卫 —— 前驱候选只要是**任一其它 IfRegion 的
`elif_conditions` 成员**就 `return None` 放弃整条链回退，交由既有嵌套 if 路径。
`core/cfg/region_ast_generator.py` +15/−1（守卫 8 行，其余是判据注释与 docstring `**嵌套处理**`
段同步；`region_analyzer.py` 本轮零改动）。两条守卫都只删不增：命中时不生成任何新形状。

被翻正的函数（项目工具 `bytecode_diff` 对「本轮前产物」与「落地后产物」逐名 A/B，`fixes.md` §四）：

| pyc | 函数 | 本轮前 → 落地后 |
|---|---|---|
| `site-packages/fly/simtradding/pboxAccount_jupyterhub.pyc` | `getVaildAccount` | 3/4 → **4/4**，`single` 报 `decompile_status: ok` `100.00%` |
| `site-packages/fly/data/quote.pyc` | `change_future_real_date` | 66/81 → 67/81（索引同步 66→67） |
| `site-packages/IQCommon/util/replace_utils.pyc` | `log_request` | 7/9 → 8/9（条目原已记 8，数值不动） |

另有 3 个产物同样去掉重复合取支（`IQEngine/data/data_proxyOK.py`、
`plugin_system_event_source/realtime_event_sourceOK.py`、`fly/data/quotationOK.py`），
本轮官方计数不变；它们与上表三行一起构成 §四 那 6 个产物改动。

## 二、门禁与归因

1. 单点（秒级回路）：`<module>.change_future_real_date` 由 `[seq_len] orig=91 decomp=93` 变 `OK`。
2. quotation.pyc：当前核重生成 147/150 → 148/150，缺陷集合与磁盘产物**逐名相同**
   （`change_his_to_forward`、`get_trend`）⇒ Round 16/17 连续两轮的 SubTask 13.3 quotation 项结案。
   `single` 实测 `real 0m5.084s`（不再是必然 60 s 超时，SubTask 17.9-⑥ 结案），写回字段与 HEAD 相同。
3. 全量产物门（402 条目，分 8 片）= CLEAN 334 + UNCHANGED 59 + WORSENED(rolled back) 8 +
   REGRESSION(rolled back) 1。9 项异常在镜像「补丁前核」上数值与缺陷函数名逐名相同
   ⇒ 全部属 Round 13 以来既有产物/核漂移族，本轮零新增回退，回滚全部生效。
4. 电池：新增 `test_repros/round18_arm/` 20 项 `--strict` 退出码 0
   （`repros=20 MISMATCH=0 MATCH=20 ERROR=0 UNEXPECTED=0 NOT-REPRODUCED=1`；11 个锚点补丁前
   MISMATCH、补丁后 MATCH，8 个负对照与 1 个 UNCONFIRMED 两世界同 MATCH）；
   既有 8 套在新核上 `--strict` 全部退出码 0、UNEXPECTED=0、ERROR=0。
5. 所有被核改写的产物都用 `single` 重量一遍，且 `single` 的重生成与磁盘产物逐字节相同（`cmp`）
   ⇒ 无二次漂移。

## 三、索引与对外序列

`pyc_index.json` 共 5 个条目变动，条目数 402、每条 `function_count` 一律不变：

- 4 条 `partial → ok`（`IQCommon/util/backtest_info_utils`、`IQEngine/config/config`、
  `plugin_fly_data/fly_api/setting_api`、`plugin_system_control/__init__`）是**索引订正，不是本轮
  补丁的效果**：它们的产物在 R18-A 落地之前就已在项目工具上逐函数全匹配（全量门对它们判 CLEAN，
  before 与 after 同为 0 缺陷），条目停在 Round 10 的旧值。
- 1 条 `matched_functions 66 → 67`（`fly/data/quote.pyc`）是 R18-A 的效果。

`scripts/pyc_batch_verify.py stats --index pyc_index.json`：

```
本轮开始前（HEAD 8145f6ff）：total_pyc 402  ok_pyc 356  total_functions 5746  matched_functions 5624  97.88%
本轮收尾                  ：total_pyc 402  ok_pyc 360  total_functions 5746  matched_functions 5629  97.96%
```

## 四、代价与残留

1. 9 文件既有产物/核漂移族（`to_pd_result` 三连：`IQCommon/util/common_func`、`IQCommon/api/klinedata`、
   `plugin_fly_data/fly_api/history_api`；`plugin_fly_data/__init__` `resist_api`；`fly/common/flytools`；
   `fly/data/quote_handler`；`plugin_system_realquote/real_quote`；`fly/common/market_time`；
   `plugin_system_persist/json_persistance` REGRESSION）——闸门每轮都会 WORSENED 回滚一次，直到按轮次
   二分定位「当前核比磁盘产物差」的那次提交。
2. quotation 残留 2：`change_his_to_forward` seq_len +1、`get_trend` 跳转终点不同。
3. `r18a_05`（for 循环内 elif 臂）在补丁前后都 MATCH，属未复现锚点：新守卫对该形状无覆盖，留下一轮。
4. `IQCommon/util/user_info_utils.pyc`（8/9）唯一缺陷 `remove_lock_files`
   `[seq_len] orig=96 decomp=97`：产物在 `for file in files: if ...: try/except` 末尾多发射一条
   `continue`（多一个 `JUMP_BACKWARD to 420`）。该处已是 Round 07 / R4-H / R100 / RC3 四条抑制判据
   叠加之地，本轮不掺进去，列为下一轮单点目标。
5. `strategy.pyc`、`calexrights_func` 孪生、`handlers` 2、`trade_live_broker` 26、`r16a_05`、
   `r15a_08`/`r15a_09`、`r17a_25`、T1/T2 then 臂收集顺序、SubTask 13.4、Task 5 遗留
   （`decrypt_database_url` +29、`cgroup` +2/+1）。
6. `git push origin main` 仍失败（`Recv failure: Connection was reset`），本轮提交留在本地。

## 五、提交物

核：`core/cfg/region_ast_generator.py`。
产物：`site-packages/fly/data/{quotation,quote}OK.py`、`site-packages/IQEngine/data/data_proxyOK.py`、
`site-packages/IQCommon/util/replace_utilsOK.py`、
`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_sourceOK.py`、
`site-packages/fly/simtradding/pboxAccount_jupyterhubOK.py`。
记录：`pyc_index.json`（5 条目）、`test_repros/round18_arm/`（20 复现 + `run_all.py` + `ANALYSIS.md`）、
`rounds/round18/{arm-design.md,fixes.md,OUTCOME.md}`、`tasks.md`（Task 18）。
