# Round 76 — fly/data/quote.pyc 11 个失败单元根因分析与复现

- 日期：2026-09-30　分析角色：测试工程师（只读分析，未改任何 core/ 代码）
- 靶：`site-packages/fly/data/quote.pyc`（92 单元，81 success / 11 failure，88.04%）
- 判据：`scripts/pyc_verify.py single`（pylingual compare_pyc 逐单元 verdict）
- 反编译命令：`python -X utf8 pycdc.py --region -o quoteOK.py quote.pyc`
- 基线状态：HEAD = 3407ac07（round76 Task0），round75 fix1（B1a 嫁接）/fix2 均未落地
- 前史：round3 曾全量分析 quote.pyc 18 个不匹配（`test_repros/round3/ANALYSIS.md`）；round75 diag1 将其中 8 个单元归入 F-ABSORB 家族（`rounds/round75/batches/fix1/FACTS.md` §4.1 #49–56）

## 0. 靶状态确认（步骤 1 读数）

```
python -X utf8 scripts\pyc_verify.py single site-packages\fly\data\quote.pyc
[single] status=failure units=81/92 success_rate=88.04%
```

11 个失败单元（verdict 与 round75 交接一致，无新增、无自愈）：

| # | 单元 | verdict |
|---|---|---|
| 1 | `<module>.Quote.build_current_period_df` | Different bytecode |
| 2 | `<module>.Quote.load_bars_from_hundsun` | Different bytecode |
| 3 | `<module>.Quote.load_get_price` | Different control flow |
| 4 | `<module>.Quote.change_his_to_forward` | Different control flow |
| 5 | `<module>.Quote.change_his_to_backward` | Different control flow |
| 6 | `<module>.Quote.get_price` | Different control flow |
| 7 | `<module>.Quote.check_frequency` | Different control flow |
| 8 | `<module>.Quote.get_real_from_zeromq` | Different control flow |
| 9 | `<module>.Quote.run_individual_transform` | Different control flow |
| 10 | `<module>.Quote.run_tick_socket` | Different control flow |
| 11 | `<module>.Quote.get_individual_data` | Different control flow |

与 round3 相比：18 失败 → 11 失败，f-string 模板错乱（R3-A）已全部修复；本轮剩余的 11 个单元中
有 7 个是 round3 已知家族的残余（R3-F/R3-B/R3-I 同族），4 个是本轮新定位的形态（R76-A/B/C/D2）。

---

## 1. 失败单元首分歧清单（对齐 diff：orig pyc vs quoteOK.py 重编译）

工具：`r76_adiff.py`（difflib 序列对齐，跳转含绝对目标；norm_ratio<1 表示跳转目标语义级不同）。

| # | 单元 | len orig→prod | 首分歧（orig || prod） | 语法形态 | 根因类 |
|---|---|---|---|---|---|
| 1 | build_current_period_df | 124→113 | idx109 `LOAD_FAST tempdict / STORE_SUBSCR …` → `POP_TOP; LOAD_CONST None` | `d['k'] = [1 if c else 0]` + `tmp = DataFrame(d, index=…); return tmp`（块尾） | **R76-E** |
| 2 | load_bars_from_hundsun | 526→533 | idx55 prod 插入 `POP_TOP + os.path.exists(DumploadDailyFile) 重求值`（7 条） | 多语句块尾接 `os.path.exists(…) and typet == 6:` | **R76-A2** |
| 3 | load_get_price | 185→185 | idx58 `POP_JUMP_FORWARD_IF_FALSE to 486` → `POP_TOP` | `if len(…) != 0:` 守卫 + 内层 `if is_utc=='0' and typet in T:` + elif | **R76-A1** |
| 4 | change_his_to_forward | 572→573 | idx262 `POP_JUMP_FORWARD_IF_FALSE to 1788`（链后兄弟块） → `to 2838`（远端 merge） | for 内 `if X: pass`（空真体） | **R76-C** |
| 5 | change_his_to_backward | 388→388 | idx232 `POP_JUMP_FORWARD_IF_TRUE to 1406`（赋值块） → `to 1402`（break 路径） | for 内 `elif A or C: <赋值> else: break` | **R76-B** |
| 6 | get_price | 256→258 | idx66 `POP_JUMP_FORWARD_IF_NONE to 726` → `LOAD_CONST None; IS_OP; POP_TOP` | `if fields is not None:` 守卫（多语句块尾） | **R76-A1** |
| 7 | check_frequency | 132→133 | idx107 `LOAD_CONST None; RETURN_VALUE` → `JUMP_FORWARD to 558`（+尾部复制 return None） | try 体全终结 raise 链后不可达 return | **R76-F** |
| 8 | get_real_from_zeromq | 793→790 | idx150 `POP_JUMP_FORWARD_IF_FALSE to 874`（elif flag==1） → `to 4048`（函数尾）；flag 块移位；exc_obj/exc_tb 变 LOAD_GLOBAL | 臂末终结核 try + elif 链 + except 内元组解包 | **R76-D2 + R76-D3** |
| 9 | run_individual_transform | 412→359 | idx103/105 recv/eval 语句组丢失；`逐笔数据返回为空` 块位移进 handler（continue 之后不可达） | while + 双层 try + continue | **R76-G** |
| 10 | run_tick_socket | 347→348 | idx14 `POP_JUMP_FORWARD_IF_FALSE to 528`（else 臂） → `to 1122`（远端）；warning 块位移 | if/else 的 true 臂末终结核 try + 兄弟语句 | **R76-D1** |
| 11 | get_individual_data | 354→354 | idx167 `POP_JUMP_FORWARD_IF_FALSE to 970`（elif 链） → `to 1730`（函数尾）；flag 块移位 | 臂末终结核 try + elif 链 | **R76-D2** |

