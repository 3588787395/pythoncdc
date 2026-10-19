# Round 4 FIX.md（await-挂起链族封闭）——终稿

规范：`.trae/specs/attain-true-completeness/`；基线 HEAD=69132f55（rr-v3r03）。
证据目录：本目录（stamps/日志/dump），探针 stage=`.trae/specs/attain-true-completeness/test_repros/round4/`。

## §0 范围与结论摘要（终稿）

范围（tasks.md Task 4）：R4 红单元 c4_20（e05 async-yield-await / e07 async 推导式×2）、e12d（幻影 await 双发）、r7_06（await×三元臂×3）、yf9 全族（prec 红 + 四 csv 非法形态复核）；须过全部门禁（邻域/负对照/合成/E 全量）。

| 探针 | 基线 | 终态 | 备注 |
|---|---|---|---|
| c4_20（test_repros/round4/c4_20_async_five.pyc） | 21/24 | **24/24** | e05=B112①；e07 .inner 与 .inner.<listcomp>=B112②，均已绿 |
| e12d（test_repros/round3/e12d_g9_awaits.pyc） | 10/11 | **11/11** | B128 幻影 await 双发已消 |
| r7_06（test_repros/round7/r7_06_ternary_lambda_await.pyc） | 7/10 | **10/10** | B47 三元臂 await 链已复原 |
| yf9_assign（rec1_yf9_assign.pyc） | 2/2 | 2/2 | 维持绿 |
| yf9_from（rec1_yf9_from.pyc） | 6/6 | 6/6 | 维持绿 |
| yf9_arg / boolop / ret / cond | compile_error | **3/3・2/2・2/2・2/2** | 复核结论：非「非法形态」而是缺语境括号的编码缺陷（裸 yield 实参/return/if 条件）；YF9 补括号后全部重建成功且字节码一致 |
| yf9_prec（rec1_yf9_prec.pyc） | 1/2 | **2/2** | `(yield i)+1` 优先级括号已复原，无语义漂移 |

红单元清单（R4）：c4_20 三红（e05/e07×2）、e12d 一红、r7_06 三红、yf9 prec 一红 + 四 csv 非法形态复核——**全部清零**（含四件由 compile_error 复核为真实缺陷并修复）。

结论摘要：5 项通用机制修复（B112①/B112②/B128/B47/YF9）+ 合成门禁暴露的 3 个族内缺口补强（B112①回边落点与 loop 消费路径、B47 赋值位形 STORE/LOAD 尾对），共 3 文件 +447/-13（region_ast_generator.py +360/-8、code_generator.py +59/-5、ast_generator_v2.py +28/-0），标记 [Bn-V3R4] 25 行，G3=0 / G4=0 / I.4 白名单判据。全部门禁过：E 全量 402 文件 6617/6617 八分片 REGRESSIONS=0、small34 1568/1568 IMPROVED=33、quotation 153/153、tests 七套件基线名单一致、IV.2 全绿（BOM 单头）、site-packages 零字节差异。残余：yield-三元臂值位形的区域装配局限（域外，§4 注记）；r5_10 附注（§3）。

## §1 修复日志（终稿）

