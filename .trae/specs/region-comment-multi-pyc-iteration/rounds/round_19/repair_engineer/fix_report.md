# R19 修复报告 — WithRegion if-drop Defect 3（post-with if/return 守卫丢失）

## 1. 修复概述

| 字段 | 值 |
|---|---|
| 轮次 | R19 (rcm-r19) |
| 目标 pyc | `IQCommon/strategy/strategy.pyc`（Defect 3）+ `IQCommon/strategy/const.pyc`（轮询） |
| 缺陷模式 | WithRegion.cleanup_blocks 误消费 with 语句之后的 if 守卫块（POP_JUMP_* 结尾的兄弟 IfRegion 条件块） |
| 修复文件 | `core/cfg/region_analyzer.py`（`_collect_normal_exit_cleanup` 结构守卫 + 归属守卫）+ `core/cfg/region_ast_generator.py`（`_generate_with` docstring） |
| 修复方法 | 在 `_collect_normal_exit_cleanup` 增加 POP_JUMP_* 结构守卫（命中即 `break` 终止清理扫描）+ block_to_region 归属守卫（非 WithRegion 占用即 `continue`） |
| 修复前 strategy.pyc | failed 0.00%（0/2，trade_strategy_add 61 true_diffs） |
| 修复后 strategy.pyc | **partial 50.00%**（1/2，trade_strategy_add 100% matched，<module> Pattern R2 不可修复） |
| const.pyc | pending → **ok 100%**（1/1，首次验证即 100%，无需修复） |
| 修复前 repro | `with ...: ...; if b is not None: x=...` → 守卫丢失，body 变孤儿无条件语句 |
| 修复后 repro | **6 DEFECT-REPRO + 5 CTRL 全部 NO-DEFECT**（11/11） |
| 回归测试 | import 编译通过；R18 repros 11/11 NO-DEFECT 不变（零回归） |

## 2. 缺陷定位

**函数**: `trade_strategy_add`（strategy.pyc）+ 最小复现 `repro_01_with_then_if_guard.py`

**字节码模式**（post-with if 守卫）：
```
...                           # with body
80  LOAD_CONST None ×3        # __exit__(None,None,None) 正常出口清理
    PRECALL 2; CALL 2; POP_TOP
    JUMP_FORWARD to 126
104 PUSH_EXC_INFO             # WITH_EXCEPT_START 异常 handler（被 exception BFS 收集）
    WITH_EXCEPT_START; POP_JUMP_IF_TRUE 118; RERAISE; ...
126 LOAD_FAST b               # ← if b is not None: 守卫（被误纳入 cleanup_blocks）
    POP_JUMP_FORWARD_IF_NONE 140
130 LOAD_CONST 'a_'; ...; STORE_FAST x   # if body（has_user_code=True，未被收集）
140 LOAD_FAST x; RETURN_VALUE
```

**根因**：`region_analyzer._collect_normal_exit_cleanup`（由 `_collect_with_cleanup_blocks` → `_build_single_with_region` → `_identify_with_regions` 调用）扫描 `start_offset >= body_end` 的块收集 normal-exit 清理块。其 `has_user_code` 检查的白名单仅含 STORE_*/CALL/BINARY_OP/COMPARE_OP 等，**不识别条件跳转指令 POP_JUMP_***。故 if 守卫块（`LOAD_FAST b; POP_JUMP_FORWARD_IF_NONE`）`has_user_code=False`、last 非 RETURN，被当线性清理块 `cleanup.append(block)`。

由于区域识别优先级 TRY>LOOP>WITH>...>IF，WITH 先于 IF 识别，block_to_region 中守卫块尚未被 IfRegion 占用，旧版无归属守卫可拦截。守卫块被 WithRegion 拥有后，`_generate_with` 将其标记为 `generated_blocks`，IfRegion 无法接管 → 守卫丢失，body 作为孤儿无条件语句残留。

**对照**：R07 Pattern T fix 在 `_generate_with` 加了 block_to_region 归属守卫（`_foreign_owned`），但那是在生成阶段排除已被其他区域占用的块；Defect 3 发生在**识别阶段**（`_collect_normal_exit_cleanup`），守卫块在 IfRegion 识别前就被 WithRegion 吞并，R07 守卫无法覆盖。

## 3. 修复方案

在 `core/cfg/region_analyzer.py:_collect_normal_exit_cleanup` 的 `has_user_code` 检查之后、`RETURN_VALUE` 检查之前，插入两道守卫：

