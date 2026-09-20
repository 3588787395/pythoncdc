# Round 14 结果（OUTCOME）

本轮按门禁顺序完成：单点修到完全 OK → quotation.pyc 单验 → 全量批量回归 → 归因 → 提交 push。
两条根因线：**R14-D**（dict 两个推导式塌陷，= Round 13 的 R13-D）与 **A-1**（值上下文表达式
merge 块的「双角色」归属，= Round 13 回退的 A2 的同源归属缺陷）。

## 一、口径（两把尺子，数字不得互相减法）

| 口径 | Round 13 记录 | Round 14 实测（本轮产物） |
| --- | --- | --- |
| 官方 loose（`pyc_index.json` 的 `bytecode_match_rate==1.0`，402 文件） | 351 ok / 51 partial | **353 ok / 49 partial**，函数 5617/5746 = 97.75% |
| 严格尺子（`_r10_strict_check`，噪声过滤 + 落点跟踪） | 321/402 文件 = 79.85%，函数 5970/6204 = 96.23% | **329/405 文件 = 81.23%，函数 6093/6332 = 96.23%** |

注：严格口径分母从 402 变为 405，因为全量 targets 含 3 个重复源产物（`klinedataOK.pyc`、
`klinedataOK_check.pyc` 等历史遗留 `.pyc`）；官方口径仍按 `pyc_index.json` 的 402 条计。
两行不可交叉相减。

## 二、本轮翻正清单（严格尺子，产物级）

| pyc | 之前 | 之后 |
| --- | --- | --- |
| `IQEngine/plugins/plugin_system_simulation/broker.pyc` | 28/29 | **29/29** |
| `IQEngine/plugins/plugin_system_simulation/live.pyc` | 28/29 | **29/29** |
| `site-packages/IQCommon/profiler_func.pyc` | 15/16 | **16/16** |
| `site-packages/IQData/utils/profiler_func.pyc` | 13/14 | **14/14** |
| `IQCommon/arg_checker.pyc` | 47/49 | 48/49（未翻正） |
| `IQEngine/utils/profiler_func.pyc` | 15/17 | 16/17（未翻正） |

⇒ 「每一轮至少解决一个 pyc」达成：本轮 **4 个 pyc 由 partial → 100%**。
重复源效应照旧：`profiler_func.py` 一处修复同时翻正 2 个 pyc（IQCommon 与 IQData/utils 各一份）。

## 三、验收工序与复现电池

```
quotation.pyc 单验           148/150 -> 147/150，产物门自动回滚（OK.py 仍 148/150）
全量产物门（406 targets）     CLEAN=327 UNCHANGED=67 WORSENED(回滚)=9 REGRESSION(回滚)=2
                             NO-OKPY=1（`ptradeAccountOK_marker_test.pyc`，历史测试残留）
                             elapsed=117s
test_repros/round14          repros=17 MISMATCH=0 MATCH=17 UNEXPECTED=0（10 个 SENTINEL 全部保持）
test_repros/round14_join     repros=16 MISMATCH=11 MATCH=5  UNEXPECTED=0（A2 前缀族，见 §五）
test_repros/round13          repros=25 MISMATCH=14 MATCH=11 UNEXPECTED=0
```

核心改动（均含「识别条件 → 归约方式 → AST 映射」注释，均为区域归属层判据，无跨区域跨层次启发式）：
- `core/cfg/region_analyzer.py` sha `110bf739bde62846`：新增 `_value_merge_hosts_next_if`
  （例外 3）、`_conditional_value_producing_arms`（例外 3 的窄化）、
  `_ternary_merge_hosts_next_if` 统一委托、前缀/后缀切分对三种例外共用。
- `core/cfg/region_ast_generator.py` sha `786140680c713f8f`：抽出 `_boolop_merge_owner_for`
  共用归属判据；`prefix_stmts_pending` 一次性延迟记录。
- `core/cfg/comprehension_generator.py` sha `65ea8b72ad9a34a2`：R14-D 容器 value 子区域
  各自归约，禁止推导式焊接路径认领宿主 op 的指令。

## 四、劣化归因：11 处全部是 Round 13 提交遗留债，与本轮 hunks 无关

用**文件级换件 A/B**（`D:/Temp/r14_ab2.py`、`r14_ab3.py`；只读、不写产物、退出即复原并核对 sha）
把三个 core 文件同时退回提交态（`git show HEAD:` 取 blob）后复测 14 文件集：

```
all_HEAD（三个 core 文件全退回提交态）  530 / 589
A-1 首版                               533 / 589   +_is_valid_interval +3×<module> -parse_db_url
A-1 + 窄化判据                          534 / 589   优势 4 个函数，劣势 0 个
```

- 劣化清单（`klinedata 52→50`、`common_func 18→17`、`real_quote 37→35`、
  `plugin_fly_data/__init__ 20→19`、`history_api 17→16`、`flytools 65→63`、
  `market_time 9→8`、`quotation 148→147`、`quote_handler 64→61`、
  `json_persistance 7→6`、`base_validator 6→5`）在 `all_HEAD` 与本轮之间
  **数字与缺陷集合完全相同** ⇒ 已提交的核心本来就产出劣于已提交的产物；
  产物门的回滚保护使仓库产物未受损，但核心侧债仍在（SubTask 13.3）。
- 同类陷阱：`klinedataOK.pyc` 数值 53/63 不变但缺陷集互换
  （`get_history_common,get_price_common` ↔ `np_tp_pd,to_pd_result`）——
  **闸门按计数判 UNCHANGED 会掩盖它**，故本轮额外做了缺陷集级比对。
- 本轮唯一自身创伤 `parse_db_url` 已由窄化判据消除（534/589 劣势 0）。
- 被产物门改写的两个重复源产物已按 HEAD 字节复原，不随本轮提交。

## 五、遗留与下一轮入口

1. **SubTask 13.1/13.2（A2 正解）**：`round14_join` 11 个 MISMATCH 仍在，两种症状同族——
   `decomp = orig + 13`（整块前缀被重复发射，`prefix_stmts_pending` 布尔粒度太粗）与
   `decomp = orig - 18`（then 区被截断）。正解是在归属层按**语句/指令粒度**登记
   「块语句序列由哪个区域发射」，设计见 `a2-design.md`。
2. **SubTask 13.3**：§四 的 11 处核心侧债（清单与证据已备）。
3. **SubTask 13.4 / A-2**：R13-C 链尾吸收（约 46 个函数字节差，收益面最大），
   最小复现待写：`PluginManager.set_engine` ×2。
4. **Task 5 遗留**：`replace_utils.decrypt_database_url`（295→324）、
   `cgroup_utils.add_process_to_cgroup`(+2)、`set_cgroup_config`(+1)。
5. **只差 1 个函数的文件 = 31 个**（严格口径，本轮实测），是下一轮的选靶池。

## 六、验收命令（可直接复跑）

```bash
# 严格尺子全量闸门（带自动回滚；基线 = rounds/round14/baseline_strict_after_r13.txt）
PYTHONIOENCODING=utf-8 python _r13_gate.py --targets D:/Temp/r13_all_targets.txt \
  --baseline .trae/specs/region-reduction-30pyc-perfect-10rounds/rounds/round14/baseline_strict_after_r13.txt \
  --out D:/Temp/r14_gate_c1.json --budget 270

# 官方 loose 口径（只读产物，不写索引）
PYTHONIOENCODING=utf-8 python D:/Temp/r14_official.py

# 复现电池
PYTHONIOENCODING=utf-8 python test_repros/round14/run_all.py
PYTHONIOENCODING=utf-8 python test_repros/round14_join/run_all.py
```
