# Round 25 反编译测试报告 — quotation.pyc (Python 3.11)

## 0. 严格执行口径与基线

- **口径**：保留 `NOP` / `EXTENDED_ARG`，仅跳过 `CACHE`；按代码对象递归做指令序列逐项比较（`opname + argval`，忽略 `co_filename` / 运行期地址）。
- **基线（r25）**：`exact = 147 / 150 = 98.00%`，差异函数 3 个：
  - `<module>`：`len_diff 1082 -> 1023 (-59)`（NOP -59，EXTENDED_ARG +1）
  - `build_future_fill_time`：`instr_diff 677 -> 677 (+0)`（5 个 JUMP_FORWARD 跳转目标错）
  - `one_prod_to_dataframe`：`len_diff 452 -> 453 (+1)`（EXTENDED_ARG +1，FOR_ITER 目标 +2）
- 反编译产物：`/tmp/r25_decompiled.py`（3673 行，stderr 空，退出码 0）。

---

## 1. 缺陷逐项分析

### 缺陷 1：`<module>` 丢失 59 个 NOP — **可豁免（非控制流缺陷）**

#### 现象
orig `<module>` 有 101 个 NOP，new 只有 42 个，差 **-59**。`<module>` 指令数 1082 -> 1023（-59），EXTENDED_ARG 63 -> 64（+1）。

#### 根因（已用 CPython 3.11 实测验证）
对 orig `<module>` 全部 59 个 NOP 做上下文 + `starts_line` 导出，发现它们聚成 **16 个簇**，**每一簇都夹在「上一个函数 `STORE_NAME prev_func`」与「下一个函数 `LOAD_CONST (defaults) + LOAD_CONST <code next_func>`」之间**，且 NOP 的 `starts_line` 是连续行号。

代表簇（节选）：

| 簇 | NOP 数 | starts_line | PREV | NEXT (下一函数) | 下一函数参数 |
|----|--------|-------------|------|-----------------|--------------|
| #0 | 7 | 422-428 | `STORE_NAME api_get_financial` | `LOAD_CONST (None×7)` @L419 → `get_kline` | 3 必需 + 7 默认 |
| #1 | 2 | 1451-1452 | `LOAD_NAME check_arg` @L1450 | `LOAD_CONST` @L1451 → `get_price` | 1 必需 + 7 默认 |
| #11 | 7 | 4519-4525 | `STORE_NAME get_market_detail_online` | `LOAD_CONST (None×7)` @L4516 → `get_klines` | 3 必需 + 7 默认 |
| #13 | 7 | 4887-4893 | `STORE_NAME get_fundamentals` | `LOAD_CONST ('range',None×6)` @L4886 → `get_fundflow_day_single` | 1 必需 + 6 默认 |
| #15 | 8 | 5153-5160 | `STORE_NAME get_industries` | `LOAD_CONST (None×2,0,0,10,'0',None,'...')` @L5153 → `get_fundflow_order_rank` | 0 必需 + 8 默认 |

**关键观察**：NOP 数 == 该函数「独占一行的默认参数」的行数。例如 `get_kline` 有 7 个默认参数（`candle_mode=None … end_date=None`），orig 源码把每个默认参数写在独立行上（行 422-428），CPython 3.11 为每个默认参数续行发一个 NOP 承载该行号（PEP 626 行号追踪，便于默认表达式求值抛错时定位）。

**实测验证**（`r25_nop_cause.py`，CPython 3.11.15）：
- 单行签名 + 默认参数：**0 NOP**
- 多行签名、无默认参数：**0 NOP**
- 多行签名 + 默认参数各占一行：**N NOP**（N = 默认参数独占行数）
- 多行 docstring：模块层不增 NOP

即：**这 59 个 NOP 全部是「多行函数签名中默认参数续行」的行号追踪 NOP，与控制流无关**。反编译器把每个函数签名重新输出成单行（语义完全等价：参数名、默认值、装饰器 `@check_arg` 数量 orig/new 一致均为 32 个、`MAKE_FUNCTION` 形态一致），所以这些续行 NOP 自然不会被重新生成。

#### 裁定
**可豁免**。不是控制流重建错误，不是语法错误；函数签名重建正确（参数/默认值/装饰器齐全），仅丢失了「多行签名续行」的行号 NOP。属反编译器排版选择（单行签名）带来的行号粒度差异，不影响可读性也不影响运行语义。若要 100% 还原，需让反编译器按 NOP 的 `starts_line` 反推原始签名换行位置并按原样输出——属美化保真度范畴，非正确性问题。

