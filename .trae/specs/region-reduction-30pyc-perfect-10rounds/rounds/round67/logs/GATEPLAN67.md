# Round 67 · 串行门禁计划（集中验证 → 落地 → 门禁 → 归档）

纪律：**门禁链严格串行**，链中不并跑任何东西（包括我自己的只读 python）；每条命令 <300 秒，
402 全量与 402 A/B 用 background 任务跑并把输出重定向到绝对路径日志。
所有路径为绝对路径；`h62.py` 的 `--mirror` 相对 `D:/Temp/opencode/r67gate`，`--spec` 相对当前目录
⇒ 统一从 `cd D:/Temp/opencode/r67gate` 里调用 `land67.py`（spec 用裸文件名）。

## 阶段 A：集中验证（对每批候选逐臂、单变量）
1. `python -X utf8 center/h62.py build --spec=<cand.json> --dst=<arm>`（镜像==工作树断言即「落地前字节」证明）
2. 同臂跑四张名单：`all16.txt`（靶）/ `battery.txt`(31) / `canary.txt`(4) / 复现 `txt`
   → `dump/<arm>*.jsonl`；对照列固定用 `center/dump/landed16.jsonl`（593/641、48 缺陷、Σ|Δ|328、Σjd184、Σtd9405）
   与 `diag*/dump/landed_*.jsonl`。
3. `h62.py ab --a=… --b=…` 逐臂读数；**采纳条件**：金丝雀 4 sha 逐字节不变 ∧ 电池 31 项不劣
   ∧ 名下靶支严格变好 ∧ 无 ERR ∧ 锚点在当前落地字节 `count==1` ∧ 判据同层次且注释三要素齐。
4. 符号核对：spec 里点名的每个函数/参数先 `grep -n` 存在、再看调用次数（不采信代理口述行号）。

## 阶段 B：合并与落地
5. `python -X utf8 mkfinal67.py m67 <spec…>`（逐文件按偏移排序合并 + 链式锚点唯一性证明）
6. `python -X utf8 mbuild67.py m67e specs/…`（多文件镜像；一个 core 文件一份 spec）
7. `python -X utf8 center/closeout67.py landproof mirr_m67e` ⇒ 必须 `same>=20 diff=0`
8. `land67.py land --spec=m67e_region_ast_generator.py.json --mirror=center/mirr_m67e`（干跑）→ 复核
   → `--apply` → 再 `landproof`；BOM/CRLF 计数按落地注释核对。

## 阶段 C：串行门禁（顺序不可换）
- **G1** `single` 跑本轮「修到完全 OK」靶（双尺 100%；未达 100% 则本轮禁止进入 G2）。
- **G2** 金丝雀：`quotation.pyc` 官方 143/143 + 严格 148/150（缺陷集逐字须为
  `change_his_to_forward #250`、`get_trend #10`）；`market_time` 官方 10/10 + 严格 10/10。
- **G3** `batch --index pyc_index.json --all --round 67`（402 verified / 0 failed；background 跑）。
- **G4** `stats --index pyc_index.json` → 只发布本轮 `stats` 打印的 funcs/matched/rate（Σfc 冻结 5746）。
- **G4′** 严格尺跑全部已发布产物：`center/strict_repo67.py all16.txt dump/strict_repo_r67_after.json`
  （内含 build_m67e 镜像 sha 一致性标记）。
- **G5** 索引审计 `center/audit5_g5_67.py`（HEAD vs 工作树逐条比对：无增删、仅轮次戳/实质项分类）。
- **G5′** 产物 blast `center/blast67.py landed m67e …`（改动产物必须恰好等于 MOVED/IMPROVED 集；未手改任何 `*OK.py`）。
- **G6** 电池两列 `closeout67.py battery landed m67e`（31 项；候选列不得比 landed 差）。

## 阶段 D：归档 + 提交 + push
- `center/archive67.py` 单向拷 scratch→`rounds/round67/batches/*`（含被拒臂）与 `logs/`；
  写 `rounds/round67/OUTCOME.md`（7 节）与 `logs/EVIDENCE.md`（A–F）。
- `git add` **只列显式路径**（禁 `add -A`）：两个 core 文件、`pyc_index.json`、变动的 `*OK.py`、
  `rounds/round67/**`、`test_repros/round67_*/**`。
- 提交后 `python -X utf8 center/gitpush_redact67.py`（脱敏 + `RAW-CREDENTIAL-TOKENS-IN-OUTPUT=0` 反向夹钳），
  再断言 `git rev-list --count refs/remotes/origin/main..HEAD` == 0。
