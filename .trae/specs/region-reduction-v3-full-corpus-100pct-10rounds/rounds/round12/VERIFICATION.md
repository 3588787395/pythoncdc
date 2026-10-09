# Round 12 验证记录（VERIFICATION）

起点 = round 11 终态：单元 **6580/6617**（99.4408 %），文件 **387/402**，残余 **15 文件 / 37 单元**。
本轮所有读数一律出自 `scripts/pyc_verify.py`（同脚本、同判据）与
`gate_round.py` / `residual_report.py`，不引用生成文件的手工修改（役规：禁止修改反编译生成的文件）。

## 一、本轮落地的仓库改动

| 提交 | 内容 | 认证方式 |
|---|---|---|
| `28c113d9` | 两处**纯注释**事实块 `[r11-b159-fact]`（循环收尾「只登记不发射」的后果与「同 entry 重复区域」失真） | `ast.dump` 与封存字节相等 + quotation/handlers/realtime_event_source 三产物逐字节相同 + 七套件 `2 failed / 280 passed / 2 xpassed` + selfcheck OK（不需 402 门） |
| `3a648cd3` `294786ce` `91e8cdcb` `8084975b` | round12 工单文档（T12-09 判决、matcher 诊断、T12-21 落地票） | 文档，不动代码 |

代码面 **净变化为 0**：T12-09 与 T12-18 两个候选都按「无翻正即逐字节撤回」处置，
T12-21 的门判决见 §三（本文件不预判）。仓库 core 当前状态在门链结束后由 §三定。

## 二、本轮工单账（每票：判据 → 实测 → 处置）

| 票 | 判据/假设 | 实测读数 | 处置 |
|---|---|---|---|
| T12-01/02 | 「已发射区域入口」不可判别 ⇒ 建台账 | 台账可建（`:25228` 一处记账即覆盖嵌套派发） | 并入 T12-09 |
| T12-05/06/08 | 只在 `:25235` 加认领豁免 | 逐字节不变（惰性） | 撤回；**原因实测**：最先写 `generated_blocks` 的是 `:21200/:21202`（重绑定免疫探针 t1218） |
| T12-09 | 三处认领豁免 + 发射台账 | 全量门 label 12：`6580/6617 -> 6580/6617`、`387 -> 387`、翻正 0、回归 0；evt 产物 20555→21692（回收 63 指令） | **撤回**（fires without flips）；文档 `FIX_T1209_CLAIM_EXEMPTION_FALSIFIED.md` |
| T12-12（诊断） | matcher 的 @2164 语句头被吞 = 识别缺失 | 否：**识别建了** `IfRegion@2164`；是 `IF_ELIF_CHAIN@2038` 把它收成 elif 后遭 `:1672-1691` 吞并（36→32 区域） | 诊断成立，自订正两条本票先前推断 |
| T12-18 | 钳制 `:1677` 吞并判据即可复原 | 五文件产物**逐字节相同**；原因：链 `blocks` 本身含 2164，归属未变 | **不落地**；结论：决定物在收集侧 |
| T12-21 | elif 臂候选的每条前驱必须归 `header_` 的区域 | matcher `net=+10 hunks=25 real=1` → `net=+0 hunks=4 real=0`；七文件零连带；全仓 regen 后**仅 1 个产物变化** | 门 label 13 判落地（见 §三） |

## 三、门（label 13，链日志 `D:/Temp/r142/install_gate13_1106.log`）

*（本节数字由链出，不手填。已到位的部分：）*

- regen `ok=402 bad=0`；regen 后 `git status --porcelain -- site-packages/` = **1 行**
  ⇒ T12-21 的改动面在全仓 402 个产物里**只触及 matcher 一个文件**；
- verify 分片 0–5 与 round 11/12 完全同读数（780/786、465/469、538/538、884/887、852/855、994/999）；
- 安装自证：备份 `e926a54f17753b33`、落地 `48b812e60ef52d27`、marker 命中 1、`py_compile` OK；
  仓库内构建复现镜像读数（matcher 产物 13345、quotation 153/153、handlers 29/30、
  wizard_quant_api 55/58、bar 84/85）。
- 待填：verify 分片 6–7、`[units]`/`[files]`/`[gates]` 汇总、checks 四门、residual 表与 `UNREGISTERED`。

**判决规则（写死，不改口）**：`翻正单元 ≥ 1` 且 `新增失败单元 = 0` 才保留；
否则 `cp D:/Temp/r142/pre_t1221_analyzer.py core/cfg/region_analyzer.py` 复原到
`e926a54f17753b33`，并用 HEAD 代码删除重生成 matcher 产物，使 `git status -- site-packages/` 归零。
两种结果都要把补丁留在 `D:/Temp/r142/analyzer_t1221_land.py` 作为 T12-22 的共要件。

## 四、本轮是否满足「至少解决一个 pyc」

**尚未满足。** 截至本文书写入时，本轮没有任何整文件翻转：残差仍是 15 文件 / 37 单元，
T12-21 使 matcher 的**缺陷内容**减少一条（被吞语句回来了），但该单元仍因 4 条跳转落点而红。
按役规「没解决一个 pyc 不得进行下一轮」，round13 不在 T12-21 判决 + T12-22 出结果之前开启；
下一步的靶仍是同一条链：matcher（16/17，四落点）与 realtime_event_source（12/13，空臂归属）。

## 五、本轮的方法账（跨轮适用，均已进 memory）

1. **惰性自证只认 CLI-vs-CLI**：进程内 `d.decompile(buf, use_region=True)` 与 CLI 产物本身差约
   90–100 字节，曾用它误判一台探针「扰动」（t1211）；也曾用它漏判真扰动（方法包装）。
   本轮 t1213/t1216b/t1217/t1219/t1220 全部以 CLI-vs-CLI 证惰性（13255 = 13255）。
2. **行级插入必须用锚行自己的缩进**：t1214 把 8 空格语句插进 12 空格块，静默反缩进，
   产物 13255→11031，仍能编译、仍打印看似合理的读数。
3. **同名/首匹配假读数**：`p1_census.py` 的 substring 过滤先用 `set_matching_type@66`、
   再用 `is_current_match@169` 命中，两次都不是 `DefaultMatcher.match`；已加 `!name` 精确模式，
   正对照 = `dumped=True` 且表头 `UNIT match@176 blocks=78 regions=45`。
4. **零读数要先有正对照**：`grep` 无输出（如 `elif_conditions.append`）不代表不存在，
   本轮改查 `elif_conditions` 全量引用才找到 `:22813` 的真实装配点。
5. **自订正入册**：本票族里我自己写错又被实测否掉的三句（「就地派发从未发生」、
   「`_generated_regions` 的 id 排除是拦路条件」、「负极性的空臂」）都留在文档里并标明证据，
   不删改历史读数。
