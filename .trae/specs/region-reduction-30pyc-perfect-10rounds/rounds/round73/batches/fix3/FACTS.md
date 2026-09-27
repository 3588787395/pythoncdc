# R73 · fix3 FACTS —— 四族端到端读数（F-TERNARY / F-EXCTABLE / F-POLARITY / F-OTHER）

工作区 `D:/Temp/opencode/r73gate/fix3`；repo `F:/Downloads/pythoncdc-main` 全程只读（未改/未提交/未 `--apply`）。
基线 HEAD = `8d136040`（R72）。镜像臂前缀 `surg*`（fix3 专用），本批产出
`surg1 ternary`、`surg2 exctable`、`surg3 polarity`、`surg4 quote`、合并臂 `surgm`。
所有读数为本工作区实测原始输出，存 `dump/`，中心可复跑复核。

---

## 1. 四族根因与状态总表

| 族 | 对象 | 根因（同层结构身份判据，无名字/偏移/阈值启发） | spec | 臂 | 状态 |
|---|---|---|---|---|---|
| F-TERNARY | `IQEngine/core/bar.py` `BarData.limit_up` / `limit_down` | `return X if C else Y` 的两条值路径汇聚到**同一个** `RETURN_VALUE` 终结块，且该块的直接入边前驱恰为 true/false 两块（CPython 求值完 IfExp 只发一次 RETURN）。原实现用 `_block_is_return_body` 无条件拒绝该形态；语句级 if/elif-return 的两个 RETURN 块彼此独立、出口不共享，仍走原拒绝路径 | `specs/ternary.json`（+34 行） | surg1 / surgm | **已修** |
| F-EXCTABLE | `IQEngine/core/commission.py` `CommissionHelp.set_commission` | R21N1 把「try_offset_end 之后、以 RETURN_VALUE 终结、全部普通前驱落在 try 保护跨度内」的块收归 try 体；若该块**含写指令**（`STORE_SUBSCR`/`STORE_ATTR`/`DELETE_SUBSCR`/`DELETE_ATTR`），CPython 必然把该 try 的异常表条目向后延伸（实测 `try: d[k]=v` 覆盖 STORE_SUBSCR），故含写指令 ⇒ 该块位于 try 语句**之后**，属 try/except/else 的 else 分支 | `specs/exctable.json`（+32 行） | surg2 / surgm | **已修** |
| F-POLARITY | `IQEngine/api/api_base.py` `get_history` | `if (A and not B) or C:` 链首 A 的假出口指向**下一个条件段 C** 而非 then 体：C 与 B 的真出口在同一块汇合、B 的跳转目标才是真 then。`_identify_conditional_regions` 的 or 链行走（`region_analyzer.py:16848-16957`）用首块跳转目标当 `_then_entry_offset`（:16873），把 B 当末段收链、把 C 当 then 入口 → region then/else 取错、条件折成 `A or include` | `specs/polarity.json`（+31 行）+ `specs/polarity_gen.json`（+32 行） | surg3 / surgm | **已修** |
| F-OTHER-1 | `fly/data/quote.py` `Quote.check_industry_code` | `assert <or-chain>, msg` 为函数**最后一条语句**时，CPython 为每个操作数发独立隐式 `LOAD_CONST None; RETURN_VALUE` exit 块（两个指令流完全相同的出口块），`_detect_assert_boolop_chain` 的 `p_target is not end_target` 块身份判据（:15257）失败 → AssertRegion 只覆盖末操作数，退化成 `if not A: assert B, M` | `specs/quote.json`（+20 行） | surg4 / surgm | **已修** |
| F-OTHER-2 | `fly/data/quote.py` `Quote.load_get_price` | `TernaryRegion@0 blocks=[0,112,142,144]` 吞掉 block144（144–282 连续直线段，含 f-string 尾 + `len(panel.major_axis)!=0` 条件跳 282→486），而该块同时是后续 `if len(panel.major_axis)!=0:` 的条件块 → 后者无法成 IfRegion，条件退化为孤立表达式（产物 `quoteOK.py:446`）、body 被上提。对应 diag1 提案 #7（`_process_if_blocks` :21530 / `_if_generate_normal` :17753） | — | — | **未打补丁**（根因已钉死，补丁形态与可复现 synth 未做） |

本轮**新达标 mandated failure→success**：`IQEngine/api/api_base`（get_history）、`IQEngine/core/commission`（set_commission）；
另有 3 个失败单元清零：`BarData.limit_up`、`BarData.limit_down`、`Quote.check_industry_code`。

---

## 2. 合并臂 `surgm`（ternary+exctable+polarity+quote 四 spec 合并）a–e 全闭环

构建：`mbuild73.py surgm specs/merged_analyzer.json specs/polarity_gen.json`
→ `core/cfg/region_analyzer.py` 4 edits **+117 行**、`core/cfg/region_ast_generator.py` 3 edits **+32 行**；
锚点断言全过、BOM/行尾保持（analyzer 无 BOM、generator 有 BOM、均为 CRLF 基）。

### a. 构建
通过（上）。

