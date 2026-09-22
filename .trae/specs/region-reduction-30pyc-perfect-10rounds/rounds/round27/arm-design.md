# Round 27 · 诊断线 B（elif 链中段条件整块丢失）—— ANALYSIS

工作目录 `D:/Temp/r27diagB/`，靶子
`F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_persist/__init__.pyc`
:: `<module>.ObjectPersistancePlugin.can_resume_strategy`，严格尺 `orig=89 decomp=57`（−32），
该文件唯一缺陷（官方尺 14/15）。所有测量在**当前落地字节**（HEAD `481a8e84`，含 R26-A）上做。

工具（全部为本目录私有镜像，未触碰仓库工作树）：
`r27d.py`（r26a.py 镜像法移植：`build --spec` 造 `mirr_head`/`mirr_cand`，`run --arm`，`one --arm`）、
`insp26.py`（区域树）、`strict26.py`（严格尺 + 官方尺逐函数）、`dumpfn26.py`（码流对照）、
`probe_elif27.py`（分析器 `_check_elif_chain` 全 `return` 打戳）、
`probe_gen27.py`（生成器发射路径 `return`/`continue` 打戳）。

---

## 一、缺陷（带字节偏移，实测）

原始码流 11 块 / 89 条（过滤 NOP/CACHE/PRECALL/EXTENDED_ARG 后）：

| 块 | start_offset | 源码语句 | 条数 | 末指令 → 后继 |
|---|---|---|---|---|
| B0 | 0 | L94 `if persist_meta['start_date'] != self._meta['start_date']:` | 10 | POP_JUMP_FORWARD_IF_FALSE →178，真边 B48 |
| B48 | 48 | L95-96 `raise RuntimeError(…)` | 18 | RAISE_VARARGS，**无后继** |
| B178 | 178 | L99 `if persist_meta['last_calendar_dt'] is None:` | 4 | POP_JUMP_FORWARD_IF_NOT_NONE →198，真边 B194 |
| B194 | 194 | L100 `return False` | 2 | RETURN_VALUE，无后继 |
| B198 | 198 | L103 `if … > self._meta['end_date']:` | 9 | POP_JUMP_FORWARD_IF_FALSE →374，真边 B244 |
| B244 | 244 | L104-105 `raise RuntimeError(…)` | 18 | RAISE_VARARGS，无后继 |
| **B374** | **374** | **L106 `if … == self._meta['end_date']:`** | **9** | POP_JUMP_FORWARD_IF_FALSE →424，真边 B420 |
| B420 | 420 | L107 `return False` | 2 | RETURN_VALUE，无后继 |
| B424 | 424 | L110/L111 两条赋值 + L112 `if next_start_date > …:` | 21 | POP_JUMP_FORWARD_IF_FALSE →548，真边 B544 |
| B544 | 544 | L113 `return False` | 2 | RETURN_VALUE |
| B548 | 548 | L115 `return True` | 2 | RETURN_VALUE |

**前驱与边类型（`insp26.py` 原始输出 `logs/insp_current.txt` L7-19，HEAD 字节）**：

```
[cond] B0   n=10 last=POP_JUMP_FORWARD_IF_FALSE    ->178 pred=-                       succ=B48,B178
[cond] B178 n=4  last=POP_JUMP_FORWARD_IF_NOT_NONE ->198 pred=B0:COND(FORWARD_IF_FALSE@178)    succ=B194,B198
[cond] B198 n=9  last=POP_JUMP_FORWARD_IF_FALSE    ->374 pred=B178:COND(FORWARD_IF_NOT_NONE@198) succ=B244,B374
[then] B48  n=18 last=RAISE_VARARGS                     pred=B0:COND(FORWARD_IF_FALSE@178)     succ=-
[else] B194 n=2  last=RETURN_VALUE                      pred=B178:COND(FORWARD_IF_NOT_NONE@198) succ=-
[else] B244 n=18 last=RAISE_VARARGS                     pred=B198:COND(FORWARD_IF_FALSE@374)   succ=-
[else] B374 n=9  last=POP_JUMP_FORWARD_IF_FALSE    ->424 pred=B198:COND(FORWARD_IF_FALSE@374)  succ=B420,B424   ← 丢失块
[else] B420 n=2  last=RETURN_VALUE                      pred=B374:COND(FORWARD_IF_FALSE@424)   succ=-
[else] B424 n=21 last=POP_JUMP_FORWARD_IF_FALSE    ->548 pred=B374:COND(FORWARD_IF_FALSE@424)   succ=B544,B548
[else] B544 n=2  last=RETURN_VALUE                      pred=B424:COND(FORWARD_IF_FALSE@548)   succ=-
[else] B548 n=2  last=RETURN_VALUE                      pred=B424:COND(FORWARD_IF_FALSE@548)   succ=-
```

