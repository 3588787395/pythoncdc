#!/usr/bin/env python3
"""生成最终交付的 minimal_repros/repro_NN.py。"""
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / 'minimal_repros'
OUT.mkdir(parents=True, exist_ok=True)

R = {}

R['01'] = dict(
    fam='F1',
    title='<call>().attr = value — STORE_ATTR 的值被丢弃变成 None',
    expect='LOAD_CONST <value>; PUSH_NULL; LOAD_NAME f; PRECALL; CALL; STORE_ATTR x',
    actual='f().x = None   （值 5 丢失）',
    ref='site-packages/IQEngine/plugins/plugin_system_accounts/api/api_stock.pyc  <module>  baseline first_diff idx=111: LOAD_CONST 10 -> LOAD_CONST None',
    src='''def f():
    return object()


f().x = 5
''')

R['02'] = dict(
    fam='F2',
    title='类体内同名别名赋值 `X = X` 被整体丢弃',
    expect='LOAD_NAME TickBar; STORE_NAME TickBar; LOAD_NAME BarData; STORE_NAME BarData',
    actual='类体里两条别名赋值全部消失，只剩 def __init__',
    ref='site-packages/IQEngine/data/data_proxy.pyc  DataProxy  baseline first_diff idx=5: LOAD_NAME TickBar -> LOAD_CONST <code object __init__>',
    src='''class DataProxy:
    TickBar = TickBar
    BarData = BarData

    def __init__(self):
        self.a = 1
''')

R['03'] = dict(
    fam='F3',
    title='连续多条 `obj.attr = a or b.c` — 第二条起被截断为裸表达式，后续语句全部丢失',
    expect='第 2 条: LOAD_FAST b; JUMP_IF_TRUE_OR_POP; LOAD_FAST env; LOAD_ATTR b; ... STORE_ATTR y',
    actual='第 2 条退化成裸表达式 `b`，`return o` 变成 `return env.b`',
    ref='site-packages/IQEngine/account/trade.pyc  create_trade  baseline first_diff idx=16 (orig 68 -> decomp 19)',
    src='''def f(o, a, b, c, env):
    o.x = a or env.a
    o.y = b or env.b
    o.z = c
    return o
''')

R['04'] = dict(
    fam='F3',
    title='F3 的 2 条极简形式（去掉尾部普通赋值）',
    expect='两条 `or` 短路 STORE_ATTR，各带一次 JUMP_IF_TRUE_OR_POP',
    actual='第 2 条退化成 `b`，`return o` 变成 `return env.b`',
    ref='同上 trade.pyc / create_trade',
    src='''def f(o, a, b, env):
    o.x = a or env.a
    o.y = b or env.b
    return o
''')

R['05'] = dict(
    fam='F4',
    title='`assert` 之前的那条局部赋值被丢弃，变量退化为全局 LOAD_GLOBAL',
    expect='LOAD_FAST trade; LOAD_ATTR amount; STORE_FAST amount; ... assert ...',
    actual='`amount = trade.amount` 整条消失，后面的 amount 变成全局名',
    ref='site-packages/IQEngine/account/order.pyc  fill  baseline first_diff idx=1: LOAD_FAST trade -> LOAD_FAST self',
    src='''def fill(self, trade):
    amount = trade.amount
    assert self.filled_amount + amount <= self.amount
    self.filled_amount += amount
    return [trade]
''')

R['06'] = dict(
    fam='F4',
    title='F4 带 assert 消息的形式（同样丢赋值）',
    expect='STORE_FAST amount 之后 LOAD_ASSERTION_ERROR / RAISE_VARARGS',
    actual='`amount = trade.amount` 消失',
    ref='同上 order.pyc / fill',
    src='''def fill(self, trade):
    amount = trade.amount
    assert self.filled_amount + amount <= self.amount, 'over fill'
    return [trade]
''')

R['07'] = dict(
    fam='F4',
    title='F4 的属性形式：`y = self.compute(x)` 在 assert 前被丢弃',
    expect='LOAD_FAST self; LOAD_METHOD compute; ...; STORE_FAST y',
    actual='`y = self.compute(x)` 消失，assert 里的 y 变成全局名',
    ref='同上 order.pyc / fill（同族）',
    src='''def f(self, x):
    y = self.compute(x)
    assert y is not None
    self.result = y
''')

