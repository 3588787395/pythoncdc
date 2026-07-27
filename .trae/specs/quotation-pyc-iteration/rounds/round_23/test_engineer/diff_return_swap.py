"""分析return语句被丢失的模式：SWAP+POP_EXCEPT+RETURN_VALUE"""
import sys
import dis
import types

sys.path.insert(0, '/workspace')

PYC = '/workspace/quotation.pyc'
SRC = '/tmp/r23_decompiled.py'


def load_pyc_code_objects(pyc_path):
    from core.pyc_loader_v2 import load_pyc_file_v2
    module = load_pyc_file_v2(pyc_path)
    code_obj = module.code.get() if hasattr(module.code, 'get') else module.code
    if hasattr(code_obj, 'to_python_code'):
        code_obj = code_obj.to_python_code()
    result = {}
    def walk(co, prefix=''):
        name = prefix + co.co_name if prefix else co.co_name
        if co.co_name == '<module>' and not prefix:
            name = '<module>'
        result[name] = co
        for const in co.co_consts:
            if isinstance(const, types.CodeType):
                sub_prefix = name + '.' if name != '<module>' else ''
                walk(const, sub_prefix)
    walk(code_obj)
    return result


def find_return_patterns(co, path=''):
    """找出SWAP+POP_EXCEPT+RETURN_VALUE或BUILD_TUPLE+SWAP+RETURN_VALUE模式"""
    instrs = list(dis.get_instructions(co))
    for i, ins in enumerate(instrs):
        # Look for SWAP followed by POP_EXCEPT (in except handler) then RETURN_VALUE
        if ins.opname == 'SWAP' and i + 2 < len(instrs):
            n1 = instrs[i+1]
            n2 = instrs[i+2]
            if n1.opname == 'POP_EXCEPT' and n2.opname == 'RETURN_VALUE':
                # Check what's before SWAP - typically BUILD_TUPLE/BUILD_MAP/BUILD_CONST_KEY_MAP
                if i > 0:
                    prev = instrs[i-1]
                    print(f"  {path}: offset {ins.offset} SWAP+POP_EXCEPT+RETURN_VALUE (prev: {prev.opname} {prev.argval!r})")
    for const in co.co_consts:
        if isinstance(const, types.CodeType):
            sub_path = f"{path}.{const.co_name}" if path else const.co_name
            find_return_patterns(const, sub_path)


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    print("=== PYC: SWAP+POP_EXCEPT+RETURN_VALUE patterns ===")
    for name, co in sorted(pyc_codes.items()):
        find_return_patterns(co, name)


if __name__ == '__main__':
    main()
