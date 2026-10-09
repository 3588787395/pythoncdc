# Round 11 第二日台账（主代理自施工，无子代理可用）

背景：四张在飞子代理票（B139b、B136b、B138、B140）全部因供应商**每日 Chat 用量上限**中途死掉
（B139b 只交了 `FIX_B139B_*.md` §0 基线表、无补丁；B136b 只建好镜像；B138/B140 只留探针与产物草稿）。
今日所有施工由主代理在镜像里做，仓库 `core/` 全程未动。

## 封表基线（不变，仍是本回合唯一落地读数）

| 项 | 值 | 来源 |
|---|---|---|
| 单元 | **6580/6617（99.4408 %）** | `rounds/round11/after`（8 分片报告） |
| 文件 | **387/402** | 同上 |
| 四硬门 | 0 / 0 / 0 / 0 | `gate_round.py … checks` |
| 残余 | **15 文件 / 37 单元** | `RESIDUAL_R11.md`（封表 15:37:42） |
| quotation | 153/153 | 本轮多次复测一致 |
| small34 | 1531/1568（19 绿文件） | 同上 |

今日**没有**新增落地：三张新票（B139c / B141 / B142）共 **5 个臂**全部证伪，逐臂读数在
`DIAG_B139C_CHAIN_START_JGATE_FALSIFIED.md` §2/§4 与 `DIAG_B142_LOOP_LANDING_INERT.md` §0/§8/§9。

## 逐票状态

| 票 | 目标 | 臂 | 读数 | 裁决 |
|---|---|---|---|---|
| B139c | `bar` 84/85、`strategy_universe` 10/11、`strategy` 26/27 | blanket 回溯 | bar 85/85，quotation 152/153 | 不落地 |
| B139c | 同上 | J-gate `360fae76ce699366` | bar **85/85**；quotation/tiu/suni/strategy/klinedata/wqa/tlb **产物逐字节 SAME_as_HEAD**；quote 86→85（新红 `load_bars_from_hundsun`） | 不落地（净 0 单元、0 文件） |
| B139c | 同上 | J+F-gate `1e5fdda8351ff923` | bar 85/85、quotation SAME、quote **仍 85/92 同一红** | 不落地；无副作用普查证明 bar 头与 hundsun 头在我能测的 CFG 事实上**不可分**，本轴收口 |
| B141 | `handlers` 29/30 | 循环终块强发 `2aa23a5a453b94cc` | **28/30**：目标单元未翻正、兄弟单元新红；控制器单元 199→**77** 指令 | 证伪；`[result] + stmts` 的列表返回只被 `:7992` 一处消费 |
| B142 | 同上 | 收尾扫放开登记 `a0a13cfad723da6d` | 产物 `9093` 字节 **与 HEAD 逐字节相同**（惰性）；quotation 仍 SAME | 证伪；下一票唯一入口在 §9 |
| B138 | `matcher` 16/17 | （死票，读数继承） | oracle `m_or_full.py` **17/17**：需 or-fold + guard-fold + 补回 `@2164` 测试**三形同单元** | 不是单机制票，挂起 |
| B140 | `api_base` 27/28 | （死票） | 我此前做的语句交换 oracle 无改善 ⇒ 结构性差 | 挂起 |

## 方法账（今日新立的两条硬规则，已进记忆）

1. **分析器内探针不惰性**：读 `.successors/.predecessors/get_block_by_offset` 自身会改产物
   （实测把 `trade_info_utils` 从 61281 字节/38/41 变成 60591/37/41，且判据置死仍如此）。
   新规矩：探针只读作用域内局部量 + `start_offset`/`len(...)`，并在引用任何读数之前做一次
   「有探针 / 无探针」产物逐字节对比自证。
2. **子区域返回值契约**：`_generate_region` 返回列表的通道在发射器里只有 1 个消费点（`:7992`），
   想「在循环之后再发兄弟语句」必须先清点全部消费点，不能靠加判据绕开。

## 下一票（未派，按代价排序）

**先记一票的前置被实测推翻**：B144 原本写「清点 `_generate_region` 返回值的全部消费点再补对称处理」。
在仓库字节上 `grep -c "_generate_region("` = **108**（含定义 1 处，消费点 107 处，遍布
`:1911 / :4215 / :6390 / :6557 / :7990 / :8358 / :9076 / :11828 / :13034 / :13961 / :14019 …`）。
逐点判定「是否接受 list」不是本回合能承受的成本，且任一单点改动都会牵动上百个非本案例区域 ⇒
**「让 loop 分支用 list 交付落点语句」这条通道按架构不可用**，不是我没写对。

因此 handlers 的可行方向改回**集合侧**（未做，留给下一轮，先要读数不要先动刀）：
IfRegion@0 的右臂块集来自 `then_blocks/else_blocks`，而 `@404` 只是 IfRegion@0 的 plain member、
不在任何字段里 ⇒ 要么分析器把落点收进**父区域**的臂集合（成员关系变更，与 B127 同族风险），
要么发射器在消费子区域之后按「子区域终块成员」续取一次（新通道，仍需逐案证明不双发）。
两条都要先回答同一个问题：**@404 应归父区域还是归循环**——这是分析器裁决，不是发射开关。

其余按代价排序：

