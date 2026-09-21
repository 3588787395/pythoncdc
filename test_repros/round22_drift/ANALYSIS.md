# Round 22 诊断电池 —— 漂移族 **J1′ / J2′ / J3′** 的最小复现集（37 项）

角色：Round 22 TEST/DIAGNOSIS（测试工程师）。**只诊断、只出复现，不改 `core/`**。
所有测量都在**仓库外镜像核**上做；仓库内唯一写入目录 = `test_repros/round22_drift/`。

被测三条候选规则（由诊断线给出、已在镜像上语料级验证，本电池负责把它们逐条钉到最小形状）：

| 规则 | 文件 / 站点（46e752ab 行号） | 一句话 |
|---|---|---|
| **J1′** | `core/cfg/region_analyzer.py::_identify_conditional_regions`，R13c 汇点塌缩（base 行 17132） | 给 `merge = else_succ` 加两条同层前置条件：(a) 臂入口与 `else_succ` 的最内层 enclosing loop 同一个；(b) 臂内裸 `return None` 块 且 `else_succ` 直接后继也是裸 `return None` 块 ⇒ 禁止塌缩 |
| **J2′** | `core/cfg/region_ast_generator.py::_discover_predicate_and_chain`（base 行 16360，`return {'blocks': chain, 'op': 'and'}` 之前） | and 链首块若是**另一个纯操作数块**前向条件跳转的落点 ⇒ 本链只是 `X or <链>` 的末析取支，拒绝以它重建整个 test |
| **J3′** | `core/cfg/region_ast_generator.py::_is_orphan_boundary_nop`（base 行 41230-41237） | 纯删除 `[A4/V-M]` 子句：该子句以「全 CFG 里任何一条条件跳转指向本边界 NOP」为由拒绝折叠 —— 一个跨区域的全局判据 |

---

## 0. 环境与纪律（复现必需）

| 项 | 值 |
|---|---|
| 解释器 | `D:/Python/python.exe` = CPython 3.11.9；每条命令前缀 `PYTHONIOENCODING=utf-8` |
| before 镜像（只读） | `D:/Temp/r23prep/mirror/base` —— 钉住 `core` = `46e752ab`，含三个缺陷 |
| after 镜像（只读） | `D:/Temp/r23prep/mirror/j123` —— base + J1′+J2′+J3′ 三块候选补丁 |
| 单补丁镜像 | `j1g`（J1′ 两条款）/ `j2p`（仅 J2′）/ `j3`（仅 J3′）/ `j13`；均在 `D:/Temp/r23prep/mirror/` |
| 条款拆分镜像（本电池自建） | `D:/Temp/r22batt/mirror/j1a`（仅 J1′(a)）/ `j1b`（仅 J1′(b)）；插桩镜像 `j1log`（行为与 base 相同，在 R13c 站点打印判据） |
| 镜像重建 | `D:/Python/python.exe D:/Temp/r23prep/probes/mk.py <名字>`（缺目录时 `run_all.py` 会打印该提示） |
| 尺子 | 只用**被测镜像自带**的 `_r10_strict_check.strict_compare`（NOISE={NOP,CACHE,PRECALL,EXTENDED_ARG}；非跳转指令逐位同；跳转按方向归一 + 无条件跳转桩尾随；`kind is None` ⇒ 一致） |
| 构建产物 | `D:/Temp/r22batt/battery/`（复现源副本、`.pyc`、`*_DECOMP.py`）；杂项 `D:/Temp/r22batt/out/`。**仓库内零写入** |
| 禁止且已遵守 | 未读写工作树 `core/`、`bytecode/`、`pycdc.py`、`pyc_index.json`、`scripts/`、`.trae/`、`tasks.md`、任何 `*OK.py`；未跑 `scripts/pyc_batch_verify.py`；无任何 git 写操作；未进入 `test_repros/round22_adoption/`；全程串行（2 核机器，从不并发两个语料扫描） |
| 仓库内唯一写入 | `F:/Downloads/pythoncdc-main/test_repros/round22_drift/`（37 个复现 + `run_all.py` + 本文件） |

一个容易踩的坑（已在 `run_all.py` 里处理）：worker 子进程的 `cwd` **必须是构建目录**，不能是仓库根，否则工作树的 `core/`、`bytecode/`、`pycdc.py` 会抢在镜像之前被 `import`，测的就不是镜像了。

