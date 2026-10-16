# Round 10 · 10.2 WIKI_REVIEW — wiki §8.2 复审六步全量重验与增量更新（评审实录）

- 执行：评审工程师（主代理验收）；日期：2026-10-17
- 复审对象：`wiki/concepts/decompile-invariant-completeness.md`（唯一权威总纲）+ 数字同步页 4 张（[[overview]] / [[index]] / [[syntax-audit-ledger]] / [[branch-coverage]]）+ [[log]]
- 树冻结：HEAD `3e0d6905a392c86361c2f75089ddd745755ff9d5`（rr-v2r10：10.1 全量终验 + VERIFICATION.md + WIKI_BRIEF.md）
- 纪律：零 `core/` 改动；只写 `wiki/` + `docs/refactor/syntax-coverage.json`（工具输出）+ `rounds/round10/`；每步实名实证；命令 ≤300s；python 一律 `python -X utf8`

---

## 步① fix 批归档落位确认

命令：`git rev-parse HEAD`、`git log --oneline origin/main`、`git merge-base --is-ancestor <sha> origin/main`（13 点抽样）、`git status --porcelain`

结果：

- HEAD = `3e0d6905`（rr-v2r10：10.1 全量终验套件）；`origin/main` = `0ad559519495a59285af01a7ae5b51dc8042e812`（rr-v2r09：9.4 验证 + 9.5 归档）
- **本规范 round1–9 全批次已在 origin/main 祖先链**（merge-base 逐点核验 **13/13 ANCESTOR-OF-origin/main**）：
  - 前序规范终态补推 `f831eeae`/`fc2aa1b1` ✓
  - round1 修复批 `a411d9d5`/`33d6e87e`/`12d7ddb9`（批次 A/B/C）✓
  - round8 归档 `91f8d27d`、merge gate `e42b8509` ✓
  - round9 修复 `58ed696b`/`3803fa73`/`42fe45fe` + 复核 `c1fa6fcf`/`c1a0c53f` ✓
  - 9.4/9.5 归档 `64314aed`/`9a3d681c`/`0ad55951` ✓
- round10 套件 `a8bc0abc`/`ea34ae03`/`3e0d6905` = 本地未推（推送属 10.3，本轮不 push）
- 工作树：除 `rounds/round10/` 证据件（未跟踪）外干净，无 `core/` 改动

判定：**落位确认通过**（round1–9 全部批次提交在 origin/main；round10 套件留待 10.3 推送）。

## 步② grep 全部落地标记（I.6 纪律）

