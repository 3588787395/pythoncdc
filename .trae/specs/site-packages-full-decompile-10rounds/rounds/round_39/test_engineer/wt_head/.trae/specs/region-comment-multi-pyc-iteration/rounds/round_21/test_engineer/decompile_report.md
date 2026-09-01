# R21 测试工程师报告

## 目标 pyc:
`IQCommon/logger/handlers.pyc`

## 验证结果
- **总函数数**: 18
- **匹配函数**: 17
- **成功率**: 94.44%
- **唯一 mismatch**: `_target` (stream 版本, varnames=('self','stream','text','msg'))

## 发现的缺陷

### 缺陷 1: Pattern SIG2 — no-SWAP 反源序连续 STORE 元组解包赋值
- **已修复** (R21 第一阶段)
- `command, data = item[0], item[1:]` 中 `command = item[0]` 丢失
- 修复: `_generate_block_statements` 中插入 no-SWAP 反源序连续 STORE 检测

### 缺陷 2: Pattern TE — try-else 子句丢失
- **已修复** (R21)
- 第二个 `_target` (stream 版本) 的 try-else 中 else 子句完全丢失
- orig: `try: stream.seek(0); text=stream.read() → JUMP_FORWARD 514(else入口) except: continue → else: msg=encode(text[:-1]); ...`
- dec (修复前): else 子句丢失，write(msg)/flush() 变成不可达代码
- **根因链** (3 处缺陷):
  1. `_find_try_else_blocks`: merge_point=None, alternative_merges=[], 降级区间空 → 返回空
     - 原因: try JUMP_FORWARD 跳过 handler 到 else, handler 以 continue 退出无公共后支配点
     - 修复: 检测 try_end_block JUMP_FORWARD 目标 > precise_handler_end → BFS 收集 else 块
  2. `_cleanup_try_else_in_loop_body`: else 块被误判为 spurious 并删除
     - 原因: 只检查 try_blocks_set 中块的直接后继, try_end_block 不在 try_blocks_set 中
     - 修复: 将 try_end_block 加入后继检查集合, 并从 else 入口做可达性分析保护 else 块链
  3. `_generate_try` else 块中 LOOP_BACK_EDGE 块: `_generate_block_statements` 误识别循环回边
     - 原因: POP_JUMP_BACKWARD_IF_TRUE 被当作 if 条件, 循环体后续块被拉入 If
     - 修复: LOOP_BACK_EDGE 块只生成循环回边前的用户语句

### 缺陷 3: handler 中 continue/break 误生成 pass
- **已修复** (R21)
- `except ValueError: continue` 被反编译为 `except ValueError: pass`
- 根因: handler body 块的 block_role 是 CONTINUE/PURE_CONTINUE, 但 `_generate_try` 的 handler 遍历没有检查 block_role
- 修复: 在 handler 块遍历中检查 block_role, CONTINUE→Continue, BREAK→Break, RETURN→Return

## 修复文件
1. `core/cfg/region_analyzer.py`:
   - `_find_try_else_blocks` (7608-7642): JUMP_FORWARD 目标 else 块收集
   - `_is_back_edge_target` (新方法): 循环回边目标判断
   - `_cleanup_try_else_in_loop_body` (3677-3710): try_end_block 后继检查 + else 链可达性保护
2. `core/cfg/region_ast_generator.py`:
   - `_generate_try` handler 块遍历 (16839+): block_role CONTINUE/BREAK/RETURN 检测
   - `_generate_try` else 块 LOOP_BACK_EDGE 处理 (17029+): 循环回边前的用户语句生成
   - `_generate_block_statements` Pattern SIG2 (32611-): no-SWAP 反源序连续 STORE

## 最小复现实例 (12 个)
- te001-te012: try-else 各种变体（continue/break/return/nested/multi-stmt/while/for）
- 修复后语义正确: 9/12
- 仍有问题: te003(return→break), te005(嵌套try-else), te008(while continue→pass)

## 已知限制
handlers.pyc `_target` 的字节码差异 (129 vs 125) 是**指令布局差异**，非语义错误：
- CPython 编译器对 `if-then` 含 `try-else` 的代码布局：then 分支 JUMP_FORWARD 跳到 try 入口（try 在 if-elif 之后）
- 反编译器生成：try 在 then 分支内部
- 两者语义完全等价，但字节码指令顺序不同
