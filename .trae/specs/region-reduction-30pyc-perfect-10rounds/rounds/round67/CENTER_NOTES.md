# Round 67 · center notes (written before the diagnose agents were launched)

## 轮初状态
- HEAD = R66 记录提交（`f972bd3c` 之后的 R66 收尾），工作树 core 字节 = R66 合并集：
  `core/cfg/region_ast_generator.py` 3 140 634 B sha256 `3db80082b87ecca06e8c…`（BOM+CRLF 50 626、裸 LF 0），
  `core/cfg/region_analyzer.py` 1 734 099 B sha256 `0e9740cc1836f3201312…`（无 BOM、CRLF 27 763）。
- 官方尺轮初基线（R66 落地后 `stats`）：5746 functions / **5698 matched / 99.16%**，ok 386、partial 16。

## 轮初缺陷表（零重测，全部取自 R66 已交叉证明的产物）
`mkr67targets.py` 把 `pyc_index.json` 的 16 支 partial 与
`r66gate/center/dump/m66e_all17.jsonl`（官方尺逐函数元组）+ `dump/strict_repo_r66_after.json`（严格尺，
跑在**已发布**产物上）联接，反向夹钳 `rows=16 no-official-record=0 no-strict-record=0`。
合计官方缺陷函数 48、严格缺陷函数 72。输出 `targets16.txt / defects16.md / diagN_targets.md / batches.txt`。

## 分批（硬上限 3 支/批）
R66 教训：诊断代理死在 150 轮上限，靶支数是主要开销 ⇒ 16 支分 6 批、每批 ≤3 支，
负载按 `max(严格缺陷, 官方 gap)` 贪心均衡：diag1 1 支(12/18)、diag2 3 支(13/17)、
diag3 3 支(6/10)、diag4 3 支(5/9)、diag5 3 支(7/9)、diag6 3 支(5/9)。

## 代理工作区
`provision67.py` 从 `r66gate/center`（规范仪器副本）+ `r66gate/diag1`（代理自产 helper）拷进
`r67gate/{center,diag1..6}`，只改写工作区根路径字面量：`h62.py align.py regdump.py disf.py nhunks.py
cstrict.py dumpfn.py mk_spec.py probe_chain.py` + `battery.txt canary.txt shapes_r63.txt all402.txt all17.txt`，
各批另有 `targets.txt / targets.md / BRIEF.md`。`gen67briefs.py` 写 6 份 BRIEF（共享基线段 + 每批自己的
已知情报与被证伪线索）。**402 全量扫描归中心**，brief 里明令禁止代理跑。

## 中心在派代理之前实测的 landed 基线（`--arm=landed`，即 R66 落地字节）
- 电池：清单由 glob 扩到 **31 项**（24 项老电池 + 7 支 round66 复现；`shapes_r63.txt` 的 11 条 pinned 与
  round63 目录完全重复，去重后不增项）。合计 matched **115/127**、缺陷函数 12 支。
  逐支读数见 `diag*/BRIEF.md` 基线段与 `dump/battery_landed.jsonl`。
  与 R66 轮初相比已改善的见证：`fsrepro` 6/7→**7/7**、`fs2` 5/10→**6/10**、新增 `r66d3_pred` 2/3
  （残余 `v6` = R66 §7.2 线索，已指派给 diag5）。
- 金丝雀 4 支：143/143 + 10/10 + 26/26 + 25/25，产物 sha
  `4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177` —— 与 R66 门禁逐支相同，
  再次确认这 4 支不在 R66 的 6 支产物 blast 内。
- 仪器核对：`h62.py run` 对 `test_repros/**.pyc` 把产物写成 `build_<arm>/F___…__r63_ftOK.py`
  （`/`→`__`、`:`→`_` 的扁平名），**不写仓库**；已实测 `test_repros/**/*OK.py` 计 0 个、
  `git status test_repros` 只有 15 条历史 `out_*` 未跟踪目录。

