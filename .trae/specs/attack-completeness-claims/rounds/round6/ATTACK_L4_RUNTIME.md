# ATTACK_L4_RUNTIME —— L4 实现层攻击：语料外真实项目 / 执行级语义差分 / 规模深度边界

> 规范：`attack-completeness-claims` Task 6（spec.md §攻击分层设计 L4 行；tasks.md 6.1–6.4）。
> 被攻击对象：「语料（402 + small34 + quotation）内全绿 ⇒ 完备」这条主张的**外延**：
> 语料外真实代码上，反编译产物是否**语义正确**、是否**可编译**、在**规模/深度**边界上是否退化。
>
> **纪律**（本轮自加，因 Task 4 已证判据盲区 27.92%）：
> * §2 的每个失败样本都做**源码级核对**（读源码 + 指令级差分），**不以判据红/绿代替语义结论**；
> * §3 的执行级差分以**原 pyc**（不是磁盘源码）为基准，且比对**返回值 + 类型 + 副作用序 + 异常类型**；
> * 「判据红」与「判据绿」都**单独报告**，不互相代替；
> * 所有读数可复算：脚本在 `rounds/round6/tools/`，原始记录在 `rounds/round6/logs/`。
>
> **本轮只测不修**：`core/cfg/**`、`scripts/pyc_verify.py`、`tests/**`、`wiki/**`、`rules.md`、
> 其它规范目录**零改动**；产出全部落在 `rounds/round6/**`。
> 判据调用形式（全轮统一）：`python -X utf8 scripts/pyc_verify.py single <pyc> --source <产物>`。
> 解释器：CPython **3.11.7**（`D:\Python\python.exe`）。

---

## §0 逐项判定（AT-4N）

| AT | 攻击项 | 判定 | 一句话证据 |
|---|---|---|---|
| **AT-41** | 语料外真实 pyc 的反编译**判据绿率**是否与语料内一致 | **击穿** | 46 个语料外真实 pyc：判据 **success 4 / failure 35 / compile_error 7**，单元 **2765/3079 = 89.80%**；语料内基线是 6617/6617 = 100%（`baseline/readings.md:29`）⇒ **语料外绿率 4/46 = 8.70%**，与语料内差 **91.3 个百分点** |
| **AT-42** | 语料外产物的**可编译性** | **击穿** | **7/46 = 15.22%** 的产物**无法编译**（`SyntaxError`）；根因两类：模块 docstring 被还原为 `__doc__ = ...` 赋值 ⇒ 其后 `from __future__ import` 非法（5 例）；其它语法破坏 2 例（`**dict` → `{*d: ...}`；f-string 内嵌三引号 ⇒ 字符串未闭合） |
| **AT-43** | 语料外产物的**语义正确性**（源码级核对） | **击穿** | 35 个判红样本逐个做指令级差分：**178 个失败单元**，根因类分布 = **C2 语句/常量级差异 32 样本、C6 注解元组丢失 12、C1 局部变量写入丢失/改写 7、C10 try/except/else 塌陷 7、C9 切片丢失 3、C5 await 丢失 3、C4 返回值丢失 3、C3 极性反转 1、C11 等价改写 4、C14 code object 无法配对 10**；已定位到具体源码↔产物差异（如 `difflib.__chain_b` 的 `b2j = {}` 被写成 `self.b2j = {}` ⇒ 运行期 `NameError`） |
| **AT-44** | **执行级语义差分**（≥8 可安全执行样例） | **击穿** | **24 个样例 / 56 个探针**：**14 处差异**，分布在 **9 个样例**；差异形态包括 `NameError`（`b2j`）、`UnboundLocalError`（`start`/`char`）、静默丢校验（`eq must be true if order is true`）、**JSON 输出损坏**（缺 `{`/`}`/`,`）、`AttributeError`（`URL.port`）、`findall` 取到错误元素 |
| **AT-45** | 深度边界：**≥164 层嵌套** | **未击穿（语义层）但结构层击穿** | 164 层**表达式/调用/下标链**：pycdc 正常（verify success、AST 深度 170→170、执行等价）；但**单子链嵌套 if 被塌陷为 and 链**（90 层 ⇒ 深度 95→7、语句 94→5，字节码等价、语义等价但**源码结构丢失**）⇒ 深度保真度不可测（见 §4 / B209） |
| **AT-46** | 规模边界：**≥500 语句函数** | **未击穿（正确性）/ 击穿（可用性）** | 520/1000/2000/3000/4000 条语句全部 **verify success + 执行等价**；但耗时 **4.9 / 8.8–13.2 / 19.9–68.5 / 69.1 / 89.8 s**（超线性，4000 条已近 90 s）⇒ 大函数进不了 300 s 门禁（B212） |
| **AT-47** | 规模边界：**巨型表达式** | **未击穿** | 5000 项布尔链、20000 元素列表字面量：pycdc 0.96–1.25 s、verify success、执行等价；5000 项加法链/字符串拼接**在 CPython 编译期即 RecursionError**（源码侧边界，非 pycdc 边界） |
| **AT-48** | 异常 / async / 生成器 / 闭包路径 | **击穿** | async：`asyncio.streams.StreamReader.read` 的 `await` 与 `slice` 同时丢失（AST 指纹 slice 2→0、await 2→0）；生成器：`json.encoder._make_iterencode` 的 `yield` 30→25、continue 1→15；异常：`dataclasses` 的 `raise ValueError` 校验被删、`csv` 的 `try/except/else` 的 **else 分支丢失** ⇒ 异常路径语义反转 |
| **AT-49** | **B142 / B143 在语料外是否复现** | **击穿（复现成立）** | AST 全量扫描 **29377 个语料外真实文件**：B142 形态 **41 个文件**、B143 形态 **3 个文件**；抽样复现：B142 **3/6**（`socket.py`、`asyncio/base_events.py`、`anyio/_core/_sockets.py`）、B143 **2/3**（语料外仅 3 个文件命中该形态，**全部抽样**：`anyio/to_interpreter.py`、`click/_termui_impl.py`）⇒ **两稀窝不是语料内孤例** |
| **AT-50** | 语料外**语言特征覆盖**（类型注解/f-string/dataclass/生成器/async/装饰器链/PEP604/except*） | **部分未击穿 / 一项不可证伪** | AST 自动判定覆盖：注解 24、f-string 35、生成器 21、async 12、装饰器链 7、PEP604 24、dataclass 6、match 1；**`except*`（PEP 654）真实语料命中 = 0**（stdlib 795 文件 + site-packages 14237 文件 AST 全扫，`TryStar` 节点数 **0**；唯一文本命中是 `ast.py` 里的字符串字面量）⇒ 该特征**无真实样本可覆盖**（B213），只能由合成补样测量：pycdc 对 `except*` **形态正确**（产物保留 `except* ValueError as eg:`，verify success 4/4，执行等价） |

