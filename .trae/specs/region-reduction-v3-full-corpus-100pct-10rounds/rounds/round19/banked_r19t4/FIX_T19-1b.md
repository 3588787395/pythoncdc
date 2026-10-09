# FIX T19-1b — `core/cfg/region_analyzer.py` 识别端：链式比较区域入口作为 run 的单名操作数

判决：**FALSIFIED**（阶段 3 未过：api_base 仍 27/28、strategy 仍 26/27，两文件均未翻转；
但本票把阻塞点从「父子争块 + 起链时序」纠正为**父子争块一条**，并把 api_base 的
or-run 实测折叠成功，代价是同单元的臂出口链在产物里丢失 hunk 0→1 / 落点 2→3）。

作用域：仅 `core/cfg/region_analyzer.py`。live 仓库未被本代理写入（实测其字节仍是
`640d33a77dcb71c2`）。交付文件 = 完整替换文件 `DELIVER/region_analyzer.py`
（sha16 `5ea802f2975b1f35`，32748 行，全 CRLF 32747 个换行、0 个裸 LF，
`py_compile` 通过 `doraise=True` 无异常）。另 re-bank 惰性单臂
`DELIVER/banked_c1_only_inert.py`（sha16 `100d747765765d6f`，产物与基线逐字节同）。

镜像：`D:/Temp/r19t4`（基线/电池）、`D:/Temp/r19t4m`（施加/测量），电池副本同相对深度。
测量器：`scripts/pyc_verify.py single <abs pyc> --source <pycdc 产物>` 与
`.trae/.../unit_diff.py <abs pyc> <dotted qualname> --prod <产物>`。
探针只在**独立进程**做（`probe/inject3.py`、`probe/inject4.py` 生成的打印副本跑在
`D:/Temp/r19t4m`，从不进 live 仓库；分析器内零 CFG 读取，只 print 已取到的对象字段）。

---

## 0 判据原文（即代码注释原文，三处同一身份判据，无平行认领表）

### C1 `_boolop_next_operand_cc_region`（新方法）+ claim 守卫放行（`_detect_boolop_conditional_chain` 内）

```
        # [R19-1b-C1 修复·链式比较区域入口是本 run 的单名操作数] 区域归约算法原则 1
        # （自底向上归约）+ 原则 3（嵌套即抽象节点）+ 原则 4（入口引用语义）：
        # 链式比较区域由 _identify_chained_compare_regions 在 boolop 识别**之前**装配
        # （analyze() 固定相位序 chained_compare -> boolop -> ternary -> conditional），
        # 故其入口块在**任何一次** boolop 链走时刻都已登记认领。claim 守卫把这个入口
        # 当作断链理由时，`A or (a < b <= c)` / `A and (a < b <= c)` 的末名操作数永远
        # 进不了 op_chain：or-run 只剩前缀，链式比较退回 IfRegion 层级变成嵌套 if，
        # 各段短路边随之落到整条语句的统一出口而不是各自的体入口（落点差）。
        # 识别条件（只读同层区域表的角色身份：block 是某 IfRegion 的 entry，该区域
        # chained_compare_ops 至少两项、chained_compare_blocks 非空、merge_block 已解析；
        # 不看名称、不看字符串常量、不看绝对偏移、不用指令条数阈值）——与本方法下方
        # 既有 cc hop（`_cc_region` 分支）用**同一个**身份判据，不另立平行机构。
        # 归约方式：命中即放行该入口充当链的下一名操作数；下一步由既有 cc hop 把整条
        # 链式比较作为**单个抽象节点**接入链，其内部续块一律不进 op_chain
        # （`_cc_internal_hit` 守卫继续拦截），因此不违反原则 2（每块唯一归属）：
        # cc 子区域的内部块仍归子区域，BoolOpRegion 只把它的 entry 记为一名操作数。
        # 判定与兄弟 run 的发现顺序无关（cc 区域先于 boolop 全部装配完成），不做事后修补。
        # 反编译流程：run 操作数齐全 -> BoolOpRegion 发射单个 ast.BoolOp，父 IfRegion
        # 得到扁平条件；每名操作数的短路边回到真正的体入口、末段落空边回到 run 出口。
        # 未命中返回 None，调用方维持原 break，行为逐字节不变。
```

