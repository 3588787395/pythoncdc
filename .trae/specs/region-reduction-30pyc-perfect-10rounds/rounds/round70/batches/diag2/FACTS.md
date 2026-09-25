# Round 70 · diag2 · FACTS（靶支 fly/data/quote.pyc）

臂名前缀 `r70diag2`。仓库只读；一切产物在 `D:/Temp/opencode/r70gate/diag2`。
镜像根 = `D:/Temp/opencode/r70gate/center`（h62.py 的 ROOT），臂目录 `mirr_r70diag2*`、
产物 `build_r70diag2*`。

## Step 0 · baseline replay（landed = R69 HEAD 5647e97b）

### 官方尺 targets（`h62.py run --arm=landed --list=targets.txt --out=dump/landed.jsonl`）
```
landed quote.pyc  72/81
  build_current_period_df 115→108 (jumpdiff 5, true 12)
  check_frequency          121→120 (1, 21)
  get_individual_data      312→311 (1, 156)
  get_price                230→232 (0, 172)
  get_real_from_zeromq     703→700 (1, 551)
  load_bars_from_hundsun   477→483 (0, 410)
  load_get_price           171→171 (0, 1)
  run_individual_transform 362→321 (2, 263)
  run_tick_socket          306→307 (2, 228)
```
Σ|Δ| = 7+1+1+2+3+6+0+41+1 = **62**（与 targets.md「R69 后 Σ|Δ| 62」一致）；
gap = 81−72 = **9** ✓；缺陷函数 **9** ✓。
注意官方尺不含 `change_his_to_backward` / `change_his_to_forward` / `check_industry_code` /
`run_tick_transform` 这 4 支（官方跳转容差），严格尺才列 → 官方 9 缺陷 ≠ 严格 13 缺陷。

### 官方尺 canary（`--list=canary.txt --out=dump/landed_canary.jsonl`）
| pyc | sha | 读数 |
|---|---|---|
| fly/data/quotation | `4d41187e356544e0` | 143/143 |
| fly/common/market_time | `af77224b34b203c4` | 10/10 |
| IQCommon/util/datetime_func | `e711b8ea86d49a15` | 26/26 |
| IQData/utils/datetime_func | `9d09af09249da177` | 25/25 |
四 sha 与采纳合同**逐字节相同** ✓。

### 45 项电池（round63..67 + pinned，`closeout69.py battery landed` 清单去掉 round68_/round69_）
- 清单：`battery45.txt`（45 项，由 center/dump/reprolist65.txt 过滤得到）
- landed 读数：**182/200**、缺陷函数 18、worse=0、ERR=0（与 targets.md 一致 ✓）

### 82 项扩展电池（`closeout69.py battery landed`，本轮实测）
- **318/356、缺陷 37、worse-than-landed=0、errors=0**（与 targets.md 一致 ✓）

### 严格尺（`python -X utf8 sstrict67.py build_landed targets.txt dump/strict_landed.json`）
- `quote.pyc strict 76/89 missing=0 extra=0`，缺陷 **13**，逐条与 targets.md 表**逐字相同** ✓：
  build_current_period_df [seq_len] 118→109 / change_his_to_backward [target_diff] #213 /
  change_his_to_forward [target_diff] #241 / check_frequency [seq_len] 123→124 /
  check_industry_code [seq_diff] #159 / get_individual_data [seq_len] 314→313 /
  get_price [seq_len] 230→232 / get_real_from_zeromq [seq_len] 703→700 /
  load_bars_from_hundsun [seq_len] 477→483 / load_get_price [seq_diff] #53 /
  run_individual_transform [seq_len] 364→321 / run_tick_socket [seq_len] 309→310 /
  run_tick_transform [target_diff] #56

**Step 0 结论：与 BRIEF/targets.md 预读数逐字段相同，无更正。**

## Step 1 · hunk tables（nested_diff.py，全路径配对，92 个 code object 中 15 个有差异）

