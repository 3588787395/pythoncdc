# Round 21 设计（arm-design）：R21-A 协程语句前缀块的 body 判据补全（一条规则，两个接线点）

诊断全文见 `test_repros/round21_oauth2/ANALYSIS.md`（指令级判决 §2、两半根因 §4/§5、
候选表 §6、电池实测 §7、原则核对 §8、诚实清单 §10）。落地实测见 `fixes.md`，收尾见 `OUTCOME.md`。
落地前 HEAD = `15a8de06`（Round 20 收尾），诊断在 `5c63ce6b` 上做出，两个 rev 上锚点原样存在、
结论一致（ANALYSIS §6/§8 末表）。

## 一、症状与目标

`site-packages/fly/oauthenticator/oauth2.pyc` —— 同一模块里两份同形孪生 `post`，
官方批量 11 函数 / 10 匹配 = `partial`，严格尺子 `DEFECT 10/12`：

```
DEFECT <module>.HSIDOAuthCallbackHandler.post   [seq_len] orig=175 decomp=166   (-9)
DEFECT <module>.OAuthCallbackHandler.post       [seq_len] orig=190 decomp=181   (-9)
```

丢的 9 条 = 一整个 `yield self.spawn_single_user(user)` 语句块（7 条）＋ 一对
`LOAD_CONST None; RETURN_VALUE`。**实测是 ABSENT（整块消失），不是 relocated**：
非跳转指令多重集差量恰好 `CALL-1 LOAD_CONST-1 LOAD_FAST-2 LOAD_METHOD-1 POP_TOP-1
RESUME-1 RETURN_VALUE-1 YIELD_VALUE-1`，只有 delete 窗口没有配对 insert，且
`argrepr` 里 `spawn_single_user orig=2 decomp=1`（ANALYSIS §2）。

真实源码形状（ANALYSIS §3）：块 624 与块 734 **完全同形** —— 「`yield f()` 语句前缀 ＋
以条件跳转结尾」，一个在 then 臂、一个在 else 臂。基线核把 624 判成 BoolOp 的 `and` 操作数、
把 734 判成纯 elif 条件块，两处都错，且错在**同一条同层判据的两个缺半**上。

## 二、两处根因（缺一不可）

**① 分析层 `_detect_boolop_conditional_chain` 的非首成员块守卫**（落地前
`core/cfg/region_analyzer.py` 24236-24243，诊断 rev 上 24186-24200）只查 `STORE_*`：

```python
if chain:
    _has_store = any(i.opname in ('STORE_FAST', ... 'STORE_ATTR') for i in current.instructions)
    if _has_store:
        break
```

而**同一函数**对起始块早已写了完整判据 `_sb_has_body`（落地前 24056-24078，诊断 rev
24013-24035）：先查 `STORE_*/BINARY_OP/DELETE_*`，再补「`CALL` 紧跟 `POP_TOP` ⇒ 块内含
表达式语句」。`sys.settrace` 实锤块 624 因无 `STORE_*` 被收进链，返回
`[(566,'or'),(624,'and')]` ⇒ `BoolOpRegion` ⇒ 产物 `if status is not None and cgroupmode == '1':`，
嵌套 if 的 else 臂（块 730 的 `return`）整块消失 ⇒ **−2**（ANALYSIS §4，日志 `logs/tr566.txt`）。

**② `_build_elif_region` 内嵌 `_check_elif_chain` 的 `_has_body_stmt`**（落地前
18274-18284，诊断 rev 18216-18243）**已有**「`CALL` 紧跟 `POP_TOP` ⇒ body 语句」判据，
但它的过滤表只排除 `NOISE_OPS + ('RESUME','NOP','CACHE','EXTENDED_ARG')`，**漏了
CPython 3.11 协程语句插在 `CALL` 与 `POP_TOP` 之间的 `YIELD_VALUE`** ⇒ 块 734 的
`CALL YIELD_VALUE RESUME POP_TOP` 看不见这一半结构 ⇒ `first_else=734` 被当纯 elif 条件块，
前缀语句退到 if/elif/else 链之后，链上三支全部 return ⇒ 死代码消除整块删除 ⇒ **−7**
（ANALYSIS §5，`r21_cond.py` 实测 `_build_elif_region([210,548,…,734,802,836])` 抢走了
`_build_basic_if_region([734,802,836])` 已建好的 IfRegion）。

−2 ＋ −7 = **−9**，与 §一 的删除窗口逐条吻合。

## 三、规则（纯同层结构判据，两个接线点共用同一谓词文本）

> 一个以条件跳转结尾的块，若其**末条条件跳转之前**存在 `CALL` →（间隙只允许
> `YIELD_VALUE`/`RESUME`）→ `POP_TOP`，或 `STORE_*/BINARY_OP/DELETE_*`，则它是 **body 块**
> （含值丢弃语句），不是 BoolOp 操作数块，也不是纯 elif 条件块。

