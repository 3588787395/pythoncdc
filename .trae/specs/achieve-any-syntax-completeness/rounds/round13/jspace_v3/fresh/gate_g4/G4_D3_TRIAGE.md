# G4 · D3 88 条「行到达 / 谓词恒假」逐条定性

> 仓库：`F:\Downloads\pythoncdc-main`，解释器 `D:/Python/python.exe` = CPython **3.11.7**。
> 本报告**只读**分析：未改 `core/`、`scripts/`、`tests/`、`tools/`，未写任何 proved 状态。
> 机器可读：`fresh/gate_g4/g4_d3_classification.json`（88 条逐条记录）。
> 分析脚本与原始输出：`D:\temp\opencode\cl_layout\g4d3\`。

## 0. 结论速览

| 类别 | 条数 | 判据 | 处置 | 预计可 proved |
|---|---|---|---|---|
| a 规则陈旧 / 不可满足 | 36 | 3.11 里不存在该操作码名（33）或该 IR 值无生产者（2）/ CACHE 死分支（1） | 从宇宙排除（3.11 口径） | 0（改任何东西都救不回来） |
| b 锚点错位 | 0 | 88/88 的 pattern 都落在声明行上，±1..±20 邻近搜索全部 offset=0 | 无需重定位 | 0（不存在） |
| c 谓词语义不匹配 | 8 | membership 守卫被校验器投影成单成员等式；守卫实测被别人满足 | 改规则模型/校验器口径（见 §4-C） | +8（改口径即得）；不改则需 8 条新 J |
| d 其它（规则有效、J 未覆盖） | 44 | 名字/取值在 3.11 真实可产出，行号正确，只是 131 个 J 没走到 | 补 J 覆盖 | +44（每条 1 条新 J） |

**处置合计：排除 36 / 重定位 0 / 需改校验器或规则模型 8 / 需补 J 44 = 88。**

## 1. 88 条是怎么取出来的（与 `executed_inventory_v3.json` 的对接）

任务口径写作「`line_reached > 0 and predicate_true == 0`」。实测核对后的事实：

- `executed_inventory_v3.json` **没有逐规则计数器**：它的粒度是 code object（`files[file] = [{name, firstlineno, phases}]`，`phase.import/run` 两阶段），只能回答「某函数的代码对象跑过没」。它也不含 `line_reached` 字段。
- 逐规则的「到达 / 谓词真假」在 `proof_records_v2.json` 的 `measurement` 里：`predicate_evaluations`、`true_evaluations`、`false_evaluations`、`pyc_runs_reaching_site`、`pyc_runs_with_true`。
- 88 条的精确选取条件：`reasons[].code == 'predicate_false_at_site'`，等价于 `predicate_evaluations > 0 且 true_evaluations == 0`（88/88 同时满足，已逐条验证）。
- 与 JSON 冻结计数完全吻合：`proof_records_v2.counts.open_reasons = {"negative_witness_missing": 29, "no_occurrence_in_J": 100, "predicate_false_at_site": 88}`；`traces_v3.summary.rules_hit_true = 156`、`empty_cov_true = 188`。
- 与 inventory 的落点核对：88 条的 anchor 分布在 7 个文件，**7/7 都在** `executed_inventory_v3.anchor_files`（16 个 anchor 文件）且**7/7 在** `inventory["files"]`（有已执行 code object 的 12 个文件）里；88 条的 `pyc_runs_reaching_site` 全部 > 0。
- 3.11 语料证据：`sys.version` = 3.11.7；J pyc magic = `a70d0d0a`；指令流来源 `core/cfg/cfg_builder.py:136` = `for instr in dis.get_instructions(self.code_obj)`。

## 2. 88 条的 pattern 形态与类别分布

### 2.0 判定规则（`classify3.py` 实现，按顺序命中即停）

1. **锚点判据**：把 `pattern` 去掉空白后与声明行起、按括号配平合并的逻辑语句比较；不在声明行就在 ±1..±20 行内逐行再搜 ⇒ 命中即 **b**。
2. **符号活性**（区分 a 与 c/d）：
   - 操作码形态（`opname ==` / `opname in (...)`）：`symbol in dis.opmap`（3.11.7）为假 ⇒ **a**；`symbol == 'CACHE'` ⇒ **a**（dis 不产出）。
   - 命名集合形态（`opname in NAME`）：解析 NAME 的集合字面量，成员**全部**不在 `dis.opmap` ⇒ **a**（本次 0 条）；否则进入第 3 步。
   - AST/IR 标记形态（`node_type`/`name` 比较）：全树找「生产者」（`'type': 'X'`、`= 'X'`、`ASTName('X')`、`co_name == 'X'` 等）为 0 处 ⇒ **a**。
3. **守卫活性**（区分 c 与 d）：取校验器在**同一 If-test AST 路径**上生成的全部候选（同守卫成员），若任一成员的 `true_evaluations > 0`（即守卫被别的成员满足过）⇒ **c**。
4. 其余 ⇒ **d**。

第 3 步用校验器自己的候选集合，而不是字符串比较：因为 universe 的一条规则会把同名 symbol 的**多个 anchor** 合并（例：`RULE-27a804e8b6d4` BINARY_OP 有 49 个 anchors），用「anchor+pattern 相同」找兄弟会漏掉守卫里的活成员。

### 2.1 按 `universe_v3.json` 的 `kind` 字段（任务要求的分组）

| kind | 条数 | 备注 |
|---|---|---|
| `opcode_eq` | 88 | 全部 88 条 |
| `isinstance_ast` | 0 | — |

**这个分组没有区分力**：88 条全部被标成 `opcode_eq`，但其中 26 条的 pattern 是 `node_type == 'X'` / `name == 'X'` 的 **AST/IR 标记比较**，与操作码无关；11 条的 symbol 是**局部集合变量名**。原因是校验器和扫描器共用同一张 `OP_NAMES`（`tools/completeness/rule_proof_check.py:73`，含 `node_type`/`name`/`kind`），于是标记比较也被记成 `opcode_eq`（详见 §6-D2）。

### 2.2 按 pattern 的真实形态 × 判定类别

| 真实形态 | 条数 | a | b | c | d |
|---|---|---|---|---|---|
| 操作码名谓词 `opname == 'X'` / `opname in (...)` | 51 | 34 | 0 | 7 | 10 |
| 命名集合守卫 `opname in NAME` | 11 | 0 | 0 | 0 | 11 |
| AST/IR 标记谓词 `node_type/name == 'X'` | 26 | 2 | 0 | 1 | 23 |
| 合计 | 88 | 36 | 0 | 8 | 44 |

### 2.3 按源文件

| 文件 | 条数 | a | b | c | d |
|---|---|---|---|---|---|
| core/cfg/code_generator.py | 25 | 2 | 0 | 1 | 22 |
| core/cfg/ast_generator_v2.py | 25 | 12 | 0 | 5 | 8 |
| core/cfg/region_ast_generator.py | 24 | 15 | 0 | 0 | 9 |
| core/cfg/region_analyzer.py | 5 | 3 | 0 | 2 | 0 |
| core/cfg/pattern_parser.py | 4 | 4 | 0 | 0 | 0 |
| core/cfg/comprehension_generator.py | 4 | 0 | 0 | 0 | 4 |
| core/cfg/ast_converter.py | 1 | 0 | 0 | 0 | 1 |

### 2.4 锚点错位(b) 的自动判据结果

- 判据：把 `pattern` 去空白后与本行起、按括号配平合并的**逻辑语句**比字符串；未命中则在 ±1..±20 行逐个再搜。
- 结果：**88/88 命中 0 偏移**（`offset` 分布只有 `0`），b 类为空。脚本 `classify3.py::find_offset()`。

## 3. 12 条抽样明细

抽样规则：6 条操作码名谓词 + 6 条 AST/IR 标记谓词，覆盖 6 个不同源文件，并让 a/c/d 三类都出现。每条给出：锚点与源码行、pattern、判定、证据命令与输出。

### 抽样 1 · `RULE-2f8806fa6f9b` — INPLACE_MULTIPLY（class a）

- 锚点：`core/cfg/region_ast_generator.py:77253`（universe `kind=opcode_eq`；本条真实形态=opcode）
- 该行实际源码：

```python
77253              if instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT',
77254                                  'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE',
77255                                  'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO',
77256                                  'INPLACE_POWER', 'INPLACE_LSHIFT',
77257                                  'INPLACE_RSHIFT', 'INPLACE_AND',
77258                                  'INPLACE_XOR', 'INPLACE_OR'):
```

- pattern（`universe_v3.json`）：`instr.opname in ('BINARY_OP', 'INPLACE_ADD', 'INPLACE_SUBTRACT', 'INPLACE_MULTIPLY', 'INPLACE_TRUE_DIVIDE', 'INPLACE_FLOOR_DIVIDE', 'INPLACE_MODULO', 'INPLACE_POWER', 'INPLACE_LSHIFT', 'INPLACE_RSHIFT', 'INPLACE_AND', 'INPLACE_XOR', 'INPLACE_OR')`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`instr.opname == 'INPLACE_MULTIPLY'`
- 实测：`predicate_evaluations=1936`、`false_evaluations=1936`、`pyc_runs_reaching_site=13`、`true_entries=0`

证据命令与输出：

```text
$ D:/Python/python.exe -X utf8 -c "import dis;print('INPLACE_MULTIPLY' in dis.opmap)"
  False
