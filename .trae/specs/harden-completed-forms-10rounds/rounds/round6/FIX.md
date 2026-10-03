# Round 6.2 修复工程师报告（FIX.md）

## 本轮修复范围

封闭 Round 6.1 评审登记的 B29–B35 缺陷，目标 round6 全部 34 复现 100% MATCH + 零回归。
硬约束：**禁止任何启发式、禁止回退**——只允许结构事实判据（指令操作码形态链 /
控制流边性质 / 区域树归属），无名字/偏移白名单。

## 已封闭缺陷

### B33 await 挂起跨链合并（r6_12 aw_await_expr，6/6 MATCH）

**根因**：`async with mgr as f: return (await g(f)) + f` 的字节码链结构为

```
aenter 链 [setup@2, poll@14, resume/体首@22, poll@48, resume/junction@56]
  体首 blk@22 = STORE as绑定 f + 用户 await setup（LOAD g, LOAD f, CALL, GET_AWAITABLE）
  junction blk@56 = 续算片段（LOAD_FAST f, BINARY_OP +）
aexit 消费链 [setup@62(SWAP+LOAD_CONST None×3+CALL+GET_AWAITABLE), poll@88,
              owner@96(POP_TOP 丢 aexit 结果 + RETURN_VALUE 消费挂起值)]
```

挂起值跨越「体首→poll→junction」两段：junction 单块重建必然缺失左操作数
（漏斗错构 Expr(f)，BINARY_OP 静默丢弃）；B31 gate 对 junction 链被 B29 排除
（成员含 BEFORE_*）、对 aexit 链重建缺用户段——两既有路径均不可达完整语句。

**修复**（[Round6-B33] 单一漏斗，`_b33_await_owner_merged_stmts`）：

1. 判据链统一在链 owner（junction）上执行（结构事实，无名字/偏移白名单）：
   - 链成员含 BEFORE_WITH/BEFORE_ASYNC_WITH（B29 领地判据，纯用户链归 B31 gate）
   - junction ∈ region.with_blocks（跨区域链禁捕）
   - `_b31_continuation_owner(owner)` 延续形态
   - **as 绑定与用户 await setup 同块**：链成员中恰一块同时含 region.target 的
     STORE_* 与 GET_AWAITABLE——挂起跨链形态的结构事实；无 as 绑定或兼 setup
     块不唯一时交由既有路径（漏斗 + B32 已正确处理单块完整计算的挂起值）
   - junction 自身无 GET_AWAITABLE
   - junction 后继中恰一条 **aexit 消费链**：链 owner 去噪指令全集 ⊆
     {POP_TOP, RETURN_*} 且含 RETURN_*（协议结果丢弃 + 挂起值消费的结构事实）
2. 每块唯一归属改判：判据成立时整条链唯一归属 junction——owner 块发射合并
   语句，其余链成员块返回空列表禁独立发射（镜像 B31 gate 的空列表改判）。
3. 合并流 = 体首块（剥 as 绑定 STORE，Round5-08 判据）→ junction 的链成员
   用户段（整体跳过 poll 块，剥 RESUME/NOP/CACHE/PUSH_NULL/EXTENDED_ARG 与
   GET_AWAITABLE 后的 LOAD_CONST None 发送值——挂起协议不是用户源码，镜像
   B31 合并流构建）+ aexit 链 owner 的 RETURN_*（POP_TOP 为协议结果丢弃，剥）。
4. `_build_statements_from_instructions` 栈式重建；尾 Expr + 挂起值协议命中
   （`_pending_value_protocol_hit`）时升级 Return(value)。
5. 两条链全部成员标记 generated（幂等）。

**AST 映射**：`Return(value=BinOp(Await(Call), Add, Name))`——挂起前调用段与
挂起后续算段由同一栈式重建自然拼接，GET_AWAITABLE 由 ExpressionReconstructor
包装为 Await，位形嵌套无感，无逐位形补丁。

### B32 async 挂起值判定补全（因子化 + SWAP/RETURN 分块）

**根因**：B32 体尾挂起值升级的内联 BFS 要求 RETURN 块**同块**含 SWAP；async
形态 SWAP 与 RETURN_VALUE 分块（SWAP 在 SEND 保存段、RETURN 在 __aexit__ 链尾），
且链上存在异常边（PUSH_EXC_INFO 处理器入口）——判定失效。

**修复**：BFS 判据因子化为 `_pending_value_protocol_hit(start_block)`（唯一
事实源，禁止复制判定）：

- 仅延伸操作码全集 ⊆ 协议指令集的块（SWAP/LOAD_CONST/PRECALL/CALL/POP_TOP/
  GET_AWAITABLE/SEND/YIELD_VALUE/RESUME/CACHE/NOP/JUMP_BACKWARD_NO_INTERRUPT/
  COPY/RETURN_VALUE/RETURN_CONST/JUMP_FORWARD/PUSH_NULL）
- 含 PUSH_EXC_INFO 的块（异常机制入口）跳过不穿越——异常处理器块唯一归属
  异常区域，不参与正常控制流链
- 命中条件 = RETURN 块操作码全集 ⊆ 协议集且（SWAP 同块**或**链中已见 SWAP）

B32 漏斗改调该 helper（行为超集：同步形态 SWAP/RETURN 同块维持命中；新增
async 分块命中与异常边不穿越）。EXTENDED_ARG 跳过补入 B33 漏斗剔除的块首
指令定位（:31129 段）。

## 修复工程量与产物状态

- 修改 2 个核心文件：
  - `core/cfg/region_ast_generator.py`：新增 `_pending_value_protocol_hit`、
    `_b33_await_owner_merged_stmts`；`_generate_with` 主循环新增 B33 调用点
    （:31055 BEFORE_* 跳过之后、`_detect_with_body_return` 之前）；B32 漏斗
    改调 helper
  - 本轮早前已提交部分：B33 漏斗剔除（withitem 解包链二次发射）、
    `_extract_with_items` 重写（EXTENDED_ARG 跳过 + 递归解析嵌套元组/星号目标）
- 全量进度：**106/115 → 107/115 → 108/115**（r6_12 aw_await_expr 封闭
  6/6 MATCH；r6_06 aw_af_aw 经 B34 修复封闭 5/5 MATCH），16 文件
  12 success / 4 failure，零回归
- 回归哨兵：六套件 tests + site-packages 5 哨兵（scheduler 52/52、strategy
  20/20、tools 6/6、trade_schedule 6/6、mq_connector 13/13、trade_info_utils
  36/41=基线）

## 残留失败单元（8 单元 5 文件）

| 文件 | 单元 | 缺陷登记 | 特征 |
|------|------|----------|------|
| r6_04 | w_with_wraps_finally(1) | B30 | with 体 wraps finally |
| r6_10 | w_loop_nest_with / w_break_in_with / w_nested_flow | B34b | Different control flow（登记特征：for-else 幻影 while False） |
| r6_11 | w_with_in_finally / w_tryfin_with_tryfin | B34c | Different control flow |
| r6_15 | g_mixed(1) | B35 | Different bytecode |

