# FIX_B116_ANALYZER — 短路链「多出口 sink」折叠拒绝（analyzer 侧认领判据）

结论标记：**「代码已落地」**（`core/cfg/region_analyzer.py` 已改，7 个整文件单元翻绿，全套电池与 14 pins 无回退）。
判定 = 唯一判据 `scripts/pyc_verify.py`（ruler sha256 `9c7567bd6776b36b`，interpreter 3.11.7），全程未改判据。
产物一律「删除 + `python -X utf8 pycdc.py -o <base>OK.py <pyc>`」重生成，无手编 `*OK.py`。

---

## 1. 折叠的因（2-3 句）

`if A: if not B: body`（函数/臂尾，CPython 3.11 为每条短路出口各建一个
`LOAD_CONST None; RETURN_VALUE` 块）里，两个操作数块的末指令都是
`POP_JUMP_FORWARD_IF_FALSE`/`POP_JUMP_FORWARD_IF_TRUE`，`_detect_boolop_conditional_chain`
照收为 and/or 链、`_boolop_resolve_merge` 把 **最后一名成员的跳转目标 off122** 当作 merge，
于是 `[R4-B116]` 之前唯一的创建点 `_create_boolop_region_from_chain` 建出一个
只有一个 merge 的 `BoolOpRegion` —— 第一条出口 off118 被 IfRegion 认作 else 臂，
第二条出口 off122 掉成 `parent=None` 的孤儿 BASIC 区域，发射端只发一对 None-return（−2）。

关键事实（探针实测）：**b01（嵌套 if）与 b03（扁平 `if A and not B:`）的字节码逐指令相同**
—— 两者都产生 off118/off122 两个互不相同的终结 sink 块。因此「折叠成 BoolOp」在源形上
不可辨识、且在出口为 sink 时必然丢一对块；而**发射嵌套 if 与发射扁平 boolop 编译回同一字节串**，
所以拒绝折叠既语义正确又零损失。

## 2. 落地点（唯一标记 `[R4-B116 sinkexit]`，全在 `core/cfg/region_analyzer.py`）

1. 新增判据 `_boolop_chain_exits_are_distinct_sinks(chain)`（紧邻创建点之前）：
   链长 ≥2；每个成员末指令属 `SHORT_CIRCUIT_JUMP_OPS ∪ FORWARD_CONDITIONAL_JUMP_OPS`
   且目标块可解析；目标块集 **≥2 个互不相同**；**每个**目标块都
   `succ==[]`（终结）且 `_check_block_has_trailing_return_none`（隐式 `return None` 尾）。
   只读块末 opcode、后继集、隐式 return None 尾部 —— 无名字/偏移/深度/宿主类型门控。
2. 消费点：`_create_boolop_region_from_chain` 创建前的第三道不变量门（与 R14b、R38 同位），
   判真即 `return None` —— 链不建区域，成员块保持未认领，交后续 IfRegion 逐层语句级归约。
   该方法是 `BoolOpRegion` 的**唯一**创建点（`_identify_boolop_regions` 的 6 个调用点全经此），
   故 C3 守卫封闭、无旁路。
3. 为被触碰的 `_create_boolop_region_from_chain` 补齐 ①–⑥ + C1/C2/C3 docstring（原文无 docstring）。
4. `region_ast_generator.py` / `code_generator.py` **字节未动**。死计数器 `_trailing_rn_exit_count`
   （`:2357`/`:2363`）**未删**：本工单的判定在 analyzer 侧认领阶段生效，不消费该计数，
   也未使其成为可证明的遗迹（仍 2 处命中、0 读取点）。

## 3. 孤儿 / `parent=None` 与 predecessor 证据（before → after）

标本 `r4v3_b01_nested_not_method` / 真靶
`site-packages/IQEngine/data/trading_dates_mixin.pyc <module>.TradingDatesMixin.trading_dates_reload`
（同形，块偏移一致），探针 `D:/Temp/rrv4/pp1.py` 原文：

| 态 | 区域事实 |
|---|---|
| before（继承自 round4/FIX_B99_B116.md §4，本轮未重跑旧码） | `BoolOpRegion(BOOL_OP) entry=off0 blocks=['off0','off16'] merge_block=off122 op_chain=[(off0,'and'),(off16,'or')] parent=IfRegion`；`IfRegion entry=off0 blocks=['off0','off30','off118'] then=['off30'] else=['off118']`；**`Region(BASIC) entry=off122 blocks=['off122'] parent=None`**（第二对 sink 无归属） |
| after（本轮实测，trading_dates_reload 与 b01 一致） | `IfRegion entry=off16 blocks=['off16','off30','off122'] then=['off30'] else=['off122'] parent=IfRegion@off0`；`IfRegion entry=off0 blocks=['off0','off16','off30','off118','off122'] else=['off118'] parent=None`；`BoolOpRegion` **不再产生**；**off122 的 `parent=None` 孤儿消失** |

