# Round 8 — REVIEW_NOP.md：单条行追踪 NOP 是否为一个族？（诊断，零生产改动）

判据：`python -X utf8 scripts/pyc_verify.py`（single / batch --index），未改动。
尺子：`compare_pyc` sha256(16)=`9c7567bd6776b36b`，解释器 3.11.7。
本轮只做：重生成产物 → 指令流对照 → 合成标本 → grep 定位站点。**未改 core/、pycdc.py、scripts/、任何 \*OK.py（语料侧产物仅由 pycdc 重生成）。**

---

## 0. 结论（先说答案）

1. **flytools 的那条 `NOP` 不是缺陷本体，而是「反编译器多写的显式 `return None`」的行追踪脚印（footprint）。**
   CPython 把 `with` 出口块（`__exit__(None,None,None)` + 紧随的 `LOAD_CONST None; RETURN_VALUE`）整块
   归属到 `with` 语句那一行；若函数的**最后一条语句是 `return`**，该 `return` 自己那行就没有任何指令可挂，
   汇编器便补一条 `NOP <line=return行>` 让 trace 能报出该行。**只有当 `return` 写在 `with` 体内才会出现。**
2. **一条孤立 NOP 不会让判据失败**（`r8nop_01` 实测：产物比原码恰好多 1 条 NOP、其余全是 +2 位移，判据 **success 2/2**）。
   ⇒ 「纯 NOP 残差」在本语料里根本不构成失分原因，**不存在一个可以靠"少发一条 NOP"翻案的族**。
3. **15 个仍然失分的单元里，NOP-shaped = 0**；带「+1 条野生 NOP」脚印的 = **2**（`flytools.modify_batcktes_info`、
   `function.reconnect`），带「NOP 丢失」脚印的 = 1（`quote.run_individual_transform`，但它同时 −53 条指令）。
   这 3 个单元的首分歧都不是 NOP（见 §2 表最后一列）。
4. **修复可用区域成员关系判定表达**：flytools 的真实分歧 = `except` 臂出口块归属被重排 + 每臂多写 `return None`
   （Round 4 §6.1/§7.2 已登记的 B99/B116 尾部 return-None / sink 身份族）；reconnect 的野生 NOP 来自
   `while <cond>:` 被改写成 `while True:` + 体内 `if not cond: break`（LoopRegion 条件块归属问题，`is_while_true`）。
   **不需要、也无法在「NOP 发射」层做任何事**——NOP 是 CPython 汇编器行为，不在归约条款管辖内。

---

## 1. flytools 实例的精确复现与定性

### 1.1 复现

```
del site-packages/fly/common/flytoolsOK.py
python -X utf8 pycdc.py -o site-packages/fly/common/flytoolsOK.py site-packages/fly/common/flytools.pyc   # 17.2s, 37794B（与 Round4 产物同尺寸）
python -X utf8 scripts/pyc_verify.py single site-packages/fly/common/flytools.pyc
  ***<module>.ProcessWrite.modify_batcktes_info: Failure: Different control flow
  [single] status=failure units=65/66 success_rate=98.48%
```

单元 `<module>.ProcessWrite.modify_batcktes_info`：orig **234** 条指令 / prod **235** 条；NOP **2 → 3**。

### 1.2 多出来的那条 NOP（精确坐标）

| 项 | 值 |
|---|---|
| 产物偏移 | **off700**（指令序号 151，0-based） |
| 产物行号 | **line=805**（`co_lines` 给出；`co_firstlineno=790`） |
| 前一条 | off698 `POP_TOP` line=804（`os.system(...)` 调用收尾） |
| 后三条 | off702/704/706 `LOAD_CONST None` ×3 line=**792** → off708 `PRECALL 2` → off712 `CALL 2` → off722 `POP_TOP` → off724 `LOAD_CONST None` → off726 `RETURN_VALUE`（全部 line=792） |
| 原码同位置 | off698 `POP_TOP` line=1142 → **off700 直接是 `LOAD_CONST None` line=1131**（无 NOP） |

