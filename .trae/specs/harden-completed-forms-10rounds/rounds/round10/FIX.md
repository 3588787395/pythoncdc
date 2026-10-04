# Round 10 终审 10.1b 修复批次报告（FIX）

批次：REVIEW.md §4 决策表 P1 优先级（B72/B48/B46/B71）+ 新破口；验证判据唯一 = scripts/pyc_verify.py（附件 compare_pyc，sha 9c7567bd6776b36b）。

## 封闭章节

### B72 nonlocal 声明发射缺失（P1）✅ 封闭
- 判据三要素：识别条件 = STORE_DEREF 写访问且 argval ∈ co_freevars 且 ∉ co_cellvars（code object 元数据，同层事实）；归约方式 = 直接命中 nonlocal 声明集（编译器已验证的封闭函数绑定事实），孙代透传（中间层 co_cellvars 为空）不再被直接父层 cellvars 过滤误杀；AST 映射 = Global 声明集增补 nonlocal 名。
- 锚点：core/cfg/region_analyzer.py `_detect_global_declarations`（~1984-2040，含三要素 docstring 与 C1/C2/C3 条款）。
- 自测：r10_14 4/7→**7/7**；r10_16 4/7→**7/7**；负对照 n10_01–04 全 MATCH；r10_11/12/13 全 MATCH。

### B48 augassign×三元操作符降级（P1）✅ 封闭
- 判据三要素：识别条件 = TernaryRegion merge_block 剥噪后首个 STORE_* 之前（仅跳 SWAP）首条有效指令为 BINARY_OP 且 oparg ∈ [13,25]（3.11 in-place 编码段，无魔法阈值）；归约方式 = 登记 is_augassign/augassign_op/augassign_target_kind 通道（与 BoolOpRegion 同构）；AST 映射 = AugAssign(op=oparg 映射操作符, value=未折叠纯 IfExp)，替代固定 `x = x + (t)` 模板。
- 锚点：region_analyzer.py `_B48_INPLACE_BINOP_MAP` + `_b48_attach_ternary_augassign`（两处 TernaryRegion 构造点调用）；region_ast_generator.py `_generate_ternary`（`_b48_ternary_raw` 保存 + 条件发射 AugAssign）。
- 自测：r7_03 5/7→**7/7**；r8_06 9/10→**10/10**；r8_10 7/12→9/12（其中 r8_x_augassign_ternary 封闭）。

### B46 三元提升 if/else 语句（P1）✅ 部分封闭（2/3 形态）
- 判据三要素（true 臂嵌套三元对称放行，与 23541 false 臂通道对称）：识别条件 = true_block 为已归约 TernaryRegion 入口（区域成员关系）∧ 尾部条件跳转目标 ∈ 该内层区域成员块集合（内层自身判别跳转，非嵌套 if 语句头逃逸边）∧ false_block 单表达式 ∧ 内层 merge 以 STORE_*/RETURN_* 终结（值被同块消费的栈事实 = 表达式位）；归约方式 = 两道嵌套 if 拒绝门（_boolop_merge_to_ternary 门 + false_is_ternary 门）对称放行，建外层 TernaryRegion（嵌套即抽象节点）；AST 映射 = ast.IfExp(body=内层 IfExp)，禁止 IfRegion 语句路径接管。
- 锚点：region_analyzer.py `_detect_ternary_pattern`（`_b46_true_nested` 标志 + 两道门放行 + docstring B46 条款）。
- 自测：r7_07 4/7→**6/7**（t_nest_left_assoc、t_nest_mixed_binop 封闭）；r8_10 r8_x_ret_nested_ternary 封闭；r7_12/r7_14 失败名单与基线逐位一致（零新破口）。

### B71 finally 体循环控制终结块（P1）⚠ 实施降级（部分）
- 已落地：B68 门控扩展（region_ast_generator.py `_b68_is_tryfin_tail_releasable` 3173-3191 + docstring [B71] 条款）——纯 POP_TOP/JUMP_* 终结块（continue=backward 跳转；break=无 machinery 纯前向跳转终结）按用户控制流计，显式排除出「空 finally」分类。
- 实施降级项（证据留存）：
  1. `_collect_finally_body_blocks` POP_EXCEPT unwind 前向截停：曾使 fin_break 宿主 `return total` 回归循环后（取证：fin_blocks 含 blk74 → 修复后独立 BASIC Region）；但 rv6_04 `try_fin_with_nested` 等 with 清理链依赖 POP_EXCEPT+JUMP_FORWARD 合法副本跟随，复验存在回归风险，已回退（HEAD 对照读数逐位一致后确认回退无损）。
  2. finally 正常副本 break 终结块发射：动态取证（D:\Temp\r10_then38.py）证实 blk38 role=BREAK、loop.break_blocks=[38]，但 `_process_if_blocks([blk38], IfRegion, 'then')` 返回 []（24245-24551 区间存在静默认领跳过，未能在本批次定位精确跳过点）；fin_continue 的幻影 elif（try 体 IfRegion 吸收 finally 正常副本 58/72/74/104）同属发射归属层，未动。
- 自测：r10_21 维持 2/4（fin_continue_stmt 正对照 MATCH 保持）；HEAD 对照（git stash 实测）读数逐位一致 = 零回归。

## 实施降级清单汇总
| 破口 | 降级内容 | 理由 |
|---|---|---|
| B46 | t_nest_in_condition（融合条件三元）未封闭 | 需融合条件识别通道 + 误判 TernaryRegion(entry=12) 撤销 + 生成端 IfExp(test=IfExp) 重建三件套；判据可构造（动态取证 r10_incond.py：两臂各携带同一融合判别跳转 POP_JUMP→28，无独立 merge），但超出本批次体量，留证待下轮 |
| B71 | fin_break break→pass、fin_continue 幻影 elif 未封闭 | 见上 1/2 条；判据面已收敛至 W11-A 认领分支，探针脚本留存 |

## 合规红线
- BOM：region_analyzer.py / region_ast_generator.py 前 3 字节 efbbbf（每次编辑后校验，最终 ✅）。
- 插桩残留：grep core/ = R10DBG|_probe_r|_patch_dbg|_R23N20_DEBUG|R9DBG **0 命中** ✅。
- OK 产物：全部经 pycdc.py 重新生成，零手改 ✅。禁 commit ✅（未执行任何 git commit）。

## 最终哨兵读数汇总
| 面 | 读数 | 结论 |
|---|---|---|
| r6_* 基线面（15 文件） | **107/107** | 全 MATCH ✅ |
| _cmp.pyc（第 16 文件） | **7/7** | 全 MATCH ✅ |
| round7 探针 | r7_03 7/7、r7_07 6/7、r7_12 5/8、r7_14 5/9 | 较基线 +4 单元，失败名单与登记面逐位一致 |
| round8 探针 | r8_06 10/10、r8_10 9/12 | 较基线 +3 单元 |
| round10 | r10_14 7/7、r10_16 7/7、n10_01–04 9/9、r10_21 2/4 | B72 封闭面 + 负对照全守；r10_21 与 HEAD 持平 |

本轮净增：**+7 单元**（r7_03×2、r7_07×2、r8_06×1、r8_10×2），零回归。
改动文件：core/cfg/region_analyzer.py、core/cfg/region_ast_generator.py（净增约 +150 行，含三要素注释）。
