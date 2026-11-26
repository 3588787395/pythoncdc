# B1 — J 空间扩充设计（104 条 open 规则，仅设计不实现）

- 产出者：ROW4 阶段二 B1（fix subagent）；时间：2026-11-26；HEAD r215=52128723 + A1/A2 未提交工作树
- 输入基线：阶段一四项裁决（ROW4_RULE_COVERAGE.md）；`b1_rules_104.json`（104 规则全字段）；rebased G4 读数（264 规则，proved=144/open=120，见 A3 报告）；judgment_space v2 schema（round9，1556 条目）
- 范围：(c)31 + false_at_site 26 + neg_missing 26 + guard_only 21 = **104 条 open 规则**；另加 1 条特例 RULE-a310f7ea600b（PREP_RERAISE_STAR，A1 修复后转 neg_missing，见 §6）
- **本文件仅为设计文档。实现需父代理批准后于阶段三执行。**

## 1. 目标

为 104 条 open 规则设计 judgment_space 新条目（新 p_j 源文件 → 3.11 pyc → 引擎复跑 → rule_proof_check v8_b1+SN 判定），使每条规则获得「正见证 + 严格负见证」或其结构豁免，最终 G4 读数收敛到：denominator 249（282 − 15(a) − 18(b 已删)），open 104→最小。

## 2. 设计原则

1. **条目最小化**：一条新条目尽量同时覆盖多条规则（同锚点成员规则合并；表达式全家桶 N01 一条覆盖 28 条规则的真评估需求）。18 个新条目族覆盖 104 条中的 96 条。
2. **复用优先**：负见证优先从现有 1556 条目中挖掘（复用扫描：对每条 neg_missing 规则，在现有条目的运行记录中找「锚点可达、谓词假、条目内规则从未真」的纯负条目），零成本项先落袋；仅缺口再造新条目。
3. **形态正交**：每条目一个明确 expected_label（form/variant/host/depth），p_j 草案一次只表达一族形态；避免「一条目测一切」导致诊断退化。
4. **验证闭环**：每批新 pyc 先跑 `rule_proof_check --counting b1 --also-legacy --structural-negative`，按 rule 的 measurement（true_evaluations/false_evaluations/anchors_located）迭代 p_j，直到目标规则拿到正/负见证；不达则按 §7 风险条目升级处理。
5. **不污染既有判据**：新条目追加到 judgment_space（v2 schema），不改 universe_v6/manifest_v3 结构；G4 复测以 rebased universe（264 规则）为准。

## 3. 现状读数（rebased，264 规则）

| 组 | 规则数 | open 原因 | 需要什么 |
|---|---|---|---|
| (c)31 | 31 | no_occurrence_in_J | 守卫链走通且成员测试处出现目标成员（每条 class_c_evidence 已给出精确链）|
| false_at_site | 26 | predicate_false_at_site | 谓词在锚点处至少一次求值为真 |
| neg_missing | 26 | negative_witness_missing | 严格负见证：一个条目内锚点可达、谓词假、该规则条目内从未真 |
| guard_only | 21 | guard_only_symbol_not_observed | 守卫真时规则自身符号被观测到（b1 计数 adjudication 2）|

## 4. 新条目族（18 个）

| 条目 | form | host | depth | 覆盖规则数 | 用途 |
|---|---|---|---|---|---|
| N01 | expr-medley | function-body | d1 单层 | 28 | 表达式全家桶（单函数） |
| N02 | plain-negative | function-body | d1 单层 | 0 | 极简负证条目（仅常量/返回） |
| N03 | nested-closure | function-body | d2 双层 | 7 | 嵌套函数/类体/闭包/删除 |
| N04 | gen-yield | generator-func-body | d1 单层 | 3 | 生成器 yield/yield from |
| N05 | async-await | async-func-body | d1 单层 | 3 | 异步 await/async for/async with |
| N06 | bigfunc-extended-arg | function-body | d1 单层 | 1 | 大函数强制 EXTENDED_ARG |
| N07 | none-backjump | function-body | d1 单层 | 2 | None 检查回跳循环 |
| N08 | match-patterns | function-body | d1 单层 | 2 | match 序列/映射/类/星号模式 |
| N09 | walrus-star-unpack | function-body | d1 单层 | 11 | 海象/星号解包/合并/复合赋值 |
| N10 | with-unpack | function-body | d1 单层 | 3 | with 绑定+解包+多项 |
| N11 | try-handler-battery | function-body | d2 双层 | 5 | try 外层 handler/except*/except-break/finally 组 |
| N12 | comp-battery | function-body | d2 双层 | 9 | 推导式电池（嵌套/多 for/多 if/海象/外层赋值） |
| N13 | ternary-boolop-chain | function-body | d1 单层 | 15 | 三元/布尔链/链式比较 |
| N14 | store-shapes | module-level | d1 单层 | 10 | 存储形态电池（注解/全局/链式/多目标/删除） |
| N15 | elif-chain-marker | function-body | d2 双层 | 6 | elif 链嵌套标记（六成员旗舰条目） |
| N16 | print-expr-single | module-level | d1 单层 | 1 | PRINT_EXPR（single 模式编译） |
| N17 | return-successor | function-body | d1 单层 | 2 | return 后继带多条指令 |
| N18 | literal-region | function-body | d1 单层 | 4 | 字面量构建区域（STORE 邻接） |

