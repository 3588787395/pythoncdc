# Round 8 修复报告 FIX_C（位C · match/异常组/推导式/实参序域）

- 修复工程师：位C（Round 8 残余破口清零冲刺）
- 基线：HEAD = 5d5b443c（位A/位B批已合入后树态）
- 判据唯一：`scripts/pyc_verify.py`（RV2 口径 = 先 regen 后 verify single）
- 涉改文件（派发授权域）：`core/cfg/pattern_parser.py`、`core/cfg/region_analyzer.py`（仅限 B81/B103 match 案例收集/分区判据扩展 + R8CDBG 插桩删除）、（后续批次按派发序列推进 exception_handler.py / comprehension_generator.py / code_generator.py / ast_converter.py）
- 证据前缀：`r8v8fixC_*`（探针读数经 R8FB_STAMP 控制落 `r8v8fixB_repro_*.json`，另配 `r8v8fixC_*` 独立证据）
- 探针基线（位B批终态 r8v8fixB_repro_final.json，本批开工复核 = r8v8fixB_repro_c_base2*.json 逐位一致）：B81_face 3/4、B103_main 10/13、B103_guard 5/8、B102_main 12/13、B102_except 5/8、B102_deep 9/10、B113_min 6/9、B113_host 12/14、B96_async 11/13、B112_async 21/24、B106_main 7/13、B106_call 4/13、B106_lam 26/27

---

## §0 修复成果表（逐族 before→after；after 随批次增量更新）

| 族 | 探针 | before（final 基线） | after | 状态 |
|----|------|--------------------|-------|------|
| B81 | B81_face | 3/4（n_true_guard 失败） | **4/4 success**（r8v8fixB_repro_c_b81_try1.json） | **已封闭** |
| B103 | B103_main | 10/13 | 10/13（e04_mapping/e05_class_kw/e06_or_guard 仍败） | 在途（§2） |
| B103 | B103_guard | 5/8 | **6/8**（GT.m 复活；none_guard/nested_guard 仍败） | 在途（§2） |
| B102 | B102_main/B102_except/B102_deep | 12/13, 5/8, 9/10 | — | 待做（§3） |
| B113残 | B113_min/B113_host | 6/9, 12/14 | — | 待做（§4） |
| B96 | B96_async | 11/13 | — | 待做（§5） |
| B112 | B112_async | 21/24 | — | 待做（§6） |
| B106 | B106_main/B106_call/B106_lam | 7/13, 4/13, 26/27 | — | 待做（§7） |

---

## §1 B81 — 真 guard `case 1 if flag:` 丢弃 + 幻影 continue（已封闭）

### 1.1 破口机理（三层叠加，判据全部 I.4 白名单）

探针 = `rounds/round1/probes_rv2/v_b74_face.pyc::n_true_guard`（源：`case 1 if flag: return "one" / case _: return "other"`）。CPython 3.11 对**无 COPY 副本协议**的字面量 case 链（后续 case 为 `case _` 时主体被直接消费）编译为：

```
blk@0 : LOAD subj; LOAD_CONST 1; COMPARE_OP ==; POP_JUMP_FORWARD_IF_FALSE → blk@22   ← 模式检查（fail 边）
blk@14: LOAD flag; POP_JUMP_FORWARD_IF_FALSE → blk@22                                ← 真 guard（fail 边同目标）
blk@18: return 'one'                                                                   ← 体
blk@22: NOP; return 'other'                                                           ← 下一 case（case _ 头+单块融合体）
```

该形态走 Phase 2 字面量扫描 `_scan_literal_match_subjects`（无 MATCH_*/COPY → Phase 1 `_mr_collect_case_body` 不认领；R8CDBG 追踪实证：v_b74_face 三函数仅 COPY 协议的 v_case_if_mid 走 Phase 1）。三层缺口：

1. **守卫块并入体（C1）**：字面量扫描链行走没有 `_mr_collect_case_body:15425-15449` 的 and-guard 链收集（Phase 1 路径自早轮已有），guard 块 blk@14 被 `_mr_collect_case_body_blocks` 收进 case 体 → 体发射时被语句层合成为幻影 if/else（且 else 臂吞掉 blk@22 的 `return 'other'`）。
2. **守卫提取锚缺失（C1）**：`pattern_parser._extract_case_guard_from_blocks` 的 search_start 锚对「无 STORE、无 COPY/MATCH_* 模式终结锚」的纯字面量头回退 0 → 头块自身的模式比较（`LOAD subj; LOAD_CONST; COMPARE_OP`）在 i=0 命中 var-const 臂形态 → guard_start=0 落入头块 → 被「守卫与头同块」抑制吞掉 → 真 guard 整体丢失。
3. **B74 幻影撤销器误杀（C3）**：`_b74_guard_arm_targets_case_body` 的体块集成员判据在「下一 case 为 `case _:` 单块融合体（NOP 标记+体同块）」时把真 guard 的 fail 目标（= 下一 case 头 = 下一 case 体成员）误判为幻影臂 → 即便守卫提取成功也被撤销。

### 1.2 修复锚点（代码已落地，I.6）

