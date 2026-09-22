- [x] Task 39: 落地 R39-B —— 从**块归属层**修子形状 A：if 臂尾的回边块只有在「本臂私有」（唯一前驱
      就是臂末块）时才认给这条臂；靶 `wizard_quant_check_limit` 两把尺同时转为匹配，全 402 A/B
      零回退（记录 `rounds/round39/DIAGNOSIS.md` §八–§九 ＋ `rounds/round39/OUTCOME.md`）
  - [x] SubTask 39.1: 靶轮字节基线确证 commit `5d509aa1`、核 sha256[:20] `6b0759b1a0a566a4eb8f`
          （2 984 567 字节 / CRLF 48 421 / BOM 在位）；全部测量在私有镜像 `mirr_head` 与新臂
          `mirr_build_r39b` 上做，建臂后即断言镜像与工作区字节全等，G4 通过前 `core/` 未写一字节。
  - [x] SubTask 39.2: 根因层级闭合（承 Round 38 线 B／本轮 §六–§七）：缺陷不在发射侧任何
          `continue` 抑制判据，而在臂尾回边块被外层 `LoopRegion` 认领 —— 见证 @58／语料 @340
          `owner=LoopRegion`、`role=PURE_CONTINUE`，链外发射后与循环自身尾回边 @60／@342
          塌缩成同一条 `JUMP_BACKWARD` ⇒ 臂尾终止符少发一条。反向用编译器证明 restoration 目标
          形态（`logs/cand_c1.py` 与见证原始指令流逐偏移相同）。
  - [x] SubTask 39.3: 第一版判据把「直落后继」写成 `len(L.successors)==1` ⇒ G0 完全无效果；
          `logs/probe39g.py` 逐条评估才看清 @330/@48 在 try 保护区里有异常入口后继（`PUSH_EXC_INFO`）。
          改成「排除更靠后与异常入口后继」后 R39-A 过 G0 构建，但在 **G4 被否证**：
          `SAME=383 IMPROVED=0 REGRESSION=16 MOVED=3`、fully matched `375→366`。
  - [x] SubTask 39.4: 逐函数拆 R39-A 的 A/B（`logs/g4_r39a_perfunc.txt`）⇒ 16 处回退全是
          「产物比原始多一条 `continue`」，而靶确实被它修好（`wizard_quant_check_limit 91/90→匹配`、
          `get_all_real_daily_kline 188/187→188/188`）。`logs/probe39h.py` 在每个 `_process_if_blocks`
          返回点打印候选后继的前驱集／`merge_block`／`back_edge_block`／owner ⇒ 分界是**私有性**：
          真 `continue` 的回边块唯一前驱就是臂末块（@340←[@330]），而误认站点前驱 ≥2
          （@394←[10,264] 是循环 `back_edge_block`；@222←[84,92]、@854←[562,832] 是本区域 `merge_block`）。
  - [x] SubTask 39.5: R39-B ＝ R39-A 判据 ＋ `len(T.predecessors)==1 and T.predecessors[0] is L`
          （规格 `logs/spec39b.json`，插入 53 行、无删除）。G0 合成电池
          `test_repros/round39_arm_tail_continue/`（见证 1 ＋对照 5）⇒ head 臂 `DEFECT 1`、
          r39b 臂 `cases=2 CLEAN=2 DEFECT=0` 且无 DEGRADED／无 EXC；G1 四池
          `5/11/2 SAME` ＋ `IMPROVED 1`（`wizard_quant_api 49/53→50/53`）`REGRESSION=0`；
          G2′ `reprobat59` 59 SAME（fully matched 48→48）；G3 `anchors107` 107 SAME（77→77）。
  - [x] SubTask 39.6: **G4（发货权威）** 402 文件三片 A/B ⇒
          `TALLY SAME=401 IMPROVED=1 REGRESSION=0 MOVED=0 ERR=0`、fully matched `a=375 b=375`；
          **G4′** 对唯一变更产物用严格尺逐函数比 `git show HEAD:` 旧产物 ⇒ `50/56 → 51/56`、
          `FIXED=[<module>.wizard_quant_check_limit]`、`BROKEN=[]`（其余 5 支改前改后逐条相同）。
  - [x] SubTask 39.7: 落地＝实测镜像的字节精确重放（`replay == measured mirror bytes: OK`），
          核 2 984 567 → 2 988 464 字节 / CRLF 48 474 / BOM 保留 / sha256[:20] `cc1254fa30410f2b9954`；
          工作区变更集只有核 1 支 ＋ 产物 1 支（`wizard_quant_apiOK.py`）＋ 索引。
          **G5**：`single` 靶官方尺 `50/53`（缺项表已无该函数），金丝雀 `fly/data/quotationOK.py`
          sha256[:20] `3f2242e73d7fd56a0096` 改前＝改后逐字节相同。
  - [x] SubTask 39.8: **G6** `batch --index pyc_index.json --all --round 39` 402/402 复验、
          `failed_pyc 0`、索引差异 404 处＝402 条轮次盖章 ＋ 仅 `wizard_quant_api.pyc` 的
          2 个字段（`matched_functions 49→50`、`bytecode_match_rate 0.9245283→0.9433962`），
          无其他状态翻转（`logs/g6_index_diff.txt`）。**G7** `stats` 见 `OUTCOME.md` §三。
  - [x] SubTask 39.9: 两条方法论收获：① 纠正 §八 误记——归档 `logs/g0_r39a.txt` 实为
          `r39w_witness DEFECT 1`、`out_r39a` 产物与 head 逐字节相同 ⇒ **R39-A 在合成见证上根本没触发**，
          只在语料触发；结论：G0 必须在**同一镜像臂**上重跑并留档，不能沿用另一次构建的结果
          （与 38.8 同源：先证明量具在测的东西上有效）。② 否证轮不是废轮——R39-A 的 16 处过火
          恰好给出唯一区分项，故先按函数拆 A/B 差异集（`NEW`/`GONE`）再谈收紧判据。
          残余：`get_all_real_daily_kline` 是合流型站点（前驱 ≥2），与子形状 B 同族，不得靠放宽
          私有性一项去够；下一轮 G2′ 加入本轮电池（head 侧见证 `DEFECT 1` 即天然阳性对照）。
