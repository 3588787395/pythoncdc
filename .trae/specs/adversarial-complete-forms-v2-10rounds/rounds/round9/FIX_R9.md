# Round 9 修复批次 FIX_R9（任务 9.2，算法修复，不 git commit）

- 基线 = REVIEW_DRAFT §1 站桩新基线（合并树 e42b8509 → 本批起始 a2d1e15e）；判据唯一 `scripts/pyc_verify.py`，RV2（先 regen `pycdc -o` 再 verify single）
- 纪律 = 只动 `core/cfg/region_analyzer.py` / `region_ast_generator.py` 的归约算法判据面；禁止回滚合并调和 hunk [B104-R3]/[B99 收窄]/H1-H4（REVIEW §4 承重实证）；I.4 白名单判据、I.6 落地声明、I.7 注释同步；命令 ≤300s 分片；regen M 态 `*OK.py` 终态 `git checkout --` 还原；插桩用完即删
- 工作队列 = §6 派发：位0（B124 四臂归属）→ 位A（B104 while 链族 14 单元）→ 位B（B125）→ 位C（B126）→ 尽力项（B127/B128/B44/Yield 探针）

## §0 位0：B124 四臂归属（只读，已完成）

方法 = MERGE_RECORD ana_ab3_r137 同款：字节级备份→改臂→regen+verify→还原→sha256 校验（每臂）；靶 = B124 五单元（e05×3 + e10×1 + r8_10×1）。

**证据**：`r9v9fix_b124_4arm.json`（control/off_b104r3/off_b99/off_h3/成对臂/off_all3/v3tip/v2tip/v2a_mg/ma_v2g 全臂读数）。

| 臂 | e05 | e10 | r8_10 | 判定 |
|---|---|---|---|---|
| control（全开） | 3/11，B124×3 败 | 31/32，1 败 | 8/12，1 败 | 基线 |
| off_b104r3（关 [B104-R3] released 值位跳过门） | **6/11，B124×0 败** | 31/32 | 8/12 | **e05×3 → [B104-R3]** |
| off_b99（关 [B99 收窄]）/ off_h3（关 [R21-15]+[R21-36] 臂尾提升） | 不变 | 不变 | 不变 | 非单因 |
| 成对臂/off_all3 | e05 同 off_b104r3 | 不变 | 不变 | 非组合因 |
| v3tip（两文件=v3 tip 996a1b1a/566ff5c5） | 4/11，B124×3 败 | 31/32，1 败 | 8/12，1 败 | **v3 tip 同败 ⇒ 非合并新增而是 v3 侧代码 + v2 独占覆盖未被组合恢复** |
| v2tip（两文件=91f8d27d） | 6/11，B124×0 败 | 32/32 | 9/12，B124×0 败 | v2 tip 全绿复核 |
| v2a_mg（v2 ana + merged gen） | 0/11 | 0/32 | 0/12 | 整体不相容（合并树 gen 依赖合并树 ana 元数据），无归属信息 |
| **ma_v2g（merged ana + v2 gen）** | 3/11（B124×3 仍败） | **32/32** | **9/12（B124×0 败）** | **e10×1 + r8_10×1 → generator 桶** |

**归属结论（修正 REVIEW §5 B124 的「4-arm 待归属」）**：
- B124 拆双桶：e05 三单元（f_compare_chain6/f_compare_binop_inside/f_compare_subscript_inside）→ **analyzer 桶**（[B104-R3] released 值位跳过门对嵌套宿主值位链过宽，与 matcher 承重门（cf_b99_r143/battery nb_for/nb_with）同文件不冲突）；e10 f_call_ternary_arg + r8_10 r8_x_with_ternary → **generator 桶**（调用实参位 IfExp 重建，v3 tip 亦败 = v2 独占覆盖被 v3 生成层重构覆盖后未恢复）。
- 双树定性修正：五单元并非「v2 tip 全绿 ⇒ 合并新增」的调和缝隙——v3 tip 亦红 ⇒ 属 v3 侧存量代码在合并树原样保留；v2 的独占覆盖在冲突调和时未被并列。修复向 = 判据面扩门（恢复 v2 覆盖 + 保留 v3 门），非回滚任何 hunk。

## §1 位A：B104 while 条件位链式比较族（14 合并新增单元 + w3_nostore 存量）

