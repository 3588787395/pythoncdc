# Source Generated with Decompyle++ (Python version)
# File: r3_09_nested_if_else_flatten.pyc (Python 3.11)

__doc__ = """R3-K: 嵌套 if 的条件吸收 + else 体提升为无条件语句（语义反转）。
对照 quote.pyc get_merger_data:
    if newSecuCode and newSecuCode in list(all_merger_data['SecuCode']):
        if not return_data.empty: return_data = return_data.append(...)
        else: return_data = all_merger_data[...]
反编译输出: if not (A and B and empty): append; assignment 无条件执行（覆盖 append 结果）。"""
def get_merger_data(self, oldSecuCode=None, newSecuCode=None):
    all_merger_data = data_proxy().get_merger_data_local()
    return_data = pandas.DataFrame()
    if oldSecuCode and oldSecuCode in list(all_merger_data.index):
        return_data = all_merger_data.loc[[oldSecuCode]]
    if newSecuCode and newSecuCode in list(all_merger_data['SecuCode']):
        if not return_data.empty:
            return_data = return_data.append(all_merger_data[all_merger_data['SecuCode'] == newSecuCode])
        else:
            return_data = all_merger_data[all_merger_data['SecuCode'] == newSecuCode]
    if oldSecuCode is None and newSecuCode is None:
        return_data = all_merger_data
    return return_data
