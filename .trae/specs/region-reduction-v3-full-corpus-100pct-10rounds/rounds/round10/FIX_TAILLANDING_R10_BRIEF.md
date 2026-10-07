# Round 10 工单 #15（续）简报：`handlers._target` 的**一对** `LOAD_CONST None/RETURN_VALUE` 缺失＝该单元全部 17 处差

取证口径同前两节（输入读盘、产物读盘上现字节、只读 stdlib、**按完整 qualname 路径配对**）。
仪器：`D:/Temp/r9main/r10loss.py` 同款 hunk 打印；本节数字为其原表 `D:/Temp/r9main/r10loss.txt` 之后的一次定点复跑。

## 一、靶面与证据

`IQCommon/logger/handlers.pyc :: <module>.TWHThreadController._target`
（文件读数 29/30 ⇒ **修好这一条单元即整文件 OK**，是本轮门禁的第三条独立路径）。

原始序列 199 条，产物 197 条，`net=+2`，17 个 hunk——但**内容差只有 1 处**：

```
delete  orig[75:77]=2  prod[75:75]=0
   ORIG: LOAD_CONST None | RETURN_VALUE
   PROD: （无）
```

其余 16 处全部是 `POP_JUMP_FORWARD_IF_FALSE` 一类**同 opcode、仅目标偏移不同**的差
（`->@412` 变 `->@408`、`->@408` 变 `->@404`……即那 4 个字节缺失沿跳转图的传播）。

缺失位置的**原字节码上下文**（这就是判据要恢复的形状，别把它当函数尾的隐式 return）：

```
 #70 LOAD_FAST   self
 #71 LOAD_ATTR   running
 #72 POP_JUMP_BACKWARD_IF_TRUE ->@104     ← `if self.running:` 真则跳回循环头 @104
 #73 LOAD_CONST  None
 #74 RETURN_VALUE                          ← 第一个隐式尾（循环出口路径的 return）
 #75 LOAD_CONST  None                      ← ★ 第二个成对的隐式尾，产物未发
 #76 RETURN_VALUE                          ← ★
 #77 LOAD_GLOBAL sys  …（其后是 `if sys.version_info[0] == 3:` 的真实语句）
```

⇒ **两块合一**的症状：循环出口路径的返回尾与「其后语句的共用尾」是两个不同的落点，
产物把它们并成一个，于是少发一对，且共用块之后的语句仍照发（所以不是截断，是**并块**）。

## 二、验收夹钳（全有或全无，不许报「17 处里修好 1 处」）

1. 复跑本仪器：`hunks` 必须由 **17 → 0**。
   若补发了一对却仍有 16 处目标差，说明补的位置不对（偏移没回到 `@412/@408` 那组），**判 FAIL**，
   不得以「内容差已消」自证。
2. `pyc_verify single site-packages/IQCommon/logger/handlers.pyc` 必须 `30/30 status=success`。
3. **配对证明出的天然负对照**（必须保持 Equal）：同文件另有
   `<module>.TWHThreadRotatingFileHandler._target`，本仪器实测 `len 126/126, hunks=0`。
   它就是 Round 9 那次「同名尾段匹配」误判的元凶——**按完整路径配对后它是干净的**。
   收紧判据时若把它一起改动（hunks 由 0 变非 0），即为以改判据换读数，判 FAIL。

## 三、与 G7 的关系（本票的真正改动面）

现 HEAD `region_ast_generator.py` 的 G7 条款实测在两处（锚点已复验，非转述）：
- `:51700` 方法 docstring 的 `(G7)` 段；
- `:51806` 代码内的 `# [G7] 只有「由前驱语句自身退出路径携带的尾」才是落点；pure-none 且
  由条件测试跳转边接入的终块是某个臂的唯一语句（源码写了 return None），必须发射` 分支，
  其放行条件是 `_pli is not None and _pli.opname == 'POP_TOP'`——**POP_TOP 巧合支**。

本票要求（沿用 `rounds/round9/FIX_G7B_LANDING_IDENTITY_BRIEF.md`，其 §G7 面在 HEAD 已复验存在）：
用**区域成员事实**替换该巧合支——`pure-none ∧ 属某区域 then/else 成员 ⇒ 语句，必须发；否则才是落点`。
本案正是要它发第二对隐式尾：两个 pure-none 终块共享同一段码，**成员关系不同**（一属循环出口，
一属其后语句的共用尾），故判据能分；靠 `POP_TOP` 不能分。

