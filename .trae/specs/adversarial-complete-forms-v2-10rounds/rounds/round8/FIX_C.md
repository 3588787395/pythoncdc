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
| B102 | B102_main/B102_except/B102_deep | 12/13, 5/8, 9/10 | **13/13, 8/8, 10/10 success**（r8v8fixB_repro_c_b102_try4.json） | **已封闭**（§3） |
| B113残 | B113_min/B113_host | 6/9, 12/14 | **9/9, 14/14 success**（r8v8fixB_repro_c_b113_try2.json） | **已封闭**（§4，含 B110 划除确认 §4.6） |
| B96 | B96_async | 11/13 | **13/13 success**（r8v8fixB_repro_c_b96_try2.json） | **已封闭**（§5） |
| B112 | B112_async | 21/24 | **21/24 维持**（a_four 同源单元已随 §5 复活；e05/e07 两单元移交 §6） | **部分移交**（§6） |
| B106 | B106_main/B106_call/B106_lam | 7/13, 4/13, 26/27 | **13/13, 13/13, 27/27 success**（r8v8fixB_repro_c_b106_try3.json） | **已封闭**（§7） |

> **位C续作（第五段·收尾）终态复核**（r8v8fixB_repro_cfinal.json，插桩清零后零行为变更证明）：
> 13 探针 166/169 与 b106_full 逐位一致（B81 4/4、B103 13/13+8/8、B102 13/13+8/8+10/10、
> B113 9/9+14/14、B96 13/13、B112 21/24 维持、B106 13/13+13/13+27/27）；站桩复核
> quotation 152/153、round1face 417/423、round2face 239/251、probe42 177/196 四面
> 逐位一致；R8CDBG 在途调查插桩族清零（含配套 `import os as _os_r8*` 行，grep 零命中，
> env 门控默认关 ⇒ 零行为变更）。门禁详情 §8，落地锚点汇总 §9，未竟移交 §10。

> **位C续作（第四段）终态批量读数**（r8v8fixB_repro_c_b106_full.json，对 c_t2final 基线）：
> 30 探针 units 297→**332**/357（+35），NEWFAIL=**0**，BETTER={B102_main +1、B102_except +3、
> B102_deep +1、B113_min +3、B113_host +2、B96_async +2、B106_main +6、B106_call +9、
> B106_lam +1}；站桩 6 面：round1face 417/423、round2face 239/251、probe42 177/196、
> residual 419/446、oldface 665/692、quotation 152/153（WORSE 全部 = 0）；
> 34 集 8 分片 1505/1568 NEWFAIL=0；r8v8fc_* 新变体电池 4 件（b102 8/10 含登记残余、
> b113_flat 21/21、b96_async 14/18 含移交残余、b106_star 18/18）。

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



---

## §3 B102 — except\* 多 handler/else/finally/嵌套/with 宿主四残余位（已封闭）

### 3.1 破口机理（四残余位三根因，判据全部 I.4 白名单）

B102 残余四失败位 = c4_03 的 e04_with、r4v4r_b102_except 的 normal_finally / star_else_finally / nested_star、r5v5_14 的 es_with。字节码级取证（r8c_dump，CPython 3.11 实测反汇编 + 异常表）确立三根因：

**根因 1（退化链配对拒绝，C3）**：CPython 3.11 对 `try: pass`（体编译为单 NOP）省略
body→handler 异常表条目——链的唯一原始条目 = handler 体自清理保护，_parse_exception_
table 合成出**退化签名 try_start == handler_start** 的链 info。finally 宿主的区间起点是
体帧胶水（try_start ≠ handler_start），配对互斥分支（try_start 不同 ∧ 互含 ⇒ 视为
「finally 体内独立 try-except」拒绝配对）把语句自有的退化链一并拒绝 ⇒ 链自建区域后
handler 整链丢失（normal_finally 的 except ValueError: 蒸发、star_else_finally 的
except* ValueError: 蒸发）。

**根因 2（else 臂错位，C1）**：PEP 654 布局不变式——含 except\* 的语句 else 体位于全部
handler **之后**（普通 except 的 else 体在 handler 之前，二者布局相反）。既有
_find_try_else_blocks/_find_inner_else_blocks 在 (try 体尾, 首 handler) 区间找 else，
命中的是 try 体正常出口的帧胶水跳转块；真 else 体（es_with 的 ok()@164）留在
try_blocks 中误入 Try.body（发射实测：	ry: fn(); if True: pass; ok()）。

**根因 3（退化嵌套平级化，C2/C3）**：外层 try 的异常表经区间扩展吞并内层退化结构后，
内外层 	ry_offset_start 相等（nested_star 同为 10）——R90 的严格大于判据失效 ⇒ 内外层
平级发射为两个兄弟 try（	ry: pass except* VE: pass except* TE: pass +
	ry: pass except Exception: return None），外层体（= 内层 try 语句）错构。

### 3.2 修复锚点（代码已落地，I.6；全部 region_analyzer.py B102 except\* 归并判据域 + 一处 region_ast_generator.py 发射补丁）

| # | 锚点 | 内容 |
|---|------|------|
| E1 | core/cfg/region_analyzer.py paired_except_indices 收集步 | [B102-fix2] 退化链配对：互斥分支前接 _b102_degenerate_chain_pairs_finally 判定——命中则退化链不受「互含拒绝」限制。非退化链逐位不变（C3） |
| E2 | core/cfg/region_analyzer.py 新增 _b102_degenerate_chain_pairs_finally + _b102_chain_reachable_blocks + _B102_ZONE_FRAME_OPS | 配对合法性判据（六项模板 docstring + C 条款）：①退化签名 try_start == handler_start；②同语句链族（同清理 target 的全部退化链）整体前/后界；③前置区 [finally.try_start, 首链头) 无实代码（有 ⇒ 链前还有 try 体实代码 ⇒ 内层链，pre_inner 形拒绝）；④尾部区 [末链尾, finally.try_end) 无**链可达**实代码（链可达 = 正常+异常边 BFS；try 体续体经链正常出口可达 ⇒ ideg 形拒绝；else 臂只经体帧胶水到达、不经链可达，不受此限）。可达集 BFS 终止性由有限块集+已访集保证（无 G4 上限） |
| E3 | core/cfg/region_analyzer.py else 识别步（_find_try_else_blocks 调用点） | [B102-fix1] 星链 else 臂：门控 = finally 宿主 ∧ 配对链 ∧ 链头块含 CHECK_EG_MATCH（3.11 except\* 标记口径，II.7 第 12 条）⇒ else = _find_star_else_blocks（[首链头, try_offset_end) 内不经链可达 ∧ ∉ handler/finally 帧集 ∧ 非噪声-only 的块）；不命中门控走既有路径逐位不变。噪声-only 块（else: pass 的 NOP 帧标记）不入 else——ast.Try 无 orelse 与 else: pass 语义等价 |
| E4 | core/cfg/region_analyzer.py 新增 _find_star_else_blocks | else 臂识别（六项模板 docstring + C 条款）：else 臂 = 异常表无 handler 边区间内唯一不经链到达的成员（区间成员关系 + 可达性差双判据） |
| E5 | core/cfg/region_analyzer.py 星框架清理扫描（adv17 _star_framework 之后） | [B102-fix1b] finally 配对链同款框架清理：链头含 CHECK_EG_MATCH ∧ 块起点 ≥ 首链头 ∧ ∉ handler 体 ∧ **经链可达** ⇒ 从 try_blocks 移 cleanup_blocks（else 臂不经链可达不受影响）。留 in try_blocks 时退化空 try 体（	ry: pass）重编译多出 body→handler 异常表条目（star_else_finally 实测 (4,4)→8 vs 期望 (4,4)→78），字节级发散 |
| E6 | core/cfg/region_analyzer.py 嵌套建立循环（R90 判据后） | [B102-fix3] 退化等起点嵌套：A 退化签名 ∧ 等起点严格包含 ∧ B handler 在 A 跨度外 ∧ **∃ 原始异常表条目 target=B 首 handler 且区间与 A 块集相交**（内层清理尾 RERAISE 必经外层 handler 续投——try-in-try 结构不变式）⇒ A.enclosing_try = B + add_child。生成器 nested 预循环经 is_child 派发 A 进 B 体 |
| E7 | core/cfg/region_ast_generator.py _generate_with 两处 else 镜像过滤（**跨文件锚，显式登记**） | [B102 with 宿主 else 镜像误杀收紧]：纯指令镜像判据（eb 与 finally 体剥噪同形）对「单调用 else 体 × 单调用 finally 体」同形误杀 else 臂（es_with 的 else: ok() × inally: _done()）。收紧 = 镜像命中还须经 handler 链可达（finally 正常副本在 handler 正常完成路径上 ⇒ 经链可达；else 臂不经链可达）。判据 = _b102_chain_reachable_blocks 可达集（I.4 白名单），非镜像块零扰动 |

