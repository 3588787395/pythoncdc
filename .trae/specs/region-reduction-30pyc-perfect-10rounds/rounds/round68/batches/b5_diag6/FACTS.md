# diag6 FACTS · Round 68

## Step 0 · baseline replay（arm=landed，工作树字节）
逐字段与 BRIEF/targets.md 预读数 **完全相符**，无更正。

### targets（dump/landed.jsonl）
- order_api.pyc **32/34**：future_order 101/92 (jump=2,true=36)；option_order 83/73 (jump=3,true=39) ✔
- risk_calculation/__init__.pyc **33/35**：_on_publish_after_trading_end 486/481 (3,33)；_save_testds_to_csv 71/68 (7,19) ✔
- flyAccount.pyc **21/23**：_do_request 436/443 (2,384)；init_connection 42/41 (0,25) ✔

### canary（4/4 全匹配，sha 合同值一致）
quotation=4d41187e356544e0, market_time=af77224b34b203c4, IQCommon datetime_func=e711b8ea86d49a15, IQData datetime_func=9d09af09249da177 ✔

### battery（45 项，dump/repro65_landed.jsonl）
matched=**174/200**、缺陷函数=**26**、Σ|Δ|=**101**、worse-than-landed=0、ERR=0 ✔
关键项：r63b5_w1 1/2 d=-1；r65_trytail 8/9 d=-3；r65d2/fs2 6/10 d=-12；r67d4_controls 7/8 d=0；r67d5_site2 4/8 d=-43；r67d6_boolop_ternary 5/6、ternary2 6/8；r67d6_whiletrue_headif 1/2 d=0。


### risk_calculation（dump/nd_risk.txt，共 3/43 差异）
- _on_set_positions 336/337：hunk1 `EXTENDED_ARG+JUMP_BACKWARD`→`JUMP_FORWARD`@256；hunk2 在 301 处多插 `EXTENDED_ARG+JUMP_BACKWARD` ⇒ **回边错位重放**（签名c 家族，+1 纯伪影级）。
- _on_publish_after_trading_end 531/523：orig[491:499] `JUMP_FORWARD; LOAD_GLOBAL time; LOAD_ATTR sleep; LOAD_CONST 0.01; PRECALL; CALL…`(8条) 被换成 1 条 `NOP` ⇒ **分支体内 time.sleep(0.01)+跳转被空化**；另有 1 NOP 删除。
- _save_testds_to_csv 81/75 (7 hunks)：R67-diag6 三签名齐：(b) `IMPORT_NAME…;IMPORT_FROM THREAD_STATUS;POP_TOP`+`LOAD_CONST 0` 被删；(c) `JUMP_BACKWARD`@37→`JUMP_FORWARD`；多处 `LOAD_CONST None/RETURN_VALUE`↔`JUMP_FORWARD` 互换（含 a 家族，受 R47 禁令）。
- **更正**：get_TradeMode_trades 在当前 landed 下 nested_diff **无任何差异**（brief 说的"残余38"已不在）。

### order_api（dump/nd_order.txt，2/37 差异）
- future_order 115/107：删 `strategy_log.info('…'.format(…))` 8 条组@72；`'买入'`/`'卖出'` 三元常量@89-92 被 decomp 用 `NOP;LOAD_FAST order_.futures_direction.value.upper()` 顶替（**三元在 kwarg 槽被拆散重排放错位置**）；删 `LOAD_FAST order_;LOAD_ATTR amount;KW_NAMES;PRECALL;CALL`@104；尾部多插 `LOAD_CONST None;RETURN_VALUE`。
- option_order 94/85：同构——删 info 组@39、`.entrust_direction.value.upper();PRECALL;CALL;'BUY'` 侵入@44、删 `PRECALL;CALL;'OPEN';COMPARE_OP==;POP_JUMP_IF_FALSE;'开仓'`@63、删 `KW_NAMES;PRECALL;CALL`@85。
- 与 R67-diag5 结论一致：表达式语句/三元在 kwarg 调用点被空化或错位。

