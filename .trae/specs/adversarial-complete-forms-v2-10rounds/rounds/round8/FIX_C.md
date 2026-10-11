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
| B103 | B103_main | 10/13 | **13/13 success**（r8v8fixB_repro_c_fixall.json） | **已封闭**（§2） |
| B103 | B103_guard | 5/8 | **8/8 success**（同上） | **已封闭**（§2） |
| B102 | B102_main/B102_except/B102_deep | 12/13, 5/8, 9/10 | — | 待做（§3） |
| B113残 | B113_min/B113_host | 6/9, 12/14 | — | 待做（§4） |
| B96 | B96_async | 11/13 | — | 待做（§5） |
| B112 | B112_async | 21/24 | — | 待做（§6） |
| B106 | B106_main/B106_call/B106_lam | 7/13, 4/13, 26/27 | — | 待做（§7） |

> 批量门禁读数（B103 封闭时点，r8v8fixB_repro_c_fixall.json 对 r8v8fixB_repro_final.json）：
> 30 探针 units 297→**304**/357，NEWFAIL=**0**，BETTER={B81_face +1、B103_main +3、B103_guard +3}；
> 站桩 6 面：round1face 417/423 SAME、round2face 238→**239**/251（v_b74_face 3→4，B81 正向外溢）、
> probe42 176→**177**/196（m05_module_match 0→1，match 宿主正向外溢）、residual 419/446 SAME、
> oldface 665/692 SAME、quotation 152/153 SAME（WORSE 全部 = 0）；
> 34 集 8 分片 1505/1568 NEWFAIL=**0**（逐文件比对 HEAD 分片证据）；
> r8v8fc_* 变体电池 13 探针 **33/33 units**（e01mini/e06mini/or_variants/with_ret 本批新建 4 探针全过）。

---

## §2 B103 — match or 模式 / or+guard / 宿主发射域（已封闭）

### 2.0 承接声明（前任 hunk 记录，代码已提交于 61102a8d，I.6）

前任位C前段为 B103 已落 hunk（git diff 5d5b443c..61102a8d，core/cfg/region_analyzer.py +274）：
- `_mr_resolve_or_arm_jump`（region_analyzer.py:14869）——字面量 or 模式 IF_FALSE 臂链解析（判据 =
  臂块以 IF_FALSE 终结 ∧ ft 为纯 JUMP_FORWARD 连接块同汇公共成功块 S）；
- `_mr_collect_case_body` 内 or 臂链解析调用 + [B103 try 宿主连接桩判定]（正常后继 = successors −
  exception_successors，:15771 一带）；
- [B103] `_collect_all_pattern_instrs` 异常边排除 + 非条件块后继经 `_is_pattern_continuation_block`
  把关（pattern_parser.py）。
- **承接时实测勘误**：前任证据 try4（12/13，e06 唯一败）与提交树不一致——提交树实测 11/13
  （**e01_value 新增失败**：`case 3 | 4:` 降级 `case 3:`，r8v8fixB_repro_cresume.json）。
  try4（01:23）早于提交（08:33），提交含 try4 后的未复核变更。本批以提交树为基线修复。

### 2.1 破口机理（三层 + 两个宿主域缺口，判据全部 I.4 白名单）

**机理 A（e01_value 回归 = or 臂材料被认领后 MatchOr 装配断链，C1）**：前任 `_mr_resolve_or_arm_jump`
把 or 臂块（`COPY; LOAD_CONST c_i; COMPARE_OP; POP_JUMP_FORWARD_IF_FALSE→下一臂`）归 match 区域作
模式材料后，臂块不再是 case（旧机制靠「case-per-arm + 体等价合并」产 MatchOr——两臂体相同才合并），
而 `parse_case_pattern` 的字面量捷径（pattern_parser.py `_extract_case_pattern` is_literal_match
分派）只消费头块局部指令 → `case 3 | 4:` 只产 MatchValue(3)，`| 4` 交替丢失。

**机理 B（e06_or_guard = or+guard 组合三缺口）**：
1. **guard 链 fail 边身份错位（C3）**：or 臂链解析后，case 头原始失败目标是臂/清理桩（jt=78），真
   守卫块（POP_TOP 接受 + `LOAD x; LOAD_CONST 1; COMPARE >; POP_JUMP_FORWARD_IF_FALSE→104`）的
   失败边指向**下一 case 头本体**（104）——and-guard 链判定按 `agc_jump.argval == next_case_offset`
   （原始 50）比对恒不中，守卫块不被链行走收集，体入口错定在守卫块（守卫+体一起被吞）。
