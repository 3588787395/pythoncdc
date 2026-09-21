# Round 18 验证记录（fixes）：R18-A 逐步骤实测

设计见 `arm-design.md`，结果汇总见 `OUTCOME.md`。所有数值都是工具/脚本自打印输出，
逐条给出处；本轮零手写数字。

## 一、单点（秒级回路）

`D:/Temp/r18/r18_fn.py change_future_real_date --trace` —— 只取
`site-packages/fly/data/quotation.pyc` 里 `<module>.change_future_real_date` 这一个 code object，
`build_cfg` + `RegionASTGenerator` + `CFGASTConverter` + `CFGCodeGenerator` 重生成，
再编译回 pyc 交给 `_r10_strict_check.strict_compare` 判定。

| 核 | 输出行 |
|---|---|
| HEAD `8145f6ff`（补丁前） | `[TRACE _discover_predicate_and_chain] cond=362 -> blocks=[358, 362]` ⇒ `RESULT change_future_real_date: [seq_len] orig=91 decomp=93` |
| 工作区（R18-A） | 无 TRACE 行 ⇒ `RESULT change_future_real_date: OK` |

补丁前生成的源码是 `if delivery_date and delivery_date < end[:8]:`，补丁后是
`if delivery_date < end[:8]:`（与原始源码一致）。

## 二、quotation.pyc 全模块重生成（仓库零写入）

`D:/Temp/r18/r18_quot.py`：把 `site-packages/fly/data/quotation.pyc` 复制到
`D:/Temp/r18/q/` 后重生成同级 `quotationOK.py`，用 `_r10_strict_check.check_pyc` 逐函数比对。

```
baseline artifact(磁盘产物) 缺陷函数: ['<module>.change_his_to_forward', '<module>.get_trend']
quotation  ok=148/150  缺陷=2
   - <module>.change_his_to_forward [seq_len] orig=548 decomp=549
   - <module>.get_trend [target_diff] #10 POP_JUMP_IF_FALSE 终点 orig=("'date'", 'LOAD_FAST') decomp=("'api_get'", 'LOAD_GLOBAL')
```

补丁前同法实测（镜像核二分）：`147/150`，多出的一项正是
`<module>.change_future_real_date`。⇒ **产物/核漂移对 quotation 收口**：当前核再生成结果
与磁盘产物的缺陷集合逐名相同（SubTask 13.3 的 quotation 项结案）。

项目工具自打印（`scripts/pyc_batch_verify.py single site-packages/fly/data/quotation.pyc`）：

```
  decompile_status:   partial
  total_functions:   143
  matched_functions: 142
  match_rate:        99.30%
  mismatches (1):
    - change_his_to_forward: orig=547 decomp=548 jump_diffs=1 true_diffs=377
real	0m5.084s
```

另结案 SubTask 17.9-⑥：`single` 对 quotation 实测 5.1 s 完成，不再是「必然 60 s 超时」，
本次写回与 HEAD 该条目字段逐字节相同（无差异），未产生 `failed` 误写。

## 三、全量产物门（402 条目，`_r13_gate.py`，分 8 片）

基线 = 本轮门禁前的磁盘产物逐函数严格比对（`D:/Temp/r18/base_all{1,2,3,4}.txt`）。
每片一条命令、`timeout 290`，逐片 SUMMARY：

```
g8_1 CLEAN=44 UNCHANGED=3 WORSENED(rolled back)=4
g8_2 CLEAN=41 REGRESSION(rolled back)=1 UNCHANGED=9
g8_3 CLEAN=44 UNCHANGED=6
g8_4 CLEAN=42 UNCHANGED=8
g8_5 CLEAN=43 UNCHANGED=6 WORSENED(rolled back)=1
g8_6 CLEAN=41 UNCHANGED=8 WORSENED(rolled back)=1
g8_7 CLEAN=41 UNCHANGED=9
g8_8 CLEAN=38 UNCHANGED=10 WORSENED(rolled back)=2
```

合计 402 = CLEAN 334 + UNCHANGED 59 + WORSENED(rolled back) 8 + REGRESSION(rolled back) 1，
**无一文件因本轮改动变差**（回滚全部生效，产物未被写坏）。

9 项 WORSENED/REGRESSION 逐文件（`before -> after`，括号为新生成的缺陷函数）：

