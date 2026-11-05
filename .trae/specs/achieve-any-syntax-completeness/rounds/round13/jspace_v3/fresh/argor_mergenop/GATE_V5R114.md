# GATE_V5R114 — rr-v5r114 验收读数（小测试收口口径）

## 0. 元信息

- 修复前 HEAD：`65606ef3`（rr-v5r113）。待验证改动：`core/cfg/region_ast_generator.py`
  `+190/−13`，标记 `[v114-ARGOR]` + `[v114-MERGENOP]`（详见 fix_patch_v5r114.diff 与
  FINDING.md）。
- 判官：`tools/completeness/semantic_diff.py` SHA256 `DBCB1E24…` 与 v5r113 基线
  judge_sha256 一致；`scripts/pyc_verify.py` SHA256
  `FE1902A90CEBD4A15925F7C34924269FD324418B9FB50B43A21BD4DBF38DDFF4` 冻结一致；
  `git diff -- tests/ scripts/pyc_verify.py tools/completeness/semantic_diff.py
  core/cfg/region_analyzer.py` 为空；唯一已跟踪改动
  `M core/cfg/region_ast_generator.py`。

## 1. 本轮验收（用户裁定口径：小测试即验收）

| 验收项 | 读数 | 结论 |
|---|---|---|
| 变体矩阵（12 案 A/B） | 4 功效案 HEAD TEXT-DIFF → v114 重编译 BYTE-EQUAL；7 控制案逐字节同且 BYTE-EQUAL；1 未领边界（E6）v114==HEAD 零漂移 | PASS |
| A/B 回归电池（226 案） | TEXT-DIFF 仅 4 = 恰为本轮 4 功效案（全 BYTE-EQUAL）；222 TEXT-SAME；既有登记差 10 案 ALL SAME-SIGNATURE；R110 案 168/169 一致（唯一差 mc1 = r110 功效案两侧同持修复正常归一） | PASS |
| pytest 7 套件 | 3 failed / 277 passed / 2 xpassed——与 v113 基线逐项一致（2 冻结对 + product_freshness 预存在陈旧：3 个 stale 条目行数/字节比 283 行 26229/26134、71 行 13299/13537、1016 行 61506/61895 与 v113 日志逐字相同） | PASS（零新增失败） |
| REAL46-031 单案权威判官 | DIFFERENT（2 R7）→ **EQUAL（diffs=[]）**（semantic_REAL46-031_v114.json） | PASS |
| 判官盲区核查（68 code objects 递归字段比对） | v113 产品 3 差异 → v114 仅剩 `/Version/__setstate__` co_code 818 vs 816（预存在，本轮零漂移，已登记下轮） | PASS（诚实台账） |
| REAL46-004 / REAL46-019 等近轮闭合案 | 回归电池内对应案（er1/pb1/mc1/r1 系等 222 案 TEXT-SAME）零漂移 | PASS |

## 2. 缺省项（如实登记）

- **1556 三分片全量语义闸门 + REAL46 全量 sweep：本轮豁免（用户裁定口径）。**
  用户明确政策：**只有大改动才由主代理跑全量闸门；小修复以小测试收口**（§1：
  变体矩阵 + A/B 回归电池 + pytest 冻结对 + 单案权威判官 + 盲区核查全绿）。
  rr-v5r114 属小改动（+190/−13 单文件两族），全量闸门按政策豁免，
  `compare_v5r114.py` 已就绪、留作未来大改动轮次一并对比使用。
- 历轮 1556 读数基线：v5r113 EQUAL 1180 / ERROR 376（见 GATE_V5R113.md）。

## 3. 不宣称事项

- 不宣称 G1/G2b/G2c/G3/G4/G6 通过；`product_complete` 仍 NOT PASS。
- REAL46-031 剩余判官盲区差异（`__setstate__`）与 E6 相邻 NOP 对已登记未修。
