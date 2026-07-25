# 修复实施报告 — Pass 1 / MATCH 区域

## 概览

按架构工程师 pass_01 分析报告，对 pythoncdc 反编译器 MATCH 区域实施 3 项零/低风险修复，
聚焦反模式消除（STORE_DEREF 缺失、DRY 重复实现、硬编码 case 数阈值）。
全部 3 项修复均落地，未触发回归，未引入禁止前缀方法名或新增后处理补丁。

## 修复清单

### 修复 1 — 补全 _is_match_subject_block 的 STORE_DEREF
- **文件**: `core/cfg/region_analyzer.py`
- **位置**: L7504-L7506（原 L7505）
- **类型**: 最低风险，扩展指令名元组
- **变更**:
  - 原 walrus 排除判据为三元组 `('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL')`
  - 扩展为四元组 `('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF')`
- **理由**: 与代码库其余 40+ 处一致，覆盖闭包/嵌套函数内 walrus (`:=`) 场景；零语义风险
- **验证**: `python -c "import core.cfg.region_analyzer"` 通过；MATCH 回归不退化

### 修复 2 — 合并 _collect_pattern_store_names 重复实现（下沉到 pattern_parser）
- **文件**:
  - `core/cfg/pattern_parser.py` — 新增模块级权威函数 `collect_pattern_store_names(pattern, names)` L1732-L1772
  - `core/cfg/region_analyzer.py` — `_mr_collect_pattern_store_names` 改为 1 行委托 L7750-L7753
  - `core/cfg/region_ast_generator.py` — `_collect_pattern_store_names` 改为 1 行委托 L16272-L16275
  - 两处 `from .pattern_parser import ...` 导入新增 `collect_pattern_store_names`
- **类型**: 低风险，纯重构
- **变更**:
  - 两处完全相同的六类递归收集（MatchAs/MatchStarred/MatchSequence/MatchMapping/MatchClass/MatchOr）
    合并为 pattern_parser 模块级函数 `collect_pattern_store_names`
  - 原实例方法保留为薄包装，签名 `(self, pattern, names)` 不变，调用点零改动
- **理由**: 消除 DRY 违背；pattern_parser 模块本就是 pattern 解析的单一职责归属
- **签名兼容性**: 实例方法 `(self, pattern, names)` 与模块函数 `(pattern, names)` 参数对齐，
  返回值均为 `None`（通过 `names` 集合 in-place 累积），完全等价
- **验证**: 编译通过；MATCH/IF/TERNARY 三个区域回归不退化

### 修复 3 — 移除 _verify_literal_match_chain 的硬编码 case 数阈值
- **文件**: `core/cfg/region_analyzer.py`
- **位置**: L7643-L7649（原 L7643-L7644）
- **类型**: 中等风险（保守做法 — 仅删除阈值，保留 reload_count 单一判据）
- **变更**:
  - 原: `if reload_count == len(case_blocks) - 1 and len(case_blocks) > 2: return False`
  - 新: `if reload_count == len(case_blocks) - 1: return False`
- **理由**: 消除硬编码 case 数下限（`> 2`）。2-case 场景下：
  - 结构型 match 的 subject 块必然含 COPY，上游 `has_copy` 判据已先行通过
  - 进入 reload_count 分支的 2-case 场景意味着 subject 无 COPY 且后续 case 重新加载 subject
    — 这正是 if-elif 的特征，应被识别为 if-elif 而非 match
- **未采用的可选增强**: 将 reload_count 启发式整体替换为 COPY 结构判据
  （subject 块含 COPY → match；不含 → if-elif）。本轮保守起见仅删除阈值，保留 reload_count 单一判据，
  待后续迭代验证后再考虑
- **验证**: MATCH 回归 79p/0f/79 与基线完全一致，2-case match 用例未误判

## 反模式自检

### 1. STORE_DEREF 三元组检查
```
$ python -c "检测 'STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL' 不带 STORE_DEREF 的同行出现"
```
- 结果: 仅 3 处跨行元组（L9845, L10102, L11018），其续行均含 `'STORE_DEREF'` 或为
  `STORE_ATTR/STORE_SUBSCR` 的有意超集（非变量 STORE 族）
- 修复 1 目标行 L7506 已含 STORE_DEREF ✓

### 2. 硬编码 case 数阈值检查
```
$ grep -n "len(case_blocks) > 2" core/cfg/region_analyzer.py
```
- 结果: 0 处命中 ✓（修复 3 已删除）

### 3. 禁止前缀方法名检查
- 未引入任何 `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀的新方法名
- 新增的 `collect_pattern_store_names` 为 pattern_parser 模块级公开函数，无禁止前缀 ✓
- 保留的 `_mr_collect_pattern_store_names` / `_collect_pattern_store_names` 为既有方法名（薄包装），非新增 ✓

### 4. 后处理补丁检查
- 未新增任何后处理补丁 ✓
- 未修改测试文件 ✓

## 编译检查
```
$ python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; \
             import core.cfg.pattern_parser; \
             from core.cfg.pattern_parser import collect_pattern_store_names; \
             print('OK: imports clean')"
OK: imports clean
```

## 回归测试结果

| 区域 | 基线 (pass/fail/error/total) | 修复后 | 状态 |
|------|------------------------------|--------|------|
| MATCH   | 79 / 0 / 0 / 79 | 79 / 0 / 0 / 79 | ✅ 一致 |
| IF      | 79 / 1 / 0 / 80 | 79 / 1 / 0 / 80 | ✅ 一致（1 失败为预存） |
| TERNARY | 69 / 7 / 0 / 76 | 69 / 7 / 0 / 76 | ✅ 一致（7 失败为预存） |

三个区域全部与基线一致，**无新增失败、无退化**。

## 修改文件清单
1. `core/cfg/region_analyzer.py`
   - L31: `from .pattern_parser import PatternParser, collect_pattern_store_names`
   - L7504-L7506: STORE_DEREF 四元组（修复 1）
   - L7643-L7649: 删除 `and len(case_blocks) > 2`（修复 3）
   - L7750-L7753: `_mr_collect_pattern_store_names` 改为委托（修复 2）
2. `core/cfg/region_ast_generator.py`
   - L81: `from .pattern_parser import collect_pattern_store_names`
   - L16272-L16275: `_collect_pattern_store_names` 改为委托（修复 2）
3. `core/cfg/pattern_parser.py`
   - L1732-L1772: 新增模块级函数 `collect_pattern_store_names`（修复 2 的权威实现）

## 未处理项（后续迭代）
按 pass_01 报告，以下高风险项不在本轮范围：
- `_detect_undetected_wildcard_match` 跨阶段补建移除
- `_region_overlaps_with_ternary` 反向过滤移除
- `_identify_match_regions` 越权捷径与 Phase 2.5 职责合并
- 通配符 match 虚拟块创建+区域字段突变+except 吞异常移除

## 实施约束遵循
- ✅ 最小修改原则 — 仅修改必要行，未做范围外重构
- ✅ 未引入禁止前缀方法名
- ✅ 未新增硬编码深度上限（本轮目标正是消除 `> 2` 阈值）
- ✅ 未新增后处理补丁
- ✅ 未修改测试文件
- ✅ 未 commit / push（由主调度器统一）
