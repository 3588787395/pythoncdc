# Round 8 评审报告（评审工程师 · 对抗攻击批次）

- 评审人：评审工程师（Round 8，任务 8.1，独立攻击，零容忍）
- 日期：2026-10-03
- 攻击对象：台账已判「无感完备」的**简单语句结构形态（表 A 扫尾）**——Return 位形态 × Pass/Delete × Assign 族（含 augassign 全算子）× Assert × Raise × 深层宿主组合 × 与 Round 7 表达式面交叉——实测「深层与浅层产物结构一致」声明
- 树状态：HEAD = `6a42146d`（round8 启动快照）；`git diff c0ab03c1 -- core/ parsers/ scripts/ pycdc.py` = **空**（放行态零在途变更，全部 MISMATCH 产生于已放行代码，无在途修复可归因）
- 唯一判据：`scripts/pyc_verify.py`（pylingual compare_pyc，Python 3.11.7）；全部 r8_*/n8_* OK.py 仅经 `pycdc.py -o` 再生成，零手改；未修改 core/、parsers/、scripts/、pycdc.py、spec.md/tasks.md 及既有 REVIEW/FIX/VERIFICATION；全部命令 ≤300 s（single 逐文件循环 13.3 s、r8 batch 2.7 s、残留 batch 6.0 s）
- 复现盘面：`test_repros/round8/`（r8_01–r8_11 + n8_01–n8_02，源码 + pyc + OK 产物）；报告：`rounds/round8/r8_all.json`（本目录 = `.trae/specs/harden-completed-forms-10rounds/rounds/round8/`）、`rounds/round8/r8_residual.json`

## 终判：**打回**（攻击面发现即登记，不做修复）

负对照 9/9 MATCH、Return 位形态（21/21）、Delete 基本面（10/10）、Raise 面（9/9）浅层与深层均成立；但 **Pass×try 宿主 / 链式赋值 / assert×交叉宿主 / 深层宿主组合面 17/109 单元 MISMATCH（7/11 文件 failure）**，其中 14 单元构成 9 个新破口族（B54–B62，含 4 处语句蒸发/幻影语句级结构破坏）、3 单元为 Round 7 已登记破口（B48/B46）读数对照实证。Round 7 残留复验 17 文件 36 失败单元与登记面逐位持平（零回归）。新破口 **B54–B62 九族**（§5）交修复工程师。

---

## §1 攻击面读数总表

探针源码 `test_repros/round8/r8_*.py`（`ast.parse` 预检 + `py_compile.compile` 全部通过，pyc 自 `__pycache__` 复制）；OK 产物 `pycdc.py -o` 生成；读数 = `pyc_verify.py single` 实测（status + units），批量对账 = `r8_all.json`（13 文件 118 单元，与逐文件 single 读数逐位一致）。