> 注：`<module>` 的 EXTENDED_ARG +1（63->64）是签名 NOP 丢失后整体偏移重排的副产物，非独立缺陷。

---

### 缺陷 2：`build_future_fill_time` 5 个 JUMP_FORWARD 跳转目标错 — **真实控制流缺陷，必须修**

#### 现象
函数指令数 677 == 677（长度相同），但 5 个 `JUMP_FORWARD` 跳转目标不同：

| idx | offset | ORIG 目标 | NEW 目标 | 含义 |
|-----|--------|-----------|----------|------|
| 229 | 1050 | **2660** | 2586 | typet==1 分支末 → orig 跳 `if total_dts:`，new 跳 `for today in trade_days:` |
| 374 | 1658 | **2660** | 2586 | typet==2 分支末 |
| 518 | 2264 | **2660** | 2586 | typet==3 分支末 |
| 565 | 2400 | **2660** | 2586 | typet==4 分支末 |
| 612 | 2536 | **2660** | 2586 | typet==13 分支末 |

ORIG 目标 2660 = `LOAD_FAST total_dts`（即 `if total_dts:` 判断块，所有 typet!=5 分支汇聚点）。
NEW 目标 2586 = `LOAD_FAST trade_days`（即 `for today in trade_days:` 循环——**完全不同的指令**）。

#### 关键字节码对照（offset 2560-2660，orig/new **完全一致**）

```
2560  LOAD_FAST    suffix                 # typet==5 else 分支：suffix 判断
2562  LOAD_CONST   ('XZCE','XDCE','XSGE')
2564  CONTAINS_OP
2566  POP_JUMP_FORWARD_IF_FALSE  to 2578
2568  BUILD_LIST  ...                     # market_time = ['10:00:00',...]
2574  STORE_FAST  market_time
2576  JUMP_FORWARD  to 2586
2578  BUILD_LIST  ...                     # else: market_time = ['10:30:00',...]
2584  STORE_FAST  market_time
2586  LOAD_FAST   trade_days              ← NEW 的 5 个 JUMP_FORWARD 落在这（错）
2588  GET_ITER
2590  FOR_ITER    to 2660
...    for today in trade_days:
...      for item in market_time:
...        total_dts.append(today + ' ' + item)
2658  JUMP_BACKWARD  to 2590
2660  LOAD_FAST   total_dts               ← ORIG 的 5 个 JUMP_FORWARD 落在这（对）
2662  POP_JUMP_FORWARD_IF_FALSE  to 2746  # if total_dts:
```

字节码布局完全相同，**唯一差异是 5 个 JUMP_FORWARD 的目标**：orig 跳过整个 typet==5 else 块（含 suffix 判断 + for 循环）直达 `if total_dts:`；new 只跳过 suffix 判断、落在 for 循环上。

#### 反编译源码错误位置（`/tmp/r25_decompiled.py` 第 360-456 行）

ORIG 应有结构：
```python
if not typet == 5:
    if typet == 1: ...; for today in trade_days: for item in trade_times: total_dts.append(...)
    elif typet == 2: ...; (同上)
    elif typet == 3: ...; (同上)
    elif typet == 4: ...; for today in trade_days: for item in market_time: ...
    elif typet == 13: ...; (同上)
else:                                   # typet == 5
    if suffix == 'T.CCFX': market_time = [...]
    elif suffix in (...): market_time = [...]
    else: market_time = [...]
    for today in trade_days:            # ← 应在 else 内部
        for item in market_time:
            total_dts.append(today + ' ' + item)
if total_dts:
    total_dts.sort(); total_dts = pandas.to_datetime(total_dts)
else:
    total_dts = pandas.to_datetime([])
return total_dts
```

