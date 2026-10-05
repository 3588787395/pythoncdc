# Round 2 评审报告（Task 2.1）—— 表A 语句结构形态对抗

- 评审角色：对抗性独立审计（只读 core/ wiki/ scripts/ site-packages parsers/，零代码修改，零 git 提交）。
- 树状态：HEAD = `a3104674`（round1 归档提交）；`git status --porcelain` 全树零在途变更（含 core/ wiki/ site-packages/）。
- 工具链：`python -c "import py_compile; py_compile.compile(f, cfile, doraise=True, optimize=0)"`（3.11.7，magic 匹配）→ `python pycdc.py x.pyc -o xOK.py` → `python scripts/pyc_verify.py single x.pyc`；全部验证先以 HEAD 代码重生成 OK.py（RV2 方法学）。
- 证据落盘：`rounds/round2/`（r2_regress_index.json、r2_regress_replay.json、r2_probe_index.json、r2_probe_results.json、r2_fail_units.json、r2_regen_verify.py）+ `test_repros/round2/`（gen_probes.py + 42 探针 .py/.pyc/OK.py）。
- 目录注记：`test_repros/round2/` 为跨规范共用目录（旧规范 round2 的 r2_/rv2_/n2_ 文件在案）。本轮新探针以 `m*`/`c*`/`x*`/`nm*`/`nc*`/`nx*` 前缀隔离，零覆盖既有文件；该目录旧 .pyc 均为未跟踪产物（git ls-tree 0 个 .pyc），非回归面，无污染。

---

## §0 终判预备结论与两态口径

| 项 | 结论 |
|---|---|
| A. 合规审计 | **通过**：I.4 黑名单五项零新增（`git diff a3104674 -- core/` = 0 行）；BOM 双核心单头 ✓；round1 登记的 4 族存量遗留（ast_generator_v2 魔数×2 / structured_analyzer depth>3 / DBG_OR×18）**实测确认已全部清除** |
| B. 站桩回归 | **通过**：45 文件重放读数与基线逐位一致（修复面/负对照/存量失败面/probes_rvC/34 集抽验 6 文件），无任何变好变差 |
| C. 完备形态攻击 | **发现破口**：42 探针 189 单元 = 154/189（81.5%）；5 个独立负对照 + 9 个文件内浅层兄弟单元全 MATCH；**新登记 B84–B97 共 14 项**（含 2 项 COMPILE_ERROR 级）+ 6 组「同 Bn 存量」机理外推证据 + 3 单元探针退化伪差如实登记 |
| D. 正面结果 | TryStar/except\* 深度 3 外推全过（A7/C3）；match 作叶子 6 宿主全过（x06）；类体 with/装饰器/import/嵌套类/docstring/augassign×三元全过；模块级 def/class 交错与 try-finally-only 全过 |

**两态口径**：本轮评审态 = 「通过（流程合规 + 站桩零回退）∧ 破口发现（B84–B97 14 项进入修复阶段）」。轮门禁（每轮 ≥1 登记破口）**已满足**；round1 修复批次 A/B/C 无回退证据，不构成对既有结论的打回。III.5 残余名单与 B77–B83 实测持平（§2），B78/B81/B83/B56/B59-61/B49/B61 的机理在本轮获得**宿主外推证据**（原登记均为函数级，本轮证实其机理在模块根/类体/handler 宿主同域触发）。

---

## §1 合规审计表（红线 × 扫描 × 命中 × 判定）

