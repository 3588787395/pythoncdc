# Round 30 —— 内层 loop 的 break 角色核验抢走承载外层回边的块（R30-C1）

基线：`06f0ba50`（Round 29 落地 ＋ 补记之后）。本轮只落地**一条同层判据**，作用面在
`core/cfg/region_analyzer.py` 的 LoopRegion 构造路径（`_r102` 块的 break 核验循环）。
核改动 `git diff --numstat` = **11 0**（5 行判据注释 ＋ 6 行代码），纯 CRLF 保持、该文件本就无
BOM，落地后与测量镜像 `mirr_c1c` **sha256 逐字节相同**（`7ee4151d31faf41b8202…`，1673044 →
1674078 字节）。

## 一、目标池与三条诊断线（均实测）

索引口径 deficit==1 的文件本轮 8 个、partial 32、Σdeficit 104（`logs/pool30.txt`）。三条线：

**线 A —— 异常尾声发射侧（Round 28/29 两次移交项）：判据否证，且同族归并被拆开。**
候选 R30-A（预消解侧拒绝消费 bare-return-None 尾声）**改进 0**：靶子
`risk_calculation/function.pyc :: save_testds_to_json` 只是把缺的那份副本移到函数尾（仍 310），
并在合成锚 `r2_09_bool_cond_invert_dec*` 上造成**真回归 102/102 → 96/80** ⇒ REJECTED。
对 `fly/common/flytools.pyc :: FileLock.acquire` 产物**字节零改动**：它的尾声载荷是
`STORE/DELETE e`（`except-as e` 清理）而非 `return None`，且混着裸 raise 迁移与环尾回边丢失。
⇒ Round 28 把两者记为「同一族」是错的，两个靶子需要两条不同的发射侧判据；
「按跳转前驱把副本重新挂回 except 退出口」的 redesign **只作推断、未落地**，原样移交。

**线 B —— 汇合块的源级嵌套归属（R29-A 的残余）：完整门禁但不占本轮槽位。**
R30-B3（`region_analyzer.py:17890` 上方 +14 行：两臂同时认领、且各有臂内前驱、且非二向条件块
的汇合块，从两臂同时取消认领，附加「两臂摘后仍非空」自保护）实测：98 文件窗 sha 级
`SAME=97 REGRESSION=0 MOVED=1`（唯一 MOVED 即靶子），严格尺 `load_daily :: <module>`
`target_diff → CLEAN`、文件 clean `22/25 → 23/25`；但全 402 官方尺
`SAME=402 IMPROVED=0 REGRESSION=0 MOVED=0` —— **完全中性**，且 G0 与 Round 29 同样不可得
（缺陷在分析器对原始字节码布局的读取，源级合成落不进那个状态）。判据、spec、门禁日志齐备，
移交后续轮次（任务 #61）。

**线 C —— `default_event_source :: events −19`：本轮采纳。**
锚点函数官方尺 `['events', 510, 491, 2, 157]`、严格尺 `512/493` 四个非相等块。根因：内层
loop 区域的 break 角色核验把一个**以「向后跳到外层 for 头部」结尾**的块认作自己的 break 出口并
并入区域块集，`region_ast_generator.py:4216` 的批量入账随即令它无人发射。该块在靶子里被**三处**
认领（`[Q] L4216 / L6469 / L20469`），所以发射侧收窄任一处都无效（实测 `candc` 臂
`SAME=2 IMPROVED=0`）—— 修必须落在分析器侧那一次认领上，这是本轮的决定性负结果。

## 二、判据 R30-C1（原则 2 唯一归属 · break 角色侧）

```python
_r30c1_last = (break_block.get_last_instruction() if break_block.instructions else None)
if (_r30c1_last is not None
        and _r30c1_last.opname in BACKWARD_JUMP_OPS
        and _r30c1_last.argval != header.start_offset):
    continue
```

候选 break 块必须**离开**本区域；若它的终止指令属于向后跳转类而落点不是本区域的头部，那条边
属于某个**外层** loop，本区域不得核验它、不得并入 `region_blocks`。同层性：三个合取项只读块
自身（终止指令的 opname 类 ＋ 落点与头部块 start_offset 的同一性关系），不读偏移常量／名字／
常量／条数／函数名／源码形状。只删不增：命中时只取消一次成员资格，不新增任何发射、语句或块；
不命中时逐字节不变。

既有判据为何都不覆盖它：`_r102` 块上方 9 行处已有**后继侧镜像**
`if _rl and _rl.opname in BACKWARD_JUMP_OPS and _rs.start_offset == _rl.argval: continue`
（「终止指令跳向自己」的后继是本 loop 回边，不是出口）——它作用在 worklist 的后继枚举上，
看不到 break 候选列表；本轮把同一个 helper、同一个 `BACKWARD_JUMP_OPS` 常量、同一个关系形状
搬到 break 角色侧，是该 idiom 的对称缺失，故补丁不引入新词汇。

