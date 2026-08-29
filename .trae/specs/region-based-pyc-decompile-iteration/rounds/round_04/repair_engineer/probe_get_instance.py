import dis, marshal

PATH = r"F:\Downloads\pythoncdc-main\site-packages\IQEngine\plugins\plugin_fly_data\fly_api\base.pyc"

with open(PATH, "rb") as f:
    header = f.read(16)
    code = marshal.load(f)

def walk(co, path):
    for c in co.co_consts:
        if hasattr(c, 'co_code'):
            if c.co_name == 'get_instance':
                print("==== get_instance (orig) ====")
                dis.dis(c)
                print("co_names:", c.co_names)
                print("co_consts:", c.co_consts)
                print("co_varnames:", c.co_varnames)
            walk(c, path + "/" + c.co_name)

walk(code, "<module>")
