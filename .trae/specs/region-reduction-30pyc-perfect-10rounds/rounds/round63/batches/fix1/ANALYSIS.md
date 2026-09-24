# Round 63 · batch 3 (fix1) · ANALYSIS

靶见证：`site-packages/IQEngine/plugins/plugin_system_matcher/matcher.pyc :: Matcher.match`
丢失原源码行 227/228/229 三条语句（`stock_listed_date = …` / `next_trading_date = proxy.get_next_trading_date(…)`
/ `is_first_five_trading_days = a <= b <= c`，26 条指令，过滤后 deficit −24）。
候选：`specs/cand_r63b3_chainstore.json`（5 edits，净 +165 行，arm=g1）。

---

## 1. 实测到的 bail 分支（不是猜的）

探针 `probe_bail.py` / `probe_bail2.py`（`sys.settrace` 行追踪 + 关键子函数返回值记录，
只在 `condition_block` 首偏移 == 1696 的那一次 `_generate_ternary` 调用上触发），
日志 `logs/bail_landed.txt`、`logs/bail2_landed.txt`。区域事实（bail_landed.txt 头部）：

```
condition_block = 1696..1818(21)   true_value_block = 1820..1828(3)
false_value_block = 1830..1832(2)  merge_block = 1834..1882(11)
merge_context='store'  value_target='is_first_five_trading_days'
blocks = [1696..1818(21) 1820..1828(3) 1830..1832(2)]
```

执行轨迹（`bail2_landed.txt` 逐条，行号即轨迹行）：

| 步 | 事实 |
|---|---|
| L34423 | 进入 **R106 链式比较分支**（`_build_ternary_boolop_condition`@L34406、Phase-7-D@L34412 均未命中） |
| 2 | `_detect_chained_compare_pattern(1696..1818)` → `{'compare_ops': ['<=','<='], 'extra_chain_blocks': [1820..1828(3)]}` |
| 3-4 | `_build_chained_compare_from_region_data` → `_try_build_method_call_chained_compare` 返回**完全正确**的 `Compare(stock_listed_date <= self._engine.trading_dt <= next_trading_date)` |
| 5 | `_build_ternary_value_expr(1820..1828)` → `Name next_trading_date`（非空） |
| 6 | `_build_ternary_value_expr(1830..1832)` → **None** |
| 8 | **RETURN `_generate_ternary` line 37552 → None** |

