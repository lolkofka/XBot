import collections
import json
import logging
import os.path
import shutil

config_file = 'data/config.json'
default_config_file = 'assets/default_config.json'


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d


if not os.path.exists('data'):
    os.mkdir('data')

if not os.path.exists('assets'):
    os.mkdir('assets')

config = {
    'xbot': {
        'token': '',
        'owners': [],
        'mongo': '',
        'debug': False,
        'database': ''
    }
}

if os.path.exists(default_config_file):
    with open(default_config_file, 'r', encoding='utf-8') as f:
        update(config, json.load(f))
else:
    with open(default_config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=True, sort_keys=True, indent=4)

if os.path.exists(config_file):
    with open(config_file, 'r', encoding='utf-8') as f:
        user_config = json.load(f)
        config = update(config, user_config)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=True, sort_keys=True, indent=4)
else:
    shutil.copyfile(default_config_file, config_file)
    logging.error('Config was created, restart needed')
    exit(0)
