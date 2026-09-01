"""R16 调试：追踪 check_stocks 函数的 assert 模式处理。"""
import sys
import types
import marshal
import dis

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    with open(pyc_path, 'rb') as f:
        f.read(16)
        code = marshal.load(f)
    result = {}
    _collect(code, result, prefix='')
    return result


def _collect(code, result, prefix):
    if not prefix:
        name = '<module>'
    else:
        name = prefix + '.' + code.co_name
    result[name] = code
    for c in code.co_consts:
        if isinstance(c, types.CodeType):
            _collect(c, result, name)


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    code = pyc_codes['<module>.check_stocks']
    print("=== check_stocks 字节码 ===")
    for ins in dis.get_instructions(code):
        print(f"  {ins.offset:4d} {ins.opname:20s} {repr(ins.argval)}")

    print("\n=== 测试 ExpressionReconstructor ===")
    from core.cfg.ast_generator_v2 import ExpressionReconstructor

    # 构造指令列表：LOAD_ASSERTION_ERROR + LOAD_CONST msg + PRECALL 0 + CALL 0 + RAISE_VARARGS 1
    class FakeInstr:
        def __init__(self, opname, argval=None, arg=None, offset=0, starts_line=None):
            self.opname = opname
            self.argval = argval
            self.arg = arg
            self.offset = offset
            self.starts_line = starts_line

    instrs = [
        FakeInstr('LOAD_ASSERTION_ERROR', offset=382),
        FakeInstr('LOAD_CONST', argval='您的输入有误', offset=384),
        FakeInstr('PRECALL', arg=0, offset=386),
        FakeInstr('CALL', arg=0, offset=390),
        FakeInstr('RAISE_VARARGS', arg=1, offset=400),
    ]

    recon = ExpressionReconstructor(code)
    result = recon.reconstruct(instrs)
    print(f"reconstruct result: {result}")


if __name__ == '__main__':
    main()
