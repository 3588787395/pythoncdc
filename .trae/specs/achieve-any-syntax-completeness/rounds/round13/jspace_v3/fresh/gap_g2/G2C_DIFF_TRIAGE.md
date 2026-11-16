# G2c 26 条 DIFF 分维度裁定 / 最小化 / 根因假设

- 仓库：`F:\Downloads\pythoncdc-main`，解释器 `D:/Python/python.exe`（3.11.7），cwd 固定为仓库根。
- 尺子：`tools/completeness/semantic_diff.py`（**新尺子**，递归比较嵌套 code object）
  `sha256 = d31948b3a0a4336078d3e031467fa942947c358ecc7584c5194bd389d1a9cc38`
- 冻结产品：`.trae/specs/attack-completeness-claims/rounds/round9/g2c_46/semantic_products/*.py`
  语料清单：同目录 `space_46.json`（46 条真实 pyc，module-only）。
- 判定命令（本次实测，只读产品/工具树，只写 `fresh/gap_g2/`）：

```
D:/Python/python.exe -X utf8 fresh/gap_g2/readjudicate.py \
  --space  .trae/specs/attack-completeness-claims/rounds/round9/g2c_46/space_46.json \
  --products .trae/specs/attack-completeness-claims/rounds/round9/g2c_46/semantic_products \
  --out fresh/gap_g2/g2c_readjudicate.json --workers 8 --timeout 20
```

输出末行（与简报的 3/26/17 逐字一致，**复现已成立**）：

```
{"total": 46, "verdicts": {"DIFFERENT": 26, "ERROR": 17, "EQUAL": 3}}
```

EQUAL = `REAL46-038 / 039 / 044`；17 ERROR 均为 `original artifact did not load/execute`（原件 pyc
在沙箱内无法独立装载，属环境不可判定，非产品缺陷——沿用既有登记口径）。

---

## 1. 26 条 DIFF 按维度分类

聚合口径：`diffs[].dimension`。`R1–R6` 只数 R1..R6；`LOAD`/`R0` 是装载与入口维（单独列）。
全 26 条合计：**R7 = 2276、R5 = 125、R2/R3/R4 = 各 2、R0 = 2、LOAD = 2、R1 = 0、R6 = 0**。

| 单元 | DIFF 数 | R1–R6 条数 | 仅 R7 条数 | 关键路径（首个 diff） |
|---|---:|---:|---:|---|
| REAL46-001 | 51 | 0 | 51 | `$.metadata.code.co_consts.v[47].co_code`（嵌套函数体） |
| REAL46-002 | 24 | 0 | 24 | `$.metadata.code.co_consts.v[15].co_consts.v[2].co_code` |
| REAL46-003 | 58 | 0 | 58 | `$.metadata.code.co_consts.v[10].co_code` |
| REAL46-004 | 60 | **58**（R2×1 R3×1 R4×1 R5×55） | 0 | `$.module_values.CONFORM`（LOAD 失败级联） |
| REAL46-007 | 45 | 0 | 45 | `$.metadata.code.co_consts.v[24].co_cellvars` 22→21 |
| REAL46-008 | 12 | 0 | 12 | `$.metadata.code.co_consts.v[3].co_code` |
| REAL46-011 | 18 | 0 | 18 | `$.metadata.code.co_consts.v[15].co_code` |
| REAL46-012 | 190 | 0 | 190 | `$.metadata.code.co_code`（模块体） |
| REAL46-013 | 42 | 0 | 42 | `$.metadata.code.co_consts.v[0].v`（嵌套 docstring 值） |
| REAL46-014 | 218 | 0 | 218 | `$.metadata.code.co_consts.v[40].co_code` |
| REAL46-015 | 100 | 0 | 100 | `$.metadata.code.co_consts.v[13].co_consts.v[4].co_code` |
| REAL46-016 | 143 | 0 | 143 | `$.metadata.code.co_consts.v[12].co_code` |
| REAL46-018 | 40 | 0 | 40 | `$.metadata.code.co_consts.v[16].co_consts.v[20].co_code` |
| REAL46-019 | 39 | 0 | 39 | `$.metadata.code.co_consts.v[17].co_code` |
| REAL46-022 | 136 | **9**（R5×9） | 127 | `$.metadata.code.co_code` |
| REAL46-023 | 99 | **9**（R5×9） | 90 | `$.metadata.code.co_code` |
| REAL46-024 | 7 | 0 | 7 | `$.metadata.code.co_consts.v[21].co_consts.v[5].co_code` |
| REAL46-031 | 50 | **48**（R2×1 R3×1 R4×1 R5×45） | 0 | `$.module_values.Any`（LOAD 失败级联） |
| REAL46-032 | 59 | 0 | 59 | `$.metadata.code.co_code` |
| REAL46-033 | 29 | 0 | 29 | `$.metadata.code.co_code` |
| REAL46-036 | 662 | 0 | 662 | `$.metadata.code.co_code` |
| REAL46-040 | 16 | 0 | 16 | `$.metadata.code.co_consts.v[5].co_code` |
| REAL46-041 | 4 | 0 | 4 | `$.metadata.code.co_consts.v[5].co_consts.v[10].co_code` |
| REAL46-042 | 173 | 0 | 173 | `$.metadata.code.co_consts.v[7].co_code` |
| REAL46-045 | 99 | 0 | 99 | `$.metadata.code.co_code` |
| REAL46-046 | 37 | **7**（R5×7） | 30 | `$.metadata.code.co_consts.v[64].co_code` |

