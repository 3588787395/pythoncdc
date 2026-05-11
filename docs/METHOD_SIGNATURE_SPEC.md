# 方法签名规范文档

## 概述

本文档定义了区域分析器（RegionAnalyzer）和区域AST生成器（RegionASTGenerator）的方法签名规范，用于防止补丁式编程模式。

## 核心原则

1. **唯一识别方法**：每个区域类型有且只有一个主识别方法
2. **唯一生成方法**：每个区域类型有且只有一个主生成方法
3. **禁止后处理**：不允许 `_fix_`、`_patch_`、`_hack_` 等补丁式方法名
4. **标准命名**：使用统一的命名约定便于代码审查和维护

## 区域类型枚举

```python
class RegionType(Enum):
    BASIC = auto()           # 基本块
    SEQUENCE = auto()        # 序列
    IF = auto()              # if分支（基础）
    IF_THEN = auto()         # if-then
    IF_THEN_ELSE = auto()    # if-then-else
    IF_ELIF_CHAIN = auto()   # if-elif链
    WHILE_LOOP = auto()      # while循环
    FOR_LOOP = auto()        # for循环
    TRY_EXCEPT = auto()      # try-except
    TRY_FINALLY = auto()     # try-finally
    WITH = auto()            # with语句
    MATCH = auto()           # match-case
    ASSERT = auto()         # assert语句
    BREAK = auto()           # break语句
    CONTINUE = auto()        # continue语句
    PASS = auto()            # pass语句
    RETURN = auto()          # return语句
    BOOL_OP = auto()         # 布尔运算
    TERNARY = auto()         # 三元表达式
```

## 区域分析器 - 主识别方法

| 区域类型 | 主识别方法 | 说明 |
|---------|----------|------|
| TRY_EXCEPT | `_identify_try_except_regions` | 识别try-except-finally区域 |
| TRY_FINALLY | `_identify_try_except_regions` | 同上，统一处理 |
| FOR_LOOP | `_identify_loop_regions` | 识别for循环区域 |
| WHILE_LOOP | `_identify_loop_regions` | 识别while循环区域 |
| WITH | `_identify_with_regions` | 识别with语句区域 |
| MATCH | `_identify_match_regions` | 识别match-case区域 |
| ASSERT | `_identify_assert_regions` | 识别assert语句区域 |
| BOOL_OP | `_identify_boolop_regions` | 识别链式比较/布尔运算区域 |
| TERNARY | `_identify_ternary_regions` | 识别三元表达式区域 |
| IF | `_identify_conditional_regions` | 识别if分支区域 |
| IF_THEN | `_identify_conditional_regions` | 同上 |
| IF_THEN_ELSE | `_identify_conditional_regions` | 同上 |
| IF_ELIF_CHAIN | `_identify_conditional_regions` | 同上 |
| SEQUENCE | `_identify_sequence_regions` | 识别序列/线性块区域 |
| BASIC | `_identify_sequence_regions` | 同上 |

### 识别方法命名规则

```
_identify_<region_type>_regions
```

- 前缀：`_identify_`
- 中缀：区域类型关键词
- 后缀：`_regions`

## 区域生成器 - 主生成方法

| 区域类型 | 主生成方法 | 说明 |
|---------|----------|------|
| TRY_EXCEPT | `_generate_try_except` | 生成try-except AST |
| TRY_FINALLY | `_generate_try_finally` | 生成try-finally AST |
| FOR_LOOP | `_generate_for_loop` | 生成for循环AST |
| WHILE_LOOP | `_generate_while_loop` | 生成while循环AST |
| WITH | `_generate_with` | 生成with语句AST |
| MATCH | `_generate_match` | 生成match-case AST |
| ASSERT | `_generate_assert` | 生成assert AST |
| BOOL_OP | `_generate_boolop` | 生成布尔运算AST |
| TERNARY | `_generate_ternary` | 生成三元表达式AST |
| IF | `_generate_if` | 生成if分支AST |
| IF_THEN | `_generate_if` | 同上 |
| IF_THEN_ELSE | `_generate_if` | 同上 |
| IF_ELIF_CHAIN | `_generate_if` | 同上（统一处理） |
| SEQUENCE | `_generate_basic` | 生成序列块AST |
| BASIC | `_generate_basic` | 同上 |

### 生成方法命名规则

```
_generate_<region_type>
```

- 前缀：`_generate_`
- 中缀：区域类型关键词
- 无后缀或可选子类型后缀

## 禁止的方法模式

以下方法名模式被严格禁止：

| 模式 | 说明 | 严重性 |
|------|------|--------|
| `_fix_*` | 后处理修正 | ERROR |
| `_patch_*` | 补丁方法 | ERROR |
| `_hack_*` | 临时hack | ERROR |
| `_workaround_*` | 变通方案 | ERROR |
| `_correct_*` | 修正方法 | ERROR |
| `_adjust_*` | 调整方法 | WARNING |
| `_merge_*` | 合并逻辑 | WARNING |
| `_fallback_*` | 回退逻辑 | WARNING |
| `_from_block` | 从块直接生成 | ERROR |
| `_raw_*` | 原始操作 | WARNING |
| `_unsafe_*` | 不安全操作 | ERROR |

## 验证工具

### 使用方法签名验证器

