# Pass 9 TRY 修复报告

## 修复内容

### Fix 1: 同步 `_identify_try_except_regions` docstring「识别策略」与实际控制流的第三路 fallback 分支

**问题位置**：`/workspace/core/cfg/region_analyzer.py:4724-4728`
（`_identify_try_except_regions` docstring 第 1 节「算法描述 / 识别策略」段落）

**问题根因**（与 Pass8-IF 同型——docstring 与实际控制流不同步）：

`_identify_try_except_regions` docstring 第 1 节「识别策略」段落原文：

```
1. 算法描述（基于"No More Gotos"论文）
   - 归约阶段: Phase 1（最先识别，优先级最高；TRY > LOOP > WITH > MATCH > ASSERT）
   - 识别策略: 基于 CPython 3.11+ 异常表（exception table）的
     (start, end, target, depth) 条目定位 try 范围与 handler 入口。
     通过 handler 入口首指令（PUSH_EXC_INFO / WITH_EXCEPT_START）分类 handler 类型。
```

仅描述主分类路径（首指令 ∈ {PUSH_EXC_INFO, WITH_EXCEPT_START}）。实际
inner_handler_indices 预扫描循环（L4810-L4857）中存在第三路 fallback 分支：

```python
for i, info in enumerate(handler_infos):
    handler_block = self.cfg.get_block_by_offset(info['handler_start'])
    if handler_block and handler_block.instructions:
        first_instr = handler_block.instructions[0]
        if first_instr.opname not in ('PUSH_EXC_INFO', 'WITH_EXCEPT_START'):
            has_copy = any(instr.opname == 'COPY' for instr in handler_block.instructions)
            has_pop_except = any(instr.opname == 'POP_EXCEPT' for instr in handler_block.instructions)
            has_reraise = any(instr.opname == 'RERAISE' for instr in handler_block.instructions)
            if has_copy and has_pop_except and has_reraise:
                has_bare_except_entry = False
                for blk in self.cfg.blocks.values():
                    ...
                if not has_bare_except_entry:
                    inner_handler_indices.add(i)
                    continue
```

即当 handler 首指令**不**属于 {PUSH_EXC_INFO, WITH_EXCEPT_START} 时，检测
handler_block 是否含 COPY + POP_EXCEPT + RERAISE 三联（try-finally cleanup 块
特征）；若含且无 bare_except_entry（无 PUSH_EXC_INFO 内层 handler），则将该
handler 标记为 inner_handler_indices（由外层 try-finally 拥有，不独立建
TryExceptRegion）。

原表述未提及此 fallback 分支，可能误导读者认为 handler 分类仅基于首指令两 opname。

**修复策略**（与 Pass8-IF 同型——仅 docstring 文本同步，不改控制流）：

在 docstring 第 1 节「识别策略」段落后追加 `[Pass9-TRY]` 段落，补记上述第三路
fallback 分支的存在与触发条件（首指令非 PUSH_EXC_INFO/WITH_EXCEPT_START + 含
COPY+POP_EXCEPT+RERAISE 三联 + 无 bare_except_entry）。不重写「识别策略」行
（避免递归漂移，与 Pass8-IF 改用 grep 验证方式描述同型保守思路一致）。

控制流不变，仅 docstring 文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py TRY
```
**结果**：`80 0 0 80 2.6 TRY files=80` —— 与基线一致（80 passed, 0 failed, 0 errors）。
无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅 docstring 文本同步） |
| 测试文件修改 | 未修改任何测试文件 |
| docstring 与实际控制流不同步（与 Pass8-IF 同型） | **已同步**（补记第三路 fallback 分支：首指令非 PUSH_EXC_INFO/WITH_EXCEPT_START + COPY+POP_EXCEPT+RERAISE 三联） |

## 未完成项

1. **TODO[pass2-CC] _try_build_* 三连 patch chain**（`_try_build_walrus_chained_compare`
   / `_try_build_literal_middle_chained_compare` / `_try_build_method_call_chained_compare`）
   仍挂账 Pass 3+，需统一操作数提取路径后删除。
2. **`_generate_try_body` 4 并列启发式**（is_child / is_in_try_blocks / is_before_try_start
   / handler_in_range）仍挂账 Pass 3+，待统一为区间包含判据。
3. **「100% 通过率」表述**：Pass7-TRY 已在 _identify_try_except_regions docstring
   追加 [Pass7-TRY] 校正段落，与 _generate_try docstring [Pass4-TRY] 段落口径一致。
   后续若实施「彻底删除原表述」需同步两处。
4. **「识别策略」表述未重写**：本轮仅追加 [Pass9-TRY] 补记段落，保留原表述作
   历史追溯。后续若实施「彻底重写为三路分类口径」需同步两处（识别策略行 + Step 1 行）。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_identify_try_except_regions` docstring 第 1 节「识别策略」段落后追加 [Pass9-TRY] 段落，补记第三路 fallback 分支：首指令非 PUSH_EXC_INFO/WITH_EXCEPT_START + COPY+POP_EXCEPT+RERAISE 三联）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/TRY/pass_09/fix_report.md`（本报告）
