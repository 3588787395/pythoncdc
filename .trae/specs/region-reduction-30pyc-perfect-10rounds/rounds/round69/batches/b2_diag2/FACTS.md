# Round 69 · diag2 · FACTS

代理：diag2（只读诊断）。靶支：`site-packages/fly/data/quote.pyc`。
臂名空间前缀：`r69diag2`。写入范围：本目录（dump/ specs/ synth/ logs/）。

## Step 0 · baseline replay

复放命令：`h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl`、
`h62.py run --arm=landed --list=canary.txt --out=dump/landed_canary.jsonl`、
`closeout67.py battery landed`、`sstrict67.py build_landed targets.txt dump/strict_landed.json`。

| 字段 | brief/targets.md 预读数 | 我的 landed 实测 | 相符? |
|---|---|---|---|
| quote 官方尺 | 70/81（gap 11） | **70/81** | ✓ |
| quote 严格尺 | 74/89 缺陷 15 | **74/89 缺陷 15，missing=0 extra=0** | ✓ |
| canary quotation | 143/143 | **143/143** | ✓ |
| canary market_time | 10/10 | **10/10** | ✓ |
| canary IQCommon datetime_func | 26/26 | **26/26** | ✓ |
| canary IQData datetime_func | 25/25 | **25/25** | ✓ |
| battery | 182/200、缺陷 18、worse=0、ERR=0 | **182/200、defect-row 18、worse-than-landed=0、ERR=0** | ✓ |

官方缺陷 11 支（`h62` 读数，`[name, orig, decomp, hunks, first_diff]`）与 targets.md §OFF 逐行相同：

| 函数 | orig | decomp | hunks | first_diff |
|---|---|---|---|---|
| build_current_period_df | 115 | 108 | 5 | 12 |
| check_frequency | 121 | 120 | 1 | 21 |
| check_limit | 330 | 311 | 2 | 248 |
| get_individual_data | 312 | 311 | 1 | 156 |
| get_price | 230 | 232 | 0 | 172 |
| get_real_from_zeromq | 703 | 678 | 0 | 660 |
| initImagedata | 243 | 225 | 0 | 190 |
| load_bars_from_hundsun | 477 | 483 | 0 | 410 |
| load_get_price | 171 | 171 | 0 | 1 |
| run_individual_transform | 362 | 321 | 2 | 263 |
| run_tick_socket | 306 | 307 | 2 | 228 |

严格尺 15 支与 targets.md §STRICT 逐行相同（含 4 支 target_diff/seq_diff 定位类：
change_his_to_backward#213、change_his_to_forward#241、check_industry_code#159、
load_get_price#53、run_tick_transform#56）。

**结论：Step 0 与 brief/targets.md 逐字段相符，无更正。**

## Step 1 · hunk tables（nested_diff.py，按 code-object 全路径配对）

产物：`build_landed/fly__data__quoteOK.py`；日志 `logs/nested_landed.txt`。
nested_diff 归一化只把跳转归为 `OP J`；NOP / EXTENDED_ARG 仍会成 hunk，下表已标注。

| code object | orig | decomp | 归一化 hunk | 判定 |
|---|---|---|---|---|
| /Quote#22（模块） | 264 | 257 | 1 | 伪影（delete 7×NOP） |
| build_current_period_df#28 | 124 | 113 | 2 | 1 伪影(EXT) + 1 真：orig[109:121] `tempdict['is_open']=pandas.DataFrame(...)` → decomp `POP_TOP, LOAD_CONST None` |
| load_bars_from_hundsun#29 | 526 | 533 | 1 | 真（过冲/重复）：decomp[49:56] 多出 `os.path.exists(DumploadDailyFile...)` 7 条 |
| load_get_price#30 | 185 | 185 | 1 | 真（极性）：orig `POP_JUMP_FORWARD_IF_FALSE` → decomp `POP_TOP` |
| change_his_to_forward#31 | 572 | 573 | 3 | 伪影（EXT×2 + NOP×1）；严格尺另见 target_diff |
| get_price#40 | 256 | 258 | 1 | 真（过冲）：`POP_JUMP_FORWARD_IF_NONE` → `LOAD_CONST None; IS_OP; POP_TOP` |
| check_stocks#59 | 71 | 70 | 1 | 伪影（delete NOP） |
| check_industry_code#61 | 196 | 196 | 1 | 真（极性）：IF_TRUE → IF_FALSE |
| check_frequency#63 | 132 | 133 | 2 | 真：中段 `LOAD_CONST None; RETURN_VALUE` → `JUMP_FORWARD`，return 被搬到函数尾（早退 return 扁平化） |
| get_real_from_zeromq#66 | 793 | 767 | 8 | 真：−24(丢 f-string 日志) −30+30(flag==1 块后移) −1(UNPACK) −2(STORE exc_*) +1(EXT 伪影)；`LOAD_FAST exc_tb`→`LOAD_GLOBAL exc_tb`×2 |
| run_individual_transform#72 | 412 | 359 | 11 | 真（大规模丢失/错位）：`socket.recv`/`eval` 段丢失、`set`→`isSet`、尾部多 `return None` |
| run_tick_transform#73 | 326 | 327 | 1 | 伪影（EXTENDED_ARG） |
| run_tick_socket#74 | 347 | 348 | 4 | 2 伪影(EXT) + 2 真：`warning('tick数据返回为空')` 由 orig[93:117] 搬到 decomp[205:230] |
| initImagedata#75 | 273 | 251 | 1 | 真（丢语句）：delete orig[38:60] `self.log.quote.debug(f'...')` 22 条 |
| get_individual_data#81 | 354 | 354 | 4 | 1 伪影(EXT) + 3 真：`if flag==1` 块 178→325 后移、尾部多 `return None` |
| check_limit#88 | 356 | 334 | 1 | 真（丢语句）：delete orig[54:76] `self.log.quote.info(f'...')` 22 条，其余全等 |

