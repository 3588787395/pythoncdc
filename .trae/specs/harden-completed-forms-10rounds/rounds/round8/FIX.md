# Round 8 修复报告（修复工程师 · 续完成批次）

- 修复人：修复工程师（Round 8 续完成批次，接手前位中断批次）
- 日期：2026-10-04
- 对象：REVIEW.md §6 交接单 B54（第一优先）续完 + B55 续完；既有登记面（B48×2/B46×1）与 Round 7 残留面零变差
- 树状态：HEAD = `6a42146d` 不变；工作树唯一 core 变更 = `core/cfg/region_ast_generator.py`（前位遗留 + B55-c 续完，474+/23−）
- 唯一判据：`scripts/pyc_verify.py`（pylingual compare_pyc，Python 3.11.7）；全部 OK.py 仅经 `pycdc.py -o` 再生成，零手改；全部命令 ≤300 s

---

## §1 遗留 diff 审计结论（前位批次工作树盘点）

前位工程师遗留 `core/cfg/region_ast_generator.py` 在途变更（+384/−23，含 [B54]/[B55] 注释锚点）+ r8_05/r8_09/r8_10 三份重生成 OK + 根目录 17 份 `_tmp_*.py` 草稿 + 过期的 `r8_fix1.json`（2026-10-03T22:46:59，OK 再生成前的中间态读数）。

**任务书基线读数「101/118 持平」系过期 batch json 所致**：遗留改动实际已生效。本批以重生成 OK + 全量 batch 实测确认：

| 遗留改动 | 审计判定 | 实测证据 |
|---|---|---|
| [B54] 链式赋值重建族（`_b54_scan_chain_continuation` / `_b54_target_ast` / `_b54_validate_chain_target_window` / `_b54_build_chain_assign_from_accumulation` + 自循环体门控 + merge 路径折入 + return 值后缀切分） | **有效，全部保留** | r8_05 11/11（`r8_assign_chain` 幻影 Expr 消失、`r8_assign_chain_subscript` 尾随 return 恢复）、r8_09 `r8_dh_while_assign_chain` 链重建（7/10）、r8_10 `r8_x_assign_ternary_chain` 链×三元（7/12）——B54 4/4 单元转 MATCH |
| [B55] 分支 A：`_b55_is_try_handler_exit_trailing_return`（try/except 尾随 return None 预标记豁免，generate() 清理循环） | **有效，保留** | r8_03 `r8_pass_except` 幻影 return 消除（8/9→续完后 9/9） |
| [B55] 分支 B：try 体装配 return_succ 裸 return 块登记（`_generate_try` 后继块判定） | **有效，保留** | try 体 return 后继块不再重复发射为幻影 `return None`（tools/scheduler/r6_11/r8_08 四 OK 产物中 6 处不可达幻影 `return None` 消失，重编译逐单元 Equal，全部读数持平或更好） |
| 17 份 `_tmp_*.py` 草稿 | 无效副产物 | 已全部删除（本批另产生 9 份诊断草稿一并清理，共 26 份） |

结论：**遗留改动零回退**（无死路 hunk）；回退数 = 0，保留数 = 全部。

## §2 本批续完动作与锚点

### B55-c 续完（r8_pass_try_finally，1 单元）——`core/cfg/region_ast_generator.py`

