# Round 65 · diag1 · FACTS（边测边写，全部为实测读数）

约定：`landed` = 仓库工作树 core（只读导入，`h62.py run --arm=landed`，写 `build_landed/`）。
所有官方读数用 `python -X utf8 h62.py run --arm=<arm> --list=<txt> --out=<jsonl>`，
A/B 用 `h62.py ab`。工作目录 `D:/Temp/opencode/r65gate/diag1`。
仓库文件零改动：唯一写动作是 `h62.py build`（它自带
`assert io.open(head,'rb').read() == io.open(_target(rel),'rb').read()`，即镜像必须与工作树字节相同，
本轮每次 build 都通过 ⇒ 工作树未被污染）。

## 0. 落地基线（复用主代理已跑的 dump/landed.jsonl + 本轮自跑 battery/canary）

```
landed realtime_event_source.pyc  11/12  [clock_worker, 1275, 1286, 10, 481]
landed matcher.pyc                 16/17  [match, 715, 715, 10, 517]
landed graph.pyc                   30/31  [_process_task_queue, 378, 378, 1, 118]
landed logger.pyc                  29/30  [write_logging_thread, 113, 113, 1, 40]
landed api_base.pyc                24/25  [get_history_df, 1742, 1719, 14, 1277]
```

canary 落地基线（4/4 全绿，sha 必须逐支不变）：
```
fly/data/quotation.pyc             143/143  sha=4d41187e356544e0
fly/common/market_time.pyc          10/10   sha=af77224b34b203c4
IQCommon/util/datetime_func.pyc     26/26   sha=e711b8ea86d49a15
IQData/utils/datetime_func.pyc      25/25   sha=9d09af09249da177
```

battery 落地基线（19 项，dump/battery_landed.jsonl；「不比落地差」= 逐行等于下表）：
```
r63_ft.pyc                            2/2   []
r63_ft2.pyc                           2/2   []
r63_ft4.pyc                           1/2   [['t4',31,22,1,23]]
probe_r63b2_cases.pyc                 7/9   [['c6_elif_try_then_more',50,50,1,15],['c8_elif_chain_only',31,33,1,15]]
probe_r63b2_cases2.pyc                7/9   [['d2_elif_notry',44,45,1,28],['d8_elif_try_chain_or_plain',51,50,1,6]]
repro_r63b2_tail_cmp_return.pyc       2/2   []
r63b3_chained_value_ctx_prefix.pyc    2/2   []
r63b4_tern_in_elif_chain.pyc          3/3   []
r63b5_w1.pyc                          1/2   [['init_connection',42,41,0,25]]
r63b3_chainstore_prefix.pyc           2/2   []
r63b4_cond_boolop_stmt_steal.pyc     13/13  []
r64d1b_closed_exit_prefix.pyc         2/2   []
r64d1b_sibdispatch_attempt.pyc        4/4   []
r64d2_chain_yield_sibling_entry.pyc   2/2   []
r64d2_valuectx_consumer.pyc           2/2   []
r64d3_postif_join.pyc                 2/2   []
r64d4_boolop_poptop_merge.pyc         3/3   []
r64d4_deferred_prefix.pyc             3/3   []
r64d5_contsink.pyc                    1/2   [['probe',122,122,1,9]]
```
注：`r64d5_contsink.pyc::probe` 是 SAME-LEN + jumpdiff=1，与 graph/logger 同族残余（落地即带病），
所以任何候选在电池上允许它保持 1/2，不能变得更差。

## 1. graph.pyc :: _process_task_queue（30/31 → 目标 31/31）

### 1.1 指令级清单（`align.py` 原始尺，含跳转目标噪声）
`python -X utf8 align.py .../IQCommon/graph.pyc build_landed/IQCommon__graphOK.py _process_task_queue`
→ `orig=421 decomp=421 ratio=0.9620`，14 个 hunk，其中 **11 个是噪声**：
- 3 个 `LOAD_CONST <code object <listcomp> ...>`：嵌套 code object 的 repr 里带文件名/行号，必然不同；
- 8 个 `POP_JUMP_*` / `JUMP_FORWARD`：只是目标偏移整体 ±2 平移。

把跳转目标归一（`JUMP*` 一律记成 `'J'`）、嵌套 code object 常量记成 `'CODEOBJ'` 后，
**实质缺陷只剩 3 个 hunk**（可复放命令见 §1.3）：

