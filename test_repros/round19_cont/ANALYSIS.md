# Round 19 分析：if 臂尾「自然迭代回边」被 `[R3-Continue]` 补发射成显式 `continue`

目标 pyc：`site-packages/IQCommon/util/user_info_utils.pyc`（项目工具 `8/9 partial`，
唯一不一致函数 `remove_lock_files`；`_r10_strict_check` 判
`[seq_len] orig=96 decomp=97`）。

## 一、缺陷的最小事实

产物 `user_info_utilsOK.py` 里 `remove_lock_files` 的最内层：

```python
                for file in files:
                    if file.endswith('.lock'):
                        file_path = os.path.join(root, file)
                        try:
                            os.unlink(file_path)
                        except BaseException:
                            system_log.error(...)
                        continue          # ← 原始源码里没有这一条
```

指令级比对（`D:/Temp/r18/r18b_diff.py`，同一脚本换个函数名即可复跑）显示两世界唯一
真实差异就是多出一条 `JUMP_BACKWARD to 420`（420 = `for file in files:` 的 FOR_ITER）：

```
 POP_EXCEPT
-JUMP_BACKWARD to 420        原始：try/except 结束直接回到循环头
+JUMP_FORWARD  to 712        产物：跳到 if 的汇合块 712
 RERAISE / COPY / POP_EXCEPT / RERAISE
 JUMP_BACKWARD to 420
+JUMP_BACKWARD to 420        ← 多出的那一条，由上面那条 `continue` 生成
 JUMP_BACKWARD to 404        外层循环尾
```

跳转方向/落点桩的差异尺子本来就归一化掉（`JUMP_FORWARD→712` 与 `JUMP_BACKWARD→420`
终点相同），**唯一的真缺陷是那多出来的一条回边**：`for: if c: <stmts>` 形态里循环体
自然迭代尾本来就有这条 `JUMP_BACKWARD`，源码级再写一条 `continue` 就变成两条。

## 二、发射点：两条路径对同一结构给出互斥结论

* `_process_if_blocks` 的 CONTINUE 角色分支（`core/cfg/region_ast_generator.py:20571-20759`）
  已经**正确抑制**：`_r100_suppress`（`:20646`）与 RC3 Mode A/B（`:20667`）之后
  `_r100_suppress=True` ⇒ 不发射 `Continue`。
* 但 `_if_generate_normal` 的 **`[R3-Continue]` 补发射**（`:16869-16896`）随后又判一次：
  「then 分支末块末指令是 `JUMP_BACKWARD` 且落点 == `region.merge_block`，
  且 `merge_block is 当前循环头`」⇒ `then_stmts.append({'type': 'Continue'})`。
  这条规则不看上层已经得出的「if 是循环体末条语句 ⇒ 该回边是自然迭代」结论，
  于是把上层刚做对的归并**推翻**。实测发射行 = `:16896`（全函数唯一命中）。

同一层次、同一结构（`merge_block` 即循环头、假出口直通迭代回边）在两条路径上得到
相反结论——这正是 Round 17 删判据④时用的同一条标准：**同层同结构必须同结论**。

## 三、四个候选规则（全部在仓库外的镜像核上实测）

镜像配方：`git archive HEAD core bytecode pycdc.py _r10_strict_check.py` 解到
`D:/Temp/r19/mirror/<name>/`，只改镜像里的 `core/cfg/region_ast_generator.py`
（脚本 `D:/Temp/r19/probes/make_mirrors.py`）。仓库零写入。

| 候选 | 规则 | 电池（39 项） | 全量 402 pyc 逐函数 A/B |
|---|---|---|---|
| `cand_a` | 整段删掉 `[R3-Continue]`（`:16877-16896`） | 修 10 锚点，负对照全保 | 改好 2 / **改坏 5**（净 −3） |
| `cand_g` | 加 `and not _r19_tail_by_fallthrough(...)`（新增 28 行辅助：臂尾块由本区域块**裸 fall-through** 进入） | 修 10 锚点，负对照全保 | 改好 2 / **改坏 2**（净 0） |
| `cand_e` | `cand_d` + `cand_g` 两条一起加 | 修 9 锚点，负对照全保 | 改好 1 / 改坏 0（净 +1） |
| **`cand_d`** | **加一行 `and not self._if_false_path_is_loop_iteration(region)`** | **修 9 锚点，负对照全保** | **改好 1 / 改坏 0（净 +1）** |

