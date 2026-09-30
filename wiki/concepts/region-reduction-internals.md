---
type: concept
title: 区域归约算法内部机制（Region Reduction Internals）
tags:
  - code-kb
related:
  - "[[region-reduction-stages]]"
  - "[[ast-generation-lineages]]"
  - "[[core-cfg-region-analyzer--region-analyzer]]"
created: 2026-09-29
updated: 2026-09-29
kind: concept
sources:
  - pycdc.py
  - core/cfg/region_analyzer.py
  - core/cfg/region_ast_generator.py
---

# 区域归约算法内部机制

本页记录**算法本身**（不变量、优先级流水线、类型映射、已知失效模式），全部来自源码注释与实现，均带 `file:line` 锚点。

## 1. 调用链（`pycdc.py:71-118`）

```
pycdc.decompile(use_region=True)
  → build_cfg(code)                        # CFG
  → RegionASTGenerator(cfg).generate()     # 归约 → AST dict
  → CFGASTConverter().convert(ast_dict)    # dict → Python ast
  → CFGCodeGenerator().generate(py_ast)    # ast → 源码文本
  → compile(source)  # 语法校验，失败仅告警仍输出
```

要点：region 路线**不走** `parsers/ast_builder.py`；三条路线在 `pycdc.py:52-53` 由 `use_region` / `use_cfg` / `cfg_hybrid` 三参数分发。

## 2. 四条不可违反的核心原则（`region_analyzer.py:1342-1348`）

理论依据："No More Gotos"（Launez et al., 2013）+ 本仓归约约束。

1. **自底向上归约**：从最内层区域向外识别，不回溯修正。
2. **每块唯一归属**：任一基本块在任何层级只属于一个区域。
3. **嵌套即抽象节点**：子区域在父区域中表现为单个抽象节点。
4. **入口引用语义**：父区域的 then/else/body 引用**子区域入口块**，而非子区域全部块。

**禁令**：禁止跨区域/跨层次的启发式规则。遇到特例应回归归约本身修正，而不是加特判。

## 3. 识别优先级流水线（`analyze()`，`region_analyzer.py:1442-1495`）

```
Phase 1  低层结构（块级特征）
  TRY(异常表/SETUP_*) → LOOP(回边+支配树) → WITH → MATCH → ASSERT
  每步之间插入专门的合并/修正：
    _coalesce_split_try_except_finally_regions   # 拆分 try+finally 重组
    _identify_empty_body_finally_regions        # 编译器省略 try 范围表项的孤儿帧
    _coalesce_nop_prefix_loop_headers           # NOP 前缀的 loop header
Phase 2.5 peephole 预处理
    P1 模式（模块级三元 + RETURN_VALUE）释放值块，
    避免 MatchRegion 误识别把三元值块吃掉
Phase 2  高层表达式（消费 Phase 1 结果）
  CHAINED_COMPARE → BOOL_OP → TERNARY
  每个高层识别都把 Phase 1 的区域列表作为 existing_regions 传入，
  用于排除已被占用的块
Phase 3+  IF 条件区域 + 序列区域 + 区域层级装配
```

优先级理由（源码注释）：异常区域可跨越循环与条件，故最高；循环有回边需特殊处理，次高；其余依赖前两者。

## 4. 区域类型 → CFG 形态 → AST 映射表（`region_analyzer.py:1353-1372`）

| 区域类型 | 识别方法 | CFG 形态 / 算法 | AST 映射 |
|---|---|---|---|
| WHILE_LOOP | `_identify_loop_regions` | 回边 B→H（H 支配 B），自然循环体收集 | `While(test, body)`；header 含条件→`while cond`，否则 `while True` |
| FOR_LOOP | `_identify_loop_regions` | header 含 `FOR_ITER`/`GET_ANITER` | `For(target, iter, body)` |
| IF / IF_THEN_ELSE | `_identify_conditional_regions` | 两后继 A,B；最近公共支配后继 = merge；A→then, B→else；else 入口是条件块→elif | `If(test, body, orelse)` |
| IF_ELIF_CHAIN | `_identify_conditional_regions` | 嵌套 if 合并为 elif 链 | `If(test, [If(test,...)])` |
| TRY_EXCEPT | `_identify_try_except_regions` | 异常表 `co_exceptiontable`/`SETUP_*` 圈定受保护区；`PUSH_EXC_INFO`+`CHECK_EXC_MATCH`→except；`RERAISE`→finally | `Try(body, handlers, finalbody)` |
| WITH | `_identify_with_regions` | `BEFORE_WITH`/`WITH_EXCEPT_START` 配对 | `With(items, body)` |
| MATCH | `_identify_match_regions` | `MATCH`+`COMPARE_OP`+`POP_JUMP_IF_NONE` 链 | `Match(subject, cases)` |
| ASSERT | `_identify_assert_regions` | `POP_JUMP_IF_TRUE` + `RAISE_VARARGS(1)` | `Assert(test, msg)` |
| BOOL_OP | `_identify_boolop_regions` | and/or 短路：条件跳到下一分支 = 右操作数 | `BoolOp(op, [l, r])` |
| TERNARY | `_identify_ternary_regions` | 两路 `POP_JUMP_IF_*` 汇聚同一 merge | `IfExp(test, body, orelse)` |
| CHAINED_COMPARE | `_identify_chained_compare_regions` | 连续比较块，左值跨块复用 | `Compare(left, ops, comps)` |
| SEQUENCE | `_identify_sequence_regions` | 剩余线性块按前驱→后继拼接 | 语句序列 |

