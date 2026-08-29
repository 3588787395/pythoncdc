# Round 29 — 容器字面量构造跨越三元分支时前序元素丢失

目标：`site-packages/IQEngine/account/order.pyc::save`（匹配率 98.08%，52 函数中的 1 个）

---

## 1. 现象（实测）

`order.pyc::save` 原始函数体 **98 条指令、17 个 `MAP_ADD`**（即 17 个键值对）。
反编译产物只剩 **10 对**，前 7 对全部丢失：

| # | 键 | 状态 |
|---|---|---|
| 1–7 | `order_id` / `entrust_no` / `calendar_dt` / `trading_dt` / `symbol` / `amount` / `entrust_direction` | **丢失** |
| 8 | `futures_direction` | 保留（三元的键，值被错误重建） |
| 9–17 | 其余 | 保留 |

---

## 2. 根因（逐指令栈轨迹，实测）

对 `save()` 的指令序列做栈追踪（`trace_stack.py`）：

```
 152 MAP_ADD 1                       3->1   top=Dict(7)   ← 前 7 对累积正常
 154 LOAD_CONST 'futures_direction'  1->2   [Dict(7), key]
 156 LOAD_FAST self                  2->3   [Dict(7), key, Name(self)]
 158 LOAD_ATTR _futures_direction    3->3   [Dict(7), key, Attr]
 168 POP_JUMP_FORWARD_IF_NONE 222    3->3   [Dict(7), key, Compare]      ← 条件压栈待归约
 210 CALL 1                          5->4   [Dict(7), key, Compare, Call]
 220 JUMP_FORWARD 224                4->4   [Dict(7), key, Compare, Call]
 222 LOAD_CONST None                 4->5   [Dict(7), key, Compare, Call, None]
 224 MAP_ADD 1                       5->3   top=Dict(1)                  ← 重置！
```

根因分两层：

### 2.1 三元区域未闭合

`POP_JUMP_FORWARD_IF_NONE` 把条件包装成 `Compare(is not None)` 压回栈等待归约，
但线性扫描没有"汇合点"概念，`Compare` 永远不被消费。于是 `MAP_ADD` 弹出栈顶三个
元素时拿到的不是 Dict，`ast_generator_v2.py` 的 fallback **新建了一个空 Dict**，
前 7 对因此丢弃。

### 2.2 区域边界切断了构造序列（更根本）

区域分析器把整个 `save()` 判定为一个 `TernaryRegion`（`dump_ternary_region.py` 实测）：

```
entry / condition_block (off=0)：RESUME + BUILD_MAP 0 + k00–k07 的 8 组 key/value
                                 + POP_JUMP_FORWARD_IF_NONE 146
true_block  (off=132)：三元真分支
false_block (off=146)：LOAD_CONST None
merge_block (off=148)：MAP_ADD 1 开始，继续 k08–k16
```

`BUILD_MAP 0 … MAP_ADD …` 这条**容器构造序列被三元区域的边界切成了两半**：
condition_block 持有 dict 与前序键值对，merge_block 继续追加，两侧各归约一次，
前序键值对在边界处丢失。

按「嵌套即抽象节点」，三元应是 dict 构造内部的嵌套子节点，而不是把 dict 构造切成两段。

> 补充实测：`probe_mode.py` 证明 `use_cfg=False` 与 `use_cfg=True` 两条流水线结果一致，
> 缺陷在共用层而非某条流水线。

---

## 3. 修复（区域归约正当）

### 3.1 `core/cfg/ast_generator_v2.py` — 三元区域的开启与闭合

三元表达式在字节码里是一个两分支区域，**两条边界都由指令自身显式给出**：
假分支入口取自 `POP_JUMP_*_IF_NONE.argval`，汇合点取自真分支末尾
`JUMP_FORWARD.argval`。

- `_open_ternary_region()`：遇到 `POP_JUMP_*_IF_NONE` 时开启区域，记录条件节点与假分支入口
- `_track_ternary_region()`：见到跨过假分支入口的 `JUMP_FORWARD` 即登记汇合点；
  扫描位置抵达汇合点时闭合区域
- `_close_ternary_region()`：把栈上的 `[test, body, orelse]` 归约为 `IfExp`

闭合前做**身份校验** `test is region['test']`：条件节点必须仍是本区域开启时压入的
那个，否则说明分支内出现了其它消费，放弃归约并保持既有行为（不误改）。

判定只使用区域内部的跳转目标，不依赖跨区启发式或固定深度。

修复后栈契约恢复（实测）：`224 MAP_ADD  5->1  top=Dict(8)`。

### 3.2 `core/cfg/region_ast_generator.py` — 容器构造区域的整体归约

`_ternary_nested_in_container_construction()`：前向模拟条件块内、块末跳转之前的值栈，
**逐格标记栈中元素的来源**（栈效应复用项目既有的 `_instruction_stack_effect`，
与 assert 条件前缀切分同属"栈效应判据"族）。判据落在**栈底元素的性质**上：

- 栈深 1 → 跳转前只有条件值，是独立三元求值；
- 栈深 > 1 **且栈底是未闭合的 CONTAINER**（`BUILD_MAP/BUILD_LIST/BUILD_SET/BUILD_TUPLE`
  开启、其追加指令尚未把它消费掉）→ 跳转发生在容器构造过程中，是嵌套分支；
- 栈深 > 1 但栈底是其它表达式 → 若干独立表达式顺序求值，按既有行为处理。