1. **[B112-V3R4①] async 生成器 yield-of-await 落点链消费门**（c4_20::e05_async_compound.go 根因）
   - 根因：`async for v in gen: yield await c` 内 `yield await c` 编译为 setup(@42: STORE_FAST c; LOAD_FAST c; GET_AWAITABLE; LOAD_CONST None——兼作外围 aenter await 链 resume 的 junction) → poll(@50: SEND;YIELD_VALUE;RESUME;JUMP_BACKWARD_NO_INTERRUPT 自环) → 落点(@58: ASYNC_GEN_WRAP;YIELD_VALUE;RESUME;POP_TOP)。`_generate_block_statements_body` 主循环对 YIELD_VALUE/ASYNC_GEN_WRAP 无语句边界 case（YIELD_VALUE 边界只在 `_build_statements_from_instructions`），指令被静默丢弃 → 语句空。B31 门对落点链不成立：`_collect_await_protocol_chain(@58)` 回溯经 junction @42 攀升越入外围 aenter/async-for 协议链（@12 GET_ANEXT 无 GET_AWAITABLE）失败 → None。
   - 判据（I.4 白名单：块内 opcode 形态 + 前驱后继边 + 登记状态，零语料特判）：新谓词 `_b112_is_landing` = 去噪（RESUME/NOP/CACHE/PUSH_NULL）后恰 [ASYNC_GEN_WRAP, YIELD_VALUE, POP_TOP]；`_b112_poll_targeting` = 落点块的 SEND 前驱（argval 指向本块）唯一；`_b112_setup_of` = 该 poll 的 GET_AWAITABLE 前驱（且为 poll 正常前驱）唯一；setup 兼 resume（junction）时首条去噪指令为 STORE_* 且被某 SEND 指向 → 合并时剥除（与 Round5-08 SEND 跳出目标块判定同源）。
   - 归约方式：整链唯一归属落点块——落点块被调用时合并 setup+落点指令流（剥噪声与 GET_AWAITABLE 后 LOAD_CONST None 发送值），经 `_build_statements_from_instructions` 重建为单条 `Expr(Yield(Await(...)))`，登记全链块/偏移；setup/poll 被调用时返回 `[]`（defer，不发射、不标记）。末语句非 Expr(Yield) 即返回 None 回退（C1 无半应用）。
   - 改动：`core/cfg/region_ast_generator.py` 新增方法 `_b112_async_gen_yield_await_gate`（紧随 `_b31_await_chain_gate` 之后，docstring 六项 + 标记）；`_generate_block_statements_body` 中紧随 B31 门调用之后接入（约 L60746 区域，行号已随编辑 +~155 漂移）。
   - 候选先行验证：monkeypatch 原型 `_r4_b112a_proto.py` → e05 输出 `body: [Expr(Yield(Await(c)))]` AST 正确（`_r4_e05_b112a.out.txt`）。
   - 验证读数：stamp=r4fix_b112a_c4_20 → c4_20 **21/24→22/24**（e05 绿，其余 21 单元逐位不变）。
   - 合成门禁补强（synth_b112a::s_plain/s_with_host，直落 body 位形 `async for x in g: yield await u(x)` 与 async with 宿主同形）：CFG 把循环回边 `JUMP_BACKWARD` 并入落点块（去噪 4 条），`_b112_is_landing` 严格 3 条判据不命中 → 幻影再现；且 hitch 修复后置的协议消费路径 `_loop_dispatch_block`（`region.is_async and is_async_poll_protocol_block`）直接标记 poll 已生成——落点块随后被 `_generate_loop` 收尾扫登记，yield 语句静默蒸发（`body: pass`）。补强 2 处（均 [B112-V3R4]）：① `_b112_is_landing` 增尾随回边跳转形态（去噪 4 条且尾为 JUMP_BACKWARD[_NO_INTERRUPT]/JUMP_FORWARD），合并流重建前剥尾跳转；② `_loop_dispatch_block` 协议消费处先对 SEND 目标落点块经 B112 门发射语句入 body_stmts，再标记 poll（门未命中行为逐位不变）。读数：synth_b112a **6/8→8/8**（product 三函数 yield 全复原）。

