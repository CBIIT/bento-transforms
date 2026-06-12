from bento_transforms.utils import logger

LOG = logger.get_logger(log_name=__file__.split("/")[-1])


def transform_local_test(trans_str: str, **kwargs):
    """An example transformation test function that
    takes a prefix and appends it to the string passed
    as the main argument
    """
    ret_val = None
    LOG.info(f"Running transform_local_test: trans_str {trans_str}, kwargs {kwargs}")
    prefix = kwargs.get("params", {}).get("prefix", "Hey now ")
    if isinstance(trans_str, str):
        # prepend something
        ret_val = f"{prefix}{trans_str}"
    else:
        # log an error here
        LOG.error(f"Expected type of str, got {type(trans_str)}")

    return ret_val
