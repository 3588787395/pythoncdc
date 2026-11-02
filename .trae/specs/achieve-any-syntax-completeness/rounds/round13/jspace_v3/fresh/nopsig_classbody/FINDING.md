# NOPSIG：类体多行 def 签名参数行 NOP 占位常量污染修复（rr-v5r107，Task 33，REAL46-018 闭合）

## 家族选定与根因

rr-v5r106 剩余登记：pe8（需派发表先行）、na5（while 重构域）、46 sweep 14
DIFFERENT。本轮盘点 14 案面：REAL46-018 与 REAL46-036 各仅 1 个 R7 维——选
**REAL46-018（argparse.cpython-311，stdlib，单 R7 维）**（工作流与 REAL46-004
enum 轮同构）。

根因（字段级 code object 比对 + semantic_diff 差异路径 + 常量表结构比对 +
noptest 编译探针）：

①**疾病定位**：字段级比对全文件仅 `<module>.Action : co_code,co_consts` 一个
真实差异（其余类级 co_consts 为嵌套 code repr 噪声）；semantic_diff 差异路径
`$.metadata.code.co_consts.v[31].code_sha`（v[31] = Action 类 code）。
co_code 逐字节比对：仅 byte59 一字节（02→03）——**co_consts 里 None 与
False 的驻留顺序翻转**（原件 [name,doc,None@2,False@3,...]，产品
[name,doc,False@2,None@3,...]），Action 体隐式 return None 的 LOAD_CONST
oparg 随之偏移。

②**疾病机制**：argparse.py 的 `Action.__init__` 签名跨 11 行（841-851），
8 个含位置默认值的参数行。CPython 3.11 编译器对**类体内多行 def 签名的每
个含位置默认值的续行**在宿主（类体）作用域发射一条行标记 NOP（noptest 实测
规则：模块级不发、无默认值不发、kwonly 默认不发、多个默认值同一续行只发
1 条）。原件 Action 类体含 8 条参数行 NOP（@14-28，行 844-851），NOP 区间
**零常量驻留**；随后 def 编译按默认值序驻留 None@2（nargs=None 首默认）、
False@3（required=False）。反编译器把该 NOP 游程交给折叠行头游程解析
（`_emit_folded_nop_run_units`），残留常量队列 `_unfolded_head_consts`
（co_consts 中无指令引用的数值常量）命中 False@3（False 只存在于默认值元组
内、无直接 LOAD_CONST 引用）→ 8 个占位全部发射 `While(False): pass`——
重编译在占位处**提前驻留 False**（idx2），与原件驻留序错位。

③**nd4 形态（单 NOP 参数行）**：1 个默认值续行的类体 async def（行号判别前）
被孤立常量语句分支（[Round 33]）抢先——NOP 前后皆语句边界命中
`_rag_is_orphan_nop_statement` → `Expr(Constant(''))` 占位渲染 `""`——
落在类体首语句位重编译成为 `__doc__`（空串驻留 + 文档字符串机制），双重
扰动（预存在疾病，nd4 复现）。

## 修复（region_ast_generator 只增不破，[v107-NOPSIG]，+74 行）

`_generate_block_statements_body` 的 SKIP_OPS NOP 链**头部**（claimed 检查
之后、孤立常量语句分支之前）插入新先行判据分支：

- **识别**（`_is_def_prologue_nop_run` 四重守卫，全同层结构事实）：①instr
  为 NOP 且语句边界（stmt_instrs 空）；②自 instr 起连续 NOP 游程 K≥1；
  ③游程后 1-3 条指令内出现 MAKE_FUNCTION、其间仅 LOAD_CONST（def 前奏
  [LOAD_CONST defaults][LOAD_CONST <code>] MAKE_FUNCTION）；④游程内全部
  NOP 的 starts_line 均 **大于** 该 def 嵌套 code 的 co_firstlineno（参数
  行 NOP 位于 def 行之后——def 前的常量表达式语句 NOP 行号小于 def 首行，
  由此与 [Round 33] 形态无损区分，互不劫持）。
- **归约**：每个参数行 NOP 发射裸 pass 占位（`_folded_statement_placeholder`
  ——[x01-V5R03] 实测任意语句位置恰编译 1 NOP、**零常量**、零跳转）。
  重编译还原 K 条 NOP 且零常量污染；随后的 def 编译按默认值序自然驻留
  None/False——co_consts 表序与原件逐位一致，co_code LOAD_CONST oparg 归位。
- **修复过程实证**：首版走「多行签名渲染」路线（NOP 游程+def 前奏登记
  hint → FunctionDef 渲染端逐默认值续行）——生成器实例碎片化（类体语句
  游走实例 ≠ def 装配实例）致 hint 永不挂载，且引入 defaults 丢失回归
  （argparse Action 8 默认值渲染为 6）——整体回退，改取裸 pass 占位路线
  （改动 +74 行、单文件、无实例状态）。
