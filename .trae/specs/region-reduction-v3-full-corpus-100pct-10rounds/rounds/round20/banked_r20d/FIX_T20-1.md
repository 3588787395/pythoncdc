# FIX_T20-1 — `core/cfg/region_analyzer.py` only: parent IfRegion arm identity at the `else_succ` predecessor census

Verdict line at the bottom. Live repo `D:/admin/.qoder/worktrees/app/f557fd/pythoncdc-main` was
never written by this agent; mirror `D:/Temp/r20d/`. All products under `D:/Temp/r20d/prod/`.
Base bytes as sealed: `region_analyzer.py 640d33a77dcb71c2` (verified sha16 of the mirror copy),
`region_ast_generator.py dff6e81a5f2ff9f6`.
Candidate lineage: `rounds/round19/banked_r19t4/region_analyzer.py` (`5ea802f2975b1f35`, closes
blocker B) **+ one new criterion** → delivered `D:/Temp/r20d/DELIVER/region_analyzer.py`
(`ce8ac50d11401920`, 32810 lines, 32809 CRLF, 0 bare LF, `py_compile doraise=True` clean).

---

## 0 The criterion, verbatim as it reads in the delivered code

```
    # [T20-1-A 词汇表] 条件取值/比较/短路接线族的指令字母表（与既有 _w14_pure_cond_pred
    # 的白名单同族）；承载语句的臂尾块必含此集合与噪声之外的操作码。
    _R20_COND_VALUE_OPS = frozenset({...})

    def _r20_explicit_edge_into(self, _r20_pb, _r20_es):
        # [T20-1-A 修复·臂内进入 else_succ 的显式跳转边不是「then 体落入独立 if」的证据]
        # 【识别条件】_r20_pb 的末端指令是一条**前向**跳转（条件跳转任意极性
        # FORWARD_CONDITIONAL_JUMP_OPS，或纯控制 JUMP_FORWARD），且其落点恰为 _r20_es。
        # 【归约方式】调用方对 else_succ 的**全部臂内侧前驱**要求该判据成立，并同时要求
        # 本臂内另有一条**承载语句**（含条件取值字母表之外的操作码）的臂尾块把原 merge 作为
        # 正常后继——此时 else_succ 是整条复合条件（and/or 与链式比较降级）的**假出口**，
        # 即本 if 的 else 臂入口；顺序落空边一个都不在臂内，故维持原 merge，else 臂照常发射。
        # 【危害形态】误判时 merge 被改成 else 臂入口，else_blocks 退化为空（entry==merge），
        # else 语句组下沉给更低层的链式比较子区，复合条件各段短路边随之落到整条语句的统一
        # 出口——同 opcode 只换落点（落点差，judge 按 CFG 等价判负）。
        # 【只读结构】块身份、末端跳转族与落点、块内操作码族；不读名称、字符串常量、绝对
        # 偏移、指令条数阈值、函数/文件名；判定发生在识别时，不事后改写已完成区域。

    def _r20_carries_statement(self, _r20_pb):
        # [T20-1-A 配套判据] 块是否承载语句：存在一条不属于「条件取值字母表 ∪ 噪声」的指令。
```

call site (single site; `_identify_conditional_regions`, was pristine :20518-:20519 — the only
`merge = else_succ` write between the then collection and the else collection; the nine other
`merge = else_succ` writes in the file are separate rules, none of which is on this shape's path):

```
                    # [T20-1-A] 臂内侧进入 else_succ 若**全部**是显式前向跳转边（无一
                    # 顺序落空），且本臂另有一条承载语句的臂尾正常汇入原 merge，则
                    # else_succ 是整条复合条件的假出口＝本 if 的 else 臂入口，不是
                    # then 体落进的下一条独立 if：维持原 merge（判据本体见
                    # _r20_explicit_edge_into / _r20_carries_statement）。
                    _r20_all_explicit = bool(_7_jumpers) and all(...)
                    _r20_arm_tail_to_merge = merge is not None and any(...)
                    if not (_w14_all_true_jump
                            or (_r20_all_explicit and _r20_arm_tail_to_merge)):
                        merge = else_succ
```

## 1 Ordering / claim fact relied on

None from region membership. The ticket's ordering wall (`_identify_conditional_regions` walks
`get_blocks_in_order()` ascending → parents before children, no cross-IfRegion claim set) is
**bypassed**: the parent's arm identity is derived from CFG edges that already exist at
parent-construction time — `else_succ.predecessors ∩ then_blocks`, each predecessor's terminal
instruction (family + `argval`), and one statement-bearing arm block's normal successor set.
No `self.regions` / `block_to_region` read, no retrospective repair of a finished region.