---

## 2. 根因分类（区域类型 × C1/C2/C3 条款 × 代码锚点）

### R76-A1 前导守卫/and 链首操作数块未被 IfRegion 认领 → 守卫裸表达式化（条件缺失）

- **影响单元**：load_get_price、get_price
- **区域类型**：IfRegion（entry 落在守卫的后继块/and 链第二操作数上）+ 未认领前导条件块
- **CFG 结构**（load_get_price 实测，`r76_regions.py` 探针）：
  ```
  block@236（=A：len(panel.major_axis)!=0，块尾 POP_JUMP_IF_FALSE→486）── 无任何区域认领
  IfRegion entry=284 merge=486 blocks=[284(B),306(C),314,376,378(elif D),386] condition_block=284
  ```
  真实结构是 `if A: { if B and C: X elif D: Y }`（A 的 false 边直跳 merge 486，越过整条 elif 链；
  B 的 false 边 → 378=D）。区域分析器只形成了内层 IfRegion@284，A 所在块@236 留在区域外。
  get_price 同形：block@144（n_instr=42，含日志 f-string、`candle_period=None`、两次
  check_datetime、check_frequency 等语句 + 尾部 `fields is not None` 的 POP_JUMP_IF_NONE→726）
  未被认领；IfRegion@328/726 只认领守卫体。
- **生成层表现**：未认领块经 `_generate_block_statements_body` 的 CJB 路径
  （`_cjb_skip_inline_if`：then-entry 是某区域 entry 时只发射 `_cjb_pre_stmts` 就 return，
  `_cjb_cond_expr` 被物化/丢弃，region_ast_generator.py:47629-47643）。产物：
  - get_price（quoteOK.py:665-666）：`fields is not None` 成裸表达式，守卫体（isinstance
    检查 + assert + for）**无条件执行** —— `if fields is not None:` 语义丢失；
  - load_get_price（quoteOK.py:446-450）：`len(panel.major_axis) != 0` 成裸表达式，
    `if is_utc=='0' and typet in T` 被拆成嵌套 if，elif 挂接层级改变
    （`if A: if B: X elif D: Y` ≠ `if A and B: X elif D: Y`，len==0 时走臂反转）。
- **违反条款**：**C1**（IfRegion 归约只读 entry=284 的局部信息，未把「以区域 merge 为
  条件边目标、fall-through 指向区域 entry 的前置条件块」这一 L(A) 内事实并入区域条件）；
  **C2**（子区域作为黑箱被父级消费时，前导守卫块的边信息未随消费传递，被 skip 分支丢弃）。
- **代码锚点**：`core/cfg/region_ast_generator.py:47629-47643`（`_cjb_skip_inline_if`
  丢弃点——即 wiki 台账 B1a 同一根因点）；`:47466-47506`（`_boolop_result` 裸表达式发射）；
  `core/cfg/region_analyzer.py:18705`（IfRegion 构造）、`:23420`（`_identify_boolop_regions`）。
- **与 B1a 的关系**：B1a（jq）是 BoolOpRegion 已形成、skip 分支把纯条件操作数从链上丢掉；
  R76-A1 是 IfRegion 从链中段 entry 开始、前导块整体未认领。同一丢弃点
  （`_cjb_skip_inline_if`）的两个入口形态。**round75 fix1 的嫁接方案（挂块上的
  `_leading_operand` + `_graft_pending_operand`）未落地，B1a 与 R76-A1 同时在场。**

