# Round 2 修复报告（Task 2.2 修复工程师位 2）—— 生成层 B90 + B96

- 位 2 封闭范围（REVIEW §5.2 派发）：B90（f-string 转换+嵌套 format-spec）、B96（async 推导式误生成）；涉改文件 = `core/cfg/ast_converter.py` + `core/cfg/comprehension_generator.py`（位 2 三文件中 `code_generator.py` 零改动——修复全部落在转换层，见 §2.1 说明）。
- 树状态：HEAD = `87e59c49`；工作树仅上述两代码文件修改 + 按RV2 方法学重新生成的 OK.py 产物（`test_repros/round2/` 的 c01/m12/x09 三份，见 §3 影响面）；零 git 提交。
- 工具链：`python -c "import py_compile; py_compile.compile(f,cfile,doraise=True,optimize=0)"`（3.11.7）→ `python pycdc.py x.pyc -o xOK.py`（先 regen 后 verify）→ `python scripts/pyc_verify.py single x.pyc`。

---

## §1 根因分析（锚点 + 机制 + 违反条款）

### §1.1 B90 —— 模块根 f-string 转换+嵌套 format-spec 渲染为集合字面量（COMPILE_ERROR）

**锚点**：`core/cfg/ast_converter.py` 原 :1399 `_convert_formatted_value_full`（format_spec 转换选型）+ :1379 `_convert_joined_str_full`（片段位共用）；共因在 AST 发射路径 `core/cfg/code_generator.py:4844-4845`（`_generate_formatted_value` 对 `ASTJoinedStr` 型 format_spec 走 `_generate_joined_str` 渲染，输出带 `f` 前缀与引号的完整 f-string 字面量）。

**机制（实测确证，修正评审草案的描述）**：评审登记的机制为「丢失 FormattedValue 包装被退化为 dict/set 字面量」；实测定位为**包装未丢失、是 spec 表示选型错误**，含两层：

1. **spec 层（B90 主因）**：`_convert_formatted_value_full` 把 `format_spec`（reconstructor 产出的 JoinedStr dict，如 `>{len(str(1))}` 的规范）经 `_convert_expression` 转成 `ASTJoinedStr`。AST 发射端 `_generate_formatted_value` 对 `ASTJoinedStr` 型 spec 渲染为 `':' + f'…'`（code_generator.py:4845），在 `:` 位置出现带引号的 f-string 字面量 → 产物 `Q = {W!r:f'>{len(str(1))}'}"` 括号语义错乱不可编译。字典发射路径早有同语义修复（`_generate_format_spec_inner_from_dict`，Round5-07：「格式说明符上下文不包 f'...'」），AST 路径缺失同判据——同层双路径判据不封闭。
2. **顶层裸 FV 层（同族共因）**：单替换字段 f-string（无 BUILD_STRING，字节码仅 FORMAT_VALUE）在 reconstructor 产出**裸 FormattedValue dict**；AST 发射端对其输出 `{…}`（无 `f` 前缀），被解析为集合/字典字面量。字典路径有同语义包裹（code_generator.py:3590-3607，Round5-07 注记），AST 路径同样缺失。

**违反条款**：T3 生成路径产物非法（II.3 破口）；C2（同一 FormattedValue 语义在字典发射路径与 AST 发射路径行为不一致——「浅层（字典路径）对而深层（AST 转换路径）错」的发射层变体）；★组④ fstring_conversion 首个对抗证据（m12）。

### §1.2 B96 —— async 推导式误生成 + 内层 code object 丢失

**锚点**：`core/cfg/ast_converter.py` :917-942 表达式分发表（**无 `ComprehensionObject` 处理项**）+ :1585 `_convert_await_expr_full`（原样包 Await）+ :1268 `_convert_call_full`（func 转换得 None）；上游生产点 = `core/cfg/region_ast_generator.py` B31 门 `_b31_await_chain_gate`（:10011 起的合并流对「编译器为 async 推导式补发的 GET_AWAITABLE」剥除判据 `_prev_call ∧ _inline_fn_awaited` 失配——iterable 本身是 CALL（`_AIT()`）时 `_inline_fn_awaited` 被首次 CALL 消耗、真实推导式 CALL 处为 False，剥除不命中）。

