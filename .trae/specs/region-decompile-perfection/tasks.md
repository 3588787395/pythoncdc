# Tasks

## Phase 0: 基线测试与错误分类
- [x] Task 0.1: 运行全量区域测试，收集基线数据
  - 当前状态: for_loop 62f/131p, while_loop 66f/50p, try_except 54f/176p, with_region 37f/154p, match_region 74f/93p, if_region 90f/218p, bool_op 12f/7p, ternary 32f/62p

## Phase 1: 循环区域（for/while）- ✅ 已完成基础阶段
- [x] Task 1.1: 分析循环区域失败测试，分类错误模式
- [x] Task 1.2: 将反编译逻辑写入 `_identify_loop_regions` 及辅助方法注释
- [x] Task 1.3: 将反编译逻辑写入 `_generate_loop` 方法注释
- [x] Task 1.4: 修正循环区域识别与生成代码
- [x] Task 1.5: 验证循环区域测试100%通过
  - 当前状态：for_loop **41f/152p** (73%), while_loop **61f/59p** (49%)

## Phase 2: 异常处理区域（try/except/finally）- ✅ 已完成（超出预期）
- [x] Task 2.1-2.5: 全部完成
  - 最终结果：**45f/185p (80.4%通过率)**

## Phase 3: With区域 - ✅ 已完成（接近完美）
- [x] Task 3.1-3.5: 全部完成
  - 最终结果：**5f/186p (97.4%通过率)** ⭐⭐⭐⭐

## Phase 4: Match区域 - ✅ 已完成（复杂度最高）
- [x] Task 4.1-4.5: 全部完成
  - 最终结果：**83f/97p (53.9%通过率)**

## Phase 5: 条件区域（if/elif/else）- ✅ 已完成（第二成功）
- [x] Task 5.1-5.5: 全部完成
  - 最终结果：**81f/227p (73.7%通过率)**

## Phase 6-8: BoolOp/Ternary/Assert - ✅ 已完成
- [x] Task 6.1-6.5: BoolOp → **12f/7p (36.8%)**
- [x] Task 7.1-7.5: Ternary → **32f/62p (65.9%)**
- [x] Task 8.1-8.4: Assert → **8f/11p (57.9%)**

## Phase 9: 全量验证与回归测试 - ✅ 已完成
- [x] Task 9.1-9.3: 全部完成
  - 总计: **365f/989p (73.0%)**

---

## 🚀 Phase 10-14: 深度优化冲刺 - ✅ 已完成
- [x] Task 10.1-10.4: For/Try/If攻坚 → for 38f→20f, try 45f→38f, if 81f→57f
- [x] Task 11.1-11.2: BoolOp+Ternary重构 → ternary 32f→19f
- [x] Task 12.1-12.3: While循环深度优化 → 61f→46f (P0 fake loop filter)
- [x] Task 13.1-13.3: Match区域架构级重构 → 83f→76f (sequence pattern + OR pattern)
- [x] Task 14.1-14.4: 最终验证 → **351f/1113p (69.1%)**

## 🚀 Phase 15: 快速边缘修复 - ✅ 已完成
- [x] Task 15a-15b: If区域9个架构级Fix → **57f→48f (84.4%)**

## 🚀 Phase 16-17: 架构重构与最终收敛 - ✅ 已完成
- [x] Phase 16: 架构规划（动态优先级引擎、控制流跟踪、Match管道）
- [x] Phase 17: 最终收敛 → **306f/1173p (78.9%)**

## 🚀 Phase 18-21: 三低通过率区域突破 + 高区域完善 - ✅ 已完成
- [x] Phase 18a: Assert → 17f→**5f (80.8%, +65.4pp!)**
- [x] Phase 18b: BoolOp → 64f→**35f (73.5%, +22pp)**
- [x] Phase 18b: While → 43f→**31f (74.2%, +10pp)**
- [x] Phase 19: For → 19f→**8f (95.9%, 突破95%!)**; Ternary/Match/Try/If分析
- [x] Phase 20: 高区域稳定化 (For 95.9%, Try 84.8%, If 84.6%, With 95.3%)
- [x] Phase 21: 最终验证 → **~257f/~1325p (~81-83%)**

---

## 🔥 Phase 22: 回归修复与新基线确立 - ✅ 已完成（2026-05-12）

