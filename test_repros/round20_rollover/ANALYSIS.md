# Round 20 — `RotatingFileHandler.perform_rollover` 丢 2 条指令：诊断 + 已实测通过的提案

状态：**机制实测锁定；提案 `f3` 四道门禁全绿**（两孪生 119/127、`check_pyc` 整文件、
26 项电池 HEAD↔候选、全量 402 条目 A/B `improved=2 broken=0`）。
HEAD = `e42ab35b`（本次实测期间从 `b7c03065` → `8ad93359` → `e42ab35b` 移动过两次，
均为纯文档/仓库清理提交；`git diff --stat b7c03065 HEAD -- core bytecode pycdc.py _r10_strict_check.py`
**输出为空** ⇒ `core/**` 逐字节同源，本文所有测量对当前 HEAD 有效）。
**仓库内 `core/**` 未做任何修改**；所有补丁只打在镜像核 `D:/Temp/r20b/mirror/f3/`。
我的 scratch = `D:/Temp/r20b/`；上一棒证据 = `D:/Temp/r20/`（只读，仅新增文件）。

---

## 0. 目标（尺子确认，同模块两份源码版本）

```
site-packages/IQCommon/logger/handlers.pyc         official 17/18 partial  (strict 28/30)
site-packages/IQEngine/utils/logger/handlers.pyc   official 13/14 partial  (strict 16/17)
唯一共同真缺陷 <module>.RotatingFileHandler.perform_rollover
    twin A [seq_len] orig=119 decomp=117   twin B [seq_len] orig=127 decomp=125
```

## 1. 原始源码形状（已实测核实，非猜测）

`D:/Temp/r20/scratch/recon_A.py` 重新编译后逐条对比：
`D:/Temp/r20b/logs/origA_seq.txt` vs `reconA_seq.txt` → **指令序列逐字相同（130 条原始 / 119 条去噪）**。
即真实源码就是 `for ... else ...` + 裸 `break`：

```python
def perform_rollover(self):            # 152
    self.stream.close()                # 153
    for x in range(self.backup_count - 1, 0, -1):    # 154  FOR_ITER@102 → 出口 198
        src = '%s.%d' % (self._filename, x)          # 155
        if os.path.exists(src):                      # 156  POP_JUMP_IF_FALSE@190 → 196(latch)
            break                                    # 157  块192 = [POP_TOP, JUMP_FORWARD→302]
    else:                                            # 158
        rename(self._filename, self._filename + '.1')# 159  块198
        self._open('w')                              # 160
        return                                       # 161
    for i in range(x, 0, -1):                        # 162  块302(preheader)+FOR_ITER@336 → 出口 556
        ...  try: rename(src,dst) except OSError: ... # 163-170
    rename(self._filename, self._filename + '.1')    # 171  块556（与 198 同文本的第二份拷贝）
    self._open('w')                                  # 172
```

## 2. 已确认事实（磁盘上可复算）

### 2.1 丢的就是 break 与 latch（`D:/Temp/r20/logs/missA.txt`）
多重集差里**只有两条** orig 独有且 decomp 无对应体的跳跃：
`+1 JUMP_FORWARD to 302`（break）、`+1 JUMP_BACKWARD to 102`（外层 latch）。
其余 ± 全是同一指令在两个世界的偏移改名：`198↔446`、`556↔552`、`336↔226`、`548↔438`、`544↔434`。

### 2.2 "20 条对 1 条"的对齐 = 整体搬迁，不是丢失（本次实测补充解释）
`missA.txt` 的 `replace orig[29:49] decomp[29:30]` 把 20 条 orig 指令只对齐到 1 条
（`POP_JUMP_FORWARD_IF_FALSE to 446`）；这 20 条 = 4 条控制流
（`POP_JUMP→196` / `POP_TOP` / `JUMP_FORWARD→302` / `JUMP_BACKWARD→102`）
+ 16 条 for/else 臂实体（`rename … CALL / POP_TOP / self._open('w') / POP_TOP / LOAD_CONST None / RETURN_VALUE`）。
那 16 条并没有丢：它们出现在 `insert orig[119:119] decomp[101:117]`，即**被搬到函数尾部**
（else 臂入口 198 → decomp 里的 446/552 两份同名拷贝，故 orig 的 `FOR_ITER to 198/556`
被换成 decomp 的 `FOR_ITER to 552/446`）。逐条核账：