命中时由 `_generate_container_construction_region()` 把区域覆盖的全部指令按 offset
顺序交表达式重建器归约为一个表达式，内部三元成为嵌套 `IfExp` 子节点。

---

## 4. 判据收紧过程（实测，两版对比）

### v1（宽判据，已废弃）
用 `dis.stack_effect` 累加条件块净栈效应，判据 `depth > 1`。

结果：**6 个文件倒退**，全量从 305 ok 跌到 301 ok，且新增 1 个 failed：

| 文件 | 基线 | v1 |
|---|---|---|
| `IQEngine/core/bar.pyc` | ok 58/58 | partial 57/58 |
| `plugin_fly_data_source/fly_data_source.pyc` | ok 70/70 | partial 69/70 |
| `fly/common/function.pyc` | ok 4/4 | **failed 0/4** |
| `fly/data/quotation.pyc` | ok 143/143 | partial 141/143 |
| `plugin_fly_data/strategy/strategy.pyc` | partial 21/24 | partial 20/24 |
| `plugin_system_risk_calculation/__init__.pyc` | partial 29/35 | partial 28/35 |

误伤根因（实测，非猜测）：

1. CPython 3.11 的 `dis.stack_effect` 对 `PRECALL` 恒返回 **-1**（真实值 0），
   对 `CALL` 恒返回 **-1**（不随参数个数变化）；`LOAD_GLOBAL` 带 push_null 标志时为 **2**。
   这些偏差使无参调用（`PRECALL 0` + `CALL 0`）累计后产生栈下溢。
2. 更关键：`depth != 1` 过宽。`bar.pyc` 的条件块在跳转前栈上确实有 2 个元素，
   但那是「`', '.join(...)` 的结果 + 条件值」——两个彼此独立的表达式顺序求值，
   **并非未闭合的容器构造**。仅看栈深无法区分这两种情形。

### v2（最终）
改为检查**栈底元素的性质**（是否为未闭合的 CONTAINER）；模拟中出现栈效应不可得
或栈下溢时一律返回 `False`，保持既有行为、绝不臆造。

修复后 6 个倒退文件全部恢复（实测：bar 58/58、fly_data_source 70/70、
function 4/4、quotation 143/143、strategy 21/24、risk_calculation 29/35）。

---

## 5. 验证数据（全部实测）

### 5.1 全量 402 pyc 回归

| 指标 | 基线（HEAD `9a5e6ff2`） | v1（宽判据） | **v2（最终）** |
|---|---|---|---|
| ok | 305 | 301 | **305** |
| partial | 97 | 100 | **97** |
| failed | 0 | 1 | **0** |
| 函数匹配 | 5424 / 5746 | 5414 / 5746 | **5424 / 5746** |

逐文件对比（`compare_results.py`）：**倒退 0 项、改善 0 项**（函数级计数）。

### 5.2 目标文件

| 指标 | 修复前 | 修复后 |
|---|---|---|
| `order.pyc` 叶子级 mismatch 函数数 | 5 | **4** |
| 其中 `save` | MISMATCH（`BUILD_MAP 0` vs `LOAD_FAST self`） | **从 mismatch 列表消失** |

### 5.3 最小复现 `repro_dict_ternary.py`

17 对字典 + 第 8 对为三元（对照真实 pyc 结构）：

| | 修复前 | 修复后 |
|---|---|---|
| 产物 | `{'k07': ... , 'k16': ...}`（前 7 对丢失） | 17 对齐全，`k07` = `self._a07 if ... else None` |
| 重编译 | 29 条指令 / 0 个 MAP_ADD | **76 条指令 / 17 个 MAP_ADD** |
| 判定 | DIFF | **BYTE-IDENTICAL** |

### 5.4 改动影响面

`impact_scan.py` 对全量 402 pyc 统计判据命中：**命中总数 1，命中文件 1/402，
即目标 `order.pyc`**。改动精准，不影响其它文件。

### 5.5 合规

- `scripts/check_patch_patterns.py` → **PASS**（无 `_fix_`/`_patch_`/`hack_` 等禁用前缀）
- `scripts/check_hardcoded_opcodes.py` → 无新增违规（报告项均为既有代码）

---

## 6. 复现命令

```bash
# 最小复现
D:/Python/python.exe repro_dict_ternary.py

# 目标文件叶子级 diff
D:/Python/python.exe diff_pyc.py F:/Downloads/pythoncdc-main/site-packages/IQEngine/account/order.pyc

# 全量回归
D:/Python/python.exe full_scan.py scan_fix29.json
D:/Python/python.exe compare_results.py scan_fix29.json scan_base29.json

# 影响面
D:/Python/python.exe impact_scan.py
```

---

## 7. 遗留（后续轮次）

`order.pyc` 仍剩 4 个 mismatch：

- **`load`**（含嵌套的 `<module>` / `Order`）：BoolOp 区域（`d['symbol'] and Engine...`）
  吞并了它前面 offset 62–104 的两条赋值语句
  （`self._calendar_dt = d['calendar_dt']`、`self._trading_dt = d['trading_dt']`）。
  首个差异：`ORIG ('LOAD_CONST','calendar_dt')` vs `RECOMP ('LOAD_CONST','symbol')`。
- **`fill`**：首个差异 `ORIG ('COPY', 1)` vs `RECOMP ('POP_TOP', None)`。