| 探针 | 攻击面 | 单元 | MATCH | 判定 | 机制归因（OK.py ↔ 源码 diff 实证） |
|---|---|---|---|---|---|
| r8_01_return_positions | Return 位形态：多分支/嵌套 if/循环早退/try-except-finally/finally 覆写/生成器 return 值/`return a, b`/`return a, *xs`/lambda 隐式 return | 11 | 11 | MATCH | 多 return 分支、嵌套 return、循环内 return、try/except/finally 各段 return、finally 覆写、生成器 `return "done"`、tuple/star 解包 return、lambda 全部保真 |
| r8_02_return_deep_hosts | Return 深层宿主：while-break/try-else/with 体/match case/async await/lambda 三元/≥3 层嵌套/生成器循环 | 10 | 10 | MATCH | return 深层宿主面全绿（try-else-finally 四段全 return 亦保真） |
| r8_03_pass_hosts | Pass 各宿主位：if 臂/循环体/函数体/类体/except 段/while-else/try-finally/match case | 9 | 7 | **MISMATCH** | r8_pass_except：尾随隐式 `return None` 被并入 try 体（**幻影 return**，B55）；r8_pass_try_finally：try/finally 全空段后尾随 `return 1` **整句蒸发**（B55）。r8_pass_while_else 丢空 else 但字节码同构 → Equal（不计 MISMATCH） |
| r8_04_delete_forms | del：局部/下标/切片/属性/多目标/元组目标/del 后续引用/循环内 del/嵌套宿主 del | 10 | 10 | MATCH | del 全形态保真（含 `del (a, b)`、循环内 `del xs[i]`、嵌套 if+for 宿主） |
| r8_05_assign_multi | Assign 族：链式 `a=b=c`/多目标/swap/星号解包头-中-尾/嵌套解包/属性/下标/切片/链式下标 | 11 | 9 | **MISMATCH** | r8_assign_chain：`a=b=c=5` 后**幻影裸 Expr `a + b + c`** 插入（B54）；r8_assign_chain_subscript：`d1['k']=d2['k']=v` 后尾随 `return d1, d2` **蒸发为裸 `(d1, d2)`**（B54）。swap/星号/嵌套解包/切片/属性全 MATCH |
| r8_06_augassign_ops | augassign 全算子（+= -= *= /= //= %= **= &= |= ^= >>= <<= @=）× RHS（常量/调用/属性链/下标链/三元） | 10 | 9 | **MISMATCH** | r8_aug_chain_rhs：`x *= a if a > b else b` → `x = x + (...)`（**B48 同签名：操作符丢失降级**，`*=` 误发射为 `+`）。其余 8 算子 × 各 RHS 形态全 MATCH |
| r8_07_assert_forms | Assert：裸/带 msg/内调用/比较链/BoolOp/循环内/`assert False`/嵌套函数内/三元交叉 | 11 | 10 | **MISMATCH** | r8_assert_nested_func：`return inner(x) + (y or 0)` **整句蒸发**，泄漏裸 Expr `y or 0`（B62）。`assert False` 尾随死代码被编译器消除 → Equal；三元 assert（带 msg）降级 if-form 但字节码同构 → Equal |
| r8_08_raise_forms | Raise：裸 reraise/实例/类/`from`/调用实参/except 链内新异常/深层宿主/f-string msg | 9 | 9 | MATCH | raise 全形态保真（含 `raise ... from exc`、f-string、except 链内二段 raise、for 宿主） |
| r8_09_deep_host_combo | 深层宿主组合：for-else+del+break+raise/try-finally return/while 内链式下标赋值/with 体 assert/match 三臂 del·swap·raise/async for raise/推导式+assert | 10 | 6 | **MISMATCH** | r8_dh_for_else_del：**break 蒸发 + else 体 raise 线性外提 + `return xs` 误入循环体**（B61）；r8_dh_while_assign_chain：链式下标赋值**拆链 + 第二目标 None 回填**（B54）；r8_dh_with_assert：with 体首赋值 `data = fh.read()` **蒸发**（B59）；r8_dh_match_multi：mapping `**rest` 捕获重建出**幻影解包 `(rest,) = {}`**（B60）。async/推导式/assert 组合 MATCH |
| r8_10_expr_cross_stmt | 与 Round 7 表达式面交叉：三元入 del 下标/assert 条件/return 元组/augassign（B48）/链式赋值/for 可迭代/raise 异常类/with 项/lambda/嵌套三元 | 12 | 6 | **MISMATCH** | r8_x_assert_ternary：无消息 assert（三元条件）**降级 `if not ...: raise AssertionError`**（B56）；r8_x_augassign_ternary：`x += aT` → `x = x + (aT)`（**B48 已登记读数对照**）；r8_x_assign_ternary_chain：链式下标 × 三元**拆链 None 回填**（B54）；r8_x_for_iter_ternary：for 可迭代三元**吞前导 `total = 0`**（B57）；r8_x_raise_ternary_class：raise 异常类三元**整句蒸发为 pass**（B58）；r8_x_ret_nested_ternary：臂含三元的外层三元**提升 if/else 双 return**（**B46 已登记读数对照**，双臂保持）。del 下标三元/return 元组三元/with 三元/lambda 三元 MATCH |
| r8_11_deep_host_combo2 | 深层宿主二批：while-else raise/try 四段全量/循环内嵌套 try+del/with 双管理器/match guard+assert | 6 | 5 | **MISMATCH** | r8_dh2_match_guard：match guard 宿主 assert+return **降级 if/else 分裂且 return 错位进 else 臂**（B56）。while-else raise/try 四段/嵌套 try del/with 双管理器全 MATCH |
| **攻击面合计** | 11 文件 | **109** | **92** | **17 MISMATCH / 7 文件** | |
| n8_01–n8_02（负对照） | 最简 return/单赋值 + 最简 pass/assert/raise/del | 9 | 9 | MATCH（§2） | |
| **总计** | 13 文件 | **118** | **101** | 85.59%；success 6 / failure 7 | |

