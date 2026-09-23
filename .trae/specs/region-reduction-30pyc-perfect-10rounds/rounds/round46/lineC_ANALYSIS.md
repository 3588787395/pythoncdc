# Round 46 · 诊断线 C（DIAGNOSE-ONLY）：等长／换位（MOVE）族的根因与同层判据

私有目录：`D:/Temp/r46diagC`（未触碰 `core/`，未执行任何 git 写操作）
共享目录：只新增三个臂目录 `D:/Temp/r43gate/mirr_r46c1`、`mirr_r46c2`、`mirr_r46c3`；
其余产物（含全部度量输出 jsonl/out/log）全在本目录，未写任何 `r43g.py run` 的共享 `ROOT/build_*`。
被测字节：HEAD `cc71dd2d`（Round 45 落地核）。所有「改前」读数对该字节成立。
判定尺：仓库根 `_r10_strict_check.py`（严格尺）；官方尺 `scripts/pyc_batch_verify.py single` 只作对照。

---

## 0. 名册核对（先把靶子钉在现行字节上）

| 名册成员 | 任务书的说法 | 现行实测（landed 字节） |
|---|---|---|
| (a) `fly/logger.pyc :: Backtest.write_logging_thread` | 官方 113/113 j=1；「strict 127 vs 128」 | 官方 `113/113 jump_diffs=1 true_diffs=40`；严格尺 `seq_diff #71 orig=('msgs',LOAD_FAST) decomp=('&lt;JUMP&gt;','JUMP')`。127/128 是**未过滤噪声**的裸条数（`RESUME/CACHE/PRECALL/EXTENDED_ARG/NOP` 计入库时），严格尺过滤后两侧都是 113 条 ⇒ 真判据是 **seq_diff（等长换位）**，不是 seq_len。 |
| (b) 「同文件 `:: _process_task_queue`」 | 378/378 同族 | **文件归属错**：`fly/logger.pyc` 里没有 `_process_task_queue`（`_load_map` 的 64 个 code object 名全部不含该串）。该函数在 `IQCommon/graph.pyc :: ModelGraph._process_task_queue`：官方 `378/378 j=1 t=118`，严格尺 `seq_diff #119 orig=('None',LOAD_CONST) decomp=('&lt;JUMP&gt;','JUMP')`。同族的另一支，但不是同一文件。 |
| (c) `finally` 换位五支 | `_all_bars_of_cache 230/231`、`check_stock 88/89`、`get_history_new 322/323`、`get_multiminute_his_data 481/482` | 四支在册未变，另加同批的 `kline_datetime_list 390/391`、`Quote.check_frequency 123/124`。见 §5 的分裂：其中两支（`get_history_new`/`get_multiminute_his_data`）**不是** (a)(b) 的形状。 |

`fly/logger.pyc` 严格尺全量：`3/64` 缺陷 = `Backtest.logging_process`(seq_len 103/95)、
`Backtest.write_logging_thread`(seq_diff)、`SafeFileHandler.check_baseFilename`(target_diff)。

---

## 1. 形状实证：(a) `write_logging_thread` 的整块外置 + 原位留跳转

### 1.1 原始指令窗口（`dis` 原样，`site-packages/fly/logger.pyc`）

```
   354 STORE_FAST                    msgs                       <- 内层 while 区域 B48 的最后一块
   356 LOAD_FAST                     q
   358 LOAD_CONST                    0
   360 COMPARE_OP                    >
   366 POP_JUMP_BACKWARD_IF_TRUE     to 64                       <- 内层 while 回边（区域 B48 出口）
   368 LOAD_FAST                     msgs                       ┐
   370 POP_JUMP_FORWARD_IF_FALSE     to 424                     │ 被外置的语句块 `if msgs: info(msgs)`
   372 LOAD_FAST                     self                       │ （块 B368 + 臂体块 B372）
   374 LOAD_ATTR                     logger_bt                  │
   384 LOAD_METHOD                   info                       │
   406 LOAD_FAST                     msgs                       │
   412 CALL                                                     │
   422 POP_TOP                                                  ┘
   424 JUMP_FORWARD                  to 666                      <- then 臂的收尾跳（块 B424）
   426 LOAD_FAST                     self                        <- else 臂区域 B426 的入口
   428 LOAD_ATTR                     status
   ...
   660 JUMP_FORWARD                  to 666
   662 LOAD_CONST                    None / 664 RETURN_VALUE     <- else 臂的 break
   668 JUMP_BACKWARD                 to 4                         <- 外层 while True 回边（块 B666）
```

