import sys
sys.path.insert(0, r"F:\Downloads\pythoncdc-main")
from pycdc import decompile_pyc

PATH = r"F:\Downloads\pythoncdc-main\site-packages\IQEngine\plugins\plugin_fly_data\fly_api\base.pyc"
src = decompile_pyc(PATH)
idx = src.find("def get_instance")
print("=== decompiled get_instance ===")
print(src[idx:idx+700])
