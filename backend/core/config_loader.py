import yaml
from pathlib import Path

_CONFIG = None

def load_config():
    global _CONFIG
    if _CONFIG is None:
        with open(Path(__file__).parents[1] / "config.yaml") as f:
            _CONFIG = yaml.safe_load(f)
    return _CONFIG