### 1.2 landed 产品（同一 code object，`site-packages/fly/loggerOK.py` 重编译）

```
   366 POP_JUMP_BACKWARD_IF_TRUE     to 64
   368 JUMP_FORWARD                  to 612     <-- ★ 原位只留一条跳
   370 LOAD_FAST self / 372 LOAD_ATTR status / 382 POP_JUMP_IF_FALSE to 608
       ...（else 臂 `if self.status: … else: break` 整段前移到 370）...
   606 JUMP_BACKWARD to 2 / 608 LOAD_CONST None / 610 RETURN_VALUE
   612 LOAD_FAST msgs                          <-- ★ 被外置的块整体落在函数体末尾
   614 POP_JUMP_FORWARD_IF_FALSE to 668
   616 LOAD_FAST self / … / 666 POP_TOP
   670 JUMP_BACKWARD to 4
```

发射块序（产品）：`B4 → [B48 内层 while] → [B426 else 臂全段] → [B368 `if msgs`] → B666 回边`
原始块序：`B4 → [B48 内层 while] → [B368 `if msgs`] → B424 → [B426 else 臂] → B666 回边`
⇒ **等长（113/113）整体换位**；语义仍等价（else 臂两支各自 continue/break，永不落到末尾块），
所以官方尺按操作码比对判它 `j=1 matched`，严格尺抓住 `#71 seq_diff`。这正是 假-ok 陷阱。

### 1.3 让生成器选了这个顺序的区域树（所有权倾倒）

`probe45e.py` + `callsitesC.py`（只读 monkeypatch，逐字抄自 r43gate 工具）：

```
LoopRegion WHILE_LOOP entry=B4  blocks=[B4,B48,B64,B228,B232,B288,B342,B356,B368,B372,
                                        B424,B426,B440,B522,B564,B620,B660,B662,B666]
  ├ LoopRegion entry=B48  blocks=[B48,B64,B228,B232,B288,B342,B356]
  ├ IfRegion   entry=B368 IF_THEN  cond=B368 merge=B424 exit=B424 then=[B372] blocks=[B368,B372]
  ├ IfRegion   entry=B426 IF_THEN_ELSE  merge=None then=[B440,B522,B564,B666,B620,B660]
  │                                   else=[B662] blocks=[…,B666]
  ├ IfRegion   entry=B440 …  /  └ IfRegion entry=B564 …
```

关键块（结构事实，全部来自所有权倾倒）：

```
B4    term=POP_JUMP_FORWARD_IF_FALSE 426  succ=[B48,B426]  preds=[B0,B666]
B48   term=POP_JUMP_FORWARD_IF_FALSE 368  succ=[B368,B64]  preds=[B4]
B356  term=POP_JUMP_BACKWARD_IF_TRUE 64   succ=[B368,B64]  preds=[B342,B288]
B368  term=POP_JUMP_FORWARD_IF_FALSE 424  succ=[B372,B424] preds=[B356,B48]   owner=IfRegion(B368)
```

⇒ **B48 区域（then 臂入口区域）的唯一臂外后继是 B368，而 B368 的全部前驱 {B48, B356}
都在 B48 区域内** ⇒ B368 只能由 then 臂到达，它是**臂的延续**，不是循环体的下一句。

发射现场的调用序（`callsitesC.py`，同一 code object 内 `_generate_region` 的到达顺序）：

```
GEN LoopRegion B4    via generate:1682
GEN LoopRegion B48   via _loop_handle_no_exit_successors:10072   <-- then 臂只生成「入口那一个区域」
GEN IfRegion   B426  via _loop_handle_no_exit_successors:10100   <-- else 臂生成，块被认领
GEN IfRegion   B368  via _loop_handle_child_region_entry:10781   <-- ★ 落单，被循环体顺扫捡到尾款
```