| 项 | orig | decomp | 说明 |
|---|---|---|---|
| else 臂 16 条 | @198（序列中段 29..44） | @446/552（尾部 101..116） | **搬迁**，条数不变 |
| break 的 `POP_TOP`（迭代器清理） | @33 | @107 | **搬迁**，`POP_TOP` 多重集两侧相等 ⇒ 非噪声指令多重集差里不出现 |
| `JUMP_FORWARD→302`（break 目标） | 1 | 0 | **真丢** −1 |
| `JUMP_BACKWARD→102`（外层 latch） | 1 | 0 | **真丢** −1 |
| 合计 | 119 | 117 | ⇒ delta = **−2**，与尺子打印值完全吻合 |

### 2.3 base 的区域层错误（`D:/Temp/r20/logs/regA.txt`）
外层 `LoopRegion@102`：`has_break=False`、`break_blocks=[]`、
`body_blocks=[102,104,192,196,302,336,338,396,428,556]` —— **把 for/else 之后的全部代码
（302 内层循环、556 循环后拷贝）吞进了循环体**；同时 `IfRegion@104` 的 `merge_block=302`。
根因在 `core/cfg/region_analyzer.py::_collect_natural_loop_body`（定义于 6101）：
- 6172 `if _bt in _exit_reachable` 判 False：`_exit_reachable` 只有 `{198}`（198 以 RETURN 终止，无后继）；
- 6174 `elif _bt not in _fwd_candidates` 判 False：6140-6154 的 BFS **从 fall_through=104 出发会穿过
  break 块 192 的无条件跳转**，于是 302 被登记成"循环内前向块"；
- ⇒ `_break_targets=∅` ⇒ 6256 分支不走，落到 6258 `_cand in _return_reachable`：
  `_has_return` 抓到 556（含 RETURN_VALUE），`_return_reachable` 沿前驱回溯
  556←336←{302,428,544}←192… **把 302/336/396/428/556 全部拉进 body** ——这就是 2.2 里"搬迁"的成因。

### 2.4 上一棒候选 c_a1 为何塌到 50（本次实测新结论）
c_a1（在 6172 加"裸出口块即 break"判据）之后区域层是**对的**：
```
LoopRegion@102  body_blocks=[102,104,192,196]  break_blocks=[302]  has_break=True
AST: For(body=[Assign, If(body=[Break, For(内层), Expr, Expr])], orelse=[Expr,Expr,Return])
产物文本: if os.path.exists(src): / break / <内层 for 与循环后代码全部缩进在 break 之后>
```
⇒ **分析器那一半是对的**（循环体、for-else、break 全部正确）；塌到 50 是因为
`break` 之后又被拼进同一条臂的代码成了不可达死代码，被 **CPython 3.11 编译器的死代码消除**删掉
（119→50）。**不是**分析器把区域拆坏。上一棒"region_analyzer:6172 已被证伪"的判断由此被推翻：
它只证伪了"单独改分析器能修好"，没证伪分析器判据本身。
（上一棒的生成器补丁打在 `region_ast_generator.py:20604` `continue`→`break`，
与 c_a1 产物逐字相同 ⇒ 对本形状无效。）

