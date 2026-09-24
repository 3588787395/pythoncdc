# Round 63 batch 5 — ANALYSIS (工具函数族 + 下单 API 族, 5 pyc)

HEAD = 96a5f310；生成器工作树 sha256 前缀 b9778ee0130865d55888（BOM+CRLF，纯 CRLF）。
region_analyzer 本轮**未改**（候选只动 region_ast_generator）。

## 0. 基线复核（arm=landed，dump/landed.jsonl，与 FACTS.md 逐行一致）

| pyc | matched | 缺陷函数 [orig, decomp, jumpdiff, truediff] |
|---|---|---|
| IQCommon/util/common_func.pyc | 18/21 | get_crontab_execute_time [93,81,2,48]、get_kline_time_by_frequency_array [231,228,0,45]、get_kline_time_by_section [210,190,0,84] |
| IQCommon/util/trade_info_utils.pyc | 38/40 | get_trade_list [339,323,14,148]、trade_operation [304,302,2,40] |
| IQData/utils/common_func.pyc | 22/24 | get_kline_time_by_section [210,190,0,84]、handle_exrights [276,268,1,263] |
| .../fly_api/order_api.pyc | 32/34 | future_order [101,92,2,36]、option_order [83,73,3,39] |
| fly/simtradding/flyAccount.pyc | 21/23 | _do_request [436,429,2,379]、init_connection [42,41,0,25] |

目标清单标注的 (32/35) 与实测 18/21 不符，以实测为准。

## 1. 见证 W1 = flyAccount.init_connection（选它的原因：deficit 只有 1、jumpdiff 0，纯形状缺陷）

### 1.1 真实源码形状（已用 shape.py 反推并逐指令验证）
`test_repros/round63_b5/r63b5_w1.py`（+ 同目录 .pyc）是**逐指令同形**的合成复现：
landed 臂在它上面复现出完全相同的缺陷元组 [42,41,0,25]（dump/w1_landed.jsonl），
因此后续全部推理在小文件上完成，每轮 <20 秒。

原始字节码（偏移）：
```
   8: [CreateConnector…UNPACK…STORE×2]  error_no != SUCCESS  POP_JUMP_IF_FALSE -> 172   ← 外层 if 测试（=循环头块）
 100: i < 3                              POP_JUMP_IF_FALSE -> 154                        ← 内层 if 测试
 112: time.sleep(1)                      JUMP_FORWARD -> 160                             ← then 臂以显式跳转结束
 154: error_info = '…超时…'              JUMP_FORWARD -> 176                             ← else 臂 = break（出环）
 160: i += 1                             JUMP_FORWARD -> 174                             ← 外层 then 臂的后续语句
 172: JUMP_FORWARD -> 176                                                        ← 外层 else 臂 = break
 174: JUMP_BACKWARD -> 8（回边）          176: return {'error_no':…,'error_info':…}
```
源码形状（shape.py 对 42 条指令做逐条比对，只有 1 条不同，见 1.4 证伪项）：
```python
while True:
    error_no, error_info = …CreateConnector(1, …)
    if error_no != SUCCESS:
        if i < 3:
            time.sleep(1)
        else:
            error_info = '…超时…'
            break
        i += 1
    else:
        break          # 172: 出环臂是「条件跳转目标块」，不是 fall-through
return {…}
```

### 1.2 区域树实测（rdump.py，只读，直接调 core.cfg.build_cfg + CFGRegionAnalyzer）
```
LoopRegion WHILE_LOOP entry=8 body_blocks=[8,100,112,154,160,172,174] break_blocks=[176]
  IfRegion IF_THEN_ELSE entry=100 merge_block=176
      then_blocks=[112, 160]   ← 160（i += 1）被吸进内层 then 臂
      else_blocks=[154]
  外层 if（块 8）**没有** IfRegion：块 8 角色 = LOOP_HEADER，其条件边被循环头启发式接管
块角色：8=LOOP_HEADER 100=LOOP_BODY 112=LOOP_BODY 154=BREAK 160=LOOP_BODY
      172=PURE_BREAK 174=LOOP_BACK_EDGE 176=RETURN
```