| # | orig | decomp | 内容 |
|---|------|--------|------|
| 1 | `[133:135]@566` = `LOAD_CONST None ; RETURN_VALUE` | `[133:134]@566` = `JUMP_FORWARD` | try 体末尾的 `return None` 变成跳到尾部 |
| 2 | `[197:197]`（无） | `[196:198]@842` = `LOAD_CONST None ; RETURN_VALUE` | 上面那对被搬到 842 |
| 3 | `[262:264]@1114` = `LOAD_CONST None ; RETURN_VALUE` | `[263:264]@1116` = `JUMP_FORWARD` | 第二处同样形态 |

即：**两个「try 体末条 `return None`」在产物里被发射到 try/except 语句之后**，
重编后该位置变成 `JUMP_FORWARD` 到一个搬后的 `LOAD_CONST None; RETURN_VALUE` 尾部。
官方 jumpdiff=1 / true=118 就是这一件事（+ 它的平移连锁）。

### 1.2 归因（落地字节行号 + 区域字段实测）
`python -X utf8 regdump.py .../graph.pyc _process_task_queue`：61 块 / 17 区域，
```
IfRegion@0  children=[Region@0, Region@16, TryExceptRegion@18, Region@566, IfRegion@844, Region@1272, TryExceptRegion@1274]
IfRegion@844 children=[Region@844, Region@888, TryExceptRegion@890, Region@1114]
```
`python -X utf8 logs/probe_posttry.py .../graph.pyc _process_task_queue`（新写的只读探针）：
```
TRY@36   try_end=114  handlers=[116]  post_try=[]   body_tail=['Assign','Expr','Assign','Assign']
TRY@242  try_end=382  handlers=[386]  post_try=[]   body_tail=[...,'Return']
TRY@18   try_end=566  handlers=[570]  post_try=[]   body_tail=['Assign','Try','Try']
TRY@908  try_end=986  handlers=[990]  post_try=[]   body_tail=[...,'Return']
TRY@890  try_end=1114 handlers=[1118] post_try=[]   body_tail=['Assign','Try']
TRY@1274 try_end=1618 handlers=[1618] post_try=[]   body_tail=['Assign','Try']
ALL REGIONS with has_trailing_return_none:
   Region entry=566  parent=IfRegion@0    blocks=[566]     ← 无后继，指令 = LOAD_CONST None; RETURN_VALUE
   Region entry=1114 parent=IfRegion@844  blocks=[1114]    ← 同上
```
关键同层次事实（都由本层区域字段给出，不需要跨层比较）：
- `Region@566.parent is TryExceptRegion@18.parent is IfRegion@0`（同层兄弟），且
  `TryExceptRegion@18.try_offset_end == 566 < min(handler_entry_blocks)==570`；
- `Region@1114.parent is TryExceptRegion@890.parent is IfRegion@844`，且
  `TryExceptRegion@890.try_offset_end == 1114 < 1118`；
- 反例自洽：`TRY@1274 try_end==handler==1618`（不满足 `<`），`TRY@36/@242/@908` 的
  `try_offset_end` 处是结构化块（`block 382/114/986` 属于 try_blocks），**不存在** BASIC 单块兄弟区域，
  所以判据在本支只命中 566 与 1114 两处。
- `post_try=[]` 证明两处都**不是** `_post_try_blocks_r19n2`（`region_ast_generator.py` L25247）走的；
  site1 的 `return None`（产物 `build_landed/IQCommon__graphOK.py` L399）是父层 IfRegion 兄弟序列发射的，
  site2 的 `Region@1114` 则**完全没有被发射**（产物 L419 之后直接是 L420 的 `try:`）。
  即同一根因的两种症状：兄弟槽多发射 / 该块丢失。

### 1.3 合成复现（可 20 秒复放，不是编造）
直接在落地产物上做**源码级**手术并重新编译，与原始 code object 比对（跳转目标/嵌套常量归一）：
```bash
cd D:/Temp/opencode/r65gate/diag1
python -X utf8 -c "<§1.3 脚本>"      # 见 logs/ 与下方读数
```
| 变异（行号是 `build_landed/IQCommon__graphOK.py` 的原始行号） | len | 残余 hunk |
|---|---|---|
| 无（as-is） | 421 | 3 |
| drop 399 | 420 | 1（@1114） |
| drop 419 | 420 | 4 |
| drop 433 / drop 439 | 421 | 3 |
| drop 399 + drop 419 | 419 | 2 |
| drop 399 + 在 413 后插入 `return None`(缩进20) | **421** | **0** ✅ |
| drop 399 + 在 388 后插 `return None`(16) + 在 413 后插(20)（= 统一「搬进 try 体」） | **421** | **0** ✅ |
| 只在 388 后插(16) + 413 后插(20)（保留 399/419，纯「追加」） | **421** | **0** ✅ |