### 3.3 判据与条款引用

- 判据（I.4 白名单，全锚点）：**异常表区间成员关系**（退化签名 = 链头 start 的原始条目；
  同清理 target 链族；E6 的 target=外层 handler 且区间相交）、**块内指令 opcode**（CHECK_EG_MATCH
  3.11 except\* 标记口径 II.7 #12——禁用 3.12 PRELOAD_RERAISE；_B102_ZONE_FRAME_OPS 框架/
  胶水/绑定清理操作码集；PREP_RERAISE_STAR/LIST_APPEND 在既有 adv17 清理判据内）、
  **后继/前驱与可达集**（_b102_chain_reachable_blocks：正常边 ∪ 异常边 BFS——链可达 = 链自有
  材料 + 体续体，else 臂 = 唯一不经链到达区间成员，这是 else/体续体/finally 副本的三分判据）、
  **区域成员关系**（E7 的 finally_blocks/handler 体成员排除；E6 的 A 块集）。无文件/函数名白名单、
  无 start_offset 魔法阈值、无跨层 X.entry in Y.blocks 反查、无新增 self 跨方法状态
  （_b102_* 均为纯函数式判定，返回值即消费）、无深度/计数上限（BFS 终止性 = 有限块集）。
- 条款：C1（else 臂识别在判据所在层——异常表区间+可达性差，不在生成层回溯；E3/E4/E5 同层归
  约各归其位）；C2（退化嵌套以 parent/children 抽象节点被外层整树派发，E6 后生成器经 is_child
  入口引用，不窥视内层；E7 的 else 臂只经区间/可达性接口被宿主消费）；C3（E1 的非退化链显式
  豁免 = 原互斥分支逐位不变；E3 的门控不命中 = 既有 else 路径逐位不变；E7 的非镜像块零扰动）。
  修复语义 = 封闭守卫恢复无感（I.3 推论）：判据对任意 handler 数、任意链位置、任意宿主
  （with/try/函数级）、任意退化嵌套深度同判（归纳论证，无需逐深度验证）。
- **CPython 3.11 codegen 不变式**（E1/E2 判据的成立基础，实测确立）：try 体编译为单 NOP
  （	ry: pass）⇌ body→handler 表项省略 ⇌ 退化签名成立。体含任何其他指令（含不可抛的
  x = 1）时编译器仍发 body→handler 表项（x1deg 实测 (4,8)→10）⇒ 链非退化、走原路径——
  该不变式保证前置区判据（③）的完备性：真退化链的前置区必为纯帧胶水。

### 3.4 docstring 合规声明（I.7）

- _b102_degenerate_chain_pairs_finally / _b102_chain_reachable_blocks /
  _find_star_else_blocks（新增）：六项模板 docstring 齐全（①CPython 3.11 codegen 不变式
  +PEP 654 布局不变式 + I.1 原则 2 算法依据②paired_except 收集步/else 识别步自底向上先于
  区域构建③异常表区间成员 + 块指令 opcode + 可达集的唯一归属判定④同语句链族整体前后界/
  else 子结构按入口引用派发⑤链头偏移经 paired_except_infos/else 块列表 → Try.orelse 的
  AST 映射接口⑥try/except*/finally 单语句重建流程位置）+ [C1][C2][C3] 条款声明。
- E1/E3/E5/E6/E7 以行内注释块声明 [B102] 判据来源、白名单构成与 C 条款；所属方法既有
  docstring 结构未改动（_identify_try_except_regions 整体 docstring 已含六项模板 + C 条款，
  本批未破坏其一致性）。

### 3.5 验证（代码已落地读数）

- 探针：B102_main 12/13 → **13/13**；B102_except 5/8 → **8/8**；B102_deep 9/10 → **10/10**
  （r8v8fixB_repro_c_b102_try4.json）。
- 攻击面全量：31 探针面 30 条目 309/357（基线 c_t2final 304/357，+5），BETTER={B102 三探针}，
  **NEWFAIL=0**（r8v8fixB_repro_c_b102_full.json 逐条目比对）。
- 变体电池（d:\Temp\opencode 本批新建 10 形态 + 正在入库见 §8）：tef（普通 except+else+finally
  负对照）维持 ✓、tesf（except\*+else+finally 主体同形）**转 success** ✓、tesf2（except\*+
  finally）维持 ✓、tesf3（except\*+else 无 finally）维持 ✓、x1deg（**退化判据负对照**：
  体含 x=1 ⇒ 链非退化 ⇒ 原路径）维持 ✓、nstar（nested_star 期望源字节等价自证）✓、
  own_else_star（	ry: pass except* E: pass else: ok() finally: done()）**转 success** ✓、
  inner_else_star（嵌套退化 + else 形）**转 success** ✓（verify 判 ruler 语义等价，NOP 数
  差异容忍）。
- 站桩 6 面：round1face **417/423** SAME、round2face **239/251**（B103 终态位持平）、
  probe42 **177/196**（同）、residual **419/446**（252/277+167/169）SAME、oldface
  **665/692**（218/227+447/465）SAME、quotation **152/153** SAME——WORSE 全部 = 0。
