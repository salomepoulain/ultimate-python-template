from pydantic_settings import BaseSettings, SettingsConfigDict, YamlConfigSettingsSource
from pydantic import BaseModel, SecretStr, Field
from pydantic_core import PydanticUndefined
from pydantic.fields import FieldInfo
from typing import Literal
import collections.abc
from typing import (
    get_origin, get_args, Dict, List, Any, Type, Union, Tuple, Optional
)
from enum import Enum
import datetime
import toml

INPUT_CONFIG_PATH = "config.yaml"

"""
This module uses Pydantic to define and manage all application settings in a single `Settings` class.

- You can add your own configuration structure by defining new Pydantic models in this file.
- All non-secret input settings are expected to be provided in the YAML file at `INPUT_CONFIG_PATH`.
- All secrets (fields of type `SecretStr` or similar) should be provided via the `.env` file or environment variables, not in YAML.
- If the config or .env are not set up correctly, the expected structure for both will be printed to help you fix the issue.
- You can specify default values and descriptions for each setting using Pydantic's `Field`.

This approach ensures a clear, validated, and maintainable configuration for your project.
"""


class ProgramConfig(BaseModel):
    
    output_folder_choice: str = Field(
        default="DATE",
        description=(
            "Custom output folder. Use 'DATE' for fDD-MM-YYYY__HH-MM-SS."
        )
    )

    # def get_output_folder(self) -> str:
    #     """
    #     Returns the output folder, replacing 'DATE' with a timestamp if present.
    #     The format is 'outputs/fDD-MM-YYYY__HH-MM-SS'.
    #     """
    #     if self.output_folder == "DATE":
    #         now = datetime.datetime.now()
    #         return f"outputs/f{now.strftime('%d-%m-%Y__%H-%M-%S')}"
    #     return self.output_folder

    _resolved_output_folder: Optional[str] = None
    
    @property
    def output_folder(self) -> str:
        if self._resolved_output_folder is not None:
            return self._resolved_output_folder
        if self.output_folder_choice == "DATE":
            now = datetime.datetime.now()
            self._resolved_output_folder = f"{now.strftime('%d-%m-%Y__%H-%M_%S')}"
        else:
            self._resolved_output_folder = self.output_folder_choice
        return self._resolved_output_folder
    
    @property
    def dir_tree(self) -> Any:
        """
        Loads the directory tree from pyproject.toml and replaces '{output_folder}' with the actual output folder.
        """
        config = toml.load("pyproject.toml")
        tree = config["tool"]["myproject"]["dirs"]["tree"]

        def replace_placeholders(obj):
            if isinstance(obj, str):
                return obj.replace("{output_folder}", self.output_folder)
            elif isinstance(obj, dict):
                return {k: replace_placeholders(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_placeholders(v) for v in obj]
            return obj

        return replace_placeholders(tree)

class LoggerConfig(BaseModel):
    """
    Logging configuration.

    level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    config_file: Path to the logging configuration file.
    """
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description=(
            "Logging level. "
            "One of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
        ),
    )
    config_file: str = Field(
        default="config.json",
        description="Path to the logging configuration file."
    )

# * create your own types starting here ---------------------------

class TestConfig(BaseModel):
    hi: str = "doei"

class WalletConfig(BaseModel):
    LABEL: SecretStr    # From .env only!
    
    token: str = Field(
        default="hoi",
        description="The token for the wallet. Default is 'hoi'.",
        title="Wallet Token",
        min_length=3,
        max_length=64,
        pattern=r"^[a-zA-Z0-9]+$",
        examples=["mytoken123"],
        alias="wallet_token",
        deprecated=False,
    )
    
    retry: int          = 3299
    test: TestConfig

class BrokerConfig(BaseModel):
    API_KEY: SecretStr  # From .env only!
    API_SECRET: SecretStr  # From .env only!
    base_url: str
    wallet_map: Dict[str, str] = Field(..., validation_alias="wallet_map")


# * create your own types starting here ---------------------------