NEW（反编译产物，错）实际输出：
```python
# 第 364-367 行：第一个 for 循环末尾多了一个 continue（源码级瑕疵，无字节码差异）
for item in all_days:
    if item.strftime('%Y%m%d') not in holidays:
        trade_days.append(item.strftime('%Y-%m-%d'))
    continue                              # ← 第 367 行：多余 continue（循环自然 JUMP_BACKWARD 被误判为 continue）
...
if not typet == 5:
    if typet == 1: ...
    elif typet == 2: ...
    elif typet == 3: ...
    elif typet == 4: ...
    elif typet == 13: ...
elif suffix == 'T.CCFX':                  # ← 第 442 行：错！应是 else 内嵌 if
    market_time = ['10:30:00', ...]
elif suffix in ('XZCE', 'XDCE', 'XSGE'):
    market_time = ['10:00:00', ...]
else:
    market_time = ['10:30:00', ...]
for today in trade_days:                  # ← 第 448 行：错！应在上面的 else 内部
    for item in market_time:
        total_dts.append(today + ' ' + item)
if total_dts:
    ...
```

#### 根因
反编译器把 `else:` 块尾部的 `for today in trade_days: for item in market_time: total_dts.append(...)` 循环**从 else 块中提升到 if/elif/else 同级**，使其成为所有分支汇合后的公共语句。于是 5 个 typet!=5 分支末尾的 `JUMP_FORWARD`（orig 中跳过整个 else 块到 `if total_dts:`）被错指到这个被提升的 for 循环（2586）。

**运行期后果**：当 `typet != 5` 时，typet 分支执行完自己的内嵌 for 循环后，会再次进入被提升的 `for today in trade_days: for item in market_time:` 循环，而此时 `market_time` 未定义（仅在 typet==5 的 suffix 分支中赋值）→ **`NameError: name 'market_time' is not defined`**。这是真实可触发的运行期错误，不是对齐问题。

#### 涉及区域 / 方法方向
- **区域类型**：`if/elif/.../else` 结构中，else 块体为「嵌套 if/elif/else + 尾随 for 循环」的复合块。
- **方法方向**：else 块的尾部语句（for 循环）归属判定。CFG 区域归约时，else 块的退出边应跳到 `if/else` 之后的合并点，而不是把 else 块的尾部语句当成 if/elif/else 的后续兄弟语句。需检查 `region_analyzer` / `structured_analyzer` 中 else 块边界识别：当一个块既被 else 分支 fall-through 进入、又被 if 分支的 JUMP_FORWARD 跳过时，应判定该块属于 else 体而非外部顺序语句。

#### 附：第 367 行多余 `continue`
源码级瑕疵：反编译器把 for 循环的自然 `JUMP_BACKWARD`（回 FOR_ITER）误判为显式 `continue`。该多余 `continue` 不产生字节码差异（仍编译为同一条 `JUMP_BACKWARD`），不影响严格口径，但属 AST 重建噪声，建议一并修正。

---

### 缺陷 3：`one_prod_to_dataframe` FOR_ITER +2 / EXTENDED_ARG +1 — **真实结构差异，但语义等价**

#### 现象
- 指令数 452 -> 453（+1），EXTENDED_ARG 8 -> 9（+1）。
- 首差 idx 98：`FOR_ITER to 1650`（orig）vs `to 1652`（new），仅 +2 偏移。
- 真正的结构差异在 idx 137：

| idx | ORIG | NEW |
|-----|------|-----|
| 137 | `POP_JUMP_FORWARD_IF_FALSE to 800` @632 | `EXTENDED_ARG` @632 |
| 138 | `LOAD_GLOBAL NULL+len` @634 | `POP_JUMP_FORWARD_IF_FALSE to 1634` @634 |

- ORIG idx 137：`if i == 0` 为假 → 跳 **800**（下一个 elif，近跳，1 字节可编码，无需 EXTENDED_ARG）。
- NEW idx 138：`if i == 0` 为假 → 跳 **1634**（循环末尾 `i = i+1` 处，远跳，需 EXTENDED_ARG）。

#### ORIG 结构（if/elif 链，每条都是 `i == 0 and len(v) == N`）
```
632  POP_JUMP_FORWARD_IF_FALSE  to 800     # if i==0 and len(v)==8 假 → 跳下一 elif
670  POP_JUMP_FORWARD_IF_FALSE  to 800     # (同 and 第二条件)
672  ... index.append(...)  (len==8 体)
798  JUMP_FORWARD  to 1632                 # 体末 → 跳出 if/elif 链到 i=i+1
800  ... elif i==0 and len(v)==10          # 下一 elif
...  (同理，每条 elif 的 i==0 假都跳到下一 elif 近目标)
1420 POP_JUMP_FORWARD_IF_FALSE  to 1632    # 最后一条 elif i==0 and len(v)==14 假 → 跳循环末
1632  LOAD_FAST i; ... i = i + 1           # 循环体末
```

