# FIX B129 — 交接失败后不得把块标成「已生成」：`_leading_*` 静默丢弃修复回报

票面：`IMPL_B129_MATCHER_LEADING_GUARD_BRIEF.md`（Round 10 实现票）
诊断凭据：`DIAG_B128_MATCHER_DROPSITE.md` Q1/Q2（trace `D:/Temp/r10diag/probe4.out`）
Scratch：`D:/Temp/r129/`
工作树基线 sha256（已核对，与封表值一致）：
- `core/cfg/region_ast_generator.py` = `e9a8f65f6451bcc895c5558528b03a9d6ef1045f418f0efd267f9900ef174e74`
- `core/cfg/region_analyzer.py` = `38a1d5142d132fd7288229851a33a02df71ccb3cf98ee40f84d4042bb8d1135e`

## 状态勾选（边做边写）

- [ ] §一 基线电池（14 臂，`files` 必须＝14）：红/绿分名单
- [ ] §二 实现：判据 = 「登记为已生成」⇔「语句确被接手（可测事实）」
- [ ] §三 靶内复测：红臂→绿，对照臂仍绿
- [ ] §四 靶点：`matcher` 17/17 + 产物含 `order.asset.symbol[None:3] in ('688', '689')`
- [ ] §五 哨兵：anchor 454/454、quotation 153/153、small34 1528/1568 & 18 files
- [ ] §六 `:54913` 注释/行为矛盾修正 + 触及方法补六项模板与 C1/C2/C3
- [ ] §七 代码已落地 / 仅归档 spec 未落地 ＋ grep 标记

## 票面摘要（绑定条款复述）

缺陷一句话：重建成功的条件表达式被**递延**给一条无人读取的交接记录（`_leading_operand`
唯一消费者 `_graft_pending_operand` 只在 `BoolOpRegion` 路径被调；本例落空块入口是
`IfRegion` ⇒ 写了永不读），而 `_leading_guard_candidate` 又在自己的 [C3] 守卫 `:38496`
（`parent is not None`）处返回 False，`:54918` 还把这个返回值丢弃，随后 `:54920` 登记块为
已生成、`:54921` 返回 `[]` ⇒ `:1887` 的逐语句降级也永不可见 ⇒ 10 条指令静默消失。

必须实现的规则：**「把块登记为已生成」与「该块语句确实被某处接手」同命题**；「接手」必须是
可测事实（返回值 / 记录是否落在会被读的区域），不得是「调用过 setter」。无人接手 ⇒ 就地发射
语句 ＋ 不加入 `generated_blocks`。

禁止（每条有本轮前例）：放宽 `:38496` parent 守卫；按文件名/函数名/偏移 `2164`/指令数 10/
嵌套深度特判；只不登记却不就地补发射；`_fix_/_merge_/_patch_/_fallback_/_hack_/_workaround_/_temp_`
前缀新方法（G3）；硬编码阈值（G4）；真 `BoolOpRegion` 宿主必须逐位不变（负对照）。
无任何 git 写命令。单命令 <300s。`python -X utf8`，不设 PYTHONIOENCODING。BOM+CRLF，按字节 patch。

## 主代理盘点（2026-10-08 08:55，覆盖上面所有勾选项的现况）

本回报由首发工程师在「核对基线 sha256」之后、跑任何电池之前被会话中断杀死，
七个复选项**全未执行**，不代表任何进度。主代理实测盘点：

| 项 | 读数 |
|---|---|
| `core/` 工作树 | `git status --porcelain -- core/` 为空；工作树字节 sha256 前 16 位 `region_ast_generator.py=e9a8f65f6451bcc8`、`region_analyzer.py=38a1d5142d132fd7`，与封表值逐位一致 ⇒ **未落任何生产码** |
| 被杀工程师留下的污染 | `test_repros/round3/r3_a14_three_arm_inner_chainOK.py` 是**改后字节**产生的过期产物（`LOG.info(info)` 从 else 臂内被移到臂外），已 `git checkout --` 单文件恢复；恢复后 `git status --porcelain -- test_repros/` 为空 |
| 票面锚点复验 | 主代理按当前 HEAD 字节复核 5 个锚点全部命中：`:54896 _cjb_skip_inline_if` 分支、`:54906 setattr(...,'_leading_operand',...)`、`:54918 self._leading_guard_candidate(...)` **返回值被丢弃**（无 `if not` 判定）、`:54920 self.generated_blocks.add(block)`、`:54921 return stmts`；`:38496` 守卫② 前的 `parent is not None → return False` 亦在位。判据成立，票可执行 |
| 重派 | 本票**重派一次**，要求：先跑自有 14 臂基线（`files`＝14）并把红/绿名单写进本文件，再动码；边做边写，受阻也要把已证/已否证写进本文件 |
