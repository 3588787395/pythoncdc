# SUBNAM：下标赋值兜底伪 Name/伪常量值幽灵赋值修复（rr-v5r109，Task 35，REAL46-001 叶闭合 `_add_slots`）

## 家族选定与根因

rr-v5r108 剩余登记选 **REAL46-001（dataclasses.cpython-311，stdlib，sha
d87ac1e1）叶**——判定器 4 个 R7 维中取 `_add_slots`（co_consts.v[73]）：
产品在真实语句 `cls_dict['__slots__'] = tuple(itertools.filterfalse(...))`
之后多发一条幽灵赋值 `cls_dict['__slots__'] = 1`（重编译 +10 字节，
co_code/co_consts 双差）。

根因（AST 出生层逐层定位：_write_line → code_generator ASTAssign →
converter `_convert_name_full` ← 区域层 dict `{'type':'Name','id':'1'}` →
`_build_subscript_assign` 输入缓冲转储 + reconstructor 孤立缓冲重放）：

①**缓冲错位**：赋值值内的三元 `('__weakref__',) if weakref_slot else ()`
注册 TernaryRegion，区域消费其条件+值块直至 merge——merge 侧残余
`[孤立 CALL 链（callable/实参指令已被上游消费）, LOAD cls_dict, LOAD
'__slots__', STORE_SUBSCR]` 落入 for 迭代前缀（`for field_name in
field_names:` 与赋值同块直线延伸），`_loop_extract_for_iter_pre_stmts` 的
STORE_SUBSCR 分支再次消费该缓冲（**重复消费**——真实赋值已由上游三元
value_target 消费端发射，产品两句并存即证）。

②**幽灵出生**：`_build_subscript_assign` 的 reg-stack 路径栈深 2（<3）跳
过；legacy 兜底 `reconstruct(孤立 CALL 链) → None`（callable 缺失无归约）
→ **盲兜底 `value_expr = {'type': 'Name', 'id': str(value_instrs[-1].argval)}`
——末指令 CALL 的 arg=1（argc）被 str() 成名字 '1'** → 幽灵
`Assign(Subscript(cls_dict['__slots__']), Name('1'))`，渲染 `= 1`。

③**姊妹形态（cb3/cb11/cb12 实测）**：值指令**全空**（整值经跳转结构由上
游消费，缓冲仅 `[LOAD obj, LOAD key, STORE_SUBSCR]`）→ 空值兜底
`Constant(None)` → 幽灵 `d[k] = None`；嵌套下标目标 `lst[0]` 同形 →
`lst[0] = 2`。双形态同一根源：**兜底从非名字事实伪造值节点**。

## 修复（region_ast_generator 只增不破，[v109-SUBNAM]，+37 行三 hunk）

- `_build_subscript_assign` obj 兜底 + value 兜底、
  `_build_complex_name_chain_assign` value 兜底：`str(argval)` 伪 Name 仅对
  **真名字装载指令**（LOAD_FAST/LOAD_NAME/LOAD_GLOBAL/LOAD_DEREF——argval
  即变量名）合法；其余（LOAD_CONST 的 argval 是常量值、CALL 的 argval 是
  argc 整数）返回 **None** 整条语句不在此层发射（真实赋值已由上游区域消
  费端发射，防幽灵重复发射）。
- 两处空值兜底 `Constant(None)`（值指令空）：返回 None（缓冲不含值指令
  = 值经跳转结构由上游消费，本层无值可发）。
- **C3**：名字装载兜底路径逐位不变（reconstruct 失败且末指令为名字装载时
  旧行为保留）；非名字兜底本就产出恒错的伪标识符/伪 None（编译为错误语
  义），返回 None 仅删除错误发射；调用方（提取器分支/链别名/R102 委托）
  均有 None 处理路径。

## 验证（全实测）

- **复现矩阵 12 案**：功效案 5——cb1（调用值内嵌三元+下标赋值+for，
  Name('1') 形）/cb2（dataclasses _add_slots 精确形）/cb3（三元整值+for，
  Constant(None) 形）/cb11（直接三元值+for）/cb12（嵌套下标目标 lst[0]
  +for）——v108 TEXT-DIFF→v109 重编译全 code object 逐字段 **BYTE-EQUAL**；
  控制案 6——cb4（无三元）/cb6（无 for）/cb7（无 for+普通后续）/cb8（链式
  多目标 [v99] 域）/cb9（[R102] 增广下标）/cb10（模块级）零变化——C3。