| code object | orig/decomp | 归一化 hunks | 判定 |
|---|---|---|---|
| /Quote#22 | 264/257 | 1 delete(NOP×7) | 伪影 |
| .../build_future_fill_time#25 | 489/489 | 1 replace(frozenset repr 顺序) | 伪影 |
| .../build_current_period_df#28 | 124/113 | 2（EXTENDED_ARG 伪影 + 真缺陷：`tempdict['is_open']=[...]`+`tmp=pandas.DataFrame(...)`+`return tmp` 整段丢失） | 真缺陷 seq_len |
| .../load_bars_from_hundsun#29 | 526/533 | 1 insert(`os.path.exists(DumploadDailyFile)` 被重复发射成裸表达式语句，7 条) | 真缺陷 seq_len +6 |
| .../load_get_price#30 | 185/185 | 1 replace(POP_JUMP_FORWARD_IF_FALSE → POP_TOP) | 真缺陷 seq_diff #53（同长） |
| .../change_his_to_forward#31 | 572/573 | 3（EXTENDED_ARG/NOP 伪影）；严格 target_diff #241 不在归一化里 | 金丝雀同名残余族（死胡同） |
| .../get_price#40 | 256/258 | 1 replace(POP_JUMP_FORWARD_IF_NONE → LOAD_CONST None+IS_OP+POP_TOP) | 真缺陷 seq_len +2 |
| .../check_stocks#59 | 71/70 | 1 delete(NOP) | 伪影 |
| .../check_industry_code#61 | 196/196 | 1 replace(IF_TRUE → IF_FALSE 极性反) | 真缺陷 seq_diff #159 |
| .../check_frequency#63 | 132/133 | 2（`return None` 早返回被挪到函数尾 + 末尾多 1 条） | 真缺陷 seq_len +1 |
| .../get_real_from_zeromq#66 | 793/791 | 7（EXTENDED_ARG 伪影 + 30 条 guard 块整体后移 + UNPACK_SEQUENCE/STORE_FAST exc_obj/exc_tb 丢失 + LOAD_FAST→LOAD_GLOBAL exc_tb ×2） | 真缺陷 seq_len −3 |
| .../run_individual_transform#72 | 412/359 | 11（try/except/if/else 结构整体塌陷，多段语句丢失/搬移，主体丢 43 条） | 真缺陷 seq_len −43（最大项） |
| .../run_tick_transform#73 | 326/327 | 1 insert(EXTENDED_ARG 伪影)；严格 target_diff #56 | 伪影+严格缺陷 |
| .../run_tick_socket#74 | 347/348 | 4（EXTENDED_ARG 伪影 ×2 + 24 条 warning guard 块整体后移） | 真缺陷 seq_len +1 + 纯位移 |
| .../get_individual_data#81 | 354/354 | 4（EXTENDED_ARG 伪影 + 28 条 flag==1 guard 块整体后移 + 末尾 RETURN 位移） | 纯位移（同长）+1 |
| TOTAL | | 15/92 | |

官方尺 Σ\|Δ\| 分解（=62）：run_individual_transform 41、build_current_period_df 7、
load_bars_from_hundsun 6、get_real_from_zeromq 3、get_price 2、check_frequency 1、
get_individual_data 1、run_tick_socket 1、load_get_price 0。

## Step 2 · 根因（regdump.py / probe_tern.py 实测，非读码推断）

