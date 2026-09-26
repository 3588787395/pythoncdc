# R71 · fix2 — F-THENOVER / F-ABSORB 事实书

- repo `F:/Downloads/pythoncdc-main`（只读，HEAD = R70 `b21c5c61`）
- 工作区 `D:/Temp/opencode/r71gate/fix2`，镜像/产物在 `D:/Temp/opencode/r71gate/center`
- 交付结论：**建议中心采纳 `specs/r71f2_full.json`**（补测后见 §7；`specs/r71f2_safe.json` 为保守备选）
  - 初次交付曾判 **NONE**（按 §1.c 字面：quotation sha 不恒等）；中心就「真实转绿」例外发起补测，
    补测**支持**该主张（§7），故结论改写为建议采纳——改写依据与读数全部落在 §7。

---

## 1. 根因复核（DIAG1 §3.1 复核通过）

`core/cfg/region_ast_generator.py::_process_if_blocks`（def `:21468`）在**分支/循环帧**内
错误认领**兄弟区域**的 merge 块：

1. **guard `:22445-22450`**（现 5 条）第 (5) 条 `merge_block is None and exit is None`
   是历史为保 `fly/data/quotation.pyc::get_trend` 金丝雀逐字节而**故意收窄**的
   （注释见 `:22420-22421`）——它挡住了 t01/t02 一族（header 认领）。
2. **认领动作 `:22451-22465`** 会把兄弟区域的 merge 块记进当前帧的
   `generated_blocks / generated_offsets`，使后续共享语句被吸进当前分支，
   跳转落点从近端 merge 变成远端 end（F-ABSORB / F-THENOVER）——t22 一族。

调用链与同型判据位置同 DIAG1（`ra-gen:21694-21704 _fis_is_ancestor_merge`、
`ra-gen:21745-21753`）。analyzer 侧无过错。

---

## 2. 交付候选（两份，均带 `[R71-thenover]` 三要素注释）

### 2.1 `specs/r71f2_safe.json` — 1 处编辑，净 +42 行（臂 `r71f2s`）

在 `_process_if_blocks` 的认领动作前加**影子认领**：

- **识别条件**（全部为同层结构身份，无函数名/文件名/偏移常量/阈值/名字白名单/新增 self 状态）：
  本帧 `region.merge_block` 同时满足
  (a) 不是本帧区域的后代（`_region` 父链上没有 `entry` 相等的节点），
  (b) 不是任何已分析区域的 `entry`（非 header），
  (c) 不大于候选区域 `blocks` 的最大偏移（isLast），
  (d) 属于候选区域的 `else_blocks`，
  (e) 位于候选区域 `blocks` 内，
  (f) 不是候选区域自己的 `entry`。
- **归约方式**：生成前把该 `merge_block` 预标记为 `generated`（影子认领），
  生成结束后若非原先已标记则撤销标记，并在随后的 `blocks` 标记循环里跳过它。
- **AST 映射**：共享尾语句留在兄弟区域不被当前帧吸收，
  该帧的跳转落点从远端 end 收回近端 merge（F-THENOVER / F-ABSORB）。

锚点自检（`mbuild71.py r71f2s specs/r71f2_safe.json`）：
```
patched core/cfg/region_ast_generator.py   edits=1 lines=+42 bytes 3199517 -> 3202448 BOM=True
mirror ready: D:/Temp/opencode/r71gate/center/mirr_r71f2s
```

### 2.2 `specs/r71f2_full.json` — 2 处编辑，净 +41 行（臂 `r71f2f`）

= 2.1 **加上** guard 第 (5) 条放宽（`_e1_dropcond5`）：

- **识别条件**：在 loop 帧（`self._current_loop is not None`）内处理一个无 `parent`
  的顶层区域，且当前块正是该区域的 `entry` 块（去掉原先额外要求的
  `merge_block is None and exit is None` 两条）。