⇒ 正确源形态是 `return None` 作为 **try 体的最后一条语句**（CPython 把它发射在保护跨度之外、
handler 之前）；三种手术都归零，说明「把体尾 return-none 终止块并进 try 体」这个归约方向是充分的。
候选 A 取最保守的实现：只在 `ast.Try.body` 末尾追加，并把该块标为已生成（抑制父层兄弟发射）。

### 1.4 候选 A = `specs/cand_r65_trytail.json`（generator 单文件，1 edit）
落地字节锚点 = `region_ast_generator.py` L26395-26401（`if _post_try_stmts_r19n2:` … `return try_ast`），
在 LF 归一文本里 `count==1`（实测），插入点在 `_generate_try` 的收尾处。
判据三要素（识别条件/归约方式/AST 映射）已写进补丁注释。
**不需要成对改 analyzer**：analyzer 已经把该块归约成带 `has_trailing_return_none` 的同层 BASIC 兄弟区域
（`region_analyzer.py` L26876–26894 的兜底归约 + L7463 `_is_return_none_block`），
信息都在字段里，缺的只是发射层的接收者 ⇒ generator-only 单文件候选。
落地后建议把 `synth/r65_trytail_w.pyc` 收进电池（它在落地上 7/8、在候选上 8/8，是唯一能区分本形状的合成语料）。

### 1.5 候选 A 读数（已实测，全部 `python -X utf8`，逐条可复放）

```bash
cd D:/Temp/opencode/r65gate/diag1
python -X utf8 h62.py build --spec=specs/cand_r65_trytail.json --dst=trytail
python -X utf8 h62.py run --arm=trytail --list=targets.txt  --out=dump/trytail.jsonl
python -X utf8 h62.py run --arm=trytail --list=battery.txt  --out=dump/battery_trytail.jsonl
python -X utf8 h62.py run --arm=trytail --list=canary.txt   --out=dump/canary_trytail.jsonl
python -X utf8 h62.py ab --a=dump/landed.jsonl           --b=dump/trytail.jsonl
python -X utf8 h62.py ab --a=dump/battery_landed.jsonl   --b=dump/battery_trytail.jsonl
python -X utf8 h62.py ab --a=dump/canary_landed.jsonl    --b=dump/canary_trytail.jsonl
python -X utf8 cstrict.py build_trytail targets.txt dump/trytail_strict.json
# 额外：全语料 398 支（site-packages 去掉 targets/canary/battery）
python -X utf8 h62.py run --arm=landed  --list=wide_all.txt --out=dump/wide_landed.jsonl  --nshard=6 --shard=0..5
python -X utf8 h62.py run --arm=trytail --list=wide_all.txt --out=dump/wide_trytail.jsonl --nshard=2 --shard=0..1
python -X utf8 h62.py ab --a=dump/wide_landed.jsonl --b=dump/wide_trytail.jsonl
```

| 组 | 落地 | 候选 A | `h62.py ab` |
|---|---|---|---|
| targets 5 支 | graph 30/31，其余 4 支各差 1 | **graph 31/31 `mism=[]`**，其余逐字节同 | `IMPROVED graph.pyc 30/31 -> 31/31`；`TALLY SAME=4 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`；`files fully matched: a=0 b=1` |
| battery 19 支 | 见 §0 | 19 支 sha 全部不变 | `TALLY SAME=19 … REGRESSION=0 MOVED=0`；`files fully matched a=14 b=14` |
| canary 4 支 | 4/4 全绿 | sha 逐支不变（`4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177`） | `TALLY SAME=4` |
| **全语料 398 支** | 381 支 full-matched | **sha 398/398 全等，0 变化** | `TALLY SAME=398 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`；`files fully matched: a=381 b=381` |
| 严格尺 `cstrict.py` | graph **33/34**（`#119 orig=('None','LOAD_CONST') decomp=('<JUMP>','JUMP')`） | graph **34/34 `missing=0 extra=0`** | 其余 4 支严格尺读数与落地完全相同 |

