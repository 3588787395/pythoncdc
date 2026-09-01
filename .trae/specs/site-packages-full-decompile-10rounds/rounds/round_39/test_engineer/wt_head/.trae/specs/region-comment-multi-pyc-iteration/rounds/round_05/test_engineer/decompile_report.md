# R05 反编译验证报告 — IQCommon/data/base_storage.pyc

## 1. 目标 pyc 信息

| 字段 | 值 |
|---|---|
| pyc 路径 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/data/base_storage.pyc` |
| 文件大小 | 1353 字节 |
| 函数数 | 5（含 `<module>` / `BaseStorage` / `__new__` / `cache_clear` / `cache_info`） |
| Python 版本 | 3.11 |
| 验证轮次 | R05 (rcm-r05) |
| 反编译产物 | `F:/Downloads/pythoncdc-main/site-packages/IQCommon/data/base_storageOK.py` (428 chars) |
| 上轮状态 | pending（未验证，按轮询规则本轮选取） |
| 本轮 R05 match_rate | **100.00%** (5/5) — 升级为 ok |

## 2. 反编译 + 字节码 diff 结果

本轮目标：按轮询规则选取下一个 `decompile_status != ok` 的 pyc（非 klinedata.pyc）。从 `pyc_index.json` 按路径字母序轮询，选取 `IQCommon/data/base_storage.pyc`（pending, function_count=5）。

执行命令：

```bash
python scripts/pyc_batch_verify.py single "F:/Downloads/pythoncdc-main/site-packages/IQCommon/data/base_storage.pyc"
```

完整输出：

```
[SINGLE] F:\Downloads\pythoncdc-main\site-packages\IQCommon\data\base_storage.pyc
  OK.py: F:\Downloads\pythoncdc-main\site-packages\IQCommon\data\base_storageOK.py
  source: 428 chars

字节码 diff 报告:
  decompile_status:   ok
  total_functions:   5
  matched_functions: 5
  match_rate:        100.00%
  missing_in_decomp: []
  extra_in_decomp:   []
```

### 修复前缺陷（Pattern M）

修复前 `base_storageOK.py` 错误输出 `@lru_cache`（无括号），丢失 `PUSH_NULL/PRECALL/CALL` 三指令：

```python
# 修复前（错误）
class BaseStorage(object):
    @lru_cache          # ← 坍缩：@lru_cache() → @lru_cache
    def __new__(cls, path):
        return super(BaseStorage, cls).__new__(cls)
```

原 pyc 字节码（`BaseStorage` 类体）含 `PUSH_NULL + LOAD_NAME lru_cache + PRECALL 0 + CALL 0`（`lru_cache()` 调用），反编译产物缺失该调用序列，导致 `__new__` 字节码不一致。

### 修复后（100% 一致）

```python
# 修复后（正确）
from IQCommon.util.pycompatibility import lru_cache
class BaseStorage(object):
    @lru_cache()        # ← 正确发射调用括号
    def __new__(cls, path):
        return super(BaseStorage, cls).__new__(cls)
    @classmethod
    def cache_clear(cls):
        cls.__new__.cache_clear()
    @classmethod
    def cache_info(cls):
        return cls.__new__.cache_info()
