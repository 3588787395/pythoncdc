# Round 32 arm design — R32-C：`POP_TOP` 是「栈上的值被丢弃」的语句终止符，不是填充指令；推导式前导语句扫描器不得把它连同所属语句一起滤掉（原则 1 块 = 前导语句 + 尾终止）

## 靶子与目标池（实测，基线 = 落地字节 `dca5bbff`，分析核 sha `a66248d3b9a3e0a1545e`）

`logs/pool32.txt` 首行（从 round 31 G6 回写的 `pyc_index.json` 直接读，不转述）：

```
baseline(landed round31 index, HEAD dca5bbff): files 402 partial 31 sum_deficit 103 deficit1 7
```

Round 31 落地的 R31-C 使 `fly/common/flytools.pyc` 翻转为 ok（`65/65`），故 deficit-1 文件由 8 个降为
7 个。七个 deficit-1 文件按落地核逐个 `run --arm=landed` 一手复测（`logs/landed_d1.txt`）：

| 文件 | 唯一 unmatched 函数 | orig/decomp | jump | true | Round 31 的在册归因 |
|---|---|---|---|---|---|
| `IQCommon/manager/instance.pyc` | `_init_config` | 86/84 | 1 | 37 | 共享 `return None` 尾声内联，R16 J1 在册反例（受保护勿再取） |
| `IQCommon/util/replace_utils.pyc` | `decrypt_database_url` | 295/324 | 1 | 250 | 已生成区域体二次走查（过量发射，需放弃发射侧） |
| `IQEngine/.../strategy.pyc` | `tick_worker_thread` | 268/247 | 32 | 113 | 链式比较条件块整体未发射（真 deficit） |
| `IQEngine/.../default_event_source.pyc` | `events` | 510/508 | 2 | 157 | R30 残余：15 条错位＋两跳转槽 |
| `IQEngine/.../realtime_event_source.pyc` | `clock_worker` | 1275/1291 | 15 | 480 | R22/R23 在册残余 D2＋D3 |
| `IQEngine/.../matcher.pyc` | `DefaultMatcher.match` | 713/689 | 9 | 524 | 281 指令区域被推迟到函数尾并旋转 |
| `IQEngine/.../risk_calculation/function.pyc` | `save_testds_to_json` | 314/310 | 19 | 8 | 异常尾声缺**重复副本**（发射侧） |

七个读数与 Round 31 表格逐字段相同（除靶子已翻转的 `flytools.pyc` 不在列）。本轮另把 13 个
deficit-2 文件用落地核整批复测（`logs/landed_d2.txt`），目的是找「同一形状同时命中一个文件的两个
函数」的翻转候选；其中 `IQCommon/utils.pyc`（`load_ini 18/13 j0`、`load_yaml 55/55 j0`）与
`fly/simtradding/flyAccount.pyc`（`init_connection 42/41 j0`）是「零跳转槽差的纯语句缺失」形状。

## 二、三条诊断线的取舍（线 A／线 B 由只诊断代理在其私有目录完成，编排方在自己的镜像根独立复测）

* **线 A（代理，候选与归因均不可沿用）**：`risk_calculation/function.pyc :: save_testds_to_json`。
  代理报称其发射侧候选（「被丢弃的推导式残值守卫 ⇒ 补内联副本」）在全 402 sha A/B 下
  `SAME=379 IMPROVED=0 REGRESSION=1 MOVED=22`、靶子 `11/15 → 14/15` 仍不翻转。**该读数无据**：它的
  私有目录内没有任何 402 A/B 产物（详见 §六）。⇒ 候选不取，且它的数字与名词都不进入本轮记录，该
  形状回到「未诊断」状态移交 Round 33 从落地字节重测。
* **线 B（代理，因果归因被编排方否证）**：`strategy.pyc :: tick_worker_thread`。代理给出块级证据
  （推导式所在块的兄弟分支入口块被并入 `boundary_stop`，`_collect_branch_blocks` 遇停止集即停），
  并把责任归到本轮落地的 R31-C「过火」。**该因果链不成立**：Round 31 发货前的全量 A/B
  （`round31/logs/g4_ab402_sha.txt`）里 `strategy.pyc` 属 400 个 SAME 之一，即 R31-C 根本没有改变该
  文件产物字节；且该 `268/247` 读数在 Round 30 落地核上就已如此（Round 31 表格首行）。代理报告中
  的 `oauth2.pyc 71/72 -> 70/72` 亦被实测否证：落地核上 `oauth2.pyc` 是 `11/11`（该文件只有 11 个
  函数）。代理私有目录内也没有它宣称跑过的镜像构建与 402 A/B 产物。⇒ 只收下其块级证据作为线索。
