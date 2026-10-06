# Round 4 主代理验证报告（Task 4.4）

- 验证执行：主代理（零实现，判据唯一 = `scripts/pyc_verify.py`；RV2 方法学 = 先以当前树 regen 全部 OK.py 再 verify）。
- 验证对象：HEAD = `3eb329d1`（回退拦截整改后）／整改前 `fa9778a5`。
- 驱动脚本：`final_verify_run.py`（regen 0–7 → verify 0–6 + shard7 拆分 → compare×8 → small34 拆两半 → quotation → tests 六套件）+ `verify_driver.py` / `verify7_split.py`；逐命令日志 `final_verify_log.txt`。
- 首跑 860s（发现回退）→ 整改 → 复跑 820s；全部命令 ≤300s（regen 单分片 37.6–80.5s；verify 单分片 18.6–48.4s）。

## §1 验证序六步读数（整改后终读数）

| # | 步骤 | 基线（spec II.6） | 本轮 | 判定 |
|---|------|------|------|------|
| 1 | 34 小测试集 batch（拆两半合并） | 1505/1568、success 1/34 | **1505/1568**、success 1/34，REGRESSIONS=0 IMPROVED=0 | 逐位持平 ✓ |
| 2 | 全量 402（8 片 regen+batch+compare） | 6554/6617（99.05%）、369/402 | **6554/6617、369/402**，8×compare 全部 **REGRESSIONS=0 IMPROVED=0** | 逐位持平 ✓ |
| 3 | quotation.pyc 单验 | 152/153（`change_his_to_forward`） | 152/153，失败单元同一 | 持平 ✓ |
| 4 | tests 六套件 | 277 passed / 2 failed（`test_B01` + `test_BOUNDARY_02`）/ 2 xpassed | 277 passed / 2 failed（同名两测试）/ 2 xpassed | 零新增失败 ✓ |
| 5 | IV.2 门禁自检 | — | 见 §3 | PASS ✓ |
| 6 | 读数汇报 | — | 见 §4 | — |

**分片明细（与基线逐片逐位一致）**：shard0 777/786、shard1 462/469、shard2 537/538、shard3 883/887、shard4 **848/855**、shard5 993/999、shard6 789/801、shard7 1265/1282；合计 **6554/6617**、files failure 33 → success 369/402。

## §2 回退拦截记录（验证序发现 → 整改 → 复验闭环）

1. **首跑回退**：shard4 `site-packages/IQEngine/plugins/plugin_fly_data/__init__.pyc` 基线 success → failure（-1 单元），8 片 compare 中唯一 `REGRESSIONS=1`；全量 6553/6617。
2. **根因**（FIX_R.md §10）：Task 4.2 位2 的 **B109** 守卫只检查**首个**条件求值块（`condition_block|header`）的越体后继，**漏检回边复判块** → 把「无 else 时各出口各自重复的隐式 `RETURN_CONST None`」误判为「共享 else 块」→ 在 `ApiMethodPlugin._on_handle_order` 的 while 循环后凭空补出 `else: return None`（`git diff … __init__OK.py` 证据：+2 行）。
3. **整改（提交 `3eb329d1`）**：判据收紧为「真 loop-else ⟺ 有 break 证据 ∧ **每个**条件求值块（初判 `condition_block|header` + 回边 `back_edge_block`，须 ≥2 个）越体的条件假后继（非 body、非 header、非 break 落点）**恰好各 1 个且收敛于同一块**，且 `else_blocks[-1]` 即该块」；判据仅用同层后继集合 + 区域成员关系（C3 守卫封闭），无名字/偏移阈值/跨层反查/计数上限。实证：`CL.m` `@0→@64`、`@60→@64` 收敛 = 真 else；`_on_handle_order` `@0→@276`、`@258→@272` 互异 = 隐式收尾。
4. **复验**：整改后 `plugin_fly_data/__init__` failure 20/21 → **success 21/21**；`c4_02` **14/14 保持**、`c4_03` 12/13、`c4_04` 10/13 未误伤；新增 `r4b_loop_else` 4/4；全量恢复 6554/6617 且 8 片 compare REGRESSIONS=0。

## §3 IV.2 门禁自检

