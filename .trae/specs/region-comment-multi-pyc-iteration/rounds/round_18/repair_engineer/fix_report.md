# R18 修复报告 — strategy.pyc trade_strategy_add KW_NAMES 关键字参数丢失

## 1. 修复概述

| 字段 | 值 |
|---|---|
| 轮次 | R18 (rcm-r18) |
| 目标 pyc | `IQCommon/strategy/strategy.pyc` |
| 缺陷模式 | with 上下文管理器调用的关键字参数（KW_NAMES）在 ctx_expr 白收集中被静默丢弃 |
| 修复文件 | `core/cfg/region_analyzer.py`（`_extract_with_items` ctx_expr 白名单）+ `core/cfg/region_ast_generator.py`（`_generate_with` docstring） |
| 修复方法 | ctx_expr 白名单加入 `'KW_NAMES'`，使 KW_NAMES 指令随 CALL 一起收集到 with 上下文表达式，下游 reconstruct 正确拆分关键字参数 |
| 修复前 pyc match_rate | 0.00%（0/2，诊断阶段 189 true_diffs in trade_strategy_add） |
| 修复后 pyc match_rate | **0.00%** (0/2) — failed（KW_NAMES 修复 -128 diffs 至 61，但 if-drop 新发现致仍 mismatched） |
| 修复前 repro | with open(path,'r',encoding='utf-8') 产物为 with open(path,'r','utf-8')（encoding= 丢失） |
| 修复后 repro | **8 DEFECT-REPRO / 3 CTRL 全部 NO-DEFECT**（11/11，KW_NAMES 修复验证） |
| 回归测试 | import 编译通过；R17 repros 10/10 NO-DEFECT 不变（零回归） |

## 2. 缺陷定位

**函数**: `trade_strategy_add`（strategy.pyc）

**源码结构**:
```python
def trade_strategy_add(user_id, business_type, strategy_name, strategy_lv2_name):
    ...
    with open(strategy_template_path, 'r', encoding='utf-8') as strategy_template:
        content = strategy_template.read()
    ...
```

**原始字节码**（offset 570-606）:
```
570 LOAD_GLOBAL 21 (NULL + open)
582 LOAD_FAST 10 (strategy_template_path)
584 LOAD_CONST 11 ('r')
586 LOAD_CONST 12 ('utf-8')
588 KW_NAMES 13                      <- ('encoding',) 关键字参数名
590 PRECALL 3
594 CALL 3                           <- 应消费 KW_NAMES 拆分 encoding='utf-8'
604 BEFORE_WITH
606 STORE_FAST 11 (strategy_template)
```

**修复前产物字节码**（KW_NAMES 丢失）:
```
570 LOAD_GLOBAL 21 (NULL + open)
582 LOAD_FAST 10 (strategy_template_path)
584 LOAD_CONST 11 ('r')
586 LOAD_CONST 12 ('utf-8')
588 PRECALL 3                        <- KW_NAMES 丢失，'utf-8' 当位置参数
592 CALL 3
602 BEFORE_WITH
```

**缺陷**: with 上下文管理器调用 `open(strategy_template_path, 'r', encoding='utf-8')` 的 `encoding=` 关键字参数在反编译产物中丢失，变为位置参数 `open(strategy_template_path, 'r', 'utf-8')`。重编字节码缺少 KW_NAMES 指令，与原始不一致（61 true_diffs 中 128 来自此缺陷的 shift noise）。

**根因**: `region_analyzer.py:8694` 的 `_extract_with_items` 方法在收集 with 上下文表达式（ctx_expr）时，使用白名单过滤指令。白名单包含 LOAD_NAME/LOAD_GLOBAL/LOAD_ATTR/LOAD_FAST/LOAD_CONST/LOAD_METHOD/CALL/PRECALL/PUSH_NULL/SWAP/COPY/BINARY_SUBSCR/BINARY_OP/BUILD_TUPLE/BUILD_LIST/BUILD_MAP/BUILD_SET/BUILD_STRING/BUILD_SLICE/UNPACK_SEQUENCE/IS_OP/CONTAINS_OP，但**遗漏 KW_NAMES**。KW_NAMES 既不在 NOISE_OPS（不被显式跳过），也不在白名单（不被收集），故静默丢弃。

