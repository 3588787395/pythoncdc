# Round 5 · FIX_B117 —— D 族「出口边内吞」：站点已定位到行，规则已实测，语料 0 翻转 ⇒ 字节级回滚

轮次：Round 5 / 破口 = `rounds/round4/REVIEW.md` §6 行 **B117**
（主靶 `realtime_event_source.pyc` 12/13 · 次靶 `profiler_func.pyc` 17/18，同机制）。
判定尺：唯一判据 `scripts/pyc_verify.py`（全程未改、未替代）。
插桩位置：临时探针一律在 `D:/Temp/rrv5/`（已删除），生产代码在判定期只做过一次可逆试改，终态已回滚。

**结论标记：「仅归档 spec 未落地」**。
**语料翻转：0**（`realtime_event_source` 12/13 → 12/13，`profiler_func` 17/18 → 17/18）。
合成臂翻转：0（本票未新增臂——按验收规则，只有语料翻转才允许追加 `r4_probe_index.json`，故交付物 4 不执行）。

---

## 1. 出口边在哪一行被丢（插桩证据链，全部实测）

靶单元 `<module>.RealtimeEventSource.clock_worker`。丢失段 = orig off **7972–8590**
（`for i in range(60)` 耗尽边之后的整个 `if persist_flag is False: …` 语句段，100 条指令）。

| 步骤 | 探针读数（原文） | 结论 |
|---|---|---|
| ① 块是否无归属 | `build_cfg + RegionASTGenerator(cfg).generate()` 后：**total blocks 191 / generated 191，UNGENERATED BLOCKS 空** | 不是「没人认领」，是**认领了却不发射**（原则 2 的登记面被内层一次性吞掉） |
| ② 成员关系 | `FOR_LOOP@7706 blocks=[7668,7706,7708,7710,7712,7814,7818,7836,7890,7960]`、`exit=None`；`IF_ELIF_CHAIN@7634 then_blocks=[7668,7706,…,8588]`、`else_blocks=[8592,…,9144]` | 7972 属 **7634 首臂成员**，与 for 循环同臂、在循环出口边之后 ⇒ 应由该臂交付（§1.5 C3 的「出口块被区域外路径引用」形） |
| ③ 出口边解析本身是对的 | `region_analyzer.py:6106-6107` `_find_loop_else`：`[_find_loop_else] header@7706 loop_type=FOR_LOOP for_iter_exit=7972 else_blocks=[] natural_exit=7972` | 分析端**算出了** natural_exit=7972 |
| ④ 出口边被丢的行 | `region_analyzer.py:5186` `region = LoopRegion(...)` 构造参数**不含 `exit=`**，`natural_exit` 只在 4891/5100 的 break/continue 判定里被读一次即弃 ⇒ 实测所有 LoopRegion `exit=None` | 出口边在**区域对象构造点**丢失（vestigial 消费，与 §6.1 点名的计数器同形态，本票未动它） |
| ⑤ 发射端拿不到段 | 调用栈（traceback.extract_stack 实测）：`_generate_if:4089 → _if_generate_normal:14514 → _if_generate_then_branch:21131 → region_ast_generator.py:21080 _process_if_blocks([_r23_or_then], region, 'then')` | **真正的丢边站点 = `region_ast_generator.py:21080`**：or-extension（`A or B` 短路正臂）只把**臂首块**交给臂发射器 ——`blocks=[7668]`——返回 3 条语句 `['Assign','Assign','For']` 即收臂；7972 之后的臂内顺序段既不在本臂序列、又被 ①②③④ 链路的登记判为「已生成」⇒ 整段不发射。同形第二站点 **21099**（无宿主 elif 链的 or-ext 分支）本票未触发。 |

即：B117 的「离开函数的出口边被认成区域内部直落」在 `clock_worker` 上的可执行落点 =
**臂的语句段被缩写成单块列表（21080）**，其上游 enabling 条件 =
**LoopRegion 构造点不携带 exit（5186）**。

