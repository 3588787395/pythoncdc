# 修复实施报告 — Pass 2 / MATCH 区域

## 概览

按架构工程师 pass_02 分析，对 pythoncdc 反编译器 MATCH 区域实施 2 项零/低风险修复，
聚焦死代码消除与 docstring 同步。本轮严格遵循"不改变控制流"约束：
仅删除永不触发的冗余判据、同步与实际不符的方法 docstring，未触碰任何执行路径。
两处修复均落地，未引入禁止前缀方法名、未引入硬编码阈值、未新增后处理补丁。

## 修复清单

### 修复 1 — 删除 _scan_literal_match_subjects 中永不触发的冗余 length 检查（死代码）
- **文件**: `core/cfg/region_analyzer.py`
- **位置**: 原 L9097-L9098（删除 2 行）
- **类型**: 最低风险，纯删除死代码
- **变更**:
  - 删除前:
    ```python
    if not case_blocks_l:
        continue
    if len(case_blocks_l) < 1:
        continue
    ```
  - 删除后:
    ```python
    if not case_blocks_l:
        continue
    ```
- **理由**:
  - `case_blocks_l` 初始化为 `[]`（L9026），后续仅 `.append`，恒为 list
  - `not case_blocks_l` 为 True 当且仅当 `len(case_blocks_l) == 0`
  - `len(case_blocks_l) < 1` 为 True 当且仅当 `len(case_blocks_l) == 0`（length 不可能为负）
  - 故第二行 `if len(case_blocks_l) < 1: continue` 在前一检查通过后**永不触发**，
    属于 100% 死代码
  - `len()` 调用与比较无副作用，删除零语义风险
- **控制流影响**: 无。空列表分支已由前一行的 `if not case_blocks_l: continue` 唯一覆盖
- **验证**: 编译通过

### 修复 2 — 同步 _identify_match_regions docstring（修正"两种形态共用"不实陈述）
- **文件**: `core/cfg/region_analyzer.py`
- **位置**: L7690-L7691（原 L7690 单行改写为两行）
- **类型**: 最低风险，纯 docstring 文本同步
- **变更**:
  - 修改前:
    ```
    两种形态共用 _mr_collect_case_body 沿条件跳转链收集 case 块。
    ```
  - 修改后:
    ```
    结构型形态通过 _mr_collect_case_body 沿条件跳转链收集 case 块；
    字面量形态在 _scan_literal_match_subjects 内联收集 case 块（不调用 _mr_collect_case_body）。
    ```
- **理由（docstring 与实际不符的证据）**:
  - 全局检索 `_mr_collect_case_body` 调用点，仅 2 处：
    1. `_identify_match_regions` L7754（结构型形态主入口）
    2. `_collect_nested_match_region` L8771（嵌套结构型形态）
  - 字面量形态 `_scan_literal_match_subjects`（L9011）**不调用** `_mr_collect_case_body`，
    而是使用自身的内联 case 收集循环（L9050-L9094：`while current and current not in visited_l`）
  - 该方法自身的 docstring（L8643、L8746-L8747）亦明确区分：
    "调用_mr_collect_case_body()（结构型）或内部逻辑（字面量型）"
  - 故原 docstring"两种形态共用 _mr_collect_case_body"与实际架构不符，本次同步为准确描述
- **控制流影响**: 无（仅 docstring 文本）
- **验证**: 编译通过

## 反模式自检

### 1. 禁止前缀方法名检查
- 未引入任何 `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀的新方法名 ✓
- 未新增任何方法（仅删除 2 行死代码 + 改写 docstring 文本）✓

### 2. 硬编码深度上限检查
- 未引入任何硬编码深度上限 ✓
- 未修改任何 case 数阈值（pass_01 已消除 `> 2` 阈值，本轮未触碰）✓

### 3. 后处理补丁检查
- 未新增任何后处理补丁 ✓
- 未修改测试文件 ✓

### 4. 控制流不变性检查
- 修复 1: 删除的 `if len(case_blocks_l) < 1: continue` 永不触发（前一检查已覆盖空列表），
  控制流等价 ✓
- 修复 2: 仅 docstring 文本，无代码语义变化 ✓

## 编译检查
```
$ python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; \
             print('OK: imports clean')"
OK: imports clean
```

## 修改文件清单
1. `core/cfg/region_analyzer.py`
   - L7690-L7691: 同步 docstring（修复 2，原 L7690 单行 → 两行准确描述）
   - L9095-L9097: 删除冗余 `if len(case_blocks_l) < 1: continue`（修复 1，原 L9097-L9098 删除）

## 未处理项（后续迭代）

按 pass_01 / pass_02 范围划分，以下高风险项不在本轮范围（需架构工程师评估后单独迭代）：

- `_detect_undetected_wildcard_match` 跨阶段补建移除（已知反模式，pass_01 已标记）
  - 该方法 L16058 在 region_ast_generator 阶段补建虚拟 MatchRegion，
    违反"区域识别归 region_analyzer、AST 生成归 ast_generator"的职责分离
  - 本轮保守起见未加注释标记（避免在未评估影响前改动该路径），建议下轮加 `# 已知反模式` 标记
- `_region_overlaps_with_ternary` 反向过滤移除
- `_identify_match_regions` 越权捷径与 Phase 2.5 职责合并
- 通配符 match 虚拟块创建 + 区域字段突变 + except 吞异常移除
  - `_generate_match` 中 L15531 `except Exception: pass` 静默吞异常为已知风险点，
    本轮未触碰（改变异常处理属控制流变更，超出本轮约束）

### 本轮评估但未采用的候选
- `_generate_match` 中 L15610-L15819 的 ~200 行字符串字面量（位于 `if` 块内，
  非函数首语句，运行期为 no-op 表达式）: 技术上属"冗余操作"，但内容为意图性文档，
  删除为大体量变更且会丢失设计说明，风险/收益不匹配，本轮保留
- `_scan_literal_match_subjects` L9024-L9025 `if block is None: continue`:
  位于 `block_to_region.get(block)` 之后，逻辑上 block 不可能为 None
  （来自 `get_blocks_in_order()` 迭代），属防御性死代码；
  但删除防御性 None 检查争议较大，本轮保守保留

## 实施约束遵循
- ✅ 最小修改原则 — 仅 2 处必要修改，未做范围外重构
- ✅ 未引入禁止前缀方法名
- ✅ 未新增硬编码深度上限
- ✅ 未新增后处理补丁
- ✅ 未修改测试文件
- ✅ 未改变控制流（修复 1 删除永不触发分支；修复 2 仅 docstring）
- ✅ 编译验证通过
- ✅ 未 commit / push（由主调度器统一）
