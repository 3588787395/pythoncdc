# R71 FIX3 — 两族候选交付读数（F-EXCTABLE / F-ASSERT）

工作区 `D:/Temp/opencode/r71gate/fix3`；镜像根 `D:/Temp/opencode/r71gate/center`；
repo `F:/Downloads/pythoncdc-main` 全程只读（HEAD `a31d3f79`，基线 R70 `b21c5c61`）。
本文件只记录实测读数与判据，不复述 BRIEF。

---

## 0. 交付物

| 文件 | 内容 |
|---|---|
| `specs/R71-exctable.json` | 候选一·生成器侧：`core/cfg/region_ast_generator.py`，2 edits，+34 行 |
| `specs/R71-exctable-analyzer.json` | 候选一·分析器侧：`core/cfg/region_analyzer.py`，2 edits，+59 行 |
| `specs/R71-analyzer-merged.json` | 上面两份里**分析器**改动的合并件（5 edits，+80 行），供组合臂一次落盘 |
| `specs/R71-assert.json` | 候选二：`core/cfg/region_analyzer.py`，3 edits，+21 行 |
| `mk_spec_f3.py` | spec 生成 + 三重自检（anchor 命中=1、anchor 非注释行必须在 repl 中保留、patched 全文件 `compile()` 通过） |
| `mbuild71.py` | 多 spec 镜像构建（每 spec 一个 file；同 file 两 spec 会拒绝并要求合并） |
| `synth/` `synth_mandated.py` `run_synth.py` `sweep_synth.py` | 合成复现与判据 |
| `regdump2.py` `etdiff.py` | 区域树 / 异常表 A/B 探针（`regdump2.py` 用 `dis`，在函数内局部导入） |
| 本文件 | `FACTS.md` |

臂名：`f3a`（exctable 全量 = gen + ana）、`f3b`（assert）、`f3ab`（两者合并）、
`f3g`（仅 gen，归因用）、`f3n`（仅 ana，归因用）。

---

## 1. 根因复核

### 1.1 F-EXCTABLE 单元① `fly_api/base.pyc::SplitOrder.parse_time_info`（生成器侧）

指令流 144/144 全同，异常表两端被撑大（`etdiff.py` 实测）：

```
orig    66..118 -> 158        264..316 -> 356
landed  66..156 -> 158        264..354 -> 356     SAME=False
```

根因与 DIAG1 §3.2 一致：`_generate_try_body`（`region_ast_generator.py:24173`，
调用点 `:26152`）的 expression-children 循环（`:25177`，handler 跳过 `:25183-25186`）
把 else 臂里的表达式子区域当 try 体消费 → `self.generated_blocks` 被污染 →
orelse 门 `:26587` 虽触达，但循环 `:26615-26616` 的 `eb in self.generated_blocks → continue`
前置条件成立 → `:27010 if orelse_stmts:` 拿不到内容 → `try_ast['orelse']` 缺键。
分析器侧该单元本就 `has_else=True`（无需改）。

### 1.2 F-EXCTABLE 单元② `IQData/entry.pyc::IQDataEntry.get_instance`（分析器侧）

**此处与 DIAG1 §3.2 的宣称不同，按实测纠正。** DIAG1 §3.2 把两支并成同一根因
（`has_else=True`、`else_blocks=[114,118,148,150]`、生成器标记污染）；实测 `get_instance`
是**分析器根本没认出 else**：

```
orig    202..760 -> 830   760..828 -> 1130      # try 体 + else（else 被 finally 保护）
landed  202..828 -> 830                         # else 被并进 try 体      SAME=False
f3g     202..828 -> 830      (仅 gen 改动)       SAME=False   ← 生成器改了也没用
f3n     202..760 -> 830   760..828 -> 1130       SAME=True    ← 仅分析器改动即转绿
f3ab    同 f3n                                    SAME=True
```

区域树（`regdump2.py`，`TryExceptRegion@202`）：

