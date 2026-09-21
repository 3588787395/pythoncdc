# Round 21 诊断 —— `site-packages/fly/oauthenticator/oauth2.pyc`：两个 `post` 各 **−9**

角色：Round 21 TEST/DIAGNOSIS。**只诊断，不改 `core/`**。所有测量都在仓库外镜像核上做。

## 0. 环境与纪律（复现必需）

| 项 | 值 |
|---|---|
| 解释器 | `D:/Python/python.exe` = CPython 3.11.9，一律 `PYTHONIOENCODING=utf-8` |
| 基线镜像 | `git archive 5c63ce6b core bytecode pycdc.py _r10_strict_check.py \| tar -x -C D:/Temp/r21d/mirr/base`（+ 仓库 `pyc_index.json` 的**只读副本**） |
| R20-A 落地后镜像 | `git archive 15a8de06 …` → `D:/Temp/r21d/mirrhead/base` |
| 候选镜像 | 基线树 + 运行时补丁（脚本 `D:/Temp/r21d/probes/r21_mk.py`，`EDITS` 表驱动，锚点唯一性 assert） |
| 目标快照 | `D:/Temp/r21d/target/oauth2.pyc`（md5 `e377c38171ea5c7bcc5fa31fcbe94a86`）+ 当前产物 `oauth2OK.py`（md5 `b3e07cb1ef20c3db5db6ca124cda1992`）的**冻结副本** |
| 尺子 | 只用 `_r10_strict_check.strict_compare`（NOISE={NOP,CACHE,PRECALL,EXTENDED_ARG}；非跳转指令逐位同；跳转按方向归一 + 无条件跳转 stub 尾随） |
| 禁止 | 全程未读写工作树 `core/`；未生成/改写任何 `*OK.py`；未跑 `scripts/pyc_batch_verify.py`、`_r13_gate.py`；未写 `pyc_index.json`；无 git 写操作 |
| 仓库内唯一写入 | `F:/Downloads/pythoncdc-main/test_repros/round21_oauth2/`（16 个复现 + `run_all.py` + 本文件） |

探针（都在 `D:/Temp/r21d/probes/`，日志在 `D:/Temp/r21d/logs/`）：
`r21_run.py`（反编译+重编译+逐函数尺子）、`r21_seq.py`（过滤后逐指令序列 + opcode/argrepr 多重集差）、
`r21_pipe.py`（CFG 块 / 区域树 / AST / 产物）、`r21_trace.py`（`sys.settrace` 按 `start_block.start_offset` 出手）、
`r21_cond.py`（运行时 monkeypatch 打条件区域站点）、`r21_twins.py`、`r21_diff.py`（`_r10_difflen.py` 隔离副本）、
`r21_mk.py`、`r21_ab.py`/`r21_par.py`/`r21_sum.py`（全量 A/B）。

## 1. 起点症状

* 官方批量：11 函数 / 10 匹配 = `partial`。
* 严格尺子：`DEFECT 10/12`，两条缺陷：

```
DEFECT <module>.HSIDOAuthCallbackHandler.post   [seq_len] orig=175 decomp=166
DEFECT <module>.OAuthCallbackHandler.post       [seq_len] orig=190 decomp=181
```

同形孪生，各差 **9 条**。

## 2. 指令级判决：**ABSENT（整块消失），不是 relocated**

`_r10_difflen.py`（副本 `D:/Temp/r21d/diffs/`）与 `r21_seq.py` 一致给出单一删除窗口：

```
--- delete orig[116:125] decomp[116:116] ---
O116 LOAD_CONST None              (块 730 的 return)
O117 RETURN_VALUE
O118 LOAD_FAST self               ┐
O119 LOAD_METHOD spawn_single_user│
O120 LOAD_FAST user               │ 块 734 的 `yield self.spawn_single_user(user)`
O121 CALL                         │ （7 条，含 3.11 协程弹栈记账 YIELD_VALUE/RESUME/POP_TOP）
O122 YIELD_VALUE                  │
O123 RESUME                       │
O124 POP_TOP                      ┘
```