产物源码（`site-packages/fly/common/flytoolsOK.py`，逐字引用）：

```python
790:    def modify_batcktes_info(self, user_id, filename, backtestid, log, backtestmode, file_path_name, datadict):
791:        try:
792:            with FileLock(user_id, filename, os.path.join(BACKTEST_DIR_PATH, f'{user_id!s}.{filename!s}.lock')):
...
804:                os.system(f'mv {backtest_tmp_path!s} {file_path_name!s}')
805:                return None            # ← off700 的 NOP 就挂在这一行
806:        except Exception as ex:
807:            if log:
808:                if backtestmode == 'backtest':
809:                    log.backtest.info(ex)
810:                elif backtestmode == 'trade':
811:                    log.trade_norm.info(ex)
812:                    return None        # ← 无 NOP（该臂出口块自身就是 LOAD_CONST/RETURN，行号可挂上）
813:                else:
814:                    return None
815:                return None
816:            else:
817:                return None
```

**为什么只有 805 这条 `return None` 生成了 NOP、而 812/814/815/817 四条没有**：805 位于 `with` 体内，
它的 `LOAD_CONST None; RETURN_VALUE` 被 `with` 出口块「吞并」并改标为 `with` 行（792），805 这行失去宿主指令；
812/814/815/817 位于 `except` 臂，其所属块自身的行号就是该 return 的行号，无需补 NOP。

CPython 侧实证（3.11.7，同一解释器，最小标本 `D:/Temp/rrv8/nopx/gen.py`）：

| 源形 | 指令数 | NOP |
|---|---|---|
| `with CM(a): g(a); return None`（return 在 with 体内，末条语句） | 59 | **off66 line=return行** |
| 同上但 `return`（裸） | 59 | 同上 |
| 同上但 `return 1` | 59 | 同上 |
| `with CM(a): g(a)` 后直接落到函数尾（**无 return**） | 58 | 无 |
| `with CM(a): g(a)` 然后在 with **外面** `return None` | 57 | 无 |
| `if a: pass`（空体复合语句） | 11 | off6 line=pass行 |

⇒ 两条野生 NOP 生成式：**N1 = `with`/cleanup 块吃掉末条 `return` 的行**；**N2 = 空体复合语句的分支目标行**（Round 1 B100 的「空体 `if …: pass` 行追踪 NOP」）。
reconnect 的野生 NOP 属于第三条：**N3 = `while True:` 循环头无指令可挂行**（`while <cond>:` 无此 NOP；实测 `whileTrue_break` 11 条含 NOP，`whilecond_break` 14 条无 NOP）。

### 1.3 原始源码形状的还原（决定性实验）

原始 def→except 只跨 **14 行**（1129→1143），产物跨 **16 行**（790→806）；原码行序列里
`csv_writer.writerow` 与循环回跳 NOP 共享 1136/1141，且 `insn46`（第二个 `with open`）在原码**没有独立行**。
⇒ 原码是 `with open(...) as fp, open(...) as fq:`（**多项 with 写在同一行**，1133），且 **try 尾、except 臂都没有显式 `return None`**。
用该还原源码编译：指令数 **234=234**，除 3 处 `LOAD_ATTR/LOAD_METHOD`（同语义，取决于 `csv`/`os` 是否真为导入名）外**逐条对齐、行号逐条相同**。

三探针（把产物拷到 scratch 只删语句，绝不手改仓库产物）：

| 探针 | 改动 | 判据 | 说明 |
|---|---|---|---|
| **P1** | 只删 line 805 | **65/66（仍失败）** | off700 的 NOP **消失**，残余分歧仅剩 3 处 `except` 臂出口跳转目标被置换：orig `918/942/930` vs prod `942/930/918` |
| **P3** | 805 缩进到 try 层（with 外） | 65/66 | 同样消掉 NOP，同样不过 |
| **P5b** | 删 line 805 + 删 line 812-817（四臂 return 及两个 `else:`） | **success 66/66** | 全文件全单元 Equal |