调用点：

```
            if not skip_claimed_check:
                # [R19-1b-C1] 下一名操作数若是**更低层链式比较区域的入口**，它不是断链
                # 理由，而是本 run 的单名操作数（判据与理由见
                # _boolop_next_operand_cc_region）；其余被认领块维持原 break。
                _r19_cc_operand = self._boolop_next_operand_cc_region(ft_succ)
                if ft_succ in claimed and _r19_cc_operand is None:
                    break
                if ft_succ in self.block_to_region and _r19_cc_operand is None:
```

### C2 cc hop 安全门的跨极性改写

```
                    # [R19-1b-C2 修复·跨极性候选改由成功落点认定成员身份] 上面的
                    # 「同出口」校验把链首末指令的跳转目标与本候选末指令的跳转目标直接
                    # 比对，隐含前提是**两者是同一种出口**。链首以 IF_TRUE 结尾（or run
                    # 的短路成功边，其目标 = 全 run 共同体入口 T）、本候选以 IF_FALSE
                    # 结尾（链式比较失败边，其目标 = run 的假出口）时前提不成立：两条边
                    # 按 CPython 降级永不同块，比对恒假，or-run 的链式比较末名操作数永远
                    # 被剥掉（同 [R53-A] 对「跨 run 比较不构成证据」的论证，此处落在 cc
                    # hop 的安全门上）。成员身份改由**成功落点**这一结构事实认定：
                    # 链首成功边目标 T 与链式比较区域「比较成立」的落点（其 merge_block，
                    # 必要时越过承接 run 接线的纯 JUMP_FORWARD 控制块）必须是同一块；
                    # 且本候选的失败边必须已在 run 的另一侧（非 T）。判据只读两侧末指令
                    # 的跳转方向族与已解析区域角色，无名称/常量/绝对偏移/指令计数。
                    # 命中即保留该操作数并交由紧随其后的既有 hop 消费；不命中维持原
                    # chain.pop()+break。同极性候选走原「同出口/等价出口」校验，逐字节不变。
```

### C3 R59「or 表达式 vs if/elif」分离器的成功落点比对

```
                # [R19-1b-C3 修复·链式比较末名操作数按成功落点比对] R59 用「首名短路
                # 目标 == 次名落空边」分离 `A or B`（两名成功沿汇入同一体入口）与
                # if/elif（两名体入口不同）。该读法默认次名操作数的落空边就是它的
                # 成功落点；次名是**链式比较区域入口**时不成立——它的落空边是链式比较
                # 的内部续段（左值求值块，CPython 对 `a < b <= c` 的降级必然如此），
                # 成功落点在整条链式比较之后。拿内部续段去比对会把合法 or-run 判成
                # if/elif 并丢弃，链式比较退回 IfRegion 层级的嵌套 if。
                # 识别条件（同层区域角色身份 + 两条成功沿同落一块；无名称、无常量、
                # 无绝对偏移、无指令计数）：chain[1][0] 是某链式比较区域的 entry
                # （判据与 C1 同一个 `_boolop_next_operand_cc_region`），且该区域的
                # 成功落点（共用件 `_boolop_cc_success_landing`）正是首名短路目标
                # _first_jt。
                # 归约方式：命中即 return chain —— 两名操作数的成功沿汇合到同一体
                # 入口，正是 R59 要证的「or 表达式」事实；不命中维持原 return None，
                # if/elif 分离行为逐字节不变。判定发生在识别时，不事后改写区域。
```

共用件（C2/C3 各写一遍会违反「一个判据一处复用」）：

```
    def _boolop_cc_success_landing(self, cc_region):
        # [R19-1b 共用件] 一条链式比较区域「比较成立」之后的落点：其 merge_block，
        # 必要时越过**纯控制 JUMP_FORWARD 跳板**（除跳转与噪声外不承载任何指令的
        # 接线块）取真正的落点；承载语句的块本身就是体入口，不越过。只读该区域已
        # 解析的角色块与该块末指令，与兄弟 run 的发现顺序无关。C2/C3 共用这一份
        # 算法，不在两处各写一遍。
```