**B34 已闭合（r6_06 aw_af_aw 5/5）**：归约层缺口 = GET_ANEXT 头无
FOR_ITER 式 fall-through 体扩展，体内 return 使正常流无 header 回边，
自然循环体退化 {header}，SEND-resume 体首块（blk@58：STORE y 绑定 +
值计算 + SWAP/POP_TOP 挂起）漏出内层 LoopRegion(46) blocks=[40,46]，
落 WithRegion 顺序处理，经 :31426 体尾链走查在 with 层发射 Return
（层级错置）。修复（region_ast_generator，生成层两方法 + _generate_loop
接入，六段注释模板）：
- _b34_unclaimed_loop_resume(region)：async-for 头（GET_ANEXT）经「header
  后继 → SEND 自循环 poll（块尾 JUMP_BACKWARD_NO_INTERRUPT 目标=自身）→
  SEND argval」结构链定位 resume 块；resume ∉ region.blocks、未生成、
  block_to_region 台账占用者为祖先区域（外层循环支配集合法登记）时放行
- _b34_loop_resume_pending_return(region, block)：后继恰一条 aexit 消费
  链（_collect_await_protocol_chain；异常 PUSH_EXC_INFO 块不参与）且链
  owner 去噪后剔除纯栈操作 {POP_TOP,SWAP,COPY} 余量恰一 RETURN_*（用户
  return 块必含值构建指令不误纳；blk@106=[POP_TOP,SWAP,POP_TOP,
  RETURN_VALUE] 为丢 aexit 结果+丢保存上下文+消费挂起值）+
  _pending_value_protocol_hit 命中；合并流 = resume 指令（剥块首 anext
  绑定 STORE_*、尾 SWAP+POP_TOP 协议对、噪声）+ owner RETURN_*，重建后
  resume + 消费链全成员标记 generated（每块唯一归属改判：resume 唯一
  归属循环体）
- _generate_loop 体装配前接入认领（r6-2 批次）

**B34 诊断（r6_06 aw_af_aw）**：`async for y in ait: return x + y` 位于
`async with m1` 内。blk@58（内层循环体）= STORE y + 值计算 + SWAP/POP_TOP
（挂起），后继 aexit 消费链 blk@72/98/106（RETURN_VALUE 消费挂起值）。内层
async for 链不构成 collect 协议链（GET_ANEXT 非 GET_AWAITABLE setup）。挂起
Return 的发射层级落在 async with 体尾而非内层 async for 体内——需按区域树
归属修正发射层级（blk@58 唯一归属内层 async for 区域，其挂起 Return 应在
该区域内发射）。

## 规范符合性

- 全部判据为结构事实（操作码形态链 / 控制流边性质 / 区域树归属），零启发式、
  零白名单、零回退
- 每块唯一归属：B33 接管时全链成员标记 generated；非 owner 链成员块空列表
  改判，维持单一发射点
- 数据流单向：判据链自底向上（块 → 链 → 区域归属），无回溯修正
- 识别方法注释含六段模板（识别条件/归约方式/AST 映射/C1/C2/C3）
- 数学表达与表运算准确性由本文档承载，与代码实现解耦

## B36 批次（for-else 融合 return 认领 + 证伪记录）

### B36-f 循环 else 链穿透认领（封闭 w_break_in_with，r6_10 3/6→4/6）

**根因**：`with mgr: for x in xs: if x: break; else: return -1; return 0`
中 else 体的 `return -1` 与 with 正常退出 `__exit__(None,None,None)` 调用
融合单块（blk@28 = 协议窗口 + LOAD_CONST -1 + RETURN_VALUE）。for 的
else 块链产出为占位（`While False: Pass`，孤立边界 NOP 摊平伪影）或空，
return 块留待 with 主循环消费——with 主循环经 `_detect_with_body_return`
把融合 return 上提到 with 层（orelse 语义丢失，渲染为幻影 while False +
return -1 错位）。

**修复**（`_loop_generate_for` else 渲染点两段认领，六段注释模板）：

1. 第一段（else 链产出为空）：沿 else 块链正常（非异常）后继链穿透，到达
   RETURN 块 B 判据——B 未 generated、唯一非异常前驱 ∈ else 块链（else 路径
   独占到达）、`_detect_with_body_return(B)` 命中、B 的归属台账占用者为祖先
   with 区域（B ∈ 祖先 with.blocks，字节码在 with 保护链上但源码语义是 else
   体的 return）。认领后 orelse += [Return]，B 标记 generated（祖先 with 主
   循环跳过，不再上提）。
2. 第二段（占位空 else）：单语句 While + test=Constant(False) + body=[Pass]
   的占位产出同为此结构证据，穿透认领同款判据，认领成功以 Return 替换占位。
3. `_b36f_claimed` 于两段 gate 之前统一初始化（修复初版占位路径 NameError
   被上层吞异常导致整个 with/for 渲染丢失的回归）。

**AST 映射**：For.orelse += [Return]；返回值经 `_detect_with_body_return`
窗口提取（融合块后半段值指令）。判据全部为后继边/块 role/归属台账同层事实，
无偏移白名单、无名字匹配。

### B36 证伪记录（a/c/d/e 实验判据全部移除，防重蹈）

- **B36-a（analyzer 清理收集前驱归属守卫）**：any/all 两语义对同一块方向
  相反——`w_loop_nest_with` blk@180（外层函数尾 return None 被内层越界收编，
  需**拒**）与 `aw_two` blk@190（m1 异常路径 return None，前驱 182 挂起轮询
  块不被收集，需**收**）：all 修 180 但拒 190 → 幻影 return None（r6_05
  aw_two/aw_three、r6_06 aw_in_af 回归）；any 收 190 但放行 180 被吞。统一
  判据（正常路径/异常路径可达性区分）待后续轮次设计，本判据段移除（结论
  注释保留于 region_analyzer.py `_collect_normal_exit_cleanup`）。
- **B36-c（generator body_end 扫描块集归属守卫）/B36-d（WITH_EXIT_CALL
  role 全局剥离 gate）**：d 的 role gate 对全部 with 生效，破坏 7 单元
  （n6_01/r6_01/r6_02/r6_03/r6_05/r6_06/r6_09 多单元 Different control
  flow）——role 全局赋予（不覆盖已有 role）使部分块被误剥离；c 与 d 组合
  收益不抵回归。两守卫移除。
- **B36-e（跨块 return 值提取）**：保留启用（`_b36_cross_block_return_value`，
  SWAP 在块首时沿纯值块前驱链重建返回值）；在 a/c/d 禁用组合下对 r6_10 无
  增量收益但无害（非跨块形态链断裂返回 None 维持既有路径），留作 w_nested_flow
  后续修复的基础设施。