2. **[B112-V3R4②] async 推导式调用在表达式重建层缺 GET_AITER 形态**（c4_20::e07_async_closure.outer.inner 与 .inner.<listcomp> 根因）
   - 根因：`async def inner(): return [v async for v in gen]` 的 await 链由 B31 门合并（setup 含 MAKE_FUNCTION(<listcomp>); GET_AITER; PRECALL 0; CALL 0; GET_AWAITABLE——编译器对含 async for 推导式自动补发的 GET_AWAITABLE 被 B31 剥除，行为正确）。`ExpressionReconstructor._process_instruction` 的 CALL(0) 推导式合并分支判据只认 GET_ITER 包出的 `Iter` 节点；GET_AITER 在逐指令扫描层不产生栈节点（迭代对象原值留栈），合并分支不命中 → CALL 普通处理弹出 Name(gen) 作 func → `Return(Call(gen,[]))`，ComprehensionObject 被弃、`<listcomp>` code object 全灭（"Missing bytecode"）。e07 三条路径差异：`async with` 宿主（e09b::a_two 形态）经 WithRegion 装配路径重建成功——绕开了该 CALL 分支；语句级 return/assign（v1/v2/v3/v5/v6、r5_10 全族）全中招。
   - 判据（同编译器合成事实，非白名单特判）：CALL ∧ argc==0 ∧ 紧邻下方 ComprehensionObject ∧ 上一显著操作码为 GET_AITER（跳过 PRECALL/CACHE/NOP/EXTENDED_ARG/RESUME 编译器填充；GET_AITER;PRECALL;CALL(0) 三连为编译器仅为推导式调用发射的合成形态，用户源码不可达）。
   - 归约方式：把栈顶迭代对象补包为 `Iter` 节点后走既有同步合并分支——`_parse_comprehension_from_code` 解包 Iter 取原值为迭代对象，is_async 由内层 code object 的 GET_ANEXT 事实在 `parse_comprehension_inner` 判定，无需外传标志。
   - 改动：`core/cfg/ast_generator_v2.py` 3 处（`ExpressionReconstructor.__init__` 增 `_b112_prev_pos_op` 追踪位；`reset()` 复位；`_process_instruction` 顶部追踪上一显著操作码 + CALL 分支增补 async 补包），全部标 `[B112-V3R4]`。
   - 候选先行验证：monkeypatch 原型 `_r4_b112b_proto.py` → r5_10 六单元全复原、v1..v6 矩阵全对（`_r4_r5_10_proto.py`、`_r4_e07_matrix_proto.py`）；`pyc_verify single` r5_10 13/13、c4_20 24/24。
   - 验证读数：stamp=r4fix_b112b_c4_20 → c4_20 **22/24→24/24**。
   - 附注（重要）：修复过程中发现 r5_10（round5 遗留探针）该形态在 HEAD 即已回退（`_r4_heads.py` 运行时关本门复跑仍为 `ait()`，证明非本轮编辑所致；r5_10 不在 R3/R4 任何门禁清单内，属未覆盖回退）。本项修复使 r5_10 13/13 复原为遗留 OK.py 基线，零新增风险。

3. **[B128-V3R4] if 条件位形 await 链唯一归属 IfRegion（防块级幻影双发）**（e12d::f_await_cond_pos 根因）
   - 根因：`if await src(i):` 条件位形（setup@40 兼 async-for resume junction → poll@66 → owner@74=[POP_JUMP_FORWARD_IF_FALSE]）双路径发射：① 块级扫描 `_generate_block_statements_body(@40)` → `_reconstruct_await_block_stmts(@40)` 独立重建裸 `Expr(Await(src(i)))`；② IfRegion 条件路径 `_if_extract_cond_instructions(@74)` + `_if_extract_condition_from_instructions(@74)`（cond_instrs 空，经链回溯重建）生成正确 `if await src(i):`。产物出现幻影前置 `await src(i)` 独立语句。另外 `_collect_await_protocol_chain` 自 @40 回溯经 junction 越界（同 B112① 的 e05 位形），使 B31 门不认领该链。
   - 判据（I.4 白名单：块后继边 + SEND argval + 区域登记关系）：新谓词 `_b128_await_owner_if_condition(block)` = block 含 GET_AWAITABLE（与 `_reconstruct_await_block_stmts` 同入口资格）∧ 其后继中的 poll 块（is_async_poll_protocol_block）以 SEND argval 指向的 resume 块（owner）是某已登记 IfRegion 的入口/条件块（IfRegion.is_block_entry：condition_block 或 entry）。
   - 归约方式：命中即 defer——`_generate_block_statements_body` 在 `_reconstruct_await_block_stmts` 调用前分流（标记块、不发射语句）；等价消费由 IfRegion 条件重建路径完成（instrumented 实测该路径独立可重建，不依赖块级标记顺序）。
   - 改动：`core/cfg/region_ast_generator.py` 2 处（新谓词紧随 `_reconstruct_await_block_stmts` 之后；守卫插入 `_generate_block_statements_body` 的 await 分支之前），均标 `[B128-V3R4]`。
   - 候选先行验证：monkeypatch 运行时原型 `_r4_b128_proto.py` → 幻影消失、`pyc_verify single` e12d **11/11**（`_r4_e12d_b128proto.py`）。
   - 验证读数：stamp=r4fix_b128_e12d → e12d **10/11→11/11**。

