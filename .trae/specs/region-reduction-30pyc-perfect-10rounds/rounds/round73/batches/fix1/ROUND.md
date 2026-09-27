# R73 · fix1（修复工程师）BRIEF —— F-PAD 族（落点一律 +4）

## 0. 使命

mandated ruler 剩余 88 个失败单元里 **F-PAD = 14 个**（R72 diag1 实测族聚类）：
指令流全同、仅跳转落点偏移**一律 +4**。你的使命：**端到端钉死 F-PAD 族，
产出候选 patch spec 并在镜像上验证**（不碰 repo、不落地），
目标之一是让某支 pyc 从 failure 变 **success（完全 OK）**。

工作区：`D:/Temp/opencode/r73gate/fix1`；基线 HEAD = **R72 提交 `8d136040`**，
h62 `--arm=landed` = repo（R72 字节）。**镜像臂名一律 `pad*`**（`mbuild73.py pad1 …`）。

## 1. 输入数据

- `filecat.json`（41 支 failure 明细）、`targets.md`、`G3v_pycverify_r72.json`。
- R72 diag1 交接 FACTS 的 F-PAD 节（判据行 + 已观测位移清单）。

## 2. 族签名与判据行（R72 实测，R73 HEAD 行号需重核）

- **签名**：失败单元第一条分歧 = 跳转落点偏移 +4、**指令条数与 opname 全同**；
  已观测位移：614→618、644→648、310→314、638→642、726→730、138→142、332→336、
  434→438，另有大位移变体 198→236、158→364、380→404、148→174、506→934。
  机制：相邻 return-None / 清理尾声块重排一个 4 字节槽。
- **判据行（region_ast_generator.py）**：
  - `:185 _is_duplicated_cleanup_exit_return`（重复清理退出 return 判定）
  - `:26482 [R35-B]` 注释段（重复清理尾声**非终末副本**不得物化为 `return None`）
  - `:14865 _if_generate_then_branch`（R71 known-unfixed 行）
- synth 对照：R72 `a04_sibling_return_none`（`<module>.post`，落点 72→76）是 F-PAD 最小复现。

## 3. 步骤

1. 从 `filecat.json` 全量扫出**签名匹配**的单元（指令流全同 + 落点 +4 / 大位移变体），
   列出命中的 pyc/单元清单（预期 ~14 单元，分布在数支文件）。
2. 复现：`python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single <pyc>
   --source <OK.py>`；`dis` 对比找第一条分歧（确认 +4 签名，排除 F-ABSORB/F-POLARITY 混入）。
3. 根因到行：monkeypatch 探针打 `_is_duplicated_cleanup_exit_return` / `[R35-B]` 路径
   的判定与物化决策，找出**为什么多物化/少物化一个 4 字节槽**。
4. 写 spec：`{"file": "core/cfg/<x>.py", "edits": [{"anchor": LF 文本恰出现 1 次, "repl": ...}]}`
   —— **repl 内嵌三要素注释（识别条件/归约方式/AST 映射）**；同层次结构身份判据：
   无函数名/文件名/偏移/阈值启发、无名字白名单、无新增 self 状态、无跨层
   `region.entry in r.blocks` 型模式。
5. 验证闭环（每件候选）：
   a. `python -X utf8 mbuild73.py pad1 specs/<候选>.json`（锚点断言必须全过）；
   b. 靶支：h62 `run --arm=pad1` 官方读数**逐项不变或改善**（不得回退）+ mandated
      `pyc_verify.py single <pyc> --source build_pad1产物` 失败单元**清零或减少且零新增**；
      **优先挑「修完全清」的单单元文件**（mandate 最短路径）；
   c. 金丝雀：market_time `af77224b34b203c4`、datetime_func `e711b8ea86d49a15` /
      `9d09af09249da177`、quotation `3eb76e512df9ab1e` 四支 sha 与 R72 逐字节相同；
   d. 电池：`python -X utf8 closeout69.py battery landed pad1` worse-than-landed=0；
   e. 严格尺：`python -X utf8 sstrict67.py build_pad1 <名单> <out>` 无新增缺陷函数。
   （b–e 原始输出存 `dump/`，供中心复核。）

## 4. 硬约束

- **不修改 repo 任何文件**（`land73` 只可 dry-run 断言，禁止 `--apply`）；402 全量扫描禁止。
- 每条命令 <300s；region_analyzer 里用 dis 必须局部导入（宽 except 吞 NameError 陷阱）。
- h62 list 文件 LF 无 BOM、跑前删旧 jsonl；sstrict67 第一参数是本工作区 `build_pad1`。
- ADR-1：位移族（counts 相等）要求 hunk 严格降 + first_diff 回移 + Σ|Δ| 不升；
  **任何他支回归即整件拒收**；不得以少发射换。
- 与 diag1/fix2/fix3 并行：若你的签名与他批族重叠（+4 落点也可能由 F-ABSORB 造成），
  在 FACTS 里如实标注并给出区分证据（指令条数是否全同），交中心裁定。

## 5. 交付

- `FACTS.md`（签名清单、根因表、每候选 a–e 验证读数、与他批的边界证据）；
- `specs/*.json`（每候选一份，anchor 断言自检打印）；
- `synth/*.py` 最小复现（若有）。