零新判据：这正是仓库里已经写了两遍（`_sb_has_body`、`_has_body_stmt`）的那条谓词的补全。
缺的只有 ① 成员块守卫根本没有 `CALL…POP_TOP` 那一半，② 过滤表漏 3.11 协程的 `YIELD_VALUE`。
不看函数名、不看字符串常量、不看原始字节码偏移（`i.offset < 末条指令.offset` 是本块内的
结构边界，与该站点既有判据同一写法），不跨区域、不跨层次。

候选表（ANALYSIS §6，全部实测；`D:/Temp/r21d/probes/r21_mk.py` 表驱动）：

| id | 规则 | HSID/OAuth decomp | 孪生 strict | 电池 | 判决 |
|---|---|---|---|---|---|
| base | 无（5c63ce6b 与 15a8de06 同） | 166 / 181 | 10/12 | 6 MISMATCH / 10 MATCH | 缺陷基线 |
| c1 | 站点 A 宽版（向前≤5 找 POP_TOP） | 176 / 191 (+1) | 10/12 | 2 MISMATCH | 残留 B 的错位 |
| c2 | 站点 A 更宽（块内任意 POP_TOP） | 176 / 191 | 10/12 | 同 c1 | 与 c1 同测值、风险更高 ⇒ **丢弃** |
| c3 | 只站点 B（过滤表补 `YIELD_VALUE`） | 173 / 188 (−2) | 10/12 | 5 MISMATCH | 证明两半缺一不可 |
| c5 | c1 + c3 | 175 / 190 | 12/12 | 4 MISMATCH | 完全收口 |
| **c6 = R21-A** | 站点 A 用与起始块/elif **同形**的判据文本 ＋ 站点 B 同 c3 | 175 / 190 | 12/12 | 3 MISMATCH / 13 MATCH | **采纳** |
| c8 | c6 ＋ 第三份拷贝（BoolOp 起始块）也补间隙 | 175 / 190 | 12/12 | 同 c6 | 目标上零增量、爆炸半径更大 ⇒ **不并入** |

## 四、四条区域归约原则的保持（落地后逐条复核）

1. **自底向上**：只改「块是否为 body 块」这一条同层判据，不改任何识别顺序、不新增遍历维度；
   内层 if 仍先于外层 BoolOp/elif 链被识别。
2. **每块唯一归属**：站点 A 让块 624 只归 then 臂的 IfRegion（不再同时是 BoolOp 操作数），
   站点 B 让块 734 只归 else 臂（`_build_basic_if_region` 已建出的 IfRegion 不再被 elif 链
   抢走）——两处都是**减少**争抢，没有制造新的多重认领。
3. **嵌套即抽象节点**：624/734 回到各自臂内后，内层 `if cgroupmode == '1'` 仍是挂在臂下的
   单个子 IfRegion（产物里可见嵌套结构，见 `fixes.md` §二 的逐行 diff）。
4. **入口引用**：两个谓词都只读被判定块自身的 `instructions` 与 `get_last_instruction()`，
   不铺开子块、不引用兄弟区域内部。

## 五、与 R20-A 的正交性

R20-A（HEAD `15a8de06`）落在 analyzer `@@ -84 / @@ -6169`（`_collect_natural_loop_body`
break-target 判别）与 generator 16934-16942/16988（W15-C 臂尾终止守卫）；本提案两个站点
（`_check_elif_chain` 18274-18284、`_detect_boolop_conditional_chain` 24236-24243）与其
**完全不相交**，不改任何 loop-break/return 路径、不在终止符之后新增语句 ⇒ 不触发
「死代码被 DCE 吞掉」的陷阱。实测在 `15a8de06` 镜像核上应用成功、孪生同样 12/12、
电池逐项同值（ANALYSIS §8 末）。

## 六、落地位置与已知代价

* 站点 A：`_detect_boolop_conditional_chain`（def 23908）内成员块守卫之后 →
  落地后注释 24270-24293、判据代码 24294-24315。
* 站点 B：`_build_elif_region`（def 17874）→ `_check_elif_chain`（def 17991）内
  `_fe_instrs_before_jump` 扫描 → 落地后注释 18280-18298、判据代码 18299-18310。
* **已知代价（尺子盲区，落地时实测，见 `fixes.md` §九）**：站点 A 单独就会把
  `IQEngine/plugins/plugin_system_event_source/realtime_event_source.pyc` 已缺陷的
  `RealtimeEventSource.clock_worker` 的产物从 `orig=1276 decomp=1251` 变成 `decomp=1079`
  ——严格尺子的 bad **计数**不变（10/12 ⇒ 产物门 UNCHANGED、A/B 只记 signature-only），
  但丢的指令从 25 条涨到 197 条。该产物按「不得变差」原则保全为落地前版本，
  根因（截断 BoolOp 链后父臂的双认领）移交 Round 22。
