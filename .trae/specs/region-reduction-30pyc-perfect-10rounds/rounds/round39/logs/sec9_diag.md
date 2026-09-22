
## 九、G4 否证 R39-A（过火 16 处）⇒ 实测分离出「私有 vs 合流」一项 ⇒ R39-B

**R39-A 的 G4（402 文件 A/B，`logs/g4_r39a_perfunc.txt`）**：

```
TALLY SAME=383 IMPROVED=0 REGRESSION=16 MOVED=3 ERR=0   files fully matched: a=375 b=366
```

但它并非无用 —— 靶确实被它修好了：`wizard_quant_api :: wizard_quant_check_limit`
`orig=91 decomp=90` ⇒ **匹配**（该文件计数不变只因同时碰坏了 `add_to_strategy_info 38/39`），
`klinedata :: get_all_real_daily_kline 188/187 → 188/188`（指令数复原，仍差 5 条）。
破的 16 处全是同一方向：**产物比原始多一条指令**（`orig=N decomp=N+1`）＝多补了一条
`continue`，重编译便多出一条 `JUMP_BACKWARD`。⇒ 形状判据只差「私有 vs 合流」这一条区分。

**实测判据（`logs/probe39h.py` → `logs/h_out.txt`：在 `_process_if_blocks` 每个返回点，
把候选臂尾直落后继逐条评估，含前驱集／merge／back_edge／owner，只测不改）**：

| 站点 | 臂尾 L | 候选 T | T 的前驱 | 是本区域 `merge_block` | 是循环 `back_edge_block` | 判别 |
|---|---|---|---|---|---|---|
| `wizard_quant_check_limit` 末臂 | @330 | @340 | **[@330]** | 否 | 否（@342 才是） | 应认 ⇒ 认了就修好 |
| `add_to_strategy_info` | @264 | @394 | [10, @264] | 否 | **是** | 不应认（R39-A 认了 ⇒ +1） |
| `add_to_strategy_info` | @92 | @222 | [84, @92] | **是** | 否 | 不应认（R39-A 认了 ⇒ +1） |
| `get_vip_user_info` | @832 | @854 | [562, @832] | **是** | 否 | 不应认（R39-A 认了 ⇒ +1） |

⇒ 分界不在「是否纯回边块」「是否属于本区域块集」，而在**归属的私有性**：源码里那条显式
`continue` 对应的回边块只有一个前驱、且那个前驱恰是本臂末块；前驱 ≥2 的后继（含本
`IfRegion` 的 `merge_block` 与循环自身的 `back_edge_block`）表示「臂自然落到链外合流点」，
那里源码本没有 `continue`。这正是原则 2（每块唯一归属）读在臂尾上的形态：私有的才归本臂。

**R39-B（同层判据，站点与 R39-A 同为 `_process_if_blocks` 末尾）**＝R39-A 的判据串 ＋
两项 `len(T.predecessors) == 1 and T.predecessors[0] is L`。规格 `logs/spec39b.json`
（由 `logs/mkspec39b.py` 派生，插入 53 行）。门禁结果与落地见 `OUTCOME.md`。

**纠正 §八 的一处记录错误**：§八 写「r39a 镜像 G0 ⇒ `r39w_witness CLEAN 0`」，而归档
`logs/g0_r39a.txt` 实为 `r39w_witness DEFECT 1  ctl_two_cont:seq_-1`，且
`test_repros/out_r39a/r39w_witness.py` 与 head 产物逐字节相同 ⇒ **R39-A 在合成见证上根本没触发**，
它只在语料上触发。（未再追这条差异的成因：加上私有性一项后见证与语料同时触发，见
`logs/g0_r39b.txt` 的 `cases=2 CLEAN=2 DEFECT=0`，说明该项正是见证所缺的一条。）
教训并入采纳前置检查：**G0 电池必须在同一镜像臂上重跑并留档，不能沿用另一次构建的结论**。