## 中心 landed16 基线（`--arm=landed`，16 支 partial 一次跑完，分 4 片）
`dump/landed16.jsonl`：items=16、matched **593/641**、缺陷函数 **48**、ERR=0、
Σ|orig−decomp| **328**、Σjumpdiff **184**、Σtruediff **9405** —— 与 R66 收口时的四个总量逐项相同，
即「轮初 = R66 落地态」成立；这也是本轮所有候选臂的 A/B 对照列。

## diag1 已返回（第一批，foreground）
- 结论 **候选：NONE**，交付 `FACTS.md`(154 行) + `synth/r67_join_after_noelse.py` + `specs/cand_r67_j1.json`。
- 其 J1 判据（`region is None ∧ self._current_loop ∧ _region.parent is None`，L21935 调用点）
  合成复现 6/7→7/7，但**金丝雀 quotation sha 变了**且 `trade_live_broker` 在臂内直接不可反编译（ERR）
  ⇒ 两道硬门禁同时失败，**不采纳**。它自证伪了自己第一条线索（E1 对三支 IfRegion 全返回 False）。
- 留下的可复核线索：`get_all_orders` 的 `IfRegion@362` 是 `Region@98` 的同层兄弟、其 entry 正是外层 if 的
  merge/exit，生成器却从 for 循环内部发射它（`blocks=[98]`、`owner=Region@98`）——本轮集中验证可拿它做窄判据。
- **仪器修正（我这边）**：provision 拷的 `battery.txt` 是 R66 的 24 行老清单（93/104），代理自己重建到 31 行
  才复放成功；已把 `dump/reprolist67.txt`(31) 覆盖进 diag2..6，省掉每批几轮自造清单。

## 派 diag2..6（background 并行）+ fix1（实现代理）
- diag2..6 后台并行，各自私有工作区，brief 里明令禁跑 402。
- diag1 交付后另派 **fix1 实现代理**（`r67gate/fix1`，拷入 diag1 的复现与被拒 spec）：把 J1 收窄成
  仅读本帧 `blocks` 实参 + `_region` 自身字段的形状，四道门（复现 7/7、靶支不 ERR 且 ≥107/119、
  电池 31 项不劣、金丝雀 4 sha 逐字节不变）全过才允许交 spec，另加 16 支 landed16 对照
  （中心基线 `dump/landed16.jsonl`，代理不跑 402）。这是 [[feedback-subagent-scope-diagnose-vs-fix]]
  规定的分工：诊断方diag1 已给出判据草案与失败读数，实现方只负责收窄与过门。

## 仪器事故（如实登记）
搭 fix1 工作区时误 `import provision67`，把 provision 全流程重跑了一遍，`battery.txt` 被
R66 的 24 行老清单覆盖（diag1..6 全部）。已在数分钟内用 `dump/reprolist67.txt`(31) 复原全部 7 个工作区，
并给每个目录留 `WORKSPACE_NOTICE.txt` 说明「24 行清单读数 93/104，不是基线；若已经跑过请重跑 landed」。
`BRIEF.md` 与 `targets.txt` 未受影响（provision 不写它们；实测 6 份 BRIEF 字节数不变）。
教训：provision 脚本必须幂等或加 `--force`，helper 不许用 import Side-effect 方式调用。

## 符号核对（brief 里点名的判据入口，全部在当前落地字节上 grep 实测）
`_loop_build_if_with_exit_branches` L10495（R65 记 L10470，+25 漂移）、
`_apply_r23n6_return_promotion` L47853（R65 记 L47636）、`_try_build_ternary_kwarg_call` L43162（R65 记 L42968）、
`get_entry_region_for_block` analyzer L27409、`_boolop_resolve_merge` analyzer L24010、
`_merge_block_is_then_exclusive` gen L16834/L18004、`_STRUCTURAL_REGION_TYPES` gen L254/260/4889/14538、
`self._current_loop` gen 有 287/2762-2764 等 ⇒ 六份 brief 的前提符号都存在，行号漂移已提醒代理自行 grep。