**本轮一句话结论**：**语料外真实代码上「完备」不成立**——判据绿率从语料内 100% 跌到 **8.70%**，
产物不可编译率 **15.22%**，执行级语义差异 **14/56 探针**；
其中**判红并不等于语义错**（21 个判红样例里 12 个在探针面上语义相同），
**判绿也不等于语义对**（Task 4 已证的值/槽位盲区在本轮语料外同样适用）。

---

## §1 攻击项清单表

| AT | 名称 | 目标 | 可证伪条件 | 实际结果 | 判定 |
|---|---|---|---|---|---|
| AT-41 | 语料外判据绿率 | `scripts/pyc_verify.py` 判定面 | 语料外真实 pyc 判据 success 率与语料内（100%）相当 | 4/46 = 8.70%，单元 2765/3079 | 击穿 |
| AT-42 | 语料外可编译性 | 产物语法 | 全部产物可编译 | 7/46 不可编译（2 类根因） | 击穿 |
| AT-43 | 语料外语义正确性 | `core/cfg/**` 发射规则 | 源码↔产物语义一致 | 32/35 判红样本有结构性差异 | 击穿 |
| AT-44 | 执行级语义差分 | 产物运行时行为 | 同输入序列下返回值/副作用/异常一致 | 14/56 探针差异 | 击穿 |
| AT-45 | 嵌套深度边界 | 区域嵌套表达力 | ≥164 层结构保真 | 表达式/调用/下标链保真；嵌套 if 塌陷 | 未击穿（语义）/ 击穿（结构） |
| AT-46 | 函数语句数边界 | 大函数处理 | ≥500 语句可处理 | 4000 条正确但 89.8 s | 未击穿（正确性）/ 击穿（可用性） |
| AT-47 | 巨型表达式边界 | 超长表达式 | 可处理 | 5000/20000 项正常 | 未击穿 |
| AT-48 | 异常/async/生成器/闭包 | 四类路径 | 路径语义保真 | await/yield/else 分支丢失 | 击穿 |
| AT-49 | B142/B143 语料外复现 | 稀窝性质 | 语料外不可复现 | B142 3/6、B143 2/6 复现 | 击穿（复现成立） |
| AT-50 | 特征覆盖（真实语料） | 语料外语料构成 | 八类特征均有真实样本 | 七类有；`except*` 真实命中 0 | 部分未击穿 / 一项不可证伪 |

---

## §2 语料外差分结果

### 2.1 语料外口径与样本构成（来源路径逐条写清）

- **语料内** = 仓库内 `site-packages/**` 的 402（`shards/shard0..7.json`）+ 34（`failing_index.json`）+ 1（`fly/data/quotation.pyc`）。
- **语料外** = (1) 系统 CPython stdlib `D:\Python\Lib`；(2) 系统 site-packages `D:\Python\Lib\site-packages`（第三方真包）；
  (3) 仓库自有模块 `core/**`、`parsers/**`、`scripts/**`、`tools/**`（**不在 `test_repros`、不在 402 语料**）。
- 样本 **46 个真实 pyc**（≥20 的要求满足），逐条来源见 `logs/l4_offcorpus_table.md` 与 `offcorpus/samples.json`。
- **源码 ≡ 原件 pyc 严格核对**（`tools/l4_src_pycheck.py`：比 `co_code` + `co_consts` + `co_names`）：**46/46 完全一致**
  ⇒ §2 的「源码语义」基准**可信**（首轮曾有 3 个 anyio 样本报不一致，根因是 `__pycache__` 里同时存在
  **pytest 断言重写版** pyc（`_fileio.cpython-311-pytest-9.0.3.pyc`）与干净版；改用干净版后不一致消失）。
- 特征标签**由源码 AST 自动判定**（`tools/l4_build_samples.py::detect_features`），不手写。

### 2.2 判据读数总表（46 个语料外真实 pyc）

| 口径 | 读数 |
|---|---|
| 判据 `status` | **success 4 / failure 35 / compile_error 7** |
| 文件级绿率 | **4/46 = 8.70%**（语料内基线 100%，`baseline/readings.md:29`） |
| 单元级绿率 | **2765/3079 = 89.80%**（语料内 6617/6617 = 100%） |
| 源码 ≡ pyc（严格） | **46/46** |
| 执行级差分样例 | 24（其中 9 个样例有差异） |

逐样本表（来源路径、特征、判据、单元、根因类、指令级差异摘录）见
**`logs/l4_failure_digest.md`**（机器生成，含每个失败单元的指令级差分明细）。

### 2.3 特征覆盖（AST 自动判定，46 样本）

| 特征 | 覆盖样本数 | 特征 | 覆盖样本数 |
|---|---|---|---|
| f-string | 35 | 注解 | 24 |
| PEP604（`X \| Y`） | 24 | 生成器 | 21 |
| async | 12 | 装饰器链 | 7 |
| dataclass | 6 | match | 1 |
| **except\***（PEP 654） | **0（真实语料）** | 合成补样 | 1（形态正确） |

> `except*` 缺口的事实基础：`D:\Python\Lib`（795 个 .py）与 `D:\Python\Lib\site-packages`（14237 个 .py）
> 全量 AST 扫描，`ast.TryStar` 节点数 = **0**；文本命中 `except*` 的 5+10 个文件经 AST 复核**全部是字符串字面量/散文**
> （例：`ast.py` 的 `self.fill("except*" if ...)`）⇒ **本机不存在真实 `except*` 语句**（B213）。

### 2.4 失败样本逐个的「源语义 vs 产物语义」差异（读源码核对，非只凭判据）

下表每行都给出：**源位置**、**产物位置**、**具体语义差异**、**最小复现**。

