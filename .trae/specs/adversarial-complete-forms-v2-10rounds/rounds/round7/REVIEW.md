# Round 7 对抗评审 · Task 7.1 交付
## 已封闭守卫族与已复审破口全量深度外推重放（守卫判据面重攻击）

- 规范：`adversarial-complete-forms-v2-10rounds`（spec.md / tasks.md / checklist.md）
- 评审角色：评审工程师子代理（只读 core/ 零修改 + 探针构建 + 攻击驱动 + 报告 + 破口登记）
- 基准快照：HEAD = `76765985`（round6 注释合规批次后树；round7 开工时 `git status --porcelain core/` = 空）
- 本轮性质：**纯攻击**（零 core 修改 / 零 git 提交 / 零 git add / 零回滚）
- 证据前缀：`r7v7_*`（`rounds/round7/`）；探针前缀：`r7v7_*`（攻击）/ `n7v7_*`（负对照）（`test_repros/round7/`，禁用既有 `r7_*/n7_*/rv7_*` 前缀，零覆盖 61 个 tracked 既有文件）
- 判据工具：`scripts/pyc_verify.py`（ruler = pylingual `equivalence_check.py::compare_pyc`，唯一判据）
- 攻击总读数：**attack 114/122 单元（41 文件）· 负对照 18/18（6 文件全 MATCH）**；新破口 **B117–B120**（4 项，均「已定位」）

---

## §0 三态终判预备结论（II.3 口径）

| 维度 | 结论 |
|------|------|
| B2 If×continue 守卫族 | **破口**：2 项（B117 else 臂 continue 深层漏接 / B118 then=continue·else=break 出口边丢失）；适用形态变体 6 探针全过（无感成立面）；边界外 break/return 无误吞 |
| B3 Loop 共享尾守卫族 | **完备（本轮攻击面内）**：12 攻击探针 37/37 全过——深层变体（≥3、try/类/嵌套循环宿主）+ 边界外（f1 显式 continue 不被过吞、真 for/while-else 不被过吞、共享尾调用副作用恰好一次）+ 组合；**负对照 2/2 保持 MATCH** |
| B4 孤儿子守卫族 | **破口**：2 项（B119 空 try 体+非空 finally 体重复发射（两深度皆破）/ B120 for-else×嵌套 if/else×循环后共享 return 深度 3 误归属）；合法嵌套子区域无误释放（b01 过）、R21 handler 返回后继认领外推过（b02/b03 过） |
| 站桩回归（6 面） | **WORSE = 0**，六面读数与 Round 6 终态逐位一致 |
| 合规审计（I.4/I.5/BOM/插桩/在途变更） | 新增违反 **0**；core/ 干净；BOM 单头（analyzer/generator）；存量黑名单项全部登记（§1） |
| 前六轮新封闭面重放 | 与站桩 6 面同一读数，逐位持平（§2/§4） |

**一句话**：三大守卫族经三方向重攻击后，B3 族在本轮攻击面内守卫封闭成立；B2/B4 族暴露 **4 个守卫缺口型新破口（B117–B120，均非窄门控反向破口——过吞面 b01/b02/b03/b01/b02/c01/c02 全过）**，其中 2 项为深层 onset（C2 深浅不一致确证）、2 项为纯形态缺陷（深度 1 即破）；站桩零回退，合规零新增。

---

## §1 合规审计表（基准 HEAD `76765985`，纯攻击 → 新增应 0）

