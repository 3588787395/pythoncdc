# rr-v5r186 — or-of-ands 三元「被拆成嵌套 if 并吞后续语句」族修复

树：F:\Downloads\pythoncdc-main（未 commit / 未 push）；解释器 D:/Python/python.exe -I -X utf8
补丁：D:\temp\opencode\cl_layout\r186\fix186.py（anchor count==1 / utf-8-sig / py_compile / 幂等 / --revert 往返 sha 一致）
改动：core/cfg/region_analyzer.py +222/−2、core/cfg/region_ast_generator.py +12/−0（仅这两个文件）

## 0. 复现（现树 HEAD 954e4153 上实测）
源：`V = OLD if (sys.flags and sys.version_info > (3,0)) or (sys.maxsize > 0 and sys.argv) else NEW`
修复前产物：`if not (sys.flags and sys.version_info > (3,0)):` / `    V = OLD if sys.maxsize > 0 and sys.argv else NEW` /
`    print('V =', V)` —— `print` 被吞进 then 体，运行时无 `V = old`。
CFG（模块）：B0[0..30]=import+OLD+NEW+`sys.flags`，B32[32..52]，B54[54..74]，B76[76..88]，B90[90..92]=LOAD OLD+JF，
B94=LOAD NEW，B96[96..124]=STORE V + print + RETURN。
修复前区域：BOOL_OP(entry=0, merge=90, op_chain=[(0,'and'),(32,'or')]) + TERNARY(entry=76) + TERNARY(entry=54) + IF_THEN(entry=0, then=[54,76,94])。

## 1. 根因（函数:行号 + 判据名，行号为 HEAD 原始树）
1. `_is_boolop_ternary_candidate`（region_analyzer.py:28020；判据 `jt_has_code`，**return False @:28098**）：
   链成员 B32 的跳转目标 B90 = [LOAD_NAME OLD; JUMP_FORWARD] 含 LOAD_NAME ⇒ 判「目标有代码」⇒ 拒绝
   BoolOp→Ternary 升级。对照 `v = 1 if (a and b) or (c and d) else 2` 值块是 LOAD_CONST（被该判据排除）故放行
   —— 判据只区分了值块的装载 opcode，不区分「条件链是否完整」。
2. `BoolOpRegion.can_be_ternary_header`（:1204；判据链 `op_chain 条件块不放行`，**return False @:1155**）：
   链中段 B32 已被截断的 BoolOpRegion 占用 ⇒ 三元识别端在链首/中段全部被拒。
3. `_detect_ternary_pattern`（:28666）：头块直连后继被当作真/假值块（`_is_single_expression_block` 值块门 @:29176-29178）；
   真/假值块都落回条件块时值块门 `return None` ⇒ 全链三元缺席；同时既有 entry=54/76 的后缀三元区域满足
   `false_is_ternary` 通道（`false_existing is TernaryRegion`，:29364），IF_THEN（entry=0, then=[54,76,94]）
   把 B94(=LOAD NEW) 与 B96 后续语句收进 then → 语句被吞，并叠出两层错序三元。
   `_build_ternary_condition_chain`（:28215）只沿「与 initial_jt 共享假出口」的均匀链走，
   在 and→or 边界（B32 的 IF_TRUE 目标 = then 值块）止步，把 or 段留在链外。
   同一断点还有一条上游成因：`_detect_boolop_conditional_chain` 的 `_ft_ctrl_only`/`_ft_jf_target_returns`
   门（**break @:35505**）在候选 fall-through 是值块时终止子链，使 `C and D` 段无法并入 BoolOp 链。

## 2. 修复（族级谓词，只读 CFG/异常边/区域身份）
新增 `_ternary_chain_completion`（region_analyzer.py:28150，六项 docstring，无 §2.1 前缀）：
* 头块末指令 ∈ FORWARD_CONDITIONAL_JUMP_OPS，且**两条条件后继都是条件链成员**（末指令正向条件跳转 +
  恰两条条件后继）；
* visited 块集沿两条出边收集链成员（终止性=块集有限性，无深度/计数上限）；其余为出口候选；
* 出口候选须恰两块、逐块 `_ofc_value_block`（`_is_single_expression_block` ∧ 无 POP_TOP ∧ 非 RETURN 收尾）；
* 两出口的正常后继须汇聚同一块（值菱形）；链中**唯一判定成员**（两后继=两出口）须为块序末位；
  真/假沿用链尾约定（非跳转目标=真值块）；
