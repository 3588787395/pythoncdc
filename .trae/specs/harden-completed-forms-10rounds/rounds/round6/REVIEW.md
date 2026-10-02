# Round 6 评审（对抗性审查：With/AsyncWith 区域 + async 五件套）

- 评审人：评审工程师（Round 6，对抗攻击者）
- 日期：2026-10-02
- 唯一判据：`scripts/pyc_verify.py`（附件 pylingual `compare_pyc`，逐 code object 单元判 Equal，全 Equal 才 success）；验证方式 = `python -c "import py_compile; py_compile.compile(file='test_repros/round6/X.py', cfile='test_repros/round6/X.pyc', doraise=True)"` → `python pycdc.py -o test_repros/round6/XOK.py test_repros/round6/X.pyc` → `python scripts/pyc_verify.py single test_repros/round6/X.pyc`（本机 Python 3.11.7）。
- 硬约束遵守：未修改任何 `core/`、`scripts/`、`pycdc.py`、wiki、既有 `*OK.py`、`site-packages/`、`.trae/specs/` 既有内容；每条 shell 命令 ≤300 s；全部 `*OK.py` 由 `pycdc.py -o` 生成，零手改；未 git commit。
- 既有/新破口归属判定方法：当前 tracked 树零改动（`git status` 仅 1 项未跟踪 = 本轮 `test_repros/round6/`），HEAD=4135e6db（round6 启动快照，round5 归档后无 core 变更），且 §2 四支 Round 5 残留读数与 round5 REVIEW2 登记值逐一相符（零漂移）——管线状态与 round5 复核时点一致。故本轮全部破口 B29–B35 均为**修复前已存在缺口（本轮攻击面新暴露）**，非任何在途变更引入；无可 stash 在途变更（树净），归属由「树净 + 残留零漂移」双证据链锁定。

---

## §1 执行摘要

### 攻击面读数汇总

**15 攻击文件 + 1 负对照（n6_01）= 16 文件（达标 ≥14）；可比单元 95（达标 ≥80），MATCH 66/95 = 69.47%；另有 3 文件 compile_error（r6_05 / r6_07 / n6_01，名义 20 单元不可比），名义总量 115。** MISMATCH 文件 13/16。**wiki 总纲将 With/AsyncWith（:146/:155/:180）与 async 五件套（:187）判「完备」的声明被对抗证伪**：8 攻击面中 0 面全封闭，5 个破口族（B29–B33）+ 2 独立破口（B34/B35）。

**负对照 n6_01 失败（compile_error 0/0）——按任务书属严重登记项**：该文件同步 with 三态（with 无 as / with as / 双管理器 as）在产物中全部正确，失败纯由其 async 半区（`async with` 体缩进丢失 → IndentationError、`async for` 体注入 `return`）触发，与 r6_05/r6_14 的 B29/B30 签名同源——**判定为既有缺口的文件级灭杀效应，非判据误报、非回归**（同步 with 简单形态在 r6_01/r6_03/r6_04/r6_08/r6_10/r6_11 等正向文件中另有 20+ 个 MATCH 单元旁证判据判别力）。

### 破口清单（B29 续接）

| 编号 | 破口 | 优先级 | 主复现 |
|---|---|---|---|
| **B29** | async with 区域装配整体失效：体缩进丢失→IndentationError 文件级灭杀 / 体降级裸表达式+幻影 `if True: pass` / 体被 `return None`+`await None(None, None)` 幻影调用顶替 | **P0** | r6_05（0/6 compile_error）、r6_12（3/6）、r6_06（1/5）、n6_01 |
| **B30** | async for 体/else 块装配错序：END_ASYNC_FOR else 块内容发射为首条体语句、真体后置且被注入 `return out`/`return None` 短路（体不可达） | **P0** | r6_14（2/7）、r6_07（0/6 compile_error）、r6_06、r6_08 |
| **B31** | await 表达式仅存赋值 RHS 一隅：return 位/binop 操作数/subscript 基底/compare 操作数/dict 值/列表元素/调用实参全部坍缩为裸 Expr 且返回值改常量/None | **P0** | r6_13（3/8）、r6_08（ad_await_dict/list/arg）、r6_07（ad_return_await） |
| **B32** | with 体 if 内 return 剥除（B27 同族、with 宿主）：`with mgr as x: if v: return x` → `if v: x`；try 体 `return v` 被 finally 内 with 感染同杀 | P1 | r6_02（6/7）、r6_03（6/7）、r6_10、r6_11（4/6）、r6_04（10/11） |
| **B33** | withitem 元组/星号目标整体丢失：`with mgr as (a, *rest)` → 裸 with + 幻影 `a, *rest = None`；`as (a, (b, c))` → 裸 with + 未定义名 | P1 | r6_01（7/8）、r6_09（6/8） |
| **B34** | for-else 体被幻影 `while False: pass` 顶替、return 上提 | P2 | r6_10（3/6） |
| **B35** | 双 yield from 之间的普通 yield 静默丢弃：`yield from xs; yield 0; yield from ys` → 中段 `yield 0` 消失 | P2 | r6_15（7/8） |

### 交接单（→ §6 详表）

P0×3（B29/B30/B31，全部为 async 半区语义级灭杀，含 3 文件级 compile_error 不可比面）；P1×2（B32/B33）；P2×2（B34/B35）。wiki 台账修订建议：With/AsyncWith 与 async 五件套由「完备」降格为「浅层封闭：同步 with 线性体 + async 单累加器 async for + await 赋值 RHS 位」，登记 B29–B35 锚点。