### R76-A2 前导操作数双重消费（裸表达式 + 条件各一次）

- **影响单元**：load_bars_from_hundsun
- **区域类型**：IfRegion@332（entry=B 块）+ 前导多语句块@144（块尾=and 首操作数）
- **CFG 结构**（实测）：block@144（n_instr=32：日志 f-string + `data=OrderedDict()` +
  `retpanel=pandas.Panel()` + `os.path.exists(DumploadDailyFile)` 的求值，块尾
  EXTENDED_ARG+POP_JUMP_IF_FALSE→1532）；B 块@332（`typet==6`，POP_JUMP→1532）；
  `IfRegion entry=332 merge=1532 blocks=[332,346,388,394,464,544,574,712,1036,1174,1238]`。
- **生成层表现**（quoteOK.py:386-387）：
  ```python
  os.path.exists(DumploadDailyFile)                          # 裸表达式（POP_TOP）
  if os.path.exists(DumploadDailyFile) and typet == 6:       # 条件里又求值一次
  ```
  block@144 的语句渲染把尾部操作数物化成裸 Expr，而 IfRegion@332 的条件重建又跨块重读同一
  组指令 → 同一组指令被两个语句消费，产物多 7 条指令（526→533），verdict=Different bytecode。
- **违反条款**：**C1**（跨块读取区域外指令；「每块唯一归属」被破坏——块尾条件指令被
  语句渲染与区域条件重建同时认领）。
- **代码锚点**：`region_ast_generator.py:47466-47506`（块级裸表达式发射）与
  `:20669`（`_if_extract_condition_from_instructions` 跨块条件重建）、`:32662`
  （`_build_boolop_expression`）；`region_analyzer.py:18692-18695`（臂共享块去重只从
  then 删除——见 R76-B）。
- **修复方向**：建立「块尾条件指令消费登记」：块尾的纯条件指令一旦被区域条件重建认领，
  块的语句渲染不得再物化它（反之亦然）；或 IfRegion 归约时把含尾操作数的前导块并入
  区域 condition 前缀（同 R76-A1 处方）。

### R76-B or 链首操作数的边目标归属错误 → 双臂交换/极性反转/break 丢失

- **影响单元**：change_his_to_backward（真身）；`r76_n03_simple_or_break.py`（最小复现，
  简化形：首操作数 TRUE 边指向 break 块被当作 if 出口 → A 真时 break 丢失）
- **区域类型**：for 循环内 IfRegion/IF_ELIF_CHAIN，else 臂为 break（break = `POP_TOP + JUMP`）
- **CFG 结构**（change_his_to_backward 实测）：
  ```
  block@1162（A：data[preindex:n].empty，POP_JUMP_IF_TRUE→1406）
  block@1192（C：…tz_localize(None) != Timestamp(…)，POP_JUMP_IF_FALSE→1406）
  block@1402（POP_TOP + JUMP_FORWARD→1742  = break 路径）
  block@1406（64 条指令的赋值块，A-true 与 C-false 的共享目标）
  IfRegion entry=1192 merge=1742 blocks=[1192,1402,1406] condition_block=1192   ← 从 C 单独成区
  IfRegion entry=1116 merge=1722 blocks=[1116,1122,1162,1402,1406]              ← 外层 if/elif
  ```
  正确源形（实验验证，`elif A or <C 取反成 ==>: <赋值 1406> else: break`，编译产物与
  orig 逐指令同形含 1402 处 POP_TOP）：A 的 TRUE 边与 C 的 FALSE 边同指赋值块 1406
  （or 链 then 臂），C 的 TRUE 边（fall-through）是 break。产物却渲染成
  `elif A or C(极性未翻): break else: <赋值>`（quoteOK.py:577-581）——
  两臂交换 + C 极性未取反：**len(A)=empty 时 orig 走赋值，产物走 break**。
- **机理**：区域分析器把 C 块按标准 CJB if 分解为 `if C: then=1402(break) else=1406`（对 C
  单独成立），外层 elif 组装时把 A 按「同构链」直接并联进 C 的条件，未校验 A 的 TRUE 边
  目标（1406）≠ 链 then 臂（1402）。`region_analyzer.py:18692-18695` 的臂共享块去重
  （then/else 都认领 1406 时只从 then 删除）进一步固定了错误的臂归属。
- **违反条款**：**C1**（成链判据缺少操作数边收敛性校验：读取了各操作数的跳转目标这一
  局部事实，但未要求同构）。