（004/031 另有 `LOAD ×1` + `R0 ×1`；这两条 R2/R3/R4 是「产品装载即失败」导致 import 流缺失的级联，
不是独立的第二个行为缺陷。）

### 明确回答

**26 条中有 5 条含 R1–R6（行为差）**：`REAL46-004 / 022 / 023 / 031 / 046`；其余 **21 条只含 R7**。
没有任何一条出现 **R1（返回值）** 或 **R6（异常）** 差异；R2/R3/R4 也只出现在 004/031 的装载失败级联中。

### 5 条行为差逐条明细（维度 / 首个 diff 路径 / 前后值）

| 单元 | 维度 | 首个 diff 路径 | 原件 | 产品 |
|---|---|---|---|---|
| REAL46-004 | LOAD, R0, R2, R3, R4, R5×55 | `LOAD` → `SyntaxError` @ line 1505；随后 `$.module_values.CONFORM` | `"conform"`（enum 模块完整装载） | `null`（模块未装载，55 个全局全缺） |
| REAL46-022 | R5×9, R7×127 | `$.module_values.AnyStr.dict.v[4][1].v`（`__module__`） | `"_sd_239a7db0f5a2"` | `"_sd_295170f73959"` |
| REAL46-023 | R5×9, R7×90 | `$.module_values._const_node_type_names.len` | `8` | `7` |
| REAL46-031 | LOAD, R0, R2, R3, R4, R5×45 | `LOAD` → `TypeError: can only concatenate str (not "bool") to str`；随后 `$.module_values.Any` | `{"t":"type","v":"Any"}` | `null`（模块未装载） |
| REAL46-046 | R5×7, R7×30 | `$.module_values.GEN_DIRS.v[0].repr` | `WindowsPath('F:/.../tools/core/cfg')` | `WindowsPath('F:/.../.trae/specs/.../round9/core/cfg')` |

---

## 2. 行为差 5 条：最小复现 / 判官读数 / 根因假设

最小复现全部落在 `fresh/gap_g2/repro/`（每份 ≤15 行），统一由
`D:/Python/python.exe -X utf8 fresh/gap_g2/repro/run_min_repro.py` 实测：
`py_compile` 原件 → 现树 `pycdc.py` 反编译 → `semantic_diff`（新尺子）→ `scripts/pyc_verify.py single`。
结果 JSON：`fresh/gap_g2/repro/min_repro_results.json`。

关键读数（原样输出）：

```
REAL46-004    product_compiles=True  judge=EQUAL      artifact_control=EQUAL
REAL46-023    product_compiles=True  judge=EQUAL      artifact_control=EQUAL
REAL46-031    product_compiles=True  judge=DIFFERENT  artifact_control=EQUAL      dims={'R7': 1}
REAL46-022    product_compiles=True  judge=DIFFERENT  artifact_control=DIFFERENT  dims={'R5': 1}
REAL46-046    product_compiles=True  judge=DIFFERENT  artifact_control=DIFFERENT  dims={'R2': 1, 'R4': 1, 'R5': 4}
```

`artifact_control` = 把**与原件逐字节相同的源码**换到另一个目录再判一次（隔离观察层伪差）。

### 2.1 REAL46-004（enum.py）— 真缺陷（冻结产品），现树已修

- 触发函数：`_test_simple_enum`。源码 `enum.py:1988`
  `failed.append('%r member mismatch:\n      %s' % (name, '\n      '.join(failed_member),))`。
- 冻结产品 `semantic_products/REAL46-004.py:1505-1506` 实际输出（实测编译报错）：

