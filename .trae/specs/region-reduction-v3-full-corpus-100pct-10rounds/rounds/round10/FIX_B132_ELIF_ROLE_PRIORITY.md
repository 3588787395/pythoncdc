# Round 10 FIX 票 B132：`matcher.DefaultMatcher.match` elif 臂 —— 发射端三点协同修复

**范围**：只实现 DIAG_B131 判定的发射端机制；不改 `core/`，不改分析器角色；镜像施工，交付 patch。
**Mirror**：`D:/Temp/r132b/wt`（`core/ bytecode/ parsers/ utils/ scripts/ pycdc.py` 逐文件 sha256 对齐仓库）。
封表校验：`core/cfg/region_ast_generator.py = e9a8f65f6451bcc895c5558528b03a9d6ef1045f418f0efd267f9900ef174e74` ✓
`core/cfg/region_analyzer.py = 38a1d5142d132fd7288229851a33a02df71ccb3cf98ee40f84d4042bb8d1135e` ✓

## 0. 先裁决 DIAG 的内部矛盾（§三.3「修分析器」 vs §六.3「分析器惰性」）

在封表字节 `e9a8f65f…` 的 `core/cfg/region_ast_generator.py`（发射端）实测标识符读数（定义 vs 使用分开数）：

| 标识符 | 发射端引用数 | 说明 |
|---|---|---|
| `block_roles`（复数属性，直接读） | **0** | 发射端从不直接读分析器的 `block_roles` 字典 |
| `get_block_role(`（访问器调用） | 102 | 发射端通过访问器间接读角色（`get_block_role` 内部 = `self.block_roles.get(...)`） |
| `BlockRole`（枚举类引用） | 186 | 均为对 `get_block_role` 返回值的比较，非读 `block_roles` 字典 |
| `IF_ELIF_CONDITION`（§三.3 拟赋予的角色） | **0** | 发射端从不读这个具体角色 |

三个丢弃点（`:16140-16177`、`:19307-19324`、`:54886-54921`）实测 `get_block_role`/`block_role`/`BlockRole`
命中数均为 **0** —— 三条路径的判据全是「区域 entry 身份 / 块集成员 / 块末 opcode / 后继身份」，
一条都不查角色。

**结论**：`block_roles` 原始属性在发射端 0 读，且 §三.3 拟修正的那个角色 `IF_ELIF_CONDITION`
在发射端 0 读，三个丢弃点 0 角色读 ⇒ **§六.3 成立**：把臂入口身份修进分析器角色表对本缺陷产物零影响，
**惰性**。**§三.3 与 §五末句「单点=修 region_analyzer」作为落地判据作废**（角色优先级修正本身仍值得做，
属分析器可解释性改进，非本缺陷落地判据）。落地机制 = 下述三个发射端站点。据此把 §七 追加进 DIAG 文档。

## 1. 基线（镜像实测，HEAD 字节）

`python -X utf8 pycdc.py matcher.pyc -o prod/matcher.py` →
`pyc_verify single` = **`units=16/17 success_rate=94.12%`**，唯一失败单元 `<module>.DefaultMatcher.match: Failure: Different control flow`。
被吞语句 `if order.asset.symbol[:3] in ('688','689'):`（块 @2164，10 指令）应在 `else:`(产品 157 行) 体内、
与 `'300'` 链（产品 167 行）同缩进（28 空格）作兄弟语句出现。

**哨兵/锚点 HEAD 基线（镜像实测，pristine）**：`trade_info_utils = 37/41`（失败名
`kill_trade_process / get_trade_status / query_trade_strategy_info / query_strategy_id`）；
`wizard_quant_api 整文件 = 55/58`；`fly/data/quotation = 153/153`。

## 2. 三点协同实现（`core/cfg/region_ast_generator.py`，全部只读白名单判据）

1. **`_if_generate_full_elif_chain` 尾块（原 `:16158-16177`）**：在 R46-B owner 判据之后加
   `elif _mb45_sibling_head:` 分支——`_mb45` 末条有语义指令 ∈ `FORWARD_CONDITIONAL_JUMP_OPS`
   且 `len(_mb45.conditional_successors)==2` ⇒ 判为兄弟语句头块，置 `_mb45_handoff_to_enclosing`
   并**既不登记也不补发**，交回包围序列发射（原则 2 唯一归属）。
