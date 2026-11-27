# ROW4 阶段三报告（122.9 Stage 3 · B1 实施）— round13

日期：2026-11-28。执行：父代理直接实施（子代理 b414e496 三次失败后收编，见 §8）。
前置：r216 阶段二落定（A1 解遮蔽＋A2 死码删除＋A3 恒等重锚＋裁决四＋B1 设计批准）。
基线（阶段二后）：264 规则 proved 144/open 120；249 口径 proved 145（含 1 条裁决四
结构豁免）/open 104。

## 1. 最终读数（双口径，豁免单独披露）

| 口径 | total | proved | strict | 结构豁免 | open |
|---|---|---|---|---|---|
| **264 全量**（universe_v6_rebased） | 264 | **179** | 175 | 4 | **85** |
| **249 口径**（排除 (a)15 工具路径） | 249 | **179** | 175 | 4 | **70** |

- 豁免 4 条：`RULE-a310f7ea600b` PREP_RERAISE_STAR（裁决四，r216）＋本轮三重奏
  `RULE-2b6f0dcd703d` RETURN_VALUE / `RULE-e7701666d7b5` RESUME /
  `RULE-ed5bec7d7a05` LOAD_CONST（§4）。
- 264 open=85 构成：`no_occurrence_in_J` 42（含 (a)15）＝anchor_drift 组 23＋纯组
  19；`negative_witness_missing` 19＝anchor_drift 组 18＋纯组 1
  （`RULE-103bb62f62c8 _frame_heads`）；`predicate_false_at_site` 19＝16＋3；
  `guard_only_symbol_not_observed` 5。
- 249 口径 open=70 构成：no_occ 27（42−(a)15，全部 open 故 proved 不变）／neg
  19／false 19／guard 5。(a)15 判定依据＝阶段一 classification_65（a 组 15 条，
  本轮在最终记录中逐一复核：全部 open、0 evals、0 proved，排除守恒）。
- **G4 门禁彩排状态：FAIL**（`rule_manifest --check` 彩排：proved=179 ready=179
  empty_cov=82 reason=mapping_or_proof_gap）。行 4 阈值 `open=0` **未达成**；
  本报告是收敛读数，**不是**门禁通过声明。

## 2. 执行链与零回归链

jspace 谱系（全部在 `test_repros/stage3_scratch/`，每步 compare_b1 零回归）：

| 版本 | 条目 | 增量 | proved | 翻转（+n，全部 zero_regression=True） | 耗时 |
|---|---|---|---|---|---|
| s2 重锚 | 1556 | r9 重锚（B1 前置，11/204 快照陈旧） | 145 | 基线（与 s1 逐位一致） | — |
| v1 | 1574 | +N01-N18（18 条） | 150 | +5：`_closure_setup`/IS_OP/LOAD_DEREF/DELETE_NAME/SET_UPDATE | 196.5s |
| v2 | 1576 | +N19 spec_battery、N20 neg_provider | 160 | +10：UnaryOp/Yield/PJBI_NONE/Dict/Await/`_lit_consume_ops`/Name/BoolOp/Compare/`_WALRUS_INTEGRATING_OPS` | 489.8s |
| v3 | 1577 | +N21 guard17_operands | 164 | +4：Set/DELETE_DEREF/Attribute/List | 530.7s |
| v4 | 1588 | +N22 族（11 条） | 176 | +12（GO-17 批，§3） | 394.2s |
| v4-final | 1588 | 豁免表裁决后复测 | **179** | +3（三重奏豁免，零扰动） | 442.1s |

- 全链 `regressions=0`（五份 compare：`cmp_s2_v1`/`cmp_v1_v2`/`cmp_v2_v3`/
  `cmp_v3_v4`/`cmp_v3_v4final`），`run_failures` 全程 0/0。
- 豁免零扰动验证：注册前后两次全量跑（`s5_b1_v4` vs `s5_b1_v4_final`）度量面逐位
  相同——witness_pos=203、witness_neg=180、no_occurrence=42、drift_rules=228、
  symbol_observed=194；唯一差异＝3 条 verdict 重分类。豁免机制纯裁决层，不动测量。
