# R73 · fix2（修复工程师）BRIEF —— 嵌套 try-except（F-ABSORB 主体，70 单元最大族）

## -1. 用户裁定（最高优先级，覆盖 R71/R72 的否定结论）

**用户明确指认：头部 control-flow 失败的根因就是「嵌套 try-except 问题」。**
R71 diag1 曾实测「否定多数是嵌套 try-except」的线索——该结论按用户裁定**作废/需重审**：
重新假设头部 cf 分歧来自 **try/except（含 try 套 try、try 包共享尾、try 在 elif 臂内、
try-else 异常表拼接）的归约路径**，探针与根因分析优先打 try/except 相关判据行
（exception table、`_process_try`/try 区域识别与发射、try 内共享尾吸收），再回看
boolop/链尾判据是否只是 try 归约错误的**下游表象**。

## 0. 使命

mandated ruler 剩余 88 个失败单元里 **F-ABSORB ≈ 70 个**（R72 diag1 实测族聚类，
`族×判据 = cf 65 + bc 5`），是本轮最大族，也是 41 支 failure 的主体。
你的使命：**从「嵌套 try-except 归约」这一根因假设出发端到端打 F-ABSORB 可钉死子族，
产出候选 patch spec 并在镜像上验证**（不碰 repo、不落地），**按子机制拆臂自证**
（ADR-1），目标之一是让某支 pyc 从 failure 变 **success（完全 OK）**。

工作区：`D:/Temp/opencode/r73gate/fix2`；基线 HEAD = **R72 提交 `8d136040`**，
h62 `--arm=landed` = repo（R72 字节）。**镜像臂名一律 `abs*`**（`mbuild73.py abs1 …`）。

## 1. 输入数据

- `filecat.json`（41 支 failure 明细）、`targets.md`、`G3v_pycverify_r72.json`。
- R72 diag1 交接 FACTS 的 F-ABSORB 节（两个子机制 + 判据行 + 已有 synth 复现）。

## 2. 两个子机制与判据行（R72 实测，R73 HEAD 行号需重核）

- **① and 链共享 else**（R72 synth a02/a03/a05/b04/b05 等 11 支 F-ABSORB 复现）：
  - `region_analyzer.py:23303 _identify_boolop_regions`
  - `region_analyzer.py:26646 _try_unify_mixed_boolop_chain`
  - `region_analyzer.py:15929 _identify_conditional_regions`
  - 形态：`if A and B: … else: …` / `elif` 链共享 else 被拆成多层，落点指令不同或 len 变。
- **② if/elif 链尾被吞进 else 臂**：
  - `region_ast_generator.py:22512 [R71-thenover]` 影子认领守卫（**R72 实测仍不充分**，
    R71 fix2 只解决了 synth t01/t02/t22 一类）
  - `region_ast_generator.py:17753 _if_generate_normal`、`:15503 _if_generate_else_branch`
  - 形态：链尾语句被错误吸进 else 臂（落点 42→46 落不同指令，synth a02）。
- 细分（R72 FACTS）：27 支「落点同但 len 变」、40 支「落点落在不同指令」、3 支 opname 变化。

## 3. 步骤

1. 从 `filecat.json` 聚类失败单元到两个子机制（头部文件 `trade_live_broker` 14、
   `quote` 12、`trade_info_utils` 5、`real_quote` 4 是主战场），
   **挑一个可端到端钉死的子族**（优先已有 synth 复现的 ①）。
2. 复现：`python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single <pyc>
   --source <OK.py>`；`dis` 对比找第一条分歧（落点/len/opname 哪一类）。
3. 根因到行：monkeypatch 探针打判据行的判定路径（boolop 归并、链尾吸收入 else 的边界）。
4. 写 spec：`{"file": "core/cfg/<x>.py", "edits": [{"anchor": LF 文本恰出现 1 次, "repl": ...}]}`
   —— **repl 内嵌三要素注释（识别条件/归约方式/AST 映射）**；同层次结构身份判据：
   无函数名/文件名/偏移/阈值启发、无名字白名单、无新增 self 状态、无跨层
   `region.entry in r.blocks` 型模式。
5. **拆臂自证**（ADR-1，R70 quote T1/T3 拆臂被证伪回退的教训）：每处编辑单独成臂
   （abs1/abs2/abs3…），单臂单 edit，各自跑验证闭环；合并臂（absm）最后单独跑一遍。
6. 验证闭环（每件候选）：
   a. `python -X utf8 mbuild73.py abs1 specs/<候选>.json`（锚点断言必须全过）；
   b. 靶支：h62 `run --arm=abs1` 官方读数**逐项不变或改善**（不得回退）+ mandated
      `pyc_verify.py single <pyc> --source build_abs1产物` 失败单元**清零或减少且零新增**；
      **优先挑「修完全清」的文件**（mandate 最短路径，例如 trade_info_utils 5 单元全清
      即 1 支 failure→success，且顺手清掉 R70 遗留 #94）；
   c. 金丝雀：market_time `af77224b34b203c4`、datetime_func `e711b8ea86d49a15` /
      `9d09af09249da177`、quotation `3eb76e512df9ab1e` 四支 sha 与 R72 逐字节相同
      （quotation 的 `change_his_to_forward` 若动，仅允许真实转绿且官方 143/143 维持）；
   d. 电池：`python -X utf8 closeout69.py battery landed abs1` worse-than-landed=0；
   e. 严格尺：`python -X utf8 sstrict67.py build_abs1 <名单> <out>` 无新增缺陷函数。
   （b–e 原始输出存 `dump/`，供中心复核。）

## 4. 硬约束

- **不修改 repo 任何文件**（`land73` 只可 dry-run 断言，禁止 `--apply`）；402 全量扫描禁止。
- 每条命令 <300s；region_analyzer 里用 dis 必须局部导入（宽 except 吞 NameError 陷阱）。
- h62 list 文件 LF 无 BOM、跑前删旧 jsonl；sstrict67 第一参数是本工作区 `build_abs1`。
- ADR-1：缺失/过冲族要求 Σ|Δ| 净减且不得以少发射换；位移族（counts 相等）要求 hunk
  严格降 + first_diff 回移 + Σ|Δ| 不升；**任何他支回归即整件拒收**。
- 与 diag1/fix1/fix3 并行：若根因与他批重叠（+4 落点也可能是 F-PAD、链尾也可能涉
  thenover），在 FACTS 里标注重叠面并给区分证据，交中心裁定。

## 5. 交付

- `FACTS.md`（子机制聚类、根因表、每臂 a–e 验证读数、合并臂读数、与他批边界证据）；
- `specs/*.json`（每候选一份，anchor 断言自检打印）；
- `synth/*.py` 最小复现（若有）。
