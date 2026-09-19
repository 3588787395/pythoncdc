"""R3-C: 与前一 if 同条件的 assert 语句被吸收为 if 的 else 分支。
对照 quote.pyc check_stock:
    if 11 >= len(s) >= 9:
        self.trade_log.error('请输入正确的标的代码')
    assert 11 >= len(s) >= 9, '请输入正确的标的代码'
反编译输出: else: assert ... （链式比较重复求值, 布局重排, orig O40 之后 decomp 多出
JUMP_FORWARD to 346 直达 assert 通过点）。"""


def check_stock(self, s):
    if not isinstance(s, str):
        self.trade_log.error("请使用字符串表示标的代码，例如'600570.SS'")
    assert isinstance(s, str), "请使用字符串表示标的代码，例如'600570.SS'"
    if 11 >= len(s) >= 9:
        self.trade_log.error('请输入正确的标的代码')
    assert 11 >= len(s) >= 9, '请输入正确的标的代码'
    if s.split('.')[1] not in ('SS', 'SZ', 'CCFX', 'XDCE', 'XSGE', 'XZCE', 'XBHS'):
        self.trade_log.error("请输入标的代码以'SS','SZ','CCFX','XDCE','XSGE','XZCE'结尾")
    assert s.split('.')[1] in ('SS', 'SZ', 'CCFX', 'XDCE', 'XSGE', 'XZCE', 'XBHS'), "结尾错误"
