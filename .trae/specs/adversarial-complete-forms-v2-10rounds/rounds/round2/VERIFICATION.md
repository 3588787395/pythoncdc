# Round 2 主代理验证报告（Task 2.4）

- 验证执行：主代理（零实现，判据唯一 = `scripts/pyc_verify.py`；RV2 方法学 = 先以当前树 regen 全部 OK.py 再 verify）。
- 验证对象：HEAD = `d8db3448`（round2 回退拦截整改后）。
- 驱动脚本：`verify_final2.py`（regen+verify+compare 8 片 + small34 + quotation + tests 六套件）+ `verify_driver.py` / `verify7_split.py`（复用 round1 归档工具，regen 改覆盖写）；逐命令日志 `final_verify_log.txt`。
- 总耗时 1613s，全部命令 ≤300s（SMALL34 首跑 301s 超时 → 按纪律拆两半 small34_a/b 重跑合并；VERIFY7-SPLIT 266.5s 在限内）。

## §1 验证序六步读数（整改后终读数）

| # | 步骤 | 基线 | 本轮 | 判定 |
|---|------|------|------|------|
| 1 | 34 小测试集 batch（拆两半合并） | 1505/1568、success 1/34 | **1505/1568**、success 1/34，REGRESSIONS=0 IMPROVED=0 | 持平 ✓ |
| 2 | 全量 402（8 片 regen+batch+compare） | 6554/6617（99.05%）、369/402 | **6554/6617、369/402**，8×compare 全部 **REGRESSIONS=0 IMPROVED=0** | 逐位持平 ✓ |
| 3 | quotation.pyc 单验 | 152/153（change_his_to_forward） | 152/153，失败单元同一 | 持平 ✓ |
| 4 | tests 六套件 | 277 passed / 2 failed（test_B01 + test_BOUNDARY_02）/ 2 xpassed | 277 passed / 2 failed（同名两测试）/ 2 xpassed | 零新增失败 ✓ |
| 5 | IV.2 门禁自检 | — | 见 §3 | PASS ✓ |
| 6 | 读数汇报 | — | 见 §4 | — |

分片明细（与基线逐片逐位一致）：shard0 777/786、shard1 **462/469**、shard2 537/538、shard3 883/887、shard4 848/855、shard5 993/999、shard6 789/801、shard7 1265/1282。

## §2 回退拦截记录（验证序发现 → 整改 → 复验闭环）

1. 首轮全量（fresh regen）6553/6617：shard1 `trade_info_utils.pyc` 的 `<module>.create_user_code_iqe` 基线 success → Different bytecode（-1 单元）。按回退拦截条款打回修复工程师。
2. 根因（FIX_P3.md §8）：P2 提交 de039b80 的 B90 分发包裹 `_convert_formatted_value_expr` 遮蔽 `''.join([FV,…])` 列表裸 FV 事实 → `_generate_call` has_fv 判 False → join 归一失效（C2 转换层产出与发射端消费判据脱节）。提交级二分（git worktree @87e59c49 vs @de039b80）确证。
3. 整改（提交 d8db3448）：包裹产物携带 `_b90_wrapped` 节点元数据 + 发射端 join 归一前还原裸 FV（无标记 JoinedStr 不解包；B90 守卫不删，round1 拼接/f-string 区分语义保持）。
4. 复验：全量恢复 6554/6617 与基线逐位一致；修复后反编译输出与 round1 终态逐字节一致（修复工程师实测）。

**方法学注记**：诊断初期「隔离 single 36/41 vs batch 35/41」分歧系产物版本错位（隔离跑读到 round1 终态陈旧 OK.py），非进程内跨文件状态污染——`_generated_regions` 为实例属性 per-file 新建，污染假说证伪（证据链见 FIX_P3.md §8）。

## §3 IV.2 门禁自检

| 项 | 结果 |
|---|---|
| IMPORT_OK | core.cfg 七模块 import 全过 ✓ |
| COMPILE_OK | 全量 compile_error=0（8 片）✓ |
| BOM | region_analyzer/region_ast_generator 首 3 字节 efbbbf 单头；ast_converter/code_generator 原无 BOM 保持原状 ✓ |
| 插桩 | grep print(/breakpoint(/pdb 新增 0 ✓ |
| 禁止前缀 | `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 新增 0（存量豁免 `_merge_block_is_*` ×2）✓ |
| 落地标记 grep | `_b90_wrapped`（ast_converter.py:1520 / code_generator.py:4320）、`_combine_annassign_statements`、`_is_inside_intermediate_loop`、`_nr_is_ancestor`、`_bo_chain_jump_targets` 均在树 ✓ |
| 影响面 | 全量 regen 后仅目标/顺带 OK.py 变化，MATCH 面产物零漂移（修复工程师批次证据 + 本轮 8 片 compare IMPROVED=0 佐证）✓ |

## §4 轮门禁与读数汇报

- **本轮封闭破口**：B84 / B85 / B86 / B87（体蒸发 + handler 臂两变体）/ B88 主体 / B89（含分组 boolop 残余）/ B90 / B91 / B92 / B95 / B96 + x09 SWAP 尾段（P2 移交项）——共 11 项登记破口封闭，轮门禁（≥1）远超满足。
- **42 探针读数**：评审基线 154/189 → 终态 **172/196**（c06 消 COMPILE_ERROR 后单元分母 +7）；负对照 nm01/nm02/nc01/nc02/nx01 全 MATCH。
- **站桩回归**：45 文件（评审基线面）逐位持平；round2 探针重点面（m01/m07/m08/m12/c01/c06/c11/x04/x09）整改后逐位一致。
- **移交清单**（如实登记，供 Round 3+）：B87 残余（c04.CTryNest，region_analyzer try/else/finally 分解域）、B88 残余（x08.return_leaf，随 B78 融合批次）、B93（幻影 with 镜像）、B94（NOP 残段假循环）、B97（handler 臂 break）、**B98 登记建议**（分组 boolop 保真，rv3_02/rv3_07 实证）、杂散 *OKOK.py 清理项。
- **沙箱/环境事件如实记录**：主代理 regen 首跑受 safe-delete 批量删除守卫拦截（每分片预删 50 OK.py 超出 turn 预算），改覆盖写 regen 后复跑成功；SMALL34 单命令 301s 超时按纪律拆半。

**终判：验证序六步全过，REGRESSIONS=0，Round 2 验证通过。**