- **归约方式**：对直接 `continue`，不走常规的块生成/认领路径。
- **AST 映射**：header 块不单独落语句，其后的共享语句留在外层帧，
  外层 `if` 的跳转落点保持近端 merge 而不被吸进 then 分支（F-THENOVER）。

锚点自检（`mkfinal71.py r71f2 …` + `mbuild71.py r71f2f …`）：
```
core/cfg/region_ast_generator.py   edits=2 lines=+41  ->  r71f2_region_ast_generator.py.json
    sources: _e1_dropcond5.json, _e17.json
patched core/cfg/region_ast_generator.py   edits=2 lines=+41 bytes 3199517 -> 3203033 BOM=True
mirror ready: D:/Temp/opencode/r71gate/center/mirr_r71f2f
```

> 注释是后补的（BRIEF §1.4 要求）。补注释后重建 `mirr_r71f2f / mirr_r71f2s` 并重跑 all56：
> **56/56 产物与补注释前的 `build_f2e17c / build_f2e17` 逐字节 sha256 相同**
> （`build_r71f2f` ⊆ `build_f2e17c`，`build_r71f2s` ⊆ `build_f2e17`，diff=[]），
> 因此下列全部读数对带标签的交付 spec 同样成立。

---

## 3. a–e 读数

### 3.1 `r71f2_full`（2 编辑）

| 门槛 | 结果 | 证据 |
|---|---|---|
| a 构建 | **PASS** | `mbuild71` 锚点断言全过（上） |
| b-h62 ab | **PASS** | `TALLY SAME=48 IMPROVED=0 REGRESSION=0 MOVED=8 ERR=0`（8 支 MOVED 全部 `gained=[] lost=[]`） `dump/ab_r71f2f.bin` |
| b-mandated | **PASS（改善）** | 56 靶 `pyc_verify single` OK 单元 **2049 → 2055（+6）**，**0 新增失败单元**、变差文件 0 `dump/pv56_{landed,r71f2f}_{a,b}.txt` |
| c 金丝雀 | **PASS（经中心裁定补测）** | 3/4 与 R70 逐字节相同；quotation sha `4d41187e356544e0 → 3eb76e512df9ab1e`，但官方 **143/143 mism=[] 不变**、mandated `get_trend` failure→success、recompile 跳转实测与原 pyc 一致 → 判定**真实转绿**（举证见 §7） `dump/canary_r71f2f.jsonl` |
| d 电池 | **PASS** | `candidate columns worse-than-landed on 0 repro(s)` `dump/battery_r71f2.bin` |
| e 严格尺 | **PASS（改善）** | `ok=2164→2170`，`defects=87→81`，**0 新增缺陷函数**；改善文件 `wizard_quant_api / quotation / load_daily / klinedata / quote` `dump/strict_{landed_all56,r71f2f}.json` |
| §1.6 合成咬合 | **PASS** | t01 ✓ t02 ✓ t22 ✓ = **3/3**；负对照 t03 仍 failure、t04 仍 success `dump/synthcheck_r71f2f.txt` |

mandated 修复的 6 个单元（全部在目标族内，0 新增）：
```
wizard_quant_api.pyc  <module>.init_stock_pool_filter     54/58 -> 55/58
quotation.pyc         <module>.get_trend                  151/153 -> 152/153
load_daily.pyc        <module>.filter_abnormal_data       25/27 -> 26/27
klinedata.pyc         <module>.get_history_common         59/64 -> 61/64
klinedata.pyc         <module>.get_price_common           (同上)
quote.pyc             <module>.Quote.run_tick_transform   79/92 -> 80/92
```

### 3.2 `r71f2_safe`（1 编辑）