---

## §2 Round 5 残留复验（B26/B27/B28 登记读数）

| 登记项 | 探针 | round5 REVIEW2 登记读数 | 本轮读数（single，现树） | 失败单元签名（本轮实测） | 判定 |
|---|---|---|---|---|---|
| B26 | `test_repros/round5/rv5_23_b23_var.pyc` | 8/10（`a_genexp` Different bytecode + `.a_genexp.<genexpr>` Missing bytecode，产物 `return None(ait())`） | **8/10（80.00%）** | `<module>.a_genexp` Different bytecode + `<module>.a_genexp.<genexpr>` Missing bytecode（产物首行即 SyntaxWarning: 'NoneType' object is not callable → `return None(ait())`） | **持平，零偏差** |
| B27 | `rv5_24_b24_var.pyc` | 8/9（`t_nested_try` Different control flow） | **8/9（88.89%）** | `<module>.t_nested_try` Different control flow（唯一失败单元，签名一致） | **持平，零偏差** |
| B28 | `rv5_25_b25_var.pyc` | 11/12（`lam_in_comp_starkw.<listcomp>.<lambda>` Different bytecode） | **11/12（91.67%）** | `<module>.lam_in_comp_starkw.<listcomp>.<lambda>` Different bytecode（唯一失败单元，签名一致） | **持平，零偏差** |
| B27/B28 鉴别诊断 | `rv5_26_diag.pyc` | 4/6（`diag_vararg_fn.<lambda>` Different bytecode + `diag_nested_try_plain` Different control flow） | **4/6（66.67%）** | 两失败单元与登记完全一致 | **持平，零偏差** |

**四支全部持平，读数不变好不变差，登记维持。** 复验偏差数 = **0**。

---

## §3 逐面攻击明细（16 文件全表，读数均以 pyc_verify single 输出为准）

### 面 1 — with 基础（r6_01_with_basic，7 函数，8 单元，**7/8 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| w_no_as | `with mgr: return 1` | MATCH | — |
| w_as_single | `with mgr as f: return f` | MATCH | — |
| w_two_mixed | `with m1 as a, m2: return a` | MATCH | — |
| w_three | `with m1 as a, m2 as b, m3 as c` | MATCH | — |
| w_tuple_unpack | `with mgr as (a, b): return a + b` | MATCH | 产物 `with mgr as (a, b):` 正确 |
| w_star_unpack | `with mgr as (a, *rest): return a + rest[0]` | **MISMATCH（Different bytecode）** | 产物降级裸 `with mgr:` + 幻影 `a, *rest = None` —— **withitem 星号目标丢失并注入 None 赋值**（→B33） |
| w_subscript_mgr | `with mgrs[0] as v` | MATCH | — |

失败签名：`<module>.w_star_unpack` Different bytecode。破口：**B33**。

### 面 2 — with 嵌套（r6_02_with_nest，6 函数，7 单元，**6/7 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| w_nest3 | 3 层嵌套 with | MATCH | 产物合并为 `with m1, m2, m3:`（字节等价重排，非破口） |
| w_nest_same_name | 嵌套 as 捕获同名 x | MATCH | 同上合并形 |
| w_with_if | `with mgr as x: if v: return x` | **MISMATCH（Different control flow）** | 产物 `if v: x` —— **if 体 return 剥除为 Expr**（→B32） |
| w_with_for | with 内 for | MATCH | — |
| w_with_while | with 内 while | MATCH | — |
| w_with_try | with 内 try/except return | MATCH | — |

破口：**B32**。

### 面 3 — with 控制流（r6_03_with_flow，6 函数，7 单元，**6/7 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| w_return | with 内 return | MATCH | — |
| w_break | with 内 for×break | MATCH | — |
| w_continue | with 内 for×continue | MATCH | — |
| w_raise | with 内 raise | MATCH | — |
| w_return_in_nest | 双层嵌套 with 内 return | MATCH | — |
| w_early_return | `with mgr as x: if v>0: return x; x=v` | **MISMATCH（Different control flow）** | 产物 `if v > 0: x / else: x = v` —— **早退 return 剥除**（→B32） |

破口：**B32**（与面 2 同签名：return 位于 with 体 if 分支内）。

### 面 4 — with 组合（r6_04_with_combo，6 函数，11 单元，**10/11 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| w_comp | with 内 listcomp return | MATCH | — |
| w_lambda | with 内 lambda 赋值 | MATCH | — |
| w_genexp_arg | with 内 sum(genexp) | MATCH | — |
| w_dictcomp | with 内 dictcomp | MATCH | — |
| w_finally_wraps_with | try/finally 包 with 包 return | MATCH | — |
| w_with_wraps_finally | `with: try: return xs[0] finally: return xs` | **MISMATCH（Different bytecode）** | 产物 finally 体 `xs / return None` —— **`return xs` 剥除 + 显式 return None 注入**（→B32 族，try/finally×with 叠加） |

破口：**B32**。

### 面 5 — AsyncWith 基础（r6_05_asyncwith_basic，5 函数，**compile_error 0/0，名义 6 单元不可比**）

产物全部函数体破坏：`async with mgr:` 后 **`return 1` 不缩进**（IndentationError: expected an indented block after 'with' statement on line 5，直接 py_compile 实测）；`aw_as` 体降级 `f` 裸表达式 + 幻影 `if True: pass`；`aw_two`/`aw_three` 多管理器体坍缩为 `a + b` / `a + b + c` 裸表达式 + 多条 `await None(None, None)` 幻影调用；`aw_await_body` 体 `await g(f)` 后随幻影 `if True: pass`。pyc_verify 报 **status=compile_error units=0/0**。