探针（都在 `D:/Temp/r22batt/`，输出在 `out/`）：
`cab.py`（语料逐函数多核 A/B，`--cores --idx`）、`disfn.py`（带偏移反汇编，NOISE 标注）、
`logsrc.py`/`logrun.py`（把复现喂给 `j1log` 插桩镜像，抓 R13C 站点判据实测值）、
`prod.py`（两个镜像核产物 unified diff）、`mk1.py`/`mk2.py`（条款拆分与插桩镜像构造，注意 `core/*.py` 是 CRLF，锚点必须按 CRLF 匹配）。

---

## 1. 起点症状（语料侧，本轮重测）

`python D:/Temp/r22batt/cab.py --cores base,j123 --idx 297,360,367,376,232`（≈ 5.5 s，串行）：

| pyc | 函数 | base strict | j123 |
|---|---|---|---|
| `IQEngine/plugins/plugin_system_persist/json_persistance.pyc` | `<module>.JsonPersistance.persist` | `seq_len orig=78 decomp=76` | **ok** |
| `IQEngine/plugins/plugin_fly_data/__init__.pyc` | `<module>.ApiMethodPlugin.resist_api` | `seq_len orig=107 decomp=105` | **ok** |
| `fly/common/flytools.pyc` | `<module>.get_mem_under_oom_status` | `seq_len orig=47 decomp=18` | **ok** |
| `fly/common/flytools.pyc` | `<module>.whitelist_filter` | `seq_len orig=116 decomp=114` | **ok** |
| `fly/common/market_time.pyc` | `<module>.MarketTime.trade_is_open` | `seq_len orig=97 decomp=89` | **ok** |
| `fly/data/quote_handler.pyc` | `get_all_fundamentals_daily` / `get_all_valuation` / `get_all_valuation_new` | 各 `seq_len orig=73 decomp=71` | **ok ×3** |
| `IQCommon/api/klinedata.pyc` | `<module>.np_tp_pd` / `<module>.to_pd_result` | `169→167` / `185→183` | **ok ×2** |
| `IQCommon/util/common_func.pyc` | `<module>.to_pd_result` | `seq_len orig=185 decomp=183` | **ok** |
| `IQData/plugins/plugin_system_realquote/real_quote.pyc` | `RealQuoteData.get_real_daily_kline` | `210→212`（过量发射） | **ok** |
| 同上 | `RealQuoteData.get_real_minute_kline_bk` | `169→171`（过量发射） | **ok** |

⇒ **13 个函数** base 错、三补丁合起来对。同批探测里 **没有任何函数从 ok 变成 MISMATCH**（9 个文件、逐函数判决全表在 `D:/Temp/r22batt/out/corpus_*.json`）。

两处需要写进风险簿的变化（都不是新 MISMATCH，两世界都仍错）：

```
376 <module>.get_kline_local       base=760→676 | j2p=760→682 | j123=760→682   （J2′ 让它靠近 6 条，仍未修好）
71  IQData/api/api_base.pyc
    <module>.get_history_df        base=1742→1722 | j2p=1742→1718 | j123=1742→1718 （J2′ 过火，距离恶化 −20→−24）
```

后一条是**严格尺子二元判决看不见**的恶化（两世界都 MISMATCH ⇒ 官方/严格门禁全绿），记入 §8/§10。

---

## 2. 指令级判决（真实反汇编，偏移为 3.11.9 实测）

### 2.1 J1′(a) —— 复现 `r22_01`（语料原型 `get_mem_under_oom_status` 47→18）

```
O0      RESUME
O2      BUILD_MAP / STORE_FAST d
O8      LOAD_FAST x / LOAD_CONST '' / COMPARE_OP ==
O14     POP_JUMP_FORWARD_IF_FALSE      to 22      # if x == '':
O16     LOAD_FAST d
O18     RETURN_VALUE                              #     return d        ← 臂（汇点）
O22     LOAD_GLOBAL list / LOAD_FAST ys / CALL / STORE_FAST zs   ← else_succ：普通语句
O38     LOAD_FAST zs / GET_ITER
O42     FOR_ITER ...
```