- **代码锚点**：`region_analyzer.py:18692-18695`（臂共享去重）、`:18705`（IfRegion 构造）、
  `:18719`（`_build_elif_region`）；生成器侧 `region_ast_generator.py:32662`
  （`_build_boolop_expression`）、`:12523`+（IF_ELIF_CHAIN → AST）。
- **最小复现**（r76_n03，17 行）：
  ```python
  for n in series:
      if data[n] is None or data[n] < 0:   # A 真（None）→ break
          break
      else:
          out.append(data[n])
  ```
  产物把 A 取反成外层 `if data[n] is not None:` 且无 else，A 真时什么都不做
  （break 丢失）→ Different control flow。
- **修复方向**：or/and 成链不变量——「所有操作数的 TRUE（or）/FALSE（and）边必须收敛到同一
  臂块」；不收敛时该操作数必须以取反形态入链并交换臂语义，或退化嵌套 if。判据只读
  L(A)（各条件块的出边），无需跨层信息。

### R76-C `if X: pass` 空真体未识别 → 吸收后继兄弟块为 if 体

- **影响单元**：change_his_to_forward；复现 `r76_05_empty_if_body.py`
- **区域类型**：for 循环内 IF_ELIF_CHAIN
- **CFG 结构**：`if X: pass` 在 3.11 编译为
  `POP_JUMP_FORWARD_IF_FALSE→(fall-through+2); NOP`（真体空标记，实验确认）。
  orig 中该 vacuous 跳转位于 elif 臂内（offsets 1778-1786），其后 1788 是**链外**的
  `if preindex is None:` 兄弟块。产物把 1788 起的块吸收成 `if <end-match>:` 的体
  （quoteOK.py:515-532），elif 的 false 边被改道到 2838（链尾 merge 之外）。
- **违反条款**：**C2**（空体 if 的黑箱边界：条件跳转的 TRUE 边 fall-through 与 FALSE 边
  同指一个后继块时，该 if 的体必须为空/pass；后继块属于父级，不得被子区域吸收）。
- **代码锚点**：`region_analyzer.py:18719`（`_build_elif_region`，未识别「跳转目标
  ==fall-through+N 且中间仅 NOP」的空体形态）；生成器 `region_ast_generator.py:17949`
  （`_if_generate_normal`）/`:12523`（elif 链生成）。
- **修复方向**：elif 臂展开时识别「臂尾条件跳转的目标 == 下一指令（经 NOP）」→ 发射
  `if X: pass`，臂到此闭合；后继块留给父级。

### R76-D1 if/else 的 true 臂末终结核 try 的出口汇聚块被吸收进 true 臂

- **影响单元**：run_tick_socket；复现 `r76_06_tryexit_absorb.py`
- **区域类型**：TryExceptRegion（嵌套）× IfRegion
- **CFG 结构**（orig 实测）：
  ```
  22: NOP 外层 try 标记
  24-62: message = socket.recv()
  64: if message: POP_JUMP_IF_FALSE→528（else 臂）
  68: NOP 内层 try 标记；70-134: message = eval(message.decode())
  136: JUMP_FORWARD→684（内层 try 正常出口）
  140-518: 内层 handler；528-682: else 臂（warning + updateflag=-1 + return None）
  684+: 链外兄弟语句 stocks = list(message.keys())[0]; real_data = …; if real_data: …
  ```
  else 臂全 return ⇒ if/else 的唯一出口是 684（兄弟块）。产物把 684+ 吸收进 true 臂
  （quoteOK.py:1444-1460），prod 的 else 边改跳 1122（函数尾）→ Different control flow。
  `逐笔数据返回为空` warning 语句也随之位移进错误块。
- **违反条款**：**C2**（then 臂子区域（终结核 try）的出口块同时是 if/else 的 merge 与链外
  语句入口时，该块唯一归属父级；子区域消费不得越过它）。
- **代码锚点**：`region_analyzer.py:7603`（`_identify_try_except_regions`）、
  `:18692-18695`（臂共享去重——本例 684 被两臂/区域共享时的归属裁决）；
  生成器 `region_ast_generator.py:17949`（`_if_generate_normal`）。
- **修复方向**：if/else 生成时校验 then 臂区域的出口块是否同时为区域外的语句入口块
  （即 if/else 的 merge）；是则该块不得并入 then 体，须作为链后语句发射。

### R76-D2 臂末终结核 try 的「冷布局」错位（编译器版本差异疑点，需修复工程师裁定）