⇒ 官方尺与严格尺同时把 `graph.pyc` 打到 **全绿**（本轮 mandate「至少一支修到完全 OK」达成），
且在全语料 398 支上**连一个字节都没有改动**——补丁只在本语料的两个站点（566 / 1114）命中。
`grep -c` 归属证明（落地字节，仓库只读）：
`def _generate_block_statements` L43356（gen 内 2 处，另一处是其 `_body` L43409）、
`self.generated_offsets` 222 处、`self._generated_regions` 256 处、`self.generated_blocks` 938 处、
`def _generate_try` 1 处、`try_offset_end` 30 处、`handler_entry_blocks` 46 处、
`has_trailing_return_none` 6 处；标记站点在 analyzer
`region_analyzer.py` L26876–26894（BASIC 兜底归约：`if self._is_return_none_block(block):
region.mark_trailing_return_none()`，`_is_return_none_block` 定义在 L7463）。

产物层面的唯一变化（`build_landed` vs `build_trytail` 的 `IQCommon__graphOK.py`，464→465 行）：
两处 `return None` 从 **try/except 之后** 搬进 **对应内层 `try` 体的末尾**
（landed L399 → trytail L388 位置；landed L419 → trytail L413 位置），
与 §1.3 三种源码手术全部归零的形态一致。

### 1.6 异常表级保真度（不只是指令流相同，保护区边界也相同）
CPython 3.11 会把 **try 体末尾的 `return`** 发射在保护跨度**之外**（实测最小合成样本）：
```python
def f(q):
    try:
        a = q[1]
        return None
    except KeyError:
        pass
# 保护表：[4,20)->24 depth=0 ; [24,44)->52 depth=1 ; [50,52)->52 depth=1
# 而 LOAD_CONST None @20 / RETURN_VALUE @22 落在 [4,20) 之外
```
原始 `graph.pyc:: _process_task_queue` 的异常表（`dis._parse_exception_table(oc)`，oc 直接用 code object）：
```
[554,558)->560 d0   [558,560)->560 d1   [560,566)->570 d0   [570,830)->838 d1
[1102,1106)->1108 d0 [1106,1108)->1108 d1 [1108,1114)->1118 d0 [1118,1258)->1266 d1
```
`@566`、`@1114` 处正是 `LOAD_CONST None ; RETURN_VALUE`，且**不被任何区间覆盖**，紧跟其后才是 handler
（570 / 1118）——与合成样本的 `end=20` 完全同构。
⇒ 把该块并进 `ast.Try.body` 末尾**同时**复现了指令流与保护跨度，不是「只有官方尺过关」的取巧形状。

### 1.7 ≤15 行合成 witness（可直接入库电池）
`synth/r65_trytail_w.py`（7 个探针，编译成 `synth/r65_trytail_w.pyc`）。只有 `w3`（11 行）触发本形状：
```python
def w3(d, k):
    if k:
        try:
            y = d[k]
            try:
                z = y[k]
                return None
            except KeyError:
                y[k] = 1
        except KeyError:
            return None
    else:
        return d
```
注意源里**没有**任何「try 之后的 `return None`」——`if k:` 分支走到底就是函数的隐式
`return None`，CPython 把它发射在 try 体末尾（保护跨度之外），落地臂把它渲染成
try/except **之后的兄弟语句**（多出一条不存在的语句），候选 A 把它收回 try 体末。
```bash
cd D:/Temp/opencode/r65gate/diag1
python -X utf8 -c "import py_compile; py_compile.compile('synth/r65_trytail_w.py', cfile='synth/r65_trytail_w.pyc', doraise=True)"
python -X utf8 h62.py run --arm=landed  --list=synthw.txt --out=dump/synthw_landed.jsonl
python -X utf8 h62.py run --arm=trytail --list=synthw.txt --out=dump/synthw_trytail.jsonl
python -X utf8 h62.py ab --a=dump/synthw_landed.jsonl --b=dump/synthw_trytail.jsonl
```
```
landed  r65_trytail_w.pyc  7/8  [['w3', 44, 45, 1, 17]]      ← 与 graph 同读数形状（+1 长度 / jumpdiff=1 / 17 true）
trytail r65_trytail_w.pyc  8/8  []
IMPROVED 7/8 -> 8/8 ; files fully matched: a=0 b=1
```
两臂产物差异（唯一一处）= `build_landed` 把 `return None` 放在 `except KeyError: return None` 之后，
`build_trytail` 放在外层 `try` 体的末尾。
未纳入 witness 的 `synth/r65_trytail.py::p5`（`for` + 嵌套 `if` + `return None`，33/30 UNDER 3）
在**两臂都失败且读数逐字节相同**，与本候选无关（属于 §5 那类缺失形状，另案）。
`w1/w2/w4/w5/w6/w7`（单层 try+return、try 尾裸 return、嵌套不同 handler、`finally`）两臂**都全绿**
⇒ 本形状需要「外层 try 体内含一个内层 try，且外层 if 分支以隐式 return 结尾」这一特定组合，
这就是它在全语料 398 支上零外溢的原因。

