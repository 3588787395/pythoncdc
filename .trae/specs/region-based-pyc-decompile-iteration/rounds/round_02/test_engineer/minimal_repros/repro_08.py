# family: F5 — `with` 块之后紧跟的 bare `return` 被丢弃（改写成直接落到函数尾）
# 预期字节码模式: with 体结束后: LOAD_CONST None x3; CALL(__exit__); POP_TOP; JUMP_FORWARD 到清理块; LOAD_CONST None; RETURN_VALUE
# 实际反编译输出: `return` 语句消失，异常表清理结构随之改变
# 关联 pyc: site-packages/IQEngine/plugins/plugin_system_finance/commission.pyc  load  baseline first_diff idx=43；json_persistance.pyc persist idx=31
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

import os


def load(self, file_path):
    with open(file_path, 'r') as fh:
        self.future_info = fh.read()
    return