**机制定论**：`region_ast_generator.py:9955 _loop_handle_no_exit_successors`（循环头条件 jump 的两个
后继都不逃逸循环时，就地合成 `If(cond, then, orelse)`）对**每一条臂只生成「该臂入口的那一个区域」**
（:10072 / :10100 两处 `self._generate_region(_*_entry_region)` 后立刻 `for _b in …: generated_blocks.add(_b)`
收臂）。then 臂的延续区域因此不被认领，留给 `_loop_generate_body` 的顺扫，在 else 臂**之后**发射；
codegen 要在 then 臂末尾接上它，只能在原位留 `JUMP_FORWARD`。
实测该函数**不存在** entry=B4 的 IfRegion（倾倒里 B4 只被 LoopRegion 认领；名义上 `if q:` 的 merge 块
B666 被 IfRegion(B426) 写进了自己的 blocks/then 集）⇒ 头部的 `if q:/else` 只能由上述发射期合成路径
表达，本轮靶就在那条路径的取臂决定上；区域树本身是**正确**的（B368 区域确实是循环的直接子区域）。

---

## 2. 同层判据候选 R46-C1（一条：then 臂沿 fall-through 封闭）

文件：`core/cfg/region_ast_generator.py`
锚点（LF 归一后**全文件唯一**，`build2.py` 断言 `anchor occurrences==1`）＝ :10070..:10075 六行：

```
                        if _then_region_id not in self._generated_regions and _then_region_id not in self._generating_regions:
                            _then_ast = self._generate_region(_then_entry_region)
                            _then_stmts = _then_ast if isinstance(_then_ast, list) else [_then_ast] if _then_ast else []
                            for _b in _then_entry_region.blocks:
                                self.generated_blocks.add(_b)
                            self._generated_regions.add(_then_region_id)
```

repl ＝ 锚点原样保留（旧命中路径逐字节不变）+ 在其后追加封闭循环 **50 行**
（其中注释头 19 行，下面是 31 行代码；`spec_r46c1.json` 记 `repl` 共 56 行 ＝ 锚 6 ＋ 新 50，
`build2.py` 断言插入行数与 CRLF/BOM 保真）：

```python
                            _r46c_frontier = set(_then_entry_region.blocks)
                            while True:
                                _r46c_priv = []
                                for _r46c_b in sorted(_r46c_frontier, key=lambda x: x.start_offset):
                                    for _r46c_s in (getattr(_r46c_b, 'successors', None) or []):
                                        if _r46c_s in _r46c_frontier or _r46c_s in _r46c_priv:
                                            continue
                                        _r46c_preds = getattr(_r46c_s, 'predecessors', None) or []
                                        if not _r46c_preds:
                                            continue
                                        if all(_r46c_p in _r46c_frontier for _r46c_p in _r46c_preds):
                                            _r46c_priv.append(_r46c_s)
                                if len(_r46c_priv) != 1:
                                    break
                                _r46c_s = _r46c_priv[0]
                                _r46c_reg = self.region_analyzer.get_entry_region_for_block(_r46c_s)
                                if (_r46c_reg is None or _r46c_reg.entry is not _r46c_s
                                        or _r46c_s in self.generated_blocks
                                        or id(_r46c_reg) in self._generated_regions
                                        or id(_r46c_reg) in self._generating_regions):
                                    break
                                _r46c_ast = self._generate_region(_r46c_reg)
                                _r46c_st = (_r46c_ast if isinstance(_r46c_ast, list)
                                            else [_r46c_ast] if _r46c_ast else [])
                                if not _r46c_st:
                                    break
                                _then_stmts.extend(_r46c_st)
                                for _b in _r46c_reg.blocks:
                                    self.generated_blocks.add(_b)
                                self._generated_regions.add(id(_r46c_reg))
                                _r46c_frontier |= set(_r46c_reg.blocks)
```

### 为什么它只读结构事实（原则 1..4 自检）

> 上面引的是 31 行代码；实际落盘的 `repl` 在它前面还有 19 行注释头（把形状与四条判据写进代码）。
> 唯一权威文本＝`D:/Temp/r46diagC/spec_r46c1.json` 的 `repl` 字段，`mirr_r46c1` 由它生成。

* ① **私有性**：候选延续块 S 的**每一条前驱**都已在「本臂已封闭块集」内 —— 读的是 `predecessors`
  集合成员关系（块身份），不读偏移、不读条数。语义：臂外没有任何块能落到 S，S 不可能是「循环体的
  下一句」，只能是本臂的延续。