| 红线 | 扫描方法 | 命中 | 判定 |
|---|---|---|---|
| 在途变更 | `git status --porcelain`（全树）+ `git diff a3104674 -- core/` | **0 行**（全树干净，HEAD 即工作树） | **PASS** |
| I.4-① 文件/函数名白名单 | grep `test_repros\|round[0-9]\|co_filename\|__name__ == '\|\.pyc'\|_OK\.py` in core/cfg/ | 9 命中：7 处注释文档性引用（round67_diag4/round14_join/round1 等）+ 2 处 `__main__` 工具入口 + 2 处 `type(x).__name__ == 'LoopRegion'`（region_analyzer.py:20330、region_ast_generator.py:6590，类型分发） | **新增 0**；存量构成与 round1 REVIEW §4 逐位相同（观察项移交 Round 6） |
| I.4-② start_offset 魔数 | grep `start_offset ==\|start_offset >\|start_offset <\|offset == \d{4,}` | 全部命中为 `start_offset == jump_target/argval` 结构派生比较（跳转目标 oparg，I.4 白名单合法用途）；**round1 登记的 ast_generator_v2:9050 `==62` 与 :14990 `==74` grep = 0 命中，确认已由批次 B 删除** | **新增 0 + 存量清除确认** PASS |
| I.4-③ 跨层 `entry in blocks` 反查 | grep `\.entry in .*\.blocks\|entry in self\.blocks` | 14 命中（与 round1 §4 计数一致，diff=0 未变）；抽样定性为 B4/C3 守卫落地与区域成员关系合法判据 | **新增 0** PASS |
| I.4-④ self 新增跨方法状态 | diff 为空（HEAD 树零变更）⇒ 无新增 | 0 | **PASS** |
| I.4-⑤ 条件性少发射/硬编码深度上限 | grep `if depth > \d+\|MAX_DEPTH\|max_depth = \d` in core/cfg/ = **0 命中**；**round1 登记的 structured_analyzer.py depth>3 确认已改结构判据** | 0 | **新增 0 + 存量清除确认** PASS |
| I.5 禁止前缀方法（新增） | grep `def _(fix_\|patch_\|fallback_\|hack_\|workaround_\|temp_\|merge_)\w+` | 仅存量 `_merge_block_is_then_exclusive`（region_ast_generator.py:19700）、`_merge_block_is_loop_back_edge`（:39849）——历史方法非本轮新增（I.5 限新增方法） | **新增 0** PASS |
| BOM 单头（IV.2） | 字节级：region_analyzer.py / region_ast_generator.py 首 3 字节 | 两文件均 = `efbbbf` 且全文 BOM 计数 = 1（无双头） | **PASS** |
| 插桩残留 | grep `breakpoint(\|import pdb\|pdb.set_trace` = 0；`DBG_[A-Z]\|临时调试` = **0 命中（round1 登记 DBG_OR×18 确认已删）**；`os.environ.get('PYCDC_DEBUG')` 门控调试 2 处（ast_generator_v2.py:23202/:23340，默认关闭）；存量无条件 print：ast_generator_v2.py 13 处（:2455/:2497 N14 警告 + :6747-6824 [调试] 块）、cfg_optimizer.py 8 处（独立分析工具） | **新增 0**；存量 print 属历史遗留（非本规范涉改六文件引入），登记为观察项移交 Round 8 清理位 | PASS（新增 0）+ 观察登记 |
| 命令时限 | 全部命令 ≤300s（重放批 45 文件 <300s 单片） | — | PASS |

**round1 存量遗留清账确认（§4 交接闭环）**：① ast_generator_v2.py 魔数 62 段 ✅ 已删；② ast_generator_v2.py `==74` no-op ✅ 已删；③ structured_analyzer.py depth>3 ✅ 已改单后继线性链判据；④ region_analyzer.py DBG_OR×18 ✅ 已删（round1 REVIEW §6.1「清理位」四项全部落地）。

---

## §2 站桩回归读数表（RV2 方法学：先 HEAD regen 再 verify）

### 2.1 round1 修复面（不得变差）

| 面 | 基线 | 本轮实测 | 判定 |
|---|---|---|---|
| r10_04 / r10_06 / r10_14 / r10_15 / r10_16 / r10_21 | 3/3、3/3、7/7、6/6、7/7、4/4 | 全 MATCH 逐位一致 | 持平 ✓ |
| rv10_31 / rv10_32 / rv10_33 | 13/13、8/8、6/6 | 全 MATCH | 持平 ✓ |
| r7_03 / r7_07 | 7/7、7/7 | 全 MATCH | 持平 ✓ |
| r7_08 | 7/8（失败单元 t_host_match_case = B77 存量） | 7/8，失败单元 `***<module>.t_host_match_case: Different control flow` | 持平 ✓ |
| rv8_01 / r8_06 | 7/7、10/10 | 全 MATCH | 持平 ✓ |
| rv8_02 | 6/7（存量单元） | 6/7，失败单元 `tryfin_then_more: Different bytecode`（B63 存量） | 持平 ✓ |

### 2.2 round1 负对照（必须保持 MATCH）

n6_01 8/8、n7_01 5/5、n7_02 5/5、n8_01 4/4、n8_02 5/5、n9_01 3/3、n9_02 4/4、n10_01..04 合计 9/9、rv9_03 4/4 —— **全 MATCH** ✓

### 2.3 存量失败面基线（不得变好也不得变差，失败单元逐一相同）

| 面 | 基线 | 本轮 | 失败单元 |
|---|---|---|---|
| v_b46_face | 1/4 | 1/4 | n_for_body_nest（B78）✓ |
| v_b71_face | 3/4 | 3/4 | v_nest_fin_continue（B79）✓ |
| v_b73_face | 2/3 | 2/3 | v_imp_cond_fin（B80）✓ |
| v_b74_face | 3/4 | 3/4 | n_true_guard（B81）✓ |
| v_b75_face | 1/3 | 1/3 | n_fin_noseg（B82）✓ |
| v_b50_face / v_b65_face / v_b76_face | 4/4、3/3、4/4 | 全 MATCH | — ✓ |
| probes_rvC rvC_v1/v3/v4 | MATCH | MATCH | — ✓ |
| probes_rvC rvC_v2 | FAIL（B83 存量） | 1/2 FAIL | `drain: Different control flow` ✓ |

### 2.4 34 小测试集抽验 6 文件