4. **[B47-V3R4] 三元臂值块 await 挂起链重建**（r7_06::t_await_ternary_branches / t_await_assign_ternary / t_await_deep_ternary 根因）
   - 根因：`return await io.a() if flag else await io.b()` 类位形的臂值块含 GET_AWAITABLE（setup 块，元组 @10/@62），臂值经 poll 恢复后在 owner 继续（真臂 owner=纯 JUMP_FORWARD 跳汇合块 / 假臂 owner=`[LOAD n, BINARY_OP]` / 落 RETURN_VALUE）。`_build_ternary_value_expr` 对臂块直接 raw `expr_reconstructor.reconstruct`：GET_AWAITABLE 正常包装 Await 后，协议发送值 `LOAD_CONST None` 成为栈顶产物，臂值被常量 None 顶替——产物 `None if flag else None`。链上 owner 侧延续指令（如 `+ n`）也不在臂块指令内。
   - 判据（I.4 白名单：链成员指令 + 操作码）：`_collect_await_protocol_chain(block)` 成链 ∧ owner 呈延续形态（`_b31_continuation_owner`）；排除含 BEFORE_WITH/BEFORE_ASYNC_WITH 的 with 协议链与链头 SWAP+CALL+GET_AWAITABLE+≥3×LOAD_CONST None 的 __aexit__ 消费链（与 B31 门 B29/B34 守卫同源同判据）。
   - 归约方式：复用 `_b31_await_chain_stream` 合并链成员为单指令流（跳过 poll、剥协议发送值与编译器噪声），再剥尾部纯控制终结符（JUMP_*/RETURN_VALUE/RETURN_CONST，不产栈值），经 expr_reconstructor 栈式重建为内嵌 Await 的臂表达式。
   - 改动：`core/cfg/region_ast_generator.py` 3 处——① B31 门内联合并循环提取为 `_b31_await_chain_stream(members)`（同逻辑无行为变更，唯一事实源）；② 新方法 `_b47_await_arm_value_expr`（置于 `_build_ternary_value_expr` 前）；③ `_build_ternary_value_expr` 在纯 JUMP 连接块递归之后、raw 重建之前接入（命中返回臂表达式，未命中返回 None 走既有路径）。
   - 候选先行验证：monkeypatch 原型 `_r4_b47_proto.py` → 三单元全复原（`await io.a() if flag else await io.b()`、`await io.a() if flag else b`、`await io.a() if flag else await io.b() + n`）、`pyc_verify single` r7_06 **10/10**。
   - 验证读数：stamp=r4fix_b47_r7_06 → r7_06 **7/10→10/10**。
   - 合成门禁补强（synth_b47::s_false_arm，赋值位形 `v = xs[0] if flag else await io.b()`）：假臂无 JUMP 连接块、直接落入三元汇合块，owner=merge（尾 [STORE_FAST v, LOAD_FAST v, RETURN_VALUE]）——合并流尾巴混入区域的「STORE 目标→重载目标」消费对，臂值被 STORE 弹出后重建为 `v`（产物 `xs[0] if flag else v`）。补强 1 处（[B47-V3R4]）：尾跳转/RETURN 剥除后，再剥相邻同目标 STORE_X/LOAD_X 尾对（臂值须留栈；TOKEN 对即区域级 Assign 的消费，value 已由 IfExp 装配；非同目标/非相邻不剥，C3）。读数：synth_b47 **3/4→4/4**。

