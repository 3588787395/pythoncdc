# FIX_R21-45 — clock_worker 损失 (B)「已声明汇合块被发在函数尾」闭合（+ 同单元新发现的假 try-else）

工单：R21-45（本会话编号 **R21-44 已被用过两次**：r71a 用于 broker `_sync_worker` 复合 while、
r73a 用于 clock_worker or-tail，故本工单取 **R21-45**；假臂那半件记作 **[R21-45b]**，同一工单、
可单独消融）。
目标单元：`<module>.RealtimeEventSource.clock_worker`
（`site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc`，13 单元，面板 12/13）
镜像：`D:/Temp/r74`（仓库 `D:/admin/.../pythoncdc-main` 全程只读，未写 `core/`、`scripts/`、`site-packages/`）

## 0. 镜像与前提校验（规则 9：逐条重测，不采信简报）

```
core/cfg/region_ast_generator.py  sha256[:16] = 11324f276cce6d5b   （门禁 38 认证字节，MATCH）
core/cfg/region_analyzer.py       sha256[:16] = f7d849e974904492   （MATCH）
```

| 字节 | clock_worker `orig/prod` | delta | hunks | landings | 判定 |
|---|---|---|---|---|---|
| landed `11324f276cce6d5b`（重测） | 1424/1311 | −113 | 7 | 18 | `units=12/13`，`***…clock_worker: Different control flow` |
| anchored `cf5868e68208adf6`（简报给的 BASE，重测） | 1424/1418 | −6 | 5 | 12 | `units=12/13`，同一单元 |

简报的 −113/7/18 与 −6/5/12 **全部复现**；产物 sha16 也复现面板表（landed `174e1174f28a669c`、
anchored `585d39d826bd000f`），故读数可比。窗口全部用 `work/allwin.py`（= `allwin_r63.py`，无
小窗过滤）+ `work/unit_diff.py --all` 双轨读，小窗（1 条跳转）不会被藏。

**简报里「@6690 的 17 指令 if 体要不要管」这一条有答案了：anchored 基已经恢复它。**
landed 的 hunk #2 是 `delete orig @6690..@6782 (17)`，anchored 的 hunk #2 只剩
`delete orig @6778..@6782 (3)` ⇒ `if holiday_not_do_before == '0': self.event_queue.put(...)`
已在原位（产品第 244-245 行），(B) 只剩那 3 条赋值的**位置**。

anchored 基的 5 窗（重测，逐条）：
```
#1 insert  prod @6496  JUMP_FORWARD            ← [R21-44] 家族的伪臂尾跳转（站点 @6496）
#2 delete  orig @6778..@6782 (3)  self.before_trading_date = now_date   ← (B)
#3 insert  prod @7242  JUMP_FORWARD            ← 站点 @7164 的伪臂尾跳转（被 ⑧ 拒动）
#4 delete  orig @7270..@7308 (6)  system_log.debug('获取重登信号量')     ← (A)
#5 replace orig @9210..@9212 (2) → prod @9170..@9172 (3)                ← #2 的内容发在函数尾
```

## 1. (B) 的读数：结构事实

区域数据（`work/census_regions.py`，只读探针，无改判定）：
```
IfRegion  condition_block=@6690..@6700(4) then=[6702] else=[] merge=@6778..@6782(3)
IfRegion  condition_block=@6548..@6578(6) then=[6580,6582,6652,6690] else=[] merge=@6792..@6844(8)
@6778  win=@6778..@6782(3)  succ=[9218(异常边), 6792]  preds=[6690(假出口), 6702(臂落点)]
       last=STORE_ATTR before_trading_date
```
即：@6778 是 `if holiday_not_do_before == '0': …` 之后、@6792（`time.sleep(FPS); continue`）之前
的**顺序语句**，两条前驱一条来自条件假出口、一条来自臂尾 —— 真汇合（arity=2）。它在源码顺序上
必然紧跟 @6690 那条 if。发射端把它发到了函数尾（anchored 产品第 313 行，编译落点 @9170），
内容对、位置差 ~1000 条偏移。

## 2. 修 (B) 的判据 [R21-45]（`_if_generate_normal` post-if 发射决策，纯插入 78→89 行）

承 `rounds/round38/CANDIDATE_r67a_mergeblock_BANKED_reclaimed_WIP.py`（`17b73582864fbba0`，
基是门禁 37 的 `20fa73b4e8231f0f`，**从未在门禁 38 字节上测过**）。先移植再测：
```
python -X utf8 work/merge_hunks.py --base D:/Temp/r67/landed_region_ast_generator.py \
  --candidate rounds/round38/CANDIDATE_r67a_mergeblock_BANKED_reclaimed_WIP.py \
  --current work/base_anchored_cf5868e68208adf6.py --out work/r67a_on_anchored.py
# applied 1 hunks (+78 行)；工具的 "8 residual not explained" 未触发判定，我另行独立验证忠实性：
# diff(anchored -> merged) = 恰好一条纯插入 insert anchored[23335..23335] merged[23335..23413] +78
```
之后我把这段文本重编成自己的整文件重建器（`build_cand_r74a_r2145.py`，标识符 `_r38b_*`→`_r2145_*`、
加探针、注释改本战役房式），**产物逐字节相同**（`4182f600fddfda77`）⇒ 重编无夹带。

