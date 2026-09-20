# Round 12 分析：推导式返回值的宽指令 fall-through 修复

## 结论（一句话）
`core/cfg/comprehension_generator.py` 的 `try_generate_comprehension_assign` 用
`_last_off + 2` 计算 fall-through 后继落点，对带 CACHE 的宽指令（3.11 的 CALL
宽 10 字节）必然失配，导致「推导式值就是 return 值、但 RETURN_VALUE 位于后继块」
的形态被降级为裸 `Expr(comp)` + 伪造 `return None`。修复后官方口径
**349 → 351 ok**（两个 merger_storage 均 100%）。

## 受害文件（官方 partial，各只差 1 函数）
| 文件 | 函数 | 修前 |
|---|---|---|
| IQEngine/data/merger_storage.pyc | MergerStorage.get_merger_date_info | orig=32 decomp=34, true_diffs=22 |
| IQData/data/merger_storage.pyc | 同名副本 | 同上 |

## 根因定位链
1. `single` 对比：first_diff index 12 `orig RETURN_VALUE vs decomp POP_TOP`。
2. 反汇编对照：ORIG try 体 = `MAKE_FUNCTION <dictcomp> ... CALL; RETURN_VALUE`
   （offset 58），DEC = `... CALL; POP_TOP; LOAD_CONST None; RETURN_VALUE`
   （推导式值被丢弃 + 伪造 return None）。
3. 追踪钩子：`try_generate_comprehension_assign` 对 block@8 返回
   `['Expr']`。CFG 实况：**try 体被异常表边界切成两块** —— block@8 末尾是
   CALL(48)，block@58 只有 RETURN_VALUE；block@8 的 successors =
   [(60, 异常边 PUSH_EXC_INFO...), (58, [RETURN_VALUE])]。
4. 代码层：fall-through 判据 `_fall_through_off = _last_off + 2`，而
   48 + 2 = 50 ≠ 58（CALL 带 4 个 CACHE，实际宽 10 字节）→ 平凡 return
   后继匹配失败 → 落入 Expr 兜底（509 行）。

## 修复（识别条件 → 归约方式 → AST 映射）
- **识别条件**：块末指令非跳转（值消费型如 CALL，控制流直落下一块），且
  前向后继中存在「过滤噪声后仅含一条 RETURN_VALUE/RETURN_CONST」的块。
  异常表 handler 边以 PUSH_EXC_INFO 开头、多条指令，天然不满足平凡判据，
  多后继无歧义。
- **归约方式**：该后继即 fall-through 块 → 推导式值即 return 值；后继块
  标记 `generated_blocks/generated_offsets`，由 try 体归约吞并。
- **AST 映射**：`Return(comp_value)`（原则 3：嵌套即抽象节点，不重复发射）。

## 验证
- 形态探针 `test_repros/round12/r12_probe_battery.py`：6/6 PASS
  （dictcomp 带过滤 / listcomp / genexpr / 无 try 平凡函数 4 正例 +
  Round 9 丢弃语句、赋值语句 2 负对照）。
- 两个 merger_storage single：**100.00% / ok**，OK.py 重新生成。
- 全量严格尺子（349 ok 清单）：零回归（见 _r12_strict_after.log）。

## 附带定性（本轮测试工程师，未修）
- `IQCommon/util/cgroup_utils.pyc`：add_process_to_cgroup / set_cgroup_config
  的差异是 **CPython 小版本代码生成差异**（3.11.7 对「try 体尾 if 真臂退出」
  生成独立 return None 块，旧版是 JUMP_FORWARD；形态探针证实 3.11.7 无法
  产出旧布局）—— 反编译器正确，严格尺子误报，与 Round 11 fly_data_source
  同族。但 delete_cgroup_config 是**真缺陷**（else 体过度吸收：
  delete_type=None 时原版删全部、产物不删），留待下轮。
- `IQCommon/util/replace_utils.pyc` decrypt_database_url：复合缺陷
  （or 链 not 成员极性丢失 + `return url` 降级 + 死代码重复），代价高，留待下轮。