轨迹尾部的行序列 `… 35149,35150,35151,35152,35153,35151,35155, 37552`` 指明落空点：
**`L35155 if cond_expr and true_expr and false_expr:`** —— `false_expr` 为 None 使整个合取式为假，
函数从 L35155 直接掉到隐式 `return None`（L37552）。
即：三个部件里唯一失败的是**假值臂表达式**，而链式比较的假值臂按 CPython 3.11 展开根本不是值分支，
是清理臂 `SWAP 2; POP_TOP`（1830..1832）——`_build_ternary_value_expr` 对它必然返回 None。
本批修正了上一批「逃逸发生在更深处」的猜测：逃逸点就是这个 IfExp 三元合取判据本身。

登记侧后果（`_process_if_blocks` L21969-21982）：`child_ast` 为空 → 分支序列不 emit 任何语句，
但 `for b in nested.blocks: self.generated_blocks.add(b)` 无条件执行 → 1696..1818 的 21 条
与 1820..1828、1830..1832 全被判为「已生成」，三句整体消失。

前导语句划界实测（`logs/split_landed.txt`、`logs/split2_landed.txt`，`probe_split*.py`）：
1696..1818 的前向栈深在偏移 1782 处**恰好归零**，严格深度判据可切出 1696..1782 = 2 条 Assign；
`_split_block_condition_prefix` 之所以返回 `[]`，**唯一**原因是终止符门（L388）
`JUMP_IF_FALSE_OR_POP ∉ FORWARD_CONDITIONAL_JUMP_OPS | NONE_CHECK_OPS`。
（曾担心 `dis.stack_effect(CALL)` 会让深度算错，故未手算而是实测：PRECALL 仍在块内，1782 处深度确为 0。）

## 2. 落地方案（区域化 / 单向数据流 / 一次正确）

全部改动在 `_generate_ternary` **内部**及其私有 helper，不改登记侧、不改区域分析器：

* E0/E1：`_split_block_condition_prefix(block, terminator_ops=None)` —— 形参默认 None 时判据与既有一字不差
  （Assert/Loop 两个既有消费者逐字节不变），[R63-b3] 允许调用方把语义同族的短路条件消费指令
  （`JUMP_IF_FALSE_OR_POP`/`JUMP_IF_TRUE_OR_POP`）纳入终止符；栈深归零判据一字未动。
* E2：新增 `_r63b3_is_chain_cleanup_arm`（纯栈重排/丢弃/无条件跳转族 + 至少一条 POP_TOP + 栈效应之和 ≤0）
  与 `_r63b3_reduce_value_ctx_chain_store`，按四条结构合取判据把该区域归约为**一个** Assign 抽象节点：
  `Assign(targets=[Name(value_target, Store)], value=Compare(left, ops=[LtE,LtE,…], comparators=[…]))`，
  块内前导段经 `pre_stmts` 随该 Assign 一同返回父序列（与 L33532-33543 `_build_ternary_boolop_condition`
  的既有划界同一实现、同一发射通道），区域成员块在本 helper 成功时才登记。任一判据不满足即 `return None`，
  保守让位给既有路径。
* E3/E4：在 Phase-7-D 与 R106 两个链式比较分支的 `generated_blocks.add(_cb)` 之后挂钩。
所有判据均带 识别条件 / 归约方式 / AST 映射 三段中文注释；无偏移特例、无函数名特例、无阈值调整。

触发点区域数据（`logs/fire_landed_s1.jsonl`，全量 firing set 探针）：
`entry=1696 ops=['<=','<='] cc_blocks=1 ctx='store' target='is_first_five_trading_days'
cond=1696..1818(21) tvb=1820..1828(3) fvb=1830..1832(2) merge=1834..1882(11) reduced=true stmts=3 pre=2`
（`chained_compare_ops` 在 `_generate_ternary` 入口确为 `[]`，在挂钩点已被 R106 分支填好，判据取的是后者。）

## 3. 见证前后行

| 测量 | 臂 | 文件 | 函数级 | `match` 行 [orig, decomp, jump, true] | 产物 sha256[:16] |
|---|---|---|---|---|---|
| 前 | f4（BASE_FACTS） | matcher.pyc | 16/17 | [713, 689, 9, 524] | f7821a793de7106b |
| 前 | landed@03:54（落地前 worktree） | matcher.pyc | 16/17 | [713, 689, 9, 524] | f7821a793de7106b |
| 前 | **nog1**（现 worktree − 本候选） | matcher.pyc | 16/17 | [713, 689, 9, 524] | f7821a793de7106b |
| 后 | **g1**（本候选） | matcher.pyc | 16/17 | **[715, 715, 10, 517]** | 74f9b8dcce12798c |
| 后 | landed@现（主循环已落地本候选） | matcher.pyc | 16/17 | [715, 715, 10, 517] | 74f9b8dcce12798c |

三条语句已在 g1 产物 L199-201 复原：
`build_g1/IQEngine__plugins__plugin_system_matcher__matcherOK.py`（222 → 226 行）。
deficit −24 → **0**（26 条丢失指令全数收回），truediff 524 → 517。

## 4. 17/17 门禁不可达：第二处独立缺陷（证伪）

`match` 仍 mismatch 的原因是**另一处与本案无关的既有位移缺陷**：
orig 索引 180..462（282 条指令，源码 219-232 区段，偏移 1314..~3200）被整体投到产物尾部
（decomp 428..713，偏移 3060..4980），而 `if self._volume_limit:`（原 292 行 / 产物 161 行）占了前面的槽。
`probe_align.py` 两份 hunk 表逐字节对照（`logs/align_landed.txt` vs `logs/align_g1.txt`）：

```
--- replace orig[180:462] decomp[180:181]      # 两臂完全相同（前/后皆有）
--- insert  orig[713:713] decomp[428:687]      # 前：259 条
--- insert  orig[713:713] decomp[428:713]      # 后：285 条（= 259 + 收回的 26 条）
RATIO 0.5926（前）  vs  0.5818（后）
```

位移 hunk 的边界一字未动 → 本候选既不制造也不修复它；jumpdiff 9→10 亦来自该位移而非本案语句。
结论：**本批不能声称 17/17**，17/17 需要另外处理 `if self._volume_limit:` 与 282 指令块的次序问题
（属区域排序/发射次序缺陷，与值语境链式比较归约正交）。

## 5. 本批证伪与踩坑

* **基准漂移**（本批最重要的方法论教训）：`specs/cand_r63b3_chainstore.json` 已于 04:20 被主循环落进
  worktree，`--arm=landed` 从此不再等于「无本候选」。第一次全量 A/B（dump/wl.jsonl，04:22-04:23）因此
  把 04:08→04:20 之间落地的其他批次改动（[R63-B4 Fix1]、R63 f-string Fix1/Fix2）记到了本候选头上，
  出现假 MOVED（`flyAccount.pyc::_do_request` 429 vs 443）。
  修正办法：`mkrevert.py` 生成 `specs/cand_r63b3_revert.json`（5 edits 逆序 anchor/repl 互换，净 −165 行），
  `mbuild.py nog1` 得 `mirr_nog1 = 现 worktree − 本候选`，恢复单变量对照。
  复核证据：`flyAccount` 在 g1 上 `_r63b3_reduce_value_ctx_chain_store` **enters=0**（201 文件同进程
  firing-set 探针 `logs/fire_g1_s0.jsonl`），且单文件/201 文件两种上下文下 landed 现值均为 443 = nog1；
  该 429/443 差与本候选无关。
* 早前对「`_generate_ternary` 入口 `chained_compare_ops=[]`」的担心被否：挂钩点（R106 分支内）区域数据已填齐，
  判据取的是填齐后的值（见 §2 firing 记录）。
* 曾手算怀疑 `dis.stack_effect(CALL)` 会使深度切分过细 → 实测否证（§1）。

## 6. 爆炸半径（单变量，同基准 nog1 → landed）

* 全量 402（`all402.txt`）：`dump/wn.jsonl` vs `dump/wl2.jsonl`
  `REGRESSION=0 IMPROVED=0 MOVED=1 SAME=401`，matched 5677→5677，clean 382→382；
  **文本变化的产物只有 1 份**——靶 matcher.pyc（`match 713→689(−24)` 变 `715→715(+0)`）。
* 机制侧同数：全量 402 firing set（`logs/fire_g1_s0.jsonl` + `logs/fire_landed_s1.jsonl`）
  = 3 enters / **1 reduction**（靶）；两处近似命中（`real_quote.pyc`、`quote.pyc` 的
  `data_count`，cond=8..48(9)、fvb=96..96(1) 单指令清理臂）被结构判据**保守拒绝**（reduced=false），
  故其产物逐字节不变 —— 与 SAME=401 一致。
* R62 钉住的 6 个形态见证（`shapes_r62.txt`）：`dump/shapes_landed.jsonl` vs `dump/shapes_g1.jsonl`
  → `REGRESSION=0 IMPROVED=0 MOVED=0 SAME=6`，matched 10→10 clean 4→4，
  6 份产物 sha 与中央基线 `D:/Temp/opencode/r63gate/dump/sh_landed.jsonl` **逐字节相同**（eec02b27…/ac81ea45…/
  50190789…/43a96728…/01eb611f…/a64563a7…）。

## 7. 合成复现（deliverable 3）

`F:/Downloads/pythoncdc-main/test_repros/round63_fix1/r63b3_chainstore_prefix.py` + `.pyc`（2724 B，本机 3.11.7 编）。
结构三条件（写在文件 docstring 里）：值语境链式比较 + 同块含 LOAD_METHOD 调用的已完结前导赋值 +
位于 if/elif/…/else 链的 else 分支内且兄弟分支全以 `continue` 收尾（→ 由 `_process_if_blocks` 作嵌套三元子区域派发）。

| 臂 | 结果 |
|---|---|
| nog1（无本候选） | `1/2`，`probe [149, 129, 5, 91]`，三句 + 整个 `else:` 单元丢失，后续 `if` 被错折成 `elif`（`dump/repro_nog1.jsonl`） |
| landed / g1（有本候选） | `2/2`，`mism=[]`（`dump/repro_landed.jsonl`、`dump/repro_g1.jsonl`） |

产物逐行 diff：`build_nog1/…r63b3_chainstore_prefixOK.py` 48 行 → `build_g1/…` 52 行，
新增正是 `stock_listed_date = listed_dt` / `next_trading_date = proxy.get_next_trading_date(…)` /
`is_first_five = stock_listed_date <= trading_dt <= next_trading_date` 与正确的 `else:` 嵌套。
（上一批的 `test_repros/round63_b3/r63b3_chained_value_ctx_prefix.py` 不复现，缺的正是条件 2/3。）

## 8. 镜像与健康度

| 镜像 | 字节 | BOM | CRLF | 裸 LF | ast.parse | py_compile | sha256[:16] |
|---|---|---|---|---|---|---|---|
| `mirr_g1`（+165 行） | 3,069,504 | True | 49,628 | 0 | OK | OK | 082fa9910150acc9 |
| `mirr_nog1`（−165 行，仅对照用，不得落地） | 3,076,514 | True | 49,772 | 0 | OK | OK | 8654498ffdc74e59 |

对照臂有效性三重核验：`cand_r63b3_revert.json` 5 逆序 anchor 各命中一次且净 −165 行；
`mirr_nog1` 在靶上复现原始见证行 `[713, 689, 9, 524]` / sha f7821a793de7106b（与 03:54 落地前
`dump/landed.jsonl`、BASE_FACTS 的 f4 行三者逐字节相同）。
（注：个别 edit 的 anchor 文本在落地后的 core 中仍作为子串存在——repl 保留了 anchor 的部分原行，
落地态以「12 处 `_r63b3_` + 逆序 revert 唯一命中」为准，不影响对照正确性。）

## 9. 文件清单

fix1 内：`ANALYSIS.md`（本件）、`specs/cand_r63b3_chainstore.json`（候选）、
`specs/cand_r63b3_revert.json` + `mkrevert.py`（对照臂）、`mkspec_r63b3.py`（候选构造，anchor 唯一性断言）、
`probe_bail.py`/`probe_bail2.py`/`probe_split.py`/`probe_split2.py`/`probe_instrs.py`/`probe_align.py`/`probe_fire.py`、
`logs/{bail_landed,bail2_landed,split_landed,split2_landed,align_landed,align_g1,fire_g1_s0,fire_landed_s1,fire_fly,fire_small}.txt|jsonl`、
`dump/{landed,g1,baseline,shapes_landed,shapes_g1,wl,wl2,wg,wn,repro_*}.jsonl`、`mirr_g1`/`mirr_nog1`、
`build_landed`/`build_g1`/`build_nog1`、列表 `targets.txt`/`shapes_r62.txt`/`all402.txt`/`repro.txt`。
仓库内新增（未跟踪）：`test_repros/round63_fix1/r63b3_chainstore_prefix.py` + `.pyc`。
未动：仓库 core 文件、`site-packages/**/*OK.py`、`pyc_index.json`；未跑 `pyc_batch_verify single|batch`、`_r13_gate.py`、任何改状态的 git 命令。

---

## 10. 集中验证方补记（主代理，04:38，落地后）

你的返场读数已采纳，两处据此更正了集中记录：

1. 主代理曾在你离场后用 `dump/wl.jsonl`（落地后 worktree）对 `dump/wg.jsonl`
   （`mirr_g1`，落地前基线）跑过一次 ab，得到 `REGRESSION history_data_source 18/18->16/18`
   与 `MOVED trade_live_broker`。主代理当时已判为基线错配（`mirr_g1` sha
   `082fa9910150acc9f2a7` == 集中 `mirr_f1`，`getattr(region,` 计数 175 即缺 tern_slot），
   你 §6 的单变量 402（`REGRESSION=0 IMPROVED=0 MOVED=1 SAME=401`）与此一致，
   该错配对照不再作为任何结论的依据。`flyAccount` 的 MOVED 归 b4 成对、
   `trade_live_broker` 的 106→123 归 b1f fstail，`EVIDENCE.md` F.1/F.6 已按逐支归属重写。
2. 主代理在**落地字节**上独立复测了你 §7 的新复现：
   `h62.py run --arm=landed --list=dump/fix1repro.txt --out=dump/rp63_fix1_landed.jsonl`
   → `r63b3_chainstore_prefix.pyc 2/2 []`。电池清单因此从 16 项增至 **17 项、clean 8 项**
   （`EVIDENCE.md` F.3 已更新）。

`matcher::match` 停在 16/17 的第二处位移缺陷（`orig[180:462]` 282 条投到产物尾部、
两臂 hunk 表相同）已作为 R64 头号线索写入 `rounds/round63/OUTCOME.md` §6。
