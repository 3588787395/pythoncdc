# Pass 4 ASSERT 修复报告

## 修复内容

### Fix 1: 同步 `_generate_assert` docstring 中消息重建逻辑的过时描述

**问题位置**：`/workspace/core/cfg/region_ast_generator.py` `_generate_assert` 方法 docstring（L2128-L2133）

**问题根因**（Pass 1-3 未触及的 docstring 漂移）：
docstring 描述消息表达式重建逻辑时，与 [Round8-12] 修改后的实际代码存在两处不一致：

1. **base_skip 集合元素不符**：
   - docstring 声称 `base_skip = {..., COPY, SWAP}`（含 COPY）
   - 实际代码（L2258-L2260）`base_skip = {'RAISE_VARARGS', 'POP_EXCEPT', 'RERAISE', 'LOAD_ASSERTION_ERROR', 'RESUME', 'NOP', 'CACHE', 'PUSH_NULL', 'SWAP'}`（**不含 COPY**）
   - 原因：[Round8-12] 为支持 walrus 消息（`(n := f())`）将 COPY 从 base_skip 移除，使 COPY+STORE 模式可被 expr_reconstructor 识别为 walrus。代码内注释（L2251-L2257）已说明此变更，但 docstring 未同步。

2. **非 BUILD_STRING 分支处理逻辑不符**：
   - docstring 声称"否则一律跳过 PRECALL/CALL"
   - 实际代码（L2261-L2279）对**所有**消息块（无论是否含 BUILD_STRING）统一执行反向 RAISE_VARARGS 扫描定位 `raise_call_start` 边界，仅过滤该边界及之后的 PRECALL/CALL
   - 原因：[Round8-12] 把 build_string 路径已有的反向扫描统一到所有情况，避免"一律跳过 PRECALL/CALL"导致 `assert x, f()` 退化为 `assert x, f`。代码内注释已说明，docstring 未同步。

**修复策略**：
仅同步 docstring 文本——从 base_skip 集合中移除 COPY，并把"否则一律跳过 PRECALL/CALL"改写为反映 [Round8-12] 统一反向扫描的实际逻辑。新增 `[Pass4-ASSERT]` 标记说明同步依据。不触及任何可执行代码，控制流不变。

**等价性证明**：
- 仅修改 docstring 文本，未修改任何可执行语句
- 编译期与运行期行为完全不变
- 维护者阅读 docstring 时获得与实际代码一致的描述，避免误判

## 编译验证

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator"
```
**结果**：退出码 0，输出 `OK`。

## 回归测试

```
timeout 290 python .trae/specs/analysis-fix-iteration/run_region_tests.py ASSERT
```
**结果**：`21 6 0 27 2.5 ASSERT files=27` —— 与基线一致（21 passed, 6 预存失败, 0 errors）。无退化。

## 反模式消除情况

| 反模式 | 本轮处理 |
|---|---|
| `_fix_` / `_merge_` / `_patch_` 前缀 | 未引入 |
| 硬编码深度上限 | 未引入 |
| 控制流改变 | 未改变（仅 docstring 文本同步） |
| 测试文件修改 | 未修改任何测试文件 |

## 未完成项

1. **`_build_assert_message` 非 build_string 分支未同步主路径 [Round8-12] walrus 反向 RAISE_VARARGS 扫描**（Pass 2 已标记）：属控制流变更，超出本轮约束。
2. **6 例预存失败**（3 ternary-in-assert-test + 3 assert-in-if-body 链式比较变体）：需识别顺序调整，非本轮范围。
3. **四条 fall-through 遍历器逻辑近似可统一**（Pass 2 已评估）：终止条件有细微差别，统一会改变边界行为，超出保守修复范围。
4. **L9436 "Fallback" 注释保留 legacy 行为**（Pass 1 已登记）：已知反模式（Fallback 补丁），待归约期统一 `_find_assertion_error_block` / `_reach_raise_varargs_block` 后消除。

## 文件清单

- `/workspace/core/cfg/region_ast_generator.py`（Fix 1：`_generate_assert` docstring L2128-L2133 同步）
- `/workspace/.trae/specs/analysis-fix-iteration/rounds/ASSERT/pass_04/fix_report.md`（本报告）
