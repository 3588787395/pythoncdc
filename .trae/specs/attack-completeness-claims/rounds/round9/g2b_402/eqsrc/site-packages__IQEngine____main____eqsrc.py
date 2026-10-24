# Source Generated with Decompyle++ (Python version)
# File: __main__.pyc (Python 3.11)

import os
import shutil
import six
from IQEngine.config import parse_config
CONTEXT_SETTINGS = {'default_map': {'run': {}}}
def run(**kwargs):
    config_path = kwargs.pop('config_path', None)
    if config_path is not None:
        config_path = os.path.abspath(config_path)
    from IQEngine import main
    source_code = kwargs.pop('strategy__source_code', None)
    cfg = parse_config(kwargs, config_path=config_path, click_type=False, source_code=source_code)
    source_code = cfg.strategy.source_code
    main.run(cfg, source_code=source_code)
def generate_config(directory):
    default_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.yml')
    target_config_path = os.path.abspath(os.path.join(directory, 'config.yml'))
    shutil.copy(default_config, target_config_path)
    six.print_('Config file has been generated in', target_config_path)