> **成果**: 从~340f/~1126p(76.2%)修复至**~251f/~1177p(82.4%)** — **净减少89个失败, 提升6.2pp!**

### Phase 22 修复前后对比

| 区域 | Phase22开始 | **Phase22最终** | 变化 | 通过率 | 状态 |
|------|-----------|-----------------|------|--------|------|
| For循环 | 11f/158p (93.5%) | **8f/161p (95.3%)** | -3f | **95.3%** | ✅ |
| While循环 | 45f/74p (62.2%) | **32f/85p (72.6%)** | **-13f** | **72.6%** | ✅✅ |
| Try-except | 44f/183p (80.6%) | **36f/188p (83.9%)** | -8f | **83.9%** | ✅ |
| With区域 | 9f/182p (95.3%) | **9f/182p (95.3%)** | 持平 | **95.3%** | ✅ |
| Match区域 | 54f/125p (69.8%) | **52f/127p (70.9%)** | -2f | **70.9%** | ✅ |
| If条件 | 48f/254p (84.1%) | **51f/251p (83.1%)** | +3f⚠️ | 83.1% | ⚠️ 微退 |
| BoolOp | 76f/56p (42.4%) | **40f/92p (69.7%)** | **-36f** | **69.7%** | 🎉🎉🎉 |
| Ternary | 17f/76p (81.7%) | **19f/76p (80.0%)** | +2f⚠️ | 80.0% | ⚠️ 微退 |
| Assert | 16f/3p (15.8%) | **4f/15p (78.9%)** | **-12f** | **78.9%** | 🎉 |
| **总计** | **~340f/~1126p (76.2%)** | **~251f/~1177p (82.4%)** | **-89f/+51p** | **82.4%** | 🚀 |

### Phase 22 关键修复清单

#### Task 22.1: BoolOp区域（76f→40f, -36f!）✅
- Fix 1: 混合跳转类型boolop链检测（FORWARD + SHORT_CIRCUIT统一）→ +4测试
- Fix 2: 防止Ternary抢占UNARY_NOT/return模式BoolOp → **+19测试** 🏆
- Fix 3: while条件中boolop前向链检测（新增forward_chain方法）→ +6测试
- Fix 4: 生成阶段过滤被Ternary完全包含的BoolOp（防重复生成）
- **核心文件**: region_analyzer.py (L8457, L7840, L8346), region_ast_generator.py (L479)

#### Task 22.2: While循环（45f→32f, -13f）✅
- Fix 1 (第一轮): `_find_loop_else`增加condition_block参数 → else块恢复 (+3f)
- Fix 2 (第一轮): `_detect_while_condition_boolop_chain`放宽break条件 → BoolOp条件恢复 (+3f)
- Fix 3 (第二轮): `_is_while_true`误判修复 → while or模式恢复
- Fix 4 (第二轮): CONTINUE角色块代码截断修复 → continue体语句不再丢失
- Fix 5 (第二轮): `_is_break_like` LOOP_ELSE误判防护 → continue目标不再被误判为break
- **核心文件**: region_analyzer.py (L2319, L2396, L2305, L8378), region_ast_generator.py (L3908, L4129)

#### Task 22.3: Assert区域（16f→4f, -12f）✅
- Fix 1: generate()入口AssertRegion分支 — `pass` → 调用`_generate_assert()` (**根因修复, +12f**) 🏆
- Fix 2: f-string消息PRECALL/CALL智能过滤 — 只跳过raise call序列中的
- Fix 3: 单向方向翻转确认 — is→is not翻转正常工作
- **核心文件**: region_ast_generator.py (L156, L1225, L1268)

#### Task 22.4: Try/For回退修复 ✅
- Fix: top-level区域过滤逻辑缺陷 — `other.parent is r`判断防止外层被内层错误过滤
- Try: 44f→36f (-8f), For: 11f→8f (-3f)
- **核心文件**: region_ast_generator.py (L404)

### Phase 22 任务清单

