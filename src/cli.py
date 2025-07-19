import click
import logging

from src.config import get_settings
from src.logger import setup_logging
from src.utils import create_directory_tree, save_used_config

logger = logging.getLogger("__name__")


@click.command()
def main():
    
        # In your main code:
    settings = get_settings()
    tree = settings.program_config.dir_tree  # This already has {output_folder} replaced
    create_directory_tree(tree)
    save_used_config(settings, settings.program_config.output_folder)

    setup_logging(input_config_json=settings.logger_config.config_file, 
                  output_folder_path=settings.program_config.output_folder,
                  level=settings.logger_config.level
                  )

    logger.info("logger set up")

if __name__ == "__main__":
    main()

