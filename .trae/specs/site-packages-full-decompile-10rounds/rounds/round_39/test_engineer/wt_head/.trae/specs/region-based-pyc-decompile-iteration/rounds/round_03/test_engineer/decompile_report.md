# Round 03 — 反编译差异分析报告（测试工程师）

- 语料：site-packages 402 个 pyc（魔数 `a70d0d0a`，Python 3.11）。本轮 **partial 101 个**（函数级匹配率约 87%）。
- 运行环境：全部命令使用 `D:/Python/python.exe`（3.11.7）；默认 `python` 为 3.13，会因 marshal 不兼容报 `tuple index out of range` 假错。
- 边界：**未修改 `core/` 下任何程序代码，未修改任何 OK.py，未放宽比对判据**（仅测量与复现，修复由修复工程师完成）。
- 本轮聚焦 4 个失败复现 family：**F2 / F6 / F7 / F8**（对应 round_02 repro_02 / 10 / 11 / 13）。

---

## 0. 方法与数据来源（可复现）

1. **基线生成**：因主代理后台未生成，已自行补齐。受单命令 ≤300s 限制，`scripts/round_batch.py` 分两批运行并合并：
   - `batch_000.json`：`--offset 0 --budget 285`（68 文件）
   - `batch_001.json`：`--offset 68 --budget 285`（33 文件）
   - 合并为 `baseline/baseline_all.json`（**101 个 partial 文件全覆盖**，含每个文件的 `mismatches[].name` 与 `first_diff{index, orig_op, orig_arg, decomp_op, decomp_arg}`）。
2. **影响面扫描**：脚本 `scan_families.py` 直接读原始 pyc（`marshal + dis`），仅对**确实不匹配的函数**做字节码形状判定，按优先级 **F2 > F8 > F7 > F6** 归类：
   - **F2**：存在 `LOAD_NAME/GLOBAL/FAST X ; STORE_NAME X`（同名）别名赋值。
   - **F8**：`IMPORT_NAME` 前同一语句内有 if 守卫跳转（`POP_JUMP_FORWARD_IF_FALSE/TRUE` 等），**且首个不一致点贴近该 import（≤6 条）**。
   - **F7**：存在 `STORE_ATTR` 的值为三元（条件跳转 + `JUMP_FORWARD` 合并点），**且首个不一致点贴近该 `STORE_ATTR`（≤8 条）**。
   - **F6**：函数含 `for/while...else`（break 跳转目标 > `FOR_ITER` 耗尽目标），**且首个不一致点落在该循环字节区间内**。
   - 未归类的 279 个不匹配函数属其它 family（F1/F3/F4/F5/F9 等），不在本轮范围。
3. **复现**：`minimal_repros/` 下 11 个最小源码复现 + `run_repros.py`（`compile → decompile → compile → 递归比对全部 code object 的 co_code`）。

---

## 1. 各 Family 影响面（精确统计）

| Family | 影响文件数 | 影响函数数 | 代表函数 / 关联文件 | 首个不一致字节码（orig → decomp） |
|---|---|---|---|---|
| **F2** | **2** | **2** | `DataProxy` / `IQEngine/data/data_proxy.pyc`；`StoreCollection` / `IQEngine/plugins/plugin_fly_data/fly_api/base.pyc` | `LOAD_NAME TickBar → LOAD_CONST <code object __init__>`（idx 5） |
| **F6** | **21** *(代理)* | **40** *(代理)* | `getchnstr` / `fly/common/convert.pyc`（唯一已确认案例） | `LOAD_FAST chn_str → JUMP_BACKWARD 10`（idx 35） |
| **F7** | **3** | **3** | `__init__` / `IQEngine/account/base_account.pyc`；`__init__` / `IQData/utils/__init__.pyc`、`IQEngine/utils/__init__.pyc` | `LOAD_FAST processed_trade → LOAD_FAST self`（idx 10） |
| **F8** | **1** | **1** | `setup` / `IQEngine/plugins/plugin_system_debug/__init__.pyc` | `LOAD_CONST 0 → LOAD_FAST config`（idx 6） |