- 34 集 8 分片：**1505/1568 NEWFAIL=0**（逐文件比对 failing_index 基线）。
- **残余如实登记**（B102 邻接形态，非四失败位判据可及，修复前即败、本批未回退）：
  ideg（	ry: [try: pass except E: pass, fn()] finally: done()——内层退化链经 E2 判据④
  正确拒绝配对（fn() 链可达 ⇒ 内层链），但内层区域经生成器 [R86 fix] 延迟派发后无人认领
  ——_ntr_has_preceding_try_blocks 把外层体帧胶水块（偏移 6 < 内层 8）计入「前导语句块」
  触发延迟，而胶水块不生成语句、主走查永不经过内层 entry ⇒ 内层 try 蒸发）；pre_inner
  （n() 在内层退化 try 之前——E2 判据③正确拒绝，同 R86 延迟缺口）。两形同根：R86 延迟
  判据的「前导 try_blocks」应排除纯胶水块（块内指令序白名单可表达），移交后续批次。



---

## §4 B113残 — 多 for 子句推导式扁平子句丢失（已封闭）+ B110 划除确认

### 4.1 破口机理（CPython 3.11 推导式 codegen 不变式，判据全部 I.4 白名单）

CPython 3.11 对 `for T in [<单元素列表字面量>]` 的推导式子句做**内联展开**：单元素列表
不建 BUILD_LIST/GET_ITER/FOR_ITER 协议，直接编译为 `<expr 求值>; STORE T`（扁平对）。
_parse_multi_for_comprehension 的 clause 头收集只统计 FOR_ITER/GET_ANEXT——扁平子句
无头，整条丢失：

- comp2 e1：`[(a, b) for a in [x] for b in [x] for x in xs]`——中位子句 `for b in [x]`
  内联为 `LOAD x; STORE b`，丢失 ⇒ `[(a, b) for a in (x,) for x in xs]`；
- comp2 e2 / c4_05 e09_comp_host：末位子句内联（e2 `for b in [xs[1]]` → `LOAD_DEREF
  xs; LOAD_CONST 1; BINARY_SUBSCR; STORE b`；e09 `for g in [open(b)]` → 调用序列 +
  `STORE g`），且全式仅剩 1 个 FOR_ITER ⇒ 单 for 路径，扁平对落在元素窗前导，
  丢失 ⇒ 子句整条消失。

等价源重构（round4 REVIEW2 §5 判据方向）：`for T in (<expr>,)`——单元素元组与单元素
列表同样内联，重编译逐字节复现原始指令序（c4_18 直接探针 e4 形既有验证，本批 f9/f10
负对照复核）。

### 4.2 修复锚点（代码已落地，I.6；全部 comprehension_generator.py）

| # | 锚点 | 内容 |
|---|------|------|
| C1 | comprehension_generator.py 新增 _b113_extract_flat_clauses（六项模板 docstring + C 条款） | 扁平子句识别：候选段 = [窗起点, 首个 STORE_*)，段内只含表达式构造 opcode（LOAD_*/BUILD_*/BINARY_*/COMPARE_OP/UNARY_*/PRECALL/CALL 等）；含 COPY（walrus `COPY 1; STORE` 副作用对，[Round10-05] 判据）/POP_*/跳转/FOR_ITER/GET_ITER/追加 opcode/UNPACK/RETURN 之一即终止（不命中零扰动，C3）。目标经 _parse_target_store_sequence 结构化解析（元组/星号目标），表达式经 expr_reconstructor 重建；iter 包装单元素元组 `{'type': 'Tuple', 'elts': [expr], 'ctx': 'Load'}`。连续扁平按序贪心消费（终止性 = 窗口有限长度，无 G4 上限） |
| C2 | _parse_multi_for_comprehension 真子句 iter 窗（gen_idx ≥ 1 分支） | iter 窗前导扁平消费：[上一子句过滤段尾, 本子句 GET_ITER 锚) 内先贪心提取扁平子句（各成独立 generator，源序插在本真子句之前），剩余窗口才是本子句 iter 表达式 |
| C3 | _parse_multi_for_comprehension 最内层元素窗（非三元分支） | 末真子句后、元素前的扁平子句消费（e2 多 for 版形态）；元素窗起点前移后交 _split_dict_comp_kv/元素重建 |
| C4 | _parse_comprehension_inner_impl 单 for 路径元素窗（非三元分支） | 单 for 路径同款消费（e2/e09 形——全式仅 1 个 FOR_ITER）；扁平 generator 按源序追加在真子句之后 |

### 4.3 判据与条款引用

- 判据（I.4 白名单）：**块内指令 opcode 序**（扁平对签名 = 表达式构造 opcode 前缀 +
  STORE_* 终结、无迭代协议/跳转/追加/COPY；目标存储序列结构 = _parse_target_store_sequence
  既有 UNPACK 栈结构判据）。无文件/函数名白名单、无偏移阈值、无跨层反查、无新 self 状态、
  无计数上限。
- 条款：C1（扁平子句在推导式 code object 指令流层识别，不回溯外层）；C2（扁平子句作为
  独立 comprehension 生成元被父推导式黑箱消费，源序保持）；C3（三处挂载点均为「不命中时
  窗口起点不变」的显式守卫——普通多 for/单 for/含 walrus 元素的推导式行为逐位保持，
  f8/f9/f10 负对照实测）。修复语义 = 封闭守卫恢复无感（I.3 推论）：判据对任意子句位置
  （中位/末位）、任意表达式形态（名/下标/调用/容器字面量）、任意推导式种类
  （list/set/dict/genexpr）、任意扁平链长同判。
- **CPython 3.11 codegen 不变式**（C1 判据成立基础）：单元素**列表字面量**子句内联 ⇔
  `<expr>; STORE T` 扁平对；≥2 元素列表不内联（f10 实测真 FOR_ITER 循环）。walrus 不可能
  出现在推导式 iterable 表达式（CPython 语法层禁止，f8 源级 SyntaxError 实证）——COPY
  守卫纯为防御性封闭。

### 4.4 docstring 合规声明（I.7）

- _b113_extract_flat_clauses（新增）：六项模板齐全（①CPython 3.11 内联不变式 + I.1 原则 4
  ②两窗自左向右贪心、消费后窗口前移③表达式构造 opcode 前缀 + STORE 终结 + COPY/协议
  opcode 终止扫描的唯一归属判定④连续扁平独立节点源序组合⑤(target, Tuple[expr]) →
  generators 的 AST 映射接口⑥多 for 推导式重建子句收集步流程位置）+ [C1][C2][C3]。
- C2/C3/C4 以行内注释块声明 [B113] 判据来源与 C3 守卫；所属方法既有 docstring 未改动
  （_parse_multi_for_comprehension 的 [Round5-B20/B23] 六项模板结构保持原样）。

### 4.5 验证（代码已落地读数）

- 探针：B113_min 6/9 → **9/9**；B113_host 12/14 → **14/14**
  （r8v8fixB_repro_c_b113_try2.json）。
- 攻击面全量：**314/357**（自 B102 终态 309/357 +5），BETTER={B113 两探针}，**NEWFAIL=0**
  （r8v8fixB_repro_c_b113_full.json 逐条目比对）。
