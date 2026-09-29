# Round 75 · fix2 · F-PAD 8 + F-POLARITY 1 + F-OTHER 1 = 10 单元修复批 — FACTS

---

## 0. 结论一句话

mandate 达成：`IQCommon/util/trade_info_utils.pyc` **36/41 failure → 41/41 success**（`pyc_verify single`，
`status=success units=41/41 success_rate=100.00%`），副产物 `fly/simtradding/ptradeAccount.pyc` 135/137 →
**137/137 success**；最终臂 `ec_afgd5b` 门禁全过：官方 41 靶 `REGRESSION=0 ERR=0`、官方 402 全量
`SAME=395 REGRESSION=0 MOVED=7 ERR=0`、严格尺 defects `69 → 63 NEW=0 CLEARED=6`、金丝雀 `4/4`、
battery `worse=0`（82 repro）、ADR-1 `WORSE=0 IMPROVED=7`、G0 `20/20`、synth `PASS`。
BRIEF §1 的 10 个靶单元本批修绿 **3 个**（`kill_trade_process`、`query_strategy_id`、
`query_trade_strategy_info`），**7 个未修**（其中 2 个是 BRIEF 明标 IN/fix3 面的
`run_tick_socket`、`modify_batcktes_info`）。交付 = `FACTS.md` + `specs/` 15 份
（2 终稿 + 10 父本 + 3 归因隔离）+ `scripts/` 25 支 + `synth/` 10 + `synth/out/` 15
（复现 + 负例 + 5 合成形状）+ `dump/` 46 份读数。
**除本归档外 repo 零写入、未落地 402 全量、未手改 `*OK.py`。**

---

## 1. 批次形态与根因（三条独立规则，逐条单臂自证）

### 1.1 最终臂

| 臂 | spec | 文件 | edits | 行数 |
|---|---|---|---|---|
| `ec_afgd5b` | `specs/ec_ge.json` | `core/cfg/region_ast_generator.py` | 8 | +227（3 226 993 → 3 243 072 B，BOM+CRLF 保持） |
| 同上 | `specs/ad5b.json` | `core/cfg/region_analyzer.py` | 4 | +148（1 781 244 → 1 791 950 B，无 BOM） |

`ec_ge.json` = `grp_g`（5 edits）+ `editc9`（1）+ **edit-E1/E2**（2）；
`ad5b.json` = **edit-D**（2）+ `pad8_1f`（1）+ **edit-D2′**（1）。
构建链：`mk_ecg/mk_editc9 → ec_g.json` → `mk_edite.py → ede.json` →（合并）`ec_ge.json`；
`mk_editd4.py → ad4.json`、`mk_editd5b.py → editd5b.json` →（合并）`ad5b.json`；
`mk_g0comments.py`（补三要素注释行）与 `mk_g0fixes.py`（去 `getattr(self,...)`）为最后两步，均幂等。

### 1.2 规则 E（`ec_ge.json` 第 7/8 edits）：try 尾 `break` 桩被漏发

- **根因（生成器）**：`_generate_try_body` 主循环命中 `nested_region` 时走
  `nested_id ∈ _generated_regions/_generating_regions` 分支，随后的
  `if block in region.try_blocks:` 为**假**就只 `self.generated_blocks.add(block)` + `continue`
  —— 块被标成"已生成"却从未发射。探针 `mk_probe14.py` 读数：
  `TRYBODY n=2 hasBreak=False tail=['With','For']`、`MAIN598 gen=False role=BlockRole.BREAK`、
  `_generate_block_statements` 包装日志 `CALL598` **从未打印**（证明该函数根本没被调用）。
- **根因（分析器侧的来路）**：该 `FOR_ITER` 的 successor 落在 handler 之后，
  `Gappended has598=False ntry=18 try_offset_start=294 try_offset_end=598` ⇒ 598 ∉ `region.blocks`
  ⇒ 生成器无从按"region 内块"发射。E1 在 `_generate_try_body` 内把这类
  「FOR_ITER 耗尽出口 / 无副作用 JUMP 直落、`get_block_role ∈ {BREAK, PURE_BREAK}`、
  且落在 `region.try_offset_start .. handler` 之间」的块拉进 `_try_blocks_eff`
  （拉入记录 `_r75e_pulled`，供 E2 复用），E2 把判据放宽为
  `if block in region.try_blocks or block.start_offset in _r75e_pulled:`。
