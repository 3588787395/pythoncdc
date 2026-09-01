# Pattern: for key in attr_list + getattr(obj, key, None) (get_security_info inner loop)
# Function: BasicDataSource.get_security_info
# Expected: for key in obj._repr_attr_list: value = getattr(obj, key, None); d[key] = value
# Actual: same (pyc 100% match, NO-DEFECT control)
def copy_attrs(asset):
    tmp_dict = {}
    for key in asset._repr_attr_list:
        value = getattr(asset, key, None)
        tmp_dict[key] = value
    return tmp_dict
# NO-DEFECT
