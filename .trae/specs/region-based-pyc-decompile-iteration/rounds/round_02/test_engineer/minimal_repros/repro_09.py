# family: F5 — `if ...: return` + 后续语句被重排成 `if/else`，return 的终止点丢失
# 预期字节码模式: if not exists: LOAD_CONST None; RETURN_VALUE；之后是 with 块；末尾再 LOAD_CONST None; RETURN_VALUE
# 实际反编译输出: 输出变成 `if ...: return None else: with ...`，末尾的 return 丢失
# 关联 pyc: site-packages/IQEngine/plugins/plugin_system_finance/commission.pyc  load（真实代码即 if-not-exists-return + with + return）
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code

import os


def load(self, file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r') as fh:
        self.future_info = fh.read()
    return
