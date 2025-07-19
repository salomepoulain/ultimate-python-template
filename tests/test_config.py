from config import get_settings, print_yaml_and_env, Settings
from pydantic import SecretStr
import json
import pytest
import os
import yaml



@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    # List all env vars you want to clear
    for var in list(os.environ.keys()):
        monkeypatch.delenv(var, raising=False)

def test_just_print_output():
    print_yaml_and_env(Settings)


def test_print_yaml_and_env(capsys):
    print_yaml_and_env(Settings)
    captured = capsys.readouterr()
    assert "config.yaml" in captured.out
    assert ".env structure" in captured.out
    assert len(captured.out) > 0


def test_get_settings_all_fields_not_missing():
    settings = get_settings()
    settings_dict = settings.model_dump()
    # Recursively check all fields are not None (for nested models too)
    def check_not_none(d):
        if isinstance(d, dict):
            for k, v in d.items():
                assert v is not None, f"{k} is None"
                check_not_none(v)
        elif isinstance(d, list):
            for item in d:
                check_not_none(item)
    check_not_none(settings_dict)

def test_get_settings_is_not_none():
    settings = get_settings()
    assert settings is not None
    # Optionally print for visual check
    print(settings.model_dump())
    
def test_print_pretty_json():
    settings = get_settings()
    # Dump as dict, but need to convert SecretStrs to string for printing
    def handle_secret(obj):
        if isinstance(obj, SecretStr):
            return str(obj)
        if isinstance(obj, dict):
            return {k: handle_secret(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [handle_secret(v) for v in obj]
        return obj
    pretty = json.dumps(handle_secret(settings.model_dump()), indent=2)
    print(pretty)

@pytest.fixture
def generic_temp_config(tmp_path, monkeypatch):
    """
    Completely generic fixture: generates temp config.yaml and .env from the actual Settings model.
    Returns paths to both files.
    """
    from config import Settings, _generate_yaml_for_model, _generate_env_for_model

    # 1. Auto-generate config dict and env dict
    yaml_dict = _generate_yaml_for_model(Settings, for_docs=False)  # <-- Use for_docs=False for real config!
    env_dict = _generate_env_for_model(Settings)

    # 2. Write them to temp files
    input_config_path = tmp_path / "config.yaml"
    with open(input_config_path, "w") as f:
        yaml.safe_dump(yaml_dict, f, sort_keys=False)

    env_path = tmp_path / ".env"
    with open(env_path, "w") as f:
        for k, v in env_dict.items():
            f.write(f"{k}={v}\n")

    # 3. Monkeypatch the config file paths for your test run
    monkeypatch.setattr("config.INPUT_CONFIG_PATH", str(input_config_path))
    # Overwrite the env_file in model_config for THIS test only
    monkeypatch.setattr("config.Settings.model_config", {
        "env_file": str(env_path),
        "env_nested_delimiter": "__"
    })

    return input_config_path, env_path

def test_settings_loads_with_generic_temp_config(generic_temp_config, capsys):
    from config import get_settings, Settings
    with pytest.raises(Exception):   # Or ValidationError
        get_settings()
    captured = capsys.readouterr()
    assert "Could not load settings!" in captured.out
    assert "config.yaml structure" in captured.out
    assert ".env structure" in captured.out
