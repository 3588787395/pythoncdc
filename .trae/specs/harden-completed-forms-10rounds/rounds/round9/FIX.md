# Round 9 修复报告（修复工程师 · 任务 9.2 收尾批次 / FIX.md）

- 修复人：修复工程师（Round 9 任务 9.2 收尾：BOM 事故恢复 + 修复树重验 + docstring 审计 + 合规清扫）
- 日期：2026-10-04
- 树状态：HEAD = `be58c97d`（前任修复工程师在途快照，含 B66/B67/B68 算法修复本体）；本批次工作树增量 = ①两核心文件 BOM 恢复（见 §1）②`region_ast_generator.py` 两个新方法 docstring 补显式 C1/C2/C3 条款声明（9 行注释，判据零改动）③重验 JSON 落盘（a–f 同名覆盖 + 新增 `r9_sentinel.json`）。算法代码零改动。
- 唯一判据：`python scripts/pyc_verify.py batch --json <输出> <pyc...>`（pylingual compare_pyc，Python 3.11.7），每条命令 ≤300 s。
- 说明：compare_pyc 独立重编译比对（OK.py 即被测反编译产物），重生成/手改无法伪造 MATCH；本批次全程未重编译探针 pyc（`test_repros/round9/*.pyc` 原样），未触碰 site-packages 任何 `*OK.py`，未修改 REVIEW.md 及更早轮次产物。

---

## §1 BOM 双头事故（诚实记录）

- **现象**：`core/cfg/region_analyzer.py` 与 `core/cfg/region_ast_generator.py` 文件头为双 BOM `ef bb bf ef bb bf`（HEAD 基线 = 单 BOM），`import core.cfg.region_analyzer` 直接 SyntaxError，整个修复树不可运行。
- **引入时点**：前任修复工程师完成算法修复并落盘自测 JSON **之后**（其自测读数于 BOM 损坏前完成并在快照提交信息中留证），某次保存对两文件头部写入重复 BOM。快照 `be58c97d` 中两文件即为双 BOM 头（`git show be58c97d:...` 首 6 字节 `efbbbfefbbbf`），故引入点在该提交内容定稿环节；具体编辑器/工具无法进一步归因，如实记录为「快照定稿时的保存事故」。
- **修复方式**：Python 字节级处理——读原始字节，剥离恰好一个多余前导 `ef bb bf`，其余字节（含 BOM 后 `"""` 起始与全部内容）原样回写。修复后实测两文件首 9 字节 = `efbbbf2222220a…`（= 单 BOM + `"""` + 换行），`len_after = len_before - 3` 逐文件断言通过；未动 BOM 之后任何字节（`git diff` 两文件首行唯一差异即 BOM）。
- **影响面**：仅文件头 3 字节 ×2 文件。修复后冒烟：`import core.cfg.region_analyzer` / `import core.cfg.region_ast_generator` 成功，`python pycdc.py --help` 正常；全部重验读数见 §5。

## §2 B68（优先 1）：空 try/finally × 循环控制流尾随装配竞争族