每条假边逐一指向下一个条件块（178→198→374→424→548），四条臂（B48/B194/B244/B420/B544/B548）
全部无后继；**产物里缺文本的是 B374**（条件整块消失），并连带 B424/B544/B548 被死代码消除。

产物（`__init__OK.py` L71-84）码流只到 d56：

```
if … != …:  raise …        # B0/B48  ✔
elif … is None: return False   # B178/B194 ✔
elif … > …:  raise …       # B198/B244 ✔
else:
    return False           # B420 —— 它的条件 B374 整块消失
    next_start_date = …    # B424/B544/B548 的文本在产物里存在，但重编译时
    …                      # 落在上面那条无条件 return 之后 ⇒ 编译器按死代码消除
```

**消失的指令**：B374 的 9 条（条件求值 + 条件跳转）+ 尾部 B424/B544/B548 的 25 条被
CPython 3.11 编译器在 `return False` 之后整段死代码消除 ⇒ 89−32=57。
（`dumpfn26.py` 输出 `logs/dump_canresume.txt`：decomp 流最后两条正是
`LOAD_CONST False / RETURN_VALUE`，offset 374/376，即 B420 被搬到了 B374 的位置。）

## 二、区域层级（当前落地字节实测，`logs/insp_current.txt`）

```
IfRegion entry=B0 blocks=11   cond=B0 then=[B48] merge=-
   elif_conditions=[B178, B198]   elif_bodies=[[B194],[B244]]
   elif_final_else=[B374, B420, B424, B544, B548]      ← B374 在这里被当成扁平语句表表头
  IfRegion entry=B178 blocks=9  cond=B178 then=[B194] merge=-     ← 子区域，第二套归属
     elif_conditions=[B198, B374]  elif_bodies=[[B244],[B420]]
     elif_final_else=[B424, B544, B548]
    IfRegion entry=B424 blocks=3  cond=B424 then=[B544] else=[B548]
```

B178..B548 同时属于外层链（`elif_conditions` + `elif_final_else`）与内层链 ⇒ 违反原则 2。
内层链 `elif_conditions` 里有 B374，外层链却把 B374 放进 `elif_final_else`（语句表）。

**回答「是区域归约塌缩还是区域建好但块被标记已生成」**：塌缩在建区域阶段，不是发射阶段——
同一份日志里 B424 有自己的 `IfRegion entry=B424`（生成器可委托），
而 B374 只有 `Region entry=B374 blocks=1`（基础块区域，**没有** `IfRegion entry=B374`）：
`_build_elif_region(B374, then=[B420], else=[B424,…])` 在下一级 `_has_body_stmt`（18340）返回 None，
B374 仅作为 B178 子链的 elif 条件存在。⇒ 外层链把它当语句表表头时，生成器**无从委托**，
也没有「已生成标记」可言（§3.3 打戳证实发射 0 条）。

## 三、阻断点（打戳实测，非阅读）

### 3.1 分析器侧：链在 B374 前一级中止，命中的是 `region_analyzer.py:18171`

`probe_elif27.py` 把 `_check_elif_chain` 内**每一个** `return` 打行号戳（原文件行号 =
戳号−40−之前插入的戳数，已逐条核对），对靶子 code object 直接跑 `RegionAnalyzer.analyze()`
（`logs/probe_elif_err.txt`）：