| 臂 | `else_blocks` | `try_blocks` 含 760/828 |
|---|---|---|
| landed / `f3g` | **无**（`has_else=False`） | 是 |
| `f3n` / `f3ab` | `[760, 828]` | 否 |

阻塞点（两条，均在 `_find_try_else_blocks` 链路上）：

1. `_try_body_terminates_abnormally`（`region_analyzer.py:10487`，被 `:10613` 调用）
   扫描 try 体时，被 else 自己的 `return`（block 828，`exception_successors=[]`）误判为
   异常终止 → 直接不认 else。
2. `_is_pass_or_return_none_block` 过滤：block 828 只有 `RETURN_VALUE`。

**归因读数**（`mandated = scripts/pyc_verify.py single`，逐 pyc 与逐 arm）：

| arm | entry.pyc | base.pyc |
|---|---|---|
| landed | 4/5 | 61/63 |
| `f3g`（仅 gen） | 4/5 | **62/63**（parse_time_info 转绿） |
| `f3n`（仅 ana） | **5/5** | 61/63 |
| `f3a` | **5/5** | 62/63 |
| `f3b` | 4/5 | 62/63（OverNightOrder 转绿） |
| `f3ab` | **5/5** | **63/63** |

结论：F-EXCTABLE 两个单元**分别落在生成器侧与分析器侧**，所以该族 spec 必须成对提交。

### 1.3 F-ASSERT 单元 `fly_api/base.pyc::OverNightOrder.__init__`

```
orig    insts=188  exc=[260..710 -> 714, 714..922 -> 922]
landed  insts=165  exc=[260..656 -> 656, 656..864 -> 864]   SAME=False
f3ab    insts=188  exc=[260..710 -> 714, 714..922 -> 922]   SAME=True
```

根因与 DIAG1 §3.4 一致：链式比较 assert 的失败中转块的 `successors` 含
「指向 try handler 入口的异常边」，`region_analyzer.py:15259 / 15303 / 15331`
三处 `succs = list(cur.successors)` 未剔除该边 → `len(succs) != 1` →
`_reach_assertion_error_block` / `_find_assertion_error_block` /
`_reaches_block_via_fallthrough` 全部提前返回失败 → `_identify_assert_regions`
不产 `AssertRegion` → 条件块退化为 `IfRegion` + 独立 `raise AssertionError` →
`LOAD_GLOBAL AssertionError` ≠ `LOAD_ASSERTION_ERROR`，指令数 165 ≠ 188。

---

## 2. 两候选的三要素判据（与 spec 内注释同文）

### 候选一 F-EXCTABLE — `specs/R71-exctable.json`（生成器侧，2 edits）

1. **识别条件（同层次结构身份）**：本 `TryExceptRegion` 自身 `has_else` 为真且持有
   `else_blocks`，而其**直接的**表达式子区域（Ternary/BoolOp 等 `_EXPR_REGION_TYPES`）
   的 `entry` 落在**本区域自己的 else 块集**内 ⇒ 该子区域属于 else 臂，不属于 try 体。
   判据与同函数既有的 `_06_handler_block_set` handler 归属分支同型：父区域用自己的
   臂块集判定自己的直接子区域，不跨层。
2. **归约方式 / 检查位置**：`region_ast_generator.py` `_generate_try_body` 的
   expression-children 循环（`:25177` 附近），命中即 `continue`——不发射、不登记
   `self.generated_blocks` / `_generated_regions`，子区域连同其块原样交回 orelse 门
   （`:26587` / `:26615-26616` / `:27010-27011`）按既有次序发射恰好一次。
3. **明确不读**：异常表 offset 区间数值、`eb.start_offset` 具体值、try/except 名称、
   阈值、名字白名单、新增 `self` 状态、跨层 `region.entry in r.blocks` 型模式。

### 候选一 F-EXCTABLE — `specs/R71-exctable-analyzer.json`（分析器侧，2 edits）

**edit0（收窄 try 体扫描集，`_try_body_terminates_abnormally` 内）**

