# CHAINALIAS：多目标链式赋值尾部别名 STORE 丢失族修复（rr-v5r99，Task 25，REAL46-004 LOAD 链全闭合）

## 家族选定与根因

rr-v5r98 登记的第 5 层：`_simple_enum.convert_class` 源码五条多目标链式赋值
`body['_x_'] = alias = value`（gnv/member_names/member_map/value2member_map/member_type）
产品全部丢失尾部别名 STORE → `member_type` 首个使用点 NameError。

根因（mt1-mt5 逐级逼近复现 + 逐构建器插桩 + 调用点追踪实证）——**同一字节码事实
（CPython 3.11 多目标赋值编译协议 `<value>; COPY 1; <obj/key>; STORE_SUBSCR|STORE_ATTR;
STORE_<简单名>`，末目标直接消费原值份额）在五条语句重建路径上均无整链归约覆盖**：

| 路径 | 缺口 | 触发形态 |
|---|---|---|
| B107 `_build_chained_complex_target_assign` | 要求复杂 STORE 数 ≥ 2——[复杂, 名] 2 目标链不认领 | 所有 [下标/属性, 别名] 链 |
| B85 `_scan_prefix_chain_assign`（BSI STORE 分支） | 要求累积段以 COPY(1) 收尾（纯名前缀链）——复杂目标链的累积段以 STORE_SUBSCR 收尾 | BSI 路径全部 |
| W16 混合链路径（`_generate_block_statements_body`） | 要求链首 store == 全块首 store——前置语句（`body = {}`）令首 store 为普通名 STORE → 整链跳过 | mt5（嵌套函数前置语句） |
| W16 兄弟段过滤器 | `_pre_body_m` 剥除 COPY（纯名链路径 `_rem_clean` 不剥）——链后紧邻的下一条多目标赋值失链退化单目标 + 别名 STORE 被吞 | mt3（连续第二条链） |
| 语句走查/BSI 落点 | 深度保持分支续接后的尾随别名 STORE 落入 `_build_subscript_assign`/`_build_attr_assign` 被静默吞没 | mt3/mt5/va7 |

三条触发路径实测：mt3（连续第二条丢别名——W16 兄弟段剥 COPY）、
mt5（嵌套函数前置 `body = {}` 全丢——走查吞别名 STORE）、
va7（循环体 if 守卫 `d[x] = alias = x` 丢别名——`_if_extract_cond_instructions`
条件前缀提取器在 STORE_SUBSCR 处先行冲刷）。

## 修复（region_ast_generator 只增不破，[v99-CHAINALIAS]，+六编辑）

1. **新构建器 `_build_complex_name_chain_assign`**：[复杂目标, 尾随名] 2 目标链整链
   归约。判据全为结构事实（I.4 白名单：opcode 序 + CPython 值栈净效应）：末条简单名
   STORE、紧邻前驱为 STORE_SUBSCR/STORE_ATTR、obj/key 装载窗口（`_B54_LOADISH_OPS`）
   左邻为 COPY(1)、值段非空且不含语句终结指令、整段净栈深 == 0（复制份额与原值份额
   全部落目标）、obj/key 窗口经 `_w16_split_value_groups` 分组数 == 复杂 store 需求
   （STORE_SUBSCR=2 / STORE_ATTR=1）。产出 Assign(targets=[complex, Name],
   is_chain_assign=True)。任一判据不满足返回 None（C3）。
2. **BSI STORE 归约点插入**（`_build_statements_from_instructions` STORE 分支
   `_build_store_statement` 前）：深度保持续接后的尾随别名 STORE 整链归约。
3. **普通块走查 STORE 归约点插入**（69288 同位）：既有 has_copy 前瞻以「下一 STORE
   前无非 STORE 指令」为链判据（obj/key 装载在两 store 之间即 break），值切片含
   STORE_SUBSCR 时 reconstruct 失败——新分支先行。
