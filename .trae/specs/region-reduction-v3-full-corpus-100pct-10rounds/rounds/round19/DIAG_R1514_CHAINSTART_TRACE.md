# DIAG R15-14 — 链起点 trace 实测：R14-05 的**前提被推翻**，真正的阻塞是父臂 merge 身份 + W14-A 修剪未接线

测量物全部在镜像 `D:/Temp/r161`（live 树未动：`region_analyzer 640d33a77dcb71c2`、
`region_ast_generator 5066b1367b6de3c7`、`git status -- core/` 空）。
镜像基线 = live `core/ pycdc.py scripts/` + 存档补丁 `region_analyzer.py`（`e13cc8827d214596`），
再加 112 个出口点标记 + 9 个方法包装（`563240489d1f3f8f`）。

## 0 探针惰性证明（CLI-vs-CLI，逐字节）

探针关 vs 探针开产物逐字节相同的目标：a01 `ce700ecc1b8f6b1b`、api_base `cc4b354986b9da69`、
strategy `a387e7e0f43443c3`，以及三个必须保持绿的对照 `plugin_system_fly_basicdata/basic_data_source 43/43`、
`IQCommon/data/local_finance 21/21`、`IQCommon/util/user_info_utils 9/9`。
（`IQEngine/core/strategy.pyc` 该轮产物为空 —— 文件缺失，记为 VOID，不计入惰性证据。）

## 1 控制读数

| 构建 | a01 | a02 | a03 | api_base | strategy |
|---|---|---|---|---|---|
| 未打补丁（= 现落地态） | 1/2 | 1/2 | 1/2 | 27/28 | 26/27 |
| 存档补丁（banked R14-05） | 1/2 | 1/2 | 1/2 | **25/29**（回退，且单元总数 28→29 ⇒ 多生成一个 code object） | 26/27 |

## 2 前提纠正（实测）

票面原话「这些字形里 or-run 根本没被识别为布尔链」**只对未打补丁的构建成立**：
pristine 在 a01/a02/a03 建链数 = **0**，在 `get_history_df` 建 15 条链但不含 `@996`。
**施加存档补丁后 or-run 确实成链**：

```
a01     chain_start(B@6)  → [[B@6,'or'],[B@18,'or']]
a03     chain_start(B@16) → [[B@16,'or'],[B@28,'or']]
api_base chain_start(B@996)→ [[B@996,'or'],[B@1008,'or']]，merge 经 _r16_cc_cleanup_hop(B@46) → B@94 / B@1098
```

单元仍红的理由是**父区域臂成员归属把臂体丢掉**（a01/a03 产物退化为 `if …: pass`）
⇒ 即 DIAG_R1405 §5 的 merge 身份票，本探针未触及。⇒ 链起点资格不是唯一闸门。

## 3 拒绝谓词与实测值（下一票的靶点）

- **api_base `@992`（and-run）与 a01/a02 `B@0`**：链走断在**认领守卫**，因为
  `_r16_boolop_cc_run_operand(cand=B@1008, prefix=[B@992,B@996])` 在第 (2) 个合取项为 **False**：
  `{"_T":"B@1098","_t":"B@1040"}`（a01：`_T=B@94, _t=B@50`）—— prefix 里混着
  `and` 成员（其跳转是 run 的**假出口**）与 `or` 成员（其跳转是**真出口**）。
  随后 R59 `M30757`：`_first_jt=B@1098` vs `_second_ft=B@1008` ⇒ `return None`。
  拒绝时刻 `claimed` n=55（含 `B@1008/B@1024/B@1036`），`block_to_region[B@1008]=IfRegion@B@1008`；
  `@1008` 自身在 `M28144` 已由新建 BoolOpRegion@996 认领，非双角色。
- **strategy `@512`**：cc 成员**已被准入**（`_r16_boolop_cc_run_operand(cand=B@536, prefix=[512,524])=true`，
  链长到 4 成员），随后被 **W14-A 修剪剥掉**（banked 30444–30470）——存档补丁从未给该修剪接线：
  `{"_w14_t0":"B@568","_w14_last_ft":"B@552","_w14_kept":[["B@512","or"],["B@524","or"]],"_w14_blk":"B@536"}`，
  而同一次链走已经算出 `_r16_cc_operand_success_edge(B@536)=B@568` —— **恰等于 `_w14_t0`**。
- **a03 pristine**：断在 `30018`，`LoopRegion@B@2(cond=B@2, head=B@16, back=B@66)`，
  `_b1b_c0 = (B@16 is header_block)`。

## 4 顺序事实（一次测量定死 §8 的适用范围）

识别顺序实测：`loop → chained_compare → boolop → ternary → conditional`。

- a01/a02/api_base：cc 区域在 boolop **之前**已存在
  （`_identify_boolop_regions:enter … cc_regions_present:["IfRegion@1008",…]`）——
  正是它污染了 `claimed`；
- a03/strategy：cc 通道返回 `nret:0`，cc IfRegion 直到
  `_identify_conditional_regions:exit` 才出现（`cc_created:["IfRegion@536",…]`）。
  ⇒ §8「cc 尚未登记」只对 strategy/a03 形状成立，对 api_base 不成立。

## 5 候选判据（纯结构事实；本票未实现）

1. **按算子分层的共享出口**：同目标合取只在「与本成员算子相同」的 prefix 成员上要求。
   若判错，反例 = a02（尾返回吞并）。
2. **让 cc 成员的 run 出口经由 cc 结构读取（success edge 而非成员自身尾跳转）**，
   接进 W14-A 修剪与 R59 测试（正是 §3 第二条的实测缺口）。
   若判错，反例 = a03（循环体/continue 出口）与 `repro_ccneg/` 的负极性链绿例。
3. **准入「尾跳转落在 run 自身已解析假出口/merge 上」的 and 前缀**。
   若判错，反例 = 当前为绿的 `m02_plain_and_not` 与普通 `if not c: A else: B`
   （即 §4 已否决的那条形如「IF_TRUE ⇒ 跳边=then」的判据）。

## 6 与其他票的衔接

- 本票把 R14-05/#40 的目标从「建链」改为「链已建后的两件事」：
  (a) 父 IfRegion 的 then/merge 身份（§2，DIAG_R1405 §5 原样成立）；
  (b) W14-A 修剪未读 cc success edge（§3 第二条，strategy 的唯一实测阻塞点）。
- 存档补丁 **不得安装**（api_base 27/28 → 25/29），但其中 `_r16_cc_operand_success_edge`
  与 `_r16_cc_cleanup_hop` 两个 helper 是 §5 判据 2 的直接材料。
- 判据落地验收顺序不变：`repro_arm` 3 例 → `repro`(9)+`repro_ccneg`(4) → 13 文件面板 →
  门链 label 19 vs **18** → 提交推送；施加/复判用 `D:/Temp/r150/integ_rig.py <candidate_region_analyzer.py>`
  （控制读数已封：battery GREEN=0 RED=3/3、api_base 27/28、strategy 26/27、
  quotation 153/153、matcher 17/17、klinedata 63/64、trade_info 38/41、wizard 55/58、real_quote 43/45）。