## 2. 试用的规则（已实测、终态已回滚）

新增方法 `_or_extension_arm_block_run(arm_entry, arm_blocks)`（置于 `_if_generate_normal` 之前）：
候选集 = 宿主 elif 链首臂成员（`_or_elif_ir.then_blocks`，空则回退 `region.then_blocks`）；
自臂首块起沿**正常后继**（剔除 `exception_successors`）在候选集内做封闭遍历，按 `start_offset` 升序返回；
封闭集外的块（链后续臂、汇合块 8592、回边块 9194、函数尾 sink 9214、handler 入口）一律不进入。
调用点 21080 由 `[arm_entry]` 改为该序列。输入全部在白名单内：块末 opcode、后继/前驱关系、异常边、区域成员关系；
无 depth/数量/语句数上限，无文件名·函数名·偏移特判，无文本后处理，无抑制式发射。
docstring 六项 ①算法依据 ②归约顺序 ③唯一归属判定 ④嵌套处理 ⑤入口引用语义 ⑥反编译流程 + C1/C2/C3 已写全（随回滚一并撤除）。

## 3. 语料翻转（唯一验收信号）与 True-hits

| 靶 | 基线 | 试改态实测 | 翻转 |
|---|---|---|---|
| `site-packages/IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` | 12/13 | **12/13**（`clock_worker` 仍 Different control flow） | **无** |
| `site-packages/IQEngine/utils/profiler_func.pyc` | 17/18 | **17/18** | **无** |

- 规则在 `clock_worker` **确实命中并确实改变了产物**：`persist_flag` 由 0 次出现变 3 次，
  `if persist_flag is False:` 在 `…OK.py:276` 出现；指令序列差量由 **−102 收窄到 −4**，
  真分歧 hunk 数 25→22，`delete orig idx[1054:1154]` 那 100 条整段**不再丢失**。
- 但该单元仍不过：首分歧移到 `idx620 LOAD_CONST <code>`（本轮 §1 已定为伪影豁免），
  真首分歧仍在 `idx667`（orig off5612→**9214** 函数尾 sink vs prod off5614→9082）与
  残留 delete hunks `orig idx[841:857]`、`idx[936:941]`（`if holiday_not_do_before == '0':` 段与
  `system_log.debug('获取重登信号量')` 段）——这两段与本 hunk 不同因，属
  FIX_A_FAMILY §5.1 登记的**臂尾外提（arm-tail hoisting）**残根：交付出来的语句段落在
  函数末尾（prod idx1235–1249）而非臂内位置。⇒ **命中未翻转**。
- `profiler_func`：探针实测 `arm-run calls=0 multi-block=0` ——
  `ProfilerTool.show_func` 的宿主**不走 or-extension 分支**（21080/21099 两处均未触发），
  其 `for range(...)` 尾随段（orig idx[203:223]，off1060）与 B117 同「出口边内吞」之名，
  但站点在**别处**（该函数无 `A or B` 正臂），本票规则不覆盖它。
- 标记 True-hits：**1 次调用 / 1 次多块交付**（`clock_worker`，序列 23 块
  `[7668,7706,7708,7710,7712,7814,7972,7980,8166,…]`）；**flips 0**。
  合成臂 True-hits 0、flips 0（本票未新增臂，也未在既有 37 臂上出现新增命中）。

## 4. 门禁读数（全部为**回滚后终态字节**实测原文；两靶产物均先删后 `pycdc.py` 重生成，无手改）

