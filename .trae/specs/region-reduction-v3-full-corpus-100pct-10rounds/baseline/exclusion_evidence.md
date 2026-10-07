# 排除类字节级证据（反向夹钳配套，封表时点 2026-10-05）

来源：`tools/corpus_census.py` 名单 + 对 `site-packages/**/*.pyc` 逐文件头/marshal 探测（1722 个全量，非抽样）。
判据口径：cpython-3.11 pyc magic = `a70d0d0a`；`co_filename` 取 `marshal.loads(raw[16:])`。

## 普查读数

```
total=1722 A=402 B=1312 C=8 A_delta=0
index_entries=402 products_ok=402/402 missing_pyc=0
```

- **A_delta=0**：A 类集合与 `pyc_index.json` 402 条 1:1 相等（对称差为空），验证面钉死在 402。
- 与 r00 封表读数 `total=1721 / C=7` 相比 **+1 C 类**（下表 C-8），A 类零位移。

## B 类（1312，派生畸形 pyc）—— 逐类判据实测

| 证据形态 | 数量 | 判据 |
|----------|------|------|
| `a70d0d0a` + `co_filename` 以 `OK.py` 结尾 | **1310** | 由反编译产物 `*OK.py` 再编译而来（三层嵌套 `__pycache__` 者 co_filename 指向上层 `*OK.cpython-311OK.py`） |
| magic `f30d0d0a`（cpython-**3.13**） | **2** | 文件名即 `__init__OK.cpython-313.pyc`，源名段为 `__init__OK`；3.11 无法 marshal 3.13 码对象，故以文件名 + magic 登记 |

两个 3.13 例外逐条：

```
IQCommon/api/__pycache__/__init__OK.cpython-313.pyc   magic=f30d0d0a size=170
IQCommon/data/__pycache__/__init__OK.cpython-313.pyc  magic=f30d0d0a size=171
```

结论：B 类 1312 个全部是「`*OK.py` 的再编译」，无一个是待反编译的原始第三方字节码。
抽样三条（co_filename 原文，可复核）：

```
IQCommon/__pycache__/__init__OK.cpython-311.pyc
  co_filename = F:/Downloads/pythoncdc-main/site-packages/IQCommon/__init__OK.py
IQCommon/__pycache__/__pycache__/__init__OK.cpython-311OK.cpython-311.pyc
  co_filename = F:/Downloads/pythoncdc-main/site-packages/IQCommon/__pycache__/__init__OK.cpython-311OK.py
IQCommon/__pycache__/__pycache__/__pycache__/__init__OK.cpython-311OK.cpython-311OK.cpython-311.pyc
  co_filename = F:/Downloads/pythoncdc-main/site-packages/IQCommon/__pycache__/__pycache__/__init__OK.cpython-311OK.cpython-311OK.py
```

## C 类（8，会话自造 scratch）

C-1 ~ C-7（r00 已登记）：均为合法 3.11 字节码，但 `co_filename` 指向 `*OK.py` / `*OK_marker_test.py`，
即把反编译产物当源码再编译的探针残骸，不是原始语料：

```
IQCommon/api/klinedataOK.pyc                          co_filename=site-packages/IQCommon/api/klinedataOK.py
IQCommon/api/klinedataOK_check.pyc                    co_filename=.../IQCommon/api/klinedataOK.py
IQEngine/plugins/plugin_system_risk_calculation/__init__OK.py.tmp.pyc
                                                      co_filename=site-packages/.../__init__OK.py
fly/common/market_time_probe_recompile.pyc            co_filename=.../fly/common/market_timeOK.py
fly/data/_tmp_difffn.pyc                              co_filename=.../fly/data/quoteOK.py
fly/dumpload/_load_algo_recomp.pyc                    co_filename=site-packages/fly/dumpload/load_algoOK.py
fly/simtradding/ptradeAccountOK_marker_test.pyc       co_filename=.../fly/simtradding/ptradeAccountOK_marker_test.py
```

C-8（本基线时刻新增，登记为类别而非静默进入 batch）：

```
IQCommon/util/email_utils.py.pyc   size=3866
前 80 字节（ASCII）：
  # Source Generated with Decompyle++ (Python version)
  # File: email_utils.pyc (Python 3.11)
  import os
  import smtplib ...
magic = 2320536f（≠ a70d0d0a）；marshal 失败（unknown type code）
```