| 文件 | 基线 | 本轮 | 判定 |
|---|---|---|---|
| email_utils | 3/4 | 3/4（send_email Different control flow） | 持平 ✓ |
| cgroup_utils | 7/8 | 7/8（set_cgroup_config） | 持平 ✓ |
| executor | 9/10 | 9/10（Executor.check_before_trading） | 持平 ✓ |
| strategy_universe | 10/11 | 10/11（_on_clear_de_listed） | 持平 ✓ |
| trading_dates_mixin | 13/14 | 13/14（trading_dates_reload） | 持平 ✓ |
| realtime_event_source | 12/13 | 12/13（clock_worker） | 持平 ✓ |

**站桩总判**：45/45 文件读数与基线逐位一致，失败单元逐一相同，零回退零异常。

---

## §3 完备形态攻击结果表

探针生成：`test_repros/round2/gen_probes.py` 程序化批量生成 42 文件（≥10 深层复现/组，嵌套深度 ≥3；C2 判据 = 深层探针产物与浅层等价物产物结构一致，实测口径 = 深层 MATCH ∧ 浅层负对照 MATCH）。读数：`r2_probe_results.json` + `r2_fail_units.json`。

### 3.1 ★组① Module 专攻（覆盖矩阵 A1 空白，12 探针 + 2 负对照）

| 探针 | 深度/形态 | 单元 | 判定 | 结论 |
|---|---|---|---|---|
| m01 docstring 位 + 语句序 + del | 模块根：docstring/import/def/class/if-main 序 | 4/5 `<module>` Different bytecode | **B84**（`del _os` 蒸发） | 破口 |
| m02 顶层 if-main 深体 | if→for→while→try/except/finally 深 5 | 2/3 `<module>` Different control flow | **B87**（try 体蒸发 `while k: pass`） | 破口 |
| m03 模块级 if/elif 链深臂 | 臂内 for-else + while/try 深 4 | 0/1 | 同 B49/B61（for-else 折叠为 if/continue 重构）+ while 体错序 | 同 Bn 存量 |
| m04 模块级 try 双嵌套 | try→try→for→with→if→while 深 7 | 0/1 | 同 B78（if+while 融合 `if i and i`）+ 体蒸发 | 同 Bn 存量 |
| m05 模块级 match + 真 guard | match→for→match 深 3 | 0/1 | 同 B81（真 guard 丢弃）+ 幻影 continue（B74 族同形） | 同 Bn 存量 |
| m06 模块级 for/while-else | for-else + while-else + continue/break | 0/1 | 同 B49/B61（while-else 体被内联进循环体） | 同 Bn 存量 |
| m07 模块级多上下文 with | with 双上下文 + 深嵌套 with | 0/1 | **B86**（第二 withitem 丢弃 + 幻影 `if True: pass`） | 破口 |
| m08 模块级语句混合 | AnnAssign/链式赋值/del/genexp | 1/2 | **B84**（del 蒸发）+ **B85**（`_L = _M = [1,2]` 丢 `_M`）+ 附注（AnnAssign 分解疑失 SETUP_ANNOTATIONS，需隔离探针） | 破口 |
| m09 模块根深 7 交叉 | with→try→for→if→while→match | 0/1 | 同 B78（条件融合）+ case 臂语句蒸发（同 B59-61 族） | 同 Bn 存量 |
| m10 def/class 交错 + 类体 if | 模块根序 | 6/6 MATCH | **未破**（13 误解自查见 §3.4） | 完备维持 |
| m11 模块级 try-finally-only | try/finally + 尾随语句 | 1/1 MATCH | **未破** | 完备维持 |
| m12 模块级值位（表B 交叉） | 三元/BoolOp/比较/f-string/默认参数 | COMPILE_ERROR | **B89**（裸语句泄漏 `_F`/`_A < _B`）+ **B90**（f-string 渲染为集合字面量 → 产物不可编译） | 破口 |
| nm01/nm02 负对照 | 浅层等价形 | 3/3、1/1 MATCH | 浅层对而深层错 ⇒ C2 破坏确证 | 对照成立 |

**组①结论**：Module 根装配存在系统性破口——**模块级 del/链式赋值/多上下文 with/深层 try 体/值位表达式五族在模块宿主蒸发或错构（B84/B85/B86/B87/B89/B90）**；A1「零专攻」空白已补，模块级语句序与 docstring 位（m01 非 del 部分/m10/m11）本身成立。

### 3.2 ★组② ClassDef 体专攻（A15 组内空白，15 探针 + 2 负对照）

