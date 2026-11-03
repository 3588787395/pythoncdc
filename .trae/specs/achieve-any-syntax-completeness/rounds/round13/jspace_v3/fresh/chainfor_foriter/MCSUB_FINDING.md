# MCSUB：match 守卫 case 体供给碎片幻影 pass 修复（rr-v5r110，Task 36，REAL46-001 叶闭合 `_get_slots`）

## 家族选定与根因

rr-v5r109 剩余登记选 **REAL46-001（dataclasses.cpython-311，sha d87ac1e1）
叶 `_get_slots`（co_consts.v[72]，214 字节最小案面）**——产品比原件多 1 条
指令（+2 字节）：守卫 case 体头多出一条行标记 NOP（产品文本在该 case 体首
渲染 `pass`）。

根因（产品/原件全量 dis 对照 + `_generate_match` 守卫块/体块转储 +
`_generate_block_statements` in-match 调用追踪）：

①**碎片切分**：`case iterable if not hasattr(iterable, '__next__'):
yield from iterable` 的 yield-from 环被分析器切成两块——前导 SETUP 块
`[LOAD_FAST iterable, GET_YIELD_FROM_ITER, LOAD_CONST None]`（供给碎片）
与 SEND 回边头块 `[SEND, YIELD_VALUE, RESUME, JUMP_BACKWARD]`（环头）。
原件该 case 体头**无 NOP**（`yield from` 行首直落 LOAD_FAST）。

②**重复/碎片走查**：case 体走查对该前导碎片块——`get_entry_region_for_
block` 返回 None（非环入口）→ `get_region_for_block` 命中 LoopRegion 但
非入口/环头/条件 → 有意中和（`nested_region = None`）→ 落普通 BSS 路径
——SETUP 碎片无法独立成句 → **BSS 返回空** → 空兜底分支（[B93d] 机制检
查不命中）补发 `{'type': 'Pass'}` → 渲染 `pass` → 重编译多 1 NOP，环头/
raise 等全部后继目标偏移 +2。而完整 `yield from iterable` 语句由嵌套
LoopRegion 生成端（SEND 回边头为入口）发射——碎片块的指令流已归该区域的
环重建消费（每块唯一归属被碎片走查违反）。

③**mc4 反例定位**（单捕获 case + 守卫 + yield-from 源）：单 case match 的
编译器简并（无 MATCH_CLASS）不形成 MatchRegion，产品走 if/else 路径——
不属本族（BYTE-EQUAL）；本族要求多 case 真_match 结构（mc1 复现）。

## 修复（region_ast_generator 只增不破，[v110-MCSUB]，+17 行一 hunk）

case 体走查的空 BSS 兜底分支（[B93d] 机制检查之后、`Pass` 发射之前）插入
**供给碎片守卫**：块的任一后继是嵌套区域入口（`get_entry_region_for_block`
命中且非本 MatchRegion、非 MatchRegion 类型）时，该块指令流归该嵌套区域的
生成端（碎片=区域环生成的 iter/SETUP 消费材料），**不补占位 pass**。

- **C3**：无区域后继的空块（真孤儿空体）保持既有 Pass 兜底逐位不变；
  [B93d] 机制块守卫原样前置；全噪声块早经既有 all-noise 分支跳过（真
  `case _: pass` 的 NOP 行标记臂不受影响）。

## 验证（全实测）

- **复现矩阵 12 案**：功效案 mc1（4 case 真_match + 捕获守卫 case + yield
  from 体——v109 TEXT-DIFF→v110 重编译全 code object 逐字段 **BYTE-EQUAL**
  产品 pass 消失）；控制案 11——mc2（无守卫多 case）/mc3（列表模式守卫
  return 体）/mc4（单捕获 case 编译简并为 if/else）/mc5（双守卫 yield）/
  mc6（守卫 case 内 for+前置赋值）/mc7（守卫 case 内 if/else）/mc8（真
  pass 臂 [C404w] 形）/mc9（dict 模式守卫）/mc10（双守卫连续）/mc11（守卫
  return 非生成器）/mc12（for 内嵌 match 守卫）——全部零变化——C3。