## 2. fly/logger.pyc :: write_logging_thread（29/30）

`align.py` → `orig=127 decomp=128 ratio=0.8706`，官方 113/113 jumpdiff=1。
实质（把跳转目标噪声剔掉后）只有一件事：**`if msgs:` 块（原 offset 368..424）被排到了 if/else 之后**。
原字节码：`if q:` 的 then 侧 = `[48 … while q>0 …, 368 LOAD_FAST msgs → 424 JUMP_FORWARD 666]`，
666 是 while 的回边块；else 侧 = `[426 … 662 LOAD_CONST None; RETURN_VALUE]`（`break`）。
`regdump.py`：
```
LoopRegion@4 body_blocks=[4,48,64,228,232,288,342,356,368,372,424,426,440,522,564,620,660,662,666]
  children=[LoopRegion@48, IfRegion@368, IfRegion@426, IfRegion@440, IfRegion@564]
```
⇒ `IfRegion@368` 的 parent 是 **LoopRegion@4**（与 `IfRegion@426` 平级），而原结构里它是
`if q:` then 侧的末块。`if q:` 本身**没有 IfRegion**（测试 `POP_JUMP_FORWARD_IF_FALSE to 426`
在 B4 内部，B4 同时含 `q = write_queue.qsize()` 语句前缀），是生成器现场合成的。

### 2.1 归一化实质 hunk 表（`python -X utf8 logs/nhunks.py <pyc> build_landed/fly__loggerOK.py write_logging_thread --ctx=3`）
`orig=127 decomp=128 substantive-hunks=3`（跳距/EXTENDED_ARG 噪声已归一为 `'J'`）：
```
HUNK delete   orig[78:87]@368(9)   decomp[78:78]@366(0)     ← 368..422 `if msgs: self.logger_bt.info(msgs)`
HUNK replace  orig[122:123]@660(1) decomp[113:115]@604(2)   ← orig `660 JUMP_FORWARD to 666`
                                                            ##   decomp `604 EXTENDED_ARG; 606 JUMP_BACKWARD to 2`
HUNK insert   orig[125:125]@664(0) decomp[117:126]@612(9)   ← 同一 9 条指令被搬到回边之后（612..666）
```
即与 §1 不同的形状：**没有多余的 return，只有一个子区域被排到了它不该在的位置**
（then 侧末尾 → 回边之后 / `else: break` 之后），并因此把「跳到循环体底部 666」变成「跳回循环头 2」。
官方 jumpdiff=1 / true=40 就是这一次换位。

### 2.2 本支候选：**NONE**（本轮不交 logger 候选）+ 排除证据
- 排除「多/缺语句」：decomp 只多 1 条（`EXTENDED_ARG`，跳距 >255 的必然产物），三条指令内容全等 ⇒ 纯顺序。
- 排除「归属被破坏」：`regdump.py` 显示 `IfRegion@368` 与 `IfRegion@426` **都是 LoopRegion@4 的 children**，
  两块都存在、都只属于一个区域（每块唯一归属未被破坏），所以修点不在 analyzer 的归约层，
  而在生成器**合成 `if q:` 时的 then 侧收口**：`if q:` 的测试由 B4 内联合成（无 IfRegion），
  合成器只能靠「同层兄弟区域 entry 落在 (test_off, false_target) 开区间内」把 `IfRegion@368` 收进 then 侧。
  这要求把「现场合成的 if」与「真实 IfRegion」两条发射路径共用同一个 then 区间判据；
  `grep -c 'merge_entry'`/`_R64-B1 sibling merge-entry dispatch`（gen L33174）表明现存的兄弟分派
  只在**有 IfRegion** 的通道里生效，合成通道没有该收口步骤 —— 这是一个需要改**两处**（合成 + 分派）
  的结构性改动，超出「一次一份 spec 只改一个文件的一处锚点」的预算，且 R64-B1 在同族上已失败一次
  （battery 的 `probe_r63b2_cases2::d8_elif_try_chain_or_plain` 停在 51/50）。
- 下一条可检验判据（给 R66）：**「内联合成测试的 then 区间」= 同层兄弟区域 entry ∈ (owner_block.test_offset, owner_block.jump_target)**；
  先在 `r64d5_contsink.pyc::probe`（SAME-LEN + jumpdiff=1，与本支同族，见 §0 电池注）上做单点验证，
  那一支的合成语料比 logger 小得多，能写成 ≤15 行的合成复现。

