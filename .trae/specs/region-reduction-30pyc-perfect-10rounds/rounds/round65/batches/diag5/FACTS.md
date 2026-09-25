# Round 65 · diag5 · FACTS（实测读数）

工作目录 `D:/Temp/opencode/r65gate/diag5`；仓库 `F:/Downloads/pythoncdc-main` **全程只读**。
所有读数均由 `python -X utf8 h62.py` / `cstrict.py` / `align.py` 产出，可复放（命令见每节）。

## 0. 仓库完整性（开工前 / 交付前）

```
core/cfg/region_ast_generator.py  3 103 668 B  sha256[:12] c9099bb0fc35  BOM  CRLF=50149  裸LF=0
core/cfg/region_analyzer.py       1 725 369 B  sha256[:12] 24a88392ee61  noBOM CRLF=27635  裸LF=0
```
与 BRIEF §4 逐字一致。`git status --porcelain` 里 **没有任何 core 文件**（只有本轮之前就存在的
`.trae/specs/.../round64/OUTCOME.md` 与若干 `?? test_repros/out_*` 未跟踪目录，非本代理所为）。
`h62.py build` 自带断言 `head mirror == worktree bytes`，三次 build 全部通过 ⇒ 工作树未被改写过。

## 1. 落地基线（7 支 targets，`--arm=landed`，逐支与 BRIEF §5 一致）

```
python -X utf8 h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl --nshard=7 --shard=I   # I=0..6
```
| 文件 | matched | 缺陷元组 [orig,decomp,jumpdiff,true] |
|---|---|---|
| IQEngine/utils/scheduler.pyc | 43/45 | get_checked_time [106,106,0,43] · run_daily [77,71,0,56] |
| fly/simtradding/flyAccount.pyc | 21/23 | _do_request [436,443,2,384] · init_connection [42,41,0,25] |
| …/fly_api/order_api.pyc | 32/34 | future_order [101,92,2,36] · option_order [83,73,3,39] |
| IQCommon/util/common_func.pyc | 19/21 | get_kline_time_by_frequency_array [231,228,0,45] · **get_kline_time_by_section [210,190,0,84]** |
| IQData/utils/common_func.pyc | 22/24 | **get_kline_time_by_section [210,190,0,84]** · handle_exrights [276,268,1,263] |
| IQCommon/util/fileio_utils.pyc | 12/14 | acquire [96,93,3,52] · write [637,637,4,519] |
| IQCommon/strategy/wizard_quant_api.pyc | 51/53 | calculate_di [75,73,0,45] · params_analysis [133,126,1,117] |

严格尺（`cstrict.py build_landed targets.txt`）：scheduler 49/52、flyAccount 21/23、order_api 33/36、
IQCommon/util 20/22、IQData/utils 25/27、fileio 13/15、wizard 52/56；`missing=0 extra=0` 全部成立。

## 2. 双生 `get_kline_time_by_section` —— **已定位并出候选（本批唯一可落地候选）**

### 2.1 双生同步性（先证实，再动手）
`align.py` 对两支 `.pyc` 输出的 opcode 序列**逐字相同**（只有文件名/行号不同）：

```
python -X utf8 align.py …/IQCommon/util/common_func.pyc build_landed/IQCommon__util__common_funcOK.py get_kline_time_by_section
python -X utf8 align.py …/IQData/utils/common_func.pyc  build_landed/IQData__utils__common_funcOK.py  get_kline_time_by_section
两者均：orig=230 decomp=209 ratio=0.9248
opcodes=[('replace',56,57,56,57),('replace',133,141,133,134),('replace',151,152,144,145),
         ('delete',155,169,148,148),('replace',183,184,162,163),('replace',187,188,166,167),
         ('replace',201,202,180,181)]
```
⇒ 任何候选必须同时在两支上量；下表每一行都是两支同读数。

