# rr-v5r150 [v150-RAISETERM] FINDING — raise 臂终止性精化（difflib _fancy_replace 闭合）

## 1. 缺陷（真实 R1）

REAL46-012 difflib 判官差单元 `Differ._fancy_replace` 尾部同步对发射：
源码 `if eqi is None: <qformat 四连 yield> else: yield '  ' + aelt`——
v149 渲染把 else 臂的 `yield '  ' + aelt` **无条件扁平化**为 post-if 语句：

- v149 渲染：`if eqi is None: <qformat> ` + `yield '  ' + aelt`（无条件）+
  `yield from self._fancy_helper(...)`——同线对情形（eqi 非 None）语义尚可，
  但**不同线对情形（eqi None）多发射一条 '  '+aelt**——unified_diff/diff 输出
  每个替换簇多一行上下文=真实 R1（doctest 主用例输出错位）。
- 最小复现 fr2（then 臂含 for+if/elif/else+raise 链 + 尾 yield-from 的生成器
  if/else）同形复现；bisect 实证触发因子=then 臂内的 opcodes 循环（V1 形），
  then 臂为裸 yield-from 时不复现（V2 形）。

## 2. 根因

区域形成 `_identify_conditional_regions` 的 then 臂收集（merge=None 时无界
walk）把 then 臂中**内层 for 循环体 if/elif/else 链的 else raise 块**（V1 形
offset 378=`raise ValueError('unknown tag')`）收进 then_blocks 列表尾部；
随后 `then_terminates_with_raise` 判据（原 24621-24628）只读 `then_blocks[-1]`
末指令——见尾即 raise ⇒ 判定「then 臂以 raise 终止」⇒ `else_blocks=[]`。
但臂的真实控制终点是 JUMP_FORWARD（454→472 正常逃逸到 merge）——raise 是
**内层子结构的内部早退**，非臂终点。else 臂被清空后，其语句块（458）从区域
blocks 剔除、交由父序列作 post-if 代码发射——else 语义丢失。

区域树证据（V1 形）：`IfRegion cond=60 then=[98,190,408,446,454,378] else=[]
merge=472`（else 收集 trace 实证 `COLLECT entry=458 -> [458]` 收集成功、被后置
清空判据丢弃）；tag-chain 区域独立存在（cond=192 elifs=[272,302,332]）。

## 3. 修复（只增不破，analyzer 单文件 +27/−1）

`then_terminates_with_raise` 判据加**臂闭合精化**：raise 构成臂终点仅当臂内
所有非终态块（末指令非 RETURN_*/RAISE_VARARGS/RERAISE）的正常后继都留在
then 块集内（无逃逸出口）。遍历 then 块——任一非终态块的后继 ∉ then 块集 ⇒
臂未闭合 ⇒ raise 非臂终点 ⇒ 保持 else 臂。全闭合（或全部终态）时维持原清空
行为逐位不变。判据只读块末 opcode 族与后继集（C1 同层结构事实）。

## 4. 验收

- 矩阵 10 案：E1 fr2 复现/E2 真 _fancy_replace 尾形 HEAD-TEXT-DIFF→v150
  **JUDGE-EQUAL 字节验证**（else 臂恢复）；C1 真 raise 臂/C2 臂内嵌 if 闭合
  raise（规则原形）SAME+JUDGE-EQUAL=原清空行为逐位保持；C3 ggo 尾（v148）/
  C4 gcm 校验对（v149）/C5 单块否定 elif（v149）/C6 B116 原形/C7 na5/
  C8 守卫嵌套全 SAME。
- 电池 301 案（R110 169 + V111..V122 + V148 13 + V149 6 + V150 5）：见
  r150_regress_result.txt。
- pytest 7 套件：2F/277P/2XP 冻结基线（B01/BOUNDARY_02）。
- difflib 判官：58/62 → **59/62（95.16%）**，_fancy_replace 闭合；余
  _mdiff/_mdiff._line_pair_iterator/_line_wrapper 3 单元。

## 5. 域名与登记

域名 RAISETERM（raise 臂终止性族）。下轮候选：difflib 余 3 判官单元
（_mdiff/_mdiff._line_pair_iterator/_line_wrapper——_line_pair_iterator 是
_mdiff 的嵌套生成器，二者可能同根）；k=1 twin 形；p=0 独立 `not (B and C)`
if 条件；守卫嵌套族（G1 专项轮）；REAL46-014 tarfile（142/160）/016
urllib.request（185/194）；REAL46-013 cookiejar 91/105、015 subprocess 68/78
余差；4 compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据与中间件

证据（本目录）：`r150_regress.py`+result、`fix_patch_v5r150.diff`、
`matrix_v5r150.py`+result、`difflib_judge_v150.txt`、本文件。中间件
（D:/temp/opencode/cl_layout/r147diag/）：fr*.pyc/fr_bisect.py/
probe_v1_*.py/fix150.py/matrix_v5r150.py/derive150.py、r150matrix/、
r150regress/。