predecessor 复原（块级，真靶原文）：`off118 succ=[] preds=['off0'] trn=True`、
`off122 succ=[] preds=['off16'] trn=True` —— 两条出口各持**一个**前驱、各属**一个** owning region。
产物片段由 `if not (self.pre_flag and self.upd_flag): …; return None; else: return None`
（边 off14 被改投 →30、off122/124 整对消失）变为

```python
if self.pre_flag:
    if not self.upd_flag:
        self._dates = self.engine.cal.get()
        self.upd_flag = True
        return None
```

handlers 的 `off404 preds[13]` / `off408 preds[2]` 目标形态**未达成**（见 §6）。

## 4. True-hits 与翻转（判据确实 fire，且 fire 换来翻转）

插桩 `D:/Temp/rrv4/hit_b116.py`（monkeypatch 计数，不改生产码）：

| 文件 | 判据调用 | 判真（=拒绝折叠） | 该文件的翻转 |
|---|---|---|---|
| `trading_dates_mixin.pyc` | 2 | **1**（off0） | **13/14 → 14/14** ✅ |
| `stock_position.pyc` | 2 | **2**（`make_trade` 塌两对 ⇒ 两条子链各判真） | **36/37 → 37/37** ✅ |
| `handlers.pyc` | 4 | 1（off412） | 29/30 → 29/30（残余另轴，§6） |
| `quotation.pyc` | 54 | **0** | 152/153 → 152/153（非同机制，§6） |
| `r4v3_b01` | 1 | 1 | **2/3 → 3/3** ✅ |
| `r4v3_b03` | 1 | 1 | **翻绿** ✅ |
| `r4v3_b05` | 1 | 1 | **翻绿** ✅ |
| `r4v3_b06` | 1 | 1 | **翻绿** ✅ |
| `r4v3_b08` | 2 | 2 | **翻绿** ✅ |
| 新增 `r4v3_b12_three_sink_and_chain` | 2 | 2 | 新臂 3/3 绿 |
| 新增 `r4v3_b13_or_head_nested_tail_sink` | 1 | 0 | 新臂 2/2 绿 |
| 新增 `r4v3_b14_converging_exit_control` | 1 | 0 | 新臂 3/3 绿（出口收敛 ⇒ 正确保留 `and` 折叠） |

合计：裁决文件集上 **72 次调用 / 12 次判真**，造成 **7 个整文件翻绿**
（2 个语料靶 + 5 个 r4 B 族臂）与 **0 个新红臂**。唯一「fire 而未翻」的是 handlers 的
off412（该文件翻绿需要第二把锁，§6）。

## 5. 全套电池 + pins 实测原文（重生成产物后）

| 项 | 基线（本轮入轮实测） | 落地后 | 要求 |
|---|---|---|---|
| `r1_probe_index` | 108/110, 44 success / 2 failure | **108/110, 44/2**（红集不变：`handler_ifelse`=B101、`r1_73`） | 108/110 ✅ 无回退；**`r1_73` 未翻**（其残余是 try-else 认领轴，见 FIX_B99_B116 §3） |
| `r4_probe_index`（入轮 31 臂） | 51/67, 15/16 | **56/67, 20/11**（+5 整文件，0 新红） | 基线 51/67, 15/16 已复现 |
| `r4_probe_index`（+3 新臂 = 34 臂） | — | **64/75, 23 success / 11 failure** | 新臂全绿 |
| `r1_regress_index` | 34/34 | **34/34** ✅ | STAY 34/34 |
| `r2v3_probe_index` | 105/126, 41/21 | **105/126, 41/21** ✅ | STAY |
| `r3_probe_index` | 101/122, 35/21 | **101/122, 35/21** ✅ | STAY |
| `trading_dates_mixin` | 13/14 | **14/14** ✅ | 靶 1 |
| `handlers` | 29/30 | **29/30**（未闭） | 靶 2 未达成 |
| `stock_position` | 36/37 | **37/37** ✅ | 靶 3 |
| `quotation` | 152/153 | **152/153**（非同机制） | 靶 4 未达成 |
| pins 14 single | — | cgroup 8/8、email 4/4、calexrights 8/8、future_contract 29/29、fly/logger 64/64、ptradeAccount 137/137、executor 10/10、history_api 19/19、quote 86/92、trade_info_utils 37/41、trade_live_broker 118/128、strategy 26/27、api_base(IQData) 27/28、matcher 16/17 | 全部逐条不变 ✅（另有 `IQEngine/api/api_base.pyc` 49/49） |
| pytest 6 文件 | 2 failed / 277 passed / 2 xpassed | **2 failed, 277 passed, 2 xpassed**（同两条：`TestDominanceFrontierIf::test_B01…`、`TestBoundaryConditions::test_BOUNDARY_02…`） | ✅ |
| import 三模块 + `compileall core` | OK | **OK** | ✅ |

