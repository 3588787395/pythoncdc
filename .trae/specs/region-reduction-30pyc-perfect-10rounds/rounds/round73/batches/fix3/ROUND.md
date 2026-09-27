# R73 · fix3（修复工程师）BRIEF —— 手术族（F-TERNARY / F-EXCTABLE / F-POLARITY / F-OTHER quote）

## 0. 使命

mandated ruler 剩余 88 个失败单元里有四个**小而判据行明确**的手术族（合计 ~8 单元，
R72 diag1 已给出到行根因）：F-TERNARY 2、F-EXCTABLE 1、F-POLARITY 2–3、F-OTHER quote 2。
你的使命：**逐族端到端钉死，产出候选 patch spec 并在镜像上验证**（不碰 repo、不落地），
**每个族单独成臂**，目标之一是让某支 pyc 从 failure 变 **success（完全 OK）**
（`commission`（1 单元）、`api_base`（1–2 单元）、`bar`（3 单元）是 mandate 最短路径）。

工作区：`D:/Temp/opencode/r73gate/fix3`；基线 HEAD = **R72 提交 `8d136040`**，
h62 `--arm=landed` = repo（R72 字节）。**镜像臂名一律 `surg*`**（`mbuild73.py surg1 …`）。

## 1. 输入数据

- `filecat.json`（41 支 failure 明细）、`targets.md`、`G3v_pycverify_r72.json`。
- R72 diag1 交接 FACTS（四族判据行 + synth 读数；R72 synth `a01` = F-TERNARY 复现）。

## 2. 四族根因与判据行（R72 实测，R73 HEAD 行号需重核）

| 族 | 单元 | 判据行 | 机制（首分歧实测） |
|---|---|---|---|
| **F-TERNARY** | `bar.BarData.limit_up` / `limit_down`（2） | `region_analyzer.py:20432 _identify_ternary_regions`；`region_ast_generator.py:3199-3223`（IF_ELIF_CHAIN 对嵌套三元的让位判据，不让位 ⇒ `ast.Return(ast.IfExp)`）、`:11711 _generate_if`、`:17753 _if_generate_normal` | try 内 `return v if c else n` 未归约成 `Return(IfExp)`，降级为 if+两个内联 return：`20 JUMP_FORWARD→RETURN_VALUE`；synth a01 可复现 |
| **F-EXCTABLE** | `commission.CommissionHelp.set_commission`（1，Different bytecode） | `region_ast_generator.py:24342`（注释：compiles try-else as two adjacent exception table entries）及 `:26152/:26587/:26615/:27010`（R71 F-EXCTABLE 落点，行号需重定位） | 指令流全同，异常表 18/18 字节但范围不同 |
| **F-POLARITY** | `trade_live_broker._sync_worker`（1，极性+落点同时动）、`api_base.get_history`（1，`60 IF_FALSE→IF_TRUE to 66` 同落点纯极性翻转） | `region_ast_generator.py:46 _negate_expr`、`:57-59`、`:12032`、`:12108`（`UnaryOp('not')` 折叠）；`region_analyzer.py:15929 _identify_conditional_regions`（then/else 臂归属） | 跳转极性被取反（`94 POP_JUMP_FORWARD_IF_TRUE→IF_FALSE`、`60 IF_FALSE→IF_TRUE`） |
| **F-OTHER quote** | `quote.check_industry_code`（`in→not in`，`idx158 CONTAINS_OP`）、`quote.load_get_price`（外层 if 被掏空，`idx52 POP_JUMP_FORWARD_IF_FALSE→POP_TOP`） | `region_ast_generator.py:88-100 _flip_contains_compare`（`{'In':'NotIn',…}`）+ 调用点 `:12743/:16032/:16386/:16823`；`:21530 _process_if_blocks`、`:17753 _if_generate_normal` | ① 会员判据被翻转；② 外层条件降级为裸表达式语句、内层 if/elif 链上提到同级。**R72 synth b07/b08 均未触发，必须先找到真实触发条件** |

注：R72 清掉的 `asset_mixin.get_assets.<listcomp>` 极性单元已不存在；
`quote` 与 `quotation`（金丝雀 `change_his_to_forward`）是**不同文件**，quotation 只作对照。

## 3. 步骤

1. 逐族在 `filecat.json` 里核实单元清单与首分歧（4 个 Different bytecode 单元中
   commission=1、quote=2、trade_live_broker=1）。
2. 复现：`python -X utf8 F:/Downloads/pythoncdc-main/scripts/pyc_verify.py single <pyc>
   --source <OK.py>`；`dis` 对比找第一条分歧（跳转方向/异常表/CONTAINS_OP/块结构）。
3. 根因到行：monkeypatch 探针打对应判据行（三元让位判据、异常表拼接、`_negate_expr`、
   `_flip_contains_compare`、`_process_if_blocks`）。
4. 写 spec：`{"file": "core/cfg/<x>.py", "edits": [{"anchor": LF 文本恰出现 1 次, "repl": ...}]}`
   —— **repl 内嵌三要素注释（识别条件/归约方式/AST 映射）**；同层次结构身份判据：
   无函数名/文件名/偏移/阈值启发、无名字白名单、无新增 self 状态、无跨层
   `region.entry in r.blocks` 型模式。
5. **逐族成臂**（surg1=F-TERNARY、surg2=F-EXCTABLE、surg3=F-POLARITY、surg4=F-OTHER quote，
   名字可调但一族一臂），各臂独立跑验证闭环；合并臂（surgm）最后单独跑。
6. 验证闭环（每件候选）：
   a. `python -X utf8 mbuild73.py surg1 specs/<候选>.json`（锚点断言必须全过）；
   b. 靶支：h62 `run --arm=surg1` 官方读数**逐项不变或改善** + mandated
      `pyc_verify.py single <pyc> --source build_surg1产物` 失败单元**清零或减少且零新增**；
      **优先挑「修完全清」的单单元文件**（commission / api_base 是 mandate 最短路径）；
   c. 金丝雀：market_time `af77224b34b203c4`、datetime_func `e711b8ea86d49a15` /
      `9d09af09249da177`、quotation `3eb76e512df9ab1e` 四支 sha 与 R72 逐字节相同；
   d. 电池：`python -X utf8 closeout69.py battery landed surg1` worse-than-landed=0；
   e. 严格尺：`python -X utf8 sstrict67.py build_surg1 <名单> <out>` 无新增缺陷函数。
   （b–e 原始输出存 `dump/`，供中心复核。）

## 4. 硬约束

- **不修改 repo 任何文件**（`land73` 只可 dry-run 断言，禁止 `--apply`）；402 全量扫描禁止。
- 每条命令 <300s；region_analyzer 里用 dis 必须局部导入（宽 except 吞 NameError 陷阱）。
- h62 list 文件 LF 无 BOM、跑前删旧 jsonl；sstrict67 第一参数是本工作区 `build_surg1`。
- ADR-1：**任何他支回归即整件拒收**；不得以少发射换；位移族要求 hunk 严格降。
- 与 diag1/fix1/fix2 并行：四族边界由你守住——若发现某单元实属 F-ABSORB/F-PAD
  （fix1/fix2 领地），FACTS 里标注并移交，不硬打。

## 5. 交付

- `FACTS.md`（四族根因表 + 每臂 a–e 验证读数 + 合并臂读数 + 移交项）；
- `specs/*.json`（每族一份，anchor 断言自检打印）；
- `synth/*.py` 最小复现（F-OTHER quote 缺口若在你这族内触发，必须附复现）。
