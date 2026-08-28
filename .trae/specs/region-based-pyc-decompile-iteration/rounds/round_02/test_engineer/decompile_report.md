# Round 02 — 反编译差异分析报告（测试工程师）

- 语料：site-packages 402 个 pyc，本轮 `partial` 102 个，共 2666 函数、2323 匹配（87.13%）
- 基线：`.trae/specs/region-based-pyc-decompile-iteration/rounds/round_02/baseline/batch_000.json`
- 运行环境：全部命令使用 `D:/Python/python.exe`（3.11.7），pyc 魔数 `a70d0d0a`
- 边界：**未修改 `core/` 下任何程序代码，未修改任何 OK.py，未放宽比对判据**

---

## 1. 102 个 partial 按不匹配函数数分布

| 不匹配函数数 | 1 | 2 | 3 | 4 | 5 | 6 | 8 | 9 | 10 | 13 | 14 | 16 | 27 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 文件数 | **37** | 25 | 16 | 5 | 6 | 4 | 1 | 1 | 2 | 1 | 1 | 1 | 1 |

> 说明：任务描述里的「29 个 bad==1」与基线实测 **`bad==1` 的文件是 37 个**。差异来自基线重跑（`pyc_index.json` 状态变化 / 遍历顺序）。本报告按实测的 **37 个** 展开，是 29 的超集。

37 个 `bad==1` 文件是「修好 1 个函数即整文件翻转」的最高性价比目标，占 102 个 partial 的 36%。

---

## 2. 方法

1. 从 `batch_000.json` 取全部 102 文件的 `mismatches`，按不匹配函数数升序排序。
2. 对 37 个 `bad==1` 文件逐个用 `tools/pyc_diff.py` 的同一套加载/比对逻辑取首个不一致点 ±8 条上下文
   （驱动脚本 `tmp/dump_diffs.py`，输出 `tmp/part_a.txt` / `tmp/part_b.txt`）。
3. 由于 `batch_000.json` 的 `first_diff.index` 是**过滤 NOP/PRECALL/EXTENDED_ARG 之后**的下标，
   而 `pyc_diff.py` 打印的是未过滤的 `dis` 流，两者下标不一致。因此另写了 `tmp/view.py`，
   复用 `testqouter/round1/base.py` 的 `_filter_noise_instrs` / `_normalize_argval`，
   使下标与基线对齐；`-j` 开关可忽略跳转位移，用于找出**真正的**首个差异（很多文件首个差异只是
   jump 目标偏移了 2~4 字节，真实改动在后面）。
4. 对归类出的每个 family，用 `core.cfg.decompile(source)` 构造最小源码复现，并用
   `minimal_repros/run_repros.py` 做 `compile → decompile → compile → 递归 co_code 比对` 验证。

---

## 3. Family 分类

共归类出 **8 个已复现 family（F1–F8）** + **1 个未复现族（F9）**。

### F1 — `<call>().attr = value`：STORE_ATTR 的值/对象栈序颠倒，常量丢失为 `None`

| 项 | 内容 |
|---|---|
| 代表函数 | `IQEngine/plugins/plugin_system_accounts/api/api_stock.pyc` `<module>`（509→509，true=1） |
| 首个不一致点 | idx 111 |

```
 111 | LOAD_CONST 10            | LOAD_CONST None        << 值丢失
 112 | PUSH_NULL                | PUSH_NULL
 113 | LOAD_NAME getcontext     | LOAD_NAME getcontext
 115 | CALL                     | CALL
 116 | STORE_ATTR prec          | STORE_ATTR prec
```

**根因判断**：CPython 3.11 对 `f().x = 5` 的栈布局是「**先压值 5，再压对象 f()**」，
`STORE_ATTR` 取 TOS1=值、TOS=对象。反编译器按「值最后压入」的常规假设取值，
拿到的是 `CALL` 的结果，先前压入的常量被当作无效残留丢弃 → 输出 `f().x = None`。
注意 `a = A(); a.x = 5`（简单属性赋值）正确，说明问题只出在 **STORE_ATTR 的对象端本身是 CALL** 的形状。

**影响面**：全 102 文件中，first_diff 形如 `LOAD_CONST <非None> → LOAD_CONST None` 的命中 **3 个文件**
（`api_stock.pyc`、`plugin_system_trade/send_message_api.pyc`、`IQEngine/utils/profiler_func.pyc`）。

**复现**：`repro_01.py`

---

### F2 — 类体内同名别名赋值 `X = X` 被整体丢弃

