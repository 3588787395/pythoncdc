# ORTAIL：and 链尾嵌套 or 操作数被截断修复（rr-v5r100，Task 26，REAL46-004 整案 EQUAL）

## 家族选定与根因

rr-v5r99 剩余登记：REAL46-004 叶差 4 项。本轮逐项解剖定位：

| 叶差 | 形态 | 处置 |
|---|---|---|
| `_is_private` co_consts 8→6 | `and` 链尾嵌套 BoolOp(or) 操作数（`and (name[-1] != '_' or name[-2] != '_')`）整体丢失——12 指令 + 常量 '-1'/'-2' 蒸发 | **本轮修复（族 A）** |
| `StrEnum.__new__` | elif 链合并丢一个臂的 `not`（1 跳转极性翻转 POP_JUMP_FORWARD_IF_TRUE→FALSE） | 登记（族 B，下轮） |
| `_proto_member.__set_name__` | 循环体多一条 JUMP_BACKWARD（重复回边，其余为 +2 目标移位） | 登记（族 C，下轮） |
| `EnumType._convert_.<dictcomp>` removed | dict 推导式整对象缺失 | 登记（既有，族 D） |

族 A 根因（nb1→nb2→nb3 逐级逼近复现 + 区域树 + 逐构建器插桩 + 调用点追踪）：

- 分析端 `_identify_conditional_regions` Step 6 的 and 短路链走查（region_analyzer
  23145-23217）在首个 IF_TRUE 极性接点终止（`if 'IF_TRUE' in _main_ft_last.opname:
  break`——or 接点不入 and 链的平铺混链防护）→ `inline_boolop_chains` 链截断于
  [0,196,238]（操作数 1-3），嵌套 or 的两个链块（300/350）不入链；
- 同一分析器已把完整梯级记入 BoolOpRegion@196 的 op_chain
  `[(196,'and'),(238,'and'),(300,'or'),(350,'and')]`（末 or 成员假边携带 'and' 标签），
  且把 or 真出口块（300/350/400）归入 IfRegion.then_blocks；
- 生成端 `_if_generate_normal` 的 ibc 消费者（27162-27397）按链 [0,196,238] 平铺重建
  `BoolOp(and, [A0, A1, A2])`——尾操作数丢失。既有 `_try_build_and_inner_or_pattern`
  （and 内嵌 or 检测器）只覆盖负极性形（or 成员 IF_TRUE→merge，`a and not (b or c)`）
  与 R7-B45 循环形（真出口=循环头），正极性 if 形（or 成员 IF_TRUE→then）不在其
  守卫内；nb2（无前缀语句、链首即条件）另经 or 链路径输出平铺 `... and D or E`
  （优先级错误）——同族兄弟形态，登记下轮。

## 修复（region_ast_generator 只增不破，[v100-ORTAIL]，+124 行）

`_if_generate_normal` ibc 消费者平铺重建之后、negate 包装之前插入链尾嵌套 or 吸收：

- 识别条件（全部同层结构事实）：①本区域直接子 BoolOpRegion 的 op_chain 包含链末块
  （分析端把嵌套 or 与 and 链记入同一 op_chain）；②op_chain 中链末块之后的尾部条目
  极性 = 非末条全部 IF_TRUE 族（NONE_CHECK 族镜像 or 链 [R75] 翻转口径）且跳转目标
  ∈ region.then_blocks（真出口），末条 IF_FALSE 族且跳转目标 == 链末块条件跳转目标
  （链假出口）；单条目尾自动拒绝；③尾部块剔除跳转后指令段 reconstruct 非空；
  ④尾部块不在链内（链块唯一归属）。
- 归约方式：尾部操作数按序重建为 BoolOp(or, [...])，追加为 and 链最后一个操作数
  （嵌套即抽象节点）；尾部块登记 generated/generated_offsets（原则 2）。AST 映射：
  `If(test=BoolOp(and, [A0, ..., BoolOp(or, [C, D])]))`——CPython 测试语境把
  `and (C or D)` 编译为 C 的 POP_JUMP_IF_TRUE→真出口 + D 的 POP_JUMP_IF_FALSE→汇合，
  与原始字节码逐条一致。