### 根因 R70-d2-T1：三元归并块承载后继 if 的例外在「函数含循环」时不可达
实测 `probe_tern.py quote.pyc get_price`：
```
TernaryRegion entry=0 merge=144 blocks=[0,112,142,144] merge_ctx=fstring container=call
blk@144 last=POP_JUMP_FORWARD_IF_NONE n=42      ← `if fields is not None:` 的条件
块 144 = f-string 三元的 merge 块，一直延伸到第一条真 if 的条件跳转
contains_block(144) = False          ← TernaryRegion 不把 merge_block 算进 contains_block
block_to_region[144] = TernaryRegion
_ternary_merge_hosts_next_if(144, tr) = True   ← R13c 例外判据本身成立
```
调用顺序（`_identify_conditional_regions` L16043 起）：
1. `_should_skip_block_for_if_region(block, block_region, loop_regions, last_instr)` **先跑**；
   进入 `elif block_region is not None: if not block_region.contains_block(block):`
   → 非 BoolOpRegion → **`return True`（直接跳过）**。
   该函数开头 `if not loop_regions: return False` ⇒ **函数里没有循环时这条早退根本不触发**，
   R13c 例外（L16188 `elif self._ternary_merge_hosts_next_if(...)`）才可达。
2. 因此凡「f-string 三元 merge 块延伸到第一条 if 条件 + 函数含 LoopRegion」的函数，
   该 if 的 IfRegion 永远建不起来：块 144 被当纯语句发射，条件跳转被换成 `POP_TOP`，
   条件变成裸表达式语句，if 体被拍平到函数层。

实测命中（quote.pyc 三支，均含循环 ⇒ 全部走死分支）：
- `get_price`：`fields is not None` 裸语句，`if fields is not None:` 体被拍平 ⇒ 官方 230→232（+2）
- `load_get_price`：`len(panel.major_axis) != 0` 裸语句，`if ... != 0:` 的 if/elif 体被拍平 ⇒ 171/171 但严格 seq_diff #53
- `load_bars_from_hundsun`：`os.path.exists(DumploadDailyFile)` 被重复发射 ⇒ 477→483（+6）

### 根因 R70-d2-T2：`_value_merge_hosts_next_if` 的 `_tail_ops` 缺 `PRECALL`（3.11 调用前导）
`_value_merge_hosts_next_if`（L26750）要求消费者之后到块末跳转之前
「是一段完整的操作数构造指令」，白名单 `_tail_ops` 含 `CALL`/`LOAD_METHOD`/`LOAD_ATTR`
但**不含 `PRECALL`**（CPython 3.11 每个 CALL 前必有 PRECALL，栈效应为 0）。
⇒ `load_bars_from_hundsun` 块 144 的尾部是 `...PRECALL; CALL`，`_ternary_merge_hosts_next_if`
返回 False，即使 T1 打通也修不到该支。实测见 Step 4 的 A/B 分列。

## Step 3 · 合成复现（`synth/`，硬规则）
- `synth/witness_r70.py` → `synth/witness_r70.pyc`（py 3.11.7 `py_compile`），名单 `synth/synth70.txt`。
- 形状：函数含 `for` 循环 + f-string 内 `len(...) if ... else 1` 三元 + 其后 `candle_period=None` /
  `check_datetime`×1 / `check_frequency` 语句前缀 + `if fields is not None: return`。
- 读数：
  ```
  landed         witness_r70.pyc  4/5  [['witness', 53, 53, 0, 3]]      ← 失败签名 true_diff=3
  r70diag2af     witness_r70.pyc  5/5  []
  r70diag2h      witness_r70.pyc  5/5  []
  ```
- 失败签名与 quote.pyc `get_price` 同源：三元把归并块尾（语句前缀）当 `post_consumer_extra_stmts`
  发射一遍，下游 IfRegion 再发一遍 ⇒ 前缀双发射（或落地前 if 被拍平 ⇒ +2）。
- **咬合 ✓（landed 失败、候选臂通过）。**

## Step 4 · 候选与 A/B
### 根因 R70-d2-T3（本轮补上，实测非读码）
`_try_wrap_fstring_pending_call`（generator L42368 定义，赋值点 **L42426**）把 f-string 归并块中
`CALL`→`POP_TOP` 消费者**之后**的全部指令折成 `region.post_consumer_extra_stmts`；当该归并块同时是
后继 IfRegion 的 entry（R13c 成立）时，尾段（`candle_period=None`/`check_*`/条件比较）被发两遍。
- 实测（`dbg1.py`/`dbg5.py` 插栈，`R70DBG=1`）：`_generate_ternary(get_price)` 返回 6 条
  `['Expr'(fstring), 'Assign'(candle_period), 'Expr'×3, 'Expr'(Compare)]`，随后
  `_generate_if(IfRegion@144)` 再发同一前缀 + `if fields is not None:`。