2. **guard 材料收集污染（C1）**：`_collect_pattern_blocks` 的 guard_like 续块扩展无差别下钻体块——
   纯赋值体块（`LOAD_CONST 'small'; STORE r; JUMP_FORWARD`）落入 store-only 判据被收进守卫材料，
   其 STORE 把守卫提取器的「最后 STORE」锚推过守卫段 → 真守卫（`x > 1`）整体丢失。
3. **or 交替丢失**：同机理 A。

**机理 C（with 宿主 match 发射域缺口，跨文件锚）**：`_generate_with` 的嵌套区域消费门
（region_ast_generator.py 两处 isinstance 元组）缺 **MatchRegion**——with 体内 match 不被消费：
match 入口块落裸语句发射、链块逐块散射（臂块成幻影 if、体块成顺序语句），match 整体再被顶层
扫描发射一份。`_generate_try` 同位消费门（:31260）含 MatchRegion 自证同构缺口（try 宿主 match
e05_class_kw 通过、with 宿主 match 全散）。

**机理 D（with 宿主 Phase 1 支配种子越界 + 体块发射归属缺口，C3）**：
1. `_mr_collect_case_body` 的支配种子行走按「受 subject 支配 ∧ 有正常前驱」收集 all_blocks——with
   宿主下经异常表边可达 with 的 handler 尾块（RERAISE/COPY 3/POP_EXCEPT 链）与 with 出口后继
   （`return r` 块），被卷入 match 区域（block_to_region 被 match 抢注）→ with 之后的 `return r`
   被 match 区吞掉不发射。[B17] try 体边界存在、with 体边界缺失（同判据不同构）。
2. `_generate_match` 体块循环的「归属其它区域」分支（:37545）处理 Try（try_blocks → 按普通块发
   语句）与 Loop（break/continue）但缺 With 分支——with 先于 match 识别（analyze 顺序），match 体
   块 block_to_region 首Claim 指向祖先 WithRegion，体块被无语句标记 generated → case 体退化 pass。

### 2.2 修复锚点（代码已落地，I.6）

