# 架构工程师分析报告 — Pass 1 / ASSERT 区域

## 方法定位
- `_identify_assert_regions`: region_analyzer.py L9269-L9474
- `_generate_assert`: region_ast_generator.py L2076-L2270
- 关键补丁: `_detect_assert_boolop_chain` (复刻 BoolOpRegion), `_build_assert_boolop_condition` (复刻 or_groups), walrus value_target 临时清空

## 4 原则合规性
- 原则 1（自底向上归约）：违反 — ASSERT 先于 BOOLOP/CC/TERNARY 识别，被迫复刻表达式级逻辑
- 原则 2（每块唯一归属）：部分违反 — assert 嵌套在 if body 时 message_block 双归属 (if57 失败)
- 原则 3（嵌套即抽象节点）：违反 — AssertRegion 把 chained-compare/boolop 链拍平到自有字段而非独立子区域嵌套
- 原则 4（入口引用语义）：基本合规 — message_block 引用嵌套 TernaryRegion 入口正确；condition_block 引用 ternary.merge_block 未实现

## 反模式检查
- **硬编码深度上限**: 4 处 `depth < 8` (L9581, L9625, L9654, L9680) — 4 个 fall-through 遍历器均硬编码 8 步上限
- **后处理补丁**: L1339 事后过滤 assert_regions 与 ternary 重叠；生成时 should_skip 守卫反向扫描所有兄弟区域
- **跨区域跨层次启发式**: _detect_assert_boolop_chain 复刻 BoolOpRegion 算法
- **Fallback 补丁**: L9408-9414 显式 "Fallback" 注释保留 legacy 行为
- **文档反模式痕迹**: L9327/L9356 文档串引用不存在的 `_fix_assert_none_check_direction`（实际为 `_invert_assert_none_check_direction`）
- **虚假通过率声明**: L9358-9359 "100% 通过率，无已知失败模式" vs 实际 22/27；L2131 同
- **状态突变 hack**: L2579-2607 walrus 临时清空 _nested_ternary.value_target
- **AssertRegion 多态方法缺失**: 未覆写 contains_block/else_block_conflict，导致 assert 嵌套在 if body 时 message_block 双归属

## 本轮建议修复（3 项，含失败用例修复）
### 修复 1 — 消除 4 处 `depth < 8` 硬编码上限
位置: region_analyzer.py L9581, L9625, L9654, L9680
策略: 删除 `and depth < 8` 条件与 depth 计数；已有 seen 集合防环，终止条件已覆盖所有合法停止点
理由: 消除硬编码深度上限反模式，对深层 fall-through 链从漏识别变为正确识别；极低风险

### 修复 2 — 清理文档串反模式痕迹与虚假通过率声明
位置: 
- L9327, L9356: `_fix_assert_none_check_direction` → `_invert_assert_none_check_direction`
- L9358-9359: 删除"100% 通过率"，改为"ASSERT bounded subset: 22/27 passed，已知失败模式：assert-in-if-body / ternary-in-assert-test"
- region_ast_generator.py L2131: 删除"字节码一致性状态：100% 完全匹配"
理由: 零风险纯文档，消除禁止前缀反模式残留 + 虚假声明，让维护者看到真实失败模式

### 修复 3 — 为 AssertRegion 补齐 contains_block/else_block_conflict 多态方法（修复 3 个失败用例）
位置: region_analyzer.py L837-874 AssertRegion 类定义
策略:
```python
def contains_block(self, block) -> bool:
    return block in self.blocks  # blocks 已含 condition_block + message_block + chain_blocks

def else_block_conflict(self, block) -> bool:
    return block is self.message_block  # message_block 含 RAISE_VARARGS，永不 fall-through 到 else
```
根因: if57 用例 `if a > 0: assert a > 0` 失败，IfRegion.then_blocks 收集时把 assert 的 message_block (含 LOAD_ASSERTION_ERROR + RAISE_VARARGS) 也纳入 then 体内，导致指令数 18 vs 23 多出 5 条。补齐多态方法后父 IfRegion 通过 contains_block 识别 message_block 已归属 AssertRegion 而跳过。
预期: 修复 if57_a/n/x 三个失败用例，ASSERT 从 22/27 提升到 25/27
理由: 消除 assert-in-if-body 双归属违反 P2/P3，让 AssertRegion 通过多态分发融入归约框架

## 其他问题（后续迭代）
- assert (ternary) 形态 condition_block=ternary.merge_block 未建立父子引用（需独立设计）
- ASSERT 先于 BOOLOP/CC/TERNARY 识别顺序调整（高风险，影响全流水线）
- walrus value_target 临时清空状态突变移除
- _detect_assert_boolop_chain 复刻逻辑改用通用 BoolOpRegion