| 项 | 内容 |
|---|---|
| 代表函数 | `IQEngine/data/data_proxy.pyc` `DataProxy`（37→33，true=32） |
| 首个不一致点 | idx 5 |

```
   5 | LOAD_NAME TickBar                          | LOAD_CONST <code object __init__>
   6 | STORE_NAME TickBar                         | MAKE_FUNCTION
   7 | LOAD_NAME BarData                          | STORE_NAME __init__
   8 | STORE_NAME BarData                         | LOAD_CONST <code object __getattr__>
```

**根因判断**：类体里的 `TickBar = TickBar`（源名与目标名相同）被当成「自赋值 / 无副作用」
或重复定义折叠掉。反编译器没有为「类体内 `STORE_NAME` 的目标名与 `LOAD_NAME` 源名相同」
这一形状生成赋值节点，直接从下一条 `def` 开始输出。

**影响面**：1 个文件（data_proxy.pyc），但这是一整类的「类体简单赋值丢失」的信号。

**复现**：`repro_02.py`

---

### F3 — 连续多条 `obj.attr = a or b.c`：从第 2 条起被截断为裸表达式，其后语句全部丢失

| 项 | 内容 |
|---|---|
| 代表函数 | `IQEngine/account/trade.pyc` `create_trade`（68→19，true=52） |
| 首个不一致点 | idx 16 |

```
  16 | JUMP_IF_TRUE_OR_POP to 104 | POP_TOP                << 短路结构被当成表达式收尾
  17 | LOAD_FAST env              | LOAD_FAST trade_id
  18 | LOAD_ATTR trading_dt       | RETURN_VALUE
  19 | LOAD_FAST trade            | -
  20 | STORE_ATTR _trading_dt     | -
  21 | LOAD_FAST price            | -
 ...  （后续 40+ 条全部消失）
```

反编译输出（真实 OK.py 摘录）：

```python
def create_trade(cls, order_id, price, amount, ...):
    env = Engine.instance()
    trade = cls()
    trade._calendar_dt = calendar_dt or env.calendar_dt
    trading_dt                  # ← 第 2 条退化成裸表达式
    return trade_id             # ← 后面 8 条 `trade._xxx = ...` 全丢
```

**根因判断**：第一条 `or` 赋值的 `STORE_ATTR` 之后，栈上残留一个短路求值结果；
反编译器对下一条同类语句的栈深度估计错误，把 `JUMP_IF_TRUE_OR_POP` 的 fall-through
误判为表达式语句的收尾（`POP_TOP`），导致区域归约提前闭合，函数剩余线性区被整体丢弃。
单条 `o.x = a or b.a` 是**能正确还原**的（候选探针 d06 通过），必须是**两条及以上连续**才触发。

**影响面**：`trade.pyc`；签名 `JUMP_IF_TRUE_OR_POP → POP_TOP`。
同类「连续短路赋值截断」在多个大函数里是造成 `orig≫decomp` 的主因之一。

**复现**：`repro_03.py`、`repro_04.py`

---

### F4 — `assert` 之前紧邻的赋值语句被丢弃，被赋值变量退化为全局名 `LOAD_GLOBAL`

| 项 | 内容 |
|---|---|
| 代表函数 | `IQEngine/account/order.pyc` `fill`（69→51，true=68） |
| 首个不一致点 | idx 1 |

```
   1 | LOAD_FAST trade          | LOAD_FAST self          << `amount = trade.amount` 整条消失
   2 | LOAD_ATTR amount         | LOAD_ATTR filled_amount
   3 | STORE_FAST amount        | LOAD_GLOBAL amount      << amount 退化成全局名
   4 | LOAD_FAST self           | BINARY_OP +
   5 | LOAD_ATTR filled_amount  | LOAD_FAST self
   6 | LOAD_FAST amount         | LOAD_ATTR amount
   7 | BINARY_OP +              | COMPARE_OP <=
   8 | LOAD_FAST self           | POP_JUMP_FORWARD_IF_TRUE
   9 | LOAD_ATTR amount         | LOAD_ASSERTION_ERROR
  10 | COMPARE_OP <=            | RAISE_VARARGS
```

**根因判断**：3.11 里 `assert cond` 展开为 `POP_JUMP_FORWARD_IF_TRUE → LOAD_ASSERTION_ERROR → RAISE_VARARGS`。
区域归约把 assert 的条件表达式当作一个独立区域的入口，紧邻其前的那条**简单赋值**
（`amount = trade.amount`）被判成「无后续使用的临时值」而删除；
后续对同一名字的引用在符号表里找不到局部绑定，于是退化成 `LOAD_GLOBAL`。
这是**语义错误**（不只是字节码形状差异）——原来的局部变量变成了全局查找。