$ D:/Python/python.exe -X utf8 D:\temp\opencode\cl_layout\g4d3\probe_emit.py  （片段：inplace_add 探针）
  inplace_add dis=BINARY_OP,LOAD_CONST,LOAD_FAST,MAKE_FUNCTION,RESUME,RETURN_VALUE,STORE_FAST,STORE_NAME（无任何 INPLACE_*）
$ grepc.py INPLACE_MULTIPLY core/cfg/region_ast_generator.py --lines
  2 hits: 77254（同一守卫）, 77271（'INPLACE_MULTIPLY': '*=' 兼容表）
$ 同守卫的活成员规则 RULE-27a804e8b6d4 (BINARY_OP)
  status=proved, true_evaluations=85
```

**判定（a）**：规则陈旧（a）：同一守卫的另一成员 BINARY_OP 在 3.11 里被实测命中并已 proved，而 12 个 INPLACE_* 成员名在 3.11 中根本不存在——源码是跨版本兼容写法（BINARY_OP + 旧名），规则却把「兼容名」当成 3.11 可满足的谓词。

**处置**：从 3.11 宇宙排除 12 条 INPLACE_*（BINARY_OP 一条代表该守卫即可）。

### 抽样 2 · `RULE-72af8df090f5` — CALL_FUNCTION（class a）

- 锚点：`core/cfg/ast_generator_v2.py:1512`（universe `kind=opcode_eq`；本条真实形态=opcode）
- 该行实际源码：

```python
 1512          elif opname in ('CALL_FUNCTION', 'CALL_METHOD'):
```

- pattern（`universe_v3.json`）：`opname in ('CALL_FUNCTION', 'CALL_METHOD')`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`opname == 'CALL_FUNCTION'`
- 实测：`predicate_evaluations=18399`、`false_evaluations=18399`、`pyc_runs_reaching_site=131`、`true_entries=0`

证据命令与输出：

```text
$ D:/Python/python.exe -X utf8 -c "import dis;print('CALL_FUNCTION' in dis.opmap, 'CALL' in dis.opmap)"
  False True
$ grepc.py "'CALL_FUNCTION'" core/cfg/ast_generator_v2.py
  20 行，全部是元组守卫/兼容名单（1512, 6563, 7387, 8046, ...）
$ 同守卫另一成员 CALL_METHOD
  同样不在 dis.opmap，open / 0 true
```

**判定（a）**：规则陈旧（a）：3.11 把 CALL_FUNCTION/CALL_METHOD 合并成 CALL，两个名字都不可能再出现在被测字节码里。

**处置**：从宇宙排除（2 条：CALL_FUNCTION、CALL_METHOD）。

### 抽样 3 · `RULE-87685c80e83d` — CACHE（class a）

- 锚点：`core/cfg/ast_generator_v2.py:2666`（universe `kind=opcode_eq`；本条真实形态=opcode）
- 该行实际源码：

```python
 2666          elif opname == 'CACHE':
```

- pattern（`universe_v3.json`）：`opname == 'CACHE'`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`opname == 'CACHE'`
- 实测：`predicate_evaluations=72749`、`false_evaluations=72749`、`pyc_runs_reaching_site=131`、`true_entries=0`

证据命令与输出：

```text
$ grepc.py get_instructions core/cfg/cfg_builder.py
  core/cfg/cfg_builder.py:136: for instr in dis.get_instructions(self.code_obj)
$ probe: raw co_code 有 CACHE 单元，dis.get_instructions 不产出 CACHE
  raw_present=True / dis_emitted=False
$ grepc.py CACHE bytecode/pyc_disasm.py
  6 行，186-190 显式跳过 CACHE
```

**判定（a）**：规则陈旧（a）：CACHE 是填充单元，不是指令。CDC 的指令流来自 dis.get_instructions（cfg_builder.py:136），3.11 的 dis 不产出 CACHE；`elif opname == 'CACHE'` 分支结构上不可达。（注意 kind 不是 opcode 语义问题，而是分支死代码问题；谓词本身在 3.11 下恒假。）

**处置**：从宇宙排除（1 条），或改标为 dead_branch 不计入 completeness 分母。

### 抽样 4 · `RULE-db1ffbe2c327` — MATCH_AS（class a）

- 锚点：`core/cfg/ast_generator_v2.py:2952`（universe `kind=opcode_eq`；本条真实形态=opcode）
- 该行实际源码：

```python
 2952          elif opname == 'MATCH_AS':
```

- pattern（`universe_v3.json`）：`opname == 'MATCH_AS'`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`opname == 'MATCH_AS'`
- 实测：`predicate_evaluations=1584`、`false_evaluations=1584`、`pyc_runs_reaching_site=96`、`true_entries=0`

证据命令与输出：

```text
$ D:/Python/python.exe -X utf8 -c "import dis;print('MATCH_AS' in dis.opmap)"
  False
