# rr-v5r149 [v149-NOTELIF] FINDING — 否定链式条件校验 if 的 elif 吸收否证（difflib get_close_matches 闭合）

## 1. 缺陷（真实 R1）

REAL46-012 difflib 判官差单元 `get_close_matches` 第二校验
`if not 0.0 <= cutoff <= 1.0: raise ValueError('cutoff must be in [0.0, 1.0]: %r')`
反编译为 `elif 0.0 <= cutoff <= 1.0:` 且 **raise 臂整体丢失**：

- v148 渲染：`if not n > 0: raise A` / `elif 0.0 <= cutoff <= 1.0: <整个函数体>`
  ——cutoff 越界时应 raise B，实际跳过全部函数体隐式返回 None=真实 R1
  （无效参数静默返回 None 而非 raise ValueError）。
- 最小复现 gcm.pyc 同形复现（两连校验 if + 循环体）。

## 2. 根因

`_build_elif_region` 内嵌 `_check_elif_chain` 把外层 else 首块（第二 if 的
链式比较首块 44）判为 elif 候选并**正极性**收集臂：elif-cond=44、臂=
[60,70,104,...]（真边 fall-through 侧=链式比较续块+函数体）、final_else=[72]
（假边 POP_TOP 清理块）。但候选 44 已是内层 IfRegion 的 condition_block——
该内层区域把 44 读作**否定条件**（`if not (chained): raise-2`：then=[74]=假边
清理块 72 续穿的 raise 臂、else=[72]、merge=104）。两套分区矛盾：内层 then 臂
（raise-2 @74）不在链臂块集（臂收集跳过已认领块）也不在 final_else（仅 [72]），
**孤儿化整体丢弃**；elif 臂混入链式比较内部块（60/70）与函数体。

结构对照：合法 `elif 0 < x < 10:`（链式比较 elif，C4 案）内层区域的 then 臂在
真边侧（fall-through 续块经 PJT 到达）→ 链正极性收集一致 → 吸收正确；合法
`elif not b: arm`（单块否定 elif，C2/C3 案）内层 then 臂恰为候选块假边**立即**
fall-through 后继 → 链臂=假边立即后继、既有臂取反渲染（R3-B109）正确。缺陷域
=否定链式条件（假边经清理块**间接**≥2 跳续穿到 then 臂）∧ 候选已被内层区域
正确分区——链吸收必然孤儿化。

判官实验：源级两 if 形重编译=Equal；elif+else 形（正极性 elif+补 else 臂）=
Different control flow（重编译链式比较缺少原始的中间 JF/POP_TOP 线程块，块数
不符）——唯一字节 Perfect 渲染=否定 if 独立成句。

## 3. 修复（只增不破，analyzer 单文件 +56/−0）

`_check_elif_chain` 候选接受点新增 [v149-NOTELIF] 否证：候选块已是内层
IfRegion.condition_block 且内层 then 首块在候选块末跳转的**假边侧**（按极性
取假边入口——假跳族=跳转目标、真跳族=fall-through 后继——单后继 fall-through
续走 ≤4 步可达）且 **≠ 候选块立即 fall-through 后继**（条件③排除单块否定
elif 的合法吸收）→ return None 交还调用方按既有 IF_THEN_ELSE + 嵌套子区域
路径渲染：`if not n > 0: raise A` 与 `if not (chained): raise B` 各自成句
（else 包裹与 elif 在 CPython 字节码层面同构——首条件块跳转目标同为内层条件
块——实测渲染产出正是源级两 if 形）。判据不命中时行为逐位不变（C2）。

## 4. 验收

- 矩阵 12 案：E1 gcm 最小形/E3 difflib 实形 HEAD-TEXT-DIFF→v149 **JUDGE-EQUAL
  字节验证**；E2 独立否定链式 if SAME+JUDGE-EQUAL（无前置 if 不触发合并，
  预存在正确）；C1 合法 elif+else/C2 单块否定 elif/C3 单块否定 elif 终态臂/
  C4 链式比较 elif/C5 ggo 尾（v148 族）/C6 B116 原形/C7 na5/C8 守卫嵌套/
  C9 否定链式+尾随 if 全 SAME（豁免不触发实证；C4/C6/C8 JUDGE-DIFF=预存在）。
- 电池 299 案（R110 169 + V111..V122 + V148 13 + V149 6）：见
  r149_regress_result.txt。
- pytest 7 套件：2F/277P/2XP 冻结基线（B01/BOUNDARY_02）。
- difflib 判官：57/62 → **58/62（93.55%）**，get_close_matches 闭合；余
  _fancy_replace/_mdiff×2/_line_wrapper 4 单元。

## 5. 域名与登记

域名 NOTELIF（elif 吸收否证族）。下轮候选：difflib 余 4 判官单元
（_fancy_replace/_mdiff×2/_line_wrapper）；k=1 twin 形；p=0 独立
`not (B and C)` if 条件；守卫嵌套族（G1 专项轮）；REAL46-014 tarfile /
016 urllib.request 余差；REAL46-013 cookiejar 91/105、015 subprocess 68/78
余差；4 compile_error；pytest 余 2 冻结对（登记态）。

## 6. 证据与中间件

证据（本目录）：`r149_regress.py`+result、`fix_patch_v5r149.diff`、
`matrix_v5r149.py`+result、`difflib_judge_v149.txt`、本文件。中间件
（D:/temp/opencode/cl_layout/r147diag/）：gcm*.pyc/probe_gcm*.py/derive149.py/
fix149.py/matrix_v5r149.py、r149matrix/、r149regress/。