- **根因机制**：`try: pass / finally: pass` 退化帧在 try 体不可抛时编译器省略 try 范围表项，区域识别阶段两处种子收集（try_start 回扩取函数首块、正常路径 finally 体收集吸收帧跳落点）把宿主尾随块（if 守卫头、循环 entry/header/条件块、循环后 return、try 后语句段）拉进 `region.blocks`；`_generate_try` 收尾对 `region.blocks` 毯式标记已生成 → 尾随 if/BoolOp 守卫、尾随 return、整个外层循环自此无派发面（r9_09 tryfin_trailing_break / tryfin_trailing_cont / tryfin_shared_guard 分别表现为整体蒸发 / try-while 嵌套倒置 / 尾随段蒸发）。
- **封闭判据（前任实现，本轮核验）**：
  1. `region_analyzer.py` :8417 `[B68 fix]`——种子收窄：try 体帧跳 `JUMP_FORWARD` 落点若为条件分支头（末指令 `POP_JUMP_*`）或 for 迭代头（含 `FOR_ITER`），不纳入 try-finally 跨度归属，交还宿主 IfRegion/LoopRegion 按入口引用语义派发；
  2. `region_analyzer.py` :9696 `[B68 fix]`——try_start 回扩收窄：取「`start_offset < try_start` 且末指令 `JUMP_FORWARD` 且 `argval > handler_start`」的帧跳块中 start_offset 最大者为真实 try 体首块，替代旧「get_blocks_in_order 首块」；无帧跳块不回扩（try 体空由 try/finally 整体表达 NOP 帧）；
  3. `region_ast_generator.py` :3106 新方法 `_b68_is_tryfin_tail_releasable` + 3 处装配守卫（:13476/:13507/:29985）——对已被拉进 `region.blocks` 的块：属 try 语句结构部分（try/else/finally/cleanup/handler/finally_copy 成员集合）或位于保护跨度内（`start_offset < try_offset_end`）或含异常机制指令/backward 跳转/循环 header 角色者照旧标记；仅「宿主顺序尾随块」跳过毯式标记，由其归属装配面正常派发。
  - **门控**（防 trade_info_utils 幻影 fp.close 回归）：两处收窄均仅在「退化空 finally 帧」生效——`finally_blocks` 全为异常机制块（剥噪后无用户语句）；非空 finally 的正常路径/副本结构（W21 保护面）维持原种子收集。
  - **为何算法驱动与嵌套无感**：判据全部为同层块对象结构事实（块末 opcode、区域自身跨度字段 `try_offset_end`/`handler_start`、区域成员集合、`loop_header` 属性），无名字/偏移白名单、无魔法阈值（跨度比较对象是区域自身边界而非硬编码常量）、无跨层跨区域回溯修正；「每块唯一归属 + 入口引用语义」保证任意嵌套深度下宿主结构块都回到宿主装配面，与具体嵌套层数无关。
- **docstring 三要素与 C 条款**：新方法 docstring 含识别条件（3 条编号）/归约方式（仅判定-毯式标记跳过，释放块由归属区域派发）/AST 映射（无，归属修正）；本批次补显式声明「C1——判据只来自同层块对象结构事实；C2——无跨层/跨区域回溯修正（只决定不标记，派发仍由归属区域完成）；C3——无按名字/文件名的个案特判」。`:9696` 处内联注释自带识别条件/归约方式/AST 映射三段，与代码逐条核对一致。审计未发现代码违反 C1/C2/C3 之处。
- **AST 映射**：归属修正类——try/finally 结构 AST 不变，尾随块按宿主正常规则映射（if→IfRegion、循环→LoopRegion、语句段直发射）。
- **复现单元转 MATCH 证据**：r9_09 三单元 tryfin_trailing_break / tryfin_trailing_cont / tryfin_shared_guard 全 MATCH（`r9_fix1.json` r9_09_b55_boundary 4/4；REVIEW §3.1 记录修复前 1/4，唯一 MATCH 为形外单元 tryfin_shared_guard 形态外单元，3 失败单元全部转 MATCH）。

## §3 B66（优先 2）：B2 continue 守卫 × with 宿主交叉失效

- **根因机制**：`for x in xs: / with open(p) as f: / if a(f): continue / use(f, x)` 的 then 臂 = with 保护跨度内边界 NOP 块 + with 退出调用块（`__exit__(None,None,None)` 清理 + `JUMP_BACKWARD` 回循环 header）。`_block_is_continue_target` 只看块自身末指令（链头末指令是 NOP）判据链未命中 → 臂渲染把链头 NOP 当孤立边界 NOP 发射幻影 `while False: pass`、退出调用块吞没——continue 蒸发、use 落入 else 臂。
- **封闭判据（前任实现，本轮核验）**：`region_ast_generator.py` :3187 新方法 `_b66_is_with_exit_continue_chain_head`（B2 continue 守卫外推一格）+ 2 处装配守卫（:30309/:52109，孤立边界 NOP 分支内先于幻影 while False 判定）。判据 = ①处于循环帧；②链头块剥噪后无用户语句；③唯一普通后继满足 with 退出回边签名（末指令 `JUMP_BACKWARD[_NO_INTERRUPT]` 且目标 = 当前循环 header，内容为 `__exit__(None,None,None)` 清理调用序列：全 LOAD_*/CALL 清理面 + 有 CALL + 有 None 常量）；④链头或后继至少一个归属某 WithRegion 块集合（with 宿主锚定，排除同形状普通调用语句块）。命中则发射 Continue 并登记链头+退出块已生成（with 语句重编译自然再生退出调用与回边，每块唯一归属不变）。
  - **为何算法驱动与嵌套无感**：全部判据为同层结构事实（块指令 opcode、普通后继集合、后继末指令与回边目标、WithRegion 成员关系——成员关系属红线明列允许判据）；「B2 判据外推一格」是把既有 continue 链头判定从末指令单点外推到「链头 NOP 块 + 退出回边后继」两点，无任何按宿主类型/名字特判，with/try 宿主内任意嵌套循环均按同一签名命中。