## 5. 角色标注体系（`BlockRole`，`region_analyzer.py:127-168`）

42 个角色分四组：循环（`LOOP_HEADER/CONDITION/BODY/ELSE/INIT/BACK_EDGE/CONDITION_RECHECK/EXIT`）、条件（`IF_CONDITION/THEN/ELSE/ELIF_CONDITION`）、异常（`TRY_BODY/EXCEPT_HANDLER/EXCEPT_STORE/FINALLY_BODY/TRY_ELSE`）、with/match、以及控制流终结（`CONTINUE/BREAK/RETURN/RETURN_NONE/RERAISE`）与纯跳转桩（`PURE_CONTINUE/PURE_BREAK/PURE_JUMP/TRIVIAL/NOP`）。

`BlockSemantics`（`region_analyzer.py:191-201`）把角色、回边信息、有效指令、语句边界、所属区域类型打包成 dataclass，是 S2 阶段产物。

## 6. 多态分发替代 isinstance 分支（`Region` 基类，`region_analyzer.py:272-310`）

区域间的类型差异通过基类上的 19 个覆写点消解，避免在识别器里散落 `isinstance`：

- 结构化角色：`annotate_structural_roles`、`annotate_cond_recheck`、`precompute_analysis`、`get_score_merge_block`
- 块归属：`is_block_entry`、`contains_block`、`is_block_in_body`、`else_block_conflict`、`get_offset_range`
- if/分支协调：`get_if_branch_boundary_stop`、`get_if_body_blocks`、`get_compactness_successors`、`get_else_blocks_for_merge`
- ternary/boolop 协调：`can_be_ternary_header`、`interrupts_boolop_forward_chain`
- with/try/match 协调：`get_with_body_orphan_instructions`、`try_except_absorb_split_from`、`should_merge_with`、`preserves_against_nested_match`

## 7. 已知失效模式与修复（知识密度最高的部分）

### 7.1 孤儿块释放（`region_analyzer.py:1410-1425`）

内部区域被过滤掉（entry 在外层区 blocks 中）时，其 merge 点等块可能既不属于任何顶级区域、也不属于自身区域 → 称为"孤儿"，会在最终 AST 中丢失。释放发生在 `RegionASTGenerator.generate()` 顶部（归约→AST 映射的桥接），把孤儿块补成独立 BASIC 区域。

**te046 修复（2026-07-14，突破 100% 基线）**：原逻辑"块所属区域非顶级 + 块不在任何顶级区 blocks → 判为孤儿"会误伤合法嵌套子区域的块。现增加"顶级祖先"检查：`parent` 链上存在顶级祖先则为合法嵌套块，不释放。该修复消除了虚假 `if True: pass` 输出。

### 7.2 yield-from/await 三元吞并（`region_analyzer.py:1501-1514`）

`yield from (ternary).items()` / `await (ternary)` 的字节码是 `SEND/YIELD_VALUE/RESUME/JUMP_BACKWARD_NO_INTERRUPT` 轮询循环 + 三元结构。`LoopRegion`（`is_yield_from_loop`）与 `TernaryRegion`（`merge_extra_blocks`）块集重叠，违反"每块唯一归属"。

处置：轮询循环块归属 TernaryRegion 而非 LoopRegion——因为它是 yield-from/await 协议的一部分；若留在 LoopRegion，`_generate_ternary` 的 Pattern 4/5/7 会先标记轮询块已生成，导致三元无法重建，整个表达式退化为 `None`。

### 7.3 match 误识别 vs 三元（Phase 2.5，`region_analyzer.py:1458-1475`）

模块级三元表达式 + `RETURN_VALUE` 会被 match 守卫误识别。P1 peephole 预处理在 Phase 1 之后、Phase 2 之前扫描并释放 `value_blocks_to_release`，保证三元识别阶段看到正确的 match 集合。

### 7.4 栈效应静态分析（`region_analyzer.py:1244-1300`）

`_stack_effect(instr) -> (push, pop)` 用于判断 merge 块的 `COMPARE_OP` 是否消费三元结果。**Python 3.11 特例**：`LOAD_ATTR` 的 arg 只是 `co_names` 索引，LSB 无方法标志含义；方法调用走独立 `LOAD_METHOD`（压 NULL+bound method、弹 1）。3.12+ 才用 `arg&1` 区分。

## 8. 规模现状与迭代代价

- 识别侧 `RegionAnalyzer` 27,175 行 / 212 方法，生成侧 `RegionASTGenerator` 51,488 行 / 248 方法。
- 前 10 大方法占两个 god class 的 28%，其中 `_generate_block_statements_body` 4,022 行读 42 个实例字段、`_generate_ternary` 3,639 行读 44 个。
- 30+ 轮迭代（`.trae/specs/` 27 个 spec 目录，round74 进行中）把 mandated 尺推到 6,540/6,617 = 98.84%、official 尺 5,717/5,746 = 99.50%、严格缺陷 75。剩余失败单元按族分布：F-ABSORB 67、F-PAD 8、F-POLARITY 1、F-OTHER 1。
- **PRD-1 结论（round73 定量判决）**：用户裁定的"嵌套 try-except 是根因"仅对 11/77 失败单元成立，65/77 首个分歧在异常区**外**；87 失败单元中原 pyc 有异常表 44 / 无 43，异常表有无与失败无相关。下一轮（round74）转 F-ABSORB orphan-child 发射。