**机制（实测确证）**：`acc = [x async for x in _AIT()]` 在 async 函数内编译为 `MAKE_FUNCTION <listcomp>; CALL _AIT(); GET_AITER; CALL(推导式, aiter); GET_AWAITABLE; SEND 轮询; STORE_FAST acc`。region 装配层 B31 await 链门先于推导式路径（region_ast_generator.py:50050 门 vs :51962 `try_generate_comprehension_assign`）独占整条挂起链，合并流重建时 GET_AITER 在通用栈机中无处理器（ast_generator_v2 栈机仅 GET_ITER 包 Iter），`ComprehensionObject + Iter` 合并分支（:1570）失配，泄漏为 `Await(value=Call(func=ComprehensionObject(<listcomp>), args=[Call(_AIT())], is_decorator=True))` dict。该 dict 到达本位转换层：分发表无 `ComprehensionObject` 项 → 警告「Unknown expression type: ComprehensionObject」→ func=None 渲染出 `acc = await None(_AIT())`；内层 `<listcomp>` code object 从未被解析 → 该单元 Missing bytecode。

**违反条款**：C2（转换层对装配层既有节点类型 `ComprehensionObject` 无识别——跨层契约缺失）；T3 生成路径（II.3）；评审 §5.1 判据草案「内层推导式 code object 必须产出对应生成器单元」未满足。

---

## §2 修复方案（封闭语义 + I.4 判据白名单逐项核对）

### §2.1 B90：转换层 spec 表示选型 + 裸 FV 规范包裹（ast_converter.py）

- **`_render_format_spec_source`（新增）**：format_spec 三态封闭——str 直通 / `Constant` str 字面规范直出 / `JoinedStr` 动态规范经**既有发射器** `code_generator._generate_format_spec_inner_from_dict`（Round5-07 语义，单一事实源）渲染为规范上下文源码（字面片段转义引号/换行、不转义花括号；FormattedValue 片段 `{expr[:conv][:spec]}`；不添加 f 前缀与引号）；非三态返回 None → 调用方回退既有 `_convert_expression` 路径（行为同 [B90] 前，不静默吞形态）。
- **`_convert_formatted_value_full`（修改）**：format_spec 以规范上下文源码 str 保留，不再转 ASTJoinedStr。
- **`_convert_formatted_value_expr`（新增，分发表项）**：经分发入口的 FormattedValue 包裹为 `ASTJoinedStr(values=[FV])`——CPython AST 对单字段 f-string 的规范形态；`_convert_joined_str_full` 片段位仍直调内层转换（无双包裹）。
- **为何不修 code_generator.py:4845**：位 2 受限文件不含 code_generator.py；转换层选型（spec 源码化 + 顶层包裹）使 AST 路径与字典路径共用同一发射语义，属同一封闭判据在转换层的落地，非个案补丁——对**所有** FormattedValue 形态（任意宿主/任意深度/动态或字面 spec）一致生效。

**I.4 白名单核对**：判据 = 节点类型字段（`type` ∈ {str/Constant str/JoinedStr/FormattedValue}，转换层字典结构事实）+ 编译器指令语义（FORMAT_VALUE 仅 f-string 语境）。黑名单五项零命中：无文件/函数名白名单、无 start_offset 阈值、无跨层 `entry in blocks` 反查、无 self 新增跨方法状态（全部方法无状态、局部变量构成）、无少发射/深度上限。

### §2.2 B96：转换层补 ComprehensionObject 识别 + 编译器 await 协议剥除（ast_converter.py + comprehension_generator.py）

