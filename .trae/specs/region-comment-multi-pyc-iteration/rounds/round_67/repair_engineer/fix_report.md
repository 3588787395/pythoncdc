# Round 67 修复工程师报告

## 修复目标
- pyc: `trade.pyc` (95.65%, 1 mismatch: `create_trade`)
- 同时分析: `future_position.pyc` (97.22%, 2 mismatches)

## 修复点

### 1. BoolOpRegion STORE_ATTR 赋值检测 (region_ast_generator.py)
- **位置**: `_generate_boolop` 方法，line ~23254
- **问题**: 当 BoolOpRegion 的 `merge_block` 包含 `STORE_ATTR`（如 `trade._calendar_dt = calendar_dt or env.calendar_dt`）时，`value_target` 为 None，导致表达式被生成为裸 `Expr`（带 `POP_TOP`），而非 `Assign`。
- **修复**: 在 `value_target` 检查之前，新增 `STORE_ATTR` 检测路径。当 `value_target` 为 None 且 `merge_block` 包含 `STORE_ATTR` 时，从 `STORE_ATTR` 前的指令重建对象表达式，生成 `Assign(targets=[Attribute(...)], value=BoolOp(...))`。
- **算法依据**: 区域归约算法原则 4（入口引用语义）—— BoolOpRegion 的 merge_block 消费短路表达式结果，`STORE_ATTR` 是消费点。
- **效果**: `trade.pyc` 的 `create_trade` 函数现在正确生成 `trade._calendar_dt = calendar_dt or env.calendar_dt`（之前缺失）。`true_diffs` 从 55 降至 52。

### 2. future_position.pyc 分析（未实施代码修复）
- `_close_holding` 和 `make_trade` 的不一致根因：IfRegion else_blocks 错误归因，导致 else 分支缺少语句，`JUMP_FORWARD` 被替换为 `LOAD_CONST None + RETURN_VALUE`。
- 这是深层结构性问题，需要修改 region_analyzer 的 else_blocks 识别逻辑，留待后续轮次修复。

### 3. base.py 归一化尝试（已回滚）
- 尝试在 `_filter_noise_instrs` 中过滤中间 `LOAD_CONST None + RETURN_VALUE`，但测试结果显示 `true_diffs` 未改善，已回滚。

## 回归测试
- 导入测试: `import core.cfg.region_analyzer; import core.cfg.region_ast_generator` → OK
- trade.pyc: 95.65% → 95.65% (持平，create_trade 仍 1 mismatch，但 true_diffs 从 55 降至 52)
- quotation.pyc 回归: 待验证

## 残留不一致
- trade.pyc `create_trade`: 52 true_diffs（第二个 `or` 表达式及后续赋值仍缺失，根因是 merge_block 被标记为 generated 后剩余指令不再处理）
- future_position.pyc: 2 mismatches（深层结构性问题）
