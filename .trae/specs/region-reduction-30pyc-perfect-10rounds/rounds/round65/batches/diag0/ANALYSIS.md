# R65 · diag0 · ANALYSIS — 13 处 `_os_dbg*` 的来源、中性机制与热路径 I/O

配套实测数据在 `FACTS.md`。本文件只回答 BRIEF §4 问的三件事：**来自哪几轮**、**为何中性**、
**热路径里是否真的发生过文件 I/O**。

## 1. 来源：三拨考古探针，名字里带着各自的轮次

按 alias 名与开关名回溯，13 处分成**三拨**，全部是「一次性定位用的路径探针」，不是任何轮次的正式判据。

### 拨一 · Round 7 的嵌套 if 生成探针（2 处，开关 `R7_DEBUG_IFGEN`）
`_os_dbg5`（L20961）、`_os_dbg4`（L20999），都读 `R7_DEBUG_IFGEN`。
内容是在 `_nested_if` 判定链里打印「这块有没有 BoolOp 子区域 / 有没有被登记进
`_nested_if_entry_generate`」。判据本身（原则 3「嵌套即抽象节点」+ 原则 2「每块唯一归属」的中文注释）
是 Round 12-N1 之后重写过的正式逻辑，探针只是贴在同一处。
**探针里还硬编码了块偏移**：L20962 的条件是
`_os_dbg5.environ.get('R7_DEBUG_IFGEN') == '1' and b.start_offset in (192, 584)`
—— 只看两个特定偏移，是典型的「我要看这两个块走到哪儿了」的单次调试，天然不可能成为长期机制。

### 拨二 · Round 30 的第 13 号探针（1 处，开关 `R30_13_DEBUG`）
`_os_dbg_13`（L33020），打印 `value_target / merge / _si / _pre_store / first_chain`。
alias 里的 `_13` 与开关名 `R30_13_DEBUG` 同源，是 R30 排查 boolop 值栈时的第 13 号埋点。
它落在 **R64-D4-B 规则体的正中间**（标记行 L32990，见 FACTS §3），是本轮唯一有合并顺序含义的一处。

> **拨一 / 拨二 是「孤儿探针」**：全仓库 `grep -rl R7_DEBUG_IFGEN` 与 `grep -rl R30_13_DEBUG`
> 都只命中 `core/cfg/region_ast_generator.py` 自身（排除 `.git/` 对象后无任何驱动脚本或文档引用），
> 当年按开关跑探针的脚本早已不在。对照之下拨三还留着驱动脚本（见下）。
> 也就是说这 3 处连「谁还会去按这个开关」都已经断了，删除的阅读收益大于任何诊断价值。

### 拨三 · Round 23 N6 的 block@456 追踪族（10 处，开关 `R23N6_*` / `R23N6_TRACE`）
`_os_dbg`（L43773，`R23N6_DEBUG2`）、`_os_dbg_main`（L44507，`R23N6_DEBUG5`）、
`_os_dbg_lf`（L47086，`R23N6_DEBUG4`）、`_os_dbg_r23n6_trace`（L47246，`R23N6_TRACE`）、
`_os_dbg_pre`（L47294，`R23N6_DEBUG3`）、以及裸 `_os_dbg` × 5（L47331/47348/47353/47358/47366，`R23N6_DEBUG`）。

这一拨的身份有**直接文件证据**：仓库里留着当年的驱动脚本
`.trae/specs/quotation-pyc-iteration/rounds/round_23/test_engineer/trace_block_456_v2.py`，
它的第一行 docstring 是「R23-N6: 追踪 block@456 在 `_generate_block_statements` 中的处理路径」，
并且逐一 `os.environ['R23N6_DEBUG']='1'` … `os.environ['R23N6_DEBUG5']='1'`
—— 恰好就是本文件里这 5 个开关名。round_39 的 `wt_head/` 镜像里还有同一份脚本的副本。