### flyAccount（dump/nd_fly.txt，5/24 差异）
- TradeAccount#10(root) 193/189、error_print、error_print_business：**纯 NOP 伪影**（官方已 OK），不是真缺陷。
- init_connection 45/44：`POP_JUMP_IF_FALSE`→`POP_JUMP_IF_TRUE+JUMP_FORWARD`（条件反转）+ `JUMP_FORWARD;LOAD_CONST str;STORE_FAST error_info;JUMP_FORWARD` 段整体被删、稍后重插（try 超时尾块重排放错）。
- **_do_request 471/480 (+9，官方 436/443 +7)**：21 hunks，但**高度规则**：×6 处
  `LOAD_FAST return_code / LOAD_CONST ('error_no','error_info') / BUILD_CONST_KEY_MAP`
  被写成 `LOAD_CONST 'error_no' / BUILD_MAP`，且每处前插 `POP_TOP; LOAD_CONST None`；另 415-419、245-249、269-273、360-364 同型；尾部 `SWAP`→`POP_TOP`、多插 `LOAD_CONST None`。⇒ 过冲不是"多发语句"而是**同一 return 字典被以不同构造形式重复降级发射**。


## Step 2 · 根因（本会话实测）
1. flyAccount._do_request 剩余 hunk（c3 之后 471/472，2 hunks）：
   - orig[457] \SWAP\ vs decomp[457] \POP_TOP\；decomp 多插 \LOAD_CONST None\@462。
   - 逐指令实测（见 dump）：handler 尾 = merge_block(2154 STORE_FAST result + 残值
     LOAD error_no/LOAD error_info/LOAD keys/BUILD_CONST_KEY_MAP/LOAD result/BUILD_TUPLE)
     → 唯一非异常后继 blk@2168=[SWAP] → blk@2170=[POP_EXCEPT, LOAD_CONST None,
     STORE_FAST e, DELETE_FAST e, RETURN_VALUE]。
   - 根因：\_generate_ternary\ 的 Pattern A2 只认「后继块末条 == RETURN_VALUE」；
     本形状后继块首条是 SWAP（异常表把 \except E as e:\ 退出链逐块切开），
     于是 A2 不命中 → 残值走 \_build_statements_from_instructions\ 发成 Expr，
     链上两块未记入 generated_blocks 被外层重放成 \POP_TOP; ...; return None\。
   - 根因实测证据：probe_c5walk 打印 merge@66 → normal_succs [80] → blk80 sig=[SWAP]
     succ=[82,102] exsucc=[102] → blk82 sig=5 条（POP_EXCEPT..RETURN_VALUE）。
2. 上一会话 c5 spec 的 A2-AS 臂体为何 inert：期望「六连逐指令各占一块」，
   实测是 **两块**（SWAP 单独一块 + 其余 5 条在下一块），\len(_sig)!=1\ 恒假 ⇒ 从不发射。