- 复用扫描（范围③）：6 条 neg_missing 无族规则对既有 1556 条目扫描，26 个复用
  候选全部穷尽，无可复用纯负条目——结论：负见证必须新构造（N20 neg_provider、
  N22 批即此结论的执行）。
- 官方命令（每轮同构，仅 jspace/out 换）：
  `python -X utf8 tools/completeness/rule_proof_check.py --universe rows/universe_v6_rebased.json --manifest round13/jspace_v3/fresh/gate_g4/manifest_v3.json --traces round13/jspace_v3/fresh/gate_g4/traces_v4.json --jspace <jspace> --out <out> --manifest-out <mout> --counting b1 --also-legacy --structural-negative`
  （经 `run_g4_memlog.py` 包装；--manifest/--traces 仅溯源，G4 度量的是 pyc 运行真值）。

## 3. GO-17 目标翻转表（范围④终局）

12 proved / 5 open：

| 目标 | 规则 | 证明条目 | 机制备注 |
|---|---|---|---|
| Tuple | RULE-4fb15b673728 | JS-B1-N22T | spec 内层 `{(b,w)}`→Tuple；preview1 裸括号误解析修正 |
| DictComp | RULE-33f06058607b | JS-B1-N22D | 双括号 `({k: v for k, v in pairs})` 才解析为 DictComp；裸单括号丢弃 |
| ListComp | RULE-2331b38d9765 | JS-B1-N22L | `{[q for q in w]}` |
| SetComp | RULE-1ac0b3bb7543 | JS-B1-N22S | 双括号 `({q for q in w})`；裸单括号解析错误修正 |
| GeneratorExp | RULE-40c5ed4fe165 | JS-B1-N22G | `{(q for q in w)}` |
| Subscript | RULE-f1e6481a06fe | JS-B1-N22X | `{w[1]}` |
| JoinedStr | RULE-823cae0aab30 | JS-B1-N22J | |
| FormattedValue | RULE-2e321a33507c | JS-B1-N22F | |
| UNARY_NOT | RULE-762ec4ca09c6 | JS-B1-N22U | |
| GET_LEN | RULE-00f0d5ffaaff | JS-B1-N22E | 陷阱修复＋**结构负证**证明（见下） |
| SET_ADD | RULE-6cc7b6a37fd5 | JS-B1-N22S | setcomp 发射 SET_ADD；preview1 形状未覆盖修正 |
| PJBI | RULE-1c5bd7459d99 | JS-B1-N22P | POP_JUMP_BACKWARD_IF_NOT_NONE |

**GET_LEN 案（唯一非纯严格负见证的 GO 翻转）**：形状
`def f(x, w): match x: case []: return w[1]; return -1`——体部 BINARY_SUBSCR
无 UNPACK 触发 pattern_parser.py:2177-2179 门→提前返回进
`_extract_starred_sequence_pattern`（循环 2450，成员 `GET_LEN` 检查 2452）→成员
TRUE 于 2452、2190/2251 守卫 0 次求值、so=True。但每个含 GET_LEN-FALSE 的 run
同时含 TRUE（runs_f=0），严格负见证（false-only run）经验不存在；--structural-negative
下弱负见证与正见证同锚（file,line,ast_path 逐位同）异 pyc→`same_anchor_diff_pyc`
结构负证采信（探测证据 `test_repros/stage3_scratch/_n22_probe_2452.py`）。**注意**：该条不在豁免表
——它是结构负证机制（裁决三）的采信，与裁决四豁免（§4）是两个机制。

5 open（全部 `guard_only_symbol_not_observed`，b1 降级；b2 口径下均为 proved 候选）：