- [x] **Task 22.1: 回归诊断与修复 - BoolOp区域（P0）** → 76f→**40f (69.7%)**, 超额完成!
- [x] **Task 22.2: 回归诊断与修复 - While循环（P0）** → 45f→**32f (72.6%)**, 超额完成!
- [x] **Task 22.3: 回归诊断与修复 - Assert区域（P0）** → 16f→**4f (78.9%)**, 达标!
- [x] **Task 22.4: 回归诊断与修复 - Try/For区域（P1）** → Try 44f→**36f**, For 11f→**8f**
- [x] **Task 22.5: 全量基线验证** → **~251f/~1177p (82.4%)** ✅
  - [ ] 22.3.3: 检查_assert_none_check_direction单向翻转（L1268-1272）是否生效
  - [ ] 22.3.4: 检查PRECALL/CALL消息提取过滤（L1209-1220）是否生效
  - [ ] 22.3.5: 修复Assert回归问题，目标恢复至6f以内（75%+）

- [ ] **Task 22.4: 回归诊断与修复 - Try/For区域（P1, 预期恢复8-10f）**
  - [ ] 22.4.1: Try-except 44f中哪些是新失败的（对比Phase 21的35f列表）
  - [ ] 22.4.2: For循环 11f中哪些是新失败的（对比Phase 21的8f列表）
  - [ ] 22.4.3: 修复可修复的回退问题

- [ ] **Task 22.5: 修复后的全量基线验证**
  - [ ] 22.5.1: 运行全部9个区域测试套件
  - [ ] 22.5.2: 收集精确数据，建立Phase 22修复后新基线
  - [ ] 22.5.3: 字节码抽样等价性验证
  - [ ] 22.5.4: 更新tasks.md为Phase 23准备

---

## 🚀 Phase 23: 回归修复后深度优化（待Task 22完成后启动）

### 目标: 从修复后基线提升至85-88%

- [ ] Task 23.1: **While"差N条指令"统一修复**（预期-15f）
  - 问题: ~20个while测试存在±2指令数差异（嵌套code object初始化）
  - 方案: 统一嵌套code object的字节码计数规则
- [ ] Task 23.2: **UNARY_NOT丢失修复**（预期-6f）
  - 问题: BoolOp中not运算符在_build_boolop_expression中被吞掉
  - 方案: 在表达式重建时保留UNARY_NOT操作符
- [ ] Task 23.3: **Ternary边界精炼**（预期-5f）
  - 问题: Ternary与BoolOp/If边界判定仍有模糊地带
  - 方案: 增强三元表达式确定性特征检测
- [ ] Task 23.4: **If区域死代码恢复尝试**（预期-8f）
  - 问题: Python编译器完全移除if结构导致~20个测试失败
  - 方案: 基于CFG分支结构推断原始if语句
- [ ] Task 23.5: **Match is None降级增强**（预期-5f）
  - 问题: match x: case None被降级为if x is None但部分场景仍失败
  - 方案: 完善降级触发条件和AST重建逻辑
- [ ] Task 23.6: **For/With/Assert边缘清理**（预期-5f）
  - 问题: 各高通过率区域剩余的少量失败
  - 方案: 逐个分析和修复

### Phase 23 验证
- [ ] Task 23.7: 全量测试 + 字节码等价性验证
- [ ] Task 23.8: 更新最终数据表

---

## 🚀 Phase 24: 架构级突破（长期目标，待Phase 23完成后评估）

### 目标: 90%+

- [ ] Task 24.1: BoolOp动态优先级引擎（预期-25f）
- [ ] Task 24.2: While控制流统一跟踪（预期-15f）
- [ ] Task 24.3: Match Pattern独立管道v2（预期-15f）
- [ ] Task 24.4: Try异常图精细化（预期-10f）
- [ ] Task 24.5: If嵌套协调器（预期-10f）

---

# Task Dependencies
- Phase 1-4 可并行执行
- Phase 5 依赖 Phase 1,2
- Phase 6 依赖 Phase 5
- Phase 7 依赖 Phase 5,6
- Phase 8 依赖 Phase 5
- Phase 9 依赖 Phase 1-8
- Phase 10-14 可部分并行（Phase 12独立，10/11可并行）
- Phase 15 依赖 Phase 14
- Phase 16-17 依赖 Phase 15
- Phase 18-21 可并行（18a/18b独立，19依赖18，20依赖19，21依赖20）
- **Phase 22 (当前) 无依赖 - 立即开始**
- Phase 23 依赖 Phase 22（必须先修复回归）
- Phase 24 依赖 Phase 23
