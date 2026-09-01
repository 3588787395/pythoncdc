# R20 测试工程师报告 — IQCommon/logger/__init__.pyc（kwonly/*vararg 签名重建修复）

## 1. 本轮目标

轮询下一个 `decompile_status != ok` 的 pyc（字母序）：**`IQCommon/logger/__init__.pyc`**（22 函数）。
该 pyc 含 `user_print`（kwonly + *vararg 签名）与 `<module>`（模块级常量/函数定义），修复前
`user_print` 签名重建错误导致 2 个函数不一致（match_rate 90.91%）。

## 2. 缺陷确认（Pattern SIG: kwonly/*vararg 签名重建）

**最小复现**（`repro_01_user_print_mirror.py`，与 logger 中 `user_print` 精确同构）：
```python
def user_print(*args, sep=' ', end='', file=None, flush=None):
    message = sep.join(map(str, args)) + end
    print(message)
```

**修复前产物**（kwonly 形参全部丢失，*vararg 名错取）：
```python
def user_print(*sep):          # 正确应为 *args, sep=' ', end='', file=None, flush=None
```

**字节码定位**：
- 原 pyc `user_print` code object：`co_varnames=('sep','end','file','flush','args','message')`，
  `co_kwonlyargcount=4`，`co_flags=0x7`（CO_VARARGS|CO_VARKEYWORDS|CO_OPTIMIZED）
- 修复前 `to_python_code()` 产物：`co_kwonlyargcount=0`（装载器硬编码），导致
  `_extract_function_args` 将 kwonly_start=arg_count=0 计算为 vararg 索引=0，把第一个
  kwonly 名 `sep` 误当 *args，其余 kwonly 名全部丢弃。

**根因**：`core/pyc_loader_v2.py` `marshal_to_pyc_obj` code 分支硬编码
`kw_only_arg_count = 0` / `pos_only_arg_count = 0`，未从 code object 读取真实
`co_kwonlyargcount` / `co_posonlyargcount`。区域生成器 `_extract_function_args`
的 kwonly-then-vararg 布局逻辑（遵循 CPython 3.11+ co_varnames 顺序）本身正确，
只是收到了错误的 `co_kwonlyargcount=0` 输入。这是**装载器修复**，非区域分析补丁。

## 3. 修复后验证

```
logger/__init__.pyc: ok 100.00% (22/22 matched)
  - user_print: 100% matched（签名恢复为
    def user_print(*args, sep=' ', end='', file=None, flush=None):）
  - <module>: 100% matched（38 true_diffs → 0）
```

`to_python_code()` 与 `marshal.load` 逐字段对比（`_diag_compare_codeobj.py`）：
```
varnames match: True
argcount match: True
kwonlyargcount match: True   # 4 == 4
flags match: True            # 0x7 == 0x7
```

`__init__OK.py` 已生成（`site-packages/IQCommon/logger/__init__OK.py`），`py_compile` 通过。

## 4. 最小复现实例（12 个，kwonly/vararg 签名控制组）

| 编号 | 文件 | 类型 | 说明 | 验证 |
|---|---|---|---|---|
| 01 | repro_01_user_print_mirror.py | DEFECT-REPRO | user_print 精确镜像（kwonly + *vararg） | NO-DEFECT 3/3 |
| 02 | repro_02_kwonly_with_pos_defaults.py | DEFECT-REPRO | 位置默认值 + *vararg + kwonly 默认值 | NO-DEFECT 2/2 |
| 03 | repro_03_kwonly_only.py | DEFECT-REPRO | 纯 kwonly 参数 | NO-DEFECT 2/2 |
| 04 | repro_04_pos_and_kwonly.py | DEFECT-REPRO | 位置参数 + kwonly | NO-DEFECT 2/2 |
| 05 | repro_05_vararg_kwarg.py | DEFECT-REPRO | *vararg + **kwarg | NO-DEFECT 2/2 |
| 06 | repro_06_full_combo.py | DEFECT-REPRO | pos + pos-default + *vararg + kwonly(有/无默认) + **kwarg | NO-DEFECT 2/2 |
| 07 | repro_07_vararg_kwonly_kwarg.py | DEFECT-REPRO | *vararg + 多 kwonly + **kwarg | NO-DEFECT 2/2 |
| 08 | repro_08_defaults_vararg_kwarg.py | DEFECT-REPRO | pos 默认值 + *vararg + kwonly + **kwarg | NO-DEFECT 2/2 |
| 09 | repro_09_method_kwonly.py | DEFECT-REPRO | 类方法 kwonly 签名 | NO-DEFECT 2/2 |
| 10 | repro_10_kwonly_required.py | DEFECT-REPRO | kwonly 无默认值（required） | NO-DEFECT 2/2 |
| 11 | repro_11_kwonly_in_if.py | DEFECT-REPRO | kwonly 签名 + if 控制流 | NO-DEFECT 2/2 |
| 12 | repro_12_multi_kwonly_defaults.py | DEFECT-REPRO | 多 kwonly 默认值 | NO-DEFECT 2/2 |

`verify_repros.py` 结果：**0 DEFECT-REPRO, 12 NO-DEFECT, 0 ERROR**（全部 py_compile + 字节码逐指令一致）。

## 5. 累计成功率

| 指标 | R19 | R20 | 变化 |
|---|---|---|---|
| verified_pyc | 37 | 38 | +1（logger/__init__.pyc） |
| ok_pyc | 25 | 26 | +1 |
| partial_pyc | 11 | 11 | 持平 |
| failed_pyc | 1 | 1 | 持平（main.pyc 深度残留） |
| total_functions | 459 | 481 | +22 |
| matched_functions | 308 | 330 | +22（user_print + <module> 及其余 20 函数） |
| cumulative_match_rate | 67.10% | **68.61%** | +1.51pp |

累计成功率 68.61% ≥ R19 67.10%（单调递增，无回归）。

## 6. 跨轮回归

- R19 minimal_repros: **11/11 NO-DEFECT**（与 R19 一致，零回归）
- R19 if-drop Defect 3 修复（with post-if/return 守卫）继续生效
- import 编译：`core.cfg.region_analyzer` / `core.cfg.region_ast_generator` / `core.cfg.code_generator` / `core.pyc_loader_v2` 全部通过

## 7. 残留

- **main.pyc**：深度残留 failed，不阻塞前向进度（与前轮一致）。
- 跨轮残留 Pattern T3/T2/A2/B/C/C2/E/F/M2/G3/R 及 R15 BOOLOP-in-return 不变。
