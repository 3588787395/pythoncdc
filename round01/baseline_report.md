# 反编译测试报告

- 总计: 50
- 通过: 20 (40.0%)
- 失败: 30 (60.0%)
- 平均匹配率: 0.8710

## 失败文件 (按匹配率升序)

| 匹配率 | 函数匹配 | 文件 |
|--------|---------|------|
| 50.00% | 1/2 | base_api.pyc |
| 50.00% | 1/2 | check_strategy.pyc |
| 50.00% | 14/28 | finance.pyc |
| 55.56% | 35/63 | klinedataOK.cpython-311.pyc |
| 55.56% | 35/63 | klinedata.pyc |
| 55.56% | 35/63 | klinedataOK.pyc |
| 57.14% | 8/14 | api_data.pyc |
| 60.71% | 17/28 | financeOK.cpython-311.pyc |
| 66.67% | 14/21 | local_finance.pyc |
| 75.00% | 3/4 | wrapper.pyc |
| 79.41% | 27/34 | main.pyc |
| 80.00% | 4/5 | gtn_api.pyc |
| 80.00% | 4/5 | i18n.pyc |
| 80.95% | 17/21 | local_financeOK.cpython-311.pyc |
| 81.25% | 13/16 | profiler_func.pyc |
| 85.29% | 29/34 | graphOK.cpython-311.pyc |
| 85.29% | 29/34 | mainOK.cpython-311.pyc |
| 85.71% | 42/49 | arg_checkerOK.cpython-311.pyc |
| 87.88% | 29/33 | instance.pyc |
| 89.80% | 44/49 | arg_checker.pyc |
| 90.91% | 10/11 | generalconf.pyc |
| 91.18% | 31/34 | graph.pyc |
| 92.31% | 24/26 | utilsOK.cpython-311.pyc |
| 93.33% | 28/30 | handlersOK.cpython-311.pyc |
| 93.33% | 28/30 | handlers.pyc |
| 95.45% | 42/44 | const.pyc |
| 95.45% | 21/22 | __init__.pyc |
| 96.97% | 32/33 | instanceOK.cpython-311.pyc |
| 97.06% | 33/34 | exceptionOK.cpython-311.pyc |
| 97.06% | 33/34 | exception.pyc |

## 详细差异 (前5个最差文件)

### base_api.pyc (50.00%)
- 函数 create_dir: diff@41
     [38] ORIG: PRECALL 1 | DECP: PRECALL 1
     [39] ORIG: CALL 1 | DECP: CALL 1
     [40] ORIG: POP_TOP None | DECP: POP_TOP None
  ** [41] ORIG: LOAD_CONST True | DECP: JUMP_FORWARD 368
  ** [42] ORIG: RETURN_VALUE None | DECP: PUSH_EXC_INFO None
  ** [43] ORIG: PUSH_EXC_INFO None | DECP: LOAD_GLOBAL BaseException
  ** [44] ORIG: LOAD_GLOBAL BaseException | DECP: CHECK_EXC_MATCH None
  ** [45] ORIG: CHECK_EXC_MATCH None | DECP: POP_JUMP_FORWARD_IF_FALSE 360

### check_strategy.pyc (50.00%)
- 函数 check_strategy: diff@25
     [22] ORIG: PRECALL 1 | DECP: PRECALL 1
     [23] ORIG: CALL 1 | DECP: CALL 1
     [24] ORIG: POP_TOP None | DECP: POP_TOP None
  ** [25] ORIG: JUMP_FORWARD 1456 | DECP: JUMP_FORWARD 1458
     [26] ORIG: LOAD_GLOBAL open | DECP: LOAD_GLOBAL open
     [27] ORIG: LOAD_FAST current_version_path | DECP: LOAD_FAST current_version_path
     [28] ORIG: LOAD_CONST r | DECP: LOAD_CONST r
     [29] ORIG: LOAD_CONST utf-8 | DECP: LOAD_CONST utf-8