$ grepc.py MATCH_AS core --lines
  5 行：astree.py:56/119（BLK_MATCH_AS 块类型标签）、ast_generator_v2.py:2951-2953（本分支）
```

**判定（a）**：规则陈旧（a）：MATCH_AS / MATCH_OR / MATCH_VALUE / MATCH_MAPPING_KEYS / UNPACK_EXTRACT / LOAD_CONSTANT 这些名字从来不是 CPython 操作码（3.10 的 match 只有 MATCH_MAPPING/MATCH_SEQUENCE/MATCH_KEYS/MATCH_CLASS），是源码里按名字猜出来的分支。

**处置**：从宇宙排除（6 条同类）。

### 抽样 5 · `RULE-8a6101820c9d` — DELETE_GLOBAL（class c）

- 锚点：`core/cfg/region_analyzer.py:23701`（universe `kind=opcode_eq`；本条真实形态=opcode）
- 该行实际源码：

```python
23701                                      if _ei.opname in ('STORE_FAST', 'STORE_NAME',
23702                                                        'STORE_GLOBAL', 'STORE_DEREF',
23703                                                        'STORE_ATTR', 'STORE_SUBSCR',
23704                                                        'BINARY_OP', 'DELETE_NAME',
23705                                                        'DELETE_FAST', 'DELETE_GLOBAL',
23706                                                        'DELETE_ATTR', 'DELETE_SUBSCR'):
```

- pattern（`universe_v3.json`）：`_ei.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL', 'STORE_DEREF', 'STORE_ATTR', 'STORE_SUBSCR', 'BINARY_OP', 'DELETE_NAME', 'DELETE_FAST', 'DELETE_GLOBAL', 'DELETE_ATTR', 'DELETE_SUBSCR')`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`_ei.opname == 'DELETE_GLOBAL'`
- 实测：`predicate_evaluations=20463`、`false_evaluations=20463`、`pyc_runs_reaching_site=131`、`true_entries=0`

证据命令与输出：

```text
$ checker rebuild（tools/completeness/rule_proof_check.py::_scan_file）
  expr = `_ei.opname == 'DELETE_GLOBAL'`
$ 源码 23701-23706 行
  if _ei.opname in ('STORE_FAST','STORE_NAME','STORE_GLOBAL','STORE_DEREF','STORE_ATTR','STORE_SUBSCR','BINARY_OP','DELETE_NAME','DELETE_FAST','DELETE_GLOBAL','DELETE_ATTR','DELETE_SUBSCR')：12 成员守卫
$ 同守卫成员实测
  STORE_FAST proved/107 true, STORE_SUBSCR proved/22, BINARY_OP proved/85, STORE_GLOBAL proved/5
$ DELETE_GLOBAL 在 3.11
  dis.opmap=True；probe `global z; del z` -> DELETE_GLOBAL
```

**判定（c）**：谓词语义不匹配（c）：行号正确、成员在 3.11 里真实存在且可产出，但校验器把「12 成员守卫」投影成「_ei.opname == 'DELETE_GLOBAL'」；实测中该守卫被 STORE_* 成员满足过 107 次，本规则因此恒假。差异在求值口径，不在源码。

**处置**：改规则模型：同一守卫只生成 1 条规则、谓词取整条守卫（pattern），或保留逐成员规则但把「守卫被其它成员满足」记录为 guard-hit 而不是 false。

### 抽样 6 · `RULE-4743f0da62f0` — _b113_stop_ops（class d）

- 锚点：`core/cfg/comprehension_generator.py:2379`（universe `kind=opcode_eq`；本条真实形态=setname）
- 该行实际源码：

```python
 2379              if first_instr.opname in _b113_stop_ops:
```

- pattern（`universe_v3.json`）：`first_instr.opname in _b113_stop_ops`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`first_instr.opname in _b113_stop_ops`
- 实测：`predicate_evaluations=88`、`false_evaluations=88`、`pyc_runs_reaching_site=28`、`true_entries=0`

证据命令与输出：

```text
$ checker rebuild
  expr = `first_instr.opname in _b113_stop_ops`（整条守卫，忠实）
$ grepc.py _b113_stop_ops core/cfg/comprehension_generator.py --lines
  3 行：2370 定义、2379 本守卫、2396 另一处复用
$ 集合成员 vs dis.opmap
  16 成员，14 个在 3.11；仅 YIELD_FROM、RETURN_CONST 是死名
```

**判定（d）**：d（其它）：这是唯一一类被校验器**忠实**求值的谓词（命名集合守卫整体求值），88 次全假只说明 28 个 J 条目里 first_instr 恰好不是这些停机指令——守卫假是正常退出口，不是规则缺陷。

**处置**：保留在 open（不排除、不改校验器），补一条「推导式首指令落在集合内」的 J。

### 抽样 7 · `RULE-938087af729e` — __NESTED_FUNC__（class a）

- 锚点：`core/cfg/code_generator.py:4115`（universe `kind=opcode_eq`；本条真实形态=marker）
- 该行实际源码：

```python
 4115              elif name == '__NESTED_FUNC__':
```

- pattern（`universe_v3.json`）：`name == '__NESTED_FUNC__'`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`name == '__NESTED_FUNC__'`
- 实测：`predicate_evaluations=14871`、`false_evaluations=14871`、`pyc_runs_reaching_site=131`、`true_entries=0`

证据命令与输出：

```text
$ grepc.py __NESTED_FUNC__ core --lines
  1 hit：code_generator.py:4115（比较本身）
$ 检验「谁生产这个 IR 值」
  0 处；core/ 没有任何代码写出 name='__NESTED_FUNC__'
```

**判定（a）**：规则陈旧（a）：`name == '__NESTED_FUNC__'` 的取值在整棵代码树里没有任何生产者，分支是死代码（14871 次求值全假）。

**处置**：从宇宙排除（1 条）。

### 抽样 8 · `RULE-014265ded990` — GenExpr（class a）

- 锚点：`core/cfg/code_generator.py:3788`（universe `kind=opcode_eq`；本条真实形态=marker）
- 该行实际源码：

```python
 3788              elif node_type == 'GenExpr':
```

- pattern（`universe_v3.json`）：`node_type == 'GenExpr'`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`node_type == 'GenExpr'`
- 实测：`predicate_evaluations=213`、`false_evaluations=213`、`pyc_runs_reaching_site=11`、`true_entries=0`

证据命令与输出：

```text
$ grepc.py "'GenExpr'" core/cfg/code_generator.py --lines
  6 行，全是消费端（3788, 3863, 5516, 5578, 5871, 6075）
$ IR 生产映射
  core/cfg/comprehension_generator.py:6588: '<genexpr>': 'GeneratorExp'
```

**判定（a）**：规则陈旧（a）：'GenExpr' 只被读、从不被写；生成器把 <genexpr> 映射成 'GeneratorExp'。3786 行的 'GeneratorExp' 分支才是活路径（后者属 d）。

**处置**：从宇宙排除（1 条），或把该行合并进 'GeneratorExp' 分支后重扫。

### 抽样 9 · `RULE-ec53116b4211` — List（class c）

