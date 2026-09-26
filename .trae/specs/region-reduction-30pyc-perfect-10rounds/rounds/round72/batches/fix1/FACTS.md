# R72 · fix1 — genexpr/listcomp Different bytecode 族 · FACTS

臂名 **fix1a**；spec `specs/fix1_comp_split.json`（单文件 `core/cfg/comprehension_generator.py`，3 edits，+79 行）。
镜像 `D:/Temp/opencode/r72gate/center/mirr_fix1a`，产物 `center/build_fix1a/`。
repo 未改一字节（`git status --porcelain` 无 `M`，仅历史遗留 `??`）。

---

## 1. 族聚类

11 个失败单元全部落在 `comprehension_generator._extract_comp_ifs` 的**过滤条件重建**上，两条互不相干的根因：

| 族 | 单元数 | pyc | 形状 |
|---|---|---|---|
| **A. and 链行界** | 10 | future_position 4、live_future_position 4、option_position 2 | `sum((e for o in it if A and B))`，A=`…entrust_direction == …`，B=`futures_direction == …` |
| **B. None 恒等极性** | 1 | asset_mixin | `[i for i in … if i]`，原码实为 `if i is not None` |

其余推导式单元（`in (CLOSE, CLOSE_TODAY)` 链、链式比较 `<= … <=`、OR 过滤）全部保持原样。

---

## 2. 根因（到行）

### 族 A —— 10 单元

CPython 3.11 按 **and 链各操作数所处的源码物理行**选跳转方向（`synth/linebreak_and_jump.py` 一条命令可复现）：

| 原源码 A/B 行界 | 首条条件跳转 | 目标 |
|---|---|---|
| 同行 | `POP_JUMP_BACKWARD_IF_FALSE` | 循环头（offset 8 / 10） |
| 换行 | `POP_JUMP_FORWARD_IF_FALSE` | 循环体末尾的 `JUMP_BACKWARD`（offset 114 / 76） |

产物一律单行（`code_generator` 从不发射多行表达式）→ 恒回跳；原 pyc 是前跳 → `argval` 分叉 → *Different bytecode*，
失败点统一在 genexpr 内 offset 20/10。`if A if B`（两个独立过滤条件）同行同样是回跳、换行同样前跳——
**唯一自由度是源码行界**，改 AST 形状无用（已实测 `twoif` 变体仍失配）。

* 证据：`dump/probe` 系列 + `probe_extract.py` 实测 `_extract_comp_ifs` 收到的段跳转——
  失配单元 `(52, FORWARD_IF_FALSE, 114), (94, BACKWARD_IF_FALSE, 8)`；
  通过单元（`in (...)`）`(52, BACKWARD, 8), (114, BACKWARD, 8)`。
* 端到端证明：手工在 `future_positionOK.py` 215/221/236/239 行的 ` and ` 前插换行 → `pyc_verify single` 83/83。

### 族 B —— 1 单元

`x is None / is not None` 被 CPython 折叠成单条 `POP_JUMP_*_IF_NONE`，指令流里没有 `COMPARE_OP/IS_OP`，
`_extract_comp_ifs` 只处理 `IF_TRUE`（包 `not`），于是裸 `i` 被当真值条件发射成 `if i` →
`POP_JUMP_IF_FALSE`，原码是 `POP_JUMP_IF_NONE`。

---

## 3. 候选 spec 与锚点断言

`specs/fix1_comp_split.json` — 3 edits，全部锚点在 LF 归一后的文件里**恰出现 1 次**，
`mbuild72` 通过（`lines=+79`），patched 全文 `compile()` 通过。

| # | 位置 | 内容 | 三要素注释 |
|---|---|---|---|
| 1 | 文件头（`class ComprehensionGenerator` 前） | 新增模块级 `_and_operand_raw_text()`：局部 import `CFGASTConverter._convert_expression` + `CodeGenerator._generate_expression(node, precedence['and'])`，渲染失败返回 `None` | ✅ |
| 2 | `_extract_comp_ifs` 段循环 1461–1471 | `not is_or_pattern` 时按 opname 补回恒等比较：`IF_NOT_NONE → x is None`、`IF_NONE → x is not None`（照抄 `region_ast_generator._fallthrough_cond_for_jump` 的极性表） | ✅ |
| 3 | BoolOp 合并 1479–1492 | 仅 `op=='and'` 且 `len(segments)==len(ifs)` 时数前缀连续 `FORWARD+IF_FALSE` 段数 p；p>0 就把 `values[p-1]` 换成 `{'type':'Name','id': 原文+'\n'+' '*15}`（+发射侧分隔空格 = 续行 16 列）；失败回退单行 | ✅ |

识别条件只用 ORIG 字节码自身的跳转方向，**无文件名/函数名/偏移阈值/名字白名单、无新增 self 状态、
无跨层 `region.entry in r.blocks`**。