R['08'] = dict(
    fam='F5',
    title='`with` 块之后紧跟的 bare `return` 被丢弃（改写成直接落到函数尾）',
    expect='with 体结束后: LOAD_CONST None x3; CALL(__exit__); POP_TOP; JUMP_FORWARD 到清理块; LOAD_CONST None; RETURN_VALUE',
    actual='`return` 语句消失，异常表清理结构随之改变',
    ref='site-packages/IQEngine/plugins/plugin_system_finance/commission.pyc  load  baseline first_diff idx=43；json_persistance.pyc persist idx=31',
    src='''import os


def load(self, file_path):
    with open(file_path, 'r') as fh:
        self.future_info = fh.read()
    return
''')

R['09'] = dict(
    fam='F5',
    title='`if ...: return` + 后续语句被重排成 `if/else`，return 的终止点丢失',
    expect='if not exists: LOAD_CONST None; RETURN_VALUE；之后是 with 块；末尾再 LOAD_CONST None; RETURN_VALUE',
    actual='输出变成 `if ...: return None else: with ...`，末尾的 return 丢失',
    ref='site-packages/IQEngine/plugins/plugin_system_finance/commission.pyc  load（真实代码即 if-not-exists-return + with + return）',
    src='''import os


def load(self, file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, 'r') as fh:
        self.future_info = fh.read()
    return
''')

R['10'] = dict(
    fam='F6',
    title='`for ... else:` 的 else 子句被丢弃',
    expect='FOR_ITER 之后紧跟 else 分支（return None），再落到循环后代码',
    actual='else 分支整体消失',
    ref='同族见于 site-packages/fly/common/convert.pyc getchnstr（循环内 continue 形状还原不同，jump=2 true=3）',
    src='''def f(items):
    for i in items:
        if i > 0:
            break
    else:
        return None
    return i
''')

R['11'] = dict(
    fam='F7',
    title='STORE_ATTR 的值为三元 `a if a is not None else f()` 时，该语句及之后全部丢失，末句被提升为 return',
    expect='LOAD_FAST p; POP_JUMP_FORWARD_IF_NONE; LOAD_FAST p; JUMP_FORWARD; PUSH_NULL; LOAD_GLOBAL set; PRECALL; CALL; LOAD_FAST self; STORE_ATTR y',
    actual='三元赋值和后续 `self.z = 0` 一起消失，`self.register_event()` 变成 `return self.register_event()`',
    ref='site-packages/IQEngine/account/base_account.pyc  __init__  baseline first_diff idx=10 (orig 25 -> decomp 14)',
    src='''class A:
    def __init__(self, total_cash, positions, processed_trade=None):
        self._total_cash = total_cash
        self._processed_trade = processed_trade if processed_trade is not None else set()
        self._transaction_cost = 0
        self.register_event()
''')

R['12'] = dict(
    fam='F8',
    title='if 块内的 `import x` 被还原成 `x = None`（IMPORT_NAME 的 level 常量丢失）',
    expect='LOAD_CONST 0; LOAD_CONST None; IMPORT_NAME ptvsd; STORE_FAST ptvsd',
    actual='ptvsd = None（并且重复一次），末尾还多出 return None',
    ref='site-packages/IQEngine/plugins/plugin_system_debug/__init__.pyc  setup  baseline first_diff idx=5 (orig 115 -> decomp 18)',
    src='''def f(engine):
    if engine.debug:
        import ptvsd
        engine.x = ptvsd.y() or 10
        engine.z = 1
''')

R['13'] = dict(
    fam='F8',
    title='F8 的语句重排形式：if 块内 import 与其后的 `or` 赋值被交换顺序，并插入 return None',
    expect='import 在最前，随后 if/嵌套 if，最后 engine.config... = config.timeout or 10',
    actual='赋值被提到 import 之前，紧跟 `return None`，import 及其后语句变成不可达代码',
    ref='site-packages/IQEngine/plugins/plugin_system_debug/__init__.pyc  setup（真实输出即 `... = config.timeout or 10` + `return None` + `import ptvsd`）',
    src='''def setup(self, engine):
    if engine.config.other.enable_debug:
        import ptvsd
        if get_python_version() == '3.11':
            ptvsd.reset()
        engine.config.other.enable_debug = config.timeout or 10
''')

HEADER = """# family: {fam} — {title}
# 预期字节码模式: {expect}
# 实际反编译输出: {actual}
# 关联 pyc: {ref}
# 判定: compile(本文件) -> decompile -> compile，递归比对所有 code object 的 co_code
"""


def main():
    for k in sorted(R):
        d = R[k]
        body = HEADER.format(**d)
        p = OUT / f'repro_{k}.py'
        p.write_text(body + '\n' + d['src'], encoding='utf-8')
        print('wrote', p.name)


if __name__ == '__main__':
    main()
