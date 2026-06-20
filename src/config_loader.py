from pathlib import Path
import tomllib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"

def _merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config(env: str) -> dict:
    with open(CONFIG_DIR / "default.toml", "rb") as f:
        config = tomllib.load(f)
    env_path = CONFIG_DIR / f"{env}.toml"
    if env_path.exists():
        with open(env_path, "rb") as f:
            config = _merge(config, tomllib.load(f))

    return config