"""
for-else / while-else 反编译错误 - 完整分析报告
==============================================

项目: pythoncdc (Python 3.11 字节码反编译器)
测试文件: trade_info_utils.pyc, klinedata.pyc
日期: 2026-09-08

================================================================
第一部分: trade_info_utils.pyc 不一致函数分析
================================================================

总函数: 40, 匹配: 27, 不匹配: 13 (67.50%)

不一致函数名称及具体字节码差异:
-----------------------------------------

1. get_trade_list (orig=339, decomp=341, jump_diffs=9, true_diffs=263)
   - 原始: for-else at FOR_ITER 412 -> 484, JUMP_FORWARD 484->594 (else块存在)
   - 原始: for-else at FOR_ITER 1606 -> 1668, JUMP_FORWARD 1668->... (else块存在)
   - 反编译: 第一个for-else保留(416->488), 第二个for-else保留(1508->1570)
   - 差异: for循环主体内break被替换为continue, 导致else块行为错误
   - 具体位置: 偏移74处 JUMP_FORWARD(594) vs LOAD_GLOBAL(os) — 跳转目标错误

2. get_trade_status (orig=155, decomp=157, jump_diffs=5, true_diffs=20)
   - 原始: for-else at FOR_ITER 456 -> 598, JUMP_FORWARD 598->810
   - 反编译: for-else保留 FOR_ITER 456->598, JUMP_FORWARD 600->830
   - 差异: JUMP_FORWARD目标偏移错误(810 vs 830), +20偏移
   - 具体位置: 偏移137处 JUMP_FORWARD(890) vs LOAD_FAST(return_trade_info)

3. get_trade_unit_info (orig=236, decomp=212, jump_diffs=9, true_diffs=45)
   - 原始: for-else at FOR_ITER 410->518, JUMP_FORWARD 518->632
   - 原始: for-else at FOR_ITER 908->1186, JUMP_FORWARD 1186->1296
   - 反编译: 第一个for-else保留(410->518, JUMP_FORWARD 518->632)
   - 反编译: 第二个for-else丢失! FOR_ITER 904->1182, 无JUMP_FORWARD
   - 差异: 第二个for-else的else块被合并到try块内的无条件代码
   - 具体位置: 偏移191处 PUSH_EXC_INFO vs LOAD_FAST(fp) — else块与except混淆

4. get_user_info (orig=94, decomp=58, jump_diffs=3, true_diffs=52)
   - 原始: for-else at FOR_ITER 186->270, JUMP_FORWARD 270->358
   - 反编译: 无for-else! FOR_ITER 184->276, 无JUMP_FORWARD
   - 差异: else块完全丢失, 原始else块内代码(fp.close())变成无条件执行
   - 具体位置: 偏移40处 SWAP(2) vs POP_TOP — return优化与else边界混淆

5. kill_trade_process (orig=573, decomp=564, jump_diffs=6, true_diffs=287)
   - 原始: for循环(无else) at FOR_ITER 1540->2462
   - 原始: while-else 循环在偏移2948区域 (JUMP_FORWARD 3054->3128)
   - 反编译: while-else保留但结构正确
   - 差异: 主要是for循环体内的break被替换为continue
   - 具体位置: 偏移138处 LOAD_GLOBAL(os) vs LOAD_GLOBAL(app_log) — 语句顺序错误

6. check_and_update_trade (orig=218, decomp=228, jump_diffs=3, true_diffs=186)
   - 包含嵌套for循环和try-except结构
   - 具体位置: 偏移36处 LOAD_FAST(csv_reader) vs LOAD_GLOBAL(FileIO)

7. create_user_code_iqe (orig=834, decomp=833, jump_diffs=2, true_diffs=273)
   - 包含POP_JUMP_FORWARD_IF_NONE vs POP_JUMP_FORWARD_IF_TRUE条件反转
   - 具体位置: 偏移528处条件跳转操作码错误

8. get_last_stat (orig=664, decomp=526, jump_diffs=1, true_diffs=182)
   - 包含多个for循环
   - 具体位置: 偏移480处变量名错误(result_data vs item)

9. add_trade (orig=129, decomp=56, jump_diffs=0, true_diffs=102)
   - 大量指令缺失(decomp只有56条 vs orig 129条)
   - 具体位置: 偏移26处LOAD_GLOBAL参数错误(datetime vs TradeOperationLogger)

10. query_strategy_id (orig=99, decomp=98, jump_diffs=2, true_diffs=5)
    - 差异极小,仅2个跳转偏移不同
    - 具体位置: 偏移94处JUMP_FORWARD vs RERAISE

11-13. trade_operation, get_trade_strategy等
    - 类似的break->continue替换和else块丢失问题

================================================================
第二部分: klinedata.pyc 不一致函数分析
================================================================

总函数: 45, 匹配: 37, 不匹配: 8 (82.22%)

1. get_history_common (orig=481, decomp=485, jump_diffs=9, true_diffs=325)
   - 原始: for-else at FOR_ITER 818->920, JUMP_FORWARD 920->1118(跳到else块后)
   - 反编译: 无for-else! FOR_ITER 824->926, 无JUMP_FORWARD
   - 差异: else块完全丢失, else体内代码无条件执行
   - 原始else: if 'datetime' not in fields: fields = ['datetime'] + fields
   - 反编译: fields = ['datetime'] + fields (无条件执行, 逻辑错误)

2. get_history_new (orig=322, decomp=321, jump_diffs=3, true_diffs=37)
   - 原始: for-else at FOR_ITER 1394->1548, JUMP_FORWARD 1548->1678
   - 反编译: for-else保留但JUMP_FORWARD目标错误: 1548->1554 (应该是1678)
   - 差异: else块被截断, 只有2字节跳转(应64字节)
   - 导致: else块体+后续代码被合并, 多出return语句

3. get_multiminute_his_data (orig=479, decomp=478, jump_diffs=10, true_diffs=134)
   - 原始: for-else at FOR_ITER 1470->2708, JUMP_FORWARD 2708->2758
   - 反编译: 无for-else! FOR_ITER 1470->2710, 无JUMP_FORWARD
   - 差异: else块完全丢失
   - 原始else: his_data_dict = get_kline_by_count_new(...)
   - 反编译: his_data_dict = get_kline_by_count_new(...) 无条件执行

4. get_price_common (orig=537, decomp=539, jump_diffs=42, true_diffs=238)
   - 原始: for-else at FOR_ITER 1548->1624, JUMP_FORWARD 1644->1798
   - 反编译: 无for-else! FOR_ITER 1558->1634, 无JUMP_FORWARD
   - 差异: 内层for-else丢失

5. get_all_real_daily_kline (orig=188, decomp=187, jump_diffs=4, true_diffs=27)
   - 原始: for(无else) at FOR_ITER 88->1044
   - 反编译: for(无else) at FOR_ITER 88->1042
   - 差异: JUMP_FORWARD vs JUMP_BACKWARD偏移计算错误

6. kline_datetime_list (orig=389, decomp=388, jump_diffs=8, true_diffs=229)
   - POP_JUMP_FORWARD_IF_TRUE vs POP_JUMP_FORWARD_IF_FALSE 条件反转
   - 偏移150处操作码类型错误

7-8. get_history_date_and_count_ifalse, get_kline_by_count_new
    - 类似的跳转偏移和条件判断错误

================================================================
第三部分: for-else 识别错误分类
================================================================

类别A: break 被替换为 continue (最常见, 最严重)
-------------------------------------------------
触发条件: for-else循环中, break前面有至少一条非空语句
原始字节码: <statement>; POP_TOP; JUMP_FORWARD (break)
反编译字节码: <statement>; JUMP_BACKWARD (continue)
影响: else块永远执行, 循环不会提前退出

受影响函数:
  - get_trade_list (多个break点)
  - kill_trade_process (for循环内break)
  - check_and_update_trade (for循环内break)
  - 所有包含"赋值/method调用 + break"的for-else

确认的最小复现 (7/12触发):
  repro1: 赋值 + break          → break丢失
  repro2: 方法调用 + break      → break丢失
  repro3: 多赋值 + break        → break丢失
  repro4: 嵌套if中break         → break丢失
  repro5: 多个break点           → 部分break丢失
  repro7: try-except内break     → break丢失
  repro9: 嵌套for-else内break   → break丢失

根因: 反编译器将POP_TOP(迭代器清理)归属于前一条语句,
      导致无法识别POP_TOP+JUMP_FORWARD=break模式

类别B: else 块完全丢失
-----------------------
触发条件: for-else中用return退出(非break), 或for-else在try-except内
原始字节码: FOR_ITER -> target; JUMP_BACKWARD; JUMP_FORWARD (else)
反编译字节码: FOR_ITER -> target; JUMP_BACKWARD; <无JUMP_FORWARD>
影响: else体内代码变成无条件执行

受影响函数:
  - get_user_info (return退出, else丢失)
  - get_trade_unit_info (第二个for-else在try内, else丢失)
  - get_history_common (for-else在if块内, else丢失)
  - get_multiminute_his_data (for-else, else丢失)
  - get_price_common (内层for-else丢失)

类别C: JUMP_FORWARD 目标偏移错误
---------------------------------
触发条件: for-else后有复杂控制流
原始: JUMP_FORWARD target = N
反编译: JUMP_FORWARD target = M (M << N)

受影响函数:
  - get_trade_status (JUMP_FORWARD 810 vs 830)
  - get_history_new (JUMP_FORWARD 1678 vs 1554, 偏差124字节!)
  - get_all_real_daily_kline (JUMP_FORWARD偏移计算错误)

类别D: 条件跳转操作码反转
--------------------------
触发条件: 复杂条件表达式的短路求值优化
原始: POP_JUMP_FORWARD_IF_TRUE
反编译: POP_JUMP_FORWARD_IF_FALSE

受影响函数:
  - kline_datetime_list (偏移150处)
  - create_user_code_iqe (POP_JUMP_FORWARD_IF_NONE vs IF_TRUE)

类别E: 多余的 return / continue 语句
--------------------------------------
触发条件: else块丢失后, 反编译器插入return/continue来保证控制流合法
原始: 正常顺序执行到函数末尾
反编译: else块后插入多余的return

受影响函数:
  - repro10, repro11, repro12 (多余return)
  - get_history_new (return截断后续代码)

================================================================
第四部分: 根因分析
================================================================

核心问题: Python 3.11 for循环break的字节码模式识别

Python 3.11 中, for循环的break生成:
  1. POP_TOP  — 弹出迭代器栈值(清理FOR_ITER压入的值)
  2. JUMP_FORWARD — 跳过else块到循环后代码

而continue生成:
  1. JUMP_BACKWARD — 直接跳回FOR_ITER

反编译器的错误逻辑:
  1. 遇到POP_TOP时, 认为它是前一条语句的"副作用"(如STORE_FAST的返回值)
  2. 将POP_TOP"消耗"掉, 不再视为break的一部分
  3. 然后遇到JUMP_FORWARD, 因为没有POP_TOP前缀, 不识别为break
  4. 错误地生成JUMP_BACKWARD(continue)代替

关键区别:
  - bare break (if: break) → POP_TOP紧跟COMPARE_OP分支, 反编译器正确识别
  - 语句+break (if: x=1; break) → POP_TOP前面有STORE_FAST, 反编译器误归属

修复建议:
  1. 在for循环break识别中, POP_TOP不应归属于前一条语句
  2. 识别模式应为: <任意语句>* + POP_TOP + JUMP_FORWARD(past else) = break
  3. while循环不受影响(无迭代器POP_TOP), 可作为参照

================================================================
第五部分: 10+ 最小复现实例
================================================================

见同目录下:
  repro_forelse_16_break_to_continue.py  (确认触发)
  repro_forelse_19_multiple_breaks.py    (确认触发)
  repro_forelse_10_break_nested.py       (确认触发)
  repro_forelse_analysis.py              (综合, 7/12触发)

以及:
  repro_forelse_01~15.py                 (各种模式)
  repro_whilelse_08~21.py                (while-else模式)
"""
