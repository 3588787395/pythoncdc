# FIX R19-T19-4 LANDED — 三元与「未闭合宿主调用前缀」融合同一块：跨度扩到栈平衡归零，整体归约为一条语句

工程师镜像 `D:/Temp/r19t1`；完整判据文本与其阶段读数见同目录 `FIX_T19-4.md`（原件入档）。
本文件只记**主代理自己复测过**的事实与安装凭据；门链读数在文末（跑出后填写，未跑出前不得引为判决）。

## 1. 安装凭据（install_deliver.py 逐文件记录，pre→post sha16）

```
core/cfg/region_ast_generator.py   5066b1367b6de3c7 -> b5795b6be150324f   py_compile OK
core/cfg/ast_generator_v2.py       e1e0dcda2e745298 -> beeaf14435e22922   py_compile OK
```

**两文件一体，缺一不可。** 我先把只装 `region_ast_generator.py` 的镜像当候选测了一次，
读数 `repro_orderapi GREEN=2 RED=3`（与基线同分）——**那是安装不完整造成的假否**；
补装 `ast_generator_v2.py` 后同一镜像立刻 `GREEN=5 RED=0`、`order_api 37/37`。
原因写在 `FIX_T19-4.md`：新路线把块指令交给 `expr_reconstructor.reconstruct(...)`，
而融合三元分支的折叠只在 `POP_JUMP_*_IF_NONE` 极性上被调用过
（`ast_generator_v2.py:755` 唯一调用点），`IF_FALSE` 极性两条臂的栈压回从未折叠，
`reconstruct` 返回垃圾；补丁把该极性接入**同一** open/track/close 机制，
开关 `fold_cond_jump_ternary` 默认关、`reset()` 清旗，故既有调用路径逐字节不变。

## 2. 判据（落进代码注释的口径，纯栈效应/指令族，无名字无常量无绝对偏移）

1. 区域条件块末为条件跳转，前向模拟块体得净深 R，跳转弹条件后**残留 L=R-1 ≥ 1**
   ——补上 `_ternary_nested_in_container_construction` docstring 第 3 条逃逸的另一半；
2. 沿 merge 链继续模拟，**第一个把栈深降到 L 以下的指令属调用消费族**（CALL/PRECALL/…）
   ⇒ 栈底那些元素是未闭合的宿主调用（接收者 + 已成型实参），不是「彼此独立的已求值表达式」；
   若先降到 L 以下的是其它族（STORE_*/POP_TOP/BINARY_SUBSCR…），返回 None 保持既有行为
   （如 `d[k] = (a if c else b)` 的赋值目标形状）；
3. 同一条链继续模拟到**栈深回到 0**，链上全部块（条件块 + 两侧臂块 + merge 块，
   含同一语句内的兄弟三元）的指令按 offset 排序，整体归约为**一个**表达式；
   模拟不可靠（效应不可得、栈下溢、臂非纯值块、链断裂/成环、跨度未闭合）一律返回 None。

## 3. 主代理自测读数（installed tree，非镜像）

```
repro_orderapi   GREEN=5 RED=0 / 5      （基线 2G/3R；o1/o4/o5 翻绿，o2/o3 保持绿）
order_api.pyc    status=success units=37/37   （基线 35/37；本文件唯一失败面清零）
repro_tail       GREEN=13 RED=0         （隐式 return/汇合尾护栏不动）
repro_arm        GREEN=0  RED=3         （与基线同）
repro_ccneg      GREEN=3  RED=1         （与基线同）
```

工程师另报：21 个语料文件基线臂/施加臂双臂对比 **0 下降**，且五个电池产物文本 `diff -rq` 逐字节相同
（该两-arm 产物我未在实时树复验——实时树正在跑门链，半重写产物不可判）。

## 4. 门链（label 19 vs 18）—— 未跑出前本节不作判决

`gate_chain.py 19 18` 于 00:13 启动（`regen` 阶段进行中：本文写作时 303/402 产物已按新代码重写）。
待填：`regen ok=/bad=`、`[units] 6584 -> ?`、`[files] 390 -> ?`、`REGRESSIONS/UNIT_REGRESSIONS/翻正单元`、
`quotation`、`small34`、`自证`、`pytest`。
任一档出现回退 ⇒ 逐字节回滚两文件（`install_deliver.py restore`，备份 sha 已存
`D:/Temp/r150/deliver_backup/`）并在此登记负极性。
