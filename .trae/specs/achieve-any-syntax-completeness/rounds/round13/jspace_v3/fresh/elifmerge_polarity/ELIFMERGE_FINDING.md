# ELIFMERGE：连续 if-raise 合并 elif 链丢臂极性修复（rr-v5r101，Task 27，REAL46-004 族 B 闭合）

## 家族选定与根因

rr-v5r100 剩余登记：REAL46-004 叶差 3 项（族 B `StrEnum.__new__` / 族 C
`_proto_member.__set_name__` / 族 D `_convert_.<dictcomp>`）。本轮选**族 B**：
`StrEnum.__new__` 的源码是连续 `if`-`raise` 序列（str.__new__ 的参数检查四连臂），
产品端合并为 elif 链时**丢一个臂的 `not`**（1 跳转极性翻转
POP_JUMP_FORWARD_IF_TRUE→FALSE）。

根因（pb1→pb2 逐级逼近复现 + 区域树/逐构建器插桩 + 调用点追踪）：族 B 叶差在
**发射层有两个兄弟位点**，取决于臂的位置与区域嵌套——

| 形态 | 复现 | 症状 | 位点 |
|---|---|---|---|
| 非末臂（嵌套 IfRegion 的主 if） | pb1/pv6/pv9（≥3 臂梯） | `and not isinstance(...)` 写成 `and isinstance(...)`——**丢 not** | `_build_boolop_condition_from_chain`（31474-31499） |
| 末臂（elif_bodies[1] 路径） | pb2（3 臂） | `A and not B` 写成 `not (A and not B)`——**多整体 not** | `_if_generate_full_elif_chain` 末臂 negate 启发式（25780-25800） |

- pb1（4 臂）区域树：顶层 IfRegion@0 elif_conditions=[70,192,314]，条件块 192
  同时是嵌套 IfRegion@192 的入口（嵌套 GEFC 把 arm3 当主 if 处理）。主 if 条件
  经 `_if_extract_condition_from_instructions`（19762）→ 31056
  `_build_boolop_condition_from_chain`——该链构建器逐成员重建时只剥离跳转
  （31474 `pure`），**不回读跳转极性**：and 链成员以 IF_TRUE 族极性跳出
  （`A and not B` 的 `not B` 操作数，CPython peephole 把 UNARY_NOT 优化进跳转
  方向）时原始表达式 X 直接入链，`not` 蒸发。对照：同函数 elif 臂路径
  （25242）与末臂路径（25776）走 `_build_boolop_expression`，其内部
  `_build_boolop_expression_inner` 49462-49470 有 canonical implicit-not 折叠
  （and 链成员 TRUE 极性 → 包 `not`）——BBE 插桩实证两臂表达式均正确折叠
  `not(CALL(isinstance))`，唯主 if 路径缺失。
- pb2（3 臂）区域树：单层 IfRegion@0 elif_conditions=[70,192]，arm3=末臂走
  25776 专属路径。重建表达式正确（BBE entry=192 折叠 ✓），但末臂 negate 启发式
  `_last_elif_negate = (jump ∈ elif_bodies[1]) != IF_TRUE`（25799）在
  uniform-and 链（成员 192 PJF→314 + 成员 230 PJT→314 同目标）上误判
  `(314 ∈ {284})=False != True → negate=True` → 整体 `_negate_expr` 包装。
  **非末臂路径有同款守卫**（W14-A 25252-25277：全员同目标且非全员 IF_TRUE →
  跳过整体取反，注释自述「按跳转方向取反会错写为 not (A and not B)（真值表
  改变）」）——末臂路径无此守卫，即同链两臂输出分叉的根因。

## 修复（region_ast_generator 只增不破，[v101-CHAINPOL]+[v101-ELIFNEG]，+49 行两 hunk）

1. **[v101-CHAINPOL]**（31499 `chain.append` 前，+14 行）：镜像 BBE 49462-49470
   与 GEFC ibc 消费者 19797-19798 的 canonical 折叠——and 成员（chain_op 由
   31454-31469 依跳转目标/极性归一）+ 跳转 IF_TRUE 族 + 非 NONE_CHECK 成员
   （身份比较语义已在 31478-31498 依 NONE 极性还原，不在此列——C3 保持其既有
   输出逐位不变）→ 包 `{'type':'UnaryOp','op':'not'}`。or 链成员（含末成员
   IF_FALSE 值块豁免）维持旧行为不折叠（未观测形态不扩域）。
2. **[v101-ELIFNEG]**（25780 末臂 negate 入口前，+35 行）：逐字镜像 25252-25277
   的 `_w14_uniform_and` 守卫（全员同目标 → `all(t is tgts[0])`，且非全员
   IF_TRUE——[R14c] 全员 IF_TRUE 同目标链是负极性 or 链 `not (A or B ...)`，
   不算 uniform-and，整体取反必须生效）——uniform-and 时跳过末臂整体取反，
   极性由逐项 implicit-not 携带。