---

## 1 阶段 1：未打补丁镜像复现封存基线（实测，`D:/Temp/r19t4`，core sha16 `640d33a77dcb71c2`）

| 读数 | 镜像 pristine | 封存 |
|---|---|---|
| api_base | `status=failure units=27/28` | 27/28 ✔ |
| strategy | `status=failure units=26/27` | 26/27 ✔ |
| round14/repro | `RED=9 / 9` | 9/9 红 ✔ |
| round14/repro_arm | `GREEN=0 RED=3 / 3` | 0/3 ✔ |
| round14/repro_ccneg | `GREEN=3 RED=1 / 4` | 3G/1R ✔ |
| round18/repro_retbreak | `GREEN=2 RED=2 DRIFT_VS_BASELINE=0 / 4` | 2G/2R ✔ |
| round19/repro_orderapi | `GREEN=2 RED=3 / 5` | 2G/3R ✔ |
| round19/repro_tail | `GREEN=13 RED=0 / 13` | 13G/0R ✔ |

基线 unit_diff（逐字）：

```
len orig=1881 prod=1881 delta=0
   ~ orig[193] @994    POP_JUMP_FORWARD_IF_TRUE   ->idx219    | prod[193] @994    POP_JUMP_FORWARD_IF_TRUE   ->idx254
   ~ orig[197] @1006   POP_JUMP_FORWARD_IF_TRUE   ->idx210    | prod[197] @1006   POP_JUMP_FORWARD_IF_TRUE   ->idx254
hunks=0 landings=2 judge_diff=True

len orig=288 prod=288 delta=0
   ~ orig[70] @522    POP_JUMP_FORWARD_IF_TRUE   ->idx87     | prod[70] @522    POP_JUMP_FORWARD_IF_TRUE   ->idx153
   ~ orig[74] @534    POP_JUMP_FORWARD_IF_TRUE   ->idx87     | prod[74] @534    POP_JUMP_FORWARD_IF_TRUE   ->idx153
   ~ orig[180] @992    POP_JUMP_FORWARD_IF_TRUE   ->idx197    | prod[180] @992    POP_JUMP_FORWARD_IF_TRUE   ->idx263
   ~ orig[184] @1004   POP_JUMP_FORWARD_IF_TRUE   ->idx197    | prod[184] @1004   POP_JUMP_FORWARD_IF_TRUE   ->idx263
hunks=0 landings=4 judge_diff=True
```

## 2 对票据前提的实测纠正（探针独立进程，逐 break 打点）

票据/存档把两个卡点写成 ①父 `IfRegion e=992` 认领 @1040、②`chain_start B@992 -> []`
起因于「走链时 `block_to_region[B@996]` 还不是 BoolOpRegion」（发现顺序）。**②在
pristine 字节上不成立**：pristine 里根本没有 in-analyzer 的 `_t19_*` 判据可读
`block_to_region[B@996]`；真实断链点是 claim 守卫读到的**链式比较区域入口**：

```
[TRC ENTER] 992 996 [(992, 'or')]
[TRC FT] 992 996 1008 True [('IfRegion', 1008, 2, [1024], 1040)]   # ft_succ=B@1008 已被认领
[TRC BRK] 992 29977                                                 # pristine 行号：if ft_succ in claimed: break
```

`('IfRegion', 1008, 2, [1024], 1040)` = 该 IfRegion entry=B@1008、`chained_compare_ops`
两项、`chained_compare_blocks=[B@1024]`、`merge_block=B@1040` —— 正是既有 cc hop 要
消费的**单个抽象节点**。同样地 start=996 的 or 走也在同一处断（`[TRC FT] 996 996 1008`）。
该认领由 chained_compare 相位先行登记，**与兄弟 run 的偏移发现顺序无关**（相位序固定），
所以 C1 是顺序无关的判据，不是「把顺序修好」。

