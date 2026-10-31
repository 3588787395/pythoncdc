# PUREBACK：循环内嵌套 if 臂漏收纯回边块修复（rr-v5r102，Task 28，REAL46-004 族 C 闭合）

## 家族选定与根因

rr-v5r101 剩余登记：REAL46-004 叶差 3 项。本轮选**族 C**：
`_proto_member.__set_name__` 的 `for base in enum_class.__mro__[1:]:` 循环体
多一条 JUMP_BACKWARD（重复回边，原件 2 条 1460/1462、产品 3 条 1460/1462/1464，
其余为 +2 目标移位）。

根因（原件/产品逐指令并排 + 区域树插桩 + A/B 文件交换）：`__set_name__` 循环
体源码为 `if descriptor is not None: / if isinstance(...): break / elif
hasattr-and: found; continue`——分析端 `_identify_conditional_regions` 的臂
过滤器（region_analyzer 24278-24303）只把**已登记**的回边块从 then/else 臂
剔除，而循环的 `back_edge_block` 登记集只含 continue 所在块（122，含用户
语句 + 臂尾 JUMP_BACKWARD）；循环结构末尾的第二个纯 JUMP_BACKWARD 块（128，
全块仅回边指令）未登记——逃逸臂过滤被归入嵌套 if 的 else 臂
（else=[110,128]）。发射端据其为 else 臂成员渲染裸 `continue`，与循环续行
重复；外层 if（`d is not None`，merge=128）假边的共享落点被嵌套臂认领后
被迫重新合成回边（130）——重编译 3 条回边 vs 原件 2 条（族 C 叶差）。

判别器（pm1 A/B 实证，防止过宽）：同形回边块有两种归属——①**共享落点**
（pc2 实测：外层 if 假边 58→128 与链假出口 120→128 共享同一纯回边块；块被
嵌套臂认领渲染会孤儿化祖先假边）→ 必须排除出臂、归循环续行；②**臂内私有
回边**（pm1 实测：`elif` 臂末回边块 136 唯一前驱 92 在臂子树内、且空
`else: pass` 落点 138 已登记）→ 必须保留在臂中渲染为 continue，它是原件
第二个回边块的唯一来源，排除即丢回边（首版无条件补录使 pm1 由
BYTE-EQUAL 转 DIFF、enum 产品 `_test_simple_enum` 新增 co_code 差，随即
加守卫后复绿）。

## 修复（region_analyzer 只增不破，[v102-PUREBACK]，+25 行一 hunk）

条件回边扫描（24278-24284）之后增补无条件纯回边同域扫描：`body_blocks`
中块尾无条件 `JUMP_BACKWARD(_NO_INTERRUPT)` 且目标==header/condition、
且未登记的块，仅当**存在本 if 臂集合之外的前驱条件边**（前驱条件跳转指向
该块且前驱 ∉ {block}∪then_blocks∪else_blocks∪chain_blocks——祖先 if 假边
共享落点的全结构事实）才补录入 `_loop_back_edge_blocks`；既有臂过滤器
（else 24288 的 `not in _loop_back_edge_blocks or == else_succ`、then 24303
经 `_then_back_edge_blocks`）随之排除该块、归循环续行唯一渲染。不入
`_conditional_back_edge_blocks`（该集合无 then/else 例外豁免口径，保持不变）。

## 验证（全实测）

- 复现矩阵：pc1（4 臂梯精确复现）/pc2（最简 2 臂）/pc4（双 if 形）/
  pc5（else 尾形）**v101 DIFF → v102 BYTE-EQUAL**（重编译全 code object
  逐字段）；控制案 pc3（无外层 if）/pc7/pc8/pc9/pc10/pc11/pc12（while 语境
  /双循环/else 臂/双 continue/嵌套两层/break 臂/两循环复合）+ pm1（M2 空 Falls
  else 形，v101 已 BYTE-EQUAL）v102 零变化——C3；pc8 文本 A/B 去多余裸
  continue（重编译等价，电池第 3 列 BYTE-EQUAL）。