- **锚点**：`_generate_try`（:28172）post-try 收集面 `_post_try_blocks_r19n2`（try_blocks 后继路径 ：28440 附近，`_succ not in _region_block_set_r19n2` 排除条件）+ 收尾 `finally:` 毯式 `for block in region.blocks: generated_blocks.add(block)`（:29732 附近）。
- **机制定位**（本批实测诊断）：`try: pass / finally: pass / return 1` 编译为 try 入口块 `JUMP_FORWARD` 直接待发射 return 块（offset 18）；区域分析把该块纳入 `TryExceptRegion.blocks`（跨度归属）却不给任何结构角色（不在 try_blocks/finally_blocks/handlers/finally_copy）。常规 post-try 收集因「后继 ∈ region.blocks」被排除；`_generate_try` 收尾毯式标记把它标记已生成 → 独立 BASIC 区域跳过 → 尾随 `return 1` 整句蒸发。`_b55_is_try_handler_exit_trailing_return`（前位分支 A/B）与预标记循环均触达不了该形态（该区域经 `_has_meaningful_return` 逃逸，块 18 的吞没点在 `_generate_try` finally 毯式标记，非预标记循环）。
- **修复**：新增 `_b55_is_pure_const_return_block`（:3085 附近，剥噪后至多两条：可选 `LOAD_CONST <const>` + `RETURN_VALUE/RETURN_CONST`，任意常量值）+ post-try 收集窄门控通道 [B55-c]（try_blocks 后继路径之后、finally_copy 路径之前）：`has_finally` 且常规收集为空时，收集「∈ region.blocks ∧ 位于异常表保护跨度之外（`start_offset ≥ try_offset_end`）∧ 不属于任何已知结构部分（try/else/finally/cleanup/handler/finally_copy keys）∧ 非 if-merge ∧ 无 RERAISE ∧ 纯常量 return ∧ block_to_region 归属为本 region ∧ 未生成」的后继块为 post-try 块，交既有 `_post_try_blocks_r19n2` 发射循环在 try 语句之后发射。dtc-r08 判据（「region.blocks 内无结构角色块 = post-try 顺序代码」）的同层推广，W21 反向经验（finally 副本后继不收集）由「跨度外 + 纯 return」双门控落实。
- **迭代记录（诚实）**：初版误以 `finally_copy_blocks.values()`（int 保留标记）为块列表迭代 → `TypeError` 从 `_generate_try` 内逸出被上游吞掉 → r8_01/r8_02/r8_09/r8_11 五个 try 面 MATCH 单元劣化（102/118）。经 file-log 定位后改为 `.keys()`（keys 即副本块起始偏移，与 dtc-r08 消费端一致）并加保护跨度门控，劣化单元全部恢复 MATCH。
- **自测哨兵**：r8_01 11/11、r8_02 10/10、r8_11 5/6（`r8_dh2_try_full_sections`/`r8_ret_try_else`/`r8_dh_try_finally_return`/`r8_ret_try_except`/`r8_ret_finally_overwrite` 保持 MATCH）、r8_08 9/9、r8_04 10/10、n8_01/n8_02 9/9 全过。

### 认领面汇总

| 项 | 状态 | 单元 |
|---|---|---|
| B54 链式赋值重建崩坏族 | **封闭**（前位落地，本批验证） | 4/4 |
| B55 try/finally 吞尾族 | **封闭**（前位 1 + 本批 1） | 2/2 |
| B56–B62 / B48 / B46 | 未认领（本批未触） | 11 单元残留 |

## §3 自测读数表（全部真实跑，命令 ≤300 s）

| # | 项 | 声明 | 实测 | 判定 |
|---|---|---|---|---|
| ① | BOM `head -c 3 core/cfg/region_ast_generator.py \| xxd` | efbbbf | `00000000: efbb bf` | ✓ |
| ① | `grep -rn "_R23N20_DEBUG\|R23N21_DEBUG" core/ \| wc -l` | 0 | **0** | ✓ |
| ① | ast.parse + import（utf-8-sig 读入） | 通过 | 通过 | ✓ |
| ② | r8 全量 batch（13 文件 118 单元，r8_*+n8_*）→ `r8_fix1.json` | 认领单元转 MATCH、登记面零变差 | **107/118**（success 7 / failure 6）；B54×4 + B55×2 全部转 MATCH；B48×2（r8_aug_chain_rhs / r8_x_augassign_ternary）+ B46×1（r8_x_ret_nested_ternary）逐位持平；n8_01 **4/4**、n8_02 **5/5** | ✓ |
| ③ | Round 7 残留 17 文件 → `r8_residual.json` | 81/117 持平 | **81/117**，17/17 文件逐单元与登记面零漂移（r7_01 8/9、r7_04 6/7、r7_05 15/16、r7_06 7/10、r7_07 4/7、r7_08 4/8、r7_10 7/8、r7_11 6/7、r7_12 5/8、r7_14 5/9、rv6_01 3/5、rv6_02 2/4、rv6_04 1/4、rv6_05 3/4、rv6_06 1/4、rv7_02 2/4、rv7_04 2/3） | ✓ |
| ④ | round6 全量 16 文件 → `r8_round6_recheck.json` | 115/115 | **115/115**（16/16 success） | ✓ |
| ⑤ | rv6+rv7 变体面 11 文件 → `r8_rv67_check.json` | 持平 | **30/44**（rv6 18/29 + rv7 12/15；11/11 文件与 round6/round7 登记面逐单元零漂移。任务书写的「20/33」与实际变体面文件清单不符——实际全集 44 单元，逐文件全部持平，任何子集亦持平，如实记录） | ✓ |
| ⑥ | 六哨兵 + option_account（全部重生成 + single） | tools 6/6、trade_schedule 6/6、mq_connector 13/13、strategy 2/2、scheduler 52/52、trade_info_utils 36/41、option_account 35/35 | **6/6、6/6、13/13、2/2、52/52、36/41、35/35**；trade_info_utils 失败 5 名单 = 基线（trade_operation / kill_trade_process / get_trade_status / query_trade_strategy_info / query_strategy_id） | ✓ |
| ⑦ | `git status` OK.py 盘点 | 仅预期产物 | core 1 文件 + 报告 json 4 份 + OK 再生成 10 份（§4 明细），无其他文件触碰 | ✓ |

