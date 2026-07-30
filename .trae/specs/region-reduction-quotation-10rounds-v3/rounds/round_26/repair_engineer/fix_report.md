# Round 26 修复报告 — 缺陷3：one_prod_to_dataframe `and` 复合条件部分提取不一致

## 一、修复方案选择

**采用方案 B**（不拆分任何 `and` 复合条件，保持原始 `if A and B:` 形式）。

理由（依任务要求「优先方案 B，更接近 orig 字节码，风险更小」）：
- 方案 A（统一拆成嵌套 `if A: if B:`）偏离原始源码语义，且会引入额外跳转块。
- 方案 B 保持 `if A and B:` 与 `elif A and B:` 一致，字节码与 orig 完全等价。
- 实现路径：当主 `if` 条件是复合 `and` 短路条件（编译为多个连续条件块，每块
  `POP_JUMP_FORWARD_IF_FALSE` 跳同一 false 目标）时，检测该链并存入
  `IfRegion.inline_boolop_chains`，AST 生成时重建完整 `BoolOp` 条件，使主条件
  与 elif 条件的复合条件提取一致。

## 二、缺陷现象与根因

### 缺陷现象（R25 状态，严格口径 147/150）
`one_prod_to_dataframe` 中 `if` 首条 `and` 复合条件被拆成外层 `if A:` + 内层
`if B:`，而 `elif` 链保留 `elif A and B:` 形式，二者不一致：
```python
if i == 0:                          # ← 首条被拆
    if len(v) == 8:                 # ← 内层
        ...
elif i == 0 and len(v) == 10:       # ← elif 仍保留完整 and
    ...
```

### 根因
主 `if` 条件块（`condition_block`）含前置语句（如 `v = str(v)`）时，
`_detect_boolop_conditional_chain` 的 `_sb_has_body` 守卫跳过该块，不创建
`BoolOpRegion`。导致主条件仅取首块（`i == 0`），次块（`len(v) == 8`）被作为
嵌套 `IfRegion` 条件，外层 `if` 的 false 跳目标从「下一 elif」变为「循环末尾」
（多 1 条 `EXTENDED_ARG`），字节码布局不一致。

elif 链则通过 `_check_elif_chain` 的 `inline_boolop_chain` 检测正确保留完整
`A and B`，故主条件与 elif 条件提取不一致。

## 三、修复点

### 修复点 1：`region_analyzer.py` `_identify_conditional_regions` — 主条件 'and' 链检测（Step 6）
- 位置：`core/cfg/region_analyzer.py` L11591-11666
- 镜像 `_check_elif_chain` 的 `inline_boolop_chain` 检测，在主条件块上检测 `and`
  短路链：沿 `POP_JUMP_FORWARD_IF_FALSE` 同一 false 目标的连续纯条件块（无
  `STORE_*`）组成 `and` 链。
- 检测到链后：`condition_block` 重定向到链末块（真正的 then/else 分支点），
  `chain_blocks` 纳入所有链块，链信息存入 `_main_inline_boolop_chain`。
- 首块可能含前置语句（由 AST 生成时 entry pre-stmt 提取处理），故仅检查后续
  块必须为纯条件块。

### 修复点 2：`region_analyzer.py` `_identify_conditional_regions` — 安全回退（merge 计算失败）
- 位置：`core/cfg/region_analyzer.py` L11961-11990
- 当主条件 `and` 链检测重定向了 `condition_block`，但所有 merge 计算均失败
  （`merge=None`，典型场景：then-body 含 `return` 导致重定向后 `then_succ` 的
  post-dominator 为 None），撤销重定向，恢复原始 `condition_block` 重新计算 merge。
- 依原则 4：不重定向时 `condition_block`=首块，`then_succ`=次条件块（无 return，
  post-dominator 正确），merge 可正确计算。`_main_inline_boolop_chain` 清空，
  该 if 保持 R25 行为，不引入回归。

### 修复点 3：`region_analyzer.py` `_build_elif_region` / `_build_basic_if_region` — 链信息存入 IfRegion
- 位置：`core/cfg/region_analyzer.py` L13382-13388（`_build_elif_region`）、
  L12514-12520（`_build_basic_if_region`）