2. **`_if_generate_elif_chain` merge 认领（原 `:19318-19324`）**：把「merge 是否为任何区域 entry」
   的身份式豁免换成「`elif_boolop.merge_block in elif_boolop.blocks`」——区域只登记自有块。
3. **`_generate_block_statements_body` 延迟交接（原 `:54896-54921`）**：`:54920` 的
   `generated_blocks.add` 改为仅当「重建条件确有接收者」时执行；接收者 = `_leading_operand` 挂到
   BoolOpRegion entry（其唯一消费者 `_build_boolop_expression`/`_graft_pending_operand`）
   或 `_leading_guard_candidate(...)` 返回 True（不再丢弃其返回值）。无接收者 ⇒ 不静默 return，
   落到下方就地发射内联 if。**未**放宽 `:38496` 的 `[C3]` `parent is not None`。

## 3. 逐半 A/B（单命令实测；判定 = 产物字节是否变化 + matcher 读数 + 哨兵读数）

以 `orig`（pristine，`e9a8f65f…`）为对照，逐半单独/组合施加（`-X utf8`，全在镜像内）：

| 变体 | 施加 | matcher 产物 sha256[16] | 产物字节 vs pristine | @2164 语句 | matcher 读数 | trade_info_utils |
|---|---|---|---|---|---|---|
| v_none | 无（pristine） | `a4e4980f31e5f46f` | — | 缺（吞） | 16/17 | 37/41 |
| v_c1 | 仅 #1 | `a4e4980f31e5f46f` | **不变（无操作）** | 缺 | 16/17 | 37/41 |
| v_c2o | 仅 #2（自有块） | `a4e4980f31e5f46f` | **不变（无操作）** | 缺 | 16/17 | 37/41 |
| v_c3 | 仅 #3 | `a4e4980f31e5f46f` | **不变（无操作）** | 缺 | 16/17 | **36/41**（破 `create_user_code_iqe`） |
| v_c2s | 仅 #2（头块身份变体） | — | — | — | 16/17 | 36/41（亦破） |
| v_c23o | #2+#3 | `f6b7ca4ee24f85e4` | **变** | 出现在缩进 32（**误挂 '300' 臂内**） | 16/17 | 36/41 |
| v_all_o | #1+#2+#3 | `0120e7b6aad35c6d` | **变** | 出现在缩进 **28（正确兄弟层）** | **16/17（未翻转）** | 36/41 |

**每半是否移字节**：单独施加速率上，#1/#2/#3 **各自对 matcher 产物逐字节不变**（印证 DIAG §六「无一足够」）；
#2+#3 合施使语句**回来但误挂**（复现 §三.2 的 line-169 型错层）；加 #1 后落到**正确缩进 28**。
⇒ #1 唯一作用是**臂边界层级**（32→28），非语句存在性。

## 4. 门禁结果（实测）

- **门禁 1（matcher 17/17）：未达。** 三点协同（v_all_o）把 @2164 恢复到正确兄弟层（缩进 28），
  但**仍 16/17**。根因：@2164 的**体内在构造错误**。@2164 子树实测 CFG（`match` 单元，pristine `build_cfg`）：
  ```
  2164 IF_FALSE→2464, csucc=[2208,2464]        # if symbol in ('688','689'):
  2208 LOAD is_first_five; IF_TRUE→2464        # 落空(假)→2212, 真→2464 ⇒ if not is_first_five:
  2212 BUY== ; IF_FALSE→2338                   # ┐
  2254 >=up ; IF_FALSE→2338  TRUE→2334 cont    # ┴ if BUY and >=up: continue   （短路 and，同落点 2338）
  2338 SELL==; IF_FALSE→2464                   # ┐
  2380 <=down; IF_FALSE→2464 TRUE→2460 cont    # ┴ elif SELL and <=down: continue
  2464 JUMP_FORWARD→3210                        # 汇合 = 块后邻语句（`if self._volume_limit…`），**非** continue
  ```
  字节码逐边吻合的**唯一正确形**：`if symbol[:3] in ('688','689'): / if not is_first_five_trading_days:
  / if BUY and >=up: continue / elif SELL and <=down: continue`（`is_first_five` 真→2464→下一语句，
  **不是** continue；BUY/>=up 为**扁平 and**，非嵌套）。
  两条发射路径都给不出该形：
  - **裸内联构造器**（#3 落到的 `:54923+`）产**嵌套** `if BUY: if >=up: continue`（>=up 假落 2464 而非 2338
    ⇒ 控制流不同）；即便再叠「else 侧为纯汇合桩的 IF_TRUE 取反」把 `not is_first_five` 补上（实测该极性补丁
    **又把 trade_info_utils 打到 36**，且 matcher 仍 16/17），and-链仍错。
  - **经 `_generate_region(IfRegion@2208)` 发臂**（实测）产 `if is_first_five or BUY and >=up: continue /
    elif SELL and <=down`——把 @2208 的 `is_first_five` 折进了子链 or（真→continue，与 2464→下一语句矛盾）⇒ 仍 16/17。
  ⇒ @2208 作为 `IfRegion`（类型 IF_THEN）的**渲染**把自身 guard 测试并入子链 or，属区域渲染/构造问题，
  **不在三点授权发射站点内**；分析器角色路线又已证惰性（§0）。故三点无法达 17/17。