### finance.pyc (50.00%)
- 函数 get_fundamentals_data: diff@101
     [98] ORIG: COMPARE_OP == | DECP: COMPARE_OP ==
     [99] ORIG: POP_JUMP_FORWARD_IF_FALSE 510 | DECP: POP_JUMP_FORWARD_IF_FALSE 510
     [100] ORIG: LOAD_FAST start_year | DECP: LOAD_FAST start_year
  ** [101] ORIG: POP_JUMP_FORWARD_IF_NOT_NONE 456 | DECP: POP_JUMP_FORWARD_IF_NOT_NONE 510
     [102] ORIG: LOAD_FAST end_year | DECP: LOAD_FAST end_year
  ** [103] ORIG: POP_JUMP_FORWARD_IF_NOT_NONE 456 | DECP: POP_JUMP_FORWARD_IF_NOT_NONE 510
     [104] ORIG: LOAD_FAST report_types | DECP: LOAD_FAST report_types
  ** [105] ORIG: POP_JUMP_FORWARD_IF_NOT_NONE 456 | DECP: POP_JUMP_FORWARD_IF_NOT_NONE 510
- 函数 get_financial_and_growth_factors: diff@3
     [0] ORIG: LOAD_FAST date | DECP: LOAD_FAST date
     [1] ORIG: POP_JUMP_FORWARD_IF_TRUE 118 | DECP: POP_JUMP_FORWARD_IF_TRUE 118
     [2] ORIG: LOAD_FAST start_year | DECP: LOAD_FAST start_year
  ** [3] ORIG: POP_JUMP_FORWARD_IF_NOT_NONE 114 | DECP: POP_JUMP_FORWARD_IF_NOT_NONE 118
     [4] ORIG: LOAD_FAST end_year | DECP: LOAD_FAST end_year
     [5] ORIG: POP_JUMP_FORWARD_IF_NOT_NONE 114 | DECP: POP_JUMP_FORWARD_IF_NOT_NONE 114
     [6] ORIG: LOAD_GLOBAL get_fundamentals_qry_date | DECP: LOAD_GLOBAL get_fundamentals_qry_date
     [7] ORIG: LOAD_FAST now | DECP: LOAD_FAST now
- 函数 get_share_change_and_valuation: diff@0
  ** [0] ORIG: LOAD_GLOBAL get_fundamentals_qry_date | DECP: LOAD_CONST None
  ** [1] ORIG: LOAD_FAST now | DECP: RETURN_VALUE None
  ** [2] ORIG: LOAD_FAST date | DECP: <MISSING> 
  ** [3] ORIG: KW_NAMES <unknown> | DECP: <MISSING> 
  ** [4] ORIG: PRECALL 2 | DECP: <MISSING> 
- 函数 get_financial_statements_pit_mode: diff@3
     [0] ORIG: LOAD_FAST date | DECP: LOAD_FAST date
     [1] ORIG: POP_JUMP_FORWARD_IF_TRUE 118 | DECP: POP_JUMP_FORWARD_IF_TRUE 118
     [2] ORIG: LOAD_FAST start_year | DECP: LOAD_FAST start_year
  ** [3] ORIG: POP_JUMP_FORWARD_IF_NOT_NONE 114 | DECP: POP_JUMP_FORWARD_IF_NOT_NONE 118
     [4] ORIG: LOAD_FAST end_year | DECP: LOAD_FAST end_year
     [5] ORIG: POP_JUMP_FORWARD_IF_NOT_NONE 114 | DECP: POP_JUMP_FORWARD_IF_NOT_NONE 114
     [6] ORIG: LOAD_GLOBAL get_fundamentals_qry_date | DECP: LOAD_GLOBAL get_fundamentals_qry_date
     [7] ORIG: LOAD_FAST now | DECP: LOAD_FAST now
- 函数 get_valuation_new: diff@218
     [215] ORIG: LOAD_FAST re_empty_data | DECP: LOAD_FAST re_empty_data
     [216] ORIG: RETURN_VALUE None | DECP: RETURN_VALUE None
     [217] ORIG: LOAD_FAST data_return | DECP: LOAD_FAST data_return
  ** [218] ORIG: STORE_FAST data_return | DECP: LOAD_ATTR empty
  ** [219] ORIG: LOAD_FAST data_return | DECP: POP_JUMP_FORWARD_IF_FALSE 1118
  ** [220] ORIG: LOAD_ATTR empty | DECP: BUILD_LIST 0
  ** [221] ORIG: POP_JUMP_FORWARD_IF_FALSE 1122 | DECP: LOAD_CONST ('secu_code', 'trading_day', 'secu_abbr')
  ** [222] ORIG: BUILD_LIST 0 | DECP: LIST_EXTEND 1

