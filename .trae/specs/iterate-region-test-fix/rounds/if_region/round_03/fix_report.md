# Round 03 — IF 区域修复报告

**修复范围**：IF 条件中三元 / walrus / await 与链式比较、表达式包裹的组合场景
**修复轮次**：10 个确认错误（聚类1 ×7 + 聚类2 ×1 + 聚类4 ×2）
**遗留**：聚类3（嵌套三元归约根本 bug，独立问题，留待 Round 4 深入）
**回归**：359 基线 + 17/18 adv03 通过（聚类3 因根本 bug 失败，与本轮修复无关）

## 聚类1：三元被外层表达式包裹（7 个错误，已通过）

源码场景：
- `if d[a if c else b] > 0:` — 三元在下标位置
- `if (a if c else b).x > 0:` — 三元在属性访问
- `if f(a if c else b) > 0:` — 三元在函数调用参数
- `if (a if c else b) is None:` — 三元 + is None
- `if (a if c else b) in lst:` — 三元 + in 测试
- `if {(a if c else b): 1}:` — 三元作为 dict key
- `if 0 < (a if c else b) < 10:` — 三元在链式比较中段

**根因**：`_build_ternary_wrapped_expr` 中 `_extract_pre_ternary_instrs` 反向追踪 test 起点时，
未跳过末尾的条件跳转（POP_JUMP_IF_FALSE 等），导致 stack_effect=-1 立即把 depth 降到 0，
误把整个 condition_block 当作 test 表达式，丢失 trapped 容器/可调用对象。

**修复**：在反向追踪前先跳过末尾的条件跳转指令，从倒数第二条开始追踪。
新增 4 个辅助方法：
- `_extract_pre_ternary_instrs(ternary_region)` — 提取 ternary test 之前的被困指令
- `_build_simple_load(instr)` — 构建 LOAD 指令的表达式 dict
- `_sim_wrapping_instr(instr, stack)` — 栈模拟单条 wrapping 指令（LOAD_ATTR/BINARY_SUBSCR/CALL/CONTAINS_OP/IS_OP/COMPARE_OP/BINARY_OP/UNARY_*/SWAP/COPY/POP_TOP）
- `_build_ternary_wrapped_expr(ternary_expr, cond_block, ternary_region, region)` — 完整条件表达式构建

调用点：`region_ast_generator.py` line 7236-7245（`merge_context='compare'` 路径）。

## 聚类2：walrus 在下标位置 + 链式比较（1 个错误，已通过）

**测试用例**：`if 0 < d[(n := f())] < 10:`

**根因**：`_try_build_walrus_chained_compare` 反向追踪时遇到 BINARY_SUBSCR 错误停止，
把容器 `d` 当作 middle 操作数。且 post-STORE 的 BINARY_SUBSCR 从未被处理。

**修复**：在 `_try_build_walrus_chained_compare` 中新增 post-STORE wrapping 检测分支。
若 STORE 之后存在 wrapping 指令（BINARY_SUBSCR/LOAD_ATTR/CALL/BUILD_MAP/CONTAINS_OP/IS_OP），
说明 walrus 值被外层表达式包裹：
1. 前向栈模拟 COPY 之前的指令构造 `[left, trapped..., walrus_value]`
2. 把 walrus_value 包裹为 NamedExpr
3. 处理 post_wrap_instrs 把 trapped 与 NamedExpr 组装为完整 middle
4. 栈底是 left，栈顶是完整 middle

## 聚类4：await 在 IF 条件中的归约（2 个错误，已通过）

### 错误 08：`if 0 < await g() < 10:`（链式比较 + await 中段）

**根因**：`_try_build_await_condition` 仅处理简单 await + 可选单 COMPARE_OP，
不识别链式比较。`reconstruct(inner_instrs)` 返回栈顶 g()，丢失 left=0。

**修复**：在 `_try_build_await_condition` 中新增链式比较检测分支。
若 cond_block 含 SWAP+COPY 且 `region.chained_compare_ops >= 2`：
1. 前向栈模拟 inner_instrs（GET_AWAITABLE 之前的指令）
2. 栈底是 left，栈顶是 await 内层表达式
3. 包装为 Await，构建 `Compare(left, ops, [await, ...tail])`

### 错误 11：`if (n := await g()) > 0:`（walrus + await 误识为 match）

**根因**：
1. `_is_simple_match_case_block` 缺少 walrus 排除（COPY+STORE_FAST 被误判为 match case）
2. `_try_build_await_condition` 不识别 cond_block 开头的 COPY+STORE walrus 模式
3. `CodeGenerator._generate_annotation_from_dict` 中 NamedExpr 分支用 `_generate_annotation_from_dict` 处理 value，
   不支持 Await 类型，导致 dict 直接 str() 输出

**修复**：
1. 在 `_is_simple_match_case_block` 中加入 walrus 排除（与 `_is_match_subject_block` 一致）
2. 在 `_try_build_await_condition` 中检测 COPY+STORE walrus 模式，把 await_expr 包装为 NamedExpr
3. 在 `CodeGenerator._generate_annotation_from_dict` 的 NamedExpr 分支改用 `_generate_expression` 处理 value

## 修改文件清单

| 文件 | 修改行数 | 内容 |
| --- | --- | --- |
| `core/cfg/region_ast_generator.py` | 新增 ~270 行 | 聚类1（4 个辅助方法 + 调用点）、聚类2（post-STORE wrapping 分支）、聚类4（walrus 包装 + 链式比较分支） |
| `core/cfg/region_analyzer.py` | 新增 ~10 行 | 聚类4（`_is_simple_match_case_block` walrus 排除） |
| `core/cfg/code_generator.py` | 修改 ~5 行 | 聚类4（NamedExpr 分支改用 `_generate_expression`） |

## 遗留问题（Round 4 处理）

### 聚类3：嵌套三元在链式比较中段（`if 0 < (a if (b if c else d) else e) < 10:`）

**症状**：反编译为 `if True: pass`，整个 IF 区域归约失败。
**根因**：嵌套三元 `a if (b if c else d) else e` 本身归约坏（独立 bug，
非链式比较问题）。简单嵌套三元 `x = a if (b if c else d) else e` 反编译为 `pass`，
简单比较 + 嵌套三元 `if (a if (b if c else d) else e) < 10:` 反编译为 `if 10:`。
RegionAnalyzer 把嵌套三元识别为多个分离 TernaryRegion，但 AST 生成时未正确嵌套。
需深入研究 region_analyzer 的 TernaryRegion 识别与归约逻辑。