分形态读数：Return 位形态（r8_01–02）21/21；Pass/Delete（r8_03–04）17/19；Assign 族（r8_05–06）18/21；Assert（r8_07）10/11；Raise（r8_08）9/9；深层宿主与交叉面（r8_09–11）17/28。每形态复现数：Return 17 函数、Pass/Delete 17（7 函数+1 类+9 函数）、Assign 19、Assert 9、Raise 8、深层宿主/交叉 22——全部 ≥8，深层宿主穿插于全部探针。表 A 五族浅层（负对照）与 Return/Delete/Raise 深层均成立，**Assign 链式重建、try 装配吞尾、assert 原生形态、深层宿主语句归属四维为真实缺口**。

## §2 负对照结果

| 负对照 | 形态 | 单元 | MATCH |
|---|---|---|---|
| n8_01_return_const | 最简 return 常量/return 名字/单赋值 | 4 | **4/4** |
| n8_02_simple_stmts | 最简 pass/无消息 assert/裸 raise 类/单 del | 5 | **5/5** |

两负对照全 MATCH：判定面对表 A 最简形态工作正常，**MISMATCH 为组合/宿主/重建维真实缺口**（非判据系统性失效），亦反证失败探针的最小归因成立。

## §3 Round 7 残留复验表（登记读数不变差）

方法：17 支残留 pyc（round7 r7 面 10 支 + round6 rv6 面 5 支 + rv7 变体 2 支）经当前核批量验证 → `r8_residual.json`；对照 Round 7 REVIEW2 §3 登记面（r7_01 8/9、r7_04 6/7、r7_05 15/16、r7_06 7/10、r7_07 4/7、r7_08 4/8、r7_10 7/8、r7_11 6/7、r7_12 5/8、r7_14 5/9、rv6_01 3/5、rv6_02 2/4、rv6_04 1/4、rv6_05 3/4、rv6_06 1/4、rv7_02 2/4、rv7_04 2/3）。

| 探针 | 登记面 | 本轮实测 | 失败单元名单 | 破口归属 | 变差判定 |
|---|---|---|---|---|---|
| r7_01_ternary_args_index | 8/9 | **8/9** | t_arg_multi_mixed | B42 残留① | 持平 |
| r7_04_ternary_binop_compare | 6/7 | **6/7** | t_compare_lhs_only | B42 残留② | 持平 |
| r7_05_ternary_comprehension | 15/16 | **15/16** | t_listcomp_ternary_filter.<listcomp> | B42 残留③ | 持平 |
| r7_06_ternary_lambda_await | 7/10 | **7/10** | t_await_ternary_branches / t_await_assign_ternary / t_await_deep_ternary | B47 | 持平 |
| r7_07_ternary_nest | 4/7 | **4/7** | t_nest_left_assoc / t_nest_in_condition / t_nest_mixed_binop | B46 | 持平 |
| r7_08_ternary_deep_host | 4/8 | **4/8** | t_host_while_body / t_host_for_else / t_host_try_sections / t_host_match_case | B48 / B49 / B50 / B46 | 持平 |
| r7_10_chain_compare_calls | 7/8 | **7/8** | c_chain_and_combo | B43 | 持平 |
| r7_11_boolop_mixed | 6/7 | **6/7** | b_and_or_repeat | B44 | 持平 |
| r7_12_boolop_nest | 5/8 | **5/8** | b_nest_three_layers / b_nest_deep_right / b_ternary_lhs_and | B44 / B44 / B46 | 持平 |
| r7_14_boolop_deep_host | 5/9 | **5/9** | h_listcomp_filter_composite + .<listcomp> / h_if_ternary_chain_composite / h_return_composite | B43 / B51 / B46 | 持平 |
| rv6_01_asyncwith_threestate | 3/5 | **3/5** | aw_break_in_try_for / aw_continue_in_try_for | B37 | 持平 |
| rv6_02_outer_handler_boundary | 2/4 | **2/4** | outer_raise_catch / nested_with_else_loop | B38 | 持平 |
| rv6_04_finally_deferred_double | 1/4 | **1/4** | try_fin_with_nested / double_fin_overwrite / try_fin_fin_body_with | B39 | 持平 |
| rv6_05_yieldfrom_mixed_else | 3/4 | **3/4** | gen_for_else_mixed | B40 | 持平 |
| rv6_06_withitem_deep_async | 1/4 | **1/4** | deep_tuple_star / star_mid_async / nested_star_tuple | B41 | 持平 |
| rv7_02_compare_chain_ternary | 2/4 | **2/4** | chain_two_ternary / chain_three_ternary | B52 | 持平 |
| rv7_04_dict3_ternary | 2/3 | **2/3** | dict3_nested_value | B53 | 持平 |