`change_his_to_backward` 在 nested_diff 下无差异（跳转已归一），差异只在严格尺 target_diff。

## Step 2 · 根因（实测打印，非读码推断）

### 缺陷族 A：while 复合条件链块的前导语句里，非 Assign 段被丢弃
（check_limit / initImagedata / get_real_from_zeromq 三支各丢 1 条 `self.log.quote.<m>(f'...')` 表达式语句）

实测链路（logs/probe_blocks.py、logs/hook_stmt.py、logs/hook_all.py，watch=块@286）：

1. check_limit 的区域树：`IfRegion@0 merge_block=286`；`BoolOpRegion entry=286 blocks=[286,486] parent=LoopRegion@486`；`LoopRegion@486 blocks=[864,486,498,550,658,670,776]`（不含 286）。
2. 块@286 实测 37 条指令（offset 286..484）：`286..402 = self.log.quote.info(f'...')`（POP_TOP 收尾）、`404..476 = redata, flag = api_get_from_zeromq(...)`（UNPACK+2×STORE）、`478..480 = count = 0`、`482..484 = LOAD_FAST redata; POP_JUMP_FORWARD_IF_TRUE 876`。
3. 生成侧 region_ast_generator.py `_loop_generate_while` L6005-6066：对 `boolop_for_while.op_chain` 中不在 loop_blocks 的链块（=块@286）切「前导语句段」（按 STORE_*/POP_TOP 切段 L6018-6055），逐段：
   - 有 UNPACK → `_build_unpack_assign_from_segment` → 追加；
   - 否则 `expr_reconstructor.reconstruct(segment)`，**仅当 `type=='Assign'` 才 `pre_stmts.append`（L6064-6066）**。
   ⇒ POP_TOP 收尾的表达式语句段重建出 Expr，被 `'Assign'` 判据直接丢掉。
4. 同函数 L6149-6165 的回边重检分段器是三级兜底（unpack → `_build_store_statement` → `_build_statement`），能产出 ast.Expr——两条分段器不一致，正是 L6041-6047 注释声称「段级 fallback 产出 ast.Expr」而代码未实现处。
5. hook 实测：`_build_statements_from_instructions` / `_build_statement` / `_build_store_statement` / `_generate_block_statements` 对 check_limit **0 次**覆盖块@286 ⇒ 该块前导语句只由 L6005-6066 一条路产出，丢段即丢语句，无第二发射者。
6. `gen.generate()` AST 实测：body[4]=Assign redata,flag、body[5]=Assign count、body[6]=While；Expr(log) 不在 body；三个缺失字符串在产物中 count==0。

**缺陷族 A 根因**：core/cfg/region_ast_generator.py `_loop_generate_while` L6063-6066 的「前导段只收 Assign」判据，把 while 复合条件链块前导段里的表达式语句段丢弃。


---

## Step 4 — 候选 spec（family A，唯一可落盘文件）

- spec：`specs/cand_r69diag2_a.json`（生成器 `specs/mk_r69diag2_a.py`）
- 目标文件：`core/cfg/region_ast_generator.py`（三支可落盘之一）
- edit 数 = 1；anchor = LF 归一后 L6056-6066 共 11 行；`u.count(anchor) == 1` 断言通过（anchor 唯一）；`h62 build` 断言 BOM=True / nl=CRLF / 行数守恒全部通过
- 臂名：**`r69diag2a`**（`h62.py build --spec=specs/cand_r69diag2_a.json --dst=r69diag2a` → `mirrors built: head pristine == worktree bytes, cand patched (1 edits, core/cfg/region_ast_generator.py, BOM=True, nl=CRLF)`；镜像 `py_compile` OK）
- 机制（只改 `_loop_generate_while` L6063-6066 一处）：在 `if ... .get('type') == 'Assign'` 之后追加一条 `elif`——当段尾 `opname ∈ {STORE_FAST, STORE_NAME, STORE_GLOBAL, STORE_DEREF, STORE_ATTR, STORE_SUBSCR, POP_TOP}`（即**同块同层的语句终结符**，正是本函数 L6032 / L6048 两处切段判据本身）时，走与**同函数回边重检分段器 L6149-6165 逐字同一条**的三级重建 `_build_store_statement → _build_statement`，产出 `append` 进本区域 `pre_stmts`（位于 While 之前、与 While 同层的兄弟语句）
- 三要素注释已随 repl 写入源文件（识别条件 / 归约方式 / AST 映射），见 `mirr_r69diag2a/core/cfg/region_ast_generator.py` L6064-6089
- 不新增 self 或帧内状态、不改 `block_to_region`、不抑制任何已发射语句、只 append 不回改（单向一次正确）
- 同族不同件：与已撤回的 `cand_r68_else_join_cut` 不同族（那件改 else-join 裁剪路径且方向是**删**；本件改 while 条件链前导段的**保留**路径且方向是**增**，位置、函数、方向三者均不同）

