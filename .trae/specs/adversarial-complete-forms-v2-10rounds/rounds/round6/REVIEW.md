# Round 6 对抗评审 · Task 6.1 交付
## `_identify_*` 十族方法注释合规与算法一致性审计

- 规范：`adversarial-complete-forms-v2-10rounds`（spec.md / tasks.md / checklist.md）
- 评审角色：评审工程师子代理（只读审计 + 探针构建 + 报告 + 打回登记）
- 基准快照：HEAD = `326a515b3f32bfb121a039c201e521f1816d492c`
- 本轮性质：**纯审计**（零实现 / 零 core 修改 / 零 git 提交 / 零 git add / TCP 零回滚）
- 证据前缀：`r6v6_*`（`rounds/round6/`）；探针前缀：`r6v6_*`（`test_repros/round6/`）
- 判据工具：`scripts/pyc_verify.py`（ruler = pylingual `equivalence_check.py::compare_pyc`）

---

## §0 三态终判预备结论

| 维度 | 结论 |
|------|------|
| 注释合规（I.7 六项 + C 条款） | **打回**：十族识别方法 10/10 **全部打回**（六项齐全，但**均未声明 C1/C2/C3 条款**）；对应生成方法 9 个打回、6 个合规 |
| 算法一致性（注释 ↔ 代码） | 未发现「注释说 A、代码做 B」的实质性矛盾（十族识别方法 Step 清单与代码流程逐段对齐；详见 §3） |
| 站桩回归（6 面） | **WORSE = 0**，全部达标（读数与 Round 5 终态逐位一致） |
| 合规审计（I.4/I.5/BOM/插桩/在途变更） | 新增违反 **0**；core/ 干净；BOM 单头；存量黑名单项已登记（见 §1） |
| 新算法破口 | **无**（本轮未新增 Bn；无绕过既有文件、无覆盖 round5 证据） |

**一句话**：本轮为注释层（I.7）系统性不合规的打回，属**形式层可整改项**，非算法破口；站桩读数零回退，合规面零新增违反。

---

## §1 合规审计表（基准 HEAD `326a515b`，纯审计 → 新增应 0）