- 首版过宽实证：无条件补录使 pm1 BYTE-EQUAL→DIFF、enum 产品
  `_test_simple_enum` 新增 co_code 差——共享落点守卫加入后复绿，pm1/enum
  逐字节与 v101 一致。
- 前轮矩阵 53 案（nb/no/mt/va/fdt/pb/pv + pc/pm）：52 BYTE-EQUAL + nb2
  维持既有登记差（与 v100 逐字节同签名）。
- REAL46-004（enum pyc sha 60e3ca30）：字段级 real-diff **v101 的
  `<module>._proto_member.__set_name__: co_code,co_exceptiontable` 移出**
  （族 C 闭合）、零新增（`_proto_member: co_consts` 剩余为嵌套 code
  firstlineno 布局噪声，同其他 co_consts+co_firstlineno-only 项）；剩
  real-diff = 既有登记同态（族 D `_convert_`+dictcomp removed、
  EnumType.__new__、Flag._missing_、convert_class）。权威 semantic_diff
  单案复跑 **EQUAL（diffs=[]）**。
- 既有登记（本轮不修）：pc6（while 语境 continue 臂丢 `i += 1`）——v101 与
  v102 产品逐字节相同（预存在形态，登记下轮家族）。
- 回归电池 50 案（r102_regress.py 双文件交换 A/B：v5r101 HEAD vs v102 同输入
  pyc 反编译产物逐字节比对）23 原案全 TEXT-SAME（w28 w2/w3 v97 既有同态）
  + 4 功效案 TEXT-DIFF/BYTE-EQUAL + pc8 文本改善 TEXT-DIFF/BYTE-EQUAL +
  22 控制案 TEXT-SAME。
- pytest 7 套件 2 failed（冻结对）/ 282 passed / 2 xpassed；比较器
  pyc_verify.py SHA256 FE1902A9… 冻结一致、tests/ 零改动。
- 全量 1556 闸门（v5r102 三分片对 v5r89 基线）**0 回归**：EQUAL 1180=1180、
  ERROR 376=376；对 v101 逐案 c4 verdict 零变化（连续第三轮零抖动）；
  分片汇总 shard0 367/152、shard1 406/113、shard2 407/111。
- REAL46 sweep（v5r102 对 v5r101）**46 案 c4 逐案零变化 0 回归**：14
  DIFFERENT/14 EQUAL/17 ERROR+skip1（c2_pyc_missing=已登记 REAL46-045）；
  REAL46-004 维持 EQUAL（diffs=[]）。

## 诚实边界

- 族 C 闭合；REAL46-004 剩 real-diff = 族 D（dictcomp removed）及
  EnumType.__new__/Flag._missing_/convert_class（r100 已登记同态）。
- pc6 形态（while 语境 continue 臂丢臂内语句）为预存在登记，本轮产品
  逐字节不变，下轮家族。
- nb2 平铺形维持登记。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r102.diff` | [v102-PUREBACK] 完整 diff（+25 行，含共享落点守卫判据注释） |
| `pc1-pc5/pc7-pc12_variant.py` | 复现+变体矩阵（4 功效案 + 7 控制案） |
| `pm1_control.py` | M2 空落点形控制案（首版过宽的 A/B 实证） |
| `pc6_registered.py` / `pc6_out_v101.py` / `pc6_out_v102.py` | 既有登记形态（产品逐字节相同实证） |
| `v101_baseline_pc.txt` | v101 A/B 基线（4 DIFF + 2 控制绿） |
| `REAL46-004_product_v102.py` | enum 产品（族 C 闭合状态） |
| `semantic_REAL46-004_v102.json`（+report） | 权威判定（EQUAL，diffs=[]） |
| `r102_regress.py` / `r102_regress_result.txt` | 50 案回归电池驱动与结果 |
