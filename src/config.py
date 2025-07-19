import yaml
from typing import Dict
from pydantic import BaseModel, SecretStr, ValidationError, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Any, Type
import logging

CONFIG_PATH = "config.yaml"


class LoggingConfig(BaseModel):
    level: str = "DEBUG"
    config_file: str = "config.json"

def EnvRequiredField(*, description: str = ""):
    return Field(..., description=description, metadata={"env_required": True})

base_url: str = EnvRequiredField(description="REQUIRED: Set in .env or environment")


# -------------------------- setup custom config classes here

# From YAML
class WalletConfig(BaseSettings):
    label: str
    token: str
    retry: int = 3

# Uses .env
class BrokerConfig(BaseSettings):
    api_key: SecretStr
    api_secret: SecretStr
    base_url: str = Field(..., description="REQUIRED: Set in .env or environment", env_required=True)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
    )

# pydantic v2
class AppConfig(BaseSettings):
    private_key: SecretStr
    log_level: str = "INFO"
    wallet_map: Dict[str, str] = Field(..., validation_alias="WALLET_MAP_JSON") # !Example

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="", 
    )

# -------------------------- add the unified in here

class Settings(BaseModel):
    logging: LoggingConfig
    app: AppConfig
    wallet: WalletConfig
    broker: BrokerConfig
    
    
# TODO: add custom fields/SeceretStr to know if its supposed to be in yaml or in .env
# TODO: add defaults.yaml, that it should read from if no value was found, but only the key (or maybe DEFAULT)
# TODO: change the validation helper functions for this

# TODO: do tests


# -------------------------- dont need to change this method
def get_settings() -> Settings:
    """
    Loads application settings by merging values from config.yaml and environment variables.

    - Attempts to load configuration from CONFIG_PATH (YAML file).
    - Validates that the YAML structure matches the Settings class.
    - For each field in Settings, builds the configuration using both YAML and environment variables,
      with environment variables taking precedence (via Pydantic BaseSettings).
    - Returns a fully constructed Settings object.
    - Logs and raises a ValidationError if configuration is invalid.

    Returns:
        Settings: The fully constructed application settings object.

    Raises:
        ValueError: If the YAML structure does not match the Settings class.
        ValidationError: If the settings data is invalid.
    """
    try:
        with open(CONFIG_PATH, "r") as f:
            yaml_data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logging.warning(f"{CONFIG_PATH} not found, proceeding with env/.env only.")
        yaml_data = {}

    _check_config_keys_match(Settings, yaml_data)
    settings_kwargs = _build_settings_kwargs(Settings, yaml_data)

    try:
        return Settings(**settings_kwargs)
    except ValidationError as e:
        logging.error("Configuration validation error:")
        logging.error(e)
        raise

# -------------------------- Helper functions

def _check_config_keys_match(settings_cls: Type[Any], yaml_data: Dict[str, Any]) -> None:
    """
    Validates that the top-level keys in the provided config.yaml data exactly match the fields
    defined in the given Pydantic settings class.

    Logs and raises a ValueError if there are any missing or extra keys, ensuring that the YAML
    configuration structure stays in sync with the Python settings model.
    If a mismatch is found, logs the expected YAML structure as a template.

    Args:
        settings_cls: The Pydantic settings class whose fields define the expected config structure.
        yaml_data: The dictionary loaded from config.yaml to be validated.

    Raises:
        ValueError: If there are missing or extra keys in the YAML compared to the settings class.
    """
    settings_keys = set(settings_cls.model_fields)
    yaml_keys = set(yaml_data)
    if yaml_keys ^ settings_keys:
        missing = settings_keys - yaml_keys
        extra = yaml_keys - settings_keys
        if missing:
            logging.error(f"Missing keys in config.yaml: {missing}")
        if extra:
            logging.error(f"Extra keys in config.yaml: {extra}")
        # --- Suggest the expected YAML structure if there is a mismatch
        mock_yaml = _generate_mock_yaml(settings_cls)
        logging.error("Expected YAML structure (template):\n" + yaml.safe_dump(mock_yaml, sort_keys=False))
        raise ValueError(
            f"Config structure mismatch: "
            f"{'; '.join([f'Missing keys in config.yaml: {missing}' if missing else '', f'Extra keys in config.yaml: {extra}' if extra else '']).strip('; ')}"
        )


def _build_settings_kwargs(settings_cls: Type[Any], yaml_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Dynamically build a dictionary of keyword arguments for instantiating a settings class.

    For each field in the settings class:
      - If the field is a Pydantic model (BaseModel/BaseSettings), instantiate it using the corresponding section from yaml_data.
        - This allows environment variables and .env to override YAML values (Pydantic's BaseSettings logic).
      - If instantiation fails, fall back to the default constructor and log a warning.
      - If the field is not a Pydantic model, use the YAML value directly.

    Args:
        settings_cls: The Pydantic settings class to instantiate.
        yaml_data: The dictionary loaded from config.yaml.

    Returns:
        dict: Keyword arguments for instantiating the settings class.
    """
    settings_kwargs: Dict[str, Any] = {}
    for field_name, field_info in settings_cls.model_fields.items():
        field_type = field_info.annotation
        yaml_section = yaml_data.get(field_name, {})
        is_pydantic_model = hasattr(field_type, "model_validate")
        if not is_pydantic_model:
            settings_kwargs[field_name] = yaml_section
            continue
        try:
            validated = field_type.model_validate(yaml_section)
            settings_kwargs[field_name] = validated
        except Exception as e:
            logging.warning(
                f"Failed to instantiate {field_type.__name__} from YAML for field '{field_name}': {e}. Using default constructor."
            )
            default_instance = field_type()
            settings_kwargs[field_name] = default_instance
    return settings_kwargs


def _generate_mock_yaml(settings_cls: Type[Any]) -> Dict[str, Any]:
    """
    Recursively generates a dictionary representing the expected YAML structure
    for the given Pydantic settings class, including nested models.

    Returns:
        Dict[str, Any]: A dictionary suitable for dumping as a YAML config template.
    """
    result: Dict[str, Any] = {}
    for field_name, field_info in settings_cls.model_fields.items():
        field_type = field_info.annotation
        default = field_info.default if field_info.default is not None else None
        if hasattr(field_type, "model_fields"):
            nested: Dict[str, Any] = _generate_mock_yaml(field_type)
            result[field_name] = nested
            continue
        value: Any = default if default is not None else f"<{getattr(field_type, '__name__', str(field_type))}>"
        result[field_name] = value
    return result


def _write_mock_yaml(settings_cls: Type[Any], filename: str = "mock_config.yaml") -> None:
    """
    Writes the expected YAML structure for the given settings class to a file.
    """
    structure = _generate_mock_yaml(settings_cls)
    with open(filename, "w") as f:
        yaml.safe_dump(structure, f, sort_keys=False)
    print(f"Mock config written to {filename}")