```
R27 ENTER  hdr=B198 else=[B374,B420,B424,B544,B548] merge=-       (B0 链的第 3 级递归)
R27 RET-VAL line=18213  →  原文件 18171 `if _then_has_ctrl_exit: return None`   ★ 唯一命中
```

同一 level 在**另一条**发起路径上却成功（外层 entry=B178 的区域自己建时）：

```
R27 ENTER  hdr=B198 else=[B374,B420,B424,B544,B548] merge=-       (B178 区域的第 2 级递归)
R27 RET-VAL line=19078 → 原 19019 return result   cond=[B374] bodies=[[B420]] fe=[B424,B544,B548]
```

逐条早退排查（**只有 18171 触发**，其余不触发）：
* 18021 `if not else_blocks_: return None` — 不触发（else 表非空）。
* 18170/18171 **触发**（见 3.2）。
* 18199（`first_else` 无条件后继≠2）/ 18206（后向条件跳回循环头）/ 18263（R37 嵌套 if + continue）
  / 18271（短路跳转是值表达式）— 均不触发。
* 18340 `_has_body_stmt` — 在 B374 级**不**触发（B374 是纯条件块）；它在**下一级**
  （hdr=B374，`first_else`=B424，B424 带两条赋值）触发并正确终止扩展
  （`R27 RET-VAL line=18387 → 原 18340`），这正是链应有的收尾（B424 是 else 体）。
* 18346（`else_block_conflict`）/ 18352 / 18410（三元）/ 18522 / 18860 / 18896 / 18922 / 19022
  — 均不触发。

⇒ 链的 4 级条件在**第 3 级**被 `_then_has_ctrl_exit` 否决，B374 被降级成 `elif_final_else`
语句表表头。

### 3.2 18171 为什么触发：`region_analyzer.py:18144`

`_check_elif_chain` 的「控制退出」前奏（原 18022-18137）判 `_then_has_raise` /
`_then_has_explicit_return` 时读的是**闭包变量 `then_blocks`** = `_build_elif_region`
那一层（最外层 if）的 then 臂，而不是当前递归级的前一臂。第 3 级时：

* B0 发起的链：`then_blocks=[B48]`，末指令 RAISE_VARARGS 且无后继 → `_then_has_raise=True`；
  18104-18113 在 `else_blocks_=[B374,…]` 中找不到「同样以 RAISE 收尾的无后继块」
  （B420/B544/B548 是 RETURN）→ `_then_has_ctrl_exit=True`；
* 18138-18145 的救援分支已经认定 `_first_else=B374` 有 2 个条件后继、末指令是
  `POP_JUMP_FORWARD_IF_FALSE`（正下一个 elif 条件块的形状），却在
  **`if not _then_has_raise:` 这一行被否决** → 落到 18171 `return None`。
* B178 发起的同型链：`then_blocks=[B194]`（RETURN 形，`_then_has_raise=False`）→ 救援生效
  → 链含 B374。这就是「同一个结构、同一个入参 `(hdr=B198, else=[B374,…], merge=None)`，
  只因发起层的第 0 臂是 raise 还是 return，结论相反」的实测证据。

### 3.3 生成器侧：B374 被语句化时发射 0 条（不是「整块跳过」守卫）

`probe_gen27.py` 在 7 个 `_generate_*` 函数的全部 `return`/`continue` 打戳，跑语料外合成复现
（`logs/probe_gen_repro_err.txt`）：

```
R27G CONT line=44175 fn=_generate_block_statements_body offs=B190,B226,B230 lists=[B226,B230]
R27G RET  line=44262 fn=_generate_block_statements_body offs=B190,B226,B230
R27G RET  line=41650 fn=_generate_block_statements      offs=B190        ← 返回 []
```
即纯条件块 B190（=语料 B374 的复现对应块）在 `_process_if_blocks`（`elif_final_else`
的语句化，调用点 `region_ast_generator.py:14834` / `15866`）里被
`_generate_block_statements_body` 判为「无能成为语句的内容」→ 发射 0 条，
条件文本**永久丢失**；随后 B226（=B420）作为普通语句发射成无条件 `return False`，
其后的 B230/B338/B342（=B424/B544/B548）成为死代码。