下游 `region_ast_generator.py:_generate_with`（L19601-19692）通过 `region.items → context_instrs → expr_instrs → expr_reconstructor.reconstruct(expr_instrs)` 链路生成 context_expr。因 expr_instrs 不含 KW_NAMES，`ast_generator_v2.py:_process_instruction` 的 KW_NAMES handler（L1112-1127，设置 `temp_vars['kw_names']`）+ CALL handler（L1180-1195，消费 `kw_names` 拆分关键字参数）无法工作，'utf-8' 被当位置参数。

**对照**: 非 with 上下文的 CALL（如 `aes_encrypt(content, aes_key=session_key, aes_iv=session_iv, return_str=True)`，3 keywords）走 `_build_statements_from_instructions` 路径，KW_NAMES 正常传入 reconstruct，关键字正确拆分。仅 with 上下文调用受影响——因为 with 走 `region.items` → ctx_expr 白名单路径，非 with 走 `_build_statements_from_instructions` 路径（无白名单过滤）。

## 3. 修复方案

在 `core/cfg/region_analyzer.py:8694` 的 `_extract_with_items` ctx_expr 白名单中加入 `'KW_NAMES'`：

```python
# 修复前
if instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_ATTR', 'LOAD_FAST',
                   'LOAD_CONST', 'LOAD_METHOD', 'CALL', 'PRECALL',
                   'PUSH_NULL', 'SWAP', 'COPY', 'BINARY_SUBSCR',
                   'BINARY_OP', 'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP',
                   'BUILD_SET', 'BUILD_STRING', 'BUILD_SLICE',
                   'UNPACK_SEQUENCE', 'IS_OP', 'CONTAINS_OP'):
    ctx_expr.append(instr)

# 修复后（+KW_NAMES）
if instr.opname in ('LOAD_NAME', 'LOAD_GLOBAL', 'LOAD_ATTR', 'LOAD_FAST',
                   'LOAD_CONST', 'LOAD_METHOD', 'CALL', 'PRECALL',
                   'PUSH_NULL', 'SWAP', 'COPY', 'BINARY_SUBSCR',
                   'BINARY_OP', 'BUILD_TUPLE', 'BUILD_LIST', 'BUILD_MAP',
                   'BUILD_SET', 'BUILD_STRING', 'BUILD_SLICE',
                   'UNPACK_SEQUENCE', 'IS_OP', 'CONTAINS_OP',
                   'KW_NAMES'):
    ctx_expr.append(instr)
```

+[R18 fix] 注释段落说明背景、触发条件、根因、修复方式。

在 `core/cfg/region_ast_generator.py:_generate_with` docstring 的「字节码一致性约束」段落加 [R18 fix] 子段落，说明 with 上下文管理器调用的关键字参数保留链路（region.items → context_instrs → expr_instrs → reconstruct）及对 region_analyzer._extract_with_items ctx_expr 白名单的依赖。

**算法 4 原则合规**:
- **自底向上归约**: ✓ 未改变归约顺序（仅在 ctx_expr 收集阶段保留 KW_NAMES）
- **每块唯一归属**: ✓ KW_NAMES 指令随 CALL 归 with 上下文表达式，无重复收集
- **嵌套即抽象节点**: ✓ 未改变
- **入口引用语义**: ✓ 未改变

**安全性**: KW_NAMES 是 Python 3.11+ 关键字参数名声明指令，仅在 CALL 前出现，栈效应为 0（不压栈/弹栈）。加入白名单不影响栈模拟，仅确保指令被收集到 ctx_expr 供下游 reconstruct 处理。`ExpressionReconstructor._process_instruction` 已有完整 KW_NAMES handler（L1112-1127）+ CALL handler（L1180-1195），修复后 KW_NAMES 正确流入。

## 4. 回归测试结果

### 模块编译检查

```
python -c "import core.cfg.region_analyzer; import core.cfg.region_ast_generator; import core.cfg.code_generator"
OK compile
```