5. **[YF9-V3R4] yield/yield from 表达式优先级与语境括号**（yf9 全族：prec/arg/ret/cond/boolop 及 e12b/e12c/e12f 根因）
   - 根因（两类）：
     ① 优先级表缺位：`_get_dict_expr_precedence` 与 `_get_ast_expr_precedence` 均把 Yield/YieldFrom 落回 atom（17），作二元/比较/布尔/下标操作数时不补括号——`(yield i) + 1` 渲染为 `yield i + 1`，重解析为 `yield (i + 1)`，字节码不一致（semantic drift）；AST 分支 `ASTYield` 亦置 `current_precedence=atom`，尾部优先级判定失效。
     ② 语境括号缺位：裸 yield 在 3.11 语法中作调用实参/return 值/if・while 条件均为 SyntaxError（`f(yield x)`/`return yield x`/`if yield x:`），AST 路径 `_generate_call`/`_generate_return`/`_generate_if`/`_generate_while` 均按 parent=0 渲染不补括号——产物直接 compile_error（yf9_arg/ret/cond、e12c 及 e12b/e12f 部分单元）。
   - 判据：yield/yield from 与 lambda 同为表达式语法最高层（最低绑定，CPython 语法 `expression: lambdef | yield_expr` 并列），操作数位形按 `self._precedence['lambda']`(1) 参与既有优先级比较；语境括号按「该位置裸 yield 是语法错误」的语法事实定点补括号（仅 ASTYield / dict Yield 命中）。
   - 归约方式：① dict 路径 `_get_dict_expr_precedence` 增 Yield/YieldFrom→lambda 槽 + dict Yield/YieldFrom 分支按 `parent_precedence>0 and lambda<parent` 补括号；② AST 路径 `_get_ast_expr_precedence` 增 ASTYield→lambda 槽 + ASTYield 分支 `current_precedence=lambda`（复用既有尾部括号判定 L3924）；③ 四个消费点（AST Call pparams/kwparams/var/kw、return、if、while）对 ASTYield 直接补括号。parent=0 的语句级/赋值右值输出逐位不变。
   - 改动：`core/cfg/code_generator.py` 共 8 处（4 处优先级 + 4 处语境括号），全部标 `[YF9-V3R4]`。
   - 候选先行验证：monkeypatch 原型 `_r4_yf9_proto.py` → yf9_prec `(yield i) + 1` 复原、`pyc_verify single` **2/2**；家族四件 proto 复跑（assign 2/2、from 6/6、r7_06 10/10、r5_10 13/13 不回归）。
   - 验证读数：stamp=r4fix_yf9 → yf9_prec **1/2→2/2**、e12b compile_error→**18/18**、e12f→2/2；stamp=r4fix_yf9b → yf9_boolop compile_error→**2/2**；stamp=r4fix_yf9c → yf9_arg→**3/3**、yf9_ret→**2/2**、yf9_cond→**2/2**、e12c→**3/3**（全族七件 19/19 全绿）。

## §2 变更清单（终稿）

`git diff 69132f55..HEAD -- core/`：**3 文件 +447/-13**（numstat：region_ast_generator.py +360/-8、code_generator.py +59/-5、ast_generator_v2.py +28/-0）；标记 [Bn-V3R4] 共 25 行（region 10 = B112×5/B128×2/B47×3、ast_v2 3、code_gen 12）。