```python
last = block.get_last_instruction()
# [R19 fix] if-drop Defect 3: POP_JUMP_* 结尾的块是兄弟 IfRegion 条件块，
# 非线性清理块。with normal-exit 清理恒线性（POP_EXCEPT/RERAISE/POP_TOP/
# JUMP_FORWARD/RETURN），绝无条件分支。清理区连续且终止于 with 自然出口
# （__exit__ 调用的 JUMP_FORWARD 目标）。扫描一旦到达条件跳转块即进入
# post-with 兄弟代码，依「每块唯一归属」终止清理扫描。
if last and last.opname.startswith('POP_JUMP_'):
    break
# [R19 fix] block_to_region 归属守卫（镜像 R07 Pattern T）：已被非-WithRegion
# 占用的块（如 TRY/LOOP 先识别的区域）不当 with cleanup。
_owner = self.block_to_region.get(block)
if _owner is not None and not isinstance(_owner, WithRegion):
    continue
```

**为何 `break` 而非 `continue`**：with normal-exit 清理区是**连续**的，位于 body_end 与 with 自然出口（`__exit__` 的 `JUMP_FORWARD` 目标）之间。一旦扫描遇到条件跳转块，必定已离开清理区进入 post-with 兄弟代码（清理块恒以 POP_EXCEPT/RERAISE/POP_TOP/JUMP_FORWARD/RETURN 结尾，绝不含 POP_JUMP）。`break` 严格反映「清理边界=自然出口」语义，避免后续兄弟代码块被误收集。本例中清理块 110/118/120（RERAISE/POP_TOP）在 126 之前已收集，`break` 不损失合法清理块。

**算法 4 原则合规**：
- **自底向上归约**: ✓ 未改变归约顺序（仅在清理块收集阶段收紧边界）
- **每块唯一归属**: ✓ 强化——POP_JUMP_* 守卫块归兄弟 IfRegion，不归 WithRegion；block_to_region 归属守卫排除已被 TRY/LOOP 占用的块
- **嵌套即抽象节点**: ✓ 未改变
- **入口引用语义**: ✓ 未改变

**安全性**：POP_JUMP_* 是 Python 3.11+ 条件跳转指令族（POP_JUMP_FORWARD_IF_TRUE/FALSE/NONE/NOT_NONE、POP_JUMP_BACKWARD_IF_* 等），仅出现在 if/while/for 条件块、BoolOp 短路块、match 守卫块。with normal-exit 清理块（`__exit__(None,None,None)` 调用 + 栈 unwind）恒线性，绝不含条件跳转。守卫语义严格无副作用。

## 4. 回归测试结果

### 模块编译检查
```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"
OK compile
```

### 目标 pyc 验证（修复后）
```
strategy.pyc: partial 50.00% (1/2)
  - trade_strategy_add: 100% matched（true_diffs 61 → 0）
  - <module>: 39 true_diffs（Pattern R2 不可修复残留）
const.pyc: ok 100.00% (1/1)  — 首次验证即 100%
```

### 最小复现实例验证
```
11 repros: 0 DEFECT-REPRO, 11 NO-DEFECT, 0 ERROR
  - 6 DEFECT-REPRO (repro_01-06): post-with if/elif/return 守卫，R19 修复后全部 NO-DEFECT
  - 5 CTRL (repro_07-11): const.pyc 镜像 + with 无 post-if + if 无 with + with 嵌套于 if，确认非缺陷路径不受影响
```

### 跨轮回归验证
- R18 minimal_repros: **11/11 NO-DEFECT**（与 R18 一致，零回归）
- R18 KW_NAMES 修复（with 关键字参数保留）继续生效

## 5. 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀: **0 新增**（修复为现有 `_collect_normal_exit_cleanup` 方法内 +2 道守卫，无新 helper 函数）
- 硬编码深度上限: **0 新增**
- 跨区域启发式: **0 新增**（修复为结构性指令族判定 POP_JUMP_* + block_to_region 权威归属，非实例特征）
- 后处理补丁: **0 新增**
- 针对特定 pyc 的硬编码绕过: **0 新增**

## 6. docstring 更新

- `region_ast_generator.py:_generate_with` docstring「字节码一致性约束」段落新增 `[R19 fix]` 子段落（L18611-18620），说明 if-drop Defect 3 根因、_collect_normal_exit_cleanup 守卫、对 with_cleanup_blocks 集合的影响、算法原则合规。
- `region_analyzer.py:_identify_with_regions` docstring「唯一归属判定」段落新增 `[R19 fix] cleanup_blocks 边界守卫` 说明（L8451-8455）。
- `_collect_normal_exit_cleanup` 修复点处新增详细行内注释（[R19 fix] ×2 段）。

## 7. 残留问题

### 本轮修复后残留
- **strategy.pyc `<module>` Pattern R2**：`IMPORT_FROM common; SWAP 2; POP_TOP` 优化器 artifact，无源码可复现，不可修复（与 R18 一致）。

### 不可修复残留（与前轮一致）
- main.pyc：深度残留 failed，不阻塞前向进度。

### 下一轮建议
继续按字母序轮询 pending pyc（IQCommon/logger/__init__.pyc 或 strategy/__init__.pyc）。Defect 3 已闭环，无新残留缺陷。