### 2.5 真正把循环后代码塞进 then 臂的发射点（本次 settrace 实测，`D:/Temp/r20b/logs/callsite_ca1.txt`）
```
blk=302  _mark_with_exit_return_explicit via
   _generate_block_statements:41563 <- _if_generate_normal:16999 <- _generate_if:11112
   <- _generate_region:3046 <- _loop_handle_child_region_entry:10654
region@336 _generate_region via _generate_block_statements_body:41649 <- ... <- _if_generate_normal:16999
```
即 `core/cfg/region_ast_generator.py:16988-17006`（`_if_generate_normal` 的
**"W15-C：then-独占 merge 块并进 then 臂"**）：
```python
16988  if (getattr(region, 'merge_block', None) is not None
16989          and self._merge_block_is_then_exclusive(region)):
...
16997      self.generated_blocks.discard(region.merge_block)
16999      _merge_then_stmts = self._generate_block_statements(region.merge_block)
17004      then_stmts = _kept + _merge_then_stmts      # ← 无条件拼到臂尾
```
它跑在**同一函数已经在 16934-16942 做过"臂内终止语句截断"**之后：
```python
16934  if then_stmts:
16935      _terminal_idx = None            # 找 Continue/Break/Return/Raise
16937          ... .get('type') in ('Continue','Break','Return','Raise')
16940      if _terminal_idx is not None and _terminal_idx < len(then_stmts) - 1:
16941          _then_terminal_overflow = then_stmts[_terminal_idx + 1:]
16942          then_stmts = then_stmts[:_terminal_idx + 1]
```
且 17482-17486 已有 `_then_terminal_overflow` 的"if 之后再发射"通道。
⇒ **同层次上"臂尾是终止语句 ⇒ 不得再往臂里拼代码"这条既有判据，在 16988 处没有被复用。**
`_process_if_blocks:20541` 是同一判据的第三处实例（`if stmts and stmts[-1] in (Break,Continue,Return,Raise): continue`）。
三处同层同判据，只有 16988 漏 ⇒ 按 mandate"同层同结构必同结论 + 优先接线既有判据"，(b) 就是补这个漏。

### 2.6 sys.settrace 反证（`D:/Temp/r20b/logs/wherebrk_ca1.txt` + 上一棒 `where_gen_A.txt`）
base 核下 `perform_rollover` 的 Break/Continue 发射点命中 **0 次** ⇒ base 连 break 都没识别（与 2.3 一致）；
c_a1 核下命中 1 次：`region_ast_generator.py:20604 _process_if_blocks reg=IfRegion(e=104,m=302)`。

## 3. 已排除
- ~~Break/Continue 发射层丢指令~~（2.6：base 根本没发射过）。
- ~~`region_analyzer:6172` 的候选会因"区域被拆坏"而塌方~~（2.4：塌方在生成器 16999，分析器结果是对的）。
- ~~只改生成器够用~~（4. 表格 `g1`：117/125，break 仍未识别，两孪生不翻）。
- ~~上一棒 `region_ast_generator.py:20604` `continue`→`break` 补丁~~（与 c_a1 产物逐字相同，无效）。
- 名字/常量/偏移匹配型规则（mandate 禁止；提案两处均为纯结构判据）。

## 4. 候选与实测（全部为本次打印值，非推断）

镜像核构建在 `D:/Temp/r20b/mirror/`（`git archive HEAD core bytecode pycdc.py _r10_strict_check.py | tar -x`，
只改副本；构建脚本 `D:/Temp/r20b/probes/r20b_mk.py` + `r20b_mk3.py`）。

```
twin  core              perform_rollover                      尺子原文
A     base(=HEAD)       orig=119 decomp=117  [seq_len]        ← 缺陷
A     c_a1(仅分析器)     orig=119 decomp=50   [seq_len]        ← 塌方（死代码被编译器消除）
A     g1 (仅生成器)      orig=119 decomp=117  [seq_len]        ← 无效（break 仍未识别）
A     f1 (两半,宽判据)   orig=119 decomp=119  OK               ← 修好，但全量 A/B broken=1（见 4.3）
A     f3 (两半,收窄)     orig=119 decomp=119  OK               ← 最终提案
B     base(=HEAD)       orig=127 decomp=125  [seq_len]
B     c_a1              orig=127 decomp=52   [seq_len]
B     g1                orig=127 decomp=125  [seq_len]
B     f1                orig=127 decomp=127  OK
B     f3                orig=127 decomp=127  OK               ← 最终提案
```
⇒ **两半缺一不可**：`g1` 单独 117/125、`c_a1` 单独 50/52、`f1/f3` 119/127。
f3 的产物（`D:/Temp/r20b/run/f3/{a,b}_handlersOK.py`）与 §1 的真实源码逐字一致
（`if os.path.exists(src): break` / `else:` 臂 / 循环后内层 for 全在正确层级）。

### 4.1 提案 R20-A（= 镜像 `f3`；两处，各自同层次、同判据，均为"接线既有判据"而非新发明）

