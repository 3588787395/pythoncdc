# NCSTMT：NONE_CHECK continue 融合丢臂内语句修复（rr-v5r104，Task 30，pc6 形态闭合）

## 家族选定与根因

rr-v5r103 剩余登记：pc6 形态——while 语境 continue 臂丢臂内语句。本轮选它
（pc6 复现在手、与族 C 同属循环臂内容域）。

根因（区域树转储 + pe1→pe7 二分 + 逐位点插桩）：pc6/pe5 的循环体内 if 前置
赋值（`d = items[i]` 独立块）使 if/elif 不成区域、由循环体通用走查渲染——
NONE_CHECK 条件（POP_JUMP_FORWARD_IF_NOT_NONE）命中 `_try_generate_
conditional_break_or_continue` 的 **while19 fix 融合**（region_ast_generator
15219-15240）：落空侧（fall-through）为 continue 目标块且跳转目标非出口时，
直接发射 `If(test=is-none 比较, body=[{'type':'Continue'}])` 并提前 return——
**臂块内用户语句被丢弃**（`i += 1` 蒸发，重编译少 4 条指令）。同函数姊妹
路径 **[R02 fix]**（15450-15463，非 NONE_CHECK 形）已有正确模式：fall-through
含有效语句时保留语句再追加 Continue——NONE_CHECK 融合缺同款镜像即根因
（pe5 实测：最小形 `while: d=items[i]; if d is None: i += 1; continue / ...`
臂内语句丢失；pe1 无前置赋值形态不触发、字节相等）。

## 修复（region_ast_generator 只增不破，[v104-NCSTMT]，+22 行一 hunk）

NONE_CHECK 融合发射前镜像 [R02 fix]：`_generate_block_statements(_fall_
through_block)` 含非 Continue 成员时，语句 + Continue 作为 if 臂发射，块登记
generated/generated_offsets（原则 2：臂块归本融合发射，与 R02 同款）；纯
continue 块（while19 fix 原形）不命中新分支、走原路径逐位不变（C3）。

## 验证（全实测）

- 复现矩阵：**8 功效案** pc6（enum 形态精确复现）/pe5（最小形）/pe6（elif
  +break）/pe7（尾部无 i+=1）/pe9（双语句臂）/pe11（elif 链）/pe12（嵌套
  while 双层）/pe14（else 尾形）——v103 DIFF → v104 重编译全 code object
  逐字段 BYTE-EQUAL；**6 控制案** pe1-pe4/pe10/pe13（无前置赋值/for 语境/
  普通比较条件）v103 已绿 v104 零变化——C3。
- 既有登记（本轮不修）：pe8（while-1 重构族兄弟形态，`if d is not None:
  ... continue` 跳转目标侧 continue）——产品 v103/v104 逐字节相同。
- REAL46-004（enum pyc sha 60e3ca30）：产品与 v103 逐字节相同、diffed 集
  不变（7 项 = r100 已登记同态）；权威 semantic_diff 单案复跑
  **EQUAL（diffs=[]）**。
- 前轮矩阵 59 案（nb/no/mt/va/fdt/pb/pv/pc/pm/pd 控制）：58 BYTE-EQUAL +
  nb2 维持既有登记差（与 v100 逐字节同签名）。
- 回归电池 74 案（r104_regress.py 双文件交换 A/B：v5r103 HEAD vs v104 同
  输入 pyc 反编译产物逐字节比对）66 TEXT-SAME（23 原案含 w28 w2/w3 v97
  既有同态 + 43 控制案）+ 8 功效案 TEXT-DIFF/BYTE-EQUAL。
- pytest 7 套件 2 failed（冻结对）/ 282 passed / 2 xpassed；比较器
  pyc_verify.py SHA256 FE1902A9… 冻结一致、tests/ 零改动。
- 全量 1556 闸门（v5r104 三分片对 v5r89 基线）**0 回归**：EQUAL 1180=1180、
  ERROR 376=376；对 v103 逐案 c4 verdict 零变化（连续第五轮零抖动）；
  分片汇总 shard0 367/152、shard1 406/113、shard2 407/111。
- REAL46 sweep（v5r104 对 v5r103）**46 案 c4 逐案零变化 0 回归**：14
  DIFFERENT/14 EQUAL/17 ERROR+skip1（c2_pyc_missing=已登记 REAL46-045）；
  REAL46-004 维持 EQUAL（diffs=[]）。

## 诚实边界

- pc6 形态闭合；pe8（while-1 重构族）为预存在登记，本轮产品逐字节不变。
- pd8/pd10（ternary-vs-if 渲染族）、nb2 平铺形维持登记；46 sweep 其余
  14 DIFFERENT/17 ERROR 在案。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r104.diff` | [v104-NCSTMT] 完整 diff（+22 行，含 R02 镜像判据注释） |
| `pc6_repro.py` / `pe1-pe7/pe9-pe14_variant.py` | 复现+变体矩阵（8 功效案 + 6 控制案） |
| `pe8_registered.py` + `pe8_out_v103/v104.py` | 既有登记形态（产品逐字节相同实证） |
| `pe_v103_baseline.txt` | v103 A/B 基线（4 DIFF + 4 控制绿） |
| `REAL46-004_product_v104.py` | enum 产品（与 v103 逐字节相同） |
| `semantic_REAL46-004_v104.json`（+report） | 权威判定（EQUAL，diffs=[]） |
| `r104_regress.py` / `r104_regress_result.txt` | 74 案回归电池驱动与结果 |