| 目标 | 规则 | 度量 | 定性 |
|---|---|---|---|
| GenExpr | RULE-014265ded990 | t=3 f=330，21 个 false-only run | **词汇缺口**：code_generator 分支 2773 存在 GenExpr 成员位，但被测区域管线从不在该位发射 GenExpr 节点；J 侧穷尽（同形状已证 GeneratorExp 规则，证不了 GenExpr 标记规则） |
| Lambda | RULE-bfbc22d0d1e3 | t=3 f=325，21 个 false-only run | 同上词汇缺口模式 |
| DELETE_GLOBAL | RULE-8a6101820c9d | t=10 f=15185，153 个 false-only run | **纯守卫**：被测管线无成员位 |
| EXTENDED_ARG | RULE-9b74da19b3e2 | t=161 f=241，3 个 false-only run | 纯守卫 |
| LOAD_CLASSDEREF | RULE-b620fe7fb512 | t=164 f=383，0 false-only | 纯守卫 |

**纯守卫 b1 不可翻证明**：b1 要求 `symbol_observed=True`（成员/投影/命名集 TRUE）；
这三条规则在被测管线的成员位要么不存在、要么从不被发射——增补任何只走守卫路径的
J 条目都无法产生成员 TRUE，故 J 空间侧不可翻；翻转路线只有 (i) 区域覆盖变化使成员
被发射（词汇/管线工作，超出 J 空间阶段范围）或 (ii) b2 口径接受守卫证明。GenExpr/
Lambda 同理但定性为词汇缺口（成员位在 code_generator 存在，区域从不路由到那里）。

## 4. 裁决四延伸：豁免表裁定（范围①②终局）

对 22 条 `negative_witness_missing`（有正见证、缺严格负）候选逐一裁定，**登记 3、
不登记 19**：

**登记（三重奏，模式 (ii) true-bound 编译器保证）**——登记于
`rule_proof_check.py STRUCTURAL_NEGATIVE_EXEMPTIONS`，三要件齐备（正见证条目＋
最低真求值数＋锚点逐位匹配），records 内 `structural_negative_exemption.registered`
全量留痕：

| 规则 | 锚点 | 正见证 | 实测 | 结构论证 |
|---|---|---|---|---|
| RETURN_VALUE | agv2:1895 | JS-B1-N22E | 319T/173F，163/163 runs TRUE，0 false-only | 每个 3.11+ 模块代码对象以 `LOAD_CONST None; RETURN_VALUE` 收尾；pyc 根必为模块代码对象；两管线必先处理根→任何产生求值的 run 必先 TRUE |
| RESUME | agv2:2680 | JS-B1-N22P | 318T/163F，163/163，0 false-only | 每个 3.11+ 代码对象以 RESUME 开头——分析器处理的第一条指令即 TRUE |
| LOAD_CONST | agv2:1080 | JS-B1-N22T | 261T/167F，163/163，0 false-only | 隐式 `return None` 使每个模块代码对象含 `LOAD_CONST None`（空模块亦然） |

共同结构论证：严格 4.1(3) 负见证要求 false-only run；三重奏的 opcode 由编译器保证
出现在每个 pyc 根代码对象首/尾，任何 Python-3.11+ J 空间中该 run 不可能存在。这与
裁决四原案（PREP_RERAISE_STAR，模式 (i) 支配守卫链尾）互补，登记格式同源（正见证＋
结构证据链＋逐规则显式登记，禁类别性豁免）。

**不登记（19 条）及理由**：

| 候选 | 理由 |
|---|---|
| `RULE-87685c80e83d` CACHE | so=False：b1 降级压倒豁免（即使登记也不翻），登记只会虚增 b2 诊断读数；249/b2 口径候选留档 |
| `RULE-bfc679b49338 _B54_LOADISH_OPS` | 9T/0F 单锚窄窗；`_b54_scan_chain_continuation`（region_ast_generator.py:5013）的 else 分支（L5072）存在即证明非装载指令可达 elif 5059——FALSE 结构可达，负缺失是语料窄窗不是结构不可能 |
| STORE_ATTR/STORE_DEREF/STORE_FAST（so=False） | 同 CACHE：b1 降级压倒 |
| STORE_GLOBAL/STORE_NAME/STORE_SUBSCR/`_store_ops`/`_store_ops_set`/`_BIND_STORE_OPS`/`_STORE_CHK`/`_STORE_CHK_B56`/`_STORE_OPS_R2P02`/`_STORE_TYPES_R61`(+chk)/`attr`/`return`/`_frame_heads` | 非编译器保证：store-free pyc 原则上可存在（如空模块 RESUME+LOAD_CONST None+RETURN_VALUE 即无任何 STORE），false-only run 未被结构排除；163/163 TRUE 是语料经验不是结构必然 |

