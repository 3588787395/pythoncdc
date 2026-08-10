# Round 67 测试工程师报告：future_position.pyc

## 目标 pyc
- 文件: `future_position.pyc`
- 路径: `F:/Downloads/pythoncdc-main/site-packages/IQEngine/plugins/plugin_system_accounts/position_model/future_position.pyc`
- 函数总数: 72
- 匹配函数: 70
- 不匹配函数: 2
- 成功率: 97.22%

## 不一致函数清单

### 1. _close_holding (orig=365, decomp=390, true_diffs=256)
- **first_diff**: index 78, orig=LOAD_FAST self, decomp=RETURN_VALUE
- **根因**: while 循环退出后，原始字节码有 `JUMP_FORWARD`（跳到 else 分支），反编译产物编译后生成了 `LOAD_CONST None + RETURN_VALUE`（隐式 return None）
- **影响**: while 循环后的 else 分支语句丢失，导致 256 条指令差异

### 2. make_trade (orig=297, decomp=292, true_diffs=33)
- **first_diff**: index 261, orig=LOAD_FAST current_date, decomp=RETURN_VALUE
- **根因**: `elif self.buy_amount - trade_amount != 0:` 分支末尾，原始字节码有 `JUMP_FORWARD`（跳到 else 分支），反编译产物编译后生成了 `LOAD_CONST None + RETURN_VALUE`
- **else 分支缺失语句**: 原始 else 分支有 `self._long_clean_time = current_date` 和 `self._buy_avg_open_price = 0.0`，但反编译产物中这两条语句被错误地放在了内层 if/else 的 else 分支中（lines 307-308）
- **影响**: 33 条指令差异

## 共同模式
两个不一致函数都有相同的根因：
1. **IfRegion else_blocks 错误归因**: 原始字节码中属于外层 else 分支的块被错误归入内层 else 分支
2. **JUMP_FORWARD 连接块被误识别为隐式 return None**: 原始字节码中用于跳过 else 的 `JUMP_FORWARD` 连接块，在反编译产物中被替换为 `LOAD_CONST None + RETURN_VALUE`

## 最小复现实例
已创建 10 个最小复现实例至 `minimal_repros/`:
- repro_01-04: 基础 if/while/else 和 if/return 模式
- repro_05: close_holding 完整模式（if/while/else + if/return）
- repro_06: make_trade 完整模式（if/elif/elif/else with return）
- repro_07-10: 简化变体

## 累计成功率
- 当前 pyc: 97.22% (70/72)
- 累计（预估）: 与上一轮持平（本 pyc 未变）