> **F6 数字说明**：21/40 是「含 `for/while...else` 且首个不一致在循环区内」的宽代理，可能混入其它循环区 bug（如 F3 孤儿语句截断）。其中**唯一已确认的 for/else 子句丢失 / continue 极性反转案例是 `convert.getchnstr`**。若仅计确证案例，F6 至少为 1 文件。

---

## 2. 各 Family 详细判定

### F2 — 类体内同名别名赋值 `X = X` 被整体丢弃

| 项 | 内容 |
|---|---|
| 代表函数 | `IQEngine/data/data_proxy.pyc` `DataProxy`（orig 37 → decomp 33，true_diffs 32） |
| 关联文件 | `data_proxy.pyc`、`plugin_fly_data/fly_api/base.pyc`（`StoreCollection`） |
| 首个不一致 | idx 5：`LOAD_NAME TickBar → LOAD_CONST <code object __init__>` |
| 根因判断 | 类体里的 `TickBar = TickBar`（源名=目标名相同）被当成「自赋值/无副作用」或重复定义折叠掉，反编译器未为这一形状生成赋值节点，直接从下一条 `def` 开始输出。`StoreCollection` 同样为 `OverNightOrderStore = OverNightOrderStore` 被丢弃。 |
| 影响面 | **2 文件 / 2 函数**（形状严格：仅同名别名赋值） |

### F6 — `for/while ... else` 子句丢失 / 循环内 `continue` 极性反转

| 项 | 内容 |
|---|---|
| 代表函数 | `fly/common/convert.pyc` `getchnstr`（orig 37 → decomp 38，jump 2 / true 3） |
| 关联文件 | `convert.pyc`（确证）；另有 20 个含 `for/while...else` 且循环区内首个不一致的文件（代理） |
| 首个不一致 | `getchnstr` idx 35：`LOAD_FAST chn_str → JUMP_BACKWARD 10`（循环内 `if A or B: continue` 被还原成相反极性，且 for/else 的 else 分支整体消失） |
| 根因判断 | 区域归约把 `for/else` 的 else 分支并入循环出口 → else 子句消失；循环体内 `if cond: continue` 被还原成相反极性（`POP_JUMP_FORWARD_IF_FALSE` 误判），多出一次 `JUMP_BACKWARD`。是**语义级错误**（循环正常结束原应返回 `None`，现在返回 `i`）。 |
| 影响面 | **代理 21 文件 / 40 函数**（含 `for/while...else` 且循环区首个不一致）；确证案例 1 文件。F6 数字偏大，需人工 triage 区分真正 for/else 丢失与其它循环区 bug。 |

### F7 — STORE_ATTR 的值为三元 `a if a is not None else f()`：该语句及后续全部丢失，末句被提升为 `return`

| 项 | 内容 |
|---|---|
| 代表函数 | `IQEngine/account/base_account.pyc` `__init__`（orig 25 → decomp 14，true 15） |
| 关联文件 | `base_account.pyc`、`IQData/utils/__init__.pyc`、`IQEngine/utils/__init__.pyc` |
| 首个不一致 | `__init__` idx 10：`LOAD_FAST processed_trade → LOAD_FAST self` |
| 根因判断 | 三元表达式两个分支各自结束于跳转（`JUMP_FORWARD` 汇合点）。区域归约把「汇合点之后」误判为不可达，或把 else 分支的值节点错挂到 `STORE_ATTR` 之外，于是三元赋值整条被丢弃；紧接着的下一条语句也被吞掉，最后一条调用被提升为 `return`（真实 OK 里 `return self.register_event()` 本应是普通调用）。**对局部标量赋三元能正确还原**，问题只在 `STORE_ATTR` 的值为三元这一形状。 |
| 影响面 | **3 文件 / 3 函数**（严格：STORE_ATTR 三元 + 首个不一致贴近该 STORE_ATTR）。注：round_02 曾用 `LOAD_FAST→LOAD_FAST` 签名给过 14 文件宽代理；本轮回严格判定为 3。 |

### F8 — if 块内 `import x` 还原失败：退化为 `x = None`、插入 `return None`、语句重排