* ② **唯一性**：满足①的 S 在全集内**恰有一个**。多个 ⇒ 区域出口是分叉而非延续 ⇒ 停。
  读的是集合基数，不是指令条数。
* ③ **入口引用**（原则 4）：S 必须是某区域的 entry（`get_entry_region_for_block(S).entry is S`），
  且该区域此刻未被生成、未注册 —— 与站点自身 :10070 的守卫同一形式，不新增语义种类。
* ④ 该区域确实产出语句（空 ⇒ 原样回退，认领状态一字不动）。
* 迭代只读块身份 / 归属 / pred-succ / 区域入口；块集单调增长 ⇒ 必终止；
  **不读** 名字、常量、绝对偏移、指令条数、region_type、也不读任何历史计数。
* 不命中时（①②③④ 任一不满足）走的是 `break`，`_then_stmts` 与锚点前的字节完全一致
  ⇒ 候选对不命中的站点是**恒等变换**（已由 §4 的逐字节对照证明）。

依据原则 1（自底向上归约：一条完整控制结构＝一个归约单位）：一条臂的归约单位不是「一个区域」，
而是「从入口区域沿 fall-through 封闭的整条路径」；把封闭单位切成一个区域，剩下的延续就被推迟归约，
表现为等长换位。

---

## 3. 镜像臂度量

臂：`D:/Temp/r43gate/mirr_r46c1`（由 `build2.py` 从 landed 字节重建，断言 BOM/CRLF/插入行数）。
度量器：本目录 `runC.py`（`strict` / `bat` / `prod`）、`lensC.py`（逐 code object 发射长度）、
`cmpC.py`（官方 A/B + 逐函数长度 A/B）。两侧在 `sys.modules` 里先清 `core*`（抄 `r45e/run45e2.py`）。

### 3.1 成员必须严格干净

```
landed   fly/logger.pyc    strict_defective=3/64   （write_logging_thread seq_diff #71）
r46c1    fly/logger.pyc    strict_defective=2/64   （write_logging_thread 消失 ⇒ 严格干净）
```
产品差分只有 4 行：`if msgs: self.logger_bt.info(msgs)` 从函数尾（16867→16875 字节）搬回
then 臂内层 while 之后，与 §1.1 的原始窗口逐条同序。

### 3.2 逐函数长度对照（「REGRESSION=0 不等于惰性」的教训）

被改动的文件只有 `fly/logger.pyc`。对它做**全部 64 个 code object** 的发射长度对照
（`lensC.py`，严格尺过滤后的条数，两臂各一次全量发射）：

```
fly/logger.pyc cos=64
  emitted-length deltas: []                      <-- 没有任何函数从 48 条悄悄变成 44 条
  verdict changes: [('<module>.Backtest.write_logging_thread', 'seq_diff' -> 'CLEAN')]
  landed defective: logging_process, write_logging_thread, check_baseFilename   (3)
  arm    defective: logging_process, check_baseFilename                          (2)
```

其余 26 支文件的产品 sha 逐位相同 ⇒ 其全部 961 个 code object 的发射长度自动相等。

### 3.3 ≥20 支部分失败文件的官方 A/B（27 支 = 现行全部 partial 文件）

`runC.py bat`，两侧各自清 `core*` 后从镜像根发射（`r46c_bat_landed.jsonl` / `r46c_bat_r46c1.jsonl`）：

```
TALLY files=27 SAME(sha)=26 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0
sum matched: landed=875  r46c1=875   sum total=961   full-match files: 0 -> 0
唯一 MOVED = fly/logger.pyc：
  write_logging_thread [113,113,j=1,t=40] -> [113,113,j=3,t=1]
  （官方两侧都不算 matched：真差异 40 条塌成 1 条，代价是 3 个跳转槽位编号变化；
    严格尺判它 CLEAN —— 官方 j 计数在这里没有裁决权。）
```

### 3.4 24 支「官方全 ok」文件的惰性证明（尺寸分层抽样，149 B … 209 KB，含语料最大 ok 文件
`fly/data/quotation.pyc`，合计 405 KB / 379 个函数）