opcodes 多重集差量（`logs/seq_oauth_post.txt`）：
`CALL -1, LOAD_CONST -1, LOAD_FAST -2, LOAD_METHOD -1, POP_TOP -1, RESUME -1, RETURN_VALUE -1, YIELD_VALUE -1`
（合计 −9），且 `argrepr` 计数 `spawn_single_user orig=2 decomp=1`。
非跳转指令在窗口前后逐位对齐 ⇒ **没有任何一块被搬到别处**（搬迁会表现为 delete+insert 成对出现，
这里只有 delete）。HSID 孪生同形（orig 块号 646-690/726/… 位移一致）。

⇒ 已知陷阱里的「POP_TOP/PUSH_NULL 记账 or `__exit__` 清理尾巴」假设**排除**：
丢的是完整语句 + 一个 `return`，不是记账噪声。

## 3. 真源码形状重建（两孪生 534-838 / 446-… 段）

```
534 LOAD_FAST user / LOAD_ATTR spawner / POP_JUMP_IF_FALSE -> 734     # if user.spawner:
548 LOAD_FAST user / LOAD_ATTR spawn_pending / POP_JUMP_IF_FALSE -> 566
562 LOAD_CONST None / RETURN_VALUE                                    #     return
566 status = yield user.spawner.poll() ; 620 LOAD_FAST status
    / POP_JUMP_IF_NONE -> 726                                         #   if status is not None:
624 yield self.spawn_single_user(user)  ← **前缀是协程语句**
    / 670 LOAD_GLOBAL cgroupmode / '1' / COMPARE_OP
    / POP_JUMP_IF_FALSE -> 730                                        #     if cgroupmode == '1':
692 set_cgroup_config(user_id) / RETURN ...                           #         set_cgroup_config; return
726 LOAD_CONST None / RETURN_VALUE                                    #     return   (566 的 false 落点/merge)
730 LOAD_CONST None / RETURN_VALUE                                    #     (624 内层 if 的 else 臂)
734 yield self.spawn_single_user(user)  ← **同样的协程语句前缀**
    / LOAD_GLOBAL cgroupmode / '1' / COMPARE_OP / POP_JUMP_IF_FALSE -> 836
802 set_cgroup_config(user_id) / LOAD_CONST None / RETURN_VALUE
836 LOAD_CONST None / RETURN_VALUE
```

关键结构事实：**块 624 与块 734 完全同形** —— 「`yield f()` 语句前缀 + 以条件跳转结尾」。
一条在 then 臂，一条在 else 臂。按"同层同结构必须同结论"，两者必须得到同一判定；
基线核把 624 判成 BoolOp 操作数、把 734 判成纯 elif 条件块，两处都错，且错在
**同一族判据的两个不同缺半**上（见 §4/§5）。

## 4. 根因 A —— `_detect_boolop_conditional_chain` 非首成员块守卫缺半（settrace 实测）

`core/cfg/region_analyzer.py`（5c63ce6b 行号；HEAD 15a8de06 行号 = +43）：

```
24186-24200 (HEAD 24229-24243)
            if chain:
                _has_store = any(
                    i.opname in ('STORE_FAST', 'STORE_NAME', 'STORE_GLOBAL',
                                 'STORE_DEREF', 'STORE_SUBSCR', 'STORE_ATTR')
                    for i in current.instructions
                )
                if _has_store:
                    break
```

`sys.settrace`（`r21_trace.py --off 566`，日志 `logs/tr566.txt`）实锤执行路径：

```
tr566.txt:138,140   24194| _has_store = any(            # 对 current=块624 求值
tr566.txt:141       24199| if _has_store:               # -> False（块 624 无 STORE_*）
tr566.txt:103,162   24401| chain.append((current, op_type))   # 624 被收进链，op='and'
tr566.txt:239-240   25099| return chain  -> [(566,'or'), (624,'and')]
```

返回的链 → `BoolOpRegion(entry=566, merge=730, op_chain=[(566,'and'),(624,'and')])`
→ 产物 `if status is not None and cgroupmode == '1':`（当前产物 `oauth2OK.py` 第 68/111 行），
嵌套 if 的 else 臂（块 730 的 `return`）与 `if status is not None:` 的归属一起被吞 → **−2**，
同时把块 624 的语句前缀提到外层。