### 2.2 指令级清单：UNDER 20 = **两条完整语句没发射**（不是语句内容错）
`regdump.py … common_func.pyc get_kline_time_by_section`：
```
CFG: 22 blocks, 12 regions
TOP: LoopRegion@122 | TernaryRegion@424 | IfRegion@530 | IfRegion@618 | TernaryRegion@692
  BoolOpRegion@530 blocks=[530,558] merge=618 entry=530 parent=IfRegion@530 value_target=None op_chain=[(530,'and'),(558,'and')]
  IfRegion@530 blocks=[530,612] cond_block=558 merge=618 then=[612]
             inline_boolop_chains={id(block530): {'blocks':[blk14@530-556, blk15@558-610], 'op':'and'}}
  IfRegion@618 blocks=[618,638] cond_block=618 merge=692 then=[638] children=[Region@618,Region@638]
  block_to_region[530] = IfRegion@530        block_to_region[618] = IfRegion@618
```

| 丢失段 | orig offsets | 指令数 | 源码 | 根因 |
|---|---|---|---|---|
| **L1** | 534,536,538,540,542,552 | 6 | `datetime_list = datetime_list[offset:]`（块 530 的链首前缀） | 见 2.3-B |
| **L2** | 618,620,622,632,634,636,638,640,662,664,666,676,680,690 | 14 | `if datetime_list_section[-1] in datetime_list: datetime_list.append(datetime_list_section[-1])` | 见 2.3-A |

6 + 14 = **20** ⇒ 精确解释 `orig=210 / decomp=190`。`jumpdiff=0` 是因为两段都是**整块删除**，
剩余指令的相对跳转目标全部自洽 —— BRIEF 里「true=84 ⇒ 整段语句没发射」的判断成立。

### 2.3 归因到方法 + 落地行号（行号为落地字节行号，`grep -c` 证明被调用）

**(A) `RegionASTGenerator._generate_if` 的 `return []`（L11584，入口 L11528）**
```
python -X utf8 trace.py …common_func.pyc get_kline_time_by_section 530,612,618,638,692
> _generate_region IfRegion@618 blocks=[618,638] merge=692 entry=618 parent=None
< _generate_region -> []            ← 整条 if 归约为空
```
运行时探针实测（region@618 进入 `_generate_if` 的那一刻）：
```
ENTRY618 in generated_blocks? True
  block_to_region[618] is region -> True
  unemitted arm blocks -> [638]
  boolop_merge_owner -> None
  generated blocks: [0,122,124,232,236,238,354,376,402,408,424,476,528,530,558,612,618]
```
⇒ 走到 L11528 `if region.entry and region.entry in self.generated_blocks:`，`boolop_child` 找不到
（BoolOpRegion@530 的 entry 是 530 不是 618），`_c2_ternary_redirect` False，
`_boolop_merge_owner_for(...) is None` ⇒ **L11584 `return []`**。
根因：`IfRegion@530` 的 **merge_block 恰是其兄弟 `IfRegion@618` 的 entry**；@530 发射时把汇合块
登记进 `generated_blocks`，@618 就被「entry 已 generated ⇒ 本区域已发射」这一推断误杀。

**(B) `_if_generate_normal` 的链首前缀提取封锁（L17347）**
```
NORMAL region@530 cond=558 inline_chains=[…]
EXTRACT cond=558 region@530 bmt=None -> pre=[] cond=[LOAD_GLOBAL,LOAD_FAST,…,COMPARE_OP]
  → 只有这一条 EXTRACT 调用；L17349 的 _if_extract_cond_instructions(region.entry=530, …) 从未被调用
```
`generate()` 的 L745-750「`and` 链首块 == entry」passthrough 分支 **故意不在入口发射前缀、
也不登记 `_entry_prefix_emitted_blocks`**，把发射权显式交给 `_if_generate_normal` 的
`entry is not cond_block` 分支；但该分支在 L17347 用 `region.entry not in self.generated_blocks`
做闸门，而块 530 已被**条件模式的子 BoolOpRegion@530**（`value_target=None`，
`_generate_boolop_impl` 只写 `condition_expr`、`return None`、不产出语句）登记为 generated
⇒ 两边都不发，语句蒸发。

对照面（为什么不能简单放开）：`IQEngine/utils/scheduler.pyc::run_weekly` 块 0 同样是
「块首含完整前缀语句 + 块尾是 and/or 短路链操作数」，但它的 `block_to_region[0]` 是普通
`Region@0`，走的是 `generate()` L762/L801 入口通道，前缀**已经**发射并登记进
`_entry_prefix_emitted_blocks`。只按「有条件模式 BoolOp 子区域」放宽 ⇒ run_weekly 43/45→42/45，
`_verify_function('run_weekly', func)` 与 `minute_time = self.get_checked_time(minute_time)` 各重复一次
（实测 difflib 输出，OVER +8）。第一版 `r65d5_b.json` 就是这么翻车的，已按 provenance 收窄。