`else_succ(22)` 是 **本 if 之后的一条独立语句**（随后进入 for 循环头），不是 merge；
把它当 merge ⇒ 区域归约把 22 之后全部语句判给 then 臂，产物里 `zs=list(ys)`、整个
`for` 循环、`return d` 一起消失（`orig=28 decomp=11`）。base 产物实测（`prod.py` 对拉）：

```
     if x == '':
         return d
-    return d                                      # ← base：中间整段被吸进已 return 的臂里
+    else:                                         # ← after：还原为 else 臂
+        zs = list(ys)
+        for z in zs:
+            if z:
+                d['a'] = 1
+                break
+        return d
```

插桩镜像对本复现的实测行（`j1log`）：

```
R13C cond=?@0[...] then=18 else_succ=22 succs=?@56[FOR_ITER:] same_loop=False shared_rn=False arm_sink=True ELSEISCOND=False
R13C   ==> WOULD COLLAPSE same_loop=False shared_rn=False
```

语料同站点（`flytools.pyc get_mem_under_oom_status`）同形：`then=54 else_succ=58 succs=?@140[FOR_ITER] same_loop=False`。

### 2.2 J1′(b) —— 复现 `r22_05`（语料原型 `json_persistance.persist` 78→76）

```
O4      LOAD_FAST d / BUILD_MAP / COMPARE_OP !=
O14     POP_JUMP_FORWARD_IF_FALSE      to 54      # if d != {}:
O16     LOAD_FAST c
O18     POP_JUMP_FORWARD_IF_FALSE      to 50      #     if c:
O20     LOAD_GLOBAL NULL+print / LOAD_CONST 1 / PRECALL / CALL / POP_TOP
O50     LOAD_CONST None / RETURN_VALUE            # ← then_blocks 末块：裸 return None
O54     LOAD_GLOBAL sys.stdout.write('empty') …   # ← else_succ：普通语句
O116    LOAD_CONST None / RETURN_VALUE            # ← else_succ 的直接后继：函数级隐式 return None
```

插桩实测：

```
R13C cond=?@4[...] then=16,20,50 else_succ=54 succs=?@116[LOAD_CONST RETURN_VALUE],?@120[PUSH_EXC_INFO …] same_loop=True shared_rn=True arm_sink=True ELSEISCOND=False
R13C   ==> WOULD COLLAPSE same_loop=True shared_rn=True
```

`same_loop=True` ⇒ (a) 在此完全不起作用（语料 persist 亦然：`same_loop=True`），
塌缩之所以错，是因为臂的「汇点」性只是**函数级隐式 `return None`**，两臂汇聚到同一个
隐式出口，塌缩后 else 侧语句被吸进 then 臂（产物把 `sys.stdout.write('empty')` 提到 if 里面）。

### 2.3 J1′ 两条前置条件同时命中的形 —— 复现 `r22_04`

```
R13C cond=?@4[...] then=8,12,14,48 else_succ=52 succs=?@114[LOAD_CONST RETURN_VALUE],?@118[PUSH_EXC_INFO …] same_loop=False shared_rn=True
R13C   ==> WOULD COLLAPSE same_loop=False shared_rn=True
```

### 2.4 J2′ —— 复现 `r22_12`（语料原型 `MarketTime.trade_is_open` 97→89）

```
O2      LOAD_FAST hhmm / LOAD_CONST '0915' / COMPARE_OP >=
O12     POP_JUMP_FORWARD_IF_FALSE      to 26      # ← 纯操作数块的前向条件跳转
O14     LOAD_FAST hhmm / LOAD_CONST '1130' / COMPARE_OP <=
O24     POP_JUMP_FORWARD_IF_TRUE       to 50      # ← or 短路（真值直达 then）
O26     LOAD_FAST hhmm / LOAD_CONST '1300' / COMPARE_OP >=     ← and 链首 = O12 的落点
O36     POP_JUMP_FORWARD_IF_FALSE      to 54
O38     … '1515' / COMPARE_OP <=
O48     POP_JUMP_FORWARD_IF_FALSE      to 54
O50     LOAD_CONST True / RETURN_VALUE
O54     LOAD_CONST False / RETURN_VALUE
```

base 以 O26 起的那条 and 链重建整个 test，左析取支整体丢失，实测产物：