- 变体电池（本批新建 	est_repros/round8/r8v8fc_b113_flat_battery.py 10 形态 21 units）：
  **21/21 全 success**——f1（三扁平+真子句链）、f2（扁平含调用 h(a)）、f3（扁平含容器
  字面量 [1,2]）、f4（过滤后扁平）、f5（set 推导式扁平）、f6（dict 推导式双扁平）、f7
  （genexpr 扁平）、f8（**walrus 元素负对照**——COPY 守卫不误判）、f9（双常量真子句
  负对照）、f10（**2 元素列表负对照**——不内联，真 FOR_ITER 保持）。
- 站桩 6 面：round1face **417/423**、round2face **239/251**、probe42 **177/196**、
  residual **419/446**、oldface **665/692**、quotation **152/153**——与 B102 终态逐位
  持平，WORSE = 0。
- 34 集 8 分片：**1505/1568 NEWFAIL=0**。

### 4.6 B110 划除确认（任务序 6，REVIEW §4）

REVIEW §4 B110 行：「多上下文 with 含 return→多余 return None……建议封闭批以独立负对照
正式确认后划除」。B113_host（= c4_05_multi_with 面）现 **14/14 success**——c4_05 的全部
失败单元（e09_comp_host + .\<listcomp\>）均归 B113 族并已封闭，B110 面内无残余失败单元。
**B110 自残余破口清单正式划除**（本轮无新证据推翻 round4 登记定性，round8 REVIEW §4 的
划除条件成立）。

### 4.7 残余如实登记

- 三元元素 × 前导扁平子句共存形态（`[x if p else y for a in xs for b in [k]]`）：单 for
  路径的三元分支（_detect_comp_ternary 命中时）未挂扁平消费——三元检测窗含扁平前缀可能
  干扰三元表达式重建。该形态不在本轮探针面（探针协议未覆盖），登记为 B113 族残余子形态，
  移交后续批次（判据方向：三元检测窗起点先经 C1 消费前移）。


---

## §5 B96 — async 推导式误生成 + 内层 code object 丢失（已封闭）

### 5.1 破口机理（两残余位，判据全部 I.4 白名单）

- **a_three（`acc.extend({k: await g2(v) for k, v in d.items() if v})`）**：含 await 的推导式
  code object 被 CPython 置 CO_COROUTINE 位（0x93），调用点自动补发 GET_AWAITABLE
  + SEND 轮询协议。区域装配层把该协议重建为 `Await(推导式)` 包装——源码不可能
  显式写 `await(<推导式>)`（推导式求值为容器不可 await，唯一合法形态即 async
  推导式的隐式协议），此包装必须剥除，否则发射 `acc.extend(await ({...}))`
  （误生成）。既有 [Round2-B96] 剥除只认 `value.type == 'Call'`（ComprehensionObject
  泄漏形态），a_three 的推导式已在区域层转为 DictComp dict——剥除判据失配。
- **a_four.\<genexpr\>（`sum(1 for x in xs if await g2(x))`）**：含 await 的
  \<genexpr\>（co_flags 0x213 = CO_ASYNC_GENERATOR）内，用户级 await 的挂起协议
  （GET_AWAITABLE; LOAD_CONST None; SEND; YIELD_VALUE; RESUME;
  JUMP_BACKWARD_NO_INTERRUPT 回 SEND）先于元素产出执行。_find_comp_append_op
  的 YIELD_VALUE 回退取**首个** YIELD——await 轮询 YIELD 被误当元素产出锚点 ⇒
  过滤窗错位：元素 1 丢失、await 表达式错位为元素（实测 `sum((await g2(x)
  for x in xs))`）。

### 5.2 修复锚点（代码已落地，I.6；comprehension_generator.py + ast_converter.py）

| # | 锚点 | 内容 |
|---|------|------|
| D1 | comprehension_generator.py _build_comp_result（单一组装点）+ 类常量 _B96_ASYNC_COMP_FLAG_MASK | [B96] async 推导式标注：co_flags（CO_COROUTINE=0x80 / CO_ASYNC_GENERATOR=0x200，inspect 常量 + 3.11 实测：async \<listcomp\>/\<setcomp\>/\<dictcomp\> 恒 0x93、含 await \<genexpr\> 恒 0x213）命中即标注 is_async_comp。该方法是一切推导式 dict 的唯一组装点（convert_comprehension_objects / 表达式重建 / generate_comprehension_function 三路汇聚），单点全覆盖 |
| D2 | st_converter.py _convert_await_expr_full | [B96] 推导式 dict 形态的同款剥除：value ∈ {ListComp,SetComp,DictComp,GeneratorExp} ∧ is_async_comp 标注 ⇒ 剥除 Await 返回推导式本体；未标注（同步推导式）保持 ASTAwaitable（用户级 await 语义保真，C3 显式豁免——`await [x for x in xs]` 形为合法源码，不可无条件剥除） |
| D3 | comprehension_generator.py _find_comp_append_op | [B96] async genexpr 元素产出 YIELD 识别：跳过轮询回环 YIELD（YIELD; RESUME; JUMP_BACKWARD_NO_INTERRUPT 收尾 = await 挂起协议；元素产出 YIELD 以 RESUME + POP_TOP/JUMP_BACKWARD 收尾，无 NO_INTERRUPT 回环），取首个非协议 YIELD 为 append 锚点。同步 genexpr 无协议 YIELD，行为逐位不变（C3） |

### 5.3 判据与条款引用

- 判据（I.4 白名单，全锚点）：**code object 元数据**（co_flags 的 CO_COROUTINE/
  CO_ASYNC_GENERATOR 位——任务 B96 判据方向「COMPILER_FLAG_ASYNCGEN 白名单」；
  CO_* 常量语义 = inspect 模块权威定义）；**块内指令 opcode 序**（await 轮询协议
  签名 = SEND 回环；GET_AWAITABLE/YIELD_VALUE 序——与 B112 判据同源）。无文件/函数
  名白名单、无偏移阈值、无跨层反查、无新 self 状态、无计数上限。
- 条款：C1（剥除判据在转换层读推导式 dict 的 co_flags 标注——元数据在判据所在层
  消费；YIELD 锚点判据在推导式指令流层）；C2（推导式经黑箱解析后仅以 dict +
  标注接口被转换层消费）；C3（同步推导式 / 无协议 YIELD 的同步 genexpr 显式豁免，
  逐位不变）。
- **CPython 3.11 codegen 不变式**（判据成立基础）：推导式含 await 或 async for ⇔
  co_flags 置 CO_COROUTINE（0x80）/ CO_ASYNC_GENERATOR（0x200）⇔ 调用点自动补发
  GET_AWAITABLE+SEND（源码不可显式写 await(<推导式>)——推导式求值为容器不可
  await）。双向可区分：同步推导式位为零 + 用户级 await 必须保留 ASTAwaitable。

### 5.4 docstring 合规声明（I.7）

- D1/D3 以行内注释块声明 [B96] 判据来源（inspect 常量 + 实测口径 + codegen 不变式）
  与 C 条款；_build_comp_result 既有结构保持。D2 在 _convert_await_expr_full 的
  [Round2-B96] docstring 之后以行内注释块增补推导式 dict 形态段（识别条件/归约方式/
  AST 映射/C 条款与既有 Call 形态同构），既有六项模板 docstring 结构未破坏。