### 2.4 三条候选的实测（`--arm=a` / `--arm=b` / `--arm=ab`）

```
python -X utf8 h62.py build --spec=specs/r65d5_a.json  --dst=a
python -X utf8 h62.py build --spec=specs/r65d5_b.json  --dst=b
python -X utf8 h62.py build --spec=specs/r65d5_ab.json --dst=ab   # 2 edits，同一文件
python -X utf8 h62.py run --arm=X --list=targets.txt --out=dump/X.jsonl
python -X utf8 cstrict.py build_X targets.txt dump/X_strict.json
```

targets 上 `get_kline_time_by_section` 元组（**两支永远同读数**）：

| 臂 | IQCommon/util | IQData/utils | scheduler | 其余 4 支 |
|---|---|---|---|---|
| landed | 19/21，gkts[210,**190**,0,84] | 22/24，gkts[210,**190**,0,84] | 43/45 | 基线 |
| a（只 A） | 19/21，gkts[210,**203**,0,84] | 22/24，gkts[210,**203**,0,84] | 43/45 ✓ | 逐字节不变 |
| b（只 B） | 19/21，gkts[210,**197**,0,**63**] | 22/24，gkts[210,**197**,0,**63**] | 43/45 ✓ | 逐字节不变 |
| **ab（A+B）** | **20/21**，gkts 已从缺陷表消失 | **23/24**，gkts 已从缺陷表消失 | 43/45 ✓ | 逐字节不变 |

严格尺同步：IQCommon/util `20/22 → 21/22`，IQData/utils `25/27 → 26/27`，
`missing=0 extra=0`；scheduler 严格尺 `49/52` 两侧同缺陷集（get_checked_time、run_daily、run_daily.func_wrapper）。

⇒ **必须成对**：A 只找回 14 指令段（203），B 只找回 6 指令段（197），只有 A+B 才把
该函数推到字节码全等。单支都过不了门禁。合并方式 = 一份 spec 两处 edit（同一文件
`core/cfg/region_ast_generator.py`），已由 `specs/r65d5_ab.json` 直接给出并实测。

### 2.5 电池 / canary（A 与 AB 各自单独量过）

```
python -X utf8 h62.py run --arm=X --list=battery.txt --out=dump/bat_X.jsonl
python -X utf8 h62.py ab --a=dump/battery_landed.jsonl --b=dump/bat_X.jsonl
python -X utf8 h62.py run --arm=X --list=canary.txt  --out=dump/can_X.jsonl
python -X utf8 h62.py ab --a=dump/canary_landed.jsonl --b=dump/can_X.jsonl
```
| 臂 | battery（19 项 R63+R64 复现） | canary（4 支 f-string/boolop 重载） |
|---|---|---|
| a | `SAME=19 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`（fully matched 14=14） | `SAME=4` 逐支 sha 不变 |
| ab | `SAME=19 IMPROVED=0 REGRESSION=0 MOVED=0 ERR=0`（fully matched 14=14） | `SAME=4` 逐支 sha 不变 |

canary sha（landed / a / ab 三列全等）：
```
quotation.pyc    4d41187e356544e0   (143/143)
market_time.pyc  af77224b34b203c4
datetime_func.pyc(IQCommon) 9d09af09249da177
datetime_func.pyc(IQData)   <同 landed>
```
电池 landed 基线本身有 5 项残余（r63_ft4 1/2、probe_r63b2_cases 7/9、probe_r63b2_cases2 7/9、
r63b5_w1 1/2、r64d5_contsink 1/2），A/AB 后**逐字节不变** ⇒ 不比落地差成立。

### 2.6 合成复现 —— **有，不是 NONE**
`synth/v1.py`（9 行）与 `synth/v2.py`（13 行）都是真复现，`python -X utf8 py_compile` 成 `.pyc`，
用同一批臂实测（`--list=synth/list2.txt`）：