## B36 批次进度与回归验证

- 全量：**109/115**（基线 108/115 → +1），16 文件 10 success / 6 failure，
  **零回归**（n6_01 8/8、r6_01 8/8、r6_02 7/7、r6_03 7/7、r6_05 6/6、
  r6_06 5/5、r6_07 6/6、r6_08 8/8、r6_09 8/8、r6_12 6/6、r6_13 8/8、
  r6_14 7/7 全绿）
- site-packages 6 哨兵全持平：tools 6/6、trade_schedule 6/6、
  mq_connector 13/13、strategy 2/2、scheduler 52/52、trade_info_utils
  36/41=基线
- 死代码清理：B36-a/c/d 实验残骸全部移除（`if False` 死代码零残留），
  B36-e/f 活判据保留

## 残留失败单元（6 单元 4 文件，较基线 8 单元减 2）

| 文件 | 单元 | 缺陷登记 | 特征 |
|------|------|----------|------|
| r6_04 | w_with_wraps_finally(1) | B30 | with 体 wraps finally |
| r6_10 | w_loop_nest_with / w_nested_flow | B34b | Different control flow（内层 with 越界收编外层 return 块；B36-a 统一判据待设计） |
| r6_11 | w_with_in_finally / w_tryfin_with_tryfin | B34c | Different control flow |
| r6_15 | g_mixed(1) | B35 | Different bytecode |

## B35 封闭（r6_15 g_mixed 8/8 MATCH，110/115）

**根因**：连续 yield-from（`yield from xs; yield 0; yield from ys`）中，混合
else 块 blk@20 = [前环耗尽 POP_TOP] + [裸 yield 0] + [yf#2 setup 表达式
（LOAD_FAST ys + GET_YIELD_FROM_ITER + LOAD_CONST None）]。loop1 旧实现
`_eb_has_yf_setup` → 整块跳过；loop2 的 `_pre_blocks` 扫描被 generated 门控
拦截（loop1 对 region.blocks 批量登记）→ 裸 yield 丢失，渲染幻影 `ys` Expr
（初版拆分点缺陷：前缀切分含 setup 表达式构建指令）。

**修复**（`_generate_loop` is_yield_from_loop else 处理，六段注释模板）：依
「每块唯一归属」按首个 GYFI 拆分——从 GYFI 反向走查，语句屏障指令（POP_TOP
语句终结/YIELD_VALUE yield 边界/STORE_* 绑定/JUMP*/协议指令等不可出现在纯
表达式构建区间的操作码）为止；屏障之后的连续指令 = setup 表达式构建段（归
后继环，现状已正确），屏障之前的指令前缀归本环 else 路径经
`_build_statements_from_instructions` 发射（YIELD_VALUE 是语句边界 →
Expr(Yield)；前环耗尽 POP_TOP 空栈 no-op）。装配序 `[_result] +
_post_yf_stmts` 保持源码顺序。初版缺陷修正：反向走查自 GYFI 起、遇屏障止
（blk@20 走查停在 POP_TOP@屏障），前缀正确排除 `LOAD_FAST ys`。

**屏障指令集提升为类级单一事实源**：`RegionASTGenerator._STMT_BARRIER_OPS`
（B35 拆分与 B30 held 值区间提取共用，零复制判定）。

## B30 封闭（r6_04 w_with_wraps_finally 11/11 MATCH，111/115）

**根因**：`with mgr: try: return xs[0] finally: return xs` 中 finally 的
return 与 with 退出协议融合。正常路径副本被异常表边界切分为**恰两块**：
blk@24 = [LOAD_FAST xs, SWAP 2, POP_TOP]（held 值替换：return 值入栈后与
try 延迟 return 压栈的 held 值交换、弃 held，栈 [exit_fn,held] →
[exit_fn,新值]）+ blk@30 = [SWAP 2, LOAD_CONST None×3, PRECALL, CALL,
POP_TOP, RETURN_VALUE]（with-exit 协议窗口 + 消费替换值返回）。W11-A 复合
门控（≥2 块且存在结构化子区域入口）与 W13 单块判据均不覆盖 → find 返回
[]，legacy 路径发射异常副本 blk@56 = [PUSH_EXC_INFO, LOAD xs, SWAP, POP_TOP,
SWAP] → 幻影 `Expr(xs) + Return(None)`（`finally: xs; return None`），
正常副本 return 整体丢失。

**修复**（单一事实源 `_b30_held_replace_pair_value(b1, b2)`，六段注释模板）：

1. **形态判据**（纯操作码形态链）：B1 剥噪声（_W13_NOISE_OPS）末两条为
   SWAP(2)+POP_TOP，SWAP 前值区间经 `_STMT_BARRIER_OPS` 屏障反向走查自查
   走至块首（vi==0——遇屏障即有前置用户语句，非本形态，拒绝）、区间非空且
   不含 SWAP；B2 剥噪声形态 [SWAP(2)] + 中段 + [RETURN_VALUE/RETURN_CONST]，
   中段操作码全集 ⊆ {LOAD_CONST,PRECALL,CALL,POP_TOP}、恰 3 个 LOAD_CONST
   （argval 均 None）、含 CALL、尾 POP_TOP。SWAP argval 恒为 2。
2. **find 侧门控**（`_find_finally_normal_copy_blocks` 复合门控拒绝分支）：
   seq 恰 2 块且命中块对判据 → 返回该块对序列为 finalbody 语句源。
3. **发射侧**（W11-A `for nb in _w11a_nc_blocks:` 循环，ghbs 之前）：B1=nb
   的唯一正常后继（successors 去 exception_successors）B2 ∈
   `_w11a_nc_offsets` 且未发射 → 块对整体发射 `Return(value=值区间重建)`，
   B1/B2 标记 generated（每块唯一归属，B2 不独立发射——with-exit 由外层
   With 语句渲染消费）。

**AST 映射**：`Try.finalbody += [Return(Name xs)]`——与源码
`finally: return xs` 重编译字节码逐指令一致（含异常副本/with-exit 分发链）。

**判据纯度**：零名字/偏移白名单；vi>0 前缀语句拒绝、B2 中段杂指令拒绝、
重建失败拒绝（C3 守卫封闭）。

## B36 批次进度与回归验证（B35/B30 后更新）

- 全量：**111/115**（B35 后 110/115 → +1），16 文件 14 success / 2 failure，
  **零回归**（r6_04 11/11 封闭；r6_10 4/6、r6_11 4/6 为仅存失败）
- site-packages 6 哨兵重生成+验证全持平：tools 6/6、trade_schedule 6/6、
  mq_connector 13/13、strategy 2/2、scheduler 52/52、trade_info_utils
  36/41=基线

## 残留失败单元（4 单元 2 文件，较基线 8 单元减 4）