裁定纪律：豁免只登记「严格负见证结构不可能」的规则；经验性 163/163 而无编译器
保证者一律留 open 待真正负见证。

## 5. N22 设计披露（范围④方法论）

- **直接形状原则**：N22 条目按 GO-17 目标逐个构造最小形状（`_n22_build_preview.py`
  → preview1/preview2 23.1s 快验证 → `_n22_build_v4.py` 全量），pyc 由
  `D:/Python/python.exe` 3.12 现场编译（magic `b"\xa7\x0d\x0d\x0a"`），逐 pyc
  verify_pyc（magic＋co_filename＋marshal 往返绑定 `test_repros/round13_b1/n*.py`）。
- **spec 内层解析规律**（f-string 格式说明符内层）：`{(b,w)}`→Tuple、`{w[1]}`→
  Subscript、`{[q for q in w]}`→ListComp、`{(q for q in w)}`→GeneratorExp、
  **`({k: v for ...})` 双括号→DictComp、`({q for q in w})` 双括号→SetComp**；
  裸单括号推导式形状解析错误或整体丢弃——DictComp/SetComp 双括号是强制项。
- **elif 链短路**：`core/cfg/code_generator.py _generate_expression` 的分支序列
  （2765 DictComp、2767 ListComp、2769 SetComp、2771 GeneratorExp、2773 GenExpr、
  2895 Subscript、2917 JoinedStr、2920 FormattedValue、3015 Name、3017 Attribute、
  3022 Tuple、3028 List、3032 Set、3040 Dict；4744-4745 十七成员 in-set 守卫）在
  匹配分支处短路——形状只要让控制流到达匹配分支即翻转，不必穿透全链。
- **or-pattern v2 发现**（`test_repros/stage3_scratch/_n22_probe_orpat.py`）：v2 管线对 or-pattern
  序列成员走 LOAD+COPY 路径（与区域管线不同），负见证构造时须按管线分账。
- **p_j 预算纪律**：操作数/f-string 族轮次 v2/v3/v4(N22)＝1/2/3；N22 是该族终轮，
  之后该族不再扩批（防过拟合——每批全量 264 回归已含此意）。

## 6. 测量机制披露（度量器事实，读数解释所需）

- **run 级跨管线状态**（rule_proof_check.py:596-765）：`begin_run` 每 pyc 一次重置
  `run_resolved/run_true/run_false`，覆盖区域＋v2 两管线；rid 在区域相已解决
  （`run_resolved`）则 v2 相同 pyc 的 `local_trace` 跳过——**跨相 run_resolved
  污染**为设计事实，对 verdict 无影响（解决即定论）但影响 run_t/runs_f 计账，
  已在此披露。
- **守卫 TRUE 在前陷阱**：741-742 处 run_true∧run_false 双置即解决；TRUE 先于
  解决记录、成员 TRUE 先于 T+F 对即安全。但守卫作用域 TRUE 若先于成员求值发生，
  可经 run_resolved 跳过掩蔽同 pyc 后续成员 FALSE——N22 形状设计已规避（成员位
  先于守卫路径）。
- **3.12 运行时事实**（豁免论证与形状设计依据）：无 TO_BOOL；推导式未内联（独立
  代码对象）；每代码对象 RESUME 起、`LOAD_CONST None`+RETURN_VALUE 收——
  §4 三重奏的编译器保证即建立在这三条上。

## 7. 证据清单（sha256 前 16 位）

