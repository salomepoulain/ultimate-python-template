import click
import logging

from src.config import get_settings
# from my_logging import setup_logging


logger = logging.getLogger("__name__")


@click.command()
def main():

    settings = get_settings() 
    print("hi")

    # setup_logging(settings)
    # logging.basicConfig(level=settings) #TODO: change if i actually need to move it like this

    

if __name__ == "__main__":
    main()

