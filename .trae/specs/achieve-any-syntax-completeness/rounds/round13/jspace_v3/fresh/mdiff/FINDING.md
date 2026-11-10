# rr-v5r152 [v152-HANDLERRET/ORCLAIM/LATCH/DUALUNPACK2] difflib 判官全闭合 59/62→62/62（MDIFF 域）

## 概述

difflib 余 3 判官单元（_mdiff / _mdiff._line_pair_iterator / HtmlDiff._line_wrapper）
一轮四修复（3 文件域 2 文件）全部闭合：**62/62 = 100.00%**（difflib_judge_v152e/g.txt）。
四个真实 R1、四个独立根因，各自复现→只增修复→字节验证：

| # | 标记 | 文件 | 实形 | 缺陷 |
|---|------|------|------|------|
| A | v152-HANDLERRET | region_ast_generator.py | `except StopIteration: return`（_line_pair_iterator） | handler 臂裸 return None 在 try+loop 上下文被误转 Break → 生成器不终止继续迭代 |
| B | v152-ORCLAIM | region_analyzer.py | `while (len(fromlines)==0 or len(tolines)==0):` | or 条件第二成员被外层 while-True 循环体收走 → 前向走查截断成单成员链 → 条件第二成员丢失 |
| C | v152-LATCH | region_analyzer.py | `while fromlist or tolist:` 体内 `if tolist: ... else: ...`（_line_wrapper） | 闩锁腿判据（loads⊆条件变量+无STORE+条件跳转）无法区分再测试腿与体内同变量 if 语句 → `if tolist:` 测试块被吸进条件 BoolOpRegion → if/else 坍塌 |
| E | v152-DUALUNPACK2 | region_ast_generator.py | `(fromline,fromtext),(toline,totext)=fromdata,todata`（_line_wrapper） | while 前缀提取器 UNPACK 状态机：首解包值=栈顶、残栈元素（次解包值源）被丢弃 → 第二目标对整体丢失、名字落 LOAD_GLOBAL |

## 根因与修复（只增不破）

### A. v152-HANDLERRET（generator +6/−0）

`_generate_handler_body_statements` 的 RETURN_VALUE 分支把「仅 LOAD_CONST None +
RETURN_VALUE」的块在 try+loop 上下文转成 `break`（旧 return-hoisting 惯用法）；
守卫 `_is_except_block` 只查 EXCEPT_STORE/EXCEPT_HANDLER 角色——handler 臂块的
角色被循环体标注粗化为 LOOP_BODY，守卫够不着。修复：结构事实补充——块归属
TryExceptRegion（`block_to_region` 成员）即豁免 Break/Continue 转换，落回下方正常
Return 重建（与 R3-B115 设计意图一致：handler 臂 return 显式重建）。

### B. v152-ORCLAIM（analyzer +30/−0）

`_detect_while_boolop_forward_chain` 走查在 fall-through 后继被其它区域认领时经
`interrupts_boolop_forward_chain` 截断。mdiff3 形：内层 collect-while（header=92、
cond=16）的 or 链 [16, 54]，54 被外层 while-True 循环体收集收走（B11 结构：认领者
blocks 含纳本循环 header）→ 截断成 [(16,'or')] 单成员链 → v143 闭合判据整体失败 →
条件第二成员丢失（渲染 `while len(fromlines)==0:`，tolines 永不复查=真实 R1）。
修复：认领者豁免——claimant 是 LoopRegion ∧ 其 blocks 含本循环 header ∧ 该块带
or 成员签名（假边跳转目标 ∉ 本循环体语义集 + 落空==本循环 header）→ 继续走查；
折叠合法性仍由 v143 闭合判据①-④整体承担（不满足逐位落回 None）。

### C. v152-LATCH（analyzer +31/−0）

