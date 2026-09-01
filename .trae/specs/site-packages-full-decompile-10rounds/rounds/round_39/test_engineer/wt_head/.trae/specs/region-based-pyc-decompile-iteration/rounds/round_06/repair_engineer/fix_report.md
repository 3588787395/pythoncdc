# Round 06 — G6 `is not None` 条件语义修复

**日期**: 2026-08-29
**轮次负责人**: Agent (region-based reduction)
**修复文件**: `core/cfg/region_ast_generator.py`（`_generate_boolop` 内 R89 内联 if 提取路径）
**目标 pyc**: `site-packages/IQData/plugins/plugin_system_db_tools/db_base.pyc`（`parse_db_url` 形态）
**净结果**: 304 ok / 98 partial（与基线一致，零确定性回归）

---

## 1. 问题家族 (G6)

`x = a or b` 之后紧跟 `if x is not None:`（或 `is None`）的条件判断。当 or-赋值与 if 条件共享
同一个 BoolOpRegion 的 merge block 时，R89 启发式会把 trailing 条件跳转吞掉，重建成内联 if。

原始字节码（CPython 3.11，`a70d0d0a`）用 `POP_JUMP_IF_NONE` / `POP_JUMP_IF_NOT_NONE`
（归入 `NONE_CHECK_OPS`）表达 `x is None` / `x is not None`，重编译应还原为对应的 `is None` /
`is not None` 比较。

## 2. 根因

R89 内联 if 提取的通用路径把条件重建成裸值再做真值测试：

```python
_if_negate_r89 = ('TRUE' in _cond_jump_r89.opname or 'NONE' in _cond_jump_r89.opname)
_test_r89 = _cond_expr_r89
if _if_negate_r89:
    _test_r89 = _negate_expr(_cond_expr_r89)
# ...
'orelse': [],          # else 分支被硬编码丢弃
```

对 `NONE_CHECK_OPS` 跳转，这会把 `if x is not None:` 错误退化为 `if not x:`
（裸值取反），并且**丢弃了 `else:` 分支**，导致反编译产物重编译后字节码非逐字节一致
（`POP_JUMP_FORWARD_IF_NONE` → `POP_JUMP_FORWARD_IF_TRUE`，且 else 体丢失）。

最小复现（`test_engineer/repro_parsedb.py`）：

```python
DB_DEFAULT_DRIVER = {}
def parse_db_url(config):
    dialect = config.pop('dialect', 'mysql')
    driver = config.pop('driver', None) or DB_DEFAULT_DRIVER.get(dialect)
    if driver is not None:
        agreement = '{}+{}'.format(dialect, driver)
    else:
        agreement = dialect
    return agreement
```

修复前反编译输出 `if not driver:`（错误），修复后 `if driver is not None:`（字节一致）。

## 3. 修复方案（区域归约正当，无 `_fix_`/`_patch_`/`_hack_` 前缀）

仅对 `NONE_CHECK_OPS` 跳转做专门处理，通用路径保持 `orelse: []` 不变（兼容性）：

1. **重建比较节点**：用 `Compare(left, ops=[Is|IsNot], comparators=[None])` 表达 `is None` / `is not None`。
2. **正确极性**：跳转命中 then 分支当且仅当（`NOT_NONE` 跳转命中 then）。统一判据：
   - `POP_JUMP_IF_NONE`：测试为 `is None` ⟺ 跳转命中 then
   - `POP_JUMP_IF_NOT_NONE`：测试为 `is None` ⟺ 跳转**未**命中 then
3. **按需生成 else**：仅当 then 块不以显式跳转绕开 else（即 else 是独立分支、父级块语句循环不会自然发射）时，
   才在 if 内生成 `orelse`，并标记该块已生成以避免重复发射。

