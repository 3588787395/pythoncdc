# CFG方法审批指南 (CFG Method Approval Guide)

## 📌 文档目的

本文档定义了CFG区域归约反编译器中**合规方法**的标准，以及**补丁式代码**的识别和审批流程。目标是确保所有新增/修改的方法都遵循"算法驱动、单一路径、职责分离"的核心原则。

---

## 🔴 补丁判定标准（6项代码特征）

**重要：补丁由代码特征决定，不由注释决定！**

### 特征1: 后处理修正（Post-processing Fix）
```python
# ❌ 违规：在生成阶段之后修改结果
def _generate_if(self, region):
    result = self._build_if_node(region)
    # 后处理修正 - 说明识别阶段有问题
    while result['body'] and result['body'][-1]['type'] == 'Return':
        if result['body'][-1].get('value', {}).get('value') is None:
            result['body'].pop()  # 删除return None
    return result

# ✅ 合规：在识别阶段就正确处理
def _identify_if(self, block):
    region = IfRegion(...)
    region.has_trailing_return_none = False  # 在这里判断
    return region
```

**判定依据**：
- 在`_generate_*`方法中存在对生成结果的修改逻辑
- 典型模式：`pop()`, `filter()`, `strip()`, `remove()`作用于AST节点列表

---

### 特征2: 特殊情况分支（Special-case Branching）
```python
# ❌ 违规：无法用统一算法覆盖的if/elif链
def _generate_if(self, region):
    if region.is_simple_compare:
        return self._handle_simple_case(region)
    elif region.is_chained_compare:
        return self._handle_chained_case(region)  # 特殊处理
    elif region.has_ternary:
        return self._handle_ternary_case(region)  # 又一个特殊处理
    else:
        return self._normal_generation(region)

# ✅ 合规：统一算法 + 数据驱动
def _generate_if(self, region):
    if isinstance(region, TernaryRegion):
        return self._generate_ternary(region)  # 委托给专门的RegionType
    if region.chained_compare_blocks:
        return self._build_chained_compare_from_region_data(region)  # 使用region数据
    # 统一的正常流程
    ...
```

**判定依据**：
- 方法内有3个以上的`if/elif`分支处理不同"特殊情况"
- 分支之间没有明显的算法共性，各自为战

---

### 特征3: 多种生成路径（Multiple Generation Paths）
```python
# ❌ 违规：同一结构类型有多个入口方法
def _try_generate_if(self, region):  # 路径1: 尝试性生成
    ...

def _generate_if_from_block(self, block):  # 路径2: 从block生成
    ...

def _fallback_generate_if(self, region):  # 路径3: fallback
    ...

# ✅ 合规：每种RegionType只有1个入口
def _generate_if(self, region):  # 唯一入口
    if region.chained_compare_blocks:
        return self._build_chained_compare(...)  # 内部辅助，不是独立路径
    ...
```

**判定依据**：
- 存在`_try_*`, `_fallback_*`, `_*_from_block`等多个方法生成同一种结构
- 方法名前缀表明这是"备选"或"尝试性"路径

---

### 特征4: 跨职责修改（Cross-responsibility Modification）
```python
# ❌ 违规：在生成器中执行分析逻辑
class RegionASTGenerator:
    def _generate_if(self, region):
        # 直接访问分析器内部数据结构
        dom_tree = self.region_analyzer.dominator_tree  # ❌
        back_edges = self.cfg.back_edges  # ❌

        # 或者直接修改region的分析结果
        region.blocks.add(some_block)  # ❌
        region.condition_block = other_block  # ❌

# ✅ 合规：只通过API访问，不修改分析结果
class RegionASTGenerator:
    def _generate_if(self, region):
        role = self.block_role(block)  # ✅ 通过API查询
        cond_expr = region.condition_expr  # ✅ 只读访问region属性
```

**判定依据**：
- 生成器中直接访问`dominator_tree`, `back_edges`, `exception_table`等分析数据
- 生成器中修改`region.blocks`, `region.condition_block`等分析结果
- 生成器中包含应该属于`RegionAnalyzer`的识别逻辑

---

### 特征5: 硬编码偏移（Hardcoded Offsets）
```python
# ❌ 违规：依赖magic number
def _generate_loop(self, region):
    if block.offset == 42:  # magic number!
        return self._special_handle()
    instructions[0:3]  # 硬编码索引

# ✅ 合规：使用语义化标识
def _generate_loop(self, region):
    if block is region.header_block:  # 语义化判断
        return self._handle_header()
    meaningful_instrs = [i for i in instructions if i.opname not in SKIP_OPS]
```

**判定依据**：
- 使用数字常量作为offset、block_id、指令索引
- 没有命名常量或语义化解释的数字字面量

---