### 5.5 验证（代码已落地读数）

- 探针：B96_async 11/13 → **13/13 success**（r8v8fixB_repro_c_b96_try2.json）。
- 攻击面全量：**316/357**（自 B113 终态 314 +2），BETTER={B96_async}，**NEWFAIL=0**
  （r8v8fixB_repro_c_b96_full.json 逐条目比对）。
- 变体电池（本批新建 	est_repros/round8/r8v8fc_b96_async_battery.py 9 函数 18
  units）：**14/18**——b1（a_three 同形）、b2（await 元素+过滤）、b4（a_four 同形）、
  b5/b6（set/dict comp await 元素裸 return）全转 success；b3/b7（**async-for 推导式
  裸 return** + 闭包内 async-for 推导式）= B112 e07 同机制残余（见 §6 移交），修复前
  同败、本批未回退。


---

## §6 B112 拆分 — ① yield await 语义丢失 / ② async 闭包推导式蒸发（部分移交）

### 6.1 调查结论与移交登记（如实，判据全部 I.4 白名单）

B112 两残余位经三轮插桩追踪（r8c_patchtest/_generate_block_statements_body/
_b31_await_chain_gate 逐块 trace），根因均落在 **[Round6-B31] await 挂起协议链
消费门**（region_ast_generator.py）与 **ExpressionReconstructor 平铺流重建**
（ast_generator_v2.py——本批禁改文件），非本批授权文件（comprehension_generator /
ast_converter / code_generator）内可及：

- **e05_async_compound.go（`yield await c`）**：字节码 = `LOAD c; GET_AWAITABLE;
  LOAD_CONST None; [SEND; YIELD_VALUE; RESUME; JUMP_BNI 轮询]; ASYNC_GEN_WRAP;
  YIELD_VALUE; RESUME; POP_TOP`。await 的轮询 YIELD 与产出的 YIELD 相邻同链——
  语句走查把 setup 块并入 await 消费后，产出段的 `ASYNC_GEN_WRAP; YIELD_VALUE`
  不再生成 Yield 节点（输出只剩 `await c` 语句，yield 语义整条丢失）。已排除
  方向：①comprehension_generator 无推导式参与，无处落锚；②ast_converter 收到的
  dict 里 Yield 节点已不存在（区域层丢失，转换层无从重组）；③code_generator 只
  渲染现存节点。判据方向（供后续批次）：gate/await-setup 消费链时若 owner 去噪
  指令含 ASYNC_GEN_WRAP+YIELD_VALUE 序（yield await 复合签名，B112 任务判据 =
  GET_AWAITABLE/YIELD_VALUE opcode 序），owner 重建必须保留 Yield 包裹——
  `Expr(Yield(value=Await(c)))`。
- **e07_async_closure.outer.inner（`return [v async for v in gen]`）**：bare
  return 的 async-for 推导式 = await 链 owner（RETURN_VALUE 消费挂起值）——
  _b31_await_chain_gate 在 generate() 收尾毯式标记处命中（实测 blk@42 FIRE），
  把全链合并流交 _build_statements_from_instructions → ExpressionReconstructor
  平铺重建：GET_AITER 无处理器、MAKE_FUNCTION 推导式常量被丢弃 ⇒ `return gen()`
  幻影 + .\<listcomp\> Missing bytecode（内层 code object 未产出）。语句走查
  （_generate_block_statements_body）从未对 setup 块（blk@4）调用
  	ry_generate_comprehension_assign（实测该块被 await-setup 分支先行消费，
  返回 []）。已排除方向：①b96 变体电池 b5/b6（GET_ITER 形 await 元素推导式裸
  return）经既有推导式认领路径通过——GET_AITER 形（async-for）独有的失配；
  ②ast_converter 侧无 ComprehensionObject 泄漏可救（MAKE_FUNCTION 在平铺重建
  中已被丢弃，转换层收不到 code 常量）；③comprehension_generator 的
  	ry_generate_comprehension_assign 具备 GET_AITER 处理能力（:412 判据在），
  但无调用点可及。判据方向（供后续批次）：B31 gate 合并流含「推导式
  MAKE_FUNCTION + GET_AITER/GET_ITER + CALL」签名时（_const_code_is_async_
  comprehension 已有编译器合成名判据）改道 comp_generator.try_generate_
  comprehension_assign 认领，或 await-setup 消费前先让推导式认领——判据均在
  region_ast_generator.py 落地。
- **同机制外溢面（b96 电池实测）**：b3（`return [await h(x) async for x in xs]`
  裸 return async-for 推导式）/ b7（async 闭包内同形）= e07 同根，修复前同败、
  本批未回退（14/18，b3/b7 两形 4 units 残余）。
- **B112 ① 的 b96 域同源部分已随 §5 封闭**：a_four.\<genexpr\>（任务 B112 拆分
  ②的 Missing bytecode 侧之一）经 D3 修复转 success——e07.\<listcomp\> 的
  Missing bytecode 是 e07 主体丢失的伴生（同根同移交）。

### 6.2 读数与登记

- B112_async：21/24 → **21/24 维持**（e05_async_compound.go、e07_async_closure.
  outer.inner、e07.\<listcomp\> 三单元移交，机制与判据方向如上；NEWFAIL=0）。
- 本批 B112 涉改文件：无（调查零落地代码；b96 域同源修复见 §5）。


---

## §7 B106 — star_args 多星/非尾星重排或丢失（已封闭）

### 7.1 破口机理（四层链路取证，判据全部 I.4 白名单）

插桩取证（区域 dict dump → 转换层 trace → 发射层 diff）确立：**区域装配层的
Call dict 对全部 B106 形态均正确**（e02 dict = Call(f, args=[Starred(x), 1])、
e04 dict = args=[Starred(xs), Starred(ys)]、lam_star lambda dict 的 arguments
vararg='a'——实参序/多星/形参全保真），丢失发生在**授权域内**的转换/发射/推导式
锚定层，共四处：

1. **转换层 var 槽抽取（ast_converter._convert_call_full）**：dict args 内的
   Starred 被抽到 ASTCall.var——单槽位（多星后者覆盖前者 ⇒ e04 的 \*xs 蒸发）
   且渲染恒在尾（⇒ e02 `f(*x, 1)` 重排为 `f(1, *x)`，重编译 BUILD_LIST
   追加序倒置，字节级发散）。
2. **lambda varargs 形参丢失（ast_converter._convert_lambda_expr）**：region 层
   arguments dict 已携带 vararg（CO_VARARGS 位形参），但无默认值时走旧扁平化
   路径（只读位置形参列表）⇒ `lambda *a: a` 退化为 `lambda: a`（lam_star
   .\<lambda\> code object 发散）。
