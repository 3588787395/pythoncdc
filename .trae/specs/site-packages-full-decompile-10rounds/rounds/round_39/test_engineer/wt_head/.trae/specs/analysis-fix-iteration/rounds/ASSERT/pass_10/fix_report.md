# Pass 10 ASSERT 修复报告

## 修复内容

### Fix 1: 校正 `_identify_assert_regions` docstring 中 [Pass9-ASSERT] 段落的两处行号引用（自写入时即偏差 +23，现 +33）

**问题位置**：`/workspace/core/cfg/region_analyzer.py:9411-9433`
（`_identify_assert_regions` docstring §1 归约过程 [Pass9-ASSERT] 段落）

**问题根因**（与 Pass10-MATCH 同型——行号引用自写入时即偏差）：

`_identify_assert_regions` docstring [Pass9-ASSERT] 段落引用两处行号：

```
(a) 实际代码（grep `_reach_assertion_error_block(succ)` 在本文件
    仅 1 处命中，L9489，[Round4-12] 修复）
(b) 实际代码（grep `mb = self._find_assertion_error_block(succ)` 在本文件
    仅 1 处命中，L9511）
```

经 git show 687cf0a（pass9-ASSERT commit）验证，**自写入时即偏差 +23**：

| 引用项 | [Pass9-ASSERT] 引用 | commit 687cf0a 实际 | 现实际 | 偏差（现） |
|---|---|---|---|---|
| `_reach_assertion_error_block(succ)` | L9489 | L9512 | L9522 | +33 |
| `mb = self._find_assertion_error_block(succ)` | L9511 | L9534 | L9544 | +33 |

即 [Pass9-ASSERT] 段落写入时引用的 L9489/L9511 与当时实际 L9512/L9534 已偏差 +23
（grep 验证：`git show 687cf0a:core/cfg/region_analyzer.py | grep -n` 两处命中
分别为 L9512/L9534）。经 Pass10-MATCH（`_identify_match_regions` docstring 追加
[Pass10-MATCH] 段落 +10，位于本方法之前）上游修改，现实际位置为 L9522/L9544
（总偏差 +33 = 写入时 +23 + Pass10-MATCH +10）。

[Pass9-ASSERT] 段落虽采用「grep ... 在本文件仅 1 处命中」兜底口径（可重新定位），
但行号 L9489/L9511 自写入时即不准确，仍可能误导读者。

**修复策略**（与 Pass10-MATCH 同型——仅 docstring 文本同步，不改控制流）：

在 [Pass9-ASSERT] 段落之后追加 `[Pass10-ASSERT]` 段落，校正：
1. [Pass9-ASSERT] 引用的 L9489/L9511 自写入时即偏差 +23（git show 687cf0a 验证）
2. 经 Pass10-MATCH +10 上游修改，现实际位置 L9522/L9544（总偏差 +33）
3. grep 验证方法不变：两处引用在本文件均仅 1 处命中（可执行代码处）
4. 本轮仅校正行号引用，控制流不变

不重写 [Pass9-ASSERT] 原段落（与 Pass8/Pass9/Pass10-MATCH 同型保守策略一致）。

控制流不变，仅 docstring 文本同步。

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `COMPILE_OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py ASSERT
```
**结果**：`21 6 0 27 2.5 ASSERT files=27` —— 与 Pass9-ASSERT 一致（21 passed, 6 预存失败, 0 errors）。
无退化（docstring-only 编辑不影响测试；baseline.txt 记录 22/5 为起始基线，Pass9-ASSERT
已记录 21/6，本轮一致）。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅 docstring 文本同步） |
| 测试文件修改 | 未修改任何测试文件 |
| docstring 行号引用自写入时即偏差（与 Pass10-MATCH 同型） | **已校正**（[Pass9-ASSERT] L9489/L9511 → 现实际 L9522/L9544，写入时偏差 +23，经 Pass10-MATCH +10 后总偏差 +33） |

## 未完成项

1. **`_reach_raise_varargs_block` Fallback 补丁消除**（Pass 5 已标记、Pass6-ASSERT 同步行号引用）：
   控制流变更，需统一 `_find_assertion_error_block` / `_reach_raise_varargs_block`
   为单一查询路径后删除。
2. **`_build_assert_message` 非 build_string 分支未同步主路径 [Round8-12] walrus 反向
   RAISE_VARARGS 扫描**（Pass 2 已标记）：属控制流变更，超出本轮约束。
3. **6 例预存失败**（3 ternary-in-assert-test + 3 assert-in-if-body 链式比较变体）：需
   识别顺序调整，非本轮范围。
4. **四条 fall-through 遍历器逻辑近似可统一**（Pass 2 已评估）：终止条件有细微差别，
   统一会改变边界行为，超出保守修复范围。
5. **`'TRUE' in cond_last.opname` / `'NOT_NONE' in cond_last.opname` / `'NOT_NONE' in
   last_instr.opname` 子串匹配统一替换为 frozenset 常量**（Pass7-ASSERT + Pass8-ASSERT
   已标记两处）：与 Pass5/Pass6-BOOLOP 同型，需统一全量替换 17+ 处。
6. **Step 4 / Step 5 表述与实际控制流差异**：Pass9-ASSERT 已在 §1 追加段落补记，
   本轮校正该段落行号引用。

## 文件清单

- `/workspace/core/cfg/region_analyzer.py`（Fix 1：`_identify_assert_regions` docstring [Pass9-ASSERT] 段落后追加 [Pass10-ASSERT] 段落，校正 L9489/L9511 → L9522/L9544，写入时偏差 +23，经 Pass10-MATCH +10 后总偏差 +33）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/ASSERT/pass_10/fix_report.md`（本报告）