- `core/cfg/region_ast_generator.py`：
  - B112①（含补强）：新门 `_b112_async_gen_yield_await_gate` + 谓词 `_b112_is_landing`（含回边吸收形态）/`_b112_poll_targeting`/`_b112_setup_of`；`_generate_block_statements_body` B31 门后接入；`_loop_dispatch_block` 协议消费处落点发射；文档串同步。
  - B128：谓词 `_b128_await_owner_if_condition` + `_generate_block_statements_body` await 分支前 defer 守卫。
  - B47（含补强）：B31 门合并循环提取为 `_b31_await_chain_stream`；新方法 `_b47_await_arm_value_expr`（含尾部 STORE/LOAD 同目标对剥除）+ `_build_ternary_value_expr` 接入。
- `core/cfg/ast_generator_v2.py`：B112② 3 处（`ExpressionReconstructor.__init__` 追踪位、`reset()` 复位、`_process_instruction` CALL 分支 async 补包）。
- `core/cfg/code_generator.py`：YF9 12 行/8 处（dict 路径 2 + AST 路径 2 + 调用实参 4〔pparam/kwparam/var/kw〕+ return/if/while 各 1）。
- 域外/未动：site-packages 零字节差异；tests/、wiki/、scripts/ 零改动；无 git 写操作（仅只读 status/diff/log）。

## §3 前后读数（终稿）

- stage 探针：stamp=r4fix_b112b_c4_20（c4_20 24/24）。
- 同族回归复验：stamp=r4fix_b112b_async_comp_regress → r5_10 13/13、e09b 13/13、r8v8fc 18/18（44/44）。
- 负对照九件：stamp=r4fix_b112b_neg9 → **60/60**（r7_07 7/7、r7_08 8/8、rv8_01 7/7、rv8_02 7/7、r8_06 10/10、r10_04 3/3、r10_15 6/6、r10_21 4/4、rv10_32 8/8）。
- 邻域 16 探针：stamp=r4fix_b112ab_neigh → **79/86 与 R3 r3q6b 基线逐位一致**（x02 6/7、x01 5/7、x04 7/7、c04 5/6、c13 3/3、m02 2/3、m06 1/1、r8_07 11/11、r8_10 11/12、rv9_01 5/5、rv9_02 4/5、r10_04 3/3、r10_15 6/6、r10_21 4/4、v_b73 3/3、v_b75 3/3）。
- 复验绿组：stamp=r4fix_b112ab_greens → r8_08 9/9、n9v9 6/6（rv8_02/r10_04/r10_15 已于负对照 60/60 中复验）。
- B128 回归复验：stamp=r4fix_b128_sanity → c4_20 24/24、r5_10 13/13、e09b 13/13、r8v8fc 18/18、r8_08 9/9、n9v9 6/6（83/83）；stamp=r4fix_b128_neg9 → 负对照九件 60/60 + 邻域 16 探针 79/86（与 r3q6b 基线逐位一致；重叠 r10_04/r10_15/r10_21 计一次，合计 126/133）。
- B47 回归复验：stamp=r4fix_b47_r7_06 → r7_06 10/10、e12d 11/11、c4_20 24/24（45/45）；stamp=r4fix_b47_sanity → r5_10 13/13、e09b 13/13、r8v8fc 18/18、r8_08 9/9、n9v9 6/6、r7_07 7/7、r7_08 8/8（74/74）；stamp=r4fix_b47_neg9 → 负对照九件全 60/60 + 邻域 16 探针 79/86（红单元逐位与基线一致：x02 for_in_match、x01 if_in_while/if_in_match、c04 CTryNest、m02 module、r8_10 r8_x_for_iter_ternary、rv9_02 while_with_whole_body）。
- YF9 回归复验：stamp=r4fix_yf9 → yf9_prec 2/2、assign 2/2、from 6/6、e12b 18/18、e12f 2/2、r7_06 10/10、e12d 11/11（51/51）；stamp=r4fix_yf9b → yf9_boolop 2/2；stamp=r4fix_yf9c → arg 3/3、ret 2/2、cond 2/2、e12c 3/3、prec 2/2、boolop 2/2、r7_06 10/10、c4_20 24/24（48/48）；stamp=r4fix_yf9_sanity → r5_10 13/13、e09b 13/13、r8v8fc 18/18、r8_08 9/9、n9v9 6/6、r7_07 7/7、r7_08 8/8、e12d 11/11（85/85）；stamp=r4fix_yf9_neg9 → 负对照九件 60/60 + 邻域 16 探针 79/86（111/118，红单元与基线逐位一致）。
- small34 广度预检（code_generator 改动面广，先跑 E 门禁 Phase 3）：`_r4_small34_check.py` → units **1568/1568**、files **34/34 success**、`pyc_verify compare` vs baseline42：**REGRESSIONS=0 IMPROVED=33**（34 件原失败文件 33 件转 success，quotation 含内）。
- B112①/B47 合成补强后全量回归（本轮 4 处新编辑生效后重跑）：stamp=r4all_green1 → 18 探针 **118/118**（c4_20 24/24、e12d 11/11、e12b 18/18、e12c 3/3、e12f 2/2、r7_06 10/10、yf9 七件 19/19、synth 五件 31/31）；stamp=r4all_sanity1 → **85/85**（r5_10 13/13、e09b 13/13、r8v8fc 18/18、r8_08 9/9、n9v9 6/6、r7_07 7/7、r7_08 8/8、e12d 11/11）；stamp=r4all_neg9_1 → 负对照九件 **60/60** + 邻域 16 探针 79/86（126/133，红单元与基线逐位一致：x02 for_in_match、x01 if_in_while/if_in_match、c04 CTryNest、m02 module、r8_10 r8_x_for_iter_ternary、rv9_02 while_with_whole_body）；small34 复跑（`_r4_small34_check2.out.txt`）→ units **1568/1568**、files 34/34 success、**REGRESSIONS=0 IMPROVED=33** 复现。

