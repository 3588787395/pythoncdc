# Pass 2 / ASSERT 修复实施报告

## 1. 实施摘要

依照架构工程师分析，本轮聚焦 ASSERT 区域的「死代码 / docstring 与实际不符 / 重复代码可消除 / 注释标记已知反模式」四类低风险问题，完成 2 项保守修复。所有修改仅触及 `core/cfg/region_analyzer.py` 与 `core/cfg/region_ast_generator.py`，未修改测试文件，未引入 `_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 前缀方法，未引入新的硬编码深度上限，未改变任何控制流（仅同步 docstring + 添加注释）。

| 修复 | 文件 | 位置 | 类型 | 状态 |
|------|------|------|------|------|
| 1 同步 `_identify_assert_regions` 已知失败模式声明（22/27→21/27 + 6 例细分） | region_analyzer.py | L9383-9390 | docstring 同步 | 完成 |
| 2 同步 `_build_assert_message` docstring（失效行号 + 虚假等价声明）+ 标记 walrus 同步差异 | region_ast_generator.py | L2650-2658（docstring）+ L2705-2709（行内注释） | docstring 同步 + 注释标记 | 完成 |

## 2. 架构分析发现

### 2.1 范围
- `_identify_assert_regions`（region_analyzer.py L9294-9499）
- `_generate_assert`（region_ast_generator.py L2093-2286）及其调用的 helper：`_build_assert_chained_compare` / `_build_assert_boolop_condition` / `_build_assert_message` / `_resolve_assert_message_ternary_expr` / `_invert_assert_none_check_direction`
- 四条 fall-through 链遍历器：`_reach_assertion_error_block` / `_find_assertion_error_block` / `_reaches_block_via_fallthrough` / `_reach_raise_varargs_block`（region_analyzer.py L9589-9711）
- `AssertRegion` 类（region_analyzer.py L848-894，Pass 1 已补齐 `contains_block` / `else_block_conflict`）

### 2.2 候选问题筛选

| 候选 | 评估 | 是否实施 |
|------|------|----------|
| docstring 「22/27 passed」与 Pass 1 实测 21/27 不符 | 纯文本同步，零风险 | ✅ 修复 1 |
| `_build_assert_message` docstring 引用失效行号「line 1624-1658」（实为 decorator 代码） | 纯文本同步，零风险 | ✅ 修复 2 |
| `_build_assert_message` docstring 声称「与主路径等价」不实（主路径未调用本方法，且 [Round8-12] 后两路逻辑已分化） | docstring 同步 + 行内注释标记 | ✅ 修复 2 |
| 四条 fall-through 遍历器逻辑近似，可统一 | 终止条件有细微差别（`_reach_assertion_error_block` 显式含 RAISE_VARARGS 终止，`_find_assertion_error_block` 靠 `len(succs)!=1` 间接终止），统一会改变边界行为 | ❌ 超出「保守修复」范围 |
| `_reach_assertion_error_block` 与 `_find_assertion_error_block(succ) is not None` 等价性 | 在「RAISE_VARARGS 块有 1 个后继」等罕见边界行为不同，直接替换有风险 | ❌ 超出「保守修复」范围 |
| `_build_assert_chained_compare` L2362 `if not all_blocks or cond_block is None` 中 `not all_blocks` 永假（`[cond_block] + list(chain_blocks)` 至少 1 元素） | 微小死代码，但 `cond_block is None` 守卫有效，删除收益极低且需重新评估短路语义 | ❌ 本轮不动（收益/风险比不划算） |

### 2.3 死代码排查结论
- 四条 fall-through 遍历器均有唯一调用方（L9407 / L9429 / L9564 / L9436），无死方法。
- `_build_assert_message` 被 chained_compare 分支（L2173）与 boolop 分支（L2196）调用，主路径未调用——非死代码，但 docstring「等价」声明误导（见修复 2）。
- `_resolve_assert_message_ternary_expr` / `_build_assert_chained_compare` / `_build_assert_boolop_condition` / `_invert_assert_none_check_direction` 均有调用方，无死代码。

## 3. 修复 1 — 同步 `_identify_assert_regions` 已知失败模式声明

### 修改内容
region_analyzer.py L9383-9390（docstring 第 6 节「已知失败模式」）：

**修改前**：
```
6. 已知失败模式
   - ASSERT bounded subset: 22/27 passed，已知失败模式：assert-in-if-body / ternary-in-assert-test