#### NEW 结构（外层 `if i == 0:` 包裹 + 内层 if/elif，elif 仍带冗余 `i == 0 and`）
```
632  EXTENDED_ARG
634  POP_JUMP_FORWARD_IF_FALSE  to 1634    # if i==0 假 → 跳循环末（远跳，需 EXTENDED_ARG）
636  ... if len(v)==8: index.append(...)
672  POP_JUMP_FORWARD_IF_FALSE  to 802     # 内层 elif len(v)==8 假 → 下一 elif（近跳）
...  (elif 链，但每条仍带冗余 i==0 and)
1634  LOAD_FAST i; ... i = i + 1
```

#### 反编译源码（`/tmp/r25_decompiled.py` 第 263-273 行，错）
```python
elif time_index is not None:
    v = str(v)
    if i == 0:                          # ← 错：外层多包了一个 if i==0
        if len(v) == 8:
            index.append(...)
        elif i == 0 and len(v) == 10:   # ← 冗余 i==0（外层已保证）
            index.append(...)
        elif i == 0 and len(v) == 11:
            ...
        elif i == 0 and len(v) == 12:
            ...
        elif i == 0 and len(v) == 14:
            ...
```

ORIG 源码（推断）应为：
```python
elif time_index is not None:
    v = str(v)
    if i == 0 and len(v) == 8:          # ← 每条都统一带 i==0 and
        index.append(...)
    elif i == 0 and len(v) == 10:
        ...
    elif i == 0 and len(v) == 11:
        ...
    elif i == 0 and len(v) == 12:
        ...
    elif i == 0 and len(v) == 14:
        ...
```

#### 根因
反编译器对 if/elif 链中「所有分支共享同一左操作数 `i == 0`」做了**部分提取**：把第一条 `if i == 0 and len(v) == 8:` 拆成外层 `if i == 0:` + 内层 `if len(v) == 8:`，但**没有对后续 elif 做同样提取**，导致 elif 仍保留冗余 `i == 0 and`。这使外层 `if i == 0:` 的假分支目标从「下一 elif（800，近）」变成「整个链末（1634，远）」，从而需要 EXTENDED_ARG、+1 指令、FOR_ITER 目标 +2。

#### 语义等价性
- `i != 0` 时：ORIG 逐个 elif 判定 `i==0 and ...`（每条都因 `i==0` 假而跳下一 elif，最终落 1632）；NEW 外层 `if i==0` 假直接跳 1634。**结果相同：什么都不做，进 `i=i+1`**。
- `i == 0` 时：ORIG 逐 elif 判 `len(v)==N`；NEW 进外层 if 后逐 elif 判 `len(v)==N`（冗余 `i==0 and` 恒真）。**结果相同**。

**运行期行为完全一致**，无 NameError、无逻辑偏差。仅 AST 形状不同（外层多包 if + elif 留冗余条件）。

#### 裁定
**真实结构差异（语义等价）**。严格字节码口径下算差异（+1 EXTENDED_ARG、跳转目标不同），但非运行期缺陷。属 AST 重建保真度问题（`and` 复合条件部分提取不一致），优先级低于缺陷 2。建议方向：`and` 复合条件提取要么对整条 if/elif 链统一提取公共左操作数，要么不提取——避免「只提第一条」的不一致。

---

## 2. 最小复现实例清单

全部存放于 `/workspace/.trae/specs/region-reduction-quotation-10rounds-v3/rounds/round_25/test_engineer/minimal_repros/`，均 `py_compile` 通过、`pycdc.py` 反编译后用 `dis` 严格口径对比验证 **DIFF（已复现）**。验证脚本：`r25_run_repros.py`（5/5 全部复现）。

### 缺陷 2 复现（4 个）

