# R100 修复工程师报告

## 一、根因分析

### 1. 现象澄清（与会话开始时测试报告的差异）

- 测试报告记录 check_strategy.pyc 为 50%（1/2），44 true_diffs。本会话实测发现：上一会话中断前，比较器 `testqouter/round1/base.py` 已在 commit `d4a9370f`/`eb6ed0b2` 中完成 [R100]/[R101] 归一化（CONTAINS_OP 取反等价、POP_JUMP_IF_NONE/FALSE 等价、jump_diffs 不再计入 true_diffs、try 块 return 抑制）。以 HEAD 反编译器 + 该比较器复测，`check_strategy.pyc` 的反编译输出**语义已正确**（无条件取反、无误加 continue、for-else 结构正确），single verify 直接达到 100%。
- 10 个最小复现实例中 9 个同样已通过；唯一残留真实缺陷是 **repro_100_04_chain_compare.py**：for-else 内链式比较 if 的 then 分支被注入多余 `continue`，导致重编译多出一条 JUMP_BACKWARD（7 true_diffs）。
- 另发现遗留验证脚本 `_r100_verify_repros.py` 的 MATCH 判定逻辑错误（要求 compare_bytecode 返回 None/空 dict，但其契约是恒返回非空 dict、以 `match=True ⇔ true_diffs 为空` 表示匹配），导致任何结果都判为 DEFECT-REPRO。已按比较器契约修正。

### 2. repro_100_04 根因（本轮修复的真实缺陷）

字节码形态（链式比较 `if low < k <= high:` 位于 for 循环体末尾）：

```
82:  LOAD low; LOAD k; SWAP; COPY; COMPARE(<); PJIF → 118   # 第一段假出口
106: LOAD high; COMPARE(<=); PJIF → 166                      # 第二段假出口
116: JUMP_FORWARD → 122                                      # 条件成立连接块
122: <body: result.extend(v)>                                # then 体
164: JUMP_BACKWARD → 80                                      # then 体自己的回边连接块 (PURE_CONTINUE)
118: POP_TOP; JUMP_BACKWARD → 80                             # 链式比较假出口清理块 = merge_block = back_edge_block
166: <for-else 体>
```

区域归约结果：`IF_THEN(entry=82, then_blocks=[116,122,164], merge_block=118)`；FOR_LOOP 的 `back_edge_block=118`。两条分支各自经独立回边块（164 / 118）回到循环头 80——这是链式比较 POP_TOP 清理迫使 CPython 拆分回边块的自然产物。

缺陷路径：AST 生成阶段 `_process_if_blocks` 按 CONTINUE/PURE_CONTINUE 角色处理末块 164 时，无条件补发 `{'type': 'Continue'}`。而源码级正确输出 `if low < k <= high: body`（if 为循环体最后一条语句）重编译时，CPython 会自然再生"假出口清理回边 + then 体回边"两条 JUMP_BACKWARD——显式 Continue 属于冗余补发，使字节码净增一条后向跳转，产生指令错位级联 diff。

对照场景（为何不能一刀切删除）：
- `if c: continue`（repro_100_05 等）：纯 continue 块独占分支（stmts 为空），其回边不由循环结构保证，必须保留显式 Continue；
- `if c: body; continue` 后还有 post-if 语句（repro_100_08）：merge 是普通后续语句块（不以 JUMP_BACKWARD→header 结尾），continue 必须保留；
- 本缺陷形态：merge_block 本身即迭代终止符（JUMP_BACKWARD→header）且分支体非空且该纯回边块为分支末块 → 回边由重编译自然再生，Continue 冗余。

## 二、修复点清单 + 算法依据

| # | 文件 / 方法 | 修改 | 算法依据 |
|---|---|---|---|
| 1 | `core/cfg/region_ast_generator.py` `_process_if_blocks`（CONTINUE/PURE_CONTINUE 角色处理分支，L16335 起） | 补发 Continue 前增加结构性冗余判定 `_r100_suppress`：(a) 所属 region 为 IfRegion 且存在 merge_block（≠本块）；(b) merge_block 末指令为 JUMP_BACKWARD(_NO_INTERRUPT) 且目标=当前循环 header；(c) 本块为分支块列表中偏移最大的末块；(d) 分支已产出语句（stmts 非空）。四条同时成立则不补发显式 Continue | 区域归约算法原则 2（每块唯一归属）：该 PURE_CONTINUE 连接块的回边语义由「if 为循环体末条语句」的结构化形态在重编译时整体再生，不应由 if 体重复发射；原则 4（入口引用语义）：IfRegion 以 merge_block 引用汇合点，merge 即迭代终止符表明两分支在迭代末尾汇合，源码层无需 goto 式显式跳转。与既有 [Round 07 迭代收尾排除]（`_block_is_structural_for_iter_exit`）同一原理的推广：凡回边由循环结构保证的纯连接块不得补发 Continue |
| 2 | `_r100_verify_repros.py` | MATCH 判定改为比较器契约：`match=True / jump_only=True / true_diffs==0`；函数级复核仅在模块级匹配后进行 | 与 `scripts/pyc_batch_verify.py` 的 matched 判定（`cmp.get('match') or cmp.get('jump_only')`）对齐 |

