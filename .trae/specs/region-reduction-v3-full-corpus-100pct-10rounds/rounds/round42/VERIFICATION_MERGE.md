# Round 42 = 合并门禁（rr-v3r01-f557fd → main）

标签 42 由本次合并消耗：它不是 v3 规范的第 42 轮修复，而是「v2+v3 合并后字节」的全量认证门禁。
`before` = round41（v3 tip 的已认证产物）。合并过程与逐条判据见
`.trae/specs/MERGE_RECORD_rr-v3r01-f557fd_to_main.md`。

## 落地字节

- `core/cfg/region_analyzer.py` sha16 = `3bf5f401614fa8e0`
  （链：`c26ee206af0e2a0d → 129bb0332df3601e → b4fb55ad2b663f96 → 3bf5f401614fa8e0`）
- `core/cfg/region_ast_generator.py` sha16 = `f81a931ffe641ccd`
  （链：`6654f4ca → 8c8edbb9 → dd82f3d3 → 86a1d703 → 84d9c474 → aaec80a2 → 7d7c22d4 → f81a931f`）
- 合并提交 = `3aa79945`，父提交 `91f8d27d`(main/v2 线) + `67c8cfa0`(v3 线)

## 门禁读数（本轮实测，非引用）

| 面 | 读数 |
|---|---|
| regen | `ok=402 bad=0`（全部产物由流水线重生成，未手改任何 OK.py） |
| 单元 | 6617/6617 = 100.0000 %，文件 402/402 |
| 对照 round41 | 单元 6617→6617、文件 402→402，文件级回退=0，UNIT_REGRESSIONS=0，新增失败单元=0 |
| 对照 v2 基线快照 | 6554/6617→6617/6617、369/402→402/402，REGRESSIONS=0，改善文件 33（join 重叠 402/402 先证） |
| quotation | 153/153（v2 基线 152/153） |
| small34 | 1568/1568 单元、34/34 文件（v2 基线 1505/1568） |
| 判据自证 selfcheck | 153/153 Equal；「常量」「极性」变异各抓到 1/153 ⇒ 比较条件未被放宽 |
| pytest 七套件 | 2 failed / 282 passed / 2 xpassed；失败项按名核对 = `test_B01_simple_if_then_else_merge` + `test_BOUNDARY_02_large_function`（基线名单）⇒ 新增失败 0 |
| 残余表 | 残余文件 0、残余单元 0、UNREGISTERED 行数 0 |
| 与 round41 相比变化的产物 | 7 个：local_finance / cgroup_utils / trade_info_utils / user_info_utils / trade_live_broker / flytools / quote_handler —— 单元读数一律不变差 |

## v2 侧靶形复跑（合并后仍生效）

`nested_battery_r140.py`：nb_for 2/2、nb_with 2/2、nb_b99 4/4（v2 的两处分析器改动各自承重，均已保留）。
round8 变体电池复跑：b105/b107×3/bmatch 全系与 v2 记录逐位一致（含产物字节数 266/222）。
唯一开放项 = `b104_chain4_battery` 的 `<module>.v2`、`<module>.v4` 两单元（while 条件位链式比较的
回边重检副本被生成为体内 if/elif）。已证：v3 tip 在同探针为 2/6（合并恢复到 4/6），且本次合并的两条
收窄门对该探针逐位无影响（四臂产物 sha 同为 `fe532cc741fb`）。为开放登记，非本次合并引入的回退。