破口：**B29（P0）**——async with 三态灭杀：缩进丢失（文件级）/体降级裸表达式/幻影 await None 调用。

### 面 6 — AsyncWith 嵌套互包（r6_06_asyncwith_nest，4 函数，5 单元，**1/5 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| aw_in_af | async for 内 async with | **MISMATCH（Different control flow）** | 体被注入 `return None`，async with 后随幻影 `if True: pass`（→B29/B30） |
| af_in_aw | async with 内 async for | **MISMATCH（Different control flow）** | 体尾部 `total` 降级裸表达式 + 幻影 if True（→B29） |
| aw_nest2 | 双层 async with | **MISMATCH（Different control flow）** | 内层体 `a + b` + `await None(None, None)` + `return None` 幻影序列（→B29） |
| aw_af_aw | async for×async with×async for 三层 | **MISMATCH（Different control flow）** | 双 `return None` 注入 + `await None(None, None)` 幻影（→B29/B30） |

破口：**B29 + B30 复合**。

### 面 7 — async def 五件套（r6_07_async_five，5 函数，**compile_error 0/0，名义 6 单元不可比**）

产物：`af_unpack_else` else 体 `result.append(-1); return result` **发射于真体 `result.append(k + v)` 之前**（体不可达）；`ad_return_await` **`return await g(3)` → `await g(3)`（return 剥除，→B31）**；`ag_af_in_ag` 被注入 `return None` 于 async for 体前 → 直接 py_compile 报 **SyntaxError: 'return' with value in async generator**（line 23），文件级灭杀。`ad_await_chain`（赋值 RHS await 链）与 `ag_yield_await` 正确。

破口：**B30（P0）+ B31（P0）**。

### 面 8 — 交叉组合（r6_08_async_cross，6 函数，8 单元，**3/8 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| for_aw | for 内 async with | **MISMATCH（Different control flow）** | `return out` 注入 async with 前（→B29/B30） |
| af_try | async for 内 try/except | **MISMATCH（Different control flow）** | handler 体 `out.append(x)` 降级 `pass`（→B30 族） |
| ad_await_dict | await 作 dict 值 | **MISMATCH（Different bytecode）** | `await g(1)` 降级语句 + `return {}` —— **dict 字面量值丢失**（→B31） |
| ad_await_list | await 作列表元素 | **MISMATCH（Different bytecode）** | 两条 await 降级语句 + `return []`（→B31） |
| ad_await_arg | await 作实参（嵌套 await 实参） | **MISMATCH（Different control flow）** | `await g(1)` 单条残留，外层 h(...) 调用整体丢失（→B31） |
| ad_with_comp | async def 内同步 with 推导式 | MATCH | — |

破口：**B29/B30/B31 复合**。

### 面 9 — 多管理器/复合管理器（r6_09_with_multimgr，7 函数，8 单元，**6/8 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| mk / w_call_mgr / w_attr_mgr / w_two_noas / w_ternary_mgr | 调用形/属性形/双无 as/三元管理器 | 全 MATCH | w_ternary_mgr `with (m1 if v else m2) as x:` 正确（ternary-with 既有守卫 :3316-3328 生效旁证） |
| w_deep_unpack | `with mgr as (a, (b, c)): return a+b+c` | **MISMATCH（Different bytecode）** | 产物裸 `with mgr: return a + b + c` —— **元组目标整体丢失，体引用未定义名**（→B33） |
| w_star_mid | `with mgr as (a, *rest, b):` | **MISMATCH（Different bytecode）** | 产物 `with mgr: a, *rest, b = None` —— **幻影 None 赋值**（→B33） |

破口：**B33**。

### 面 10 — with 深度混合（r6_10_with_deepmix，5 函数，6 单元，**3/6 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| w_loop_nest_with | with→for→with→if→return | **MISMATCH（Different control flow）** | 内层 `if y: x` —— return 剥除（→B32） |
| w_break_in_with | with 内 for-else（else 内 return） | **MISMATCH（Different control flow）** | else 体被 **`while False: pass` 幻影循环**顶替、`return -1` 上提出 else（→B34） |
| w_assign_after_with / w_while_in_with | with 后赋值 / with 内 while×break | MATCH | — |
| w_nested_flow | 双 with 嵌套 if-continue/break | **MISMATCH（Different control flow）** | 产物结构重排后 elif 化、尾部 `return x` 丢失（→B32 族） |

破口：**B32 + B34**。

### 面 11 — with×try 混合（r6_11_with_trymix，5 函数，6 单元，**4/6 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| w_try_in_with | with 内 try/except return | MATCH | — |
| w_with_in_except | except 内 with return | MATCH | — |
| w_with_in_finally | `try: return v finally: with mgr: pass` | **MISMATCH（Different control flow）** | 产物 try 体 `v` —— **`return v` 剥除**（→B32；B27 嵌套 try 同族、宿主换 finally×with） |
| w_tryfin_with_tryfin | try→with→try/finally 包 return | **MISMATCH（Different control flow）** | 内层 `return xs[0]` → `xs[0]`（→B27/B32 复合） |
| w_raise_caught_outside | with 内 raise 外层接住 | MATCH | — |

破口：**B32**（B27 在 with 宿主下的扩展暴露）。