| # | 锚点 | 内容 |
|---|------|------|
| G1 | `core/cfg/pattern_parser.py` `_extract_case_pattern` 字面量分派位 | [B103 or 臂链材料扩展]：`_collect_or_arm_chain_instrs(case_block)` 收集臂材料（同汇 S 协议，与 `_mr_resolve_or_arm_jump` 判据同源——同判据双实现同步），扩展指令序列交 `_extract_or_or_literal_pattern` 合成 MatchOr；无臂链（单字面量 case：ft 直落体/守卫块非纯连接块；or 守卫 IF_TRUE 极性）返回空表，行为逐位不变 |
| G2 | `core/cfg/pattern_parser.py` 新增 `_pure_jf_argval` + `_collect_or_arm_chain_instrs`（六项模板 docstring + [C1][C2][C3]） | 纯 JUMP_FORWARD 连接块目标偏移判定 + 臂链指令收集；终止性由 `_seen` 有限集保证（无 G4 上限）；成功边解析经 exception_successors 排除异常表边 |
| G3 | `core/cfg/pattern_parser.py` `_collect_pattern_blocks` guard_like 续块扩展 | [B103 守卫链边界]：守卫链续块以条件跳转**终结**（失败边离开 case 指向下一 case——守卫链协议本体）；体入口块以无条件跳转/RETURN/落穿终结不入材料。体首 if（条件跳转但目标在体内 ≠ fail 边）经既有分类判定自然排除，不误吞。原 store-only 体块污染「最后 STORE」锚 → 真守卫丢失路径封闭 |
| G4 | `core/cfg/region_analyzer.py` `_mr_collect_case_body` and-guard 链 | [B103 or-guard 链 fail 边同一性]（B81 F1 同族外推）：链认定目标取双值——原始跳转目标（直连形态）或 `_mr_skip_case_connectors(jt)` 解析后的下一 case 头偏移（or 臂/清理桩间接形态）。单守卫（非 and 链）与 and 链同判据覆盖 |
| G5 | `core/cfg/region_analyzer.py` `_mr_skip_case_connectors` | [B103 try/with 宿主连接桩]「后继唯一」按正常边集合（successors − exception_successors）计数——与链行走 is_connector 判据（前任 hunk）同步；无宿主桩块异常边集为空，行为逐位不变 |
| G6 | `core/cfg/region_analyzer.py` `_mr_collect_case_body` 支配检查 | [B103] 末 case 判定按连接桩解析后的真实下一候选：`case 2 \| 3:`（无 `case _` 的末 or case）原始失败目标是受支配清理桩，桩后继（链外 merge）被当 default 候选登记幻影 `case _`；支配检查对象 = 解析后候选，直连形态解析结果 == jt 行为不变 |
| G7 | `core/cfg/region_analyzer.py` `_scan_literal_match_subjects` | 同判据双实现同步：or 臂链解析调用 + and-guard 链 fail 边双目标 + 末 case 支配检查解析后候选（与 `_mr_collect_case_body` G4/G6 同源，字面量扫描不登记幻影臂 case、不与 G1 的 MatchOr 双重合并） |
| G8 | `core/cfg/region_analyzer.py` `_identify_match_regions` 候选循环 | [B103 or 臂材料子链去重]（[B16] 子链去重扩展）：候选块 ∈ 某 MatchRegion.blocks 且 ∉ 其任何 case 体块集 ⇒ 它是该链链材料（头/臂/桩/守卫/汇合），唯一归属（原则 2）禁止重建子链——Phase 1 claimed 快照在循环内不更新，臂块候选回溯前驱重建幻影/重复区域（e06 层级错构）。case 体块不在此列（嵌套 match subject 位于外层 case 体内，二次归约合法——e09_nested_match 自证） |
| G9 | `core/cfg/region_analyzer.py` `_mr_collect_case_body` 支配种子行走 | [B103 with 宿主边界]（[B17] try 体边界同构）：subject ∈ 某 WithRegion.with_blocks 时 match L(A) 以 with 体为界——with handler 尾块/清理块/出口后继（`return r`）是宿主结构块/后续语句，不属 match；判据 = 宿主区域成员关系（白名单）；merge 由调用点另行并入不受影响；无 with 宿主行为逐位不变 |
| G10 | `core/cfg/region_ast_generator.py` `_generate_with` 消费门（**跨文件锚，显式登记**） | [B103 with 宿主 match 消费缺口]：两处嵌套区域消费门 isinstance 元组补 MatchRegion（与 `_generate_try` :31260 同位门同步）——match 入口块经 `_generate_region → _generate_match` 整树生成，链块登记 generated 防逐块散射 |
| G11 | `core/cfg/region_ast_generator.py` `_generate_match` 体块「归属其它区域」分支（**跨文件锚**） | [B103 with 宿主 match 体块消费缺口]：补 WithRegion 分支（与上方 Try 分支同判据同构）——case 体块 ∈ 祖先 with_blocks 时按普通块生成语句归本 case 体发射（首Claim 归属与语义归属分离 = 识别顺序协议，try 宿主同形态自证） |

### 2.3 判据与条款引用

- 判据（I.4 白名单，全锚点）：**块末指令 opcode**（臂块以 POP_JUMP_FORWARD_IF_FALSE 终结；连接块
  纯 JUMP_FORWARD；守卫链续块以条件跳转终结 / 体入口以无条件跳转-RETURN 终结）、**后继/前驱集合
  与跳转目标 oparg**（臂成功边纯连接块同汇公共成功块 S = or 协议本体，也是臂与「下一 case 头」的
  区分判据——下一 case 头的成功边汇合到它自己的体 S' ≠ S）、**异常边**（exception_successors
  集合差：连接桩唯一后继判定 / 臂材料收集成功边解析 / with 宿主 handler 排除）、**区域成员关系**
  （链材料去重 G8、with 体边界 G9、祖先 with_blocks 体块归属 G11）、**支配关系**（末 case 判定
  G6 沿用 B15 同族判据）。无文件/函数名白名单、无 start_offset 阈值、无跨层反查、无新 self 状态、
  无深度/计数上限（臂链终止性由 `_seen` 有限集保证）。
