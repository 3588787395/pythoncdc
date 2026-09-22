# Round 31 · 诊断线 A — `site-packages/fly/common/flytools.pyc :: <module>.FileLock.acquire`

纯诊断（DIAGNOSE-ONLY）。本轮 **未修改 `F:\Downloads\pythoncdc-main` 任何文件**（`core/`、`.trae/`、`test_repros/` 全程只读；未运行任何 git 写命令；未执行 `git remote -v` / 读取 `.git/config`）。所有实验都在私有镜像 `D:/Temp/r31diagA/c1/mirr_*` 上完成，所有数字都取自本目录 `logs/` 下由我自己生成的文件（逐条给出处），未实测的量均已标注。

---

## 0. 结论摘要（3 句根因）

1. `except OSError as e` 的 **外层 if**（`IfRegion entry=B200`，then 臂 `[B242]`、else 臂 `[B366,B508,B558]`、`merge=None`）在收集 then 臂时，把 **本臂自身的终止语句块 B364（裸 `raise`）** 留在 `then_stop` 里当作臂间边界——因为 `boundary_stop` 里同时含 B314/B364（`region_analyzer.py` L16581/L16610 → L17135）。
2. B364 因此不属于任何区域块表，只能由 `region_ast_generator.py:24695` 的 handler 顺序尾部在 **整个 if/else 之后** 发射：一个错位同时造出 H1（@364 raise→jump）、H2（@558 `POP_EXCEPT/LOAD_CONST/STORE_FAST e/DELETE_FAST e/JUMP` as-var 清理尾声整块被 raise 顶掉，−4）、H3（@586 循环回边消失，−1）。
3. 只需在 **分析层**（原则 2「每块唯一归属」）取消这一错误认领（只删不增、不新增任何发射），`acquire` 从官方尺子 `88/85 jd=2 td=14` 直接 **翻转为 65/65**，严格尺子同步归零（`orig=90 decomp=90`，非等快块 0）。

Round 30 对本族的「需发射侧补回 as-var 清理尾声 + 回边」判断 **被本轮实测否证**：尾声块 B558/回边块 B584 早在 else 臂里，缺的不是发射，而是臂成员身份。

---

## 1. 靶子与首手 hunks 证据

靶子读数（`logs/f402_head.jsonl`，arm=head，与 landed 逐字节同一 core，由 `r31c.py build` 断言 `head mirror == worktree bytes`）：

```
flytools.pyc  64/65   [['acquire', 88, 85, 2, 14]]
```

严格尺子逐指令 hunks（`logs/hunks_landed_tracked.txt`，脚本 `c1/hunks30.py`，对象 = 落地 core + 仓库跟踪产物 `site-packages/fly/common/flytoolsOK.py`）：

```
<module>.FileLock.acquire  acquire
  filtered orig=90 decomp=85 delta=-5   non-equal blocks=3
  H1 replace  orig[45:46] @364..364  ->  decomp[45:46] @364..364   n=1/1
        o @364 ('0','RAISE_VARARGS')   d @364 ('<JUMP>','JUMP')
  H2 replace  orig[71:76] @558..566  ->  decomp[71:72] @558..558   n=5/1
        o @558 POP_EXCEPT, @560 LOAD_CONST None, @562 STORE_FAST 'e',
          @564 DELETE_FAST 'e', @566 JUMP   ->  d @558 ('0','RAISE_VARARGS')
  H3 delete   orig[84:85] @586..586  ->  decomp[80:80] @576..574   n=1/0
        o @586 ('<JUMP>','JUMP')      # JUMP_BACKWARD 42 循环回边
```

三块 hunk 是 **一个** 根因的三个投影：raise 错位（H1）→ raise 占掉尾声位（H2，−4 条）→ 尾声被吞导致回边发射路径丢失（H3，−1 条）。合计 −5，与官方 `jump_diffs=2 true_diffs=14` 同向。

落地产物（`site-packages/fly/common/flytoolsOK.py` L866-889，只读）把 `raise` 放在整个 if/else 之后；arm-b 产物（`c1/build_b/fly__common__flytoolsOK.py`，见 `logs/diff_flytools_head_vs_b.txt`）为真码：

```python
             except OSError as e:
                 if e.errno != errno.EEXIST:
                     if os.path.exists(self.lockfile):
                         os.unlink(self.lockfile)
                     raise
                 if time.time() - start_time >= self.timeout:
                     os.unlink(self.lockfile)
                     raise FileLockException('Timeout occured.')
                 time.sleep(self.delay)
             else:
                 break
```

## 2. 根因链（全部首手，行号为落地 core 的行号）