**影响面**：全部 102 个 partial 中，first_diff 恰为 `LOAD_FAST → LOAD_GLOBAL` 的命中 **17 个文件 / 18 个函数**，
是覆盖面最广的一族。

**复现**：`repro_05.py`（无 msg）、`repro_06.py`（带 msg）、`repro_07.py`（属性形式 `y = self.compute(x)`）

---

### F5 — `with` / `if` 之后的 bare `return` 丢失（提前返回被降级为跳转或 if/else）

| 项 | 内容 |
|---|---|
| 代表函数 | `IQEngine/plugins/plugin_system_finance/commission.pyc` `load`（87→84，true=43）；`json_persistance.pyc` `persist`（78→77，true=46）；`IQCommon/logger/handlers.pyc` `_target` |
| 首个不一致点 | commission.load idx 43 |

```
  38 | LOAD_CONST None     | LOAD_CONST None       # __exit__(None,None,None)
  41 | CALL                | CALL
  42 | POP_TOP             | POP_TOP
  43 | LOAD_CONST None     | JUMP_FORWARD          << 原: 显式 return；反编译: 跳到清理块
  44 | RETURN_VALUE        | PUSH_EXC_INFO
  45 | PUSH_EXC_INFO       | WITH_EXCEPT_START
  46 | WITH_EXCEPT_START   | POP_JUMP_FORWARD_IF_TRUE
```

**根因判断**：函数末尾（`with` 块之后）的显式 `return` 在字节码里确实是
`LOAD_CONST None; RETURN_VALUE`（2 条）。反编译器把 `with` 清理块的出口统一成
`JUMP_FORWARD` 到异常表尾部，把显式 return 合并掉了。
**更严重的是**：当 `return` 之后还有代码时（真实 `load()` 的形状是
`if not exists: return` + `with` + `return`），反编译器会把「`if` + 随后的语句」
重排成 `if/else`，使 `return` 的终止点丢失 —— 见 `repro_09`，输出变成
`if ...: return None else: with ...`。

**影响面**：`LOAD_CONST → JUMP_FORWARD` 8 个文件 ∪ `JUMP_FORWARD → LOAD_CONST` 10 个文件
= **17 个文件**（两集合有 1 个文件重叠），是数量最大的族之一。

**复现**：`repro_08.py`、`repro_09.py`

---

### F6 — `for ... else:` 的 else 子句丢失；循环内 `continue` 的条件极性被反转

| 项 | 内容 |
|---|---|
| 代表函数 | `fly/common/convert.pyc` `getchnstr`（37→38，jump=2 / true=3） |
| 首个不一致点 | idx 12（jump-only 差异在 idx 5） |

```
   5 | FOR_ITER to 160                        | FOR_ITER to 162
  12 | POP_JUMP_FORWARD_IF_TRUE to 104        | POP_JUMP_FORWARD_IF_FALSE to 160   << 极性反转
  33 | JUMP_FORWARD to 160                    | JUMP_FORWARD to 162
  34 | JUMP_BACKWARD 10                       | JUMP_BACKWARD 10
  35 | LOAD_FAST chn_str                      | JUMP_BACKWARD 10                   << 多一条
  36 | RETURN_VALUE                           | LOAD_FAST chn_str
```

**根因判断**：循环体内的 `if A or B: continue` 被还原成 `if not A: <body>` 的相反极性，
多出一次 `JUMP_BACKWARD`；`for/else` 的 else 分支在区域归约时被并入循环出口，
else 子句整体消失（`repro_10` 的输出里 `else: return None` 被删掉，语义改变：
循环正常结束时原本返回 `None`，现在会返回 `i`）。

**影响面**：convert.pyc（1 个文件翻转）；`for/else`、`while/else` 在业务代码里出现频率不高，
但一旦出现就是**语义级错误**。

**复现**：`repro_10.py`

---

### F7 — STORE_ATTR 的值为三元 `a if a is not None else f()`：该语句及后续全部丢失，末句被提升为 `return`

| 项 | 内容 |
|---|---|
| 代表函数 | `IQEngine/account/base_account.pyc` `__init__`（25→14，true=15） |
| 首个不一致点 | idx 10 |