| 文件 | 单元 | 缺陷登记 | 特征 |
|------|------|----------|------|
| r6_10 | w_loop_nest_with / w_nested_flow | B34b | Different control flow（内层 with 越界收编外层 return 块；B36-a 统一判据待设计） |
| r6_11 | w_with_in_finally / w_tryfin_with_tryfin | B34c | Different control flow |

## B34c 封闭（r6_11 w_with_in_finally / w_tryfin_with_tryfin 6/6 MATCH，113/115）

**根因**：`try: return X finally: <体含 with 或嵌套 finally>` 时 CPython 把
返回值压栈后穿越 finally 内联副本与 with 进入/退出协议，由后续块
RETURN_VALUE 消费（延迟 return 跨块形态）。两单元共同缺陷 = 该跨链值流未
重构：try 体渲染裸 `v`/`xs[0]`（Return 丢失），RETURN 消费块被 with 收编后
经 `_detect_with_body_return` 空窗口判据误判为 with 体 return None → 幻影
`return None` 或值丢失。

两形态字节码链（Shape A w_with_in_finally / Shape B w_tryfin_with_tryfin）：

```
Shape A: blk@4(try 体: LOAD v + 跳异常链) → blk@6(LOAD mgr+BEFORE_WITH)
         → blk@10(POP_TOP 丢 __enter__ 结果) → blk@12(NOP+退出窗口+RETURN_VALUE)
Shape B: blk@12(finally1 副本 xs.append(1)) → blk@26(append 副本续)
         → blk@68(SWAP+退出窗口) → blk@92(append(2) 副本+RETURN_VALUE)
```

**修复**（单一事实源 `_b34c_finally_deferred_return(block)`，六段注释模板，
挂接点 `_generate_block_statements_body` 中 `_try_deferred_return_in_loop`
之后）：

1. R1 归属：block ∈ TryExceptRegion.try_blocks 且 has_finally（区域树归属，
   结构事实）。
2. R2 值段定位：剥噪声逆向栈扫描（STORE_*/栈深归零为语句边界，块末栈深恰
   1）取 try 体压栈值段；栈效应模型（LOAD +1 / PRECALL 1参 -1 / 2参 -2 /
   CALL -1 / POP_TOP -1 / SWAP 0）。
3. R3 链走查（budget 16 + visited 防环）：单非异常后继链，链块四分类——
   - 终止块：末 RETURN_*，前缀**先剥退出窗口**（`_b34c_is_exit_window`：
     剥首 SWAP 后恰 [LOAD_CONST None×3 + PRECALL + CALL + POP_TOP]，窗口
     内部栈自洽净 -1，不计入余量核算——初版「前缀净 0」判据错杀此形态）
     余量 ⊆ `_DEFERRED_RET_CLEANUP_OPS` 且净 0，且无停机集命中、无 held
     替换（`_b34c_has_held_replace`：SWAP(2) 紧邻 POP_TOP → B30 领地语义
     守卫，防吞 w_with_wraps_finally 形态）；
   - 进入协议块：BEFORE_WITH/BEFORE_ASYNC_WITH 尾（允许直随 POP_TOP-only
     块）；
   - 退出窗口块：`_b34c_is_exit_window` 命中；
   - 清理副本块：指令 ⊆ 清理集、栈净 0、归属有主（异常表成员）。
4. 归约：值段 `expr_reconstructor.reconstruct` → `Return(value)`（含
   `_w14_explicit_return_flag`），前缀清理语句委托
   `_generate_stmts_from_instrs`（R64-D4 镜像）；链全成员标记
   generated/generated_offsets（每块唯一归属，防二次发射）。
5. 配套改判：`_detect_with_body_return` 尾部新增——无 SWAP 且值窗口空返回
   None（延迟 return 消费形态非 with 体 return）；有 SWAP 维持
   Return(None)（B30/B36-e 路径依赖不变）。

**AST 映射**：`Try.body += [Return(X)]`；with 体为 Pass/清理语句，与源码
`try: return v finally: with mgr: pass` 重编译字节码逐指令一致。

**判据纯度**：零名字/偏移白名单；链走查 budget/visited 封闭、held 替换
守卫防 B30 领地误吞、终止块余量 ⊆ 清理集拒绝杂指令（C1/C2/C3 守卫齐备）。
防回归事前验证：B30 w_with_wraps_finally（blk@24 [LOAD xs,SWAP,POP_TOP] →
blk@30 终端）被链上 held 替换判据拒绝，全量证实 r6_04 11/11 持平。

## B34c 批次进度与回归验证

- 全量：**113/115**（B30/B36 后 111/115 → +2），16 文件 15 success /
  1 failure，**零回归**（n6_01 8/8、r6_01 8/8、r6_02 7/7、r6_03 7/7、
  r6_04 11/11、r6_05 6/6、r6_06 5/5、r6_07 6/6、r6_08 8/8、r6_09 8/8、
  r6_12 6/6、r6_13 8/8、r6_14 7/7、r6_15 8/8 全绿；仅 r6_10 4/6 残留）
- site-packages 6 哨兵重生成+验证全持平：tools 6/6、trade_schedule 9/9
  （100%）、mq_connector 13/13、strategy 2/2、scheduler 52/52、
  trade_info_utils 36/41=基线

## 残留失败单元（2 单元 1 文件，较基线 8 单元减 6）

| 文件 | 单元 | 缺陷登记 | 特征 |
|------|------|----------|------|
| r6_10 | w_loop_nest_with / w_nested_flow | B34b | Different control flow（内层 with 越界收编外层 return 块；B36-a 统一判据待设计） |

## B34b 封闭（r6_10 w_loop_nest_with / w_nested_flow 6/6 MATCH，115/115 全清）

**根因**：with 清理块位置扫描（`get_blocks_in_order` 为块创建序）缺少可达性
约束——内层 with 的 cleanup 收集可沿创建序越界收编**不属于本 with 协议链**
的外部块。两形态：

1. `w_loop_nest_with`（`with mgr: for x in xs: with mgr as y: if y: return x`
   + 尾 `return None`）：blk@180（外层函数尾 return None，无条件边到达）被
   内层 with 越界收编 → 尾声吞入 cleanup → 渲染丢显式 else/出口结构 →
   Different control flow。
2. `w_nested_flow`（双层 with + for 内 continue/break + 尾 return x）：同源
   越界收编，continue-sink 与外层协议链块混入内层 cleanup。

**修复**（`_collect_normal_exit_cleanup` 统一判据 + 细化判据，六段注释模板；
`_collect_with_cleanup_blocks` 调用点传递 `exception_blocks` 与自身处理器
`hb`）：

1. **统一判据（B36-a 遗留任务收敛）**：位置扫描候选块必须从本 with 协议种子
   （entry ∪ body ∪ exception_blocks）**前向正常可达**（BFS 沿正常后继）；
   扩展时三类块不穿越——已归属区域树的块、其他 with 的种子块（BEFORE_*
   所在链）、**外部 with 处理器**（含 WITH_EXCEPT_START 且非自身处理器）。
   外部处理器不可扩展是内层 with 越界收编外层协议链的唯一通道，切断之。
