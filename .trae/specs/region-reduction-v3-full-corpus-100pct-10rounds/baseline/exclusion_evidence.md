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