```

## 3. 当前 pyc 成功率

| 指标 | 修复前 | R05 修复后 | 变化 |
|---|---|---|---|
| 总函数数 | 5 | 5 | — |
| 一致函数数 | 4 | **5** | +1 |
| 当前 pyc 成功率 | 80.00% | **100.00%** | +20.00 pp |
| decompile_status | partial | **ok** | 升级 |

**结论**：Pattern M 修复（`_generate_decorator` ASTCall 始终发射调用括号）使 base_storage.pyc 达到 100% 字节码一致，升级为 ok。

## 4. 不一致函数清单（修复前 1 个，修复后 0 个）

### 修复前 — Pattern M（装饰器调用坍缩，1 函数）

| 函数名 | orig | decomp | true_diffs | 首个差异 |
|---|---|---|---|---|
| BaseStorage | 33 | 30 | 27 | 6: PUSH_NULL → LOAD_NAME 'lru_cache'（@lru_cache() 坍缩为 @lru_cache） |

> `BaseStorage` 类体的 `@lru_cache()` 装饰器被坍缩为 `@lru_cache`，丢失 `PUSH_NULL/PRECALL/CALL` 三指令（true_diffs=27 为类体后续偏移传播）。`__new__`/`cache_clear`/`cache_info` 函数体本身一致，仅类体装饰器区域不一致。

### 修复后 — 全部一致（0 不一致）

## 5. 累计成功率（跨所有已验证 pyc）

执行命令：`python scripts/pyc_batch_verify.py stats`

```
======================================================================
累计统计:
  total_pyc:             402
  verified_pyc:          17
  ok_pyc:                14
  partial_pyc:           1
  failed_pyc:            2
  total_functions:       241
  matched_functions:     135
  cumulative_match_rate: 56.02%
