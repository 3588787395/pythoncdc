# 产物可复现性修复报告（PYTHONHASHSEED 非确定性）

日期：2026-08-30
基线提交：`0ef8e88b`（305 ok / 97 partial / 0 failed）

---

## 1. 问题：反编译产物不可复现

同一份代码、同一个 pyc、同一台机器，**仅改变 `PYTHONHASHSEED` 就会产出不同的源码**。

### 1.1 实测方法

`PYTHONHASHSEED` 必须在进程启动前设定，无法在同进程内切换，故采用跨进程扫描：

```
PYTHONHASHSEED=<s> D:/Python/python.exe nondet_scan.py <s> 305
```

对 `pyc_index.json` 中全部 305 个 `ok` 文件逐个反编译，记录产物 md5，跨 seed 比对。
seed 取值：`0 / 1 / 2 / 3 / 7`。

### 1.2 修复前实测数据

| 指标 | 数值 |
|---|---|
| 样本（ok 文件） | 305 |
| 产物种类 = 1（完全稳定） | 296 个（97.0%） |
| 产物种类 = 5（每个 seed 都不同） | **9 个（3.0%）** |
| **不可复现率** | **3.0%** |

9 个受影响文件：

```
site-packages/IQCommon/arg_checker.pyc
site-packages/IQCommon/const.pyc
site-packages/IQCommon/logger/__init__.pyc
site-packages/IQData/utils/arg_checker.pyc
site-packages/IQData/utils/logger/logger.pyc
site-packages/IQEngine/const.pyc
site-packages/IQEngine/plugins/plugin_system_trade/enums.pyc
site-packages/IQEngine/utils/arg_checker.pyc
site-packages/fly/data/quotation.pyc
```

### 1.3 差异归因

对 9 个文件取 seed=0/1/2 三组产物做逐行 diff：

| 文件 | diff 行 | 总行数 | 是否仅为字面量元素顺序 |
|---|---:|---:|---|
| `IQCommon/arg_checker.py` | 1 | 326 | YES |
| `IQCommon/const.py` | 2 | 422 | YES |
| `IQCommon/logger/__init__.py` | 1 | 165 | YES |
| `IQData/utils/arg_checker.py` | 1 | 293 | YES |
| `IQData/utils/logger/logger.py` | 1 | 431 | YES |
| `IQEngine/const.py` | 1 | 330 | YES |
| `IQEngine/.../enums.py` | 4 | 145 | YES |
| `IQEngine/utils/arg_checker.py` | 1 | 320 | YES |
| `fly/data/quotation.py` | 5 | 3764 | YES |
| **合计** | **17** | | **17 / 17 = 100.0%** |

样例：

```
seed0: valid = isinstance(value, six.string_types) and value[-1] in ('d', 'y', 'q', 'm')
seed1: valid = isinstance(value, six.string_types) and value[-1] in ('y', 'd', 'q', 'm')
seed2: valid = isinstance(value, six.string_types) and value[-1] in ('y', 'q', 'm', 'd')

seed0: NULL_SET = {'', 'null', 'NULL', None, 'None'}
seed1: NULL_SET = {'', None, 'null', 'NULL', 'None'}
```

**结论：零结构性差异，100% 是集合/元组字面量的元素顺序。**

---

## 2. 根因

`set` / `frozenset` 的迭代顺序由元素哈希决定，而 CPython 默认启用哈希随机化
（`PYTHONHASHSEED`）。反编译器在多处**直接遍历集合常量**来构造 AST 或渲染源码，
于是把逐进程变化的哈希顺序泄漏进了产物。

真正的**根源在加载阶段**，而非渲染阶段：

```python
# core/pyc_loader_v2.py:57-61（修复前）
elif isinstance(obj, frozenset):
    result = PycSequence(PycObject.TYPE_FROZENSET)
    result._values = [marshal_to_pyc_obj(item, module) for item in obj]   # ← 顺序在此丢失
```

原始 pyc 里的 frozenset 常量在这一步被展开成 `PycSequence._values`，
**顺序当场丢失**，后续所有渲染路径都只能继承这个随机顺序。
仅改渲染层（code_generator）无效——实测已证实：先改了 7 处渲染点后
`arg_checker` 仍在 3 个 seed 下产生 3 种结果，直到改掉加载器才归零。

---

## 3. 安全性论证：为什么排序不会破坏字节一致性

关键疑问：集合字面量若以 `BUILD_SET` 逐元素构建，元素顺序会影响指令顺序，
排序就可能破坏字节一致性。

**实测反驳**——原始字节码形态：

```
 94 BUILD_SET                    0
 96 LOAD_CONST                   frozenset({'513030.XSHG', '513500.XSHG', ...})
 98 SET_UPDATE                   1
100 STORE_NAME                   't0_symbol_set'
```

源码的集合字面量在**编译期已被折叠为 frozenset 常量**，书写顺序在 pyc 内
**根本不存在、不可恢复**。重编译时同样折叠为 frozenset，而 `frozenset` 的
相等性与元素顺序无关。因此：

- 元素顺序对重编译后的 `(opname, argval)` 序列**无影响**；
- 这 9 个文件顺序乱变却始终保持 `ok` 状态，正是该结论的实证。

---

## 4. 修复

新增统一工具（`core/ast_nodes.py`，两个流水线共用）：

