# STMTSPILL：值语境短路链消费端语句溢出修复（rr-v5r105，Task 31，pd8/pd10 形态闭合）

## 家族选定与根因

rr-v5r104 剩余登记选 pd8/pd10 形态（登记名为 ternary-vs-if 渲染族——实测机制
为「值语境短路链消费端吞块内/跨块用户语句」，v103 orcall 族的姊妹域；同轮
并行深查的 pe8 while-1 重构族两版窄修复均破坏 pc6 级已闭合案，按纪律放弃本
轮修复、维持登记）。

**叶 1（pd10/ta2/ta3）— ternary 条件链头块 SUBSCR/ATTR 前缀切分缺失。**
`return d['n'] if opt or d else 0` 的 ternary 注册为 TernaryRegion@0，条件
`opt or d` 是链（condition_chain_blocks=[(block0,'or'),(block66,'or')]），
链首块 0 与前序语句同块（CPython 直到首个跳转才断块）：[dictcomp 调用语句
（2-24）、`d['n'] = len(d)`（26-58，STORE_SUBSCR）、LOAD opt、PJT]。条件链
构建器 `_build_ternary_boolop_condition` 的前缀切分集 `_STORE_OPS_R2P02`
只含简单名 STORE（FAST/NAME/GLOBAL/DEREF）——切分点落在最后一个简单
STORE（STORE_FAST d@24），SUBSCR/ATTR 赋值整段留在条件操作数区，被
expr_reconstructor 栈回放静默吞掉（reconstruct 只返回栈顶 `opt`，赋值语句
蒸发）。产品只剩 dictcomp 赋值 + ternary（pd10 丢 `d['n'] = len(d)`、ta2 丢
`o.x = len(d)`、ta3 丢两条 SUBSCR 赋值）。

**叶 2（pd8/tb2/tb3/tb4）— 值语境 kwargs 双链跨块续接缺失。**
`r = wrap(payload=m or w, tag=opt or 'z')` 两条 kwargs or 链各注册为独立
BoolOpRegion：链 1 blocks=[0,144,146] merge=146、链 2 blocks=[146,150,152]
merge=152。同一调用语句被块边界切开：链 1 的 merge 块 146 = 链 2 的条件头
[LOAD opt, JITOP→152]，而 KW_NAMES/PRECALL/CALL/STORE r 在块 152。值语境
发射流：value_target 为 None（merge 块无 STORE）→ 走 `elif
has_short_circuit_op...` 分支；[B56-V3R3] RETURN 续接要求 merge 块尾
RETURN_VALUE（此处是 JITOP）不命中 → `Expr(BoolOp)` 兜底——产品坍缩为
`m or w`（裸语句 + POP_TOP），调用消失、`return r` 退化全局名读取
（tb3 更乱：`m or w / r = opt / return m`）。

## 修复（region_ast_generator 只增不破，[v105-TERNSUB] + [v105-KWCONT]，+254 行三 hunk）

**叶 1 [v105-TERNSUB]**（`_build_ternary_boolop_condition` 前缀切分，+30 行）：
切分扫描集扩展 STORE_SUBSCR/STORE_ATTR；[R36 镜像守卫]——链成员块同时是
另一 Ternary/BoolOp 区域的 merge_block 且该 SUBSCR/ATTR STORE 是块内第一条
store 时，它是上游区域的值消费 STORE（上游随其 Assign 发射），不作切分点
保持旧截断行为，避免幽灵重复发射。前缀整段交 `_build_statements_from_
instructions`（R61 同一语句重建通道，支持 Subscript/Attribute 目标）。
守卫必要性 A/B 实证：禁用守卫 → tc6（`o['x'] = 1 if opt else 2; return
o['y'] if opt or d else 0` 链路径 R36 形）DIFF（上游 STORE 幽灵重复）、
tc1（扫描循环路径 R36 形）不受影响；恢复守卫 → tc6 复绿。

**叶 2 [v105-KWCONT]**（新 helper `_v105_try_kwarg_chain_continuation` ~+190
行 + B56 分支挂点 ~+10 行）：在 B56 与 Expr(BoolOp) 兜底之间插入跨块续接
路径。六重守卫（全同层结构事实，无名字/偏移白名单）：① merge 块非噪声
不含 STORE 且以 SHORT_CIRCUIT_JUMP 收尾（下一条 kwargs 链的条件头）；
② 沿短路跳转 fall-through 成员块行走（≤8 块封顶，禁语句边界类指令、块尾
合法短路跳转豁免）；③ 完成块 STORE 前段含 KW_NAMES/PRECALL/CALL（调用
续接事实）且无禁令指令、STORE 后无第二 STORE；④ initial_stack = 链首块
前缀剥「最后 STORE 之后」残留栈（栈顶替换 boolop，B56/[v103-ORCALL] 同一
消费契约）+ **[v103-ORCALL] 镜像守卫**——链首块含完整推导式调用语句时
identify_block_prefix_instructions 只返回悬空碎片（pd8 实测 2 条
[LOAD_CONST, MAKE_FUNCTION]），GET_ITER + 语句归约入口判据命中时直取全
前缀（首版缺此镜像：tb2-tb4 绿而 pd8 不生效，插桩定位后补）；⑤ 跨块窗口
（含链 2 短路跳转）以 fold_boolop_keep_or_pop=True 重建为完整调用表达式
（[B237-V3R40] 同一开关，推导式元素窗先例）；⑥ 任一守卫失败/重建失败/
返回 None 即逐位退回既有 Expr(BoolOp) 兜底（C3）。发射 Assign(STORE 目标,
完整调用) + 行走块/完成块登记 generated/generated_offsets + merge 为 entry
的下游区域经 _downstream_region_entry 派发登记（原则 4，R64-B1/P2-1 同款）
+ 完成块 STORE 后剩余指令交 _generate_stmts_from_instrs（B76 同款
裁剪-发射-登记模式，pd8 的 `return r` 由其归约）。