新条目计数：**18 族**（N02/N06/N16 含实现期变体，实际 p_j 约 20-22 个文件）。
预计新增 jspace 条目 ≈ 20-24（部分族拆 host/depth 变体以保持形态正交）。

### p_j 草案（关键条目全文）

#### N01 — 表达式全家桶（单函数）

```python
def expr_medley(a, b, c):
    lam = lambda x: x + 1
    lc = [x for x in range(3)]
    sc = {x for x in range(3)}
    dc = {x: x for x in range(3)}
    ge = (x for x in range(3))
    fs = f"{a!r:>10} {b} {c}"
    sb = a[1]; sl = a[1:2]
    is1 = a is None; is2 = a is not None
    nt = not a; ng = -a; ps = +a; iv = ~a
    bo = a and b or c; cp = (a < b) <= (b < c)
    tu = (a, b); st = {a, b}; di = {a: b}; li = [a, b]
    at = a.real; ca = lam(a)
    for it in a: pass
    return fs
```

覆盖 cg 表达式分派系（3780-3969、2148-2174、4032-4055）与 agv2 一元/跳转系。

#### N15 — elif 链嵌套标记（六成员旗舰条目）

```python
def chain(x, seq):
    if x == 1:
        while x > 0: x -= 1            # While
        for i in seq: pass             # For
    elif x == 2:
        try:
            pass
        except Exception: pass         # Try
        match x:
            case 1: pass               # Match
    elif x == 3:
        if x > 2:
            while True:
                if x: break            # Break
                continue               # Continue
    else:
        pass
```

核心约束（agv2:13416 extract_elif_chain）：嵌套 def；while current_nodes；首个 If 带 _is_nested_if 标记（L13446）；if_index <= 2（L13452）；range(if_index) 迭代。六成员规则同锚共享一条目。

#### N12 — 推导式电池（嵌套/多 for/多 if/海象/外层赋值）

```python
def cb(data):
    n = 3
    a = [[y for y in row] for row in data]
    b = [x for x in data if x > 1 if (m := x) < 9]
    c = {k: v for k, v in data.items() if k in (1, 2)}
    d = (x * 2 for x in data for y in data)
    out = [(last := x) for x in data]
    return a, b, c, d, out, m, last
```

_APPEND_OPS 需主解析失败的推导式回退（病态形式：超深嵌套或含非常规命名），实现期迭代。

#### N13 — 三元/布尔链/链式比较

```python
def tb(a, b, c):
    x = a if (b and c) else (c if b else a)
    y = (a or b) if (b or c) else (a and c)
    z = 1 if a < b < c else 2
    w = x if y else z if x else y
    v = (a and b) or (c and x) or (b and y)
    u = x if (a or b or c) else y if a else z
    return v if u else w
```

去重后 15 条。三元布尔条件需 condition_chain_blocks>1 且无嵌套条件表达式（rag:55864/55971/55973）。

其余条目 p_j 草案见 `b1_design_data.json`（字段 pj/note/rules）。

## 5. 规则 → 条目映射总表（104 条）