| 探针 | 形态 | 单元 | 判定 | 结论 |
|---|---|---|---|---|
| c01 类级赋值十形 | 链式/多目标/AnnAssign/f-string/lambda | 4/5 CAssign Different bytecode | **B85**（`D = E = {...}` 丢 `E`） | 破口 |
| c02 类级 if/else 深臂 | class→if→for→if→while→try 深 6 | 6/7 CIf.items | 同 B78（融合）+ **B88**（尾随 return 拉入 for 体） | 破口（新元） |
| c03 类级 for | class→for→if→while 深 4 | 3/4 CFor | 同 B78（`while _n and _n` 融合） | 同 Bn 存量 |
| c04 类级 try 三嵌套 | class→try→try（except/else/finally 全件） | 5/6 CTryNest | **B87**（内层 try-else 体 `OUT = 5` 蒸发） | 破口（新元） |
| c05 类级 with | class→with→for→try→if→with 深 6 | 5/5 MATCH | **未破** | 完备维持 |
| c06 类级 match + 真 guard | class→match→for→if→match 深 5 | COMPILE_ERROR | **B91**（guard 重构为 if/else + 类体幻影 `return None` → 'return' outside function） | 破口 |
| c07 方法间语句 | 类体 if/del/assert/import 夹 method | 5/6 CBetween.third | 同 B78（融合）；类体 del 归 B84、`assert True`→幻影空串字节等价（注记） | 同 Bn 存量 |
| c08 装饰器带参 | 类装饰器+方法装饰器+参数 | 8/8 MATCH | **未破**（★组⑥ decorator_with_args 附带覆盖） | 完备维持 |
| c09 类级 import + global | 类体 import/from-import + 方法 global | 6/6 MATCH | **未破** | 完备维持 |
| c10 三层嵌套类 | 每层类体赋值/for/if + 深方法 | 8/8 MATCH | **未破** | 完备维持 |
| c11 函数↔类交替 | 函数内类引用闭包参数 | 8/10 top_make.Top | **B92**（类体 `TV = x` LOAD_CLASSDEREF 读取闭包 → 赋值蒸发） | 破口 |
| c12 类体六宿主深交叉 | class→if→for→try→with→while 深 6 + 方法 match | 3/3 MATCH | **未破** | 完备维持 |
| c13 类级 del/assert/raise/pass/Expr | 类体 del + 深 loop 方法 | 1/3 CMisc | **B84**（`del TMP` 蒸发）+ **B88**（`return None` 蒸发） | 破口 |
| c14 类/方法 docstring 位 | docstring/非 docstring 常量语句/深体 | 7/7 MATCH | **未破**（非 docstring 裸常量语句保留正确） | 完备维持 |
| c15 类级 augassign×三元 RHS | `M *= 2 if N else 1`（B46 交叉） | 3/3 MATCH | **未破**——B46 三元机理**不在类体宿主复现** | 完备维持 |
| nc01/nc02 负对照 | 浅层类体 | 4/4、3/3 MATCH | 对照成立 | — |

**组②结论**：类体宿主十轮零探针的空白已补；**类体专属新破口 3 项（B85 链式赋值/B91 guard→幻影 return COMPILE_ERROR/B92 闭包读取蒸发）**，类体 del 蒸发归入 B84（与模块根同机理同族）；c05/c08/c09/c10/c12/c14/c15 七面未破。

### 3.3 表A 其余组交叉深度探针（10 探针 + 1 负对照）

| 探针 | 形态 | 单元 | 判定 | 结论 |
|---|---|---|---|---|
| x01 If 作叶 × 5 宿主 | func→宿主→if→宿主→if ≥3 | 4/7 | if_in_while = **B94**（NOP 残段假循环×2 + 体蒸发）；if_in_match = **B88**（return 吞入 `case _` 臂）+ 同 B78；if_in_try = 探针退化伪差（注记） | 破口 ×2 |
| x02 For 作叶 × 5 宿主 | 同构 | 5/7 | for_in_try = 同 **B83**（内层 for 镜像泄漏到 finally 后，**无 raise 触发变体**）；for_in_match = **B88**；其余 MATCH | 同 Bn + 破口 |
| x03 While 作叶 × 5 宿主 | 同构 | 6/7 | while_in_try = 探针退化伪差；其余 MATCH（含退化单元） | 伪差注记 |
| x04 Try 作叶 × 5 宿主 | 同构 | 4/7 | try_in_while = **B87**（try 体 `R = 1` 蒸发 + 幻影 continue）；try_in_with = **B87**（handler 臂 `R = 2` 蒸发）；try_in_if = 探针退化伪差 | 破口 |
| x05 With 作叶 × 5 宿主 | 同构 | 6/7 | with_in_match = **B93**（match 叶被幻影 `with _A() as a` 镜像替换） | 破口 |
| x06 Match 作叶 × 5 宿主 | 同构 | 7/7 MATCH | **未破**——match 作叶子在任何宿主均正确 | 完备维持 |
| x07 except\* 深 3（A7/C3 外推） | ts_shallow/for 宿主/with+fin 宿主 | 4/4 MATCH | **未破**——except\* 深度外推通过（该组原仅 R2 单轮浅覆盖） | 完备维持 |
| x08 语句叶 × 深宿主 | assert/raise/return/del/assign/import 叶 | 5/8 | assert_leaf = 同 B56（assert 降级）+ 同 B78；raise_leaf = **B87**（try/raise 整体搬出 for 体）；return_leaf = **B88**（return None 蒸发）；del/assign/import 叶 MATCH | 破口 + 同 Bn |
| x09 FunctionDef/Async 宿主 | def 深宿主 + async 五件套 | 7/10 | AHost.a1 = **B95**（await 语句在 for 体蒸发）；AHost.a2 = **B96**（async 推导式 → `await None(_AIT())` + 内层 `<listcomp>` code object 丢失）；def_in_if/def_in_try MATCH | 破口 ×2 |
| x10 ExceptHandler 深宿主 | handler 体宿主六形态 | 2/3 | h_basic = **B97**（except 臂内 break 蒸发）+ 同 B78（融合）+ 同 B59-61 族（match → if/else 体错位）；h_shallow MATCH | 破口 + 同 Bn |
| nx01 负对照 | 六宿主浅层等价 | 7/7 MATCH | 对照成立 | — |