| 项 | 结果 |
|---|---|
| IMPORT_OK | `core.cfg` 七模块 import 全过 ✓ |
| COMPILE_OK | 全量 compile_error=0（8 片逐片 0；`c4_14` 的 compile_error 已由 B100 修复转 success）✓ |
| BOM | `region_analyzer.py`/`region_ast_generator.py` 首 3 字节 `efbbbf`、计数 1；`pattern_parser.py` 原无 BOM 保持原状 ✓ |
| 插桩 | 本轮新增行 grep `print(|breakpoint(|pdb.|# TODO|# FIXME|# DEBUG|# XXX` → 0 ✓ |
| 禁止前缀 | 本轮新增行 grep `def (_fix_|_merge_|_patch_|_fallback_|_hack_|_workaround_|_temp_)` → 0 ✓ |
| I.4 黑名单 | 新增 `self.` 跨方法状态 0；`start_offset` 阈值比较 0；跨层 `entry in blocks` 0；名字白名单 0；深度/计数上限 **唯一命中 = 删除的 `range(8)`**（硬编码上限被移除，非新增）✓ |
| 落地标记 grep（I.6） | `[B100]` 6 处、`[B101]` 4 处（`region_ast_generator.py`）；`[B102 fix]` 2 处、`[B109` 1 处（`region_analyzer.py`）；`[B103 fix]` 2 处（`pattern_parser.py`）；新方法 `_import_level_from_prefix`（`:11256` 邻域）在树 ✓ |
| 影响面 | 全量 regen 后 8 片 compare IMPROVED=0、REGRESSIONS=0，MATCH 面产物零漂移（含整改前唯一漂移文件已复原）✓ |

## §4 轮门禁与读数汇报

- **本轮封闭破口**：**B100**（relative_import 层级丢失 → 产物非法；`c4_14` 0/0 compile_error → **5/5 success**）+ **B101**（star_import 丢失；`c4_15` 5/7 → **7/7**）+ **B102**（except\* 多 handler/else/finally 错构；`n4_05` 2/3 → **3/3**、`c4_03` 11/13 → **12/13**）+ **B109**（while-else 体末 break 分支；`c4_02` 13/14 → **14/14**）+ **B103 部分**（match 守卫极性；`c4_04` 8/13 → **10/13**）。轮门禁（≥1）远超满足。
- **站桩回归**：6 面 WORSE=0（round2face 234/251、probe42 172/196、round1face 417/423、residual 417/446、oldface 664/692、quotation 152/153）；全量 402 与 34 集终验逐位持平。
- **合规**：Task 4.3 复核终审**通过**（I.4 五项 / I.5 七前缀 / I.7 注释六项+C 条款与代码一致 / BOM 单头 / 插桩 0 / 零手改 `*OK.py`）；新变体攻击误伤 0（level=0 绝对导入、非 star 导入、普通 except、真 guard、普通 while/for-else 逐位不变）。
- **台账同步（强制，II.7 #7）**：B100–B113 确证后须同步 wiki 台账 §5 形式层计数；本项统一于 Round 10 Task 10.2 落位（前 9 轮不改 wiki，按纪律）。
- **移交清单**（如实登记，供 Round 5+）：
  - **未封闭 B 项（本轮登记）**：B103 残余（`e04_mapping` 跨 case 头越界收集 / `e05_class_kw` case 拆区 / `e06_or_guard` or+guard 链错构）、B104（chained_compare 链尾操作数损坏/宿主蒸发）、B105（walrus 条件/实参位丢失）、B106（star_args 多星/非尾星重排，根因疑在 `ast_generator_v2.py` 顺序固化）、B107（multi_target 链式/解包值丢失）、B108（try-finally-only finally 复制 / `del`→`pass`）、B110（多上下文 with 多余 `return None`）、B111（局部类方法 decorator→元组）、B112（async `yield await` / async 推导式）。
  - **B113**：复核**驳回**「CPython peephole 不可逆」证伪降级，**维持破口**（现产物引用未绑定 a/b；等价源可逐字节复现原字节码）。
  - **沿袭**：round2 遗留 B87 残余/B88 残余/B93/B94/B97、B96（async 推导式）、round3 移交 B98/B99 残余/B44/B1b 五单元。
- **沙箱/环境事件**：首跑 shard4 回退（见 §2）已按回退拦截条款闭环；无超时事件。

**终判：验证序六步全过，8 片 REGRESSIONS=0，Round 4 验证通过。**