| # | 锚点 | 内容 |
|---|------|------|
| F1 | `core/cfg/region_analyzer.py` `_scan_literal_match_subjects` 链行走（or-guard 解析后，≈:16617-16649） | [B81 and-guard 链修复]：臂块尾随条件跳转目标 == 下一 case 头偏移（fail 边同一性）且极性 ∈ IF_FALSE/IF_TRUE 前后向四操作（真值臂正/反两态）⇒ 守卫材料，归 match 区域（visited_l/all_blocks_l），体入口跳过守卫链前进到真体首块。判据与 `_mr_collect_case_body` and-guard 链同源；or 臂 IF_TRUE 目标是体 ≠ fail 边，不受影响 |
| F2 | `core/cfg/pattern_parser.py` `_extract_case_guard_from_blocks` search_start 锚（≈:380-414） | [B81 真 guard 锚点]：STORE 锚与模式终结锚均不存在时（纯字面量/单例子头），头块以模式自身失败跳转终结（基本块在首个条件跳转处结束）⇒ search_start = 头块终结跳转之后，模式比较不再误触臂形态；通配+守卫融合头（POP_TOP+守卫同块）守卫在终结跳转之前，锚定后无可提取段 = 与旧行为（同块抑制→None）一致，零扰动 |
| F3 | `core/cfg/region_analyzer.py` `_b74_guard_arm_targets_case_body`（≈:2158-2290） | [B81 细化]：新增 fail_case_offset 参数——臂终止跳转目标 == fail 边（下一 case 头/merge 偏移）⇒ 臂以「守卫失败」离开 case，这是真 guard 的定义判据（guard 尾随条件跳转目标指向下一 case header），优先于体块集成员关系（修复 `case _:` 单块融合体的误杀）；同时重放 search_start 与 F2 锚同步（docstring「提取器判据演进时本重放需同步」条款落实） |
| F4 | `core/cfg/region_analyzer.py` 三处调用点（≈:14508/16225/16746 `_b74_guard_arm_targets_case_body(_pb, case_bodies, fail_case_offset=_fail_off)`） | 传参落地（`_fail_off` = 下一 case 头或 merge 偏移，调用点既有变量） |

### 1.3 判据与条款引用

- 判据（I.4 白名单）：**guard 尾随条件跳转目标 oparg == 下一 case header 偏移**（跳转目标指令 oparg 事实）+ 头块内条件跳转位置（块内指令序）+ 头块终结跳转（块末 opcode）+ 体块成员关系（区域成员关系）。无文件/函数名白名单、无 start_offset 阈值、无跨层反查、无新 self 状态。
- 条款：C1（守卫块/守卫指令的局部消费在两条平行链行走与提取器中各归其位）、C3（B74 撤销器以 fail 边同一性显式守卫封闭，恢复「真 guard 臂失败边离开 case」的结构不变式）；修复语义 = 封闭守卫恢复无感（I.3 推论），非个案补丁——判据对任意字面量/单例子模式、任意 case 链位置、任意嵌套深度同判（归纳论证，无需逐深度验证）。
- 注：字面量扫描与 Phase 1 扫描是同一 case 链协议的两个平行实现；F1 把 Phase 1 已证的 and-guard 链判据补齐到字面量实现，属「判据在判据所在层修」（I.2 单向数据流，不在生成层回溯）。

### 1.4 docstring 合规声明（I.7）

- `_extract_case_guard_from_blocks`（本批触及）：新增六项模板 docstring（①三级锚点序算法依据②自底向上归约顺序③search_start 前后模式/守卫材料唯一归属④臂链解析嵌套处理⑤守卫表达式 dict 的 AST 映射接口⑥反编译流程位置）+ [C1][C2][C3] 声明。
- `_b74_guard_arm_targets_case_body`（本批触及）：docstring 增补 [B81 细化] 段（fail 边同一性优先于体成员关系）+ 重放同步边界条件更新；保留原 [C1][C2][C3] 声明。
- `_scan_literal_match_subjects` 链行走段：F1 以行内注释块声明判据来源、[C1][C2][C3] 与 `_mr_collect_case_body` 同源关系（该方法整体 docstring 不在本批触及范围，未改动其既有注释结构）。

### 1.5 验证

- 探针：B81_face 3/4 → **4/4 success**（`r8v8fixB_repro_c_b81_try1.json`）。
- 变体电池（`test_repros/round8/` 本批新建 `r8v8fc_*` 前缀，见 §8 清单）14 形态实测：t1（n_true_guard 本体）✓、t3（比较守卫 `case 1 if y > 0:`）✓、t7（链中捕获+守卫 `case n if flag:`，基线 compile_error）✓、t10（反转真值守卫 `case 1 if not flag:`）✓、t11（and 链守卫）✓、t13（COPY 协议反转守卫，基线已过维持）✓、t14（`not (a and b)` 字节等价歧义形态，基线已过维持）✓；t4/t5/t6/t9/t12（负对照/已过形态）全部维持 ✓。
- 同域正外溢：B103_guard 5/8 → **6/8**（GT.m `case {'a': v} if v:` 守卫复活——其 fail 目标恰为 `case _:` 单块融合体，F3 修复同一误杀）。
- 残余如实登记（B81 家族子形态，非本族判据可及）：t2（`case _ if y > 0:` 通配+守卫融合头——守卫在头块内终结跳转之前，F2 锚不可及、`_mr_head_has_capture_binding` 无捕获绑定为 False 使 allow_in_header_block 恒假）移交 B103 拆分批次；t8（`case 1 | 2 if flag:` or-模式+守卫）= B103 e06_or_guard 同形，见 §2。