| # | 样本 | 源 → 产物 | 语义差异（读源码/指令级核对） | 最小复现 |
|---|---|---|---|---|
| 1 | `stdlib_difflib` | `D:\Python\Lib\difflib.py` → `offcorpus/stdlib_difflibOK.py` | 源 `SequenceMatcher.__chain_b` 里 `b2j = {}`（**局部变量**）；产物写成 `self.b2j = {}`（**属性赋值**），随后 `b2j.setdefault(...)` 变成**未定义名查找** ⇒ 运行期 `NameError: name 'b2j' is not defined`。指令级差分：`STORE_FAST b2j` 被替换为 `STORE_ATTR self.b2j`；同类命中 `get_matching_blocks`(`la`)、`get_opcodes`(`answer`)、`find_longest_match`(`besti/bestj` 整条赋值丢失) | `repro/min_difflib2.py`（**由真实 difflib.py 2064 行缩减到 779 行**，删 17 个顶层块）：源 `[Match(a=1,b=0,size=3), Match(a=4,b=4,size=0)]` ／ 产物 `EXC NameError name 'b2j' is not defined`；判据 `failure`。**（缩减器首轮用 `ratio()` 作探针时过度缩减、源侧自坏，已弃用；改为 `get_matching_blocks()` 后缩减稳定。）** |
| 2 | `stdlib_csv` | `D:\Python\Lib\csv.py` → `offcorpus/stdlib_csvOK.py` | 源 `Sniffer.has_header` 的投票循环用 `try/except/else`（`else: hasHeader -= 1`）；产物**丢掉 else 分支**，`hasHeader -= 1` 变成**无条件执行** ⇒ 类型转换失败时「+1 再 -1」净 0，**表头判定语义反转**；`sniff()` 另现 `UnboundLocalError: start` | `repro/min_csv.py`（真实 csv.py 453→377 行）：源 `True` ／ 产物 `EXC UnboundLocalError: start`；判据 `failure` |
| 3 | `stdlib_dataclasses` | `D:\Python\Lib\dataclasses.py` → `offcorpus/stdlib_dataclassesOK.py` | 源 `_process_class` 有 `raise ValueError('eq must be true if order is true')` 前置校验；产物**整块校验被删**（指令级差分删除 `LOAD_CONST 'eq must be true if order is true'` + `RAISE_VARARGS`）⇒ 非法入参被静默接受；`_add_slots` 另把 `__slots__` 写成 `1`（`STORE_SUBSCR`）⇒ `slots=True` 抛 `TypeError` | 执行级探针（`logs/l4_semdiff.json`）：源 `ValueError: eq must be true if order is true` ／ 产物 `NO-ERROR`；`slots=True`：源 `('a',)` ／ 产物 `TypeError: 'int' object is not iterable` |
| 4 | `stdlib_json_encoder` | `D:\Python\Lib\json\encoder.py` → `offcorpus/stdlib_json_encoderOK.py` | 源 `JSONEncoder.iterencode` 用 `yield '{'` / `yield '}'` / `yield ','` 分隔；产物**分隔符字面量丢失** ⇒ `JSONEncoder(sort_keys=True, indent=2).encode({'b':1,'a':2})` 输出 `'\n  "a"2,\n  "b"1\n'`——**不是合法 JSON** | 执行级探针：源 `'{\n  "a": 2,\n  "b": 1\n}'` ／ 产物 `'\n  "a"2,\n  "b"1\n'` |
| 5 | `stdlib_typing` | `D:\Python\Lib\typing.py` → `offcorpus/stdlib_typingOK.py` | 源 `get_args` 返回 **tuple**；产物返回 **list**（`[<class 'int'>], <class 'str'>`）⇒ 类型语义漂移 | 执行级探针（类型敏感的 repr 比对） |
| 6 | `stdlib_xml_ElementPath` | `D:\Python\Lib\xml\etree\ElementPath.py` → `offcorpus/stdlib_xml_ElementPathOK.py` | 源 `findall(el, './/b')` 返回 2 个 `<b>` 元素；产物返回 **1 个 `<root>`** ⇒ 路径匹配语义错误 | 执行级探针：源 `[<Element 'b'>, <Element 'b'>]` ／ 产物 `[<Element 'root'>]` |
| 7 | `stdlib_tomllib_parser` | `D:\Python\Lib\tomllib\_parser.py` → `offcorpus/stdlib_tomllib_parserOK.py` | 源 `loads('a = 1')` 正常；产物 `UnboundLocalError: cannot access local variable 'char'` ⇒ **控制流塌陷**（条件赋值路径丢失） | 执行级探针：源 `{'a': 1, 'b': 'x'}` ／ 产物 `UnboundLocalError: char` |
| 8 | `stdlib_re__parser` | `D:\Python\Lib\re\_parser.py` → `offcorpus/stdlib_re__parserOK.py` | 源 `parse('(?P<x>a)\|b', 0)` 可解析；产物抛 `re.error: missing >, unterminated name at position 5` ⇒ **正则解析器自身被反编译坏** | 执行级探针（探针自身在源侧有瑕疵：`.groupindex` 不存在于 `SubPattern`；**以产品侧更早的 `re.error` 为证据**） |
| 9 | `sp_httpcore_models` | `D:\Python\Lib\site-packages\httpcore\_models.py` → `offcorpus/sp_httpcore_modelsOK.py` | 源 `URL.__init__` 赋 `self.port`（类属性存在）；产物**类成员/属性缺失** ⇒ `AttributeError: 'URL' object has no attribute 'port'` | 执行级探针：源 `URL(scheme=b'http', host=b'example.com', port=None, target=b'/x')` ／ 产物 `AttributeError` |
| 10 | `repo_core_cfg_builder` | `F:\Downloads\pythoncdc-main\core\cfg\cfg_builder.py` → `offcorpus/repo_core_cfg_builderOK.py` | ① `ControlFlowGraph.to_dict`：源 `return data`（`Return`）⇒ 产物 `Expr`（**恒返回 None**）；② `CFGBuilder.build`：`LOAD_GLOBAL ControlFlowGraph … CALL 1` 整段被删 ⇒ **CFG 对象根本没构造**；③ `_build_basic_blocks`：`JUMP_IF_TRUE_OR_POP` ×2 → `JUMP_IF_FALSE_OR_POP` ×2 ⇒ **判定极性反转**；④ `_parse_instructions`：`isinstance(_argval, tuple)` 检查被删 | 逐条见 `logs/l4_failure_digest.md`（`repo_core_cfg_builder` 节）；判据 `failure`（10 个失败单元） |
| 11 | `stdlib_asyncio_streams` | `D:\Python\Lib\asyncio\streams.py` → `offcorpus/stdlib_asyncio_streamsOK.py` | `StreamReader.read`：源 2 处切片 + 2 处 `await`；产物 **slice 0 处、await 0 处**，`del` 也丢失 ⇒ 读取语义改变 | 指令级差分（`logs/l4_source_divergence.md` `stdlib_asyncio_streams` 节） |
| 12 | `stdlib_asyncio_base_events` | `D:\Python\Lib\asyncio\base_events.py` → `offcorpus/stdlib_asyncio_base_eventsOK.py` | 20 个失败单元；含 `await` 丢失（`shutdown_asyncgens` await 1→0、comprehension 1→0）、`boolop` 丢失（`wait_closed` 1→0）、`return` 计数漂移 | 指令级差分（`logs/l4_failure_digest.md`） |
| 13–35 | 其余 23 个判红样本 | 见 `logs/l4_failure_digest.md` | 每个样本都给出：**失败单元名 + 指令数（原→产物）+ 指令级差分摘录 + 根因类** | 同上（机器生成，可逐条复算） |
| 43–46 | 4 个判绿样本 | `core/config.py`、`core/object_pool.py`、`parsers/context_manager.py`、`sympy/.../qexpr.py` | 判据绿；其中 3 个已做执行级差分 ⇒ **探针面全部一致**（无「判绿但语义错」）；`sp_sympy_qexpr` 未做执行级差分（**未核实项**） | `logs/l4_semdiff.json` |