| 文件 | 模式 | 首差 | 复现结果 |
|------|------|------|----------|
| `repro_01_buildfuture_ifelse_forloop.py` | 单 typet 分支 + else 内嵌 if/elif/else + 尾随 for | `JUMP_FORWARD 206 vs 138` | ✅ 复现 |
| `repro_02_buildfuture_multi_elif_forloop.py` | 多 typet elif 分支（各带内嵌循环）+ else 内嵌 if/elif/else + 共享 for | `JUMP_FORWARD 354 vs 286` | ✅ 复现 |
| `repro_03_buildfuture_suffix_elif_shared_forloop.py` | typet elif 链无 trailing else + else(suffix) + 共享 for | `JUMP_FORWARD 370 vs 302` | ✅ 复现 |
| `repro_05_buildfuture_minimal_else_forloop.py` | 最小化：单 if 分支 + else 内嵌 if/else + 尾随 for（仅 17 行函数体） | `JUMP_FORWARD 174 vs 106` | ✅ 复现 |

四个复现的反编译产物均呈现与真实 `build_future_fill_time` 完全相同的错误形态：else 块尾部的 `for d in days: for v in m:` 被提升到 if/elif/else 同级，typet!=5 分支的 `JUMP_FORWARD` 落在该 for 上而非 `if out:`。

### 缺陷 3 复现（1 个）

| 文件 | 模式 | 首差 | 复现结果 |
|------|------|------|----------|
| `repro_04_oneprod_compound_and_chain.py` | `if i==0 and len(v)==8: ... elif i==0 and len(v)==10: ...`（4 条统一 and 链） | `POP_JUMP_FORWARD_IF_FALSE 100 vs 380` | ✅ 复现 |

反编译产物呈现与真实 `one_prod_to_dataframe` 完全相同的错误形态：第一条 `if i==0 and len(v)==8` 被拆成外层 `if i==0:` + 内层 `if len(v)==8:`，后续 elif 保留冗余 `i==0 and`，外层假分支远跳（+EXTENDED_ARG）。

### 缺陷 1 复现
**不构造**。已用 `r25_nop_cause.py` 实测证明这 59 个 NOP 是 CPython 3.11 对「多行签名默认参数续行」的行号追踪 NOP（PEP 626），与控制流无关；反编译器单行输出签名是语义等价的排版选择，不构成可复现的控制流缺陷。

---

## 3. 真实性裁定汇总

| 缺陷 | 函数 | 类型 | 裁定 | 运行期影响 | 处理建议 |
|------|------|------|------|-----------|----------|
| 1 | `<module>` | NOP -59 | **可豁免** | 无（仅行号粒度） | 排版保真度，非正确性问题；可选改进：按 NOP `starts_line` 还原多行签名 |
| 2 | `build_future_fill_time` | 5 个 JUMP_FORWARD 目标错 | **真实缺陷，必须修** | `typet!=5` 时 `market_time` 未定义 → `NameError` | 修 else 块尾部 for 循环的归属判定（区域归约/结构化分析器） |
| 3 | `one_prod_to_dataframe` | +1 EXTENDED_ARG / 跳转目标远跳 | **真实结构差异（语义等价）** | 无（行为一致） | AST 保真度改进：`and` 复合条件提取一致性；优先级低于缺陷 2 |

### 严格口径结论
- **147/150 = 98%**（保留 NOP/EXTENDED_ARG，仅跳 CACHE）。
- 3 个差异中：**1 个真实控制流缺陷必须修（缺陷 2）**，1 个语义等价的结构差异建议修（缺陷 3），1 个非控制流的行号 NOP 损失可豁免（缺陷 1）。
- 修正缺陷 2 后预期达 148/150 = 98.7%；同时修正缺陷 3 后预期达 149/150 = 99.3%；缺陷 1 的剩余 1 个差异需多行签名排版还原方可消除，属美化范畴。

---

## 4. 关键文件路径

- 反编译产物：`/tmp/r25_decompiled.py`
- 严格口径基线脚本：`strict2_nop_check.py`
- 缺陷 1 分析：`r25_nop_context.py`（NOP 上下文导出）、`r25_nop_cause.py`（CPython 3.11 NOP 成因实测）、`r25_firstlineno.py`（函数首行号）
- 缺陷 2 分析：`r25_bfft_jumps.py`（JUMP_FORWARD/POP_JUMP 全量对照）、`r25_bfft_loop.py`（首循环 + 首差区字节码）
- 缺陷 3 分析：`r25_oneprod_diff.py`（首差 + EXTENDED_ARG 位置）、`r25_oneprod_full.py`（首差区完整字节码）、`r25_oneprod_elif.py`（elif 链结构）
- 复现验证：`r25_run_repros.py`（5/5 复现）
- 复现实例目录：`minimal_repros/repro_0[1-5]_*.py`