## 阶段 A 集中验证（中心独立复测，不采信代理口述）
每份 spec 先在**当前落地字节**上核锚点 `count==1`，再用 `center/h62.py build` 建私有镜像
（build 自带「head 镜像 == 工作树字节」断言），然后中心自己跑 targets/battery/canary/复现 + 严格尺。

| 臂 | 来源 | 锚点 | 复现（landed→臂） | 16 支 A/B | 电池 31 | 金丝雀 4 | 严格尺 16 |
|---|---|---|---|---|---|---|---|
| `c1` | diag2 analyzer L16448 or-chain 尾段 | 1/1 | `r67_guard_tern` 1/2→**2/2** | IMPROVED=1（`IQData/utils/common_func` **23/24→24/24**）MOVED=1(api_base) REG=0 | SAME=31 | SAME=4 sha 全同 | 655→656，缺陷 72→71 |
| `hc` | diag4 generator 2 edits（handler continue） | 1/1,1/1 | `s1` 严格 3/4→**4/4**；控制 `c3` 仍 1 缺陷（seq_len→seq_diff，形状变、计数不变） | MOVED=1（官方中性，严格 +1）REG=0 | SAME=31 | SAME=4 | `realtime_event_source` 10/12→**11/12** |
| `j3` | fix1 由 diag1 J1 收窄（5 条件，全读本帧/本区域字段） | 1/1 | `r67_join_after_noelse` 6/7→**7/7** | IMPROVED=1（`trade_live_broker` 107/119→**108/119**）MOVED=1(quote) REG=0 | SAME=31 | SAME=4 sha 全同 | `trade_live_broker` 105/123→**106/123** |
| **`m67e`** | 合并集（analyzer 1 edit +66；generator 3 edits +102） | 链式唯一性通过 | 复现 4 项 IMPROVED=2 MOVED=2 SAME=0 REG=0 | **IMPROVED=2 REGRESSION=0 MOVED=3 SAME=11 ERR=0**，完全匹配 0→1 | **SAME=31（零见证移动）** | **SAME=4（四 sha 逐字节不变）** | **655/727→658/727、缺陷 72→69** |

合并镜像字节核对：generator 3 149 323 B BOM=True CRLF 50 728（=50 626+102）裸 LF 0；
analyzer 1 739 284 B 无 BOM CRLF 27 829（=27 763+66）裸 LF 0。

### 中心对代理结论的独立更正
- fix1 更正 diag1 的「J1 让靶支 ERR」：中心/fix1 复测 j1 臂为 **108/119 且不 ERR**，J1 真正的死因是
  金丝雀 sha 移开（`3eb76e512df9ab1e`）。fix1 又用逐帧读数证伪 diag1 交下来的「blocks 单元素」收窄方向
  （命中帧全是 2 元素 `[68,98]`/`[332,362]`），真正的分离判据是**被认领区域自身的 `merge_block`/`exit` 为空**；
  反例 `quotation::get_trend` 的 `mb=220 x=220` 正是被第 (5) 条挡住的那一支。
- diag2 更正中心轮初表：`handle_exrights` 不是位移（轮初 §"未采纳"把它当位移），真实缺陷是
  or-chain 第三操作数丢失 + 块 14 被当作链成员跳过而孤立。
- diag4 更正仪器三处：`cstrict.py` 无法配对 scratch 路径复现（中心已补 `sstrict67.py`）、
  `nhunks.py` 未归一 `EXTENDED_ARG` 会让「jump 前 1 指令删除 hunk」被当成真缺陷、
  `regdump.py` 不打印 `handler_entry_blocks`/`except_handlers`。
- 严格尺上 `quote::run_tick_transform` 的 `target_diff` 从 #135 移到 #56（同一条缺陷换位置，计数不变），
  由 j3 在 quote 的 while 去嵌套引入 ⇒ 登记为形状变化，不算新增缺陷、也不算收益。

## 402 全量扫描（中心，background）
`sweep402_67.py landed m67e`（日志 `logs/sweep402_67.log`，输出 `dump/landed_402.jsonl` /
`dump/m67e_402.jsonl`，分 4 片 × 最多 8 轮续跑）。landed 列同时用来审计 `pyc_index.json`。