**结论：17/17 文件逐文件逐单元与登记面持平（81/117），36 个失败单元名单与 B42 残留×3 + B43/B44/B46–B51 + B52/B53 逐一对应，零回归、零漂移。**（B45 已封闭单元 h_while_composite / b_nest_deep_mixed 保持 MATCH，B42 已封闭 6 单元保持 MATCH。）

## §4 合规审计结果（在途变更审计）

| 项 | 判定 | 实测证据 |
|---|---|---|
| BOM（G0 红线） | **通过** | `head -c 3 core/cfg/region_ast_generator.py \| xxd` = `efbb bf` |
| 插桩残留（_R23N20_DEBUG/R23N21_DEBUG/_patch_dbg/_probe_r） | **通过** | `grep -rn "_R23N20_DEBUG\|R23N21_DEBUG\|_patch_dbg\|_probe_r" core/ \| wc -l` = **0** |
| 在途变更面（放行态零在途） | **通过** | `git diff c0ab03c1 -- core/ parsers/ scripts/ pycdc.py` = **空**（HEAD = `6a42146d` 仅含 round8 启动快照：`.trae/.../rounds/round8/verify_driver.py` + tasks.md，无 core 触碰）；无从触发四红线（名字白名单 / start_offset 魔数 / 跨层回溯 / 新 self 跨方法状态） |
| 新增自建产物 | 通过 | 本轮仅新增 `test_repros/round8/`（13 探针）+ `rounds/round8/`（本报告 + 2 json）；`git status` 无对已跟踪文件的修改 |

## §5 新破口登记（B54 起；编号续接 B53）

**归属总表**：全部 MISMATCH 产生于放行态代码（`git diff c0ab03c1 -- core/ parsers/ scripts/ pycdc.py` = 空）——14 单元为既有缺口（结构/宿主维变体新暴露），3 单元为 Round 7 已登记破口（B48/B46）交叉对照实证，非修复引入。

### B54 — 链式赋值重建崩坏族（值流断裂 / 幻影 Expr / 尾随 return 蒸发）（P1）
- **锚点（建议）**：链式赋值（`value; COPY 1; STORE_*; ...` 多重 STORE 链）未被结构化重建——`region_ast_generator.py:2818-2850` walrus `COPY 1; STORE_*` 前缀检测面（结构同形：链式赋值前缀与 walrus 前缀仅差后续 STORE 段）与 `:979` 通用语句发射器 COPY argval==1 处理面；识别侧语句终结切分。
- **机制**：多目标链（Name 链 / 下标目标链）被按单赋值逐段消费——(a) Name 链后尾随 return 的表达式被**泄漏为幻影裸 Expr**（`a=b=c=5; return a+b+c` → 多出 `a + b + c` 语句）；(b) 下标目标链后**尾随 return 蒸发为裸元组**（`d1['k']=d2['k']=v; return d1,d2` → `(d1, d2)`）；(c) 下标目标链**拆链 + 第二目标值 None 回填**（`out[i]=out['last']=xs[i]` → `out[i]=xs[i]` + `out['last']=None`，含三元 RHS 同签名）。
- **最小复现**：`r8_05 r8_assign_chain / r8_assign_chain_subscript`、`r8_09 r8_dh_while_assign_chain`、`r8_10 r8_x_assign_ternary_chain`。共 4 单元。
- **回归哨兵**：r8_05 其余 9 MATCH 单元（swap/星号/嵌套解包/切片/属性/多目标）+ n8_01 n8_single_assign。

