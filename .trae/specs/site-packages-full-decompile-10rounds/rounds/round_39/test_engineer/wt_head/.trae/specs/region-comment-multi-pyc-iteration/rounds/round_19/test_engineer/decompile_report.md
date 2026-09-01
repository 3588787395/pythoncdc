# R19 测试工程师报告 — WithRegion if-drop Defect 3 + strategy/const.pyc 轮询

## 1. 本轮目标

1. **修复 if-drop Defect 3**（R18 残留）：WithRegion.cleanup_blocks 误消费 with 语句之后的 if 守卫块（`POP_JUMP_*` 结尾的兄弟 IfRegion 条件块）。目标 pyc：`IQCommon/strategy/strategy.pyc::trade_strategy_add` —— 恢复 `if strategy_lv2_name is not None:` 守卫。
2. **轮询下一个 pending pyc**：`IQCommon/strategy/const.pyc`（1 fn，字母序首个 medium-small pending pyc）。

## 2. if-drop Defect 3 确认

**最小复现**（`repro_01_with_then_if_guard.py`）：
```python
def f(p, b):
    with open(p, 'r', encoding='utf-8') as fh:
        content = fh.read()
    if b is not None:
        x = 'a_' + b
    return x
```

**修复前产物**（守卫被丢弃，body 变孤儿无条件语句）：
```python
def f(p, b):
    with open(p, 'r', encoding='utf-8') as fh:
        content = fh.read()
    x = 'a_' + b          # if b is not None: 守卫丢失
    return x
```

**字节码定位**（`_r19_probe.pyc` 函数 f）：
- offset 80–102: with 正常出口 `__exit__(None,None,None); JUMP_FORWARD to 126`
- offset 104–124: WITH_EXCEPT_START 异常 handler
- offset 126: `LOAD_FAST b; POP_JUMP_FORWARD_IF_NONE 140` ← `if b is not None:` 守卫
- offset 130: `LOAD_CONST 'a_'; LOAD_FAST b; BINARY_OP +; STORE_FAST x` ← if body
- offset 140: `LOAD_FAST x; RETURN_VALUE`

异常表 `38 to 78 -> 104 [1]`，故 body_start=38, body_end=80。

**区域分析输出（修复前）**：
```
WithRegion entry=0
  with_blocks: [38]
  exception_blocks: [104, 112]
  cleanup_blocks: [110, 118, 120, 126]   ← 126 误入 cleanup！
  body_offset_start/end: 38 80
```
block 126（`LOAD_FAST b; POP_JUMP_FORWARD_IF_NONE`）被误纳入 `cleanup_blocks`，致 WithRegion 拥有该 if 守卫块；下游 `_generate_with` 将其标记为 `generated_blocks`，IfRegion 无法接管 → 守卫丢失，body 作为孤儿无条件语句残留。

**根因**：`region_analyzer._collect_normal_exit_cleanup`（`_identify_with_regions` 路径）的 `has_user_code` 检查仅识别 STORE_*/CALL/BINARY_OP 等，不识别条件跳转指令（`POP_JUMP_*`）。守卫块（`LOAD_FAST b; POP_JUMP_IF_NONE`）`has_user_code=False`，且 last 指令非 RETURN，故被当线性清理块收集。WITH 识别优先级（TRY>LOOP>WITH>...>IF）先于 IF，故 block_to_region 中 126 尚未被 IfRegion 占用，旧版无归属守卫可拦截。

## 3. strategy.pyc 验证（修复后）

```
strategy.pyc: partial 50.00% (1/2 matched)
  - trade_strategy_add: 100% matched（true_diffs 61 → 0，if-drop 修复）
  - <module>: 39 true_diffs（Pattern R2 IMPORT_FROM+SWAP+POP_TOP 优化器 artifact，不可修复）
```

修复后 `trade_strategy_add` 正确恢复守卫：
```python
if strategy_name in CUSTOM_STRATEGY_NAME_DICT:
    strategy_hub_name = CUSTOM_STRATEGY_NAME_DICT[strategy_name]
else:
    return {'error_no': -1, ...}
if strategy_lv2_name is not None:        # ← 守卫恢复
    strategy_hub_name = strategy_hub_name + '_' + strategy_lv2_name
```

## 4. const.pyc 轮询验证

```
const.pyc: ok 100.00% (1/1 matched)  — 首次验证即 100%
```
内容为模块级常量赋值（字符串 / dict / list），无控制流结构，反编译产物与原字节码完全一致。`constOK.py` 已生成。

## 5. 最小复现实例（11 个）

| 编号 | 文件 | 类型 | 修复前 | 修复后 |
|---|---|---|---|---|
| 01 | repro_01_with_then_if_guard.py | DEFECT-REPRO | if 守卫丢失 | NO-DEFECT 2/2 |
| 02 | repro_02_with_then_if_else.py | DEFECT-REPRO | if-else 守卫丢失 | NO-DEFECT 2/2 |
| 03 | repro_03_with_then_if_return.py | DEFECT-REPRO | if-return 守卫丢失 | NO-DEFECT 2/2 |
| 04 | repro_04_with_then_elif_chain.py | DEFECT-REPRO | elif 链守卫丢失 | NO-DEFECT 2/2 |
| 05 | repro_05_with_then_if_method_call.py | DEFECT-REPRO | if+方法调用守卫丢失 | NO-DEFECT 2/2 |
| 06 | repro_06_with_then_if_attr_compare.py | DEFECT-REPRO | if+属性比较守卫丢失 | NO-DEFECT 2/2 |
| 07 | repro_07_ctrl_const_assignments.py | CTRL（const.pyc 镜像） | NO-DEFECT | NO-DEFECT 1/1 |
| 08 | repro_08_ctrl_const_dict.py | CTRL（const.pyc 镜像） | NO-DEFECT | NO-DEFECT 1/1 |
| 09 | repro_09_ctrl_with_no_postif.py | CTRL（with 无 post-if） | NO-DEFECT | NO-DEFECT 2/2 |
| 10 | repro_10_ctrl_if_no_with.py | CTRL（if 无 with） | NO-DEFECT | NO-DEFECT 2/2 |
| 11 | repro_11_ctrl_with_in_if.py | CTRL（with 嵌套于 if） | NO-DEFECT | NO-DEFECT 2/2 |

`verify_repros.py` 结果：**0 DEFECT-REPRO, 11 NO-DEFECT, 0 ERROR**。

## 6. 累计成功率

| 指标 | R18 | R19 | 变化 |
|---|---|---|---|
| verified_pyc | 36 | 37 | +1（const.pyc） |
| ok_pyc | 24 | 25 | +1 |
| partial_pyc | 11 | 11 | 持平（strategy failed→partial） |
| failed_pyc | 1 | 1 | 持平（main.pyc 深度残留） |
| total_functions | 458 | 459 | +1 |
| matched_functions | 306 | 308 | +2（trade_strategy_add + const） |
| cumulative_match_rate | 66.81% | **67.10%** | +0.29pp |

累计成功率 67.10% ≥ R18 66.81%（单调递增，无回归）。

## 7. 跨轮回归

- R18 minimal_repros: **11/11 NO-DEFECT**（与 R18 一致，零回归）
- R18 KW_NAMES 修复（with 关键字参数保留）继续生效

## 8. 残留

- **strategy.pyc `<module>` Pattern R2**：`IMPORT_FROM common; SWAP 2; POP_TOP` 优化器 artifact，无源码可复现，不可修复（与 R18 一致）。
- **main.pyc**：深度残留 failed，不阻塞前向进度（与前轮一致）。