1. **识别条件**：try 体成员 = 异常边指向**本区域自己** `handler_entry_blocks` 的块，
   以及从这些「受本区域 except 句保护」的块沿 `successors` 向前、只经过
   `exception_successors` 为空（CPython 不给不可抛指令登记异常表条目）的块所能到达的
   `try_blocks` 成员；被**别的目标**保护的块（如同一 try 语句的 finally 入口）立即截断。
2. **归约方式**：受保护前向闭包。仅在收窄结果非空时替换扫描集合，否则保持原集合与原行为；
   下方 `RETURN`/`JUMP_BACKWARD`/`JUMP_FORWARD` 判据逐条不变。
3. **不读**：异常表 offset 数值、块 offset 常量、阈值、名字白名单、新增 `self` 状态、跨层比较。

> 这一版判据是**被实测逼出来的**：最初的天真版「只保留 `exception_successors ∩ handler` 的块」
> 会把没有 finally 的 try 体内 `return` 尾块（CPython 把 RETURN 排除在保护区间外）一并滤掉，
> 导致 `IQCommon/api/klinedata.pyc` **43/45 → 41/45 回归**
> （新增 `get_kline_by_count`、`get_kline_by_date_one`），违反 ADR-1。
> 拆分定位：`klinedata` 上 gen 单独 = 43/45（干净），ana 仅 edit0 = 41/45（回归源），
> ana 仅 edit1 = 43/45（干净）。改成「受保护前向闭包 + 空集合不收窄」后
> `f3a / f3n / f3ab` 全部回到 **43/45 = landed**，回归消除。

**edit1（else 尾块闭包，`_identify_try_except_regions` 内）**

1. **识别条件**：与已认定 else 块链相邻（前驱在本区域自己已认定的 else 块集内）、
   位于「最后一个 else 块之后、本区域第一个 handler 入口之前」、非 handler 块、
   仍在 `region.try_blocks` 中、且唯一有效指令以 `RETURN` 结尾。
2. **归约方式**：仅在 `else_blocks` 非空时追加进 `else_blocks`。
3. **不读**：偏移常量、阈值、名字白名单、新增 `self` 状态、跨层比较。
   **注意**：只改局部 `try_blocks` 变量，**不写回 `region.try_blocks`**（edit1 依赖其含尾块）。

### 候选二 F-ASSERT — `specs/R71-assert.json`（3 edits）

1. **识别条件（同层次结构身份）**：`cur.exception_successors` 是 CFG 依据异常表登记的
   「本块 → try handler 入口」异常边集合；**它不是 fall-through 边**。
2. **归约方式 / 检查位置**：`region_analyzer.py:15259`（`_reach_assertion_error_block`）、
   `:15303`（`_find_assertion_error_block`）、`:15331`（`_reaches_block_via_fallthrough`）
   把 `list(cur.successors)` 换成 `list(cur.conditional_successors)`
   （`core/cfg/basic_block.py:91-93`：`successors - exception_successors`）。
   剔除后恰为 1 才继续追踪；剔除后为 0 或 >1 仍按原样返回失败——
   **只放宽「被异常边撑成 2 后继」这一种情形**，普通双后继条件块不受影响。
3. **不读**：异常表 start/end/target 数值、block offset 数值、函数/文件名、
   `depth<8` 之外的阈值、名字白名单、新增 `self` 状态、跨层 `region.entry in r.blocks` 模式。

---

## 3. step a–e 全读数

### step a — 构建（锚点断言全过）

```
mbuild71.py f3a   specs/R71-exctable.json specs/R71-exctable-analyzer.json
  patched region_ast_generator.py  edits=2 lines=+34  BOM=True
  patched region_analyzer.py       edits=2 lines=+59  BOM=False
mbuild71.py f3b   specs/R71-assert.json
  patched region_analyzer.py       edits=3 lines=+21  BOM=False
mbuild71.py f3ab  specs/R71-exctable.json specs/R71-analyzer-merged.json
  patched region_ast_generator.py  edits=2 lines=+34  BOM=True
  patched region_analyzer.py       edits=5 lines=+80  BOM=False
（head 镜像字节 == worktree、candidate CRLF 计数/BOM/行数插入量三项断言全过）
```

