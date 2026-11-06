# FINDING — rr-v5r125 [诊断轮]：handler 尾块作用域专案——v124-HANDLERTAIL 未解释交互全解（三类真相）+ 候选/走查两步实验闭环，尾块发射步待定序专案

## 0. 结论速览

- v124-HANDLERTAIL「tail 存在即环消失 vs 链日志从未触发」矛盾**全解**——
  三类独立真相叠加，历轮实验证据全部对号入座；零源码改动收口（工作树
  core/* 与 HEAD 0c6308fc 逐字节一致）。
- 尾块归位的**设计两步已实验闭环**（候选搜索+链走查），第三步（发射）受
  新发现的管线 id 布局敏感性阻遏，登记定序专案。

## 1. 真相一：`successors` 是 set——v124-HANDLERTAIL carnage 的真实机制

`BasicBlock.successors: Set['BasicBlock']`（basic_block.py:66）。v124 尾
hunk 的 `_v125_cur = _v125_tl.successors[0]` 对 set 下标 → **TypeError:
'set' object is not subscriptable**，且该行在 walk 的 try 块之外 → 异常传播
→ handler 装配中止 → try 语句整体蒸发（环作为 handler 子节点连带丢失）。
- try@494（tl=608, nsucc=1）等 4 个门真 handler 全部死于此行（净态步进插
  桩：GATE-IN 有、WALK-BEGIN 无、夹缝仅 `successors[0]` 一行）。
- v124-A 态 carnage 与「严格 A/B 单变量翻转」全部由此解释——**与链过宽无
  关**（v124 §50.5 的过宽假说作废）。

## 2. 真相二：历轮「instrumented」实验全部无效（插桩自伤链）

1. `print(file=_v124_sys)` 绑的是 **sys 模块而非 stderr** → print 必抛
   TypeError → except 内再抛 → 装配中止（ carnage + 零日志）。
2. shell 内嵌 python -c 的 `\\n` 被引号层解释为**真实换行**，打断字符串
   字面量 → region_ast_generator.py **SyntaxError** → pycdc.py **静默回退
   降级反编译器**——C/D 态的「环消失+语句跨函数串线」全部是回退产物，与
   hunk 逻辑无关（教训：**源码编辑一律走 Edit 工具或脚本文件**，已照办）。
3. 「_generate_try 从未被调用」亦为假象：入口探针插在 SyntaxError 文件上
   （回退态）。净态 Edit 工具插桩后 _generate_try 正常调用（8 次/模块，
   try@150/428/494/652 全达）。

## 3. 真相三（新发现）：管线 id 布局敏感性（预存在卫生隐患）

净态有效实验中：r9（walk 重排后）链触发 `chain ok=True [752]` ✓；r10b
（仅加 emit 捕获插桩、执行路径零变化）**hunk 整体未达**（连无条件 R7 日志
都没有）——同文件两次运行结果翻转。机制：对象 id 分配随无关源码改动漂移
→ id 散列的 set 迭代序（分析器/装配器多处 `for s in block.successors` 等）
变化 → 装配结果翻转。管线上游存在 id 序依赖（预存在），本族恰在刀锋上。
**任何源码编辑都可能经 id 布局漂移翻转输出**——电池/扫描既往稳定说明多数
路径序不敏感，但 iterfind 形在刀锋。登记为独立卫生专案（定序化：管线边界
处集合迭代一律排序消费）。

## 4. 设计两步实验闭环（净态 Edit 工具插桩实测）

1. **候选链首搜索（前驱子树判别式）——外科手术级精准**：未被实义区域认领
   的块 ∧ 全部条件前驱区域 ∈ region 严格子树。全模块 11 个 try 中**仅
   try@150 产出候选 [752]**（elem_v125_cands_surgical.py 同步存档）；其余
   10 个（含最易偷链的 try@652——其 handler 出口 742 直落 752，但 742 ∈
   自块=非严格后代）全部 cands=[]。判别式天然排除：handler 直落尾（前驱=
   自身）、他域回流、普通 try/except 的 try 后语句。
2. **链走查（POP_EXCEPT 终结先于 generated 检查）**：`cand@752 chain
   ok=True [752]` ✓——752（赋值）→ 772（含 POP_EXCEPT，已被预标记
   generated，作终结证明不重标记）。
3. **第三步（发射）待专案**：发射步异常未捕获（r9 产物 try 体蒸发=中止
   signature），且 id 敏感性使插桩不稳定。修复面=先定序专案（真相三），
   再发射步（`_generate_handler_body_statements(752)` 异常捕获+归位）。

## 5. 验收口径

诊断登记轮：**零源码改动**（工作树 core/* = HEAD 0c6308fc 逐字节一致；
净态复核 iterfind while1=1/append=1、prepare while1=1）。判官 REAL46-008
维持 38/39（R7=1）。不宣称 G1/G2c/G3/G4/G6 通过；product_complete 仍
NOT PASS。

## 6. 剩余登记（下一轮候选）

1. **管线定序专案**（真相三）：集合迭代排序消费（卫生级，独立轮）——
   id 布局敏感性的根治；亦是尾块发射步的前置。
2. **尾块发射步**（§4.3）：定序后实施发射+异常捕获，判官 REAL46-008
   39/39 最后一里。
3. v118 E2 残余（while 底部 store-recheck）同域；E6 相邻 NOP 对；
   46 sweep 其余 DIFFERENT（REAL46-011~016）/4 compile_error。

## 7. 证据文件

`elem_v125_cands_surgical.py`（候选精准性产物快照）、`v125_real.log`（净态
步进插桩日志：GATE-IN/WALK-BEGIN/chain 行）、本文件；插桩中间件
D:/temp/opencode/cl_layout/r125diag/（edit_*.py 编辑脚本、各轮产物）不入库。