| 门槛 | 结果 | 证据 |
|---|---|---|
| a 构建 | **PASS** | `mbuild71 r71f2s` |
| b-h62 ab | **PASS** | `TALLY SAME=54 IMPROVED=0 REGRESSION=0 MOVED=2 ERR=0`（MOVED：`matcher`、`realtime_event_source`，均 `gained/lost=[]`） `dump/ab_r71f2s.bin` |
| b-mandated | **PASS（持平）** | 56 靶 OK 单元 **2049 → 2049**，0 增 0 减。直接实测于臂 `f2e17`（`dump/pv56_f2e17_{a,b}.txt` 与 landed 行级完全相同），`r71f2s` 的 56 产物经 sha256 证与 `f2e17` 逐字节相同 |
| c 金丝雀 | **PASS** | 4/4 sha 与 R70 逐字节相同：`4d41187e356544e0 / af77224b34b203c4 / e711b8ea86d49a15 / 9d09af09249da177`；quotation 官方 143/143；quotation/market_time 产物文本与 landed `cmp` 为空（sha256 验证） `dump/canary_r71f2s.jsonl` |
| d 电池 | **PASS** | `candidate columns worse-than-landed on 0 repro(s)`（表内含 r71f2f/r71f2s 两列） `dump/battery_r71f2.bin` |
| e 严格尺 | **PASS（持平）** | `ok=2164 / defects=87`，0 改善 0 新增 `dump/strict_r71f2s.json` |
| §1.6 合成咬合 | **FAIL（1/3）** | 仅 t22 ✓；t01 `get_trend`、t02 `filter_abnormal` 仍 failure `dump/synthcheck_r71f2s.txt` |

---

## 4. 关键发现：被钉住的 quotation sha 是**字节码错误**的产物

t01 源码注释自证：`# F-THENOVER (get_trend / quotation cf2)`，即 t01 是
`fly/data/quotation.pyc::get_trend` 的最小复刻，两者区域树同构 →
**任何纯区域结构判据必然同时命中**（这是 §1.c 与 §1.6 互斥的结构性原因）。

而这一支金丝雀本身是错的：

- 原始 `quotation.pyc::get_trend` 字节码：`LOAD_FAST fields; POP_JUMP_FORWARD_IF_FALSE to 206`
  —— `if fields` 为假时跳到 **206 = `if date:` 测试**（`if date:` 在 `if fields:` **之外**）。
- **landed** 产物重编译：同位置是 `POP_JUMP_FORWARD_IF_FALSE to 220`（跳过整个 `if date:` 块，
  差值 14 字节 = `if date` 块大小）→ 与原字节码**不一致**。
- `pyc_verify single` 因此对 landed quotation 报
  `units=151/153  ***<module>.get_trend: Failure: Different control flow`。
- `r71f2_full` 臂：`units=152/153`（`get_trend` 消失，只剩历史遗留的 `change_his_to_forward`），
  且其 `get_trend` 指令序列与原 pyc **逐条完全一致**（`dis` 比对 `identical_to_orig = True`；
  landed = `False`，唯一差异就是上面那个跳转目标）。
- 两臂 quotation 产物文本 diff = **恰好 1 个 hunk**：`if date:` 缩进 8 → 4。

> 同时暴露仪器口径问题：h62 的 `matched_functions` 对 landed quotation 报 `143/143 mism=[]`，
> 而 mandated `pyc_verify` 报 `151/153` —— **h62 会漏掉这一类真实控制流分歧**，
> 同类漏报还包括 `strategy_universe._on_clear_de_listed`（h62 报 11/11 matched，
> 但 E16 臂把 `de_listed.add(o)` 提到了 `if i` 外层，语义更差，mandated 判 failure）。

---

## 5. 为什么安全臂修不了 t01/t02（结构性不可修）

- **E1**（单独放宽 guard 第 5 条）：t01 ✓ t02 ✓，但 quotation sha
  `4d41187e356544e0 → 3eb76e512df9ab1e` → 按 §1.c「整件候选作废」（`dump/canary_f2e1.jsonl`）。
- **E17**（单独影子认领）：4/4 sha 恒等，但 t01/t02 仍 failure（该族 mb == 候选 entry，
  被 (f) `mb is not _region.entry` 排除）→ §1.6 只有 1/3。