### 3.4 II.7 十三条误解自查（对 §3 中「未破/完备维持」宣告）

1. **循环论证分母**：未犯——未以 RegionType 枚举或本轮探针面充当分母，128 分母仍为 ast 权威口径。
2. **有过就算**：未犯——「未破」判定基于宿主×深度双向探针（如 x06 五宿主 + x07 三形态 + c12 深 6 交叉），非单例通过。
3. **语料证据口径**：未犯——探针为构造形（非 site-packages 语料抽样），语料仅作站桩回归。
4. **无限分母**：未犯——本轮单元分母封闭（42 文件 189 单元，逐单元可复现）。
5. **节点词汇当完备**：未犯——match/except\* 的「未破」以字节码结构一致（C2 黑箱）为准，非以 AST 节点可产出为准。
6. **浅层测试当无感证明**：未犯——每个「未破」宣告均伴随 ≥3 层深层单元（nc/nm/nx 负对照仅证浅层形无伪差）。
7. **门禁读数当完备性**：未犯——§2 站桩读数仅用于回归判定，不用于完备宣告。
8. **顶层构造粗清单**：本轮 Module/ClassDef 专攻恰是对该误解的补救（A1/A15 此前零专攻）。
9. **识别率当完备性**：未犯——判定口径为 C2 产物一致，非识别命中率。
10. **维度互替**：未犯——本轮读数不反驳语法完备台账，亦不被字节等价门禁反驳。
11. **改工具不改方法**：未犯——零工具修改（pyc_verify/pycdc 零触碰）。
12. **错误检测标准**：本轮 except\* 探针产物经 3.11 标记核对路径验证（CHECK_EG_MATCH 族），未涉 3.12 PRELOAD_RERAISE。
13. **语料上限当能力上限**：未犯——破口登记均给锚点+机理，非语料外推。

---

## §4 新破口登记（B84–B97）

登记规则执行情况：命中与既有 Bn **同机理**者标「同 Bn 存量」不重复编号（B78/B81/B83/B56/B59-61/B49/B61 获外推证据，见 §4.2）；机理不同者新编号 B84–B97。

### 4.1 新编号破口（14 项）