**已否证的生成器现场**（本轮再测一遍，仍然成立）：
`_generate_if` 里「本区域 entry 出现在**另一个** IfRegion 的 `elif_conditions` ⇒ 发射 `[]`」
守卫（当前字节 `region_ast_generator.py:11156-11159`）在靶子与复现上**均无戳**
（`uniq -c` 统计里只有 `RET 11017 ×2`、`RET 11163 ×1`，无 `RET 11159`）⇒ 该站点仍与本案无关，
继续禁用。生成器侧也无「区域建好但块被标记已生成」的丢法：B374 根本没有以它 entry 的区域
（`_build_elif_region(B374, then=[B420], else=[B424,…])` 因 `_has_body_stmt`（B424）返回 None，
B374 只作为 B178 子区域的 elif 条件存在），所以生成器无从委托。

## 四、真实源码形状（只看原始码流跳转布局）

B0/B178/B198/B374 的假边**逐一指向下一个条件块**（178→198→374→424），四条臂全为
sink（raise/return，无后继，故无 JUMP_FORWARD）；只有第 4 个条件 B374 的假边进入的 B424
**自带两条赋值**，不是纯条件块。⇒ 真实源码是 5 条**平级独立 if**（无任何 elif），
`if/elif…` 展平与 `if…; if…` 在 3.11 下码流逐条相同。因此结构判定必须保证
**每个块唯一归属且文本完整**：
* 要么外层链一路吃到 B374、以 B424 为 else 体（`conditions=[B178,B198,B374]`，
  `final_else=[B424,B544,B548]`）——实测这与原始码流逐条同形；
* 要么外层链在 B178 处就让位给子区域（外层 `else:` 体直接渲染子 IfRegion(B178)）。
现在两者混用：外层吃掉了子链的前两级条件、又把子链的第三级条件 B374 塞进扁平语句表
⇒ B374 无从发射。

## 五、候选判据（定稿 R27-A）

### 5.1 形状学结论与被否证的宽松版

形状学结论：**在「链的下一级候选头块 F 是纯条件块」时，「上一臂以 raise 终结」不构成
把链中止的理由**——纯条件块没有语句化表示（§3.3 实测发射 0 条），中止链必然吞掉它的
条件文本；而继续吃进链则由 18288-18340 既有的 `_has_body_stmt` 纯度判据（同层、读块
自身指令）保证「带前导语句的块（B424）仍然终止扩展」。

**宽松版 C2（已实测否证）**：18144 处只加「F 是纯条件块」一条放行
（`spec_c2.json`，`logs/ab402_head_vs_cand_C2.txt`、`logs/strict402_C2.txt`）：

* 官方尺 402 文件 A/B：`{'SAME': 394, 'IMPROVED': 1, 'MOVED': 7, 'REGRESSION': 0, 'ERR': 0}`；
* 严格尺却抓到一处**真退化**：
  `fly/common/tradingday_calendar.pyc <module>.get_start_day head=None d=212 → cand=target_diff d=212`
  （`#79 JUMP 终点 orig=('start_date','LOAD_FAST') decomp=('get_minite_time',...)`）。
  产物差异：C2 把独立的 `if type == 'daily': … else: …` 误并进链，
  并将 `start_date, end_date = get_minite_time(end_date, count)` 从 `else` 体里抬了出来。

⇒ 「F 是纯条件块」不充分，还缺一个同层结构事实。

### 5.2 判别事实（`probe_guard27.py` 实测，非阅读）

在 18170 否决点前插一条戳，打印该层的全部同层事实（`self/then_blocks` 为闭包变量，
已在戳里读出）。语料对照（`logs/gd_target_err.txt`，HEAD 字节）：