**(a) 分析器 `core/cfg/region_analyzer.py:6172-6175`**（`_collect_natural_loop_body` 内）
现状两条判据都判 False（§2.3）。把 `if/elif` 改写成三析取项的单个 `if`，追加第三条
**结构**析取项：跳转块自身是 CPython 3.11 里 `for` 内 `break` 的固定 codegen 形状
（去噪后 = **至少一条 `POP_TOP`（迭代器清理）+ 恰好一条无条件前向跳转**）⇒ 其目标就是 break 出口。
不看名字、不看常量、不看偏移。
```python
                                if (_bt in _exit_reachable
                                        or _bt not in _fwd_candidates
                                        or _r20_is_break_stub_block(_bb)):
                                    _break_targets.add(_bt)
```
辅助谓词（模块级，`class` 之前；镜像里落在 `region_analyzer.py:91`）：
```python
_R20_NOISE_OPS = frozenset(('NOP', 'CACHE', 'EXTENDED_ARG', 'PRECALL', 'RESUME'))
_R20_FWD_JUMPS = frozenset(('JUMP_FORWARD', 'JUMP_ABSOLUTE'))

def _r20_is_break_stub_block(bb):
    core = [i for i in bb.instructions if i.opname not in _R20_NOISE_OPS]
    if len(core) < 2:                 # ← 收窄点：必须含 >=1 POP_TOP
        return False
    if core[-1].opname not in _R20_FWD_JUMPS:
        return False
    return all(i.opname == 'POP_TOP' for i in core[:-1])
```
`_bb` 就是 6156 循环里已有的"块"变量（不新增遍历维度）。6163-6171 的既有注释记录了
一条**历史误判**（`create_daily_stats` 偏移 196 曾被当成 break 目标），正是第②判据要挡的；
新析取项只在该块本身是 `for`-`break` 桩时才放开，且：电池 `r20a_10_anchor_create_daily_stats`
在 HEAD 与 f3 两侧都是 **MATCH**（它就是这条历史误判的守卫），全量 A/B `broken=0`。

**(b) 生成器 `core/cfg/region_ast_generator.py:16988-16989`**（W15-C splice）：
**臂尾已是终止语句时不得再并入 merge 块**。不是新判据 —— 同一函数 16934-16942 已用
`('Continue','Break','Return','Raise')` 做臂内截断，`_process_if_blocks:20541` 用同一集合
做"终止后不再发射块"，只有 16988 漏用（§2.5）。
```python
                if (getattr(region, 'merge_block', None) is not None
                        and self._merge_block_is_then_exclusive(region)
                        and not (then_stmts
                                 and isinstance(then_stmts[-1], dict)
                                 and then_stmts[-1].get('type') in
                                     ('Break', 'Continue', 'Return', 'Raise'))):
```
跳过后 merge 块不再被标 `generated`，由外层区域序列正常发射 ⇒ 循环后代码回到函数层级。

**符合四条区域归约原则**：(a) 只是把已存在的 break 出口登记为 break（不新增区域嵌套、不改归约次序）；
(b) 只是**取消**一次跨层次拼接，让 merge 块回到它本来的父区域层级 —— 内层→外层次序、
"每块只属于一个区域"、"嵌套区域在父层是单一抽象节点"、"父层 then/else 只引用子区域入口块"均未被触碰。

### 4.2 四道验收门禁 —— 全部实测通过（f3）

```
门禁1 孪生 A：  a  f3  <module>.RotatingFileHandler.perform_rollover  orig=119 decomp=119  OK
门禁1 孪生 B：  b  f3  <module>.RotatingFileHandler.perform_rollover  orig=127 decomp=127  OK
                （D:/Temp/r20b/logs/f3_twins.txt）
门禁2 整文件唯一尺子 check_pyc：
                [f3] twin a core=f3 functions=30 ok=29 bad=1
                       <module>.TWHThreadController._target [seq_len] orig=192 decomp=190   ← 本轮豁免的已知残差
                [f3] twin b core=f3 functions=17 ok=17 bad=0                                  ← 整份文件零缺陷
门禁3 电池 26 项（同 `run_all.py`，双向自检 + 表选择随 --core）：
                BATTERY pythoncdc-main :: repros=26  MISMATCH=18  MATCH=8   ERROR=0  UNEXPECTED=0
                BATTERY f3            :: repros=26  MISMATCH=7   MATCH=19  ERROR=0  UNEXPECTED=0
                ⇒ 11 项翻正（01,02,03,04,05,06,12,13,14,15,16），0 项倒退
门禁4 全量 402 索引条目 A/B（8 路分块，`absum_f3b.txt`）：
                base tag=baseb records=402 sum(n_ok)=5985
                ==== cand f3b : improved=2 broken=0 signature-only=0  sum(n_ok)=5987
                  IMPROVED IQCommon/logger/handlers.pyc        28->29  remaining=['<module>.TWHThreadController._target']
                  IMPROVED IQEngine/utils/logger/handlers.pyc  16->17  remaining=[]
```