- **docstring 三要素与 C 条款**：docstring 含识别条件（4 条编号）/机制/归约方式/AST 映射（ast.Continue）；本批次补显式 C1/C2/C3 声明（C2 特别注明 `region_analyzer.regions` 仅作成员关系查询、不改写任何区域归属）。与代码逐条核对一致。
- **AST 映射**：ast.Continue（then 臂），退出调用块由 with 语句重编译再生。
- **复现单元转 MATCH 证据**：r9_06 cont_in_with MATCH（`r9_fix1.json` r9_06_b2_with_try_cross 4/4；修复前 2/4，cont_in_try 本就 MATCH）；同面正例与负对照（r9_10 收缩面 5/5）未误触发。

## §4 B67（优先 3）：BoolOp 混合链 × continue 守卫

- **根因机制**：`for x in xs: if a(x) and b(x) or c(x): continue / keep(x)` 中 for 迭代目标绑定 `STORE_FAST x` 与首操作数 `a(x)` 同块（循环体首块 = FOR_ITER 直接后继），`_sb_has_body` 把该 STORE 当 body 语句 → BoolOp 链检测从首块拒绝启动 → 混合链 `A and B or C` 回落单条件拆裂（`if a(x): pass / if b(x) or c(x): continue`，语义改变：a 为假时 b/c 不再短路求值）且 continue 块被重复登记发射（尾部多出一条 continue）。
- **封闭判据（前任实现，本轮核验）**：`region_analyzer.py` :27724 `[B67 fix]`——for 迭代目标 STORE 豁免：本块首条非噪声指令为 `STORE_*` 且某普通前驱以 `FOR_ITER`/`GET_ANEXT`/`GET_AITER` 收尾时，该 STORE 偏移记入豁免集合（CPython 对 for/async for 目标的绑定恒为 FOR_ITER+STORE_* 相邻对；真 body 赋值只会出现在该 STORE 之后，不受豁免影响），`_sb_has_body` 排除该偏移后完整链 [and,or,or] 经既有 B1b 边汇聚判据装配为单个 BoolOpRegion。
  - **为何算法驱动与嵌套无感**：判据 = 块首非噪声指令 opcode + 前驱块末 opcode（同层结构事实）；豁免的是「已由 for 语句头发射的迭代目标绑定」这一编译器恒定事实，不做任何 if/BoolOp 形态或嵌套层数特判；任意嵌套循环内的混合链均按同一相邻对事实豁免。
- **docstring 三要素与 C 条款**：`:27724` 内联注释含识别条件/机制/归约方式（豁免后交既有 B1b 装配面）与 AST 映射路径（单个 BoolOpRegion→BoolOp 条件），与代码逐条核对一致；本审计确认其满足 C1（opcode+前驱集合）/C2（无跨层回溯）/C3（无名字特判），无需改动。非独立新方法，无 docstring 载体，C 条款在 FIX.md 本节声明存档。
- **AST 映射**：`BoolOp(And, [a(x), BoolOp(Or, [b(x), c(x)])])` 守卫 + Continue，无拆裂、无多余 continue。
- **复现单元转 MATCH 证据**：r9_06 cont_with_boolop MATCH（同 `r9_fix1.json` r9_06 4/4）；round7 BoolOp 面（r7_11 6/7、r7_12 5/8、r7_14 5/9）与 round8 哨兵 trade_info_utils 36/41 读数零漂移，证明豁免未误扩（B42–B51/B56–B62 残留面逐位持平）。

## §5 修复树重验自测读数表（本批次独立复跑，全部覆盖写入同名 JSON）