## 待办（代理返回后）
逐臂单变量复测（targets/battery/canary + `h62.py ab`）→ 采纳/回退 → `mkfinal67.py`+`mbuild67.py` 合并落地
→ 串行门禁 G1…G6′（含 402 A/B 与产物 blast）→ `rounds/round67/` 归档 → 显式路径 `git add` + 提交 + push（脱敏）。

## 阶段 A′：402 全量 + 后续批次裁决（13:33–13:55）
`m67e` 402 A/B（`dump/landed_402.jsonl` vs `dump/m67e_402.jsonl`，4 shards ×1 轮，均 exit=0、402/402）：
**IMPROVED=2 REGRESSION=0 MOVED=3 ERR=0**；完全匹配文件 **386→387**；逐支：
`common_func` 23/24→**24/24**、`trade_live_broker` 107/119→**108/119**、
`api_base::get_history_df` [1742,1719,14,1277]→[1742,**1740**,14,1263]（缺 23 条→缺 2 条）、
`realtime_event_source`/`quote` MOVED 且缺陷集不变（仅文本移位）。⇒ m67e 语料净收益实测成立、零回归。

### diag5（real_quote/order_api/scheduler + 名下主靶 r66d3_pred::v6）
- 交付 `specs/cand_r67_ccprefix.json`（generator 2 edits，helper `_r67_split_cc_ternary_stmt_prefix`，
  三要素注释齐；中心已 grep 证实 `_split_block_condition_prefix` L336、`_build_statements_from_instructions`
  L27926 与常量 `FORWARD_CONDITIONAL_JUMP_OPS|NONE_CHECK_OPS|SHORT_CIRCUIT_JUMP_OPS`（L143 import）**都存在**）。
- 第二步 `specs/cand_r67_dsplit_analyzer.json`（analyzer 判据 (d) 的栈深归零放宽）——代理证得
  analyzer-only 会**丢语句**（v6 `[36,34,2,16]→[36,34,1,34]`，`k = 1` 消失）、generator-only 对 landed 的
  v6 完全惰性 ⇒ 只能成对。中心采纳**成对**（代理的「先生成器后 analyzer」是单文件批次规则，不是测量结论）。
- real_quote 四支＝纯位移族（30/35 条整段搬尾 + `EXTENDED_ARG` 长度位，零语句增减）；
  order_api 三支＝R50 kwarg 槽位 bail 族（`_try_build_ternary_kwarg_call` landed L43162，唯一调用 L38156）；
  scheduler `run_daily`/`func_wrapper`＝cellvar 降级，`nhunks.py` 因同名 code object ×2 直接 AssertionError（工具限制）。**候选：NONE**。
- 陷阱入库：`region_analyzer.py` **没有模块级 `import dis`**，在该 gate 用 `dis.stack_effect` 必须**局部导入**，
  否则 NameError 被上层宽 except 吞掉、产物静默退化成 `if 0 < int(dc): if 200: pass`（实测 `[36,28,0,29]`）。

### m67f = m67e + diag5 两步（中心独立复测）
`mkfinal67.py m67f`（5 spec）⇒ analyzer **2 edits +110 行**、generator **5 edits +156 行**，链式锚点唯一性通过；
`mbuild67.py m67f` ⇒ generator 3 153 249 B BOM=True CRLF 50 782 裸 LF 0、analyzer 1 742 308 B 无 BOM CRLF 27 873 裸 LF 0。

| 量表 | landed → m67f（中心自己跑的） |
|---|---|
| 电池 31 | `r66d3_pred.pyc` **2/3→3/3**，TALLY SAME=30 IMPROVED=1 **REGRESSION=0 MOVED=0**，完全匹配 24→25 |
| 金丝雀 4 | **SAME=4**，四 sha 逐字节不变 |
| diag5 合成 3 | `r67_ccprefix` 1/5→**5/5**、`r67_ccprefix2` 1/3→**2/3**、`r67_site2` 3/8→**4/8**（w1/w2/w3/w4/w5/c6 六支 witness 修复） |
| 16 支 A/B | IMPROVED=2（common_func 24/24、trade_live_broker 108/119）MOVED=3 REGRESSION=0 SAME=11 ERR=0 |
| 严格尺 16 | **658/727、缺陷 69**（landed 655/727、72） |