- 判据只看区域树，而 t01 与 quotation::get_trend 的区域树**同构**
  （`IfRegion@0` 的 `merge_block` == 候选 entry，196 / 206）→
  没有任何同层结构身份能区分二者；区分只能靠函数名/阈值/文件名，全部为 BRIEF 明令禁止。

---

## 6. 被否决候选清单

| 实验 | 判据增量 | 否决理由 |
|---|---|---|
| E1 | 放宽 guard 第(5)条 | quotation sha 变（§1.c） |
| E2 | branch 帧 defer 非后代替选 | quotation 143→141、t22/t29 退化 |
| E8 | 无条件影子屏蔽帧 merge | quotation 141/143、market_time 9/10、t03 h62 2/2→1/2 |
| E9 | + `merge_block in _region.blocks` | 与 E8 读数完全相同，回归未消 |
| E10 | + `merge is not _region.entry` | 同上 |
| E11 | + 「候选不是本帧后代」父链测试 | quotation 142/143（`change_his_to_forward` 回归） |
| E12 | + 「mb 不是任何区域 entry」header 测试 | all56 `REGRESSION=1`（quote 72/81→71/81，新增 `get_stock_status`） |
| E13 | null 影子（探针对照） | 证明 E12 回归确由影子引起；quote 回到 72/81 |
| E14 | E12 + 祖先链按 **entry 相等** | REGRESSION=0 但 3 支指标恶化（`get_history_df` jump_diffs 11→126 等） |
| E16 | E14 + isLast | 指标恶化消失，但 `strategy_universe._on_clear_de_listed` 语义被证伪（字节码 ground truth），verifier 报 11/11 是漏报 |
| **E17 / r71f2_safe** | E16 + inElse | 见 §3.2 —— a–e 全过、金丝雀恒等，**仅 §1.6 1/3 不达标** |
| **r71f2_full** | E17 + 放宽 guard | 见 §3.1 + §7 —— §1.6 3/3、a/b/d/e 全过且有实质改善；quotation sha 变动经中心裁定补测判为**真实转绿**（官方 143/143 不变、mandated `get_trend` 转绿、recompile 跳转与原 pyc 一致），**最终采纳** |

### 56 靶 probe 的结构证据（E14）
全 56 靶上命中的 17 处影子，**全部 `samePar=True`**（帧与候选恒为同 parent 的兄弟）——
「同 parent」无区分力；真正的区分力来自 (c) isLast + (d) inElse 的组合（E16/E17）。

---

## 7. 中心裁定补测（针对「quotation sha 变动 = 真实转绿」的举证）

臂 = `r71f2f`（`specs/r71f2_full.json`）。旧 jsonl 全部先删除再重跑，python 侧写文件。

### 7.1 quotation 官方尺

```
python -X utf8 h62.py run --arm=landed --list=canary.txt --out=dump/canary_landed.jsonl
python -X utf8 h62.py run --arm=r71f2f --list=canary.txt --out=dump/canary_r71f2f.jsonl
python -X utf8 h62.py ab --a=dump/canary_landed.jsonl --b=dump/canary_r71f2f.jsonl
```
```
landed  quotation.pyc 143/143 []
r71f2f  quotation.pyc 143/143 []
MOVED  fly/data/quotation.pyc  gained=[] lost=[]
TALLY SAME=3 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0  (unpaired lists=0)
```
**结论：quotation 官方仍 143/143，mism=[]，gained/lost 均空，REGRESSION=0。**

### 7.2 quotation mandated（`pyc_verify.py single`，两臂同命令逐单元对照）

```
python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single \
  F:/Downloads/pythoncdc-main/site-packages/fly/data/quotation.pyc \
  --source <build_臂>/fly__data__quotationOK.py
```

| | landed | r71f2f |
|---|---|---|
| 读数 | `status=failure units=151/153 success_rate=98.69%` | `status=failure units=152/153 success_rate=99.35%` |
| 失败单元 | `<module>.change_his_to_forward`、`<module>.get_trend` | `<module>.change_his_to_forward` |