- **影响单元**：get_individual_data、get_real_from_zeromq；合成探针 `r76_07_terminal_try_elif.py`
- **CFG 结构**（orig 实测，两单元同形）：
  ```
  884/788: if redata: POP_JUMP_IF_FALSE→970/874（elif flag==1 链）
  888-966: redata = redata.get('data').get(…)          ← 臂前缀
  968: JUMP_FORWARD→1124/1032                            ← 直接跳进推迟的 try 单元
  970-1122: elif flag==1 / elif flag==-1 / return(None, flag)  ← elif 链物理位置在 try 之前
  1124: NOP try 标记；1126-1740: try 体（全 return 终结）；1742-1882: handler
  ```
  即 `if redata: <赋值; 终结核 try/except> elif … elif …; return None` 的原始布局中，
  **try 单元被推迟到 elif 链之后**。产物源码（quoteOK.py:1056-1144 / 1582-1614）语义等价
  （try 内联在臂内、elif 链跟随），但本地 3.11.7 重编译会把 elif 链放到函数尾
  （prod 首分歧：POP_JUMP→970 变 →1730/4048）。
- **关键实验**：`r76_07_terminal_try_elif.py` 用同形源在 3.11.7 下编译 → 反编译 → **MATCH**
  （3.11.7 对该形态总是内联 try、elif 在后；5 组变体实验均未复现推迟布局）。
  ⇒ **orig quote.pyc 疑由行为不同的 3.11.x 编译（臂末终结核 try 被推迟发射）**。
- **对修复工程师的硬结论**：这两个单元的产物源码很可能语义正确；若 3.11.7 下不存在能
  产生 orig 布局的源形态（建议做一次源级可达性穷举：if/elif/else 排列、try/except/else/
  finally 组合），则字节级不可修，应按「编译器版本布局差」提请用户裁定（对比 R74 的
  TRYVERDICT 先例），不要为凑字节去破坏语义。
- **违反条款**：若裁定为可修，属于 **C2**（elif 链块在父级与臂区域间的归属裁决错误）；
  若为编译器差异则不构成算法缺陷，但需要记录在案。

### R76-D3 except handler 内元组解包降级

- **影响单元**：get_real_from_zeromq；复现 `r76_08_exc_unpack.py`
- **orig**：handler 内 `exc_type, exc_obj, exc_tb = sys.exc_info()`
  （`UNPACK_SEQUENCE` + 3×`STORE_FAST`）；**产物**（quoteOK.py:1135-1137）丢
  UNPACK_SEQUENCE 与 exc_obj/exc_tb 两个 STORE，只剩 `exc_type = sys.exc_info()`，
  且对 exc_tb 的引用变 **LOAD_GLOBAL**（运行时 NameError）——真实语义缺陷，非布局。
- **违反条款**：**C1**（handler 块语句重建的指令跨度校验缺失：UNPACK_SEQUENCE 的
  目标数与 STORE 数不匹配时未回退）。
- **代码锚点**：`region_ast_generator.py` 的 handler 语句生成（`_generate_block_
  statements_body` 的 UNPACK 分支，`:47431-47449` 附近——`_unpack_result` 只在找到
  完整语句组时生效）。
- **修复方向**：handler/语句组内出现 `UNPACK_SEQUENCE` 时校验后续连续 STORE 数 ==
  UNPACK 序列数，不满足则整组回退保守渲染（禁止只留部分目标）。

### R76-E 列表包裹三元 + 下标赋值降级 + 尾语句吞没（round3 R3-F 残余）

- **影响单元**：build_current_period_df；复现 `r76_09_ternary_subscr.py`（同 round3 r3_06）
- **orig 尾部**（if 体末）：`tempdict['is_open'] = [1 if … != 0 else 0]`（BUILD_LIST+
  STORE_SUBSCR）→ `tmp = pandas.DataFrame(tempdict, index=index)` → `return tmp`；
  **产物**（quoteOK.py:379-381）：裸 `[1 if … else 0]`（POP_TOP），STORE_SUBSCR、
  DataFrame 构造、return tmp 全部丢失，函数变隐式 return None。
- **违反条款**：**C1**（伪三元合并的语句边界判据未覆盖「共享 BUILD_LIST + STORE_SUBSCR」
  的目标归属；组内未被任何语句认领的指令（DataFrame/return）未触发回退）。
- **代码锚点**：`region_ast_generator.py:47466-47506`（`_boolop_result`/语句发射）与
  TernaryRegion 生成段；`region_analyzer.py:1055`（BoolOpRegion）/TernaryRegion。
- **修复方向**：round3 P1-1 处方仍有效——表达式语句发射前校验组内是否含
  STORE_SUBSCR/STORE_FAST/RETURN_VALUE 或存在未认领指令；伪三元合并校验 BUILD_LIST
  位于跳转汇合点之后（r3_06/r76_09 可作回归用例）。

