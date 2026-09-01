# Round 33 修复报告：`if A or B:` 短路链翻转 + PtradeAccount 类体常量语句 NOP 保留

日期：2026-08-30　修复人：修复工程师　基线：ok=309 / partial=93，funcs=4857/5149（Round 32）

## 1. 根因（已亲自实测验证）

### 1.1 `stock_order_response_transform`：or 短路链被识别为 and 链，结构翻转

- 现象：`ptradeAccount.pyc::stock_order_response_transform` 源码
  `if A or B: X elif C: Y` 被解构成 `if not A: [if B: X elif C: Y]`，
  A 为 true 时 X 丢失（语义错误，非纯字节码差异）。
- 根因：`core/cfg/region_analyzer.py::_identify_conditional_regions` 的
  `_main_inline_boolop_chain` 只识别 and 链（各段 `POP_JUMP_FORWARD_IF_FALSE`
  跳同一 merge 目标）。or 链的形态不同：首段 `POP_JUMP_FORWARD_IF_TRUE`
  短路跳到 then 入口，仅末段 `POP_JUMP_FORWARD_IF_FALSE` 跳
  else/elif/merge 且 fallthrough 指向 then 入口。旧逻辑未识别该形态，
  把 or 链当单层 if 归约，产生 `not A` 包裹的翻转结构。
- 实证：CPython 3.11 对 `if A or B: X elif C: Y` 的编译形态（dis 验证）——
  or 链首段跳转方向与 and 链相反，这是区分二者的唯一可靠信号。

### 1.2 `PtradeAccount` 类体：源码常量表达式语句的 NOP 被丢弃，co_code 差 8 字节

- 现象：`PtradeAccount` 类体反编译后 co_code 471 vs 原始 467 字节（差 4 个 NOP），
  类体重编译字节码不一致，验证报 mismatch。
- 根因（CPython 3.11 编译行为，`compiler_visit_stmt_expr`，compile.c ≈L4069）：
  源码中函数定义间的**常量表达式语句**（裸字符串/数字）编译为
  **发射 NOP 且不加载进 co_consts**。反编译器把该语句整体丢弃 →
  重编译时 NOP 缺失 → co_code 不匹配。因为常量不进 co_consts，
  这类差异只有逐字节比较 co_code 才能发现。
- 判别特征（与行号标记 NOP 区分）：前一条有效指令是语句边界
  （STORE_NAME/STORE_ATTR 等），后一条是语句开始
  （LOAD_CONST <code> / LOAD_NAME property 等）；**块首/块尾 NOP
  （前后缺失）是行号标记，必须排除**——这是本轮发现并修正的关键误判
  （v1 判据曾把函数体块尾行号标记 NOP 误判为常量语句，类体渲染出现
  2 处多余 `""""""`）。
- 占位常量字符串是安全载体：`''` 同样走 Constant 分支发 NOP 且不进
  co_consts，不影响 co_consts 对比；渲染为 `""""""`（docstring 格式化
  路径）可正常编译，重编译精确还原 NOP。

### 1.3 验证锚点 `same_code` 的 co_consts 身份比较恒失败

- 现象：类体 co_code 已字节级一致（471/471）后验证仍报 mismatch。
- 根因：`same_code` 的 `o.co_consts != d.co_consts` 对含嵌套 code object
  的 consts 走**对象身份比较**——PtradeAccount 类体含 135 个方法
  code object，身份比较恒不等 → 类体永远 mismatch，锚点不可信。
- 修复：改为递归比较（非 code object 按值、code object 递归各字段）。

## 2. 改动

- `core/cfg/region_analyzer.py`（or 短路链识别）
  - `_identify_conditional_regions` 内 `_main_inline_boolop_chain`：
    补 or 链形态识别——首段 IF_TRUE 短路跳 then 入口 + 末段 IF_FALSE
    跳 else/elif/merge 且 fallthrough 指向 then 入口；
  - 修复后 `if A or B: X elif C: Y` 保持原结构，不再翻转。
