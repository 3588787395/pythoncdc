# Round 10 工单 #15（B127）落地回报 —— G7 尾块身份改「区域成员事实」

**结论先说：本票零翻转（handlers 仍 29/30、hunks 仍 17），且票面 §三 指定的站点在现字节上
不可能翻转本单元**——判据面 `_r8_b121_implicit_tail_landing_sinks` 是**只减不增**的抑制集，
而本案缺的那对 `LOAD_CONST None/RETURN_VALUE` 从未被任何发射路径请求过。
补丁已实现、已复验无回退、已归档，**未落地**（见 §7）。

- 标记：`[r10-b127-g7member]`（补丁文件中命中 3 处：(G7) docstring 段 / 臂成员字段表 / G7 代码支）
- 工作副本：`D:/Temp/r15b/wt`（镜像；**仓库 `core/` 一行未改**，实测见 §0）
- 交付物：`D:/Temp/r15b/b127.patch`（unified diff，6647 B）+ 整文件替换件
  `D:/Temp/r15b/region_ast_generator.B127patched` + 安装器 `D:/Temp/r15b/install_b127.py`
  （本仓库配了文本过滤器，CRLF 上下文补丁 `git apply` 不可靠 ⇒ 以 sha256 逐字节换件为准）
- 判据：`scripts/pyc_verify.py`（compare-only）；产物一律先删旧再
  `python -X utf8 pycdc.py <in.pyc> -o <out>` 重生成；未手改任何 `*OK.py`。

## 0. 镜像自证（先于任何实验）

| 项 | 实测 |
|---|---|
| 镜像 `core/ bytecode/ parsers/ utils/ scripts/ pycdc.py` 逐文件 sha256 | 与仓库一致，`verify_failures=0`（脚本 `D:/Temp/r15b/setup_mirror.py`） |
| 35 个 pyc + 35 个既有产物拷贝 | 全部 sha256 一致，`bad=0` |
| 镜像 HEAD 态 `pycdc.py handlers.pyc` 产物 | sha256 前16位 `65badb9485d3b8f3` ＝ 仓库 `handlersOK.py` **逐字节相同** ⇒ 镜像执行的就是 HEAD 的 `core` |
| `core/cfg/region_ast_generator.py` HEAD sha256 | `e9a8f65f6451bcc895c5558528b03a9d6ef1045f418f0efd267f9900ef174e74` |
| 回报时（本文件写成后）仓库该文件 sha256 | 仍为 `e9a8f65f…`（`install_b127.py check` 打印 `== sealed HEAD : True / marker hits : 0`） |

## 1. 复现票面仪器（HEAD 态、镜像产物）

仪器 `D:/Temp/r15b/b127_hunk.py` = r10loss 同款 + §六 强制的两处修正：
嵌套 code object 常量归一为 `<co qualname>`（否则 `repr()` 里的地址/文件名必产假差）、
root 参数化（读数只取自镜像，不读仓库产物）。

```
IQCommon/logger/handlers.pyc :: <module>.TWHThreadController._target        len 199/197 hunks=17 contentdiff=1
IQCommon/logger/handlers.pyc :: <module>.TWHThreadRotatingFileHandler._target len 126/126 hunks=0  contentdiff=0
```
唯一内容差逐字节复现：`delete orig[75:77]=2 prod[75:75]=0`，ORIG＝`LOAD_CONST None | RETURN_VALUE`；
其余 16 处全是同 opcode 仅偏移差（`->@412`→`->@408`、`->@408`→`->@404`、`->@994`→`->@988`……）。
`pyc_verify single`（HEAD）：`status=failure units=29/30`，失败单元＝`<module>.TWHThreadController._target: Different control flow`。
⇒ 票面 §一/§二.1/§二.3 三条取证**全部为真**，锚点也全部在位（§2）。

## 2. 站点复验（票面锚点 vs 现字节）