## §4 复核（终稿）——合成门禁（B 类交叉变体，test_repros/round4/rec1_synth_*.pyc）

每修复族 ≥2 交叉变体（族外宿主/不同消费形态/多层嵌套），以 `rec1_run.py` 驱动读 `pyc_verify single`：

| 合成探针 | 族 | 变体要点 | 初始 | 最终 |
|---|---|---|---|---|
| rec1_synth_b112a_asyncgen | B112① | 直落 body `yield await u(x)`；if 守卫宿主；async with 宿主 | 6/8 | **8/8**（补强后） |
| rec1_synth_b112b_closure | B112② | 同步 def 内 async 闭包 list/set 推导式；双层嵌套 + if 过滤 | 11/11 | **11/11** |
| rec1_synth_b128_await_cond | B128 | if/elif 条件宿主；`v = await io.a(i) if i else 0`（跨 B47） | 4/4 | **4/4** |
| rec1_synth_b47_ternary | B47 | 真臂 await/假臂常量；赋值位形假臂 await；双臂 binop | 3/4 | **4/4**（补强后） |
| rec1_synth_yf9_ctx | YF9 | 嵌套 yield `(yield i)+1`；比较操作数 `(yield i)<3`；移位操作数 `(yield i)<<2` | 3/4→4/4 | **4/4** |