2. **细化判据（bare-None 尾声吸收形态）**：不可达候选块去噪后恰为
   `[LOAD_CONST None, RETURN_VALUE]` 或单条 `[RETURN_CONST None]`，且至少
   一条正常前驱以 POP_JUMP_* 终结（条件分支假边直达尾声）时仍收编——此为
   R113/F5 系既定 with-cleanup 语义：if-else 假分支尾声与函数尾隐式 return
   同位，收编后经隐式 return 过滤渲染为函数尾，重编译与 pyc 逐指令同构。
   无条件边（fall-through/JUMP_FORWARD）到达的尾声不属此形态——那是外层
   with 的 exit-block（F5 机制经 `_find_with_exit_block` 取回顶层显式发射，
   w_loop_nest_with blk@180），必须拒绝。

**AST 映射**：条件假边 bare-None 尾声收编 → 隐式 return 过滤 → 函数尾无
显式 return None，与源码省略尾 return None 的渲染逐指令同构；无条件边
exit-block 拒收 → 顶层显式发射（exit_via_jump=True），结构各归其位。

**判据纯度**：零名字/偏移/函数白名单；判据全部为前向可达性（控制流边性质）
+ 操作码形态链（去噪后指令序）+ 前驱终结操作码性质。

**实证链（check_trade_name 细化方向判定）**：

1. git stash 对照区域树：旧代码把 blk@372（外层 if 的 else 分支 return
   None，条件前驱 POP_JUMP 假边直达）误收编进 with@150 cleanup；strict
   统一判据正确拒收后 IfRegion 显式渲染 `else: return None` → 候选与 pyc
   仅差 372↔376 两个跳转目标互换（80 指令数相同）→ 裁决器拒绝（哨兵回归
   36/41 → 35/41）。
2. 决定性事实：旧渲染（收编 + 隐式过滤）与 pyc **逐指令全等（80/80 含跳转
   目标）**——bare-None 尾声收编正是字节码精确的正确路径。
3. 细化判据四形态方向验证：trade_info_utils check_trade_name @14 拒
   180/150 ✓、@0 收 164/172/174 ✓、r6_05 aw_two 两层收 190 ✓、@150 收 372
   拒 376 ✓。

## B34b 批次进度与回归验证（round6 全清）

- 全量：**115/115 = 100%**（B34c 后 113/115 → +2），16 文件 16 success /
  0 failure，**零回归**（n6_01 8/8、r6_01 8/8、r6_02 7/7、r6_03 7/7、
  r6_04 11/11、r6_05 6/6、r6_06 5/5、r6_07 6/6、r6_08 8/8、r6_09 8/8、
  r6_10 6/6、r6_11 6/6、r6_12 6/6、r6_13 8/8、r6_14 7/7、r6_15 8/8 全绿）
- site-packages 6 哨兵重生成+验证全持平：tools 6/6、trade_schedule 6/6、
  mq_connector 13/13、strategy 2/2、scheduler 52/52、trade_info_utils
  36/41=基线（失败单元明细与基线一致：trade_operation / kill_trade_process
  / get_trade_status / query_trade_strategy_info / query_strategy_id；
  **check_trade_name 不在失败列表**——strict 判据回归 35/41 已由细化判据
  修复回归）
- region_analyzer.py B36-a 结论注释尾部已追加「[Round6-B34b 更新] 统一判据
  已实现」段落；恒真冗余比较已清理

## 残留失败单元（round6 全清：0 单元）

Round 6 全部 34 复现单元 115/115 = 100% MATCH，无残留。


## 打回修复批次（Round 6.3 复核回应）

回应 REVIEW2.md §5 打回项 #1–#4（A10 红线 / A8 / A9 / A7）。B37–B41 依
终判登记交后续轮次，本批未越界触碰。除本节追加与 `core/cfg/
region_ast_generator.py`、`core/cfg/region_analyzer.py` 两文件修复外，
未改动任何其他文件（REVIEW2.md / REVIEW.md / spec.md / tasks.md / 全部
\*OK.py / rv6 探针均未手改）。

### #1 [A10 红线] region_ast_generator.py UTF-8 BOM 恢复

- **事故链**：BOM `efbbbf` 于评审时点 4135e6db 在位（首 3 字节实测），
  commit `fbfc2e7b` hunk `@@ -1,4` 将 `-﻿"""` 改为 `+"""` 时剥除；此后
  `1c059d1b` / `4cd2a9f6` / `30468033` / `eedb08cc` 四批修复与收官快照
  均未发现未恢复，直至本复核终判打回（A10 红线）。
- **恢复动作**：Python bytes 级操作（`open(p,'rb')` 读全量 → 断言现头
  3 字节为 `22 22 22` 且非 `efbbbf` → 前置 `b'\xef\xbb\xbf'` 写回），
  只改文件头 3 字节，其余字节零触碰。恢复后文件 3 428 503 字节。
- **验证**：`head -c 3 core/cfg/region_ast_generator.py | xxd` =
  `00000000: efbb bf`；`git diff` 首行显示 `-"""` / `+﻿"""` 行首 BOM
  差异，其余 hunk 均为本批代码修复。
- **自测项固化声明**：**BOM 校验（`head -c 3` = `efbb bf`）自本批起
  纳入后续每批修复的自测项**（与语法/导入检查同批执行）。

### #2 [A8] LOOP_BACK_EDGE 跳过分支：方案 A 恢复（实测定案）

- **取证**：`git show 4cd2a9f6 -- core/cfg/region_ast_generator.py` hunk
  `@@ -30717,9 +31503,6` 确认被删分支原文（现树 :31750 WITH_EXIT_CLEANUP
  分支之后、PURE_BREAK 分支之前）：

  ```python
  if self.region_analyzer.get_block_role(block) == BlockRole.LOOP_BACK_EDGE:
      self.generated_blocks.add(block)
      continue
  ```

  分支沿袭：`127b59d4`（Initial commit）落地、`889a0417` 演进、
  `da260298`（R66 fix：LOOP_BACK_EDGE 多语句回边块 AugAssign/del 发射）
  依赖其把回边块归属让渡给循环装配路径，`4cd2a9f6` 静默移除。
- **与 Round6 新判据的相互作用分析**：B29 协议消费链（挂起轮询块经
  `_consume_async_with_protocol_if`/`_walk_async_pending_return` 在 with
  主块循环之前整体消费并标记 generated）；B34b 可达性（清理块可达性
  BFS 在 analyzer 侧完成，cleanup 块角色为 WITH_EXIT_CLEANUP，前一分支
  已拦截）；B30 块对归约（held 替换块对在 try/finally handler 路径与
  `_w11a_nc_offsets` 发射侧成对标记 generated）。三者消费对象均先于该
  分支登记，互斥不重叠——分析预测恢复无冲突，实测证实（见下）。