`_r2164_purge_latch_legs`（R21-64 再测试腿清除）的 is_leg 判据（无 STORE + 条件
跳转 + loads ⊆ 条件变量集）对 `while fromlist or tolist:` 体内的 `if tolist:`
测试块同样命中（loads={tolist}⊆{fromlist,tolist}）→ 该块被吸进条件 BoolOpRegion
→ IfRegion 无法形成 → 两个 if/else 坍塌成 `todata = tolist.pop(0)` + `todata =
('', ' ')` 顺序语句（真实 R1：pop 结果被无条件覆盖）。修复：闩锁腿目标精化——腿
的条件跳转目标必须到达循环再入点（header）或循环出口（条件链 merge），直接命中
或经腿形续块（无 STORE、条件跳转，混合链闩锁成员前向跳下一闩锁腿）有界（6 步）
走查到达；体内 if 臂块带 STORE、走查失败 ⇒ 不再被吸。mdiff3 再测试链 [268,306]
（目标 92=header）维持清除。

### E. v152-DUALUNPACK2（generator +108/−0）

`_loop_generate_while` 前缀提取器 UNPACK 状态机：首解包值=reconstruct 栈顶（SWAP
后 TOS），残栈元素是紧随 UNPACK 的值源——既有路径丢弃残栈，第二 UNPACK 见空缓冲
→ value=None → 目标对静默丢弃（toline/totext 落 LOAD_GLOBAL=真实 R1）。修复：
①有值缓冲时 reconstruct 后捕获残栈（非 PUSH_NULL 元素、TOS 在前）为 pending 队
列；紧随的空缓冲 UNPACK 从队列取值。②首解包完成后随指令直接是 UNPACK_* 时持存
(target, value)，链解包值来自残栈时合并发射单条 Assign(targets=[Tuple([首对,链
对])], value=Tuple([首值,链值]))——重编译经同一 SWAP+多 UNPACK 形再生（字节等价）。
独立连续解包（各自值缓冲）与任何不匹配逐位落回既有逐解包发射。

（同族缺口另存三处状态机（_loop_extract_self_loop_stmts/_entry_unpack_info/
_unpack_info/_nbi_unpack_info）与 _build_effective_stmts 的 _fu_ 路径——E3 合成案
实证预存在（HEAD==v152 同缺陷形），登记 RESIDUNPACK 专项轮（Task 79）。本轮修复
D（_fu_ 路径同法补丁）因无实证功效已回退。）

## 验收

- 复现案判官：mdiff3.pyc Equal/Equal、lw.pyc Equal/Equal（字节等价）
- 真实 difflib 判官：**62/62 = 100.00%**（59/62→61/62 修复 B/A → 61/62 修复 C
  控制流对齐 → 62/62 修复 E 字节对齐；difflib_judge_v151c.txt=59/62 基线、
  difflib_judge_v152.txt=61/62（B/A 后）、difflib_judge_v152c.txt=61/62（C 后）、
  difflib_judge_v152e.txt/v152g.txt=62/62 终态）
- 矩阵 15 案 ALL PASS（E1 mdiff3/E2 latch_if HEAD-TEXT-DIFF→v152 JUDGE-EQUAL；
  E3 dual_unpack SAME 预存在 DIFF=RESIDUNPACK 登记案；C1-C12 回归防护全 SAME：
  独立连续解包/单解包/v150 fancy 尾/na5/v149 gcm/B116 预存在 DIFF 维持/v151
  outer yield/裸 handler return/handler break/真共享头/async/and 链）
- 电池 326 案（R110 169 + V111..V152 累计 + V152 15）——r152_regress_result.txt
- pytest 2F/277P/2XP 冻结基线
- REAL46 全量 sweep 小修口径豁免

## 文件

- matrix_v5r152.py / matrix_v5r152_result.txt（r152matrix）
- r152_regress.py / r152_regress_result.txt
- difflib_judge_v152*.txt（B/A 后 61/62、C 后 61/62、E 后 62/62 终态）
- fix152.py（A+B）/ fix152c.py（C）/ fix152e.py（E）/ derive152.py
- fix_patch_v5r152.diff
- 复现存档：r147diag/mdiff3_src.py + mdiff3.pyc、r147diag/lw_src.py + lw.pyc