### b. 靶支读数（mandated = `scripts/pyc_verify.py single <pyc> --source <OK.py>`；官方 = `h62.py run`）

六靶 mandated（`dump/mandated_surgm.txt`，landed 基线同表左列）：

| 靶 | landed | surgm | 变化 |
|---|---|---|---|
| `IQEngine/core/bar` | failure 82/85（limit_up / limit_down / `_history_bars`） | failure **84/85**（仅 `_history_bars`） | **-2 失败单元** |
| `IQEngine/core/commission` | failure 9/10（set_commission Different bytecode） | **success 10/10** | **failure→success** |
| `IQEngine/api/api_base` | failure 48/49（get_history cf） | **success 49/49** | **failure→success** |
| `IQData/api/api_base` | failure 27/28（get_history_df cf） | failure 27/28 | 不变 |
| `fly/data/quote` | failure 80/92（12 fails） | failure **81/92**（11 fails） | **-1 失败单元**（check_industry_code） |
| `plugin_system_trade/trade_live_broker` | failure 114/128（14 fails） | failure 114/128 | 不变 |
| **合计** | **360/392（32 个失败单元）** | **365/392（27 个失败单元）** | **+5 单元 / 0 新增失败** |

全量 402 支官方尺（`dump/surgm_all402.jsonl` vs `dump/all402_landed.jsonl`，`h62 ab`）：
`TALLY SAME=398 IMPROVED=0 REGRESSION=0 MOVED=4 ERR=0`，`files fully matched a=394 b=394`，
读数 **5746/5717 = 99.50% 与基线逐项相同**（4 个 MOVED 仅 sha 变、mism 集合 gained=[] lost=[]）。

### c. 金丝雀（`dump/canary_surgm.jsonl`）
quotation `3eb76e512df9ab1e`、market_time `af77224b34b203c4`、IQCommon datetime_func `e711b8ea86d49a15`、
IQData datetime_func `9d09af09249da177` —— **4/4 与 pin 相同**（且 4/143、10/10、26/26、25/25 官方读数不变）。

### d. battery（`dump/batt_surgm.txt`）
`python -X utf8 closeout69.py battery landed surgm` → **`candidate columns worse-than-landed on 0 repro(s)`**。

### e. strict（`dump/strict_all402_surgm.json`）
`STRICT TOTAL ok=6131 / functions=6207 / defects=76`（基线 landed `ok=6127 / defects=80`）；
按 `(pyc, 函数名)` 比对：**`NEW_DEFECT_FUNCTIONS=0`，`FIXED=4`**
（`<module>.get_history`、`<module>.BarData.limit_up`、`<module>.BarData.limit_down`、`<module>.Quote.check_industry_code`）。

---

## 3. 单臂读数（各自 a–e 摘要）

| 臂 | spec | b（mandated 靶支） | c 金丝雀 | d battery | e strict（对 landed） |
|---|---|---|---|---|---|
| surg1 | ternary +34 | bar 82/85 → **84/85** | 4/4 不变 | worse-than-landed=0（`batt_cmp_surg12.txt`） | `new_defects=0 fixed=2`（limit_up/limit_down） |
| surg2 | exctable +32 | commission 9/10 → **10/10 success** | 4/4 不变 | 同上 | `new_defects=0 fixed=0`（strict 口径下 set_commission 本就不在缺陷集） |
| surg3 | polarity +31 / gen +32 | IQEngine api_base 48/49 → **49/49 success**；其余 5 靶 mandated 逐项不变 | 4/4 = pin（`dump/canary_surg3.jsonl`） | worse-than-landed=0（`dump/batt_surg3.txt`） | `ok=6127→6128`，`new_defects=0 fixed=1`（`<module>.get_history`） |
| surg4 | quote +20 | quote 80/92 → **81/92**（check_industry_code）；其余 5 靶不变 | 4/4 不变 | worse-than-landed=0（`dump/batt_surg4.txt`） | `new_defects=0 fixed=1`（`Quote.check_industry_code`） |
| **surgm** | 上述合并 | 见 §2，**+5 单元 / 0 新增失败 / 3 支 status=success** | 4/4 = pin | **0** | **`new_defects=0 fixed=4`** |

各臂官方 6 靶读数与 landed 完全相同（`h62 ab`：SAME=5、MOVED=1（mism 同集）、REGRESSION=0）——
官方尺本就不 flag 这几个单元，靶支改善只体现在 mandated 尺上。

---

## 4. F-POLARITY 根因链与最小复现

**编译形态差**（`_polsbs.py` / `_polcgen.py` 实测，CPython 3.11.7）：

- `if A or B:` → A `IF_TRUE→then`，B `IF_FALSE→else`，B fall→then。
- `if not A or B:` → A `IF_FALSE→then`（R13c 已收），B 同上。
- `if (A and not B) or C:` → A `IF_FALSE→C`，B `IF_FALSE→then`，B fall→C，C `IF_FALSE→else`，C fall→then。
  **首块跳转目标是「下一个条件段」而非 then 入口。**