CFG/区域事实（`logs/blockdump_head.txt`、`logs/probe32_head2.txt`，脚本 `c1/blockdump30.py`、`c1/probe32.py`，`--core mirr_head`）：

```
LoopRegion entry=B42 body=B42,B44,B180,B198,B200,B366,B508,B558,B584
  TryExceptRegion entry=B44 try=[B44] else=[B178]   (nb=16, blocks 含 B364)
    IfRegion entry=B200 cond=B200 then=[B242] else=[B366,B508,B558] merge=None
    IfRegion entry=B242 cond=B242 then=[B314] else=[]  merge=B364
B364  role=LOOP_ELSE  succ=B568  excsucc=B568  pred=B242,B314   RAISE_VARARGS 0
B314  role=LOOP_ELSE  succ=B364,B568  excsucc=B568  pred=B242    ... os.unlink
B558  role=LOOP_BODY  succ=B584  excsucc=-     pred=B508   POP_EXCEPT|LOAD_CONST|STORE_FAST e|DELETE_FAST e|JUMP_FORWARD 584
B584  role=LOOP_BACK_EDGE succ=B42            pred=B558   EXTENDED_ARG 1|JUMP_BACKWARD 42
_collect_branch_blocks @L17137 entry=B242 merge=-   stop=B8..,B314,B364,B366,B428,B568,B576,B578,B588 -> B242
_collect_branch_blocks @L17250 entry=B366 ...                                             -> B366,B508,B558,B584
```

链路：

1. `region_analyzer.py` L15433 `_identify_conditional_regions`；L16581 `boundary_stop = block_region.get_if_branch_boundary_stop(block)`；L16610 `boundary_stop |= self._get_enclosing_structural_boundary_stop(block)`（L26022）。对 B200 而言该停止集含 **B314 与 B364**（嵌套 if 的体内/汇合块被当作外层结构边界）。
2. L17135-17136 构造 `then_stop` / `else_stop`，L17137 `then_blocks = self._collect_branch_blocks(then_succ, merge, then_stop)`（L25808）→ then 臂只拿到 `[B242]`，**B364 被排除**；`IfRegion@B200` 的 `merge=None`，B364 也不在别处。
3. `B364` 的归属落到父区 `TryExceptRegion@B44` 的块表 → 发射侧 handler 循环 `region_ast_generator.py` L24661 起、L24695 `hbs = self._generate_handler_body_statements(hb)` 顺序尾部发射（L25900-25907 把 `RAISE_VARARGS 0` 编为 `{'type':'Raise','exc':None}`）。发射链首手记录见 `logs/probe_head.txt`、`logs/probe_head2.txt`（`c1/probe31.py` 逐方法栈回溯）。
4. 后果：raise 语句在 if/else 之后 ⇒ H1；handler 正常出口尾声（B558）与回边（B584）随尾部游标一并错位/丢失 ⇒ H2、H3。**尾声没有被"漏抄"，是发射顺序游标被错位块推动**。

**否证 Round 30 的"发射侧缺拷贝"框架（实测）**：本候选 **完全不改发射侧**（补丁只落在 `region_analyzer.py`），`acquire` 即 `65/65` 且严格尺子 0 hunks（`logs/hunks_b_flytools.txt`：`filtered orig=90 decomp=90 delta=+0 non-equal blocks=0`）。若真缺尾声拷贝，纯归属修正不可能补齐 5 条指令。

## 3. 候选同层判据

只读结构：块身份、区域角色字段（臂入口 / 兄弟臂入口 / `merge`）、`predecessors` / `successors` / `exception_successors` 关系。不读名字、常量、绝对偏移、指令条数、函数名/文件名。命中时 **仅从本臂局部停止集 `discard`**（只删不增：无新增发射、语句、块）。

> 注：第一版候选 R31-A1/A2（`spec/spec_r31a1.json`、`spec_r31a2.json`）按「已在 `self.regions` 里的嵌套 IfRegion 的 merge」表述，实测 **零效果**（`logs/w4_a1.jsonl`、`logs/w4_a2.jsonl` 与 head 读数完全相同），原因首手测得：做臂收集的那一刻嵌套 `IfRegion@B242` 尚未注册（`logs/probe34.txt`：`regions so far: TryExceptRegion@B44, LoopRegion@B42`）。故改写为下述 **纯 CFG 前驱/后继形式**。

### R31-B（站点一，L17136 之后）

锚点（唯一命中，1 次；文件 pure-CRLF、无 BOM，`region_ast_generator.py` 才有 BOM，本轮未触碰）：

