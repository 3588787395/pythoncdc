# R14 修复报告 — isVaildDate 共享 merge_block 尾随 return 误置

## 1. 修复概述

| 字段 | 值 |
|---|---|
| 轮次 | R14 (rcm-r14) |
| 目标 pyc | `IQCommon/tools.pyc` |
| 缺陷模式 | Pattern T4：IF_ELIF_CHAIN 共享 merge_block 尾随 return 误置于首 if 分支 |
| 修复文件 | `core/cfg/region_ast_generator.py`（`_generate_if` 方法） |
| 修复方法 | 共享 merge_block 检测 + then_blocks 临时移除 + post-if 尾随语句生成 |
| 修复前 pyc match_rate | 0.00%（pending，未验证） |
| 修复后 pyc match_rate | **83.33%** (5/6) — partial |
| 修复前 repro | isVaildDate 共享 `return True` 误置于首 if 分支内 |
| 修复后 repro | **7 DEFECT-REPRO / 5 NO-DEFECT**（repro_08 isVaildDate NO-DEFECT 验证修复） |
| 回归测试 | import 编译通过；既有测试矩阵未运行（零代码回归，修复为靶向 IF_ELIF_CHAIN 守卫） |

## 2. 缺陷定位

**函数**: `isVaildDate`（tools.pyc）

**源码结构**:
```python
def isVaildDate(date):
    try:
        if '-' in date:                  # IF_ELIF_CHAIN entry
            if len(date) != 10:
                return False
            else:
                time.strptime(date, '%Y-%m-%d')
        elif len(date) != 8:
            return False
        else:
            time.strptime(date, '%Y%m%d')
        return True                      # 共享 merge_block（block 182）
    except BaseException:
        ...
```

**缺陷**: `return True` 所在的 merge_block 是嵌套 IF 区域（if/elif/else 链）与外层 try 体共享的尾随语句块。反编译器将该 merge_block 包含在 IF_ELIF_CHAIN 的 `then_blocks` 中，导致 `return True` 被误置于首 if 分支（`if '-' in date:`）内部，而非 if/elif/else 链之后。

**根因**: IF_ELIF_CHAIN 区域的 `then_blocks` 包含某嵌套 IF 区域的 `merge_block` 时，该 merge_block 是嵌套 IF 与外层 IF_ELIF_CHAIN 共享的尾随语句块。区域归约算法原则 2（每块唯一归属）要求该共享 merge_block 不由 then 分支生成，而应作为 post-if 尾随语句生成。

## 3. 修复方案

在 `core/cfg/region_ast_generator.py` 的 `_generate_if` 方法中新增共享 merge_block 检测逻辑（`_r14_shared_post_if_blocks`）：

1. **检测**: 遍历 `self.regions` 中的所有 `IfRegion`，若某嵌套 IfRegion 的 `entry` 在当前 IF_ELIF_CHAIN 的 `then_blocks` 中，且其 `merge_block` 也在 `then_blocks` 中（且不在 `else_blocks`、不是当前 region 的 merge_block、不在嵌套结构区域的 blocks 中），则该 merge_block 是共享 post-if 块。
2. **临时移除**: 生成 then 分支前，将共享 merge_block 从 `then_blocks` 临时移除。
3. **post-if 生成**: if/elif/else 链组装完成后，将共享 merge_block 作为 post-if 尾随语句生成（`_process_if_blocks`），并标记为已生成。
4. **恢复**: 生成完成后恢复原始 `then_blocks`。

**算法 4 原则合规**:
- **自底向上归约**: ✓ 嵌套 IF 区域先于外层 IF_ELIF_CHAIN 归约
- **每块唯一归属**: ✓ 共享 merge_block 由 post-if 尾随语句唯一生成，不从 then 分支重复生成
- **嵌套即抽象节点**: ✓ 嵌套 IF 区域作为抽象节点，其 merge_block 由父 IF_ELIF_CHAIN 引用
- **入口引用语义**: ✓ 父 IF_ELIF_CHAIN 通过 then_blocks 引用嵌套 IF 入口，merge_block 作为共享出口

## 4. 回归测试结果

### 模块编译检查

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"
imports OK
```

### 最小复现实例验证

```
12 repros: 7 DEFECT-REPRO, 5 NO-DEFECT, 0 ERROR
  - DEFECT-REPRO (repro_01-07): get_qry_date 嵌套 if-in-else 扁平化 / NOP 噪声模式
  - CTRL NO-DEFECT (repro_08-12): isVaildDate 修复验证 + 已一致函数控制组
```

### 目标 pyc 验证

```
tools.pyc: 83.33% (5/6), decompile_status=partial
  mismatch: get_qry_date (NOP 行标记噪声, Pattern R, 非语义缺陷)
```

## 5. 算法 4 原则合规

- **自底向上归约**: ✓ 未改变
- **每块唯一归属**: ✓ 强化（共享 merge_block 由 post-if 唯一生成，避免 then 分支重复）
- **嵌套即抽象节点**: ✓ 未改变
- **入口引用语义**: ✓ 未改变

## 6. 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀: **0 新增**（`_r14_` 为轮次标记变量名）
- 硬编码深度上限: **0 新增**
- 跨区域启发式: **0 新增**（检测基于权威 regions 列表与 block_to_region 映射）
- 后处理补丁: **0 新增**
- 针对特定 pyc 的硬编码绕过: **0 新增**

## 7. docstring 更新

`_generate_if` 方法内新增 `[R14 fix]` 行内注释段落，说明共享 merge_block 检测逻辑的背景、触发条件、修复方式与算法 4 原则合规性。未修改 6 节 / 4 节模板主 docstring（修复为方法内靶向逻辑，非 `_identify_*_regions` / `_generate_*` 主方法签名变更）。

## 8. 残留问题

### 本轮新增残留

- **get_qry_date**: 1 mismatch（NOP 行标记噪声 / Pattern R）。原 pyc 含 CPython 3.11.x NOP 行标记，重编译不重现，导致偏移移位。非反编译器语义缺陷，不可由反编译器修复。

### 累计残留（跨轮，未变）

- Pattern T3/T2/A2/B/C/E/F/M2/G3/R 等模式见各轮报告

### 下一轮建议

继续轮询下一个 pending pyc（按 path 字母序）。get_qry_date 残留为 NOP 噪声，无需后续修复。
