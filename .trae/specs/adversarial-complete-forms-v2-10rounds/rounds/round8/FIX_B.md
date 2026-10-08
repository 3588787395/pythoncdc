# Round 8 修复批 位B续作（发射域）修复报告（任务 8.2 · 批次二·续）

- 修复工程师子代理（位B续作·发射/装配域；前任位A/位B两批已完成并提交，HEAD=8f528733 承接）
- 工作树：`F:\Downloads\pythoncdc-main`（win32 / PowerShell 5.1 / python 3.11）
- 涉改文件边界遵守声明：`core/cfg/region_ast_generator.py`（发射/装配域）+ `core/cfg/ast_generator_v2.py`（表达式重建）+ `core/cfg/region_analyzer.py`（仅 B77/B78 判据族确需识别层协同时，锚 `_is_ternary_block`/`_identify_ternary_regions`；位A B121/B109 守卫未动）；禁改 pattern_parser.py / exception_handler.py / comprehension_generator.py / code_generator.py / ast_converter.py（位C域）
- 判据唯一：`scripts/pyc_verify.py`（ruler = pylingual equivalence_check；读数全部 RV2 口径 = 先 regen（pycdc -o）后 verify）
- 证据前缀：`r8v8fixB_*`（`rounds/round8/`）
- 零 git 写操作；探针 .py 源/pyc 零改动；regen 副作用结束时统一 `git checkout --` 还原

---

## §0 修复成果总览（增量维护，配额中断防丢）

| 序 | 族 | 探针 | before（after_b108_del 基线） | after | 状态 |
|----|----|------|------------------------------|-------|------|
| 0a | **B108**（try-finally-only finally 体复制/`del` 蒸发） | B108_main（c4_06） | 12/14 → **14/14**（前任位B落地；本批复验维持 + docstring 合规补正） | 14/14 | 封闭（前任落地，本批复验） |
| 0b | **B111**（decorator-with-args 退元组） | B111_main（c4_19）/ B111_cross（r5v5_12） | 27/28→**28/28**、21/22→**22/22**（前任位B落地；本批复验维持 + docstring 合规补正） | 28/28、22/22 | 封闭（前任落地，本批复验） |
| 1 | **B104** chained_compare | B104_main | 11/14 | （在途） | |
| 2 | **B105** walrus | B105_main / B105_call | 8/13、6/12 | （在途） | |
| 3 | **B107** multi_target | B107_main | 10/14 | （在途） | |
| 4 | **B99 残** for 宿主 BoolOp return | B99_min | 8/9 | （在途） | |
| 5 | **B98 拆分** 分组 boolop | B98_matrix / B98_hosts / B98_resid | 5/15、11/18、2/5 | （在途） | |
| 6 | **B77** match 臂三元 return | B77_face | 7/8 | （在途） | |
| 7 | **B78** 条件位融合三元 | B78_face | 1/4 | （在途） | |
| 8 | **B79** 嵌套双层 finally×continue | B79_face | 3/4 | （在途） | |
| 9 | **B80** finally 条件段×else import×handler return | B80_face | 2/3 | （在途） | |
| 10 | **B82** B75 残留两臂 return 互换 | B82_face | 1/3 | （在途） | |
| 11 | **B83** 循环体镜像块泄漏 finalbody | B83_face | 1/2 | （在途） | |

### §0.1 任务 0：插桩清零 + B108/B111 注释合规（已完成）

- **R8FIXBDBG 插桩 2 处已删**（region_ast_generator.py ≈L29115-29117 child walk print + ≈L31242-31246 finalbody legacy print，含 `_os_r8fb`/`_os_r8fb2` import 行）；grep `R8FIXBDBG` / `_os_r8fb` 全树零命中。
- **B108/B111 docstring 合规修正**（以代码真实算法为准，I.7；触及方法 4 个）：
  - `region_ast_generator.py _generate_try_body`（:27956 docstring）：③唯一归属判定补声明 [B108] finally 体 normal path 副本 ternary 跳过守卫（entry ∉ finally 块集 + 等块数 sibling ∈ finally 块集 ⇒ 副本 ⇒ 标记 generated 唯一归属 finalbody）+ handler/else 块集跳过守卫——原 docstring 未声明该行为，属「注释与代码行为不一致」，已修正注释。
  - `region_ast_generator.py _generate_handler_body_statements`（:31882 docstring）：③补声明 [B108] DELETE_FAST/NAME/GLOBAL/DEREF → Delete([Name(ctx='Del')])、DELETE_ATTR/DELETE_SUBSCR 经 _build_delete_stmt，及 as-var 清理守卫（本块内紧邻前驱 LOAD_CONST None + STORE 同名）不发射——原 docstring 未声明 DELETE 语句分支。
  - `ast_generator_v2.py _process_instruction`（:223）：docstring 由单行「处理单条指令」补齐六项模板 + C1/C2/C3（③声明 [B111] 加载指令族含 LOAD_CLOSURE/LOAD_CLASSDEREF；C2 声明与 _load_instr_to_ast 同集同语义）。
  - `ast_generator_v2.py _load_instr_to_ast`（:2388）：docstring 由单行补齐六项模板 + C1/C2/C3（③声明 [B111] cell 引用族，未知 opcode 显式占位符豁免）。
- **复验**：B108_main 14/14、B111_main 28/28、B111_cross 22/22 维持（`r8v8fixB_repro_task0_check.json`）。

---

## §1 B104：chained_compare（在途）

（待补）

---

## §2 B105：walrus（在途）

（待补）

---

## §3 B107：multi_target（在途）

（待补）

---

## §4 B99 残：for 宿主 BoolOp return（在途）

（待补）

---

## §5 B98 拆分：R1/R2/R3 + B44 存量（在途）

（待补）

---

## §6 B77：match case 臂内三元 return（在途）

（待补）

---

## §7 B78：条件位融合三元（在途）

（待补）

---

## §8 B79：嵌套双层 finally×continue（在途）

（待补）

---

## §9 B80：finally 条件段 × else 臂 import × handler return（在途）

（待补）

---

## §10 B82：B75 残留（在途）

（待补）

---

## §11 B83：try 体 while 内 raise 镜像块泄漏（在途）

（待补）

---

## §12 自测门禁读数（定稿前批量重放，在途）

（待补）

---

## §13 代码已落地声明（I.6）

（待补）

---

## §14 未竟项与移交（如实登记）

（待补）