1. `trade_info_utils` 的共用尾家族（`query_strategy_id` +1、`query_trade_strategy_info` 净 0）——
   与 handlers 同族但不同单元，2 单元，不翻文件。
2. `matcher` 三形同单元票（oracle 文本已钉死，`m_or_full.py` 17/17），需一次改三处，风险最高、收益 1 文件。
3. `handlers` 归属裁决票（上述两条方向，先读数后动刀）。

## 追加（同日晚，读数把 handlers 的宿主钉到行）：归属其实已经解决

用无副作用普查（新建 CFG + 新建 RegionAnalyzer，独立进程）读 `IfRegion` 的臂字段：

```
IfRegion entry@0   condition_block=46  merge_block=412  exit=412
                   then_blocks = [90, 404, 408]      else_blocks = []
                   blocks      = [0, 90, 404, 408]
IfRegion entry@412 condition_block=412  else_blocks=[1012]  blocks=[412,458,504,658,1008,1012,1016,1020]
```

⇒ **`@404` 已经在父区域 IfRegion@0 的 `then_blocks` 里**，「归属未定」这个前提不成立；
把它丢掉的是父臂消费时对 `generated_blocks` 的跳过（该方法的 6 节模板自己写着
「遇到已在标记集中的块直接 continue」），而 `@404` 正是被 loop 收尾扫
（`:5361-5374`）登记进 `generated_blocks` 的。这同时解释了 B142 为什么逐字节惰性：
B142 判据没命中（或命中后仍被 `:7998` 的 `_child_region_blocks` 分支跳过），
所以父臂的 `continue` 照旧发生。

**锚点自我更正（必须留着，别再被引用成施工点）**：我先写「实际语句在 `:24966`
`if b in self.generated_blocks: continue`」，随后逐行读回 `:24958-24975` 证明**错位**——
那一段是 `_loop_entry_generate` / `_fis_skip_blocks` 的**检测循环**（R59：为
`for_iter_setup` 块决定改走 `_generate_region`），不是发射跳过点。
发射跳过点在 `_process_if_blocks`（`:24770` 起）里，`24900-25100` 段内
`if … in self.generated_blocks: continue` 形式共 **5 处**（相对行 67/120/174/195 等），
下一票**必须先把这 5 处逐条读回、指出哪一处消费 `then_blocks`**，再动手；
本台账不再给出未读回的行号。

下一票（B145，判据已给定，站点待读回）：在真正的父臂发射跳过处放一个**结构例外**——
块为终块（零正常后继 ∧ 零异常后继）∧ ∈ 某子区域 `blocks` ∧ 不在**任何**区域的角色字段里
∧ 前驱全落在该子区域内 ⇒ 该块的 `generated_blocks` 登记来自「只登记不发射」的收尾扫，
应当在此发射一次。必须同时证明：(i) 真被子区域发射过的终块不会命中
（需先读 `_loop_generate_while` 对 body/else 终块的登记路径）；
(ii) 同文件 `TWHThreadRotatingFileHandler._target` 的两个 entry@2 LoopRegion 不因此双发
（`@780` 在另一区域是 `body_blocks` 成员，被第 3 条排除）。
注意这是**单点放行**：同一类跳过在 loop 的 else 臂消费点 `:7998` 也存在，
若只改一处就必须在票里写明只覆盖哪一个臂消费，不得声称整族已修。

**B145 已按上述判据实现并实测（同日第三次惰性）**：补丁字节 `3c0ce73bf16adbef`，
helper `_r145_arm_terminal_exception`（终块 ∧ 无任何角色字段（全局遍历 self.regions）
∧ 前驱全在同一子区域内）装在 `_process_if_blocks` 的
`if anchor_stmts and block.start_offset in anchor_stmts: …` 之后的那个
`if block in self.generated_blocks: continue` 上（读回确认这才是 `_process_if_blocks`
自己的逐块发射循环，`:24966/:25019/:25073` 三处都是检测循环）。读数：

| 文件 | HEAD | B145 |
|---|---|---|
| `IQCommon/logger/handlers.pyc` | 29/30 | 29/30，产物 `9093` 字节 **SAME_as_HEAD** |
| `fly/data/quotation.pyc` | 153/153 | 153/153，**SAME_as_HEAD** |

⇒ 该循环**不是**渲染 `IfRegion@0.then_blocks=[90,404,408]` 的那条路径（或 helper 对 `@404` 返回 False，
两种可能都还未分离）。因此本轴第四次动手的前提是**派发追踪**，不是再改判据：
用已证明惰性的探针形（只读 `block.start_offset` 与局部量，跑一遍与 HEAD 产物逐字节对比自证）
在候选消费点打印「谁以什么 blocks 参数调用了谁」，先确定 `IfRegion@0` 的右臂经由
`_generate_if` / `_process_if_blocks` / `_if_generate_branch_stmts` / `:13034/:13116`
之中哪一条真正消费到 `@404` 的位置，再决定放行点。镜像补丁留在
`D:/Temp/r141/wt/core/cfg/region_ast_generator.py`（安装脚本 `patch_b145.py`），仓库字节未动。





网络事实：`git push` 今日连续 4 次失败（`Recv failure: Connection was reset` / `port 443 … Couldn't connect`），
三个 round-11 提交（`9a738074`、`cdee0498`、`8b5a0c56`）仍在本地待推。