施加 C1..C3 后的走链实测（`patched/v_c123.py` 行号）：

```
[TRC FT] 996 996 1008 True [('IfRegion', 1008, 2, [1024], 1040)]
[TRC ENTER] 996 1008 [(996, 'or')]          # 放行，cc 入口成为下一名操作数
[TRC ENTER] 996 1782 [(996, 'or'), (1008, 'and')]   # 既有 cc hop 消费后 hop 到函数尾
```

即链成为 `[(996,'or'),(1008,'or')]`（`is_pure_or_chain` 分支把末名重标为 'or'），
R59 处 C3 命中并 `return chain` → BoolOpRegion entry=B@996 建立。
父走（start=992）在 C2 处按设计被拦（`[TRC POP] 992 29864`：cc 成功落点 @1040 ≠
链首目标 @1098），链退回 `[(992,'or'),(996,'or')]` 后返回 None —— 父 and-run 仍不建，
这与「嵌套渲染即可复原落点」一致，不是本票的失分点。

## 3 阶段 2：判据自身 repro（landings 变化，逐字）

施加 C1..C3（`D:/Temp/r19t4m/prod/api_c123.py`）：

```
- @1128    STORE_FAST                     _last_real_59
   ~ orig[193] @994    POP_JUMP_FORWARD_IF_TRUE   ->idx219    | prod[193] @994    POP_JUMP_FORWARD_IF_TRUE   ->idx218
   ~ orig[206] @1032   POP_JUMP_FORWARD_IF_FALSE  ->idx219    | prod[206] @1032   POP_JUMP_FORWARD_IF_FALSE  ->idx218
   ~ orig[209] @1038   JUMP_FORWARD               ->idx219    | prod[209] @1040   JUMP_FORWARD               ->idx306
hunks=1 landings=3 judge_diff=True
```

条件侧**确实折叠成功**（产物 `if not include:` 内层变成
`if _query_date > pm_close_market_datetime or am_close_market_datetime < _query_date <= pm_open_market_datetime:`
且臂体 @1040 已在其内），@994 的落点从 idx254 移到 idx218（= 原 idx219 的 @1098 邻位，
差 1 个索引），@1006 那条落点差**消失**。代价：`@1098..@1198` 的 elif/else 语句组
整段不再发射（hunk 0→1，`- @1128 STORE_FAST _last_real_59` 等）。

strategy 侧施加后与基线逐字相同（`hunks=0 landings=4`，26/27）：本判据不触及
它（其阻塞是 `and`/W14-A 尾钳方向，见存档 §2.2）。⇒ **阶段 2 部分达标**（api_base
@1006 那条落点差消掉，但该单元 `judge_diff` 仍在且 hunk 增加；strategy 无变化）。

## 4 阶段 3：落点条未达（实测）

| 变体（每变体只差一个 call site，helper 定义恒随附，为逻辑死码不改产物） | api_base | strategy |
|---|---|---|
| pristine | 27/28, hunks=0 landings=2 | 26/27, hunks=0 landings=4 |
| C1 | 27/28, hunks=0 landings=2（产物与基线同文） | 26/27（未测，判据不触及其走链） |
| C1+C2 | 27/28, hunks=0 landings=2（产物与基线同文） | 26/27 |
| C1+C2+C3（交付件） | **27/28**, hunks=1 landings=3 | 26/27, hunks=0 landings=4 |

⇒ **无文件翻转**，按验收阶梯止于阶段 3（阶段 4 只跑电池，数字见 §5；面板 15 文件
未跑，不作落地理由）。

## 5 阶段 4：六电池（基线 vs 交付件同跑，镜像内）——零漂移

| 电池 | pristine | 施加 C1..C3 |
|---|---|---|
| round14/repro | RED=9/9 | RED=9/9 |
| round14/repro_arm | GREEN=0 RED=3/3 | GREEN=0 RED=3/3 |
| round14/repro_ccneg | GREEN=3 RED=1/4 | GREEN=3 RED=1/4 |
| round18/repro_retbreak | 2G/2R DRIFT=0 | 2G/2R DRIFT=0 |
| round19/repro_orderapi | 2G/3R | 2G/3R |
| round19/repro_tail | 13G/0R | 13G/0R |

