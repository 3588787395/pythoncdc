# Round 19 验证记录（fixes）：R19-A 逐步骤实测

设计见 `arm-design.md`，逐条两世界实测见 `test_repros/round19_cont/ANALYSIS.md`，
结果汇总见 `OUTCOME.md`。以下数值全部是工具/脚本自打印输出。

## 一、单点（修到完全 OK）

`scripts/pyc_batch_verify.py single site-packages/IQCommon/util/user_info_utils.pyc`：

```
  decompile_status:   ok
  total_functions:   9
  matched_functions: 9
  match_rate:        100.00%
  missing_in_decomp: []
  extra_in_decomp:   []
```

严格尺子复验同一 pyc：

```
  OK      9/9  IQCommon/util/user_info_utils.pyc
文件级：全部一致 1 / 1，有真缺陷 0
函数级：严格一致 9 / 9
```

产物 `site-packages/IQCommon/util/user_info_utilsOK.py` 的全部改动是删掉一条语句（`git diff --stat`
= `1 file changed, 1 deletion(-)`）：

```
                         except BaseException:
                             system_log.error('用户 {} 锁文件 {} 清理失败，错误原因：{}'.format(...))
-                        continue
```

## 二、发射点实测（打补丁前，`sys.settrace` 抓真实命中）

| 函数 | `merge_block is header` | `else_blocks` | `_if_false_path_is_loop_iteration` | 结论 |
|---|---|---|---|---|
| `user_info_utils::remove_lock_files` | True | 空（`[]`） | **True** | 补发的 `continue` 多余（假出口 blk@712 是单条 `JUMP_BACKWARD→420` 纯回边） |
| `user_info_utils::get_vip_user_info` | True | 4 块 | False | 与本轮无关（谓词因 else 分支为假） |
| `local_finance::get_local_valuation_factors` | True | 空 | **False** | `continue` 必须留（假出口 blk@544 有 LOAD_GLOBAL/LOAD_ATTR/CALL/POP_TOP 用户语句后才回边） |
| `plugin_system_fly_basicdata/basic_data_source::get_security_info` | True | 空 | **False** | `continue` 必须留（假出口 blk@254 含 BUILD_MAP/STORE_SUBSCR） |

⇒ 该谓词在「多余」与「必需」两类真实样本上取值正确，是可用判据；后两行正是宽规则
（`cand_a`/`cand_g`）会改坏的形状。

## 三、核改动

`core/cfg/region_ast_generator.py` 一个 hunk，`+38/−1`，其中**代码只有一行**
（`[R3-Continue]` 补发射守卫新增末判据 `and not self._if_false_path_is_loop_iteration(region)`，
原第④条的 `):` 移到新行末），其余 37 行是该规则的判据注释与实测记录改写
（`[R19-A 修复]` 段：识别条件／归约方式／唯一归属·结构结论一致／反编译流程／保留理由）。
不新增方法、不新增谓词、不看名字/常量/偏移。

字节级：BOM 保留、纯 CRLF（`crlf == lf == 48226`）、`ast.parse` 通过；
`2966969 → 2970385` 字节，`48189 → 48226` 行；
raw sha256[:16] `93203a1ec37e1ae4 → faf70dafbce09acf`，LF 归一 `a107457c5215daaf → e7ab6a8d436603a5`。
`git diff` 过滤注释后的代码变化只有那 1 行（`−` 1 行 / `+` 2 行）。

## 四、round19_cont 电池（39 项）

```
打补丁前（HEAD 26e330ca）：repros=39  MISMATCH=13  MATCH=26  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=7
打补丁后（R19-A）        ：repros=39  MISMATCH=4   MATCH=35  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=7
镜像核 cand_d 复跑       ：repros=39  MISMATCH=4   MATCH=35  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=7   （逐项判定与落地核相同）
```

修掉的 9 项锚点（01/02/03/06/08/09/10/13/16）EXPECT 已改标 `SENTINEL`；
残留 4 项（04 臂尾 `try/finally`、05 `try/except/else`、12 臂尾嵌套 `while`、14 `elif` 臂尾 `try`）
仍为 `MISMATCH`（`--strict` 通过，实测走的是另一条发射路径）；
未复现 7 项为 `UNCONFIRMED`；负对照 19 项两世界全 `MATCH`。`--strict` 退出码 0。

## 五、既有电池（回归复验，全部 `--strict`）