```
ok-sample files=24 byte-identical=24 sha-diff=0 official-regression=0 err=0
all fully matched both arms: True
```
这 24 支在严格尺下的现行成色（landed，也是 arm，因产品逐字节相同）：
`全部一致 21/24 文件，函数级 440/444`；3 支 假-ok = `quotation.pyc 148/150`、
`dockerspawner.pyc 24/25`、`fly/common/common.pyc 5/6` —— 均非本族形状，本候选不碰它们。

### 3.5 站点普查（曝光面）

`censusG.py` 在 landed 核上钩住 `_loop_handle_no_exit_successors`，对 27 partial + 24 ok 共 51 支
（379+961＝1340 个 code object）逐站记录五段判据停在哪一段（`r46c_census51b.out`，全量）：

```
SITE trade_logs_control  __init__    hdr=B12  then=B232  then_region=NONE            <- ③ 第一段停
site reconnect           function    hdr=B70  then=B192(IfRegion) ext=['B520','B70'] none private
                                                                              <- ① 私有性停
FIRE write_logging_thread logger     hdr=B4   then=B48(LoopRegion) absorb IfRegion:B368
STATS {'site':3,'then_region':2,'fire':1,'stop_priv':1,'stop_multi':0,'stop_noregion':0,
       'stop_done':0,'no_succ':0}
```

⇒ 语料里该站点本身很稀（51 支仅 3 次到达），判据在全语料样本上**只放开 1 个站点**，
与 §3.3/§3.4 的 sha 证据完全一致（27 partial 中 MOVED=1，24 ok 中 0）。
①（私有性）与 ③（区域入口）各被语料 witness 独立扣住一次 ⇒ 两条合取项都不是摆设；
②（唯一性）在 51 支里 n_priv>1 的站点数 = 0，在合成见证 w3（两段串联延续）里由封闭循环
多步走通（w3 转严格干净），未观测到「多私有后继」误放。
全 402 分片普查（`r46c_census_sh{0..3}.out`，见 §3.6）用于把 1340 → 全语料的到达/放开数钉死。

### 3.6 全 402 语料站点普查

`censusG.py` 按 4 分片跑完**全 402 支语料**（`r46c_census_sh{0..3}.out`）：

```
shard1: STATS {'site':3,'then_region':2,'fire':1,'stop_priv':1,…}   <- 三支站点全在 shard1
shard0 / shard2 / shard3: STATS 全 0
合计：到达 _loop_handle_no_exit_successors 的站点 3 个 / 402 支，
      then 臂是区域入口的 2 个，判据放开（FIRE）1 个 = write_logging_thread
```
即候选在**全语料**只打开一个站点，曝光面与 §3.3 的 MOVED=1、§3.4 的 24/24 逐字节相同自洽。

### 3.7 全 402 逐字节爆炸半径（G4 等价）

`full402.py`：臂产品文本 vs **入库产物**（先证明入库产物确为落地核输出：51 支已测文件的
utf-8-sig + CRLF 归一 sha 与 `runC.py bat landed` 记下的内存文本 sha **51/51 相符**）。
逐支比对归一 sha，任何不同都记 `changed`。

| 文件 | 核字节 | CRLF 行数 |
|---|---|---|
| landed `core/cfg/region_ast_generator.py` | 2 997 983 | 48 592 |
| `mirr_r46c1` 同文件 | 3 002 415 (+4 432) | 48 642 (+50) |
| `mirr_r46c2`（放宽臂，删 ① 前驱约束） | 3 002 308 | — |
| `mirr_r46c3`（R33-A 还原臂） | 2 997 995 | — |

两侧 BOM 均在、全 CRLF、LF-only 行数 0；臂相对 landed 的差异是 **+50 行 / −0 行**（纯追加）。

**全 402 支跑完（`r46c_full402.jsonl`，402 行 / 0 ERR / 0 缺 sha，`jobD.log` 末行
`SCAN DONE r46c1 over 402 files`）**：

```
total=402  changed=1  byte-identical=401   (401 支里 |len_changed| 最大值 = 0)
changed = site-packages/fly/logger.pyc   sha_arm b09ecfe6 vs sha_landed 53e97563  Δ=+8 字符
```
⇒ 候选在**整个语料（79 个目录 / 402 支）**上的爆炸半径就是 §1/§2 那一支、一个 4 行的块位移
（+8 字符 = `if msgs:` 两行从函数尾搬到 then 臂内，长度不变、顺序变），与 §3.3 的 MOVED=1、
§3.4 的 24/24、§3.6 的 FIRE=1 三方交叉自洽。
其余 401 支产品逐字节相同 ⇒ 它们的严格尺裁决**按构造**不可能变化（无需再跑 401 次严格尺）。

