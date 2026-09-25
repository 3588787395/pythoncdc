# round69_diag5

来源 `D:/Temp/opencode/r69gate/diag5`（Round 69 批次 B5：`trade_info_utils` 39/40、`risk_calculation/__init__` 33/35）；采纳 spec：`cand_r69_loop_hdr_import.json`（region_ast_generator 1 edit / +33 行，[R69-loop-hdr-import]：`_loop_process_header_instructions` 补 IMPORT 分支 —— 本 header 块自身指令流中 `IMPORT_NAME`（前两条为 level/fromlist 实参、其后 `IMPORT_FROM`/`IMPORT_STAR`、再由 `STORE_*`+`POP_TOP` 收尾）产 `ImportFrom` 推入 `_hdr_stmts` 并清缓冲，`STORE_*` 因 `value_instrs` 空而不再物化）。

消费者：`_save_testds_to_csv` 官方 **71/68 → 71/70**（`|Δ|` 3→1），严格 **75/68 → 75/72**（`|Δ|` 7→3），嵌套 hunk **7 → 4**；文件官方 33/35 维持（未关缺口，如实记录），严格 ok 计数 34/37 维持。判定臂：`landed` → `m69`。

| 见证 | landed → m69 |
|---|---|
| `t_n2.pyc` | 1/2 bad=1 → **2/2 bad=0** |
| `t_n3.pyc` | 1/2 bad=1 → **2/2 bad=0** |
| `try_A.pyc` | 1/2 bad=1 → 1/2 bad=1（形状陷阱对照：`while True:`+import+`if x: break` 不走本缺陷路径，故不咬合，留档） |

被否决候选：LoopRegion/IfRegion `_type_priority` 调序（monkeypatch 实测 `_on_publish_after_trading_end` 486/481→486/486，但官方仍 33/35，且三副作用 + 跨区域包含违 §2）；签名 (a) 撞 R47 禁令。详见 `rounds/round69/batches/b5_diag5`。

`.pyc` 本机编译生成，仓库只入库 `.py`（`.gitignore` 忽略 `*.pyc`）。