### B55 — try/finally 装配吞尾族（幻影 return / 尾随 return 蒸发）（P1）
- **锚点（建议）**：`_generate_try_body`（region_ast_generator.py:26215）/`_generate_try`（:27900）体装配 + try 区域与后续语句的块归属判据（B50 同锚面，无三元纯结构形态）。
- **机制**：(a) try 体含 return + except 段为 pass 时，函数尾随隐式 `return None` 被并入 try 体（**幻影不可达 return**，字节码形态改变）；(b) try/finally 全空段（pass/pass）后**尾随 `return 1` 整句蒸发**（try 区域吞并后续语句块归属）。
- **最小复现**：`r8_03 r8_pass_except / r8_pass_try_finally`。共 2 单元。
- **回归哨兵**：r8_01 r8_ret_try_except / r8_ret_finally_overwrite、r8_02 r8_ret_try_else、r8_11 r8_dh2_try_full_sections、r8_03 其余 7 MATCH 单元（B45/B50 已封闭面禁变差）。

### B56 — assert 原生形态降级族（LOAD_ASSERTION_ERROR 丢失 / return 错位）（P2）
- **锚点（建议）**：`_generate_assert`（region_ast_generator.py:3541）+ `_collect_assert_prefix_stmts`（:477）前缀切分与三元区域/match-case 体归属竞争。
- **机制**：assert 原生字节码形态（LOAD_ASSERTION_ERROR + RAISE_VARARGS）未重建、走通用 if-not 路径——(a) 条件位含三元时降级 `if not cond: raise AssertionError`（LOAD_GLOBAL AssertionError ≠ LOAD_ASSERTION_ERROR，字节码不同）；(b) match guard 宿主下 `assert v<1000, msg; return v*2` 降级 if/else 分裂且 **return 错位进 else 臂**（控制流改变）。带 msg 且字节码同构的形态（r8_assert_ternary_cross）Equal 不计。
- **最小复现**：`r8_10 r8_x_assert_ternary`、`r8_11 r8_dh2_match_guard`。共 2 单元。
- **回归哨兵**：r8_07 其余 10 MATCH 单元（含 r8_assert_ternary_cross / r8_assert_msg / r8_assert_chain）、r8_10 r8_x_del_ternary。

### B57 — for 可迭代位三元吞前导语句（P1）
- **锚点（建议）**：`_loop_generate_for`（region_ast_generator.py:4710）可迭代表达式装配 × `_identify_ternary_regions` 区域抢占边界。
- **机制**：`for v in (xs if t else ys):` 可迭代位三元区域归约把前导初始化语句 `total = 0` 一并吞并——初始化蒸发（NameError 级语义破坏）。
- **最小复现**：`r8_10 r8_x_for_iter_ternary`。共 1 单元。
- **回归哨兵**：r8_02 r8_ret_gen_deep、r8_09 r8_dh_async_raise（for 宿主面 MATCH 单元）。

### B58 — raise 异常类三元整句蒸发（P1）
- **锚点（建议）**：raise 重建（RAISE_VARARGS 边界反扫，region_ast_generator.py:3780-3785 面附近）× 三元区域抢占（异常类实参位三元 + CALL 后缀）。
- **机制**：`raise (ValueError if x > 0 else TypeError)("...")` 的异常类位三元区域归约失败后块归属悬空，**整条 raise 语句蒸发为 pass**（函数体退化为隐式 return None）。
- **最小复现**：`r8_10 r8_x_raise_ternary_class`。共 1 单元。
- **回归哨兵**：r8_08 全部 9 MATCH 单元（raise 面禁变差）、r8_09 r8_dh_for_else_del 修复后的 raise 面。

### B59 — with 体首赋值蒸发（P2）
- **锚点（建议）**：`_generate_with`（region_ast_generator.py:31620）体装配与 withitem 消费面（B29–B35/B41 已审面下游）——体首赋值（上下文变量方法调用 RHS）块归属丢失。
- **机制**：`with open(p) as fh: data = fh.read(); assert data, msg` → with 体首赋值 `data = fh.read()` 蒸发、仅剩 assert（**引用未定义名**，产物为破损代码）。
- **最小复现**：`r8_09 r8_dh_with_assert`。共 1 单元。
- **回归哨兵**：r8_02 r8_ret_with、r8_10 r8_x_with_ternary、r8_11 r8_dh2_with_multi（with 面 MATCH 单元）。