class Settings(BaseSettings):
    """
    The main application settings class.

    This class aggregates all configuration sections for the application.
    You can add or remove config sections (as Pydantic models) as needed for your project.

    Example fields:
        - program_config: General program behavior settings.
        - logger_config: Logging configuration.
        - wallet_config: Wallet-related settings (example, replace as needed).
        - broker_config: Broker/API-related settings (example, replace as needed).

    A `Settings` instance represents the **fully validated, merged configuration** for your application,
    combining values from config.yaml (for non-secret fields) and .env/environment variables (for secrets).

    The class uses Pydantic's BaseSettings to:
    - Load non-secret fields from YAML (via YamlConfigSettingsSource).
    - Load secret fields (e.g., SecretStr) from .env or environment variables.
    - Validate all fields and provide helpful error messages if configuration is missing or invalid.

    You can access all config sections and values as attributes on the `Settings` instance.
    """

    program_config: ProgramConfig
    logger_config: LoggerConfig
    # Add your own config sections below as needed:
    wallet_config: WalletConfig     # * Example config section (replace or remove as needed)
    broker_config: BrokerConfig     # * Example config section (replace or remove as needed)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__"  # Enables APP_CONFIG__PRIVATE_KEY style env vars
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type,
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple:
        """
        Customizes the order of config sources for loading settings.

        Loads config in this order:
        1. YAML file (config.yaml)
        2. Environment variables
        3. .env file
        4. Secret files
        5. Direct init values

        Args:
            settings_cls: The settings class.
            init_settings: Pydantic's init settings source.
            env_settings: Pydantic's environment settings source.
            dotenv_settings: Pydantic's dotenv settings source.
            file_secret_settings: Pydantic's file secret settings source.

        Returns:
            tuple: The ordered sources for loading settings.
        """
        return (
            YamlConfigSettingsSource(settings_cls, yaml_file=INPUT_CONFIG_PATH),
            env_settings,
            dotenv_settings,
            file_secret_settings,
            init_settings,
        )
        
# Entrypoint and main function
def get_settings() -> Settings:
    """
    Loads and returns the application settings using Pydantic's Settings class.

    Returns:
        Settings: The fully constructed application settings object.

    Raises:
        Exception: If loading or validation fails, prints a helpful error message,
                   shows the expected config.yaml and .env structure, and re-raises the exception.
    """
    try: 
        return Settings()  # type: ignore
    except Exception as e:
        print("\n[ERROR] Could not load settings! Please check your config.yaml and .env files.")
        print("Make sure your .yaml and .env are structured like this:\n")
        print_yaml_and_env(Settings)
        print("\n[Exception details]:")
        print(e)
        raise

# ------ helper functions

def _is_secret_field(field: FieldInfo) -> bool:
    """
    Determines if a Pydantic model field is a secret field (SecretStr or similar).

    Handles:
    - Direct SecretStr fields.
    - Optional[SecretStr], Union[SecretStr, ...], or Annotated[SecretStr, ...].

    Args:
        field: The Pydantic model field to check.

    Returns:
        bool: True if the field is a SecretStr (or compatible), False otherwise.
    """
    try:
        typ = field.annotation
    except AttributeError:
        return False
    # Handles direct SecretStr
    if typ is SecretStr:
        return True
    # Handles Optional[SecretStr], Annotated[SecretStr], etc
    if hasattr(typ, "__origin__"):
        # e.g. Union[SecretStr, None], Annotated[SecretStr, ...]
        args = getattr(typ, "__args__", ())
        return any(t is SecretStr for t in args)
    return False