======================================================================
```

| 指标 | R03 累计 | R04 累计 | R05 累计 |
|---|---|---|---|
| verified_pyc | 16 | 16 | **17** |
| ok_pyc | 13 | 13 | **14** |
| partial_pyc | 1 | 1 | 1 |
| failed_pyc | 2 | 2 | 2 |
| total_functions | 236 | 236 | **241** |
| matched_functions | 129 | 130 | **135** |
| cumulative_match_rate | 54.66% | 55.08% | **56.02%** |

### 与上一轮对比

- **R04 → R05 累计 match_rate**：55.08% → 56.02%（+0.94 pp，单调递增）。
- **本 pyc 贡献**：base_storage.pyc 从 pending → ok（5/5），累计 +5 matched functions、+1 ok_pyc、+1 verified_pyc。
- **本 pyc 状态**：达到 100%，升级为 ok。

## 6. 复现实例清单

验证脚本：`minimal_repros/verify_repros.py`（函数级字节码 diff）。

共构造 12 个最小复现实例（7 Pattern M + 5 控制）。**修复前 7 DEFECT-REPRO / 5 NO-DEFECT；修复后 11 NO-DEFECT / 1 DEFECT-REPRO（repro_11 残留）**：

| # | 实例文件 | 模式 | 修复前 | 修复后 | 首个差异（修复前） |
|---|---|---|---|---|---|
| 01 | repro_01_deco_call_on_method | M-方法上 @deco() | DEFECT | **NO-DEFECT** ✓ | 5: PUSH_NULL → LOAD_NAME 'deco' |
| 02 | repro_02_deco_call_on_toplevel_func | M-顶层函数 @deco() | DEFECT | **NO-DEFECT** ✓ | 4: PUSH_NULL → LOAD_NAME 'deco' |
| 03 | repro_03_ctrl_deco_no_parens_method | CTRL-@deco 无括号方法 | NO-DEFECT | **NO-DEFECT** ✓ | — |
| 04 | repro_04_deco_call_with_arg_method | M-@deco(arg) 方法 | NO-DEFECT | **NO-DEFECT** ✓ | — |
| 05 | repro_05_deco_call_classmethod_chain | M-@deco() classmethod 链 | DEFECT | **NO-DEFECT** ✓ | 6: PUSH_NULL → LOAD_NAME 'deco' |
| 06 | repro_06_deco_call_multi_args | M-@deco(a, b) 多参 | NO-DEFECT | **NO-DEFECT** ✓ | — |
| 07 | repro_07_deco_call_kwarg | M-@deco(k=v) 关键字 | NO-DEFECT | **NO-DEFECT** ✓ | — |
| 08 | repro_08_attr_deco_call | M-@x.deco() 属性 | DEFECT | **NO-DEFECT** ✓ | 6: LOAD_METHOD → LOAD_ATTR 'deco' |
| 09 | repro_09_deco_call_on_new_classcell | M-@deco() on __new__ | DEFECT | **NO-DEFECT** ✓ | 6: PUSH_NULL → LOAD_NAME 'deco' |
| 10 | repro_10_stacked_deco_call | M-@deco1()@deco2() 堆叠 | DEFECT | **NO-DEFECT** ✓ | 5: PUSH_NULL → LOAD_NAME 'deco1' |
| 11 | repro_11_two_deco_call_stacked | M2-两个 @deco() 堆叠嵌套 | DEFECT | DEFECT（残留） | 6: LOAD_NAME 'deco1' → 'deco2'（顺序错乱） |
| 12 | repro_12_ctrl_classmethod_no_parens | CTRL-@classmethod 无括号 | NO-DEFECT | **NO-DEFECT** ✓ | — |

### Pattern M 修复验证结果

| repro | 子模式 | 修复前 | 修复后 |
|---|---|---|---|
| repro_01 | @deco() on method | DEFECT-REPRO | **NO-DEFECT** ✓ |
| repro_02 | @deco() on toplevel func | DEFECT-REPRO | **NO-DEFECT** ✓ |
| repro_05 | @deco() classmethod chain | DEFECT-REPRO | **NO-DEFECT** ✓ |
| repro_08 | @x.deco() attribute | DEFECT-REPRO | **NO-DEFECT** ✓ |
| repro_09 | @deco() on __new__ | DEFECT-REPRO | **NO-DEFECT** ✓ |
| repro_10 | @deco1()@deco2() stacked (single collapse) | DEFECT-REPRO | **NO-DEFECT** ✓ |
| repro_11 | two @deco() stacked (nesting error) | DEFECT-REPRO | DEFECT-REPRO（残留，Pattern M2） |

**6/7 Pattern M repro 修复**。repro_11 残留：触发条件是「两个零参 @deco() 堆叠」，缺陷不在装饰器渲染层（_generate_decorator），而在更早的表达式重建阶段（ExpressionReconstructor）将 `deco1()(deco2()(m))` 错误嵌套为 `deco2(deco1())(m)`。见第 7 节。

### 控制组验证（repro_03/04/06/07/12）

5 个控制组实例全部 NO-DEFECT，证实：
- repro_03：`@deco`（无括号，ASTName）→ 正确（不发射括号）
- repro_04/06/07：`@deco(args)`（有参调用，ASTCall 有 args）→ 正确（发射括号+参数）
- repro_12：`@classmethod`（无括号）→ 正确

这隔离出 Pattern M 的触发条件：**ASTCall 装饰器节点 + 零参数**。修复前 `_generate_decorator` 在 `args_code` 为空时 `return func_code`（丢括号），将 `@deco()` 坍缩为 `@deco`。

## 7. 缺陷根因分析（本轮新增）

### Pattern M — 装饰器调用坍缩（@deco() → @deco）

**触发条件**：装饰器为零参调用形式 `@deco()`（CPython 生成 `PUSH_NULL + LOAD deco + PRECALL + CALL`），AST 重建正确产出 `ASTCall(func=Name('deco'), args=[])` 节点。

**根因**：`core/cfg/code_generator.py` 的 `_generate_decorator` 方法（ASTNode 路径）在 `isinstance(node, ASTCall)` 分支中，当 `args_code` 为空时执行 `return func_code`（丢弃调用括号）。该逻辑源自历史「F08 修复：无参装饰器不加括号」，但 F08 错误地将两种语义不同的形式 conflated：
- `@deco` → ASTName 节点（无调用，1 个 CALL：deco(func) 应用）
- `@deco()` → ASTCall 节点（零参调用，2 个 CALL：先 deco() 再应用）

两者字节码不同（`@deco()` 含 `PUSH_NULL/PRECALL/CALL`，`@deco` 不含），必须通过 AST 节点类型区分渲染。ASTCall 语义即「调用」，无论是否有参数都必须发射括号 `()`。

**修复**：`_generate_decorator` 的 ASTCall 分支始终返回 `f'{func_code}({", ".join(args_code)})'`，args 为空时为 `func_code()`。ASTName/ASTAttribute 分支不变（不发射调用括号）。修复由修复工程师在 `core/cfg/code_generator.py` 实现，详见 `repair_engineer/fix_report.md`。

**最小 repro**：repro_01/02/05/08/09/10（全部修复为 NO-DEFECT）。

**实际 pyc 对应函数**：BaseStorage 类体（`@lru_cache()` 装饰器）。

**为何实际 pyc 100% 修复**：base_storage.pyc 的 `@lru_cache()` 正是 Pattern M 的标准形式（单个零参装饰器调用），修复后正确发射 `@lru_cache()`，5/5 函数全部一致。

### Pattern M2 — 堆叠装饰器嵌套错误（repro_11 残留，本轮未修复）

**触发条件**：两个零参 `@deco()` 堆叠：`@deco1() @deco2() def m`。CPython 字节码：`deco1() + deco2() + MAKE_FUNCTION + CALL(deco2()(m)) + CALL(deco1()(deco2()(m)))`。

**根因（初步定位）**：缺陷不在装饰器渲染层（`_generate_decorator` 已正确），而在更早的表达式重建阶段。调试显示，传给 `_build_function_def` 的 `decorator` 参数已被错误嵌套为 `deco2(deco1())(m)`（即 `deco1()` 被当作 `deco2` 的参数），而非正确的 `deco1()(deco2()(m))`。`_extract_decorators` 忠实地处理了这个（已错误的）Call 树，返回 `[Call(deco2, args=[Call(deco1, [])])]`，渲染为 `@deco2(deco1())`。

**待定位**：`ExpressionReconstructor` 或区域 AST 生成阶段在重建堆叠装饰器 Call 树时，将堆叠应用错误嵌套为参数传递。需下一轮深入表达式重建的 Call 树构建逻辑。

**最小 repro**：repro_11（DEFECT-REPRO 残留）。

**实际 pyc 对应函数**：base_storage.pyc 无此模式（仅单个 `@lru_cache()`），故不影响本轮 100% 结果。

## 8. 产物清单

| 产物 | 路径 |
|---|---|
| 本报告 | `.trae/specs/region-comment-multi-pyc-iteration/rounds/round_05/test_engineer/decompile_report.md` |
| 验证脚本 | `.trae/specs/.../round_05/test_engineer/minimal_repros/verify_repros.py` |
| 复现实例 01-12 | `.trae/specs/.../round_05/test_engineer/minimal_repros/repro_01_*.py` … `repro_12_*.py` |
| 验证原始输出（修复前） | `.trae/specs/.../round_05/test_engineer/_verify_repros_out_pre.txt` |
| 验证原始输出（修复后） | `.trae/specs/.../round_05/test_engineer/_verify_repros_out_post.txt` |
| 反编译 OK.py（修复后重新生成） | `site-packages/IQCommon/data/base_storageOK.py` |

## 9. pyc_index.json 更新

`scripts/pyc_batch_verify.py single` 已自动回写 base_storage.pyc 条目：
`decompile_status=ok` / `bytecode_match_rate=1.0` / `ok_py_generated=true`。
`last_tested_round` 手动补写为 5。
本 pyc 达到 100%，升级为 ok。

## 10. 约束遵守

- 未修改 `core/cfg/*` 任何代码（修复由 repair engineer 负责）。
- 未修改任何 `+OK.py` 文件（base_storageOK.py 由 single 命令生成，未手工编辑）。
- 未修改 pyc_index.json 超出 single 命令自动回写范围 + last_tested_round 补写。
- 未执行 git commit。
- 所有命令均在预算内（single ≤60s 实测 <5s，stats ≤60s 实测 <5s，repro 验证 ≤60s 实测 <10s）。
- 12 个 repro 均 ≤30 行、自包含、无业务逻辑/领域知识。
- 算法约束（bottom-up / 唯一块归属 / nested=abstract / parent ref child entry）未违反。
- 无反模式前缀新增（`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`）。