#### 2.5 7 个 `compile_error` 样本（产物不可编译）逐个根因

| 样本 | 来源 | 产物错误（行号见产物） | 根因 |
|---|---|---|---|
| `repo_scripts_verify` | `F:\Downloads\pythoncdc-main\scripts\pyc_verify.py` | L27 `SyntaxError: from __future__ imports must occur at the beginning of the file` | 模块 docstring 被还原为 **`__doc__ = "..."` 赋值语句**（不是裸字符串）⇒ 其后的 `from __future__ import annotations` 非法 |
| `sp_packaging_specifiers` | `D:\Python\Lib\site-packages\packaging\specifiers.py` | L10 同上 | 同上 |
| `sp_packaging_version` | `D:\Python\Lib\site-packages\packaging\version.py` | L9 同上 | 同上 |
| `sp_pydantic_dataclasses` | `D:\Python\Lib\site-packages\pydantic\_internal\_dataclasses.py` | L5 同上 | 同上 |
| `sp_sqlalchemy_collections` | `D:\Python\Lib\site-packages\sqlalchemy\orm\collections.py` | L104 同上 | 同上 |
| `sp_pydantic_fields` | `D:\Python\Lib\site-packages\pydantic\fields.py` | L643 `SyntaxError: invalid syntax` | 源 `_DefaultValues = {**_Attrs, 'kw_only': None, ...}` ⇒ 产物写成 **`{*_Attrs: None, ...}`**（`**` 被改成 `*` 且多了 `:`） |
| `stdlib_enum` | `D:\Python\Lib\enum.py` | L1487 `SyntaxError: unterminated string literal` | 源 f-string 内嵌 `"""..."""` 三引号片段 ⇒ 产物字符串未闭合 |

### 2.6 「通用小样例复现」的反例（诚实读数）

`tools/l4_repro.py` 用 10 个**通用最小样例**（元组解包、校验删除、return 丢失、极性反转、await 丢失、
注解丢失、类属性丢失、未绑定局部、切片丢失、装饰器链）逐个跑 pycdc + 判据 + 执行级比对：
**9/10 未复现**（判据 success 且执行等价；仅「注解丢失」判红但执行等价）⇒
**语料外缺陷是上下文相关的**（同一形态在小样例里不复现）⇒
「最小复现」必须由**真实模块缩减**得到（§2.4 第 1、2 行的 `repro/min_*.py`），
**通用小样例不足以作为「该形态完备」的证据**（这本身是对 L5 证据层的输入）。

---

## §3 执行级差分结果表

### 3.1 方法

- 两侧各跑**独立子进程**、cwd = 各自的**空隔离临时目录**：
  **原模块 = 原件 `.pyc`**（`SourcelessFileLoader`，还原包上下文以支持相对导入），
  **产物 = `offcorpus/<slug>OK.py`**（`SourceFileLoader`）。
- 同一份 probe 规格（**表达式** 记返回值 + **类型名** + **stdout/stderr** + **隔离目录新增文件**；
  **代码块** 记副作用序）逐条执行（`tools/l4_semdiff.py`）。
- 比对口径：返回值 repr **且类型名**、异常**类型 + 消息**、stdout（副作用序）、文件副作用、模块公开名集合。

### 3.2 结果（24 样例 / 56 探针 / **14 处差异**）