### R76-F 全终结分支链后不可达 return None 位移/复制（round3 R3-B 残余，布局级）

- **影响单元**：check_frequency；复现 `r76_10_dead_return_shift.py`（同 round3 r3_11）
- **orig**：try 体 if/elif/else 全 raise/assert 终结，链尾与 PUSH_EXC_INFO 之间有不可达
  `LOAD_CONST None; RETURN_VALUE`；**产物**：原位变 `JUMP_FORWARD→558`，函数尾复制出
  return None（+1 指令）+ 2 处 2 字节跳移。
- **违反条款**：C1（块内指令的发射位置唯一性——不可达隐式 return 属于其所在块，不得
  物化为跨块跳转+复制）。
- **锚点**：`region_ast_generator.py` 的隐式 return 处理（`_check_block_has_trailing_
  return_none` / `mark_trailing_return_none`，region_analyzer.py:18713-18716 的调用点）。
- **修复方向**：不可达隐式 return 保持原位或省略，不得搬到函数尾复制（等价但计分不过）。

### R76-G while + 双层 try + continue 的 try 区域块归属错乱（round3 R3-I 残余，灾难级）

- **影响单元**：run_individual_transform；简化复现 `r76_11_nested_try_scramble.py`
- **产物**（quoteOK.py:1322-1383）：内层 try 体变 `pass`、`message = socket.recv()` /
  `eval(message.decode())` 语句丢失、业务块（stocks/real_data 分发、socket.close、
  isSet 检查）被吸入 except handler 且位于 `continue` 之后（不可达位），
  `time.sleep(0); self.individual_subscribe.isSet()` 循环尾裸表达式化；指令 412→359。
- **违反条款**：**C1**（异常表条目界定的 try 体/handler 块集合与发射覆盖不一致，
  体内块逃逸进 handler——与 R3-I/round13 家族同根）。
- **代码锚点**：`region_analyzer.py:7603`（`_identify_try_except_regions`）；
  `region_ast_generator.py` `_generate_try_body`（round75 fix2 的 E1/E2 规则针对
  「FOR_ITER 出口块落 handler 后」的同族形态，但本单元是「双 try 嵌套 + continue」
  变体，未被覆盖）。
- **修复方向**：round3 P0-2 处方（异常表驱动的 try/except 块归属不变量 + handler 不得
  吸收范围外块 + 位移即回退）仍有效；r76_11 是覆盖「双 try + continue」变体的回归用例。

---

## 3. 复现清单（统一流水线读数，见 test_repros/round76/RESULTS.txt）

判定 = compare_pyc（编译 → `pycdc --region` → 重编译 → 逐单元比对）。三类方法：
- **synthetic**：合成源 `r76_XX_*.py`（py_compile optimize=0）；
- **slice**：quoteOK.py 方法逐字切片 + 同文件导入语句（保 LOAD_GLOBAL 符号绑定形态）；
- **real**：quote.pyc 真身码对象移植为顶层单函数 pyc（16 字节原头 + marshal(code)），
  产物重编译后提取函数码再移植对齐比较——自稳定缺陷（对产物形已不再出错）的唯一
  忠实复现法。