### 面 12 — AsyncWith 控制流（r6_12_asyncwith_flow，5 函数，6 单元，**3/6 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| aw_return | `async with mgr: return v` | **MISMATCH（Different control flow）** | 体降级 `v` 裸表达式 + 幻影 `if True: pass`（→B29） |
| aw_break | async with 内 async for×break | **MISMATCH（Different control flow）** | 体尾 `x` 裸表达式 + 幻影 if True（→B29） |
| aw_continue | async with 内 async for×continue | MATCH | — |
| aw_raise | async with 内 raise | **MISMATCH（Different control flow）** | raise 后幻影 `if True: pass`（→B29；语义等价性破坏在控制流差异） |
| aw_await_expr | `async with mgr as f: return (await g(f)) + f` | **MISMATCH（Different control flow）** | 体 `await g(f); f` —— return 与 binop 全部瓦解（→B29+B31 复合） |

破口：**B29（+B31）**。

### 面 13 — await 位置矩阵（r6_13_async_await_pos，6 函数，8 单元，**3/8 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| ad_await_chain | 赋值 RHS await 链 `a = await g(1); b = await g(2)` | MATCH | —（await 唯一幸存位形） |
| ad_await_while | while 体 await | MATCH | — |
| ad_await_in_comp | listcomp 内 await | **MISMATCH（Different control flow）** | `[await g(x) for x in xs]` → 裸推导式语句（→B31+B23 族边界） |
| ad_await_binop | `return await g(1) + await g(2)` | **MISMATCH（Different bytecode）** | 两条裸 await 语句，return 丢弃（→B31） |
| ad_await_subscript | `return (await g(1))[0]` | **MISMATCH（Different bytecode）** | `await g(1)` + `return 0` —— 下标链断裂（→B31） |
| ad_await_nested | `return h(await g(await g(1)))` | **MISMATCH（Different control flow）** | 单条 `await g(1)` 残留（→B31） |
| ad_await_compare | `return await g(1) > 3` | **MISMATCH（Different bytecode）** | `await g(1)` + `return 3` —— 比较被常量替代（→B31） |

破口：**B31（P0）**。

### 面 14 — async for 形态矩阵（r6_14_asyncfor_forms，6 函数，7 单元，**2/7 failure**）

| 函数 | 源形态 | 读数 | 产物形态对照 |
|---|---|---|---|
| af_break_continue | if-continue / if-break | MATCH | — |
| af_unpack | target 解包 `async for a, b in ait` | **MISMATCH（Different control flow）** | `return out` 注入体前、真体后置不可达（→B30） |
| af_else | async for-else | **MISMATCH（Different control flow）** | else 体 `out += 100; return out` 抢先于真体（→B30） |
| af_nested | 嵌套 async for | **MISMATCH（Different control flow）** | `return out` 注入外层体前（→B30） |
| af_return_body | 体含条件 return | **MISMATCH（Different control flow）** | `return None` 注入体前（→B30） |
| af_star | 星号 target `async for a, *rest` | **MISMATCH（Different control flow）** | `return out` 注入（→B30+B33 族） |

破口：**B30（P0）**。正向旁证：单累加器 `out += x`（n6_01.c_asyncfor、r6_12.aw_continue）MATCH —— async for 深于单累加器即破。

### 面 15 — yield from 形态（r6_15_yield_forms，7 函数，8 单元，**7/8 failure**）

| 函数 | 源形态 | 读数 |
|---|---|---|
| make / g_yield_from / g_yield_from_call / g_nested_gen / gen_outer / ag_yield_only | yield from 直/调用形/嵌套/async gen | 全 MATCH |
| g_mixed | `yield from xs; yield 0; yield from ys` | **MISMATCH（Different bytecode）**：产物 `yield from xs; yield from ys` —— **中段 `yield 0` 静默丢弃**（→B35） |

破口：**B35**。

### 负对照（n6_01_control，7 函数，**compile_error 0/0，名义 8 单元不可比**）

| 函数 | 形态 | 产物 |
|---|---|---|
| c_with_simple / c_with_as / c_with_two | 同步 with 三态 | **全部正确**（`with mgr:` / `as f` / 双管理器 `as a, b`） |
| c_asyncwith | `async with mgr: return 2` | `async with mgr:` 后 `return 2` **不缩进** → IndentationError（B29 签名） |
| c_asyncfor | 单累加器 async for | 体被注入 `return out` 于 `out += x` 前（B30 签名） |
| c_await / c_asyncgen | await 语句位 / 简单 async gen | 正确 |

**判定**：同步 with 负对照面成立（判据无误报）；async 半区失败签名与 r6_05/r6_14 完全同源 = B29/B30 既有缺口的文件级灭杀（tracked 树零改动 + §2 残留零漂移 → 非回归）。**负对照失败按任务书如实登记为严重发现，归因 B29/B30 而非新独立破口。**

### 单元合计

可比 95 单元（66 MATCH / 29 MISMATCH）+ 3 文件 compile_error（r6_05 名义 6、r6_07 名义 6、n6_01 名义 8，共 20 单元不可比）。名义 115。

---

## §4 算法合规审计（现树在途变更守卫抽查）

审计对象：本轮 4 个高频被改 core 文件（`comprehension_generator.py`、`code_generator.py`、`ast_converter.py`、`ast_generator_v2.py`）+ `region_ast_generator.py`。**基线事实：`git status` tracked 零改动（HEAD=4135e6db），git diff 为空——现树即 round5 归档态，无在途 hunk 可逐查，故按任务书做 8 项落地标记抽查 + 全局卫生检查。**