**判据（同层结构身份）**：候选 then 入口块自身是条件跳尾块、且其 fall-through 正是当前末段的跳转目标
（两者真出口汇合）⇒ 候选 then 入口仍是条件段，链继续延伸，并把 `_then_entry_offset` 前移到当前末段的真出口后重新行走。
判据只读本链相邻三块的后继关系；对 `if A or B:`（候选 then 入口非条件块）与 `if A or B: if C:`
（C 的 fall-through 是其自身 then 体、不等于链末跳转目标）**零行为变化**（§4 synth 三个 control 全 0 diff 印证）。

**生成端**：链成员「末跳目标落在更靠后链成员上」⇒ 链不是平铺 or，按该跳把链切成连续组，
组内沿用原极性规则（假出口 → then 的支取反，R61 In/NotIn 不取反），组间为 or ⇒ `BoolOp(or, [BoolOp(and,[A, not B]), C])`；
无此类成员时切出唯一组、走原平铺 `BoolOp(or, _main_parts)`，既有用例逐字节不变。
`_cidiff`（orig pyc vs 产物）：`IQEngine/api/api_base.get_history` **134 instr、2 行差异 → 0 行**。

**synth**：`synth/polarity_andor.py`（2 trigger + 4 control）→ `dump/polarity_andor.pyc`，读数 `dump/pol_synth_cidiff.txt`：

| 函数 | landed | surgm |
|---|---|---|
| `trig_mixed_or` | 3 diff（产物 `if not A or B: if C: ... else ...`） | **0 diff**（产物 `if A and not B or C:`） |
| `trig_mixed_or_body` | 3 diff | **0 diff** |
| `ctrl_plain_or` / `ctrl_not_or` / `ctrl_nested_body` | 0 | 0 |
| `ctrl_and_group`（`if (A and B) or C:`） | 5 diff | 5 diff（**与基线一致，非本轮引入**，见 §5） |

---

## 5. 移交项与未决项

1. **F-OTHER-2 `Quote.load_get_price`（未打补丁）**：根因已钉死（TernaryRegion 吞并后续 if 的条件块 144，
   `_cidiff` 显示 orig/产物各 171 instr、**仅 1 行**差异 index58 `POP_JUMP_FORWARD_IF_FALSE(to 486)` vs `POP_TOP`）。
   需要的改动方向：`_process_if_blocks` / `_identify_ternary_regions` 不把「同时是后续条件块的共享块」收进 TernaryRegion，
   或允许 conditional 识别声明该 entry。**补丁形态 + 可复现 synth 未做。**
2. **`BarData._history_bars`（F-ABSORB 族）**：surg1 后仍剩的唯一 bar 失败单元，属 fix2 范围，移交 fix2。
3. **`IQData/api/api_base.get_history_df`**：103 行 `_cidiff` 差异，**不是** F-POLARITY（surg3 前后完全一致、
   landed=103 行），属另一族（控制流重排，候选 F-ABSORB / F-PAD），移交对应批次。
4. **`if (A and B) or C:`（synth `ctrl_and_group`）**：landed 与 surgm 均 5 行差异，产物退化成
   `if not (A and B): return 1; return 2`（**丢掉 `or C` 操作数**）。既有缺陷、本轮未引入也未修复，记录为
   F-POLARITY 邻近的开口（and 组无 `not` 时 or 链未建，条件被整体取反）。
5. 全量 mandated 402 扫描按纪律**归中心**（本轮只跑 6 靶 mandated + 402 官方尺 + 402 strict）。

---

## 6. 产物清单

- spec：`specs/ternary.json`、`specs/exctable.json`、`specs/polarity.json`、`specs/polarity_gen.json`、
  `specs/quote.json`、`specs/merged_analyzer.json`（4 合 1，+117）。
- synth：`synth/assert_or_tail.py`（F-OTHER-1，4 trigger/3 control，landed 4 FAIL → mirror 全 7 PASS）、
  `synth/polarity_andor.py`（F-POLARITY，2 trigger/4 control）。
- 读数（`dump/`）：`mandated_surg3.txt`、`mandated_surgm.txt`、`mandated_surg12.txt`、`mandated_surg4.txt`、
  `fix3_targets_surg3.jsonl`、`fix3_targets_surgm.jsonl`、`fix3_targets_landed3.jsonl`、
  `canary_surg3.jsonl`、`canary_surgm.jsonl`、`batt_surg3.txt`、`batt_surgm.txt`、`batt_cmp_surg12.txt`、
  `surg3_all402.jsonl`、`surgm_all402.jsonl`、`strict_all402_surg3.json`、`strict_all402_surgm.json`、
  `pol_synth_cidiff.txt`、`pol_s3_api_base.py`、`pol_landed_api_base.py`。
- 工具：`_mkpolarity.py`、`_mkpolgen.py`、`_mkmerged.py`、`_poldec.py`（按镜像臂反编译单 pyc）、
  `_mkmand.py` / `_mand_<arm>.py`（mandated 六靶对比）、`_strictcmp3.py`、`_polrun.py`、`_mksynthpol.py`。