判据四条（区域数据 / opcode 类别 / 前驱后继结构；无函数名、无绝对偏移、无计数阈值、无跨层启发）：
① merge 块不在本区域 then/else 臂内；② merge 块的**每个**前驱都属于 `region.blocks` 且不止一条；
③ merge 块剥噪后的末条是语句终止符（`STORE_*`/`POP_TOP`/…），且不是 `JUMP*`/`POP_JUMP*`/`RETURN*`/`RAISE*`
（注释里的反例：末条为 `SWAP` 时放行会凭空多发一条 `return None` —— 本单元实测踩过）；
④ 唯一归属：无别的区域把它宣为 condition_block/header_block/entry、也不是别的区域的 then/else 臂成员，
且不被「嵌套在本 if 之内」的 Try/With/Match 含住（用包含判祖先，不依赖 `region.parent` 链）。
不成立 ⇒ 不改 `_should_emit`，零副作用。**注**：④b 与祖先判定要扫 `region_analyzer.regions` 的声明字段，
读的是「这块归谁发」的身份事实（原则 2），不是别的区域的取值启发。

## 3. (B) 实测读数：hunk 关掉，但带出一个新洞

| 字节 | orig/prod | delta | hunks | landings | 判定 |
|---|---|---|---|---|---|
| anchored 基 | 1424/1418 | −6 | 5 | 12 | 12/13 |
| **+ [R21-45]（半件 A 独走）** | 1424/1421 | **−3** | **4** | **9** | `status=failure units=12/13`，同一单元 |

#2（@6778 三条赋值缺失）与 #5（函数尾多发）**同时消失**：产品第 245 行
`self.before_trading_date = now_date` 已在 @6690 的 if 之后、@6792 的 `time.sleep(FPS)` 之前。
**但冒出新窗 #2'：`replace orig @6652 (JUMP_FORWARD,1) → prod LOAD_CONST None; RETURN_VALUE (2)`** ——
这是 anchored 基里早已存在、被错位发射掩盖的第二个缺陷（见 §4）。

## 4. [R21-45b]：假 `try/except/else`（本会话新定位，独立半件）

区域数据：`TryExceptRegion entry=@6582 try_blocks=[6582] else_blocks=[6652] handlers=[[6672,6678]]`，
而 `@6652 = [JUMP_FORWARD 6690]`、`@6678 = [POP_EXCEPT, JUMP_FORWARD 6690]` —— try 体的正常完成边
与 handler 出口**落同一块 @6690**（CPython 3.11 无 else 的 try/except 布局）。发射端
`_generate_try` 的 orelse 循环按 `BlockRole.PURE_BREAK` 给它发了 `else: break`（产品 241-242 行），
编译结果是在 try 成功后**跳出整个 while**（在 anchored 基里那条 break 跳到的正是错位的 @6778 尾块，
所以对齐器把它当成一条普通跳转，窗口被藏住；(B) 修好后它裸露出来）。

判据（本区域 else_blocks + except_handlers + 跳转目标同一性；不读本单元以外的东西）：
① 该 else 块剥噪后恰剩一条无条件前向跳转，目标 T 是真实块；② 本区域至少一个 handler 臂，且**每个**臂末块
剥噪后的收尾也跳向同一个 T；③ 否则原样落回既有路径。命中 ⇒ 视作空臂：与既有 BREAK 分支同样登记
`generated_blocks`（唯一归属），不产出语句。

| 字节 | orig/prod | delta | hunks | landings | 判定 |
|---|---|---|---|---|---|
| anchored + [R21-45b]（半件 B 独走） | 1424/1418 | −6 | 5 | 11 | 12/13（本单元窗口数不变，但产品字节变了 `0a900f18cdbd9550`） |
| anchored + A + B（r74c） | 1424/1420 | −4 | **3** | 9 | 12/13 |

⇒ B 半件**必须**与 A 同乘才显效（单独走时它只改掉跳转落点，不减少窗口），A 半件单独走时把 B 的缺陷暴露成窗口。
`delta` 计数 −3→−4 变差而窗口 4→3 变简，按本战役惯例以「窗口 + 是否翻正」论，不以 `abs(delta)` 论。

## 5. 数派（规则 2，`CENSUS_r2145_counts.txt`，20 个面板文件）

