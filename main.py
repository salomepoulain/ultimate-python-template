# from cli import main


# def main():
    # setup_logging()
    # logging.basicConfig(level="INFO")
    # logger.debug("debug message", extra={"x": "hello"})
    # logger.info("info message")
    # logger.critical("this is such a special case of logging idk")
    # logger.warning("warning message")
    # logger.error("error message")
    # logger.critical("critical message")
    # try:
    #     1 / 0
    # except ZeroDivisionError:
    #     logger.exception("exception message")


if __name__ == "__main__":
    # main()
    # The line `# import yaml` is a commented-out import statement for the `yaml` module in Python.
    # This line is not executed when the script runs because it is preceded by a `#` symbol, which
    # indicates a comment in Python. Comments are ignored by the Python interpreter and are used to
    # provide explanations or notes within the code for developers to read.
    from src.config import get_settings
    
    settings = get_settings()
    print(settings.model_dump())