### 1.3 生效机制（trace_break.py 用 sys.settrace 精确抓到构造点）
产物里的 `if not error_no != SUCCESS: break` 由
`region_ast_generator.py::_loop_build_if_with_exit_branches`（L10433）构造，L10459
`_then_stmts = [{'type': 'Break'}]` 是断点行。机制链：
L10444-10448 无条件做「交换两臂 + 取反条件」的卫哨改写（`_else_is_exit and not _then_is_exit` → swap，`_negate=True`），
把出环臂提到 then 侧；卫哨形态下 else 臂（=真正的循环体续块）被 L10485-10487
`if _then_has_break: pass` 丢弃，改由父层平铺发射。

### 1.4 候选 c1（specs/cand_r63b5_hdrjt.json，2 处编辑，L10444-10448 + L10484-10493）
判据（只看控制流方向，不看名字/块号/文件）：**出环臂是条件跳转的「目标」还是「落穿」**。
- 落穿侧出环（`if not cond: break` 的真实布局：测试直接条件跳到续块）→ 保留既有 swap+negate；
- 跳转目标侧出环（本例 172，一个环内 PURE_BREAK 桩块，其后继才是循环出口）→ 不 swap、不取反，
  按自然 IF_THEN_ELSE 归约，并把出环臂物化成 `orelse=[Break]/[Return]`（与既有 then 侧
  `_then_succ in _exit_succs` 分支同构、方向相反）。

实测（dump/c1.jsonl、dump/w1_c1.jsonl）：

| 见证 | landed | c1 |
|---|---|---|
| flyAccount.init_connection | [42,41,0,25] | [42,41,**3**,**12**] |
| 合成复现 r63b5_w1.init_connection | [42,41,0,25] | [42,41,3,12] |
| 其余 4 支 pyc（含孪生 IQData/IQCommon common_func、order_api、trade_info_utils） | — | **产物逐字节相同**（cmp_arms: REGRESSION=0 IMPROVED=0 MOVED=1 SAME=4） |

→ 见证**确实动了**（truediff 25→12，指令序 L16-L29 段与 orig 逐条对齐：
`POP_JUMP_IF_FALSE / i<3 / POP_JUMP_IF_FALSE / sleep / JUMP_FORWARD`），不是 R62 那种 inert 候选。
但 deficit 仍为 -1、jumpdiff 0→3，且**产物语义被破坏**（`i += 1` 逃出外层 then 臂、内层 else 的 `break` 丢失）：

```python
if error_no != SUCCESS:
    if i < 3: time.sleep(1)
    else: error_info = '…超时…'   # ← break 丢了
else: break
i += 1                          # ← 逃到整条 if/else 之外
```
**结论：c1 不可单独落地**，它只是把缺陷从「卫哨极性」推进到「臂归属」这一层，
量到了 13 个 truediff 的下界，并证明极性判据本身是生效的。

### 1.5 被证伪的假设（都做了实测，不是推测）
1. ~~「根因只是 `_loop_build_if_with_exit_branches` 的 swap+negate」~~ → c1 证伪：
   极性改对后形状仍错，因为内层 IfRegion 已把 160 吸进 then_blocks（见 1.6）。
2. ~~「then 臂改用 `_generate_region(entry_region)`（父层只引用子区域入口）就能修正」~~
   → c2（specs/cand_r63b5_hdrjt2.json，在 c1 上加第 3 处编辑 L10478-10483）实测
   元组 [42,41,**2,15**]，比 c1 的 12 **更差**，证伪。
3. ~~「`i += 1` 与 `break` 的错位是生成器 `_generate_if` 的臂切分问题」~~ → 区域树里
   then_blocks=[112,160]、merge_block=176 已经是分析器的产物，生成器无从区分。