- `core/cfg/region_ast_generator.py`（类体 NOP 占位，3 处）
  - 新增 `_rag_is_orphan_nop_statement`：区域归约版常量语句 NOP 判别；
    `prev is None`（块首）与 `nxt is None`（块尾）均判 False
    （行号标记，非常量语句）；
  - `_build_statements_from_instructions` 的 NOP 分支：命中孤立 NOP 语句时
    生成 `Expr(Constant(''))` 占位（`_nop_placeholder` 标记）；
  - 两处镜像的 SKIP_OPS 分支（handler/finally 体 ≈L22054 与普通块
    ≈L38989 内联循环，replace_all 同步修改）：命中
    `_rag_is_orphan_nop_statement` 时生成占位语句，否则落入既有
    `_is_orphan_boundary_nop`（行号标记 → `While(False)` 折叠）。
    **注意：类体单块走 `_generate_block_statements_body` 的 L38989
    内联循环，不经过 `_build_statements_from_instructions`**——这也是
    前期修复落错位置（ASTGeneratorV2 / `_build_statements_from_instructions`）
    未生效的原因。
- `core/cfg/ast_generator_v2.py`（双向保险，非实际路径）
  - `_generate_instructions_content`：过滤 NOP 时保留孤立 NOP
    （`_is_orphan_nop_statement` 判 True 的保留），使
    `_process_instruction_sequence` 能看到并生成占位；
  - `_is_orphan_nop_statement`：`prev is None` / `nxt is None` 均判 False
    （修正块尾行号标记 NOP 误判）。
  - `decompile_pyc(use_cfg=True)` 实际走 `use_region=True` →
    RegionASTGenerator，此文件为 `generate_ast_v2` 路径的保险。
- `.trae/.../round_32/repair_engineer/verify_ptrade_full.py`（验证锚点修正）
  - `same_code` 的 co_consts 改为递归比较（`_same_consts`：嵌套 code
    object 递归各字段，非 code object 按值），使类体/模块级验证可信。

## 2.5 回归修复（r33b，全量扫描对比 round_32 基线发现并修复）

修复后按 round_32 同口径全量扫描（full_scan_r33.py，分片并行）对比基线，
发现 **3 个文件 ok→partial 的疑似倒退**，逐一实测确认为两类真实回归并修复：

### 2.5.1 `strategy_context.__repr__`：or 链成员跳过逻辑缺「链尾 IF_FALSE 段」确认（31/31→30/31）

- 现象：`if not callable(v) and not k.startswith('_'): items.append(...)`（and 链带
  not，段块全部 `POP_JUMP_FORWARD_IF_TRUE` 跳同一循环尾）被解构成嵌套
  `if not callable(v): [if k.startswith('_'): pass else: append]`，多 1 条
  JUMP_BACKWARD，重编译不匹配。
- 根因：`_identify_conditional_regions` 的 or 链成员跳过逻辑（`_is_or_member`，
  Round 33 新增）只按「前驱 IF_TRUE + 跳转目标匹配」判定，未确认链尾存在
  IF_FALSE 段。`if not A and not B: X`（and 链带 not）与 `if A or B: continue`
  （短路 continue）字节码同为「段块全 IF_TRUE 跳同一目标」，被误判为 or 链
  成员而跳过，and 链解构失败。DBG_OR 实测：`or-chain member skip: block=96`
  后链首 58 的 or 检测正确拒绝（no false tail），但 96 已被跳过。
- 修复：跳过前沿 fallthrough 走链，确认存在 IF_FALSE 段（真 or 链）才跳过；
  链断或走完无 IF_FALSE 段则恢复普通处理（与 or 链检测的 `_or_has_false_tail`
  判据对称）。修复后 96 不再跳过，31/31 恢复。

### 2.5.2 `time_validator.can_cancel_order`：BoolOp 链检测把 or 链末段 + then 体首块拼成假 and 链（5/5→4/5）

- 现象：`if A or B: [if C: return True]` 中 `is_listing` 判断整体消失，产物变为
  `if A or B: return True`（44 指令 vs 37）。