### diag1b / diag3 / diag6 的回退（中心复测或按其自有机器可读见证判定，全部不落地）
- **diag1b `cand_r67_b1`**（analyzer 菱形汇合点 merge 回收）：复现 1/6→3/6、电池 SAME=31、金丝雀 sha 全同，
  但名下靶支 **MOVED 变差**：`_process_order` 396→**369**（orig 454），t349→355 ⇒ 缺陷量放大，**不落地**。
  代理自pin 根因：回收到的汇合点 2648 同时承载消费者与其后四条语句，`_mb_first_store_idx`（L21785-21794）只会按 `STORE_*` 切。
- **diag3 `cand_r67_bare_return_sink`**（臂 `d3c1`，generator 1 edit）：中心实测 电池 SAME=31、金丝雀 SAME=4 sha 全同、
  16 支 `MOVED=1 REGRESSION=0`：`_do_request` [436,443,2,384]→**[436,429,1,380]**。
  官方尺/严格尺读数都不变（443 过冲 7 → 429 欠缺 7，**Σ|Δ| 不变**，只把过冲翻成等量欠缺），
  按 [[project-official-vs-strict-gate-blindness]] 的 Σ|Δ| 否决 ⇒ **不采纳**，判据与锚点留档（其注释形态可复用）。
- **diag6 `cand_r67_whiletrue_headif`**（臂 `r67d6w1`）：按其自有 dump 读数 `write_logging_thread`
  [113,113,1,40]→[113,**41**,1,107]、电池 `r63b5_w1::init_connection` [42,41,0,25]→[42,**32**,0,32]
  ⇒ 两支同步崩塌，需生成器侧「重发头块前缀去重」配套才可能成立，**单侧不落地**。
  diag6 另交来一条**根因已证但落在第三个文件**的缺陷：`core/cfg/comprehension_generator.py::
  _detect_comp_ternary`（L1601，扫描循环 L1619-1653 在**第一条** forward 条件跳转处 `break`，条件切片 L1664）
  丢掉共享同一 false 目标的第二条条件跳转 ⇒ `A if (A>0 and B>0) else 0` 降为 `A if A>0 else 0`，
  语料见证 `wizard_quant_api::get_DMI.calculate_di`（官方 51/53、严格 52/56 双尺皆红）+ 9 行合成复现两支。
  ⇒ 中心已开 `fix2` 实现代理（工作区 `r67gate/fix2`，其 `h62.py`/`mbuild67.py` 的 ALLOWED 已加第三个文件），
  门禁合同：合成 6/6+8/8、wizard 51/53→52/53 且严格 52/56→53/56、电池零回归、金丝雀四 sha 不变、16 支零回归。
- diag6 另报一条**尺子覆盖**问题（本轮不解决但要登记）：`fly/logger::SafeFileHandler.check_baseFilename`
  官方 34/34 PASS，严格 `target_diff #14` 抓到真实语义反转 —— orig `return 1 if (X or not Y)`，
  产物 `if not (X or Y): return 1`（`not` 被从单个操作数 Y 推到了整个 BoolOp 上）。

## 阶段 B：m67g = m67f + fix2（第三个 core 文件）
fix2 由 diag6 已证的 `comprehension_generator._detect_comp_ternary` 首跳 `break` 根因出发实现
`specs/cand_r67_comptern_boolop.json`（1 edit +56 行，`_r67_boolop_chain_end` 同层链判据，
中心已复核注释三要素与「只读本存储区结构、无名字/文件/阈值」）。中心独立复测（`--arm=f2` 单臂）：
电池 31 SAME=31、金丝雀 SAME=4 sha 全同、16 支 **IMPROVED=1（wizard 51/53→52/53）REGRESSION=0 MOVED=0**。