| # | 组 | rule_id | symbol | 锚点 | pattern_class | 条目 | 负证/备注 |
|---|---|---|---|---|---|---|---|
| 1 | c31 | RULE-010c1b2cf1d7 | Break | ast_generator_v2.py:13459 | mixed:ast_marker_eq,ast_marker_in_set | N15 | （守卫链证据见 §5 附表） |
| 2 | c31 | RULE-6ce83d58fb8b | Continue | ast_generator_v2.py:13459 | mixed:ast_marker_eq,ast_marker_in_set | N15 | （守卫链证据见 §5 附表） |
| 3 | c31 | RULE-681e794c6afb | For | ast_generator_v2.py:13459 | mixed:ast_marker_eq,ast_marker_in_set | N15 | （守卫链证据见 §5 附表） |
| 4 | c31 | RULE-ae6695fa4fca | Match | ast_generator_v2.py:13459 | mixed:ast_marker_eq,ast_marker_in_set | N08；亦见 N15 | （守卫链证据见 §5 附表） |
| 5 | c31 | RULE-d1e1d76ee83d | PRINT_EXPR | ast_generator_v2.py:11556 | opcode_in_set | N11；亦见 N16 | （守卫链证据见 §5 附表） |
| 6 | c31 | RULE-cbb06f6eb54d | Try | ast_generator_v2.py:13459 | mixed:ast_marker_eq,ast_marker_in_set | N11；亦见 N15 | （守卫链证据见 §5 附表） |
| 7 | c31 | RULE-6048d12971c9 | While | ast_generator_v2.py:13459 | mixed:ast_marker_eq,ast_marker_in_set | N15 | （守卫链证据见 §5 附表） |
| 8 | c31 | RULE-8fc89ce420ac | _APPEND_OPS | ast_generator_v2.py:3330 | opcode_in_named_set | N12 | （守卫链证据见 §5 附表） |
| 9 | c31 | RULE-e950c889b956 | _BIND_STORE_OPS | region_analyzer.py:16977 | opcode_in_named_set | N10 | （守卫链证据见 §5 附表） |
| 10 | c31 | RULE-a6c5590d7e93 | _BIND_UNPACK_OPS | region_analyzer.py:16990 | opcode_in_named_set | N10 | （守卫链证据见 §5 附表） |
| 11 | c31 | RULE-9890ff971e58 | _CHECK_OPS_r08b | region_ast_generator.py:41716 | opcode_in_named_set | N11 | （守卫链证据见 §5 附表） |
| 12 | c31 | RULE-996e7c860ca0 | _DELETE_NAME_OPS | region_ast_generator.py:65190 | opcode_in_named_set | N14 | （守卫链证据见 §5 附表） |
| 13 | c31 | RULE-b2e2ae122393 | _NOISE | region_analyzer.py:8235 | opcode_in_named_set | N11 | （守卫链证据见 §5 附表） |
| 14 | c31 | RULE-cd390e67679f | _STORE_CHK_R02 | region_ast_generator.py:54405 | opcode_in_named_set | N13 | （守卫链证据见 §5 附表） |
| 15 | c31 | RULE-31256e3fd90e | _STORE_OPS_R2P02 | region_ast_generator.py:55971 | opcode_in_named_set | N13 | （守卫链证据见 §5 附表） |
| 16 | c31 | RULE-532506346aa4 | _b107_store_ops | region_ast_generator.py:76425 | opcode_in_named_set | N09 | （守卫链证据见 §5 附表） |
| 17 | c31 | RULE-f3e459303717 | _b33_noise | region_ast_generator.py:14704 | opcode_in_named_set | N05 | （守卫链证据见 §5 附表） |
| 18 | c31 | RULE-d7cb17e16c13 | _bounce_names | comprehension_generator.py:4064 | opcode_in_named_set | N12 | （守卫链证据见 §5 附表） |
| 19 | c31 | RULE-eea05924d17d | _cmp_ops_set | region_ast_generator.py:22175 | opcode_in_named_set | N13 | （守卫链证据见 §5 附表） |
| 20 | c31 | RULE-54c66455c6d9 | _cso | comprehension_generator.py:298 | opcode_in_named_set | N12 | （守卫链证据见 §5 附表） |
| 21 | c31 | RULE-51fbefc39b4b | _ctx_value_ops | region_ast_generator.py:46465 | opcode_in_named_set | N10 | （守卫链证据见 §5 附表） |
| 22 | c31 | RULE-ba395f773988 | _frame_bookkeeping | comprehension_generator.py:856 | opcode_in_named_set | N12；亦见 N17 | （守卫链证据见 §5 附表） |
| 23 | c31 | RULE-eb169da1a935 | _hb_noise_ops | region_ast_generator.py:44134 | opcode_in_named_set | N11 | （守卫链证据见 §5 附表） |
| 24 | c31 | RULE-9eea46812142 | _jump_ops | comprehension_generator.py:1902 | opcode_in_named_set | N12 | （守卫链证据见 §5 附表） |
| 25 | c31 | RULE-969c990c53ef | _mt_store_ops | region_ast_generator.py:76740 | opcode_in_named_set | N09 | （守卫链证据见 §5 附表） |
| 26 | c31 | RULE-5c5d7b71d2bb | _skip_ops | region_ast_generator.py:78499 | opcode_in_named_set | N14 | （守卫链证据见 §5 附表） |
| 27 | c31 | RULE-048e69dc7408 | _v105_sub_attr | region_ast_generator.py:55973 | opcode_in_named_set | N13 | （守卫链证据见 §5 附表） |
| 28 | c31 | RULE-e8aa239b163e | _yf_store_ops | region_ast_generator.py:7870 | opcode_in_named_set | N04 | （守卫链证据见 §5 附表） |
| 29 | c31 | RULE-a8dffc095ffd | attr | region_ast_generator.py:53333 | ast_marker_eq | N09 | （守卫链证据见 §5 附表） |
| 30 | c31 | RULE-26ee397f261c | skip_ops | region_ast_generator.py:78444 | opcode_in_named_set | N14 | （守卫链证据见 §5 附表） |
| 31 | c31 | RULE-e255ab564575 | subscr | region_ast_generator.py:53367 | ast_marker_eq | N09 | （守卫链证据见 §5 附表） |
| 32 | pred_false | RULE-4773744d80c4 | <lambda> | code_generator.py:2396 | ast_marker_eq | N01 |  |
| 33 | pred_false | RULE-84fd5ec5ec83 | Await | code_generator.py:3969 | ast_marker_eq | N05 |  |
| 34 | pred_false | RULE-d2b392e7ea86 | BoolOp | code_generator.py:3960 | ast_marker_eq | N01 |  |
| 35 | pred_false | RULE-e9cd9be060c0 | Compare | code_generator.py:3966 | ast_marker_eq | N01 |  |
| 36 | pred_false | RULE-d46e58a97d98 | Iter | code_generator.py:3790 | ast_marker_eq | N01 |  |
| 37 | pred_false | RULE-bed4750b6923 | SETUP_ANNOTATIONS | region_ast_generator.py:940 | opcode_eq | N14 |  |
| 38 | pred_false | RULE-f6348059bc55 | SET_UPDATE | ast_generator_v2.py:1655 | mixed:opcode_eq,opcode_in_set | N09 |  |
| 39 | pred_false | RULE-1dc9e2f98754 | Slice | code_generator.py:3930 | ast_marker_eq | N01 |  |
| 40 | pred_false | RULE-097f2c50ba6b | UNARY_INVERT | region_ast_generator.py:51807 | mixed:opcode_eq,opcode_in_set | N01；亦见 N13 |  |
| 41 | pred_false | RULE-da070a431a90 | UNARY_NEGATIVE | ast_generator_v2.py:6571 | mixed:opcode_eq,opcode_in_set | N01 |  |
| 42 | pred_false | RULE-b85ddfe6b1a8 | UNARY_POSITIVE | ast_generator_v2.py:6571 | mixed:opcode_eq,opcode_in_set | N01 |  |
| 43 | pred_false | RULE-09e890625a53 | UnaryOp | code_generator.py:3963 | ast_marker_eq | N01 |  |
| 44 | pred_false | RULE-3114624d4364 | Yield | code_generator.py:448 | mixed:ast_marker_eq,ast_marker_in_set | N04 |  |
| 45 | pred_false | RULE-0453cb2cf048 | YieldFrom | code_generator.py:456 | mixed:ast_marker_eq,ast_marker_in_set | N04 |  |
| 46 | pred_false | RULE-b6cb0f6833d9 | _LITERAL_BUILD_OPS | region_ast_generator.py:73958 | opcode_in_named_set | N09；亦见 N18 |  |
| 47 | pred_false | RULE-4982a763071c | _STORE_CHK_P21 | region_ast_generator.py:54599 | opcode_in_named_set | N13 |  |
| 48 | pred_false | RULE-d0e49b29cc07 | _TRUE_POLARITY_COND_JUMP_OPS | region_ast_generator.py:56308 | opcode_in_named_set | N13 |  |
| 49 | pred_false | RULE-eb09655713ec | _WALRUS_INTEGRATING_OPS | region_ast_generator.py:73960 | opcode_in_named_set | N09 |  |
| 50 | pred_false | RULE-938087af729e | __NESTED_FUNC__ | code_generator.py:4115 | ast_marker_eq | N03 |  |
| 51 | pred_false | RULE-4743f0da62f0 | _b113_stop_ops | comprehension_generator.py:2379 | opcode_in_named_set | N12 |  |
| 52 | pred_false | RULE-e4932ccfc508 | _b68_machinery | region_ast_generator.py:5399 | opcode_in_named_set | N13 |  |
| 53 | pred_false | RULE-1576dfcf29af | _closure_setup | comprehension_generator.py:554 | opcode_in_named_set | N03；亦见 N12 |  |
| 54 | pred_false | RULE-aca0cb9d01d5 | _kop_names | comprehension_generator.py:3977 | opcode_in_named_set | N12 |  |
| 55 | pred_false | RULE-8b54bff8cdbb | _lit_skip_ops | region_ast_generator.py:73951 | opcode_in_named_set | N09；亦见 N18 |  |
| 56 | pred_false | RULE-51cc986d9724 | _pad | comprehension_generator.py:6301 | opcode_in_named_set | N12 |  |
| 57 | pred_false | RULE-1ebd3fdc3786 | _pre_store_ops | region_ast_generator.py:59052 | opcode_in_named_set | N13；亦见 N18 |  |
| 58 | guard_only | RULE-38d1a1fef6a0 | DELETE_DEREF | region_analyzer.py:2463 | opcode_in_set | N03 |  |
| 59 | guard_only | RULE-8a6101820c9d | DELETE_GLOBAL | region_analyzer.py:23701 | opcode_in_set | N03；亦见 N14 |  |
| 60 | guard_only | RULE-efc4bb08d567 | DELETE_NAME | ast_generator_v2.py:22405 | opcode_in_set | N03 |  |
| 61 | guard_only | RULE-33f06058607b | DictComp | code_generator.py:3780 | mixed:ast_marker_eq,ast_marker_in_set | N01 |  |
| 62 | guard_only | RULE-9b74da19b3e2 | EXTENDED_ARG | region_analyzer.py:4837 | opcode_in_set | N06 |  |
| 63 | guard_only | RULE-2e321a33507c | FormattedValue | code_generator.py:3935 | mixed:ast_marker_eq,ast_marker_in_set | N01 |  |
| 64 | guard_only | RULE-00f0d5ffaaff | GET_LEN | ast_generator_v2.py:21495 | mixed:opcode_eq,opcode_in_set | N08 |  |
| 65 | guard_only | RULE-014265ded990 | GenExpr | code_generator.py:3788 | mixed:ast_marker_eq,ast_marker_in_set | N01 |  |
| 66 | guard_only | RULE-40c5ed4fe165 | GeneratorExp | code_generator.py:3786 | mixed:ast_marker_eq,ast_marker_in_set | N01 |  |
| 67 | guard_only | RULE-179dc43c132e | IS_OP | ast_generator_v2.py:2748 | mixed:opcode_eq,opcode_in_set | N01 |  |
| 68 | guard_only | RULE-823cae0aab30 | JoinedStr | code_generator.py:3932 | mixed:ast_marker_eq,ast_marker_in_set | N01 |  |
| 69 | guard_only | RULE-b620fe7fb512 | LOAD_CLASSDEREF | ast_generator_v2.py:1103 | opcode_in_set | N03 |  |
| 70 | guard_only | RULE-1e003061d4c8 | LOAD_DEREF | ast_generator_v2.py:1103 | opcode_in_set | N03 |  |
| 71 | guard_only | RULE-bfbc22d0d1e3 | Lambda | code_generator.py:361 | mixed:ast_marker_eq,ast_marker_in_set | N01 |  |
| 72 | guard_only | RULE-2331b38d9765 | ListComp | code_generator.py:3782 | mixed:ast_marker_eq,ast_marker_in_set | N01 |  |
| 73 | guard_only | RULE-639e08245c2d | POP_JUMP_BACKWARD_IF_NONE | ast_generator_v2.py:1410 | mixed:opcode_eq,opcode_in_set | N01；亦见 N07 |  |
| 74 | guard_only | RULE-1c5bd7459d99 | POP_JUMP_BACKWARD_IF_NOT_NONE | ast_generator_v2.py:1372 | mixed:opcode_eq,opcode_in_set | N01；亦见 N07 |  |
| 75 | guard_only | RULE-6cc7b6a37fd5 | SET_ADD | ast_generator_v2.py:5237 | opcode_in_set | N01 |  |
| 76 | guard_only | RULE-1ac0b3bb7543 | SetComp | code_generator.py:3784 | mixed:ast_marker_eq,ast_marker_in_set | N01 |  |
| 77 | guard_only | RULE-f1e6481a06fe | Subscript | code_generator.py:3910 | mixed:ast_marker_eq,ast_marker_in_set | N01 |  |
| 78 | guard_only | RULE-762ec4ca09c6 | UNARY_NOT | ast_generator_v2.py:6571 | mixed:opcode_eq,opcode_in_set | N01 |  |
| 79 | neg_missing | RULE-8637d89b4417 | Attribute | code_generator.py:4032 | mixed:ast_marker_eq,ast_marker_in_set | N01 | 复用扫描负证：现有条目中锚点可达且 Attribute 为假者（候选 JS-FSTRING-013、JS-ANNASSIGN-001） |
| 80 | neg_missing | RULE-87685c80e83d | CACHE | ast_generator_v2.py:2666 | mixed:opcode_eq,opcode_in_set | — | ⚠ 同上（CACHE false=267 但条目内混真）：CACHE 内联缓存遍布码流，纯负条目可能不存在；备选：结构负证豁免或 N02b 窄窗口条目 |
| 81 | neg_missing | RULE-7437333913d0 | Dict | code_generator.py:4055 | mixed:ast_marker_eq,ast_marker_in_set | N01 | 复用扫描负证：JS-IFEXP-003 等（无 Dict 节点路径） |
| 82 | neg_missing | RULE-ed5bec7d7a05 | LOAD_CONST | ast_generator_v2.py:1062 | mixed:opcode_eq,opcode_in_set | — | ⚠ 已有 false=135 但无纯负条目（LOAD_CONST 几乎处处为真）：复用扫描优先，若无纯负条目则造 N02b（LOAD_CONST 稀疏窗口）或申请结构负证豁免 |
| 83 | neg_missing | RULE-ec53116b4211 | List | code_generator.py:2174 | mixed:ast_marker_eq,ast_marker_in_set | N01 | 负证候选：N02 极简条目（无 List/Starred） |
| 84 | neg_missing | RULE-c214919432c0 | Name | code_generator.py:2148 | mixed:ast_marker_eq,ast_marker_in_set | — | 负证候选：N02 常量-only 变体（2148 处无 Name 求值） |
| 85 | neg_missing | RULE-e7701666d7b5 | RESUME | ast_generator_v2.py:2662 | mixed:opcode_eq,opcode_in_set | — | ⚠ RESUME false=131 但无纯负条目：复用扫描，失败则结构负证豁免 |
| 86 | neg_missing | RULE-2b6f0dcd703d | RETURN_VALUE | ast_generator_v2.py:1877 | mixed:opcode_eq,opcode_in_set | — | ⚠ RETURN_VALUE false=141 但无纯负条目：复用扫描，失败则结构负证豁免 |
| 87 | neg_missing | RULE-db3c378f2dad | STORE_ATTR | ast_generator_v2.py:1038 | mixed:opcode_eq,opcode_in_set | N09 | 复用扫描负证：JS-ASSERT-010 |
| 88 | neg_missing | RULE-5949b5021f68 | STORE_DEREF | ast_generator_v2.py:920 | opcode_in_set | N14 | 复用扫描负证：JS-AUGASSIGN-006（STORE_DEREF 假） |
| 89 | neg_missing | RULE-4f50e56b6e25 | STORE_FAST | ast_generator_v2.py:920 | mixed:opcode_eq,opcode_in_set | N14 | 复用扫描负证：JS-AUGASSIGN-006 |
| 90 | neg_missing | RULE-e77fbe9ddbee | STORE_GLOBAL | ast_generator_v2.py:920 | opcode_in_set | N14 | 复用扫描负证：JS-AUGASSIGN-006 |
| 91 | neg_missing | RULE-840c719d57c6 | STORE_NAME | ast_generator_v2.py:920 | opcode_in_set | N14 | 复用扫描负证：JS-AUGASSIGN-006 |
| 92 | neg_missing | RULE-6997aa6c7097 | STORE_SUBSCR | ast_generator_v2.py:999 | mixed:opcode_eq,opcode_in_set | N09 | 复用扫描负证：JS-ASSERT-010 |
| 93 | neg_missing | RULE-2ad1ffa97019 | Set | code_generator.py:4047 | mixed:ast_marker_eq,ast_marker_in_set | N01 | 复用扫描负证：JS-IFEXP-003 等 |
| 94 | neg_missing | RULE-4fb15b673728 | Tuple | code_generator.py:2150 | mixed:ast_marker_eq,ast_marker_in_set | N01 | 负证候选：N02 |
| 95 | neg_missing | RULE-60c852acef19 | _STORE_CHK | region_ast_generator.py:55066 | opcode_in_named_set | N13 | 复用扫描负证：JS-ASSERT-010 |
| 96 | neg_missing | RULE-1dd012303932 | _STORE_CHK_B56 | region_ast_generator.py:55687 | opcode_in_named_set | N13 | 复用扫描负证：JS-CONTINUE-023 |
| 97 | neg_missing | RULE-ab1d4cc5ec5e | _STORE_TYPES_R61 | region_ast_generator.py:54936 | opcode_in_named_set | N13 | 复用扫描负证：JS-BOOLOP-055 之外的 N13 变体 |
| 98 | neg_missing | RULE-572fd2eb12b9 | _STORE_TYPES_R61_chk | region_ast_generator.py:55312 | opcode_in_named_set | N13 | 复用扫描负证：N13 变体 |
| 99 | neg_missing | RULE-103bb62f62c8 | _frame_heads | comprehension_generator.py:840 | opcode_in_named_set | N05 | 复用扫描负证：JS-CONTINUE-023 或 N12 |
| 100 | neg_missing | RULE-b231086215ec | _lit_consume_ops | region_ast_generator.py:73957 | opcode_in_named_set | N09；亦见 N18 | 复用扫描负证：JS-CONTINUE-023 |
| 101 | neg_missing | RULE-08253d92ea26 | _store_ops | region_ast_generator.py:12365 | opcode_in_named_set | N13；亦见 N14 | 复用扫描负证：JS-ASSERT-010 |
| 102 | neg_missing | RULE-e4ed34fb8c7f | _store_ops_set | region_ast_generator.py:55325 | opcode_in_named_set | N13 | 复用扫描负证：JS-ASSERT-010 |
| 103 | neg_missing | RULE-b0bb824910b4 | return | ast_generator_v2.py:4906 | ast_marker_eq | N17 | 负证候选：N02（4906 处 return 标记为假） |
| 104 | neg_missing | RULE-bfc679b49338 | self._B54_LOADISH_OPS | region_ast_generator.py:4960 | opcode_in_named_set | — | ⚠ _B54_LOADISH_OPS false=0（仅有真评估）：需新负证条目（N02b）使 4960 锚点处 LOADISH 集成员不出现 |