---

## 4. 合成见证与真反例控制（G0）

源：`D:/Temp/r46diagC/r46c_witness.py`（w1/w2/w3）、`r46c_controls.py`（n1..n6），
用本机 CPython 3.11.7 `py_compile` 出 `.pyc`。

```
landed   r46c_witness.pyc    strict_defective=3/4
    - <module>.w1 seq_diff #25 orig=('msgs',LOAD_FAST) decomp=('<JUMP>','JUMP')
    - <module>.w2 seq_diff #14 orig=('b',LOAD_FAST)    decomp=('<JUMP>','JUMP')
    - <module>.w3 seq_diff #19 orig=('a',LOAD_FAST)    decomp=('<JUMP>','JUMP')
r46c1    r46c_witness.pyc    strict_defective=0/4            <-- 三支全部转严格干净
```
三支都是 §1 的形状的纯结构复刻（w1 内层 while + 延续 if；w2 内层 if + 延续 if；w3 两段延续区域串联
⇒ 检验封闭循环走多步）。

真反例控制（6 支，必须两臂**逐字节相同**）：

```
landed   r46c_controls.pyc   strict_defective=4/7   n2 target_diff / n3 seq_len 46|45
                                                            / n4 seq_len 28|27 / n6 seq_len 26|19
r46c1    r46c_controls.pyc   strict_defective=4/7   （同名同 kind 同 msg，一字不差）
控制产物 sha256[:16]：landed=930c4d21a1a66c80  r46c1=930c4d21a1a66c80  ⇒ BYTE-IDENTICAL
（n1、n5 两臂都严格干净，也在同一份逐字节相同的产品里）
```

控制不是「够不到站点的空靶」——`probeG.py` 在 landed 核上把站点实况打了出来：

```
SITE n1 hdr=B4 term=POP_JUMP_FORWARD_IF_FALSE then=B48 then_region=NONE
SITE n2 hdr=B4 term=POP_JUMP_FORWARD_IF_FALSE then=B48
     then_region=LoopRegion:B48 | ext_succ=['B82'] private=['B82'] n_priv=1 | would_absorb=NO-REGION
SITE write_logging_thread hdr=B4 … then_region=LoopRegion:B48
     | ext_succ=['B368'] private=['B368'] n_priv=1 | would_absorb=IfRegion:B368
```

即：n1 到站但 then 臂不是区域（③ 的第一段拦住，「无区域可吸收」）；n2 到站、有唯一私有后继 B82，
但 B82 不是任何区域的 entry（③ 的第二段拦住）；只有 (a) 走到「吸收」。
另把 ① 私有性整段拆掉造的**放宽臂** `mirr_r46c2` 在同一控制片上仍然逐字节相同
⇒ n1/n2 由 ③ 而非 ① 保住，控制的「保住理由」被逐条指认，不是巧合。
（① 与 ② 的独立保住证据见 §3.4 语料侧站点普查。）

---

## 5. 名册其余成员：两支不是这个形状（否证）

对每支取严格尺第一处发散的 8 条窗口，看「原始窗口是否在产品里整体重现」：