- **`parse_comprehension_code_object`（comprehension_generator.py 新增模块级函数）**：对推导式 code object 独立建 CFG 并走既有 `parse_comprehension_inner` 全管线（多 for/async 混合 clause、单 clause、async 头识别均复用既有判据）；is_async 由内层 GET_AITER/GET_ANEXT/END_ASYNC_FOR 协议指令元数据判定（评审 §5.1 草案 B96 判据落地）；每次调用局部构造解析器对，零跨方法状态。
- **`_convert_comprehension_object_call`（ast_converter.py 新增）**：识别 `Call(func=ComprehensionObject(code), args=[iter])` 泄漏形态 → 经上述函数解析内层 code object → `_convert_expression` 落为 ASTListComp/ASTSetComp/ASTDictComp/ASTGenExpr。判据：`co_name ∈ {<listcomp>,<dictcomp>,<setcomp>,<genexpr>}`（**编译器合成名事实**——与 region_analyzer `_const_code_is_async_comprehension`、comprehension_generator `generate_comprehension_function` 同一谓词，Python 语法禁止用户取得尖括号名，非用户标识符白名单）∧ 恰一位置实参 ∧ 无关键字实参；任一不满足或解析失败返回 None 回退通用路径。
- **`_convert_await_expr_full`（修改）**：value 为上述泄漏 Call 且内层 code object `co_flags & 0x80`（COROUTINE 位，**I.4 白名单「code object 元数据」**——async 推导式的内层 code object 编译为协程函数，实测 x09 `<listcomp>` co_flags=0x93，同步推导式 0x13）时，剥除编译器为推导式协程启动补发的 Await+Call 包装，返回推导式本体；同步推导式（无该位）保留 ASTAwaitable 包裹（用户级 await 语义，重编译再生 GET_AWAITABLE）——C3 显式排除，无静默剥除。
- **`_convert_call_full`（修改）**：func 位泄漏形态同样还原（覆盖 B31 门剥除成功（无 Await 包裹）与未剥除两种变体）。

**I.4 白名单核对**：判据 = co_name 编译器合成名 + co_flags 元数据 + 实参数量结构。黑名单五项零命中（同 §2.1 口径）；「以少发射换全绿」不成立——还原分支只把 func=None 的必然垃圾 ASTCall 换为真实推导式节点，其余路径逐字节保持。

---

## §3 自测读数表（门禁 1–5 逐项 before/after）

### 门禁 1：破口探针

| 探针 | before | after | 判定 |
|---|---|---|---|
| m12 产物 | `Q = {W!r:f'>{len(str(1))}'}"` COMPILE_ERROR（status=compile_error units=0/0） | **COMPILE_OK**；`Q = f'{W!r:>{len(str(1))}}'` 与原源逐字符一致；f-string 指令段（LOAD_NAME W…FORMAT_VALUE 6…STORE_NAME Q）与原 pyc **逐指令等价**（实测 opcode 流比对）；units=2/3 | f-string 部分封闭 ✓ |
| m12 `<module>` 单元 | Different bytecode（B89 裸 `_F`/`_A < _B` 泄漏，位 3） | 仍 Different bytecode——实测残余差异**恰为 B89 两条泄漏语句**（recomp 多出 `LOAD_NAME,POP_TOP` ×1 与 `LOAD_NAME,LOAD_NAME,COMPARE_OP,POP_TOP` ×1），非本位改动 | 位 3 未封闭，如实记录 ✓ |
| x09 units | 7/10（AHost.a1=B95、AHost.a2=B96、`<listcomp>` Missing bytecode + 警告 Unknown expression type: ComprehensionObject） | **8/10**：`<listcomp>` 单元恢复且逐指令 MATCH（实测 dis 全等）；a2 产出 `acc = [x async for x in _AIT()]`（原 `acc = await None(_AIT())`），警告消除 | B96 登记机理封闭 ✓ |
| x09 AHost.a2 单元 | Different bytecode | 仍 Different bytecode——实测残余差异**仅为尾段**：原 `LOAD_FAST i; SWAP 2; POP_TOP; RETURN_VALUE`（return i，async-for 迭代器栈清理）vs recomp `LOAD_FAST i; POP_TOP; LOAD_CONST None; RETURN_VALUE`。该 SWAP 尾段在 region_ast_generator `_b31_await_chain_gate` 合并流 → `_build_statements_from_instructions`（POP_TOP/RETURN_VALUE 语句边界，:32126-32306 区）重建，**不在位 2 涉改文件内**（B31 门又先于 :51962 推导式路径独占链，推导式路径自身亦无 SWAP 尾段判据） | 位 3 域残留，如实说明（见 §6） |
| c01（顺带） | 4/5，`J = f"v={A!r:'>4'}"`（字面 spec 带引号 → 单元字节差） | 4/5 持平（B85 位 3 仍在），但 J 段修复为 `f'v={A!r:>4}'` 且**实测逐指令等价**（LOAD_CONST '>4'…BUILD_STRING…STORE_NAME J 全等） | 顺带收益 ✓ |
| round2 负对照 nm01/nm02/nc01/nc02/nx01 | MATCH | 全 MATCH（实测） | 保持 ✓ |
| x07 except* 面 | 4/4 MATCH | MATCH | 保持 ✓ |

### 门禁 2：不越界面保持

