# Pass 8 SEQ (Sequence) 修复报告

## 修复内容

### Fix 1: 同步 `_generate_basic_region` docstring 中「字节码一致性状态：截至 Pass 03」表述

**问题位置**：`/workspace/core/cfg/region_ast_generator.py:25130-25147`
（`_generate_basic_region` 方法 docstring「字节码一致性约束」节末段追加 [Pass8-SEQ] 校正段落）

**问题根因**（与 Pass3-BOOLOP / Pass8-TERNARY 在 `_generate_boolop` / `_generate_ternary`
docstring 同步测试状态同型「过时时点表述」）：

`_generate_basic_region` docstring「字节码一致性约束」节末段原文：
```
- 字节码一致性状态：SEQ 套件存在已知失败（截至 Pass 03: 127p/10f/137，
  有界子集 80 文件）。失败用例分两类：(a) L1_basic 子目录的 NameError
  类失败（test 侧引用未定义名，属测试基础设施问题）；(b)
  basic/test_b23yieldfrom_complex 的嵌套 code object 指令数不匹配。
  原 docstring 声称「100% 完全匹配（basic 122/122），无遗留」与实测矛盾，已同步。
```

其中「截至 Pass 03: 127p/10f/137」表述仅引用 Pass 03 时点状态、未说明 Pass 4-7 期间
无回归变化，可能误读为「Pass 03 后状态已变」。

**对称缺失**（Pass3-BOOLOP 已在 `_generate_boolop` docstring 同步同型问题；
Pass8-TERNARY 已在 `_generate_ternary` docstring 同步同型问题）：

`_generate_boolop` docstring（region_ast_generator.py L17672-L17680）中 Pass3-BOOLOP
已对同型「字节码一致性状态」表述追加了 `[Pass3-BOOLOP]` 校正段落。

`_generate_ternary` docstring 中 Pass8-TERNARY（本轮上一区域）已对同型「截至 Pass 01」
表述追加了 `[Pass8-TERNARY]` 校正段落。

但 `_generate_basic_region` docstring 中的同型「截至 Pass 03」表述**未校正**——
对称缺失。截至 Pass 7，应同步 Pass 4-7 期间的状态变化（实际为无变化）。

**修复策略**（与 Pass3-BOOLOP / Pass8-TERNARY 同型——保留原表述作历史追溯，追加校正段落）：

保留原「截至 Pass 03: 127p/10f/137」表述作历史追溯，追加 `[Pass8-SEQ]` 段落校正口径：
- SEQ bounded subset 80 文件实测自 Pass 03 起持续为 127 passed / 10 failed /
  0 errors / 137 总计（Pass7-SEQ fix_report 回归记录 `127 10 0 137 1.7 SEQ files=80`，
  与本 docstring 原「Pass 03: 127p/10f/137」口径一致）
- Pass 3-7 期间持续 127p/10f/137，无新增失败亦无失败消除
- 10 例预存失败分两类：(a) L1_basic 子目录 NameError 类（测试基础设施问题，非反编译器问题）；
  (b) basic/test_b23yieldfrom_complex 嵌套 code object 指令数不匹配，非保守修复范围
  （与 Pass7-SEQ §未完成项 7 同源）
- 与 Pass3-BOOLOP 在 `_generate_boolop` docstring / Pass8-TERNARY 在
  `_generate_ternary` docstring 中追加同步测试状态段落同型

控制流不变，仅 docstring 文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py SEQ
```
**结果**：`127 10 0 137 1.7 SEQ files=80` —— 与基线一致（127 passed, 10 预存失败,
0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅添加注释） |
| 测试文件修改 | 未修改任何测试文件 |
| 过时时点表述（与 Pass3-BOOLOP / Pass8-TERNARY 在 _generate_boolop / _generate_ternary docstring 同步测试状态同型） | **已校正**（追加 [Pass8-SEQ] 段落，说明 Pass 3-7 期间状态持续 127p/10f/137 无变化） |

## 未完成项

1. **`_generate_block_statements` 内 3 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量
   统一替换为 `RETURN_TERMINATOR_OPS`**（Pass7-SEQ 已标记 L25092 首处，余 L25128 / L20595
   同型未标记）：全量替换需逐处评估 break 模式判别语义等价性，留待后续 Pass 统一处理
   （与 Pass6-SEQ §未完成项 1 同源扩展）。
2. **文件全量 40+ 处 `('RETURN_VALUE', 'RETURN_CONST')` 字面量未替换**（Pass6-SEQ
   §未完成项 1，Pass7-SEQ 在 region_ast_generator.py 标记 1 处新发现）：全量替换需逐处评估
   语义等价性，留待后续 Pass 统一处理。
3. **`_loop_depth > 0` 跨层启发式消除**（Pass 4 已标记 `TODO[pass3-SEQ]-F`，对应
   `[Pass4-SEQ]` 注释）：中风险，需先在识别阶段完善 break 块标记。
4. **`_cond_jump_bs` 兜底分支删除**（Pass 1 TODO[pass2-SEQ]-C，已标记）：中风险，
   需先在 `_identify_conditional_regions` 末尾扫描未认领条件跳转块。
5. **`_generate_block_statements` god-method 瘦身**（Pass 2 TODO[pass3-SEQ]-E）：
   高风险，需把语句边界判定移到识别阶段。
6. **`_is_trivial_return_block` Pattern 1 收紧为 `argval is None`**（Pass 2
   TODO[pass2-SEQ]-B）：低风险但属控制流变更，需评估影响。
7. **10 例预存失败**：L1_basic NameError 类（测试基础设施问题）+
   basic/test_b23yieldfrom_complex（字节码重建差异），非保守修复范围。
8. **「截至 Pass 03」表述对称缺失已补齐**：本轮在 `_generate_basic_region` docstring
   中追加 [Pass8-SEQ] 校正段落，与 `_generate_boolop` docstring [Pass3-BOOLOP] 段落 /
   `_generate_ternary` docstring [Pass8-TERNARY] 段落口径一致。后续若实施「彻底删除原表述」
   需同步三处。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_generate_basic_region` docstring
  「字节码一致性约束」节末段追加 [Pass8-SEQ] 校正段落，与 `_generate_boolop`
  [Pass3-BOOLOP] 段落 / `_generate_ternary` [Pass8-TERNARY] 段落口径一致）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/sequence/pass_08/fix_report.md`（本报告）
