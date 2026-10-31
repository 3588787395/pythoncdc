# ARMTAIL：IfRegion 臂块被跨臂 BoolOpRegion 整链认领修复（rr-v5r98，Task 24，REAL46-004 第 4 形态闭合）

## 家族选定与根因

REAL46-004（enum.py）LOAD 失败链第 4 层（rr-v5r97 登记）：`_find_data_type_` 的 elif 臂尾
`data_types.add(candidate or base)` + `break` 迁移到内层 for 之后 → `_get_mixins_`
data_types = {StrEnum, str} → `class FlagBoundary(StrEnum)` TypeError。

根因（fdt 独立复现 + 区域树 + 逐调用点实证）：

- 区域树本身正确：IfRegion@314 blocks=[314,356,388] then=[356](continue) else=[388] merge=418；
  BoolOpRegion@358（参数链 `candidate or base`）blocks=[358,386,388]，value_target=None、
  is_condition_context=False、parent=LoopRegion——链的 merge/尾块 388 同时是 IfRegion 的 else 臂块，
  链首块 358/386 不在臂块集内（重叠层）。
- 发射分层错误：`_process_if_blocks` 臂扫描（branch='else'）到达 B388（BREAK 角色 + 有效指令）
  走通用重建 `_generate_block_statements(388)`——调用语句的 method/首操作数在链首块 B358 压栈，
  B388 单块重建返回 None → `data_types.add(...)` 丢失、Break 由 BREAK 角色分支单独补发；
  BoolOpRegion@358 稍后由循环层 `_loop_dispatch_block` 整链生成（R61 merge 延续路径），
  产出 `data_types.add(candidate or base)` + `break` 落在循环尾层级 → 语句迁移。
- 前驱事实：B358 preds=[314]（仅本 if 条件块）——链 exclusively 属于 else 臂。

## 修复（region_ast_generator 只增不破，[v98-ARMTAIL]，+47 行）

`_process_if_blocks` 臂扫描在 B71 守卫之后、BREAK 角色分支之前插入臂块跨臂表达式区域整树派发：
臂块 b ∈ 某 BoolOpRegion.blocks 且区域入口不在本臂块集（_block_set）时，整树派发
`_generate_boolop(R)`（臂语句以子区域为抽象节点，原则 2/3/4），其全部成员块登记已生成；
后续循环层走查经 _generated_regions 跳过，不再迁移。守卫全为结构事实：
①入口不在本臂块集且区域未生成/未在生成中/入口未被生成；
②条件形（is_condition_context）不取——条件链由所属 IfRegion 条件提取派发（镜像 R61 fallback 排除口径）；
③链入口全部前驱是本 if 的 entry 或本臂块（链仅由本 if 内部可达，不吞外部共享链）。

## 验证（全实测）

- fdt 独立复现（`_find_data_type_` 自包含抽取）：修复前 DIFF（else 臂剩 break、add+break 迁移
  for 尾、死 continue）→ 修复后重编译**全 code object 逐字段 BYTE-EQUAL**
  （co_code SHA256 c727c96bef754265 ×548 字节、异常表、consts、names、varnames、freevars、
  cellvars、argcount、flags、stacksize 全等）。文本层两个残差均证明 3.11.7 重编译字节恒等：
  死 `continue`（编译器丢弃）与 f-string vs 常量 %-format（常量 %r 格式+元组被折叠为
  FORMAT_VALUE/BUILD_STRING 同一序列）。
- REAL46-004（enum.cpython-311.pyc 重编译）：叶级函数差异 **5 → 4**
  （`_find_data_type_` 移出差异集；v97 集合 = {dictcomp(removed), _find_data_type_,
  StrEnum.__new__, _is_private, _proto_member.__set_name__} → v98 去掉 _find_data_type_；
  `<module>.EnumType._convert_.<dictcomp>` removed 为 v97 既有非本轮回归）；
  LOAD 链第 4 层消除——**FlagBoundary TypeError 消失**，推进到第 5 层
  `NameError: name 'member_type' is not defined`（convert_class）。
- 权威 semantic_diff REAL46-004：维持 **DIFFERENT**（60 维不变：LOAD+R0+R2+R3+R4+55×R5；
  LOAD 失败类型 TypeError→NameError 在 verdict 之下）。
- 回归电池 23 案（r98_regress.py，产物文本 v97↔v98 文件交换 A/B）：
  **22/23 TEXT-SAME**（fn_find_new、te1、mk_iterencode、yp1-8、er1-er4+er_variants、fe1、
  fe_variants、s3、te_shapes、te_variants8、w28 全部逐字节不变；其中 22 案重编译 BYTE-EQUAL、
  w28 的 w2/w3 重编译差为 v97 既有同态）；唯一 TEXT-DIFF = fdt（本轮修复目标）。
- pytest 7 套件：2 failed（TestDominanceFrontierIf::test_B01_simple_if_then_else_merge、
  TestBoundaryConditions::test_BOUNDARY_02_large_function 冻结对）/ 282 passed / 2 xpassed。
- 比较器冻结：scripts/pyc_verify.py SHA256
  FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4 一致、tests/ 零改动。
- 全量 1556 闸门（3 分片 vs v5r89 基线）与 REAL46 sweep：见本轮提交说明（0 回归）。

## 第 5 层登记（下一轮家族，未修）

LOAD 链推进到 `_simple_enum.convert_class`：源码 1669-1674 五条**多目标链式赋值**
`body['_x_'] = alias = value`（gnv/member_names/member_map/value2member_map/member_type）
产品全部丢失尾部别名 STORE（`body['_generate_next_value_'] = etype._generate_next_value_` 等），
`member_type` 首个使用点 NameError。最小复现（本目录）：
- mt3：**连续第二条**多目标赋值丢别名（`d['a'] = g = []` 保留 g、`d['b'] = h = {}` 丢 h，
  `return (g, h)` 仍引用 h）；
- mt5：嵌套函数（convert 闭包 + for k, v 循环消费别名 + return member_type）三条全丢。
单条形（mt1/mt2/mt4：常量/空列表/属性 RHS 均正常）不触发——触发条件与连续性/嵌套函数上下文相关，
下一轮做逐函数字节比对定位发射层。

## 诚实边界

- REAL46-004 未达 EQUAL（第 5 层阻塞 LOAD）；权威判定维持 DIFFERENT（60 维）。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r98.diff` | [v98-ARMTAIL] 完整 diff（含三重结构守卫注释） |
| `fdt.py` / `fdt.pyc` | 第 4 形态独立最小复现（源 + 编译产物） |
| `fdt_out_v97_prefix.py` / `fdt_out_v98.py` | 修复前/后产品 A/B（迁移缺陷消除） |
| `REAL46-004_product_v5r98.py` | enum 产品（第 4 层闭合状态） |
| `case_REAL46-004_v98.json` / `semantic_REAL46-004_v98.json` | 权威判定（DIFFERENT 60 维，LOAD 第 5 层 NameError） |
| `mt3_layer5_repro.py/.pyc` / `mt5_layer5_repro.py/.pyc` | 第 5 层登记复现（连续链式赋值/嵌套函数丢别名） |
| `r98_regress.py` | 23 案回归电池驱动（文件交换 A/B + 重编译逐字段比对） |
