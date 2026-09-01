# Pattern: nested for loops with dict assignment (assets_to_dict)
# Function: BasicDataSource.assets_to_dict
# Expected: OrderedDict, nested for, dict[key] = value
# Actual: same (pyc 100% match, NO-DEFECT control)
import collections
def assets_to_dict(assets):
    asset_dict = collections.OrderedDict()
    for asset_type_list in assets:
        for asset in asset_type_list:
            asset_dict[asset] = asset
    return asset_dict
# NO-DEFECT