| 文件 | before→after | 新生成缺陷 |
|---|---|---|
| `IQCommon/util/common_func.pyc` | 18/22→17/22 | `to_pd_result` |
| `IQCommon/api/klinedata.pyc` | 52/63→50/63 | `np_tp_pd`、`to_pd_result` |
| `IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc` | 17/18→16/18 | `to_pd_result` |
| `IQEngine/plugins/plugin_fly_data/__init__.pyc` | 20/21→19/21 | `resist_api` |
| `fly/common/flytools.pyc` | 65/66→63/66 | `get_mem_under_oom_status`、`whitelist_filter` |
| `fly/data/quote_handler.pyc` | 64/72→61/72 | `get_all_fundamentals_daily`、`get_all_valuation`、`get_all_valuation_new` |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | 37/45→35/45 | `get_real_daily_kline`、`get_real_minute_kline_bk` |
| `fly/common/market_time.pyc` | 9/10→8/10 | `trade_is_open` |
| `IQEngine/plugins/plugin_system_persist/json_persistance.pyc` | 7/7→6/7（REGRESSION） | `persist` |

归因（镜像核 A/B，`D:/Temp/r18/ab_pre{1,2,3}.json` vs `ab_post{1,2}.json`）：
上表每一项在**补丁前核**里数值与缺陷函数名逐名相同（`json_persistance` 6/7 `persist`、
`history_api` 16/18、`market_time` 8/10、`real_quote` 35/45、`flytools` 63/66、
`klinedata` 50/63、`plugin_fly_data/__init__` 19/21、`quote_handler` 61/72、
`common_func` 17/22）⇒ 全部属 Round 13 以来既有的产物/核漂移族，与 R18-A 无关。

补丁前后**逐名变化**的只有两处（均为变好）：

| 文件 | 补丁前 | 补丁后 | 消失的缺陷函数 |
|---|---|---|---|
| `site-packages/fly/data/quotation.pyc` | 147/150 | 148/150 | `<module>.change_future_real_date` |
| `site-packages/fly/data/quote.pyc` | 68/89 | 69/89 | `<module>.change_future_real_date` |

（`fly/data/quote_handler.pyc` 的缺陷清单里没有同名函数，本轮无变化。）

## 四、产物文本里被删掉的外层 elif 重复合取支

`git diff` 逐条（`-` 是本轮前的产物，`+` 是当前核输出）：

| 产物 | 变更 |
|---|---|
| `site-packages/fly/data/quotationOK.py` | `if delivery_date < end[:8]:` 恢复（另 116/135 行是产物自 Round 9 起未随核更新的整文件重排放） |
| `site-packages/fly/data/quoteOK.py` | `- if delivery_date and delivery_date < end[:8]:` → `+ if delivery_date < end[:8]:` |
| `site-packages/IQEngine/data/data_proxyOK.py` | `- if engine_instance().config.strategy.run_type == const.RunType.TRADING and now_time >= dt + datetime.timedelta(minutes=1):` → `+ if now_time >= dt + datetime.timedelta(minutes=1):` |
| `site-packages/IQCommon/util/replace_utilsOK.py` | `- if status in {301, 302} and location:` → `+ if location:` |
| `site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_sourceOK.py` | `- if self.is_rebuild == '1' and now_date > self.first_run_date and current_time >= self.rebuild_time:` → `+ if current_time >= self.rebuild_time:` |
| `site-packages/fly/simtradding/pboxAccount_jupyterhubOK.py` | `- if account_site_verification == '1' and account_type == 'PBOX_UFX_INTERFACE' and error_no != 0:` → `+ if error_no != 0:` |

本轮前产物（HEAD `8145f6ff` 的同名文件）与落地后产物，各自用项目工具的
`bytecode_diff` 对同一 pyc 打分（`D:/Temp/r18/ab_official.py`，只读比对、不重新生成，
因此两行的唯一差别就是产物文本）：

```
IQCommon/util/replace_utils                                    HEAD=7/9   POST=8/9   *** CHANGED ***
IQEngine/data/data_proxy                                       HEAD=8/9   POST=8/9
IQEngine/plugins/plugin_system_event_source/realtime_event_source HEAD=11/12 POST=11/12
fly/data/quotation                                             HEAD=142/143 POST=142/143
fly/data/quote                                                 HEAD=66/81 POST=67/81  *** CHANGED ***
fly/simtradding/pboxAccount_jupyterhub                         HEAD=3/4   POST=4/4    *** CHANGED ***
```

消失的缺陷函数名（`D:/Temp/r18/who_flip.py`、`D:/Temp/r18/pbox_who.py`）：

```
IQCommon/util/replace_utils        fixed_by_patch=['log_request']
fly/data/quote                     fixed_by_patch=['change_future_real_date']
fly/simtradding/pboxAccount_jupyterhub  HEAD 3/4 ['getVaildAccount'] -> POST 4/4 []
```

⇒ `fly/simtradding/pboxAccount_jupyterhub.pyc` 由本轮补丁从 3/4 变到 **4/4 全匹配**，
`single` 自打印 `decompile_status: ok` `match_rate: 100.00%`。
另两个索引条目里已记着旧的高值（replace_utils 8、pboxAccount 4），所以索引数值不动，
但磁盘产物本身是本轮才真正达到那个数。

