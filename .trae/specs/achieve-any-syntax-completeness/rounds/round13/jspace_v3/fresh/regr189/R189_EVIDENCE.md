# rr-v5r189 — r171 两处回归收窄（保留 CONT-TAIL 收益）

树：`F:\Downloads\pythoncdc-main`（未 commit / 未 push）；解释器 `D:/Python/python.exe -I -X utf8`
补丁：`D:\temp\opencode\cl_layout\r189\fix189.py`（anchor `count==1` / utf-8-sig / BOM 保持 / `py_compile` / 幂等 / `--revert`）
改动：`core/cfg/region_ast_generator.py` **+12 / −6**（唯一文件；BOM `efbbbf` 单头 + 全 LF 不变）

## 1. 复现（探针，非阅读猜测）
| 案 | 收窄前产物 sha16 | 判官 | 直跑 |
|---|---|---|---|
| `e01_g1_b98_matrix` | `6f317b37` | 13/15（`f_b98_or_tail_and_group`、`f_b98_while_cond_pos`） | 1→0 |
| `r9_02_b2_dual_continue` | `a889c714` | 4/5（`break_continue_mix`） | `keep` 调用 3→0 |

单 hunk 分离（`edit_tree.py` + 冻结树 `t_nohunk*`）复核 BISECT：只停 hunk A ⇒ e01 回到 `73cf27c6`（14/15）；
只停 hunk B ⇒ r9_02 回到 `3aa5d940`（5/5）。

## 2. hunk A — `_process_if_blocks` `[v171-NESTED-ARM]`（认领口径收窄）
- 误认领的那一条条件：**merge 同一性门** `if _v171_mb is not _v171_pmb ... continue`
  ——只有「嵌套 IfRegion 的 merge 与本区域同一个」时，才把嵌套区域的臂块从父臂块列表剔除。
- r9_02 实测（`instrument_e/q/p2`）：父 `IfRegion@8`（merge=92，循环出口）的 else 臂里有嵌套
  `IfRegion@36`（merge=60，= 循环 back_edge_block，与父 merge 不同）⇒ 门不成立 ⇒ 其裸跳转臂尾
  `blk@58`（仅 `JUMP_BACKWARD`）留在父臂走查里被第二次发射：
  `_if_generate_else_branch(IfRegion@8)` 返回 `['If','Continue']`，最终 `For.body` = `[If(orelse=[If,Continue]), Expr]`
  ⇒ 渲染成 `continue` 在 `keep(x)` 之前 ⇒ 死代码（每块唯一归属被破坏）。
- e01 实测：同一扇门在 `(a and b) or c or d` 上把**带用户指令的操作数块**也剔掉了 ⇒ 条件被摊成嵌套 if/pass。
- 收窄后判据（只读块指令集，I.4 白名单）：仍对每个嵌套 IfRegion 的 then/else 成员求交，但只剔除
  「块内除 `RESUME/NOP/CACHE/PUSH_NULL/EXTENDED_ARG/JUMP_BACKWARD(_NO_INTERRUPT)/JUMP_FORWARD/JUMP_ABSOLUTE`
  外无任何指令」的**纯跳转臂尾**；merge 同一性门整条删除（它不是不变量）。
- 结果：r9_02 5/5（`bb86df78`，`break_continue_mix` 语句数 8=源码 8）；e01 的 or_tail 回到
  `if i and (a and b or c or d)`（`f_b98_or_tail_and_group` 由 (4 If/9 stmt/1 Pass) → (1/5/0)）。

## 3. hunk B — `_if_generate_normal` `[v171-ITER-EXIT-b]`：**不需要改**（有实证的「无可收窄」）
探针（`instrument_b2/b5/b6`）枚举全部命中站点：cookiejar 3 处 + r9_02 1 处：
| 站点 | entry/merge | merge 前驱 | 区域外前驱 | merge 归属区域 | then | loop hdr/be |
|---|---|---|---|---|---|---|
| `_normalized_cookie_tuples` | 564/572 | [564] | [] | LoopRegion | [568] | 18/572 |
| `as_lwp_str` | 76/120 | [72,76] | [72] | LoopRegion | [118] | 48/120 |
| `_really_load` | 1026/1076 | [1026,1030] | [] | TryExceptRegion | [1072] | 402/1076 |
| **`break_continue_mix`** | 36/60 | [36] | [] | LoopRegion | [58] | 6/60 |
`_normalized_cookie_tuples` 与 `break_continue_mix` 在上述**全部**结构事实上完全相同；停用该守卫时前者多一条
尾部 `continue`（本轮收益丢失 ⇒ 103/105 掉），后者少一条前导 `continue`。⇒ 该守卫自身不携带区分信息，
「按结构收窄 hunk B」不存在可行解；r9_02 的伤害面在 hunk A 的臂块去重上（§2），因此 hunk B 逐字保持。