| 文件 | 判定 | 根因类 | 说明 |
|---|---|---|---|
| real_build_current_period_df.pyc | **MISMATCH**（Different bytecode） | R76-E | 真身码移植，verdict 与靶一致 |
| real_load_bars_from_hundsun.pyc | **MISMATCH**（Different bytecode） | R76-A2 | 同上 |
| real_load_get_price.pyc | **MISMATCH**（Different control flow） | R76-A1 | 同上 |
| real_change_his_to_forward.pyc | **MISMATCH**（Different control flow） | R76-C | 同上 |
| real_change_his_to_backward.pyc | **MISMATCH**（Different control flow） | R76-B | 同上 |
| real_get_price.pyc | **MISMATCH**（Different control flow） | R76-A1 | 同上 |
| real_check_frequency.pyc | **MISMATCH**（Different control flow） | R76-F | 同上 |
| real_get_real_from_zeromq.pyc | **MISMATCH**（Different control flow） | R76-D2+D3 | 同上 |
| real_run_individual_transform.pyc | **MISMATCH**（Different control flow） | R76-G | 同上 |
| real_run_tick_socket.pyc | **MISMATCH**（Different control flow） | R76-D1 | 同上 |
| real_get_individual_data.pyc | **MISMATCH**（Different control flow） | R76-D2 | 同上 |
| slice_load_get_price.py | **MISMATCH**（2/3） | R76-A1 | 产物形自不稳（对其自身重编译产物仍错） |
| slice_get_price.py | **MISMATCH**（2/3） | R76-A1 | 同上 |
| slice_load_bars_from_hundsun.py | **MISMATCH**（2/3） | R76-A2 | 同上 |
| slice_run_individual_transform.py | **MISMATCH**（2/3） | R76-G | 产物形自不稳（真实灾难形的次级形态仍错） |
| r76_05_empty_if_body.py | **MISMATCH**（1/2） | R76-C | 合成最小复现 |
| r76_06_tryexit_absorb.py | **MISMATCH**（1/2） | R76-D1 | 合成最小复现 |
| r76_08_exc_unpack.py | **MISMATCH**（1/2） | R76-D3 | 合成最小复现 |
| r76_09_ternary_subscr.py | **MISMATCH**（1/2） | R76-E | 合成最小复现（round3 r3_06 同型仍在） |
| r76_10_dead_return_shift.py | **MISMATCH**（1/2） | R76-F | 合成最小复现（r3_11 同型仍在） |
| r76_11_nested_try_scramble.py | **MISMATCH**（1/2） | R76-G | 合成最小复现（简化形） |
| r76_n03_simple_or_break.py | **MISMATCH**（1/2） | R76-B | 合成最小复现（首 or 操作数 break 丢失形） |
| r76_b1a_jqcond.py（=round75 repro75_jqcond） | **MISMATCH**（4/5） | B1a | jq replace_args 前导操作数丢弃仍在 |
| r76_b1b_orarm.py（=round75 neg75_jqcond2） | **MISMATCH**（2/3） | B1b | `if a and b or c:` or 臂丢失仍在 |

**MISMATCH 合计 24 项**（真身移植 11 + 切片 4 + 合成 7 + B1a/B1b 2）≥ 任务要求 10；
ERROR=0。全量读数见 `RESULTS.txt`（41 文件：MISMATCH=24 MATCH=17）。

**MATCH 负对照（≥2，实际 17：3 个专用负对照 + 7 个探针边界 MATCH + 7 个产物形切片 MATCH）**：

| 文件 | 判定 | 意义 |
|---|---|---|
| r76_n01_simple_and.py | **MATCH**（2/2） | 平铺 `if A and B: X else: Y` 正确 → A1 缺陷的边界 |
| r76_n02_simple_guard.py | **MATCH**（2/2） | 简单 `if x is not None:` + 顺序体正确 → 守卫需嵌套子结构+多语句前导才触发 |
| r76_n04_simple_try_elif.py | **MATCH**（2/2） | try 为臂首语句（无前导赋值）的 if/elif 正确 → D2 触发需「赋值前缀+终结核」 |
| r76_01_guard_leak.py | MATCH（2/2） | 简化守卫形未触发（真实 42 指令前导块才触发）|
| r76_02/02b_andchain*.py | MATCH（2/2） | 平铺 and+elif 未触发 |
| r76_03/03b_double_eval*.py | MATCH（2/2） | 简化双重求值形未触发（真实 f-string 前导才触发）|
| r76_04_or_armswap.py | MATCH（2/2） | 推导形 or+break 未触发臂交换（真实 64 指令共享赋值块才触发）|
| r76_07_terminal_try_elif.py | MATCH（2/2） | **冷布局在 3.11.7 编译的同形源上不存在** → R76-D2 编译器差异疑点的正面证据 |
| slice_change_his_to_forward/backward、slice_build_current_period_df、slice_check_frequency、slice_get_individual_data、slice_get_real_from_zeromq、slice_run_tick_socket | MATCH | 产物形自稳定（错误形态二次往返不再变化）→ 需 real 移植法才能暴露；slice_get_individual_data/get_real_from_zeromq 的 MATCH 同时是 D2 编译器差异假设的独立证据（产物形在 3.11.7 下可正确往返） |

---

## 4. 给修复工程师的建议（按收益/风险排序）

1. **P0（R76-A1+A2，覆盖 3 个真实单元，与 B1a 同点同族）**：前导条件块并入 IfRegion。
   在 `_cjb_skip_inline_if`（region_ast_generator.py:47629-47643）与 IfRegion 归约
   （region_analyzer.py:18705）之间建立同层判据：块尾条件跳转的 fall-through 是区域
   entry、且跳转目标 == 区域 merge（或区域 merge 的支配祖先）时，该块的纯条件指令必须
   作为区域条件的**前导操作数**入链（单操作数守卫则并入为外层 if/嵌套结构），并登记
   消费（杜绝 A2 的二次物化）。round75 fix1 的 `_leading_operand`/`_graft_pending_operand`
   方案可推广到单操作数守卫；落地时用 load_get_price/get_price/load_bars 三个 real 移植
   复现作验收，负对照 r76_n01/n02 不得回归。