⇒ **flytools 这一单元的真实缺陷 = 5 条被凭空写出的尾部 `return None`**（1 条在 with 体内 → 留下 NOP 脚印；4 条在 except 臂 → 重排臂出口跳转）。
Round 4 §6 记的「唯一差异 = 一条 NOP」**低估了**：那 6 处位移里有 3 处不是位移伪影，是目标置换（P1 已证：NOP 没了它们还在）。

---

## 2. 语料侧：15 个失分单元的 NOP 分类

方法：`pyc_verify batch` 逐文件（重生成产物后）→ 取失败单元名 → 指令流对照。
口径：把两条流各自**删掉所有 NOP**、跳转目标归一为「NOP-剥离序列中的目标序号」（消除 +2 位移伪影），再比对。

| # | 文件 | 单元 | 指令 orig→prod | NOP orig→prod | 野生/丢失 NOP（产物行） | 剥离 NOP 后残差 | 分类 |
|--:|---|---|---|---|---|--:|---|
| 1 | IQEngine/core/strategy/strategy_universe.pyc | `<module>.StrategyUniverse._on_clear_de_listed` | 70→70 | 0→0 | — | 2 | **not-NOP-related**（臂汇合目标 27→33） |
| 2 | IQEngine/core/bar.pyc | `<module>.BarData._history_bars` | 66→66 | 0→0 | — | 2 | not-NOP-related（32→51） |
| 3 | IQData/api/api_base.pyc | `<module>.get_history_df` | 1900→1900 | 0→0 | — | 72 | not-NOP-related |
| 4 | IQCommon/data/finance.pyc | `<module>.get_fields` | 177→178 | 1→1 | 位置不变（`try:`） | 35 | not-NOP-related（EXTENDED_ARG +1，EA 形） |
| 5 | IQEngine/plugins/plugin_system_matcher/matcher.pyc | `<module>.DefaultMatcher.match` | 800→**790** | 1→1 | NOP 位置 518→508 | 60 | not-NOP-related（−10 指令） |
| 6 | fly/dumpload/load_daily.pyc | `<module>` | 1017→1017 | 3→3 | 位置完全一致 | 2 | not-NOP-related（JUMP_FORWARD 目标 664→682） |
| 7 | IQEngine/plugins/plugin_fly_data/strategy/strategy.pyc | `<module>.Strategy.tick_worker_thread` | 294→294 | 2→2 | 位置一致 | 8 | not-NOP-related |
| 8 | IQEngine/plugins/plugin_system_trade/function.pyc | `<module>.reconnect` | 101→**102** | **0→1** | **off70 line=1210 `while True:`** | 4 | **N3 脚印；不是 NOP-only**（跳转目标 84→99 置换） |
| 9 | fly/data/quote.pyc | `<module>.Quote.build_current_period_df` | 124→**113** | 0→0 | — | 25 | not-NOP-related（判据报 Different bytecode） |
| 10 | fly/data/quote.pyc | `<module>.Quote.check_frequency` | 132→133 | 1→1 | 位置一致 | 9 | not-NOP-related |
| 11 | fly/data/quote.pyc | `<module>.Quote.get_real_from_zeromq` | 793→791 | 1→1 | 位置 191→192 | 76 | not-NOP-related |
| 12 | fly/data/quote.pyc | `<module>.Quote.run_individual_transform` | 412→**359** | 2→2 | **NOP 丢失 @111** | 135 | not-NOP-related（−53 指令，NOP 丢失只是伴生） |
| 13 | fly/data/quote.pyc | `<module>.Quote.run_tick_socket` | 347→348 | 2→2 | 位置 14→15 | 129 | not-NOP-related |
| 14 | fly/data/quote.pyc | `<module>.Quote.get_individual_data` | 354→355 | 1→1 | 位置 206→207 | 27 | not-NOP-related |
| 15 | fly/common/flytools.pyc | `<module>.ProcessWrite.modify_batcktes_info` | 234→**235** | **2→3** | **off700 line=805 `return None`** | 6 | **N1 脚印；不是 NOP-only**（P1 证伪） |