| 编号 | 形态 | 最小复现 | 锚点 | 机制 | 违反条款 | 探针 |
|---|---|---|---|---|---|---|
| **B84** | 非函数宿主 `del NAME` 语句蒸发（DELETE_NAME 发射路径缺失） | 模块级/类体 `del X`（m01 `_os`、m08 `_L`、c13 `TMP`）；函数级 del 正常（r8_04 10/11、x08 delete_leaf MATCH） | code_generator.py:3094 `_generate_delete_node` + :207/:308 分发；模块根 region_ast_generator.py:1966 区段、类体 :32458 `_generate_class_body_from_code` | 模块/类体顺序语句装配不产出 Delete 节点，DELETE_NAME 块被静默丢弃（无「块集非空但发射为空」报错） | C2（宿主相关发射）+ I.4 ⑤ 同型风险 | m01/m08/c13 |
| **B85** | 非函数宿主链式/多目标赋值丢第二目标 | 模块级 `_L = _M = [1, 2]`、类体 `D = E = {...}` → 仅首目标发射；函数级正常（r8_05 11/11） | region_ast_generator.py:28 链式赋值 COPY 模式判据（`MIN_INSTRS_FOR_CHAIN_ASSIGN_PATTERN`）；code_generator.py:2697-2702 多目标路径 | COPY/GLOBAL 链式模式识别未应用于模块/类体宿主，次级 STORE 被丢弃 | C2 | m08/c01 |
| **B86** | 模块根多上下文 with 丢第二 withitem + 幻影 `if True: pass` | 模块级 `with _A() as a, _B() as b:` → 单 withitem；函数级多上下文 with 正常（R6/R9 面） | region_ast_generator.py:32772-32841（withitem 轮询装配）、:33438（withitem 解包链认领） | 模块根 with 区域仅认领首上下文，第二 SETUP_WITH 链落入幻影 if 尾 | C1/C2 | m07 |
| **B87** | 深宿主异常区域体/臂语句蒸发（try 体/handler 臂/try-else 臂/整体搬出） | ① if-main 内 `for→while→try/except/finally` 体蒸发（m02）；② while 宿主 try 体 `R = 1` 蒸发+幻影 continue（x04 try_in_while）；③ with 宿主 handler 臂 `R = 2` 蒸发（x04 try_in_with）；④ for 宿主 try/raise 整体搬出循环（x08 raise_leaf）；⑤ 类体嵌套 try 的 else 臂 `OUT = 5` 蒸发（c04） | region_ast_generator.py try 域装配区（W11-A/B50/B71 修复邻域 :28888-30199）、handler 臂收集区 | 深宿主下 try 子区域臂/体块认领后未发射且无报错（静默蒸发）；raise_leaf 为块重定位变体 | C1/C2 | m02/c04/x04×2/x08 |
| **B88** | 深循环/match 宿主尾随 return 归属错位（蒸发/拉入循环体/吞入 case 臂） | ① 方法内 for/while 深嵌套后 `return None` 蒸发（c13.boom、x08 return_leaf）；② `return ITEMS` 被拉入 for 体（c02 CIf.items）；③ 尾随 `return 5` 被吞入 `case _` 臂（x01 if_in_match、x02 for_in_match） | region_ast_generator.py 尾声内联区（:1748-1794 尾随 return 处理、[B55] 预标记）+ 循环/case 臂归属 | 尾随 return 块被循环/match 子区域误认领：发射位置错（拉入/吞入）或彻底丢弃 | C1/C2（B62 同族但机理不同：B62 为 RETURN_VALUE 前消费链，本组为块归属/发射位） | c02/c13/x01/x02/x08 |
| **B89** | 模块根值位裸语句泄漏 | 模块级 `W = 1 if _F else 2` 后泄漏裸 `_F` 语句；`_A < _B < _C` 前泄漏裸 `_A < _B`（m12） | region_ast_generator.py 模块根序列发射区（:17253 BoolOp 入口、:14527 Assign 包装注释） | 三元条件/比较 LHS 消费点在模块根被作为独立语句重复发射（镜像泄漏子型） | C1/C2 | m12 |
| **B90** | 模块根 f-string 转换+嵌套 format-spec 渲染为集合字面量 → **COMPILE_ERROR** | 模块级 `f'{W!r:>{len(str(1))}}'` → `Q = {W!r:f'>{len(str(1))}'}"`（{} 括号语义错乱，产物不可编译） | ast_converter.py:1379 `_convert_joined_str_full`、:1399 `_convert_formatted_value_full`（★组④ fstring_conversion 首个对抗证据） | FormattedValue(format_spec=JoinedStr) 嵌套结构在转换/发射层丢失 FormattedValue 包装，被退化为 dict/set 字面量 | T3 生成路径产物非法（II.3 破口）+ C2 | m12 |
| **B91** | 类体 match 真 guard → if/else 重构 + 类体幻影 `return None` → **COMPILE_ERROR** | 类体 `case {'k': [x, *rest]} if x:` → `if x: ... else: return None`（return 在类体非法）；函数级真 guard 为控制流 FAIL（B81 存量） | region_ast_generator.py guard 消费区（:1805-1900 `_leading_guard`/R76）+ match 装配区；类体 :32458 | 类体宿主下 guard 转换为 if/else 且 else 臂注入幻影 return（守卫封闭判据未覆盖类体宿主） | C3 + C2（B81 族类体变体，产物级更重） | c06 |
| **B92** | 类体闭包读取赋值蒸发（LOAD_CLASSDEREF） | 函数内 `class Top: TV = x`（x 为闭包参数）→ `TV = x` 整行蒸发；非闭包类体赋值正常（c10 MATCH） | region_analyzer.py:2266-2303（B72 cell/freevar 元数据判据区）；region_ast_generator.py:32458 | 类体代码对象 LOAD_CLASSDEREF 值位的 Assign 装配被丢弃（B72 判据未覆盖类体读取方向） | C1 | c11 |
| **B93** | match 叶子宿主被幻影 with 镜像替换 | `with _A() as a: match 1: case 1: with _A() as b: match 2: case 2: R=(a,b)` → 内层 `match 2: case 2:` 变为幻影 `with _A() as a:`（外层兄弟区域副本） | region_analyzer.py match 识别区（:12920 `_identify_match_regions`）+ 区域父子认领 | 深宿主下 match 子区域被同层 with 区域镜像替换（区域成员关系误认领） | C2（B83 镜像族同域、非 finalbody 泄漏路径） | x05 |
| **B94** | NOP 残段 while 循环边界误判 → 幻影假循环 + 体蒸发 | 折叠残段 `while 1: R = 1`（含跳转目标 NOP）→ 反编译为 `while False: pass ×2 + while True: 1`，`R = 1` 蒸发 | region_analyzer.py 假循环过滤/role 修正区（:5011-5054）、clamp 判定（:5104-5108） | 跳转目标 NOP 使循环头/回边判定错位，产出两个假循环幻影并丢失循环体 | C1 | x01 |
| **B95** | await 语句深宿主蒸发 | `async def a1: async with: if: for i: await self.a2(i)` → `await` 变 `pass`；函数级 await×三元为 B47 存量（表达式级） | code_generator.py:5413 `_generate_awaitable`；region_ast_generator.py:9663-9664（fall-through Await 认领） | for 体宿主下 await Expr 语句的语句性发射缺失（仅表达式位认领在案） | C1/C2 | x09 |
| **B96** | async 推导式误生成 + 内层 code object 丢失 | `async def a2: async for i in _AIT(): acc = [x async for x in _AIT()]` → `acc = await None(_AIT())` + 裸 `i` 泄漏；`<listcomp>` 单元 Missing bytecode | comprehension_generator.py:149-160（`_has_async_comp` 模板）、:369/:409（GET_AITER/await 循环） | async comprehension 装配模板误套用（推导式退化为 await Call），内层推导式 code object 未产出 | C2 + T3 生成路径（II.3 破口） | x09 |
| **B97** | handler 臂内循环控制 break 蒸发 | `except ValueError: → for→if→while→try: i-=1 except ValueError: break` → `break` 变 `pass` | region_ast_generator.py B71 边类型封闭守卫邻域（:30137-30161，该守卫仅覆盖 finally 域，handler 臂循环控制未纳入） | except 臂内循环控制终结块（BlockSemantics.is_break 事实）归属丢失 | C1/C3（B71 同机理异域：finally→handler 臂） | x10 |