```
-        if hhmm >= '1300' and hhmm <= '1515':                     # base
+        if hhmm >= '0915' and hhmm <= '1130' or hhmm >= '1300' and hhmm <= '1515':   # after
```

语料同形（`D:/Temp/r22batt/tio_base.txt` 第 5 行）：base 产物正是
`if current_dt >= '1300' and current_dt <= '1515':`，丢了 `>= '0915' and <= '1130' or`。

### 2.5 J3′ —— 复现 `r22_28`（语料原型 `whitelist_filter` 116→114）

```
O50     LOAD_FAST mode / LOAD_CONST 2 / COMPARE_OP ==
O60     POP_JUMP_FORWARD_IF_FALSE      to 98      # elif mode == 2: 的 false 路径
O62     …（mode==2 臂体）
O96     JUMP_FORWARD                   to 100     # ← base 产物重编译后少掉的就是这一条
O98     NOP                             ← `else: pass` 的语句边界锚点（本链自己的条件跳转落点）
O100    LOAD_GLOBAL NULL+print / LOAD_CONST 'tail' …
```

`_is_orphan_boundary_nop` 的 `[A4/V-M]` 子句扫**全 CFG**，只要有任何条件跳转 `argval == nop_off`
就 `return False`。这里指向 O98 的正是**本 elif 链自己**在 O60 发出的那条跳转 ——
它是「由外层条件结构自动再生」的边界锚点，本该折叠。拒绝折叠 ⇒ `else: pass` 臂不还原 ⇒
产物重编译后缺 `JUMP_FORWARD`，`orig=29 decomp=28`；语料 `whitelist_filter` 是两条链 ⇒ `116→114`。
after 产物补回的是：

```
+    else:
+        while False:
+            pass
```

---

## 3. 真源码形状重建

三个站点在**真源码**里的对应形状（也就是本电池锚点反复使用的四种形）：

```
J1′(a)                            J1′(b)
if A:                             try:
    return v                          if A:
<普通语句>          ← 不是 else!            if B: <语句>
for x in xs: …                            return          # 臂内裸 return None
                                      <普通语句>           # 其后又是隐式 return None
                                  except BaseException: …

J2′                               J3′
if A and B or C and D:            if m == 1: <语句>
    <语句>                          elif m == 2: <语句>
                                    else: pass            # ← 边界 NOP 所在臂
                                    <尾随语句>
```

同层原则读法：J1′(a) 问的是「`else_succ` 与臂是否处在**同一层循环作用域**」；
J1′(b) 问的是「臂的汇点是不是**函数级隐式出口**」；J2′ 问的是「and 链首是否为**别人的短路落点**」；
J3′ 问的是「这条边界 NOP 是不是**本结构自己的**折叠残留」。四者都是同层/同结构判据，
不需要跨区域启发式；base 的四处缺的正是这个「同层」限定。

---

## 4. 根因与站点代码（J1′）

base `core/cfg/region_analyzer.py` 行 17125-17136：

```
                _25b_else_is_cond = (len(else_succ.conditional_successors) == 2
                    and _25b_else_last is not None
                    and _25b_else_last.opname in FORWARD_CONDITIONAL_JUMP_OPS)
                if not _25b_else_is_cond and self._if_arm_is_sink(then_blocks, then_stop):
                    merge = else_succ                                  # ← R13c 无条件塌缩
```

`j123` 里实际接线（diff 实测，`+17129,7 → +17129,23`）：

```
                _25b_arm_loop  = self._find_enclosing_loop(then_blocks[0])
                _25b_else_loop = self._find_enclosing_loop(else_succ)
                _25b_same_loop = _25b_arm_loop is _25b_else_loop
                _25b_shared_rn = (any(self._is_return_none_block(b) for b in then_blocks)
                                  and any(self._is_return_none_block(s)
                                          for s in else_succ.successors))
                if (not _25b_else_is_cond and _25b_same_loop and not _25b_shared_rn
                        and self._if_arm_is_sink(then_blocks, then_stop)):
```

**条款级归因（语料，7 个世界逐函数 A/B 实测）**

