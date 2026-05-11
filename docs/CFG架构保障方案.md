# CFG反编译器架构保障方案 — 防止走回补丁老路

## 一、核心红线规则

### 规则1：禁止后处理修正

**定义**：后处理修正 = 在结构识别完成后，通过额外的方法修正识别结果。

**判断标准**：
- 方法名包含 `fix`、`patch`、`correct`、`adjust`、`repair` → 违规
- 方法在 `analyze()` 的识别步骤之后执行，且修改已有区域 → 违规
- 方法遍历已有区域列表并修改其属性 → 违规

**允许的例外**：
- `_build_region_hierarchy()` — 这是构建层次关系，不是修正识别结果
- `_find_try_else_blocks()` — 这是完善当前正在构建的区域，不是后处理修正

### 规则2：禁止在AST生成阶段做结构判断

**定义**：AST生成阶段只负责将区域信息映射为AST节点，不应做任何控制流结构的二次判断。

**判断标准**：
- `_generate_*_from_block()` 形式的方法 → 违规（应从区域生成，不从块生成）
- 在 `_generate_block_statements()` 中根据指令序列判断控制结构 → 违规
- 在生成阶段重新分析支配关系或回边 → 违规

**允许的例外**：
- break/continue/return 的识别 — 这些是语句级别的语义，不是控制流结构
- 表达式重建（`ExpressionReconstructor`）— 这是独立的模块

### 规则3：禁止同一功能存在多个版本

**定义**：不允许同一功能存在 v1/v2 并存的情况。

**判断标准**：
- 同名方法带 `_v2` 后缀且原方法仍存在 → 违规
- 同一逻辑在两处实现 → 违规

**处理方式**：确定正确的版本，删除旧版本。

### 规则4：每次修改必须通过完备性测试

**定义**：任何对 region_analyzer.py 或 region_ast_generator.py 的修改，必须通过完备性测试套件。

**完备性测试套件** = 覆盖所有控制流语法及其嵌套排列组合的测试用例集合。

---

## 二、架构约束检查清单

每次修改代码前，必须通过以下检查：

### 修改前检查

| 检查项 | 通过标准 |
|--------|---------|
| 修改是否在识别阶段解决问题？ | 是 → 通过；否 → 重新设计 |
| 修改是否引入后处理方法？ | 否 → 通过；是 → 违规 |
| 修改是否在AST生成阶段做结构判断？ | 否 → 通过；是 → 违规 |
| 修改是否增加了新的 `_is_*` 启发式判断？ | 否 → 通过；是 → 评估是否可用算法替代 |

### 修改后检查

| 检查项 | 通过标准 |
|--------|---------|
| region_analyzer.py 中"关键修复"标记数是否仍为0？ | 0 → 通过 |
| region_ast_generator.py 中"关键修复"标记数是否仍为0？ | 0 → 通过 |
| 是否存在 `_fix_*` 或 `_merge_*` 后处理方法？ | 否 → 通过 |
| 完备性测试是否全部通过？ | 是 → 通过 |

---

## 三、正确的问题解决路径

### 3.1 循环相关问题

| 问题症状 | 错误做法 | 正确做法 |
|----------|---------|---------|
| while循环条件不正确 | 在AST生成时修正条件 | 完善 `_find_loop_condition()` 算法 |
| continue被误判为pass | 在 `_generate_block_statements` 中添加特殊case | 完善 natural back edge 算法，精确区分隐式/显式跳转 |
| break被错误替换 | 添加更多 `_is_break_block` 变体 | 完善退出块的语义特征定义，统一到 `_is_loop_exit_successor()` |
| for-else丢失else | 在生成阶段查找else块 | 完善 `_find_loop_else()` 算法 |

### 3.2 条件相关问题

| 问题症状 | 错误做法 | 正确做法 |
|----------|---------|---------|
| if-else分支错误 | 在生成阶段交换then/else | 完善 `_analyze_if_region()` 中的分支判定 |
| elif链未识别 | 添加 `_merge_elif` 后处理 | 完善 `_check_elif_chain()` 算法 |
| merge点不正确 | 添加 `_fix_merge_point` 后处理 | 完善 `_find_merge_point()` 的可达性分析 |

