# Task 9.1：语义级差分比较器

> 工具：`tools/completeness/semantic_diff.py`（v1.0.0）
> 自测：`tools/completeness/semantic_diff_selftest.py`
> 证据：`rounds/round9/semantic_diff_selftest.json`（17/17）
> 状态：Task 9.1 完成；Task 9.2–9.7 未开始。**不声称语料完备或 J 门槛达标。**

## 0. 为什么不能只看结构等价

规范要求以语义级证据判断「原产物」与「反编译产物」是否等价。`semantic_diff.py` 因此不比较 AST/源码文本，而是把两侧放到独立子进程沙箱中，用同一组参数、同一份种子文件、同一工作目录、同一环境与 RNG 种子执行，比较可观测行为；AST 相同、文本相同都不自动算通过。

## 1. 沙箱契约

| 项 | 实现 |
|---|---|
| 进程隔离 | 原产物、产物各跑一个 `python -B -X utf8 semantic_diff.py --worker` 子进程 |
| 工作目录 | 每侧独立临时目录；两侧种子文件逐字节相同 |
| 环境 | `PYTHONHASHSEED=<seed>`、`PYTHONDONTWRITEBYTECODE=1`、`TZ=UTC`、`TMPDIR/TEMP/TMP=<cwd>/.tmp` |
| RNG | 子进程内 `random.seed(seed)`；不冻结时间、不伪造网络 |
| 超时 | 每侧独立 `timeout_s`（默认 8s）；超时不是通过 |
| 路径清洗 | 输出中的沙箱绝对路径替换为 `<cwd>`，对象默认 repr 的内存地址归一为 `0xADDR` |
| 文件观测 | 种子前后快照（相对路径、大小、sha256）；只观测沙箱 cwd 内文件 |
| 事件观测 | stdout/stderr 写入、`open`、`remove/unlink`、`rename/replace` 按发生顺序记录 |
| 全局观测 | 默认 `observe_globals=["*"]`（所有非 dunder、非模块全局）；显式 `[]` 可关闭 |

## 2. 观测维度（R1–R7）

| 维度 | 比较内容 | 失败含义 |
|---|---|---|
| R1 | 返回值：类型 + 结构 + 值 + 别名关系 + 对象字段 | 返回语义不同 |
| R2 | 每次调用及 import 的 stdout | 可见输出不同 |
| R3 | 每次调用及 import 的 stderr | 错误输出不同 |
| R4 | 统一事件序列（stdout/stderr/文件操作） | 执行顺序或副作用顺序不同 |
| R5 | 参数原地变更、模块全局、文件快照、模块全局别名组 | 副作用不同 |
| R6 | 异常类型、args、message、`__notes__`、cause/context | 异常语义不同 |
| R7 | docstring、annotations、signature、defaults、`__dict__`、wrapper chain、`co_*`、类/模块元数据 | 契约/元数据不同 |

`semantic_case` 的两个必要条件由工具显式记录：

- `signature_binding`：`inspect.signature(...).bind(*args, **kwargs)` 是否成功；
- `body_reached`：`sys.settrace` 是否观察到目标函数/类 `__init__` 的 code object 执行。

原侧绑定失败或 body 未到达 → `INCONCLUSIVE` / `ERROR`，不得判 `EQUAL`。产物侧绑定失败或 body 未到达 → `DIFFERENT`，不得静默放过。

## 3. 状态与退出码

| 状态 | 含义 | CLI 退出码 |
|---|---|---|
| `EQUAL` | 原侧与产物侧观测齐全且所有维度一致 | 0 |
| `DIFFERENT` | 至少一个可观测维度不同（含产物 import/执行失败、产物超时） | 1 |
| `INCONCLUSIVE` | 输入无法绑定、原侧 body 未到达等，证据不足 | 2 |
| `ERROR` | 原产物缺失/无法执行、harness 失败、种子状态不一致 | 3 |

`DIFFERENT` 只是「行为不同」的证据，**不自动等于 G3 的有效杀死**；是否有效杀死、是否等价变异，留给 Task 9.2 的独立变异总体与等价证明。

## 4. 容差声明

默认只忽略位置性元数据：

- `metadata.code.co_filename`
- `metadata.code.co_firstlineno`
- `metadata.code.co_linetable`

理由：注释、空行、文件摆放会改变这些字段，但不改变语义；不忽略 docstring、signature、defaults、`co_code`、`co_consts`、`co_names`、`co_varnames` 等。

浮点容差必须由 case 显式给出：

```json
"tolerance": {"float_abs_tol": 1e-12, "float_rel_tol": 1e-9}
```

工具把实际命中的容差路径写回 `result.tolerances`；不提供「忽略整个 R1–R7 维度」的开关，避免用容差掩盖破口。