| # | 审计项 | 结果 | 证据 / 锚点 |
|---|--------|------|------------|
| 1 | `git status --porcelain core/` | **空 ✓** | 本轮零 core 改动；工作树仅有 7 个 `test_repros/round2/*OK.py` regen 副作用 M（见 #6）+ 本轮新增 untracked 产物 |
| 2 | BOM 单头检查 | **analyzer/generator 单头 ✓；code_generator 存量无 BOM（如实登记）** | `region_analyzer.py` head3=`efbbbf` BOMcount=1；`region_ast_generator.py` head3=`efbbbf` BOMcount=1；`code_generator.py` head3=`222222`（`###` 注释头）BOMcount=0——与 HEAD 逐字节一致（core/ 干净），沿袭存量状态非本轮引入，登记待主代理裁定 |
| 3 | I.5 七前缀方法（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`） | **存量 3，新增 0** | `region_ast_generator.py:20231 _merge_block_is_then_exclusive`、`:41403 _merge_block_is_loop_back_edge`（round6 已登记之存量谓词）；**补录** `parsers/ast_builder.py:30213 _fallback_build`（沿袭存量，parsers/ 本轮零改动；round6 审计口径限 core/cfg 未列） |
| 4a | I.4 黑名单·文件名/函数名白名单 | **新增 0（存量均为编译器合成名判定）** | `region_ast_generator.py:2057/2062 func_name == '<module>'`、`:2339/:2437 '<lambda>'`、`:9835/:36598 co_name == '<module>'`——尖括号编译器合成名（同 `<listcomp>` 族，非用户标识符白名单） |
| 4b | I.4 黑名单·start_offset 魔法阈值 | **存量** | `region_ast_generator.py:24732 b.start_offset in (192,584)`（`R7_DEBUG_IFGEN` 调试门控，行号自 round6 的 :24616 漂移 +116）；`structured_analyzer.py:7937/7952/7970 start_offset == 0`（legacy 判定） |
| 4c | I.4 黑名单·跨层 `X.entry in Y.blocks` 反查 | **存量** | `region_ast_generator.py:1451,1470,1495,1512,21433,27771,28355,30035,34913`；`region_analyzer.py:25525,25527,31123` |
| 4d | I.4 黑名单·新增 self 跨方法状态 | **新增 0** | 本轮零 core 改动 |
| 4e | I.4 黑名单·硬编码深度/计数上限 | **存量** | `region_analyzer.py:2663(max_depth=15),2822/2827(max_depth=3),7049(_depth>10),7884(depth>16)`；`region_ast_generator.py:15858(_ft3_depth>8),31120(max_depth=6)` |
| 5 | 插桩残留 | **存量，均 env-gated** | `region_ast_generator.py` 16 处 environ 门控（`R7_DEBUG_IFGEN`×2 :24732/24770、`R30_13_DEBUG` :40234、`R23N6_DEBUG2/5/4` :52108/52865/55631、`R16_DEBUG`×2 :53013/53049 等）；`ast_generator_v2.py:23202/23340`（`PYCDC_DEBUG`）；`opcode_feature_detector.py:72`（`PYTHON_VERSION_OVERRIDE`，合法） |
| 6 | `*OK.py` 手改检查 | **未手改 ✓** | 7 个 tracked `M` 系**本轮站桩 regen 副作用**（r7v7_station.py 先 regen 再 verify 口径所必需），文件名单与 round6 登记逐位一致：`test_repros/round2/c02_class_ifOK.py`、`c03_class_forOK.py`、`m04_module_tryOK.py`、`m09_module_deep_crossOK.py`、`nx01_shallow_hostsOK.py`、`x03_while_deep_hostsOK.py`、`x10_handler_hostsOK.py`。依纪律**如实登记、未还原**（主代理处理） |

**合规审计新增违反数 = 0**（code_generator 无 BOM 与 `_fallback_build` 为存量状态补录，非新增违反）。

---

## §2 站桩回归读数表（6 面，单进程串行，RV2 = 先 regen 再 verify）

驱动：`rounds/round7/r7v7_station.py`（沿用主代理就位版本）；
对照：`rounds/round7/r7v7_compare_regress.py`（r6v6_compare_regress.py 副本，前缀 r7v7_）→ `r7v7_station_regress_compare.json`。

| 面 | 本轮读数 | Round 6 终态基线 | 对照结论 | 证据 JSON |
|----|---------|-----------------|---------|-----------|
| round2face | **234/251** | 234/251 | same=45 / improved=0 / **WORSE=0** | `r7v7_regress_round2face.json` |
| probe42 | **176/196** | 176/196 | same=28 / improved=14 / **WORSE=0** | `r7v7_regress_probe42.json` |
| round1face | **417/423** | 417/423 | same=24 / improved=0 / **WORSE=0** | `r7v7_full_round1face.json` |
| residual | **417/446** | 417/446 | same=62 / improved=10 / **WORSE=0** | `r7v7_full_residual_a.json`+`_b.json` |
| oldface | **664/692** | 664/692 | same=55 / improved=4 / **WORSE=0** | `r7v7_full_oldface_a.json`+`_b.json` |
| quotation | **152/153** | 152/153 | 唯一失败 `change_his_to_forward` 基线一致 | `r7v7_quotation.json` |

- **六面 WORSE 合计 = 0**；六面读数与 Round 6 终态**逐位一致**，无回退。
- improved 计数来自 round2/round1 基线 JSON 为**旧快照**（round5/6 已登记同批 improved 名单，非本轮改动所致——本轮 core/ 零改动）。

---

## §3 守卫族逐族攻击表（B2/B3/B4 × 三方向）

协议：每族 ≥10 最小复现（深度 ≥3 / 交叉组合）+ ≥2 MATCH 负对照（浅层朴素形态）；宿主条件一律非常量（无 `if 1:`/`while 1:+break`）；每探针含 shallow（深度 1）与 deep（深度 ≥3）**同形态孪生函数**，实测判据 = **深层与浅层产物同过 verify（字节等价）⇒ 结构一致**；深层失败而浅层孪生通过 = C2 深浅不一致 = 破口证据。生成器：`test_repros/round7/gen_probes_r7v7.py`；驱动：`rounds/round7/r7v7_attack.py`（py_compile → pycdc regen → batch + 逐文件 single → `r7v7_probe_index.json`/`r7v7_probe_results.json`/`r7v7_probe_detail.json`）。补充证据：`r7v7_struct_cmp.py` → `r7v7_struct_cmp.json`（逐函数源码↔产物 AST 比对：42/96 equal、54 unequal 全部为「体尾冗余 continue 补发」类**字节等价重排**（负对照 n2a 亦然），不构成深浅不对称，不作破口判据——判据唯一性归 pyc_verify）。

### §3.1 B2 If×continue 守卫族（13 攻击 + 2 bracket + 2 负对照 = **38/40 + 5/8**；负对照 6/6）

守卫落地锚点（现行行号，spec III.5 原锚 :10289/:10423-10427/:10455-10579 因 round6 docstring 批次漂移）：`_block_is_continue_target` :12954、`_block_is_pure_continue` :13029、循环头 break 条件路径 continue 判据 `_loop_handle_no_exit_successors` :13089-13130（`_then_is_pure_cont` :13102 / `_else_is_pure_cont` :13108）、条件取反×内层 if-continue 重组 `_5_post_extra` :21694-21715（消费 :22070）、merge==back_edge 无条件 Continue 兄弟追加 :21807-21845、B66 continue 链头 :3414。

| 方向 | 探针 | 形态 | 读数 | 深浅一致判定 |
|------|------|------|------|------------|
| (a) 适用形态变体 | r7v7_b2a01 | for→if→if→if: continue（深度 3） | 3/3 ✓ | 一致 |
| (a) | r7v7_b2a02 | while→try→for→if: continue（try 体宿主） | 3/3 ✓ | 一致 |
| (a) | r7v7_b2a03 | 类方法宿主 for→if→if: continue+else | 4/4 ✓ | 一致 |
| (a) | r7v7_b2a04 | elif 链分支 = continue（深度 3） | 3/3 ✓ | 一致 |
| (a) | r7v7_b2a05 | 非纯 continue（臂尾带语句，深度 3） | 3/3 ✓ | 一致 |
| (a) | r7v7_b2a06 | 嵌套双循环各自 continue（深度 3） | 3/3 ✓ | 一致 |
| (b) 边界外 | r7v7_b2b01 | if c: break（深度 3）——Break 不得误吞为 Continue | 3/3 ✓ | 一致（无误吞） |
| (b) | r7v7_b2b02 | if c: return X（深度 3） | 3/3 ✓ | 一致（无误吞） |
| (b) | r7v7_b2b03 | 条件取反+内层 if-continue **无 else**（重组守卫边界外，深度 3） | 3/3 ✓ | 一致（守卫不误触发） |
| (b) | r7v7_b2b04 | **else 分支 continue**（深度 1 ✓ / 深度 3 ✗） | 2/3 ✗ | **不一致 → B117** |
| (b) bracket | r7v7_x_b2b04_d2 | else-continue 深度 2 | 1/2 ✗ | **B117 深度 onset = 2**（最小复现） |
| (c) 组合 | r7v7_b2c01 | If×continue + Loop 共享尾同现（深度 3） | 3/3 ✓ | 一致 |
| (c) | r7v7_b2c02 | then/else 双 continue（两分支均指回边） | 3/3 ✓ | 一致 |
| (c) | r7v7_b2c03 | **continue 与 break 同 if/else**（深度 1 ✗） | 2/3 ✗ | **纯形态破 → B118**（bracket x_b2c03_pure 1/2 ✗ 确证纯形态） |
| 负对照 | n7v7_b2n01 / n7v7_b2n02 | 浅层朴素 if-continue / if-else-continue / 非纯 continue | 6/6 ✓ | MATCH 保持 |

### §3.2 B3 Loop 共享尾守卫族（12 攻击 + 2 负对照 = **37/37**；负对照 6/6）

守卫落地锚点（现行行号）：`_is_loop_tail_convergence_block`（显式 Continue 冗余抑制·前驱 ≥2 判据）region_ast_generator.py:12963-13027；W14-C 共享尾归属 region_analyzer.py:21659-21680；B109 真 loop-else 守卫 region_analyzer.py:4864-4911（round4 整改 `3eb329d1` 形态）；`_find_loop_else` :5722、`_loop_else_nop_marker` :5630、`_clamp_loop_else_to_enclosing_try` :5585。

| 方向 | 探针 | 形态 | 读数 | 深浅一致判定 |
|------|------|------|------|------------|
| (a) 适用形态变体 | r7v7_b3a01 | for: if c: S 共享尾 f2 形态（深度 3，双前驱回边） | 3/3 ✓ | 一致（冗余抑制正确） |
| (a) | r7v7_b3a02 | while 宿主共享尾（深度 3） | 3/3 ✓ | 一致 |
| (a) | r7v7_b3a03 | try 体宿主共享尾（深度 3） | 3/3 ✓ | 一致 |
| (a) | r7v7_b3a04 | 类方法宿主共享尾 | 4/4 ✓ | 一致 |
| (a) | r7v7_b3a05 | 嵌套双循环各自共享尾（深度 3） | 3/3 ✓ | 一致 |
| (a) | r7v7_b3a06 | 共享尾含调用副作用（sink.append 恰好一次） | 3/3 ✓ | 一致（无漏发/重发） |
| (b) 边界外 | r7v7_b3b01 | 显式 continue（f1·单前驱）——汇合抑制守卫不得误吞 | 3/3 ✓ | 一致（显式 continue 存活，无误吞） |
| (b) | r7v7_b3b02 | 真 for-else（break 证据，深度 3） | 3/3 ✓ | 一致（B109 守卫不误杀） |
| (b) | r7v7_b3b03 | 真 while-else（深度 3） | 3/3 ✓ | 一致 |
| (c) 组合 | r7v7_b3c01 | 共享尾 + If×continue 同循环 | 3/3 ✓ | 一致 |
| (c) | r7v7_b3c02 | loop-else + 共享尾 + continue 三守卫同现 | 3/3 ✓ | 一致（互不打架） |
| (c) | r7v7_b3c03 | 跨层共享尾逐层汇合（深度 4） | 3/3 ✓ | 一致 |
| 负对照 | n7v7_b3n01 / n7v7_b3n02 | 浅层共享尾 / 浅层 for-else·while-else | 6/6 ✓ | MATCH 保持 |

**B3 族小结**：本轮三方向攻击面内无新破口；守卫呈「恢复无感」而非窄门控（f1 显式 continue 与真 loop-else 两个最易被过吞的边界外形态均存活）。此为**本轮覆盖面结论**，非全量完备宣告（II.7 自查见 §7）。

### §3.3 B4 孤儿子守卫族（12 攻击 + 2 bracket + 2 负对照 = **34/37 + 5/8**；负对照 6/6）

守卫落地锚点（现行行号）：孤儿块释放·顶级祖先检查 region_ast_generator.py:1717-1800（te046 修复形态）；R09 空/不可抛 try 体孤儿帧识别 region_analyzer.py:1460（识别侧）；R21 handler 返回后继认领 region_analyzer.py:9010-9046（spec 原 :9017-9019 漂移带）。

| 方向 | 探针 | 形态 | 读数 | 深浅一致判定 |
|------|------|------|------|------------|
| (a) 适用形态变体 | r7v7_b4a01 | 嵌套 if/else 汇合块链（深度 4） | 3/3 ✓ | 一致 |
| (a) | r7v7_b4a02 | try 内 try 内循环 + finally（深度 3） | 3/3 ✓ | 一致 |
| (a) | r7v7_b4a03 | **空 try 体 + 非空 finally**（if 宿主 / while→if→try 深度 3，**两深度皆 ✗**） | 1/3 ✗ | **纯形态破 → B119**（bracket x_b4a03_pure 1/2 ✗ 确证纯形态） |
| (a) | r7v7_b4a04 | 类方法宿主 try/finally + 嵌套 if 汇合 | 4/4 ✓ | 一致 |
| (a) | r7v7_b4a05 | with 体宿主 with→if→for→if（深度 3） | 3/3 ✓ | 一致 |
| (a) | r7v7_b4a06 | try 体仅表达式 + finally（深度 3） | 3/3 ✓ | 一致 |
| (b) 边界外 | r7v7_b4b01 | 合法嵌套子区域块（深度 4）——不得误释放/幻影语句 | 3/3 ✓ | 一致（无误释放） |
| (b) | r7v7_b4b02 | try/except 后 return（R21 认领形态，深度 3） | 3/3 ✓ | 一致 |
| (b) | r7v7_b4b03 | try/except/else 三段（深度 3） | 3/3 ✓ | 一致 |
| (c) 组合 | r7v7_b4c01 | 孤儿汇合块 + Loop 共享尾（B4×B3） | 3/3 ✓ | 一致 |
| (c) | r7v7_b4c02 | 孤儿 finally 帧 + If×continue（B4×B2） | 3/3 ✓ | 一致 |
| (c) | r7v7_b4c03 | **孤儿汇合块 + loop-else（B4×B3，深度 1 ✓ / 深度 3 ✗）** | 2/3 ✗ | **不一致 → B120**（bracket x_b4c03_d2 深度 2 = 2/2 ✓ ⇒ 深度 3 onset） |
| 负对照 | n7v7_b4n01 / n7v7_b4n02 | 浅层 try/finally·for-else / 浅层 try-except-return | 6/6 ✓ | MATCH 保持 |

### §3.4 攻击覆盖矩阵（守卫族 × 三方向）

| 守卫族 | (a) 变体 | (b) 边界外 | (c) 组合 | 负对照 | 族读数 | 结论 |
|--------|---------|-----------|---------|--------|--------|------|
| B2 If×continue | 6/6 一致 | 3/4 一致（b04 ✗→B117） | 2/3 一致（c03 ✗→B118） | 2/2 MATCH | 38/40（+bracket 5/8） | **破口 ×2** |
| B3 Loop 共享尾 | 6/6 一致 | 3/3 一致（无误吞/无漏接） | 3/3 一致 | 2/2 MATCH | 37/37 | 完备（本轮面内） |
| B4 孤儿子 | 5/6 一致（a03 ✗→B119） | 3/3 一致 | 2/3 一致（c03 ✗→B120） | 2/2 MATCH | 34/37（+bracket 5/8） | **破口 ×2** |

---

## §4 前六轮新封闭面重放结论

- 重放载体 = 站桩 6 面（§2）：round2face（round2 攻击面）、probe42（B42 面）、round1face（round1 哨兵面）、residual（残余破口登记面）、oldface（round3 旧形态面）、quotation——六面读数与 Round 6 终态**逐位一致**，即 B1b/B6–B40/B45/B54/B55/B66–B68 等已封闭面与既有残余面在本轮（core 零改动）下**零位移**。
- 守卫族落地锚点 grep 复核：B2/B3/B4 全部落地代码在树（§3 各族锚点表；spec III.5 原行号漂移 +110～+125 行系 round6 docstring 批次所致，机制未变——round6 提交 `76765985` 为纯 docstring/AST_EQUAL 批次）。
- 残余破口承接名单（III.5）未被本轮攻击面扰动：residual 面 417/446 与基线持平。

---

## §5 破口登记（自 B117 续接；wiki §8.3 状态机 = 已定位）

> **编号勘误**：初稿误用 B77–B80（与 round2 承接 designated B77–B83 及既有台账冲突），已按台账最高号 B116 续接重编号为 B117–B120。

| 编号 | 锚点（file:line） | 机制说明 | 违反条款 | 最小复现 | 当前 verify 读数 | 状态 |
|------|------------------|---------|---------|---------|----------------|------|
| **B117** | `core/cfg/region_ast_generator.py:13089-13130`（else-continue 守卫唯一落点 = 循环**头** break 条件路径 `_loop_handle_no_exit_successors` 的 `_then_is_pure_cont`/:13102 `_else_is_pure_cont`/:13108）+ `:21807-21845`（merge==back_edge 时 Continue 兄弟追加，无「if 区域是否宿主尾区域」守卫） | 体内 if 的 else 臂 = 纯 continue 回边块（POP_JUMP_IF_FALSE → 单前驱 JUMP_BACKWARD 块）时，生成层将 else-continue **降级重排**为「then 臂尾补 Continue + else 臂删除、后继语句并入 then」。该重排仅当 if 区域 = 循环体尾区域时保语义；当 if 之上还有宿主 if 且宿主 if 后有顺序后继（如 `if flag: if x>0: acc+=x else: continue; acc+=1`）时，false 边落到宿主后继 `acc+=1` 而非回边 → continue 语义丢失。深度 1 孪生（if 即循环体唯一/尾区域）同重排但语义等价 → verify 通过；深度 ≥2 即破（bracket 确证 onset=2）。字节码证据：原 pyc 含专用 continue 块（JUMP_BACKWARD@66），OK 重编译后该块消失、false 边直指汇合块 | **C2**（深度 1 通过 / 深度 ≥2 失败 = 深浅行为不一致）+ **C3**（if 区域 false 边指向区域外回边块，属「continue 目标跨区域」非局部引用，无显式认领守卫） | `test_repros/round7/r7v7_x_b2b04_d2.py`（深度 2）；`r7v7_b2b04.py::b2b04_deep`（深度 3） | r7v7_b2b04 = 2/3、r7v7_x_b2b04_d2 = 1/2 | 已定位 |
| **B118** | `core/cfg/region_ast_generator.py` `_generate_if`（:14356 方法族）else 臂发射 + 循环出口块归属（`_is_jump_to_continue` :12839、`_loop_handle_exit_successors` 一带；Break 发射守卫只认领 then 路径） | `if c: continue else: break`（if/else 为循环体全部语句）编译后 **else→break 边与 FOR_ITER 自然出口共享同一出口块**（出口块 = POP_TOP + 循环外代码）。if 生成只发 then=[Continue]；else 臂（break 边）因目标 = 循环出口块（区域外）被丢弃，且无守卫补发显式 `break`。重编译后 false 边落到体尾**隐式 JUMP_BACKWARD**（原出口块 POP_TOP 消失）→ break 语义变「继续迭代」（耗尽迭代器）。字节码证据：原 `28 POP_TOP` vs OK 重编译 `28 JUMP_BACKWARD to 10`。深度 3 变体（b2c03_deep：break 块非循环出口）反而通过 → 破口形态特指「else-break 出口块 == 循环出口汇合块」 | **C3**（else 目标 = 循环出口块 = 跨区域非局部引用「fall-through 是别区域 entry」类，无显式守卫认领 → break 边静默丢失） | `test_repros/round7/r7v7_x_b2c03_pure.py`（纯形态深度 1）；`r7v7_b2c03.py::b2c03_shallow` | r7v7_b2c03 = 2/3、r7v7_x_b2c03_pure = 1/2 | 已定位 |
| **B119** | `core/cfg/region_ast_generator.py:29361 _generate_try`（空 try 体发射分支）+ `core/cfg/region_analyzer.py:1460`（R09 孤儿 finally 帧识别——**仅识别侧**，发射侧无对应守卫） | `try: pass finally: <body>`（try 体零指令）时，finally 体语句被**同时**重建进 try 体与 finally 体（重复发射）→ 重编译出两份 finally 体指令。字节码证据：原 try 体无用户指令（仅异常表），OK 重编译 try 体含 `LOAD_FAST/UNARY_NOT/STORE` 全套。与 B63（空 try/fin 后**尾随段**）、B69（**空** finally 吞尾随 return）机制不同：本形态 = 空 try 体 + **非空 finally 体** 的**体重复**，III.5 残余名单未覆盖 | **原则 2 每块唯一归属**（I.1；同一 finally 体块被消费/发射两次 = C1 局部消费被破坏的发射侧表现） | `test_repros/round7/r7v7_x_b4a03_pure.py`（纯形态）；`r7v7_b4a03.py`（if 宿主与 while→if→try 深度 3，两深度皆破） | r7v7_b4a03 = 1/3、r7v7_x_b4a03_pure = 1/2 | 已定位 |
| **B120** | `core/cfg/region_ast_generator.py:1717-1800`（孤儿块释放·顶级祖先检查）× `core/cfg/region_analyzer.py:4864-4911`（B109 真 loop-else 守卫）组合面；if 条件合并逻辑（:21849 注释所指 L 系合并路径） | for-else × 嵌套 if/else(break) × 循环后共享 return（深度 3）：循环出口与宿主 if false 边的**共享后继 `return acc`**（非孤儿、有顶级祖先）被误归属进宿主 `if flag:` 臂体（OK 中 `return acc` 缩进至 if 体末、函数级 return 消失）→ flag=false 路径语义由 `return acc` 变隐式 `return None`。伴随症状：兄弟 if 被合并 elif 链 + 两臂幻影 continue（同 B117 降级机制，深度 2 时该重排字节等价故通过）。深度 bracket：深度 2 孪生 x_b4c03_d2 = 2/2 ✓，深度 3 即破 ⇒ **C2 深浅不一致确证** | **C2**（深度 2 通过 / 深度 3 失败）+ **原则 3 嵌套即抽象节点**（I.1：宿主区域展开吞并父级后继语句） | `test_repros/round7/r7v7_b4c03.py::b4c03_deep` | r7v7_b4c03 = 2/3（x_b4c03_d2 = 2/2 ✓ 为边界负对照） | 已定位 |

**新破口计数 = 4（B117–B120），全部「已定位」**。无「过度守卫（窄门控反向破口）」：过吞敏感面（b2b01 break / b2b02 return / b2b03 无 else 重组 / b3b01 显式 continue / b3b02·b3b03 真 loop-else / b4b01 合法嵌套）6/6 全过——守卫判据未见 I.4「以少发射换全绿」变体。

---

## §6 结论与移交

### 终判

| 项 | 判定 |
|----|------|
| 本轮门禁（≥1 破口登记 或 ≥1 读数改善） | **达成**（新破口 4 项 B117–B120） |
| 站桩回归 | 6 面全部持平，WORSE=0，**通过** |
| 合规审计 | 新增违反 0，**通过**（2 项存量补录登记） |
| 建议 | **进入 Task 7.2 修复批**：B117/B118/B120 按 I.3 推论封闭守卫恢复无感（判据仅取 I.4 白名单：块末 opcode / 后继前驱集合 / 区域成员关系——如「if 区域 false/else 边目标是否为当前循环 back_edge/出口块」「if 区域是否宿主尾区域」均为同层结构事实）；B119 在 `_generate_try` 空 try 体分支保持空体（发 `pass`）实现 finally 体唯一归属。**禁止**窄门控/个案补丁（I.4 黑名单「以少发射换全绿」变体，打回项）；修复后 B117–B120 最小复现须转 MATCH 且 §3 全部负对照与 bracket 正例（x_b4c03_d2 等）保持 MATCH |

### 交付物清单

| 交付物 | 路径 |
|--------|------|
| 本报告 | `rounds/round7/REVIEW.md` |
| 攻击驱动 / 生成器 | `rounds/round7/r7v7_attack.py`、`test_repros/round7/gen_probes_r7v7.py` |
| 探针三件套 | `test_repros/round7/r7v7_*`（41 攻击）+ `n7v7_*`（6 负对照）× `.py/.pyc/*OK.py` |
| 探针证据 | `r7v7_probe_index.json` / `r7v7_probe_results.json` / `r7v7_probe_detail.json` / `r7v7_struct_cmp.py`+`.json` |
| 站桩证据 | `r7v7_station.py`（主代理就位）、`r7v7_quotation.json`、`r7v7_regress_round2face.json`（主代理先跑两面，本轮复核一致）、`r7v7_regress_probe42.json`、`r7v7_full_round1face.json`、`r7v7_full_residual_a/b.json`、`r7v7_full_oldface_a/b.json`、`r7v7_compare_regress.py`、`r7v7_station_regress_compare.json` |

**未触碰**：`core/` 全部；`rounds/round1..6` 全部既有文件；`test_repros/round7/` 既有 61 个 tracked 文件（r7_*/n7_*/rv7_*）；任何 `*OK.py`（除站桩 regen 副作用 7 个 M 态，已登记未还原）。

