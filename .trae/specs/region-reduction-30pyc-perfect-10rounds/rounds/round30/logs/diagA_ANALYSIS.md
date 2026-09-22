# Round 30 (diag A) — 异常尾声内联副本发射侧：靶子实测与 R30-A 判据

基线：落地核 `06f0ba50`（含 R29-A）。本文件全部为**镜像打戳实测**，未改动仓库一处。
`landed` 臂 = 仓库核字节；`cand` 臂 = R30-A；`noprune` = 整体关掉预消解（对照）。
本轮实测 jsonl：`w17_{landed,cand}.jsonl`、`rb38_{landed,cand}.jsonl`、`an96_{landed,cand}.jsonl`。

## 0. 结论速览

- 两个靶子**不是同一种缺陷**（修正 Round 28 的「同族」归并）：
  - `function.pyc :: <module>.save_testds_to_json` = **发射侧缺一份内联 `return None` 尾声副本**。
  - `flytools.pyc :: <module>.FileLock.acquire` = **裸 raise 迁移 + `except-as e` 清理尾声 + 环尾回边丢失**的混形，
    尾声载荷是 `STORE/DELETE e`（as-var 清理）而非 `return None`，**不由 R30-A 命中**（实测 cand 对其字节零改动）。
- 关键实测结论：**不存在既窄又安全的发射侧判据能在预消解侧（1557-1586）修复 function.pyc。**
  R30-A（拒绝消费 bare-return-None 尾声）实测：**改进 0、函数靶子仅把副本移到函数尾（MOVED，仍 310），
  且在 `r2_09_bool_cond_invert_dec*` 合成锚上造成真回归**（102/102→96/80）。故 R30-A 应 **REJECTED**，
  移交的是 §3 的「按跳转前驱把副本重新挂回 except 退出口」发射侧重设计（**INFERRED，未落地**）。

## 1. Per-target 实测表（official ruler，landed 核，本轮重测）