- 命令式：`r10v10_marks_scan.py`（utf-8-sig 逐行包含匹配；范围 `core/**/*.py`；HEAD 3e0d6905 冻结树；结果 = `r10v10_wiki_marks.json`）
- 全表 **72 项**（round9 落地标记 12 + 应 0 命中 2 + 前八轮/历史批次 58）：**71 PASS / 1 FAIL**
- FAIL 唯 1 项：`_graft_pending_operand`（应 0 实 3）⇒ 见「异常节」（重大发现）
- 补充枚举（步②富证据，36 项，含 round1–8 批次抽样）：`r10v10_wiki_marks_supp.json`（已并入主 JSON `supplementary`）；要点——`[B71`×12（[B72`×1、[B73`×3、[B74`×5、[B75`×8、[B76`×2、[B65`×2、[B46`×8、[B50`×3、[B82`×4、[B100`×6、[B104-R3]`×4、[R21-86`×8、[R76-A1`×12、`_cjb_skip_inline_if`×6、`_leading_operand`×6 均在树；`[B126-R1`/`_b126_claimed` 0 命中（9.3b 已移除，预期）；`[B88`/`[B93`/`[B94`/`[B97`/`[B99 收窄]` 0 命中为**无字面标签**（行以机制锚点登记，非落地缺口，逐项在案）

### 72 项全表（markers）

| 标记 | 命中（文件:行，前 3） | 数量 | 判定 | 说明 |
|---|---|---|---|---|
| `[B104-R9` | region_ast_generator.py:8643/8662/8753 等 5 处 | 5 | PASS | B104-R9 语句前缀变体/混合操作数求值段集扩门 |
| `[B104-R4]` | region_ast_generator.py:8758（1 处） | 1 | PASS | B104-R4 POP_TOP 表达式语句终结符（w3_nostore 封闭） |
| `_extract_recheck_store_stmts` | region_ast_generator.py:7381/8756/8762 等 5 处 | 5 | PASS | 路 A 多语句 STORE 边界抽取器因子化（六项 docstring） |
| `[B124-R1` | region_analyzer.py:19952/20063/20088 | 3 | PASS | B124-R1 自足 return 形扩门（分析器桶） |
| `_b124r1_chain_region_is_self_return` | region_analyzer.py:19953/20075/20087 | 3 | PASS | B124-R1 守卫方法（merge 块清理/协议族+RETURN_VALUE 终结） |
| `[B124-R2a` | region_ast_generator.py:46557/46701 | 2 | PASS | B124-R2a 连接清理对守卫（SWAP(2)+POP_TOP 邻接） |
| `[B124-R2b` | region_ast_generator.py:46678（1 处） | 1 | PASS | B124-R2b with 协议边界守卫（BEFORE_WITH 族） |
| `_ternary_host_call_prefix_span` | region_ast_generator.py:46537/46624/47391 | 3 | PASS | T19-4 宿主调用前缀跨度（e10/r8_10 病灶面） |
| `[B125-R1` | region_ast_generator.py:9056（1 处） | 1 | PASS | B125-R1 祖先链排除（_child_region_blocks_r23 调用侧） |
| `_child_region_blocks_r23` | region_ast_generator.py:9043/9048/9052 等 5 处 | 5 | PASS | B125 祖先/子区域区分扫描（R23 守卫族） |
| `[B126-R2` | region_analyzer.py:7914/8161/8411 | 3 | PASS | B126-R2 异常路径尾闩守卫 |
| `_b126r2_raise_only_trampoline_exit` | region_analyzer.py:7920/8174/8404 | 3 | PASS | B126-R2 守卫方法（RAISE_VARARGS/RERAISE 终点） |
| `[B126-R1` | —（0 命中） | 0 | PASS | B126-R1 认领集补守卫（9.3b 已按 REVIEW2 R-1 全量移除） |
| `_b126_claimed` | —（0 命中） | 0 | PASS | B126-R1 认领集变量（9.3b 已移除，应 0） |
| `[B106-R3` | comprehension_generator.py:1683（1 处） | 1 | PASS | B106-R3 LOAD_METHOD 净栈 +1 补 delta（round8 P0 回退修复） |
| `[B109` | region_analyzer.py:5909/6317/6495 | 3 | PASS | B109 while-else break 守卫（round4 落地） |
| `[B110` | —（0 命中） | 0 | PASS | B110 划除确认（round8 声明为划除，非落地项，应 0） |
| `[B112` | —（0 命中） | 0 | PASS | B112 await 链消费门（round4 开放破口，round8 部分移交——无落地声明，应 0） |
| `[B113` | comprehension_generator.py:1225/1254/1291 等 6 处 | 6 | PASS | B113 推导式 for 链回归修复（round8） |
| `[B118` | region_ast_generator.py:24502（1 处） | 1 | PASS | B118 else-break 三元化（round7） |
| `[B119` | region_ast_generator.py:3881/3891/3943 等 13 处 | 13 | PASS | B119 try 体 return 吞并（round7） |
| `[B120` | region_ast_generator.py:7021（1 处） | 1 | PASS | B120 loop_analyzer NOP 幻影（round7） |
| `[B121` | region_analyzer.py:1834/5214 | 2 | PASS | B121 while 条件守卫 if gate（round7） |
| `[B83` | region_ast_generator.py:33373/33432 | 2 | PASS | B83 try/finally+raise 吞并（round4 提出/round8 位B 落地） |
| `[B77` | region_ast_generator.py:40339/40447/41236 | 3 | PASS | B77 designated 臂值钻石重建（round8 位B） |
| `[B81` | pattern_parser.py:366/467/1413；region_analyzer.py:2172/2182/2260 等 12 处 | 12 | PASS | B81 match guard 字面量幻影（round8 位C） |
| `[B102` | region_analyzer.py:9674/10014/10034；region_ast_generator.py:39089/39228 等 9 处 | 9 | PASS | B102 except* handler 链（round4/round8 位C） |
| `[B96` | ast_converter.py:1826；comprehension_generator.py:119/136/2062 等 5 处 | 5 | PASS | B96 async 生成器（round8 位C） |
| `[B98-R1` | region_ast_generator.py:46956/48271/48293 | 3 | PASS | B98-R1 镜像极性共享块重建（round8 位B 部分封闭） |
| `[B82` | region_ast_generator.py:31529/31605/31612 等 4 处 | 4 | PASS | B82 臂 return 副本消费（round8 位B） |
| `[B103` | pattern_parser.py:31/251/322；region_analyzer.py:2239/16103/17069 等 34 处 | 34 | PASS | B103 or 守卫/try 体（round8 位C/R2） |
| `[B104-R2a` | region_analyzer.py:4744/4778/4804；region_ast_generator.py:7333/7405/8581 等 18 处 | 18 | PASS | B104-R2a while 条件 and 尾（round8 R2 批） |
| `_B104_CC_RECHECK_EVAL_OPS` | region_ast_generator.py:242/8827/8831 等 5 处 | 5 | PASS | B104-R2b 纯值求值白名单完备化（round8 声明锚点，常量定义+4 消费点） |
| `[B104-R2b` | —（0 命中） | 0 | PASS | B104-R2b 无字面标记（round8 声明锚点 = _B104_CC_RECHECK_EVAL_OPS，另列核验） |
| `[B105-R2` | region_ast_generator.py:61440（1 处） | 1 | PASS | B105-R2 walrus 消费点（round8 R2 批） |
| `[B107-R2` | region_ast_generator.py:63419/63489 | 2 | PASS | B107-R2 多目标赋值（round8 R2 批） |
| `[B117` | region_ast_generator.py:24215/24530/26799 等 12 处 | 12 | PASS | B117 挂起循环回边块认领（round7） |
| `[B75` | region_ast_generator.py:31302/31364/31427 等 8 处 | 8 | PASS | B75 try 宿主 global 消费（round1 批 B） |
| `[B72` | region_analyzer.py:2400（1 处） | 1 | PASS | B72 global 声明错位（v6 harden round10 封闭） |
| `[B71` | region_ast_generator.py:38/3825/3913 等 13 处 | 13 | PASS | B71 try/finally else 块（v6 harden round10 部分封闭） |
| `[B48` | region_analyzer.py:2299/2307/28413；region_ast_generator.py:48332/50343 等 6 处 | 6 | PASS | B48 else-try 边界（v6 harden round10 封闭） |
| `[B46` | region_analyzer.py:26306/26371/26869 等 8 处 | 8 | PASS | B46 If 条件嵌套（v6 harden round10 部分封闭） |
| `[B1b fix` | region_analyzer.py:20500/22020/31592 等 14 处 | 14 | PASS | B1 族五臂封闭（round1） |
| `_sb_has_body` | region_analyzer.py:20503/20512/21344 等 18 处 | 18 | PASS | B1 族 or 裸尾续接同一谓词 |
| `_block_is_continue_target` | region_ast_generator.py:3984/12952/12957 等 13 处 | 13 | PASS | B2 continue 守卫 |
| `[fix3-T1` | region_ast_generator.py:17296（1 处） | 1 | PASS | B3 共享尾守卫族 fix3-T1 |
| `[fix3-T6` | region_ast_generator.py:24480（1 处） | 1 | PASS | B3 共享尾守卫族 fix3-T6 |
| `[W23` | region_ast_generator.py:25314/57894 | 2 | PASS | B3 共享尾守卫族 W23 |
| `[R71-thenover` | region_ast_generator.py:29482/29487 | 2 | PASS | B3 共享尾守卫族 R71-thenover |
| `W14-C` | region_analyzer.py:24389/24398/34368 等 5 处 | 5 | PASS | B3 共享尾守卫族 W14-C（臂收集+汇合剪枝） |
| `[B99` | region_analyzer.py:21108/25606/25624 等 9 处 | 9 | PASS | B99 boolop 吸收收窄/残（round3-8） |
| `[B100` | region_ast_generator.py:768/36959/37198 等 6 处 | 6 | PASS | B100 import 深嵌套（round4） |
| `[B101` | region_ast_generator.py:779/1335/19038 等 4 处 | 4 | PASS | B101 star import（round4） |
| `[B114` | region_ast_generator.py:12616/12743/37418 等 5 处 | 5 | PASS | B114 import a.b as a（round5） |
| `[B115` | region_analyzer.py:20734/21668/32013 等 4 处 | 4 | PASS | B115 while 条件 and/or 幻影（round5） |
| `[B116` | region_ast_generator.py:2693（1 处） | 1 | PASS | B116 位置参数 cellvars（round5） |
| `[B84` | region_ast_generator.py:2148/37214/37602 | 3 | PASS | B84 del/with 吞并（round2 P2） |
| `[B85` | region_ast_generator.py:60/37237/37470 等 12 处 | 12 | PASS | B85（round2 P2） |
| `[B86` | region_ast_generator.py:38508/38926/57019 等 5 处 | 5 | PASS | B86（round2 P2） |
| `[B87` | region_analyzer.py:14035/14248/14340；region_ast_generator.py:4591/4625/31703 等 11 处 | 11 | PASS | B87 try 体嵌套宿主（round2 P2/P3） |
| `[B88` | —（0 命中） | 0 | PASS | B88 return 嵌套宿主（round9 矩阵仍破口，无落地声明，应 0） |
| `[B89` | region_ast_generator.py:38633/38675/42883 | 3 | PASS | B89 boolop 链（round2 P3） |
| `[B90` | ast_converter.py:1547/1596 | 2 | PASS | B90 f-string format-spec（round2 P2） |
| `[B91` | region_ast_generator.py:4357/4380 | 2 | PASS | B91（round2 P3） |
| `[B92` | region_ast_generator.py:63748（1 处） | 1 | PASS | B92（round2 P3） |
| `[B93` | —（0 命中） | 0 | PASS | B93 with-in-match 幻影镜像（round9 矩阵仍破口，无落地声明，应 0） |
| `[B94` | —（0 命中） | 0 | PASS | B94 while NOP 残段（round9 矩阵仍破口，无落地声明，应 0） |
| `[B95` | region_ast_generator.py:10094（1 处） | 1 | PASS | B95（round2 P3） |
| `[B97` | —（0 命中） | 0 | PASS | B97 handler break（round9 矩阵仍破口，无落地声明，应 0） |
| `[B108` | region_ast_generator.py:31710/32842/35863 等 4 处 | 4 | PASS | B108 finally 吞并（round8 位B） |
| `[B111` | ast_generator_v2.py:248/263/487 等 6 处 | 6 | PASS | B111 LOAD_CLASSDEREF/CLOSURE（round8 位B） |
| `_graft_pending_operand` | region_ast_generator.py:43043/43174/43180 | 3 | **FAIL（应 0 实 3）** | B1a 归档嫁接方案（兼具「路线废弃」与「符号在树」双重事实，见异常节） |

### 补充枚举（36 项，supplementary）

| 模式 | 数量 | 站点（前 3） | 注 |
|---|---|---|---|
| `[B76` | 2 | core/cfg/region_ast_generator.py:45034；core/cfg/region_ast_generator.py:45044 | — |
| `[B75` | 8 | core/cfg/region_ast_generator.py:31302；core/cfg/region_ast_generator.py:31364；core/cfg/region_ast_generator.py:31427 等 8 处 | — |
| `[B73` | 3 | core/cfg/region_ast_generator.py:35531；core/cfg/region_ast_generator.py:35633；core/cfg/region_ast_generator.py:35698 | — |
| `[B74` | 5 | core/cfg/region_analyzer.py:2160；core/cfg/region_analyzer.py:16035；core/cfg/region_analyzer.py:16184 等 5 处 | — |
| `[B71` | 13 | core/cfg/region_ast_generator.py:38；core/cfg/region_ast_generator.py:3825；core/cfg/region_ast_generator.py:3913 等 13 处 | — |
| `[B65` | 2 | core/cfg/region_ast_generator.py:45128；core/cfg/region_ast_generator.py:45429 | — |
| `[B50` | 3 | core/cfg/region_analyzer.py:2026；core/cfg/region_analyzer.py:2039；core/cfg/region_analyzer.py:2060 | — |
| `[B46` | 8 | core/cfg/region_analyzer.py:26306；core/cfg/region_analyzer.py:26371；core/cfg/region_analyzer.py:26869 等 8 处 | — |
| `[B82` | 4 | core/cfg/region_ast_generator.py:31529；core/cfg/region_ast_generator.py:31605；core/cfg/region_ast_generator.py:31612 等 4 处 | — |
| `[B77` | 3 | core/cfg/region_ast_generator.py:40339；core/cfg/region_ast_generator.py:40447；core/cfg/region_ast_generator.py:41236 | — |
| `[B81` | 12 | core/cfg/pattern_parser.py:366；core/cfg/pattern_parser.py:467；core/cfg/pattern_parser.py:1413 等 12 处 | — |
| `[B83` | 2 | core/cfg/region_ast_generator.py:33373；core/cfg/region_ast_generator.py:33432 | — |
| `[B88` | 0 | — | — |
| `[B84` | 3 | core/cfg/region_ast_generator.py:2148；core/cfg/region_ast_generator.py:37214；core/cfg/region_ast_generator.py:37602 | — |
| `[B93` | 0 | — | — |
| `[B94` | 0 | — | — |
| `[B97` | 0 | — | — |
| `[B100` | 6 | core/cfg/region_ast_generator.py:768；core/cfg/region_ast_generator.py:36959；core/cfg/region_ast_generator.py:37198 等 6 处 | — |
| `[B109` | 3 | core/cfg/region_analyzer.py:5909；core/cfg/region_analyzer.py:6317；core/cfg/region_analyzer.py:6495 | — |
| `[B126-R1` | 0 | — | 9.3b 已移除，0 命中为预期 |
| `_b126_claimed` | 0 | — | 同上，0 命中为预期 |
| `[B114` | 5 | core/cfg/region_ast_generator.py:12616；core/cfg/region_ast_generator.py:12743；core/cfg/region_ast_generator.py:37418 等 5 处 | — |
| `[B115` | 4 | core/cfg/region_analyzer.py:20734；core/cfg/region_analyzer.py:21668；core/cfg/region_analyzer.py:32013 等 4 处 | — |
| `[B116` | 1 | core/cfg/region_ast_generator.py:2693 | — |
| `[B103-R2` | 1 | core/cfg/pattern_parser.py:251 | — |
| `[B105-R2` | 1 | core/cfg/region_ast_generator.py:61440 | — |
| `[B107-R2` | 2 | core/cfg/region_ast_generator.py:63419；core/cfg/region_ast_generator.py:63489 | — |
| `[B104-R3]` | 4 | core/cfg/region_analyzer.py:19952；core/cfg/region_analyzer.py:20043；core/cfg/region_analyzer.py:20102 等 4 处 | — |
| `[B99 收窄]` | 0 | — | B99 封闭以 B99-R1/R2 命名，本字面量无命中 |
| `[R21-86` | 8 | core/cfg/region_ast_generator.py:369；core/cfg/region_ast_generator.py:390；core/cfg/region_ast_generator.py:536 等 8 处 | — |
| `[R75 fix1]` | 3 | core/cfg/region_ast_generator.py:43033；core/cfg/region_ast_generator.py:43044；core/cfg/region_ast_generator.py:43167 | — |
| `[R76-A1` | 12 | core/cfg/region_ast_generator.py:2048；core/cfg/region_ast_generator.py:2082；core/cfg/region_ast_generator.py:2132 等 12 处 | — |
| `[R76-A2` | 0 | — | 该字面量无命中（相关守卫以 [R76-A1]/函数名载体在树，见 _cjb_skip_inline_if / _contains_identity） |
| `_leading_operand` | 6 | core/cfg/region_ast_generator.py:43052；core/cfg/region_ast_generator.py:43059；core/cfg/region_ast_generator.py:43170 等 6 处 | — |
| `_contains_identity` | 6 | core/cfg/region_ast_generator.py:43032；core/cfg/region_ast_generator.py:43038；core/cfg/region_ast_generator.py:43040 等 6 处 | — |
| `_cjb_skip_inline_if` | 6 | core/cfg/region_ast_generator.py:43044；core/cfg/region_ast_generator.py:43170；core/cfg/region_ast_generator.py:60503 等 6 处 | — |

## 异常节（重大发现）：`_graft_pending_operand` 在树 —— 与 wiki/log/spec 旧表述矛盾

- **事实**（只读实测，HEAD 3e0d6905）：`core/cfg/region_ast_generator.py:43043`（`def _graft_pending_operand` 定义）、`:43174`（docstring 判据）、`:43180`（调用）；同族 `[R75 fix1]` 注释 ×3（`:43033/:43044/:43167`）、`_leading_operand` ×6（`:43052/:43059/:43170/:43230` + 发射端 `:60525/:60529`）、`_cjb_skip_inline_if` ×6（`:43044` + 发射段 `:60503-60515`）、`_contains_identity` ×6
- **引入提交**：`c53df077`（2026-09-30 harden round1 在途快照）；harden round1 REVIEW A2/A5 审计在案（5/5 通过，未标识该符号与 v2 表述的「零命中」矛盾）
- **矛盾面（如实登记，勿自修代码）**：
  - 总纲 §6 B1a「round75 fix1 嫁接方案 `_graft_pending_operand` 仅存归档 spec、未落地」、§8.1「已废弃不落地」；
  - `wiki/log.md` 2026-10-04 条目「round75 归档嫁接方案 `_graft_pending_operand` 确证废弃」；
  - 本规范 `spec.md:55`「落地标记 `_graft_pending_operand` 树中零命中」（B1 教训举例句）
- **处置**：总纲 §6/§8.1 按**在树事实**更正（「路线废弃」判据不变——B1 封闭以五臂算法为准；嫁接符号族未清理、随快照在树）；log 历史条目只增不删、新条目（步⑥）内说明；`spec.md` 为冻结输入不改。**是否追加规则面清理由主代理裁决**。

## 步③ 台账（§5）全量三态落位 + 组合级 25 号分层

口径（II.3/III.2–III.5）：Σ 行枚举权威 = `docs/refactor/syntax-coverage.json` + `tools/kb/syntax_coverage.py` 大写过滤实测 **97 = 29 语句 + 31 表达式 + 8 match 模式 + 29 操作符叶**（小写辅助节点 alias/arg/arguments/comprehension/keyword/match_case/withitem/excepthandler 不计分母），+ 表C 31 = **128**。

### 3.1 三态终表（v7）

| 台账表 | 行数 | 完备 | 破口 | 零能力 |
|---|---|---|---|---|
| 表A 语句与结构 | 29 | 15 | **14** | 0 |
| 表B 表达式（31+8+29） | 68 | 62 | **6** | 0 |
| 表C 扩展形态 | 31 | 26 | **5** | 0 |
| **Σ** | **128** | **103** | **25** | **0** |

破口 25 行清单（行内锚点 = 总纲 §5 各表「判定」列）：

- **表A（14）**：If（B46 尾项+B78）、While（B94）、Break（B79）、Continue（B97）、Try（B87/B73/B75）、With（B93）、Match（B74+B122）、Raise（B87 变体）、Assert（B56）、Return（B88）、Delete（B84）、AugAssign（B76+B48 残留变体）、Import（B73）、Global（B75）
- **表B（6）**：BoolOp（B98）、IfExp（B123；B124 已封闭留档）、Slice（B127）、ListComp（B112②）、Await（B112①+B128）、Yield（round3 F9 存量，探针重建待办）
- **表C（5）**：augmented_assign（B76+B48 残留变体）、await_expr（B112①+B128）、global_nonlocal（B75）、match_statement（B74+B122）、slice（B127）

> 核算注：round9 评审表A 分组显示 Σ=28（`Delete/Assign/AnnAssign（3）` 组注缺失）与声明「29 行 14 破」差 1——按 Σ=128 与表C augmented_assign 破口唯一解 = **AugAssign 行**（破口，B76+B48 残留变体），本轮按解落账。

### 3.2 与 round9 评审（101/27/0）增量对照

**升格 2 行（破口→完备）**：

| 行 | 依据（哪次修复/哪条证据） |
|---|---|
| chained_comparison（表C） | round9 位A+位0：B104 族 14 单元全转（B104_main 12→14/14、chain4 4→6/6、chain5 2→5/5、n9_whilehost 5→9/9 含存量 R4；`FIX_R9.md` §1）+ CCMP.m 值位链 B124 同步翻正（c4_09 13→14/14，§1.5）；门禁承重面 broker 128/128、matcher 17/17、循环族 68/68 不回退 |
| for_else（表C，含 while-else） | round9 位B：B125 两单元全转（b109 8→9/9、r5_13 10→11/11；r9w16 族电池全 2/2；`FIX_R9.md` §2） |

**封闭但行不升**：B124 族 5 单元全转（IfExp 行存量 B123 维持破口）；B126 n9_stmt_sweep 5→6/6（Assert 行存量 B56 维持破口）。**其余 22 行破口与 round9 逐位一致**（`REVIEW_DRAFT.md` §3.2 移交读数维持）。终审链：`REVIEW2.md`（整改）→ `REVIEW3.md`（放行）→ `VERIFICATION.md`（9.4 六步：六面 2092/2161 WORSE=0、34 集 1568/1568、pass→fail=0）。

### 3.3 组合级挂账 25 号分层终表

25 号清单（权威 = `harden-completed-forms-10rounds` spec `rounds/round10/REVIEW.md` §4.1 残留决策表 + `REVIEW2.md`）：B42–B51 / B56–B65 / B69–B71 / B73–B76 内未封闭部分，扣除已划除 B45/B64。

**清零 9**（对抗规范 v2 round1 批次 A/B/C + 同链实证）：

| 编号 | 口径/依据（一行） |
|---|---|
| B46 尾项 | 批次 A（`FIX_A.md` §2，t_nest_in_condition）† |
| B48 残留变体 | 批次 A（`FIX_A.md` §1，t_host_try_sections / B50 同链；`REVIEW2.md` §3 如实登记 t_host_while_body 另存变体）† |
| B74 | 批次 A（`FIX_A.md` §3，match case 体首幻影 guard） |
| B65 | 批次 B（`VERIFICATION.md:44`） |
| B71 | 批次 B（fin_continue/fin_break）+ 批次 C（边类型封闭 `12d7ddb9`；残余 fin_continue 转 B79 续接）† |
| B73 | 批次 B（`FIX_B.md` §4，try 四段 import 宿主泄漏） |
| B75 | 批次 B（`FIX_B.md` §5，try 宿主 global 5/6→6/6） |
| B76 | 批次 B（`FIX_B.md` §2，augassign×BoolOp RHS 体蒸发） |
| B50 | round1 `REVIEW2.md` §3 实测「封闭真实（+2），外推过」（v_two_except_fin 4/4；归因链 6/8→7/8 真实 +1） |

> v2 round1 登记封闭 = 批次 A（B48 残留变体/B46 尾项/B74）+ 批次 B（B71/B73/B75/B76/B65）+ 批次 C（B71 边类型）= 8 项（`VERIFICATION.md:44`）；+ B50 同链实证 = **清零 9**。† = 台账/round9 仍以该编号作行内沿袭锚点的**保守带账**项，归属裁决留主代理。

**维持 16**：

| 编号 | 残余/现状（一行，源 = round1 `REVIEW.md` §2 逐项复验表） |
|---|---|
| B42 | 部分（r7_01 t_arg_multi_mixed 于合并期翻正）；r7_04 t_compare_lhs_only、r7_05 t_listcomp_ternary_filter 维持（C1 参数栈位/比较 LHS/推导式 filter） |
| B43 | r7_10 c_chain_and_combo（链式比较×BoolOp 汇合块消费点错位） |
| B44 | r7_11/r7_12 BoolOp 重复/三层/深右嵌套（B1 双入口同族）；round9 证据缺口（未抽验如实标注） |
| B47 | r7_06 await×三元臂 ×3（外提越 POP_JUMP 对） |
| B49 | r7_08 t_host_for_else（else 体三元增强赋值，前驱集归属） |
| B51 | rv7_02 if 三元链复合值 ×2 |
| B56 | r8_07 r8_assert_nested_func（幻影 else 源）；r8_10 assert×三元 |
| B57 | r8_10 r8_x_for_iter_ternary |
| B58 | r8_10 r8_x_raise_ternary_class |
| B59 | r8_09 r8_dh_for_else_del（深宿主 with 首赋值族） |
| B60 | r8_09 r8_dh_with_assert |
| B61 | r8_09 r8_dh_match_multi + r8_11 r8_dh2_match_guard |
| B62 | r7_14 h_return_composite（return(call+BoolOp) 尾语句蒸发） |
| B63 | rv8_02 tryfin_then_more（空 try/fin 后非纯常量尾随段） |
| B69 | rv9_01 emptyfin_in_if（if 臂内空 try/fin 吞尾随 return） |
| B70 | rv9_02 while_with_whole_body（while True+with 幻影 break） |

**口径差另册（如实登记）**：round1 `REVIEW.md` §2.2(g) 已登记「决策表含 B52/B53/B63 而 III.5 区间名单未列」的子集差——**B52/B53**（决策表含、25 号区间外，实测残留持平）+ **B11-R2**（r4_or4_and2，1/2 持平，独立另册）建议 10.3 归档时统一口径；**B63 在 25 号区间内（B56–B65），维持**（非另册）。

### 3.4 wiki 落账变更清单（本轮 edit 明细）

- §0 读数表：4 行重写（128/128；103/25/0；25 号分层 清零 9/维持 16；80.47%）
- §4 T4/T6：程度列去「B1 破坏/未封闭」矛盾 → 落账口径
- §5.2：14 破口行注入行内编号（含 AugAssign 隐匿行修正）；§5.3：6 破口行 + 操作符叶 32→29 更正（round9 口径注记：「32 叶」为旧口径，分母枚举 29 叶全绿）；§5.4：match_statement/augmented_assign/slice/global_nonlocal/await_expr 5 行 + for_else/chained_comparison 升格注记
- §5.5：汇总重写（103/25/0 + 80.47%）+ 残留段落更新
- §6：B1a 括注按在树事实更正 + 新增「B77+ 批次登记」（已封闭 B104 族/B124/B125/B126；开放 B98/B127/B128/Yield/B44/B122 与行内编号族）
- §8.1：状态列「2026-10-04 终审」→「2026-10-17 复审」+ B1a 行括注更正 + 新增 B104 族/B124 族/B125/B126 行 + 全量复核注（72 项 71 PASS/1 异常）
- §9.1：「五次」→「七次」+ v6 行去「现行」+ 新增 v7 行
- frontmatter `updated` → 2026-10-17；检索词追加 v7 数字
- 同步页 4 张（数字核对表见步⑤）；[[log]] 新条目（步⑥）

## 步④ 路径层重跑 `tools/kb/syntax_coverage.py`

命令：`python -X utf8 tools/kb/syntax_coverage.py`（输出 `docs/refactor/syntax-coverage.json`）

| 项 | before 快照 | after 快照 |
|---|---|---|
| sha256 | `86539c44fe6ae974fa5a03f2500f5d0fe99d4bac3d34f79b8ca6a766bfd4b9ae` | `86539c44fe6ae974fa5a03f2500f5d0fe99d4bac3d34f79b8ca6a766bfd4b9ae` |
| size | 2724 | 2724 |
| 读数 | 128/128 = 100%，uncovered = 0 | 128/128 = 100%，uncovered = 0 |

- **sha256 前后一致 ⇒ 确定性重跑，零漂移**（与 Round 10 10.1 终验读数一致；不手改工具输出）。
- 快照存证：`r10v10_coverage_before.json` / `r10v10_coverage_after.json`。

## 步⑤ 占比重算（II.1）与数字同步核对表

**II.1 口径**：完备占比 = 完备形态数 ÷ 128 = **103 ÷ 128 = 80.46875% ≈ 80.47%**（分子只计已复审行；破口 25 不计分子；零能力 0）。

### 数字同步核对表（禁矛盾数字）

| 页面 | 位置 | 旧值 | 新值（v7） | 状态 |
|---|---|---|---|---|
| 总纲 | §0 表 4 行 | 128/0/0；25 号未清零；100% | 103/25/0；分层 清零 9/维持 16；80.47% | 已改 |
| 总纲 | §4 T4/T6 | B1 破坏/未封闭 | 落账口径（B1 封闭 + 25 行编号） | 已改 |
| 总纲 | §5.2/5.3/5.4 | 27 处判定 | 破口 25 行编号 + 升格 2 行 + 29 叶更正 | 已改 |
| 总纲 | §5.5 | 128/0/0 ⇒ 100% | 103/25/0 ⇒ 80.47% | 已改 |
| 总纲 | §6 | B1a 括注（未落地） | 在树事实更正 + B77+ 登记 | 已改 |
| 总纲 | §8.1 | 2026-10-04 终审 | 2026-10-17 复审 + 行增补 | 已改 |
| 总纲 | §9.1 | 五次 / v6 现行 | 七次 / v7 现行 | 已改 |
| 总纲 | frontmatter / 检索词 | 2026-09-29；旧关键词 | 2026-10-17；v7 关键词 | 已改 |
| overview.md | L43 | 完备 128/破口 0/100%；25 号未清零 | 103/25/0 ⇒ 80.47%；分层 9/16 | 已改 |
| index.md | L155 | v1–v6；128/0/0 ⇒ 100% | v1–v7；103/25/0 ⇒ 80.47%；分层 9/16 | 已改 |
| syntax-audit-ledger.md | L18 | 2026-10-04 终审；128/0/0 ⇒ 100% | 2026-10-17 复审 v7；103/25/0 ⇒ 80.47% | 已改 |
| branch-coverage.md | L18 / L35 | 128/0/0 ⇒ 100%；v6 现行 | 103/25/0 ⇒ 80.47%；v7；检索词更新 | 已改 |
| log.md | 新条目 | — | 2026-10-17 迭代 + 破口变迁 | 已增 |
| docs/refactor/syntax-coverage.json | 全文件 | sha 86539c44… | sha 86539c44…（未变） | 工具输出 |

- 非数字历史叙述项：`cfg-anatomy.md` L105「B1 破口」为历史叙事，**未改**（建议主代理裁决是否追注）。
- 模块页/其他页 `:128` 等命中经逐个定性 = 行号锚点（非完备数字），**未动**。

## 步⑥ `wiki/log.md` 记录

- 新条目「2026-10-17（对抗规范 v2 Round 10：六步重验 + 三态落账 v7）」插入 `# Research Log` 后（2026-10-04 条目前，新在前）；内容 = 六步结果 + 破口变迁（v6 128/0/0 → v7 103/25/0；B104 族/B124/B125/B126 封闭；B127/B128/Yield/B44 开放）+ 提交锚（`3e0d6905`/`0ad55951`）+ 嫁接符号在树更正说明（只增不删）。

## 遗留与建议（交主代理）

1. **全表重锚未做**（round1 `REVIEW.md` §6.2 曾建议统一重锚 §5 `file:line` 锚点；本 BRIEF 未列该项）——保留 2026-09-29 快照锚点（合 §5 证据规则），建议另立批次。
2. **B127/B128/Yield 探针重建 + B44 证据缺口**（round9 §3.3/§6 位D 队列）移交后续轮次。
3. **25 vs 29 口径统一**（B52/B53 与 B11-R2 另册）建议 10.3 归档时处理。
4. **`_graft_pending_operand` 符号族**：wiki/log 已按在树事实更正；是否清理代码符号（删除性变更）待裁决。
5. **cfg-anatomy.md L105 历史叙述**是否追注 v7 口径，待裁决。

## 附：本轮产出物

- `WIKI_REVIEW.md`（本文）；`r10v10_wiki_marks.json`（72 markers + supplementary 36 + bracket 清单 + summary）；`r10v10_wiki_marks_supp.json`（补充枚举原始件）；`r10v10_coverage_before.json` / `r10v10_coverage_after.json`（sha 存证）
- wiki 改动：`wiki/concepts/decompile-invariant-completeness.md`、`wiki/overview.md`、`wiki/index.md`、`wiki/concepts/syntax-audit-ledger.md`、`wiki/concepts/branch-coverage.md`、`wiki/log.md`
- 改动文件 hash 存证（全部 edit 完成后实测）：
  - 总纲 `decompile-invariant-completeness.md` sha256：`BABC581290FCDAA7577FD49CEFA25378DC26854255D9861F1A36A574713468BC` → `6ae21ee7994350fd3edbcdded888640f9cc4c88a644be573a13f7c6cd2e43f20`（25711 → 32324 B）
  - 同步页/日志 git blob sha1（before → after）：overview `2ba23439…` → `26edab92…`；index `7e9a3f9c…` → `121bd806…`；log `401060c1…` → `2be7137a…`；syntax-audit-ledger `31232279…` → `683b2011…`；branch-coverage `27278217…` → `5cf49366…`（before = `git rev-parse HEAD:路径`，after = `git hash-object 路径`）