**计数（本票的主产品）**

- `pure-NOP`：**0**
- `NOP+shift-only`（"只要没有这条 NOP 就会过"）：**0** ← 由 §1.3 P1（NOP 消掉仍 65/66）与 §3 r8nop_01（孤立 NOP 判 success）双向否证
- `not-NOP-related`：**15/15**
- 带 **野生 +1 行追踪 NOP** 脚印的单元：**2**（`flytools.modify_batcktes_info` N1、`function.reconnect` N3）
- 带 **NOP 丢失** 脚印的单元：**1**（`quote.run_individual_transform`，Round 1 B100 型，但同单元 −53 指令）
- NOP 计数与位置**完全一致**却仍失败的单元：**9**

⇒ 这些一分文件不是「一族 NOP」，而是**同一族「凭空物化的尾部语句 / 出口块归属」**的不同可见度；NOP 只是它在行号表上的影子。

---

## 3. 合成标本：`test_repros/round8/r8nop_*`（25 个，索引 `r8_probe_index.json`）

流水线（与 Round 4 `_r4v3gen.py` 一致，全程不手改产物）：写 `.py` → `py_compile` → `pycdc.py -o <base>OK.py` → `pyc_verify batch --index`。

| # | 标本 | 今天的判据 | 与配对标本的**唯一**构造差异（自证翻转） |
|--:|---|---|---|
| 01 | with 体末无 return、except 有 handler（产物自己补了 `return None`→**+1 NOP**） | **MATCH 2/2** | ← 与 13 比：把体内嵌套 `with` 换成一条普通语句，就**不再失败**（NOP 本身不致命） |
| 02 | 同上但源码显式写 `return None` | MATCH | 与 01 只差那条显式 `return None`（两者都过 ⇒ N1 的 NOP 被判据容忍） |
| 03 | `while <cond>:` + `if: break` | MATCH | 与 17 同族对照 |
| 04 | `while True:` + `if not cond` 守卫 | MATCH | — |
| 05 | 函数体内 `if a: pass`（N2 空体 NOP） | MATCH | — |
| **06** | except handler 内 `if/elif` 双臂**不写** return | **MISMATCH** | **↔ 07**：给每个臂补一条尾部 `return None` ⇒ MATCH。翻转构造＝**臂尾 `return None`** |
| 07 | 同上，臂尾显式 `return None` | MATCH | 06/07 即 flytools 的最小可读复现 |
| 08 | `except Exception: pass` | MATCH | — |
| 09 | with 体末 `return a + 1` | MATCH | 证明 N1 对「带值 return」同样只留脚印不失败 |
| 10 | `return None` 写在 with **外面** | MATCH | 该形不产生 NOP（§1.2 表第 5 行） |
| 11 | 多项 `with A() as a, B() as b:` | MATCH | flytools 原码的真实形状 |
| 12 | `try: while True: …` | MATCH | — |
| **13** | `try: with A: with B: …; 尾语句` + `except: lg(e)`（flytools 形状） | **MISMATCH** | **↔ 24**：删掉外层 with 体里「内层 with 之后的那条语句」⇒ MATCH。翻转构造＝**内层 cleanup 之后的尾语句** |
| **14** | 13 + 全部显式 return（flytools 产物形状） | **MISMATCH** | 说明「补 return」不能翻案，方向反了 |
| **15** | except handler 内 `if/elif pass/else` | **MISMATCH** | **↔ 22**：把同一条链从 `except` 里搬到函数体 ⇒ MATCH。翻转构造＝**宿主是不是 except handler** |
| **16** | `while <cond>:` + `if/elif pass/else: continue` + 尾 return | **MISMATCH** | **↔ 23**：删掉 else 臂末尾的 `continue` ⇒ MATCH。翻转构造＝**continue** |
| 17 | `while <cond>:` + `if: break` | MATCH | 与 21 互为翻转（见下） |
| 18 | 顶层 `if/elif` 链，臂不写 return | MATCH | 与 06 对照：同样的臂形在**函数体**里能过、在 **except handler** 里过不了 |
| **19** | 13 的源码补上 with 体末 `return None` | **MISMATCH** | 产物反而把两个 with 合并成 `with CM(a), open(a) as fp:`（多行→多项 with 合并丢结构） |
| **20** | 15 的 `pass` 换成真语句 | **MISMATCH** | 证明 15 的成因**不是** `pass`/空体 NOP |
| **21** | 16 删掉 `elif …: pass` 臂 | **MISMATCH** | 产物把 `while cond:` 改写成 `while True:` + `if not cond: break`（=reconnect 的 N3 脚印） |
| 22 | 15 去掉 try/except 宿主 | MATCH | 15↔22 翻转对 |
| 23 | 16 去掉 `continue` | MATCH | 16↔23 翻转对 |
| 24 | 13 去掉外层 with 体的尾语句 | MATCH | 13↔24 翻转对 |
| **25** | 13 + 只在 except 臂补 `return None` | **MISMATCH** | 单补臂 return 不够，需与 24 的组合才回正 |