## 3. matcher.pyc :: DefaultMatcher.match（16/17，官方 715/715 SAME-LEN jumpdiff=10）

`python -X utf8 logs/nhunks.py .../matcher.pyc build_landed/IQEngine__plugins__plugin_system_matcher__matcherOK.py match --ctx=0`
→ `orig=800 decomp=809 substantive-hunks=4`（800/809 是含 `EXTENDED_ARG` 的完整计数，官方 715 剔掉了它们）：
```
HUNK insert   orig[168:168]@1064(0)   decomp[168:169]@1066(1)     ← 纯 EXTENDED_ARG 噪声（跳距）
HUNK delete   orig[207:519]@1320(312) decomp[208:208]@1320(0)     ← 312 条整块消失在该位置
HUNK delete   orig[644:648]@3952(4)   decomp[333:333]@2062(0)     ← 4 条（`fill = order.unfilled_amount` 前缀）
HUNK insert   orig[798:798]@4962(0)   decomp[483:807]@3060(324)   ← 产物尾部多出的 324 条
```
**实测证明这是同一段代码的换位，不是缺语句**（脚本：取 `A[207:519]` 与 `B[483:807]` 归一化后做
`SequenceMatcher`）：`len X=312 len Y=324 similarity=0.9748`，非 equal 部分只有
```
  insert   X[0:0]        Y[0:3]   ['LOAD_FAST order','LOAD_ATTR unfilled_amount','STORE_FAST fill']
  replace  X[1:2]        Y[4:5]   JUMP_FORWARD -> JUMP_BACKWARD          （×2 处）
  insert   ×9            EXTENDED_ARG                                    （跳距噪声）
  insert   X[312:312]    Y[322:324] ['EXTENDED_ARG','JUMP_BACKWARD']
```
即：Y = 前面 3 条（属于 orig[204:207] 的 `fill = …`）+ X 的 312 条 + 12 条跳距/回边噪声。
`orig src lines(1320..1944) = (219, 234)`（`co_lines()` 反查）；产物尾部那段落在产品第 190–203 行，
首条语句 `fill = order.unfilled_amount`。两处 `JUMP_FORWARD↔JUMP_BACKWARD` 方向翻转是换位的**指纹**：
被搬的块里有回边指向它**前面**的循环头，块一旦排到尾部，同一目标的相对方向就反了。

⇒ 与 R64 移交线索一致（「715/715 同计数=顺序问题，不要再去找缺失语句」），
本轮把范围进一步收窄为：**orig 源 219–234 行那一整个兄弟槽被追加到了父序列末尾**，
前槽被 `if self._volume_limit:` 占据。归因层面（每块唯一归属）没有坏：两个槽的区域都存在、
各自只属于一个父区域；坏的是**父层发射顺序**。

### 3.1 本支候选：**NONE**（本轮不交顺序候选）+ 理由
在产物上无法写 ≤15 行合成复现（该形状要求父序列里两个兄弟区域的**入度/回边**同时存在，
最小可复现需要真实循环 + 两个 if 槽，实测 `r64d5_contsink` 也只有 122/122 SAME-LEN 级别）。
不交候选的具体原因：可用的同层次判据只有一个（兄弟区域按 `entry.start_offset` 升序发射），
但它要求 AST 节点携带来源块 entry 偏移，现存 `ast_*` dict 不携带该信息
（`grep -c "'type': 'If'"` 产出的 dict 里没有 block/offset 字段），
加字段=改 `_generate_block_statements` 的返回契约（gen L43356 / L43409 两处，938 个 `generated_blocks` 使用点），
不可能在一份 spec 的一次锚点编辑里完成，也不会「只影响这一支」。留给 R66 的最小实验：
给 `RegionASTGenerator` 加一个 `self._stmt_origin: dict[id(stmt) -> entry_offset]`（只在 append 处写，
不参与语义），在**单个**父序列 append 完成后按 origin 做一次稳定排序，先只在 battery 上量。

## 4. realtime_event_source.pyc :: RealtimeEventSource.clock_worker（11/12，官方 1275/1286 OVER+11）