## 6 剩余闸门（写给下一手，本票实测到位）

**阻塞点唯一化 = 票据的 A，且只剩 A。** 需要的是识别端的父臂收集规则：
父 `IfRegion entry=B@992` 的 then 收集现在从 B@996（= 已在下层归约的 BoolOpRegion 的
entry）起步并沿后继下钻，吸进子区内部块（B@1024/B@1034/B@1036）与子区臂体 B@1040，
于是父区既没拿到 @1098 的 elif/else 出口链、又与子区争块。实测证据是 §3 的 hunk
（@1098 组语句整体消失）。落点复原需要的正确形状：父区 then=[子区 entry 引用]、
边界=子区 merge=B@1098、@1098 组作为父区的 else/elif 链在**父层**发射。

读过的候选机器与本票结论：
- `_collect_branch_blocks`（pristine :31494）docstring 明写「不使用 block_to_region
  排除，区域归属冲突由上层调用者处理」——所以**这里不是插平行认领表的地方**；
  改动应在调用侧（`_build_basic_if_region` / `_build_elif_region` 传入的
  `stop_set` / `get_if_branch_boundary_stop` 一族）：让「entry 是下层区域入口」的后继
  展开在**该下层区域的 merge_block** 处停住，并把该 merge 作为臂边界而非臂内块。
- `[R31-B]` 同层 stop-set 规则（pristine :20366、:22744 两处引用）是本票未走完的那条线：
  它管的是「终止臂的块不得被认领为臂内边界」，与本形态同族但方向相反（本形态是
  子区 merge 同时是父区 else 入口）。
- W14-A 尾钳（pristine :30227-:30260，`len(chain) >= 3` 且链首 IF_TRUE）在 C1..C3 之后
  不是本形态的阻塞点：api_base 的 or-run 只 2 名成员，未进该尾钳。
- 票据候选清单里的 `_main_inline_boolop_chain`（pristine :19271-:19616）**不可用**：
  它只交付单一 `op`（`{'blocks':[...], 'op': 'and'|'or'}`），结构上表达不了
  `not include and (X or Y)` 的混合极性；且其 and 游走硬要求链首 `IF_FALSE`
  （:19527-:19530）与后续成员非 `IF_TRUE`（:19577）、成员目标 == 链首目标（:19594），
  三处对本字形独立拒绝。要走这条路必须改生成端消费（`core/cfg/region_ast_generator.py`），
  该文件本票无权触碰。
- 强制 `merge = BoolOpRegion.merge_block` 的旧回归臂（存档 hunk #2）未在本票复现，
  本票也没有引入任何 merge 改写。

复现设施（可复用）：`D:/Temp/r19t4/probe/patch19.py`（按 hunk 组合出变体，字节级 CRLF，
锚点 count==1 断言）、`D:/Temp/r19t4/probe/inject3.py` / `inject4.py`（对 pristine 或
patched 文件按模式插入 `[TRC ...]` 打点，含 claim 归属与 cc 区域角色读数）。

## 7 判决

FALSIFIED — 阶段 3 未过：api_base **27/28**（hunks 0→1、landings 2→3，@1006 落点差消失
但 @1098 elif/else 语句组整体丢失）、strategy **26/27**（本判据不触及）。零电池回退
（6/6 读数与基线全同）。仍在 False 的具体判据不再是链侧谓词——C1/C2/C3 三处谓词实测
全部命中并建立了 `BoolOpRegion entry=B@996 op_chain=[(B@996,'or'),(B@1008,'or')]`；
失败发生在父层 `IfRegion entry=B@992` 的臂边界收集：它把子区 entry=B@996 的内部块
（B@1024/B@1034/B@1036）与子区臂体 B@1040 一并吸入，因此子区 merge=B@1098 没能成为
父区臂边界、@1098 起的 elif/else 链在父层无处发射。
