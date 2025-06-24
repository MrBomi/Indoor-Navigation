import yaml
import os

class Config:
    def __init__(self, path='config/config.yaml'):
        with open(path, 'r') as f:
            self._config = yaml.safe_load(f)

    def get(self, *keys):
        data = self._config
        for key in keys:
            data = data.get(key)
            if data is None:
                raise KeyError(f"Key {'.'.join(keys)} not found in config")
        return data
