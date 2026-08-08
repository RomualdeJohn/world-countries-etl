from pathlib import Path
import tomllib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"


def _merge(base: dict, override: dict) -> dict:
    """
    Deep-merge two config dictionaries so environment overrides win.

    Nested dicts are merged recursively; all other values are replaced.

    Input:
        base (dict): default config loaded from default.toml.
            Sample: {"database": {"port": 5432}, "logging": {"level": "INFO"}}
        override (dict): environment-specific overrides from e.g. dev.toml.
            Sample: {"database": {"host": "127.0.0.1"}, "logging": {"level": "DEBUG"}}

    Result:
        dict: merged config with override values applied.
            Sample: {"database": {"port": 5432, "host": "127.0.0.1"}, "logging": {"level": "DEBUG"}}
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(env: str) -> dict:
    """
    Load default.toml and merge the environment-specific TOML on top.

    Gives each script one config object for API, database, and logging settings.

    Input:
        env (str): environment name used to pick config/{env}.toml.
            Sample: "dev"

    Result:
        dict: merged application config.
            Sample: {"rest_countries": {"limit": 100}, "database": {"port": 5432}}
    """
    with open(CONFIG_DIR / "default.toml", "rb") as f:
        config = tomllib.load(f)
    env_path = CONFIG_DIR / f"{env}.toml"
    if env_path.exists():
        with open(env_path, "rb") as f:
            config = _merge(config, tomllib.load(f))

    return config