语料 4 靶合计 units：**230/234 → 232/234**（trading_dates_mixin +1、stock_position +1；
其余两靶读数不变）。

## 6. 未翻两靶的残余（下一手最窄靶点，附证据）

1. **`handlers.pyc <module>.TWHThreadController._target`（B99 原锚）**：本判据在该单元
   确有 1 次 fire（off412 的 `sys.version_info[0]==3 and …[1]==11` 链，出口 off1012/off1016/off1020
   三 sink 互异 ⇒ 折叠被拒），但 off404/off408 **不是 BoolOp 链成员**：`off90`
   （`while self.running` 顶测，false→off408）与 `off390`（`POP_JUMP_BACKWARD_IF_TRUE` 底测，
   fall-through→off404）是**同一个 LoopRegion 的两条出口**，末指令一为 forward-conditional、
   一为 backward-conditional，不在任何短路链里。`LoopRegion entry=off90 blocks=[…,'off390','off404','off408'] else_blocks=['off408']`
   —— **off404 既不在 body_blocks 也不在 else_blocks**，故永不进入 `_generate_block_statements`
   （与 FIX_B99_B116 §5 的实测一致）。残余最窄靶点 = `region_analyzer` 的 LoopRegion 出口认领：
   循环「顶测 false 出口」与「底测 fall-through 出口」为两个不同终结隐式 return None 块时，
   各给一个 owning role（原则2/原则4），而非只把 else_blocks 收一个。
   对照实验：CPython 3.11 编译 `if o.a: while o.running: o.g()` 时两条出口**汇入同一块**，
   本原形分叉成两块 ⇒ 认领阶段必须显式承认双出口。
2. **`fly/data/quotation.pyc <module>.get_fundflow_day`（B102）**：54 次判据调用
   **0 次判真**，其分歧是 `POP_JUMP_IF_FALSE off196→268 vs →272` 与 `FOR_ITER off202→272 vs →268`
   **两条边目标互换**（REVIEW §表格 B102 行），属边重定向/循环出口轴，不是 sink 折叠轴。
   未做任何特例。

## 7. 排除清单（本轴已证否/已证的边界）

- **不能**用「短路目标必须同一 merge」这类宽判据：`if a or b:` 型链的合法成员目标本就各异
  （or 的 true 边跳 body、and 的 false 边跳 value 块），b13（or 头 + 嵌套尾 sink）实测判真 0 次、
  保持折叠语义正确。宽判据会打掉 b14/quote 一类现绿臂。
- **不需要**在 generator 侧做任何 trailing-return-None 消费：折叠一旦在认领阶段被拒绝，
  两条出口的 sink 各自成为 IfRegion 的 else/then 块，既有发射路径自然复原两对
  `LOAD_CONST None + RETURN_VALUE`。前四张工单的 0-flip 正因此。
- 拒绝折叠后 b03（源本就是扁平 `and`）也翻绿 —— 证明「嵌套 if 与扁平 boolop 在双 sink 形态下
  编译回同一字节串」，故本判据不引入语义/字节损失，只是把不可辨识的源形统一到**可完整发射**的一侧。

## 8. 字节与标记核验（无 git）

- `core/cfg/region_analyzer.py`：入轮 2030385 B / 31979 行 → 落地 **2037812 B / 32073 行**
  （+94 行：判据方法 + 两道注释/门 + `_create_boolop_region_from_chain` docstring）；
  1 个前导 BOM、`raw[3:]` 内无第二个 BOM、`CRLF==LF==32073`（全 CRLF，含新写入区）、`ast.parse` OK。
- `core/cfg/region_ast_generator.py`：**3684310 B / 58669 行 / 1 BOM** —— 逐字节未动。
- 标记实测：`[R2-B106`=4、`[R2-B107`=7、`[R2-B108`=5、`[R3-B115`=1、`[R3-B109`=3、
  `r3-b100-armjoin`=8（**全部存活**）；新增 `[R4-B116 sinkexit]`=4（方法 docstring 1、门注释 1、
  被触碰方法 docstring 内 2），`_boolop_chain_exits_are_distinct_sinks`=2（def + 唯一消费点 ⇒ 计数确被读取）。
- 禁止名实测：`_fix_/_patch_/_fallback_/_hack_/_workaround_/_temp_` 新增 0 处；无硬编码深度/计数上限、
  无函数名/文件名/偏移特例、无文本后处理。
- `test_repros/round4/r4_probe_index.json`：31 → **34 臂**（新增 b12/b13/b14，全绿）；
  早轮索引与 `REVIEW.md` 未改。所有被重生成产物（r1/r1_regress/r2/r3/r4/pins/4 靶）均由
  删除 + `pycdc.py -o` 重跑得到。
