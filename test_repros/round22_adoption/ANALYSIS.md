# Round 22 —— realtime_event_source −197：区域树「整块集合批量标 generated」与父臂收养缺口

诊断轮（Round 22 test engineer）。**本轮不修改 `core/`**，不改任何 `*OK.py`，不跑
`scripts/pyc_batch_verify.py` / `_r13_gate.py`，不写 `pyc_index.json`，无任何 git 写操作。
仓库内唯一写入目录：`test_repros/round22_adoption/`；其余全部产物在 `D:/Temp/r22diag/`。

---

## 1. 环境与纪律

| 项 | 值 |
| --- | --- |
| 解释器 | `D:/Python/python.exe`（CPython 3.11.9），每条命令前置 `PYTHONIOENCODING=utf-8` |
| 单条命令上限 | 300 s（实际全部 <280 s；长任务分片 + `next=` 续跑） |
| HEAD 镜像 | `D:/Temp/r22diag/mirr/head` = `46e752abd16ebb306495b627c106ef645951fa80`（含 R21-A） |
| 基线镜像 | `D:/Temp/r22diag/mirr/pre21` = `15a8de06e3af49e649795c49577acff319e1c47e`（R21-A 之前） |
| 镜像构造 | `git archive <rev> core bytecode pycdc.py _r10_strict_check.py \| tar -x -C <dir>` + 只读 `pyc_index.json` 副本（`probes/r22_mk.py base <name> --rev <r>`） |
| 候选镜像 | `probes/r22_mk.py patch <dir> <specfile>`：字节级表驱动补丁、锚点唯一性断言（`count(old)!=1` 立即 SystemExit）、CRLF 保持、`compile()` 语法自检 |
| 尺子 | 唯一 `_r10_strict_check.strict_compare`（NOISE={NOP,CACHE,PRECALL,EXTENDED_ARG}，非跳转指令逐位同、跳转按方向归一 + 无条件跳转 stub 尾随）；逐函数打印 `[seq_len] orig=N decomp=M` |
| 工作树 | `F:/Downloads/pythoncdc-main/core/` 全程只读（探针一律 `sys.path.insert(0, <mirror>)` 后 `import pycdc`，运行时 monkeypatch，绝不写盘） |

继承的上一手产物（**未重跑**，直接引用）：

* `D:/Temp/r22diag/mirr/{head,pre21}`、`logs/run_{head,pre21}.txt`、`logs/pipe_{head,pre21}.txt`、
  `dump/{pre21,head}_re.txt`（21931 B / 19109 B）
* 编排方独立复核：`D:/Temp/r21_orch/HANDOFF_r21a_overfire.md`、`D:/Temp/r21watch/`
* 全量 A/B 记录（402 文件 × 两世界）：`D:/Temp/r21fix/ab/r21base_decomp/`、`r21head_decomp/`

本轮新增探针（全部在 `D:/Temp/r22diag/probes/`）：
`r22_wrap.py`（构造点出入参 + 调用栈）、`r22_hier.py`（`_build_region_hierarchy` 逐行）、
`r22_scan.py`（不变量全库扫描）、`r22_gdbg.py`/`r22_gdbg2.py`（生成器调用树 + `generated_blocks` 增量）、
`r22_ptrace.py`/`r22_ptrace2.py`（`sys.settrace` 按 `region.entry.start_offset` 开闸的逐行/关键行判决）、
`sp_c1.py`/`sp_c2.py`/`sp_dbg_gen.py`（候选镜像补丁规格）。
所有 settrace/monkeypatch 观测都做了**非扰动校验**：观测脚本同时落盘产物，
`md5(logs/ptrace_head.txt.product.txt) == md5(dump/head_re.txt)`（19109 B 全等），
`md5(logs/g2_head.txt.product.txt)` 同理 —— 观测不改变结论。

---

## 2. 症状：两个世界的尺子读数

`logs/run_pre21.txt` 与 `logs/run_head.txt`（12 个函数，两世界都是 `strict: 10/12`）：

| 函数 | pre21（基线） | HEAD（R21-A 之后） | 备注 |
| --- | --- | --- | --- |
| `RealtimeEventSource.clock_worker` | `orig=1276 decomp=1251`（**−25**） | `orig=1276 decomp=1079`（**−197**） | 本轮唯一目标 |
| `RealtimeEventSource.get_one_event` | `orig=19 decomp=20`（**+1**） | `orig=19 decomp=20`（**+1**） | 两世界完全一致，见 §8 |
| 其余 10 个函数 | ok | ok | — |

R21-A 在本文件的**唯一**守卫命中点是 `cur=7270`（编排方 `HANDOFF_r21a_overfire.md` §3 独立复核：
17 次守卫求值中仅 1 次 `break`）。产物体积 `21381 → 18560` 字符（−2821），
逐函数指令数 `1251 → 1079`（−172）。

`n_ok` 读数 10/12 → 10/12 **完全中性** —— 与 R21 的教训一致：只看 `n_ok` 会把 −25→−197
读成"没变差"。本轮所有候选一律同时报 `n_ok` 与 `Σ|orig−decomp|`。

全量侧（引用 `D:/Temp/r21fix/logs/ab_blind.txt`，402 文件，两世界各 402 条记录）：