```
  10 | LOAD_FAST processed_trade   | LOAD_FAST self                << 三元赋值整条消失
  11 | POP_JUMP_FORWARD_IF_NONE    | LOAD_METHOD register_event
  12 | LOAD_FAST processed_trade   | CALL
  13 | JUMP_FORWARD to 78          | RETURN_VALUE
  14 | LOAD_GLOBAL set             | -
  15 | CALL                        | -
  16 | LOAD_FAST self              | -
  17 | STORE_ATTR _processed_trade | -
  18 | LOAD_CONST 0                | -                             << `self._transaction_cost = 0` 也丢
  ...
  22 | LOAD_METHOD register_event  | -
```

真实 OK.py 输出：

```python
def __init__(self, total_cash, positions, processed_trade=None):
    self._positions = positions
    self._frozen_cash = 0
    self._total_cash = total_cash
    return self.register_event()        # ← 三元赋值、self._transaction_cost=0 全丢，末句被提升为 return
```

**根因判断**：三元表达式的两个分支各自结束于跳转（`JUMP_FORWARD` 汇合点）。
区域归约把「汇合点之后」误判为不可达，或者把 else 分支的值节点错挂到 `STORE_ATTR` 之外，
于是三元赋值整条被丢弃；紧接着的下一条语句也被吞掉，最后一条调用被提升为 `return`。
（对比：同样的三元赋给**局部标量**是能正确还原的，候选探针 e07 通过；
问题只出在 **`STORE_ATTR` 的值为三元** 这一形状。）

**影响面**：base_account.pyc；first_diff 签名 `LOAD_FAST → LOAD_FAST` 在全部 102 文件中命中 14 个。

**复现**：`repro_11.py`

---

### F8 — if 块内的 `import x` 还原失败：`IMPORT_NAME` 退化成 `x = None`，并插入多余 `return None` / 语句重排

| 项 | 内容 |
|---|---|
| 代表函数 | `IQEngine/plugins/plugin_system_debug/__init__.pyc` `setup`（115→18，true=109，**本批单函数损失最大**） |
| 首个不一致点 | idx 5 |

```
   5 | POP_JUMP_FORWARD_IF_FALSE to 834 | POP_JUMP_FORWARD_IF_FALSE to 88
   6 | LOAD_CONST 0                     | LOAD_FAST config              << 语句被重排
   7 | LOAD_CONST None                  | LOAD_ATTR timeout
   8 | IMPORT_NAME ptvsd                | JUMP_IF_TRUE_OR_POP 52
   9 | STORE_FAST ptvsd                 | LOAD_CONST 10
  10 | LOAD_GLOBAL get_python_version   | LOAD_FAST engine
  11 | CALL                             | LOAD_ATTR config
  12 | LOAD_CONST '3.11'                | LOAD_ATTR other
  13 | COMPARE_OP ==                    | STORE_ATTR enable_debug
```

真实 OK.py 输出（节选）：

```python
def setup(self, engine):
    if engine.config.other.enable_debug:
        engine.config.other.enable_debug = config.timeout or 10   # ← 从块尾被提到块首
        return None                                               # ← 凭空插入的 return
        import ptvsd                                              # ← 变成不可达代码
        if get_python_version() == '3.11':
            ...
```

更小形态（repro_12）的输出：

```python
def f(engine):
    if engine.debug:
        ptvsd = None        # ← IMPORT_NAME 的 level 常量丢失
        ptvsd = None        # ← 重复一次
        engine.x = ptvsd.y() or 10
        engine.z = 1
        return None         # ← 凭空插入
```

**根因判断**：3.11 的 `import x` 是 `LOAD_CONST <level>; LOAD_CONST None; IMPORT_NAME; STORE_FAST`
四指令序列。反编译器的常量栈模拟把 `LOAD_CONST 0`（level）与紧邻的常量折叠/丢弃，
`IMPORT_NAME` 节点拿不到 level 参数与 `STORE_FAST` 目标，退化成 `x = None`；
同时该块被错误地插入 `return None`，其后代码变成不可达。

**影响面**：plugin_system_debug（115→18）1 个文件，但该函数 97 条指令被抹掉，是本批损失最大的单点。

**复现**：`repro_12.py`、`repro_13.py`

---

### F9（未复现）— 模块尾部多出 `RETURN_VALUE`；`from mod import name as alias` 退化成元组赋值