| # | 审计项 | 方法 | 结果 | 判定 |
|---|---|---|---|---|
| 1 | [Round5-B20] 落地标记 | grep core/cfg | comprehension_generator.py :1269/:1307/:1334/:1351（4 处：clause 过滤窗/窗起点/互斥归属/iter 窗） | 在位 ✓ |
| 2 | [Round5-B21] 标记 | 同上 | comprehension_generator.py :1323/:1726 域 + code_generator.py :1892/:1893/:1924/:5099/:5488/:5491（8 处，含单元素 Tuple 尾随逗号 arity 与目标渲染委托） | 在位 ✓ |
| 3 | [Round5-B22] 落地机器 | read | `_parse_target_store_sequence`（comprehension_generator.py:1658 定义 + :1325/:1693/:1704/:1708/:1713/:1738 调用点 ≥1 定义多调用）+ `_find_comp_target_names` walrus COPY 守卫（:1644-1647 `COPY arg==1 ∧ 后继 STORE_*` 排除集） | 在位 ✓ |
| 4 | [Round5-B23] 标记 | grep | comprehension_generator.py :288/:1069/:1193/:1269 域/:1280/:1297/:1313/:1353/:1386 + ast_generator_v2.py :1353（10 处：闭包状态机/clause 头/协议块识别/PUSH_NULL 补消费） | 在位 ✓ |
| 5 | [Round5-B24] 标记 | grep | comprehension_generator.py :563/:568/:651/:686/:723/:736（6 处：R9 收窄/认领分支/后继块三重判据/簿记注记） | 在位 ✓ |
| 6 | [Round5-B25] 标记 | grep | ast_converter.py :1001/:1654/:1678/:1727 + code_generator.py :5441（5 处：FunctionObject 分支/arguments dict 挂载/重建器/发射委托） | 在位 ✓ |
| 7 | 判据卫生（用户标识符字面量/start_offset 魔数） | read 抽查 | `_find_comp_target_names`（:1623-1656）与 `_parse_target_store_sequence`（:1658 起）判据仅用操作码形态/COPY arg==1/`.0` 惯例名/UNPACK 位协议，无用户标识符、无 start_offset 魔数 | 通过 ✓ |
| 8 | BOM（G0） | 首 4 字节 | region_ast_generator.py = `efbbbf22`（efbbbf 在位） | 通过 ✓ |
| 9 | 插桩残留 | `git show 7e09e36d` / `45864cc5` 增行 grep `print(/pdb/breakpoint/FIXME/XXX/DEBUG` | 各仅命中 FIX.md 自述行文字本身，代码行零命中；现树 `git diff` 为空 | 通过 ✓ |
| 10 | 文件规模锚点 | 本轮实测 | region_ast_generator.py `_generate_with`（:29919 起）发射 `'AsyncWith' if region.is_async else 'With'`（:31203）——与 wiki :146 `WITH:181 → :29499` 锚点同域（文件已增长，行号漂移约 +1700，wiki 锚点需随 B29 修复同步更新） | 记录 ✓ |

**§4 结论：10 项全过，零违规。** 本轮 zero core 改动，Round 5 修复资产（标记/机器/BOM）完好在位。

---

## §5 破口登记（锚点 + 机制假设 + 条款；B29 起，全部为既有缺口、经本轮攻击面新暴露）

### B29 — async with 区域装配整体失效（**P0**）

- **破坏条款**：C2（结构组合灾难：async with 体三态灭杀）+ 完备性（wiki :146/:155/:187 AsyncWith「完备」证伪）
- **现象与签名（三态）**：
  1. **体缩进丢失 → 文件级灭杀**：`async with mgr: return 1` → 产物 `async with mgr:` 后 `return 1` 顶格（IndentationError: expected an indented block after 'with' statement，r6_05 line 5-6 / n6_01 line 14-15 直接 py_compile 实测）→ 全文件 compile_error；
  2. **体降级裸表达式 + 幻影守卫**：`async with mgr: return v` → `async with mgr: v / if True: pass`；`raise ValueError(v)` 后同随幻影 `if True: pass`（r6_12.aw_return/aw_raise/aw_break、r6_06.af_in_aw）；
  3. **体被幻影调用顶替**：`async with m1 as a, m2 as b: return a + b` → 体 `a + b; await None(None, None); return None; if True: pass`（r6_05.aw_two、r6_06.aw_nest2）——`await None(None, None)` 为 **`__aexit__` await 调用未被归约成 With 节点**的裸露残迹（callable=None 常量 + 双占位实参）。
- **机制假设（锚点实测）**：async with 装配唯一专用路径 = `_generate_with`（region_ast_generator.py:29919 起）内 **:30544 `if region.is_async and not body_stmts:` 闸门**——async 体提取依赖 **:30549-30559「SEND+YIELD 双持有」的 LoopRegion 识别**（`_has_send and _has_yield`）从 LOOP_ELSE 块捞体语句；目标提取仅认 **:30589/:30624 首条 STORE_* 单名**。当体为简单线性 return（无循环覆盖、体块早于闸门被通用块路径以错误块序消费）时 `body_stmts` 为空或错序：缩进态=体块被主块序列认领但 With 节点体发射为空；裸表达式态=体语句被逐块 Expr 化；幻影态=`__aenter__/__aexit__` 协议对（GET_AWAITABLE;SEND;YIELD_VALUE;RESUME）未被 With 装配整体消费，`await None(...)` 幻影与 `if True: pass` 幻影守卫（:3316-3328 ternary-merge 守卫的退化形）漏出。对照组：同步 with 全形态线性体 MATCH（`'With'` 发射 :31203 不走 is_async 分支）。
- **复现组**：r6_05 全体（6 单元不可比）、r6_12.aw_return/aw_break/aw_raise/aw_await_expr、r6_06.aw_nest2/af_in_aw、r6_08.for_aw、n6_01.c_asyncwith（≈12 单元/3 文件级）。
- **状态**：签名级定位（:30544 闸门 + :30556-30558 识别判据 + :31203 发射实测），精确误序分支待修复轮插桩圈定。

