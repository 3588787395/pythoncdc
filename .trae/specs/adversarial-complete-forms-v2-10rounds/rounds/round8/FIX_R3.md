# Round 8 回退整改批 FIX_R3（任务「残余破口清零冲刺」·P0 回退修复批）

- 规范：`adversarial-complete-forms-v2-10rounds`（spec.md 理论基准 I 全部 + II.7）
- 被整改对象：主代理 402 全量验证序（shard4_report_new.json）实测的 **1 单元回退**——`site-packages/IQEngine/plugins/plugin_fly_data/local_variables/finance.pyc` 基线 132/132 → 131/132，唯一失败单元 `***<module>.PositionDict.__init__.<dictcomp>: Failure: Different bytecode`（dictcomp 键 `symbol.replace('XSHE','SZ').replace('XSHG','SS')` 整体蒸发 → 裸 `symbol`）
- 判据唯一：`scripts/pyc_verify.py`（RV2 口径 = 先 regen 后 verify）
- 证据前缀：本批新增 `r8v8fixB_repro_p0r2.json`（放行面 6 探针）+ `r8v8fixC_finreg_p0.json`（本批总证据）；最小复现探针 `r8v8fb_finreg.py`（`r8v8fb_` 前缀纪律）
- 纪律：零 git commit/push；命令 ≤300s；不重跑 402 全量（主代理复验 shard4）；临时脚本均在 `d:/Temp/opencode`（repo 内零残留）；本人 regen 副产物 8 件结束已 `git checkout --` 还原（c4_04/c4_07/c4_09/c4_10/r5v5_09 + b104_chain4/b105_walrus/b107_mtarget3 三电池 OK）；主代理 402 验证序产物（site-packages/** M 态）保持原样

---

## §0 引入 hunk 定位（对主代理二分结论的实测勘误）

主代理二分声称「865b901e 该文件 132/132 success → 回退由整改批 6c4468ef 引入」。**实测该结论不成立，真引入点 = 865b901e（位C定稿）本批的 [B106] hunk，非整改批 6c4468ef**：

| 实测（临时 worktree + RV2 单验） | finance.pyc 读数 | 最小复现 |
|---|---|---|
| worktree@b09c23f3（865b901e 父提交） | **132/132**（line 616 键链完整） | 4 形全正确 |
| worktree@49603022（core/ 与 865b901e 逐位相同：`git diff 865b901e..49603022 -- core/` 为空，49603022 只改 test_repros/docs） | **131/132**（同名失败单元，键蒸发） | 4 形中键链 2 形蒸发 |
| 工作树 HEAD 458e740e（整改批含入） | 131/132（= 402 shard4 报告读数） | 同上 |

**主代理二分误导机理**：`finance.pyc` 本身 gitignored（tracked 的是 `financeOK.py` 基线产物）；历轮提交纪律均为「regen 副作用已还原」，故 865b901e/6c4468ef/458e740e 各提交时点的 tracked `financeOK.py` 是**旧轮 stale 内容**（恰含键链、编译与原 pyc 字节相同——因键链本就是正确反编译）。主代理在 865b901e worktree 内读到 132/132 的「成功」实为 stale 基线产物的字节等价命中，未反映该提交反编译器的真实输出。**任何时点的真值只能以「现跑 pycdc + RV2」为准**——本批全按此口径实测。

**整改批 6c4468ef 五项修复（B104-R2a/R2b、B105-R2、B107-R2、B103-R2）经复核与本回退无关**：五 hunk 分别在 while 循环头折叠/海象净栈深/链式复杂目标/match 守卫域，均不触及 dictcomp 键/值切分路径；本回退自 865b901e 引入后历经整改批三轮验证（r2fixallB/C、站桩 3 面、34 集）均未被探针面覆盖（4-form 键链形不在任何登记探针中）。

---

## §1 回退根因（引入 hunk 锚点 + 机制）

**引入 hunk**：865b901e [B106] `core/cfg/comprehension_generator.py` `_find_dict_kv_split_point`（现锚点 :1664）内的 **elif 链重构**——把原尾置 `delta = self._get_stack_delta(instr)` 共用求值改为 `elif` 分支结构（现 :1695-1712：PUSH_NULL / CALL_FUNCTION_EX / LIST_EXTEND 族 + else 回退 `_get_stack_delta`），但 `if instr.opname == 'LOAD_METHOD': _has_load_method = True` 分支只置标记、**未定 `delta`**，其后共用的 `stack_depth += delta; depth_history.append(...)` 复用**上一迭代的 stale delta**。

**机制一句话**：方法链 `k.m1(...).m2(...)` 的第二个 `LOAD_METHOD` 紧跟 `CALL`（delta = −(n+1) = −3）之后，stale delta 二次污染深度历史（正确值应为 +1：3.11 `LOAD_METHOD` 弹 receiver、压 [self|NULL, method] 两槽净 +1）⇒ `final_depth < 1` ⇒ 切分点 `None` ⇒ `_split_dict_comp_kv` 键窗为空 `key_expr=None` ⇒ 推导式解析整体回退，键链蒸发、键退化为裸迭代目标名。

**形态敏感性精确解释**（与实测 4 形逐位吻合）：单方法键（`k.replace('a','b')`）的 `LOAD_METHOD` 前驱是 `LOAD_FAST`（stale delta 恰为 +1）⇒ 侥幸存活；值侧链（形 D）同理由 `LOAD_FAST` 前驱侥幸存活；键侧 ≥2 方法链（形 A/形 B）必中招——即 finance.pyc `PositionDict.__init__`（`symbol.replace('XSHE','SZ').replace('XSHG','SS')`）132→131 的唯一失败单元。

**判据错误定性**：该 hunk 声称「判据 = opcode 栈效应（I.4 白名单）」，但重构后的模拟在 LOAD_METHOD 位**不再计算真实栈净效应**（读未定义于本迭代的变量 = 判据本身错误），按任务纪律「若某 hunk 判据本身错误则按正确判据重写该 hunk」执行——**只重写该分支，不回滚整个 B106 hunk**（PUSH_NULL/CALL_FUNCTION_EX/LIST_EXTEND 族覆盖 = c4_12 7/13→13/13、r5v5_07 4/13→13/13、lambda 变体 26/27→27/27 的已放行面，维持不变）。

---

## §2 修复（判据 + 锚点 + I.6 落地声明）

**修复判据（I.4 白名单：块内 opcode 序 + CPython 3.11 值栈净效应）**：`LOAD_METHOD` 弹 receiver、压 [self|NULL, method] 两槽，净栈 **+1**；与既有 [R40 fix] 的 `CALL −(n+1)` 口径配套（CALL 弹 n 实参 + method + self|NULL 共 n+2、压 1 结果）。

**修复锚点**：`core/cfg/comprehension_generator.py:1683-1697`（`_find_dict_kv_split_point`，:1664）——`LOAD_METHOD` 分支补 `delta = 1`（[B106-R3] 内联注释块承载根因/判据/放行面维持声明）。单 hunk +14 行、零新增 def、零删除（B106 其余协议族覆盖原样保留，C3）。

**行为等价性论证**：对不含 PUSH_NULL/CALL_FUNCTION_EX/LIST_EXTEND 族的窗口，修复后深度模拟与 b09c23f3（回退前基线）逐位一致（`_get_stack_delta(LOAD_METHOD)` 本就返回 +1，elif 重构前的落穿路径同为 +1）；对含 B106 新协议族的窗口维持 865b901e 设计覆盖。改变行为的窗口仅有「LOAD_METHOD 前驱 delta ≠ +1」的位形 = 旧代码深度历史必错、切分必 None、键必蒸发的位形 ⇒ 本修复不可能使任何原 PASS 单元转 FAIL（蒸发酵果 = 字节不等 = 必 FAIL）。

**[I.6 代码已落地声明]**：上述修复已写入工作树 `core/cfg/comprehension_generator.py`（`git diff --stat -- core/` = 单文件 +14），未 commit/push（纪律）；下表全部读数在该落地态实测取得。

---

## §3 读数表

| 验证面 | before（引入后） | after（本批） |
|---|---|---|
| 最小复现 `test_repros/round8/r8v8fb_finreg.py`（4 形：裸键链/PositionDict 原形/单方法键对照/值侧链对照） | 7/9（`<module>.<dictcomp>` + `PositionDict.__init__.<dictcomp>` 两单元 Different bytecode） | **9/9 success**（4 形键链全恢复） |
| **finance.pyc RV2 单验（回退主体）** | 131/132 | **132/132 success** |
| 放行面 6 探针（R8FB_STAMP=p0r2） | — | B104_main **14/14**、B105_main **13/13**、B105_call **12/12**、B107_main **14/14**、B103_main **13/13**、B103_guard **8/8**（74/74；`r8v8fixB_repro_p0r2.json`） |
| 变体电池 3 件（整改批放行面） | — | b104_chain4 **6/6**、b105_walrus **5/5**、b107_mtarget3 **6/6** |
| 触及域加验（B106/B113/推导式族电池） | — | b106_star **18/18**、b106_mixed **7/7**、b113_flat **21/21**、b113_doubfor **10/10**；b96_async 14/18（b3/b7.inner.\<listcomp\> 4 单元为 B112 存量移交项，**修复前后逐位一致、非本批引入**，实测对照：无修复 HEAD 同读数） |
| 站桩 round1face | 417/423（基线） | **417/423**（逐位一致） |
| 34 集 shard0 | 183/190（基线） | **183/190，NEWFAIL=0**（5 失败文件全在 failing_index.json 基线索引） |
| shard4 其余 5 基线失败文件（防回退面） | 9/10、10/11、13/14、18/19、34/37（402 报告） | **逐位一致**（executor/strategy_universe/trading_dates_mixin/history_api/order_api，无恶化无扰动） |

---

## §4 SimulationParameters 星参形态变化定性记录（非失败源）

- 单元：`SimulationParameters.__init__`（finance.pyc 同文件）。基线（b09c23f3 实测）：`datetime.datetime(*(self._engine.config.strategy.start_date.timetuple()[:3]))`；当前：`datetime.datetime(*self._engine.config.strategy.start_date.timetuple()[:3])`（括号形态 → 裸星形态）。
- 定性：**字节等价**——两种源形态编译为相同字节码（星实参解包 `x.timetuple()[:3]` 均为 LOAD→BUILD_SLICE→BINARY_SUBSCR→CALL_FUNCTION_EX 序）；该单元验证始终 PASS（本批 132/132 内含），**非失败源**。
- 形态来源：865b901e [B106] star_args 实参序保真（c4_12 7/13→13/13、r5v5_07 4/13→13/13、lambda 变体 26/27→27/27 放行面）——非主代理声称的「整改批 B104-R2b/B106 域外溢」（整改批不触及该路径）；如实登记为 B106 放行面的形态差异，验证口径下无影响。

---

## §5 IV.2 合规

| 项 | 读数 |
|---|---|
| py_compile 涉改文件 | `core/cfg/comprehension_generator.py`（唯一涉改）rc=0 |
| 包导入 | `from core.cfg.comprehension_generator import ComprehensionGenerator` OK |
| 插桩残留 | 零（本批全部调试脚本在 `d:/Temp/opencode`，repo 内 grep print/pdb/R8CDBG/R8FBDBG 零命中；diff +14 行零 print） |
| G3（新增 def 前缀） | 未新增任何 def（单 hunk 分支内修正）——零违规 |
| G4（硬编码） | 零路径/偏移/计数硬编码 |
| BOM 单头 | 首字节 102,114,111（'fro'），无 BOM |
| I.7 docstring 同步 | `_find_dict_kv_split_point` 存量无 docstring（[R40 fix] 行内注释风格，b09c23f3 即如此）——守卫行为变化由 [B106-R3] 内联注释块就地承载（:1683-1695），无 docstring 失同步 |
| 探针命名 | `r8v8fb_finreg.py`（最小复现）；证据 `r8v8fixB_repro_p0r2.json` / `r8v8fixC_finreg_p0.json` |

---

## §6 证据清单

- `rounds/round8/r8v8fixC_finreg_p0.json`——本批总证据（回退定位 worktree 实测记录、修复锚点、全部读数、IV.2）
- `rounds/round8/r8v8fixB_repro_p0r2.json`——放行面 6 探针（74/74）
- `rounds/round8/r8v8rev_34set_shard0.json`——34 集 shard0（183/190，NEWFAIL=0）
- `rounds/round8/r8v8fixB_full_round1face.json`——站桩 round1face（417/423）
- `test_repros/round8/r8v8fb_finreg.py`——最小复现探针（4 形）
- `shard4_report_new.json`——主代理 402 序回退报告（before 131/132 读数来源）

**移交**：无新登记；B112 async 闭包推导式族（b96 电池 4 单元）维持存量移交，B122/B123 候选维持前批登记。轮终判 = 本 P0 回退已封闭（132/132 恢复 + 放行面零回退），建议主代理按纪律仅复验 shard4。
