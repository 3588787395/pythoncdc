# Round 19 结果（OUTCOME）

一条根因线（R19-A），按门禁顺序完成：单点修到完全 OK → quotation.pyc 单验 → 全量批量回归 →
索引回填 → 提交 push。设计稿 `arm-design.md`，验证记录 `fixes.md`，逐条两世界实测
`test_repros/round19_cont/ANALYSIS.md`。

## 一、解决了什么

`core/cfg/region_ast_generator.py` `_if_generate_normal` 里的 `[R3-Continue]` 补发射（Round 03 为
`is_ST_stock_real` 那类「if/elif 链后还有后续语句」形状加的分支终结边 `continue`）四条判据是
① `then_stmts` 非空、② `self._current_loop` 存在、③ `region.merge_block is 当前循环 header`、
④ then 分支末块以 `JUMP_BACKWARD` 直达 merge。四条只看 **then 臂自己**，不看这个 if 在循环体里的
位置：`for …: if c: <语句>` 且该 if 是循环体末条语句时，条件的假出口本身就是循环的自然迭代回边，
臂尾回边已由 `for` 语句重编译自然再生，再补一条源码级 `continue` 就多编一个 `JUMP_BACKWARD`
⇒ `[seq_len] orig=96 decomp=97`。

同层的 `_process_if_blocks` CONTINUE 角色块抑制路径（`_r100_suppress`）早就用
`_if_false_path_is_loop_iteration(region)` 判定同一件事并给出「不发射」的结论，两条路径对同一结构
结论相反。修法是接进来而不是新建判据：给 `[R3-Continue]` 守卫补第⑤条末判据
`and not self._if_false_path_is_loop_iteration(region)`（原第④条的 `):` 移到新行末）。
**代码改动一行**，其余 37 行是该规则的判据注释（`[R19-A 修复]` 段：识别条件／归约方式／
唯一归属·结构结论一致／反编译流程／保留理由）。不新增方法、不新增谓词、不看名字/常量/偏移。

该 `continue` 补发射规则不可整体删除：实测删掉整个 `[R3-Continue]` 块在 5 个真实文件上净 −3 函数
（`basic_data_source`、`local_finance`、`plugin_system_fly_basicdata/basic_data_source`、
`trade_live_broker`、`fly/data/quote`）。宽规则（只保留④、去掉⑤的 `cand_a`/`cand_g` 形状）在
全语料 A/B 上净 −3，虽然它们能过 round19_cont 全部 19 个负对照 —— 电池负对照不足以否证宽规则。

被翻正的函数（`fixes.md` §一）：

| pyc | 函数 | 本轮前 → 落地后 |
|---|---|---|
| `site-packages/IQCommon/util/user_info_utils.pyc` | `remove_lock_files` | 8/9 → **9/9**，条目 `partial 0.888…` → `ok 1.0`，`single` 报 `decompile_status: ok` `100.00%`，严格尺子同报 `OK 9/9` |

全语料只有这一个函数因本轮改动变好（镜像核全量 A/B：improved 1、broken 0），对应产物唯一改动是
`site-packages/IQCommon/util/user_info_utilsOK.py` 删掉 `except BaseException:` 臂后那条多余
`continue`（`1 file changed, 1 deletion(-)`）。这正是 Round 18 OUTCOME §四第 4 条列出的下一轮单点目标。

## 二、门禁与归因

1. 单点（修到完全 OK）：`user_info_utils.pyc` 由 `partial 8/9` 变 `ok 9/9 100.00%`，严格尺子
   `OK 9/9`。发射点 `sys.settrace` 实测四个真实函数：目标函数谓词 `True`（该补发是多余的），
   `get_local_valuation_factors`、`get_security_info` 谓词 `False`（`continue` 必须留）——
   后两个正是宽规则会改坏的形状（`fixes.md` §二）。
2. quotation.pyc：`single` 实测 `partial 142/143 99.30%`，与 Round 18 收尾时逐字相同，
   缺陷仍只有 `change_his_to_forward`；产物 `quotationOK.py` 未被改写（`git status` 干净）。