**镜像完整性** — `mirr_fix1a` 共 34 个文件（`core/` 全树 + `pycdc.py`），与工作树逐文件比对**仅 1 个不同**：
`core/cfg/comprehension_generator.py`。`region_ast_generator.py` / `region_analyzer.py` /
`code_generator.py` / `ast_nodes.py` 逐字节相同 ⇒ 判据没有藏到别的文件里。

---

## 4. a–e 验证读数（臂 = fix1a）

**a. 构建** — `mbuild72.py fix1a specs/fix1_comp_split.json`
```
patched core/cfg/comprehension_generator.py edits=3 lines=+79 bytes 108192 -> 113731 BOM=False
mirror ready: D:/Temp/opencode/r72gate/center/mirr_fix1a  from 1 spec(s)
```

**b. 四支靶** — `h62 run` 官方读数 **逐项不变**；mandated `pyc_verify single` **11 失败 → 0**

| pyc | 官方 landed | 官方 fix1a | mandated landed | mandated fix1a |
|---|---|---|---|---|
| future_position | 72/72 | **72/72** | 79/83 | **83/83 success** |
| live_future_position | 64/64 | **64/64** | 71/75 | **75/75 success** |
| option_position | 60/60 | **60/60** | 65/67 | **67/67 success** |
| asset_mixin | 16/16 | **16/16** | 20/21 | **21/21 success** |

`ab` 4 支 REGRESSION=0（sha 变、mism 集合空↔空）。原始输出 `dump/fix1a_pycverify_targets.txt`、
`dump/landed_t4.jsonl`、`dump/fix1a_t4.jsonl`、`dump/fix1a_ab_targets.txt`。

**c. 金丝雀** — `h62 run` on `canary.txt`：`TALLY SAME=4 IMPROVED=0 REGRESSION=0 MOVED=0`
sha16 与 R71 钉值逐字节相同：quotation `3eb76e512df9ab1e`、market_time `af77224b34b203c4`、
datetime_func `e711b8ea86d49a15` / `9d09af09249da177`；
quotation 官方 **143/143**，mandated **152/153**（`change_his_to_forward` 的既有 control-flow 项，与本族无关）。

**d. 电池** — `closeout69.py battery landed fix1a` → **candidate columns worse-than-landed on 0 repro(s)**（82 repro）
`dump/fix1a_battery.txt`

**e. 严格尺** — `sstrict67.py build_<arm> dump/strict_list.txt`
| | ok/defects |
|---|---|
| landed | 454/456，defects **2**（asset_mixin `<listcomp>` + quotation `change_his_to_forward`） |
| fix1a | 455/456，defects **1**（仅 quotation 既有项） |

**无新增缺陷函数**，asset_mixin `<listcomp>` 由 `[seq_diff] POP_JUMP_IF_NONE` 转绿。`dump/strict_landed.json`、`dump/strict_fix1a.json`

---

## 5. 单元迁移

| | 指标 |
|---|---|
| 失配单元（四支） | **11 → 0** |
| 完全 OK 的靶 pyc | **0 → 4**（future_position **79/83 → 83/83**，另三支同步 100%） |
| 新增失败 | 0 |
| 金丝雀字节变化 | 0/4 |
| 电池回归 | 0/82 |
| 严格尺新缺陷 | 0 |

---

## 6. ADR-1 自评

**可采纳（自评：高）**，理由：

1. **判据同源**：触发条件就是原 pyc 自己的跳转方向（`segments[0]` 为 `POP_JUMP_FORWARD_IF_FALSE`），
   无任何名称/偏移/阈值/白名单。
2. **零外溢的结构性论证**：产物恒单行 ⇒ 恒回跳；因此 `segments[0]` 前跳 ⇒ 该单元**必然当前失配**，
   反之所有当前通过的单元与金丝雀 `segments[0]` 为回跳 ⇒ p=0 ⇒ 一个字节都不改
   （金丝雀 `SAME=4`、电池 `worse=0` 是这条论证的实测背书，不是运气）。
3. **净减而非换发射**：判据只在「原码确实换过行」时多发射一个续行换行，不删任何指令、不合并任何语义；
   族 B 用 `Compare(Is/IsNot, None)` 替换真值条件，指令数与原 pyc 逐条对齐（`strict` 19/20 → 20/20）。
4. **改动面**：全部落在 ALLOWED 三文件中的 `comprehension_generator.py`，3 处、+79 行（其中大半是三要素注释）；
   无新增 `self` 状态；渲染复用发射侧既有的两个对象（`CFGASTConverter` / `CodeGenerator`），
   不自造文本算法——渲染失败一律 `None` 回退单行，**宁可不修也不猜**。
5. **已知残留（不影响采纳）**：续行缩进是固定常量（15 空格 + 发射侧操作符分隔空格 = 16 列），
   对本族 10 处 `return sum((…))`（语句缩进 8）观感合理，但对语句缩进更深/更浅的推导式只是合法而非最优；
   要精确对齐操作数首列需要把语句缩进传进 `_extract_comp_ifs`，那是跨层状态，按 ADR-1 不做。