| # | 面 | 期望 | 实测 | 逐位对照 | 判定 |
|---|---|---|---|---|---|
| a | r9 攻击面 12 pyc（r9_01..10 + n9_01/02） | 50/50 | **50/50**（12/12 文件 success） | 5 个此前 MISMATCH（r9_06 ×2 + r9_09 ×3）全部 MATCH，负对照保持 | ✓ |
| b | round6 全量 16 pyc | 115/115 | **115/115**（16/16 success） | 逐文件 units 与基线一致 | ✓ |
| c | round7 全量 16 pyc | 104/128 | **104/128**（5 success / 11 failure 文件） | 24 失败单元与 `r9_regress.json` §2.1 名单**逐位一致**（r7_01(1)/r7_03(2)/r7_04(1)/r7_05(1)/r7_06(3)/r7_07(3)/r7_08(4)/r7_10(1)/r7_11(1)/r7_12(3)/r7_14(4)，脚本比对 11/11 IDENTICAL） | ✓ |
| d | round8 全量 13 pyc | 107/118 | **107/118**（8 success / 5 failure） | 失败文件 = r8_06/r8_07/r8_09/r8_10/r8_11，与基线一致 | ✓ |
| e | rv8 3 pyc | 17/20 | **18/20**（rv8_01 6/7、rv8_02 6/7、rv8_03 6/6） | 交接词「17/20」为笔误：前任落盘 `rv8_check.json` 基线即 **18/20**（`with_body_tryfin_chain` 经 B68 修复由 5/7→6/7 转正，`rv8_02OK.py` 按 pycdc.py -o 流程重生成，快照内含），失败单元 chain_value_boolop / tryfin_then_more 与基线一致 | ✓ 持平 |
| f | 六哨兵 + option_account + quotation | tools 6/6、trade_schedule 6/6、mq_connector 13/13、strategy 2/2、scheduler 52/52、trade_info_utils 36/41、option_account 35/35、quotation 152/153 | **302/308**：6/6、6/6、13/13、2/2、52/52、**36/41**、35/35、**152/153**（报告 `r9_sentinel.json`，哨兵路径沿用 round6–8 FIX.md 口径） | trade_info_utils 失败 5 名单 = 基线（trade_operation/kill_trade_process/get_trade_status/query_trade_strategy_info/query_strategy_id）；quotation 唯一失败 = change_his_to_forward | ✓ |

docstring 补齐（纯注释）后复跑 a 面：仍 50/50，零行为影响。全部期望读数达成，无回落，无需追加算法改动。

## §6 合规清扫

- **插桩**：`parsers/` 零命中；`core/` 命中 20 行 `_dbg_` 全部位于 `region_ast_generator.py`（R30_13_DEBUG / R23N6_DEBUG5/4/3 / R23N6_TRACE 环境变量门控），与 HEAD（`be58c97d`）**逐字节一致**——系更早轮次历史遗留，本轮（含前任修复批次）零新增；`R9DBG|_probe_r|_patch_dbg` core/ 与 parsers/ 均零命中。
- **工作树**：`git status` = 两核心文件（BOM + 9 行 docstring）+ round9 五个重验 JSON 覆盖 + 新增 `r9_sentinel.json`，无其他未预期改动；REVIEW.md 及更早轮次产物零触碰；site-packages 下既有 `*OK.py` 零触碰。

## §7 残留交接

1. **Round 8 沿袭残留**（本批全部逐位持平，未认领）：round7 失败 24 单元（B42×3/B43/B44/B46–B51）、round8 失败 11 单元（B48×2/B56–B62）、rv8 失败 2 单元（B65 chain_value_boolop / B63 tryfin_then_more）、r4_or4_and2 1 单元（B11-R2）——按原交接单交后续批次。
2. **quotation 哨兵口径**（REVIEW.md §1 注记沿袭）：仓库根平面副本 pyc 与基线路径 `site-packages/fly/data/quotation.pyc` 字节不同，建议后续轮统一以 shard json 路径（原路径）为哨兵口径；本批沿用原路径口径 152/153。
3. **tasks.md Task 9.2 勾选与最终提交**：留主代理执行（本批次未做 git commit）。