| 靶子 pyc | 文件读数 | 失败函数 | orig/decomp | jump/true | strict kind | cand(R30-A) |
|---|---|---|---|---|---|---|
| `IQEngine/plugins/plugin_system_risk_calculation/function.pyc` | 14/15 | `<module>.save_testds_to_json` | 314/310 | 19/8 | `seq_len` | 314/**310**（MOVED，字节+1 行 `return None`） |
| `fly/common/flytools.pyc` | 64/65 | `<module>.FileLock.acquire` | 88/85 | 2/14 | `seq_len` | 88/85（**字节零改动**） |

> `bytecode_diff` 报 orig=88（官方尺），严格尺 filtered=90（对 CACHE/行号对齐口径不同），逐指令定位以严格尺为准。

### 1a. function.pyc :: save_testds_to_json —— 首处分歧（原始字节码偏移）

`fd30.py`（严格 token 字母表 + 跳转目标折叠 + difflib 对齐）：

```
orig=314 decomp=310 delta=-4   non-equal blocks: 1
  DELETE  orig[302:306](4) -> decomp[302:302]   off o@1976 d@1978
```

即 orig 的 @1976-1982 四连 `POP_EXCEPT; POP_EXCEPT; LOAD_CONST None; RETURN_VALUE`
（= 块 B1976@1976 + B1978@1978-1982）在产物中整体缺失。

**LOST 还是 MOVED（mv30.py）**：`DELETE orig@1976..1982 n=4 : MOVED(->decomp off 1970) n=4/4`。
—— 该 MOVED 是**假阳性**：`POP_EXCEPT;POP_EXCEPT;LOAD_CONST None;RETURN_VALUE None` 这条 token 串**自重复**
（orig 出现 **2 次**：@1968-1974 与 @1976-1982；decomp 只出现 **1 次**）。逐串搜索必命中另一份同形串。
实测串计数证明是 **LOST 的第二份内联副本**：orig count=2、decomp count=1。**分类：LOST（发射侧少一份）。**

CFG 归属（`block_to_region` 直查 + `blockdump30.py`）：
```
B1968 role=EXCEPT_STORE owner=TryExceptRegion@1162(try)  POP_EXCEPT                              <- 存活副本(前导)
B1970 role=EXCEPT_STORE owner=TryExceptRegion@1162(try)  POP_EXCEPT LOAD_CONST None RETURN_VALUE  <- 存活副本(发射)
B1976 role=PURE_JUMP    owner=Region@1976 (顶层 BASIC)    POP_EXCEPT                              <- 缺失副本(被消费)
B1978 role=RETURN       owner=Region@1978 (顶层 BASIC)    POP_EXCEPT LOAD_CONST None RETURN_VALUE  <- 缺失副本(被消费)
```
两份尾声对应 except 的**两条不同退出路径**（B1968←B1512 走 try 内、B1976←o#293@1958 `JUMP_FORWARD 1976` 落到顶层），
CPython 3.11 每路各内联一份；核只为「在 try 区内」那份发射，「落到顶层 BASIC」那份被预消解吃掉。

### 1b. flytools.pyc :: FileLock.acquire —— 三处分歧（混形，非 return-None 尾声）

```
orig=90 decomp=85 delta=-5   non-equal blocks: 3
  REPLACE orig@364 n=1 (RAISE_VARARGS 0)  -> decomp@364 n=1 (JUMP_FORWARD 558)
  REPLACE orig@558 n=5 (POP_EXCEPT LOAD_CONST None STORE_FAST e DELETE_FAST e JUMP_FORWARD 584)
                                          -> decomp@558 n=1 (RAISE_VARARGS 0)
  DELETE  orig@586 n=1 (JUMP_BACKWARD 42  <- 循环回边)  (mv30 报 MOVED=假阳性: 同 op 串在 idx20@178 复现)
```
`while:` 环（LoopRegion@42，回边 B584→B42）内含 `try/except OSError as e:`。B558 是 except 正常出口的
**as-var 清理尾声** `POP_EXCEPT;LOAD_CONST None;STORE_FAST e;DELETE_FAST e;JUMP_FORWARD→回边`；核把裸 `raise`
迁移到 @558，于是 `STORE/DELETE e` 清理 + 回边一并丢失。尾声载荷是 as-var 而非 return-None，**R30-A 不覆盖**，
需独立「as-var 清理尾声 + 回边保序」判据（列 §5 移交）。

## 2. 发射侧站点定位（按 STAMP 实测，非推断）

p30a（9 枚行为中性戳）/ p30b（2 枚决定戳），全部落在**真实语句**上（教训：戳若落在 `elif`/`else` 续行会重挂分支链、
污染控制流；修正后干净臂读数与 landed **逐字节 14/15 一致**，证明行为中性）。原始偏移门控输出：

**EMIT（存活副本）** — `_generate_handler_body_statements`，`region_ast_generator.py:26091-26092`
（`elif self._try_depth > 0 and not stmts:` → append `Return value=None`）。实测：
```
[R30B EMIT-HBS-RETNONE] cfg=save_testds_to_json emit_block=1970 try=2
[R30P HBS-ENTRY] off=1968/1970 try=2 stk=
   _generate_block_statements_body <- _build_store_statement <- _build_function_def:1949
   <- generate:1629 <- _generate_region:3062 <- _generate_try:24607 <- _generate_try:24697
[R30P HBS-RETVAL] off=1970 try=2 ns=0
```
（行号为戳版镜像，已相对 pristine 位移；pristine 发射行 = 26091-26092。栈显示副本经 **try 处理器路径** 产出。）

**CONSUME（缺失副本被丢）** — 顶层「异常清理-only BASIC 区」预消解，`region_ast_generator.py:1557-1586`，
其门控 1582 `if _has_meaningful_return: continue` 因该尾声 `LOAD_CONST` 的 `argval is None`（非「有意义」）而不 continue，
遂执行 1585-1586 `generated_blocks.add/_offsets.add` 静默消费。实测：
```
[R30B CONSUMED] cfg=save_testds_to_json consumed_block=1976 region_entry=1976
[R30B CONSUMED] cfg=save_testds_to_json consumed_block=1978 region_entry=1978
[R30P REG] entry=1976/1978 rtype=BASIC cleanskip=False   ; [R30P BASICDISPATCH] entry=1976/1978（随后被消费，不到发射）
```

**关键否证（removal-only 无效）**：`noprune` 与 `cand` 都只把这份尾声**吐到函数尾**，重编译后指令数仍 **310**
（`build_landed/...functionOK.py` 无第 368 行；`cand` 多一行 `    return None`，`matched=14/15` 不变、mism 仍 19/8）。
即：**光是「别消费」不会把它放回结构正确位置**——函数尾隐式 return 会与之合并，净增指令 0。
→ 修复必须在**正确的 except 退出口发射**（emission-side），预消解侧的 removal-only 判据不可能奏效。

## 3. 候选判据 R30-A（排序第一，实测后 REJECTED）+ 唯一可行移交设计 R30-A′

**R30-A（实测候选，removal-only，站点=预消解 1585 前）**：
> 谓词（纯结构）：一个顶层 BASIC 区，其所有块指令 ∈ {`POP_EXCEPT`, `LOAD_CONST(argval is None)`, `RETURN_VALUE`}
> 且含 ≥1 `RETURN_VALUE`，则**不消费**（原逻辑会消费）。锚点：`region_ast_generator.py:1582-1586`，
> 紧邻既有守卫 `if _has_meaningful_return: continue` 之后插入。
- **实测结论：REJECTED。** 改进 0；function.pyc 仅 MOVED（副本移到函数尾，deficit 不变）；且在合成锚
  `r2_09_bool_cond_invert_dec` 上把 landed 的 102/**102** 打成 96/**80**（伪造 `else: return None` 分支，deficit 0→16，真回归）。
- 如何避开 R28 的 12 文件回归集：R28 回归源于**放宽发射侧抑制 `26106-26108`**；R30-A 命中的是**不同站点（预消解 1585）**，
  与 26106 不相交，故 17 文件窗内 0 回归（实测 SAME=14 MOVED=3）。**但避开 12 文件集 ≠ 安全**——锚族暴露了它的回归。

**R30-A′（唯一能修 function.pyc 的方向；INFERRED，本轮未落地）**：emission-side、按结构 re-attach。
> 谓词：仅当某顶层 bare-return-None 清理尾声区，存在一条**来自 try/except 处理器出口的 `JUMP_FORWARD` 前驱**
> （实测 o#293@1958 →@1976）指向它，且本函数 CFG 内**另有 ≥1 份同形 `POP_EXCEPT×2 LOAD_CONST(None) RETURN_VALUE` 已被发射**
> （即确为 CPython 逐退出路径的第二份拷贝）时——**不消费**，并把该 `return None` **挂到该处理器退出口**（经
> `_generate_handler_body_statements` 的 26091 等价路径），而非作为顶层尾语句。
- 「≥1 份已发射同形副本」这一 sibling 计数门是区分 function.pyc（真·重复）与 bool_cond_invert 锚（孤立、应被消费）的
  结构开关，可避开 §4 的锚回归。但**位置正确性**还需处理器-前驱映射（改区域生成器，非预消解 tweak），
  本轮范围内无法验证为绿，**故仅移交设计、不主张可落地**。

## 4. 触发面实测（NOT the 402；分类按 sha 字节 + ruler）

| 集合 | n | SAME | MOVED(字节变·ruler 同) | IMPROVED | REGRESSION |
|---|---|---|---|---|---|
| 17 文件窗 `wl_all17` | 17 | 14 | 3 (function, r28_repro, trade_live_broker) | 0 | **0** |
| 38 合成 repro `reprobat38` | 38 | 37 | 1 (r2_04_return_in_loop_finally) | 0 | **0** |
| 96 锚 `anchors96` | 96 | 93 | 1 (r2_04_return_in_loop_finally) | 0 | **2** |

- 锚回归 2 例：`r2_09_bool_cond_invert_dec`（102/102→**96/80**，deficit +16）、`..._dec_dec`（99/100→99/99，lateral/劣）。
  根因实测：cand 在该函数伪造 `else:\n    return None`（diff @52→+53,54），把 landed 的计数对齐打乱。
- function.pyc/r28_repro 的 MOVED：cand 于产物**尾部新增 `return None`**，重编译后 orig/decomp 仍 314/310、100/96，deficit 未闭合。
- jsonl：以上全部见 `D:/Temp/r30diagA/{w17,rb38,an96}_{landed,cand}.jsonl`（cand 臂 = `mirr_cand`，spec `spec_r30a.json`）。

## 5. 语料无关合成 repro（设计）+ CONTROL

> 诚实标注：**本轮未新编译**（turn 预算）；下列形状与 §1 的 r28_repro（100/96，实测已存在）同构，判定为
> **INFERRED-from-measured**（repro 形状 = 已实测 r28_repro 的等价改写；CONTROL 为可编译规格）。移交落地上应 COMPILE+MEASURE。

- **REPRO（应触发 function 型 LOST）**：多层嵌套 `try/except BaseException`，**两条 except 退出路径均以隐式 `return None` 收尾**
  且其中一条落到函数顶层（编译器为第二路内联 `POP_EXCEPT×2;LOAD_CONST None;RETURN_VALUE`）：
```python
def repro(x):
    try:
        a()
        return None
    except BaseException:
        try:
            b()
            return None
        except BaseException:
            try:
                c()
            except BaseException:
                d()
            return None      # 第二路的内联清理尾声 = 被预消解吞掉的那份
```
- **CONTROL-1（不应触发；单路 return-None）**：仅一层 except 尾随 `return None`，无第二份顶层清理尾声
  → 预消解无 bare-return-None 顶层区可消费 → cand 字节 SAME。用于证明判据不误伤单副本情形。
- **CONTROL-2（隔离 flytools 形；as-var）**：`while True: try:...; except OSError as e: <fall-through 回边>`，
  尾声载荷为 `STORE/DELETE e` 而非 return-None → **R30-A 谓词不命中**（实测 flytools cand 字节零改动佐证），
  证明「return-None 尾声」与「as-var 清理尾声」是两个正交簇，须各自判据。

## 6. Measured vs Inferred + Rejected clusters

**MEASURED（本轮镜像打戳/ruler/diff 直接观测）**：
- 靶子读数、首处分歧偏移、LOST 二判（串计数 2 vs 1）、CFG 归属、EMIT@26091(emit_block=1970 try=2)、
  CONSUME@1585(consumed_block=1976/1978)、noprune/cand 仅 MOVED 到函数尾（310 不变）、
  flytools cand 字节零改动、R30-A 的 17/38/96 全 tally、bool_cond_invert 锚 102/102→96/80 回归。

**INFERRED（未直接观测，据测得外推）**：
- R30-A′ 的「挂回处理器退出口可闭合 deficit」——需区域生成器改造 + 前驱映射，本轮未实现未验证。
- §5 合成 repro/CONTROL 的字节级读数（形状等价于已实测 r28_repro，未各自 COMPILE）。
- flytools 三处混形的可修性（仅定位，未测任何修复判据）。

**REJECTED clusters —— 不要选这些，因为…**
1. **R30-A（预消解侧拒绝消费 bare-return-None）**：改进 0（仅 MOVED），且在 `r2_09_bool_cond_invert_dec*` 造成真回归（+16 deficit）。已实测否决。
2. **removal-only 全类（含 noprune）**：`§2` 否证——函数尾 `return None` 与隐式返回合并，净增 0 指令，deficit 永不闭合；发射**位置**才是瓶颈。
3. **把「flytools.acquire」并入本簇**：尾声是 as-var `STORE/DELETE e` + 回边丢失，字节层与 return-None 谓词正交，强行覆盖会牵动 LOOP/raise 迁移，风险面 = R28 抑制放宽级别，不可窄。
4. **放宽 `26106-26108` 抑制以多吐 return-None**：正是 R28 12 文件回归来源（quotation.pyc HTTPError 会得 4 个伪 `return None`），本方案站点须保持在预消解/处理器 re-attach，不得触碰 26106。