## Step 5 — 五列读数（臂名 `r69diag2a` vs `landed`）

| 列 | landed | r69diag2a | 判定 |
|---|---|---|---|
| targets 官方尺（quote.pyc） | **70/81** | **72/81** | IMPROVED |
| targets 16 支全表（`all16.txt`） | — | SAME=15 **IMPROVED=1** REGRESSION=0 MOVED=0 ERR=0 | 无回归 |
| 严格尺（`sstrict67 build_<arm> targets.txt`） | **74/89 缺陷 15**（missing0 extra0） | **76/89 缺陷 13**（missing0 extra0） | IMPROVED，无新增 target_diff |
| battery（`closeout67.py battery landed r69diag2a`） | 182/200 缺陷 18 ERR=0 | 182/200 缺陷 18 ERR=0 | SAME，worse-than-landed **0/45** |
| canary（4 支 sha） | 4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177 | 四个 sha **逐字相同** | SAME=4 IMPROVED=0 REGRESSION=0 ERR=0 |
| synth（`synth/r69diag2_synth.txt` 2 支） | f = 1/2（`r69diag2_whilepre.pyc` 缺陷） | **f = 2/2** | 咬合成立 |
| landproof（`closeout67.py landproof mirr_r69diag2a`） | — | 33 core files，same=32 **diff=1**（唯一 diff = 被编辑的 `region_ast_generator.py`） | 无越权改动 |

### ADR-1 合规自检（family A）
- 族别：**缺失族（seq_len）**
- Σ\|orig−decomp\|（11 支官方缺陷函数，h62 读数）：**121 → 62**，净 **−59**，严格下降
- **不是靠少发射换的**：decomp 计数只增不减——`check_limit` 311→330（缺陷消除）、`initImagedata` 225→245（缺陷消除）、`get_real_from_zeromq` 678→700（Δ 由 −25 收到 −3）；无一支 decomp 计数变小
- 严格尺新增 target_diff = **0**：`change_his_to_backward` / `change_his_to_forward` / `run_tick_transform` 三支原有 target_diff 逐条仍在，无新增行
- 完全匹配函数 +2（`check_limit`、`initImagedata` 出榜）；`nested_diff` 差异 code object **16 → 14**

### 与撤回件 `cand_r68_else_join_cut` 的差异证明（贴臂名读数）
- R68 撤回件读数（BRIEF 记录）：`matcher 715/715 → 713/466`、`quote 70/81 → 64/81`，全为删除类回归
- 本件 `r69diag2a` 读数：
  - `all16.txt`（含 matcher.pyc 的 16 支）：**SAME=15 / IMPROVED=1 / REGRESSION=0 / MOVED=0 / ERR=0**
  - `matcher.pyc`：h62 **17/17 → 17/17**；`nested_diff` 两侧产物**逐字节相同**（`logs/nested_matcher_landed.txt` == `logs/nested_matcher_r69diag2a.txt`，均 `match#16 orig=800 decomp=807 hunks=7`，7 个 hunk 全为 EXTENDED_ARG 伪影）——与 R68 的 715→713/466 **完全不同**
  - `quote.pyc`：**70/81 → 72/81**（与 R68 的 64/81 方向相反）
- 结论：不同族、不同位置、方向相反（只增不删），三支读数均无回归

### VERDICTS（nested_diff，仅列受影响者）
| code object | landed | r69diag2a |
|---|---|---|
| check_limit#88 | 356/334 hunks=1 **缺陷**（delete orig[54:76] 22 条 `self.log.quote.info(f'...')`） | **全匹配，出榜** |
| initImagedata#75 | 273/251 hunks=1 **缺陷**（delete orig[38:60] 22 条 `self.log.quote.debug(f'...')`） | **全匹配，出榜** |
| get_real_from_zeromq#66 | 793/767 hunks=8 | 793/791 hunks=7（−24 条 f-string 日志删除 hunk 消失，残余 gap=2 属他族） |
| 其余 10 支（build_current_period_df / check_frequency / get_individual_data / get_price / load_bars_from_hundsun / load_get_price / run_individual_transform / run_tick_socket …） | — | h62 读数逐条不变 |
| 差异 code object 总数 | 16 / 92 | **14 / 92** |

### 候选名（最终回报用）
`cand_r69diag2_a_while_chain_prefix_expr_keep`（spec：`specs/cand_r69diag2_a.json`，臂：`r69diag2a`）

### 对 BRIEF 的更正
- 无。Step 0 逐字段核对无出入，本步亦未发现 BRIEF 记载的读数、位置或规则有误。