`python -X utf8 scripts/pyc_verify.py batch --index test_repros/round8/r8_probe_index.json` 实测读数（本轮亲自跑）：

```
"files_total": 25, "units_total": 50, "units_success": 41, "success_rate": 0.82
```

**MISMATCH 臂 = 9（06 13 14 15 16 19 20 21 25）／ MATCH 对照臂 = 16**，满足 ≥8 标本、≥3 MISMATCH、≥2 MATCH 的围栏要求。
自证翻转对：06↔07、13↔24、15↔22、16↔23；另 01/02/09/10 四臂共同钉住「孤立野生 NOP 不致命」这一条（围栏不许把修复下到 NOP 发射上）。

---

## 4. 生产站点（全部 grep 核实存在于今日工作树）

文件实测行数：`core/cfg/region_ast_generator.py` **58770** 行、`core/cfg/region_analyzer.py` **32337** 行、`core/cfg/code_generator.py` **6023** 行。

**站点 1（flytools 的 with 体末 `return None` + 四臂 `return None`）**
`core/cfg/region_ast_generator.py:2357` 起：

```
2357:            _trailing_rn_exit_count = 0
2358:            if _func_cfg is not None and hasattr(_func_cfg, 'blocks'):
2362:                if self.region_analyzer._check_block_has_trailing_return_none(_blk):
2363:                    _trailing_rn_exit_count += 1
2372:            # 最终决定：始终保留 return None，确保字节码一致。
2373:            if filtered_body and self._is_trailing_return_none_statement(filtered_body[-1]):
2374:                if len(filtered_body) == 1:
2375:                    # 单条 return None → 保留（字节码一致需要）
2376:                    pass
```

`grep -rn "_trailing_rn_exit_count" core/` 仍只有 **2 处**（2357 置 0、2363 +=1），**没有任何读取点**；
2373 的守卫体是 `pass`（2376）与注释（2377）⇒ **该处不消费出口块计数，恒常物化尾部 `return None`**。
这正是 flytools 的 5 条凭空 return 的出生地，也是 reconnect 型臂出口置换的出生地。
配套符号（grep 核实）：`core/cfg/region_analyzer.py:1315 def _check_block_has_trailing_return_none`；
`core/cfg/code_generator.py:2232 def _filter_trailing_return_none`（调用点 521 / 2218 / 2269 / 2370）。