- 锚点：`core/cfg/code_generator.py:2174`（universe `kind=opcode_eq`；本条真实形态=marker）
- 该行实际源码：

```python
 2174          elif node_type in ('List', 'Starred'):
```

- pattern（`universe_v3.json`）：`node_type in ('List', 'Starred')`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`node_type == 'List'`
- 实测：`predicate_evaluations=2`、`false_evaluations=2`、`pyc_runs_reaching_site=1`、`true_entries=0`

证据命令与输出：

```text
$ checker rebuild
  expr = `node_type == 'List'`（源码是 `node_type in ('List','Starred')`）
$ 同守卫成员
  Starred: status=proved, true_evaluations=14
$ 'List' 的生产者
  18 处，如 ast_generator_v2.py:1567/7340 `'type': 'List'`、:21501 `return {'type': 'List', ...}`
$ 求值次数
  2 次 / 1 个 J 条目，全假
```

**判定（c）**：谓词语义不匹配（c）：与 DELETE_GLOBAL 同一机制——2 成员守卫被投影成单成员等式；Starred 分支实测命中 14 次（已 proved），'List' 因此 2 次求值全假。

**处置**：同 c：规则模型按守卫聚合；聚合后本条立即有正/负见证。

### 抽样 10 · `RULE-7437333913d0` — Dict（class d）

- 锚点：`core/cfg/code_generator.py:4055`（universe `kind=opcode_eq`；本条真实形态=marker）
- 该行实际源码：

```python
 4055                  elif node_type == 'Dict':
```

- pattern（`universe_v3.json`）：`node_type == 'Dict'`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`node_type == 'Dict'`
- 实测：`predicate_evaluations=2`、`false_evaluations=2`、`pyc_runs_reaching_site=1`、`true_entries=0`

证据命令与输出：

```text
$ checker rebuild
  expr = `node_type == 'Dict'`（单成员守卫，无投影问题）
$ 'Dict' 生产者
  core/ 内 22 处（ast_generator_v2 14 处构造 dict-IR，region_ast_generator 等 8 处）
$ 求值次数
  2 次 / 1 个 J 条目（dict-IR 回退路径几乎没被 J 走到）
```

**判定（d）**：d（其它）：模式真实、行号正确、无投影问题；只是 J 语料里几乎没有走 dict-IR 回退路径的条目，2 次求值都发生在 node_type 为其它值的场合。

**处置**：保留 open，补一条走 dict-IR 的 J。

### 抽样 11 · `RULE-4773744d80c4` — <lambda>（class d）

- 锚点：`core/cfg/code_generator.py:2396`（universe `kind=opcode_eq`；本条真实形态=marker）
- 该行实际源码：

```python
 2396          if node.name == '<lambda>':
```

- pattern（`universe_v3.json`）：`node.name == '<lambda>'`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`node.name == '<lambda>'`
- 实测：`predicate_evaluations=934`、`false_evaluations=934`、`pyc_runs_reaching_site=128`、`true_entries=0`

证据命令与输出：

```text
$ grepc.py "'<lambda>'" core --lines
  15 行；包括 ast_converter.py:1017 co_name == '<lambda>'、ast_generator_v2.py:5478/8264/24057、region_ast_generator.py:33711
$ checker rebuild
  expr = `node.name == '<lambda>'`（忠实）
$ 求值次数
  934 次 / 128 个 J 条目，全假
```

**判定（d）**：d（其它）：'<lambda>' 是 CPython 自己的 co_name 约定，值真实存在；只是 J 里 934 次进入 _generate_function_def 的都不是 lambda（region_ast_generator/ast_generator 侧先处理掉了）。

**处置**：保留 open，补一条把 lambda 送进 _generate_function_def 的 J（或确认该分支被上游取代后按规则陈旧处理）。

### 抽样 12 · `RULE-4f466f58c93b` — Return（class d）

- 锚点：`core/cfg/ast_converter.py:340`（universe `kind=opcode_eq`；本条真实形态=marker）
- 该行实际源码：

```python
  340              if node_type == 'Return':
```

- pattern（`universe_v3.json`）：`node_type == 'Return'`
- 校验器重建出的谓词（`rule_proof_check._scan_file`）：`node_type == 'Return'`
- 实测：`predicate_evaluations=244`、`false_evaluations=244`、`pyc_runs_reaching_site=28`、`true_entries=0`

证据命令与输出：

```text
$ checker rebuild
  expr = `node_type == 'Return'`（忠实）
$ 'Return' 生产者
  core/ 内 169 处（ast_converter.py 等构造 Return 节点）
$ 求值次数
  244 次 / 28 个 J 条目，全假
```

**判定（d）**：d（其它）：ast_converter.py:340 的 `if node_type == 'Return':` 是局部 node_type 分发；244 次进入都没遇到 Return。属覆盖缺口。

**处置**：保留 open，补一条在 _convert_return 之外的路径上遇到 Return 的 J，或核对上游是否已把 Return 拦掉。

## 4. 每类的可执行结论

### 4-A 规则陈旧 / 不可满足 — 36 条 ⇒ 建议从宇宙排除