`python -X utf8 logs/nhunks.py .../realtime_event_source.pyc build_landed/IQEngine__plugins__plugin_system_event_source__realtime_event_sourceOK.py clock_worker --ctx=0`
→ `orig=1442 decomp=1458 substantive-hunks=14`，其中只有两处是大的：
```
HUNK delete  orig[959:976]@6690(17)   decomp[962:962]@6694(0)     ← orig 源 442–444 行
HUNK delete  orig[1192:1304]@7972(112) decomp[1170:1170]@7794(0)  ← orig 源 498–507 行
HUNK insert  orig[1408:1408]@9194(0) decomp[1274:1409]@8404(135)  ← 产品第 289–297 行（尾部）
HUNK replace orig[1411:1413]@9210(2) decomp[1412:1429]@9142(17)   ← 产品第 314–315 行
```
与 matcher 同样的证明（`X=A[1192:1304]`, `Y=B[1274:1409]`）：`len X=112 len Y=135 similarity=0.8907`，
差异 = 头部 6 条（`… initial_trading_date == / POP_JUMP_FORWARD_IF_FALSE`，属于前一槽）
+ 尾部 19 条 `['JUMP_FORWARD','PUSH_NULL','LOAD_FAST check_trading_time','LOAD_FAST am_open', …]`
+ 2 条 EXTENDED_ARG。⇒ **clock_worker 也是「一个兄弟槽被追加到末尾」+「末尾多出一次 elif 测试」**。

**R64 移交线索的定量确认（这条是对的）**：按 argrepr 统计 orig/decomp 的名字发射次数
```
name                       orig decomp
check_trading_time            4    5     ← 多发射一次（产品第 312 行 `elif check_trading_time(...)`）
check_handle_date            见下（两个嵌套 code object line 380 / 383 在 decomp 侧计数为 0）
am_open / am_close / pm_open / pm_close / pm_over / config / frequency / strategy / _engine
                              7/7/7/11/7/9/2/4 → 8/8/8/12/8/10/3/5   （整条 elif 臂 +1）
EventEnum 11→10  dt 17→16  now_date 21→20  event_queue 9→8  None 9→8  PRE_BEFORE_TRADING_START 2→1
                                                              （被搬到尾部的那一段造成的等量损失）
```
`check_trading_time` 的 LOAD 偏移：ORIG `[1794, 2890, 3946, 8594]` vs DECOMP `[1794, 2890, 3946, 7802, 9052]`
⇒ 前 3 个臂位置完全一致，第 4 个（orig 8594，源 527 行）在产物里出现**两次**（7802 / 9052）。
产物第 275 行是有内容的那次发射（`elif …: if check_handle_date(now_date): …`，第 276–281 行），
第 312 行是**空臂**：`elif check_trading_time(…):` + `pass`（第 313 行）。
`check_handle_date` 在 orig 里被调用 1 次（@8668，源 534 行）+ 定义 2 个嵌套 code object，
产物里只剩 1 次调用（@7876）⇒ 空臂那一次是**纯粹的重复发射**，归属层（`generated_blocks`）没有重复块，
是 elif 链分派在「then 侧已被别的槽生成完」时仍然保留了 `elif <test>: pass`。

### 4.1 本支候选：**NONE**（本轮）+ 排除证据
在产物上做源码手术并重新编译（与 §1.3 同一把尺：归一化后的 `SequenceMatcher` hunk 数）：
```
变异                                        decomp 长度   实质 hunk   大 hunk
as-is（build_landed）                          1458         14        delete@7972(112) / insert(135)
drop 产品第 312–313 行（空 elif 臂 + pass）      1440         14        delete@7972(112) / insert(117)
原始 clock_worker                              1442          —          —
```
⇒ 那条**空 elif 臂正好值 18 条指令**（1458→1440，把 OVER +16 变成 −2，长度几乎对齐），
但 5 个大 hunk 一个都没消失：112 条位移与它**不是同一件事**。
所以修完重复臂只能让计数对齐，jumpdiff 仍不会是 0 ⇒ 无法验证「修到 12/12」，收益不足；
而且判据要落在 elif 链分派（gen 的 elif 通道，R61 家族）上，风险面 = 全语料所有 elif 链。
结论：与 §3 同因（父序列 append 顺序 + 空臂保留），两支合并成一条 R66 判据（见 §3.1 末尾）。

## 5. api_base.pyc :: get_history_df（24/25，官方 1742/1719 UNDER 23）