```python
_else_body_r89 = []
if _cond_jump_r89.opname in NONE_CHECK_OPS:
    _jump_goes_to_then_r89 = (
        _then_blk_r89 is not None
        and self.cfg.get_block_by_offset(_cond_jump_r89.argval) is _then_blk_r89)
    _test_is_none_r89 = (
        _jump_goes_to_then_r89
        if 'NOT_NONE' not in _cond_jump_r89.opname
        else (not _jump_goes_to_then_r89))
    _test_r89 = {
        'type': 'Compare',
        'left': _cond_expr_r89,
        'ops': [{'type': 'Is' if _test_is_none_r89 else 'IsNot'}],
        'comparators': [{'type': 'Constant', 'value': None}],
    }
    if (_else_blk_r89 is not None and _then_blk_r89 is not None):
        _then_falls_into_else = _else_blk_r89 in getattr(_then_blk_r89, 'successors', ())
        if not _then_falls_into_else:
            _else_body_r89 = self._generate_block_statements(_else_blk_r89)
            self.generated_blocks.add(_else_blk_r89)
            self.generated_offsets.add(_else_blk_r89.start_offset)
elif _if_negate_r89:
    _test_r89 = _negate_expr(_cond_expr_r89)
```

## 4. 验证

### 4.1 最小复现集（`test_engineer/repros_round6.py`）

| 变体 | 结果 |
|------|------|
| parsedb (`or` 默认赋值 + `if is not None` + else) | BYTE-IDENTICAL |
| isnone (`if x is None:` + else) | BYTE-IDENTICAL |
| nonone_no_else (`if x is not None:` 无 else) | BYTE-IDENTICAL |
| simple_nonone (`if x is not None:`) | BYTE-IDENTICAL |
| simple_isnone (`if x is None:`) | BYTE-IDENTICAL |
| inline_after_or (`x=a or b; if x is not None:`) | BYTE-IDENTICAL |
| while_nonone (`while x is not None:`) | DIFF（**while 路径独立问题，非本轮范围**） |

> 注：简单 `if x is not None:`（无 or 前导）此前已被正确处理；本轮修复的是
> **or-赋值与 if 共享 merge block** 这一结构变体。

### 4.2 真实目标翻转

- `db_base.pyc`：`partial` → `ok`（30/30 函数字节一致），`parse_db_url` 形态修复生效。

### 4.3 全量回归（402 pyc）

- 重编译 `(opname, argval)` 逐条比对（跳转指令仅比 opcode 名）。
- 结果：**304 ok / 98 partial**，与基线完全一致。
- 提交基线（HEAD 提交版 `pyc_index.json）对比：
  - `committed-ok → 现 non-ok`：仅 1 个 = `strategy_universe.pyc`（partial，rate 0.909）。
    经验证该文件在**未修改的 HEAD 代码**上重跑同为 partial（10/11）→ 属**非确定性抖动文件**，
    **非本轮回归**。
  - `committed-non-ok → 现 ok`：1 个 = `db_base.pyc`（本轮真实修复）。
- 通用路径（`orelse: []`）行为不变，`arg_checker` 等 3 个家族共 4 个文件保持 ok，零回归。

## 5. 改动文件清单

- `core/cfg/region_ast_generator.py`（+45 / -2，仅 R89 NONE_CHECK 分支）
- `pyc_index.json`（重验证状态更新）
- `site-packages/**/*OK.py`（批量重编译产物，自动生成，未手改）

## 6. 遗留 / 后续轮次候选

- **G6-while**：`while x is not None:` 路径（`_loop_generate_while`）仍存在独立的 `is None`
  取反判据问题（`while_nonone` 复现 DIFF），建议下一轮作为独立任务处理。
- **G5 `in`→`not in` 反转**（convert.pyc::getchnstr）：`CONTAINS_OP 0 + POP_JUMP_IF_TRUE`
  被反转为 `CONTAINS_OP 1 + POP_JUMP_IF_FALSE`，但忠实源码复现未触发（真实字节码有不可见结构差异），
  风险较高，暂列候选。