逐单元增减（`dump/pv_quo_{landed,r71f2f}.txt`）：

- **failure → success（1 个）**：`<module>.get_trend`
- **success → failure（新增，必须 0）**：**0 个**
- 不变 failure：`<module>.change_his_to_forward`（历史遗留，与本候选无关）

### 7.3 产物逐行 diff

`build_landed/fly__data__quotationOK.py` vs `build_r71f2f/fly__data__quotationOK.py`
（`dump/quo_landed_vs_r71f2f.diff`）：

- 两文件均 3692 行；
- **仅 1 个 hunk、共 4 个变更行**，全部落在 `get_trend` 尾部：
  ```
  -        if date:
  -            params['date'] = date
  +    if date:
  +        params['date'] = date
  ```
- 其余 3688 行逐字相同 → **除 `get_trend` 相关 hunk 外无任何其它变化**。

### 7.4 关键跳转实测（recompile 后的 code object，非源码文本）

用 `marshal` 读原 pyc、`compile()` 编两臂产物，取 `get_trend` code object，
定位 `LOAD_FAST fields` 之后的 `POP_JUMP_FORWARD_IF_FALSE`，读其 **实测目标偏移** 与**目标处指令**：

| 来源 | 该跳转实测目标 | 目标处指令 | `api_get` 所在偏移 | 指令总数 |
|---|---|---|---|---|
| **原 pyc** `fly/data/quotation.pyc` | **206** | `LOAD_FAST date` | 220 | 67 |
| **landed** 产物重编译 | **220** | `LOAD_GLOBAL api_get` | 220 | 67 |
| **r71f2f** 产物重编译 | **206** | `LOAD_FAST date` | 220 | 67 |

逐条序列比对（`(opname, argrepr)` 全表）：

```
landed==orig : False      # 唯一差异：POP_JUMP_FORWARD_IF_FALSE 'to 206' -> 'to 220'
r71f2f==orig : True       # 67/67 指令完全一致
```

**结论：`r71f2_full` 的 `get_trend` 重编译字节码与原 pyc 逐条一致；
landed 的重编译字节码与原 pyc 不一致（假分支跳过了 `if date:`）。**
即原 pin `4d41187e356544e0` 锁定的是一个与原 pyc 控制流不符的产物，
`3eb76e512df9ab1e` 才对应正确产物。

### 7.5 其余 3 支金丝雀（r71f2f 臂逐支复测）

| 支 | r71f2f sha | R70 pinned | 结论 | 官方读数 |
|---|---|---|---|---|
| `fly/common/market_time.pyc` | `af77224b34b203c4` | `af77224b34b203c4` | **SAME** | 10/10 mism=[] |
| `IQCommon/util/datetime_func.pyc` | `e711b8ea86d49a15` | `e711b8ea86d49a15` | **SAME** | 26/26 mism=[] |
| `IQData/utils/datetime_func.pyc` | `9d09af09249da177` | `9d09af09249da177` | **SAME** | 25/25 mism=[] |
| `fly/data/quotation.pyc` | `3eb76e512df9ab1e` | `4d41187e356544e0` | CHANGED（§7.1–7.4 裁定为真实转绿） | 143/143 mism=[] |

### 7.6 全套 a–e 最终读数（全部直接跑在 `r71f2f` 臂上）