---

## §7 II.7 十三条误解自查（宣告前强制自检）

| # | 误解 | 本轮是否触犯 | 说明 |
|---|------|------------|------|
| 1 | 循环论证分母 | 否 | 攻击分母 = 探针单元（源码构成），非 `RegionType` 枚举/实现自身 |
| 2 | 有过就算 | 否 | B3 族「完备」结论限定本轮三方向攻击面并逐探针列读数；失败项逐一定位不略过 |
| 3 | 语料证据口径 | 否 | 探针为定向构造（守卫判据三方向），非语料抽样 |
| 4 | 无限分母 | 否 | 探针集封闭（47 文件），不随深度/组合膨胀计分 |
| 5 | 节点词汇当完备 | 否 | 判据 = pyc_verify 字节等价 + 深浅孪生对照，非 AST 节点词表 |
| 6 | 浅层测试当无感证明 | 否 | 每探针强制深度 ≥3 deep 孪生；负对照浅层仅作 MATCH 锚；B117/B120 用深度 bracket（2/3）确证 onset |
| 7 | 门禁读数当完备性 | 否 | 站桩 6 面仅作回归旁证；docstring 标称通过率未采信 |
| 8 | 顶层构造粗清单 | 否 | 攻击到守卫判据面（:13089-13130/:21807/:1717-1800/:4864-4911 行级锚点 + 字节码逐块 diff） |
| 9 | 识别率当完备性 | 否 | 结论以 C1/C2/C3 不变式归属表达 |
| 10 | 维度互替 | 否 | 站桩（字节等价回归）/ 守卫封闭（不变式）/ 合规（I.4/I.5）三维独立呈报 |
| 11 | 改工具不改方法 | 否 | 本轮零 core/零工具改动；判据唯一 = scripts/pyc_verify.py 未动 |
| 12 | 错误检测标准 | 否 | 未涉 except* 标记（3.11 CHECK_EG_MATCH/PREP_RERAISE_STAR 口径未混淆） |
| 13 | 语料上限当能力上限 | 否 | 破口登记未以「语料未见」作封闭依据；B3 完备结论限定攻击面范围如实声明 |

**自查结论：未触犯 II.7 任一条。**