| 样本 | 判据 | 探针 | 差异 | 具体差异（源 vs 产物） |
|---|---|---|---|---|
| `stdlib_difflib` | failure | 7 | **5** | 5 个探针全变 `NameError: name 'b2j' is not defined`；源分别返回 `0.75` / `[Match(a=0,b=0,size=2), …]` / `[('equal',0,2,0,2), …]` / `[]` / `0.0` |
| `stdlib_dataclasses` | failure | 5 | **2** | ① 源 `ValueError: eq must be true if order is true` ／ 产物 `NO-ERROR`（校验被删）；② `slots=True`：源 `('a',)`+`3` ／ 产物 `TypeError: 'int' object is not iterable` |
| `stdlib_json_encoder` | failure | 3 | **1** | `sort_keys+indent`：源 `'{\n  "a": 2,\n  "b": 1\n}'` ／ 产物 `'\n  "a"2,\n  "b"1\n'`（非法 JSON） |
| `stdlib_typing` | failure | 3 | **1** | `get_args(Union[int,str])`：源 `(int, str)`(tuple) ／ 产物 `([int], str)`(tuple，**首元素成了 list**) |
| `stdlib_csv` | failure | 1 | **1** | 源 `True` ／ 产物 `UnboundLocalError: start` |
| `stdlib_xml_ElementPath` | failure | 1 | **1** | 源 `[<Element 'b'>, <Element 'b'>]` ／ 产物 `[<Element 'root'>]` |
| `stdlib_tomllib_parser` | failure | 1 | **1** | 源 `{'a': 1, 'b': 'x'}` ／ 产物 `UnboundLocalError: char` |
| `stdlib_re__parser` | failure | 1 | **1** | 源侧 `AttributeError`（探针自身瑕疵：`.groupindex` 不存在） ／ 产物 `re.error: missing >, unterminated name at position 5` |
| `sp_httpcore_models` | failure | 2 | **1** | 源 `URL(scheme=b'http', host=b'example.com', port=None, target=b'/x')` ／ 产物 `AttributeError: 'URL' object has no attribute 'port'` |
| `stdlib_contextlib` / `stdlib_functools` / `stdlib_ipaddress` / `stdlib_argparse` / `stdlib_subprocess` / `stdlib_tarfile` / `stdlib_statistics` / `stdlib_http_cookiejar` / `stdlib_unittest_case` / `stdlib_asyncio_timeouts` / `stdlib_asyncio_taskgroups` / `stdlib_asyncio_streams` | failure | 1–4 | 0 | **判红但探针面语义相同**（12 例）⇒ 判据在这些点**过严**（红≠错） |
| `repo_core_config` / `repo_core_object_pool` / `repo_parsers_ctx` | **success** | 1–2 | 0 | 判绿且探针面一致（本轮**未观察到「判绿但语义错」**） |

### 3.3 判据与执行级的关系（本轮读数）

| 读数 | 值 | 说明 |
|---|---|---|
| 执行样例 | 24 | ≥8 的要求满足（3.0×） |
| 判据绿且探针面语义不同 | **0 / 3** | 本轮**未观察到**假绿（但探针面窄，不等于「无假绿」） |
| 判据红且探针面语义**相同** | **12 / 21 = 57.1%** | **判红 ≠ 语义错**（文件级全或无 + 归一化副作用） |
| 判据红且探针面语义不同 | **9 / 21 = 42.9%** | 判据红中真正语义错的份额 |
| 探针总差异率 | **14 / 56 = 25.0%** | 语料外产物在**可执行面**上的语义差异密度 |

> 结论：**判据的红与绿在语料外都不可直接当语义结论**——
> 红有 57.1% 假阳性，绿在本轮 3 例中未出现假阳性，但 Task 4 已证值类型/槽位/docstring 盲区
> （变异漏检 27.92%）⇒ **绿仍不是语义对的证明**。

---

## §4 边界读数

### 4.1 深度边界（≥164 层）

| 样例 | 读数 |
|---|---|
| 括号表达式 **164 层** | pycdc 1.25 s，verify **success**，AST 深度 6→6，执行等价 |
| 括号表达式 256 / 512 层 | **CPython 编译期 `RecursionError`**（源码侧边界，pycdc 未参与） |
| 嵌套调用 **164 层**（164 个函数） | pycdc 2.49 s，verify **success**，AST 深度 **170→170**，语句 332→332，执行等价 |
| 嵌套调用 256 层 | CPython 编译期 RecursionError |
| 下标链 **164 / 256 层** | verify **success**，AST 深度 **170→170 / 262→262**，执行等价 |
| `if` 缩进嵌套 **90 层** | pycdc 1.93 s，verify **success**，执行等价；**但 AST 深度 95→7、语句 94→5**（见 4.3） |
| `if` 缩进嵌套 120 层 | **CPython `IndentationError: too many levels of indentation`**（源码侧边界） |
| `if` 缩进嵌套 10 / 30 / 60 / 90 层（**单子链**形态：仅叶子带副作用） | verify **success**，执行等价；同样**深度塌陷到 7**（4.3） |

### 4.2 规模边界（≥500 语句函数 / 巨型表达式）

| 样例 | pycdc 耗时 | 判据 | 执行 | 说明 |
|---|---|---|---|---|
| 520 条语句 | 4.86 s | success | 等价 | — |
| 1000 条语句 | 8.75 s（另一次 13.23 s） | success | 等价 | 耗时**方差大**（机器负载） |
| 2000 条语句 | 19.87 s（另一次 68.51 s） | success | 等价 | **超线性**（2× 语句 → 2.3×–3.4× 时间） |
| 3000 条语句 | 69.12 s | success | 等价 | — |
| **4000 条语句** | **89.84 s** | success | 等价 | 距 300 s 命令门限仅 ~3.3× 余量 ⇒ **B212** |
| 5000 项布尔链 | 0.96 s | success | 等价 | — |
| 20000 元素列表字面量 | 1.25 s | success | 等价 | — |
| 5000 项加法链 / 字符串拼接 | — | — | — | **CPython 编译期 `RecursionError`**（源码侧边界） |

### 4.3 边界结论（退化形态）

1. **正确性边界**：在 **164 层表达式/调用/下标链、4000 条语句、20000 元素字面量** 上，
   产物**判据全绿且执行级等价** ⇒ pycdc 在这些规模上**未出现挂死/崩溃/截断**。
2. **结构退化边界（新增读数）**：**单子链嵌套 `if` 被塌陷为一条 `and` 链**——
   90 层嵌套 ⇒ 产物深度 95→7、语句 94→5（`boundary/nest_if_90OK.py` 第 5 行是一条 993 字符的 `and` 链）。
   在「单子链（各层只有一个子节点、条件相同）」这一形态下**字节码等价、语义等价**（判据 success、执行等价）；
   在「各层条件/体不同」时**不塌陷**（手工核验 `boundary/nest3b_distinct_bodies.py` → `...OK.py`：
   3 层、各层 `x += 1/2/4`，产物与源一致，输出 7/7）⇒
   塌陷条件 = **单子链**；风险 = 产物**源码结构不可信**，且**深度保真度没有任何现有门禁能测**（B209）。
3. **可用性边界**：函数语句数与反编译耗时呈**超线性**（4000 条 ≈ 90 s），本轮**未**测到挂死/崩溃，
   但**大函数不适合进 300 s 门禁**（B212）。
4. **不可判定项**：CPython 自身的编译期上限（缩进 ≈100 层 / 括号 ≈200 层 / 加法链 ≈1000 项）
   **先于** pycdc 生效 ⇒ 「≥164 层嵌套」在**缩进形态**上**无法构造**（只能构造表达式/调用/下标形态），
   该缺口是**构造器缺口**而非 pycdc 缺口（登记为 §7 的方法层输入）。