四个锚点**全部命中且行号未漂**：`:51700` docstring `(G7)` 段、`:51806-51808` G7 注释、
`:51809-51812` G7 代码支（巧合支 `_pli.opname == 'POP_TOP'` 实为 `:51810`）、
`:51813-51821` `_joint_owner` 走查。消费点 `:51909`（`_generate_block_statements` 单一漏斗）。

## 3. 实测所有权事实（`probe_b127.py` / `survey.py` / `trace3b_b127.py` / `gate_probe.py`）

`TWHThreadController._target`（co_qualname 实测 `TWHThreadController._target`，`co_firstlineno=61`，
44 块 / 18 区域；负对照 `TWHThreadRotatingFileHandler._target` 首行 220——两者同名，
按 `co_qualname`/首行区分，**不得**按 `co_name` 区分，仪器已按完整 qualname 配对）。

| 终块 | kind | 唯一前驱 | 前驱末 opcode / argval | 入边 | 区域成员（实测角色） |
|---|---|---|---|---|---|
| `@404`（orig #73/#74） | pure-none | `@390`（循环体尾） | `POP_JUMP_BACKWARD_IF_TRUE` / `104` | **条件假边顺序落点**（by_jump=False，by_fall=True） | `LoopRegion` plain-member（**无任何臂角色**）＋ `IfRegion.then_blocks` |
| `@408`（orig #75/#76，缺的那对） | pure-none | `@90`（`while` 初测试块） | `POP_JUMP_FORWARD_IF_FALSE` / `408` | 条件跳转 ∧ 顺序落点（by_jump=True） | `LoopRegion.else_blocks` ＋ `IfRegion.then_blocks` |

字节上下文（原码）：`@390 POP_JUMP_BACKWARD_IF_TRUE→@104`、`@404/@406 LOAD_CONST None/RETURN_VALUE`、
`@408/@410 LOAD_CONST None/RETURN_VALUE`、`@412 LOAD_GLOBAL sys`；`co_lines` 实测 `@390..@410` 全部属
**行 63（`while` 行）**，`@412` 属行 75 ⇒ 两对尾都是编译器为 `while` 出口各边内联的副本，
`@412` 是外层 `IfRegion` 的 merge（由 `@44`、`@88` 两条假边进入），**不是**「`@408` 的共用尾宿主」。

**为什么 `POP_TOP` 不能分、成员事实能分（票面 §三 的命题，实测部分成立）**：
`@404`/`@408` 前驱末 opcode 分别是 `POP_JUMP_BACKWARD_IF_TRUE` / `POP_JUMP_FORWARD_IF_FALSE`，
两者都非 `POP_TOP` ⇒ 旧 G7 对二者同判「不是落点」；成员事实确有区别（`@408` 在
`LoopRegion.else_blocks`＋`IfRegion.then_blocks`，`@404` 只 plain-member 属循环），
但**这个区别不改变裁决**（§4 的新支对二者同样判「语句」），故成员事实也不能翻转本单元——
真正分岔的地方不在这道门（见 §6）。

**判据面在本 code object 上的实际死因**（`gate_probe.py` 逐门重放，现字节）：
```
### unit=_target minline=61  actual sinks=[]
  off404   G4b BREAK  pred off390 last=POP_JUMP_BACKWARD_IF_TRUE argval=104 (fall-through only; kind=pure-none)
```
⇒ 全有或全无循环在 **G4b** 就断（`@404` 排在 `@408` 之前），**G7 支在本单元从未被执行**。
票面 §三「G7 的 POP_TOP 巧合支是本票真正改动面」在 handlers 上**不成立**。

**抑制集只减不增的直接实验**（`force_sink.py`，只 monkeypatch、不入库）：