同一拨留下的**其它**命名清楚地显示当时把 block@456（`fly/data/quotation.pyc`）的整条
`_generate_block_statements` 路径切成了 6 个观测点，编号 DEBUG / DEBUG2…DEBUG5 / TRACE：
| 观测点 | 打印的前缀 | 它在问什么 |
|---|---|---|
| L43773 `R23N6_DEBUG2` | ` _generate_block_statements block@…` | 进没进主函数 |
| L44507 `R23N6_DEBUG5` | `reached main stmts processing` | 走没走到主语句处理 |
| L47086 `R23N6_DEBUG4` | `reached leftover stmt_instrs` | 走没走到剩余指令分支 |
| L47246 `R23N6_TRACE` | `reached post-stmt_instrs` | 走没走到语句后段 |
| L47294 `R23N6_DEBUG3` | ` pre-fix block@…` | 走没走到 return 提升前 |
| L47331…47366 `R23N6_DEBUG` | `chain=` / `NO chain` / `last_stmt is not Expr` / `SKIPPED` / `EMPTY stmts` | 该分支到底走了哪一条 |

配套注释也直接暴露身份：L47245 写的是 `# 追踪 block@456 是否到达此处`（**只为该探针而写**，故本 spec 一并删），
而 `_has_bt2 / _has_bt2_main / _has_bt2_lf / _has_bt2_trace / _has_bt2_pre` 这 5 个变量全是同一句
`any(i.opname == 'BUILD_TUPLE' and i.arg == 2 …)` —— 当年是为了盯 `return (re_error, re_data)` 这种
BUILD_TUPLE 2 形态才加的二次门控，变量名互不相同正是因为写在同一个函数里怕撞名。

**注意：探针留下了，判据也留下了。** `_apply_r23n6_return_promotion`（L47376 起）、
`_r23n6_in_except_context`、`_block_ends_with_pop_top_r23n6`、`_non_noise_r23n6` 都是 R23-N6
的正式产物提升判据，本 spec 一行没动。

## 2. 为何行为中性：三层理由，从弱到强

1. **形态上**：每个 alias 全生命周期只被读一次，且一定是
   `if <alias>.environ.get('ENV')`（FACTS §1 逐 token 核对）。`os.environ.get` 是无副作用的字典读。
   gated 体 59 行里出现过的被调用者只有 `any / get / getattr / isinstance / len / print / sorted / str / type`。
2. **运行时**：门禁与 harness（`h62.py`、`cstrict.py`、仓库 `scripts/*`）都不设这 8 个开关，
   唯一设它们的是上面那份 round-23 考古脚本。⇒ 开关恒为 None ⇒ 13 个 gated 体一次都不执行。
3. **即使开关打开也不影响产物**（比 1、2 更强，见 FACTS §7）：
   把 8 个开关全设成 `1` 跑 landed 臂，`quotation` 等 4 支金丝雀产生了 **616 行**调试 stderr、
   电池产生 **175 行**，证明这些块**真的在热路径上被执行**；但两臂产物仍 `SAME=19 / SAME=4`、
   `MOVED=0`、`ERR=0`，0 个 NameError。理由很直白：13 个 `print` 一律带 `file=_sys_dbg*.stderr`，
   写的是**流**不是**文件**，而生成的 13 个局部变量只喂给自己所在 gated 体的 `if` / `print`。

### 关于「删掉会不会让某条代码路径变空」
9 处（#1–#9）所在块另有正式语句，删完仍非空。4 处（#10–#13，原 L47347–47371）的**子句唯一内容就是调试代码**，
所以必须连 `else:` / `elif stmts:` 子句头一起删；留头删体就是 SyntaxError。
删整条子句与「空体子句」语义等价：`else: pass ≡ 无 else`，`elif cond: pass ≡ 该臂不存在`
（该臂为真时原本什么都不做，控制流一样落到 L47373 `self.generated_blocks.add(block)`）。
`py_compile OK` + 402/电池/canary 全同，是这两条等价性的实测背书。

