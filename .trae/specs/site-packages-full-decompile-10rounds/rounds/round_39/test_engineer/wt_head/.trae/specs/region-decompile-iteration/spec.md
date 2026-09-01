# 规格说明：区域归约算法驱动的反编译器迭代完善

## 目标
将 pythoncdc 反编译器的字节码一致率从 92.4% 提升到 100%，使所有 547 个 pyc 文件反编译后字节码完全匹配。

## 背景
- 当前状态：402 个已索引 pyc 文件中，262 个 100% 匹配，136 个部分匹配，4 个 0% 匹配
- 平均匹配率：92.4%
- 反编译器基于区域归约算法（No More Gotos 论文），核心模块：
  - `core/cfg/region_analyzer.py` (21218行) — 区域识别与归约
  - `core/cfg/region_ast_generator.py` (36852行) — 区域→AST映射
  - `core/cfg/dominator_analyzer.py` — 支配树与循环检测
- 区域类型：BASIC, SEQUENCE, IF, IF_THEN, IF_THEN_ELSE, IF_ELIF_CHAIN, WHILE_LOOP, FOR_LOOP, TRY_EXCEPT, TRY_FINALLY, WITH, MATCH, ASSERT, BREAK, CONTINUE, PASS, RETURN, BOOL_OP, TERNARY

## 方案
采用双工程师迭代模式：
1. **测试工程师**：选取未通过 pyc 文件 → 反编译 → 验证字节码 → 分析不一致 → 提取最小复现实例
2. **修复工程师**：根据分析结果 → 定位 region_analyzer/region_ast_generator 中的问题 → 按区域归约算法修正 → 回归验证

每轮至少解决一个 pyc 文件，未解决不进入下一轮。

## 范围
- 主要修改：`core/cfg/region_analyzer.py`, `core/cfg/region_ast_generator.py`
- 可能修改：`core/cfg/dominator_analyzer.py`, `core/cfg/basic_block.py`
- 禁止修改：反编译生成的 OK.py 文件

## 约束
1. 必须遵循区域归约算法，禁止启发式补丁
2. 禁止跨区域跨层次的规则
3. 每个块在任何层级只属于一个区域
4. 嵌套区域在父区域中作为单个抽象节点
5. 单向数据流，不回溯修正
6. 所有命令执行不超过 300 秒
7. 每轮必须 git commit + push
8. 禁止修改反编译生成的文件

## 验收标准
- 所有 547 个 pyc 文件反编译成功
- 每个文件在同目录下生成同名+OK的py文件
- 字节码一致率 100%
- 成功率 100%