| 文件/函数 | 首个不一致点 | 现象 |
|---|---|---|
| `fly/common/user_error.pyc` `<module>`（47→48，true=1） | idx 47：`None → RETURN_VALUE` | 反编译产物在模块尾**多出 1 条** `RETURN_VALUE` |
| `IQData/utils/profiler_func.pyc` `<module>`（116→112，true=72） | idx 41：`LOAD_CONST 0 → LOAD_CONST ['LineProfiler']` | `from _line_profiler import LineProfiler as CLineProfiler` 被还原成 `CLineProfiler = ('LineProfiler',)`，`IMPORT_NAME` / `IMPORT_FROM` 被吞 |

profiler_func 的关键片段：

```
  41 | LOAD_CONST 0                 | LOAD_CONST ('LineProfiler',)
  42 | LOAD_CONST ('LineProfiler',) | STORE_NAME CLineProfiler
  43 | IMPORT_NAME '_line_profiler' | LOAD_NAME sys
  44 | IMPORT_FROM 'LineProfiler'   | LOAD_ATTR version_info
  45 | STORE_NAME 'CLineProfiler'   | LOAD_CONST 0
  46 | POP_TOP                      | BINARY_SUBSCR
```

**已排除的假设**（都用最小源码验证过，均为 PASS，说明不是这些触发的）：
`from x import y as z` 单独出现、紧跟 try/except ImportError 之后、前面带多条 `import a`、
后面跟 `class C(CLineProfiler)`。需要在真实 pyc 上继续定位。

---

## 4. 其他观察（尚未归纳成独立 family，供修复工程师参考）

| 现象 | 文件/函数 | 证据 |
|---|---|---|
| 多目标下标赋值 `call_args[end] = cache_start` 退化成简单赋值 `start_ = cache_start` | `IQEngine/utils/cache_storage.pyc` `func_wrapper`（270→240） | idx 56：`LOAD_FAST cache_start; LOAD_DEREF call_args; LOAD_FAST end; STORE_SUBSCR` → `JUMP_FORWARD; LOAD_FAST cache_start; STORE_FAST start_` |
| `try:` 块范围被扩大到整个函数体，`except` 子句位置错移 | `plugin_fly_data/local_variables/finance.pyc` `__missing__` | idx 35：`JUMP_FORWARD; PUSH_EXC_INFO; LOAD_GLOBAL AttributeError...` → 直接 `LOAD_GLOBAL Position`（try 包裹范围错误） |
| `POP_JUMP_FORWARD_IF_NOT_NONE` 被还原成极性相反的 `POP_JUMP_FORWARD_IF_TRUE` | `db_base.pyc _get_session_maker`、`oauth2.pyc post`（188→64） | first_diff `POP_JUMP_FORWARD_IF_NOT_NONE → POP_JUMP_FORWARD_IF_TRUE` |
| `try/except BaseException` 被还原成 `if/else` | `plugin_system_persist/__init__.pyc` `setup`（161→163） | idx 79：`JUMP_FORWARD; PUSH_EXC_INFO; CHECK_EXC_MATCH` → `LOAD_GLOBAL os; LOAD_ATTR path; LOAD_METHOD exists` |
| 块顺序重排（`hasattr` 分支被提前） | `IQData/manager/plugin_manager.pyc` / `IQEngine/core/plugin_manager.pyc` `set_engine` | idx 75：`JUMP_FORWARD; LOAD_GLOBAL hasattr` → `LOAD_FAST plugin_config; LOAD_METHOD update` |

---

## 5. `bad==1` 的 37 个文件全表

按 `true_diffs` 升序（越小越好修）。列：`orig→decomp` 为过滤后的指令条数，`jump/true` 为
`jump_diffs/true_diffs`，`#idx` 为基线 `first_diff` 下标。