- 先例：STORE 路径 L40474–40487 已有同层次双色彩守卫（`_r36.entry is region.merge_block`
  ∧ 非 BASIC ∧ blocks 差集非空 ⇒ `_after_store_stmts=[]`）；f-string 路径缺同款守卫。

### 采纳候选：`r70diag2af`（spec `specs/cand_r70diag2_af.json`，2 个编辑，两文件）
| key | 文件 | 站点 | 三要素 |
|---|---|---|---|
| A | region_analyzer | `_should_skip_block_for_if_region` ≈L16043 | 识别：`block_region` 是 TernaryRegion 且 `_ternary_merge_hosts_next_if(block, region)` 成立；归约：不跳过该块，交由 R13c 建 IfRegion；AST：`if/elif` 结构照常发射（R13c 注释处） |
| F | region_ast_generator | `_try_wrap_fstring_pending_call` L42426 前 | 识别：承载方必须是 **IfRegion** ∧ `entry is region.merge_block` ∧ `blocks-{merge_block}` 非空；归约：`_extra=[]`（尾段不进 post-extra）；AST：三元只发 `Expr(Call)`，尾段由下游 IfRegion 发块前缀+`ast.If` |

> 关键收窄：最初把承载方写成「任意非 BASIC 区域」⇒ `r63_ft.pyc`/`r63_ft2.pyc` 被
> **同 entry 的 TernaryRegion**（`entry=104 merge=104`，blocks `[126,104,120,124]`）误匹配、
> `return False/True` 被清空（45 项 182→180）。改成 `isinstance(..., IfRegion)` 后恢复 182、
> 且 targets 仍 73/81（`dbg6.py` 实测两处命中）。

### 试过的臂（全部实测，勿重开）
| 臂 | 编辑 | 官方 targets | 45 项 | 判定 |
|---|---|---|---|---|
| r70diag2a | A | 72/81，get_price **251** | – | 拒（Σ\|Δ\| 62→81） |
| r70diag2b | B(PRECALL) | 71/81，`fill_minute_or_day_blank` 回归 | – | 拒 |
| r70diag2ab | A+B | 71/81 | – | 拒 |
| r70diag2ace | A+C+D | 72/81，get_price 251 | 182 worse=0 | 拒（get_price 更差） |
| r70diag2f | A+C+D+E | 72/81，get_price 251 | 182 worse=0 | 拒 |
| r70diag2g | A+C+D+E+F（F 过宽） | **73/81** | **180 worse=2** | 拒（r63_ft/ft2） |
| r70diag2h | A+C+D+E+F（F=IfRegion） | **73/81** | 182 worse=0 | 通过，但含冗余 C/D/E |
| **r70diag2af** | **A+F** | **73/81** | **182 worse=0** | **采纳** |
| r70diag2fo | F 单独 | 72/81（get_price 232） | – | 证明 A 必需 ⇒ AF 已最小 |

### AF 五列读数（全部本轮实测）
- 官方 targets：`quote.pyc 73/81`，缺陷 8（get_price 从 9 缺陷名单中消失，无新增）
  Σ\|Δ\| = 41+7+6+3+1+1+1+0 = **60**（landed 62，get_price 2→0）
- `nested_diff`：有差异 code object **15 → 14**（`/Quote#22/get_price#40` 消失；其余逐条不变）
  （注：`build_future_fill_time` 的 frozenset repr 顺序受 PYTHONHASHSEED 影响，13/14 会抖动）
- 金丝雀 4 sha：`4d41187e356544e0` 143/143、`af77224b34b203c4` 10/10、
  `e711b8ea86d49a15` 26/26、`9d09af09249da177` 25/25 ✓