r8 面 11 个残留 MISMATCH = B56×2（r8_x_assert_ternary / r8_dh2_match_guard）+ B57×1 + B58×1 + B59×1 + B60×1 + B61×1 + B62×1 + B48×2 + B46×1，与 REVIEW.md §5 登记名单逐一对应。

## §4 OK.py 再生成盘点（全部 `pycdc.py -o`，零手改）

- **r8 面（10 份）**：r8_01–r8_11 中 10 份 + n8_01/n8_02（读数与登记面一致或转 MATCH）。内容变化 6 份：
  - r8_03（B55：幻影 return None 消除 + `return 1` 恢复）、r8_05 / r8_09 / r8_10（B54 链重建，前位批次已再生成本批确认）；
  - r8_08（B55 副效应：try 体 return 后不可达幻影 `return None` 消除，9/9 保持）。
- **哨兵/回归面（4 份内容变化，其余零漂移）**：IQCommon/toolsOK（幻影 return 消除，6/6）、IQEngine/utils/schedulerOK（×2 处幻影消除，52/52）、round6/r6_11_with_trymixOK（幻影消除，6/6）、r8_08（见上）。幻影消除均不可达语句级清理，重编译逐单元 Equal，全部读数持平或更好。
- 其余重生成产物（round6 15 份、rv6/rv7 11 份、residual r7/rv 17 份、mq_connector/trade_schedule/strategy/option_account/trade_info_utils 5 份）与已提交版逐字节零漂移。

## §5 未落地清单（交后续批次）

| 项 | 单元 | 最小复现 |
|---|---|---|
| B56 assert 原生形态降级族 | 2 | r8_10 r8_x_assert_ternary、r8_11 r8_dh2_match_guard |
| B57 for 可迭代三元吞前导语句 | 1 | r8_10 r8_x_for_iter_ternary |
| B58 raise 异常类三元整句蒸发 | 1 | r8_10 r8_x_raise_ternary_class |
| B59 with 体首赋值蒸发 | 1 | r8_09 r8_dh_with_assert |
| B60 match mapping `**rest` 幻影解包 | 1 | r8_09 r8_dh_match_multi |
| B61 for-else else 外提 + break 蒸发 | 1 | r8_09 r8_dh_for_else_del |
| B62 return(call+BoolOp) 尾语句蒸发 | 1 | r8_07 r8_assert_nested_func |
| B48 augassign × 三元 RHS（Round 7 沿袭） | 2 | r8_06 r8_aug_chain_rhs、r8_10 r8_x_augassign_ternary |
| B46 三元提升 if/else 语句（Round 7 沿袭） | 1 | r8_10 r8_x_ret_nested_ternary |

合计 11 单元（r8 攻击面 107/118 → 封顶 118/118 尚差 11）+ Round 7 残留 36 单元（r8_residual 81/117）。

## 附：本批新增/变更文件

- `core/cfg/region_ast_generator.py`（B55-c 续完 + 前位遗留保留，474+/23−）
- `rounds/round8/FIX.md`（本报告）、`r8_fix1.json`（重生成）、`r8_residual.json`（重生成）、`r8_round6_recheck.json`（新）、`r8_rv67_check.json`（新）
- OK 再生成 10 份（§4）；`_tmp_*.py` 26 份全部删除
