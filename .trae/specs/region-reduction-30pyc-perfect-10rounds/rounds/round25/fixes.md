# Round 25 候选与判据（fixes）

## 状态
诊断代理 `r25-diag-d3`（只读，`D:/Temp/r25land/agent_d3/`）与编排方的独立取证并行进行；
本文件先固定**编排方自己从两份读数得到的机制假设**，代理的 Q1-Q6 结论到位后在下方续写并裁决。

## 一、机制假设（由两条独立读数收敛而来）

### 证据 1（官方尺，`dump/pool25_*.jsonl`）
`data_proxy.pyc :: get_bar` → `o=86 d=86 j=3 t=8 first@76 LOAD_FAST self | LOAD_CONST None`。

### 证据 2（严格尺，`logs/strict_pre25.txt`）
同一函数 `[seq_len] orig=86 decomp=90` —— 产物**多 4 条**。
官方尺的 `_trim_spurious_intermediate_returns`（R97）在对齐位置删掉产物里两对
`LOAD_CONST None + RETURN_VALUE` 后才读成 86/86。

### 证据 3（产物源码，`site-packages/IQEngine/data/data_proxyOK.py` L32-45）
```
if bar is not None:
    if frequency == 'tick':
        return self.TickBar(asset, bar, dt)
    elif engine_instance().config.strategy.run_type == const.RunType.TRADING:
        …
        if bar is not None:
            return self.BarData(self, asset, bar, now_dt)
    else:
        return self.BarData(self, asset, bar, dt)   # ← 被当成 elif 链的 else 臂
else:
    return None                                     # ← 被当成外层 if 的 else 臂
```

### 证据 4（原始字节码真实布局，代理与 `D:/Temp/r24diag/jump/out/NORM_get_bar__orig.txt` 一致）
```
ORIG    B478 RETURN_VALUE | B526 return BarData(…, dt) | B574 LOAD_CONST None; RETURN_VALUE
```
即原始里 `return BarData(…, dt)` 是条件链的**直落续块**（不是任何 `else` 臂），
而 `B574` 那对 `LOAD_CONST None/RETURN_VALUE` 是**函数级隐式出口**，外层 `if` 根本没有 `else` 块。

### 假设
分析器把「条件链的唯一直落续块」认领成了 `else` 臂（`_identify_conditional_regions` →
`_build_elif_region` 的 `final_else` 计算），于是
1. 真值臂末尾的 `return BarData(…, dt)` 被移进一个 `else` 臂，落地次序整体后移；
2. 外层 `if` 的 `else` 被物化成显式 `return None` 语句（而不是复用函数级隐式出口），
   每一处物化多产生一对 `LOAD_CONST None; RETURN_VALUE` ⇒ 严格尺看到的 +4。

⇒ **本轮判据要表达的是「一个臂只能是唯一归属」**：某块若同时是（a）条件块跳转的目标、
（b）链尾/区域尾的直落续块，则它不能被任何 `else` 臂认领；函数级隐式出口块不得被物化成显式
`return None` 语句。

同层性：判据只读 region 的 `entry`/臂块/`else` 目标块 与「该块是否为 CFG 出口 sink」这类
**同层结构事实**，不读偏移量、不读函数名，也不引入跨层启发。

## 二、承重件告警（不得重踩）
* `project-r16-lead-sink-collapse`：sink 臂归并（`_if_arm_is_sink` ⇒ `merge := else_succ`）过度触发却是承重件，
  整块删除的全量 A/B 实测 improved=8 / **broken=5**（`instance.pyc 31→29`、`cgroup_utils 6→5`、
  两个 `plugin_manager`、`trade_live_broker 97→96`）。本轮判据必须避开这 5 个反例。
* Round 24 线 A（跳转修补）全量 better=2 / equal=8 / worse=14，打破 11 个 ok 文件 —— 已否证，
  本轮判据不得写成「消掉多余的 `JUMP_FORWARD`」。
* `_is_return_none_block`（约 L7116）与 `_find_enclosing_loop`（约 L2410）是既有可复用件；
  R22 落地的 J1′ 判据 (b) 项已经处理过「臂尾已是裸 `return None` 块 且 `else_succ` 直接后继也是」这一半。

## 三、门禁
见 `arm-design.md` §四。补充一条：候选必须先给出**子因 (i) 与 (ii) 各自的最小复现**，
其中 (ii)（`load_daily.<module>` 的 `JUMP·A·B → B·JUMP·A` 旋转）若无法在 `.py` 形状上复现，
必须在记录里写明并只以语料锚点验收（`arm-design.md` §六、§八）。
