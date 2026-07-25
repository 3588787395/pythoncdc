# 修复实施报告 — Pass 1 / WITH 区域

## 概述
依照架构工程师分析报告实施 3 项反模式消除修复。修复 1 在实施中发现架构师方案（exc_target 上界）会触发回归，改用行为等价的方式消除 magic number。修复 2、3 按原方案实施。所有修改通过编译检查与 WITH/LOOP/TRY 三组回归测试（均达基线）。

## 修改文件
- `/workspace/core/cfg/region_analyzer.py`
- `/workspace/core/cfg/region_ast_generator.py`

## 修复 1 — 消除 `_collect_normal_exit_cleanup` 的 magic number（偏离原方案，行为等价重构）

### 原方案与回归发现
架构师建议将 `_collect_with_cleanup_blocks` 已计算的 `exc_target`（WITH_EXCEPT_START 偏移）作为参数传入 `_collect_normal_exit_cleanup`，把上界 `block.start_offset + 1000` 改为 `exc_target`。

按此实施后触发回归：
- `test_w058.py::TestW058::test_decompile` 失败（`async def f(): async with ctx as v: x = v`）
- 错误：`嵌套code object不匹配 (指令1): 指令数不匹配: 43 vs 41`（多 2 条指令）

### 根因分析（exc_target 不是语义上界）
通过反汇编 test_w058 确认字节码布局：
```
36  STORE_FAST x           # body_end
38  LOAD_CONST None        # __aexit__ setup
...
62  SEND/YIELD/RESUME      # __aexit__ await loop
70  POP_TOP/LOAD_CONST/RETURN_VALUE
76  PUSH_EXC_INFO          # exc_target = 76（异常处理器 START）
78  WITH_EXCEPT_START
...
92  POP_JUMP_FORWARD_IF_TRUE / RERAISE   # 异常处理器尾部（normal successor）
96  COPY/POP_EXCEPT/RERAISE
102 POP_TOP/.../RETURN_VALUE
```
- `exc_target=76` 是异常处理器**起始**，处理器代码延伸到 112。
- 异常处理器 BFS（`_collect_with_cleanup_blocks`）只跟随 WITH_EXCEPT_START 后继与 exception_successors，**漏掉 normal-successor 尾块**（offset 92）。
- 原 `+1000` 上界把这些漏掉的尾块作为 normal_exit_cleanup 收集（抑制生成）。
- 改用 `exc_target` 上界后，offset>=76 的块不在 [body_end, exc_target) 内 → 不再收集 → 作为代码生成 → 多 2 条指令。

### +1000 实为 no-op 的证明
原代码：
```python
in_range = any(
    body_end <= instr.offset < block.start_offset + 1000
    for instr in block.instructions
)
if not in_range:
    continue
```
- 经上文 `if block.start_offset < body_end: continue` 后，必有 `block.start_offset >= body_end`。
- 块首指令 offset >= block.start_offset >= body_end → `body_end <= instr.offset` 恒真。
- 单基本块指令跨度远小于 1000 字节 → `instr.offset < block.start_offset + 1000` 恒真。
- 故对非空块 `in_range` 恒为 True；对空块 `any(...)` 为 False。
- 真正的上界由上文 `BEFORE_WITH/BEFORE_ASYNC_WITH` break 与下文 `has_user_code` 过滤共同提供。

### 实施方式（行为等价）
将 no-op 的 `in_range` 检查替换为等价的空块跳过：
```python
# 上界由上文 BEFORE_WITH break 与下方 has_user_code 过滤共同确定；
# 原硬编码常量上界（block.start_offset 加固定字节数）是恒为真的 no-op：
# block.start_offset >= body_end 已保证首指令 offset >= body_end，
# 且单基本块指令跨度远小于该固定字节数。此处仅保留空块跳过语义。
if not block.instructions:
    continue
```
- 不新增 `exc_target` 参数（用作上界会回归；作为未使用参数是 code smell）。
- `_collect_with_cleanup_blocks` 与 `_collect_normal_exit_cleanup` 签名保持不变。
- 行为等价：非空块继续走 has_user_code 过滤；空块跳过（与原 `any(...)`=False 一致）。

### 验证
- WITH: 80p/0f/80 ✓（回归消除，恢复基线）
- LOOP: 79p/0f/79 ✓
- TRY: 80p/0f/80 ✓

## 修复 2 — 抽取 ASYNC_WITH_SEND_LOOP_OPS 常量 + 谓词方法

