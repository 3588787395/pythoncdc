# R72 · fix1（修复工程师）BRIEF —— genexpr/listcomp Different bytecode 族

## 0. 使命

mandated ruler 在 402 支产物上有 12 个 **Different bytecode** 失败单元，其中 **11 个集中在
`comprehension_generator.py`（至今 0 编辑）相关的推导式族**：

| pyc | units_failed | 类别 | 失败单元 |
|---|---|---|---|
| `position_model/future_position.pyc` | 4 | Different bytecode 4 | `buy_open_order_amount.<genexpr>`(L215 off20)、`sell_open_order_amount.<genexpr>`(L221)、`_buy_close_today_order_amount.<genexpr>`(L236)、`_sell_close_today_order_amount.<genexpr>`(L239) |
| `position_model/live_future_position.pyc` | 4 | 同上 | `buy_open_order_amount.<genexpr>`(L228)、`sell_open_order_amount.<genexpr>`(L234)、`_buy_close_today_order_amount.<genexpr>`(L249)、`_sell_close_today_order_amount.<genexpr>`(L252) |
| `position_model/option_position.pyc` | 2 | 同上 | `buy_open_order_amount.<genexpr>`(L203)、`sell_open_order_amount.<genexpr>`(L209) |
| `data/asset_mixin.pyc` | 1 | Different bytecode 1 | `get_assets.<listcomp>`(L91 off10) |

三支 position_model 同目录同构、单元名与行号模式一致，**一条判据清三支（10 单元）+ 一支
listcomp = 11 单元**；这也是本轮「至少一支 pyc 修到完全 OK」的最短路径
（`future_position` 4 单元全清即 79/83 → 83/83 success）。

你的使命：端到端产出候选 patch spec 并在镜像上验证。**不碰 repo、不落地。**

工作区：`D:/Temp/opencode/r72gate/fix1`；基线 HEAD = **R71 提交 `6c0a8f8c`**，
h62 `--arm=landed` = repo（R71 字节）。

## 1. 输入数据

- `filecat.json`（47 支 failure 明细）、`targets.md`、`G3v_pycverify_r71.json`。
- 靶产物：`site-packages/IQEngine/plugins/plugin_system_accounts/position_model/*OK.py`、
  `site-packages/IQEngine/data/asset_mixinOK.py`。

## 2. 建议步骤

1. 复现：对四支跑 `python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single
   <pyc> --source <OK.py>`，拿到单元 verdict；`dis` 对比原 pyc 与重编译产物的该 genexpr/
   listcomp code object，找第一条分歧指令（常见：推导式内部跳转/分支结构、
   `FOR_ITER`/`JUMP_BACKWARD` 与内层条件的块划分、listcomp 返回路径）。
2. 根因到行：先查 `core/cfg/comprehension_generator.py`（0 编辑，第一嫌疑），再查
   region_analyzer 对推导式内部块的归约、region_ast_generator 的推导式发射
   （monkeypatch 探针逐块打印）。
3. 写 spec：`{"file": "core/cfg/<x>.py", "edits": [{"anchor": LF 文本恰出现 1 次, "repl": ...}]}`
   —— **repl 内嵌三要素注释（识别条件/归约方式/AST 映射）**；同层次结构身份判据：
   无函数名/文件名/偏移/阈值启发、无名字白名单、无新增 self 状态、无跨层
   `region.entry in r.blocks` 型模式。
4. 验证闭环（每条候选）：
   a. `python -X utf8 mbuild72.py <臂名> specs/<候选>.json`（锚点断言必须全过）；
   b. 四支靶：h62 `run --arm=<臂名>` 官方读数**逐项不变或改善**（不得回退）+ mandated
      `pyc_verify.py single <pyc> --source <build_<臂名>产物>` 失败单元**清零或减少且零新增**；
   c. 金丝雀：market_time `af77224b34b203c4`、datetime_func `e711b8ea86d49a15` /
      `9d09af09249da177`、quotation `3eb76e512df9ab1e` 四支产物 sha 与 R71 逐字节相同，
      quotation 官方 143/143、mandated 152/153 不倒退；
   d. 电池：`python -X utf8 closeout69.py battery landed <臂名>` worse-than-landed=0；
   e. 严格尺：`python -X utf8 sstrict67.py build_<臂名> <名单> <out>` 无新增缺陷函数。
   （b–e 原始输出存 `dump/`，供中心复核。）

## 3. 硬约束

- **不修改 repo 任何文件**（`land72` 只可 dry-run 断言，禁止 `--apply`）；402 全量扫描禁止。
- 每条命令 <300s；region_analyzer/comprehension_generator 里用 dis 必须局部导入。
- h62 list 文件 LF 无 BOM、跑前删旧 jsonl；sstrict67 第一参数是本工作区 `build_<arm>`。
- ADR-1：缺失/过冲族（seq_len 类）要求 Σ|Δ| 净减且不得以少发射换；位移族（counts 相等）要求
  hunk 严格降 + first_diff 回移 + Σ|Δ| 不升；**任何他支回归即整件拒收**。

## 4. 交付

- `FACTS.md`（族聚类、根因表、每候选 a–e 验证读数）；
- `specs/*.json`（每候选一份，anchor 断言自检打印）；
- `synth/*.py` 最小复现（若有）。