| # | 文件（相对 site-packages/） | 不匹配函数 | orig→decomp | jump/true | 首个不一致点 |
|---|---|---|---|---|---|
| 1 | `fly/common/user_error.pyc` | `<module>` | 47→48 | 0/1 | #47 `None ` → `RETURN_VALUE ` |
| 2 | `IQEngine/plugins/plugin_system_accounts/api/api_stock.pyc` | `<module>` | 509→509 | 0/1 | #111 `LOAD_CONST 10` → `LOAD_CONST ` |
| 3 | `fly/common/convert.pyc` | `getchnstr` | 37→38 | 2/3 | #35 `LOAD_FAST chn_str` → `JUMP_BACKWARD 10` |
| 4 | `IQEngine/account/base_account.pyc` | `__init__` | 25→14 | 0/15 | #10 `LOAD_FAST processed_trade` → `LOAD_FAST self` |
| 5 | `IQEngine/plugins/plugin_fly_data/__init__.pyc` | `_on_before_trading_start_trading_thread` | 62→62 | 2/19 | #43 `LOAD_FAST order` → `JUMP_FORWARD 364` |
| 6 | `IQEngine/plugins/plugin_fly_data/local_variables/finance.pyc` | `__missing__` | 62→61 | 0/27 | #35 `JUMP_FORWARD 296` → `LOAD_GLOBAL Position` |
| 7 | `IQEngine/account/base_position.pyc` | `last_price` | 33→24 | 0/31 | #2 `LOAD_ATTR isnan` → `LOAD_GLOBAL np` |
| 8 | `IQEngine/data/data_proxy.pyc` | `DataProxy` | 37→33 | 0/32 | #5 `LOAD_NAME TickBar` → `LOAD_CONST <code object __init__>` |
| 9 | `IQData/utils/__init__.pyc` | `__init__` | 34→28 | 0/33 | #1 `LOAD_FAST d` → `LOAD_GLOBAL list` |
| 10 | `IQCommon/util/datetime_func.pyc` | `change_2str_of_time_2_datetime` | 63→38 | 0/33 | #30 `LOAD_GLOBAL datetime` → `LOAD_FAST endtime` |
| 11 | `IQData/utils/datetime_func.pyc` | `change_2str_of_time_2_datetime` | 63→38 | 0/33 | #30 `LOAD_GLOBAL datetime` → `LOAD_FAST endtime` |
| 12 | `IQEngine/plugins/plugin_system_accounts/position_model/future_position.pyc` | `make_trade` | 297→292 | 1/34 | #260 `JUMP_FORWARD 1442` → `LOAD_CONST ` |
| 13 | `IQEngine/plugins/plugin_system_finance/commission.pyc` | `load` | 87→84 | 1/43 | #43 `LOAD_CONST ` → `JUMP_FORWARD 302` |
| 14 | `fly/common/op_station.pyc` | `__new__` | 87→67 | 2/43 | #43 `LOAD_CONST ` → `LOAD_FAST cls` |
| 15 | `IQEngine/plugins/plugin_system_persist/json_persistance.pyc` | `persist` | 78→77 | 1/46 | #31 `LOAD_CONST ` → `JUMP_FORWARD 188` |
| 16 | `IQEngine/account/trade.pyc` | `create_trade` | 68→19 | 0/52 | #16 `JUMP_IF_TRUE_OR_POP 104` → `POP_TOP ` |
| 17 | `IQEngine/plugins/plugin_fly_data/fly_api/order_api_trade.pyc` | `order_market` | 215→215 | 4/53 | #161 `JUMP_FORWARD 850` → `LOAD_GLOBAL strategy_log` |
| 18 | `fly/common/aes_encrypt.pyc` | `code_encrypt_so` | 239→238 | 3/56 | #182 `JUMP_FORWARD 1006` → `LOAD_CONST ` |
| 19 | `IQData/entry.pyc` | `get_instance` | 149→142 | 0/59 | #90 `LOAD_GLOBAL system_log` → `LOAD_CONST ` |
| 20 | `fly/common/common.pyc` | `api_get_from_zeromq` | 255→257 | 8/59 | #195 `POP_EXCEPT ` → `LOAD_FAST message` |
| 21 | `IQEngine/account/order.pyc` | `fill` | 69→51 | 0/68 | #1 `LOAD_FAST trade` → `LOAD_FAST self` |
| 22 | `IQData/utils/profiler_func.pyc` | `<module>` | 116→112 | 0/72 | #41 `LOAD_CONST 0` → `LOAD_CONST ['LineProfiler']` |
| 23 | `IQEngine/plugins/plugin_system_persist/__init__.pyc` | `setup` | 161→163 | 4/79 | #79 `JUMP_FORWARD 630` → `LOAD_GLOBAL os` |
| 24 | `IQData/plugins/plugin_system_client_db/client_db.pyc` | `request_mysql_server` | 88→53 | 0/87 | #1 `LOAD_GLOBAL os` → `LOAD_GLOBAL context` |
| 25 | `IQCommon/logger/handlers.pyc` | `_target` | 108→98 | 2/91 | #17 `JUMP_FORWARD 252` → `LOAD_FAST stream` |
| 26 | `IQData/manager/plugin_manager.pyc` | `set_engine` | 184→184 | 4/91 | #75 `JUMP_FORWARD 790` → `LOAD_FAST plugin_config` |
| 27 | `IQEngine/core/plugin_manager.pyc` | `set_engine` | 194→194 | 4/100 | #75 `JUMP_FORWARD 832` → `LOAD_FAST plugin_config` |
| 28 | `IQEngine/plugins/plugin_system_debug/__init__.pyc` | `setup` | 115→18 | 1/109 | #6 `LOAD_CONST 0` → `LOAD_FAST config` |
| 29 | `IQData/plugins/plugin_system_db_tools/db_base.pyc` | `_get_session_maker` | 160→159 | 1/126 | #32 `POP_JUMP_FORWARD_IF_NOT_NONE 240` → `POP_JUMP_FORWARD_IF_TRUE 238` |
| 30 | `fly/oauthenticator/itn.pyc` | `authenticate` | 227→97 | 1/130 | #97 `LOAD_FAST pwd` → `None ` |
| 31 | `fly/common/future_param.pyc` | `get_future_param` | 181→184 | 2/133 | #49 `JUMP_FORWARD 314` → `POP_TOP ` |
| 32 | `IQEngine/plugins/plugin_fly_data/quote/get_stock_status.pyc` | `get_stock_status` | 177→42 | 1/146 | #31 `JUMP_FORWARD 486` → `LOAD_GLOBAL strategy_log` |
| 33 | `fly/oauthenticator/oauth2.pyc` | `post` | 188→64 | 0/154 | #20 `POP_JUMP_FORWARD_IF_NOT_NONE 990` → `POP_JUMP_FORWARD_IF_TRUE 206` |
| 34 | `IQEngine/plugins/plugin_system_event_source/default_event_source.pyc` | `events` | 510→501 | 2/156 | #352 `LOAD_FAST day` → `LOAD_FAST self` |
| 35 | `IQEngine/utils/cache_storage.pyc` | `func_wrapper` | 270→240 | 1/203 | #56 `LOAD_FAST cache_start` → `JUMP_FORWARD 266` |
| 36 | `IQEngine/core/executor.pyc` | `check_before_trading` | 243→237 | 3/215 | #24 `LOAD_CONST False` → `LOAD_FAST self` |
| 37 | `IQCommon/graph.pyc` | `_process_task_queue` | 378→354 | 1/304 | #69 `LOAD_FAST value_list` → `LOAD_FAST task_id` |