## 验证（全实测）

- 复现矩阵 **20/20**：7 功效案 pd8（enum 外的 kwargs 双链精确形）/pd10/
  ta2（STORE_ATTR 前缀）/ta3（双 SUBSCR 前缀）/tb2（位置参+kwarg 链）/
  tb3（三 kwarg 链）/tb4（kwarg 链+尾随语句）——v104 DIFF→v105 重编译全
  code object 逐字段 BYTE-EQUAL；13 控制案零变化——C3：pd1-pd7/pd9
  （v103 已闭）、tc1（扫描循环 R36 形）、tc2（简单 STORE 链头）、tc4
  （无前缀纯 ternary）、tc5/pd6（单 kwarg 链，merge 即完成块、既有
  value_target 路径）、tc6（链路径 R36 形）。
- 回归电池 **113 案**（r105_regress.py 双文件交换 A/B：v5r104 HEAD vs v105
  同输入 pyc 反编译产物逐字节比对 + 逐顶层函数重编译比对）：**7 功效案
  TEXT-DIFF/BYTE-EQUAL + 106 TEXT-SAME**（23 原案含 w28 w2/w3 v97 既有
  同态 + 全部控制案）；既有登记差维持且与 v104 逐字节同签名（w28 w2/w3、
  nb2、pe8、pe8_target）。
- pytest 7 套件（test_algorithm_correctness/test_boundary_cases/
  test_complete_syntax_coverage/test_control_flow_completeness_matrix/
  test_core_functional/test_deep_nesting_pressure/test_product_freshness）
  **2 failed（冻结对：TestDominanceFrontierIf::test_B01_simple_if_then_
  else_merge、TestBoundaryConditions::test_BOUNDARY_02_large_function）/
  277 passed / 2 xpassed**；第 3 failed =
  TestProductFreshness::test_products_match_current_code——在位 site-packages
  产物预存在陈旧（A/B 实证：在位产物 ≠ v104 HEAD 产物、v105 产物 == v104
  产物逐字节，三 corpus 文件 INPLACE!=V104 且 V105==V104），非本轮引入。
- 比较器 pyc_verify.py SHA256 冻结一致、tests/ 零改动。
- REAL46-004（enum.cpython-311.pyc）单案权威 semantic_diff 复跑
  **EQUAL**（rc=0，verdicts={'EQUAL': 1}）；产品与 v104 逐字节相同（行尾
  规范化后）。
- 全量 1556 闸门（v5r105 三分片对 v5r89 基线）**0 回归**：EQUAL 1180=1180；
  对 v104 逐案 c4 verdict 唯一变化 JS-WHILE-045 ERROR→None——None=本轮 4 路
  并发下判定未产出（NO_C4），单案复跑（--offset 923 --limit 1）=ERROR
  unexecuted 与 v104 基线逐字一致，定性为已登记的并发反编译超时抖动族
  （r96 轮 7 案、r100 轮 JS-LISTCOMP-004 同族）非回归；分片汇总 shard0
  367/152、shard1 406/112+NO_C4 1、shard2 407/111。
- REAL46 sweep（v5r105 对 v5r104）**45 案 c4 逐案零变化 0 回归**：14
  DIFFERENT/14 EQUAL/17 ERROR+skip1（c2_pyc_missing=已登记 REAL46-045），
  与 v104 分布逐案相同；REAL46-004 维持 EQUAL。

## 诚实边界

- pd8/pd10 形态闭合；pe8（while-1 重构族）本轮深查后放弃修复（两版窄修复
  均破坏 pc6 级已闭合案：`_collect_natural_loop_body` 前向吸收排除破坏
  pe1/pe3/pe4；`_is_while_true` 可达性判定破坏 pc6/pe1-pe14）——诊断在案
  （自然出口块 92 + break 落点 90 被前向吸收 → `_is_while_true` 判 True →
  site9k while-1 发射；需派发表先行），维持登记。
- nb2 平铺形维持登记；46 sweep 其余 14 DIFFERENT/17 ERROR 在案。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r105.diff` | [v105-TERNSUB]+[v105-KWCONT] 完整 diff（+254 行三 hunk） |
| `pd8.py`/`pd10.py`/`ta2/ta3/tb2/tb3/tb4.py` | 复现+变体矩阵（7 功效案） |
| `tc1/tc2/tc4/tc5/tc6.py` | 控制案（R36 两路径守卫形/简单 STORE/无前缀/单 kwarg/链路径 R36） |
| `pd8_out.py`/`pd10_out.py` | v105 产品（与源码语义等价、重编译 BYTE-EQUAL） |
| `pd8.pbpyc`/`pd10.pbpyc` | 原件字节码（A/B 输入） |
| `matrix_v104_baseline.txt` | v104 基线（7 功效 DIFF + 13 控制绿） |
| `r105_regress.py`/`r105_regress_result.txt` | 113 案回归电池驱动与结果 |
| `REAL46-004_product_v105.py` | enum 产品（与 v104 逐字节相同） |
| `semantic_REAL46-004_v105.json`（+report/+log） | 权威判定（EQUAL） |