候选式已在四标本上面自洽；**排产纪律不变**：必须在 #16 之后重取角色——
#16 改成员关系（`while True` 归还体内 `if`），而本票判据**直接消费成员关系**，
先派本票等于用自己的取证去追别人正在改的字节。

## 四、禁止项

- 禁在函数尾「补一个 `return None`」（那是输出端凑数，且 §一 已证其后仍有真实语句）。
- 禁 `POP_TOP`/`LOAD_CONST` 计数或深度门控；禁文件名/函数名特判；禁 G3 前缀新方法。
- 先臂后码：`r10g7_` 前缀，≥10 复现、深度 ≥3，负对照 ≥2
  （其中一条**必须**是 `TWHThreadRotatingFileHandler._target` 形的干净同名单元）。
- 回报边做边写：`rounds/round10/FIX_B127_G7_MEMBER.md`；零翻转按 sha256 逐字节回滚。

## 五、同判据面的另外两条单元（本轮新取证）——`trade_info_utils` 因此成为第二扇可翻正的门

对 `IQCommon/util/trade_info_utils.pyc` 的四个失败单元逐条复跑同款 hunk 仪器：

| 单元 | len | 真实内容差 | 形状 |
|---|---|---|---|
| `<module>.get_trade_status` | 171/171 | **0**（1 hunk 是 `JUMP_FORWARD` 目标 `@810→@786`） | 纯落点（属 #14 A 档） |
| `<module>.kill_trade_process` | 659/659 | **0**（2 hunk 是 `IF_NONE↔IF_FALSE` 两条目标**互相换位**；第三条见 §六 是仪器假差） | 换位（属 #14 B 档） |
| `<module>.query_strategy_id` | 117/116 | **2**：`orig[108] JUMP_FORWARD ->@648` 在产物里变成 `LOAD_CONST None; RETURN_VALUE`（就地内联返回），且 `orig[115:117]` 那对 `LOAD_CONST None/RETURN_VALUE` 消失 | **与 §一 `_target` 同一枚硬币的两面** |
| `<module>.query_trade_strategy_info` | 122/122 | **3**：两处同形（`orig` 的 `JUMP_FORWARD ->@618` 被写成就地内联 `LOAD_CONST None; RETURN_VALUE`） | 同上 |

⇒ 本票的机制表述要按此收紧：**共享的隐式尾声 epilogue 没有被识别为单一落点**，
于是每条路径各自内联一份 `return None`，而真正该被跳进去的共用尾反而不发。
`_target` 表现为「少发一对」，`query_*` 表现为「多发内联 + 少发共用尾」——
**一条判据同时管三单元**。
`trade_info_utils.pyc` 现 37/41：若本票收 `query_strategy_id` + `query_trade_strategy_info`，
#14 收 `get_trade_status` + `kill_trade_process`（换位形），**该文件即可 41/41 整文件翻正**。
⇒ 轮门禁因此有两条独立路径：`handlers`（本票 1 单元）与 `trade_info_utils`（本票 2 + #14 2）。

## 六、仪器假差登记（禁把它记成缺陷）

`kill_trade_process` 的第一条 hunk 是
`LOAD_CONST <code object <listcomp> at 0x000001EF2BE9E330, file "./fly_docker_py311/…", line 228>`
对 `LOAD_CONST <code object <listcomp> at 0x000001EF2BE9E230, file "p", line 228>` ——
差的是 **`repr()` 里的内存地址与文件名**，两个 listcomp 本体未必不同。
`seq()` 直接取 `argrepr`，凡含嵌套 code object 的常量都必然产生假差。
⇒ 计数已剔除该条（故上表写「0 真实内容差」）；
未来任何按 `argrepr` 比较的统计都必须先把嵌套 code object 归一为 `<co>`，
否则假差会混进「单元数」里（Round 9 的 `NORMALIZER_BLIND` 误判即同源）。


## 七、附：落地标记的**准确拼写**（防未来的假阴性 grep）

主代理本轮一次 grep 误报「Round 1 的三处守卫标记在 HEAD 已不存在」——
实为我的模式写错大小写/轮次（`r8-b98` 应为 `r1-b98`）。`git show HEAD:` 复测命中数：

| 标记 | 命中 |
|---|---|
| `[r1-b98-elsescope]` | 5 |
| `[r3-b100-armjoin]` | 5 |
| `[r3-b100-armjoin-tailexit]` | 4 |
| `[r3-b103-armjoin-termexit]` | 5 |
| `[R5-B100-armjoin-trueentry]` | 4 |
| G7 条款（`G7`） | 2（`:51700` docstring、`:51806` 代码） |