### klinedataOK.cpython-311.pyc (55.56%)
- 函数 get_history_new: diff@0
  ** [0] ORIG: LOAD_GLOBAL type | DECP: LOAD_CONST None
  ** [1] ORIG: LOAD_FAST symbols | DECP: RETURN_VALUE None
  ** [2] ORIG: PRECALL 1 | DECP: <MISSING> 
  ** [3] ORIG: CALL 1 | DECP: <MISSING> 
  ** [4] ORIG: LOAD_GLOBAL str | DECP: <MISSING> 
- 函数 _all_bars_of_cache: diff@26
     [23] ORIG: LOAD_FAST start_date | DECP: LOAD_FAST start_date
     [24] ORIG: LOAD_FAST end_date | DECP: LOAD_FAST end_date
     [25] ORIG: COMPARE_OP > | DECP: COMPARE_OP >
  ** [26] ORIG: POP_JUMP_FORWARD_IF_TRUE 148 | DECP: POP_JUMP_FORWARD_IF_TRUE 160
     [27] ORIG: LOAD_FAST start_date | DECP: LOAD_FAST start_date
     [28] ORIG: LOAD_CONST 20050101 | DECP: LOAD_CONST 20050101
     [29] ORIG: COMPARE_OP < | DECP: COMPARE_OP <
  ** [30] ORIG: POP_JUMP_FORWARD_IF_FALSE 214 | DECP: POP_JUMP_FORWARD_IF_TRUE 160
- 函数 get_kline_by_count_new: diff@0
  ** [0] ORIG: LOAD_GLOBAL OrderedDict | DECP: LOAD_CONST None
  ** [1] ORIG: PRECALL 0 | DECP: RETURN_VALUE None
  ** [2] ORIG: CALL 0 | DECP: <MISSING> 
  ** [3] ORIG: STORE_FAST history_data_dict | DECP: <MISSING> 
  ** [4] ORIG: LOAD_GLOBAL get_benchmark_datetime | DECP: <MISSING> 
- 函数 get_kline_by_count_new.<dictcomp>: 函数缺失
- 函数 get_kline_by_count_new.<dictcomp>.<listcomp>: 函数缺失

### klinedata.pyc (55.56%)
- 函数 get_history_new: diff@0
  ** [0] ORIG: LOAD_GLOBAL type | DECP: LOAD_CONST None
  ** [1] ORIG: LOAD_FAST symbols | DECP: RETURN_VALUE None
  ** [2] ORIG: PRECALL 1 | DECP: <MISSING> 
  ** [3] ORIG: CALL 1 | DECP: <MISSING> 
  ** [4] ORIG: LOAD_GLOBAL str | DECP: <MISSING> 
- 函数 _all_bars_of_cache: diff@26
     [23] ORIG: LOAD_FAST start_date | DECP: LOAD_FAST start_date
     [24] ORIG: LOAD_FAST end_date | DECP: LOAD_FAST end_date
     [25] ORIG: COMPARE_OP > | DECP: COMPARE_OP >
  ** [26] ORIG: POP_JUMP_FORWARD_IF_TRUE 160 | DECP: POP_JUMP_FORWARD_IF_TRUE 148
     [27] ORIG: LOAD_FAST start_date | DECP: LOAD_FAST start_date
     [28] ORIG: LOAD_CONST 20050101 | DECP: LOAD_CONST 20050101
     [29] ORIG: COMPARE_OP < | DECP: COMPARE_OP <
     [30] ORIG: POP_JUMP_FORWARD_IF_FALSE 214 | DECP: POP_JUMP_FORWARD_IF_FALSE 214
- 函数 get_kline_by_count_new: diff@0
  ** [0] ORIG: LOAD_GLOBAL OrderedDict | DECP: LOAD_CONST None
  ** [1] ORIG: PRECALL 0 | DECP: RETURN_VALUE None
  ** [2] ORIG: CALL 0 | DECP: <MISSING> 
  ** [3] ORIG: STORE_FAST history_data_dict | DECP: <MISSING> 
  ** [4] ORIG: LOAD_GLOBAL get_benchmark_datetime | DECP: <MISSING> 
- 函数 get_kline_by_count_new.<dictcomp>: 函数缺失
- 函数 get_kline_by_count_new.<dictcomp>.<listcomp>: 函数缺失
