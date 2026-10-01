# r1_reg 最小复现：round1 全量验证唯一单元级回退
# PluginRiskCalculation.get_daily_summary（risk_calculation/__init__.pyc 41/43 → 40/43）
#
# 【真身码对象移植】本形态无法用合成源码忠实切片（合成切片触发的都是无关既有
# 缺陷：早退 return else 化 / merge 尾语句双发射），故按预案移植真身码对象：
# 从 site-packages/IQEngine/plugins/plugin_system_risk_calculation/__init__.pyc
# 提取 PluginRiskCalculation.get_daily_summary 方法码对象（marshal 原样搬运、
# 字节逐位相同），用 compile 模板合成「module + class + 单方法」三单元 pyc
# （r1_reg_get_daily_summary.pyc，随本文件提交）。
# 模板须带模块级绑定 `import six` / `RunType = None`：方法体内 LOAD_GLOBAL 名字
# 的模块级在场决定 3.11 编译器对 six.iteritems(...) 发
# LOAD_GLOBAL NULL+six; LOAD_ATTR iteritems 形态；缺绑定则发
# LOAD_GLOBAL six; LOAD_METHOD iteritems 形态，与真身重编译产物错位。
#
# 重新生成：python 本文件（默认写同目录 r1_reg_get_daily_summary.pyc）。
#
# 触发形态（orig pyc get_daily_summary 指令流取证，剔行号，方法内相对偏移）：
#   三元内嵌方法调用实参（summary.update({... 'returns': t if len(...)==0 else ...})）
#   的 TernaryRegion merge 块尾依次承载：
#     ① 数条普通语句（STORE_NAME/STORE_SUBSCR：today=... / date=today / d[k]=...）
#     ② 一条纯表达式语句 self._returns.append(total_return)（CALL+POP_TOP 收尾）
#     ③ 独立 if 测试 self._engine.benchmark_portfolio + POP_JUMP_FORWARD_IF_FALSE
#        （fall-through=顶层 IfRegion entry，跳转目标=该 if 的 merge）
#   R76-A1/A2 MERGEPATH 前导守卫剥离（region_ast_generator.py
#   _try_build_ternary_merge_consumer_expr 内 _detect_leading_guard(region.merge_block)）
#   把 ③ 的条件段误判为「外层守卫」剥离：wrap 记录孤儿化（fall-through 区域
#   3660/3952 被三元自身 R59-B if-upgrade 提前生成，顶层循环 allgen continue
#   跳过记录读取），且尾跳转条件被抽空后升级端把 ② 的调用表达式绑定为 if
#   测试 → 产物 `if self._returns.append(total_return):`，真测试
#   self._engine.benchmark_portfolio 消失（Different bytecode）。
#
# 修复 = MERGEPATH 剥离点加 [R1-REG 守卫]（R59-B 升级消费端让位，同文件
# _try_build_ternary_merge_consumer_expr）：升级端必然消费该尾时让位。
#
# 双向实测（本文件生成物）：
#   守卫禁用（pre-fix 行为）→ get_daily_summary Failure: Different bytecode，
#     产物 52 行 `if self._returns.append(total_return):`；
#   守卫启用（现树）→ success 3/3 100.00%，append 还原为独立语句 +
#     `if self._engine.benchmark_portfolio:` 正常 if。

import marshal
import os
import types

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', '..',
                   'site-packages', 'IQEngine', 'plugins',
                   'plugin_system_risk_calculation', '__init__.pyc')
DST = os.path.join(HERE, 'r1_reg_get_daily_summary.pyc')


def find_class(c):
    for k in c.co_consts:
        if hasattr(k, 'co_code') and k.co_name == 'PluginRiskCalculation':
            return k
    return None


def find_method(cls, name):
    for k in cls.co_consts:
        if hasattr(k, 'co_code') and k.co_name == name:
            return k
    return None


def main():
    with open(SRC, 'rb') as f:
        f.read(16)
        root = marshal.load(f)
    cls_real = find_class(root)
    assert cls_real is not None
    method = find_method(cls_real, 'get_daily_summary')
    assert method is not None

    # 模板：模块级绑定 six/RunType + 单方法类（见文件头说明）
    tpl_src = ("import six\n"
               "RunType = None\n"
               "class PluginRiskCalculation:\n"
               "    def _tpl_method(self):\n"
               "        pass\n")
    tpl_mod = compile(tpl_src, 'r1_reg_get_daily_summary.py', 'exec')
    tpl_cls = next(k for k in tpl_mod.co_consts if hasattr(k, 'co_code'))

    cls_consts = tuple(method if (hasattr(k, 'co_code') and k.co_name == '_tpl_method')
                       else k for k in tpl_cls.co_consts)
    cls_names = tuple('get_daily_summary' if n == '_tpl_method' else n
                      for n in tpl_cls.co_names)
    new_cls_code = types.CodeType(
        tpl_cls.co_argcount, tpl_cls.co_posonlyargcount, tpl_cls.co_kwonlyargcount,
        tpl_cls.co_nlocals, tpl_cls.co_stacksize, tpl_cls.co_flags, tpl_cls.co_code,
        cls_consts, cls_names, tpl_cls.co_varnames,
        'r1_reg_get_daily_summary.py', 'PluginRiskCalculation',
        tpl_cls.co_qualname, 1, b'', tpl_cls.co_exceptiontable,
        tpl_cls.co_freevars, tpl_cls.co_cellvars)

    mod_consts = tuple(new_cls_code if (hasattr(k, 'co_code') and k.co_name == 'PluginRiskCalculation')
                       else k for k in tpl_mod.co_consts)
    new_mod = types.CodeType(
        tpl_mod.co_argcount, tpl_mod.co_posonlyargcount, tpl_mod.co_kwonlyargcount,
        tpl_mod.co_nlocals, tpl_mod.co_stacksize, tpl_mod.co_flags, tpl_mod.co_code,
        mod_consts, tpl_mod.co_names, tpl_mod.co_varnames,
        'r1_reg_get_daily_summary.py', '<module>',
        tpl_mod.co_qualname, 1, b'', tpl_mod.co_exceptiontable,
        tpl_mod.co_freevars, tpl_mod.co_cellvars)

    with open(DST, 'wb') as f:
        f.write(b'\xa7\x0d\x0d\x0a' + b'\x00' * 12)  # 3.11 magic a70d0d0a + 12B 头
        marshal.dump(new_mod, f)
    print('written', DST)


if __name__ == '__main__':
    main()