### 实施
1. 模块级常量（region_ast_generator.py L88）：
```python
ASYNC_WITH_SEND_LOOP_OPS = frozenset({
    'SEND', 'YIELD_VALUE', 'RESUME',
    'JUMP_BACKWARD_NO_INTERRUPT', 'NOP',
})
```
2. 谓词方法（L14163）：
```python
def _is_async_with_send_loop(self, loop_region, with_region) -> bool:
    if not isinstance(with_region, WithRegion):
        return False
    if not getattr(with_region, 'is_async', False):
        return False
    if loop_region.entry is None:
        return False
    return all(i.opname in ASYNC_WITH_SEND_LOOP_OPS for i in loop_region.entry.instructions)
```
3. 替换 5 处 inline 5-元组字面量（任务列出 4 处 L14323/14329/14344/14953；额外发现 L1985 同一 5-元组 DRY 违反，一并重构）：
   - L1985（`_generate_region` 调度器：LoopRegion.parent 为 WithRegion）
   - L14346、L14352、L14367、L14976（`_generate_with` 内部）
   - L14346/L14352 保留额外 `BlockRole.LOOP_ELSE` 判据（谓词未覆盖）
   - L14976 WithRegion 为 `child.parent`（非 `region`）

### 行为等价性说明
- L1985、L14976 原本未检查 `is_async`；谓词新增该检查。等价因为 SEND/YIELD_VALUE/RESUME/JUMP_BACKWARD_NO_INTERRUPT 指令序列为 async 专属，sync WithRegion 的子 LoopRegion 不可能仅由这些 opname 组成。
- 纯重构，无行为变化。

### 未触及的 2 处 inline（不同 opname 集合，超范围）
- L4294、L10311：使用 **6-元组**（含 `'CACHE'`），分别在 loop back-edge 处理与 await SEND loop 检测中。语义不同于 async-with 5-元组；改用 5-元组常量会改变 CACHE 处理行为，违反"行为必须等价"。保持原样。

## 修复 3 — 修正 `_identify_with_regions` docstring 归约顺序

region_analyzer.py L7174：
- 旧：`归约阶段: Phase 1（在 TRY 之后，LOOP 之前）`
- 新：`归约阶段: Phase 1（在 TRY、LOOP 之后，MATCH/ASSERT 之前；优先级第三档）`
- 补注：async-with 的 SEND/YIELD 协程恢复循环因此会被 `_identify_loop_regions` 先识别为 LoopRegion，目前由 `_generate_with` 内的 ASYNC_WITH_SEND_LOOP_OPS 判据 patch 处理（待后续在归约期消除）。

## 反模式自检

| 检查 | 期望 | 实际 | 结果 |
|---|---|---|---|
| `grep -n "+ 1000\|+1000" core/cfg/region_analyzer.py` | 0 | 0 | ✓ magic number 消除 |
| `grep -n "ASYNC_WITH_SEND_LOOP_OPS" region_ast_generator.py` | 常量定义 + 谓词引用 | L88 定义 + L14176 谓词引用 | ✓ |
| `grep -c "'SEND', 'YIELD_VALUE', 'RESUME'" region_ast_generator.py` | 0 | 3 | ⚠ 见下 |
| 禁止前缀方法名 | 无 _fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_ | 仅 `_is_async_with_send_loop`（任务明确合规） | ✓ |
| 新增后处理补丁 | 无 | 无 | ✓ |
| 硬编码深度上限 | 无 | 无 | ✓ |

### 关于 inline 字面量 count=3 的说明
任务自检期望 0，实际为 3：
- **L89**：`ASYNC_WITH_SEND_LOOP_OPS` 常量定义本身（集中定义点，**期望存在**）。
- **L4294、L10311**：使用 6-元组 `('SEND', 'YIELD_VALUE', 'RESUME', 'JUMP_BACKWARD_NO_INTERRUPT', 'NOP', 'CACHE')`，分别在 async for/with 挂起协议子循环（loop back-edge 处理）与 await SEND loop 检测中。这是**不同的 opname 集合**（多 'CACHE'）与**不同的语义上下文**（async-for/await，非 async-with），不在本次 5-元组重构范围。改用 5-元组会改变 CACHE 处理 → 违反行为等价。

5-元组 inline 字面量（任务目标）已**全部消除**（原 4 处 + L1985 共 5 处全部改用谓词）。

## 回归测试结果
| Region | 基线 | 实际 | 时长 |
|---|---|---|---|
| WITH | 80p/0f/80 | 80p/0f/80 | 2.4s |
| LOOP | 79p/0f/79 | 79p/0f/79 | 2.3s |
| TRY | 80p/0f/80 | 80p/0f/80 | 2.5s |

编译检查：`python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"` → IMPORT OK ✓

## 与原方案的偏差
1. **修复 1 偏离**：原方案用 exc_target 作上界。实施后 test_w058 回归（43 vs 41 指令）。根因：exc_target 是异常处理器**起始**而非**结束**，处理器尾块（normal successor，BFS 漏收）原由 +1000 no-op 兜底收集。改用行为等价方式：识别 +1000 为 no-op（非空块恒真），替换为 `if not block.instructions: continue`，依赖 BEFORE_WITH break + has_user_code 作真上界。magic number 已消除，行为等价。
2. **修复 2 超出列出的 4 处**：额外重构 L1985（同一 5-元组 DRY 违反，`_generate_region` 调度器层）。L4294/L10311（6-元组含 CACHE）未触及（不同 opname 集合，行为等价约束）。

## 未 commit / push（由主调度器统一）