调用点正交性：`_build_boolop_condition_from_chain` 唯一调用方（31056）的
整体 negate 决策（31067-31100）自带同款 W14/R14c/mixed-polarity 守卫——
uniform-and 链不做整体取反、逐成员极性由折叠携带，互补无双重翻转。

## 验证（全实测）

- A/B 文件交换（v100 HEAD vs v101）：复现矩阵 **14/14 重编译全 code object
  逐字段 BYTE-EQUAL**——修复功效案 4（pb1/pb2/pv6/pv9：v100 DIFF→v101
  BYTE-EQUAL）+ 控制案 10（pb3/pb4/pv1-pv5/pv7/pv8/pv10：v100 已 BYTE-EQUAL，
  v101 零变化——C3 证据，含 pv2 R14c 负极性 or 链整体取反守卫负例）。
- 前轮复现矩阵 27 案：26 BYTE-EQUAL + nb2 维持既有登记差（与 v100 逐字节
  同签名，非本轮新差）。
- REAL46-004（enum.cpython-311.pyc sha 60e3ca30）：字段级比对 v101 vs r100
  产品——**唯一变化 `<module>.StrEnum.__new__: co_code` 移出差异集**（族 B
  闭合），零新增零回归；剩 real-diff = 既有登记族（族 C `__set_name__`
  co_code+co_exceptiontable、族 D `_convert_`+dictcomp removed、
  EnumType.__new__/Flag._missing_/convert_class r100 已存在同态）。
  权威 semantic_diff 单案复跑 **EQUAL（diffs=[]）**（c4 verdict EQUAL、
  seed 0、与 v100 单案证据同构）。
- 回归电池 37 案（r101_regress.py 文件交换 A/B：v5r100 HEAD vs v101 同输入
  pyc 反编译产物逐字节比对）**23 原案全 TEXT-SAME**（fn_find_new/te1/
  mk_iterencode/yp1-8/er1-er4+er_variants/fe1/fe_variants/s3/te_shapes/
  te_variants8/w28/fdt 零变化；w2/w3 重编译差 v97 既有同态）+ 14 新案
  （4 功效案 TEXT-DIFF/BYTE-EQUAL + 10 控制案 TEXT-SAME）。
- pytest 7 套件 2 failed（冻结对 TestDominanceFrontierIf::test_B01、
  TestBoundaryConditions::test_BOUNDARY_02）/ 282 passed / 2 xpassed；
  比较器 pyc_verify.py SHA256 FE1902A9… 冻结一致、tests/ 零改动。
- 全量 1556 闸门（v5r101 三分片对 v5r89 基线）**0 回归**：EQUAL 1180=1180、
  ERROR 376（v100 为 375+NO_C4 1）；对 v100 唯一 verdict 变化
  JS-LISTCOMP-004 probe_only→ERROR——单案复跑（--offset 556 --limit 1）=ERROR
  与 v98/v99 基线 c4 逐字一致（v100 该案 4 路并发判定未产出 NO_C4，本轮记录到
  真实基线值），定性为已登记的并发反编译超时抖动族非回归；分片汇总
  shard0 367/152、shard1 406/113、shard2 407/111。
- REAL46 sweep（v5r101 对 v5r100）**46 案 c4 逐案零变化 0 回归**：14
  DIFFERENT/14 EQUAL/17 ERROR+skip1（c2_pyc_missing=已登记 REAL46-045）；
  REAL46-004 维持 EQUAL（diffs=[]）。

## 诚实边界

- 族 B 两个发射位点本轮一并闭合（同叶差签名、同方法域、互为兄弟形态）；
  REAL46-004 剩余 real-diff 项（族 C/D 及 EnumType.__new__ 等）为 r100 已
  登记同态，本轮未触碰。
- nb2 平铺形（无前缀语句、链首即条件块的 or 尾——or 链检测域）维持登记。
- 46 sweep 其余 DIFFERENT/ERROR 案在案。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r101.diff` | [v101-CHAINPOL]+[v101-ELIFNEG] 完整 diff（+49 行，含判据注释） |
| `pb1-pb4_repro.py` / `*_out.py` | 四形态复现（修复后产品） |
| `pv1-pv10_variant.py` | 十变体矩阵（4 功效案 + 6 控制案，含 pv2 R14c 守卫负例） |
| `v100_baseline.txt` | v100 A/B 基线（4 DIFF + 10 控制绿） |
| `REAL46-004_product_v101.py` | enum 产品（族 B 闭合状态） |
| `semantic_REAL46-004_v101.json`（+report） | 权威判定（EQUAL，diffs=[]） |
| `r101_regress.py` / `r101_regress_result.txt` | 37 案回归电池驱动与结果 |