- **C3**：判据仅 NOP 游程+def 前奏+行号判别形态命中；def 前常量语句 NOP
  （行号 < def 首行）与无 def 前奏 NOP 回落既有分支逐位不变。

## 验证（全实测）

- **REAL46-018（argparse.cpython-311.pyc）**：semantic_diff 单案复跑
  **EQUAL**（此前 DIFFERENT/R7；`sd_argparse2.py` 判据：status EQUAL、
  diffs=[]）；字段级真实差异集 `Action: co_code,co_consts` 清空（仅剩类级
  co_consts 嵌套 repr 噪声与 firstlineno）。
- 变体矩阵 **10/10**：功效案 nd1（3 默认值 3 续行）/nd2（5 默认值含
  真值常量）/nd3（双多行 def 同类体）/nd4（async def 单默认值续行——
  v106 下 `""` 占位成 __doc__，v107 修复）——v106 TEXT-DIFF→v107 重编译
  全 code object 逐字段 BYTE-EQUAL；控制案 nd5（模块级多行 def，零
  NOP）/nd6（无默认值+单行 def）/nd7（同续行双默认值=1 NOP 分组形）/
  nd8（模块级 async）/nd9（def 前常量语句 NOP——Round-33 既有路径）/
  nd10（注解+默认值）零变化——C3。
- 回归电池 **130 案**（r107_regress.py 双文件交换 A/B：v5r106 HEAD=3384e441
  vs v107）**4 功效案（nd1-nd4）TEXT-DIFF/BYTE-EQUAL + 126 TEXT-SAME**
  （23 原案含 w28 w2/w3 v97 既有同态 + 全部控制案）；既有登记差维持与
  v104 逐字节同签名（w28 w2/w3、na5、pe8、pe8_target）。
- pytest 7 套件 **冻结对一致 2 failed**（TestDominanceFrontierIf::test_B01
  _simple_if_then_else_merge、TestBoundaryConditions::test_BOUNDARY_02
  _large_function）/ 277 passed / 2 xpassed；第 3 failed = product_freshness
  在位产物预存在陈旧（A/B 复核：v107 产物 == v104 产物逐字节，含
  trade_info_utils——fresh_ab 首轮对该文件的 != 为 A/B 换文件时
  `__pycache__` 缓存伪影，反编译器确定性复验 cur==v104 成立）；比较器
  pyc_verify.py SHA256 FE1902A9 冻结一致、tests/ 零改动。
- REAL46-004（enum.cpython-311.pyc sha 60e3ca30）单案权威 semantic_diff
  复跑 **EQUAL**（verdicts={'EQUAL': 1}）。
- 全量 1556 闸门（v5r107 三分片对 v5r89 基线）**0 回归**：EQUAL 1180=1180、
  ERROR 376=376，对 v106 **1556 案 c4 verdict 逐案零变化**（连续第七轮零
  抖动，上轮抖动案 JS-WHILE-045 本轮稳定于基线值 ERROR）；分片汇总 shard0
  367/152、shard1 406/113、shard2 407/111（与基线逐分片一致）。
- REAL46 sweep（v5r107 对 v5r106）**唯一变化 REAL46-018 DIFFERENT→EQUAL
  （本轮修复功效，46 sweep 首个经裸 pass 占位路线达 EQUAL 的 R7 阻塞案，
  sweep 读数 DIFFERENT 14→13 / EQUAL 14→15）**：其余 44 案 c4 逐案零变化
  0 回归（13 DIFFERENT/15 EQUAL/17 ERROR+skip1，c2_pyc_missing=已登记
  REAL46-045）；REAL46-004 维持 EQUAL。

## 诚实边界

- REAL46-018 闭合（46 sweep DIFFERENT 14→13 预期，以 sweep 实测为准）。
- pe8（while-1 重构族，需派发表先行）、na5（while 条件嵌套 or 尾，loop
  重构域）维持登记；46 sweep 其余 DIFFERENT/ERROR 在案。
- 不宣称 G2c 通过；`product_complete` 仍 **NOT PASS**。

## 证据（本目录）

| 文件 | 作用 |
|---|---|
| `fix_patch_v5r107.diff` | [v107-NOPSIG] 完整 diff（+74 行） |
| `nd1-nd4.py` | 功效案（类体多行 def 参数行 NOP 形态） |
| `nd5-nd10.py` | 控制案（模块级/无默认值/分组/async/常量语句/注解） |
| `argparse_prod_v107.py` | argparse 产品（判官 EQUAL） |
| `sd_argparse2.py` | REAL46-018 单案判官驱动 |
| `r107_regress.py`/`r107_regress_result.txt` | 130 案回归电池驱动与结果 |
| `semantic_REAL46-004_v107.json`（+report） | enum 案权威判定（EQUAL） |
