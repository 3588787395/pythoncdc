# FINDING — rr-v5r124 [v124-LOOPHEAD]：/iterfind while-1 环孤儿化修复（派发表先行补位=层级裁决后环头重挂）——环族结构闭合，尾块作用域残差与未解释交互登记

## 0. 结论速览

- /iterfind（−102 字节）while-1 体丢失大族的结构主体本轮闭合：
  **[v124-LOOPHEAD] 层级裁决后重挂 pass**（region_analyzer +69，单文件）——
  实证病形为 TryExceptRegion@494 在构造期**前向吸收环头 492**（同块双认领）
  且构造期已定父（`_build_region_hierarchy` 以 `parent is not None` 跳过再裁
  决），环从未获得子节点 → while 1 壳/环体 append/break 全丢。
  v124 后 **iterfind 源结构完全还原**（756→858 字节；`while 1:` +
  `selector.append(ops[token[0]](next, token))` + `raise SyntaxError` +
  `break` 全部归位），prepare_predicate 维持全字段 BYTE-EQUAL。
- 残差（登记）：handler 尾块作用域——`_cache[cache_key] = selector`（原版
  为 KeyError handler 末语句）产品排到 try 语句之外（本形语义等价、重编译
  字节不同 25 字节）→ 判官 REAL46-008 维持 38/39（R7=1）。
- 尾块续接实验（[v124-HANDLERTAIL]）三轮受控实验证据矛盾（严格 A/B 实证
  tail 存在即环消失，而插桩显示链从未触发=gate 全假），交互机制未明——
  完整回退，登记为下轮专案（§5）。
- 回归：电池 267 案 **TEXT-DIFF 0**（重挂仅在 iterfind 形触发，全语料零漂
  移）；pytest 7 套件 **2 failed/282 passed/2 xpassed**（与 rr-v5r123 基线
  一致）；矩阵 5 案 **ALL PASS**（1 OBSERVE 结构还原 + 4 控制零漂移）。

## 1. 根因（层级追踪实证）

- 探针（probe_hier.py/prefilter）：`_build_region_hierarchy` 进入时
  try@428/652/494 的 parent **已=150**（构造期 try-in-try 嵌套装配定父，
  get_offset_range 吸收环头块后区间罩住环体）；既有裁决对这些区域
  `if child.parent is not None: continue` 跳过。
- 层级结果：外层 try@150.children=[428,652,494,148,492]——内层双 try 成环的
  **兄弟**而非**子节点**（其 entry 494/652 ∈ 环 body_blocks），环节点排末
  且体被兄弟吞并。
- 按 r105 教训不改 `_collect_natural_loop_body`/`_is_while_true`（窄修曾
  破坏 pc6 级已闭合案）；改在**层级裁决之后**补重挂 pass。

## 2. 修复（[v124-LOOPHEAD]，只增不破，单文件 +69）

`_build_region_hierarchy` 末尾（boolop 同入口补挂之后、roots 返回之前）新
增重挂 pass——判据全同层结构事实：

- child 为 TryExceptRegion 且现父 P 为另一 TryExceptRegion（构造期吸收定父
  的病形）；存在 LoopRegion L：child.entry ∈ L.body_blocks（真实环体嵌套）、
  L.entry ≠ child.entry（非同入口 peer）、L 与 child 同宿（L.parent is P 或
  None）、L 非 child 后代（防环）、L.entry ≠ P.entry。
- 取区间最窄合格 L 重挂：child.parent=L、L.children 按入口偏移序插入、
  P.children 移除。只改层级父子关系，不动块认领/区域块集。
- C2：无合格 L 逐位不变（电池 267 案 0 TEXT-DIFF 实证）；C3：纯关系重挂。

## 3. 验证（全实测）

- **ElementPath**：iterfind 结构完全还原（756→858 字节；while 1 + append +
  raise + break 全归位）；prepare_predicate 维持 BYTE-EQUAL；全文件残差仅
  iterfind code/exctab（尾块作用域 25 字节序）；判官（--source 新鲜产物）
  **38/39 97.44%**（与 v122 持平，iterfind 唯一失败单位）。
- **A/B 电池 267 案**（r124_regress.py，单文件 ANA 交换 HEAD 7474b0e6 vs
  v124）：**TEXT-DIFF 0/267**；R110 168/169 一致（唯一差 mc1 正常归一）；
  登记差 10 案 ALL SAME-SIGNATURE（含 pe8 while-1 域——零漂移）；NO-SRC 0。
- **pytest 7 套件**：2 failed / 282 passed / 2 xpassed（与 rr-v5r123 基线
  逐项一致，余 2 失败=既有冻结对）。
- **变体矩阵 5 案**（matrix_v5r124.py，A/B 单文件交换）：E1（iterfind 同构
  精确形）HEAD TEXT-DIFF→v124 结构完全还原=OBSERVE-PASS（残差同 §0）；
  C1 while1+循环顶 try（v119 形）/C2 try-in-try 无环/C3 环体 try+break/
  C4 嵌套 while-try 全部零漂移 BYTE-EQUAL。**MATRIX: ALL PASS**。
- **REAL46 sweep 46 案 A/B**（v124 与 HEAD 双侧新鲜产物 --source）：
  见 §6 提交读数（预期仅 008 案读数变化、其余 45 案逐字节一致）。

## 4. 验收口径

大改动级（动核心层级装配）按指令执行全额闸门（267 案电池+pytest+sweep A/B
+矩阵）。不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍 NOT PASS。

## 5. 剩余登记（下一轮候选）

1. **handler 尾块作用域残差**（iterfind/E1 的 25 字节：handler 末语句在产
   品排 try 外）：[v124-HANDLERTAIL] 续接实验三轮受控实验证据矛盾——严格
   A/B（单变量 tail ON/OFF）实证 tail 存在即环消失；插桩（链触发写文件日
   志）显示链从未触发（gate 全假）；净态复现稳定。交互机制未明，需专案
   （怀疑 successor 属性惰性求值/装配期次序副作用），修复面=handler 末语
   句作用域归位（判官 REAL46-008 39/39 的最后一里）。
2. v118 E2 残余（while 底部 store-recheck）同域；E6 相邻 NOP 对；
   46 sweep 其余 DIFFERENT（REAL46-011~016）/4 compile_error。

## 6. 证据文件

`fix_patch_v5r124.diff`（+69 单文件）、`matrix_v5r124.py`+result、
`r124_regress.py`+result、`probe_iterfind.py`/`probe_hier.py`（层级探针，
r123 目录同源）、本文件；探针中间件 D:/temp/opencode/cl_layout/r124diag、
r124matrix、r124regress（sweep 双侧 log 与 result）不入库。
