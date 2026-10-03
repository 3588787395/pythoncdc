# Round 7 修复工程师报告（FIX.md）

## 批次一（修复工程师一；子代理三次基础设施故障后由主代理接管完成）

### 已封闭

#### R7-O1（机械修复）——await 链头守卫短路恢复
`region_ast_generator.py` await 协议链头资格处恢复 `if p is None: return None` 短路（置于 `_is_setup` 守卫之后、`_resume_of_poll(p)` 之前），p=None 不再触达 `_resume_of_poll`；docstring [C2] 同步为「守卫拒绝非 GET_AWAITABLE 链头；poll 缺失返回 None」双职责表述。

#### R7-O2（遗留插桩清除）
`region_analyzer.py` a6666b92 代遗留 `_R23N20_DEBUG` env 门控插桩 7 处（含 `start_offset == 342` 魔数探针）整体清除，纯减法零行为触碰。`grep -rn "_R23N20_DEBUG|R23N21_DEBUG" core/` = 0。

#### B45（P0，2/2 封闭）——while/if 复合条件外提变形
前位修复工程师落 [`_detect_while_condition_nested_and_or_chain` / `_b45_rebuild_boolop_chain_slice` / `_build_boolop_skipedge_grouped`]（括号化 `while A and (B or C)` 嵌套链检测 + 链切片扁平 or_groups 重建 + skip 边分段），本批实测确认封闭：`r7_14 h_while_composite`、`r7_12 b_nest_deep_mixed` 双双 MATCH，r7_13 7/7、r7_09 7/7 守卫保持。

#### B42（P0，6/9 封闭）——三元操作数外围表达式结构蒸发
既有 B42 架构（`_b42_split_cond_prefix` + `_b42_rebuild_chain_value_stream` 分段值流重建）修复三处结构缺陷后生效：
1. **条件前缀锚定**（`_b42_split_cond_prefix`）：锚点从块尾指令改为**块内首个条件跳转**——合并真臂续块布局中 POP_JUMP 位于块中，锚定块尾 JUMP_FORWARD 会把真臂值误并反扫窗（r7_04 实证）。[C1] 只读块指令与操作码栈效应；[C2] 无锚/前缀含 STORE 返回 None 回退；[C3] 无状态无副作用。
2. **段收集含最内层条件前缀**：`ternary_chain[1:-1]` → `[1:]`。值流段数必须 = len(elts)+1（N 个 cond 前缀 + 1 个 merge 消费段），旧切片漏最内层前缀致栈序错乱必败（`xs[t1]+ys[t2]` 内层前缀=[BINARY_SUBSCR,LOAD ys] 实证）。
3. **后向链扩展 + 全链块标记**：生成序自底向上（内层先于外层），触发重建的常是拥有终结 merge 块的内层区域——沿 `merge_block==chain[0].entry` 后向收集前辈三元（visited 防环）；重建成功后标记**全链**块 generated（每块唯一归属由本语句承载，防内层重复发射裸 Expr/Return）。
4. **钩子放行 return 上下文 + 单链受限接管**：`merge_ctx in (None, 'return')`（`return (aT)==x` 的 COMPARE_OP 蒸发形态）；单链（len=1）仅在 merge 消费段含 {COMPARE_OP, IS_OP, CONTAINS_OP, BINARY_SUBSCR, BINARY_SLICE} 时接管，BINARY_OP/CALL 等其余消费形态交既有绿路径（Pattern A/call 装配）零劫持；新增「全空段守卫」（S0..SN 全空 = 纯裸三元 → None 回退，n7_01 5/5 行为逐位不变）。

B42 封闭 6 单元：`r7_02 t_dict_both_ternary / t_list_element / t_nested_container`（8/8 文件转 success）、`r7_01 t_subscript_index_ternary`（8/9）、`r7_04 t_compare_both_sides`（6/7）、`r7_03 t_unpack_ternary`（前位修复）。
B42 残留 3 单元（如实登记，交批次二/后续）：`r7_01 t_arg_multi_mixed`（CALL 实参段，内层早返回路径在 B42 钩子之前发射）、`r7_04 t_compare_lhs_only`（同上单链 return 形态）、`r7_05 t_listcomp_ternary_filter.<listcomp>`（推导式子码对象生成路径不同源）。

### 自测读数（终局树实测）
| 项 | 读数 |
|---|---|
| BOM | `efbb bf` ✓ |
| `_R23N20_DEBUG`/`R23N21_DEBUG` grep | 0 ✓ |
| ast.parse + import | 通过 ✓ |
| r7 攻击面 16 文件 | **104/128**（评审基线 96，+8：B45 2 + B42 6），负对照 n7_01/n7_02 各 5/5 保持 |
| round6 全量 16 文件 | **115/115**，16 success ✓ |
| rv6 探针 | **18/29** 持平（B37–B41 无变差）✓ |
| 六哨兵 | tools 6/6、trade_schedule 6/6、mq_connector 13/13、strategy 2/2、scheduler 52/52、trade_info_utils 36/41（失败 5 名单=基线）✓ |
| option_account | **35/35** ✓ |

### 批次边界声明
- 本批改动面 = 2 个 core 文件 + 本 FIX.md + rounds/round7/ 报告 json；根目录诊断草稿（_r7fix_*/_r7diag*）清理
- 未认领（交批次二）：B46（6 单元）/B43（3）/B44（3）/B47（3）/B48（3）/B49（1）/B50（1）/B51（1）+ B42 残留 3 单元
- 判据面：全部为块指令操作码形态/栈效应/区域归属/合并边身份等同层结构事实；零名字白名单、零偏移魔数、零跨层回溯、零新 self 跨方法状态