```python
def ordered_const_items(container):
    items = list(container)
    try:
        items.sort(key=lambda v: (type(v).__name__, repr(v)))
    except Exception:
        try:
            items.sort(key=repr)
        except Exception:
            pass
    return items
```

排序键取 `(类型名, repr)` 而非直接 `sorted()`：混合类型集合
（如 `{'', 'null', 'NULL', None, 'None'}`）直接排序会因 `None` 与 `str`
不可比较而抛 `TypeError`。

应用到全部 6 个集合遍历点：

| 文件 | 位置 | 说明 |
|---|---|---|
| `core/pyc_loader_v2.py` | 57-61 | **根源**：加载期展开 frozenset |
| `parsers/ast_builder.py` | 7538 | SET_UPDATE 构造 ASTSet |
| `parsers/ast_builder.py` | 10147 | LOAD_CONST frozenset → ASTSet |
| `core/cfg/ast_generator_v2.py` | 772 | SET_UPDATE（CFG 流水线） |
| `core/cfg/ast_generator_v2.py` | 24471 | SET_UPDATE（CFG 流水线） |
| `core/cfg/code_generator.py` | 3597-3598 | frozenset 渲染 |
| `core/cfg/code_generator.py` | 3900-3903 | set / frozenset 渲染 |

空集合保持输出 `set()`（而非 `{}`，后者语义是空 dict）。

改动量：**5 个文件，+69 / −9 行**。无 `_fix_` / `_patch_` / `_hack_` 前缀，
无跨区启发式、无硬编码深度。

---

## 5. 修复后实测数据

### 5.1 复现性（同 5 个 seed 全量重测）

| 指标 | 修复前 | 修复后 |
|---|---:|---:|
| 产物种类 = 1 | 296（97.0%） | **305（100.0%）** |
| 产物种类 = 5 | 9（3.0%） | **0** |
| **不可复现率** | **3.0%** | **0.00%** |

单点验证（`IQCommon/arg_checker.pyc`）：

```
修复前: seed0=('d','y','q','m') seed1=('y','d','q','m') seed2=('y','q','m','d')  md5 各不相同
修复后: seed0=seed1=seed2=('d','m','q','y')  md5 5698dfe855fa（三次一致）
```

副产品：排序后顺序恰好还原为源码书写顺序 `('d','m','q','y')`，
与仓库中已提交版本一致，故该文件不再产生 diff 噪声。

### 5.2 全量回归（402 pyc）

| 指标 | 基线 `0ef8e88b` | 修复后 |
|---|---:|---:|
| ok | 305 | **305** |
| partial | 97 | **97** |
| failed | 0 | **0** |
| 函数通过 | — | 5424 / 5746 |

**零回归。**

### 5.3 产物变化核验

15 个 `*OK.py` 变化（因为此前提交的版本本身就带着某个随机 seed 的顺序）：

| 差异性质 | 行数 | 占比 |
|---|---:|---:|
| 集合/元组元素顺序 | 27 | 77.1% |
| 嵌套元组集合顺序 | 8 | 22.9% |
| 语义改变 | **0** | **0%** |

8 行嵌套集合（3 个 `trade_scheduleOK.py` 的 `STOCK_SCHEDULE` /
`FUTURE_SCHEDULE` / `OPTION_SCHEDULE` / `HKS_SCHEDULE`）已用
`ast.literal_eval` 严格验证**元素集合完全相等**：

```
STOCK_SCHEDULE   old=240  new=240  元素集合完全相等
FUTURE_SCHEDULE  old=285  new=285  元素集合完全相等
STOCK_SCHEDULE   old=240  new=240  元素集合完全相等
FUTURE_SCHEDULE  old=285  new=285  元素集合完全相等
STOCK_SCHEDULE   old=240  new=240  元素集合完全相等
FUTURE_SCHEDULE  old=285  new=285  元素集合完全相等
OPTION_SCHEDULE  old=240  new=240  元素集合完全相等
HKS_SCHEDULE     old=330  new=330  元素集合完全相等
```

---

## 6. 遗留与建议

- 修复只覆盖**集合常量**这一条非确定性路径。理论上仍可能存在其他依赖
  `set` 迭代顺序的**算法层**逻辑（region 分析中大量使用 `frozenset` 做集合
  运算，但集合运算不涉及迭代顺序，故风险低）。若后续再观察到状态抖动，
  可用同一套 `nondet_scan.py` 快速定位。
- 建议：批量回归命令统一加 `PYTHONHASHSEED=0`，做到"即使存在未发现的非
  确定性源也能复现"的双保险。
- 本次修复未新增任何 ok 文件（非正确性缺陷，而是**可复现性**缺陷），
  但消除了 3.0% 的产物抖动，使 `ok/partial` 判定不再随机漂移。

---

## 7. 复现命令

```bash
cd F:/Downloads/pythoncdc-main
D=/.trae/specs/region-based-pyc-decompile-iteration/rounds/round_06/test_engineer

# 5 个 seed 全量扫描（约 80s/seed）
for s in 0 1 2 3 7; do
  PYTHONHASHSEED=$s D:/Python/python.exe $D/nondet_scan.py $s 305
done

# 归因分析
PYTHONHASHSEED=0 D:/Python/python.exe $D/dump_variants.py 0
PYTHONHASHSEED=1 D:/Python/python.exe $D/dump_variants.py 1
PYTHONHASHSEED=2 D:/Python/python.exe $D/dump_variants.py 2
D:/Python/python.exe $D/analyze_variants.py 2
```
