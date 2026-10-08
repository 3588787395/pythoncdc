# Round 10 诊断票 B131 简报：`matcher.DefaultMatcher.match` 的 elif 臂 —— 块 2164 在同一区域内身兼两角

**范围：只诊断，禁改 `core/`，禁 git 写，不跑全量门禁。** Scratch：`D:/Temp/r131/`。
探针可复用（只读，HEAD 字节有效）：`D:/Temp/r129/probe_elif.py`、`D:/Temp/r129/probe_h.py`（后者插桩全部
`RegionASTGenerator` 实例与 `generated_blocks` 写入栈）。

## 一、B129 被否证的部分（必须先读，否则会重跑同一死路）

B129 把丢弃点钉在 `region_ast_generator.py:54896-54921`（`_cjb_skip_inline_if` 把条件递给无人读的
`_leading_operand` / 被丢弃返回值的 `_leading_guard_candidate`）。两名工程师各以三个变体实现过该判据，
**共同读数**：`matcher.pyc` 16/17 → 16/17（零翻转）、small34 1528 → 1525/1527（`jq_trans_module`
65/65→63/65、`trade_info_utils` 37/41→36/41 破坏），故按 §四.7 逐字节回滚，`core/` 现为封表值
`e9a8f65f6451bcc8` / `38a1d5142d132fd7`。实测否证三条：

1. 整条流水线里 `blk 2164` 的 `_generate_block_statements` **根本没走到 `:54896`**：它在 `:52172-52173`
   就因 `block in self.generated_blocks` 直接返回；第一次认领者是
   `_if_generate_elif_chain` 的 `self.generated_blocks.add(elif_boolop.merge_block)`（`:19307-19324`）。
   `DIAG_B128` 那条 377 事件 trace 是**单元级**生成器，不是模块级的实际认领路径 —— 这是本票的教训：
   认领者要用「插桩所有 generator 实例 + 打印写入栈」定位，不能只看一个单元的调用栈。
2. 把该认领去掉后语句**确实回来了**（产物出现 `if order.asset.symbol[:3] in ('688','689'):`），
   但它落在**前一个 `'300'` 臂体内**（臂边界错），仍 16/17 ⇒ 只治认领不够，还须治臂归属。
3. `trade_info_utils.create_user_code_iqe` 在 HEAD 是**正确**的，而它的形状同样走「静默认领」；
   任何「登记 ⇔ 被接手」的全称式实现都会把它改红 ⇒ 本票不得以全称判据为解，须以身份判据为解。

## 二、主代理 2026-10-08 02:21 在 HEAD 字节实测的区域事实（勿重推，可直接引用）

`build_cfg(match.co)` → 78 块；块 `@2164` 的归属（`probe_elif.py` 原样输出）：

```
BoolOpRegion with merge==tb: entry=2038 blocks=[2038, 2080]
        chain=[(2038,'and'), (2080,'and')] parent=IfRegion
IfRegion cond=2080 entry=2038 type=IF_ELIF_CHAIN parent=IfRegion   (blocks 共 11)
   elif_conditions=[2164]
   elif_bodies=[[2208, 2212, 2254, 2338, 2334, 2380, 2460]]
   elif_final_else=[]  then=[2160]  else=[2164, 2208, 2212, 2254, 2334, 2338, 2380, 2460]  merge=2464
   TB membership: condition_block=False  in elif_conditions=True  in elif_bodies=False
                  in elif_final_else=False  in then_blocks=False  in else_blocks=True
```

⇒ **同一个 `@2164` 同时是**：① 该 IF_ELIF_CHAIN 的 `elif_conditions[0]`（须发射成 `elif <test>:`），
② 同区域 `else_blocks` 的成员（须发射成 else 臂内容），③ 前置 BoolOp（`2038 and 2080`）的
`merge_block`（被 `:19324` 认领为「已生成」）。三种身份互斥，违反 `rules.md` §1.2 原则 2（每块唯一归属）。
另注：`:19318-19323` 的既有豁免只检查「`merge_block` 是否为 `self.regions` 中某区域的 `entry`」，
而 `@2164` 不是任何区域的 entry（实测）—— 所以该豁免**结构上不可能**命中本例；它的 docstring 自称
「不限于顶级区域」，而循环只遍历 `self.regions`，此注释/行为矛盾另记 Task 11。

## 三、要回答的四个问题（边做边写进本文件）

1. **渲染路径**：`match` 单元里这条链由 `_if_generate_elif_chain` 还是 `_if_generate_full_elif_chain`
   发射？给出实际命中的 `文件:函数:行` 与该函数读的是哪些列表（`elif_conditions`/`elif_bodies`/
   `else_blocks`/`elif_final_else`）。为何 `elif_conditions[0]` 的 test 没出现在产物里 —— 是被
   `generated_blocks` 挡住，还是被 `else_blocks` 路径当普通语句吞掉？
2. **臂边界**：为什么去掉认领后该臂体落进**前一个臂**内部？发射端按什么身份决定「臂体到此结束」
   （`merge_block`？下一个 `elif_conditions` 的入口？`JUMP_FORWARD` 落点？）给行号。
3. **`else_blocks` 的双重身份从哪来**：`region_analyzer` 里构造 IF_ELIF_CHAIN 的
   `elif_conditions`/`else_blocks` 的赋值处（`region_analyzer.py:22580` 一带、`:4115` 一带）分别用什么
   判据；`else_blocks` 是否本应只含「链后 else 臂」而错误地把 elif 条件块一并塞入（Python 的
   `elif` 在 AST 里就是 `orelse` 里的嵌套 `If`，故 **条件块本身属于 orelse 的第一个节点**）——
   若是，正确判据应表达为「`elif_conditions` 成员在 `else_blocks` 中以臂入口身份出现，不得再以
   普通语句块发射」，须给出这是分析端职责还是发射端职责的**依据**（不得凭「哪边改起来小」决定）。
4. **最小复现** ≤4 条并说明哪些复现：
   `if A and B: x() elif C: y()`（C 为单块条件，本例形状）、
   `if A and B: x() elif C: y() else: z()`、
   `for` 内上述链、对照 `if A: x() elif C: y()`（BoolOp 缺席 ⇒ 应已正确）。
   用本机 CPython 3.11.7 `py_compile` 生成 pyc，`python -X utf8 pycdc.py -o` 到 scratch 后
   `python -X utf8 scripts/pyc_verify.py single <pyc>` 读数；**不得**覆盖 `site-packages/` 下任何产物。

## 四、约束

单命令 ≤300s；`python -X utf8`，禁 `PYTHONIOENCODING`；读源码 `encoding='utf-8-sig'`；
禁任何 git 写；禁改 `core/`；禁「成员非 condition」这类无判别力计数（吞并证据须是
**身份 ∧ 产物 AST 有无对应语句**的合取，见 `DIAG_B128` Q0-Q1）；禁为让两文件好看而强行并案。
产出四样：宿主 `文件:函数:行`、误发条件的白名单表述（opcode／块末／后继／区域身份）、
是否静默豁免（若是即 `rules.md §1.5 C3` 违例，须同票封闭）、复现臂名单与逐臂读数。