---

## 6. 最小复现运行结果

运行方式（< 60s，实测约 7s）：

```
cd .trae/specs/region-based-pyc-decompile-iteration/rounds/round_02/test_engineer/minimal_repros
D:/Python/python.exe run_repros.py
```

输出：

```
[FAIL] repro_01.py      F1   <module> 指令#4: 原='LOAD_CONST 5' 反编译='LOAD_CONST None'
[FAIL] repro_02.py      F2   DataProxy 指令#5: 原='LOAD_NAME TickBar' 反编译='LOAD_CONST <code object __init__>'
[FAIL] repro_03.py      F3   f 指令#8: 原='JUMP_IF_TRUE_OR_POP to 46' 反编译='POP_TOP'
[FAIL] repro_04.py      F3   f 指令#8: 原='JUMP_IF_TRUE_OR_POP to 46' 反编译='POP_TOP'
[FAIL] repro_05.py      F4   fill 指令#1: 原='LOAD_FAST trade' 反编译='LOAD_FAST self'
[FAIL] repro_06.py      F4   fill 指令#1: 原='LOAD_FAST trade' 反编译='LOAD_FAST self'
[FAIL] repro_07.py      F4   f 指令#1: 原='LOAD_FAST self' 反编译='LOAD_GLOBAL y'
[FAIL] repro_08.py      F5   load 指令#17: 原='JUMP_FORWARD to 132' 反编译='LOAD_CONST None'
[FAIL] repro_09.py      F5   load 指令#25: 原='JUMP_FORWARD to 198' 反编译='LOAD_CONST None'
[FAIL] repro_10.py      F6   f 指令#10: 原='JUMP_FORWARD to 32' 反编译='JUMP_FORWARD to 28'
[FAIL] repro_11.py      F7   __init__ 指令#4: 原='LOAD_FAST processed_trade' 反编译='LOAD_FAST self'
[FAIL] repro_12.py      F8   f 指令#4: 原='LOAD_CONST 0' 反编译='LOAD_CONST None'
[FAIL] repro_13.py      F8   setup 指令#5: 原='POP_JUMP_FORWARD_IF_FALSE to 182' 反编译='POP_JUMP_FORWARD_IF_FALSE to 98'
----------------------------------------------------------------------------------------------------
复现用例 总计 13   PASS 0   FAIL 13
FAIL 列表: repro_01.py ... repro_13.py
----------------------------------------------------------------------------------------------------
对照组（已知可正确往返，验证比对器不过严）共 4 个
[PASS] control_simple_assign  (对照)
[PASS] control_if_else_return (对照)
[PASS] control_try_except     (对照)
[PASS] control_aug_attr       (对照)
对照组 PASS 4/4
```