| 合成件 | landed | arm a | arm b | arm ab |
|---|---|---|---|---|
| `synth/v1.pyc` | 1/2 `p[51,38,0,15]` | **2/2** | 1/2 `p[51,38,0,15]`（不动） | **2/2** |
| `synth/v2.pyc` | 1/2 `p[71,52,1,53]` | 1/2 `p[71,65,0,52]` | 1/2 `p[71,58,0,33]` | **2/2** |

⇒ `v1` 单证 D5-A（汇合块即兄弟入口 ⇒ 整条 if 被吞，jumpdiff=0 与真品同签名）；
`v2` 加回三元前缀 + `set/sort` + 尾部三元，**必须 A+B 才 2/2** —— 与双生正品完全同构。
关键前提（第一版 8 行复现失败的原因）：链首块必须**同时**承担三元汇合 STORE、完整赋值语句、
and 链操作数三重角色，且被吞的 if 的条件是 `in`（CONTAINS_OP）—— 少了三元就落在不同基本块里，
`landed` 直接 2/2，复现不出来。

## 3. `fly/simtradding/flyAccount.pyc :: _do_request` [436,443,2,384] 过冲 +7

### 3.1 指令级清单：过冲**全部**是 `POP_TOP; LOAD_CONST None`，零删除
```
lenA=471 lenB=480 net=+9     （官方尺口径 net=+7）
纯插入 8 处，纯删除 0 处：
  INS decomp@294  : POP_TOP | LOAD_CONST None
  INS decomp@318  : POP_TOP | LOAD_CONST None
  INS decomp@1290 : POP_TOP | LOAD_CONST None
  INS decomp@1352 : POP_TOP | LOAD_CONST None
  INS decomp@1798 : POP_TOP | LOAD_CONST None
  INS decomp@2012 : POP_TOP | LOAD_CONST None
  INS decomp@2036 : POP_TOP | LOAD_CONST None
  INS decomp@2184 : LOAD_CONST None
```
落地 `OK.py` 对应源码（`build_landed/fly__simtradding__flyAccountOK.py` L130-131）：
```
                    (error_dict, {} if is_dict else [])      ← 应是 return，退化成裸 Expr ⇒ POP_TOP
                    return None                              ← 凭空多出的 LOAD_CONST None; RETURN_VALUE
```
正确形态是 `return error_dict, ({} if is_dict else [])`：
orig 128 之后 `130 LOAD_FAST error_dict … 292 BUILD_TUPLE 2, 294 RETURN_VALUE`。

### 3.2 归因（方法 + 落地行号 + 运行时调用证据）
`regdump.py … _do_request`：93 blocks / 33 regions，其中 **7 个 TernaryRegion 的 merge 块只有一条
`BUILD_TUPLE 2`、`merge_context` 为 `None`**（不是 `'store'/'iter'/'compare'/'while_cond'`）：
```
TERN@280  blocks=[280,286,290,292] merge=292  ctx=None  parent=IfRegion@36     merge instrs=[('BUILD_TUPLE',2)]
TERN@296  blocks=[296,308,312,314] merge=314  ctx=None  parent=IfRegion@36
TERN@1254 blocks=[1284,1254,1266,1282] merge=1284 ctx=None parent=IfRegion@820
TERN@1310 … TERN@1770 … TERN@1992 … TERN@2014                                    （同形）
TERN@2056 blocks=[2152,2148,2056,2154] merge=2154 ctx='store' parent=TryExceptRegion@4   ← 第 8 处 LOAD_CONST None
```
7 个 `ctx=None` 的 merge 偏移 292/314/1284/1354/1798/2010/2032 与 §3.1 的 7 个
`POP_TOP|LOAD_CONST None` 插入点 294/318/1290/1352/1798/2012/2036 **一一对应**。
即：值语境三元（其结果块以 `RETURN_VALUE` 终结、且三元只是被返回元组的一个元素）被归约成
`Expr(元组) + Return(None)`，`RETURN_VALUE` 没有被折回 `ast.Return(value=Tuple)`。

负责折叠的既有方法是 **`_apply_r23n6_return_promotion`（`def` 落地 L47376）**，
其 L47420-47423 守卫「块尾（跳过 JUMP）是 POP_TOP 就不提升」——真品这里块尾正是被三元区域
发射成 Expr 后留下的 POP_TOP，于是提升被自己的守卫挡死。`{'type':'Return','value':None}`
的另外三处合成点在 `_generate_handler_body_statements`（`def` L26569，行 26793/27082/27539）。