- **门禁 2（哨兵）：破。** #3 单独即把 `trade_info_utils` 打到 36/41，**新增失败名 `create_user_code_iqe`**
  ——正是 DIAG §一.3 预警的「登记 ⇔ 被接手」全称式实现的红线。本票未能把它收成身份式判据（见 §5）。
  `wizard_quant_api` 整文件 55/58 不变（jq_trans_module 所在文件未退）。`quotation` 153/153 不变。

## 5. 否证 / 更正（对 DIAG 与本票前提）

1. **否证「三点足以达 17/17」**：三点把 @2164 恢复到**正确层级（缩进 28）**，实为**有效进展**（v_c23o 缩进 32 误挂
   → v_all_o 缩进 28 正确，逐字节可证），但**不足以达 17/17**：@2164 体的短路 and-链 + `not is_first_five`
   归属须由区域渲染产出，越出三点范围。
2. **确认 §六.3 成立、§三.3 作废**（见 §0，镜像实测 + 与本 session 记忆表『analyzer role route is inert』一致）。
3. **更正 §一.3 的可守性**：#3 的接收者门（BoolOp-entry 或 `_leading_guard_candidate` True）
   仍是**全称式**「登记⇔接手」，故复现 `create_user_code_iqe` 回归。要既不吞 @2164 又不破
   `create_user_code_iqe`，须再加**身份**区分二者的 pend_key（本票未找到白名单身份判据——
   @2164 pend_key=2208 与 create_user_code_iqe 的 pend_key 在「是否 BoolOp entry / 是否顶层 IfRegion entry」
   上不冲突地都可判 False，无进一步同层身份可分）。
4. 未发现「`[C3]` `:38496` 放宽可救」——按令**未动**；动它即 B122/B123 致命动作，不试。

## 6. 结论与交付

**门禁不可达，patch 归档不落地。** 交付 `D:/Temp/r132b/b132.patch`（= v_all_o vs pristine，
`region_ast_generator.py` before `e9a8f65f6451bcc8…` / after `2ba64dc75f6b1271…`），**仅供证据留存，勿应用**：
它 ① matcher 停 16/17（不达门禁 1），② 破 `trade_info_utils` 37→36（不达门禁 2）。镜像已复原 pristine（`e9a8f65f…`，已校验）。

要点：三点协同修复**确有可测进展**（@2164 由消失 → 正确兄弟层级），但本缺陷的**最后一环是 @2208 区域的
guard/and-链渲染**，越出三点授权范围；分析器角色路线惰性；#3 全称接收者门破哨兵。
建议下一票：(a) 专治 IfRegion@2208 的「IF_THEN 区域把自身单测折进子 or 链」渲染判据（同层身份：真边指向
本区域 merge/块后邻语句而非子链 continue），或 (b) 给 #3 找到能区分 @2164 与 `create_user_code_iqe`
pend_key 的身份判据——须以 `create_user_code_iqe` 不破为门禁，不得用全称登记⇔接手。