| 成员 | 严格尺 | 发散处 orig | 发散处 decomp | 原窗重现位置 | 判定 |
|---|---|---|---|---|---|
| `fly/logger :: write_logging_thread` | seq_diff 113/113 | `LOAD_FAST msgs; POP_JUMP_IF_FALSE 424; …` | `JUMP_FORWARD 612; LOAD_FAST self…` | @+33 逐字 | §1/§2 形状 |
| `IQCommon/graph :: _process_task_queue` | seq_diff 378/378 | `LOAD_CONST None; RETURN_VALUE; PUSH_EXC_INFO…` | `JUMP_FORWARD 842; PUSH_EXC_INFO…` | @+88 逐字 | 同族，**但站点不同**：产品与 landed 在 r46c1 下**逐字节相同**（见 §3.3），它的换位不经 `_loop_handle_no_exit_successors` |
| `klinedata :: _all_bars_of_cache` | seq_len 230/231 | `LOAD_GLOBAL history_cache; …` | `JUMP_FORWARD 498;` + 同一窗口 | @+1 | 同族（外置+原位留跳），r46c1 下产品逐字节不变 |
| `Quote.check_stock` | seq_len 88/89 | `LOAD_CONST 11; len(s)…` | `JUMP_FORWARD 346;` + 同一窗口 | @+1 | 同族，r46c1 逐字节不变 |
| `Quote.check_frequency` | seq_len 123/124 | `LOAD_CONST None; RETURN_VALUE; PUSH_EXC_INFO…` | `JUMP_FORWARD 558; PUSH_EXC_INFO…` | 否 | **另一种形状**（except 副本与 return 交织），r46c1 不变 |
| `get_history_new` | seq_len 322/323 | `JUMP_FORWARD 1678; LOAD_FAST frequency…` | `LOAD_FAST kline_data_dict; RETURN_VALUE; …` | 否 | **反向**：产品把 `return X` 内联进原应放跳的槽位（finally 复制/内联族），与「整块外置+原位留跳」方向相反 |
| `get_multiminute_his_data` | seq_len 481/482 | `JUMP_FORWARD 2758; LOAD_GLOBAL NULL+get_kline_by_count_new…` | `LOAD_FAST his_data_dict; RETURN_VALUE; …` | 否 | 同上 |
| `kline_datetime_list` | seq_len 390/391 | `POP_JUMP_FORWARD_IF_TRUE 666; …time_count -= 1…` | `POP_JUMP_FORWARD_IF_FALSE 1704; …` | @+42 | 另一形状（条件极性＋块移），r46c1 不变 |

⇒ **族内至少三种形状**：
 (I) 循环头合成 if/else 时 then 臂不沿 fall-through 封闭 —— 本判据治，语料见证 (a)（**1 支**）；
 (II) 同一「整块外置＋原位 `JUMP_FORWARD`」表观但站点在别处（`_process_task_queue` /
 `_all_bars_of_cache` / `check_stock` 三支在 r46c1 下产品逐字节不变）；
 (III) `finally` 的 `return X` 被内联到跳转槽（`get_history_new` / `get_multiminute_his_data`
 / `check_frequency`），方向与 MOVE 族相反，属 R33-A 之后的另一层。

---

## 6. 否证清单（falsified leads）

1. **名册 (b) 的文件归属被否证**：`fly/logger.pyc` 内 `_load_map` 的 64 个 code object 无一叫
   `_process_task_queue`；它在 `IQCommon/graph.pyc`（官方 378/378 j=1，严格 seq_diff #119）。
2. **「strict 127 vs 128」被否证**：严格尺两侧均 113 条（seq_diff），127/128 是含 CACHE/PRECALL/
   EXTENDED_ARG 的裸条数，Round 44 手记的这组数不能当判据用。
3. **「一个判据收掉整个等长换位族」被否证**：r46c1 在 `graph.pyc` / `klinedata.pyc` /
   `quote.pyc` 三份产品上与 landed **逐字节相同**（16702/97197/87698 字符，sha 同）；它只动
   `logger.pyc` 一支。名册 (c) 的 5 支全部不被本判据触及。
4. **R33-A 不重复也不覆盖本族**：R33-A 在 `region_ast_generator.py:25496`
   `_find_return_chain_via_successors._is_cleanup_only_no_return`（try/finally 的 return 链穿透），
   读的是**栈效应/操作码类别**（净栈 0 + 尾 POP_TOP + 块内无跳转）；本候选读的是**块归属与 pred/succ
   封闭性**，不同层不同判据。`IQCommon/utils.pyc :: load_yaml` 在 landed 已严格干净（见 §3.5），
   R33-A 的判据也**不能**解释 (a)：(a) 被外置的块以 `LOAD_FAST msgs; POP_JUMP_IF_FALSE` 起头并含
   分支跳转，直接被 R33-A 的「块内无任何跳转」否决。
5. **控制片靠 ① 私有性保住的假设被否证**：`n2` 的 B82 实测**通过**私有性检验（`private=['B82']`），
   真正保住它的是「S 必须是区域 entry」；放宽臂 `mirr_r46c2`（删掉 ① 的全部前驱约束）在控制片上
   仍逐字节相同。
