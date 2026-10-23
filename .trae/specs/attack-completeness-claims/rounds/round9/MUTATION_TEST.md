# Task 9.2 变异测试驱动

- 工具：`tools/completeness/mutation_test.py` v1.0.0
- 自测：`tools/completeness/mutation_test_selftest.py`，9/9 通过
- 证据：`rounds/round9/mutation_selftest.json`
- 真实冒烟：`rounds/round9/mutation_smoke_server_version.json`
- 后端：`tools/completeness/semantic_diff.py` v1.0.0

## 1. 定位

变异测试不是「把现有用例改一改」，也不是从规则清单反推样本。它的总体来自：

1. 读取原始源码；
2. 遍历原始 AST 的全部节点；
3. 按固定算子逐节点生成候选；
4. 先验证「原源码 → `ast.unparse` → 重编译」基线仍为 `EQUAL`；
5. 再逐个编译 mutant，用同一 `case` 的入口、调用、环境、种子与原始产物做 `semantic_diff`。

因此，变异总体与当前规则表、当前 J 空间、当前通过用例相互独立；用例只决定「哪些变异能被观察到」，不决定「生成哪些变异」。

## 2. 算子与候选

当前确定性算子（v1.0.0）：

| 算子 | 变换 |
|---|---|
| `binop` | `Add/Sub/Mult/Div/FloorDiv/Mod/Pow/Shift/Bit/MatMult` 固定交换 |
| `compare` | `Eq/NotEq/Lt/LtE/Gt/GtE/Is/IsNot/In/NotIn` 固定交换 |
| `augassign` | `Add/Sub/Mult/Div/FloorDiv/Mod/Bit` 固定交换 |
| `unaryop` | `USub↔UAdd`、`Invert→Not` |
| `boolop` | `and↔or` |
| `constant` | 数值 `+1`、字符串/字节追加 `_mut`、`None→0`、布尔取反 |
| `return` | `return value → return None` |
| `if` / `while` | 条件取反 |

每个候选记录：

```json
{"mutation_id":"M0002","operator":"binop","description":"Mult -> FloorDiv",
 "lineno":2,"col_offset":11,"path":[["body",0],["value",null]],"payload":{"op":"FloorDiv"}}
```

`path` 是 AST 字段路径，不依赖行号，避免格式变化导致错位。链式比较只变异第一个比较符；这是 v1 的明确边界，不是「已覆盖全部比较」。

## 3. 基线身份检查

在生成任何 mutant 前，工具先做：

```
原始源码 -> ast.parse -> ast.unparse -> 写 baseline.py -> semantic_diff(case, baseline.py)
```

只有基线为 `EQUAL` 才继续。否则报告 `ABORTED_BASELINE`，退出码 3，不产生「killed/missed」读数。

这防止把 `ast.unparse` 的格式变化、编译器元数据差异或源码/产物不匹配误算成变异杀死。基线失败时，报告保留 `baseline.diffs` 供定位，不把失败包装成「工具通过」。

## 4. 判定与统计

对每个 mutant，调用与 Task 9.1 相同的 `semantic_diff.compare_case`。`semantic_diff` 的 `DIFFERENT` 仍然是严格差分；变异层再做证明解释：

| semantic_diff | 等价证明 | 变异层状态 |
|---|---|---|
| `DIFFERENT` | 无，且存在 R1–R6 或非 code 元数据差异 | `KILLED` |
| `DIFFERENT` | 无，且差异全部位于 `$.metadata.code.*` | `MISSED`（只有字节码差异、行为未观察到；不得算 killed） |
| `DIFFERENT` | 有，且差异全部位于 `$.metadata.code.*` | `EQUIVALENT`（行为层等价；记录 `equivalence_note`） |
| `DIFFERENT` | 有，但存在 R1–R6 或非 code 元数据差异 | `FALSE_KILL` |
| `EQUAL` | 无 | `MISSED` |
| `EQUAL` | 有 | `EQUIVALENT` |
| `INCONCLUSIVE` | 任意 | `INCONCLUSIVE` |
| `ERROR` | 任意 | `ERROR` |

计数口径：

```
scored      = KILLED + MISSED
mutation_score = KILLED / scored
missed_rate    = MISSED / scored
false_kill_rate = FALSE_KILL / evaluated
```

- `EQUIVALENT` 不计入分母；`INCONCLUSIVE` / `ERROR` 永不计为 killed。
- `FALSE_KILL` 表示「证明说等价，但 R1–R6 或非 code 元数据仍有差异」，是证明/判据冲突，不是通过。
- `mutation_score` 只描述当前判据在当前变异总体上的观察能力，不是完备性证明。
- 退出码：`0` 无 missed/false-kill；`1` 有 missed（`--allow-missed` 可放行）；`2` 有 inconclusive；`3` baseline 失败、error 或 false-kill。