* **[R21-45] A**：`R2145EVAL` **1477** 次求值，`R2145FIRE` **5** 次 —— 文件 4 handlers(@452)、
  6 trade_info_utils(@236,@1276)、9 strategy(@1072)、13 realtime(@6778，目标)。
  拒绝分布：shape 1433、other-arm-member 37、declared-head 2。
  4 次非目标 fire 的产物**逐字节不变**（共享尾被 `if _should_emit:` 之后的 W23 跨层唯一归属再压一次，
  或该块语句本已由臂通道发出）⇒ 净爆炸半径 1 个文件。
* **[R21-45b] B**：`R2145bEVAL` **106** 次求值，`R2145bFIRE` **77** 次，覆盖 16/20 个文件
  （quotation 4、quote 7、klinedata 6、handlers 2、wizard 6、trade_info_utils 10、real_quote 8、
  strategy 2、broker 15、realtime 2、risk_calculation 2、三个 arg_checker 各 3、三个 profiler_func 2/1/2）。
  拒绝：handler-exit-not-shared 23、not-bare-jump 6。
  然而 B 独走的产物只有 1 个文件变化（`base -> r74e changed files = 1`）：其余 75 次 fire 落点在
  「块已被 generated/被嵌套区域认领/本来不走 BREAK 分支」的路径上，输出不变。
* 探针惯性（已证）：探针构建 + `R2145_CENSUS=1` 与无探针构建在 **20/20** 个面板产物上 `cmp` 全等；
  另：早期定位用的 stderr-only orphan 探针（`work/probe_orphan.py`）同样 20/20 不变。
* 顺带证伪一个假设：@6778 **不是**孤儿块释放路径（`region_ast_generator.py:1893-1951`
  `_orphaned_blocks`）发的 —— 探针在该单元内 `R74ORPHAN/R74BASIC` 计数为 0；真正的挪动发生在
  `_if_generate_normal` 的 post-if 决策被 `_mb_in_nested_structural`（只沿 `region.parent` 认祖先）跳过后。
  r67a 注释里「被 `_loop_postprocess` 残余清扫挪到循环体之后」这句话我**没有独立证实**，只是文本继承。

## 6. 2×2 半件表（规则 4）+ 与已入库 [R21-44] 的组合

| 组合 | delta | hunks | landings | 判定行 |
|---|---|---|---|---|
| anchored（基） | −6 | 5 | 12 | 12/13 |
| A 独走 `5ade1c37c0c9bb8c` | −3 | 4 | 9 | 12/13 |
| B 独走 `4e1a853a957a3fd8` | −6 | 5 | 11 | 12/13 |
| A+B `f51f9de14d216cda`（**本工单交付候选**） | −4 | 3 | 9 | 12/13 |
| A+[R21-44]（r73 的 `83a430f2700ae3a4` 移植） | −4 | 3 | 6 | 12/13 |
| A+B+[R21-44]（r74d 三件） | −5 | 2 | 6 | 12/13 |

## 7. 面板（`PANEL_20files_before_after.txt`）

20 个文件逐一 base / r74c / r74d 三列 sha16 + `units=x/y`：**changed files = 1**
（`realtime_event_source.pyc`，22322 → 21820 字节）；单元读数两列全等
`153/153, 92/92, 64/64, 30/30, 58/58, 41/41, 28/28, 45/45, 27/27, 37/37, 126/128, 17/17, 12/13,
43/43, 49/49, 39/39, 43/43, 17/17, 15/15, 18/18`，面板合计 954/966 不变。
broker 126/128 的失败项仍只有 `_process_order`、`_sync_worker` ⇒ 四个 canary
（`ipo_stocks_order`、`_process_cancel_order`、`_trade_status_handle`、`etf_purchase_redemption`）
与 `quote.pyc 92/92`、`quotation.pyc 153/153` 全部保持绿色（A、B、A+B、三件四种字节下都一样）。
**未翻正**：fires 5/77 而 FLIPS=0 ⇒ 按规则 3 只能作为合取件入库，不安装。

判定行（r74c，交付候选）：
```
[single] status=failure units=12/13 success_rate=92.31%
Failure: ***<module>.RealtimeEventSource.clock_worker: Different control flow
```

## 8. 还开着的机制 = (A)，以及它为什么必须排在 [R21-44] 前面