```
靶子   GUARD hdr=B198 else=[B374,B420,B424,B544,B548] merge=- closure_then=[B48]/[B244]
              raise=True veto=True arm=B244 succs=[] arm_last=RAISE_VARARGS
              F=B374 else_pure=True else_succs=[420,424]
误伤   GUARD hdr=B168 else=[B202,B214,B590,...]        merge=- closure_then=[B172]
              raise=True veto=True arm=B172 succs=[] arm_last=RAISE_VARARGS
              F=B202 else_pure=True else_succs=[214,590]
```

两层在 header 臂（同为无后继 RAISE 终端块）、F 纯度、`merge_`（同为 None）上**完全相同**，
唯一同层可判别事实是 **F 自己的真臂（F 的条件后继中除尾跳转落点者）是否为终端 sink**
（复现上直接打印该事实，`logs/gd_repro_err.txt`）：

```
repro_01(丢文本) hdr=B106 F=B190 else_pure=True false_blk=B230 true_arm=B226
                       true_arm_last=RETURN_VALUE true_arm_sink=True      → 必须放行
repro_02(控制)   hdr=B0   F=B36  else_pure=True false_blk=B68  true_arm=B48
                       true_arm_last=POP_JUMP_FORWARD_IF_NOT_NONE true_arm_sink=False
                       （B48 后继 5,6；区域树里已有 IfRegion entry=B36）→ 必须保留否决
```

语义解释：F 的真臂 fallthrough ⇒ 双臂在链后汇合，把 F 并入链会把汇合语句抬出 `else` 体
（get_start_day 正是如此）；F 的真臂是 sink ⇒ 本层不存在汇合点，`if A: raise` + `if B: …`
与 `if A: raise / elif B: …` 码流同形，此时唯一约束是原则 2 的归属与文本完整性。

### 5.3 判据（写进 18144）

放行条件 = 既有 18141-18143 的同层形状识别 + 两条同层结构事实：

1. **纯度**：F=`else_blocks_[0]` 除尾条件跳转 `_fe_last` 外不携带自身语句
   ——opcode 集与本函数 18289 既有 `_has_body_stmt` 判据**同一份**，不是新造模式；
2. **无汇合点**：F 的真臂 `len(conditional_successors \ {get_block_by_offset(_fe_last.argval)}) == 1`
   且该臂 `not successors` 且末指令 `in ('RETURN_VALUE','RETURN_CONST','RAISE_VARARGS','RERAISE')`
   ——与本函数既有终端 sink 惯用法（18028/18074/18119）同一族 opcode。

只读 `header_`/`else_blocks_[0]`/其条件后继与这些块自身的末指令，不读函数名、不读源码文本、
不比绝对 offset、不看父/子区域顺序。

## 六、候选补丁（对当前工作树字节）

现场：`core/cfg/region_analyzer.py`，锚点原字节 18144-18145，纯插入 33 行（0 行删除），
补丁后文件 sha256[:16] `7a88adcedf5249ef → f5eccfb152dcc73f`，仍为纯 CRLF、无 BOM（已核对
`rawC.count(b'\n')==rawC.count(b'\r\n')`，且逐行 re-join 能字节还原）。

* r26a.py spec 格式：`D:/Temp/r27diagB/spec_c3a.json`（`anchor` 断言在文件中唯一，occurrences=1）
* unified diff：`D:/Temp/r27diagB/patch_c3a.diff`（由 `mkdiff27.py` 从 mirr_head/mirr_cand 真实字节生成，
  并已验证 anchor→repl 能字节还原 mirr_cand、`py_compile` 通过）