### step b — 22 靶 A/B（h62 官方 byte-diff 口径，跑前删旧 jsonl）

| arm | TALLY | MOVED |
|---|---|---|
| `f3a` | `SAME=20 IMPROVED=0 REGRESSION=0 MOVED=2 ERR=0` | `entry.pyc`、`base.pyc` |
| `f3b` | `SAME=21 IMPROVED=0 REGRESSION=0 MOVED=1 ERR=0` | `base.pyc` |
| `f3ab` | `SAME=20 IMPROVED=0 REGRESSION=0 MOVED=2 ERR=0` | `entry.pyc`、`base.pyc` |

**REGRESSION=0（ADR-1 满足）**；`files fully matched a=14 b=14`。
`IQCommon/api/klinedata.pyc` 三臂均 **43/45 = landed**（回归已消）。

### step b' — mandated 读数（`scripts/pyc_verify.py single`，官方 ruler 看不到异常表差异）

| pyc | landed | f3a | f3b | f3ab |
|---|---|---|---|---|
| `IQData/entry.pyc` | 4/5 `get_instance` fail | **5/5** | 4/5 | **5/5** |
| `...fly_api/base.pyc` | 61/63 `OverNightOrder`+`parse_time_info` fail | 62/63（仅 `OverNightOrder` fail） | 62/63（仅 `parse_time_info` fail） | **63/63** |

### step c — 金丝雀（h62 16 位 sha，四臂逐支比对）

| 文件 | 期望 | landed | f3a | f3b | f3ab | 官方读数 |
|---|---|---|---|---|---|---|
| `fly/common/market_time.pyc` | `af77224b34b203c4` | 同 | 同 | 同 | 同 | 10/10 |
| `IQCommon/util/datetime_func.pyc` | `e711b8ea86d49a15` | 同 | 同 | 同 | 同 | 26/26 |
| `IQData/utils/datetime_func.pyc` | `9d09af09249da177` | 同 | 同 | 同 | 同 | 25/25 |
| `fly/data/quotation.pyc` | `4d41187e356544e0` | 同 | 同 | 同 | 同 | **143/143** |

`ALL CANARY SHA MATCH: True`（三臂 sha 与期望值逐字相同）。

### step d — battery（`closeout69.py battery landed f3ab`）

`repro pycs discovered: 82 (round63 batches + 11 pinned R62 witnesses)`
→ **`candidate columns worse-than-landed on 0 repro(s)`**
（82 行 landed/f3ab 两列读数逐行相同，含 4 个已知遗留 bad>0 的复现，均未变化。）

### step e — strict（`sstrict67.py`，22 靶清单）

| 臂 | ok / functions | defects |
|---|---|---|
| `build_landed` | 952 / 1006 | **54** |
| `build_f3ab` | 953 / 1006 | **53** |

缺陷集合 diff：**NEW in f3ab = 0**；FIXED by f3ab = 1
（`base.pyc <module>.OverNightOrder.__init__ seq_len orig=172 decomp=148`）。
无新增缺陷函数、无新增 `target_diff`。

> 口径说明：strict 比较不含异常表，所以 `entry.get_instance` / `parse_time_info`
> 在 landed 下本就不算 strict 缺陷（`entry.pyc` landed 已是 5/5）；两族的判定必须走
> mandated `pyc_verify.py`，strict 只作「无新增缺陷」的护栏。

---

## 4. 合成咬合（`synth_mandated.py`：反编译 → 回编译 → 比 `co_code` + `dis._parse_exception_table`）