## 5. 等价证明清单

格式：

```json
{
  "M0002": {
    "proof": "case 域为 int；x*1 == x//1 对 int x 成立",
    "scope": "case-relative"
  }
}
```

规则：

- 证明必须非空；空证明直接报错。
- 工具不验证证明的数学真值，只负责把它绑定到 mutation id 并在报告中保留。
- `scope` 由提交者声明，通常是 `case-relative` 或 `global`；当前自测只用 `case-relative`。
- 证明只覆盖行为层；若仍有 R1–R6 差异，判 `FALSE_KILL`。
- 只允许「仅有 code 元数据差异」的证明走 `EQUIVALENT`，避免把真实行为差异用一句证明抹掉。

## 6. 自测证据

`mutation_selftest.json`：9/9 checks 通过。

主体用例：

```python
def mix(a, b):
    if a > b:
        return a - b
    return a + b

def unused(a, b):
    return a * b
```

调用：`(5,3)`、`(2,4)`、`(2,2)`；入口 `mix`。

读数：

| 指标 | 值 |
|---|---:|
| baseline | `EQUAL` |
| generated / selected | 8 / 8 |
| KILLED | 6 |
| MISSED | 2 |
| EQUIVALENT | 0 |
| FALSE_KILL | 0 |
| INCONCLUSIVE / ERROR | 0 / 0 |
| mutation_score | 0.75 |
| missed_rate | 0.25 |

两个 survivor 都位于未被调用的 `unused` 函数（`return None`、`Mult -> FloorDiv`）；这是用例覆盖缺口，不是工具把 survivor 算成 killed。

等价证明用例：

```python
def f(x):
    return x * 1
```

`Mult -> FloorDiv` 的 mutant 为 `x // 1`；case 域为 int。证明清单绑定该 mutation id 后：

| 指标 | 值 |
|---|---:|
| KILLED | 2 |
| EQUIVALENT | 1 |
| FALSE_KILL | 0 |
| mutation_score | 1.0 |

该 mutant 的唯一差异是 `$.metadata.code.co_code.sha256`；按上表解释为行为层等价，而不是 `FALSE_KILL`。

同一 mutant 在**不提供证明**时读数为：

| 指标 | 值 |
|---|---:|
| KILLED | 2 |
| MISSED | 1 |
| mutation_score | 0.6667 |
| missed_rate | 0.3333 |

这证明工具不会把「只有字节码差异」自动算成 killed；缺少证明时按 survivor 处理。

## 7. 真实 pyc 冒烟

`mutation_smoke_server_version.json`：

- 原始：`site-packages/fly/server_version.pyc`
- 源码：`site-packages/fly/server_versionOK.py`
- 入口：`module`
- baseline：`EQUAL`
- 生成 1 个变异（模块常量字符串追加 `_mut`）
- 结果：`KILLED`，1/1；`FALSE_KILL=0`

该冒烟只证明「pyc 原始 + 源码变异 + 真实模块入口」链路可跑，不证明 402 语料已被变异覆盖。

## 8. 明确边界

1. 算子是有限集合，不是「所有可能的源码变异」；没有 `match`、装饰器、推导式、参数默认值、异常处理分支等专用算子。
2. 链式比较只变异首项；`await`/生成器消费等语义由 `semantic_diff` 的后端边界决定。
3. `ast.unparse` 可能丢失类型注释、格式和部分源码信息；基线失败会中止，不会静默继续。
4. 等价证明由评审者提供，工具不承担证明真值；`case-relative` 证明不能外推到其他调用域。
5. 未调用函数、未触发分支的 survivor 是预期的覆盖缺口；要减少它应补 case 或扩大入口，而不是改统计口径。
6. `semantic_diff` 不是 OS 级沙箱；时间、网络、UUID、PID 未冻结；全局变量观测上限 200，超出即 `INCONCLUSIVE`。
7. `mutation_score` 不能写成「完备性百分比」；它只进入 G3 的 killed/survived 计数器，最终措辞仍受 Task 8 双读数与 Task 10 门禁约束。

## 9. 用法

```text
python -X utf8 tools/completeness/mutation_test.py \
  --case case.json --source subject.py --out mutations.json

python -X utf8 tools/completeness/mutation_test.py --case case.json --source subject.py --list
python -X utf8 tools/completeness/mutation_test.py --case case.json --source subject.py \
  --equivalents equivalents.json --max-mutants 200 --allow-missed
```

`case.json` 的 `original` / `calls` / `entrypoint` / 容差字段与 Task 9.1 相同；`--source` 可省略，此时取 `case.source` 或 `case.original.source`。