### B60 — match mapping `**rest` 捕获幻影解包（P2）
- **锚点（建议）**：MatchMapping 构建（pattern_parser.py:2277/:2408）双星 rest 捕获 → 目标绑定 AST 映射；`_generate_match`（region_ast_generator.py:33183）case 体装配。
- **机制**：`case {"op": op, **rest}:` 双星捕获重建出**幻影解包语句 `(rest,) = {}`**（运行时必炸：dict 不可单目标解包）；其余体语句与返回保真。
- **最小复现**：`r8_09 r8_dh_match_multi`。共 1 单元。
- **回归哨兵**：r8_02 r8_ret_match、r8_11 r8_dh2_match_guard 的 case 面、r8_09 其余 MATCH 单元。

### B61 — for-else else 体线性外提 + break 蒸发（无三元形态）（P2）
- **锚点（建议）**：`_loop_generate_for`（region_ast_generator.py:4710）else 装配（B49/B35 拆分判据面）+ break 证据链（B10-R 复审面 :4573-4602）。
- **机制**：else 体为 raise 时 else 子句蒸发、raise 线性外提为循环后无条件语句（**else 语义破坏**），且循环体 if 臂内 `break` 随之蒸发、`return xs` 误入循环体——B49 登记面（else 体含三元增强赋值）的无三元纯结构变体。
- **最小复现**：`r8_09 r8_dh_for_else_del`。共 1 单元。
- **回归哨兵**：r8_01 r8_ret_in_loop（for-else return 面）、r8_03 r8_pass_loop_body / r8_pass_while_else、r8_11 r8_dh2_while_else_raise（B49 已封闭哨兵 t_host_for_else 禁变差）。

### B62 — return(call+BoolOp) 尾语句蒸发 → 裸 Expr 泄漏（P2）
- **锚点（建议）**：`_generate_return_ast`（region_ast_generator.py:55327）+ 语句终结切分（H13 trailing 语句发射面 :41641-41686 下游）——return 表达式含 CALL + BoolOp 组合时的切分丢失 RETURN 框架。
- **机制**：嵌套 def 宿主后 `return inner(x) + (y or 0)` **整句蒸发**、BoolOp 子树泄漏为裸 Expr `y or 0`（隐式 return None，返回值丢失）。
- **最小复现**：`r8_07 r8_assert_nested_func`。共 1 单元。
- **回归哨兵**：r8_01 r8_ret_tuple / r8_ret_star、r8_02 r8_ret_lambda_ternary、r8_07 其余 10 MATCH 单元。

### 既有破口读数对照（本轮交叉实证，非新登记）

| 破口 | 本轮对照单元 | 实测 | 与登记签名对照 |
|---|---|---|---|
| B48（augassign × 三元 RHS 操作符丢失） | r8_06 r8_aug_chain_rhs（`*=` → `+` 误发射）、r8_10 r8_x_augassign_ternary（`+=` → `=` 降级） | 2 单元 MISMATCH | 与 r7_03 t_augassign_mul_ternary / t_augassign_ternary 同签名，机制一致（TernaryRegion Assign 重建固定 `x = x + (t)` 模板） |
| B46（三元提升 if/else 语句） | r8_10 r8_x_ret_nested_ternary（臂含三元外层三元 → if/else 双 return，双臂保持） | 1 单元 MISMATCH | 与 r7_07 t_nest_left_assoc 同机制（识别面失败 → IfRegion 通用路径接管），本轮形态双臂无丢失 |

## §6 交接单（按优先级排序，供修复工程师认领）