---

## §5 B142 / B143 复核（语料外）

### 5.1 形态扫描（语料外真实源码，AST 级）

- 扫描范围：`D:\Python\Lib` + `D:\Python\Lib\site-packages` + 仓库 `core/`、`parsers/`、`tools/`、`scripts/`
  = **29377 个真实 .py 文件**（`tools/l4_b142_b143.py`，预筛 `finally` + `continue/break`，再 AST 判定）。
- 命中：**B142 形态 41 个文件**（`try` 带 `finally` 且其内含 `continue`），
  **B143 形态 3 个文件**（`break` 出现在 `try.finalbody` 内）。

### 5.2 抽样复现（每形态取命中最多的 6 个模块）

| 形态 | 模块（来源） | 判据 | 结构比对（源 → 产物） | 复现 |
|---|---|---|---|---|
| **B142** | `D:\Python\Lib\socket.py`（`socket._sendfile_use_sendfile` L394） | failure | 源 `Try=4, finalbody=1, Continue=1, Break=2` → 产物 **`Continue=0, Break=4`** ⇒ **`continue` 整条丢失** | **是** |
| **B142** | `D:\Python\Lib\asyncio\base_events.py`（`create_server` L1506） | failure | 源 `Try=3, finalbody=1` → 产物 **`finalbody=3`** ⇒ **finally 副本重复发射**，且重复出来的那份**落在 `if not completed:` 之外** ⇒ 正常路径也会 `sock.close()` | **是** |
| **B142** | `D:\Python\Lib\site-packages\anyio\_core\_sockets.py`（`create_tcp_listener` L407） | failure | 源 `Try=3, finalbody=1, Continue=1` → 产物该函数内 **Try/finally/continue 全为 0** ⇒ try/finally 结构整体丢失 | **是** |
| **B142** | `D:\Python\Lib\asyncio\base_events.py`（`_connect_sock` L956） | failure | 结构计数一致（本例未复现） | 否 |
| **B142** | `D:\Python\Lib\site-packages\anyio\_core\_fileio.py` / `anyio\__init__.py` | failure | 本例未复现（计数一致） | 否 |
| **B143** | `D:\Python\Lib\site-packages\anyio\to_interpreter.py`（`run_sync` L223，`break` 在 `finalbody` L211 内） | failure | 源 `Try=3, finalbody=4, Break=1` → 产物 **`Try=2, finalbody=0, Break=0`** ⇒ **finally 体与 break 整体丢失** | **是** |
| **B143** | `D:\Python\Lib\site-packages\click\_termui_impl.py`（`_pipepager` L513） | compile_error | 源 `Try=3, finalbody=2, Break=1` → 产物 `Try=2, finalbody=3, Break=0` ⇒ **break 丢失 + finally 副本膨胀** | **是** |
| **B143** | `D:\Python\Lib\site-packages\asyncio\locks.py` | failure | 本例未复现（计数一致） | 否 |

### 5.3 结论

- **B142 / B143 在语料外真实代码上复现成立**（B142 抽样 6 个模块中 **3 个**复现；B143 语料外仅 **3 个**文件命中该形态、**全部抽样**，其中 **2 个**复现）⇒
  二者**不是语料内孤例**，round5 的「B142 = 形态级缺口」定性在语料外**同样成立**。
- 语料外的表现与语料内**同族但更重**：除了「finally 副本重复」，还出现
  「**continue 整条消失**」（socket.py）、「**try/finally 结构整体消失**」（anyio/_core/_sockets.py）、
  「**finally 与 break 整体消失**」（anyio/to_interpreter.py）。
- 具体可引用的产物片段（`b142b143/b142_socketOK.py` L314-341）：
  源 `if timeout and not selector_select(timeout): raise TimeoutError('timed out')`
  ⇒ 产物 `if not (timeout and not selector_select(timeout)): pass else: <整个循环体>`
  （**raise 被替换成 `pass`，且 `if count:` 块被挂到错误的分支**），
  源 L394 的 `continue` 消失 ⇒ `BlockingIOError` 之后落入 `if sent == 0:`（`sent` 未绑定）。
- **登记**：B142/B143 的**表现面**在语料外扩展 ⇒ 新破口 **B207**（finally 副本重复 + 脱离保护）、
  **B208**（continue 整条丢失）；B143 的语料外表现并入 **B209** 之外的独立条目（B204 的近亲）
  ⇒ 见 §6。

---

## §6 新破口登记（自 **B202** 起；不复用 B163–B201）

> 归属层除注明外均为 **L4 实现层**；状态：**开放**。全部可用 `rounds/round6/tools/` 的脚本复现。

