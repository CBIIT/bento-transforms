import logging

global_log_level = "INFO"


def get_logger(log_name=None, **optargs):
    log_level = optargs.get("log_level", global_log_level)
    logging.basicConfig(level=log_level)
    logger = logging.getLogger(log_name)

    return logger


def set_global_log_level(log_level):
    global_log_level = (
        log_level
        if log_level in ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
        else "INFO"
    )