- 条款：C1（臂/守卫材料的局部消费各归其位——G1/G2/G3 在材料所在层提取，不回溯）；C2（with 宿主
  经显式接口消费：G9/G10/G11 中 WithRegion 仅以 with_blocks 块集与 entry 引用被消费，match 不窥
  视 handler 内部）；C3（守卫失败边 = case 链显式结构协议——G4 的 fail 边同一性判据是 B81 F1-F3
  同族外推；G9 的宿主边界与 [B17] try 边界同构封闭）。修复语义 = 封闭守卫恢复无感（I.3 推论）：
  判据对任意字面量交替数、任意 case 链位置、任意宿主（if/try/with/循环/模块）、任意嵌套深度同判
  （归纳论证，无需逐深度验证）。
- 注：G1/G2 与区域层 `_mr_resolve_or_arm_jump` 是同一 or 协议的两个平行消费端（识别层认领臂块、
  提取层从臂块重建 MatchOr），判据字面同源（I.2 单向数据流，无生成层回溯）。

### 2.4 docstring 合规声明（I.7）

- `_collect_or_arm_chain_instrs` / `_pure_jf_argval`（新增）：六项模板齐全（①No More Gotos 多分
  支选择 + I.1 原则4 case 头栈协议②自底向上材料追加不重排③同汇协议唯一归属判定④嵌套由识别层二次
  扫描独立归约、终止性有限集保证⑤产出臂指令序列供 MatchOr 合成⑥字面量分派位调用）+ [C1][C2][C3]。
- `_mr_skip_case_connectors`（触及）：docstring 增补 [B103 try/with 宿主连接桩] 段（正常边集合计
  数）+ C 条款更新；保留原 [B16-C3] 条款。
- 其余锚点以行内注释块声明 [B103] 判据来源 + [C1][C2][C3]（G3/G4/G6/G7/G8/G9/G10/G11，均带机
  理说明与白名单判据；所属方法整体 docstring 未改动其既有注释结构）。

### 2.5 验证（代码已落地读数）

- 探针：B103_main 10/13 → **13/13 success**；B103_guard 5/8 → **8/8 success**；B81_face
  **4/4 维持**（r8v8fixB_repro_c_fixf5/c_fixall.json）。
- or 变体电池（本批新建 `r8v8fc_b103_e01mini/e06mini/or_variants/with_ret` + 既有 9 探针）：
  **13 探针 33/33 units**——e01 形（if 宿主 or 无守卫）、e06 形（or+guard 双 case）、
  or_noguard/or_empty_body/or_strings/or_last_case（无 `case _` 的末 or case，幻影 `case _` 封
  闭）/or_loop_host（循环宿主 or+guard）/or_mid_chain（链中 or）/or_return_body（return 体）、
  w_ret/w_match_ret（with+match+return 负对照）全过。
- e06_or_guard 发射实测：`with ctx(): match x: case 1 | 2 | 3 if x > 1: r='small' / case 4 | 5
  if x > 4: r='mid' / case _: r='other'` + with 后 `return r` 完整（with 宿主 + or + guard + 尾
  return 三层叠加形态）。
- 批量门禁：见 §0 表下读数（30 探针 304/357 NEWFAIL=0、站桩 6 面 WORSE=0 含两面 +1 正向外溢、
  34 集 1505/1568 NEWFAIL=0）。
- **残余如实登记（B81 家族子形态，§1.5 t2 承接）**：t2 通配+守卫融合头 `case _ if y > 0:`（守卫
  在头块内终结跳转之前）仍败——机理在案：`_extract_case_guard_from_blocks` 三级锚点序无「通配
  丢弃 POP_TOP」锚（(a)STORE/(b)模式终结均不存在时落入 (c) 头块终结跳转锚——守卫自身的 PJF 即终
  结跳转，search_start 越过守卫段）+ `allow_in_header_block` 门要求 `_mr_head_has_capture_binding`
  恒 False（通配头无捕获绑定）。修复方向：锚点序补 (b') 前导 `LOAD subj; POP_TOP` 通配丢弃锚（I.4
  白名单：块内 opcode 序，与 `_extract_case_pattern` 的通配丢弃判定 :1309-1318 同判据）+ allow 门
  扩展为「头块 ∉ case 体块集 ∧（捕获绑定 ∨ 通配丢弃头形态）」。涉及 `_b74_guard_arm_targets_
  case_body` 重放同步（docstring「提取器判据演进时本重放需同步」条款）。本批未及落地（B102-B106
  六族优先级更高），如实移交后续批次。

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