| 门槛 | 读数 | 证据 |
|---|---|---|
| a 构建 | `edits=2 lines=+41`，锚点断言全过 | `mbuild71 r71f2f specs/r71f2_full.json` |
| b-h62 ab（56 靶官方） | `SAME=48 IMPROVED=0 REGRESSION=0 MOVED=8 ERR=0`，8 支 MOVED 全部 `gained=[] lost=[]` | `dump/ab_r71f2f.bin` |
| b-mandated（56 靶，直接重跑） | OK 单元 **2049 → 2055（+6）**，**新增失败单元 0**，变差文件 0 | `dump/pv56_{landed,r71f2f}_{a,b}.txt` |
| c 金丝雀 | 3/4 与 R70 逐字节相同；quotation sha 变但官方 143/143 且 §7.1–7.4 证实为转绿 | `dump/canary_r71f2f.jsonl` |
| d 电池 | `candidate columns worse-than-landed on 0 repro(s)`（82 repro × 3 列） | `dump/battery_r71f2.bin` |
| e 严格尺 | `ok=2164→2170`、`defects=87→81`，**0 新增缺陷函数** | `dump/strict_r71f2f.json` |
| §1.6 合成咬合 | **t01 ✓ t02 ✓ t22 ✓ = 3/3**；负对照 t03 仍 failure、t04 仍 success | `dump/synthcheck_r71f2f.txt` |

mandated 56 靶 +6 单元明细（新增失败 0）：

```
+ <module>.get_trend                quotation.pyc         151/153 -> 152/153
+ <module>.filter_abnormal_data     load_daily.pyc         25/27  -> 26/27
+ <module>.get_history_common       klinedata.pyc          59/64  -> 61/64
+ <module>.get_price_common         klinedata.pyc          (同上)
+ <module>.Quote.run_tick_transform quote.pyc              79/92  -> 80/92
+ <module>.init_stock_pool_filter   wizard_quant_api.pyc   54/58  -> 55/58
```

### 7.7 补测是否推翻原结论

**部分推翻，已改写。** 原 §7（现 §8）判 NONE 的唯一依据是 §1.c 的字面
「quotation sha 与 R70 不逐字节相同 → 整件候选作废」。补测证明：

1. 官方尺 143/143 与 landed 完全相同、`gained/lost=[]`、`REGRESSION=0`；
2. mandated `get_trend` **failure→success，0 新增**；
3. 产物 diff 仅 `get_trend` 一 hunk，无其它变化；
4. **recompile 后的跳转目标**：原 pyc=206、landed=220、`r71f2f`=206，
   且 `r71f2f` 指令序列与原 pyc **67/67 完全一致** → 旧 pin 锁定的才是错的；
5. 另 3 支金丝雀 sha 全部 = R70 pinned。

即该 sha 变动属于「真实转绿而非回退」，落入中心裁定的例外。
**结论改写为：建议中心采纳 `specs/r71f2_full.json`（配套：把
`fly/data/quotation.pyc` 的 pin 重钉为 `3eb76e512df9ab1e`）。**

---

## 8. 结论与需要的配套

**采纳建议：采纳 `specs/r71f2_full.json`（2 处编辑，臂 `r71f2f`）**，附 §7 裁定证据。

其读数汇总：a ✓ / b ✓（h62 `REGRESSION=0`，mandated +6 单元 0 新增）/
c △（3/4 逐字节相同，quotation 为**经裁定的真实转绿**，官方 143/143 不变）/
d ✓（0）/ e ✓（缺陷 87→81，0 新增）/ §1.6 ✓（t01/t02/t22 = 3/3，负对照不变）。

**需要的配套（中心动作，1 项）：**

- 把 `fly/data/quotation.pyc` 的金丝雀 pin 从 `4d41187e356544e0`
  重钉为 `3eb76e512df9ab1e`。依据见 §4 与 §7.4：旧 pin 对应的重编译字节码
  `POP_JUMP_FORWARD_IF_FALSE to 220`，与原 pyc 的 `to 206` 不一致（mandated 亦判 failure）；
  新 pin 对应的产物与原 pyc 逐条一致。
  （等价替代：把该支判据从「字节恒等」改为「mandated 读数不降 + 官方读数不降」。）

**若中心不接受重钉** → 退回 **`specs/r71f2_safe.json`**（1 处编辑，臂 `r71f2s`）：
a–e 全过、4/4 金丝雀逐字节相同、全尺度 0 回归，但 §1.6 只有 1/3（仅 t22）、
56 靶 mandated 2049→2049（0 增 0 减）、strict 87→87。**不建议**——
它会为一个合成用例改动 `matcher` 与 `realtime_event_source` 两个真实文件
却换不来任何真实单元收益（§9.1/§9.2 的附带改动分别为「等价」与「同错不同形」）。