- **同层身份判据**：只用同层块对象的结构事实（末指令 opname、`get_block_role`、
  region 的 try/handler 偏移边界、`_r75e_pulled` 集合），无函数名/文件名/偏移常量阈值/名字白名单。
- **清掉的单元**（`mand41_ab_ecafd4e.json`，臂含 E、不含 D2′）：
  `get_trade_status`、`kill_trade_process`、`query_strategy_id`、`trade_operation`
  —— 其中 `kill_trade_process`、`query_strategy_id` 是 BRIEF §1 点名的 F-PAD 靶。

### 1.3 规则 D2′（`ad5b.json` 第 4 个 edit）：分支尾隐式 `return None` 不属任何分支臂

- **根因**：`_collect_branch_blocks` 的无界收集（`merge is None`）把「函数尾隐式 return」
  连同它的中转前驱一起收进臂内，产物把 `return None` 发在 if/try 体内。
- **第一版（edit-D2）的回归**：判据只看块的**末指令**是否隐式 return，
  不查块内是否还有用户语句。`IQCommon/data/asset_storage.pyc :: load` 的尾块形如
  `del new_assets; release_memory_with_measurement(); LOAD_CONST None; RETURN_VALUE`
  —— 被整块剔出 else 臂，两条语句外提（产物 `del new_assets` 由 12 空格掉到 8 空格）：
  官方尺 `8/8 → 7/8`（`p402_ecafd5e.jsonl` REGRESSION=1、`p1_asset_d5e.jsonl` 同）。
  **归因隔离**（`mk_t123.py` 三臂单变量）：`ecg_t_A` 8/8、`ecg_t_D` 8/8、
  `ecg_t_D2` 7/8 ⇒ 回归唯一来自 edit-D2，与 A/D/E 无关。
- **修正（D2′）**：加**纯度判据** —— 去噪后指令序列必须恰为
  `LOAD_CONST None; RETURN_VALUE` 或 `RETURN_CONST None`（长度 2 / 1），
  才允许剔除；否则保留。资产语句的尾块因此留在臂外。
- **清掉的单元**：`query_trade_strategy_info`（`ec_afgd4e` 40/41 → `ec_afgd5b` 41/41）。

### 1.4 其余 6 处（继承自本批前半程，单臂自证读数见 §3）

| edit | 文件 | 作用（一句话） | 单臂读数 |
|---|---|---|---|
| `editc9` | ast_gen | `IF_ELIF` 归约后残留的隐式 return 收口 | tiu 36→37、ptrade 不变、p402 `REGRESSION=0`、strict `69→68` |
| `grp_g` ×5 | ast_gen | 前导操作数 / `_is_implicit_ret_none` / 单前驱跨兄弟块尾 的成组修正 | tiu 36→37、ptrade 135→137 |
| `edit-D` ×2 | analyzer | `_collect_normal_exit_cleanup` 跨语句标记 + 两条 carve-out（纯占位 `JUMP_FORWARD` 块、handler 出口 jump 的纯隐式 return 尾） | 并入 `ec_afgd4e` 后 tiu 36→40 |
| `pad8_1f`（edit-A） | analyzer | with 正常退出清理扫描的让位判据 | 单臂 tiu 36→36（为 D/E 提供同层前置） |

---

## 2. BRIEF §1 十单元 i–iii 判定表（数据列来自 `center/fam75.json` + `mand41_ab_ecafd5b.json`）