`cand_d` 用的 `_if_false_path_is_loop_iteration`（`:18752`）是**既有同层判据**，
`:20665` 的 CONTINUE 角色抑制已经在用它；把它接到 `[R3-Continue]` 上就是让两条路径
共用同一个结论，不新增任何规则。`cand_e` 与 `cand_d` 在电池与全量两项实测上**逐条相同**
⇒ 那 28 行辅助谓词是纯冗余，按「最小改动」取 `cand_d`。

`cand_a` / `cand_g` 被实测否掉，改坏的真实函数（电池里复现不出来，只有全量 A/B 抓得到）：

```
cand_a  BROKEN IQCommon/data/basic_data_source.pyc               8->7   BasicDataSource.get_security_info
cand_a  BROKEN IQCommon/data/local_finance.pyc                  20->19  get_local_financial_factors / get_local_valuation_factors
cand_a  BROKEN IQData/plugins/plugin_system_fly_basicdata/basic_data_source.pyc 43->42  BasicDataSource.get_security_info
cand_a  BROKEN IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc 97->96  TradeLiveBroker._process_* / _sync_worker
cand_a  BROKEN fly/data/quote.pyc                               69->68  Quote.api_get_from_*_zeromq 等
cand_g  BROKEN IQCommon/data/local_finance.pyc                  20->19  get_local_financial_factors
cand_g  BROKEN IQEngine/plugins/plugin_system_trade/trade_live_broker.pyc 97->96  TradeLiveBroker._process_*
```

⇒ **本电池的 19 个负对照不足以否掉过宽规则**：`cand_a` 在本电池上 39 项全绿（负对照零破坏），
在全量上却净亏 3 个函数。门禁必须包含全量逐函数 A/B，不能只看电池。

`cand_d` 全量唯一非计数变化：`fly/data/quote_handler.pyc` 的
`get_kline_local`（本来就不一致）产物长度 677→676，匹配数 11/11 不变。

## 四、逐条两世界实测

| 项 | HEAD `26e330ca` | `cand_d` | 归类 |
|---|---|---|---|
| 01 anchor_corpus_try_except | MISMATCH 65/66 | MATCH | R19-A 修掉 |
| 02 anchor_one_loop_try_except | MISMATCH 32/33 | MATCH | R19-A 修掉 |
| 03 anchor_try_except_pass | MISMATCH 27/28 | MATCH | R19-A 修掉 |
| 04 anchor_try_finally | MISMATCH 31/32 | MISMATCH 31/32 | 残留 |
| 05 anchor_try_except_else | MISMATCH 37/38 | MISMATCH 37/38 | 残留 |
| 06 anchor_two_excepts | MISMATCH 43/44 | MATCH | R19-A 修掉 |
| 07 anchor_while_outer_try | MATCH | MATCH | 未复现 |
| 08 anchor_two_deep_try | MISMATCH 37/38 | MATCH | R19-A 修掉 |
| 09 anchor_in_method_try | MISMATCH 32/33 | MATCH | R19-A 修掉 |
| 10 anchor_module_scope_try | MISMATCH 38/39 | MATCH | R19-A 修掉 |
| 11 anchor_else_arm_try | MATCH | MATCH | 未复现 |
| 12 anchor_arm_ends_nested_while | MISMATCH 27/29 | MISMATCH 27/29 | 残留 |
| 13 anchor_second_if_try | MISMATCH 37/38 | MATCH | R19-A 修掉 |
| 14 anchor_elif_arm_try | MISMATCH 42/43 | MISMATCH 42/43 | 残留 |
| 15 anchor_try_in_with_arm | MATCH | MATCH | 未复现 |
| 16 anchor_handler_raises | MISMATCH 32/33 | MATCH | R19-A 修掉 |
| 17 anchor_while_finally | MATCH | MATCH | 未复现 |
| 18 anchor_inner_for_break | MATCH | MATCH | 未复现 |
| 19 anchor_try_then_sibling_stmt | MATCH | MATCH | 未复现 |
| 20 neg_real_if_continue | MATCH | MATCH | 负对照 |
| 21 neg_real_stmt_then_continue | MATCH | MATCH | 负对照 |
| 22 neg_real_continue_then_body_stmts | MATCH | MATCH | 负对照 |
| 23 neg_continue_in_try_finally | MATCH | MATCH | 负对照 |
| 24 neg_chained_sibling_ifs | MATCH | MATCH | 负对照 |
| 25 neg_if_elif_at_loop_tail | MATCH | MATCH | 负对照 |
| 26 neg_if_else_at_loop_tail | MATCH | MATCH | 负对照 |
| 27 neg_arm_with_return | MATCH | MATCH | 负对照 |
| 28 neg_outer_continue_after_inner_loop | MATCH | MATCH | 负对照 |
| 29 neg_while_body_call | MATCH | MATCH | 负对照 |
| 30 anchor_while_in_if_deep | MATCH | MATCH | 未复现 |
| 31 neg_nested_if_deep_arm_tail | MATCH | MATCH | 负对照 |
| 32 neg_try_except_in_body_not_arm | MATCH | MATCH | 负对照 |
| 33 neg_try_except_arm_then_if_tail | MATCH | MATCH | 负对照 |
| 34 neg_real_continue_in_nested_if | MATCH | MATCH | 负对照 |
| 35 neg_arm_call_then_continue_after_if | MATCH | MATCH | 负对照 |
| 36 neg_plain_arm_call | MATCH | MATCH | 负对照 |
| 37 neg_plain_arm_augassign | MATCH | MATCH | 负对照 |
| 38 neg_arm_with_block | MATCH | MATCH | 负对照 |
| 39 neg_arm_nested_for | MATCH | MATCH | 负对照 |