| 形状 | landed | f3a | f3b | f3ab |
|---|---|---|---|---|
| `t24_assert_in_try`（F-ASSERT+，DIAG1 钉死） | red | red | **OK** | **OK** |
| `t15_assert_then_unreachable`（F-ASSERT−） | OK | OK | OK | OK |
| `t27_try_except_else_range`（F-EXC+，DIAG1 钉死） | red (`extable`) | **OK** | red | **OK** |
| `t20_two_try_except_seq`（F-EXC−） | OK | OK | OK | OK |
| `ex_try_noelse`（F-EXC−，本轮新增） | OK | OK | OK | OK |
| `as_assert_outside`（F-ASSERT−，本轮新增） | OK | OK | OK | OK |
| `e_e5_finally` / `e_e7_kline_like`（本轮新增） | OK | OK | OK | OK（未复现缺陷，净中性） |
| `ex_else_ternary` / `ex_else_return`（本轮新增） | red | red | red | red → **known-unfixed #2** |
| `as_assert_in_try` / `a_a1_return` / `a_a4_classmethod`（本轮新增） | red | red | red | red → **known-unfixed #1** |

四条负对照在四臂全部 OK ⇒ 两候选均未引入新缺陷形状。

---

## 5. known-unfixed（如实列出，不修）

### #1 重复 `AssertRegion` 吞掉链式比较的前缀赋值

- 现象：`try` 内「直线前缀 + 链式比较 assert」（如 `h = int(hour); m = int(minute);
  assert 0 <= h < 24; assert 0 <= m < 60; return ...`）在任何臂上产物都缺
  `h = int(hour)` / `m = int(minute)` 两条语句（`insts 62 → 54`）。
- 根因：`region_analyzer.py:14865` 的守卫
  `if isinstance(self.block_to_region.get(block), AssertRegion): continue`
  **只挡 AssertRegion**；而链式比较的第二段块已被 `TryExceptRegion` 登记，
  `:15018`/`:15028` 的 `if cb not in self.block_to_region` 又因此**不再登记**，
  于是该块在循环中再次通过判定，产出与 `AssertRegion@4` **块集重叠**的
  `AssertRegion@80`（实测 `AssertRegion@4 blocks=[4,80,94]` 与
  `AssertRegion@80 blocks=[80,94]` 并存），父序列的 `_generate_assert`
  前缀移交路径被重叠区域打乱，前缀语句无人发射。
- 只有 `assert` 在 try 外时该冲突不存在（`as_assert_outside` OK）。
- 不影响两个 mandated 单元（`t24` 与 `OverNightOrder.__init__` 形状不含该前缀，
  实测 `f3b`/`f3ab` 均转绿）。

### #2 else 尾语句成孤儿块，整条被丢弃

- 现象：`ex_else_ternary` 的 else 含 `label = ... ; text = label`，产物丢掉
  `text = label`（`insts 33 → 31`），并把函数尾的 `return text` 吞进 else。
- 根因：该直线尾块（offset 82–86）**不属于任何区域**——
  `TryExceptRegion@4.blocks = [0,4,70,74,78,80,88,120,126,130,132]` 不含 82，
  顶层也无 `Region@82`；orelse 循环只遍历 `else_blocks=[70,74,78,80]`，
  孤儿块从未被发射。
- 与 F-EXCTABLE 的两处改动正交（改前改后读数相同），且不是异常表问题
  （是 `bytecode` 差异），不属于本族 mandated 单元。

---

## 6. 结论

- 两候选各自达成 BRIEF 指定目标，且**互相独立**（`f3a` 只动两支 exctable，
  `f3b` 只动 assert 单元，归因臂 `f3g`/`f3n` 进一步把 exctable 拆到生成器/分析器各半）。
- `REGRESSION=0`、金丝雀 4/4 sha 逐字相同、battery `worse-than-landed=0`、
  strict 缺陷集合 `NEW=0 / FIXED=1`。
- 建议中心**采纳两候选**（组合落盘即 `specs/R71-exctable.json` +
  `specs/R71-analyzer-merged.json` 中 exctable 部分 + `specs/R71-assert.json`，
  实测组合臂 `f3ab` 使 `base.pyc = 63/63`、`entry.pyc = 5/5`）。
- 两条 known-unfixed 属于相邻缺陷，建议另立 change 处理。
