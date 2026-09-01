"""R20 测试工程师：调试 fill_minute_or_day_blank 反编译失败原因"""
import sys
import dis
import types
import traceback

sys.path.insert(0, '/workspace')

from core.pyc_loader_v2 import load_pyc_file_v2

PYC = '/workspace/quotation.pyc'


def load_pyc_code_objects(pyc_path):
    module = load_pyc_file_v2(pyc_path)
    if not module:
        return {}
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


def main():
    pyc_codes = load_pyc_code_objects(PYC)
    name = 'fill_minute_or_day_blank'
    co = pyc_codes[name]
    print(f"=== {name} ===")

    try:
        from core.cfg.cfg_builder import CFGBuilder

        cfg = CFGBuilder().build(co)
        # 探查cfg属性
        print(f"cfg type: {type(cfg).__name__}")
        print(f"cfg attrs: {[a for a in dir(cfg) if not a.startswith('_')]}")

        # 尝试获取blocks
        blocks = None
        for attr in ['blocks', '_blocks', 'all_blocks', 'get_blocks', 'block_list']:
            if hasattr(cfg, attr):
                v = getattr(cfg, attr)
                if callable(v):
                    try:
                        blocks = v()
                    except Exception:
                        pass
                else:
                    blocks = v
                print(f"blocks via {attr}: type={type(v).__name__}")
                break

        if blocks is None:
            print("No blocks attr found")
            return

        # blocks可能是dict
        if isinstance(blocks, dict):
            print(f"blocks is dict, keys count: {len(blocks)}")
            for k in sorted(blocks.keys())[:30]:
                b = blocks[k]
                print(f"  block {k}: {b}")
        else:
            print(f"blocks type: {type(blocks).__name__}, len={len(blocks) if hasattr(blocks, '__len__') else '?'}")
            try:
                for b in blocks:
                    print(f"  {b}")
                    break
            except Exception as e:
                print(f"iter err: {e}")

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()