汇总（工具自打印）：

```
HEAD    repros=39  MISMATCH=13  MATCH=26  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=7
cand_d  repros=39  MISMATCH=4   MATCH=35  ERROR=0  UNEXPECTED=0  NOT-REPRODUCED=7
```

## 五、交给修复工程师的门禁

```
# 落地前（HEAD 核）：MISMATCH=13、UNEXPECTED=0、退出码 0
PYTHONIOENCODING=utf-8 python test_repros/round19_cont/run_all.py --strict
# 落地后：把 §四 标「R19-A 修掉」的 9 项 EXPECT 从 MISMATCH 改成 SENTINEL，再跑
#         期望 MISMATCH=4、UNEXPECTED=0、退出码 0
PYTHONIOENCODING=utf-8 python test_repros/round19_cont/run_all.py --strict
```

镜像核复核（仓库零写入）：`D:/Temp/r19/mirror/cand_d` 已是 `cand_d` 的成品，
`PYTHONIOENCODING=utf-8 python test_repros/round19_cont/run_all.py --core D:/Temp/r19/mirror/cand_d`
必须给出 `MISMATCH=4 MATCH=35 UNEXPECTED=0`。

全量逐函数 A/B 复跑（必须仍是「改好 1 / 改坏 0」）：

```
PYTHONIOENCODING=utf-8 python D:/Temp/r19/probes/r19_par.py <落地后核目录> <tag> 10 0 402 decomp
PYTHONIOENCODING=utf-8 python D:/Temp/r19/probes/r19_sum.py <tag>
```

## 六、残留（本轮不覆盖）

1. 锚点 04（臂尾 `try/finally`）、05（臂尾 `try/except/else`）、12（臂尾嵌套 `while`）、
   14（`elif` 臂尾 `try`）——四者在 `cand_a`/`cand_g` 下 04 能修、其余三项仍 MISMATCH，
   说明它们走的是**另一条**发射路径（不是 `:16896`），需要单独定位。
2. 7 个未复现形状（07/11/15/17/18/19/30）：`while` 外层、else 臂、`with` 臂内 try、
   `while...finally`、内层 for 带 break、臂尾之后还有兄弟语句、深层 `while` in `if`。
3. `user_info_utils` 之外的同族残留：`IQCommon/util/trade_info_utils.pyc`（`cand_a`/`cand_g`
   能改好 `35→36`，`cand_d` 不动它）——记为下一轮候选，本轮不为其放宽判据。
