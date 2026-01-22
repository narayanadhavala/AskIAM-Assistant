import yaml
import os
from pathlib import Path

_CONFIG = None

def load_config():
    global _CONFIG
    if _CONFIG is None:
        with open(Path(__file__).parents[1] / "config.yaml") as f:
            _CONFIG = yaml.safe_load(f)
        # Expand environment variables in config
        _CONFIG = _expand_env_vars(_CONFIG)
    return _CONFIG

def _expand_env_vars(obj):
    """Recursively expand ${VAR_NAME} in config values."""
    if isinstance(obj, dict):
        return {k: _expand_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_expand_env_vars(item) for item in obj]
    elif isinstance(obj, str):
        # Replace ${VAR_NAME} with environment variable value
        if obj.startswith("${") and obj.endswith("}"):
            var_name = obj[2:-1]
            return os.getenv(var_name, obj)
        return obj
    else:
        return obj