### 特征6: 顺序依赖（Order Dependency）
```python
# ❌ 违规：执行顺序影响正确性
def generate(self):
    self._fix_issue_a()  # 必须先执行
    self._fix_issue_b()  # 依赖于a的结果
    self._patch_issue_c()  # 依赖于b的结果
    result = self._generate()

# ✅ 合规：无顺序依赖
def generate(self):
    regions = self.region_analyzer.analyze()  # 一次性分析
    for region in regions:
        ast = self._generate_region(region)  # 独立生成
```

**判定依据**：
- 多个fix/patch方法必须按特定顺序调用
- 后续方法依赖前序方法的副作用
- 无法并行或重排执行顺序

---

## ✅ 方法创建6项必答问题

在添加任何新方法之前，必须回答以下问题：

### Q1: 这个方法的单一职责是什么？
- **要求**：用一句话描述该方法做什么
- **合规示例**："_generate_if负责将IfRegion转换为If AST节点"
- **违规示例**："_fix_if_issues修复if语句的各种问题"

### Q2: 这个方法属于哪个阶段？
- **选项**：识别阶段(RegionAnalyzer) / 生成阶段(RegionASTGenerator) / 辅助工具
- **要求**：不得跨阶段

### Q3: 是否已有相同RegionType的生成方法？
- **如果否** → 正常创建
- **如果是** → 为什么需要新方法？能否扩展现有方法？

### Q4: 这个方法是否修改传入参数？
- **合规**：只读取参数，返回新结果
- **违规**：修改region.blocks, region.attributes等

### Q5: 这个方法是否有后处理逻辑？
- **合规**：生成即最终结果，无需修正
- **违规**：方法末尾有pop(), filter(), strip()等操作

### Q6: 能否通过单元测试验证这个方法？
- **要求**：必须可测试，不能依赖全局状态或执行顺序

---

## 📝 合规方法模板

```python
def _generate_{REGION_TYPE}(self, region: {RegionTypeClass}) -> {ReturnType}:
    """
    {RegionType}区域的AST生成器

    算法：
    1. {步骤1}
    2. {步骤2}
    3. {步骤3}

    输入：{RegionType}实例（由RegionAnalyzer提供）
    输出：AST节点或节点列表

    不变性：
    - 不修改region属性
    - 不调用其他_generate_*方法（除委托外）
    - 无后处理修正
    """

    # 前置条件检查
    if not region.entry:
        return {'type': 'Pass'}

    region_id = id(region)
    self._generating_regions.add(region_id)

    try:
        # 核心生成逻辑（无特殊分支）
        result = self._build_{region_type}_node(region)

        return result

    finally:
        self._generating_regions.discard(region_id)
        self._generated_regions.add(region_id)
```

---

## 🔄 审批流程

### 第1步：自审（Self-review）
开发者对照上述6项特征自检：
- [ ] 无后处理修正
- [ ] 无特殊情况分支（>3个if/elif）
- [ ] 无多路径入口
- [ ] 无跨职责访问
- [ ] 无硬编码偏移
- [ ] 无顺序依赖

**工具支持**：运行审计脚本
```bash
python scripts/audit_compliance.py --verbose
```

### 第2步：代码审查（Code Review）
审查者检查：
1. 方法命名是否符合规范（无`_try_`, `_fix_`等前缀）
2. 是否遵循单一职责原则
3. 是否有对应的单元测试
4. 审计脚本是否报告FAIL

### 第3步：CI集成（CI Integration）
在CI pipeline中添加：
```yaml
- name: Compliance Audit
  run: |
    python scripts/audit_compliance.py --json --output audit_report.json
    # 如果report中fail > 0，CI失败
```

**通过标准**：
- FAIL = 0 （必须）
- WARN < 10 （建议）

---

## 📚 常见违规案例库

### 案例1: Return None过滤（后处理修正）
**位置**：`_generate_if`, `_generate_match_as_if`
**问题**：
```python
while stmts and stmts[-1].get('type') == 'Return' \
      and stmts[-1].get('value', {}).get('type') == 'Constant' \
      and stmts[-1].get('value', {}).get('value') is None:
    stmts.pop()
```
**根因**：RegionAnalyzer未正确标记trailing return none
**修复方案**：在`_identify_if`/`_identify_match`中设置`region.has_trailing_return_none = True`，在生成时跳过

**状态**：⚠️ WARN（待修复）

---

### 案例2: Try体生成的_try_前缀（多路径）
**位置**：原`_try_generate_body`（已修复为`_generate_try_body`）
**问题**：方法名暗示这是"尝试性"路径
**修复**：✅ 已重命名为标准`_generate_*`前缀

**状态**：✅ FIXED

---

### 案例3: Match→If转换的特殊方法（多路径）
**位置**：`_generate_match_as_if`
**问题**：MatchRegion可能生成Match或If两种结构
**评估**：这是合理的委托模式，因为Match→If是语义转换，不是fallback
**结论**：✅ 合规（但应考虑是否应在识别阶段决定）