def _sample_value_for_type(tp: Any) -> Any:
    """
    Recursively return a 'sample' value for a given type annotation.

    Handles:
    - Optionals and Unions: picks the first non-None type.
    - Annotated: uses the first type argument.
    - Dict/Mapping: returns a dict with sample key/value.
    - List/Sequence: returns a list with a sample item.
    - str, int, float, bool: returns a sample value.
    - Enum: returns the first value or a placeholder.
    - Nested BaseModel: recurses to generate a sample dict.
    - Fallback: returns a string placeholder with the type name.

    Args:
        tp: The type annotation to generate a sample value for.

    Returns:
        Any: A sample value matching the type annotation.
    """
    origin = get_origin(tp)
    args = get_args(tp)

    # Handle Optionals and Unions
    if origin is Union:
        non_none = [a for a in args if a is not type(None)]
        return _sample_value_for_type(non_none[0]) if non_none else None

    # Handle Annotated
    if origin is not None and hasattr(origin, "__origin__") and hasattr(origin, "__args__"):
        return _sample_value_for_type(args[0])

    # Handle Dict/Mapping
    if origin in (dict, Dict, collections.abc.Mapping):
        key_type, val_type = args or (str, str)
        if key_type is str and val_type is str:
            return '{"str": "str", "str": "str"}'
        return {str(_sample_value_for_type(key_type)): _sample_value_for_type(val_type)}

    # Handle List/Sequence
    if origin in (list, List, collections.abc.Sequence):
        item_type = args[0] if args else str
        return [_sample_value_for_type(item_type)]

    # Handle basic types
    if tp is str:
        return "<str>"
    if tp is int:
        return 0
    if tp is float:
        return 0.0
    if tp is bool:
        return False

    # Handle Enums
    if isinstance(tp, type) and issubclass(tp, Enum):
        return list(tp)[0].value if len(tp) else "<enum>"

    # Handle nested BaseModel
    if isinstance(tp, type) and issubclass(tp, BaseModel):
        return _generate_yaml_for_model(tp)

    # Fallback: return a string placeholder with the type name
    type_name = getattr(tp, "__name__", str(tp))
    return f"<{type_name}>"


def _generate_yaml_for_model(model: Type[BaseModel], for_docs: bool = True) -> Dict[str, Any]:
    """
    Generate a dictionary representing the expected YAML structure for a given Pydantic model.

    Args:
        model: The Pydantic BaseModel class to inspect.
        for_docs: If True, include (value, comment) tuples for documentation; if False, include only values for real config.

    Returns:
        Dict[str, Any]: A dictionary mapping field names to either (value, comment) tuples (for docs)
                        or just values (for real config).

    - Secret fields (e.g., SecretStr) are skipped.
    - Field descriptions are included as comments if for_docs is True.
    - Nested BaseModel fields are recursed.
    """
    result: Dict[str, Any] = {}
    for name, field in model.model_fields.items():
        if _is_secret_field(field):
            continue
        field_type = field.annotation
        comment = getattr(field, "description", None)
        if field.default is not PydanticUndefined:
            value = field.default
        else:
            value = _sample_value_for_type(field_type)
        result[name] = (value, comment) if for_docs else value
    return result


def _gather_all_keys_values(
    data: Dict[str, Any], indent: int = 0, result: Optional[List[Tuple[int, str, Any, Optional[str]]]] = None
) -> List[Tuple[int, str, Any, Optional[str]]]:
    """
    Recursively gather all keys and values, with indent, for global alignment.

    Args:
        data: The dictionary to process.
        indent: The current indentation level.
        result: The list to append results to (used for recursion).

    Returns:
        List of tuples: (indent, key, value, comment)
    """
    if result is None:
        result = []
    for key, val in data.items():
        value, comment = val if isinstance(val, tuple) else (val, None)
        result.append((indent, key, value, comment))
        if isinstance(value, dict):
            _gather_all_keys_values(value, indent + 1, result)
    return result


def _gather_comment_rows(
    data: Dict[str, Any], indent: int = 0, result: Optional[List[Tuple[int, str, str, str]]] = None
) -> List[Tuple[int, str, str, str]]:
    """
    Gather rows (indent, key, value, comment) for lines with comments.

    Args:
        data: The dictionary to process.
        indent: The current indentation level.
        result: The list to append results to (used for recursion).

    Returns:
        List of tuples: (indent, key_str, value, comment) for lines with comments.
    """
    if result is None:
        result = []
    for key, val in data.items():
        value, comment = val if isinstance(val, tuple) else (val, None)
        if comment:
            pad = " " * (indent * 4)
            key_str = f"{pad}{key}:"
            result.append((indent, key_str, str(value), comment))
        if isinstance(value, dict):
            _gather_comment_rows(value, indent + 1, result)
    return result


