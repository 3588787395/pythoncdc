# R71 · diag1（测试工程师，只读诊断）BRIEF

## 0. 使命

Round 70 落地后，mandated ruler（`F:/Downloads/pythoncdc-main/scripts/pyc_verify.py`，pylingual
`compare_pyc`）对 402 支产物给出 56 支 failure。中心已解析分类：**Different control flow 102 个
失败单元（本轮重点）**、Different bytecode 17、Extra bytecode 6；其中 **48 支是官方尺 ok 但
pylingual failure 的「分歧集」**。你的使命：**只读诊断**分歧集里控制流失败最重的文件，定位
`core/cfg/region_analyzer.py` / `region_ast_generator.py` 的根因（到行号），按族聚类，产出
**≥10 支最小复现**与三要素判据提案（不写 patch，不改 repo）。

你的工作区：`D:/Temp/opencode/r71gate/diag1`（仪器已按本目录 ROOT 重定向）。
基线：HEAD = R70 落地提交 `b21c5c61`，repo core = R70 字节（h62 `--arm=landed` 即 repo）。

## 1. 输入数据

- `filecat.json`：56 支 failure 文件的逐支数据（official/pylingual 读数、失败类别计数、
  每支前 40 条 failure 明细串，串里含 pylingual 前缀命名的失败单元名）。
- `G3v_pycverify_r70.json`：全量报告（rows 有完整 failures）。
- 产物在 repo：`site-packages/**/*OK.py`；官方尺/严格尺仪器同 R70。

## 2. 诊断对象（按 cf 降序；A 组必做，B 组尽量聚类）

A 组（cf≥2，官方 ok）：`wizard_quant_api`(cf4, pyl 54/58)、`finance`(cf3, 29/32)、
`bar`(cf3, 82/85)、`jq_trans_module`(cf2, 63/65)、`fly_api/base`(cf2, 61/63)、
`strategy`(cf2, 25/27)、`flytools`(cf2, 64/66)、`future_contract_info`(cf2, 27/29)、
`load_daily`(cf2, 25/27)、`oauth2`(cf2, 10/12)、`ptradeAccount`(cf2, 135/137 —— R70 文本移位支，核实其 cf 失败是否 R70 前已存在)、`quotation`(cf2, 151/153 —— **金丝雀，只诊断不判死罪**，R71 是否允许打它由中心裁定)。
B 组（cf=1 长尾约 26 支 + cf=0 Different-bytecode 5 支）：按 failure 签名聚类成族
（例：position_model 三支 cf=0 Different bytecode 4/4/2 大概率同根因）。

## 3. 步骤

1. 从 `filecat.json` 提取每支的失败单元名；对每支跑
   `python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single <pyc> --source <OK.py>`
   复现 failure 明细（含单元 verdict 串）。
2. 对失败单元：`dis` 原始 pyc vs 重编译产物的该 code object，找第一条分歧指令（控制流类：
   跳转目标/跳转极性/块结构）。
3. 回溯到 region_analyzer/generator 的判据行（用 R70 同款探针手法：monkeypatch + 逐块打印）。
4. 写最小复现 `.py` 到 `synth/`（编译成 pyc 后用 pyc_verify single 验证 landed 复现同一类别失败）。
   **≥10 支**，覆盖尽可能多的族。
5. `FACTS.md`：每支靶的根因表（文件/单元/分歧指令/根因行号/族），每族给出三要素判据提案
   （识别条件/归约方式/AST 映射）与预期影响面（还有哪些文件同族）。

## 4. 硬约束

- **只读**：不修改 repo 任何文件；可以建自己的镜像与产物（仅限本工作区）。
- 每条命令 <300s；**禁止 402 全量扫描**（归中心）。
- region_analyzer 无模块级 `import dis`——探针里用 dis 必须局部导入，否则 NameError 被宽
  except 吞掉、产物静默退化（R67 实测陷阱）。
- h62 list 文件必须 LF 无 BOM；删旧 jsonl 再跑（resume 语义）；PowerShell 重定向写 UTF-16，
  一律用 python 侧写文件；`os.chdir` 会破坏相对路径，传绝对 pyc 路径。
- `sstrict67.py` 第一参数是本工作区 `build_<arm>` 目录名。
- mandated 单支验证：`python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single
  <pyc> --source <产物.py>`（--source 可指向镜像产物）。
- 判据提案必须是**同层次结构身份判据**：无函数名/文件名/偏移/阈值启发、无名字白名单、
  无新增 self 状态、无跨层 `region.entry in r.blocks` 型模式。

## 5. 交付

- `FACTS.md`（根因表 + 族聚类 + 三要素提案 + 影响面）；
- `synth/*.py` ≥10 支最小复现（附每支 landed 读数）；
- `specs/` 留空（你不出 patch），但每族给出「建议改 analyzer 还是 generator、大约几处编辑」。