### 关于 try/except
13 处**没有一个位于 `try:` 体内**（按缩进回溯包围块链逐一核对，FACTS §1）。
所以不存在「原来靠 except 吞掉调试异常、删掉后走了不同恢复路径」这种隐藏改变。

## 3. 热路径里到底有没有文件 I/O —— **没有，一次都没有**

这是本轮最要紧的负面结论，三条独立证据：

1. **静态**：`_os_dbg*` 与 `.open(` / `path.join` / `.write(` 同行出现次数 = **0**。
   13 个 gated 体共 59 行，按危险名（`open` `write` `path.join` `makedirs` `mkdir` `rename` `remove` `shutil` `flush`）
   全文扫描 = **0 命中**；13 个 `print` 全部显式 `file=<stderr>`。
   ⇒ BRIEF §1 担心的「3 MB 生成器里的隐藏文件 I/O」**在本文件里其实不存在**；真正的开销只是
   `os.environ` 查找 + 若干次 `import os` / `import sys`（都是 sys.modules 命中）和一堆
   `any(... for i in block.instructions)` 的 CPU —— 而后者在开关关闭时根本不执行。
2. **运行时**：`--arm=landed` 跑完 402 支后，`build_landed/` 里只有 402 个 `.py` 产物（+ 1 个 `__pycache__` 目录），
   **没有多出任何由生成器写出的调试文件**；候选臂同样。
3. **对照**：把 8 个开关全部设成 1，产物 sha 一个都没变（FACTS §7），进一步排除
   「曾经有人开着开关跑过、把某个调试副作用固化进了产物」这种可能。

⇒ 清理的实际收益是**阅读噪声 + 每个 block 若干次 `environ.get`/`import` 的开销**，
而不是 BRIEF 假设的「隐藏文件 I/O」。提速幅度应当按这个口径预期，别当成 I/O 优化。

## 4. 影响面与风险评级


* 删 78 行（13 处 import + 59 行 gated 体 + 1 行专属注释 + 4 个子句头 + 1 个多余空行 + 6 个 `import sys`）。
* 纯删除，无一行新增代码；不改任何判据、不改任何控制流走向（除把 4 个空子句折叠掉）。
* 与 R64 唯一的空间冲突是 site 3 落在 R64-D4-B 规则体内；其余 12 处彼此相距甚远、且与其它 5 个并行代理
  诊断的 partial 无文本重叠区（它们改的是识别条件/发射路径，本轮删的是 print）。
* 13 个 anchor 各自独立且只含本站点文本，方便主代理与别的 spec 拼接；相邻的 #10–#13 已刻意拆成 4 个小 anchor
  而不是整块删除。
* 综合评级：**低风险**，且是唯一一个「删完 402 支 MOVED=0」有双重口径（sha16 + 全文件 sha256）背书的批次。

## 5. 后续建议（不在本批次内）

1. **同款残留还有 5 处**：`_os`（L696/L768，`R23N21_DEBUG`）、`_os_ebm`（L12327，`EBM_DEBUG`）、
   `_os_w16g`（L44645）、`_os_w16`（L44681，`R16_DEBUG`）。形态与本轮 13 处一致（`if <alias>.environ.get(...)` 门控 + 只 print），
   可复用本轮的「逐 token 普查 + gated 体审计 + 开关全开对照」流程再清一遍。
   口径自校验：文件内 `import os as _*` 共 18 处 = 13（本 spec）+ 5（上述）；`environ.get` 共 18 处，
   候选字节剩 5 处，正好吻合。
2. 若想要可开关的诊断，建议改成模块级一个 `_DBG = os.environ.get(...)` 常量 + 统一 logger，
   而不是在每个热块里 `import os as _os_dbgN` —— 后者会让下一个读者误以为这些是判据的一部分。
3. 工作区交付的 `targets.txt` 双前缀损坏（FACTS §8）值得单独修一次，否则后续轮次任何用它的 402 A/B
   都是「两臂同样报错 → SAME=402」的假绿。
