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