| 语料函数 | base | j1a(仅 a) | j1b(仅 b) | j1g(a+b) | j2p | j3 | j123 |
|---|---|---|---|---|---|---|---|
| `ApiMethodPlugin.resist_api` | 107→105 | **ok** | 107→105 | **ok** | 107→105 | 107→105 | **ok** |
| `get_mem_under_oom_status` | 47→18 | **ok** | 47→18 | **ok** | 47→18 | 47→18 | **ok** |
| `get_all_fundamentals_daily` | 73→71 | **ok** | 73→71 | **ok** | 73→71 | 73→71 | **ok** |
| `get_all_valuation` | 73→71 | **ok** | 73→71 | **ok** | 73→71 | 73→71 | **ok** |
| `get_all_valuation_new` | 73→71 | **ok** | 73→71 | **ok** | 73→71 | 73→71 | **ok** |
| `JsonPersistance.persist` | 78→76 | 78→76 | **ok** | **ok** | 78→76 | 78→76 | **ok** |

⇒ 两个条款**语料层面互不冗余**：J1′ 的 6 个语料受害者里 (a) 覆盖 5 个（全部 `same_loop=False`），
(b) 只覆盖 persist 一个（`same_loop=True`）。
本电池的 `r22_04` 是两条款同时命中的重叠形（`j1a`、`j1b` 各自都能修）——留着它正是为了让
「冗余」这件事必须在门禁里显式出现，而不是靠读代码默认它不存在。

**复现层面同表**（`--single --after D:/Temp/r22batt/mirror/j1a|j1b`）：01/02/03 = 仅 (a)；
04 = (a) 与 (b) 各自单独可修；05 = 仅 (b)（`j1a` 仍 `MISMATCH 39→37`）。

## 5. 根因与站点代码（J2′）

base `region_ast_generator.py` 行 16340-16362（`_discover_predicate_and_chain` 尾部）：
链扩展循环结束、`if len(chain) < 2: return None` 之后**无条件** `return {'blocks': chain, 'op': 'and'}`。
`_collect_boolop_operands_from_condition` 的调用点（base 行 22435-22438）把整个 test 交给这条链，
于是 `X or <链>` 只剩 `<链>`。`j123` 在 return 之前插入（实测 diff `+16360,6 → +16360,22`）：

```
        _head = chain[0]
        for _pj in _head.predecessors:
            if _pj in chain or _pj.start_offset >= _head.start_offset:
                continue
            _pl = _pj.get_last_instruction()
            if (_pl is not None and _pl.argval is not None
                    and _pl.argval == _head.start_offset
                    and _pl.opname in FORWARD_CONDITIONAL_JUMP_OPS
                    and self._chain_block_is_pure(_pj)):
                return None
```

`return None` 是**只删不增**：不重建 and 链，交回既有单条件/嵌套路径。语料与复现一致：
`trade_is_open` 仅 `j2p` 可修（97→89 → ok），`get_history_df` 也仅 `j2p` 受影响（−20→−24）。

## 6. 根因与站点代码（J3′）

base `region_ast_generator.py` 行 41230-41237（`_is_orphan_boundary_nop` 的 `[A4/V-M]` 子句）：

```
                # [A4/V-M] 条件跳转以本 NOP 自身为汇合目标（argval == nop_off）：
                if (bi2.opname in CONDITIONAL_JUMP_OPS
                        and getattr(bi2, 'argval', None) == nop_off):
                    return False
```

它位于 `for blk in self.cfg.get_blocks_in_order()` 的**全 CFG 扫描**里 ⇒ 判据没有区域归属信息：
指向该 NOP 的条件跳转可以来自完全无关的另一个区域（本例就是本结构自己的 elif 跳转）。
J3′ = 纯删除该 8 行（5 行注释 + 3 行判据；diff `41227,14 → 41243,6`）。
语料 `whitelist_filter` 仅 `j3` 可修（116→114 → ok）。逐指令对拉确认本复现丢的就是尾跳转
（`base 29→28`、`j123 29→29`）：

```
O94   POP_TOP
- O96   JUMP_FORWARD to 100      ← orig（mode==2 臂尾：跳过 else 臂）
+ O96   LOAD_GLOBAL NULL+print   ← base 产物（else 臂不存在 ⇒ 臂尾直接落入 tail）
```

`[A4/V-M]` 原本要保护的对象由同函数内**其余**判据继续保护 —— 电池里 `r22_34..37` 四个 GUARD
（`if/else: pass` 尾随、`while False: pass`、try 内 `else: pass`、无 else 的 elif 链）在两世界都 MATCH。