- **REAL46-001（dataclasses.cpython-311.pyc sha d87ac1e1）**：产品
  `_get_slots` 与原件逐字段一致；字段级真实差异集 `_get_slots` **移出**
  （仅剩 firstlineno 噪声类）；semantic_diff 单案复跑 R7 维 **3→2**（剩余
  v[47]=_get_field 跳转目标偏移 / v[69]=_process_class 多维——各自独立疾
  病域，维持 DIFFERENT 在案）。
- **REAL46-004（enum.cpython-311.pyc sha 60e3ca30）**：单案权威
  semantic_diff 复跑 **EQUAL（diffs=[]）**。
- 回归电池 **169 案**（r110_regress.py 双文件交换 A/B：v5r109 HEAD=03537d69
  vs v110 同输入 pyc 反编译产物逐字节比对 + 逐顶层函数重编译比对）**1 功效
  案（mc1）TEXT-DIFF/BYTE-EQUAL + 168 TEXT-SAME**（23 原案 + r108/r109 全
  部已闭合功效案稳定 TEXT-SAME/BYTE-EQUAL；既有登记差维持与 r109 逐字节同
  签名：w28_shapes w2/w3、ca6、ca13、ca15、cb5、na5、pd8_prod、pe8、
  pe8_target）。
- pytest 7 套件 **冻结对一致 2 failed**（TestDominanceFrontierIf::test_B01
  _simple_if_then_else_merge、TestBoundaryConditions::test_BOUNDARY_02
  _large_function）/ 277 passed / 2 xpassed；第 3 failed = product_freshness
  在位产物预存在陈旧（前轮已 A/B 实证非本轮引入）；比较器 pyc_verify.py
  SHA256 FE1902A9 冻结一致、tests/ 与 scripts/ 零改动。
- 全量 1556 闸门（v5r110 三分片对 v5r89 基线）**0 回归**：EQUAL 1180=1180、
  ERROR 376=376，对 v109 **1556 案 c4 verdict 逐案零变化**（连续第十轮零抖
  动）；分片汇总 shard0 367/152、shard1 406/113、shard2 407/111（与基线逐
  分片一致）。REAL46 sweep（v5r110 对 v5r109）**46 案 c4 verdict 逐案零变化
  0 回归**：13 DIFFERENT/15 EQUAL/17 ERROR+skip1（c2_pyc_missing=已登记
  REAL46-045）——REAL46-001 维持 DIFFERENT（剩余两函数独立疾病域在案，本
  轮叶闭合体现为判定器 R7 维 3→2 与字段级差异集移出）、REAL46-004 维持
  EQUAL。

## 诚实边界

- REAL46-001 叶闭合（`_get_slots` 字段级+判定器 R7 维 3→2 双双移出）；整案
  维持 DIFFERENT——剩余两函数独立疾病域在案。
- pe8（while-1 重构族，需派发表先行）、na5（while 条件嵌套 or 尾，loop 重
  构域）、REAL46-019 剩余病灶、未领姊妹 ca6/ca13/ca15/cb5 维持登记；46
  sweep 其余 DIFFERENT/ERROR 在案。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r110.diff` | [v110-MCSUB] 完整 diff（+17 行单文件一 hunk） |
| `mc1-mc12.py` | 变体矩阵（1 功效 + 11 控制） |
| `probe_match_guard.py`/`probe_match_bss.py` | 守卫块收集/in-match BSS 追踪插桩 |
| `dc_prod_v110.py`/`dc_fielddiff_v110.txt` | dataclasses 产品与字段级差异集 |
| `sd_r110.py`/`semantic_REAL46-004_v110.json`（+001） | 判官驱动与判定（EQUAL / R7 3→2） |
| `semantic_46_v5r110.json`（+report） | REAL46 sweep v5r110 实测（46 案逐案零变化） |
| `r110_regress.py`/`r110_regress_result.txt` | 169 案回归电池驱动与结果 |