## 三、门禁（严格串行；原始日志见 `logs/`）

| # | 门禁 | 结果 |
|---|---|---|
| G0 | 非空判据（语料无关合成复现） | `test_repros/round30_enclosing_loop_backedge_break/r30c_w2.pyc`：head `3/6`，三个缺陷函数 `w_a_true_break_epilogue 27/21`、`w_b_true_break_yield_epilogue 23/19`、`w_e_deep 30/26`（`logs/g0_head.jsonl`）；CONTROL 电池 `r30c_witness.pyc` head `6/6`（`logs/g1b_head.jsonl`）。形状：外层 for 的循环体在嵌套 loop **之后**还有语句，承载尾语句的块以「向后跳 for 头部」结尾同时又正是内层的 break 出口 |
| G1 | FIX 翻转 ＋ CONTROL 不变 | cand `r30c_w2.pyc 6/6 mism=[]`（产物 sha `d17b0ae28839af5e → 82e204835d56eeed`）；CONTROL 电池产物 **sha 逐字节相同** `ef52a76276145780` ⇒ 判据可证不触及四条邻位：内层自己的回边、真 forward break、for 套 for 的 break、`while True` 破出且区域出口块之后无块（`logs/g1b_c1.jsonl`） |
| G1′ | 语料靶子 | `default_event_source.pyc :: events` `510/491 → 510/508`（找回 17 条；jump=2、true=157 两侧同），文件仍 `13/14 partial`；同簇 `matcher.pyc`、`realtime_event_source.pyc`、`clock_worker` 逐字节不变 |
| G2′ | 前轮 38 个合成复现电池 | `logs/g2prime_38.txt`：`SAME=38 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0` |
| G3 | 96 条承重锚点电池 | `logs/g3_96.txt`：`SAME=96 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`，空读数 0 |
| G4 | 全 402 A/B（发货判据；**sha 优先**） | `logs/g4_ab402_sha.txt`：`SAME=401 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0`，完全匹配文件 `a=370 b=370`；唯一 MOVED = `default_event_source.pyc`，`gained=['events',510,508,2,157] lost=['events',510,491,2,157]`，计数级复核 `logs/g4_ab402.txt` 同形 |
| G4′ | 唯一变化产物严格尺 | `logs/g4prime_{head,c1}.txt`：head `512/493 seq_len −19` → cand `512/510 −2`，`strict clean 13/14` 与 sigma-defect 1 两侧不变 ⇒ **STRICT-BETTER**；一手 hunk 表 `logs/g4prime_hunks_events.txt` |
| G4″ | 判据足迹的**产物间**差分（一手） | c1 相对 head 在 `events` 里只有一段 **17 条插入**（@3210..3314：`date.replace(15,30)` → `dt`、`Event(EventEnum.AFTER_TRADING_END, dt, dt)` 的 yield、循环尾 `POP_TOP`），**零删除、其余零改动**；同一 15 条串（`LOAD_FAST 'day' … STORE_FAST 'dt_before_day_trading'`）在两臂产物中各出现一次且同在 @3116 ⇒ 错排未变，本轮只补回被吞的那 17 条 |
| G5′ | 落地形（带注释）等价性 | `mirr_c1c` 去掉那 5 行注释后与测量臂 `mirr_c1` **逐字节相同**（`provec.py`：唯一 insert opcode、5 行全注释）；三档电池对测量臂 `SAME=38 / SAME=96 / SAME=402 MOVED=0`（`logs/landing_form_gates.txt`、`logs/e_g4_ab402_sha.txt`） |
| G5 | `single` 靶子与承重锚点 | 靶子 `partial 13`（缺口从 19 条指令降到 2 条，未翻转）；金丝雀全部保持：`load_daily.pyc ok 23`、`fly/data/quotation.pyc ok 143`、`plugin_system_persist/__init__.pyc ok 15`、`custom_tools.pyc ok 6`（`logs/` 内 `g5_single`） |
| G6 | `batch --index pyc_index.json --all --round 30` 全量复验 | `logs/batch_all30.txt`：`[402/402]` 跑完、`[BATCH] index written back` 恰 1 次、Traceback／KeyboardInterrupt／MemoryError 0 行、结尾统计块完整；索引改动逐字段核对 `logs/index_delta30.txt`：**只有 `last_tested_round` 29→30（402 条）**，`decompile_status`／`bytecode_match_rate`／`matched_functions`／`function_count` 等其余字段改动 **0 条**，键集合无增删、条目数 402、Σ`function_count` 5746 不变 |
| G7 | `stats --index pyc_index.json` | `logs/stats30.txt`：`total_pyc 402 / verified_pyc 402 / ok_pyc 370 / partial_pyc 32 / failed_pyc 0 / total_functions 5746 / matched_functions 5642 / cumulative_match_rate 98.19%` |

## 四、唯一产物变化的逐项交代