- `git status --porcelain` 代码文件仅 `core/cfg/ast_converter.py`、`core/cfg/comprehension_generator.py`；region_ast_generator.py / region_analyzer.py / code_generator.py 零改动。
- 全部 42 探针 + 45 站桩文件 regen 后，**仅 3 份 OK.py 字节变化**（m12/x09=本位修复、c01=顺带收益），其余 84 份逐字节不变——影响面字节级证据。
- m12 其余单元（B89）、x09 AHost.a1（B95）读数与失败单元逐一相同（位 3 未受扰动）。

### 门禁 3：站桩回归面（先 regen 后 verify，对照 rounds/round2/r2_regress_replay.json）

| 面 | 基线 | 本轮 | 判定 |
|---|---|---|---|
| r10_04/r10_06/r10_14/r10_15/r10_16/r10_21 | 全 MATCH | 全 MATCH | 持平 ✓ |
| rv10_31/rv10_32/rv10_33 | 全 MATCH | 全 MATCH | 持平 ✓ |
| r7_03 / r7_07 | 7/7、7/7 | 全 MATCH | 持平 ✓ |
| r7_08 | 7/8（t_host_match_case，B77 存量） | 7/8，失败单元同一 | 持平 ✓ |
| rv8_01 / r8_06 | 7/7、10/10 | 全 MATCH | 持平 ✓ |
| rv8_02 | 6/7（tryfin_then_more，B63 存量） | 6/7，失败单元同一 | 持平 ✓ |
| n6_01/n7_01/n7_02/n8_01/n8_02/n9_01/n9_02/n10_01..04/rv9_03 | 全 MATCH | 全 MATCH | 持平 ✓ |
| v_b46/v_b71/v_b73/v_b74/v_b75 | 1/4、3/4、2/3、3/4、1/3 | 同读数，失败单元逐一相同（n_for_body_nest/v_nest_fin_continue/v_imp_cond_fin/n_true_guard/n_fin_noseg） | 持平 ✓ |
| v_b50/v_b65/v_b76 | 4/4、3/3、4/4 | 全 MATCH | 持平 ✓ |
| probes_rvC rvC_v1/v3/v4 | MATCH | MATCH | 持平 ✓ |
| probes_rvC rvC_v2 | 1/2 FAIL（drain，B83 存量） | 1/2 FAIL，失败单元同一 | 持平 ✓ |
| quotation.pyc（附加加验） | 152/153（change_his_to_forward） | 152/153，失败单元同一，OK.py 逐字节不变 | 持平 ✓ |

### 门禁 4：34 小测试集抽验 6 文件

| 文件 | 基线 | 本轮 | 失败单元 |
|---|---|---|---|
| email_utils | 3/4 | 3/4 | send_email ✓ |
| cgroup_utils | 7/8 | 7/8 | set_cgroup_config ✓ |
| executor | 9/10 | 9/10 | Executor.check_before_trading ✓ |
| strategy_universe | 10/11 | 10/11 | StrategyUniverse._on_clear_de_listed ✓ |
| trading_dates_mixin | 13/14 | 13/14 | TradingDatesMixin.trading_dates_reload ✓ |
| realtime_event_source | 12/13 | 12/13 | RealtimeEventSource.clock_worker ✓ |

### 门禁 5：IV.2 自检

- BOM：两文件首 3 字节非 efbbbf（原无 BOM），全文 BOM 计数 = 0（**保持原状，未新增**）。
- `import core.cfg.ast_converter` / `import core.cfg.comprehension_generator`：OK。
- 新增代码 grep `print(|breakpoint(|import pdb|pdb.set_trace`：0 命中；新增方法名 grep `_fix_|_patch_|_fallback_|_hack_|_workaround_|_temp_`：0 命中。
- 判据合规：无用户名白名单（co_name 四值为编译器合成名事实，与既有 `_const_code_is_async_comprehension` 同谓词）、无 start_offset 魔数、无深度/计数上限、无 self 新增跨方法状态、无跨层 `entry in blocks` 反查。
- 影响面：见门禁 2（仅 3 份 OK.py 变化，均为目标/顺带单元）。

---

## §4 触及方法 docstring 更新说明（I.7 六项模板 + C1/C2/C3）