### B30 — async for 体/else 块装配错序：else 内容抢先、真体被 `return` 注入短路（**P0**）

- **破坏条款**：C1（体不可达：累加/过滤语义全丢）+ C2 + 完备性（wiki :187 async for「完备」证伪）
- **现象与签名**：`async for a, b in ait: out += a * b` → `async for a, b in ait: return out; out += a * b`（r6_14.af_unpack）；async for-else 的 else 体 `out += 100; return out` **发射于真体之前**（r6_14.af_else、r6_07.af_unpack_else）；`async for x: if x > 5: return x` → `async for x: return None; if x > 5: return x`（af_return_body）；嵌套 async for 外层体同注入（af_nested、r6_06.aw_in_af/aw_af_aw、r6_08.for_aw）。注入的 `return` 取值恰为循环后继块（else 块/循环出口块）的首个返回值——**循环出口块被误并入体首**。产物 r6_07 中该形态直接触发 `SyntaxError: 'return' with value in async generator`（async gen 内注入 return）→ 文件级灭杀。
- **机制假设**：async for 的 END_ASYNC_FOR 协议尾（GET_ANEXT;LOAD_CONST None;SEND;YIELD_VALUE;RESUME;JUMP_BACKWARD_NO_INTERRUPT;END_ASYNC_FOR）构成的 **else/出口块与体块在块排序中错位**：体生成按 start_offset 线性收集时，出口块（含 `return out`）偏移小于体块或被 block role 误判为体首 → 注入于体前。旁证：单累加器形态 `out += x`（无 else、出口无显式 return）MATCH（n6_01.c_asyncfor、r6_12.aw_continue）——出口块一旦携带显式 return/else 体即破；对照 r5 B23 `_find_async_clause_heads`（comprehension_generator.py:1192-1240）在推导式侧已正确解析同一协议块，**非推导式（语句级 async for）路径无等价协议块消费器**。
- **复现组**：r6_14 五失败函数、r6_07.af_unpack_else/ag_af_in_ag、r6_06.aw_in_af/aw_af_aw、r6_08.for_aw/af_try（≈15 单元/1 文件级）。
- **状态**：签名级定位，块排序/角色判定分支待插桩圈定。

### B31 — await 表达式仅存「赋值 RHS」一隅，其余位形数据流断裂（**P0**）

- **破坏条款**：C1（返回值→常量/None：调用结果静默丢弃）+ 完备性（wiki :187 await_expr「完备」证伪）
- **现象与签名（await 幸存矩阵）**：
  - 幸存：赋值 RHS（`a = await g(1)` r6_07.ad_await_chain MATCH）、裸语句位、while 体语句位（r6_13.ad_await_while MATCH）；
  - 坍缩：`return await g(3)` → `await g(3)`（return 剥除，r6_07.ad_return_await）；`return await g(1) + await g(2)` → 两条裸 await（binop 断）；`return (await g(1))[0]` → `await g(1); return 0`（下标断）；`return await g(1) > 3` → `await g(1); return 3`（比较断）；`return {'k': await g(1)}` → `await g(1); return {}`（dict 值断）；`return [await g(1), await g(2)]` → `return []`（列表断）；`return h(await g(await g(1)))` → `await g(1)`（实参断，外层调用整体丢失）。
- **机制假设（锚点实测）**：Await 节点构造于 `ast_generator_v2.py:1165`（GET_AWAITABLE 处理器），其作为独立表达式参与组合的挂载仅在 **:1188/:1202/:2976/:6053/:7717 等点的「栈顶即 Await」特判**——即 await 后**紧跟**消费指令（STORE/POP_TOP）的布局才被认领；当 await 值需穿越组合指令（BINARY_OP/BINARY_SUBSCR/COMPARE_OP/BUILD_MAP/BUILD_LIST/CALL 的操作数栈），栈序重组把 Await 降级为独立 Expr 语句、其栈上值由后续常量/None 顶替。对照组：同步 Call 同位形（`return h(g(1))` 类）在 r5 面全 MATCH——破口特异于 await 的双指令形态（CALL;GET_AWAITABLE;SEND;…;POP_TOP 悬挂）。
- **复现组**：r6_13 五失败函数、r6_08.ad_await_dict/ad_await_list/ad_await_arg、r6_07.ad_return_await、r6_12.aw_await_expr（≈13 单元）。
- **状态**：签名级定位（:1165 构造点 + :1188/:1202 特判族实测），组合挂载缺失的精确分支待圈定。

### B32 — with 体 if 内 return 剥除（B27 同族、with 宿主）（**P1**）