```
WORSE  IQEngine/.../realtime_event_source.pyc  n_ok 10->10  sum|delta| 26 -> 198
BETTER IQEnviro/.../fly/oauthenticator/oauth2.pyc  n_ok 10->12  sum|delta| 18 -> 0
TOTAL  worse=1  better=1
```

---

## 3. 指令级判决：7248/7270 处真实源码形状

`clock_worker` 中相关字节码（`D:/Temp/r22diag/logs/dis_7372_7520.txt` + `pipe_head.txt` 块表）：

```
7248  LOAD_DEREF self / LOAD_ATTR first_run_date / COMPARE_OP !=
      POP_JUMP_FORWARD_IF_FALSE -> 7492        # if now_date != self.first_run_date:
7270  LOAD_GLOBAL system_log / LOAD_ATTR debug / LOAD_CONST '获取重登信号量'
      PRECALL / CALL / POP_TOP                  # ← 值丢弃语句，不是条件操作数
      LOAD_DEREF login_semaphore / LOAD_METHOD acquire / LOAD_CONST timeout=…
      CALL / POP_JUMP_FORWARD_IF_FALSE -> 7492  # if login_semaphore.acquire(...) is False:
7372  system_log.error('获取重登信号量超时，系统退出'); self.event_queue.put((dt, EventEnum.SYSTEM_EXIT))
7488  LOAD_CONST None / RETURN_VALUE            # return None
7492  ← 汇合点（merge）
7582  LOAD_DEREF self / LOAD_ATTR before_trading_date / COMPARE_OP >
      POP_JUMP_FORWARD_IF_FALSE -> …            # elif now_date > self.before_trading_date:
```

判决性事实：`7270` 块**开头**是一条 `CALL → POP_TOP` 的值丢弃语句，随后才是第二个条件。
所以「把 7248 与 7270 折成 `A and B`」在字节码层面不成立 —— 这正是 R21-A site A
要截断的东西，也是 HEAD 与 pre21 的唯一分歧来源。

区域树差异（`logs/re_diff_pre21_head.txt`，`pipe_pre21.txt` vs `pipe_head.txt`）：

```
pre21:  BoolOpRegion entry=7248  blocks=[7248, 7270]      ← 假区域，吞掉 7270 的 4 行
        IfRegion@7248 children=[BoolOpRegion@7248]         ← 17396 add_child 收养
HEAD :  （无 BoolOpRegion@7248）
        IfRegion@7248 then_blocks=[7270, 7372, 7488] children=[]
        IfRegion@7270 then_blocks=[7372, 7488]      children=[]
```

两世界**相同**的部分（重要，见 §7 C.2）：

```
IfRegion@7164  merge=7216  then_blocks=[7186,7202,7214,7212,7248,7270,7492,7372,7582,7488,
                                        7604,7634,7620,7632,7668,8592,7630,7706,...]  (51 blocks)
IfRegion@7186  merge=7248  then_blocks=[7212,7216,7582,7604,7634,7620,7632,7668,8592,7630,
                                        7706,8666,8904,...]                            (45 blocks)
IfRegion@7216  merge=7582  then_blocks=[7248,7270,7492,7372,7488]  blocks=[7488,7216,7248,7270,7372,7492]
IfRegion@7248  merge=7492  then_blocks=[7270,7372,7488]            blocks=[7248,7270,7372,7488]
IfRegion@7270  merge=7492  then_blocks=[7372,7488]                 blocks=[7270,7372,7488]
IfRegion@7582  merge=7634  nblocks=28
```

即：`@7186` 的臂里既列了子区域入口 `7216`，又列了 `@7216` 的**内部块** `7248/7270/7372/7488/7492`，
还列了本该属于**兄弟**链的 `7582/7604/7634/…`（`@7186.merge=7248` 但 7248 之后一路到循环尾都被
`_collect_branch_blocks` 收进来了）。这一形状在两世界都存在。

---

## 4. 真源码形状重建（由区域数据 + 逐块 dis 反推，非读代码）

```python
while True:                                              # LoopRegion@5598 / @5614
    ...
    if now_date > self.pre_before_trading_date:          # @7164  merge=7216
        if pre_before_trading <= now_time < pm_close or now_time >= pm_open:   # @7216(条件块 7186/7202/7212/7214)
            if now_date != self.first_run_date:          # @7248  merge=7492
                system_log.debug('获取重登信号量')
                if login_semaphore.acquire(timeout=...) is False:   # @7270 merge=7492
                    system_log.error('获取重登信号量超时，系统退出')   # @7372
                    self.event_queue.put((dt, EventEnum.SYSTEM_EXIT))
                    return None                                     # @7488
                ...                                                 # 7492 merge
        elif now_date > self.before_trading_date:        # @7582 merge=7634   ← 被丢失的臂
            ...                                                     # @7604/@7634/@7706/… 共 42 块
```

（`@7186` 与 `@7216` 是同一条 `or` 条件的"表达式子区域 / 结构区域"双身份对，
与 R16-A、R15-H1+H2 处理的族系一致：`@7186.blocks` 含 `7216`，`@7216.blocks` 含 `7248…7488`。）