---

## 7. 电池（37 项）实测

一条命令（全量 ≈ 2 s，远低于 120 s 预算）：

```
cd F:/Downloads/pythoncdc-main
PYTHONIOENCODING=utf-8 D:/Python/python.exe test_repros/round22_drift/run_all.py --show-defects
```

真值表：`FIX` = before 必须 MISMATCH、after 必须 MATCH；`GUARD` = 两世界必须 MATCH；
`RESIDUE` = 两世界必须 MISMATCH（被顺带修好 → `REVIVED` 仅告警；before 变 MATCH → `NEW-REGRESSION` 失败）。
实测汇总（`D:/Temp/r22batt/out/battery_attrib.txt` = 37 项 × 7 个单补丁世界全表）：

| # | 形状（目标函数） | 类别 | before | after | 单独可修的世界 |
|---|---|---|---|---|---|
| 01 | `if x=='': return d` + 其后 for 循环（`f`，28） | FIX | MISMATCH 28→11 | MATCH | j1a / j1g |
| 02 | if/else 两臂各一个 for（`f`，27） | FIX | MISMATCH 27→25 | MATCH | j1a / j1g |
| 03 | 同上但生成器（yield+continue，`f`，44） | FIX | MISMATCH 44→42 | MATCH | j1a / j1g |
| 04 | try 内臂 = for + 裸 `return None`（`f`，40） | FIX | MISMATCH 40→38 | MATCH | **j1a 与 j1b 都行** |
| 05 | try 内嵌套 if + 裸 `return None`（`f`，39） | FIX | MISMATCH 39→37 | MATCH | **仅 j1b** |
| 06 | for 内 `if y: return x` 合法塌缩（`f`，15） | GUARD | MATCH | MATCH | — |
| 07 | 嵌套循环分裂臂（`f`） | GUARD | MATCH | MATCH | — |
| 08 | 臂含 loop、else 侧普通语句（`f`） | GUARD | MATCH | MATCH | — |
| 09 | 普通 if/else 双臂（负例，`f`） | GUARD | MATCH | MATCH | — |
| 10 | `if a: return None` 后接调用（`f`） | GUARD | MATCH | MATCH | — |
| 11 | 语句后裸 `return None`（`f`） | GUARD | MATCH | MATCH | — |
| 12 | 语料原形 `A>=s and A<=e or A>=s2 and A<=e2`（`T.open`，21） | FIX | MISMATCH 21→13 | MATCH | 仅 j2p |
| 13 | 同形换数值参数（`f`，21） | FIX | MISMATCH 21→13 | MATCH | 仅 j2p |
| 14 | 最小形 `a and b or c and d` + print（`f`，15） | FIX | MISMATCH 15→11 | MATCH | 仅 j2p |
| 15 | 操作数含 `not in` / `in`（`f`，21） | FIX | MISMATCH 21→13 | MATCH | 仅 j2p |
| 16 | 三支 or `A and B or C and D or E and F`（`f`，17） | FIX | MISMATCH 17→9 | MATCH | 仅 j2p |
| 17 | and-or 臂内两语句 + 尾随（`f`，23） | FIX | MISMATCH 23→19 | MATCH | 仅 j2p |
| 18 | **负例：纯 `A and B` 必须照常重建**（`f`） | GUARD | MATCH | MATCH | — |
| 19 | 双臂嵌套 `and`（`f`） | GUARD | MATCH | MATCH | — |
| 20 | `elif A and B or C and D:`（`f`） | GUARD | MATCH | MATCH | — |
| 21 | `return A and B or C and D`（值位置，`f`） | GUARD | MATCH | MATCH | — |
| 22 | 前一条 if 之后接 `if a and b:`（`f`） | GUARD | MATCH | MATCH | — |
| 23 | `A and B or C`（单末支）（`f`，11） | RESIDUE | MISMATCH 11→13 | MISMATCH 11→13 | 无 |
| 24 | `A or (B and C)` 带括号（`f`） | RESIDUE | MISMATCH `target_diff #2` | 同左 | 无 |
| 25 | `while A and B or C and D:`（`f`，21） | RESIDUE | MISMATCH 21→3 | MISMATCH 21→3 | 无 |
| 26 | `A or B and C` 不带括号（`f`） | RESIDUE | MISMATCH `target_diff #2` | 同左 | 无 |
| 27 | persist 形搬进 while（`f`，73） | RESIDUE | MISMATCH 73→65 | MISMATCH 73→65 | 无 |
| 28 | 两条 elif 链各带 `else: pass`（`f`，29） | FIX | MISMATCH 29→28 | MATCH | 仅 j3 |
| 29 | 双 elif 链 else pass（whitelist 原形，`f`，53） | FIX | MISMATCH 53→52 | MATCH | 仅 j3 |
| 30 | 最简 elif + `else: pass` + 尾随（`f`，25） | FIX | MISMATCH 25→24 | MATCH | 仅 j3 |
| 31 | `else: pass` 在 for 体内（`f`，30） | FIX | MISMATCH 30→29 | MATCH | 仅 j3 |
| 32 | elif 臂内 BoolOp（与 J2′ 同函数共存，`f`，33） | FIX | MISMATCH 33→32 | MATCH | 仅 j3 |
| 33 | elif 链 + else pass 后再挂独立 if（`f`，33） | FIX | MISMATCH 33→32 | MATCH | 仅 j3 |
| 34 | `if/else: pass` + 尾随（`f`） | GUARD | MATCH | MATCH | — |
| 35 | `while False: pass`（`f`） | GUARD | MATCH | MATCH | — |
| 36 | try 内 `else: pass`（`f`） | GUARD | MATCH | MATCH | — |
| 37 | elif 链无 else（`f`） | GUARD | MATCH | MATCH | — |