3. 次要 bug：该镜像里 Instruction 类**没有 \rgrepr\ 属性**（只有 opname/argval），
   用 \_r68_ops[3].argrepr\ 会 AttributeError → 被上层宽 except 吞掉、整个函数体退化成 \pass   （r68b5_a2as 首次实测 _do_request 436/**3**、h4/h5 decomp=3 即此）。改用 \rgval\ 名字比较。

## Step 3 · 合成复现
- synth/r68d6_handler_return2.py（h4/h5：except-as 内 ternary 赋值 + eturn dict, result\）
  landed **1/3**（h4 37/38、h5 41/42，jump=1 true=11）→ r68b5_a2as2 **3/3** ✔ 咬合
- synth/r68d6_handler_return.py（h1/h2/h3）landed 4/4 → r68b5_a2as2 4/4（不回归）
- synth/r68d6_tuple_ternary.py landed 3/4 → c3 4/4；r68d6_tuple_ternary2 landed 1/3 → c3 3/3

## Step 4 · 候选与 A/B（spec: specs/cand_r68b5_a2as.json，臂 r68b5_a2as2）
判据三要素已写进新臂体注释（识别条件=本 region merge_block 残值 + 唯一非异常后继链
SWAP/POP_EXCEPT/LOAD_CONST/STORE_FAST/DELETE_FAST/RETURN_VALUE 六连 exact-match 且
LOAD_CONST.argval is None、STORE/DELETE 名字相同、链块不属于 generated_blocks/region.blocks；
归约方式=残值归约为 Return、链块记入 generated_blocks 阻止重放；AST 映射=Return(reconstruct(残值))）。

五列实测（r68b5_a2as2）：
- targets：order_api **32/34**（unchanged）、risk_calculation **33/35**（unchanged）、
  flyAccount **22/23**（_do_request 436/**436** 完全 OK，landed 436/443；仅剩 init_connection 42/41）
- battery45：matched **179/200**（landed 174）、defect funcs **21**（26）、Σ|Δ| **92**（101）、worse=**0**、ERR=0
- canary sha：4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177 **全部逐字节不变**
- synth 见证：r68d6_handler_return2 landed 1/3 → 3/3（h4/h5 修好）；tuple_ternary landed 3/4→4/4（c3 编辑）

## Step 5 · 严格尺（sstrict67，名单 targets.txt，LF 归一后逐指令）
- arm 68b5_a2as2\（dump/strict_b5a2as2.json）：
  order_api 33/36（missing=0 extra=0）、__init__ 34/37、flyAccount **22/23**，
  STRICT TOTAL **ok=89 / functions=96 / defects=7**；flyAccount 唯一残余 init_connection
  [seq_len] orig=42 decomp=41。
- \landed\（dump/strict_land2.json）：order_api 33/36、__init__ 34/37、flyAccount 21/23
  （_do_request seq_len 436/445 + init_connection 42/41），STRICT TOTAL **ok=88 / 96 / defects=8**。
- 结论：a2as2 严格尺净 +1（defects 8→7），零 missing/extra，order_api 与 risk_calculation
  严格尺读数与 landed 完全一致（无回归）。

## Step 6 · init_connection 根因（只读实测）
- orig 逐指令（flyAccount.pyc co_name=init_connection，带 offset）：
  98 \POP_JUMP_FORWARD_IF_FALSE to 172\（条件 \error_no != SUCCESS\）；
  100-110 \if i < 3\；112-150 sleep；152 JUMP_FORWARD→160；
  154-156 \error_info='...超时...'\；158 JUMP_FORWARD→176（出环）；
  160-168 \i += 1\；170 JUMP_FORWARD→174（回边）；**172 JUMP_FORWARD→176（else 臂＝break）**；
  174 JUMP_BACKWARD→8；176 起 return 字典。
  ⇒ 源码形状 = \if error_no != SUCCESS: <inner if/else> else: break\（then=落出块 100、
  else=跳转目标 172），条件 opcode 为 **IF_FALSE**。
- 旧行为（probe_initif.py 实测）：\is_if_false=True ft=100 jb=172 exit=[172] brk=[172]\ →
  \_loop_build_if_with_exit_branches\ 先做「else 是出口且 then 不是 ⇒ 交换两臂 + 取反」，
  产出 \If(not (error_no != SUCCESS), body=[Break])\，**else 臂被 \_then_has_break → pass\ 丢弃**，
  块 100 由调用方在 if 之后单独发射。
  重编译结果 = \POP_JUMP_FORWARD_IF_TRUE + JUMP_FORWARD\（2 条）而非 orig 的
  \POP_JUMP_FORWARD_IF_FALSE\（1 条）+ 远端 172 处的 JUMP_FORWARD；且 inner else 块
  （LOAD_CONST/STORE_FAST 超时串）从 orig[30:32] 挪到 decomp[35:37]。
  nested_diff 读数（landed）：eplace orig[18:19]=IF_FALSE decomp[18:20]=IF_TRUE+JUMP_FORWARD  ＋ \delete orig[29:33]\ ＋ \insert decomp[35:37]\，orig 45 / decomp 44。
- 正确映射（本会话推导并复核）：条件跳转语义恒为
  「IF_FALSE：假时跳 _jump_block、真时落 _fall_through；IF_TRUE：真时跳 _jump_block、假时落 _fall_through」，
  且 \_expr\ 是被测试的栈顶值 C（3.11 把源码 not 折进极性），故统一规则
  **\_then_succ = _fall_through\、\_else_succ = _jump_block\、\_negate = not _is_if_false\**，
  并且 **else 臂是出口时也要用与 then 臂同一条出环归约发射 Break/Return**。
  init_connection（IF_FALSE, ft=体, jt=出口）⇒ \If(error_no != SUCCESS, body=[inner], orelse=[Break])  ⇒ 重编译回 \POP_JUMP_IF_FALSE → 172\ + 远端 JUMP_FORWARD，与 orig 同构。
- 爆炸半径控制：**保留**「then 臂含 Break 时不发射 else 臂」的既有收敛——
  实测该收敛只在 ft 本身是出口-Break 时触发，此时新旧两臂赋值+取反结果完全一致，
  故本改动只影响「ft=体、jt=出口」这一类（正是 init_connection 所属类）。


## Step 7 · 第 4 edit 候选（spec: specs/cand_r68b5_initc.json，臂 r68b5_initc3）

在 `cand_r68b5_a2as.json`（edits 0-2 = c3 + A2-AS，原样不动）之上追加第 4 条 edit：
`core/cfg/region_ast_generator.py::_loop_build_if_with_exit_branches` 整函数替换（anchor
在当前落地字节 `count==1`，h62 build 断言通过）。

判据三要素（已写进新臂体注释，缺一不可）：
- 识别条件：只读本调用点已算好的形参 `_is_if_false/_fall_through/_jump_block/_exit_succs`
  与本块自身身份 `get_entry_region_for_block(b).entry is b`；条件跳转语义恒为
  「IF_FALSE 假跳/真落；IF_TRUE 真跳/假落」，`_expr` 是被测试栈顶值 C  =>  
  **then=fall_through、else=jump_block、negate=not is_if_false**。
- 归约方式：(1) 两臂共用 `_r68_branch`；(2) 非出口臂若本身是 IfRegion entry -> 改走
  `_generate_block_statements(b)` 的既有条件分派发射该 if，再 (a) 按臂入口块角色
  `BlockRole.BREAK/PURE_BREAK` 补 `Break`（条件 if 的无条件前跳被当跳转 opcode 过滤、
  不产生语句），(b) 逐个补发该区域尚未认领的块（`i += 1` 在内层 if 之后的兄弟位置），
  (c) 认领 `region.blocks`；分派没产出 If 节点时回退既有 `_generate_region`；
  (3) **空 then 臂折叠**：臂语句列表恰为 `[{'type':'Pass'}]` 且 else 臂非空时，
  按 `if C: <空> else: S` == `if not C: S` 把 else 臂搬进 then 臂并取反条件
  （否则空 then 臂要多插一条 JUMP_FORWARD 跳过 else）。
- AST 映射：`If(test=_negate_expr(_expr) if _negate else _expr, body=then, orelse=else)`；
  折叠时 `If(test=_expr if _negate else _negate_expr(_expr), body=else)`，省略 orelse。

### Step 7.1 · 关键中间读数（为什么必须补发剩余块 + 补 Break）
- 只做极性修正（臂 `r68b5_initc2`）：flyAccount **23/23** 已达成，但
  test_repros/round67_diag4::c3_cont_cond 由 landed 的 `if not g(): break`
  变成 `if g(): pass else: break` => 多 1 条 JUMP_FORWARD，Sigma|delta| 101->**92**
  （该函数 0->1）。
- 追加空 then 臂折叠（臂 `r68b5_initc3`）：该函数回到与 landed **逐字节相同**，
  Sigma|delta| 101->**91**，且 changed 产品只剩 4 个、**全部是 landed 有缺陷 -> 本臂无缺陷**。
- 复核手段：`python -X utf8 nested_diff.py "<pyc>" "<OK.py>" <name-filter>`、
  `blast67.py landed <arm> dump/repro65_landed.jsonl dump/repro65_<arm>.jsonl`。

### Step 7.2 · 交付候选五列实测（臂 `r68b5_initc3`）

| 列 | landed | r68b5_a2as2 | **r68b5_initc3（本候选）** |
|---|---|---|---|
| targets | 32/34、33/35、21/23 | 32/34、33/35、22/23 | **32/34、33/35、23/23**（flyAccount 全清；`h62 ab` SAME=2 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0，files fully matched 0->1） |
| battery45 | 174/200、defects 26、SigmaAbs 101、worse=0 | 179/200、21、92、worse=0 | **180/200、defects 20、SigmaAbs 91、worse=0、ERR=0**（`blast67`：matched 174->180，fully matched files 30->34，changed=4 **全为改进**：r63b5_w1、r67d3_lostreturn、r67d3_return_sink、r67d3_return_tern） |
| canary 4 sha | 4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177 | 同左 | **同左，逐字节不变**（dump/b5initc3_canary.jsonl，143/143、10/10、26/26、25/25 全 matched） |
| synth 见证 | handler_return 4/4；handler_return2 **1/3**；tuple_ternary **3/4**；tuple_ternary2 **1/3** | handler_return2 3/3、tuple_ternary 4/4、tuple_ternary2 3/3 | **4/4、3/3、4/4、3/3 全通过**（landed 失败的 3 件全部转正，咬合；dump/landed_synth_b5all.jsonl vs dump/b5initc3_synth_b5all.jsonl） |
| 严格尺 | 88/96 defects 8 | 89/96 defects 7 | **90/96 defects 6**（order_api 33/36、__init__ 34/37、flyAccount **23/23**，missing=0 extra=0；dump/strict_b5initc3.json） |

ERR 计数：targets/canary/synth/battery 四组 dump 共 56 条记录，errish=0。

### Step 7.3 · 反编译产物核对（flyAccount::init_connection）
本臂产物与 orig 源码形状逐字节同构：
`if error_no != SUCCESS: [if i<3: sleep else: error_info=...; break] + i += 1  else: break`；
nested_diff `orig=45 decomp=45 hunks=0`（a2as2 时为 orig=45 decomp=44 hunks=2）。

## Step 8 · 逐靶 VERDICT

| 靶 | landed | 本候选 | gap | VERDICT |
|---|---|---|---|---|
| fly/simtradding/flyAccount.pyc | 21/23 | **23/23**（严格尺 23/23、nested_diff hunks=0） | -2 -> 0 | **候选：`D:/Temp/opencode/r68gate/diag6/specs/cand_r68b5_initc.json`（臂 `r68b5_initc3`）** |
| IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc | 33/35 | 33/35（逐字节同 landed，`h62 ab` SAME） | 2 -> 2 | **候选：NONE**（本候选不触碰该靶；残余 `_on_publish_after_trading_end` 486/481、`_save_testds_to_csv` 71/68（h62 官方读数；严格尺同列为 488/481、75/68）属表达式/导出结构族，本会话未在白名单三文件内定位到可落地三要素判据；排除读数：改前改后 33/35、严格尺 34/37 完全一致） |
| IQEngine/plugins/plugin_fly_data/fly_api/order_api.pyc | 32/34 | 32/34（逐字节同 landed，`h62 ab` SAME） | 2 -> 2 | **候选：NONE**（残余 `future_order` 101/92、`option_order` 83/73 为 kwarg 槽内三元/表达式语句错位族，未在白名单三文件内找到可落地判据；排除读数：改前改后 32/34、严格尺 33/36 完全一致） |

对 BRIEF 的更正：
1. BRIEF 的 `get_TradeMode_trades` 差异本 dir 复测已不存在（TradeAccount#10 只剩 NOP 伪影）。
2. 早先 `r68b5_a2as` 臂 `_do_request 436/3` 的读数是镜像 Instruction 类无 `argrepr`、
   AttributeError 被宽 except 吞掉导致函数体退化 `pass` 的假读数，改用 `argval` 后正常。
3. 本轮在 ADR-1 下执行：判据 3 按缺陷类型分列（缺语句/过冲类要 SigmaAbs 净减少），
   本候选 101->91 满足净减少，且 changed 产品零回归。

中心最该先验的一条：`blast67 landed r68b5_initc3 dump/repro65_landed.jsonl dump/repro65_r68b5_initc3.jsonl`
—— 期望 `official instruction-gap sum 101 -> 91`、`changed=4` 且 4 个全为 landed 侧有缺陷。