判定：**不是字节码文件**，是旧工具 Decompyle++ 生成的 Python 源码文本被误命名为 `.pyc`；
同目录已有真实语料 `email_utils.pyc` 与其产物 `email_utilsOK.py`，故本文件不可能进入 A 类，
按 C 类排除。它的出现使 `total` 从 1721 变 1722，A 类读数不受影响（A_delta=0）。

## 夹钳断言（每轮重跑）

1. `total = A + B + C` 且无第四类（脚本以命名规则 + 索引成员判定，实测 1722 = 402 + 1312 + 8）。
2. `A_delta = 0` 且 `products_ok = 402/402`、`missing_pyc = 0`。
3. 任一轮若出现名单外 pyc，脚本必须先登记类别，禁止静默进入 batch。

## 2026-10-07 复演（Round 9 主代理，逐字节取证，非引用上表）

在本工作树 `site-packages/` 下重跑，脚本只做 stdlib（marshal+os）：

1. **A 类完备性**：`A_roster` 402 条**全部在盘**（missing=0），且**全部有同目录兄弟产物**
   `X.pyc → XOK.py`（无产物者 0）⇒ 用户要求的「同目录下同名 +OK 的 py 文件」在 A 类上是完备的。
2. **B 类派生性的字节级证明**：1312 个 B 类 pyc **逐个** `marshal.loads` 后读 module code object 的
   `co_filename`，结果 **1312/1312 以 `OK.py` 结尾，反例 0**，不可读 0。
   即每一个 B 类文件的源都是我们自己发射的 `*OK.py`（不是 site-packages 的真实模块），
   排除口径成立；去重后涉及 841 个不同的 `*OK.py` 文件名（同一产物被反复编译进
   嵌套 `__pycache__/__pycache__/` 是 B 类膨胀到 1312 的原因）。
3. **C 类**：7 条全部在盘（`klinedataOK.pyc`、`klinedataOK_check.pyc`、
   `__init__OK.py.tmp.pyc`、`market_time_probe_recompile.pyc` 等自造探针/临时件）。
   本轮我删除了上节登记的 C 类第 8 件 `IQCommon/util/email_utils.pyOK.py`
   （0 字节，未入 git、非产物、非语料），删除属清理自造垃圾，不改 A 类口径（A_delta=0）。
4. **台账缺陷登记（未修）**：`corpus_census.json` 的 `corpus_root` 与 `index_files` 仍写着
   **另一个工作树** `…/worktrees/app/6f79dd/pythoncdc-main/…`，而 `*_roster` 是相对文件名，
   因此本轮按本树磁盘复核仍然有效；但**以该 JSON 的 root 字段去解析路径会指到陈旧树**。
   后续任何脚本一律以 `*_roster`（相对）+ 当前树 root 组合，禁止直接取 `corpus_root`。

结论：A=402 的语料边界经字节级反证后仍然成立，"100% 成功"的分母就是 402 文件 / 6617 单元，
不存在被误排除的真实模块。

### 盘上 `*.pyc` 计数与夹钳的差一件（实测，非推测）

按扩展名穷举 `site-packages/**/*.pyc`：**1722** 件，而 `A∪B∪C` 名册为 **1721** 件，
差 **1** 件且无重复、无幽灵（`A&B=A&C=B&C=0`，名册中不在盘的 0 件）：

    IQCommon/util/email_utils.py.pyc   3866 字节   ← 不在任何名册

取证：该文件 `marshal.loads` 直接 `ValueError: bad marshal data`，首 16 字节为
`b'# Source Generat'`（行首 `# Source Generated with Decompyle++ (Python version)`），
且与同目录 `email_utils OK.py`（带空格名、3866 字节、git 自 Round 1 前即跟踪）**逐字节相同**。
⇒ 它是**反编译器的源码输出被存成了 `.pyc` 名**，不是字节码，不可能被反编译，
故不属于 A 类；普查脚本的枚举以「合法 pyc 头」为条件，因此它从一开始就未进入 `total=1721`。

**结论与口径修正**：语料边界仍成立（A=402 全部有产物、B=1312 全部派生自 `*OK.py`、零反例），
但"100% 的分母"必须这样表述才不错：
`1722 = 402(A) + 1312(B) + 7(C) + 1(非字节码的伪 pyc)`；
后续夹钳断言应改为「扩展名计数 − 伪 pyc 数 = A+B+C」，并把该伪 pyc 作为 C 类第 8 件登记在册
（它是产物文本，不是语料模块，保留原位不删——git 已跟踪，删除属改动他人入库物）。
