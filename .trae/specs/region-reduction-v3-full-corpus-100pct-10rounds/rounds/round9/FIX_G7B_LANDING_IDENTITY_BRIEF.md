# Round 9 ticket #15 简报：隐式尾声落点的身份判据（G7 的替代式）

## 为什么立案（主代理逐单元名单实测）

G7 落地前后对 `fly/data/quote.pyc` 的失败单元名单：

    前（after_preG7_b121_only） 87/92：build_current_period_df, get_individual_data,
                                    get_real_from_zeromq, run_individual_transform, run_tick_socket
    后（after）                86/92：上述五个 + **check_frequency**

⇒ G7 是用 `quote.check_frequency` 换回 `history_data_source.get_bars`（各 +1/−1，净 0）。
这不是回滚 G7 的理由（`get_bars` 那两条确实是源码写下的 `else: return None`），
但它证明 G7 抓的是**相关**而不是**不变式**。

## 标本两侧都已钉住（臂常驻，可直接当验收面）

`test_repros/round9/r9q_02_assert_else_implicit_tail.py`（当前 **1/2**，应转 2/2）：

    def check(n):
        if n not in ('w', 'mo'):
            try: tmp = int(n)
            except BaseException: assert False, 'bad int'
            else: assert tmp > 0, 'bad pos'

产物在 try/else 之后多写了一条 `return None`——正确答案是**抑制**（B121 当时抑制了、该臂绿）。
反侧由 `r9g7_01_else_arm_twin`、`r9g7_04_mixed_elsearm_and_tail` 钉住（当前 2/2，
必须**保持** 2/2：它们就是 get_bars 形，抑制会把两条真语句吞掉）。

## 候选替代式（**未经证实**，工单第一件事是验它）

G7 现式：`kind == 'handler-epilogue' ∨ 前驱末指令 == POP_TOP`。`POP_TOP` 一支是opcode 巧合，
不是区域事实；用 Round 8 探针（`D:/Temp/rrv8/probe_b121_roles.py`）已有的角色数据重看四个标本面：

| 标本 | kind | 在区域中扮演的角色 | 应判 |
|---|---|---|---|
| `get_bars` 288 / 292 | pure-none | **某 IfRegion 的 `else_blocks` 成员**（臂体本身） | 语句 |
| `flytools` 722 / 748 | pure-none | 不在任何 then/else/merge 角色里（with 体尾顺序续体） | 落点 |
| `flytools` 906/918/930/942 | handler-epilogue | 918/930 也是 `else_blocks` 成员，942 是 `merge_block` | 落点 |
| `r9q_02` 尾块 | pure-none（推测） | 不在臂角色内（try/else 之后的汇合尾） | 落点 |

⇒ 能把四者同时判对的最小式子是：
**`pure-none` 且本块是某区域 `then_blocks`/`else_blocks` 的成员 ⇒ 语句（发射）；
其余（含 handler-epilogue）⇒ 逐边落点（不发射）**——不再需要 `POP_TOP` 这一支。
这是区域成员事实（原则 2/4），比 G7 的 opcode 巧合更符合 rules.md 的算法口径。

**未验证清单（先做，做完才许改代码）**：
1. `r9q_02` 尾块的实际区域角色必须由探针打印确认（上表该行是推测）。
2. `r8` 电池 31 臂与 `r9` 全部臂在新式下的 sink 集合要逐臂重算，确认无绿臂转红。
3. `history_data_source` 19/19、`flytools` 66/66、`quotation` 153/153 三点先单验再动代码。

## 排序与边界（硬性）

- **必须在 #14 落地并重测之后**。理由：G7 判据的 G5 用「前驱与落点同属一区域」，
  而 #14（`[R9-B122 fwdonly]`）正在改**区域边界与成员归属**——边界一变，本票所有角色读数作废，
  必须用新字节重取。任何在 #14 之前得到的"验证"都不算数。
- 若 #14 之后 `check_frequency` 已被顺带修好，本票降级为「判据改写（去掉 POP_TOP 巧合支）」，
  仍要做，但验收改为「零回退 + 判据表达为区域事实」，不再声称翻单元。
- 禁止同时保留 POP_TOP 支与新角色支（两真相源）；替换即替换，删除的常量/分支须在报告列明影响面。
- 验收读数一律逐单元名单，不许只报 `86/92` 这类总数。