```
--- a/core/cfg/region_analyzer.py
+++ b/core/cfg/region_analyzer.py
@@ -18143,6 +18143,39 @@
                         if _fe_last and _fe_last.opname in (FORWARD_CONDITIONAL_JUMP_OPS | SHORT_CIRCUIT_JUMP_OPS):
                             if not _then_has_raise:
                                 _then_has_ctrl_exit = False
+                            # R27-A 区域归约算法原则 2（每块唯一归属）+ 原则 1（块 = 前导
+                            # 语句 + 尾跳转）：上一臂以 raise 终结不构成「下一条件块属于
+                            # else 体」的独占证据。仅当以下两个同层结构事实同时成立才放行：
+                            # (1) else 头 F 除尾条件跳转外不携带自身语句（纯条件块，opcode 集
+                            #     与本函数 18289 既有 `_has_body_stmt` 判据同一份）。F 没有语句化
+                            #     表示：链中止后它落入链尾扁平 `elif_final_else` 语句表，
+                            #     region_ast_generator._generate_block_statements 对其发射 0 条
+                            #     （44175→44262 实测），条件文本永久丢失，其臂退化为无条件语句，
+                            #     兄弟语句被 3.11 编译器当死代码消除
+                            #     （IQEngine/plugin_system_persist.can_resume_strategy B374，89→57）；
+                            # (2) F 的真臂（F 的条件后继中除尾跳转落点者）无后继且以终端指令收尾
+                            #     ——本层没有汇合点，「上一臂 raise 后另起一条 if」与「并入 elif」
+                            #     码流同形；反之若 F 的真臂 fallthrough，双臂在链后汇合，并入会把
+                            #     汇合语句抬出 else 体（实测踩坑：fly/tradingday_calendar
+                            #     .get_start_day 的 `if type == 'daily'`）。
+                            # 带前导语句的块（靶子 B424）仍由本函数 18340 的同一纯度判据终止扩展。
+                            elif not any(
+                                    _r27_i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
+                                                      'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR',
+                                                      'BINARY_OP', 'DELETE_NAME', 'DELETE_FAST',
+                                                      'DELETE_GLOBAL', 'DELETE_ATTR', 'DELETE_SUBSCR')
+                                    for _r27_i in _first_else.instructions
+                                    if _r27_i.offset < _fe_last.offset):
+                                _r27_fb = (self.cfg.get_block_by_offset(_fe_last.argval)
+                                           if _fe_last.argval is not None else None)
+                                _r27_fa = [s for s in _first_else.conditional_successors
+                                           if s is not _r27_fb]
+                                if (len(_r27_fa) == 1 and not _r27_fa[0].successors
+                                        and _r27_fa[0].get_last_instruction() is not None
+                                        and _r27_fa[0].get_last_instruction().opname in
+                                            ('RETURN_VALUE', 'RETURN_CONST', 'RAISE_VARARGS',
+                                             'RERAISE')):
+                                    _then_has_ctrl_exit = False
                         # 反编译逻辑推导（elif降级修复·模式1）：
```

（`patch_c3a.diff` 是机器生成的权威版本；上面为可读副本。）

## 七、闸门（全部实测，均为**最终交付字节** `f5eccfb152dcc73f`）

复现对已落地：`F:/Downloads/pythoncdc-main/test_repros/round27_elif_double/`
（`r27b_01_elif_midchain_condition_drop.py/.pyc`、`r27b_02_control_rejoin_keeps_veto.py/.pyc`，
本轮 3.11.7 `py_compile` 现场编译；只新建文件，未触碰任何既有文件/索引/OK.py）。