- 将 `main_inline_boolop_chain` 合并到 `IfRegion.inline_boolop_chains`
  （`key=id(condition_block)`），与 elif 链的 `inline_boolop_chain` 同等处理。

### 修复点 4：`region_ast_generator.py` `_if_generate_full_elif_chain` / `_if_generate_normal` — 重建复合 BoolOp 条件
- 位置：`core/cfg/region_ast_generator.py` L7715（elif 链路径）、L10453（普通 if 路径）
- 通过 `inline_boolop_chains.get(id(cond_block))` 取出主条件链，从链中各块的指令
  重建完整 `BoolOp` 条件（`{'type':'BoolOp','op':'and','values':[...]}`），并标记
  链中其余块为 `generated`（每块唯一归属）。
- 两条路径（elif 链 / 普通 if）镜像实现，保证主条件与 elif 条件一致。

### 修复点 5（本轮新增，关键）：`region_ast_generator.py` `generate()` 入口处理 — 复合 'and' 条件 IfRegion 入口识别
- 位置：`core/cfg/region_ast_generator.py` L296-324
- **此为本轮修复 load_bars_from_hundsun -195 回归的关键修复点。**
- 根因：`generate()` 入口处理中，原仅当 `entry_region.condition_block == entry_block`
  时 `pass`（让 IfRegion 处理）。'and' 链检测将 `condition_block` 重定向到链末块后，
  `condition_block != entry_block`，落入 `else` 分支：将 `entry_block` 作为基本语句
  提取（emit 前置语句）并标记 `generated`。随后 `_generate_if_region` 派发检测到
  `region.entry in generated_blocks`（L7231），无 `boolop_child`，丢弃整个 IfRegion
  （`return []`），导致 `if os.path.exists(...) and typet == 6:` 及其整个 body 丢失
  （load_bars_from_hundsun -195 指令回归）。
- 修复：新增 `elif` 分支，当 `entry_region` 是 IfRegion 且 `entry_region.entry is
  entry_block` 且 `inline_boolop_chains` 存在以 `entry_block` 为首块的链时，`pass`
  （让 IfRegion 的 `_if_generate_normal` 统一处理：提取 entry 前置语句 + 重建
  BoolOp 条件 + 生成 if + body）。
- 判据精确：elif 链的 `inline_boolop_chain` 以 elif 条件块为首块，`entry_block`
  不会匹配，故不影响 elif/普通 if 入口处理。

## 四、docstring 更新（6 项模板）

按 6 项模板（①算法依据 ②归约顺序 ③唯一归属判定 ④嵌套处理 ⑤入口引用语义
⑥反编译流程）更新涉及方法 docstring：

1. `_identify_conditional_regions`（region_analyzer.py）：
   - ②归约顺序：新增 Step 6（[R26-Defect3] 主条件 'and' 短路链检测）说明。
   - ⑤入口引用语义：新增复合 'and' 条件下 entry=首链块、condition_block 重定向到
     链末块的说明，及 generate() 入口处理识别此模式的说明。

2. `_build_elif_region`（region_analyzer.py）：
   - ⑤入口引用语义：新增 `main_inline_boolop_chain` 合并到 `inline_boolop_chains`、
     主条件与 elif 条件复合条件提取一致的说明。

3. `_build_basic_if_region`（region_analyzer.py）：
   - Args：新增 `main_inline_boolop_chain` 参数说明（依原则 2 + 原则 4）。

4. `generate()` / `_if_generate_normal` / `_if_generate_full_elif_chain`
   （region_ast_generator.py）：以 6 项模板内联注释更新（这些方法沿用既有内联
   注释风格，无方法级 docstring），覆盖 ①算法依据 ②归约顺序 ③唯一归属判定
   ④嵌套处理 ⑤入口引用语义 ⑥反编译流程。

## 五、回归验证结果

### 验证步骤 a — import check
```
IMPORT_OK
```

### 验证步骤 b — 反编译 + compile check
```
DECOMPILE_EXIT=0
COMPILE_OK
（stderr 0 行）
```