运行时调用计数（monkeypatch 计数，仓库零改动）：
```
_do_request      : _loop_build_if_with_exit_branches=0  _generate_ternary=1  _try_build_ternary_kwarg_call=0
option_order     : _try_build_ternary_kwarg_call=1  _discover_predicate_and_chain=1  _loop_build_if_with_exit_branches=0
future_order     : _try_build_ternary_kwarg_call=1  _discover_predicate_and_chain=2  _loop_build_if_with_exit_branches=0
```

### 3.3 **R64 移交线索被证伪**
BRIEF §5 说 diag5 指到 `_loop_build_if_with_exit_branches`（约 L10470）。
`grep -n` 复核：该函数**确实存在**，`def` 正好在 **L10470**（调用点仅 L10014，全文件引用 2 处）——
行号不是编的。但它是 **loop** 侧 helper，`_do_request` 的三个出站点都在 `if func: … else: …`
的臂里、不在任何 LoopRegion 内，**运行时调用 0 次**（§3.2 计数）。
⇒ 该线索对 `_do_request` 无效，下一轮不要再去 L10470 找。
「过冲由 R63-B4 成对引入」这条我**无法在只读约束下证伪/证实**（要做旧核臂，
`h62.py build` 有 `head == worktree bytes` 断言，不允许装旧字节）；
但过冲的落点在 §3.2 的三元-return 折叠上，与 R63-B4 的 elif/三元让位判据同族。

## 4. `IQEngine/utils/scheduler.pyc`（43/45，AB 臂逐字节不变）

### 4.1 `get_checked_time` [106,106,0,43] —— **纯 MOVE，坐实「顺序问题」**
```
align: orig=122 decomp=122  ratio=0.9016   ← SAME-LEN 成立
HUNK replace orig[23:32]@130  decomp[23:24]@130
  ORIG: 130 LOAD_GLOBAL NULL+divmod | LOAD_FAST minute_time | LOAD_CONST 100 | PRECALL | CALL
        | UNPACK_SEQUENCE | STORE_FAST hour | STORE_FAST minute | JUMP_FORWARD to 390
  DEC : 130 JUMP_FORWARD to 352
HUNK insert  orig[71:71]@-   decomp[63:71]@352
  DEC : 352 LOAD_GLOBAL NULL+divmod | … | 388 STORE_FAST minute      （同一批指令，挪到这里）
```
⇒ 没有任何指令丢失/多出：`hour, minute = divmod(minute_time, 100)`（orig 源码行 241）
在原始布局里位于**内层 try 体内、handler 的 `PUSH_EXC_INFO`@170 之前**，落地把它排到了
handler 汇合点（390→352）之后。BRIEF 里「SAME-LEN ⇒ 找块被排到哪儿」的判断成立。
`run_weekly` 在 §2.4 已被用作 D5-B 的反面教材（其块 0 归属是普通 `Region@0`，前缀已发射）。

### 4.2 `run_daily` [77,71,0,56] UNDER 6 —— **cellvar 退化，不在区域归约层**
```
orig=92 decomp=82  net=-10
DEL orig@8   MAKE_CELL minute
DEL orig@168 LOAD_GLOBAL NULL+int | LOAD_FAST time_info | LOAD_CONST 1 | BINARY_SUBSCR
             | PRECALL | CALL | SWAP                       （= hour = int(time_info[0])）
DEL orig@212 STORE_DEREF minute
DEL orig@45  LOAD_CLOSURE minute
```
`minute` 在原码里是 **cell variable**（被 L262 的嵌套 `func_wrapper` 闭包捕获），
落地按普通局部量发射 ⇒ `STORE_DEREF→STORE_FAST`、`MAKE_CELL/LOAD_CLOSURE/SWAP` 整套消失。
这是 co_cellvars/freevars 与代码生成层的问题，**没有**「entry/merge_block/parent/then_blocks/
body_blocks + 控制流角色 + 指令模式」的同层次结构判据可以表达它 ⇒ 本批不出候选。