- 归属注记：尾部块可能已被 BoolOpRegion 条件路径（`_if_extract_condition_from_
  instructions` 31174 的 generated 认领）预先标记——该路径产出的表达式随后被本
  ibc 重建覆盖（无语句发射），generated 标记不构成「已发射」证据，故不做
  generated 排除；重复发射由极性/目标守卫与 1556 闸门约束。

修复过程记录：首版补丁曾因 `_v100_tail_parts`/`_v100_tail_blocks` 未初始化
（NameError 传出 `_if_generate_normal` → 上游回退降级为 `if A0: pass / else: ...`）
——进程内异常捕获定位后补初始化；该 NameError 传播路径即 ibc 重建被上游
try/except 回退吞并的实证。

## 验证（全实测）

- 复现矩阵 **12/12 重编译全 code object 逐字段 BYTE-EQUAL**：
  nb1（return 语境 or 尾——既有正确路径不回归）、nb2（无前缀语句平铺形——既有
  登记差不变）、nb3（enum `_is_private` 精确复现：前置赋值 + if/else + 正极性 or 尾）
  + no1（最小 2-and+or 尾）/no2（3-and+3-or 尾）/no4（elif 条件内 or 尾）/
  no5（is-None or 尾，NONE_CHECK 翻转路径）/no7（3 成员 or 尾）/no8（or 居链中
  ——守卫负例拒绝，C3）/no9（or 头 and 尾——R68-D4 域不回归）/no10（值语境）。
- REAL46-004（enum.cpython-311.pyc）：叶级函数差异 **4 → 3**（`_is_private` 移出
  差异集；剩 dictcomp removed + StrEnum.__new__ + _proto_member.__set_name__ 为
  既有登记族）；权威 semantic_diff **DIFFERENT 2 维 → EQUAL（diffs=[]）**——
  R0-R7 全维全过，enum.py 产品与原件语义完全相等（LOAD 链 rr-v5r97 起
  UnboundLocalError×2→TypeError→NameError 四层逐轮消除后，本轮最后 2 个 R7
  维度闭合，整案 60 维→2 维→0 维轨迹完成）。
- 回归电池 23 案（r100_regress.py 文件交换 A/B：v5r99 HEAD vs v100 同输入 pyc
  反编译产物逐字节比对）**23/23 TEXT-SAME**（w2/w3 重编译差为 v97 既有同态）。
- pytest 7 套件 2 failed（冻结对）/ 282 passed / 2 xpassed；比较器 pyc_verify.py
  SHA256 FE1902A9… 冻结一致、tests/ 零改动。
- 全量 1556 闸门（3 分片 vs v5r89 基线）与 REAL46 sweep：见本轮提交说明（0 回归）。

## 诚实边界

- REAL46-004 达 EQUAL（本轮闭合）；46 sweep 其余 14 DIFFERENT/17 ERROR 案在案
  （REAL46-045 skip 维持）。
- nb2 平铺形（无前缀语句、链首即条件块的 or 尾）为同族兄弟形态，本轮不触发
  修复路径（链构造走 or 链检测域），登记下轮。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r100.diff` | [v100-ORTAIL] 完整 diff（+124 行，含判据注释） |
| `nb1-nb3_repro.py` / `*_out_v100.py` | 三形态复现（修复后产品） |
| `no1-no10_variant.py` | 八变体矩阵（含 no8/no9 守卫负例） |
| `REAL46-004_product_v5r100.py` | enum 产品（整案 EQUAL 状态） |
| `case_REAL46-004_v100.json` / `semantic_REAL46-004_v100.json` | 权威判定（EQUAL，diffs=[]） |
| `r100_regress.py` | 23 案回归电池驱动 |
