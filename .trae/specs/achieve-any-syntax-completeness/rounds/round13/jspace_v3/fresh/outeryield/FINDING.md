# rr-v5r151 [v151-OUTERYIELD] 共享头嵌套去重计数分支的 yield 内容守卫（OUTERYIELD 域）

## F1 功效案（difflib._line_pair_iterator 实形最小化）

```python
def gen(line_iterator):
    fromlines, tolines = ([], [])
    while True:
        while len(fromlines) == 0:
            from_line, to_line, found_diff = next(line_iterator)
            if from_line is not None:
                fromlines.append((from_line, found_diff))
            if to_line is not None:
                tolines.append((to_line, found_diff))
        from_line, fromdiff = fromlines.pop(0)
        to_line, todiff = tolines.pop(0)
        yield (from_line, to_line, fromdiff | todiff)
```

v150 渲染把外层 `while True:` 整体丢弃——pops+yield 变成 while 循环**之后**的顺序语句，
生成器最多 yield 一次即终止（真实 R1：无限循环→单次发射，difflib._mdiff 主用例输出
行数塌缩）。E1/E2 矩阵实证 HEAD-TEXT-DIFF→v151 恢复双层循环 + JUDGE-EQUAL 字节验证。

## 根因（R21-77-F5 共享头去重的计数分支）

两 LoopRegion 共享 condition_block（外层 while True 头 == 内层 while test 块）时，
去重判据的**计数分支** `len(body_a_set - body_b_set) <= 2` 把「外层体只多 2 块」
近似为「外层没有自己的内容」（同测试重复包装，R104 域）。但差集 ≤2 块可以是
**外层自己的循环体语句**：`while True:` 包裹内层 `while <test>:` 的真实嵌套——
外层回边自 pops+yield 块（2 块：POP_TOP/UNPACK/STORE… + YIELD_VALUE + JUMP_ABSOLUTE
回共享测试块）落回共享测试块，difflib._line_pair_iterator 实形。此时外层被
removal_set 剔除 → while True 包装与 pops+yield 体一起从区域树消失。

（对照：mdiff3.pyc（真实 `_line_pair_iterator` 全形，含 or 条件 + try/except）中
LOOP hdr=16 back=450 与 LOOP hdr=92 back=306 仍以同样机制被去重——本轮守卫对
mdiff3 形同样命中，但其渲染另有 or 链吸收与 except 臂两处独立缺陷（HEAD 与 v151
同为缺陷形，TEXT-SAME 不现于此矩阵），登记 MDIFF 专项轮处理：
D:/temp/opencode/cl_layout/r147diag/mdiff3_src.py 四缺陷复现存档。）

## 修复（analyzer 单文件 +23/−2，只增不破）

`core/cfg/region_analyzer.py` R21-77-F5 去重两处计数分支各加 [v151-OUTERYIELD]
yield 内容守卫：`_diff = body_x_set - body_y_set` 中任一块含 YIELD_VALUE ⇒
计数分支不成立（外层有自己的 yield 体语句），交由既有
`_r104_outer_wrapper_is_redundant` 结构判据裁决（其本就是权威出口）。

- 不动结构判据本身；`len(_diff) <= 2` 无 yield 时行为逐位不变。
- async await 的 SEND+YIELD_VALUE 轮询形不受影响：await 自循环已在
  `_is_await_polling_loop` 单独排除（C3 矩阵 SAME+JUDGE-EQUAL 实证）。
- C2 真同测试共享头（无 yield 差集）维持原去重行为（SAME 实证）。

## 验收

- 矩阵 10 案 ALL PASS（E1/E2 HEAD-TEXT-DIFF→v151 JUDGE-EQUAL；C1 while-True-break /
  C2 真共享头 / C3 async / C4 纯 yield 生成器 / C5 v150 fancy 尾 / C6 na5 /
  C7 v149 gcm 全 SAME+JUDGE-EQUAL；C8 B116 原形 SAME 预存在 DIFF 维持）
- difflib 判官 59/62 维持（fresh 产物重跑 difflib_judge_v151c.txt；v150/v151 产物
  TEXT-IDENTICAL 零漂移；剩余 3 差单元 _mdiff / _mdiff._line_pair_iterator /
  _line_wrapper 登记 MDIFF 专项轮）
- 电池 311 案（R110 169 + V111..V122/V148/V149/V150 累计 + V151 10）——见
  r151_regress_result.txt
- pytest 冻结基线 2F/277P/2XP

## 文件

- matrix_v5r151.py / matrix_v5r151_result.txt
- r151_regress.py / r151_regress_result.txt
- difflib_judge_v151.txt / difflib_judge_v151c.txt（fresh 产物重跑）
- fix_patch_v5r151.diff