- 根因：`_detect_boolop_conditional_chain`（先于 conditional 阶段运行）把 or 链
  末段 B（IF_FALSE 跳 else、fallthrough 指向 then 入口）与 then 体首块 C
  （IF_FALSE 跳同一 else 目标）识别为 and 链 `B and C`，创建
  `BoolOpRegion(entry=78, blocks=[78,140])` 吸收 C；主 IfRegion then=[140,202]
  生成时 140 已被 BoolOpRegion 抢占 → 生成空。诊断实测 region 树：
  `BoolOpRegion entry=78 blocks=[78, 140]` + `IfRegion entry=0 blocks=[0,78,140,202]`。
- 修复：`_detect_boolop_conditional_chain` 启动前检查链首块是否为 or 链成员
  （前驱 IF_TRUE 跳转目标 == 本块 fallthrough/then 入口），并沿 fallthrough
  走链确认链尾存在 IF_FALSE 段才返回 None（跳过 BoolOp 检测）；无 IF_FALSE
  段的 and-not / 短路 continue 形态不跳过（strategy_context 依赖同一判据，
  已实测不回退）。or 链整体由 conditional 阶段的 `_main_inline_boolop_chain`
  统一归约，BoolOp 重建在 AST 端完成，不依赖 BoolOpRegion。
- 附带：同一次扫描确认 `trade_stock_account` 的 12/13 为修复中间态残留
  （当前代码 4 个 seed 下均 13/13 ok），`time_validator`/`strategy_context`
  在 HEAD（修复前）代码下实测 5/5、31/31 全匹配，证明为真回归而非口径差异。

## 3. 验证结果（全部实测，PYTHONHASHSEED=0）

| 步骤 | 命令/方式 | 结果 |
|---|---|---|
| a. or 链目标函数 | `verify_ptrade_full.py`（修正 same_code 前） | stock_order_response_transform 匹配 |
| b. ptradeAccount 全函数 | `verify_ptrade_full.py`（co_code/consts/names/varnames 递归全等） | **total=136 matched=136 mismatched=0**（Round 32 基线 134/136） |
| b2. 递归精确对比 | `test_engineer/verify_ptrade_recursive.py`（全部嵌套 code object 的 co_code/co_names/co_varnames/co_freevars/co_cellvars/递归 consts） | 模块级一致；PtradeAccount 类体差异 0；类体内方法 匹配 135 / 不匹配 0 |
| c. 类体占位生成 | `test_engineer/diag_region_cls.py` | 类体 4 个占位（Expr line=254/1244/1701/1728）全部生成，top-level 语句 147 → 151 |
| d. 全量回归 | `full_scan_r33.py` 分片（402 pyc，PYTHONHASHSEED=0） | **ok=311 / partial=91 / failed=0；函数级 5439/5746**；与 round_32 基线（scan_after_fix 同口径）**倒退 0、改进 2**（convert、user_info_utils）；修复前（scan_after_fix）308/94，回归 3 处全部恢复（见 scan_after_fix2.json） |
| d1. 补丁合规 | `scripts/check_patch_patterns.py` | PASS（region_analyzer.py / region_ast_generator.py 均 OK） |
| d2. opcode 计数 | `scripts/check_hardcoded_opcodes.py` | region_analyzer=694（Round 32: 694，持平，回归修复零新增）、region_ast_generator=1370（Round 32: 1363，+7）；新增均为 NOP/噪声指令判定所需指令名（NOP/RESUME/CACHE/PUSH_NULL）及 or 链回归判据所需，无危险模式 |

## 4. 已知遗留（Round 34 候选）

按成功率升序 partial 列表：IQCommon/graph（30/31）、IQCommon/util/datetime_func
（25/26）等，详见 pyc_index.json 中 partial 条目明细。

## 5. 附件

- `test_engineer/`：`diag_nop_path.py` / `diag_full_pipeline.py` /
  `diag_region_cls.py` / `diag_class_render.py`（NOP 占位链路逐层定位）、
  `verify_ptrade_recursive.py`（递归精确对比锚点）、`strict_verify_ptrade.py`
  等诊断与验证脚本；
- `repair_engineer/full_scan_r33.py` / `scan_after_fix.json`：全量回归逐文件明细。