```

**修改后**：
```
6. 已知失败模式
   - ASSERT bounded subset: 21/27 passed（Pass 1 实测基线；原分析报告
     声称 22/27 偏高 1 例，已校正）。已知 6 例失败（Pass 1 §7.3 实测）：
     - 3 例 ternary-in-assert-test（assert 条件本身为三元表达式，需建立
       condition_block = ternary.merge_block 父子引用，本识别器未处理）；
     - 3 例 assert-in-if-body（链式比较变体：assert 嵌入 if body，涉及
       ASSERT 与 BOOLOP/CC/TERNARY 识别顺序的高风险调整，未处理）。
```

### 依据
Pass 1 报告 §6 实测：任务给定基线 22p/5f/27，stash 实测基线 **21p/6f/27**（分析报告基线数字偏高 1 例），修复后维持 21p/6f/27。Pass 1 报告 §7.3 列出 6 例失败：
- 3 例 ternary-in-assert-test：`test_r14_ternary_assert_two_ternaries_boolop` / `test_r17_ternary_assert_test_method` / `test_r20_ternary_assert_msg_binop_two`
- 3 例 assert-in-if-body（链式比较变体）：`test_adv18_assert_in_if_body` / `test_adv19_assert_chained_cmp_in_if_body` / `test_adv20_assert_chained_cmp_in_branches`

### 风险评估
零风险——仅 docstring 文本同步，不触及任何可执行代码。

## 4. 修复 2 — 同步 `_build_assert_message` docstring + 标记 walrus 同步差异

### 4.1 docstring 同步（L2650-2658）

**修改前**：
```
- 与 _generate_assert 主路径中 message 重建逻辑等价（line 1624-1658）。
- 抽出为方法以便链式比较分支复用，避免逻辑重复。
```

**修改后**：
```
- 仅供 _generate_assert 的链式比较分支（chained_compare / boolop）
  复用；_generate_assert 默认主路径未调用本方法，而是内联一份
  独立的消息重建逻辑（含 [Round8-12] walrus 反向 RAISE_VARARGS 扫描）。
- 已知差异（保守修复，待后续轮次统一）：主路径在 [Round8-12] 为
  walrus 消息引入反向 RAISE_VARARGS 扫描，本方法仅 has_build_string
  分支同步了该扫描，非 build_string 分支仍为旧逻辑（一律跳过
  PRECALL/CALL），未同步 walrus 处理。
- 旧 docstring 中「line 1624-1658」引用已失效（该行段实为
  decorator 处理代码，与 assert message 无关），已清除。
```

### 4.2 行内注释标记（L2705-2709）

在 `_build_assert_message` 非 build_string 分支前添加注释：

```python
else:
    # [Pass 2] 已知差异：未同步主路径 [Round8-12] 的 walrus 反向
    # RAISE_VARARGS 扫描（chain 分支暂不进入 walrus 消息场景）。
    # 保守修复：仅标记，不改控制流；若后续 chain + walrus 用例
    # 出现，需统一两路逻辑。
    for instr in instrs:
        if instr.opname in base_skip or instr.opname in ('PRECALL', 'CALL'):
            continue
        msg_instrs.append(instr)