- **方案 A（恢复）实施**：分支原样复位，并在代码处加「[Round6-A8] 恢复
  R8/R66 判据，与 B29+ 判据共存论证」十三行注释（判据语义 + 三新判据
  共存论证逐条对应）。
- **实测裁决（方案 A 全绿，采用）**：round6 全量 115/115（16 文件全
  success）+ 六哨兵全持平 + option_account 35/35 + 23 个重生成 OK 产物
  与已提交版逐字节零漂移——方案 A 无任何读数回退，按任务书规则采用；
  方案 B（声明式重落地）无需启用。
- 哨兵选择说明（诚实记录）：`find site-packages -name
  "*validate_data*.pyc"` 零命中（全仓库亦无该 pyc；R8 期
  repro_r01_02_validate_data.py 为占位符，无 pyc 可测）。R8 代判据的
  实证面由 option_account（R66 代、da260298 明示依赖本分支）承载：
  恢复前基线 35/35、恢复后 35/35，回边多语句发射形态（AugAssign/del）
  经 r6 全量与零漂移复核无回归。若后续轮次重建 validate_data pyc 哨兵，
  应补跑。

### #3 [A9] R23N21_DEBUG 插桩清除（7 处全清零）

- **region_ast_generator.py**：`import sys as _sys` 已被 `4cd2a9f6`
  hunk `@@ -695,7`/`@@ -767,7` 删除，遗留 :733/:803 两处
  `print(..., file=_sys.stderr)` 呈破损态（env 置位即 NameError）。按
  评审建议**整块清除**（含 if 门控行与配套 `import os as _os` 脚手架，
  4 行 ×2 处）。
- **残留一并清除**（任务书 #3「若发现其他 R23N21_DEBUG 门控残留一并
  清除」）：`region_analyzer.py` 另有 5 处同门控残留（原 :25153/:25160/
  :25171 三处 `block.start_offset == 0` 偏移魔数探针、原 :27404 一处、
  原 :27492 起的 `_dbg` 门控组），均为 R23/N21 期调试插桩；虽自带
  `import sys as _sys` 未呈破损态，仍按零残留要求整块清除（30 行）。
  文件内其他门控插桩（DBG_OR、R7_DEBUG_IFGEN、_os_ebm/_os_dbg 系）非
  R23N21_DEBUG 门控且自洽，未越界触碰。
- **验证**：`grep -rn "R23N21_DEBUG" core/ | wc -l` = **0**；
  `_sys\.`/`_os\.` 零残留；`ast.parse`（utf-8-sig）+ `import core.cfg.
  region_ast_generator` / `import core.cfg.region_analyzer` 全通过。

### #4 [A7] 四方法补 C1/C2/C3 条款声明

条款语义按任务书定义（C1 只读本层块事实不跨区域回溯 / C2 归约产物只
引用子区域入口与归属台账 / C3 用户形态与协议形态双向可区分），格式对
齐同文件 `_collect_await_protocol_chain` / `_b34c_finally_deferred_return`
既有写法；每条声明均按该方法实际判据行为撰写：

| 方法 | C3 双向区分机制（摘要） |
|---|---|
| `_b31_continuation_owner` | 延续形态去噪后必含 STORE_*/POP_TOP 之外操作码，绑定/丢弃形态全为 STORE_*/POP_TOP，两类全集互斥且穷尽 |
| `_const_code_is_async_comprehension` | 编译器合成名 <listcomp>/<dictcomp>/<setcomp>/<genexpr>；Python 标识符语法禁止用户取得尖括号名 |
| `_b34c_has_held_replace` | 「finally: return X」指纹相邻对 SWAP(arg=2)+POP_TOP；try 体延迟 return 值段必不命中、finally 内联 return 值段必命中 |
| `_b34c_is_exit_window` | __exit__ 正常退出指纹 [SWAP?]+None×3+PRECALL+CALL+POP_TOP；异常路径实参为异常三元组非全 None；调用方余量 ⊆ 清理集且净栈效应 0 兜底用户显式调用 |

C1/C2 逐方法如实声明：两个 B34c 静态谓词与两个 B31 谓词均为「无归约
产物、不持有/登记任何块」，归属登记均由调用方（_b31_await_chain_gate /
_b34c_finally_deferred_return / B30 发射侧）按归属台账执行——谓词自身
无产物，声明与行为一致。

### 自测读数表（终局树：#1–#4 全部落位后实测）

| # | 自测项 | 结果 |
|---|---|---|
| 1 | BOM：`head -c 3 core/cfg/region_ast_generator.py \| xxd` | `00000000: efbb bf` ✓ |
| 2 | `grep -rn "R23N21_DEBUG" core/ \| wc -l` | **0** ✓ |
| 3 | ast.parse（generator utf-8-sig / analyzer）+ 双模块 import | 全通过 ✓ |
| 4 | round6 全量（r6_01..r6_15 + n6_01 = 16 文件）batch | **115/115 success = 100%**，16/16 文件 success，零位移 ✓ |
| 5a | tools.pyc 重生成 + single | 6/6 ✓ |
| 5b | trade_schedule.pyc 重生成 + single | 6/6 ✓ |
| 5c | mq_connector.pyc 重生成 + single | 13/13 ✓ |
| 5d | strategy/strategy.pyc 重生成 + single | 2/2 ✓ |
| 5e | IQEngine/utils/scheduler.pyc 重生成 + single | 52/52 ✓ |
| 5f | trade_info_utils.pyc 重生成 + single | **36/41** = 基线（失败单元 = trade_operation / kill_trade_process / get_trade_status / query_trade_strategy_info / query_strategy_id，check_trade_name 不在列表）✓ |
| 6 | option_account.pyc 重生成 + single（R66 哨兵） | **35/35**（恢复前基线同为 35/35，持平）✓ |
| 6′ | validate_data.pyc | site-packages 全库零命中，无 pyc 可测（诚实记录，见 #2 哨兵说明） |
| 7 | 方案 A 定案后全套读数重跑 | 上表即终局树读数，全部持平 ✓ |
| 8 | 重生成 23 个 OK 产物后 `git status` | 仅 `core/cfg/region_analyzer.py`、`core/cfg/region_ast_generator.py`（本批修复）+ 预期新报告 `r6_fixback.json`；**全部 OK.py 零内容变化（零漂移）** ✓ |

### 批次边界声明

- 本批改动面 = 2 个 core 文件 + 本 FIX.md 追加 + 自测报告 json
  （`.trae/specs/.../rounds/round6/r6_fixback.json`，工具产出）。
- 未触碰：REVIEW2.md / REVIEW.md / spec.md / tasks.md / 任何 \*OK.py
  手改 / rv6 探针 / B37–B41 相关判据面。
- 判据面审查：本批零新判据（#2 为既有判据复位；#3 为插桩清除；#4 为
  docstring；#1 为字节头修复），无名字白名单、无偏移魔数（清除的
  `block.start_offset == 0` 探针属减法）、无跨层读取、无新 self 状态。