| symbol | anchor | 陈旧判据 | 求值次数 |
|---|---|---|---|
| `INPLACE_ADD` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `INPLACE_AND` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `INPLACE_FLOOR_DIVIDE` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `INPLACE_LSHIFT` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `INPLACE_MODULO` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `INPLACE_MULTIPLY` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `INPLACE_OR` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `INPLACE_POWER` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `INPLACE_RSHIFT` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `INPLACE_SUBTRACT` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `INPLACE_TRUE_DIVIDE` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `INPLACE_XOR` | core/cfg/region_ast_generator.py:77253 | 符号不在 `dis.opmap`(3.11.7) | 1936 |
| `MATCH_AS` | core/cfg/ast_generator_v2.py:2952 | 符号不在 `dis.opmap`(3.11.7) | 1584 |
| `MATCH_MAPPING_KEYS` | core/cfg/pattern_parser.py:2116 | 符号不在 `dis.opmap`(3.11.7) | 285 |
| `MATCH_OR` | core/cfg/ast_generator_v2.py:2967 | 符号不在 `dis.opmap`(3.11.7) | 1584 |
| `MATCH_VALUE` | core/cfg/ast_generator_v2.py:2890 | 符号不在 `dis.opmap`(3.11.7) | 1584 |
| `POP_JUMP_IF_FALSE` | core/cfg/ast_generator_v2.py:5243 | 符号不在 `dis.opmap`(3.11.7) | 5246 |
| `POP_JUMP_IF_NONE` | core/cfg/pattern_parser.py:748 | 符号不在 `dis.opmap`(3.11.7) | 1418 |
| `POP_JUMP_IF_NOT_NONE` | core/cfg/pattern_parser.py:740 | 符号不在 `dis.opmap`(3.11.7) | 1480 |
| `POP_JUMP_IF_TRUE` | core/cfg/ast_generator_v2.py:6002 | 符号不在 `dis.opmap`(3.11.7) | 3682 |
| `CALL_FUNCTION` | core/cfg/ast_generator_v2.py:1512 | 符号不在 `dis.opmap`(3.11.7) | 18399 |
| `CALL_FUNCTION_KW` | core/cfg/region_ast_generator.py:4557 | 符号不在 `dis.opmap`(3.11.7) | 406 |
| `CALL_METHOD` | core/cfg/ast_generator_v2.py:1512 | 符号不在 `dis.opmap`(3.11.7) | 21873 |
| `JUMP_ABSOLUTE` | core/cfg/ast_generator_v2.py:18526 | 符号不在 `dis.opmap`(3.11.7) | 30153 |
| `JUMP_IF_FALSE` | core/cfg/region_ast_generator.py:40616 | 符号不在 `dis.opmap`(3.11.7) | 171 |
| `JUMP_IF_TRUE` | core/cfg/region_ast_generator.py:40616 | 符号不在 `dis.opmap`(3.11.7) | 171 |
| `FORWARD_JUMP_IF_FALSE` | core/cfg/region_analyzer.py:7160 | 符号不在 `dis.opmap`(3.11.7) | 979 |
| `FORWARD_JUMP_IF_TRUE` | core/cfg/region_analyzer.py:7160 | 符号不在 `dis.opmap`(3.11.7) | 979 |
| `CACHE` | core/cfg/ast_generator_v2.py:2666 | CACHE 是填充单元；`dis.get_instructions` 不产出（cfg_builder.py:136） | 72749 |
| `GenExpr` | core/cfg/code_generator.py:3788 | IR 取值无生产者（0/6 处写它） | 213 |
| `LOAD_CONSTANT` | core/cfg/ast_generator_v2.py:1062 | 符号不在 `dis.opmap`(3.11.7) | 49826 |
| `RAISE` | core/cfg/ast_generator_v2.py:2570 | 符号不在 `dis.opmap`(3.11.7) | 3473 |
| `RETURN_CONST` | core/cfg/ast_generator_v2.py:1877 | 符号不在 `dis.opmap`(3.11.7) | 59342 |
| `SETUP_LOOP` | core/cfg/region_analyzer.py:4663 | 符号不在 `dis.opmap`(3.11.7) | 257 |
| `UNPACK_EXTRACT` | core/cfg/pattern_parser.py:2190 | 符号不在 `dis.opmap`(3.11.7) | 283 |
| `__NESTED_FUNC__` | core/cfg/code_generator.py:4115 | IR 取值无生产者（0/1 处写它） | 14871 |

分组计数（36 = 33 个不在 `dis.opmap` 的操作码名 + 1 个 CACHE 死分支 + 2 个无生产者的 IR 取值）：

| 族 | 条数 | symbol |
|---|---|---|
| INPLACE_* | 12 | INPLACE_ADD, INPLACE_AND, INPLACE_FLOOR_DIVIDE, INPLACE_LSHIFT, INPLACE_MODULO, INPLACE_MULTIPLY, INPLACE_OR, INPLACE_POWER, INPLACE_RSHIFT, INPLACE_SUBTRACT, INPLACE_TRUE_DIVIDE, INPLACE_XOR |
| MATCH_* | 4 | MATCH_AS, MATCH_MAPPING_KEYS, MATCH_OR, MATCH_VALUE |
| POP_JUMP_* | 4 | POP_JUMP_IF_FALSE, POP_JUMP_IF_NONE, POP_JUMP_IF_NOT_NONE, POP_JUMP_IF_TRUE |
| CALL_* | 3 | CALL_FUNCTION, CALL_FUNCTION_KW, CALL_METHOD |
| JUMP_* | 3 | JUMP_ABSOLUTE, JUMP_IF_FALSE, JUMP_IF_TRUE |
| FORWARD_JUMP_* | 2 | FORWARD_JUMP_IF_FALSE, FORWARD_JUMP_IF_TRUE |
| CACHE | 1 | CACHE |
| GenExpr | 1 | GenExpr |
| LOAD_* | 1 | LOAD_CONSTANT |
| RAISE | 1 | RAISE |
| RETURN_CONST | 1 | RETURN_CONST |
| SETUP_LOOP | 1 | SETUP_LOOP |
| UNPACK_EXTRACT | 1 | UNPACK_EXTRACT |
| __NESTED_FUNC__ | 1 | __NESTED_FUNC__ |

结论与影响：

- 这 36 条**在任何 3.11 J 语料下都不可能 true**：33 条的符号名不在 `dis.opmap`（3.11.7）里，1 条（CACHE）是 `dis` 不产出的填充单元，2 条是 core/ 无生产者的 IR 取值。
- 建议：从 `universe_v3.json` 的 344 条中排除这 36 条（或改标 `legacy_name`/`dead_branch` 不计入 completeness 分母）。排除后分母 344→308，已 proved 的 127 条不变（D3 从 113 降到 77）。
- 注意：这些**源码行本身不算陈旧**（如 77253 的 `BINARY_OP + 12 个 INPLACE_*` 守卫是跨版本兼容写法，保留是对的），陈旧的是「把兼容名当成 3.11 可满足谓词」的规则建模。因此不建议改 `core/`。

### 4-B 锚点错位 — 0 条

- 88/88 的 pattern 都在声明行上（§2.4）；无需重定位，预计可 proved +0。
- 说明：v3 的 `anchors_located=5896/5896`、`predicate_not_located=0` 与本结论一致；我另行重建了 5260 个候选、`unmapped=0`（§7 `rebuild.py` 输出）。

### 4-C 谓词语义不匹配 — 8 条 ⇒ 需改一处口径（二选一，先定口径再改代码）

| symbol | anchor | 校验器实际求的谓词 | 同守卫被实测满足的成员(true_evals) | 本规则 false 次数 |
|---|---|---|---|---|
| DELETE_DEREF | core/cfg/region_analyzer.py:2463 | instr.opname == 'DELETE_DEREF' | STORE_DEREF(9) | 22581 |
| DELETE_GLOBAL | core/cfg/region_analyzer.py:23701 | _ei.opname == 'DELETE_GLOBAL' | STORE_FAST(107)、STORE_NAME(135)、STORE_GLOBAL(5)、STORE_DEREF(9)、STORE_ATTR(10) | 20463 |
| DELETE_NAME | core/cfg/ast_generator_v2.py:22405 | instr.opname == 'DELETE_NAME' | DELETE_FAST(3) | 20463 |
| LOAD_CLASSDEREF | core/cfg/ast_generator_v2.py:1103 | opname == 'LOAD_CLASSDEREF' | LOAD_NAME(40)、LOAD_GLOBAL(98)、LOAD_FAST(122)、LOAD_DEREF(31)、LOAD_CLOSURE(24) | 40758 |
| List | core/cfg/code_generator.py:2174 | node_type == 'List' | Starred(14) | 2 |
| POP_JUMP_BACKWARD_IF_NONE | core/cfg/ast_generator_v2.py:1410 | opname == 'POP_JUMP_BACKWARD_IF_NONE' | POP_JUMP_FORWARD_IF_NONE(21) | 17440 |
| POP_JUMP_BACKWARD_IF_NOT_NONE | core/cfg/ast_generator_v2.py:1372 | opname == 'POP_JUMP_BACKWARD_IF_NOT_NONE' | POP_JUMP_FORWARD_IF_NOT_NONE(13) | 17497 |
| SET_ADD | core/cfg/ast_generator_v2.py:5237 | instructions[j].opname == 'SET_ADD' | FOR_ITER(77)、GET_ANEXT(11)、LIST_APPEND(3)、YIELD_VALUE(20) | 41 |

