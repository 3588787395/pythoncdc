import dis, marshal, types

# Generate a small module exercising subscript assignment shapes, compile to pyc.
src = '''
class Store:
    def set_one(self, d, key_obj, val):
        # container=attr, index=attr (the fly_api shape)
        self.instance_dict[key_obj.__name__] = val
        # simple triple
        d[key_obj] = val
        # container=attr, index=simple
        self.buf[k] = val
        # container=simple, index=attr
        m[key_obj.name] = val
        return d
'''
import py_compile, os
path = r"F:\Downloads\pythoncdc-main\.trae\specs\region-based-pyc-decompile-iteration\rounds\round_04\repair_engineer\repro_subscr_src.py"
with open(path, "w") as f:
    f.write(src)
pyc = path + "c"
if os.path.exists(pyc):
    os.remove(pyc)
py_compile.compile(path, cfile=pyc, dfile=path, doraise=True)
print("compiled", pyc)
