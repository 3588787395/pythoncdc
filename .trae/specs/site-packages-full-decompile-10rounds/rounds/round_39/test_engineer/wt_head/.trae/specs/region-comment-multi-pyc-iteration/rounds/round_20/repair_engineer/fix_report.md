# R20 修复报告 — kwonly/*vararg 签名重建（装载器 co_kwonlyargcount 修复）

## 1. 修复概述

| 字段 | 值 |
|---|---|
| 轮次 | R20 (rcm-r20) |
| 目标 pyc | `IQCommon/logger/__init__.pyc`（22 函数，修复前 90.91% → 修复后 100%） |
| 缺陷模式 | Pattern SIG：装载器硬编码 `kw_only_arg_count=0`，致函数签名重建丢失全部 kwonly 形参、*vararg 名错取 |
| 修复文件 | `core/pyc_loader_v2.py`（`marshal_to_pyc_obj` code 分支）+ `core/cfg/region_ast_generator.py`（`_extract_function_args` docstring 同步） |
| 修复方法 | 从 code object 读取真实 `co_kwonlyargcount` / `co_posonlyargcount`，替代硬编码 0 |
| 修复前 logger/__init__.pyc | partial 90.91%（20/22，`user_print` 2 true_diffs + `<module>` 38 true_diffs） |
| 修复后 logger/__init__.pyc | **ok 100%**（22/22，0 true_diffs） |
| 修复前 repro | `def user_print(*sep):`（kwonly 丢失） |
| 修复后 repro | **12 DEFECT-REPRO 控制组全部 NO-DEFECT**（12/12） |
| 回归测试 | import 编译通过；R19 repros 11/11 NO-DEFECT 不变（零回归） |

## 2. 缺陷定位

**函数**: `user_print`（logger/__init__.pyc）+ 最小复现 `repro_01_user_print_mirror.py`

**字节码证据**（`_diag_compare_codeobj.py`，修复后）：
```
=== marshal.load user_print ===
co_varnames: ('sep', 'end', 'file', 'flush', 'args', 'message')
co_argcount: 0
co_kwonlyargcount: 4
co_flags: 0x7

=== to_python_code user_print ===
co_varnames: ('sep', 'end', 'file', 'flush', 'args', 'message')
co_argcount: 0
co_kwonlyargcount: 4
co_flags: 0x7

DIFF: varnames/argcount/kwonlyargcount/flags 全部 True
```

**根因链**：
1. `core/pyc_loader_v2.py` code 分支此前硬编码 `pyc_code.kw_only_arg_count = 0`。
2. `to_python_code()` 用该值构造 CodeType → `co_kwonlyargcount=0`。
3. `RegionASTGenerator._extract_function_args` 按 CPython 3.11+ co_varnames 布局
   （positional, kwonly, *vararg, **kwarg, locals）重建签名：`kwonly_start = arg_count = 0`，
   `kwonly_count = co_kwonlyargcount = 0` → kwonly 列表为空；`*vararg` 索引 `_next_idx = 0`，
   把 varnames[0]（`sep`）误当 `*args` → `def user_print(*sep)`，其余 kwonly 名全部丢失。
4. 签名错误传播到 `<module>`（`user_print` 的 MAKE_FUNCTION 位于模块级，其默认值/形参元组
   与常量表错配），导致 `<module>` 38 true_diffs + `user_print` 2 true_diffs。

**为何这是装载器缺陷而非区域分析缺陷**：`_extract_function_args` 的 kwonly-then-vararg
布局逻辑（L2131-2157 注释已明确遵循 CPython 3.11+ 顺序）是正确的，只是被喂了错误的
`co_kwonlyargcount=0`。区域归约算法中函数签名是父 FunctionDef 的**原子属性**（自底向上
归约时直接取用，不回溯），签名数据必须由装载器准确还原。

## 3. 修复方案

`core/pyc_loader_v2.py` code 分支，将两处硬编码 0 改为从 code object 读取真实值：

```python
# [R20 fix] kwonly/posonly arg count must be read from the code object,
# not hardcoded to 0. ...
pyc_code.pos_only_arg_count = getattr(obj, 'co_posonlyargcount', 0)
pyc_code.kw_only_arg_count = getattr(obj, 'co_kwonlyargcount', 0)
```

**安全性**：`co_posonlyargcount` / `co_kwonlyargcount` 是 CPython 3.8+/3.6+ marshaled code
对象的标准字段；`getattr(..., 0)` 对缺失字段回退 0，兼容旧版本 pyc。仅修正装载器数据
还原的正确性，不触碰任何区域识别/生成逻辑。

**算法 4 原则合规**：
- **自底向上归约**: ✓ 签名是 FunctionDef 原子属性，装载器保证归约输入准确
- **每块唯一归属**: ✓ 未改变
- **嵌套即抽象节点**: ✓ 未改变
- **入口引用语义**: ✓ 签名重建正确后，MAKE_FUNCTION 默认值（含 kw_defaults）与形参
  位置严格对齐，父引用子入口语义自动恢复

**修复后 `user_print` 签名**：
```python
def user_print(*args, sep=' ', end='', file=None, flush=None):
```

## 4. 回归测试结果

### 模块编译检查
```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator; import core.pyc_loader_v2"
OK compile
```

### 目标 pyc 验证（修复后）
```
logger/__init__.pyc: ok 100.00% (22/22 matched)
  - user_print: 100% matched
  - <module>: 100% matched（38 true_diffs → 0）
```

### 最小复现实例验证（12 个 kwonly/vararg 签名控制组）
```
12 repros: 0 DEFECT-REPRO, 12 NO-DEFECT, 0 ERROR
  - repro_01-12: user_print 镜像 + kwonly/vararg 全部组合（pos+defaults+vararg+kwonly+kwarg
    全组合、纯 kwonly、required kwonly、类方法 kwonly、kwonly+if 控制流），全部 NO-DEFECT
```

### 跨轮回归验证
- R19 minimal_repros: **11/11 NO-DEFECT**（与 R19 一致，零回归）
- R19 if-drop Defect 3 修复（with post-if/return 守卫）继续生效

### 累计成功率
| 指标 | R19 | R20 |
|---|---|---|
| cumulative_match_rate | 67.10%（308/459） | **68.61%（330/481）** |

## 5. 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀: **0 新增**
- 硬编码深度上限: **0 新增**
- 跨区域启发式: **0 新增**（修复为读取标准 code object 字段，非实例特征）
- 后处理补丁: **0 新增**
- 针对特定 pyc 的硬编码绕过: **0 新增**

## 6. docstring 更新

- `region_ast_generator.py:_extract_function_args` docstring 新增 `[R20 fix]` 段落
  （背景/问题/修复/算法合规 4 节），说明装载器数据链路对签名重建的影响。
- `core/pyc_loader_v2.py` 修复点处新增详细行内注释（[R20 fix] 段，含根因与修复说明）。

## 7. 残留问题

### 本轮修复后残留
无（logger/__init__.pyc 22/22 100% 一致）。

### 不可修复残留（与前轮一致）
- main.pyc：深度残留 failed，不阻塞前向进度。

### 下一轮建议
继续按字母序轮询下一个 pending pyc（`IQCommon/logger/handlers.pyc`，30 函数）。
Pattern SIG 已闭环，无新残留缺陷。