- **破坏条款**：C1（早退语义丢失：函数改走 fall-through 返回）
- **现象与签名**：`with mgr as x: if v: return x` → `if v: x`（r6_02.w_with_if）；`with mgr as x: if v > 0: return x else: x = v` → if 体 `x`（r6_03.w_early_return）；with→for→with→if 内 return 同杀（r6_10.w_loop_nest_with）；`try: return v / finally: with mgr: pass` → try 体 `v`（r6_11.w_with_in_finally）；`try: return xs[0] / finally: return xs`（with 包 try/finally）→ finally 体 `xs; return None`（r6_04.w_with_wraps_finally）；双层 try×with×finally 同杀（r6_11.w_tryfin_with_tryfin）。
- **机制假设**：与 B27 同根——return 值穿越清理段的块布局下，B24 落地的单层后继判据 `_find_returns_pending_value_successor`（comprehension_generator.py:685-797）仅服务推导式认领路径；**with 体路径的 return 值在「WITH_EXCEPT_START 清理 if + 块 3.11 异常表切块」布局下未命中任何 return 认领器 → 通用块路径把 RETURN 前值消费为 Expr**。r6_11.w_with_in_finally 证实与 finally×with 的异常表叠加相关（B27 为 finally×try 嵌套，本轮为 finally 体含 with）。
- **复现组**：r6_02.w_with_if、r6_03.w_early_return、r6_04.w_with_wraps_finally、r6_10.w_loop_nest_with/w_nested_flow、r6_11.w_with_in_finally/w_tryfin_with_tryfin（8 单元）。
- **状态**：签名级定位（B27 同族机制外推 + 产物对照），with 清理段块布局的精确判据缺口待圈定。

### B33 — withitem 元组/星号目标整体丢失：幻影 `= None` 赋值注入（**P1**）

- **破坏条款**：C1（绑定结构失真：未定义名引用/幻影赋值）+ 完备性（wiki :155 withitem「完备」证伪）
- **现象与签名**：`with mgr as (a, *rest)` → `with mgr:` + 体首注入 `a, *rest = None`（r6_01.w_star_unpack，Different bytecode：重编译多出 LOAD_CONST None + UNPACK_EX）；`with mgr as (a, *rest, b)` → `a, *rest, b = None`（r6_09.w_star_mid）；`with mgr as (a, (b, c))` → 裸 `with mgr:` + 体引用未定义 a/b/c（r6_09.w_deep_unpack，目标整体蒸发）。对照组：`with mgr as (a, b)`（扁平二元）与全部单名 as MATCH——**单名 STORE 可达，UNPACK 序列 target 不可达**。
- **机制假设（锚点实测）**：withitem target 提取仅认「首条 STORE_* 的 argval 单名」（region_ast_generator.py:30589-30592 / :30624-30625 两处 `opname in ('STORE_FAST',…)` → `_async_target = _first_real_instr.argval`；同步路径同型单名假设），**无 r5 B21 为推导式落地的 `_parse_target_store_sequence` 等价结构解析**（UNPACK_SEQUENCE/UNPACK_EX arity/星号位）；元组/星号 target 的 UNPACK 指令既不进 With.items.optional_vars 也不被认领，落入体块后经 None 常量回填成幻影赋值或直接蒸发。修复可复用 comprehension_generator.py:1658 既有结构解析器（跨区域类型共享判据，非白名单）。
- **复现组**：r6_01.w_star_unpack、r6_09.w_deep_unpack/w_star_mid（3 单元）。
- **状态**：锚点级定位（:30589/:30624 单名假设实测 + 扁平对照 MATCH）。

### B34 — for-else 体被幻影 `while False` 顶替（**P2**）

- **破坏条款**：C1（else 体语义丢失）+ C3（幻影循环注入改变结构）
- **现象与签名**：`with mgr: for x in xs: if x: break / else: return -1` → 产物 else 体为 **`while False: pass`** + `return -1` 上提出 else（r6_10.w_break_in_with，Different control flow）。真源 for-else 的 else 体块（无循环体）被通用循环识别器误判为「零迭代循环」并发射 `while False` 占位。
- **机制假设**：else 体块入口判定依赖回边存在性；else 体首指令为 return 时块无回边、被 LoopRegion 识别器以空体循环吞并后以 `while False` 重放。仅此一单元复现，机制圈定留修复轮。
- **复现组**：r6_10.w_break_in_with（1 单元）。

### B35 — 双 yield from 之间普通 yield 丢弃（**P2**）

- **破坏条款**：C1（产出序列缺元素：`yield 0` 静默消失）
- **现象与签名**：`yield from xs; yield 0; yield from ys` → `yield from xs; yield from ys`（r6_15.g_mixed，Different bytecode：重编译少一条 YIELD_VALUE+LOAD_CONST 0 序列）。单 yield from、yield from 调用形、嵌套 gen、async gen 纯 yield 均 MATCH——**GET_YIELD_FROM 协议块夹层的用户 YIELD 序列无认领窗**。
- **机制假设**：yield from 编译为 SEND/YIELD 协议循环，两个协议块之间的普通 `yield 0`（YIELD_VALUE 独立块）被第二协议块的块收集吞并（协议尾判定把夹层块划入协议域）。
- **复现组**：r6_15.g_mixed（1 单元）。

### 归属总表

| 编号 | 归属 | 证据 |
|---|---|---|
| B29/B30/B31/B33/B34/B35 | 既有缺口（本轮新暴露） | tracked 树零改动 + §2 四支 Round 5 残留零漂移 + round5 归档后无 core commit |
| B32 | 既有缺口（B27 同族扩展面） | 同上 + r5 REVIEW2 §2 B27「嵌套 try 包 return 普通值即杀」登记在案，本轮证实 with 宿主/finally×with 叠加同杀 |