**为什么这是"缺半"而不是"需要新判据"**：同一函数对**起始块**早已写了完整判据
`_sb_has_body`（24013-24035，HEAD 24056-24078）：先查 `STORE_*/BINARY_OP/DELETE_*`，
再补「`CALL` 紧跟 `POP_TOP` ⇒ 块内含表达式语句」。非首成员块只抄了前一半。
CPython 3.11 里合法的 `and`/`or` 操作数块**不会**中途弹栈（值要交给下一操作数或 merge 块消费），
只有语句（`f()` / `yield f()`）才 `CALL … POP_TOP`；协程语句在两者之间多插
`YIELD_VALUE`（`RESUME` 已在过滤表里）。

辅助证据（非缺陷点，但解释了为什么起始块 566 能通过）：
`NONE_CHECK_OPS` 豁免段 23921-23948 与 `_cond_start_offset` 栈深回溯把块 566 的
`STORE_FAST status` 划到条件起点之前 ⇒ `_sb_has_body(566)=False`。这一半是对的
（`status = yield poll()` 确实是"条件块的前缀语句"，A 族不需要动它）。

## 5. 根因 B —— `_check_elif_chain` 的 `_has_body_stmt` 已有判据，但过滤表漏 `YIELD_VALUE`

`core/cfg/region_analyzer.py` `_build_elif_region`（def 17831/HEAD 17874，call site 17328/HEAD 17371）
内嵌 `_check_elif_chain`：

```
18216-18243 (HEAD 18259-18286)
            _fe_last = first_else.get_last_instruction()
            if _fe_last and _fe_last.opname in FORWARD_CONDITIONAL_JUMP_OPS:
                _has_body_stmt = any(i.opname in ('STORE_FAST', ..., 'DELETE_SUBSCR')
                                     for i in first_else.instructions
                                     if i.offset < _fe_last.offset)
                if not _has_body_stmt:
                    _fe_instrs_before_jump = [
                        i for i in first_else.instructions
                        if i.offset < _fe_last.offset
                        and i.opname not in NOISE_OPS
                        and i.opname not in ('RESUME', 'NOP', 'CACHE', 'EXTENDED_ARG')  # ← 没有 YIELD_VALUE
                    ]
                    for _idx, _i in enumerate(_fe_instrs_before_jump):
                        if _i.opname == 'CALL' and _idx + 1 < len(_fe_instrs_before_jump):
                            if _fe_instrs_before_jump[_idx + 1].opname == 'POP_TOP':
                                _has_body_stmt = True
                                break
                if _has_body_stmt:
                    return None
```

该判据的**设计意图**（函数 docstring 18206-18215 原文："扩展 body 语句检测：函数调用语句
（CALL + POP_TOP）也应被识别为 body 语句 … 否则 IF_ELIF_CHAIN 会错误吸收 try 体和 post-try 代码"）
与块 734 的情形逐字相同，只是 3.11 协程语句在 `CALL` 与 `POP_TOP` 之间多一条 `YIELD_VALUE`，
`_has_body_stmt` 保持 False ⇒ `first_else=734` 被当成 elif 条件块。

`r21_cond.py`（monkeypatch 记录调用/返回值，`logs/cond_c1.txt`）实测：
`_build_basic_if_region(args=[734,802,836]) → IfRegion` 先建出来了，随后
`_build_elif_region(args=[210,548,562,566,624,692,726,730,734,802,836]) → IfRegion`
把 734 吸进 `IfRegion@210` 的 elif 链 ⇒ `IfRegion@210.else_blocks` 退化成扁平 `[734,802,836]`，
734 的前缀语句被推到 if/elif/else **链之后**；链的三支全部 return
⇒ CPython 3.11 死代码消除把整条 `yield self.spawn_single_user(user)` 删掉 ⇒ **−7**。

−2（根因 A）+ −7（根因 B）= **−9**，与 §2 的删除窗口逐条吻合。