## 4. 为达到 e01 15/15 必需的第三处（r117 D1b，`_loop_generate_while` `[v117-ELIFTEST]`）
- 收窄前：`get_entry_region_for_block(b) is not None` 即排除吸收。
- 探针（`instrument_c/c3`）：e01 `blk@46` 的查询返回 **IfRegion@32（entry=32 ≠ 46）**——不是本块自己的区域；
  排除后旋转 while 条件链断裂、`if n > 2: break` 整段消失（`f_b98_while_cond_pos` 0 个 If、直跑超时）。
- 收窄后：`... and getattr(_b_entry_region, 'entry', None) is b`（守卫回到它自己写明的前提）。
  difflib 的 6 处命中全部 `entry is b`，逐字不变。

## 5. 验证读数
- 回归案：e01 **15/15**（`e5b02d5e`，= r116 正确形）、r9_02 **5/5**（`bb86df78`）；
  直跑：`f_b98_while_cond_pos(1,1,1)=3`（不死循环）、`f_b98_or_tail_and_group(1,1,1,1)=1`、
  `break_continue_mix([5,1,-1,9])` keep=3 `[5,-1,9]`（原件/产物逐项相同）。
- 五语料（`gate/corpus_run189.py fix`）：request `db2172e8f1a6` 194/194、tarfile `8b35ed1396ac` 158/160、
  cookiejar `d39c77eeb677` 103/105、subprocess `557b9b0bfe9e` 75/78、difflib `d70df6006a50` 62/62
  —— 与本轮起点**逐字节相同**。
- J 空间：任务口径（冻结 r187 证据 + 32 条产物变化 overlay）**covered_5tuple 1174**（= 基线，未下降；
  r7_only=6、semantic_failures=6 不变）；全量重跑 1105→**1117**（+12）。32 条产物变化全部仍判 EQUAL：
  BOOLOP 17 / CONTINUE 11 / WHILE 1 / RETURN 1 / IFEXP 1 / NAMEDEXPR 2，均为臂块去重族。
- 458 电池（`battery189.py`，old=冻结树 / new=补丁树）：rows 458、**TEXT-DIFF 0**（458 全 TEXT-SAME ⇒
  ⊆ 17 允许集、BYTE-EQUAL 平凡成立）、`C7_skipedge` TEXT-SAME、NO-SRC 0、COMPILE-ERR 0。
  因 458 案 old==new 逐字节相同，R110 text+sig 一致读数与 r187 基线同值（166/169；本树 harness 的
  R110 基线文件已随轮次迁移，打印 0/169 属读数工装问题，不是差异）。
- AST：五语料 `(If,stmt,Pass)` base==fix（request 286/1725/17、tarfile 324/1750/12、cookiejar 240/1213/8、
  subprocess 270/1125/22、difflib 114/737/9）；回归案只动了两个函数，且都朝源码收敛
  （`break_continue_mix` 9→8 = 源码 8；or_tail 4 If/9 stmt/1 Pass → 1/5/0，源码 2/6/0）。
- 红线：五语料 text=SAME、逐 code object `changed=NONE`；tarfile/cookiejar/subprocess 各 12 具名单元
  36/36 **BYTE-SAME**。
- 卫生：`validate_region_generator_signatures.py` → `统计: 14 个错误, 6 个警告`；
  `region_ast_generator.py` / `region_analyzer.py` BOM `efbbbf` 单头；`comprehension_generator.py`
  无 BOM（首字节 `66726f`）+ CRLF（6691/6691）；`git status` 仅 `core/cfg/region_ast_generator.py` M。
- fix189.py：二次 apply 两 hunk 全 skip；`--revert` → sha `d9d60964`→`ebea8de6`（= 改前原文），
  再 apply → `d9d60964`；两向均过 `py_compile`。

## 6. 产物清单（`D:\temp\opencode\cl_layout\r189`）
`fix189.py`、`r189_runner.py`、`merge_shards.py`、`overlay189.py`、`battery189.py`、
`gate/{corpus_run189,redline189,ast189}.py`、`probe/{edit_tree,instrument_b..q,run_trace,run_behaviour}.py`、
`work/{semantic_r189_shard0..7,semantic_r189_merged,semantic_r189_frozen_plus,coverage_r189,coverage_r189_frozen_plus}.json`、
`gate/{base_products,fix_products,raw_judge_*}`、`base/`（改前冻结树）。