### 4.3 f1 → f3 的收窄过程（为什么 `POP_TOP` 是必需的）
`f1`（= c_a1 的宽判据：去噪后"恰好一条无条件前向跳转"即算 break 出口，`len(core)>=1`）
两孪生 119/127 通过，但全量 A/B **broken=1**：
```
==== cand f1b : improved=2 broken=1 signature-only=1  sum(n_ok)=5986
  BROKEN IQEngine/plugins/plugin_system_finance/slippage.pyc 19->18 newbad=['<module>.create_new_price.check_and_return']
==== cand c_a1 : improved=0 broken=1 signature-only=2      （上一棒已有数据，同一处弄坏）
==== cand g1b : improved=0 broken=0 signature-only=0 sum(n_ok)=5985   （本次重跑，我的镜像）
```
⇒ 弄坏 slippage 的是**分析器那一半**，生成器守卫单独是无害的（g1b broken=0）。
`slippage.check_and_return` 的 CFG（`D:/Temp/r20b/logs/slip_cfg_base.txt`）：
```
 off=   96 last=POP_JUMP_FORWARD_IF_FALSE 150  succ=[150,124]  ← 链式比较 numbers[i] <= value < numbers[i+1]
 off=  124 last=JUMP_FORWARD 130               succ=[130]      ← 块 124 = [JUMP_FORWARD 130]，**无 POP_TOP**
 IfRegion entry=66 merge=130  then_blocks=[124]
```
块 124 是链式比较的 out-of-line 臂桩（§1 里提到过的那类"只有 `JUMP_FORWARD`、不带迭代器清理"的桩），
被宽判据误认成 `break` ⇒ 产物 `if numbers[i] <= value < numbers[i+1]: break / return numbers[i] / else: return value`
（`slip_f1.txt` 与 `slip_c_a1.txt` 逐字相同，orig=38 decomp=35）。
`break` 语义上也讲不通：该循环根本没有迭代器需要在此处清理。
**收窄 = 要求桩里至少有 1 条 `POP_TOP`**（CPython 3.11 的 `break` 位于 `for` 内时必须弹掉迭代器；
`FOR_ITER` 只在耗尽时弹自身）⇒ `f3` 在同一处保持 MATCH，全量 A/B `broken=0`。
`f3` 也顺手把 `signature-only` 从 1 收敛到 0（scheduler.pyc 那条在 f1 下签名漂移、f3 下不漂移）。

### 4.4 电池（26 项，HEAD 真值表 `EXPECT` / 候选真值表 `EXPECT_CAND`）
- 双向自检：每条 EXPECT 键都有同名 `r20a_*.py`，每个 `r20a_*.py` 都有键，且值非 None；<20 项直接 rc=2。
- 表随 `--core` 选择：仓库核用 `EXPECT`，镜像核用 `EXPECT_CAND`。HEAD 与 f3 两侧 `UNEXPECTED=0`。
- `r20a_10_anchor_create_daily_stats` 在 HEAD 上是 **MATCH** ⇒ 它是**守卫**（防过宽），名字保留历史含义，注释已说明。
- 我实测 `r20a_02_anchor_rollover_shape` 在 HEAD 上 **MISMATCH（orig=112 decomp=110）**，
  与 fix engineer 的"不重现"说法相反；已按我的打印值登记为 MISMATCH。