## 回归拦截修复批次（全量验证回退响应）

> 承接：主代理验证批次一（commit c9e33a16）REGRESSIONS=4 触发回退拦截——
> shard4 IQEngine/core/strategy/strategy.pyc（−7 单元）、shard5
> plugin_system_finance commission.pyc+slippage.pyc（−5 单元）、shard7
> fly/dockerspawner/dockerspawner.pyc（单元 +2 但文件翻转）。本批定位
> 三处根因并落三处修复，修复后 4 文件全部转回 success，shard4/5/7
> batch+compare REGRESSIONS=0。本章节由接手收尾的修复工程师复验后落盘。

### 根因结论（三处）

1. **[R6-F1] with-in-try 的 try 协同占用纯展开块被拒收成孤儿 → 顶层幻影
   `return None`**（commission.FutureCommission.load /
   strategy.on_before_trading_start 等 9 处实证）。with 嵌套在 try 体内
   时，本 with 自身 WITH_EXCEPT_START 处理器的被抑制恢复链
   （POP_TOP/POP_EXCEPT/… → LOAD_CONST None + RETURN_VALUE 出口终端）落在
   try 的异常表保护区间内，被 TryExceptRegion 以「区间内全部块」方式协同
   登记。B34b 可达性 BFS 的「后继已被其他区域占用 → 停」判据把该链上的
   出口终端块一并拒之 reach 之外 → C3 拒收 → 孤儿化 → 顶层发射出与源码
   不符的显式 `return None`。协同占用 ≠ 冲突归属：同一协议块对 try 是
   体内块、对 with 是自身协议块。
2. **[R6-F1b] 多管理器 with 链 own_handler 恒取最内层，其余层处理器被
   抑制出口终端不可达 → 同签名幻影**（strategy.pyc 7 处实证）。异常链
   走查（`_collect_with_cleanup_blocks` 经 RERAISE 块异常后继串收）把
   with 链上全部嵌套层的 WITH_EXCEPT_START 处理器都收进 exception_blocks，
   而 own_handler 只取 body_start 对应条目（多管理器链共享最内层
   body_start → 恒为最内层处理器），其余层处理器在 BFS pop 时被判
   「外部」跳过——其被抑制恢复链（POP_TOP/POP_EXCEPT 纯展开 →
   LOAD_CONST None + RETURN_VALUE 终端）不可达，终端块成孤儿 → 同签名
   幻影 `return None`。
3. **[R6-F2] B29 await 链头资格未设 GET_AWAITABLE 门控，yield from 轮询
   环误成链吞掉 setup 块内裸 yield 语句**（dockerspawner.DockerSpawner.
   start 实证：`yield self.docker('start', …)` 蒸发、yield from 行保留）。
   `yield from <expr>` 编译协议（GET_YIELD_FROM_ITER + LOAD_CONST None →
   SEND/YIELD_VALUE/RESUME/JUMP_BACKWARD_NO_INTERRUPT 轮询自环）与 await
   轮询环共用 SEND 纯协议 poll 块形态，唯一结构区别是 await 链 setup 含
   GET_AWAITABLE、yield from setup 含 GET_YIELD_FROM_ITER。向后回溯方向
   由 `_setup_of_poll` 强制 GET_AWAITABLE，向前枚举方向未设同等资格 →
   自「yield-from setup」块误成链：门控把 setup 块 defer 给 owner（返回
   []），而 owner 侧收链因无 GET_AWAITABLE setup 必然失败——两侧不对称
   导致 defer 永不兑现，setup 块内先于 yield from 的裸 yield 语句被吞。

### 三处修复的判据与锚点

| # | 锚点（file:line） | 判据（纯结构事实） |
|---|---|---|
| F1 | region_analyzer.py:12213–12239（白名单注释 + `_b34b_try_coowned_unwind_ops` frozenset:12236）；BFS 后继分支 :12323–12330 | 后继归属 `isinstance(owner, TryExceptRegion)` 且块内全部指令操作码 ∈ 纯展开操作码集合（POP_TOP/POP_EXCEPT/RERAISE/COPY/SWAP/LOAD_CONST/RETURN_VALUE/RETURN_CONST/JUMP_FORWARD/JUMP_ABSOLUTE/NOP/RESUME/CACHE）→ 透明遍历（入栈继续 BFS）；非 try 归属或含用户指令（CALL/STORE_*/FOR_ITER 等）维持占用即停。LoopRegion/WithRegion 拥有的块不在白名单 |
| F1b | region_analyzer.py:12248–12293（外部处理器分支内被抑制出口终端回链走查） | 外部处理器（`WITH_EXCEPT_START` ∈ 块且 `is not own_handler`）尾指令 `get_last_instruction()` 呈 `POP_JUMP_*` 且 argval 非空 → 沿被抑制延续边（真边）只读走查：链上允许 a) try 协同占用纯展开块（F1 同款白名单 + 唯一正常后继）或 b) 自由纯展开块（唯一正常后继）；终端须为自由 bare-None 块（去噪后恰为 LOAD_CONST None + RETURN_VALUE 或单条 RETURN_CONST None）且**前驱数 = 1**（被抑制专用出口）；终端加入 reach 后仍须通过位置扫描全部守卫才可收编 |
| F2 | region_ast_generator.py:9250–9272（注释）+ 守卫 :9273–9274（`if not _is_setup(cur): return None`） | 向前枚举起点 cur 必须自身含 GET_AWAITABLE（`_is_setup`）；不含即返回 None，门控不 fire，块走既有发射路径（与 B31 前行为逐位一致）。GET_AWAITABLE（await 协议）与 GET_YIELD_FROM_ITER（yield from 协议）按操作码互斥 |

三处均带六段注释 + C1/C2/C3 条款；判据全部为纯结构事实（操作码集合、
归属区域类型、前驱计数、SEND/GET_AWAITABLE 协议形态），零名字白名单、
零 start_offset 魔数、零跨层回溯（全部只读同层结构：block_to_region、
cfg 后继/前驱、块内指令）、零新 self 状态（全部函数内局部变量）。

### 自测读数表（接手收尾复验，全部真实跑）