- YF9 变体调整说明：初版 s_ternary_arm（`x = (yield i) if i else 0`，yield 作三元臂值）失败模式为「TernaryRegion 未成立→退化为 if 语句」，属**区域装配层**（yield 挂起协议与三元区域边界交互）既有局限，与本修（仅增删括号的优先级/语境层）无关；yield-in-ternary-arm 不在 R4 红项（yf9 族）与负对照清单内，记为域外残余（§6），变体替换为同族 s_shift（移位操作数位形）。调整后 4/4。
- 合成门禁共暴露 3 个真实族内缺口（b112a 直落/with 宿主、b47 赋值位形）并全部补强归零；b112b/b128 零缺口。
- 证据文件：`_r4_e07_dump.py/.out.txt`、`_r4_e07_trace.py/.out.txt`、`_r4_e07_recon.py/.out.txt`、`_r4_e07_bsi.py/.out.txt`、`_r4_heads.py`（head 模拟）、`_r4_r5_10_{now,head,proto}.py`、`_r4_e07_matrix_proto.py`、`_r4_c4_20_proto.py`、`_r4_b112b_proto.py`、`_r4_e05_b112a.out.txt`、`_r4_b128_proto.py`、`_r4_b47_proto.py`、`_r4_yf9_proto.py`、`_r4_synth_b112a_trace{,2,3,4}.py/.out.txt`、`_r4_synth_b112a_cfg.py`、`_r4_small34_check.py`+`_r4_paths34.json`+`r4_small34_report_{a,b,new}.json`、合成源/产物 `test_repros/round4/rec1_synth_b112{a,b}*/rec1_synth_b{128,47}*/rec1_synth_yf9*`、stamps `rec1_probes_r4fix_*.json` 与 `rec1_probes_r4all_{green1,sanity1,neg9_1}.json`、`rec1_probes_r4synth_try*.json`。

## §5 门禁读数（终稿）——E 全量终验（final_verify_run_r4.py，493s，基线=69132f55）

编排证据：`final_verify_log.txt` + `final_verify_summary.json` + `regen_shard{0..7}.json` + `shard{0..7}_report_new.json`。

- regen 八分片：402/402 全部 rc=0，失败记录 **0**（regen_shard*.json 空）。
- verify 八分片（含 shard7 拆分）：**402 文件全 success，units 6617/6617，files_failure=0**（786+469+538+887+855+999+801+1282）。
- compare×8 vs baseline42：**REGRESSIONS=0（八分片均）**、IMPROVED=0——冻结面逐位稳定。
- small34：`SMALL34-A/B` 全 success，合并 **1568/1568、34/34 success**；`SMALL34-CMP` Movement Matrix：**failure→success 33、REGRESSIONS=0**。
- quotation 单验：`site-packages/fly/data/quotation.pyc` → **153/153 success_rate=100.00%**。
- tests 七套件：`2 failed, 282 passed, 2 xpassed in 8.39s`——失败名单与 R3 基线**逐项一致**（test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function；基线即红，非本轮退化）。
- IV.2 自检：IMPORT_OK ✓、COMPILE_OK ✓、BOM 单头（region_ast_generator/region_analyzer）✓、instrumentation code 命中 0（字符串内 3 处与 R3 同款既有文案：21731/22466/54012）、**G3_forbidden_prefix_new_defs=0**。
- site-packages 零字节差异（git status -- site-packages/ 空）；core/ 仅 3 个预期 M 文件。

## §6 落地声明（终稿）

- 产物：`core/cfg/region_ast_generator.py`、`core/cfg/code_generator.py`、`core/cfg/ast_generator_v2.py` 三文件修复冻结（+447/-13），标记 25 行；探针只增于 `.trae/specs/attain-true-completeness/test_repros/round4/`（含 5 合成件），本目录证据/工具链不动 core 之外任何受管目录。
- 判据合规：I.4 白名单（块内 opcode 形态/前驱后继边/异常边/区域成员/登记状态；零语料、文件名、行号特判）；C1 各门未命中即逐位回退；C2/C3 冻结面 REGRESSIONS=0；G3=0；G4=0；标记 [Bn-V3R4]。
- 残余（登记，不在 R4 范围）：
  1. yield-三元臂值位形（`x = (yield i) if i else 0`）：TernaryRegion 未成立退化为 if 语句，属区域装配层既有局限；不在 R4 红项/负对照/合成清单内，探针已换同族变体（§4 注记）。
  2. r5_10 附注：B112② 修复使其复原为遗留 OK.py 基线 13/13；该形态在 HEAD 即已回退（非本轮所致），不在 R3/R4 门禁清单。
- 交付：FIX.md 为唯一对本轮规范的中文存档；未做任何 git 提交（冻结就绪待审）。