6. **「(c) 的 `finally` 换位是 R33-A 形状的残余」被否证（用镜像臂 r46c3 现场判定）**：
   `mirr_r46c3` 把 `_is_cleanup_only_no_return` 还原成 R33-A 之前的
   `return all(i.opname in _cleanup_only_ops …)` 一行。
   * 反证有效性：该臂下 `IQCommon/utils.pyc :: load_yaml` 立刻退回缺陷
     （`seq_len orig=55 decomp=57`，landed 是 `26/26 全严格干净`）⇒ R33-A 的结构臂确实在管这条路。
   * 判定：`IQCommon/api/klinedata.pyc` 与 `fly/data/quote.pyc` 的产品在 landed 与 r46c3 下
     **逐字节相同**（sha 7a34666cb4bd / 同），`get_history_new`、`get_multiminute_his_data`、
     `kline_datetime_list`、`_all_bars_of_cache`、`Quote.check_stock`、`Quote.check_frequency`
     的缺陷 kind/msg 一字不差 ⇒ 这几支**不经过** R33-A 的站点，是另一种形状，
     既不是 R33-A 的过度命中，也不能靠 R33-A 的判据族解释。
7. **「(b)(c) 与 (a) 同一发射站点」被否证**：`callsitesC.py` 逐函数统计
   `_loop_handle_no_exit_successors` 在发射序里出现的次数 ——
   `write_logging_thread`=2（:10072 取 then、:10100 取 else），
   `_process_task_queue`=0、`_all_bars_of_cache`=0、`Quote.check_stock`=0、`Quote.check_frequency`=0；
   后三者的臂取自 `_process_if_blocks:{20581,20618,21107}` /
   `_if_generate_else_branch:14924` / `_generate_try:{24858,25208}` / `generate:1682`。
   r46c1 下它们的产品逐字节不变。
   `_all_bars_of_cache` 的落单块是 B412/B450（倾倒里它们既是 IfRegion(B326)/B250 的 then 成员，
   又作为顶层 BASIC 区域在 `generate:1682` 的最后两个调用里被发射）⇒ 子形状 (II) 的因在
   **归属层的双认领**，与本轮候选不同层，留下一轮。

---

## 7. 上不上（ship / do-not-ship）

**结论：可上（SHIP），但收益只有 1 支，且验收尺必须是严格尺。**

支持面（全部对 landed 字节 `cc71dd2d` 成立，度量见 §3/§4/§3.7）：

* 靶子严格干净：`fly/logger.pyc` 严格缺陷 `3/64 → 2/64`，`write_logging_thread` 的 `seq_diff`
  消失，产品窗口与 §1.1 原始 dis **逐条同序**，`if msgs:` 块从函数尾回到 then 臂内。
* 爆炸半径 = 该一支：全 402 语料逐字节扫描 `changed=1 / identical=401 / ERR=0`；
  27 支 partial 官方 `REGRESSION=0`（`SAME(sha)=26`）；24 支「官方全 ok」抽样 24/24 逐字节相同；
  逐 code object 发射长度 **零变化**（不存在「48 条悄悄变 44 条」）。
* 判据不越界：合成见证 `3/4 → 0/4` 缺陷，6 个真反例控制**逐字节相同**，且每个控制「被哪一条
  合取项保住」被逐条指认（§4）；站点普查 FIRE=1（§3.6）。

必须随附的两条注意事项：

1. **官方尺会在该支上把 `jump_diffs` 从 1 读到 3**（真差异 40 条塌成 1 条，代价是 3 个跳转槽号），
   官方 matched 总数两侧不变（875/961 → 875/961）。若验收只看官方 j 计数，这一支会被误记为
   「变差」。这正是任务书点出的 假-ok 陷阱的镜像面 ⇒ 以严格尺为准。
2. **本判据不收掉 MOVE 族**：名册 (b)(c) 六支在 r46c1 下产品逐字节不变（§5、§6.3/§6.6/§6.7）。
   形状 (II)（顶层 BASIC 区域双认领，`_all_bars_of_cache` 已定位到 `generate:1682` 的落单发射）
   与形状 (III)（`finally` 的 `return X` 内联进跳转槽位，已用镜像臂 r46c3 现场排除 R33-A 关联）
   是**另两轮**的靶子，留下的线索：形状 (II) 的站点在归属层，形状 (III) 的站点在 return 链层。