### (c)31 守卫链证据（摘录，全文见 `b1_rules_104.json` class_c_evidence）

- **RULE-010c1b2cf1d7**（Break@ast_generator_v2.py:13459）：elif 链形态门控：extract_elif_chain（agv2:13416，嵌套 def）进入 243 次（legacy）。锚点 L13459 需 while current_nodes → 首个 If 带 _is_nested_if 标记（L13446）→ if_index <= 2（L13
- **RULE-6ce83d58fb8b**（Continue@ast_generator_v2.py:13459）：同 RULE-010c1b2cf1d7（同一锚点行 13459 的成员规则）。
- **RULE-681e794c6afb**（For@ast_generator_v2.py:13459）：同 RULE-010c1b2cf1d7（同一锚点行 13459 的成员规则）。
- **RULE-ae6695fa4fca**（Match@ast_generator_v2.py:13459）：同 RULE-010c1b2cf1d7（同一锚点行 13459 的成员规则）。
- **RULE-d1e1d76ee83d**（PRINT_EXPR@ast_generator_v2.py:11556）：if 结构形态门控：真实外层函数 _generate_if_ast@agv2:10211（AST 包含关系修正；进入 793 次 legacy）。锚点 L11556 的守卫链：if_struct.is_compound_condition and chain_len > 1（L10996）→ 遍历 
- **RULE-cbb06f6eb54d**（Try@ast_generator_v2.py:13459）：同 RULE-010c1b2cf1d7（同一锚点行 13459 的成员规则）。
- **RULE-6048d12971c9**（While@ast_generator_v2.py:13459）：同 RULE-010c1b2cf1d7（同一锚点行 13459 的成员规则）。
- **RULE-8fc89ce420ac**（_APPEND_OPS@ast_generator_v2.py:3330）：回退路径形态门控：_extract_comp_elt@agv2:3300 全程 0 进入；唯一调用点 L3285 在 _parse_comprehension_from_code 的 dis 回退 try 块（L3257）内，而主路径 L3251-3252 `if comp_ast is not N
- **RULE-e950c889b956**（_BIND_STORE_OPS@region_analyzer.py:16977）：with 绑定形态门控：_parse_bind_unpack@region_analyzer:16956（嵌套 def）0 进入；调用点 L17001 在 _extract_with_items（进入 126 次 region）内，守卫链 for idx, bw_pos → _tj < len(in
- **RULE-a6c5590d7e93**（_BIND_UNPACK_OPS@region_analyzer.py:16990）：同 RULE-e950c889b956（同一函数 _parse_bind_unpack；锚点 L16990 elif）。
- **RULE-9890ff971e58**（_CHECK_OPS_r08b@region_ast_generator.py:41716）：try 结构形态门控：真实外层函数 _generate_try@rag:40468（AST 包含关系修正；进入 187 次 region）。锚点 L41716 的守卫链：if _outer_handler_entries and handlers（L41677）→ 遍历外层 handler 块指令 
- **RULE-996e7c860ca0**（_DELETE_NAME_OPS@region_ast_generator.py:65190）：三元删除目标形态门控：_build_multi_target_del_targets@rag:65125 0 进入；调用点 L65094 在 _try_build_ternary_store_assign（进入 13 次 region）内，守卫链 last_instr.opname == 'DELE
- **RULE-b2e2ae122393**（_NOISE@region_analyzer.py:8235）：except-break 形态门控：_is_except_break_exit@region_analyzer:8210 进入 6 次；锚点 L8235 在 for i in instrs[idx+1:]（L8234）内——全部 6 次调用中切片为空（break 为区域末条指令）。需 break 之
- **RULE-cd390e67679f**（_STORE_CHK_R02@region_ast_generator.py:54405）：boolop 存储形态门控：_generate_boolop_impl@rag:53928 进入 56 次；锚点 L54405 守卫链：boolop_expr（L54364）→ 无 value_target 且非 augassign 且 merge_block 非空（L54369）→ POP_TOP
- **RULE-31256e3fd90e**（_STORE_OPS_R2P02@region_ast_generator.py:55971）：三元 boolop 条件形态门控：_build_ternary_boolop_condition@rag:55864 0 进入；调用点 L58373 在 _generate_ternary（进入 100 次 region）内，守卫 _nested_cond_expr is None（L58360 o
- **RULE-532506346aa4**（_b107_store_ops@region_ast_generator.py:76425）：链式复杂目标赋值形态门控：_build_chained_complex_target_assign@rag:76354 进入 415 次；锚点 L76425 在 for _b107_ii in range(0, len(instrs))（L76418）内，循环体在到达成员测试前于 L76421-76
- **RULE-f3e459303717**（_b33_noise@region_ast_generator.py:14704）：await-owner 形态门控：_b33_await_owner_merged_stmts@rag:14587 进入 122 次；锚点 L14704 守卫链 for _m in members[_mi:]（L14700）→ for i in _m.instructions（L14703）。全部调用
- **RULE-d7cb17e16c13**（_bounce_names@comprehension_generator.py:4064）：混合 bool 链形态门控：_b247_mixed_boolchain@comprehension_generator:3926 进入 19 次；锚点 L4064 在 for _j in _jumps（L4060）内，全部调用中 _jumps 为空。需带跳转指令的混合布尔链形态。
- **RULE-eea05924d17d**（_cmp_ops_set@region_ast_generator.py:22175）：链式比较三元形态门控：_try_build_ternary_operand_chained_compare@rag:22017 进入 13 次；锚点 L22175 守卫链 for _cb in chain_blocks（L22172）→ for _i in _cb.instructions（L221
- **RULE-54c66455c6d9**（_cso@comprehension_generator.py:298）：推导式赋值形态门控：try_generate_comprehension_assign@comprehension_generator:177 进入 2917 次；锚点 L298 守卫链 for comp_indices（L281）→ if _comp_loop_idx in _chained_pa
- **RULE-51fbefc39b4b**（_ctx_value_ops@region_ast_generator.py:46465）：with 项补全形态门控：_b86_complete_with_items@rag:46372 进入 124 次；锚点 L46565…L46465 的守卫链为 4 层嵌套循环（region blocks → 指令 → 前向扫描 → _pj 成员测试），全部调用中从未到达成员测试。
- **RULE-ba395f773988**（_frame_bookkeeping@comprehension_generator.py:856）：return 后继形态门控：_find_returns_pending_value_successor@comprehension_generator:766 进入 1 次；锚点 L856 守卫链：for s in block.successors（L816）→ for i in s_instrs[
- **RULE-eb169da1a935**（_hb_noise_ops@region_ast_generator.py:44134）：handler 体形态门控：_generate_handler_body_statements@rag:43187 进入 607 次；锚点 L44134 守卫链：handler 块含 UNPACK_SEQUENCE/UNPACK_EX（L44116）→ _hb_ok（L44130）→ for _hb
- **RULE-9eea46812142**（_jump_ops@comprehension_generator.py:1902）：值链形态门控：_value_chain_key_split_point@comprehension_generator:1879 进入 5(region)/1(legacy) 次；锚点 L1902 在 for _i, _ins in enumerate(instrs)（L1901）内，该循环在全部 
- **RULE-969c990c53ef**（_mt_store_ops@region_ast_generator.py:76740）：多目标解包形态门控：_build_multi_target_unpack@rag:76640 进入 66 次；锚点 L76740 守卫链 while _mt_idx < len(_mt_all)（L76677）→ 非 UNPACK_SEQUENCE（L76682）→ 非 UNPACK_EX（L767
- **RULE-5c5d7b71d2bb**（_skip_ops@region_ast_generator.py:78499）：return 重建形态门控：_generate_return_ast@rag:78386 0 进入；18 个调用点全部位于角色/形态守卫之后（如 _generate_block_statements_body@L70523 的 BlockRole.BREAK+RETURN_VALUE 守卫、_pro
- **RULE-048e69dc7408**（_v105_sub_attr@region_ast_generator.py:55973）：同 RULE-31256e3fd90e（同一函数 _build_ternary_boolop_condition；锚点 L55973 elif，前置 L55971 _STORE_OPS_R2P02 分支未命中）。
- **RULE-e8aa239b163e**（_yf_store_ops@region_ast_generator.py:7870）：yield-from 循环形态门控：_generate_loop@rag:7579 进入 444 次；锚点 L7870 守卫链 region.metadata['is_yield_from_loop']（L7695）→ _yf_expr（L7850）→ 遍历 region.blocks（L7862）
- **RULE-a8dffc095ffd**（attr@region_ast_generator.py:53333）：augassign 目标形态门控：_build_boolop_augassign_target@rag:53307 进入 5 次；锚点 L53333 被 L53320-53322 `kind = getattr(region,'augassign_target_kind',None); if kin
- **RULE-26ee397f261c**（skip_ops@region_ast_generator.py:78444）：同 RULE-5c5d7b71d2bb（同一函数 _generate_return_ast；锚点 L78444，位于 return_instr.opname == 'RETURN_VALUE'（L78399）之后的指令扫描内）。
- **RULE-e255ab564575**（subscr@region_ast_generator.py:53367）：同 RULE-a8dffc095ffd（同一函数；锚点 L53367 kind == 'subscr' 分支，需 `x[i] += <boolop>` 形态）。