def _dump_yaml_with_comment_alignment(data: Dict[str, Any]) -> str:
    """
    Print YAML so all values align vertically, and comments (if present) align to the right of the longest value needing a comment.
    Adds a blank line before each new top-level key (indent==0) except the first.

    Args:
        data: The dictionary to render as YAML, where each value may be a (value, comment) tuple.

    Returns:
        str: The formatted YAML string with aligned values and comments, and blank lines between top-level keys.
    """
    # Gather all rows for key and value alignment
    all_rows = _gather_all_keys_values(data)
    comment_rows = _gather_comment_rows(data)
    # Find max lengths for alignment
    max_key_len = max(len(" " * (indent * 4) + key + ":") for indent, key, value, comment in all_rows)
    # Only consider values with comments for comment alignment
    max_value_len_with_comment = 0
    if comment_rows:
        max_value_len_with_comment = max(len(value) for _, _, value, _ in comment_rows)
    # Print recursively, using these widths
    def _print(data: Dict[str, Any], indent: int = 0, is_top_level: bool = False) -> list[str]:
        lines = []
        pad = " " * (indent * 4)
        for idx, (key, val) in enumerate(data.items()):
            value, comment = val if isinstance(val, tuple) else (val, None)
            key_str = f"{pad}{key}:".ljust(max_key_len + 1)
            # Add blank line before each new top-level key except the first
            if is_top_level and idx > 0:
                lines.append("")
            if isinstance(value, dict):
                lines.append(f"{pad}{key}:")
                lines.extend(_print(value, indent + 1))
            else:
                # Align value, align comment if it exists
                value_str = str(value)
                if comment:
                    value_str = value_str.ljust(max_value_len_with_comment + 4)
                    line = f"{key_str}{value_str}# {comment}"
                else:
                    line = f"{key_str}{value_str}"
                lines.append(line)
        return lines
    return "\n".join(_print(data, is_top_level=True))


def _generate_env_for_model(model: Type[BaseModel], prefix: str = "") -> Dict[str, str]:
    """
    Generate a dictionary representing the expected .env structure for a given Pydantic model.

    Args:
        model: The Pydantic BaseModel class to inspect.
        prefix: The prefix to use for environment variable names (used for nested models).

    Returns:
        Dict[str, str]: A dictionary mapping environment variable names to sample values or "<SECRET>" for secret fields.

    - Secret fields (e.g., SecretStr) are represented as "<SECRET>".
    - Nested BaseModel fields are recursed with double underscore delimiters.
    - Fields ending with "JSON" are given a sample JSON string.
    """
    result: Dict[str, str] = {}
    for name, field in model.model_fields.items():
        env_key = (prefix + name).upper()
        if _is_secret_field(field):
            result[env_key] = "<SECRET>"
        else:
            field_type = field.annotation
            if isinstance(field_type, type) and issubclass(field_type, BaseModel):
                # Recurse only if it's a BaseModel subclass
                result |= _generate_env_for_model(field_type, prefix=f"{env_key}__")
            elif name.upper().endswith("JSON"):
                result[env_key] = '{"sample": "value"}'
    return result


def print_yaml_and_env(SettingsClass: Type[BaseSettings]) -> None:
    """
    Prints the expected structure of config.yaml and .env for the given Pydantic settings class.
    """
    yaml_dict = _generate_yaml_for_model(SettingsClass, for_docs=True)
    print("\n======================== config.yaml structure ========================\n")
    # This will return a big string, ready to print
    print(_dump_yaml_with_comment_alignment(yaml_dict))
    env_dict = _generate_env_for_model(SettingsClass)
    print("\n======================== .env structure ========================\n")
    for key, value in env_dict.items():
        print(f"{key}={value}")
    print("\n\n")