2. **P0（R76-B）**：or/and 成链加「边收敛性」判据（region_analyzer.py:18692-18705 +
   `_build_boolop_expression`）：操作数边目标不收敛时必须取反入链/交换臂或退化为嵌套
   if；臂共享块去重（:18692-18695）须按边的真实极性归属裁决而非固定删 then。验收：
   real_change_his_to_backward + r76_n03；注意 :18692 注释中 load_daily.pyc 的旧形态
   不得回归。
3. **P1（R76-C）**：elif 臂展开识别 `if X: pass`（跳转目标==fall-through+2 且中缝仅 NOP）
   → 发射 pass 并闭合臂，兄弟块归父级。验收：real_change_his_to_forward + r76_05。
4. **P1（R76-D1）**：if/else 的 then 臂区域出口块 == 链外语句入口时禁止并入 then 体。
   验收：real_run_tick_socket + r76_06；负对照 r76_n04。
5. **P1（R76-D3）**：handler 内 UNPACK_SEQUENCE 与 STORE 数量校验，不足整组回退。
   验收：r76_08 + real_get_real_from_zeromq（连同 D2 的裁定）。
6. **P2（R76-E/F/G：round3 已开处方的残余）**：E/F 直接复用 round3 P1-1/P2-2 处方
   （语句跨度校验/不可达 return 保位），r76_09/r76_10 为现成回归用例；G 复用 round3 P0-2
   异常表驱动归属不变量，r76_11 扩展「双 try+continue」变体。
7. **R76-D2 先裁定再动手**：get_individual_data / get_real_from_zeromq 的 elif 链布局
   是「臂末终结核 try 被原编译器推迟」的形态（5 组 3.11.7 同形源实验全部内联 → MATCH）。
   修复工程师应先做 3.11.7 源级可达性穷举；不可达则提请用户按「编译器版本布局差」
   裁定（R74 TRYVERDICT 先例），避免为凑字节破坏正确的语义结构。
8. **B1a/B1b 提示**：B1b（`if a and b or c:` 的 or 臂丢失）与 R76-B 同为「链首/链中操作数
   边归属」家族——建议同一批处理，复用 r76_b1b_orarm.py 作回归。

---

## 5. B1a / B1b 现状确认读数（步骤 3 要求）

| 破口 | 复现文件 | 复跑读数 | 结论 |
|---|---|---|---|
| B1a（BoolOp 前导操作数丢弃，jq_trans_module.replace_args） | `…/round75/batches/fix1/synth/repro75_jqcond.py`（本轮复制为 `test_repros/round76/r76_b1a_jqcond.py`） | units **4/5**，`***<module>.func_get_bars_convert_code.replace_args: Failure: Different control flow` | **仍 MISMATCH**（round75 fix1 嫁接未落地；`git log` 确认 HEAD 3407ac07 无 jqop1） |
| B1b（语句上下文 `if a and b or c:` or 臂丢失） | `…/synth/neg75_jqcond2.py`（本轮复制为 `r76_b1b_orarm.py`） | units **2/3**，`***<module>.neg_b: Failure: Different control flow` | **仍 MISMATCH**（第二丢弃入口未定位未封闭） |

落地标记检查：当前树 grep `_graft_pending_operand` / `_contains_identity` 未命中
（round75 fix1 未落地），与 spec.md「B1a 落地 + B1b 定位封闭」的 round76 要求相符。

## 6. 产物与工具索引

- 复现目录：`F:\Downloads\pythoncdc-main\test_repros\round76\`（RESULTS.txt + 23 MISMATCH
  复现 + 8 负对照 + 各 `_dec.py`/`_dec.pyc`）
- 分析工具（C: 工作目录，未写仓库）：`r76_dis.py`（反汇编）、`r76_adiff.py`（对齐 diff）、
  `r76_regions.py`（CFG 块 + 区域结构 dump）、`r76_exctab.py`（3.11 异常表解码探针）、
  `r76_pipe.py`/`r76_real_pipe.py`（判定流水线）、`gen_r76*.py`/`r76_transplant.py`
  （复现生成）、`run_r76_final.py`（统一运行器）
- 关键读数命令：`python -X utf8 scripts\pyc_verify.py single site-packages\fly\data\quote.pyc`
