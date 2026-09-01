# Round 04 修复报告 — 区域归约反编译迭代

**日期**: 2026-08-29
**提交前缀**: `rbi-r04:`
**状态**: 303 ok / 99 partial（G1 交付，本轮 0 翻转）

---

## 1. 本轮目标与交付

本轮核心交付为 **G1（yield 在循环体内丢失）** 的结构性修复，落点在
`core/cfg/region_ast_generator.py` 的 `_loop_extract_self_loop_stmts` /
`_loop_process_header_instructions` / `_loop_extract_pre_stmts_from_instrs` 三处
header 块处理路径（P1–P8 形态，含 id_gen/`while True` yield-first/yield-last、
`for` yield、yield-in-if、多 yield while、yield 赋值等）。

修复机理（无启发式补丁、无单文件特判）：
- 用**栈深度归约**定位 `while` 自循环 header 回边条件的「重检起点」，
  替代旧「找最后 STORE 后向前扩展」的脆弱启发式（旧逻辑遇到首个
  `YIELD_VALUE` 即截断体，丢弃后续 yield）。
- 按区域归约算法原则 2（每块唯一归属）为新增值栈语句插入 `YIELD_VALUE`
  边界处理，镜像 `_build_statements_from_instructions` 的 yield 协议清理
  （`RESUME + POP_TOP` 作为 yield 协议收尾），与既有的 yield 重建路径一致。

## 2. 验证结果

- **最小复现集（Round 04 `test_engineer/minimal_repros/`）**：
  `repro_01`–`repro_07` 全 PASS（含对照组 4/4：`control_simple_assign`、
  `control_if_else_return`、`control_try_except`、`control_aug_attr`）。
  即 `run_repros.py` 的「编译→反编译→重编译→递归 co_code 比对」全部一致。
- **quotation.pyc**：单文件验证通过（字节码零退化）。
- **全量回归（3 块，覆盖 99 个 partial 文件）**：G1 叠加后 **0 翻转**。

## 3. 翻转目标排查（本轮关键工作）

对全部 99 个 partial 文件做 `first_diff` 模式聚合与「最接近 ok」排序，
逐一排查可翻转候选。结论：**当前语料中不存在干净、单点、可安全翻转的目标**。

### 3.1 仅 1 个 mismatch 且 true_diffs≤2 的文件（共 3 个，全部不可翻转）

| 文件 | 函数 | 问题 | 判定 |
|---|---|---|---|
| `IQCommon/data/local_finance.pyc` | `<lambda>` | `POP_JUMP_IF_TRUE` vs `POP_JUMP_IF_FALSE`（极性反转） | **非规范字节码，不可翻转** |
| `IQEngine/plugins/plugin_fly_data/fly_api/base.pyc` | `get_instance` | COPY 残留栈导致下标赋值操作数错位 | **深层 COPY-leftover，高风险** |
| `fly/common/user_error.pyc` | `<module>` | 模块级 NOP / 多余 `RETURN_VALUE` | **模块级编译产物，难** |

**local_finance 详细论证**（已用 3.11.7 实测证伪）：
- 原始 lambda 第 6 条 = `POP_JUMP_FORWARD_IF_TRUE 112`（跳向 `x['company_type']` = true 分支）。
- CPython 3.11 **规范** `IfExp` **永远**编译为 `POP_JUMP_IF_FALSE`（已用
  `str(int(...)) if C else x['company_type']` 与 `x['company_type'] if C else str(int(...))`
  两种顺序实测确认，二者均得 `IF_FALSE`）。
- 因此原始 pyc 的 `IF_TRUE` 是**非规范编码**（推断由较早 3.11.x（3.11.0/3.11.1）
  的 inverted-ternary codegen 生成，而验证用 3.11.7 已不再产生）。
- 验证器以 3.11.7 重编译，**无任何标准 Python 源**能复现 `IF_TRUE 112`，
  故此 lambda 字节码永不可能对齐 → 排除为翻转目标。

### 3.2 其余「接近 ok」文件（true_diffs ≥ 3，均为深层控制流归约问题）

- `fly/common/convert.pyc::getchnstr` (td=3)：连续同目标跳转应归约为
  **扁平 `or` 条件**，却被嵌套为 `if not A: if B or C:`，属 区域归约的
  控制流合并难题（G5 候选）。
- `fly/common/market_time.pyc` (td=10)、`fly/simtradding/ptradeOptionAccount.pyc` (td=12)
  等：均为 19–429 量级 true_diffs，首差落在 `JUMP_FORWARD/LOAD_FAST`、
  `POP_JUMP_IF_NOT_NONE`→`POP_JUMP_IF_TRUE` 等，是函数级控制流/条件重构缺陷，
  非单点可修。
- `IQData/plugins/plugin_system_db_tools/db_base.pyc` (td=126)、
  `fly/oauthenticator/oauth2.pyc` (td=154)：首差为
  `POP_JUMP_IF_NOT_NONE`→`POP_JUMP_IF_TRUE`，即 `a if a is not None else b`
  被退化为 `a if a else b`（丢失 `is not None` 语义，G6 候选），但因伴随
  大量其它 mismatch，本轮修此家族亦不能翻转。

## 4. 反模式自检

- 本轮新增函数/分支**无** `def _fix_*` / `_patch_*` / `_hack_*` 等反模式前缀。
- G1 修复严格遵循区域归约算法 4 原则（自底向上归约 / 每块唯一归属 /
  嵌套即抽象节点 / 入口引用语义），以栈效应判据替代硬编码深度与目标特判。

## 5. 结论与后续轮次规划

Round 04 交付了真实的 G1 正确性提升（yield 在循环中不再丢失，复现集 7/7 PASS），
但因语料剩余 partial 文件**均含非规范字节码或深层控制流归约缺陷**，本轮未能
翻转任何文件（仍为 303 ok / 99 partial）。遵守「不强行伪造翻转、不引入启发式补丁」
原则，未对 3 个 1-mismatch 文件做冒险修改。

**后续轮次目标家族（按预期收益排序）**：
- **G4 — COPY-leftover 下标/属性赋值**：`fly_api/base.pyc::get_instance` 的
  `r = store_class()`（COPY 1 残留栈）未被后继 `STORE_SUBSCR` 复用为值操作数，
  导致 `self.instance_dict[store_class.__name__] = r` 错乱为
  `store_class[None] = self.instance_dict`。需在下标/属性赋值路径做
  「COPY+STORE 残留栈 → 重载为 LOAD_FAST var」的归约（风险较高，需广域回归）。
- **G5 — 连续同目标跳转归约扁平 `or`**：`convert.pyc::getchnstr` 类控制流合并。
- **G6 — `is not None` 三元/条件语义保留**：`POP_JUMP_IF_NOT_NONE` 应保留
  `is not None` 语义而非退化为真值判断。
- **G2 — 闭包自由变量 LOAD_DEREF→LOAD_GLOBAL / STORE_DEREF→STORE_FAST**：
  独立家族，需在变量解析路径修正。

> 注：local_finance.pyc 的 `<lambda>` 因原始 pyc 为非规范 3.11.0/3.11.1 字节码，
> 在 3.11.7 验证范式下**永不可字节码对齐**，标记为已知非目标，不计入迭代。