⇒ 守卫**未丢**；「grep 零命中」在断言缺失之前必须先怀疑大小写与所查文件
（本案三处标记在 `region_analyzer.py` 而非 generator）。

## 八、名单扩至 9 条后的**逐单元验收夹钳**（取代 §一/§五 的 3 条版；机制同一）

| # | 单元（完整 qualname） | 实测差（读回语句） | 该单元的验收夹钳 |
|---|---|---|---|
| 1 | `IQCommon/logger/handlers.pyc :: <module>.TWHThreadController._target` | `orig[75:77]` 一对 `LOAD_CONST None/RETURN_VALUE` 未发（#72 `POP_JUMP_BACKWARD_IF_TRUE→@104` 的出口尾与 `#77` 之后语句的共用尾并成一块） | hunks **17→0** ∧ `single` 30/30；**只补一对不算过**（余 16 处是那 4 字节的传播） |
| 2 | `IQCommon/util/trade_info_utils.pyc :: <module>.query_strategy_id` | `orig[108] JUMP_FORWARD→@648` 被写成内联 `LOAD_CONST None; RETURN_VALUE`，且 `orig[115:117]` 共用尾缺失 | 内联必须**改回跳转**且共用尾**在位**；不得反向（把共用尾删了凑数＝少发射换全绿） |
| 3 | 同文件 `:: <module>.query_trade_strategy_info` | 两处同类内联（`orig[94]`、`orig[113]` 的 `JUMP_FORWARD→@618`） | **净差为 0 但缺陷为真**：判据必须让两处内联同时消失，逐 hunk 归零，不得以 `net==0` 判无缺陷 |
| 4 | `fly/data/quote.pyc :: <module>.Quote.check_frequency` | `orig[106:108]` 就地返回被写成 `JUMP_FORWARD`，另在函数末多出 `prod[130:132]` 一对 | 返回**归位**且末位多余对**消失**（两处同判据，缺一即仍红） |
| 5 | `IQCommon/api/klinedata.pyc :: <module>.get_multiminute_his_data` | `orig[512] JUMP_FORWARD→@527` 变内联 `LOAD_FAST his_data_dict; RETURN_VALUE`，且 `orig[527]` 的 `LOAD_FAST his_data_dict` 在产物里成了 `LOAD_CONST None` | 共用尾内容**记回正确返回点**：两条必须同时修，否则值错为 `None` |
| 6 | `IQCommon/strategy/wizard_quant_api.pyc :: <module>.filter_desicion` | `IF_NONE` 应落 `if x is None: return` 的 `@710`，产物落 `@774` 尾部且函数末多一对 `LOAD_CONST None/RETURN_VALUE` | 落点归位 ∧ 多余对消失 |
| 7 | `fly/data/quote.pyc :: <module>.Quote.get_real_from_zeromq` | 真差两条：`JUMP_FORWARD`(#174) 与 `POP_JUMP_IF_FALSE`(#178) 应进共用尾 `return None, flag`，产物在块前多插 `JUMP_FORWARD@1024→1034` 把两条入边都跳过 | **先做常数位移检验**：31 处差里只有一条 `JUMP_FORWARD` 多余，其余是 2 字节位移影子 ⇒ 夹钳＝多余跳转消失后位移自动归零，不许逐 offset 对齐 |
| 8 | `IQCommon/util/trade_info_utils.pyc :: <module>.kill_trade_process` | 两条跳转目标互换（`IF_NONE`/`IF_FALSE`） | 互换纠正后 hunks→0；单向规则必错（见 `FIX_LANDING_R10_BRIEF.md` §六.2） |
| 9 | 同文件 `:: <module>.get_trade_status` | 应落 `error_no == 0` 共用测试段，实落 `POP_EXCEPT/RERAISE` 尾声 | 与 §六.2 的 F1 同一判据（**一判据吃 `load_daily` 与本文件**） |

**同一性断言（本票的立论，不可拆成多票各自记功）**：1–7 都是
「**共用返回尾未被认成一个落点**」——产物要么逐路内联返回、要么把入口跳到尾之后。
8、9 属落点票的汇合块判据，但 §六.2 的 F1 与本票 #7 读回的是同一枚 handler/尾块身份 ⇒
两票须互相复跑对方名单，任一票改动使对方名单出现新红即判回退。

**翻正预期（只按文件差 1 单元者）**：#1 即 `handlers` 整文件翻正。
`trade_info_utils`（37/41）需 2/3/8/9 四条齐闭合；`quote`（86/92）需 6 条；`klinedata`（61/64）需 3 条；
`wizard_quant_api`（55/58）需 3 条 —— 除 #1 外**一律不作翻正承诺**。