差异在哪里（可复现，不必重跑 trace）：

- 源码是**一个 N 成员守卫**，例如 `core/cfg/region_analyzer.py:23701`：`if _ei.opname in ('STORE_FAST', ..., 'DELETE_GLOBAL', ...)`。
- 校验器把同一守卫拆成 N 个候选，逐个求 `left == 'SYM'`（`tools/completeness/rule_proof_check.py:354-367`，其中 `in` + 元组分支在 356-362 行把 `test` 改写成 `left == Constant(symbol)`）。
- 于是「守卫被 STORE_FAST 满足」的那次访问里，`_ei.opname == 'DELETE_GLOBAL'` 必然为假，本条被记成 false-only（实测 DELETE_GLOBAL 20463 次求值全假，而同守卫 STORE_FAST 有 107 次 true 且已 proved）。
- 同一构造在校验器里有**两套口径**：集合写成字面量元组 ⇒ 投影成单成员等式；集合写成变量名 ⇒ 整条守卫一起求值（`_opcode_tests` 的 Name/Attribute 分支，`rule_proof_check.py:233-234`，例：`_b113_stop_ops` 的候选 expr 是`first_instr.opname in _b113_stop_ops`）。这就是口径缺陷本身。

改哪一处、以及预计可 proved：

1. **改规则模型（推荐，改动在 `tools/completeness/rule_universe.py` 的规则身份 + 校验器的候选生成）**：同一守卫只生成 1 条规则，`symbol` 用守卫表达式（或 `GUARD:<file>:<line>`），谓词取整条 `pattern`。这样这 8 条立即同时具备正见证（守卫被满足的条目）与负见证（守卫未满足的条目，已有）⇒ **+8 proved**。
2. **只改校验器（`rule_proof_check.py:356-362`）而不改规则身份**：会让同一守卫的每个成员在同一访问上全部为真，等于把「逐操作码覆盖」降格成「逐守卫覆盖」，G4 声称的语义会变弱——不建议。
3. **什么都不改**：这 8 条的符号在 3.11 都真实可产出（7 个操作码全部通过 3.11.7 产出探针——`LOAD_CLASSDEREF` 需 `def outer(): v=1; class C: w=v` 这类「函数内类体引用外层自由变量」构造；`'List'` 有 18 处生产者），属「一条 J 就能证明」⇒ 各补 1 条定向 J 即可 **+8 proved**（探针：`probe_emit.py`，见 §7）。

两类口径下的条数对照：

- 按 `pattern` 语义（整条守卫）= 规则：8 条可救，改口径即 proved。
- 按 `symbol` 语义（单成员）= 规则：这 8 条仍是覆盖缺口，需 8 条新 J。
- 另有 **27 条 a 类**同样处在「守卫被别人满足」的场景（`guard_true_with_other_member=True`），但因为它们的成员名在 3.11 不存在，**改口径也救不回来**，所以必须排除——这也说明「改口径」不能替代 a 类排除。

### 4-D 其它（规则有效、J 未覆盖）— 44 条 ⇒ 补 J，不改代码

| 子类 | 条数 |
|---|---|
| 操作码名谓词（活操作码，131 个 J 未在该点产出） | 10 |
| 命名集合守卫（整条守卫忠实求值，守卫未命中） | 11 |
| AST/IR 标记谓词（取值真实存在，J 未走到该分支） | 23 |

三类各自需要什么样的 J（每条都只差 1 条 J：负见证已存在，补上正见证即 proved）：

- **操作码 10 条**：`END_ASYNC_FOR`(需 async for)、`MAP_ADD`(dict 推导)、`MATCH_KEYS`/`MATCH_MAPPING`(match 语句)、`SETUP_ANNOTATIONS`(模块级注解)、`SET_UPDATE`(`{*a, *b}`)、`UNARY_INVERT`(`~x`)、`UNARY_NEGATIVE/NOT/POSITIVE`。全部有 3.11.7 产出探针证据（§7 `siblings2.py`：`dis_emitted=True`）。
- **命名集合守卫 11 条**：集合成员里多数是 3.11 活操作码（`_LITERAL_BUILD_OPS` 5/5、`_STORE_CHK_P21` 6/6、`_b68_machinery` 6/6、`_closure_setup` 3/3、`_pre_store_ops` 4/4、`_pad` 4/4、`_lit_skip_ops` 4/4、`_WALRUS_INTEGRATING_OPS` 9/9、`_kop_names` 2/2；仅 `_b113_stop_ops`(14/16)、`_TRUE_POLARITY_COND_JUMP_OPS`(2/3) 含死名）。这些守卫的「假」多为循环/扫描的**正常退出口**，要给的是「扫描位置恰好落在集合内」的 J。
- **AST/IR 标记 23 条**：主要是 `code_generator.py` 的 dict-IR 回退分支（`node_type == 'Dict'/'Set'/'Tuple'/'Subscript'/...`，多次只被求值 2 次）与 `ast_converter.py:340` 的 `'Return'`。需要一条真正走 dict-IR 回退路径的 J（不是普通 ASTNode 路径）。

## 5. 88 条全表

排序：class → 文件 → 行号。`ev/false/runs` = `predicate_evaluations / false_evaluations / pyc_runs_reaching_site`。