4. **W16 兄弟段过滤器保留 COPY**（`_pre_body_m` 剥除表移除 COPY；对齐纯名链路径
   `_rem_clean`；SWAP 维持剥除——返回值栈清理协议域无兄弟段证据）。
5. **`_loop_extract_for_iter_pre_stmts` STORE_SUBSCR/STORE_ATTR 分支前瞻归约**：
   buf 以链协议收尾且下一有效指令为简单名 STORE 时整链归约 + `_unpack_skip_remaining=1`
   跳过被吸并的别名 STORE（mt5 缝合点）。
6. **`_if_extract_cond_instructions` STORE_SUBSCR/STORE_ATTR 分支前瞻归约**：同款
   + `_c2_skip_until = 别名索引+1`（va7 缝合点；pre_unpack_info 形态已在上方整条
   消费不受影响）。

## 验证（全实测）

- 复现矩阵 **15/15 重编译全 code object 逐字段 BYTE-EQUAL**：mt1-mt5（单条/空列表/
  连续两条/属性 RHS/嵌套函数）+ va1-va10（attr 目标/3 目标混合/嵌套下标/双名尾/
  调用值/循环体 if 守卫/模块级/if 臂内/attr+下标混合链）。
- REAL46-004（enum.cpython-311.pyc）：**LOAD 链全闭合**——产品完整执行，
  FlagBoundary 四成员（STRICT/CONFORM/EJECT/KEEP）、IntFlag、EnumMeta 全部就位；
  权威 semantic_diff **DIFFERENT 60 维 → DIFFERENT 2 维**（R0-R6 全过、55 R5
  module_values 全等；剩 2 R7 = `_is_private` co_consts 8→6——v98 时代 LOAD 阻塞
  下 R7 不可提取，现暴露的既有叶差家族，与 StrEnum.__new__/_proto_member.__set_name__/
  EnumType._convert_.<dictcomp> removed 同为下轮登记族）。
- 叶级函数差异维持 4（v98 同集：dictcomp removed + StrEnum.__new__/_is_private/
  _proto_member.__set_name__ changed）——本轮修复在叶级无新增差异、LOAD 闭合在
  verdict 之下把 R7 残差从被 LOAD 屏蔽变为显式可见。
- 回归电池 23 案（r99_regress.py 文件交换 A/B：v5r98 HEAD vs v99 同输入 pyc 反编译
  产物逐字节比对）**23/23 TEXT-SAME**（fn_find_new/te1/mk_iterencode/yp1-8/er1-er4+
  er_variants/fe1/fe_variants/s3/te_shapes/te_variants8/w28/fdt 全部零变化；w2/w3
  重编译差为 v97 既有同态）。
- pytest 7 套件 2 failed（TestDominanceFrontierIf::test_B01_simple_if_then_else_merge、
  TestBoundaryConditions::test_BOUNDARY_02_large_function 冻结对）/ 282 passed /
  2 xpassed；比较器 pyc_verify.py SHA256 FE1902A9… 冻结一致、tests/ 零改动。
- 全量 1556 闸门（3 分片 vs v5r89 基线）与 REAL46 sweep：见本轮提交说明（0 回归）。

## 诚实边界

- REAL46-004 未达 EQUAL（剩 2 R7 = `_is_private` co_consts 残差族在案）。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r99.diff` | [v99-CHAINALIAS] 完整 diff（新构建器 + 五插入 + 过滤对齐） |
| `mt1-mt5_repro.py` / `*_out_v99.py` | 五形态复现（修复后产品） |
| `va1-va10_variant.py` | 十变体矩阵 |
| `REAL46-004_product_v5r99.py` | enum 产品（LOAD 闭合状态） |
| `case_REAL46-004_v99.json` / `semantic_REAL46-004_v99.json` | 权威判定（DIFFERENT 2 维，R0-R6 全过） |
| `r99_regress.py` | 23 案回归电池驱动 |
