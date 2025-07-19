import datetime as dt
import json
import logging
from typing import override
import pathlib
import atexit

LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}

INPUT_LOGGER_PATH = "config/logging_configs"

OUTPUT_LOGGER_PATH = "outputs/output_folder/logs"


class MyJSONFormatter(logging.Formatter):
    def __init__(
        self,
        *,
        fmt_keys: dict[str, str] | None = None,
    ):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    @override
    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord):
        always_fields = {
            "message": record.getMessage(),
            "timestamp": dt.datetime.fromtimestamp(
                record.created, tz=dt.timezone.utc
            ).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: (
                msg_val
                if (msg_val := always_fields.pop(val, None)) is not None
                else getattr(record, val)
            )
            for key, val in self.fmt_keys.items()
        } | always_fields
        for key, val in record.__dict__.items():
            if key not in LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val

        return message

# TODO: change to make it be output_folder path. do not have the dependency for the weird folder structure shit
def setup_logging(input_config_json, output_folder, level):
    config_file = pathlib.Path(f"{INPUT_LOGGER_PATH}/{input_config_json}.json") 
    with open(config_file) as f_in:
        config = json.load(f_in)
        
    for handler in config.get("handlers", {}).values():
        if "filename" in handler:
            log_path = pathlib.Path(OUTPUT_LOGGER_PATH.replace("output_folder", output_folder) / handler["filename"] )            
            handler["filename"] = str(log_path)

    logging.config.dictConfig(config)
    
    logging.basicConfig(level=level)
    
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)

# * setup custom filters here  -------------------------- 

class SpecialMessageFilter(logging.Filter):
    def filter(self, record):
        return "special" in record.getMessage()

class NonErrorFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno <= logging.INFO