```
1505: failed.append(f'{name!r} member mismatch:\n      {"""
1506:       """.join(failed_member)!s}')
$ D:/Python/python.exe -X utf8 -c "import py_compile;py_compile.compile(r'...REAL46-004.py',doraise=True)"
SyntaxError: unterminated string literal (detected at line 1505)
```

- 机制：`%` 格式被重建为 f-string，替换字段里塞进了含**真实换行**的常量 `'\n      '`（渲染成 `"""↵      """`），
  而定界符仍是单引号 `'` → 3.11 词法层在换行处截断字符串。
- 根因函数（`core/cfg/**`）：`core/cfg/code_generator.py` 的
  **`_generate_joined_str_from_dict`**（f-string 组装）→ 定界符决策
  **`_select_fstring_delimiter`**（`code_generator.py:5091`，rr-v5r78 新增）。
  该决策在「替换字段文本含真实换行/反斜杠」的形态下必须放弃单字符定界符（或退回 `format()` 拼接），
  未做此判定时必产出不可编译源码。
- 最小复现 `repro/g2c_REAL46-004_min.py`（8 行）：现树输出改为 `f'''…{"""↵      """.join(…)}'''`，
  `product_compiles=True`，判官 **EQUAL**、`pyc_verify single status=success 1/1`。
- 结论：**真缺陷，冻结产品命中**；现树因 `8df3a3f0 rr-v5r78` 的定界符选择修复而不再复现。

### 2.2 REAL46-023（ast.py）— 真缺陷（冻结产品），现树已修

- 触发点：模块级 `ast.py:581-601`：
  `_const_types = {… Ellipsis: (type(...),)}`、
  `_const_node_type_names = {bool:…, type(None): 'NameConstant', …, type(...): 'Ellipsis'}`。
- 冻结产品（同文件 538/540 行，单行压平）：

```
538: _const_types = {Num: …, NameConstant: (type(None), bool), Ellipsis: (type(None),)}
540: _const_node_type_names = {bool: 'NameConstant', type(None): 'NameConstant', … , type(None): 'Ellipsis'}
```

  `type(...)` 变成 `type(None)`，导致 `type(None)` 重复键覆盖：8 项塌成 7 项
  （判官读数 `$.module_values._const_node_type_names.len 8 → 7`，
  `$.module_values._const_types.v[1][1].v[0].v "ellipsis" → "NoneType"`）。
- 根因函数：**`core/pyc_loader_v2.py::marshal_to_pyc_obj`**。marshal 码 `'.'`（Ellipsis）没有分支，
  落到末尾 `else`（打印 unknown 后 `return None`）；下游把该 const 当 `None` 渲染。
  `PycObject.TYPE_ELLIPSIS` 的 `__str__/to_python` 早已就绪，缺的只是 loader 产物。
- 最小复现 `repro/g2c_REAL46-023_min.py`（6 行）：现树 **EQUAL**、`pyc_verify success 1/1`。
- 结论：**真缺陷，冻结产品命中**；现树因 `97ef7f87 rr-v5r85`（loader 补 `obj is ...` 分支）而不再复现。

### 2.3 REAL46-031（packaging/version.py）— 真缺陷（冻结产品），现树修了主体、留下 R7 尾巴

- 触发点：`version.py:234-240` 的模块级三元

```
VERSION_PATTERN = (
    _VERSION_PATTERN_OLD
    if (sys.implementation.name == "cpython" and sys.version_info < (3, 11, 5))
    or (sys.implementation.name == "pypy"  and sys.version_info < (3, 11, 13))
    or sys.version_info < (3, 11)
    else _VERSION_PATTERN
)
```

- 冻结产品（160-169 行）把它拆成嵌套 `if` + 裸表达式语句 + 布尔赋值：

```
160: if sys.implementation.name == 'cpython':
161:     if not sys.version_info < (3, 11, 5):
162:         if sys.version_info < (3, 11, 13):
163:             if sys.version_info < (3, 11):
164:                 pass
165:             else:
166:                 _VERSION_PATTERN          # 裸表达式，无赋值
167:         else:
168:             _VERSION_PATTERN_OLD
169:         VERSION_PATTERN = sys.implementation.name == 'pypy' and … or sys.version_info < (3, 11)
```

  于是第 263 行 `re.compile('\\s*' + VERSION_PATTERN + '\\s*')` 在**导入期**抛
  `TypeError: can only concatenate str (not "bool") to str`。