## 五、复现电池

新增 `test_repros/round18_arm/`（20 项 + `run_all.py` + `ANALYSIS.md`），
`--strict` 退出码 0：

```
repros=20  MISMATCH=0  MATCH=20  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
```

11 个锚点在补丁前核 MISMATCH、补丁后 MATCH，8 个负对照与 1 个 UNCONFIRMED
（`r18a_05` for 循环内 elif 臂）两世界都 MATCH，逐个双世界实测表见
`test_repros/round18_arm/ANALYSIS.md` §四（脚本 `D:/Temp/r18arm/measure.py --core <核目录>`）。

既有 8 套电池在落地后的核上 `--strict` 全部退出码 0、UNEXPECTED=0、ERROR=0
（日志 `D:/Temp/r18/bat_round13*.log`、`bat_round14*.log`、`bat_round15_arm.log`、
`bat_round16_*.log`、`bat_round17_arm.log`）：

```
round13      repros=25  MISMATCH=14  MATCH=11  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=2
round13b     repros=0   strict-MATCH=0 strict-MISMATCH=0
round14      repros=17  MISMATCH=0   MATCH=17  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round14_join repros=16  MISMATCH=1   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=0
round15_arm  repros=12  MISMATCH=2   MATCH=10  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round16_arm  repros=16  MISMATCH=1   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round16_sink repros=15  MISMATCH=0   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=2
round17_arm  repros=26  MISMATCH=1   MATCH=25  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
```

## 六、索引回填（只用项目工具实测）

`scripts/pyc_batch_verify.py single <pyc>` 四条，工具自打印：

| 条目 | 工具输出 | 索引变更 |
|---|---|---|
| `site-packages/IQEngine/plugins/plugin_fly_data/fly_api/setting_api.pyc` | `decompile_status: ok` `15/15` `100.00%` | `partial 0.9333 matched 14` → `ok 1.0 matched 15` |
| `site-packages/IQCommon/util/backtest_info_utils.pyc` | `ok` `10/10` `100.00%` | `partial 0.9 matched 9` → `ok 1.0 matched 10` |
| `site-packages/IQEngine/plugins/plugin_system_control/__init__.pyc` | `ok` `13/13` `100.00%` | `partial 0.9231 matched 12` → `ok 1.0 matched 13` |
| `site-packages/IQEngine/config/config.pyc` | `ok` `11/11` `100.00%` | `partial 0.9091 matched 10` → `ok 1.0 matched 11` |
| `site-packages/IQEngine/api/api_base.pyc` | `partial` `47/48` `97.92%`（`cancel_order` 仍不一致） | 无变更（已是该值） |

这 4 条属**索引订正**：产物在 Round 18 落地 R18-A 之前就已逐函数全匹配
（全量门对它们判 CLEAN，before 与 after 同为 0 缺陷），只是条目停在早先轮次的 `partial`；
不是本轮补丁的效果，如实记在此处。

另外，凡本轮被核改写的产物，都用 `single` 重新量过一遍，使条目与产物一致：

| 条目 | 工具输出 | 索引变更 |
|---|---|---|
| `site-packages/fly/data/quote.pyc` | `partial` `67/81` `82.72%` | `matched 66` → `matched 67`（本轮补丁效果，见 §四） |
| `site-packages/IQCommon/util/replace_utils.pyc` | `partial` `8/9` `88.89%`（`decrypt_database_url`） | 无变更（产物本已 8，条目原停在 8） |
| `site-packages/IQEngine/data/data_proxy.pyc` | `partial` `8/9` `88.89%`（`get_bar`） | 无变更 |
| `site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | `partial` `11/12` `91.67%`（`clock_worker`） | 无变更 |
| `site-packages/fly/simtradding/pboxAccount_jupyterhub.pyc` | `ok` `4/4` `100.00%` | 无变更（条目原已记 4/4 ok） |

`single` 对 `quote.pyc` 的重生成与磁盘产物逐字节相同（`cmp` 通过），对
`replace_utils / data_proxy / realtime_event_source` 亦同 ⇒ 核输出确定性，无二次漂移。

`pyc_index.json`：条目数 402、每条 `function_count` 一律不变。

## 七、对外序列（工具自打印）

`scripts/pyc_batch_verify.py stats --index pyc_index.json`：

```
HEAD 8145f6ff（本轮开始前）：total_pyc 402  ok_pyc 356  total_functions 5746  matched_functions 5624  97.88%
Round 18（本轮收尾）      ：total_pyc 402  ok_pyc 360  total_functions 5746  matched_functions 5629  97.96%
```

+5 的构成：4 条索引订正 +4（`setting_api`/`backtest_info_utils`/`plugin_system_control`/
`config` 各 +1），本轮补丁 `fly/data/quote.pyc` 的 `change_future_real_date` +1。