3. 全量产物门（402 条目，分 8 片）= CLEAN 335 + UNCHANGED 58 + WORSENED(rolled back) 8 +
   REGRESSION(rolled back) 1。9 项异常与 Round 18 的 9 项**逐文件、逐数值相同**
   ⇒ 仍是 Round 13 以来既有产物/核漂移族，本轮零新增回退，回滚全部生效。
4. 电池：新增 `test_repros/round19_cont/` 39 项，`--strict` 退出码 0
   （补丁前 `MISMATCH=13 MATCH=26 NOT-REPRODUCED=7` → 补丁后 `MISMATCH=4 MATCH=35 NOT-REPRODUCED=7`，
   `ERROR=0 UNEXPECTED=0`；镜像核 `cand_d` 复跑逐项判定相同）。9 个修掉的锚点 EXPECT 改标
   `SENTINEL`；19 个负对照两世界全 `MATCH`。
   既有 9 套在新核上 `--strict` 全部退出码 0、UNEXPECTED=0、ERROR=0，与 Round 18 收尾时逐套相同，
   唯一变化是 `round13` 的 `r13_02_spurious_continue_loop` 由「复现缺陷」变「已修」（EXPECT 改标
   `SENTINEL`）—— 同一族缺陷在 Round 13 就记过形状。
5. 索引回填只由 `single` 工具自己写回，本轮被核改写的产物只有 `user_info_utilsOK.py` 一个，
   其 `single` 重生成与磁盘产物逐字节相同（`cmp`）⇒ 无二次漂移。

## 三、索引与对外序列

`pyc_index.json` 只有 1 个条目变动（上述 `user_info_utils`），条目数 402、每条 `function_count`
一律不变。

`scripts/pyc_batch_verify.py stats --index pyc_index.json`：

```
本轮开始前（HEAD 26e330ca）：total_pyc 402  ok_pyc 360  total_functions 5746  matched_functions 5629  97.96%
本轮收尾                  ：total_pyc 402  ok_pyc 361  total_functions 5746  matched_functions 5630  97.98%
```

## 四、代价与残留

1. round19_cont 残留 4 个锚点仍 `MISMATCH`：04 臂尾 `try/finally`、05 `try/except/else`、
   12 臂尾嵌套 `while`、14 `elif` 臂尾 `try` —— 实测走的是另一条发射路径（不由 `[R3-Continue]`
   命中），另 7 项 `UNCONFIRMED`（本轮构造不出该形状）留下一轮。
2. 9 文件既有产物/核漂移族（`to_pd_result` 三连：`IQCommon/util/common_func`、`IQCommon/api/klinedata`、
   `plugin_fly_data/fly_api/history_api`；`plugin_fly_data/__init__` `resist_api`；`fly/common/flytools`；
   `fly/data/quote_handler`；`plugin_system_realquote/real_quote`；`fly/common/market_time`；
   `plugin_system_persist/json_persistance` REGRESSION）——闸门每轮都会 WORSENED 回滚一次，直到按轮次
   二分定位「当前核比磁盘产物差」的那次提交。
3. quotation 残留 2：`change_his_to_forward` seq_len +1、`get_trend` 跳转终点不同。
4. `IQCommon/util/trade_info_utils.pyc` 的同族多发射只有宽规则能修，宽规则在全语料 A/B 上净 −3，
   本轮如实放弃，需另找判据。
5. `strategy.pyc`、`calexrights_func` 孪生、`handlers` 2、`trade_live_broker` 26、`r16a_05`、
   `r15a_08`/`r15a_09`、`r17a_25`、`r18a_05`、T1/T2 then 臂收集顺序、SubTask 13.4、Task 5 遗留
   （`decrypt_database_url` +29、`cgroup` +2/+1）。

## 五、提交物

核：`core/cfg/region_ast_generator.py`（+38/−1，代码 1 行）。
产物：`site-packages/IQCommon/util/user_info_utilsOK.py`（−1 行 `continue`）。
记录：`pyc_index.json`（1 条目）、`test_repros/round19_cont/`（39 复现 + `run_all.py` + `ANALYSIS.md`）、
`test_repros/round13/run_all.py`（`r13_02` EXPECT 改标）、
`rounds/round19/{arm-design.md,fixes.md,OUTCOME.md}`、`tasks.md`（Task 19）。