* **线 C（取，本轮发货）**：`IQCommon/utils.pyc :: load_ini` 所在形状 —— 直线代码里一条
  **值被丢弃的表达式语句**（尾 `POP_TOP`）在「同块还构造推导式」时整条消失，官方尺
  `jump_diffs=0`、严格尺单块 `−5`。取舍理由：① 第一个合成见证就在落地核上失败（G0 立即成立），
  且 CONTROL 在同一次运行里保持 matched；② 判据是**补回一条结构上已经存在的语句**，不引入任何
  新形状识别；③ 全量命中面实测后才发货。

## 三、根因链（编排方一手实测：`logs/hunk_load_ini.txt`、`logs/dump_load_ini.txt`、
`logs/g0_head.log`、`logs/g0_c.log`）

1. `load_ini` 全部指令无一条跳转（`dump_load_ini.txt` 左右两列），原字节码四条语句：
   `RESUME`／`config = configparser.ConfigParser()`／`config.read(path)`（`@40..80`，
   `LOAD_FAST 'config'`、`LOAD_METHOD 'read'`、`LOAD_FAST 'path'`、`PRECALL`、`CALL`、`POP_TOP`）／
   `return {s.name: {…} for s in config.values()}`。产物里第三条整条不见，
   严格尺读成一个块：`filtered orig=18 decomp=13 delta=-5  non-equal blocks=1`，
   `H1 delete orig[5:10] @40..80 -> decomp[5:5]`。
2. 该函数被归约为**单个基本块**，语句序列在同一块的指令流里按「前导语句」交出去：
   `region_ast_generator.py:43514` 对块调用
   `ComprehensionGenerator.try_generate_comprehension_assign(block, ...)`；后者在
   `comprehension_generator.py:63` 定位块内第一个推导式 `MAKE_FUNCTION`（前一指令是
   `LOAD_CONST <code '<dictcomp>'>`），并把 `comp_idx` 之前的指令切片作为「前导语句」交给
   `:280 _generate_pre_comp_stmts(pre_comp_instrs, ...)`。
3. 调用方 `:273-278` **已经**把 `POP_TOP` 认成语句终止符（「pre_comp_instrs 末尾指令必须是
   STORE/POP_TOP/IMPORT，否则说明栈上还有未消费的值，交回通用重建路径」）。而被调方
   `:621-623` 的扫描器却把 `POP_TOP` 与 `RESUME/NOP/CACHE/PUSH_NULL` 一起 `continue` 掉：
   被丢弃的栈值所属指令留在 `current_instrs` 里继续累积，直到函数结束才随局部变量一起丢弃 ——
   既没有成为 `Expr` 语句，也没有并入下一条语句。`c3` 型（`config.read(path)` 之后还有
   `n = 3`）里 `n = 3` 正常发射、裸调用依旧消失，正是这条累积链被下一条 `STORE_FAST` 接管的征状。
4. 同层不一致（两侧对同一个 opname 类的语句角色判定相反）即为本判据的根：**两侧必须同层一致**。

## 四、判据 R32-C（原则 1 块 = 前导语句 + 尾终止 · 前导语句扫描器侧）

落地位置：`core/cfg/comprehension_generator.py:621`（`_generate_pre_comp_stmts` 的扫描循环），
`git diff --numstat` = `13 1`（唯一的删除行是原 `POP_TOP` 所在的那条过滤元组），核 sha256
`fa43dbc9e878eeacbfe0`（102871 B／1947 行 CRLF，与实测镜像 `mirr_c` 逐字节相同）。

```python
for instr in pre_instrs:
    if instr.opname in ('RESUME', 'NOP', 'CACHE', 'PUSH_NULL'):
        continue
    if instr.opname == 'POP_TOP':
        # [R32-C 同层判据 · 原则 1 块 = 前导语句 + 尾终止] POP_TOP 是「栈上的值被
        # 丢弃」的语句终止符，不是填充指令 —— 调用方把「pre_comp_instrs 末尾是
        # STORE/POP_TOP/IMPORT」当作语句边界，本扫描器却把同一 op 当噪声滤掉，
        # 两侧必须同层一致。它闭合此前累积的栈上表达式并作为 Expr 语句发射；累积
        # 段为空（该行没有值被丢弃）时与既有行为逐字节相同。
        if current_instrs:
            _r32c_expr = self.expr_reconstructor.reconstruct(current_instrs)
            if _r32c_expr:
                stmts.append({'type': 'Expr', 'value': _r32c_expr})
        current_instrs = []
        continue
```

识别的是**同层结构**：一个 opname 类（值丢弃终止符）在语句流里的角色，以及「栈上是否已有累积的
值」这一局部结构状态；不读名字／常量／绝对偏移／条数／函数名，也不针对推导式种类。归约方式：
命中的块把本就已存在的语句发射出来；`current_instrs` 为空（该 `POP_TOP` 上方没有语句）或重建失败
时，控制流与既有行为逐字节相同。这是本轮唯一的发货判据，落在既有第三个核文件
`comprehension_generator.py`（Round 9/11/14 曾在此文件落地过判据，非新站点）。

