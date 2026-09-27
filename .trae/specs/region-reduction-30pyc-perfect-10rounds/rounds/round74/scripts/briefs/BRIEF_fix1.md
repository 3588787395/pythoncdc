# R74 · fix1（修复工程师）BRIEF — F-ABSORB 主体：**abs2 orphan-child 发射 + abs1 合臂**

## 0. 使命

R73 的 ADR-1 **拒收了 absm**（收益 +4 单元，但 klinedata 丢 1 条尾语句＝以少发射换）。
本轮按中心方向在 **`core/cfg/region_ast_generator.py` 侧补 orphan child region 发射（abs2）**，
再与 R73 的 abs1（`region_analyzer._is_nested_if_else_pattern` same-target 豁免）合成**合臂 absj**，
目标：**保留 abs1 的全部收益 + 尾语句恢复 + 任何他支零回归**，拿到 mandate
（`IQCommon/data/local_finance.pyc` 20/21 → 21/21）。

工作区：`D:/Temp/opencode/r74gate/fix1`；基线 HEAD = **`6bb9716a`**（R73 落地，
generator `33e22ee451148af8` / analyzer `b9dcc727ea5918ea`）。

## 1. 输入与既有弹药

- `filecat.json`（35/77 明细）、`fam74_r74.json`（F-ABSORB 67）、`dump/crosstab74.txt`、
  `G3v_pycverify_r73.json`、`fail74.txt`。
- **R73 可复用 spec**：`D:/Temp/opencode/r73gate/fix2/specs/abs1_nested_same_exit.json`
  （analyzer 单 edit，已自证 +4 单元、battery worse=0、strict NEW=0）。复制到本区 `specs/abs1.json`
  （内容勿改，锚点须在**当前 HEAD** 上仍恰 1 次 —— 跑前断言，见 §3a）。
- **根因与成因实证**：`r73gate/fix2/FACTS.md §2/§5` —— 共享尾 region 合并后，
  `Region@2710` 成为 child 但**不在 `blocks/then_blocks`** → 生成器跳过 → 语句丢失；
  证据 dump `rd2_base.txt` / `rd2_ns.txt`、`diff_klinedata_landed_vs_absm.txt`。

## 2. 两臂定义（单臂单 edit，各自闭环）

- **arm `abs2`**：**仅** `core/cfg/region_ast_generator.py` 新增/改动一处 —— 「child region 未被
  blocks/then_blocks 覆盖时按序补发射」。判据必须**同层结构身份**：不许函数名/文件名/偏移阈值/
  名字白名单/新 self 状态/跨层 `region.entry in r.blocks`。repl 内嵌三要素注释
  （识别条件 / 归约方式 / AST 映射）。
- **arm `absj`**：`abs1`（analyzer 1 edit）+ `abs2`（generator 1 edit）**合并**，作为最终候选。

## 3. 步骤（闭环顺序）

a. **基线复现**：`mbuild74.py abs1 specs/abs1.json`（锚点断言：LF 归一后恰 1 次、BOM/行尾断言过）
   → `h62.py run --arm=abs1 --list=…`（41 靶或本区 35 靶清单）+ mandated 逐支
   `python -X utf8 …/scripts/pyc_verify.py single <pyc> --source build_abs1/<产物>`，
   确认 R73 读数可复现（local_finance 21/21、finance +2、trade_live_broker +1）；
b. **抓丢失现场**：对 `IQCommon/api/klinedata.pyc`，比较 abs1 产物 vs 落地产物的
   `get_multiminute_his_data`（`dis` + strict `seq_len` 482），确认**哪一条 child region 被跳过**；
c. **写 abs2**：锚定生成器的 child 遍历/emit 路径；先在镜像臂上跑 klinedata mandated 单点
   （尾语句恢复 = 481/482 指令回来、strict seq_len 回到 ≥482），再跑合臂；
d. **合臂 absj**：`mbuild74.py absj specs/abs1.json specs/abs2.json`（两 edit 各恰 1 次）。
e. **验证闭环（absj 必跑全项，abs2 单臂跑 a–c）**：
   1. 官方：`h62.py run --arm=absj --list=<35 靶>` → **逐项 ≥ landed 且 ≥ abs1**，
      `Σ|Δ|` ≤ 185、`Σjump_diffs` ≤ 123（对 41 靶口径）、失配函数 ≤ 28；
   2. mandated：35 靶 **≥ 6540+4 单元**（含 local_finance 21/21 转 success、finance ≥31/32、
      trade_live_broker ≥115/128）、**零新失败单元**；
   3. klinedata 靶点：`get_multiminute_his_data` **丢语句必须恢复**（seq_len ≥ 482、
      `get_kline_by_count_new` load 数与落地产物一致）；
   4. 金丝雀 4 支 sha16 == pin（`3eb76e512df9ab1e`/`af77224b34b203c4`/`e711b8ea86d49a15`/
      `9d09af09249da177`），quotation mandated 152/153 维持；
   5. `closeout69.py battery landed absj` → **worse-than-landed = 0**；
   6. `sstrict67.py build_absj <75 缺陷名单> out` → **新增缺陷 0**、缺陷数 ≤ 75；
   7. synth：复用 `r73gate/fix2/synth/abs_a01_shared_and_else.py`（应 failure→success）
      与 `abs_a02_true_nested.py`（负例 sha 必须与落地逐字节相同）；**新增一条
      「合并后 child 含尾语句」的最小复现**，absj 下语句不丢。
   全部原始输出落 `dump/`，汇总进 `FACTS.md`。

## 4. ADR-1 接受判据（不满足即自判拒收、如实写明）

- **WORSE = 0**：任何他支/他单元变差、任何语句/指令变少（含 klinedata −11）＝整件拒收；
- 位移族：hunk 严格子集 + first_diff 回移 + Σ|Δ| 不升；
- abs1 收益不得回吐（local_finance 必须 success，否则 abs2 视为破坏 abs1）。

## 5. 硬规则

不改 repo（`land74` 只 dry-run、禁 `--apply`）；不手改 `*OK.py`；每条命令 <300s；
ALLOWED = `region_ast_generator.py` / `region_analyzer.py`（abs1 只许原样复用）/ `comprehension_generator.py`；
h62 列表 LF 无 BOM、跑前删旧 jsonl；产物名含 `:` 走 `.replace(':','_')`。

## 6. 交付

`FACTS.md`（a–e 逐项读数、abs2 判据与成因、与 fix2/fix3 重叠面）、`specs/abs2*.json`、
`specs/absj.json`（或分文件列两条 edit）、`synth/` 复现、`dump/` 原始 jsonl。