```python
            then_stop = {else_succ} | (boundary_stop - {then_succ})
            else_stop = {then_succ} | (boundary_stop - {else_succ})
```

```python
            # [R31-B 同层判据 · 原则 2 每块唯一归属 · 臂内终止汇合块侧]
            for _r31b_arm, _r31b_other, _r31b_merge, _r31b_stop in (
                    (then_succ, else_succ, merge, then_stop),
                    (else_succ, then_succ, merge, else_stop)):
                if _r31b_arm is None:
                    continue
                _r31b_inner = {_r31b_arm}
                _r31b_go = True
                while _r31b_go:
                    _r31b_go = False
                    for _r31b_s in list(_r31b_stop):
                        if (_r31b_s is _r31b_merge or _r31b_s is _r31b_other
                            or _r31b_s is _r31b_arm):
                            continue
                        if (_r31b_s.successors
                            - (getattr(_r31b_s, "exception_successors", None) or set())):
                            continue
                        _r31b_preds = set(_r31b_s.predecessors)
                        if not _r31b_preds or not (_r31b_preds & _r31b_inner):
                            continue
                        if not _r31b_preds <= (_r31b_inner | _r31b_stop):
                            continue
                        _r31b_stop.discard(_r31b_s)
                        _r31b_inner.add(_r31b_s)
                        _r31b_go = True
                        break
```

三条件（①非 merge/非兄弟臂入口/非臂自身；②**无正常后继**，后继全在异常表边上＝硬出口块；③前驱 ⊆ 臂内集∪停止集且 ≥1 前驱在臂内）在 `acquire` 上逐条实测：B364 ①②③ 全中（`succ=excsucc={B568}`）；B314 被 ② 拒绝（正常后继 `{B364}`）故仍在停止集，嵌套 `IfRegion@B242` 的 `then=[B314]` 不被破坏；不动点仅一轮。释放后 `_collect_branch_blocks`（L25808）把 B364 收进 then 臂，且 W14-C 外部性剪枝不撤销它——L25951 `if _w14_p not in in_set and _w14_p not in stop:` 正是「停止集前驱豁免」，B314∈stop 故 B364 存活。

命中后的区域树（arm=b 实跑 `c1/blockdump30.py --core mirr_b`，`logs/blockdump_b_head.txt`）逐块印证机制：

```
IfRegion entry=B200 cond=B200 then=['B242','B364'] else=[] merge=None      # 夺回自身终点
IfRegion entry=B242 cond=B242 then=['B314']       else=[] merge=B364       # 嵌套区未被破坏
```

### R31-C（= R31-B + 站点二重放，推荐落地形式）

站点二锚点（唯一命中，L19268-19271）：`elif` 链汇合重建后 **重取** then 臂，用的是重建的 `_then_stop`，会把站点一的成果整体覆盖：

```python
                if boundary_stop:
                    _then_stop |= (set(boundary_stop) - {then_blocks[0]})
                then_blocks = self._collect_branch_blocks(
                    then_blocks[0], _chain_merge, stop_set=_then_stop)
```

R31-C 在 `_then_stop` 建好之后、重取之前，用 **同一判据** 重放一次（臂＝`then_blocks[0]`，兄弟＝`else_blocks[0] if else_blocks else None`，merge＝`_chain_merge`，停止集＝`_then_stop`），代码逐字符同站点一（仅缩进 +4）。

精确补丁文件（可直接交给落地工程）：
- `D:/Temp/r31diagA/spec/spec_r31b.json`（1 edit，40 插入行）
- `D:/Temp/r31diagA/spec/spec_r31c.json`（2 edits，40 + 28 插入行）— 生成器 `c1/mkspec31c.py`，两份均经 `py_compile` 通过、pure-CRLF 断言通过、`build` 断言插入行数一致。

## 4. 门禁读数（全部本人生成，出处随行）