| # | 单元 | 家族 | IN/OUT | lenA/lenB | 首分歧（fam75 reason） | 目标位移 Δ | mandated landed→cand | 本批判定（i/ii/iii） |
|---|---|---|---|---|---|---|---|---|
| 1 | `trade_live_broker :: _sync_worker` | F-POLARITY | OUT | 346/**345** | `idx 47 POP_JUMP_FORWARD_IF_TRUE -> POP_JUMP_FORWARD_IF_FALSE` | —（极性翻转） | fail→fail | **非 PAD**：真极性改写 + 1 条指令差（`len` 不等），须按 BRIEF §2.3 单独给行级对照，本批未动 |
| 2 | `trade_live_broker :: etf_basket_order` | F-PAD | OUT | 691/691 | `target 506 -> 934 lands on SAME instr, len equal` | +428 | fail→fail | **(iii) 纯位移**（指令序列同、字节距离差；BRIEF 要点 `EXTENDED_ARG 1 ≠ 3`）；本批未修 |
| 3 | `quote :: load_get_price` | F-OTHER | OUT | 168/168 | `opname POP_JUMP_FORWARD_IF_FALSE -> POP_TOP at idx 52` | —（缺一层判断） | fail→fail | **(ii) 多/少一层判断**（产品少一层短路判断）；本批未修 |
| 4 | `quote :: check_frequency` | F-PAD | OUT | 122/122 | `target 198 -> 236 lands on SAME instr, len equal` | +38 | fail→fail | **(iii) 纯位移**（mandate 候选，本批未修 ⇒ 交后续） |
| 5 | `quote :: run_tick_socket` | F-PAD | **IN** | 308/308 | `target 158 -> 364 lands on SAME instr, len equal` | +206 | fail→fail | **(iii) 纯位移**；BRIEF §2.4 标 IN（fix3 面），按硬规不自合并 |
| 6 | `trade_info_utils :: kill_trade_process` | F-PAD | OUT | 576/576 | `target 1120 -> 1124 lands on SAME instr, len equal` | +4 | **fail → success** | **(i) region 归约错位**（表象是 4 字节位移，真身是 try 尾 `break` 桩漏发；规则 E 修复后 mandated 转 success） |
| 7 | `trade_info_utils :: query_trade_strategy_info` | F-PAD | OUT | 109/109 | `target 210 -> 214 lands on SAME instr, len equal` | +4 | **fail → success** | **(i) region 归约错位**（分支尾隐式 `return None` 被收进 then 臂；规则 D2′ 修复） |
| 8 | `trade_info_utils :: query_strategy_id` | F-PAD | OUT | 105/105 | `target 202 -> 206 lands on SAME instr, len equal` | +4 | **fail → success** | **(i) region 归约错位**（同 #6，规则 E 修复） |
| 9 | `function :: reconnect` | F-PAD | OUT | 89/89 | `JUMP_FORWARD target 148 -> 174 lands on SAME instr, len equal` | +26 | fail→fail | **(iii) 纯位移**；本批未修 |
| 10 | `flytools :: ProcessWrite.modify_batcktes_info` | F-PAD | **IN** | 216/216 | `target 380 -> 404 lands on SAME instr, len equal` | +24 | fail→fail | **(iii) 纯位移**；BRIEF §2.4 标 IN（fix3 面），不自合并 |

**判定读数说明（Q1 答复）**：7 个 F-PAD 单元全部满足 `lenA == lenB` 且首分歧"lands on SAME instr"，
即**指令序列逐条相同、只有字节距离不同** ⇒ 表象属 (iii) 纯位移；
本批修绿的 3 个（#6/#7/#8）经探针证明**不是**补一条 NOP、也不是布尔短路，
而是**区域归属错位**（break 桩 / 尾 `return None` 发射层级不同），修复后 mandated 判据
「产品重新编译字节 == 原 pyc」直接转 success ⇒ 归入 (i)。
未修的 4 个 (iii) 单元（#2/#4/#9/#10）位移量 24–428 字节不等，需指令级定位
（`EXTENDED_ARG`/常量编码/多一条载入）后才能断言是"应判 SAME 的位移"还是"真 pad"，
本批未做 ⇒ 如实留档，交后续批。
另：本批**额外**修绿 2 个不在 10 单元内的单元 —— `trade_info_utils.get_trade_status`、
`trade_operation`（规则 E 顺带），以及 `ptradeAccount` 两个 `*_order_update`（规则 E/D 同源）。

---

## 3. 每臂 a–e 读数（`dump/perarm75_fix2.txt` 为机读原表）

a = 官方 41 靶 `h62 ab`；b = mandated `mand_ab` list41（tiu 单元 + ptrade）；
c = 金丝雀 4 支 `h62 ab`；d = battery；e = 严格尺。

| 臂 | a 官方41 | b mandated | c 金丝雀 | d battery | e strict |
|---|---|---|---|---|---|
| `pad8_1f` | SAME=39 REG=0 MOVED=2 ERR=0 | tiu 36→36、ptrade 135→135 | n/a | n/a | n/a |
| `grp_g` | SAME=39 REG=0 MOVED=2 ERR=0 | tiu 36→**37**、ptrade 135→**137** | n/a | n/a | n/a |
| `editc9` | SAME=40 REG=0 MOVED=1 ERR=0 | tiu 36→**37**、ptrade 135→135 | 4/4 REG=0 | n/a | 69→68 NEW=0 CLEARED=1 |
| `ec_afgd4e`（E、无 D2′） | SAME=38 **REG=0** MOVED=3 ERR=0 | tiu 36→**40**、ptrade 135→**137** | n/a | n/a | n/a |
| `ec_afgd5e`（E + D2 原版） | SAME=37 REG=0 MOVED=4 ERR=0 | tiu 36→**41**、ptrade 137 | 4/4 REG=0 | worse=0 | 69→63 NEW=0 CLEARED=6 |
| **`ec_afgd5b`（终稿）** | SAME=38 **REG=0** MOVED=3 ERR=0 | tiu 36→**41**、ptrade 137 | **4/4 REG=0** | **worse=0** | **69→63 NEW=0 CLEARED=6** |

p402（402 支官方全量）：

| 臂 | TALLY | fully matched |
|---|---|---|
| `editc9` | SAME=401 REG=0 MOVED=1 ERR=0 | 394 → 394 |
| `ecafd5e`（拒收） | SAME=**393 REGRESSION=1** MOVED=8 ERR=0 | 394 → **393** |
| **`ecafd5b`（终稿）** | SAME=**395 REGRESSION=0** MOVED=7 ERR=0 | 394 → **394** |
| `ecafd5b_v2 / _v3`（G0 注释与 `getattr` 修正后复跑） | 同上，且 402 份产物 **sha 逐位相同** | 394 → 394 |

---

## 4. 被拒臂与回归剖析（BRIEF §4「任何他支回归即整件拒收」）

- **拒收**：`ec_afgd5e` = `ec_ge + ad5`（edit-D2 原版）。官方 402 全量 `REGRESSION=1`：
  `IQCommon/data/asset_storage.pyc 8/8 → 7/8`，`mism=[['load', 190, 189, 2, 121]]`。
- **产品文本差分**（`build_landed` vs `build_ec_afgd5e`，唯一 1 处 hunk）：

  ```
  -            del new_assets                 (12 空格，else 臂内)
  -            release_memory_with_measurement()
  +        del new_assets                     (8 空格，if/else 外)
  +        release_memory_with_measurement()
  ```

  即两条真实语句**外提**（违「不得以少发射换全绿」的镜像形态：多发到错误层级）。
- **归因隔离**（`mk_t123.py` → `specs/t_A/t_D/t_D2.json`，三臂均 = `ec_g` + 子集，
  单变量，`dump/p1_asset_*.jsonl`）：

  | 臂 | 变量 | asset_storage `load` |
  |---|---|---|
  | `ecg_t_A` | 只加 `pad8_1f` | 8/8 |
  | `ecg_t_D` | 只加 edit-D 两处 | 8/8 |
  | `ecg_t_D2` | **只加 edit-D2** | **7/8**（同一 mism） |
  | `ec_afgd4e` | E + D + A，无 D2 | 8/8 |
  | `ec_afgd5b` | E + D + A + **D2′** | **8/8** |

- **处置**：不删规则（它正是 41/41 的最后一格），而是**收紧判据**（纯度检查）⇒ `ec_afgd5b`。
  拒收臂读数与隔离读数全部入档（`p402_ecafd5e.jsonl`、`p1_asset_*.jsonl`、`mk_t123.py`）。

---

## 5. 门禁读数（终稿 `ec_afgd5b`）

| 门 | 命令 | 读数 | 结论 |
|---|---|---|---|
| a 官方 41 靶 | `h62 run --arm=ec_afgd5b --list=list41.txt` + `ab` | `SAME=38 IMPROVED=0 REGRESSION=0 MOVED=3 ERR=0`（MOVED 三支 gained/lost 均空）、fully matched 33→33 | PASS |
| a′ 官方 402 全量 | `h62 run --list=list402.txt` + `ab` | `SAME=395 REGRESSION=0 MOVED=7 ERR=0`、fully matched 394→394 | PASS |
| b mandated | `mand_ab.py list41.txt landed ec_afgd5b` | `TOTAL CLEARED=7 NEW=0`；tiu `failure [36,41] → success [41,41]`；ptrade `failure [135,137] → success [137,137]` | **mandate 达成** |
| c 金丝雀 | `h62 run --list=list_canary.txt` + `ab` | `SAME=4 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0` | PASS |
| d battery | `closeout69.py battery landed ec_afgd5b` | `candidate columns worse-than-landed on 0 repro(s)`（82 repro） | PASS |
| e 严格尺 | `sstrict67.py build_ec_afgd5b list41.txt` | `ok=1655/1718、defects 69 → 63、NEW=0、CLEARED=6`（含 `get_trade_status`、`trade_operation` 两条 `target_diff` 消失） | PASS |
| ADR-1 | `adr73.py ec_afgd5b fam75.json` | 71 单元 `WORSE=0 IMPROVED=7 SAME=64`（`dump/adr74_ec_afgd5b.json`、`dump/adr73_ecafd5b.txt`） | PASS |
| G0 硬规 | `fix2/g0audit.py` | `20/20`：三要素注释 ✓、无 `self` 状态/`getattr(self,..)` ✓、无跨层 `X.entry in Y.blocks` ✓、无文件名/函数名白名单 ✓、无 `start_offset` 偏移阈值 ✓、两文件 `ast.parse`+`py_compile` ✓、BOM 与原件一致 ✓、repo `core/scripts/site-packages` 已跟踪零改动 ✓ | PASS |
| synth | `synth/build_synth.py` | `repro75_tiu` head `failure 36/41` → cand `success 41/41`（sha 不同）；`neg75_trytail` 两臂 sha `11e2e722c8d4d37e` 逐字节相同 | PASS |
| 等价性（G0 两处修订后） | `h62 run` 复跑 p402 | 402/402 产物 sha 与修订前逐位相同；battery `worse=0`；金丝雀 `4/4` | PASS |

---

## 6. 与 fix1 / fix3 的重叠面

- **fix1（F-ABSORB 61，`specs/jqop1.json`）**：靶是 `jq_trans_module :: replace_args` ×2
  （b-orphan-child 子机理）。与本批 10 单元 **0 交集**；本批任何 spec 都不含
  `_cjb_skip_inline_if` 路径的改写（`grp_g` 的前导操作数改动与 fix1 的嫁接助手不同层、不同文件段）。
- **fix3（inside-try 9 = F-ABSORB 7 + F-PAD 2）**：BRIEF §2.4 点名的 2 个 IN 单元
  `quote :: run_tick_socket`、`flytools :: modify_batcktes_info` 出现在本批靶表里，但按硬规
  **标注证据交中心、不自合并**：本批两臂对它们读数 `fail → fail`（与 landed 同状态），
  即本批未触碰 fix3 面，无交叠风险。
- **额外修绿但不属本批靶面**：`get_trade_status`、`trade_operation`（tiu）、
  `ptradeAccount.*_order_update` ×2、`quote_handler` 两个 `*_stocks_local`（strict CLEARED）。
  这些单元属 diag1 的其他家族 / R70 交接项（`trade_operation target_diff #94`），
  在 FACTS 里如实标注为**顺带收益**，不计入 10 单元达成率。

---

## 7. 遗留与交接（本批不修）

1. **4 个 (iii) 纯位移 F-PAD**：`etf_basket_order`（Δ428）、`check_frequency`（Δ38）、
   `reconnect`（Δ26）、`modify_batcktes_info`（Δ24）—— 需指令级定位（`EXTENDED_ARG`/常量编码）
   才能判定「应判 SAME」还是「真 pad」。
2. **F-POLARITY `_sync_worker`**（len 346/345 + `IF_TRUE→IF_FALSE`）：真极性翻转 vs `not` 消去
   的行级对照（lineA 1364 / lineB 841）本批未做 ⇒ BRIEF §2.3 仍欠。
3. **F-OTHER `quote :: load_get_price`**（产品少一层 `POP_JUMP_FORWARD_IF_FALSE → POP_TOP`）未修。
4. **切片型最小复现不可用**（工程事实，入档以免重踩）：真身 pyc 与本地 3.11.7 编译切片的
   `LOAD_GLOBAL NULL+name / LOAD_ATTR` 形态依赖**模块级符号表是否绑定该名字**
   （`import time` 才走 NULL+ 形态）；补齐 import 后 opname 签名已逐条相同，
   但 jump 目标仍差 4 字节 ⇒ 切片两臂 mandated 均 success、只有 sha 不同
   （`synth/probe_repro.txt` 5 个合成形状全部不触发、`synth/slice75_trytail.*` 同）。
   因此复现取**真身 pyc**，负例取合成结构（两臂 sha 相同）。
5. **`_cjb_skip_inline_if` 的语句上下文 or 操作数**（fix1 交接项）本批未接。

---

## 8. 证据索引（工作区 `D:/Temp/opencode/r75gate/fix2` → 本目录；共 112 份 / ~1.25 MB）

- **specs/（15 份）**：终稿 `ec_ge.json` + `ad5b.json`；父本 `ec_g.json`、`ede.json`、
  `grp_g.json`、`editc9.json`、`ad4.json`、`ad5.json`、`editd5.json`、`editd5b.json`、
  `pad8_1f.json`；回归归因隔离 `t_A.json`、`t_D.json`、`t_D2.json`
- **scripts/（25 支）**：spec 构建链 `mk_ecg / mk_editc9 / mk_edite / mk_editep / mk_editd /
  mk_editd2 / mk_editd4 / mk_editd5 / mk_editd5b / mkspec_pad8`；G0 `mk_g0comments /
  mk_g0fixes / g0audit`；归因 `mk_t123 / mk_probe10..14 / funcdiff`；
  运行 `run_arm / mand_ab / perarm / batt69 / mkspec_jqop`（后者供与 fix1 对照）
- **synth/（10）+ synth/out/（15）**：`build_synth.py`、`probe_repro.py`、
  `repro75_tiu.note`（真身 pyc 副本的重建说明；`repro75_tiu.pyc` 为字节拷贝故不入档，
  由 `build_synth.py` 重生成）、`neg75_trytail.py`、`slice75_trytail.py`、
  5 个合成形状 `a..e_*.py`、`out/{synth.json, landed_*.py, ec_afgd5b_*.py}` 两臂产物
- **dump/（46 份）**：`perarm75_fix2.txt`（机读 a–e 总表）、`g0audit.txt`、
  `battery_landed_vs_ecafd5b.txt`、`adr73_ecafd5b.txt`、`adr74_ec_afgd5b.json`、
  `probe_repro.txt`、`list1_asset.txt`、`list402.txt`；
  `list41_{landed,pad8_1f,grp_g,editc9,ecafd4e,ecafd5e,ecafd5b}.jsonl`（7）；
  `p402_{landed,editc9,ecafd5e,ecafd5b,ecafd5b_v2,ecafd5b_v3}.jsonl`（6）；
  `mand41_ab_{pad8_1f,grp_g,editc9,ecafd4e,ecafd5e,ecafd5b}.json` + `mand41_ab_grp_g.txt`（7）；
  `strict41_{landed,editc9,ecafd5e,ecafd5b}.json`（4）；
  `canary_{editc9,ecafd5e,ecafd5b,ecafd5b_v2}.jsonl`（4，head 在 `fix1/dump/`）；
  `p1_asset_{landed,c9,gg,t_A,t_D,t_D2,d5,d5e,d4e,d5b}.jsonl`（10，回归归因）