jspace 谱系：`judgment_space_r9_rebaselined.json` EF0FCB9928A9B0FD（1556）→
`..._b1_v1.json` D11422F9E4A1F1E6（1574）→ `..._v2.json` 3EEC5C7732875333（1576）→
`..._v3.json` AF49FCCF0A750F13（1577）→ `..._v4.json` 1B6E51867BC3081E（1588）。
读数：s2 `3147AE5B2AF51A63`、v1 `729A40925476C145`、v2 `13A4085BF08EDE5D`、
v3 `FFA29817F507DF98`、v4 `91EF94AFA9C3D205`（豁免前）、**v4-final
`s5_b1_v4_final_proof_records.json` 1C37CD318305347E ＋ manifest
0528D3F9C594E293**。compare：`4FAA9746741FE110`/`96C0DD6223AB0620`/
`D6D0AC3995DAC8EE`/`D59CD9CEF08EB578`/`AEBE75B503BF3D7A`。N22 预演：
preview2 records `55F4E782A4660B8D`、mini jspace `BBA8CFAAFAD4F0BC`。
N22 pyc（11/11）：N22T 1D94087C10B4DDFC、N22D 6A844E16C70E1F1E、
N22L 14A81112DCE6C7A0、N22S 5DCB02792210D4DD、N22G 0EF2403250C8B18E、
N22X 84DDB808E97B2FDF、N22J 2F49EF287F9245A1、N22F 0D886130A62CD926、
N22U D2162EFEC841482E、N22E 4A255C42D4119C9E、N22P 1B25B7A6D6095671。
工具：`rule_proof_check.py` 5312865D2B4F1076、`rule_manifest.py`
24217C6F8EC8B4E6、universe A585187BBF3B1B54。memlog（v4-final）
`g4_v4_final_memlog.txt` 2E26FC0FDEC1F5EF——avail_pagefile 3548→3362 MB、
负载峰值 64%、守卫阈值 2000 MB 未触发，exit=0。

## 8. 过程披露（诚实记账）

1. **子代理失败**：阶段三原派子代理 b414e496 三次失败（1 崩溃＋2 上下文耗尽）
   后判 OUT OF CONTEXT，父代理直接实施；子代理此前「高置信」断言
   （LOAD_CLASSDEREF/DELETE_GLOBAL/SET_ADD/EXTENDED_ARG 均纯守卫）经父代理逐一
   复核——SET_ADD 实为可翻（N22S 已证），其余定性成立。子代理断言不采信、必复核。
2. **工件损失与重建**：D:\temp 清场丢失原始 s0-s3 工件与报告草稿；已重建且逐项
   复核（读数链与丢失前记录一致）。丢失前工件哈希不可复现——接受以内容级一致＋
   双哈希披露（重建后哈希为准，§7）处理，不冒充原始工件。
3. **基敏感对照**：一次中间态错基读数（jspace_v3m，proved=165）归档为基敏感性
   对照（`test_repros/stage3_scratch/` 内留档），**不入证据链**——正式链仅 §2 表。
4. **--manifest/--traces 溯源参数**：正式命令携带 round13/jspace_v3 下的
   manifest_v3/traces_v4（provenance only）；G4 度量只依赖 pyc 运行真值，
   该参数不影响读数，为防误读在此披露。
5. **p_j 防过拟合**：每批全量 264 规则回归（compare_b1）已执行五次全绿；N22 后
   操作数族不再扩批。

## 9. 后续（阶段三范围外，移交清单）

- 5 条 GO open：GenExpr/Lambda 词汇缺口＋3 条纯守卫——需区域覆盖变化或 b2 口径
  裁决，J 空间侧已穷尽（§3）。
- 19 条 neg_missing：需真正的 false-only run 负见证（§4 表；STORE_* 族或可经
  store-free 形状构造，但那同时会翻转其 TRUE 语义——须逐条设计）。
- 42 条 no_occ（含 (a)15）：(a)15 已随 249 口径排除；(c) 类需扩 J 形态（阶段一
  已定性路线）。
- 卫生批（挂账）：cg/rag 陈旧注释、闲置 `Dict[str, Any]` 注解、
  `_generate_dict_comp_from_dict` 死码、tests/nook/test_regression.py L15。
- 终局对齐：REACHABILITY 行 4 字面命令（round9 universe 339）——339 vs 344 差异
  裁决（§见 ROW4_RULE_COVERAGE.md 状态节）。