## 6. 候选规则全表（含失败项）

度量 = `r21_twins.py`（目标 pyc，12 个限定名逐函数尺子）+ `run_all.py --measure`（16 项电池）
+ 全量 A/B（`r21_par.py`/`r21_sum.py`，402 索引项逐函数 `n_ok`）。
"孪生" 列：`HSID orig=175 / OAuth orig=190`。

| id | 规则（站点 + 判据） | HSID decomp | OAuth decomp | strict | 电池（基线核） | 判决 |
|---|---|---|---|---|---|---|
| base | 无（5c63ce6b） | **166 (−9)** | **181 (−9)** | 10/12 | 6 MISMATCH / 10 MATCH | 缺陷基线 |
| base_head | 无（15a8de06，含 R20-A） | 166 | 181 | 10/12 | 6 MISMATCH / 10 MATCH | R20-A 与本族无关 |
| **c1** R21-A′ | 站点 A：成员块加「CALL…POP_TOP（含 YIELD_VALUE/RESUME 间隙，向前≤5）」 | **176 (+1)** | **191 (+1)** | 10/12 | 2 MISMATCH(13,14 之类) | 修掉 A，残留 B 的错位 → +1 条 `JUMP_FORWARD`（唯一差量） |
| **c2** R21-B′ | 站点 A（更宽）：成员块尾跳之前出现**任何** `POP_TOP` 即判 body | 176 | 191 | 10/12 | 同 c1 | 与 c1 同测值 ⇒ 宽判据无额外收益，风险更高（`POP_TOP` 也出现在 with/异常记账）→ **丢弃** |
| **c3** R21-C | 站点 B：`_check_elif_chain` 过滤表补 `YIELD_VALUE` 间隙（一行） | **173 (−2)** | **188 (−2)** | 10/12 | 5 MISMATCH | 只补 B，A 的 −2 仍在 ⇒ 证明两半缺一不可 |
| **c5** | c1 + c3 | **175 (0)** | **190 (0)** | **12/12** | 12 MATCH / 4 MISMATCH | **完全收口** |
| **c6 = R21-A（提案）** | 站点 A 用**与起始块/elif 完全同形**的判据文本（过滤表 + CALL→gap→POP_TOP 扫描）+ 站点 B 同 c3 | **175 (0)** | **190 (0)** | **12/12** | 12 MATCH / 4 MISMATCH | **采纳**（HEAD 15a8de06 同样 12/12） |
| **c8** | c6 + 第三份拷贝（BoolOp 起始块 24024-24035）也补间隙 | 175 | 190 | 12/12 | 同 c6 | 目标上无增量收益；扩大爆炸半径 → **不并入**，留待全量数据判断 |

c1 残留 +1 的定性（`diffs/c1__OAuthCallbackHandler.diff.txt`）：`JUMP_FORWARD orig=0 decomp=1`，
来自 else 臂（块 734）语句被链后放置后仍需绕开 if/elif/else 的 fall-through，
属根因 B 的下游症状 —— c6 一并消除。

## 7. 电池（16 项）实测逐项

`python test_repros/round21_oauth2/run_all.py --core <镜像> [--base] [--strict]`