- 45 项电池：**182/200**，worse=0，ERR=0（与 landed 完全一致）✓
- 82 项扩展电池：`battery landed r70diag2af` → landed **318/356 bad=37**、af **318/356 bad=37**，
  `candidate columns worse-than-landed on 0 repro(s)` ✓（两列逐项相同，无丢语句）
- 严格尺：`sstrict67.py build_r70diag2af` → **77/89、缺陷 12、missing=0 extra=0**
  （landed 76/89 缺陷 13；仅 `get_price [seq_len] 230→232` 消失，`target_diff` 三支原样保留）
- 合成见证：landed 4/5 → af **5/5** ✓
- 锚点：`mk_cand70.py` 每条 `txt.count(anchor)==1` 断言通过（A/F 各 1 处）✓

### ADR-1 判据（get_price 属 `seq_len` 族）
- 该族 Σ\|orig−decomp\| **62 → 60（净 −2）** ✓；
- 不是以少发射换：get_price 现与 orig **逐条相等**（230=230），差额来自**去掉重复发射的前缀**，
  语句集合未减少（82 项 bad 与 landed 逐项相同）✓；
- 严格尺未新增 `target_diff`（三支原样）✓；其余族数值逐项未变 ✓。

## Step 5 · 收口

### VERDICTS（靶支 fly/data/quote.pyc，官方 72→73/81）
- `get_price`：**修好**（230→232 归零，严格/官方双尺同时匹配，hunk 消失）。候选 **r70diag2af**。
- `load_bars_from_hundsun`（Δ6）/`load_get_price`（严格 seq_diff #53）：**候选 NONE**
  —— 命中同一根因链但被 T2（`_value_merge_hosts_next_if` 的 `_tail_ops` 缺 `PRECALL`）卡住；
  B/A+B/A+B 形态实测均回归（`fill_minute_or_day_blank`），本轮不落地，形状记 **NONE**。
- `build_current_period_df`（Δ7，`tempdict['is_open']`/`tmp=pandas.DataFrame`/`return tmp` 整段丢失）、
  `run_individual_transform`（Δ41，最大项）、`check_frequency`/`get_individual_data`/
  `get_real_from_zeromq`/`run_tick_socket`：**候选 NONE**（本轮未达成，留给下轮；
  `run_individual_transform` 建议先做 `synth/` 最小复现）。
- 金丝雀同名残余族 `change_his_to_forward`/`check_industry_code`/`run_tick_transform`
  （严格 `target_diff`）：**候选 NONE**（已知死胡同，按 BRIEF §6 不重开）。

**候选：`r70diag2af`**（spec `specs/cand_r70diag2_af.json`；臂 `r70diag2af`；2 编辑 / 2 文件）。

### 对 BRIEF 的更正
1. §0 步骤 1 写的是 `closeout67.py battery landed`，本目录实际只有 **`closeout69.py`**；
   且 `battery(arms)` 的 worse 统计只比对 `arm != arms[0]` ⇒ **单臂调用恒报 0**，
   必须写成 `closeout69.py battery landed <arm>` 才是真的对照（我先单臂跑过一次，读数作废）。
2. §5 未列：`battery45.txt` 带 **UTF-8 BOM**，h62 会把 BOM 当路径前缀 →
   `OSError [Errno 22] '\ufeffF:/...'`；本目录用 `battery45_nobom.txt`。
3. §5 未列：PowerShell `python ... > file` 写出的是 **UTF-16LE**，Python 侧要 `encoding='utf-16'`。
4. §0 步骤 4 写 `sstrict67.py <臂名> <名单>`，实际首参是 **build 目录名**（`build_<臂名>`），
   例：`sstrict67.py build_r70diag2af targets.txt dump/strict_af.json`。
5. §6 站点：`_try_wrap_fstring_pending_call` 定义 L42368、`post_consumer_extra_stmts` 赋值 **L42426**
   （BRIEF 未列，本轮根因 T3 所在）。