* **极性文法守卫**：各成员按末跳转族取 and/or，须满足 `and+ (or and+)*`（首成员 IF_FALSE、每个 or 后必接 and）
  —— 生成端 `_build_ternary_boolop_condition.or_groups` 只对这一族成立；or→and 镜像族与 `not (...)` 族拒绝回退。

接线（全部命中才生效，未命中原路逐字节）：
| 位置 | 判据 | 作用 |
|---|---|---|
| region_analyzer.py:27880/:28032 | `_can_be_ternary_header` + BoolOpRegion 前缀放行 | 放行被截断 BoolOp 前缀占住的条件头 |
| :29317 | 链补全通道（TCX 之后，链须为补全链真子集） | 链 = [A,B] → [A,B,C,D]，真/假值块换成菱形出口 |
| :29767 | `not _ofc_completed` | 禁止用被截断 op_chain 覆盖补全链（否则丢 or 段） |
| :31148 | BoolOpRegion **真子集**才摘（`op_chain ⊊ chain`） | 前缀 BoolOp 不再重复发射前导语句；同集时保留 BoolOp 优先级（防 `file and 'I' or 'D'` 变 IfExp） |
| region_ast_generator.py:55950 | 镜像既有 `cond_block in _entry_import_extracted_blocks` 守卫 | 链首 import 前缀不重复发射（`import sys` 只出一次） |

## 3. 复现案判官 / 运行
* `scripts/pyc_verify.py single r.pyc --source <product>` → `status=success units=1/1 success_rate=100.00%`
* `tools/completeness/semantic_diff.py.compare_case` → `status=EQUAL`, `dims={}`, 无 R1–R6
* 产物：`V = OLD if sys.flags and sys.version_info > (3, 0) or sys.maxsize > 0 and sys.argv else NEW` +
  `print('V =', V)`；运行输出 `V = old`（与源码一致）

## 4. 五语料判官（产物逐字节与基线相同 ⇒ 文本零变化）
request 194/194、difflib 62/62、tarfile 158/160、cookiejar 103/105、subprocess 75/78（判官 raw：
gate/raw_judge_{base,fix}_*.txt；产物 sha 五对全等，byte-identical=True）

## 5. 458 电池（D:\temp\opencode\cl_layout\r186\battery，old=现树、new=补丁树）
rows 458 / MISSING 0 / COMPILE-ERR 0；**TEXT-SAME 458，TEXT-DIFF 0**（⊆ 17 允许集，集外 0）；
`C7_skipedge` TEXT-SAME；`R110 text+sig consistent 166/169`（old==new；3 处差异 mc1/na5/pd8_prod 均为
基线自身更差、现树更好）。补丁活跃性金丝雀：同一条 A/B 路径上 G1–G6 与复现案 TEXT-DIFF、G7/G9/G10 TEXT-SAME。

## 6. 红线 + AST
* 红线（gate/redline186.py）：request/tarfile/cookiejar/subprocess/difflib **全部 code object changed=NONE**；
  tarfile 12（含 `_FileInFile.read`/`_Stream._read`/`TarFile.next`）+ cookiejar 12（含 `_str2time`/`deepvalues`）
  + subprocess 12（含 `__del__`/`__exit__`/`call`/`run`）具名单元全 **BYTE-SAME**（覆盖 38 案既有集合）。
* AST（gate/ast186.py）：五语料 `(If, stmt, Pass)` 前后全等 request(286,1725,17)、tarfile(324,1750,12)、
  cookiejar(240,1213,8)、subprocess(270,1125,22)、difflib(114,737,9)；逐 def/class 无差异，无语句减少、
  无幻影新增；`tarfile.next` source=(11,43,0) = product(11,43,0)。

## 7. 卫生
* `scripts/validate_region_generator_signatures.py` → `统计: 14 个错误, 6 个警告`（与基线一致）
* 两 cfg 文件 BOM 单头 `efbbbf`（bom_count=1）、无 CRLF；`git status` 仅这两文件 M
* 合成非语料探针 10 条（work/family2/*.py）：G1/G2/G4/G5/G6 由“错/丢语句”转为与源码逐值相等；
  G3(单 or 尾)/G7(or→and 镜像)/G9(if 语句)/G10(值 boolop) 文本逐字节不变；
  G8 `not (...)` 属另一族（取反极性），本轮按 C3 保持原行为不变。

## 8. 补丁自检
`fix186.py`：apply 幂等（二次跑全 skip）、`--revert` 往返 sha 一致
（9a911358/3ad22c2a ↔ a5e560e2/ebea8de6）、BOM 断言、两文件 py_compile。
