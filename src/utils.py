import pathlib
from typing import List, Any
import yaml
from pathlib import Path

CONFIGS_USED_PATH = "outputs/output_folder/configs_used"
INPUT_CONFIG_PATH = "config.yaml"

def create_directory_tree(tree: List[str]) -> None:
    """
    Creates directories from a list of paths, skipping file paths (those with a file extension).
    Args:
        tree: List of directory and file paths (placeholders already replaced).
    """
    for path in tree:
        p = pathlib.Path(path)
        # Only create if this is a directory path (no suffix, and not a known file name)
        # Optionally, also allow trailing slashes as directory markers
        is_probably_dir = not p.suffix and not p.name.startswith('.') and not p.name.lower().endswith('.env')
        if is_probably_dir or str(path).endswith("/") or p.is_dir():
            try:
                p.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {p.resolve()}")
            except FileExistsError:
                # If a file exists with the same name, print a warning but don't crash
                print(f"⚠️  Path exists and is a file, not directory: {p.resolve()}")
        else:
            # This path looks like a file, so skip making a directory
            print(f"ℹ️  Skipping file: {p.resolve()}")
            
            
def save_used_config(input_config_settings_path, input_config_logger_path, output_used_config_path):
    """
    Saves config to outputs/<output_folder>/configs_used/used_config.yaml
    """
    # Path to the configs_used subdirectory
    output_path = Path(CONFIGS_USED_PATH.replace("output_folder", output_folder))
    # configs_used_dir.mkdir(parents=True, exist_ok=True)

    # Path to the YAML file
    
    # Path to the logging config used file

    # Convert Pydantic model to dict if needed
    if hasattr(config, "model_dump"):
        config_dict = config.model_dump()
    elif isinstance(config, dict):
        config_dict = config
    else:
        raise ValueError("config must be a Pydantic model or a dict")

    with open(output_path, "w") as f:
        yaml.safe_dump(config_dict, f, sort_keys=False)
    print(f"Saved used config to: {output_path.resolve()}")