---

## §6 修复交接单（按优先级排序）

| 优先级 | 破口 | 机制一句话 | 最小验收组（转 MATCH 判据 = pyc_verify single success） | 回归哨兵清单 |
|---|---|---|---|---|
| **P0** | **B29** | async with 体装配 :30544 闸门 + SEND/YIELD LoopRegion 识别（:30549-30559）在线性体/多管理器布局下失效：体缩进丢失（文件级 IndentationError）/降级裸 Expr/`await None(None,None)`+`if True: pass` 幻影漏出（`__aexit__` 协议未整体消费） | r6_05（compile_error → 6/6）、n6_01（→ 8/8）、r6_12（3/6 → 6/6） | r6_05/r6_06/r6_08/r6_12 各自 MATCH 单元（aw_continue、af_break_continue 等）、r6_01/r6_03 同步 with 面、round5 r5_10 13/13、site-packages 五哨兵（152/153、65/65、84/92、118/128、41/43）不变差 |
| **P0** | **B30** | 语句级 async for 无 END_ASYNC_FOR 协议块消费器（推导式侧 r5 B23 `_find_async_clause_heads` comprehension_generator.py:1192 已有同构判据未推广至语句级）：出口/else 块并入体首、`return` 注入短路真体；async gen 内注入 return 触发 SyntaxError 文件级灭杀 | r6_14（2/7 → 7/7）、r6_07（compile_error → 6/6）、r6_06（1/5 → 5/5） | r6_14.af_break_continue/r6_12.aw_continue/n6_01.c_asyncfor 单累加器面、r6_08 其余 MATCH 单元 |
| **P0** | **B31** | Await 节点（ast_generator_v2.py:1165）仅 :1188/:1202/:2976 等栈顶特判认领；穿越 BINARY_OP/SUBSCR/COMPARE/BUILD_MAP/BUILD_LIST/CALL 操作数栈即降级裸 Expr、值被常量/None 顶替 | r6_13（3/8 → 8/8）、r6_08 ad_await_dict/ad_await_list/ad_await_arg 转 MATCH | r6_13.ad_await_chain/ad_await_while（RHS/语句位幸存面）、r6_07.ad_await_chain、r5_10 13/13（await-in-comp 既有面）、r5_02 genexp 12/12 |
| **P1** | **B32** | return 值穿越 WITH_EXCEPT_START 清理段布局下无 return 认领器（B24 `_find_returns_pending_value_successor` 仅推导式路径）：值消费为 Expr、return 剥除；B27 同族 with/finally 宿主扩展 | r6_02（6/7 → 7/7）、r6_03（6/7 → 7/7）、r6_11（4/6 → 6/6） | r5_09 12/12、rv5_24 8/9（B27 基线不回退）、r6_04 10/11、rv5_26_diag 4/6 |
| **P1** | **B33** | withitem target 仅认首条 STORE_* 单名（region_ast_generator.py:30589/:30624）：UNPACK_SEQUENCE/UNPACK_EX 序列目标蒸发或幻影 `= None` 注入；修复应复用 comprehension_generator.py:1658 `_parse_target_store_sequence` 结构判据 | r6_01（7/8 → 8/8）、r6_09（6/8 → 8/8） | r6_01.w_tuple_unpack（扁平 as MATCH 面）、r5_06 13/13、r5_04 13/13（B20/B21 既有面不回退） |
| **P2** | **B34** | for-else 体（return 形）被空体循环识别吞并、以 `while False: pass` 重放 | r6_10（3/6 → 6/6） | r6_10 其余 MATCH 单元、round3 for-else 面读数（r3_34 1/2 基线） |
| **P2** | **B35** | 双 yield from 协议块夹层的用户 YIELD 序列无认领窗 | r6_15（7/8 → 8/8） | r6_15 其余 7 MATCH 单元、round5 async gen 面 |
| P3 | Round 5 残留 B26/B27/B28 + B24 handler 残留 + B20 Pattern B 边界 | 见 round5 REVIEW2 §6 / FIX.md 未落地表 | 读数不得低于 §2 登记值（8/10、8/9、11/12、4/6） | §2 四支读数即回归基线 |

**修复边界提醒（算法合规）**：全部修复限于区域归约算法同层结构事实判据（识别/归约/生成/发射），禁止按函数名/文件名白名单；B29/B30 同根（async 协议块的整体消费），判据应以「GET_AWAITABLE/SEND/YIELD_VALUE/RESUME/END_ASYNC_FOR 协议块边界」结构事实统一解决，B30 应推广而非复制 comprehension_generator 侧既有 `_find_async_clause_heads`；B33 必须复用/共享 `_parse_target_store_sequence` 而非另写单形补丁；B31 判据须覆盖 return/binop/subscript/compare/dict/list/call-arg 全位形（位形嵌套无感）；docstring 三要素 + C1/C2/C3 条款同步。

**wiki 台账修订建议**：`wiki/concepts/decompile-invariant-completeness.md` :146/:155/:180（With/AsyncWith/withitem）与 :187（async 五件套）的「完备」降格为「浅层封闭：同步 with 线性体（含控制流/组合/MATCH）+ 扁平 as 单名/二元元组 + async 单累加器 async for + await 赋值 RHS/语句位」，并登记 B29–B35 七破口锚点（含 3 文件级 compile_error 灭杀签名）。