- **未领姊妹形态 1 案（cb5：STORE_ATTR 目标+三元值+for——整语句被吞进
  for 迭代表达式；v107==v109 逐字节同 A/B 直证，v105-TERNSUB 姊妹域，如实
  登记留待后续轮）**。
- **REAL46-001（dataclasses.cpython-311.pyc sha d87ac1e1）**：产品幽灵语句
  消失；字段级真实差异集 `_add_slots` **移出**（co_consts 表逐元素相等，
  仅剩嵌套 code repr 噪声与 firstlineno 类）；semantic_diff 单案复跑 R7 维
  **4→3**（剩余 v[47]=_get_field / v[69]=_process_class / v[72]=_get_slots
  ——各自独立疾病域，维持 DIFFERENT 在案）。
- **REAL46-004（enum.cpython-311.pyc sha 60e3ca30）**：单案权威
  semantic_diff 复跑 **EQUAL（diffs=[]）**。
- 回归电池 **157 案**（r109_regress.py 双文件交换 A/B：v5r108 HEAD=fb15a17b
  vs v109 同输入 pyc 反编译产物逐字节比对 + 逐顶层函数重编译比对）**5 功效
  案（cb1/cb2/cb3/cb11/cb12）TEXT-DIFF/BYTE-EQUAL + 152 TEXT-SAME**（23 原
  案 + r108 全部已闭合功效案稳定为 TEXT-SAME/BYTE-EQUAL + 控制案；既有登记
  差维持与 r108 逐字节同签名：w28_shapes w2/w3、ca6、ca13、ca15、cb5、na5、
  pd8_prod、pe8、pe8_target）。
- pytest 7 套件 **冻结对一致 2 failed**（TestDominanceFrontierIf::test_B01
  _simple_if_then_else_merge、TestBoundaryConditions::test_BOUNDARY_02
  _large_function）/ 277 passed / 2 xpassed；第 3 failed = product_freshness
  在位产物预存在陈旧（前轮已 A/B 实证非本轮引入）；比较器 pyc_verify.py
  SHA256 FE1902A9 冻结一致、tests/ 与 scripts/ 零改动。
- 全量 1556 闸门（v5r109 三分片对 v5r89 基线）与 REAL46 sweep（v5r109 对
  v5r108）：见 semantic_shard{0,1,2}_v5r109.json 与 semantic_46_v5r109.json
  实测记录。

## 诚实边界

- REAL46-001 叶闭合（`_add_slots` 字段级+判定器 R7 维 4→3 双双移出）；整案
  维持 DIFFERENT——剩余三函数各自独立疾病（_get_field 跳转目标偏移、
  _get_slots match/case 渲染 +NOP、_process_class 多维）在案。
- cb5（STORE_ATTR+三元值+for 语句吞入迭代）与 v108 逐字节同，未领留待。
- pe8（while-1 重构族，需派发表先行）、na5（while 条件嵌套 or 尾，loop 重
  构域）、REAL46-019 剩余病灶维持登记；46 sweep 其余 DIFFERENT/ERROR 在案。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r109.diff` | [v109-SUBNAM] 完整 diff（+37 行单文件三 hunk） |
| `cb1-cb12.py` | 变体矩阵（5 功效 + 6 控制 + 1 未领姊妹） |
| `probe_subnam_birth.py` | 幽灵出生点输入缓冲转储插桩 |
| `disdiff.py`/`enum_fielddiff.py` | 逐指令比对器/字段级比对器 |
| `dc_prod_v109.py`/`dc_fielddiff_v109.txt` | dataclasses 产品与字段级差异集 |
| `sd_r109_004.py`/`semantic_REAL46-004_v109.json` | enum 案权威判定（EQUAL） |
| `sd_r109_001.py`（合入 004 驱动）/`semantic_REAL46-001_v109.json` | dataclasses 案判定（R7 4→3） |
| `r109_regress.py`/`r109_regress_result.txt` | 157 案回归电池驱动与结果 |
