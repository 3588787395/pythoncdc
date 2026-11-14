# rr-v5r161 fix161c 设计（父代理，含两树实证）

## 一、两树探针实证（probe3.py，runpy 跑真实 pycdc 管线，instrument 链检测）

| 案 | HEAD 树（f7d80873） | v161 树（+103/−3） |
|---|---|---|
| fused `not a or (b and c)` | CALL#0 @0 → None；CALL#1 @6 → [(6,and),(10,and)]（→ 错误 factored 形） | [(0,or),(6,and),(10,and)] ✓ |
| not_or `not a or b` | CALL#0 @0 → None；CALL#1 @6 → None（→ HEAD 正确渲染无 else） | [(0,or),(6,and)]（→ 多 else 风格漂移） |
| nottail `a and not (b and c)` | CALL#0 @0 → None；CALL#1 @6 → [(6,and),(10,or)]（→ 正确） | [(0,and),(6,and),(10,or)]（→ **误融合** `not (a and b and c)`） |

字节码（H2_dis.txt）：融合头 head FALSE→body；NOTTAIL head FALSE→exit、末成员 TRUE→exit。
两形在门时点镜像，v161 门改动使走查越过 HEAD 断链点 → NOTTAIL 被吞。
故 fix161b（走查尾守卫 >=3）与任何门级收窄都不成立：**必须完全回退 v161 五处插入**。

## 二、fix161c 形态：标准走查失败后的专用融合头探测

注入点：`if len(chain) < 2:`（现 L35558，HEAD 同位置）之前——标准走查已失败时
才尝试；命中则用专用链继续走既有下游（mixed-chain unify 等），不命中 return None
（与 HEAD 逐字节同路径，C3 安全）。

探测器 `_detect_fused_not_head_chain(start_block)`（只读 CFG，I.4 白名单）：
1. head = start_block；末指令须为 FALSE 极性条件跳转；B = 其跳转目标块。
2. Y = head 的 fall-through 后继；Y 末指令须为条件跳转；E = Y 跳转目标块；
   要求 E 存在、E ≠ B、且 `not _is_equivalent_exit_block(B, E)`。
3. 从 Y 起沿「非跳转目标后继」走 and-run：
   - 若某成员 fall-through == B → 该成员为末成员，结束；
   - 否则 fall-through 必须是条件跳转块且其跳转目标 == E（或等价于 E），加入 run；
   - 其它情况 → 不成立。
4. 命中条件：run 成员数 **≥ 2**；返回 chain = [(head,'or')] + [(m,'and') for m in run]。

## 三、三案判别验证（本设计）

| 案 | head→B | Y→E | run | 末成员 ft | 判定 |
|---|---|---|---|---|---|
| fused | @0→14 | @6→18 | @6,@10（均→18） | 14==B ✓ | **命中**（run=2）→ 与 v161 链逐元素相同 |
| not_or | @0→10 | @6→14 | @6 only | 10==B ✓ | run=1 <2 → **不命中** → HEAD 路径（无 else）✓ |
| nottail | @0→18 | @6→14 | @6 only（@10 为 PJIT→18≠E） | — | run=1 <2 → **不命中** → HEAD 路径（正确 AND 渲染）✓ |

c 形 `not a or (not b and c)`：Y 为 PJIT→E，成员跳 E 判据不看极性 → 命中（run=2）✓

## 四、验收

- a_not_or / C161_not_or / pv8 逐字 SAME HEAD（无 else）+ 判官 EQUAL
- NOTTAIL 七案（E1_ggo_tail/E3_ggo_real/C1_merged_exit/C2_ret1/C3_tail3/pv2/pv3）逐字 SAME HEAD + EQUAL
- difflib 62/62；request 190/194
- 六功效案与 v161 基线产品（E161_*_B.py）逐字 SAME（TEXT-DIFF vs HEAD + BYTE-EQUAL）
- 矩阵 19 案全过；电池 458 案 TEXT-DIFF 恰 6；R110 168/167；REG-10 维持；NO-SRC 0