| 编号 | 根因 | 表现（最小复现 / 读数） | 归属层 | 判定空间条目 | 状态 |
|---|---|---|---|---|---|
| **B202** | **产物不可编译**：① 模块 docstring 被还原成 `__doc__ = ...` **赋值语句** ⇒ 其后 `from __future__ import` 非法；② `**dict` 解包被写成 `{*d: ...}`；③ f-string 内嵌三引号 ⇒ 字符串未闭合 | 语料外 **7/46 = 15.22%**：`repo_scripts_verify` L27、`sp_packaging_specifiers` L10、`sp_packaging_version` L9、`sp_pydantic_dataclasses` L5、`sp_sqlalchemy_collections` L104、`sp_pydantic_fields` L643、`stdlib_enum` L1487 | L4 | JS-DOC-*/JS-IMPORT-* | 开放 |
| **B203** | **局部变量写入被改写为属性赋值 / 整条丢失** ⇒ 后续读取变成未定义名查找 ⇒ 运行期 `NameError`（`STORE_FAST x` → `STORE_ATTR self.x`；`STORE_FAST x` 消失而 `LOAD_GLOBAL x` 留存） | `difflib.__chain_b`（`b2j = {}` → `self.b2j = {}` ⇒ `NameError: b2j`）、`get_matching_blocks`(`la`)、`get_opcodes`(`answer`)、`find_longest_match`(`besti/bestj`)；执行级：`repro/min_difflib2.py`（真实 difflib.py 2064→779 行）源返回 Match 列表 ／ 产物 `NameError` | L4 | JS-ASSIGN-*/JS-SCOPE-* | 开放 |
| **B204** | **`try/except/else` 的 `else` 分支丢失** ⇒ 异常路径也执行 else 体 | `csv.Sniffer.has_header`：源 `else: hasHeader -= 1`；产物 `hasHeader -= 1` 变成**无条件** ⇒ 类型转换失败时净增变 0 ⇒ **表头判定语义反转**（`repro/min_csv.py`） | L4 | JS-TRY-*/JS-EXCEPT-* | 开放 |
| **B205** | **前置校验 / `raise` 被删除** ⇒ 非法入参被静默接受 | `dataclasses._process_class`：`raise ValueError('eq must be true if order is true')` 整块消失（指令级差分可见 `LOAD_CONST`+`RAISE_VARARGS` 被删）⇒ 源 `ValueError` ／ 产物 `NO-ERROR`；`core/cfg/cfg_builder.py::_parse_instructions` 的 `isinstance(_argval, tuple)` 检查被删 | L4 | JS-RAISE-*/JS-CHECK-* | 开放 |
| **B206** | **分支极性反转**（`JUMP_IF_TRUE_OR_POP` ↔ `JUMP_IF_FALSE_OR_POP`） | `core/cfg/cfg_builder.py::CFGBuilder._build_basic_blocks`：2 处极性反转（指令级差分可见） | L4 | JS-BOOLOP-*/JS-JUMP-* | 开放 |
| **B207** | **finally 副本重复发射，且重复副本脱离原保护条件**（B142 症状的语料外形态） | `asyncio/base_events.py::create_server`：源 `finally: if not completed: for sock in sockets: sock.close()`；产物 `finally: if not completed: for sock in sockets: sock.close()` **+ `sockets` + `sock.close()`**（在 `if` 之外）⇒ **正常路径也会关闭监听 socket**；结构计数 `finalbody 1→3` | L4 | JS-FINALLY-*/JS-B142-* | 开放 |
| **B208** | **`continue` 形态整条丢失**（B142 症状的语料外形态） | `socket.py::_sendfile_use_sendfile`：源 L394 `continue` 消失 ⇒ `BlockingIOError` 后落入 `if sent == 0:`（`sent` 未绑定）⇒ 运行期 `UnboundLocalError`；同一函数的 `raise TimeoutError('timed out')` 还被替换成 `pass` | L4 | JS-CONTINUE-*/JS-B142-* | 开放 |
| **B209** | **结构塌陷：单子链嵌套 `if` 被合并为一条 `and` 链** ⇒ 产物**源码结构不可信**、深度保真度不可测 | `boundary/nest_if_90OK.py`：90 层嵌套 ⇒ 产物深度 **95→7**、语句 **94→5**（第 5 行是一条 993 字符的 `and` 链）；本形态字节码等价、语义等价（判据 success）⇒ 现有门禁**测不到**该退化 | L4 | JS-IF-*/JS-DEPTH-* | 开放 |
| **B210** | **字面量 / 分隔符片段丢失** ⇒ 输出内容损坏 | `json/encoder.py`：`yield '{'` / `yield '}'` / `yield ','` 丢失 ⇒ `JSONEncoder(indent=2).encode(...)` 输出 `'\n  "a"2,\n  "b"1\n'`（**非法 JSON**）；`typing.get_args` 返回 list 而非 tuple | L4 | JS-CONST-*/JS-STR-* | 开放 |
| **B211** | **类成员 / 属性丢失** ⇒ `AttributeError` | `httpcore/_models.py::URL`：`self.port` 相关赋值丢失 ⇒ `AttributeError: 'URL' object has no attribute 'port'` | L4 | JS-CLASS-* | 开放 |
| **B212** | **规模-耗时超线性** ⇒ 大函数不可进 300 s 门禁 | 4000 条语句函数：pycdc **89.84 s**（1000 条 8.75–13.2 s；2000 条 19.9–68.5 s；3000 条 69.1 s）⇒ 增长 ≈ O(n^1.5–2.3) | L4 | JS-SCALE-* | 开放 |
| **B213** | **口径/覆盖缺口**：真实语料**零 `except*`** ⇒ PEP 654 无法由真实项目覆盖 | stdlib 795 文件 + site-packages 14237 文件 AST 全扫：`ast.TryStar` 节点 **0**；文本命中全是字符串字面量 ⇒ 合成补样 `offcorpus/synth_except_star.py` 形态**正确**（verify success 4/4、执行等价），但**无真实分布证据** | L4（口径层） | JS-EXCEPTSTAR-* | 定性登记 |

**不新立编号、但须并入既有台账的两项**：

| 项 | 处置 |
|---|---|
| 「判据红 ≠ 语义错」：21 个判红样例里 **12 个（57.1%）** 在探针面语义相同 | 并入 **B201**（判据读数分层标注）的口径扩展：本轮补「**红也有假阳性**」的一侧读数 |
| 「通用最小样例复现不了语料外缺陷」（9/10 不复现） | 并入 **B163/B168**（证据-形态错配）的口径扩展：**通用样例绿 ⇒ 该形态在真实上下文里对**，该推断**不成立** |

---

## §7 对方法层的输入（交给 Task 8 的方法设计）

1. **判定空间必须新增「语料外真实项目」维**（不是「更多探针」）：
   语料外判据绿率 **8.70%**（4/46）而语料内 100% ⇒
   **「语料内全绿 ⇒ 完备」的外延被证伪**；判定空间需登记
   「真实项目来源分布（stdlib / site-packages / 自有仓）」这一维，并要求每维有**独立证据**。
2. **语义差分判据必须是执行级 + 类型敏感 + 副作用序**（主判据），静态判据降为辅证：
   本轮 14/56 差异**全部**是静态判据看不出来的（`NameError`、静默丢校验、JSON 损坏、tuple→list、属性缺失）；
   反向也成立：静态判据红有 **57.1%** 假阳性 ⇒ **红与绿都不可直接当语义结论**（round4 §6.1 的分层标注须扩成「红/绿双向」）。
3. **「通用最小样例」不能替代真实上下文证据**：9/10 通用样例不复现语料外缺陷
   ⇒ 覆盖检查器须新增「**真实项目缩减复现**」这一证据形态（本轮 `repro/min_*.py` 提供了原型：
   真实模块按顶层块做 delta-debugging，缺陷签名保持即接受删除）。
