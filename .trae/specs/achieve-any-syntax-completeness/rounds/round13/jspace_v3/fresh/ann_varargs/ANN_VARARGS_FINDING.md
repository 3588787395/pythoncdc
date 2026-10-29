# varargs（`*args`/`**kwargs`）参数注解丢失（rr-v5r87）

状态：**已修复**（`region_ast_generator.py` +33 行注解归属扩展、
`code_generator.py` +22 行两渲染路径、`ast_converter.py` +10 行透传，均只增不破）。
真实案例：G2c REAL46-031（`packaging/version.py`）`wrapper(*args: object,
**kwargs: object)` 与 `__replace__(**kwargs: Unpack[_VersionReplace])`；
修复后产品签名与源一致，R7 差 6→2（剩模块 co_code 2 字节既有非语义差）。

## 缺陷

PEP 563 下注解是 MAKE_FUNCTION flag 4 的扁平对元组
`('args','object','kwargs','object','return','object')`。反编译产物把
**可变位置/关键字形参的注解丢弃**（返回注解与普通参数注解正常）：

```python
# 源
def wrapper(*args: object, **kwargs: object) -> object: ...
def rep(self, **kwargs: Unpack[VersionReplace]) -> Self: ...
def plain(x: int, *rest: str, **opts: float) -> None: ...
# HEAD 产物
def wrapper(*args, **kwargs) -> object: ...
def rep(self, **kwargs) -> Self: ...
def plain(x: int, *rest, **opts) -> None: ...
```

最小复现 `ann_repro.py`：打印 `__annotations__`，产品侧 vararg/kwarg 条目
全缺（`{'return': 'object'}` vs 原 `{'args': 'object', 'kwargs': 'object',
'return': 'object'}`）。REAL46-031 的 co_consts 差（`v[49]` 3→2、`v[62]`
98→96，丢 `'args'`/`'kwargs'`/`'Unpack[...]'` 与注解对元组）即此。

## 根因（三处断点串联，全链实证）

探针 `ann_probe.py`→`ann_probe4.py` 逐层定位：

1. **识别端漏配**（`region_ast_generator.py:3776` 注解归属循环）：
   `_all_args = posonlyargs + args + kwonlyargs` **不含 vararg/kwarg**
   （`_extract_function_args` 产出的二者是纯字符串名，不在任何列表）→
   注解对 `(name, type)` 按名匹配无果被静默丢弃。
2. **转换端压扁**（`ast_converter.py:1722/1733` `_convert_arguments`）：
   dict 形式 vararg/kwarg 一律 `result['vararg'] = vararg.get('arg')`
   压回字符串——即使识别端产出带注解 dict 也在此丢注解（P4 探针实证：
   渲染器收到的 vararg 恒为字符串）。
3. **渲染端不发射注解**（`code_generator.py:632/661`
   `_generate_arguments_dict` 与 `6364/6422` `_generate_arguments`）：
   发射 `f'*{vararg_name}'` / `f'**{kwarg_name}'`，不查注解槽。

（`ast_generator_v2.py:4895` 另一处归属循环同样只匹配 args/kwonlyargs——
该路径是 V2 生成器备用链，本修不动它，留作后续同族。）

## 修复（三处只加不破坏）

1. 注解归属循环 for-else：按名匹配 `args.get('vararg')`/`args.get('kwarg')`
   （兼容字符串与 dict 两形态），命中时**升级为 dict 形式**
   `{'arg': name, 'annotation': type_node}`——dict 形参是下游既有约定
   （positional args 注解即 dict+annotation 槽位）；未命中时 args 原样。
2. `_convert_arguments`：带 `annotation` 的 dict vararg/kwarg **保持 dict
   透传**至 `ASTFunctionDef._vararg`；无注解 dict 维持旧压回字符串
   （逐字节不变路径）。
