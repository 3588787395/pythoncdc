# 区域归约算法全面完善 - 100%反编译成功率

## Why
当前反编译器对 site-packages/ 下 43 个 pyc 文件（219 个函数）存在字节码不一致问题，成功率仅 82.5%（1033/1252 匹配函数）。需要基于区域归约算法系统性修复所有不一致，实现 100% 反编译成功率与字节码完全匹配。

## What Changes
- 基于区域归约算法分析每个失败 pyc 的不一致模式，将反编译逻辑写入识别方法的注释中
- 建立 pyc 文件索引，逐个 pyc 进行测试-修复迭代
- 实现测试工程师 + 修复工程师的双角色迭代工作流
- 每轮至少解决一个 pyc 文件，从最严重（match_rate 最低）的文件开始
- 所有区域类型同样完善，所有方法必须符合区域归约算法
- 禁止跨区域跨层次的启发式规则，禁止破坏算法对嵌套的天然支持
- 禁止修改反编译生成的 OK.py 文件
- 必须用 `scripts/pyc_batch_verify.py` 验证
- 每轮必须提交并 push 到远程

## Impact
- Affected specs: region_analyzer.py（区域识别与归约）、region_ast_generator.py（区域→AST映射）、ast_converter.py（AST转换）、code_generator.py（代码生成）
- Affected code: core/cfg/ 目录下所有模块
- Affected tests: testqouter/、site-packages/ 下 43 个 pyc 文件

## ADDED Requirements

### Requirement: Pyc索引建立与排序
系统 SHALL 从 `site-packages/` 目录扫描所有 pyc 文件，建立索引，按 bytecode_match_rate 从低到高排序，优先修复最严重的文件。

#### Scenario: 索引建立成功
- **WHEN** 启动反编译完善流程
- **THEN** 系统从 pyc_index.json 读取所有 decompile_status != 'ok' 的条目，按 match_rate 升序排列形成待修复队列

### Requirement: 测试工程师角色
测试工程师 SHALL 对每个待修复 pyc 执行反编译验证，分析字节码不一致的具体位置和原因，创建最小复现实例（10+ 个可复现问题的实例）。

#### Scenario: 测试工程师完成分析
- **WHEN** 测试工程师对 pyc 文件执行 `pyc_batch_verify.py single` 验证
- **THEN** 输出字节码 diff 报告，包含 total_functions、matched_functions、mismatches 详情
- **THEN** 对每个 mismatch 函数，标注 orig_count vs decomp_count、jump_diffs、true_diffs、first_diff

### Requirement: 修复工程师角色
修复工程师 SHALL 根据测试工程师的分析结果，依照区域归约算法修改 core/cfg/ 下代码，增强算法通用性。

#### Scenario: 修复工程师完成修复
- **WHEN** 修复工程师根据 mismatch 分析定位到具体区域识别或 AST 生成逻辑问题
- **THEN** 修改 region_analyzer.py 或 region_ast_generator.py 中相应方法
- **THEN** 将反编译逻辑写入识别方法的注释中
- **THEN** 重新运行验证确认 fix 有效

### Requirement: 迭代工作流
系统 SHALL 执行 10 轮测试-修复迭代，每轮包含：测试→分析→修复→验证→提交。

#### Scenario: 单轮迭代完成
- **WHEN** 一轮迭代开始
- **THEN** 测试工程师取一个 pyc 文件进行反编译验证
- **THEN** 分析不一致原因并创建最小复现实例
- **THEN** 修复工程师根据分析完善代码
- **THEN** 验证该 pyc 的 bytecode_match_rate 达到 1.0
- **THEN** 提交并 push 到远程
- **THEN** 进入下一个 pyc 文件

#### Scenario: 单轮必须解决至少一个 pyc
- **WHEN** 一轮迭代中未能使任何 pyc 的 match_rate 达到 1.0
- **THEN** 禁止进入下一轮，必须继续修复直到该 pyc 解决

### Requirement: 区域归约算法一致性
所有区域识别和 AST 生成方法 SHALL 符合区域归约算法原则：

#### Scenario: 算法原则遵守
- **WHEN** 修改区域识别或 AST 生成逻辑
- **THEN** 从最内层到最外层识别区域（归约顺序）
- **THEN** 每个块在任何层级只属于一个区域
- **THEN** 嵌套区域在其父区域中作为单个抽象节点表示
- **THEN** 归约后父区域的 then/else 列表引用子区域的入口
- **THEN** 禁止跨区域跨层次的启发式规则

### Requirement: OK.py 生成与禁止修改
系统 SHALL 在 pyc 同目录下生成同名+OK.py 文件，且禁止修改已生成的反编译文件。

#### Scenario: OK.py 正确生成
- **WHEN** pyc 反编译成功且字节码 100% 匹配
- **THEN** 在 pyc 同目录生成 `<name>OK.py`
- **THEN** 该文件内容为反编译生成的源码，后续轮次禁止修改

### Requirement: 批量回归验证
每轮修复后 SHALL 使用 `scripts/pyc_batch_verify.py batch` 对所有已 ok 的 pyc 进行回归验证。

#### Scenario: 回归验证通过
- **WHEN** 修复工程师完成代码修改
- **THEN** 运行 `pyc_batch_verify.py batch` 验证所有 pyc
- **THEN** 确认已 ok 的 pyc 仍然 ok（无回归）
- **THEN** 确认新修复的 pyc 变为 ok

### Requirement: 每轮提交并 Push
每轮迭代完成后 SHALL 提交更改并 push 到远程仓库。

#### Scenario: 提交推送成功
- **WHEN** 一轮迭代完成（至少一个 pyc 解决）
- **THEN** git add 相关修改文件
- **THEN** git commit 并 push 到 origin

## MODIFIED Requirements

### Requirement: region_analyzer.py 区域识别方法注释
每个区域识别方法 SHALL 在其注释中记录反编译逻辑推导过程，包括：输入 CFG 模式、识别条件、归约规则、AST 映射。

## REMOVED Requirements
(None)
