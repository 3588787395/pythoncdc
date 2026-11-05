# rr-v5r116 [v116-FOLDRET] 变体矩阵案源
# E1: IPv4Network.__init__ 形——if/elif 臂 + lambda + 折叠对（None/lambda 驻留序）
# E2: 折叠对 + 前置常量（驻留序敏感形）
# C1: 源码 return 形（repro4 同构，行标记存在）
# C2: 源码 bare return 嵌套（repro1 同构）
CASES = {
    'E1_foldret_lambda': '''class C:
    def m(self, p):
        if p == 1:
            self.h = self.i
        elif p == 2:
            self.h = lambda: [p]
''',
    'E2_foldret_consts': '''class D:
    def n(self, p, q):
        if p == "x":
            self.a = q
        elif p == "y":
            self.b = lambda: [q]
        elif p == "z":
            self.c = 7
''',
    'C1_src_ret': '''class W:
    def m(self, state):
        self._log = []
        if isinstance(state, tuple):
            if len(state) == 6:
                self._p, self._q = state[:2]
                return
            if len(state) == 2:
                _, slot = state
                self._x = slot
        self._tail = 1
        return ("tail", getattr(self, "_x", None))
''',
    'C2_src_ret_nested': '''class V:
    def __setstate__(self, state):
        self._a = None
        self._b = None
        if isinstance(state, tuple):
            if len(state) == 6:
                self._p, self._q = state
                return
            if len(state) == 2:
                _, slot_dict = state
                if isinstance(slot_dict, dict):
                    self._x = slot_dict["_x"]
                    self._y = slot_dict["_y"]
                    return
        if isinstance(state, dict):
            version_nt = state.get("_v")
            if version_nt is not None:
                self._z = version_nt
''',
}