## 6. 特例：RULE-a310f7ea600b（PREP_RERAISE_STAR，A1 修复）

A1 解遮蔽后该规则从 no_occurrence 转 negative_witness_missing：true_evals 0→6，symbol_observed=True，正见证 JS-EXCEPTSTAR-001。其 elif 位于七成员守卫内层梯的最后一支，**任何到达该 elif 的求值必然为真**（前六支已覆盖其余六成员）——严格负见证在结构上不可能。三种处置选项（裁决归父代理）：

1. **结构负证豁免**：在 b1+SN 判据中为「链尾独占成员」增加结构豁免（该规则真评估即完备证据）；
2. **宇宙重锚**：将该规则重锚到 L23464 七成员守卫（in-set 谓词），负见证可用其他成员 pyc；
3. **保持 open**：如实报告 neg_missing，不计入收敛目标。

同类风险规则（复用扫描失败时的后备豁免名单）：CACHE@agv2:2666、RESUME@2662、RETURN_VALUE@1877、LOAD_CONST@1062（内联缓存/帧指令遍布码流，纯负条目可能不存在）。

## 7. 实施流程（阶段三，待批准）

1. **复用扫描**（零成本）：对 26 条 neg_missing + 21 条 guard_only 规则，从现有 1556 条目的运行数据挖纯负条目与符号观测记录；
2. **新条目落地**：按 §4 生成 p_j 源文件（test_repros/round15/），Python 3.11 编译为 pyc，登记 jspace v2 条目（含 required_evidence 探针与 counterexample_hint）；
3. **验证闭环**：批量复跑 rule_proof_check（a3_env，rebased universe 264），按 measurement 迭代 p_j（预计每族 1-3 轮）；
4. **G4 复测**：终测读数落袋，更新 G4 报告；对未收敛规则按 §6 处置并留痕。