| # | 审计项 | 结果 | 证据 / 锚点 |
|---|--------|------|------------|
| 1 | `git status --porcelain core/` | **空 ✓** | 本轮零 core 改动 |
| 2 | BOM 检查 | **单头 ✓** | `core/cfg/region_analyzer.py` head3=`efbbbf` BOMcount=1；`core/cfg/region_ast_generator.py` head3=`efbbbf` BOMcount=1 |
| 3 | I.5 七前缀方法（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`） | **存量 2，非本轮新增** | `region_ast_generator.py:20115 _merge_block_is_then_exclusive`、`:41216 _merge_block_is_loop_back_edge`。语义为**谓词**（返回真/假），非后处理补丁；不命中 `patch_detector.py:28.1` 的 `_merge_{condition,compare,chain}` 规则 |
| 4a | I.4 黑名单·文件名/函数名白名单 | **新增 0** | 未发现 `co_name == '...'` / 目标函数名个案特判（抽查 `region_analyzer.py` / `region_ast_generator.py`） |
| 4b | I.4 黑名单·start_offset 魔法阈值 | **存量** | `region_ast_generator.py:24616 b.start_offset in (192,584)`（`R7_DEBUG_IFGEN` 调试门控）；`structured_analyzer.py` 多处 `start_offset == 0`（legacy 判定） |
| 4c | I.4 黑名单·跨层 `X.entry in Y.blocks` 反查 | **存量** | `region_ast_generator.py:1451,1470,1495,1512,21317,28239,29919,34797`；`region_analyzer.py:25468,25470,31053` |
| 4d | I.4 黑名单·新增 self 跨方法状态 | **新增 0** | 本轮零 core 改动 |
| 4e | I.4 黑名单·硬编码深度/计数上限 | **存量** | `region_analyzer.py:2663(max_depth=15),2822/2827(max_depth=3),7041(_depth>10),7876(depth>16)`；`region_ast_generator.py:15742(_ft3_depth>8),31004(max_depth=6)`；`tests/anti_patch/patch_detector_enhanced.py:358(depth>3)` |
| 5 | 插桩残留 | **存量 19 处，均 env-gated** | 主要 `region_ast_generator.py` ~17 处（`R23N6/R16/R30_13/R7_DEBUG_IFGEN` 等门控）；`ast_generator_v2.py:23202/23340`（`PYCDC_DEBUG`）；`opcode_feature_detector.py:72`（`PYTHON_VERSION_OVERRIDE`，合法） |
| 6 | `*OK.py` 手改检查 | **未手改 ✓** | 全树无手改；`test_repros/round2/` 7 个 `*OK.py` 为 `M` 系 **RV2 强制 regen 副作用**（committed 快照陈旧），非手改，遵守 TCP 零回滚未还原（见下） |

**regen 副作用登记的 7 个 tracked 文件**（`git status` 显示 `M`）：
`test_repros/round2/c02_class_ifOK.py`、`c03_class_forOK.py`、`m04_module_tryOK.py`、`m09_module_deep_crossOK.py`、`nx01_shallow_hostsOK.py`、`x03_while_deep_hostsOK.py`、`x10_handler_hostsOK.py`。
根因：RV2 口径要求「先 regen（`pycdc -o`）再 verify」，HEAD 快照为陈旧 `*OK.py`，regen 后内容更新。**非手改、非本轮实现产物**；依「TCP 零回滚」硬约束未执行 checkout/restore。

**合规审计新增违反数 = 0。**

---

## §2 站桩回归读数表（6 面，单进程串行）

驱动：`rounds/round6/r6v6_station.py`（r5v5_station.py 副本，输出前缀改 `r6v6_`）；
对照：`rounds/round6/r6v6_compare_regress.py` → `r6v6_station_regress_compare.json`。

| 面 | 本轮读数 | Round 5 终态 | 对照结论 | 证据 JSON |
|----|---------|-------------|---------|-----------|
| round2face | **234/251** | 234/251 | same=45 / improved=0 / **WORSE=0** | `r6v6_regress_round2face.json` |
| probe42 | **176/196** | 176/196 | same=28 / improved=14 / **WORSE=0** | `r6v6_regress_probe42.json` |
| round1face | **417/423** | 417/423 | same=24 / improved=0 / **WORSE=0** | `r6v6_full_round1face.json` |
| residual | **417/446** | 417/446 | same=62 / improved=10 / **WORSE=0** | `r6v6_full_residual_a.json`+`_b.json` |
| oldface | **664/692** | 664/692 | same=55 / improved=4 / **WORSE=0** | `r6v6_full_oldface_a.json`+`_b.json` |
| quotation | **152/153** | 152/153 | 唯一失败 `change_his_to_forward` 基线一致 | `r6v6_quotation.json` |

- **六面 WORSE 合计 = 0**；improved 计数来自 round2/round1 基线 JSON 为**旧快照**（非本轮改动）。
- 各面读数与 Round 5 终态**逐位一致**，无回退。

---

## §3 十族逐方法审计表（I.7）

口径：I.7 要求 docstring **六项齐全**（①算法依据 ②归约顺序 ③唯一归属判定 ④嵌套处理 ⑤入口引用语义 ⑥反编译流程）**并注明本方法满足/恢复的 C1/C2/C3 条款**。

### §3.1 十族识别方法（`core/cfg/region_analyzer.py`）

| 族 | 方法 @ 行 | 六项齐全 | C1/C2/C3 条款 | 结论 |
|----|----------|---------|--------------|------|
| conditional | `_identify_conditional_regions` :17936 | ✓ (17948/17990/18001/18029/18052/18070) | **缺**（Step5 内联 `[C1]` :17978，非条款声明） | **打回**（I.7） |
| loop | `_identify_loop_regions` :4171 | ✓ (4177/4209/4218/4240/4250/4258) | **缺** | **打回**（I.7） |
| try_except | `_identify_try_except_regions` :8170 | ✓ (8176/8197/8207/8222/8235/8245) | **缺** | **打回**（I.7） |
| with | `_identify_with_regions` :13260 | ✓ (13266/13313/13323/13340/13352/13360) | **缺** | **打回**（I.7） |
| match | `_identify_match_regions` :13955 | ✓ (13961/13986/13998/14013/14024/14035) | **缺** | **打回**（I.7） |
| assert | `_identify_assert_regions` :16662 | ✓ (16668/16726/16738/16751/16763/16776) | **缺** | **打回**（I.7） |
| chained_compare | `_identify_chained_compare_regions` :17467 | ✓ (17480/17512/17523/17534/17545/17555) | **缺** | **打回**（I.7） |
| ternary | `_identify_ternary_regions` :22524 | ✓ (22535/22580/22596/22619/22630/22640) | **缺** | **打回**（I.7） |
| boolop | `_identify_boolop_regions` :25657 | ✓ (25666/25710/25749/25771/25785/25795) | **缺**（Step5 内联 `[C3]` :25707，非条款声明） | **打回**（I.7） |
| sequence | `_identify_sequence_regions` :30878 | ✓ (30885/30912/30921/30931/30941/30952) | **缺** | **打回**（I.7） |

**共性**：十族识别方法 docstring **六项模板全部齐全**，却**一致**以 `本方法遵循区域归约算法 4 核心原则: 自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口` 收尾——这是 **I.1 四原则**，**不是 I.3 的 C1/C2/C3 条款**。仅 conditional（:17978 内联 `[C1]`）与 boolop（:25707 内联 `[C3]`）各自出现**单条内联标注**，均未形成「C1/C2/C3 条款」完整声明。⇒ 十族识别方法 **10/10 打回**（违反 I.7 末句）。

### §3.2 对应生成方法（`core/cfg/region_ast_generator.py`）

| 族 | 方法 @ 行 | docstring 形态 | 六项 | C 条款 | 结论 |
|----|----------|---------------|------|--------|------|
| try_except | `_generate_try` :29245 | ①–⑥ 显式标号（29336–29361） | ✓ | ✓「C 条款：C1/C2/C3」:29361 | **合规** |
| try_except | `_generate_try_body` :27489 | ①–⑥（27492–27515） | ✓ | ✓:27519 | **合规** |
| try_except | `_generate_handler_body_statements` :31247 | ①–⑥（31250–31270） | ✓ | ✓:31273 | **合规** |
| with | `_generate_with` :33923 | ①–⑥（33926–33948） | ✓ | ✓:33950 | **合规** |
| sequence | `_generate_block_statements` :51287 | ①–⑥（51290–51311） | ✓ | ✓:51313 | **合规** |
| sequence | `_generate_block_statements_body` :51455 | ①–⑥（51458–51477） | ✓ | ✓:51479 | **合规** |
| loop | `_generate_loop` :5061 | 旧格式（输入契约/AST 映射规则/子区域处理/字节码一致性约束）:5064 | ✗ | ✗ | **打回**（I.7） |
| assert | `_generate_assert` :4330 | 旧格式:4332 | ✗ | ✗ | **打回**（I.7） |
| conditional & chained_compare | `_generate_if` :14356 | 旧格式:14357 | ✗ | ✗ | **打回**（I.7） |
| chained_compare | `_generate_value_context_chain_compare_assign` :14767 | 旧格式:14768 | ✗ | ✗ | **打回**（I.7） |
| match | `_generate_match` :35520 | 旧格式:35521 | ✗ | ✗ | **打回**（I.7） |
| boolop | `_generate_boolop` :39176（重入包装） | 三要素（识别条件/归约方式/AST 映射）:39177 | ✗ | ✗ | **打回**（I.7） |
| boolop | `_generate_boolop_impl` :39207 | 旧格式:39208 | ✗ | ✗ | **打回**（I.7） |
| ternary | `_generate_ternary` :41621 | 旧格式:41622 | ✗ | ✗ | **打回**（I.7） |
| sequence | `_generate_basic_region` :50867 | 旧格式:50868 | ✗ | ✗ | **打回**（I.7） |

**审视结论**：合规 docstring 的公认形态 = `_generate_with` 形态（①–⑥ 显式标号 + 独立「C 条款：」行）。旧格式（输入契约/AST 映射规则/子区域处理/字节码一致性约束）虽含"三要素"近义内容，但**不含 I.7 六项标号与 C 条款**，判 **不合规**。

### §3.3 注释 ↔ 代码一致性抽查（未发现实质矛盾）

- 十族识别方法 docstring 的 Step 1..N 清单与其后代码流程**逐段对齐**（loop:4276+、try_except:8283+、with:13391+、match:14046+、assert:16811+、chained_compare:17569+、conditional:18083+、ternary:22660+、boolop:25833+、sequence:30971+）。
- 各方法末尾「测试矩阵通过率 100%（…/…）」为文档标称值，非本轮实测，**不作为完备性判据**（防 II.7「门禁读数当完备性」）。
- 未发现「注释声明 C1/C2/C3 而代码未落地」的反向矛盾——因识别方法**根本未声明 C 条款**（缺项，非错述）。

---

## §4 打回登记表

| 编号 | 对象 | 锚点（file:line） | 违反条款 | 机制 | 修复方向 |
|------|------|------------------|---------|------|---------|
| R6-D1 | 十族识别方法 ×10 | `region_analyzer.py:4171,8170,13260,13955,16662,17467,17936,22524,25657,30878` | **I.7** | docstring 六项齐全但**未注明满足/恢复的 C1/C2/C3 条款**（以 I.1 四原则收尾） | 各方法 docstring 增补「C 条款：C1…/C2…/C3…」声明；conditional/boolop 可由内联 `[C1]`/`[C3]` 升格为完整声明 |
| R6-D2 | `_generate_loop` | `region_ast_generator.py:5064` | **I.7** | 旧格式 docstring，缺六项标号 + C 条款 | 改建为 `_generate_with` 形态（①–⑥ + C 条款） |
| R6-D3 | `_generate_assert` | `region_ast_generator.py:4332` | **I.7** | 同上 | 同上 |
| R6-D4 | `_generate_if` | `region_ast_generator.py:14357` | **I.7** | 同上（conditional/chained_compare 共用） | 同上 |
| R6-D5 | `_generate_value_context_chain_compare_assign` | `region_ast_generator.py:14768` | **I.7** | 同上 | 同上 |
| R6-D6 | `_generate_match` | `region_ast_generator.py:35521` | **I.7** | 同上 | 同上 |
| R6-D7 | `_generate_boolop` | `region_ast_generator.py:39177` | **I.7** | 仅三要素，缺六项 + C 条款（包装方法） | 同上 |
| R6-D8 | `_generate_boolop_impl` | `region_ast_generator.py:39208` | **I.7** | 旧格式，缺六项 + C 条款 | 同上 |
| R6-D9 | `_generate_ternary` | `region_ast_generator.py:41622` | **I.7** | 旧格式，缺六项 + C 条款 | 同上 |
| R6-D10 | `_generate_basic_region` | `region_ast_generator.py:50868` | **I.7** | 旧格式，缺六项 + C 条款 | 同上 |

**打回计数**：识别方法 **10**；生成方法 **9**；合计 **19**。
**合规计数**：生成方法 **6**（`_generate_try` / `_generate_try_body` / `_generate_handler_body_statements` / `_generate_with` / `_generate_block_statements` / `_generate_block_statements_body`）。
**新算法破口 Bn**：**0**（无 C1/C2/C3 不变式破坏证据；无站桩回退）。

> 说明：R6-D1..D10 均为 **I.7 注释合规**层打回（形式层可整改），**不涉及** I.3 不变式破坏；按 II.3 不计入「破口」。

---

## §5 移交清单

| 交付物 | 路径 | 状态 |
|--------|------|------|
| 本报告 | `rounds/round6/REVIEW.md` | 已产出 |
| 站桩驱动（副本，前缀 `r6v6_`） | `rounds/round6/r6v6_station.py` | 已产出（未改动 round5 同名脚本） |
| 回归对照脚本 | `rounds/round6/r6v6_compare_regress.py` | 已产出 |
| 对照结果 | `rounds/round6/r6v6_station_regress_compare.json` | 6 面 WORSE=0 |
| 证据 JSON | `rounds/round6/r6v6_regress_round2face.json`、`r6v6_regress_probe42.json`、`r6v6_full_round1face.json`、`r6v6_full_residual_a.json`+`_b.json`、`r6v6_full_oldface_a.json`+`_b.json`、`r6v6_quotation.json` | 已产出 |

**未触碰**：`rounds/round5/` 全部既有文件（含 `r5v5_*` 证据）；`round6/` 既有 tracked 文件（`final_verify_run.py`/`verify7_split.py`/`verify_driver.py`）；任何 `*OK.py`；`core/`。

**遗留登记**：7 个 `test_repros/round2/*OK.py` 为 RV2 regen 副作用（`M`），未回滚。

---

## §6 II.7 十三条误解自查（宣告前的强制自检）

| # | 误解 | 本轮是否触犯 | 说明 |
|---|------|------------|------|
| 1 | 循环论证分母 | 否 | 未用 `RegionType` 枚举/实现自身当分母 |
| 2 | 有过就算 | 否 | 打回逐方法列锚点，未以"存在即完备"计 |
| 3 | 语料证据口径 | 否 | 站桩仅作**回归**旁证，非完备性判据 |
| 4 | 无限分母 | 否 | 未引入随深度/组合膨胀的分母 |
| 5 | 节点词汇当完备 | 否 | 未以 AST 节点词表判完备 |
| 6 | 浅层测试当无感证明 | 否 | 未以浅层站桩宣告无感成立 |
| 7 | 门禁读数当完备性 | 否 | 明确拒绝 docstring 标称"100%"作判据（§3.3） |
| 8 | 顶层构造粗清单 | 否 | 审计到方法/条款/行号粒度 |
| 9 | 识别率当完备性 | 否 | 未以识别率代替不变式 |
| 10 | 维度互替 | 否 | 注释合规(I.7) / 站桩(字节等价) / 不变式(I.3) 三维独立呈报 |
| 11 | 改工具不改方法 | 否 | 本轮只审计，未改任何判据工具 |
| 12 | 错误检测标准 | 否 | 未涉及 3.11/3.12 except* 标记混淆 |
| 13 | 语料上限当能力上限 | 否 | 未以语料规模主张能力边界 |

**自查结论**：本轮未触犯 II.7 任一条。

---

## 附：简明结论

- 十族识别方法：**合规 0 / 打回 10**（全部因 I.7 缺 C1/C2/C3 条款声明）。
- 对应生成方法：**合规 6 / 打回 9**。
- 合计：**合规 6 / 打回 19**。
- 打回方法名：`_identify_conditional_regions`、`_identify_loop_regions`、`_identify_try_except_regions`、`_identify_with_regions`、`_identify_match_regions`、`_identify_assert_regions`、`_identify_chained_compare_regions`、`_identify_ternary_regions`、`_identify_boolop_regions`、`_identify_sequence_regions`、`_generate_loop`、`_generate_assert`、`_generate_if`、`_generate_value_context_chain_compare_assign`、`_generate_match`、`_generate_boolop`、`_generate_boolop_impl`、`_generate_ternary`、`_generate_basic_region`。
- 站桩 6 面 **WORSE = 0**。
- 合规审计**新增违反 = 0**（core/ 干净、BOM 单头、插桩/黑名单项均为存量）。
- **无新算法破口**（Bn=0）。