## 5. 自测证据（17/17）

`semantic_diff_selftest.py` 覆盖：

| 用例 | 断言 |
|---|---|
| `equal-int` | 同函数同参数 → `EQUAL` |
| `type-int-bool` | `1` vs `True` → `DIFFERENT`，R1 |
| `float-tolerance` | 显式 1e-12 容差 → `EQUAL`，容差路径回显 |
| `docstring-loss` | docstring 丢失 → `DIFFERENT`，R7 |
| `format-only` | 注释/空行变化 → `EQUAL`（位置字段按声明忽略） |
| `signature-default` | 默认值变化 → `DIFFERENT`，R7 |
| `exception-message` | 异常消息变化 → `DIFFERENT`，R6 |
| `side-effect` | 参数列表被改写 → `DIFFERENT`，R5 |
| `stdout-order` | 输出顺序变化 → `DIFFERENT`，R2/R4 |
| `file-effect` | 写文件内容变化 → `DIFFERENT`，R5 |
| `module-diff` | 模块全局 `1` vs `True` → `DIFFERENT`，R5 |
| `async-equal` | async 函数 → `EQUAL` |
| `class-equal` | 类构造 + 实例字段 → `EQUAL` |
| `binding-inconclusive` | 两侧参数均无法绑定 → `INCONCLUSIVE` |
| `product-import-failure` | 产物 import 抛错 → `DIFFERENT`，LOAD |
| `pyc-equal` | 原始 `.pyc` + 产物 `.py` → `EQUAL` |
| `missing-original` | 原产物缺失 → `ERROR` |

另做一次真实语料冒烟：`site-packages/fly/server_version.pyc` 与 `server_versionOK.py`，`entrypoint=module` → `EQUAL`。该冒烟只证明工具可跑真实 pyc/产物对，不证明 402 语料整体完备。

## 6. 已知边界（不得当作完备）

1. **不是 OS 级沙箱**：只隔离 cwd 与 Python 进程；不拦截网络、系统调用、cwd 之外的写文件。
2. **stdout/stderr 只覆盖 Python 层**：`os.write(1, ...)`、子进程直接写 fd 不进入事件序列。
3. **对象身份是局部证据**：同一返回值内部的别名由 `ref/oid` 捕获；返回值、输入、全局之间的跨对象身份未建立统一图。模块全局别名组只覆盖 `observe_globals` 选中的名字。
4. **装饰器顺序不是直接观测**：通过 wrapper chain、signature、docstring、执行行为间接约束，未重建源码装饰器列表。
5. **生成器/异步生成器会被消费**：`list(...)` / `async for` 会改变惰性语义；无限生成器只能靠超时判 `DIFFERENT/INCONCLUSIVE`，不能证明等价。
6. **时间/网络/外部随机源未冻结**：只固定 RNG 种子与 hash seed；涉及真实时钟、网络、UUID、PID 的用例应显式排除或加容差，否则可能误报。
7. **异常回溯位置不比较**：只比较类型、args、message、notes、cause/context；不比较 traceback 行号。
8. **模块代码元数据来自当前解释器重编译**：原始 pyc 与产物源码均按 CPython 3.11 读取；位置字段默认忽略，`co_code/co_consts` 等仍比较。
9. **全局观测有上限**：`observe_globals=["*"]` 最多比较 200 个全局；超出时工具标记 `globals_truncated` 并判 `INCONCLUSIVE`，不以截断后的子集判 `EQUAL`。

## 7. 用法

```powershell
python -X utf8 tools/completeness/semantic_diff.py --case case.json
python -X utf8 tools/completeness/semantic_diff.py --cases cases.jsonl --out results.jsonl
python -X utf8 tools/completeness/semantic_diff_selftest.py
```

最小 case：

```json
{
  "case_id": "example",
  "original": {"pyc": "site-packages/fly/server_version.pyc"},
  "product": {"source": "site-packages/fly/server_versionOK.py"},
  "entrypoint": "module",
  "observe_globals": ["*"],
  "timeout_s": 8
}
```

`entrypoint` 支持 `module`、`function:name`、`function:Class.method`、`class:Name`。

## 8. 下一步

- Task 9.2：`mutation_test.py` 独立变异总体、等价证明、漏检/误杀统计；`semantic_diff` 只作为行为判定器，不把 `DIFFERENT` 直接计为有效杀死。
- Task 9.3：升级 `jspace_generator.py` / `coverage_checker.py` 到 C1–C5 五元组。
- 在 Task 9.6 把本工具接入 E 门禁，并把 R1–R7 的 INCONCLUSIVE/ERROR 计入双读数，不得计入通过。