电池门禁输出：

```
BATTERY :: repros=37  FIX=17/17  GUARD=15/15  RESIDUE=5/5  REVIVED=0  FAIL=0  ERROR=0
GATE: PASS        rc=0
```

三个交叉检验（都通过）：
① 每个 FIX 都能被**它自己那条规则**的单独镜像修好，且**只**被它修好（j2p 修不动 01-05/28-33，j3 修不动 12-17…）；
② 15 个 GUARD 在**全部 7 个世界**（base/j1a/j1b/j1g/j2p/j3/j123）都是 MATCH；
③ 5 个 RESIDUE 在全部世界都是 MISMATCH 且**缺陷签名逐字不变** ⇒ 没有被任何补丁顺带恶化。

## 8. 三规则与归约原则的张力（以及和规则描述不一致之处）

1. **J1′ 两条判据不是同一件事的两种写法。** 任务书把 J1′ 描述成一条规则的两次条件；
   实测在语料上它们**互斥地**覆盖 6 个受害者：(a) 管 5 个（全部 `same_loop=False`），
   (b) 只管 persist 一个（`same_loop=True`）。同时落地才有完整收益；若将来要拆开落地，
   必须知道单独落 (b) 会丢掉 5 个、单独落 (a) 会丢掉 persist。
2. **J2′ 的覆盖面比描述窄。** 任务书点名的 `X or (A and B)`（带括号，24）与 `X or A and B`
   （不带括号，26）在两世界都错，且错因是 **merge 块归属**（`target_diff`，跳转终点从
   `LOAD_CONST` 变成 `LOAD_FAST`），不是 and 链截断；`if A and B or C:`（末支是单条件，23）
   与 `while A and B or C and D:`（25，21→3）同样没被 J2′ 触及 —— 后者是**循环 test** 路径，
   `_discover_predicate_and_chain` 在这里根本没被调用（或另有兜底），仍过量发射 18 条。
   J2′ 只覆盖「if test + 末析取支本身是 and 链」。
3. **RESIDUE 不等于「语料干净」。** `run_all.py` 的 PASS-in-both 只说明该最小形状在两世界
   表现一致；语料里同名族缺陷可能照旧（例如 `market_time.MarketTime.is_open` 的
   `target_diff #27`、`flytools.FileLock.acquire 90→85`、`api_data.check_limit_common
   target_diff #154` 在**全部 7 个世界**逐字相同 —— 本轮实测确认，非猜测）。
4. **J3′ 的删除是纯减法，但保护面靠其余判据兜住。** `[A4/V-M]` 删掉后，四个 J3′ GUARD 无一
   松动；不过这条结论的强度只到「本电池 + 9 个语料文件」为止，全量 402 文件 A/B 不在测试
   工程师权限内（见 §9）。
