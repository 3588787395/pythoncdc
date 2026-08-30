# Round 32 测试报告 — ptradeAccount.pyc（135/137）

日期：2026-08-30　测试环境：D:/Python/python.exe（3.11.7）　对象：`site-packages/fly/simtradding/ptradeAccount.pyc`

## 1. 不匹配函数清单（list_mismatch.py 实测）

| 函数名 | orig 指令数 | decomp 指令数 | 首个差异 |
|---|---|---|---|
| `order_response_order_update` | 97 | 30 | index 21: orig `LOAD_FAST order_item` vs decomp `JUMP_BACKWARD 166` |
| `trade_response_order_update` | 116 | 30 | index 21: orig `LOAD_FAST order_item` vs decomp `JUMP_BACKWARD 166` |

两个函数症状完全相同：反编译产物（ptradeAccountOK.py:889-907）为

```python
for order_item in datalist:
    pass
else:
    algo.tmporders.set_instance(tmporders)
    return None
```

即**整个循环体 + 外层 try/finally 全部丢失**（finally 的 release 也没了），指令数 97/116 → 30。

## 2. 根因判断（含证据链）

**一句话**：try/finally 之后的显式 `return None` 块被 LoopRegion 当作自然出口收进 else_blocks，使 LoopRegion 的 offset range 反超 TryExceptRegion，`_build_region_hierarchy` 依优先级（LoopRegion=5 > TryExceptRegion=3）把**外层 try 挂成了循环的子区域**，层级颠倒导致 try/循环体在生成时全部丢失。

证据链（探针 `probe_top_regions.py` / `probe_cmp_all.py`，目标 vs 变体 A2）：

| | A2（try 包全 + 隐式 return） | 目标（try 包全 + **显式** return None 在 finally 后） |
|---|---|---|
| TryExceptRegion range | (4, **628**) | (4, **614**) |
| LoopRegion range | (4, **500**) | (4, **620**) |
| 层级 | try(parent=None) ⊃ loop ✔ | **loop(parent=None) ⊃ try** ✘ |

异常表（`4 to 210 -> 550/564` 等）两者几乎一致，`_identify_try_except_regions` 在目标上**识别成功**（entry=4，blocks 与 A2 同构）；差异纯在下游层级归约。

怀疑代码位置：
1. `core/cfg/region_analyzer.py:3641`（`region_blocks.update(else_blocks)`）与 `:3648-3657`（[W3 fix] natural-exit 收纳 `_check_block_has_trailing_return_none` 后继块）——把 post-try return 块 620 收进 LoopRegion，loop range 被撑到 620。
2. `core/cfg/region_analyzer.py:769-782`（`TryExceptRegion.get_offset_range`）——range 按 try_blocks/handlers/else/finally 计算，止于 cleanup 尾块 614，不含 all_blocks 中的 620。
3. `core/cfg/region_analyzer.py:22449-22655`（`_build_region_hierarchy`）——range 打平/反转时按优先级取 best_parent（`:22601-22604`），LoopRegion(5) 反超 TryExceptRegion(3)，父子方向颠倒。修复方向：a) try 语句后的提升 return 块不应计入 LoopRegion else_blocks；或 b) 层级判定中 TryExceptRegion 与 LoopRegion 互相覆盖对方 entry 时优先 try 包 loop（参照 `:22589-22599` 的 try 父候选特判思路）。

## 3. 最小复现（variant_work/，pyc_batch_verify decompile_single+bytecode_diff 实测）

**同构（复现 97→30 截断 + 层级颠倒）**：
- `F_return_after_finally.py/.pyc/OK.py`（本轮新增）：= A2 + try/finally 后显式 `return None`。**实测 `orig=97 decomp=30`，与 `order_response_order_update` 完全同构**；渲染产物同样为 `for: pass` + else，层级 probe 确认 TryExceptRange(164,626) ⊂ LoopRegion(164,632)、try.parent=LoopRegion。

**不同构（仅复现较轻的拍平缺陷，不触发截断）**：
- `A_finally_inner_try`：MISMATCH f orig=98 decomp=98（内层 try 拍平、finally 渲染成 except/finally）
- `A2_try_wraps_all`：MISMATCH f 98/98（同上）
- `A3_static_method`：MISMATCH order_response_order_update 98/98（同上）
- `A4_for_else`：MISMATCH f 98/98（同上）
- `A5_return_in_try`（return 在 try **内**）：不触发截断——return 在 try 范围内时不产生 post-try return 块，层级不颠倒
- `B_finally_elifchain` / `C_nofinally_inner_try` / `D_nofinally_elifchain` / `E_finally_plain_for`：全部 2/2 MATCH，不触发

**结论**：触发条件 = `for 循环在 try/finally 内 + return None 位于 try/finally 语句之后`（F 变体），缺一不可；上一工程师的 A 系列变体均缺「finally 后显式 return」要素，故只复现了拍平未复现截断。

## 4. 本轮新增文件

- `variant_work/F_return_after_finally.{py,pyc,OK.py}` — 最小复现三件套
- `probe_cmp_all.py`、`probe_top_regions.py`、`probe_phase_track.py`、`probe_try_regions.py` — 层级/区域结构探针（phase_track.txt / probe_try_out.txt 为其输出）