## 五、本轮一手实测（编排方自己的镜像根 `D:/Temp/r32gate/c1`，非转述）

| 门禁 | 读数 | 日志 |
|---|---|---|
| G0 见证（首件，5 函数） | 落地核 `7/10`（`w1 17/12 j0`、`w2 17/12 j0`、`w3 19/14 j0`）→ 发货核 `10/10` | `g0_head.log` / `g0_c.log` |
| G0 见证（扩样，10 函数） | 落地核 `12/17`（`w1..w5` 全部 `j0`）→ 发货核 `17/17`；5 条 CONTROL 两把核下逐字节同 | `rp_head.log` / `rp_c.log` |
| G0 靶子＋CONTROL | `utils.pyc 20/22 → 21/22`；CONTROL `quotation.pyc 143/143`、`oauth2.pyc 11/11` 两把核 `SAME` | `g0_head.jsonl` / `g0_c.jsonl` |
| G2′ 38 合成复现 | `{"SAME": 38, "IMPROVED": 0, "REGRESSION": 0, "MOVED": 0, "other": 0}` | `g2prime_38.txt` |
| G3 100 承重锚点（98 ＋ round31 见证／CONTROL） | `{"SAME": 100, ...}` | `g3_100.txt` |
| G4 全 402 A/B（sha 优先，发货判据） | `SAME=400 IMPROVED=2 REGRESSION=0 MOVED=0 ERR=0`，`files fully matched: a=371 b=371` | `g4_ab402_sha.txt` |
| G4-d1 七个 deficit-1 文件 | `SAME=7 IMPROVED=0 REGRESSION=0 MOVED=0`（本判据与七个靶子无交集） | `g4d1_d1.txt` |
| G4′ 严格尺逐个变化产物 | `utils.pyc 24/26 σ2 Σ7 → 25/26 σ1 Σ2`；`wizard_quant_api.pyc 49/56 σ7 Σ22 → 50/56 σ6 Σ12` | `g4prime_utils.txt` / `g4prime_wizard.txt` |

G4 的两个 IMPROVED 是 `IQCommon/utils.pyc :: load_ini`（`18/13 → matched`）与
`IQCommon/strategy/wizard_quant_api.pyc :: get_strategy_finance_factor_info`（`28/18 → matched`）；
`MOVED=0` 表示除这两处外全 402 文件产物字节不变。

## 六、被排除的候选与已知代价（勿再取）

* **线 A（代理）整条不可沿用**：其报告给出的「全 402 A/B `SAME=379 IMPROVED=0 REGRESSION=1
  MOVED=22`」在其镜像根 `D:/Temp/r32gate/A` 内**没有任何产物**（该目录唯一含 `SAME` 字样的文件是
  它自己的 harness 副本 `r32c_A.py`），编排方无法复现亦无法否证；其「真实根因＝发射位点未置位既有
  标志」点名的 `handler_hoisted_excepthand`、`pending_trailing_suppressed_handlers` 两个符号，在
  `core/` 全树 grep **零命中** ⇒ 该归因连符号层面都不成立。⇒ 本轮既不落其候选，也**不把它的名词
  接线结论移交下一轮**；「缺失的重复清理尾声」这一形状仍开放，Round 33 必须从落地字节重新一手测量
  后再立判据。可留用的只有它的结构探针输出（`logs/A-p13_pred.log`：函数出口块 `POP_EXCEPT +
  LOAD_CONST(None) + RETURN_VALUE`、无后继、全部前驱为纯 POP_EXCEPT 清理块）与它的候选 spec
  （`logs/A-candidate-spec.json`），二者均为**未经编排方证实**的线索。
* **线 B 的「R31-C 过火」归因**：被 Round 31 归档的 `g4_ab402_sha.txt`（`strategy.pyc` 为 SAME）与
  `268/247` 在 Round 30 落地核上的既有读数否证；其 `oauth2.pyc 71/72` 亦与实测 `11/11` 冲突。
  其块级观察（兄弟分支入口块被并入停止集）保留为**未经证实的线索**，与本轮发货判据无关。
* **本判据不翻转任何文件**：`utils.pyc` 仍有 `load_yaml 55/55 j0 t32`（等长错位，另一形状），
  `wizard_quant_api.pyc` 仍有 4 个 unmatched。官方计数池与 Round 31 同形（`partial 31`），
  函数级 `+2`。
* 「一条语句被整条滤掉」的形状在 `d1list` 七个靶子里 **零命中**（`G4-d1 SAME=7`），故本轮不声称
  触及 Round 31 移交的任何一个靶子。
