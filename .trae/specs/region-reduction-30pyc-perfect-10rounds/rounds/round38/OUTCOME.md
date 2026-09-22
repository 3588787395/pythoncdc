# Round 38 OUTCOME —— 两条诊断线加一条独立线全部不达发货条件：本轮 `core/` 零改动

靶轮字节：commit `7b8af974`（Round 37 R37-A），核 sha256[:20] `6b0759b1a0a566a4eb8f`。
逐条测量与证据指针见 `arm-design.md`；本文件只记结论。

## 一、结论

1. **未发货**：本轮没有一条同层判据通过前置条件检查，`core/` 一个字节都没写，
   受跟踪产物一份都没变，`pyc_index.json` 未被改写（仍是 Round 37 G6 的实测回写）。
   因此 G1–G7 无对象可跑；轮次花在**选靶与排除**上，产出是 Round 39 的开工前置。
2. **索引未被破坏（实测，非自报）**：全 402 文件在 `head` 臂（与工作区核逐字节全等的私有镜像）
   上整批复测，`logs/g4_head.all.jsonl` 402 行、0 harness error；与 `pyc_index.json`
   逐文件逐字段比对 **冲突 0**（`logs/index_vs_head38.py`），两侧同为
   `Σtotal 5746 / Σmatched 5650 / 整文件全匹配 375`。
3. **语料内已无机械故障**：全 402 崩溃探针 3 片（134 文件/片，0 error）崩溃列全空；
   探针先经反向 R36-A 镜像阳性对照（`fly_api/base.pyc` 复现
   `2x TypeError @ :4824 in _fold_break_to_return`）。⇒ 96 个 deficit 函数全为判据级形状。

## 二、本轮真正的发现：靶簇被拆成两种形状，且产物语义错

最大的一簇是 8 个函数各差**一条** `JUMP_BACKWARD`（81 签名组 / 94 不匹配函数）。窗口探针
`logs/dupjump38.txt` 否证了「一簇一形状」：

| 子形状 | 行数 | 判别事实 | 产物后果 |
|---|---|---|---|
| A | 2（`wizard_quant_check_limit 91/90`、`get_all_real_daily_kline 188/187`） | 前一条指令同 token、两条回边同落点 | 重复回边并成一条；`continue` 被挪到 if/elif 链**之外** |
| B | 6（`fill_kline_data`、`fill_kline_data_by_pre`×2、`one_prod_to_dataframe`×2、`is_delisting_stock_real`） | 前一条指令不同 token、落点不同 | 臂尾回边被并掉 ⇒ **else 臂摊平成顺序语句**，`nan_data[…]=0` 随即被下一行覆盖（语义错，不只是指令数错） |

⇒ 这一簇必须按两条不同判据分别处理，任何「8 行一把梭」的候选都应被拒。

## 三、三条线的否证理由（逐条可复核）

* **线 A（子形状 B）**：交付自证其判据「把臂尾跳转从块名袋里剥出来」在区域构造期**够不到**
  （那层没有「臂尾 vs 其他出口」的概念），且其点名的检查站点实测未到达；它建议的下一步实验
  （打印该 `if` 区域的 `then_blocks/else_blocks/merge`）未做。⇒ 无候选。
* **线 B（子形状 A）**：报告归因于 `ast_from_stmt` 的 elif 脱糖，并给出「`orelse_if` 非空 ⇒
  忠实体」开关，点名 5 个构造站点。编排方复核：该函数名与该形参名在核内 **grep 0 命中**，
  行号体系与核内 `_is_elif` 拼装点（`:12427 / :15901 / :16012 / :32627`）不对应。
  ⇒ 判据不可按报告实施；**代理报告里点名的符号必须在采纳前 grep 验证**（本轮据此否决）。
* **第三条线（编排方独立，`logs/fallback38.txt`）**：把 96 缺口里 8 行分成
  extra-jump(3)／klinedata-return(2)／等长 `finally` 换位(5) 三组。
  这 8 行在官方尺上确为不匹配（`seq_len`/`seq_diff`），不是尺子噪声；但修它们的判据会
  直接压到 Round 33／Round 35 刚落地的两条规则，需要独立见证 ⇒ 不作本轮靶。

## 四、留给 Round 39 的可用资产

* 合成控制 `logs/r38_elif_continue_controls.py`：其中 **`ctl_two_cont` 在落地字节上确证 FAIL**
  （编排方以 `logs/g0_38.py` 在 `mirr_head` 实跑：`DEFECT 1 1 ctl_two_cont:seq_-1`，
  其余三支 CLEAN）⇒ 子形状 A 一族的 G0 见证已就绪，且 G0 驱动器本身已冒烟校验
  （镜像解析断言、显式 `cfile`、异常钩子三条均工作）。
* 门禁基线全部在镜像上重测完毕，下一轮只需跑「改后」侧：
  `logs/reprobat59.txt` ＋ `logs/g2p_head59.jsonl`（59 / 48 全匹配 / Σ|Δ| 176）、
  `logs/anchors107.txt` ＋ `logs/g3_head107.jsonl`（107 / 77 / Σ|Δ| 446）、
  G1 池 `logs/g1_d1_5.txt`、`logs/g1_d2_11.txt`，G4 的改前侧＝`logs/g4_head.all.jsonl`。
* 靶清单见 `arm-design.md` §八（含未动的同簇兄弟 `matcher :: match 713/689` 与在册残余）。

## 五、卫生

`git status --porcelain` 本轮新增项只有 `rounds/round38/**` 记录文件；`core/`、`site-packages/**`、
`pyc_index.json` 无改动；未跟踪项仍只有开工前既存的 `_r10_difflen.py`、`_r13_gate.py`、
`scripts/core_bisect.py`（非本轮产物，未触碰）。