**状态**：✅ ACCEPTED

---

### 案例4: 空分支过滤（后处理修正）
**位置**：`_generate_basic_region`
**问题**：
```python
if not _has_meaningful:
    if _has_control_flow:
        block_stmts = []  # 过滤空块
```
**根因**：未区分"真正的空块"和"控制流后的空块"
**修复方案**：RegionAnalyzer应标记`BlockRole.EMPTY_AFTER_CONTROL_FLOW`

**状态**：⚠️ WARN（待修复）

---

### 案例5: dominator_tree直接访问（跨职责）
**位置**：（假设性案例）
**问题**：
```python
def _generate_if(self, region):
    doms = self.region_analyzer.dominator_tree.dominators(entry)
```
**修复**：使用`self.block_role(block)` API

**状态**：N/A（当前代码中未发现）

---

### 案例6: 硬编码指令索引（硬编码偏移）
**位置**：（假设性案例）
**问题**：
```python
instr = block.instructions[2]  # 第3条指令是条件
```
**修复**：使用语义化查找
```python
cond_instr = next(i for i in block.instructions if i.opname in CONDITIONAL_JUMP_OPS)
```

**状态**：N/A（当前代码中少量存在，均为WARN级别）

---

### 案例7: Pass+Return None合并（后处理修正）
**位置**：`_generate_block_statements`
**问题**：
```python
if has_nop and has_return:
    # 特殊处理NOP+RETURN_VALUE模式
    pass_return_stmts = stmts
```
**根因**：未识别这是`while True: break`的bytecode模式
**修复方案**：在RegionAnalyzer中识别这种模式并标记为`BlockRole.WHILE_TRUE_BREAK`

**状态**：⚠️ WARN（待修复）

---

### 案例8: finally拷贝块截断（边界情况）
**位置**：`_generate_try_body`
**问题**：
```python
_fc_keep = region.finally_copy_blocks.get(block.start_offset)
if _fc_keep is not None:
    # 截断指令序列
    cutoff_idx = ...
    truncated_instrs = block.instructions[:cutoff_idx]
```
**评估**：这是finally语义的正确处理，属于算法必要部分
**结论**：✅ 合规（但需补充注释说明算法原理）

**状态**：✅ ACCEPTED

---

### 案例9: nested try区域排序（顺序依赖风险）
**位置**：`_generate_try_body`
**问题**：
```python
for ntr in sorted(nested_try_regions, key=lambda r: r.try_offset_start):
    # 必须按偏移排序处理
```
**评估**：这是正确的拓扑排序，不是任意的顺序依赖
**结论**：✅ 合规（基于数据依赖的合理排序）

**状态**：✅ ACCEPTED

---

### 案例10: import语句预提取（跨职责边缘）
**位置**：`_generate_if`, `generate`
**问题**：在生成阶段从指令流中提取import语句
**评估**：这不是"分析逻辑"，而是"语法重建"的一部分
**结论**：⚠️ 边缘情况（建议提取为独立的_import_preprocessor）

**状态**：⚠️ WARN（建议重构）

---

## 📊 当前合规状态总览

| 维度 | 状态 | 数量 | 说明 |
|------|------|------|------|
| 方法命名 | ✅ PASS | 0 | 所有禁止前缀已消除 |
| 后处理修正 | ⚠️ WARN | ~7处 | Return None过滤，待Phase 6修复 |
| 跨职责 | ⚠️ WARN | 少量 | import提取等边缘情况 |
| 多路径 | ✅ PASS | 0 | 每种RegionType唯一入口 |
| 硬编码偏移 | ⚠️ WARN | 少量 | 主要是索引访问 |
| 分析结果修改 | ✅ PASS | 0 | 未发现直接修改 |

**总体评级**: ⚠️ **B+** （核心原则已满足，细节待优化）

---

## 🎯 下一步行动项

### 高优先级（必须在v2.0前完成）
1. [ ] 消除所有Return None过滤（迁移到识别阶段）
2. [ ] 为空分支过滤建立RegionAnalyzer标记机制
3. [ ] 将import提取逻辑独立为预处理器

### 中优先级（v2.1优化）
4. [ ] 减少硬编码索引，使用语义化查找
5. [ ] 为所有WARN项添加TODO注释和issue追踪

### 低优先级（持续改进）
6. [ ] 提高单元测试覆盖率（目标>90%）
7. [ ] 建立性能基准测试套件

---

## 📞 联系与反馈

如有疑问或发现新的违规案例，请：
1. 更新本文档的"常见违规案例库"
2. 运行审计脚本确认影响范围
3. 提交PR时引用相关案例编号

**最后更新**: 2026-05-07
**版本**: v1.0
**审核人**: AI Assistant