```
single realtime_event_source   12/13  （基线同值，已复原）
single profiler_func           17/18  （基线同值，已复原）
batch round4/r4_probe_index    71/81 单元  files 27 success / 10 failure / compile_error 0 / error 0   STAY
batch round1/r1_probe_index   108/110 单元  files 44 / 2                                              STAY
batch round1/r1_regress_index  34/34  单元  files 17 / 0                                              STAY
batch round2/r2v3_probe_index 105/126 单元  files 41 / 21                                             STAY
batch round3/r3_probe_index   101/122 单元  files 35 / 21                                             STAY
pins（14，全部 = 基线）quotation 152/153 · handlers 29/30 · trading_dates_mixin 14/14 ·
  stock_position 37/37 · cgroup 8/8 · email 4/4 · calexrights 8/8 · future_contract 29/29 ·
  fly/logger 64/64 · ptradeAccount 137/137 · quote 86/92 · trade_info_utils 37/41 ·
  trade_live_broker 118/128（失败单元仍 quotation.get_fundflow_day / handlers.TWHThreadController._target）
pytest 6 套件   2 failed / 277 passed / 2 xpassed（仍 test_B01_simple_if_then_else_merge、test_BOUNDARY_02_large_function）
import 三模块 OK；python -X utf8 -m compileall -q core OK
未跑：402 语料批（并行会话占机，按工单禁止）。
```

## 5. 回滚与字节完整性 · 插桩残留

```
core/cfg/region_ast_generator.py  3684310 bytes（= 工单事实）/ \n 计数 58668 ⇒ 行数口径 58669 /
                                    前导 BOM 1 / CRLF 58668 / bare LF 0 / ast.parse OK
core/cfg/region_analyzer.py       2045409 bytes / \n 计数 32167（行数口径 32168）/ 1 BOM / bare LF 0 —— 本票全程未改
core/cfg/code_generator.py        未触碰
标记复验（全库计数，与入轮逐条相同）：
  [R2-B106] 4 · [R2-B107] 7 · [R2-B108] 5 · [R3-B115] 1 · [R3-B109] 3 ·
  [R4-B116 sinkexit] 4 · [R5-B100-armjoin-trueentry] 4
插桩残留 grep（终态）：
  grep -c "R5-B117"            core/cfg/region_analyzer.py region_ast_generator.py code_generator.py  → 0
  grep -c "_or_extension_arm_block_run"  同上                                                        → 0
  grep -rn "_or_extension_arm_block_run|_r5_b117|probe[0-9]"  core/ scripts/ test_repros/            → 0
  临时探针 11 个脚本全部位于 D:/Temp/rrv5/，已删除；生产目录零新增文件。
禁止前缀命名新增方法 0；硬编码深度/数量上限 0；文件名·函数名·偏移特判 0；文本后处理 0。
§6.1 的 vestigial 生成端计数器（region_ast_generator.py:2357/2363）本票**未动**，也未据其立规则。
```

## 6. 收窄后的残余（下一票的最窄表述）

1. **B117 在 `clock_worker` 的可执行站点已实名到行**：`region_ast_generator.py:21080`
   （or-extension 正臂只交臂首块）；同形站点 21099（无宿主 elif 链）与 `region_analyzer.py:5186`
   （LoopRegion 构造不带 exit，`_find_loop_else` 的 `natural_exit` 被弃）是 enabling 面。
   单靠 21080 一处改，语句段能出来但**位置在函数末尾** ⇒ 必须与「臂尾交付位置」同修才有翻转。
2. **翻转所需的最小并集** = 本票的臂语句段交付（−102→−4 已证）+ FIX_A_FAMILY §5.1 的
   **臂尾外提**（`if holiday_not_do_before == '0':` 段与 `system_log.debug('获取重登信号量')` 段
   两处 delete hunk 与末尾 replace hunk 同源）。两票并轨是下一手；单独任一票都只能得到「命中未翻转」。
3. **`profiler_func` 与 B117 不同站点**：or-ext 分支 calls=0，其 `for range(...)` 尾随段
   需另找宿主（提示：该函数无 `A or B` 正臂，应在 `_if_generate_then_branch`/`_loop_generate_body`
   的臂序列侧，而非 21080）。
4. **出口边身份在分析端已算出但未被携带**（`natural_exit` → `LoopRegion.exit` 缺字段传递），
   这是 C3「出口块被区域外路径引用须显式认领」的结构性缺口；若要根治需在构造点补 `exit=natural_exit`
   并逐针复验（本票未做，属高影响面改动）。
