# MEASURED R19-3 —— 三张下一轮票的逐指令靶心（修好落点列后的新读数，全部只读复量）

工具口径：`unit_diff.py`（已修，qualname + `landings` 列）+ 独立进程 marshal/`dis` 普查；
判据本体＝`compare_pyc`（先套 NOP/EXTENDED_ARG/不可达清除，再 CFG 等价，再逐条 bytecode）。
本轮未动 core：`region_ast_generator.py 5066b1367b6de3c7`、`region_analyzer.py 640d33a77dcb71c2`。

## 1. `IQCommon/logger/handlers.pyc::<module>.TWHThreadController._target`（29/30，本文件唯一失败单元 ⇒ 整文件翻绿）

```
len orig=199 prod=197 delta=-2      hunks=1（≤2 条故不打印细目）landings=3
```

三个落点差全是**同 opcode 只换落点**，且落点全在函数末尾：

```
orig[83] @456 POP_JUMP_FORWARD_IF_FALSE -> idx193   | prod[81] @452 -> idx195
orig[90] @502 POP_JUMP_FORWARD_IF_FALSE -> idx195   | prod[88] @496 -> idx191
orig[93] @516 POP_JUMP_FORWARD_IF_FALSE -> idx197   | prod[91] @510 -> idx193
```

`LOAD_CONST None; RETURN_VALUE` 成对普查（同一 qualname，逐码对象）：

```
ORIG  TWHThreadController._target            len=199  pairs=7  at idx=[73, 75, 123, 191, 193, 195, 197]
PROD  TWHThreadController._target            len=197  pairs=6  at idx=[73, 121, 189, 191, 193, 195]
ORIG/PROD TWHThreadRotatingFileHandler._target  len=126 pairs=2  两侧相同（同文件另一单元，不受影响）
```

⇒ 原函数有 **7 条各自独立的 `return None` 出口**（3.11 不给 `return` 语句做尾巴共享：每条出口自带一对
`LOAD_CONST None; RETURN_VALUE`），产物只发出 **6** 条。缺失位置精确可定位：
原 idx **75** 处那一对——它紧跟 idx 73 的另一对（**两条相邻出口**），产物在 73 之后只剩一对，
即产物源码把两条相邻出口**并成了同一条 return**；其后 4 对两侧一一对应（121/189/191/193/195 ≡ 123/191/193/195/197），
只是被并掉的那一对造成 2 指令位移，于是三条条件跳转的名义落点集体错位（`landings=3` 是影子，不是三个独立缺陷）。

**这张票的判据形状**（依 [[in-analyzer-probes-perturb-cfg]] 只在独立进程量）：
某条件块的落空边/跳边指向一个「只做 `return None` 的出口块」，而该出口块的**前驱数≥2**且
它的**前驱中至少一个是另一条出口块的直接前驱**（即两条出口在原 CFG 里是两个独立抽象节点）；
此时不得把两条出口折叠成一条语句。此判据与前三次被实测否决的守卫不同：
先前动的是发射/剥离支（`_nested_merge_return_skip` 匹配数 0、两条 while 臂尾剥离器消融后逐字节不变、
`_is_return_none_join_block` 加臂后 8 文件面板全同），**没有一次针对「相邻两出口被并」**；
本读数第一次把缺陷钉在 idx 73/75 这一对上。开票前先答两问：
①原 CFG 中 idx 75 出口块的前驱是谁（是否即 @456/@502/@516 三条跳边之一）；
②产物源码在该处是一条什么语句（读 `handlersOK.py` 内 `_target` 对应行段，不读字节码猜）。

## 1b. 上票的关键补充读数（同一单元，独立进程 marshal/`dis` 复量）

缺失那对**只有一个前驱**，且相邻那对**零前驱（纯落空）**——这把本票与此前被否决的
「`return None` ⇒ 汇合」轴区分开：

```
@404（idx73/74，产物仍发的那对）：以它为落点的跳转 = 0 条；它由 idx72 @402
    POP_JUMP_BACKWARD_IF_TRUE ->@104 落空后**顺序进入**（即 while 尾测试的正常出口）
@408（idx75/76，产物缺的那对）：以它为落点的跳转 = 1 条，来自
    orig[17] @102 POP_JUMP_FORWARD_IF_FALSE
@412（orig line 75，下一条语句 `if sys.version_info[0]==3 …`）在其后顺序继续
```

⇒ 原字节码在此处是**两条各自独立、且前驱集合不同**的 `return None` 出口：
一条只能由前一块落空进入，另一条只能由一条条件跳转进入。产物把两者折叠成一条，
于是净少一对、三条远端跳转集体错位（`landings=3` 全为影子）。
**判据形状（开票前先对照否决记录，勿重复旧轴）**：不得用「某块是 `return None` 纯块 ⇒ 当作汇合尾」
（该轴已在本战役被实测否决，见 memory 的 falsified 轴清单与本仓 `REGISTER`/`tasks.md` §15-18）；
可用的是**前驱集合不对称**：两块同为纯返回块且相邻/同尾，但一块的前驱=「唯一落空边」、
另一块的前驱=「≥1 条条件跳转」⇒ 二者是两个独立抽象节点，折叠即丢出口。
开票还须回答：@102 那条跳转属于哪个区域（其真值边 @104 起 while 体），
以及产物源码在该区域给了什么语句（`handlersOK.py` line 27-40：`if sys.version_info[0]==3 and sys.version_info[1]==5:`
`while self.running:` … `return None` —— 只有一条 return，无 else 出口）。

## 2. `fly/data/quote.pyc::<module>.Quote.build_current_period_df`（86/92 之一，非整文件）

```
len orig=123 prod=113 delta=-10      hunks=1 landings=0
== replace orig[108..120 @516..@568] prod[108..110] del=12 ins=2
   - @518 LOAD_CONST 'is_open'   - @520 STORE_SUBSCR
   - @524 LOAD_GLOBAL NULL+pandas - @536 LOAD_ATTR DataFrame
   - @550 KW_NAMES - @552 PRECALL - @556 CALL - @566 STORE_FAST tmp
   + @514 POP_TOP  + @516 LOAD_CONST None
```

⇒ 函数**最后两条语句整条消失**（`tempdict['is_open'] = …` 与 `tmp = pandas.DataFrame(tempdict, index=…)`），
取而代之的是「弹栈 + 隐式返回」。这是**尾巴语句被吞**而非落点问题：与残余表 §具名 读数一致，
但本表把它从「共用尾」族里分出来——它 `landings=0`，与 `get_real_from_zeromq` 的
`exc_tb` 作用域族也不同，三者不能共用一条判据。

## 3. `IQCommon/util/trade_info_utils.pyc::<module>.kill_trade_process`（38/41 之一）

```
len orig=659 prod=659 delta=0   hunks=0 landings=2
```

纯落点残差，2 处，与 `api_base.get_history_df` 同属「同 opcode 只换落点」档；
该文件另有 2 个失败单元（`query_strategy_id` 内容差 2 hunk、`query_trade_strategy_info` 3 hunk + 1 落点），
故不产生整文件翻绿 ⇒ 优先级低于 §1/§2。

## 4. 排队结论（不改目标口径）

整文件翻绿候选按性价比：`api_base`+`strategy`（r19t4 施工中，落点 2/4）、
`klinedata`（r19t3 诊断中，1 内容 hunk + 2 影子）、`order_api`（r19t1 施工中，2 单元）、
**`handlers`（本文件 §1 新读数，第一次把缺陷钉到 idx 73/75 那对被并掉）**。
`quote`/`trade_info_utils`/`trade_live_broker`/`__init__`(risk) 只涨单元数。