```bash
# 验证所有方法签名
python scripts/validate_method_signatures.py

# 验证分析器
python scripts/validate_region_analyzer_signatures.py core/cfg/region_analyzer.py

# 验证生成器
python scripts/validate_region_generator_signatures.py core/cfg/region_ast_generator.py

# 输出JSON格式
python scripts/validate_method_signatures.py --json
```

### 集成到 pre-commit

在 `.pre-commit-config.yaml` 中添加：

```yaml
repos:
  - repo: local
    hooks:
      - id: method-signature-check
        name: Method Signature Check (Anti-Patch)
        entry: python scripts/validate_method_signatures.py
        language: system
        types: [python]
        files: ^core/cfg/.*\.py$
        pass_filenames: false
```

## 防补丁检查规则

### 规则 1：单一识别方法
每个区域类型在 `RegionAnalyzer` 中必须只有 **一个** 主识别方法。

违规示例：
```python
def _identify_if_regions(self): ...  # 不推荐
def _identify_if_then_regions(self): ...  # 不推荐
def _identify_if_else_regions(self): ...  # 违规：多个识别方法
```

正确做法：
```python
def _identify_conditional_regions(self):  # 统一处理所有if类型
    # 根据条件块结构分类为 IF_THEN / IF_THEN_ELSE / IF_ELIF_CHAIN
    pass
```

### 规则 2：单一生成方法
每个区域类型在 `RegionASTGenerator` 中必须只有 **一个** 主生成方法。

违规示例：
```python
def _generate_if_then(self): ...
def _generate_if_else(self): ...  # 违规
```

正确做法：
```python
def _generate_if(self, region):  # 统一处理所有if类型
    if region.region_type == RegionType.IF_THEN_ELSE:
        # 处理if-else
    elif region.region_type == RegionType.IF_ELIF_CHAIN:
        # 处理elif链
    pass
```

### 规则 3：禁止后处理修正
不允许在生成后进行修正或修补。

违规示例：
```python
def _generate_if(self, region):
    ast = self._do_generate(region)
    return self._fix_ast(ast)  # 违规：后处理修正
```

正确做法：
```python
def _generate_if(self, region):
    # 在识别阶段正确分类，在生成阶段直接生成正确的AST
    return self._build_if_node(region)
```

## 验证报告格式

```
================================================================================
  方法签名验证报告 - 防补丁机制
================================================================================
  分析器: core/cfg/region_analyzer.py
  生成器: core/cfg/region_ast_generator.py

  [区域分析器]
--------------------------------------------------------------------------------
    ✓ OK       | IF_THEN_ELSE    | 识别: _identify_conditional_regions
    ✓ OK       | IF_ELIF_CHAIN   | 识别: _identify_conditional_regions
    ✓ OK       | FOR_LOOP        | 识别: _identify_loop_regions
    ...

  [区域生成器]
--------------------------------------------------------------------------------
    ✓ OK       | IF_THEN_ELSE    | 生成: _generate_if
    ✓ OK       | FOR_LOOP        | 生成: _generate_for_loop
    ...

  [违规详情]
--------------------------------------------------------------------------------
    ✗ [ERROR] forbidden_pattern (generator)
        方法: _patch_special_case:1234, 模式: patch_pattern
    ⚠ [WARNING] multiple_generate_methods (generator)
        区域: BOOL_OP, 方法: _generate_bool, _generate_boolop

================================================================================
  统计: 1 个错误, 1 个警告
  结论: ✗ 验证失败
================================================================================
```

## 维护指南

### 添加新区域类型

1. 在 `RegionType` 枚举中添加新类型
2. 在 `RegionAnalyzer` 中添加识别方法
3. 在 `RegionASTGenerator` 中添加生成方法
4. 更新本规范文档
5. 运行验证器确保无违规

### 代码审查检查清单

- [ ] 新方法是否遵循命名规范？
- [ ] 是否有多个方法处理同一区域类型？
- [ ] 是否有补丁式方法名？
- [ ] 是否存在后处理修正逻辑？

## 附录：完整区域类型映射表

### 识别方法映射

| RegionType | 识别方法 |
|------------|---------|
| BASIC | _identify_sequence_regions |
| SEQUENCE | _identify_sequence_regions |
| IF | _identify_conditional_regions |
| IF_THEN | _identify_conditional_regions |
| IF_THEN_ELSE | _identify_conditional_regions |
| IF_ELIF_CHAIN | _identify_conditional_regions |
| FOR_LOOP | _identify_loop_regions |
| WHILE_LOOP | _identify_loop_regions |
| TRY_EXCEPT | _identify_try_except_regions |
| TRY_FINALLY | _identify_try_except_regions |
| WITH | _identify_with_regions |
| MATCH | _identify_match_regions |
| ASSERT | _identify_assert_regions |
| BOOL_OP | _identify_boolop_regions |
| TERNARY | _identify_ternary_regions |

### 生成方法映射

| RegionType | 生成方法 |
|------------|---------|
| BASIC | _generate_basic |
| SEQUENCE | _generate_basic |
| IF | _generate_if |
| IF_THEN | _generate_if |
| IF_THEN_ELSE | _generate_if |
| IF_ELIF_CHAIN | _generate_if |
| FOR_LOOP | _generate_for_loop |
| WHILE_LOOP | _generate_while_loop |
| TRY_EXCEPT | _generate_try_except |
| TRY_FINALLY | _generate_try_finally |
| WITH | _generate_with |
| MATCH | _generate_match |
| ASSERT | _generate_assert |
| BOOL_OP | _generate_boolop |
| TERNARY | _generate_ternary |