**根因（诊断实据 `r9v9fix_diag_*.py` 驱动 + [T] 插桩追踪）**：CPython 3.11 旋转 while 的**入口**条件段块（cond_block）可携带循环前缀语句（`n = 0; while 0 < x < n < 100:` 的初始化赋值被识别层条件块搜索并入链头块），而**回边**副本所在体块的尾段按语句边界（末条 STORE_*/POP_TOP 之后）截取、永不含前缀语句 ⇒ [R21-66] SEG 副本身份判据的全块变体永不相等（实测 chain4/e08_while 全族 `latch_copy=False`），路 B（`_is_recheck and latch_copy and boundary==store`）永不命中 ⇒ 重检副本泄漏为体语句幻影 `if 0<x<10: pass` / `if 0<x and n<True: ... elif n<100:`。第二缺口：路 B 的单段 `_build_store_statement` 只重建单语句，多语句前缀（`x += 1; n += 1`）丢码。第三缺口（w3_nostore，存量 R4）：`out.append(x); x += 1` 闩锁块中 POP_TOP 结尾的表达式语句与赋值并段，重建只存赋值、表达式语句蒸发。

**修复（region_ast_generator.py，三处扩门 + 一处因子化，「代码已落地」）**：
1. `[B104-R9 语句前缀变体]`：SEG 集追加「末条 STORE_*/POP_TOP 语句边界之后的求值尾段」变体（与体块尾段截取方式对称，同一终结 opcode 族；无前缀段块边界 -1 不产生新项，既有全块变体全保留，加性扩门）。锚点 = `_r2166_seg_set` 构造环内（`_loop_generate_while` cc 分支，`region_ast_generator.py:8649-8659` 一带）。
2. `[B104-R9 混合操作数求值段集]`：`_r2166_mixed_seq_set` = 识别层 [B104-R2a] 操作数块的条件求值段（`_b104r2_cond_eval_seq`，与路 A 同一判据），并入 case C 回边纯重检身份集（`and flag` 尾块等）。
3. 路 B 多语句前缀改用 STORE 边界多段抽取器 + `[B104-R4]` POP_TOP 表达式语句终结符并入切分集（split_expr_stmts=True；路 A 不传此参、v2 语义逐位不变）。
4. 路 A 内联抽取器因子化为 `_extract_recheck_store_stmts`（六项 docstring + C1/C2/C3 声明齐全），路 A 调用参数缺省 = 段切分/重建序与 v2 原内联实现逐位一致；路 B 单语句前缀逐字节同既有行为。

**读数（before → after，证据 `r9v9_repro_r92pre_b104.json` → `r9v9_repro_r92fixA2_b104.json` / `r92fixA_b104.json`）**：

| 探针 | before | after |
|---|---|---|
| B104_main（c4_09） | 12/14 | **13/14**（e08_while 翻正；CCMP.m = with 宿主值位链 → B124 分析器桶，§2） |
| chain4 电池 | 4/6 | **6/6** |
| chain5 电池 | 2/5 | **5/5** |
| opdeep 电池 | 2/4 | **4/4** |
| exprtail 电池 | 2/5 | **4/5**（v1/v2 翻正；v3 = B123 存量，§4 移交） |
| foror 电池 | 3/3 | 3/3 |
| n9_whilehost | 5/9 | **9/9**（w3_plain/w3_deep/w3_and 翻正 + 存量 w3_nostore 翻正 = B104-R4 一并封闭） |

- **B104 while 条件位族 14 合并新增单元全转 MATCH，存量 R4（w3_nostore）一并封闭**。
- 承重面（`r9v9fix_bearing.json`）：broker 128/128、matcher 17/17、finance success（single 32/32，402 批量口径 132/132 由 34 集复核）、quote_handler 79/79、realtime 13/13、quotation 153/153、nb_for 2/2、nb_with 2/2、nb_b99 4/4 全绿。
- I.4 白名单核验：全部判据 = 块内 opcode 序 + 语句终结 opcode 族（STORE_*/POP_TOP/UNPACK 计数）+ 既有 `_b104r2_cond_eval_seq`；零名字/偏移/阈值/跨层反查。G3：新增方法 `_extract_recheck_store_stmts` 无禁前缀。

## §2 位B：B125 嵌套循环宿主 while-else 蒸发（2 单元）

（待位A）

## §3 位C：B126 assert 链归约吞 while 回边载体（1 单元）

（待位B）

## §4 尽力项：B127/B128/Yield 探针重建/B44 证据缺口

（待位C）

## §5 站桩回归（七面 + 承重面 + 34 集）

（终态汇总）