未新增任何 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 方法；无后处理补丁、无跨区域启发式、无深度上限、无 pyc 特定硬编码。修复落在 AST 生成的通用分支发射逻辑上。

## 三、docstring 更新清单

- `core/cfg/region_ast_generator.py` `_process_if_blocks`：6 节模板保持不变（算法依据/归约顺序/唯一归属判定/嵌套处理/入口引用语义/反编译流程六节原文未动），模板之后追加 `[R100 fix]` 段落说明纯连接 continue 块冗余抑制判据；行内注释以 `[R100 fix]` 标注（含四条判据逐条说明）。
- 本轮未修改任何 `_identify_*_regions` 方法（根因在生成侧而非识别侧：区域识别结果 IF_THEN/FOR_LOOP 本身正确）。
- `_r100_verify_repros.py` 判定处标注 `[R100 fix]` 注释。

## 四、回归结果（数字对比）

| 项目 | 修改前 | 修改后 |
|---|---|---|
| R100 复现 10 例（`python _r100_verify_repros.py`） | 脚本逻辑缺陷全报 DEFECT-REPRO；按比较器契约实测 9 MATCH / 1 DEFECT（repro_100_04, 7 true_diffs） | **10/10 MATCH** |
| round_15 minimal_repros（13 py） | 10 MATCH / 3 DEFECT（repro_04、repro_07、verify_repros.py，均预先存在） | 10 MATCH / 3 DEFECT（完全一致，零回归） |
| round_19 minimal_repros（23 py） | 22 MATCH / 1 DEFECT（verify_repros.py 脚本自身，预先存在） | 22 MATCH / 1 DEFECT（完全一致，零回归） |
| round_07+08 minimal_repros（29 py） | 22 MATCH / 7 DEFECT（nested-try 系列+脚本，预先存在） | 22 MATCH / 7 DEFECT（完全一致，零回归） |
| round_11+14+16 minimal_repros（49 py） | 39 MATCH / 10 DEFECT（nested-if-in-else 系列+脚本，预先存在） | 39 MATCH / 10 DEFECT（完全一致，零回归） |
| round_20+21 minimal_repros（37 py） | 33 MATCH / 4 DEFECT（te005/te008/te012+脚本，预先存在） | 33 MATCH / 4 DEFECT（完全一致，零回归） |

以上"修改前"基线均通过 `git stash push core/cfg/region_ast_generator.py` 后实测复跑取得，缺陷清单逐一比对完全相同 → 本轮修改零回归。

pyc 级抽查（全部保持 ok / match_rate=100%）：default_info.pyc、trading_day_manager.pyc、mq_connector.pyc、resource_utils.pyc、zt_api.pyc、custom_tools.pyc、**trading_schedule.pyc**（continue-sink 典型场景 get_trading_schedule 所在文件）、trade_schedule.pyc ×2。

模块导入检查：`import core.cfg.region_analyzer / region_ast_generator / code_generator` 通过。

## 五、目标 pyc 最终状态

```
[SINGLE] site-packages/IQCommon/api/check_strategy.pyc
  decompile_status: ok      total_functions: 2      matched_functions: 2
  match_rate: 100.00%       missing_in_decomp: []   extra_in_decomp: []
  OK.py: site-packages/IQCommon/api/check_strategyOK.py（已生成，py_compile 通过）
```

check_strategy 函数反编译源码与原始语义一致：`if pre_version < change_version <= current_version:` 未取反；无注入 continue；for-else 结构正确。

## 六、残留不一致数

- check_strategy.pyc：**0**（2/2 函数一致）。
- R100 复现实例：**0**。
- 历史轮次复现目录中的 DEFECT（round_08 nested-try 系列、round_14 nested-if-in-else 系列、round_21 te005/te008/te012 等）均为本轮之前即存在的既有问题，数量与基线完全一致，不属于本轮改动引入或扩大的范围。

## 七、未尽事项说明

1. 测试报告所述"条件取反 + for-else 误识别"两缺陷在 HEAD 反编译器上无法复现——其成因是报告生成时点早于比较器 commit d4a9370f/eb6ed0b2（将 jump-only 及若干等价形态计为匹配）。当前 OK.py 源码经人工审读确认语义正确，非被比较器掩盖（POP_JUMP 方向取反若真实存在会改变比较/跳转语义，OK.py 中不存在）。
2. `site-packages/IQCommon/util/resource_utilsOK.py` 在批量验证时被工具自动再生成（HEAD 代码即可复现的既有漂移，与本次源码修改无关，已用 stash 对照证实）；未手工编辑任何 *OK.py。
3. 会话开始时的遗留诊断脚本 `_r100_cfg/_r100_dis/_r100_dis2/_r100_diff/_r100_patch/_r100_revert/_r100_test_fix/_r100_regions*.py` 未做改动（其中 _r100_patch/_r100_revert 含未完成的中断补丁逻辑，未执行）；本轮新增 `_r100_regression.py`（回归批跑脚本）供后续轮次复用。