| 复现 | 基线（5c63ce6b / 15a8de06 同） | R21-A（c6，两 rev 同） | 表值 |
|---|---|---|---|
| 01 anchor_twin_full | MISMATCH 102/95 | MATCH | SENTINEL |
| 02 anchor_boolop_then_yield | MATCH | MATCH | MATCH（**独立形状不复现**：缺了 `if user.spawner:` 外壳，A 族不触发 —— 见 §10） |
| 03 anchor_elif_yield_prefix | MISMATCH seq_diff@16 | MATCH | SENTINEL |
| 04 neg_plaincall_prefix | MATCH | MATCH | MATCH |
| 05 anchor_plaincall_boolop | MATCH | MATCH | MATCH（普通调用在 A 站点该形状下已被起始块判据接住） |
| 06 neg_assign_prefix_both | MATCH | MATCH | MATCH |
| 07 neg_pure_elif_chain | MATCH | MATCH | MATCH |
| 08 anchor_elif_bodies_yield | MISMATCH 70/63 | MATCH | SENTINEL |
| 09 anchor_double_nested_yield | MATCH | MATCH | MATCH（两层嵌套同形但不触发，外壳才是必要条件） |
| 10 anchor_hsid_twin_clone | MISMATCH 122/115 | MATCH | SENTINEL |
| 11 neg_call_in_elif_condition | MATCH | MATCH | MATCH（CALL 后是 COMPARE_OP ⇒ 间隙扫描立即停止） |
| 12 neg_await_shape | MISMATCH 44/41 | MISMATCH 44/41 | MISMATCH（`GET_AWAITABLE/SEND` 族，异因，未被本规则顺带修好，也未恶化） |
| 13 anchor_yield_prefix_in_loop | MISMATCH 40/34 (−6) | MISMATCH 40/41 (+1) | MISMATCH（循环内同族：R21-A 找回 6 条但多 1 条跳，**距离 −6→+1**；与 R20-A 站点无冲突但循环 merge 归属另有根因） |
| 14 neg_real_and_chain | MISMATCH 18/20 (+2) | MISMATCH 18/20 (+2) | MISMATCH（过量发射族，Round 22 目标） |
| 15 anchor_try_except_yield | MATCH | MATCH | MATCH（try/except 外壳下 A 族不触发） |
| 16 anchor_yield_prefix_real_merge | MISMATCH seq_diff@10 | MATCH | SENTINEL |

计数：基线核 `MISMATCH=6 MATCH=10 ERROR=0`；R21-A 核 `MISMATCH=3 MATCH=13 ERROR=0`；
两世界的 `EXPECT_BASE`/`EXPECT` 均 `UNEXPECTED=0`（`--strict` exit 0，见 §9）。

## 8. 提案 R21-A（唯一一条规则，两个接线点）

**规则**（纯同层结构判据，不看函数名/字符串常量/字节码偏移，不跨区域跨层次）：

> 一个以条件跳转结尾的块，若其**末条条件跳转之前**存在 `CALL … POP_TOP`
> （中间只允许 `YIELD_VALUE`/`RESUME`/噪声指令）或 `STORE_*/BINARY_OP/DELETE_*`，
> 则它是 **body 块**（含值丢弃语句），不是 BoolOp 操作数块，也不是纯 elif 条件块。

这正是仓库里**已经写了三遍**的判据（`_sb_has_body` 24013-24035、`_has_body_stmt` 18216-18243、
IfExp 落点 24244-24255）的补全，零新判据；缺的是
① 成员块守卫根本没有 `CALL…POP_TOP` 那一半，② 三份拷贝的过滤表都漏了 3.11 协程的 `YIELD_VALUE`。

**补丁 A**（`core/cfg/region_analyzer.py`，函数 `_detect_boolop_conditional_chain`，
行区 **24186-24200**（5c63ce6b）= **24229-24243**（HEAD 15a8de06））：
在既有 `if _has_store: break` 之后追加同形判据（命中即 `break`，把链留在上一成员）。

**补丁 B**（同文件，函数 `_build_elif_region` 内嵌 `_check_elif_chain`，
行区 **18216-18243** = **18259-18286**）：
把 `for _idx, _i in enumerate(_fe_instrs_before_jump)` 里的
「`CALL` 紧跟 `POP_TOP`」改为「`CALL` →（`YIELD_VALUE`/`RESUME` 间隙）→ `POP_TOP`，
遇其他指令立即停止」。

两段完整补丁文本 = `D:/Temp/r21d/probes/r21_mk.py` 里的 `NEW_MEMBER_C6` 与 `NEW_ELIF`
（可直接 diff 出来；`r21_mk.py c6` 重建候选镜像，锚点唯一性由 assert 保证）。

四条归约原则的保持：
* 自底向上：只改"块是否为 body"的同层判据，不改识别顺序；
* 每块唯一归属：补丁 A 让块 624 归 then 臂 IfRegion，补丁 B 让块 734 归 else 臂
  （`_build_basic_if_region` 已建出的 IfRegion 不再被 elif 链抢走）——**减少**争抢；