### 4.2 「同 Bn 存量」机理外推证据（不重复编号，登记为对应 Bn 的扩展证据面）

| 同 Bn | 本轮新证据（单元） | 外推结论 |
|---|---|---|
| B78（条件位融合） | c03/c07（类体与方法内 `if X: while Y:` → `while X and Y:`）、m04/m09（模块根）、x10 h_basic（handler 臂）、c02/x01/x02（融合为组件） | 融合机理**宿主无关**：模块根/类体/方法/handler 全域触发；原登记（v_b46_face）仅为三元变体，非三元纯条件融合同样成立 |
| B81（真 guard 装配缺口） | m05（模块级 `case {'op': op} if op:` guard 丢弃 + 幻影 continue） | 模块根宿主触发；c06 证明类体宿主下产物升级为 COMPILE_ERROR（→B91） |
| B49/B61（loop-else 归属） | m03（模块级 for-else 折叠为 if/continue 重构）、m06（模块级 while-else 体被内联进循环体） | 模块根宿主触发（原登记为函数级 for-else 三元/深宿主组合） |
| B83（循环体镜像泄漏） | x02 for_in_try（嵌套 try/for 内层 for 镜像泄漏到 finally 后，**无 raise**） | 触发面外推：原锁定条件「循环内 raise」非必要条件，嵌套 try/for 亦触发 |
| B56（assert 降级） | x08 assert_leaf（`assert i or 1` → `if not i: pass`，断言 raise 语义丢失） | 深循环宿主触发 |
| B59/B60/B61 族（match 深宿主装配） | m09（case 臂语句蒸发 `RES='one'`→pass）、x10 h_basic（handler 内 match → `if True: pass else: R='o'` 臂体错位） | match 作宿主的装配缺陷在模块根/handler 宿主复现（对照：match 作叶子 x06 全过） |

### 4.3 探针退化伪差（口径注记，不登记为破口）

x01.if_in_try、x03.while_in_try、x04.try_in_if 三单元报 Different bytecode，经指令流比对确认为**探针退化伪差**：探针源含 `if 1:` / `while 1:`+`break` 折叠形，CPython 优化留下跳转目标 NOP 残段，原 pyc 异常表出现零长区间（如 `4 to 4 -> 38`）与目标 NOP——该几何**无法从任何规范源码复现**，比较管 remove_nop 不剥跳转目标 NOP，故必差。设计教训（移交后续轮探针协议）：避免 `if 1:`/`while 1:`+break 折叠宿主形，改用非常量条件。真实失败统计已剔除该 3 单元：**35 失败单元 − 3 伪差 = 32 真实失败单元 + 2 COMPILE_ERROR 文件**。

---

## §5 修复交接单（致 Task 2.2 修复工程师）

### 5.1 判据草案（只取 I.4 白名单：块末 opcode / 后继前驱集合 / 异常边 / 区域成员关系 / code object 元数据 / 指令 oparg）