| 方法 | 文件 | 变更 | 六项 + C 条款 |
|---|---|---|---|
| `_convert_formatted_value_full` | ast_converter.py | format_spec 源码化 + 注释 | ①算法依据 ②识别条件 ③归约方式 ④AST 映射 ⑤反编译流程位置 ⑥共用关系；C1/C2/C3 声明与代码一致 |
| `_convert_formatted_value_expr`（新增） | ast_converter.py | 分发入口包裹 JoinedStr | 六项 + C1/C2/C3 齐全 |
| `_render_format_spec_source`（新增） | ast_converter.py | spec 三态渲染 | 六项 + C1/C2/C3 齐全 |
| `_convert_comprehension_object_call`（新增） | ast_converter.py | 泄漏形态还原 | 六项 + C1/C2/C3 齐全 |
| `_convert_call_full` | ast_converter.py | 顶部还原分支 + docstring | 六项 + C1/C2/C3 齐全 |
| `_convert_await_expr_full` | ast_converter.py | async 协议剥除 + docstring | 六项 + C1/C2/C3 齐全 |
| `parse_comprehension_code_object`（新增） | comprehension_generator.py | 模块级解析入口 | 六项（识别条件/归约方式/AST 映射/反编译流程）+ C1/C2/C3 齐全 |
| `_convert_joined_str_full` | ast_converter.py | **零代码改动**（片段位直调内层转换的既有行为保持，裸 FV 语义不变） | — |

## §5 落地声明（I.6）

**代码已落地**。落地标记：`core/cfg/ast_converter.py` 内 `_convert_formatted_value_expr` / `_render_format_spec_source` / `_convert_comprehension_object_call` 三方法树中实存且经分发表（`'FormattedValue': self._convert_formatted_value_expr`）与调用点（`_convert_call_full` / `_convert_await_expr_full` 顶部）接线；`core/cfg/comprehension_generator.py` 内 `parse_comprehension_code_object` 被上述转换层调用（grep 可复核）。m12 COMPILE_OK + f-string 段逐指令等价、x09 8/10（`<listcomp>` 单元恢复）为落地实证。

## §6 遗留观察项（如实说明）

1. **x09 AHost.a2 单元残留（无法在本位封闭）**：`return i`（SWAP 2 + POP_TOP + RETURN_VALUE，async-for 迭代器栈清理的块内延迟返回）被重建为裸 `i` + `return None`。机制与锚点：region_ast_generator.py `_b31_await_chain_gate`（:10011 起）合并流（a) 剥除判据 `_inline_fn_awaited` 被 iterable 的首次 CALL 误消耗（:9995-10003）；(b) `_build_statements_from_instructions`（:31878-32306）POP_TOP 语句边界把 `[LOAD_FAST i, SWAP 2]` 重建为 Expr、RETURN_VALUE 落为 Return(None)，无 SWAP 尾段判据）。两处均在位 3 涉改文件（region_ast_generator.py），B31 门又先于 :51962 推导式路径独占挂起链——位 2 两文件无守卫触点。**本位已把该单元从「推导式整体错构 + 内层 code object 丢失」收敛为单一 SWAP 尾段差异**，移交位 3 按其既有 `_try_deferred_return_in_loop` 判据族封闭。
2. **m12 `<module>` 单元残留**：B89 裸语句泄漏（`_F`、`_A < _B`）为位 3 域（region_ast_generator 模块根序列发射），本位未触碰；f-string 位（B90）已封闭。
3. **c01 CAssign 单元**：f-string 位已逐指令等价，单元仍因 B85（链式赋值丢第二目标，位 3）失败——读数持平。
4. **观察**：AST 发射路径 f-string 形态簇（`f'{x:.2f}'` 字面 spec、`f'{W!r}'`、`f'{x}'` 裸 FV）经本次修复全部转为可编译且逐指令等价（roundtrip 实测）；评审草案 B90「FormattedValue(format_spec=JoinedStr) 结构保真」按实测根因修正为「spec 规范上下文源码化 + 顶层规范包裹」——保真的对象是重编译指令流与 CPython AST 规范形态（JoinedStr([FV])），而非保留发射端无法正确渲染的 ASTJoinedStr spec 中间表示。
5. **临时脚本**：位 2 调试脚本均即时清理，无残留；`rounds/round2/fix2_replay_{a,b,c}.json`、`fix2_probe_replay_{a,b,c}.json` 为本轮读数产物（复用评审侧 r2_regen_verify.py 驱动）。round2 目录内 `tmp_*_b94.py` 与 `fixp3/` 为并行位产物，未触碰。