| 类 | symbol | anchor | 形态 | ev/false/runs | 判据 |
|---|---|---|---|---|---|
| a | `LOAD_CONSTANT` | core/cfg/ast_generator_v2.py:1062 | opcode | 49826/49826/131 | 符号不在 `dis.opmap`(3.11.7) |
| a | `CALL_FUNCTION` | core/cfg/ast_generator_v2.py:1512 | opcode | 18399/18399/131 | 符号不在 `dis.opmap`(3.11.7) |
| a | `CALL_METHOD` | core/cfg/ast_generator_v2.py:1512 | opcode | 21873/21873/131 | 符号不在 `dis.opmap`(3.11.7) |
| a | `RETURN_CONST` | core/cfg/ast_generator_v2.py:1877 | opcode | 59342/59342/131 | 符号不在 `dis.opmap`(3.11.7) |
| a | `RAISE` | core/cfg/ast_generator_v2.py:2570 | opcode | 3473/3473/130 | 符号不在 `dis.opmap`(3.11.7) |
| a | `CACHE` | core/cfg/ast_generator_v2.py:2666 | opcode | 72749/72749/131 | CACHE 是填充单元；`dis.get_instructions` 不产出（cfg_builder.py:136） |
| a | `MATCH_VALUE` | core/cfg/ast_generator_v2.py:2890 | opcode | 1584/1584/96 | 符号不在 `dis.opmap`(3.11.7) |
| a | `MATCH_AS` | core/cfg/ast_generator_v2.py:2952 | opcode | 1584/1584/96 | 符号不在 `dis.opmap`(3.11.7) |
| a | `MATCH_OR` | core/cfg/ast_generator_v2.py:2967 | opcode | 1584/1584/96 | 符号不在 `dis.opmap`(3.11.7) |
| a | `POP_JUMP_IF_FALSE` | core/cfg/ast_generator_v2.py:5243 | opcode | 5246/5246/112 | 符号不在 `dis.opmap`(3.11.7) |
| a | `POP_JUMP_IF_TRUE` | core/cfg/ast_generator_v2.py:6002 | opcode | 3682/3682/111 | 符号不在 `dis.opmap`(3.11.7) |
| a | `JUMP_ABSOLUTE` | core/cfg/ast_generator_v2.py:18526 | opcode | 30153/30153/131 | 符号不在 `dis.opmap`(3.11.7) |
| a | `GenExpr` | core/cfg/code_generator.py:3788 | marker | 213/213/11 | IR 取值无生产者（0/6 处写它） |
| a | `__NESTED_FUNC__` | core/cfg/code_generator.py:4115 | marker | 14871/14871/131 | IR 取值无生产者（0/1 处写它） |
| a | `POP_JUMP_IF_NOT_NONE` | core/cfg/pattern_parser.py:740 | opcode | 1480/1480/51 | 符号不在 `dis.opmap`(3.11.7) |
| a | `POP_JUMP_IF_NONE` | core/cfg/pattern_parser.py:748 | opcode | 1418/1418/51 | 符号不在 `dis.opmap`(3.11.7) |
| a | `MATCH_MAPPING_KEYS` | core/cfg/pattern_parser.py:2116 | opcode | 285/285/12 | 符号不在 `dis.opmap`(3.11.7) |
| a | `UNPACK_EXTRACT` | core/cfg/pattern_parser.py:2190 | opcode | 283/283/11 | 符号不在 `dis.opmap`(3.11.7) |
| a | `SETUP_LOOP` | core/cfg/region_analyzer.py:4663 | opcode | 257/257/9 | 符号不在 `dis.opmap`(3.11.7) |
| a | `FORWARD_JUMP_IF_FALSE` | core/cfg/region_analyzer.py:7160 | opcode | 979/979/36 | 符号不在 `dis.opmap`(3.11.7) |
| a | `FORWARD_JUMP_IF_TRUE` | core/cfg/region_analyzer.py:7160 | opcode | 979/979/36 | 符号不在 `dis.opmap`(3.11.7) |
| a | `CALL_FUNCTION_KW` | core/cfg/region_ast_generator.py:4557 | opcode | 406/406/34 | 符号不在 `dis.opmap`(3.11.7) |
| a | `JUMP_IF_FALSE` | core/cfg/region_ast_generator.py:40616 | opcode | 171/171/32 | 符号不在 `dis.opmap`(3.11.7) |
| a | `JUMP_IF_TRUE` | core/cfg/region_ast_generator.py:40616 | opcode | 171/171/32 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_ADD` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_AND` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_FLOOR_DIVIDE` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_LSHIFT` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_MODULO` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_MULTIPLY` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_OR` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_POWER` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_RSHIFT` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_SUBTRACT` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_TRUE_DIVIDE` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| a | `INPLACE_XOR` | core/cfg/region_ast_generator.py:77253 | opcode | 1936/1936/13 | 符号不在 `dis.opmap`(3.11.7) |
| c | `LOAD_CLASSDEREF` | core/cfg/ast_generator_v2.py:1103 | opcode | 40758/40758/131 | 守卫被投影成单成员等式；同守卫已由 LOAD_NAME/LOAD_GLOBAL/LOAD_FAST 满足 |
| c | `POP_JUMP_BACKWARD_IF_NOT_NONE` | core/cfg/ast_generator_v2.py:1372 | opcode | 17497/17497/131 | 守卫被投影成单成员等式；同守卫已由 POP_JUMP_FORWARD_IF_NOT_NONE 满足 |
| c | `POP_JUMP_BACKWARD_IF_NONE` | core/cfg/ast_generator_v2.py:1410 | opcode | 17440/17440/131 | 守卫被投影成单成员等式；同守卫已由 POP_JUMP_FORWARD_IF_NONE 满足 |
| c | `SET_ADD` | core/cfg/ast_generator_v2.py:5237 | opcode | 41/41/9 | 守卫被投影成单成员等式；同守卫已由 FOR_ITER/GET_ANEXT/LIST_APPEND 满足 |
| c | `DELETE_NAME` | core/cfg/ast_generator_v2.py:22405 | opcode | 20463/20463/131 | 守卫被投影成单成员等式；同守卫已由 DELETE_FAST 满足 |
| c | `List` | core/cfg/code_generator.py:2174 | marker | 2/2/1 | 守卫被投影成单成员等式；同守卫已由 Starred 满足 |
| c | `DELETE_DEREF` | core/cfg/region_analyzer.py:2463 | opcode | 22581/22581/131 | 守卫被投影成单成员等式；同守卫已由 STORE_DEREF 满足 |
| c | `DELETE_GLOBAL` | core/cfg/region_analyzer.py:23701 | opcode | 20463/20463/131 | 守卫被投影成单成员等式；同守卫已由 STORE_FAST/STORE_NAME/STORE_GLOBAL 满足 |
| d | `Return` | core/cfg/ast_converter.py:340 | marker | 244/244/28 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `MAP_ADD` | core/cfg/ast_generator_v2.py:1607 | opcode | 16171/16171/131 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `SET_UPDATE` | core/cfg/ast_generator_v2.py:1655 | opcode | 16144/16144/131 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `MATCH_MAPPING` | core/cfg/ast_generator_v2.py:2917 | opcode | 1867/1867/97 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `MATCH_KEYS` | core/cfg/ast_generator_v2.py:2930 | opcode | 1869/1869/97 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `UNARY_NEGATIVE` | core/cfg/ast_generator_v2.py:6571 | opcode | 66/66/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `UNARY_NOT` | core/cfg/ast_generator_v2.py:6571 | opcode | 66/66/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `UNARY_POSITIVE` | core/cfg/ast_generator_v2.py:6571 | opcode | 66/66/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `END_ASYNC_FOR` | core/cfg/ast_generator_v2.py:8409 | opcode | 1900/1900/32 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `Lambda` | core/cfg/code_generator.py:361 | marker | 211/211/11 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `Yield` | core/cfg/code_generator.py:448 | marker | 189/189/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `YieldFrom` | core/cfg/code_generator.py:456 | marker | 189/189/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `<target>` | core/cfg/code_generator.py:2116 | marker | 390/390/69 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `Tuple` | core/cfg/code_generator.py:2150 | marker | 2/2/1 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `<lambda>` | core/cfg/code_generator.py:2396 | marker | 934/934/128 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `DictComp` | core/cfg/code_generator.py:3780 | marker | 213/213/11 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `ListComp` | core/cfg/code_generator.py:3782 | marker | 213/213/11 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `SetComp` | core/cfg/code_generator.py:3784 | marker | 213/213/11 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `GeneratorExp` | core/cfg/code_generator.py:3786 | marker | 213/213/11 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `Iter` | core/cfg/code_generator.py:3790 | marker | 211/211/11 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `Subscript` | core/cfg/code_generator.py:3910 | marker | 191/191/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `Slice` | core/cfg/code_generator.py:3930 | marker | 189/189/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `JoinedStr` | core/cfg/code_generator.py:3932 | marker | 191/191/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `FormattedValue` | core/cfg/code_generator.py:3935 | marker | 191/191/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `BoolOp` | core/cfg/code_generator.py:3960 | marker | 189/189/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `UnaryOp` | core/cfg/code_generator.py:3963 | marker | 189/189/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `Compare` | core/cfg/code_generator.py:3966 | marker | 189/189/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `Await` | core/cfg/code_generator.py:3969 | marker | 187/187/10 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `Attribute` | core/cfg/code_generator.py:4032 | marker | 2/2/1 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `Set` | core/cfg/code_generator.py:4047 | marker | 2/2/1 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `Dict` | core/cfg/code_generator.py:4055 | marker | 2/2/1 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `_closure_setup` | core/cfg/comprehension_generator.py:554 | setname | 149/149/20 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `_b113_stop_ops` | core/cfg/comprehension_generator.py:2379 | setname | 88/88/28 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `_kop_names` | core/cfg/comprehension_generator.py:3977 | setname | 187/187/6 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `_pad` | core/cfg/comprehension_generator.py:6219 | setname | 5/5/2 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `SETUP_ANNOTATIONS` | core/cfg/region_ast_generator.py:940 | opcode | 685/685/25 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `_b68_machinery` | core/cfg/region_ast_generator.py:5399 | setname | 197/197/12 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `UNARY_INVERT` | core/cfg/region_ast_generator.py:51769 | opcode | 65/65/9 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `_STORE_CHK_P21` | core/cfg/region_ast_generator.py:54561 | setname | 7/7/4 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `_TRUE_POLARITY_COND_JUMP_OPS` | core/cfg/region_ast_generator.py:56270 | setname | 3/3/3 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `_pre_store_ops` | core/cfg/region_ast_generator.py:59014 | setname | 7/7/2 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `_lit_skip_ops` | core/cfg/region_ast_generator.py:73913 | setname | 4/4/1 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `_LITERAL_BUILD_OPS` | core/cfg/region_ast_generator.py:73920 | setname | 3/3/1 | 取值在 3.11 真实可产出，J 未覆盖 |
| d | `_WALRUS_INTEGRATING_OPS` | core/cfg/region_ast_generator.py:73922 | setname | 3/3/1 | 取值在 3.11 真实可产出，J 未覆盖 |

## 6. 校验器 / 规则模型的口径缺陷（不改，只登记）

### D1 membership 守卫被投影成单成员等式（8 条 c 类的直接原因）

- 位置：`tools/completeness/rule_proof_check.py:354-367`（`_scan_file` 的 opcode 分支 + `emit`），关键在 356-362：`in (lit...)` 被改写成 `ast.Compare(left, [Eq()], [Constant(symbol)])`。
- 与 233-234（`_opcode_tests` 对 Name/Attribute 容器返回 `ast.unparse(container)` 作 symbol、谓词保持整条 test）**自相矛盾**：同一语义（成员集合）因写法不同而有两套求值口径。
- 影响：40 条规则有同守卫兄弟（本报告口径），其中 35 条的守卫「被别的成员满足过」；8 条活成员规则因此被判 false-only（c 类），27 条死成员规则被同一机制掩盖（但真正原因是 a 类陈旧）。
- 若要判「某 opcode 是否被该行处理」，单成员等式是对的；若要判「该守卫行是否被执行到有效分支」，整条守卫才对。**必须先定 G4 想证明哪一件事**，再决定改 `rule_universe.py`（规则身份）还是 `rule_proof_check.py`（求值）。

### D2 `kind` 记账口径：AST 标记比较被记成 `opcode_eq`

- 位置：`tools/completeness/rule_proof_check.py:73` `OP_NAMES = {"opname", "opcode", "name", "kind", "node_type", "node_name"}`。
- 后果：88 条里 26 条 `node_type/name == 'X'` 被归为 `opcode_eq`（`universe_v3.json` 里 `isinstance_ast` 只有 15 条），任务要求的「isinstance_ast vs opcode_eq」分组因此无法用于 D3 定性（§2.1）。
- 建议：给标记比较单独的 `kind`（如 `ir_marker_eq`），`symbol` 保留取值；不影响本报告结论。

### D3 命名集合守卫的规则身份是**局部变量名**（11 条）

- 例：`_pad`、`_b68_machinery`、`_kop_names`、`_pre_store_ops`、`_LITERAL_BUILD_OPS`…`proof_records_v2.json` 的 `symbol` 就是这些变量名。
- `rule_id = sha256(kind|symbol|anchor)`（`G4_PROOF_THEORY.md` 的 proof_id 口径）不含集合内容：改动集合成员不会触发 `anchor_source_drift`（该校验只看文件 sha），规则语义会静默漂移。
- 建议（后续 gate）：把集合内容纳入 rule_id，或在 `universe_v3.json` 里固化 `set_members`。本报告已在 JSON 里为这 11 条记录 `set_members` / `set_dead_members`。

## 7. 复现

所有脚本在 `D:\temp\opencode\cl_layout\g4d3\`（只读分析，全部可用 `D:/Python/python.exe -X utf8 <script>` 重跑，cwd=`F:\Downloads\pythoncdc-main`）：

| 脚本 | 作用 |
|---|---|
| `dump88.py` | 取出 88 条并逐条打印 anchor 行源码 → `dump88.json` |
| `shape88.py` | pattern 形态分类 + `dis.opmap` 成员检查 → `shapes.json` |
| `sets_markers.py` | 11 条命名集合的定义解析；25 条 `==` 形态标记字面量的全树出现点 |
| `siblings2.py` | 守卫兄弟 + 3.11.7 产出探针（dis 与 raw co_code 双口径） → `probe2.json` |
| `probe_emit.py` | 18 个「活符号」的 3.11.7 产出探针（含 CACHE 反例）：证明 d/c 类只差一条 J |
| `rebuild.py` | 导入校验器 `_scan_file`，打印 12 个锚点重建出的谓词（c 类的直接证据） |
| `classify3.py` | 最终分类（守卫成员取自校验器自己的候选，按 If-test AST 路径对齐） → `g4_d3_classification.json` |
| `grepc.py` | `grep -cF` 的等价实现（本机无 grep 二进制），`--lines` 打印命中行 |
| `stats.py` | 分布/兄弟统计 |

关键一次性证据（原样命令）：

```text
$ D:/Python/python.exe -X utf8 -c "import dis,sys;print(sys.version);print('CALL_FUNCTION' in dis.opmap, 'INPLACE_MULTIPLY' in dis.opmap, 'CACHE' in dis.opmap)"
3.11.7 (tags/v3.11.7:fa7a6f2, Dec  4 2023, 19:24:49) [MSC v.1937 64 bit (AMD64)]
False False True

$ D:/Python/python.exe -X utf8 -c "import importlib.util as u;print(u.MAGIC_NUMBER.hex())"   # 与 J pyc 头 a70d0d0a 一致
a70d0d0a
```

