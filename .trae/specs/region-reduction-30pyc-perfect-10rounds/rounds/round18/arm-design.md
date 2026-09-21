# Round 18 设计（arm-design）：R18-A 生成端 and 链发现的 elif 唯一归属守卫

本轮一条根因线（R18-A）。取证与实测记录写在 `fixes.md`，结果写在 `OUTCOME.md`；
形状级复现与双世界实测表在 `test_repros/round18_arm/ANALYSIS.md`。

## 1. 症状与定位方式

Round 13 起，`fly/data/quotation.pyc` 的磁盘产物（Round 9 `393d9ff0`）与当前核的再生成结果
每轮都差一个函数（产物 148/150、核 147/150），闸门每轮 `WORSENED(rolled back)`
—— 即 SubTask 13.3「产物/核漂移」。定位手法：把候选修订的 `core`+`bytecode`+根目录 `*.py`
用 `git archive` 解到 `D:/Temp/r18/mirror/<rev8>`，配 HEAD 的 `quotation.pyc` 与
HEAD 的 `_r10_strict_check.check_pyc`，在镜像里重生成并逐函数比对（仓库零写入）：

| 修订 | 轮次 | quotation |
|---|---|---|
| `393d9ff0` | Round 9 | 148/150 |
| `675ca714` | Round 10 | 148/150 |
| `8a1b1def` | Round 12 | 148/150 |
| `f89b85f2` | Round 13 | **147/150**（新增 `<module>.change_future_real_date`） |
| `8d44386c` | Round 15 | 147/150 |
| `8145f6ff` | HEAD | 147/150 |

⇒ 退化点在 Round 13 的「生成端 and 短路链发现回退」（A1）。

## 2. 病根（一句话）

Round 13 的 `_discover_predicate_and_chain` 按 CFG 拓扑反向收集 and 链合取支时，
判据只有「前驱末跳转目标 == 本块汇合目标 + 前驱 fallthrough 进入本块 + 前驱不是某区域的
entry 兼 condition_block」。`elif X:` 的条件块恰好满足前三条，却不是任何区域的 entry
（它只是**父**链区域的 `elif_conditions` 成员），于是被当成臂内尾随 `if` 的首个合取支，
把外层测试重复发射成 `if X and X < e:`。块级数值见 `test_repros/round18_arm/ANALYSIS.md` §一。

这是禁止的「跨区域跨层次」用法：同一块同时充当两个区域的结构成员，违反原则 2
（每个块在任何场合只属于一个区域）。

## 3. 修法：只补唯一归属判据，不加新规则

守卫与既有「前驱是嵌套 if 头（entry + condition_block）」同构，只是认领来源从
`get_entry_region_for_block` 换成「任一其它 IfRegion 的 `elif_conditions` 包含它」：
命中即放弃整条链回退，交由既有单条件生成路径发射。生成层不新增任何形状识别、
不做层次/循环豁免，因此 Round 17 删掉的那类「跨层次放行」不会以另一种形式回来。

备选与放弃理由：
- 给链尾块加「纯净性」要求 —— 是新的形状判据，且真实 and 链的链首本就允许前缀赋值
  （`t = x > 1; if t and y > 2:`），按纯净性一刀切会打掉 24 号负对照；放弃。
- 只在「前驱与 region 不同层次」时放弃 —— 层次本身不是病根，唯一归属才是；
  且 Round 17 刚删掉一条按层次放行的豁免，不应再以层次为判据。放弃。
- 改用 `break`（停止扩展但保留已收集链）而非 `return None` —— 语义上更宽，
  但实测两种写法在 20 个复现与 quotation/quote 上结果相同（27 号锚定形状两世界皆 MATCH），
  故取与相邻守卫一致的 `return None`，不引入未验证的行为差异。

## 4. 门禁计划（按 Mandate 顺序）

1. 单点：`<module>.change_future_real_date` 单函数重生成 → 严格尺子 OK
   （`D:/Temp/r18/r18_fn.py`，秒级回路）。
2. quotation.pyc：镜像外全模块重生成 + 逐函数严格比对 → 与磁盘产物缺陷集合逐名相同。
3. 全量产物回归：`_r13_gate.py` 覆盖 `pyc_index.json` 全部 402 条目，分 8 片、每片一条命令
   （单条命令 <300 s），逐文件判 CLEAN/UNCHANGED/IMPROVED/WORSENED(rolled back)/REGRESSION。
4. 复现电池：`test_repros/round18_arm/`（20 项：11 SENTINEL + 8 负对照 + 1 UNCONFIRMED）
   与既有 8 套 `--strict` 全绿。
5. 索引回填：只用项目工具 `scripts/pyc_batch_verify.py single` 的实测写回，
   收尾以 `stats` 的累计匹配率作为唯一对外序列。