| 项 | 内容 |
|---|---|
| 代表函数 | `IQEngine/plugins/plugin_system_debug/__init__.pyc` `setup`（orig 115 → decomp 18，true 109，**单函数损失最大**） |
| 关联文件 | `plugin_system_debug/__init__.pyc`（1 文件） |
| 首个不一致 | idx 6：`LOAD_CONST 0 → LOAD_FAST config`（import 的 level 常量 0 被吞，后续赋值被提到 import 之前并插入 `return None`，import 变不可达） |
| 根因判断 | 3.11 的 `import x` 是 `LOAD_CONST <level>; LOAD_CONST None; IMPORT_NAME; STORE_FAST` 四指令序列。常量栈模拟把 `LOAD_CONST 0`（level）与紧邻常量折叠/丢弃，`IMPORT_NAME` 拿不到 level 与 `STORE_FAST` 目标 → 退化成 `x = None`，且块被错误插入 `return None`，其后代码变不可达。 |
| 影响面 | **1 文件 / 1 函数**（严格：import-in-if 且首个不一致贴近该 import）。虽仅 1 文件，但该单函数 97 条指令被抹掉，是本轮损失最大的单点。 |

---

## 3. T2 最小复现实例与运行结果

### 3.1 复现清单（≥10 个，位于 `minimal_repros/`）

| 编号 | 关联 Family | 内容 | 来源 |
|---|---|---|---|
| repro_01.py | F2 | 类体 `TickBar=TickBar; BarData=BarData` 被丢弃 | 复用 round_02 repro_02 |
| repro_02.py | F6 | `for...else` 的 else 子句被丢弃 | 复用 round_02 repro_10 |
| repro_03.py | F7 | `STORE_ATTR` 值为三元，语句+后续丢失、末句提升 return | 复用 round_02 repro_11 |
| repro_04.py | F8 | if 块内 import 重排 + 插入 return None | 复用 round_02 repro_13 |
| repro_05.py | F6 变体 | `for...else` 带 `continue`（预期仍丢 else） | 新增 |
| repro_06.py | F6 变体 | `while...else`（验证 while/else 同族） | 新增 |
| repro_07.py | F7 变体 | `STORE_SUBSCR` 值为三元 | 新增 |
| repro_08.py | F7 变体 | `STORE_ATTR` 三元（条件用 `is None` 形式） | 新增 |
| repro_09.py | F8 变体 | if 块内 import 后跟普通赋值 | 新增 |
| repro_10.py | F8 变体 | if/elif 块内 import | 新增 |
| repro_11.py | F2 变体 | 类体单条同名别名 `X = X` | 新增 |

对照组 4 个（在 `run_repros.py` 内联，验证比对器不过严）：`control_simple_assign` / `control_if_else_return` / `control_try_except` / `control_aug_attr`。

### 3.2 运行结果

```
cd .trae/specs/region-based-pyc-decompile-iteration/rounds/round_03/test_engineer/minimal_repros
D:/Python/python.exe run_repros.py
```

```
[FAIL] repro_01.py  F2  DataProxy 指令#5: 原='LOAD_NAME TickBar' 反编译='LOAD_CONST <code object __init__>'
[FAIL] repro_02.py  F6  f 指令#10: 原='JUMP_FORWARD to 32' 反编译='JUMP_FORWARD to 28'
[FAIL] repro_03.py  F7  __init__ 指令#4: 原='LOAD_FAST processed_trade' 反编译='LOAD_FAST self'
[FAIL] repro_04.py  F8  setup 指令#5: 原='POP_JUMP_FORWARD_IF_FALSE to 182' 反编译='POP_JUMP_FORWARD_IF_FALSE to 98'
[PASS] repro_05.py  F6   (for...else + continue 变体：本形状未触发)
[PASS] repro_06.py  F6   (while...else 变体：本形状未触发)
[FAIL] repro_07.py  F7  __init__ 指令#4: 原='LOAD_FAST v' 反编译='LOAD_FAST self'
[FAIL] repro_08.py  F7  __init__ 指令#4: 原='LOAD_FAST processed_trade' 反编译='LOAD_FAST self'
[PASS] repro_09.py  F8   (if-import + 普通赋值变体：本形状未触发)
[PASS] repro_10.py  F8   (if/elif-import 变体：本形状未触发)
[FAIL] repro_11.py  F2  C 指令#5: 原='LOAD_NAME X' 反编译='LOAD_CONST <code object m>'
----------------------------------------------------------------------------------------------------
复现用例 总计 11   PASS 4   FAIL 7
FAIL 列表: repro_01.py repro_02.py repro_03.py repro_04.py repro_07.py repro_08.py repro_11.py
----------------------------------------------------------------------------------------------------
对照组（已知可正确往返，验证比对器不过严）共 4 个
[PASS] control_simple_assign  (对照)
[PASS] control_if_else_return (对照)
[PASS] control_try_except     (对照)
[PASS] control_aug_attr       (对照)
对照组 PASS 4/4
```