3. **推导式元素产出锚点误置（comprehension_generator._find_comp_append_op）**：
   星实参调用形元素的实参构建段含内层 BUILD_LIST 0 + LIST_EXTEND + LIST_APPEND
   （CALL_FUNCTION_EX 协议）——首个 LIST_APPEND 属内层实参构建，被误当元素产出
   锚点 ⇒ 元素窗错位、Call 整体蒸发（st_comp 实测元素退化回退 Name(target)，
   v9 genexpr 同形）。
4. **dict comp 键/值切分点栈模拟缺口（comprehension_generator._find_dict_kv_
   split_point / _get_stack_delta）**：CALL_FUNCTION_EX 协议族（PUSH_NULL/
   LIST_EXTEND/LIST_APPEND/CALL_FUNCTION_EX）与 BUILD_LIST 0（arg=0 时旧
   `if instr.arg else 0` 守卫记 delta=0，实为 +1）未入模拟 ⇒ 深度历史全程
   偏低 ⇒ 星实参键窗切分失败（v8 实测键窗截到 BUILD_LIST 0 → 键退化为 []）。

### 7.2 修复锚点（代码已落地，I.6；ast_converter.py + comprehension_generator.py）

| # | 锚点 | 内容 |
|---|------|------|
| F1 | st_converter.py _convert_call_full 实参循环 | [B106] star 实参保序转换：Starred 保留在 pparams 位置实参序内（经 _convert_expression 落 Starred dict，发射层按位渲染 *expr）。判据 = dict args 的 Starred 成员事实（CALL 前操作数块序，I.4 白名单）；旧 var 槽路径退役为本修复覆盖（同步推导式单尾星等价形渲染同构） |
| F2 | st_converter.py _convert_lambda_expr B25 门扩展 | [B106] lambda *args/**kwargs 形参保真：arguments dict 的 vararg/kwarg 成员存在时同样携带 _args_dict 走 _generate_arguments_dict 渲染（该渲染器 vararg/kwarg 分支既有）；两者皆无时保持旧扁平路径（C3） |
| F3 | comprehension_generator.py _find_comp_append_op 新增 append_kind 参数 + 两调用点 | [B106] 元素产出锚点按推导式种类精化（co_name → 产出 opcode：listcomp→LIST_APPEND/setcomp→SET_ADD/dictcomp→MAP_ADD/genexpr→YIELD_VALUE），取该 opcode 的**最末**出现（元素产出是循环体最后一条有效指令，其后即回边；内层实参构建的 LIST_APPEND 恒在其前；async 轮询 YIELD 恒在元素 YIELD 之前，与 §5 D3 判据结论一致）。普通形态首=末，行为逐位不变（C3） |
| F4 | comprehension_generator.py _find_dict_kv_split_point 协议族 delta + _get_stack_delta BUILD_* 0 修正 | [B106] CALL_FUNCTION_EX 协议族栈效应入模拟（PUSH_NULL=+1；CALL_FUNCTION_EX=-(3+kwargs位)+1；LIST_EXTEND/LIST_APPEND/DICT_UPDATE/DICT_MERGE/SET_UPDATE=-1）+ BUILD_* n 弹 n 压 1 的 arg=0 修正（1-(arg or 0)）。判据 = opcode 栈效应（I.4 白名单） |

### 7.3 判据与条款引用

- 判据（I.4 白名单，全锚点）：**CALL 实参序列指令 oparg 序**（任务 B106 判据方向：
  dict args 的 Starred 成员 = CALL 前操作数块序的保序事实，转换层不得重排/去重）；
  **code object 元数据**（co_name → 推导式产出 opcode；lambda arguments 的
  CO_VARARGS/CO_VARKEYWORDS 位形参——region 层既有产物，转换层只读消费）；
  **块内指令 opcode 栈效应**（协议族 delta）。无文件/函数名白名单、无偏移阈值、
  无跨层反查、无新 self 状态、无计数上限。
- 条款：C1（四层各自在判据所在层修复——实参序在转换层保真、形参在转换层携带、
  锚点/切分在推导式指令流层精化，均不回溯区域层——区域层 dict 本已正确）；
  C2（Starred/lambda 形参经 dict 接口黑箱传递，发射层只按位渲染）；C3（单尾星
  等价形 / 普通推导式首=末 / 无 vararg-kwarg lambda / 无星实参键窗——四类既有
  形态显式豁免，行为逐位不变）。
- 注：区域装配层（ast_generator_v2 ExpressionReconstructor 的 CALL_FUNCTION_EX
  栈机）对 B106 全部探针形态产出正确 dict（本轮取证结论），零改动——B106 不涉
  禁改文件。

### 7.4 docstring 合规声明（I.7）

- F1/F2/F4 以行内注释块声明 [B106] 判据来源（操作数块序/形参布局元数据/opcode
  栈效应）、机理与 C 条款；所属方法既有 docstring 结构未破坏（_convert_call_full
  的 [Round2-B96] 六项段、_convert_lambda_expr 的 [Round5-B25] 段、
  _find_dict_kv_split_point 的 [R40 fix] 段保持原样）。
- F3 在 _find_comp_append_op 内以 [B106]/[B96] 注释块并列声明两判据（种类精化
  锚点 + async 轮询 YIELD 跳过），方法无整体 docstring（既有状态，本批未新增
  违规）。

### 7.5 验证（代码已落地读数）

- 探针：B106_main 7/13 → **13/13**；B106_call 4/13 → **13/13**；B106_lam
  26/27 → **27/27**（r8v8fixB_repro_c_b106_try3.json）。
- 攻击面全量：**332/357**（自 B96 终态 316 +16），BETTER={B106 三探针}，
  **NEWFAIL=0**（r8v8fixB_repro_c_b106_full.json 逐条目比对）。
- 变体电池（本批新建 	est_repros/round8/r8v8fc_b106_star_battery.py 12 函数 18
  units）：**18/18 全 success**——v1（双星）、v2（非尾星）、v3（首尾夹星）、v4
  （星+kw+双星 kw）、v5（全混合五实参）、v6/v7（星调用作 list/set 推导式元素）、
  v8（**星调用作 dict 推导式键+值双位**，F4 修复）、v9（星调用作 genexpr 元素，
  F3 修复）、v10（lambda *a/**kw + 星调用）、v11（星为尾部单值）、v12（星为
  调用表达式 *gen()）。
- 站桩 6 面：round1face **417/423**、round2face **239/251**、probe42 **177/196**、
  residual **419/446**、oldface **665/692**、quotation **152/153**——与 B96 终态
  逐位持平，WORSE = 0。
- 34 集 8 分片：**1505/1568 NEWFAIL=0**。
- 其余变体电池复核：b102_battery 8/10（ideg/pin 残余维持）、b113_flat 21/21、
  b96_async 14/18（b3/b7 = §6 移交残余维持）、b106_star 18/18——无回退。

---

## §8 自测门禁读数（位C续作全批终态，收尾段采集）

### 8.1 攻击面 31 探针对比表

before = `r8v8fixB_repro_final.json`（位B批终态）；after = `r8v8fixB_repro_c_b106_full.json`
（位C续作第四段终态，30 条目）；cfinal 复核 = `r8v8fixB_repro_cfinal.json`（第五段插桩
清零后 13 探针重跑，读数与 after 逐位一致）。

| 探针 | before | after | 判定 |
|------|--------|-------|------|
| B108_main | 14/14 | 14/14 | SAME |
| B99_min | 9/9 | 9/9 | SAME |
| B104_main | 14/14 | 14/14 | SAME |
| B105_main | 13/13 | 13/13 | SAME |
| B105_call | 12/12 | 12/12 | SAME |
| B107_main | 14/14 | 14/14 | SAME |
| B111_main | 28/28 | 28/28 | SAME |
| B111_cross | 22/22 | 22/22 | SAME |
| B98_matrix | 7/15 | 7/15 | 维持（登记移交） |
| B98_hosts | 13/18 | 13/18 | 维持（登记移交） |
| B98_resid | 2/5 | 2/5 | 维持（登记移交） |
| B78_face | 1/4 | 1/4 | 维持（登记移交） |
| B79_face | 3/4 | 3/4 | 维持（登记移交） |
| B80_face | 2/3 | 2/3 | 维持（登记移交） |
| B82_face | 2/3 | 2/3 | 维持（登记移交） |
| B83_face | 2/2 | 2/2 | SAME |
| B77_face | 8/8 | 8/8 | SAME |
| B81_face | 3/4 | **4/4** | **BETTER** |
| B103_main | 10/13 | **13/13** | **BETTER** |
| B103_guard | 5/8 | **8/8** | **BETTER** |
| B102_main | 12/13 | **13/13** | **BETTER** |
| B102_except | 5/8 | **8/8** | **BETTER** |
| B102_deep | 9/10 | **10/10** | **BETTER** |
| B113_min | 6/9 | **9/9** | **BETTER** |
| B113_host | 12/14 | **14/14** | **BETTER** |
| B96_async | 11/13 | **13/13** | **BETTER** |
| B112_async | 21/24 | 21/24 | 维持（§6 移交三单元） |
| B106_main | 7/13 | **13/13** | **BETTER** |
| B106_call | 4/13 | **13/13** | **BETTER** |
| B106_lam | 26/27 | **27/27** | **BETTER** |
| **合计（30 条目）** | **297/357** | **332/357** | **+35，NEWFAIL=0** |

- BETTER 12 项全表如上；NEWFAIL = **0**（其余条目全 SAME/维持，WORSE 无）。
- 第 31 探针 = `r8v8fc_b81_t2_wildguard`（b09c23f3 已入库独立探针）：**3/3 success**
  （本段收尾复核实测）——31 探针面合计 **335/360**。

### 8.2 站桩 6 面 + 34 集

- **cfinal 收尾复核（插桩清零后重跑，读数逐位一致）**：quotation **152/153**（残余 =
  change_his_to_forward）、round1face **417/423**（残余 = trade_info_utils 36/41 +
  quotation 面 1）、round2face **239/251**、probe42 **177/196**——四面 WORSE 全部 = 0。
- residual **419/446**（252/277 + 167/169）、oldface **665/692**（218/227 + 447/465）：
  第四段 M 态证据（`r8v8fixB_full_residual_a/b.json`、`r8v8fixB_full_oldface_a/b.json`，
  采集时点 2026-10-11 19:00-19:02，插桩 env 门控默认关在案树）。本段复跑触及 300s
  纪律线即中止（23/72 处），未产生新 JSON；行为同一性由 13 探针 + 上述四面 cfinal
  逐位复核背书，读数沿用有效（详见 §10.3）。
- 34 集 8 分片：**1505/1568，NEWFAIL=0**（`r8v8fixB_34set_shard0-7.json` 第四段 M 态
  证据沿用，采集时点同上）。

### 8.3 IV.2 门禁自检（收尾段）

- **py_compile**：七涉改文件全过（pattern_parser / exception_handler /
  comprehension_generator / code_generator / ast_converter / region_analyzer /
  region_ast_generator，exit=0）。
- **import 自检**：`core.cfg.region_analyzer` / `region_ast_generator` /
  `ast_converter` / `comprehension_generator` / `pattern_parser` /
  `exception_handler` / `code_generator` 全部 import OK。
- **BOM**：code_generator.py 无 BOM（首 3 字节 222222，存量不改）；pattern_parser.py
  222222、exception_handler.py 696d70、ast_converter.py 222222、
  comprehension_generator.py 66726f 无 BOM（存量）；region_analyzer.py /
  region_ast_generator.py 首 3 字节 **efbbbf**（单 BOM 存量保持）。注：前段中断写入
  曾引入双 BOM（efbbbf×2）致 py_compile 失败（U+FEFF），本段修复恢复存量单 BOM。
- **grep `R8CDBG`**：**零命中**（含配套 `import os as _os_r8*` 行；前段中断遗留 6 处
  print + 4 处孤立 import 及其参数续行共 28 行清零，env 门控默认关 ⇒ 删除 = 零行为
  变更，cfinal 复核背书）。
- **G3**：无新增 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀
  方法（`git diff core/` 新增 def = _b113_extract_flat_clauses /
  _b102_chain_reachable_blocks / _b102_degenerate_chain_pairs_finally /
  _b102_cleanup_target_of（嵌套）/ _find_star_else_blocks，另 _find_comp_append_op /
  _find_star_else_blocks 同名族既有触及——均族标记/描述性命名，无违禁前缀）。
- **G4**：无新增硬编码深度/计数上限（BFS/行走终止性全部由有限块集 + 已访集保证；
  `_b102_a_max = max(块偏移)` 为数据计算值非上限；CO_COROUTINE=0x80 /
  CO_ASYNC_GENERATOR=0x200 为 inspect 常量元数据白名单，非深度/计数门）。
- **命令纪律**：全部命令 ≤300s（residual 面复跑 300s 触顶即中止，如上）。

---

## §9 代码已落地声明（I.6 汇总，行号 = 收尾终态树实测）

六族标记 grep 核验：`[B81` / `[B103` / `[B102` / `[B113` / `[B96` / `[B106]` 于
`core/` 全命中 **74 处**（comprehension_generator.py 18、region_analyzer.py 26、
pattern_parser.py 22、region_ast_generator.py 5、ast_converter.py 3），与下表逐条
对应；六族全封闭（B112 §6 调查零落地代码）。

| 族 | 锚点（§小节 → file:line 终态树） |
|----|----------------------------------|
| B81（§1.2 F1-F4） | F1 region_analyzer.py:17193（`_scan_literal_match_subjects` 链行走 and-guard 链，:17210 同族外推注释）；F2 pattern_parser.py:351/:452（`_extract_case_guard_from_blocks` (c) 纯字面量头锚）；F3 region_analyzer.py:2172（`_b74_guard_arm_targets_case_body` docstring [B81 细化]）+:2293（fail 边同一性）+:2260（重放同步）；F4 三调用点 region_analyzer.py:14880+:14893 / :16758+:16771 / :17324+:17337 |
| B103（§2.2 G1-G11） | G1 pattern_parser.py:1536（`_extract_case_pattern` or 臂链材料扩展）；G2 pattern_parser.py:1209（`_pure_jf_argval`）+:1224（`_collect_or_arm_chain_instrs`）；G3 pattern_parser.py:307（guard_like 续块守卫链边界）；G4 region_analyzer.py:15981（`_mr_collect_case_body` or-guard 链）+:17210（字面量扫描侧）；G5 region_analyzer.py:15766（`_mr_skip_case_connectors` 宿主连接桩）；G6 region_analyzer.py:15958+:17181（末 case 支配检查）；G7 region_analyzer.py:17159（字面量 or 臂链解析）+:14800（G8 候选循环子链去重）+:15805（G9 支配种子 with 宿主边界）；G10 region_ast_generator.py:35322+:35352（`_generate_with` 消费门 MatchRegion，跨文件锚）；G11 region_ast_generator.py:37557（`_generate_match` 体块 WithRegion 分支，跨文件锚）。t2 附注（b09c23f3 同批封闭）：pattern_parser.py:424（(b') 通配丢弃锚）+:1516；region_analyzer.py:17488（`_mr_head_has_wildcard_discard`）+:2239（重放同步） |
| B102（§3.2 E1-E7） | E1 region_analyzer.py:8908（[B102-fix2] 退化链配对）；E2 region_analyzer.py:8607（`_b102_degenerate_chain_pairs_finally`）+:8568（`_b102_chain_reachable_blocks`）+:8649（`_b102_cleanup_target_of`）+:8548（`_B102_ZONE_FRAME_OPS`）；E3 region_analyzer.py:10010（[B102-fix1] 星链 else 门控）；E4 region_analyzer.py:11992（`_find_star_else_blocks`）；E5 region_analyzer.py:9898（[B102-fix1b] 框架清理）；E6 region_analyzer.py:10171（[B102-fix3] 退化嵌套）；E7 region_ast_generator.py:35373+:35512（[B102 with 宿主 else 镜像误杀收紧]——**位B域跨文件锚**（发射补丁），调 `_b102_chain_reachable_blocks` :8568 判据） |
| B113（§4.2 C1-C4，全 comprehension_generator.py） | C1 :1892（`_b113_extract_flat_clauses`，docstring :1894）；C2 :1487（真子句 iter 窗前导扁平消费）；C3 :1574（最内层元素窗扁平消费）；C4 :1225/:1254/:1291（单 for 路径元素窗扁平消费） |
| B96（§5.2 D1-D3） | D1 comprehension_generator.py:119+:136（`_B96_ASYNC_COMP_FLAG_MASK`）+:2868（`_build_comp_result` 单点标注）；D2 ast_converter.py:1826（`_convert_await_expr_full` 推导式 dict 形态剥除）；D3 comprehension_generator.py:2048（`_find_comp_append_op` async 轮询 YIELD 跳过） |
| B106（§7.2 F1-F4） | F1 ast_converter.py:1362（`_convert_call_full` star 实参保序）；F2 ast_converter.py:1925（`_convert_lambda_expr` vararg/kwarg 形参保真）；F3 comprehension_generator.py:2027（`_find_comp_append_op` append_kind 种类精化）+:1169/:1405（两调用点）；F4 comprehension_generator.py:1696/:1699/:1709（CALL_FUNCTION_EX 协议族 delta）+:1764（BUILD_* n 的 arg=0 修正） |
| B112（§6） | 无落地代码（调查零落地；机制与判据方向在案，移交 §10.1） |

- 位B域跨文件锚显式登记：region_ast_generator.py 的 B102 发射补丁（E7，
  :35373/:35512）——判据本体 `_b102_chain_reachable_blocks` 在 region_analyzer.py:8568。
- region_analyzer.py 在途 hunk（对 b09c23f3 增量 +340/-47，含插桩清零 -19 行）：B102
  六锚（E1-E6）、B103 G4-G9、B81 F1/F3/F4、t2 两锚、B17/B103 宿主边界段（:15805 一带）。
- pattern_parser.py / exception_handler.py / code_generator.py 全部锚点已提交于
  b09c23f3（本段零改动，工作树非 M）。

---

## §10 未竟项与移交

1. **B112 三单元移交**（§6 机制与判据方向在案）：e05_async_compound.go（`yield await c`
   复合）、e07_async_closure.outer.inner、e07.\<listcomp\>。根因 = **[Round6-B31] await
   挂起协议链消费门**（region_ast_generator.py，非位C续作授权域）+ **ExpressionReconstructor
   平铺重建**（ast_generator_v2.py，禁改文件）。判据方向在案：①gate/await-setup 消费链
   owner 去噪指令含 ASYNC_GEN_WRAP+YIELD_VALUE 序（yield await 复合签名）时 owner
   重建必须保留 `Expr(Yield(value=Await(c)))` 包裹；②B31 gate 合并流含「推导式
   MAKE_FUNCTION + GET_AITER/GET_ITER + CALL」签名时改道
   `try_generate_comprehension_assign` 认领（或 await-setup 消费前先让推导式认领）。
   伴生面：b96 电池 b3/b7（async-for 推导式裸 return 同根，4 units）。B112_async
   **21/24 维持**。
2. **已登记邻接残余**（各节在案，本批未回退）：B102 ideg / pre_inner（R86 延迟判据的
   「前导 try_blocks」应排除纯胶水块，块内指令序白名单可表达）；B113 三元元素 × 前导
   扁平子句共存形态（三元检测窗起点先经 C1 消费前移）；**B81 t2 形态已于 b09c23f3 同批
   封闭**（`r8v8fc_b81_t2_wildguard` 3/3，本段收尾复核实测；§1.5/§2.5 的 t2 残余登记
   段落为 61102a8d 时点历史记载，终态以本条为准）。
3. **站桩读数采集时点说明**：residual（419/446 = 252/277 + 167/169）与 oldface
   （665/692 = 218/227 + 447/465）两面证据采集于第四段（2026-10-11 19:00-19:02，
   `r8v8fixB_full_residual_a/b.json` / `r8v8fixB_full_oldface_a/b.json`，插桩 env
   门控默认关在案树）；34 集 8 分片（1505/1568）同为第四段 M 态分片证据
   （`r8v8fixB_34set_shard0-7.json`）。本段（第五段）插桩清零后行为同一性由 13 探针
   （r8v8fixB_repro_cfinal.json）+ quotation / round1face / round2face / probe42 四面
   cfinal 复核逐位一致背书——插桩为 env 门控默认关，删除 = 零行为变更，上述读数沿用
   有效。
4. **攻击面残余清单**（全部为已登记移交项，位C续作域外）：B98_matrix 7/15、
   B98_hosts 13/18、B98_resid 2/5、B78_face 1/4、B79_face 3/4、B80_face 2/3、
   B82_face 2/3、B112_async 21/24。
5. **涉改文件终态规模**（`git diff --numstat core/`，对 b09c23f3 增量，未提交）：
   ast_converter.py +48/-3、comprehension_generator.py +250/-13、region_analyzer.py
   +340/-47（含插桩清零 -19 行）、region_ast_generator.py +21/-14（含插桩清零
   -9 行）——4 文件合计 **+659/-77**；其中插桩清除 28 行，其余全部为 B102/B113/
   B96/B106 修复锚点（§9 表）。