| # | 自测项 | 结果 |
|---|---|---|
| 1 | BOM：`head -c 3 core/cfg/region_ast_generator.py \| xxd` | `00000000: efbb bf` ✓ |
| 2 | `grep -rn "R23N21_DEBUG" core/ \| wc -l` | **0** ✓ |
| 3 | ast.parse（analyzer utf-8 / generator utf-8-sig）+ 双模块包路径 import | 全通过 ✓ |
| 4 | round6 全量 batch（r6_01..r6_15 + n6_01 = 16 文件，报告 `r6_regfix.json`） | **115/115**，16/16 文件 success，rate 1.0，零位移 ✓ |
| 5 | rv6 探针 batch（7 探针 29 单元，报告 `rv6_regfix.json`） | **18/29 持平**：rv6_01=3/5、rv6_02=2/4、rv6_03=4/4、rv6_04=1/4、rv6_05=3/4、rv6_06=1/4、rv6_07=4/4，与 REVIEW2 §3 登记面逐文件一致，MISMATCH 单元名单亦一致（aw_break_in_try_for/aw_continue_in_try_for、outer_raise_catch/nested_with_else_loop、try_fin_with_nested/double_fin_overwrite/try_fin_fin_body_with、gen_for_else_mixed、deep_tuple_star/star_mid_async/nested_star_tuple）；**B37–B41 登记面无变差** ✓ |
| 6 | 六哨兵重生成 + single | tools 6/6 ✓、trade_schedule 6/6 ✓、mq_connector 13/13 ✓、IQCommon/strategy/strategy 2/2 ✓、IQEngine/utils/scheduler 52/52 ✓、trade_info_utils **36/41**=基线（失败 5 单元 = trade_operation/kill_trade_process/get_trade_status/query_trade_strategy_info/query_strategy_id，名单不变，留档 `r6_sentinel_trade_info.json`）✓ |
| 7 | option_account.pyc（`find site-packages` 定位 = IQEngine/plugins/plugin_system_accounts/account_model/）重生成 + single | **35/35** ✓ |
| 8 | 4 个回退文件重生成 + single | IQEngine/core/strategy/strategy **20/20** ✓、plugin_system_finance/commission **25/25** ✓、plugin_system_finance/slippage **19/19** ✓、fly/dockerspawner/dockerspawner **26/26** ✓（全 success，与主代理读数一致） |
| 9 | `git status` OK.py 漂移盘点（含 15 支 modified OK.py 补齐重生成） | 见下节，无新 failure 文件 ✓ |

补充自测报告 json（工具产出）：`r6_regfix.json`、`rv6_regfix.json`、
`r6_sentinel_trade_info.json`、`r6_okdrift_fail5.json`（重生成前 5 支
failure 文件读数+失败名单）、`r6_okdrift_regen15.json`（补齐重生成后
15 支读数）。

### OK.py 漂移盘点结论（自测 #9）

前工程师中断时 15 支 modified OK.py 留在盘上（sha 对账证实 = 批次一
修复前核的重生成产物，未覆盖本批三处修复后的输出）。本批以当前核
（含三处修复）将其**全部补齐重生成**并逐支 single（重生成允许，零手改）：

- **9 支 success**：fileio_utils 15/15、client_db 9/9、strategy_context
  31/31、json_persistance 7/7、function(risk) 15/15、broker 38/38、
  IQEngine/utils/__init__ 33/33、oauth2 12/12、flyAccount 24/24——内容
  变化但 single 仍全 success。
- **4 支 failure 但与 HEAD 分片报告登记面逐单元持平**（读数 + 失败名单
  均一致，全部既有基线缺口，非本批引入）：wizard_quant_api 55/58
  （filter_desicion、get_DMI.calculate_di.<genexpr>×2）、trade_info_utils
  36/41（基线 5 单元名单不变）、future_contract_info 27/29（check_user、
  info_conbine）、quote_handler 78/79（get_kline_local）。
- **2 支重生成后与 HEAD blob 内容一致**（git clean，HEAD 提交内已含修复
  后产物）：flytools 65/66 持平（失败名单 modify_batcktes_info 不变）；
  plugin_fly_data/strategy **23/27 → 26/27 = 修复净改善 +3**——
  on_before_trading_start / on_after_trading_end / on_once_handle 三个
  with-in-try 幻影 return 单元转绿（正属 F1 根因实证名单），
  tick_worker_thread 为既有残留缺口继续登记。
- **无任何新出现 failure 的文件**；4 个回退文件 OK.py 与 HEAD 一致且
  single 全 success（见 #8）。

### 与 B34b 原修复的兼容性论证

B34b 原修复的关键维持项：w_loop_nest_with 内层 with 的 BFS 仍止于
122/114/84，blk@180（函数尾 return None 块）保持不可达、交还顶层发射。
本批三处修复不破此约束：

1. **F1 白名单按归属区域类型分流**：blk@180 若被外层结构占用，其归属为
   LoopRegion/WithRegion（非 TryExceptRegion）→ 不入白名单 → 占用即停
   维持；try 协同占用分支仅对 `isinstance(owner, TryExceptRegion)` 且
   纯展开形态放行。内层 with 的 BFS 扩展在到达任何 blk@180 归属块前
   已被外层处理器 158 的「WITH_EXCEPT_START 且非 own_handler → 停」
   判据截断，白名单不参与该路径。
2. **F1b 终端前驱数 = 1 判据排除共享 exit-block**：blk@180 的前驱 =
   {156 正常跳转, 178 展开链}，前驱计数 2 → 即使某路径把它误认为被
   抑制终端也被拒绝（被抑制专用出口与正常/被抑制共享 exit-block 按前驱
   计数互斥，C3 条款）——B34b 的 exit-block 交还顶层发射语义不变。
3. **F2 与 B34b 无交集**：F2 只作用于 await 链资格（GET_AWAITABLE
   门控），不触碰 with 可达性；await 链行为不变（向后回溯方向本就经
   `_setup_of_poll` 强制同资格，向前方向补齐的是对称性）。
4. 实证背书：六哨兵持平（#6）+ option_account 35/35（#7）+ rv6_02
   （B34b 正向反例探针）2/4 与 §3 登记面持平（#5）+ round6 16 文件
   115/115 零位移（#4）——B34b 全部既有守卫行为在修复后核下逐位不变。

### 批次边界声明

- 本批改动面 = `core/cfg/region_analyzer.py`（F1+F1b）+
  `core/cfg/region_ast_generator.py`（F2）+ 本 FIX.md 追加 + 自测报告
  json（`r6_regfix.json` / `rv6_regfix.json` / `r6_sentinel_trade_info.json`
  / `r6_okdrift_fail5.json` / `r6_okdrift_regen15.json`，工具产出）+
  15 支 modified OK.py 补齐重生成（`pycdc.py -o`，零手改）。
- 未触碰：REVIEW2.md / REVIEW.md / spec.md / tasks.md / rv6 探针 /
  B37–B41 相关判据面。
- 判据面审查：三处新判据均为纯结构事实（操作码集合 / 归属区域类型 /
  前驱计数 / GET_AWAITABLE 协议形态），无名字白名单、无 start_offset
  魔数、无跨层回溯、无新 self 状态；全部带六段注释 + C1/C2/C3 条款。
- 遗留清理：5 棵二分工作树（pycdc_b1tree/b2tree/b3tree/r5tree/r6tree）
  已 `git worktree remove --force` 清理（详见 git worktree list 留档）；
  pcdc_r0 / pcdc_wt / pcdc_r8wt 为历史遗留非本批产物，未动。