G4 的 `MOVED=1` 意味着整个语料只有一份产物字节变了：
`site-packages/IQEngine/plugins/plugin_system_event_source/default_event_sourceOK.py`，
`events` 方法在 `while True:` 体之后补回外层 for 循环体的尾部语句序列
（`date = day.to_pydatetime().replace(...)` 的分钟参数、`dt` 赋值、
`yield Event(EventEnum.AFTER_TRADING_END, dt, dt)` 与收尾 `POP_TOP`）。
`git status --porcelain` 实测整仓被本轮改动的受跟踪文件为
`core/cfg/region_analyzer.py`、`pyc_index.json`、该 1 份 `*OK.py`，共 3 个。
G6 后该产物的 sha 与测量臂产物 `sha256` **相同**（`e80b5b38f0146f2b`）⇒ 发货核复现了测量结果。

## 五、本轮的方法论收获：官方尺「MOVED 而 matched 不变」可以是 17 条指令的净恢复

G4 的官方尺把靶子读成 `13/14 → 13/14`（该函数两侧都不匹配），分类为 MOVED 而非 IMPROVED；
若只看完全匹配文件数（370→370）会误判为「本轮无收益」。Round 28 已确立「凡 MOVED 必回严格尺
逐函数核」，本轮把它推到下一层：**MOVED 的方向要靠严格尺的 σ/缺口来定，而不是靠 matched 计数**。
一手读数 −19 → −2、产物间差分只有 17 条插入，才说明这条判据是在**补回被吞的指令**而非重排。
另一条同向的方法论：**同一个块被三处认领时，只有取消「分析器侧那一次认领」才有效**；
发射侧收窄任何一处都会被其余两处抵消（`candc` 臂的实测死路）。

## 六、残余与移交

* **靶子剩余 −2**：`orig@3208..3212` 的 `JUMP_FORWARD <exit> / JUMP_BACKWARD <inner header>`
  两连。这不是本轮判据的形状；若原始那条死回边无法从任何忠实源码重新生成，`events` 有 −2 下限
  —— 需自己的轮次判定，不要在门禁轮里补跳转发射。
* **R30-C2（未落地，证据齐备）**：父 loop 在子 loop 入口处按原则 4 移交子区域时，
  fall-through 序中排在子区域之前的裸体块必须**先就地渲染**。实测单独用计数中性（491→491），
  与 C1 同用可把严格尺压到只剩 1 个非相等块、官方尺 `true_diffs 157→31`（代价：多 22 行源码、
  `jump_diffs 2→4`）。靶子同上；spec `D:/Temp/r30diagC/spec_c2.json`，臂 `mirr_n2`/`mirr_c12`。
* **R30-B3（线 B，未落地，门禁齐备）**：`load_daily :: <module>` 严格尺 `target_diff` 的归属
  修复；spec `D:/Temp/r30diagB/spec30b3.json`。官方尺中性、G0 不可得，故需要与一个能翻转计数
  的判据同轮或被单独授权。
* **异常尾声族（线 A）**：两个靶子已拆成两族，各需自己的发射侧判据；三份抑制型候选的否证数据在
  `D:/Temp/r28diagA/`，本轮的 `D:/Temp/r30diagA/`。靶子仍 `function.pyc 14/15`、`flytools.pyc 64/65`。
* 未动残余：`matcher.DefaultMatcher.match`（−24/−26，属 if 臂归属层）、`clock_worker +16`、
  `replace_utils.decrypt_database_url +29`、`instance._init_config −1`、
  `plugin_fly_data/strategy.pyc` 两条、`quote.pyc` f-string 族与 `load_bars_from_hundsun 477/470`、
  语料外见证 `r29x_01_module_if_deficit_witness.pyc <module> 142/138`
  （本轮实测其损伤是 `for row in (payload or [1,2])` 的 or 链被从 for 迭代头吸走，**不是**
  汇合块形状，任何 R30-B 判据都翻不动它）。
* 电池基线：`anchors96.txt` ＋ 38 个前轮复现继续承重；承重锚点新增
  `test_repros/round30_enclosing_loop_backedge_break/r30c_w2.pyc`（head 必须 3/6，判据后 6/6）
  与 `r30c_witness.pyc`（两核必须 6/6 且产物 sha `ef52a76276145780`），
  `default_event_source.pyc` 由本轮起必须 `13/14` 且 `events` 缺口 ≤2；
  金丝雀 `load_daily.pyc` 23、`quotation.pyc` 143、`plugin_system_persist/__init__.pyc` 15、
  `custom_tools.pyc` 6 不变。
* 新增合成复现 `test_repros/round30_enclosing_loop_backedge_break/`（`.py` 入库，`.pyc` 由
  `python -X utf8 -c "import py_compile;py_compile.compile(f, cfile=f[:-3]+'.pyc', doraise=True)"`
  重生成，`*.pyc` 已 gitignore）。注意：`py_compile` 默认只写 `__pycache__`，
  电池读的是**同名同级** `.pyc`，必须显式给 `cfile`。