**统计**

| 指标 | 值 |
|---|---|
| 复现用例总数 | **13**（覆盖 8 个 family：F1×1、F2×1、F3×2、F4×3、F5×2、F6×1、F7×1、F8×2） |
| 复现用例 PASS / FAIL | **0 / 13**（全部成功复现出缺陷，符合预期） |
| 对照组 PASS / FAIL | **4 / 4**（比对器未过严，不是无脑 FAIL） |
| 单次运行耗时 | ≈ 7 s（要求 < 60 s） |

判定口径：递归遍历两棵 code object 树（按 `co_consts` 顺序），
对每个 code object 逐一比对 `co_code` 字节（以及 `co_names` / `co_varnames`），
**全部一致才判 PASS**。`run_repros.py` 另外打印过滤 NOP/EXTENDED_ARG/PRECALL 后的
首条指令差异，仅用于定位，不作为判定依据。

---

## 7. 优先级建议（按「修一个能翻转多少个 pyc 文件」排序）

| 优先级 | Family | 直接归因的 `bad==1` 文件 | 全部 102 partial 中的签名命中 | 修复难度 |
|---|---|---|---|---|
| **P0** | **F4** assert 前的赋值被丢弃 | order.pyc（#21） | **17 个文件 / 18 个函数**（`LOAD_FAST → LOAD_GLOBAL`） | 低（一条语句的存活判定） |
| **P0** | **F5** with/if 之后的 bare return 丢失 | commission.pyc（#13）、json_persistance.pyc（#15） | **17 个文件**（`LOAD_CONST↔JUMP_FORWARD` 两签名并集） | 低（保留显式 `return` 节点，勿并入清理块出口） |
| **P1** | **F3** 连续 `or` 短路赋值截断 | trade.pyc（#16） | 1 个（但每个命中都丢 40+ 条指令） | 中（栈深度/区域闭合判定） |
| **P1** | **F8** if 块内 import 还原失败 | plugin_system_debug（#28，115→18） | 1 个（损失最大的单点） | 中（`IMPORT_NAME` 的 level 常量栈模拟） |
| **P2** | **F1** `<call>().attr = value` 值丢失 | api_stock.pyc（#2，仅差 1 条指令） | 3 个文件 | 低（STORE_ATTR 值/对象栈序） |
| **P2** | **F7** STORE_ATTR 值为三元时截断 | base_account.pyc（#4） | 签名 `LOAD_FAST → LOAD_FAST` 命中 14 文件 | 中 |
| **P3** | **F2** 类体别名赋值丢失 | data_proxy.pyc（#8） | 1 个 | 低 |
| **P3** | **F6** for/else 与 continue 极性 | convert.pyc（#3） | 1 个 | 中 |
| — | F9（未复现） | user_error.pyc（#1）、profiler_func.pyc（#22） | 2 个 | 待定位 |

**最值得优先修的 3 个：F4 → F5 → F3。**
F4 与 F5 都是「一条语句的存活/形态判定」问题，覆盖面最广（分别 17 / 18 个文件），
且修复后能同时改善那 65 个 `bad≥2` 文件里的部分函数；
F3 虽然直接归因只有 1 个文件，但它每次触发都会抹掉几十条指令，
是 `bad≥2` 大函数 `orig ≫ decomp` 的主要贡献者之一。

---

## 8. 交付物清单

```
rounds/round_02/test_engineer/
├── decompile_report.md                 本文件
├── minimal_repros/
│   ├── run_repros.py                   批量验证器（含对照组）
│   ├── repro_01.py  ... repro_13.py    13 个最小复现
└── tmp/                                临时分析脚本与中间产物
    ├── dump_diffs.py / view.py         差异导出与查看（下标与基线对齐）
    ├── probe.py / mkcand*.py           候选模式探针
    ├── part_a.txt / part_b.txt         37 个 bad==1 文件的上下文导出
    └── table37.md                      第 5 节表格的原始数据
```