`mkfinal67.py m67g`（6 spec / 3 文件）⇒ analyzer 2 edits +110、generator 5 edits +156、comprehension 1 edit +56；
链式锚点唯一性通过。镜像 m67g 字节指纹（落地即实测字节）：
generator 3 153 249 B sha f712bc20d7ad44542e18 BOM=True CRLF 50 782 裸 LF 0；
analyzer 1 742 308 B sha af8cc88b9f89779b3ef0 无 BOM CRLF 27 873 裸 LF 0；
comprehension_generator 108 192 B sha be5490c1118c7199fe0a 无 BOM CRLF 2 016 裸 LF 0。

| 量表 | landed → m67g（中心） |
|---|---|
| 16 支 A/B | **IMPROVED=3**（common_func 23/24→**24/24**、trade_live_broker 107/119→**108/119**、wizard 51/53→**52/53**）MOVED=3 SAME=10 **REGRESSION=0 ERR=0** |
| 402 A/B | **IMPROVED=3 REGRESSION=0 MOVED=3 SAME=396 ERR=0**；harness 口径完全匹配文件 386→387；官方指令缺口 Σ\|Δ\| 328→296；Σmatched 5698→5701（本行先前抄作 298/5700，已在文末更正段按出货日志改判）|
| 产物 blast | identical=397 changed=5（m67f）/ 6（m67g，wizard 加入）＝恰等于 IMPROVED+MOVED 集 |
| 电池（公开 45 项，含本轮 14 支新复现） | matched 161/200→**174/200**、缺陷函数 39→**26**、8 项变好、**worse-than-landed=0**、errors=0 |
| 严格尺 16 | 655/727（缺陷 72）→**659/727（缺陷 68）** |
| 合成复现 | d5：1/5→5/5、1/3→2/3、3/8→4/8；d6：4/6→5/6、3/8→6/8；whiletrue 1/2 不变（该臂被否决） |

## 落地前索引审计（G5 前置，只读）
> **本小节结论已被文末「更正」第 2 条作废**（按 `path` 键控重算＝`inconsistent=0`）。原文保留作溯源。
`pyc_index.json`（R66 写入，sha ccb36bad36387c7a、402 条目、CRLF 4553 裸 LF 0）与本轮 fresh
`--arm=landed` 402 逐条比对 ⇒ **只有 1 条不一致**：`IQData/utils/common_func.pyc` 索引 (24,24,ok) vs
fresh 23/24（缺陷 `handle_exrights` 276/268）。即 R66 索引里这条「ok」相对 R66 落地字节是**乐观的**；
本轮 diag2 的 or-chain 尾段判据把它真修到 24/24（G1 实测 100.00% 且严格 27/27）。
G3 之后以重跑值为准，登记为「索引被本轮实测纠正 1 条」，不算回归也不当收益来源。

## 复现入库
`center/stage_repros67.py --compile` ⇒ `test_repros/round67_diag1..6/` 共 **14 个 .py**（+.pyc 本机生成，
.gitignore 忽略 *.pyc）：diag1 join_after_noelse、diag2 guard_tern、diag3 四支（含被否决臂）、
diag4 handler_continue+controls、diag5 三支、diag6 三支（含被否决臂）。公开电池由 31 项增至 **45 项**。

## 阶段 C：串行门禁（落地后，顺序未换）
- **G1** `single site-packages/IQData/utils/common_func.pyc` → `decompile_status ok, total_functions 24,
  matched_functions 24, match_rate 100.00%, missing_in_decomp [], extra_in_decomp []`；
  严格尺 `OK 27/27 … 文件级：全部一致 1 / 1，有真缺陷 0`。
  （本轮「修到完全 OK」的靶＝common_func，由 diag2 的 or-chain 尾段判据闭掉。）
- **G2** quotation 官方 143/143 + 严格 `DEFECT 148/150`，缺陷集逐字为 `change_his_to_forward #250`、
  `get_trend #10`；market_time 官方 10/10 + 严格 10/10；IQData/utils/datetime_func 25/25+25/25；
  IQCommon/util/datetime_func 26/26+26/26。日志 `logs/gate/G2_*.txt`。