**统计**：复现用例 **11 个（全部目标 family 各 ≥1，且必现 FAIL ≥4）** → **FAIL 7 / PASS 4**；对照组 **PASS 4/4**（比对器未过严，非无脑 FAIL）。单次运行约 7s（< 60s）。

**观察（供修复工程师参考）**：
- F2 / F6 / F7 / F8 的「核心形状」复现（repro_01~04）全部 FAIL，确认四族 bug 稳定可复现。
- F6 的 `continue` 变体（repro_05）与 `while...else` 变体（repro_06）**PASS** → 说明 for/else 子句丢失只在「`break` 风格的 for/else」形状下触发，continue/while 形状不触发（与 convert.getchnstr 的 continue 极性反转属同一族但不同子形状）。
- F8 的「import 后跟普通赋值」（repro_09）与「if/elif import」（repro_10）**PASS** → import-in-if 的还原失败只在「import 位于带 `or`/嵌套 if 且其后有跨语句赋值」的复杂块内触发（即 repro_04 的精确形状）。
- F7 的两个变体（repro_07 `STORE_SUBSCR` 三元、repro_08 `is None` 形式）均 **FAIL** → 该缺陷不限于 `STORE_ATTR`，`STORE_SUBSCR` 值为三元同样丢失，根因是「三元赋值整条被区域归约截断」，与具体存储目标无关。

---

## 4. 优先级建议（按「修一个能翻转多少个 pyc 文件」排序）

| 优先级 | Family | 影响文件 | 影响函数 | 修复难度 | 说明 |
|---|---|---|---|---|---|
| **P0** | **F7** | 3（严）/ 14（round_02 宽代理） | 3 | 中 | **静默语义错误**：三元赋值整条丢失 + 末句被提升为 `return`，行为被改变但无报错；且变体显示 `STORE_SUBSCR` 亦受影响，覆盖面可能大于严格计数。 |
| **P1** | **F2** | 2 | 2 | 低 | 类体别名整体丢失，修复点单一（为「同名 `LOAD_NAME→STORE_NAME`」生成赋值节点）。 |
| **P2** | **F8** | 1 | 1 | 中 | 单文件但单函数损失最大（115→18），`IMPORT_NAME` 的 level 常量栈模拟需修正。 |
| **P3** | **F6** | 21（代理，确证 1） | 40（代理） | 中 | 数字最大但含混：21 是「含 for/while...else 且循环区首个不一致」的宽代理，需 triage 分离真正 for/else 丢失与其它循环区 bug。唯一确证案例 `convert.getchnstr`。 |

**本轮最优先修：`F7`**。理由：
1. 它是四族中**唯一确证的静默语义错误**（不是字节码形状差异，而是运行时行为被改变：该 return 的应是普通调用，却变成 `return`）。
2. 严格计数 3 文件、宽代理 14 文件，是「修一处即翻转多文件」性价比最高者；
3. 复现显示缺陷根因是「三元赋值整条被区域归约截断」，不限于 `STORE_ATTR`，修复后有望同时改善 `STORE_SUBSCR` 等同类形状。

> 交付物：`decompile_report.md`、`minimal_repros/repro_01..11.py`、`minimal_repros/run_repros.py`、`scan_families.py`、`baseline/baseline_all.json`、`impact_families.json`。临时分析脚本均在 `rounds/round_03/test_engineer/` 下，未触碰项目根目录与 `core/`。