---

## 9. 遗留（建议另开一轮）

1. `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc::clock_worker`
   的 `time.sleep(FPS)` 归属：原 pyc 字节码显示 4 个条件（`now_date==before`、`now_date>after`、
   `delay_after_trading>=now_time`、`now_time>=after_trading`）的假分支**全部**汇到同一个
   sleep 块（`8924/8946/8962/8972 → 9144`），语句体则 `9142 → 9194` 跳过它。
   实测三种源形态中只有**平铺形态**
   `elif B1 and B2 and C1 and C2: body else: time.sleep(FPS)` 与之匹配；
   landed 的「内层 else」与 safe/full 臂的「外层 else」**都不是** ground truth
   （CPython 3.11 实测：内层 else → 条件假时跳过 sleep；外层 else → 内层假时跳过 sleep）。
   两臂在 mandated/strict/h62 上读数完全相同（均报 `clock_worker: Different control flow`），
   属**同错不同形**、无回归；但要真正修好需要改 if/elif 的发射形态。
2. `plugin_system_matcher::DefaultMatcher.match`：safe/full 臂把
   `if A: … continue; if B:` 改成 `elif B:` 并把不可达的 `while False: pass` 外提一层。
   因 A 分支必以 `continue` 结束，`if`/`elif` **语义等价**；`while False` 恒不可达。
   判定：中性。
3. `strategy_universe._on_clear_de_listed`：现有 verifier（h62 matched_functions、
   `pbv.bytecode_diff`）对「指令数不同但报 matched」的函数过松，需要更严的口径。

---

## 10. 证据索引

- specs：`specs/r71f2_full.json`、`specs/r71f2_safe.json`（实验件 `specs/_e*.json`）
- 合并/构建：`mkfinal71.py r71f2 …`、`mbuild71.py r71f2{f,s} …`
- 金丝雀：`dump/canary_{landed,r71f2f,r71f2s,f2e1}.jsonl`
  （`h62 ab canary_landed vs canary_r71f2f` → `TALLY SAME=3 REGRESSION=0 MOVED=1 gained/lost=[]`）
- synth：`dump/synthcheck_{landed,r71f2f,r71f2s,f2e1,f2e17,f2e17c}.txt`
- mandated 56 靶：直接臂 `dump/pv56_{landed,r71f2f}_{a,b}.txt`；
  实验臂 `dump/pv56_{f2e17,f2e17c}_{a,b}.txt`
- quotation 裁定（§7）：`dump/pv_quo_{landed,r71f2f}.txt`（mandated 单支）、
  `dump/quo_landed_vs_r71f2f.diff`（产物逐行 diff，1 hunk / 4 行）、
  recompile 跳转实测见 §7.4 表
- h62 ab：`dump/ab_{r71f2f,r71f2s,f2e17,f2e17c}.txt/.bin`，jsonl `dump/*_56.jsonl`，
  基线 `center/dump/landed56_r71.jsonl`
- 电池：`dump/battery_r71f2.bin`（`closeout69.py battery landed r71f2f r71f2s`，
  82 个 repro × landed/r71f2f/r71f2s 三列，`candidate columns worse-than-landed on 0 repro(s)`）
- 严格尺：`dump/strict_{landed_all56,r71f2f,r71f2s}.json`（`sstrict67.py`），
  `ok=2164/2170/2164`，`defects=87/81/87`
- 逐处影子日志：`dump/shadow{,12,14,16}.log`；探针 `probe.log`
- 字节码 ground truth：`dump/quotation_landed_vs_e1.diff`，
  原 `fly/data/quotation.pyc::get_trend` 与 `realtime_event_source.pyc::clock_worker` 的 `dis` 输出
- 合成源：`D:/Temp/opencode/r71gate/diag1/synth/t0{1,2,22}*.py`