5. **`get_kline_local`（760→676→682）的位移归因是 J2′，不是 J1′。** 早期诊断笔记把它记成
   J1′ 家族收益，本轮 7 世界实测：`j1a/j1b/j1g` 下仍是 676，只有 `j2p`（及 j123）变 682。

## 9. 门禁

| 门禁 | 命令 | 结果 |
|---|---|---|
| 电池（每形一条，双向） | `run_all.py --show-defects` | 37/37 分类正确，`GATE: PASS`，rc=0，**≈2 s** |
| 条款归因 | `run_all.py --single --after D:/Temp/r22batt/mirror/{j1a,j1b}` | 01-05 按 §4 表逐条命中 |
| 单规则归因 | `run_all.py --single --after .../{j1g,j2p,j3}` | 每个 FIX 只被自己的规则修好；GUARD/RESIDUE 全部不动 |
| 语料 spot A/B | `D:/Temp/r22batt/cab.py --cores base,j123 --idx 297,360,367,376,232`（+ `5,48,159,14,186,71`） | 13 修好、0 新 MISMATCH、1 距离恶化（`get_history_df`）、1 距离改善未修好（`get_kline_local`） |

自我约束（fail-closed 设计）：`run_all.py` 启动即做双向自检（文件集合 == 真值表键集合、类别合法、
复现数 ≥ 10），任一镜像目录缺 `pycdc.py`/`_r10_strict_check.py` 直接 `ENV FAIL`（退出码 2）并打印
`mk.py` 重建命令；门禁失败退出码 1；`REVIVED` 只告警（提示真值需重新基线）。
本电池**不做**全量 402 文件 A/B、**不跑** `scripts/pyc_batch_verify.py`、**不改** `pyc_index.json`
——那是落地/验收线的职责，此处只保证「每条规则的最小复现 + 不可破坏的守卫」可被一条命令重跑。

## 10. 未收口 / 诚实清单

1. **J2′ 语料过火未最小化。** `IQData/api/api_base.pyc <module>.get_history_df`
   （base `1742→1722`，`j2p`/`j123` `1742→1718`）：约 3 轮尝试（含 `if x: pass` 前置 +
   `if a and b:` 等 10 个过火探针）都得到「两世界 MATCH」，无法把该过火压成 ≤25 行复现。
   现状：只在 §1/§8 以语料数字登记，无电池项。落地前需要「同层细化」（任务 #31 的方向）。
2. **RESIDUE 族的真正根因未定位。** 23（末支单条件）、24/26（`X or (A and B)` 的 merge 归属）、
   25（while test 过量发射）、27（`while` 里的 persist 形：R13c 站点 `arm_sink=False`，
   插桩显示塌缩压根没发生 ⇒ 与 J1′ 无关）各属另一族，需要后续派单。
3. **`with` 语句在本环境不可用。** 3.11.9 的 `with` 在 `__exit__` 后多发一条 `JUMP_FORWARD`，
   与语料构建的字节码不同形，导致 persist 直接复刻版（`g1/g2/p1..p9` 共 11 个变体）在两世界
   都 MATCH、不具鉴别力；复现 05 改用同层嵌套 if 保持 O50/O116 两块裸 `return None` 的同构关系。
   这是**本机解释器版本**限制，不是规则限制；若换成语料构建的 3.11.x，05 可再缩一层。
4. **`MarketTime.is_open` `target_diff #27`** 七世界逐字相同，未收口。
5. **GUARD 的站点覆盖不均匀。** `r22_07/10/11` 在 `j1log` 下打印 **0 条 R13C 行** —— 它们根本不
   经过 R13c 站点，只能证明「该形状不被破坏」，不能证明「守卫判据在站点上被正确评估」。
   真正压站点判据的是 `r22_06`（`same_loop=True, shared_rn=False ⇒ 塌缩仍应发生`）与 `r22_04`。
6. **镜像漂移风险。** 本电池判决完全依赖 `D:/Temp/r23prep/mirror/*`；若 `base` 的钉住提交
   （`46e752ab`）变更，`run_all.py` 的 before 列即失效 —— 已通过 `_check_core()` 的
   `ENV FAIL` 提示（要求镜像含 `_r10_strict_check.py`）做最低限度防呆。