**站点 2（reconnect 的 `while True:` 野生 NOP，N3）**
`core/cfg/region_analyzer.py:515 is_while_true: bool = False`；
`region_analyzer.py:685`「condition_block 归属 TernaryRegion，循环以 while_true 形态运行」；
`region_analyzer.py:1366`「header 含条件 → while cond；否则 while True」；`region_analyzer.py:4563-4564`（Step 7 及降级规则）。
⇒ 条件块被别的区域认领 ⇒ 循环退化为 `while True:` ⇒ CPython 必须在循环头补一条行追踪 NOP。r8nop_21 的产物直接印出该改写。

### 条款归属（不硬套）

- 这**不是** `rules.md §5.3` 的 NOP 豁免问题：§5.3 谈的是「能否把 NOP 差异当作对齐伪影」，而本轮实测**一条孤立 NOP 不改变判据读数**（r8nop_01 = MATCH），故既不需要豁免、也没有可豁免的失分。
- 真正的破口落在 **§1.2 原则2（每块唯一归属）/ §1.5 C1 局部消费 + C3 守卫封闭**：`with` cleanup 块与 `except` 臂出口块的区域认领决定了「要不要为某个出口块物化一条 `return None`」。站点 1 已经**算出了出口块计数却没有消费**（2357-2376），符合 §6.4「代码已落地 vs 仅归档 spec」的 B1 形态；站点 2 是条件块被非局部区域抢走（C3 缺显式认领守卫）。
- 但**「NOP 发射」本身不在归约条款管辖内**：NOP 是 CPython 汇编器为行追踪补的洞，反编译器只能通过「不写出这条语句」来避免它，不能也不该直接操纵它。

### 修复可否用区域成员关系表达？

**可以，而且必须**：
1. flytools（P5b 已给可过形状）：把 §1.2/§1.5 的区域成员关系补上后，判定应为
   「该出口块是否被 ≥2 个区域外臂共享 / 是否就是函数隐式 sink」——**按区域分箱消费 `_trailing_rn_exit_count`**（Round 4 §7.2 已写下同一建议），
   使得**每个臂不各发一条 `return None`、with 体末也不发**。这样 flytools 的 NOP（N1）与 3 处臂置换**同时**消失（P5b = 66/66 是硬证）。
2. reconnect（N3）：条件块归属必须由 LoopRegion 认领（`is_while_true=False`），属站点 2 的 C3 守卫，与 NOP 无关。
3. **禁止**任何「发 NOP / 不发 NOP」层面的补丁：`r8nop_01 / 02 / 09 / 10` 四臂已证明该层面动作用户判据上零收益，且会污染 N2 型（`if …: pass`）标本。

---

## 5. 本轮改动清单与如实声明

- 新增：`test_repros/round8/r8nop_01..25`（`.py`/`.pyc`/`OK.py` 各 25）+ `test_repros/round8/r8_probe_index.json`（25 条）+ 本文件。
- 语料侧：按认证方式重生成 10 份产物（flytools、strategy_universe、bar、api_base、finance、matcher、load_daily、plugin_fly_data/strategy、function、quote），**未手改任何 \*OK.py**；`probe/` 三探针（P1/P3/P5b）与还原标本全部写在 `D:/Temp/rrv8/`，未落地仓库。
- 零生产代码改动；未动 `core/`、`pycdc.py`、`scripts/`、`*OK.py`；未跑 402 文件批与 34 集。
- 未闭合：`matcher`（−10 指令）、`quote.build_current_period_df`（−11 指令、Different bytecode）、`api_base`（72 处残差）的机制仍需按 A 族（臂汇合身份）单独定标，本轮只做了 NOP 维度的否证。
- 行号为**本轮实测**（region_ast_generator 58770 / region_analyzer 32337 / code_generator 6023）。
