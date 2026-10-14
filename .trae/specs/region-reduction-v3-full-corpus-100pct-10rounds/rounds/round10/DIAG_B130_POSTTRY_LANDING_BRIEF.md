# Round 10 诊断票 B130 简报：F1「try/except 之后的顺序续体被让给 handler 尾声」的宿主在哪

**范围：只诊断，禁改 `core/`，禁 git 写，不建大电池，不跑全量门禁。**
（两段式派工：诊断先钉宿主，实现票再动判据 —— B126/B128 两次 150 回合截断的直接教训。）

## 一、要定位的现象（已实测，勿重推）

同一形状在**两个不同文件**上复现，且都是「只差 1 单元」的文件：

| 单元 | 一条跳转 | 原始该落之处 | 产物实落之处 |
|---|---|---|---|
| `fly/dumpload/load_daily.pyc :: <module>`（26/27） | `#654 JUMP_FORWARD` | `@2478`＝`print('++++++结束更新的执行时间' + time.strftime('%Y%m%d %H:%M:%S'))`（try/except **之后**的语句） | `@2562`＝`JUMP_FORWARD→2626; PUSH_EXC_INFO; except Exception as err:`（**异常处理器区**） |
| `IQCommon/util/trade_info_utils.pyc :: <module>.get_trade_status`（37/41） | `#112 JUMP_FORWARD` | `@151` 起＝两臂共用的 `error_no == 0` 测试段 | `@147`＝`POP_EXCEPT; RERAISE; …`（handler 尾声） |

（仪器与逐边打印见 `rounds/round10/FIX_LANDING_R10_BRIEF.md` §九 F1；原始/产物双侧块窗由
`D:/Temp/r9main/unitmap.py`＋内联探针复演。）

**读法**：跳转本身没丢、opcode 没错，错的是**它被接到哪个块**——链后/try 后的顺序续体被交给异常区，
于是产物在语义上「跳过 except 之后的代码，落进处理器」，重编译后控制流图不同 ⇒ 判据报
`Different control flow`。

## 二、要回答的四个问题（写文件 `rounds/round10/DIAG_B130_POSTTRY_LANDING.md`，边做边写）

1. 对这两条语句所在块跑 `build_cfg` + `CFGRegionAnalyzer.analyze()`：
   `try/except` 生成的 `TryExceptRegion` 的 **`natural_exit` / `merge_block` / 其后继**各是谁？
   被错接的续体块（`load_daily` 的 `@2478`、`get_trade_status` 的 `@151`）在其中以何身份出现（成员？
   `else_blocks`？完全不在区域里？）？
2. 发射端在哪一步用**什么依据**为这条跳转挑落点（候选枚举 → 评分 → 取首）？
   给出 `文件:函数:行` 与该行的选择依据（白名单事实：块末 opcode／后继前驱／异常边／区域成员）。
3. 两文件是否**同一处**代码致错？若是，一条判据即可；若否，分开报告（禁止为了「一判据吃两文件」的好看结论而强行并案 —— 本 campaign 已有三次「look-alike 实为另一机制」的前例）。
4. 最小复现：≤4 条（`try/except` 后跟一条语句、`try/except/else`、嵌套 `for` 内的 `try/except` 后语句、
   以及一条**已正确**的对照：`try/except` 后无语句）。只需说明哪些复现，不必建电池。

## 三、约束（与本 campaign 全局一致）

- 探针从仓外导入 `core`（`sys.path.insert(0, ROOT)`），**不得**改 `core/` 任何文件；
  临时输出写自己的 scratch（建议 `D:/Temp/r130/`）。
- 禁任何 git 写命令（内存紧张，git 还会因 867 条 `wt_head` 长路径刷屏；用 pathspec 精确取数）。
- 单条命令 ≤300s；`python -X utf8`，禁 `PYTHONIOENCODING`；读源码用 `encoding='utf-8-sig'`。
- 产物一律由 `python -X utf8 pycdc.py -o <out> <rel>` 生成到 scratch，
  **不得**删除/覆盖 `site-packages/` 下任何 `*OK.py`。
- 不得把「块是区域成员但不是 `condition_block`」这类**无判别力**的计数当证据（见
  `FIX_OMISSION_R10_BRIEF.md` §十：`then/else/body` 成员本就不该是 condition，12/13 是正常值）。
  吞并/错接的证据须是**合取**：身份 ∧ 产物 AST 内是否有对应语句（`DIAG_B128` Q0-Q1 即此形）。

## 四、这张诊断票的产出如何被使用

实现票只消费三样东西：**宿主 `文件:函数:行`**、**误发条件的白名单表述**、**是否静默豁免**（若是，
它本身就是一处 `rules.md §1.5 C3` 违例，须与主修同票封闭，不得留「以后再补」）。
预期收益（由主代理实测名单给出，非承诺）：`load_daily` 26/27→27/27、
`trade_info_utils` 37/41→38/41（该文件另需 #15 的 2 条与换位 1 条才翻正）。
