# ORCALL：值语境 or 链首块含推导式语句时前缀截断修复（rr-v5r103，Task 29，REAL46-004 族 D 闭合）

## 家族选定与根因

rr-v5r102 剩余登记：REAL46-004 叶差（族 D `EnumType._convert_.<dictcomp>`
removed）。本轮选**族 D**——`_convert_` 的
`body = {t[0]: t[1] for t in members}` 推导式整 code object 缺失，且
`body['__module__'] = module`、`tmp_cls = type(...)`、
`cls = _simple_enum(etype=cls, boundary=boundary or KEEP)(tmp_cls)` 三条
连带丢失，产品坍缩为 `cls = boundary or KEEP`。

根因（原件/产品并排 + 区域树转储 + pd1→pd4 梯度复现 + 逐消费者插桩）：
`_convert_` 中四条语句同落一个基本块（CPython 直到 or 短路跳转
JUMP_IF_TRUE_OR_POP 才断块）——分析端把该块登记为值语境 or 链
（BoolOpRegion@266 blocks=[266,366,378] op_chain=[(266,'or')]）。生成端
`_generate_boolop_impl` 的两个 `identify_block_prefix_instructions` 消费者
在该链首块上被 **GET_ITER 截断**：

- `identify_block_prefix_instructions`（region_analyzer 4627-4684）首扫描
  循环遇 GET_ITER 即 break（4638 停表），且 has_get_iter 回溯修剪
  （4659-4683）的「可继续表达式」白名单不含 MAKE_FUNCTION——块含完整推导式
  调用语句（LOAD_CONST <code> + MAKE_FUNCTION + iterable 装载 + GET_ITER +
  CALL + STORE 直落同块，CPython 3.11 推导式即独立 code object 的调用语句
  形状）时只返回悬空碎片（pd1 实测 2 条 [LOAD_CONST, MAKE_FUNCTION] vs
  pd2 无推导式形态全前缀 3 条 [PUSH_NULL, LOAD 装饰器, LOAD 实参]）。
- 消费者 ①pre_stmts 提取（region_ast_generator 50571）：碎片中无语句归约
  入口 → 50596 `last_stmt_end_idx=-1` → 前缀整段丢弃——三条前缀赋值蒸发。
- 消费者 ②拼接初始栈（51225 附近 `_init_stack`）：碎片 reconstruct 的残余
  栈丢失调用链前缀装载（PUSH_NULL/LOAD 装饰器/LOAD 实参），merge 块的
  KW_NAMES/PRECALL/CALL 续接重建错位 → `_full_rhs` 退化为裸 or 表达式 →
  `cls = f(etype=cls, boundary=boundary or KEEP)(tmp_cls)` 坍缩为
  `cls = boundary or KEEP`。

## 修复（region_ast_generator 只增不破，[v103-ORCALL]+[v103-ORCALL-2]，两消费者同款守卫）

两处 identify 调用点各加 GET_ITER 截断补全：链首块非噪声指令中存在
GET_ITER/GET_AITER，且其后、链尾短路跳转之前存在语句归约入口
（`_is_statement_reduction_entry`——推导式调用语句完整包含于本块的全结构
事实）时，直取全前缀（剥噪声、去链尾短路跳转——与链块「链首操作数块」定义
同构）。语句切分仍由既有逻辑承担（消费者①的 last_stmt_end_idx、消费者②的
last-STORE——消费端契约不变）。无 GET_ITER 的链首块（pd2/pd3 形）不命中，
C3 逐位保持。

## 验证（全实测）

- 复现矩阵：pd1（_convert_ 尾部四语句精确复现）/pd5（前置 listcomp + 双
  推导式）/pd6（推导式 + or kwarg 调用）/pd7（推导式 + 双 kwarg 含 or）/
  pd9（推导式 + 属性宿主 + 装饰器调用链）**v102 DIFF → v103 重编译全
  code object 逐字段 BYTE-EQUAL**（5 功效案，pd5-pd7/pd9 为 v102 下额外
  DIFF 的同族形态）；控制案 pd2/pd3/pd4（无推导式/纯 kwarg or/纯推导式）
  零变化——C3。
- 既有登记（本轮不修）：pd8/pd10（产品 v102/v103 逐字节相同——
  ternary-vs-if 渲染族兄弟形态，登记下轮）。
- REAL46-004（enum pyc sha 60e3ca30）：字段级 **removed 0（dictcomp 回归）、
  `<module>.EnumType._convert_` 从 real-diff 集移出**（v102→v103 产品文本
  差 = 精确恢复四条语句）；剩 real-diff = r100 已登记同态
  （EnumType.__new__、Flag._missing_、convert_class；`_convert_: co_consts`
  为推导式 code firstlineno 布局噪声）。权威 semantic_diff 单案复跑
  **EQUAL（diffs=[]）**。
- 前轮矩阵 60 案（nb/no/mt/va/fdt/pb/pv/pc/pm + pd 控制）：59 BYTE-EQUAL +
  nb2 维持既有登记差（与 v100 逐字节同签名）。
- 回归电池 60 案（r103_regress.py 双文件交换 A/B：v5r102 HEAD vs v103 同
  输入 pyc 反编译产物逐字节比对）55 TEXT-SAME（23 原案含 w28 w2/w3 v97
  既有同态 + 32 控制案）+ 5 功效案 TEXT-DIFF/BYTE-EQUAL。
- pytest 7 套件 2 failed（冻结对）/ 282 passed / 2 xpassed；比较器
  pyc_verify.py SHA256 FE1902A9… 冻结一致、tests/ 零改动。
- 全量 1556 闸门（v5r103 三分片对 v5r89 基线）**0 回归**：EQUAL 1180=1180、
  ERROR 376=376；对 v102 逐案 c4 verdict 零变化（连续第四轮零抖动）；
  分片汇总 shard0 367/152、shard1 406/113、shard2 407/111。
- REAL46 sweep（v5r103 对 v5r102）**46 案 c4 逐案零变化 0 回归**：14
  DIFFERENT/14 EQUAL/17 ERROR+skip1（c2_pyc_missing=已登记 REAL46-045）；
  REAL46-004 维持 EQUAL（diffs=[]）。

## 诚实边界

- 族 D 闭合——REAL46-004 四个叶差家族（族 A/B/C/D）至此全部闭合，整案
  维持 EQUAL（diffs=[]）。
- pd8/pd10（ternary-vs-if 渲染族）为预存在登记，本轮产品逐字节不变。
- nb2 平铺形维持登记；46 sweep 其余 14 DIFFERENT/17 ERROR 在案。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r103.diff` | [v103-ORCALL]+[v103-ORCALL-2] 完整 diff（含判据注释） |
| `pd1-pd7/pd9_variant.py` | 复现+变体矩阵（5 功效案 + 3 控制案） |
| `pd8/pd10_registered.py` + `*_out_v102/v103.py` | 既有登记形态（产品逐字节相同实证） |
| `REAL46-004_product_v103.py` | enum 产品（族 D 闭合状态） |
| `semantic_REAL46-004_v103.json`（+report） | 权威判定（EQUAL，diffs=[]） |
| `r103_regress.py` / `r103_regress_result.txt` | 60 案回归电池驱动与结果 |
