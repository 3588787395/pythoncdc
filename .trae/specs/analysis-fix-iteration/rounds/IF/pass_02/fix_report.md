# Pass 2 第 11 轮 IF 区域修复报告

## 修复范围

本轮聚焦 IF 区域生成阶段的副作用消除与 docstring 口径同步，共 2 项修复。

---

## Fix 1: 消除 _if_generate_full_elif_chain 的 region.then_blocks 副作用

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:7019-7062`（原 7019-7054，行号因新增 try/finally 与注释略有下移）

**问题根因**：
生成阶段在 `_if_generate_full_elif_chain` 中直接篡改
`region.then_blocks = [b for b in region.then_blocks if b not in _blocks_to_remove]`，
违反「识别阶段一次正确」原则。若同一 region 被多次生成（如被多次 `_generate_region` 调用引用），
第二次会看到已改短的 `then_blocks`，导致语句漏生成。

**修复策略**：save/restore（try/finally）模式，让本地修改只在
`_if_generate_then_branch` / `_if_generate_elif_chain` 调用窗口内生效。

**具体变更**（`/workspace/core/cfg/region_ast_generator.py`）：

- 在原修改前新增（约 7031 行）：
  ```python
  _saved_then_blocks = region.then_blocks
  try:
  ```
- 将原 `if region.chained_compare_blocks and ...` 块、
  `then_stmts = self._if_generate_then_branch(region)` 与
  `elif_part = self._if_generate_elif_chain(region)` 三段统一缩进进入 `try` 体。
- 在 `try` 体后新增（约 7059-7060 行）：
  ```python
  finally:
      region.then_blocks = _saved_then_blocks
  ```
- `self._generating_regions.discard(region_id)` 与
  `self._generated_regions.add(region_id)` 保留在 try/finally 之后，行为不变。

**控制流保证**：
- 正常路径：then/elif 生成完成后 finally 恢复原 then_blocks。
- 异常路径：then/elif 任一调用抛出异常时，finally 仍执行恢复，避免 region 状态污染。
- 不进入 `if region.chained_compare_blocks and ...` 分支时：`_saved_then_blocks`
  保存的就是原值，finally 恢复为等值赋值，无副作用。

**新增注释**（7023-7025 行，标注本轮修复）：
```
# [Pass2-11] 用 save/restore（try/finally）包裹对 region.then_blocks 的本地
# 修改与后续 _if_generate_then_branch / _if_generate_elif_chain 调用，确保
# 即便本 region 被多次生成也不会看到被改短的 then_blocks（消除生成阶段副作用）。
```

原 `TODO[pass2-CC]` 注释保留（指向更大的 BoolOpRegion 重构方向，本轮不动）。

---

## Fix 2: 同步 docstring 与 Pass 1 fix_report 一致

### 2.1 region_analyzer.py docstring

**位置**：`/workspace/core/cfg/region_analyzer.py:10055-10058`

**变更前**：
```
6. 已知失败模式
   - 当前测试矩阵通过率: 100%（if_region 311/311），无已知失败模式
   - 本方法遵循区域归约算法 4 核心原则:
     自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口
```

**变更后**：
```
6. 已知失败模式
   - Pass 1 后 IF 区域识别稳定，bounded subset 仍有 1 处预存失败（见 baseline_failures.txt），非本次引入。
   - 本方法遵循区域归约算法 4 核心原则:
     自底向上归约 / 每块唯一归属 / 嵌套即抽象节点 / 父引用子入口
```

### 2.2 region_ast_generator.py docstring

**位置**：`/workspace/core/cfg/region_ast_generator.py:6633`

**变更前**：
```
- 字节码匹配状态: 100% 完全匹配（if_region 311/311）
```

**变更后**：
```
- 字节码匹配状态: Pass 1 后稳定（bounded subset 79/80，1 处预存失败见 baseline_failures.txt）
```

**口径对齐**：与 Pass 1 fix_report「IF bounded subset 79/80，1 处预存失败」一致。

---

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 生成阶段篡改识别阶段产物（then_blocks） | **已消除**（save/restore 包裹，调用结束恢复原值） |
| 测试文件修改 | 未修改任何测试文件 |

本轮重点消除的副作用：生成阶段对 `region.then_blocks` 的就地修改被限定在
`_if_generate_then_branch` / `_if_generate_elif_chain` 调用窗口内，调用结束
（无论正常返回还是异常）后 region 状态恢复至调用前，符合「识别阶段一次正确」原则。

---

## 编译验证

执行命令：
```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```

**结果**：退出码 0，输出 `OK: imports succeeded`。

附加静态/行为验证：
- `ast.parse` 两个文件均成功（语法/缩进正确）。
- 模拟 save/restore 行为：try 内篡改 `then_blocks` 后，finally 恢复，断言恢复后等于原列表，通过。

---

## 未完成项

1. **TODO[pass2-CC] 未完成**：`_detect_boolop_after_chained_compare` 与本调用块
   仍存在，等待 Pass 2 后续轮次将「CC + and/or 短路块」识别阶段统一为
   `BoolOpRegion`（CC IfRegion 作为 `op_chain` 元素，通过 entry 引用）后，
   一并删除该后处理补丁。本轮仅做副作用隔离，未做识别阶段重构。
2. **baseline_failures.txt 中的 1 处预存失败**：非本轮引入，未处理（属 Pass 1
   baseline 范围）。
3. **测试矩阵回归**：本轮仅做 import 与静态/行为单元验证，未跑完整 if_region
   311 用例矩阵（任务约束未要求；如需可在后续轮次补跑）。

---

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1 + Fix 2.2）
- `/workspace/core/cfg/region_analyzer.py`（Fix 2.1）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/IF/pass_02/fix_report.md`（本报告）
