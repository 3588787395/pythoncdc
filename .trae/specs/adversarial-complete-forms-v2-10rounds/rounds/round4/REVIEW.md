# Round 4 评审报告（Task 4.1）—— 表C 31 扩展形态对抗

> 独立对抗评审（只读审计 + 探针构建 + 报告）。HEAD = `47a0d7ad`（round4 启动快照）；`git diff 2a11fc3a..HEAD -- core/` 为空、工作树 `core/` 零改动。
> 口径：一切读数以 HEAD 代码 regen（RV2：`python pycdc.py <pyc> -o <同目录>OK.py`）后 verify；结论逐条引用条款编号（I.x / C1/C2/C3 / II.3 / 13 误解编号）。
> 探针：`test_repros/round4/`（前缀 `c4*`/`n4_0*`，零覆盖既有 133+ round3 文件与 round4 预置 tracked 文件）。命令全部 ≤300s，站桩分片执行。
> 说明：`test_repros/round4/` 目录本已存在且含 69 个 tracked 预置文件（ANALYSIS.md、`_probe_*` 等）；本轮新增 20 个 `c4_*` 攻击探针 + 5 个 `n4_0*` 负对照（含 .py/.pyc/*OK.py），零覆盖、零改动 tracked 文件（`git status` 无 M 项）。

## §0 终判预备结论（三态）

**三态口径（II.3）**：对 spec III.4 表C 的 31 扩展形态（归并为 20 形态族）逐一给出「完备 / 破口 / 零能力」。完备证据 = 深层探针 ≥3 层嵌套 ∧ 宿主矩阵交叉全 MATCH ∧ 负对照 MATCH；破口证据 = 锚点 file:line + 机制 + 违反条款。

**终判预备**：
1. **表C 大面积破口：20 形态族中 13 族确证破口**——`except*`、match+守卫+8 模式、多上下文 with、try-finally-only、multi_target、chained_comparison、walrus、star_args、relative_import、star_import、nested_comprehension（多 for 子句）、decorator_with_args（局部类方法）、async 五件套、while-else。**仅 7 族维持完备**：elif 链、augmented_assign、keyword_args、slice、global/nonlocal、f-string 转换符。
2. **新登记破口 B100–B113（14 项）**——其中 `relative_import`（B100）与 `star_import`（B101）为**结构性零能力表征**：`from . import mod` 发射 `from  import mod`（**产物非法**）；`from os.path import *` 发射 `import os.path`（star 丢失）。`except*`（B102）为**首攻即破且浅层负对照 n4_05 亦失败**（比 C2「深层才错」更强）。
3. **negative control 反向证据**：`n4_05_neg_except_star` 2/3（`n_except_star_two` 两 handler 即破）；`c4_12_star_args.e02_shallow`（`f(*x,1)` 浅层即破）——坐实破口**非深层专属**。
4. **站桩回归 6 面零回退**（§2，WORSE=0），其中 3 面较承接基线改善；quotation 152/153 逐单元相同。

---

## §1 合规审计表（只统计本轮起点后的新增；基准 = HEAD `47a0d7ad`）

审计方法：`git diff 2a11fc3a..HEAD -- core/`（**空**）+ `git status --porcelain`（全树）+ 树内 grep + 字节级 BOM 计数。

| 红线 | 扫描方法 | 命中 | 判定 |
|---|---|---|---|
| 在途变更（core/） | `git status --porcelain core/` | **空**；本轮改动仅 `test_repros/round4/` 探针与 `rounds/round4/` 证据（均未跟踪/声明） | **PASS** |
| I.4-① 文件/函数名白名单 | 新增行（本轮无 core 改动） | 0 | 新增 0 PASS |
| I.4-② start_offset 魔法阈值 | 新增行 | 0（树内存量 `start_offset` 均为序键/集合成员，无 `> / < / == 常数`） | 新增 0 PASS |
| I.4-③ 跨层 `entry in blocks` 反查 | 新增行 | 0（树内存量见注①） | 新增 0 PASS |
| I.4-④ 新增 `self.` 跨方法状态 | 新增行 | 0 | 新增 0 PASS |
| I.4-⑤ 少发射/硬编码深度上限 | 新增行 | 0（树内存量 `_loop_depth/_function_depth` 为生成器状态标志非区域嵌套上限） | 新增 0 PASS |
| I.5 禁止前缀方法（新增） | 新增行 `def (_fix_\|_merge_\|_patch_\|_fallback_\|_hack_\|_workaround_\|_temp_)` | 0（树内存量 3 处历史名） | 新增 0 PASS |
| BOM 单头（IV.2） | 逐文件首 3 字节 + 全文计数 | `region_ast_generator.py`=`efbbbf`/1；`region_analyzer.py`=`efbbbf`/1；`code_generator/exception_handler/pattern_parser/comprehension_generator/ast_converter` 无 BOM | PASS |
| 插桩残留 | 新增行 grep `print(\|pdb\|breakpoint(\|# TODO\|# FIXME\|# DEBUG` | 0 | 新增 0 PASS |
| `*OK.py` 手改 | `git status --porcelain \| grep OK.py` | 0 个 tracked `*OK.py` 显示 modified（仅本轮新增未跟踪 `c4*/n4_0*OK.py`） | PASS |
| 命令时限 | 全部 ≤300s（站桩分片、单面 ≤72 文件） | — | PASS |

**审计结论：I.4 五项 + I.5 七前缀 + BOM + 插桩 + 在途 + `*OK.py` 全 PASS，本轮新增违规 0**（本轮为纯评审，无 core 源码改动）。
> 注①：跨层 `X.entry in Y.blocks` 反查在树内**存量**出现（如 `region_ast_generator.py:1410/21139/29741/34546`、`region_analyzer.py:25364`），均为历史守卫实现，属本规范 HEAD 基线之前，**非本轮新增**，不作本轮打回项；仍建议 Round 7/8 逐条复核其是否构成 C3 破口。

---

## §2 站桩回归读数表（RV2：先 HEAD regen 再 verify）

对照脚本 `r4v4_compare_regress.py` → `r4v4_station_regress_compare.json`；逐文件读数 `r4v4_regress_*.json` / `r4v4_full_*.json`。

| 面 | 文件 | 承接基线 | 本轮读数 | same/improved/**WORSE** | 判定 |
|---|---|---|---|---|---|
| v2 round2 45 文件面 | 45 | 234/251 | 234/251 | 45/0/**0** | 逐位持平 ✓ |
| v2 round2 42 探针面 | 42 | 154/189(tail) | **172/196** | 32/10/**0** | 无回退，10 文件改善 ✓ |
| v2 round1 哨兵面 | 24 | 417/423 | 417/423 | 24/0/**0** | 逐位持平 ✓ |
| v1 残余面 | 72 | 404/446 | **417/446** | 62/10/**0** | 无回退，10 文件改善 ✓ |
| 旧规范 round6–10 面 | 59 | 658/692 | **664/692** | 55/4/**0** | 无回退，4 文件改善 ✓ |
| quotation.pyc 单验 | 1 | 152/153（唯一失败 `change_his_to_forward`） | 152/153，失败单元逐一相同 | — | 持平 ✓ |

**站桩总判：6 面零回退（WORSE=0）、零缺失文件（only_base=0）、失败单元无新增（除 tail-only 面口径限制）。** PASS。
> 注：`round2face`/`probe42` 基线为 tail-only（失败单元名截断），对这两面以「状态 + units 读数」为准；`round1face`/`residual`/`oldface` 基线含完整 failures，逐单元集合比对 `miss/extra` 均 0（probe42 报告的 `miss/extra` 为 tail-only 口径噪声，不算真实位移）。

---

## §3 完备形态攻击结果表

探针生成：`test_repros/round4/gen_probes.py`（程序化 25 文件：20 `c4_*` 攻击 + 5 `n4_0*` 负对照；另有 1 个 round4 预置 tracked 文件 `n4_01_no_match_control` 被 glob 纳入）。读数：`r4v4_probe_results.json` / `r4v4_probe_full.json`。
**TOTAL 301/338 = 89.05%**（attack 262/298、neg 39/40；compile_error 1：`c4_14`）。

### 3.1 逐族结果（20 形态族）

| # | 形态族 | 探针 | 读数 | 失败单元要点 | 判定 |
|---|---|---|---|---|---|
| 1 | **elif 链** | c4_01 / n4_01 | **14/14** | —（含模块根/类体/for/while/try/with/match/闭包/推导式交叉） | **完备** |
| 2 | **for-else / while-else** | c4_02 | 13/14 | `CL.m`（while 体末为 break 分支 + else + 循环后 return：else 与末尾 `return y` 均丢失） | **破口 B109** |
| 3 | **except* 异常组** | c4_03 / n4_05 | 11/13（neg 2/3） | `e01_root`（第 2 个 `except*` 被错构为 `else` 分支）、`e04_with`（`except*+else+finally` 拆成独立 try）；neg `n_except_star_two` 浅层即破 | **破口 B102** |
| 4 | **match+守卫+8 模式** | c4_04 | 8/13 | `e04_mapping`（第 2 个 mapping case 被错写成第 1 个）、`e05_class_kw`（第 2 class 模式+默认丢失）、`e06_or_guard`（or+guard 完全错构）、`e07_capture.inner`（守卫 `is not None`→真值 `a`）、`CM.m`（守卫丢失） | **破口 B103** |
| 5 | **多上下文 with** | c4_05 | 12/14 | `e01_root`/`e03_triple`/`CW.m`/`e08_closure`（with 体含 return → 多余 `return None`）；`e09_comp_host`（多 for 子句丢失，见 B113） | **破口 B110** |
| 6 | **try-finally-only** | c4_06 | 12/14 | `e01_root`（finally 体被复制进 try 体、return 移入 try）；`e06_while`（finally 内 `del x` → `pass`） | **破口 B108** |
| 7 | **multi_target_assign** | c4_07 | 10/14 | `e04_unpack`（链式解包 + 尾部 return 丢失）、`e05_star_unpack`（`c,*d` 目标丢失）、`e06_chain_target`（`a[0]=b[1]=x+1` → `b[1]=None`）、`e09_attr_chain`（`o.a=o.b=x` → `o.b=None`） | **破口 B107** |
| 8 | **augmented_assign** | c4_08 | **13/13** | —（含 `+=`/位运算/`@=`/`**=`、下标/属性/闭包非局部、BoolOp RHS 交叉全过） | **完备** |
| 9 | **chained_comparison** | c4_09 | 11/14 | `e04_deep`（`0<x<10<x*2` → `0<x and 10<True`，**链尾操作数被常量替换**）、`e08_while`（while+链→if）、`CCMP.m`（with 宿主 return 链蒸发为 None） | **破口 B104** |
| 10 | **walrus** | c4_10 | 8/13 | `e01_root`（`if (n:=len(x))>3`→`if 3:`）、`CW2.m`、`e09_with`、`e05_nested`（比较条件内 walrus 丢失）、`e06_call_arg`（walrus 作实参→整条调用丢失） | **破口 B105** |
| 11 | **keyword_args** | c4_11 | **14/14** | —（含 `**dict` 混合、类体/闭包/推导式/嵌套调用交叉） | **完备** |
| 12 | **star_args** | c4_12 | 7/13 | `e02_shallow`（`f(*x,1)`→`f(1,*x)` 重排，**浅层即破**）、`e03_mixed`、`e04_deep`（`f(*xs,*ys,...)`→ 丢 `*xs`）、`e06_nested.inner`（`f(*xs,*xs)`→丢一）、`CSA.m`、`e07_match_host` | **破口 B106** |
| 13 | **slice** | c4_13 | **13/13** | —（步长/负步长/表达式边界/切片删除目标/推导式交叉全过） | **完备** |
| 14 | **relative_import** | c4_14 | **compile_error 0/0** | 产物 `from  import mod`（level 丢失→**非法语法**）、`from .sub import`→`from sub import`、`from ..pkg`→`from pkg` | **破口 B100**（产物非法） |
| 15 | **star_import** | c4_15 | 5/7 | `<module>`（`from os.path import *`→`import os.path`，star 丢失）、`e01_use`（Missing bytecode，star 名丢失） | **破口 B101** |
| 16 | **global / nonlocal** | c4_16 | **21/21** | —（global/nonlocal 在嵌套函数/循环/条件/类体/推导式宿主全过） | **完备** |
| 17 | **f-string 转换符** | c4_17 | **12/12** | —（`!r/!s/!a`、嵌套字段、动态 format spec、转换符表达式全过） | **完备** |
| 18 | **nested_comprehension** | c4_18（+B113 最小复现） | 30/30 直接探针，**但 B113 破** | `_scratch_m4`：`[(a,b) for a in [xs[0]] for b in [xs[1]]]`→丢第 2 子句；`[(a,b) for x in xs for a in [x] for b in [x]]`→三子句丢一 | **破口 B113** |
| 19 | **decorator_with_args** | c4_19 | 27/28 | `e09_method_local.Local.m`（函数局部类的方法带参装饰器 → `@((x,))`，装饰器变元组） | **破口 B111** |
| 20 | **async 五件套** | c4_20 | 21/24 | `e05_async_compound`（`yield await c`→`await c`，yield 丢失）、`e07_async_closure.outer.inner`（async 推导式蒸发为 `gen()`，`<listcomp>` Missing bytecode） | **破口 B112** |

**族合计**：完备 7 族（1/8/11/13/16/17 及 for-else 单侧）；破口 13 族；零能力 0（relative_import/star_import 归为**破口**，因其 T1/T2/T3 路径在但产物非法/丢失，非路径缺失）。

### 3.2 负对照（MATCH 对照）结果

| 负对照 | 内容 | 读数 | 判定 |
|---|---|---|---|
| n4_01_neg_control_flow | for-else/while-else/elif/try-finally 浅层 | 5/5 | MATCH |
| n4_02_neg_expr | multi_target/augassign/chain_compare/walrus/slice/fstring/kwarg/star/nested_comp 浅层 | 12/12 | MATCH |
| n4_03_neg_match_with | match value/seq、multi-with、global 浅层 | 5/5 | MATCH |
| n4_04_neg_deco_async | deco/await/async-for/async-with/yield-from 浅层 | 8/8 | MATCH |
| n4_05_neg_except_star | 单/双 `except*` 浅层 | **2/3** | **FAIL**（`n_except_star_two` 两 handler 即破 ⇒ B102 非深层专属） |
| （预置）n4_01_no_match_control | 既存 tracked 文件 | 7/7 | MATCH（非本轮探针） |

### 3.3 II.7 十三条误解自查（对本轮「完备维持」宣告）

| # | 误解 | 本轮自查 |
|---|---|---|
| 1 | 循环论证分母 | 分母 338 由探针真实单元数求和；完备族分母来自独立探针 |
| 2 | 有过就算 | 未以「有成功单元」充完备；完全按单元 MATCH 判定 |
| 3 | 语料证据口径 | 探针判据 = 逐 code object 字节码等价，非文本比对 |
| 4 | 无限分母 | 分母固定 338，无动态扩张 |
| 5 | 节点词汇当完备 | 完备族基于**全单元 MATCH ∧ 负对照 MATCH** |
| 6 | 浅层测试当无感证明 | 已用 n4_05 / c4_12.e02_shallow 反证「浅层即破」，不据浅层判完备 |
| 7 | 门禁读数当完备性 | §2 站桩合格 ≠ 完备；§3 独立攻击给三态 |
| 8 | 顶层构造粗清单 | 按 III.4 全名单细分 20 形态族、逐宿主交叉 |
| 9 | 识别率当完备性 | 未以「识别到」充「保真」；relative_import 识别到但产物非法 → 破口 |
| 10 | 维度互替 | 宿主维度（模块根/类体/函数根/if/for/while/try/with/match/推导式/闭包）与形态维度交叉独立取证 |
| 11 | 改工具不改方法 | 未改核心；读数为 HEAD 原样 |
| 12 | 错误检测标准（3.11=CHECK_EG_MATCH/PREP_RERAISE_STAR/is_except_star） | except* 探针仅用 3.11 标记面；本轮错误均为 `Different control flow/bytecode`、`Missing bytecode`、`compile_error`，未见 3.12 `PRELOAD_RERAISE` 误报 |
| 13 | 语料上限当能力上限 | 未以语料规模推论能力上限 |

---

## §4 新破口登记（B100 起）

登记规则：与既有 Bn 同机理者标「同 Bn 存量」，不重复编号；新机理自 **B100** 续接（B98/B99 已于 round3 用尽）。全部破口附锚点 file:line + 机制 + 违反条款。

### 4.1 新编号破口

| 编号 | 形态 | 最小复现（探针.单元） | 锚点 file:line | 机制 | 违反条款 |
|---|---|---|---|---|---|
| **B100** | **relative_import 层级丢失 → 产物非法** | `c4_14.e01_use`：`from . import mod`→`from  import mod`；`from .sub import name`→`from sub import name`；`from ..pkg import other`→`from pkg import other`（整文件 compile_error） | `core/cfg/region_ast_generator.py:11256-11268`（IMPORT_NAME 前导 LOAD_CONST int 回看仅扫 `_self_loop_instrs`，相对层级未捕获）；构造处 `:662/:970/:1281/:7126` 未携带 `level`；发射 `core/cfg/code_generator.py:387-391`（dict 路径 `'.'*level`）/`:3406-3421`（AST 路径完全不发射 level） | `IMPORT_NAME` 的 level 参数（栈顶 LOAD_CONST int）未被读取/传递，相对导入降级为绝对且无模块名 → 产物非法 | **C1**（局部消费：import 区域未消费 level 结构事实）+ **T3 生成路径**丢失 AST `ImportFrom.level`；破坏 I.1 原则4（入口引用语义） |
| **B101** | **star_import 丢失** | `c4_15.<module>`：`from os.path import *`→`import os.path`、`from collections import *`→`import collections`；`c4_15.e01_use` Missing bytecode | `core/cfg/region_ast_generator.py:11277-11293`（`IMPORT_STAR` 检测仅在 self-loop 分支；模块级直线代码路径未识别）；`core/cfg/code_generator.py:372-393`（ImportFrom 需含 `{'name':'*'}`） | `IMPORT_NAME+IMPORT_STAR` 未被重建为 `ImportFrom(names=['*'])`，降级为普通 `Import(module)`，star 名与后续 LOAD_NAME 全丢 | **C1** + I.1 原则4（ImportFrom 节点类型映射错误）；同 B100 属「import 形态保真」族 |
| **B102** | **except\* 多 handler / else / finally 错构** | `c4_03.e01_root`：两 `except*` → 第 2 个变 `else`；`c4_03.e04_with`：`except*+else+finally` 拆成两个独立 try；neg `n4_05.n_except_star_two`（浅层亦破） | `core/cfg/region_analyzer.py:8122 _identify_try_except_regions`；`core/cfg/exception_handler.py`；发射 `core/cfg/code_generator.py:697-702 / :2093-2094`（`is_except_star`） | TryStar 归并时，第二个 `except*` 手的异常组块被误认作 else 臂（handler 归并/汇合剪枝未按 `CHECK_EG_MATCH`/`PREP_RERAISE_STAR` 区分），`else`/`finally` 与多 handler 的组合边界坍缩 | **C2**（黑箱组合：多 handler 抽象节点未整体保真）+ **C3**（handler 归并守卫未封闭）；I.1 原则2（每块唯一归属） |
| **B103** | **match mapping/class/or+guard/guard 错构** | `c4_04.e04_mapping`（第 2 mapping case 覆写成第 1）、`e05_class_kw`（第 2 class 模式+默认丢失）、`e06_or_guard`（or+guard 完全错构）、`e07_capture.inner`（守卫 `is not None`→`a`）、`CM.m`（守卫丢失） | `core/cfg/pattern_parser.py:66 parse_case_guard`、`:313 _extract_case_guard_from_blocks`；`core/cfg/region_analyzer.py:13887 _identify_match_regions` | 模式解析器对 mapping 键集/`**rest`、class 关键字模式、or 模式与 guard 的组合未按模式子块唯一归属解析；guard 块与 case header 同块时被误并 → 模式/守卫保真丢失 | **C1**（模式子块局部消费失败）+ **C2**（多 case 抽象节点组合泄漏）；I.1 原则3（嵌套即抽象节点） |
| **B104** | **chained_comparison 链尾操作数损坏 / 宿主蒸发** | `c4_09.e04_deep`：`0<x<10<x*2`→`0<x and 10<True`；`e08_while`：`while 0<x<n<100:` → `if ...`；`CCMP.m`：with 宿主 `return a<b<c<len(...)` → `return None` | `core/cfg/region_analyzer.py:17399 _identify_chained_compare_regions`；`core/cfg/region_ast_generator.py:14321`（条件 Compare 重建） | 链式比较的**末操作数**（含 BinOp/Call）未被消费，被常量/布尔占位替换；链式比较块在 while 头/with 宿主下归属错位 → 值链蒸发 | **C1**（末操作数未局部消费）+ **C2**（宿主相关结构不一致）；I.1 原则4 |
| **B105** | **walrus 条件/实参位丢失** | `c4_10.e01_root`：`if (n:=len(x))>3:`→`if 3:`；`e05_nested`：`if (a:=x+1)>y:`→`if y:`；`e06_call_arg`：`f((n:=x+1),n)`→仅剩 `n=x+1`；`CW2.m`、`e09_with` | `core/cfg/region_ast_generator.py:2919-2972`（NamedExpr 重建）、`:14321`（`NamedExpr(walrus, Compare)` 条件路径）、`:12529-12532` | `NamedExpr` 的 value 消费链在「比较条件」与「调用实参」消费位断链，仅保留 STORE 目标或退回常量/占位 | **C1**（walrus 值链局部消费失败）+ **T3 生成**；同 B88 家族（值消费链断裂） |
| **B106** | **star_args 多星/非尾星 重排或丢失** | `c4_12.e02_shallow`：`f(*x,1)`→`f(1,*x)`（浅层即破）；`e04_deep`：`f(*xs,*ys,**{...})`→丢 `*xs`；`e06_nested.inner`：`f(*xs,*xs)`→丢一；`e03_mixed`、`CSA.m`、`e07_match_host` | `core/cfg/code_generator.py:3495/:3561`（starred 实参发射）；Call/arguments 重建于 `region_ast_generator.py` | 调用实参列表中多个 `*` 或 `*` 非尾置时，参数顺序被打乱（star 后移）、多余 star 被丢弃 | **C1**（实参序列未整体消费）+ I.1 原则4（Call 参数序保真）；同 B95 存量化实参族 |
| **B107** | **multi_target 链式解包/属性·下标链赋值 值丢失** | `c4_07.e04_unpack`：`a,b=c,d=(x,x+1)` → 尾部 return 丢失；`e05_star_unpack`：`a,*b=c,*d=[...]`→ 丢 `c,*d`；`e06_chain_target`：`a[0]=b[1]=x+1`→`b[1]=None`；`e09_attr_chain`：`o.a=o.b=x`→`o.b=None` | `core/cfg/region_ast_generator.py:1008/:11412/:12309`（unpack_info）；`core/cfg/code_generator.py:1136/:3102`（链式赋值发射） | 链式赋值（多目标/解包目标）在生成层只保留首目标值，后续目标值退化为 `None`；解包元组 RHS 重建丢失部分目标 | **C1** + I.1 原则4（Assign 目标序/值语义） |
| **B108** | **try-finally-only finally 体复制 / `del`→`pass`** | `c4_06.e01_root`：finally 体被复制进 try 体且 return 移入 try；`e06_while`：finally 内 `del x` → `pass` | `core/cfg/region_ast_generator.py` Try/finally 生成（spec 空体 finally 锚点 `:9016-9019`）；`core/cfg/region_analyzer.py` try 识别 | finally 体块归属错位：部分语句被同时归入 try 体（复制）；`del`（DELETE 指令）在 finally 中未被识别为 Delete 语句 → 退化为 `pass` | **C1**（finally 体块唯一归属失败）+ **C2**（try/finally 组合结构不一致）；I.1 原则2 |
| **B109** | **while-else 丢失（体末为 break 分支）** | `c4_02.CL.m` 与 `_scratch_m4.c1`：`while xs: ... if y>3: break\nelse: return None\nreturn y` → 输出 `while ...: break; return None`（else 消失、末尾 return 丢失） | `core/cfg/region_analyzer.py:5666 _find_loop_else`；loop-else 发射于 `region_ast_generator.py` | 当 while 体末语句为 break 分支（无其它体语句）时，`_find_loop_else` 判定失败：else 块与循环后块被合并为无条件 return | **C3**（loop-else 守卫未封闭）+ I.1 原则1（loop 区域边界识别） |
| **B110** | **多上下文 with 含 return 体 → 多余 `return None`** | `c4_05.e01_root`/`e03_triple`/`CW.m`/`e08_closure`：`with c1, c2: return expr` → 追加不可达 `return None` | `core/cfg/region_analyzer.py:13192 _identify_with_regions`；`region_ast_generator.py` with 生成 | `with`（≥2 项或嵌套 with）体含 return 时，with 区域出口块被额外发射 RETURN_CONST None，产生多余返回 | **C1**（with 区域出口块归属重复）+ I.1 原则2 |
| **B111** | **局部类方法 decorator-with-args → 元组** | `c4_19.e09_method_local.Local.m`：`@deco(x) def m` → `@((x,))` | `core/cfg/region_ast_generator.py:2451-2496 _extract_decorators`、`:3545-3634`（类内 decorator）；`core/cfg/code_generator.py:2725`（`@` 处理） | 函数局部定义类的方法带参装饰器被重建为元组字面量（`((x,))`），装饰器 Call 结构丢失 | **C1** + I.1 原则4（FunctionDef.decorator_list 引用语义） |
| **B112** | **async：`yield await expr` 丢失 / async 推导式蒸发** | `c4_20.e05_async_compound`：`yield await c`→`await c`；`e07_async_closure.outer.inner`：`[v async for v in gen]`→`gen()`（`<listcomp>` Missing bytecode） | `core/cfg/region_ast_generator.py` async for/with/yield 生成（spec `:30154`） | async 生成器中 `yield await` 的 yield 语义丢失（退化为 await 语句）；async 推导式在闭包内未识别 → 值退化为原生成器调用 | **C1**（await/yield 值链局部消费）+ **T3**；async 推导式项 **同 B96 存量** |
| **B113** | **多 for 子句推导式子句丢失** | `_scratch_m4.comp2.e2`：`[a for a in [xs[0]] for b in [xs[1]]]`→`[a for a in (xs[0],)]`；`comp2.e1`：三子句丢一；`c4_05.e09_comp_host` | `core/cfg/comprehension_generator.py:79 parse_comprehension_code_object`（multi-for 路径 `_parse_multi_for_comprehension`，:95 引用） | 多 `for` 子句推导式中，当某子句迭代器为「列表字面量/含非纯常量表达式」时，后续 `for` 子句的归约块未被消费 → 子句丢失、自由变量悬空 | **C1**（推导式子句块局部消费失败）+ I.1 原则2（每块唯一归属） |

### 4.2 「同 Bn 存量」机理外推证据（不重复编号）

| 同 Bn | 本轮新证据（单元） | 外推结论 |
|---|---|---|
| **B96**（async 推导式） | `c4_20.e07_async_closure.outer.inner` + `<listcomp>` Missing bytecode | async 推导式在闭包宿主仍破，承接 round3 B96 |
| **B88/B90**（值消费链断裂 / 产物非法） | `c4_03`（产物 `else: if TypeError is not None`）、`c4_05`（多余 `return None`）、`c4_14`（产物非法 `from  import mod`） | 值/结构消费链断裂仍是主要机理族；B100 产物非法属 B90 同类（生成路径产物非法） |
| **B76**（augassign × BoolOp RHS） | `c4_08.e04_boolop_rhs`（`r += (a or b)`）、`e07_b76_deep` **MATCH** | 该形态在 augassign 定向探针下**未复现** B76，疑似已在 round3 前修复；建议 Round 8 复核 B76 台账状态 |
| **既有 loop-else 残留** | `c4_02.CL.m`/`_scratch_m4.c1` | `_find_loop_else` 的 break-only 体守卫缺口，若与 III.5 名单既有 loop 残留同机理则并入该 B 项 |

### 4.3 探针退化伪差（口径注记，不登记为破口）

本轮探针**全改用非常量条件**，未复现 `if 1:`/`while 1:` 常量折叠伪差。`c4_14` 的 `compile_error` 为**真实产物非法**（`from  import mod`），非探针退化；`c4_05.e09_comp_host` 探针设计交叠（with 宿主 + 多 for 推导式），其失败已归入 B113（经 `_scratch_m4` 最小复现确证为推导式子句丢失，与 with 无关）。

---

## §5 修复交接单（致 Task 4.2 修复工程师）

### 5.1 判据草案（只取 I.4 白名单：块末 opcode / 后继前驱集合 / 异常边 / 区域成员关系 / code object 元数据 / 指令 oparg）

| 破口 | 判据草案（白名单） |
|---|---|
| **B100** | `IMPORT_NAME` 前导 `LOAD_CONST` 的 **int argval**（level 事实，编译器写入的 oparg 结构）——回看窗口扩至 `IMPORT_NAME` 前 2–3 条指令并跨基本块取最近 int 常量；`ImportFrom` dict 必须携带 `level`，发射处按其补 `'.'*level`。禁函数名/模块名白名单 |
| **B101** | `IMPORT_NAME` 后继 `IMPORT_STAR`（块末 opcode 族事实）——命中即在模块级与 self-loop 两条路径统一产出 `ImportFrom(names=[{'name':'*'}])`。两路径共用同一判据，禁按宿主分支裁剪 |
| **B102** | handler 区域内 `CHECK_EG_MATCH`/`PREP_RERAISE_STAR` opcode 序 + 异常边集合成员关系——第 2+ 个 `except*` 手按 `is_except_star` 标记独立认领，else 臂仅由异常表无 handler 边判定；`else`/`finally` 边界由异常表成员关系封闭 |
| **B103** | 模式子块**块末 opcode**（MATCH_MAPPING/MATCH_CLASS/MATCH_KEYS/MATCH_SEQUENCE/MATCH_STAR）+ case 子块集合成员关系——每个 case 的模式子块唯一归属；guard 块判据 = 尾随条件跳转目标指向下一 case（`pattern_parser.py` 现有 `jump_target_offset` 判据扩至 mapping/class/or 分支） |
| **B104** | 链式比较块的后继集合 + 末操作数块块末 opcode——末操作数块（LOAD/COMPARE/BinOp/Call 序）必须整体归入 Compare 节点，禁常量/布尔占位；宿主无关（with/while 头同样走同判据） |
| **B105** | `NamedExpr` 消费位：STORE 前的值消费链块集合成员关系——比较条件与调用实参位均按「STORE 目标 + 值链块」整体认领，禁仅发射 STORE |
| **B106** | Call 实参序列的指令 oparg 序（PUSH/PRECALL/CALL 前操作数块序）——按指令顺序重建实参，多个 `*`/非尾 `*` 均保序，禁重排/去重 |
| **B107** | 链式赋值块的目标 STORE 序列 + 值块成员关系——多目标/解包目标全部按同值块认领，禁后续目标退 `None` |
| **B108** | try 区域 `generated_blocks` 唯一归属 + DELETE_* opcode——finally 体块不得同时归 try 体；DELETE 指令识别为 Delete 语句 |
| **B109** | 回边 entry + else 块集合成员关系（`_find_loop_else` break-only 体）——while 体末为 break 分支时，else 块与循环后块按异常/跳转目标集合封闭，禁合并为无条件 return |
| **B110** | with 区域出口块集合 + RETURN_CONST opcode——with 体已含 return 时，区域出口不再发射 RETURN_CONST None（区域出口块唯一归属） |
| **B111** | 装饰器 Call 重建块集合 + `__build_class__`/decorator 发射序——局部类方法装饰器按 Call 结构重建，禁退元组 |
| **B112** | async for/with/yield 的 GET_AWAITABLE/SEND/YIELD_VALUE opcode 序——`yield await` 保 yield 语义；async 推导式按 `is_async` code object 元数据识别（与 B96 同域） |
| **B113** | 推导式子句块的 `generators` 列表长度 + 各子句归约块集合成员关系——每个 `for` 子句块唯一归属，迭代器为列表字面量/非纯常量表达式时不得丢子句 |

### 5.2 并行派发建议（破口族不相交 ∧ 涉改文件不相交）

- **位 1（`region_ast_generator.py` 生成层）**：B100/B101（import 保真）、B104（链式比较）、B105（walrus）、B107（multi_target）、B110（with 出口）、B111（decorator）、B112（async）、B108（try/finally 生成）。文件集中、判据同族（值/结构消费链），建议串行分组。
- **位 2（`region_analyzer.py` 识别层）**：B102（except* handler 归并）、B103（match 模式解析，可并行落 `pattern_parser.py`）、B109（`_find_loop_else` 守卫）。
- **位 3（`comprehension_generator.py`）+ `code_generator.py`**：B113（多 for 子句）、B106（star_args 实参序，`code_generator.py`）、B100/B101 发射端。
- **注**：位 1 与位 2 涉改文件不相交（生成层 vs 识别层），可**并行**；B100/B101 跨 `region_ast_generator.py` 与 `code_generator.py`（位 1/位 3 交叠），须划分同一工程师避免冲突。

### 5.3 门禁与回归提醒（对 4.2 修复工程师自测）

- 自测门禁 = 本轮全部 MISMATCH 转 MATCH ∧ 负对照 `n4_01–n4_05` 全 MATCH（现 n4_05 2/3）∧ 站桩回归 6 面（§2）不变差 ∧ IV.2 门禁自检全过（IMPORT_OK/COMPILE_OK/BOM 单头/G0/G3/G4/影响面字节级抽验）。
- **新增回归基准**：`test_repros/round4/` 20 攻击探针本轮读数 = attack **262/298**、neg 39/40、compile_error 1（c4_14）；修复后不得低于本轮，已破单元以 MATCH 为目标；`c4_14` 须转 success。
- **台账同步（强制）**：B100–B113 确证后须同步 wiki 台账 §5 形式层计数（完备 128→117 / 破口 0→11，按 20 形态族三态落位；II.7 #7 要求禁不改台账而维持「完备」）。
- 触及方法 docstring 六项模板（I.7）+ C1/C2/C3 条款；落地声明「代码已落地」（I.6）；判据禁止名字白名单/start_offset 魔数/深度特判/少发射换绿。
- **优先级提醒**：B100/B101（产物非法/零能力）与 B102/B103（核心语法保真）应优先；B104/B105/B106 浅层可破，属高危。

---

## 附：本轮产物清单

- `rounds/round4/`：`REVIEW.md`（本文件）、`r4v4_attack.py`、`r4v4_station.py`、`r4v4_compare_regress.py`、`r4v4_probe_index.json`、`r4v4_probe_results.json`、`r4v4_probe_full.json`、`r4v4_regress_round2face.json`、`r4v4_regress_probe42.json`、`r4v4_full_round1face.json`、`r4v4_full_residual_a/b.json`、`r4v4_full_oldface_a/b.json`、`r4v4_quotation.json`、`r4v4_station_regress_compare.json`
- `test_repros/round4/`：`gen_probes.py` + 20 `c4_*` 攻击探针 + 5 `n4_0*` 负对照（各 `.py/.pyc/*OK.py`）+ `_scratch_m4/`（B113/B109/B110 最小复现）