| 强制 sink 集 | 产物 len | hunks |
|---|---|---|
| `∅`（HEAD） | 199/197 | 17 |
| `{@404}` | 199/197 | 17 |
| `{@408}` | 199/**195** | 17 |
| `{@404,@408}` | 199/**195** | 17 |

⇒ 把任一发尾登记为落点只会**再少发**一对（195），hunks 一动不动；
`_generate_block_statements:51909` 命中后的动作是「登记 generated + 发射空语句表」，
结构上无法把缺失的那对**材料化**。本票站点与验收夹钳 1/2 互斥。

## 4. 判据实现（补丁内容，镜像态）

`core/cfg/region_ast_generator.py`，方法 `_r8_b121_implicit_tail_landing_sinks`，三处改动：

1. **臂成员字段表**（与 `_R8_B121_TRANSFER_OPS` 同处声明，唯一读取面）：
   `_R8_B121_ARM_FIELDS = ('then_blocks', 'else_blocks', 'elif_final_else', 'elif_bodies')`
2. **G7 代码支**（`:51806-51821`）：删掉 `_pli.opname == 'POP_TOP'` 巧合支，把
   **G5 的 `_joint_owner` 走查与 G7 的成员事实合进同一次 `for _r in self.regions`**
   （不另立第二套归属判定 ⇒ 不违反「唯一事实源」）；新支读的是
   `kind == 'pure-none' ∧ 本块是任一区域 then/else/elif 臂成员 ⇒ 该尾承载源码语句，
   必须发射，整集作废`；`handler-epilogue` 仍由块内退栈对自证续体、不受成员门约束。
   `_pli` 仍供 G4b 使用，未新增任何 opcode/计数/深度/名字读取。
3. **(G7) docstring**（`:51700-51711`）改写：删去「故本门取 opcode 事实」的旧论证，
   改为成员事实表述，并把两个实测标本写进去（get_bars 288/292 反例、flytools
   722/748 正例）。

`python -X utf8 -m py_compile` 在镜像上通过。BOM 保留、CRLF=59128、裸 LF=0（逐字节补丁）。
sha256：`e9a8f65f6451bcc8…174e74` → `47d52c5443c4004e…dbb623`。

## 5. 轴的人口量（禁把改写当装饰——`census.py`，35 文件全量）

逐块重放 G1–G6 后**单块存活**的终块 **194** 个（194 个唯一 cfg 实例），新旧 G7 四象限：

| old_pass | new_pass | 块数 | 含义 |
|---|---|---|---|
| False | False | 127 | 两判据同判「语句」 |
| True | True | 32 | 两判据同判「落点」 |
| True | **False** | **19** | pure-none ∧ 前驱末 `POP_TOP` ∧ **是臂成员**：旧支放行（抑制），新支改判为语句 |
| **False** | True | **16** | pure-none ∧ 前驱非 `POP_TOP` ∧ **不属任何臂**：旧支误杀，新支认作落点 |

⇒ 判据**不是**同义改写：分歧人口 35/194（两个方向都有）。分歧分布在 11 个文件
（含 `real_quote::get_subscribe_market_codes off684/766`、`realtime_event_source::clock_worker
off7488/8166`、`trade_live_broker::submit_order off354`、`trade_info_utils::query_strategy_id off644` 等）。

## 6. 验收读数（全部取镜像重生成产物）

| # | 夹钳 | HEAD | 打补丁后 | 判定 |
|---|---|---|---|---|
| 1 | `handlers :: TWHThreadController._target` hunks | **17**（199/197） | **17**（199/197，产物 sha `65badb9485d3` 与 HEAD 逐字节相同） | **未达 17→0，FAIL** |
| 2 | `pyc_verify single handlers.pyc` | `status=failure 29/30` | `status=failure 29/30`（产物路径 `D:/Temp/r15b/wt/site-packages/IQCommon/logger/handlersOK.py`） | **未达 30/30，FAIL** |
| 3 | 负对照 `TWHThreadRotatingFileHandler._target` | `126/126 hunks=0` | `126/126 hunks=0` | **保持 Equal** ✔（判据未被为凑数放宽/收紧） |
| 4a | `fly/data/quotation.pyc` single | `153/153 status=success` | `153/153 status=success` | 不回退 ✔ |
| 4b | `D:/Temp/r15b/anchor_mir.json`（`r9w16/anchor_index.json` 5 文件，路径改写为镜像） | `454/454`（39.9 s） | `454/454`（35.2 s） | 不回退 ✔ |
| 4c | `baseline/small34_index.json` 34 文件（一次 batch，未分片：139 s / 260 s） | **1528/1568**（files 34：18 success/16 failure） | **1528/1568**（同上，`elapsed 260 s`） | 不回退 ✔ |
| 5 | 判据面命中集（35 文件、1331 个唯一 unit 实例） | 非空集 3 个 unit | 非空集 3 个 unit，**逐 unit 完全相同（set-diff=0）** | 不回退 ✔ |

补强证据：35 个镜像产物重生成后 sha256 **全部 SAME**（`regen.py`，`DIFF` 计数 0）
⇒ 本补丁在本轮可读语料上是**字节级惰性的**。
命中集明细（新旧同）：`flytools::modify_batcktes_info [722,748,906,918,930,942]`、
`IQEngine/plugins/plugin_fly_data/strategy/strategy::on_before_trading_start [448,474]`、
`::on_after_trading_end [434,460]`。
G7 反例复验：`history_data_source::get_bars off288/off292` 在新判据下仍 `arm_member=True`
（`IfRegion.else_blocks` / `IfRegion.then_blocks`）⇒ 仍判「语句」⇒ 集空 ⇒ 两条 RETURN_VALUE 照发（无回退）。

## 7. 名单单元 2–7（§八）读数（仪器同 §1，产物字节相同 ⇒ 前后一列即可）

| # | 单元（完整 qualname） | len orig/prod | hunks | 内容差 | 判定 |
|---|---|---|---|---|---|
| 2 | `IQCommon/util/trade_info_utils.pyc :: <module>.query_strategy_id` | 117/116 | 4 | 2 | 未动（该文件仍 37/41） |
| 3 | 同文件 `:: <module>.query_trade_strategy_info` | 122/122 | 5 | 3 | 未动 |
| 4 | `fly/data/quote.pyc :: <module>.Quote.check_frequency` | 131/132 | 4 | 2 | 未动（该文件仍 86/92） |
| 5 | `IQCommon/api/klinedata.pyc :: <module>.get_multiminute_his_data` | 529/530 | 5 | 2 | 未动（61/64） |
| 6 | `IQCommon/strategy/wizard_quant_api.pyc :: <module>.filter_desicion` | 195/197 | 2 | 1 | 未动（55/58） |
| 7 | `fly/data/quote.pyc :: <module>.Quote.get_real_from_zeromq` | 782/780 | 39 | 5 | 未动 |

⇒ 2–7 **既未修复也未回退**（零位移）；8、9 属 #14，本票未触碰。
没有任何一个单元因为本判据而翻正，因此**本轮门禁的 handlers 路径不成立**，
`trade_info_utils` 也不会因本票向 41/41 靠近。

## 8. 被否证的票面前提（逐条，含主代理给的锚点）

1. **否证**：「本案是 G7 放行/抑制的取舍」（§三）。实测 handlers._target 的 sink 集在
   **G4b**（`:51799-51802`）就整集作废，G7 支（`:51809-51812`）在该单元**从未被求值**。
2. **否证**：「改 G7 判据即可补回那一对尾」。判据面是抑制集，消费动作只发射空语句；
   强制 `{@408}`/`{@404,@408}` 使产物从 197 降到 **195**，hunks 恒为 17（§3 表）。
3. **部分否证**：「两个 pure-none 终块成员关系不同，故判据能分」。成员关系确实不同
   （`@408`＝`LoopRegion.else_blocks`＋`IfRegion.then_blocks`；`@404`＝循环 plain-member＋`IfRegion.then_blocks`），
   但新判据对二者同判「语句」，区分不产生任何发射差异。
4. **否证**（§一 对源码形状的解说）：`@408` 不是「其后语句的共用尾」。`@408` 由 `@90` 块的
   `POP_JUMP_FORWARD_IF_FALSE→@408`（`while` 初测试假边）独占接入，且 `@390..@410` 全属
   行 63；`@412` 是外层 `IfRegion` 的 merge（`@44`、`@88` 两条假边进入，行 75），
   没有任何边跳进「`@408` 之后」。用 3.11.7 实编对照：`if a and b: while r: body` 只产**一对**尾，
   `if a and b: while r: body; return` 也只产一对——本原码的**两对相邻、同行号**副本是
   逐边内联产物，不是源码级共用尾。
5. **锚点复验为真**：`:51806-51812`、`:51813-51821`、`:51700` 与票面完全一致（巧合支精确在 `:51810`）。
6. **仪器假差**：票面 §六 的 `<listcomp>` 地址差在本仪器中已被 `<co qualname>` 归一消除；
   复跑 `kill_trade_process` 未再出现该假差。

## 9. 真正的缺陷位置（交回主代理改派，本票未动）

发射侧证据（`trace3b_b127.py`，按调用栈打印）：

```
=== GBS off408  -> ['Return']  claimed=True  [minline 61]
     :8007  _loop_generate_while      ← 唯一请求者（else_blocks 兜底通道 _if_generate_branch_stmts）
（off404 无任何请求记录：整个 _target 单元内 _generate_block_statements 从未被以 @404 调用）
IF render entry=0 cond=46 then=[90, 408, 404] else=[] merge=412
```
即：`@404` 属 `LoopRegion#83504.blocks`（**无臂角色**）被外层 `IfRegion.then_blocks` 列出，
但按原则 2（一块一主）由循环认领，而 `_loop_generate_while` 只消费
`body_blocks` 与 `else_blocks=[@408]`，**从不请求循环「顺序落点出口块」的语句** ⇒
两条出口边的落点被并成一次发射。`@408` 发射并被登记 generated，`@404` 蒸发。
下一票的改动面在 while 发射端（`:8000-8007` 的 else/顺序出口通道 + `:8219-8240` 的
`_sequential_after_loop` / `_trailing_return_none_stmts` 装配），
身份事实仍应是成员关系：**出口终块 ∧ 属本循环 blocks ∧ 不在 body_blocks/else_blocks ∧
其唯一前驱在 body_blocks** ⇒ 它是循环出口的第二条边落点，必须作为循环后顺序语句发射。
（本票按 §四 禁改发射端，未动，以免与同时在 `core/` 上取数的两名工程师相互踩字节。）

## 10. 最终状态

**「仅归档 spec 未落地」** —— 仓库 `core/` 未被本票编辑（回报写出后实测
`core/cfg/region_ast_generator.py` sha256 仍为封表值 `e9a8f65f6451bcc8…`、
`[r10-b127-g7member]` 命中 0），全部读数来自镜像 `D:/Temp/r15b/wt`。

- grep 标记：`[r10-b127-g7member]`（补丁态命中 3）
- 补丁：`D:/Temp/r15b/b127.patch`；整文件件：`D:/Temp/r15b/region_ast_generator.B127patched`
  （sha256 `47d52c5443c4004e65ce702d89a417fe1947db60aa2dffc6900801003dbbb623`）；
  换件/校验/回滚：`python -X utf8 D:/Temp/r15b/install_b127.py apply|check|revert`
- 建议：**按零翻转归档，不落地**（夹钳 1、2 未达；夹钳 3、4、5 全保持）。
  落地它的唯一收益是消掉 `rules.md §1.5 C3` 的巧合支（人口 35/194，见 §5），
  但它在现语料上字节惰性，且 handlers 路径仍红 ⇒ 不构成轮门禁的第三条独立路径。