4. 反推源码形状的实验：`else: continue` 假设**被证伪**（172 是 JUMP_FORWARD→176 出环，
   不是回边）；`else: pass` 假设**被证伪**（42 条指令里 172 的跳转未被 no-op 过滤掉，
   说明它是真的跳到循环出口）；只有 `else: break` 与 orig 差 1 条（shape.py 输出
   `X 35 | JUMP_BACKWARD 8 | JUMP_FORWARD 176`，即我的候选多出一条出环跳转）。

### 1.6 下一步判据方向（写给 R64，位置精确到函数）
`region_analyzer.py`：IfRegion 的 merge/臂收集（L17521、L17557
`_collect_branch_blocks(then_succ, merge, then_stop)`，函数体在 L26449）。
本例 merge 被算成 176（循环出口），于是 then 臂沿 `112 →(JUMP_FORWARD) 160 →174→8→…→176`
无界吸收到 176。真实形状要求：**当某臂（else=154）的终块出环（BREAK/PURE_BREAK → 循环出口）
而另一臂（then=112）的终块以显式无条件前向跳转离开本臂、其目标块（160）不是该终块的
fall-through 时，merge 应钉在该跳转目标（160），160 回归父层序列归约。**
即「臂的边界由显式跳转决定，而不是由 post-dominator 决定」——这与 L17515-17530 已落地的
[R31b]「一臂为汇点 ⇒ merge := else 臂入口」是同一族的判据，属于**收窄既有结构判据**，
不是新开逃逸口。风险：`_collect_branch_blocks` 是全语料公用例程，必须走 402 全量分片
（`--nshard=2 --shard=0/1`，每条 <280 秒）验证。

## 2. 与第 3 批兄弟代理的重叠声明
本批改动全部落在 `region_ast_generator.py::_loop_build_if_with_exit_branches`
（循环头 if 的出环臂极性与臂归属）与（下一步）`region_analyzer` 的 IfRegion merge 计算。
**未触碰** BoolOp 区域的 merge 块栈语义；如果第 3 批也改 `_collect_branch_blocks` /
IfRegion merge（1.6 的方向），两处改动会重叠，集中验证时只能落地其一。

## 3. 本批未推进的部分（诚实记账）
- order_api（future_order/option_order）：本轮 3 个候选全部 SAME（产物逐字节未变），
  即 R50 指出的 `_try_build_ternary_kwarg_call` kwarg 槽位提前 bail 与「只做前向的链遍历」
  在本批候选下仍未被触及；「为什么合成复现能修而真实 future_order 不动」这一问题**未回答**，
  因为本批的 W1 复现修的是另一族缺陷（循环头极性），与 order_api 的 ternary/kwarg 族不同源。
- trade_info_utils（get_trade_list / trade_operation）、IQData handle_exrights、
  IQCommon get_kline_time_by_*：本轮未展开诊断（45 分钟预算内全部投给 W1 一条链）。
  孪生文件（IQData vs IQCommon 的 common_func）在 c1 上表现完全一致（都 SAME），
  没有证据支持「同一缺陷在两源不同根因」在本批被触发。
- 402 全量：**未跑**（c1 语义被破坏，不具落地资格，跑全量只会浪费预算）。

## 4. 复现与复测指令（全部非侵入，产物只落 diag5/）
```
cd D:/Temp/opencode/r63gate/diag5
# 1) 合成复现（等价形状，20 秒一轮）
python -X utf8 h62.py run --arm=landed --list=w1.txt --out=dump/w1_landed.jsonl --budget=200
python -X utf8 h62.py build --spec=specs/cand_r63b5_hdrjt.json --dst=c1
python -X utf8 h62.py run --arm=c1 --list=w1.txt --out=dump/w1_c1.jsonl --budget=200
# 2) 反推源码形状：把候选源码喂给 shape.py，逐指令对齐
python -X utf8 shape.py <pyc> <fn> <cand.py>
# 3) 区域树 / 块角色（只读，直接调 landed core）
python -X utf8 rdump.py <pyc> <fn>
# 4) 定位构造 AST 节点的源码行（sys.settrace，只读）
python -X utf8 trace_break.py <pyc>
# 5) 逐函数指令对比
python -X utf8 fdiff.py <pyc> <OK.py> <fn> [--raw]
```