| 闸 | 对象 | head（当前落地字节） | cand（R27-A） |
|---|---|---|---|
| G0 非空 | `r27b_01_elif_midchain_condition_drop.pyc::<module>.can_resume`（语料外合成） | 官方 2/3，`mism=[['can_resume',70,41,0,31]]`，strict `seq_len orig=70 decomp=41`，sha `a66879799a537eca` | — |
| G1 翻转 | 同上 | — | 官方 **3/3 `mism=[]`**，strict `ok 70/70`，sha `79ec5e7e90a68671` |
| G2 控制 | `r27b_02_control_rejoin_keeps_veto.pyc`（get_start_day 形状的语料外合成：guard raise + 双臂汇合） | 3/3，strict 全 ok（11/11、34/34、30/30），sha `72c41897c76130f8` | sha **相同** `72c41897c76130f8` |
| G2b 控制（语料） | `fly/common/tradingday_calendar.pyc::get_start_day` | strict ok 212/212、官方 28/28 | 同（C2 曾在此退化 `target_diff`，本版已消掉） |
| 靶子 | `IQEngine/plugins/plugin_system_persist/__init__.pyc::can_resume_strategy` | 官方 14/15，strict `seq_len 89→57` | 官方 **15/15**，strict **ok 89/89** ⇒ 该文件翻 OK |
| G3 锚定电池 | `batt92.txt`（round2/3/4 合成 92 文件，与 402 语料零交集） | 92/92 matched、无 error | 92 文件产物 sha **逐一相同**（sha-changed=[]），无 ERR、无 `total_functions==0`、无 OK→FAIL |
| G4 全语料 | `all402.txt` 402 文件双臂（402/402 记录，无 error、无 0 函数） | — | `{'SAME': 401, 'IMPROVED': 1, 'MOVED': 0, 'REGRESSION': 0, 'ERR': 0, 'MISSING': 0}`；IMPROVED=`plugin_system_persist/__init__.pyc 14/15->15/15 fixed=['can_resume_strategy']` |
| G4b 严格尺 | 402 文件中 sha 不同者（`strictab27.py`） | — | **仅 1 个函数变化**：`can_resume_strategy head=seq_len d=57 → cand=None d=89`；其余语料函数严格签名全同 |

日志：`logs/ab402_head_vs_cand_R27A.txt`、`logs/strict402_R27A.txt`、`logs/batt_head.txt`+
`logs/batt_cand.txt`、`logs/landed.jsonl`、`logs/rp_head.jsonl`+`logs/rp_cand.jsonl`。

## 八、已否证 / 残余风险

否证清单：
* `region_ast_generator.py:11156-11159`（本轮禁用的旧 11145-11147 现场）——打戳无 `RET 11159`，
  在靶子与复现上均不触发（§3.3）。
* 「发射路径漏发 / 区域建好但块被标记已生成」——否证：不存在以 B374 为 entry 的区域
  （`_build_elif_region(B374,…)` 因下一级 B424 带前导语句在 18340 返回 None），
  生成器无从委托；文本丢失发生在扁平 `elif_final_else` 语句化处（§3.3）。
* 「在 18144 无条件放行」（C1）与「仅纯度放行」（C2）——C2 被严格尺抓到 `get_start_day` 真退化（§5.1）。
* 「修 staleness：把 `_then_has_raise` 改读当前层前一臂」——否证：靶子失败层的**当前层**前一臂
  B244 本身就是 RAISE 终端块（`closure_then=[B244]` 那一条戳），改读后 `_then_has_raise` 仍为 True，
  否决照旧；staleness 只是同一条戳里的旁证，不是阻断因。
* 第二个见证 `plugin_fly_data/strategy.pyc::tick_worker_thread`（268/247）**不是本现场**：
  它在 `region_analyzer.py:18860`（`if not _d2_terminal: return None`）中止（`logs/probe_tick_err.txt`），
  R27-A 后该文件仍 23/24、产物 sha 与 head 相同 ⇒ 另案。

残余风险：
1. 判据 (2) 要求 F 的真臂**单个**条件后继且为 sink；若某函数 F 有两个真臂后继（嵌套布尔短路形状），
   本判据保守不放行 → 保持 head 行为（不引入退化，但同类丢文本不修）。
2. `_fe_last.argval` 解析失败（后向跳转/None）时 `_r27_fb=None ⇒ len(_r27_fa)!=1` → 不放行，保守。
3. RERAISE 加入终端集是沿用本文件既有多处同一组合（168 处出现），非新造。
4. 靶子文件仍只有 1 个函数变化；语料内没有第二例同形正例，泛化证据只有合成复现 + 严格尺零退化。
5. 与 R26-A（`region_ast_generator.py:10084-10097`）正交：`plugin_fly_data/__init__.pyc` 20/20 双臂相同。