4. **判据面必须能看见「赋值目标」与「变量作用域」**（B203）：
   `STORE_FAST` → `STORE_ATTR` / `LOAD_GLOBAL` 的改写，静态判据当前**完全不可见**
   （round4 B197 只补了 `arg` 槽位，未覆盖**赋值目标**）⇒ 判据增强需求应新增「赋值目标 + 局部/全局解析」维度。
5. **深度/规模保真度需要独立指标**（B209/B212）：
   现有门禁只有「判红/判绿」，无法表达「结构塌陷但语义等价」；方法层应给出
   **结构保真指标**（嵌套深度、语句数、区域数在源↔产物间的差）与**耗时上界**（可进 300 s 门禁的最大规模）。
6. **语料特征覆盖必须逐特征核实「真实语料是否存在」**（B213）：
   `except*` 在本机真实语料中为 0 ⇒ 「PEP 654 已完备」这类断言**没有证据面**；
   覆盖检查器应能输出「**该特征在真实语料中的实例数**」，为 0 时该特征只能记「合成补样测过、真实分布未覆盖」。
7. **不可证伪项登记**（转方法层）：
   - AT-44 的执行级差分覆盖面有限（24/46 样例、56 探针，且探针只覆盖公开 API）⇒
     「产物在**未探针面**上是否还有差异」在现有读数下**不可证伪** ⇒ 需要**差分 fuzz**（随机输入 + 属性断言）补强。
   - 「崩溃/挂死」在 4000 条语句内**未观测到**⇒ 该维度的不可证伪性需由**更大规模 + 超时门禁**给出。

---

## 附录 A：本轮产物清单（`rounds/round6/`）

| 路径 | 内容 |
|---|---|
| `ATTACK_L4_RUNTIME.md` | 本报告 |
| `tools/l4_build_samples.py` | 语料外样本清单构建（**AST 自动特征判定** + 优先取未被 pytest 改写的 pyc） |
| `tools/l4_offcorpus_diff.py` | 语料外差分驱动（pycdc → `pyc_verify single` + 源码≡pyc 核对） |
| `tools/l4_src_pycheck.py` | 「源码 ≡ 原件 pyc」**严格**核对（`co_code`+`co_consts`+`co_names`） |
| `tools/l4_summarize.py` | §2 表汇总（JSON / CSV / Markdown） |
| `tools/l4_source_divergence.py` | 源码级 AST 指纹差分 + AST dump 统一差分（**不依赖判据 verdict**） |
| `tools/l4_byte_diff.py` | **指令级**差分（按 `co_qualname` 配对 code object，归一化后序列差分） |
| `tools/l4_classify.py` | 失败单元根因分类（C1–C14） |
| `tools/l4_digest.py` | 逐样本失败摘要表（§2 的数据源） |
| `tools/l4_make_probes.py` + `exec_probes.json` | 执行级探针规格（24 样例 / 56 探针） |
| `tools/l4_semdiff.py` | 执行级语义差分（两侧独立子进程 + 隔离 cwd + 沙箱空目录） |
| `tools/l4_repro.py` | 10 个通用最小样例（**不复现**的诚实读数） |
| `tools/l4_minimize.py` | 真实模块的 delta-debugging 缩减（最小复现） |
| `tools/l4_eval_min.py` | 缩减件的判据 + 执行级取证 |
| `tools/l4_boundary.py` | 规模/深度边界攻击（§4） |
| `tools/l4_b142_b143.py` | B142/B143 语料外形态扫描 + 抽样复现（§5） |
| `tools/l4_inspect_failures.py` | 失败样本取证（失败单元 + 产物编译错误原文） |
| `offcorpus/` | 46 个语料外样本的 **pyc 副本 + 反编译产物**（`OK.py`）+ `samples.json` + 合成补样 |
| `repro/` | 最小复现件（`min_difflib2.py` 779 行 / `min_csv.py` 377 行）+ 通用样例 + 缩减件产物 |
| `boundary/` | 边界样例源 + 产物（`nest_if_90OK.py` 等） |
| `b142b143/` | B142/B143 复现用的 pyc + 产物（`b142_socketOK.py` 等） |
| `logs/` | 全部原始读数：`l4_offcorpus_summary.json`、`offcorpus_diff.csv`、`l4_offcorpus_table.md`、`l4_source_divergence.{json,md}`、`l4_byte_diff.json`、`l4_classify.{json,md}`、`l4_failure_digest.md`、`l4_semdiff.json`、`l4_repro.json`、`l4_minimize.json`、`l4_min_eval.json`、`l4_boundary*.json`、`l4_b142_b143{,_scan}.json`、`l4_src_pycheck.json` |

## 附录 B：口径与纪律声明

1. **只测不修**：`core/cfg/**`、`scripts/pyc_verify.py`、`tests/**`、`wiki/**`、`rules.md`、其它规范目录零改动；产出全部在 `rounds/round6/**`。
2. **不 push**；提交前缀 `rr-v4r06:`。
3. **判据调用形式**：全轮统一 `python -X utf8 scripts/pyc_verify.py single <pyc> --source <产物>`；读数以该命令 stdout 的 `[single] status=` 为准。
4. **原模块基准 = 原件 `.pyc`**（不是磁盘源码）：46/46 样例经严格核对（code+consts+names）确认磁盘源码与 pyc 同源，
   但**执行级差分仍以 pyc 为准**（避免任何源码漂移污染结论）。
5. **诚实读数**：
   - 判据红**不等于**语义错（12/21 = 57.1% 假红）；判据绿在本轮 3 例中未见假绿，但**不等于**绿即语义对（Task 4 盲区 27.92% 仍适用）；
   - 10 个**通用最小样例 9 个不复现** ⇒ 缺陷是上下文相关的，最小复现必须由真实模块缩减得到；
   - `except*` 在本机**真实语料中不存在**（AST 全扫 0 命中）⇒ 该特征只有合成补样证据；
   - 边界读数受**机器负载影响明显**（同一样例两次耗时差 ~3×）⇒ §4 的耗时只作**量级**读数，不作精确基准；
   - `sp_sympy_qexpr`（判绿）**未做**执行级差分 ⇒ 「4 个判绿样例全部语义正确」**未被完整验证**（未核实项）。
6. **未改动既有产物**：`site-packages/**` 的 402 认证产物、`test_repros/**` 零改动、零重跑（E 门禁全量由 Task 10 负责）。