| 破口 | 判据草案 |
|---|---|
| B84 | 模块/类体顺序域内块末 opcode ∈ {DELETE_NAME}（函数域 DELETE_FAST/DELETE_DEREF 已覆盖）⇒ 必须产出 ASTDelete；同时装配器对「块集非空 ∧ 发射为空」从静默改为报错（B76 封闭时同款守卫先例） |
| B85 | 链式赋值判据 = 值块内 COPY/GLOBAL 指令 oparg + 连续 STORE_* 计数（code_generator.py:2697 路径对称启用到模块/类体宿主），目标数 = STORE 计数，禁止按宿主分支裁剪 |
| B86 | with 域 items 数 = 该域内 SETUP_WITH/BEGIN... 块末 opcode 计数（块元数据），第二上下文链（withitem 解包认领 :33438 判据）按块成员关系归属同一 With.items |
| B87 | try 子区域臂/体归属 = 异常表 start/end 区间覆盖（异常边白名单）+ 块集成员；臂块被认领后必须发射或显式豁免（else 臂/handler 臂同判据），幻影 continue 禁止 |
| B88 | 尾随 return 归属 = 出口块块末 opcode ∈ {RETURN_VALUE, RETURN_CONST} ∧ 后继集合不含循环头/case 臂入口（后继集合判据禁止拉入）；case 臂吞入变体加「case 体出口后继 = 函数出口」守卫 |
| B89 | 模块根值消费点发射唯一性：同一消费块只允许挂接一个语句宿主（区域成员关系唯一归属，原则 2） |
| B90 | JoinedStr 转换：FormattedValue(format_spec=JoinedStr) 结构保真（ast_converter.py:1399）；发射端产物必须 `ast.parse` 通过方可落地（IV.2 COMPILE_OK 前置） |
| B91 | guard 消费判据（:1805-1900 `_leading_guard`）对称适用于类体宿主；幻影 return 注入点禁止（else 臂语句源必须来自块集成员） |
| B92 | 类体 Assign 装配补 LOAD_CLASSDEREF opname 判据（指令 opcode 白名单；与 B72 的 co_cellvars 元数据判据同源） |
| B93 | 区域认领唯一性：子区域入口同一性 + 区域成员关系守卫（同 B50/B71 封闭判据族），禁止兄弟区域副本替换 |
| B94 | 假循环过滤判据收紧：回边目标 + POP_JUMP_BACKWARD 块末 opcode 双事实（:5011-5054 role 修正区）；跳转目标 NOP 块不得作为循环头证据 |
| B95 | await 语句性发射：块内 GET_AWAITABLE + POP_TOP 序（指令 oparg）⇒ 产出 Expr(Await)；fall-through 认领（:9663）仅限赋值位 |
| B96 | async comprehension 识别 = 内层 code object co_flags COMPILER_FLAG_ASYNCGEN/await 指令（元数据白名单）；内层推导式 code object 必须产出对应生成器单元 |
| B97 | handler 臂循环控制 = BlockSemantics.is_break/is_continue 事实（:198-200）+ 区域成员关系；B71 边类型封闭守卫（:30137-30161）的域从 finally 块扩展到 handler 臂（判据同构，非个案补丁） |

### 5.2 并行派发建议（破口族不相交 ∧ 涉改文件不相交）

- **位 1（region_analyzer.py 识别/装配层）**：B93（镜像替换）+ B94（假循环边界）——识别判据域，与发射层无交集
- **位 2（ast_converter.py + comprehension_generator.py + code_generator.py 生成层）**：B90（f-string）+ B96（async 推导式）——表达式/推导式生成域
- **位 3（region_ast_generator.py 发射层，建议串行或合并派发）**：B84/B85（非函数宿主语句）→ B86/B87/B97（with/异常域）→ B88（return 归属）→ B91/B92（类体）——同文件高内聚，不宜并行切分
- **注**：B89 随位 3 模块根序列发射一并处理；B78/B81/B83/B56/B59-61 族外推证据供对应封闭批次复用判据，无需独立位

### 5.3 门禁与回归提醒（对 2.2 修复工程师自测）

- 自测门禁 = 本轮全部 MISMATCH 转 MATCH ∧ 负对照保持 MATCH ∧ 34 小测试集无回退 ∧ 站桩回归面（§2 五组读数）不变差 ∧ IV.2 门禁自检清单全过
- **新增回归基准**：test_repros/round2/ 42 探针（m01–m12/nm×2、c01–c15/nc×2、x01–x10/nx01）本轮读数 154/189 + 2 COMPILE_ERROR，修复后不得低于本轮，已破单元修复后以 MATCH 为目标
- 负对照基线（§2.2/§2.3 全表）不得回退；probes_rvC/rvC_v2 保持 FAIL（B83 存量，本轮未修复）
- 触及方法 docstring 六项模板（I.7）+ C1/C2/C3 条款；落地声明「代码已落地」（I.6）；判据禁止名字白名单/start_offset 魔数/深度特判/少发射换绿

---

## 附：本轮产物清单

- `rounds/round2/`：REVIEW.md、r2_regen_verify.py、r2_regress_index.json、r2_regress_replay.json、r2_probe_index.json、r2_probe_results.json、r2_fail_units.json
- `test_repros/round2/`：gen_probes.py + 42 探针（m01–m12、nm01–nm02、c01–c15、nc01–nc02、x01–x10、nx01，各 .py/.pyc/*OK.py）+ r2_mine.txt + r2_probe_index.json