- 根因函数：**`core/cfg/region_analyzer.py::_is_ternary_block`**（三元区判定；rr-v5r84 在其内加
  `[TCX-扩展]` 条件链续接通道）。该判定在「条件链首块与**前序语句**（import/赋值）同块、
  BoolOp 走链退化为从 or 尾段起步」的形态下找不到 TernaryRegion，
  于是把条件物化成 IfRegion、把两个值块降级为裸表达式语句。
- 最小复现 `repro/g2c_REAL46-031_min.py`（13 行，or-of-ands + 三元）：
  现树三元**已正确**，但判官仍 `DIFFERENT`，**只剩 `R7 ×1`（`$.metadata.code.co_code`）**——
  产品多打了一条 `import sys`：

```
4: import sys
5: import sys          # ← 重复语句（源只有一条）
8: VERSION_PATTERN = OLD if … else NEW
```

  `pyc_verify single status=failure units=0/1`（字节级不等），但语义中性（重复 import 幂等）。
  即：rr-v5r84 修好了三元，**同族仍留下「区域入口前序语句重复发射」**（见 §4 附带发现）。
- 结论：**真缺陷，冻结产品命中**（导入期 TypeError）；现树行为已等价，规模从 48 条行为差降到 1 条 R7。

### 2.4 REAL46-022（typing.py）— 伪差异（判定器合成模块名）

- 判官路径：`$.module_values.<TypeVar>.dict.v[4][1].v`，值就是模块名：
  原件 `_sd_239a7db0f5a2` → 产品 `_sd_295170f73959`（9 个 TypeVar 各一条）。
- 机制：`semantic_runner`/`semantic_diff` 以 `_sd_<sha12(路径)>` 作为装载模块名；原件路径是
  `D:\Python\Lib\__pycache__\typing.cpython-311.pyc`，产品在仓库 `.trae/.../semantic_products/`，
  两条路径必然不同 → `TypeVar.__module__` 必然不同。`canon()` 只在 `_type_name()` 与 `repr` 里
  抹掉 `_sd_*` 前缀，**不抹裸字符串值**，于是泄漏成 R5。
- 证据（同源对照）：`repro/g2c_REAL46-022_min.py`（3 行，仅 `T = TypeVar('T')`）
  判官 `DIFFERENT dims={'R5': 1}`，且把**逐字节相同的源码**放到另一目录再判仍 `DIFFERENT dims={'R5': 1}`
  → 差异与反编译质量无关，是观察层伪差。
- 结论：**伪差异**，不计入行为缺陷。

### 2.5 REAL46-046（tools/kb/syntax_coverage.py）— 伪差异（`__file__` 锚定路径）

- 判官路径：`$.module_values.ROOT/GEN_DIRS/GEN_FILES_EXTRA/OUT` 的 `repr`，全部是
  `Path(__file__).resolve().parent` 派生值。原件 pyc 在 `F:/.../tools/kb/` → `F:/.../tools/core/...`；
  产品被写到 `.trae/specs/.../round9/semantic_products/` → 同一表达式给出 `.trae/specs/.../round9/core/...`。
- 证据（同源对照）：`repro/g2c_REAL46-046_min.py`（5 行）判官 `DIFFERENT dims={'R2':1,'R4':1,'R5':4}`，
  同源换目录对照**同样** `DIFFERENT dims={'R2':1,'R4':1,'R5':4}` → 差异完全由摆放位置决定。
- 结论：**伪差异**（评估装载位置必然差），不计入行为缺陷。既有提交 `97ef7f87` 的说明亦同此登记。

---

## 3. 伪差异清单

| 单元 | 伪差性质 | 判据 | 证据 |
|---|---|---|---|
| REAL46-022 | 判定器合成模块名 `_sd_<sha12>` 泄漏进 `__module__` | 同源换目录仍 R5 | `repro/min_repro_results.json` → `judge_identical_source_elsewhere` |
| REAL46-046 | `__file__` 锚定路径随产品摆放位置改变 | 同源换目录仍 R2/R4/R5 | 同上 |

**伪差异 2 条**（行为差 5 条中占 2 条）；真缺陷 3 条（004/023/031），且**均为冻结产品命中、现树已不再产生同样的行为破坏**。

---

## 4. 附带发现（不在 26 条内，但同族且**现树仍存活**）

削 031 时暴露的活缺陷：`or`-**两**个 and 组的三元被拆成守卫 `if not (A and B):` 并把后续语句吞进体内。

`repro/g2c_REAL46-031_side_orofands2_min.py`（7 行）：

