# REAL46-031 三元重建缺陷：or-of-ands 条件三元被误拆为嵌套 if（rr-v5r84）

状态：**已修复**（`core/cfg/region_analyzer.py` +78 行，0 删除，纯结构判据）。
条目：G2c REAL46-031（`packaging.version`，offset 30），HEAD 上 exec 失败
（`TypeError: can only concatenate str (not "bool")` → diffs LOAD+R0+R5…）。

## 缺陷

源（packaging/version.py 真实代码）是三元表达式：

```python
VERSION_PATTERN = (
    _VERSION_PATTERN_OLD
    if (sys.implementation.name == "cpython" and sys.version_info < (3, 11, 5))
    or (sys.implementation.name == "pypy" and sys.version_info < (3, 11, 13))
    or sys.version_info < (3, 11)
    else _VERSION_PATTERN
)
```

条件为「or-复合-and 比较链」。HEAD 产物把三元**拆成嵌套 if（分支是裸表达式、
无赋值）+ `VERSION_PATTERN = <条件布尔值>`**，运行 `TypeError`。

最小复现 `tern_repro.py`：简单条件 / 纯 and 链 / 纯 or 链三元均正确，唯
**or-of-comparison-ands** 触发（`tern_variants.py` 5 变体隔离）。

## 根因（同层 CFG 结构事实，见 fix_patch.diff 注释）

1. BoolOp walk 从链首 B1 被 `[sb-has-body]` 守卫拒绝（B1 含前序 import/STORE
   语句）→ 退化为从 or 尾段成员 B3 起步；R54-A 混合链救援要求
   `T_J.start_offset > T_F.start_offset`（if 语句布局），三元布局值块在条件链
   之后、方向相反 → 拒。
2. BoolOpRegion 只覆盖 or 尾段（entry=链中段而非首块），条件链 walk 在其入口
   止步；三元检测各路径全灭（B3 被 `_is_boolop_ternary_candidate` 拒、B1 的
   true_block 被值块守卫拒、B2 被 `_is_ternary_block` 拒）。
3. TernaryRegion 缺席 → 3 个 IfRegion 物化错序三元 → `VERSION_PATTERN = <bool>`。

## 修复（[TCX-扩展] 两处，均只加不破坏）

1. **链续接通道**（`_detect_ternary_pattern`）：walk 链长 ≥2 且链尾 fall-through
   后继恰为某既有 BoolOpRegion entry（身份恒等）、op_chain 与已走链块零重叠、
   接口闭合（BoolOp 末成员 jt=其 merge、ft=链尾跳转目标）、ft/jt 均单表达式值块
   → chain_blocks 续接 op_chain 块，由既有 len(chain)>1 路径重导值块建
   TernaryRegion。触发边界限 walk 链长 ≥2（防 or 尾段中间成员误立独立三元）。
2. **skip_ternary 守卫扩展**：`_tcx_boolop_extended` 置位且 BoolOp op_chain ⊆
   candidate_blocks → can_upgrade（该 BoolOp 是三元条件组成部分而非独立结构）。

op 信息生成端由 `_build_ternary_boolop_condition` 按各成员末跳转方向推导
（IF_FALSE→and / IF_TRUE→or），无需携带。

## 验证（实测读数）

| 检查 | HEAD 基线 | 修复后 |
|---|---|---|
| repro 产物 | 嵌套 if + `VERSION_PATTERN = <bool>` | `VERSION_PATTERN = A if COND else B`（真三元），运行 `VP str new` 无 TypeError |
| `tern_variants.py` 5 变体 | simple/and/or/or_three preserved，or_of_and 坏 | 全部 ternary_preserved=True，逐形态一致 |
| REAL46-031 exec | RC=1 `TypeError: can only concatenate str (not "bool")` | **RC=0**（COMPILE_OK，stderr 空；verdict 仍 DIFFERENT——剩余为该 1231 行模块其它既有 R7/R5 差，另一族） |
| pytest 7 文件 | 2 failed / 282 passed / 2 xpassed（既有 B01、BOUNDARY_02） | **2 failed / 282 passed / 2 xpassed，零新增失败** |
| 全量 1556 语义闸门 | 基线 `semantic_shard{0,1,2}_v5r79.json` | 见下节 |

## 全量 1556 闸门（对 v5r79 基线，三分片 offset 0/519/1038）

| 指标 | v5r79 基线 | v5r84 |
|---|---|---|
| entries | 1556 | 1556 |
| verdicts | EQUAL 1132 / ERROR 424 | EQUAL 1132 / ERROR 424 |
| 总 verdict 变化 | — | **0** |
| 回归（EQUAL→non-EQUAL） | — | **0** |
| 改善（non-EQUAL→EQUAL） | — | 0（REAL46-031 不在 J 空间；其 exec 改善在 G2c 空间，verdict 因剩余 R7/R5 仍 DIFFERENT） |

产物：`semantic_shard{0,1,2}_v5r84.json` + `_report.json`；比对脚本
`compare_v5r84.py`（与 compare_v5r79.py 同法，基线换成 v5r79 三分片）。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `tern_repro.py` / `.pyc` / `tern_repro_decompiled.py` | 最小复现 + 修复后正确产物 |
| `tern_variants.py` | 5 变体 oracle（触发边界隔离） |
| `tern_dis.py` | 模块字节码 dump |
| `tern_region.py` | CFG/region dump（HEAD 错误：3 个嵌套 IfRegion，无 TernaryRegion） |
| `fix_patch.diff` | +78 行修复完整 diff（含判据注释） |

## 诚实边界

- 不宣称 G2c 通过（REAL46-031 verdict 仍 DIFFERENT：剩余 R7/R5 为该模块其它
  既有差；REAL46-004 use_args、022/023/046 R5 仍在案）；`product_complete`
  仍 **NOT PASS**。
- 修复命中边界为 or-of-comparison-ands 且走链长 ≥2 的三元；其它复杂条件三元
  形态未逐一验证（以全量闸门零回归兜底）。