### 目标 pyc 验证（修复后）

```
strategy.pyc: 0.00% (0/2), decompile_status=failed
  - <module>: 39 true_diffs (Pattern R2 不可修复残留)
  - trade_strategy_add: 61 true_diffs (KW_NAMES 修复 -128 diffs，if-drop 新发现 61 diffs)
```

trade_strategy_add true_diffs: 189 → 61（-128，KW_NAMES 修复贡献）。encoding='utf-8' 正确保留（offset 588 KW_NAMES 13 在产物中存在）。

### 最小复现实例验证

```
11 repros: 0 DEFECT-REPRO, 11 NO-DEFECT, 0 ERROR
  - 8 DEFECT-REPRO (repro_01-08): with-keyword-drop 模式，R18 修复后全部 NO-DEFECT
  - 3 CTRL (repro_09-11): 无 keyword / 裸 ctx / 非 with CALL，确认非 with 路径不受影响
```

### 跨轮回归验证

- R17 minimal_repros: 10/10 NO-DEFECT（与 R17 一致，无回归）
- R17 目标 pyc zt_api.pyc: 100% (4/4)（与 R17 一致，无回归）

## 5. 算法 4 原则合规

- **自底向上归约**: ✓ 未改变
- **每块唯一归属**: ✓ 强化（KW_NAMES 随 CALL 归 with 上下文表达式，不丢失）
- **嵌套即抽象节点**: ✓ 未改变
- **入口引用语义**: ✓ 未改变

## 6. 反模式自检

- `_fix_` / `_merge_` / `_patch_` / `_fallback_` / `_hack_` / `_workaround_` / `_temp_` 前缀: **0 新增**（修复为白名单 +1 项，无新 helper 函数）
- 硬编码深度上限: **0 新增**
- 跨区域启发式: **0 新增**（修复为指令名白名单扩展，非实例特征）
- 后处理补丁: **0 新增**
- 针对特定 pyc 的硬编码绕过: **0 新增**

## 7. docstring 更新

`_generate_with` 方法 docstring 的「字节码一致性约束」段落新增 `[R18 fix]` 子段落（region_ast_generator.py:18603-18610），说明 with 上下文管理器调用的关键字参数保留链路、KW_NAMES 在 ctx_expr 中的收集依赖、对 region_analyzer._extract_with_items 的修复引用、算法原则合规性。`_extract_with_items` 的 ctx_expr 白名单处新增 `[R18 fix]` 行内注释（region_analyzer.py:8694-8701）。

## 8. 残留问题

### 本轮新增残留

- **trade_strategy_add if-drop / return-drop**（Defect 3，新发现）：WithRegion 的 cleanup_blocks / generated_blocks 误包含 with 语句之后的块（if 条件块 / return None 块）。`if strategy_lv2_name is not None: strategy_hub_name = ...` 的 if 守卫被丢弃，仅保留 body。最小复现：`with open(p,'r',encoding='utf-8') as f: ...; if b is not None: x = x + '_' + b`。根因与 R07 fix（post-body 块循环 block_to_region 归属守卫）同类但未覆盖。R19 修复目标。

### 不可修复残留

- **<module> Pattern R2**：原始 `from fly.common.enums import common, enums` 编译为 `IMPORT_FROM common; SWAP 2; POP_TOP` 优化器 artifact，无源码可复现，compare_bytecode 严格比较致无法匹配。

### 累计残留（跨轮，未变）

- Pattern T3/T2/A2/B/C/C2/E/F/M2/G3/R 等模式见各轮报告

### 下一轮建议

R19 修复 WithRegion cleanup 误消费 with 语句之后块（if-drop / return-drop）。修复后 trade_strategy_add 应达 100%，strategy.pyc 升级为 1/2=50% partial（<module> Pattern R2 不可修复）。修复方向：`region_analyzer.py` _extract_with_items / _identify_with_regions 的 cleanup_blocks 计算增加归属守卫，排除 with 语句之后的非 cleanup 块（参考 R07 fix 的 block_to_region 归属判定）。