### 3.3 异常处理相关问题

| 问题症状 | 错误做法 | 正确做法 |
|----------|---------|---------|
| try块范围不正确 | 在生成阶段过滤块 | 完善 `_collect_blocks_in_range()` 的offset范围计算 |
| except handler丢失 | 添加 `_fix_missing_handlers` | 完善 `_extract_except_handler()` 的handler链追踪 |
| finally被误判为except | 添加 `_fix_finally_type` | 完善 `_parse_exception_table()` 的handler类型判断 |
| try-else丢失 | 在生成阶段查找else | 完善 `_find_try_else_blocks()` 算法 |

### 3.4 层次关系问题

| 问题症状 | 错误做法 | 正确做法 |
|----------|---------|---------|
| 区域重叠 | 添加 `_fix_overlaps` 后处理 | 完善 `_build_region_hierarchy()` 的包含关系判定 |
| 父子关系错误 | 添加 `_fix_hierarchy` 后处理 | 完善区域归约算法，确保识别顺序正确 |

---

## 四、代码质量指标

### 4.1 硬性指标（必须维持）

| 指标 | 当前值 | 红线 |
|------|--------|------|
| region_analyzer.py 行数 | 1,378 | ≤ 3,000 |
| region_ast_generator.py 行数 | 1,611 | ≤ 3,000 |
| "关键修复"标记总数 | 0 | = 0 |
| 后处理方法数 | 0 | = 0 |
| `_fix_*` 方法数 | 0 | = 0 |
| `_merge_*` 后处理方法数 | 0 | = 0 |

### 4.2 软性指标（应持续改善）

| 指标 | 当前值 | 目标 |
|------|--------|------|
| 完备性测试通过率 | 待测量 | 100% |
| 单个方法最大行数 | ~150 | ≤ 80 |
| 方法平均行数 | ~30 | ≤ 40 |

---

## 五、代码审查要点

每次代码审查时，重点检查以下模式：

### 5.1 危险模式（立即拒绝）

```python
# 模式1：后处理修正
def _fix_*(self): ...          # 任何 fix 方法
def _patch_*(self): ...        # 任何 patch 方法
def _correct_*(self): ...      # 任何 correct 方法
def _adjust_*(self): ...       # 任何 adjust 方法

# 模式2：在生成阶段做结构判断
def _generate_if_from_block(self, block): ...  # 从块生成结构
def _generate_while_from_condition(self, block): ...

# 模式3：v2版本并存
def _merge_conditions(self): ...
def _merge_conditions_v2(self): ...  # 不允许共存

# 模式4：在analyze()中添加后处理步骤
def analyze(self):
    ...
    self._fix_something()  # 违规！
```

### 5.2 安全模式（允许）

```python
# 模式1：在识别阶段完善算法
def _find_merge_point(self, header, branch_a, branch_b):
    # 改进可达性分析算法 → 允许
    reachable_from_a = self._get_reachable_set(branch_a)
    ...

# 模式2：在区域构建时完善属性
def _identify_loop_regions(self):
    ...
    region.else_blocks = self._find_loop_else(header, body)  # 允许

# 模式3：统一的语句级语义识别
def _generate_block_statements(self, block):
    # 识别 break/continue/return → 允许（语句级，非结构级）
    if self._is_break_jump(instr, block):
        stmts.append({'type': 'Break'})
```

---

## 六、持续改进流程

```
发现问题
    ↓
定位根因（在识别阶段还是生成阶段？）
    ↓
┌─ 识别阶段问题 ──→ 完善识别算法 ──→ 运行完备性测试
│
└─ 生成阶段问题 ──→ 检查是否缺少区域属性 ──→ 在识别阶段添加属性 ──→ 运行完备性测试
                     （不允许在生成阶段做结构判断）
```

**核心原则**：问题总是在上游（识别阶段）解决，而不是在下游（生成阶段）修补。
