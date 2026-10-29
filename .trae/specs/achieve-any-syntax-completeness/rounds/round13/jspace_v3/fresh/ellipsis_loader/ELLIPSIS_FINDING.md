# Ellipsis 常量 loader 缺分支：`type(...)` 反编译成 `type(None)`（rr-v5r85）

状态：**已修复**（`core/pyc_loader_v2.py` +8 行 0 删除，单分支窄修）。
条目：G2c REAL46-023（stdlib `D:\Python\Lib\ast.py`），修复后 **DIFFERENT → EQUAL**。

## 缺陷

REAL46-023 语义差（1 R7 + 9 R5）的实证分解：

- `_const_node_type_names` 原 8 项、产品 7 项；产品 dict 末项
  `type(None): 'Ellipsis'` 与第二项 `type(None): 'NameConstant'` **重复键**，
  运行时后者覆盖前者 → 丢 `bool/type(None) → 'NameConstant'` 映射、
  丢 `type(...) → 'Ellipsis'` 映射（错位值 NameConstant/Ellipsis/Num/Str 全由此出）。
- `_const_types` 里 `Ellipsis: (type(None),)`——原源为 `(type(...),)`。

两处同根：**`...`（Ellipsis 常量）被渲染成 `None`**。

最小复现 `ell_repro.py`：`X = type(...)` / `Y = {type(...): 'Ellipsis'}` /
`Z = (type(...),)` → 产物全变 `type(None)`，运行输出 `<class 'NoneType'>`
vs 原 `<class 'ellipsis'>`。反编译时 stderr 直接打出冒烟枪：
`DEBUG: Unknown marshal type <class 'ellipsis'>`。

## 根因（loader 层，非 region/生成层）

`core/pyc_loader_v2.py` 的 `marshal_to_pyc_obj` 把 marshal 对象转 PycObject：
None/bool/int/float/complex/str/bytes/tuple/list/dict/frozenset/code 均有分支，
**唯独无 Ellipsis**（marshal 类型码 `'.'`）→ 落到末尾 `else` 打印 DEBUG 并
`return None` → 该 co_consts 成员变成 None 节点 → 下游按 None 渲染。

而 `core/pyc_objects.py` 的 `PycObject.TYPE_ELLIPSIS = '.'` **早已存在**且
`__str__`（渲染 `"..."`，line 107）与 `to_python`（返回 `...`，line 283）
均已就绪——只是 loader 从不产出该类型。

## 修复

`marshal_to_pyc_obj` 在 `obj is None` 分支后新增：

```python
elif obj is ...:
    return Ref(PycObject(PycObject.TYPE_ELLIPSIS))
```

精确身份判据（`is`），不与 bool/int 等类型分支交错；命中不了时逐字节不变。

## 验证（实测读数）

| 检查 | 修复前 | 修复后 |
|---|---|---|
| repro 产物 | `type(None)` ×3 + DEBUG 行 | `type(...)` ×3，无 DEBUG，运行输出与原逐字一致 |
| REAL46-023（ast.py 全模块 judge） | DIFFERENT（1 R7 + 9 R5） | **EQUAL** |
| REAL46-022 / REAL46-046 复测 | DIFFERENT（观察层 R5） | 仍 DIFFERENT，差异逐字不变（`_sd_*` 合成模块名泄漏 / `__file__` 路径锚定——观察层，另见下节） |
| pytest 7 文件 | 2 failed / 282 passed / 2 xpassed（既有 B01、BOUNDARY_02） | **2 failed / 282 passed / 2 xpassed，零新增失败** |
| 全量 1556 闸门 | 基线 `semantic_shard{0,1,2}_v5r84.json` | 见下节 |

## 全量 1556 闸门（对 v5r84 基线，三分片 offset 0/519/1038）

| 指标 | v5r84 基线 | v5r85 |
|---|---|---|
| entries | 1556 | 1556 |
| verdicts | EQUAL 1132 / ERROR 424 | EQUAL 1132 / ERROR 424 |
| 总 verdict 变化 | — | **0** |
| 回归（EQUAL→non-EQUAL） | — | **0** |
| 改善（non-EQUAL→EQUAL） | — | 0（REAL46-023 在 G2c 46 空间非 J 空间；其 EQUAL 改善见上表） |

产物：`semantic_shard{0,1,2}_v5r85.json` + `_report.json`；比对脚本
`compare_v5r85.py`（同 compare_v5r84.py 方法，基线换成 v5r84 三分片）。

## 附：G2c 剩余 R5 定性（REAL46-022/046，观察层非反编译缺陷）

用 `g2c_r5_detail.py` 取全量 R5 差异详情：

- **REAL46-046**（`tools/kb/syntax_coverage.py`）：7 条 R5 全是
  `ROOT = Path(os.environ.get('KB_ROOT') or Path(__file__).resolve().parents[2])`
  的路径值——原源跑在其原位置（`F:/.../tools`）、产品跑在 sandbox
  （`D:/temp`），同一公式不同摆放位置 → 绝对路径不同。judge 的 `_scrub`
  只归一 workdir 字符串，不归一 `__file__` 锚定值。
- **REAL46-022**：9 条 R5 全是 `_sd_<hash>` ——judge 合成模块名
  （`semantic_diff.py:511` `_sd_+path.sha[:12]`）泄漏进 TypeVar 等的
  `__module__` 观察值；原/产品路径不同 → 合成名不同。

两者字节码语义与原源一致，差异全在观察/输入模型层，**非反编译器缺陷**，
按 spec 不为非缺陷改产品码，定性关闭（与 G2b R7 同类）。

## 诚实边界

- REAL46-023 修复后为 EQUAL；不宣称 G2c 整体通过（REAL46-004 use_args、
  022/046 观察层、多条仅 R7 仍在案）；`product_complete` 仍 **NOT PASS**。
- 修复只覆盖 marshal 读取侧 Ellipsis；StopIteration 等其它冷门 marshal 码
  仍走 else（无实证样本触发，不动）。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `ell_repro.py` / `.pyc` / `ell_repro_decompiled.py` | 最小复现 + 修复后正确产物 |
| `g2c_r5_detail.py` | R5 差异详情探针（judge compare_case 全量 diffs） |
| `fix_patch.diff` | +8 行修复 diff（含根因注释） |