```python
import sys
OLD = 'old'
NEW = 'new'
V = OLD if (sys.flags and sys.version_info > (3, 0)) or (sys.maxsize > 0 and sys.argv) else NEW
print('V =', V)
```

现树产品（实测）：

```python
import sys
OLD = 'old'
NEW = 'new'
if not (sys.flags and sys.version_info > (3, 0)):
    V = OLD if sys.maxsize > 0 and sys.argv else NEW
    print('V =', V)
```

运行对照：源 `V = old`，产品**什么都不打印**（`V` 未定义、`print` 被吞）。
判官 `DIFFERENT {'R5','R7','R4','R2'}`（`$.module_values.V` 原件 `"old"` → 产品 `null`；
`import stdout differs: "V = old\n" → ""`）；`pyc_verify single` → `***<module>: Failure: Different control flow`。

根因同 §2.3：`core/cfg/region_analyzer.py::_is_ternary_block` 的 `[TCX-扩展]` 续接通道只在
`len(chain_blocks) >= 2` 且链尾后继恰为 BoolOpRegion entry 时成立；两个 and 组的 or 链落入
「首段被立为独立 IfRegion、尾段被立为内层三元」的错序物化。
建议单独登记（不在本次 26 条口径内，未改任何产品代码）。

---

## 5. G2b：CORPUS402-0226（唯一 DIFF）

判定命令（同尺子，只读）：

```
D:/Python/python.exe -X utf8 fresh/gap_g2/readjudicate.py \
  --space  .trae/specs/attack-completeness-claims/rounds/round9/g2b_402/space_402.json \
  --products .trae/specs/attack-completeness-claims/rounds/round9/g2b_402/semantic_products \
  --out fresh/gap_g2/g2b_readjudicate.json --workers 12 --timeout 20
→ {"total": 402, "verdicts": {"ERROR": 342, "EQUAL": 59, "DIFFERENT": 1}}
```

（**口径更正**：本次实测为 59 EQUAL / 1 DIFF / 342 ERROR；简报的「57/1/337」三项合计 395≠402，应是笔误或另一产品集，本文以实测为准。）

- 维度构成：**仅 R7 ×2**，无任何 R1–R6：
  `$.metadata.code.co_consts.v[10].co_code`、`$.metadata.code.co_consts.v[16].co_code`。
- 产品与参考源逐字节相同（`sha256 4d30c2d2…` 同时是 c1 与 c3），说明差异不在文本层。
- 用 `dis` 对齐两处嵌套 code object，差异只是**缺少行标记 NOP**：

```
== v[10] AbstractAccount      len 110 vs 108
   delete orig[23:25] = [('NOP', None), ('NOP', None)]
== v[16] AbstractDataSource   len 147 vs 146
   delete orig[9:10]  = [('NOP', None)]
```

- 判定：**R7-only 结构差，语义中性，非行为缺陷**。这 3 条 NOP 是 CPython 3.11 为类体内
  **多行 def 签名（含位置默认值）**发射的行标记；参考源把这些签名写成单行，重编译自然不带 NOP。
  与既有 `rr-v5r107` NOPSIG 族同源（行标记占位），属「源码排版 → 字节码行标记」层差异。
- 一句话根因/定性：**产品文本正确、行为等价，仅因参考源签名排版少了 3 条签名行 NOP 而报 R7；
  不构成反编译缺陷。**

---

## 6. 复现物与命令索引

| 文件 | 用途 |
|---|---|
| `fresh/gap_g2/readjudicate.py` | 通用重判驱动（只用现尺子，不改产品） |
| `fresh/gap_g2/g2c_readjudicate.json` | 46 案全量 diffs（本次读数 3/26/17） |
| `fresh/gap_g2/g2c_classification.json` | 机器可读分类（26 条逐条维度/首差/注解） |
| `fresh/gap_g2/build_classification.py` | 由 readjudicate JSON 生成上述分类 |
| `fresh/gap_g2/g2b_readjudicate.json` | 402 案全量 diffs（59/1/342） |
| `fresh/gap_g2/repro/*.py` | 5 份最小复现 + 1 份附带发现 |
| `fresh/gap_g2/repro/run_min_repro.py` | 编译→反编译→判官→`pyc_verify single` 一键实测 |
| `fresh/gap_g2/repro/min_repro_results.json` | 上述 5 份的逐项读数（含同源对照） |

**纪律声明**：未修改 `core/`、`scripts/`、`tests/`、`tools/` 任何文件；未放宽 R7（`co_code/co_consts/co_exceptiontable`
始终受保护）；所有读数均来自本页列出的命令输出。