```
round13      repros=25  MISMATCH=13  MATCH=12  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=2   （r13_02_spurious_continue_loop 本轮转 MATCH，EXPECT 改标 SENTINEL）
round13b     repros=0   strict-MATCH=0 strict-MISMATCH=0
round14      repros=17  MISMATCH=0   MATCH=17  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round14_join repros=16  MISMATCH=1   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=0
round15_arm  repros=12  MISMATCH=2   MATCH=10  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round16_arm  repros=16  MISMATCH=1   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round16_sink repros=15  MISMATCH=0   MATCH=15  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=2
round17_arm  repros=26  MISMATCH=1   MATCH=25  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
round18_arm  repros=20  MISMATCH=0   MATCH=20  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=1
```

与 Round 18 收尾时逐套相同，唯一变化是 `round13` 的 `r13_02_spurious_continue_loop`
由「复现缺陷」变「已修」（这正是 Round 13 当年记下的同族缺陷形状）。

## 六、quotation.pyc 单验

`scripts/pyc_batch_verify.py single site-packages/fly/data/quotation.pyc`：

```
  decompile_status:   partial
  total_functions:   143
  matched_functions: 142
  match_rate:        99.30%
  mismatches (1):
    - change_his_to_forward: orig=547 decomp=548 jump_diffs=1 true_diffs=377
```

与 Round 18 收尾时逐字相同，产物 `quotationOK.py` 未被改写（`git status` 干净）。

## 七、全量产物门（402 条目，`_r13_gate.py`，分 8 片，逐片一条命令）

基线 = 落地前磁盘产物逐函数严格比对（`D:/Temp/r19/gate/b00.txt … b07.txt`，
`_r10_strict_check.py --manifest`，utf-8 写出）。逐片 SUMMARY：

```
g00 CLEAN=42 UNCHANGED=14 WORSENED(rolled back)=2
g01 CLEAN=54 UNCHANGED=3
g02 CLEAN=39 UNCHANGED=2
g03 CLEAN=51 UNCHANGED=5 WORSENED(rolled back)=1
g04 CLEAN=36 UNCHANGED=7 WORSENED(rolled back)=2
g05 CLEAN=32 UNCHANGED=7
g06 CLEAN=38 REGRESSION(rolled back)=1 UNCHANGED=7
g07 CLEAN=43 UNCHANGED=13 WORSENED(rolled back)=3
```

合计 402 = CLEAN 335 + UNCHANGED 58 + WORSENED(rolled back) 8 + REGRESSION(rolled back) 1。
9 项 WORSENED/REGRESSION 与 Round 18 的 9 项**逐文件、逐数值相同**：

```
IQCommon/api/klinedata.pyc                52/63 -> 50/63
IQCommon/util/common_func.pyc             18/22 -> 17/22
IQData/plugins/plugin_system_realquote/real_quote.pyc 37/45 -> 35/45
IQEngine/plugins/plugin_fly_data/__init__.pyc        20/21 -> 19/21
IQEngine/plugins/plugin_fly_data/fly_api/history_api.pyc 17/18 -> 16/18
IQEngine/plugins/plugin_system_persist/json_persistance.pyc 7/7 -> 6/7   （REGRESSION）
fly/common/flytools.pyc                   65/66 -> 63/66
fly/common/market_time.pyc                 9/10 ->  8/10
fly/data/quote_handler.pyc                64/72 -> 61/72
```

⇒ 本轮零新增回退（回滚全部生效，产物未被写坏）。落地后 `git status` 只有
`core/cfg/region_ast_generator.py`、`pyc_index.json`、`site-packages/IQCommon/util/user_info_utilsOK.py`
三处改动——即 R19-A 对全语料产物的净影响就是目标文件那一条 `continue`。

## 八、索引与对外序列

`pyc_index.json` 只有 1 个条目变动（`single` 工具自己写回）：
`IQCommon/util/user_info_utils.pyc` `partial 0.8888888888888888 matched 8`
→ `ok 1.0 matched 9`。条目数 402、每条 `function_count` 一律不变。

`scripts/pyc_batch_verify.py stats --index pyc_index.json`：

```
本轮开始前（HEAD 26e330ca）：total_pyc 402  ok_pyc 360  total_functions 5746  matched_functions 5629  97.96%
本轮收尾                  ：total_pyc 402  ok_pyc 361  total_functions 5746  matched_functions 5630  97.98%
```

+1 全部来自本轮补丁（镜像核全量 A/B：improved 1、broken 0）。