## 5. 其余 4 支（本批未出候选，仅出清单）
```
fileio_utils::write    [637,637,4,519] orig=720 decomp=721 net=+1  hunk=29（几乎全是跳转位移）
  唯一结构性 hunk replace o@206 9->2：
    ORIG: NOP | LOAD_CONST None ×3 | PRECALL | CALL | POP_TOP | LOAD_CONST True | RETURN_VALUE
    DEC : EXTENDED_ARG | JUMP_FORWARD to 778
  ⇒ finally 收尾块被搬到函数末尾再用长跳过去，SAME-LEN + jumpdiff=4 = 同一类 try/finally **排程**问题。
fileio_utils::acquire  [96,93,3,52]  orig=114 decomp=108 net=-6；insert d@302 0->8
wizard::params_analysis[133,126,1,117] orig=144 decomp=137 net=-7
  delete o@50 9->0；decomp 在 40-44 多出 POP_EXCEPT|LOAD_CONST None|RETURN_VALUE
  且丢掉 LOAD_GLOBAL NULL+float | LOAD_FAST value_params | PRECALL | CALL（`float(value_params)`）
  ⇒ 也是 except/finally 收尾排程 + 一条被吞的调用。
wizard::calculate_di   [75,73,0,45]  orig=90 decomp=88 net=-2；delete o@152 1->0, o@240 1->0
common_func(IQCommon)::get_kline_time_by_frequency_array [231,228,0,45]
  orig=254 decomp=251 net=-3；delete o@1070 3->0，其余为 None/跳转 1->1 抖动
order_api::option_order [83,73,3,39] / future_order [101,92,2,36]
  §3.2 计数证明 `_try_build_ternary_kwarg_call`（def L42708）在两支各被调用 **1 次** ⇒ R50 指认的
  阻塞点确在活跃路径上；本批**未**再碰汇合块归属（R50 已测成 inert/更差）。
```

## 6. 更宽语料的附带影响（18 支 site-packages，超出本批 7 支 targets）
```
cp D:/Temp/opencode/r65gate/r65_targets.txt → wide.txt（剥掉批注，18 个 .pyc）
python -X utf8 h62.py run --arm=landed --list=wide.txt --out=dump/w_landed.jsonl --nshard=5 --shard=0..4
python -X utf8 h62.py run --arm=ab     --list=wide.txt --out=dump/w_ab.jsonl     --nshard=5 --shard=0..4
python -X utf8 h62.py ab --a=dump/w_landed.jsonl --b=dump/w_ab.jsonl
```
```
IMPROVED IQCommon/util/common_func.pyc   19/21 -> 20/21
IMPROVED IQData/utils/common_func.pyc    22/24 -> 23/24
MOVED    …trade_live_broker.pyc  get_etf_stock_info [144,117,1,139] -> [144,146,1,139]
TALLY SAME=15 IMPROVED=2 REGRESSION=0 MOVED=1 ERR=0
```
唯一 MOVED 由**编辑 A** 造成（b 臂不动，a/ab 臂同为 146），落地 `difflib` 实测它**找回了被整块吞掉的
10 行源码**（`if isinstance(security, list): … elif …: return None / else: pass`），
只是多出 2 条（疑似 `in_stock = []` 重复 + `else: pass`）⇒ 144 vs 146，函数仍未过门禁，
**matched_functions 105/119 不变**。方向正确、非回归，但该函数的主责代理需复核这 2 条。

## 7. 交付物清单
```
specs/r65d5_ab.json   ← 推荐落地件：1 文件 2 edits（A+B），targets +2 支、电池/canary 逐字节不变
specs/r65d5_a.json    ← A 单独件（找回被吞 if；合成 v1 即 2/2）
specs/r65d5_b.json    ← B 单独件（找回链首前缀赋值）
synth/v1.py v1.pyc  synth/v2.py v2.pyc   ← 合成 witness（§2.6）
FACTS.md  ANALYSIS.md
```
三份 spec 都是**同一文件** `core/cfg/region_ast_generator.py`，不需要 generator+analyzer 成对；
但 **A 与 B 必须成对**才能过双生函数门禁（§2.4 表格）。
本代理全程未写仓库：`git status --porcelain` 里没有任何 core 文件，
两支 core 的 sha/字节数/CRLF 数/裸 LF 数与 BRIEF §4 逐字相符（§0）。