| 序 | 项 | 优先级 | 单元 | 类型 | 修复要求（判据只允许同层结构事实） | 自测哨兵 |
|---|---|---|---|---|---|---|
| 1 | **B54** 链式赋值重建崩坏族 | P1 | 4 | 算法修复 | `COPY 1` 多重 STORE 链识别为多目标赋值结构（与 walrus 前缀按「后续 STORE 段存在性」互斥判定）；链值流完整透传至每一目标 | r8_05 9 MATCH 单元 + n8_01 4/4 保持 |
| 2 | **B55** try/finally 吞尾族 | P1 | 2 | 算法修复 | try 体装配后续语句归属按块末 RETURN/FALLTHROUGH 结构事实切分；全空段不吞尾、不补幻影 return | r8_01/r8_02/r8_11 try 面 MATCH 单元保持 |
| 3 | **B57** for 可迭代三元吞前导语句 | P1 | 1 | 算法修复 | 三元区域抢占不得越出可迭代表达式块；前导语句按块归属保留 | r8_10 其余 MATCH 单元保持 |
| 4 | **B58** raise 异常类三元整句蒸发 | P1 | 1 | 算法修复 | raise 重建与三元区域块归属竞争消解；归约失败禁止静默 pass | r8_08 9/9 保持 |
| 5 | **B56** assert 原生形态降级族 | P2 | 2 | 算法修复 | assert 装配触达 LOAD_ASSERTION_ERROR 形态（条件位三元/match guard 宿主下保持原生 RAISE 框架，return 不入 else 臂） | r8_07 10/11 面 + r8_assert_ternary_cross 保持 |
| 6 | **B59** with 体首赋值蒸发 | P2 | 1 | 算法修复 | with 体语句切分按块归属完整发射（禁止静默丢弃） | r8_02/r8_10/r8_11 with 面 MATCH 保持 |
| 7 | **B60** match mapping `**rest` 幻影解包 | P2 | 1 | 算法修复 | 双星 rest 捕获直接绑定目标名，禁止合成解包语句 | r8_02 r8_ret_match 保持 |
| 8 | **B61** for-else else 外提 + break 蒸发 | P2 | 1 | 算法修复 | else 装配按块归属重验（B49 判据面扩展至无三元形态）+ break 证据链保持 | r8_01/r8_03/r8_11 循环 else 面 MATCH 保持 |
| 9 | **B62** return(call+BoolOp) 尾语句蒸发 | P2 | 1 | 算法修复 | return 表达式切分保 RETURN 框架完整（H13 面下游语句终结判据复核） | r8_07 其余 10 MATCH 单元保持 |
| 10 | Round 7 残留（B42×3 / B43 / B44 / B46–B53） | 沿袭 | 36 | 算法修复 | 按 Round 7 REVIEW.md §6 交接单认领；登记读数本轮已复验持平（§3），修复后以 r8_residual.json 面禁变差 | r8_residual 81/117 各文件禁变差 |

**总回归哨兵清单（修复自测 = 全部保持 + 本轮 MISMATCH 转 MATCH）**：n8_01/n8_02 9/9；r8_01 11/11、r8_02 10/10、r8_04 10/10、r8_08 9/9 全 MATCH 面；部分 MATCH 面禁变差（r8_03 7/9、r8_05 9/11、r8_06 9/10、r7_08 4/8、r8_07 10/11、r8_09 6/10、r8_10 6/12、r8_11 5/6）；Round 7 残留 r8_residual.json 17 文件 81/117 逐位持平；round6 全量 16 文件 115/115；六哨兵 + option_account 35/35（主代理验证序覆盖）。

---

## 附：复现产物清单

- `test_repros/round8/r8_01_return_positions.{py,pyc,OK.py}` … `r8_11_deep_host_combo2.{py,pyc,OK.py}`（11 攻击文件）
- `test_repros/round8/n8_01_return_const.{py,pyc,OK.py}`、`n8_02_simple_stmts.{py,pyc,OK.py}`（2 负对照）
- `rounds/round8/r8_all.json`（13 文件 batch 报告）、`rounds/round8/r8_residual.json`（Round 7 残留 17 文件 batch 报告）
- 编译链：`ast.parse` 预检 → `py_compile.compile` → `__pycache__/*.cpython-311.pyc` 复制为 `*.pyc` → `pycdc.py -o *OK.py` → `pyc_verify.py single/batch`
- 评审过程零修改 core/、parsers/、scripts/、pycdc.py、spec.md/tasks.md；未手改任何既有 *OK.py；未触碰 REVIEW/FIX/VERIFICATION 历史文档