- **G3** `batch --index pyc_index.json --all --round 67`（background，exit 0）→
  `total_pyc 402 / verified_pyc 402 / ok_pyc 387 / partial_pyc 15 / failed_pyc 0`，
  `total_functions 5746 / matched_functions 5701 / cumulative_match_rate 99.22%`；索引已写回。
- **G4** `stats --index pyc_index.json` → 与 G3 逐字相同（5746 / 5701 / 99.22%，ok 387、partial 15、failed 0）。
  轮初发布值 5746 / 5698 / 99.16% ⇒ matched **+3**、完全匹配文件 **386→387**、partial **16→15**。
- **G4′** `strict_repo67.py all16.txt` 跑**已发布产物**：`STRICT TOTAL ok=659 / functions=727`
  （轮初 655/727、缺陷 72 → 68），且**每一支 `mirror-sha …=measured`**，即「出货字节 == 被测字节」逐支成立。
- **G5** `audit5_g5_67.py`：`entries HEAD=402 worktree=402、added=0 removed=0、key-shape diffs=0、
  round-stamp-only=399、substantive=3`（wizard 51→52；common_func 23→24 且 partial→ok；trade_live_broker 107→108），
  `status HEAD={ok:386,partial:16} → NEW={ok:387,partial:15}`，`matched 5698→5701 delta=+3`。
- **G5′** `blast67.py landed m67g`：`products identical=396 changed=6 unresolved=0`，改动集
  ＝wizard/api_base/common_func/realtime_event_source/trade_live_broker/quote，**恰等于 IMPROVED+MOVED 集**；
  官方指令缺口 Σ|Δ| 328→**296**；未手改任何 `*OK.py`（全部由工具链写）。
- **G6** 电池两列：31 项老清单（`battery_landed.jsonl`＝R66 字节 vs `m67g_battery.jsonl`）
  **115/127→116/127、IMPROVED=1(r66d3_pred 2/3→3/3)、WORSE=0、MOVED=0**；
  45 项公开清单（含本轮 14 支新复现）**161/200→174/200、缺陷函数 39→26、8 项变好、worse-than-landed=0、errors=0**。
  落地后 arm=landed 与 arm=m67g 已同字节（两列逐行相同），故另建 `center/mirr_r66`（HEAD blob + LF→CRLF 复原，
  两支 R66 指纹 sha256/大小逐字节命中 R66 提交记录）作真基线列，脚本 `center/mkmirr_r66.py`，
  日志 `logs/gate/G6_battery_r66_vs_m67g.txt`。

## 对本文先前两处读数的更正（落地后独立复算，出货记录以此为准）
1. **`Σmatched 5700` 作废**：`dump/m67g_402.jsonl` 实际合计 **5701/5746**，与 G3/G4 发布值、
   写回后的 `pyc_index.json` 逐支相同（`per-file diff vs published index: 0`、402/402 配对）。
   轮初 landed 5698 ⇒ **+3**，与 G5 的三条 substantive 一一对应。先前的 5700 是抄录自中间态（m67f）读数。
2. **「R66 索引对 common_func 乐观 1 条」作废**：HEAD 索引里 `IQData/utils/common_func.pyc` 是
   **(23, partial)**，与本轮 fresh `--arm=landed` 402 逐条比对 **inconsistent=0**
   （两侧 Σ 都是 5698/5746）。原判断的取数方式已不可复现（最可能是按 basename 键控时与同名兄弟
   `IQCommon/util/common_func.pyc` 串位——仓库里 common_func 有两支同名源），此处只以按 `path` 键控重算的
   `inconsistent=0` 为准。结论：本轮不存在「纠正索引乐观项」，common_func 23→24 是**真修复**，
   计入收益；G5 的三条 substantive 全部是改善方向。
3. G5′ 的 Σ|Δ| 以本次日志 **296** 为准（先前抄作 298）。