### 验证步骤 c — 严格口径（strict2_nop_check.py）
```
orig cos: 150  new cos: 150
NOP 差异函数数: 1   (<module> -59 NOP，PEP626 多行签名续行，可豁免)
EXTENDED_ARG 差异函数数: 0
exact=148/150 (98.67%) diff=2

差异函数:
  <module>: len_diff len 1082->1023 (-59)          # PEP626 NOP，可豁免
  build_future_fill_time: instr_diff len 677->677   # CPython 常量折叠 frozenset，可豁免
```
**严格口径 148/150**（R25 为 147/150，本轮提升 +1，消除 one_prod_to_dataframe 缺陷3）。
load_bars_from_hundsun 不再出现在差异列表（-195 回归已修复）。

### 验证步骤 d — 归一化口径（exact_match_stats.py）
```
[stats] total=150 matched=150 mismatched=0 missing=0 success_rate=100.00%
```
**归一化口径 150/150**（无退化）。

### 验证步骤 e — 测试矩阵
```
9 failed, 318 passed, 11 skipped
```
**318 pass / 9 fail / 11 skip**（与 R25 基线一致，9 个 fail 为既有 L3 深层嵌套用例，
非本轮引入，无退化）。

### 验证步骤 f — one_prod_to_dataframe 源码一致性
```
263:    if i == 0 and len(v) == 8:
265:    elif i == 0 and len(v) == 10:
267:    elif i == 0 and len(v) == 11:
269:    elif i == 0 and len(v) == 12:
271:    elif i == 0 and len(v) == 14:
```
全部 5 条统一为 `if i == 0 and len(v) == N:` 形式，不再混合。
load_bars_from_hundsun 恢复：
```
505:    if os.path.exists(DumploadDailyFile) and typet == 6:
```

## 六、残留不一致数

**0**。one_prod_to_dataframe 的 if/elif 复合 `and` 条件全部统一为 `if A and B:`
形式，无混合。load_bars_from_hundsun 的 `if os.path.exists(...) and typet == 6:`
恢复完整。

严格口径仅剩 2 个可豁免差异（<module> PEP626 NOP + build_future_fill_time
frozenset 常量折叠），均非复合条件提取问题。

## 七、算法 4 原则合规自检

| 原则 | 合规说明 |
|------|----------|
| ① 自底向上归约 | 'and' 链检测在 `_identify_conditional_regions` 主循环中按 start_offset 倒序处理；安全回退在 merge 计算失败时撤销重定向恢复原始 condition_block（自底向上重算 merge）。 |
| ② 每块唯一归属 | 链中所有块纳入 `chain_blocks`（防止 `_collect_branch_blocks`/`_check_elif_chain` 误吸收）；AST 生成标记链中其余块为 `generated`（`_main_ibc` 路径 L10466），不被外层重复生成。generate() 入口识别复合 'and' IfRegion 时不标记 entry 为 generated，由 `_if_generate_normal` 统一归属。 |
| ③ 嵌套即抽象节点 | 复合 `and` 条件 IfRegion 在父区域中作为单个抽象节点；嵌套 IfRegion 继承父区域的复合条件语义，主条件与 elif 条件同等处理。 |
| ④ 入口引用语义 | 父序列通过 `entry`（首链块，含前置语句）引用 IfRegion；`condition_block` 指向链末块（条件求值终态点）；AST 生成通过 `inline_boolop_chains` 重建完整 BoolOp 条件，不展开子区域所有块。 |

合规约束检查：
- 无 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀新方法 ✓
- 无硬编码深度上限 ✓
- 无跨区域启发式（'and' 链检测仅基于同一 false 跳转目标 + 纯条件块判据，单区域内）✓

## 八、修改文件清单

- `core/cfg/region_analyzer.py`：
  - `_identify_conditional_regions`：主条件 'and' 链检测（Step 6）、安全回退、
    docstring 更新。
  - `_build_elif_region` / `_build_basic_if_region`：`main_inline_boolop_chain`
    合并到 `inline_boolop_chains`、docstring 更新。
- `core/cfg/region_ast_generator.py`：
  - `generate()`：复合 'and' 条件 IfRegion 入口识别（修复点 5，关键）。
  - `_if_generate_full_elif_chain` / `_if_generate_normal`：`_main_ibc` 重建
    复合 BoolOp 条件。

## 九、未 commit / push

依任务要求，本轮不执行 `git commit` / `git push`，由主调度统一处理。