```

### 4.3 依据
- **失效行号**：`grep` 验证 region_ast_generator.py L1624-1658 实为 decorator `call_count_after_make` 计数循环与 `has_decorator_args` 初始化代码，与 assert message 无关。
- **调用关系**：`grep "_build_assert_message("` 命中 3 处——L2173（chained_compare 分支）/ L2196（boolop 分支）/ L2643（定义）。主路径（L2241-2286）内联了独立逻辑，未调用本方法。
- **逻辑分化**：主路径 [Round8-12] 注释（L2243-2253）明确说明「旧逻辑：非 BUILD_STRING 时一律跳过所有 PRECALL/CALL…新逻辑：统一用反向扫描定位 RAISE_VARARGS 边界」。本方法 has_build_string 分支（L2678-2704）已同步反向扫描，但非 build_string 分支（L2710-2713）仍为旧逻辑——主路径已修复的 walrus 漏洞在本方法 chain 分支中仍潜在存在。

### 4.4 风险评估
零风险——仅 docstring 文本同步 + 行内注释添加，不触及任何可执行代码的控制流或逻辑。

### 4.5 未实施的相关高风险修复（明确排除）
将本方法非 build_string 分支替换为主路径的反向 RAISE_VARARGS 扫描逻辑可消除已知差异，但属于「改变控制流」，违反本轮严格约束，留待后续轮次处理。

## 5. 编译检查

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; print('OK')"
```
输出：`OK`（退出码 0）。

## 6. 反模式自检

| 自检项 | 期望 | 实测 | 备注 |
|--------|------|------|------|
| `grep -n "depth < 8" core/cfg/region_analyzer.py` | 0 | 0 | ✓（Pass 1 已清除，本轮未引入） |
| `grep -nE "_fix_|_merge_|_patch_|_fallback_|_hack_|_workaround_|_temp_" core/cfg/region_*.py` 中本轮新增 | 0 | 0 | ✓（未新增任何前缀方法） |
| 新增硬编码深度上限 | 0 | 0 | ✓ |
| 改变控制流 | 否 | 否 | ✓（仅 docstring + 注释） |
| `grep -n "22/27 passed" core/cfg/region_analyzer.py` | 0 | 0 | ✓（修复 1 已校正为 21/27） |
| `grep -n "line 1624-1658" core/cfg/region_ast_generator.py` | 0 | 0 | ✓（修复 2 已清除失效引用） |
| `grep -n "100%.*(通过率\|完全匹配)\|无已知失败模式"` ASSERT 区域命中 | 0 | 0 | ✓（Pass 1 已清除，本轮未回填） |

## 7. 修改文件清单

- `/workspace/core/cfg/region_analyzer.py`：L9383-9390（`_identify_assert_regions` docstring 第 6 节「已知失败模式」同步为 21/27 + 6 例细分）。
- `/workspace/core/cfg/region_ast_generator.py`：
  - L2650-2658（`_build_assert_message` docstring「实现要点」前两行替换：清除失效行号 + 校正等价性声明 + 标记 walrus 同步差异）。
  - L2705-2709（`_build_assert_message` 非 build_string 分支前添加 `[Pass 2]` 行内注释标记已知差异）。

## 8. 与 Pass 1 的衔接

- Pass 1 已消除 `depth < 8` 硬编码、`_fix_assert_none_check_direction` 前缀、ASSERT 区域虚假「100% 通过率」声明，并补齐 `AssertRegion.contains_block` / `else_block_conflict` 多态方法。
- Pass 2 沿用 Pass 1 §7.3 的实测基线（21p/6f/27）校正 docstring 残留的「22/27」旧数字（Pass 1 修复 2 替换「100% 通过率」时填入的中间值），并发现 Pass 1 未触及的 `_build_assert_message` docstring 失效行号 + 主路径/chain 路逻辑分化问题。
- 两轮均未引入回归（Pass 1 §6 已验证 IF/TERNARY 完全无退化；本轮纯 docstring + 注释，不可能产生回归）。

未 commit / push（依规由主调度器统一处理）。
