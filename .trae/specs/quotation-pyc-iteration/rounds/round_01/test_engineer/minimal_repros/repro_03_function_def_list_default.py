"""
Defect 03 — FUNCTION_DEF: 列表默认值丢失导致 `filter_type=` 语法错误
================================================================
触发区域类型：FUNCTION_DEF (函数定义默认参数)
根因初判：
    core/cfg/region_ast_generator.py `_build_function_def`
    (L1100-1122) 的 `defaults` 处理分支只识别 Constant/Tuple/
    List/常量元组，但当默认值通过 `BUILD_LIST + LIST_EXTEND` 在
    模块级动态构造（CPython 对可变默认值 `['ST','HALT',...]` 的
    编译方式）时，defaults 节点被重建为空，code_generator
    `_generate_arguments_dict` (code_generator.py L534-543) 仍
    根据 `len(defaults)` 判定该参数有默认值，于是发射 `name=` 但
    default_code 为空，产生 `filter_type=` 语法错误。

最小字节码模式（Python 3.11，模块级）：
    LOAD_NAME check_arg
    BUILD_LIST 0
    LOAD_CONST ('ST', 'HALT', 'DELISTING')
    LIST_EXTEND 1                              # ['ST','HALT','DELISTING']
    LOAD_CONST None                            # query_date default
    BUILD_TUPLE 2                              # defaults tuple
    LOAD_CONST <code filter_stock_by_status>
    MAKE_FUNCTION defaults
    PRECALL
    CALL
    STORE_NAME filter_stock_by_status

反编译产物（错误，语法错误）：
    @check_arg
    def filter_stock_by_status(stocks, filter_type=, query_date=None):
        return get_quote().filter_stock_by_status(stocks, filter_type, query_date)
期望产物：
    @check_arg
    def filter_stock_by_status(stocks, filter_type=['ST', 'HALT', 'DELISTING'], query_date=None):
        return get_quote().filter_stock_by_status(stocks, filter_type, query_date)

验证：python pycdc.py <this>.pyc  # 生成 filter_type= 缺默认值
"""
def check_arg(f):
    return f

@check_arg
def filter_stock_by_status(stocks, filter_type=['ST', 'HALT', 'DELISTING'], query_date=None):
    return get_quote().filter_stock_by_status(stocks, filter_type, query_date)