| 项 | HEAD | f3 | 类别 |
|---|---|---|---|
| 01 anchor_for_else_bare_break | MISMATCH 38/34 | MATCH | 锚点（翻正） |
| 02 anchor_rollover_shape | MISMATCH 112/110 | MATCH | 锚点（翻正） |
| 03 anchor_break_target_is_next_loop | MISMATCH 53/51 | MATCH | 锚点（翻正） |
| 04 anchor_tryexcept_in_body | MISMATCH 69/65 | MATCH | 锚点（翻正） |
| 05 anchor_nested_if_break | MISMATCH 40/36 | MATCH | 锚点（翻正） |
| 06 anchor_method_in_class | MISMATCH 122/120 | MATCH | 锚点（翻正） |
| 07 neg_break_target_shared | MISMATCH 32/7 | MISMATCH 32/7 | 同族别因（负例，防过宽） |
| 08 neg_for_else_no_break | MATCH | MATCH | 守卫 |
| 09 neg_plain_for_break | MATCH | MATCH | 守卫 |
| 10 anchor_create_daily_stats | MATCH | MATCH | 守卫（HEAD 即 MATCH） |
| 11 neg_break_inside_except | MISMATCH 43/36 | MISMATCH 43/36 | 同族别因 |
| 12 unconf_twinb_method_call | MISMATCH 40/38 | MATCH | 孪生 B 形状（翻正） |
| 13 anchor_two_bare_exit_jumps | MISMATCH 37/36 | MATCH | 锚点（翻正） |
| 14 anchor_break_target_is_while | MISMATCH 38/46 | MATCH | 锚点（翻正） |
| 15 anchor_break_target_is_try | MISMATCH 49/45 | MATCH | 锚点（翻正） |
| 16 anchor_elif_arm_break | MISMATCH 39/38 | MATCH | 锚点（翻正） |
| 17 anchor_nested_for_else_double_break | MISMATCH 47/40 | MISMATCH 47/39 | 同族别因（部分改善，未翻正） |
| 18 anchor_break_with_handler_after | MISMATCH seq_diff #17 | MISMATCH seq_diff #17 | 同族别因 |
| 19 neg_bare_jump_merge_in_body | MATCH | MATCH | **本轮新增守卫：正是 f1 弄坏 f3 不弄坏的形状** |
| 20 neg_nested_break_target_outer_body | MATCH | MATCH | 守卫 |
| 21 neg_while_true_break | MISMATCH 23/19 | MISMATCH 23/19 | 同族别因 |
| 22 neg_while_else_break | MATCH | MATCH | 守卫 |
| 23 neg_chain_compare_merge | MISMATCH 29/26 | MISMATCH 29/26 | **链式比较守卫**（slippage 同族，f3 不弄坏） |
| 24 neg_if_arm_return_in_loop | MATCH | MATCH | 守卫 |
| 25 neg_try_finally_in_body | MATCH | MATCH | 守卫 |
| 26 neg_break_in_nested_except | MISMATCH 48/46 | MISMATCH 48/46 | 同族别因 |

## 5. 仍开放（**不阻塞本提案**，逐条都是"另一次缺陷"）
1. 电池里 7 项在 f3 下仍 MISMATCH：`07`(32→7) `11`(43→36) `17`(47→40，f3 下 47→39，量级未变)
   `18`(seq_diff #17) `21`(23→19) `23`(29→26) `26`(48→46)。
   共同点：break 出口块**不止一个**，或出口块落在 `except`/`while` 等别的区域种类里，或链式比较与循环出口共享 merge。
   全量 A/B 证明这些形状在语料里**没有**被 f3 触碰（base 也是 MISMATCH ⇒ 非回归），属后续轮次。
2. `_if_generate_normal` elif 链返回路径 ~17134 还有一处同形状 splice。f3 未守该处已通过
   两孪生 + 26 项 + 402 条目 ⇒ 本形状不经过它；是否同时守，建议下一轮以"17134 处能否构造出翻正例"决定
   （**不要**为不重现的形状预先加守卫，那正是过宽启发式的来源）。
3. `TWHThreadController._target`（orig=192 decomp=190）为上一棒已登记的独立残差，本轮按 mandate 忽略。

## 6. 复现命令（全部只读 / 只写我自己的目录）
```bash
# 孪生 + 门禁1/2
D:/Python/python.exe test_repros/round20_rollover/run_all.py                 # HEAD，期望 UNEXPECTED=0 rc=0
D:/Python/python.exe test_repros/round20_rollover/run_all.py --core D:/Temp/r20b/mirror/f3   # 候选，同
# 门禁4（402 条目 8 路 A/B，各 ~75-155 s）
D:/Python/python.exe D:/Temp/r20/probes/r20_par.py <tag> <mirror> ; D:/Python/python.exe D:/Temp/r20b/probes/r20b_sum.py <tag>
```