* 嵌套即抽象节点：624/734 回到各自臂内，内层 `if cgroupmode` 仍是单个子 IfRegion；
* 入口引用：区域仍只引用臂入口块，不铺开子块。

**与 R20-A 的复合性**：R20-A（HEAD 15a8de06）落在 analyzer `@@ -84,6 +84,46 @@`、
`@@ -6169,9 +6209,12 @@`（`_collect_natural_loop_body` break-target 判别）与
generator 16934-16942/16988（W15-C 臂尾终止守卫）。本提案的两个站点（18216-18243、24186-24200）
与其**完全不相交**，且不改任何 loop-break/return 路径、不在终止符之后新增语句 ⇒
不会触发"死代码被 DCE 吞掉"的陷阱。实测 `git archive 15a8de06` 基线上补丁锚点原样存在、
应用成功、孪生同样 12/12。

## 9. 四道门禁（实测）

1. **孪生 strict**：`r21_twins.py` on c6 →
   `<module>.HSIDOAuthCallbackHandler.post` 与 `<module>.OAuthCallbackHandler.post` 均无 DEFECT，
   `strict: 12/12 functions match`（5c63ce6b 与 15a8de06 两个基线上的 c6 都一样）。
   基线核对照：`strict: 10/12` + 两条 `orig=175 decomp=166` / `orig=190 decomp=181`。
2. **电池**：见 §7；`--strict` 退出码见下。
3. **官方批量**：官方 11/10(`partial`) → 12/12（strict 口径；未跑 `scripts/pyc_batch_verify.py`，属禁止项）。
4. **全量 A/B（402 索引项，逐函数 `n_ok`）**：*进行中*，命令
   `D:/Temp/r21d/probes/r21_par.py D:/Temp/r21d/mirr/base base 12 0 402 r0`
   与 `… r21_par.py D:/Temp/r21d/mirr/c6 c6 12 0 402 r0`，汇总
   `r21_sum.py base c6`，日志 `D:/Temp/r21d/logs/ab_base.log`、`ab_c6.log`。要求 `improved>=1, broken=0`。

## 10. 未收口 / 诚实清单

* **A 族的触发条件比"块含协程语句"更窄**：复现 02/05/09/15（同样含 624 型块，但**没有**
  `if user.spawner:` 外壳、或外层是 try/except）在基线核上就是 MATCH。
  即 settrace 看到的错误链 `[(566,'or'),(624,'and')]` 只在 566 本身是"某 if 臂的落点块"时形成。
  §4 的站点是实测命中点（`logs/tr566.txt`），但**上游为什么会走到成员块扩展**仍依赖
  外层 IfRegion 的 `IF_FALSE` 同目标判据（NONE_CHECK_OPS 豁免段 23921-23948）；
  本提案不需要动它，但这条依赖链没有完全画清。
* **复现 13（循环体内的同族形状）未收口**：R21-A 把 −6 变成 +1，仍 MISMATCH。
  多出的一条是 `JUMP_FORWARD`，与 §6 c1 残留同族（merge 归属），需在
  `LoopRegion` 的 body/merge 判定里另找站点；未做（避免与 R20-A 站点纠缠）。
* **复现 12（`await`）/14（真 and/or 链 +2）**：两世界同形异因缺陷，本规则不碰。
  14 属已登记的"过量发射族"（Round 22 目标）。
* **无关但顺手发现的发射缺陷**：`if (yield self.g(x)):` 产物丢外层括号
  → `if yield self.g(x):` SyntaxError → 无法进电池（原复现 11 因此换形）。
  记录备查，不属 R21-A 范围。
* **全量 A/B 的 base 快照**用的是 5c63ce6b（任务书指定的 pre-R20-A HEAD）；
  修复实际会落在 15a8de06 之上。已在 15a8de06 上复核站点/锚点/孪生/电池四个世界一致，
  但 402 全量只在 5c63ce6b 对上做（HEAD 对作为补充，如时间允许）。
