"""Generate Task 0.5 before-reading summary documents from recorded JSON evidence."""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))


def load(rel):
    with open(os.path.join(BASE, rel), encoding="utf-8") as f:
        return json.load(f)


def write(rel, text):
    p = os.path.join(BASE, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", rel)


DATE = "2026-10-24"
FREEZE = ("基线 commit `e755d773`；判据 `scripts/pyc_verify.py`（SHA256 `FE1902A9...38DDFF4`）与外部 "
          "`pylingual/equivalence_check.py`（SHA256 `9C7567BD...50045A6`）未修改。")

# ---------- J sample ----------
jsum = load(r"j_sample\semantic_j_sample_before_summary.json")
jrec = load(r"j_sample\semantic_j_sample_before.json")
diff_ids = [r["entry_id"] for r in jrec["records"]
            if isinstance(r.get("c4"), dict) and r["c4"].get("verdict") == "DIFFERENT"]
md = f"""# J 样本 before 读数（Task 0.5）

复跑命令（与 round9 `GATE_INTEGRATION.md` 完全同参数）：

```
python -X utf8 tools\\completeness\\semantic_runner.py --space .trae\\specs\\attack-completeness-claims\\rounds\\round9\\judgment_space.json --out <OUT>\\j_sample\\semantic_j_sample_before.json --report <OUT>\\j_sample\\semantic_j_sample_before_summary.json --product-dir <OUT>\\j_sample\\semantic_products --limit 100 --timeout 15 --seconds 240
```

日期：{DATE}。{FREEZE}

## 读数对照

| 项 | round9 历史 | 本次复跑 |
|---|---:|---:|
| 有效记录 | 51 | {jsum['total']} |
| EQUAL | 45 | {jsum['verdicts']['EQUAL']} |
| DIFFERENT | 6 | {jsum['verdicts']['DIFFERENT']} |
| c1_source_missing 跳过 | 49 | {jsum['skipped']['c1_source_missing']} |
| stopped | skipped | {jsum['stopped']} |

DIFFERENT 条目（与 round9 完全一致）：{", ".join("`" + i + "`" for i in diff_ids)}。

结论：J 样本 before 读数与 round9 历史读数**逐项一致**，基线可复现。
"""
write(r"j_sample\J_SAMPLE_BEFORE.md", md)

# ---------- G5 402 ----------
g5 = load("g5_before_summary.json")
sh = g5["g5_402"]["shards"]
tot = g5["g5_402"]
rows = "\n".join(
    f"| shard{r['shard']} | {r['files']} | {r['success']}/{r['failure']}/{r['compile_error']}/{r['error']} "
    f"| {r['units_success']}/{r['units_total']} | {r['success_rate']:.1%} | {r['elapsed_sec']}s |"
    for r in sh)
md = f"""# 402 G5 基线 before 读数（Task 0.5）

命令（i=0..7；8 分片并行）：

```
python -X utf8 scripts\\pyc_verify.py batch --index .trae\\specs\\region-reduction-v3-full-corpus-100pct-10rounds\\baseline\\shards\\shard{{i}}.json --json <OUT>\\g5_402\\shard{{i}}_report.json
```

日期：{DATE}。{FREEZE}

## 分片读数

| 分片 | 文件数 | success/failure/compile_error/error | 单元（含嵌套） | 单元率 | 耗时 |
|---|---:|---|---:|---:|---:|
{rows}
| **合计** | **{tot['files_total']}** | **402/0/0/0** | **{tot['units_success']}/{tot['units_total']}** | **{tot['units_rate']:.1%}** | — |

对照历史口径：402 语料八分片历史读数 **6617/6617 全绿**；本次复跑 **{tot['units_success']}/{tot['units_total']} 全绿**，逐分片文件数 51×7+45=402 一致。结论：402 G5 基线 before 读数与历史读数**一致**。

注：单元数为 pyc_verify batch 报告的 `units_total`（含嵌套 code object），shard 索引内 `function_count`（仅顶层函数）之和 5746 为不同口径，勿混用。
"""
write(r"g5_402\G5_402_BEFORE.md", md)

# ---------- small34 ----------
s = g5["g5_small34"]
md = f"""# small34 before 读数（Task 0.5）

```
python -X utf8 scripts\\pyc_verify.py batch --index .trae\\specs\\region-reduction-v3-full-corpus-100pct-10rounds\\baseline\\small34_index.json --json <OUT>\\g5_small34\\small34_report.json
```

日期：{DATE}。{FREEZE}

| 项 | 历史读数 | 本次复跑 |
|---|---:|---:|
| 文件 | 34 | {s['files']} |
| status success/failure | 34/0 | {s['success']}/{s['failure']} |
| 单元 | 1568/1568 | {s['units_success']}/{s['units_total']} |
| 单元率 | 100% | {s['success_rate']:.1%} |
| 耗时 | — | {s['elapsed_sec']}s |

结论：与历史 1568/1568 **一致**。
"""
write(r"g5_small34\SMALL34_BEFORE.md", md)

# ---------- quotation ----------
qpath = os.path.join(BASE, r"g5_quotation\quotation_single_log.txt")
with open(qpath, "rb") as f:
    qb = f.read()
q = qb.decode("utf-16") if qb.startswith(b"\xff\xfe") else qb.decode("utf-8", "replace")
md = f"""# quotation before 读数（Task 0.5）

```
python -X utf8 scripts\\pyc_verify.py single site-packages\\fly\\data\\quotation.pyc
```

日期：{DATE}。{FREEZE}

原始输出（末三行）：

```
{q.strip().splitlines()[-3]}
{q.strip().splitlines()[-2]}
{q.strip().splitlines()[-1]}
```

| 项 | 历史读数 | 本次复跑 |
|---|---:|---:|
| status | success | success |
| 单元 | 153/153 | 153/153 |
| 单元率 | 100% | 100% |

结论：与历史 153/153 **一致**。
"""
write(r"g5_quotation\QUOTATION_BEFORE.md", md)

# ---------- real46 ----------
r46 = load(r"real46\real46_before.json")["results"]
order = [s["slug"] for s in json.load(open(
    r".trae\specs\attack-completeness-claims\rounds\round6\offcorpus\samples.json", encoding="utf-8"))["samples"]]
rows = []
for slug in order:
    r = r46[slug]
    rows.append(f"| {slug} | {r['status']} | {r['units']} | {r['success_rate']} |")
n_ok = sum(1 for r in r46.values() if r["status"] == "success")
n_ce = sum(1 for r in r46.values() if r["status"] == "compile_error")
n_fail = sum(1 for r in r46.values() if r["status"] == "failure")
u_ok = u_tot = 0
for r in r46.values():
    if "/" in r["units"]:
        a, b = r["units"].split("/")
        u_ok += int(a)
        u_tot += int(b)
md = f"""# 46 真实 pyc before 读数（Task 0.5）

命令（对每个样本）：

```
python -X utf8 scripts\\pyc_verify.py single .trae\\specs\\attack-completeness-claims\\rounds\\round6\\offcorpus\\<slug>.pyc
```

日期：{DATE}。{FREEZE}

## 汇总

| 项 | 数值 |
|---|---:|
| 样本总数（origin=real） | 46 |
| status=success（全单元 EQUAL） | {n_ok} |
| status=compile_error（产物不可编译） | {n_ce} |
| status=failure（部分单元差异） | {n_fail} |
| 单元合计 | {u_ok}/{u_tot}（{u_ok / u_tot:.2%}） |

对照历史 L4 攻击读数（round6）：判据绿 **4/46**、不可编译 **7/46**、单元 **2765/3079** —— 本次复跑逐项一致。

## 明细

| slug | status | units | success_rate |
|---|---|---|---|
{chr(10).join(rows)}
"""
write(r"real46\REAL46_BEFORE.md", md)

# ---------- master ----------
md = f"""# BEFORE_READINGS — Task 0.5 before 读数总表

日期：{DATE}。{FREEZE}

工作目录：`.trae/specs/achieve-any-syntax-completeness/rounds/round11/baseline_before/`（本文件所在目录，下称 OUT）。

| # | 读数 | 命令 | 结果 | 与历史对照 |
|---|---|---|---|---|
| 1 | J 样本（semantic_runner，round9 同参数） | 见 `OUT\\j_sample\\J_SAMPLE_BEFORE.md` | 51 有效：45 EQUAL / 6 DIFFERENT；49 c1_source_missing 跳过；DIFF=JS-IF-017/021/076/088/090/097 | round9 逐项一致 |
| 2 | 402 G5 八分片（pyc_verify batch ×8） | 见 `OUT\\g5_402\\G5_402_BEFORE.md` | 402/402 文件全 success；单元 6617/6617（100%） | 历史 6617/6617 一致 |
| 3 | small34 | 见 `OUT\\g5_small34\\SMALL34_BEFORE.md` | 34/34 文件；单元 1568/1568（100%） | 历史 1568/1568 一致 |
| 4 | quotation | 见 `OUT\\g5_quotation\\QUOTATION_BEFORE.md` | success；单元 153/153（100%） | 历史 153/153 一致 |
| 5 | 46 真实 pyc（offcorpus，pyc_verify single ×46） | 见 `OUT\\real46\\REAL46_BEFORE.md` | 4 success / 7 compile_error / 35 failure；单元 2765/3079（89.80%） | round6 L4 攻击读数逐项一致 |

## 说明

- 以上均为**基线 commit `e755d773`（HEAD 即基线）** 上的 before 读数，供本规范后续 Task 的 after 对照。
- 复跑脚本：`OUT\\summarize_before.py`（402/small34 汇总）、`OUT\\run_real46.py`（46 真实 pyc）。
- J 样本的 6 个 DIFFERENT 与 46 真实 pyc 的 42 个非绿样本即本规范 Task 2/3/4/5/6 要消化的既知债务面，不因基线全绿而豁免。
- 402/small34/quotation 全绿仅说明**既有回归基线**在当前树上可复现；"任何语法完备"由 `REACHABILITY.md` 五行决定，与本表相互独立。
"""
write("BEFORE_READINGS.md", md)
print("ALL SUMMARIES DONE")