3. 两渲染路径补注解发射：`_generate_arguments_dict` 复用既有
   `_arg_with_annotation`（string 输入输出 `str(arg)` 与旧逐字一致）；
   `_generate_arguments` 在 dict 分支查 `annotation` 槽（PEP 563 原文优先
   `_annotation_raw_text`，与位置参数注解同法）。
4. 连带容错：`region_ast_generator.py:3992` `_b116` 幽灵 AnnAssign 过滤
   的名集装配对 dict 形参按 `.get('arg')` 取名（与 posonly/args/kwonly
   同法），防升级后的 dict 误入集失效。

## 验证（实测读数）

| 检查 | 修复前 | 修复后 |
|---|---|---|
| repro 三函数 `__annotations__` | vararg/kwarg 条目全缺 | **与原逐字一致**（3/3） |
| 变体矩阵 `va_variants.py` 8 形态 | 注解形态丢 | 1-8 全对：注解恢复、无注解/默认值/posonly/lambda 逐字节不变 |
| REAL46-031 签名 | `*args, **kwargs` / `**kwargs` 裸 | `*args: object, **kwargs: object` / `**kwargs: Unpack[_VersionReplace]` 与源一致 |
| REAL46-031 R7 差 | 6 条（含 const 丢失） | **2 条**（模块 co_code len/sha 差 2 字节，既有非语义编码差） |
| 三元回归（rr-v5r84 族） | — | repro 仍真三元、变体 5/5 preserved |
| if-早返回回归（rr-v5r86 族） | — | repro `f(-1)` 仍抛 ValueError、消息一致 |
| pytest 7 文件 | 2 failed / 282 passed / 2 xpassed（既有 B01、BOUNDARY_02） | **2 failed / 282 passed / 2 xpassed，零新增失败** |
| 全量 1556 闸门 | 基线 `semantic_shard{0,1,2}_v5r86.json` | 见下节 |

## 全量 1556 闸门（对 v5r86 基线，三分片 offset 0/519/1038）

| 指标 | v5r86 基线 | v5r87 |
|---|---|---|
| entries | 1556 | 1556 |
| verdicts | EQUAL 1132 / ERROR 423 / None 1 | EQUAL 1132 / ERROR 424 |
| 总 verdict 变化 | — | **1（抖动记录恢复真值）** |
| 回归（EQUAL→non-EQUAL） | — | **0** |
| 改善（non-EQUAL→EQUAL） | — | 0（REAL46-031 在 G2c 46 空间非 J 空间；其 R7 6→2 见上表） |

唯一变化 `JS-GENEXP-020 None→ERROR`：v5r86 基线中该条是并发负载超时
抖动产生的 `NO_C4`（rr-v5r86 已登记排除，单条复跑真值为 ERROR）；本轮
闸门无并发干扰，恢复为 ERROR——与 v5r85 基线及复跑真值逐字一致。
**最终读数：EQUAL 1132=1132，0 回归。**

产物：`semantic_shard{0,1,2}_v5r87.json` + `_report.json`；比对脚本
`compare_v5r87.py`（同前法，基线换 v5r86 三分片）。

## 诚实边界

- REAL46-031 仍 DIFFERENT（模块 co_code 差 2 字节在案，属另一族编码差）；
  不宣称 G2c 通过（REAL46-004 use_args、022/046 观察层、13 条仅 R7 在案）；
  `product_complete` 仍 **NOT PASS**。
- `ast_generator_v2.py` 备用路径的同名归属循环未修（非主链，无产品实证）；
  如后续该路径承载真实案例再开同族任务。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `ann_repro.py` / `.pyc` / `ann_repro_decompiled.py` | 最小复现 + 修复后正确产物（`__annotations__` 逐字一致） |
| `va_variants.py` | 8 形态变体矩阵（注解/无注解/混合/默认值/posonly/lambda） |
| `ann_probe.py`–`ann_probe4.py` | 四层定位探针：注解元组形态 → 节点 args 升级 → 双调用路径区分 → 渲染器输入实证 |
| `fix_patch.diff` | 三文件修复完整 diff（含判据注释） |