Evidence that the redirection really was the identification defect (probe process only,
`D:/Temp/r20d/probe2.py` wraps `_collect_branch_blocks` and prints the caller line):

```
pristine (640d33a77dcb71c2):
  [CBB] entry=996 merge=1782 stop=[1098] res=[996,1008,1024,1034,1036,1040] owner=None   caller :20406
  [CBB] entry=1098 merge=1098 stop=[996] res=[]                                          caller :20520
  => IfRegion e=992 merge=1098 then=[996,1008,1024,1034,1036,1040] else=[]
r19t4 candidate (5ea802f2975b1f35):
  [CBB] entry=996 ... merge=1782 owner=BoolOpRegion(996)  /  [CBB] entry=1098 merge=1098 res=[]
  => IfRegion e=992 merge=1098 then=[996,1024,1034,1036,1040] else=[]
DELIVER (ce8ac50d11401920):
  [T20DBG] blk=992 es=1098 merge=1782 jumpers=[1024,1036] expl=True tail=True
  [CBB] entry=1098 merge=1782 stop=[996] res=[1098,1142,1200]
  => IfRegion e=992 merge=1782 then=[996,1024,1034,1036,1040] else=[1098,1142,1200]
```

i.e. the criterion fires on the ticket's shape and produces exactly the arm identity that
r19t4 §6 asked for (`@1098` group as the parent's else, merge = the statement exit `1782`).

## 2 Stage 1 — unpatched mirror reproduces the sealed baseline (all 19 files + 6 batteries)

```
api_base 27/28   strategy 26/27   klinedata 63/64   handlers 29/30   wizard_quant_api 55/58
trade_info_utils 38/41   real_quote 43/45   order_api 37/37   realtime_event_source 12/13
risk_calculation/__init__ 41/43   trade_live_broker 118/128   quote 86/92   matcher 17/17
quotation 153/153   bar 85/85   strategy_universe 11/11   load_daily 27/27
plugin_system_log/__init__ 10/10   plugin_system_trade/function 71/71
repro 9R/9   repro_arm 0G/3R   repro_ccneg 3G/1R   repro_retbreak 2G/2R DRIFT=0
repro_orderapi 5G/0R   repro_tail 13G/0R
unit_diff api_base   hunks=0 landings=2 (@994->254 vs 219, @1006->254 vs 210)
unit_diff strategy   hunks=0 landings=4 (@522/@534->153 vs 87, @992/@1004->263 vs 197)
```

## 3 Stage 2/3 — LANDING BAR MISSED

| arm | api_base | strategy | api_base residual |
|---|---|---|---|
| base (640d33a…) | 27/28 | 26/27 | `hunks=0 landings=2` |
| r19t4 candidate | 27/28 | 26/27 | `hunks=1 landings=3` (@1006 gone, @1098 group dropped) |
| DELIVER (candidate + T20-1-A) | **27/28** | **26/27** | `hunks=1 landings=3` |

Product hashes prove the delivered criterion is **byte-inert on the product**:
`prod/v2/api_base.py == prod/p20/api_base.py == 07e731a45762eb4a` and
`prod/v2/strategy.py == prod/base/strategy.py == a387e7e0f43443c3` — while the *region* it emits
did change (§1). So the correct parent arm identity is declared and the renderer ignores it.

Independent confirmation from strategy, where the analyzer already declares the right shape in
the bytes I measured: `IfRegion e=512 merge=1286 then=[536,…,820] else=[568]` — the body `@568`
is already `else_blocks[0]` and the run's own `BoolOpRegion e=512 merge=568` — yet `@522/@534`
still emit `->820` (the enclosing statement-list end) instead of `->568`. Same for the second
instance (`IfRegion e=982 merge=1038`, `BoolOpRegion e=982 merge=1038`, `@992/@1004 ->1286`).

## 4 Stage 4 — collateral (partial, stopped at stage 3)

Delivered arm, 8 files measured (the all-green ones + both shapes the ticket flagged):
`quotation 153/153, matcher 17/17, log_init 10/10, trade_function 71/71, bar 85/85,
strategy_universe 11/11, load_daily 27/27, order_api 37/37` — **zero drift**.
6 batteries on the delivered file:

```
repro RED=9/9   repro_arm GREEN=0 RED=3/3   repro_ccneg GREEN=3 RED=1/4
repro_retbreak GREEN=2 RED=2 DRIFT_VS_BASELINE=0/4   repro_orderapi GREEN=5 RED=0/5
repro_tail GREEN=13 RED=0/13        (all six identical to the stage-1 baseline → zero drift)
```

The remaining 9 panel files were not re-measured (ladder stopped at stage 3; this file must not
be installed — it fires without flips).

Delta provenance: `D:/Temp/r20d/DELIVER/region_analyzer.py` = r19t4 candidate bytes
(`5ea802f2975b1f35`) + the T20-1-A hunks. The delta alone is reproducible byte-exactly (CRLF
anchors, count==1 asserted) on any base by
`python -X utf8 D:/Temp/r20d/patch20b.py <base region_analyzer.py> <out>` — so the criterion can
be re-applied on top of the landed bytes if a later generator-side ticket wants it.
Probe rigs (own-process only, never installed into the repo): `D:/Temp/r20d/probe.py`
(block/region/ownership census), `D:/Temp/r20d/probe2.py` (`_collect_branch_blocks` caller +
`block_to_region` owner at call time), `D:/Temp/r20d/panel.py` (arm driver,
`pycdc.py --region <abs pyc> -o D:/Temp/r20d/prod/<arm>/<name>.py` then
`scripts/pyc_verify.py single --source`), `D:/Temp/r20d/idx.py` (dump-index → offset mapping).
Mirror core/cfg/region_analyzer.py restored to pristine `640d33a77dcb71c2` after measurement.

## 5 Negative arm that was falsified first (kept as evidence)

v1 of the same ticket (`D:/Temp/r20d/cand/region_analyzer_patched.py`, sha16 `abcee214b7eef8ae`)
wrote the criterion as "every arm-internal predecessor of `else_succ` is a *statement-free
condition-wiring* block (value-op alphabet only) landing on `else_succ`". Measured term-by-term
on api_base: `B@1024` = `LOAD*/COMPARE_OP + POP_JUMP_FORWARD_IF_FALSE -> 1098` → True;
`B@1036` = `POP_TOP + JUMP_FORWARD -> 1098` → **False** (POP_TOP is outside the alphabet, and the
repo's own comment at :29005/:29581 treats POP_TOP-bearing pure-JUMP_FORWARD blocks as a distinct
family = break/discard lowering, so widening the alphabet there is not free). Product then stayed
byte-identical to the r19t4 candidate → v1 abandoned in favour of the edge-based v2 above.

## 6 Where the remaining defect actually lives (for the next ticket)

Not in `region_analyzer.py`. The analyzer now declares, for both units, the arm entry the landing
needs (`api_base`: `IfRegion@992.else_blocks[0] = B@1098`; `strategy`: `IfRegion@512.else_blocks[0]
= B@568`, `IfRegion@982` sibling likewise). The product sends the run members' short-circuit edges
to the **enclosing statement-list end** (`1254` / `820` / `1286`) instead of that declared arm
entry. That target choice is made on the consumption side
(`core/cfg/region_ast_generator.py`, the BoolOp-run-in-condition edge resolution /
elif-chain rendering), which this ticket had no authority to touch. Same family as the landed
#37 "tail jumps must land on the region-declared merge" axis, whose residual instances the
`trade_live_broker` trio (1 landing each, all *earlier* than orig) already exhibits.

Verdict: **FALSIFIED** — stage 3 not met (api_base 27/28, strategy 26/27; zero flips; the two
ticket units' products byte-identical to the unpatched/r19t4 arms). Specific predicate that is
still False, and on which block: none inside `region_analyzer.py` any more —
`_r20_all_explicit=True` and `_r20_arm_tail_to_merge=True` on `B@992`/`else_succ=B@1098`
(v1's `_r20_cond_wiring_into(B@1036, B@1098)` was the False term, falsified in §5). The failure
moved to the consumer: with the parent's `else_blocks=[1098,1142,1200]` correctly declared, the
generator still does not emit that group (hunks 0→1, `- @1124 BINARY_OP +`, `- @1128 STORE_FAST
_last_real_59`) and still resolves `@522/@534 -> 820` for strategy.