| 门禁 | arm=head(=landed) | R31-B（站点一） | R31-C（两站点） |
|---|---|---|---|
| 靶子 `flytools.pyc` | `64/65 [['acquire',88,85,2,14]]` `logs/w4_head.jsonl` | **`65/65 []`** `logs/w4_b.jsonl` | **`65/65 []`** `logs/w4_c.jsonl` |
| 靶子严格 hunks | 3 hunks / −5 `logs/hunks_landed_tracked.txt` | `90/90`, **0 hunks** `logs/hunks_b_flytools.txt` | 同 b（402 上 b↔c 逐字节 SAME，故同一产物） |
| G0 见证 `r31a_witness.pyc` | `1/4`（w_a 52/47 jd4 td11、w_b 48/44 jd3 td14、w_c 64/63 jd2 td51 皆败）`logs/g0_landed.jsonl`,`logs/w4_head.jsonl` | `2/4`（**w_b 修复**） | `3/4`（**w_a+w_b 修复**，w_c 仍败） |
| G1 控制 `r31a_control.pyc` | `5/7`（c2、c6 在 landed 已败）`logs/g1b_landed.jsonl` | `5/7`，**产物 sha 与 head 相同** | `5/7`，**sha 同** |
| 38 复现电池 | — | SAME=38 / IMP 0 / REG 0（27 全配）`logs/bat38_{head,b}.jsonl` | SAME=38 / IMP 0 / REG 0 `logs/bat38_c.jsonl` |
| 98 锚点电池 | — | SAME=98 / IMP 0 / REG 0（70 全配）`logs/anc98_{head,b}.jsonl` | SAME=98 / IMP 0 / REG 0 `logs/anc98_c.jsonl` |
| **全 402 语料 A/B（sha-first）** | — | SAME=400 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0；全配文件 370→371 `logs/f402_ab.txt` | SAME=400 IMPROVED=1 REGRESSION=0 MOVED=1 ERR=0；370→371 `logs/f402_ac.txt` |
| B ↔ C 直接对比 | — | — | **SAME=402**（语料内零差异；差异只在合成 w_a/w_c） |

（窗口化子集已被"全 402 双臂"覆盖并超出要求；两臂各 402/402 条记录，8 个后台 shard 各 ≤100s，无 ERR。）

### 唯一的 MOVED 文件（诚实披露，与"非命中文件逐字节不变"的偏差）

402 中产物字节变化的文件只有 2 个（`logs/f402_*.jsonl` sha 对比）：

- `site-packages/fly/common/flytools.pyc`：`64/65 → 65/65`（目标翻转）。
- `site-packages/IQCommon/api/gtn_api.pyc`：`5/5 → 5/5`（官方尺子双臂全配），产物文本变化＝去掉 `if …: return (…)` 之后的 `else: time.sleep(1)` 的 `else` 缩进（`then` 臂以 `return` 终止，判据 ② 对 RETURN_VALUE 同样成立，故臂夺回自身终点块，`time.sleep(1)` 回到 if 之后的正常位置）。严格尺子双臂 **皆 0 hunks**（`logs/hunks_b_gtnapi.txt`、`logs/hunks_head_gtnapi.txt`：`send_by_get 118/118 blocks=0`、`send_by_post 113/113 blocks=0`），语义等价（then 臂必返回），且新版更贴近真源。**尺子中性、非回归**，但确实不是逐字节不变——落地时须接受这一处文本变动。

即：**命中面 = 2/402 文件、1 翻转 + 1 中性；其余 400 文件逐字节不变。**

## 5. Round 30 / Round 28 已排除项：复判（带量）

- **R30-A（预归约期拒收裸 `return None` 尾声）**：不重提。Round 30 记录其对本靶子产物逐字节相同；本轮独立佐证＝本靶子缺陷不是尾声拷贝问题（纯归属修正即 `90/90`、0 hunks）。锚点电池里 `r2_09_bool_cond_invert{,_dec,_dec_dec,_dec_dec_dec}.pyc` 在 B/C 两臂 sha 全同（`1/2,1/2,1/2,2/2` 不变）。
- **Round 30「removal-only 整类不可行」**：**仅对"异常尾声缺失"那一族成立**，对本形状不成立——本轮就是 removal-only（两站点都只做 `set.discard`）且翻转靶子。据此把该结论限定为「不适用于臂内终止汇合块形状」。
- **Round 28「本族需发射侧判据」**：对 `flytools.acquire` **否证**（见 §2 末）；Round 28 的原靶 `site-packages/IQEngine/plugins/plugin_system_risk_calculation/function.pyc`（`14/15`，`save_testds_to_json 314/310 jd=19 td=8`）在本候选下 **sha 不变、读数不变**（`logs/f402_{head,c}.jsonl`）⇒ 两族确为两族，本判据不去碰它。
- **Round 30「不要把 flytools 并入 return-None 簇」**：确认。本候选同时命中 `gtn_api`（return 终止臂）而不命中 return-None 簇，形状按「臂内硬出口」而非「尾声类型」聚类。
- **`26106-26108` 放宽**：未重提（本轮补丁不触及该处）。

## 6. 「一个形状还是两个形状」

**两个形状（同一判据，站点不同）+ 第三个残余形状**：