`python -X utf8 logs/nhunks.py .../api_base.pyc build_landed/IQData__api__api_baseOK.py get_history_df --ctx=0`
→ `orig=1900 decomp=1873 substantive-hunks=8`：
```
HUNK replace  orig[457:462]@2242(5)    decomp[457:458]@2242(1)   产品第 296 行 if/or 条件
HUNK replace  orig[522:527]@2506(5)    decomp[518:519]@2496(1)   产品第 305 行三元赋值
HUNK insert   orig[534:534]@2534(0)    decomp[526:530]@2516(4)   产品第 305–306 行
HUNK insert   orig[552:552]@2578(0)    decomp[548:552]@2570(4)   产品第 312 行 `time_count -= 1`
HUNK delete   orig[584:586]@2690(2)    decomp[584:584]@2688(0)   产品第 318 行
HUNK delete   orig[1034:1035]@4968(1)  decomp[1032:1032]@4958(0) 产品第 377 行
HUNK delete   orig[1039:1063]@4982(24) decomp[1036:1036]@4970(0) 产品第 377 行  ← 24 条整块缺失
HUNK replace  orig[1072:1073]@5126(1)  decomp[1045:1046]@5002(1)
```
**这一支与前两支不同：是真缺语句。** 最大块 `orig[1039:1063]`（24 条，原始源 520–522 行）内容实测为
```
4982 EXTENDED_ARG
4984 POP_JUMP_FORWARD_IF_FALSE to 6896
4986 LOAD_FAST engine_obj
4988 LOAD_ATTR basic_data_handler
4998 LOAD_METHOD get_dividend
5020 LOAD_FAST symbol
5022 LOAD_CONST None
5024 PRECALL
5028 CALL
…
```
= 源形态 `if not tmp_dividends: tmp_dividends = engine_obj.basic_data_handler.get_dividend(symbol, None)`。
产物里该 guard **完全不存在**：`grep -n 'get_dividend' build_landed/IQData__api__api_baseOK.py` 只命中
**1 次**（第 185 行，属于**另一个函数** `get_future_history_df`；orig 侧 `get_dividend` 的 LOAD_METHOD
在两个函数里各一次：`get_future_history_df @3090`、`get_history_df @4998`）。
产物第 377–379 行现在是
```
377         if fq == DIVIDEND_CALC_TYPE[1] and len_real_data > 0:
378             return real_data if fields is None else real_data[fields]
379         dividends = tmp_dividends[symbol]      ← 直接读 tmp_dividends，guard 没了
```
其余 4 处（2242/2506/2534/2570 各 4~5 条）集中在产品第 296/305/312 行的
`or` 条件与三元赋值上，是 BoolOp/Ternary 展开的**指令形状差异**（不是丢语句），
2+1 两处小 delete 在 2690/4968。

### 5.1 本支候选：**NONE**（本轮）+ 下一步判据
缺 guard 的形状要先确认它归谁：`tmp_dividends = …get_dividend(…)` 只在被 `if not tmp_dividends:`
包住时出现，而该 if 的 then 侧赋值正好被「值上下文/链式消费」吸收（`tmp_dividends` 下一条语句即消费它）。
这与 R64 已知的 `r64d2_valuectx_consumer` / `r64d1b_closed-shared-exit-prefix` 家族同形，
区别是这次被吞掉的是**赋值目标本身**（`if not X: X = f()` 后面 X 被读）。
下一步可检验判据：`IfRegion.then` 是单块、块内唯一语句是 `Assign(target=T)`，
且 `T` 在 if 之后的同层第一条语句里被 LOAD，且 `if` 的 test 是 `UnaryOp(Not, T)`
⇒ 禁止吞并（该形状等价于 `X = X or f()` 的反向：`if not X: X = f()` 不能被改写成 `X or f()` 的一部分）。
本轮未做实验，因为需要先量化它在 battery 的 `r64d2_valuectx_consumer.pyc`（2/2 全绿）上会不会破——
那是「已入库 witness」，破一支就丢一次 mandate。

## 6. 交付清单
| 支 | 候选 | 读数 |
|---|---|---|
| `IQCommon/graph.pyc` | **A = `specs/cand_r65_trytail.json`**（generator，1 edit） | targets `IMPROVED 30/31 -> 31/31`、strict `33/34 -> 34/34`、battery SAME=19、canary SAME=4、**全语料 398 支 sha 全等**；合成 witness `synth/r65_trytail_w.pyc` `7/8 -> 8/8`（§1.7，可入库电池） |
| `fly/logger.pyc` | NONE（§2.2） | 9 条指令换位，判据需改两处 |
| `matcher.pyc` | NONE（§3.1） | 312 条位移，similarity 0.9748 证明同段 |
| `realtime_event_source.pyc` | NONE（§4.1） | 112 条位移 + 1 次空 elif 臂重复（`check_trading_time` 4→5） |
| `IQData/api/api_base.pyc` | NONE（§5.1） | 真缺 24 条（`if not tmp_dividends:` guard 被吞） |