预估成本：p_j 编写与编译 ~1 人日；复用扫描脚本 ~0.5 日；验证迭代 2-4 轮各 ~10 分钟机时。

## 8. 风险

1. **快照陈旧**：11/204 抽查项的 pyc 输入与快照声明不一致（round13 后重写）；B1 实施前需以当前仓内 pyc 重新生成 jspace 基线（re-baseline），否则新旧条目见证不可比。
2. **纯负条目不存在**：CACHE/RESUME/RETURN_VALUE/LOAD_CONST/PREP_RERAISE_STAR 等结构性覆盖指令，严格负见证可能无法构造 → 需裁决豁免（§6）。
3. **p_j 过拟合**：新条目可能连带改变其他规则的测量（新增真/假评估改变 composition）；每批落地后须跑全量 264 规则回归对比（不能只看目标规则）。
4. **(a)15 与 (b)18 计数**：G4 终读数的分母口径（249 vs 248）取决于 PREP_RERAISE_STAR 处置与 (a)15 排除口径，需父代理在阶段三收口时明确。

## 9. 产物清单

- `b1_rules_104.json` — 104 规则全字段（含 (c)31 守卫链证据）
- `b1_design_data.json` — 18 条目族定义 + p_j 草案 + 负证映射（本设计的机读版）
- `b1_rules_detail.txt` / `b1_patterns.txt` / `b1_list_all.txt` — 规则明细工作稿
- 本文档 `B1_J_EXPANSION_DESIGN.md`