三件组合（§6 最后一行）只剩 2 窗，都在 @7164 站点：
```
#1 insert prod @7248 JUMP_FORWARD                     ← 臂尾伪跳转
#2 delete orig @7270..@7308 (6) system_log.debug('获取重登信号量')
```
**对简报 §A 的一处更正（实测 dis，`work/dis_unit.py orig … 7150 7400`）**：@7270 的前 6 条
`LOAD_GLOBAL(NULL+system_log) LOAD_ATTR debug LOAD_CONST('获取重登信号量') PRECALL CALL POP_TOP`
以 **POP_TOP 收尾 = 一条语句**，不可能是 `and` 的操作数。所以 @7248/@7270 **不是**一个
`now_date != first_run_date and acquire(...) is False` 的 BoolOp（r66a §2 记的融合测试形状在源码层
不可表达），而是两条嵌套 if 的正常流：
```
if (A and B) or C:                       # @7164 站点，[R21-44] 的 flat 形状（③④⑤ 都成立）
    if now_date != self.first_run_date:          # @7248 假出口=真出口后续 @7492；无人认领
        system_log.debug('获取重登信号量')          # @7270 前缀语句（现在被噪声过滤器丢掉）
        if login_semaphore.acquire(timeout=LOGIN_TIMEOUT * 60) is False:   # @7270 尾测试
            system_log.error('获取重登信号量超时，系统退出'); …; return None   # @7372/@7488
    <@7492 顺序语句>                        # 两个假出口线程到同一汇合点
```
决定性实验（不是散文）：在三件字节上把 [R21-44] 的合取⑧改成放行（`work/DIAG_r74d_relax8.py`）：
```
len orig=1424 prod=1150 delta=-274 hunks=5   （@7582 臂 54 条、@7960..@8276 臂 55 条、
                                               @8282..@9192 160 条整臂被删）
```
⇒ ⑧ 是对的（保守性成立），**但 (A) 不修就永远拿不到 @7164/@7582**：臂入口 @7248 必须先「可派发」。
下一步的两条出路（都是声明级，与本工单同形）：
1. 分析端为 @7248 声明 `IfRegion(condition_block=@7248, then=[@7270], else=[], merge=@7492)`
   —— 它现在只是 `inline_boolop_chains[id(@7248)] = {'blocks': [7248,7270], 'op': None}` 的成员；
2. 或在 `_if_generate_elif_chain` 的臂体装配里拒掉这条 op=None 的折叠（r66a 的
   `07ff9a163b07140a` 已经是**只拒绝**的守卫，实测 delta −6→0 但把 6 条语句发在链尾 = 位置问题），
   改发「前缀语句 + 嵌套 If」。两者闭合后 ⑧ 自动放行，flat 形状由 [R21-44] 接管。

## 9. 交付物（`D:/Temp/r74/DELIVER/`）

`FIX_R21-45_clock_worker_merge_placement.md`（本文）
`build_cand_r74a_r2145.py`（整文件字节级重建器：`--halves a|b|a,b`、`--no-probe`、`--base`、`--out`；
BOM + 全 CRLF、锚点唯一断言、`py_compile`）
`CANDIDATE_r74a_r2145_onlyA_5ade1c37c0c9bb8c.py`、`CANDIDATE_r74e_r2145_onlyB_4e1a853a957a3fd8.py`
`CANDIDATE_r74c_r2145_AB_f51f9de14d216cda.py`（推荐候选）、`CANDIDATE_r74c_r2145_AB_probe_a7b26cceb9c6cfa8.py`（同判据 + 探针）
`CANDIDATE_r74d_AB_plus_R2144_3e7af79a63b5d0cf.py`、`DIAG_r74d_relax_conjunct8.py`（⑧ 放行诊断）
`PRODUCT_base_anchored_/PRODUCT_r74a_/PRODUCT_r74e_/PRODUCT_r74c_/PRODUCT_r74d_/PRODUCT_diag_relax8_realtime_event_sourceOK.py`
`ALLWIN_r74c.txt`、`ALLWIN_r74d.txt`、`JUDGE_r74c.txt`、`JUDGE_r74d.txt`
`CENSUS_r2145_counts.txt`、`CENSUS_probe_r74c_01..20.txt`、`CENSUS_r2145A_01..20.txt`
`PANEL_20files_before_after.txt`、`PANEL_log_base_1_10.txt`、`PANEL_log_base_11_20.txt`、
`PANEL_log_r74c_1_10.txt`、`PANEL_log_r74c_11_20.txt`、`merge_r67a_to_anchored.txt`、`probe_orphan.py`
`BASE_anchored_P1P2_on_g38_cf5868e68208adf6.py`（= 我的 BASE 副本，builder 的默认 `--base` 取
`work/base_anchored_cf5868e68208adf6.py`，与本副本逐字节相同）、
`landed_g38_region_ast_generator_11324f276cce6d5b.py`（门禁 38 字节的比对副本）

## 10. 仓库状态

仓库 `core/`、`scripts/`、`site-packages/`、`rounds/` 未写；所有产物落 `D:/Temp/r74/out|work|DELIVER`。
镜像收尾恢复门禁 38 字节：`core/cfg/region_ast_generator.py = 11324f276cce6d5b`、
`core/cfg/region_analyzer.py = f7d849e974904492`（安装前后各 `cmp` 一次）。