1. 形状 1（`acquire`、`w_b`）：外层 if `merge=None`，仅站点一即修复 ⇒ **R31-B 足够翻转靶子**。
2. 形状 2（`w_a`）：外层 if 的 merge 稍后由 `elif` 链汇合重建（L19262-19271）恢复，并用重建停止集 **覆盖** 站点一的成果 ⇒ 需站点二重放；R31-C 下 `w_a` 由败转配（head 记为 `52/47 jd=4 td=11`，见 `logs/w4_head.jsonl`；C 臂 `logs/w4_c.jsonl` 的 mism 列表里已无 `w_a`，见证整体 `1/4 → 3/4`）。语料内 402 文件 b↔c 零差异 ⇒ 站点二在真实语料上 **测得中性**，其价值目前只在合成形状上可见。
3. 形状 3（`w_c`，arms 均硬出口 + 更深嵌套）：B/C 两臂都未修复（官方 `64/63 jd2 td51` 不变；严格侧由 landed 的 `5 hunks / delta −1` 变为 `3 hunks / delta +3`，见 `logs/hunks_witness_landed_vs_b.txt`、`logs/hunks_c_w_c.txt`），残余项是「隐式 `return None` 对过量发射 + 一个 jump 槽」，与本判据无关，另案。
4. 控制侧非命中理由（逐块实测，非推断）：`c2` 臂尾是 `break`——B106 `succ=B154, excsucc=∅` 有正常后继，条件 ② 拒（`logs/probe32_c2_arm_tail_is_break.txt`）；`c6` 两臂各自的 raise 块 B82/B100 **本已在臂内**（`L17137 -> B66,B78,B82` / `L17250 -> B84,B96,B100`，停止集里根本没有 S），判据无从触发（`logs/probe32_c6_both_arms_end_in_raise.txt`）。c2/c6 在 landed 已败（另族），本轮两臂 sha 不变，**不可作为"保持全配"的控制**，只作"不触发"证据。

## 7. 可落地性与置信度

- 靶子 **可翻转**（不是只能收缩）：`64/65 → 65/65`，官方与严格两把尺子同时归零，产物文本＝真码。
- 同层性：判据只读身份/角色字段/前后继关系（代码内无任何 `co_names`/`consts`/offset/count/函数名）；只删不增（`discard`），非命中路径逐字节不变（400/402 实测印证，唯一偏差为 `gtn_api` 的尺子中性 `else` 移除）。
- 置信：**高**。依据＝全 402 双臂 sha A/B（REGRESSION=0、ERR=0）+ 38/98 电池 SAME + 严格尺子 0 hunks + 逐条件 CFG 首手核对（B364 中、B314 由 ② 排除）。
- 建议发货形式：**R31-C**（两站点），与 R31-B 在语料上逐字节同果、并额外修复形状 2；若要把改动面压到最小，可先落 R31-B（靶子同样翻转），把站点二留作后续轮次。
- 残余风险（需编排方接受）：(a) `gtn_api.pyc` 的尺子中性文本变化；(b) 站点二在 402 语料内零命中，其在真实语料之外的 `elif`-链形状上的效果 **未测**（不外推）；(c) 语料外的合成形状 w_c 与 c2/c6 类残余项不属本判据。

## 8. 出处与复算命令

产物清单（均本人生成）：`witness/r31a_witness.{py,pyc}`、`witness/r31a_control.{py,pyc}`（`py_compile.compile(f, cfile=<path>, doraise=True)`，Python 3.11.7）；镜像 `c1/mirr_{head,a1,a2,b,c}`（`region_analyzer.py` 私有副本）；产物 `c1/build_<arm>/`；日志 `logs/*`；脚本 `c1/{r31c,hunks30,blockdump30,probe31,probe32,probe33,probe34,mkspec31,mkspec31b,mkspec31c}.py`；列表 `w4.txt`、`reprobat38.txt`、`anchors98.txt`、`all402.txt`。

```sh
cd D:/Temp/r31diagA/c1
python -X utf8 r31c.py build --spec=D:/Temp/r31diagA/spec/spec_r31c.json --dst=c
python -X utf8 r31c.py run --arm=c --list=D:/Temp/r31diagA/all402.txt \
  --out=D:/Temp/r31diagA/logs/f402_c_s0.jsonl --nshard=4 --shard=0     # ×4 后台
python -X utf8 r31c.py ab --a=D:/Temp/r31diagA/logs/f402_head.jsonl \
  --b=D:/Temp/r31diagA/logs/f402_c.jsonl
python -X utf8 hunks30.py F:/Downloads/pythoncdc-main/site-packages/fly/common/flytools.pyc \
  D:/Temp/r31diagA/c1/build_b/fly__common__flytoolsOK.py acquire
```
